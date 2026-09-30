# P5a.19 工单 1 & 3 — precedent 注入取证（只读）

**结论**：A-008 两 epoch 注入的是**两份不同的先例记录**，差异源于"动态取最新先例"，**不是截断**。
工单 3 的 precedent `3d05a416ea71` 实为 **TAU-R-102 的工具序列 plan**，不含任何"item 修改后锁定"文字结论。

## 1. 注入选取逻辑（代码）

`backend/worker.py:154-179` `_inject_precedent`：

```python
best, sim = None, 0.0
for p in trace_store.list_precedents():
    s = 1.0 if p.get("sig") == sig_family else \
        signature.similarity(req.content, p.get("content") or "")
    if s > sim:
        sim, best = s, p
...
summary = json.dumps(best["plan"], ensure_ascii=False)[:2000]   # ≈500 token 上限
tokens_injected = len(summary) // 4
```

`backend/monitor/trace_store.py:389-395` `list_precedents`：`ORDER BY id DESC LIMIT 500`。

**关键事实**：所有 τ REQ 的 `req.content` = `"你好，我需要帮助"`（req JSON `task` 字段，占位开场白），
而 `_store_precedent`（`worker.py:136-151`）存的 `content` = 同样的 `req.content`。
因此对任何 τ 任务，遍历中**每个先例的 similarity 都是 1.0**（`if s > sim` 严格大于），
`best` = **id 最大的先例** = 上一个完成任务的 plan，与任务族无关。

## 2. 工单 1：A-008 两 epoch 注入原文 diff

span `precedent_injected`（两 epoch 都报 `precedent_sig=1932cfe427b1`, `similarity=1.0`）：

| epoch | trace_id | tokens_injected | 被注入先例 id | 先例 req_id | plan_bytes | summary=plan[:2000] |
|---|---|---|---|---|---|---|
| 4 | 2b4917e1-a358-4807-9034-4031ef7e5c0a | 436 | 305 | TAU-A-**007**(e4) | 1744 | 436 = 1744//4 |
| 5 | f854dfb5-60ed-413e-8af2-6a5c5b08665c | 213 | 439 | TAU-A-**007**(e5) | 852 | 213 = 852//4 |

- 两先例 `sig` 相同（1932cfe427b1，均为 A-007 的签名），但 **plan 不同**（A-007 两个 epoch 各跑一次，工具序列长度不同）。
- 注入的是"紧邻上一个任务"，即 A-008 之前刚跑完的 **A-007**（`id` 相邻：305 前于 306，439 前于 440）。
- **非截断**：`tokens_injected` 精确等于 `len(plan_json[:2000])//4`，两次都在 2000 字符上限之内。

**对 P5a.19 F2 的确认**：`tokens 436 vs 213` = 两份不同先例，非注入模板截断。
**升级点**：F2 描述的"随先例库累积而变"更准确地说是**恒取 id 最大者**（相似度恒 1.0 的并列），
因此 precedent-assisted 臂实际注入的是"上一个任务的工具序列"，**语义相关性不成立**（构造效度问题）。

## 3. 工单 3：precedent `3d05a416ea71` 原文核查

R-105 两 epoch 注入同一 `precedent_sig=3d05a416ea71`、`tokens_injected=281`：

| epoch | trace_id | 注入先例 id | 先例 req_id | plan_bytes |
|---|---|---|---|---|
| 4 | ca1ff8d1-78c6-4654-bffd-4701bd80e32b | 425 | TAU-R-**102**(e4) | 1127 |
| 5 | fa73670f-2d57-4417-ae71-8c92fda68aaa | 559 | TAU-R-**102**(e5) | 1127 |

- `281 = 1127//4`，两 epoch 内容一致（R-102 两 epoch plan 恰好都 1127 字节）。
- 该先例是 **R-102 的工具调用计划**，序列为：
  `find_user_id_by_name_zip → get_user_details → get_order_details ×3 →`
  **`modify_pending_order_address`（#W4219264） → `get_product_details` → `modify_pending_order_items`（#W4219264）→ …**
- 它**只含工具序列，不含任何文字结论**；其中地址修改排在 item 修改**之前**（与 R-105 GT 同序）。

**裁决含义**：R-105 e5 的"未试先拒（断言地址不可改）"**不能**归因于该先例的"文字结论"——
先例无此文字；其序列反而展示了"先地址后 item"的正确顺序。
P5a.16 §2.3 提出的"沉积物以传闻形式起效的正面案例"在此**证据不足**。

## 4. 复现

```bash
# 被注入先例原文
sqlite3 -readonly backend/logs/trace.db \
 "SELECT id,req_id,sig,plan_json FROM precedents WHERE id IN (305,439,425,559)"
# 注入 span
sqlite3 -readonly backend/logs/trace.db \
 "SELECT trace_id,attributes FROM spans WHERE type='precedent_injected' \
  AND trace_id IN ('2b4917e1-a358-4807-9034-4031ef7e5c0a','f854dfb5-60ed-413e-8af2-6a5c5b08665c', \
  'ca1ff8d1-78c6-4654-bffd-4701bd80e32b','fa73670f-2d57-4417-ae71-8c92fda68aaa')"
```
