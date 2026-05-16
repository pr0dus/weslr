"""Evidence bridge to Frontier metadata adapter helpers V1.

Pure in-memory helpers for mapping existing evidence chat bridge metadata into
Frontier-compatible inspection metadata. This module does not call search,
models, advisors, registries, write files, mutate runtime chat behavior, or
create WESLR state.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from typing import Any

try:  # Keep dependency schema-level only; do not require it for runtime behavior.
    from weslr.output_provenance import ALLOWED_AUTHORITY_LEVELS, ALLOWED_TRUTH_CLASSES
except Exception:  # pragma: no cover - defensive import boundary
    ALLOWED_AUTHORITY_LEVELS = {"unknown"}
    ALLOWED_TRUTH_CLASSES = {"unverified", "unknown"}


ALIGNMENT_TYPE_V1 = "frontier_evidence_bridge_metadata_alignment_v1"
ALIGNMENT_VALIDATION_SCHEMA_V1 = "frontier_evidence_bridge_alignment_validation_v1"
OUTPUT_PROVENANCE_VALIDATION_SCHEMA_V1 = "evidence_bridge_output_provenance_validation_v1"

FRONTIER_PATHS_RELATED_V1 = [
    "_frontier_intelligence_limited_runtime",
    "_frontier_intelligence_ordinary_task",
    "_frontier_intelligence_shadow",
]

EVIDENCE_BRIDGE_SOURCE_MODULES_V1 = [
    "evidence_chat_bridge",
    "evidence_pipeline",
    "evidence_packet_builder",
    "evidence_answer_builder",
    "evidence_needed_detector",
]

_REQUIRED_ALIGNMENT_FIELDS_V1 = {
    "alignment_type",
    "source_bridge",
    "evidence_used",
    "authority",
    "truth_status",
    "automatic_truth_write",
    "source_count",
    "source_urls_present",
    "source_classes",
    "search_attempted",
    "classification_summary",
    "frontier_paths_related",
    "model_calls",
    "advisor_calls",
    "memory_writes",
    "truth_writes",
    "raw_text_stored",
    "safe_to_wire_runtime",
    "superseded_fallback_or_generic_answer",
}

_FORBIDDEN_ALIGNMENT_FIELDS_V1 = {
    "source_urls",
    "sources",
    "raw_source_text",
    "source_text",
    "raw_text",
    "raw_private_text",
    "source_id",
    "source_ids",
    "registry_write",
    "registry_writes",
    "registry_entry",
    "registry_entries",
    "provenance_source_id",
    "provenance_source_ids",
    "authority_elevation",
    "runtime_authority",
    "runtime_wiring",
    "broad_runtime_replacement",
    "official_iq_score",
    "official_benchmark_score",
    "certification_claim",
    "answer_key",
    "answer_keys",
    "hidden_prompt",
    "hidden_prompts",
    "protected_material",
    "protected_test_item",
    "protected_test_items",
}

_FORBIDDEN_PROVENANCE_FIELDS_V1 = _FORBIDDEN_ALIGNMENT_FIELDS_V1 | {
    "source_authority",
    "source_authority_elevation",
    "live_source_registration",
}

_FORBIDDEN_TEXT_MARKERS_V1 = {
    "official_score_iq_or_certification_claim": [
        "official iq",
        "certified iq",
        "official score",
        "official benchmark score",
        "officially certified",
        "certification claim",
    ],
    "protected_material_or_answer_key": [
        "answer key",
        "protected material",
        "protected test item",
        "protected benchmark item",
    ],
    "hidden_prompt_exposure": [
        "hidden prompt",
        "hidden system prompt",
        "system prompt secret",
    ],
    "runtime_authority_drift": [
        "runtime wiring authorized",
        "broad runtime replacement",
        "source authority elevated",
        "registry write performed",
    ],
}

_SAFE_CLASSIFICATION_FIELDS_V1 = (
    "record_type",
    "evidence_needed",
    "need_type",
    "confidence",
    "reason",
    "authority",
    "automatic_search_allowed",
)


def to_frontier_evidence_bridge_metadata_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy; never writes or mutates input."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Mapping):
        return {str(key): to_frontier_evidence_bridge_metadata_json_safe_v1(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_frontier_evidence_bridge_metadata_json_safe_v1(value) for value in obj]
    try:
        return json.loads(json.dumps(obj))
    except Exception:
        return str(obj)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_bool(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else bool(value)


def _as_non_negative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    return 0


def _safe_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _classification_summary(classification: Any) -> dict[str, Any]:
    source = _as_mapping(classification)
    summary: dict[str, Any] = {}
    for key in _SAFE_CLASSIFICATION_FIELDS_V1:
        if key in source:
            summary[key] = _safe_scalar(source[key])
    return to_frontier_evidence_bridge_metadata_json_safe_v1(summary)


def build_frontier_evidence_bridge_alignment_v1(
    evidence_metadata: Mapping[str, Any] | None,
    *,
    superseded_fallback_or_generic_answer: bool = False,
) -> dict[str, Any]:
    """Map existing ``_evidence_metadata`` into Frontier-compatible metadata."""
    metadata = _as_mapping(evidence_metadata)
    source_urls = metadata.get("source_urls", [])
    source_urls_present = bool(source_urls) if isinstance(source_urls, list) else False

    return {
        "alignment_type": ALIGNMENT_TYPE_V1,
        "source_bridge": "evidence_chat_bridge",
        "evidence_used": _as_bool(metadata.get("evidence_used", False)),
        "authority": _safe_scalar(metadata.get("authority", "external_evidence_unverified")) or "external_evidence_unverified",
        "truth_status": _safe_scalar(metadata.get("truth_status", "unverified")) or "unverified",
        "automatic_truth_write": False,
        "source_count": _as_non_negative_int(metadata.get("source_count", 0)),
        "source_urls_present": source_urls_present,
        "source_classes": [],
        "search_attempted": _as_bool(metadata.get("search_attempted", False)),
        "classification_summary": _classification_summary(metadata.get("classification", {})),
        "frontier_paths_related": list(FRONTIER_PATHS_RELATED_V1),
        "model_calls": False,
        "advisor_calls": False,
        "memory_writes": False,
        "truth_writes": False,
        "raw_text_stored": False,
        "safe_to_wire_runtime": False,
        "superseded_fallback_or_generic_answer": bool(superseded_fallback_or_generic_answer),
    }


def _walk_json(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    items = [(path, value)]
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            items.extend(_walk_json(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            items.extend(_walk_json(child, f"{path}[{index}]"))
    return items


def _contains_any(value: str, markers: list[str]) -> bool:
    lower = value.lower()
    return any(marker in lower for marker in markers)


def _add_violation(violations: list[dict[str, str]], category: str, path: str, message: str) -> None:
    violations.append({"category": category, "path": path or "$", "message": message})


def _validate_common_forbidden_content(
    obj: Any,
    violations: list[dict[str, str]],
    *,
    forbidden_fields: set[str],
) -> None:
    for path, value in _walk_json(obj):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in forbidden_fields:
            _add_violation(violations, "forbidden_field", path, f"forbidden field {terminal}")
        if isinstance(value, str):
            for category, markers in _FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(value, markers):
                    _add_violation(violations, category, path, f"forbidden marker for {category}")


def validate_frontier_evidence_bridge_alignment_v1(alignment: Any) -> dict[str, Any]:
    """Validate Frontier evidence bridge alignment metadata without raising."""
    safe = to_frontier_evidence_bridge_metadata_json_safe_v1(alignment)
    violations: list[dict[str, str]] = []

    if not isinstance(safe, Mapping):
        _add_violation(violations, "schema", "$", "alignment must be a mapping")
        safe = {}

    missing = sorted(_REQUIRED_ALIGNMENT_FIELDS_V1 - set(safe.keys()))
    for field in missing:
        _add_violation(violations, "schema", field, "missing required field")

    if safe.get("alignment_type") != ALIGNMENT_TYPE_V1:
        _add_violation(violations, "schema", "alignment_type", f"must be {ALIGNMENT_TYPE_V1}")
    if safe.get("source_bridge") != "evidence_chat_bridge":
        _add_violation(violations, "schema", "source_bridge", "must be evidence_chat_bridge")

    for key in ("safe_to_wire_runtime", "model_calls", "advisor_calls", "memory_writes", "truth_writes", "raw_text_stored", "automatic_truth_write"):
        if safe.get(key) is True:
            _add_violation(violations, "side_effect_boundary", key, f"{key} must remain false")

    if "source_urls" in safe:
        _add_violation(violations, "raw_source_boundary", "source_urls", "source_urls must not be copied into alignment")
    if not isinstance(safe.get("source_classes", []), list):
        _add_violation(violations, "schema", "source_classes", "source_classes must be a list")
    if safe.get("truth_status") != "unverified":
        _add_violation(violations, "truth_boundary", "truth_status", "truth_status must remain unverified for bridge alignment v1")
    if safe.get("frontier_paths_related") != FRONTIER_PATHS_RELATED_V1:
        _add_violation(violations, "schema", "frontier_paths_related", "unexpected Frontier path list")

    _validate_common_forbidden_content(safe, violations, forbidden_fields=_FORBIDDEN_ALIGNMENT_FIELDS_V1)

    valid = not violations
    return {
        "schema_version": ALIGNMENT_VALIDATION_SCHEMA_V1,
        "valid": valid,
        "validation_status": "accepted" if valid else "rejected",
        "violations": violations,
        "violation_count": len(violations),
    }


def build_output_provenance_for_evidence_bridge_v1(alignment_or_evidence_metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build metadata-only output provenance for the evidence bridge."""
    source = _as_mapping(alignment_or_evidence_metadata)
    truth_class = source.get("truth_status") if source.get("truth_status") in ALLOWED_TRUTH_CLASSES else "unverified"
    authority_level = "unknown"
    if authority_level not in ALLOWED_AUTHORITY_LEVELS:
        authority_level = "unknown"
    return {
        "schema_version": "1.0",
        "generated_by": "evidence_chat_bridge",
        "source_modules": list(EVIDENCE_BRIDGE_SOURCE_MODULES_V1),
        "trigger_type": "user_message",
        "input_channel": "chat",
        "output_channel": "chat",
        "truth_class": truth_class,
        "authority_level": authority_level,
        "llm_assisted": False,
        "advisor_assisted": False,
        "memory_write_performed": False,
        "queue_write_performed": False,
        "runtime_action_performed": False,
    }


