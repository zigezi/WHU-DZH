"""P5a.20 便签 1：GT-vs-final 字段级 diff（纯函数，不依赖 tau）。

供 sidecar.rpc_reward 计算、scoring 落 span。只处理 DB 层数据；
不接触 hidden instruction（红线）。
"""
import json
from typing import Any, Dict, List

RESPOND = "respond"


def _short(v: Any, n: int = 160) -> Any:
    if isinstance(v, (dict, list)):
        s = json.dumps(v, ensure_ascii=False, default=str)
        return s[:n] + ("…" if len(s) > n else "")
    if isinstance(v, str):
        return v[:n] + ("…" if len(v) > n else "")
    return v


def data_diff(agent: Dict[str, Any], gt: Dict[str, Any], limit: int = 30) -> List[dict]:
    """比较两份 retail/airline data dict，返回有界字段级差异。"""
    diffs: List[dict] = []
    truncated = False
    entities = list({**agent, **gt}.keys())
    for entity in entities:
        a_e = agent.get(entity)
        g_e = gt.get(entity)
        if not isinstance(a_e, dict) and not isinstance(g_e, dict):
            continue
        a_e = a_e or {}
        g_e = g_e or {}
        for eid in sorted(set(a_e) | set(g_e)):
            av, gv = a_e.get(eid), g_e.get(eid)
            if av == gv:
                continue
            if isinstance(av, dict) and isinstance(gv, dict):
                for field in sorted(set(av) | set(gv)):
                    if av.get(field) != gv.get(field):
                        diffs.append({"entity": entity, "id": eid, "field": field,
                                      "gt": _short(gv.get(field)),
                                      "agent": _short(av.get(field))})
                        if len(diffs) >= limit:
                            truncated = True
                            break
            else:
                diffs.append({"entity": entity, "id": eid, "field": "*",
                              "gt": _short(gv), "agent": _short(av)})
                if len(diffs) >= limit:
                    truncated = True
            if truncated:
                break
        if truncated:
            break
    if truncated:
        diffs.append({"truncated": True})
    return diffs


def _key(action) -> str:
    name = action.get("name") if isinstance(action, dict) else getattr(action, "name", None)
    kwargs = action.get("kwargs", {}) if isinstance(action, dict) else getattr(action, "kwargs", {})
    return name + "|" + json.dumps(kwargs, ensure_ascii=False, sort_keys=True, default=str)


def _item(action) -> dict:
    name = action.get("name") if isinstance(action, dict) else getattr(action, "name", None)
    kwargs = action.get("kwargs", {}) if isinstance(action, dict) else getattr(action, "kwargs", {})
    return {"name": name, "kwargs": _short(kwargs, 120)}


def actions_diff(agent_actions, gt_actions, terminate=(), limit: int = 20) -> Dict[str, List[dict]]:
    """返回 agent 相对 GT 的 {missing, extra}（跳过 terminate/respond）。"""
    def norm(acts):
        out = {}
        for a in acts:
            name = a.get("name") if isinstance(a, dict) else getattr(a, "name", None)
            if name in terminate or name == RESPOND:
                continue
            out[_key(a)] = _item(a)
        return out

    ag = norm(agent_actions)
    gt = norm(gt_actions)
    missing = [gt[k] for k in gt if k not in ag][:limit]
    extra = [ag[k] for k in ag if k not in gt][:limit]
    return {"missing": missing, "extra": extra}
