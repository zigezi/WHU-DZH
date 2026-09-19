# Phase P5a.8 证据 — updater 结果裁决（第 1 步：补证据）

- 生成时间：2026-09-15T13:56:54+08:00  分支：simple-agent @ a347126

## 1. span_id 证明：epoch-3-proposal.json 前 3 条原文

```
{"type": "threshold_patch", "target": "monitor/elayer", "root_cause_layer": "E", "evidence": ["e48a27b1-7d75-48ea-a920-1fa41b198201", "c5671275-80c9-478c-96ed-328c76fa2ee6", "3797442e-2d5b-4b83-9a91-89b0343a01f5", "d57f55c0-5d07-4d4d-84f0-831ff7425e46", "L002", "C002", "E002"], "span_ids": ["c5671275-80c9-478c-96ed-328c76fa2ee6", "3797442e-2d5b-4b83-9a91-89b0343a01f5", "d57f55c0-5d07-4d4d-84f0-831ff7425e46"], "suggested_value": null, "confidence": 0.3333, "req_id": "TAU-A-000", "loss": 1.0}
{"type": "prompt_hint", "target": "monitor/llayer", "root_cause_layer": "L", "evidence": ["61a243dc-8740-4e05-9c1f-0162bbcef63a", "4b5298f0-9960-467f-9418-7def9b074a4a", "af99aedb-470f-4a35-a31d-f8cdab5b7f24", "b4d1582f-ba20-46a0-b4ee-d018efd78800", "L001", "L002", "C002", "E002"], "span_ids": ["4b5298f0-9960-467f-9418-7def9b074a4a", "af99aedb-470f-4a35-a31d-f8cdab5b7f24", "b4d1582f-ba20-46a0-b4ee-d018efd78800"], "suggested_value": null, "confidence": 0.6, "req_id": "TAU-A-002", "loss": 1.0}
{"type": "prompt_hint", "target": "SYSTEM_PROMPT", "root_cause_layer": "C", "evidence": ["fc041a8e-e438-4fe3-bc33-36f858d8e2c3", "43949016-8634-4c8e-9214-84455f4a6509", "81b6775e-17f1-4117-b93e-a331d2fc80ef", "329214f8-6d08-4d34-a123-83a297ac54c1", "C002"], "span_ids": ["43949016-8634-4c8e-9214-84455f4a6509", "81b6775e-17f1-4117-b93e-a331d2fc80ef", "329214f8-6d08-4d34-a123-83a297ac54c1"], "suggested_value": null, "confidence": 1.0, "req_id": "TAU-A-007", "loss": 1.0}
```

### span_ids 全部可解析（36/36 非空；108 个 span_id 全部命中 trace.db）

```
non-empty span_ids proposals: 36 / 36
span_ids total=108 missing=0
# 抽样解析：
c5671275-80c9-478c-96ed-328c76fa2ee6|E|sandbox_exec|tau__calculate
4b5298f0-9960-467f-9418-7def9b074a4a|L|step|步骤17
43949016-8634-4c8e-9214-84455f4a6509|C|llm_call|LLM推理
```

## 2. updater 成本汇总（¥10 上限执行情况）

```
{"updater_llm_tokens": 0, "note": "updater 使用确定性 Shapley 归因（anomaly 规则 + 边际贡献），无 LLM 调用，token 消耗为 0", "budget_cny": 10.0, "spent_cny": 0.0}
# 记入 spans：
updater-epoch-3|updater_run|{"updater_llm_tokens": 0, "proposals": 36, "budget_cny": 10.0, "spent_cny": 0.0}
updater-epoch-3|updater_run|{"updater_llm_tokens": 0, "proposals": 36, "budget_cny": 10.0, "spent_cny": 0.0}
```

## 3. 裁决要点确认（合规边界，本次不越线）

- 红线：worker 的 system prompt 含 get_wiki 注入的 τ wiki 段——**评测环境资产，不可改**；本次未改任何 system prompt。
- threshold_patch（9 条）：全部暂缓，未动 guard 阈值。
- 归因器输出：25/9/2 为**未验证启发式**，仅用于提案定向；本证据不将其作为真实根因分布引用。

## 4. 下一步（未完成，按裁决顺序）

- 第 2 步：起草 SYSTEM_PROMPT 修改建议（不直接改）+ 段落归属 + wiki 不触碰证明 → 交作者审
- 第 4 步：签名归一化补丁（族数 10~30、最大族<30%、每族≥3）、prompt_cache_hit/miss_tokens instrumentation

---

## 5. 第 2 步：SYSTEM_PROMPT 修改建议草稿（未应用）

- 产出：`.agent/proposals/epoch-3-prompt-draft.md`
- **关键事实**：τ 模式 system prompt = wiki 全文（`dialogue_driver.py:99` + `worker.py:279`），**不存在 worker 自有段**。
- 因此 25 条 SYSTEM_PROMPT 提案**没有合法直接落点**；合规改法只能是"新增独立 worker 自有段"，wiki 逐字节不动。
- 草稿含：wiki 基线 sha256、分隔标记方案、wiki 不触碰证明方法、5 条候选 worker 规则（方向性、未验证）、红线边界。
- 状态：**待作者审阅圈定生效子集（第 3 步）**，未改任何 system prompt。
