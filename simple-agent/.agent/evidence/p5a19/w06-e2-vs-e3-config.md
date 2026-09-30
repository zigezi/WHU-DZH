# P5a.19 工单 6 — e2 vs e3 配置 diff（解释 76.3% 异常）

**结论**：e2（76.3%）与 e3（73.3%）**不可比**。两次运行处于不同测量配置：
e2 无臂选择（direct-only）且全部 τ 任务共用**一个退化签名**；e3 起才引入"逐任务 instruction 签名 + 双臂"。
"e2 高于 POLICY epoch"是**仪器替换**的结果，不是 POLICY 未超越校准前基线的证据。

## 1. 时间线

| 事件 | 时间 | commit |
|---|---|---|
| epoch-2 full run（135 任务，76.3%） | 2026-09-14 10:31 | `32004eb`（10:34 提交，P5a.5） |
| epoch-3 full run（135 任务，73.3%） | 2026-09-14 15:29 | `88000fc`（17:31 提交，P5a.6） |

两 run 之间只隔 `88000fc`（P5a.6）。

## 2. `88000fc` 改了什么（即测量路径变更）

```
backend/worker.py:
- sig_family = signature.sign(req.content)                      # 旧：签占位开场白 → 所有 τ 任务同族
+ sig_family = (tau_spec.get("sig") if tau_spec else None) or signature.sign(req.content)
                                                                 # 新：签 hidden instruction → 135 族

- router.update(sig_family, "direct", status.status == "success", total_tokens)
+ arm, explored = router.choose_meta(sig_family, ["direct","precedent-assisted"])
+ ... _inject_precedent(...)                                     # 新：第二臂 precedent-assisted
+ router.update(sig_family, arm, status.status == "success", total_tokens)
```

`backend/monitor/routing.py`：新增 `DEFAULT_ARMS = ["direct","precedent-assisted"]`。

## 3. 两 run 的可观测配置差异

| 维度 | epoch-2 | epoch-3 |
|---|---|---|
| 签名来源 | `signature.sign("你好，我需要帮助")` | hidden instruction 全文 |
| 签名基数 | **1 个族**（全部 τ 同族） | **135 族**（P5a.6 自述"max share 1.5%"） |
| 路由臂 | **仅 direct**（代码无臂分支） | direct + precedent-assisted |
| 先例注入 | 无 | 有（本次工单 1/3 证明：注入的是"上一任务"计划） |
| 报告分桶 | 无 | state-changing / read-only |

## 4. 证据

```bash
git show 88000fc --stat
git show 88000fc -- backend/worker.py | grep -E "^[+-].*(sig|arm|precedent|router)"
git log --format="%h %ad %s" --date=format:"%m-%d %H:%M" \
  --since="2026-09-14 00:00" --until="2026-09-14 23:59"
# 旁证：e2 期先例 sig 全为 4c2be0c87a8f（占位开场白签名）
sqlite3 -readonly backend/logs/trace.db \
 "SELECT substr(created_at,1,10) d, count(DISTINCT sig) FROM precedents GROUP BY d"
```

## 5. 对 P5a.19 §二 的支撑与补充

- 支撑"e2 悬案"的仪器解释：e2 与 e3 不是同一把尺子。
- **补充风险**：e2→e3 同时引入了 precedent-assisted 臂，而工单 1/3 证明该臂注入的
  是**语义无关的上一任务计划**。因此"加入第二臂"本身可能就是 e3 相对 e2 下降的候选原因之一。
  在测量模式（P5a.19 §四：固定 50/50 随机化）落地前，**不能**用 e2/e3 差值论证 POLICY 效果。
