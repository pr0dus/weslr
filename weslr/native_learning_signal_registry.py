#!/usr/bin/env python3
"""WESLR native learning signal registry helpers V1.

Safe helper-only layer for normalizing provenance-bearing learning signals into
in-memory records. This module does not train models, call external models,
score benchmarks, write files, persist `.weslr` state, wire runtime/chat/voice,
approve proposals, or implement changes.
"""

from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional

try:
    from weslr.native_reasoning_frame import FORBIDDEN_FIELD_NAMES, FORBIDDEN_TEXT_MARKERS
except Exception:  # pragma: no cover - import fallback for direct script inspection
    FORBIDDEN_FIELD_NAMES = set()
    FORBIDDEN_TEXT_MARKERS = {}

SIGNAL_TYPE_V1 = "native_learning_signal_v1"
REGISTRY_TYPE_V1 = "native_learning_signal_registry_v1"
SIGNAL_VALIDATION_SCHEMA_V1 = "native_learning_signal_validation_v1"
REGISTRY_VALIDATION_SCHEMA_V1 = "native_learning_signal_registry_validation_v1"
SIGNAL_EXECUTION_STATUS_V1 = "non_executing_learning_signal_only"
REGISTRY_EXECUTION_STATUS_V1 = "non_executing_learning_registry_only"

ALLOWED_SIGNAL_FAMILIES_V1 = {
    "generic_response_signal",
    "missing_context_signal",
    "evidence_boundary_signal",
    "capability_boundary_signal",
    "fake_memory_risk_signal",
    "self_check_issue_signal",
    "shadow_review_signal",
    "drift_signal",
    "readiness_gap_signal",
    "contract_insufficiency_signal",
    "user_correction_signal",
    "proposal_rejection_signal",
    "hardcoded_path_dominance_signal",
}

CONFIDENCE_LABELS_V1 = {
    "weak",
    "provisional",
    "recurring_candidate",
    "validated_by_review",
}

LEARNING_STATUS_V1 = {
    "signal_only": True,
    "not_truth": True,
    "not_proposal": True,
    "not_approval": True,
    "not_implementation": True,
}

SAFETY_BOUNDARIES_V1 = [
    "learning_signal_is_not_truth",
    "repeated_signal_is_not_automatic_change",
    "proposal_is_not_approval",
    "approval_is_not_implementation",
    "implementation_requires_tests_and_release_gate_check",
    "no_raw_private_text_by_default",
    "no_hidden_prompts",
    "no_answer_keys",
    "no_protected_items",
    "no_model_training_payloads",
    "no_automatic_self_modification",
    "no_runtime_or_voice_wiring",
    "no_persistence_by_default",
]

FORBIDDEN_SIGNAL_FIELDS_V1 = set(FORBIDDEN_FIELD_NAMES) | {
    "raw_private_text",
    "hidden_prompt",
    "hidden_prompts",
    "answer_key",
    "answer_keys",
    "protected_item",
    "protected_items",
    "protected_test_item",
    "protected_test_items",
    "official_score",
    "official_scores",
    "benchmark_answer",
    "benchmark_answers",
    "iq_score",
    "official_iq_score",
    "clinical_score",
    "certification_claim",
    "model_weight_update",
    "fine_tune_payload",
    "auto_approval",
    "auto_approved",
    "auto_implementation",
    "auto_implemented",
    "runtime_write",
    "persistence_target",
    "score",
    "scores",
    "numeric_score",
    "benchmark_score",
    "grade",
    "grades",
    "pass_fail",
    "passed",
    "failed",
}

FORBIDDEN_TEXT_MARKERS_V1 = {
    **FORBIDDEN_TEXT_MARKERS,
    "raw_private_text": ["raw private text"],
    "model_training_or_fine_tuning": ["model weight update", "fine tune payload", "fine-tune payload", "gradient update"],
    "numeric_score_or_pass_fail_grading": ["numeric score", "pass/fail", "final grade", "graded as"],
    "fake_self_awareness": ["fake self-awareness claim", "i am self-aware as fact", "proven self aware"],
}

