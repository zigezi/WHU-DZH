#!/usr/bin/env python3
"""DC-7 密钥脱敏（P5a.72 §一.2 立法 / P5a.73 §四 验证）。

纪律：一切 compaction/摘要/日志/证据制品只许存密钥的**位置**（backend/.env，mode 600），禁止存**值**。
本模块做撞库式扫描（已知前缀族正则），命中即以位置线索替换、销毁明文：

    mask_secrets(text) -> (redacted_text, hits)

不打印、不回写任何明文；自检用**假密钥**，验证输出中无明文残留。

    /root/miniconda3/envs/mini-agent/bin/python scripts/secret_mask.py --selftest
    printf '%s' "$SOME_SUMMARY" | /root/miniconda3/envs/mini-agent/bin/python scripts/secret_mask.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, ".agent", "reports")
LOCATION_HINT = "backend/.env"

# 前缀族（撞库式扫描；含文献/立法点名的 sk-/ghz_/ghp_，并覆盖 GitHub 现行族）
PATTERNS = [
    ("deepseek_key", re.compile(r"sk-[A-Za-z0-9_-]{16,}")),
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("github_token", re.compile(r"gh[pozrsu]_[A-Za-z0-9]{20,}")),
    ("github_token_ghz", re.compile(r"ghz_[A-Za-z0-9]{16,}")),
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai_key", re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}")),
    ("aws_akid", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("bearer", re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}")),
]


def mask_secrets(text):
    """返回 (脱敏文本, 命中列表)。命中只记 kind/长度，不记值。"""
    hits, out = [], text or ""
    for kind, pat in PATTERNS:
        def _sub(m, _k=kind):
            length = len(m.group(0))
            hits.append({"kind": _k, "len": length})
            return f"[REDACTED:{_k} len={length} -> {LOCATION_HINT}]"
        out = pat.sub(_sub, out)
    return out, hits


def _selftest():
    # 假密钥（非真实值）：仅用于验证脱敏生效
    fake = (
        "compaction summary\n"
        "Important Details:\n"
        f"DEEPSEEK_API_KEY=sk-FAKEdeadBEEF0123456789abcdefXYZ\n"
        "GITHUB_TOKEN=ghp_FAKE0000000000000000000000000000000000\n"
        "legacy=ghz_FAKE9999999999999999\n"
        "note=keep this normal text and a short sk-x stub\n"
    )
    # 逐条提取明文值（去重），用于"输出无明文"断言
    raw_values = sorted({m.group(0) for _, p in PATTERNS for m in p.finditer(fake)})
    redacted, hits = mask_secrets(fake)
    leaked = [v for v in raw_values if v in redacted]
    out = {
        "note": "DC-7 脱敏自检（假密钥；验证输出无明文）",
        "mask_rule_location": "scripts/secret_mask.py::mask_secrets",
        "patterns": [k for k, _ in PATTERNS],
        "raw_secret_values": len(raw_values),
        "hits": hits,
        "plaintext_leak_after_mask": len(leaked),
        "normal_text_preserved": "normal text" in redacted,
        "short_stub_preserved": "sk-x stub" in redacted,
        "all_pass": (len(raw_values) == 3 and len(hits) >= 3 and not leaked
                     and "normal text" in redacted and "sk-x stub" in redacted),
        "redacted_sample": redacted,
    }
    os.makedirs(R, exist_ok=True)
    json.dump(out, open(os.path.join(R, "dc7-mask-selftest.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


def main():
    if "--selftest" in sys.argv:
        return _selftest()
    data = sys.stdin.read()
    redacted, hits = mask_secrets(data)
    sys.stdout.write(redacted)
    print(f"\n[{len(hits)} secret(s) redacted]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
