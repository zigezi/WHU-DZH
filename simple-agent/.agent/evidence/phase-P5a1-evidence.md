# Phase 5a.1 证据 — DialogueDriver 多轮回路

- 生成时间：2026-09-11T18:03:04+08:00  分支：simple-agent @ 78ff6c8

## 1. τ 任务端到端（airline task 0, trace=985905c8-6e64-4b9d-b50e-7169923cc045），dialogue_turn span 交替

```
$ sqlite3 -readonly logs/trace.db "SELECT turn,role,tokens,substr(text,1,50) FROM spans WHERE trace_id='985905c8-6e64-4b9d-b50e-7169923cc045' AND type='dialogue_turn' ORDER BY start_time"
1|user|366|Hi, I’d like to book a one-way flight from New Yor
2|assistant|3870|I can help with that. First, could you please prov
3|user|765|Sure, my user ID is mia_li_3668.
4|assistant|3939|Thanks. Could you also tell me:

1. What cabin cla
5|user|1250|Economy, please. Just one passenger, and I’d prefe
6|assistant|4001|I do need the passenger details for the booking, i
7|user|1798|I’m the only passenger, my name is Mia Li, and my 
8|assistant|4061|I understand, but I do need the passenger’s date o
9|user|2403|I don’t want to provide my date of birth. If it’s 
10|assistant|5029|I found direct flights available from New York (JF
11|user|3126|Neither, because I don’t want to fly before 11am E
12|assistant|10807|There are no direct New York–Seattle flights depar
13|user|4205|Please book the lowest-price one-stop option depar
14|assistant|10998|Let me confirm the lowest-price option that depart
15|user|5507|Yes, book that itinerary. No insurance. I have 3 c
16|assistant|11244|A reservation can use at most one travel certifica
17|user|7014|Yes, please proceed with this booking.
18|assistant|11730|The booking couldn’t be completed because **flight
19|user|8668|Yes, book that option instead. No insurance, 3 che
20|assistant|11913|Let me confirm the revised booking details:

- **U
21|user|10491|Yes, please proceed.
```

- turn 0 由 driver 用 hidden instruction 生成的真实首轮用户消息（非占位开场白）✅
- 任务因 max_tokens=100000 预算被 guard 熔断（g_halted），属真实成本信号

## 2. 回归：老单轮 REQ-001 trace 结构不变（trace=93350b99-06b4-4a5d-b7d4-8f73b86fb3a4）

```
$ sqlite3 ... SELECT layer,type,count(*) ... WHERE trace_id='93350b99-06b4-4a5d-b7d4-8f73b86fb3a4'
C|llm_call|3
E|sandbox_exec|2
L|abstain_check|1
L|plan|1
L|step|3
L|task|1
O|observability|1
T|tool_call|2
V|acceptance_check|4
V|progress|2
$ tau 专属 span（dialogue_turn/tool_scope）计数（want 0）
0
$ E 层 span 均含 plan_node_id
write_file|n0
read_file|n1
```

- 与 v2.3 P3 证据一致：L(task/plan/step/abstain_check)+C+T+E+V+O，E 层 plan_node_id=n0/n1 ✅
