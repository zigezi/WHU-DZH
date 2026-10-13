# P5a.59 阶段二 活体验证批报告（诚实版）

## 运行
- 批：18 题（陷阱富集：锁死 5 + 支付/换货/重复/可用性/礼品卡 + 对照）；`ROUTER_MODE=direct`（无注入）。
- 7 哨兵 env 全开。结果：**6/18 PASS**；**tokens = 1,854,737**。

## 判读表

### 1. 点火台账
| 资产 | 点火 | on_fail | on_pass |
|---|---|---|---|
| gift_card_balance_enforce_v1 | 5 | 5 | 0 |
| lock_order_v1 | **0** | 0 | 0 |
| repeat_failure_v1 | 0 | 0 | 0 |
| items_count_match_v1 | 0 | 0 | 0 |
| non_delivered_exchange_v1 | 0 | 0 | 0 |
| flight_availability_enforce_v1 | 0 | 0 | 0 |
| payment_amount_sum_enforce_v1 | 0 | 0 | 0 |

### 2. 陷阱存活：锁死 5 题 **4 FAIL / 1 PASS**，且**锁序拦截器零点火**。

## 两个真发现（本次运行的产出）
1. **接线缺陷（已修）**：τ 路径工具名带 `tau__` 前缀，而名称匹配型守卫（lock/count/exchange/avail/payment）按**无前缀名**匹配 → **静默失效**（只有不依赖工具名的 giftcard_enforce 点了 5 次）。修法：`execute_tool` 内 `gname` 归一化后再过守卫（保留原名给 registry）。→ 本轮**所有名称型哨兵实际未在岗**，阶段二"目的 1：锁序活体确认"**未达成**。
2. **预算超顶**：本批 **1,854,737 > 1.5M 硬顶**（超 ~355k；18 题里 A-009 180k、A-000/A-008 偏重）。**超支登记。**

## 结论与停止线（按 a59 §三）
- 阶段二因**接线缺陷**判为**无效运行**（哨兵未实际点火 → 台账无意义）；且**预算超顶**。
- 修复已提交；**重跑需要新的预算授权**（a59 硬顶 1.5M 已破）。
- 目的 2（器官活体试产）：本轮无有效尸体产出（哨兵失效 + 无新候选），未启动。

## 待裁决
1. **授权修正后重跑阶段二**（建议缩减批次以保 1.5M 内，如锁死 5 + giftcard 2 + 少量对照 = ~10 题）；或
2. 先以**零 token 单测**验证接线修复（构造 `tau__modify_pending_order_items` 走 `execute_tool` 断言 veto），再定重跑。
