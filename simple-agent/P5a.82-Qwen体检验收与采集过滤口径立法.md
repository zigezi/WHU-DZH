# P5a.82 — Qwen3.8-Max 体检验收裁决与采集过滤口径立法

**裁者**：仲裁席（本席）
**日期**：2026-10-15
**案由**：(一) Qwen3.8-Max 体检答卷（针对最新提交 Diff 5889320...3d3f5ef 的五层审查）价值判定；(二) opencode a80 执行回执（image(129)，本地提交 2f0e3bb 未推送）中实抓缺陷之二的「误判洪水」过滤口径裁决请求；(三) RL-3 例外条款待裁项的用户直裁登记。
**证据**：Qwen 答卷全文（p5a80-co.txt）；opencode a80 回执（image(129)）；P5a.77/78（DC-9 修法）；P5a.79/80（采集钩子与语境锚定）；P5a.68（校准投毒禁令）。

---

## §一 体检总评：有价值，二审试用期正式上岗

**裁决：Qwen3.8-Max 体检通过，即日以「二审 reviewer（试用期）」身份上岗。其全部 finding 一律视为「待验证假设」，执行方（opencode）验证回执后方可立法——本案即示范流程。**

五项 finding 逐项评分：

| # | finding | 判定 | 价值 |
|---|---|---|---|
| 1 | DC-9 沙盒存在层级绕过：_guard_production 仅在 register_asset()，set_credit/revalidate/patch_asset/shadow_event 等写函数可能直写生产注册表 | **潜在新高危，待验证**（§四下单验证） | 若证实 = 二审制度首次捕获仲裁+执行双盲区，高 |
| 2a | 钩子 JSON 转义只覆盖 \r\n\t，其余控制字符（\b \v \0 等 U+0000–001F）仍会打断 JSONL | **正确**（RFC 8259 控制字符必须转义），是对 opencode 换行修复的真扩展 | 中，采纳为加固（§五） |
| 2b | __oplog_fini 的 sleep 0.1 等待进程替换 flush，高负载下可能丢失 stderr 摘要 | **合理的系统批判**，低危（最坏=摘要截断，非损坏） | 低-中，入待办（§五） |
| 2c | BASH_ENV 仅对 bash 生效；subprocess 经 /bin/sh（dash）时钩子静默失效 | **正确**，属契约内盲区 | 低，文档化即可（§五） |
| 3 | classify() 「凡 rc!=0 即 test_or_build_fail」必灌爆农场；给出四层过滤设计（崩溃信号优先/工具族白名单/良性黑名单/SA_INVESTIGATION 标记） | **与 opencode 自抓缺陷收敛一致，且给出可立法方案** | 高，骨架采纳（§三），修正两处 |
| 4 | list_all() 的 `r[9] or "unknown"` 对空字符串会返回 "" 而非 "unknown" | **假阳性，语言语义错误**（§二登记 QB-1） | 负 |
| 5 | 称「本次提交涉及显式授权例外推送」并警告例外常态化 | **状态误读**：本轮本地未推送（RL-3 默认，opencode 回执明确）；其警戒方向已由用户直裁关闭（§六） | 低，误读登记 |

**信噪比结论**：1 项潜在新高危 + 1 项收敛确认附可立法方案 + 3 项正确的次要健壮性意见，对 1 项假阳性 + 1 项状态误读。二审的用处正在于前者；假阳性正是试用期要校准的东西。净判定：**有价值**。

**附记（哈希观察）**：Qwen 审查的 Diff 范围为 5889320...3d3f5ef，与 opencode 回执的本地提交号 2f0e3bb 不一致。推定用户已手动推送或向 Qwen 提供了特定 diff 快照；两者内容均指向 a80 落地（钩子 + 语境锚定），审查目标一致，不影响评级。此不一致仅登记，不立案。

---

## §二 假阳性登记 QB-1：Python 真值性语义错误

Qwen finding 4 主张：`r[9] or "unknown"` 在 r[9] 为空字符串时返回 `""`。

**事实**：Python 中 `"" or "unknown"` 返回 `"unknown"`——空字符串为 falsy，`or` 短路取后者。原式对 NULL 与空串均产出 "unknown"，**被指控的 bug 不存在**。且其建议的「修复」`r[9] if r[9] else "unknown"` 与原式**语义完全等价**，SQL 层 COALESCE(NULLIF(...)) 建议无的放矢。

**裁决**：
1. 不改任何代码。
2. 登记 **QB-1**（Qwen 二审档案首条校准数据）：错误类型 = 语言语义假阳性（confident wrong claim，附等价「修复」使其更难被一眼识破）。
3. 教训入册 **LR-5**：二审 finding 的可验证性分级——语言语义类主张可零 token 即时证伪，优先验证；架构类主张（如 finding 1）需代码取证，按 §四 流程。二审的产出永远是假设，不是事实。

---

## §三 误判洪水：采集过滤口径 v1 立法（blocking 项解禁）

opencode 自抓：钩子全量记录退出码，classify() 凡 rc!=0 即归 test_or_build_fail；grep 无匹配、diff、管道等良性非零退出一旦收割将灌爆农场、污染校准（P5a.68 校准投毒禁令适用）。本轮不跑 harvest 的决定**正确，予以确认**。现立法如下：

