# P5a.97 §二 回执完备性附件（DC-10 二级）

## 一、复检包规格整改（a97 §一.2）
- 上轮漏 **P2-02**（a95 三失败件之一）。**本轮已补齐**：复检包 = P2-04 + P3-02 + **P2-02** + 随机 P2-01（seed96 核准）。
- 包：`.agent/local/A3-deid-recheck-3.md`；P2-02 关键残留实测：徐康/姜美娟/周星 = 0。

## 二、逐点机制分析报告（a95 §三，禁止打地鼠）

| 实例 | 为什么漏/遮 | 修法 |
|---|---|---|
| 徐康 ×12 | v2 姓氏表缺 `徐`；语境名在折叠文本上贪心取 4 字被长度过滤丢弃 | 补全姓氏表；语境名改在**原文**（行分隔）取；表格姓名格；尾随停用字剥离；实体全局替换 |
| `公司`→【PERSON-002】×39（过遮） | v2 把公司名 `c[:3]/c[:4]` 前缀碎片当字号并入（含通用词） | 删除前缀碎片法；**白名单硬护栏**（精确不遮）+ 实体匹配可击穿；换行折叠下用 `\s*` 回贴跨行实体 |
| 胶合水印 `婷总经理`/`学6.` | v2 只清“整行孤立单字”，胶合形态逃逸 | v3 对**确认水印字**清除其全部出现（含胶合），签署字段行豁免 |
| 断行逃逸 `兔展智⏎能` | 正则逐行匹配，换行切断标识符 | 实体识别在**换行折叠文本**上；遮蔽用 `\s*` 连接并**保留换行数** |
| 北大（短名） | 无长短名变体映射 | `e2_variants.json` 变体闭包（北京大学→北大） |
| 袁粒 ×8 | `导师袁粒等` 贪心取 4 字被长度过滤；`首席科学家袁粒` 无该语境 | 尾随停用字剥离（等/团队/教授…）+ 补 `导师/首席科学家/科学家` 语境 |
| 兔展智能 | 公司核心只剥 `有限公司`，残留 `科技` | 扩展 `CORE_STRIP`（科技/技术/信息/…）+ 二次行业词剥离 |

## 三、探针覆盖域声明（a96 A3 / a95 §四.6）
- 闭包探针：`闭包残留 0（量程：已入表实体之变体；未入表实体不在本探针量程，由 fixture 与人工锚覆盖）`
- 召回探针：`召回残留 0（量程：PII 正则 + 公司全称/核心 + 姓氏表格格 + 长号；未含特征者由人工锚覆盖）`

## 四、代码全文入档（a96 A4）

### 4.1 白名单硬护栏 / 遮蔽（`scripts/e2_deident.py`）
```python
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

def _name_clean(g):
    """剥离尾随非名字符（等/团队/教授…），返回合格 2–3 字姓名或 None。"""
    for _ in range(2):
        for st in TRAIL_STOP:
            if g.endswith(st) and len(g) - len(st) in (2, 3):
                g = g[:-len(st)]
    return g if _nameish(g) else None

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
    # COMPANY/PII/DOCNO/PROJ 在折叠文本；NAME 在原文（行/空分隔，避免跨行吞字）
    for f in folded:
        for kind, pat in PII:
            for m in pat.finditer(f):
                ent[kind].add(m.group(0))
        for pat in DOCNO:
            for m in pat.finditer(f):
                ent["DOCNO"].add(m.group(0))
        for m in COMPANY.finditer(f):
            ent["COMPANY"].add(_clean_company(m.group(1)))
        for m in PROJ_CN.finditer(f):
            ent["BRAND"].add(m.group(1))
        # PROJ：仅词典（揭榜方项目/产品名），不用全局连字符正则（避免遮通用技术词，a95 §四.5/§二.4）
    for t in texts:
        for m in NAME_CTX.finditer(t):
            add_names(m.group(1))
        for m in NAME_REV.finditer(t):
            add_names(m.group(1))
        for m in NAME_CELL.finditer(t):
            add_names(m.group(1))
    # 变体闭包（已知长短名成对）：实体在文中出现 → 补其缩写（P5a.95 §四.2）
    var = json.load(open(os.path.join(ROOT, "scripts", "e2_variants.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "scripts", "e2_variants.json")) else {}
    joined = "".join(texts)                          # 变体查**原文**（含空格名）
    for full, abbr in var.get("institution_abbrev", {}).items():
        if full in joined:
            ent["COMPANY"].add(full); ent["COMPANY"].add(abbr)
    for full, abbr in var.get("product_alias", {}).items():
        if full in joined:
            ent["PROJ"].add(full); ent["PROJ"].add(abbr)
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

def remove_watermark(text, wm):
    """清除水印字（含胶合，a95 §二.3）；**签署字段行永不删**（a93 §3.2 铁律）。行数守恒。"""
    if not wm:
        return text
    out = []
    for ln in text.split("\n"):
        if SIGN_FIELD.search(ln):
            out.append(ln); continue
        out.append("".join(ch for ch in ln if ch not in wm))
    return "\n".join(out)

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

```

