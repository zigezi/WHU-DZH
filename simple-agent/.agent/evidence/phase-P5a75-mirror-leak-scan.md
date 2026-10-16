# P5a.75 §五 镜像泄密扫描（零 token 工单）

日期：2026-10-14
脚本：`scripts/mirror_leak_scan.py`（复用 `secret_mask` 前缀族；只记 kind/长度/文件，不记值）
报告：`.agent/reports/mirror-leak-scan-{local-head,mirror-9ec0c8b,mirror-full-9ec0c8b}.json`

## 结论

**无明文泄漏。三处扫描 secret_hits=0；`9ec0c8b` 未含密钥明文 → 无需历史清洗。**

| 扫描 | 对象 | files_scanned | secret_hits | plaintext_leak |
|---|---|---|---|---|
| A | 本地 HEAD（**待同步内容**） | 512 | **0** | false |
| B | 镜像 `9ec0c8b:simple-agent`（**已推送子树**） | 510 | **0** | false |
| C | 镜像 `9ec0c8b` 全树 | 538 | **0** | false |

正对照：植入假 `ghp_…` → 扫描器命中（`github_token` len=40），确认检测有效、非空转。

## 方法
- `git archive <ref> [prefix] | tar -x` 取全树文本 → 逐文件过 `secret_mask` 前缀族（`sk-`/`ghp_`/`ghz_`/`github_pat_`/`sk-ant-`/`sk-proj-`/`AKIA`/`Bearer`）。
- 二进制/超 2MB 跳过；排除掩码器自身（见下）。

## 诚实注记（扫描器自指误报，已修）
首轮 B 扫出 3 命中，**全是 `scripts/secret_mask.py` 内故意假密钥夹具**（`sk-FAKE…`/`ghp_FAKE…`/`ghz_FAKE…`）——非真泄漏。根因：排除表用相对路径精确匹配，而 subtree 前缀（`simple-agent/`）使相对路径变了。已改为**后缀匹配**（`rel.endswith(.../scripts/secret_mask.py)`），复扫归零。此即"扫描器自身也须过 known-answer 正/负对照"的实例。

## 待办（用户侧）
- 吊销/轮换 `key.txt` token（第二次同类暴露，a75 §四）。
- 下次手动同步后，可再跑本轮 A 扫描（待同步内容）作常规闸；`9ec0c8b` 已净。
