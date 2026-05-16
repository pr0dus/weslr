"""WESLR Internal Corpus to Advisor Review Adapter Helpers V1.

Safe, in-memory helpers that map internal evaluation corpus status/review
artifacts into existing WESLR advisor-review proposal structures. This module
does not persist queue items, call advisor LLMs, call models, create a runner,
score outputs, create a parallel advisor/audit layer, mutate `.weslr` state, or
change runtime/chat/voice behavior.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any
import json
import re

from weslr.advisor_prompt_templates import get_advisor_prompt_template
from weslr.advisor_review_queue import (
    AdvisorReviewQueueSafetyFlags,
    advisor_review_queue_item_to_dict,
    create_empty_advisor_review_queue_item,
    validate_advisor_review_queue_item,
)
from weslr.internal_evaluation_corpus import (
    REVIEW_CARDS_SCHEMA_VERSION,
    STATUS_BUNDLE_SCHEMA_VERSION,
    build_internal_evaluation_corpus_review_cards_v1,
    build_internal_evaluation_corpus_status_bundle_v1,
    summarize_internal_evaluation_corpus_review_cards_v1,
    summarize_internal_evaluation_corpus_status_bundle_v1,
    to_internal_evaluation_corpus_status_bundle_json_safe_v1,
)

ADAPTER_TYPE = "internal_corpus_to_advisor_review_adapter_v1"
SUMMARY_MODE = "redacted_count_only"
REVIEW_SCOPE = "internal_corpus_status_and_dry_review_cards"
DEFAULT_ADVISOR_TASK = "gap_taxonomy_review"
DEFAULT_ADVISOR_TEMPLATE_ID = "advisor_prompt:gap_taxonomy_review"

ALLOWED_ADVISOR_TASKS = [
    "test_suggestion",
    "synthetic_example_suggestion",
    "gap_taxonomy_review",
    "wording_risk_review",
    "reasoning_pattern_review",
]

BLOCKED_ADVISOR_TASKS = [
    "answer_selection",
    "truth_authority",
    "soundness_authority",
    "official_score_claim",
    "benchmark_specific_tuning",
    "answer_key_use",
    "runtime_mutation",
    "memory_mutation",
    "governance_override",
    "advisor_call_execution",
    "external_model_call",
]

FORBIDDEN_TRUE_FIELDS = {
    "advisor_call_allowed": "advisor_call_allowed must remain false",
    "model_calls": "model_calls must remain false",
    "safe_to_execute": "safe_to_execute must remain false",
    "raw_prompts_included": "raw_prompts_included must remain false",
    "protected_material_included": "protected_material_included must remain false",
    "answer_keys_included": "answer_keys_included must remain false",
    "hidden_prompts_included": "hidden_prompts_included must remain false",
    "raw_private_text_included": "raw_private_text_included must remain false",
    "official_score_claim": "official_score_claim must remain false",
    "runner_created": "runner_created must remain false",
    "scoring_created": "scoring_created must remain false",
    "auto_approval": "auto_approval must remain false",
    "auto_implementation": "auto_implementation must remain false",
    "queue_persistence_performed": "queue_persistence_performed must remain false",
    "writes_performed": "writes_performed must remain false",
    "runtime_changed": "runtime_changed must remain false",
    "parallel_advisor_queue_created": "parallel advisor queue must not be created",
    "parallel_advisor_prompt_system_created": "parallel advisor prompt system must not be created",
    "parallel_audit_system_created": "parallel audit system must not be created",
}

FORBIDDEN_FIELD_NAMES = {
    "raw_prompt",
    "input_prompt",
    "prompts",
    "protected_item",
    "protected_test_item",
    "hidden_prompt",
    "hidden_prompts",
    "answer_key",
    "answer_keys",
    "correct_answer",
    "official_solution",
    "benchmark_item_id",
    "benchmark_item_ids",
    "score",
    "scores",
    "numeric_score",
    "grade",
    "pass_fail",
    "solver_execution",
    "answer_selection",
    "runtime_mutation",
    "runtime_write",
    "weslr_state_write",
    "advisor_llm_call",
    "external_model_call",
}

SENSITIVE_TEXT_PATTERNS = {
    "raw prompt": re.compile(r"raw prompt|input prompt|synthetic prompt:", re.IGNORECASE),
    "protected material": re.compile(r"protected material|protected test item|proprietary test item|question stem", re.IGNORECASE),
    "answer key": re.compile(r"answer[_ -]?key|official solution|correct answer", re.IGNORECASE),
    "hidden prompt": re.compile(r"hidden[_ -]?prompt|system prompt extraction", re.IGNORECASE),
    "raw private text": re.compile(r"raw private text|private user data|ssn|social security|passport|password\s*[:=]", re.IGNORECASE),
    "official score claim": re.compile(r"official score|official iq|iq score|benchmark score|clinical score|certification|certified result", re.IGNORECASE),
    "runtime secret": re.compile(r"api[_ -]?key|sk-[A-Za-z0-9]|token|secret", re.IGNORECASE),
    "weslr state write": re.compile(r"\.weslr|write.*weslr state|persist.*corpus", re.IGNORECASE),
    "model call": re.compile(r"call model|external model|invoke model|openai|openrouter|ollama", re.IGNORECASE),
    "advisor call": re.compile(r"call advisor|advisor llm|run advisor|invoke advisor", re.IGNORECASE),
}

REDACTION = "[redacted]"


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    if str(value).strip():
        return [str(value).strip()]
    return []


def _string_values(value: Any, *, include_keys: bool = False) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for key, nested in value.items():
            if include_keys:
                values.append(str(key))
            values.extend(_string_values(nested, include_keys=include_keys))
        return values
    if isinstance(value, (list, tuple, set)):
        values: list[str] = []
        for nested in value:
            values.extend(_string_values(nested, include_keys=include_keys))
        return values
    return []


def _redact_text(value: str) -> str:
    redacted = str(value)
    for pattern in SENSITIVE_TEXT_PATTERNS.values():
        redacted = pattern.sub(REDACTION, redacted)
    return redacted


def _without_allowed_blocklist_text(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_allowed_blocklist_text(nested)
            for key, nested in value.items()
            if key not in {"blocked_advisor_tasks", "allowed_advisor_tasks"}
        }
    if isinstance(value, list):
        return [_without_allowed_blocklist_text(item) for item in value]
    return value


def _detect_sensitive_text(value: Any) -> list[str]:
    scan_value = _without_allowed_blocklist_text(value)
    joined = "\n".join(_string_values(scan_value, include_keys=False))
    findings: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    return sorted(set(findings))


def _dangerous_field_paths(value: Any, path: str = "payload") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_FIELD_NAMES:
                findings.append(nested_path)
            findings.extend(_dangerous_field_paths(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            findings.extend(_dangerous_field_paths(nested, f"{path}[{index}]"))
    return findings


def _coerce_source_artifact(source: Any) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    if isinstance(source, dict) and source.get("bundle_type") == STATUS_BUNDLE_SCHEMA_VERSION:
        bundle = to_internal_evaluation_corpus_status_bundle_json_safe_v1(source)
        return "status_bundle", bundle, summarize_internal_evaluation_corpus_status_bundle_v1(bundle), {}
    if isinstance(source, dict) and source.get("schema_version") == REVIEW_CARDS_SCHEMA_VERSION:
        review = _json_safe(deepcopy(source))
        review_summary = summarize_internal_evaluation_corpus_review_cards_v1(review)
        bundle = build_internal_evaluation_corpus_status_bundle_v1([])
        bundle.update(
            {
                "readiness_label": review.get("readiness_label", "needs_operator_review"),
                "case_count": int(review.get("card_count", 0) or 0),
                "category_count": len(_as_list(review.get("categories_covered"))),
                "categories_covered": _as_list(review.get("categories_covered")),
                "missing_categories": [],
                "invalid_case_count": 0,
                "invalid_card_count": int(review.get("invalid_card_count", 0) or 0),
                "duplicate_case_id_count": int(review.get("duplicate_case_id_count", 0) or 0),
            }
        )
        return "review_cards", bundle, summarize_internal_evaluation_corpus_status_bundle_v1(bundle), review_summary
    if source is None:
        bundle = build_internal_evaluation_corpus_status_bundle_v1()
        return "default_status_bundle", bundle, summarize_internal_evaluation_corpus_status_bundle_v1(bundle), {}
    bundle = build_internal_evaluation_corpus_status_bundle_v1(source)
    review = build_internal_evaluation_corpus_review_cards_v1(source)
    return "corpus_or_cases", bundle, summarize_internal_evaluation_corpus_status_bundle_v1(bundle), summarize_internal_evaluation_corpus_review_cards_v1(review)


def _queue_payload_for_summary(summary: dict[str, Any], source_artifact_type: str) -> dict[str, Any]:
    invalid_count = int(summary.get("invalid_case_count", 0) or 0) + int(summary.get("invalid_card_count", 0) or 0)
    suggestion_type = "test_coverage_review"
    task_type = "gap_taxonomy_review"
    if invalid_count:
        suggestion_type = "safety_policy_review"
        task_type = "wording_risk_review"
    elif int(summary.get("category_count", 0) or 0) == 0:
        suggestion_type = "gap_taxonomy_review"
        task_type = "gap_taxonomy_review"
    template = get_advisor_prompt_template(task_type)
    item = create_empty_advisor_review_queue_item(
        suggestion_id=f"internal_corpus_advisor_review_{source_artifact_type}_v1",
        trigger_reason=(
            "internal corpus advisor review proposal; "
            f"scope={REVIEW_SCOPE}; readiness={summary.get('readiness_label', 'unknown')}"
        ),
        recommended_action="operator review of redacted internal corpus coverage/status only",
        suggestion_type=suggestion_type,
        source="diagnostic",
        capability_scope=["internal_evaluation_corpus", REVIEW_SCOPE],
        risk_level="medium" if invalid_count else "low",
        requires_operator_approval=True,
        advisor_call_allowed=False,
        advisor_call_mode="local_scan_only",
        review_status="pending_review",
        operator_decision="pending_review",
        notes=[
            "redacted structural summary only",
            "no advisor/model call authorized",
            f"advisor_prompt_template_id:{template.template_id}",
        ],
        safety_flags=AdvisorReviewQueueSafetyFlags(),
    )
    errors = validate_advisor_review_queue_item(item)
    if errors:
        raise ValueError("internal corpus advisor queue payload invalid: " + "; ".join(errors))
    return advisor_review_queue_item_to_dict(item)


def build_internal_corpus_advisor_review_payload_v1(status_bundle_or_review: Any = None) -> dict[str, Any]:
    """Build a redacted, in-memory advisor-review proposal payload."""
    source_artifact_type, bundle, summary, review_summary = _coerce_source_artifact(status_bundle_or_review)
    safety_posture = bundle.get("safety_posture", {}) if isinstance(bundle.get("safety_posture", {}), dict) else {}
    redacted_summary = {
        "summary_mode": SUMMARY_MODE,
        "readiness_label": str(bundle.get("readiness_label", summary.get("readiness_label", "needs_operator_review"))),
        "case_count": int(bundle.get("case_count", summary.get("case_count", 0)) or 0),
        "category_count": int(bundle.get("category_count", summary.get("category_count", 0)) or 0),
        "categories_covered": _as_list(bundle.get("categories_covered", [])),
        "missing_category_count": len(_as_list(bundle.get("missing_categories", []))),
        "invalid_case_count": int(bundle.get("invalid_case_count", summary.get("invalid_case_count", 0)) or 0),
        "invalid_card_count": int(bundle.get("invalid_card_count", summary.get("invalid_card_count", 0)) or 0),
        "duplicate_case_id_count": int(bundle.get("duplicate_case_id_count", summary.get("duplicate_case_id_count", 0)) or 0),
        "allowed_next_step_count": len(_as_list(bundle.get("allowed_next_steps", []))),
        "blocked_next_step_count": len(_as_list(bundle.get("blocked_next_steps", []))),
        "safety_posture_true_count": sum(1 for value in safety_posture.values() if bool(value)),
        "safety_posture_key_count": len(safety_posture),
        "review_card_count": int(review_summary.get("total_cards", 0) or bundle.get("case_count", 0) or 0),
        "review_invalid_count": int(review_summary.get("invalid_cards", bundle.get("invalid_card_count", 0)) or 0),
        "non_execution_flags": {
            "runner_created": False,
            "scoring_created": False,
            "model_calls": False,
            "advisor_calls": False,
            "safe_to_execute": False,
        },
    }
    queue_payload = _queue_payload_for_summary(redacted_summary, source_artifact_type)
    payload = {
        "adapter_type": ADAPTER_TYPE,
        "schema_version": "1.0",
        "source_artifact_type": source_artifact_type,
        "source_schema_version": str(bundle.get("schema_version", "unknown")),
        "source_readiness_label": redacted_summary["readiness_label"],
        "review_scope": REVIEW_SCOPE,
        "redacted_summary": redacted_summary,
        "advisor_prompt_template_id": DEFAULT_ADVISOR_TEMPLATE_ID,
        "advisor_review_queue_payload": queue_payload,
        "allowed_advisor_tasks": list(ALLOWED_ADVISOR_TASKS),
        "blocked_advisor_tasks": list(BLOCKED_ADVISOR_TASKS),
        "non_authoritative": True,
        "requires_operator_approval": True,
        "requires_validation": True,
        "not_runtime_truth": True,
        "advisor_call_allowed": False,
        "advisor_call_mode": "local_scan_only",
        "model_calls": False,
        "advisor_calls": False,
        "safe_to_execute": False,
        "raw_prompts_included": False,
        "protected_material_included": False,
        "answer_keys_included": False,
        "hidden_prompts_included": False,
        "raw_private_text_included": False,
        "official_score_claim": False,
        "runner_created": False,
        "scoring_created": False,
        "queue_persistence_performed": False,
        "parallel_advisor_queue_created": False,
        "parallel_advisor_prompt_system_created": False,
        "parallel_audit_system_created": False,
        "side_effects": {
            "in_memory_only": True,
            "writes_performed": False,
            "queue_persistence_performed": False,
            "model_calls_performed": False,
            "advisor_calls_performed": False,
            "runtime_changed": False,
            "training_performed": False,
        },
    }
    return _json_safe(payload)


def validate_internal_corpus_advisor_review_payload_v1(payload: Any) -> dict[str, Any]:
    """Validate adapter payload safety and return structured diagnostics."""
    issues: list[str] = []
    item = payload if isinstance(payload, dict) else {}
    if not isinstance(payload, dict):
        issues.append("payload must be a dict")
    if item.get("adapter_type") != ADAPTER_TYPE:
        issues.append("invalid adapter_type")
    if item.get("review_scope") != REVIEW_SCOPE:
        issues.append("invalid review_scope")
    for key, message in FORBIDDEN_TRUE_FIELDS.items():
        if bool(item.get(key, False)):
            issues.append(message)
    for key in ("non_authoritative", "requires_operator_approval", "requires_validation", "not_runtime_truth"):
        if item.get(key) is not True:
            issues.append(f"{key} must be true")
    if item.get("advisor_call_mode") != "local_scan_only":
        issues.append("advisor_call_mode must remain local_scan_only")
    side_effects = item.get("side_effects", {}) if isinstance(item.get("side_effects", {}), dict) else {}
    for key, message in FORBIDDEN_TRUE_FIELDS.items():
        if bool(side_effects.get(key, False)):
            issues.append(f"side_effects.{message}")
    for path in _dangerous_field_paths(item):
        issues.append(f"forbidden field: {path}")
    for finding in _detect_sensitive_text(item):
        issues.append(finding)
    queue_payload = item.get("advisor_review_queue_payload", {})
    if isinstance(queue_payload, dict):
        try:
            queue_item = create_empty_advisor_review_queue_item(**{k: v for k, v in queue_payload.items() if k not in {"schema_version", "created_at", "updated_at", "safety_flags"}})
            queue_item.created_at = str(queue_payload.get("created_at", queue_item.created_at))
            queue_item.updated_at = str(queue_payload.get("updated_at", queue_item.updated_at))
            queue_errors = validate_advisor_review_queue_item(queue_item)
            issues.extend(f"advisor_queue: {error}" for error in queue_errors)
        except Exception as exc:  # normal validation path: report, do not raise
            issues.append(f"advisor_queue invalid: {exc}")
        if bool(queue_payload.get("advisor_call_allowed", False)):
            issues.append("advisor queue advisor_call_allowed must remain false")
        if queue_payload.get("advisor_call_mode") != "local_scan_only":
            issues.append("advisor queue advisor_call_mode must remain local_scan_only")
    else:
        issues.append("advisor_review_queue_payload must be a dict")
    return {
        "schema_version": "internal_corpus_to_advisor_review_adapter_validation_v1",
        "summary_mode": SUMMARY_MODE,
        "valid": not issues,
        "issue_count": len(sorted(set(issues))),
        "issues": sorted(set(issues)),
        "adapter_type": str(item.get("adapter_type", "unknown")),
        "non_authoritative": bool(item.get("non_authoritative", False)),
        "requires_operator_approval": bool(item.get("requires_operator_approval", False)),
        "advisor_call_allowed": bool(item.get("advisor_call_allowed", True)),
        "model_calls": bool(item.get("model_calls", True)),
        "safe_to_execute": bool(item.get("safe_to_execute", True)),
        "writes_performed": bool(side_effects.get("writes_performed", True)),
        "queue_persistence_performed": bool(item.get("queue_persistence_performed", True)),
        "runner_created": bool(item.get("runner_created", True)),
        "scoring_created": bool(item.get("scoring_created", True)),
    }


def summarize_internal_corpus_advisor_review_payload_v1(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a count-only/redacted summary of an adapter payload."""
    item = to_internal_corpus_advisor_review_payload_json_safe_v1(payload if isinstance(payload, dict) else {})
    validation = validate_internal_corpus_advisor_review_payload_v1(item)
    summary = item.get("redacted_summary", {}) if isinstance(item.get("redacted_summary", {}), dict) else {}
    return _json_safe(
        {
            "schema_version": "internal_corpus_to_advisor_review_adapter_summary_v1",
            "summary_mode": SUMMARY_MODE,
            "adapter_type": str(item.get("adapter_type", "unknown")),
            "review_scope": str(item.get("review_scope", "unknown")),
            "readiness_label": str(item.get("source_readiness_label", summary.get("readiness_label", "needs_operator_review"))),
            "category_count": int(summary.get("category_count", 0) or 0),
            "invalid_count": int(summary.get("invalid_case_count", 0) or 0) + int(summary.get("invalid_card_count", 0) or 0),
            "allowed_advisor_task_count": len(_as_list(item.get("allowed_advisor_tasks"))),
            "blocked_advisor_task_count": len(_as_list(item.get("blocked_advisor_tasks"))),
            "safety_posture_summary": {
                "non_authoritative": bool(item.get("non_authoritative", False)),
                "requires_operator_approval": bool(item.get("requires_operator_approval", False)),
                "advisor_call_allowed": bool(item.get("advisor_call_allowed", True)),
                "model_calls": bool(item.get("model_calls", True)),
                "safe_to_execute": bool(item.get("safe_to_execute", True)),
                "runner_created": bool(item.get("runner_created", True)),
                "scoring_created": bool(item.get("scoring_created", True)),
                "valid": bool(validation.get("valid", False)),
            },
            "validation_issue_count": int(validation.get("issue_count", 0) or 0),
            "qualitative_only": True,
            "no_scores": True,
            "not_official_score": True,
            "redacted_count_only": True,
        }
    )


