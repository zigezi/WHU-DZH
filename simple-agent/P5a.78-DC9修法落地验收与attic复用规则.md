# P5a.78 DC-9 修法落地验收与 attic 复用规则

日期：2026-10-14
依据：image 126（a77 执行回报，提交 2ee906e）

## 一、三条修法落地：验收通过

- §二.1 注册表沙盒：SA_REGISTRY_PATH 解析 + register_asset 生产写须显式 production=True / SA_REGISTRY_PRODUCTION=1，缺省沙盒、越权写直接 PermissionError；单元验证（生产写被拒/沙盒写成功）✓。
- §二.2 不变性断言：scripts/regression_sweep.py 跑 12 电池 + firing_audit 并断言生产注册表 sha256 前后一致，实测 GREEN ✓。
- §二.3 封线隔离：18 脚本入 scripts/attic/（含 README 只读归档），scripts/manifest 在册清单，核验无在役脚本 import 被移模块 ✓。
- 计数更正（12）与 LR-4「存在≠无害」入册、DC-9 状态「已修」✓。

## 二、行为变更知会确认

organ.birth 默认沙盒、生产出生须显式 production=True——确认。当前无生产出生调用，不破现状；此默认即"生产写是例外"的结构表达，正是立法本意。

## 三、attic 复用规则（裁决确认，入规则）

opencode 问：a77 把 e8 件入档只读，而 e9-harness-spec 曾标其为 E2 可复用，冲突如何解？

**裁定：opencode 的解法正确，固化为规则——attic 复用 = 复制，不原地运行。** E2 建设段从 attic 复制所需 e8/e9 harness 件到 E2 设施命名空间，副本进入在册清单并须满足当前出生标准（含 naming_proof 等）；attic 原件永不在原地执行。归档是封存运行权，不是封存源代码。

## 四、盘面

尸体 7/30、4 类；E2 建设段在轨，设施事实清单已出；待用户域事实（投标语料来源/规模、评测器归属）以成任务书。本地领先镜像 3 个快照（3f2c3da / aa4b1aa / 2ee906e），待用户手动同步。
