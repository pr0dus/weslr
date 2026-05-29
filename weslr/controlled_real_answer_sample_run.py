"""Metadata-only helpers for controlled real-answer sample-run planning v1.

This module is intentionally pure, deterministic, and fail-closed.
It prepares future controlled sample-run metadata only; it does not execute
runs, call adapters, capture answers, or persist raw content.
"""

from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping

from weslr.real_answer_quality_observation_helpers import (
    ALLOWED_SOURCE_CLASSES_V1 as REAL_ANSWER_ALLOWED_SOURCE_CLASSES_V1,
    BLOCKED_LABELS_V1 as REAL_ANSWER_BLOCKED_LABELS_V1,
    RESULT_LABELS_V1 as REAL_ANSWER_RESULT_LABELS_V1,
    to_real_answer_quality_observation_json_safe_v1,
)

HELPER_TYPE_V1 = "weslr_controlled_real_answer_sample_run_v1"
BOUNDARY_TYPE_V1 = "controlled_real_answer_sample_run_boundary_v1"
CASE_TYPE_V1 = "controlled_real_answer_sample_case_v1"
ADAPTER_CONTRACT_TYPE_V1 = "controlled_real_answer_adapter_contract_v1"
RUN_PLAN_TYPE_V1 = "controlled_real_answer_sample_run_plan_v1"
OBSERVATION_STUB_TYPE_V1 = "controlled_real_answer_observation_stub_v1"
REVIEW_PACKET_TYPE_V1 = "controlled_real_answer_sample_review_packet_v1"
SUMMARY_TYPE_V1 = "controlled_real_answer_sample_run_summary_v1"

ALLOWED_SOURCE_CLASSES = {"public_open", "synthetic_weslr_created"}
EXECUTION_MODE = "controlled_internal"
MIN_FIRST_RUN_CASES = 3
MAX_FIRST_RUN_CASES = 5

# Preserve compatibility with the helper boundary vocabulary where it helps.
RESULT_LABELS_V1 = set(REAL_ANSWER_RESULT_LABELS_V1)
BLOCKED_LABELS_V1 = set(REAL_ANSWER_BLOCKED_LABELS_V1) | {
    "unknown_execution_mode",
    "missing_case_id",
    "missing_prompt_descriptor_ref",
    "missing_expected_observation_dimensions",
    "missing_adapter_review_ref",
    "missing_operator_approval_ref",
    "missing_abort_path",
    "missing_rollback_policy",
    "invalid_case_count",
    "case_count_below_minimum",
    "case_count_above_maximum",
    "no_run_marker_missing",
    "invalid_precondition_status",
}

DENIED_AUTHORITY_FLAGS_V1 = {
    "public_output_authority",
    "final_answer_authority",
    "public_live_authority",
    "public_ux_authority",
    "voice_authority",
    "runtime_authority",
    "live_runtime_authority",
    "model_call_authority",
    "search_call_authority",
    "advisor_call_authority",
    "official_claim_authority",
    "turing_claim_authority",
    "intelligence_claim_authority",
    "certification_claim_authority",
    "public_readiness_authority",
    "voice_readiness_authority",
    "live_user_safety_readiness_authority",
    "benchmark_score_authority",
    "model_superiority_authority",
    "raw_persistence_authority",
    "private_memory_authority",
    "unknown_engine_authority",
    "automatic_lesson_promotion_authority",
}

BOOLEAN_PASSTHROUGH_KEYS_V1 = {
    "runtime_authority",
    "final_answer_authority",
    "public_output_authority",
    "public_live_authority",
    "public_ux_authority",
    "voice_authority",
    "live_runtime_authority",
    "model_call_authority",
    "search_call_authority",
    "advisor_call_authority",
    "official_claim_authority",
    "turing_claim_authority",
    "intelligence_claim_authority",
    "certification_claim_authority",
    "public_readiness_authority",
    "voice_readiness_authority",
    "live_user_safety_readiness_authority",
    "benchmark_score_authority",
    "model_superiority_authority",
    "raw_persistence_authority",
    "private_memory_authority",
    "unknown_engine_authority",
    "automatic_lesson_promotion_authority",
}

