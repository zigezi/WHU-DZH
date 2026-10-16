# P5a.79 农场欠料处置：洁池 + 采集钩子（含接线状态诚实注记）

日期：2026-10-15
依据：a79 §二/§三；脚本 `scripts/op_log_hook.sh`、`install_op_hook.sh`、`op_log_hook_battery.py`
自证：`.agent/reports/op-log-hook-battery.json`（5/5）

## 一、洁池（§二.1，零 token）
- `code_corpses` schema 增 `source`(real/demo) + `capture` 字段（`trace_store._ensure_column` 兼容旧库）。
- a64 `--demo` 两具（`#1` ts16:00 pytest、`#2` ts16:01 import x）标注 **source=demo / capture=a64_demo**，隔离出校准分布。
- **触发线只计 real**：`code_corpses.real_count()/real_classes()`；`code_op_log`/`code_harvest` 计数与 `mine_input` 均改用 real-only。
- 读数：总计 8 = **6 real / 2 demo**；real 类 4（test_or_build_fail 2 / syntax_death 2 / timeout_loop 1 / env_missing 1）→ 6/30。

## 二、漏采尸体补录（§三，特例）
- 本会话 `scripts/attic/e3_substrate_check.py` 运行 rc=1（`ModuleNotFoundError: domains`）——同期有回报引用，准予补录：`source=real, capture=retroactive_session_report`。补录后 **6 real**。
- 下不为例：钩子（下节）建成后，漏采即死档，不再补。

## 三、采集钩子（§二.2，治本，零 token）
- **机制** `scripts/op_log_hook.sh`：作为 **`BASH_ENV`** 被 `bash -c "<cmd>"` 源入；注册 `EXIT` trap，把 `$BASH_EXECUTION_STRING`（`-c` 的整条命令）+ 退出码（可选 stderr 摘要，`CODE_OPS_CAPTURE_STDERR=1`）追加写 `code-ops.jsonl`。异常静默、**不改命令行为、不拦截**。
- **安装器** `scripts/install_op_hook.sh`：写入 `/etc/profile.d/` + `~/.bashrc` + `~/.profile` + `/etc/bash.bashrc`（带 marker，幂等），导出 `BASH_ENV`/`CODE_OPS_LOG`。
- **自证**（naming_proof + 关闭回归，5/5）：
  - `naming_proof`：必败命令 `bash -c 'false'` → 日志出现对应条目（rc=1）✓；
  - 成功命令 stdout/rc 保真 ✓；退出码不被改动 ✓；
  - **关闭回归**：`CODE_OPS_HOOK_DISABLE=1` → 不误记、不拦截、行为不变 ✓；
  - stderr 摘要（开启时）✓。
- **接线状态（诚实注记）**：opencode 的 bash 工具是**非交互 `bash -c`**（无 PS1、无 BASH_ENV 继承、非持久）。钩子只在进程环境含 `BASH_ENV` 时生效。安装器已落 profile；**本会话服务进程未继承**（不改运行中进程环境），故本轮**尚无透明采集**——**下个会话**若由登录 shell 启动（或 opencode 启动 env 注入 `BASH_ENV`）即透明接线。这是"存在≠在岗"纪律下的如实标注：机制已自证，接线待环境继承。

## 四、E2 主线（§二.3）
- 钩子接入后，E2 建设段工程活的失败将自动入池；设施事实清单已在 `.agent/evidence/phase-P5a76-e2-facility-facts.md`，待用户域事实。

## 五、盘面
- 校准池 **6 real / 4 类**（另 2 demo 隔离）；回归扫 `regression_sweep.py` **13 电池** GREEN（含钩子自证）；触发线 6/30、3/3 类。
