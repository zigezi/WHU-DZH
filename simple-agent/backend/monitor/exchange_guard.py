"""P5a.48：资产 non_delivered_exchange_v1 —— 前置条件可读（status==delivered）。

点火：即将调用 exchange_delivered_order_items，而**已知**该 order 状态 != delivered → 否决。
未知状态 → 不拦（避免误伤）。状态来自先前 get_order_details 的工具结果（observe）。
"""
import json
import re
from typing import Optional, Tuple

TARGET = "exchange_delivered_order_items"
SYNTHETIC = ("NOT-DELIVERED：该订单当前状态不是 delivered，无法 exchange。"
             "请先确认订单状态（或改用退货/其它路径）。")
_ORDER_RE = re.compile(r'"order_id"\s*:\s*"([^"]+)"')
_STATUS_RE = re.compile(r'"status"\s*:\s*"([^"]+)"')


class ExchangeGuard:
    def __init__(self):
        self._status = {}   # order_id -> status

    def observe(self, tool_name: str, args: dict, output: str):
        """从工具结果里记录订单状态（仅 get_order_details）。"""
        if tool_name != "get_order_details":
            return
        s = str(output or "")
        om = _ORDER_RE.search(s)
        sm = _STATUS_RE.search(s)
        if om and sm:
            self._status[om.group(1)] = sm.group(1)

    def before(self, tool_name: str, args: dict) -> Tuple[bool, Optional[str]]:
        if tool_name != TARGET:
            return False, None
        oid = (args or {}).get("order_id")
        st = self._status.get(oid)
        if st is not None and st != "delivered":
            return True, SYNTHETIC
        return False, None


guard = ExchangeGuard()


def reset():
    global guard
    guard = ExchangeGuard()
    return guard
