# B-3 溯源层 schema（P5a.30 B-3 / P5a.54）

**载体**：`backend/monitor/provenance.py` → `.agent/reports/assets.json`（tracked；规则为 L2，非敏感）。
**版本**：`schema_version = b3-v2`（P5a.56：加 `field_validated` 信用级、`revoke`、`observability_proof`）。

## 资产记录字段
| 字段 | 必填 | 说明 |
|---|---|---|
| `asset_id` | ✔ | 唯一标识（如 `lock_order_v1`） |
| `type` | ✔ | ∈ {interceptor_rule, prompt_patch, threshold_patch, precedent_update} |
| `text` | | 资产规则文本（L2） |
| `trigger` | | 确定性点火规则 |
| `validated_domain` | ✔ | 域标签（τ / code …）——跨域复用须再验证（域标签铁律） |
| `death_cause` | | 死因（lock_order / repeat_failure / …） |
| `credit_level` | ✔ | ∈ {T1_candidate, **field_validated**, T1, T2, T3} |
| `status` | ✔ | active / dormant / pending_revalidation |
| `evidence` | ✔ | 证据串（金丝雀电池 + C-1 + 回测 + firing-audit …） |
| `observability_proof` | ✔(新) | P5a.56 出生要件：谓词点火条件须可由 args/可观测状态确定性计算 |
| `status`(revoked) | | `revoke()` 置 status=revoked + reason + knowledge_moved_to |
| `domain_pack` / `rule_id` | | 与 `backend/domains/` 的域包关联 |
| `created_at` | 自动 | |
| `last_revalidated` | 自动 | 最近复验时间（衰减管理触发用） |
| `revalidation_log` | 自动 | [{at, evidence, result}]；非 pass → status=pending_revalidation |
| `schema_version` | 自动 | b3-v1 |

## 校验
`validate_asset(rec)` 返回缺失/非法字段清单；`register_asset` 强制校验（非法即拒）。

## 与其它册子
- 负结果 → `.agent/reports/negative-results.md`（不同册：负结果 = 被杀路线，非资产）；
- 负先例（L1.5）→ `negative_precedents` 表（**警告通道**，独立于注入层与溯源层）。
