#!/usr/bin/env python3
"""E2 评测器框架（a85 §四 纯确定性）：规则集 schema + 确定性判定。

支持三类检查（对应任务三型）：
  - required_sections: 必备章节（子串/正则）；缺失 → fail
  - dimensions: 维度合规（规则化）—— require 集合出现 ∧ forbid 集合出现 → fail
  - number_fields: 数字一致性——同一字段标签下抽取的所有金额须相等，否则 fail

规则集 **内容** 由裁者随任务书预注册冻结（本文件只是**框架**，a85 §七.2）。
"""
import re

from e2_unit_norm import extract_amounts, to_cents


def check(doc_text: str, ruleset: dict) -> dict:
    """返回 {pass: bool, failures: [ {type, detail} ]}。确定性。"""
    failures = []
    # 1) 必备章节
    for sec in ruleset.get("required_sections", []):
        if not re.search(sec, doc_text):
            failures.append({"type": "missing_section", "detail": sec})
    # 2) 维度合规（规则化集合逻辑：A 出现 ∧ B 出现 → 矛盾）
    for dim in ruleset.get("dimensions", []):
        a_hit = any(re.search(p, doc_text) for p in dim.get("require", []))
        b_hit = any(re.search(p, doc_text) for p in dim.get("forbid", []))
        if a_hit and b_hit:
            failures.append({"type": "dimension_conflict", "detail": dim.get("name", "?")})
    # 3) 数字一致性：同字段多次出现须一致
    for label in ruleset.get("number_fields", []):
        vals = set()
        for line in doc_text.splitlines():
            if label in line:
                for _, cents in extract_amounts(line):
                    vals.add(cents)
        if len(vals) > 1:
            failures.append({"type": "number_inconsistent", "detail": f"{label}:{sorted(vals)}"})
    return {"pass": not failures, "failures": failures}


def load_ruleset(path: str) -> dict:
    import json
    return json.load(open(path, encoding="utf-8"))


# =========================================================================
# P5a.91 §四：规则集 v0.3 全量引擎（R1 模板 / R2.1 表内勾稽 / R2.2 跨文档 / R3 集合逻辑）
# 证据形式=原文片段(quote≤50)+章节路径（a91 §一：不用行号，工具无关）
# =========================================================================
import re as _re

_DATE = _re.compile(r"(\d{4})\s*[-年/]\s*(\d{1,2})\s*[-月/]\s*(\d{1,2})")
_HEAD = _re.compile(r"^\s*(?:第[一二三四五六七八九十]+[章节]|[一二三四五六七八九十]+、|\d+(?:\.\d+)*\s+\S|[（(][一二三四五六七八九十]+[)）])")


def _chapter(text, idx):
    head = ""
    for ln in text[:idx].splitlines():
        if _HEAD.match(ln):
            head = ln.strip()
    return head


def _evidence(text, phrase):
    i = text.find(phrase)
    if i < 0:
        return {"quote": "", "chapter": ""}
    return {"quote": text[i:i + 40].replace("\n", " ")[:40], "chapter": _chapter(text, i)}


def _dates(text):
    out = []
    for m in _DATE.finditer(text):
        out.append((m.group(0), int(m.group(1)), int(m.group(2)), int(m.group(3))))
    return out


def _num_or_none(line, unit_mult):
    sub = extract_amounts(line)
    if sub:
        return sub[0][1]
    nums = _re.findall(r"\d[\d,]*(?:\.\d+)?", line)
    if nums and unit_mult:
        return int(round(float(nums[0].replace(",", "")) * unit_mult * 100))
    return None


def _label_amount(text, label, unit_mult=1):
    for ln in text.splitlines():
        if label in ln:
            v = _num_or_none(ln, unit_mult)
            if v is not None:
                return v
    return None


def _label_str(text, label):
    for ln in text.splitlines():
        if label in ln:
            rest = ln.split(label, 1)[1].lstrip("：: 　")
            toks = rest.split()
            if toks:
                return toks[0]
    return None


def _mk(rid, verdict, evidence=None, detail=""):
    return {"id": rid, "verdict": verdict, "evidence": evidence or {}, "detail": detail}


