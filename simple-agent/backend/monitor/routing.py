"""路由后验表（P3.2）：Beta 后验 + Thompson 采样选择执行臂。

choose: ε=0.1 概率随机探索，否则按 Beta 后验 Thompson 采样选臂；
update: 成功 α+1，失败 β+1，并累计 token。
"""
import os
import random
from typing import List, Optional

from .trace_store import trace_store

DEFAULT_ARMS = ["direct"]
EPSILON = 0.1
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-chat")


def env_fingerprint() -> str:
    return MODEL_NAME


class Router:
    def __init__(self, epsilon: float = EPSILON):
        self.epsilon = epsilon

    def choose(self, sig_family: str, arms: Optional[List[str]] = None) -> str:
        arms = arms or DEFAULT_ARMS
        if not arms:
            return "direct"
        if random.random() < self.epsilon:
            return random.choice(arms)
        best_arm, best_sample = arms[0], -1.0
        for arm in arms:
            alpha, beta = trace_store.get_route_params(
                sig_family, arm, env_fingerprint()
            )
            sample = random.betavariate(alpha, beta)
            if sample > best_sample:
                best_sample, best_arm = sample, arm
        return best_arm

    def update(self, sig_family: str, arm: str, success: bool,
               tokens: float = 0):
        return trace_store.update_route(
            sig_family, arm, env_fingerprint(), success, tokens
        )


router = Router()
