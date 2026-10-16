# 设计便签 2（第 0 步）— 线束保真初筛器 harness-fidelity screen

**依据**：P5a.16 §三 第 0 步 + P5a.20 §一.4（instruction⇄GT 一致性入机器检查）+ §三.1（批准便签）
**目标**：对 e4↔e5 全部不一致对（不只尾部）产出"候选隔离 + 理由"，机器初筛、**人审签字后才约束**（MR-7）。
**红线**：机器只产候选与理由，**不附 PASS/FAIL 判定**（防锚定），不落 instruction 明文。

## 1. 输入
- GT：`tau-bench` tasks（`tau_task_id`/`split` 已知）→ instruction / actions / outputs。
- 轨迹：`trace.db` 的 `spans`（`dialogue_turn`(role=user 即模拟器) / `tool_call` / `verdict` / `arm_choice`）。
- 元数据：`backend/requirements/tau/*.json`（tau_env/tau_task_id/sig/bucket）。

## 2. 五项检查（逐任务，逐对）

| # | 检查 | 机器方法 | 命中样例（已知） |
|---|---|---|---|
| C1 | **GT 自洽重放** | 从初始 data 依序 replay GT actions（排除 terminate）→ 必须 reward=1；否则任务定义坏 | 全局 sanity |
| C2 | **instruction⇄GT 动作集一致性**（新） | 从 instruction 抽实体/动作提及（商品名、订单号、件数、日期、航点），与 GT action set 比对 | R-105：instruction 提 Jigsaw 退货，GT 无 |
| C3 | **模拟器⇄GT 一致性** | 对每轮 user turn 抽约束（日期/航点/数量/商品），与 GT args 比对 | A-008："just Mohamed" vs GT 3 人；A-019："5/20"/"LGA" vs GT 5/19/JFK |
| C4 | **GT 前提可达性** | 逐步 replay，捕获任何 GT action error（锁序/不存在的航班） | R-105 锁序（已由工单 2 独立确认） |
| C5 | **臂/注入一致性标注** | 读 `arm_choice`/`precedent_injected`，标 `arm_e4/arm_e5/exploration/content_sha256` | A-019 异臂 → 丧失可比性 |

**比对为规范化后字符串匹配**（门店/商品名/日期 ISO 化）；C2/C3 需 NL 抽取，采用
**确定性优先**（GT 已有实体做词表 + 正则），仅对无法匹配项再选配 LLM 兜底（LLM 不落 instruction 明文）。

## 3. 输出与流程

```
.agent/reports/p5a20-screen-<epoch>.json
  per task: {task_id, tau_env, tau_task_id, arm_e4, arm_e5,
             candidates: [{check:"C2", verdict:"quarantine_candidate", reason:"...", evidence_span_ids:[...]}]}
```
- opencode 只产候选；**用户抽检签字** → `p5a20-quarantine-<epoch>.json`（约束性清单）。
- 隔离对移出变更点统计的分子分母，但**保留在原始 pass-rate**（诚实税）。

## 4. 复现/验证
- 先对已知 3 案 + 2 健康样本跑：期望 A-008/A-019/R-105 命中，A-027/A-007 不命中（C1–C4）。
- 全量：135 对 e4↔e5（按 req_id 对齐）。

## 5. 顺带修一处红线隐患（访问控制，P5a.20 §二）
`sidecar.py:202-217 rpc_list_tasks` 目前**明文返回 instruction**（与其 docstring"不返回完整 hidden instruction"矛盾）。
Ingest 只需 `sig`（md5）+ 动作名 + bucket。**设计**：`rpc_list_tasks` 改为返回
`instruction_sha256_16`（+ `instruction_chars`），不返回明文；ingest 落 REQ 时只存 md5。
另：updater 输入域 = epoch 报告 + trace.db（`updater.py:80-102` 已确认不读目录），
建议加常量 denylist `FORBIDDEN_INPUT_DIRS = {".agent/local"}` 作显式访问控制（纵深防御）。

## 6. 工作量
- `scripts/harness_screen.py`（新，~200 行）+ `rpc_list_tasks` 小改 + 测试。中风险（NL 抽取的误报率需人审兜底）。
