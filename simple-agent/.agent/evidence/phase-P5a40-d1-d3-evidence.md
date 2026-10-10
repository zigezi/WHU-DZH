# P5a.40 落地证据：D1 词典过宽修复 + D3 注入池准入 + 提取保真机检

## D1（词典过宽误伤普通名词）
- 根因：商品名（`Action Camera`/`Bluetooth Speaker`）的词元进了 NAME 集，大小写+复数匹配命中普通词（`Action`→`actions`、`request`/`modifications` 等）。
- 修：**停用词护栏**（`deident.STOPWORDS`）——普通英语词即使撞字典也不得伪真值化；定向采集让**商品名归 PROD、人名归 NAME**。
- 新机检 `membership_proof`：被替换值须能反查 DB 成员（含成员词元、大小写不敏感）；**非成员 + 停用词 = 过宽替换 = FAIL**；另出 `not_in_static_dict` 覆盖报告（运行派生地址/email 等，informational）。

## D3（注入池准入，E 门参数）
- **注入物合格 = 源 run verdict = PASS**（`e8_freeze.py` 按 (req_id, epoch) 查 verdict 过滤）。
- 本轮 **过滤掉 185 个非 PASS 沉积**；过滤后达标线仍过（同域 95.6% / distinct 60 / top-1 3.4% / 臂 46+45+44）。

## 提取保真机检（新）
- 每份注入计划的工具数 vs 源 run `tool_call` 数比对；不一致记档（不静默丢调用）。
- 结果：**85 例不一致**（入报告 `extraction_defects`，供 E 门审查）。

## 结果
```
e8_build_deident.py: distinct=443  all_pass=true
  membership_proof_fails=0   not_in_static_dict=122(informational)  unclassified={}
e8_freeze.py: gates.all_pass=true  pool_rejected_nonpass=185  extraction_defect_n=85
e8_sandbox.py: SANDBOX MECHANICAL PASS
```
- D2（叙述层/调用层断裂）：a40 判部分天生；其可机检部分 = 上述提取保真，已记档。
- 新样本：`.agent/reports/e8-deid-audit-final.md`（8 例，自由文本重度）。

## 触发规则（a40 §四）
两个修复均为**减法**（停用词护栏、verdict 过滤）+ 专项机检可完全机验 → 免除人工轮（豁免适用）。回归集 = 旧 10 + v2 14 + 本轮 8 案。
