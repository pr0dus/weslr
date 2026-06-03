"""Metadata-only reaction-time latency budget helper v1.

This module is intentionally pure, deterministic, import-safe, and fail-closed.
It only handles metadata for future latency/reaction-time audit use. It does not
perform runtime measurement, profiling, telemetry, routing, chat/UI wiring,
voice/audio access, provider/model/search calls, or any authority-granting
behavior.
"""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Iterable, Mapping
from typing import Any

HELPER_TYPE_V1 = "reaction_time_latency_budget_helper_v1"
PACKET_SCHEMA_V1 = "reaction_time_latency_budget_audit_packet_v1"
PACKET_VALIDATION_STATUS_VALID_V1 = "valid"
PACKET_VALIDATION_STATUS_INVALID_V1 = "invalid"

SAFE_CASE_SOURCE_CLASSES_V1 = {
    "synthetic_internal_prompt",
    "synthetic_fixture",
    "metadata_only_trace",
    "operator_supplied_nonprivate_metadata",
    "public_open_metadata",
    "unknown_safe_metadata",
}

FORBIDDEN_CASE_SOURCE_CLASSES_V1 = {
    "private_user_chat",
    "live_production_user",
    "microphone_stream",
    "raw_audio",
    "voiceprint",
    "private_file",
    "hidden_prompt",
    "official_benchmark_material",
    "provider_log",
    "customer_data",
    "credential_or_secret",
    "public_claim_dashboard",
    "behavior_pack_promotion_source",
}

LATENCY_CATEGORY_LABELS_V1 = {
    "perceived_reaction_time",
    "first_visible_acknowledgement",
    "local_routing_decision_time",
    "safety_preflight_validation_time",
    "memory_context_lookup_time",
    "evidence_provenance_lookup_time",
    "response_planning_time",
    "first_token_or_first_visible_output_time",
    "streaming_progressive_response_cadence",
    "long_task_acknowledgement_time",
    "background_async_safe_continuation_boundary",
    "operator_approval_wait_boundary",
    "blocked_task_explanation_time",
}

LATENCY_BUDGET_TIER_LABELS_V1 = {
    "tier_0_immediate_acknowledgement_100_200ms",
    "tier_1_first_visible_reaction_under_250ms",
    "tier_2_simple_local_routing_300_500ms",
    "tier_3_short_answer_planning_under_1_2s",
    "tier_4_long_answer_streaming_required",
    "tier_5_blocked_high_risk_fast_safe_explanation",
    "tier_6_operator_governance_wait_no_fake_progress",
}

MEASUREMENT_METHOD_LABELS_V1 = {
    "synthetic_metadata_estimate",
    "manual_operator_observation",
    "controlled_fixture_metadata",
    "future_controlled_runtime_measurement_requires_approval",
}

FORBIDDEN_MEASUREMENT_METHODS_V1 = {
    "live_runtime_instrumentation",
    "production_telemetry",
    "provider_log_analysis",
    "private_chat_timing_extraction",
    "microphone_audio_timing_extraction",
    "hidden_prompt_timing_extraction",
    "official_benchmark_timing_extraction",
    "public_dashboard_timing_extraction",
}

DENIED_AUTHORITY_FIELDS_V1 = {
    "runtime_authority",
    "routing_authority",
    "chat_authority",
    "voice_authority",
    "microphone_authority",
    "audio_processing_authority",
    "measurement_execution_authority",
    "profiling_authority",
    "memory_write_authority",
    "provider_call_authority",
    "search_call_authority",
    "behavior_pack_promotion_authority",
    "benchmark_claim_authority",
    "public_performance_claim_authority",
    "product_readiness_authority",
    "certification_authority",
}

JSON_SCALAR_TYPES_V1 = (str, int, float, bool)
PACKET_FIELD_NAMES_V1 = {
    "schema",
    "case_id",
    "case_source_class",
    "interaction_family",
    "target_latency_band",
    "observed_latency_band",
    "measurement_method",
    "latency_categories",
    "latency_budget_tier",
    "metadata_only",
    "raw_text_stored",
    "private_data_used",
    "audio_used",
    "runtime_path_used",
    "safety_preflight_present",
    "authority_boundary_preserved",
    "blocked_reason",
    "risk_notes",
    "latency_bottleneck_label",
    "improvement_candidate_label",
    "denied_authority",
    "validation_status",
    "validation_errors",
    "internal_only",
    "non_authoritative",
    *DENIED_AUTHORITY_FIELDS_V1,
}

UNSAFE_KEY_VALUE_FRAGMENTS_V1 = {
    "privateuserchat",
    "liveproductionuser",
    "microphone",
    "rawaudio",
    "audio",
    "voiceprint",
    "privatefile",
    "hiddenprompt",
    "officialbenchmark",
    "providerlog",
    "customerdata",
    "credential",
    "secret",
    "publicclaim",
    "publicperformance",
    "benchmarkclaim",
    "productreadiness",
    "certification",
    "runtimeauthority",
    "routingauthority",
    "chatauthority",
    "voiceauthority",
    "measurementexecutionauthority",
    "profilingauthority",
    "behaviorpackpromotion",
}

UNSAFE_URL_SCHEMES_V1 = ("http://", "https://", "ftp://", "file://", "content://")
UNSAFE_FILE_EXTENSIONS_V1 = (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".opus")

__all__ = [
    "HELPER_TYPE_V1",
    "PACKET_SCHEMA_V1",
    "PACKET_VALIDATION_STATUS_VALID_V1",
    "PACKET_VALIDATION_STATUS_INVALID_V1",
    "SAFE_CASE_SOURCE_CLASSES_V1",
    "FORBIDDEN_CASE_SOURCE_CLASSES_V1",
    "LATENCY_CATEGORY_LABELS_V1",
    "LATENCY_BUDGET_TIER_LABELS_V1",
    "MEASUREMENT_METHOD_LABELS_V1",
    "FORBIDDEN_MEASUREMENT_METHODS_V1",
    "DENIED_AUTHORITY_FIELDS_V1",
    "build_reaction_time_latency_budget_packet_v1",
    "validate_reaction_time_latency_budget_packet_v1",
    "summarize_reaction_time_latency_budget_packet_v1",
    "to_reaction_time_latency_budget_json_safe_v1",
    "render_reaction_time_latency_budget_markdown_v1",
    "build_initial_reaction_time_latency_budget_examples_v1",
]


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _normalize_token(value: Any) -> str:
    text = _safe_str(value).lower()
    return "".join(ch for ch in text if ch.isalnum())


