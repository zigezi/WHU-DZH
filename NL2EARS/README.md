# WHU-DZH · AI 辅助需求开发平台

一个"OpenSpec 风格"的 AI 需求工程平台：用户在浏览器中注册/登录（图形验证码保护），登录后进入会话式对话，AI（Moonshot/Kimi）以 OpenSpec 的探索(explore)/提案(propose)方法论逐轮反问用户、澄清需求；用户确认后生成需求分析文档，并可一键转换为**低歧义 EARS 需求规格说明书**。每个会话对应 workspace 下一个时间戳命名的文件夹，全部产物可打包下载。

## 功能特性

- **注册 / 登录 / 图形验证码**：SVG 验证码（点击刷新，5 分钟有效，一次性），密码 bcrypt 加密，JWT 会话
- **会话管理（用户 1:N 会话）**：用户可创建多个会话，登录后自动开启新会话，侧边栏切换历史会话
- **OpenSpec 式 AI 反问**：AI 每次只问 1-2 个聚焦问题，逐轮澄清目标/用户/功能/约束/验收标准/非目标
- **需求分析文档生成**：点击「完成 / 归档」，AI 依据整段对话生成结构化 `requirements-<ts>.md` 写入会话文件夹
- **低歧义 EARS 转换**：点击「⬇ 下载低歧义EARS需求」，按 `ears-convert.prompt.md` 规则将需求文档转换为 EARS 规格说明书（五类句式、封闭术语表、TBD 清单、验收追踪矩阵），并下载整个会话文件夹 ZIP
- **产物下载**：任意会话可下载其完整文件夹（ZIP），仅属主可访问

## 技术架构

```
浏览器 (Vue 3 SPA)  ──HTTP──>  Express :3000  ──pg──>  PostgreSQL (Docker :5432)
                                    │
                                    └── curl ──>  Moonshot API (api.moonshot.cn/v1)
```

- 前端：Vue 3 + Vite，构建产物 `frontend/dist` 由 Express 静态托管，单端口对外
- 后端：Node.js + Express，JWT 鉴权中间件，分层 routes（auth / sessions）
- 数据库：PostgreSQL，表 `users`、`sessions`（用户一对多会话）、`messages`（含 role/session_id）
- AI：Moonshot Kimi。反问/需求生成用 `moonshot-v1-8k`；EARS 转换用 `moonshot-v1-32k`（提示词+输出较大，8k 上下文不足）。因 Moonshot WAF 按 TLS 指纹拦截 Node 内置 fetch，后端统一用系统 `curl` 调用。

## 目录结构

```
user-app/
├── backend/                # Node/Express 后端
│   ├── src/index.js        # 入口（托管前端静态文件 + API）
│   ├── src/db.js           # PostgreSQL 连接与建表
│   ├── src/ai.js           # Moonshot 调用（反问/文档/EARS）
│   ├── src/routes/auth.js  # 注册/登录/验证码/JWT
│   ├── src/routes/sessions.js  # 会话/消息/归档/EARS/下载
│   ├── .env                # 环境配置（含 API Key，勿提交）
│   └── package.json
├── frontend/               # Vue 3 前端
│   └── src/{App.vue, Chat.vue}
├── workspace/              # 会话产物目录
│   └── session-<时间戳>/    # 每个会话一个文件夹
│       ├── requirements-<ts>.md        # 需求分析文档
│       └── requirements-<ts>-ears.md   # EARS 规格（转换后生成）
├── ears-convert.prompt.md  # EARS 转换任务提示词（转换规则+参考范例）
├── requirements.txt        # 依赖清单
├── README.md
└── deployment.txt          # 部署说明
```

## 快速开始

1. 安装依赖：见 `requirements.txt`（`backend/` 与 `frontend/` 各执行 `npm install`）
2. 配置数据库与环境：见 `deployment.txt`
3. 构建前端：`cd frontend && npm run build`
4. 启动后端：`cd backend && node src/index.js`（或 `npm start`）
5. 浏览器访问：http://localhost:3000

## 数据库表

| 表 | 说明 | 关键字段 |
|---|---|---|
| users | 用户 | id, username, email, password(bcrypt), created_at |
| sessions | 会话 | id, user_id(外键), name, folder, status(active/archived), created_at |
| messages | 消息 | id, user_id, session_id(外键), role(user/assistant), content, created_at |

## 安全说明

- `backend/.env` 含 Moonshot API Key 与数据库口令，**严禁提交**（已加入 .gitignore 建议）
- 会话下载/EARS 接口均校验 JWT 且仅限 session 属主
- PostgreSQL 绑定 127.0.0.1，不对外暴露

## 许可证

详见各子模块；本平台自研代码按 MIT 精神开放，OpenSpec 为其独立上游项目。
