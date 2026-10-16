# P5a.16 三案复审与变更点审计修订（裁决）

**裁决人**：task-book 作者 / 仲裁者
**输入**：用户上传的三任务双 epoch 全轨迹原始记录（`p5a13-A019-R105-both-epochs.md`、`p5a13-A008-both-epochs.md`，opencode 未附判定，防锚定协议合规）
**触发**：用户判定 A-019、R-105、A-008 均有问题，指示"去掉 e4/e5，根据结果重审变更点审计"
**状态**：终裁。本文件修订 P5a.15 的变更点审计结论，优先级高于 P5a.15 冲突部分。

---

## 〇、裁判自纠声明

P5a.15 基于尾部样本包的裁决中：
- A-008 被我定性为"PASS→FAIL 回归，机制假设=P1 确认行为诱发模拟器窄答"——**机制定性错误，撤回**。
- A-019、R-105 被我判为"fail-fail 模糊，收窄不计分"——方向正确但**深度不足**，未识别出两案失败机制本身就是线束纠缠，连 token 差值都不可解释。

三案深审 3/3 发现线束级问题，说明尾部抽查包的信息量高于预期，也验证用户坚持看原始记录（而非我的二手摘要）是对的。本裁决全部结论以 span 级证据为准。

---

## 一、裁决总表

| 任务 | e4→e5 结局 | P5a.15 原判 | P5a.16 终裁 | 处置 |
|---|---|---|---|---|
| TAU-A-008 | PASS→FAIL | POLICY 回归嫌疑（P1 机制假设） | **线束驱动 flip**：模拟器失真 + agent 算术滑误；P1 假设驳回 | 隔离仓；A-008 案卷关闭（非 POLICY 回归） |
| TAU-A-019 | FAIL→FAIL | 模糊，不计分 | **任务线束纠缠**：GT/模拟器日期不一致 + e5 模拟器提前退场；且两臂不一致 | 隔离仓 |
| TAU-R-105 | FAIL→FAIL | 模糊，不计分 | **任务内禀陷阱常量**（操作锁序）+ 部分线束纠缠 | 隔离仓 |
| TAU-A-027 | PASS→PASS | 健康 | 维持 | 保留在审计集 |
| TAU-A-007 | PASS→PASS | 健康 | 维持 | 保留在审计集 |

**"去掉 e4/e5"的执行口径**：三对从一切 e4↔e5 变更点统计与 POLICY 归因论证中移除（进隔离仓，单独报告为"线束噪声下限"）；仍计入原始 pass-rate（诚实税，MR-9 精神不变）。

**修订后核心结论：已深审样本中，e4↔e5 不存在可归因于 worker 的回归或变更点。** 唯一 flip（A-008）为线束驱动。

---

## 二、逐案裁决（span 级证据）

### 2.1 TAU-A-008 —— 撤销 POLICY 回归定性

**两 epoch 注入同一 POLICY v1**（policy_id `174e4c5dfd45`，e4 span `826be241` / e5 span `30a857d5`）。同配置下的 PASS→FAIL flip 按定义不可能是 POLICY 变更点，只可能是联合噪声。噪声源定位：

**断点 1：24 小时窗口算术错误（worker 侧真实缺陷）**
- e4 step 7，`tau__think` 显式推理："created 2024-05-14T16:03:16, current 2024-05-15 15:00 — within 24 hours… can be cancelled" → 正确 → step 10 `cancel_reservation` 执行 → PASS。
- e5 turn 12，纯文本断言："created 2024-05-14 16:03 (**more than 24 hours ago** as of now, 2024-05-15 15:00)" → **错误**（实际 22h57m）→ 全程未调 `cancel_reservation`（e5 总工具调用 7 次，无 cancel）→ GT 动作缺失。
- 性质：心算时间窗口 → 输出虚假约束断言。这是 P2"不臆造"的精神违背，但 POLICY 文本并未阻止它发生 → **POLICY 文本对算术滑误无效**，需要"显式计算"类教训或金丝雀（见 §四 L-A008）。
- 对照意义：e4 用 think 算对了，e5 不用 think 算错了。这不是 POLICY 差异，是 worker 内部策略漂移（同配置随机性）。

**断点 2：模拟器违背 GT（线束侧缺陷）**
- e4 turn 9 模拟器主动给全约束："Book the new business round trip for **the same 3 passengers**…" → agent 订 3 人 → actions_match PASS。
- e5 turn 16 agent 问"book for all three, or…"，turn 17 模拟器答"**just Mohamed Silva**"——GT 要求 3 名乘客（原预订 K1NW8N 乘客名单即 3 人）。模拟器答案与自身 GT 指令矛盾，此后任务不可赢。
- 联合因果说明：agent 的澄清问题本身合理，但创造了模拟器出错的叉路。不能免责 worker（更稳的策略是默认沿用原预订乘客名单），也不能怪 POLICY——e4/e5 同 POLICY。**此类 flip 的唯一干净归因是"线束噪声下限"的实例。**

