# P5a.20 epoch-6 结果与分析（direct-only 干净基线）

**运行**：2026-09-29，`ROUTER_MODE=direct`（注意力/precedent 臂**关闭**），POLICY v1 仍在。
135 τ train，10,158,445 tokens，`train_loss=42.0`。

## 1. 聚合对照

| epoch | 臂 | POLICY | pass | pass% | SC 桶 | RO 桶 |
|---|---|---|---|---|---|---|
| 3 | Thompson 混合 | 无 | 99/135 | 73.3% | 69.8% | 86.2% |
| 4 | Thompson 混合 | v1 | 102/135 | 75.6% | 75.5% | 75.9% |
| 5 | Thompson 混合 | v1 | 102/135 | 75.6% | 71.7% | 89.7% |
| **6** | **direct-only** | v1 | **93/135** | **68.9%** | **66.0%** | 79.3% |

**表面读数**：关掉注意力臂后反而更低（−6.7pp vs e5）。**但不可据此说"注意力有用"**（见 §3）。

## 2. 失败结构（e6）

- 失败 42 条；其中屏幕 C4（GT 自相矛盾）任务 15 条里 **6 fail / 9 pass** → **C4 是筛查信号，非"不可赢"**（冗余 GT 动作报错但 DB 终态仍可达）。
- 剔 C4 后：non-C4 = 84/120 = 70.0%（仍低于 e5）。
- watchlist：A-008 FAIL（同线束噪声）、A-019 FAIL、R-105 FAIL（同任务缺陷）；A-007/A-027/A-018/R-102 PASS。

## 3. 关键反证：e6 的下滑**不能**归因于"去掉注意力臂"

按 e5 臂拆 e5→e6 迁移：

| e5 臂 | pass→pass | pass→fail | fail→pass | fail→fail | e5 pass | pass→fail 率 |
|---|---|---|---|---|---|---|
| direct | 40 | 13 | 5 | 11 | 53 | **24.5%** |
| precedent-assisted | 40 | **9** | 8 | 9 | 49 | **18.4%** |

- 若"注意力臂有用"，则 e5 的 precedent 任务在 e6 变 direct 后应**降更多**；实测**降更少**（18.4% vs 24.5%）。
- 即 e6 是**整轮系统性偏差**（两个原臂任务都掉），差异来自 **run 间漂移/随机性**（相隔 13 天、换 key、默认 temperature、无 seed、`deepseek-flash` 别名模型可能更新），**不是臂效应**。

## 4. 结论（诚实版）

1. **本套注意力方法是否有用：epoch-6 无法回答。** 聚合"注意力 off 更差"不可解释为能力差；反向也无证据。
2. **run 间方差约 ±6.7pp（≈±9 任务）**——e3/e4/e5 的 MERGE/REJECT 级差（5.7pp 以内）**均在噪声带内**，进一步支持 P5a.19 §二"聚合暂定"。
3. **唯一能回答命题一的实验 = epoch-7**：与 e6 **背靠背、同仪器、只差臂**（固定 50/50 + 冻结快照），做**同轮内** direct vs precedent 对照，消除 run 漂移。

## 5. 下一步（建议）

- 立即跑 **epoch-7**（`freeze_precedents --epoch 7` + `SA_EPOCH=7 ROUTER_MODE=measurement`），与 e6 同日对照；
- e7 完成后：watchlist 三案 + 邻近注入对 + 非 C4 子集，做**同轮内**臂效应估计（e7 内 direct vs precedent），并报告 pre-registered SC∈[70,80%] 是否站住。
