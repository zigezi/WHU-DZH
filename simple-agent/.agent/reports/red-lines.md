# 常设红线登记册（Standing Red Lines）

> 每线：**内容 / 来源 / 状态**。红线=结构性禁令，不因个案便利而松；违反须主动披露。
> 本册与 `governance-defect-classes.md`（缺陷修法不变式）互补：一册记"不许做"，一册记"如何不重犯"。

## RL-1 指令明文禁令（hidden instruction）
- **内容**：dev 集指令明文不得进入 updater/worker 可见面（威胁模型=过拟合提案）。
- **来源**：P5a.20 §二（三层分层访问）。
- **状态**：在役。

## RL-2 secret 值禁令（DC-7）
- **内容**：一切 compaction/摘要/日志/证据制品只许存密钥**位置**（`backend/.env`，mode 600），禁止存**值**；摘要生成器须脱敏（`scripts/secret_mask.py`）。
- **来源**：P5a.72 §一.2；P5a.74 §二验收。
- **状态**：在役。

## RL-3 agent 禁 git push / 推送权不离人
- **内容**：① agent 可达 shell **禁 `git push`**；simple-agent 远端同步=**用户手动**；② `/root/simple-agent` **不得配 remote**（结构性边界，非缺陷）；③ `key.txt` 的 token **opencode 永不使用**。
- **来源**：P5a.74 §三。
- **状态**：在役（生效即本轮起）。**注**：本令下达前 opencode 曾受用户当场指令推送镜像 `9ec0c8b`，已主动披露（`.agent/evidence/phase-P5a74-push-disclosure.md`）。
