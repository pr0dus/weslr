from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class WarrantRecord:
    warrant_type: str = ""
    source: str = ""
    explanation: str = ""
    confidence: str = ""
    deterministic: bool = False
    human_teachable: bool = True


@dataclass
class InferenceNode:
    node_id: str = ""
    node_type: str = ""
    content: str = ""
    confidence: str = ""
    source: str = ""
    supports: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)


@dataclass
class InferenceEdge:
    edge_id: str = ""
    from_node: str = ""
    to_node: str = ""
    relation_type: str = ""
    warrant: WarrantRecord = field(default_factory=WarrantRecord)
    confidence: str = ""


@dataclass
class SolverOutput:
    solver_id: str = ""
    solver_family: str = ""
    proposed_answer: str = ""
    confidence: str = ""
    explanation: str = ""
    nodes_created: list[str] = field(default_factory=list)
    conflicts_created: list[str] = field(default_factory=list)
    status: str = ""


@dataclass
class ConflictRecord:
    conflict_id: str = ""
    conflict_type: str = ""
    node_ids: list[str] = field(default_factory=list)
    explanation: str = ""
    severity: str = ""
    resolved: bool = False


@dataclass
class TraceLegibilityRecord:
    human_explanation_available: bool = True
    symbolic_forms_translated: bool = True
    private_authority_used: bool = False
    opaque_solver_output_used: bool = False
    explanation_notes: list[str] = field(default_factory=list)


@dataclass
class TraceAntiGamingRecord:
    uses_item_id: bool = False
    uses_answer_key: bool = False
    uses_answer_position_bias: bool = False
    stores_raw_question_by_default: bool = False
    official_score_claimed: bool = False


@dataclass
class ReasoningTrace:
    schema_version: str
    trace_id: str
    task_id: str
    task_family: str
    domain: str
    required_skill: str
    nodes: list[InferenceNode]
    edges: list[InferenceEdge]
    solver_outputs: list[SolverOutput]
    conflicts: list[ConflictRecord]
    selected_answer: str
    confidence: str
    uncertainty: str
    human_explanation: str
    anti_gaming: TraceAntiGamingRecord
    legibility: TraceLegibilityRecord
    failure_mode: str


def create_empty_reasoning_trace(
    *,
    trace_id: str = "",
    task_id: str = "",
    task_family: str = "",
    domain: str = "",
    required_skill: str = "",
    schema_version: str = "1.0",
) -> ReasoningTrace:
    return ReasoningTrace(
        schema_version=schema_version,
        trace_id=trace_id,
        task_id=task_id,
        task_family=task_family,
        domain=domain,
        required_skill=required_skill,
        nodes=[],
        edges=[],
        solver_outputs=[],
        conflicts=[],
        selected_answer="",
        confidence="",
        uncertainty="",
        human_explanation="",
        anti_gaming=TraceAntiGamingRecord(),
        legibility=TraceLegibilityRecord(),
        failure_mode="",
    )


def reasoning_trace_to_dict(trace: ReasoningTrace) -> dict[str, Any]:
    return asdict(trace)


def reasoning_trace_from_dict(data: dict[str, Any]) -> ReasoningTrace:
    return ReasoningTrace(
        schema_version=data.get("schema_version", ""),
        trace_id=data.get("trace_id", ""),
        task_id=data.get("task_id", ""),
        task_family=data.get("task_family", ""),
        domain=data.get("domain", ""),
        required_skill=data.get("required_skill", ""),
        nodes=[InferenceNode(**item) for item in data.get("nodes", [])],
        edges=[
            InferenceEdge(
                edge_id=item.get("edge_id", ""),
                from_node=item.get("from_node", ""),
                to_node=item.get("to_node", ""),
                relation_type=item.get("relation_type", ""),
                warrant=WarrantRecord(**item.get("warrant", {})),
                confidence=item.get("confidence", ""),
            )
            for item in data.get("edges", [])
        ],
        solver_outputs=[SolverOutput(**item) for item in data.get("solver_outputs", [])],
        conflicts=[ConflictRecord(**item) for item in data.get("conflicts", [])],
        selected_answer=data.get("selected_answer", ""),
        confidence=data.get("confidence", ""),
        uncertainty=data.get("uncertainty", ""),
        human_explanation=data.get("human_explanation", ""),
        anti_gaming=TraceAntiGamingRecord(**data.get("anti_gaming", {})),
        legibility=TraceLegibilityRecord(**data.get("legibility", {})),
        failure_mode=data.get("failure_mode", ""),
    )


