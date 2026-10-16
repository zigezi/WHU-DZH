#!/usr/bin/env bash
# P5a.79 §二.2 采集钩子安装器（一次性；幂等）。
#
# 目标：让所有 `bash -c "<cmd>"` 源入 op_log_hook.sh —— 手段是给**进程环境**注入 BASH_ENV。
# 做法：写入系统/用户 profile（登录/交互 shell 继承）+ 打印 opencode 启动环境的注入方式。
# 运行时无需任何手工步骤；但已运行的 opencode 服务需**重启**才继承新环境。
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$ROOT/scripts/op_log_hook.sh"
LOG="$ROOT/.agent/logs/code-ops.jsonl"
MARK="# >>> simple-agent op_log_hook (P5a.79) >>>"

ENVBLOCK="$MARK
export BASH_ENV=\"$HOOK\"
export CODE_OPS_LOG=\"$LOG\"
# <<< simple-agent op_log_hook <<<"

install_into() {
    local f="$1"
    touch "$f" 2>/dev/null || { echo "[skip] $f (不可写)"; return; }
    if grep -qF "$MARK" "$f" 2>/dev/null; then
        echo "[ok] 已安装：$f"
    else
        printf '\n%s\n' "$ENVBLOCK" >> "$f" && echo "[done] 写入：$f"
    fi
}

echo "== 采集钩子安装（P5a.79 §二.2）=="
echo "HOOK=$HOOK"
echo "LOG=$LOG"
install_into /etc/profile.d/simple-agent-ophook.sh
install_into "$HOME/.bashrc"
install_into "$HOME/.profile"
install_into "/etc/bash.bashrc"

cat <<EOF

== opencode 启动环境注入（关键；否则非交互 bash -c 不继承）==
当前 opencode 服务的进程环境不会被本脚本改写。要让采集对**下一次**会话生效，二选一：
  A) 由登录 shell 启动 opencode（已装 profile 则自动继承 BASH_ENV）；或
  B) 在 opencode 启动配置/容器 env 中设：
       BASH_ENV=$HOOK
       CODE_OPS_LOG=$LOG
自检：python scripts/op_log_hook_battery.py（naming_proof + 关闭回归）
EOF
