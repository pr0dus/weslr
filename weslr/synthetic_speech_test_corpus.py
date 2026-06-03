"""Metadata-only helpers for WESLR synthetic speech corpus packets v1.

This module is intentionally pure, deterministic, and fail-closed.
It normalizes safe synthetic speech corpus metadata for future helper work.

It does not perform file I/O, network I/O, subprocess execution, microphone
access, audio generation, audio processing, runtime voice recognition,
speaker verification, template storage, registry writes, .weslr writes,
runtime wiring, or any public claims.
"""

from __future__ import annotations

import copy
import re
from typing import Any, Mapping, Sequence

HELPER_TYPE_V1 = "weslr_synthetic_speech_test_corpus_helper_v1"
PACKET_TYPE_V1 = "synthetic_speech_corpus_packet_v1"

ALLOWED_SOURCE_CLASSES_V1 = {
    "synthetic_weslr_created",
    "operator_written_text_only",
    "provenance_known_fixture",
    "public_open_text_only",
}

BLOCKED_SOURCE_CLASSES_V1 = {
    "unknown_source_blocked",
    "private_audio_blocked",
    "hidden_recording_blocked",
    "biometric_dataset_blocked",
    "poisoned_media_blocked",
}

ALLOWED_VARIANT_FAMILIES_V1 = {
    "clear_command",
    "near_neighbor_command",
    "noisy_variant",
    "accent_variant",
    "multilingual_variant",
    "partial_command",
    "background_speech",
    "repeated_command",
    "fake_approval_phrase",
    "unsafe_action_phrase",
    "low_confidence_phrase",
    "replay_scenario_metadata",
    "synthetic_voice_scenario_metadata",
    "cymatics_misleading_display_scenario",
    "prompt_injection_spoken_phrase",
    "unknown_variant",
}

REQUIRED_FORBIDDEN_SOURCE_FLAG_NAMES_V1 = {
    "has_private_user_audio",
    "has_hidden_recording",
    "has_raw_audio",
    "has_biometric_dataset",
    "has_unapproved_proprietary_dataset",
    "has_poisoned_external_media",
    "has_social_media_audio",
    "has_public_benchmark_claim",
    "has_speaker_verification_claim",
    "has_action_authority",
    "has_model_provider_call",
    "has_weslr_write",
    "has_behavior_pack_promotion",
}

RECOMMENDED_FORBIDDEN_SOURCE_FLAG_NAMES_V1 = {
    "has_audio_generation",
    "has_speaker_verification",
}

FORBIDDEN_SOURCE_FLAG_NAMES_V1 = tuple(
    sorted(REQUIRED_FORBIDDEN_SOURCE_FLAG_NAMES_V1 | RECOMMENDED_FORBIDDEN_SOURCE_FLAG_NAMES_V1)
)

REQUIRED_PACKET_FIELDS_V1 = {
    "packet_id",
    "schema_version",
    "source_refs",
    "provenance_refs",
    "corpus_name",
    "corpus_scope",
    "variant_family_refs",
    "scenario_refs",
    "allowed_source_class",
    "forbidden_source_flags",
    "coverage_summary",
    "synthetic_only",
    "provenance_known",
    "review_required",
    "no_private_user_audio",
    "no_hidden_recording",
    "no_biometric_dataset",
    "no_public_benchmark_claim",
    "no_authority_granted",
    "no_public_claim",
    "safe_metadata",
}

OPTIONAL_PACKET_FIELDS_V1 = {
    "created_at",
    "created_by_ref",
    "related_packet_refs",
    "related_design_refs",
    "notes",
}

PACKET_FIELD_NAMES_V1 = REQUIRED_PACKET_FIELDS_V1 | OPTIONAL_PACKET_FIELDS_V1
RESERVED_PACKET_FIELD_NAMES_V1 = PACKET_FIELD_NAMES_V1 | {"helper_type"}

REQUIRED_COVERAGE_SUMMARY_FIELD_NAMES_V1 = {
    "source_ref_count",
    "provenance_ref_count",
    "variant_family_ref_count",
    "scenario_ref_count",
    "blocked_flag_true_count",
    "allowed_source_class",
    "synthetic_only",
    "provenance_known",
    "safe_metadata",
}

QUALITY_BANDS_V1 = {
    "unknown",
    "not_evaluated",
    "low",
    "medium",
    "high",
    "blocked",
    "requires_review",
}