def validate_output_provenance_for_evidence_bridge_v1(provenance: Any) -> dict[str, Any]:
    """Validate evidence bridge output provenance metadata without raising."""
    safe = to_frontier_evidence_bridge_metadata_json_safe_v1(provenance)
    violations: list[dict[str, str]] = []

    if not isinstance(safe, Mapping):
        _add_violation(violations, "schema", "$", "provenance must be a mapping")
        safe = {}

    required = {
        "schema_version",
        "generated_by",
        "source_modules",
        "trigger_type",
        "input_channel",
        "output_channel",
        "truth_class",
        "authority_level",
        "llm_assisted",
        "advisor_assisted",
        "memory_write_performed",
        "queue_write_performed",
        "runtime_action_performed",
    }
    for field in sorted(required - set(safe.keys())):
        _add_violation(violations, "schema", field, "missing required field")

    if safe.get("generated_by") != "evidence_chat_bridge":
        _add_violation(violations, "schema", "generated_by", "must be evidence_chat_bridge")
    if safe.get("source_modules") != EVIDENCE_BRIDGE_SOURCE_MODULES_V1:
        _add_violation(violations, "schema", "source_modules", "unexpected source modules")
    if safe.get("truth_class") != "unverified":
        _add_violation(violations, "truth_boundary", "truth_class", "truth_class must remain unverified")
    if safe.get("authority_level") != "unknown":
        _add_violation(violations, "authority_boundary", "authority_level", "authority_level must remain unknown until enum approval")

    for key in ("llm_assisted", "advisor_assisted", "memory_write_performed", "queue_write_performed", "runtime_action_performed"):
        if safe.get(key) is True:
            _add_violation(violations, "side_effect_boundary", key, f"{key} must remain false")

    _validate_common_forbidden_content(safe, violations, forbidden_fields=_FORBIDDEN_PROVENANCE_FIELDS_V1)

    valid = not violations
    return {
        "schema_version": OUTPUT_PROVENANCE_VALIDATION_SCHEMA_V1,
        "valid": valid,
        "validation_status": "accepted" if valid else "rejected",
        "violations": violations,
        "violation_count": len(violations),
    }


