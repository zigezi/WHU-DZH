# scripts/attic — 封线时代脚本 · 只读归档（P5a.77 §二.3）

**此目录内脚本不参与任何运行。** 归档如下已封线路线（a54 收官 / a44 e8 结案 / e7 结案）的脚本：

- E3 代码域基板（a54 按预注册判据处死）：`e3_generator*`、`e3_executor*`、`e3_pilot*`、`e3_substrate_check`。
- e8 沉积注入线（a44 结案）：`e8_*`。
- e7 CopyGuard 审计（e7 结案）：`e7_copyguard_audit`。
- 随 e8 归档的 τ 衍生件：`l15_build_negative_precedents`（依赖 `e8_freeze`）。

## 纪律
1. **不可执行写路径**：本目录脚本默认不得写生产制品（含 `.agent/reports/assets.json`）。
2. **如需复活**：复制出 attic 后在 `scripts/manifest` 重新在册，并跑 `scripts/regression_sweep.py` 验证注册表不变性。
3. **复用规则（P5a.78 §三 裁定，固化）**：**attic 复用 = 复制，不原地运行。** E2 等新线从本目录**复制**所需 e8/e9 harness 件到其设施命名空间；副本须重新进入 `scripts/manifest` 在册清单并满足**当前**出生标准（含 `naming_proof` 等）。**归档封存的是运行权，不是源代码。** 原件永不在原地执行。
4. 归档脚本内的 `sys.path.insert(ROOT/scripts)` 依赖已随之失效，故**不可在原位直接运行**（这正是归档意图）。
