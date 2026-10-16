#!/usr/bin/env python3
"""τ-bench 批量入库与分族（P5a 5a.4 + P5a.9 签名归一化）。

- 仅接 test split（airline + retail）；retail train 只在报告中登记，不入库；
- signature 去重（相似度 >0.85 视为同族，保留代表）；
- **签名归一化（P5a.9 §三.1）**：族签名改用 **GT 动作类型序列**（粗粒度），
  再对 <3 的小族做确定性合并，使 train 集族数 10~30、最大族 <30%、每族 ≥3。
  选型理由：动作类型签名无需 NLP/实体归一化，且天然不暴露 instruction 明文，只存 md5。
- 按族分层切 train/dev（dev 占比 ≥15%）；
- 生成 `.agent/reports/tau-ingest.md`。

红线：instruction 明文（含归一化明文）禁入 worker 历史/span/证据，只存 md5。
"""
import hashlib
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from requirements.adapters.tau.bridge import SidecarClient  # noqa: E402
import signature  # noqa: E402

REQ_DIR = os.path.join(BACKEND, "requirements", "tau")
REPORT_DIR = os.path.join(ROOT, ".agent", "reports")
REPORT = os.path.join(REPORT_DIR, "tau-ingest.md")

DEDUP_THRESHOLD = 0.85
DEV_RATIO = 0.15
BUDGET = {"max_steps": 30, "max_tokens": 200000, "timeout_s": 1200}
TOKENS_PER_TURN = 2000
TURNS = 15
PRICE_CNY_PER_MTOKEN = 2.0


def _req_id(env_name, task_id):
    tag = "A" if env_name == "airline" else "R"
    return f"TAU-{tag}-{task_id:03d}"


def _cat(action: str) -> str:
    for p in ("get_", "find_", "list_", "search_"):
        if action.startswith(p):
            return "read"
    if action == "calculate":
        return "compute"
    if action.startswith("think"):
        return "think"
    if action.startswith("transfer"):
        return "transfer"
    return "write"


def _family_key(actions):
    """GT 动作类型序列（排序后的多重集）作为粗粒度族键。"""
    return "|".join(sorted(_cat(a) for a in actions))


def _md5(s):
    return hashlib.md5(s.encode()).hexdigest()[:12]


def _cluster_train(train_items):
    """对 train 任务做族聚类 + <3 小族确定性合并。返回 key -> family_label。"""
    groups = defaultdict(list)
    for it in train_items:
        groups[_family_key(it["actions"])].append(it)
    ordered = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    big, small = [], []
    for key, members in ordered:
        (big if len(members) >= 3 else small).append([key, list(members)])
    for key, members in small:
        ks = set(key.split("|")) if key else set()
        best, best_j = None, -1.0
        for b in big:
            bs = set(b[0].split("|")) if b[0] else set()
            j = len(ks & bs) / max(1, len(ks | bs))
            if j > best_j or (j == best_j and best is not None and len(b[1]) > len(best[1])):
                best_j, best = j, b
        if best is None:
            big.append([key, list(members)])
        else:
            best[1].extend(members)
    key_to_label = {}
    for key, _members in big:
        key_to_label[key] = _md5("family::" + key)
    return key_to_label


