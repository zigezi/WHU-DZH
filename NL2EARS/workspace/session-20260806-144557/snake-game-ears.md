# 需求规格说明书（EARS）— 儿童贪吃蛇小游戏

- spec_id: SPEC-SNAKE-20260806
- source: requirements-20260806-145045.md
- version: 1.1
- 说明: 本文档由自然语言需求经 EARS 转换生成。所有带 [TBD-xx] 的数值为**默认假设**，在需求方确认前，实现必须严格按默认值执行，不得自行更改。
- 范围注记: 原文「七、后续任务建议」（用户测试、性能优化、界面美化）为过程性建议，不属于产品需求，不纳入本规格。

---

## 0. 术语表（封闭词汇表）

本文档及后续实现中，以下术语为唯一合法表述，禁止同义替换。

| 术语 | 类别 | 定义 |
|---|---|---|
| Game | entity | 游戏实例，包含 state、grid、snake、apples |
| GameState | enum | {ready, playing, cleared, failed}，封闭集合 |
| Grid | value | 正方形格点棋盘，20 列 × 20 行 [TBD-02] |
| Cell | value | Grid 中的一个格点，坐标记作 (列, 行)，左上角为 (0, 0)，列向右递增、行向下递增，取值 0~19 |
| Snake | entity | 由有序 Cell 序列组成的蛇，队首为 head，队尾为 tail |
| Apple | entity | 占据一个 Cell 的可食物体 |
| Direction | enum | {up, down, left, right}，封闭集合 |
| DirectionButton | ui | 屏幕下方固定渲染的四个方向按钮，分别对应 Direction 四值 [TBD-06] |
| Player | role | 儿童玩家，系统唯一角色 |
| 移动步进 | concept | Snake 每 200ms（= 5 格/秒 [TBD-04]）前进一格的离散动作，一切判定以步进为单位 |

---

## 1. 全局规则（Ubiquitous）

- **GR-01** The system shall 仅提供单人游戏模式，不提供任何多人或对战入口。
- **GR-02** The system shall 仅包含一个固定关卡，不提供关卡选择、关卡编辑或关卡进度界面。
- **GR-03** The system shall 不持久化任何游戏状态；浏览器页面关闭或刷新后，全部游戏状态丢弃，再次打开时 Game.state 为 ready。
- **GR-04** The system shall 以鼠标点击 DirectionButton 作为唯一操控方式，不提供键盘或其他输入途径 [TBD-11]。
- **GR-05** WHILE Game.state != playing, the system shall 忽略一切 DirectionButton 输入。

---

## 2. 功能需求（Functional Requirements）

### FR-01 游戏初始化与开始

- 模式: Event-driven
- 原文映射: 三、功能需求 - 单人模式实现 / 游戏关卡
- **EARS**: WHEN Player 点击「开始游戏」按钮, the system shall 执行以下全部动作，并在 500ms 内呈现首帧画面 [TBD-09]:
  1. 将 Game.state 置为 playing；
  2. 初始化 Snake，长度 3 节 [TBD-03]，坐标固定为 head=(10,10)、身体依次为 (9,10)、(8,10)，初始方向为 right；
  3. 在 Grid 上随机放置 10 个 Apple [TBD-01]，放置约束为：10 个 Apple 占据 10 个互不相同的 Cell；任何 Apple 不得与 Snake 身体重叠；任何 Apple 与 Snake.head 的曼哈顿距离不小于 3；
  4. Snake 开始以 5 格/秒的恒定速度自动移动 [TBD-04]，全程不加速、不减速。
- **验收点**: 验收基于不变量判定（Apple 数量 = 10、互不重叠、不在蛇身、与蛇头距离 ≥ 3），而非具体随机位置。

### FR-02 方向控制

