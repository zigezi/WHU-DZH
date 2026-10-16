#!/usr/bin/env python3
"""P5a.75 §五（零 token 工单）：镜像泄密扫描。

用 secret_mask 同族前缀规则扫描待同步内容与已推送快照，核查是否含密钥明文。
只记 kind/长度/文件，**不记值**。

  python scripts/mirror_leak_scan.py --repo /root/simple-agent --ref HEAD --label local-head
  python scripts/mirror_leak_scan.py --repo /root/WHU-DZH --ref 9ec0c8b --prefix simple-agent --label mirror-9ec0c8b
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from secret_mask import mask_secrets  # noqa: E402

R = os.path.join(ROOT, ".agent", "reports")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
# 掩码器自身含**故意**假密钥夹具（sk-FAKE… 等），非真泄密 → 排除，避免自指误报
# 用后缀匹配：带 subtree 前缀（如 simple-agent/）时相对路径前缀会变
EXCLUDE_SUFFIXES = (os.path.join("scripts", "secret_mask.py"),)


def scan_dir(rootdir, max_bytes=2_000_000):
    hits, scanned, skipped = [], 0, 0
    for dirpath, dirnames, filenames in os.walk(rootdir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, rootdir)
            if rel.endswith(EXCLUDE_SUFFIXES):
                skipped += 1
                continue
            try:
                if os.path.getsize(path) > max_bytes:
                    skipped += 1
                    continue
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except (UnicodeDecodeError, OSError):
                skipped += 1          # 二进制/不可读
                continue
            scanned += 1
            _, h = mask_secrets(text)
            for x in h:
                hits.append({"file": rel, "kind": x["kind"], "len": x["len"]})
    return scanned, skipped, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--prefix", default=None, help="subtree prefix like simple-agent")
    ap.add_argument("--label", required=True)
    args = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="leakscan-")
    try:
        tar = subprocess.run(["git", "-C", args.repo, "archive", args.ref] +
                             ([args.prefix] if args.prefix else []),
                             capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", tmp], input=tar.stdout, check=True)
        scanned, skipped, hits = scan_dir(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    out = {"label": args.label, "repo": args.repo, "ref": args.ref, "prefix": args.prefix,
           "files_scanned": scanned, "files_skipped_binary_large_or_excluded": skipped,
           "secret_hits": len(hits), "plaintext_leak": bool(hits), "hits": hits}
    os.makedirs(R, exist_ok=True)
    json.dump(out, open(os.path.join(R, f"mirror-leak-scan-{args.label}.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