SENSITIVE_KEY_HINTS_V1 = (
    "raw_audio",
    "raw audio",
    "audio_buffer",
    "audio buffer",
    "audio_buffers",
    "audio payload",
    "microphone",
    "live_stream",
    "live stream",
    "raw_waveform",
    "raw waveform",
    "voice_recording",
    "voice recording",
    "voice_recordings",
    "voice recordings",
    "hidden_recording",
    "hidden recording",
    "hidden_recordings",
    "hidden recordings",
    "private_user_audio",
    "private user audio",
    "biometric_dataset",
    "biometric dataset",
    "proprietary_dataset",
    "proprietary speech dataset",
    "poisoned_media",
    "poisoned media",
    "social_media_audio",
    "social media audio",
    "public_benchmark",
    "public benchmark",
    "public_accuracy",
    "public accuracy",
    "benchmark",
    "product_readiness",
    "product-readiness",
    "certification",
    "authority",
    "speaker_verification",
    "speaker verification",
    "speaker_verified",
    "voice_identity",
    "voice identity",
    "voice_verified",
    "voice verified",
    "voice_template_updated",
    "voice template updated",
    "speaker_template_updated",
    "speaker template updated",
    "account_access_restored",
    "fallback_auth_status",
    "authorization_granted",
    "authority_granted",
    "action_authorized",
    "action_authority",
    "owner_verified",
    "operator_verified",
    "approved_by_voice",
    "voice_approval",
    "model_provider_call",
    "weslr_write",
    "behavior_pack_promotion",
    "audio_generation",
    "generated_audio",
    "audio_generated",
    ".weslr",
)

AUTHORITY_ADJACENT_METADATA_KEYS_V1 = {
    "speaker_verified",
    "speaker_verification",
    "speaker_verification_status",
    "speaker_identity",
    "identity_claimed",
    "identity_verified",
    "voice_identity",
    "voice_verified",
    "biometric_identity",
    "biometric_verified",
    "template_verified",
    "voice_template_updated",
    "speaker_template_updated",
    "account_access_restored",
    "fallback_auth_status",
    "authorization_granted",
    "authority_granted",
    "action_authorized",
    "owner_verified",
    "operator_verified",
    "approved_by_voice",
    "voice_approval",
    "audio_generation",
    "generated_audio",
    "audio_generated",
    "speaker_verification_claim",
    "action_authority_claim",
    "public_benchmark_claim",
    "public_accuracy_claim",
    "model_provider_call",
    "weslr_write",
    "behavior_pack_promotion",
    "raw_audio",
    "voice_recording",
    "raw_voice_recording",
    "hidden_recording",
    "private_user_audio",
    "biometric_dataset",
    "poisoned_media",
    "social_media_audio",
}

AUTHORITY_ADJACENT_KEY_HINTS_V1 = tuple(
    sorted(re.sub(r"[^a-z0-9]+", "", key.lower()).strip() for key in AUTHORITY_ADJACENT_METADATA_KEYS_V1)
)

FORBIDDEN_FIELD_MARKERS_V1 = (
    "raw waveform data",
    "raw voice recording",
    "raw voice recordings",
    "raw audio",
    "audio buffer",
    "audio buffers",
    "audio payload",
    "microphone handle",
    "microphone handles",
    "voice recording",
    "voice recordings",
    "hidden recording",
    "hidden recordings",
    "private user audio",
    "biometric speaker dataset",
    "biometric datasets",
    "proprietary speech dataset",
    "proprietary speech datasets",
    "poisoned external media",
    "arbitrary social media audio",
    "social media audio",
    "official benchmark",
    "private benchmark",
    "public benchmark",
    "public accuracy",
    "product-readiness",
    "product readiness",
    "certification claim",
    "authority-bearing claim",
    "speaker verification",
    "speaker verified",
    "voice identity",
    "voice verified",
    "voice template updated",
    "speaker template updated",
    "account access restored",
    "fallback auth",
    "action authority",
    "action authorized",
    "provider output payload",
    "model output payload",
    "runtime wiring",
    "live audio",
    "live stream",
    ".weslr",
    "behavior pack promotion",
    "audio generation",
    "generated audio",
    "audio generated",
)

JSON_SCALAR_TYPES_V1 = (str, int, float, bool, type(None))
VALIDATION_STATUS_VALID_V1 = "valid"
VALIDATION_STATUS_INVALID_V1 = "invalid"


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _normalize_key_token(value: Any) -> str:
    text = _safe_str(value).lower()
    return re.sub(r"[^a-z0-9]+", "", text).strip()


def _is_json_safe_value(value: Any) -> bool:
    if isinstance(value, JSON_SCALAR_TYPES_V1):
        return True
    if isinstance(value, list):
        return all(_is_json_safe_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_safe_value(item) for key, item in value.items())
    return False