- 模式: Event-driven
- 原文映射: 三、功能需求 - 单人模式实现（验收标准：鼠标点击上下左右操控）
- **EARS**: WHEN Player 点击某个 DirectionButton 且 Game.state == playing, the system shall 缓存该方向；在 Snake 的下一个移动步进时，将移动方向变更为最近一次缓存的 Direction。
- **输入缓冲规则（强一致要求）**: 每个移动步进只生效最近一次点击；同一步进间隔内的多次点击按覆盖式处理（后一次覆盖前一次），不排队。
- **异常路径**: IF 生效时目标 Direction 与 Snake 当前实际移动方向互为 180° 反向, THEN the system shall 忽略该输入，Snake 保持原方向。反向判定一律针对当前实际移动方向，不针对已缓存方向。
- **时序约束**: 从点击发生到画面呈现方向变化，延迟不得超过 100ms [TBD-07]。

### FR-03 吃苹果

- 模式: Event-driven
- 原文映射: 三、功能需求 - 单人模式实现（吃掉所有苹果）
- **EARS**: WHEN Snake.head 进入一个包含 Apple 的 Cell, the system shall 在同一移动步进内执行: 移除该 Apple，并将 Snake 长度增加 1 节 [TBD-05]（新节出现在尾部，即本步进内 tail 不移动）。

### FR-04 通关判定

- 模式: Unwanted-condition（目标达成式）
- 原文映射: 三、功能需求 - 通关机制（吃掉所有苹果即通关成功）
- **EARS**: IF FR-03 执行后 Grid 上 Apple 数量为 0, THEN the system shall 立即将 Game.state 置为 cleared，停止 Snake 移动，并在 500ms 内显示通关成功界面 [TBD-09]。
- **通关后流程**: 通关成功界面提供一个「再玩一次」按钮 [TBD-12]；WHEN Player 点击该按钮, the system shall 执行 FR-01 的动作序列（同点开始游戏）。
- **验收点**: 通关判定不得依赖定时轮询，必须由吃苹果事件触发。

### FR-05 失败判定与自动重开

- 模式: Unwanted-condition
- 原文映射: 三、功能需求 - 通关机制（否则通关失败，并重新开始游戏）
- **EARS**: IF Snake.head 移出 Grid 边界, OR Snake.head 进入 Snake 身体所占的任一 Cell, THEN the system shall 依次执行:
  1. 将 Game.state 置为 failed，停止 Snake 移动；
  2. 显示失败提示界面，持续 2 秒 [TBD-09]；
  3. 自动执行 FR-01 的第 1~4 步动作（无需点击任何按钮），Game.state 直接置为 playing。
- **碰撞判定基准（强一致要求）**: 撞自身判定基于**移动前**的身体 Cell 集合，且包含本步进内将移出的 tail 格——即蛇头进入本步将让出的尾格仍判定为碰撞。
- **异常路径**: 失败判定与通关判定在同一移动步进内不得同时成立；若同时满足（吃掉最后一个 Apple 的步进不发生碰撞），通关判定优先 [TBD-08]。

---

## 3. 非功能需求（Non-Functional Requirements）

- **NFR-01 流畅性**: WHILE Game.state == playing, the system shall 维持画面渲染帧率不低于 50 FPS（目标 60 FPS），且任何单次输入到视觉反馈的延迟不超过 100ms [TBD-07]。
- **NFR-02 浏览器兼容**: The system shall 在 Microsoft Edge 最近两个稳定版本上正常运行，本文档全部 FR 在该环境下通过验收。
- **NFR-03 儿童可用性**: WHERE 目标用户为儿童, the system shall 满足: DirectionButton 可点击区域不小于 64×64 CSS 像素 [TBD-10]；开始、失败、通关界面的核心操作不依赖阅读超过 10 个汉字的文本 [TBD-10]。

---

## 4. 技术约束（Constraints）

- **CON-01** 实现形态为纯前端 Web 应用，运行环境为 Edge 浏览器，不依赖任何后端服务。
- **CON-02** 不使用任何数据持久化机制（含 localStorage、Cookie、IndexedDB）。

---

## 5. 非目标（Non-goals）

- **NG-01** 不实现任何形式的社交功能，包括但不限于分享、排行榜、好友系统、多人对战。
- **NG-02** 不实现复杂图形效果，包括但不限于粒子特效、3D 渲染、光影效果、动画过渡。
- **NG-03** 不实现高级游戏机制，包括但不限于道具系统、加速机制、多关卡、AI 对手、障碍物。

