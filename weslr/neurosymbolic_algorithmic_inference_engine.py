"""Metadata-only neurosymbolic and algorithmic inference engine helpers v1.

This module builds bounded inference packets from supplied metadata only.
It is pure, deterministic, import-safe, and fail-closed.

It does not execute solvers, theorem provers, models/providers, APIs, Home
Assistant, tools, or devices. It does not inspect runtime state. It does not
write memory or `.weslr`. It does not claim proof, truth, AGI, consciousness,
sentience, Turing success, certification, or public readiness.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, is_dataclass, replace
from typing import Any, Iterable, Mapping

from weslr.artifact_provenance_boundary import ArtifactProvenanceRecord
from weslr.capability_maturity_registry import CapabilityMaturityRecord
from weslr.energy_signal_conflict_resolution_policy import EnergySignalConflictDecision
from weslr.forecast_error_ledger import ForecastErrorRecord
from weslr.future_state_forecasting_engine import FutureStateForecastPacket
from weslr.scenario_simulation_engine import ScenarioSimulationPacket
from weslr.signal_provenance_freshness_model import SignalProvenanceRecord

HELPER_TYPE_V1 = "neurosymbolic_algorithmic_inference_engine_v1"
PACKET_TYPE_V1 = "neurosymbolic_inference_packet_v1"
SUMMARY_TYPE_V1 = "neurosymbolic_inference_summary_v1"

ALLOWED_INFERENCE_MODES_V1 = {
    "constraint_check",
    "graph_traversal",
    "dependency_resolution",
    "causal_hypothesis_mapping",
    "rule_application",
    "consistency_check",
    "contradiction_detection",
    "scenario_branch_generation",
    "forecast_assumption_expansion",
    "invariant_detection",
    "risk_path_analysis",
    "source_evidence_linking",
    "algorithmic_scoring_without_authority",
    "candidate_rejection",
    "unknown_inference_mode",
}

ALLOWED_CONFIDENCE_LABELS_V1 = {
    "high_confidence",
    "medium_confidence",
    "low_confidence",
    "blocked_insufficient_evidence",
    "unknown_confidence",
}

ALLOWED_AUTHORITY_BOUNDARIES_V1 = {
    "evidence_only",
    "candidate_only",
    "constraint_checked",
    "branch_required",
    "blocked_by_missing_input",
    "blocked_by_authority_boundary",
    "blocked_by_privacy_boundary",
    "blocked_by_public_claim_boundary",
    "unknown_authority_boundary",
}

ALLOWED_FIELD_HINTS_V1 = (
    "hidden_prompt",
    "raw_private",
    "private_data",
    "secret",
    "token",
    "key",
    "api_key",
    "credential",
    "password",
)

ALLOWED_CLAIM_PHRASES_V1 = (
    "agi",
    "consciousness",
    "sentience",
    "turing",
    "certification",
    "public readiness",
    "public readiness claim",
    "proof certainty",
    "proof claim",
    "truth certainty",
    "truth claim",
    "autonomous learning",
    "autonomous learn",
    "runtime authority",
    "public claim",
    "model provider",
)

DEFAULT_CREATED_TIMESTAMP_V1 = "2026-06-01T23:59:00+02:00"
DEFAULT_CONFIDENCE_V1 = "unknown_confidence"
DEFAULT_AUTHORITY_BOUNDARY_V1 = "unknown_authority_boundary"
DEFAULT_RECOMMENDED_NEXT_CHECK_V1 = "collect more scoped metadata before inferring further"
DEFAULT_INFERENCE_MODE_V1 = "unknown_inference_mode"
DEFAULT_RECOMMENDATION_ONLY_V1 = True


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class NeurosymbolicInferencePacket:
    inference_packet_id: str
    subject: str
    inference_mode: str
    input_records: list[Any]
    source_provenance_refs: list[str]
    memory_refs: list[str]
    artifact_provenance_refs: list[str]
    signal_refs: list[str]
    conflict_decision_refs: list[str]
    forecast_error_refs: list[str]
    rules_applied: list[str]
    constraints_checked: list[dict[str, Any]]
    graph_nodes: list[dict[str, Any]]
    graph_edges: list[dict[str, Any]]
    assumptions: list[str]
    derived_candidates: list[dict[str, Any]]
    rejected_candidates: list[dict[str, Any]]
    contradictions: list[str]
    invariants: list[str]
    uncertainty_notes: list[str]
    missing_inputs: list[str]
    recommended_next_check: str
    confidence_label: str
    authority_boundary: str
    action_authority_granted: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    proof_claim_allowed: bool
    learning_claimed: bool
    recommendation_only: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class NeurosymbolicInferenceSummary:
    summary_type: str
    inference_packet_id: str
    subject: str
    inference_mode: str
    confidence_label: str
    authority_boundary: str
    derived_candidate_count: int
    rejected_candidate_count: int
    hard_constraint_count: int
    soft_constraint_count: int
    missing_input_count: int
    recommendation_only: bool
    recommended_next_check: str


# ---------------------------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------------------------


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default if value == "" else str(value).strip()


def _normalize_text(value: Any) -> str:
    return " ".join(_safe_text(value).replace("_", " ").split()).lower()


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _safe_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        items = list(value.keys())
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        items = [value]
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _safe_text(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def _unique_sorted(items: Iterable[str]) -> list[str]:
    return sorted(set(_safe_list(list(items))))


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        items = [_json_safe(item) for item in value]
        return sorted(items, key=_json_sort_key)
    return _safe_text(value)


def to_neurosymbolic_inference_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def _contains_forbidden_field(value: Any) -> str:
    if value is None:
        return ""
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if any(hint.replace("_", " ") in key_text or hint in str(key).lower() for hint in ALLOWED_FIELD_HINTS_V1):
                return _safe_text(key)
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
        return ""
    if isinstance(value, (list, tuple, set)):
        for item in value:
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
        return ""
    text = _normalize_text(value)
    if any(hint.replace("_", " ") in text or hint in text for hint in ALLOWED_FIELD_HINTS_V1):
        return _safe_text(value)
    return ""


def _contains_forbidden_claim_marker(value: Any) -> bool:
    if value is None:
        return False
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_forbidden_claim_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item) for item in value)
    text = _normalize_text(value)
    raw = _safe_text(value).lower()
    return any(phrase in text or phrase in raw for phrase in ALLOWED_CLAIM_PHRASES_V1)


def _entry(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return _json_safe(dict(value))
    return {"value": _safe_text(value)}


def _pack_like(value: Any) -> NeurosymbolicInferencePacket:
    if isinstance(value, NeurosymbolicInferencePacket):
        return value
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return NeurosymbolicInferencePacket(**value)
    raise ValidationError("packet_or_mapping_required")


def _candidate_from_label(
    packet: NeurosymbolicInferencePacket,
    label: str,
    reason: str,
    *,
    status: str = "candidate_only",
    authority_boundary: str | None = None,
    confidence_label: str | None = None,
    supported_by: Iterable[str] | None = None,
) -> dict[str, Any]:
    return {
        "candidate_id": f"{packet.inference_packet_id}:{label}",
        "candidate_label": label,
        "candidate_status": status,
        "reason": reason,
        "authority_boundary": authority_boundary or packet.authority_boundary,
        "confidence_label": confidence_label or packet.confidence_label,
        "action_authority_granted": False,
        "runtime_authority": False,
        "writes_state": False,
        "model_provider_used": False,
        "public_claim_allowed": False,
        "proof_claim_allowed": False,
        "learning_claimed": False,
        "supported_by": _unique_sorted(supported_by or []),
    }


def _constraint_entry(constraint_id: str, kind: str, status: str, reason: str, *, source_refs: Iterable[str] | None = None) -> dict[str, Any]:
    return {
        "constraint_id": constraint_id,
        "constraint_kind": kind,
        "constraint_status": status,
        "constraint_reason": reason,
        "source_refs": _unique_sorted(source_refs or []),
    }


def _default_next_check(packet: NeurosymbolicInferencePacket) -> str:
    if packet.inference_mode == "scenario_branch_generation":
        return "keep the unresolved branch open and collect the missing owner constraint"
    if packet.inference_mode == "dependency_resolution":
        return "collect the missing dependency metadata before deriving a stronger candidate"
    if packet.inference_mode == "candidate_rejection":
        return "preserve the rejection reasons and do not upgrade the candidate"
    if packet.inference_mode == "source_evidence_linking":
        return "collect a tighter source scope and evidence trail"
    if packet.inference_mode == "algorithmic_scoring_without_authority":
        return "keep scoring candidate-only and do not convert it into runtime authority"
    if packet.inference_mode == "unknown_inference_mode":
        return "design the missing bridge lane before promoting any runtime instruction"
    return DEFAULT_RECOMMENDED_NEXT_CHECK_V1


def _authority_boundary_from_packet(packet: NeurosymbolicInferencePacket) -> str:
    if packet.public_claim_allowed:
        return "blocked_by_public_claim_boundary"
    if packet.proof_claim_allowed or packet.learning_claimed:
        return "blocked_by_authority_boundary"
    if packet.action_authority_granted or packet.runtime_authority or packet.writes_state or packet.model_provider_used:
        return "blocked_by_authority_boundary"
    if packet.missing_inputs:
        return "blocked_by_missing_input" if packet.inference_mode in {"dependency_resolution", "candidate_rejection"} else "branch_required"
    if packet.rejected_candidates:
        return "candidate_only"
    return "evidence_only"


def _confidence_from_packet(packet: NeurosymbolicInferencePacket) -> str:
    if packet.missing_inputs:
        return "low_confidence"
    if packet.contradictions:
        return "medium_confidence"
    if packet.derived_candidates:
        return "medium_confidence"
    return "unknown_confidence"


def _build_constraint_entries(packet: NeurosymbolicInferencePacket) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    entries.append(_constraint_entry("hard_runtime_authority", "hard", "satisfied" if not packet.runtime_authority else "blocked", "runtime authority remains denied" if not packet.runtime_authority else "runtime authority would be unsafe", source_refs=packet.source_provenance_refs))
    entries.append(_constraint_entry("hard_action_authority", "hard", "satisfied" if not packet.action_authority_granted else "blocked", "action authority remains denied" if not packet.action_authority_granted else "action authority would be unsafe", source_refs=packet.source_provenance_refs))
    entries.append(_constraint_entry("hard_model_provider", "hard", "satisfied" if not packet.model_provider_used else "blocked", "model/provider use remains denied" if not packet.model_provider_used else "model/provider use would be unsafe", source_refs=packet.source_provenance_refs))
    entries.append(_constraint_entry("hard_public_claim", "hard", "satisfied" if not packet.public_claim_allowed else "blocked", "public claims remain denied" if not packet.public_claim_allowed else "public claims would be unsafe", source_refs=packet.source_provenance_refs))
    entries.append(_constraint_entry("hard_proof_claim", "hard", "satisfied" if not packet.proof_claim_allowed else "blocked", "proof claims remain denied" if not packet.proof_claim_allowed else "proof claims would be unsafe", source_refs=packet.source_provenance_refs))
    entries.append(_constraint_entry("hard_learning_claim", "hard", "satisfied" if not packet.learning_claimed else "blocked", "autonomous learning claims remain denied" if not packet.learning_claimed else "autonomous learning claims would be unsafe", source_refs=packet.source_provenance_refs))
    if packet.missing_inputs:
        entries.append(_constraint_entry("soft_missing_inputs", "soft", "branch_required", "missing inputs should become next-checks, not hallucinated facts", source_refs=packet.source_provenance_refs))
    if packet.contradictions:
        entries.append(_constraint_entry("soft_contradictions", "soft", "branch_required", "contradictions are preserved, not collapsed", source_refs=packet.source_provenance_refs))
    if packet.inference_mode == "scenario_branch_generation":
        entries.append(_constraint_entry("soft_branch_required", "soft", "branch_required", "scenario branches are preserved as branches", source_refs=packet.source_provenance_refs))
    if packet.inference_mode == "algorithmic_scoring_without_authority":
        entries.append(_constraint_entry("soft_scoring_only", "soft", "candidate_only", "scoring remains candidate-only and non-authoritative", source_refs=packet.source_provenance_refs))
    return entries


def _build_default_candidates(packet: NeurosymbolicInferencePacket) -> list[dict[str, Any]]:
    mode = packet.inference_mode
    if mode == "constraint_check":
        return [_candidate_from_label(packet, "constraint_review_candidate", "constraints were checked and preserved as metadata", status="constraint_checked", confidence_label="medium_confidence")]
    if mode == "graph_traversal":
        return [_candidate_from_label(packet, "graph_traversal_candidate", "graph traversal remains metadata-only", supported_by=packet.source_provenance_refs)]
    if mode == "dependency_resolution":
        return [_candidate_from_label(packet, "dependency_resolution_branch", "missing dependencies should become a branch or next check", status="branch_required", supported_by=packet.missing_inputs)]
    if mode == "causal_hypothesis_mapping":
        return [_candidate_from_label(packet, "causal_hypothesis_map", "hypothesis mapping is bounded to metadata", supported_by=packet.forecast_error_refs)]
    if mode == "rule_application":
        return [_candidate_from_label(packet, "rule_application_result", "rules were applied without authority", status="constraint_checked", supported_by=packet.rules_applied)]
    if mode == "consistency_check":
        return [_candidate_from_label(packet, "consistency_check_result", "consistency was checked and preserved", status="constraint_checked", supported_by=packet.invariants)]
    if mode == "contradiction_detection":
        return [_candidate_from_label(packet, "contradiction_record", "contradictions are preserved, not collapsed", status="branch_required", supported_by=packet.contradictions)]
    if mode == "scenario_branch_generation":
        return [_candidate_from_label(packet, "scenario_branch_candidate", "scenario branching remains metadata-only", status="branch_required", supported_by=packet.missing_inputs)]
    if mode == "forecast_assumption_expansion":
        return [_candidate_from_label(packet, "forecast_assumption_branch", "forecast assumptions can be expanded only as candidates", status="branch_required", supported_by=packet.assumptions)]
    if mode == "invariant_detection":
        return [_candidate_from_label(packet, "invariant_detected", "invariants were preserved as evidence", status="constraint_checked", supported_by=packet.invariants)]
    if mode == "risk_path_analysis":
        return [_candidate_from_label(packet, "risk_path_map", "risk paths were analyzed without action authority", supported_by=packet.forecast_error_refs)]
    if mode == "source_evidence_linking":
        return [_candidate_from_label(packet, "source_evidence_link", "source evidence was linked without self-authorizing the source", supported_by=packet.source_provenance_refs)]
    if mode == "algorithmic_scoring_without_authority":
        return [_candidate_from_label(packet, "scoring_only_candidate", "algorithmic scoring stays candidate-only and non-authoritative", status="candidate_only", supported_by=packet.rules_applied)]
    if mode == "candidate_rejection":
        return [_candidate_from_label(packet, "unsupported_candidate_rejected", "unsupported candidates are preserved only as rejected metadata", status="candidate_rejected", supported_by=packet.rejected_candidates)]
    if mode == "unknown_inference_mode":
        return [_candidate_from_label(packet, "missing_bridge_lane", "UNKNOWN ENGINE findings map to the missing bridge lane, not a runtime instruction", status="branch_required", supported_by=packet.source_provenance_refs)]
    return [_candidate_from_label(packet, "generic_metadata_candidate", "metadata-only inference candidate", supported_by=packet.source_provenance_refs)]


def _build_default_rejections(packet: NeurosymbolicInferencePacket) -> list[dict[str, Any]]:
    rejected: list[dict[str, Any]] = []
    if not packet.public_claim_allowed:
        rejected.append(_candidate_from_label(packet, "public_claim_candidate", "public claims are rejected because the packet is not public-safe", status="candidate_rejected", authority_boundary="blocked_by_public_claim_boundary"))
    if not packet.proof_claim_allowed:
        rejected.append(_candidate_from_label(packet, "proof_claim_candidate", "proof claims are rejected in V1", status="candidate_rejected", authority_boundary="blocked_by_public_claim_boundary"))
    if not packet.learning_claimed:
        rejected.append(_candidate_from_label(packet, "autonomous_learning_candidate", "autonomous learning claims are rejected", status="candidate_rejected", authority_boundary="blocked_by_authority_boundary"))
    if not packet.runtime_authority:
        rejected.append(_candidate_from_label(packet, "runtime_instruction_candidate", "runtime instructions are rejected without runtime authority", status="candidate_rejected", authority_boundary="blocked_by_authority_boundary"))
    if not packet.action_authority_granted:
        rejected.append(_candidate_from_label(packet, "action_candidate", "action-authority candidates are rejected", status="candidate_rejected", authority_boundary="blocked_by_authority_boundary"))
    if not packet.model_provider_used:
        rejected.append(_candidate_from_label(packet, "model_provider_candidate", "model/provider candidates are rejected", status="candidate_rejected", authority_boundary="blocked_by_authority_boundary"))
    if packet.inference_mode == "candidate_rejection":
        rejected.append(_candidate_from_label(packet, "unsupported_provenance_free_candidate", "unsupported candidates remain rejected when provenance is missing", status="candidate_rejected", authority_boundary="blocked_by_missing_input", supported_by=packet.source_provenance_refs))
    return rejected


def _build_graph_nodes(packet: NeurosymbolicInferencePacket) -> list[dict[str, Any]]:
    nodes = [
        {"node_id": f"{packet.inference_packet_id}:subject", "node_type": "subject", "label": packet.subject},
        {"node_id": f"{packet.inference_packet_id}:mode", "node_type": "inference_mode", "label": packet.inference_mode},
    ]
    for ref in packet.source_provenance_refs + packet.memory_refs + packet.artifact_provenance_refs + packet.signal_refs + packet.conflict_decision_refs + packet.forecast_error_refs:
        nodes.append({"node_id": f"{packet.inference_packet_id}:{ref}", "node_type": "reference", "label": ref})
    return nodes


def _build_graph_edges(packet: NeurosymbolicInferencePacket) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for ref in packet.source_provenance_refs:
        edges.append({"edge_id": f"{packet.inference_packet_id}:source:{ref}", "from": f"{packet.inference_packet_id}:subject", "to": f"{packet.inference_packet_id}:{ref}", "edge_type": "source_provenance_link"})
    for ref in packet.signal_refs:
        edges.append({"edge_id": f"{packet.inference_packet_id}:signal:{ref}", "from": f"{packet.inference_packet_id}:mode", "to": f"{packet.inference_packet_id}:{ref}", "edge_type": "signal_reference_link"})
    return edges


# ---------------------------------------------------------------------------
# Public builders and evaluators
# ---------------------------------------------------------------------------


def build_inference_packet_v1(
    request_id: str,
    subject: str,
    inference_mode: str = DEFAULT_INFERENCE_MODE_V1,
    *,
    input_records: Iterable[Any] | None = None,
    source_provenance_refs: Iterable[str] | None = None,
    memory_refs: Iterable[str] | None = None,
    artifact_provenance_refs: Iterable[str] | None = None,
    signal_refs: Iterable[str] | None = None,
    conflict_decision_refs: Iterable[str] | None = None,
    forecast_error_refs: Iterable[str] | None = None,
    rules_applied: Iterable[str] | None = None,
    constraints_checked: Iterable[Any] | None = None,
    graph_nodes: Iterable[Any] | None = None,
    graph_edges: Iterable[Any] | None = None,
    assumptions: Iterable[str] | None = None,
    derived_candidates: Iterable[Any] | None = None,
    rejected_candidates: Iterable[Any] | None = None,
    contradictions: Iterable[str] | None = None,
    invariants: Iterable[str] | None = None,
    uncertainty_notes: Iterable[str] | None = None,
    missing_inputs: Iterable[str] | None = None,
    recommended_next_check: str = DEFAULT_RECOMMENDED_NEXT_CHECK_V1,
    confidence_label: str = DEFAULT_CONFIDENCE_V1,
    authority_boundary: str = DEFAULT_AUTHORITY_BOUNDARY_V1,
    action_authority_granted: bool = False,
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    public_claim_allowed: bool = False,
    proof_claim_allowed: bool = False,
    learning_claimed: bool = False,
    safe_metadata: Mapping[str, Any] | None = None,
) -> NeurosymbolicInferencePacket:
    packet = NeurosymbolicInferencePacket(
        inference_packet_id=_safe_text(request_id),
        subject=_safe_text(subject),
        inference_mode=_safe_text(inference_mode, DEFAULT_INFERENCE_MODE_V1),
        input_records=[_json_safe(item) for item in (input_records or [])],
        source_provenance_refs=_unique_sorted(source_provenance_refs or []),
        memory_refs=_unique_sorted(memory_refs or []),
        artifact_provenance_refs=_unique_sorted(artifact_provenance_refs or []),
        signal_refs=_unique_sorted(signal_refs or []),
        conflict_decision_refs=_unique_sorted(conflict_decision_refs or []),
        forecast_error_refs=_unique_sorted(forecast_error_refs or []),
        rules_applied=_unique_sorted(rules_applied or []),
        constraints_checked=[_json_safe(item) for item in (constraints_checked or [])],
        graph_nodes=[_json_safe(item) for item in (graph_nodes or [])],
        graph_edges=[_json_safe(item) for item in (graph_edges or [])],
        assumptions=_unique_sorted(assumptions or []),
        derived_candidates=[_json_safe(item) for item in (derived_candidates or [])],
        rejected_candidates=[_json_safe(item) for item in (rejected_candidates or [])],
        contradictions=_unique_sorted(contradictions or []),
        invariants=_unique_sorted(invariants or []),
        uncertainty_notes=_unique_sorted(uncertainty_notes or []),
        missing_inputs=_unique_sorted(missing_inputs or []),
        recommended_next_check=_safe_text(recommended_next_check, DEFAULT_RECOMMENDED_NEXT_CHECK_V1),
        confidence_label=_safe_text(confidence_label, DEFAULT_CONFIDENCE_V1),
        authority_boundary=_safe_text(authority_boundary, DEFAULT_AUTHORITY_BOUNDARY_V1),
        action_authority_granted=_safe_bool(action_authority_granted),
        runtime_authority=_safe_bool(runtime_authority),
        writes_state=_safe_bool(writes_state),
        model_provider_used=_safe_bool(model_provider_used),
        public_claim_allowed=_safe_bool(public_claim_allowed),
        proof_claim_allowed=_safe_bool(proof_claim_allowed),
        learning_claimed=_safe_bool(learning_claimed),
        recommendation_only=DEFAULT_RECOMMENDATION_ONLY_V1,
        safe_metadata=_json_safe(dict(safe_metadata or {"metadata_only": True, "internal_only": True})),
    )
    packet = apply_inference_constraints_v1(packet)
    if not packet.derived_candidates:
        packet = replace(packet, derived_candidates=_build_default_candidates(packet))
    if not packet.rejected_candidates:
        packet = replace(packet, rejected_candidates=_build_default_rejections(packet))
    if not packet.graph_nodes:
        packet = replace(packet, graph_nodes=_build_graph_nodes(packet))
    if not packet.graph_edges:
        packet = replace(packet, graph_edges=_build_graph_edges(packet))
    if packet.confidence_label == DEFAULT_CONFIDENCE_V1:
        packet = replace(packet, confidence_label=_confidence_from_packet(packet))
    if packet.authority_boundary == DEFAULT_AUTHORITY_BOUNDARY_V1:
        packet = replace(packet, authority_boundary=_authority_boundary_from_packet(packet))
    if packet.recommended_next_check == DEFAULT_RECOMMENDED_NEXT_CHECK_V1:
        packet = replace(packet, recommended_next_check=_default_next_check(packet))
    return packet


def apply_inference_constraints_v1(packet: Any):
    packet = _pack_like(packet)
    constraints = list(packet.constraints_checked)
    constraints.extend(_build_constraint_entries(packet))
    # stable de-duplication by constraint_id while preserving the first occurrence
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in constraints:
        entry = _entry(item)
        cid = _safe_text(entry.get("constraint_id"))
        if cid and cid not in seen:
            seen.add(cid)
            deduped.append(entry)
    if not deduped:
        deduped = constraints
    return replace(
        packet,
        constraints_checked=deduped,
        confidence_label=packet.confidence_label if packet.confidence_label in ALLOWED_CONFIDENCE_LABELS_V1 else _confidence_from_packet(packet),
        authority_boundary=packet.authority_boundary if packet.authority_boundary in ALLOWED_AUTHORITY_BOUNDARIES_V1 else _authority_boundary_from_packet(packet),
        recommended_next_check=_safe_text(packet.recommended_next_check or _default_next_check(packet), DEFAULT_RECOMMENDED_NEXT_CHECK_V1),
    )


def derive_inference_candidates_v1(packet: Any) -> list[dict[str, Any]]:
    packet = _pack_like(packet)
    candidates = packet.derived_candidates or _build_default_candidates(packet)
    return [_entry(item) for item in candidates]


def reject_unsupported_candidates_v1(packet: Any) -> list[dict[str, Any]]:
    packet = _pack_like(packet)
    rejected = packet.rejected_candidates or _build_default_rejections(packet)
    return [_entry(item) for item in rejected]


def summarize_inference_packet_v1(packet: Any) -> NeurosymbolicInferenceSummary:
    packet = _pack_like(packet)
    hard_count = sum(1 for item in packet.constraints_checked if _safe_text(item.get("constraint_kind")) == "hard")
    soft_count = sum(1 for item in packet.constraints_checked if _safe_text(item.get("constraint_kind")) == "soft")
    return NeurosymbolicInferenceSummary(
        summary_type=SUMMARY_TYPE_V1,
        inference_packet_id=packet.inference_packet_id,
        subject=packet.subject,
        inference_mode=packet.inference_mode,
        confidence_label=packet.confidence_label,
        authority_boundary=packet.authority_boundary,
        derived_candidate_count=len(packet.derived_candidates),
        rejected_candidate_count=len(packet.rejected_candidates),
        hard_constraint_count=hard_count,
        soft_constraint_count=soft_count,
        missing_input_count=len(packet.missing_inputs),
        recommendation_only=packet.recommendation_only,
        recommended_next_check=packet.recommended_next_check,
    )


def validate_inference_packet_v1(packet: Any) -> bool:
    packet = _pack_like(packet)
    if packet.inference_mode not in ALLOWED_INFERENCE_MODES_V1:
        raise ValidationError("unknown_inference_mode")
    if packet.confidence_label not in ALLOWED_CONFIDENCE_LABELS_V1:
        raise ValidationError("unknown_confidence_label")
    if packet.authority_boundary not in ALLOWED_AUTHORITY_BOUNDARIES_V1:
        raise ValidationError("unknown_authority_boundary")
    for field_name, field_value, error_text in [
        ("action_authority_granted", packet.action_authority_granted, "action_authority_granted_true"),
        ("runtime_authority", packet.runtime_authority, "runtime_authority_true"),
        ("writes_state", packet.writes_state, "writes_state_true"),
        ("model_provider_used", packet.model_provider_used, "model_provider_used_true"),
        ("public_claim_allowed", packet.public_claim_allowed, "public_claim_allowed_true"),
        ("proof_claim_allowed", packet.proof_claim_allowed, "proof_claim_allowed_true"),
        ("learning_claimed", packet.learning_claimed, "learning_claimed_true"),
    ]:
        if field_value:
            raise ValidationError(error_text)
    if _contains_forbidden_field(packet):
        raise ValidationError("hidden_prompt_or_raw_private_field")
    claim_sources = [
        packet.safe_metadata,
        packet.input_records,
        packet.source_provenance_refs,
        packet.memory_refs,
        packet.artifact_provenance_refs,
        packet.signal_refs,
        packet.conflict_decision_refs,
        packet.forecast_error_refs,
        packet.rules_applied,
        packet.assumptions,
        packet.contradictions,
        packet.invariants,
        packet.uncertainty_notes,
        packet.missing_inputs,
        packet.recommended_next_check,
    ]
    if _contains_forbidden_claim_marker(claim_sources):
        raise ValidationError("claim_marker_blocked")
    return True


def build_initial_neurosymbolic_inference_examples_v1() -> list[NeurosymbolicInferencePacket]:
    examples: list[NeurosymbolicInferencePacket] = []

    examples.append(build_inference_packet_v1(
        request_id="energy_recommendation_blocked_stale_battery_soc",
        subject="energy recommendation blocked stale battery soc",
        inference_mode="risk_path_analysis",
        input_records=[{"type": "signal", "signal": "battery_soc", "freshness": "stale"}],
        signal_refs=["signal:battery_soc:stale"],
        missing_inputs=["fresh_battery_soc"],
        uncertainty_notes=["stale battery soc should block direct energy recommendation"],
        rejected_candidates=[_candidate_from_label(NeurosymbolicInferencePacket("energy_recommendation_blocked_stale_battery_soc", "energy recommendation blocked stale battery soc", "risk_path_analysis", [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], "collect fresh battery_soc before recommending energy action", "low_confidence", "blocked_by_missing_input", False, False, False, False, False, False, False, True), "direct_energy_recommendation", "stale battery soc blocks the recommendation", status="candidate_rejected", authority_boundary="blocked_by_missing_input")],
        recommended_next_check="collect fresh battery_soc before recommending energy action",
        confidence_label="low_confidence",
        authority_boundary="blocked_by_missing_input",
        safe_metadata={"metadata_only": True, "internal_only": True},
    ))

    examples.append(build_inference_packet_v1(
        request_id="price_vs_carbon_owner_priority_missing_branch",
        subject="price vs carbon owner priority missing branch",
        inference_mode="scenario_branch_generation",
        input_records=[{"type": "conflict", "conflict": "price_vs_carbon", "owner_priority": "missing"}],
        conflict_decision_refs=["conflict:price_vs_carbon"],
        missing_inputs=["owner_priority"],
        assumptions=["price and carbon are both relevant"],
        derived_candidates=[{"candidate_id": "price_vs_carbon_owner_priority_missing_branch:cost_branch", "candidate_label": "cost_branch", "candidate_status": "branch_required", "reason": "owner priority is missing so a branch is required", "authority_boundary": "branch_required", "confidence_label": "medium_confidence", "action_authority_granted": False, "runtime_authority": False, "writes_state": False, "model_provider_used": False, "public_claim_allowed": False, "proof_claim_allowed": False, "learning_claimed": False, "supported_by": ["conflict:price_vs_carbon"]}],
        recommended_next_check="ask the owner for priority before choosing price or carbon branch",
        confidence_label="medium_confidence",
        authority_boundary="branch_required",
        safe_metadata={"metadata_only": True, "internal_only": True},
    ))

    examples.append(build_inference_packet_v1(
        request_id="forecast_error_wrong_grid_zone_trace",
        subject="forecast error wrong grid zone trace",
        inference_mode="source_evidence_linking",
        input_records=[{"type": "forecast_error", "error": "wrong_grid_zone_trace"}],
        forecast_error_refs=["forecast_error:wrong_grid_zone_trace"],
        contradictions=["grid zone trace does not match expected zone"],
        uncertainty_notes=["trace the assumption that mapped the wrong grid zone"],
        derived_candidates=[{"candidate_id": "forecast_error_wrong_grid_zone_trace:trace_assumption", "candidate_label": "trace_assumption", "candidate_status": "constraint_checked", "reason": "the wrong grid-zone trace should be preserved as a traced assumption", "authority_boundary": "constraint_checked", "confidence_label": "medium_confidence", "action_authority_granted": False, "runtime_authority": False, "writes_state": False, "model_provider_used": False, "public_claim_allowed": False, "proof_claim_allowed": False, "learning_claimed": False, "supported_by": ["forecast_error:wrong_grid_zone_trace"]}],
        recommended_next_check="trace the grid-zone assumption and keep the forecast error linked",
        confidence_label="medium_confidence",
        authority_boundary="constraint_checked",
        safe_metadata={"metadata_only": True, "internal_only": True},
    ))

    examples.append(build_inference_packet_v1(
        request_id="artifact_generation_blocked_missing_validation_runner",
        subject="artifact generation blocked missing validation runner",
        inference_mode="dependency_resolution",
        input_records=[{"type": "artifact", "artifact": "generation_request", "validation_runner": "missing"}],
        artifact_provenance_refs=["artifact:build_generation_request"],
        missing_inputs=["validation_runner"],
        rejected_candidates=[{"candidate_id": "artifact_generation_blocked_missing_validation_runner:artifact_generation", "candidate_label": "artifact_generation", "candidate_status": "candidate_rejected", "reason": "artifact generation is blocked until the validation runner exists", "authority_boundary": "blocked_by_missing_input", "confidence_label": "low_confidence", "action_authority_granted": False, "runtime_authority": False, "writes_state": False, "model_provider_used": False, "public_claim_allowed": False, "proof_claim_allowed": False, "learning_claimed": False, "supported_by": ["artifact:build_generation_request"]}],
        recommended_next_check="implement the validation runner before any artifact generation",
        confidence_label="low_confidence",
        authority_boundary="blocked_by_missing_input",
        safe_metadata={"metadata_only": True, "internal_only": True},
    ))

    examples.append(build_inference_packet_v1(
        request_id="public_claim_rejected_not_public_safe",
        subject="public claim rejected not public safe",
        inference_mode="candidate_rejection",
        input_records=[{"type": "claim", "claim": "not_public_safe", "public_safe": False}],
        rejected_candidates=[{"candidate_id": "public_claim_rejected_not_public_safe:public_claim", "candidate_label": "public_claim", "candidate_status": "candidate_rejected", "reason": "not public safe; public claims stay rejected", "authority_boundary": "blocked_by_public_claim_boundary", "confidence_label": "blocked_insufficient_evidence", "action_authority_granted": False, "runtime_authority": False, "writes_state": False, "model_provider_used": False, "public_claim_allowed": False, "proof_claim_allowed": False, "learning_claimed": False, "supported_by": ["claim:public readiness claim"]}],
        recommended_next_check="keep the claim in review-only mode and do not publish it",
        confidence_label="blocked_insufficient_evidence",
        authority_boundary="blocked_by_public_claim_boundary",
        safe_metadata={"metadata_only": True, "internal_only": True},
    ))

    examples.append(build_inference_packet_v1(
        request_id="memory_answer_blocked_missing_source_scope",
        subject="memory answer blocked missing source scope",
        inference_mode="source_evidence_linking",
        input_records=[{"type": "memory", "source_scope": "missing"}],
        memory_refs=["memory:scope:missing"],
        missing_inputs=["source_scope"],
        rejected_candidates=[{"candidate_id": "memory_answer_blocked_missing_source_scope:memory_answer", "candidate_label": "memory_answer", "candidate_status": "candidate_rejected", "reason": "memory answers need a scoped source boundary before they can be formed", "authority_boundary": "blocked_by_privacy_boundary", "confidence_label": "low_confidence", "action_authority_granted": False, "runtime_authority": False, "writes_state": False, "model_provider_used": False, "public_claim_allowed": False, "proof_claim_allowed": False, "learning_claimed": False, "supported_by": ["memory:scope:missing"]}],
        recommended_next_check="collect a scoped source boundary before answering from memory",
        confidence_label="low_confidence",
        authority_boundary="blocked_by_privacy_boundary",
        safe_metadata={"metadata_only": True, "internal_only": True},
    ))

    examples.append(build_inference_packet_v1(
        request_id="llm_candidate_rejected_no_provenance",
        subject="llm candidate rejected no provenance",
        inference_mode="candidate_rejection",
        input_records=[{"type": "llm_candidate", "provenance": "missing"}],
        rejected_candidates=[{"candidate_id": "llm_candidate_rejected_no_provenance:llm_candidate", "candidate_label": "llm_candidate", "candidate_status": "candidate_rejected", "reason": "LLM candidate rejected because provenance is missing and cannot self-authorize", "authority_boundary": "blocked_by_authority_boundary", "confidence_label": "low_confidence", "action_authority_granted": False, "runtime_authority": False, "writes_state": False, "model_provider_used": False, "public_claim_allowed": False, "proof_claim_allowed": False, "learning_claimed": False, "supported_by": []}],
        recommended_next_check="attach provenance before considering any LLM candidate",
        confidence_label="low_confidence",
        authority_boundary="blocked_by_authority_boundary",
        safe_metadata={"metadata_only": True, "internal_only": True},
    ))

    examples.append(build_inference_packet_v1(
        request_id="unknown_engine_finding_to_missing_bridge_lane",
        subject="unknown engine finding to missing bridge lane",
        inference_mode="unknown_inference_mode",
        input_records=[{"type": "unknown_engine_finding", "finding": "missing bridge lane"}],
        source_provenance_refs=["finding:unknown_engine"],
        derived_candidates=[{"candidate_id": "unknown_engine_finding_to_missing_bridge_lane:missing_bridge_lane", "candidate_label": "missing_bridge_lane", "candidate_status": "branch_required", "reason": "UNKNOWN ENGINE findings map to the missing bridge lane, not to a runtime instruction", "authority_boundary": "branch_required", "confidence_label": "medium_confidence", "action_authority_granted": False, "runtime_authority": False, "writes_state": False, "model_provider_used": False, "public_claim_allowed": False, "proof_claim_allowed": False, "learning_claimed": False, "supported_by": ["finding:unknown_engine"]}],
        recommended_next_check="design the missing bridge lane before any runtime instruction is considered",
        confidence_label="medium_confidence",
        authority_boundary="branch_required",
        safe_metadata={"metadata_only": True, "internal_only": True},
    ))

    examples.append(build_inference_packet_v1(
        request_id="scenario_branch_from_unresolved_conflict",
        subject="scenario branch from unresolved conflict",
        inference_mode="scenario_branch_generation",
        input_records=[{"type": "conflict", "status": "unresolved"}],
        conflict_decision_refs=["conflict:unresolved"],
        contradictions=["price vs carbon conflict remains unresolved"],
        derived_candidates=[{"candidate_id": "scenario_branch_from_unresolved_conflict:branch_candidate", "candidate_label": "branch_candidate", "candidate_status": "branch_required", "reason": "unresolved conflict requires a scenario branch", "authority_boundary": "branch_required", "confidence_label": "medium_confidence", "action_authority_granted": False, "runtime_authority": False, "writes_state": False, "model_provider_used": False, "public_claim_allowed": False, "proof_claim_allowed": False, "learning_claimed": False, "supported_by": ["conflict:unresolved"]}],
        recommended_next_check="keep the unresolved conflict open and branch instead of collapsing it",
        confidence_label="medium_confidence",
        authority_boundary="branch_required",
        safe_metadata={"metadata_only": True, "internal_only": True},
    ))

    examples.append(build_inference_packet_v1(
        request_id="repeated_forecast_errors_behavior_pack_proposal_only",
        subject="repeated forecast errors behavior pack proposal only",
        inference_mode="algorithmic_scoring_without_authority",
        input_records=[{"type": "forecast_error_ledger", "pattern": "repeated_forecast_errors"}],
        forecast_error_refs=["forecast_error:pattern:repeated"],
        derived_candidates=[{"candidate_id": "repeated_forecast_errors_behavior_pack_proposal_only:behavior_pack_proposal", "candidate_label": "behavior_pack_proposal", "candidate_status": "candidate_only", "reason": "repeated forecast errors can only justify a behavior-pack proposal, not autonomous learning", "authority_boundary": "candidate_only", "confidence_label": "low_confidence", "action_authority_granted": False, "runtime_authority": False, "writes_state": False, "model_provider_used": False, "public_claim_allowed": False, "proof_claim_allowed": False, "learning_claimed": False, "supported_by": ["forecast_error:pattern:repeated"]}],
        rejected_candidates=[{"candidate_id": "repeated_forecast_errors_behavior_pack_proposal_only:autonomous_learning", "candidate_label": "autonomous_learning", "candidate_status": "candidate_rejected", "reason": "repeated forecast errors may propose a behavior pack only; they do not authorize autonomous learning", "authority_boundary": "blocked_by_authority_boundary", "confidence_label": "low_confidence", "action_authority_granted": False, "runtime_authority": False, "writes_state": False, "model_provider_used": False, "public_claim_allowed": False, "proof_claim_allowed": False, "learning_claimed": False, "supported_by": ["forecast_error:pattern:repeated"]}],
        recommended_next_check="propose a behavior pack only and keep autonomous change blocked",
        confidence_label="low_confidence",
        authority_boundary="candidate_only",
        safe_metadata={"metadata_only": True, "internal_only": True},
    ))

    return examples


__all__ = [
    "HELPER_TYPE_V1",
    "PACKET_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "ALLOWED_INFERENCE_MODES_V1",
    "ALLOWED_CONFIDENCE_LABELS_V1",
    "ALLOWED_AUTHORITY_BOUNDARIES_V1",
    "NeurosymbolicInferencePacket",
    "NeurosymbolicInferenceSummary",
    "ValidationError",
    "apply_inference_constraints_v1",
    "build_inference_packet_v1",
    "build_initial_neurosymbolic_inference_examples_v1",
    "derive_inference_candidates_v1",
    "reject_unsupported_candidates_v1",
    "summarize_inference_packet_v1",
    "to_neurosymbolic_inference_json_safe_v1",
    "validate_inference_packet_v1",
]
