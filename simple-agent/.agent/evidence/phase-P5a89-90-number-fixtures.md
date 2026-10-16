# P5a.89–90 执行：E2 任务书成书认知 + number 夹具补齐（a89 §四 / a90 §五）

日期：2026-10-16
依据：a89（E2 任务书成书）、a90（规则集 v0.2 修订）

## opencode 工单（a89 §四 / a90 §五）：number 夹具补 ≥3 例 + 重标定
- `e2_eval_calibration.py` 增**夹具池合成** `synthetic_number_docs()`：3 份真实勾稽模板（同一金额两处须相等，R2.2 型），数值虚构，**标 fixture，不入基线统计**（a83 §四）。
- 复跑标定（`.agent/reports/e2-eval-calibration.json`）：
  - 特异度 **1.0**；missing_section **10/10**；dimension_conflict **10/10**；**number_inconsistent 4/4**（1 真实 + 3 合成，样本薄问题解除）。
  - fixtures=34，synthetic_number=3。**全绿** → a89 §四 smoke 判分前置满足。

## a89（任务书成书）认知
- §〇 裁者勘误（第 3 笔）：真缺口=抽取器识别（¥ 前缀/裸数列/大写中文），非 raw/-layout 参数——与 opencode a88 定位一致，已登记。
- §一 smoke 5 卡 / §二 规则集 v0.1 草案 / §三 epoch 参数化生成规则 / §四 判分管线 / §五 三并行收口——**属裁者/用户文书**，opencode 待冻结信号后**重钉指纹**。

## a90（v0.2）认知
- §一 法律依据锚定（南山区办法第十八条两款；知产失信以正式认定文书为前提；地区差异真实 → 规则参数随项目走）。
- §二 修订：R3.3/3.4/3.6 冻结；R3.1 加**同包 + 同版本**双守卫（版本不可判→NA）；R3.2 拆 a（确定性冻结）/b（未决纠纷→恒 NA，epoch-2+ 语义候选）；R3.5 重写为**阈值从任务输入取**（内置常数案作废）+ 元问题裁决「裁判读卷，考生随意」（评测器直接评，运行时检索永不进金标准）。
- §三 变更控制立法；§四 语料新增「榜单通知原文」（smoke 不受影响，R3.5 恒 NA 恰测 R4 NA 纪律）。

## opencode 待办（等输入）
1. 规则集 **v0.2 冻结** → 重钉 `taskbook_fingerprint.json`；
2. 冻结后，evaluator 需实现 **R1 模板识别** + **R2.1 表内勾稽方程** + **R3 集合逻辑六条**（现 `e2_eval.py` 仅 required_sections/dimensions/number_fields 框架）——**建设段下一批**；
3. smoke 点火（a86 §三 六项闭合 + 本批三并行）。

## 盘面
- 回归 15 电池 GREEN；镜像未推（RL-3）。
