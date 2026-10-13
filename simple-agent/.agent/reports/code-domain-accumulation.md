# 代码域尸体攒批协议（P5a.64 §三，零 token）

## 一、仪表（已建成）
- `backend/monitor/code_corpses.py`：`add/classify/list_all/mine_input`；表 `code_corpses(ts,op,command,exit_code,error,death_class)`。
- `scripts/code_op_log.py`：**常态化落盘** opencode 代码操作日志 → `.agent/logs/code-ops.jsonl`(append) **并**入 `code_corpses`；支持 `--ingest-file`。
- `scripts/code_corpse_collect.py`：批量采集（`--log` / `--demo`）。
- 死亡分类（种子，待尸体确认）：`syntax_death / env_missing / timeout_loop / test_or_build_fail / op_fail`。

## 二、攒批期禁令（P5a.64 §三.2）
- **禁谓词起草**（ring_draft 保持关闭）；
- **禁任何代码域资产出生**；
- **禁能力声明**。
- **只攒尸体，不开药。**

## 三、Phase 1 再校准触发线（预注册，P5a.64 §三.3）
- 触发条件：代码尸体 **≥30** 且覆盖 **≥3 个 death_class**；
- 触发后：呈尸体库 + 器官分诊草稿 → 裁者人工金标准终裁 → 按 a59 同协议做代码域 Phase 1 校准（敏感性/特异性双线，合格线随批次构成预注册）。

## 四、出生要件继承（自始全套，P5a.64 §三.4）
可观测性证明 + `naming_proof` + 金丝雀电池 + C-1 + **影子模式**——一要件不免。

## 五、当前状态（攒批中）
- **尸体 6 具 / death_class 4 类**（含首批真实操作失败：timeout_loop / syntax_death / test_or_build_fail / env_missing；由本 session 观测的代码操作失败与 demo 组成）。
- 触发线（30 / 3）：**未达**（尸体数不足）→ 继续攒批。
- 落盘：`.agent/logs/code-ops.jsonl`。

## 六、换道裁决与双触发线（P5a.65）
- **不换道**：SWE-bench 属代理域，资产须在部署域尸体上出生；自有日志全保真、零 token、骑行真实工作。自有日志主线继续。
- **SWE-bench 双触发线（待命，非死亡）**：
  - **量线**：攒批停滞（真实工作喂不出 30 具）；
  - **多样性线**：Phase 1 代码域校准时死因类过窄（分诊尺测不出特异度）。
  - 任一线触发 → 启动时四件套预注册：① 零 token 可行性道钉 ② 污染金丝雀（e7 教训：DeepSeek 或见过 GitHub issue 语料）③ 预算上限 ④ 定位写明"语料富化，非能力声明"。
- **§四 禁令**：**禁止为攒尸体而人造任务跑批**（E3 已封顶此路）；**尸体只从真实工作中捡拾**。
- 状态：6 尸体 / 4 类；量线与多样性线**均未触发**。
