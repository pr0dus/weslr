"""Metadata-only energy grid signal intelligence helpers v1.

This module builds bounded energy/grid intelligence packets from supplied
metadata only. It is pure, deterministic, import-safe, and fail-closed.

It does not call APIs. It does not connect to Home Assistant. It does not
fetch live grid/weather/price data. It does not create dashboards. It does not
call models/providers. It does not execute tools. It does not control devices.
It does not create automations. It does not write memory or `.weslr`.
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
    summarize_future_state_forecast_packet_v1,
    to_future_state_forecast_json_safe_v1,
    validate_future_state_forecast_packet_v1,
)
from weslr.scenario_simulation_engine import (
    ScenarioSimulationPacket,
    build_scenario_simulation_packet_v1,
    summarize_scenario_simulation_packet_v1,
    to_scenario_simulation_json_safe_v1,
    validate_scenario_simulation_packet_v1,
)
from weslr.signal_provenance_freshness_model import (
    SignalProvenanceRecord,
    build_signal_provenance_record_v1,
    summarize_signal_provenance_record_v1,
    to_signal_provenance_json_safe_v1,
    validate_signal_provenance_record_v1,
)

HELPER_TYPE_V1 = "energy_grid_signal_intelligence_v1"
REQUEST_TYPE_V1 = "energy_grid_signal_intelligence_request_v1"
PACKET_TYPE_V1 = "energy_grid_signal_intelligence_packet_v1"
SUMMARY_TYPE_V1 = "energy_grid_signal_intelligence_summary_v1"

ALLOWED_ENERGY_SIGNAL_DOMAINS_V1 = {
    "home_energy",
    "pv_generation",
    "battery_storage",
    "grid_import_export",
    "house_load",
    "heat_pump",
    "ev_charging",
    "electricity_price",
    "grid_carbon",
    "fossil_fuel_percentage",
    "country_import_export_flow",
    "weather_forecast",
    "home_assistant_state",
    "manual_owner_context",
    "unknown_energy_signal",
}

ALLOWED_RECOMMENDATION_MODES_V1 = {
    "observe_only",
    "collect_more_data",
    "dashboard_recommendation",
    "forecast_input",
    "scenario_input",
    "owner_decision_support",
    "automation_proposal_only",
    "blocked_control_request",
}

ALLOWED_OWNER_OPERATOR_MODES_V1 = {
    "home_owner_mode",
    "installer_operator_mode",
    "research_mode",
    "dashboard_designer_mode",
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
    "safety guarantee",
    "energy savings guarantee",
    "carbon optimization correctness guarantee",
    "autonomous learning",
    "autonomous learn",
    "prediction certainty",
    "runtime authority",
    "public claim",
    "learning claim",
    "model provider",
)

DEFAULT_CREATED_TIMESTAMP_V1 = "2026-06-01T23:34:00+02:00"
DEFAULT_DOMAIN_V1 = "unknown_energy_signal"
DEFAULT_RECOMMENDATION_MODE_V1 = "observe_only"
DEFAULT_OWNER_OPERATOR_MODE_V1 = "home_owner_mode"
DEFAULT_CONFIDENCE_V1 = "unknown_confidence"
DEFAULT_UNCERTAINTY_V1 = "unknown_uncertainty"
DEFAULT_RECOMMENDED_NEXT_STEP_V1 = "collect more metadata before deciding"
DEFAULT_RECOMMENDATION_ONLY_V1 = True
DEFAULT_FORECAST_ERROR_LEDGER_READY_V1 = True

STALE_FRESHNESS_STATUSES_V1 = {"stale", "expired", "missing_timestamp", "future_timestamp"}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EnergyGridSignalIntelligenceRequest:
    request_id: str
    subject: str
    domain: str
    recommendation_mode: str
    owner_operator_mode: str
    signal_records: list[SignalProvenanceRecord]
    conflict_decisions: list[EnergySignalConflictDecision]
    forecast_packets: list[FutureStateForecastPacket]
    scenario_packets: list[ScenarioSimulationPacket]
    capability_maturity_records: list[CapabilityMaturityRecord]
    forecast_error_records: list[ForecastErrorRecord]
    optimization_goals: list[str]
    owner_priorities: list[str]
    safety_constraints: list[str]
    comfort_constraints: list[str]
    deadline_constraints: list[str]
    privacy_constraints: list[str]
    possible_recommendations: list[str]
    scenario_inputs: list[str]
    forecast_inputs: list[str]
    missing_signals: list[str]
    recommended_next_step: str
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class EnergyGridSignalIntelligencePacket:
    energy_intelligence_id: str
    subject: str
    domain: str
    created_timestamp: str
    location_scope: str
    country: str
    region: str
    grid_zone: str
    market_zone: str
    timezone: str
    owner_operator_mode: str
    home_energy_state_summary: dict[str, Any]
    grid_context_summary: dict[str, Any]
    signal_inputs: list[str]
    signal_provenance_summary: list[dict[str, Any]]
    freshness_summary: dict[str, str]
    conflict_summary: dict[str, Any]
    normalization_summary: dict[str, Any]
    optimization_goals: list[str]
    owner_priorities: list[str]
    safety_constraints: list[str]
    comfort_constraints: list[str]
    deadline_constraints: list[str]
    privacy_constraints: list[str]
    possible_recommendations: list[str]
    scenario_inputs: list[str]
    forecast_inputs: list[str]
    missing_signals: list[str]
    confidence_label: str
    uncertainty_label: str
    recommended_next_step: str
    recommendation_mode: str
    recommendation_only: bool
    automation_allowed: bool
    device_control_allowed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    energy_savings_claimed: bool
    prediction_certainty_claimed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class EnergyGridSignalIntelligenceSummary:
    summary_type: str
    energy_intelligence_id: str
    subject: str
    domain: str
    recommendation_mode: str
    confidence_label: str
    uncertainty_label: str
    missing_signal_count: int
    recommendation_only: bool
    recommended_next_step: str


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


def to_energy_grid_signal_intelligence_json_safe_v1(value: Any) -> Any:
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


def _forecast_like(item: Any) -> FutureStateForecastPacket:
    if isinstance(item, FutureStateForecastPacket):
        validate_future_state_forecast_packet_v1(item)
        return item
    if isinstance(item, Mapping):
        return build_future_state_forecast_packet_v1(item)
    if is_dataclass(item):
        return build_future_state_forecast_packet_v1(asdict(item))
    raise ValidationError("unknown_forecast_packet")


def _scenario_like(item: Any) -> ScenarioSimulationPacket:
    if isinstance(item, ScenarioSimulationPacket):
        validate_scenario_simulation_packet_v1(item)
        return item
    if isinstance(item, Mapping):
        return build_scenario_simulation_packet_v1(item)
    if is_dataclass(item):
        return build_scenario_simulation_packet_v1(asdict(item))
    raise ValidationError("unknown_scenario_packet")


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


def _summary_signals(records: Iterable[SignalProvenanceRecord]) -> list[dict[str, Any]]:
    return [to_signal_provenance_json_safe_v1(summarize_signal_provenance_record_v1(record)) for record in records]


def _freshness_summary(records: Iterable[SignalProvenanceRecord]) -> dict[str, str]:
    return dict(sorted((record.signal_id, record.freshness_status) for record in records))


def _conflict_summary(decisions: Iterable[EnergySignalConflictDecision]) -> dict[str, Any]:
    conflict_classes: set[str] = set()
    unresolved: set[str] = set()
    scenario_branch_required = False
    for decision in decisions:
        conflict_classes.update(decision.conflict_classes)
        unresolved.update(decision.unresolved_conflicts)
        scenario_branch_required = scenario_branch_required or decision.scenario_branch_required
    return {
        "conflict_classes": sorted(conflict_classes),
        "decision_count": len(list(decisions)) if isinstance(decisions, list) else None,
        "scenario_branch_required": scenario_branch_required,
        "unresolved_conflicts": sorted(unresolved),
        "decision_summaries": [to_energy_signal_conflict_json_safe_v1(summarize_energy_signal_conflict_decision_v1(d)) for d in decisions],
    }


def _home_energy_state_summary(signals: list[SignalProvenanceRecord], recommendations: list[str], missing_signals: list[str]) -> dict[str, Any]:
    return {
        "signal_classes": sorted({signal.signal_class for signal in signals}),
        "signal_count": len(signals),
        "recommendation_count": len(recommendations),
        "missing_signal_count": len(missing_signals),
        "stale_signal_present": any(signal.freshness_status in STALE_FRESHNESS_STATUSES_V1 for signal in signals),
    }


def _grid_context_summary(signals: list[SignalProvenanceRecord]) -> dict[str, Any]:
    countries = sorted({signal.country for signal in signals if getattr(signal, "country", "")})
    regions = sorted({signal.region for signal in signals if getattr(signal, "region", "")})
    grid_zones = sorted({signal.grid_zone for signal in signals if getattr(signal, "grid_zone", "")})
    market_zones = sorted({signal.market_zone for signal in signals if getattr(signal, "market_zone", "")})
    return {
        "countries": countries,
        "regions": regions,
        "grid_zones": grid_zones,
        "market_zones": market_zones,
        "context_kind": "macro_context" if any(signal.signal_class == "import_export_flow_provider" for signal in signals) else "household_context",
    }


def _normalization_summary(signals: list[SignalProvenanceRecord], conflicts: list[EnergySignalConflictDecision]) -> dict[str, Any]:
    return {
        "normalized_signal_count": len(signals),
        "normalized_conflict_count": len(conflicts),
        "stale_count": sum(1 for signal in signals if signal.freshness_status in STALE_FRESHNESS_STATUSES_V1),
        "conflict_classes": sorted({c for decision in conflicts for c in decision.conflict_classes}),
    }


def _classify_confidence_and_uncertainty(signals: list[SignalProvenanceRecord], conflicts: list[EnergySignalConflictDecision], missing_signals: list[str], recommendation_mode: str, owner_priorities: list[str]) -> tuple[str, str]:
    if missing_signals:
        return "blocked_insufficient_evidence", "high_uncertainty"
    if any(signal.freshness_status in STALE_FRESHNESS_STATUSES_V1 for signal in signals):
        return "low_confidence", "high_uncertainty"
    if conflicts:
        return "medium_confidence", "medium_uncertainty"
    if not owner_priorities and recommendation_mode in {"owner_decision_support", "automation_proposal_only"}:
        return "low_confidence", "medium_uncertainty"
    if len(signals) >= 3:
        return "high_confidence", "low_uncertainty"
    if len(signals) == 1:
        return "medium_confidence", "medium_uncertainty"
    return "unknown_confidence", "unknown_uncertainty"


def _recommended_next_step(recommendation_mode: str, missing_signals: list[str], signals: list[SignalProvenanceRecord], conflicts: list[EnergySignalConflictDecision]) -> str:
    if missing_signals:
        return f"collect {missing_signals[0]} metadata"
    if any(signal.freshness_status in STALE_FRESHNESS_STATUSES_V1 for signal in signals):
        return "collect more data before recommending action"
    if conflicts:
        return "compare scenario branches and preserve conflict metadata"
    if recommendation_mode == "dashboard_recommendation":
        return "prepare a dashboard recommendation packet only"
    if recommendation_mode == "blocked_control_request":
        return "keep the request blocked and do not control devices"
    return DEFAULT_RECOMMENDED_NEXT_STEP_V1


def _recommended_mode_from_inputs(recommendation_mode: str, signals: list[SignalProvenanceRecord], conflicts: list[EnergySignalConflictDecision], missing_signals: list[str]) -> str:
    if recommendation_mode:
        return recommendation_mode
    if missing_signals:
        return "collect_more_data"
    if conflicts:
        return "owner_decision_support"
    if any(signal.signal_class == "home_assistant_state" for signal in signals):
        return "forecast_input"
    return DEFAULT_RECOMMENDATION_MODE_V1


def _risk_summary(signals: list[SignalProvenanceRecord], conflicts: list[EnergySignalConflictDecision], missing_signals: list[str], owner_priorities: list[str]) -> dict[str, Any]:
    return {
        "stale_signal_present": any(signal.freshness_status in STALE_FRESHNESS_STATUSES_V1 for signal in signals),
        "conflict_present": bool(conflicts),
        "missing_signal_present": bool(missing_signals),
        "owner_priority_gap": not bool(owner_priorities),
        "risk_labels": sorted(
            {
                *({"stale_signal"} if any(signal.freshness_status in STALE_FRESHNESS_STATUSES_V1 for signal in signals) else set()),
                *({"conflict"} if conflicts else set()),
                *({"missing_signal"} if missing_signals else set()),
                *({"owner_priority_gap"} if not owner_priorities else set()),
            }
        ),
    }


def _possible_recommendations(recommendation_mode: str, signals: list[SignalProvenanceRecord], conflicts: list[EnergySignalConflictDecision], missing_signals: list[str]) -> list[str]:
    recommendations: list[str] = []
    if missing_signals:
        recommendations.append("collect_more_data")
    if any(signal.freshness_status in STALE_FRESHNESS_STATUSES_V1 for signal in signals):
        recommendations.append("collect_more_data")
    if conflicts:
        recommendations.append("owner_decision_support")
        recommendations.append("scenario_input")
    if recommendation_mode == "dashboard_recommendation":
        recommendations.append("dashboard_recommendation")
    if recommendation_mode == "blocked_control_request":
        recommendations.append("blocked_control_request")
    if not recommendations:
        recommendations.append("observe_only")
    return sorted(set(recommendations))


def _build_energy_grid_intelligence_request_from_parts(request_id: str, subject: str, domain: str, recommendation_mode: str, owner_operator_mode: str, signal_records: list[SignalProvenanceRecord], conflict_decisions: list[EnergySignalConflictDecision], forecast_packets: list[FutureStateForecastPacket], scenario_packets: list[ScenarioSimulationPacket], capability_maturity_records: list[CapabilityMaturityRecord], forecast_error_records: list[ForecastErrorRecord], optimization_goals: list[str], owner_priorities: list[str], safety_constraints: list[str], comfort_constraints: list[str], deadline_constraints: list[str], privacy_constraints: list[str], possible_recommendations: list[str], scenario_inputs: list[str], forecast_inputs: list[str], missing_signals: list[str], recommended_next_step: str, safe_metadata: Mapping[str, Any] | None, extra_metadata: Mapping[str, Any]) -> EnergyGridSignalIntelligenceRequest:
    return EnergyGridSignalIntelligenceRequest(
        request_id=_safe_text(request_id),
        subject=_safe_text(subject),
        domain=_safe_text(domain),
        recommendation_mode=_safe_text(recommendation_mode),
        owner_operator_mode=_safe_text(owner_operator_mode),
        signal_records=signal_records,
        conflict_decisions=conflict_decisions,
        forecast_packets=forecast_packets,
        scenario_packets=scenario_packets,
        capability_maturity_records=capability_maturity_records,
        forecast_error_records=forecast_error_records,
        optimization_goals=_safe_list(optimization_goals),
        owner_priorities=_safe_list(owner_priorities),
        safety_constraints=_safe_list(safety_constraints),
        comfort_constraints=_safe_list(comfort_constraints),
        deadline_constraints=_safe_list(deadline_constraints),
        privacy_constraints=_safe_list(privacy_constraints),
        possible_recommendations=_safe_list(possible_recommendations),
        scenario_inputs=_safe_list(scenario_inputs),
        forecast_inputs=_safe_list(forecast_inputs),
        missing_signals=_safe_list(missing_signals),
        recommended_next_step=_safe_text(recommended_next_step),
        safe_metadata={"metadata_only": True, "internal_only": True, **dict(safe_metadata or {}), **dict(extra_metadata)},
    )


def build_energy_grid_intelligence_request_v1(
    *,
    request_id: str,
    subject: str,
    domain: str,
    recommendation_mode: str = DEFAULT_RECOMMENDATION_MODE_V1,
    owner_operator_mode: str = DEFAULT_OWNER_OPERATOR_MODE_V1,
    signal_records: Iterable[Any] | None = None,
    conflict_decisions: Iterable[Any] | None = None,
    forecast_packets: Iterable[Any] | None = None,
    scenario_packets: Iterable[Any] | None = None,
    capability_maturity_records: Iterable[Any] | None = None,
    forecast_error_records: Iterable[Any] | None = None,
    optimization_goals: Iterable[str] | None = None,
    owner_priorities: Iterable[str] | None = None,
    safety_constraints: Iterable[str] | None = None,
    comfort_constraints: Iterable[str] | None = None,
    deadline_constraints: Iterable[str] | None = None,
    privacy_constraints: Iterable[str] | None = None,
    possible_recommendations: Iterable[str] | None = None,
    scenario_inputs: Iterable[str] | None = None,
    forecast_inputs: Iterable[str] | None = None,
    missing_signals: Iterable[str] | None = None,
    recommended_next_step: str = DEFAULT_RECOMMENDED_NEXT_STEP_V1,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> EnergyGridSignalIntelligenceRequest:
    signals = [_signal_like(item) for item in (signal_records or [])]
    conflicts = [_decision_like(item) for item in (conflict_decisions or [])]
    forecasts = [_forecast_like(item) for item in (forecast_packets or [])]
    scenarios = [_scenario_like(item) for item in (scenario_packets or [])]
    maturities = [_maturity_like(item) for item in (capability_maturity_records or [])]
    errors = [_error_like(item) for item in (forecast_error_records or [])]
    recommendation_mode = _safe_text(recommendation_mode)
    owner_operator_mode = _safe_text(owner_operator_mode)
    missing = _safe_list(missing_signals)
    if not recommended_next_step or recommended_next_step == DEFAULT_RECOMMENDED_NEXT_STEP_V1:
        recommended_next_step = _recommended_next_step(recommendation_mode, missing, signals, conflicts)
    return _build_energy_grid_intelligence_request_from_parts(
        request_id=request_id,
        subject=subject,
        domain=domain,
        recommendation_mode=recommendation_mode,
        owner_operator_mode=owner_operator_mode,
        signal_records=signals,
        conflict_decisions=conflicts,
        forecast_packets=forecasts,
        scenario_packets=scenarios,
        capability_maturity_records=maturities,
        forecast_error_records=errors,
        optimization_goals=_safe_list(optimization_goals),
        owner_priorities=_safe_list(owner_priorities),
        safety_constraints=_safe_list(safety_constraints),
        comfort_constraints=_safe_list(comfort_constraints),
        deadline_constraints=_safe_list(deadline_constraints),
        privacy_constraints=_safe_list(privacy_constraints),
        possible_recommendations=_safe_list(possible_recommendations),
        scenario_inputs=_safe_list(scenario_inputs),
        forecast_inputs=_safe_list(forecast_inputs),
        missing_signals=missing,
        recommended_next_step=_safe_text(recommended_next_step),
        safe_metadata=safe_metadata,
        extra_metadata=extra_metadata,
    )


def _energy_grid_intelligence_packet_from_request(request: EnergyGridSignalIntelligenceRequest, *, created_timestamp: str = DEFAULT_CREATED_TIMESTAMP_V1, safe_metadata: Mapping[str, Any] | None = None, **extra_metadata: Any) -> EnergyGridSignalIntelligencePacket:
    signals = request.signal_records
    conflicts = request.conflict_decisions
    forecasts = request.forecast_packets
    scenarios = request.scenario_packets
    missing_signals = list(request.missing_signals)
    if any(signal.freshness_status in STALE_FRESHNESS_STATUSES_V1 for signal in signals) and not missing_signals:
        missing_signals = ["fresh_signal_metadata"]
    confidence_label, uncertainty_label = _classify_confidence_and_uncertainty(signals, conflicts, missing_signals, request.recommendation_mode, request.owner_priorities)
    recommendation_mode = _recommended_mode_from_inputs(request.recommendation_mode, signals, conflicts, missing_signals)
    return EnergyGridSignalIntelligencePacket(
        energy_intelligence_id=f"{request.request_id}_energy_intelligence",
        subject=request.subject,
        domain=request.domain,
        created_timestamp=_safe_text(created_timestamp),
        location_scope="local_home" if any(signal.source_scope.startswith("local") for signal in signals) else "macro_context",
        country=next((signal.country for signal in signals if getattr(signal, "country", "")), ""),
        region=next((signal.region for signal in signals if getattr(signal, "region", "")), ""),
        grid_zone=next((signal.grid_zone for signal in signals if getattr(signal, "grid_zone", "")), ""),
        market_zone=next((signal.market_zone for signal in signals if getattr(signal, "market_zone", "")), ""),
        timezone=next((signal.timezone for signal in signals if getattr(signal, "timezone", "")), ""),
        owner_operator_mode=request.owner_operator_mode,
        home_energy_state_summary=_home_energy_state_summary(signals, request.possible_recommendations, missing_signals),
        grid_context_summary=_grid_context_summary(signals),
        signal_inputs=[signal.signal_id for signal in signals],
        signal_provenance_summary=_summary_signals(signals),
        freshness_summary=_freshness_summary(signals),
        conflict_summary=_conflict_summary(conflicts),
        normalization_summary=_normalization_summary(signals, conflicts),
        optimization_goals=list(request.optimization_goals),
        owner_priorities=list(request.owner_priorities),
        safety_constraints=list(request.safety_constraints),
        comfort_constraints=list(request.comfort_constraints),
        deadline_constraints=list(request.deadline_constraints),
        privacy_constraints=list(request.privacy_constraints),
        possible_recommendations=_possible_recommendations(recommendation_mode, signals, conflicts, missing_signals),
        scenario_inputs=[packet.scenario_simulation_id for packet in scenarios],
        forecast_inputs=[packet.forecast_id for packet in forecasts],
        missing_signals=missing_signals,
        confidence_label=confidence_label,
        uncertainty_label=uncertainty_label,
        recommended_next_step=request.recommended_next_step if request.recommended_next_step else _recommended_next_step(recommendation_mode, missing_signals, signals, conflicts),
        recommendation_mode=recommendation_mode,
        recommendation_only=True,
        automation_allowed=False,
        device_control_allowed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        energy_savings_claimed=False,
        prediction_certainty_claimed=False,
        learning_claimed=False,
        safe_metadata={"metadata_only": True, "internal_only": True, **dict(safe_metadata or {}), **dict(extra_metadata)},
    )


def build_energy_grid_intelligence_packet_v1(
    request: Any,
    /,
    *,
    created_timestamp: str = DEFAULT_CREATED_TIMESTAMP_V1,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> EnergyGridSignalIntelligencePacket:
    normalized_request = request if isinstance(request, EnergyGridSignalIntelligenceRequest) else build_energy_grid_intelligence_request_v1(**dict(request)) if isinstance(request, Mapping) else build_energy_grid_intelligence_request_v1(**asdict(request)) if is_dataclass(request) else None
    if normalized_request is None:
        raise ValidationError("unknown_request")
    packet = _energy_grid_intelligence_packet_from_request(normalized_request, created_timestamp=created_timestamp, safe_metadata=safe_metadata, **extra_metadata)
    validate_energy_grid_signal_intelligence_packet_v1(packet)
    return packet


def validate_energy_grid_signal_intelligence_packet_v1(packet: Any) -> bool:
    original = packet if isinstance(packet, Mapping) else asdict(packet) if is_dataclass(packet) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    if _contains_forbidden_claim(original):
        raise ValidationError("forbidden_claim_marker_detected")
    normalized = packet if isinstance(packet, EnergyGridSignalIntelligencePacket) else EnergyGridSignalIntelligencePacket(**dict(packet)) if isinstance(packet, Mapping) else EnergyGridSignalIntelligencePacket(**asdict(packet)) if is_dataclass(packet) else None
    if normalized is None:
        raise ValidationError("unknown_packet")
    if normalized.domain not in ALLOWED_ENERGY_SIGNAL_DOMAINS_V1:
        raise ValidationError("unknown_energy_signal_domain")
    if normalized.owner_operator_mode not in ALLOWED_OWNER_OPERATOR_MODES_V1:
        raise ValidationError("unknown_owner_operator_mode")
    if normalized.recommendation_mode not in ALLOWED_RECOMMENDATION_MODES_V1:
        raise ValidationError("unknown_recommendation_mode")
    if normalized.confidence_label not in ALLOWED_CONFIDENCE_LABELS_V1:
        raise ValidationError("unknown_confidence")
    if normalized.uncertainty_label not in ALLOWED_UNCERTAINTY_LABELS_V1:
        raise ValidationError("unknown_uncertainty")
    if normalized.recommendation_mode == "blocked_control_request" and normalized.recommendation_only is not True:
        raise ValidationError("blocked_control_request_must_be_recommendation_only")
    if normalized.recommendation_mode == "dashboard_recommendation" and normalized.recommendation_only is not True:
        raise ValidationError("dashboard_recommendation_must_be_recommendation_only")
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
    if normalized.energy_savings_claimed:
        raise ValidationError("energy_savings_claimed_true")
    if normalized.prediction_certainty_claimed:
        raise ValidationError("prediction_certainty_claimed_true")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_true")
    if normalized.domain not in ALLOWED_ENERGY_SIGNAL_DOMAINS_V1:
        raise ValidationError("unknown_energy_signal_domain")
    if _contains_forbidden_field(normalized.safe_metadata) or _contains_forbidden_claim(normalized.safe_metadata):
        raise ValidationError("forbidden_safe_metadata_detected")
    for signal in normalized.signal_provenance_summary:
        if _contains_forbidden_field(signal) or _contains_forbidden_claim(signal):
            raise ValidationError("forbidden_signal_summary_detected")
    return True


def summarize_energy_grid_signal_intelligence_packet_v1(packet: Any) -> EnergyGridSignalIntelligenceSummary:
    normalized = packet if isinstance(packet, EnergyGridSignalIntelligencePacket) else EnergyGridSignalIntelligencePacket(**dict(packet)) if isinstance(packet, Mapping) else EnergyGridSignalIntelligencePacket(**asdict(packet)) if is_dataclass(packet) else None
    if normalized is None:
        raise ValidationError("unknown_packet")
    validate_energy_grid_signal_intelligence_packet_v1(normalized)
    return EnergyGridSignalIntelligenceSummary(
        summary_type=SUMMARY_TYPE_V1,
        energy_intelligence_id=normalized.energy_intelligence_id,
        subject=normalized.subject,
        domain=normalized.domain,
        recommendation_mode=normalized.recommendation_mode,
        confidence_label=normalized.confidence_label,
        uncertainty_label=normalized.uncertainty_label,
        missing_signal_count=len(normalized.missing_signals),
        recommendation_only=normalized.recommendation_only,
        recommended_next_step=normalized.recommended_next_step,
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
    country: str = "DE",
    region: str = "de",
    grid_zone: str = "de-lu",
    market_zone: str = "de-day-ahead",
    timezone: str = "Europe/Berlin",
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
        country=country,
        region=region,
        grid_zone=grid_zone,
        market_zone=market_zone,
        timezone=timezone,
        forecasting_allowed=True,
        scenario_simulation_allowed=True,
        memory_write_allowed=False,
        action_authority_granted=False,
        safe_metadata={"synthetic": True, "metadata_only": True},
    )


def _forecast(subject: str, domain: str, horizon: str, *, signals: list[SignalProvenanceRecord] | None = None, conflicts: list[EnergySignalConflictDecision] | None = None) -> FutureStateForecastPacket:
    return build_future_state_forecast_packet_v1(
        {
            "request_id": subject,
            "subject": subject,
            "domain": domain,
            "forecast_horizon": horizon,
            "signal_records": signals or [],
            "conflict_decisions": conflicts or [],
            "safe_metadata": {"synthetic": True},
        }
    )


def _scenario(subject: str, domain: str, *, forecast_packets: list[FutureStateForecastPacket] | None = None, signals: list[SignalProvenanceRecord] | None = None, conflicts: list[EnergySignalConflictDecision] | None = None, missing_inputs: list[str] | None = None, hints: list[str] | None = None, branch_preferences: list[str] | None = None) -> ScenarioSimulationPacket:
    return build_scenario_simulation_packet_v1(
        {
            "request_id": subject,
            "subject": subject,
            "domain": domain,
            "forecast_packets": forecast_packets or [],
            "signal_records": signals or [],
            "conflict_decisions": conflicts or [],
            "missing_inputs": missing_inputs or [],
            "scenario_hints": hints or [],
            "branch_preferences": branch_preferences or [],
            "safe_metadata": {"synthetic": True},
        }
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


def _capability(capability_id: str, capability_name: str, family: str, maturity: str, lane: str) -> CapabilityMaturityRecord:
    return build_capability_maturity_record_v1(
        capability_id=capability_id,
        capability_name=capability_name,
        capability_family=family,
        current_maturity=maturity,
        latest_commit="static_reference_v1",
        latest_judgment="metadata_only",
        recommended_next_lane=lane,
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
        confidence_before=0.72,
        confidence_after=0.36,
        assumptions_used=["synthetic assumption"],
        assumptions_failed=["synthetic failed assumption"],
        signals_used=["synthetic_signal"],
        recommendation_taken="bounded_recommendation",
        owner_action_taken="metadata_only_review",
        action_authority_used=False,
        resulting_effect="synthetic outcome",
        corrective_lesson="keep boundary explicit",
        recommended_model_update="metadata-only packet helpers",
        behavior_pack_candidate="energy_grid_signal_behavior_pack_candidate",
        requires_owner_review=True,
        safe_metadata={"synthetic": True},
    )


def build_initial_energy_grid_signal_intelligence_examples_v1() -> list[EnergyGridSignalIntelligencePacket]:
    price = _signal(
        signal_provenance_id="energy_price_signal_v1",
        signal_id="energy_price_signal",
        signal_name="Energy Price Signal",
        signal_class="electricity_price_provider",
        source_system="price_api",
        source_provider="static_reference",
        source_reference="day_ahead_price",
        source_url_or_entity_id="day_ahead_price",
        source_scope="public_open",
        freshness_status="fresh",
    )
    carbon = _signal(
        signal_provenance_id="energy_carbon_signal_v1",
        signal_id="energy_carbon_signal",
        signal_name="Energy Carbon Signal",
        signal_class="grid_carbon_provider",
        source_system="carbon_api",
        source_provider="static_reference",
        source_reference="carbon_intensity",
        source_url_or_entity_id="carbon_intensity",
        source_scope="public_open",
        freshness_status="fresh",
    )
    pv = _signal(
        signal_provenance_id="pv_generation_signal_v1",
        signal_id="pv_generation_signal",
        signal_name="PV Generation Signal",
        signal_class="weather_provider",
        source_system="weather_api",
        source_provider="synthetic_reference",
        source_reference="pv_generation_forecast",
        source_url_or_entity_id="pv_generation_forecast",
        source_scope="public_open",
        freshness_status="fresh",
    )
    battery = _signal(
        signal_provenance_id="battery_storage_signal_v1",
        signal_id="battery_storage_signal",
        signal_name="Battery Storage Signal",
        signal_class="home_assistant_entity",
        source_system="home_assistant",
        source_provider="local_entity",
        source_reference="sensor.battery_soc",
        source_url_or_entity_id="sensor.battery_soc",
        source_scope="local_home",
        freshness_status="fresh",
    )
    stale_ha = _signal(
        signal_provenance_id="stale_home_assistant_state_v1",
        signal_id="stale_home_assistant_state",
        signal_name="Stale Home Assistant State",
        signal_class="home_assistant_entity",
        source_system="home_assistant",
        source_provider="local_entity",
        source_reference="sensor.battery_soc",
        source_url_or_entity_id="sensor.battery_soc",
        source_scope="local_home",
        freshness_status="stale",
    )
    country_flow = _signal(
        signal_provenance_id="country_import_export_flow_v1",
        signal_id="country_import_export_flow",
        signal_name="Country Import Export Flow",
        signal_class="import_export_flow_provider",
        source_system="grid_public_data",
        source_provider="static_reference",
        source_reference="country_flow",
        source_url_or_entity_id="country_flow",
        source_scope="public_open",
        freshness_status="fresh",
        country="DE",
        region="de",
        grid_zone="de-lu",
        market_zone="de-day-ahead",
    )
    departure = _signal(
        signal_provenance_id="ev_departure_owner_v1",
        signal_id="ev_departure_time",
        signal_name="EV Departure Time",
        signal_class="manual_owner_signal",
        source_system="manual_owner",
        source_provider="owner_note",
        source_reference="departure_time",
        source_url_or_entity_id="departure_time",
        source_scope="manual",
        freshness_status="fresh",
    )
    price_conflict = _conflict("price_vs_carbon_owner_decision", ["price_vs_carbon_conflict"], [price, carbon], scenario_branch_required=True)
    missing_owner_priority = _conflict("missing_owner_priority_low_confidence", ["price_vs_comfort_conflict"], [price, carbon], scenario_branch_required=True)
    forecast_pv = _forecast("pv_surplus_forecast_support", "energy_home_forecast", "short_term", signals=[pv])
    forecast_battery = _forecast("battery_reserve_recommendation", "energy_home_forecast", "short_term", signals=[battery])
    forecast_ev = _forecast("ev_charging_deadline_support", "energy_home_forecast", "short_term", signals=[battery, departure])
    forecast_heat = _forecast("heat_pump_preheat_scenario", "energy_home_forecast", "short_term", signals=[price, carbon])
    forecast_macro = _forecast("country_import_export_macro_context", "grid_signal_forecast", "medium_term", signals=[country_flow])
    scenario_heat = _scenario("heat_pump_preheat_scenario", "energy_home_scenario", forecast_packets=[forecast_heat], signals=[price, carbon], conflicts=[_conflict("heat_pump_preheat_scenario", ["price_vs_comfort_conflict"], [price, carbon], scenario_branch_required=True)], hints=["comfort first", "cost branch"], branch_preferences=["comfort_first_branch", "cost_optimized_branch"])
    scenario_price = _scenario("price_vs_carbon_conflict_owner_decision", "energy_home_scenario", forecast_packets=[forecast_heat], signals=[price, carbon], conflicts=[price_conflict], hints=["price vs carbon"], branch_preferences=["cost_optimized_branch", "carbon_optimized_branch", "baseline_branch"])
    scenario_pv = _scenario("pv_surplus_forecast_support", "energy_home_scenario", forecast_packets=[forecast_pv], signals=[pv], hints=["pv surplus"], branch_preferences=["optimistic_branch", "conservative_branch"])
    scenario_stale = _scenario("stale_home_assistant_signal_collect_more_data", "energy_home_scenario", forecast_packets=[forecast_battery], signals=[stale_ha], missing_inputs=["fresh_home_assistant_state"], hints=["stale ha signal"], branch_preferences=["wait_and_observe_branch", "blocked_branch"])

    examples = [
        _packet_from_request(
            build_energy_grid_intelligence_request_v1(
                request_id="pv_surplus_forecast_support",
                subject="pv_surplus_forecast_support",
                domain="pv_generation",
                recommendation_mode="forecast_input",
                owner_operator_mode="research_mode",
                signal_records=[pv, weather_signal()],
                forecast_packets=[forecast_pv],
                scenario_packets=[scenario_pv],
                forecast_inputs=[forecast_pv.forecast_id],
                scenario_inputs=[scenario_pv.scenario_simulation_id],
                optimization_goals=["forecast support"],
                owner_priorities=["preserve evidence"],
                possible_recommendations=["forecast_input", "scenario_input"],
                recommended_next_step="use forecast packet as input only",
            )
        ),
        _packet_from_request(
            build_energy_grid_intelligence_request_v1(
                request_id="battery_reserve_recommendation",
                subject="battery_reserve_recommendation",
                domain="battery_storage",
                recommendation_mode="owner_decision_support",
                owner_operator_mode="home_owner_mode",
                signal_records=[battery],
                forecast_packets=[forecast_battery],
                scenario_packets=[_scenario("battery_reserve_recommendation", "energy_home_scenario", forecast_packets=[forecast_battery], signals=[battery], hints=["battery reserve"], branch_preferences=["baseline_branch"])],
                optimization_goals=["protect battery reserve"],
                owner_priorities=["home owner comfort"],
                safety_constraints=["avoid deep discharge"],
                possible_recommendations=["owner_decision_support"],
            )
        ),
        _packet_from_request(
            build_energy_grid_intelligence_request_v1(
                request_id="ev_charging_deadline_support",
                subject="ev_charging_deadline_support",
                domain="ev_charging",
                recommendation_mode="owner_decision_support",
                owner_operator_mode="home_owner_mode",
                signal_records=[battery, departure],
                forecast_packets=[forecast_ev],
                scenario_packets=[_scenario("ev_charging_deadline_support", "energy_home_scenario", forecast_packets=[forecast_ev], signals=[battery, departure], missing_inputs=["departure_time"], hints=["deadline support"], branch_preferences=["deadline_first_branch", "blocked_branch"])],
                deadline_constraints=["departure_time"],
                possible_recommendations=["owner_decision_support"],
            )
        ),
        _packet_from_request(scenario_heat_as_request(scenario_heat, forecast_heat, price, carbon)),
        _packet_from_request(
            build_energy_grid_intelligence_request_v1(
                request_id="price_vs_carbon_conflict_owner_decision",
                subject="price_vs_carbon_conflict_owner_decision",
                domain="grid_import_export",
                recommendation_mode="owner_decision_support",
                owner_operator_mode="installer_operator_mode",
                signal_records=[price, carbon],
                conflict_decisions=[price_conflict],
                forecast_packets=[forecast_heat],
                scenario_packets=[scenario_price],
                optimization_goals=["minimize cost", "minimize carbon"],
                owner_priorities=["owner must choose priority"],
                possible_recommendations=["owner_decision_support", "scenario_input"],
            )
        ),
        _packet_from_request(
            build_energy_grid_intelligence_request_v1(
                request_id="country_import_export_macro_context",
                subject="country_import_export_macro_context",
                domain="country_import_export_flow",
                recommendation_mode="observe_only",
                owner_operator_mode="research_mode",
                signal_records=[country_flow],
                forecast_packets=[forecast_macro],
                scenario_packets=[_scenario("country_import_export_macro_context", "grid_signal_scenario", forecast_packets=[forecast_macro], signals=[country_flow], hints=["macro context"], branch_preferences=["baseline_branch"])],
                optimization_goals=["macro context only"],
                possible_recommendations=["observe_only"],
            )
        ),
        _packet_from_request(
            build_energy_grid_intelligence_request_v1(
                request_id="stale_home_assistant_signal_collect_more_data",
                subject="stale_home_assistant_signal_collect_more_data",
                domain="home_assistant_state",
                recommendation_mode="collect_more_data",
                owner_operator_mode="home_owner_mode",
                signal_records=[stale_ha],
                forecast_packets=[forecast_battery],
                scenario_packets=[scenario_stale],
                missing_signals=["fresh_home_assistant_state"],
                possible_recommendations=["collect_more_data"],
            )
        ),
        _packet_from_request(
            build_energy_grid_intelligence_request_v1(
                request_id="missing_owner_priority_low_confidence",
                subject="missing_owner_priority_low_confidence",
                domain="home_energy",
                recommendation_mode="owner_decision_support",
                owner_operator_mode="home_owner_mode",
                signal_records=[price],
                forecast_packets=[forecast_pv],
                missing_signals=[],
                owner_priorities=[],
                possible_recommendations=["owner_decision_support"],
            )
        ),
        _packet_from_request(
            build_energy_grid_intelligence_request_v1(
                request_id="dashboard_recommendation_only",
                subject="dashboard_recommendation_only",
                domain="grid_import_export",
                recommendation_mode="dashboard_recommendation",
                owner_operator_mode="dashboard_designer_mode",
                signal_records=[price, carbon],
                forecast_packets=[forecast_heat],
                scenario_packets=[scenario_price],
                possible_recommendations=["dashboard_recommendation"],
            )
        ),
        _packet_from_request(
            build_energy_grid_intelligence_request_v1(
                request_id="blocked_device_control_request",
                subject="blocked_device_control_request",
                domain="heat_pump",
                recommendation_mode="blocked_control_request",
                owner_operator_mode="installer_operator_mode",
                signal_records=[price, carbon],
                forecast_packets=[forecast_heat],
                scenario_packets=[scenario_heat],
                possible_recommendations=["blocked_control_request"],
                safety_constraints=["no device control"],
            )
        ),
    ]
    return examples


def _packet_from_request(request: EnergyGridSignalIntelligenceRequest) -> EnergyGridSignalIntelligencePacket:
    return _energy_grid_intelligence_packet_from_request(request)


def weather_signal() -> SignalProvenanceRecord:
    return _signal(
        signal_provenance_id="weather_forecast_signal_v1",
        signal_id="weather_forecast_signal",
        signal_name="Weather Forecast Signal",
        signal_class="weather_provider",
        source_system="weather_api",
        source_provider="static_reference",
        source_reference="weather_forecast",
        source_url_or_entity_id="weather_forecast",
        source_scope="public_open",
        freshness_status="fresh",
    )


def scenario_heat_as_request(scenario_heat: ScenarioSimulationPacket, forecast_heat: FutureStateForecastPacket, price: SignalProvenanceRecord, carbon: SignalProvenanceRecord) -> EnergyGridSignalIntelligenceRequest:
    return build_energy_grid_intelligence_request_v1(
        request_id="heat_pump_preheat_scenario",
        subject="heat_pump_preheat_scenario",
        domain="heat_pump",
        recommendation_mode="scenario_input",
        owner_operator_mode="home_owner_mode",
        signal_records=[price, carbon],
        forecast_packets=[forecast_heat],
        scenario_packets=[scenario_heat],
        scenario_inputs=[scenario_heat.scenario_simulation_id],
        forecast_inputs=[forecast_heat.forecast_id],
        optimization_goals=["maintain_comfort", "minimize_cost"],
        comfort_constraints=["comfort first"],
        safety_constraints=["do not silently sacrifice comfort"],
        possible_recommendations=["scenario_input"],
    )
