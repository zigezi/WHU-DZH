# P5a.19 第 1 批 + 工单 1 取证 — 证据包（只读）

**依据**：`P5a.19-路由取证确认与聚合暂定降级裁决.md` §三（序 1/2/6 立即开工）
**性质**：离线、只读；不改测量路径；未提交任何 span/worker 历史（红线不变）
**日期**：2026-09-25

## 交付清单

| 工单 | 文件 | 状态 |
|---|---|---|
| 1 & 3 | `.agent/evidence/p5a19/w01-w03-precedent-injection.md` | 完成 |
| 2 | `.agent/evidence/p5a19/w02-lock-order-probe.md` | 完成 |
| 4 | `.agent/evidence/p5a19/w04-gt-export.md` | 完成 |
| 6 | `.agent/evidence/p5a19/w06-e2-vs-e3-config.md` | 完成 |
| — | 本索引 | — |
| 5 | acceptance_check 字段级 diff 埋点 | 未开工（属 §三 序 5，下一次 epoch 前） |
| 3(全量) | 第 0 步机器初筛 | 未开工（属 §三 序 3，需先出筛查器设计） |

> **红线冲突（需仲裁）**：工单 4 要求"instruction 明文入证据包"，与 P5a.6/P5a.9 红线
> "instruction 明文禁入 evidence 文件"冲突。本批按红线处理：instruction 明文放**未跟踪**
> `.agent/local/p5a19-gt-instructions.md`（`.gitignore` 命中），tracked 证据只含 GT actions/outputs/评测语义与派生结论。
> 如需明文入库，请显式覆盖红线。

## 执行摘要（每条一行）

1. **工单 1（A-008 注入 diff）**：e4 注入 `id=305`（A-007 e4 计划，1744B→436tok），e5 注入 `id=439`（A-007 e5 计划，852B→213tok）。
   **非截断**；根因是"相似度恒 1.0（所有 τ content 相同）+ `ORDER BY id DESC` → 恒取最新先例"。
   → precedent-assisted 臂实际注入"上一个任务的工具序列"，语义相关性不成立（构造效度问题）。
2. **工单 3（precedent `3d05a416ea71`）**：实为 **TAU-R-102** 的 plan（1127B，两 epoch 一致，281tok）。
   仅含工具序列，**无**"item 修改后锁定"文字结论；其序列反而是"先地址后 item"。
   → P5a.16"沉积物起效正面案例"**证据不足**。
3. **工单 2（锁序）**：**实证**。`items` 把状态改 `pending (item modified)` → `address` 报 `non-pending order cannot be modified`。
   address→items 成功；items→address 失败。GT 为 address→items。R-105 两 epoch 均 items-first → 双败，**常量**。
4. **工单 4（GT）**：评测为**最终 DB 状态哈希相等** + output 子串。
   - A-008：GT **3 名乘客**；e5 模拟器"just Mohamed"违背 GT → 不可赢（P5a.16 证实）。
   - A-019：GT 返程 **HAT033 / 2024-05-19**、航点 **JFK**；模拟器要 5/20、DTW–LGA → 均违背 GT（P5a.16 证实）。
   - R-105：GT **含** Backpack 退货 → **P5a.16"GT 无 backpack"证伪**；真正缺口是 instruction 另要求退 Jigsaw，
     而 **GT actions 未含**（instruction ⊋ GT）→ 跟随指令即多改 DB 致 FAIL，**任务定义级缺陷**。
5. **工单 6（e2 vs e3）**：e2 = **direct-only + 1 个退化签名**；e3 = 135 签名 + 双臂。**不可比**；
   "e2 异常"是仪器替换。且 e2→e3 新增的 precedent 臂（见 1/3）本身可能是下降候选因。

## 对既往裁决的净影响

- **三案（A-008/A-019/R-105）全部为线束/任务定义缺陷**，非 worker/POLICY 变更点 → 支持 P5a.16 隔离处置（结论不变，证据加强，并修正两处细节：backpack 在 GT；jigsaw 才是缺口）。
- **POLICY v1"暂定"** 维持；本轮**未**产出可恢复 confirmed 的证据。
- **precedent-assisted 臂**：构造效度存疑 + 两 epoch 注入内容不同 → 臂级结论应再降置信；测量模式（P5a.19 §四）落地前不得用于因果。

## 待办（需仲裁/授权）

1. 工单 5：`acceptance_check` 携带 GT-vs-final 字段级 diff 的设计（P5a.19 §四 要求先交一页设计便签）。
2. 第 0 步机器初筛器设计（机器只产"候选隔离+理由"，人审签字后才约束）。
3. 红线覆盖决定（工单 4 instruction 明文是否入库）。
