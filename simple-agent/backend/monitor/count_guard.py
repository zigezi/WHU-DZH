"""P5a.48：资产 items_count_match_v1 —— 纯句法谓词（域语义为零）。

点火：即将调用 exchange/modify items 且 `len(item_ids) != len(new_item_ids)` → 否决。
理由：tau 要求一一对应交换；两列表等长是纯句法检查，几乎不存在合法反例。
"""
from typing import Optional, Tuple

TARGET_TOOLS = {"exchange_delivered_order_items", "modify_pending_order_items"}
SYNTHETIC = ("COUNT-MISMATCH：item_ids 与 new_item_ids 长度必须相等（一一对应），"
             "请修正后再调用。")


class CountMatchGuard:
    def before(self, tool_name: str, args: dict) -> Tuple[bool, Optional[str]]:
        if tool_name not in TARGET_TOOLS:
            return False, None
        a = args or {}
        i, n = a.get("item_ids"), a.get("new_item_ids")
        if isinstance(i, list) and isinstance(n, list) and len(i) != len(n):
            return True, SYNTHETIC
        return False, None


guard = CountMatchGuard()


def reset():
    global guard
    guard = CountMatchGuard()
    return guard
