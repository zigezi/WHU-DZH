# P5a.6 · epoch-3 前置补丁指令（opencode 直接执行版）

> **性质**：小补丁指令，非新任务书。MR-1~MR-6 全部有效：每项改动单独 commit + 证据原文粘贴进 `.agent/evidence/phase-P5a6-evidence.md`。
> **目标**：修掉三个让 epoch"不可测"的缺陷，然后跑 epoch-3 并做首次双门对比。**顺序不许换**：补丁 1→2→3 全部验收通过后才许跑 epoch-3。

---

## 补丁 1：τ 任务签名改用 hidden instruction（修单族塌缩）

**现状 bug**：所有 τ REQ 的 `task` 字段是通用占位开场白，`signature.sign(req.content)` 把 135 条任务塌缩成同一个 sig_family `4c2be0c87a8f`，族级指标全废。

**改动**：
- τ 模式下（REQ 含 `tau_env` 字段），签名输入改为经 sidecar `get_instruction(session_id)` 取回的 **hidden instruction 全文**；常规任务仍签 `task` 文本，行为不变。
- 签名时机：eval_loop 提交任务前（ingest 时预签也可，写入 REQ JSON 的 `sig` 字段，二选一，探针哪个顺用哪个）。
- **红线**：hidden instruction 的明文**禁止**进 worker 对话历史、禁止进任何 span attributes 明文、禁止进 evidence 文件。日志和库里只出现 md5 后的 sig_family。evidence 里粘贴的是**族分布统计**，不是指令原文。

**验收**（SQL 输出原文粘贴）：
```bash
sqlite3 -readonly backend/logs/trace.db "SELECT sig_family, COUNT(*) FROM routes GROUP BY sig_family" 
# 或等价的 REQ 级统计：重签后 135 条 τ 任务散成 >=10 个族，最大族占比 <40%
```

---

## 补丁 2：启用 precedent-assisted 臂（让学习机制真的启动）

**现状 bug**：routing 全程只有 `direct` 一臂，`precedent-assisted` 从未启用，epoch 间无"处理组"，学习无从发生。

**改动**：
- `monitor/routing.py` 臂列表扩展为 `["direct", "precedent-assisted"]`，Thompson 采样 ε=0.1 不变。
- `worker.py`：任务开始且路由选中 `precedent-assisted` 时，查 `precedents`（按补丁 1 的新签名取相似先例，similarity ≥0.2 才注入），将先例的 **plan 摘要**注入系统/上下文。
- **注入上限**：摘要 ≤500 tokens（超出截断），防上下文爆炸；注入动作写 span `layer="L", type="precedent_injected", attributes={precedent_sig, similarity, tokens_injected}`。
- 臂选择本身写 span `type="arm_choice", attributes={sig_family, arm, exploration: bool}`。
- dev split 任务**固定走 direct 臂**（dev 是尺子，不许被处理污染）。

**验收**：
1. 一个 epoch 内两臂都有真实样本（SQL 查 `arm_choice` span 按 arm 分组计数，两臂均 >0）；
2. `precedent_injected` span 的 `tokens_injected` 全部 ≤500；
3. 老 REQ 单轮任务回归：direct 臂行为与 epoch-2 逐字段一致。

---

## 补丁 3：epoch 报告分桶（拆穿虚荣通过率）

**现状问题**：τ-bench 对纯查询任务偏松（GT 不改 db 时不做事也可能 reward=1），76.3% 的通过率是混合口径。

**改动**：
- `eval_loop.py` 报告新增分桶：按任务的 GT 是否改变 db 终态，把任务分为 `state-changing` / `read-only` 两桶，**分别报通过率、loss、token 均值**；判定逻辑用 τ 任务定义里的 db 断言是否为空，探针确认后写死。
- 总通过率保留，但报告里必须注明口径（混合/分桶三行并列）。

**验收**：epoch-3 报告中两桶分列，且 `read-only` 桶通过率 > `state-changing` 桶（若不成立，写说明进 evidence——这可能是更深的口径问题）。

---

## 然后：epoch-3 与首次双门

1. `python monitor/eval_loop.py --epoch 3 --tau-only --split train --tag tau-`（全量 135，成本护栏 ¥50/日不变，预估 ¥20±5；超预估 50% 自动停）。
2. 跑完执行 `python scripts/epoch_gate.py .agent/reports/tau-epoch-2.json .agent/reports/tau-epoch-3.json`，输出 MERGE/REJECT 结论。**注意：本次没有人工改动介入，epoch-3 相对 epoch-2 的唯一变量是补丁 1-3（测量修复+第二臂启用），这正是要隔离观察的处理效应。**
3. 产出 `.agent/reports/tau-epoch-3.md`，必含三读数：
   - **同族 token Δ**：epoch-2 vs epoch-3 同 sig_family 的 token 均值对比（补丁 1 后族可比了）；
   - **arm_value_delta**：precedent-assisted vs direct 的成功率 / 步数 / token 三列对比（允许 token 上升，看换来了什么）；
   - **分桶通过率**：state-changing 桶的通过率是 DeepSeek 的真实水位。
4. 全部证据（SQL 输出、报告、epoch_gate 结论）粘贴进 `.agent/evidence/phase-P5a6-evidence.md`，一个 commit 收尾。

## 明确不做

归因命中率（等 replay.py 金种子工厂，另立任务书）、AUROC2（无 OOD 标签，维持 ⬜）、updater 提案（等 epoch-3 真实失败样本出来再说）、任何新依赖。
