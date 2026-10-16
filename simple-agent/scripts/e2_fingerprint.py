#!/usr/bin/env python3
"""P5a.88 §三：指纹绑定脚手架（taskbook_fingerprint.json；双向绑定；naming_proof）。"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")


def _sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def compute(ruleset_path):
    """评测器仪器指纹：规则集 + 单位表 + 抽取参数 + 提示词模板 + 版本。"""
    return {
        "ruleset_sha": _sha_file(ruleset_path) if os.path.exists(ruleset_path) else "missing",
        "unit_table_sha": _sha_file(os.path.join(SCRIPTS, "e2_unit_norm.py")),
        "eval_params_sha": _sha_file(os.path.join(SCRIPTS, "e2_eval_params.json")),
        "prompt_sha": _sha_file(os.path.join(SCRIPTS, "e2_prompt_v1.1.md")),
        "eval_version": json.load(open(os.path.join(SCRIPTS, "e2_eval_params.json"),
                                       encoding="utf-8")).get("ruleset_version", "?"),
        "prompt_version": "v1.1",
    }


def canon(fp):
    return hashlib.sha256(json.dumps(fp, sort_keys=True).encode()).hexdigest()[:16]


def write(ruleset_path, out=None):
    out = out or os.path.join(SCRIPTS, "taskbook_fingerprint.json")
    json.dump(compute(ruleset_path), open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


def verify(ruleset_path, taskbook_path, fp_path):
    """双向绑定：独立指纹文件 == 当前仪器；任务书内嵌同值。"""
    if not os.path.exists(fp_path):
        return False
    fp = json.load(open(fp_path, encoding="utf-8"))
    if fp != compute(ruleset_path):
        return False
    if taskbook_path and os.path.exists(taskbook_path):
        tb = open(taskbook_path, encoding="utf-8").read()
        key = canon(fp)
        if f"fingerprint: {key}" not in tb and key not in tb:
            return False
    return True


def _selftest():
    d = tempfile.mkdtemp()
    rs = os.path.join(d, "ruleset.json")
    json.dump({"required_sections": ["项目"]}, open(rs, "w"))
    fp_path = os.path.join(d, "fp.json")
    write(rs, fp_path)
    tb_ok = os.path.join(d, "tb_ok.md")
    open(tb_ok, "w").write(f"# taskbook\nfingerprint: {canon(json.load(open(fp_path)))}\n")
    tb_bad = os.path.join(d, "tb_bad.md")
    open(tb_bad, "w").write("# taskbook\nfingerprint: deadbeefdeadbeef\n")
    rs2 = os.path.join(d, "ruleset2.json")
    json.dump({"required_sections": ["项目", "经费"]}, open(rs2, "w"))

    checks = [
        ("np_positive", verify(rs, tb_ok, fp_path) is True),
        ("np_missing_fpfile", verify(rs, tb_ok, os.path.join(d, "nope.json")) is False),
        ("np_hash_mismatch", verify(rs2, tb_ok, fp_path) is False),
        ("np_taskbook_bad_embedded", verify(rs, tb_bad, fp_path) is False),
    ]
    n, passed = len(checks), sum(1 for _, ok in checks if ok)
    out = {"note": "P5a.88 §三 指纹脚手架 naming_proof", "n": n, "passed": passed,
           "all_pass": passed == n, "results": [{"case": c, "pass": ok} for c, ok in checks]}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "e2-fingerprint-selftest.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    print("usage: --selftest | build(ruleset) | verify(...)")
    sys.exit(2)