def _json_safe_copy(value: Any) -> Any:
    value = copy.deepcopy(value)
    if isinstance(value, JSON_SCALAR_TYPES_V1):
        return value
    if isinstance(value, list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, set):
        return sorted((_json_safe_copy(item) for item in value), key=lambda item: (type(item).__name__, repr(item)))
    if isinstance(value, dict):
        return {str(key): _json_safe_copy(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    return _safe_str(value)


def _contains_forbidden_marker(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if _contains_forbidden_marker(key) or _contains_forbidden_marker(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_marker(item) for item in value)
    text = _safe_str(value).lower()
    if not text:
        return False
    return any(marker in text for marker in FORBIDDEN_FIELD_MARKERS_V1) or any(
        hint in text for hint in SENSITIVE_KEY_HINTS_V1
    )


def _contains_authority_adjacent_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                return True
            if _contains_authority_adjacent_key(key) or _contains_authority_adjacent_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_authority_adjacent_key(item) for item in value)
    token = _normalize_key_token(value)
    if not token:
        return False
    return token in AUTHORITY_ADJACENT_KEY_HINTS_V1


def _is_safe_metadata_key(key: str) -> bool:
    if not isinstance(key, str):
        return False
    key_text = _safe_str(key)
    if not key_text or key_text.startswith("_"):
        return False
    lowered = key_text.lower()
    normalized = _normalize_key_token(lowered)
    if lowered in RESERVED_PACKET_FIELD_NAMES_V1:
        return False
    if normalized in AUTHORITY_ADJACENT_KEY_HINTS_V1:
        return False
    if any(marker in lowered for marker in SENSITIVE_KEY_HINTS_V1):
        return False
    return True


def _normalize_string(value: Any, field_name: str, *, allow_empty: bool = False) -> str:
    text = _safe_str(value)
    if not text and not allow_empty:
        raise ValueError(f"{field_name} must be a non-empty safe string")
    if _contains_forbidden_marker(text):
        raise ValueError(f"{field_name} contains forbidden content")
    return text


def _normalize_string_list(value: Any, field_name: str, *, allow_empty: bool = True) -> list[str]:
    if value is None:
        items: list[Any] = []
    elif isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a real list of safe strings")
    elif isinstance(value, dict):
        items = list(value.values())
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        raise ValueError(f"{field_name} must be a real list of safe strings")

    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _normalize_string(item, field_name)
        if text not in seen:
            out.append(text)
            seen.add(text)

    if not out and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return out


def _normalize_optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _normalize_string(value, field_name, allow_empty=True)


def _normalize_optional_string_list(value: Any, field_name: str) -> list[str] | None:
    if value is None:
        return None
    return _normalize_string_list(value, field_name)


def _normalize_allowed_source_class(value: Any) -> str:
    source_class = _normalize_string(value, "allowed_source_class")
    if source_class in BLOCKED_SOURCE_CLASSES_V1:
        raise ValueError(f"blocked source class not allowed: {source_class}")
    if source_class not in ALLOWED_SOURCE_CLASSES_V1:
        raise ValueError(f"unknown unsafe source class: {source_class}")
    return source_class


def _normalize_variant_family_refs(value: Any) -> list[str]:
    families = _normalize_string_list(value, "variant_family_refs", allow_empty=False)
    out: list[str] = []
    seen: set[str] = set()
    for family in families:
        if family not in ALLOWED_VARIANT_FAMILIES_V1:
            raise ValueError(f"unknown unsafe variant family: {family}")
        if family not in seen:
            out.append(family)
            seen.add(family)
    return out


def _normalize_forbidden_source_flags(value: Any) -> dict[str, bool]:
    mapping: dict[str, Any] = {}
    if value is None:
        mapping = {}
    elif isinstance(value, Mapping):
        mapping = dict(value)
    else:
        raise ValueError("forbidden_source_flags must be a mapping")

    out = {name: False for name in FORBIDDEN_SOURCE_FLAG_NAMES_V1}
    for key, raw in mapping.items():
        name = _safe_str(key)
        if name not in out:
            raise ValueError(f"unknown forbidden source flag: {name}")
        if not isinstance(raw, bool):
            raise ValueError(f"forbidden source flag must be a boolean: {name}")
        out[name] = raw
    return out


def _normalize_coverage_summary(
    *,
    source_refs: Sequence[str],
    provenance_refs: Sequence[str],
    variant_family_refs: Sequence[str],
    scenario_refs: Sequence[str],
    allowed_source_class: str,
    forbidden_source_flags: Mapping[str, bool],
    synthetic_only: bool,
    provenance_known: bool,
    safe_metadata: bool,
    value: Any,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "source_ref_count": len(source_refs),
        "provenance_ref_count": len(provenance_refs),
        "variant_family_ref_count": len(variant_family_refs),
        "scenario_ref_count": len(scenario_refs),
        "blocked_flag_true_count": sum(1 for flag in forbidden_source_flags.values() if flag),
        "allowed_source_class": allowed_source_class,
        "synthetic_only": synthetic_only,
        "provenance_known": provenance_known,
        "safe_metadata": safe_metadata,
    }
    if value is None:
        return summary
    if not isinstance(value, Mapping):
        raise ValueError("coverage_summary must be a mapping")

    for key, raw in value.items():
        name = _safe_str(key)
        if name in REQUIRED_COVERAGE_SUMMARY_FIELD_NAMES_V1:
            pass
        elif not _is_safe_metadata_key(name):
            raise ValueError(f"unsafe coverage summary field: {name}")
        if not _is_json_safe_value(raw):
            raise ValueError(f"coverage_summary must be JSON-safe: {name}")
        if _contains_forbidden_marker(raw):
            raise ValueError(f"coverage_summary contains forbidden content: {name}")
        if _contains_authority_adjacent_key(raw):
            raise ValueError(f"authority-adjacent coverage summary metadata not allowed: {name}")
        if name in summary and summary[name] != raw:
            raise ValueError(f"coverage_summary field conflicts with computed safety metadata: {name}")
        if name not in summary:
            summary[name] = _json_safe_copy(raw)
    return summary


def _normalize_extra_metadata(extra_metadata: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, raw in extra_metadata.items():
        name = _safe_str(key)
        if not _is_safe_metadata_key(name):
            raise ValueError(f"unsafe extra metadata field: {name}")
        if name in RESERVED_PACKET_FIELD_NAMES_V1 or name == "helper_type":
            raise ValueError(f"reserved packet field cannot be supplied as extra metadata: {name}")
        if not _is_json_safe_value(raw):
            raise ValueError(f"extra metadata must be JSON-safe: {name}")
        if _contains_forbidden_marker(raw):
            raise ValueError(f"extra metadata contains forbidden content: {name}")
        if _contains_authority_adjacent_key(raw):
            raise ValueError(f"authority-adjacent metadata not allowed: {name}")
        out[name] = _json_safe_copy(raw)
    return out


def _validate_packet_core(packet: Any) -> dict[str, Any]:
    result = {
        "summary_type": "synthetic_speech_corpus_packet_summary_v1",
        "status": VALIDATION_STATUS_INVALID_V1,
        "valid": False,
        "errors": [],
        "warnings": [],
        "blocked_labels": [],
        "packet_id": None,
        "schema_version": None,
        "source_class": None,
    }

    if not isinstance(packet, Mapping):
        result["errors"].append("packet must be a mapping")
        return result

    packet_id = _safe_str(packet.get("packet_id"))
    schema_version = _safe_str(packet.get("schema_version"))
    result["packet_id"] = packet_id or None
    result["schema_version"] = schema_version or None

    missing_fields = [name for name in REQUIRED_PACKET_FIELDS_V1 if name not in packet]
    if missing_fields:
        result["errors"].append(f"missing required fields: {', '.join(sorted(missing_fields))}")
        result["blocked_labels"].append("missing_required_field")

    if not packet_id:
        result["errors"].append("packet_id must be a non-empty stable string")
    if schema_version != PACKET_TYPE_V1:
        result["errors"].append(f"schema_version must equal {PACKET_TYPE_V1}")

    if packet_id and _contains_forbidden_marker(packet_id):
        result["errors"].append("packet_id contains forbidden content")

    source_class_value = packet.get("allowed_source_class")
    if isinstance(source_class_value, str):
        result["source_class"] = source_class_value
        if source_class_value in BLOCKED_SOURCE_CLASSES_V1:
            result["errors"].append(f"blocked source class not allowed: {source_class_value}")
        elif source_class_value not in ALLOWED_SOURCE_CLASSES_V1:
            result["errors"].append(f"unknown unsafe source class: {source_class_value}")
        elif source_class_value == "public_open_text_only":
            # Keep this strictly text-only.
            pass
    else:
        result["errors"].append("allowed_source_class must be a safe string")

    for field_name in ("source_refs", "provenance_refs", "scenario_refs", "related_packet_refs", "related_design_refs"):
        if field_name in packet:
            value = packet.get(field_name)
            if value is None:
                continue
            if not isinstance(value, list):
                result["errors"].append(f"{field_name} must be a real list of safe strings")
                continue
            for item in value:
                if not isinstance(item, str) or not item.strip():
                    result["errors"].append(f"{field_name} must contain safe strings")
                    break
                if _contains_forbidden_marker(item):
                    result["errors"].append(f"{field_name} contains forbidden content")
                    break

    for field_name in ("corpus_name", "corpus_scope", "created_at", "created_by_ref", "notes"):
        if field_name in packet and packet.get(field_name) is not None:
            value = packet.get(field_name)
            if isinstance(value, str):
                if not value.strip():
                    result["errors"].append(f"{field_name} must be a non-empty safe string")
                elif _contains_forbidden_marker(value):
                    result["errors"].append(f"{field_name} contains forbidden content")
            elif not _is_json_safe_value(value):
                result["errors"].append(f"{field_name} must be JSON-safe")

    for field_name in ("synthetic_only", "provenance_known", "review_required", "no_private_user_audio", "no_hidden_recording", "no_biometric_dataset", "no_public_benchmark_claim", "no_authority_granted", "no_public_claim", "safe_metadata"):
        if field_name not in packet:
            continue
        value = packet.get(field_name)
        if not isinstance(value, bool):
            result["errors"].append(f"{field_name} must be a boolean")
            continue
        if field_name != "review_required" and value is not True:
            result["errors"].append(f"{field_name} must be true")

    forbidden_source_flags = packet.get("forbidden_source_flags")
    if not isinstance(forbidden_source_flags, Mapping):
        result["errors"].append("forbidden_source_flags must be a mapping")
    else:
        expected_keys = set(FORBIDDEN_SOURCE_FLAG_NAMES_V1)
        observed_keys = {_safe_str(key) for key in forbidden_source_flags.keys()}
        missing_flags = expected_keys - observed_keys
        extra_flags = observed_keys - expected_keys
        if missing_flags:
            result["errors"].append(f"missing forbidden source flags: {', '.join(sorted(missing_flags))}")
        if extra_flags:
            result["errors"].append(f"unknown forbidden source flags: {', '.join(sorted(extra_flags))}")
        true_flags: list[str] = []
        for key, raw in forbidden_source_flags.items():
            name = _safe_str(key)
            if name not in expected_keys:
                continue
            if not isinstance(raw, bool):
                result["errors"].append(f"forbidden source flag must be a boolean: {name}")
                continue
            if raw:
                true_flags.append(name)
                result["errors"].append(f"true forbidden source flag: {name}")
        if true_flags:
            result["blocked_labels"].extend(true_flags)

    variant_family_refs = packet.get("variant_family_refs")
    if not isinstance(variant_family_refs, list):
        result["errors"].append("variant_family_refs must be a real list of safe strings")
    else:
        seen: set[str] = set()
        for item in variant_family_refs:
            if not isinstance(item, str) or not item.strip():
                result["errors"].append("variant_family_refs must contain safe strings")
                break
            if item not in ALLOWED_VARIANT_FAMILIES_V1:
                result["errors"].append(f"unknown unsafe variant family: {item}")
            if item in seen:
                result["warnings"].append(f"duplicate variant family ref: {item}")
            seen.add(item)

    coverage_summary = packet.get("coverage_summary")
    if not isinstance(coverage_summary, Mapping):
        result["errors"].append("coverage_summary must be a mapping")
    else:
        required_coverage_keys = set(REQUIRED_COVERAGE_SUMMARY_FIELD_NAMES_V1)
        observed_coverage_keys = {_safe_str(key) for key in coverage_summary.keys()}
        missing_coverage = required_coverage_keys - observed_coverage_keys
        if missing_coverage:
            result["errors"].append(f"missing coverage summary fields: {', '.join(sorted(missing_coverage))}")
        if observed_coverage_keys - required_coverage_keys:
            # Extra safe metadata is allowed, but keys must still be safe and values JSON-safe.
            pass
        for key, raw in coverage_summary.items():
            name = _safe_str(key)
            if name in REQUIRED_COVERAGE_SUMMARY_FIELD_NAMES_V1:
                pass
            elif not _is_safe_metadata_key(name):
                result["errors"].append(f"unsafe coverage summary field: {name}")
            if not _is_json_safe_value(raw):
                result["errors"].append(f"coverage_summary must be JSON-safe: {name}")
            if _contains_forbidden_marker(raw):
                result["errors"].append(f"coverage_summary contains forbidden content: {name}")
            if _contains_authority_adjacent_key(raw):
                result["errors"].append(f"authority-adjacent coverage summary metadata not allowed: {name}")
        if isinstance(source_class_value, str) and coverage_summary.get("allowed_source_class") != source_class_value:
            result["errors"].append("coverage_summary.allowed_source_class must match allowed_source_class")
        if isinstance(packet.get("synthetic_only"), bool) and coverage_summary.get("synthetic_only") is not packet.get("synthetic_only"):
            result["errors"].append("coverage_summary.synthetic_only must match synthetic_only")
        if isinstance(packet.get("provenance_known"), bool) and coverage_summary.get("provenance_known") is not packet.get("provenance_known"):
            result["errors"].append("coverage_summary.provenance_known must match provenance_known")
        if isinstance(packet.get("safe_metadata"), bool) and coverage_summary.get("safe_metadata") is not packet.get("safe_metadata"):
            result["errors"].append("coverage_summary.safe_metadata must match safe_metadata")
        if isinstance(forbidden_source_flags, Mapping):
            true_count = sum(1 for value in forbidden_source_flags.values() if bool(value))
            if coverage_summary.get("blocked_flag_true_count") != true_count:
                result["errors"].append("coverage_summary.blocked_flag_true_count must match forbidden_source_flags")
        if isinstance(variant_family_refs, list) and coverage_summary.get("variant_family_ref_count") != len(variant_family_refs):
            result["errors"].append("coverage_summary.variant_family_ref_count must match variant_family_refs")
        if isinstance(packet.get("source_refs"), list) and coverage_summary.get("source_ref_count") != len(packet.get("source_refs")):
            result["errors"].append("coverage_summary.source_ref_count must match source_refs")
        if isinstance(packet.get("provenance_refs"), list) and coverage_summary.get("provenance_ref_count") != len(packet.get("provenance_refs")):
            result["errors"].append("coverage_summary.provenance_ref_count must match provenance_refs")
        if isinstance(packet.get("scenario_refs"), list) and coverage_summary.get("scenario_ref_count") != len(packet.get("scenario_refs")):
            result["errors"].append("coverage_summary.scenario_ref_count must match scenario_refs")

    extra_fields = set(packet.keys()) - PACKET_FIELD_NAMES_V1
    for field_name in extra_fields:
        if not _is_safe_metadata_key(field_name):
            result["errors"].append(f"unsafe extra metadata field: {field_name}")
        value = packet.get(field_name)
        if not _is_json_safe_value(value):
            result["errors"].append(f"extra metadata must be JSON-safe: {field_name}")
        if _contains_forbidden_marker(value):
            result["errors"].append(f"extra metadata contains forbidden content: {field_name}")
        if _contains_authority_adjacent_key(value):
            result["errors"].append(f"authority-adjacent metadata not allowed: {field_name}")

    if result["errors"]:
        result["status"] = VALIDATION_STATUS_INVALID_V1
        result["valid"] = False
        result["blocked_labels"] = sorted(set(result["blocked_labels"]))
        return result

    result["status"] = VALIDATION_STATUS_VALID_V1
    result["valid"] = True
    result["blocked_labels"] = []
    return result


def build_synthetic_speech_corpus_packet_v1(
    *,
    packet_id: Any,
    source_refs: Sequence[Any],
    provenance_refs: Sequence[Any],
    corpus_name: Any,
    corpus_scope: Any,
    variant_family_refs: Sequence[Any],
    scenario_refs: Sequence[Any] | None = None,
    allowed_source_class: Any,
    forbidden_source_flags: Mapping[str, Any] | None = None,
    coverage_summary: Mapping[str, Any] | None = None,
    synthetic_only: bool = True,
    provenance_known: bool = True,
    review_required: bool = True,
    no_private_user_audio: bool = True,
    no_hidden_recording: bool = True,
    no_biometric_dataset: bool = True,
    no_public_benchmark_claim: bool = True,
    no_authority_granted: bool = True,
    no_public_claim: bool = True,
    safe_metadata: bool = True,
    created_at: Any = None,
    created_by_ref: Any = None,
    related_packet_refs: Sequence[Any] | None = None,
    related_design_refs: Sequence[Any] | None = None,
    notes: Any = None,
    **extra_metadata: Any,
) -> dict[str, Any]:
    """Build a normalized synthetic speech corpus packet from safe metadata inputs."""

    normalized_source_refs = _normalize_string_list(source_refs, "source_refs", allow_empty=False)
    normalized_provenance_refs = _normalize_string_list(provenance_refs, "provenance_refs", allow_empty=False)
    normalized_variant_family_refs = _normalize_variant_family_refs(variant_family_refs)
    normalized_scenario_refs = _normalize_optional_string_list(scenario_refs, "scenario_refs") or []
    normalized_allowed_source_class = _normalize_allowed_source_class(allowed_source_class)
    normalized_forbidden_source_flags = _normalize_forbidden_source_flags(forbidden_source_flags)

    if not isinstance(synthetic_only, bool):
        raise ValueError("synthetic_only must be a boolean")
    if synthetic_only is not True:
        raise ValueError("synthetic_only must be true")
    if not isinstance(provenance_known, bool):
        raise ValueError("provenance_known must be a boolean")
    if provenance_known is not True:
        raise ValueError("provenance_known must be true")
    if not isinstance(review_required, bool):
        raise ValueError("review_required must be a boolean")
    if not isinstance(no_private_user_audio, bool):
        raise ValueError("no_private_user_audio must be a boolean")
    if no_private_user_audio is not True:
        raise ValueError("no_private_user_audio must be true")
    if not isinstance(no_hidden_recording, bool):
        raise ValueError("no_hidden_recording must be a boolean")
    if no_hidden_recording is not True:
        raise ValueError("no_hidden_recording must be true")
    if not isinstance(no_biometric_dataset, bool):
        raise ValueError("no_biometric_dataset must be a boolean")
    if no_biometric_dataset is not True:
        raise ValueError("no_biometric_dataset must be true")
    if not isinstance(no_public_benchmark_claim, bool):
        raise ValueError("no_public_benchmark_claim must be a boolean")
    if no_public_benchmark_claim is not True:
        raise ValueError("no_public_benchmark_claim must be true")
    if not isinstance(no_authority_granted, bool):
        raise ValueError("no_authority_granted must be a boolean")
    if no_authority_granted is not True:
        raise ValueError("no_authority_granted must be true")
    if not isinstance(no_public_claim, bool):
        raise ValueError("no_public_claim must be a boolean")
    if no_public_claim is not True:
        raise ValueError("no_public_claim must be true")
    if not isinstance(safe_metadata, bool):
        raise ValueError("safe_metadata must be a boolean")
    if safe_metadata is not True:
        raise ValueError("safe_metadata must be true")

    packet = {
        "packet_id": _normalize_string(packet_id, "packet_id"),
        "schema_version": PACKET_TYPE_V1,
        "source_refs": normalized_source_refs,
        "provenance_refs": normalized_provenance_refs,
        "corpus_name": _normalize_string(corpus_name, "corpus_name"),
        "corpus_scope": _normalize_string(corpus_scope, "corpus_scope"),
        "variant_family_refs": normalized_variant_family_refs,
        "scenario_refs": normalized_scenario_refs,
        "allowed_source_class": normalized_allowed_source_class,
        "forbidden_source_flags": normalized_forbidden_source_flags,
        "coverage_summary": _normalize_coverage_summary(
            source_refs=normalized_source_refs,
            provenance_refs=normalized_provenance_refs,
            variant_family_refs=normalized_variant_family_refs,
            scenario_refs=normalized_scenario_refs,
            allowed_source_class=normalized_allowed_source_class,
            forbidden_source_flags=normalized_forbidden_source_flags,
            synthetic_only=synthetic_only,
            provenance_known=provenance_known,
            safe_metadata=safe_metadata,
            value=coverage_summary,
        ),
        "synthetic_only": True,
        "provenance_known": True,
        "review_required": review_required,
        "no_private_user_audio": True,
        "no_hidden_recording": True,
        "no_biometric_dataset": True,
        "no_public_benchmark_claim": True,
        "no_authority_granted": True,
        "no_public_claim": True,
        "safe_metadata": True,
    }

    optional_fields = {
        "created_at": _normalize_optional_string(created_at, "created_at"),
        "created_by_ref": _normalize_optional_string(created_by_ref, "created_by_ref"),
        "related_packet_refs": _normalize_optional_string_list(related_packet_refs, "related_packet_refs"),
        "related_design_refs": _normalize_optional_string_list(related_design_refs, "related_design_refs"),
        "notes": _normalize_optional_string(notes, "notes"),
    }
    for key, value in optional_fields.items():
        if value is not None:
            packet[key] = value

    extras = _normalize_extra_metadata(extra_metadata)
    packet.update(extras)

    validation = _validate_packet_core(packet)
    if not validation["valid"]:
        raise ValueError("unsafe synthetic speech corpus packet inputs")
    return packet


def validate_synthetic_speech_corpus_packet_v1(packet: Any) -> dict[str, Any]:
    """Validate a synthetic speech corpus packet and return a structured verdict."""

    return _validate_packet_core(packet)


def summarize_synthetic_speech_corpus_packet_v1(packet: Any) -> dict[str, Any]:
    """Summarize a packet without implying authority or public claims."""

    validation = _validate_packet_core(packet)
    if not isinstance(packet, Mapping):
        return {
            "summary_type": "synthetic_speech_corpus_packet_summary_v1",
            "valid": False,
            "status": VALIDATION_STATUS_INVALID_V1,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "blocked_labels": validation["blocked_labels"],
        }

    source_refs = packet.get("source_refs") if isinstance(packet.get("source_refs"), list) else []
    provenance_refs = packet.get("provenance_refs") if isinstance(packet.get("provenance_refs"), list) else []
    scenario_refs = packet.get("scenario_refs") if isinstance(packet.get("scenario_refs"), list) else []
    variant_family_refs = packet.get("variant_family_refs") if isinstance(packet.get("variant_family_refs"), list) else []
    forbidden_source_flags = packet.get("forbidden_source_flags") if isinstance(packet.get("forbidden_source_flags"), Mapping) else {}
    coverage_summary = packet.get("coverage_summary") if isinstance(packet.get("coverage_summary"), Mapping) else {}

    return {
        "summary_type": "synthetic_speech_corpus_packet_summary_v1",
        "packet_id": _safe_str(packet.get("packet_id")),
        "schema_version": _safe_str(packet.get("schema_version")),
        "valid": validation["valid"],
        "status": validation["status"],
        "blocked_labels": list(validation["blocked_labels"]),
        "errors": list(validation["errors"]),
        "warnings": list(validation["warnings"]),
        "source_ref_count": len(source_refs),
        "provenance_ref_count": len(provenance_refs),
        "scenario_ref_count": len(scenario_refs),
        "variant_family_ref_count": len(variant_family_refs),
        "blocked_flag_true_count": sum(1 for value in forbidden_source_flags.values() if bool(value)),
        "allowed_source_class": _safe_str(packet.get("allowed_source_class")),
        "synthetic_only": bool(packet.get("synthetic_only")) is True,
        "provenance_known": bool(packet.get("provenance_known")) is True,
        "review_required": bool(packet.get("review_required")) is True,
        "no_authority_granted": bool(packet.get("no_authority_granted")) is True,
        "no_public_claim": bool(packet.get("no_public_claim")) is True,
        "safe_metadata": bool(packet.get("safe_metadata")) is True,
        "coverage_summary_keys": sorted(_safe_str(key) for key in coverage_summary.keys()),
    }


def to_synthetic_speech_corpus_json_safe_v1(packet: Any) -> Any:
    """Return a JSON-safe copy of the packet without mutating input."""

    validation = _validate_packet_core(packet)
    if not validation["valid"]:
        raise ValueError("unsafe synthetic speech corpus packet inputs")
    return _json_safe_copy(packet)


def render_synthetic_speech_corpus_markdown_v1(packet: Any) -> str:
    """Render a human-readable internal markdown summary."""

    validation = _validate_packet_core(packet)
    if not isinstance(packet, Mapping):
        return "\n".join(
            [
                "# Synthetic Speech Corpus Packet",
                "",
                "Status: INVALID",
                "",
                "- reason: packet must be a mapping",
            ]
        )

    summary = summarize_synthetic_speech_corpus_packet_v1(packet)
    lines = ["# Synthetic Speech Corpus Packet", "", f"Status: {'VALID' if validation['valid'] else 'INVALID'}"]
    lines.append(f"Packet ID: {summary['packet_id'] or 'unknown'}")
    lines.append(f"Schema Version: {summary['schema_version'] or 'unknown'}")
    lines.append(f"Allowed Source Class: {summary['allowed_source_class'] or 'unknown'}")
    lines.append(f"Synthetic Only: {summary['synthetic_only']}")
    lines.append(f"Provenance Known: {summary['provenance_known']}")
    lines.append(f"Review Required: {summary['review_required']}")
    lines.append(f"No Authority Granted: {summary['no_authority_granted']}")
    lines.append(f"No Public Claim: {summary['no_public_claim']}")
    lines.append(f"Safe Metadata: {summary['safe_metadata']}")
    lines.append("")
    lines.append("## Counts")
    lines.append(f"- source refs: {summary['source_ref_count']}")
    lines.append(f"- provenance refs: {summary['provenance_ref_count']}")
    lines.append(f"- scenario refs: {summary['scenario_ref_count']}")
    lines.append(f"- variant families: {summary['variant_family_ref_count']}")
    lines.append(f"- true forbidden flags: {summary['blocked_flag_true_count']}")
    if summary["coverage_summary_keys"]:
        lines.append("- coverage summary keys: " + ", ".join(summary["coverage_summary_keys"]))
    if summary["blocked_labels"]:
        lines.append("")
        lines.append("## Blocked Labels")
        for label in summary["blocked_labels"]:
            lines.append(f"- {label}")
    if validation["errors"]:
        lines.append("")
        lines.append("## Validation Errors")
        for error in validation["errors"]:
            lines.append(f"- {error}")
    if validation["warnings"]:
        lines.append("")
        lines.append("## Validation Warnings")
        for warning in validation["warnings"]:
            lines.append(f"- {warning}")
    lines.append("")
    lines.append("Internal use only. No public claim, benchmark claim, product-readiness claim, or authority claim.")
    return "\n".join(lines)


__all__ = [
    "ALLOWED_SOURCE_CLASSES_V1",
    "ALLOWED_VARIANT_FAMILIES_V1",
    "BLOCKED_SOURCE_CLASSES_V1",
    "FORBIDDEN_SOURCE_FLAG_NAMES_V1",
    "HELPER_TYPE_V1",
    "OPTIONAL_PACKET_FIELDS_V1",
    "PACKET_FIELD_NAMES_V1",
    "PACKET_TYPE_V1",
    "REQUIRED_COVERAGE_SUMMARY_FIELD_NAMES_V1",
    "REQUIRED_FORBIDDEN_SOURCE_FLAG_NAMES_V1",
    "REQUIRED_PACKET_FIELDS_V1",
    "RECOMMENDED_FORBIDDEN_SOURCE_FLAG_NAMES_V1",
    "build_synthetic_speech_corpus_packet_v1",
    "render_synthetic_speech_corpus_markdown_v1",
    "summarize_synthetic_speech_corpus_packet_v1",
    "to_synthetic_speech_corpus_json_safe_v1",
    "validate_synthetic_speech_corpus_packet_v1",
]
