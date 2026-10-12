#!/usr/bin/env python3
"""P5a.52：基板 v3（真实仓库 + 变异注入，dogfooding）任务装配（零 token）。

- 模块来源 = **本项目纯逻辑模块**（无 I/O/配置/密钥；避开 .env/映射表——安全条款）；
- 任务 = 模块的**变异态**（注入 bug）+ 隐藏测试（自包含断言）；参考态全过，变异态杀 ≥1 测试；
- 簇单位 = 模块（family）。
产出：.agent/reports/e3-pilot-tasks-v3.json、e3-v3-gate.json
  /root/miniconda3/envs/mini-agent/bin/python scripts/e3_generator_v3.py
"""
import json
import os
import signal
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, ".agent", "reports")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from e3_generator import MUT_TRANSFORMS  # noqa: E402

MODULES = {
    "precedent_select": "backend/monitor/precedent_select.py",
    "repeat_guard": "backend/monitor/repeat_guard.py",
    "count_guard": "backend/monitor/count_guard.py",
    "interceptor": "backend/monitor/interceptor.py",
    "payment_guard": "backend/monitor/payment_guard.py",
    "exchange_guard": "backend/monitor/exchange_guard.py",
    "diff": "backend/requirements/adapters/tau/diff.py",
}

# 自包含测试（在 exec(模块源码) 后于同一命名空间运行；断言模块公开 API）
TESTS = {
    "precedent_select": [
        "cands=[{'id':10,'sig':'A','plan':[{'tool':'x'}]},{'id':30,'sig':'A','plan':[{'tool':'y'}]},{'id':20,'sig':'B','plan':[{'tool':'z'}]}]",
        "b=select(cands,'A'); assert b is not None and b['id']==10",
        "assert select(cands,'Z') is None",
        "assert len(content_hash([{'tool':'a'}]))==16",
        "assert plan_types([{'tool':'tau__x'},{'tool':'tau__y'}])==['tau__x','tau__y']",
    ],
    "repeat_guard": [
        "a={'x':1}",
        "G=RepeatFailureGuard(); G.after('t',a,False); G.after('t',a,False); assert G.before('t',a)[0] is True",
        "G2=RepeatFailureGuard(); G2.after('t',a,False); assert G2.before('t',a)[0] is False",
        "G3=RepeatFailureGuard(); G3.after('t',a,False); G3.after('t',a,False); G3.after('u',{'y':2},True); assert G3.before('t',a)[0] is False",
    ],
    "count_guard": [
        "assert CountMatchGuard().before('exchange_delivered_order_items',{'item_ids':['a','b'],'new_item_ids':['c']})[0] is True",
        "assert CountMatchGuard().before('exchange_delivered_order_items',{'item_ids':['a'],'new_item_ids':['b']})[0] is False",
        "assert CountMatchGuard().before('get_order_details',{'x':1})[0] is False",
    ],
    "interceptor": [
        "I=OrderLockInterceptor(); assert I.before('modify_pending_order_items',{'order_id':'#W1'})[0] is True",
        "I2=OrderLockInterceptor(); I2.before('modify_pending_order_items',{'order_id':'#W1'}); assert I2.before('modify_pending_order_items',{'order_id':'#W1'})[0] is False",
        "I3=OrderLockInterceptor(); I3.after('modify_pending_order_address',{'order_id':'#W1'},True); assert I3.before('modify_pending_order_items',{'order_id':'#W1'})[0] is False",
    ],
    "payment_guard": [
        "assert to_cents(33.33)+to_cents(33.33)+to_cents(33.34)==10000",
        "g=PaymentSumGuard(); g.observe('get_order_details',{},'{\"total\": 100.00}'); assert g.before('book_reservation',{'payment_methods':[{'amount':60},{'amount':30}]})[0] is True",
        "g2=PaymentSumGuard(); g2.observe('get_order_details',{},'{\"total\": 100.00}'); assert g2.before('book_reservation',{'payment_methods':[{'amount':60},{'amount':40}]})[0] is False",
    ],
    "exchange_guard": [
        "g=ExchangeGuard(); g.observe('get_order_details',{},'{\"order_id\": \"#W1\", \"status\": \"pending\"}'); assert g.before('exchange_delivered_order_items',{'order_id':'#W1'})[0] is True",
        "g2=ExchangeGuard(); g2.observe('get_order_details',{},'{\"order_id\": \"#W1\", \"status\": \"delivered\"}'); assert g2.before('exchange_delivered_order_items',{'order_id':'#W1'})[0] is False",
        "assert ExchangeGuard().before('exchange_delivered_order_items',{'order_id':'#W1'})[0] is False",
    ],
    "diff": [
        "d=data_diff({'orders':{'#W1':{'status':'x'}}},{'orders':{'#W1':{'status':'y'}}}); assert any(x.get('id')=='#W1' for x in d)",
        "r=actions_diff([{'name':'a','kwargs':{}}],[{'name':'b','kwargs':{}}],terminate=('respond',)); assert any(m['name']=='b' for m in r['missing'])",
    ],
}


