# 生成器官设计（P5a.58）— 五环 + 影子出生路径

**状态**：MVP 建成（零 token）；待命（τ 无新尸体，空转正常）。

## 一、五环管线（`backend/monitor/organ.py: Pipeline`）
| 环 | 现状 | 器官化 | MVP |
|---|---|---|---|
| 开采 | `scripts/p5a36_failure_mine.py`（自动） | 触发化（批次落盘即跑） | `ring_mine` 委托 |
| 分诊 | 五类预分类（半自动） | **全机检**：可观测性 + 死因归类 + 可拦截性 | `ring_triage` |
| 谓词起草 | opencode 手工 | **LLM 起草器**（尸体簇→谓词规格+干预语义）——**唯一 LLM 格子** | `ring_draft`（无 LLM 时模板） |
| 金丝雀 | 手工建电池 | 半自动：死亡案例→阳性探针；合法形状库→阴性对照 | `ring_canary` |
| 认证 | C-1（自动） | 不变 | `ring_certify` |

## 二、出生路径：影子模式（shadow）
- 新资产一律先出生为 **`status=shadow`**：拦截器在线运行但**只记日志不否决**（"我本会拦这一步"）。
- **影子毕业**：累计 **≥10 次影子点火 ∧ 零影子误伤**（对最终 PASS 的 run 点火=误伤）→ 自动转 `active`。
- **任一影子误伤** → 自动降级 `pending_revalidation`（回炉）+ 事件上报。
- 实现：`provenance.shadow_event()`（B-3 记 `shadow_firings`/`shadow_misfires`）；`organ.shadow_fire()`。
- 三级验证桥：**金丝雀（笼里对）→ 追溯审计（历史里对）→ 影子期（眼前这条 run 里对）**，第三级 token 成本为零。

## 三、宪法级自治边界（`organ.assert_in_scope` 强制）
器官**永不**：① 触碰奖励函数/验证器；② 编辑测试与金丝雀电池；③ 自行变更 taxonomy/值分类法/死因分类法；④ 让缺可观测性证明者进影子；⑤ 让无影子证据者转正；⑥ 直接 commit/push（产出入**证据域**，不入**提交域**）。
- 机检墙：`FORBIDDEN_PATH`（`scoring.py/eval_loop.py/e3_executor/e3_generator/*_battery.py/canary/hidden_test/reward`）→ 命中即 `PermissionError`。
- 出生门：`can_birth()` 强制 `observability_proof` 等必填（§三.4）。

## 四、B-3 schema（b3-v3 增补）
- status 增 `shadow`；字段 `shadow_firings` / `shadow_misfires`；`SHADOW_GRADUATION={min_firings:10,max_misfires:0}`。

## 五、建造纪律（P5a.58 §四）
- **MVP 即止**；空转待命正常（消防栓）；建造全程零模型 token（LLM 起草器联调除外，记小账）。

## 六、自检（零 token）
`scripts/organ_selftest.py` → `organ-selftest.json`：**all_pass**——宪法墙拒 3 类路径、出生门拒缺证明、出生为 shadow、10 FAIL 点火自动毕业、1 误伤自动回炉；真实资产库未被污染。
