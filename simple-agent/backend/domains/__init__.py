"""P5a.45 §三.3 / P5a.44 §三.3：域包（DomainPack）——harness 域无关化。

一个域包描述该域接入多臂 harness/拦截器/脱敏所需的最小接口；τ 为一个已落地包，
代码域（E3）为待落地包。随机化/冻结/bootstrap/CopyGuard/运行表/ITT 逐字复用，不重写。
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass
class DomainPack:
    name: str
    mutating_tools: Set[str]
    transfer_tool: str
    read_prefixes: Tuple[str, ...]
    entity_field_class: Dict[str, str]
    interceptor_rules: List[dict] = field(default_factory=list)
    lock_scope_key: str = "order_id"
    description: str = ""


_REGISTRY: Dict[str, DomainPack] = {}


def register(pack: DomainPack) -> DomainPack:
    _REGISTRY[pack.name] = pack
    return pack


def get(name: str):
    return _REGISTRY.get(name)


def list_domains() -> List[str]:
    return list(_REGISTRY)


# 触发注册（导入即注册）
from . import tau as _tau      # noqa: E402,F401
from . import code as _code    # noqa: E402,F401