class _T(Exception):
    pass


def _alarm(s, f):
    raise _T()


def run_ok(src, tests, timeout=1.5):
    old = signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        ns = {}
        exec(src, ns)
        for t in tests:
            exec(t, ns)
        return True
    except Exception:  # noqa: BLE001
        return False
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def mutate(src):
    for a, b in MUT_TRANSFORMS:
        if a in src and a not in b:
            m = src.replace(a, b, 1)
            if m != src:
                yield f"op:{a}->{b}", m


def compose_pairs(src):
    """难度旋钮（bugs>=2）：从不同起点叠加 2 个变异算子 → 多个 2-bug 坏模块。"""
    tf = MUT_TRANSFORMS
    for i in range(len(tf)):
        out, applied, kinds = src, 0, []
        for a, b in tf[i:]:
            if applied >= 2:
                break
            if a in out and a not in b:
                m = out.replace(a, b, 1)
                if m != out:
                    out, applied = m, applied + 1
                    kinds.append(f"{a}->{b}")
        if applied == 2:
            yield "+".join(kinds), out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--bugs", type=int, default=1)
    _a = ap.parse_args()
    tasks, rejected, mutants = [], 0, {}
    per_module = 8          # 每模块最多 8 个变异任务（凑 ≥30 题普查）
    for fam, rel in MODULES.items():
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            rejected += 1
            continue
        src = open(path, encoding="utf-8").read()
        tests = TESTS[fam]
        if not run_ok(src, tests):          # 参考态必须全过
            rejected += 1
            continue
        cnt = 0
        candidates = list(compose_pairs(src)) if _a.bugs >= 2 else list(mutate(src))
        for kind, m in candidates:
            if not run_ok(m, tests):         # 变异态杀 ≥1 测试
                # 静默配置（a53 §三）：可见 = 变异态**当前已通过**的测试（happy），边界入暗袋
                visible = [t for t in tests if run_ok(m, [t])]
                tasks.append({"task_id": f"E3V3-{fam}-{cnt}", "template_family": fam,
                              "is_canary": False, "buggy": m, "reference": src,
                              "hidden_tests": tests, "visible": visible,
                              "bug_kind": kind, "module": rel})
                mutants.setdefault(fam, []).append(kind)
                cnt += 1
                if cnt >= per_module:
                    break
        if cnt == 0:
            rejected += 1
    gate = {"note": "P5a.52 v3 装配门（参考态全过 ∧ 变异态杀≥1测试；dogfooding 真模块）",
            "admitted": len(tasks), "rejected": rejected, "mutants": mutants}
    json.dump({"note": "E3 v3 真模块变异任务", "n": len(tasks), "tasks": tasks},
              open(os.path.join(R, "e3-pilot-tasks-v3.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(gate, open(os.path.join(R, "e3-v3-gate.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(gate, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