def evaluate(docs: dict, task_input: dict, ruleset: dict):
    """docs: {模板名: 文本}；task_input: 结构化参数 dict（阈值/单位），评测器**不解析自然语言段落**（a91 §三.1）。"""
    unit = int(task_input.get("unit_mult_yuan", 1) or 1)
    out = []
    for r in ruleset.get("rules", []):
        k = r["kind"]
        rid = r["id"]
        if k == "structural":
            t = docs.get(r["doc"], "")
            if not t:
                out.append(_mk(rid, "NA", detail="missing_doc"))
                continue
            miss = [s for s in r["required"] if s not in t]
            out.append(_mk(rid, "FAIL", detail=f"missing:{miss}", evidence=_evidence(t, miss[0])) if miss
                       else _mk(rid, "PASS", evidence=_evidence(t, r["required"][0])))
        elif k == "structural_any":
            t = docs.get(r.get("doc", ""), "".join(docs.values()))
            if not t:
                out.append(_mk(rid, "NA", detail="missing_doc")); continue
            hit = any(s in t for s in r["required_any"])
            out.append(_mk(rid, "PASS" if hit else "FAIL",
                           detail="" if hit else "none_of:" + ",".join(r["required_any"])))
        elif k == "structural_template":
            t = docs.get(r["doc"], "")
            if not t:
                out.append(_mk(rid, "NA", detail="missing_doc")); continue
            req = r["default"]
            for key, v in r.get("variants", {}).items():
                if key in t:
                    req = v; break
            miss = [s for s in req if s not in t]
            out.append(_mk(rid, "FAIL", detail=f"missing:{miss}") if miss else _mk(rid, "PASS"))
        elif k == "table_equations":
            t = docs.get(r["doc"], "")
            if not t:
                out.append(_mk(rid, "NA", detail="missing_doc")); continue
            verdict, det = "PASS", []
            for eq in r["equations"]:
                lhs = _label_amount(t, eq["lhs"], unit)
                if lhs is None:
                    verdict = "NA" if verdict != "FAIL" else verdict; det.append(f"{eq['lhs']}?NA"); continue
                if "rhs_sum" in eq:
                    parts = [_label_amount(t, x, unit) for x in eq["rhs_sum"]]
                    if any(p is None for p in parts):
                        verdict = "NA" if verdict != "FAIL" else verdict; det.append(f"{eq['lhs']}:rhs?NA"); continue
                    ok = lhs == sum(parts)
                else:
                    rhs = _label_amount(t, eq["rhs"], unit)
                    if rhs is None:
                        verdict = "NA" if verdict != "FAIL" else verdict; continue
                    ok = (lhs == rhs) if eq["op"] == "eq" else (lhs >= rhs) if eq["op"] == "ge" else True
                if not ok:
                    verdict = "FAIL"; det.append(f"{eq['lhs']} fail")
            out.append(_mk(rid, verdict, detail=";".join(det)))
        elif k == "cross_doc_equal":
            if any(d not in docs or not docs[d] for d in r["docs"]):
                out.append(_mk(rid, "NA", detail="doc_or_version_undecidable")); continue
            vals = []
            for d in r["docs"]:
                v = _label_amount(docs[d], r["label"], unit)
                if v is None:
                    v = _label_str(docs[d], r["label"])
                vals.append(v)
            if any(v is None for v in vals):
                out.append(_mk(rid, "NA", detail="label_missing")); continue
            out.append(_mk(rid, "PASS" if len(set(map(str, vals))) == 1 else "FAIL",
                           detail=f"values={vals}"))
        elif k == "implication_count_zero":
            t = docs.get(r["if_doc"], "")
            if not t or r["if_phrase"] not in t:
                out.append(_mk(rid, "NA", detail="antecedent_absent")); continue
            tt = docs.get(r["then_doc"], "")
            if not tt:
                out.append(_mk(rid, "NA", detail="then_doc_missing")); continue
            cnt = _label_amount(tt, r["then_label"], 1)
            nonzero = False
            for ln in tt.splitlines():
                if r["then_label"] in ln and _re.search(r"[1-9]\d*\s*条", ln):
                    nonzero = True
            out.append(_mk(rid, "FAIL" if (nonzero or (cnt or 0) > 0) else "PASS"))
        elif k == "always_na":
            out.append(_mk(rid, "NA", detail=r.get("note", "")))
        elif k == "date_before":
            alld = "\n".join(docs.values())
            da = _dates(alld)
            a = next((x for x in da if r["a"] in _chapter(alld, alld.find(x[0])) or r["a"] in alld), None)
            # 用标签邻近日期
            a = _labeled_date(alld, r["a"]) or (da[0] if da else None)
            b = _labeled_date(alld, r["b"])
            if not a or not b:
                out.append(_mk(rid, "NA", detail="date_missing")); continue
            out.append(_mk(rid, "PASS" if a[1:] < b[1:] else "FAIL", detail=f"{a[0]}<{b[0]}?"))
        elif k == "range_contains":
            alld = "\n".join(docs.values())
            span = _labeled_dates(alld, r["outer"])
            inner = _labeled_dates(alld, r["inner"])
            if len(span) < 2 or not inner:
                out.append(_mk(rid, "NA", detail="range_or_inner_missing")); continue
            lo, hi = span[0][1:], span[-1][1:]
            ok = all(lo <= d[1:] <= hi for d in inner)
            out.append(_mk(rid, "PASS" if ok else "FAIL"))
        elif k == "param_threshold_date":
            if r["param"] not in task_input:
                out.append(_mk(rid, "NA", detail="param_absent_in_task_input")); continue
            months = int(task_input[r["param"]])
            alld = "\n".join(docs.values())
            a = _labeled_date(alld, r["a"]); b = _labeled_date(alld, r["b"])
            if not a or not b:
                out.append(_mk(rid, "NA", detail="date_missing")); continue
            y, m, d = a[1], a[2] + months, a[3]
            y += (m - 1) // 12; m = (m - 1) % 12 + 1
            out.append(_mk(rid, "PASS" if (y, m, d) >= b[1:] else "FAIL"))
        else:
            out.append(_mk(rid, "NA", detail=f"unknown_kind:{k}"))
    counts = {}
    for x in out:
        counts[x["verdict"]] = counts.get(x["verdict"], 0) + 1
    return {"rules": out, "counts": counts}


def _labeled_date(text, label):
    for ln in text.splitlines():
        if label in ln:
            ds = _dates(ln)
            if ds:
                return ds[0]
    return None


def _labeled_dates(text, label):
    for ln in text.splitlines():
        if label in ln:
            ds = _dates(ln)
            if ds:
                return ds
    return []


def eval_fingerprint() -> str:
    """P5a.87 §四.2：评测器仪器参数指纹（抽取模式/单位表/规则集版本）——须并入 env_fingerprint。"""
    import hashlib
    import json
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e2_eval_params.json")
    try:
        data = open(p, "rb").read()
        return hashlib.sha256(data).hexdigest()[:16]
    except Exception:  # noqa: BLE001
        return "unknown"