**裁决**：A-008 案卷（P5a.15 开立）关闭，定性"非 POLICY 回归"。P1 机制假设驳回——轨迹中无任何"确认轮挤掉信息轮"的证据。

### 2.2 TAU-A-019 —— 任务线束纠缠，双 epoch 均不可赢

- **GT/模拟器/DB 三方日期不一致**：模拟器 turn 13（e4）称返程"5/20 instead of 5/18"，但 DB 原返程为 **5/19**（HAT002 LGA→PHX 2024-05-19，见 e5 step 2 工具输出）。"晚两天"=5/20 还是 5/21 无一致答案，agent 怎么选都可能与 GT 错位。
- **e4 死法**：模拟器中途追加自相矛盾的约束（morning before 7am → 无 → cheapest Economy），agent 按用户确认的"same dates 5/17 & 5/20"把**四段航班全换**（HAT275/226/245/073，step 15），db_final_state FAIL。
- **e5 死法**：模拟器要"DTW–LGA 直飞"，库里直飞**不存在**（step 7/8 四次 `search_direct_flight` 全返回 `[]`）；agent 如实告知后，模拟器**放弃任务**（turn 11 "I'll leave the reservation as is"）——GT 要求的加行李、改返程两个动作，模拟器从未发起。e5 从 turn 11 起结构性不可赢。
- **149.5k→65.0k 的"收窄"= 模拟器提前退场**，不是 worker 效率提升。FP-4 在此对上无任何可读信号。
- **附加 disqualifier**：e4 为 precedent 臂（exploration=true，span `d09cf0aa`），e5 为 direct 臂（span `3d6efec4`）——**臂不一致**，该对本来就不具备跨 epoch 可比性。

### 2.3 TAU-R-105 —— 任务内禀陷阱（锁序）为常量，非变更点

- **操作锁序陷阱**：GT 要求改 pending 订单 item + 改地址。e4 step 19 实证：先 `modify_pending_order_items` → 状态变 `pending (item modified)` → `modify_pending_order_address` 报错 "non-pending order cannot be modified"。正确顺序应为**先地址后 item**。两 epoch 均先改 item，各踩一次——**常量，不是 e4→e5 的变化**。
- **e5 的"未试先拒"**：turn 18 agent 未尝试即断言地址不可改。信念碰巧为真，但本次运行无证据。若该知识来自注入的 precedent（`3d05a416ea71`，两 epoch 均注入 281 tokens），则是"沉积物以传闻形式起效"的实例——**需核查该 precedent 原文是否含此结论**（§五工单 3）。
- **模拟器诱发额外动作**：模拟器主动要求退 backpack（e4 turn 13 / e5 turn 9），GT 动作列表无此项。若评测非子集语义，此额外动作本身即可致 actions_match FAIL——需核对 GT 原文（§五工单 4）。
- **token 收窄部分真实**：e4 turn 6/8/10 存在三轮重复确认（P1 的经典靶子），e5 流程明显精简。206.8k→152.8k 的差值**部分**符合 P1 意图——但结局锁死 FAIL，按分层规则不可计分，仅作定性备注。

---

## 三、变更点审计教义修订

P5a.15 的四象限协议保留，但前置并追加以下条款：

### 第 0 步：线束保真筛查（harness-fidelity screen）——全量，非抽样

任何任务对进入机制归因之前，先过三问：
1. 模拟器每句发言是否与该任务 GT 指令一致？（A-008 e5："just Mohamed" vs GT 3 人 → 违）
2. 模拟器是否发起了 GT 动作所需的全部请求？（A-019 e5：未发起行李/改期 → 违）
3. GT 动作前提在环境中是否可达？（R-105：锁序是否允许两动作共存 → 待探针确认）

任一违反 → **隔离仓**：移出变更点统计的分子分母，单独汇总为"线束噪声下限"报告。隔离对在原始 pass-rate 中保留（诚实税）。

**3/5 抽查被隔离 ⇒ 筛查必须全量**。e4↔e5 全部不一致对（discordant pairs）都要过第 0 步，不允许只查大 Δ 尾部。

### 臂一致性前提

跨 epoch 对比仅在**同臂**对上进行；臂不一致对（A-019）直接丧失比较资格。审计表新增 `arm_e4`/`arm_e5`/`exploration` 列。

### FP-4 收紧

FP-4 只在 **PASS→PASS 且过第 0 步** 的对上计分。FAIL→FAIL 的 token 差值在模拟器可驱动对话长度的前提下**结构性不可解释**（A-019 e5 = 模拟器退场 artifact），维持"不计分"且理由升级为结构性。

