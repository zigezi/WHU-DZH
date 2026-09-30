"""P5a.33 §一：类型前缀伪真值脱敏（纯函数，零 LLM）。

规格（a30 §5.3 + a32 §一 + a33 §一）：
- 类型前缀伪真值：RES_/FLT_/ORD_/USR_/PAY_/ITEM_/NAME_ + _0x<hex>；
- 日期：**全体加同一固定偏移**（保先后/差值/相对今日 —— 不做"随机日"）；
- 金额/数值：保序保量级（固定比例缩放）；
- 注入物内共指一致（同原值→同假值）；生成确定性（seed）。
- 映射表为敏感物：调用方负责存本地未跟踪区；本模块只产出 mapping。

红线：不接触 instruction 明文。
"""
import hashlib
import re
from datetime import date, timedelta

TYPE_BY_KEY = {
    "reservation_id": "RES",
    "flight_number": "FLT",
    "order_id": "ORD",
    "user_id": "USR",
    "payment_method_id": "PAY",
    "payment_id": "PAY",
    "item_ids": "ITEM",
    "new_item_ids": "ITEM",
    "item_id": "ITEM",
    "first_name": "NAME",
    "last_name": "NAME",
    "name": "NAME",
}
DATE_KEYS = {"date", "dob", "created_at", "updated_at", "payment_date"}
AMT_KEYS = {"amount", "price", "total", "balance", "refund", "cost", "fee"}
DATE_OFFSET_DAYS = 1007
AMT_FACTOR = 1.37

_RE_ORDER = re.compile(r"#W\d{6,}")
_RE_PAY = re.compile(r"\b(?:credit_card|gift_card|certificate)_\d+\b")
_RE_FLT = re.compile(r"\b[A-Z]{2,3}\d{2,4}\b")
_RE_USER = re.compile(r"\b[a-z]+_[a-z]+_\d{3,5}\b")
_RE_RES = re.compile(r"\b(?=[A-Z0-9]*\d)[A-Z0-9]{6}\b")
_RE_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

_REAL_PATTERNS = {
    "order_id": _RE_ORDER,
    "user_id": _RE_USER,
    "payment_id": _RE_PAY,
    "flight_no": _RE_FLT,
    "reservation_id": _RE_RES,
}


def _fake(t, value, seed):
    h = hashlib.sha256(f"{seed}|{t}|{value}".encode("utf-8")).hexdigest()[:6].upper()
    return f"{t}_0x{h}"


def _shift_date(s):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if not m:
        return s
    y, mo, d = map(int, m.groups())
    try:
        nd = date(y, mo, d) + timedelta(days=DATE_OFFSET_DAYS)
    except ValueError:
        return s
    return nd.isoformat()


class DeIdentifier:
    def __init__(self, seed="e8"):
        self.seed = seed
        self.mapping = {}  # (type, real) -> fake  (injectant-internal co-reference)

    def _map(self, t, v):
        k = (t, v)
        if k not in self.mapping:
            self.mapping[k] = _fake(t, v, self.seed)
        return self.mapping[k]

    def _scrub(self, s):
        """对任意字符串做**就地**实体替换（含自由文本里的嵌入值）。"""
        s = _RE_ORDER.sub(lambda m: self._map("ORD", m.group(0)), s)
        s = _RE_PAY.sub(lambda m: self._map("PAY", m.group(0)), s)
        s = _RE_FLT.sub(lambda m: self._map("FLT", m.group(0)), s)
        s = _RE_USER.sub(lambda m: self._map("USR", m.group(0)), s)
        s = _RE_RES.sub(lambda m: self._map("RES", m.group(0)), s)
        s = _RE_DATE.sub(lambda m: _shift_date(m.group(0)), s)
        return s

    def _trans(self, key, val):
        if isinstance(val, str):
            if key in ("first_name", "last_name", "name") and val and not val.startswith("NAME_"):
                return self._map("NAME", val)
            return self._scrub(val)
        if key in AMT_KEYS and isinstance(val, (int, float)) and not isinstance(val, bool):
            return round(val * AMT_FACTOR, 2)
        return val

    def _args(self, args):
        out = {}
        for k, v in (args or {}).items():
            if isinstance(v, dict):
                out[k] = self._args(v)
            elif isinstance(v, list):
                out[k] = [self._args(x) if isinstance(x, dict) else
                          self._trans(k, x) for x in v]
            else:
                out[k] = self._trans(k, v)
        return out

    def plan(self, plan):
        return [{"tool": s.get("tool"), "args": self._args(s.get("args"))}
                for s in (plan or [])]


def lint_lint_parse_and_names(deid_plan):
    """检查 (b)：JSON 可解析 + 工具名合法。"""
    import json
    txt = json.dumps(deid_plan, ensure_ascii=False)
    json.loads(txt)
    bad = [s.get("tool") for s in deid_plan
           if not str(s.get("tool", "")).startswith("tau__")]
    return {"json_ok": True, "bad_tools": bad}


def lint_no_residual(orig_plan, deid_plan):
    """检查 (a)：脱敏后不含原始真值。"""
    orig = _collect_strings(orig_plan)
    deid = " ".join(_collect_strings(deid_plan))
    residual = sorted({v for v in orig if len(v) >= 4 and v in deid
                       and any(p.search(v) for p in _REAL_PATTERNS.values())})
    # 也扫 deid 文本里的真值模式
    pattern_hits = sorted({m.group(0) for p in _REAL_PATTERNS.values()
                           for m in p.finditer(deid)})
    return {"residual_real_values": residual[:20], "pattern_hits": pattern_hits[:20],
            "ok": not residual and not pattern_hits}


def lint_db_nonmember(deid_plan, db_members):
    """检查 (c)：所有伪真值对 DB dump 断言非成员。"""
    fakes = sorted({v for v in _collect_strings(deid_plan)
                    if re.match(r"^(RES|FLT|ORD|USR|PAY|ITEM|NAME)_0x", str(v))})
    members = sorted({f for f in fakes if f in db_members})
    return {"fakes": len(fakes), "db_members_of_fakes": members, "ok": not members}


def _collect_strings(obj):
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            out += _collect_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            out += _collect_strings(v)
    elif isinstance(obj, str):
        out.append(obj)
    return out