### 4.2 变体闭包探针（`scripts/e2_deid_closure_probe.py` 全文）
```python
#!/usr/bin/env python3
"""E2 变体闭包探针（P5a.96 条款三）：扫已入表实体的变体残留。

量程声明（必含，a96 A3）：**本探针只管"已入表实体的变体残留"；未入表实体的发现不在本量程，
由召回 fixture + 人工锚覆盖。** 变体仅从映射表实体生成（禁全局形近扫描）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_deid_closure_probe.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import e2_deident as D  # noqa: E402

DEID = "/root/e2-corpus/deid"
MAP = os.path.join(ROOT, ".agent", "local", "e2-deid-mapping.json")
R = os.path.join(ROOT, ".agent", "reports")


def variants(value, kind):
    v = set()
    v.add(value)
    v.add(re.sub(r"\s+", "", value))                       # 断行折叠
    if kind == "COMPANY":
        for c in D._company_cores(value):
            v.add(c)
    return {x for x in v if len(x) >= 2}


def main():
    if not os.path.exists(MAP):
        print(json.dumps({"error": "no mapping"})); return 2
    m = json.load(open(MAP, encoding="utf-8"))
    entities = [(k.split("\x00", 1)[0], k.split("\x00", 1)[1]) for k in m]
    deid = {}
    for fn in os.listdir(DEID):
        if fn.endswith(".txt") and fn != "STATUS":
            deid[fn] = open(os.path.join(DEID, fn), encoding="utf-8", errors="replace").read()
    residual = []
    for kind, val in entities:
        for var in variants(val, kind):
            if var == "unknown":
                continue
            for fn, t in deid.items():
                if var in t:
                    residual.append({"entity": val, "kind": kind, "variant": var, "file": fn})
                    break
    out = {"note": "E2 变体闭包探针（a96 条款三）",
           "entities": len(entities), "residual": residual[:50], "residual_count": len(residual),
           "closure_clean": not residual,
           "coverage_declaration": "闭包残留 {}（量程：已入表实体之变体；未入表实体不在本探针量程，"
                                   "由 fixture 与人工锚覆盖）".format(len(residual))}
    json.dump(out, open(os.path.join(R, "e2-deid-closure-probe.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"entities": len(entities), "residual_count": len(residual),
                      "closure_clean": out["closure_clean"], "sample": residual[:15]},
                     ensure_ascii=False, indent=1))
    return 0 if out["closure_clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
```

## 五、映射表版本
- 现行 **mapping v3** sha16=`6e647b2c6cdf3cc9`
- 上版 **v2 作废**（存档 `e2-deid-mapping.v2.json` sha16=`229f86d24775f06c`）

## 六、指纹双向绑定确认
- canon = `eed2a0cb8f0f9e01`
- `taskbook_fingerprint.json` = `{"ruleset_sha": "75b4224f3791cf2a", "unit_table_sha": "8d39d7b49cffaaa6", "eval_params_sha": "a7ae953e70a1547c", "prompt_sha": "32c79f5e972a6cbd", "whitelist_sha": "667ae8893778844e", "variants_sha": "4314b159b8f2b89a", "eval_version": "v0.4（a96 A1 签署拆分）", "prompt_version": "v1.1"}`
- `e2_eval_params.json` ruleset_version = `v0.4（a96 A1 签署拆分）`；任务书须内嵌 canon，`e2_fingerprint.verify()` 校验一致。
- 脚手架自证 4/4（正例/缺文件/哈希不符/任务书内嵌错值）。

## 七、a98/a99 认知
- **a98**：E2 仍为标书域；公开法律数据集 → 夹具池（tier=fixture），**永不入基线**；法律域 epoch-2+ 候选。
- **a99**：病院夹具科——**按用户指示本轮暂不处理**。
