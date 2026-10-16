# P5a.44–45 落地证据：e9 部署资产（锁序拦截器）+ 销账 + harness 规格

## 1. e9 部署资产：锁序执行期拦截器 Path B'（a45 §二/§三.2）
- `backend/monitor/interceptor.py`：`OrderLockInterceptor`——确定性谓词：
  `modify_pending_order_items` 即将执行 ∧ 同订单 `modify_pending_order_address` **未成功** ∧ 该订单**未被否决过** → **否决执行**（返回合成结果，锁不扣）；once-per-order 状态位避免死循环。
- `backend/worker.py`：`execute_tool` 接拦截器（`SA_LOCK_INTERCEPTOR=1` 启用），点火记 `interceptor_fire` span；每任务 `lockguard.reset()`。
- **出生证**：validated_domain=τ，死因=锁序，证据=a28 回测(0/12)+B-2 电池。

## 2. B-2 金丝雀电池（a45 §三.1）
`scripts/e9_canary_battery.py` → `e9-canary-battery.json`：**7/7 通过**
（P1 items-first 必拦 / P2 once-per-order 放行 / P3 先地址不拦 / P4 异单独立 / P5 非目标工具不动 / P6 地址失败仍拦 / P7 合成文案正确）。
**验证器为电池，非 epoch**——token≈0。

## 3. 销账（a44 §四）
- `e8_analysis.py`：补 **Δ1/Δ3 簇 wild bootstrap 95% CI**——Δ1 −7.1pp(P≤0=0.90)、Δ3 −3.3pp(P≤0=0.74)，均非正。
- `e8_extraction_audit.py`：**R3∩在用注入物**——44 个在用注入物中 **36 个**源 run 带保真缺口 → "注入物=忠实蒸馏"叙事被削弱（不改 e8 结论性质，臂间同构）。

## 4. harness 规格（a45 §三.3）
`.agent/reports/e9-harness-spec.md`：随机化/冻结/形态对齐/簇 bootstrap/CopyGuard/运行表/ITT/脱敏管线——域无关化存档，E3 复用。

## 5. 发热门（a44 §三）
部署资产从 **0 → 1**（锁序拦截器，带电池出生证）。τ 域 epoch 级燃烧冻结；下一交付物=活资产，非文档。
