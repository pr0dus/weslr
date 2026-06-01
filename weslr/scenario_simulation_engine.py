"""Metadata-only scenario simulation engine helpers v1.

This module builds bounded scenario simulation packets from supplied metadata
only. It is pure, deterministic, import-safe, and fail-closed.

It does not call APIs. It does not fetch live data. It does not connect to Home
Assistant. It does not call models/providers. It does not execute UNKNOWN
ENGINE or NAIE. It does not write memory or `.weslr`. It does not control
devices or create automations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping

from weslr.capability_maturity_registry import (
    CapabilityMaturityRecord,
    build_capability_maturity_record_v1,
    summarize_capability_maturity_registry_v1,
    to_capability_maturity_json_safe_v1,
    validate_capability_maturity_record_v1,
)
from weslr.energy_signal_conflict_resolution_policy import (
    EnergySignalConflictDecision,
    build_energy_signal_conflict_decision_v1,
    summarize_energy_signal_conflict_decision_v1,
    to_energy_signal_conflict_json_safe_v1,
    validate_energy_signal_conflict_decision_v1,
)
from weslr.forecast_error_ledger import (
    ForecastErrorRecord,
    build_forecast_error_record_v1,
    summarize_forecast_error_ledger_v1,
    summarize_forecast_error_record_v1,
    to_forecast_error_json_safe_v1,
    validate_forecast_error_record_v1,
)
from weslr.future_state_forecasting_engine import (
    FutureStateForecastPacket,
    build_future_state_forecast_packet_v1,
    build_future_state_forecast_request_v1,
    build_initial_future_state_forecast_examples_v1,
    summarize_future_state_forecast_packet_v1,
    to_future_state_forecast_json_safe_v1,
    validate_future_state_forecast_packet_v1,
)
from weslr.signal_provenance_freshness_model import (
    SignalProvenanceRecord,
    build_signal_provenance_record_v1,
    summarize_signal_provenance_record_v1,
    to_signal_provenance_json_safe_v1,
    validate_signal_provenance_record_v1,
)

HELPER_TYPE_V1 = "scenario_simulation_engine_v1"
REQUEST_TYPE_V1 = "scenario_simulation_request_v1"
PACKET_TYPE_V1 = "scenario_simulation_packet_v1"
SUMMARY_TYPE_V1 = "scenario_simulation_packet_summary_v1"

ALLOWED_SCENARIO_DOMAINS_V1 = {
    "weslr_project_scenario",
    "artifact_build_scenario",
    "energy_home_scenario",
    "grid_signal_scenario",
    "operator_workflow_scenario",
    "product_market_scenario",
    "wifi_rf_sensing_scenario",
    "research_to_prototype_scenario",
    "unknown_domain",
}

ALLOWED_SCENARIO_STATUS_LABELS_V1 = {
    "simulation_ready",
    "simulation_ready_with_uncertainty",
    "branching_required",
    "blocked_missing_input",
    "blocked_conflicting_signal",
    "blocked_stale_signal",
    "blocked_authority_boundary",
    "unknown_status",
}

ALLOWED_SCENARIO_BRANCH_LABELS_V1 = {
    "baseline_branch",
    "optimistic_branch",
    "conservative_branch",
    "cost_optimized_branch",
    "carbon_optimized_branch",
    "comfort_first_branch",
    "deadline_first_branch",
    "wait_and_observe_branch",
    "blocked_branch",
    "unknown_branch",
}

ALLOWED_REVERSIBILITY_LABELS_V1 = {
    "reversible",
    "partially_reversible",
    "hard_to_reverse",
    "irreversible",
    "unknown_reversibility",
}

ALLOWED_CONFIDENCE_LABELS_V1 = {
    "high_confidence",
    "medium_confidence",
    "low_confidence",
    "blocked_insufficient_evidence",
    "unknown_confidence",
}

ALLOWED_UNCERTAINTY_LABELS_V1 = {
    "low_uncertainty",
    "medium_uncertainty",
    "high_uncertainty",
    "unknown_uncertainty",
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
    "energy savings guarantee",
    "autonomous learning",
    "autonomous learn",
    "prediction certainty",
    "runtime authority",
    "public claim",
    "learning claim",
    "model provider",
)

DEFAULT_CREATED_TIMESTAMP_V1 = "2026-06-01T23:26:00+02:00"
DEFAULT_DOMAIN_V1 = "unknown_domain"
DEFAULT_STATUS_V1 = "unknown_status"
DEFAULT_BRANCH_LABEL_V1 = "unknown_branch"
DEFAULT_REVERSIBILITY_V1 = "unknown_reversibility"
DEFAULT_CONFIDENCE_V1 = "unknown_confidence"
DEFAULT_UNCERTAINTY_V1 = "unknown_uncertainty"
DEFAULT_RECOMMENDED_NEXT_LANE_V1 = "IMPLEMENT_WESLR_SCENARIO_SIMULATION_ENGINE_V1"
DEFAULT_FORECAST_ERROR_LEDGER_READY_V1 = True

STALE_FRESHNESS_STATUSES_V1 = {
    "stale",
    "expired",
    "missing_timestamp",
    "future_timestamp",
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ScenarioSimulationRequest:
    request_id: str
    subject: str
    domain: str
    forecast_packets: list[FutureStateForecastPacket]
    signal_records: list[SignalProvenanceRecord]
    conflict_decisions: list[EnergySignalConflictDecision]
    capability_maturity_records: list[CapabilityMaturityRecord]
    forecast_error_records: list[ForecastErrorRecord]
    assumptions: list[str]
    known_constraints: list[str]
    missing_inputs: list[str]
    scenario_hints: list[str]
    branch_preferences: list[str]
    recommended_next_lane: str
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ScenarioSimulationPacket:
    scenario_simulation_id: str
    subject: str
    domain: str
    created_timestamp: str
    input_summary: dict[str, Any]
    forecast_refs: list[str]
    signal_refs: list[str]
    signal_provenance_summary: list[dict[str, Any]]
    conflict_decision_refs: list[str]
    conflict_summary: dict[str, Any]
    assumptions: list[str]
    known_constraints: list[str]
    missing_inputs: list[str]
    scenario_branches: list[dict[str, Any]]
    branch_count: int
    recommended_branch_if_any: str
    blocked_branches: list[str]
    reversibility_summary: dict[str, Any]
    risk_summary: dict[str, Any]
    expected_tradeoffs: list[str]
    owner_priority_needed: bool
    recommended_next_observation: str
    recommended_next_lane: str
    scenario_status: str
    confidence_label: str
    uncertainty_label: str
    forecast_error_ledger_ready: bool
    recommendation_only: bool
    action_authority_granted: bool
    automation_allowed: bool
    device_control_allowed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    prediction_certainty_claimed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ScenarioSimulationPacketSummary:
    summary_type: str
    scenario_simulation_id: str
    subject: str
    domain: str
    scenario_status: str
    branch_count: int
    confidence_label: str
    uncertainty_label: str
    recommended_next_lane: str


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
    return " ".join(_safe_text(value).split()).lower()


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


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _json_safe(value: Any) -> Any:
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
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return _safe_text(value)


def to_scenario_simulation_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def _contains_forbidden_field(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if any(hint in key_text for hint in ALLOWED_FIELD_HINTS_V1):
                return key_text
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
    return ""


def _contains_forbidden_claim(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if any(phrase in key_text for phrase in ALLOWED_CLAIM_PHRASES_V1):
                return key_text
            nested = _contains_forbidden_claim(item)
            if nested:
                return nested
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            nested = _contains_forbidden_claim(item)
            if nested:
                return nested
    elif isinstance(value, str):
        lowered = _normalize_text(value)
        if any(phrase in lowered for phrase in ALLOWED_CLAIM_PHRASES_V1):
            return lowered
    return ""


def _forecast_like(item: Any) -> FutureStateForecastPacket:
    if isinstance(item, FutureStateForecastPacket):
        validate_future_state_forecast_packet_v1(item)
        return item
    if isinstance(item, Mapping):
        return build_future_state_forecast_packet_v1(item)
    if is_dataclass(item):
        return build_future_state_forecast_packet_v1(asdict(item))
    raise ValidationError("unknown_forecast_packet")


def _signal_like(item: Any) -> SignalProvenanceRecord:
    if isinstance(item, SignalProvenanceRecord):
        validate_signal_provenance_record_v1(item)
        return item
    if isinstance(item, Mapping):
        return build_signal_provenance_record_v1(**dict(item))
    if is_dataclass(item):
        return build_signal_provenance_record_v1(**asdict(item))
    raise ValidationError("unknown_signal_record")


def _decision_like(item: Any) -> EnergySignalConflictDecision:
    if isinstance(item, EnergySignalConflictDecision):
        validate_energy_signal_conflict_decision_v1(item)
        return item
    if isinstance(item, Mapping):
        return build_energy_signal_conflict_decision_v1(**dict(item))
    if is_dataclass(item):
        return build_energy_signal_conflict_decision_v1(**asdict(item))
    raise ValidationError("unknown_conflict_decision")


def _maturity_like(item: Any) -> CapabilityMaturityRecord:
    if isinstance(item, CapabilityMaturityRecord):
        validate_capability_maturity_record_v1(item)
        return item
    if isinstance(item, Mapping):
        return build_capability_maturity_record_v1(**dict(item))
    if is_dataclass(item):
        return build_capability_maturity_record_v1(**asdict(item))
    raise ValidationError("unknown_capability_maturity_record")


def _error_like(item: Any) -> ForecastErrorRecord:
    if isinstance(item, ForecastErrorRecord):
        validate_forecast_error_record_v1(item)
        return item
    if isinstance(item, Mapping):
        return build_forecast_error_record_v1(**dict(item))
    if is_dataclass(item):
        return build_forecast_error_record_v1(**asdict(item))
    raise ValidationError("unknown_forecast_error_record")


def _unique_sorted(items: Iterable[str]) -> list[str]:
    return sorted(set(_safe_list(list(items))))


def _summary_refs_for_signals(records: Iterable[SignalProvenanceRecord]) -> list[dict[str, Any]]:
    return [to_signal_provenance_json_safe_v1(summarize_signal_provenance_record_v1(record)) for record in records]


def _summary_refs_for_decisions(decisions: Iterable[EnergySignalConflictDecision]) -> list[dict[str, Any]]:
    return [to_energy_signal_conflict_json_safe_v1(summarize_energy_signal_conflict_decision_v1(decision)) for decision in decisions]


def _summary_refs_for_forecasts(packets: Iterable[FutureStateForecastPacket]) -> list[dict[str, Any]]:
    return [to_future_state_forecast_json_safe_v1(summarize_future_state_forecast_packet_v1(packet)) for packet in packets]


def _freshness_values_from_forecasts(forecast_packets: Iterable[FutureStateForecastPacket]) -> list[str]:
    values: list[str] = []
    for packet in forecast_packets:
        values.extend(list(packet.freshness_summary.values()))
    return values


def _conflict_labels_from_decisions(decisions: Iterable[EnergySignalConflictDecision]) -> list[str]:
    labels: list[str] = []
    for decision in decisions:
        labels.extend(decision.conflict_classes)
        labels.extend(decision.unresolved_conflicts)
    return labels


def _has_stale_signals(signal_records: Iterable[SignalProvenanceRecord], forecast_packets: Iterable[FutureStateForecastPacket]) -> bool:
    for record in signal_records:
        if record.freshness_status in STALE_FRESHNESS_STATUSES_V1:
            return True
    for packet in forecast_packets:
        if any(value in STALE_FRESHNESS_STATUSES_V1 for value in packet.freshness_summary.values()):
            return True
    return False


def _build_risk_summary(
    *,
    domain: str,
    status: str,
    missing_inputs: list[str],
    stale_signals: bool,
    conflicts: list[str],
    owner_priority_needed: bool,
) -> dict[str, Any]:
    return {
        "domain_focus": domain,
        "status_focus": status,
        "risk_labels": sorted(
            {
                *({"missing_input"} if missing_inputs else set()),
                *({"stale_signal"} if stale_signals else set()),
                *({"conflict"} if conflicts else set()),
                *({"owner_priority_gap"} if owner_priority_needed else set()),
            }
        ),
        "risk_count": len(missing_inputs) + (1 if stale_signals else 0) + (1 if conflicts else 0) + (1 if owner_priority_needed else 0),
        "notes": [
            "branches are bounded hypotheses",
            "authority remains external to the packet",
        ],
    }


def _build_reversibility_summary(branches: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for branch in branches:
        label = _safe_text(branch.get("reversibility", DEFAULT_REVERSIBILITY_V1))
        counts[label] = counts.get(label, 0) + 1
    return {
        "counts": dict(sorted(counts.items())),
        "has_irreversible_branch": counts.get("irreversible", 0) > 0,
        "has_hard_to_reverse_branch": counts.get("hard_to_reverse", 0) > 0,
    }


def _branch(
    *,
    branch_id: str,
    branch_label: str,
    branch_name: str,
    branch_purpose: str,
    reversibility: str,
    expected_tradeoffs: Iterable[str] | None = None,
    risk_notes: Iterable[str] | None = None,
    next_observation: str = "",
    blocked_reason: str = "",
) -> dict[str, Any]:
    return {
        "branch_id": _safe_text(branch_id),
        "branch_label": _safe_text(branch_label),
        "branch_name": _safe_text(branch_name),
        "branch_purpose": _safe_text(branch_purpose),
        "reversibility": _safe_text(reversibility),
        "expected_tradeoffs": _safe_list(expected_tradeoffs),
        "risk_notes": _safe_list(risk_notes),
        "next_observation": _safe_text(next_observation),
        "blocked_reason": _safe_text(blocked_reason),
    }


def _classify_confidence_and_uncertainty(status: str, branch_count: int, has_missing_inputs: bool, has_stale_signals: bool, has_conflicts: bool) -> tuple[str, str]:
    if has_missing_inputs:
        return "blocked_insufficient_evidence", "high_uncertainty"
    if status == "blocked_stale_signal":
        return "low_confidence", "high_uncertainty"
    if has_conflicts or branch_count > 1:
        return "medium_confidence", "high_uncertainty"
    if has_stale_signals:
        return "low_confidence", "medium_uncertainty"
    if branch_count == 1:
        return "high_confidence", "low_uncertainty"
    return "unknown_confidence", "unknown_uncertainty"


def _recommended_next_observation(domain: str, status: str, missing_inputs: list[str], blocked_branches: list[str]) -> str:
    if missing_inputs:
        return missing_inputs[0]
    if status == "blocked_stale_signal":
        return "refresh_stale_signal_metadata"
    if status == "blocked_authority_boundary":
        return "separate_authority_from_metadata_and_retry"
    if status == "branching_required":
        return "compare branches and preserve conflict metadata"
    if blocked_branches:
        return "confirm blocked branch boundary before further simulation"
    if domain == "artifact_build_scenario":
        return "confirm validation runner metadata"
    if domain == "energy_home_scenario":
        return "collect fresh energy signals and re-run simulation"
    if domain == "wifi_rf_sensing_scenario":
        return "confirm privacy boundary metadata"
    return "rebuild simulation if inputs change"


def _recommended_next_lane(domain: str, status: str, request: ScenarioSimulationRequest) -> str:
    if request.recommended_next_lane:
        return request.recommended_next_lane
    if status == "branching_required":
        return "DESIGN_WESLR_TRI_ENGINE_ORCHESTRATION_BOUNDARY_V1"
    if domain == "energy_home_scenario":
        return "IMPLEMENT_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1"
    if domain == "artifact_build_scenario":
        return "DESIGN_WESLR_SOURCE_EVIDENCE_GRAPH_V1"
    if domain == "weslr_project_scenario":
        return "IMPLEMENT_WESLR_CAPABILITY_MATURITY_REGISTRY_V1"
    return DEFAULT_RECOMMENDED_NEXT_LANE_V1


def _build_branch_set(request: ScenarioSimulationRequest) -> list[dict[str, Any]]:
    branches: list[dict[str, Any]] = []
    domain = request.domain
    labels = set(request.branch_preferences)
    forecast_statuses = [packet.forecast_status for packet in request.forecast_packets]
    forecast_refs = [packet.forecast_id for packet in request.forecast_packets]
    conflicts = _conflict_labels_from_decisions(request.conflict_decisions)
    has_stale = _has_stale_signals(request.signal_records, request.forecast_packets)
    missing = list(request.missing_inputs)

    if domain == "energy_home_scenario" and any("price_vs_carbon" in label for label in conflicts):
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_cost_optimized",
                branch_label="cost_optimized_branch",
                branch_name="cost_optimized_branch",
                branch_purpose="minimize cost while preserving safety metadata",
                reversibility="reversible",
                expected_tradeoffs=["lower cost", "higher carbon"],
                risk_notes=["price priority remains explicit"],
                next_observation="compare with carbon branch",
            ),
            _branch(
                branch_id=f"{request.request_id}_carbon_optimized",
                branch_label="carbon_optimized_branch",
                branch_name="carbon_optimized_branch",
                branch_purpose="minimize carbon while preserving safety metadata",
                reversibility="reversible",
                expected_tradeoffs=["lower carbon", "higher cost"],
                risk_notes=["carbon priority remains explicit"],
                next_observation="compare with cost branch",
            ),
            _branch(
                branch_id=f"{request.request_id}_baseline",
                branch_label="baseline_branch",
                branch_name="baseline_branch",
                branch_purpose="preserve the existing decision baseline",
                reversibility="reversible",
                expected_tradeoffs=["minimal change", "lower decision pressure"],
                risk_notes=["baseline keeps conflict visible"],
                next_observation="preserve conflict summary",
            ),
        ])
    elif domain == "energy_home_scenario" and has_stale:
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_wait_and_observe",
                branch_label="wait_and_observe_branch",
                branch_name="wait_and_observe_branch",
                branch_purpose="wait for fresh signal metadata before changing anything",
                reversibility="reversible",
                expected_tradeoffs=["delay action", "protect from stale signal"],
                risk_notes=["stale signal remains blocking"],
                next_observation="refresh stale signal metadata",
            ),
            _branch(
                branch_id=f"{request.request_id}_blocked",
                branch_label="blocked_branch",
                branch_name="blocked_branch",
                branch_purpose="hold simulation because the source is stale",
                reversibility="unknown_reversibility",
                expected_tradeoffs=["no action", "no premature confidence"],
                risk_notes=["blocked until fresh metadata arrives"],
                next_observation="collect fresh signal",
                blocked_reason="stale signal boundary",
            ),
        ])
    elif domain == "energy_home_scenario" and missing:
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_deadline_first",
                branch_label="deadline_first_branch",
                branch_name="deadline_first_branch",
                branch_purpose="prioritize deadline-limited energy planning",
                reversibility="partially_reversible",
                expected_tradeoffs=["deadline protection", "possible comfort reduction"],
                risk_notes=["missing departure or schedule data keeps confidence bounded"],
                next_observation="collect missing timing metadata",
            ),
            _branch(
                branch_id=f"{request.request_id}_blocked",
                branch_label="blocked_branch",
                branch_name="blocked_branch",
                branch_purpose="hold until missing input is supplied",
                reversibility="unknown_reversibility",
                expected_tradeoffs=["no action", "no invented deadline"],
                risk_notes=["missing input is still blocking"],
                next_observation="collect missing input",
                blocked_reason="missing input boundary",
            ),
        ])
    elif domain == "energy_home_scenario" and any("comfort_vs_cost" in label or "price_vs_comfort" in label for label in conflicts):
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_comfort_first",
                branch_label="comfort_first_branch",
                branch_name="comfort_first_branch",
                branch_purpose="preserve comfort while keeping metadata bounded",
                reversibility="reversible",
                expected_tradeoffs=["more comfort", "more cost"],
                risk_notes=["comfort priority remains explicit"],
                next_observation="compare with cost branch",
            ),
            _branch(
                branch_id=f"{request.request_id}_cost_optimized",
                branch_label="cost_optimized_branch",
                branch_name="cost_optimized_branch",
                branch_purpose="reduce cost while keeping safety visible",
                reversibility="reversible",
                expected_tradeoffs=["less cost", "less comfort"],
                risk_notes=["cost priority remains explicit"],
                next_observation="compare with comfort branch",
            ),
        ])
    elif domain == "energy_home_scenario" and (
        any("pv" in _normalize_text(hint) or "weather" in _normalize_text(hint) for hint in request.scenario_hints)
        or any(label in {"optimistic_branch", "conservative_branch"} for label in labels)
    ):
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_optimistic",
                branch_label="optimistic_branch",
                branch_name="optimistic_branch",
                branch_purpose="assume sunny conditions and higher surplus",
                reversibility="reversible",
                expected_tradeoffs=["more surplus", "higher confidence in PV"],
                risk_notes=["sunny branch is optimistic"],
                next_observation="compare with cloudy branch",
            ),
            _branch(
                branch_id=f"{request.request_id}_conservative",
                branch_label="conservative_branch",
                branch_name="conservative_branch",
                branch_purpose="assume cloudy conditions and lower surplus",
                reversibility="reversible",
                expected_tradeoffs=["less surplus", "lower confidence in PV"],
                risk_notes=["cloudy branch stays cautious"],
                next_observation="compare with sunny branch",
            ),
        ])
    elif domain == "energy_home_scenario":
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_baseline",
                branch_label="baseline_branch",
                branch_name="baseline_branch",
                branch_purpose="retain current state as a neutral branch",
                reversibility="reversible",
                expected_tradeoffs=["stable state", "minimal change"],
                risk_notes=["neutral branch preserves optionality"],
                next_observation="rebuild after new metadata",
            )
        ])
    elif domain == "artifact_build_scenario":
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_blocked",
                branch_label="blocked_branch",
                branch_name="blocked_branch",
                branch_purpose="hold build because validation runner metadata is missing",
                reversibility="unknown_reversibility",
                expected_tradeoffs=["no build", "no unsafe write"],
                risk_notes=["validation runner is required"],
                next_observation="restore validation runner metadata",
                blocked_reason="missing validation runner",
            )
        ])
    elif domain == "product_market_scenario":
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_blocked",
                branch_label="blocked_branch",
                branch_name="blocked_branch",
                branch_purpose="hold public pilot because claim lifecycle evidence is missing",
                reversibility="unknown_reversibility",
                expected_tradeoffs=["no public pilot claim", "no overstatement"],
                risk_notes=["claim lifecycle evidence missing"],
                next_observation="collect claim lifecycle metadata",
                blocked_reason="claim lifecycle missing",
            )
        ])
    elif domain == "wifi_rf_sensing_scenario":
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_blocked",
                branch_label="blocked_branch",
                branch_name="blocked_branch",
                branch_purpose="hold WiFi/RF simulation because privacy boundary metadata is missing",
                reversibility="unknown_reversibility",
                expected_tradeoffs=["no sensing expansion", "no privacy boundary violation"],
                risk_notes=["privacy boundary must be explicit"],
                next_observation="define privacy boundary metadata",
                blocked_reason="privacy boundary missing",
            )
        ])
    elif domain == "weslr_project_scenario" and any("implementation wave" in hint for hint in request.scenario_hints):
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_baseline",
                branch_label="baseline_branch",
                branch_name="baseline_branch",
                branch_purpose="continue implementation wave using metadata-only projections",
                reversibility="reversible",
                expected_tradeoffs=["implementation progress", "bounded uncertainty"],
                risk_notes=["keep runtime later"],
                next_observation="continue helper implementation wave",
            ),
            _branch(
                branch_id=f"{request.request_id}_wait_and_observe",
                branch_label="wait_and_observe_branch",
                branch_name="wait_and_observe_branch",
                branch_purpose="preserve orchestration for later runtime integration",
                reversibility="partially_reversible",
                expected_tradeoffs=["delay orchestration", "preserve architecture"],
                risk_notes=["runtime boundary remains future work"],
                next_observation="preserve orchestration boundary for later",
            ),
        ])
    elif domain == "weslr_project_scenario" and any("orchestration" in hint for hint in request.scenario_hints):
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_wait_and_observe",
                branch_label="wait_and_observe_branch",
                branch_name="wait_and_observe_branch",
                branch_purpose="preserve tri-engine orchestration for later runtime work",
                reversibility="partially_reversible",
                expected_tradeoffs=["later runtime integration", "no premature execution"],
                risk_notes=["orchestration boundary remains preserved"],
                next_observation="keep orchestration in design space",
            )
        ])
    elif labels & {"wait_and_observe_branch", "blocked_branch"} or has_stale:
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_wait_and_observe",
                branch_label="wait_and_observe_branch",
                branch_name="wait_and_observe_branch",
                branch_purpose="wait and observe instead of forcing a fake answer",
                reversibility="reversible",
                expected_tradeoffs=["delay action", "protect evidence quality"],
                risk_notes=["uncertainty preserved"],
                next_observation="rebuild with fresh inputs",
            )
        ])
    elif not branches:
        branches.extend([
            _branch(
                branch_id=f"{request.request_id}_baseline",
                branch_label="baseline_branch",
                branch_name="baseline_branch",
                branch_purpose="preserve the current bounded state",
                reversibility="reversible",
                expected_tradeoffs=["stable interpretation", "low transformation risk"],
                risk_notes=["baseline branch used when nothing forces divergence"],
                next_observation="rebuild when input set changes",
            )
        ])

    if any("price_vs_carbon" in conflict for conflict in conflicts) and len(branches) < 3:
        # Ensure three branches for the price-vs-carbon rehearsal.
        branches = branches[:2] + [
            _branch(
                branch_id=f"{request.request_id}_baseline",
                branch_label="baseline_branch",
                branch_name="baseline_branch",
                branch_purpose="preserve the neutral baseline branch",
                reversibility="reversible",
                expected_tradeoffs=["minimal change", "keeps conflict visible"],
                risk_notes=["baseline assists comparison"],
                next_observation="compare all three branches",
            )
        ]

    return branches


def _scenario_status_from_request(request: ScenarioSimulationRequest, branches: list[dict[str, Any]]) -> str:
    if request.domain not in ALLOWED_SCENARIO_DOMAINS_V1:
        return "unknown_status"
    if any(value in STALE_FRESHNESS_STATUSES_V1 for value in _freshness_values_from_forecasts(request.forecast_packets)) or any(record.freshness_status in STALE_FRESHNESS_STATUSES_V1 for record in request.signal_records):
        return "blocked_stale_signal" if not request.missing_inputs else "blocked_missing_input"
    if request.missing_inputs:
        return "blocked_missing_input"
    if any(decision.scenario_branch_required or decision.unresolved_conflicts for decision in request.conflict_decisions) or len(branches) > 1:
        return "branching_required"
    if any(record.current_authority == "blocked" or record.current_maturity == "blocked_or_deprecated" for record in request.capability_maturity_records):
        return "blocked_authority_boundary"
    if any(label == "blocked_branch" for label in (branch.get("branch_label", "") for branch in branches)):
        return "blocked_authority_boundary" if request.domain in {"product_market_scenario", "wifi_rf_sensing_scenario"} else "blocked_missing_input"
    if len(request.forecast_packets) > 1 or len(request.signal_records) > 1:
        return "simulation_ready_with_uncertainty"
    return "simulation_ready"


def build_scenario_simulation_request_v1(
    *,
    request_id: str,
    subject: str,
    domain: str,
    forecast_packets: Iterable[Any] | None = None,
    signal_records: Iterable[Any] | None = None,
    conflict_decisions: Iterable[Any] | None = None,
    capability_maturity_records: Iterable[Any] | None = None,
    forecast_error_records: Iterable[Any] | None = None,
    assumptions: Iterable[str] | None = None,
    known_constraints: Iterable[str] | None = None,
    missing_inputs: Iterable[str] | None = None,
    scenario_hints: Iterable[str] | None = None,
    branch_preferences: Iterable[str] | None = None,
    recommended_next_lane: str = DEFAULT_RECOMMENDED_NEXT_LANE_V1,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> ScenarioSimulationRequest:
    request = ScenarioSimulationRequest(
        request_id=_safe_text(request_id),
        subject=_safe_text(subject),
        domain=_safe_text(domain),
        forecast_packets=[_forecast_like(item) for item in (forecast_packets or [])],
        signal_records=[_signal_like(item) for item in (signal_records or [])],
        conflict_decisions=[_decision_like(item) for item in (conflict_decisions or [])],
        capability_maturity_records=[_maturity_like(item) for item in (capability_maturity_records or [])],
        forecast_error_records=[_error_like(item) for item in (forecast_error_records or [])],
        assumptions=_safe_list(assumptions),
        known_constraints=_safe_list(known_constraints),
        missing_inputs=_safe_list(missing_inputs),
        scenario_hints=_safe_list(scenario_hints),
        branch_preferences=_safe_list(branch_preferences),
        recommended_next_lane=_safe_text(recommended_next_lane),
        safe_metadata={"metadata_only": True, "internal_only": True, **dict(safe_metadata or {}), **dict(extra_metadata)},
    )
    return request


def build_scenario_simulation_packet_v1(
    request: Any,
    /,
    *,
    created_timestamp: str = DEFAULT_CREATED_TIMESTAMP_V1,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> ScenarioSimulationPacket:
    normalized_request = request if isinstance(request, ScenarioSimulationRequest) else build_scenario_simulation_request_v1(**dict(request)) if isinstance(request, Mapping) else build_scenario_simulation_request_v1(**asdict(request)) if is_dataclass(request) else None
    if normalized_request is None:
        raise ValidationError("unknown_request")

    branches = _build_branch_set(normalized_request)
    status = _scenario_status_from_request(normalized_request, branches)
    has_missing_inputs = bool(normalized_request.missing_inputs)
    has_stale_signals = _has_stale_signals(normalized_request.signal_records, normalized_request.forecast_packets)
    has_conflicts = bool(normalized_request.conflict_decisions)
    confidence_label, uncertainty_label = _classify_confidence_and_uncertainty(
        status,
        len(branches),
        has_missing_inputs,
        has_stale_signals,
        has_conflicts,
    )
    blocked_branches = [branch["branch_label"] for branch in branches if branch["branch_label"] == "blocked_branch"]
    recommended_branch = next((branch["branch_label"] for branch in branches if branch["branch_label"] not in {"blocked_branch", "unknown_branch"}), branches[0]["branch_label"] if branches else "")
    owner_priority_needed = has_conflicts or any("priority" in _normalize_text(constraint) for constraint in normalized_request.known_constraints)
    forecast_error_ledger_ready = bool(
        normalized_request.forecast_error_records
        or has_missing_inputs
        or has_stale_signals
        or has_conflicts
    )
    packet = ScenarioSimulationPacket(
        scenario_simulation_id=f"{normalized_request.request_id}_scenario",
        subject=normalized_request.subject,
        domain=normalized_request.domain,
        created_timestamp=_safe_text(created_timestamp),
        input_summary={
            "request_id": normalized_request.request_id,
            "forecast_count": len(normalized_request.forecast_packets),
            "signal_count": len(normalized_request.signal_records),
            "conflict_decision_count": len(normalized_request.conflict_decisions),
            "capability_maturity_count": len(normalized_request.capability_maturity_records),
            "forecast_error_count": len(normalized_request.forecast_error_records),
            "assumption_count": len(normalized_request.assumptions),
            "constraint_count": len(normalized_request.known_constraints),
        },
        forecast_refs=[packet.forecast_id for packet in normalized_request.forecast_packets],
        signal_refs=[record.signal_id for record in normalized_request.signal_records],
        signal_provenance_summary=_summary_refs_for_signals(normalized_request.signal_records),
        conflict_decision_refs=[decision.conflict_decision_id for decision in normalized_request.conflict_decisions],
        conflict_summary={
            "conflict_classes": sorted({conflict for decision in normalized_request.conflict_decisions for conflict in decision.conflict_classes}),
            "scenario_branch_required": any(decision.scenario_branch_required for decision in normalized_request.conflict_decisions),
            "unresolved_conflicts": sorted({conflict for decision in normalized_request.conflict_decisions for conflict in decision.unresolved_conflicts}),
            "decision_summaries": _summary_refs_for_decisions(normalized_request.conflict_decisions),
            "forecast_summaries": _summary_refs_for_forecasts(normalized_request.forecast_packets),
        },
        assumptions=list(normalized_request.assumptions),
        known_constraints=list(normalized_request.known_constraints),
        missing_inputs=list(normalized_request.missing_inputs),
        scenario_branches=branches,
        branch_count=len(branches),
        recommended_branch_if_any=recommended_branch,
        blocked_branches=blocked_branches,
        reversibility_summary=_build_reversibility_summary(branches),
        risk_summary=_build_risk_summary(
            domain=normalized_request.domain,
            status=status,
            missing_inputs=list(normalized_request.missing_inputs),
            stale_signals=has_stale_signals,
            conflicts=_conflict_labels_from_decisions(normalized_request.conflict_decisions),
            owner_priority_needed=owner_priority_needed,
        ),
        expected_tradeoffs=sorted({tradeoff for branch in branches for tradeoff in branch.get("expected_tradeoffs", [])}),
        owner_priority_needed=owner_priority_needed,
        recommended_next_observation=_recommended_next_observation(normalized_request.domain, status, list(normalized_request.missing_inputs), blocked_branches),
        recommended_next_lane=_recommended_next_lane(normalized_request.domain, status, normalized_request),
        scenario_status=status,
        confidence_label=confidence_label,
        uncertainty_label=uncertainty_label,
        forecast_error_ledger_ready=_safe_bool(forecast_error_ledger_ready),
        recommendation_only=True,
        action_authority_granted=False,
        automation_allowed=False,
        device_control_allowed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        prediction_certainty_claimed=False,
        learning_claimed=False,
        safe_metadata={"metadata_only": True, "internal_only": True, **dict(safe_metadata or {}), **dict(extra_metadata)},
    )
    validate_scenario_simulation_packet_v1(packet)
    return packet


def validate_scenario_simulation_packet_v1(packet: Any) -> bool:
    original = packet if isinstance(packet, Mapping) else asdict(packet) if is_dataclass(packet) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    if _contains_forbidden_claim(original):
        raise ValidationError("forbidden_claim_marker_detected")
    normalized = packet if isinstance(packet, ScenarioSimulationPacket) else ScenarioSimulationPacket(**dict(packet)) if isinstance(packet, Mapping) else ScenarioSimulationPacket(**asdict(packet)) if is_dataclass(packet) else None
    if normalized is None:
        raise ValidationError("unknown_packet")
    if normalized.domain not in ALLOWED_SCENARIO_DOMAINS_V1:
        raise ValidationError("unknown_domain")
    if normalized.scenario_status not in ALLOWED_SCENARIO_STATUS_LABELS_V1:
        raise ValidationError("unknown_status")
    for branch in normalized.scenario_branches:
        branch_label = _safe_text(branch.get("branch_label", DEFAULT_BRANCH_LABEL_V1))
        reversibility = _safe_text(branch.get("reversibility", DEFAULT_REVERSIBILITY_V1))
        if branch_label not in ALLOWED_SCENARIO_BRANCH_LABELS_V1:
            raise ValidationError("unknown_branch_label")
        if reversibility not in ALLOWED_REVERSIBILITY_LABELS_V1:
            raise ValidationError("unknown_reversibility")
        if _contains_forbidden_field(branch) or _contains_forbidden_claim(branch):
            raise ValidationError("forbidden_branch_metadata_detected")
    if normalized.confidence_label not in ALLOWED_CONFIDENCE_LABELS_V1:
        raise ValidationError("unknown_confidence")
    if normalized.uncertainty_label not in ALLOWED_UNCERTAINTY_LABELS_V1:
        raise ValidationError("unknown_uncertainty")
    if normalized.action_authority_granted:
        raise ValidationError("action_authority_granted_true")
    if normalized.automation_allowed:
        raise ValidationError("automation_allowed_true")
    if normalized.device_control_allowed:
        raise ValidationError("device_control_allowed_true")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_true")
    if normalized.writes_state:
        raise ValidationError("writes_state_true")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_true")
    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_true")
    if normalized.prediction_certainty_claimed:
        raise ValidationError("prediction_certainty_claimed_true")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_true")
    if _contains_forbidden_field(normalized.safe_metadata) or _contains_forbidden_claim(normalized.safe_metadata):
        raise ValidationError("forbidden_safe_metadata_detected")
    return True


def summarize_scenario_simulation_packet_v1(packet: Any) -> ScenarioSimulationPacketSummary:
    normalized = packet if isinstance(packet, ScenarioSimulationPacket) else ScenarioSimulationPacket(**dict(packet)) if isinstance(packet, Mapping) else ScenarioSimulationPacket(**asdict(packet)) if is_dataclass(packet) else None
    if normalized is None:
        raise ValidationError("unknown_packet")
    validate_scenario_simulation_packet_v1(normalized)
    return ScenarioSimulationPacketSummary(
        summary_type=SUMMARY_TYPE_V1,
        scenario_simulation_id=normalized.scenario_simulation_id,
        subject=normalized.subject,
        domain=normalized.domain,
        scenario_status=normalized.scenario_status,
        branch_count=normalized.branch_count,
        confidence_label=normalized.confidence_label,
        uncertainty_label=normalized.uncertainty_label,
        recommended_next_lane=normalized.recommended_next_lane,
    )


def _signal(
    *,
    signal_provenance_id: str,
    signal_id: str,
    signal_name: str,
    signal_class: str,
    source_system: str,
    source_provider: str,
    source_reference: str,
    source_url_or_entity_id: str,
    source_scope: str = "local",
    freshness_status: str | None = None,
    control_capable: bool = False,
) -> SignalProvenanceRecord:
    return build_signal_provenance_record_v1(
        signal_provenance_id=signal_provenance_id,
        signal_id=signal_id,
        signal_name=signal_name,
        signal_class=signal_class,
        source_system=source_system,
        source_provider=source_provider,
        source_reference=source_reference,
        source_url_or_entity_id=source_url_or_entity_id,
        source_scope=source_scope,
        retrieval_method="synthetic_in_memory",
        freshness_status=freshness_status,
        control_capable=control_capable,
        forecasting_allowed=True,
        scenario_simulation_allowed=True,
        memory_write_allowed=False,
        action_authority_granted=False,
        safe_metadata={"synthetic": True, "metadata_only": True},
    )


def _forecast_packet(subject: str, domain: str, horizon: str, *, signals: list[SignalProvenanceRecord] | None = None, conflicts: list[EnergySignalConflictDecision] | None = None, maturities: list[CapabilityMaturityRecord] | None = None, errors: list[ForecastErrorRecord] | None = None, missing_inputs: list[str] | None = None, scenario_hints: list[str] | None = None) -> FutureStateForecastPacket:
    return build_future_state_forecast_packet_v1(
        build_future_state_forecast_request_v1(
            request_id=subject,
            subject=subject,
            domain=domain,
            forecast_horizon=horizon,
            signal_records=signals or [],
            conflict_decisions=conflicts or [],
            capability_maturity_records=maturities or [],
            forecast_error_records=errors or [],
            missing_inputs=missing_inputs or [],
            scenario_hints=scenario_hints or [],
            safe_metadata={"synthetic": True},
        )
    )


def _conflict(subject: str, classes: list[str], signals: list[SignalProvenanceRecord], *, scenario_branch_required: bool = False) -> EnergySignalConflictDecision:
    return build_energy_signal_conflict_decision_v1(
        conflict_decision_id=f"{subject}_conflict",
        decision_subject=subject,
        conflict_classes=classes,
        involved_signals=signals,
        scenario_branch_required=scenario_branch_required,
        safe_recommendation_mode="recommendation_only",
    )


def _capability(capability_id: str, capability_name: str, family: str, maturity: str, next_lane: str) -> CapabilityMaturityRecord:
    return build_capability_maturity_record_v1(
        capability_id=capability_id,
        capability_name=capability_name,
        capability_family=family,
        current_maturity=maturity,
        latest_commit="static_reference_v1",
        latest_judgment="metadata_only",
        recommended_next_lane=next_lane,
        safe_metadata={"synthetic": True},
    )


def _error(record_id: str, subject: str, domain: str, horizon: str, error_type: str) -> ForecastErrorRecord:
    return build_forecast_error_record_v1(
        forecast_error_record_id=record_id,
        source_forecast_id=f"{record_id}_forecast",
        source_scenario_simulation_id=f"{record_id}_scenario",
        source_energy_intelligence_id=f"{record_id}_intel",
        subject=subject,
        domain=domain,
        forecast_horizon=horizon,
        expected_outcome="synthetic expected outcome",
        observed_outcome="synthetic observed outcome",
        outcome_match_status="missed",
        error_type=error_type,
        error_severity="moderate",
        confidence_before=0.75,
        confidence_after=0.38,
        assumptions_used=["synthetic assumption"],
        assumptions_failed=["synthetic failed assumption"],
        signals_used=["synthetic_signal"],
        recommendation_taken="bounded_recommendation",
        owner_action_taken="metadata_only_review",
        action_authority_used=False,
        resulting_effect="synthetic outcome",
        corrective_lesson="keep the boundary explicit",
        recommended_model_update="metadata-only branch tracking",
        behavior_pack_candidate="scenario_behavior_pack_candidate",
        requires_owner_review=True,
        safe_metadata={"synthetic": True},
    )


def build_initial_scenario_simulation_examples_v1() -> list[ScenarioSimulationPacket]:
    forecast_examples = build_initial_future_state_forecast_examples_v1()
    by_id = {packet.forecast_id: packet for packet in forecast_examples}

    price = _signal(
        signal_provenance_id="scenario_price_v1",
        signal_id="scenario_price",
        signal_name="Scenario Price",
        signal_class="electricity_price_provider",
        source_system="price_api",
        source_provider="static_metadata",
        source_reference="price_day_ahead",
        source_url_or_entity_id="price_day_ahead",
        source_scope="public_open",
        freshness_status="fresh",
    )
    carbon = _signal(
        signal_provenance_id="scenario_carbon_v1",
        signal_id="scenario_carbon",
        signal_name="Scenario Carbon",
        signal_class="grid_carbon_provider",
        source_system="carbon_api",
        source_provider="static_metadata",
        source_reference="carbon_intensity",
        source_url_or_entity_id="carbon_intensity",
        source_scope="public_open",
        freshness_status="fresh",
    )
    cloudy_pv = _signal(
        signal_provenance_id="scenario_pv_cloudy_v1",
        signal_id="scenario_pv_cloudy",
        signal_name="Scenario PV Cloudy",
        signal_class="weather_provider",
        source_system="weather_api",
        source_provider="synthetic_reference",
        source_reference="weather_forecast",
        source_url_or_entity_id="weather_forecast",
        source_scope="public_open",
        freshness_status="fresh",
    )
    stale_soc = _signal(
        signal_provenance_id="scenario_soc_stale_v1",
        signal_id="scenario_soc_stale",
        signal_name="Scenario SOC Stale",
        signal_class="home_assistant_entity",
        source_system="home_assistant",
        source_provider="local_entity",
        source_reference="sensor.battery_soc",
        source_url_or_entity_id="sensor.battery_soc",
        source_scope="local_home",
        freshness_status="stale",
        control_capable=True,
    )
    fresh_soc = _signal(
        signal_provenance_id="scenario_soc_fresh_v1",
        signal_id="scenario_soc_fresh",
        signal_name="Scenario SOC Fresh",
        signal_class="home_assistant_entity",
        source_system="home_assistant",
        source_provider="local_entity",
        source_reference="sensor.battery_soc",
        source_url_or_entity_id="sensor.battery_soc",
        source_scope="local_home",
        freshness_status="fresh",
        control_capable=True,
    )
    departure = _signal(
        signal_provenance_id="scenario_departure_v1",
        signal_id="scenario_departure_time",
        signal_name="Scenario Departure Time",
        signal_class="manual_owner_signal",
        source_system="manual_owner",
        source_provider="owner_note",
        source_reference="departure_time",
        source_url_or_entity_id="departure_time",
        source_scope="manual",
        freshness_status="fresh",
    )

    examples = [
        _scenario_packet_for_price_vs_carbon(price, carbon, forecast_examples),
        _scenario_packet_for_pv_weather(cloudy_pv, forecast_examples),
        _scenario_packet_for_stale_soc(stale_soc, forecast_examples),
        _scenario_packet_for_ev_deadline(fresh_soc, departure, forecast_examples),
        _scenario_packet_for_heat_pump(price, carbon, forecast_examples),
        _scenario_packet_for_artifact_blocked(by_id["artifact_build_forecast_missing_validation_runner_forecast"], forecast_examples),
        _scenario_packet_for_public_pilot_blocked(by_id["public_pilot_forecast_blocked_claim_lifecycle_missing_forecast"], forecast_examples),
        _scenario_packet_for_wifi_privacy_blocked(by_id["wifi_rf_research_forecast_blocked_privacy_boundary_missing_forecast"], forecast_examples),
        _scenario_packet_for_tri_engine_runtime_later(by_id["tri_engine_orchestration_forecast_preserved_for_runtime_later_forecast"], forecast_examples),
        _scenario_packet_for_implementation_wave_continue(by_id["next_lane_forecast_capability_registry_to_implementation_wave_forecast"], forecast_examples),
    ]
    return examples


def _scenario_packet_for_price_vs_carbon(price: SignalProvenanceRecord, carbon: SignalProvenanceRecord, forecasts: list[FutureStateForecastPacket]) -> ScenarioSimulationPacket:
    request = build_scenario_simulation_request_v1(
        request_id="energy_price_vs_carbon_three_branches",
        subject="energy_price_vs_carbon_three_branches",
        domain="energy_home_scenario",
        forecast_packets=[forecasts[1]],
        signal_records=[price, carbon],
        conflict_decisions=[_conflict("energy_price_vs_carbon_three_branches", ["price_vs_carbon_conflict"], [price, carbon], scenario_branch_required=True)],
        assumptions=["owner priority is not yet resolved"],
        known_constraints=["compare cost and carbon branches"],
        scenario_hints=["price vs carbon"],
        branch_preferences=["cost_optimized_branch", "carbon_optimized_branch", "baseline_branch"],
        recommended_next_lane="IMPLEMENT_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1",
    )
    return build_scenario_simulation_packet_v1(request)


def _scenario_packet_for_pv_weather(cloudy_pv: SignalProvenanceRecord, forecasts: list[FutureStateForecastPacket]) -> ScenarioSimulationPacket:
    request = build_scenario_simulation_request_v1(
        request_id="pv_surplus_sunny_vs_cloudy_branches",
        subject="pv_surplus_sunny_vs_cloudy_branches",
        domain="energy_home_scenario",
        forecast_packets=[forecasts[2]],
        signal_records=[cloudy_pv],
        assumptions=["sunny and cloudy branches must stay separate"],
        known_constraints=["weather uncertainty remains bounded"],
        scenario_hints=["pv weather uncertainty"],
        branch_preferences=["optimistic_branch", "conservative_branch"],
        recommended_next_lane="IMPLEMENT_WESLR_FUTURE_STATE_FORECASTING_ENGINE_V1",
    )
    return build_scenario_simulation_packet_v1(request)


def _scenario_packet_for_stale_soc(stale_soc: SignalProvenanceRecord, forecasts: list[FutureStateForecastPacket]) -> ScenarioSimulationPacket:
    request = build_scenario_simulation_request_v1(
        request_id="battery_reserve_wait_and_observe_stale_soc",
        subject="battery_reserve_wait_and_observe_stale_soc",
        domain="energy_home_scenario",
        forecast_packets=[forecasts[3]],
        signal_records=[stale_soc],
        assumptions=["stale soc must not drive a forced action"],
        known_constraints=["wait or block rather than guess"],
        scenario_hints=["stale soc"],
        branch_preferences=["wait_and_observe_branch", "blocked_branch"],
        recommended_next_lane="IMPLEMENT_WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1",
    )
    return build_scenario_simulation_packet_v1(request)


def _scenario_packet_for_ev_deadline(fresh_soc: SignalProvenanceRecord, departure: SignalProvenanceRecord, forecasts: list[FutureStateForecastPacket]) -> ScenarioSimulationPacket:
    request = build_scenario_simulation_request_v1(
        request_id="ev_deadline_first_branch_missing_departure_time",
        subject="ev_deadline_first_branch_missing_departure_time",
        domain="energy_home_scenario",
        forecast_packets=[forecasts[4]],
        signal_records=[fresh_soc, departure],
        missing_inputs=["departure_time"],
        assumptions=["deadline planning needs departure metadata"],
        known_constraints=["deadline branch requires schedule metadata"],
        scenario_hints=["deadline first"],
        branch_preferences=["deadline_first_branch", "blocked_branch"],
        recommended_next_lane="IMPLEMENT_WESLR_FORECAST_ERROR_LEDGER_V1",
    )
    return build_scenario_simulation_packet_v1(request)


def _scenario_packet_for_heat_pump(price: SignalProvenanceRecord, carbon: SignalProvenanceRecord, forecasts: list[FutureStateForecastPacket]) -> ScenarioSimulationPacket:
    request = build_scenario_simulation_request_v1(
        request_id="heat_pump_comfort_first_vs_cost_branch",
        subject="heat_pump_comfort_first_vs_cost_branch",
        domain="energy_home_scenario",
        forecast_packets=[forecasts[1]],
        signal_records=[price, carbon],
        conflict_decisions=[_conflict("heat_pump_comfort_first_vs_cost_branch", ["price_vs_comfort_conflict"], [price, carbon], scenario_branch_required=True)],
        assumptions=["comfort and cost remain in tension"],
        known_constraints=["compare comfort first and cost first branches"],
        scenario_hints=["comfort vs cost"],
        branch_preferences=["comfort_first_branch", "cost_optimized_branch"],
        recommended_next_lane="IMPLEMENT_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1",
    )
    return build_scenario_simulation_packet_v1(request)


def _scenario_packet_for_artifact_blocked(forecast: FutureStateForecastPacket, forecasts: list[FutureStateForecastPacket]) -> ScenarioSimulationPacket:
    runner = _capability(
        capability_id="artifact_validation_runner_missing",
        capability_name="Artifact Validation Runner Missing",
        family="artifact_and_code_generation",
        maturity="design_only",
        next_lane="DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1",
    )
    request = build_scenario_simulation_request_v1(
        request_id="artifact_build_validation_runner_missing_blocked_branch",
        subject="artifact_build_validation_runner_missing_blocked_branch",
        domain="artifact_build_scenario",
        forecast_packets=[forecast],
        capability_maturity_records=[runner],
        missing_inputs=["validation_runner"],
        assumptions=["artifact build should not proceed without validation"],
        known_constraints=["blocked branch until runner exists"],
        scenario_hints=["artifact build blocked"],
        branch_preferences=["blocked_branch"],
        recommended_next_lane="DESIGN_WESLR_SOURCE_EVIDENCE_GRAPH_V1",
    )
    return build_scenario_simulation_packet_v1(request)


def _scenario_packet_for_public_pilot_blocked(forecast: FutureStateForecastPacket, forecasts: list[FutureStateForecastPacket]) -> ScenarioSimulationPacket:
    request = build_scenario_simulation_request_v1(
        request_id="public_pilot_claim_lifecycle_missing_blocked_branch",
        subject="public_pilot_claim_lifecycle_missing_blocked_branch",
        domain="product_market_scenario",
        forecast_packets=[forecast],
        missing_inputs=["claim_lifecycle_evidence"],
        assumptions=["external release claims need lifecycle evidence"],
        known_constraints=["keep release assertions internal only"],
        scenario_hints=["claim lifecycle missing"],
        branch_preferences=["blocked_branch"],
        recommended_next_lane="DESIGN_WESLR_PUBLIC_CLAIM_LIFECYCLE_TRACKER_V1",
    )
    return build_scenario_simulation_packet_v1(request)


def _scenario_packet_for_wifi_privacy_blocked(forecast: FutureStateForecastPacket, forecasts: list[FutureStateForecastPacket]) -> ScenarioSimulationPacket:
    request = build_scenario_simulation_request_v1(
        request_id="wifi_rf_privacy_boundary_missing_blocked_branch",
        subject="wifi_rf_privacy_boundary_missing_blocked_branch",
        domain="wifi_rf_sensing_scenario",
        forecast_packets=[forecast],
        missing_inputs=["privacy_boundary"],
        assumptions=["rf sensing requires explicit privacy boundary"],
        known_constraints=["do not expand beyond privacy scope"],
        scenario_hints=["privacy boundary missing"],
        branch_preferences=["blocked_branch"],
        recommended_next_lane="DESIGN_WESLR_PRIVACY_SENSITIVE_SIGNAL_PROCESSING_BOUNDARY_V1",
    )
    return build_scenario_simulation_packet_v1(request)


def _scenario_packet_for_tri_engine_runtime_later(forecast: FutureStateForecastPacket, forecasts: list[FutureStateForecastPacket]) -> ScenarioSimulationPacket:
    request = build_scenario_simulation_request_v1(
        request_id="tri_engine_runtime_later_orchestration_branch",
        subject="tri_engine_runtime_later_orchestration_branch",
        domain="weslr_project_scenario",
        forecast_packets=[forecast],
        assumptions=["runtime orchestration is still later work"],
        known_constraints=["preserve orchestration boundary"],
        scenario_hints=["orchestration later"],
        branch_preferences=["wait_and_observe_branch"],
        recommended_next_lane="DESIGN_WESLR_TRI_ENGINE_ORCHESTRATION_BOUNDARY_V1",
    )
    return build_scenario_simulation_packet_v1(request)


def _scenario_packet_for_implementation_wave_continue(forecast: FutureStateForecastPacket, forecasts: list[FutureStateForecastPacket]) -> ScenarioSimulationPacket:
    request = build_scenario_simulation_request_v1(
        request_id="implementation_wave_continue_future_forecast_to_scenario",
        subject="implementation_wave_continue_future_forecast_to_scenario",
        domain="weslr_project_scenario",
        forecast_packets=[forecast],
        assumptions=["implementation wave should continue"],
        known_constraints=["keep runtime later"],
        scenario_hints=["implementation wave continue"],
        branch_preferences=["baseline_branch"],
        recommended_next_lane="IMPLEMENT_WESLR_FUTURE_STATE_FORECASTING_ENGINE_V1",
    )
    return build_scenario_simulation_packet_v1(request)
