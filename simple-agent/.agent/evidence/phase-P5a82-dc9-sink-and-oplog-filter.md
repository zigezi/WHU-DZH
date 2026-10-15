# P5a.82 执行：DC-9 写路径下沉 + filter_oplog_v1 部署 + a81 认知

日期：2026-10-15
依据：a82 §三/§四/§五/§七；a81（E2 任务书骨架）
回执对象：a82 §七.2 单批次 (a)(b)(c)

## (b) §四 DC-9 写路径审计表（QB-2 确认成立）

| 写函数 | 是否经守卫（原状） | 修后 |
|---|---|---|
| `register_asset` | ✅ 有守卫 | 经 `_save(d, production)` |
| `set_credit` | ❌ 直写 | ✅ 经 `_save` 守卫 |
| `shadow_event` | ❌ 直写 | ✅ 经 `_save` 守卫 |
| `patch_asset` | ❌ 直写 | ✅ 经 `_save` 守卫 |
| `supersede` | ❌ 直写 | ✅ 经 `_save` 守卫 |
| `revoke` | ❌ 直写 | ✅ 经 `_save` 守卫 |
| `revalidate` | ❌ 直写 | ✅ 经 `_save` 守卫 |

**修法**：守卫下沉至 I/O 层 `_save(d, allow_production=False)`；所有写函数增 `production` 参数透传。合法生产写：`c1_coldstart_gate.revalidate(production=True)`；`organ.birth/shadow_fire` 带 `production`。**证据**：`scripts/provenance_guard_battery.py` → 17/17（沙盒 7/7 可写；生产 7/7 缺省拒；显式授权 3/3 允许）；真实注册表未被触碰。

## (a) §三 filter_oplog_v1 部署 + 离线重放

- **模块**：`backend/monitor/oplog_filter.py`（signal≥128 / timeout(124∧timeout(1)) / 白名单 build-test 族 / 黑名单良性控制流 / 灰区隔离）。
- **classify 修法**（§三.6）：废止"凡 rc!=0 即 test_or_build_fail"；`signal_death` 单列；非特定错误→`op_fail`。
- **fixtures 自证**（§三.7）：`scripts/oplog_filter_battery.py` → **24/24 deployed**（每口径 ≥2 正 2 负）。
- **离线重放**（§三.8）：`scripts/oplog_replay.py`；本次 21 行 → collect 4（3 gray + 1 signal，全为去重命中）/ drop 17 / 新增 0。**农场仍 6 real / 4 类**；4 条历史种子维持隔离（去重跳过）。
- **harvest 解禁**（§三 末）：已按 v1 口径运行，`added=0`（无新真实失败），`real_total=6`。

## (c) harvest 首轮统计
- `added=0`；丢弃以黑名单（grep/diff/git）与 rc0 为主；无灰区新增。**无污染**。

## §五 钩子加固
1. ✅ 控制字符兜底：`__oplog_jsonstr` 增 `tr -d` C0 剔除（\r\n\t 已转义）。
2. ⚠️ `sleep`→`wait`：**尝试后回退**——进程替换的 `tee` 非可 `wait` 的后台作业，单 `wait` 有竞态会截断摘要；保留 `wait`+小睡兜底（低危，见 a82 finding 2b）。
3. ✅ 文档化盲区：钩子头注明 **BASH_ENV 仅覆盖 bash，`/bin/sh`(dash) 子进程不采集**。

## §二 / §七 登记
- **LR-5** 入 `lessons-register.md`（二审 finding 可验证性分级：语言语义类零 token 证伪优先，架构类走验证令）。
- **Qwen 二审档案** `.agent/reports/qwen-review-register.md`：正面积分 finding1(确认)+finding3(采纳)；负面积分 QB-1(假阳性)+finding5(状态误读)。
- **§六**：RL-3 原文不变（用户直裁）；token 轮换仍挂账。

## a81（E2 任务书骨架）
- 认知：注册段三方输入骨架，域事实仍待用户（§八清单）；opencode 侧无可代填项，不编造（a68）。设施事实清单已在 `phase-P5a76-e2-facility-facts.md`。

## 回归
- `regression_sweep.py`：**15 电池** GREEN，注册表不变性保持（含 `provenance_guard_battery` / `oplog_filter_battery`）。
