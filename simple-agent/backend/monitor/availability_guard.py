"""P5a.54 C4-2：资产 flight_availability_v1 —— 订/改使用**已知无座**航班。

点火（确定性）：即将 `book_reservation`/`update_reservation_flights`，其 `flights` 中某
`flight_number` 的**本 run 内** search 观测到的 `available_seats[cabin]` < 所需乘客数 → 否决。
- **只基于可用性字段 + 本 run 新鲜度**（guard 每任务 reset），不基于"先前搜过"（P5a.48 用户裁定）；
- 未观测到该航班/座位 → 不拦（避免误伤）；update 乘客数未知 → 不拦。
"""
import json
from typing import Optional, Tuple


class FlightAvailabilityGuard:
    def __init__(self):
        self._seats = {}   # flight_number -> {cabin: available_seats}

    def observe(self, tool_name: str, args: dict, output: str):
        if not tool_name.startswith("search_"):
            return
        try:
            flights = json.loads(output) if isinstance(output, str) else output
        except Exception:  # noqa: BLE001
            return
        if not isinstance(flights, list):
            return
        for f in flights:
            if isinstance(f, dict) and f.get("flight_number") and isinstance(f.get("available_seats"), dict):
                self._seats[f["flight_number"]] = f["available_seats"]

    def before(self, tool_name: str, args: dict) -> Tuple[bool, Optional[str]]:
        a = args or {}
        if tool_name == "book_reservation":
            n = len(a.get("passengers") or [])
        elif tool_name == "update_reservation_flights":
            n = len(a.get("passengers") or [])   # 若未提供则 n=0 → 不拦（保守）
        else:
            return False, None
        cabin = a.get("cabin")
        if n <= 0 or not cabin:
            return False, None
        for f in a.get("flights") or []:
            fn = f.get("flight_number") if isinstance(f, dict) else None
            seats = self._seats.get(fn)
            if seats is not None and isinstance(seats.get(cabin), int) and seats[cabin] < n:
                return True, (f"NO-SEATS：航班 {fn} 的 {cabin} 在本 run 观测中仅剩 "
                              f"{seats[cabin]} 座 < 所需 {n} 座。请改选有座航班。")
        return False, None


guard = FlightAvailabilityGuard()


def reset():
    global guard
    guard = FlightAvailabilityGuard()
    return guard
