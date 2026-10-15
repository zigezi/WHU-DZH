"""P5a.82 §三：采集过滤口径 v1（filter_oplog_v1）。

对 code-ops.jsonl 逐行判级：signal / timeout / build(白名单) / drop(黑名单) / gray(灰区)。
- 必采：rc>=128（信号死亡）；rc==124 且 timeout(1) 包裹（超时）。
- 白名单采：构建/测试工具族且 rc!=0。
- 黑名单丢：良性控制流（grep/diff/test/…）非零。
- 灰区隔离：其余非零 → 采集但 tier=gray，不计触发线、不进校准池。
零 token、纯确定性。
"""
import os
import re

SIGNAL_RC = 128

# 构建/测试工具族（首词；多词模式特殊处理）
_WHITELIST_SINGLE = {"pytest", "make", "gcc", "g++", "javac", "tsc", "mypy", "ruff"}
_WHITELIST_SUB = {"cargo": {"test", "build"}, "go": {"test", "build"},
                  "npm": {"test", "build"}, "pnpm": {"test", "build"},
                  "yarn": {"test", "build"}}
# 良性控制流（首词）；git 仅 status/diff/log
_BLACKLIST_SINGLE = {"grep", "diff", "test", "[", "which", "find", "ls", "cat",
                     "head", "tail", "wc", "sort", "uniq", "comm", "cmp"}
_BLACKLIST_GIT_SUB = {"status", "diff", "log"}

_PIPE = re.compile(r"\| |\|;|&&|\|\||;| \| ")


def _first_toks(cmd: str):
    seg = re.split(r"&&|\|\||;|\|", cmd or "", maxsplit=1)[0].strip()
    return seg.split()


def _base(tok: str) -> str:
    return os.path.basename(tok or "")


def is_signal(rc: int) -> bool:
    return rc >= SIGNAL_RC


def is_timeout(toks) -> bool:
    return bool(toks) and _base(toks[0]) == "timeout"


def is_whitelist(toks) -> bool:
    if not toks:
        return False
    b = _base(toks[0])
    if b in _WHITELIST_SINGLE:
        return True
    if b in ("python", "python3"):
        return "-m" in toks and any(t in ("pytest",) for t in toks)
    if b == "cmake":
        return "build" in toks
    if b in _WHITELIST_SUB:
        subs = [t for t in toks[1:] if not t.startswith("-")]
        return bool(subs) and subs[0] in _WHITELIST_SUB[b]
    return False


def is_blacklist(toks) -> bool:
    if not toks:
        return False
    b = _base(toks[0])
    if b in _BLACKLIST_SINGLE:
        return True
    if b == "git":
        subs = [t for t in toks[1:] if not t.startswith("-")]
        return bool(subs) and subs[0] in _BLACKLIST_GIT_SUB
    return False


def _subclass(ev) -> str:
    e = (ev.get("error") or "").lower()
    if "syntaxerror" in e or "indentationerror" in e:
        return "syntax_death"
    if "modulenotfound" in e or "importerror" in e:
        return "env_missing"
    return "test_or_build_fail"


def filter_event(ev: dict) -> dict:
    """返回 {action: collect|drop, tier, death_class, reason}。rc==0 恒 drop。"""
    rc = int(ev.get("exit_code", 0) or 0)
    if rc == 0:
        return {"action": "drop", "reason": "no_death"}
    toks = _first_toks(ev.get("command") or "")
    if is_signal(rc):
        return {"action": "collect", "tier": "signal", "death_class": "signal_death"}
    if rc == 124 and is_timeout(toks):
        return {"action": "collect", "tier": "timeout", "death_class": "timeout_loop"}
    if is_whitelist(toks):
        return {"action": "collect", "tier": "build", "death_class": _subclass(ev)}
    if is_blacklist(toks):
        return {"action": "drop", "reason": "benign_nonzero"}
    return {"action": "collect", "tier": "gray", "death_class": "op_fail"}
