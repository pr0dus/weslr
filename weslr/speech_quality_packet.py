"""Metadata-only helpers for the WESLR speech quality packet boundary v1.

This module is intentionally pure, deterministic, and fail-closed.
It normalizes safe metadata-only speech quality packets for future helper work.

It does not perform file I/O, network I/O, subprocess execution, microphone
access, audio processing, runtime voice recognition, speaker verification,
registry writes, .weslr writes, runtime wiring, or any public claims.
"""

from __future__ import annotations

import copy
import re
from typing import Any, Mapping, Sequence

HELPER_TYPE_V1 = "weslr_speech_quality_packet_helper_v1"
PACKET_TYPE_V1 = "speech_quality_packet_v1"

QUALITY_BANDS_V1 = {
    "unknown",
    "not_evaluated",
    "low",
    "medium",
    "high",
    "blocked",
    "requires_review",
}

QUALITY_BAND_FIELD_NAMES_V1 = {
    "top_1_command_accuracy_band",
    "top_2_candidate_usefulness_band",
    "false_positive_band",
    "false_negative_band",
    "rejection_quality_band",
    "command_family_confusion_band",
    "confidence_calibration_error_band",
    "noise_robustness_band",
    "accent_robustness_band",
    "multilingual_robustness_band",
    "replay_synthetic_voice_sensitivity_band",
    "operator_correction_band",
    "cymatics_usefulness_band",
    "cymatics_interpretability_band",
    "overtrust_risk_band",
    "privacy_leakage_risk_band",
}

ALLOWED_GAP_LABELS_V1 = {
    "feature_quality_gap",
    "preprocessing_gap",
    "command_vocabulary_gap",
    "command_confusion_gap",
    "false_positive_gap",
    "false_negative_gap",
    "rejection_gap",
    "calibration_gap",
    "noise_robustness_gap",
    "accent_robustness_gap",
    "multilingual_gap",
    "synthetic_voice_gap",
    "replay_gap",
    "cymatics_interpretability_gap",
    "operator_attention_gap",
    "overfit_risk",
    "unknown_gap",
}

BLOCKER_FIELD_NAMES_V1 = {
    "has_raw_audio",
    "has_microphone_access",
    "has_runtime_voice_event",
    "has_private_user_audio",
    "has_hidden_recording",
    "has_biometric_identity_claim",
    "has_speaker_verification_claim",
    "has_action_authority",
    "has_public_accuracy_claim",
    "has_model_provider_call",
    "has_weslr_write",
    "has_behavior_pack_promotion",
}

REQUIRED_PACKET_FIELDS_V1 = {
    "packet_id",
    "schema_version",
    "source_refs",
    "provenance_refs",
    "corpus_ref",
    "command_set_ref",
    "feature_pipeline_ref",
    "scenario_refs",
    "quality_scope",
    "quality_band_fields",
    "gap_labels",
    "blocker_fields",
    "synthetic_only",
    "review_required",
    "no_authority_granted",
    "no_public_claim",
    "safe_metadata",
}

OPTIONAL_PACKET_FIELDS_V1 = {
    "created_at",
    "created_by_ref",
    "related_review_refs",
    "related_design_refs",
    "notes",
}

PACKET_FIELD_NAMES_V1 = REQUIRED_PACKET_FIELDS_V1 | OPTIONAL_PACKET_FIELDS_V1
RESERVED_PACKET_FIELD_NAMES_V1 = PACKET_FIELD_NAMES_V1 | {"helper_type"}

SENSITIVE_KEY_HINTS_V1 = (
    "raw_audio",
    "raw_waveform",
    "audio_buffer",
    "microphone",
    "live_stream",
    "live audio",
    "transcript",
    "provider_output",
    "model_output",
    "hidden_runtime_event",
    "benchmark",
    "product_readiness",
    "certification",
    "authority",
    "public_accuracy",
    ".weslr",
    "voice",
    "speaker_verification",
    "speaker_verification_claim",
    "biometric_identity",
    "biometric_identity_claim",
    "action_authority",
    "action_authority_claim",
    "runtime_event",
    "live_stream",
    "hidden_recording",
    "private_user_audio",
    "model_provider_call",
    "weslr_write",
    "behavior_pack_promotion",
    "raw user",
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
}

