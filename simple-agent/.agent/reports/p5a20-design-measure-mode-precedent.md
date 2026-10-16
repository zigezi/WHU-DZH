# 设计便签 3 — 测量模式 precedent 选择器（真实签名 / content_hash / epoch 快照冻结）

**依据**：P5a.19 §四.2 + P5a.20 §一.1 裁决 2（批准便签）
**目标**：让"沉积物是否有用"（命题一）可被**无偏、可复现**地测量。三处修复：
真实签名选择 / content_hash / epoch 快照冻结；并配套固定 50/50 臂分配（epoch-7）。

## 1. 缺陷回顾（P5a.19 工单 1/3 取证）
- τ REQ `content` 全为占位语 → `signature.similarity` 恒 1.0 → `list_precedents(ORDER BY id DESC)` **恒取最新**
  = 上一完成任务的工具序列（A-008 注入 A-007；R-105 注入 R-102）。**语义相关性 = 0**。
- 无快照：先例库随 epoch 累积，同任务跨 epoch 注入内容不同（436 vs 213 tok）。

## 2. 设计

### 2.1 选择器（`worker.py:_inject_precedent`）
替换遍历逻辑为：
1. **仅同族**：候选 = `sig_family` 精确相等的先例；
2. **仅先前 epoch**：排除本 epoch/本次运行写入的先例（用快照 epoch 标签过滤）；
3. **确定性 tie-break**：同族多条时取 `id` 最小（最早沉积），**不再**用占位 `content` 的 similarity；
4. 无同族候选 → 记 `precedent_skip` span（`reason:"no_family_precedent"`），**不注入**（宁可空也不注入无关内容）。

### 2.2 epoch 快照冻结
- 表：`precedent_snapshots(epoch INTEGER, id, sig, req_id, plan_json, content_hash, source_epoch)`，
  或目录 `.agent/precedents/epoch-<N>.jsonl`（选定实现取简单者）。
- 时机：epoch 开始时一次性冻结（epoch_gate 启动钩子），本 epoch 内只读快照。
- 效果：同一任务在两个复制 epoch 注入**字节一致**（配合纯 50/50 臂分配）。

### 2.3 content_hash 埋点
`precedent_injected` span 增加：
`content_sha256_16 = sha256(json.dumps(plan)).hexdigest()[:16]`、`content_chars`、`source_epoch`。
用于跨 epoch **字节相等**断言（工单 1 的自动化版本）。

### 2.4 臂分配（epoch-7 固定 50/50，测量模式）
- 新增 `ROUTER_MODE = measurement|production`（env 开关）。
- measurement：`arm = "precedent-assisted" if blake2b(task_id, salt) 的奇偶 else "direct"`；
  **不调用 Thompson、不 update route_params**（测量与学习分离，治 F1 的选择偏差）。
- production：维持 Thompson（现行为）。

## 3. 迁移与前置
- epoch-6：**direct-only 干净基线**（新埋点先落地，基线重测）——不需要本选择器。
- epoch-7：启用本选择器 + 固定 50/50，正式回答命题一。
- schema 变更需交 MR-1（代码+证据）；快照需在 epoch-6 前冻结一次以生成 epoch-7 的先前库。

## 4. 验证（实施时）
1. 复制 epoch 上同一任务 `content_sha256_16` 必须相等；不等则算法非确定，阻断。
2. 断言注入先例 `req_id` ≠ 紧邻上一任务（除非恰为同族）。
3. 单测：`precedent_skip` 在无同族时产生且不污染消息。
4. 回归：direct 臂无 `precedent_injected` span（已是现状）。

## 5. 风险
- 同族先例长期为空 → 命题一退化为"无可注入"；需在 epoch-7 前确认各族至少一条**先前**沉积（否则先跑一个"播种"epoch）。
- 快照与主表漂移 → 只读快照 + 哈希校验。
