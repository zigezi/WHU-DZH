# e8 判读报告（P5a.43 运行令）

**运行**：2026-10-10，三臂 direct/sibling/unrelated，matrix_hash=`85fef79fe57a6f28`（冻结，未动）。
135 τ train，10,289,545 tokens，train_loss=34.0。**不做跨 epoch 对比。**

## 1. 主终点 Δ2 = sibling − unrelated

| 臂 | pass | 率 |
|---|---|---|
| direct | 36/46 | 78.3% |
| sibling | 32/45 | 71.1% |
| unrelated | 33/44 | 75.0% |

- **Δ2 = −3.9pp**；family 簇 wild bootstrap（5000×）95% CI = **[−22.1, +12.9]pp**；P(Δ2≤0)=**0.662**。
- **判定：不排零 → 非胜。** 形态对齐后的纯内容相关效应未显示出来。

## 2. 次要终点（对照 e3–e5 安慰剂带 +2.6~+11.5pp，非参照零）

- Δ1 = sibling − direct = **−7.1pp**
- Δ3 = unrelated − direct = **−3.3pp**（首次干净安慰剂测量）
- 三臂中 **direct 最高**；两种注入均不高于 direct。注入本身（无论内容相关性）在本轮为**轻微负向/中性**。

## 3. 骨架分解（强制）

| 注入物结尾类 | sibling | unrelated | Δ2(pp) |
|---|---|---|---|
| state_change_end | 18/25 | 19/26 | −1.1 |
| transfer_end | 9/13 | 10/13 | −7.7 |
| query_end | 4/5 | 4/5 | 0.0 |

效应未集中于任何骨架类；无正向分量可归因。

## 4. 纪律与附件

- **ITT**：135 行按所分臂全量分析；2 例 ineligible 留在 sibling 分母。
- **CopyGuard**：审计层开启，命中 **0**（脱敏成立，无抄袭信号；不覆盖 τ 判定）。
- **分母新旧对照（一行）**：旧口径 443/450/300（整改前快照，(req,plan) 对 vs distinct 计划）= 新口径 491（τ 计划行）/306（PASS∧去重）/55（在用 distinct）因去重时点与脱敏后坍缩而不同。
- **R3 附件**：提取保真 138 例（69 截断/69 扩张，e3/e6 集中）→ 疑溯源/计数口径缺陷，挂 B-3。
- 证据文件：`e8-run-table.json`（135 行：task/arm/injectant/deid_hash/verdict/tokens）、`e8-copyguard-audit.json`（0 命中）、`e8-analysis.json`。

## 5. 结论（语义明确）

**在这套系统第一次"语义明确的证据"里，注意力（同族骨架注入）相对形态对齐的安慰剂臂 Δ2 不显著（CI 含零），且不高于 direct。** 结合 e7 的 +15.7pp 被 a27 判为簇脆弱、且 e8 已消除主要混淆，**"沉积骨架迁移有效"未获支持**。

—— e8 之后按 P5a.43 §三 固定议程：发热检查点（资产数）、E2 立项、e9 锁序拦截器。
