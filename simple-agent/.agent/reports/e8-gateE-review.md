# E 门审查材料（P5a.30–41）

> 用途：E 门 = e8 矩阵冻结审查。审完签 E 门 → 等 e8 运行令。

## 1. 冻结矩阵与达标线
- seed=`e8-20260929` k=3 near_jaccard=0.6
- 臂任务数：{'direct': 46, 'sibling': 45, 'unrelated': 44}

| 达标线 | 值 | 阈值 | 结果 |
|---|---|---|---|
| top-1 覆盖率 | 0.034 | ≤0.15 | OK |
| distinct | 60 | ≥20 | OK |
| 同域覆盖率 | 0.956 | ≥0.60 | OK |
| all_pass | True | — | OK |

## 2. D3 注入池准入（P5a.40 §二）
- 按源 run verdict=PASS 过滤：剔除 **185** 个非 PASS 沉积；过滤后 distinct 60 / 三臂 {'direct': 46, 'sibling': 45, 'unrelated': 44}。

## 3. 提取保真机检（P5a.40 §三.3）
- 计划工具数 vs 源 run tool_call 数不一致：**85 例**（已记档）。
  - TAU-A-003 (e3): plan=24 run=14
  - TAU-A-013 (e3): plan=1 run=2
  - TAU-A-016 (e3): plan=11 run=13
  - TAU-A-018 (e3): plan=2 run=3
  - TAU-A-020 (e3): plan=5 run=3
  - TAU-A-024 (e3): plan=4 run=5
  - TAU-A-026 (e3): plan=7 run=5
  - TAU-A-030 (e3): plan=10 run=11

## 4. 两臂形态平衡表（长度）
- sibling: {'n': 43, 'min': 2, 'max': 24, 'mean': 7.9}
- unrelated: {'n': 44, 'min': 1, 'max': 14, 'mean': 4.7}

## 5. 骨架组成（P5a.41 §二）
**任务集（135）按 GT 动作类型**：
- 总计 state_change 108 / read_only 18 / correct_refusal 9
- airline {'read_only': 11, 'state_change': 23, 'correct_refusal': 7}
- retail {'state_change': 85, 'read_only': 7, 'correct_refusal': 2}

**注入池按结尾动作**：全池 {'query_end': 82, 'state_change_end': 259, 'transfer_end': 109}；**PASS-only 池 {'state_change_end': 151, 'transfer_end': 97, 'query_end': 52}**
- PASS-only **state_change_end 占比 = 50.3%**；分层抽样要求=False
- 成功骨架里 **97 条是 transfer(拒绝) 结尾**（占 32.3%）

**矩阵内两臂骨架类型构成（应一致）**：
- sibling: {'state_change_end': 25, 'transfer_end': 13, 'query_end': 5}
- unrelated: {'query_end': 13, 'state_change_end': 18, 'transfer_end': 13}

## 6. 脱敏库机检状态
- distinct_deid=443 all_pass=True proof_fails=0 not_in_static_dict=122(informational)

## 7. e8 预注册增补（P5a.41 §三）
- Δ2 判读报告必须附骨架组成分解：分别报告 状态变更型 与 拒绝型 注入物的 Δ2 分量；若效应全落在拒绝型，结论须写 拒绝骨架迁移有效，不得泛化 沉积有效。

## 8. 待签
- E 门通过 → 等 e8 运行令（三臂 direct/sibling/unrelated；主终点 Δ2=sibling−unrelated 簇 CI；~2h/10M tokens）。