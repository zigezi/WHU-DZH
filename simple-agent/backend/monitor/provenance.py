"""P5a.30 B-3 / P5a.44 §三.3：资产溯源层（最小 schema）。

资产 = 带域标签的规则；每条记录：asset×语境(validated_domain)×信用级别×上次复验时间戳×证据。
只注册**已通过验证器**的资产；未验证不登记。
存储：.agent/reports/assets.json（tracked；规则文本为 L2，非敏感）。
"""
import json
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 生产注册表（唯一真值）。FILE 保留为向后兼容的覆写点（自检用隔离存储时直接赋临时路径）。
PRODUCTION_FILE = os.path.join(ROOT, ".agent", "reports", "assets.json")
FILE = PRODUCTION_FILE


def _active_file():
    """P5a.77 §二.1：注册表路径解析——SA_REGISTRY_PATH 优先（沙盒），否则 FILE（默认生产）。"""
    return os.environ.get("SA_REGISTRY_PATH") or FILE


def _is_production(path):
    return os.path.abspath(path) == os.path.abspath(PRODUCTION_FILE)


def _guard_production(path, allow):
    """DC-9 修法：写生产注册表须显式授权（production=True 或 SA_REGISTRY_PRODUCTION=1），缺省即沙盒。"""
    if _is_production(path) and not (allow or os.environ.get("SA_REGISTRY_PRODUCTION") == "1"):
        raise PermissionError(
            "DC-9: refusing to write PRODUCTION registry without explicit opt-in "
            "(pass production=True or set SA_REGISTRY_PRODUCTION=1); test/self-check "
            "scripts must set SA_REGISTRY_PATH to a temp copy")

CREDIT_LEVELS = ("T1_candidate", "field_validated", "T1", "T2", "T3")
SCHEMA_VERSION = "b3-v3"
STATUSES = ("active", "shadow", "dormant", "pending_revalidation", "revoked",
            "superseded", "ineligible")
# P5a.58 §二：影子期毕业条件（累计 ≥10 次影子点火 ∧ 零影子误伤）
SHADOW_GRADUATION = {"min_firings": 10, "max_misfires": 0}
# B-3 溯源层 schema（P5a.30 B-3 / P5a.54）：资产的最小必填字段
REQUIRED_FIELDS = ("asset_id", "type", "validated_domain", "credit_level", "status", "evidence")
ASSET_TYPES = ("interceptor_rule", "prompt_patch", "threshold_patch", "precedent_update")


def validate_asset(rec: dict) -> list:
    """返回缺失/非法字段清单（空 = 合法）。"""
    errs = []
    for f in REQUIRED_FIELDS:
        if not rec.get(f):
            errs.append(f"missing:{f}")
    if rec.get("credit_level") and rec["credit_level"] not in CREDIT_LEVELS:
        errs.append(f"bad_credit_level:{rec['credit_level']}")
    if rec.get("type") and rec["type"] not in ASSET_TYPES:
        errs.append(f"bad_type:{rec['type']}")
    return errs


def _load():
    path = _active_file()
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {"assets": []}
    return {"assets": []}


def _save(d, allow_production: bool = False):
    """P5a.82 §四：一切写路径必经此 I/O 层守卫（DC-9 下沉，堵 QB-2 绕过）。"""
    path = _active_file()
    _guard_production(path, allow_production)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def register_asset(rec: dict, production: bool = False) -> dict:
    d = _load()
    rec = dict(rec)
    rec.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
    rec.setdefault("status", "active")
    rec.setdefault("credit_level", "T1_candidate")
    rec["schema_version"] = SCHEMA_VERSION
    errs = validate_asset(rec)
    if errs:
        raise ValueError(f"invalid asset record: {errs}")
    d["assets"] = [a for a in d["assets"] if a.get("asset_id") != rec.get("asset_id")]
    d["assets"].append(rec)
    _save(d, production)
    return rec


def list_assets(domain: str = None):
    d = _load()
    if domain:
        return [a for a in d["assets"] if a.get("validated_domain") == domain]
    return d["assets"]


