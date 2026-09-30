# e8 脱敏库人工抽检样本（10 例：伪真值/共指/关系保持/无残余真值）

> 检查项：① 全部实体为类型前缀伪真值（RES_/FLT_/...）② 同一实体全程同假值（共指）
> ③ 日期保序（整体平移，相对关系不变）④ 无原始真值。解盲/对照放 .agent/local/（未跟踪）。

## Case 01  (injectant=?, deid_hash=7357ec9d3ac93d50)
lint: no_residual=True json_ok=True db_nonmember=True

**脱敏后计划**：
```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x4630C0"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xB3DB41"
  }
 },
 {
  "tool": "tau__search_direct_flight",
  "args": {
   "origin": "ATL",
   "destination": "PHL",
   "date": "2027-02-25"
  }
 },
 {
  "tool": "tau__search_direct_flight",
  "args": {
   "origin": "ATL",
   "destination": "EWR",
   "date": "2027-02-25"
  }
 },
 {
  "tool": "tau__search_onestop_flight",
  "args": {
   "origin": "ATL",
   "destination": "PHL",
   "date": "2027-02-25"
  }
 },
 {
  "tool": "tau__search_onestop_flight",
  "args": {
   "origin": "ATL",
   "destination": "EWR",
   "date": "2027-02-25"
  }
 },
 {
  "tool": "tau__update_reservation_flights",
  "args": {
   "reservation_id": "RES_0xB3DB41",
   "cabin": "economy",
   "flights": [
    {
     "flight_number": "FLT_0x39A298",
     "date": "2027-02-25"
    },
    {
     "flight_number": "FLT_0x771144",
     "date": "2027-02-25"
    }
   ],
   "payment_id": "PAY_0x8F153D"
  }
 }
]
```

## Case 02  (injectant=?, deid_hash=cf7475ad034780a9)
lint: no_residual=True json_ok=True db_nonmember=True

**脱敏后计划**：
```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x620727"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "IFOYYZ"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x05EFC4"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xCC919A"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User USR_0x620727 requests cancellation of two reservations. RES_0x05EFC4 (MCO-SEA, business) has already-flown segments (2027-02-14 and 2027-02-15), so it cannot be cancelled by the agent. IFOYYZ (CLT-EWR round trip, basic economy, created 2027-02-13) is outside the 24-hour window and has no travel insurance, so it cannot be cancelled by the agent. User acknowledges these policy limitations and requests human assistance."
  }
 }
]
```

## Case 03  (injectant=?, deid_hash=a85da34a5b612de7)
lint: no_residual=True json_ok=True db_nonmember=True

**脱敏后计划**：
```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0x11F42F",
   "last_name": "NAME_0xD7AF8D",
   "zip": "92133"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xA59AD7"
  }
 }
]
```

## Case 04  (injectant=?, deid_hash=6661a5c9455ca8e1)
lint: no_residual=True json_ok=True db_nonmember=True

**脱敏后计划**：
```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x620727"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "IFOYYZ"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x05EFC4"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xCC919A"
  }
 },
 {
  "tool": "tau__search_direct_flight",
  "args": {
   "origin": "JFK",
   "destination": "MCO",
   "date": "2027-02-23"
  }
 },
 {
  "tool": "tau__search_direct_flight",
  "args": {
   "origin": "JFK",
   "destination": "MCO",
   "date": "2027-02-21"
  }
 },
 {
  "tool": "tau__search_direct_flight",
  "args": {
   "origin": "JFK",
   "destination": "MCO",
   "date": "2027-02-22"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User USR_0x620727 requests cancellation of reservation RES_0x05EFC4 (MCO -> PHX -> SEA, one-way, business, 2 passengers). Flight segments were scheduled for 2027-02-14 and 2027-02-15, both in the past relative to the current date 2027-02-16, so the trip may contain already-flown segments. Agent cannot cancel a trip with used segments and is transferring for human handling. Note: user's separate request to cancel IFOYYZ was denied as ineligible (basic economy, no travel insurance, booked more than 24 hours prior, airline did not cancel). RES_0xCC919A nonstop change could not be made (no nonstop JFK -> MCO flights on 2027-02-21, 2027-02-22, or 2027-02-23)."
  }
 }
]
```