METADATA_PASSTHROUGH_KEYS_V1 = {
    "case_id",
    "source_case_id",
    "source_class",
    "registry_approved",
    "source_lineage_complete",
    "prompt_descriptor_ref",
    "adapter_review_ref",
    "operator_approval_ref",
    "abort_path",
    "rollback_policy",
    "execution_mode",
    "answer_sample_ref",
    "redaction_status",
    "raw_answer_stored",
    "no_run_marker",
    "case_count",
    "min_first_run_cases",
    "max_first_run_cases",
    "helper_type",
    "boundary_type",
    "case_type",
    "adapter_contract_type",
    "plan_type",
    "observation_stub_type",
    "review_packet_type",
    "summary_type",
    "metadata_only",
    "internal_only",
    "expected_observation_dimensions",
    "blocked_labels",
    "denied_authority_flags",
}

SENSITIVE_KEY_HINTS_V1 = (
    "raw_answer",
    "raw_prompt",
    "prompt",
    "raw_response",
    "response_text",
    "raw_transcript",
    "transcript_text",
    "raw_context",
    "context_text",
    "live_user",
    "private_memory",
    "private_data",
    "private_text",
    "hidden_material",
    "benchmark_material",
    "provider_model_output",
    "final_answer",
    "dot_weslr",
    "voice",
    "public_live_authority",
    "runtime_authority",
    "official_claim",
    "turing_claim",
    "intelligence_claim",
    "certification_claim",
    "public_readiness",
    "manipulation",
    "fake_empathy",
    "template",
    "stereotype",
    "persona",
    "roleplay",
    "production",
    "auto_learning",
    "hidden_router",
)

