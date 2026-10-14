# P5a.68–69 落地证据：攒批纪律解释 + ring_draft LLM 起草器联调

## P5a.68（纪律，无代码动作）
- **批量的形式不违禁，违禁的是任务来源**：批量执行 backlog 真实工单=合规；为凑 30 具而造"易死任务"=违禁。
- 补强理由：代码尸体库是 Phase 1 的**已知答案/刻度来源**，人造任务会把死因分布扭成"我们选择去诱发的几类"→ 校准到虚构操作者（与 a62 越界同类，方向相反）。
- 我已遵守：**不造任务**；`code_harvest` 只捡真实失败。

## P5a.69 ring_draft LLM 起草器联调（唯一 LLM 格子）
- 脚本 `scripts/ring_draft.py`：分诊处置单 → LLM 起草 → 草稿落盘 `.agent/reports/ring-drafts/`（**证据域，不部署/不出生/不进注册册**）。
- 输入只用**已有语料**（25 条 τ 候选，known-answer 自检）；无新开采。
- 预算：**tokens 9,924 < 0.1M 硬顶**，运行时闸未触发（`stopped=null`）。
- **验收口径（a69 §五，看走通不看质量）**：
  | 项 | 结果 |
  |---|---|
  | 端到端贯通（分诊→draft→落盘） | ✅ `end_to_end_ok=true` |
  | 草稿要素齐全（谓词文本/点火条件/**可观测性声明**/误伤面自评/干预语义型） | ✅ `elements_complete_ok=true` |
  | **acceptance_ok** | ✅ |
- **known-answer 语义型自检**：`known_answer_semantics_ok=false`——**仅 REPEAT::\*** 7 条 LLM 判为 `behavior-reroute`（我预期待定 `benign-reissue`）。**属设计定性分歧，非质量判定**（a69 明确不判质量）；登记为 `ring_draft` 的待议点（重复失败守卫的干预语义型归属），留代码域 Phase 1 校准。
- 宪法边界照旧：draft 只产文本，不碰 reward/verifier/测试/分类法，无 commit/push。

## 附带确认（a69 §六）
- a67 交付核验通过：`backlog.md` 四字段、`governance-defect-classes.md` DC-1~6、作废归档两笔。
