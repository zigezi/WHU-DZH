"""P5a.30 B-3 / P5a.44 §三.3：资产溯源层（最小 schema）。

资产 = 带域标签的规则；每条记录：asset×语境(validated_domain)×信用级别×上次复验时间戳×证据。
只注册**已通过验证器**的资产；未验证不登记。
存储：.agent/reports/assets.json（tracked；规则文本为 L2，非敏感）。
"""
import json
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILE = os.path.join(ROOT, ".agent", "reports", "assets.json")

CREDIT_LEVELS = ("T1_candidate", "field_validated", "T1", "T2", "T3")
SCHEMA_VERSION = "b3-v3"
STATUSES = ("active", "dormant", "pending_revalidation", "revoked", "superseded", "ineligible")
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
    if os.path.exists(FILE):
        try:
            return json.load(open(FILE, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {"assets": []}
    return {"assets": []}


def _save(d):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    json.dump(d, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def register_asset(rec: dict) -> dict:
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
    _save(d)
    return rec


def list_assets(domain: str = None):
    d = _load()
    if domain:
        return [a for a in d["assets"] if a.get("validated_domain") == domain]
    return d["assets"]


def set_credit(asset_id: str, level: str, evidence: str) -> dict:
    d = _load()
    for a in d["assets"]:
        if a.get("asset_id") == asset_id:
            if level not in CREDIT_LEVELS:
                raise ValueError(f"bad credit_level: {level}")
            a["credit_level"] = level
            a.setdefault("revalidation_log", []).append(
                {"at": datetime.now().isoformat(timespec="seconds"),
                 "evidence": evidence, "result": "credit_raised", "level": level})
    _save(d)
    return next((a for a in d["assets"] if a.get("asset_id") == asset_id), None)


def patch_asset(asset_id: str, **fields) -> dict:
    d = _load()
    for a in d["assets"]:
        if a.get("asset_id") == asset_id:
            a.update(fields)
    _save(d)
    return next((a for a in d["assets"] if a.get("asset_id") == asset_id), None)


def supersede(asset_id: str, superseded_by: str, reason: str = "") -> dict:
    d = _load()
    for a in d["assets"]:
        if a.get("asset_id") == asset_id:
            a["status"] = "superseded"
            a["superseded_by"] = superseded_by
            a["superseded_at"] = datetime.now().isoformat(timespec="seconds")
            if reason:
                a["superseded_reason"] = reason
    _save(d)
    return next((a for a in d["assets"] if a.get("asset_id") == asset_id), None)


def revoke(asset_id: str, reason: str, knowledge_moved_to: str = "negative_precedents") -> dict:
    d = _load()
    for a in d["assets"]:
        if a.get("asset_id") == asset_id:
            a["status"] = "revoked"
            a["revoked_at"] = datetime.now().isoformat(timespec="seconds")
            a["revoked_reason"] = reason
            a["knowledge_moved_to"] = knowledge_moved_to
    _save(d)
    return next((a for a in d["assets"] if a.get("asset_id") == asset_id), None)


def revalidate(asset_id: str, evidence: str, result: str = "pass"):
    d = _load()
    for a in d["assets"]:
        if a.get("asset_id") == asset_id:
            a["last_revalidated"] = datetime.now().isoformat(timespec="seconds")
            a.setdefault("revalidation_log", []).append(
                {"at": a["last_revalidated"], "evidence": evidence, "result": result})
            if result != "pass":
                a["status"] = "pending_revalidation"
    _save(d)
    return next((a for a in d["assets"] if a.get("asset_id") == asset_id), None)