---

## 6. TBD 与默认假设清单

以下默认值在需求方确认前为实现依据。**下游实现（含代码生成模型）必须采用表中默认值，不得自行选择其他取值。**

| TBD 编号 | 槽位 | 默认假设 | 影响的需求条目 |
|---|---|---|---|
| TBD-01 | Apple 总数与放置方式 | 10 个，FR-01 时一次性随机放置：占据 10 个互不相同的 Cell、不与蛇身重叠、与蛇头曼哈顿距离 ≥ 3；被吃后不补充 | FR-01, FR-03, FR-04 |
| TBD-02 | Grid 尺寸 | 20 × 20 Cell | FR-01, 全局 |
| TBD-03 | Snake 初始状态 | head=(10,10)，身体 (9,10)、(8,10)，初始方向 right | FR-01 |
| TBD-04 | 移动速度 | 恒定 5 格/秒（每步进 200ms），全程不变 | FR-01, NFR-01 |
| TBD-05 | 吃苹果的效果 | 长度 +1 节（新节在尾部，本步进 tail 不动），无得分显示、无音效要求 | FR-03 |
| TBD-06 | 操控 UI 形态 | 屏幕下方固定渲染四个 DirectionButton（上下左右） | FR-02, NFR-03 |
| TBD-07 | 性能阈值 | 帧率 ≥ 50 FPS（目标 60）；输入延迟 ≤ 100ms | FR-02, NFR-01 |
| TBD-08 | 判定优先级 | 同步进冲突时通关判定优先于失败判定 | FR-04, FR-05 |
| TBD-09 | 界面切换时长 | 首帧 ≤ 500ms；通关界面 ≤ 500ms；失败提示停留 2 秒 | FR-01, FR-04, FR-05 |
| TBD-10 | 可用性数值 | 按钮可点击区域 ≥ 64×64 CSS 像素；核心操作文本 ≤ 10 个汉字 | NFR-03 |
| TBD-11 | 操控方式范围 | 仅鼠标点击（原文未排除键盘，此处为加强假设：禁止键盘操控以保证跨实现一致） | GR-04, FR-02 |
| TBD-12 | 通关后流程 | cleared 界面提供「再玩一次」按钮，点击后执行 FR-01 动作序列 | FR-04 |

---

## 7. 验收追踪矩阵

| 需求 ID | 原文出处 | 验收方式 |
|---|---|---|
| FR-01 | 单人模式实现 / 游戏关卡 | 黑盒: 点击开始后按不变量验收——Apple=10、互不重叠、不在蛇身、与蛇头距离≥3；Snake 初始坐标精确为 (10,10)(9,10)(8,10) |
| FR-02 | 单人模式实现（验收标准） | 黑盒: 点击四向按钮蛇转向；反向点击被忽略；同步进内连点两次仅最后一次生效 |
| FR-03 | 单人模式实现（描述） | 黑盒: 蛇头触苹果后苹果消失、蛇长 +1（尾节增长） |
| FR-04 | 通关机制（成功分支） | 黑盒: 吃完第 10 个苹果后 500ms 内出现通关界面；点「再玩一次」重新开局 |
| FR-05 | 通关机制（失败分支） | 黑盒: 撞墙/撞自身（含本步将让出的尾格）→ 失败提示 → 2 秒后自动重开并直接进入 playing |
| NFR-01 | 流畅性要求 | 白盒/性能: Edge DevTools 帧率面板 ≥ 50 FPS |
| NFR-02 | 技术约束与环境 | 黑盒: Edge 最近两版本全用例通过 |
| NFR-03 | 可用性需求 | 黑盒: 按钮尺寸测量；无长文本依赖走查 |
| CON-01/02 | 技术约束与环境 | 白盒: 代码中无网络请求与存储 API 调用 |
| NG-01/02/03 | 非目标 | 审查: 交付物中不存在对应功能入口 |