SAFE_SIGNAL_FIELDS_V1 = {
    "signal_id",
    "signal_type",
    "signal_family",
    "source_layer",
    "source_ref",
    "provenance_refs",
    "recurrence_key",
    "redaction_status",
    "privacy_status",
    "evidence_status",
    "confidence_label",
    "learning_status",
    "suggested_investigation",
    "safety_boundaries",
    "created_at",
    "execution_status",
}


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return copy.deepcopy(value)
    if isinstance(value, tuple):
        return list(copy.deepcopy(value))
    if isinstance(value, set):
        return sorted(copy.deepcopy(value), key=repr)
    return [copy.deepcopy(value)]


def _string_list(value: Any) -> List[str]:
    return [item for item in (_compact(v, "") for v in _as_list(value)) if item]


def _compact(value: Any, default: str = "not_supplied") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if text else default
    if isinstance(value, Mapping):
        for key in ("summary", "status", "signal_type", "source_ref", "suggested_investigation", "issue_type"):
            if value.get(key):
                return _compact(value[key], default=default)
    return _compact(str(value), default=default)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"{prefix}_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _utc_timestamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _walk(obj: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(value, child)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _walk(value, f"{path}[{index}]")


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def _recurrence_key_for(signal: Mapping[str, Any]) -> str:
    explicit = _compact(signal.get("recurrence_key"), "")
    if explicit:
        return explicit
    seed = {
        "family": _compact(signal.get("signal_family")),
        "source_layer": _compact(signal.get("source_layer")),
        "signal_type": _compact(signal.get("signal_type")),
        "source_ref": _compact(signal.get("source_ref")),
        "suggested_investigation": _compact(signal.get("suggested_investigation")),
    }
    return _stable_id("nlsrrec", seed)


def _group_ids(signals: Iterable[Mapping[str, Any]], key: str) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    for signal in signals:
        value = _compact(signal.get(key))
        groups.setdefault(value, []).append(_compact(signal.get("signal_id")))
    return {k: sorted(v) for k, v in sorted(groups.items())}


