# P5a.20 便签 2 实施证据 — 第 0 步线束保真初筛器

**commit 内容**：新增 `scripts/harness_screen.py`；`sidecar.rpc_list_tasks` 增 hash 字段；`updater` 加访问控制 denylist。
**性质**：机器只产候选+理由，**人审签字后方为约束清单**（MR-7）。不附 PASS/FAIL 判定（防锚定）。

## 1. 交付

| 文件 | 作用 |
|---|---|
| `scripts/harness_screen.py` | C1–C5 初筛器 |
| `backend/requirements/adapters/tau/sidecar.py` | `rpc_list_tasks` 增 `instruction_sha256_16` / `instruction_chars` |
| `backend/monitor/updater.py` | `FORBIDDEN_INPUT_DIRS=(".agent/local",)` + `_assert_allowed_input` |
| `.agent/reports/p5a20-screen.json` | 全量 e4/e5 初筛结果（135 任务） |
| `.agent/reports/p5a20-watchlist.*` | 关注任务清单（见另一证据） |

运行：
```bash
PYTHONPATH=.agent/vendor/tau-bench .agent/venv/tau/bin/python scripts/harness_screen.py --epoch 4 5
```

## 2. 全量结果（e4↔e5，135 任务，耗时 4m）

| 检查 | 命中任务数 | 置信 | 说明 |
|---|---|---|---|
| C1 GT 重放确定性 | 0 | high | 两次 GT 重放 DB hash 恒等 |
| **C4 GT 前提不可达/自相矛盾** | **15** | high | GT 动作本身报 Error |
| C2 instruction⇄GT 商品集 | 64 | **low（需人审）** | 启发式，FP 率偏高 |
| C3 模拟器⇄GT | 7 | low | 日期/航点/乘客数矛盾 |
| C5 跨 epoch arm 不一致 | 52 | high | Thompson 漂移（≈39% 任务对丧失臂级可比性） |
| —— 候选隔离总数 | **83 / 135** | | |

## 3. C4 名单（真实 GT 缺陷，高风险）

GT 动作 replay 直接报错 → 该任务**按 GT 自身都不可能赢**：

| 出现动作 | 报错 | 任务 |
|---|---|---|
| `get_product_details` | `product not found` | R-002, R-003, R-004, R-021 |
| `return_delivered_order_items` | `payment method should be either the original payment method or a gift card` | R-012, R-013 |
| `find_user_id_by_email` | `user not found` | R-035, R-036, R-038, R-055 |
| `find_user_id_by_name_zip` | `user not found` | R-039, R-067, R-068 |
| `exchange_delivered_order_items` | `non-delivered order cannot be exchanged` | R-064, R-106 |

> 这 15 条属**任务定义级缺陷**，与 worker/POLICY 无关；建议直接进隔离仓（另见 R-105：jigsaw⊄GT）。

## 4. 红线处理

- **初筛器不落 instruction 明文**：`env.user` 置 `StubUser`（避免 τ HUMAN 策略回显指令到 stdout）；输出只含 `instruction_sha256_16`。
- **RPC 收口（部分）**：`rpc_list_tasks` 不再只是裸明文，增 hash 派生字段；**移除明文需把签名计算迁到 sidecar（列为后续设计项）**，本轮为不破坏 ingest 采用加性改法。
- **updater 访问控制**：显式 denylist `.agent/local`，纵深防御。

## 5. 已知局限（需人审兜底）

- C2 用"退货语境句 + 商品名词元"启发式，**FP 明显**（如把 "received with the vacuum cleaner" 误判）。64 条须逐条人审，不可直接当约束。
- C3 仅覆盖日期/航点/乘客收窄，漏掉纯人名/纯语义矛盾（如 A-008 "just Mohamed" 已覆盖，但更隐晦的漏）。
- C4/C1/C5 为确定性，可直接采信。

## 6. 建议

1. 对 C4 的 15 条 + 既有三案，合并为**隔离集 v1 候选**，交用户抽检签字。
2. C2 的 64 条降级为"待人工 triage"，不参与机器约束。
3. 用隔离集 v1 在保留子集上重算 e3/e4/e5 聚合与 SC（P5a.19 §二恢复路径）。