AUTHORITY_ADJACENT_KEY_HINTS_V1 = tuple(sorted({
    re.sub(r"[^a-z0-9]+", "_", key).strip("_") for key in AUTHORITY_ADJACENT_METADATA_KEYS_V1
}))

FORBIDDEN_FIELD_MARKERS_V1 = (
    "raw waveform data",
    "audio buffers",
    "microphone handles",
    "live stream handles",
    "unredacted transcripts from real users",
    "provider output payloads",
    "model output payloads",
    "hidden runtime event logs",
    "public benchmark identifiers",
    "product-readiness claims",
    "certification claims",
    "authority-bearing claims",
)

VALIDATION_STATUS_VALID_V1 = "valid"
VALIDATION_STATUS_INVALID_V1 = "invalid"

JSON_SCALAR_TYPES_V1 = (str, int, float, bool, type(None))


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


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


def _normalize_key_token(value: Any) -> str:
    text = _safe_str(value).lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _contains_authority_adjacent_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
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
    if any(marker.replace(" ", "_") in lowered for marker in FORBIDDEN_FIELD_MARKERS_V1):
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


def _normalize_quality_band_fields(value: Any) -> dict[str, str]:
    mapping = value if isinstance(value, Mapping) else {}
    out = {name: "unknown" for name in sorted(QUALITY_BAND_FIELD_NAMES_V1)}
    for key, raw in mapping.items():
        name = _safe_str(key)
        if name not in QUALITY_BAND_FIELD_NAMES_V1:
            raise ValueError(f"unknown metric band field: {name}")
        band = _normalize_string(raw, name)
        if band not in QUALITY_BANDS_V1:
            raise ValueError(f"unsafe metric band for {name}: {band}")
        out[name] = band
    return out


def _normalize_blocker_fields(value: Any, extra_blockers: Mapping[str, Any] | None = None) -> dict[str, bool]:
    mapping: dict[str, Any] = {}
    if isinstance(value, Mapping):
        mapping.update(value)
    if extra_blockers:
        mapping.update(extra_blockers)

    out = {name: False for name in sorted(BLOCKER_FIELD_NAMES_V1)}
    for key, raw in mapping.items():
        name = _safe_str(key)
        if name not in BLOCKER_FIELD_NAMES_V1:
            raise ValueError(f"unknown blocker field: {name}")
        out[name] = bool(raw)
    return out


