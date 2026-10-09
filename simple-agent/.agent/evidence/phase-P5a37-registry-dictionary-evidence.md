# P5a.37 落地证据：分类法注册表 + DB 字典抹除 + 机器④全库

**依据**：P5a.37 §三/§四。诊断（字段名单驱动→分类法驱动）接受并重构。

## 1. 分类法注册表（单一事实源）
`deident.FIELD_CLASS`（I/II/III/IV/FREE）+ `field_class()`/`prefix_for()`；
**生成器与 lint 共用**。未命中 → **默认 I（从严）+ 不默认放行**（a37 §三 实现铁律）。

## 2. DB 全量实体字典抹除（a37 §四）
`collect_db_sets()` 从 retail+airline 全量数据建 11,014 个实体值：
`ORD 1000 / USR 1000 / RES 2300 / PAY 2181 / ITEM 591 / PROD 50 / FLT 300 / ADDR 2783 / NAME 109 / EMAIL 1000`。
生成器 `_dbscrub()` 先做字典抹除（词边界，按长度降序），再走正则（date/money/email/…）。

## 3. 机器④（残值扫描）全库
- 词表 = 补遗后分类法 + **DB 全量字典**；**词边界匹配**（修了"伪值 `RES_0x770817` 含 zip `77081`"的子串 FP）；
- 对**全库 443 计划**运行（非抽样）。

## 4. 本轮修掉的实现空洞
| 空洞 | 修法 |
|---|---|
| `flight_number` 未入注册表 → 前缀 XID | 注册表补 I/FLT |
| `zip` 为**整数**时未走 str 分支而漏脱 | `_trans` 对 I/III 类数值型值转 str 映射 |
| PSEUDO_PREFIXES 缺 CERT_/PHONE_/XID_ | 补全 |
| 机器④ 子串误报 | 改为词边界 regex |

## 5. 结果
```
/ e8_build_deident.py --epoch 7
distinct_deid_plans = 443
all_pass = true         # no_residual ∧ json ∧ db_nonmember ∧ db_dict(机器④) ∧ tools
unclassified = {}       # 注册表全覆盖
mapping_sha256 = 9d384d4d…   # 映射表仅存 .agent/local/（未跟踪）
```
- 重跑 `e8_freeze.py`：达标线仍全过（top1/distinct/同域）；`e8_sandbox.py`：**MECHANICAL PASS**。
- 新抽检样本：`e8-deid-audit-sample.md`（10 例，脱敏后）；左右对照 `.agent/local/e8-deid-audit-sidebyside.md`（未跟踪）。

## 6. 旧的 10 案
按 a37 §五：旧库整体作废，旧 10 案 + a37 归档为**生成器回归测试集**；用户抽检**改在新库上重新抽样**。G 门保持关闭，e8 继续冻结。
