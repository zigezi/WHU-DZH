"""需求集加载与入库门禁（P1.1）。

规则：
- 每条需求一个 JSON 文件；
- 无 assertions 的需求直接拒绝入库（绑定率 100% 门禁）；
- split 只允许 train / dev。
"""
import glob
import json
import os
from typing import Dict, List

REQUIREMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_SPLITS = {"train", "dev"}
VALID_SEVERITIES = {"blocker", "major", "minor"}


class RequirementError(ValueError):
    pass


def load_requirement(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    req_id = data.get("req_id")
    if not req_id:
        raise RequirementError(f"{path}: 缺少 req_id")

    if data.get("split") not in VALID_SPLITS:
        raise RequirementError(
            f"{req_id}: split 必须属于 {sorted(VALID_SPLITS)}"
        )

    if not (data.get("task") or "").strip():
        raise RequirementError(
            f"{req_id}: 缺少 task 字段，拒绝入库（eval_loop 只允许用 task 喂模型）"
        )

    assertions = data.get("assertions") or []
    if not assertions:
        raise RequirementError(f"{req_id}: 无 assertions，拒绝入库（绑定率门禁）")

    for a in assertions:
        if not a.get("name"):
            raise RequirementError(f"{req_id}: assertion 缺少 name")
        # τ 任务的断言由 scoring.py 直接产出，无需 shell cmd
        if not a.get("cmd") and not data.get("tau_env"):
            raise RequirementError(f"{req_id}: assertion 缺少 cmd")
        if a.get("severity") not in VALID_SEVERITIES:
            raise RequirementError(
                f"{req_id}: assertion severity 必须属于 {sorted(VALID_SEVERITIES)}"
            )

    data.setdefault("title", req_id)
    data.setdefault("ears_text", "")
    data.setdefault("budget", {})
    return data


def load_all() -> List[Dict]:
    paths = sorted(glob.glob(os.path.join(REQUIREMENTS_DIR, "*.json")))
    paths += sorted(glob.glob(os.path.join(REQUIREMENTS_DIR, "tau", "*.json")))
    return [load_requirement(p) for p in paths]


def load_by_split(split: str) -> List[Dict]:
    return [r for r in load_all() if r["split"] == split]


def get(req_id: str) -> Dict:
    for req in load_all():
        if req["req_id"] == req_id:
            return req
    raise KeyError(f"requirement not found: {req_id}")
