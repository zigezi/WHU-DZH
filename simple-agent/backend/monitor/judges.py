"""统一判决接口（P1 先落地 JudgeVerdict，P2 起所有判决类输出都走这里）。"""
from typing import List
from pydantic import BaseModel


class JudgeVerdict(BaseModel):
    decision: str            # PASS / FAIL / PARTIAL / HALT / ABSTAIN
    confidence: float
    domain_check: bool       # False = 出适用域，弃权升级
    evidence_refs: List[str] = []  # span_id / trace_id / 文件路径
    form: str                # rule | table | llm

    def is_pass(self) -> bool:
        return self.decision == "PASS"
