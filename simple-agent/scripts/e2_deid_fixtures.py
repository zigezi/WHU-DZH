#!/usr/bin/env python3
"""E2 脱敏 fixture 电池（P5a.95 §四.1/§四.2 + P5a.96 条款二/三 + P5a.93 §3.4）。

- 精度 fixture：白名单/任务荷载词零误遮（a95 §四.1）；
- 召回 fixture：全泄漏形态 100% 遮蔽（a92 §4.2 + a95 §四.2 扩展）；
- 水印判别器 共存案/重合案（a93 §3.4）。
覆盖域声明随报告输出（a95 §四.6）。
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

PRECISION_SYN = ("管理公司 技术 人工智能 创新 深圳市 南山区 负责人 统一 智能 平台 系统\n"
                 "第一部分 第二部分 实施方案 经费预算 合计 直接费用 间接费用 小计\n"
                 "建设周期 签署日期 严重失信主体信息 场景名称 有效期\n")

RECALL_SYN = "\n".join([
    "股东信息表",
    "姜美娟                                  35",
    "法定代表人：徐康", "本申请由北京大学推荐，联系人徐康，电话13800138000。",
    "本项目由深圳兔展智能科技有限公司组织实施。深圳兔",
    "展智能科技有限公司（“兔展智能”）成立于 2014",
    "研发 兔灵大模型，自研 Open-Sora Plan 与 UniWorld-V2。",
    "报告编号 2025年第G20152177号。许可文书 22511376880。",
    "纳税人识别号 91330100MA27XW1234",
])

WM_COEXIST = "\n".join([
    "签署页",
    "法定代表人：李明",
    "签署日期：2024-03-01",
    "本项目文件与大学本科、档案管理、深度学习内容。",
    "婷","学","周","婷","学","周","婷","学","周","婷","学","周","婷","学","周","婷","学","周","婷","学","周",
    "李明",                                                    # 连续真名（甲名）
])
WM_OVERLAP = "\n".join([
    "深圳市南山区科技项目管理",   # 含"科""理"等潜在水印字
    "周", "周", "周", "周", "周", "周", "周", "周",   # 高频孤立"周"（水印带）
    "本项目使用人工智能管理系统平台。",
])


def deid(syn, wm_extra=None):
    ent = D.collect_entities([syn])
    wm = D.watermarks([syn]) | (wm_extra or set())
    m = {}
    return D.deid_text(syn, m, ent, wm, WL), m, wm


def main():
    checks = []

    # 1) 精度：白名单/任务荷载词零误遮
    out, _, _ = deid(PRECISION_SYN)
    whitelist_hits = [w for w in [
        "管理公司", "技术", "人工智能", "创新", "深圳市", "南山区", "负责人", "统一", "智能",
        "平台", "系统", "第一部分", "第二部分", "实施方案", "经费预算", "合计",
        "直接费用", "间接费用", "小计", "建设周期", "签署日期", "严重失信主体信息", "场景名称", "有效期"]
        if w and w not in out]
    checks.append({"case": "precision_whitelist_zero_mask", "pass": not whitelist_hits,
                   "masked_wrongly": whitelist_hits})

    # 2) 召回：全形态 100% 遮蔽
    out, _, _ = deid(RECALL_SYN)
    leak = [t for t in ["姜美娟", "徐康", "北京大学", "深圳兔展智能科技有限公司", "兔展智能",
                        "深圳兔", "兔灵", "Open-Sora", "UniWorld", "13800138000",
                        "91330100MA27XW1234", "2025年第G20152177号"] if t in out]
    checks.append({"case": "recall_all_forms_masked", "pass": not leak, "leaks": leak})

    # 3) 水印共存案：签署字段保留、连续真名遮蔽、散布水印清除（路径不互换）
    out, _, wm = deid(WM_COEXIST)
    sign_kept = "签署日期：2024-03-01" in out and "法定代表人：" in out
    real_masked = "李明" not in out
    # a101 §四.5：水印删除挂起——不要求清除；要求**不误删正文**（文件/大学/档案/深度学习完整）
    no_overdelete = all(w in out for w in ("文件", "大学本科", "档案管理", "深度学习"))
    checks.append({"case": "watermark_suspended_no_overdelete",
                   "pass": sign_kept and real_masked and no_overdelete and bool(wm),
                   "sign_kept": sign_kept, "real_masked": real_masked,
                   "no_overdelete": no_overdelete, "wm_registered": sorted(wm)})

    # 4) 水印重合案：正文常用字不被误删
    out, _, _ = deid(WM_OVERLAP)
    content_kept = ("深圳市南山区科技项目管理" in out and "人工智能管理系统平台" in out)
    checks.append({"case": "watermark_overlap_content_kept", "pass": content_kept, "out_has": content_kept})

    n, passed = len(checks), sum(1 for c in checks if c["pass"])
    out = {"note": "E2 脱敏 fixture 电池",
           "n": n, "passed": passed, "deployed": passed == n, "results": checks,
           "coverage_domain": "量程：合成埋件（精度白名单 / 召回全形态 / 水印共存·重合）；"
                              "已知排除：真实语料中未入表实体之发现（由独立召回探针 + 人工锚覆盖）；"
                              "水印探针量程=孤立+胶合残留"}
    json.dump(out, open(os.path.join(R, "e2-deid-fixtures.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"deployed": out["deployed"], "passed": passed, "n": n,
                      "fails": [c for c in checks if not c["pass"]]}, ensure_ascii=False, indent=1))
    return 0 if out["deployed"] else 1


if __name__ == "__main__":
    sys.exit(main())
