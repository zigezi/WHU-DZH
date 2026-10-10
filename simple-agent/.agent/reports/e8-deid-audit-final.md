# e8 终轮人工核查样本（自由文本重度单元，P5a.39 §三）

> 只判两条：**(a) 读得通吗**（替换后文本作为先例是否连贯、无突兀伪值堆砌）
> **(b) 有无违和裸字符串**（既不像伪真值 `XXX_0x…` 又不像封闭词表的字符串=未知类探测器）。
> ②③④①⑤ 已全部机检通过，不必再判。


## Case 01  (task=TAU-A-014 <- injectant=TAU-A-027)  free_text_chars=668
lint: no_residual=True db_nonmember=True db_dict_ok=True

**自由文本片段：**
- `summary`:
  ```
  User USR_0x620727 requests cancellation of reservation RES_0x05EFC4 (MCO -> PHX -> SEA, one-way, business, 2 passengers). Flight segments were scheduled for 2027-02-14 and 2027-02-15, both in the past relative to the current date 2027-02-16, so the trip may contain already-flown segments. Agent cannot cancel a trip with used segments and is transferring for human handling. Note: user's separate request to cancel RES_0x66C878 was denied as ineligible (basic economy, no travel insurance, booked more than 24 hours prior, airline did not cancel). RES_0xCC919A nonstop change could not be made (no nonstop JFK -> MCO flights on 2027-02-21, 2027-02-22, or 2027-02-23).
  ```
**完整脱敏计划：**
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

## Case 02  (task=TAU-A-044 <- injectant=TAU-A-042)  free_text_chars=526
lint: no_residual=True db_nonmember=True db_dict_ok=True

**自由文本片段：**
- `summary`:
  ```
  User USR_0xF47CC1 wants to cancel reservation RES_0x5EE04D (basic economy, one way MCO→SFO, flights RES_0xD35880 on 2027-02-20 and RES_0xE5C089 on 2027-02-21, booked 2027-02-03) due to illness and receive a refund. Reservation record shows insurance: no, and the booking is outside the 24-hour window, so cancellation is not permitted under policy. User insists she purchased travel insurance with this flight and requests that a human agent investigate the insurance purchase separately, potentially under a different record.
  ```
**完整脱敏计划：**
```
[
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x5EE04D"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User USR_0xF47CC1 wants to cancel reservation RES_0x5EE04D (basic economy, one way MCO→SFO, flights RES_0xD35880 on 2027-02-20 and RES_0xE5C089 on 2027-02-21, booked 2027-02-03) due to illness and receive a refund. Reservation record shows insurance: no, and the booking is outside the 24-hour window, so cancellation is not permitted under policy. User insists she purchased travel insurance with this flight and requests that a human agent investigate the insurance purchase separately, potentially under a different record."
  }
 }
]
```

## Case 03  (task=TAU-A-016 <- injectant=TAU-A-022)  free_text_chars=454
lint: no_residual=True db_nonmember=True db_dict_ok=True

**自由文本片段：**
- `summary`:
  ```
  User USR_0x0C0F16 wants to change flights on reservation RES_0xB6F07E (EWR→MIA→LAX, 2027-02-22) to travel home sooner due to a family health emergency. The reservation is basic economy and cannot be modified per policy; user is willing to upgrade cabin but that does not permit a flight change. Cancellation also not permitted (booked 2027-02-10, no travel insurance, airline did not cancel). Requesting human assistance for the health-related exception.
  ```
**完整脱敏计划：**
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

## Case 04  (task=TAU-A-025 <- injectant=TAU-A-013)  free_text_chars=446
lint: no_residual=True db_nonmember=True db_dict_ok=True

**自由文本片段：**
- `summary`:
  ```
  User USR_0xEABE8B (regular member) requests changing reservation RES_0x2E8786 to a nonstop ATL→LAS flight, changing destination and routing. Reservation is basic_economy, round_trip (LAX-ATL), and the first two segments (LAX→ORD 2027-02-14, ORD→ATL 2027-02-15) have already been flown. Change is not possible via agent tools (cabin upgrade would not permit flight/destination change; used segments cannot be modified). User requests human review.
  ```