def summarize_frontier_evidence_bridge_alignment_v1(alignment: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a redacted/count-only inspection summary."""
    safe = _as_mapping(to_frontier_evidence_bridge_metadata_json_safe_v1(alignment))
    return {
        "alignment_type": safe.get("alignment_type"),
        "evidence_used": bool(safe.get("evidence_used")),
        "authority": safe.get("authority"),
        "truth_status": safe.get("truth_status"),
        "source_count": _as_non_negative_int(safe.get("source_count", 0)),
        "source_urls_present": bool(safe.get("source_urls_present")),
        "search_attempted": bool(safe.get("search_attempted")),
        "model_calls": False,
        "advisor_calls": False,
        "memory_writes": False,
        "truth_writes": False,
        "raw_text_stored": False,
        "safe_to_wire_runtime": False,
        "validation_status": validate_frontier_evidence_bridge_alignment_v1(safe)["validation_status"],
    }


def render_frontier_evidence_bridge_alignment_markdown_v1(alignment: Mapping[str, Any] | None) -> str:
    """Render redacted Markdown summary with no URLs or raw source text."""
    summary = summarize_frontier_evidence_bridge_alignment_v1(alignment)
    no_write = not any(summary[key] for key in ("model_calls", "advisor_calls", "memory_writes", "truth_writes", "raw_text_stored", "safe_to_wire_runtime"))
    return "\n".join([
        "Evidence bridge Frontier alignment: metadata-only",
        f"- evidence used: {summary['evidence_used']}",
        f"- authority: {summary['authority']}",
        f"- truth status: {summary['truth_status']}",
        f"- source count: {summary['source_count']}",
        f"- source URLs present: {summary['source_urls_present']}",
        f"- search attempted: {summary['search_attempted']}",
        f"- safety posture: unverified, non-authoritative, no-write={no_write}",
        f"- validation: {summary['validation_status']}",
    ])


__all__ = [
    "ALIGNMENT_TYPE_V1",
    "build_frontier_evidence_bridge_alignment_v1",
    "validate_frontier_evidence_bridge_alignment_v1",
    "build_output_provenance_for_evidence_bridge_v1",
    "validate_output_provenance_for_evidence_bridge_v1",
    "to_frontier_evidence_bridge_metadata_json_safe_v1",
    "summarize_frontier_evidence_bridge_alignment_v1",
    "render_frontier_evidence_bridge_alignment_markdown_v1",
]
