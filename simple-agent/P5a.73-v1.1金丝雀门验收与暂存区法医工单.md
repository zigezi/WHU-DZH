# P5a.73 v1.1 金丝雀门验收与暂存区法医工单

日期：2026-10-14
依据：image 118/119（P5a.72 §三 完工回报）、GitHub 镜像提交账（远端 HEAD edcebed1）

## 一、金丝雀门 v1.1：验收通过

- GREEN 4/4：捏造 / 重试风暴 / 换策略 / **隐式语义故障**（read_sensor 返回 schema 合法 JSON 但 reading_c=47 > safe_max_c=35 却标 status="nominal"；机制在场=不被 status 骗到，false_accept=吞下矛盾）。
- 读数：mechanism_present=4/4、recall=1.0、canary_leak=false、excluded=[]、tokens 4,483-5,054 < 0.1M，两次独立运行一致；法则 5（fault_not_triggered 剔除）机制就位；v1 冻结不改 ✓。
- **结论：代码域首资产出生的门侧前置正式完成。**

## 二、暂存区 4 个 reports 改动：法医工单（零 token）

裁者边界声明：未提交内容只存于服务器工作区，裁者无法远程查看；GitHub 镜像已将嫌疑窗口压缩至 **a71 同步（远端 edcebed1，10-14 02:46Z）之后、v1.1 会话提交尝试之前**。

**裁者预判（非结论）**：头号嫌疑 = a71 收割核对轮自身的报告写入——尸体计数 6→7 必然触发 code-domain-accumulation / 尸体库 / 台账等文件更新，可能被 git add 后未随代码提交，或收割在提交后再次运行。

opencode 法医五步：
1. `git status --porcelain` + `git diff --cached --stat` 点名四文件；
2. 读 diff 内容——报告头带 P5a 编号，定产出轮次；
3. `stat -c '%y %n'` mtime 对会话时间线；
4. turn-events.jsonl 交叉验证写入事件；
5. 处置：合法产物**补提交**（提交信息注明来源轮次），碎屑 `git checkout --` 清场。结果回报裁者。

## 三、常设规则（防再发）

**每会话开工先 `git status`，工作区不净先清算**——"预存改动阻塞提交"入 governance-defect-classes.md 候选（待法医结果定性后正式成类）。

## 四、DC-7 处置状态更新

- 用户侧：**API key 与 GitHub token 均已轮换** ✓（10-14）。
- opencode 侧：摘要生成器密钥脱敏（a72 §一.2 立法）**待验证**——下轮回报须含脱敏落地证据（脱敏规则代码位置 + 一次含假密钥的摘要试跑，输出中无明文）。

## 五、裁者事故登记（第 5 次"引而未写"：本令）

最终修补，不再迭代措辞：**凡含文书交付的轮次，write 必须是本轮第一个动作，先成文后回复。** 若再犯，用户可直接开新会话——裁决链全在本目录，启动上下文即文件清单，换会话零成本。