def _is_json_safe_scalar(value: Any) -> bool:
    return value is None or isinstance(value, JSON_SCALAR_TYPES_V1)


def _json_safe_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return { _safe_str(key): _json_safe_copy(raw) for key, raw in value.items() }
    if isinstance(value, list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, set):
        return [_json_safe_copy(item) for item in sorted(value, key=lambda item: _safe_str(item))]
    if _is_json_safe_scalar(value):
        return value
    return _safe_str(value)


def _contains_unsafe_reference(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    normalized = _normalize_token(value)
    if lowered.startswith(UNSAFE_URL_SCHEMES_V1):
        return True
    if any(ext in lowered for ext in UNSAFE_FILE_EXTENSIONS_V1):
        return True
    return any(fragment in lowered or fragment in normalized for fragment in UNSAFE_KEY_VALUE_FRAGMENTS_V1)


def _normalize_string_list(
    value: Any,
    field_name: str,
    *,
    allowed_values: set[str] | None = None,
    allow_empty: bool = True,
) -> list[str]:
    if value is None:
        items: Iterable[Any] = []
    elif isinstance(value, (str, bytes, dict)):
        raise ValueError(f"{field_name} must be a real list of safe strings")
    elif isinstance(value, (list, tuple, set)):
        items = value
    else:
        raise ValueError(f"{field_name} must be a real list of safe strings")

    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _safe_str(item)
        if not text:
            raise ValueError(f"{field_name} contains empty value")
        if _contains_unsafe_reference(text):
            raise ValueError(f"{field_name} contains forbidden content")
        if allowed_values is not None and text not in allowed_values:
            raise ValueError(f"{field_name} contains unsafe label")
        if text not in seen:
            out.append(text)
            seen.add(text)

    if not out and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return out


def _normalize_safe_string(value: Any, field_name: str, *, allow_empty: bool = False) -> str:
    text = _safe_str(value)
    if not text and not allow_empty:
        raise ValueError(f"{field_name} must be a non-empty safe string")
    if _contains_unsafe_reference(text):
        raise ValueError(f"{field_name} contains forbidden content")
    return text


def _normalize_denied_authority_map(value: Any) -> dict[str, bool]:
    if value is None:
        return {name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)}
    if not isinstance(value, Mapping):
        raise ValueError("denied_authority must be a mapping")

    out: dict[str, bool] = {}
    for field in sorted(DENIED_AUTHORITY_FIELDS_V1):
        if field not in value:
            raise ValueError(f"missing denied authority field: {field}")
        raw = value[field]
        if not isinstance(raw, bool):
            raise ValueError(f"denied authority field {field} must be boolean false")
        if raw is not False:
            raise ValueError(f"denied authority field {field} must be false")
        out[field] = False

    extra = sorted(set(_safe_str(key) for key in value.keys()) - DENIED_AUTHORITY_FIELDS_V1)
    if extra:
        raise ValueError(f"unexpected denied_authority field(s): {', '.join(extra)}")
    return out


def _canonical_case_id(
    case_source_class: str,
    interaction_family: str,
    target_latency_band: str,
    observed_latency_band: str,
    measurement_method: str,
    latency_categories: list[str],
    latency_budget_tier: str,
) -> str:
    basis = "|".join([
        PACKET_SCHEMA_V1,
        case_source_class,
        interaction_family,
        target_latency_band,
        observed_latency_band,
        measurement_method,
        ",".join(latency_categories),
        latency_budget_tier,
    ])
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]
    return f"rtlb-{digest}"


