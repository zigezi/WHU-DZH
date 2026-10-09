# e8 脱敏库抽检样本 v2（跨 airline/retail 多族；rubric 见 P5a.37 §三）

① I-III 全类型前缀伪真值 ② 同实体同假值/不同实体不同值 ③ 日期数值保序 ④ 无原始真值（机器已过）⑤ IV 裸值仅限封闭词表

## Case 01  env=airline  (task=TAU-A-000 <- injectant=TAU-A-007)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

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

## Case 02  env=airline  (task=TAU-A-005 <- injectant=TAU-A-026)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

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
   "reservation_id": "RES_0x66C878"
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
   "summary": "User USR_0x620727 requests cancellation of two reservations. RES_0x05EFC4 (MCO-SEA, business) has already-flown segments (2027-02-14 and 2027-02-15), so it cannot be cancelled by the agent. RES_0x66C878 (CLT-EWR round trip, basic economy, created 2027-02-13) is outside the 24-hour window and has no travel insurance, so it cannot be cancelled by the agent. User acknowledges these policy limitations and requests human assistance."
  }
 }
]
```

## Case 03  env=airline  (task=TAU-A-014 <- injectant=TAU-A-027)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

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
   "reservation_id": "RES_0x66C878"
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
   "summary": "User USR_0x620727 requests cancellation of reservation RES_0x05EFC4 (MCO -> PHX -> SEA, one-way, business, 2 passengers). Flight segments were scheduled for 2027-02-14 and 2027-02-15, both in the past relative to the current date 2027-02-16, so the trip may contain already-flown segments. Agent cannot cancel a trip with used segments and is transferring for human handling. Note: user's separate request to cancel RES_0x66C878 was denied as ineligible (basic economy, no travel insurance, booked more than 24 hours prior, airline did not cancel). RES_0xCC919A nonstop change could not be made (no nonstop JFK -> MCO flights on 2027-02-21, 2027-02-22, or 2027-02-23)."
  }
 }
]
```

## Case 04  env=airline  (task=TAU-A-015 <- injectant=TAU-A-049)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x37D3D5"
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

## Case 05  env=airline  (task=TAU-A-016 <- injectant=TAU-A-022)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

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

## Case 06  env=airline  (task=TAU-A-029 <- injectant=TAU-A-037)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0xACD976"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xBAD0E6"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xF7F3DB"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x9767C8"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x1FEB12"
  }
 },
 {
  "tool": "tau__cancel_reservation",
  "args": {
   "reservation_id": "RES_0x9767C8"
  }
 },
 {
  "tool": "tau__send_certificate",
  "args": {
   "user_id": "USR_0xACD976",
   "amount": 274.0
  }
 }
]
```

## Case 07  env=airline  (task=TAU-A-040 <- injectant=TAU-R-011)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__find_user_id_by_email",
  "args": {
   "email": "EMAIL_0x4BE33D"
  }
 },
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0xAAB29F"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x879BCD"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xB5926B"
  }
 },
 {
  "tool": "tau__return_delivered_order_items",
  "args": {
   "order_id": "ORD_0x879BCD",
   "item_ids": [
    "ITEM_0x67C3F9",
    "ITEM_0x0CC511",
    "ITEM_0x748196",
    "ITEM_0x1EB942"
   ],
   "payment_method_id": "PAY_0x79AF5B"
  }
 },
 {
  "tool": "tau__return_delivered_order_items",
  "args": {
   "order_id": "ORD_0xB5926B",
   "item_ids": [
    "ITEM_0xD7B0B9"
   ],
   "payment_method_id": "PAY_0xB08498"
  }
 }
]
```

## Case 08  env=airline  (task=TAU-A-046 <- injectant=TAU-R-040)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__find_user_id_by_email",
  "args": {
   "email": "EMAIL_0xA6529B"
  }
 },
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x823809"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x73D3A6"
  }
 },
 {
  "tool": "tau__modify_pending_order_payment",
  "args": {
   "order_id": "ORD_0x73D3A6",
   "payment_method_id": "PAY_0xB30F9E"
  }
 }
]
```

## Case 09  env=retail  (task=TAU-R-002 <- injectant=TAU-R-027)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0xF657B8",
   "last_name": "NAME_0x47FBCA",
   "zip": "ADDR_0x3B87E6"
  }
 },
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x751500"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xA8C35E"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x4CA5A2"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xD1BC71"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xBD307E"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0x9174D3"
  }
 },
 {
  "tool": "tau__return_delivered_order_items",
  "args": {
   "order_id": "ORD_0x4CA5A2",
   "item_ids": [
    "ITEM_0xF645AB",
    "ITEM_0x6EE25B"
   ],
   "payment_method_id": "PAY_0xE3B7F0"
  }
 },
 {
  "tool": "tau__exchange_delivered_order_items",
  "args": {
   "order_id": "ORD_0x4CA5A2",
   "item_ids": [
    "ITEM_0xD69A60"
   ],
   "new_item_ids": [
    "ITEM_0xB7CB1A"
   ],
   "payment_method_id": "PAY_0xE3B7F0"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "Customer NAME_0xF657B8 NAME_0x47FBCA (USR_0x751500) wanted to return a NAME_0x4E4E59 and NAME_0x19E5A1 and exchange NAME_0x11AACF for the waterproof version, all in delivered order ORD_0x4CA5A2. A return was submitted for the hose and backpack, which changed the order status to 'return requested'. The subsequent exchange for the hiking boots (item ITEM_0xD69A60 to waterproof item ITEM_0xB7CB1A) failed because a non-delivered order cannot be exchanged. Customer prefers the exchange over the return, but the return cannot be undone. Requesting help to switch from the return to the exchange if possible."
  }
 }
]
```

