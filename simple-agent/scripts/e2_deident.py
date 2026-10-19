#!/usr/bin/env python3
"""E2 语料脱敏 v3（P5a.92/93/95/96 综合）。

相对 v2 的关键升级：
- 管线顺序（a95 §四.3）：**实体识别在换行折叠文本上执行**，先于一切替换；
- 白名单硬护栏（a95 §四.1 + a96 A2/条款二）：SAFE_WHITELIST/任务荷载保全名单精确不遮蔽；
  **实体匹配 > 白名单**（含白名单词的实体整体遮蔽，可击穿）；
- 准标识符类：报告编号/文书号→【DOCNO-】；项目/产品名→【PROJ-】（a95 §四.5）；
- 水印判别器（a93 §3.2）：a 仅孤立单字 / b 集合全文无连续共现 / c 跨页重复；**签署字段永不删**；
- 遮蔽预算异常检测（a95 §四.4）：代号/字符比超阈值报警；
- 覆盖域声明（a95 §四.6）。
"""
import itertools
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/root/e2-corpus/raw"
DEID = "/root/e2-corpus/deid"
LOCAL = os.path.join(ROOT, ".agent", "local")
MAP = os.path.join(LOCAL, "e2-deid-mapping.json")
MAP_V_ARCHIVE = os.path.join(LOCAL, "e2-deid-mapping.v2.json")
WHITELIST = os.path.join(ROOT, "scripts", "e2_whitelist.json")

# 遮蔽预算：代号数 / 非空白字符数 的基线上限（超即报警转人工，a95 §四.4）
BUDGET_RATIO_MAX = 0.06

