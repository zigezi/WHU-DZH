#!/usr/bin/env python3
"""E2 缺陷注入夹具生成器（a83 §四 / a85 §七.2）：真实文档 + 程序化注入已知缺陷 → 已知答案集。

用途：(i) 标定评测器灵敏度/特异度（评测器的 naming_proof）；(ii) 器官电池 fixture 来源。
夹具**只证明仪器**，不进基线 epoch 统计，不算尸体来源（a83 §四）。
零 token。
"""
import re

from e2_unit_norm import extract_amounts


def inject_missing_section(text: str, section_pattern: str):
    """删除含该章节模式的行（模拟缺失必备章节）。"""
    lines = text.splitlines()
    kept = [ln for ln in lines if not re.search(section_pattern, ln)]
    if len(kept) == len(lines):
        return None  # 无法注入（该模式缺席）
    return "\n".join(kept)


def inject_dimension_conflict(text: str, require: str, forbid: str):
    """追加一行同时含 require 与 forbid → 制造维度矛盾。"""
    return text + f"\n本项目已识别{require}，同时承诺：{forbid}。\n"


def inject_number_tamper(text: str, label: str):
    """篡改某字段某次出现的金额（首个金额 +1）→ 制造数字不一致。"""
    out, done = [], False
    for line in text.splitlines():
        if (not done) and label in line:
            amts = extract_amounts(line)
            if amts:
                raw, _ = amts[0]
                broken = re.sub(r"\d", lambda m: m.group(0), raw) + "9"  # 轻微改动
                line = line.replace(raw, broken, 1)
                done = True
        out.append(line)
    return "\n".join(out) if done else None


def make_fixtures(docs: dict, ruleset: dict) -> list:
    """docs: {name: text} → fixtures [{name, doc, label, kind}]。label: clean/defect。"""
    fixtures = []
    secs = ruleset.get("required_sections", [])
    dims = ruleset.get("dimensions", [])
    nums = ruleset.get("number_fields", [])
    for name, text in docs.items():
        fixtures.append({"name": f"{name}::clean", "doc": text, "label": "clean", "kind": "none"})
        for s in secs:
            d = inject_missing_section(text, s)
            if d is not None:
                fixtures.append({"name": f"{name}::miss[{s}]", "doc": d, "label": "defect",
                                 "kind": "missing_section"})
        for dim in dims:
            if dim.get("require") and dim.get("forbid"):
                fixtures.append({"name": f"{name}::dim[{dim['name']}]",
                                 "doc": inject_dimension_conflict(text, dim["require"][0], dim["forbid"][0]),
                                 "label": "defect", "kind": "dimension_conflict"})
        for lbl in nums:
            d = inject_number_tamper(text, lbl)
            if d is not None:
                fixtures.append({"name": f"{name}::num[{lbl}]", "doc": d, "label": "defect",
                                 "kind": "number_inconsistent"})
    return fixtures
