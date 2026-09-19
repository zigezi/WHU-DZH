# Phase P5a.11 证据 — Part 1 机制指纹 + 机制存在性验证

- 生成时间：2026-09-16T10:59:35+08:00  分支：simple-agent @ 482b629
- 范围：仅 Part 1（零成本指纹 + 金丝雀/guard 单元测试）。**Part 2（epoch-5）未启动**，按裁决顺序等待。

## 0. 冻结检查（Part 2 前置）

```
$ git diff --stat 482b629..HEAD -- backend/
(空 = backend 零 diff)
$ sqlite3 ... policy_inject policy_id distinct
174e4c5dfd45
```

## 1. Part 1 四条机制指纹（epoch-3 vs epoch-4）

```
=== Part 1 机制指纹（epoch-3 vs epoch-4）===
tasks: e3=135 e4=135
FP-4 e3: n=135 p90=128,048 p99=204,794 max=271,002 >150k=8
FP-4 e4: n=135 p90=122,837 p99=174,967 max=206,782 >150k=5
FP-1 e3: assistant(RESPOND) turns=834 pre-first-toolcall(确认型)=147 avg_turns/task=13.4
FP-1 e4: assistant(RESPOND) turns=794 pre-first-toolcall(确认型)=143 avg_turns/task=12.8
FP-5 e3: circuit_break=0 feedback_injected=0 feedback_response=0 same-tool-fail-run>=3=0
FP-5 e4: circuit_break=0 feedback_injected=1 feedback_response=1 same-tool-fail-run>=3=0
FP-2 e3: tool_calls=1011 unfounded=147 ratio=14.5%
FP-2 e4: tool_calls=1036 unfounded=144 ratio=13.9%
   sample: trace=0367c73b tool=tau__get_order_details unfounded_args=["order_id='#W7209932'"]
   sample: trace=03e78b32 tool=tau__transfer_to_human_agents unfounded_args=['summary=\'User: Yusuf Li (user_id: yusuf_li_7255). Order #W6750959 (was pending) — user requested (1) modifying the Bluetooth Speaker to the green version, which succeeded (item 3254583681 → 9440686670, $3.76 refunded to paypal_8080730), and (2) changing the shipping address to his NYC address from his other order #W3407479 (476 Maple Drive, Suite 432, New York, NY 10093, USA). The address change FAILED because the item modification locked the order (status now "pending (item modified)"), so it can no lon...(+207)\'']
   sample: trace=09fc3608 tool=tau__get_reservation_details unfounded_args=["reservation_id='GXWCPN'"]
```

### 指纹判读

- **FP-4（P4 结束即止）✅ 支持**：p90 128k→123k、p99 205k→175k、max 271k→207k、>150k 任务 8→5，尾部收窄。
- **FP-1（P1 修正版）🔶 部分支持**：RESPOND 轮 834→794、平均轮数 13.4→12.8（不升）；但"首个 tool_call 前的 assistant 轮"147→143，**未≈0**。该启发式把"缺信息时的合法澄清提问"也算进来了（τ 任务常需先向用户问参数），故不能证明 P1 的"确认型单独轮≈0"；属启发式口径问题，如实标注。
- **FP-5（P5 失败换策略）⚠️ 数据不足**：两 epoch `circuit_break=0`、`same-tool-fail-run>=3=0`；e4 仅 `feedback_injected=1/feedback_response=1`。**guard 熔断在 τ 任务里几乎不触发**，本指纹给不出有效读数（不硬凑）。
- **FP-2（P2 不臆造）🔶 弱信号/高误报**：unfounded 占比 14.5%→13.9%（微降）。3 条人工抽查全部为**误报**：
  1. `order_id='#W7209932'`：值应来自先前工具返回，启发式因格式/截断未匹配到；
  2. `transfer_to_human_agents summary=...`：是模型**生成的摘要文本**，非"臆造事实"；
  3. `reservation_id='GXWCPN'`：应来自 `get_user_details` 返回，同上误报。
  → FP-2 比率被误报主导，**不作为可靠信号**。

## 2. 机制存在性验证（金丝雀 + guard 单元测试）

```
=== guard 单元测试（确定性，无 LLM）===
same tool+args+error x3 -> decisions=['PASS', 'PARTIAL', 'HALT'] (期望 PASS/PARTIAL/HALT)
different args -> ['PASS', 'PASS'] (期望 PASS/PASS，不误熔断)

=== 金丝雀任务（真实 LLM，假工具永远报错）===
  step0: canary_fetch args={'key': 'alpha'} -> guard=PASS
  step1: final text = "The tool call failed. Here's the report:\n\n**Result: Unable to retrieve the value for key `'alpha'`.*"
  总工具调用=1 相同签名重复=0 guard_HALT=False tokens=906 策略变化=False

=== 金丝雀·强制重试（验证 guard HALT 分支）===
  step0: call#1 args={'key': 'alpha'} -> guard=PASS
  step1: call#2 args={'key': 'alpha'} -> guard=PARTIAL
  step2: model stopped (no tool call)
  总工具调用=2 guard_HALT=False tokens=1920

=== 结论 ===
- guard 状态机存在且工作: True
- 金丝雀(自然): {'calls': 1, 'repeats': 0, 'halted': False, 'tokens': 906}
- 金丝雀(强制重试): {'calls': 2, 'halted': False, 'tokens': 1920}
- 定位：机制存在性验证；不得引用为 P5 提升通过率的证据
```

### 结论（机制存在性，非通过率证据）

- **guard 状态机存在且工作 ✅**：相同 tool+args+error 连打 3 次 → PASS/PARTIAL/HALT；换参数不误熔断。
- **金丝雀（自然）**：假工具永久报错，模型**调用 1 次即放弃**（改策略/结束），相同签名重复=0，guard 未触发。
- **金丝雀（强制重试）**：模型重复到第 2 次即收到 PARTIAL 纠偏反馈，随后**停止**（未第 3 次），guard 仍未触发。
- **综合**：机制（熔断+纠偏）**存在且工作**；但 DeepSeek 在失败时**会主动换策略/停止**，使 guard 的 no-progress HALT 在实践中几乎不触发——这解释了 FP-5 的 circuit_break=0。
- ⚠️ **定位声明**：以上两项是"机制存在性验证"，**不得**被引用为"P5 提升通过率"的证据。
