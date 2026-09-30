# P5a.20 epoch-6 运行配置（direct-only 干净基线）

**目的**：P5a.20 §三.2 —— 摆脱坏 precedent 臂污染，重测真实 direct 水位；同时验证便签 1/2/3 的新仪器。

## 运行配置

| 项 | 值 |
|---|---|
| 日期 | 2026-09-29 |
| 模型 | deepseek-chat（响应 deepseek-flash，见既有别名警报） |
| key | 用户新供 key（`…489a`，已直连 200 验证；前一个 `…8f40` 为 401 无效，未使用） |
| backend | `SA_MAX_STEPS=30 ROUTER_MODE=direct`，pid 见启动时 |
| sidecar | 重启后含便签1 `rpc_reward` 新码，127.0.0.1:8010 |
| 范围 | `--tau-only --split train`（135 任务），tag `tau-`（报告 `tau-epoch-6.json`） |
| 臂 | **全部 direct，不注入**（`ROUTER_MODE=direct` 且 direct/measurement 均不更新 Thompson） |

启动命令：
```bash
# sidecar
scripts/tau_sidecar.sh stop && scripts/tau_sidecar.sh start
# backend
cd backend && SA_MAX_STEPS=30 ROUTER_MODE=direct \
  /root/miniconda3/envs/mini-agent/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
# epoch
cd backend && /root/miniconda3/envs/mini-agent/bin/python monitor/eval_loop.py \
  --epoch 6 --tau-only --split train --tag tau-
```
（detached：`setsid ... </dev/null > .agent/logs/epoch-6.log 2>&1 &`）

## 新仪器在本轮的落点
- `acceptance_check`/`verdict` 携带 `r_actions/r_outputs/data_diff/actions_diff/gt_data_hash/agent_data_hash`（便签1）。
- `arm_choice` 全为 `direct`；无 `precedent_injected`（便签3 的 direct 模式）。
- （便签2 初筛器离线运行，不影响本轮。）

## 验收方式（完成后）
- `tau-epoch-6.json`：135 条 loss/verdict；
- 与 watchlist（`.agent/reports/p5a20-watchlist.*`）对照：三案、邻近注入对、15 条 C4 GT 缺陷任务的结局；
- 与 e5（75.6% / SC 71.7%）比较：direct-only 真实水位是否高于 73.3%（e3 被坏臂污染）。
- 通过后 → 便签3 的 epoch-7（`freeze_precedents --epoch 7` + `SA_EPOCH=7 ROUTER_MODE=measurement` 固定 50/50）回答命题一。
