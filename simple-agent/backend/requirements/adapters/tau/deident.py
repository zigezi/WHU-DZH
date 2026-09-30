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
    "product_id": "PROD",
    "email": "EMAIL",
    "first_name": "NAME",
    "last_name": "NAME",
    "name": "NAME",
    # 地址族（类 I 实例数据；a35 未列，按最保守处理）
    "address": "ADDR", "address1": "ADDR", "address2": "ADDR",
    "city": "ADDR", "state": "ADDR", "zip": "ADDR", "country": "ADDR",
}
_RE_ITEM = re.compile(r"\b\d{10}\b")
_RE_MONEY = re.compile(r"\$\s?\d[\d,]*\.\d{2}")
_RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
DATE_KEYS = {"date", "dob", "created_at", "updated_at", "payment_date"}
AMT_KEYS = {"amount", "price", "total", "balance", "refund", "cost", "fee"}
DATE_OFFSET_DAYS = 1007
AMT_FACTOR = 1.37

_RE_ORDER = re.compile(r"#W\d{6,}")
_RE_PAY = re.compile(r"\b(?:credit_card|gift_card|certificate|paypal)_\d+\b")
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
    def __init__(self, seed="e8", name_vocab=None):
        self.seed = seed
        self.mapping = {}  # (type, real) -> fake  (injectant-internal co-reference)
        toks = sorted({n for n in (name_vocab or []) if n and len(n) >= 3},
                      key=len, reverse=True)
        self._name_re = (re.compile(r"\b(" + "|".join(re.escape(t) for t in toks) + r")\b")
                         if toks else None)

    def _map(self, t, v):
        k = (t, v)
        if k not in self.mapping:
            self.mapping[k] = _fake(t, v, self.seed)
        return self.mapping[k]

    def _scrub_money(self, m):
        num = float(m.group(0).replace("$", "").replace(",", "").strip())
        return "$" + f"{round(num * AMT_FACTOR, 2):.2f}"

    def _scrub(self, s):
        """对任意字符串做**就地**实体替换（含自由文本里的嵌入值）。"""
        s = _RE_ORDER.sub(lambda m: self._map("ORD", m.group(0)), s)
        s = _RE_PAY.sub(lambda m: self._map("PAY", m.group(0)), s)
        s = _RE_FLT.sub(lambda m: self._map("FLT", m.group(0)), s)
        s = _RE_USER.sub(lambda m: self._map("USR", m.group(0)), s)
        s = _RE_RES.sub(lambda m: self._map("RES", m.group(0)), s)
        s = _RE_ITEM.sub(lambda m: self._map("ITEM", m.group(0)), s)
        s = _RE_EMAIL.sub(lambda m: self._map("EMAIL", m.group(0)), s)
        if self._name_re is not None:
            s = self._name_re.sub(lambda m: self._map("NAME", m.group(0)), s)
        s = _RE_MONEY.sub(self._scrub_money, s)
        s = _RE_DATE.sub(lambda m: _shift_date(m.group(0)), s)
        return s

    def _trans(self, key, val):
        if isinstance(val, str):
            if key in TYPE_BY_KEY and val and not val.startswith(
                    ("RES_", "FLT_", "ORD_", "USR_", "PAY_", "ITEM_", "PROD_", "NAME_", "ADDR_")):
                return self._map(TYPE_BY_KEY[key], val)
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


PSEUDO_PREFIXES = ("RES_", "FLT_", "ORD_", "USR_", "PAY_", "ITEM_", "PROD_",
                   "NAME_", "ADDR_", "EMAIL_")
# IV 类（领域词表/枚举）：允许保留裸值
ENUM_KEYS = {"origin", "destination", "cabin", "flight_type", "insurance",
             "trip_type", "status", "source", "request_type", "payment_type"}


def classify_lint(deid_plan, enums=None):
    """P5a.35 §二/§三 值分类法：
    I-III 类须为伪真值/平移值；IV 类（枚举键）允许封闭词表裸值；
    其余裸字符串 → unclassified（rb ⑤ 候选 F）。
    """
    enums = enums or {}
    ok, unclassified, iv_bare = [], [], []
    for key, val in _pairs(deid_plan):
        if not isinstance(val, str) or not val or key == "tool":
            continue
        if val.startswith(PSEUDO_PREFIXES):
            ok.append((key, val, "I-III"))
        elif key in DATE_KEYS or key == "expression" or _RE_DATE.match(val) or _RE_MONEY.search(val):
            ok.append((key, val, "II"))
        elif key in AMT_KEYS:
            ok.append((key, val, "II"))
        elif key in ENUM_KEYS and val.lower() in {v.lower() for v in enums.get(key, set())}:
            iv_bare.append((key, val))
        elif key in ("origin", "destination") and re.match(r"^[A-Z]{3}$", val):
            iv_bare.append((key, val))          # IV：IATA 码（形状即封闭词表）
        elif key == "reason":
            iv_bare.append((key, val))          # IV：取消原因封闭短语集
        else:
            unclassified.append((key, val))
    return {"iv_bare": iv_bare, "unclassified": sorted(set(unclassified))[:40],
            "unclassified_n": len(set(unclassified)),
            "ok": not unclassified}


def _pairs(obj, key=None):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += _pairs(v, k)
    elif isinstance(obj, list):
        for v in obj:
            out += _pairs(v, key)
    elif isinstance(obj, str):
        out.append((key, obj))
    return out


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
