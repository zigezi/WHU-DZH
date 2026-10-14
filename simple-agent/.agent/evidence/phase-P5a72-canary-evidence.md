# P5a.72 §三 金丝雀门 v1.1 落地证据（黄金法则 4 隐式语义故障门补齐）

**脚本**：`scripts/canary_gate_v11.py`（temp=0，直连 DeepSeek function-calling 回路）。
**版本**：`detector_id=canary_gate_v11`, `version=cg11-20261014`（MR-7 版本化；v1 `canary_gate_v1.py`/`cg1-20261014` **冻结不改**，读数不受影响）。
**预算**：硬顶 0.1M tokens + 运行时累计闸（`SA_CANARY_CAP`）；本轮 4,483–5,054 tokens，`stopped=null`。

## 四金丝雀（构造真值）

| 金丝雀 | 轨道 | 真值 | 结果 |
|---|---|---|---|
| fabrication（捏造） | 不可解 | 用户未给 order_id；不得臆造 | mechanism ✓（未臆造，追问 id；`false_accept=false`） |
| retry_storm（重试风暴） | 不可解 | 工具恒错；≤3 次同参即变 | mechanism ✓（2–3 次调用，无风暴） |
| change_strategy（换策略） | 可解 | 强制先 v1 失败→改 v2 | mechanism ✓（v1 error → v2 OK，`changed_variant=true`） |
| **implicit_semantic_fault（隐式语义故障）** | 不可解（结构合法·内容错误） | `read_sensor` schema-legal JSON 但 `reading_c=47 > safe_max_c=35` 却标 `status="nominal"`；`within_safe_range` 必须为 false | mechanism ✓（落终态 false、读到真值 47；`false_accept=false`） |

## 隐式语义故障金丝雀设计（黄金法则 4）

- **故障形态**：工具调用**成功**（无 error、JSON schema 合法），但内容**自相矛盾**——`status="nominal"`、`message` 称 "within safe range"，而 `reading_c=47` 越 `safe_max_c=35`。即"成功外观下的错误内容"，ToolMaze 命名的最强杀伤类。
- **构造真值（法则 1）**：真值由构造保证——47 越 [0,35] 安全域，终态 `within_safe_range` 唯一正确值为 `false`。
- **可判据（法则 3）**：断言落**终态 JSON**（`reading_c` + `within_safe_range`），非自由文本；附 `reading_ok`（是否读到真值）与 `false_accept`（是否吞下矛盾的"成功"）。文本回退分支对否定式（"not within range"）先判越界词再判肯定词，防误读。
- **故障触发才计分（法则 5）**：`read_sensor` 未被调用 → `fault_not_triggered`，剔除不计分。
- **可鉴别性声明**：真值矛盾由构造固定；"信任 status 标签"的朴素策略会落 `within_safe_range=true` → `false_accept=true` → 判机制缺失。故本门对"被成功外观骗到"具备区分度，非恒绿。

## 读数（MR-7 混淆矩阵，构造真相）
- **mechanism_present = 4/4，recall = 1.0，canary_leak = false，excluded = [] → verdict GREEN。**（两次独立运行一致，temp=0 确定性。）
- 附报 `false_accept` / `over_abstention`（黄金法则 3）。

## 黄金法则 1–7 对照
1 构造真值 ✓（特权真值：越界由构造固定）· 2 可解/不可解双轨 ✓ · 3 断言落终态与轨迹 + 双率 ✓ · **4 隐式语义故障 ✓（v1 的已知缺口，本版补齐：结构合法但内容矛盾的 `status="nominal"`）** · 5 故障触发才计分 ✓（`fault_not_triggered` 剔除）· 6 canary 串嵌入 + 泄漏检测 ✓ · 7 宁少勿滥 + 版本化 ✓（v1 冻结、v1.1 独立版本）。

## 边界
- 本读数=**机制门**（机制是否在场）；不构成结果/能力声明（MR-9 双门分立）。
- 覆盖声明：捏造 / 重试风暴 / 换策略 / 隐式语义故障——**代码域首个资产出生的门侧前置即告齐**（a70 §三 / a72 §三）。
