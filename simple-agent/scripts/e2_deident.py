#!/usr/bin/env python3
"""P5a.86/92：E2 语料脱敏 v2（修复 DC-10 召回失效）。

v1 缺陷：只按少量"标签+姓名"上下文匹配，漏三类（a92 §2.2）：
  ① 水印散布单字（跨页孤立单字）；② 语境位/反向人名（股东/监事/CTO…）；③ 公司短名与半遮蔽。
v2 三对策（a92 §4.1）：
  a 语境触发器扩表 + **反向语境**（名在职务词之前）；
  b 公司全称入表后其**核心字号**并入映射，全局遮蔽（禁半遮蔽/跨行残前缀）；
  c **水印带清除**（同字集跨页孤立高频 → 整带清除，行数守恒）。

  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_deident.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/root/e2-corpus/raw"
DEID = "/root/e2-corpus/deid"
MAP = os.path.join(ROOT, ".agent", "local", "e2-deid-mapping.json")
MAP_V1_ARCHIVE = os.path.join(ROOT, ".agent", "local", "e2-deid-mapping.v1.json")

PATTERNS = [
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("MOBILE", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("LANDLINE", re.compile(r"(?<!\d)0\d{2,3}-\d{7,8}(?!\d)")),
    ("IDCARD", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("USCC", re.compile(r"(?<![0-9A-Z])[0-9A-HJ-NPQRTUWXY]{18}(?![0-9A-Z])")),
    ("BANKACCT", re.compile(r"(?<!\d)\d{16,19}(?!\d)")),
    ("COMPANY", re.compile(r"(?:[^\u4e00-\u9fa5]|由|及|与|和|为|对|于|在|是)([\u4e00-\u9fa5]{2,20}?(?:有限公司|股份有限公司|集团|研究院|设计院|事务所|银行|大学|学院|中心))")),
]
# a 语境触发器（前向）
NAME_CTX = re.compile(
    r"(?:联系人|法定代表人|负责人|项目负责人|项目总部责任人|责任人|项目经理|项目总监|技术负责人|"
    r"首席技术官|CTO|技术官|编制人|审核人|批准人|签字|签名|姓名|股东|监事|董事|成员|总经理|"
    r"董事长|经理|主任|主管|秘书|经办人|填报人|承诺人|授权代表|委托代理人|教授|博士)[：:\s]*"
    r"([\u4e00-\u9fa5]{2,4})")
# 反向语境（名在职务词之前，容忍中间水印/空格 ≤2 字）
NAME_CTX_REV = re.compile(
    r"([\u4e00-\u9fa5]{2,4})[\s\u4e00-\u9fa5]{0,2}?(?:监事|董事|股东|总经理|董事长|CTO|首席技术官|经理|负责人)")
# 表格姓名格（姓名 + 空格 + 数字，如 股东表 "姜美娟   35"）
NAME_CELL = re.compile(r"(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]{2,3})\s{2,}\d")
_SURNAME = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳唐罗薛伍余米贝姚孟高夏蔡田樊胡凌霍虞万支柯昝管卢莫房裘缪干解应宗丁宣邓郁单杭洪包诸左石崔吉龚程邢滑裴陆荣翁荀羊甄封芮储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍郤璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴瞿阎连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公]"


def _is_nameish(s):
    return len(s) in (2, 3) and s[0] in _SURNAME


def _mk_mapper(mapping):
    counters = {}
    for k in mapping:
        counters[k.split("\x00", 1)[0]] = counters.get(k.split("\x00", 1)[0], 0) + 1

    def repl(kind, value):
        key = f"{kind}\u0000{value}"
        if key not in mapping:
            counters[kind] = counters.get(kind, 0) + 1
            mapping[key] = f"【{kind}-{counters[kind]:03d}】"
        return mapping[key]
    return repl


def collect_names(texts):
    names = set()
    for t in texts:
        for m in NAME_CTX.finditer(t):
            if _is_nameish(m.group(1)):
                names.add(m.group(1))
        for m in NAME_CTX_REV.finditer(t):
            if _is_nameish(m.group(1)):
                names.add(m.group(1))
        for m in NAME_CELL.finditer(t):
            if _is_nameish(m.group(1)):
                names.add(m.group(1))
    return names


def _suffixes():
    return ("有限公司", "股份有限公司", "集团", "研究院", "设计院", "事务所", "银行", "大学", "学院", "中心")


def company_cores(companies):
    """全称 → 核心字号（剥行政区划前缀 + 行业后缀）。"""
    cores = set()
    for c in companies:
        x = c
        for suf in _suffixes():
            if x.endswith(suf):
                x = x[:-len(suf)]
        x = re.sub(r"^(?:中国|广东省?|深圳市?|广州市?|南山区?|北京|上海|[\u4e00-\u9fa5]{1,3}[市区县省])", "", x)
        for token in re.split(r"[^\u4e00-\u9fa5]+", x):
            if len(token) >= 2:
                cores.add(token)
        # 前缀片段（防跨行残前缀，如"深圳兔"）
        for n in (3, 4):
            if len(c) >= n:
                cores.add(c[:n])
    return {c for c in cores if len(c) >= 2}


def company_anchors(companies):
    """锚字取自**去行政区划+行业后缀后的核心 token 首字**（如 兔展智能→兔），避免用前缀碎片（深圳兔→深）。"""
    anchors = set()
    for c in companies:
        x = c
        for suf in _suffixes():
            if x.endswith(suf):
                x = x[:-len(suf)]
        x = re.sub(r"^(?:中国|广东省?|深圳市?|广州市?|南山区?|北京|上海|[\u4e00-\u9fa5]{1,3}[市区县省])", "", x)
        for token in re.split(r"[^\u4e00-\u9fa5]+", x):
            if len(token) >= 2:
                anchors.add(token[0])
    return anchors


def brand_words(texts):
    """品牌/产品名：CJK 2-4 字 + 产品类词（大模型/模型/平台/系统/引擎/App）。"""
    brands = set()
    pat = re.compile(r"(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]{2,4}?)(?=大模型|模型|平台|系统|引擎|App)")
    for t in texts:
        for m in pat.finditer(t):
            brands.add(m.group(1))
    return {b for b in brands if len(b) >= 2}


def brand_anchors(cores):
    """核心字号首字作锚（如 兔展智能→兔），兜底产品品牌（兔灵）。"""
    return {c[0] for c in cores if len(c) >= 2}


def detect_watermark(texts, min_count=6, max_set=8):
    """散布水印：孤立单字跨页高频现 → 判定为水印字集。排除常用字（男/码/号/年月日/数字…）。"""
    from collections import Counter
    STOP = set("男女码号年月日时分秒一二三四五六七八九十百千万亿元的是了在有和与及对为于项目第章节部分个件条款名单位")
    cnt = Counter()
    for t in texts:
        for ln in t.splitlines():
            s = ln.strip()
            if len(s) == 1 and re.fullmatch(r"[\u4e00-\u9fa5]", s):
                cnt[s] += 1
            for m in re.finditer(r"(?<=\s)([\u4e00-\u9fa5])(?=\s{2,})", ln):
                cnt[m.group(1)] += 1
    cand = {c for c, n in cnt.items() if n >= min_count and c not in STOP}
    if len(cand) > max_set:
        cand = {c for c, _ in cnt.most_common(max_set) if c not in STOP}
    return cand


def remove_watermark(text, wm):
    """整带清除水印字（行数守恒）：整行仅含水印字→清空；行内孤立水印字→抹除。"""
    if not wm:
        return text
    wmset = "".join(re.escape(c) for c in wm)
    out = []
    for ln in text.split("\n"):
        core = re.sub(r"\s", "", ln)
        if core and len(core) <= 6 and all(ch in wm for ch in core):
            out.append("")
            continue
        ln = re.sub(r"(?<=\s)([%s])(?=\s|$)" % wmset, "", ln)
        out.append(ln)
    return "\n".join(out)


def _clean_company(s):
    """剥离前导连接/动词（本项目由/毕业于/由/及…），取真正公司名。"""
    parts = re.split(r"(?:毕业于|成立于|位于|由|及|与|和|为|对|于|在|是)", s)
    return parts[-1] if parts and parts[-1] else s


def deid_text(text, mapping, names, cores, wm, brands=None, anchors=None):
    repl = _mk_mapper(mapping)
    for kind, pat in PATTERNS:
        if kind == "COMPANY":                      # 只替换组(1)的公司名部分（保留边界+前导词）
            def _sub(m):
                g1 = m.group(1); clean = _clean_company(g1)
                lead = g1[:len(g1) - len(clean)]
                return m.group(0)[:m.start(1) - m.start(0)] + lead + repl(kind, clean)
            text = pat.sub(_sub, text)
        else:
            text = pat.sub(lambda m: repl(kind, m.group(0)), text)
    text = remove_watermark(text, wm)
    for nm in sorted(names, key=len, reverse=True):
        if nm in text:
            text = text.replace(nm, repl("PERSON", nm))
    for c in sorted(cores, key=len, reverse=True):
        if c in text:
            text = text.replace(c, repl("COMPANY", c))
    for b in sorted(brands or set(), key=len, reverse=True):
        if b in text:
            text = text.replace(b, repl("BRAND", b))
    return text


def main():
    os.makedirs(DEID, exist_ok=True)
    os.makedirs(os.path.dirname(MAP), exist_ok=True)
    if os.path.exists(MAP):                       # v1 存档
        import shutil, hashlib
        shutil.copy(MAP, MAP_V1_ARCHIVE)
        print("archived mapping v1 ->", MAP_V1_ARCHIVE,
              "sha16=", hashlib.sha256(open(MAP_V1_ARCHIVE, "rb").read()).hexdigest()[:16])
    files = sorted(f for f in os.listdir(RAW) if f.endswith(".txt"))
    raws = {fn: open(os.path.join(RAW, fn), encoding="utf-8", errors="replace").read() for fn in files}
    texts = list(raws.values())
    names = collect_names(texts)
    companies = set()
    for t in texts:
        for m in PATTERNS[6][1].finditer(t):
            companies.add(_clean_company(m.group(1)))
    cores = company_cores(companies)
    brands = brand_words(texts)
    anchors = company_anchors(companies)
    wm = detect_watermark(texts)
    mapping = {}
    for fn in files:
        open(os.path.join(DEID, fn), "w", encoding="utf-8").write(
            deid_text(raws[fn], mapping, names, cores, wm, brands, anchors))
    json.dump(mapping, open(MAP, "w"), ensure_ascii=False, indent=1)
    json.dump({"watermark_chars": sorted(wm)}, open(os.path.join(ROOT, ".agent", "local", "e2-watermark.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"files": len(files), "names": len(names), "company_cores": len(cores),
                      "watermark_chars": sorted(wm), "mapping_entries": len(mapping)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
