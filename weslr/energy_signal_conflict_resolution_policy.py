"""Metadata-only energy signal conflict resolution policy helpers v1.

This module classifies and resolves conflicts between synthetic energy/home/grid
signals. It is pure, deterministic, import-safe, and fail-closed.

It does not call APIs. It does not connect Home Assistant. It does not fetch
live grid/weather/electricity data. It does not control devices. It does not
write memory or `.weslr`. It does not route chat.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping

from weslr.signal_provenance_freshness_model import (
    ALLOWED_CONFLICT_TYPES_V1 as SIGNAL_CONFLICT_TYPES_V1,
    ALLOWED_FRESHNESS_LABELS_V1,
    ALLOWED_QUALITY_LABELS_V1,
    SignalProvenanceRecord,
    build_initial_signal_provenance_examples_v1,
    build_signal_provenance_record_v1,
    evaluate_signal_freshness_v1,
    evaluate_signal_quality_v1,
    to_signal_provenance_json_safe_v1,
)

HELPER_TYPE_V1 = "energy_signal_conflict_resolution_policy_v1"
DECISION_TYPE_V1 = "energy_signal_conflict_decision_v1"
SUMMARY_TYPE_V1 = "energy_signal_conflict_decision_summary_v1"

ALLOWED_CONFLICT_CLASSES_V1 = {
    "no_conflict",
    "price_vs_carbon_conflict",
    "price_vs_comfort_conflict",
    "carbon_vs_comfort_conflict",
    "pv_forecast_vs_weather_conflict",
    "battery_soc_source_conflict",
    "grid_import_export_scope_conflict",
    "unit_conflict",
    "region_or_grid_zone_conflict",
    "timestamp_or_freshness_conflict",
    "source_disagreement",
    "privacy_or_authority_conflict",
    "control_capability_conflict",
    "forecast_vs_observed_conflict",
    "unknown_conflict",
}

ALLOWED_RESOLUTION_STRATEGIES_V1 = {
    "preserve_conflict",
    "ask_owner_priority",
    "wait_for_fresh_signal",
    "prefer_local_sensor",
    "prefer_fresher_signal",
    "prefer_owner_manual_priority",
    "prefer_safety_constraint",
    "prefer_deadline_constraint",
    "branch_scenarios",
    "recommend_no_action",
    "recommend_data_collection",
    "block_recommendation",
    "unknown_resolution",
}

ALLOWED_ENERGY_GOALS_V1 = {
    "minimize_cost",
    "minimize_carbon",
    "maximize_self_consumption",
    "protect_battery_reserve",
    "maintain_comfort",
    "meet_ev_departure_deadline",
    "avoid_grid_import",
    "avoid_grid_export",
    "avoid_peak_load",
    "grid_supportive_behavior",
    "safety_first",
    "owner_manual_priority",
}

FORBIDDEN_FIELD_HINTS_V1 = (
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

FORBIDDEN_CLAIM_PHRASES_V1 = (
    "agi",
    "consciousness",
    "sentience",
    "turing",
    "certification",
    "public readiness",
    "public readiness claim",
    "energy savings guarantee",
    "prediction certainty",
    "runtime authority",
    "public claim",
    "learning claim",
)

DEFAULT_GOAL_V1 = "safety_first"
DEFAULT_RESOLUTION_STRATEGY_V1 = "preserve_conflict"
DEFAULT_RECOMMENDATION_MODE_V1 = "recommendation_only"

TRADEOFF_CONFLICTS_V1 = {
    "price_vs_carbon_conflict",
    "price_vs_comfort_conflict",
    "carbon_vs_comfort_conflict",
    "pv_forecast_vs_weather_conflict",
    "battery_soc_source_conflict",
    "grid_import_export_scope_conflict",
    "region_or_grid_zone_conflict",
    "timestamp_or_freshness_conflict",
    "source_disagreement",
    "privacy_or_authority_conflict",
    "control_capability_conflict",
    "forecast_vs_observed_conflict",
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EnergySignalConflictDecision:
    conflict_decision_id: str
    decision_subject: str
    conflict_classes: list[str]
    involved_signals: list[str]
    signal_provenance_summary: list[dict[str, Any]]
    freshness_summary: dict[str, str]
    region_scope_summary: dict[str, str]
    unit_scope_summary: dict[str, str]
    owner_priority: bool
    optimization_goal: str
    safety_constraints: list[str]
    comfort_constraints: list[str]
    deadline_constraints: list[str]
    privacy_constraints: list[str]
    authority_constraints: list[str]
    preferred_signal_if_any: str
    unresolved_conflicts: list[str]
    scenario_branch_required: bool
    confidence_adjustment: float
    recommended_resolution_strategy: str
    recommended_next_signal: str
    safe_recommendation_mode: str
    action_authority_granted: bool
    automation_allowed: bool
    device_control_allowed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class EnergySignalConflictSummary:
    summary_type: str
    conflict_decision_id: str
    decision_subject: str
    conflict_classes: list[str]
    recommended_resolution_strategy: str
    confidence_adjustment: float
    scenario_branch_required: bool
    unresolved_conflicts: list[str]
    optimization_goal: str
    safe_recommendation_mode: str


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


def to_energy_signal_conflict_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def _contains_forbidden_field(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if any(hint in key_text for hint in FORBIDDEN_FIELD_HINTS_V1):
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


def _contains_forbidden_claim_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _contains_forbidden_claim_marker(key) or _contains_forbidden_claim_marker(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item) for item in value)
    blob = _normalize_text(value)
    if not blob:
        return False
    if any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1):
        return True
    return False


def _record_like(value: Any) -> SignalProvenanceRecord:
    if isinstance(value, SignalProvenanceRecord):
        return value
    if not isinstance(value, Mapping):
        value = asdict(value) if is_dataclass(value) else {}
    return SignalProvenanceRecord(
        signal_provenance_id=_safe_text(value.get("signal_provenance_id")),
        signal_id=_safe_text(value.get("signal_id")),
        signal_name=_safe_text(value.get("signal_name")),
        signal_class=_safe_text(value.get("signal_class")),
        source_system=_safe_text(value.get("source_system")),
        source_provider=_safe_text(value.get("source_provider")),
        source_reference=_safe_text(value.get("source_reference")),
        source_url_or_entity_id=_safe_text(value.get("source_url_or_entity_id")),
        source_scope=_safe_text(value.get("source_scope")),
        owner_authorized=_safe_bool(value.get("owner_authorized")),
        operator_authorized=_safe_bool(value.get("operator_authorized")),
        retrieval_method=_safe_text(value.get("retrieval_method")),
        retrieval_timestamp=_safe_text(value.get("retrieval_timestamp")),
        reported_timestamp=_safe_text(value.get("reported_timestamp")),
        timezone=_safe_text(value.get("timezone")),
        region=_safe_text(value.get("region")),
        country=_safe_text(value.get("country")),
        grid_zone=_safe_text(value.get("grid_zone")),
        market_zone=_safe_text(value.get("market_zone")),
        unit=_safe_text(value.get("unit")),
        value_type=_safe_text(value.get("value_type")),
        expected_update_cadence=_safe_text(value.get("expected_update_cadence")),
        freshness_status=_safe_text(value.get("freshness_status")),
        quality_status=_safe_text(value.get("quality_status")),
        poison_shield_status=_safe_text(value.get("poison_shield_status")),
        privacy_sensitivity=_safe_text(value.get("privacy_sensitivity")),
        control_capable=_safe_bool(value.get("control_capable")),
        forecasting_allowed=_safe_bool(value.get("forecasting_allowed")),
        scenario_simulation_allowed=_safe_bool(value.get("scenario_simulation_allowed")),
        memory_write_allowed=_safe_bool(value.get("memory_write_allowed")),
        action_authority_granted=_safe_bool(value.get("action_authority_granted")),
        conflict_status=_safe_text(value.get("conflict_status")),
        normalization_status=_safe_text(value.get("normalization_status")),
        safe_metadata=dict(value.get("safe_metadata") or {}),
    )


def _summary_record(record: SignalProvenanceRecord) -> dict[str, Any]:
    return {
        "signal_id": record.signal_id,
        "signal_name": record.signal_name,
        "signal_class": record.signal_class,
        "freshness_status": record.freshness_status,
        "quality_status": record.quality_status,
        "conflict_status": record.conflict_status,
        "source_scope": record.source_scope,
        "region": record.region,
        "country": record.country,
        "grid_zone": record.grid_zone,
        "market_zone": record.market_zone,
        "unit": record.unit,
        "control_capable": record.control_capable,
        "memory_write_allowed": record.memory_write_allowed,
        "action_authority_granted": record.action_authority_granted,
    }


def _synthetic_signal_record(signal_id: str, signal_name: str, signal_class: str, **overrides: Any) -> SignalProvenanceRecord:
    payload = dict(
        signal_provenance_id=f"{signal_id}_provenance_v1",
        signal_id=signal_id,
        signal_name=signal_name,
        signal_class=signal_class,
        source_system=overrides.pop("source_system", signal_class),
        source_provider=overrides.pop("source_provider", "synthetic"),
        source_reference=overrides.pop("source_reference", signal_id),
        source_url_or_entity_id=overrides.pop("source_url_or_entity_id", signal_id),
        source_scope=overrides.pop("source_scope", "local_home"),
        owner_authorized=overrides.pop("owner_authorized", False),
        operator_authorized=overrides.pop("operator_authorized", False),
        retrieval_method=overrides.pop("retrieval_method", "synthetic_in_memory"),
        retrieval_timestamp=overrides.pop("retrieval_timestamp", "2026-06-01T20:00:00+02:00"),
        reported_timestamp=overrides.pop("reported_timestamp", "2026-06-01T19:58:00+02:00"),
        timezone=overrides.pop("timezone", "Europe/Berlin"),
        region=overrides.pop("region", "de-by"),
        country=overrides.pop("country", "DE"),
        grid_zone=overrides.pop("grid_zone", "de-lu"),
        market_zone=overrides.pop("market_zone", "de-lu"),
        unit=overrides.pop("unit", "kWh"),
        value_type=overrides.pop("value_type", "numeric"),
        expected_update_cadence=overrides.pop("expected_update_cadence", "hourly"),
        freshness_status=overrides.pop("freshness_status", ""),
        quality_status=overrides.pop("quality_status", ""),
        poison_shield_status=overrides.pop("poison_shield_status", "clean"),
        privacy_sensitivity=overrides.pop("privacy_sensitivity", "low"),
        control_capable=overrides.pop("control_capable", False),
        forecasting_allowed=overrides.pop("forecasting_allowed", True),
        scenario_simulation_allowed=overrides.pop("scenario_simulation_allowed", True),
        memory_write_allowed=overrides.pop("memory_write_allowed", False),
        action_authority_granted=overrides.pop("action_authority_granted", False),
        conflict_status=overrides.pop("conflict_status", "no_conflict"),
        normalization_status=overrides.pop("normalization_status", ""),
        safe_metadata=dict(overrides.pop("safe_metadata", {})),
    )
    payload.update(overrides)
    return build_signal_provenance_record_v1(**payload)


def _signal_bucket(record: SignalProvenanceRecord) -> str:
    sid = _normalize_text(record.signal_id)
    sname = _normalize_text(record.signal_name)
    sc = _normalize_text(record.signal_class)
    if "price" in sid or "price" in sname or "electricity_price" in sc:
        return "price"
    if "carbon" in sid or "carbon" in sname or "carbon" in sc:
        return "carbon"
    if "comfort" in sid or "comfort" in sname:
        return "comfort"
    if "pv" in sid or "pv" in sname or "weather" in sid or "weather" in sname:
        return "pv_weather"
    if "battery_soc" in sid or "soc" in sid:
        return "battery_soc"
    if "import_export" in sid or "import_export" in sname or "flow" in sc:
        return "grid_flow"
    if "occupancy" in sid or "presence" in sid:
        return "occupancy"
    if record.control_capable:
        return "control_capable"
    if record.freshness_status in {"stale", "expired", "missing_timestamp", "future_timestamp"}:
        return "stale_or_uncertain"
    return "general"


def _freshness_summary(records: list[SignalProvenanceRecord]) -> dict[str, str]:
    return {record.signal_id: evaluate_signal_freshness_v1(record) for record in records}


def _region_summary(records: list[SignalProvenanceRecord]) -> dict[str, str]:
    return {record.signal_id: f"{record.region}|{record.country}|{record.grid_zone}|{record.market_zone}" for record in records}


def _unit_summary(records: list[SignalProvenanceRecord]) -> dict[str, str]:
    return {record.signal_id: record.unit for record in records}


def _provenance_summary(records: list[SignalProvenanceRecord]) -> list[dict[str, Any]]:
    return [
        {
            "signal_id": record.signal_id,
            "signal_class": record.signal_class,
            "signal_name": record.signal_name,
            "freshness_status": evaluate_signal_freshness_v1(record),
            "quality_status": evaluate_signal_quality_v1(record),
            "conflict_status": record.conflict_status,
            "source_scope": record.source_scope,
            "region": record.region,
            "country": record.country,
            "grid_zone": record.grid_zone,
            "market_zone": record.market_zone,
            "unit": record.unit,
            "control_capable": record.control_capable,
        }
        for record in records
    ]


def _confidence_adjustment(conflicts: list[str], freshness: dict[str, str], quality: list[str]) -> float:
    score = 0.0
    if conflicts and conflicts != ["no_conflict"]:
        score -= 0.25
    if any(value in {"stale", "expired"} for value in freshness.values()):
        score -= 0.2
    if any(value in {"missing_timestamp", "future_timestamp"} for value in freshness.values()):
        score -= 0.15
    if any(value in {"poison_risk", "privacy_limited", "wrong_scope", "conflicting", "low_quality", "missing"} for value in quality):
        score -= 0.25
    return max(-1.0, min(0.0, round(score, 2)))


def _goal_from_text(value: Any) -> str:
    text = _safe_text(value)
    return text if text else DEFAULT_GOAL_V1


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def classify_energy_signal_conflict_v1(records: Iterable[Any]) -> str:
    items = [_record_like(item) for item in records]
    if not items:
        return "no_conflict"
    if any(item.conflict_status not in SIGNAL_CONFLICT_TYPES_V1 for item in items):
        return "unknown_conflict"

    buckets = [_signal_bucket(item) for item in items]
    ids = [item.signal_id for item in items]
    scopes = {item.source_scope for item in items}
    units = {item.unit for item in items if item.unit}
    regions = {(item.region, item.country, item.grid_zone, item.market_zone) for item in items}
    freshness = [evaluate_signal_freshness_v1(item) for item in items]
    control_capable = any(item.control_capable for item in items)

    if any(bucket == "price" for bucket in buckets) and any(bucket == "carbon" for bucket in buckets):
        return "price_vs_carbon_conflict"
    if any(bucket == "price" for bucket in buckets) and any(bucket == "comfort" for bucket in buckets):
        return "price_vs_comfort_conflict"
    if any(bucket == "carbon" for bucket in buckets) and any(bucket == "comfort" for bucket in buckets):
        return "carbon_vs_comfort_conflict"
    if any("pv_forecast" in _normalize_text(item.signal_id) or "pv" in _normalize_text(item.signal_name) for item in items) and any("weather" in _normalize_text(item.signal_id) or "weather" in _normalize_text(item.signal_name) for item in items):
        return "pv_forecast_vs_weather_conflict"
    if any("battery_soc" in _normalize_text(item.signal_id) for item in items) and len({item.source_system + "|" + item.source_provider for item in items}) > 1:
        return "battery_soc_source_conflict"
    if len(scopes) > 1 and any(bucket == "grid_flow" for bucket in buckets):
        return "grid_import_export_scope_conflict"
    if any(item.signal_class == "external_document_signal" or _normalize_text(item.privacy_sensitivity) in {"high", "very_high", "private"} or "occupancy" in _normalize_text(item.signal_id) for item in items):
        return "privacy_or_authority_conflict"
    if control_capable and any(not item.action_authority_granted for item in items):
        if any(bucket == "control_capable" for bucket in buckets):
            return "control_capability_conflict"
    if len(units) > 1:
        return "unit_conflict"
    if len(regions) > 1:
        return "region_or_grid_zone_conflict"
    if len(set(freshness)) > 1 or any(value in {"stale", "expired", "missing_timestamp", "future_timestamp"} for value in freshness):
        return "timestamp_or_freshness_conflict"
    if len(set((item.signal_class, item.source_system, item.source_provider, item.source_reference) for item in items)) > 1:
        return "source_disagreement"
    if len(set(ids)) > 1:
        return "forecast_vs_observed_conflict" if any("forecast" in _normalize_text(item.signal_id) for item in items) else "semantic_conflict"
    return "no_conflict"


# ---------------------------------------------------------------------------
# Builders and resolution
# ---------------------------------------------------------------------------


def build_energy_signal_conflict_decision_v1(
    *,
    conflict_decision_id: str,
    decision_subject: str,
    conflict_classes: Iterable[str],
    involved_signals: Iterable[Any],
    owner_priority: bool = False,
    optimization_goal: str = DEFAULT_GOAL_V1,
    safety_constraints: Iterable[str] | None = None,
    comfort_constraints: Iterable[str] | None = None,
    deadline_constraints: Iterable[str] | None = None,
    privacy_constraints: Iterable[str] | None = None,
    authority_constraints: Iterable[str] | None = None,
    preferred_signal_if_any: str = "",
    unresolved_conflicts: Iterable[str] | None = None,
    scenario_branch_required: bool | None = None,
    confidence_adjustment: float | None = None,
    recommended_resolution_strategy: str | None = None,
    recommended_next_signal: str = "",
    safe_recommendation_mode: str = DEFAULT_RECOMMENDATION_MODE_V1,
    action_authority_granted: bool = False,
    automation_allowed: bool = False,
    device_control_allowed: bool = False,
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    public_claim_allowed: bool = False,
    learning_claimed: bool = False,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> EnergySignalConflictDecision:
    records = [_record_like(item) for item in involved_signals]
    conflicts = _safe_list(conflict_classes)
    resolved_strategy = recommended_resolution_strategy or _pick_resolution_strategy(records, conflicts, owner_priority, optimization_goal, safety_constraints or [], comfort_constraints or [], deadline_constraints or [], privacy_constraints or [], authority_constraints or [])
    if scenario_branch_required is None:
        scenario_branch_required = any(conflict in TRADEOFF_CONFLICTS_V1 for conflict in conflicts)
    if confidence_adjustment is None:
        confidence_adjustment = _confidence_adjustment(conflicts, _freshness_summary(records), [evaluate_signal_quality_v1(r) for r in records])
    decision = EnergySignalConflictDecision(
        conflict_decision_id=_safe_text(conflict_decision_id),
        decision_subject=_safe_text(decision_subject),
        conflict_classes=conflicts,
        involved_signals=[item.signal_id for item in records],
        signal_provenance_summary=_provenance_summary(records),
        freshness_summary=_freshness_summary(records),
        region_scope_summary=_region_summary(records),
        unit_scope_summary=_unit_summary(records),
        owner_priority=_safe_bool(owner_priority),
        optimization_goal=_goal_from_text(optimization_goal),
        safety_constraints=_safe_list(safety_constraints),
        comfort_constraints=_safe_list(comfort_constraints),
        deadline_constraints=_safe_list(deadline_constraints),
        privacy_constraints=_safe_list(privacy_constraints),
        authority_constraints=_safe_list(authority_constraints),
        preferred_signal_if_any=_safe_text(preferred_signal_if_any),
        unresolved_conflicts=_safe_list(unresolved_conflicts if unresolved_conflicts is not None else ([c for c in conflicts if c != "no_conflict"])),
        scenario_branch_required=_safe_bool(scenario_branch_required),
        confidence_adjustment=float(confidence_adjustment),
        recommended_resolution_strategy=_safe_text(resolved_strategy),
        recommended_next_signal=_safe_text(recommended_next_signal),
        safe_recommendation_mode=_safe_text(safe_recommendation_mode),
        action_authority_granted=_safe_bool(action_authority_granted),
        automation_allowed=_safe_bool(automation_allowed),
        device_control_allowed=_safe_bool(device_control_allowed),
        runtime_authority=_safe_bool(runtime_authority),
        writes_state=_safe_bool(writes_state),
        model_provider_used=_safe_bool(model_provider_used),
        public_claim_allowed=_safe_bool(public_claim_allowed),
        learning_claimed=_safe_bool(learning_claimed),
        safe_metadata={**dict(safe_metadata or {}), **dict(extra_metadata)},
    )
    validate_energy_signal_conflict_decision_v1(decision)
    return decision


def _pick_resolution_strategy(
    records: list[SignalProvenanceRecord],
    conflicts: list[str],
    owner_priority: bool,
    optimization_goal: str,
    safety_constraints: list[str],
    comfort_constraints: list[str],
    deadline_constraints: list[str],
    privacy_constraints: list[str],
    authority_constraints: list[str],
) -> str:
    freshness = _freshness_summary(records)
    quality = [evaluate_signal_quality_v1(record) for record in records]
    if any(value in {"stale", "expired", "missing_timestamp", "future_timestamp"} for value in freshness.values()):
        return "wait_for_fresh_signal"
    if owner_priority or optimization_goal == "owner_manual_priority":
        return "prefer_owner_manual_priority"
    if safety_constraints or optimization_goal == "safety_first":
        return "prefer_safety_constraint"
    if deadline_constraints or optimization_goal == "meet_ev_departure_deadline":
        return "prefer_deadline_constraint"
    if any(conflict in {"price_vs_carbon_conflict", "price_vs_comfort_conflict", "carbon_vs_comfort_conflict", "pv_forecast_vs_weather_conflict", "battery_soc_source_conflict", "grid_import_export_scope_conflict", "region_or_grid_zone_conflict", "source_disagreement", "forecast_vs_observed_conflict"} for conflict in conflicts):
        return "branch_scenarios"
    if any(q in {"poison_risk", "privacy_limited", "wrong_scope", "conflicting", "missing", "stale", "low_quality"} for q in quality):
        return "recommend_no_action"
    if privacy_constraints:
        return "prefer_safety_constraint"
    if comfort_constraints and optimization_goal == "maintain_comfort":
        return "prefer_safety_constraint"
    if authority_constraints:
        return "block_recommendation"
    return "preserve_conflict" if conflicts else "recommend_data_collection"


def resolve_energy_signal_conflict_v1(
    records: Iterable[Any],
    *,
    decision_subject: str,
    optimization_goal: str = DEFAULT_GOAL_V1,
    owner_priority: bool = False,
    safety_constraints: Iterable[str] | None = None,
    comfort_constraints: Iterable[str] | None = None,
    deadline_constraints: Iterable[str] | None = None,
    privacy_constraints: Iterable[str] | None = None,
    authority_constraints: Iterable[str] | None = None,
    preferred_signal_if_any: str = "",
    recommended_next_signal: str = "",
    safe_recommendation_mode: str = DEFAULT_RECOMMENDATION_MODE_V1,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> EnergySignalConflictDecision:
    items = [_record_like(item) for item in records]
    conflict_class = classify_energy_signal_conflict_v1(items)
    unresolved = [] if conflict_class == "no_conflict" else [conflict_class]
    if conflict_class == "unknown_conflict":
        strategy = "unknown_resolution"
    else:
        strategy = _pick_resolution_strategy(items, [conflict_class], owner_priority, optimization_goal, _safe_list(safety_constraints), _safe_list(comfort_constraints), _safe_list(deadline_constraints), _safe_list(privacy_constraints), _safe_list(authority_constraints))
    if conflict_class == "timestamp_or_freshness_conflict" and strategy not in {"wait_for_fresh_signal", "recommend_no_action"}:
        strategy = "wait_for_fresh_signal"
    if conflict_class in TRADEOFF_CONFLICTS_V1:
        scenario_branch_required = True
    else:
        scenario_branch_required = False if conflict_class == "no_conflict" else conflict_class in TRADEOFF_CONFLICTS_V1
    if not recommended_next_signal:
        recommended_next_signal = "collect_fresh_local_signal" if strategy == "wait_for_fresh_signal" else "collect_resolution_context"
    if conflict_class in {"privacy_or_authority_conflict", "control_capability_conflict"}:
        strategy = "block_recommendation" if strategy == "preserve_conflict" else strategy
    if conflict_class == "no_conflict" and any(_safe_text(item.freshness_status) in {"stale", "expired", "missing_timestamp", "future_timestamp"} for item in items):
        strategy = "wait_for_fresh_signal"
        unresolved = ["timestamp_or_freshness_conflict"]
    return build_energy_signal_conflict_decision_v1(
        conflict_decision_id=f"{_safe_text(decision_subject).replace(' ', '_').lower()}_decision_v1",
        decision_subject=decision_subject,
        conflict_classes=[conflict_class],
        involved_signals=items,
        owner_priority=owner_priority,
        optimization_goal=optimization_goal,
        safety_constraints=safety_constraints,
        comfort_constraints=comfort_constraints,
        deadline_constraints=deadline_constraints,
        privacy_constraints=privacy_constraints,
        authority_constraints=authority_constraints,
        preferred_signal_if_any=preferred_signal_if_any,
        unresolved_conflicts=unresolved,
        scenario_branch_required=scenario_branch_required,
        confidence_adjustment=None,
        recommended_resolution_strategy=strategy,
        recommended_next_signal=recommended_next_signal,
        safe_recommendation_mode=safe_recommendation_mode,
        action_authority_granted=False,
        automation_allowed=False,
        device_control_allowed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        learning_claimed=False,
        safe_metadata=safe_metadata,
        **extra_metadata,
    )


# ---------------------------------------------------------------------------
# Validation and summary
# ---------------------------------------------------------------------------


def validate_energy_signal_conflict_decision_v1(decision: Any) -> bool:
    original = decision if isinstance(decision, Mapping) else asdict(decision) if is_dataclass(decision) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    normalized = decision if isinstance(decision, EnergySignalConflictDecision) else _decision_like(decision)
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if not normalized.conflict_decision_id:
        raise ValidationError("conflict_decision_id_required")
    if not normalized.decision_subject:
        raise ValidationError("decision_subject_required")
    for conflict in normalized.conflict_classes:
        if conflict not in ALLOWED_CONFLICT_CLASSES_V1:
            raise ValidationError("unknown_conflict_class")
    if normalized.recommended_resolution_strategy not in ALLOWED_RESOLUTION_STRATEGIES_V1:
        raise ValidationError("unknown_resolution_strategy")
    if normalized.optimization_goal not in ALLOWED_ENERGY_GOALS_V1:
        raise ValidationError("unknown_optimization_goal")
    if normalized.action_authority_granted:
        raise ValidationError("action_authority_granted_must_be_false")
    if normalized.automation_allowed:
        raise ValidationError("automation_allowed_must_be_false")
    if normalized.device_control_allowed:
        raise ValidationError("device_control_allowed_must_be_false")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.safe_metadata and _contains_forbidden_claim_marker(normalized.safe_metadata):
        raise ValidationError("forbidden_claim_marker_detected")
    return True


def _decision_like(value: Any) -> EnergySignalConflictDecision:
    if isinstance(value, EnergySignalConflictDecision):
        return value
    if not isinstance(value, Mapping):
        value = asdict(value) if is_dataclass(value) else {}
    return EnergySignalConflictDecision(
        conflict_decision_id=_safe_text(value.get("conflict_decision_id")),
        decision_subject=_safe_text(value.get("decision_subject")),
        conflict_classes=_safe_list(value.get("conflict_classes")),
        involved_signals=_safe_list(value.get("involved_signals")),
        signal_provenance_summary=[dict(item) for item in value.get("signal_provenance_summary", [])],
        freshness_summary={str(k): _safe_text(v) for k, v in dict(value.get("freshness_summary", {})).items()},
        region_scope_summary={str(k): _safe_text(v) for k, v in dict(value.get("region_scope_summary", {})).items()},
        unit_scope_summary={str(k): _safe_text(v) for k, v in dict(value.get("unit_scope_summary", {})).items()},
        owner_priority=_safe_bool(value.get("owner_priority")),
        optimization_goal=_safe_text(value.get("optimization_goal")),
        safety_constraints=_safe_list(value.get("safety_constraints")),
        comfort_constraints=_safe_list(value.get("comfort_constraints")),
        deadline_constraints=_safe_list(value.get("deadline_constraints")),
        privacy_constraints=_safe_list(value.get("privacy_constraints")),
        authority_constraints=_safe_list(value.get("authority_constraints")),
        preferred_signal_if_any=_safe_text(value.get("preferred_signal_if_any")),
        unresolved_conflicts=_safe_list(value.get("unresolved_conflicts")),
        scenario_branch_required=_safe_bool(value.get("scenario_branch_required")),
        confidence_adjustment=float(value.get("confidence_adjustment", 0.0) or 0.0),
        recommended_resolution_strategy=_safe_text(value.get("recommended_resolution_strategy")),
        recommended_next_signal=_safe_text(value.get("recommended_next_signal")),
        safe_recommendation_mode=_safe_text(value.get("safe_recommendation_mode")),
        action_authority_granted=_safe_bool(value.get("action_authority_granted")),
        automation_allowed=_safe_bool(value.get("automation_allowed")),
        device_control_allowed=_safe_bool(value.get("device_control_allowed")),
        runtime_authority=_safe_bool(value.get("runtime_authority")),
        writes_state=_safe_bool(value.get("writes_state")),
        model_provider_used=_safe_bool(value.get("model_provider_used")),
        public_claim_allowed=_safe_bool(value.get("public_claim_allowed")),
        learning_claimed=_safe_bool(value.get("learning_claimed")),
        safe_metadata=dict(value.get("safe_metadata") or {}),
    )


def summarize_energy_signal_conflict_decision_v1(decision: Any) -> EnergySignalConflictSummary:
    normalized = _decision_like(decision)
    validate_energy_signal_conflict_decision_v1(normalized)
    return EnergySignalConflictSummary(
        summary_type=SUMMARY_TYPE_V1,
        conflict_decision_id=normalized.conflict_decision_id,
        decision_subject=normalized.decision_subject,
        conflict_classes=list(normalized.conflict_classes),
        recommended_resolution_strategy=normalized.recommended_resolution_strategy,
        confidence_adjustment=normalized.confidence_adjustment,
        scenario_branch_required=normalized.scenario_branch_required,
        unresolved_conflicts=list(normalized.unresolved_conflicts),
        optimization_goal=normalized.optimization_goal,
        safe_recommendation_mode=normalized.safe_recommendation_mode,
    )


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------


def build_initial_energy_signal_conflict_examples_v1() -> list[EnergySignalConflictDecision]:
    examples = build_initial_signal_provenance_examples_v1()
    by_id = {item.signal_id: item for item in examples}
    pv_forecast = _synthetic_signal_record(
        signal_id="pv_forecast_signal",
        signal_name="PV Forecast Signal",
        signal_class="weather_provider",
        source_system="forecast_service",
        source_provider="forecast_service",
        source_reference="pv-forecast-1",
        source_url_or_entity_id="forecast:pv",
        source_scope="location_scoped",
        unit="kWh",
        value_type="numeric",
        expected_update_cadence="hourly",
        safe_metadata={"signal_value": 14},
    )
    heat_pump_comfort = _synthetic_signal_record(
        signal_id="heat_pump_comfort_signal",
        signal_name="Heat Pump Comfort Signal",
        signal_class="heat_pump_api",
        source_system="heat_pump_api",
        source_provider="heat_pump_vendor",
        source_reference="heat-pump-comfort-1",
        source_url_or_entity_id="device:heat-pump-1",
        source_scope="local_home",
        unit="°C",
        value_type="numeric",
        expected_update_cadence="hourly",
        safe_metadata={"signal_value": 21.0},
    )
    occupancy_privacy = _synthetic_signal_record(
        signal_id="occupancy_privacy_signal",
        signal_name="Occupancy Privacy Signal",
        signal_class="home_assistant_entity",
        source_system="home_assistant",
        source_provider="local_entity",
        source_reference="binary_sensor.occupancy",
        source_url_or_entity_id="binary_sensor.occupancy",
        source_scope="local_home",
        privacy_sensitivity="high",
        safe_metadata={"signal_value": True},
    )
    local_import_export = _synthetic_signal_record(
        signal_id="local_import_export_flow_signal",
        signal_name="Local Import Export Flow Signal",
        signal_class="import_export_flow_provider",
        source_system="home_energy_meter",
        source_provider="local_meter",
        source_reference="meter-home-flow",
        source_url_or_entity_id="meter:home-flow",
        source_scope="local_home",
        unit="kW",
        value_type="numeric",
        expected_update_cadence="minutes",
        safe_metadata={"signal_value": 1.5},
    )
    stale_price = _synthetic_signal_record(
        signal_id="stale_price_signal",
        signal_name="Stale Price Signal",
        signal_class="electricity_price_provider",
        source_system="price_api",
        source_provider="market_operator",
        source_reference="stale-price-1",
        source_url_or_entity_id="de-day-ahead",
        source_scope="market_zone",
        unit="EUR/kWh",
        expected_update_cadence="hourly",
        reported_timestamp="2026-06-01T10:00:00+02:00",
        safe_metadata={"signal_value": 0.37},
    )
    return [
        resolve_energy_signal_conflict_v1(
            [by_id["electricity_price_day_ahead_recent"], by_id["carbon_intensity_grid_zone_recent"]],
            decision_subject="price_low_carbon_high_conflict",
            optimization_goal="minimize_cost",
            recommended_next_signal="collect_owner_priority",
        ),
        resolve_energy_signal_conflict_v1(
            [by_id["electricity_price_day_ahead_recent"], pv_forecast],
            decision_subject="price_high_pv_surplus_likely_conflict",
            optimization_goal="maximize_self_consumption",
            recommended_next_signal="collect_fresh_weather_and_pv",
        ),
        resolve_energy_signal_conflict_v1(
            [pv_forecast, by_id["weather_forecast_location_scoped"]],
            decision_subject="pv_forecast_weather_cloud_conflict",
            optimization_goal="maximize_self_consumption",
            recommended_next_signal="collect_fresh_weather",
        ),
        resolve_energy_signal_conflict_v1(
            [by_id["battery_soc_home_assistant_fresh"], by_id["battery_soc_source_conflict"]],
            decision_subject="battery_soc_source_mismatch_conflict",
            optimization_goal="protect_battery_reserve",
            recommended_next_signal="verify_inverter_and_home_assistant_sources",
        ),
        resolve_energy_signal_conflict_v1(
            [by_id["import_export_country_macro_context"], local_import_export],
            decision_subject="country_import_export_vs_household_flow_conflict",
            optimization_goal="avoid_grid_import",
            recommended_next_signal="collect_local_household_flow",
        ),
        resolve_energy_signal_conflict_v1(
            [heat_pump_comfort, by_id["electricity_price_day_ahead_recent"]],
            decision_subject="heat_pump_comfort_vs_price_conflict",
            optimization_goal="maintain_comfort",
            safety_constraints=["comfort_band"],
            recommended_next_signal="collect_comfort_constraints",
        ),
        resolve_energy_signal_conflict_v1(
            [by_id["electricity_price_day_ahead_recent"], by_id["carbon_intensity_grid_zone_recent"]],
            decision_subject="ev_departure_deadline_vs_carbon_window_conflict",
            optimization_goal="meet_ev_departure_deadline",
            deadline_constraints=["departure_deadline"],
            recommended_next_signal="collect_departure_deadline_and_required_soc",
        ),
        resolve_energy_signal_conflict_v1(
            [occupancy_privacy, by_id["weather_forecast_location_scoped"]],
            decision_subject="occupancy_signal_privacy_limited_conflict",
            optimization_goal="maintain_comfort",
            privacy_constraints=["occupancy_private"],
            recommended_next_signal="collect_lower_sensitivity_proxy",
        ),
        resolve_energy_signal_conflict_v1(
            [by_id["battery_soc_home_assistant_fresh"]],
            decision_subject="control_capable_entity_read_only_conflict",
            optimization_goal="safety_first",
            recommended_next_signal="no_action_required",
        ),
        resolve_energy_signal_conflict_v1(
            [stale_price],
            decision_subject="stale_signal_no_action_recommendation",
            optimization_goal="safety_first",
            recommended_next_signal="request_fresh_timestamped_signal",
        ),
    ]
