# P5a.88 执行：-layout 普查确认 + 脱敏断言（抓到真漏遮蔽）+ 指纹脚手架

日期：2026-10-16
依据：a88 §二/§三/§四/§六

## §二 -layout 普查（物理前提修正）
- 装 `poppler-utils` → `pdftotext 20.11`；对 **raw PDF 只读**抽到仓库外 `/root/e2-corpus/census/{layout,rawmode}/`。
- 读数：**`-layout` 重抽 16 行/6 文件**，**与交付 txt（16 行/6 文件）逐一致**；rawmode 仅 3/2。
- **结论**：交付 txt 即 `pdftotext -layout` 产物；**抽取参数 = `-layout`，冻结入 `e2_eval_params.json`**；同名行模式真实存在（a87 §四 缺口定位正确=抽取器非参数）。

## §四 脱敏不变性机器断言（修正规格）+ 抓到真缺陷
- `scripts/assert_deid_invariance.py`：行数绝对等 / 章节计数+(按映射归一后)文本等 / 数字串差异须被映射表解释 / **漏遮蔽检测**（映射值仍现于 deid → 报警）。
- **naming_proof 4/4**：正例 + 负例（偷改金额、偷删行、漏遮蔽）全判对。
- **实抓真缺陷（安全级）**：首跑报警 `sections_mismatch` + 残留扫描揭示 **deid 仍有未遮蔽真名**（徐康×9、何菁×9、黄伟鹏×4…）——因旧脱敏器只按少量上下文前缀匹配姓名，同名词在无上下文处漏遮。
  - **修法**：脱敏器改**两遍**——先收集候选名（扩充上下文：责任人/批准人/签字/项目经理…），再**全局替换**；并修跨文件代号冲突。
  - 复跑：deid 残留映射值 **0**；断言 **all_pass=True**；标定特异度 1.0、灵敏度 全 1.0（missing/dim/number）。
  - 登记 QB-3（Qwen 方向对、规格有洞：原"数字串集合完全一致"对合法遮蔽必假阳性；已按映射解释修正）。

## §三 指纹绑定脚手架
- `scripts/e2_fingerprint.py`：`taskbook_fingerprint.json` = 规则集哈希 + 单位表哈希 + 抽取参数哈希 + 版本；**双向绑定**（任务书内嵌同值 `fingerprint: <canon>`，运行时 `verify()` 校验）。
- **不碰 .env**（a88 §三.1）。naming_proof **4/4**（正例 / 缺文件 / 哈希不符 / 任务书内嵌错值）。
- 当前值：`ruleset_sha=73057d4a4881b2b4`、`unit_table_sha=8d39d7b49cffaaa6`、`eval_params_sha=1eb144faab02f557`、`canon=9b381eb7a1f77e2b`（规则集仍 provisional，待裁者冻结 v0.1 后重钉）。

## 回归 / 提交
- 回归 15 电池 GREEN。提交本地，镜像未推（RL-3）。

## §五 a86 §三 清单滚动
#1 ✅ #2 ✅ #3 ✅（number 补齐 + 断言）· **#3b 脱敏断言 ✅** · **#3c 指纹脚手架 ✅** · #4 ✅；#5 任务书成书（裁者）；#6 语料规模（用户）。
