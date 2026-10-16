# Phase 5a.2 证据 — 工具桥（sidecar 客户端）

- 生成时间：2026-09-11T18:03:14+08:00  分支：simple-agent @ 78ff6c8

## 1. per-session τ 工具注册 + 本地工具关闭（tool_scope span）

```
$ sqlite3 ... type='tool_scope' WHERE trace_id='985905c8-6e64-4b9d-b50e-7169923cc045'
{"mode": "tau", "disabled": ["shell", "file_ops"], "tau_tools": ["tau__book_reservation", "tau__calculate", "tau__cancel_reservation", "tau__get_reservation_details", "tau__get_user_details", "tau__list_all_airports", "tau__search_direct_flight", "tau__search_onestop_flight", "tau__send_certificate", "tau__think", "tau__transfer_to_human_agents", "tau__update_reservation_baggages", "tau__update_reservation_flights", "tau__update_reservation_passengers"]}
```

## 2. τ 任务工具调用全部 tau__ 前缀，无 shell

```
$ sqlite3 ... SELECT DISTINCT name WHERE layer='T'
tau__get_user_details
tau__search_direct_flight
tau__search_onestop_flight
tau__book_reservation
$ E 层 span 存在（effect_diff 对 τ 恒空属正常，只查存在）
E|sandbox_exec|8
```

## 3. sidecar 不可达 → 立即结构化报错，不 hang

```
$ (sidecar stopped) python3 bridge probe
SidecarError in 0.01s: sidecar unreachable: URLError: <urlopen error [Errno 111] Connection refused>
forwarder RuntimeError in 0.01s: [tau] sidecar error on calculate: sidecar unreachable: URLError: [Errno 111] Connection refused
```

## 4. 工具生命周期

- 每 episode reset 后 ToolBridge.register(session) 动态注册 tau__* 到 τ 专用 registry；finish() 注销
- τ 任务使用独立 ToolRegistry（不含 shell/file_ops），不污染全局 registry，无并发串扰