def build_reaction_time_latency_budget_packet_v1(
    *,
    case_id: str | None = None,
    case_source_class: str,
    interaction_family: str,
    target_latency_band: str,
    observed_latency_band: str,
    measurement_method: str,
    latency_categories: Iterable[Any] | None = None,
    latency_budget_tier: str,
    metadata_only: bool = True,
    raw_text_stored: bool = False,
    private_data_used: bool = False,
    audio_used: bool = False,
    runtime_path_used: bool = False,
    safety_preflight_present: bool = True,
    authority_boundary_preserved: bool = True,
    blocked_reason: Iterable[Any] | None = None,
    risk_notes: Iterable[Any] | None = None,
    latency_bottleneck_label: str = "",
    improvement_candidate_label: str = "",
    denied_authority: Mapping[str, Any] | None = None,
    internal_only: bool = True,
    non_authoritative: bool = True,
    validation_status: str | None = None,
    validation_errors: Iterable[Any] | None = None,
) -> dict[str, Any]:
    source = _normalize_safe_string(case_source_class, "case_source_class")
    if source not in SAFE_CASE_SOURCE_CLASSES_V1:
        raise ValueError("unsafe case_source_class")

    interaction = _normalize_safe_string(interaction_family, "interaction_family")
    target_band = _normalize_safe_string(target_latency_band, "target_latency_band")
    observed_band = _normalize_safe_string(observed_latency_band, "observed_latency_band")
    method = _normalize_safe_string(measurement_method, "measurement_method")
    budget_tier = _normalize_safe_string(latency_budget_tier, "latency_budget_tier")
    if target_band not in LATENCY_BUDGET_TIER_LABELS_V1:
        raise ValueError("unsafe target_latency_band")
    if observed_band not in LATENCY_BUDGET_TIER_LABELS_V1:
        raise ValueError("unsafe observed_latency_band")
    if method not in MEASUREMENT_METHOD_LABELS_V1:
        raise ValueError("unsafe measurement_method")
    if budget_tier not in LATENCY_BUDGET_TIER_LABELS_V1:
        raise ValueError("unsafe latency_budget_tier")

    categories = _normalize_string_list(
        latency_categories or [],
        "latency_categories",
        allowed_values=LATENCY_CATEGORY_LABELS_V1,
        allow_empty=False,
    )

    packet = {
        "schema": PACKET_SCHEMA_V1,
        "case_id": _safe_str(case_id) if case_id is not None else _canonical_case_id(
            source,
            interaction,
            target_band,
            observed_band,
            method,
            categories,
            budget_tier,
        ),
        "case_source_class": source,
        "interaction_family": interaction,
        "target_latency_band": target_band,
        "observed_latency_band": observed_band,
        "measurement_method": method,
        "latency_categories": categories,
        "latency_budget_tier": budget_tier,
        "metadata_only": bool(metadata_only),
        "raw_text_stored": bool(raw_text_stored),
        "private_data_used": bool(private_data_used),
        "audio_used": bool(audio_used),
        "runtime_path_used": bool(runtime_path_used),
        "safety_preflight_present": bool(safety_preflight_present),
        "authority_boundary_preserved": bool(authority_boundary_preserved),
        "blocked_reason": _normalize_string_list(blocked_reason or [], "blocked_reason"),
        "risk_notes": _normalize_string_list(risk_notes or [], "risk_notes"),
        "latency_bottleneck_label": _normalize_safe_string(latency_bottleneck_label, "latency_bottleneck_label", allow_empty=False),
        "improvement_candidate_label": _normalize_safe_string(improvement_candidate_label, "improvement_candidate_label", allow_empty=False),
        "denied_authority": _normalize_denied_authority_map(denied_authority),
        **{name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
        "validation_status": _safe_str(validation_status) if validation_status is not None else PACKET_VALIDATION_STATUS_VALID_V1,
        "validation_errors": _normalize_string_list(validation_errors or [], "validation_errors"),
        "internal_only": bool(internal_only),
        "non_authoritative": bool(non_authoritative),
    }

    if not packet["case_id"]:
        raise ValueError("case_id must be a non-empty safe string")
    if _contains_unsafe_reference(packet["case_id"]):
        raise ValueError("case_id contains forbidden content")
    if packet["metadata_only"] is not True:
        raise ValueError("metadata_only must be true")
    if packet["raw_text_stored"] is not False:
        raise ValueError("raw_text_stored must be false")
    if packet["private_data_used"] is not False:
        raise ValueError("private_data_used must be false")
    if packet["audio_used"] is not False:
        raise ValueError("audio_used must be false")
    if packet["runtime_path_used"] is not False:
        raise ValueError("runtime_path_used must be false")
    if packet["safety_preflight_present"] is not True:
        raise ValueError("safety_preflight_present must be true")
    if packet["authority_boundary_preserved"] is not True:
        raise ValueError("authority_boundary_preserved must be true")
    if packet["internal_only"] is not True:
        raise ValueError("internal_only must be true")
    if packet["non_authoritative"] is not True:
        raise ValueError("non_authoritative must be true")

    validation = validate_reaction_time_latency_budget_packet_v1(packet)
    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]) or "reaction time latency budget packet validation failed")
    return packet


def _scan_for_unsafe_content(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_scan_for_unsafe_content(raw) for raw in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_scan_for_unsafe_content(item) for item in value)
    if isinstance(value, str):
        return _contains_unsafe_reference(value)
    return False


