# P5a.91 执行：规则集 v0.3 全量引擎 + 逐规则 fixture + 指纹重钉

日期：2026-10-16
依据：a91 §四 下批工单（blocking smoke）

## §四 evaluator v0.3 全量实现
`scripts/e2_eval.py` 增规则引擎 `evaluate(docs, task_input, ruleset)`，支持规则类型：
- **R1 模板**：`structural`（申请书/实施方案必备项）、`structural_template`（信用报告变体识别）。
- **R2.1 表内勾稽**：`table_equations`（合计=直接+间接；小计=财政+自筹；自筹≥财政；单位归一后比对）。
- **R2.2 跨文档比对**：`cross_doc_equal`（项目预算 ≡ 项目预算 ≡ 项目预算；缺文档/版本不可判→NA）。
- **R3 集合逻辑六条**：R3.1 cross_doc+同版本守卫、R3.2a implication_count_zero、R3.2b always_na、R3.3 date_before、R3.4 range_contains、R3.5 param_threshold_date（阈值取自**结构化参数**）、R3.6 cross_doc_equal。
- **证据形式**：原文片段 quote(≤40)+章节路径（**不用行号**，a91 §一.1）。
- **评测器纪律**：结构化参数通道（task_input dict，不解析自然语言）；未知 kind→NA，不崩溃。

## 逐规则 fixture（naming_proof 延伸，每条 ≥1 正 1 负）
`scripts/e2_eval_rules_battery.py` → **25/25 deployed**：12 规则 base 全 PASS/NA + 11 条负例各触发对应 FAIL + R3.2b 恒 NA + R3.5 缺参 NA。
证据：`.agent/reports/e2-eval-rules-battery.json`。

## 指纹重钉（a91 §四 末）
`scripts/taskbook_fingerprint.json`（规则集 v0.3 + 提示词 v1.1 + 单位表 + 抽取参数）：
- `ruleset_sha=cdb1ac336414500e`（v0.3）、`prompt_sha=32c79f5e972a6cbd`（v1.1）、`unit_table_sha=8d39d7b49cffaaa6`、`eval_params_sha=62d2edf130b370f2`。
- `canon=312020652efd4aeb`（任务书须内嵌此值，运行时 `verify()` 双向绑定）。脚手架 naming_proof 仍 4/4。
- 提示词 v1.1 落 `scripts/e2_prompt_v1.1.md`（模板 + 5 卡 + 评测器纪律）。

## §五 点火前清单状态
1–4 ✅；5 任务书成书+lint+冻结 ✅（a91 闭合）；6 语料规模（用户，缓）；**7 evaluator v0.3 + 逐规则 fixture ✅**；**8 指纹重钉 ✅**；9 A3 人工抽检 1–2 件 deid（用户，点火前）。
→ **7/8 完成；仅余用户侧 #6/#9**，smoke 待 #9 后自动点火（a91 §五）。

## 盘面
回归 **16** 电池 GREEN。镜像未推（RL-3；本地领先 8 提交）。
