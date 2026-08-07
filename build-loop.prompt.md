# 任务：为 NL2EARS 平台实现「代码生成 + 沙箱验证 + 自动修复 + Preview」构建子系统（v1）

> 本文件是给编码代理（opencode）执行的实施任务书。
> 用法：在 NL2EARS 仓库根目录启动 opencode，输入「请按照 build-loop.prompt.md 完成 v1 构建子系统的实现」。
> 版本: 1.1（已并入首轮工程审查的 18 项修复）

---

## 〇、开工前必读（先读后写，违反即返工）

1. 先完整阅读以下现有文件，理解现有架构与代码风格，**新代码必须与现有风格一致**（分层 routes、curl 调 Moonshot、JWT 中间件、PG 查询方式）：
   - `backend/src/index.js`（入口、静态托管、中间件挂载方式）
   - `backend/src/db.js`（PG 连接与建表模式）
   - `backend/src/ai.js`（curl 调 Moonshot 的封装方式——**禁止改用 fetch/axios**，Moonshot WAF 会拦截 Node 原生请求）
   - `backend/src/routes/auth.js`、`backend/src/routes/sessions.js`（JWT 属主校验的实现模式，新接口必须复用）
   - `frontend/src/Chat.vue`、`frontend/src/App.vue`（前端结构与组件风格）
2. 读完后先用一段话向用户复述：现有鉴权方式、Moonshot 调用方式、会话目录结构，确认理解无误再动手。
3. **非回归红线**：不得改动现有反问、归档、EARS 转换、下载四个功能的任何行为；所有新增代码放在新文件/新路由中，对现有文件的修改仅限「挂载新路由」和「前端加面板入口」。
4. **环境前提检查**（不满足则停下来报告，不要硬写）：
   - 后端进程可访问 `/var/run/docker.sock`（宿主机直跑：运行用户在 docker 组；后端容器化：需挂载 socket，且 Binds 源路径必须是**宿主机**绝对路径，不是容器内路径——DooD 经典坑，路径前缀校验也按宿主机路径做）；
   - 系统 git 可用；docker 可用；
   - 服务器上已存在 `node:20-alpine` 镜像（`docker image inspect` 验证，不存在则提示管理员先执行 setup-build-env.sh）。

---

## 一、任务背景与目标

本平台现状：用户经对话生成 `requirements-<ts>.md`，并可转换为低歧义 EARS 规格 `requirements-<ts>-ears.md`，产物在 `workspace/session-<ts>/`。

本次要实现 v1 构建子系统，让平台从「需求文档生成器」升级为「能生成并验证可运行应用的 Builder」。验收时必须能演示以下完整链路：

1. 基于会话内已有的 EARS 文档，一键生成**纯前端可运行应用**（HTML/CSS/JS，无后端）；
2. 生成的代码自动在 **Docker 沙箱**中做静态验证（语法检查 + 静态服务可达性检查）；
3. 验证失败时，LLM 自动分析报错、产出补丁、应用后重跑，**最多 8 轮**，全程日志可见；
4. 前端面板可浏览生成项目的**文件树**、查看文件内容、**下载 ZIP**；
5. 应用可通过浏览器内 **iframe Preview** 直接运行；
6. 支持**增量修改**（用户输入一条修改指令 → LLM 出补丁 → 沙箱验证 → 生效）和**版本回滚**（每轮一个 git commit，可恢复到任一历史版本，恢复后目录与该版本完全一致）。

### 服务器硬约束（阿里云轻量 2核2G/40G，所有设计必须服从）

- 沙箱容器配额：`Memory=256MB`、`CpuQuota=50000`（半核）、`PidsLimit=100`、`NetworkMode=none`、`AutoRemove=true`，外层硬超时 120 秒；
- **同时最多 1 个沙箱在跑**：实现一个进程内串行队列，其余构建请求排队（状态 queued）；
- Preview **不得使用容器**：Express 静态托管 + iframe `sandbox="allow-scripts"` 实现（**禁止添加 allow-same-origin**，原因见 2.4）；
- 沙箱断网，一切依赖必须离线可用：只使用预置的 `node:20-alpine` 镜像，runtime 允许清单 v1 仅 `["static-web"]`，manifest 出现其他值直接拒绝。

