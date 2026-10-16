# E3 多步执行器先导 — 双轴判据报告（P5a.53）

## 建造（零 token）
- `scripts/e3_executor_multi.py`：agent 回路四工具 `read_file / run_visible_tests / edit_file / submit`（submit **显式**）；隐藏测试 submit 后**外部**判分、只读；步数≤20；确定性过程型死亡检测（premature_done / test_loop / partial_fix_plateau / regression_break）。
- 冒烟（桩，零 token）：`e3-executor-multi-smoke.json` **all_pass**——
  好桩（edit→run→submit）→ PASS 无过程死亡；懒桩（直接 submit）→ **premature_done**；循环桩（连跑3次）→ **test_loop**。
- 静默配置沿用（可见=变异态当前已通过的 happy 测试）；v3 任务重生成。

## 双轴判据（10 探针）
| 轮次 | 配置 | fail | fail_rate | 难度轴 | 过程型死亡 | 过程轴 | tokens |
|---|---|---|---|---|---|---|---|
| A | bugs=1 | 1 | **0.10** | ❌（<20%） | **1**（regression_break） | ✅ | 118,559 |
| B | bugs=2（唯一一次难度调整，锁死） | 2 | **0.20** | ✅ | **0** | ❌ | 119,744 |

- **两轴从未同时达标**：调整前难度出带但过程轴有 1；调整后难度入带但过程型死亡归零。

## 判定（按 a53 §四）
- **过程轴为 0**（锁定配置下模型在回路里纪律完好：读→跑→改→复跑→提交，无 premature_done/test_loop/partial_fix_plateau/regression_break）。
- 按 a53 §四.2：**停跑上报，不再授权任何形态/执行器变更**；登记结论——
  **"该尺度下过程纪律饱和；代码域免疫工作须 SWE-bench 级基板"**，带事实重开裁（不得再发明 v4）。

## token
- 累计：前三轮 41,739 + 多步 A 118,559 + B 119,744 = **280,042**（0.8M 硬顶的 **35.0%**）。

## 备注（诚实）
- 出现过 1 次过程型死亡（regression_break，bugs=1），说明**过程谓词在原则上可被观测**；但它出现在难度出带的配置下，锁定配置下为 0。故不能声称"过程死亡的栖息地已找到"。
- 与 τ 对照：τ 的过程死亡（锁死/重复风暴）诞生于**长程多轮工具循环 + 状态锁定**；本尺度（≤20 步、单文件修复）过程太短。**"过程可能短了"这一用户直觉，在数据上得到支持。**

## 待裁决
按 a53 §四封顶：**带事实重开裁**（承认廉价基板/短过程尺度够不到；代码域免疫须 SWE-bench 级长程基板）。
