# P5a.56 落地证据：首起资产撤销 + 判据细化 + 谓词两型原型

## 案 1：certificate_update_v1 撤销（首起资产撤销）
- `provenance.revoke()` → status=**revoked**，reason=行为改道型误伤+点火必要条件不可观测，knowledge_moved_to=negative_precedents。
- 死因知识保留在 L1.5 负先例册（`tool_error:certificate cannot be used`）。
- **新出生要件（可观测性证明）**：B-3 增 `observability_proof` 字段；谓词点火条件须可由 args/可观测状态确定性计算，否则不予出生（追溯解释 gift_card 覆盖缺口只能登记）。

## 案 2：lock_order_v1 良性再发重分类
- 税负：**118/962 ≈ 12.3%**（每首个改物品一步否决税）入册。
- 电池补案（N6）：**"本任务无需改地址"** 真实合法形状 → 首次否决、重发通过（结局保持）；电池 **8/8**。
- 结局保持性静态不可证 → 留待在役干预日志。

## 案 3 + §二：判据细化（干预语义分级）与升级
- 审计器 `firing_audit.py` 增 `mode ∈ {benign, hard}`：benign 记税、hard 记硬线。
- 复跑（962 run）结果：
  - **硬线违例：仅 certificate_update_v1**（已撤销）；其余全 0。
  - rescue：lock_order 6 / items_count 1 / non_delivered 1（**总救场 8**）。
  - benign 税：lock_order 118（12.3%）；enforce 原型 46（4.8%）。

| 资产 | mode | rescue | cov | 升级 |
|---|---|---|---|---|
| lock_order_v1 | benign | 6 | 1.0 | **field_validated(static)** |
| items_count_match_v1 | hard | 1 | 1.0 | **field_validated(static)** |
| non_delivered_exchange_v1 | hard | 1 | 0.5 | **field_validated(static)** |
| repeat/payment/availability/giftcard | — | 0 | 0.0 | 维持 T1_candidate（盲区入册） |
| certificate_update_v1 | hard | — | — | **revoked** |

## §三：谓词两型立法 + 前置强制型原型（授权试产）
- 两型：**观测依赖型**（需先验观测，盲区天生，误伤零）/ **前置强制型**（未观测即否决 + 良性再发）。
- 原型 `flight_availability_enforce_v1`：book/update 前无本 run 可用性观测 → 否决"先查座位，查完重发即通过"（once-per-key）。
  - 电池 6/6（含 N2 重发通过、N3 已查不足仍拦）；C-1 PASS；审计良性（0 硬线，税 46）。
  - 桌面审查给出可观测性证明（点火=观测缺失，可判定）。
- payment_sum / gift_card **不跟进**（待原型审计结论）。

## 资产库
**在役 8（1 撤销，共登记 9）**；τ 采收季**收官，转哨兵模式**：日志自然累积、不再主动开挖。
