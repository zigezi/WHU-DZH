"""P5a.48 §八：资产 repeat_failure_v1 —— 重复失败执行期拦截器（Path B' 否决式）。

- 谓词（确定性）：即将执行 (tool, canonical_args) 的**完全相同调用**，该键已**失败 ≥2 次**
  （即第 3 次相同失败尝试）→ **否决执行**。
- 干预语义（否决式，参照 P5a.32 Path B'）：返回合成结果，引导换参数/方法（P5 纪律）。
- 状态位：按 (tool, canonical_args) 键；成功即清零（合法重演不受影响）；键独立。
- 阴性对照（不该拦）：成功重复 / 不同参数 / 不同工具 / 失败次数未达阈值。
- 归属 monitor（纯规则，禁 LLM）。
"""
import json
from typing import Optional, Tuple

THRESHOLD = 3          # 达到第 3 次相同失败尝试即拦（前两次放行）
SYNTHETIC = ("REPEATED-FAILURE：完全相同的调用（工具+参数）已失败 {n} 次。"
             "请改变参数或方法（不要原地重试），或说明当前无法完成。")


class RepeatFailureGuard:
    def __init__(self, threshold: int = THRESHOLD):
        self.threshold = threshold
        self._fails = {}   # key -> consecutive fail count

    @staticmethod
    def _key(tool_name: str, args: dict) -> str:
        return tool_name + "|" + json.dumps(args or {}, sort_keys=True, default=str)

    def before(self, tool_name: str, args: dict) -> Tuple[bool, Optional[str]]:
        n = self._fails.get(self._key(tool_name, args), 0)
        if n >= self.threshold - 1:       # 本次将是第 threshold 次相同失败尝试
            return True, SYNTHETIC.format(n=n)
        return False, None

    @staticmethod
    def _is_state_change(tool_name: str) -> bool:
        return not tool_name.startswith(("get_", "search_", "list_", "find_",
                                         "calculate", "think"))

    def after(self, tool_name: str, args: dict, success: bool):
        k = self._key(tool_name, args)
        if success:
            # P5a.48 修正（N4）：任意**状态变更**成功后，环境已变，
            # 先前失败的键可能本会成功 → 清零全部计数（避免把合法重试拦死）
            if self._is_state_change(tool_name):
                self._fails.clear()
            else:
                self._fails.pop(k, None)   # 只读成功 → 清本键
        else:
            self._fails[k] = self._fails.get(k, 0) + 1


guard = RepeatFailureGuard()


def reset():
    global guard
    guard = RepeatFailureGuard()
    return guard
