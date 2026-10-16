#!/usr/bin/env python3
"""P5a.82 §三.7：filter_oplog_v1 自证电池（每条口径 ≥2 正 2 负；零 token）。

规则：signal / timeout / whitelist(build) / blacklist(benign drop) / gray / classify 修法。
全绿方可标 deployed。

  /root/miniconda3/envs/mini-agent/bin/python scripts/oplog_filter_battery.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.oplog_filter import filter_event  # noqa: E402
from monitor import code_corpses as cc  # noqa: E402

R = os.path.join(ROOT, ".agent", "reports")
checks = []


def ev(command, exit_code, error=""):
    return {"command": command, "exit_code": exit_code, "error": error}


def expect(name, e, want_action, want_tier=None, want_class=None):
    v = filter_event(e)
    ok = (v["action"] == want_action
          and (want_tier is None or v.get("tier") == want_tier)
          and (want_class is None or v.get("death_class") == want_class))
    checks.append({"case": name, "pass": ok, "got": v,
                   "want": {"action": want_action, "tier": want_tier, "death_class": want_class}})


def main():
    # 规则1 signal 必采（+2/-2）
    expect("signal_pos_139", ev("python x.py", 139), "collect", "signal", "signal_death")
    expect("signal_pos_137", ev("some_tool", 137), "collect", "signal", "signal_death")
    expect("signal_neg_rc1", ev("frobnicate", 1), "collect", "gray")      # 非信号 → 灰区
    expect("signal_neg_rc0", ev("some_tool", 0), "drop")                  # 无死亡

    # 规则2 timeout 必采（+2/-2）
    expect("timeout_pos_a", ev("timeout 5 sleep 10", 124), "collect", "timeout", "timeout_loop")
    expect("timeout_pos_b", ev("timeout 1 python slow.py", 124), "collect", "timeout", "timeout_loop")
    expect("timeout_neg_nowrap", ev("sleep 10", 124), "collect", "gray")  # 非 timeout(1) 包裹 → 灰
    expect("timeout_neg_rc0", ev("timeout 5 true", 0), "drop")

    # 规则3 白名单 build/test（+2/-2）
    expect("wl_pos_pytest", ev("pytest -q", 1, "AssertionError"), "collect", "build", "test_or_build_fail")
    expect("wl_pos_pym", ev("python -m pytest tests", 2, "ModuleNotFoundError: x"), "collect", "build", "env_missing")
    expect("wl_neg_rc0", ev("pytest -q", 0), "drop")
    expect("wl_neg_fmt", ev("cargo fmt", 1), "collect", "gray")           # cargo fmt 非 build/test → 灰

    # 规则4 黑名单丢（+2/-2）
    expect("bl_pos_grep", ev("grep foo bar", 1), "drop")
    expect("bl_pos_gitdiff", ev("git diff", 1), "drop")
    expect("bl_neg_signal", ev("grep foo bar", 139), "collect", "signal", "signal_death")  # 信号优先
    expect("bl_neg_unknown", ev("frobnicate", 1), "collect", "gray")

    # 规则5 灰区隔离（+2/-2）
    expect("gray_pos_a", ev("frobnicate --x", 3), "collect", "gray")
    expect("gray_pos_b", ev("sleep abc", 2), "collect", "gray")
    expect("gray_neg_grep", ev("grep", 1), "drop")
    expect("gray_neg_build", ev("pytest", 1, "AssertionError"), "collect", "build")

    # 规则6 classify 修法（废止一刀切；信号单列）
    classify_checks = [
        ("classify_signal", cc.classify("run", 139, "") == "signal_death"),
        ("classify_timeout", cc.classify("run", 124, "") == "timeout_loop"),
        ("classify_no_blanket", cc.classify("run", 1, "weird failure") == "op_fail"),
        ("classify_assert", cc.classify("run", 1, "AssertionError") == "test_or_build_fail"),
    ]
    for name, ok in classify_checks:
        checks.append({"case": name, "pass": ok})

    n, passed = len(checks), sum(1 for c in checks if c["pass"])
    out = {"note": "P5a.82 §三.7 filter_oplog_v1 自证电池（≥2 正 2 负/规则；零 token）",
           "deployed": passed == n, "n": n, "passed": passed, "results": checks}
    json.dump(out, open(os.path.join(R, "oplog-filter-battery.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"note": out["note"], "deployed": out["deployed"], "passed": passed, "n": n,
                      "fails": [c for c in checks if not c["pass"]]}, ensure_ascii=False, indent=1))
    return 0 if out["deployed"] else 1


if __name__ == "__main__":
    sys.exit(main())