def add_inference_node(
    trace: ReasoningTrace,
    *,
    node_id: str,
    node_type: str,
    content: str,
    confidence: str = "",
    source: str = "",
    supports: list[str] | None = None,
    violations: list[str] | None = None,
    uncertainties: list[str] | None = None,
) -> InferenceNode:
    node = InferenceNode(
        node_id=node_id,
        node_type=node_type,
        content=content,
        confidence=confidence,
        source=source,
        supports=list(supports or []),
        violations=list(violations or []),
        uncertainties=list(uncertainties or []),
    )
    trace.nodes.append(node)
    return node


def add_inference_edge(
    trace: ReasoningTrace,
    *,
    edge_id: str,
    from_node: str,
    to_node: str,
    relation_type: str,
    warrant: WarrantRecord,
    confidence: str = "",
) -> InferenceEdge:
    edge = InferenceEdge(
        edge_id=edge_id,
        from_node=from_node,
        to_node=to_node,
        relation_type=relation_type,
        warrant=warrant,
        confidence=confidence,
    )
    trace.edges.append(edge)
    return edge


def add_solver_output(
    trace: ReasoningTrace,
    *,
    solver_id: str,
    solver_family: str,
    proposed_answer: str,
    confidence: str = "",
    explanation: str = "",
    nodes_created: list[str] | None = None,
    conflicts_created: list[str] | None = None,
    status: str = "",
) -> SolverOutput:
    output = SolverOutput(
        solver_id=solver_id,
        solver_family=solver_family,
        proposed_answer=proposed_answer,
        confidence=confidence,
        explanation=explanation,
        nodes_created=list(nodes_created or []),
        conflicts_created=list(conflicts_created or []),
        status=status,
    )
    trace.solver_outputs.append(output)
    return output


def add_conflict(
    trace: ReasoningTrace,
    *,
    conflict_id: str,
    conflict_type: str,
    node_ids: list[str],
    explanation: str,
    severity: str = "",
    resolved: bool = False,
) -> ConflictRecord:
    conflict = ConflictRecord(
        conflict_id=conflict_id,
        conflict_type=conflict_type,
        node_ids=list(node_ids),
        explanation=explanation,
        severity=severity,
        resolved=resolved,
    )
    trace.conflicts.append(conflict)
    return conflict


def validate_reasoning_trace(trace: ReasoningTrace) -> list[str]:
    messages: list[str] = []

    if not trace.task_id:
        messages.append("trace with no task_id is not allowed")

    node_ids = set()
    for node in trace.nodes:
        if not node.node_id:
            messages.append("node with empty node_id is not allowed")
            continue
        node_ids.add(node.node_id)

    anti = trace.anti_gaming
    if anti.official_score_claimed:
        messages.append("official_score_claimed true is not allowed")
    if anti.uses_answer_key:
        messages.append("uses_answer_key true is not allowed")
    if anti.uses_item_id:
        messages.append("uses_item_id true is not allowed")
    if anti.stores_raw_question_by_default:
        messages.append("stores_raw_question_by_default true is not allowed")

    legibility = trace.legibility
    if legibility.private_authority_used:
        messages.append("private_authority_used true is not allowed")
    if legibility.opaque_solver_output_used:
        messages.append("opaque_solver_output_used true is not allowed")

    for edge in trace.edges:
        if edge.from_node not in node_ids or edge.to_node not in node_ids:
            messages.append(
                f"edge references missing nodes: {edge.edge_id or '<missing-edge-id>'}"
            )
        if not edge.warrant.explanation:
            messages.append(
                f"warrant missing explanation for edge: {edge.edge_id or '<missing-edge-id>'}"
            )

    for conflict in trace.conflicts:
        missing = [node_id for node_id in conflict.node_ids if node_id not in node_ids]
        if missing:
            messages.append(
                f"conflict references missing nodes: {conflict.conflict_id or '<missing-conflict-id>'}"
            )

    return messages


__all__ = [
    "ReasoningTrace",
    "InferenceNode",
    "InferenceEdge",
    "SolverOutput",
    "ConflictRecord",
    "WarrantRecord",
    "TraceLegibilityRecord",
    "TraceAntiGamingRecord",
    "create_empty_reasoning_trace",
    "reasoning_trace_to_dict",
    "reasoning_trace_from_dict",
    "validate_reasoning_trace",
    "add_inference_node",
    "add_inference_edge",
    "add_solver_output",
    "add_conflict",
]
