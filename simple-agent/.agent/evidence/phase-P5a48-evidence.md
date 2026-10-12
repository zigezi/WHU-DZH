# P5a.48 落地证据：REPEAT::* 资产（repeat_failure_v1）走完整路径

**依据**：P5a.48 §八——REPEAT::* 建电池**批准**，须走完整资产路径：精确点火规则 + 干预语义 + 金丝雀≥5（含阴性对照）+ C-1；25 候选逐条，不许批量。

## 1. 谓词 + 干预语义（Path B' 否决式）
- `backend/monitor/repeat_guard.py`：`RepeatFailureGuard`
  - **点火规则（确定性）**：即将执行的 `(tool, canonical_args)` 键**失败计数 ≥ threshold-1**（默认 threshold=3）→ 否决该次执行。
  - **干预语义**：返回合成结果（引导"改变参数/方法，不要原地重试"，P5 纪律）。
  - 状态位：按 `(tool, args)` 键；**成功即清零**（合法重演不受影响）；键独立。
- `backend/worker.py`：`execute_tool` 接线（`SA_REPEAT_GUARD=1`），点火记 `interceptor_fire{rule=repeat_failure_v1}` span；每任务 `repeat_guard.reset()`。

## 2. 金丝雀电池（≥5，含阴性对照）
`scripts/repeat_guard_battery.py` → `repeat-guard-battery.json`：**6/6 通过**
- P1 第 3 次相同失败 → 拦（该拦的）
- P2 未达阈值（第 2 次）→ 放行
- **N1 成功重演 → 放行**（阴性对照）
- **N2 不同参数 → 放行**（阴性对照）
- **N3 不同工具 → 放行**（阴性对照）
- P3 合成文案正确（含"改变参数或方法"）

## 3. C-1 冷启动复现门
`scripts/c1_coldstart_gate.py --asset repeat_failure_v1 --battery repeat_guard_battery.py`：**PASS**
（干净容器只装 harness+注册表+电池；电池 6/6；资产在场；零 token）→ 出生证末栏入 `assets.json.revalidation_log`。

## 4. 资产库状态
- `lock_order_v1`（τ，C-1 PASS）
- `repeat_failure_v1`（τ，C-1 PASS）
- **部署资产 = 2**（发热比 ~30:2）。
- 余下失败开采候选（`user not found`×15 等）**逐条同此流程**，未批量放行。

## 5. C-1 门泛化
`c1_coldstart_gate.py` 增 `--battery/--battery-json`，可对任意资产电池做冷启动复现（`interceptor.py`+`repeat_guard.py` 均随容器装入）。
