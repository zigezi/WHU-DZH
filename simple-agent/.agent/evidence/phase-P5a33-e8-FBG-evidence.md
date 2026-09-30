# P5a.33 e8 工单 B/F/G 证据

## F. CopyGuard 全参数审计版（a30 §二.2 / a33 §三）
- `backend/monitor/copyguard.py`：`entity_values()`（含自由文本嵌入实体）+ `scan_trace()`（值进 args 且**未经先前工具结果**=命中；先前工具结果豁免）。
  **全参数扫描**（user_id/order_id/payment_id/flight_no/reservation_id/date），归一化去 `#`。**不改结局**。
- e7 全样本审计 `scripts/e7_copyguard_audit.py` → `e7-copyguard-audit.json`：
  **72 条注入，3 条命中，全部为 self**（A-000/A-005/A-029）；**sibling 0 命中**。
  → e7 的 sibling +17.5pp **不是字符串抄答案驱动**（弱支持"结构相关"）；答案泄漏集中在 self（与 a30 发现 3 一致）。
  → 脱敏后（伪真值）预期命中 = 0；任何命中 = 脱敏 lint 失效信号。

## B. worker e8 三臂接线（a33 §四 B）
- `backend/worker.py`：新增 `_e8_load()`（缓存 `e8-matrix-freeze.json` + `e8-deid-snapshot.json`）与 `_inject_frozen()`；
  `ROUTER_MODE=e8` 时按**冻结矩阵**取 arm(sibling/unrelated→注入脱敏计划；direct→不注入)，记 `arm_choice{source:e8-frozen}` + `precedent_injected{content_sha256_16=deid_hash, reason}`；e8 模式**不更新 Thompson**。
- 运行时注入的是**脱敏版**（无真值）；冻结矩阵来自 E（纯随机臂 + k=3）。

## G. 沙盒 shakedown（a32 §四 机械清单）
`scripts/e8_sandbox.py`（默认不 live）：

```
1_deid_lint3     : true    (443 计划三检全绿)
2_matrix_gates   : true    (top1 3.4% / distinct 63 / 同域 97.8%)
3_form_balance   : true    (sibling n=44 / unrelated n=44)
4_copyguard_e7   : true    (72 审计，3 命中全 self)
5_worker_e8_load : true    (matrix 135 行 / deid 443 行)
SANDBOX MECHANICAL: PASS
```

**未做**：`--live` 的 10 任务烟跑（耗 token，待授权）。

## 剩余 e8 门
- [ ] 用户抽检脱敏库 5–10 例（检查伪真值/共指/关系保持）——**待用户**。
- [ ] 10 任务 live 烟跑（可选，耗 token）。
- 上述完成 → 可签发 e8 开工令（三臂，~2h/10M tokens）。
