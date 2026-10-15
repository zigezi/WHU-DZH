# P5a.76 建设段发现：自检脚本污染生产资产注册表

日期：2026-10-14
来源：a76 §二.1 建设段的设施自检（**非** §三 受批准的回扫；属我额外运行的设施核验）
定性：仪器缺陷（silent instrument mutation），非任务失败。

## 现象
运行 `scripts/e3_substrate_check.py` 后，`git status` 显示 `.agent/reports/assets.json` 被改写：
- `lock_order_v1` 由 `credit_level=field_validated`、`live_confirmed=true`、含 5 条 `revalidation_log`（含 a59 活体点火记录）
  → 被重置为 `credit_level=T1_candidate`、无 `live_confirmed`、无 `revalidation_log`，`created_at` 被刷新为本次运行时间。

## 根因
`e3_substrate_check.py:28` 调用 `provenance.register_asset({... "credit_level":"T1_candidate" ...})`，
且 `provenance` 指向**真实**注册表（`.agent/reports/assets.json`）——自检把早已晋级、积累活体证据的资产**覆盖回初始候选态**。
对照：`organ_selftest.py:13` 正确地把 `prov.FILE` 指向临时文件（隔离存储），不污染生产库。

## 处置（DC-8：先快照后清场）
- 快照：改写后的注册表 → `.agent/local/p5a76-assets-mutation/assets.after-e3_substrate_check.json`（不跟踪）。
- 还原：`git checkout -- .agent/reports/assets.json`；复核 `lock_order_v1` 三个字段恢复（field_validated / live_confirmed / 5 条 log）。工作区清净。

## 建议修法（待裁，属真实工单）
1. 自检/校验脚本一律走**隔离存储**（`organ_selftest` 模板：临时 `prov.FILE`），禁写生产 `.agent/reports/assets.json`；
2. 或 `provenance.register_asset` 对**已存在 asset_id** 做**合并/保留富字段**而非覆盖，并对候选态降级设显式闸；
3. 纳入 §三 回扫触发面（设施变更自动触发时，核查注册表 diff 应为空）。

## 与 a76 的关系
a76 §三 的价值主张正是"验证多轮改动后仪器无衰变（存在≠在岗）"——本发现即该主张的一次实证：
**一个"自检"会静默破坏它本要保护的注册表**。§三 官方清单（12 电池 + firing_audit）本身全绿且逐字节一致；
本污染来自清单外我额外运行的 `e3_substrate_check.py`。
