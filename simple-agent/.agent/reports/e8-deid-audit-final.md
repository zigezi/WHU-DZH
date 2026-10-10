# e8 终轮人工核查样本 v2（P5a.40 后；自由文本重度单元）

> 只判两条：**(a) 读得通吗** **(b) 有无违和裸字符串**。①-⑤ 机检已过 + D1 停用词护栏已修。

## Case 01  (task=TAU-A-030 <- injectant=TAU-A-016)  free_text_chars=2039

**自由文本片段：**
- `thought`:
  ```
  User is silver member, reservation RES_0x558BA7 is economy, no insurance. Policy: compensation for delayed flights can be offered only if user is silver/gold OR has travel insurance OR flies business, and only after changing or cancelling the reservation, and only if user complains and asks. Here silver member qualifies by membership, but the policy says "and wants to change or cancel the reservation... offer a certificate after confirming facts and changing or cancelling the reservation." So compensation requires changing or cancelling. User hasn't asked to change/cancel. Also refund to original payment method not allowed for delay since cancellation rules: economy without insurance not cancellable unless within 24 hours or airline cancelled. So cannot offer refund. Could offer certificate if they change/cancel reservation, amount 50 × passengers = 150. Need to ask if they want to change/cancel.
  ```
- `thought`:
  ```
  Need to check cancellation eligibility for RES_0x558BA7. Reservation created 2027-02-06, current time 2027-02-16, more than 24 hours after booking. Economy cabin, no travel insurance. Airline did not cancel the flight; user says flight is delayed. Policy: basic economy or economy flights can be cancelled only if travel insurance bought and condition met; business can always cancel. Here no insurance, economy. So cannot cancel. Therefore cannot cancel and cannot offer certificate (which requires changing/cancelling). Also segments: flight FLT_0x43F4AD on 2027-02-16, FLT_0x12FFBA on same date, not flown yet (departed? no info). Cannot cancel. So deny.
  ```
- `summary`:
  ```
  User USR_0xA184CF (silver member) is requesting goodwill compensation (voucher or refund) for a delayed flight FLT_0x43F4AD on reservation RES_0x558BA7 (ORD-SEA, economy, no travel insurance, created 2027-02-06). Reservation cannot be cancelled under policy because it is outside 24 hours, no insurance, and flight was delayed not cancelled. Certificate cannot be offered because change/cancel is not possible. User asks to escalate for goodwill compensation authorization.
  ```
**完整脱敏计划：**
```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0xA184CF"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x9503E1"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xDD1073"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xD0FD6F"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xFF6C0E"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xD0D39C"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x3D1765"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x6CCFE9"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x38341C"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x558BA7"
  }
 },
 {
  "tool": "tau__think",
  "args": {
   "thought": "User is silver member, reservation RES_0x558BA7 is economy, no insurance. Policy: compensation for delayed flights can be offered only if user is silver/gold OR has travel insurance OR flies business, and only after changing or cancelling the reservation, and only if user complains and asks. Here silver member qualifies by membership, but the policy says \"and wants to change or cancel the reservation... offer a certificate after confirming facts and changing or cancelling the reservation.\" So compensation requires changing or cancelling. User hasn't asked to change/cancel. Also refund to original payment method not allowed for delay since cancellation rules: economy without insurance not cancellable unless within 24 hours or airline cancelled. So cannot offer refund. Could offer certificate if they change/cancel reservation, amount 50 × passengers = 150. Need to ask if they want to change/cancel."
  }
 },
 {
  "tool": "tau__think",
  "args": {
   "thought": "Need to check cancellation eligibility for RES_0x558BA7. Reservation created 2027-02-06, current time 2027-02-16, more than 24 hours after booking. Economy cabin, no travel insurance. Airline did not cancel the flight; user says flight is delayed. Policy: basic economy or economy flights can be cancelled only if travel insurance bought and condition met; business can always cancel. Here no insurance, economy. So cannot cancel. Therefore cannot cancel and cannot offer certificate (which requires changing/cancelling). Also segments: flight FLT_0x43F4AD on 2027-02-16, FLT_0x12FFBA on same date, not flown yet (departed? no info). Cannot cancel. So deny."
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User USR_0xA184CF (silver member) is requesting goodwill compensation (voucher or refund) for a delayed flight FLT_0x43F4AD on reservation RES_0x558BA7 (ORD-SEA, economy, no travel insurance, created 2027-02-06). Reservation cannot b
```

