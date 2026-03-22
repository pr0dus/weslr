from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


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
    next_due_tick: int = 0
    wake_reason: str = "initial"
    cadence_interval: int = 1

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


@dataclass
class NeedState:
    id: str
    title: str
    kind: str
    description: str
    origin: str
    scope: str
    pressure: float
    novelty: float
    status: str
    created_at: int
    updated_at: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MessageState:
    id: str
    from_agent: str
    to_agent: str
    kind: str
    theme: str
    content: str
    created_at: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PublicMemoryState:
    id: str
    title: str
    kind: str
    content: str
    source: str
    stability: float
    created_at: int
    updated_at: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectState:
    id: str
    name: str
    purpose: str
    status: str
    owners: List[str]
    created_at: int
    updated_at: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RelationshipState:
    source_agent: str
    target_agent: str
    trust: float
    usefulness: float
    friction: float
    last_event: str
    updated_at: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SelfModificationProposalState:
    id: str
    agent_id: str
    created_at: int
    target_path: str
    scope: str
    pressure_source: str
    problem_summary: str
    proposed_change: str
    expected_benefit: str
    risk_level: str
    checkpoint_ref: str
    status: str
    validation_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkItemState:
    id: str
    title: str
    status: str
    priority: float
    owner: str
    created_at: int
    project_id: str
    need_id: str
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CommunicatorState:
    name: str
    status: str
    current_intent: str
    active_pursuit: str
    unresolved_question: str
    curiosity_target: str
    attraction_bias: str
    avoidance_bias: str
    curiosity: float
    dominant_need: str
    last_decision_summary: str
    intent_history: List[str]
    question_history: List[str]
    unresolved_objections: List[str]
    last_wake_at: int
    updated_at: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentState:
    id: str
    title: str
    hypothesis: str
    owner: str
    status: str
    created_at: int
    related_need: str
    project_id: str
    observations: str
    follow_up: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