**采集口径 v1（filter_oplog_v1，对 code-ops.jsonl 逐行适用）：**

1. **必采（信号死亡）**：rc ≥ 128（139 SIGSEGV / 137 SIGKILL·OOM / 143 SIGTERM 等）的任何命令。
2. **必采（超时就绪）**：rc == 124 且命令经 timeout(1) 包裹 → 归 timeout_loop。（Qwen 方案漏此条：timeout 的 124 < 128，信号规则捕获不到，本席补上。）
3. **白名单采**：命令首词（管道取首段）属构建/测试工具族——{pytest, python -m pytest, make, cmake --build, cargo test, cargo build, go test, go build, npm/pnpm/yarn 之 build|test 子命令, gcc, g++, javac, tsc, mypy, ruff}——且 rc != 0 → 采集，按 stderr digest 细分既有类（test_or_build_fail / syntax_death / env_missing）。
4. **黑名单丢**：{grep, diff, test, [, which, find, ls, cat, head, tail, wc, sort, uniq, comm, cmp, git status, git diff, git log} 的 rc != 0 → 丢弃。此为良性控制流，非缺陷。
5. **灰区隔离**：不在任一清单且 rc != 0 → 采集但标 `tier=gray`，**不计触发线、不进校准池**，由人工或二审抽检定级后转正或丢弃。（以此替代 Qwen 的 SA_INVESTIGATION 环境变量方案：灰区口径已覆盖未知未知的保全需求，不引入新状态位，简化契约。）
6. **classify() 修法**：废止「凡 rc!=0 即 test_or_build_fail」的一刀切。信号死亡单独立类 **signal_death**——首个真实实例入账后方计入死亡类别多样性（防空类刷触发线）。
7. **出生要求照旧**：filter_oplog_v1 上线前跑 synthetic fixtures——上述六条口径每条至少 2 正 2 负样例，全绿方可标记 deployed（naming_proof 纪律延伸至过滤器）。
8. **离线重放**：code-ops.jsonl 现存全部历史行按 v1 口径重放一遍，命中者按规则入库/隔离/丢弃；此前重置隔离的 4 条历史种子维持隔离，不动。

**生效后**，harvest 解禁。

---

## §四 DC-9 层级绕过验证令（QB-2 待验证假设）

Qwen finding 1 若是真的，则 P5a.77 的修法只在 register_asset() 一处设岗，其余写函数可直写 PRODUCTION_FILE，DC-9 结构性失效。此为**可零 token 验证**的架构主张。

**令 opencode（下会话第一项，与钩子弹幕同优先级）：**
1. grep provenance.py 全部写路径：set_credit、revalidate、patch_asset、shadow_event，及任何其他落盘函数。
2. 逐一判定：是否内部路由经 register_asset()/_guard_production，还是直写 PRODUCTION_FILE。
3. 回执 = 「写路径清单 × 守卫状态」表。

**若确认绕过**：立法将守卫下沉至 I/O 层——提取 `_write_registry(data, allow_production)` 底层函数，一切写路径必经之（采纳 Qwen 建议骨架）。regression_sweep 增加对应不变式用例。
**若证伪**（所有写函数本就走 register_asset）：登记 QB-2 = 架构假阳性，入 Qwen 校准档案，与 QB-1 并列。

无论真伪，此单示范了二审工作流：**finding → 验证令 → 回执 → 立法或销案**。

---

## §五 钩子加固待办（不阻塞，随下次钩子触改一并做）

1. 控制字符兜底：__oplog_jsonstr 在 \r\n\t 之外过滤其余非打印字符（或极端情况 base64 兜底）——采纳 Qwen 2a。
2. __oplog_fini 的 sleep 0.1 改为 wait 具体后台 PID 或写入前显式关闭重定向 stderr  fd——采纳 Qwen 2b。
3. manifest/README 文档化盲区：BASH_ENV 仅覆盖 bash；经 /bin/sh（dash）的 subprocess 调用不在采集契约内——采纳 Qwen 2c。

三项均为加固，非缺陷修复，不动当前钩子在岗状态。

---

## §六 RL-3 例外条款：用户直裁登记

opencode 回执中遗留待裁项：「是否把『用户显式授权时 agent 可推送』写进 RL-3」。用户已直裁：**「不写，我手动推」**。

**裁决**：RL-3 原文不变，例外条款不立，该待裁项关闭。远程同步维持用户手动专属。再次提醒挂账事项：**key.txt GitHub token 二次暴露的轮换仍未执行**；下次手动同步前先跑 mirror_leak_scan。

---

## §七 生效与回执

1. 本裁决自落盘生效。
2. opencode 回执（单批次）：(a) filter_oplog_v1 fixtures 全绿证据 + 离线重放结果；(b) §四 DC-9 验证表；(c) harvest 解禁后首轮收割按 v1 口径的入库/隔离/丢弃统计。
3. Qwen3.8-Max 二审档案建立：正面积分 = finding 1（待验证新高危）+ finding 3（骨架被立法采纳）；负面积分 = QB-1 假阳性 + finding 5 状态误读。医院入职触发线仍悬而未决，二审表现累计入评估。
4. 用户侧：E2 三项域事实作业进行中（本席知悉，不催）；token 轮换挂账。

**裁者自律核对**：本文件已先写后言，ls 验证后发出 REF。

—— 仲裁席
