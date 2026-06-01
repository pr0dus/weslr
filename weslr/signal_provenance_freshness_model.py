"""Metadata-only signal provenance and source freshness helpers v1.

This module models synthetic signal provenance, freshness, quality, and simple
conflicts. It is pure, deterministic, import-safe, and fail-closed.

It does not ingest real signals. It does not call APIs. It does not connect to
Home Assistant. It does not write memory or `.weslr`. It does not route chat.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Iterable, Mapping

HELPER_TYPE_V1 = "signal_provenance_freshness_model_v1"
RECORD_TYPE_V1 = "signal_provenance_record_v1"
SUMMARY_TYPE_V1 = "signal_provenance_summary_v1"

ALLOWED_FRESHNESS_LABELS_V1 = {
    "fresh",
    "recent",
    "stale",
    "expired",
    "missing_timestamp",
    "future_timestamp",
    "unknown_freshness",
}

ALLOWED_QUALITY_LABELS_V1 = {
    "high_quality",
    "medium_quality",
    "low_quality",
    "stale",
    "missing",
    "conflicting",
    "poison_risk",
    "privacy_limited",
    "wrong_scope",
    "unknown_quality",
}

ALLOWED_SOURCE_CLASSES_V1 = {
    "home_assistant_entity",
    "inverter_or_battery_api",
    "ev_charger_api",
    "heat_pump_api",
    "electricity_price_provider",
    "grid_carbon_provider",
    "import_export_flow_provider",
    "weather_provider",
    "grid_operator_public_data",
    "repo_commit_metadata",
    "validation_result",
    "artifact_provenance",
    "memory_retrieval_result",
    "manual_owner_signal",
    "external_document_signal",
    "unknown_source",
}

ALLOWED_CONFLICT_TYPES_V1 = {
    "no_conflict",
    "value_conflict",
    "timestamp_conflict",
    "unit_conflict",
    "region_conflict",
    "source_disagreement",
    "semantic_conflict",
    "privacy_conflict",
    "authority_conflict",
    "unknown_conflict",
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
    "runtime authority",
    "public claim",
    "learning claim",
    "write to .weslr",
    ".weslr write",
)

DEFAULT_RETRIEVAL_TIMESTAMP_V1 = "2026-06-01T20:00:00+02:00"
DEFAULT_REPORTED_TIMESTAMP_V1 = "2026-06-01T19:58:00+02:00"
DEFAULT_TIMEZONE_V1 = "Europe/Berlin"
DEFAULT_REGION_V1 = "de"
DEFAULT_COUNTRY_V1 = "DE"
DEFAULT_GRID_ZONE_V1 = "de-lu"
DEFAULT_MARKET_ZONE_V1 = "de-day-ahead"
DEFAULT_UNIT_V1 = "kWh"
DEFAULT_VALUE_TYPE_V1 = "numeric"
DEFAULT_EXPECTED_CADENCE_V1 = "hourly"
DEFAULT_POISON_SHIELD_STATUS_V1 = "clean"
DEFAULT_PRIVACY_V1 = "low"
DEFAULT_SCOPE_V1 = "local"


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SignalProvenanceRecord:
    signal_provenance_id: str
    signal_id: str
    signal_name: str
    signal_class: str
    source_system: str
    source_provider: str
    source_reference: str
    source_url_or_entity_id: str
    source_scope: str
    owner_authorized: bool
    operator_authorized: bool
    retrieval_method: str
    retrieval_timestamp: str
    reported_timestamp: str
    timezone: str
    region: str
    country: str
    grid_zone: str
    market_zone: str
    unit: str
    value_type: str
    expected_update_cadence: str
    freshness_status: str
    quality_status: str
    poison_shield_status: str
    privacy_sensitivity: str
    control_capable: bool
    forecasting_allowed: bool
    scenario_simulation_allowed: bool
    memory_write_allowed: bool
    action_authority_granted: bool
    conflict_status: str
    normalization_status: str
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SignalProvenanceSummary:
    summary_type: str
    signal_provenance_id: str
    signal_id: str
    signal_name: str
    freshness_status: str
    quality_status: str
    conflict_status: str
    signal_class: str
    source_scope: str
    unit: str
    region: str
    country: str
    grid_zone: str
    market_zone: str
    control_capable: bool
    forecasting_allowed: bool
    scenario_simulation_allowed: bool
    memory_write_allowed: bool
    action_authority_granted: bool


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


def to_signal_provenance_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def _collect_strings(value: Any) -> list[str]:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        strings: list[str] = []
        for key, item in value.items():
            strings.extend(_collect_strings(key))
            strings.extend(_collect_strings(item))
        return strings
    if isinstance(value, (list, tuple, set)):
        strings: list[str] = []
        for item in value:
            strings.extend(_collect_strings(item))
        return strings
    text = _safe_text(value)
    return [text] if text else []


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
    for text in _collect_strings(value):
        blob = _normalize_text(text)
        if any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1):
            return True
    return False


def _parse_dt(value: str) -> datetime | None:
    text = _safe_text(value)
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _age_for_record(record: Any) -> timedelta | None:
    retrieval = _parse_dt(getattr(record, "retrieval_timestamp", ""))
    reported = _parse_dt(getattr(record, "reported_timestamp", ""))
    if retrieval is None or reported is None:
        return None
    return retrieval - reported


def _cadence_bucket(cadence: str) -> str:
    text = _normalize_text(cadence)
    if any(token in text for token in ("second", "minute", "near-real-time", "realtime", "real-time")):
        return "fast"
    if any(token in text for token in ("hour", "day-ahead", "daily", "hourly")):
        return "hourly"
    if any(token in text for token in ("event", "context", "manual", "owner")):
        return "context"
    return "unknown"


def _freshness_from_age(age: timedelta | None, cadence: str) -> str:
    if age is None:
        return "missing_timestamp"
    if age.total_seconds() < -60:
        return "future_timestamp"
    bucket = _cadence_bucket(cadence)
    age_seconds = age.total_seconds()
    if bucket == "fast":
        if age_seconds <= 5 * 60:
            return "fresh"
        if age_seconds <= 60 * 60:
            return "recent"
        if age_seconds <= 4 * 60 * 60:
            return "stale"
        return "expired"
    if bucket == "hourly":
        if age_seconds <= 60 * 60:
            return "fresh"
        if age_seconds <= 6 * 60 * 60:
            return "recent"
        if age_seconds <= 24 * 60 * 60:
            return "stale"
        return "expired"
    if bucket == "context":
        if age_seconds <= 24 * 60 * 60:
            return "fresh"
        if age_seconds <= 3 * 24 * 60 * 60:
            return "recent"
        if age_seconds <= 7 * 24 * 60 * 60:
            return "stale"
        return "expired"
    return "unknown_freshness"


def _quality_from_record(record: Any, freshness_status: str, conflict_status: str) -> str:
    if freshness_status == "missing_timestamp":
        return "missing"
    if freshness_status in {"stale", "expired"}:
        return "stale"
    if freshness_status == "future_timestamp":
        return "low_quality"
    if conflict_status != "no_conflict":
        if conflict_status in {"privacy_conflict", "authority_conflict"}:
            return "privacy_limited" if conflict_status == "privacy_conflict" else "wrong_scope"
        return "conflicting"
    poison = _normalize_text(getattr(record, "poison_shield_status", ""))
    if poison and any(token in poison for token in ("blocked", "quarantine", "poison", "hostile", "unsafe")):
        return "poison_risk"
    if _normalize_text(getattr(record, "privacy_sensitivity", "")) in {"high", "very_high", "sensitive", "private"}:
        return "privacy_limited"
    unit = _safe_text(getattr(record, "unit", ""))
    region = _safe_text(getattr(record, "region", ""))
    country = _safe_text(getattr(record, "country", ""))
    grid_zone = _safe_text(getattr(record, "grid_zone", ""))
    if not unit or unit == "unknown":
        return "low_quality"
    if not region and not country and not grid_zone:
        return "wrong_scope"
    if region == "unknown" or country == "unknown" or grid_zone == "unknown":
        return "medium_quality"
    if _safe_text(getattr(record, "signal_class", "")) == "external_document_signal":
        return "privacy_limited"
    return "high_quality"


def _normalization_status(record: Any) -> str:
    unit = _safe_text(getattr(record, "unit", ""))
    region = _safe_text(getattr(record, "region", ""))
    country = _safe_text(getattr(record, "country", ""))
    grid_zone = _safe_text(getattr(record, "grid_zone", ""))
    if unit and region and country and grid_zone:
        return "normalized"
    if unit or region or country or grid_zone:
        return "partial"
    return "unknown"


def _safe_metadata_copy(value: Mapping[str, Any] | None, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if value:
        payload.update(dict(value))
    if extra:
        payload.update(dict(extra))
    return payload


def _record_like(value: Any) -> SignalProvenanceRecord:
    if isinstance(value, SignalProvenanceRecord):
        return value
    if not isinstance(value, Mapping):
        value = asdict(value) if is_dataclass(value) else {}
    safe_metadata = value.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
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
        safe_metadata=dict(safe_metadata or {}),
    )


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------


def evaluate_signal_freshness_v1(record: Any) -> str:
    normalized = _record_like(record)
    freshness = _freshness_from_age(_age_for_record(normalized), normalized.expected_update_cadence)
    if freshness not in ALLOWED_FRESHNESS_LABELS_V1:
        return "unknown_freshness"
    return freshness


def detect_signal_conflict_v1(records: Iterable[Any]) -> str:
    items = [_record_like(item) for item in records]
    if len(items) < 2:
        return "no_conflict"

    first = items[0]
    if any(_safe_text(item.signal_id) != first.signal_id for item in items[1:]):
        return "semantic_conflict"

    values = [_safe_text(item.safe_metadata.get("signal_value") if item.safe_metadata else "") for item in items]
    if len({value for value in values if value}) > 1:
        return "value_conflict"

    retrievals = [_safe_text(item.retrieval_timestamp) for item in items]
    reported = [_safe_text(item.reported_timestamp) for item in items]
    if len(set(retrievals)) > 1 or len(set(reported)) > 1:
        return "timestamp_conflict"

    units = {_safe_text(item.unit) for item in items if _safe_text(item.unit)}
    if len(units) > 1:
        return "unit_conflict"

    regions = {(_safe_text(item.region), _safe_text(item.country), _safe_text(item.grid_zone), _safe_text(item.market_zone)) for item in items}
    if len(regions) > 1:
        return "region_conflict"

    sources = {(_safe_text(item.signal_class), _safe_text(item.source_system), _safe_text(item.source_provider), _safe_text(item.source_reference)) for item in items}
    if len(sources) > 1:
        return "source_disagreement"

    authorities = {(item.owner_authorized, item.operator_authorized, item.action_authority_granted) for item in items}
    if len(authorities) > 1:
        return "authority_conflict"

    privacy = {_safe_text(item.privacy_sensitivity) for item in items}
    if len(privacy) > 1 and any(level in {"high", "very_high", "private"} for level in privacy):
        return "privacy_conflict"

    names = {_safe_text(item.signal_name) for item in items}
    types = {_safe_text(item.value_type) for item in items}
    if len(names) > 1 or len(types) > 1:
        return "semantic_conflict"

    return "no_conflict"


def evaluate_signal_quality_v1(record: Any) -> str:
    normalized = _record_like(record)
    freshness = normalized.freshness_status or evaluate_signal_freshness_v1(normalized)
    conflict = normalized.conflict_status or "no_conflict"
    if freshness == "unknown_freshness":
        return "unknown_quality"
    return _quality_from_record(normalized, freshness, conflict)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_signal_provenance_record_v1(
    *,
    signal_provenance_id: str,
    signal_id: str,
    signal_name: str,
    signal_class: str,
    source_system: str,
    source_provider: str,
    source_reference: str,
    source_url_or_entity_id: str,
    source_scope: str = DEFAULT_SCOPE_V1,
    owner_authorized: bool = False,
    operator_authorized: bool = False,
    retrieval_method: str = "synthetic_in_memory",
    retrieval_timestamp: str = DEFAULT_RETRIEVAL_TIMESTAMP_V1,
    reported_timestamp: str = DEFAULT_REPORTED_TIMESTAMP_V1,
    timezone: str = DEFAULT_TIMEZONE_V1,
    region: str = DEFAULT_REGION_V1,
    country: str = DEFAULT_COUNTRY_V1,
    grid_zone: str = DEFAULT_GRID_ZONE_V1,
    market_zone: str = DEFAULT_MARKET_ZONE_V1,
    unit: str = DEFAULT_UNIT_V1,
    value_type: str = DEFAULT_VALUE_TYPE_V1,
    expected_update_cadence: str = DEFAULT_EXPECTED_CADENCE_V1,
    freshness_status: str | None = None,
    quality_status: str | None = None,
    poison_shield_status: str = DEFAULT_POISON_SHIELD_STATUS_V1,
    privacy_sensitivity: str = DEFAULT_PRIVACY_V1,
    control_capable: bool = False,
    forecasting_allowed: bool = True,
    scenario_simulation_allowed: bool = True,
    memory_write_allowed: bool = False,
    action_authority_granted: bool = False,
    conflict_status: str | None = None,
    normalization_status: str | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
    **extra_metadata: Any,
) -> SignalProvenanceRecord:
    provisional = SignalProvenanceRecord(
        signal_provenance_id=_safe_text(signal_provenance_id),
        signal_id=_safe_text(signal_id),
        signal_name=_safe_text(signal_name),
        signal_class=_safe_text(signal_class),
        source_system=_safe_text(source_system),
        source_provider=_safe_text(source_provider),
        source_reference=_safe_text(source_reference),
        source_url_or_entity_id=_safe_text(source_url_or_entity_id),
        source_scope=_safe_text(source_scope),
        owner_authorized=_safe_bool(owner_authorized),
        operator_authorized=_safe_bool(operator_authorized),
        retrieval_method=_safe_text(retrieval_method),
        retrieval_timestamp=_safe_text(retrieval_timestamp),
        reported_timestamp=_safe_text(reported_timestamp),
        timezone=_safe_text(timezone),
        region=_safe_text(region),
        country=_safe_text(country),
        grid_zone=_safe_text(grid_zone),
        market_zone=_safe_text(market_zone),
        unit=_safe_text(unit),
        value_type=_safe_text(value_type),
        expected_update_cadence=_safe_text(expected_update_cadence),
        freshness_status=_safe_text(freshness_status or ""),
        quality_status=_safe_text(quality_status or ""),
        poison_shield_status=_safe_text(poison_shield_status),
        privacy_sensitivity=_safe_text(privacy_sensitivity),
        control_capable=_safe_bool(control_capable),
        forecasting_allowed=_safe_bool(forecasting_allowed),
        scenario_simulation_allowed=_safe_bool(scenario_simulation_allowed),
        memory_write_allowed=_safe_bool(memory_write_allowed),
        action_authority_granted=_safe_bool(action_authority_granted),
        conflict_status=_safe_text(conflict_status or ""),
        normalization_status=_safe_text(normalization_status or ""),
        safe_metadata=_safe_metadata_copy(safe_metadata, extra_metadata),
    )
    freshness = freshness_status or evaluate_signal_freshness_v1(provisional)
    conflict = conflict_status or "no_conflict"
    quality = quality_status or _quality_from_record(provisional, freshness, conflict)
    normalization = normalization_status or _normalization_status(provisional)
    record = SignalProvenanceRecord(
        **{**asdict(provisional), "freshness_status": freshness, "quality_status": quality, "conflict_status": conflict, "normalization_status": normalization}
    )
    validate_signal_provenance_record_v1(record)
    return record


def build_initial_signal_provenance_examples_v1() -> list[SignalProvenanceRecord]:
    return [
        build_signal_provenance_record_v1(
            signal_provenance_id="battery_soc_home_assistant_fresh_v1",
            signal_id="battery_soc_home_assistant_fresh",
            signal_name="Battery SoC Home Assistant Fresh",
            signal_class="home_assistant_entity",
            source_system="home_assistant",
            source_provider="local_entity",
            source_reference="sensor.home_battery_soc",
            source_url_or_entity_id="sensor.home_battery_soc",
            source_scope="local_home",
            owner_authorized=True,
            operator_authorized=True,
            retrieval_method="entity_read",
            retrieval_timestamp="2026-06-01T20:00:00+02:00",
            reported_timestamp="2026-06-01T19:59:15+02:00",
            timezone="Europe/Berlin",
            region="de-by",
            country="DE",
            grid_zone="de-lu",
            market_zone="de-day-ahead",
            unit="%",
            value_type="numeric",
            expected_update_cadence="minutes",
            poison_shield_status="clean",
            privacy_sensitivity="low",
            control_capable=True,
            forecasting_allowed=True,
            scenario_simulation_allowed=True,
            safe_metadata={"signal_value": 62},
        ),
        build_signal_provenance_record_v1(
            signal_provenance_id="electricity_price_day_ahead_recent_v1",
            signal_id="electricity_price_day_ahead_recent",
            signal_name="Electricity Price Day Ahead Recent",
            signal_class="electricity_price_provider",
            source_system="price_api",
            source_provider="market_operator",
            source_reference="day-ahead-2026-06-01",
            source_url_or_entity_id="de-day-ahead",
            source_scope="market_zone",
            owner_authorized=False,
            operator_authorized=False,
            retrieval_method="api_poll",
            retrieval_timestamp="2026-06-01T20:00:00+02:00",
            reported_timestamp="2026-06-01T18:30:00+02:00",
            timezone="Europe/Berlin",
            region="de",
            country="DE",
            grid_zone="de-lu",
            market_zone="de-day-ahead",
            unit="EUR/kWh",
            value_type="numeric",
            expected_update_cadence="day-ahead hourly",
            poison_shield_status="clean",
            privacy_sensitivity="low",
            control_capable=False,
            forecasting_allowed=True,
            scenario_simulation_allowed=True,
            safe_metadata={"signal_value": 0.31},
        ),
        build_signal_provenance_record_v1(
            signal_provenance_id="carbon_intensity_grid_zone_recent_v1",
            signal_id="carbon_intensity_grid_zone_recent",
            signal_name="Carbon Intensity Grid Zone Recent",
            signal_class="grid_carbon_provider",
            source_system="carbon_api",
            source_provider="grid_operator",
            source_reference="de-lu-carbon",
            source_url_or_entity_id="grid-zone:de-lu",
            source_scope="grid_zone",
            owner_authorized=False,
            operator_authorized=False,
            retrieval_method="api_poll",
            retrieval_timestamp="2026-06-01T20:00:00+02:00",
            reported_timestamp="2026-06-01T19:20:00+02:00",
            timezone="Europe/Berlin",
            region="de",
            country="DE",
            grid_zone="de-lu",
            market_zone="de-lu",
            unit="gCO2/kWh",
            value_type="numeric",
            expected_update_cadence="hourly",
            poison_shield_status="clean",
            privacy_sensitivity="low",
            control_capable=False,
            forecasting_allowed=True,
            scenario_simulation_allowed=True,
            safe_metadata={"signal_value": 248},
        ),
        build_signal_provenance_record_v1(
            signal_provenance_id="import_export_country_macro_context_v1",
            signal_id="import_export_country_macro_context",
            signal_name="Import Export Country Macro Context",
            signal_class="import_export_flow_provider",
            source_system="grid_context_api",
            source_provider="national_operator",
            source_reference="de-import-export",
            source_url_or_entity_id="country:de",
            source_scope="country_macro",
            owner_authorized=False,
            operator_authorized=False,
            retrieval_method="api_poll",
            retrieval_timestamp="2026-06-01T20:00:00+02:00",
            reported_timestamp="2026-06-01T19:55:00+02:00",
            timezone="Europe/Berlin",
            region="de",
            country="DE",
            grid_zone="de",
            market_zone="de",
            unit="MW",
            value_type="numeric",
            expected_update_cadence="hourly",
            poison_shield_status="clean",
            privacy_sensitivity="low",
            control_capable=False,
            forecasting_allowed=True,
            scenario_simulation_allowed=True,
            safe_metadata={"signal_value": -420},
        ),
        build_signal_provenance_record_v1(
            signal_provenance_id="weather_forecast_location_scoped_v1",
            signal_id="weather_forecast_location_scoped",
            signal_name="Weather Forecast Location Scoped",
            signal_class="weather_provider",
            source_system="weather_api",
            source_provider="forecast_service",
            source_reference="weather-berlin-2026-06-01",
            source_url_or_entity_id="lat:52.52,lon:13.405",
            source_scope="location_scoped",
            owner_authorized=False,
            operator_authorized=False,
            retrieval_method="api_poll",
            retrieval_timestamp="2026-06-01T20:00:00+02:00",
            reported_timestamp="2026-06-01T19:40:00+02:00",
            timezone="Europe/Berlin",
            region="de-be",
            country="DE",
            grid_zone="de-lu",
            market_zone="de-lu",
            unit="°C",
            value_type="numeric",
            expected_update_cadence="hourly daily",
            poison_shield_status="clean",
            privacy_sensitivity="low",
            control_capable=False,
            forecasting_allowed=True,
            scenario_simulation_allowed=True,
            safe_metadata={"signal_value": 18.3},
        ),
        build_signal_provenance_record_v1(
            signal_provenance_id="pv_forecast_weather_conflict_v1",
            signal_id="pv_forecast_weather_conflict",
            signal_name="PV Forecast Weather Conflict",
            signal_class="weather_provider",
            source_system="weather_api",
            source_provider="forecast_service",
            source_reference="weather-cloud-cover-high",
            source_url_or_entity_id="lat:52.52,lon:13.405",
            source_scope="location_scoped",
            owner_authorized=False,
            operator_authorized=False,
            retrieval_method="synthetic_in_memory",
            retrieval_timestamp="2026-06-01T20:00:00+02:00",
            reported_timestamp="2026-06-01T19:30:00+02:00",
            timezone="Europe/Berlin",
            region="de-be",
            country="DE",
            grid_zone="de-lu",
            market_zone="de-lu",
            unit="%",
            value_type="numeric",
            expected_update_cadence="hourly",
            poison_shield_status="clean",
            privacy_sensitivity="low",
            control_capable=False,
            forecasting_allowed=True,
            scenario_simulation_allowed=True,
            conflict_status="source_disagreement",
            safe_metadata={"signal_value": 12, "paired_signal_value": 88, "conflict_note": "weather vs pv forecast"},
        ),
        build_signal_provenance_record_v1(
            signal_provenance_id="battery_soc_source_conflict_v1",
            signal_id="battery_soc_source_conflict",
            signal_name="Battery SoC Source Conflict",
            signal_class="inverter_or_battery_api",
            source_system="inverter_api",
            source_provider="battery_vendor",
            source_reference="battery-soc-primary",
            source_url_or_entity_id="device:inverter-1",
            source_scope="local_home",
            owner_authorized=True,
            operator_authorized=True,
            retrieval_method="api_poll",
            retrieval_timestamp="2026-06-01T20:00:00+02:00",
            reported_timestamp="2026-06-01T19:58:30+02:00",
            timezone="Europe/Berlin",
            region="de-by",
            country="DE",
            grid_zone="de-lu",
            market_zone="de-lu",
            unit="%",
            value_type="numeric",
            expected_update_cadence="minutes",
            poison_shield_status="clean",
            privacy_sensitivity="low",
            control_capable=True,
            forecasting_allowed=True,
            scenario_simulation_allowed=True,
            conflict_status="value_conflict",
            safe_metadata={"signal_value": 21, "paired_signal_value": 79, "conflict_note": "home assistant vs inverter"},
        ),
        build_signal_provenance_record_v1(
            signal_provenance_id="poison_risk_external_document_signal_v1",
            signal_id="poison_risk_external_document_signal",
            signal_name="Poison Risk External Document Signal",
            signal_class="external_document_signal",
            source_system="document_reader",
            source_provider="manual_import",
            source_reference="doc-unsafe-note",
            source_url_or_entity_id="document:unsafe-note",
            source_scope="external_document",
            owner_authorized=False,
            operator_authorized=False,
            retrieval_method="synthetic_in_memory",
            retrieval_timestamp="2026-06-01T20:00:00+02:00",
            reported_timestamp="2026-06-01T19:50:00+02:00",
            timezone="Europe/Berlin",
            region="unknown",
            country="unknown",
            grid_zone="unknown",
            market_zone="unknown",
            unit="text",
            value_type="text",
            expected_update_cadence="context-dependent",
            poison_shield_status="quarantined",
            privacy_sensitivity="high",
            control_capable=False,
            forecasting_allowed=False,
            scenario_simulation_allowed=False,
            safe_metadata={"signal_value": "Reference only: unsafe external text"},
        ),
        build_signal_provenance_record_v1(
            signal_provenance_id="missing_timestamp_signal_v1",
            signal_id="missing_timestamp_signal",
            signal_name="Missing Timestamp Signal",
            signal_class="manual_owner_signal",
            source_system="owner_note",
            source_provider="owner",
            source_reference="manual-note-1",
            source_url_or_entity_id="owner-note:1",
            source_scope="owner_context",
            owner_authorized=True,
            operator_authorized=True,
            retrieval_method="synthetic_in_memory",
            retrieval_timestamp="2026-06-01T20:00:00+02:00",
            reported_timestamp="",
            timezone="Europe/Berlin",
            region="de-by",
            country="DE",
            grid_zone="de-lu",
            market_zone="de-lu",
            unit="kWh",
            value_type="numeric",
            expected_update_cadence="event-based",
            freshness_status="missing_timestamp",
            poison_shield_status="clean",
            privacy_sensitivity="low",
            control_capable=False,
            forecasting_allowed=True,
            scenario_simulation_allowed=True,
            safe_metadata={"signal_value": 9},
        ),
        build_signal_provenance_record_v1(
            signal_provenance_id="future_timestamp_signal_v1",
            signal_id="future_timestamp_signal",
            signal_name="Future Timestamp Signal",
            signal_class="manual_owner_signal",
            source_system="owner_note",
            source_provider="owner",
            source_reference="manual-note-future",
            source_url_or_entity_id="owner-note:future",
            source_scope="owner_context",
            owner_authorized=True,
            operator_authorized=True,
            retrieval_method="synthetic_in_memory",
            retrieval_timestamp="2026-06-01T20:00:00+02:00",
            reported_timestamp="2026-06-01T21:00:00+02:00",
            timezone="Europe/Berlin",
            region="de-by",
            country="DE",
            grid_zone="de-lu",
            market_zone="de-lu",
            unit="kWh",
            value_type="numeric",
            expected_update_cadence="event-based",
            freshness_status="future_timestamp",
            poison_shield_status="clean",
            privacy_sensitivity="low",
            control_capable=False,
            forecasting_allowed=True,
            scenario_simulation_allowed=True,
            safe_metadata={"signal_value": 14},
        ),
    ]


# ---------------------------------------------------------------------------
# Validation and summary
# ---------------------------------------------------------------------------


def validate_signal_provenance_record_v1(record: Any) -> bool:
    original = record if isinstance(record, Mapping) else asdict(record) if is_dataclass(record) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    normalized = _record_like(record)
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.signal_class not in ALLOWED_SOURCE_CLASSES_V1:
        raise ValidationError("unknown_source_class")
    if normalized.freshness_status not in ALLOWED_FRESHNESS_LABELS_V1:
        raise ValidationError("unknown_freshness")
    if normalized.quality_status not in ALLOWED_QUALITY_LABELS_V1:
        raise ValidationError("unknown_quality")
    if normalized.conflict_status not in ALLOWED_CONFLICT_TYPES_V1:
        raise ValidationError("unknown_conflict")
    if normalized.memory_write_allowed:
        raise ValidationError("memory_write_allowed_must_be_false")
    if normalized.action_authority_granted:
        raise ValidationError("action_authority_granted_must_be_false")
    if not normalized.signal_provenance_id:
        raise ValidationError("signal_provenance_id_required")
    if not normalized.signal_id:
        raise ValidationError("signal_id_required")
    if not normalized.signal_name:
        raise ValidationError("signal_name_required")
    if normalized.current_authority if False else False:
        pass
    if normalized.safe_metadata and _contains_forbidden_claim_marker(normalized.safe_metadata):
        raise ValidationError("forbidden_claim_marker_detected")
    return True


def summarize_signal_provenance_record_v1(record: Any) -> SignalProvenanceSummary:
    normalized = _record_like(record)
    validate_signal_provenance_record_v1(normalized)
    return SignalProvenanceSummary(
        summary_type=SUMMARY_TYPE_V1,
        signal_provenance_id=normalized.signal_provenance_id,
        signal_id=normalized.signal_id,
        signal_name=normalized.signal_name,
        freshness_status=normalized.freshness_status,
        quality_status=normalized.quality_status,
        conflict_status=normalized.conflict_status,
        signal_class=normalized.signal_class,
        source_scope=normalized.source_scope,
        unit=normalized.unit,
        region=normalized.region,
        country=normalized.country,
        grid_zone=normalized.grid_zone,
        market_zone=normalized.market_zone,
        control_capable=normalized.control_capable,
        forecasting_allowed=normalized.forecasting_allowed,
        scenario_simulation_allowed=normalized.scenario_simulation_allowed,
        memory_write_allowed=normalized.memory_write_allowed,
        action_authority_granted=normalized.action_authority_granted,
    )
