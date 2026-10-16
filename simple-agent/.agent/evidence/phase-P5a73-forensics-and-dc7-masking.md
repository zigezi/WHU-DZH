# P5a.73 §二/§四 暂存区法医结论与 DC-7 脱敏落地证据

日期：2026-10-14
脚本：`scripts/secret_mask.py`（`--selftest`）→ `.agent/reports/dc7-mask-selftest.json`

## 一、暂存区法医五步（a73 §二）

**嫌疑窗口**：远端镜像 HEAD `edcebed1`（10-14）之后、v1.1 会话提交尝试之前（裁者边界声明）。
**裁者预判**：a71 收割核对轮自身报告写入（尸体 6→7）。

### 步骤与结果

1. **点名四文件**（`git status --porcelain`、`git diff --cached --stat`）：
   - `git diff --cached --stat` **为空** → **无任何已暂存内容**；四改动均为**未暂存工作区**改动：
     `c1-coldstart-gate.json`、`decomposition-report.md`、`e3-executor-smoke-v2.json`、`e3-v3-gate.json`。
2. **读 diff 定产出轮次**（报告头/内容）：
   | 文件 | HEAD 版 | 工作区版 | 内容判定 |
   |---|---|---|---|
   | c1-coldstart-gate.json | repeat_failure_v1 6/6 | **lock_order_v1 8/8 + naming_proof** | DC-3/DC-4「naming_proof」修复轮（a59/a60，10-13） |
   | decomposition-report.md | 生成 09-29 | 生成 **10-13T14:56** | monitor/plan_observer 滚动产物 |
   | e3-executor-smoke-v2.json | E3-000..n=7 | E3V21-00..n=4 | e3 v2.1 实验轮（a51，10-12） |
   | e3-v3-gate.json | admitted 13 | admitted 51 | e3 v3「bugs≥2」实验轮（a52/a53，10-12） |
3. **mtime 对会话时间线**（`stat -c '%y %n'`）：10-13 14:19 / 10-13 14:56 / 10-12 14:15 / 10-12 15:31。
   **均早于 a71（10-14 10:46）** → 裁者预判（a71 收割）**被证伪**。
4. **turn-events.jsonl 交叉验证**：`.agent/logs/turn-events.jsonl` 仅 1 行（10-13 16:40 `py_compile`），**无**四文件写入事件 → 无法交叉印证，记录为空见证。
5. **复现性探针**（零 token，决定性）：
   - `e3_executor.py --smoke-v2`（当前代码）→ 生成 `E3V21-03/04/06` n=3，**≠** 工作区 n=4 → 工作区为**旧版残留**。
   - `e3_generator_v3.py`（默认）→ admitted 13（=HEAD）；`--bugs 2` → admitted 46；**均 ≠** 工作区 51 → 工作区为**更旧配置残留**。
   - `c1_coldstart_gate.py` 默认 `--asset lock_order_v1` 且写 `naming_proof` → **工作区版=当前代码输出**（未运行以免 `provenance.revalidate` 改写 assets.json）。

### 结论与处置
- **证伪**：四改动**非** a71 产物，是 a50–a60 实验轮（10-12~10-13）遗留的未提交工作区残留，此后历轮提交均选择不带入。
- **合法产物 → 补提交**：`c1-coldstart-gate.json`（=当前代码默认输出，DC-3/DC-4 修复的 C-1 出生证据）。
- **碎屑 → 清场**（`git checkout --`）：`decomposition-report.md`（滚动快照）、`e3-executor-smoke-v2.json`（旧 v2.1 残留）、`e3-v3-gate.json`（旧 bugs≥2 残留），以及探针期间被覆盖的 `e3-pilot-tasks-v3.json`（还原至 HEAD）。
- 复现探针产物已全部还原；`git status` 余留仅本次合法交付。

## 二、DC-7 脱敏落地证据（a73 §四）

- **脱敏规则代码位置**：`scripts/secret_mask.py::mask_secrets`（前缀族正则：`sk-` / `ghp_/gho_/ghs_/ghr_/ghu_/ghz_` / `github_pat_` / `sk-ant-` / `sk-proj-` / `AKIA…` / `Bearer …`）。
- **命中动作**：以 `[REDACTED:<kind> len=N -> backend/.env]` 替换——**只留位置线索，销毁明文值**，不记录值本身。
- **一次含假密钥的摘要试跑**：`--selftest` 对含 `sk-FAKE…` / `ghp_FAKE…` / `ghz_FAKE…` 的假摘要脱敏。
  读数（`.agent/reports/dc7-mask-selftest.json`）：`raw_secret_values=3`、`hits=3`、
  **`plaintext_leak_after_mask=0`**、普通文本与短桩 `sk-x` 未误伤 → `all_pass=true`。
- **待办（用户侧/opencode 侧）**：摘要生成器须实际调用 `mask_secrets`（opencode compaction 管道接入点不在本仓；本仓提供可复用规则与自检）。

## 三、附带处置：key.txt 权限
- `key.txt`（用户放入的 GitHub token）原为 `-rw-r--r--`（全局可读）。已 `chmod 600`（`-rw-------`），并加入 `.gitignore`（`/key.txt`），防误提交。**值未读取、未外泄、未入任何制品。**

## 四、常设规则（a73 §三）
- 每会话开工先 `git status`，工作区不净先清算——已正式成类 **DC-8**（见 governance-defect-classes.md）。
