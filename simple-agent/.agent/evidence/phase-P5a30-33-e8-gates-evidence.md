# P5a.30–33 e8 工单 A/C/D/E 证据

**依据**：a30 §二.3/§5.2、a31、a32 §一、a33 §一/§二/§四。全部零 token。

## A. 伪真值脱敏库（P5a.33 §一）
- `backend/requirements/adapters/tau/deident.py`：类型前缀伪真值 `RES_/FLT_/ORD_/USR_/PAY_/ITEM_/NAME_ + _0x<hex>`；
  日期**单一固定偏移**（+1007 天，保先后/差值）；金额同一比例（×1.37，保序）；**注入物内共指一致**；`seed=e8-20260929`。
  自由文本里的嵌入实体亦**就地**替换（regex scrub）。
- `scripts/e8_build_deident.py --epoch 7`：
  - distinct τ 计划 **443**（非 τ 10 个跳过）；
  - **lint 三检全绿**：无残余真值 ∧ JSON 合法/工具名合法 ∧ 假值 DB 非成员；
  - 映射表 → `.agent/local/e8-deident-mapping.json`（**未跟踪**，`gitignore` 命中）；证据只记 `mapping_sha256=e2e819dc…` 与 seed。
- 产物：`e8-deid-snapshot.json`（443 条脱敏计划）、`e8-deid-lint.json`。

## C. 三臂臂内选择器（P5a.30 §5.2 / a33 §二）
- `monitor/precedent_select.py: select_for_arm`：direct→无；sibling=**同域同族**→（空则）**同域近族**（工具类型 Jaccard≥0.6）→`ineligible`；unrelated=**异族形态匹配**（长度差优先、类型 Jaccard 次之）。**k=3 仅臂内；不跨臂/跨域递补。**

## D/E. 矩阵冻结 + 达标线（P5a.30 §二.3/§5.2、a33 §二）
- `scripts/e8_freeze.py`：臂=**纯随机 1/3**（`blake2b(seed|req_id)%3`）——**不受配额影响**（驳回再分配机制）。
- **达标线（all_pass=true）**：

| 门 | 值 | 阈值 | 结果 |
|---|---|---|---|
| top-1 注入物覆盖率 | 3.4% | ≤15% | ✅ |
| distinct 注入物 | 63 | ≥20 | ✅ |
| 同域覆盖率（sibling 臂） | **97.8%** | ≥60% | ✅ |
| 三臂任务数 | 46/45/44 | ~1/3 | ✅ |

> 注：a31 §三 预警"零售同域覆盖 <60%"**未发生**——因用**全库 443 条**（非 e7 的 13 条）作候选池，同域同/近族足够；这是破垄断（全库+随机+k=3）的直接效果。

- 形态平衡表（长度）：sibling n=44 mean 7.0 / unrelated n=44 mean 4.8（无精确匹配时取最近邻；差异待 e8 前评估，是否需收紧 `±2`）。产物 `e8-matrix-freeze.json`。

## 结论
A/C/D/E 完成且**达标线全过** → 不触发"回报仲裁"条款；可继续 B（worker 三臂接线）、F（CopyGuard）、G（沙盒）。
