# P5a.74 法医结论验收、DC-7 脱敏验收与推送路径否决令

日期：2026-10-14
依据：image 120（a73 执行回报）、phase-P5a73-forensics-and-dc7-masking.md（未读，以回报为准）

## 一、法医结论：验收；裁者预判证伪入档

- 四改动均**未暂存**（工作区残留），mtime 10-12~10-13，实为 **E3 先导期与 a59 期的旧产物**（e3-executor-smoke-v2 / e3-v3-gate / decomposition-report / c1-coldstart-gate），非 a71 收割产物——裁者预判证伪，入档。法医流程（点名→内容→mtime→探针→处置）有效，空见证（turn-events 无相关写入）如实记录 ✓。
- 复现探针定性正确：不可复现者（e3 两件，代码已演进）= 调试碎屑 → 清场；与当前代码一致者（c1-coldstart-gate，a59 轮 8/8 + naming_proof）= 合法交付 → 补提交。提交 3f2c3da，工作区清净 ✓。
- **微修（入常设规则）**：今后法医处置执行**先快照后清场**——checkout 前把待弃版本 cp 至 .agent/local/（不跟踪），保留可逆性。本次未快照，下不为例。
- DC-8（工作区残留）成类 ✓；"开工先 git status"常设规则生效中。

## 二、DC-7 脱敏：验收通过

scripts/secret_mask.py::mask_secrets 覆盖 sk-/ghp_/ghz_/github_pat_ 前缀族；含假密钥摘要自检 raw=3 / hits=3 / plaintext_leak_after_mask=0 ✓。key.txt 已 chmod 600 + .gitignore，值未读未泄 ✓。DC-7 双侧（用户轮换 + 机器脱敏）关闭。

## 三、推送路径：否决

opencode 请示"给远程 URL 我推镜像"——**否决，维持现状**：

1. 常设安全约束：agent 可达 shell 禁 git push，simple-agent 远端同步 = 用户手动。此约束不变。
2. **本仓无 remote 是结构性边界，不是缺陷**——它在机制上保证推送权不离人。不要给 /root/simple-agent 配 remote。
3. key.txt 的 token 只供用户手动同步使用；opencode 永不使用，此条入红线。
4. 用户下次手动同步后，镜像即新鲜（当前远端 HEAD edcebed1，本地已含 3f2c3da，差一个快照）。

## 四、盘面

金丝雀门 v1.1 四门齐（代码域出生门侧前置完成）；DC-7/DC-8 关闭；代码尸体 7/30、4 类；主线回到静默攒批 + backlog 自理；无待办悬置（除用户手动同步镜像）。
