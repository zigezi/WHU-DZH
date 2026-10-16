# P5a.93–96 执行回执：DC-10 二级修复 + #11 Diff + A1–A4

日期：2026-10-16
依据：a93（#11/水印判别器/always_na）、a94（无工单）、a95（DC-10 二级 7 项）、a96（A1–A4 + 条款一至三）

## §一 always_na 分发逻辑（a93 §一）
实现为**声明式**（数据驱动，非命令式硬编码）：规则在 `e2_ruleset_v0.4.json` 声明 `{"id":"R3.2b","kind":"always_na"}`，
引擎按 `kind` 分发：
```python
elif k == "always_na":
    out.append(_mk(rid, "NA", detail=r.get("note", "")))
```
→ 输出恒 NA，且被指纹（canon 见 §五）冻结后篡改即在点火闸断裂。

## §二 #11 提示词逐字 Diff（a93 §2.2）→ `.agent/evidence/phase-P5a93-prompt-diff.md`
唯一实质变更 = 证据形式（行号→quote+章节路径，a91 立法）；另两处为占位符显式化与枚举间距（排版）。**未发现注入性措辞。待用户确认。**

## §三 水印判别器升级（a93 §3.2 + §3.3 披露）
- **判别器（三条件）**：a 仅孤立单字 / b 集合全文无连续共现 / c 跨≥3段重复；**签署字段永不删**。
- **披露（a93 §3.3）**：停用表 = `CN_STOP`（男女码号年月日时分秒一二…项目第章节部分个件条款名单位）；
  "孤立"定义 = 行内**唯一非空白字符**的 CJK 单字；区域约束 = 无（全文，不限页眉页脚）；
  触发伪码 = `watermarks()`（见 `scripts/e2_deident.py`）。
- **共存案/重合案**：`scripts/e2_deid_fixtures.py` 通过（签署存活 / 连续真名遮蔽 / 散布水印清除且不误删正文用字）。

## §四 a95 二级修复 7 项
1. **精度 fixture** ✓（白名单/任务荷载词零误遮）；
2. **召回 fixture 扩展** ✓（断行实体、胶合水印、长短名成对）；
3. **管线顺序** ✓：实体识别在**换行折叠文本**上，先于替换；**代码层白名单硬护栏**（`mask_entity` 白名单精确不遮、实体可击穿）；
4. **遮蔽预算异常** ✓：`BUDGET_RATIO_MAX=0.06`，本次无报警（v2 曾 25×；v3 已消）；
5. **准标识符** ✓：【DOCNO-】/【PROJ-】；**永不遮蔽清单**=`e2_whitelist.json`（行政区划/日期/通用词/模板章节名/R2表头/R3短语）；
6. **覆盖域声明** ✓：召回探针/闭包探针/fixture 报告均打印量程 + 已知排除；
7. **全量重脱敏** ✓（10 件）→ 双 fixture + 探针 → **人工复检包** `.agent/local/A3-deid-recheck-3.md`。

## §五 a96 A1–A4
- **A1**：规则集 **v0.4** 拆分 R1 签署项——`R1-签署文本标签`（文本标签存在性，structural_any）+ `R1-印章物理存在`（**永久 NA**，documented_exclusion）。
- **A2**：`SAFE_WHITELIST`+任务荷载保全名单入 `e2_whitelist.json`，与 `e2_variants.json` **并入 fingerprint**。
- **A3**：**两层双绿**——第一层发现召回（fixture 4/4 + 独立召回探针 residual=0）+ 第二层变体闭包（探针 residual=0，量程=已入表实体变体）；报告含覆盖域声明。
- **A4**：条款二/三的**代码全文**即 `e2_deident.py`（白名单护栏 `mask_entity`）+ `e2_deid_closure_probe.py`（变体闭包，仅从映射表实体生成），随本回执入档。

## §六 指纹重钉
`taskbook_fingerprint.json`：`ruleset_sha=75b4224f3791cf2a`(v0.4)、`whitelist_sha=667ae8893778844e`、`variants_sha=4314b159b8f2b89a`、`prompt_sha=32c79f5e972a6cbd`(v1.1)、`unit_table_sha=8d39d7b49cffaaa6`、`eval_params_sha=a7ae953e70a1547c`；**canon=`eed2a0cb8f0f9e01`**。脚手架自证 4/4。

## §七 机器读数汇总
| 项 | 结果 |
|---|---|
| `e2_deid_fixtures.py` | **4/4 deployed**（精度/召回/水印共存/重合）|
| 精度断言 `assert_deid_invariance.py` | **all_pass** |
| 独立召回探针 | **residual=0**（量程：PII正则+公司全称/核心+姓氏表格格+长号）|
| 变体闭包探针 | **residual=0**（量程：已入表实体变体）|
| 遮蔽预算 | 无报警（P3-02 ratio≈0.015）|
| 规则电池 v0.4 | **28/28** |
| 回归扫 | **16 电池 GREEN** |

## §八 状态
- **#9 OPEN**（待用户复检 4 件）+ **#11 待用户确认 Diff** → smoke 冻结。
- 复检包：`.agent/local/A3-deid-recheck-3.md`（2 失败件 + 随机 P2-01）。
