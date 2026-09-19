# P5a.10 — P1-P5 子集圈定 + epoch-4 解锁

> 作者裁决，基于 .agent/evidence/phase-P5a9-evidence.md 中的草稿全文（commit 37db7c7）。
> 前置检查单至此全绿，epoch-4 解锁。

---

## 一、结构改法批准（维持 P5a.9 §二）

- 批准"新增 [WORKER-OWN POLICY] 段"结构：wiki 逐字节不动（airline sha256=56c33580...、retail sha256=d539fd2a... 为基线），POLICY 段追加于 wiki 之后，policy_id=md5(段文本)[:12]，注入写 policy_inject span。
- 实现位置：dialogue_driver.py 取 wiki 后拼接，worker.py 不改。

## 二、P1-P5 逐条裁决

| 规则 | 裁决 | 理由 |
|---|---|---|
| P1 先确认再动作 | 🔶 修正后生效 | 修正：复述关键参数必须与工具调用同轮完成（content 携带核对 + 同轮 tool_call），**禁止为确认单独占一轮对话**（纯文本轮 = RESPOND = 白烧一轮并扰动模拟用户） |
| P2 不臆造信息 | ✅ 生效 | 通用纪律，零额外轮次成本 |
| P3 上下文自摘要 | ❌ 作废 | 模型无法压缩自身上下文，属代码层功能非提示词规则；写入 prompt 只会诱导空摘要烧 token。转入 backlog：worker 上下文压缩特性另立任务书 |
| P4 结束即止 | ✅ 生效 | 对准 epoch-3 对话爆炸成本异常（mean/median 差 8 倍） |
| P5 工具失败换策略 | ✅ 生效 | guard 熔断指纹在提示词层的软前置，与现有机制同向 |

## 三、POLICY v1 定稿

- 生效子集：{P1（修正版）, P2, P4, P5}，policy_version=worker-policy-v1。
- 打包是有意的：epoch-4 双门只判定"POLICY 段整体有效性"，不判定单条贡献；若 REJECT 再消融，不预烧逐条臂。
- 应用方式：人工应用，单独 commit，message 尾部回填 Loss-Before/After（按 opencode 既有惯例）。

## 四、epoch-4 执行参数（解锁）

- `eval_loop.py --epoch 4 --tau-only --split train --tag tau-`，135 任务，双臂（direct / precedent-assisted）与 dev 锁定不变；
- 成本护栏 ¥50/日，预估 ¥20±5，超预估 50% 自动停；
- `epoch_gate.py tau-epoch-3.json tau-epoch-4.json`（基线 = epoch-3，唯一变更量 = POLICY v1）；
- 报告除既有三项外新增一条：**policy 段的 prefix cache 覆盖验证**——POLICY 段加入后 llm_call span 的 hit/miss 比不应显著恶化（POLICY 与 wiki 同为静态前缀，应被缓存覆盖）；若 hit 率显著下降，需在报告中解释。

## 五、明确不做（维持）

不重跑 epoch-2/3；不动 reward 权重与 guard 阈值；不引入新依赖；threshold_patch 类提案继续冻结；P3 仅入 backlog 不实施；归因命中率、AUROC2 继续挂起。
