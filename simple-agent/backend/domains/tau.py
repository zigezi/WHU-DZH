"""τ 域包（已落地）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import DomainPack, register  # noqa: E402
from requirements.adapters.tau.deident import FIELD_CLASS  # noqa: E402

MUT = {
    "cancel_reservation", "book_reservation", "update_reservation_flights",
    "update_reservation_baggages", "send_certificate", "cancel_pending_order",
    "modify_pending_order_address", "modify_pending_order_items",
    "modify_pending_order_payment", "exchange_delivered_order_items",
    "return_delivered_order_items",
}

TAU = register(DomainPack(
    name="tau",
    mutating_tools=MUT,
    transfer_tool="transfer_to_human_agents",
    read_prefixes=("get_", "search_", "list_", "find_", "calculate", "think"),
    entity_field_class=dict(FIELD_CLASS),
    interceptor_rules=[{
        "rule": "lock_order_v1",
        "target_tool": "modify_pending_order_items",
        "prereq_tool": "modify_pending_order_address",
        "scope_key": "order_id",
        "death_cause": "lock_order",
    }],
    lock_scope_key="order_id",
    description="τ-bench airline/retail；已部署资产=lock_order_v1 拦截器",
))
