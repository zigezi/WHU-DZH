"""V 层执行器（P1.2 / P1.3）：把需求断言变成可执行的尺子。

- run_assertions: subprocess 跑每条断言，exit 0 = pass，写 V 层 span；
- verdict: 按 severity 加权算 loss，写 verdict span，返回 JudgeVerdict；
- 支持 {workspace}/{db}/{req_id}/{trace_id} 占位符替换。
"""
import os
import subprocess
import time
from typing import List, Optional

from pydantic import BaseModel

from requirements import loader
from .collector import add_event
from .judges import JudgeVerdict
from .trace_store import DB_PATH

WORK_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "workspace")
)

SEVERITY_WEIGHTS = {"blocker": 3, "major": 2, "minor": 1}
ASSERTION_TIMEOUT_S = 30


class AssertionResult(BaseModel):
    req_id: str
    name: str
    passed: bool
    severity: str
    exit_code: int
    output: str = ""
    duration_ms: float = 0


def _substitute(cmd: str, req_id: str, trace_id: Optional[str]) -> str:
    return (
        cmd.replace("{workspace}", WORK_DIR)
        .replace("{db}", os.path.abspath(DB_PATH))
        .replace("{req_id}", req_id)
        .replace("{trace_id}", trace_id or "")
    )


def _run_one(req_id: str, trace_id: Optional[str], assertion: dict) -> AssertionResult:
    cmd = _substitute(assertion["cmd"], req_id, trace_id)
    start = time.time()
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=WORK_DIR,
            capture_output=True, text=True, timeout=ASSERTION_TIMEOUT_S,
        )
        exit_code = proc.returncode
        output = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        exit_code = 124
        output = "assertion timeout"
    except Exception as e:  # noqa: BLE001
        exit_code = 1
        output = str(e)
    return AssertionResult(
        req_id=req_id,
        name=assertion["name"],
        passed=exit_code == 0,
        severity=assertion["severity"],
        exit_code=exit_code,
        output=output[:500],
        duration_ms=(time.time() - start) * 1000,
    )


def run_assertions(req_id: str, trace_id: Optional[str] = None,
                   cheap_only: bool = False,
                   parent_span_id: Optional[str] = None) -> List[AssertionResult]:
    req = loader.get(req_id)
    results: List[AssertionResult] = []
    for assertion in req.get("assertions", []):
        if cheap_only and not assertion.get("cheap"):
            continue
        res = _run_one(req_id, trace_id, assertion)
        results.append(res)
        if trace_id:
            add_event(
                trace_id=trace_id,
                name=res.name,
                layer="V",
                span_type="acceptance_check",
                parent_span_id=parent_span_id,
                attributes={
                    "req_id": req_id,
                    "name": res.name,
                    "passed": res.passed,
                    "severity": res.severity,
                    "exit_code": res.exit_code,
                },
            )
    return results


def compute_loss(results: List[AssertionResult]) -> int:
    return sum(SEVERITY_WEIGHTS.get(r.severity, 1) for r in results if not r.passed)


def verdict(req_id: str, trace_id: Optional[str] = None,
            results: Optional[List[AssertionResult]] = None,
            parent_span_id: Optional[str] = None) -> JudgeVerdict:
    if results is None:
        results = run_assertions(req_id, trace_id=trace_id,
                                 parent_span_id=parent_span_id)
    loss = compute_loss(results)
    failed = [r.name for r in results if not r.passed]
    decision = "PASS" if loss == 0 else "FAIL"
    v = JudgeVerdict(
        decision=decision,
        confidence=1.0 if results else 0.0,
        domain_check=True,
        evidence_refs=[trace_id] if trace_id else [],
        form="rule",
    )
    if trace_id:
        add_event(
            trace_id=trace_id,
            name="V层判决",
            layer="V",
            span_type="verdict",
            parent_span_id=parent_span_id,
            attributes={
                "req_id": req_id,
                "decision": decision,
                "loss": loss,
                "failed": failed,
                "total_assertions": len(results),
            },
        )
    return v


def evaluate(req_id: str, trace_id: Optional[str] = None,
             parent_span_id: Optional[str] = None) -> dict:
    """返回 verdict + loss + 明细，供 epoch 评测器使用。"""
    results = run_assertions(req_id, trace_id=trace_id,
                             parent_span_id=parent_span_id)
    v = verdict(req_id, trace_id, results, parent_span_id)
    return {"verdict": v, "loss": compute_loss(results), "results": results}