def to_internal_corpus_advisor_review_payload_json_safe_v1(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deep JSON-safe adapter payload copy without writing files."""
    return _json_safe(deepcopy(payload))


def render_internal_corpus_advisor_review_payload_markdown_v1(payload: dict[str, Any]) -> str:
    """Render safe adapter payload Markdown without raw prompts or protected content."""
    item = to_internal_corpus_advisor_review_payload_json_safe_v1(payload if isinstance(payload, dict) else {})
    summary = summarize_internal_corpus_advisor_review_payload_v1(item)
    redacted = item.get("redacted_summary", {}) if isinstance(item.get("redacted_summary", {}), dict) else {}
    lines = [
        "# WESLR Internal Corpus Advisor Review Adapter Payload V1",
        "",
        "- summary mode: redacted_count_only",
        f"- adapter type: {summary['adapter_type']}",
        f"- review scope: {summary['review_scope']}",
        f"- readiness label: {summary['readiness_label']}",
        f"- category coverage count: {summary['category_count']}",
        f"- invalid count: {summary['invalid_count']}",
        f"- allowed advisor task count: {summary['allowed_advisor_task_count']}",
        f"- blocked advisor task count: {summary['blocked_advisor_task_count']}",
        f"- missing category count: {int(redacted.get('missing_category_count', 0) or 0)}",
        "- non-authoritative: true",
        "- requires operator approval: true",
        "- advisor call allowed: false",
        "- model calls: false",
        "- scoring created: false",
        "- runner created: false",
        "- safe to execute: false",
        "- queue persistence performed: false",
    ]
    markdown = "\n".join(lines)
    for pattern in SENSITIVE_TEXT_PATTERNS.values():
        markdown = pattern.sub(REDACTION, markdown)
    return markdown
