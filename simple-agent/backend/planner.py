"""确定性极简线性规划器（P3 §5.0.0）。

不调用 LLM。把 task 文本切为**单链**节点序列（节点=预期动作步骤），
解析不出动作时退化为单节点。它是真实规划器（当前为退化形态），
用于让 B/C 段观测有真实数据源，而不是伪造 plan span。

step→node 映射规则（v2.2 §5.0.0）集中定义在 `Plan.node_for_step`，
未来多分支规划器落地时单点替换即可。
"""
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

MAX_NODES = 10

# 动作动词（按出现顺序切分步骤）
ACTION_VERBS = [
    "创建", "新建", "写入", "添加", "生成", "读取", "查看", "列出", "运行",
    "执行", "计算", "打印", "安装", "测试", "删除", "修改", "更新", "移动",
    "复制", "提交", "处理", "搜索", "查找", "下载", "上传", "编译", "构建",
]

# 文件路径 token（用于粗略 owns 归属）
_FILE_RE = re.compile(r"[\w\-./]+\.\w{1,6}")


@dataclass
class PlanNode:
    node_id: str
    action: str
    agent: str = "worker"
    deps: List[str] = field(default_factory=list)
    owns: List[str] = field(default_factory=list)


@dataclass
class Plan:
    plan_id: str
    req_id: Optional[str]
    nodes: List[PlanNode]
    planner_model: str = "deterministic-linear-v1"
    prompt_version: str = "n/a"

    def to_json(self) -> Dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": n.node_id,
                    "agent": n.agent,
                    "action": n.action,
                    "deps": list(n.deps),
                    "owns": list(n.owns),
                }
                for n in self.nodes
            ]
        }

    def node_for_step(self, step: int) -> str:
        """纯时间序对齐：第 k 步 → n{min(k, node_count-1)}。"""
        if not self.nodes:
            return "n0"
        return f"n{min(step, len(self.nodes) - 1)}"


def _extract_actions(text: str) -> List[str]:
    hits = []
    for verb in ACTION_VERBS:
        for m in re.finditer(re.escape(verb), text or ""):
            hits.append((m.start(), verb))
    hits.sort(key=lambda x: x[0])
    actions: List[str] = []
    for _, verb in hits:
        if actions and actions[-1] == verb:
            continue
        actions.append(verb)
    return actions[:MAX_NODES]


def make_plan(req: Any) -> Plan:
    text = getattr(req, "content", None) or (req.get("content") if isinstance(req, dict) else "") or ""
    req_id = getattr(req, "req_id", None) if not isinstance(req, dict) else req.get("req_id")
    files = _FILE_RE.findall(text or "")

    actions = _extract_actions(text)
    if not actions:
        nodes = [PlanNode(node_id="n0", action="fallback", owns=["workspace/"])]
    else:
        nodes = []
        for i, action in enumerate(actions):
            deps = [f"n{i - 1}"] if i > 0 else []
            owns = [files[i]] if i < len(files) else []
            nodes.append(PlanNode(node_id=f"n{i}", action=action, deps=deps, owns=owns))

    return Plan(plan_id=str(uuid.uuid4()), req_id=req_id, nodes=nodes)
