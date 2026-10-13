#!/usr/bin/env python3
"""P5a.66 §二.3：sentinel-ledger 自动化（从 assets.json + firing-audit.json 生成，零 token）。
  /root/miniconda3/envs/mini-agent/bin/python scripts/sentinel_ledger.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, ".agent", "reports")


def main():
    assets = json.load(open(os.path.join(R, "assets.json")))["assets"]
    try:
        audit = json.load(open(os.path.join(R, "firing-audit.json")))["assets"]
    except Exception:  # noqa: BLE001
        audit = {}
    order = ["lock_order_v1", "repeat_failure_v1", "items_count_match_v1",
             "non_delivered_exchange_v1", "flight_availability_enforce_v1",
             "payment_amount_sum_enforce_v1", "gift_card_balance_enforce_v1",
             "flight_availability_v1", "payment_amount_sum_v1", "gift_card_balance_v1",
             "certificate_update_v1"]
    by = {a["asset_id"]: a for a in assets}
    L = ["# τ 哨兵台账（自动生成；源 assets.json + firing-audit.json）", "",
         "| 资产 | 状态 | 信用 | live_confirmed | 死因 | 型 | 救场 | 覆盖 | 税 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for aid in order:
        if aid not in by:
            continue
        a = by[aid]; v = audit.get(aid, {})
        lc = a.get("live_confirmed"); lcs = "—" if lc is None else ("True" if lc else "False")
        L.append(f"| `{aid}` | {a.get('status','?')} | {a.get('credit_level','?')} | {lcs} | "
                 f"{a.get('death_cause','?')} | {v.get('mode','-')} | {v.get('rescue','-')} | "
                 f"{v.get('coverage','-')} | {v.get('fires_on_pass','-')} |")
    act = [a for a in assets if a["status"] == "active"]
    fv = [a for a in act if a["credit_level"] == "field_validated"]
    lc_t = [a["asset_id"] for a in assets if a.get("live_confirmed") is True]
    L += ["", "## 汇总",
          f"- 在役 {len(act)}；field_validated {len(fv)}；live_confirmed True: {', '.join(lc_t) or '—'}",
          f"- superseded {len([a for a in assets if a['status']=='superseded'])}；revoked {len([a for a in assets if a['status']=='revoked'])}",
          "- 哨兵静默可解性：接线电池全绿后，静默=未发生，非失能。"]
    out = os.path.join(R, "sentinel-ledger.md")
    open(out, "w").write("\n".join(L) + "\n")
    print(f"sentinel-ledger.md regenerated ({len(order)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
