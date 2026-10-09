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

# ---- P5a.37 §三：分类法注册表（生成器与 lint 的单一事实源）----
# 类：I 标识符 / II 数值日期金额 / III 个人标识 / IV 封闭词表 / FREE 自由文本
FIELD_CLASS = {
    # I
    "order_id": "I", "reservation_id": "I", "user_id": "I",
    "payment_method_id": "I", "payment_id": "I", "item_id": "I", "item_ids": "I",
    "new_item_ids": "I", "product_id": "I", "certificate_id": "I",
    "flight_number": "I",
    # II
    "date": "II", "dob": "II", "created_at": "II", "updated_at": "II",
    "payment_date": "II", "amount": "II", "price": "II", "total": "II",
    "balance": "II", "refund": "II", "cost": "II", "fee": "II", "expression": "II",
    # III
    "address": "III", "address1": "III", "address2": "III", "city": "III",
    "zip": "III", "email": "III", "phone": "III",
    "first_name": "III", "last_name": "III", "name": "III",
    # IV
    "origin": "IV", "destination": "IV", "cabin": "IV", "flight_type": "IV",
    "insurance": "IV", "state": "IV", "country": "IV", "status": "IV",
    "source": "IV", "reason": "IV", "trip_type": "IV", "baggages": "IV",
    "total_baggages": "IV", "nonfree_baggages": "IV", "product_type": "IV",
    # 非实体
    "tool": "FREE", "summary": "FREE", "thought": "FREE", "reasoning": "FREE",
    "content": "FREE",
}
PREFIX_BY_KEY = {
    "order_id": "ORD", "reservation_id": "RES", "user_id": "USR",
    "payment_method_id": "PAY", "payment_id": "PAY", "item_id": "ITEM",
    "item_ids": "ITEM", "new_item_ids": "ITEM", "product_id": "PROD",
    "certificate_id": "CERT", "flight_number": "FLT",
    "address": "ADDR", "address1": "ADDR",
    "address2": "ADDR", "city": "ADDR", "zip": "ADDR", "phone": "PHONE",
    "email": "EMAIL", "first_name": "NAME", "last_name": "NAME", "name": "NAME",
}


def field_class(key):
    """未命中注册表 → 默认从严 I（P5a.37 §三 实现铁律）。"""
    return FIELD_CLASS.get(key, "I")


def prefix_for(key):
    return PREFIX_BY_KEY.get(key, "XID")


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
# P5a.38 §二.2：金额形态（含裸小数）统一走 II 类缩放
_RE_DEC = re.compile(r"(?<![\d.])\d[\d,]*\.\d{1,2}(?![\d.])")
_RE_NUM = re.compile(r"(?<![\d.])\d+(?:\.\d+)?(?![\d.])")
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
    def __init__(self, seed="e8", name_vocab=None, db_sets=None):
        self.seed = seed
        self.mapping = {}  # (type, real) -> fake  (injectant-internal co-reference)
        toks = sorted({n for n in (name_vocab or []) if n and len(n) >= 3},
                      key=len, reverse=True)
        self._name_re = (re.compile(r"\b(" + "|".join(re.escape(t) for t in toks) + r")\b")
                         if toks else None)
        # P5a.37 §四 / P5a.38 §二.1：DB 全量实体字典抹除（词界 + 大小写 + 复数 + 名称词元变体容忍）
        self._db_subs = []
        for pref, vals in (db_sets or {}).items():
            alts = set()
            for v in vals:
                if not v or len(v) < 4:
                    continue
                alts.add(v)
                if pref in ("NAME", "PROD") and " " in v:      # 多词名 → 词元变体
                    for tok in v.split():
                        if len(tok) >= 4:
                            alts.add(tok)
            if alts:
                rx = re.compile(
                    r"(?<![A-Za-z0-9_])(?:" +
                    "|".join(re.escape(a) for a in sorted(alts, key=len, reverse=True)) +
                    r")s?(?![A-Za-z0-9_])", re.IGNORECASE)
                self._db_subs.append((rx, pref))

    def _dbscrub(self, s):
        for rx, pref in self._db_subs:
            s = rx.sub(lambda m: self._map(pref, m.group(0)), s)
        return s

    def _map(self, t, v):
        k = (t, v)
        if k not in self.mapping:
            self.mapping[k] = _fake(t, v, self.seed)
        return self.mapping[k]

    def _scale_money(self, m):
        try:
            num = float(m.group(0).replace("$", "").replace(",", "").strip())
        except ValueError:
            return m.group(0)
        return f"{round(num * AMT_FACTOR, 2):.2f}"

    def _scrub(self, s, money=True):
        """就地脱敏：**先**平移日期、缩放金额（在原始文本上），**再**做实体替换，
        以免缩放破坏已生成的伪真值（P5a.38 §二）。money=False 供 expression 专用路径。"""
        s = _RE_DATE.sub(lambda m: _shift_date(m.group(0)), s)
        if money:
            s = _RE_DEC.sub(self._scale_money, s)  # 金额（含裸小数、含 $ 前缀）
        s = self._dbscrub(s)                        # DB 字典（词界+大小写+词元变体）
        s = _RE_ORDER.sub(lambda m: self._map("ORD", m.group(0)), s)
        s = _RE_PAY.sub(lambda m: self._map("PAY", m.group(0)), s)
        s = _RE_FLT.sub(lambda m: self._map("FLT", m.group(0)), s)
        s = _RE_USER.sub(lambda m: self._map("USR", m.group(0)), s)
        s = _RE_RES.sub(lambda m: self._map("RES", m.group(0)), s)
        s = _RE_ITEM.sub(lambda m: self._map("ITEM", m.group(0)), s)
        s = _RE_EMAIL.sub(lambda m: self._map("EMAIL", m.group(0)), s)
        if self._name_re is not None:
            s = self._name_re.sub(lambda m: self._map("NAME", m.group(0)), s)
        return s

    def _scale_all_numbers(self, s):
        """表达式内：整数与小数全部按同一比例缩放（P5a.38 §二.2）。"""
        return _RE_NUM.sub(self._scale_money, s)

    def _trans(self, key, val):
        cls = field_class(key)
        if cls in ("I", "III"):
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return self._map(prefix_for(key), str(val))
            if isinstance(val, str) and val and not val.startswith(PSEUDO_PREFIXES):
                return self._map(prefix_for(key), val)
            return self._scrub(val) if isinstance(val, str) else val
        if isinstance(val, str):
            if key == "expression":
                return self._scale_all_numbers(self._scrub(val, money=False))  # 仅此一处缩放
            return self._scrub(val)  # IV 裸词保留；嵌在其中的 id/日期/金额仍抹
        if cls == "II" and isinstance(val, (int, float)) and not isinstance(val, bool):
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
                   "NAME_", "ADDR_", "EMAIL_", "CERT_", "PHONE_", "XID_")