FORBIDDEN_MARKERS_V1 = (
    ".weslr",
    "private memory",
    "private_memory",
    "private data",
    "live user",
    "live_user",
    "live chat",
    "hidden",
    "semi-private",
    "semi private",
    "private",
    "unapproved",
    "provider output",
    "model output",
    "provider_model_output",
    "transcript",
    "final answer",
    "final_answer",
    "runtime",
    "public live",
    "voice",
    "official claim",
    "official",
    "turing",
    "intelligence",
    "certification",
    "public readiness",
    "production",
    "auto-learning",
    "auto learning",
    "hidden router",
    "hidden_router",
    "shadow router",
)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _safe_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        values = list(value.keys())
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = _safe_str(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def _unique_sorted(labels: Iterable[str]) -> list[str]:
    if isinstance(labels, (str, bytes)):
        items = [labels]
    else:
        items = list(labels)
    return sorted(set(_safe_list(items)))


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _redact_key(key: str, value: Any) -> Any:
    key_text = _safe_str(key).lower()
    if key_text in BOOLEAN_PASSTHROUGH_KEYS_V1 or key_text in METADATA_PASSTHROUGH_KEYS_V1:
        return _json_safe(value)
    if key_text == "raw_answer_stored":
        return _json_safe(value)
    if any(hint in key_text for hint in SENSITIVE_KEY_HINTS_V1):
        return f"[redacted:{_safe_str(key) or 'sensitive'}]"
    return _json_safe(value)


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _redact_key(str(key), val)
            for key, val in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted((_json_safe(item) for item in value), key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return f"[redacted:{type(value).__name__}]"


def to_controlled_real_answer_sample_json_safe_v1(value: Any) -> Any:
    """Convert controlled-real-answer sample structures to deterministic JSON-safe data."""

    return _json_safe(value)


def _contains_forbidden_marker(value: Any) -> bool:
    for text in _collect_strings(value):
        lowered = text.lower()
        for marker in FORBIDDEN_MARKERS_V1:
            if marker in lowered:
                return True
    return False


def _collect_strings(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            strings.extend(_collect_strings(key))
            strings.extend(_collect_strings(item))
        return strings
    if isinstance(value, (list, tuple, set)):
        for item in value:
            strings.extend(_collect_strings(item))
        return strings
    text = _safe_str(value)
    if text:
        strings.append(text)
    return strings


def _source_class_allowed(source_class: str) -> bool:
    return _safe_str(source_class) in ALLOWED_SOURCE_CLASSES


def _collect_denied_authority_flags(record: Mapping[str, Any]) -> list[str]:
    lineage = _as_mapping(record.get("source_lineage"))
    case = _as_mapping(record.get("case"))
    adapter = _as_mapping(record.get("adapter_contract"))
    flags: list[str] = []
    for key in DENIED_AUTHORITY_FLAGS_V1:
        if _safe_bool(record.get(key)) or _safe_bool(lineage.get(key)) or _safe_bool(case.get(key)) or _safe_bool(adapter.get(key)):
            flags.append(key)
    return _unique_sorted(flags)


def build_controlled_real_answer_sample_case_v1(
    *,
    case_id: str,
    source_class: str,
    registry_approved: bool,
    prompt_descriptor_ref: str,
    expected_observation_dimensions: Iterable[str],
) -> dict[str, Any]:
    """Build a metadata-only sample case descriptor."""

    source_lineage = {
        "source_case_id": _safe_str(case_id),
        "source_class": _safe_str(source_class),
        "registry_approved": _safe_bool(registry_approved),
        "prompt_descriptor_ref": _safe_str(prompt_descriptor_ref),
        "source_lineage_complete": True,
    }
    record = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "case_type": CASE_TYPE_V1,
        "case_id": _safe_str(case_id),
        "source_class": _safe_str(source_class),
        "registry_approved": _safe_bool(registry_approved),
        "prompt_descriptor_ref": _safe_str(prompt_descriptor_ref),
        "expected_observation_dimensions": _unique_sorted(expected_observation_dimensions),
        "source_lineage": source_lineage,
        "source_lineage_complete": True,
        "metadata_only": True,
        "internal_only": True,
        "raw_answer_stored": False,
    }
    return to_controlled_real_answer_sample_json_safe_v1(record)


def build_controlled_real_answer_adapter_contract_v1(
    *,
    adapter_id: str,
    adapter_type: str,
    run_id: str,
    commit: str,
    source_case_id: str,
    source_class: str,
    registry_approved: bool,
    operator_approval_ref: str,
    answer_sample_ref: str,
    raw_answer_stored: bool = False,
    redaction_status: str = "redacted",
    execution_mode: str = EXECUTION_MODE,
    runtime_authority: bool = False,
    final_answer_authority: bool = False,
    public_output_authority: bool = False,
    **extra_metadata: Any,
) -> dict[str, Any]:
    """Build a future adapter contract; no execution occurs."""

    record = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "adapter_contract_type": ADAPTER_CONTRACT_TYPE_V1,
        "adapter_id": _safe_str(adapter_id),
        "adapter_type": _safe_str(adapter_type),
        "run_id": _safe_str(run_id),
        "commit": _safe_str(commit),
        "source_case_id": _safe_str(source_case_id),
        "source_class": _safe_str(source_class),
        "registry_approved": _safe_bool(registry_approved),
        "operator_approval_ref": _safe_str(operator_approval_ref),
        "answer_sample_ref": _safe_str(answer_sample_ref),
        "raw_answer_stored": False,
        "redaction_status": _safe_str(redaction_status),
        "execution_mode": _safe_str(execution_mode),
        "runtime_authority": False,
        "final_answer_authority": False,
        "public_output_authority": False,
        "metadata_only": True,
        "internal_only": True,
    }
    if extra_metadata:
        record.update(extra_metadata)
    record["raw_answer_stored"] = False
    record["execution_mode"] = EXECUTION_MODE
    record["runtime_authority"] = False
    record["final_answer_authority"] = False
    record["public_output_authority"] = False
    return to_controlled_real_answer_sample_json_safe_v1(record)


def validate_controlled_real_answer_sample_preconditions_v1(
    value: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate future-run preconditions and fail closed."""

    record = dict(_as_mapping(value))
    normalized = to_controlled_real_answer_sample_json_safe_v1(record)
    if not isinstance(normalized, dict):
        normalized = {}

    blocked_labels: list[str] = []

    case = _as_mapping(normalized.get("case")) or normalized
    adapter = _as_mapping(normalized.get("adapter_contract")) or normalized
    lineage = _as_mapping(normalized.get("source_lineage") or case.get("source_lineage"))

    case_id = _safe_str(case.get("case_id") or normalized.get("case_id"))
    source_class = _safe_str(case.get("source_class") or adapter.get("source_class") or lineage.get("source_class"))
    registry_approved = _safe_bool(case.get("registry_approved") if "registry_approved" in case else adapter.get("registry_approved") if "registry_approved" in adapter else lineage.get("registry_approved"))
    prompt_descriptor_ref = _safe_str(case.get("prompt_descriptor_ref") or normalized.get("prompt_descriptor_ref"))
    expected_dims = _safe_list(case.get("expected_observation_dimensions") or normalized.get("expected_observation_dimensions"))
    lineage_complete = _safe_bool(normalized.get("source_lineage_complete") if "source_lineage_complete" in normalized else case.get("source_lineage_complete") if "source_lineage_complete" in case else lineage.get("source_lineage_complete"))

    if not case_id:
        blocked_labels.append("missing_case_id")
    if not prompt_descriptor_ref:
        blocked_labels.append("missing_prompt_descriptor_ref")
    if not expected_dims:
        blocked_labels.append("missing_expected_observation_dimensions")
    if not lineage or not lineage_complete:
        blocked_labels.append("incomplete_source_lineage")
    if not source_class or not _source_class_allowed(source_class):
        blocked_labels.append("unknown_source_class")
    if not registry_approved:
        blocked_labels.append("registry_not_approved")
    if not _safe_str(normalized.get("adapter_review_ref") or adapter.get("adapter_review_ref")):
        blocked_labels.append("missing_adapter_review_ref")
    if not _safe_str(normalized.get("operator_approval_ref") or adapter.get("operator_approval_ref")):
        blocked_labels.append("missing_operator_approval_ref")
    if _safe_bool(normalized.get("raw_answer_stored") or adapter.get("raw_answer_stored")):
        blocked_labels.append("raw_answer_stored_true")
    if not _safe_str(normalized.get("redaction_status") or adapter.get("redaction_status")):
        blocked_labels.append("missing_redaction_status")
    if not lineage:
        blocked_labels.append("missing_source_lineage")
    elif not _safe_bool(normalized.get("source_lineage_complete") if "source_lineage_complete" in normalized else lineage.get("source_lineage_complete", True)):
        blocked_labels.append("incomplete_source_lineage")
    if _collect_denied_authority_flags(normalized):
        blocked_labels.append("unknown_authority_flag")
    if not _safe_str(normalized.get("abort_path") or adapter.get("abort_path")):
        blocked_labels.append("missing_abort_path")
    if not _safe_str(normalized.get("rollback_policy") or adapter.get("rollback_policy")):
        blocked_labels.append("missing_rollback_policy")

    execution_mode = _safe_str(normalized.get("execution_mode") or adapter.get("execution_mode") or EXECUTION_MODE)
    if execution_mode != EXECUTION_MODE:
        blocked_labels.append("unknown_execution_mode")

    valid = not blocked_labels
    blocked = not valid
    precondition_status = "valid" if valid else "blocked"
    if blocked_labels and not case_id:
        precondition_status = "blocked"

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "precondition_type": "controlled_real_answer_sample_preconditions_v1",
        "valid": valid,
        "blocked": blocked,
        "precondition_status": precondition_status,
        "case_id": case_id,
        "source_class": source_class,
        "registry_approved": registry_approved,
        "blocked_labels": _unique_sorted(blocked_labels),
        "denied_authority_flags": _collect_denied_authority_flags(normalized),
        "raw_answer_stored": False,
        "metadata_only": True,
        "internal_only": True,
        "normalized": normalized,
    }


def build_controlled_real_answer_sample_run_plan_v1(
    cases: Iterable[Mapping[str, Any]],
    *,
    run_id: str = "",
    adapter_review_ref: str = "",
    operator_approval_ref: str = "",
    abort_path: str = "",
    rollback_policy: str = "",
    execution_mode: str = EXECUTION_MODE,
    **extra_metadata: Any,
) -> dict[str, Any]:
    """Build a metadata-only future sample-run plan for 3–5 approved cases."""

    input_cases = [to_controlled_real_answer_sample_json_safe_v1(case) for case in cases]
    normalized_cases = [c if isinstance(c, dict) else {} for c in input_cases]

    blocked_labels: list[str] = []
    for case in normalized_cases:
        if _contains_forbidden_marker(case):
            blocked_labels.append("raw_private_content_requested")
        if _contains_forbidden_marker(case.get("source_class")):
            blocked_labels.append("unknown_source_class")
        if not _source_class_allowed(_safe_str(case.get("source_class"))):
            blocked_labels.append("unknown_source_class")
        if not _safe_bool(case.get("registry_approved")):
            blocked_labels.append("registry_not_approved")
        if _safe_bool(case.get("raw_answer_stored")):
            blocked_labels.append("raw_answer_stored_true")

    case_count = len(normalized_cases)
    if case_count < MIN_FIRST_RUN_CASES:
        blocked_labels.append("case_count_below_minimum")
    if case_count > MAX_FIRST_RUN_CASES:
        blocked_labels.append("case_count_above_maximum")
    if case_count == 0:
        blocked_labels.append("invalid_case_count")
    if execution_mode != EXECUTION_MODE:
        blocked_labels.append("unknown_execution_mode")

    plan = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "plan_type": RUN_PLAN_TYPE_V1,
        "run_id": _safe_str(run_id),
        "adapter_review_ref": _safe_str(adapter_review_ref),
        "operator_approval_ref": _safe_str(operator_approval_ref),
        "abort_path": _safe_str(abort_path),
        "rollback_policy": _safe_str(rollback_policy),
        "execution_mode": _safe_str(execution_mode),
        "case_count": case_count,
        "min_first_run_cases": MIN_FIRST_RUN_CASES,
        "max_first_run_cases": MAX_FIRST_RUN_CASES,
        "cases": normalized_cases,
        "blocked_labels": _unique_sorted(blocked_labels),
        "denied_authority_flags": _unique_sorted(
            flag for case in normalized_cases for flag in _collect_denied_authority_flags(case)
        ),
        "raw_answer_stored": False,
        "no_run_marker": True,
        "metadata_only": True,
        "internal_only": True,
    }
    if extra_metadata:
        plan.update(extra_metadata)
    plan["raw_answer_stored"] = False
    plan["no_run_marker"] = True
    plan["execution_mode"] = EXECUTION_MODE
    return to_controlled_real_answer_sample_json_safe_v1(plan)


def validate_controlled_real_answer_sample_run_plan_v1(
    value: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a future sample-run plan and fail closed."""

    plan = dict(_as_mapping(value))
    normalized = to_controlled_real_answer_sample_json_safe_v1(plan)
    if not isinstance(normalized, dict):
        normalized = {}

    blocked_labels: list[str] = list(_safe_list(normalized.get("blocked_labels")))
    cases = normalized.get("cases")
    if not isinstance(cases, list):
        cases = []
    case_count = len(cases)
    if case_count < MIN_FIRST_RUN_CASES:
        blocked_labels.append("case_count_below_minimum")
    if case_count > MAX_FIRST_RUN_CASES:
        blocked_labels.append("case_count_above_maximum")
    if case_count == 0:
        blocked_labels.append("invalid_case_count")

    if not _safe_bool(normalized.get("no_run_marker")):
        blocked_labels.append("no_run_marker_missing")
    if _safe_bool(normalized.get("raw_answer_stored")):
        blocked_labels.append("raw_answer_stored_true")
    if _safe_str(normalized.get("execution_mode")) != EXECUTION_MODE:
        blocked_labels.append("unknown_execution_mode")
    if not _safe_str(normalized.get("operator_approval_ref")):
        blocked_labels.append("missing_operator_approval_ref")
    if not _safe_str(normalized.get("adapter_review_ref")):
        blocked_labels.append("missing_adapter_review_ref")
    if not _safe_str(normalized.get("abort_path")):
        blocked_labels.append("missing_abort_path")
    if not _safe_str(normalized.get("rollback_policy")):
        blocked_labels.append("missing_rollback_policy")

    for case in cases:
        c = _as_mapping(case)
        source_lineage = _as_mapping(c.get("source_lineage"))
        source_class = _safe_str(c.get("source_class") or source_lineage.get("source_class"))
        if not source_class or not _source_class_allowed(source_class):
            blocked_labels.append("unknown_source_class")
        if _contains_forbidden_marker(c):
            blocked_labels.append("raw_private_content_requested")
        if not _safe_bool(c.get("registry_approved") if "registry_approved" in c else source_lineage.get("registry_approved")):
            blocked_labels.append("registry_not_approved")
        if _safe_bool(c.get("raw_answer_stored")):
            blocked_labels.append("raw_answer_stored_true")
        if _collect_denied_authority_flags(c):
            blocked_labels.append("unknown_authority_flag")
        if not _safe_str(c.get("case_id")):
            blocked_labels.append("missing_case_id")
        if not _safe_str(c.get("prompt_descriptor_ref")):
            blocked_labels.append("missing_prompt_descriptor_ref")
        if not _safe_list(c.get("expected_observation_dimensions")):
            blocked_labels.append("missing_expected_observation_dimensions")
        if not source_lineage or not _safe_bool(c.get("source_lineage_complete") if "source_lineage_complete" in c else source_lineage.get("source_lineage_complete")):
            blocked_labels.append("incomplete_source_lineage")

    valid = not blocked_labels
    blocked = not valid
    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "plan_type": RUN_PLAN_TYPE_V1,
        "valid": valid,
        "blocked": blocked,
        "plan_status": "valid" if valid else "blocked",
        "case_count": case_count,
        "blocked_labels": _unique_sorted(blocked_labels),
        "denied_authority_flags": _unique_sorted(
            flag for case in cases for flag in _collect_denied_authority_flags(case)
        ),
        "raw_answer_stored": False,
        "no_run_marker": _safe_bool(normalized.get("no_run_marker")),
        "metadata_only": True,
        "internal_only": True,
        "normalized_plan": normalized,
    }


def build_controlled_real_answer_observation_stub_v1(
    *,
    observation_id: str,
    run_id: str,
    answer_sample_ref: str,
    source_case_id: str,
    source_class: str,
    redaction_status: str,
    expected_observation_dimensions: Iterable[str],
    operator_review_required: bool = True,
    **extra_metadata: Any,
) -> dict[str, Any]:
    """Build an observation-ready metadata stub for a future answer sample."""

    stub = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "observation_stub_type": OBSERVATION_STUB_TYPE_V1,
        "observation_id": _safe_str(observation_id),
        "run_id": _safe_str(run_id),
        "answer_sample_ref": _safe_str(answer_sample_ref),
        "source_case_id": _safe_str(source_case_id),
        "source_class": _safe_str(source_class),
        "redaction_status": _safe_str(redaction_status),
        "expected_observation_dimensions": _unique_sorted(expected_observation_dimensions),
        "operator_review_required": _safe_bool(operator_review_required),
        "raw_answer_stored": False,
        "metadata_only": True,
        "internal_only": True,
    }
    if extra_metadata:
        stub.update(extra_metadata)
    stub["raw_answer_stored"] = False
    return to_controlled_real_answer_sample_json_safe_v1(stub)