**完整脱敏计划：**
```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0xEABE8B"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x2E8786"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User USR_0xEABE8B (regular member) requests changing reservation RES_0x2E8786 to a nonstop ATL→LAS flight, changing destination and routing. Reservation is basic_economy, round_trip (LAX-ATL), and the first two segments (LAX→ORD 2027-02-14, ORD→ATL 2027-02-15) have already been flown. Change is not possible via agent tools (cabin upgrade would not permit flight/destination change; used segments cannot be modified). User requests human review."
  }
 }
]
```

## Case 05  (task=TAU-R-081 <- injectant=TAU-R-098)  free_text_chars=663
lint: no_residual=True db_nonmember=True db_dict_ok=True

**自由文本片段：**
- `summary`:
  ```
  User NAME_0xA1D11C Li (USR_0xE22ADC) requested two NAME_0x6F4DC8 on pending order ORD_0x591F0D: (1) modify the NAME_0xD8BA77 to the cheapest available green type, and (2) change the shipping address from the LA address (ADDR_0xB85EDF, ADDR_0x7424C5, ADDR_0x031416, CA ADDR_0xDCCFD3) to his NYC address (ADDR_0x74B2AF, ADDR_0x1DEC63, ADDR_0x63E28F, NY ADDR_0x1DDF4D). NAME_0xD3C1AF 1 succeeded (order now 'pending (item modified)', $5.15 refund issued to PayPal). NAME_0xD3C1AF 2 failed because the order status changed to 'pending (item modified)', which can no longer be modified. User needs human assistance to update the shipping address on order ORD_0x591F0D.
  ```
**完整脱敏计划：**
```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0xA1D11C",
   "last_name": "NAME_0xDA2707",
   "zip": "ADDR_0xDCCFD3"
  }
 },
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0xE22ADC"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x591F0D"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xB65D6F"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0x5D18A5"
  }
 },
 {
  "tool": "tau__modify_pending_order_items",
  "args": {
   "order_id": "ORD_0x591F0D",
   "item_ids": [
    "ITEM_0x8C2C94"
   ],
   "new_item_ids": [
    "ITEM_0xC511F9"
   ],
   "payment_method_id": "PAY_0x745E8A"
  }
 },
 {
  "tool": "tau__modify_pending_order_address",
  "args": {
   "order_id": "ORD_0x591F0D",
   "address1": "ADDR_0x74B2AF",
   "address2": "ADDR_0x1DEC63",
   "city": "ADDR_0x63E28F",
   "state": "NY",
   "country": "USA",
   "zip": "ADDR_0x1DDF4D"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User NAME_0xA1D11C Li (USR_0xE22ADC) requested two NAME_0x6F4DC8 on pending order ORD_0x591F0D: (1) modify the NAME_0xD8BA77 to the cheapest available green type, and (2) change the shipping address from the LA address (ADDR_0xB85EDF, ADDR_0x7424C5, ADDR_0x031416, CA ADDR_0xDCCFD3) to his NYC address (ADDR_0x74B2AF, ADDR_0x1DEC63, ADDR_0x63E28F, NY ADDR_0x1DDF4D). NAME_0xD3C1AF 1 succeeded (order now 'pending (item modified)', $5.15 refund issued to PayPal). NAME_0xD3C1AF 2 failed because the order status changed to 'pending (item modified)', which can no longer be modified. User needs human assistance to update the shipping address on order ORD_0x591F0D."
  }
 }
]
```

## Case 06  (task=TAU-R-051 <- injectant=TAU-R-019)  free_text_chars=629
lint: no_residual=True db_nonmember=True db_dict_ok=True

**自由文本片段：**
- `summary`:
  ```
  User NAME_0xC74B27 NAME_0xE0D15C (USR_0x66EAB5) had a delivered order ORD_0x71BC44. She wanted to return the NAME_0x51F714 AND exchange the NAME_0xBEEB1A and NAME_0x3FB902 for the cheapest available versions of the same products. The return was processed successfully (order status now 'return requested'), but the exchange failed because the order was no longer in 'delivered' status. Requesting the exchange to: NAME_0xBEEB1A ITEM_0xBA6D31 -> ITEM_0xFD6373 (large, memory foam, beige, $247.87), NAME_0x3FB902 ITEM_0x44BFA9 -> ITEM_0xF2C251 (leather, blue, no armrest, standard back, $646.39), refund difference to PAY_0x1DBCAD.
  ```
