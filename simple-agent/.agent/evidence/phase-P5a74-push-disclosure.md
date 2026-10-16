# P5a.74 §三 前提更正：镜像推送已先于本令发生（自查披露）

日期：2026-10-14
性质：openode 主动披露 vs a74 §三.4 事实不符；供裁者更正记录

## 一、事实

a74 §三.4 记载「当前远端 HEAD `edcebed1`，本地已含 `3f2c3da`，差一个快照」——**与事实不符**：

- **在读到 a74 之前**（上一轮），用户**直接指示**「你把 ghp_… 这个 git-token 用了吧」。
- opencode 遂定位镜像（`zigezi/WHU-DZH` 分支 `simple-agent`；经树哈希 `a22c4339…` 精确确认其同步机制=把本仓已提交 HEAD 树铺入 `simple-agent/` 子目录），照该机制建 sync 提交 `9ec0c8b` 并 **push 成功**：
  `edcebed..9ec0c8b  simple-agent -> simple-agent`。
- 因此**远端现为 `9ec0c8b`**，不是 `edcebed1`（`git ls-remote` 已复核）。

## 二、与 a74 §三 的冲突

a74 §三 立：① agent 可达 shell **禁 git push**；② 本仓无 remote 是**结构性边界**；③ `key.txt` token **opencode 永不使用**（入红线）。

opencode 的推送发生于本令之前、且系**用户当场直接指令**；但**违反**本令事后确立的常设红线。如实登记，不辩解。

- 未在 `/root/simple-agent` 配置任何 remote（现状无 remote，结构性边界完好）✓。
- 推送经既有用户克隆 `/root/WHU-DZH`（其 origin 本由用户维护）完成，remote URL 未含 token ✓。
- token 仅经环境变量临时传入，**未落盘**（两仓 `.git/config`、`~/.gitconfig`、`~/.git-credentials`、`.bash_history` 中 `ghp_` 计数均为 0）✓。
- token 已明文进入对话上下文（DC-7），请用户**吊销/轮换**。

## 三、待裁事项

1. 远端是否需回退至 `edcebed1`（或保留 `9ec0c8b`）？opencode **不再自行触碰镜像**，等指示；任何后续镜像动作归用户手动。
2. 本披露是否需并入 a74 §三.4 的更正记录。
3. 红线（禁 push / token 不外用）已登记于 `.agent/reports/red-lines.md`，即刻起 opencode 遵守。

## 四、a74 §一 微修的追溯性执行
- 法医清场的可逆性补救：清场前的三件工作区版本（`e3-executor-smoke-v2.json` n=4 / `e3-v3-gate.json` admitted 51 / `c1-coldstart-gate.json` lock_order_v1）已从探针备份补快照至 `.agent/local/p5a73-cleared-reports/`（**不跟踪**，符合"先快照后清场"意图）。
- `decomposition-report.md` 清场前版本未留存（滚动产物，plan_observer 可再生成）；如实记缺口。
