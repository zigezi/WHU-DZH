"""P5a.58 生成器官（MVP）：五环管线骨架 + 影子出生路径 + 宪法级自治边界。

宪法（器官**永不**做，越界即拒）：
  1. 触碰奖励函数/验证器；2. 编辑测试与金丝雀电池；3. 自行变更 taxonomy/值分类法/死因分类法；
  4. 让缺可观测性证明者进入影子期；5. 让无影子证据者转正；6. 直接 commit/push（产出入证据域，不入提交域）。
"""
import os
import re
from typing import List, Optional, Tuple

from . import provenance as prov

# 宪法：禁止触碰的路径模式（奖励函数/验证器/测试/电池）
FORBIDDEN_PATH = re.compile(
    r"(scoring\.py|eval_loop\.py|e3_executor|e3_generator|_battery\.py|canary|"
    r"hidden_test|reward)", re.I)

# 出生要件：点火条件须可观测（占位实现 = 必须有非空 observability_proof）
REQUIRED_BIRTH_FIELDS = ("asset_id", "type", "validated_domain", "trigger",
                         "observability_proof", "evidence")


def assert_in_scope(path: str):
    """宪法墙：器官永不许编辑奖励/验证器/测试/电池。"""
    if FORBIDDEN_PATH.search(path or ""):
        raise PermissionError(f"[organ] constitution violation: forbidden path {path}")


def can_birth(candidate: dict) -> Tuple[bool, List[str]]:
    """§三.4 可观测性证明 + §五(P5a.59) 名称匹配守卫须有 naming_proof（经真实 execute_tool、生产命名）。"""
    errs = [f"missing:{f}" for f in REQUIRED_BIRTH_FIELDS if not candidate.get(f)]
    if candidate.get("name_matching") and not candidate.get("naming_proof"):
        errs.append("missing:naming_proof(名称匹配守卫须经真实 execute_tool 生产命名点火证明)")
    errs += prov.validate_asset({**candidate, "credit_level": "T1_candidate", "status": "shadow"})
    return (not errs), errs


def birth(candidate: dict, production: bool = False) -> dict:
    """出生路径：通过门 → 登记为 **shadow**（拦截器在线运行但只记日志不否决）。
    写生产注册表须显式 production=True（DC-9；自检走 SA_REGISTRY_PATH 沙盒）。"""
    ok, errs = can_birth(candidate)
    if not ok:
        raise ValueError(f"[organ] birth rejected: {errs}")
    rec = dict(candidate)
    rec.update({"status": "shadow", "credit_level": "T1_candidate",
                "shadow_firings": 0, "shadow_misfires": 0})
    return prov.register_asset(rec, production=production)


def shadow_fire(asset_id: str, run_verdict: str, production: bool = False) -> dict:
    """影子期点火记账 → 自动毕业(active)或回炉(pending_revalidation)。"""
    return prov.shadow_event(asset_id, run_verdict, production=production)


# ---- 五环管线（MVP；ring_draft 是唯一允许 LLM 的格子）----
class Pipeline:
    def ring_mine(self, epoch: int) -> dict:
        """环1 开采（触发化）：批次落盘即跑（MVP 委托 p5a36 逻辑）。"""
        return {"ring": "mine", "epoch": epoch, "note": "见 scripts/p5a36_failure_mine.py"}

    # 死因 → 处置（确定性规则；校准用）
    #  reject   = 非过程陷阱（数据/能力/实现 bug）→ 拦截器拦不出
    #  deploy   = 可拦截 ∧ 直接可观测
    #  decompose= 可拦截但需先验观测（改写为前置强制型）→ 允许与人工分歧
    REJECT_SIG = ("user not found", "invoke()")
    DECOMPOSE_SIG = ("not enough seats", "gift card balance",
                     "not enough balance", "certificate cannot be used")

    def classify_disposition(self, pattern: dict) -> str:
        kind = pattern.get("kind")
        if kind in ("order_lock", "repeat_failure"):
            return "deploy"
        sig = (pattern.get("pattern_id") or "") + " " + " ".join(pattern.get("examples", []))
        low = sig.lower()
        if any(s in low for s in self.REJECT_SIG):
            return "reject"
        if any(s in low for s in self.DECOMPOSE_SIG):
            return "decompose"
        if kind == "tool_error":
            return "deploy"
        return "decompose"

    def ring_triage(self, patterns: List[dict]) -> List[dict]:
        """环2 分诊（全机检）：死因归类 + 可拦截性 + 处置。"""
        out = []
        for p in patterns:
            disp = self.classify_disposition(p)
            out.append({**p, "disposition": disp,
                        "interceptable": disp in ("deploy", "decompose"),
                        "observable": disp == "deploy"})
        return out

    def ring_draft(self, corpse_cluster: dict, llm=None) -> dict:
        """环3 谓词起草（**唯一 LLM 格子**）：尸体簇 → 谓词规格 + 干预语义初稿。
        MVP 无 LLM 时返回模板草稿；联调时才调 LLM（记小账）。"""
        if llm is None:
            return {"ring": "draft", "cluster": corpse_cluster.get("pattern_id"),
                    "spec": "<待 LLM 起草：点火规则 + 干预语义>", "llm_cell": True}
        return llm(corpse_cluster)

    def ring_canary(self, death_cases: List[dict], legit_shapes: List[dict]) -> dict:
        """环4 金丝雀（半自动）：死亡案例→阳性探针；合法形状库→阴性对照。"""
        return {"ring": "canary",
                "positive": [c.get("task_id") for c in death_cases][:5],
                "negative": [s.get("name") for s in legit_shapes][:5]}

    def ring_certify(self, asset_id: str, battery: str) -> dict:
        """环5 认证：C-1（已有，自动）。"""
        return {"ring": "certify", "asset_id": asset_id,
                "note": f"run scripts/c1_coldstart_gate.py --asset {asset_id} --battery {battery}"}
