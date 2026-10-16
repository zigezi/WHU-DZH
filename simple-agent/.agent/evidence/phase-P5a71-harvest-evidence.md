# P5a.71 §三 回合末收割核对 证据

**执行**：`scripts/code_harvest.py`（零 token）。
**输入**：`.agent/logs/turn-events.jsonl`（1 条**真实**失败：`sentinel_ledger.py` 首次页脚修复时的 `SyntaxError`，ASCII 引号）。
**结果**：
- 首次运行：events_read=1，**added=1**（6→7）→ **收割管线未断**（若为 0 则同 tau__ 类管道断点）。
- 二次运行：added=0（去重 (ts,command,exit)）→ 去重正常。
- **corpses_total = 7；death_classes = 4**（env_missing / syntax_death / test_or_build_fail / timeout_loop）；**触发线（30/3）未达**。
- 存储注记：`turn-events.jsonl`、`code_corpses`（trace.db）均在 gitignore 区（运行时数据不入库）；计数在 tracked 证据留痕。

## 口径钉界（§二）
- comprehension（理解层）三变体全通 → 假设**关闭**；
- **rescue（救场层）不关闭** → 并入代码域首批资产出生后的实证环节。
