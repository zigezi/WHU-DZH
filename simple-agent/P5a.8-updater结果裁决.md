# P5a.8 — updater 运行结果裁决（commit a347126）

> 作者裁决，针对 opencode 的 updater 运行报告（36 失败 → 36 提案，.agent/proposals/epoch-3-proposal.json）。
> 与此前文件冲突处以本文件为准。

---

## 一、合规确认（通过项）

- 只出提案未自动改资产 ✅（v1 铁律遵守，产出在 .agent/proposals/）
- suggested_value 全为 null ✅（诊断给方向、取值待人工，边界正确）
- 36 失败 → 36 提案，数量一一对应 ✅

## 二、证据缺失（补齐前本次 updater 运行不算交付完成，MR-1）

1. **span id 证明**：贴出 epoch-3-proposal.json 的前 3 条原文，证明每条提案的 span_id（或等价字段）存在且非空。数量对应 ≠ 逐条挂证。
2. **updater 成本汇总**：裁决 4 约束 3 要求 updater 自身 token 消耗记入 spans 并在提案文件末尾汇总（¥10 上限执行情况）。当前报告完全缺失，必须补。

## 三、SYSTEM_PROMPT 提案红线（25 条 prompt_hint 适用）

worker 的 system prompt 含 get_wiki 注入的 τ-bench wiki，**wiki 段是评测环境资产，不是本系统资产**：

- 凡提案/草稿触及 wiki 注入段，一律作废；
- 只允许修改 worker 自有行为指令段（本系统 L/C 层提示词）；
- 后续起草的每条修改建议必须标注改动落在哪一段，并给出不触碰 wiki 段边界的证明（如贴出段落分隔标记）。

## 四、threshold_patch 类提案（9 条）全部暂缓

- P5a.7 已裁决不动 guard 阈值，此处维持并扩大至全部阈值类提案；
- 理由：阈值改动无金种子无法验证，放松阈值会制造双门检不出的通过率虚高；
- 解冻条件：replay.py 金种子工厂就位后另立任务书重审。

## 五、归因器输出定级

 updater 内部 Shapley 归因器的 25/9/2 根因分布（SYSTEM_PROMPT / elayer / llayer）为**未经验证的启发式输出**（对照 Who&When SOTA 14.2%），仅可用于提案定向，**禁止作为真实根因分布引用**到任何报告或证据文件。

## 六、下一步顺序（epoch-4 仍被前置检查单阻塞，不得跳过）

1. 补第二节两项证据；
2. 按提案高频模式起草 SYSTEM_PROMPT 修改建议（不直接改），每条标注段落归属 + wiki 段不触碰证明；
3. 草稿交作者审阅，圈定生效子集；
4. 完成 epoch-4 前置检查单剩余两项：签名归一化补丁（族数 10~30、最大族 <30%、每族 ≥3）、prompt_cache_hit/miss_tokens instrumentation 确认；
5. 以上全部完成后才解锁 epoch-4（eval_loop.py --epoch 4 --tau-only --split train --tag tau-，¥50/日护栏，epoch_gate 对 tau-epoch-3.json）。

## 明确不做（维持）

- 不重跑 epoch-2/3；不动 reward 权重与 guard 阈值；不引入新依赖；
- 归因命中率、AUROC2 继续挂起，等 replay.py 金种子工厂与 OOD 标签。