def build_controlled_real_answer_sample_review_packet_v1(
    *,
    plan: Mapping[str, Any],
    precondition_result: Mapping[str, Any] | None = None,
    observation_stubs: Iterable[Mapping[str, Any]] | None = None,
    no_run_marker: bool = True,
    **extra_metadata: Any,
) -> dict[str, Any]:
    """Build an operator-reviewable packet for the no-run sample boundary."""

    plan_map = _as_mapping(plan)
    preconditions = _as_mapping(precondition_result) if precondition_result is not None else validate_controlled_real_answer_sample_preconditions_v1(plan_map)
    stubs = [to_controlled_real_answer_sample_json_safe_v1(stub) for stub in (observation_stubs or [])]

    packet = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "review_packet_type": REVIEW_PACKET_TYPE_V1,
        "plan_status": _safe_str(preconditions.get("precondition_status") or preconditions.get("plan_status") or "blocked"),
        "precondition_status": _safe_str(preconditions.get("precondition_status") or "blocked"),
        "plan_summary": {
            "case_count": int(plan_map.get("case_count") or len(_as_mapping({"cases": plan_map.get("cases")}).get("cases") or []) or 0),
            "min_first_run_cases": MIN_FIRST_RUN_CASES,
            "max_first_run_cases": MAX_FIRST_RUN_CASES,
            "execution_mode": _safe_str(plan_map.get("execution_mode") or EXECUTION_MODE),
        },
        "blocked_labels": _unique_sorted(
            list(_safe_list(plan_map.get("blocked_labels")))
            + list(_safe_list(preconditions.get("blocked_labels")))
            + [label for stub in stubs for label in _safe_list(stub.get("blocked_labels"))]
        ),
        "denied_authority_flags": _unique_sorted(
            list(_safe_list(plan_map.get("denied_authority_flags")))
            + list(_safe_list(preconditions.get("denied_authority_flags")))
            + [flag for stub in stubs for flag in _safe_list(stub.get("denied_authority_flags"))]
        ),
        "no_run_marker": _safe_bool(no_run_marker),
        "operator_review_required": True,
        "raw_answer_stored": False,
        "metadata_only": True,
        "internal_only": True,
        "observation_stubs": stubs,
    }
    if extra_metadata:
        packet.update(extra_metadata)
    packet["no_run_marker"] = _safe_bool(no_run_marker)
    packet["operator_review_required"] = True
    packet["raw_answer_stored"] = False
    return to_controlled_real_answer_sample_json_safe_v1(packet)


