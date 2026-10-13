#!/usr/bin/env python3
"""P5a.59 四：哨兵接线金丝雀（零 token）——**经真实 execute_tool、按生产命名 `tau__`** 的点火证明。
5 件名称型守卫各一 `tau__` 前缀 veto 断言 + 原名/非触发负例。常驻套件。

  /root/miniconda3/envs/mini-agent/bin/python scripts/sentinel_wiring_battery.py
"""
import importlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)

for f in ("SA_LOCK_INTERCEPTOR", "SA_REPEAT_GUARD", "SA_COUNT_GUARD", "SA_EXCHANGE_GUARD",
          "SA_AVAIL_ENFORCE_GUARD", "SA_PAYMENT_ENFORCE_GUARD", "SA_GIFTCARD_ENFORCE_GUARD"):
    os.environ[f] = "1"

from tools.registry import ToolResult  # noqa: E402
from monitor.trace_store import trace_store  # noqa: E402
from monitor.schema import Trace  # noqa: E402
from monitor import (interceptor, repeat_guard, count_guard, exchange_guard,  # noqa: E402
                     availability_guard, payment_guard, giftcard_guard)
import worker  # noqa: E402

TID = "wiring-battery"


class StubReg:
    def __init__(self):
        self.called = []

    def execute(self, call):
        self.called.append(call.tool_name)
        return ToolResult(success=True, output="ok")


def setup_trace():
    trace_store.add_trace(Trace(trace_id=TID, task_id=TID, task_content="wiring battery",
                                start_time=time.time(), status="running"))


def reset_all():
    interceptor.reset(); repeat_guard.reset(); count_guard.reset(); exchange_guard.reset()
    availability_guard.reset(); payment_guard.reset(); giftcard_guard.reset()


def run_case(name, tool, args, expect_veto, setup=None):
    reset_all()
    if setup:
        setup()
    reg = StubReg()
    res = worker.execute_tool(TID, None, tool, args, registry=reg)
    veto = (reg.called == [])            # 未执行 = 被拦
    ok = (veto == expect_veto) and ((res.success is False) if expect_veto else True)
    return {"case": name, "tool": tool, "veto": veto, "expect_veto": expect_veto, "pass": ok}


def main():
    setup_trace()
    cases = []
    # 5 件名称型守卫：tau__ 前缀 veto 断言
    cases.append(run_case("lock_tau_prefix_veto", "tau__modify_pending_order_items",
                          {"order_id": "#W1"}, True))
    cases.append(run_case("count_tau_prefix_veto", "tau__exchange_delivered_order_items",
                          {"item_ids": ["a", "b"], "new_item_ids": ["c"]}, True))
    cases.append(run_case("exchange_tau_prefix_veto", "tau__exchange_delivered_order_items",
                          {"order_id": "#W1"}, True,
                          setup=lambda: exchange_guard.guard.observe(
                              "get_order_details", {}, '{"order_id": "#W1", "status": "pending"}')))
    cases.append(run_case("avail_enforce_tau_prefix_veto", "tau__book_reservation",
                          {"cabin": "economy", "passengers": [{"n": 1}],
                           "flights": [{"flight_number": "HAT1"}]}, True))
    cases.append(run_case("payment_enforce_tau_prefix_veto", "tau__book_reservation",
                          {"payment_methods": [{"amount": 1}]}, True))
    # 负例1：非目标工具（tau__ 前缀）→ 不拦
    cases.append(run_case("neg_non_target_tool", "tau__get_order_details", {"order_id": "#W1"}, False))
    # 负例2：原名回归（无 tau__，生产不应出现）→ 归一化后仍按目标处理=拦；此处用非目标原名示意不误拦
    cases.append(run_case("neg_unprefixed_non_target", "get_order_details", {"order_id": "#W1"}, False))
    # 负例3：lock 已改地址后 → 不拦
    cases.append(run_case("neg_lock_after_address", "tau__modify_pending_order_items",
                          {"order_id": "#W1"}, False,
                          setup=lambda: interceptor.interceptor.after(
                              "modify_pending_order_address", {"order_id": "#W1"}, True)))
    n = len(cases); passed = sum(1 for c in cases if c["pass"])
    out = {"note": "P5a.59 四：哨兵接线金丝雀（真实 execute_tool + tau__ 生产命名）",
           "n": n, "passed": passed, "all_pass": passed == n, "cases": cases}
    json.dump(out, open(os.path.join(ROOT, ".agent", "reports", "sentinel-wiring-battery.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
