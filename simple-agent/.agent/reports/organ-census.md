# 全尸体普查报告（P5a.63 §二，零 token）

**对象**：962 run 的全部历史 FAIL 尸体（ring_draft 禁用，纯静态）。

## 结果
| 指标 | 值 |
|---|---|
| 尸体数（去重 (req,小时)） | **274** |
| 处置分布 | decompose **233** / deploy **27** / reject **14** |
| 命中现有守卫死因（covered_by_existing） | 7 簇（见下） |
| **器官新提名（deploy_new）** | **0** |

**敏感性（8 簇核对）**：lock_order ✅ / repeat_failure ✅ / items_count ✅ / non_delivered ✅ / payment_sum ✅ / flight_availability ✅ / gift_card_balance ✅ / **certificate_update = n/a（历史 259 尸体中无 certificate 尸体）** → **7/7 实测，无 MISS**。
**特异性**：deploy_new **0 件**，deploy 率 **0.0% ≤ 2%**（预注册合格线 ✓）。

## 判定
- **census_clean = True**（敏感性达标 ∧ 特异性达标 ∧ 零新提名）。
- 按 a63 §三：**封线条件满足**（τ 主动线可由"冻结未封"转"封线，纯哨兵背景模式"）——**封线与否为裁决人权柄**，本报告只呈数据。
- 备注：deploy 27 件全部 **covered_by_existing**（命中现有 7 簇），故 `deploy_new=0`；若不做 a62 §一 拆分，器官产能账会虚增 27——微修已落。

## 与 a62 §三 越界的关系
a62 §三"矿脉枯竭"基于 18 具**陷阱富集**样本，被 a63 判统计越界。本普查用**全 274 具**（非选择性）复核：**零新提名**——枯竭命题在全样本上仍成立（但仅就"现有哨兵死因覆盖 + 当前语料"而言）。
