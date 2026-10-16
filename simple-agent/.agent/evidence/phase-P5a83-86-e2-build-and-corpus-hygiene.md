# P5a.83–86 执行：E2 文本先行 + 语料卫生 + 评测器设施 + e2_corpses 池

日期：2026-10-15
依据：a83（文本先行范围冻结/A案否决）、a84（GPU否决/教义）、a85（三型/评测器纯确定性）、a86（冒烟条件生效/语料卫生）

## a83 / a84（裁决认知，无独立工单）
- a83：A 案否决（多模态推迟 epoch-3+）；B 案修正采纳（确定性数据集仅作**评测器校准夹具**，非 epoch 语料）；C 案前提勘误；文本先行范围冻结（docx+pdf 文本层，**不读图**）。
- a84：GPU 迁移否决（当前零 GPU 负载）；教义「**操作者可黑箱，仪器必须过程可见**」登记（拟入器官宪章邻近条款）。

## a86 §二 语料卫生（**blocking，已立即处置**）
- 原地：`/root/simple-agent/E2File/`（20 文件 6.7M，**未脱敏 PII**，未 gitignore）。
- 处置：
  1. **整体移出仓库树** → `/root/e2-corpus/raw/`（raw 只读封存）；
  2. `.gitignore` 增 `E2File/` · `/e2-corpus/` · `*.pdf`（兜底）；
  3. **脱敏副本** → `/root/e2-corpus/deid/`（`scripts/e2_deident.py`：手机/固话/身份证/统一社会信用代码/邮箱/银行账号/公司名/姓名 → `【KIND-n】`），映射仅存 `.agent/local/e2-deid-mapping.json`（gitignored）；de-id 复扫 **PII 残留 0**；65 条映射；
  4. E2 运行以 deid 为输入，raw 只读。
- 证据：`git status` 已无 E2File；`git check-ignore .agent/local/e2-deid-mapping.json` = ignored。
- **LR-6** 入册：「数据入位当日即查 git 边界」。

## a85 §七.2 / a86 §三.2 评测器设施（建设段，零运行预算）
1. `scripts/e2_unit_norm.py`：**单位归一表**（万/亿/千/元/角/分 + 中文数字 + 全角 + 逗号）→ 分（int）；`extract_amounts`。
2. `scripts/e2_eval.py`：**维度合规规则集框架**——`required_sections` / `dimensions`（A出现∧B出现→判死）/ `number_fields`（同字段金额须一致）；纯确定性。
3. `scripts/e2_defect_injector.py`：**缺陷注入夹具生成器**——真实文档 + 注入已知缺陷（删章节 / 造维度矛盾 / 篡改数字）→ 已知答案集。
   - 规则集**内容**待裁者随任务书冻结（本处仅框架；calibration 用 provisional ruleset 演示）。

## a85 §七.2 / a86 §三.3 夹具标定（评测器版 naming_proof）
- `scripts/e2_eval_calibration.py`（只用 deid）：8 文档 → 7 clean 基 → 21 夹具。
- 读数：**特异度 1.0**；灵敏度 missing_section **7/7**、dimension_conflict **7/7**；number_inconsistent 夹具 **0**（现有 deid 文档无"标签+金额同行"，注入器跳过）——**如实记缺口**，待选入含金额字段文档补标定。
- 报告：`.agent/reports/e2-eval-calibration.json`。

## a86 §三.4 e2_corpses 池
- `trace_store` 建表 `e2_corpses`（与 code_corpses 同构 + `domain_pack`）；`backend/monitor/e2_corpses.py`（同采集口径 v1 + 语境锚定）。当前 0 具（运行段未启，符合"E2 以资产=0 开局"）。
- 采集链：E2 会话以工具层钩子（`op_log_hook.sh`/`BASH_ENV`）+ 回合末收割 + 任务判定通道喂入，`ingest_event` 走 filter_oplog_v1。

## 回归
- `regression_sweep.py` 15 电池 GREEN；注册表不变性保持。

## a86 §三 前置清单进度
| # | 事项 | 状态 |
|---|---|---|
| 1 | 语料卫生 | ✅ 完成 |
| 2 | 评测器建设回执 | ✅ 框架+单位表+注入器（本回执）|
| 3 | 评测器过夹具标定 | ◑ 部分（特/敏 1.0；number 夹具缺，待补文档）|
| 4 | e2_corpses 池建成 | ✅ 表+模块就位（0 具）|
| 5 | 任务书成书 + 规则集冻结 | 裁者 |
| 6 | 语料总批次规模 | 用户 |
