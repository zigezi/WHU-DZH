# epoch-3 SYSTEM_PROMPT 修改建议草稿（P5a.8 第 2 步）

> 性质：**草稿，交作者审阅，未应用**。按 P5a.8 裁决第 2 步产出。
> 前置声明（裁决 §5）：updater 的 25/9/2 归因分布是**未验证启发式**，本草稿仅用于**定向**，不构成根因结论。

---

## 0. 关键事实：τ 模式当前没有"worker 自有段"

代码路径（可复核）：

- `backend/dialogue_driver.py:99`：`self.system_prompt = self.sidecar.get_wiki(self.session_id)`
- `backend/worker.py:279`：`messages = [{"role":"system","content": driver.system_prompt}, {"role":"user","content": first_user}]`

即：**τ 模式 system prompt = wiki 全文，无任何 worker 自有行为指令段。**
（worker 常量 `SYSTEM_PROMPT` 仅用于常规任务；τ 模式不注入它。）

wiki 基线（未改动前的 sha256，供后续不触碰证明）：

```
airline  wiki_len=6155  sha256=56c335801c16e26b54f600f9db99eb04d31db477e86eb160341d5c66b796c5c8
retail   wiki_len=5718  sha256=d539fd2a46a8b8dd2e934ff9ed92f43e9f6b56bc7a718db8d2803ba8ad8f6bf7
```

**推论**：25 条 `SYSTEM_PROMPT` 提案**没有合法的直接落点**——现状下任何对 system prompt 的修改都会命中 wiki 段（评测环境资产）→ 按裁决 §3 一律作废。因此本步只能提出"**新增**一个与 wiki 分离的 worker 自有段"，不能改 wiki。

---

## 1. 合规改法（建议，待批）

在 wiki 之后**追加**一个带明确分隔标记的 worker 自有策略段：

```
<WIKI-BEGIN sha256=...>            ← 现有 wiki 段，逐字节不动
...env.wiki 原文...
<WIKI-END>
[WORKER-OWN POLICY v1 — 本系统资产，非评测环境资产]
...worker 自有行为规则...
[/WORKER-OWN POLICY]
```

- 只**新增** `[WORKER-OWN POLICY]` 段；wiki 段不改一个字符。
- 实现位置（若获批）：`dialogue_driver.py` 取到 wiki 后拼接该段，`worker.py` 无需改。

### wiki 不触碰证明（方法）
1. 注入前后，对 `<WIKI-BEGIN>..<WIKI-END>` 之间的子串单独求 sha256，须等于上表基线；
2. 或对整段做前缀校验：注入后字符串必须以原 wiki 原文开头（`injected.startswith(wiki)`）。

---

## 2. 候选 worker 自有规则（方向性，未验证）

> 均限于"本系统对 agent 的通用行为约束"，**不复制评测环境的 rules/wiki 内容**（复制即变相引入评测资产）。
> 括号内为对应的启发式根因模式，仅定向。

- **P1 先确认再动作**：收到请求先复述关键参数，再调用工具（对应 C 层目标漂移类）。
- **P2 不臆造信息**：仅使用用户提供或工具返回的信息（通用 agent 纪律）。
- **P3 上下文自摘要**：当上下文过长时，先压缩历史再继续（对应 C002 上下文膨胀）。
- **P4 结束即止**：确认目标达成后明确结束，不额外发起无关动作。
- **P5 工具失败换策略**：同一工具连续失败时改变参数或方法，不原地重试。

---

## 3. 红线与边界

- **禁止**修改、删除、重排 wiki 段任何字符（评测环境资产）。
- **禁止**把评测环境的 `rules`（如 retail 的"一次只调一个工具"）当作 worker 自有规则引入——那是评测资产，应留在评测侧。
- 本段仅为**行为提示**，不得包含任何 env 专属政策文本。

---

## 4. 待作者裁决项

1. 是否批准"新增 worker 自有段"这一结构改法（否则 25 条 SYSTEM_PROMPT 提案全部作废）；
2. 从 P1–P5 中圈定生效子集；
3. 圈定后由人工应用并单独 commit，再进 epoch-4（前置检查单见 P5a.8 §6.4）。

---

## 5. POLICY 段版本化（P5a.9 §2.3 新增要求）

- `policy_id = md5(POLICY段文本)[:12]`；`policy_version` 建议形如 `worker-policy-v1`。
- 注入时写 span：`layer="L", type="policy_inject", attributes={policy_id, policy_version, policy_chars}`。
- 目的：epoch 间通过率变化可归因到**具体策略版本**；无版本化的 POLICY 段不得上线。
- 红线：wiki 段 sha256 不变（`injected.startswith(wiki)` 成立），POLICY 段追加在 wiki 之后。
