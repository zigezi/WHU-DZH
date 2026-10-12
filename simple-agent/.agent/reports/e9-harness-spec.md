# 多臂试验 harness 规格（域无关，E3 复用储备）— P5a.45 §三.3

> 收割已建成、已验证的试验设施；不新增架构。E3 代码域原样复用。

## 组件与接口
1. **任务级随机化**：`router.choose_measurement(task_id, arms)` = `blake2b(MODEL:task_id) % len(arms)`；确定性、不可被配额影响（P5a.33 随机化保卫）。
2. **矩阵冻结**：`scripts/e8_freeze.py` 产出 `{matrix_hash, arms, matrix[task->arm,injectant,deid_hash], gates, ledger, form_balance}`；运行期间冻结，改配置=作废。
3. **形态对齐**：长度分箱(1-3/4-6/7-10/11+)×结尾动作三类；两臂逐箱/逐类差≤10pp、均值差≤1.0；一发成稿（禁 reshuffle-until-pretty）。
4. **簇稳健推断**：family 级 wild bootstrap 5000×，主终点判据=CI 排零；固定 pp 判带作废。
5. **CopyGuard**：结果感知（值进 args ∧ 未经先前工具结果）；标记+隔离，**永不改 reward**。
6. **运行表 schema**：`{task_id, req_id, arm, injectant, deid_hash, verdict, tokens}`。
7. **ITT**：assigned=analyzed；ineligible 留分母。
8. **脱敏管线**：分类法注册表（I-IV）+ DB 全量字典 + 伪真值 + 机器④（文档内可解释性）。

## 运行配方
```
freeze_precedents --epoch N            # 先例快照冻结
e8_build_deident --epoch N             # 脱敏库 + lint
e8_freeze --epoch N --seed ...         # 矩阵冻结 + 达标线
ROUTER_MODE=<mode> SA_EPOCH=N backend; tau_sidecar start
eval_loop --epoch N --tau-only --split train --tag tau-
e8_analysis  /  e7_copyguard_audit     # 判读
```
## 域无关化清单（E3 迁移时替换）
- 任务/工具/实体字典 → 目标域；
- 脱敏分类法注册表 → 目标域实体类；
- 拦截器谓词 → 目标域死因谓词（见 e9 拦截器模式：确定性 + 执行前 + once-per-key 状态位）。
其余（随机化/冻结/bootstrap/CopyGuard/运行表/ITT）**逐字复用**。
