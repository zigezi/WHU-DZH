# P5a.66 落地证据：接管（回合末收割）+ 四件积压工单

## §一 尸体来源接管
- **主：回合末收割** → `scripts/code_harvest.py`（读本回合真实失败 JSONL `.agent/logs/turn-events.jsonl`，去重 (ts,command,exit)，并入 code_corpses；**不伪造、不造任务**）。
- **辅：操作即记** → `scripts/code_op_log.py`（长耗时命令用）。
- **否决**"保持现状"。
- 本次收割执行：**本回合 0 新**（无真实失败）→ 累计 6 具 / 4 类；触发线（30/3）未达。
- 终态方向：未来给工具调用层打自动钩子（按 naming_proof 同款：先证明钩子自己在真实执行路径点火）。

## §二 积压工单（有独立价值，死亡白捡）
1. **B-1 env_fingerprint 真指纹（MR-8 旧债）** ✅：
   - 新 `backend/monitor/env_state.py`（`observe(resp)` / `fingerprint()`）；
   - `worker` 每次 LLM 响应后 `env_state.observe(resp)`，并落 span 字段 `response_model`/`system_fingerprint`；
   - `routing.env_fingerprint()` 改为 `响应模型|system_fingerprint`（回退别名）。
   - 验证：`deepseek-flash|aeb56401ca74e127821c4f9126dcb669`（此前恒为别名 `deepseek-chat`）。
2. **ring_draft 否决消息措辞素材库** ✅：`ring-draft-prompt-notes.md`（"点火≠救场"→ 措辞为显性设计变量 + 候选变体）。
3. **sentinel-ledger 自动化** ✅：`scripts/sentinel_ledger.py`（从 assets.json + firing-audit.json 生成，11 行）；替代手工改账。
4. **organ 分诊 deploy/covered 拆分脚本化** ✅：`organ_ingest_corpses`（covered_by_existing/deploy_new）+ `organ_census`（cover_of 按 kind/错误串）口径一致；本批 deploy_new=0。

## §三 τ2/τ3
- 不采用（τ 已封线；962-run 普查吃干榨净）。执行：无动作。

## §四 触发线
- 代码尸体 ≥30 ∧ ≥3 类：当前 **6 具 / 4 类**（类的腿达标，欠量）→ 未触发，继续攒批。