def _normalize_extra_metadata(extra_metadata: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, raw in extra_metadata.items():
        name = _safe_str(key)
        if not _is_safe_metadata_key(name):
            raise ValueError(f"unsafe extra metadata field: {name}")
        if name in PACKET_FIELD_NAMES_V1 or name == "helper_type":
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
        "status": VALIDATION_STATUS_INVALID_V1,
        "valid": False,
        "errors": [],
        "warnings": [],
        "blocked_labels": [],
        "packet_id": None,
        "schema_version": None,
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

    for field_name in (
        "source_refs",
        "provenance_refs",
        "scenario_refs",
        "related_review_refs",
        "related_design_refs",
    ):
        if field_name in packet:
            value = packet.get(field_name)
            if isinstance(value, (str, bytes)):
                result["errors"].append(f"{field_name} must be a real list of safe strings")
            elif not isinstance(value, (list, tuple, set, dict)) and value is not None:
                result["errors"].append(f"{field_name} must be a real list of safe strings")

    for field_name in ("corpus_ref", "command_set_ref", "feature_pipeline_ref", "quality_scope", "created_at", "created_by_ref", "notes"):
        if field_name in packet and packet.get(field_name) is not None and not isinstance(packet.get(field_name), JSON_SCALAR_TYPES_V1):
            if not _is_json_safe_value(packet.get(field_name)):
                result["errors"].append(f"{field_name} must be JSON-safe")

    if packet.get("synthetic_only") is not True:
        result["errors"].append("synthetic_only must be true")
    if packet.get("no_authority_granted") is not True:
        result["errors"].append("no_authority_granted must be true")
    if packet.get("no_public_claim") is not True:
        result["errors"].append("no_public_claim must be true")
    if packet.get("safe_metadata") is not True:
        result["errors"].append("safe_metadata must be true")

    blocker_fields = packet.get("blocker_fields")
    if not isinstance(blocker_fields, Mapping):
        result["errors"].append("blocker_fields must be a mapping")
    else:
        for name in BLOCKER_FIELD_NAMES_V1:
            if name not in blocker_fields:
                result["errors"].append(f"missing blocker field: {name}")
                break
        for key, raw in blocker_fields.items():
            if _safe_str(key) not in BLOCKER_FIELD_NAMES_V1:
                result["errors"].append(f"unknown blocker field: {_safe_str(key)}")
            if bool(raw):
                result["blocked_labels"].append(_safe_str(key))
                result["errors"].append(f"true blocker field: {_safe_str(key)}")

    quality_band_fields = packet.get("quality_band_fields")
    if not isinstance(quality_band_fields, Mapping):
        result["errors"].append("quality_band_fields must be a mapping")
    else:
        for name in QUALITY_BAND_FIELD_NAMES_V1:
            if name not in quality_band_fields:
                result["errors"].append(f"missing metric band field: {name}")
        for key, raw in quality_band_fields.items():
            name = _safe_str(key)
            if name not in QUALITY_BAND_FIELD_NAMES_V1:
                result["errors"].append(f"unknown metric band field: {name}")
                continue
            band = _safe_str(raw)
            if band not in QUALITY_BANDS_V1:
                result["errors"].append(f"unsafe metric band for {name}: {band}")

    gap_labels = packet.get("gap_labels")
    if not isinstance(gap_labels, list):
        result["errors"].append("gap_labels must be a real list of safe strings")
    else:
        seen: set[str] = set()
        for label in gap_labels:
            text = _safe_str(label)
            if not text:
                result["errors"].append("gap_labels contains empty label")
                continue
            if text not in ALLOWED_GAP_LABELS_V1:
                result["errors"].append(f"unsafe gap label: {text}")
            if text in seen:
                result["warnings"].append(f"duplicate gap label: {text}")
            seen.add(text)

    for field_name in ("source_refs", "provenance_refs", "scenario_refs", "related_review_refs", "related_design_refs"):
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

    for field_name in ("corpus_ref", "command_set_ref", "feature_pipeline_ref", "quality_scope", "created_at", "created_by_ref", "notes"):
        if field_name in packet and packet.get(field_name) is not None:
            value = packet.get(field_name)
            if isinstance(value, str):
                if not value.strip():
                    result["errors"].append(f"{field_name} must be a non-empty safe string")
                elif _contains_forbidden_marker(value):
                    result["errors"].append(f"{field_name} contains forbidden content")
            elif not _is_json_safe_value(value):
                result["errors"].append(f"{field_name} must be JSON-safe")

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


def build_speech_quality_packet_v1(
    *,
    packet_id: Any,
    source_refs: Sequence[Any],
    provenance_refs: Sequence[Any],
    corpus_ref: Any,
    command_set_ref: Any,
    feature_pipeline_ref: Any,
    scenario_refs: Sequence[Any] | None = None,
    quality_scope: Any = "speech_quality_metadata",
    quality_band_fields: Mapping[str, Any] | None = None,
    gap_labels: Sequence[Any] | None = None,
    blocker_fields: Mapping[str, Any] | None = None,
    synthetic_only: bool = True,
    review_required: bool = True,
    no_authority_granted: bool = True,
    no_public_claim: bool = True,
    safe_metadata: bool = True,
    created_at: Any = None,
    created_by_ref: Any = None,
    related_review_refs: Sequence[Any] | None = None,
    related_design_refs: Sequence[Any] | None = None,
    notes: Any = None,
    **extra_metadata: Any,
) -> dict[str, Any]:
    """Build a normalized speech-quality packet from safe metadata inputs."""

    blocker_merge: dict[str, Any] = {}
    normalized_extra: dict[str, Any] = {}
    for key, value in extra_metadata.items():
        name = _safe_str(key)
        if name == "schema_version":
            if _safe_str(value) != PACKET_TYPE_V1:
                raise ValueError("schema_version must equal speech_quality_packet_v1")
            continue
        if name in BLOCKER_FIELD_NAMES_V1:
            blocker_merge[name] = value
        else:
            normalized_extra[key] = value

    packet = {
        "packet_id": _normalize_string(packet_id, "packet_id"),
        "schema_version": PACKET_TYPE_V1,
        "source_refs": _normalize_string_list(source_refs, "source_refs", allow_empty=False),
        "provenance_refs": _normalize_string_list(provenance_refs, "provenance_refs", allow_empty=False),
        "corpus_ref": _normalize_string(corpus_ref, "corpus_ref"),
        "command_set_ref": _normalize_string(command_set_ref, "command_set_ref"),
        "feature_pipeline_ref": _normalize_string(feature_pipeline_ref, "feature_pipeline_ref"),
        "scenario_refs": _normalize_string_list(scenario_refs, "scenario_refs"),
        "quality_scope": _normalize_string(quality_scope, "quality_scope"),
        "quality_band_fields": _normalize_quality_band_fields(quality_band_fields),
        "gap_labels": _normalize_string_list(gap_labels, "gap_labels"),
        "blocker_fields": _normalize_blocker_fields(blocker_fields, blocker_merge),
        "synthetic_only": bool(synthetic_only) is True,
        "review_required": bool(review_required) is True,
        "no_authority_granted": bool(no_authority_granted) is True,
        "no_public_claim": bool(no_public_claim) is True,
        "safe_metadata": bool(safe_metadata) is True,
    }

    if packet["synthetic_only"] is not True:
        raise ValueError("synthetic_only must be true")
    if packet["no_authority_granted"] is not True:
        raise ValueError("no_authority_granted must be true")
    if packet["no_public_claim"] is not True:
        raise ValueError("no_public_claim must be true")
    if packet["safe_metadata"] is not True:
        raise ValueError("safe_metadata must be true")

    optional_fields = {
        "created_at": _normalize_optional_string(created_at, "created_at"),
        "created_by_ref": _normalize_optional_string(created_by_ref, "created_by_ref"),
        "related_review_refs": _normalize_optional_string_list(related_review_refs, "related_review_refs"),
        "related_design_refs": _normalize_optional_string_list(related_design_refs, "related_design_refs"),
        "notes": _normalize_optional_string(notes, "notes"),
    }
    for key, value in optional_fields.items():
        if value is not None:
            packet[key] = value

    extras = _normalize_extra_metadata(normalized_extra)
    packet.update(extras)

    validation = _validate_packet_core(packet)
    if not validation["valid"]:
        raise ValueError("unsafe speech quality packet inputs")
    return packet


def validate_speech_quality_packet_v1(packet: Any) -> dict[str, Any]:
    """Validate a speech-quality packet and return a structured verdict."""

    return _validate_packet_core(packet)


def summarize_speech_quality_packet_v1(packet: Any) -> dict[str, Any]:
    """Summarize a packet without implying authority or public claims."""

    validation = _validate_packet_core(packet)
    if not isinstance(packet, Mapping):
        return {
            "summary_type": "speech_quality_packet_summary_v1",
            "valid": False,
            "status": VALIDATION_STATUS_INVALID_V1,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "blocked_labels": validation["blocked_labels"],
        }

    band_fields = packet.get("quality_band_fields") if isinstance(packet.get("quality_band_fields"), Mapping) else {}
    gap_labels = packet.get("gap_labels") if isinstance(packet.get("gap_labels"), list) else []
    source_refs = packet.get("source_refs") if isinstance(packet.get("source_refs"), list) else []
    provenance_refs = packet.get("provenance_refs") if isinstance(packet.get("provenance_refs"), list) else []
    scenario_refs = packet.get("scenario_refs") if isinstance(packet.get("scenario_refs"), list) else []
    blockers = packet.get("blocker_fields") if isinstance(packet.get("blocker_fields"), Mapping) else {}

    return {
        "summary_type": "speech_quality_packet_summary_v1",
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
        "gap_label_count": len(gap_labels),
        "quality_band_count": len(band_fields),
        "blocker_true_count": sum(1 for value in blockers.values() if bool(value)),
        "no_authority_granted": bool(packet.get("no_authority_granted")) is True,
        "no_public_claim": bool(packet.get("no_public_claim")) is True,
        "safe_metadata": bool(packet.get("safe_metadata")) is True,
        "review_required": bool(packet.get("review_required")) is True,
    }


def to_speech_quality_packet_json_safe_v1(packet: Any) -> Any:
    """Return a JSON-safe copy of the packet without mutating input."""

    validation = _validate_packet_core(packet)
    if not validation["valid"]:
        raise ValueError("unsafe speech quality packet inputs")
    return _json_safe_copy(packet)


def render_speech_quality_packet_markdown_v1(packet: Any) -> str:
    """Render a human-readable internal markdown summary."""

    validation = _validate_packet_core(packet)
    if not isinstance(packet, Mapping):
        return "\n".join(
            [
                "# Speech Quality Packet",
                "",
                "Status: INVALID",
                "",
                "- reason: packet must be a mapping",
            ]
        )

    summary = summarize_speech_quality_packet_v1(packet)
    lines = ["# Speech Quality Packet", "", f"Status: {'VALID' if validation['valid'] else 'INVALID'}"]
    lines.append(f"Packet ID: {summary['packet_id'] or 'unknown'}")
    lines.append(f"Schema Version: {summary['schema_version'] or 'unknown'}")
    lines.append(f"Synthetic Only: {bool(packet.get('synthetic_only'))}")
    lines.append(f"No Authority Granted: {bool(packet.get('no_authority_granted'))}")
    lines.append(f"No Public Claim: {bool(packet.get('no_public_claim'))}")
    lines.append(f"Safe Metadata: {bool(packet.get('safe_metadata'))}")
    lines.append("")
    lines.append("## Counts")
    lines.append(f"- source refs: {summary['source_ref_count']}")
    lines.append(f"- provenance refs: {summary['provenance_ref_count']}")
    lines.append(f"- scenario refs: {summary['scenario_ref_count']}")
    lines.append(f"- gap labels: {summary['gap_label_count']}")
    lines.append(f"- quality bands: {summary['quality_band_count']}")
    lines.append(f"- true blockers: {summary['blocker_true_count']}")
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
    "ALLOWED_GAP_LABELS_V1",
    "BLOCKER_FIELD_NAMES_V1",
    "HELPER_TYPE_V1",
    "PACKET_TYPE_V1",
    "QUALITY_BANDS_V1",
    "QUALITY_BAND_FIELD_NAMES_V1",
    "REQUIRED_PACKET_FIELDS_V1",
    "OPTIONAL_PACKET_FIELDS_V1",
    "build_speech_quality_packet_v1",
    "render_speech_quality_packet_markdown_v1",
    "summarize_speech_quality_packet_v1",
    "to_speech_quality_packet_json_safe_v1",
    "validate_speech_quality_packet_v1",
]