### 联合因果原则

"模拟器出错"不自动豁免 worker：模拟器响应 agent 行为，二者耦合（A-008 断点 2 需 agent 提问 × 模拟器答错联合成立）。归因语言统一为"该 flip 需要 X ∧ Y 联合成立"，禁止单因归因。

### 结局分类修订

四象限 → 五分类：PASS→PASS / PASS→FAIL / FAIL→PASS / FAIL→FAIL / **⊗ 隔离（线束）**。

---

## 四、进入沉积工厂的真实教训（走 updater 提案流程，我不直接改 POLICY）

- **L-A008（数值/时间门槛显式计算）**：凡政策含数值或时间窗口门槛（24h、金额上限、件数上限），必须调 `tau__calculate`/`tau__think` 显式计算，禁止心算断言。证据：e4 think 算对 vs e5 心算算错（同任务、同配置、同 POLICY）。
  - 金丝雀化建议：构造"created_at 距 now 恰为 23hxx"的边界案例，断言 agent 必须显式计算后再下结论。这是 FP-2 退役后"臆造约束"类金丝雀的具体素材。
- **L-R105（同一对象多操作的锁序）**：对同一实体的多个修改操作，先执行不改变锁定语义的，后执行会改变状态的。前置依赖：§五工单 2 的探针确认可行顺序后，方可写成确定性教训；若两操作互斥，则该任务进任务缺陷清单而非教训库。

---

## 五、给 opencode 的核查 / 埋点工单

1. **precedent 注入一致性取证**：A-008 同一 precedent（sig `1932cfe427b1`）e4 注入 436 tokens、e5 注入 213 tokens。查注入管线的截断/模板逻辑——同一 sig 的注入内容应字节一致，否则"同 precedent"假设不成立，双臂设计的因果隔离被削弱。输出：差异原因 + 两 epoch 注入原文 diff（脱敏后入证据包）。
2. **零售锁序探针**：在沙盒内确定性验证 `modify_pending_order_address` → `modify_pending_order_items` 顺序是否可行（及反向锁定的确切条件）。成本极低（离线 DB 即可），把 R-105 从"未知"变成"已知"。
3. **precedent `3d05a416ea71` 原文核查**：是否含"item 修改后订单锁定"结论？若有，e5 R-105 的未试先拒即沉积物起效的实例（正面案例！），应记录为 precedent 臂有效性的首个机制级证据。
4. **GT 原文入证据包**：导出 τ-bench 任务 JSON（instruction + GT actions + evaluation criteria）for A-008/A-019/R-105，确认：(a) A-019 GT 返程日期与 DB 是否一致；(b) R-105 GT 是否含 backpack 退货（子集 vs 精确匹配语义）；(c) A-008 GT 乘客数。
5. **acceptance_check span 增强**： verdict span 必须携带 GT-vs-最终状态 的 diff 字段（哪个字段/哪个动作不匹配），禁止只报 pass/fail。本次三案复查中"为什么 FAIL"全部靠人工推断，不可扩展。

## 六、对既往裁决的影响评估

| 既往裁决 | 影响 |
|---|---|
| P5a.14 epoch-5 复制成功、POLICY v1 晋升 confirmed asset | **维持**。晋升基于聚合指标（75.6%/75.6%，SC 71.7%∈[70,80%]），线束噪声对两 epoch 对称作用，聚合级结论不受任务级隔离影响。 |
| epoch-3→4 MERGE（+5.7pp SC） | 聚合级维持；但**任务级机制归因欠审计债**：e3→e4 改善集需补第 0 步筛查后才能写进论文的机制章节。优先级：论文前必做。 |
| P5a.15 变更点审计 | 按本文件修订。已深审样本中 worker 可归因变更点=0；审计产出重定义为"噪声下限测量"。 |
| FP-4 指纹 | 维持活跃，计分范围按 §三收紧（PASS→PASS ∧ 过保真筛查）。 |
| 双臂设计 | 新增风险项：precedent 注入量跨 epoch 不一致（工单 1）。修复前，臂级结论降一级置信。 |

## 七、论文素材备注

A-008 是理想的"基准噪声下限"展品：同模型、同配置、同 POLICY 的两个 epoch，一个 PASS 一个 FAIL，全轨迹证明 flip 由模拟器失真 + 心算滑误联合产生。这把"τ-bench 类交互基准的可复现性批判"从文献抱怨升级为带完整证据链的实证案例——与金丝雀门（测量机制）+ 变更点审计（隔离噪声）共同构成方法论的闭环叙事。

---

**下一步等待**：opencode 完成 §五工单 1/2/3（低成本取证）后回报；用户确认本裁决后，隔离规则生效，e4↔e5 全量不一致对过第 0 步筛查（opencode 可先机器初筛模拟器-GT 一致性，人审兜底）。