def summarize_controlled_real_answer_sample_run_v1(value: Mapping[str, Any] | Iterable[Any]) -> dict[str, Any]:
    """Summarize sample-run metadata using counts/status only."""

    if isinstance(value, Mapping) and "cases" in value:
        items = value["cases"]
    else:
        items = value

    normalized: list[dict[str, Any]] = []
    for item in items:
        normalized.append(_as_mapping(item))

    blocked_labels = _unique_sorted(label for record in normalized for label in record.get("blocked_labels", []))
    denied_authority_flags = _unique_sorted(flag for record in normalized for flag in record.get("denied_authority_flags", []))
    status_counts: dict[str, int] = {"valid": 0, "blocked": 0}
    for record in normalized:
        status = "valid" if not _safe_bool(record.get("blocked")) and not _safe_bool(record.get("invalid")) else "blocked"
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "summary_type": SUMMARY_TYPE_V1,
        "total_records": len(normalized),
        "valid_records": status_counts.get("valid", 0),
        "blocked_records": status_counts.get("blocked", 0),
        "blocked_label_count": len(blocked_labels),
        "blocked_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "record_status_counts": status_counts,
        "raw_answer_stored": False,
        "metadata_only": True,
        "internal_only": True,
    }


__all__ = [
    "HELPER_TYPE_V1",
    "BOUNDARY_TYPE_V1",
    "CASE_TYPE_V1",
    "ADAPTER_CONTRACT_TYPE_V1",
    "RUN_PLAN_TYPE_V1",
    "OBSERVATION_STUB_TYPE_V1",
    "REVIEW_PACKET_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "ALLOWED_SOURCE_CLASSES",
    "EXECUTION_MODE",
    "MIN_FIRST_RUN_CASES",
    "MAX_FIRST_RUN_CASES",
    "RESULT_LABELS_V1",
    "BLOCKED_LABELS_V1",
    "build_controlled_real_answer_sample_case_v1",
    "build_controlled_real_answer_adapter_contract_v1",
    "validate_controlled_real_answer_sample_preconditions_v1",
    "build_controlled_real_answer_sample_run_plan_v1",
    "validate_controlled_real_answer_sample_run_plan_v1",
    "build_controlled_real_answer_observation_stub_v1",
    "build_controlled_real_answer_sample_review_packet_v1",
    "summarize_controlled_real_answer_sample_run_v1",
    "to_controlled_real_answer_sample_json_safe_v1",
]
