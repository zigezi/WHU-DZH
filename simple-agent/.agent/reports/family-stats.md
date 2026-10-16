# 任务族复发率统计

- 总任务数：6
- 任务族数：5

| 排名 | 签名 | 数量 | 占比 | 代表任务 |
|---|---|---|---|---|
| 1 | fcfe8120cda2 | 2 | 33.3% | 在 workspace 创建 hello.txt 写入 hi |
| 2 | aaca89deafa6 | 1 | 16.7% | 读取 frontend/index.html 的内容 |
| 3 | dc1d8cd853bb | 1 | 16.7% | 读取 test.txt 文件内容并告诉我 |
| 4 | c7ef7b7f9ba9 | 1 | 16.7% | 读取 workspace 里的 test.txt 文件并告诉我内容 |
| 5 | 97f51999228e | 1 | 16.7% | 在 workspace 创建 smoke.txt 写入 ok |

## 决策结论

Top 族占比 33.3% ≤ 50% → **P3 只做路由表，编译留桩**。
