# 治理缺陷类清单（元器官记忆体，P5a.67 §五）

> 每类：**现象 / 根因 / 结构性修法 / 状态**。目的：同类缺陷**结构性封堵**，不逐次道歉。

## DC-1 生成器吞人工立法注记
- **现象**：自动生成的 `sentinel-ledger.md` 覆盖了 v3 手工页脚（50-run 检查点等立法注记）。
- **根因**：立法文本与数据同处输出面，生成即覆盖。
- **修法**：立法文本进**生成模板的常设页脚**（`STANDING_RULES`），不进数据行；单源生成随行保留。
- **状态**：✅ 已修（commit `f529ada`）。

## DC-2 硬顶事后账（预算闸缺失）
- **现象**：阶段二首跑 1.85M > 1.5M 硬顶，事后才登记。
- **根因**：硬顶只是账本条目，非运行时闸。
- **修法**：**运行时预算闸**——任务间累计检查，触顶即停（`SA_BUDGET_CAP`）。
- **状态**：✅ 已修（`organ_stage2`）。

## DC-3 存在未接线（名实不符）
- **现象**：5 件名称型守卫因 τ 工具名 `tau__` 前缀，自部署起**从未活体点火**；审计的扑救是静态回放。
- **根因**：接线路径未被"真实执行路径"验证；存在 ≠ 在岗。
- **修法**：① `execute_tool` 内 `gname` 归一化；② **naming_proof 出生要件**——名称匹配守卫出生前须经真实 `execute_tool`、生产命名过零 token 点火证明，并入 C-1；③ 常驻**接线金丝雀**（9/9）。
- **状态**：✅ 已修（`042d3f7`/`a66`）。

## DC-4 C-1 保真度缺口
- **现象**：C-1 冷启动门 7/7 全过，却漏掉 DC-3（合成事件未走真实 execute_tool 命名路径）。
- **根因**：门的合成事件命名约定与生产不一致。
- **修法**：C-1 增 `naming_proof` 相（真实 execute_tool + 生产命名点火证明）。
- **状态**：✅ 已修（并入 C-1 出生证行）。

## DC-5 人工立法页脚易失（同类，预防）
- **现象/风险**：凡"手工维护的规则文本"置于自动产物中，都会被下一次生成吞掉。
- **修法**：一切常设规则进**模板单源**；数据生成不得覆盖规则区。
- **状态**：✅ 以 DC-1 为样板推广。

## DC-6 "点火≠救场"（设计变量，非缺陷，登记）
- **现象**：lock_order_v1 活体点火 3 次仅救 1 次。
- **处置**：否决消息**措辞质量**列为 `ring_draft` 显性设计变量（素材库 `ring-draft-prompt-notes.md`）。
- **状态**：登记（随 C① ring_draft 联调验证）。
---

## DC-7 密钥入上下文（P5a.72 §一）
- **现象**：compaction 摘要 "Important Details" 段含 **DeepSeek API key 与 GitHub classic token 明文值**，经截图进入对话——两处暴露。
- **根因**：摘要/日志/证据制品生成器无 secret 脱敏；"只存位置"纪律此前只覆盖 hidden instruction，未覆盖全部 secret 类。
- **修法**：① 一切 compaction/摘要/日志/证据制品只许存密钥的**位置**（`backend/.env`，mode 600），禁止存**值**；② 摘要生成器加密钥脱敏（正则被撞库式扫描 `sk-`/`ghz_`/`ghp_` 前缀）；③ 红线由"hidden instruction 明文禁令"扩展至**全部 secret 类**；④ 暴露面（opencode 会话上下文、compaction 摘要文件、对话记录）立即轮换，不等计划窗口。
- **状态**：立法中（值轮换为用户侧动作；掩码纪律即刻生效）。

---

## DC-8 工作区残留未清算（未暂存改动跨轮漂移）
- **现象**：四个 `reports/` 未暂存改动（10-12~10-13 实验轮残留：c1/e3-smoke/e3-v3-gate/decomposition）长期滞留工作区，至 a71/v1.1 会话被裁者误判为 a71 收割产物。
- **根因**：测试脚本就地写 tracked 报告，轮末未统一 `git status` 清算；提交只 stage 意图内文件，残留随轮漂移。法医证伪见 `.agent/evidence/phase-P5a73-forensics-and-dc7-masking.md`。
- **修法**：① **每会话开工先 `git status`，工作区不净先清算**；② 轮末收割增"工作区清点"一步；③ 测试产物二选一——补提交（注明来源轮次）或 `git checkout --` 清场，不留中间态；④ **清场先快照后清场**：checkout 前把待弃版本 `cp` 至 `.agent/local/`（不跟踪），保留可逆性（a74 §一 微修）。
- **状态**：✅ 已成类（a73 §二 法医定性；a74 §一 补微修④）。

---

## DC-9 自检污染生产注册表（silent instrument mutation）
- **现象**：`e3_substrate_check.py` 运行后把 `lock_order_v1` 重置回 `T1_candidate`，丢失 `field_validated` + `live_confirmed` + 5 条 `revalidation_log`（a76 建设段设施核验时发现）。
- **根因**：自检脚本 `register_asset(...)` 指向**真实** `.agent/reports/assets.json`，以初始候选态覆盖已晋级资产；无隔离存储。
- **修法**：① 自检/校验脚本一律走隔离存储（`organ_selftest` 的临时 `prov.FILE` 模板），禁写生产注册表；② 或 `register_asset` 对已存在 asset_id 做合并/保留富字段而非覆盖；③ §三 回扫触发面增"注册表 diff 应为空"核查。
- **状态**：✅ 已修（P5a.77 §二）：`provenance` 支持 `SA_REGISTRY_PATH` 沙盒 + `register_asset` 生产写须显式授权（缺省即沙盒）；`regression_sweep.py` 增注册表前后 hash 不变性断言；封线脚本移 `scripts/attic/` + `scripts/manifest` 清单。原发现：`.agent/evidence/phase-P5a76-instrument-mutation-finding.md`。

---

**元注**：本册是"元器官的记忆体"——每类缺陷的**修法即一条可复用的结构性不变式**，供未来域迁移与器官成熟复用。