def validate_reaction_time_latency_budget_packet_v1(packet: Any) -> dict[str, Any]:
    result = {
        "helper_type": HELPER_TYPE_V1,
        "schema": PACKET_SCHEMA_V1,
        "case_id": None,
        "case_source_class": None,
        "interaction_family": None,
        "target_latency_band": None,
        "observed_latency_band": None,
        "measurement_method": None,
        "latency_budget_tier": None,
        "valid": False,
        "status": PACKET_VALIDATION_STATUS_INVALID_V1,
        "errors": [],
        "warnings": [],
        "blocked_reasons": [],
        "internal_only": False,
        "non_authoritative": False,
    }

    if not isinstance(packet, Mapping):
        result["errors"].append("packet must be a mapping")
        result["blocked_reasons"].append("invalid_packet_shape")
        return result

    result["case_id"] = _safe_str(packet.get("case_id")) or None
    result["case_source_class"] = _safe_str(packet.get("case_source_class")) or None
    result["interaction_family"] = _safe_str(packet.get("interaction_family")) or None
    result["target_latency_band"] = _safe_str(packet.get("target_latency_band")) or None
    result["observed_latency_band"] = _safe_str(packet.get("observed_latency_band")) or None
    result["measurement_method"] = _safe_str(packet.get("measurement_method")) or None
    result["latency_budget_tier"] = _safe_str(packet.get("latency_budget_tier")) or None
    result["internal_only"] = packet.get("internal_only") is True
    result["non_authoritative"] = packet.get("non_authoritative") is True

    required_fields = PACKET_FIELD_NAMES_V1
    missing = [name for name in sorted(required_fields) if name not in packet]
    if missing:
        result["errors"].append(f"missing required fields: {', '.join(missing)}")
        result["blocked_reasons"].append("missing_required_fields")

    extra = sorted(set(_safe_str(name) for name in packet.keys()) - required_fields)
    if extra:
        result["errors"].append(f"unexpected fields: {', '.join(extra)}")
        result["blocked_reasons"].append("unexpected_fields")

    schema = _safe_str(packet.get("schema"))
    if schema != PACKET_SCHEMA_V1:
        result["errors"].append(f"schema must equal {PACKET_SCHEMA_V1}")

    case_id = _safe_str(packet.get("case_id"))
    if not case_id:
        result["errors"].append("case_id must be a non-empty safe string")
        result["blocked_reasons"].append("invalid_case_id")
    elif _contains_unsafe_reference(case_id):
        result["errors"].append("case_id contains forbidden content")
        result["blocked_reasons"].append("unsafe_metadata")

    source = _safe_str(packet.get("case_source_class"))
    if source not in SAFE_CASE_SOURCE_CLASSES_V1:
        result["errors"].append("unsafe case_source_class")
        result["blocked_reasons"].append("unsafe_source_class")

    interaction = _safe_str(packet.get("interaction_family"))
    if not interaction:
        result["errors"].append("interaction_family must be a non-empty safe string")
    elif _contains_unsafe_reference(interaction):
        result["errors"].append("interaction_family contains forbidden content")
        result["blocked_reasons"].append("unsafe_metadata")

    for field_name in ("target_latency_band", "observed_latency_band", "latency_budget_tier"):
        text = _safe_str(packet.get(field_name))
        if text not in LATENCY_BUDGET_TIER_LABELS_V1:
            result["errors"].append(f"unsafe {field_name}")
            result["blocked_reasons"].append("unsafe_latency_tier")

    method = _safe_str(packet.get("measurement_method"))
    if method not in MEASUREMENT_METHOD_LABELS_V1:
        result["errors"].append("unsafe measurement_method")
        result["blocked_reasons"].append("unsafe_measurement_method")

    categories = packet.get("latency_categories")
    if not isinstance(categories, list):
        result["errors"].append("latency_categories must be a real list of safe strings")
        result["blocked_reasons"].append("invalid_latency_categories")
    else:
        seen: set[str] = set()
        for item in categories:
            if not isinstance(item, str):
                result["errors"].append("latency_categories must contain only safe strings")
                result["blocked_reasons"].append("nested_unsafe_metadata")
                continue
            text = _safe_str(item)
            if text not in LATENCY_CATEGORY_LABELS_V1:
                result["errors"].append(f"unsafe latency category label: {text}")
                result["blocked_reasons"].append("unsafe_latency_category")
            if _contains_unsafe_reference(text):
                result["errors"].append("latency_categories contains forbidden content")
                result["blocked_reasons"].append("unsafe_metadata")
            if text in seen:
                result["warnings"].append(f"duplicate latency category label: {text}")
            seen.add(text)
        if not categories:
            result["errors"].append("latency_categories must not be empty")

    for field_name, expected_value in (
        ("metadata_only", True),
        ("raw_text_stored", False),
        ("private_data_used", False),
        ("audio_used", False),
        ("runtime_path_used", False),
        ("safety_preflight_present", True),
        ("authority_boundary_preserved", True),
        ("internal_only", True),
        ("non_authoritative", True),
    ):
        value = packet.get(field_name)
        if not isinstance(value, bool):
            result["errors"].append(f"{field_name} must be boolean {expected_value}")
            result["blocked_reasons"].append("invalid_boolean_field")
        elif value is not expected_value:
            result["errors"].append(f"{field_name} must be {expected_value}")
            result["blocked_reasons"].append("authority_boundary_violation")

    for field_name in ("latency_bottleneck_label", "improvement_candidate_label"):
        text = _safe_str(packet.get(field_name))
        if not text:
            result["errors"].append(f"{field_name} must be a non-empty safe string")
        elif _contains_unsafe_reference(text):
            result["errors"].append(f"{field_name} contains forbidden content")
            result["blocked_reasons"].append("unsafe_metadata")

    for field_name in ("blocked_reason", "risk_notes", "validation_errors"):
        value = packet.get(field_name)
        if not isinstance(value, list):
            result["errors"].append(f"{field_name} must be a real list of safe strings")
            result["blocked_reasons"].append("nested_unsafe_metadata")
            continue
        for item in value:
            if not isinstance(item, str):
                result["errors"].append(f"{field_name} must contain only safe strings")
                result["blocked_reasons"].append("nested_unsafe_metadata")
                continue
            text = _safe_str(item)
            if _contains_unsafe_reference(text):
                result["errors"].append(f"{field_name} contains forbidden content")
                result["blocked_reasons"].append("unsafe_metadata")

    denied = packet.get("denied_authority")
    if not isinstance(denied, Mapping):
        result["errors"].append("denied_authority must be a mapping")
        result["blocked_reasons"].append("authority_boundary_violation")
    else:
        denied_keys = { _safe_str(key) for key in denied.keys() }
        missing_denied = sorted(DENIED_AUTHORITY_FIELDS_V1 - denied_keys)
        extra_denied = sorted(denied_keys - DENIED_AUTHORITY_FIELDS_V1)
        if missing_denied:
            for name in missing_denied:
                result["errors"].append(f"missing denied authority field: {name}")
                result["blocked_reasons"].append(name)
        if extra_denied:
            result["errors"].append(f"unexpected denied_authority field(s): {', '.join(extra_denied)}")
            result["blocked_reasons"].append("authority_boundary_violation")
        for name in DENIED_AUTHORITY_FIELDS_V1:
            raw = denied.get(name)
            if not isinstance(raw, bool):
                result["errors"].append(f"denied authority field {name} must be boolean false")
                result["blocked_reasons"].append(name)
            elif raw is not False:
                result["errors"].append(f"denied authority field {name} must be false")
                result["blocked_reasons"].append(name)
            if packet.get(name) is not False:
                result["errors"].append(f"top-level denied authority field {name} must be false")
                result["blocked_reasons"].append(name)

    # Explicitly reject any unsafe content embedded anywhere in the packet values.
    if _scan_for_unsafe_content(packet):
        result["errors"].append("packet contains forbidden content")
        result["blocked_reasons"].append("unsafe_metadata")

    validation_status = _safe_str(packet.get("validation_status"))
    if validation_status not in {PACKET_VALIDATION_STATUS_VALID_V1, PACKET_VALIDATION_STATUS_INVALID_V1}:
        result["errors"].append("validation_status must be valid or invalid")
        result["blocked_reasons"].append("invalid_validation_status")
    if validation_status != PACKET_VALIDATION_STATUS_VALID_V1:
        result["errors"].append("validation_status must be valid for a valid packet")
        result["blocked_reasons"].append("invalid_validation_status")

    validation_errors = packet.get("validation_errors")
    if not isinstance(validation_errors, list):
        result["errors"].append("validation_errors must be a real list of safe strings")
        result["blocked_reasons"].append("nested_unsafe_metadata")
    else:
        if validation_errors:
            result["warnings"].append("validation_errors present in packet")
        for item in validation_errors:
            if not isinstance(item, str):
                result["errors"].append("validation_errors must contain only safe strings")
                result["blocked_reasons"].append("nested_unsafe_metadata")
                continue
            if _contains_unsafe_reference(item):
                result["errors"].append("validation_errors contains forbidden content")
                result["blocked_reasons"].append("unsafe_metadata")

    if result["errors"]:
        result["status"] = PACKET_VALIDATION_STATUS_INVALID_V1
        result["valid"] = False
    else:
        result["status"] = PACKET_VALIDATION_STATUS_VALID_V1
        result["valid"] = True

    deduped_blocked: list[str] = []
    seen_blocked: set[str] = set()
    for label in result["blocked_reasons"]:
        text = _safe_str(label)
        if text and text not in seen_blocked:
            deduped_blocked.append(text)
            seen_blocked.add(text)
    result["blocked_reasons"] = deduped_blocked
    return result


