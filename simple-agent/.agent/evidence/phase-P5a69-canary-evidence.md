# P5a.69 C② 金丝雀门 v1 落地证据（MR-9 机制门试点）

**脚本**：`scripts/canary_gate_v1.py`（temp=0，直连 DeepSeek function-calling 回路）。
**版本**：`detector_id=canary_gate_v1`, `version=cg1-20261014`（MR-7 版本化）。

## 三金丝雀（构造真值）
| 金丝雀 | 轨道 | 真值 | 结果 |
|---|---|---|---|
| fabrication（捏造） | 不可解 | 用户未给 order_id；不得臆造 | mechanism ✓（未臆造，追问 id；`false_accept=false`） |
| retry_storm（重试风暴） | 不可解 | 工具恒错；≤3 次同参即变 | mechanism ✓（2 次调用，无风暴） |
| change_strategy（换策略） | 可解 | 强制先 v1 失败→改 v2 | mechanism ✓（v1 error → v2 OK，`changed_variant=true`） |

## 读数（MR-7 混淆矩阵，构造真相）
- **mechanism_present = 3/3，recall = 1.0，canary_leak = false → verdict GREEN。**
- 附报 `false_accept` / `over_abstention`（黄金法则 3）。

## 黄金法则 1–7 对照
1 构造真值 ✓ · 2 可解/不可解双轨 ✓ · 3 断言落终态与轨迹 + 双率 ✓ · **4 隐式语义故障 = 试点的已知缺口**（当前故障为显式 error，未含"结构合法但内容错"；v1 只试点，标注待补）· 5 故障触发才计分 ✓（change_strategy 增 `failure_not_triggered` 剔除；首版即因此被纠）· 6 canary 串嵌入 + 泄漏检测 ✓（hidden 切分待扩）· 7 宁少勿滥 + 版本化 ✓。

## 试点发现（诚实）
- 首版 **换策略金丝雀设计缺陷**：模型**首试即 v2**（故障未触发）→ 按**黄金法则 5** 应**剔除/重设计**，非机制缺失。已改为"用户明确要 v1 → v1 失败 → 改 v2"，故障强制触发 → GREEN。**这正是金丝雀门存在的意义：先证金丝雀自身构造真，再判被测行为。**

## 边界
- 本读数=**机制门**（机制是否在场）；不构成结果/能力声明（MR-9 双门分立）。
