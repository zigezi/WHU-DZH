# P5a.49 §三 C1 建造阶段证据（E3 先导 · 零 token）

## 交付
- **任务生成器** `scripts/e3_generator.py`：模板族 + 参数变异（seeded RNG）+ 新颖性机检（prompt_hash 去重）。
- **测试灵敏度门**：参考解全过 ∧ ≥3 变异体被杀（每族含 ≥3 个**精心设计的错误变体** + 通用算子变异）；不满足不入库。
- **探针 schema**：`task_id / template_family / prompt_hash / signature / doc / hidden_tests / reference / mutants_killed`；`template_family` 为簇单位。
- **污染金丝雀**：HumanEval 式公开题（`has_close_elements` 等）混入，标 `is_canary`。
- **执行安全**：变异体/参考解执行带 **signal 超时**（防变异体死循环挂死）。

## 灵敏度门良率（P5a.49 §三.C1 要求先报）
```
requested=40  admitted=38  rejected=4  admit_rate=0.95  canary_n=4  mutants_killed_min=4
```
- 良率 **95%**；6 个模板族各自过门。产物 `e3-pilot-tasks.json`、`e3-sensitivity-gate.json`。
- **未产生任何能力声明**（本阶段不含臂、不跑模型）。

## C3 报告模板已冻结（先写后跑）
- `.agent/reports/e3-pilot-report-template.md`：人口统计 / 死亡分类分布（§六种子类目）/ 金丝雀差分 / 仪器校准注记 / 谓词候选；**禁能力声明**。

## 待办（需开工令）
- **C2 两阶段执行**：需先建 **E3 执行器**（把 spec 交 agent、agent 产算子、隐藏单测判分、失败类别结构化）——属 C1 建造的延伸；建好后跑阶段一 10 题校准 → 阶段二 30 题（≤0.8M tokens，硬顶）。
- **C4 并行**：拆解重写组（gift_card / not_enough_seats / certificate_update）案头再审（挂起）。