## Case 10  env=retail  (task=TAU-R-005 <- injectant=TAU-R-052)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0x27BD83",
   "last_name": "NAME_0xDA2707",
   "zip": "ADDR_0xEE2C6E"
  }
 },
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x73D3B9"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x38129D"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xD4D880"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x3B7E48"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x4FCCAC"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0xA22157"
  }
 },
 {
  "tool": "tau__calculate",
  "args": {
   "expression": "3066.23 - 2895.55"
  }
 },
 {
  "tool": "tau__exchange_delivered_order_items",
  "args": {
   "order_id": "ORD_0x38129D",
   "item_ids": [
    "ITEM_0xCC975B"
   ],
   "new_item_ids": [
    "ITEM_0xCE603C"
   ],
   "payment_method_id": "PAY_0xDA002E"
  }
 }
]
```

## Case 11  env=retail  (task=TAU-R-011 <- injectant=TAU-R-029)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0xF657B8",
   "last_name": "NAME_0x47FBCA",
   "zip": "ADDR_0x3B87E6"
  }
 },
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x751500"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xA8C35E"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x4CA5A2"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xD1BC71"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xBD307E"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0xB47768"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0x69A9EE"
  }
 },
 {
  "tool": "tau__exchange_delivered_order_items",
  "args": {
   "order_id": "ORD_0xA8C35E",
   "item_ids": [
    "ITEM_0x9112FA"
   ],
   "new_item_ids": [
    "ITEM_0x8392EB"
   ],
   "payment_method_id": "PAY_0xE3B7F0"
  }
 },
 {
  "tool": "tau__exchange_delivered_order_items",
  "args": {
   "order_id": "ORD_0x4CA5A2",
   "item_ids": [
    "ITEM_0xF645AB"
   ],
   "new_item_ids": [
    "ITEM_0x168B5A"
   ],
   "payment_method_id": "PAY_0xE3B7F0"
  }
 }
]
```

## Case 12  env=retail  (task=TAU-R-016 <- injectant=TAU-R-028)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0xF657B8",
   "last_name": "NAME_0x47FBCA",
   "zip": "ADDR_0x3B87E6"
  }
 },
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x751500"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xA8C35E"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x4CA5A2"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xD1BC71"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xBD307E"
  }
 },
 {
  "tool": "tau__return_delivered_order_items",
  "args": {
   "order_id": "ORD_0xA8C35E",
   "item_ids": [
    "ITEM_0x9112FA"
   ],
   "payment_method_id": "PAY_0xE3B7F0"
  }
 },
 {
  "tool": "tau__return_delivered_order_items",
  "args": {
   "order_id": "ORD_0x4CA5A2",
   "item_ids": [
    "ITEM_0xF645AB",
    "ITEM_0x6EE25B"
   ],
   "payment_method_id": "PAY_0xE3B7F0"
  }
 },
 {
  "tool": "tau__return_delivered_order_items",
  "args": {
   "order_id": "ORD_0xD1BC71",
   "item_ids": [
    "ITEM_0x378223",
    "ITEM_0xCFA959"
   ],
   "payment_method_id": "PAY_0xE3B7F0"
  }
 },
 {
  "tool": "tau__cancel_pending_order",
  "args": {
   "order_id": "ORD_0xBD307E",
   "reason": "ordered by mistake"
  }
 }
]
```

## Case 13  env=retail  (task=TAU-R-019 <- injectant=TAU-A-000)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x394A9C"
  }
 },
 {
  "tool": "tau__search_direct_flight",
  "args": {
   "origin": "JFK",
   "destination": "SEA",
   "date": "2027-02-21"
  }
 },
 {
  "tool": "tau__search_direct_flight",
  "args": {
   "origin": "LGA",
   "destination": "SEA",
   "date": "2027-02-21"
  }
 },
 {
  "tool": "tau__search_direct_flight",
  "args": {
   "origin": "EWR",
   "destination": "SEA",
   "date": "2027-02-21"
  }
 },
 {
  "tool": "tau__search_onestop_flight",
  "args": {
   "origin": "JFK",
   "destination": "SEA",
   "date": "2027-02-21"
  }
 },
 {
  "tool": "tau__search_onestop_flight",
  "args": {
   "origin": "LGA",
   "destination": "SEA",
   "date": "2027-02-21"
  }
 },
 {
  "tool": "tau__search_onestop_flight",
  "args": {
   "origin": "EWR",
   "destination": "SEA",
   "date": "2027-02-21"
  }
 }
]
```