PII = [
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("MOBILE", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("LANDLINE", re.compile(r"(?<!\d)0\d{2,3}-?\d{7,8}(?!\d)")),
    ("IDCARD", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("USCC", re.compile(r"(?<![0-9A-Z])[0-9A-HJ-NPQRTUWXY]{18}(?![0-9A-Z])")),
    ("BANKACCT", re.compile(r"(?<!\d)\d{16,19}(?!\d)")),
]
DOCNO = [
    re.compile(r"\d{4}\s*年\s*第\s*[A-Z]?\d+\s*号"),
    re.compile(r"(?<!\d)\d{9,}(?!\d)"),                     # 许可决定文书号等长号（USCC/银行号已先摘）
]
COMPANY = re.compile(r"(?:[^\u4e00-\u9fa5]|由|及|与|和|为|对|于|在|是)([\u4e00-\u9fa5]{2,20}?(?:有限公司|股份有限公司|集团|研究院|设计院|事务所|银行|大学|学院|中心))")
PROJ_CN = re.compile(r"(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]{2,4}?)(?=大模型)")
PROJ_EN = re.compile(r"[A-Za-z][A-Za-z0-9]*-[A-Za-z0-9-]+")
NAME_CTX = re.compile(
    r"(?:联系人|法定代表人|负责人|项目负责人|项目总部责任人|责任人|项目经理|项目总监|技术负责人|"
    r"首席技术官|CTO|技术官|编制人|审核人|批准人|签字|签名|姓名|股东|监事|董事|总经理|董事长|"
    r"经理|主任|主管|秘书|经办人|填报人|承诺人|授权代表|委托代理人|教授|博士|导师|院士|研究员|"
    r"首席科学家|科学家|总工程师)[：:\s]*([\u4e00-\u9fa5]{2,4})")
NAME_REV = re.compile(r"([\u4e00-\u9fa5]{2,4})[\s\u4e00-\u9fa5]{0,2}?(?:监事|董事|股东|总经理|董事长|CTO|首席技术官|经理|负责人)")
NAME_CELL = re.compile(r"(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]{2,3})\s{2,}\d")
NAME_GENDER = re.compile(r"(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]{2,3})[ \t　]+[男女](?![\u4e00-\u9fa5])")
EMAIL_FRAG_AT = re.compile(r"[A-Za-z0-9._%+-]{2,}@")                 # 断行邮箱局部名@
EMAIL_FRAG_ASCII = re.compile(r"[A-Za-z][A-Za-z0-9._-]{3,}")          # 性别行内的 ASCII 局部名
GENDER_ROW = re.compile(r"[ \t　][男女][ \t　]")
SURNAME = set("赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛范彭郎鲁韦昌马苗凤花方俞任袁柳唐罗薛伍余米贝姚孟高夏蔡田樊胡凌霍虞万支柯管卢莫房裘缪程邢翁储靳段富巫乌焦巴牧山谷车侯全班仰秋仲伊宫宁仇栾甘厉祖武符刘景詹龙叶幸司黎印白蒲从鄂索咸赖卓屠蒙池乔能苍双闻党翟谭贡劳姬申扶堵冉雍桑桂牛通边燕冀浦尚农温庄晏柴瞿阎连茹习宦艾容向古易慎戈廖庾居衡步都耿满弘匡国文寇广禄阙东欧沃利蔚越隆师巩聂晁勾敖融冷辛阚那简饶空曾沙养鞠须丰巢关蒯相查后荆红游竺权盖益桓徐邓萧钟雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯")
CN_STOP = set("男女码号年月日时分秒一二三四五六七八九十百千万亿元的是了在有和与及对为于项目第章节部分个件条款名单位")
SUFFIX = ("有限公司", "股份有限公司", "集团", "研究院", "设计院", "事务所", "银行", "大学", "学院", "中心")
CORE_STRIP = SUFFIX + ("科技", "技术", "信息", "网络", "智能", "实业", "发展", "生物", "医疗", "电子", "数智", "数据")
ADMIN_LEAD = re.compile(r"^(?:中国|广东省?|深圳市?|广州市?|南山区?|北京|上海|[\u4e00-\u9fa5]{1,3}[市区县省])")
LEAD_NOUN = re.compile(r"(?:主体名称|单位名称|公司名称|企业名称|名称|投标人|申请人|申报单位|采购人|供应商|甲方|乙方|本单位|该单位|本|该)")


def load_whitelist():
    w = json.load(open(WHITELIST, encoding="utf-8"))
    s = set()
    for k in ("never_mask_generic", "never_mask_admin", "never_mask_template",
              "never_mask_table", "never_mask_r3"):
        s |= set(w.get(k, []))
    return s


def _fold(text):
    """换行折叠：去掉所有空白（仅用于**实体识别**；遮蔽时按字间 \s* 回贴）。"""
    return re.sub(r"\s+", "", text)


def _nameish(s):
    return len(s) in (2, 3) and s[0] in SURNAME


TRAIL_STOP = ("等", "人", "团队", "教授", "老师", "同志", "先生", "女士", "院士", "研究员",
              "医生", "博士", "硕士", "同学", "主任", "经理", "总监", "总", "简介", "介", "牵")
BAD_END = set("于业技目牵介划项则的了在和与及")


NON_NAME = {"毕业于", "项目技", "项目牵", "本项目", "项目", "技术", "公司", "简介", "管理", "基于", "产业"}


def _name_clean(g):
    """剥离尾随非名字符（等/团队/教授/简介…），拒收普通词/坏尾，返回合格 2–3 字姓名或 None。"""
    for _ in range(2):
        for st in TRAIL_STOP:
            if g.endswith(st) and len(g) - len(st) in (2, 3):
                g = g[:-len(st)]
    if not _nameish(g):
        return None
    if g in NON_NAME or g[-1] in BAD_END:
        return None
    return g


def _clean_company(s):
    parts = LEAD_NOUN.split(s)
    s = parts[-1] if parts and parts[-1] else s
    parts = re.split(r"(?:毕业于|成立于|位于|由|及|与|和|为|对|于|在|是)", s)
    return parts[-1] if parts and parts[-1] else s


def _company_cores(name):
    x = name
    for suf in CORE_STRIP:
        if x.endswith(suf):
            x = x[:-len(suf)]
    x = ADMIN_LEAD.sub("", x)
    cores = [t for t in re.split(r"[^\u4e00-\u9fa5]+", x) if len(t) >= 2]
    # 再剥一层尾部行业词（兔展智能科技→兔展智能）
    extra = []
    for t in cores:
        for suf in ("科技", "技术", "信息", "网络", "智能", "数智"):
            if t.endswith(suf) and len(t) - len(suf) >= 2:
                extra.append(t[:-len(suf)])
    return cores + extra


def collect_entities(texts):
    """识别实体：语境/反向在**换行折叠文本**上；表格姓名格在**原文本**（空格有意义）上。"""
    folded = [_fold(t) for t in texts]
    ent = {"EMAIL": set(), "MOBILE": set(), "LANDLINE": set(), "IDCARD": set(),
           "USCC": set(), "BANKACCT": set(), "COMPANY": set(), "PERSON": set(),
           "BRAND": set(), "DOCNO": set(), "PROJ": set()}

    def add_names(g):
        nm = _name_clean(g[:4]) or _name_clean(g[:3]) or _name_clean(g[:2])
        if nm:
            ent["PERSON"].add(nm)
    # COMPANY/PROJ 在折叠文本（CJK，无数字粘连问题）；PII/DOCNO 在原文（防表格列数被拼成假长号）
    for f in folded:
        for m in COMPANY.finditer(f):
            ent["COMPANY"].add(_clean_company(m.group(1)))
        for m in PROJ_CN.finditer(f):
            ent["BRAND"].add(m.group(1))
    for t in texts:
        for kind, pat in PII:
            for m in pat.finditer(t):
                ent[kind].add(m.group(0))
        for pat in DOCNO:
            for m in pat.finditer(t):
                ent["DOCNO"].add(m.group(0))
        for m in NAME_CTX.finditer(t):
            add_names(m.group(1))
        for m in NAME_REV.finditer(t):
            add_names(m.group(1))
        for m in NAME_CELL.finditer(t):
            add_names(m.group(1))
        for m in NAME_GENDER.finditer(t):
            add_names(m.group(1))
        for m in EMAIL_FRAG_AT.finditer(t):
            ent["EMAIL"].add(m.group(0))
        for ln in t.split("\n"):
            if GENDER_ROW.search(ln):
                for m in EMAIL_FRAG_ASCII.finditer(ln):
                    ent["EMAIL"].add(m.group(0))
    # 变体闭包（已知长短名成对）：实体在文中出现 → 补其缩写（P5a.95 §四.2）
    var = json.load(open(os.path.join(ROOT, "scripts", "e2_variants.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "scripts", "e2_variants.json")) else {}
    joined = "".join(texts)                          # 变体查**原文**（含空格名）
    for full, abbr in var.get("institution_abbrev", {}).items():
        if full in joined:
            ent["COMPANY"].add(full); ent["COMPANY"].add(abbr)
    for full, abbr in var.get("product_alias", {}).items():
        if full in joined:
            ent["PROJ"].add(full); ent["PROJ"].add(abbr)
    for term in var.get("project_terms", []):
        if term in joined:
            ent["PROJ"].add(term)
    return ent


def watermarks(texts, min_count=6):
    """a93 §3.2 判别器：a 仅孤立单字 / b 集合全文无连续共现 / c 跨≥3 段重复。"""
    from collections import Counter
    cnt = Counter()
    for t in texts:
        for ln in t.split("\n"):
            s = ln.strip()
            if len(s) == 1 and re.fullmatch(r"[\u4e00-\u9fa5]", s):
                cnt[s] += 1
    cand = {c for c, n in cnt.items() if n >= min_count and c not in CN_STOP}
    joined = "".join(texts)
    for a, b in itertools.permutations(cand, 2):     # b：集合内任何相邻排列出现即非水印（真名）
        if (a + b) in joined or (b + a) in joined:
            cand.discard(a); cand.discard(b)
    return cand


SIGN_FIELD = re.compile(r"签[署字章]|盖章|法定代表人")


WATERMARK_DELETE = False   # a101 §四.5：水印清除回炉，**只登记不删除**（防字符级越界删除）


def remove_watermark(text, wm):
    """a101 §四.5：水印清除挂起——只登记（wm 写入 local/e2-watermark.json），不删除正文任何字符。"""
    return text


def _masker(mapping):
    counters = {}
    for k in mapping:
        counters[k.split("\x00", 1)[0]] = counters.get(k.split("\x00", 1)[0], 0) + 1

    def code(kind, value):
        key = f"{kind}\u0000{value}"
        if key not in mapping:
            counters[kind] = counters.get(kind, 0) + 1
            mapping[key] = f"【{kind}-{counters[kind]:03d}】"
        return mapping[key]
    return code


def mask_entity(text, value, code, kind, wl):
    if value in wl:                       # 白名单精确匹配 → 不遮蔽
        return text, False
    pat = re.compile(r"\s*".join(re.escape(ch) for ch in value))

    def _repl(m):
        seg = m.group(0)
        return code(kind, value) + "\n" * seg.count("\n")   # 保留换行数（行数守恒）
    new = pat.sub(_repl, text)
    return new, (new != text)


def deid_text(text, mapping, ent, wm, wl):
    code = _masker(mapping)
    text = remove_watermark(text, wm)
    # 长实体优先（公司 > 核心 > 人/品牌）；白名单护栏
    items = []
    for v in ent["COMPANY"]:
        items.append(("COMPANY", v))
        for core in _company_cores(v):
            items.append(("COMPANY", core))
    for k in ("PERSON", "BRAND", "PROJ", "DOCNO", "EMAIL", "MOBILE", "LANDLINE", "IDCARD", "USCC", "BANKACCT"):
        for v in ent[k]:
            items.append((k, v))
    items.sort(key=lambda x: len(x[1]), reverse=True)
    for kind, v in items:
        text, _ = mask_entity(text, v, code, kind, wl)
    # 纯正则兜底（PII 未被识别为实体时）
    for kind, pat in PII:
        text = pat.sub(lambda m: code(kind, m.group(0)), text)
    return text




# =========================================================================
# P5a.108 (c) 最小遮蔽核心：只遮【锚定实体字典 + 确定 PII + REF 块】；
# 推测层降级为「标记不遮蔽」（输出人工校正阅读清单）。
# =========================================================================
REF_HEAD = re.compile(r"^\s*(参考文献|References|Bibliography|引用文献)\s*$", re.I)
CITE_LINE = re.compile(
    r"^\s*(?:[\[(]?\d{1,3}[\])]?[\.\s]+)?"
    r"(?:[A-Z][A-Za-z.\-]+[,\s]+){2,}.*(?:19|20)\d{2}\b")
NAME_PAIR = re.compile(r"[A-Z][a-z]+[\s,]+[A-Z][a-z]+")
YEAR = re.compile(r"(?:19|20)\d{2}")
QUOTED = re.compile(r'"[^"]{8,}"')


def _is_cite(ln):
    s = ln.strip()
    if not s:
        return False
    if REF_HEAD.match(s):
        return True
    if len(NAME_PAIR.findall(s)) >= 2:
        return True
    if QUOTED.search(s) and YEAR.search(s):
        return True
    if CITE_LINE.match(s):
        return True
    if s.lower().startswith("and ") and NAME_PAIR.search(s):
        return True
    return False
REF_ALLOW = os.path.join(ROOT, ".agent", "local", "e2-refs-allowance.json")


def load_entities():
    p = os.path.join(ROOT, "scripts", "e2_entities.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def mask_ref_blocks(text, ref_chars):
    lines = text.split("\n")
    out, in_block = [], False
    for ln in lines:
        s = ln.strip()
        if REF_HEAD.match(ln):
            in_block = True
            ref_chars.update(ch for ch in ln if not ch.isspace())
            out.append("【REFS-】")
            continue
        if in_block and s == "":
            in_block = False
            out.append(ln)
            continue
        cite = _is_cite(ln)
        # 块内延续：无 CJK、非空、且不是新章节标题
        continuation = in_block and s and not re.search(r"[\u4e00-\u9fa5]", s) and len(s) < 120
        if cite or continuation:
            if not in_block and cite:
                ref_chars.update(ch for ch in ln if not ch.isspace())
                out.append("【REFS-】")
                in_block = True
            else:
                ref_chars.update(ch for ch in ln if not ch.isspace())
                out.append("")
        else:
            out.append(ln)
    return "\n".join(out)


def _entity_pattern(value):
    body = r"\s*".join(re.escape(ch) for ch in value)
    return re.compile(body, re.IGNORECASE if re.search(r"[A-Za-z]", value) else 0)


def mask_anchor(text, code, entities, wl, variants):
    vals = []
    for kind, arr in entities.items():
        for v in arr:
            if len(v) >= 2 and v not in wl:
                vals.append((kind, v))
    for full, abbr in variants.get("institution_abbrev", {}).items():
        vals += [("COMPANY", full), ("COMPANY", abbr)]
    for full, abbr in variants.get("product_alias", {}).items():
        vals += [("PROJ", full), ("PROJ", abbr)]
    vals.sort(key=lambda x: len(x[1]), reverse=True)
    for kind, v in vals:
        if v in wl:
            continue

        def _repl(m, _k=kind, _v=v):
            return code(_k, _v) + "\n" * m.group(0).count("\n")
        text = _entity_pattern(v).sub(_repl, text)
    return text


def core_deid(text, code, entities, wl, variants, ref_chars):
    text = mask_ref_blocks(text, ref_chars)
    text = mask_anchor(text, code, entities, wl, variants)
    for kind, pat in PII:
        text = pat.sub(lambda m: code(kind, m.group(0)), text)
    return text


def speculative_markers(texts, entities, wl):
    ent = collect_entities(texts)
    anchor = set()
    for arr in entities.values():
        anchor |= set(arr)
    markers, seen = [], set()
    for kind, arr in ent.items():
        for v in arr:
            if len(v) < 2 or v in wl or v in anchor:
                continue
            k = (kind, v)
            if k not in seen:
                seen.add(k); markers.append({"kind": kind, "candidate": v})
    # 碎片类（域尾 / 孤立数字段）——推测层标记，供人工校正
    FRAG_DOMAIN = re.compile(r"[A-Za-z0-9-]+\.(?:com|cn|net|org)\b", re.I)
    FRAG_DIGITS = re.compile(r"(?<!\d)\d{5,8}(?!\d)")
    for t in texts:
        for m in FRAG_DOMAIN.finditer(t):
            k = ("FRAGMENT", m.group(0))
            if k not in seen:
                seen.add(k); markers.append({"kind": "FRAGMENT", "candidate": m.group(0)})
        for ln in t.split("\n"):
            if GENDER_ROW.search(ln):
                for m in FRAG_DIGITS.finditer(ln):
                    k = ("FRAGMENT", m.group(0))
                    if k not in seen:
                        seen.add(k); markers.append({"kind": "FRAGMENT", "candidate": m.group(0)})
    return markers


def main():
    wl = load_whitelist()
    entities = load_entities()
    variants = json.load(open(os.path.join(ROOT, "scripts", "e2_variants.json"), encoding="utf-8"))
    os.makedirs(DEID, exist_ok=True); os.makedirs(LOCAL, exist_ok=True)
    files = sorted(f for f in os.listdir(RAW) if f.endswith(".txt"))
    raws = {fn: open(os.path.join(RAW, fn), encoding="utf-8", errors="replace").read() for fn in files}
    mapping, ref_chars = {}, set()
    for fn in files:
        code = _masker(mapping)
        out = core_deid(raws[fn], code, entities, wl, variants, ref_chars)
        open(os.path.join(DEID, fn), "w", encoding="utf-8").write(out)
    json.dump(mapping, open(MAP, "w"), ensure_ascii=False, indent=1)
    json.dump(sorted(ref_chars), open(REF_ALLOW, "w"), ensure_ascii=False, indent=1)
    json.dump({"watermark_chars": []}, open(os.path.join(LOCAL, "e2-watermark.json"), "w"), ensure_ascii=False, indent=1)
    markers = speculative_markers(list(raws.values()), entities, wl)
    json.dump({"note": "推测层标记清单（不遮蔽；人工校正落成字典条目，a108 §三.1）",
               "n": len(markers), "markers": markers},
              open(os.path.join(LOCAL, "e2-review-markers.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"mode": "(c) minimal-core", "files": len(files),
                      "entities": {k: len(v) for k, v in entities.items()},
                      "mapping_entries": len(mapping), "ref_chars": len(ref_chars),
                      "markers": len(markers)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
