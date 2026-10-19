#!/usr/bin/env python3
"""P5a.91 §四：规则集 v0.3 逐规则 fixture 电池（每条 ≥1 正 1 负；naming_proof 延伸）。

  /root/miniconda3/envs/mini-agent/bin/python scripts/e2_eval_rules_battery.py
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e2_eval import evaluate, load_ruleset  # noqa: E402
from e2_normalize import locate_quote  # noqa: E402

R = os.path.join(ROOT, ".agent", "reports")
RULESET = load_ruleset(os.path.join(ROOT, "scripts", "e2_ruleset_v0.4.json"))

TASK = {"unit_mult_yuan": 10000, "credit_report_validity_months": 3}

BASE = {
 "申请书": (
   "揭榜申请书\n填表声明与保证\n第一部分：申报主体\n第二部分：技术方案\n第三部分：项目预算\n"
   "项目预算：100\n经费预算：100\n场景名称：智慧园区\n知识产权无失信声明\n"
   "签署日期：2023-12-01\n建设周期：2024-01-01 至 2024-12-31\n"),
 "实施方案": (
   "实施方案\n一、场景需求理解\n二、建设单位\n三、合作模式\n四、实施计划\n五、经费预算\n"
   "项目预算：100\n经费预算：100\n场景名称：智慧园区\n阶段月份：2024-05-01\n"),
 "信用报告": (
   "信用报告\n基本信息\n严重失信主体信息 0 条\n数据更新时间：2023-11-01\n"),
 "概算": (
   "经费概算（单位：万元）\n项目预算 100\n合计 210\n直接费用 100\n间接费用 110\n"
   "小计 210\n财政资助 100\n自筹经费 110\n"),
}

EXPECT_BASE = {
 "R1-申请书": "PASS", "R1-实施方案": "PASS", "R1-信用报告": "PASS",
 "R1-签署文本标签": "PASS", "R1-印章物理存在": "NA",
 "R2.1": "PASS", "R2.2": "PASS", "R3.1": "PASS", "R3.2a": "PASS", "R3.2b": "NA",
 "R3.3": "PASS", "R3.4": "PASS", "R3.5": "PASS", "R3.6": "PASS",
}


def verd(docs, task=TASK):
    return {x["id"]: x["verdict"] for x in evaluate(docs, task, RULESET)["rules"]}


def mutate(doc, old, new):
    d = copy.deepcopy(BASE)
    d[doc] = d[doc].replace(old, new)
    return d


def main():
    checks = []
    base = verd(BASE)
    for rid, want in EXPECT_BASE.items():
        checks.append({"case": f"base::{rid}", "pass": base.get(rid) == want,
                       "got": base.get(rid), "want": want})

    negs = [
        ("R1-申请书", mutate("申请书", "第三部分", "___")),
        ("R1-实施方案", mutate("实施方案", "合作模式", "___")),
        ("R1-信用报告", mutate("信用报告", "基本信息", "___")),
        ("R2.1", mutate("概算", "合计 210", "合计 200")),
        ("R2.2", mutate("概算", "项目预算 100", "项目预算 200")),
        ("R3.1", mutate("实施方案", "经费预算：100", "经费预算：200")),
        ("R3.2a", mutate("信用报告", "严重失信主体信息 0 条", "严重失信主体信息 2 条")),
        ("R3.3", mutate("申请书", "签署日期：2023-12-01", "签署日期：2024-06-01")),
        ("R3.4", mutate("实施方案", "阶段月份：2024-05-01", "阶段月份：2025-05-01")),
        ("R3.5", mutate("信用报告", "数据更新时间：2023-11-01", "数据更新时间：2023-01-01")),
        ("R3.6", mutate("实施方案", "场景名称：智慧园区", "场景名称：智慧园区X")),
        ("R1-签署文本标签", mutate("申请书", "签署日期：2023-12-01", "日期：2023-12-01")),
    ]
    for rid, docs in negs:
        v = verd(docs).get(rid)
        checks.append({"case": f"neg::{rid}", "pass": v == "FAIL", "got": v, "want": "FAIL"})

    # a100 §二.2：quote 空白归一化定位（±1 空格 / 多空格 run / 全角空格 仍匹配）
    doc = "01    合计（直接费用+间接费用）   100   110   210"
    q1 = "01 合计（直接费用+间接费用） 100 110 210"      # 空格被折叠
    q2 = "01  合计（直接费用+间接费用）    100  110  210" # 多空格 run
    q3 = "01　合计（直接费用+间接费用）　100 110 210"  # 全角空格
    checks.append({"case": "normalize_quote_plusminus_space", "pass": locate_quote(doc, q1)})
    checks.append({"case": "normalize_quote_multispace_run", "pass": locate_quote(doc, q2)})
    checks.append({"case": "normalize_quote_fullwidth_space", "pass": locate_quote(doc, q3)})
    # R3.2b：无论输入恒 NA（不得越权判 FAIL）
    v = verd(BASE).get("R3.2b")
    checks.append({"case": "R3.2b_always_na", "pass": v == "NA", "got": v})
    # R3.5：任务输入缺参数 → NA
    v = verd(BASE, {"unit_mult_yuan": 10000}).get("R3.5")
    checks.append({"case": "R3.5_param_absent_na", "pass": v == "NA", "got": v})

    n, passed = len(checks), sum(1 for c in checks if c["pass"])
    out = {"note": "P5a.91 §四 规则集 v0.3 逐规则 fixture 电池（≥1 正 1 负）",
           "version": RULESET["version"], "n": n, "passed": passed,
           "deployed": passed == n, "fails": [c for c in checks if not c["pass"]]}
    json.dump(out, open(os.path.join(R, "e2-eval-rules-battery.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["deployed"] else 1


if __name__ == "__main__":
    sys.exit(main())