## Case 14  env=retail  (task=TAU-R-025 <- injectant=TAU-R-062)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0x333861",
   "last_name": "NAME_0x5F3321",
   "zip": "ADDR_0x074205"
  }
 },
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x3858F1"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x54229B"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x9FD39F"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x545E68"
  }
 },
 {
  "tool": "tau__list_all_product_types",
  "args": {}
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0x5D18A5"
  }
 }
]
```

## Case 15  env=retail  (task=TAU-R-050 <- injectant=TAU-R-080)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__find_user_id_by_email",
  "args": {
   "email": "EMAIL_0x471EEB"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xB5A14E"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0x574C05"
  }
 },
 {
  "tool": "tau__calculate",
  "args": {
   "expression": "54.84 - 46.85"
  }
 },
 {
  "tool": "tau__exchange_delivered_order_items",
  "args": {
   "order_id": "ORD_0xB5A14E",
   "item_ids": [
    "ITEM_0xDEBA72"
   ],
   "new_item_ids": [
    "ITEM_0x586B15"
   ],
   "payment_method_id": "PAY_0xC18D27"
  }
 }
]
```

## Case 16  env=retail  (task=TAU-R-057 <- injectant=TAU-A-002)
lint: no_residual=True json_ok=True db_nonmember=True db_dict_ok=True

```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x6BFCB0"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x143EF0"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x456D4C"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x3D38C5"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x878D98"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xD19D4D"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xFF3E83"
  }
 },
 {
  "tool": "tau__update_reservation_flights",
  "args": {
   "reservation_id": "RES_0x143EF0",
   "cabin": "economy",
   "flights": [
    {
     "flight_number": "FLT_0xB55C14",
     "date": "2027-02-22"
    },
    {
     "flight_number": "FLT_0xD91760",
     "date": "2027-02-22"
    }
   ],
   "payment_id": "PAY_0xD25547"
  }
 },
 {
  "tool": "tau__update_reservation_flights",
  "args": {
   "reservation_id": "RES_0x3D38C5",
   "cabin": "economy",
   "flights": [
    {
     "flight_number": "FLT_0x2383E1",
     "date": "2027-03-01"
    },
    {
     "flight_number": "FLT_0xCCDAB4",
     "date": "2027-03-01"
    },
    {
     "flight_number": "FLT_0x512BDE",
     "date": "2027-03-03"
    },
    {
     "flight_number": "FLT_0x372F71",
     "date": "2027-03-03"
    }
   ],
   "payment_id": "PAY_0x2A393F"
  }
 },
 {
  "tool": "tau__update_reservation_flights",
  "args": {
   "reservation_id": "RES_0x878D98",
   "cabin": "economy",
   "flights": [
    {
     "flight_number": "FLT_0x6BC124",
     "date": "2027-02-25"
    },
    {
     "flight_number": "FLT_0x7B4B16",
     "date": "2027-02-25"
    }
   ],
   "payment_id": "PAY_0xD25547"
  }
 },
 {
  "tool": "tau__update_reservation_flights",
  "args": {
   "reservation_id": "RES_0xD19D4D",
   "cabin": "economy",
   "flights": [
    {
     "flight_number": "FLT_0x7B032D",
     "date": "2027-02-24"
    },
    {
     "flight_number": "FLT_0xABB4FE",
     "date": "2027-02-24"
    }
   ],
   "payment_id": "PAY_0xE6C196"
  }
 },
 {
  "tool": "tau__update_reservation_flights",
  "args": {
   "reservation_id": "RES_0xFF3E83",
   "cabin": "economy",
   "flights": [
    {
     "flight_number": "FLT_0xDBF586",
     "date": "2027-02-22"
    },
    {
     "flight_number": "FLT_0x207CCC",
     "date": "2027-02-23"
    }
   ],
   "payment_id": "PAY_0x7BB5F9"
  }
 }
]
```
