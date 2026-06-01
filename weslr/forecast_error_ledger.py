"""Metadata-only forecast error ledger helpers v1.

This module records synthetic forecast/scenario/recommendation outcome metadata
so WESLR can reason about stale signals, wrong assumptions, bad causal
hypotheses, missing data, and behavior-pack candidates.

It is pure, deterministic, import-safe, and fail-closed.
It does not update runtime behavior automatically. It does not write memory or
`.weslr`. It does not claim autonomous learning.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping

HELPER_TYPE_V1 = "forecast_error_ledger_v1"
RECORD_TYPE_V1 = "forecast_error_record_v1"
LEDGER_TYPE_V1 = "forecast_error_ledger_v1"
SUMMARY_TYPE_V1 = "forecast_error_ledger_summary_v1"

ALLOWED_OUTCOME_MATCH_STATUSES_V1 = {
    "matched",
    "partially_matched",
    "missed",
    "opposite_outcome",
    "unobserved",
    "observation_incomplete",
    "blocked_no_observation",
    "unknown",
}

ALLOWED_ERROR_TYPES_V1 = {
    "stale_signal",
    "missing_signal",
    "wrong_signal",
    "wrong_region_or_grid_zone",
    "wrong_unit",
    "signal_conflict_unresolved",
    "bad_causal_hypothesis",
    "wrong_assumption",
    "wrong_owner_priority",
    "overconfidence",
    "underconfidence",
    "poisoned_signal",
    "authority_gap",
    "privacy_gap",
    "scenario_branch_missing",
    "invalidation_trigger_missed",
    "observation_missing",
    "unknown_error",
}

ALLOWED_SEVERITIES_V1 = {"none", "minor", "moderate", "major", "critical", "unknown"}

ALLOWED_DOMAINS_V1 = {
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
    "autonomous learning",
    "autonomous learn",
    "public readiness",
    "public readiness claim",
    "energy savings guarantee",
    "prediction certainty",
    "runtime authority",
    "public claim",
    "learning claim",
    "agi",
    "consciousness",
    "sentience",
    "turing",
    "certification",
)

DEFAULT_DOMAIN_V1 = "unknown_domain"
DEFAULT_OUTCOME_V1 = "unknown"
DEFAULT_ERROR_TYPE_V1 = "unknown_error"
DEFAULT_SEVERITY_V1 = "unknown"
DEFAULT_FORECAST_HORIZON_V1 = "unknown"


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ForecastErrorRecord:
    forecast_error_record_id: str
    source_forecast_id: str
    source_scenario_simulation_id: str
    source_energy_intelligence_id: str
    subject: str
    domain: str
    forecast_horizon: str
    created_timestamp: str
    observation_timestamp: str
    expected_outcome: str
    observed_outcome: str
    outcome_match_status: str
    error_type: str
    error_severity: str
    confidence_before: float
    confidence_after: float
    assumptions_used: list[str]
    assumptions_failed: list[str]
    signals_used: list[str]
    stale_signals: list[str]
    missing_signals: list[str]
    conflicting_signals: list[str]
    wrong_region_or_grid_zone: bool
    wrong_unit: bool
    poisoned_or_quarantined_signal: bool
    bad_causal_hypothesis: bool
    wrong_owner_priority: bool
    overconfidence_detected: bool
    underconfidence_detected: bool
    recommendation_taken: str
    owner_action_taken: str
    action_authority_used: bool
    resulting_effect: str
    corrective_lesson: str
    recommended_model_update: str
    behavior_pack_candidate: str
    requires_owner_review: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ForecastErrorLedger:
    forecast_error_ledger_id: str
    ledger_version: str
    records: list[ForecastErrorRecord]
    record_count: int
    domain_counts: dict[str, int]
    error_type_counts: dict[str, int]
    severity_counts: dict[str, int]
    repeated_error_patterns: list[str]
    owner_review_required_records: list[str]
    behavior_pack_candidates: list[str]
    recommended_next_lanes: list[str]
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ForecastErrorRecordSummary:
    summary_type: str
    forecast_error_record_id: str
    source_forecast_id: str
    subject: str
    domain: str
    outcome_match_status: str
    error_type: str
    error_severity: str
    confidence_before: float
    confidence_after: float
    stale_signal_count: int
    missing_signal_count: int
    conflicting_signal_count: int
    behavior_pack_candidate: str
    requires_owner_review: bool


@dataclass(frozen=True, slots=True)
class ForecastErrorLedgerSummary:
    summary_type: str
    forecast_error_ledger_id: str
    record_count: int
    domain_counts: dict[str, int]
    error_type_counts: dict[str, int]
    severity_counts: dict[str, int]
    repeated_error_patterns: list[str]
    owner_review_required_records: list[str]
    behavior_pack_candidates: list[str]
    recommended_next_lanes: list[str]


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


def to_forecast_error_json_safe_v1(value: Any) -> Any:
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


def _contains_forbidden_claim_marker(value: Any, *, _metadata_scope: bool = False) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if _metadata_scope or key_text == "safe_metadata" or key_text.endswith("_metadata"):
                if _contains_forbidden_claim_marker(item, _metadata_scope=True):
                    return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item, _metadata_scope=_metadata_scope) for item in value)
    if not _metadata_scope and not isinstance(value, str):
        return False
    blob = _normalize_text(value)
    if not blob:
        return False
    return any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1)


def _record_like(value: Any) -> ForecastErrorRecord:
    if isinstance(value, ForecastErrorRecord):
        return value
    if not isinstance(value, Mapping):
        value = asdict(value) if is_dataclass(value) else {}
    return ForecastErrorRecord(
        forecast_error_record_id=_safe_text(value.get("forecast_error_record_id")),
        source_forecast_id=_safe_text(value.get("source_forecast_id")),
        source_scenario_simulation_id=_safe_text(value.get("source_scenario_simulation_id")),
        source_energy_intelligence_id=_safe_text(value.get("source_energy_intelligence_id")),
        subject=_safe_text(value.get("subject")),
        domain=_safe_text(value.get("domain")),
        forecast_horizon=_safe_text(value.get("forecast_horizon")),
        created_timestamp=_safe_text(value.get("created_timestamp")),
        observation_timestamp=_safe_text(value.get("observation_timestamp")),
        expected_outcome=_safe_text(value.get("expected_outcome")),
        observed_outcome=_safe_text(value.get("observed_outcome")),
        outcome_match_status=_safe_text(value.get("outcome_match_status")),
        error_type=_safe_text(value.get("error_type")),
        error_severity=_safe_text(value.get("error_severity")),
        confidence_before=float(value.get("confidence_before", 0.0) or 0.0),
        confidence_after=float(value.get("confidence_after", 0.0) or 0.0),
        assumptions_used=_safe_list(value.get("assumptions_used")),
        assumptions_failed=_safe_list(value.get("assumptions_failed")),
        signals_used=_safe_list(value.get("signals_used")),
        stale_signals=_safe_list(value.get("stale_signals")),
        missing_signals=_safe_list(value.get("missing_signals")),
        conflicting_signals=_safe_list(value.get("conflicting_signals")),
        wrong_region_or_grid_zone=_safe_bool(value.get("wrong_region_or_grid_zone")),
        wrong_unit=_safe_bool(value.get("wrong_unit")),
        poisoned_or_quarantined_signal=_safe_bool(value.get("poisoned_or_quarantined_signal")),
        bad_causal_hypothesis=_safe_bool(value.get("bad_causal_hypothesis")),
        wrong_owner_priority=_safe_bool(value.get("wrong_owner_priority")),
        overconfidence_detected=_safe_bool(value.get("overconfidence_detected")),
        underconfidence_detected=_safe_bool(value.get("underconfidence_detected")),
        recommendation_taken=_safe_text(value.get("recommendation_taken")),
        owner_action_taken=_safe_text(value.get("owner_action_taken")),
        action_authority_used=_safe_bool(value.get("action_authority_used")),
        resulting_effect=_safe_text(value.get("resulting_effect")),
        corrective_lesson=_safe_text(value.get("corrective_lesson")),
        recommended_model_update=_safe_text(value.get("recommended_model_update")),
        behavior_pack_candidate=_safe_text(value.get("behavior_pack_candidate")),
        requires_owner_review=_safe_bool(value.get("requires_owner_review")),
        runtime_authority=_safe_bool(value.get("runtime_authority")),
        writes_state=_safe_bool(value.get("writes_state")),
        model_provider_used=_safe_bool(value.get("model_provider_used")),
        public_claim_allowed=_safe_bool(value.get("public_claim_allowed")),
        learning_claimed=_safe_bool(value.get("learning_claimed")),
        safe_metadata=dict(value.get("safe_metadata") or {}),
    )


def _error_type_from_record(record: ForecastErrorRecord) -> str:
    if record.observed_outcome == "blocked_no_observation":
        return "observation_missing"
    if record.poisoned_or_quarantined_signal:
        return "poisoned_signal"
    if record.stale_signals:
        return "stale_signal"
    if record.missing_signals:
        return "missing_signal"
    if record.conflicting_signals:
        return "signal_conflict_unresolved"
    if record.wrong_region_or_grid_zone:
        return "wrong_region_or_grid_zone"
    if record.wrong_unit:
        return "wrong_unit"
    if record.bad_causal_hypothesis:
        return "bad_causal_hypothesis"
    if record.wrong_owner_priority:
        return "wrong_owner_priority"
    if record.overconfidence_detected:
        return "overconfidence"
    if record.underconfidence_detected:
        return "underconfidence"
    if record.requires_owner_review and not record.action_authority_used:
        return "authority_gap"
    if record.observed_outcome in {"missed", "opposite_outcome"} and not record.assumptions_failed:
        return "wrong_assumption"
    return _safe_text(record.error_type or DEFAULT_ERROR_TYPE_V1)


def _severity_from_record(record: ForecastErrorRecord) -> str:
    if record.error_severity in ALLOWED_SEVERITIES_V1:
        return record.error_severity
    if record.outcome_match_status == "matched":
        return "none"
    if record.observed_outcome == "blocked_no_observation":
        return "minor"
    if record.poisoned_or_quarantined_signal or record.action_authority_used:
        return "critical"
    if record.conflicting_signals or record.missing_signals:
        return "major"
    if record.stale_signals or record.overconfidence_detected or record.underconfidence_detected:
        return "moderate"
    return "unknown"


def _outcome_from_record(record: ForecastErrorRecord) -> str:
    if record.observed_outcome == "blocked_no_observation":
        return "blocked_no_observation"
    if not record.observation_timestamp:
        return "unobserved"
    return _safe_text(record.outcome_match_status or DEFAULT_OUTCOME_V1)


def _behavior_pack_from_error_type(error_type: str) -> str:
    mapping = {
        "stale_signal": "refresh_signal_freshness_pack",
        "missing_signal": "missing_signal_collection_pack",
        "wrong_signal": "signal_selection_review_pack",
        "wrong_region_or_grid_zone": "region_normalization_pack",
        "wrong_unit": "unit_normalization_pack",
        "signal_conflict_unresolved": "conflict_branching_pack",
        "bad_causal_hypothesis": "causal_hypothesis_review_pack",
        "wrong_assumption": "assumption_audit_pack",
        "wrong_owner_priority": "owner_priority_alignment_pack",
        "overconfidence": "confidence_calibration_pack",
        "underconfidence": "confidence_calibration_pack",
        "poisoned_signal": "poison_shield_review_pack",
        "authority_gap": "authority_boundary_pack",
        "privacy_gap": "privacy_boundary_pack",
        "scenario_branch_missing": "scenario_branching_pack",
        "invalidation_trigger_missed": "invalidation_trigger_pack",
        "observation_missing": "observation_collection_pack",
    }
    return mapping.get(error_type, "")


def _next_lane_from_error_type(error_type: str) -> str:
    mapping = {
        "stale_signal": "DESIGN_WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1",
        "missing_signal": "DESIGN_WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1",
        "wrong_region_or_grid_zone": "DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1",
        "wrong_unit": "DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1",
        "signal_conflict_unresolved": "DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1",
        "bad_causal_hypothesis": "DESIGN_WESLR_FORECASTING_AND_SCENARIOS_V1",
        "wrong_assumption": "DESIGN_WESLR_FORECASTING_AND_SCENARIOS_V1",
        "wrong_owner_priority": "DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1",
        "overconfidence": "DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1",
        "underconfidence": "DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1",
        "poisoned_signal": "DESIGN_WESLR_POISON_SHIELD_ADVERSARIAL_CONTENT_QUARANTINE_AND_AUTHORITY_FIREWALL_V1",
        "authority_gap": "DESIGN_WESLR_CAPABILITY_MATURITY_REGISTRY_V1",
        "privacy_gap": "DESIGN_WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1",
        "scenario_branch_missing": "DESIGN_WESLR_ENERGY_SIGNAL_CONFLICT_RESOLUTION_POLICY_V1",
        "invalidation_trigger_missed": "DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1",
        "observation_missing": "DESIGN_WESLR_FORECAST_ERROR_LEDGER_V1",
    }
    return mapping.get(error_type, "")


# ---------------------------------------------------------------------------
# Builders and validators
# ---------------------------------------------------------------------------


def build_forecast_error_record_v1(
    *,
    forecast_error_record_id: str,
    source_forecast_id: str,
    source_scenario_simulation_id: str,
    source_energy_intelligence_id: str,
    subject: str,
    domain: str = DEFAULT_DOMAIN_V1,
    forecast_horizon: str = DEFAULT_FORECAST_HORIZON_V1,
    created_timestamp: str = "2026-06-01T20:00:00+02:00",
    observation_timestamp: str = "2026-06-01T20:10:00+02:00",
    expected_outcome: str = "",
    observed_outcome: str = "",
    outcome_match_status: str = DEFAULT_OUTCOME_V1,
    error_type: str = DEFAULT_ERROR_TYPE_V1,
    error_severity: str = DEFAULT_SEVERITY_V1,
    confidence_before: float = 0.0,
    confidence_after: float = 0.0,
    assumptions_used: Iterable[str] | None = None,
    assumptions_failed: Iterable[str] | None = None,
    signals_used: Iterable[str] | None = None,
    stale_signals: Iterable[str] | None = None,
    missing_signals: Iterable[str] | None = None,
    conflicting_signals: Iterable[str] | None = None,
    wrong_region_or_grid_zone: bool = False,
    wrong_unit: bool = False,
    poisoned_or_quarantined_signal: bool = False,
    bad_causal_hypothesis: bool = False,
    wrong_owner_priority: bool = False,
    overconfidence_detected: bool = False,
    underconfidence_detected: bool = False,
    recommendation_taken: str = "",
    owner_action_taken: str = "",
    action_authority_used: bool = False,
    resulting_effect: str = "",
    corrective_lesson: str = "",
    recommended_model_update: str = "",
    behavior_pack_candidate: str = "",
    requires_owner_review: bool = False,
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    public_claim_allowed: bool = False,
    learning_claimed: bool = False,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> ForecastErrorRecord:
    record = ForecastErrorRecord(
        forecast_error_record_id=_safe_text(forecast_error_record_id),
        source_forecast_id=_safe_text(source_forecast_id),
        source_scenario_simulation_id=_safe_text(source_scenario_simulation_id),
        source_energy_intelligence_id=_safe_text(source_energy_intelligence_id),
        subject=_safe_text(subject),
        domain=_safe_text(domain),
        forecast_horizon=_safe_text(forecast_horizon),
        created_timestamp=_safe_text(created_timestamp),
        observation_timestamp=_safe_text(observation_timestamp),
        expected_outcome=_safe_text(expected_outcome),
        observed_outcome=_safe_text(observed_outcome),
        outcome_match_status=_safe_text(outcome_match_status),
        error_type=_safe_text(error_type),
        error_severity=_safe_text(error_severity),
        confidence_before=float(confidence_before),
        confidence_after=float(confidence_after),
        assumptions_used=_safe_list(assumptions_used),
        assumptions_failed=_safe_list(assumptions_failed),
        signals_used=_safe_list(signals_used),
        stale_signals=_safe_list(stale_signals),
        missing_signals=_safe_list(missing_signals),
        conflicting_signals=_safe_list(conflicting_signals),
        wrong_region_or_grid_zone=_safe_bool(wrong_region_or_grid_zone),
        wrong_unit=_safe_bool(wrong_unit),
        poisoned_or_quarantined_signal=_safe_bool(poisoned_or_quarantined_signal),
        bad_causal_hypothesis=_safe_bool(bad_causal_hypothesis),
        wrong_owner_priority=_safe_bool(wrong_owner_priority),
        overconfidence_detected=_safe_bool(overconfidence_detected),
        underconfidence_detected=_safe_bool(underconfidence_detected),
        recommendation_taken=_safe_text(recommendation_taken),
        owner_action_taken=_safe_text(owner_action_taken),
        action_authority_used=_safe_bool(action_authority_used),
        resulting_effect=_safe_text(resulting_effect),
        corrective_lesson=_safe_text(corrective_lesson),
        recommended_model_update=_safe_text(recommended_model_update),
        behavior_pack_candidate=_safe_text(behavior_pack_candidate),
        requires_owner_review=_safe_bool(requires_owner_review),
        runtime_authority=_safe_bool(runtime_authority),
        writes_state=_safe_bool(writes_state),
        model_provider_used=_safe_bool(model_provider_used),
        public_claim_allowed=_safe_bool(public_claim_allowed),
        learning_claimed=_safe_bool(learning_claimed),
        safe_metadata={**dict(safe_metadata or {}), **dict(extra_metadata)},
    )
    validate_forecast_error_record_v1(record)
    return record


def validate_forecast_error_record_v1(record: Any) -> bool:
    original = record if isinstance(record, Mapping) else asdict(record) if is_dataclass(record) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    normalized = _record_like(record)
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.outcome_match_status not in ALLOWED_OUTCOME_MATCH_STATUSES_V1:
        raise ValidationError("unknown_outcome_match_status")
    if normalized.error_type not in ALLOWED_ERROR_TYPES_V1:
        raise ValidationError("unknown_error_type")
    if normalized.error_severity not in ALLOWED_SEVERITIES_V1:
        raise ValidationError("unknown_severity")
    if normalized.domain not in ALLOWED_DOMAINS_V1:
        raise ValidationError("unknown_domain")
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
    if normalized.action_authority_used:
        raise ValidationError("action_authority_used_must_be_false")
    if normalized.safe_metadata and _contains_forbidden_claim_marker(normalized.safe_metadata):
        raise ValidationError("forbidden_claim_marker_detected")
    return True


def summarize_forecast_error_record_v1(record: Any) -> ForecastErrorRecordSummary:
    normalized = _record_like(record)
    validate_forecast_error_record_v1(normalized)
    return ForecastErrorRecordSummary(
        summary_type=RECORD_TYPE_V1,
        forecast_error_record_id=normalized.forecast_error_record_id,
        source_forecast_id=normalized.source_forecast_id,
        subject=normalized.subject,
        domain=normalized.domain,
        outcome_match_status=_outcome_from_record(normalized),
        error_type=_error_type_from_record(normalized),
        error_severity=_severity_from_record(normalized),
        confidence_before=normalized.confidence_before,
        confidence_after=normalized.confidence_after,
        stale_signal_count=len(normalized.stale_signals),
        missing_signal_count=len(normalized.missing_signals),
        conflicting_signal_count=len(normalized.conflicting_signals),
        behavior_pack_candidate=normalized.behavior_pack_candidate,
        requires_owner_review=normalized.requires_owner_review,
    )


def build_forecast_error_ledger_v1(
    *,
    records: Iterable[Any],
    forecast_error_ledger_id: str = "forecast_error_ledger_v1",
    ledger_version: str = "v1",
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> ForecastErrorLedger:
    items = [_record_like(item) for item in records]
    for item in items:
        validate_forecast_error_record_v1(item)
    domain_counts: dict[str, int] = {}
    error_type_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    repeated: dict[str, int] = {}
    owner_review_required_records: list[str] = []
    behavior_pack_candidates: list[str] = []
    recommended_next_lanes: list[str] = []
    for record in items:
        domain_counts[record.domain] = domain_counts.get(record.domain, 0) + 1
        error_type = _error_type_from_record(record)
        error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        severity = _severity_from_record(record)
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        pattern = f"{error_type}:{record.domain}:{record.subject}"
        repeated[pattern] = repeated.get(pattern, 0) + 1
        if record.requires_owner_review:
            owner_review_required_records.append(record.forecast_error_record_id)
        if record.behavior_pack_candidate:
            behavior_pack_candidates.append(record.behavior_pack_candidate)
        lane = _next_lane_from_error_type(error_type)
        if lane:
            recommended_next_lanes.append(lane)
    repeated_error_patterns = [f"{pattern} x{count}" for pattern, count in sorted(repeated.items()) if count > 1]
    return ForecastErrorLedger(
        forecast_error_ledger_id=_safe_text(forecast_error_ledger_id),
        ledger_version=_safe_text(ledger_version),
        records=items,
        record_count=len(items),
        domain_counts=dict(sorted(domain_counts.items())),
        error_type_counts=dict(sorted(error_type_counts.items())),
        severity_counts=dict(sorted(severity_counts.items())),
        repeated_error_patterns=repeated_error_patterns,
        owner_review_required_records=sorted(set(owner_review_required_records)),
        behavior_pack_candidates=sorted(set(behavior_pack_candidates)),
        recommended_next_lanes=sorted(set(recommended_next_lanes)),
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        learning_claimed=False,
        safe_metadata={**dict(safe_metadata or {}), **dict(extra_metadata)},
    )


def summarize_forecast_error_ledger_v1(ledger: Any) -> ForecastErrorLedgerSummary:
    normalized = ledger if isinstance(ledger, ForecastErrorLedger) else _ledger_like(ledger)
    validate_forecast_error_ledger_v1(normalized)
    return ForecastErrorLedgerSummary(
        summary_type=LEDGER_TYPE_V1,
        forecast_error_ledger_id=normalized.forecast_error_ledger_id,
        record_count=normalized.record_count,
        domain_counts=dict(normalized.domain_counts),
        error_type_counts=dict(normalized.error_type_counts),
        severity_counts=dict(normalized.severity_counts),
        repeated_error_patterns=list(normalized.repeated_error_patterns),
        owner_review_required_records=list(normalized.owner_review_required_records),
        behavior_pack_candidates=list(normalized.behavior_pack_candidates),
        recommended_next_lanes=list(normalized.recommended_next_lanes),
    )


def _ledger_like(value: Any) -> ForecastErrorLedger:
    if isinstance(value, ForecastErrorLedger):
        return value
    if not isinstance(value, Mapping):
        value = asdict(value) if is_dataclass(value) else {}
    return ForecastErrorLedger(
        forecast_error_ledger_id=_safe_text(value.get("forecast_error_ledger_id")),
        ledger_version=_safe_text(value.get("ledger_version")),
        records=[_record_like(item) for item in value.get("records", [])],
        record_count=int(value.get("record_count", 0) or 0),
        domain_counts={str(k): int(v) for k, v in dict(value.get("domain_counts", {})).items()},
        error_type_counts={str(k): int(v) for k, v in dict(value.get("error_type_counts", {})).items()},
        severity_counts={str(k): int(v) for k, v in dict(value.get("severity_counts", {})).items()},
        repeated_error_patterns=_safe_list(value.get("repeated_error_patterns")),
        owner_review_required_records=_safe_list(value.get("owner_review_required_records")),
        behavior_pack_candidates=_safe_list(value.get("behavior_pack_candidates")),
        recommended_next_lanes=_safe_list(value.get("recommended_next_lanes")),
        runtime_authority=_safe_bool(value.get("runtime_authority")),
        writes_state=_safe_bool(value.get("writes_state")),
        model_provider_used=_safe_bool(value.get("model_provider_used")),
        public_claim_allowed=_safe_bool(value.get("public_claim_allowed")),
        learning_claimed=_safe_bool(value.get("learning_claimed")),
        safe_metadata=dict(value.get("safe_metadata") or {}),
    )


def validate_forecast_error_ledger_v1(ledger: Any) -> bool:
    original = ledger if isinstance(ledger, Mapping) else asdict(ledger) if is_dataclass(ledger) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    normalized = _ledger_like(ledger)
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
    if normalized.record_count != len(normalized.records):
        raise ValidationError("record_count_mismatch")
    for record in normalized.records:
        validate_forecast_error_record_v1(record)
    if normalized.safe_metadata and _contains_forbidden_claim_marker(normalized.safe_metadata):
        raise ValidationError("forbidden_claim_marker_detected")
    return True


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------


def build_initial_forecast_error_examples_v1() -> list[ForecastErrorRecord]:
    return [
        build_forecast_error_record_v1(
            forecast_error_record_id="pv_surplus_missed_stale_weather_v1",
            source_forecast_id="pv_forecast_1",
            source_scenario_simulation_id="scenario_1",
            source_energy_intelligence_id="energy_intelligence_1",
            subject="pv_surplus_missed_stale_weather",
            domain="energy_home_forecast",
            forecast_horizon="2h",
            created_timestamp="2026-06-01T20:00:00+02:00",
            observation_timestamp="2026-06-01T22:00:00+02:00",
            expected_outcome="high_pv_surplus",
            observed_outcome="low_pv_output",
            outcome_match_status="missed",
            error_type="stale_signal",
            error_severity="major",
            confidence_before=0.84,
            confidence_after=0.31,
            assumptions_used=["weather fresh enough"],
            assumptions_failed=["weather fresh enough"],
            signals_used=["weather_forecast_location_scoped"],
            stale_signals=["weather_forecast_location_scoped"],
            resulting_effect="missed surplus window",
            corrective_lesson="refresh weather before PV recommendation",
            recommended_model_update="require fresh weather before immediate PV calls",
            behavior_pack_candidate="refresh_signal_freshness_pack",
            requires_owner_review=False,
        ),
        build_forecast_error_record_v1(
            forecast_error_record_id="battery_reserve_wrong_soc_source_v1",
            source_forecast_id="soc_forecast_1",
            source_scenario_simulation_id="scenario_2",
            source_energy_intelligence_id="energy_intelligence_2",
            subject="battery_reserve_wrong_soc_source",
            domain="energy_home_forecast",
            forecast_horizon="30m",
            created_timestamp="2026-06-01T20:00:00+02:00",
            observation_timestamp="2026-06-01T20:20:00+02:00",
            expected_outcome="battery reserve adequate",
            observed_outcome="battery reserve low",
            outcome_match_status="missed",
            error_type="wrong_signal",
            error_severity="major",
            confidence_before=0.91,
            confidence_after=0.18,
            assumptions_used=["home assistant soc source is authoritative"],
            assumptions_failed=["home assistant soc source is authoritative"],
            signals_used=["battery_soc_home_assistant_fresh", "battery_soc_source_conflict"],
            conflicting_signals=["battery_soc_source_conflict"],
            resulting_effect="bad reserve recommendation",
            corrective_lesson="verify inverter source before reserve decisions",
            recommended_model_update="prefer verified inverter source when conflict exists",
            behavior_pack_candidate="signal_selection_review_pack",
            requires_owner_review=True,
        ),
        build_forecast_error_record_v1(
            forecast_error_record_id="heat_pump_preheat_wrong_missing_comfort_priority_v1",
            source_forecast_id="heat_pump_forecast_1",
            source_scenario_simulation_id="scenario_3",
            source_energy_intelligence_id="energy_intelligence_3",
            subject="heat_pump_preheat_wrong_missing_comfort_priority",
            domain="energy_home_forecast",
            forecast_horizon="3h",
            created_timestamp="2026-06-01T20:00:00+02:00",
            observation_timestamp="2026-06-01T23:00:00+02:00",
            expected_outcome="comfort maintained",
            observed_outcome="comfort below band",
            outcome_match_status="opposite_outcome",
            error_type="wrong_owner_priority",
            error_severity="major",
            confidence_before=0.77,
            confidence_after=0.42,
            assumptions_used=["price goal outranks comfort"],
            assumptions_failed=["comfort priority missing"],
            signals_used=["heat_pump_comfort_signal", "electricity_price_day_ahead_recent"],
            wrong_owner_priority=True,
            resulting_effect="comfort sacrificed",
            corrective_lesson="comfort band must outrank price",
            recommended_model_update="make comfort constraints explicit",
            behavior_pack_candidate="owner_priority_alignment_pack",
            requires_owner_review=True,
        ),
        build_forecast_error_record_v1(
            forecast_error_record_id="ev_charging_wrong_departure_changed_v1",
            source_forecast_id="ev_forecast_1",
            source_scenario_simulation_id="scenario_4",
            source_energy_intelligence_id="energy_intelligence_4",
            subject="ev_charging_wrong_departure_changed",
            domain="scenario_simulation",
            forecast_horizon="4h",
            created_timestamp="2026-06-01T20:00:00+02:00",
            observation_timestamp="2026-06-01T22:00:00+02:00",
            expected_outcome="ev charged before departure",
            observed_outcome="ev departed undercharged",
            outcome_match_status="missed",
            error_type="wrong_assumption",
            error_severity="critical",
            confidence_before=0.88,
            confidence_after=0.12,
            assumptions_used=["departure time stable"],
            assumptions_failed=["departure time changed"],
            signals_used=["electricity_price_day_ahead_recent"],
            resulting_effect="missed departure target",
            corrective_lesson="track departure changes as an invalidation trigger",
            recommended_model_update="treat departure shift as mandatory replan trigger",
            behavior_pack_candidate="invalidation_trigger_pack",
            requires_owner_review=True,
        ),
        build_forecast_error_record_v1(
            forecast_error_record_id="carbon_recommendation_wrong_grid_zone_unresolved_v1",
            source_forecast_id="carbon_forecast_1",
            source_scenario_simulation_id="scenario_5",
            source_energy_intelligence_id="energy_intelligence_5",
            subject="carbon_recommendation_wrong_grid_zone_unresolved",
            domain="grid_signal_forecast",
            forecast_horizon="1h",
            created_timestamp="2026-06-01T20:00:00+02:00",
            observation_timestamp="2026-06-01T20:30:00+02:00",
            expected_outcome="lower carbon window",
            observed_outcome="higher carbon window",
            outcome_match_status="missed",
            error_type="wrong_region_or_grid_zone",
            error_severity="major",
            confidence_before=0.79,
            confidence_after=0.22,
            assumptions_used=["grid zone mapping correct"],
            assumptions_failed=["grid zone mapping correct"],
            signals_used=["carbon_intensity_grid_zone_recent"],
            wrong_region_or_grid_zone=True,
            resulting_effect="wrong region basis",
            corrective_lesson="normalize grid zone before recommendation",
            recommended_model_update="require verified grid-zone mapping",
            behavior_pack_candidate="region_normalization_pack",
            requires_owner_review=False,
        ),
        build_forecast_error_record_v1(
            forecast_error_record_id="price_recommendation_partially_matched_comfort_priority_v1",
            source_forecast_id="price_forecast_1",
            source_scenario_simulation_id="scenario_6",
            source_energy_intelligence_id="energy_intelligence_6",
            subject="price_recommendation_partially_matched_comfort_priority",
            domain="energy_home_forecast",
            forecast_horizon="6h",
            created_timestamp="2026-06-01T20:00:00+02:00",
            observation_timestamp="2026-06-01T26:00:00+02:00",
            expected_outcome="price savings with comfort preserved",
            observed_outcome="price savings, slightly reduced comfort",
            outcome_match_status="partially_matched",
            error_type="underconfidence",
            error_severity="moderate",
            confidence_before=0.45,
            confidence_after=0.66,
            assumptions_used=["comfort margin is large"],
            assumptions_failed=[],
            signals_used=["electricity_price_day_ahead_recent"],
            underconfidence_detected=True,
            resulting_effect="conservative recommendation",
            corrective_lesson="raise confidence when evidence is consistent",
            recommended_model_update="allow more decisive recommendation when signals are aligned",
            behavior_pack_candidate="confidence_calibration_pack",
            requires_owner_review=False,
        ),
        build_forecast_error_record_v1(
            forecast_error_record_id="import_export_macro_signal_overweighted_v1",
            source_forecast_id="grid_forecast_1",
            source_scenario_simulation_id="scenario_7",
            source_energy_intelligence_id="energy_intelligence_7",
            subject="import_export_macro_signal_overweighted",
            domain="grid_signal_forecast",
            forecast_horizon="1d",
            created_timestamp="2026-06-01T20:00:00+02:00",
            observation_timestamp="2026-06-02T20:00:00+02:00",
            expected_outcome="macro grid context only",
            observed_outcome="household action overreacted",
            outcome_match_status="opposite_outcome",
            error_type="wrong_signal",
            error_severity="major",
            confidence_before=0.85,
            confidence_after=0.27,
            assumptions_used=["country import export implies household flow"],
            assumptions_failed=["macro context is not household truth"],
            signals_used=["import_export_country_macro_context"],
            resulting_effect="overweighted macro signal",
            corrective_lesson="distinguish macro context from household flow",
            recommended_model_update="label macro signals as context only",
            behavior_pack_candidate="signal_selection_review_pack",
            requires_owner_review=True,
        ),
        build_forecast_error_record_v1(
            forecast_error_record_id="good_forecast_matched_fresh_local_signals_v1",
            source_forecast_id="good_forecast_1",
            source_scenario_simulation_id="scenario_8",
            source_energy_intelligence_id="energy_intelligence_8",
            subject="good_forecast_matched_fresh_local_signals",
            domain="energy_home_forecast",
            forecast_horizon="2h",
            created_timestamp="2026-06-01T20:00:00+02:00",
            observation_timestamp="2026-06-01T22:00:00+02:00",
            expected_outcome="local forecast matched",
            observed_outcome="local forecast matched",
            outcome_match_status="matched",
            error_type="unknown_error",
            error_severity="none",
            confidence_before=0.73,
            confidence_after=0.76,
            assumptions_used=["fresh local signals"],
            assumptions_failed=[],
            signals_used=["battery_soc_home_assistant_fresh", "weather_forecast_location_scoped"],
            resulting_effect="forecast confirmed",
            corrective_lesson="fresh local signals can be sufficient",
            recommended_model_update="keep local freshness weighting",
            behavior_pack_candidate="",
            requires_owner_review=False,
        ),
        build_forecast_error_record_v1(
            forecast_error_record_id="next_lane_forecast_wrong_hidden_dependency_v1",
            source_forecast_id="lane_forecast_1",
            source_scenario_simulation_id="scenario_9",
            source_energy_intelligence_id="energy_intelligence_9",
            subject="next_lane_forecast_wrong_hidden_dependency",
            domain="weslr_project_forecast",
            forecast_horizon="1w",
            created_timestamp="2026-06-01T20:00:00+02:00",
            observation_timestamp="2026-06-08T20:00:00+02:00",
            expected_outcome="next lane clear",
            observed_outcome="next lane blocked",
            outcome_match_status="missed",
            error_type="scenario_branch_missing",
            error_severity="major",
            confidence_before=0.82,
            confidence_after=0.29,
            assumptions_used=["dependency visible"],
            assumptions_failed=["hidden dependency existed"],
            signals_used=["forecast_error_ledger", "capability_maturity_registry"],
            resulting_effect="hidden dependency missed",
            corrective_lesson="branch on hidden dependency risk",
            recommended_model_update="surface hidden dependencies as explicit branch points",
            behavior_pack_candidate="conflict_branching_pack",
            requires_owner_review=True,
        ),
        build_forecast_error_record_v1(
            forecast_error_record_id="public_readiness_forecast_correctly_blocked_v1",
            source_forecast_id="public_forecast_1",
            source_scenario_simulation_id="scenario_10",
            source_energy_intelligence_id="energy_intelligence_10",
            subject="public_readiness_forecast_correctly_blocked",
            domain="product_market_forecast",
            forecast_horizon="1m",
            created_timestamp="2026-06-01T20:00:00+02:00",
            observation_timestamp="2026-06-02T20:00:00+02:00",
            expected_outcome="public readiness blocked",
            observed_outcome="public readiness blocked",
            outcome_match_status="blocked_no_observation",
            error_type="invalidation_trigger_missed",
            error_severity="minor",
            confidence_before=0.61,
            confidence_after=0.61,
            assumptions_used=["public readiness may be claimable"],
            assumptions_failed=["public readiness must stay blocked"],
            signals_used=["capability_maturity_registry"],
            resulting_effect="correctly blocked",
            corrective_lesson="public readiness claims remain blocked without approval",
            recommended_model_update="keep public-readiness gate locked",
            behavior_pack_candidate="public_claim_lifecycle_review_pack",
            requires_owner_review=True,
        ),
    ]