def set_credit(asset_id: str, level: str, evidence: str, production: bool = False) -> dict:
    d = _load()
    for a in d["assets"]:
        if a.get("asset_id") == asset_id:
            if level not in CREDIT_LEVELS:
                raise ValueError(f"bad credit_level: {level}")
            a["credit_level"] = level
            a.setdefault("revalidation_log", []).append(
                {"at": datetime.now().isoformat(timespec="seconds"),
                 "evidence": evidence, "result": "credit_raised", "level": level})
    _save(d, production)
    return next((a for a in d["assets"] if a.get("asset_id") == asset_id), None)


def shadow_event(asset_id: str, run_verdict: str, production: bool = False) -> dict:
    """P5a.58 §二：影子点火记账 + 自动毕业/降级。
    run_verdict=FAIL → shadow_firings+1（本会拦下的潜在救场）；=PASS → shadow_misfires+1（误伤）。
    毕业：firings≥10 ∧ misfires=0 → status=active；任一 misfire>0 → status=pending_revalidation（回炉）。"""
    d = _load()
    a = next((x for x in d["assets"] if x.get("asset_id") == asset_id), None)
    if a is None:
        return None
    if (run_verdict or "").upper() == "FAIL":
        a["shadow_firings"] = a.get("shadow_firings", 0) + 1
    else:
        a["shadow_misfires"] = a.get("shadow_misfires", 0) + 1
    if a.get("status") == "shadow":
        if a.get("shadow_misfires", 0) > SHADOW_GRADUATION["max_misfires"]:
            a["status"] = "pending_revalidation"
            a["shadow_note"] = "misfire>0 → 回炉"
            a.setdefault("revalidation_log", []).append(
                {"at": datetime.now().isoformat(timespec="seconds"),
                 "evidence": "shadow misfire", "result": "demote_shadow"})
        elif a.get("shadow_firings", 0) >= SHADOW_GRADUATION["min_firings"]:
            a["status"] = "active"
            a.setdefault("revalidation_log", []).append(
                {"at": datetime.now().isoformat(timespec="seconds"),
                 "evidence": f"shadow graduated: firings={a['shadow_firings']}, misfires=0",
                 "result": "promote_shadow"})
    _save(d, production)
    return a


def patch_asset(asset_id: str, production: bool = False, **fields) -> dict:
    d = _load()
    for a in d["assets"]:
        if a.get("asset_id") == asset_id:
            a.update(fields)
    _save(d, production)
    return next((a for a in d["assets"] if a.get("asset_id") == asset_id), None)


def supersede(asset_id: str, superseded_by: str, reason: str = "", production: bool = False) -> dict:
    d = _load()
    for a in d["assets"]:
        if a.get("asset_id") == asset_id:
            a["status"] = "superseded"
            a["superseded_by"] = superseded_by
            a["superseded_at"] = datetime.now().isoformat(timespec="seconds")
            if reason:
                a["superseded_reason"] = reason
    _save(d, production)
    return next((a for a in d["assets"] if a.get("asset_id") == asset_id), None)


def revoke(asset_id: str, reason: str, knowledge_moved_to: str = "negative_precedents", production: bool = False) -> dict:
    d = _load()
    for a in d["assets"]:
        if a.get("asset_id") == asset_id:
            a["status"] = "revoked"
            a["revoked_at"] = datetime.now().isoformat(timespec="seconds")
            a["revoked_reason"] = reason
            a["knowledge_moved_to"] = knowledge_moved_to
    _save(d, production)
    return next((a for a in d["assets"] if a.get("asset_id") == asset_id), None)


def revalidate(asset_id: str, evidence: str, result: str = "pass", production: bool = False):
    d = _load()
    for a in d["assets"]:
        if a.get("asset_id") == asset_id:
            a["last_revalidated"] = datetime.now().isoformat(timespec="seconds")
            a.setdefault("revalidation_log", []).append(
                {"at": a["last_revalidated"], "evidence": evidence, "result": result})
            if result != "pass":
                a["status"] = "pending_revalidation"
    _save(d, production)
    return next((a for a in d["assets"] if a.get("asset_id") == asset_id), None)
