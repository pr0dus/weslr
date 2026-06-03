"""Metadata-only helpers for WESLR MFCC feature-quality analysis v1.

This module is intentionally pure, deterministic, import-safe, and fail-closed.
It only handles metadata for future speech-recognition quality and
cymatics/signal-display analysis. It does not perform audio processing,
microphone access, runtime wiring, file I/O, network I/O, model/provider
calls, search/advisor calls, or any authority-granting behavior.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping

HELPER_TYPE_V1 = "mfcc_feature_quality_metadata_helper_v1"
PACKET_SCHEMA_VERSION_V1 = "mfcc_feature_quality_metadata_packet_v1"
PACKET_VALIDATION_STATUS_VALID_V1 = "valid"
PACKET_VALIDATION_STATUS_INVALID_V1 = "invalid"

SAFE_SOURCE_TYPE_CLASSES_V1 = {
    "synthetic_metadata",
    "public_open_text_metadata",
    "internal_metadata",
    "operator_supplied_metadata",
    "unknown_safe_metadata",
}

SAFE_DATASET_PROVENANCE_CLASSES_V1 = {
    "synthetic_metadata",
    "public_open_text_metadata",
    "internal_metadata",
    "operator_supplied_metadata",
    "unknown_safe_metadata",
}

SAFE_FEATURE_FAMILY_LABELS_V1 = {
    "mfcc",
    "delta",
    "delta_delta",
    "spectral_metadata",
    "chroma_metadata",
    "cymatics_display_metadata",
}

SAFE_QUALITY_DIMENSION_KEYS_V1 = {
    "completeness",
    "stability",
    "frame_window_consistency",
    "feature_availability",
    "noise_condition_label",
    "language_command_domain_label",
    "synthetic_accent_noise_test_condition_label",
    "synthetic_accent_noise_condition_label",
    "command_set_coverage",
    "expected_vs_observed_recognition_metadata",
    "error_category_label",
    "confidence_calibration_metadata",
    "cymatics_display_usefulness_label",
    "cymatics_display_interpretability_label",
}

SAFE_RECOGNITION_QUALITY_KEYS_V1 = {
    "calibration",
    "false_accept_labels",
    "false_reject_labels",
    "command_ambiguity_labels",
    "noise_robustness_labels",
    "multilingual_accent_condition_labels",
    "quality_notes",
    "observed_quality_notes",
}

SAFE_CYMATICS_USEFULNESS_KEYS_V1 = {
    "visual_expressiveness",
    "diagnostic_usefulness",
    "feature_gap_diagnosis",
    "noise_diagnosis",
    "rhythm_diagnosis",
    "emphasis_diagnosis",
    "command_instability_diagnosis",
    "interpretability_label",
    "no_real_time_wiring",
}

DENIED_AUTHORITY_FIELDS_V1 = {
    "runtime_authority",
    "microphone_authority",
    "audio_processing_authority",
    "raw_audio_storage_authority",
    "speaker_verification_authority",
    "voice_template_authority",
    "identity_authority",
    "benchmark_claim_authority",
    "public_accuracy_claim_authority",
    "product_readiness_authority",
    "certification_authority",
    "model_provider_authority",
    "memory_write_authority",
    "behavior_pack_promotion_authority",
}

# Canonical token hints for key/alias matching.
_DENIED_AUTHORITY_TOKEN_HINTS_V1 = {
    "runtimeauthority",
    "microphoneauthority",
    "audioprocessingauthority",
    "rawaudiostorageauthority",
    "speakerverificationauthority",
    "voicetemplateauthority",
    "identityauthority",
    "benchmarkclaimauthority",
    "publicaccuracyclaimauthority",
    "productreadinessauthority",
    "certificationauthority",
    "modelproviderauthority",
    "memorywriteauthority",
    "behaviorpackpromotionauthority",
    "runtimeauthoritygranted",
    "microphoneauthoritygranted",
    "audioprocessingauthoritygranted",
    "rawaudiostorageauthoritygranted",
    "speakerverificationauthoritygranted",
    "voicetemplateauthoritygranted",
    "identityauthoritygranted",
    "benchmarkclaimauthoritygranted",
    "publicaccuracyclaimauthoritygranted",
    "productreadinessauthoritygranted",
    "certificationauthoritygranted",
    "modelproviderauthoritygranted",
    "memorywriteauthoritygranted",
    "behaviorpackpromotionauthoritygranted",
    "runtimeauthorityfalse",
    "microphoneauthorityfalse",
    "audioprocessingauthorityfalse",
    "rawaudiostorageauthorityfalse",
    "speakerverificationauthorityfalse",
    "voicetemplateauthorityfalse",
    "identityauthorityfalse",
    "benchmarkclaimauthorityfalse",
    "publicaccuracyclaimauthorityfalse",
    "productreadinessauthorityfalse",
    "certificationauthorityfalse",
    "modelproviderauthorityfalse",
    "memorywriteauthorityfalse",
    "behaviorpackpromotionauthorityfalse",
}

UNSAFE_KEY_TOKEN_HINTS_V1 = {
    "rawaudio",
    "waveform",
    "audiobytes",
    "audiofile",
    "audiofilepath",
    "audiourl",
    "microphonedevice",
    "hidderecording",
    "speakeridentity",
    "speakerverification",
    "voicetemplate",
    "biometric",
    "voiceprint",
    "benchmarkclaim",
    "publicaccuracy",
    "productionclaim",
    "certificationclaim",
    "modelproviderresult",
    "runtimemicrophone",
    "rawtranscript",
    "privateaudio",
    "privatevoice",
    "voiceverified",
    "identityverified",
    "approvedbyvoice",
    "accountaccessrestored",
    "voiceapproval",
}

UNSAFE_VALUE_TOKEN_HINTS_V1 = {
    "rawaudio",
    "waveform",
    "audiobytes",
    "audiofile",
    "audiourl",
    "microphone",
    "hiddenrecording",
    "speakeridentity",
    "speakerverification",
    "voicetemplate",
    "biometric",
    "voiceprint",
    "benchmarkclaim",
    "publicaccuracy",
    "productionclaim",
    "certificationclaim",
    "modelproviderresult",
    "runtimemicrophone",
    "rawtranscript",
    "privateaudio",
    "privatevoice",
    "voiceverified",
    "identityverified",
    "approvedbyvoice",
    "accountaccessrestored",
    "voiceapproval",
}

UNSAFE_FILE_EXTENSIONS_V1 = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus"}
UNSAFE_URL_SCHEMES_V1 = ("http://", "https://", "ftp://", "file://", "content://")

PACKET_FIELD_NAMES_V1 = {
    "helper_type",
    "schema_version",
    "packet_id",
    "source_type_classification",
    "dataset_provenance_class",
    "feature_family_metadata",
    "quality_dimensions",
    "cymatics_usefulness_metadata",
    "recognition_quality_metadata",
    "internal_only",
    "non_authoritative",
    "validation_status",
    "validation_errors",
    "blocked_reasons",
    "denied_authority_fields",
    *DENIED_AUTHORITY_FIELDS_V1,
}

JSON_SCALAR_TYPES_V1 = (str, int, float, bool)


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
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe_copy(raw) for key, raw in value.items()}
    if isinstance(value, list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, set):
        return [_json_safe_copy(item) for item in sorted(value, key=lambda item: _safe_str(item))]
    if _is_json_safe_scalar(value):
        return value
    raise ValueError(f"value is not JSON-safe: {type(value).__name__}")


def _contains_unsafe_file_or_url(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith(UNSAFE_URL_SCHEMES_V1):
        return True
    if any(ext in lowered for ext in UNSAFE_FILE_EXTENSIONS_V1):
        return True
    if lowered.endswith(tuple(UNSAFE_FILE_EXTENSIONS_V1)):
        return True
    return False


def _contains_unsafe_token(value: Any, token_hints: set[str]) -> bool:
    if isinstance(value, Mapping):
        return any(
            _contains_unsafe_token(key, token_hints) or _contains_unsafe_token(raw, token_hints)
            for key, raw in value.items()
        )
    if isinstance(value, (list, tuple, set)):
        return any(_contains_unsafe_token(item, token_hints) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        normalized = _normalize_token(value)
        return _contains_unsafe_file_or_url(value) or any(
            hint in lowered or hint in normalized for hint in token_hints
        )
    return False


def _is_safe_metadata_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    key_text = _safe_str(key)
    if not key_text or key_text.startswith("_"):
        return False
    normalized = _normalize_token(key_text)
    if normalized in _DENIED_AUTHORITY_TOKEN_HINTS_V1:
        return False
    if normalized in UNSAFE_KEY_TOKEN_HINTS_V1:
        return False
    if any(fragment in key_text.lower() for fragment in ("raw_audio", "speaker_verified", "voice_verified", "identity_verified", "benchmark_claim", "public_accuracy_claim", "production_claim", "certification_claim", "model_provider_result")):
        return False
    return True


def _normalize_list_of_strings(value: Any, field_name: str, *, allow_empty: bool = True, allowed_values: set[str] | None = None) -> list[str]:
    if value is None:
        items: Iterable[Any] = []
    elif isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a real list of safe strings")
    elif isinstance(value, dict):
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
        if _contains_unsafe_token(text, UNSAFE_VALUE_TOKEN_HINTS_V1):
            raise ValueError(f"{field_name} contains forbidden content")
        if allowed_values is not None and text not in allowed_values:
            raise ValueError(f"{field_name} contains unsafe label: {text}")
        if text not in seen:
            out.append(text)
            seen.add(text)

    if not out and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return out


def _normalize_safe_mapping(value: Any, field_name: str, *, allowed_keys: set[str] | None = None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    out: dict[str, Any] = {}
    for key, raw in value.items():
        name = _safe_str(key)
        if not _is_safe_metadata_key(name):
            raise ValueError(f"unsafe metadata field: {name}")
        if name in PACKET_FIELD_NAMES_V1:
            raise ValueError(f"reserved packet field cannot be used as metadata: {name}")
        if allowed_keys is not None and name not in allowed_keys:
            raise ValueError(f"unsafe metadata field: {name}")
        if _contains_unsafe_token(raw, UNSAFE_VALUE_TOKEN_HINTS_V1):
            raise ValueError(f"{field_name} contains forbidden content")
        out[name] = _json_safe_copy(raw)
    return out


def _default_denied_authority_fields() -> dict[str, bool]:
    return {name: False for name in sorted(DENIED_AUTHORITY_FIELDS_V1)}


def _canonical_packet_id(source_type_classification: str, dataset_provenance_class: str, feature_family_metadata: list[str]) -> str:
    basis = "|".join(
        [
            PACKET_SCHEMA_VERSION_V1,
            source_type_classification,
            dataset_provenance_class,
            ",".join(feature_family_metadata),
        ]
    )
    token = _normalize_token(basis)
    return f"mfcc-feature-quality-{token[:24] or 'packet'}"


def build_mfcc_feature_quality_packet_v1(
    *,
    packet_id: str | None = None,
    source_type_classification: str,
    dataset_provenance_class: str,
    feature_family_metadata: Iterable[Any] | None = None,
    quality_dimensions: Mapping[str, Any] | None = None,
    cymatics_usefulness_metadata: Mapping[str, Any] | None = None,
    recognition_quality_metadata: Mapping[str, Any] | None = None,
    denied_authority_fields: Mapping[str, Any] | None = None,
    internal_only: bool = True,
    non_authoritative: bool = True,
    validation_status: str | None = None,
    validation_errors: Iterable[Any] | None = None,
    blocked_reasons: Iterable[Any] | None = None,
    **extra_metadata: Any,
) -> dict[str, Any]:
    source = _safe_str(source_type_classification)
    provenance = _safe_str(dataset_provenance_class)
    if source not in SAFE_SOURCE_TYPE_CLASSES_V1:
        raise ValueError(f"unsafe source_type_classification: {source}")
    if provenance not in SAFE_DATASET_PROVENANCE_CLASSES_V1:
        raise ValueError(f"unsafe dataset_provenance_class: {provenance}")

    families = _normalize_list_of_strings(
        feature_family_metadata or [],
        "feature_family_metadata",
        allow_empty=False,
        allowed_values=SAFE_FEATURE_FAMILY_LABELS_V1,
    )

    packet = {
        "helper_type": HELPER_TYPE_V1,
        "schema_version": PACKET_SCHEMA_VERSION_V1,
        "packet_id": _safe_str(packet_id) if packet_id is not None else _canonical_packet_id(source, provenance, families),
        "source_type_classification": source,
        "dataset_provenance_class": provenance,
        "feature_family_metadata": families,
        "quality_dimensions": _normalize_safe_mapping(quality_dimensions or {}, "quality_dimensions", allowed_keys=SAFE_QUALITY_DIMENSION_KEYS_V1),
        "cymatics_usefulness_metadata": _normalize_safe_mapping(
            cymatics_usefulness_metadata or {},
            "cymatics_usefulness_metadata",
            allowed_keys=SAFE_CYMATICS_USEFULNESS_KEYS_V1,
        ),
        "recognition_quality_metadata": _normalize_safe_mapping(
            recognition_quality_metadata or {},
            "recognition_quality_metadata",
            allowed_keys=SAFE_RECOGNITION_QUALITY_KEYS_V1,
        ),
        "denied_authority_fields": _default_denied_authority_fields(),
        "internal_only": bool(internal_only),
        "non_authoritative": bool(non_authoritative),
        "validation_status": _safe_str(validation_status) if validation_status else PACKET_VALIDATION_STATUS_VALID_V1,
        "validation_errors": _normalize_list_of_strings(validation_errors or [], "validation_errors"),
        "blocked_reasons": _normalize_list_of_strings(blocked_reasons or [], "blocked_reasons"),
    }

    if not packet["packet_id"]:
        raise ValueError("packet_id must be a non-empty safe string")
    if _contains_unsafe_token(packet["packet_id"], UNSAFE_VALUE_TOKEN_HINTS_V1):
        raise ValueError("packet_id contains forbidden content")
    if packet["internal_only"] is not True:
        raise ValueError("internal_only must be true")
    if packet["non_authoritative"] is not True:
        raise ValueError("non_authoritative must be true")

    denied = denied_authority_fields or {}
    if not isinstance(denied, Mapping):
        raise ValueError("denied_authority_fields must be a mapping")
    for name in DENIED_AUTHORITY_FIELDS_V1:
        raw = denied.get(name, False)
        if not isinstance(raw, bool):
            raise ValueError(f"denied authority field {name} must be boolean false")
        if raw is not False:
            raise ValueError(f"denied authority field {name} must be false")
        packet[name] = False
        packet["denied_authority_fields"][name] = False

    if extra_metadata:
        for key, raw in extra_metadata.items():
            name = _safe_str(key)
            if not _is_safe_metadata_key(name):
                raise ValueError(f"unsafe metadata field: {name}")
            if name in PACKET_FIELD_NAMES_V1:
                raise ValueError(f"reserved packet field cannot be used as metadata: {name}")
            if _contains_unsafe_token(raw, UNSAFE_VALUE_TOKEN_HINTS_V1):
                raise ValueError(f"{name} contains forbidden content")
            packet[name] = _json_safe_copy(raw)

    validation = validate_mfcc_feature_quality_packet_v1(packet)
    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]) or "mfcc feature quality packet validation failed")
    return packet


def _scan_packet_for_unsafe_metadata(packet: Any, *, path: str = "packet") -> list[str]:
    findings: list[str] = []

    if isinstance(packet, Mapping):
        for key, raw in packet.items():
            key_text = _safe_str(key)
            normalized = _normalize_token(key_text)
            is_authority_field = key_text in DENIED_AUTHORITY_FIELDS_V1 and (
                path == "packet" or path.endswith(".denied_authority_fields")
            )
            if not is_authority_field and not _is_safe_metadata_key(key_text):
                findings.append(f"unsafe metadata field at {path}: {key_text or '<non-string-key>'}")
            if not is_authority_field and (normalized in _DENIED_AUTHORITY_TOKEN_HINTS_V1 or normalized in UNSAFE_KEY_TOKEN_HINTS_V1):
                findings.append(f"authority-adjacent metadata field at {path}: {key_text or '<non-string-key>'}")
            findings.extend(_scan_packet_for_unsafe_metadata(raw, path=f"{path}.{key_text}" if key_text else path))
        return findings

    if isinstance(packet, (list, tuple, set)):
        for idx, item in enumerate(packet):
            findings.extend(_scan_packet_for_unsafe_metadata(item, path=f"{path}[{idx}]"))
        return findings

    if isinstance(packet, str):
        lowered = packet.lower()
        normalized = _normalize_token(packet)
        if _contains_unsafe_file_or_url(packet):
            findings.append(f"unsafe audio reference at {path}")
        elif any(hint in lowered or hint in normalized for hint in UNSAFE_VALUE_TOKEN_HINTS_V1):
            findings.append(f"unsafe metadata content at {path}")
    return findings


def validate_mfcc_feature_quality_packet_v1(packet: Any) -> dict[str, Any]:
    result = {
        "helper_type": HELPER_TYPE_V1,
        "schema_version": PACKET_SCHEMA_VERSION_V1,
        "packet_id": None,
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

    packet_id = _safe_str(packet.get("packet_id"))
    result["packet_id"] = packet_id or None

    required_fields = (
        "helper_type",
        "schema_version",
        "packet_id",
        "source_type_classification",
        "dataset_provenance_class",
        "feature_family_metadata",
        "quality_dimensions",
        "cymatics_usefulness_metadata",
        "recognition_quality_metadata",
        "internal_only",
        "non_authoritative",
        "validation_status",
        "validation_errors",
        "blocked_reasons",
        "denied_authority_fields",
        *sorted(DENIED_AUTHORITY_FIELDS_V1),
    )
    missing = [name for name in required_fields if name not in packet]
    if missing:
        result["errors"].append(f"missing required fields: {', '.join(missing)}")
        result["blocked_reasons"].append("missing_required_fields")

    if _safe_str(packet.get("helper_type")) != HELPER_TYPE_V1:
        result["errors"].append(f"helper_type must equal {HELPER_TYPE_V1}")
    if _safe_str(packet.get("schema_version")) != PACKET_SCHEMA_VERSION_V1:
        result["errors"].append(f"schema_version must equal {PACKET_SCHEMA_VERSION_V1}")
    if not packet_id:
        result["errors"].append("packet_id must be a non-empty safe string")
    elif _contains_unsafe_token(packet_id, UNSAFE_VALUE_TOKEN_HINTS_V1):
        result["errors"].append("packet_id contains forbidden content")

    source = _safe_str(packet.get("source_type_classification"))
    provenance = _safe_str(packet.get("dataset_provenance_class"))
    if source not in SAFE_SOURCE_TYPE_CLASSES_V1:
        result["errors"].append("unsafe source_type_classification")
    if provenance not in SAFE_DATASET_PROVENANCE_CLASSES_V1:
        result["errors"].append("unsafe dataset_provenance_class")

    result["internal_only"] = packet.get("internal_only") is True
    result["non_authoritative"] = packet.get("non_authoritative") is True
    if packet.get("internal_only") is not True:
        result["errors"].append("internal_only must be true")
    if packet.get("non_authoritative") is not True:
        result["errors"].append("non_authoritative must be true")

    feature_families = packet.get("feature_family_metadata")
    if not isinstance(feature_families, list):
        result["errors"].append("feature_family_metadata must be a real list of safe strings")
    else:
        seen: set[str] = set()
        for item in feature_families:
            text = _safe_str(item)
            if not text:
                result["errors"].append("feature_family_metadata contains empty value")
                continue
            if text not in SAFE_FEATURE_FAMILY_LABELS_V1:
                result["errors"].append(f"unsafe feature family label: {text}")
            if text in seen:
                result["warnings"].append(f"duplicate feature family label: {text}")
            seen.add(text)

    for field_name, allowed_keys in (
        ("quality_dimensions", SAFE_QUALITY_DIMENSION_KEYS_V1),
        ("cymatics_usefulness_metadata", SAFE_CYMATICS_USEFULNESS_KEYS_V1),
        ("recognition_quality_metadata", SAFE_RECOGNITION_QUALITY_KEYS_V1),
    ):
        value = packet.get(field_name)
        if not isinstance(value, Mapping):
            result["errors"].append(f"{field_name} must be a mapping")
            continue
        for key, raw in value.items():
            name = _safe_str(key)
            if not _is_safe_metadata_key(name):
                result["errors"].append(f"unsafe metadata field: {name}")
                continue
            if name in PACKET_FIELD_NAMES_V1:
                result["errors"].append(f"reserved packet field cannot be used as metadata: {name}")
                continue
            if allowed_keys is not None and name not in allowed_keys:
                # Unknown-but-safe metadata is allowed; unknown unsafe metadata is blocked above.
                pass
            if _contains_unsafe_token(raw, UNSAFE_VALUE_TOKEN_HINTS_V1):
                result["errors"].append(f"{field_name} contains forbidden content")
            if not _is_json_safe_scalar(raw) and not isinstance(raw, (list, tuple, set, Mapping)):
                result["errors"].append(f"{field_name} must be JSON-safe")

    denied_fields = packet.get("denied_authority_fields")
    if not isinstance(denied_fields, Mapping):
        result["errors"].append("denied_authority_fields must be a mapping")
    else:
        for name in DENIED_AUTHORITY_FIELDS_V1:
            if name not in denied_fields:
                result["errors"].append(f"missing denied authority field: {name}")
                result["blocked_reasons"].append(name)
                continue
            raw = denied_fields.get(name)
            if not isinstance(raw, bool):
                result["errors"].append(f"denied authority field {name} must be boolean false")
                result["blocked_reasons"].append(name)
            elif raw is not False:
                result["errors"].append(f"denied authority field {name} must be false")
                result["blocked_reasons"].append(name)
            if packet.get(name) is not False:
                result["errors"].append(f"top-level denied authority field {name} must be false")
                result["blocked_reasons"].append(name)

    extra_scans = _scan_packet_for_unsafe_metadata(packet)
    if extra_scans:
        for finding in extra_scans:
            if finding not in result["errors"]:
                result["errors"].append(finding)
                result["blocked_reasons"].append("unsafe_metadata")

    # Keep blocked reasons stable and safe.
    deduped_blocked: list[str] = []
    seen_blocked: set[str] = set()
    for label in result["blocked_reasons"]:
        text = _safe_str(label)
        if text and text not in seen_blocked:
            deduped_blocked.append(text)
            seen_blocked.add(text)
    result["blocked_reasons"] = deduped_blocked

    result["valid"] = not result["errors"]
    result["status"] = PACKET_VALIDATION_STATUS_VALID_V1 if result["valid"] else PACKET_VALIDATION_STATUS_INVALID_V1
    return result


def to_mfcc_feature_quality_json_safe_v1(packet: Any) -> Any:
    """Return a JSON-safe copy without laundering invalid packets into validity."""
    if not isinstance(packet, Mapping):
        raise ValueError("packet must be a mapping")
    return _json_safe_copy(packet)


def summarize_mfcc_feature_quality_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_mfcc_feature_quality_packet_v1(packet)
    packet_map = packet if isinstance(packet, Mapping) else {}
    summary = {
        "helper_type": HELPER_TYPE_V1,
        "schema_version": PACKET_SCHEMA_VERSION_V1,
        "packet_id": _safe_str(packet_map.get("packet_id")) or None,
        "status": validation["status"],
        "valid": validation["valid"],
        "errors": list(validation["errors"]),
        "warnings": list(validation["warnings"]),
        "blocked_reasons": list(validation["blocked_reasons"]),
        "internal_only": packet_map.get("internal_only") is True,
        "non_authoritative": packet_map.get("non_authoritative") is True,
        "source_type_classification": _safe_str(packet_map.get("source_type_classification")) or None,
        "dataset_provenance_class": _safe_str(packet_map.get("dataset_provenance_class")) or None,
        "feature_family_metadata": list(packet_map.get("feature_family_metadata", [])) if isinstance(packet_map.get("feature_family_metadata"), list) else [],
    }
    return summary


def render_mfcc_feature_quality_markdown_v1(packet: Any) -> str:
    validation = validate_mfcc_feature_quality_packet_v1(packet)
    if not validation["valid"]:
        raise ValueError("packet must validate before markdown rendering")

    packet_map = packet if isinstance(packet, Mapping) else {}
    feature_families = packet_map.get("feature_family_metadata", [])
    if not isinstance(feature_families, list):
        feature_families = []
    quality_dimensions = packet_map.get("quality_dimensions", {})
    if not isinstance(quality_dimensions, Mapping):
        quality_dimensions = {}
    recognition_quality_metadata = packet_map.get("recognition_quality_metadata", {})
    if not isinstance(recognition_quality_metadata, Mapping):
        recognition_quality_metadata = {}
    cymatics_usefulness_metadata = packet_map.get("cymatics_usefulness_metadata", {})
    if not isinstance(cymatics_usefulness_metadata, Mapping):
        cymatics_usefulness_metadata = {}

    lines = [
        "# MFCC Feature Quality Metadata Packet V1",
        "- Status: VALID",
        f"- Packet ID: {_safe_str(packet_map.get('packet_id'))}",
        f"- Source Type: {_safe_str(packet_map.get('source_type_classification'))}",
        f"- Dataset Provenance: {_safe_str(packet_map.get('dataset_provenance_class'))}",
        f"- Feature Families: {', '.join(_safe_str(item) for item in feature_families) or 'none'}",
        f"- Internal Only: {packet_map.get('internal_only') is True}",
        f"- Non-Authoritative: {packet_map.get('non_authoritative') is True}",
        f"- No Runtime Authority: {packet_map.get('runtime_authority') is False}",
        f"- No Microphone Authority: {packet_map.get('microphone_authority') is False}",
        f"- No Audio Processing Authority: {packet_map.get('audio_processing_authority') is False}",
        f"- No Raw Audio Storage Authority: {packet_map.get('raw_audio_storage_authority') is False}",
        f"- No Speaker Verification Authority: {packet_map.get('speaker_verification_authority') is False}",
        f"- No Voice Template Authority: {packet_map.get('voice_template_authority') is False}",
        f"- No Identity Authority: {packet_map.get('identity_authority') is False}",
        f"- No Benchmark Claim Authority: {packet_map.get('benchmark_claim_authority') is False}",
        f"- No Public Accuracy Claim Authority: {packet_map.get('public_accuracy_claim_authority') is False}",
        f"- No Product Readiness Authority: {packet_map.get('product_readiness_authority') is False}",
        f"- No Certification Authority: {packet_map.get('certification_authority') is False}",
        f"- No Model Provider Authority: {packet_map.get('model_provider_authority') is False}",
        f"- No Memory Write Authority: {packet_map.get('memory_write_authority') is False}",
        f"- No Behavior Pack Promotion Authority: {packet_map.get('behavior_pack_promotion_authority') is False}",
        "",
        "## Quality Dimensions",
    ]
    for key in sorted(quality_dimensions):
        lines.append(f"- {key}: {_safe_str(quality_dimensions[key])}")
    lines.append("")
    lines.append("## Recognition Quality")
    for key in sorted(recognition_quality_metadata):
        lines.append(f"- {key}: {_safe_str(recognition_quality_metadata[key])}")
    lines.append("")
    lines.append("## Cymatics Usefulness")
    for key in sorted(cymatics_usefulness_metadata):
        lines.append(f"- {key}: {_safe_str(cymatics_usefulness_metadata[key])}")
    lines.append("")
    lines.append("Internal use only. Metadata only. Not proof of cognition or authority.")
    return "\n".join(lines)


def build_initial_mfcc_feature_quality_examples_v1() -> dict[str, list[dict[str, Any]]]:
    safe_base = dict(
        source_type_classification="synthetic_metadata",
        dataset_provenance_class="synthetic_metadata",
        feature_family_metadata=["mfcc", "delta", "delta_delta", "spectral_metadata", "chroma_metadata", "cymatics_display_metadata"],
        quality_dimensions={
            "completeness": "full",
            "stability": "stable",
            "frame_window_consistency": "consistent",
            "feature_availability": "complete",
            "noise_condition_label": "clean",
            "language_command_domain_label": "english_command_set",
            "synthetic_accent_noise_test_condition_label": "none_identifying",
            "command_set_coverage": "broad",
            "expected_vs_observed_recognition_metadata": "aligned",
            "error_category_label": "none",
            "confidence_calibration_metadata": "calibrated",
            "cymatics_display_usefulness_label": "useful",
            "cymatics_display_interpretability_label": "clear",
        },
        cymatics_usefulness_metadata={
            "visual_expressiveness": "clear",
            "diagnostic_usefulness": "high",
            "feature_gap_diagnosis": "strong",
            "noise_diagnosis": "helpful",
            "rhythm_diagnosis": "helpful",
            "emphasis_diagnosis": "helpful",
            "command_instability_diagnosis": "low",
            "interpretability_label": "clear",
            "no_real_time_wiring": True,
        },
        recognition_quality_metadata={
            "calibration": "stable",
            "false_accept_labels": [],
            "false_reject_labels": [],
            "command_ambiguity_labels": [],
            "noise_robustness_labels": ["good"],
            "multilingual_accent_condition_labels": ["neutral"],
            "quality_notes": "internal metadata only",
        },
    )

    safe_examples = [
        {
            "example_id": "clean-synthetic-command-metadata",
            "label": "clean synthetic command metadata",
            "packet": build_mfcc_feature_quality_packet_v1(packet_id="mfcc-clean-1", **safe_base),
            "expected_valid": True,
        },
        {
            "example_id": "noisy-synthetic-command-metadata",
            "label": "noisy synthetic command metadata",
            "packet": build_mfcc_feature_quality_packet_v1(
                packet_id="mfcc-noisy-1",
                **{
                    **safe_base,
                    "quality_dimensions": {
                        **safe_base["quality_dimensions"],
                        "noise_condition_label": "noisy",
                    },
                    "recognition_quality_metadata": {
                        **safe_base["recognition_quality_metadata"],
                        "noise_robustness_labels": ["mixed"],
                    },
                },
            ),
            "expected_valid": True,
        },
        {
            "example_id": "multilingual-command-set-metadata",
            "label": "multilingual command-set metadata",
            "packet": build_mfcc_feature_quality_packet_v1(
                packet_id="mfcc-multi-1",
                **{
                    **safe_base,
                    "quality_dimensions": {
                        **safe_base["quality_dimensions"],
                        "language_command_domain_label": "multilingual_command_set",
                        "synthetic_accent_noise_test_condition_label": "non_identifying_multilingual",
                    },
                    "recognition_quality_metadata": {
                        **safe_base["recognition_quality_metadata"],
                        "multilingual_accent_condition_labels": ["multilingual"],
                    },
                },
            ),
            "expected_valid": True,
        },
        {
            "example_id": "accent-condition-no-identity",
            "label": "accent-condition metadata without speaker identity",
            "packet": build_mfcc_feature_quality_packet_v1(
                packet_id="mfcc-accent-1",
                **{
                    **safe_base,
                    "quality_dimensions": {
                        **safe_base["quality_dimensions"],
                        "synthetic_accent_noise_test_condition_label": "accent_condition_non_identifying",
                    },
                },
            ),
            "expected_valid": True,
        },
        {
            "example_id": "incomplete-mfcc-metadata",
            "label": "incomplete MFCC metadata",
            "packet": build_mfcc_feature_quality_packet_v1(
                packet_id="mfcc-incomplete-1",
                source_type_classification="internal_metadata",
                dataset_provenance_class="internal_metadata",
                feature_family_metadata=["mfcc", "delta"],
                quality_dimensions={
                    "completeness": "partial",
                    "stability": "unstable",
                    "frame_window_consistency": "inconsistent",
                    "feature_availability": "partial",
                    "noise_condition_label": "clean",
                    "language_command_domain_label": "english_command_set",
                    "synthetic_accent_noise_test_condition_label": "none_identifying",
                    "command_set_coverage": "limited",
                    "expected_vs_observed_recognition_metadata": "gapped",
                    "error_category_label": "missing_delta_delta",
                    "confidence_calibration_metadata": "uncalibrated",
                    "cymatics_display_usefulness_label": "weak",
                    "cymatics_display_interpretability_label": "partial",
                },
                cymatics_usefulness_metadata={
                    "visual_expressiveness": "weak",
                    "diagnostic_usefulness": "partial",
                    "feature_gap_diagnosis": "missing_delta_delta",
                    "noise_diagnosis": "helpful",
                    "rhythm_diagnosis": "helpful",
                    "emphasis_diagnosis": "helpful",
                    "command_instability_diagnosis": "medium",
                    "interpretability_label": "partial",
                    "no_real_time_wiring": True,
                },
                recognition_quality_metadata={
                    "calibration": "uncalibrated",
                    "false_accept_labels": ["none"],
                    "false_reject_labels": ["some"],
                    "command_ambiguity_labels": ["medium"],
                    "noise_robustness_labels": ["weak"],
                    "multilingual_accent_condition_labels": ["unknown"],
                    "quality_notes": "feature coverage incomplete",
                },
            ),
            "expected_valid": True,
        },
        {
            "example_id": "missing-delta-delta-metadata",
            "label": "missing delta/delta-delta metadata",
            "packet": build_mfcc_feature_quality_packet_v1(
                packet_id="mfcc-missing-delta-delta-1",
                source_type_classification="synthetic_metadata",
                dataset_provenance_class="synthetic_metadata",
                feature_family_metadata=["mfcc", "spectral_metadata"],
                quality_dimensions={
                    "completeness": "partial",
                    "stability": "stable",
                    "frame_window_consistency": "consistent",
                    "feature_availability": "partial",
                    "noise_condition_label": "clean",
                    "language_command_domain_label": "english_command_set",
                    "synthetic_accent_noise_test_condition_label": "none_identifying",
                    "command_set_coverage": "partial",
                    "expected_vs_observed_recognition_metadata": "gapped",
                    "error_category_label": "missing_delta_delta",
                    "confidence_calibration_metadata": "uncalibrated",
                    "cymatics_display_usefulness_label": "partial",
                    "cymatics_display_interpretability_label": "partial",
                },
                recognition_quality_metadata={
                    "calibration": "uncalibrated",
                    "false_accept_labels": [],
                    "false_reject_labels": ["more_than_expected"],
                    "command_ambiguity_labels": ["low"],
                    "noise_robustness_labels": ["mixed"],
                    "multilingual_accent_condition_labels": ["neutral"],
                    "quality_notes": "delta-delta not present",
                },
            ),
            "expected_valid": True,
        },
        {
            "example_id": "inconsistent-frame-window-metadata",
            "label": "inconsistent frame/window metadata",
            "packet": build_mfcc_feature_quality_packet_v1(
                packet_id="mfcc-window-1",
                source_type_classification="operator_supplied_metadata",
                dataset_provenance_class="operator_supplied_metadata",
                feature_family_metadata=["mfcc", "delta", "delta_delta"],
                quality_dimensions={
                    "completeness": "partial",
                    "stability": "unstable",
                    "frame_window_consistency": "inconsistent",
                    "feature_availability": "complete",
                    "noise_condition_label": "clean",
                    "language_command_domain_label": "english_command_set",
                    "synthetic_accent_noise_test_condition_label": "none_identifying",
                    "command_set_coverage": "broad",
                    "expected_vs_observed_recognition_metadata": "gapped",
                    "error_category_label": "frame_window_mismatch",
                    "confidence_calibration_metadata": "uncalibrated",
                    "cymatics_display_usefulness_label": "useful",
                    "cymatics_display_interpretability_label": "mixed",
                },
                recognition_quality_metadata={
                    "calibration": "unstable",
                    "false_accept_labels": ["low"],
                    "false_reject_labels": ["high"],
                    "command_ambiguity_labels": ["high"],
                    "noise_robustness_labels": ["weak"],
                    "multilingual_accent_condition_labels": ["neutral"],
                    "quality_notes": "frame/window inconsistency",
                },
            ),
            "expected_valid": True,
        },
        {
            "example_id": "cymatics-weak-signal-case",
            "label": "cymatics display weak-signal case",
            "packet": build_mfcc_feature_quality_packet_v1(
                packet_id="mfcc-cymatics-weak-1",
                source_type_classification="internal_metadata",
                dataset_provenance_class="internal_metadata",
                feature_family_metadata=["spectral_metadata", "cymatics_display_metadata"],
                quality_dimensions={
                    "completeness": "partial",
                    "stability": "stable",
                    "frame_window_consistency": "consistent",
                    "feature_availability": "partial",
                    "noise_condition_label": "noisy",
                    "language_command_domain_label": "command_visualization",
                    "synthetic_accent_noise_test_condition_label": "none_identifying",
                    "command_set_coverage": "narrow",
                    "expected_vs_observed_recognition_metadata": "gapped",
                    "error_category_label": "weak_visual_signal",
                    "confidence_calibration_metadata": "low",
                    "cymatics_display_usefulness_label": "weak",
                    "cymatics_display_interpretability_label": "partial",
                },
                cymatics_usefulness_metadata={
                    "visual_expressiveness": "weak",
                    "diagnostic_usefulness": "limited",
                    "feature_gap_diagnosis": "possible",
                    "noise_diagnosis": "present",
                    "rhythm_diagnosis": "possible",
                    "emphasis_diagnosis": "possible",
                    "command_instability_diagnosis": "possible",
                    "interpretability_label": "partial",
                    "no_real_time_wiring": True,
                },
                recognition_quality_metadata={
                    "calibration": "low",
                    "false_accept_labels": ["low"],
                    "false_reject_labels": ["medium"],
                    "command_ambiguity_labels": ["high"],
                    "noise_robustness_labels": ["weak"],
                    "multilingual_accent_condition_labels": ["neutral"],
                    "quality_notes": "weak cymatics display",
                },
            ),
            "expected_valid": True,
        },
    ]

    unsafe_examples = [
        {
            "example_id": "unsafe-audio-url-case",
            "label": "unsafe audio URL case",
            "packet": {
                "helper_type": HELPER_TYPE_V1,
                "schema_version": PACKET_SCHEMA_VERSION_V1,
                "packet_id": "mfcc-unsafe-audio-url-1",
                "source_type_classification": "synthetic_metadata",
                "dataset_provenance_class": "synthetic_metadata",
                "feature_family_metadata": ["mfcc"],
                "quality_dimensions": {"noise_condition_label": "clean"},
                "cymatics_usefulness_metadata": {},
                "recognition_quality_metadata": {},
                "internal_only": True,
                "non_authoritative": True,
                "validation_status": PACKET_VALIDATION_STATUS_INVALID_V1,
                "validation_errors": [],
                "blocked_reasons": [],
                "denied_authority_fields": _default_denied_authority_fields(),
                **_default_denied_authority_fields(),
                "notes": "http://example.com/sample.wav",
            },
            "expected_valid": False,
        },
        {
            "example_id": "unsafe-raw-audio-case",
            "label": "unsafe raw-audio metadata case",
            "packet": {
                "helper_type": HELPER_TYPE_V1,
                "schema_version": PACKET_SCHEMA_VERSION_V1,
                "packet_id": "mfcc-unsafe-raw-audio-1",
                "source_type_classification": "synthetic_metadata",
                "dataset_provenance_class": "synthetic_metadata",
                "feature_family_metadata": ["mfcc"],
                "quality_dimensions": {"raw_audio": True},
                "cymatics_usefulness_metadata": {},
                "recognition_quality_metadata": {},
                "internal_only": True,
                "non_authoritative": True,
                "validation_status": PACKET_VALIDATION_STATUS_INVALID_V1,
                "validation_errors": [],
                "blocked_reasons": [],
                "denied_authority_fields": _default_denied_authority_fields(),
                **_default_denied_authority_fields(),
            },
            "expected_valid": False,
        },
        {
            "example_id": "unsafe-speaker-identity-case",
            "label": "unsafe speaker identity case",
            "packet": {
                "helper_type": HELPER_TYPE_V1,
                "schema_version": PACKET_SCHEMA_VERSION_V1,
                "packet_id": "mfcc-unsafe-speaker-identity-1",
                "source_type_classification": "synthetic_metadata",
                "dataset_provenance_class": "synthetic_metadata",
                "feature_family_metadata": ["mfcc"],
                "quality_dimensions": {"speaker_identity": "operator"},
                "cymatics_usefulness_metadata": {},
                "recognition_quality_metadata": {},
                "internal_only": True,
                "non_authoritative": True,
                "validation_status": PACKET_VALIDATION_STATUS_INVALID_V1,
                "validation_errors": [],
                "blocked_reasons": [],
                "denied_authority_fields": _default_denied_authority_fields(),
                **_default_denied_authority_fields(),
            },
            "expected_valid": False,
        },
        {
            "example_id": "unsafe-benchmark-claim-case",
            "label": "unsafe benchmark-claim case",
            "packet": {
                "helper_type": HELPER_TYPE_V1,
                "schema_version": PACKET_SCHEMA_VERSION_V1,
                "packet_id": "mfcc-unsafe-benchmark-1",
                "source_type_classification": "benchmark_claim",
                "dataset_provenance_class": "benchmark_claim",
                "feature_family_metadata": ["mfcc"],
                "quality_dimensions": {"public_accuracy_claim_authority": True},
                "cymatics_usefulness_metadata": {},
                "recognition_quality_metadata": {"quality_notes": "public benchmark claim"},
                "internal_only": True,
                "non_authoritative": True,
                "validation_status": PACKET_VALIDATION_STATUS_INVALID_V1,
                "validation_errors": [],
                "blocked_reasons": [],
                "denied_authority_fields": _default_denied_authority_fields(),
                **_default_denied_authority_fields(),
            },
            "expected_valid": False,
        },
        {
            "example_id": "unsafe-runtime-authority-case",
            "label": "unsafe runtime-authority case",
            "packet": {
                "helper_type": HELPER_TYPE_V1,
                "schema_version": PACKET_SCHEMA_VERSION_V1,
                "packet_id": "mfcc-unsafe-runtime-1",
                "source_type_classification": "runtime_microphone",
                "dataset_provenance_class": "runtime_microphone",
                "feature_family_metadata": ["mfcc"],
                "quality_dimensions": {"runtime_authority": True},
                "cymatics_usefulness_metadata": {},
                "recognition_quality_metadata": {},
                "internal_only": True,
                "non_authoritative": True,
                "validation_status": PACKET_VALIDATION_STATUS_INVALID_V1,
                "validation_errors": [],
                "blocked_reasons": [],
                "denied_authority_fields": _default_denied_authority_fields(),
                **_default_denied_authority_fields(),
            },
            "expected_valid": False,
        },
    ]

    return {
        "helper_type": HELPER_TYPE_V1,
        "schema_version": PACKET_SCHEMA_VERSION_V1,
        "safe_examples": safe_examples,
        "unsafe_examples": unsafe_examples,
    }