**完整脱敏计划：**
```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0xC74B27",
   "last_name": "NAME_0xE0D15C",
   "zip": "ADDR_0xB1B407"
  }
 },
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x66EAB5"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x71BC44"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x3FBF30"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0xA44AC6"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0xE63FFF"
  }
 },
 {
  "tool": "tau__return_delivered_order_items",
  "args": {
   "order_id": "ORD_0x71BC44",
   "item_ids": [
    "ITEM_0x0F4800"
   ],
   "payment_method_id": "PAY_0x1DBCAD"
  }
 },
 {
  "tool": "tau__exchange_delivered_order_items",
  "args": {
   "order_id": "ORD_0x71BC44",
   "item_ids": [
    "ITEM_0xBA6D31",
    "ITEM_0x44BFA9"
   ],
   "new_item_ids": [
    "ITEM_0xFD6373",
    "ITEM_0xF2C251"
   ],
   "payment_method_id": "PAY_0x1DBCAD"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User NAME_0xC74B27 NAME_0xE0D15C (USR_0x66EAB5) had a delivered order ORD_0x71BC44. She wanted to return the NAME_0x51F714 AND exchange the NAME_0xBEEB1A and NAME_0x3FB902 for the cheapest available versions of the same products. The return was processed successfully (order status now 'return requested'), but the exchange failed because the order was no longer in 'delivered' status. Requesting the exchange to: NAME_0xBEEB1A ITEM_0xBA6D31 -> ITEM_0xFD6373 (large, memory foam, beige, $247.87), NAME_0x3FB902 ITEM_0x44BFA9 -> ITEM_0xF2C251 (leather, blue, no armrest, standard back, $646.39), refund difference to PAY_0x1DBCAD."
  }
 }
]
```

## Case 07  (task=TAU-R-002 <- injectant=TAU-R-027)  free_text_chars=621
lint: no_residual=True db_nonmember=True db_dict_ok=True

**自由文本片段：**
- `summary`:
  ```
  Customer NAME_0xF657B8 NAME_0x47FBCA (USR_0x751500) wanted to return a NAME_0x4E4E59 and NAME_0x19E5A1 and exchange NAME_0x11AACF for the waterproof version, all in delivered order ORD_0x4CA5A2. A return was submitted for the NAME_0x8243AA and NAME_0x4C446F, which changed the order status to 'return requested'. The subsequent exchange for the NAME_0xF4F9A5 (item ITEM_0xD69A60 to waterproof item ITEM_0xB7CB1A) failed because a non-delivered order cannot be exchanged. Customer prefers the exchange over the return, but the return cannot be undone. Requesting help to switch from the return to the exchange if possible.
  ```
**完整脱敏计划：**
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
   "summary": "Customer NAME_0xF657B8 NAME_0x47FBCA (USR_0x751500) wanted to return a NAME_0x4E4E59 and NAME_0x19E5A1 and exchange NAME_0x11AACF for the waterproof version, all in delivered order ORD_0x4CA5A2. A return was submitted for the NAME_0x8243AA and NAME_0x4C446F, which changed the order status to 'return requested'. The subsequent exchange for the NAME_0xF4F9A5 (item ITEM_0xD69A60 to waterproof item ITEM_0xB7CB1A) failed because a non-delivered order cannot be exchanged. Customer prefers the exchange over the return, but the return cannot be undone. Requesting help to switch from the return to the exchange if possible."
  }
 }
]
```

## Case 08  (task=TAU-R-072 <- injectant=TAU-A-018)  free_text_chars=451
lint: no_residual=True db_nonmember=True db_dict_ok=True

**自由文本片段：**
- `summary`:
  ```
  User USR_0x3889F8 is requesting cancellation of reservation RES_0xD239D9 (MIA to PHX, one-way, basic economy, booked 2027-02-12, no insurance) due to a change of plans. Cancellation is not permitted under policy because it is basic economy, outside 24 hours, no travel insurance, and the airline did not cancel the flight. User understands the policy but is requesting an exception or a travel voucher/gift card for the value, so escalation is needed.
  ```
**完整脱敏计划：**
```
[
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xD239D9"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User USR_0x3889F8 is requesting cancellation of reservation RES_0xD239D9 (MIA to PHX, one-way, basic economy, booked 2027-02-12, no insurance) due to a change of plans. Cancellation is not permitted under policy because it is basic economy, outside 24 hours, no travel insurance, and the airline did not cancel the flight. User understands the policy but is requesting an exception or a travel voucher/gift card for the value, so escalation is needed."
  }
 }
]
```
