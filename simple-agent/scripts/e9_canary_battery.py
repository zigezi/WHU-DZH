#!/usr/bin/env python3
"""P5a.45 §三.1 / §二：锁序拦截器 B-2 金丝雀电池（≥5 探针，已知答案）。

判定 = 谓词点火正确性：**该拦的拦住、不该拦的不动**。确定性、零 token。
部署前验证器：全过 → 拦截器可入运行时。

  /root/miniconda3/envs/mini-agent/bin/python scripts/e9_canary_battery.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from monitor.interceptor import OrderLockInterceptor, SYNTHETIC  # noqa: E402

PROBES = []


def probe(name, fn):
    PROBES.append((name, fn))


# 探针 1：items-first（address 未改、未否决）→ 必须拦（覆盖 5 锁死任务型 R-041/072/098/105/058）
probe("P1_items_first_must_block", lambda: (
    lambda I: I.before("modify_pending_order_items", {"order_id": "#W1"})[0] is True
)(OrderLockInterceptor()))

# 探针 2：once-per-order —— 否决后重新发起同订单 items → 放行（不死循环）
def p2():
    I = OrderLockInterceptor()
    v1, _ = I.before("modify_pending_order_items", {"order_id": "#W1"})
    v2, _ = I.before("modify_pending_order_items", {"order_id": "#W1"})
    return v1 is True and v2 is False
probe("P2_once_per_order_reissue_passes", p2)

# 探针 3：先改地址（成功）再改物品 → 不拦（不该拦的不动）
def p3():
    I = OrderLockInterceptor()
    I.after("modify_pending_order_address", {"order_id": "#W1"}, success=True)
    return I.before("modify_pending_order_items", {"order_id": "#W1"})[0] is False
probe("P3_address_first_no_block", p3)

# 探针 4：异单独立 —— W2 未改地址 → 拦；不影响 W1
def p4():
    I = OrderLockInterceptor()
    a = I.before("modify_pending_order_items", {"order_id": "#W1"})[0]
    b = I.before("modify_pending_order_items", {"order_id": "#W2"})[0]
    return a is True and b is True
probe("P4_per_order_independent", p4)

# 探针 5：非目标工具（地址/查询/其它）→ 永不动
def p5():
    I = OrderLockInterceptor()
    return (I.before("modify_pending_order_address", {"order_id": "#W1"})[0] is False
            and I.before("get_order_details", {"order_id": "#W1"})[0] is False
            and I.before("return_delivered_order_items", {"order_id": "#W1"})[0] is False)
probe("P5_other_tools_never_block", p5)

# 探针 6：地址失败（未成功）→ items 仍拦（address_done 未置位）
def p6():
    I = OrderLockInterceptor()
    I.after("modify_pending_order_address", {"order_id": "#W1"}, success=False)
    return I.before("modify_pending_order_items", {"order_id": "#W1"})[0] is True
probe("P6_failed_address_still_blocks", p6)

# 探针 7：合成返回文案含"先改地址"与"重新发起"（可读、可执行）
def p7():
    I = OrderLockInterceptor()
    _, synth = I.before("modify_pending_order_items", {"order_id": "#W1"})
    return synth == SYNTHETIC and "先执行 modify_pending_order_address" in synth
probe("P7_synthetic_text_correct", p7)


def main():
    results = []
    for name, fn in PROBES:
        try:
            ok = bool(fn())
        except Exception as e:  # noqa: BLE001
            ok = False
            print(f"  {name}: ERROR {e!r}")
        results.append({"probe": name, "pass": ok})
    n = len(results)
    passed = sum(1 for r in results if r["pass"])
    out = {"note": "e9 锁序拦截器 B-2 金丝雀电池（≥5 探针，已知答案）",
           "n": n, "passed": passed, "all_pass": passed == n, "results": results}
    path = os.path.join(ROOT, ".agent", "reports", "e9-canary-battery.json")
    json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print("->", path)
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
