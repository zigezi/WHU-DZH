#!/usr/bin/env python3
"""E2 脱敏 fixture 电池（(c) 最小遮蔽核心；门套与生产同源 — P5a.107 三铁律）。

走**生产核心路径** `e2_deident.core_deid`：锚定实体字典 + 确定 PII + REF 整块。
  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_deid_fixtures.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import e2_deident as D  # noqa: E402

R = os.path.join(ROOT, ".agent", "reports")
WL = D.load_whitelist()
VAR = json.load(open(os.path.join(ROOT, "scripts", "e2_variants.json"), encoding="utf-8"))


def run(text, entities):
    mapping, ref = {}, set()
    code = D._masker(mapping)
    return D.core_deid(text, code, entities, WL, VAR, ref), mapping, ref


def main():
    checks = []

    # 1) 精度：白名单/任务荷载词零误遮（空字典）
    prec = ("管理公司 技术 人工智能 创新 深圳市 南山区 负责人 统一 智能 平台 系统\n"
            "拟采用 支持 多模态 能力 区级 设计 第一部分 经费预算 合计 直接费用 间接费用\n")
    out, _, _ = run(prec, {})
    bad = [w for w in prec.split() if w and w not in out]
    checks.append({"case": "precision_whitelist_zero_mask", "pass": not bad, "masked_wrongly": bad})

    # 2) 召回：字典实体遮蔽 + 大小写不敏感（VOLO~Volo）+ 变体
    ents = {"PERSON": ["徐康", "胡松"], "COMPANY": ["深圳兔展智能科技有限公司"],
            "PROJ": ["VOLO"], "DOCNO": ["2025年第G20152177号"]}
    rec = ("法定代表人：徐康，成员胡松；本项目由深圳兔展智能科技有限公司实施；\n"
           "引用 \"Volo: Vision outlooker\"；报告编号 2025年第G20152177号。\n")
    out, _, _ = run(rec, ents)
    leak = [t for t in ["徐康", "胡松", "深圳兔展智能科技有限公司", "Volo", "VOLO", "2025年第G20152177号"] if t in out]
    checks.append({"case": "recall_dict_case_insensitive", "pass": not leak, "leaks": leak})

    # 3) REF 整块遮蔽（作者/标题/期刊/年份全不留，行数守恒）
    refdoc = ('正文段落。\nReferences\n'
              'Li Yuan, Qibin Hou, Zihang Jiang, Jiashi Feng, and Shuicheng Yan.\n'
              '"Volo: Vision outlooker for visual recognition." IEEE TPAMI, 2024.\n'
              '正文再续。\n')
    out, _, refc = run(refdoc, {})
    ref_ok = ("Li Yuan" not in out and "Qibin" not in out and "Vision outlooker" not in out
              and "【REFS-】" in out and refdoc.count("\n") == out.count("\n"))
    checks.append({"case": "ref_block_whole_masked", "pass": ref_ok, "ref_chars": len(refc)})

    # 4) 白名单击穿：实体含白名单词（北京己任 ⊃ 北京）→ 实体整体遮；独立「北京」保留
    ents2 = {"COMPANY": ["北京己任科技有限公司"]}
    pierce = "北京己任科技有限公司与北京地区。\n"
    out, _, _ = run(pierce, ents2)
    checks.append({"case": "entity_pierces_whitelist",
                   "pass": ("北京己任科技有限公司" not in out and "北京地区" in out)})

    # 5) 水印删除已退役（不得因水印字删正文常用词）
    wmdoc = "本项目文件与大学本科、深度学习、档案管理。\n周\n学\n婷\n"
    out, _, _ = run(wmdoc, {})
    checks.append({"case": "watermark_delete_retired_no_char_loss",
                   "pass": all(w in out for w in ("文件", "大学本科", "深度学习", "档案管理"))})

    n, passed = len(checks), sum(1 for c in checks if c["pass"])
    out = {"note": "E2 脱敏 fixture 电池（(c) 核心路径；门套同源 a107）",
           "n": n, "passed": passed, "deployed": passed == n, "results": checks,
           "coverage_domain": "量程：锚定字典实体(含大小写/变体) + 确定 PII + REF 块 + 白名单击穿；"
                              "不覆盖：未入表实体的发现（由推测层标记清单 + 人工校正覆盖）"}
    json.dump(out, open(os.path.join(R, "e2-deid-fixtures.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"deployed": out["deployed"], "passed": passed, "n": n,
                      "fails": [c for c in checks if not c["pass"]]}, ensure_ascii=False, indent=1))
    return 0 if out["deployed"] else 1


if __name__ == "__main__":
    sys.exit(main())