## Case 05  (injectant=?, deid_hash=5c2a5c26dc1389f0)
lint: no_residual=True json_ok=True db_nonmember=True

**脱敏后计划**：
```
[
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "MDCLVA"
  }
 },
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x412BCF"
  }
 }
]
```

## Case 06  (injectant=?, deid_hash=a630464ac844b186)
lint: no_residual=True json_ok=True db_nonmember=True

**脱敏后计划**：
```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x0C0F16"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xB6F07E"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x3BE21A"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x495FDE"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x2466E9"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User USR_0x0C0F16 wants to change flights on reservation RES_0xB6F07E (EWR→MIA→LAX, 2027-02-22) to travel home sooner due to a family health emergency. The reservation is basic economy and cannot be modified per policy; user is willing to upgrade cabin but that does not permit a flight change. Cancellation also not permitted (booked 2027-02-10, no travel insurance, airline did not cancel). Requesting human assistance for the health-related exception."
  }
 }
]
```

## Case 07  (injectant=?, deid_hash=07091be8e4ab30ea)
lint: no_residual=True json_ok=True db_nonmember=True

**脱敏后计划**：
```
[
 {
  "tool": "tau__find_user_id_by_email",
  "args": {
   "email": "yusuf.rossi@example.com"
  }
 },
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0xA1D11C",
   "last_name": "NAME_0xCA6CEA",
   "zip": "19122"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x133452"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "1656367028"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "4896585277"
  }
 }
]
```

## Case 08  (injectant=?, deid_hash=7a8d7268df37e79d)
lint: no_residual=True json_ok=True db_nonmember=True

**脱敏后计划**：
```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0xF5C887"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xB8A58A"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x2DA655"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "IIHXDG"
  }
 },
 {
  "tool": "tau__search_direct_flight",
  "args": {
   "origin": "JFK",
   "destination": "DTW",
   "date": "2027-02-17"
  }
 },
 {
  "tool": "tau__book_reservation",
  "args": {
   "user_id": "USR_0xF5C887",
   "origin": "JFK",
   "destination": "DTW",
   "flight_type": "one_way",
   "cabin": "basic_economy",
   "flights": [
    {
     "flight_number": "FLT_0xFC22BF",
     "date": "2027-02-17"
    }
   ],
   "passengers": [
    {
     "first_name": "NAME_0x638004",
     "last_name": "NAME_0xEE6BCC",
     "dob": "1979-07-12"
    }
   ],
   "payment_methods": [
    {
     "payment_id": "PAY_0x321CD1",
     "amount": 75.35
    }
   ],
   "total_baggages": 0,
   "nonfree_baggages": 0,
   "insurance": "no"
  }
 }
]
```

## Case 09  (injectant=?, deid_hash=819d740aa7f52acf)
lint: no_residual=True json_ok=True db_nonmember=True

**脱敏后计划**：
```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0xB87484",
   "last_name": "NAME_0x5F3321",
   "zip": "78712"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x5BFD8E"
  }
 },
 {
  "tool": "tau__modify_pending_order_address",
  "args": {
   "order_id": "ORD_0x5BFD8E",
   "address1": "123 Elm Street",
   "address2": "Suite 641",
   "city": "Austin",
   "state": "TX",
   "country": "USA",
   "zip": "78712"
  }
 }
]
```

## Case 10  (injectant=?, deid_hash=e2bb9160f8befe06)
lint: no_residual=True json_ok=True db_nonmember=True

**脱敏后计划**：
```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x236709"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x9729F8"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xF2964B"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User USR_0x236709 wants to cancel reservation RES_0x9729F8 (MCO->BOS->CLT, 2027-03-01, basic economy, 2 passengers, no insurance, booked 2027-02-07) and receive a refund. Cancellation is not permitted under policy since it is beyond the 24-hour window, the airline did not cancel the flight, and no travel insurance was purchased. User is requesting escalation/approval beyond standard policy."
  }
 }
]
```
