"""Metadata-only future-state forecasting engine helpers v1.

This module builds bounded forecast packets from supplied metadata only. It is
pure, deterministic, import-safe, and fail-closed.

It does not call APIs. It does not fetch live data. It does not connect to Home
Assistant. It does not call models/providers. It does not execute UNKNOWN
ENGINE or NAIE. It does not write memory or `.weslr`. It does not control
devices or create automations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from weslr.capability_maturity_registry import (
    CapabilityMaturityRecord,
    build_capability_maturity_record_v1,
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
    summarize_forecast_error_record_v1,
    to_forecast_error_json_safe_v1,
    validate_forecast_error_record_v1,
)
from weslr.signal_provenance_freshness_model import (
    SignalProvenanceRecord,
    build_signal_provenance_record_v1,
    summarize_signal_provenance_record_v1,
    to_signal_provenance_json_safe_v1,
    validate_signal_provenance_record_v1,
)

HELPER_TYPE_V1 = "future_state_forecasting_engine_v1"
REQUEST_TYPE_V1 = "future_state_forecast_request_v1"
PACKET_TYPE_V1 = "future_state_forecast_packet_v1"
SUMMARY_TYPE_V1 = "future_state_forecast_packet_summary_v1"

ALLOWED_FORECAST_DOMAINS_V1 = {
    "weslr_project_forecast",
    "artifact_build_forecast",
    "energy_home_forecast",
    "grid_signal_forecast",
    "scenario_simulation",
    "operator_workflow_forecast",
    "product_market_forecast",
    "wifi_rf_sensing_forecast",
    "research_to_prototype_forecast",
    "unknown_domain",
}

ALLOWED_FORECAST_HORIZONS_V1 = {
    "immediate",
    "short_term",
    "medium_term",
    "long_term",
    "unknown_horizon",
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

ALLOWED_FORECAST_STATUS_LABELS_V1 = {
    "forecast_ready",
    "forecast_ready_with_uncertainty",
    "scenario_branch_required",
    "blocked_missing_signal",
    "blocked_conflicting_signal",
    "blocked_stale_signal",
    "blocked_authority_boundary",
    "unknown_status",
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

DEFAULT_CREATED_TIMESTAMP_V1 = "2026-06-01T20:52:00+02:00"
DEFAULT_DOMAIN_V1 = "unknown_domain"
DEFAULT_HORIZON_V1 = "unknown_horizon"
DEFAULT_CONFIDENCE_V1 = "unknown_confidence"
DEFAULT_UNCERTAINTY_V1 = "unknown_uncertainty"
DEFAULT_STATUS_V1 = "unknown_status"
DEFAULT_RECOMMENDED_NEXT_LANE_V1 = "IMPLEMENT_WESLR_FUTURE_STATE_FORECASTING_ENGINE_V1"
DEFAULT_FORECAST_ERROR_LEDGER_READY_V1 = True

STALE_FRESHNESS_STATUSES_V1 = {
    "stale",
    "expired",
    "missing_timestamp",
    "future_timestamp",
}

CONFLICTING_DECISION_STATUSES_V1 = {
    "scenario_branch_required",
    "blocked_conflicting_signal",
}

MISSING_SIGNAL_STATUSES_V1 = {
    "blocked_missing_signal",
    "unknown_status",
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FutureStateForecastRequest:
    request_id: str
    subject: str
    domain: str
    forecast_horizon: str
    signal_records: list[SignalProvenanceRecord]
    conflict_decisions: list[EnergySignalConflictDecision]
    capability_maturity_records: list[CapabilityMaturityRecord]
    forecast_error_records: list[ForecastErrorRecord]
    assumptions: list[str]
    known_constraints: list[str]
    missing_inputs: list[str]
    scenario_hints: list[str]
    recommended_next_lane: str
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class FutureStateForecastPacket:
    forecast_id: str
    subject: str
    domain: str
    forecast_horizon: str
    created_timestamp: str
    input_summary: dict[str, Any]
    signal_refs: list[str]
    signal_provenance_summary: list[dict[str, Any]]
    freshness_summary: dict[str, str]
    conflict_decision_refs: list[str]
    conflict_summary: dict[str, Any]
    capability_maturity_refs: list[str]
    assumptions: list[str]
    known_constraints: list[str]
    missing_inputs: list[str]
    scenario_branches: list[dict[str, Any]]
    forecasted_state: dict[str, Any]
    forecast_status: str
    confidence_label: str
    uncertainty_label: str
    invalidation_triggers: list[str]
    recommended_next_observation: str
    recommended_next_lane: str
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
class FutureStateForecastPacketSummary:
    summary_type: str
    forecast_id: str
    subject: str
    domain: str
    forecast_horizon: str
    forecast_status: str
    confidence_label: str
    uncertainty_label: str
    missing_input_count: int
    scenario_branch_count: int
    recommendation_only: bool
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


def to_future_state_forecast_json_safe_v1(value: Any) -> Any:
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


def _record_like(item: Any) -> SignalProvenanceRecord:
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


def _freshness_summary(records: Iterable[SignalProvenanceRecord]) -> dict[str, str]:
    summary: dict[str, str] = {}
    for record in records:
        summary[record.signal_id] = record.freshness_status
    return dict(sorted(summary.items()))


def _provenance_summary(records: Iterable[SignalProvenanceRecord]) -> list[dict[str, Any]]:
    return [to_signal_provenance_json_safe_v1(summarize_signal_provenance_record_v1(record)) for record in records]


def _conflict_summary(decisions: Iterable[EnergySignalConflictDecision]) -> dict[str, Any]:
    conflict_classes = []
    unresolved = []
    scenario_branch_required = False
    for decision in decisions:
        conflict_classes.extend(decision.conflict_classes)
        unresolved.extend(decision.unresolved_conflicts)
        scenario_branch_required = scenario_branch_required or decision.scenario_branch_required
    unique_conflicts = sorted(set(conflict_classes))
    return {
        "conflict_classes": unique_conflicts,
        "decision_count": len(list(decisions)) if isinstance(decisions, list) else None,
        "scenario_branch_required": scenario_branch_required,
        "unresolved_conflicts": sorted(set(unresolved)),
    }


def _forecasted_state_from_request(request: FutureStateForecastRequest) -> dict[str, Any]:
    if not request.signal_records:
        return {
            "summary": "insufficient evidence to forecast a stable state",
            "state_kind": "unknown",
        }
    freshness = _freshness_summary(request.signal_records)
    signal_classes = sorted({record.signal_class for record in request.signal_records})
    return {
        "summary": f"bounded forecast for {request.subject}",
        "state_kind": "scenario_based",
        "signal_classes": signal_classes,
        "freshness_classes": sorted(set(freshness.values())),
    }


def _scenario_branches_from_request(request: FutureStateForecastRequest, status: str) -> list[dict[str, Any]]:
    branches: list[dict[str, Any]] = []
    if status == "scenario_branch_required" or any(decision.scenario_branch_required for decision in request.conflict_decisions):
        branches.append(
            {
                "branch_id": f"{request.request_id}_branch_primary",
                "branch_type": "preserve_conflict",
                "next_check": request.recommended_next_lane,
            }
        )
        branches.append(
            {
                "branch_id": f"{request.request_id}_branch_safety",
                "branch_type": "safety_first",
                "next_check": "collect_missing_fresh_signals",
            }
        )
    elif status in {"blocked_missing_signal", "blocked_stale_signal", "blocked_conflicting_signal"}:
        branches.append(
            {
                "branch_id": f"{request.request_id}_blocked_followup",
                "branch_type": "blocked_followup",
                "next_check": request.missing_inputs[:1] or [request.recommended_next_lane],
            }
        )
    return branches


def _classify_confidence_and_uncertainty(
    status: str,
    freshness_values: list[str],
    conflict_values: list[str],
    missing_inputs: list[str],
    signal_count: int,
) -> tuple[str, str]:
    if status == "blocked_missing_signal" or missing_inputs:
        return "blocked_insufficient_evidence", "high_uncertainty"
    if status == "blocked_stale_signal":
        return "low_confidence", "high_uncertainty"
    if status == "blocked_conflicting_signal" or status == "scenario_branch_required":
        return "medium_confidence", "high_uncertainty"
    if any(value in STALE_FRESHNESS_STATUSES_V1 for value in freshness_values):
        return "low_confidence", "medium_uncertainty"
    if any(value != "no_conflict" for value in conflict_values):
        return "medium_confidence", "medium_uncertainty"
    if signal_count >= 3:
        return "high_confidence", "low_uncertainty"
    if signal_count == 1:
        return "medium_confidence", "medium_uncertainty"
    return "unknown_confidence", "unknown_uncertainty"


def _classify_status(request: FutureStateForecastRequest) -> str:
    if request.domain == "unknown_domain" or request.forecast_horizon == "unknown_horizon":
        return "unknown_status"
    if request.missing_inputs:
        return "blocked_missing_signal"
    freshness_values = [record.freshness_status for record in request.signal_records]
    if any(status in STALE_FRESHNESS_STATUSES_V1 for status in freshness_values):
        return "blocked_stale_signal"
    conflict_statuses = [decision.recommended_resolution_strategy for decision in request.conflict_decisions]
    if any(decision.scenario_branch_required for decision in request.conflict_decisions) or any(value in CONFLICTING_DECISION_STATUSES_V1 for value in conflict_statuses):
        return "scenario_branch_required"
    if any(decision.unresolved_conflicts for decision in request.conflict_decisions):
        return "blocked_conflicting_signal"
    if not request.signal_records:
        return "blocked_missing_signal"
    if request.capability_maturity_records:
        if any(record.current_maturity == "blocked_or_deprecated" or record.current_authority == "blocked" for record in request.capability_maturity_records):
            return "blocked_authority_boundary"
    return "forecast_ready_with_uncertainty" if len(request.signal_records) == 1 else "forecast_ready"


def _recommended_next_observation(request: FutureStateForecastRequest, status: str) -> str:
    if status == "blocked_missing_signal":
        return request.missing_inputs[0] if request.missing_inputs else "collect_missing_signal_metadata"
    if status == "blocked_stale_signal":
        return "refresh_stale_signal_and_rebuild_forecast"
    if status == "scenario_branch_required":
        return "compare_scenario_branches_against_owner_priority"
    if status == "blocked_conflicting_signal":
        return "resolve_signal_conflict_before_forecast"
    if status == "blocked_authority_boundary":
        return "separate_authority_from_metadata_and_retry"
    if request.domain == "artifact_build_forecast":
        return "confirm_validation_runner_before_any_build_step"
    if request.domain == "energy_home_forecast":
        return "collect_fresh_signal_and_conflict_resolution_metadata"
    if request.domain == "wifi_rf_sensing_forecast":
        return "confirm_privacy_boundary_and_source_scope"
    return "maintain_monitoring_and_rebuild_if_inputs_change"


def _recommended_next_lane(request: FutureStateForecastRequest, status: str) -> str:
    if request.recommended_next_lane:
        return request.recommended_next_lane
    if request.domain == "energy_home_forecast":
        return "IMPLEMENT_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1"
    if request.domain == "artifact_build_forecast":
        return "DESIGN_WESLR_SOURCE_EVIDENCE_GRAPH_V1"
    if request.domain == "weslr_project_forecast":
        return "IMPLEMENT_WESLR_CAPABILITY_MATURITY_REGISTRY_V1"
    if status == "scenario_branch_required":
        return "DESIGN_WESLR_TRI_ENGINE_ORCHESTRATION_BOUNDARY_V1"
    return DEFAULT_RECOMMENDED_NEXT_LANE_V1


def build_future_state_forecast_request_v1(
    *,
    request_id: str,
    subject: str,
    domain: str,
    forecast_horizon: str,
    signal_records: Iterable[Any] | None = None,
    conflict_decisions: Iterable[Any] | None = None,
    capability_maturity_records: Iterable[Any] | None = None,
    forecast_error_records: Iterable[Any] | None = None,
    assumptions: Iterable[str] | None = None,
    known_constraints: Iterable[str] | None = None,
    missing_inputs: Iterable[str] | None = None,
    scenario_hints: Iterable[str] | None = None,
    recommended_next_lane: str = DEFAULT_RECOMMENDED_NEXT_LANE_V1,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> FutureStateForecastRequest:
    request = FutureStateForecastRequest(
        request_id=_safe_text(request_id),
        subject=_safe_text(subject),
        domain=_safe_text(domain),
        forecast_horizon=_safe_text(forecast_horizon),
        signal_records=[_record_like(item) for item in (signal_records or [])],
        conflict_decisions=[_decision_like(item) for item in (conflict_decisions or [])],
        capability_maturity_records=[_maturity_like(item) for item in (capability_maturity_records or [])],
        forecast_error_records=[_error_like(item) for item in (forecast_error_records or [])],
        assumptions=_safe_list(assumptions),
        known_constraints=_safe_list(known_constraints),
        missing_inputs=_safe_list(missing_inputs),
        scenario_hints=_safe_list(scenario_hints),
        recommended_next_lane=_safe_text(recommended_next_lane),
        safe_metadata={"metadata_only": True, "internal_only": True, **dict(safe_metadata or {}), **dict(extra_metadata)},
    )
    return request


def build_future_state_forecast_packet_v1(
    request: Any,
    /,
    *,
    created_timestamp: str = DEFAULT_CREATED_TIMESTAMP_V1,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> FutureStateForecastPacket:
    normalized_request = request if isinstance(request, FutureStateForecastRequest) else build_future_state_forecast_request_v1(**dict(request)) if isinstance(request, Mapping) else build_future_state_forecast_request_v1(**asdict(request)) if is_dataclass(request) else None
    if normalized_request is None:
        raise ValidationError("unknown_request")

    status = _classify_status(normalized_request)
    freshness_summary = _freshness_summary(normalized_request.signal_records)
    conflict_values = [decision.recommended_resolution_strategy for decision in normalized_request.conflict_decisions]
    confidence_label, uncertainty_label = _classify_confidence_and_uncertainty(
        status,
        list(freshness_summary.values()),
        conflict_values,
        normalized_request.missing_inputs,
        len(normalized_request.signal_records),
    )
    forecast_error_ledger_ready = bool(
        normalized_request.forecast_error_records
        or normalized_request.missing_inputs
        or any(value in STALE_FRESHNESS_STATUSES_V1 for value in freshness_summary.values())
        or any(decision.scenario_branch_required or decision.unresolved_conflicts for decision in normalized_request.conflict_decisions)
    )
    packet = FutureStateForecastPacket(
        forecast_id=f"{normalized_request.request_id}_forecast",
        subject=normalized_request.subject,
        domain=normalized_request.domain,
        forecast_horizon=normalized_request.forecast_horizon,
        created_timestamp=_safe_text(created_timestamp),
        input_summary={
            "request_id": normalized_request.request_id,
            "signal_count": len(normalized_request.signal_records),
            "conflict_decision_count": len(normalized_request.conflict_decisions),
            "capability_maturity_count": len(normalized_request.capability_maturity_records),
            "forecast_error_count": len(normalized_request.forecast_error_records),
            "scenario_hint_count": len(normalized_request.scenario_hints),
            "assumption_count": len(normalized_request.assumptions),
            "constraint_count": len(normalized_request.known_constraints),
        },
        signal_refs=[record.signal_id for record in normalized_request.signal_records],
        signal_provenance_summary=_provenance_summary(normalized_request.signal_records),
        freshness_summary=freshness_summary,
        conflict_decision_refs=[decision.conflict_decision_id for decision in normalized_request.conflict_decisions],
        conflict_summary={
            "conflict_classes": sorted({conflict for decision in normalized_request.conflict_decisions for conflict in decision.conflict_classes}),
            "scenario_branch_required": any(decision.scenario_branch_required for decision in normalized_request.conflict_decisions),
            "unresolved_conflicts": sorted({conflict for decision in normalized_request.conflict_decisions for conflict in decision.unresolved_conflicts}),
            "decision_summaries": [to_energy_signal_conflict_json_safe_v1(summarize_energy_signal_conflict_decision_v1(decision)) for decision in normalized_request.conflict_decisions],
        },
        capability_maturity_refs=[record.capability_id for record in normalized_request.capability_maturity_records],
        assumptions=list(normalized_request.assumptions),
        known_constraints=list(normalized_request.known_constraints),
        missing_inputs=list(normalized_request.missing_inputs),
        scenario_branches=_scenario_branches_from_request(normalized_request, status),
        forecasted_state=_forecasted_state_from_request(normalized_request),
        forecast_status=status,
        confidence_label=confidence_label,
        uncertainty_label=uncertainty_label,
        invalidation_triggers=sorted({
            *({"missing_input"} if normalized_request.missing_inputs else set()),
            *({"stale_signal"} if any(value in STALE_FRESHNESS_STATUSES_V1 for value in freshness_summary.values()) else set()),
            *({"conflict"} if any(decision.scenario_branch_required or decision.unresolved_conflicts for decision in normalized_request.conflict_decisions) else set()),
            *({"authority_boundary"} if any(record.current_authority == "blocked" or record.current_maturity == "blocked_or_deprecated" for record in normalized_request.capability_maturity_records) else set()),
        }),
        recommended_next_observation=_recommended_next_observation(normalized_request, status),
        recommended_next_lane=_recommended_next_lane(normalized_request, status),
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
    validate_future_state_forecast_packet_v1(packet)
    return packet


def validate_future_state_forecast_packet_v1(packet: Any) -> bool:
    original = packet if isinstance(packet, Mapping) else asdict(packet) if is_dataclass(packet) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    if _contains_forbidden_claim(original):
        raise ValidationError("forbidden_claim_marker_detected")
    normalized = packet if isinstance(packet, FutureStateForecastPacket) else FutureStateForecastPacket(**dict(packet)) if isinstance(packet, Mapping) else FutureStateForecastPacket(**asdict(packet)) if is_dataclass(packet) else None
    if normalized is None:
        raise ValidationError("unknown_packet")
    if normalized.domain not in ALLOWED_FORECAST_DOMAINS_V1:
        raise ValidationError("unknown_domain")
    if normalized.forecast_horizon not in ALLOWED_FORECAST_HORIZONS_V1:
        raise ValidationError("unknown_horizon")
    if normalized.confidence_label not in ALLOWED_CONFIDENCE_LABELS_V1:
        raise ValidationError("unknown_confidence")
    if normalized.uncertainty_label not in ALLOWED_UNCERTAINTY_LABELS_V1:
        raise ValidationError("unknown_uncertainty")
    if normalized.forecast_status not in ALLOWED_FORECAST_STATUS_LABELS_V1:
        raise ValidationError("unknown_status")
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
    for signal in normalized.signal_provenance_summary:
        if _contains_forbidden_field(signal) or _contains_forbidden_claim(signal):
            raise ValidationError("forbidden_signal_summary_detected")
    if _contains_forbidden_field(normalized.safe_metadata) or _contains_forbidden_claim(normalized.safe_metadata):
        raise ValidationError("forbidden_safe_metadata_detected")
    return True


def summarize_future_state_forecast_packet_v1(packet: Any) -> FutureStateForecastPacketSummary:
    normalized = packet if isinstance(packet, FutureStateForecastPacket) else FutureStateForecastPacket(**dict(packet)) if isinstance(packet, Mapping) else FutureStateForecastPacket(**asdict(packet)) if is_dataclass(packet) else None
    if normalized is None:
        raise ValidationError("unknown_packet")
    validate_future_state_forecast_packet_v1(normalized)
    return FutureStateForecastPacketSummary(
        summary_type=SUMMARY_TYPE_V1,
        forecast_id=normalized.forecast_id,
        subject=normalized.subject,
        domain=normalized.domain,
        forecast_horizon=normalized.forecast_horizon,
        forecast_status=normalized.forecast_status,
        confidence_label=normalized.confidence_label,
        uncertainty_label=normalized.uncertainty_label,
        missing_input_count=len(normalized.missing_inputs),
        scenario_branch_count=len(normalized.scenario_branches),
        recommendation_only=normalized.recommendation_only,
        recommended_next_lane=normalized.recommended_next_lane,
    )


def _base_signal(
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
    retrieval_timestamp: str = "2026-06-01T20:00:00+02:00",
    reported_timestamp: str = "2026-06-01T19:59:00+02:00",
    freshness_status: str | None = None,
    confidence_controls: bool = False,
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
        retrieval_timestamp=retrieval_timestamp,
        reported_timestamp=reported_timestamp,
        freshness_status=freshness_status,
        control_capable=confidence_controls,
        forecasting_allowed=True,
        scenario_simulation_allowed=True,
        memory_write_allowed=False,
        action_authority_granted=False,
        safe_metadata={"synthetic": True, "metadata_only": True},
    )


def _base_conflict(*, conflict_decision_id: str, subject: str, conflict_classes: Iterable[str], involved_signals: Iterable[SignalProvenanceRecord], scenario_branch_required: bool = False) -> EnergySignalConflictDecision:
    return build_energy_signal_conflict_decision_v1(
        conflict_decision_id=conflict_decision_id,
        decision_subject=subject,
        conflict_classes=list(conflict_classes),
        involved_signals=list(involved_signals),
        scenario_branch_required=scenario_branch_required,
        safe_recommendation_mode="recommendation_only",
    )


def _base_capability(*, capability_id: str, capability_name: str, family: str, maturity: str, next_lane: str) -> CapabilityMaturityRecord:
    return build_capability_maturity_record_v1(
        capability_id=capability_id,
        capability_name=capability_name,
        capability_family=family,
        current_maturity=maturity,
        latest_commit="static_reference_v1",
        latest_judgment="metadata_only",
        owner_approval_required=False,
        recommended_next_lane=next_lane,
        safe_metadata={"synthetic": True},
    )


def _base_error(*, record_id: str, subject: str, domain: str, horizon: str, error_type: str) -> ForecastErrorRecord:
    return build_forecast_error_record_v1(
        forecast_error_record_id=record_id,
        source_forecast_id=f"{record_id}_source_forecast",
        source_scenario_simulation_id=f"{record_id}_source_scenario",
        source_energy_intelligence_id=f"{record_id}_source_energy_intel",
        subject=subject,
        domain=domain,
        forecast_horizon=horizon,
        expected_outcome="synthetic expected outcome",
        observed_outcome="synthetic observed outcome",
        outcome_match_status="missed",
        error_type=error_type,
        error_severity="moderate",
        confidence_before=0.74,
        confidence_after=0.33,
        assumptions_used=["synthetic assumption"],
        assumptions_failed=["synthetic failed assumption"],
        signals_used=["synthetic_signal"],
        stale_signals=[],
        missing_signals=[],
        conflicting_signals=[],
        recommendation_taken="bounded_recommendation",
        owner_action_taken="metadata_only_review",
        action_authority_used=False,
        resulting_effect="synthetic outcome",
        corrective_lesson="review the missing signal boundary",
        recommended_model_update="preserve evidence-scope gating",
        behavior_pack_candidate="behavior_pack_candidate_metadata_only",
        requires_owner_review=True,
        safe_metadata={"synthetic": True},
    )


def build_initial_future_state_forecast_examples_v1() -> list[FutureStateForecastPacket]:
    examples: list[FutureStateForecastPacket] = []

    examples.append(
        build_future_state_forecast_packet_v1(
            build_future_state_forecast_request_v1(
                request_id="next_lane_forecast_capability_registry_to_implementation_wave",
                subject="next_lane_forecast_capability_registry_to_implementation_wave",
                domain="weslr_project_forecast",
                forecast_horizon="immediate",
                capability_maturity_records=[
                    _base_capability(
                        capability_id="capability_registry_v1",
                        capability_name="Capability Maturity Registry",
                        family="friction_and_behavior_packs",
                        maturity="validated",
                        next_lane="IMPLEMENT_WESLR_FUTURE_STATE_FORECASTING_ENGINE_V1",
                    )
                ],
                assumptions=["implementation wave should continue"],
                known_constraints=["metadata only"],
                missing_inputs=[],
                scenario_hints=["continue implementation wave"],
            )
        )
    )

    fresh_soc = _base_signal(
        signal_provenance_id="energy_soc_fresh_v1",
        signal_id="battery_soc_fresh",
        signal_name="Battery SoC Fresh",
        signal_class="home_assistant_entity",
        source_system="home_assistant",
        source_provider="local_entity",
        source_reference="sensor.battery_soc",
        source_url_or_entity_id="sensor.battery_soc",
        source_scope="local_home",
        freshness_status="fresh",
        confidence_controls=True,
    )
    grid_import = _base_signal(
        signal_provenance_id="grid_import_price_v1",
        signal_id="grid_import_price_current",
        signal_name="Grid Import Price Current",
        signal_class="electricity_price_provider",
        source_system="price_api",
        source_provider="static_metadata",
        source_reference="price_day_ahead",
        source_url_or_entity_id="price_day_ahead",
        source_scope="public_open",
        freshness_status="fresh",
    )
    examples.append(
        build_future_state_forecast_packet_v1(
            build_future_state_forecast_request_v1(
                request_id="energy_evening_grid_import_risk_with_fresh_signals",
                subject="energy_evening_grid_import_risk_with_fresh_signals",
                domain="energy_home_forecast",
                forecast_horizon="short_term",
                signal_records=[fresh_soc, grid_import],
                assumptions=["evening demand may increase"],
                known_constraints=["avoid unnecessary grid import"],
                scenario_hints=["load shifting"],
            )
        )
    )

    pv_weather = _base_signal(
        signal_provenance_id="pv_weather_uncertain_v1",
        signal_id="pv_weather_uncertain",
        signal_name="PV Weather Uncertain",
        signal_class="weather_provider",
        source_system="weather_api",
        source_provider="synthetic_reference",
        source_reference="weather_forecast",
        source_url_or_entity_id="weather_forecast",
        source_scope="public_open",
        freshness_status="fresh",
    )
    examples.append(
        build_future_state_forecast_packet_v1(
            build_future_state_forecast_request_v1(
                request_id="pv_surplus_likelihood_with_weather_uncertainty",
                subject="pv_surplus_likelihood_with_weather_uncertainty",
                domain="energy_home_forecast",
                forecast_horizon="medium_term",
                signal_records=[pv_weather],
                assumptions=["weather may improve"],
                known_constraints=["forecast remains uncertain"],
                scenario_hints=["surplus likely if irradiance rises"],
            )
        )
    )

    stale_soc = _base_signal(
        signal_provenance_id="battery_soc_stale_v1",
        signal_id="battery_soc_stale",
        signal_name="Battery SoC Stale",
        signal_class="home_assistant_entity",
        source_system="home_assistant",
        source_provider="local_entity",
        source_reference="sensor.battery_soc",
        source_url_or_entity_id="sensor.battery_soc",
        source_scope="local_home",
        freshness_status="stale",
        confidence_controls=True,
    )
    examples.append(
        build_future_state_forecast_packet_v1(
            build_future_state_forecast_request_v1(
                request_id="battery_reserve_depletion_risk_with_stale_soc_blocked",
                subject="battery_reserve_depletion_risk_with_stale_soc_blocked",
                domain="energy_home_forecast",
                forecast_horizon="short_term",
                signal_records=[stale_soc],
                assumptions=["battery reserve matters"],
                known_constraints=["stale signal cannot authorise action"],
                scenario_hints=["block until fresh SOC"],
            )
        )
    )

    examples.append(
        build_future_state_forecast_packet_v1(
            build_future_state_forecast_request_v1(
                request_id="ev_deadline_risk_missing_departure_time",
                subject="ev_deadline_risk_missing_departure_time",
                domain="energy_home_forecast",
                forecast_horizon="short_term",
                signal_records=[fresh_soc],
                missing_inputs=["departure_time"],
                assumptions=["ev needs readiness by departure"],
                known_constraints=["deadline cannot be inferred without departure time"],
            )
        )
    )

    price = _base_signal(
        signal_provenance_id="price_conflict_v1",
        signal_id="price_signal",
        signal_name="Price Signal",
        signal_class="electricity_price_provider",
        source_system="price_api",
        source_provider="static_metadata",
        source_reference="price_day_ahead",
        source_url_or_entity_id="price_day_ahead",
        source_scope="public_open",
        freshness_status="fresh",
    )
    carbon = _base_signal(
        signal_provenance_id="carbon_conflict_v1",
        signal_id="carbon_signal",
        signal_name="Carbon Signal",
        signal_class="grid_carbon_provider",
        source_system="carbon_api",
        source_provider="static_metadata",
        source_reference="carbon_intensity",
        source_url_or_entity_id="carbon_intensity",
        source_scope="public_open",
        freshness_status="fresh",
    )
    conflict = _base_conflict(
        conflict_decision_id="price_vs_carbon_conflict_v1",
        subject="price_vs_carbon_conflict_requires_scenario_branch",
        conflict_classes=["price_vs_carbon_conflict"],
        involved_signals=[price, carbon],
        scenario_branch_required=True,
    )
    examples.append(
        build_future_state_forecast_packet_v1(
            build_future_state_forecast_request_v1(
                request_id="price_vs_carbon_conflict_requires_scenario_branch",
                subject="price_vs_carbon_conflict_requires_scenario_branch",
                domain="scenario_simulation",
                forecast_horizon="medium_term",
                signal_records=[price, carbon],
                conflict_decisions=[conflict],
                assumptions=["owner priority not yet set"],
                known_constraints=["branch tradeoff paths"],
            )
        )
    )

    examples.append(
        build_future_state_forecast_packet_v1(
            build_future_state_forecast_request_v1(
                request_id="artifact_build_forecast_missing_validation_runner",
                subject="artifact_build_forecast_missing_validation_runner",
                domain="artifact_build_forecast",
                forecast_horizon="immediate",
                capability_maturity_records=[
                    _base_capability(
                        capability_id="artifact_build_runner_missing",
                        capability_name="Artifact Build Validation Runner",
                        family="artifact_and_code_generation",
                        maturity="design_only",
                        next_lane="DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1",
                    )
                ],
                missing_inputs=["validation_runner"],
                assumptions=["build output requires validation"],
                known_constraints=["no build without runner"],
            )
        )
    )

    examples.append(
        build_future_state_forecast_packet_v1(
            build_future_state_forecast_request_v1(
                request_id="public_pilot_forecast_blocked_claim_lifecycle_missing",
                subject="public_pilot_forecast_blocked_claim_lifecycle_missing",
                domain="product_market_forecast",
                forecast_horizon="long_term",
                capability_maturity_records=[
                    _base_capability(
                        capability_id="public_claim_lifecycle_missing",
                        capability_name="Public Claim Lifecycle",
                        family="public_product_and_claims",
                        maturity="design_only",
                        next_lane="DESIGN_WESLR_PUBLIC_CLAIM_LIFECYCLE_TRACKER_V1",
                    )
                ],
                missing_inputs=["claim_lifecycle_evidence"],
                assumptions=["public pilot claims require lifecycle evidence"],
                known_constraints=["no external release assertion"],
            )
        )
    )

    examples.append(
        build_future_state_forecast_packet_v1(
            build_future_state_forecast_request_v1(
                request_id="wifi_rf_research_forecast_blocked_privacy_boundary_missing",
                subject="wifi_rf_research_forecast_blocked_privacy_boundary_missing",
                domain="wifi_rf_sensing_forecast",
                forecast_horizon="medium_term",
                signal_records=[fresh_soc],
                missing_inputs=["privacy_boundary"],
                assumptions=["rf sensing may involve privacy sensitive data"],
                known_constraints=["privacy boundary must be explicit"],
            )
        )
    )

    examples.append(
        build_future_state_forecast_packet_v1(
            build_future_state_forecast_request_v1(
                request_id="tri_engine_orchestration_forecast_preserved_for_runtime_later",
                subject="tri_engine_orchestration_forecast_preserved_for_runtime_later",
                domain="weslr_project_forecast",
                forecast_horizon="medium_term",
                signal_records=[fresh_soc, grid_import],
                assumptions=["runtime orchestration remains later work"],
                known_constraints=["orchestration preserved for future design"],
                scenario_hints=["implementation wave continues"],
            )
        )
    )

    return examples
