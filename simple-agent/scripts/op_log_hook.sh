#!/usr/bin/env bash
# P5a.79 §二.2 工具调用层采集钩子（a66 §一 D 类解禁）。
#
# 机制：作为 BASH_ENV 被 `bash -c "<cmd>"` 源入。注册 EXIT trap，把本次 shell 的
# `$BASH_EXECUTION_STRING`（即 `-c` 传入的整条命令）+ 退出码（可选 stderr 摘要）
# 追加写入 code-ops.jsonl。**不改命令行为、不拦截**；任何异常都静默退出。
#
# 用法（由 install_op_hook.sh 安装，或临时）：
#   CODE_OPS_LOG=/path/code-ops.jsonl BASH_ENV=/path/op_log_hook.sh bash -c 'false'
# 禁用：CODE_OPS_HOOK_DISABLE=1（走关闭回归）

# 禁用路径：不装 trap、不写日志、零副作用
if [ "${CODE_OPS_HOOK_DISABLE:-0}" = "1" ]; then
    return 0 2>/dev/null || exit 0
fi

__oplog_file="${CODE_OPS_LOG:-$HOME/.local/state/simple-agent/code-ops.jsonl}"
__oplog_stderr=""

# 最小 JSON 字符串转义（避免每条命令 fork python；须处理换行，否则 JSONL 断行）
__oplog_jsonstr() {
    local s=$1
    s=${s//\\/\\\\}
    s=${s//\"/\\\"}
    s=${s//$'\r'/\\r}
    s=${s//$'\n'/\\n}
    s=${s//$'\t'/\\t}
    printf '"%s"' "$s"
}

__oplog_emit() {
    local cmd="$1" rc="$2" err=""
    [ -z "$cmd" ] && return 0
    if [ -n "$__oplog_stderr" ] && [ -s "$__oplog_stderr" ]; then
        err="$(tail -c 200 "$__oplog_stderr" 2>/dev/null | tr '\n' ' ')"
    fi
    mkdir -p "$(dirname "$__oplog_file")" 2>/dev/null
    printf '{"ts":"%s","op":"shell","command":%s,"exit_code":%s,"error":%s}\n' \
        "$(date +%FT%T 2>/dev/null)" "$(__oplog_jsonstr "$cmd")" "${rc:-0}" \
        "$(__oplog_jsonstr "$err")" >> "$__oplog_file" 2>/dev/null
    return 0
}

# stderr 摘要（可选；默认关，避免改变工具 stderr 语义）
if [ "${CODE_OPS_CAPTURE_STDERR:-0}" = "1" ]; then
    __oplog_stderr="$(mktemp 2>/dev/null)"
    if [ -n "$__oplog_stderr" ]; then
        exec 2> >(tee -a "$__oplog_stderr" >&2)
    fi
fi

__oplog_fini() {
    local rc=$?
    # stderr 经进程替换异步落盘，稍等其刷写
    [ -n "$__oplog_stderr" ] && sleep 0.1
    __oplog_emit "$BASH_EXECUTION_STRING" "$rc"
    [ -n "$__oplog_stderr" ] && rm -f "$__oplog_stderr"
    return $rc
}

# 只在 `bash -c` 场景记录（有 BASH_EXECUTION_STRING）；否则不接线
if [ -n "$BASH_EXECUTION_STRING" ]; then
    trap '__oplog_fini' EXIT
fi
return 0 2>/dev/null || exit 0