# IV 类（领域词表/枚举）：允许保留裸值
ENUM_KEYS = {"origin", "destination", "cabin", "flight_type", "insurance",
             "trip_type", "status", "source", "request_type", "payment_type"}


def classify_lint(deid_plan, enums=None):
    """P5a.35 §二/§三 值分类法：
    I-III 类须为伪真值/平移值；IV 类（枚举键）允许封闭词表裸值；
    其余裸字符串 → unclassified（rb ⑤ 候选 F）。
    """
    ok, unclassified, iv_bare = [], [], []
    for key, val in _pairs(deid_plan):
        if not isinstance(val, str) or not val:
            continue
        cls = field_class(key)
        if cls == "FREE":
            continue
        if cls == "IV":
            iv_bare.append((key, val))
            continue
        if val.startswith(PSEUDO_PREFIXES):
            ok.append((key, val, "I-III"))
        elif cls == "II":
            ok.append((key, val, "II"))
        else:  # I/III 未脱 → 从严判 unclassified
            unclassified.append((key, val))
    return {"iv_bare": iv_bare, "unclassified": sorted(set(unclassified))[:40],
            "unclassified_n": len(set(unclassified)),
            "ok": not unclassified}


_RE_YEAR = re.compile(r"^\d{4}$")


def entityish(v):
    """类 I/III 标识符形状（排除年份、普通短词、枚举词）。"""
    if not isinstance(v, str) or len(v) < 4:
        return False
    if _RE_YEAR.match(v):
        return False
    if re.search(r"[0-9_#@.]", v):        # 含数字或特殊符 → 标识符
        return True
    return len(v) >= 7                    # 纯词需较长（降低普通词 FP）


_RE_TWO = re.compile(r"(?<![\d.])\d+\.\d{2}(?![\d.])")


_RE_NUMTXT = re.compile(r"\d[\d,]*(?:\.\d+)?")


def lint_price_residual(deid_plan, orig_plan):
    """P5a.38 §二.3：金额残值——deid 的两位小数必须能由**同文档原始数值×1.37**解释，
    否则视为未缩放残值（文档内可解释性，避免稠密价格库的撞号 FP）。"""
    orig_nums = _RE_NUMTXT.findall(" ".join(_collect_strings(orig_plan)))
    scaled = set()
    for x in orig_nums:
        try:
            scaled.add(f"{round(float(x.replace(',', '')) * AMT_FACTOR, 2):.2f}")
        except ValueError:
            pass
    deid_txt = " ".join(_collect_strings(deid_plan))
    toks = set(_RE_TWO.findall(deid_txt))
    hits = sorted(t for t in toks if t not in scaled)
    return {"hits": hits[:20], "n": len(hits), "ok": not hits}


_DB_RX_CACHE = None


def _db_rx(db_values):
    global _DB_RX_CACHE
    if _DB_RX_CACHE is None or _DB_RX_CACHE[0] is not db_values:
        vals = sorted({v for v in db_values if entityish(v)}, key=len, reverse=True)
        rx = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(re.escape(v) for v in vals)
                        + r")(?![A-Za-z0-9_])")
        _DB_RX_CACHE = (db_values, rx)
    return _DB_RX_CACHE[1]


def lint_db_dictionary(deid_plan, db_values):
    """P5a.37 §四：机器④——输出中不得出现任何 DB 真实标识符值（词边界匹配）。"""
    txt = " ".join(_collect_strings(deid_plan))
    rx = _db_rx(db_values)
    hits = sorted({m.group(0) for m in rx.finditer(txt)})
    return {"hits": hits[:20], "n": len(hits), "ok": not hits}


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