---

## 二、后端实现清单

### 2.1 数据库：`backend/src/db.js` 追加两张表（沿用现有建表模式）

```sql
CREATE TABLE IF NOT EXISTS builds (
  id SERIAL PRIMARY KEY,
  session_id INTEGER REFERENCES sessions(id),
  user_id INTEGER REFERENCES users(id),
  status VARCHAR(32) NOT NULL DEFAULT 'queued',
    -- 枚举全集：queued / coding / validating / debugging / modifying / passed / failed
    -- 终态仅 passed 与 failed；「活跃」= 其余五种
  iterations INTEGER NOT NULL DEFAULT 0,
  error_summary TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  finished_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS build_events (
  id SERIAL PRIMARY KEY,
  build_id INTEGER REFERENCES builds(id),
  agent VARCHAR(32),        -- coder / sandbox / debugger / system
  event_type VARCHAR(32),   -- status / log / file / patch / error
  content TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.2 新文件 `backend/src/sandbox.js`：Docker 沙箱封装

用 `dockerode`（加入 backend/package.json 依赖）实现，导出：

- `runValidation(buildDir)`：
  - **验证脚本方式（禁止 sh -c 拼接）**：把验证脚本 `_validate.cjs` 写入 buildDir（验证结束后删除，**不进 git**、不进 ZIP、不出现在文件树），容器命令固定为 `node /app/_validate.cjs`。脚本逻辑：
    1. 检查 `index.html` 存在，不存在则 exit 1；
    2. 对每个 `.js` 文件，以及从 `index.html` 提取的每个内联 `<script>` 块（写入临时文件），执行 `node --check`（生成的代码已被 prompt 禁止 ESM，统一按普通脚本检查；若检测到 `import/export`，改用 `node --input-type=module --check` 再试一次，两者都失败才算语法错误）；
    3. 用 node 内置 `http` 起静态服务监听 127.0.0.1 随机端口，`http.get` 请求 `/index.html` 返回非空即通过；
    4. **脚本必须显式 `process.exit(0/1)` 自行结束，严禁留下常驻进程**（否则容器不退出，全部构建被误判为超时）；
  - 挂载：`Binds: [<宿主机 buildDir 绝对路径>:/app:ro]`——**只读挂载**（验证不需要写 /app；rw 会让容器内 root 在 buildDir 留下 root 属主文件，导致后端后续写文件 EPERM）。挂载源 `path.resolve` 后校验以 `workspace/session-<ts>/build` 为前缀，否则拒绝；
  - 配额与超时按硬约束；超时 `docker.kill()` 记为失败（errorType=timeout，日志注明疑似死循环）；
  - 返回 `{passed, exitCode, stdoutTail, stderrTail, errorType}`，stdout/stderr 只保留**尾部 50 行**。
- `pullTemplateImage()`：管理员手动预拉镜像（导出供脚本使用，不挂 HTTP 路由；**禁止在请求路径上在线拉镜像**）。

串行队列：模块级 `queue` 数组 + `running` 标志，`enqueue(task)` 返回排队位置；同时仅 1 个任务执行。

### 2.3 新文件 `backend/src/builder.js`：构建编排状态机

导出 `startBuild(sessionId, userId)`、`applyModification(buildId, instruction, userId)`、`revalidate(buildId, userId)`，均为**异步 fire-and-forget**（HTTP 接口先同步校验、立即返回 buildId，进度走 SSE）。

`startBuild` 流程：

1. 校验会话属主 + 会话目录存在 `*-ears.md`（取最新一份），不存在返回 409 提示先完成 EARS 转换；
2. 创建 `workspace/session-<ts>/build/`，在其中 `git init`，**随后立即执行仓库级 `git config user.email builder@localhost && git config user.name builder`**（新机器无全局 identity，不配则 commit 必炸）。系统无 git 时降级为每轮整目录快照 `.versions/<n>/`，降级模式下**补丁一律改用「文件全文覆写」方式应用**；
3. status=coding：调 `ai.js` 新增的 `generateApp(earsContent)`（见 2.5），产出 JSON：`{files: [{path, content}], entry: "index.html", runtime: "static-web"}`。逐文件写入 build/（写前路径净化：拒绝绝对路径与 `..`）。git commit `v0: initial generation`；
4. status=validating：`sandbox.runValidation()`；
5. 通过 → status=passed，写 `manifest.json`（files 清单、entry、iterations、最终 commit；**manifest.json 加入 ZIP 与文件树的排除清单**），结束；
6. 失败 → 修复循环（最多 8 轮，`builds.iterations` 递增）：
   - status=debugging：调 `ai.js` 的 `debugFix(...)`（见 2.5），优先要 unified diff；
   - **补丁应用容错**：先剥离 markdown ``` 围栏；用 `git apply --whitespace=fix --recount`（子进程 execFile 参数数组调用，禁止 shell 字符串拼接）；apply 失败则把错误回喂重出一次；**连续两次失败则降级为让 LLM 输出受影响文件全文直接覆写**（仍计迭代）；
   - 重新验证；通过则 commit `fix round <n>: <错误摘要首行>`，退出循环；
   - 8 轮未过 → status=failed，`error_summary` 记录最后一轮错误尾部，保留全部日志与 git 历史；
