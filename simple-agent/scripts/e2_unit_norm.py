#!/usr/bin/env python3
"""E2 评测器设施之一：单位归一表 + 数值归一（a85 §三/§七.2）。

确定性、零 token。把中/英/符号金额写法归一到「分」（int），供数字一致性检查。
单位归一表是金标准管线最可能的藏虫处 → 缺陷注入夹具重点照顾（a85 §三）。
"""
import re

# 单位倍率（相对"元"）
UNIT = {
    "元": 1, "圆": 1, "块": 1, "￥": 1, "¥": 1, "rmb": 1, "人民币": 1, "cny": 1,
    "万元": 10_000, "万": 10_000, "w": 10_000, "万圆": 10_000,
    "亿元": 100_000_000, "亿": 100_000_000,
    "千元": 1_000, "k": 1_000, "千": 1_000,
    "角": 0.1, "分": 0.01,
}
_CN_DIGIT = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
             "六": 6, "七": 7, "八": 8, "九": 9,
             "壹": 1, "贰": 2, "叁": 3, "肆": 4, "伍": 5,
             "陆": 6, "柒": 7, "捌": 8, "玖": 9}
_CN_UNIT = {"十": 10, "百": 100, "千": 1000, "拾": 10, "佰": 100, "仟": 1000}


def cn_to_int(s: str):
    """中文数字（壹佰贰拾万 风格也覆盖常用简体）→ int；不支持则 None。"""
    s = s.strip()
    if not s:
        return None
    # 阿拉伯优先
    if re.fullmatch(r"\d+", s):
        return int(s)
    total, section, number = 0, 0, 0
    for ch in s:
        if ch in _CN_DIGIT:
            number = _CN_DIGIT[ch]
        elif ch in _CN_UNIT:
            section += (number or 1) * _CN_UNIT[ch]
            number = 0
        elif ch == "万":
            total = (total + section + number) * 10_000
            section = number = 0
        elif ch == "亿":
            total = (total + section + number) * 100_000_000
            section = number = 0
        else:
            return None
    return total + section + number


def to_cents(text: str):
    """把金额写法归一为「分」(int)。无法解析 → None。"""
    if text is None:
        return None
    s = str(text).strip()
    s = s.replace(",", "").replace("，", "").replace(" ", "")
    s = s.replace("（", "(").replace("）", ")")
    # 全角数字 → 半角
    s = "".join(chr(ord(c) - 0xFEE0) if "０" <= c <= "９" else c for c in s)
    m = re.search(r"([0-9]+(?:\.[0-9]+)?|[零一二两三四五六七八九十百千万亿壹贰叁肆伍陆柒捌玖拾佰仟]+)\s*([a-zA-Z元圆块￥¥角分千 wWkK万亿]*|人民币|万|亿)?", s)
    if not m:
        return None
    num_raw, unit = m.group(1), (m.group(2) or "").lower()
    num = float(num_raw) if re.fullmatch(r"[0-9.]+", num_raw) else cn_to_int(num_raw)
    if num is None:
        return None
    # 归一单位：处理含"万/亿"与"元/角/分"的组合
    mult = 1
    for key in sorted(UNIT, key=len, reverse=True):
        if key and key in unit:
            mult = UNIT[key]
            break
    return int(round(num * mult * 100))


def extract_amounts(text: str):
    """抽取文本中所有金额（分），返回 [(raw, cents)]。
    覆盖两种形态：① 前缀货币（¥1,000,000）② 后缀单位（100 万元 / 210 元）。"""
    out = []
    pat = re.compile(
        r"(?:[￥¥]\s*[0-9][0-9,，]*(?:\.[0-9]+)?)"                 # 前缀货币
        r"|(?:[0-9][0-9,，]*(?:\.[0-9]+)?\s*(?:万元|亿元|千元|万|亿|千|元|圆|块|角|分))")  # 后缀单位
    for m in pat.finditer(text):
        c = to_cents(m.group(0))
        if c is not None:
            out.append((m.group(0).strip(), c))
    return out
