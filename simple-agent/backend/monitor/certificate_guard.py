"""P5a.54 C4-3：资产 certificate_update_v1 —— 改签用 certificate 支付（政策禁止）。

点火（确定性，**限 update 场景**）：即将调用 `update_reservation_*`，且支付方式为
`certificate_*` → 否决。**排除** book / 纯回复（正确拒绝形状）——只拦"正在提交的改签支付"。
误伤边界：正确拒绝（agent 告知用户不可用）无 update 调用 → 不触发。
"""
from typing import Optional, Tuple

UPDATE_PREFIX = "update_reservation_"
PAY_KEYS = ("payment_id", "payment_method_id")
SYNTHETIC = ("CERT-UPDATE：政策不允许用 certificate 支付改签（update_reservation_*）。"
             "请改用 credit_card / gift_card 等允许的方式。")


class CertificateUpdateGuard:
    def before(self, tool_name: str, args: dict) -> Tuple[bool, Optional[str]]:
        if not tool_name.startswith(UPDATE_PREFIX):
            return False, None
        a = args or {}
        for k in PAY_KEYS:
            v = a.get(k)
            if isinstance(v, str) and v.startswith("certificate_"):
                return True, SYNTHETIC
        return False, None


guard = CertificateUpdateGuard()


def reset():
    global guard
    guard = CertificateUpdateGuard()
    return guard
