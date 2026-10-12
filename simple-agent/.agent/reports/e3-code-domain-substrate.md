# E3 代码域基板立项（P5a.44 §三.3）

**定位**：e9 部署资产（τ 锁序拦截器）完成后第一优先。用**已建成、已验证**的多臂 harness 在**代码域**验证"域标签 `validated_domain` + 死因谓词资产"的可移植性。

## 一、域标签落地（`validated_domain`）
- 溯源层 `backend/monitor/provenance.py`：资产记录 = `asset×validated_domain×credit_level×last_revalidated×evidence`。
- 首个登记：`lock_order_v1`，`validated_domain=tau`，`credit_level=T1_candidate`，`death_cause=lock_order`，证据 = a28 回测(0/12)+B-2 电池(7/7)。
- 规则：**未过验证器的资产不登记**；`validator=金丝雀电池`，非 epoch。

## 二、harness 域无关化（DomainPack）
`backend/domains/`：
- `DomainPack{name, mutating_tools, transfer_tool, read_prefixes, entity_field_class, interceptor_rules, lock_scope_key}`；
- `tau` 包（已落地）；`code` 包（E3 stub，`lock_scope_key=path`，`interceptor_rules=[]` 待普查）；
- 复用面（逐字复用，不重写）：任务级随机化、矩阵冻结、形态对齐、簇 wild bootstrap、CopyGuard、运行表 schema、ITT、脱敏分类法管线。

## 三、E3 首个交付物（提案）
1. **代码域死因普查**：在代码域任务轨迹上（写/改/删/执行类）做失败模式普查，产出**确定性谓词候选**（对标 τ 锁序）；`interceptor_rules` 逐条过 B-2 式金丝雀电池后登记 `validated_domain=code`。
2. **代码域任务集**：最小 30–50 条、含长程多步（对标 R-105 类），作为 E3 的 L2/L1 harness 输入。
3. **脱敏/实体类**：`path/file_id/commit_sha/symbol`（taxonomy 已在 code 包 stub 中占位）。

## 四、成功判据
- 至少 **1 条**代码域资产经金丝雀电池验证并登记（`validated_domain=code`）；
- harness 在代码域一轮 L2/L1 产出**语义明确**的读数（排=非排零可判）；
- 不新增架构层（发热门约束：部署资产数只增不减）。

## 五、非目标
- 不做规划 agent（P5a.45 选项 A 否决）；
- 不做 skill 触发（确定性触发优先，P5a.25）；
- 不在 τ 域继续 epoch 级燃烧（发热门）。

## 六、自检
`scripts/e3_substrate_check.py` → 域包 tau/code 加载 ✓、资产 `lock_order_v1` 登记（`validated_domain=tau`）✓、拦截器谓词与域包规则一致 ✓。