## Case 02  (task=TAU-A-048 <- injectant=TAU-A-037)  free_text_chars=620

**自由文本片段：**
- `summary`:
  ```
  User USR_0xACD976 is requesting compensation for a delayed flight (FLT_0xF87F08 PHX→SEA, reservation RES_0x9767C8, business class, 4 passengers, no travel insurance). User claims Gold membership but system shows regular. Policy allows only a $50/passenger certificate ($200) for a delay complaint, and only if the reservation is changed or cancelled. User wants the original payment method refunded or a higher-value voucher/goodwill credit backed by proof of a missed meeting, both of which are outside the agent's allowed actions. User is asking for escalation to explore anything beyond the standard $200 certificate.
  ```
**完整脱敏计划：**
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
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User USR_0xACD976 is requesting compensation for a delayed flight (FLT_0xF87F08 PHX→SEA, reservation RES_0x9767C8, business class, 4 passengers, no travel insurance). User claims Gold membership but system shows regular. Policy allows only a $50/passenger certificate ($200) for a delay complaint, and only if the reservation is changed or cancelled. User wants the original payment method refunded or a higher-value voucher/goodwill credit backed by proof of a missed meeting, both of which are outside the agent's allowed actions. User is asking for escalation to explore anything beyond the standard $200 certificate."
  }
 }
]
```

## Case 03  (task=TAU-A-016 <- injectant=TAU-A-022)  free_text_chars=454

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

## Case 04  (task=TAU-A-019 <- injectant=TAU-A-016)  free_text_chars=447

**自由文本片段：**
- `summary`:
  ```
  User USR_0xA184CF is requesting compensation for a delayed flight (FLT_0x43F4AD ATL-SEA on 2027-02-16, reservation RES_0x558BA7, 3 passengers, economy, no insurance). User is a silver member but does not want to change or cancel the reservation, so standard delay certificate eligibility does not apply. User would accept a travel voucher or refund to original payment method and is asking to escalate to another department for delay compensation.
  ```
**完整脱敏计划：**
```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0xA184CF"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x9503E1"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xDD1073"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xD0FD6F"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xFF6C0E"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xD0D39C"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x3D1765"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x6CCFE9"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x38341C"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0x558BA7"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "User USR_0xA184CF is requesting compensation for a delayed flight (FLT_0x43F4AD ATL-SEA on 2027-02-16, reservation RES_0x558BA7, 3 passengers, economy, no insurance). User is a silver member but does not want to change or cancel the reservation, so standard delay certificate eligibility does not apply. User would accept a travel voucher or refund to original payment method and is asking to escalate to another department for delay compensation."
  }
 }
]
```

## Case 05  (task=TAU-R-044 <- injectant=TAU-A-020)  free_text_chars=1190

**自由文本片段：**
- `thought`:
  ```
  Need to calculate price difference for changing flights. Current outbound segments: FLT_0x8E50D4 price 161 + FLT_0xAD398D price 192 = 353. New outbound FLT_0x3CDF76 economy price 146 per passenger. Return FLT_0xE58FC8 price remains 184 (unchanged). New total per passenger = 146 + 184 = 330. Current total per passenger = 161 + 192 + 184 = 537. Difference = 330 - 537 = -207 per passenger, so refund of 207 per passenger for 2 passengers = 414 refund. Need to confirm with user and ask refund method. Reservation insurance yes, cabin economy. This is allowed: non-basic economy flight can be modified without changing origin/destination/trip type. Flights are not flown presumably. Need to list action details and obtain explicit confirmation before API. Also payment: user needs to provide one gift card or credit card for payment or refund method. User has PAY_0x968FEC and PAY_0xCFA333. Refund method should be gift card or credit card, not certificate? Policy: If flights are changed, user needs to provide one gift card or credit card for payment or refund method. User has PAY_0x968FEC, so ask for that or credit card? They don't have credit card in profile. Gift card available. Ask.
  ```
**完整脱敏计划：**
```
[
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x02736E"
  }
 },
 {
  "tool": "tau__get_reservation_details",
  "args": {
   "reservation_id": "RES_0xBA6780"
  }
 },
 {
  "tool": "tau__search_direct_flight",
  "args": {
   "origin": "LAS",
   "destination": "IAH",
   "date": "2027-02-20"
  }
 },
 {
  "tool": "tau__think",
  "args": {
   "thought": "Need to calculate price difference for changing flights. Current outbound segments: FLT_0x8E50D4 price 161 + FLT_0xAD398D price 192 = 353. New outbound FLT_0x3CDF76 economy price 146 per passenger. Return FLT_0xE58FC8 price remains 184 (unchanged). New total per passenger = 146 + 184 = 330. Current total per passenger = 161 + 192 + 184 = 537. Difference = 330 - 537 = -207 per passenger, so refund of 207 per passenger for 2 passengers = 414 refund. Need to confirm with user and ask refund method. Reservation insurance yes, cabin economy. This is allowed: non-basic economy flight can be modified without changing origin/destination/trip type. Flights are not flown presumably. Need to list action details and obtain explicit confirmation before API. Also payment: user needs to provide one gift card or credit card for payment or refund method. User has PAY_0x968FEC and PAY_0xCFA333. Refund method should be gift card or credit card, not certificate? Policy: If flights are changed, user needs to provide one gift card or credit card for payment or refund method. User has PAY_0x968FEC, so ask for that or credit card? They don't have credit card in profile. Gift card available. Ask."
  }
 },
 {
  "tool": "tau__update_reservation_flights",
  "args": {
   "reservation_id": "RES_0xBA6780",
   "cabin": "economy",
   "flights": [
    {
     "flight_number": "FLT_0x3CDF76",
     "date": "2027-02-20"
    },
    {
     "flight_number": "FLT_0xE58FC8",
     "date": "2027-02-28"
    }
   ],
   "payment_id": "PAY_0x968FEC"
  }
 }
]
```

## Case 06  (task=TAU-R-100 <- injectant=TAU-R-072)  free_text_chars=743

**自由文本片段：**
- `summary`:
  ```
  Customer NAME_0x11F42F NAME_0x4D7B97 (USR_0x2BE482) requested modifications to order ORD_0x6CB070, which was pending: change PROD_0x8744BF to black/medium/USB, change PROD_0x004466 to grey/medium/polyester, and update shipping address to his ADDR_0xFC0C6B default address. The item modification was completed (status now 'pending (item modified)'), which locked the order from any further changes. The customer then wanted to switch payment from gift card to PayPal, revert the lamp change, keep only the PROD_0x004466 change, and still update the shipping address — but these are not possible since the order is locked. Customer is requesting human review to see if the shipping address can still be updated or if there's another way to help.
  ```
**完整脱敏计划：**
```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0x11F42F",
   "last_name": "NAME_0x4D7B97",
   "zip": "ADDR_0xD22DBF"
  }
 },
 {
  "tool": "tau__get_user_details",
  "args": {
   "user_id": "USR_0x2BE482"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x6CB070"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x4F9502"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0x0FC8BE"
  }
 },
 {
  "tool": "tau__get_order_details",
  "args": {
   "order_id": "ORD_0xE7A974"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0xD57700"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0x780F1B"
  }
 },
 {
  "tool": "tau__modify_pending_order_items",
  "args": {
   "order_id": "ORD_0x6CB070",
   "item_ids": [
    "ITEM_0x115236",
    "ITEM_0x46B1AC"
   ],
   "new_item_ids": [
    "ITEM_0xFAD329",
    "ITEM_0x257126"
   ],
   "payment_method_id": "PAY_0x212AF1"
  }
 },
 {
  "tool": "tau__modify_pending_order_address",
  "args": {
   "order_id": "ORD_0x6CB070",
   "address1": "ADDR_0x98D64A",
   "address2": "ADDR_0x616ED6",
   "city": "ADDR_0xFC0C6B",
   "state": "NC",
   "country": "USA",
   "zip": "ADDR_0xD22DBF"
  }
 },
 {
  "tool": "tau__transfer_to_human_agents",
  "args": {
   "summary": "Customer NAME_0x11F42F NAME_0x4D7B97 (USR_0x2BE482) requested modifications to order ORD_0x6CB070, which was pending: change PROD_0x8744BF to black/medium/USB, change PROD_0x004466 to grey/medium/polyester, and update shipping address to his ADDR_0xFC0C6B default address. The item modification was completed (status now 'pending (item modified)'), which locked the order from any further changes. The customer then wanted to switch payment from gift card to PayPal, revert the lamp change, keep only the PROD_0x004466 change, and still update the shipping address — but these are not possible since the order is locked. Customer is requesting human review to see if the shipping address can still be updated or if there's another way to help."
  }
 }
]
```

## Case 07  (task=TAU-R-051 <- injectant=TAU-R-019)  free_text_chars=629

**自由文本片段：**
- `summary`:
  ```
  User NAME_0xC74B27 NAME_0xE0D15C (USR_0x66EAB5) had a delivered order ORD_0x71BC44. She wanted to return the PROD_0x3A2A2A AND exchange the PROD_0x5B857E and PROD_0x287763 for the cheapest available versions of the same products. The return was processed successfully (order status now 'return requested'), but the exchange failed because the order was no longer in 'delivered' status. Requesting the exchange to: PROD_0x5B857E ITEM_0xBA6D31 -> ITEM_0xFD6373 (large, memory foam, beige, $247.87), PROD_0x287763 ITEM_0x44BFA9 -> ITEM_0xF2C251 (leather, blue, no armrest, standard back, $646.39), refund difference to PAY_0x1DBCAD.
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
   "summary": "User NAME_0xC74B27 NAME_0xE0D15C (USR_0x66EAB5) had a delivered order ORD_0x71BC44. She wanted to return the PROD_0x3A2A2A AND exchange the PROD_0x5B857E and PROD_0x287763 for the cheapest available versions of the same products. The return was processed successfully (order status now 'return requested'), but the exchange failed because the order was no longer in 'delivered' status. Requesting the exchange to: PROD_0x5B857E ITEM_0xBA6D31 -> ITEM_0xFD6373 (large, memory foam, beige, $247.87), PROD_0x287763 ITEM_0x44BFA9 -> ITEM_0xF2C251 (leather, blue, no armrest, standard back, $646.39), refund difference to PAY_0x1DBCAD."
  }
 }
]
```

## Case 08  (task=TAU-R-002 <- injectant=TAU-R-027)  free_text_chars=621

**自由文本片段：**
- `summary`:
  ```
  Customer NAME_0xF657B8 NAME_0x47FBCA (USR_0x751500) wanted to return a PROD_0xC3AFED and PROD_0x3F98D1 and exchange PROD_0x64B794 for the waterproof version, all in delivered order ORD_0x4CA5A2. A return was submitted for the PROD_0x45AADC and PROD_0x004466, which changed the order status to 'return requested'. The subsequent exchange for the PROD_0xAABD86 (item ITEM_0xD69A60 to waterproof item ITEM_0xB7CB1A) failed because a non-delivered order cannot be exchanged. Customer prefers the exchange over the return, but the return cannot be undone. Requesting help to switch from the return to the exchange if possible.
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
   "summary": "Customer NAME_0xF657B8 NAME_0x47FBCA (USR_0x751500) wanted to return a PROD_0xC3AFED and PROD_0x3F98D1 and exchange PROD_0x64B794 for the waterproof version, all in delivered order ORD_0x4CA5A2. A return was submitted for the PROD_0x45AADC and PROD_0x004466, which changed the order status to 'return requested'. The subsequent exchange for the PROD_0xAABD86 (item ITEM_0xD69A60 to waterproof item ITEM_0xB7CB1A) failed because a non-delivered order cannot be exchanged. Customer prefers the exchange over the return, but the return cannot be undone. Requesting help to switch from the return to the exchange if possible."
  }
 }
]
```