def _redact_for_json_safe(value: Any, *, path: str = "") -> Any:
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, raw in value.items():
            key_text = _safe_str(key)
            if path == "":
                safe_key = key_text if key_text in PACKET_FIELD_NAMES_V1 else "[redacted-key]"
            elif path == "denied_authority":
                safe_key = key_text if key_text in DENIED_AUTHORITY_FIELDS_V1 else "[redacted-key]"
            else:
                safe_key = key_text if not _contains_unsafe_reference(key_text) else "[redacted-key]"
            next_path = key_text if not path else f"{path}.{key_text}"
            redacted[safe_key] = _redact_for_json_safe(raw, path=next_path)
        return redacted
    if isinstance(value, list):
        return [_redact_for_json_safe(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, tuple):
        return [_redact_for_json_safe(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, set):
        return [_redact_for_json_safe(item, path=f"{path}[{index}]") for index, item in enumerate(sorted(value, key=lambda item: _safe_str(item)))]
    if isinstance(value, str):
        return "[redacted]" if _contains_unsafe_reference(value) else value
    if _is_json_safe_scalar(value):
        return value
    return _safe_str(value)


def to_reaction_time_latency_budget_json_safe_v1(packet: Any) -> Any:
    """Return a JSON-safe copy without laundering invalid packets into validity."""
    if not isinstance(packet, Mapping):
        raise ValueError("packet must be a mapping")

    validation = validate_reaction_time_latency_budget_packet_v1(packet)
    safe_copy = _redact_for_json_safe(copy.deepcopy(packet))
    if validation["valid"]:
        return safe_copy

    if isinstance(safe_copy, Mapping):
        safe_copy = dict(safe_copy)
        safe_copy["validation_status"] = PACKET_VALIDATION_STATUS_INVALID_V1
        safe_copy["validation_errors"] = list(validation["errors"])
        safe_copy["blocked_reason"] = list(validation["blocked_reasons"])
    return safe_copy


def summarize_reaction_time_latency_budget_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_reaction_time_latency_budget_packet_v1(packet)
    packet_map = packet if isinstance(packet, Mapping) else {}
    summary = {
        "helper_type": HELPER_TYPE_V1,
        "schema": PACKET_SCHEMA_V1,
        "case_id": _safe_str(packet_map.get("case_id")) or None,
        "case_source_class": _safe_str(packet_map.get("case_source_class")) or None,
        "interaction_family": _safe_str(packet_map.get("interaction_family")) or None,
        "target_latency_band": _safe_str(packet_map.get("target_latency_band")) or None,
        "observed_latency_band": _safe_str(packet_map.get("observed_latency_band")) or None,
        "measurement_method": _safe_str(packet_map.get("measurement_method")) or None,
        "latency_categories": list(packet_map.get("latency_categories", [])) if isinstance(packet_map.get("latency_categories"), list) else [],
        "latency_budget_tier": _safe_str(packet_map.get("latency_budget_tier")) or None,
        "blocked_reason": list(packet_map.get("blocked_reason", [])) if isinstance(packet_map.get("blocked_reason"), list) else [],
        "risk_notes": list(packet_map.get("risk_notes", [])) if isinstance(packet_map.get("risk_notes"), list) else [],
        "latency_bottleneck_label": _safe_str(packet_map.get("latency_bottleneck_label")) or None,
        "improvement_candidate_label": _safe_str(packet_map.get("improvement_candidate_label")) or None,
        "status": validation["status"],
        "valid": validation["valid"],
        "errors": list(validation["errors"]),
        "warnings": list(validation["warnings"]),
        "blocked_reasons": list(validation["blocked_reasons"]),
        "metadata_only": packet_map.get("metadata_only") is True,
        "internal_only": packet_map.get("internal_only") is True,
        "non_authoritative": packet_map.get("non_authoritative") is True,
        "authority_boundary_preserved": packet_map.get("authority_boundary_preserved") is True,
    }
    return summary


def render_reaction_time_latency_budget_markdown_v1(packet: Any) -> str:
    validation = validate_reaction_time_latency_budget_packet_v1(packet)
    if not validation["valid"]:
        raise ValueError("packet must validate before markdown rendering")

    packet_map = packet if isinstance(packet, Mapping) else {}
    categories = packet_map.get("latency_categories", [])
    if not isinstance(categories, list):
        categories = []
    blocked = packet_map.get("blocked_reason", [])
    if not isinstance(blocked, list):
        blocked = []
    risks = packet_map.get("risk_notes", [])
    if not isinstance(risks, list):
        risks = []
    denied = packet_map.get("denied_authority", {})
    if not isinstance(denied, Mapping):
        denied = {}

    lines = [
        "# WESLR Reaction Time Latency Budget Audit Packet V1",
        "- Status: VALID",
        f"- Schema: {_safe_str(packet_map.get('schema'))}",
        f"- Case ID: {_safe_str(packet_map.get('case_id'))}",
        f"- Case Source Class: {_safe_str(packet_map.get('case_source_class'))}",
        f"- Interaction Family: {_safe_str(packet_map.get('interaction_family'))}",
        f"- Target Latency Band: {_safe_str(packet_map.get('target_latency_band'))}",
        f"- Observed Latency Band: {_safe_str(packet_map.get('observed_latency_band'))}",
        f"- Measurement Method: {_safe_str(packet_map.get('measurement_method'))}",
        f"- Latency Budget Tier: {_safe_str(packet_map.get('latency_budget_tier'))}",
        f"- Latency Categories: {', '.join(_safe_str(item) for item in categories) or 'none'}",
        f"- Metadata Only: {packet_map.get('metadata_only') is True}",
        f"- Raw Text Stored: {packet_map.get('raw_text_stored') is True}",
        f"- Private Data Used: {packet_map.get('private_data_used') is True}",
        f"- Audio Used: {packet_map.get('audio_used') is True}",
        f"- Runtime Path Used: {packet_map.get('runtime_path_used') is True}",
        f"- Safety Preflight Present: {packet_map.get('safety_preflight_present') is True}",
        f"- Authority Boundary Preserved: {packet_map.get('authority_boundary_preserved') is True}",
        f"- Blocked Reason: {', '.join(_safe_str(item) for item in blocked) or 'none'}",
        f"- Risk Notes: {', '.join(_safe_str(item) for item in risks) or 'none'}",
        f"- Latency Bottleneck Label: {_safe_str(packet_map.get('latency_bottleneck_label'))}",
        f"- Improvement Candidate Label: {_safe_str(packet_map.get('improvement_candidate_label'))}",
        f"- Internal Only: {packet_map.get('internal_only') is True}",
        f"- Non-Authoritative: {packet_map.get('non_authoritative') is True}",
        "",
        "## Denied Authority",
    ]
    for name in sorted(DENIED_AUTHORITY_FIELDS_V1):
        lines.append(f"- {name}: {denied.get(name) is False}")
    lines.extend([
        "",
        "Internal use only. Metadata only. Non-authoritative.",
        "No runtime measurement, no public benchmark claim, and no product-readiness claim.",
    ])
    return "\n".join(lines)


def build_initial_reaction_time_latency_budget_examples_v1() -> dict[str, list[dict[str, Any]]]:
    safe_examples = [
        {
            "example_id": "immediate-acknowledgement-metadata",
            "label": "immediate acknowledgement metadata case",
            "packet": build_reaction_time_latency_budget_packet_v1(
                case_id="rtlb-safe-ack-1",
                case_source_class="synthetic_internal_prompt",
                interaction_family="acknowledgement",
                target_latency_band="tier_0_immediate_acknowledgement_100_200ms",
                observed_latency_band="tier_1_first_visible_reaction_under_250ms",
                measurement_method="synthetic_metadata_estimate",
                latency_categories=["perceived_reaction_time", "first_visible_acknowledgement"],
                latency_budget_tier="tier_0_immediate_acknowledgement_100_200ms",
                blocked_reason=[],
                risk_notes=["internal metadata only"],
                latency_bottleneck_label="safety preflight path",
                improvement_candidate_label="safe acknowledgement polish",
            ),
            "expected_valid": True,
        },
        {
            "example_id": "first-visible-reaction-metadata",
            "label": "first visible reaction metadata case",
            "packet": build_reaction_time_latency_budget_packet_v1(
                case_id="rtlb-safe-react-1",
                case_source_class="synthetic_fixture",
                interaction_family="reaction",
                target_latency_band="tier_1_first_visible_reaction_under_250ms",
                observed_latency_band="tier_1_first_visible_reaction_under_250ms",
                measurement_method="controlled_fixture_metadata",
                latency_categories=["first_visible_acknowledgement", "local_routing_decision_time"],
                latency_budget_tier="tier_1_first_visible_reaction_under_250ms",
                blocked_reason=[],
                risk_notes=["staged feedback only"],
                latency_bottleneck_label="first visible reaction",
                improvement_candidate_label="faster acknowledgment shell",
            ),
            "expected_valid": True,
        },
        {
            "example_id": "simple-local-routing-metadata",
            "label": "simple local routing metadata case",
            "packet": build_reaction_time_latency_budget_packet_v1(
                case_id="rtlb-safe-routing-1",
                case_source_class="metadata_only_trace",
                interaction_family="local-routing",
                target_latency_band="tier_2_simple_local_routing_300_500ms",
                observed_latency_band="tier_2_simple_local_routing_300_500ms",
                measurement_method="manual_operator_observation",
                latency_categories=["local_routing_decision_time", "safety_preflight_validation_time"],
                latency_budget_tier="tier_2_simple_local_routing_300_500ms",
                blocked_reason=[],
                risk_notes=["routing metadata only"],
                latency_bottleneck_label="local routing branch",
                improvement_candidate_label="shorter preflight path",
            ),
            "expected_valid": True,
        },
        {
            "example_id": "safety-preflight-metadata",
            "label": "safety preflight latency metadata case",
            "packet": build_reaction_time_latency_budget_packet_v1(
                case_id="rtlb-safe-preflight-1",
                case_source_class="operator_supplied_nonprivate_metadata",
                interaction_family="safety-preflight",
                target_latency_band="tier_2_simple_local_routing_300_500ms",
                observed_latency_band="tier_3_short_answer_planning_under_1_2s",
                measurement_method="controlled_fixture_metadata",
                latency_categories=["safety_preflight_validation_time", "blocked_task_explanation_time"],
                latency_budget_tier="tier_2_simple_local_routing_300_500ms",
                blocked_reason=[],
                risk_notes=["safety gate remains first"],
                latency_bottleneck_label="safety preflight gate",
                improvement_candidate_label="faster safe check",
            ),
            "expected_valid": True,
        },
        {
            "example_id": "memory-context-lookup-metadata",
            "label": "memory/context lookup metadata case",
            "packet": build_reaction_time_latency_budget_packet_v1(
                case_id="rtlb-safe-memory-1",
                case_source_class="public_open_metadata",
                interaction_family="memory-lookup",
                target_latency_band="tier_3_short_answer_planning_under_1_2s",
                observed_latency_band="tier_3_short_answer_planning_under_1_2s",
                measurement_method="synthetic_metadata_estimate",
                latency_categories=["memory_context_lookup_time", "evidence_provenance_lookup_time"],
                latency_budget_tier="tier_3_short_answer_planning_under_1_2s",
                blocked_reason=[],
                risk_notes=["lookup remains internal"],
                latency_bottleneck_label="memory lookup path",
                improvement_candidate_label="bounded lookup metadata",
            ),
            "expected_valid": True,
        },
        {
            "example_id": "evidence-provenance-lookup-metadata",
            "label": "evidence/provenance lookup metadata case",
            "packet": build_reaction_time_latency_budget_packet_v1(
                case_id="rtlb-safe-evidence-1",
                case_source_class="unknown_safe_metadata",
                interaction_family="evidence-provenance",
                target_latency_band="tier_3_short_answer_planning_under_1_2s",
                observed_latency_band="tier_4_long_answer_streaming_required",
                measurement_method="manual_operator_observation",
                latency_categories=["evidence_provenance_lookup_time", "response_planning_time"],
                latency_budget_tier="tier_3_short_answer_planning_under_1_2s",
                blocked_reason=[],
                risk_notes=["internal notes only"],
                latency_bottleneck_label="provenance lookup",
                improvement_candidate_label="tight provenance metadata",
            ),
            "expected_valid": True,
        },
        {
            "example_id": "response-planning-metadata",
            "label": "response planning metadata case",
            "packet": build_reaction_time_latency_budget_packet_v1(
                case_id="rtlb-safe-plan-1",
                case_source_class="synthetic_fixture",
                interaction_family="response-planning",
                target_latency_band="tier_3_short_answer_planning_under_1_2s",
                observed_latency_band="tier_3_short_answer_planning_under_1_2s",
                measurement_method="synthetic_metadata_estimate",
                latency_categories=["response_planning_time", "first_token_or_first_visible_output_time"],
                latency_budget_tier="tier_3_short_answer_planning_under_1_2s",
                blocked_reason=[],
                risk_notes=["planning remains metadata only"],
                latency_bottleneck_label="response planning",
                improvement_candidate_label="narrow planning boundary",
            ),
            "expected_valid": True,
        },
        {
            "example_id": "streaming-cadence-metadata",
            "label": "long-answer streaming cadence metadata case",
            "packet": build_reaction_time_latency_budget_packet_v1(
                case_id="rtlb-safe-stream-1",
                case_source_class="synthetic_internal_prompt",
                interaction_family="streaming-cadence",
                target_latency_band="tier_4_long_answer_streaming_required",
                observed_latency_band="tier_4_long_answer_streaming_required",
                measurement_method="controlled_fixture_metadata",
                latency_categories=["first_token_or_first_visible_output_time", "streaming_progressive_response_cadence"],
                latency_budget_tier="tier_4_long_answer_streaming_required",
                blocked_reason=[],
                risk_notes=["streaming cadence metadata only"],
                latency_bottleneck_label="stream cadence",
                improvement_candidate_label="steady staged output",
            ),
            "expected_valid": True,
        },
        {
            "example_id": "blocked-task-explanation-metadata",
            "label": "blocked-task explanation metadata case",
            "packet": build_reaction_time_latency_budget_packet_v1(
                case_id="rtlb-safe-blocked-1",
                case_source_class="metadata_only_trace",
                interaction_family="blocked-explanation",
                target_latency_band="tier_5_blocked_high_risk_fast_safe_explanation",
                observed_latency_band="tier_5_blocked_high_risk_fast_safe_explanation",
                measurement_method="manual_operator_observation",
                latency_categories=["blocked_task_explanation_time", "operator_approval_wait_boundary"],
                latency_budget_tier="tier_5_blocked_high_risk_fast_safe_explanation",
                blocked_reason=["blocked by safety policy"],
                risk_notes=["fast safe refusal only"],
                latency_bottleneck_label="blocked response path",
                improvement_candidate_label="concise boundary explanation",
            ),
            "expected_valid": True,
        },
        {
            "example_id": "operator-approval-wait-metadata",
            "label": "operator-approval wait metadata case",
            "packet": build_reaction_time_latency_budget_packet_v1(
                case_id="rtlb-safe-approval-1",
                case_source_class="public_open_metadata",
                interaction_family="operator-approval",
                target_latency_band="tier_6_operator_governance_wait_no_fake_progress",
                observed_latency_band="tier_6_operator_governance_wait_no_fake_progress",
                measurement_method="future_controlled_runtime_measurement_requires_approval",
                latency_categories=["operator_approval_wait_boundary", "background_async_safe_continuation_boundary"],
                latency_budget_tier="tier_6_operator_governance_wait_no_fake_progress",
                blocked_reason=["waiting for operator approval"],
                risk_notes=["no fake progress"],
                latency_bottleneck_label="governance wait",
                improvement_candidate_label="clear wait boundary",
            ),
            "expected_valid": True,
        },
    ]

    unsafe_examples = [
        {
            "example_id": "unsafe-private-chat-timing",
            "label": "unsafe private chat timing case",
            "packet": {
                "schema": PACKET_SCHEMA_V1,
                "case_id": "rtlb-unsafe-private-chat-1",
                "case_source_class": "private_user_chat",
                "interaction_family": "timing",
                "target_latency_band": "tier_1_first_visible_reaction_under_250ms",
                "observed_latency_band": "tier_1_first_visible_reaction_under_250ms",
                "measurement_method": "synthetic_metadata_estimate",
                "latency_categories": ["perceived_reaction_time"],
                "latency_budget_tier": "tier_1_first_visible_reaction_under_250ms",
                "metadata_only": True,
                "raw_text_stored": False,
                "private_data_used": False,
                "audio_used": False,
                "runtime_path_used": False,
                "safety_preflight_present": True,
                "authority_boundary_preserved": True,
                "blocked_reason": ["private chat timing"],
                "risk_notes": ["private_user_chat"],
                "latency_bottleneck_label": "private chat timing",
                "improvement_candidate_label": "blocked private timing",
                "denied_authority": {name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                **{name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                "validation_status": PACKET_VALIDATION_STATUS_INVALID_V1,
                "validation_errors": ["private chat timing is forbidden"],
                "internal_only": True,
                "non_authoritative": True,
            },
            "expected_valid": False,
        },
        {
            "example_id": "unsafe-microphone-audio-timing",
            "label": "unsafe microphone/audio timing case",
            "packet": {
                "schema": PACKET_SCHEMA_V1,
                "case_id": "rtlb-unsafe-mic-1",
                "case_source_class": "synthetic_internal_prompt",
                "interaction_family": "audio-timing",
                "target_latency_band": "tier_1_first_visible_reaction_under_250ms",
                "observed_latency_band": "tier_1_first_visible_reaction_under_250ms",
                "measurement_method": "microphone_audio_timing_extraction",
                "latency_categories": ["first_visible_acknowledgement"],
                "latency_budget_tier": "tier_1_first_visible_reaction_under_250ms",
                "metadata_only": True,
                "raw_text_stored": False,
                "private_data_used": False,
                "audio_used": True,
                "runtime_path_used": False,
                "safety_preflight_present": True,
                "authority_boundary_preserved": True,
                "blocked_reason": ["microphone/audio timing"],
                "risk_notes": ["microphone_stream"],
                "latency_bottleneck_label": "mic timing",
                "improvement_candidate_label": "blocked audio timing",
                "denied_authority": {name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                **{name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                "validation_status": PACKET_VALIDATION_STATUS_INVALID_V1,
                "validation_errors": ["microphone audio timing extraction is forbidden"],
                "internal_only": True,
                "non_authoritative": True,
            },
            "expected_valid": False,
        },
        {
            "example_id": "unsafe-provider-log-timing",
            "label": "unsafe provider log timing case",
            "packet": {
                "schema": PACKET_SCHEMA_V1,
                "case_id": "rtlb-unsafe-provider-log-1",
                "case_source_class": "synthetic_fixture",
                "interaction_family": "provider-log",
                "target_latency_band": "tier_2_simple_local_routing_300_500ms",
                "observed_latency_band": "tier_2_simple_local_routing_300_500ms",
                "measurement_method": "provider_log_analysis",
                "latency_categories": ["local_routing_decision_time"],
                "latency_budget_tier": "tier_2_simple_local_routing_300_500ms",
                "metadata_only": True,
                "raw_text_stored": False,
                "private_data_used": False,
                "audio_used": False,
                "runtime_path_used": False,
                "safety_preflight_present": True,
                "authority_boundary_preserved": True,
                "blocked_reason": ["provider log analysis"],
                "risk_notes": ["provider_log"],
                "latency_bottleneck_label": "provider log path",
                "improvement_candidate_label": "blocked provider logs",
                "denied_authority": {name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                **{name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                "validation_status": PACKET_VALIDATION_STATUS_INVALID_V1,
                "validation_errors": ["provider log analysis is forbidden"],
                "internal_only": True,
                "non_authoritative": True,
            },
            "expected_valid": False,
        },
        {
            "example_id": "unsafe-public-performance-claim",
            "label": "unsafe public performance claim case",
            "packet": {
                "schema": PACKET_SCHEMA_V1,
                "case_id": "rtlb-unsafe-public-claim-1",
                "case_source_class": "public_open_metadata",
                "interaction_family": "public-claim",
                "target_latency_band": "tier_0_immediate_acknowledgement_100_200ms",
                "observed_latency_band": "tier_0_immediate_acknowledgement_100_200ms",
                "measurement_method": "manual_operator_observation",
                "latency_categories": ["perceived_reaction_time"],
                "latency_budget_tier": "tier_0_immediate_acknowledgement_100_200ms",
                "metadata_only": True,
                "raw_text_stored": False,
                "private_data_used": False,
                "audio_used": False,
                "runtime_path_used": False,
                "safety_preflight_present": True,
                "authority_boundary_preserved": True,
                "blocked_reason": ["public performance claim"],
                "risk_notes": ["public_performance"],
                "latency_bottleneck_label": "public claim drift",
                "improvement_candidate_label": "blocked public claim",
                "denied_authority": {name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                **{name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                "validation_status": PACKET_VALIDATION_STATUS_INVALID_V1,
                "validation_errors": ["public performance claims are forbidden"],
                "internal_only": True,
                "non_authoritative": True,
            },
            "expected_valid": False,
        },
        {
            "example_id": "unsafe-runtime-authority",
            "label": "unsafe runtime authority case",
            "packet": {
                "schema": PACKET_SCHEMA_V1,
                "case_id": "rtlb-unsafe-runtime-authority-1",
                "case_source_class": "metadata_only_trace",
                "interaction_family": "authority",
                "target_latency_band": "tier_6_operator_governance_wait_no_fake_progress",
                "observed_latency_band": "tier_6_operator_governance_wait_no_fake_progress",
                "measurement_method": "synthetic_metadata_estimate",
                "latency_categories": ["operator_approval_wait_boundary"],
                "latency_budget_tier": "tier_6_operator_governance_wait_no_fake_progress",
                "metadata_only": True,
                "raw_text_stored": False,
                "private_data_used": False,
                "audio_used": False,
                "runtime_path_used": False,
                "safety_preflight_present": True,
                "authority_boundary_preserved": False,
                "blocked_reason": ["runtime authority"],
                "risk_notes": ["runtime_authority"],
                "latency_bottleneck_label": "authority boundary",
                "improvement_candidate_label": "blocked runtime authority",
                "denied_authority": {name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                **{name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                "runtime_authority": True,
                "validation_status": PACKET_VALIDATION_STATUS_INVALID_V1,
                "validation_errors": ["runtime authority is forbidden"],
                "internal_only": True,
                "non_authoritative": True,
            },
            "expected_valid": False,
        },
        {
            "example_id": "unsafe-behavior-pack-promotion",
            "label": "unsafe behavior-pack promotion case",
            "packet": {
                "schema": PACKET_SCHEMA_V1,
                "case_id": "rtlb-unsafe-bpp-1",
                "case_source_class": "synthetic_fixture",
                "interaction_family": "promotion",
                "target_latency_band": "tier_5_blocked_high_risk_fast_safe_explanation",
                "observed_latency_band": "tier_5_blocked_high_risk_fast_safe_explanation",
                "measurement_method": "manual_operator_observation",
                "latency_categories": ["blocked_task_explanation_time"],
                "latency_budget_tier": "tier_5_blocked_high_risk_fast_safe_explanation",
                "metadata_only": True,
                "raw_text_stored": False,
                "private_data_used": False,
                "audio_used": False,
                "runtime_path_used": False,
                "safety_preflight_present": True,
                "authority_boundary_preserved": True,
                "blocked_reason": ["behavior pack promotion"],
                "risk_notes": ["behavior_pack_promotion"],
                "latency_bottleneck_label": "promotion misuse",
                "improvement_candidate_label": "blocked promotion misuse",
                "denied_authority": {name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                **{name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)},
                "behavior_pack_promotion_authority": True,
                "validation_status": PACKET_VALIDATION_STATUS_INVALID_V1,
                "validation_errors": ["behavior pack promotion authority is forbidden"],
                "internal_only": True,
                "non_authoritative": True,
            },
            "expected_valid": False,
        },
    ]

    return {
        "helper_type": HELPER_TYPE_V1,
        "schema": PACKET_SCHEMA_V1,
        "safe_examples": safe_examples,
        "unsafe_examples": unsafe_examples,
    }
