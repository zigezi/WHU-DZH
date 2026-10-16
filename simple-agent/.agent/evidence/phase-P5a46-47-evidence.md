# P5a.46–47 落地证据：失败开采首跑 + C-1 冷启动复现门 + E3 假设清单

## 1. τ 失败开采管线首跑（a47 §三.1）
- 新 `scripts/p5a36_failure_mine.py`（此前为空账）——从 e1–e8 尸体库挖死亡模式。
- 结果：**FAIL 任务 259**，**谓词候选 25**（全部标"候选"，未登记资产）。
  - `ERR::user not found` ×15、`ERR::non-pending order cannot be modified`（锁序）×6、
    `not enough seats on flight …` ×5+2+1、`gift card balance is not enough` ×4、重复失败重复模式等。
- 产物：`.agent/reports/p5a36-death-patterns.json`。候选 → 金丝雀电池 → 才可登记 `validated_domain=tau` 资产。

## 2. C-1 冷启动复现门（a47 §二）
- 新 `scripts/c1_coldstart_gate.py`：干净容器（`/tmp/opencode/c1-clean-*`）**只装** harness(`interceptor.py`) + 资产注册表(`assets.json`) + 验证器(电池)，无会话历史/本地卷宗；跑 B-2 电池。
- 结果：**PASS**——电池 7/7、资产在场、`lock_order_v1` 点火正确、零 token。
  - 出生证末栏写入：`C-1 冷启动复现门：PASS（干净容器 …；电池 7/7；资产在场=True；零 token）`（见 `assets.json.revalidation_log`）。
- 判定：**资产是真实可移植的物，不是黑板幻觉的投影。**

## 3. E3 假设清单（a46 §二 收留形式）
- `.agent/reports/e3-survey-hypotheses.md`：6 条方向（测试空转/构建破坏/奖励黑客/环境污染/过早收敛/顺序敏感）**明确标注为假设，非谓词**；只指导 E3 先导埋探针。

## 4. 安全（a46 §四）
- classic token（`ghp_…TXv`）须**立即 revoke 重置**；**本轮未推送**（尊重安全令，等新 token）。

## 5. 状态
- τ 资产 = 1（`lock_order_v1`，过 B-2 + C-1）；失败开采首跑完成，τ 谓词候选 25 条待认证。
- 部署资产数：1（发热比 ~30:1）。
