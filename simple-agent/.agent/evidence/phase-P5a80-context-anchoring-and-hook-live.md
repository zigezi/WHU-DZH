# P5a.80 执行：尸体语境锚定（schema）+ 采集钩子活体验证与两个实抓缺陷

日期：2026-10-15
依据：a80 §一/§三；脚本 `scripts/op_log_hook.sh`、`backend/monitor/code_corpses.py`、`trace_store.py`

## 一、§三 立法落地：尸体语境锚定（零 token）
- `code_corpses` 增三字段：`git_head` / `env_fingerprint` / `schema_v`（`trace_store._ensure_column` 兼容旧库）。
- `code_corpses.add()` 采集时刻自动写入：`git_head` = `git rev-parse --short HEAD`；`env_fingerprint` = `env_state.fingerprint()`（B-1 设施）；`schema_v` = `"cc-v2"`。
- **旧条目**（8 具中 id 1–8 在加列前产生）：三字段为 `NULL` → `list_all` 归一为 **`unknown`**，**不报错、不弃尸**（a80 §三）。分析工具（`mine_input` 等）不受影响。
- 校验：`PRAGMA table_info` 含新列；`list_all` 对旧条目返回 `unknown`。

## 二、§一 采集钩子：活体验证（重要更正）
- **事实更正**：上一轮我判定"本会话不继承 BASH_ENV、须下会话接线"——**错**。安装器落 profile 后，opencode 的 shell **本会话即已继承** `BASH_ENV`；钩子在 09:28Z 起**已自动采集**我的真实工具命令（code-ops.jsonl 出现多行命令条目）。故"下会话第一件事"提前在本会话达成。
- 活体证据：登录 shell 内 `bash -c '<必败命令>'` → 日志出现 `exit_code=127` 条目（`oplog_live_probe_cmd_zzz`）。钩子**在岗**。

## 三、实抓两个缺陷（诚实）
1. **JSON 换行缺陷（已修）**：多行 shell 命令含**字面换行**，旧 `__oplog_jsonstr` 未转义 → JSONL **断行**、逐行解析失败（`Invalid control character`）。修法：`s=${s//$'\r'/\\r}; s=${s//$'\n'/\\n}`；验证：多行命令 → 单行合法 JSON（`\n` 转义）。
2. **误判洪水风险（待裁，未修）**：钩子记**全部**命令的退出码；`classify()` 对任意 `exit_code!=0` 落入 `test_or_build_fail`。shell 日常有大量良性非零（`grep` 无匹配、`diff` 有差异、`[ ]` 假、管道 `SIGPIPE`…）——**回合末收割一跑，农场会被良性非零灌爆**，污染校准分布（a68）。**故本轮不跑 harvest**，请裁者定过滤口径（例：只收特定 op/命令族；或加"investigation vs work"标注；或仅收崩溃类 rc）。
3. **洁净**：实抓期间的元命令/探针行已从 `code-ops.jsonl` 清除（重置为 4 条历史种子）；DB 未受污染（仍 6 real/2 demo）。

## 四、§二/§四/§五
- §二（漂移不影响可分析性三层）、§四（既有裁决重申）、§五（混合版本语料库不视缺陷）——裁定，无动作。

## 五、盘面
- 回归扫 13 电池 GREEN、注册表不变性保持；校准池 6 real/4 类；钩子**在岗**（待裁过滤口径后方可安全收割）；E2 建设段待用户域事实。
