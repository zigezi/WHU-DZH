# P5a.9 — P5a.8 第 1/2 步验收 + epoch-4 前置授权

> 作者裁决，针对 commit cd4ad5c（补证据）与 ae61c5d（SYSTEM_PROMPT 草稿，未应用）。

---

## 一、第 1 步（补证据）：验收通过

- 36/36 提案 span_ids 非空，108 个 span_id 在 trace.db 全命中（missing=0），前 3 条原文已入证据 ✅
- updater 为确定性 Shapley（无 LLM），tokens=0、spent=¥0/¥10，cost 字段已写入提案文件并落 updater_run 0 层 span ✅
- 定级备注：提案为归因模板生成的方向性提示（非 LLM 诊断），维持 P5a.8 第五节"启发式、不得作为真实根因分布引用"的定级。

## 二、第 2 步（草稿）：架构批准，内容待审

1. **结构事实确认**：τ 模式 system prompt = wiki 全文（dialogue_driver.py:99 → worker.py:279），worker 自有段不存在。P5a.8 §3 在现状下无合法落点，25 条 SYSTEM_PROMPT 提案维持作废，直至 POLICY 段落地。
2. **批准 [WORKER-OWN POLICY] 追加架构**：wiki 之后新增带分隔标记的 POLICY 段，wiki 逐字节不动，sha256 基线 + injected.startswith(wiki) 作为不触碰证明。
3. **新增要求——POLICY 段版本化**：policy_id / 内容 hash 必须记入 spans，使 epoch 间通过率变化可归因到具体策略版本。无版本化的 POLICY 段不得上线。
4. **第 3 步（作者圈定生效子集）阻塞中**：opencode 需贴出 .agent/proposals/epoch-3-prompt-draft.md 全文（至少 P1-P5 完整条文 + 不触碰证明段落），作者审阅后圈定子集。P1-P5 当前定级：方向性、未验证。

## 三、第 4 步授权：两项 epoch-4 前置立即执行（不依赖第 3 步）

1. **签名归一化补丁**：per-instruction hash 过细，改粗粒度族聚类（实体归一化后 md5，或 GT 动作类型序列签名，二选一取实现简单者，证据中说明选型理由）。
   - 验收：135 任务 → 族数 10~30；最大族占比 <30%；每族 ≥3 任务。
   - 红线不变：instruction 明文（含归一化后明文）禁入 worker 历史、span 属性、证据文件，只存 md5。
2. **cache instrumentation**：确认 DeepSeek 是否返回 prompt_cache_hit_tokens / prompt_cache_miss_tokens，接入 spans 埋点（不加新依赖，仅多存 int）。若 API 不返回，如实报告"不可得"并关闭此项，不得伪造。

## 四、解锁条件（维持）

epoch-4 启动需全部就绪：
- [ ] 第 3 步：作者圈定 P1-P5 生效子集，POLICY 段（版本化）落地
- [ ] 签名归一化验收通过
- [ ] cache instrumentation 落地或确认不可得
- [ ] epoch-4：eval_loop.py --epoch 4 --tau-only --split train --tag tau-，¥50/日护栏，epoch_gate 对 tau-epoch-3.json

## 明确不做（维持）

不重跑 epoch-2/3；不动 reward 权重与 guard 阈值；不引入新依赖；threshold_patch 类提案继续冻结；归因命中率、AUROC2 继续挂起。
