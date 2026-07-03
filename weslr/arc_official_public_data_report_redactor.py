"""Redaction helpers for ARC official-public parse/scorer surface reports.

The redactor keeps metadata/provenance/checksum fields and strips raw grids,
expected outputs, latent rules, answer descriptors, and raw task dumps.
"""

from __future__ import annotations

from typing import Any, Mapping

SCHEMA_VERSION_V1 = "arc_official_public_data_report_redactor_v1"

_ALLOWED_STRING_KEYS_V1 = {
    "schema_version",
    "report_kind",
    "report_name",
    "repository",
    "branch",
    "start_head",
    "end_head",
    "commit_status",
    "actual_preflight_head",
    "owner_challenge_summary",
    "scope_statement",
    "dummy_no_data_fixture_statement",
    "official_public_data_untouched",
    "official_percentage",
    "implemented_files",
    "adapter_behavior",
    "emitter_behavior",
    "scorer_behavior",
    "harness_behavior",
    "approval_dependency",
    "leakage_audit",
    "validation_results",
    "readiness_verdict",
    "recommended_next_lane",
}

_FORBIDDEN_KEY_TOKENS_V1 = (
    "expected_output",
    "reference_grid",
    "reference_output",
    "latent_rule",
    "answer_descriptor",
    "solution_explanation",
    "raw_task_json",
    "task_json_dump",
    "official_task_json",
    "hidden_answer",
    "public_private_marker",
    "train_input",
    "train_output",
    "test_input",
)

_FORBIDDEN_VALUE_TOKENS_V1 = (
    "expected_output",
    "reference_grid",
    "reference_output",
    "latent rule",
    "answer descriptor",
    "solution explanation",
    "raw task json",
    "task json dump",
    "hidden answer",
)


def _safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _safe(item) for key, item in value.items() if not _is_forbidden_key(key)}
    if isinstance(value, tuple):
        return [_safe(item) for item in value]
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, set):
        return [_safe(item) for item in sorted(value, key=repr)]
    return str(value)


def _is_forbidden_key(key: Any) -> bool:
    text = str(key).strip().lower()
    return any(token in text for token in _FORBIDDEN_KEY_TOKENS_V1)


def _sanitize_text(value: str) -> str:
    text = " ".join(value.split())
    lower = text.lower()
    if any(token in lower for token in _FORBIDDEN_VALUE_TOKENS_V1):
        return "[redacted]"
    return text


def redact_arc_official_public_report_payload_v1(payload: Any) -> Any:
    if isinstance(payload, str):
        return _sanitize_text(payload)
    if isinstance(payload, Mapping):
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            if _is_forbidden_key(key):
                continue
            sanitized[str(key)] = redact_arc_official_public_report_payload_v1(value)
        return sanitized
    if isinstance(payload, tuple):
        return [redact_arc_official_public_report_payload_v1(item) for item in payload]
    if isinstance(payload, list):
        return [redact_arc_official_public_report_payload_v1(item) for item in payload]
    if isinstance(payload, set):
        return [redact_arc_official_public_report_payload_v1(item) for item in sorted(payload, key=repr)]
    return _safe(payload)


__all__ = [
    "SCHEMA_VERSION_V1",
    "redact_arc_official_public_report_payload_v1",
]
