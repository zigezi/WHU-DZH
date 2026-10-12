"""P5a.32/45：e9 部署资产 —— 锁序执行期确定性拦截器（Path B'，否决式）。

- 归属 **monitor**（纯规则职权；确定性谓词，禁 LLM）。
- 时机 = **执行前**（调用产生 < 调用执行 < 锁死生效；合法窗口=执行前）。
- 谓词：`modify_pending_order_items` 即将执行，且**同订单尚未**执行过
  `modify_pending_order_address`，且该订单**未被本拦截器否决过**。
- 动作：**否决**该次执行，返回合成结果（不执行 → 锁不扣）。
- once-per-order 状态位：同订单第二次 items 调用**直接放行**（避免死循环）。
- 误报成本 = 每单至多一次空转轮次；漏报成本 = 任务失败 → 宁早勿晚。

部署：worker 以 `SA_LOCK_INTERCEPTOR=1` 启用；每次点火记 span（证据）。
"""
from typing import Optional, Tuple

INTERCEPT_TOOL = "modify_pending_order_items"
ADDRESS_TOOL = "modify_pending_order_address"
SYNTHETIC = ("INTERCEPTED：本订单若还需改地址，请先执行 modify_pending_order_address，"
             "再改物品；若本订单无需改地址，请重新发起本调用即可通过。")


class OrderLockInterceptor:
    """每 episode 一个实例（按订单维护状态位）。确定性、无 LLM。"""

    def __init__(self):
        self._address_done = set()   # 已成功改过地址的 order_id
        self._vetoed = set()         # 已被否决过一次的 order_id

    @staticmethod
    def _oid(tool_name: str, args: dict) -> Optional[str]:
        return (args or {}).get("order_id")

    def before(self, tool_name: str, args: dict) -> Tuple[bool, Optional[str]]:
        """执行前调用。返回 (veto, synthetic_result)。veto=True 表示**不执行**。"""
        if tool_name != INTERCEPT_TOOL:
            return False, None
        oid = self._oid(tool_name, args)
        if oid is None or oid in self._vetoed or oid in self._address_done:
            return False, None
        self._vetoed.add(oid)
        return True, SYNTHETIC

    def after(self, tool_name: str, args: dict, success: bool):
        """执行后调用（仅在**真正执行**后）；更新状态位。"""
        if tool_name == ADDRESS_TOOL and success:
            oid = self._oid(tool_name, args)
            if oid:
                self._address_done.add(oid)


# 全局实例（worker 每任务 reset）
interceptor = OrderLockInterceptor()


def reset():
    global interceptor
    interceptor = OrderLockInterceptor()
    return interceptor
