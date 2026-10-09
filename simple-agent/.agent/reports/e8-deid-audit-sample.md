# e8 脱敏库人工抽检样本（10 例；rubric 见 P5a.37 §三）

检查：① I-III 全类型前缀伪真值 ② 同实体同假值/不同实体不同值 ③ 日期数值保序 ④ 机器（已过）⑤ IV 裸值仅限封闭词表

## Case 01  injectant=?
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

## Case 02  injectant=?
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

## Case 03  injectant=?
```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0x11F42F",
   "last_name": "NAME_0xD7AF8D",
   "zip": "ADDR_0x08ACF1"
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

## Case 04  injectant=?
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

## Case 05  injectant=?
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

## Case 06  injectant=?
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

## Case 07  injectant=?
```
[
 {
  "tool": "tau__find_user_id_by_email",
  "args": {
   "email": "EMAIL_0x04C732"
  }
 },
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0xA1D11C",
   "last_name": "NAME_0xCA6CEA",
   "zip": "ADDR_0x1C0778"
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
   "product_id": "PROD_0x4AEFE5"
  }
 },
 {
  "tool": "tau__get_product_details",
  "args": {
   "product_id": "PROD_0x682FE4"
  }
 }
]
```

## Case 08  injectant=?
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
   "reservation_id": "RES_0x070F03"
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

## Case 09  injectant=?
```
[
 {
  "tool": "tau__find_user_id_by_name_zip",
  "args": {
   "first_name": "NAME_0xB87484",
   "last_name": "NAME_0x5F3321",
   "zip": "ADDR_0x1DAFB7"
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
   "address1": "ADDR_0xEA7F96",
   "address2": "ADDR_0x7C5CAB",
   "city": "ADDR_0x0556F9",
   "state": "TX",
   "country": "USA",
   "zip": "ADDR_0x1DAFB7"
  }
 }
]
```

## Case 10  injectant=?
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
