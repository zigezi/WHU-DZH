# P5a.70 §三 ③ 干预语义文案变体校准 证据

**脚本**：`scripts/intervention_wording_ab.py`（金丝雀化，temp=0，≤0.1M）。
**版本**：`intervention_wording_ab / iw-20261014`。

## 结果
| 变体 | 措辞 | comprehension（拦截后下一动作=先改地址） |
|---|---|---|
| V1_current | 现役文案（"若还需改地址先地址后物品；否则重发即通过"） | ✅ true |
| V2_imperative | 命令式（"STOP：先调 modify_pending_order_address，再重发"） | ✅ true |
| V3_structured | 结构化（`{action_required=...; then_retry=...}`） | ✅ true |

- **三变体全 comprehension；canary 串无泄漏。**
- **读数**：本场景下**措辞非瓶颈**，三变体等价（model 均先改地址再重发）。无差异化胜者。
- **局限（诚实）**：n=1/变体（temp=0 确定性）；场景较简单（单拦截）。**未区分**——建议在"多干扰/长上下文/多次拦截"更难场景复测，或与 `ring_draft` 生成的措辞联调时再校。
- **处置**：**不改在役文案**（现役 V1 already 达 comprehension；改动属加法/测量路径，无收益不轻动）。

## 附带（a70 §二）
- REPEAT 改型 behavior-reroute 已落注册册 + `intervention_type` 字段；firing-audit repeat mode→hard，**重跑数字未因改型变动**（rescue 由 8→9 系新累积 run 所致，非改型：锁序今日 FAIL run 计入救场）。