def create_native_learning_signal_v1(
    *,
    signal_family: str,
    source_layer: str,
    source_ref: str,
    signal_id: Optional[str] = None,
    signal_type: str = SIGNAL_TYPE_V1,
    provenance_refs: Optional[Iterable[Any]] = None,
    recurrence_key: Optional[str] = None,
    redaction_status: str = "redacted_or_no_raw_private_text_supplied",
    privacy_status: str = "safe_metadata_only",
    evidence_status: str = "requires_review_not_truth",
    confidence_label: str = "provisional",
    suggested_investigation: str = "review repeated safe signal before proposing changes",
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Create one JSON-safe in-memory native learning signal record."""
    family = signal_family if signal_family in ALLOWED_SIGNAL_FAMILIES_V1 else "generic_response_signal"
    confidence = confidence_label if confidence_label in CONFIDENCE_LABELS_V1 else "provisional"
    seed = {
        "signal_family": family,
        "source_layer": _compact(source_layer),
        "source_ref": _compact(source_ref),
        "provenance_refs": _string_list(provenance_refs),
        "suggested_investigation": _compact(suggested_investigation),
    }
    signal: Dict[str, Any] = {
        "signal_id": _compact(signal_id, "") or _stable_id("nlsigv1", seed),
        "signal_type": SIGNAL_TYPE_V1 if signal_type != SIGNAL_TYPE_V1 else signal_type,
        "signal_family": family,
        "source_layer": _compact(source_layer),
        "source_ref": _compact(source_ref),
        "provenance_refs": _string_list(provenance_refs),
        "recurrence_key": _compact(recurrence_key, "") or _recurrence_key_for(seed),
        "redaction_status": _compact(redaction_status),
        "privacy_status": _compact(privacy_status),
        "evidence_status": _compact(evidence_status),
        "confidence_label": confidence,
        "learning_status": copy.deepcopy(LEARNING_STATUS_V1),
        "suggested_investigation": _compact(suggested_investigation),
        "safety_boundaries": list(SAFETY_BOUNDARIES_V1),
        "created_at": _compact(created_at, "") or _utc_timestamp(),
        "execution_status": SIGNAL_EXECUTION_STATUS_V1,
    }
    return _json_safe(signal)


def normalize_native_learning_signal_v1(raw_signal: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a safe learning signal record from raw dict-like input without mutation."""
    safe_raw = _json_safe(raw_signal or {})
    if not isinstance(safe_raw, Mapping):
        safe_raw = {}

    dropped_paths = []
    for path, _value in _walk(safe_raw):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_SIGNAL_FIELDS_V1:
            dropped_paths.append(path)

    base = create_native_learning_signal_v1(
        signal_id=_compact(safe_raw.get("signal_id"), "") or None,
        signal_family=_compact(safe_raw.get("signal_family"), "generic_response_signal"),
        source_layer=_compact(safe_raw.get("source_layer"), "unspecified_source_layer"),
        source_ref=_compact(safe_raw.get("source_ref"), "unspecified_source_ref"),
        provenance_refs=_string_list(safe_raw.get("provenance_refs")),
        recurrence_key=_compact(safe_raw.get("recurrence_key"), "") or None,
        redaction_status="forbidden_fields_dropped" if dropped_paths else _compact(safe_raw.get("redaction_status"), "redacted_or_no_raw_private_text_supplied"),
        privacy_status="safe_metadata_only_private_payload_removed" if dropped_paths else _compact(safe_raw.get("privacy_status"), "safe_metadata_only"),
        evidence_status=_compact(safe_raw.get("evidence_status"), "requires_review_not_truth"),
        confidence_label=_compact(safe_raw.get("confidence_label"), "provisional"),
        suggested_investigation=_compact(safe_raw.get("suggested_investigation"), "review repeated safe signal before proposing changes"),
        created_at=_compact(safe_raw.get("created_at"), "") or None,
    )
    if dropped_paths:
        base["redaction_status"] = "forbidden_fields_dropped"
        base["privacy_status"] = "safe_metadata_only_private_payload_removed"
    return _json_safe(base)


def _violation(category: str, path: str, message: str) -> Dict[str, str]:
    return {"category": category, "path": path or "$", "message": message}


def validate_native_learning_signal_v1(signal: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate one native learning signal remains safe, non-executing, and non-authoritative."""
    safe = _json_safe(signal or {})
    if not isinstance(safe, Mapping):
        safe = {}
    violations: List[Dict[str, str]] = []

    if safe.get("signal_type") != SIGNAL_TYPE_V1:
        violations.append(_violation("invalid_signal_type", "signal_type", "signal_type must be native_learning_signal_v1"))
    if safe.get("signal_family") not in ALLOWED_SIGNAL_FAMILIES_V1:
        violations.append(_violation("invalid_signal_family", "signal_family", "signal_family is not allowed"))
    if safe.get("confidence_label") not in CONFIDENCE_LABELS_V1:
        violations.append(_violation("invalid_confidence_label", "confidence_label", "confidence_label must be non-numeric approved label"))
    if safe.get("execution_status") != SIGNAL_EXECUTION_STATUS_V1:
        violations.append(_violation("execution_authorization_drift", "execution_status", "signal must remain non-executing"))

    learning = safe.get("learning_status") if isinstance(safe.get("learning_status"), Mapping) else {}
    for key in ("signal_only", "not_truth", "not_proposal", "not_approval", "not_implementation"):
        if learning.get(key) is not True:
            violations.append(_violation("learning_status_drift", f"learning_status.{key}", "signal must remain signal-only and non-authoritative"))

    for required in ("signal_id", "source_layer", "source_ref", "recurrence_key"):
        if not _compact(safe.get(required), ""):
            violations.append(_violation("missing_required_field", required, f"{required} is required"))

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_SIGNAL_FIELDS_V1:
            category = "forbidden_field"
            if terminal in {"raw_private_text"}:
                category = "raw_private_text"
            elif terminal in {"hidden_prompt", "hidden_prompts"}:
                category = "hidden_prompt"
            elif terminal in {"answer_key", "answer_keys", "benchmark_answer", "benchmark_answers"}:
                category = "answer_key_or_benchmark_answer"
            elif terminal in {"protected_item", "protected_items", "protected_test_item", "protected_test_items"}:
                category = "protected_test_material"
            elif terminal in {"official_score", "official_scores", "iq_score", "official_iq_score", "clinical_score", "certification_claim", "benchmark_score"}:
                category = "official_iq_benchmark_or_certification"
            elif terminal in {"model_weight_update", "fine_tune_payload"}:
                category = "model_training_or_fine_tuning"
            elif terminal in {"auto_approval", "auto_approved", "auto_implementation", "auto_implemented"}:
                category = "auto_approval_or_auto_implementation"
            elif terminal in {"runtime_write", "persistence_target"}:
                category = "runtime_or_persistence_authorization_drift"
            elif terminal in {"score", "scores", "numeric_score", "grade", "grades", "pass_fail", "passed", "failed"}:
                category = "numeric_score_or_pass_fail_grading"
            violations.append(_violation(category, path, f"forbidden field present: {terminal}"))
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            violations.append(_violation("numeric_score_or_numeric_metric", path, "numeric fields are not allowed in learning signals"))
        if isinstance(value, str):
            for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(value, markers):
                    violations.append(_violation(category, path, f"forbidden text marker detected: {category}"))

    return {
        "validation_schema": SIGNAL_VALIDATION_SCHEMA_V1,
        "valid": not violations,
        "validation_status": "accepted" if not violations else "rejected",
        "violation_count": len(violations),
        "violations": violations,
    }


def build_native_learning_signal_registry_v1(signals: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Normalize, validate, and group learning signals in memory only."""
    normalized = [normalize_native_learning_signal_v1(signal) for signal in _as_list(signals)]
    validations = [validate_native_learning_signal_v1(signal) for signal in normalized]
    duplicate_ids = sorted({sid for sid in [s.get("signal_id") for s in normalized] if [s.get("signal_id") for s in normalized].count(sid) > 1})
    valid_count = sum(1 for result in validations if result["valid"])
    registry_seed = {"signals": [s.get("signal_id") for s in normalized], "duplicates": duplicate_ids}
    registry = {
        "registry_id": _stable_id("nlsregv1", registry_seed),
        "registry_type": REGISTRY_TYPE_V1,
        "total_signals": len(normalized),
        "valid_signal_count": valid_count,
        "invalid_signal_count": len(normalized) - valid_count,
        "signals": normalized,
        "signal_validations": validations,
        "duplicate_signal_ids": duplicate_ids,
        "groups_by_recurrence_key": _group_ids(normalized, "recurrence_key"),
        "groups_by_signal_family": _group_ids(normalized, "signal_family"),
        "groups_by_source_layer": _group_ids(normalized, "source_layer"),
        "safety_boundaries": list(SAFETY_BOUNDARIES_V1),
        "execution_status": REGISTRY_EXECUTION_STATUS_V1,
    }
    return _json_safe(registry)


def validate_native_learning_signal_registry_v1(registry: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a registry remains in-memory, non-executing, and non-authorizing."""
    safe = _json_safe(registry or {})
    if not isinstance(safe, Mapping):
        safe = {}
    violations: List[Dict[str, str]] = []

    if safe.get("registry_type") != REGISTRY_TYPE_V1:
        violations.append(_violation("invalid_registry_type", "registry_type", "registry_type must be native_learning_signal_registry_v1"))
    if safe.get("execution_status") != REGISTRY_EXECUTION_STATUS_V1:
        violations.append(_violation("execution_authorization_drift", "execution_status", "registry must remain non-executing"))

    signals = safe.get("signals") if isinstance(safe.get("signals"), list) else []
    ids = [_compact(signal.get("signal_id"), "") for signal in signals if isinstance(signal, Mapping)]
    duplicate_ids = sorted({sid for sid in ids if sid and ids.count(sid) > 1})
    for sid in duplicate_ids:
        violations.append(_violation("duplicate_signal_id", "signals", f"duplicate signal_id flagged: {sid}"))

    for index, signal in enumerate(signals):
        result = validate_native_learning_signal_v1(signal if isinstance(signal, Mapping) else {})
        for item in result["violations"]:
            violations.append(_violation(item["category"], f"signals[{index}].{item['path']}", item["message"]))

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_SIGNAL_FIELDS_V1:
            violations.append(_violation("forbidden_field", path, f"forbidden field present in registry: {terminal}"))
        if isinstance(value, str):
            for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(value, markers):
                    violations.append(_violation(category, path, f"forbidden text marker detected in registry: {category}"))

    return {
        "validation_schema": REGISTRY_VALIDATION_SCHEMA_V1,
        "valid": not violations,
        "validation_status": "accepted" if not violations else "rejected",
        "violation_count": len(violations),
        "violations": violations,
        "duplicate_signal_ids": duplicate_ids,
    }


def summarize_native_learning_signal_registry_v1(registry: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a count-only/redacted registry summary."""
    safe = _json_safe(registry or {})
    signals = safe.get("signals") if isinstance(safe.get("signals"), list) else []
    duplicate_count = len(safe.get("duplicate_signal_ids") or [])
    validation = validate_native_learning_signal_registry_v1(safe)
    return {
        "total_signals": int(safe.get("total_signals") or len(signals)),
        "valid_signal_count": int(safe.get("valid_signal_count") or 0),
        "invalid_signal_count": int(safe.get("invalid_signal_count") or 0),
        "families_present": sorted((safe.get("groups_by_signal_family") or {}).keys()),
        "source_layers_present": sorted((safe.get("groups_by_source_layer") or {}).keys()),
        "recurrence_key_count": len(safe.get("groups_by_recurrence_key") or {}),
        "duplicate_count": duplicate_count,
        "safety_status": "safe" if validation["valid"] else "review_required",
        "execution_status": safe.get("execution_status", REGISTRY_EXECUTION_STATUS_V1),
    }


def to_native_learning_signal_registry_json_safe_v1(registry: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a JSON-serializable registry copy without persistence."""
    return _json_safe(registry)


def render_native_learning_signal_registry_markdown_v1(registry: Mapping[str, Any]) -> str:
    """Render safe Markdown for a native learning signal registry."""
    safe = _json_safe(registry or {})
    summary = summarize_native_learning_signal_registry_v1(safe)
    lines = [
        "# Native Learning Signal Registry",
        "",
        f"- Registry type: `{safe.get('registry_type', REGISTRY_TYPE_V1)}`",
        f"- Total signals: {summary['total_signals']}",
        f"- Valid signals: {summary['valid_signal_count']}",
        f"- Invalid signals: {summary['invalid_signal_count']}",
        f"- Execution status: `{summary['execution_status']}`",
        "",
        "## Signal Families",
    ]
    for family in summary["families_present"]:
        count = len((safe.get("groups_by_signal_family") or {}).get(family, []))
        lines.append(f"- `{family}`: {count}")
    lines.extend(["", "## Source Layers"])
    for layer in summary["source_layers_present"]:
        count = len((safe.get("groups_by_source_layer") or {}).get(layer, []))
        lines.append(f"- `{layer}`: {count}")
    lines.extend(["", "## Recurrence Groups"])
    for recurrence_key, ids in sorted((safe.get("groups_by_recurrence_key") or {}).items()):
        lines.append(f"- `{recurrence_key}`: {len(ids)} signal(s)")
    lines.extend(["", "## Safety Boundaries"])
    for boundary in SAFE_BOUNDARIES_FOR_MARKDOWN_V1:
        lines.append(f"- {boundary}")
    lines.extend([
        "",
        "## Non-Learning / Non-Truth Disclaimer",
        "These records are signal-only metadata. They are not truth, proposals, approvals, implementations, scores, or model-training payloads.",
    ])
    return "\n".join(lines)


SAFE_BOUNDARIES_FOR_MARKDOWN_V1 = [
    "learning signal is not truth",
    "repeated signal is not automatic change",
    "proposal is not approval",
    "approval is not implementation",
    "no raw private text, hidden prompts, answer keys, protected items, model training payloads, or runtime writes",
]
