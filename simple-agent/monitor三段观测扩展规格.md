# monitor 三段观测扩展规格（实施任务书增补）

> 定位：插入《simple-agent判断力机制实施任务书》，A 段并入 P2，B/C 段并入 P3。
> 目标：monitor 从"只看单 agent 步数/token"升级为**三面观测**——执行面（每个命令及效果+循环反馈）、规划面（细粒度 plan 的产生过程）、切分面（规划师粗粒度拆分的质量）。
> 原则不变：三面数据全部落同一个 trace.db 的 span 树，用 parent_span_id 串粒度，不建第二套存储。

---

## A. 执行面：每个命令及效果 + 循环反馈的有效性

### A.1 效果捕获（改 `tools/registry.py`）

现在 E 层 span 只存截断 output，看不到"这一锤子下去世界变了什么"。改造：

```python
def _manifest(work_dir: str) -> dict:
    """{相对路径: md5前8位}，跳过 .git 与 >10MB 文件"""
    
def execute(self, call: ToolCall) -> ToolResult:
    before = _manifest(self.work_dir)
    ...原有执行...
    after = _manifest(self.work_dir)
    effect = {
        "created":  sorted(set(after) - set(before))[:50],
        "modified": sorted(p for p in after if p in before and after[p] != before[p])[:50],
        "deleted":  sorted(set(before) - set(after))[:50],
    }
    exec_span.attributes["effect_diff"] = effect
```

`tools/shell.py` 的 span 额外记 `exit_code / stdout_tail(500字) / stderr_tail(500字)`。

**验收**：执行任务"创建 a.txt 并修改 b.txt"，`SELECT json_extract(attributes,'$.effect_diff') FROM spans WHERE layer='E'` 返回精确的 created/modified 清单。

### A.2 循环反馈链路（配合 P2 的 `monitor/guard.py`）

熔断不只是"停"，还要回答"**反馈给了之后它改没改**"：

- guard 触发时除 `circuit_break` span 外，把**注入给 agent 的纠偏消息文本**记录为 span：`layer="G", type="feedback_injected", attributes={guard_span_id, msg_hash}`；
- `worker.py` 记录反馈后的下一个工具调用，写 span：`type="feedback_response", parent_span_id=<feedback_injected 的 id>, attributes={corrected: bool}`；
- `corrected` 判定（确定性规则）：下一次调用的签名（工具+参数哈希）**不同于**导致熔断的重复签名，或反馈后 3 步内有断言新通过。

**验收**：构造死循环任务 → 熔断注入反馈 → 查询 `feedback_response.corrected` 有值；统计接口能回答"反馈纠正率"（这是衡量纠偏消息质量的核心指标，纠偏消息本身以后也是要进化的资产）。

---

## B. 规划面：细粒度 plan 的产生过程全程留痕

规划器（任务书 P3 之后落地）每次产规划，写**一条 L 层 plan span**：

```python
# monitor/plan_observer.py（新建）
def record_plan(trace_id, req_id, plan_json, planner_model, prompt_version, usage, latency_ms):
    """layer='L', type='plan', attributes={
        plan_id, req_id, planner_model, prompt_version,
        tokens, latency_ms,
        node_count, max_depth,          # 从 plan_json 算
        schema_valid,                   # DAG 无环/依赖可解/agent 名存在
        owns_disjoint,                  # 静态校验 owns 不相交
    }"""
```

执行侧联动：`worker.py` 接受 `plan_node_id` 参数，**该节点产生的所有 span 都挂这个属性**——plan 与 execution 的映射就此打通。

**验收**：`SELECT * FROM spans WHERE type='plan'` 能拿到结构化摘要；任意执行 span 能反查所属 plan 节点。

---

## C. 切分面：规划师的"粗粒度切分质量"打分

不是新埋点，是**用 A/B 的数据算出来的派生指标**。`monitor/plan_observer.py`：

```python
def decomposition_report(plan_id) -> dict:
    return {
        "node_success_rate": ...,    # 各节点 verdict 通过率
        "avg_retries": ...,          # 平均重试
        "rework_edges": ...,         # 下游失败归因到上游产物的次数（handoff 缺陷率）
        "owns_conflicts": ...,       # ★ 关键：并行节点 effect_diff 的实际文件交集数
                                     #   （计划声称不相交 vs 实际撞车——规划师的谎言检测器）
        "token_cv": ...,             # 各节点 token 变异系数（粒度均匀度：悬殊说明切分失衡）
        "critical_path": ...,        # DAG 关键路径长度（串行瓶颈）
        "replan_count": ...,         # 同一 req 被重规划次数（切分债）
    }
```

结果写 span：`layer="O", type="decomposition_eval", attributes={...}`。

**这是规划师的"绩效表"**：按 `(planner_model, prompt_version)` 聚合这些指标，就是 P3 路由表给"规划器提示词版本"分 arm 的奖励信号——规划师自己也在被路由和学习。

**验收**：构造一个故意 owns 重叠的 plan，两个并行节点改同一文件 → `owns_conflicts ≥ 1` 且能被 SQL 查出。

---

## 三面合一的查询视图

`monitor/report.py` 的 `generate_full_report` 增加三节：

```json
{"execution_health": {"feedback_correction_rate": ..., "tool_effect_stats": ...},
 "planning_health":  {"plan_schema_valid_rate": ..., "avg_node_count": ...},
 "decomposition_health": {"owns_conflict_rate": ..., "rework_edge_rate": ..., "planner_leaderboard": [...]}}
```

monitor.py 轮询日志加一行：`PLAN | id={} | nodes={} | success={} | conflicts={} | rework={}`。

## 依赖与排期

| 段 | 依赖 | 排期并入 |
|---|---|---|
| A | 无新依赖，改现有两个文件 | P2（与 guard 同批，1 天内） |
| B | 需要规划器存在；schema 先行，规划器落地即自动出数 | P3 |
| C | 依赖 A 的 effect_diff + B 的 plan span | P3 末～P4 初 |

**一句话**：A 让 monitor 看见"锤子与钉子"，B 让它看见"图纸怎么画的"，C 让它给"图纸设计师"打绩效——三面数据进同一棵 span 树，Shapley 归因从此能区分"工人不行、图纸不行、还是派活的不行"。