7. 每步状态变更、日志、补丁写 `build_events`。

`applyModification`：校验属主 + 存在终态 build → 读取 build/ 文件（超 24k tokens 时只带文件清单+相关文件，日志注明裁剪）→ `incrementalModify()` 出补丁 → 同样的容错应用 → 沙箱验证 → 通过则 commit `modify: <instruction 前 50 字>`，失败进修复循环。

`revalidate`：重新执行沙箱验证，失败自动进修复循环（用于环境变化或人工改文件后的复验）。

### 2.4 新文件 `backend/src/routes/build.js`：HTTP 接口

**路由层统一要求**：属主校验、EARS 存在性检查、活跃 build 冲突检查（活跃=queued/coding/validating/debugging/modifying，**按会话判定**）全部**同步**完成并返回 403/409，通过后才触发异步流程。已有终态 build 的会话再次 POST build 返回 409 并提示改用 modify 或 revalidate。

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/sessions/:id/build` | 触发构建，返回 `{buildId}` |
| POST | `/api/builds/:id/modify` | body `{instruction}`，增量修改 |
| POST | `/api/builds/:id/revalidate` | 重跑沙箱验证，失败自动进修复循环 |
| GET | `/api/builds/:id/events` | SSE，见下方实现约束 |
| GET | `/api/sessions/:id/build/files` | 递归文件树 JSON（排除 `.git`、`node_modules`、`.versions`、`_validate.cjs`、`manifest.json`） |
| GET | `/api/sessions/:id/build/file?path=<rel>` | 单文件内容（≤100KB，路径前缀校验） |
| GET | `/api/sessions/:id/build/versions` | git log 列表（hash/message/time） |
| POST | `/api/sessions/:id/build/restore` | 见下方安全约束 |
| GET | `/api/sessions/:id/build/download` | build/ 打包 ZIP（排除 .git/.versions/_validate.cjs/manifest.json；**不得解引用符号链接**） |
| GET | `/preview/:sessionId/` | 静态托管 build/，见下方安全约束 |

**SSE 实现约束（events 接口）**：
- 鉴权：`?token=<JWT>` 查询参数（**原生 EventSource 无法设置 Authorization 头**，与 preview 同一套 token 校验函数），并校验 build 属主；
- 响应头：`Content-Type: text/event-stream`、`Cache-Control: no-cache`、有反代时 `X-Accel-Buffering: no`，立即 `flushHeaders()`；
- **每 20 秒发一行心跳注释**（`: ping`）——一次构建含多轮 LLM 调用可持续 10+ 分钟，无心跳会被中间层 60s 静默断连；
- wire 格式：`id: <eventId>`、`event: <type>`、`data: <JSON>`；`after` 重放历史后转 1~2s DB 轮询推新增；build 终态后发 `event: done` 并关闭；
- 兼容 EventSource 自动重连的 `Last-Event-ID` 头（等价于 after）；`req.on('close')` 必须清理轮询定时器。

**restore 安全约束**：body `{hash}` 必须匹配 `^[0-9a-f]{7,40}$`；一律 execFile/spawn **参数数组**调用 git（**禁止 shell 拼接，hash 来自用户输入，拼接即 RCE**）；恢复语义为「工作区与该版本完全一致」：`git restore --source=<hash> --staged --worktree -- .` 之后 `git clean -fd`（删除该版本不存在的多余文件——只 restore 不 clean 会留下新版本的残留文件，恢复结果是版本混杂体）；然后重新沙箱验证，通过则 commit `restore to <hash>`。

**Preview 路由安全约束**：
- 鉴权：iframe 无法带 Authorization 头，采用 `?token=<JWT>`；**为防 token 落访问日志/浏览器历史**：首次验证通过后 `Set-Cookie`（HttpOnly + `Path=/preview/<id>/` + SameSite=Strict）并 302 到无 token URL，后续走 cookie；**preview 与 events 路由的访问日志不得记录 query string**；
- 路径：`path.resolve` 前缀校验，防目录穿越；
- 响应头：`Content-Security-Policy: default-src 'self' 'unsafe-inline'; img-src 'self' data:`；
- iframe 侧只用 `sandbox="allow-scripts"`。**禁止加 allow-same-origin**：preview 与平台同源，加上后生成的不可信代码可读平台 localStorage 里的 JWT，沙箱形同虚设。

### 2.5 `backend/src/ai.js` 新增三个函数（沿用 curl 封装，模型 `moonshot-v1-32k`）

- `generateApp(earsContent)`：system prompt 要点——严格按 EARS 规格实现，术语表中的常量/坐标/时序/TBD 默认值必须原样采用；只输出规定 JSON，禁止输出解释；`index.html` 入口；**文件数量尽量少（建议 ≤6 个），优先内联，禁止留截断注释**（32k 输出截断是 JSON 解析失败最大来源）；不使用任何外部 CDN/网络资源（沙箱断网）；**禁止 ESM import/export 与 `<script type="module">`**（统一 CommonJS 语法，沙箱按此检查）；**所有 localStorage/sessionStorage/cookie 访问必须 try/catch 并降级为内存实现**（Preview 运行在禁用存储的 sandbox iframe 中，直接访问会抛 SecurityError 导致白屏）。
- `debugFix(earsPart, stderrTail, involvedFiles)`：你是调试器；输出最小 unified diff；禁止重写整个文件；禁止为消除报错而删除/弱化 EARS 需求对应的功能；报错与需求冲突时以 EARS 原文为准。
- `incrementalModify(instruction, earsContent, currentFiles)`：同上；修改指令与 EARS 冲突时按 EARS 执行并在日志标注。
- 三者统一：JSON/diff 解析失败重试 1 次（回喂解析错误）；每次调用 token 用量写 `build_events`。

---

## 三、前端实现清单

新组件 `frontend/src/BuildPanel.vue`，在 Chat.vue 会话区旁（或下方折叠面板）接入，四个 Tab：

1. **构建日志**：`EventSource` 连 events 接口（`?token=`），滚动显示 agent/时间/内容；状态徽章（queued→coding→validating→debugging→passed/failed）；当前迭代数 n/8；
2. **文件**：递归文件树（自写递归组件，不引第三方树组件），点击右侧等宽 `<pre>` 显示内容；
3. **预览**：passed 后显示 `<iframe :src="'/preview/'+sessionId+'/?token='+jwt" sandbox="allow-scripts">` +「新窗口打开」链接；构建中显示进度占位；
4. **版本**：commit 列表（message/时间），每条带「恢复到此版本」（confirm → restore → 刷新预览）+「下载 ZIP」。

Chat.vue 入口：会话存在 EARS 文档时显示「生成应用」按钮；已有终态 build 的会话显示「修改应用」输入框与「重新验证」按钮。

---

## 四、部署脚本：仓库根目录新增 `setup-build-env.sh`（生成但不执行）

```bash
# 1. 2G swap（幂等）
# 2. 将后端运行用户加入 docker 组（usermod -aG docker <user>，提示重新登录生效）
# 3. docker pull node:20-alpine
# 4. PostgreSQL 降配说明（shared_buffers=128MB / work_mem=4MB / max_connections=20）
# 5. crontab 每日 docker system prune -f
# 6. 后端启动建议：node --max-old-space-size=400 src/index.js
```

---

## 五、验收标准（服务器无浏览器，按以下可自动执行的方式自验并输出证据）

1. **端到端生成**：用包含贪吃蛇 EARS 文档的会话触发构建 → passed；`curl` 带 token 访问 `/preview/:id/` 返回 200，index.html 及其引用的全部相对路径资源可达；静态检查生成代码含方向按钮处理逻辑。「浏览器实际试玩」标注为管理员人工项；
2. **自动修复**：人为向生成文件注入一个**内联 script** 语法错误 → 调 revalidate → 日志可见 debugging 轮次 → 最终 passed，git 历史有对应 fix commit；
3. **增量修改两次**：先后提交两条指令（如「苹果数量改为 15」「失败提示改为 3 秒」）→ 均 passed、各自独立 commit、第二次不破坏第一次；
4. **版本回滚**：restore 到 v0 → build/ 目录与 v0 完全一致（含删除后续新增文件），preview 内容回到初始版本；
5. **文件与下载**：文件树完整；文件可查看；ZIP 下载后 `unzip` 验证 index.html 存在且其引用的相对路径资源均在包内；
6. **权限**：非属主 token 访问 files/preview/restore/events 全部 403；
7. **资源合规**：构建期间 `docker inspect <容器>` 输出证明 `Memory=268435456`、`CpuQuota=50000`（容器存活短，不用 docker stats）；同会话重复 POST 返回 409；**跨会话**连续两个构建，第二个为 queued；
8. **非回归**：用 curl 对反问/归档/EARS 转换/会话下载四个旧接口各发一次真实请求，状态码与响应结构符合预期。

输出形式：验收清单逐项 PASS/FAIL + 关键日志摘录 + `git log` 文本。

---

## 六、明确的非目标（禁止做）

- 不做多智能体并行（无 Decomposer/并行 Coder/Integrator）——v1 单 Coder 一次生成全部文件；
- 不做生成带后端的应用，不做容器常驻 Preview；
- 不引入 Python 依赖、不引入 LangChain/LangGraph 等编排框架；
- 不换数据库、不改鉴权方案、不动现有 EARS 提示词；
- 不在沙箱内联网安装依赖；
- 不给 preview iframe 加 allow-same-origin。

---

## 七、卡住时的处理

- Docker socket 权限/路径问题 → 诊断写日志后停下来报告，不要绕过（如改成 chmod 777）；
- Moonshot 输出 JSON 解析反复失败 → 先 ```json 代码块提取容错，仍失败则记录原始输出并标 failed，不得静默吞错；
- git 不可用的降级模式只在 startBuild 时判定一次，全程一致使用，不得中途切换；
- 任何与现有代码冲突的设计判断 → 优先保护现有功能（非回归红线），并在最终报告列出所做权衡。
