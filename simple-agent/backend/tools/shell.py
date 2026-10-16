import os
import re
import shlex
import subprocess
import threading

from monitor.collector import add_event

# 全局约束第 4 条：永久 deny（agent 不可触达）
DENY_PATTERNS = [
    r"(^|[;&|]\s*)(kill|pkill|killall)\b",
    r"(^|[;&|]\s*)systemctl\b",
    r"(^|[;&|]\s*)(shutdown|reboot|poweroff|halt)\b",
    r":\(\)\s*\{",
    r"mkfs(\.|\s)",
    r"dd\s+if=.*of=/dev/",
    r">\s*/dev/sd[a-z]",
]

# 只读命令：默认放行（含特例校验）
READ_ONLY = {
    "ls", "cat", "head", "tail", "wc", "grep", "egrep", "fgrep", "find",
    "echo", "pwd", "sed", "awk", "sort", "uniq", "cut", "tr", "which",
    "whoami", "env", "date", "stat", "file", "diff", "tee", "cd", "export",
    "sqlite3", "printf", "true", "test", "du", "df", "tree",
}

# 写命令：仅当所有路径参数 realpath 后位于 workspace/ 内才放行
WRITE_CMDS = {"rm", "cp", "mv", "touch", "mkdir", "rmdir", "ln", "chmod", "chown"}

# 允许的程序（残余风险：python -c 可绕过，由 G 层留痕 + MR-4 兜底）
ALLOW_PROGRAMS = {"python", "python3", "pip", "pip3", "pytest", "npm", "npx", "node"}

# git 只读子命令放行；commit/push 显式 deny；其余默认拒绝
GIT_READONLY = {"status", "diff", "log", "show", "branch", "rev-parse", "ls-files"}
GIT_DENY = {"commit", "push"}

# 显式 deny：网络出口默认关闭
NET_DENY = {"curl", "wget"}

# 重定向操作符
REDIRECT_OPS = {">", ">>"}

# 标准安全汇（字符设备，非文件写入；允许 2>/dev/null 这类常规用法）
REDIRECT_SAFE_SINKS = {"/dev/null", "/dev/stdout", "/dev/stderr"}

_OPERATORS = {"|", ";", "&&", "||"}
_last = threading.local()


def _real_in_workspace(path: str, work_dir: str) -> bool:
    if not path:
        return False
    if not os.path.isabs(path):
        path = os.path.join(work_dir, path)
    real = os.path.realpath(path)
    ws = os.path.realpath(work_dir)
    return real == ws or real.startswith(ws + os.sep)


def _tokenize(command: str):
    lex = shlex.shlex(command, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def _split_segments(tokens):
    segments, current = [], []
    for tok in tokens:
        if tok in _OPERATORS:
            if current:
                segments.append(current)
                current = []
        else:
            current.append(tok)
    if current:
        segments.append(current)
    return segments


def _check_redirects(tokens, work_dir):
    for i, tok in enumerate(tokens):
        if tok in REDIRECT_OPS:
            target = tokens[i + 1] if i + 1 < len(tokens) else ""
            if target in REDIRECT_SAFE_SINKS:
                continue
            if not _real_in_workspace(target, work_dir):
                return False, f"重定向目标越出 workspace: {target!r}"
    return True, ""


def _check_segment(tokens, work_dir):
    if not tokens:
        return True, ""
    ok, reason = _check_redirects(tokens, work_dir)
    if not ok:
        return ok, reason

    cmd = os.path.basename(tokens[0])
    args = tokens[1:]

    # 只读命令
    if cmd in READ_ONLY:
        if cmd == "find" and any(a in ("-exec", "-execdir", "-delete") for a in args):
            return False, "find 带 -exec/-delete 被拒绝"
        if cmd == "sqlite3" and "-readonly" not in args:
            return False, "sqlite3 必须带 -readonly（防止篡改 trace.db）"
        return True, ""

    # 写命令：所有路径参数必须落在 workspace 内
    if cmd in WRITE_CMDS:
        for a in args:
            if a.startswith("-"):
                continue
            if not _real_in_workspace(a, work_dir):
                return False, f"写命令路径越出 workspace: {a!r}"
        return True, ""

    # 程序类
    if cmd in ALLOW_PROGRAMS:
        return True, ""

    # git
    if cmd == "git":
        sub = args[0] if args else ""
        if sub in GIT_DENY:
            return False, f"git {sub} 被拒绝（版本控制只归人工）"
        if sub in GIT_READONLY:
            return True, ""
        return False, f"git {sub or '(none)'} 不在只读白名单"

    # 显式 deny
    if cmd in NET_DENY:
        return False, f"{cmd} 被拒绝（网络出口默认关闭）"

    return False, f"命令不在白名单内: {cmd}"


def _evaluate(command: str, work_dir: str):
    """返回 (allowed, reason)。命令替换一律拒绝；逐段过白名单。"""
    if "$(" in command or "`" in command:
        return False, "命令替换 $()/反引号一律拒绝"
    try:
        tokens = _tokenize(command)
    except ValueError as e:
        return False, f"shell 解析失败: {e}"
    for seg in _split_segments(tokens):
        ok, reason = _check_segment(seg, work_dir)
        if not ok:
            return False, reason
    return True, ""


def _block(trace_id, parent_span_id, command, reason):
    if trace_id:
        add_event(
            trace_id=trace_id, name="权限拦截", layer="G",
            span_type="permission_check", parent_span_id=parent_span_id,
            attributes={"cmd": command[:200], "verdict": "deny", "reason": reason},
        )
    raise PermissionError(f"Command blocked by guard: {reason}")


def run_command(work_dir: str, command: str, timeout: int = 30,
                trace_id: str = None, parent_span_id: str = None, **kwargs) -> str:
    # 全局永久 deny（与解析结果无关，直接命中即拦）
    for pattern in DENY_PATTERNS:
        if re.search(pattern, command):
            _block(trace_id, parent_span_id, command, f"命中永久 deny 规则: {pattern}")

    allowed, reason = _evaluate(command, work_dir)
    if not allowed:
        _block(trace_id, parent_span_id, command, reason)

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        _last.exit_code = result.returncode
        _last.stdout_tail = (result.stdout or "")[-500:]
        _last.stderr_tail = (result.stderr or "")[-500:]
        output = f"$ {command}\n"
        output += f"Exit code: {result.returncode}\n"
        if result.stdout:
            output += f"--- STDOUT ---\n{result.stdout[:3000]}\n"
        if result.stderr:
            output += f"--- STDERR ---\n{result.stderr[:2000]}\n"
        return output
    except subprocess.TimeoutExpired:
        _last.exit_code = 124
        _last.stdout_tail = ""
        _last.stderr_tail = "timeout"
        return f"Command timed out after {timeout}s: {command}"


def get_last_exec() -> dict:
    return {
        "exit_code": getattr(_last, "exit_code", None),
        "stdout_tail": getattr(_last, "stdout_tail", ""),
        "stderr_tail": getattr(_last, "stderr_tail", ""),
    }


run_command._last_exec_meta = get_last_exec
