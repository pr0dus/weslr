from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class AgentState:
    name: str
    energy: int
    storage: int
    gpu_quota: int
    reputation: float
    last_inspect_at: int = 0
    last_trade_at: int = 0
    age_ticks: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ActionResult:
    action: str
    status: str
    summary: str
    energy_delta: int = 0
    storage_delta: int = 0
    reputation_delta: float = 0.0
    artifact: str | None = None
    module: str | None = None
    target: str | None = None
    raw_output: str = ""