def main():
    client = SidecarClient()
    all_tasks = []
    registry = {}
    for env_name in ("airline", "retail"):
        data = client.list_tasks(env_name, "test")
        registry[env_name] = data["count"]
        for t in data["tasks"]:
            all_tasks.append({
                "env": env_name, "id": t["id"],
                "instruction": t["instruction"],
                "actions": t.get("actions", []),
            })
    try:
        retail_train = client.list_tasks("retail", "train")["count"]
    except Exception:
        retail_train = None

    # 去重
    reps, dropped = [], 0
    for t in all_tasks:
        if any(signature.similarity(t["instruction"], r["instruction"]) > DEDUP_THRESHOLD
               for r in reps):
            dropped += 1
            continue
        reps.append(t)

    # 分层切 train/dev（先按 sig 排序，再抽样）
    for t in reps:
        t["sig_raw"] = signature.sign(t["instruction"])
    reps.sort(key=lambda x: x["sig_raw"])
    dev_n = max(1, int(len(reps) * DEV_RATIO + 0.999))
    dev_idx = set(range(0, len(reps), max(1, len(reps) // dev_n))[:dev_n])

    train_items = [reps[i] for i in range(len(reps)) if i not in dev_idx]
    dev_items = [reps[i] for i in range(len(reps)) if i in dev_idx]

    key_to_label = _cluster_train(train_items)

    def label_for(item):
        key = _family_key(item["actions"])
        if key in key_to_label:
            return key_to_label[key]
        # dev 兜底：按类别集 Jaccard 找最近的 train 族
        ks = set(key.split("|")) if key else set()
        best, best_j = None, -1.0
        for k, lab in key_to_label.items():
            bs = set(k.split("|")) if k else set()
            j = len(ks & bs) / max(1, len(ks | bs))
            if j > best_j:
                best_j, best = j, lab
        return best if best else _md5("family::" + key)

    os.makedirs(REQ_DIR, exist_ok=True)
    for fn in os.listdir(REQ_DIR):
        if fn.startswith("TAU-") and fn.endswith(".json"):
            os.remove(os.path.join(REQ_DIR, fn))

    written = []
    for i, t in enumerate(reps):
        req_id = _req_id(t["env"], t["id"])
        split = "dev" if i in dev_idx else "train"
        try:
            bucket = client.task_bucket(t["env"], t["id"], "test")
        except Exception:
            bucket = "unknown"
        req = {
            "req_id": req_id,
            "split": split,
            "title": f"tau-bench {t['env']} task {t['id']}",
            "task": "你好，我需要帮助",
            "tau_env": t["env"],
            "tau_task_id": t["id"],
            "tau_task_split": "test",
            "tau_bucket": bucket,
            "assertions": [
                {"name": "db_final_state", "severity": "blocker", "tau": True},
                {"name": "actions_match", "severity": "blocker", "tau": True},
            ],
            "budget": dict(BUDGET),
            "source": f"tau-bench/{t['env']}",
            "sig": label_for(t),
        }
        with open(os.path.join(REQ_DIR, f"{req_id}.json"), "w", encoding="utf-8") as f:
            json.dump(req, f, ensure_ascii=False, indent=2)
        written.append(req)

    train_written = [r for r in written if r["split"] == "train"]
    n_dev = sum(1 for r in written if r["split"] == "dev")
    fam = defaultdict(int)
    for r in train_written:
        fam[r["sig"]] += 1
    fam_sizes = sorted(fam.values())
    n_sc = sum(1 for r in written if r.get("tau_bucket") == "state-changing")
    n_ro = sum(1 for r in written if r.get("tau_bucket") == "read-only")
    est_tokens = len(written) * TURNS * TOKENS_PER_TURN * 2
    est_cost = est_tokens / 1_000_000 * PRICE_CNY_PER_MTOKEN

    os.makedirs(REPORT_DIR, exist_ok=True)
    lines = [
        "# τ-bench ingest 报告（5a.4 + P5a.9 签名归一化）",
        "",
        f"- 解析范围：test split only",
        f"- 原始任务数：airline={registry.get('airline')} + retail={registry.get('retail')} "
        f"= {len(all_tasks)}",
        f"- 去重丢弃：{dropped}（阈值 similarity>{DEDUP_THRESHOLD}）",
        f"- 入库 REQ 数：{len(written)}（train={len(train_written)}, dev={n_dev}）",
        f"- dev 占比：{n_dev/len(written):.1%}（要求 ≥15%）",
        f"- retail train（登记、本期不入库）：{retail_train}",
        f"- 分桶：state-changing={n_sc} / read-only={n_ro}",
        "",
        "## 签名归一化（P5a.9 §三.1）",
        "",
        f"- 选型：GT 动作类型序列（read/write/compute/think/transfer 多重集）+ <3 小族确定性合并",
        f"- train 族数：**{len(fam)}**（要求 10~30）",
        f"- 最大族占比：**{max(fam_sizes)/len(train_written):.1%}**（要求 <30%）",
        f"- 最小族规模：**{fam_sizes[0]}**（要求 ≥3）",
        f"- 族规模分布：{fam_sizes}",
        "",
        "## 成本预估（双模型口径）",
        "",
        f"- 单 epoch token 预估：{est_tokens:,}；成本 ≈ ¥{est_cost:.2f}",
        "",
        "## 入库清单（前 10 条示例）",
        "",
        "| req_id | split | sig_family | tau_env | tau_task_id |",
        "|---|---|---|---|---|",
    ]
    for r in written[:10]:
        lines.append(f"| {r['req_id']} | {r['split']} | {r['sig']} | {r['tau_env']} | {r['tau_task_id']} |")
    lines.append("")
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[tau_ingest] raw={len(all_tasks)} dropped={dropped} written={len(written)} "
          f"(train={len(train_written)}, dev={n_dev})")
    print(f"[tau_ingest] families={len(fam)} max_share={max(fam_sizes)/len(train_written):.1%} "
          f"min_size={fam_sizes[0]} sizes={fam_sizes}")
    print(f"[tau_ingest] report -> {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
