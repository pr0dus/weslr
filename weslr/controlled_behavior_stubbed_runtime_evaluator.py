"""Controlled behavior stubbed runtime evaluator helpers V1.

This module bridges metadata-only dry running to controlled stubbed observation.
It consumes safe synthetic/stub metadata only. It does not execute prompts, call
ChatResponder, call models/search/advisors, persist files, or write WESLR
runtime state.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from weslr.behavior_evaluation_report import (
    ALLOWED_EVALUATION_FAMILIES_V1,
    ALLOWED_PROPERTY_LABELS_V1,
    SIDE_EFFECT_FLAGS_V1,
    build_behavior_evaluation_family_v1,
    build_behavior_evaluation_report_v1,
    summarize_behavior_evaluation_report_v1,
    validate_behavior_evaluation_report_v1,
)
from weslr.controlled_behavior_dry_runner import (
    derive_family_label_from_observations_v1,
    derive_readiness_label_from_family_results_v1,
)
from weslr.controlled_behavior_prompt_set import (
    build_default_controlled_behavior_prompt_set_v1,
    summarize_controlled_behavior_prompt_set_v1,
    validate_controlled_behavior_prompt_item_v1,
    validate_controlled_behavior_prompt_set_v1,
)

EVALUATOR_TYPE_V1 = "weslr_controlled_behavior_stubbed_runtime_evaluator_v1"
SCHEMA_VERSION_V1 = "1.0"

OBSERVATION_MODES_V1 = {
    "metadata_only",
    "stubbed_runtime",
    "controlled_local_runtime",
    "live_runtime",
}
ACTIVE_OBSERVATION_MODE_V1 = "stubbed_runtime"

ALLOWED_STUB_SOURCES_V1 = {
    "synthetic_expected_metadata",
    "safe_test_override",
    "safe_synthetic_summary",
    "local_deterministic_metadata",
}

FORBIDDEN_STUB_SOURCES_V1 = {
    "external_model_output",
    "web_search_output",
    "advisor_output",
    "raw_chat_responder_output",
    "production_conversation_log",
    "private_user_text",
    "hidden_prompt",
    "answer_key",
    "protected_material",
}

FORBIDDEN_KEYS_V1 = {
    "raw_text",
    "raw_prompt",
    "response_text",
    "final_answer",
    "full_conversation",
    "source_urls",
    "hidden_prompt",
    "answer_key",
    "protected_material",
}

FORBIDDEN_CLAIM_TEXT_V1 = {
    "passed turing test",
    "official benchmark",
    "certified intelligent",
    "iq score",
    "human level",
    "conscious",
    "sentient",
    "soul",
    "alive",
}
_FORBIDDEN_CLAIM_PATTERNS_V1 = {
    phrase: re.compile(r"(?<![a-z0-9_])" + re.escape(phrase) + r"(?![a-z0-9_])")
    for phrase in FORBIDDEN_CLAIM_TEXT_V1
}

REQUIRED_FALSE_FLAGS_V1 = (
    "prompt_execution",
    "prompt_executed",
    "chat_responder_calls",
    "chat_responder_called",
    "model_calls",
    "advisor_calls",
    "web_search",
    "memory_writes",
    "raw_text_stored",
    "numeric_scores_used",
    "official_benchmark_claim",
    "turing_test_claim",
    "iq_claim",
    "certification_claim",
    "raw_private_text_included",
    "weslr_runtime_state_created",
)


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def to_controlled_behavior_stubbed_runtime_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy. This is not a sanitizer."""
    return _json_safe(obj)


def _walk(value: Any, path: str = ""):
    yield path, value
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


def _contains_forbidden_claim_text(value: str) -> str | None:
    lowered = value.lower()
    for phrase, pattern in _FORBIDDEN_CLAIM_PATTERNS_V1.items():
        if pattern.search(lowered):
            return phrase
    return None


def _has_source_url(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or "www." in lowered


def _safe_string_list(value: list[str] | None) -> list[str]:
    return [str(item) for item in (value or [])]


def build_stubbed_runtime_metadata_v1(
    *,
    prompt_id: str,
    family: str,
    observed: bool = True,
    property_label: str = "needs_review",
    properties_observed: list[str] | None = None,
    properties_missing: list[str] | None = None,
    safe_summary: str = "",
    stub_source: str = "safe_test_override",
) -> dict[str, Any]:
    """Build safe stubbed runtime observation metadata."""
    summary = " ".join(str(safe_summary or "").split())
    return {
        "prompt_id": str(prompt_id),
        "family": str(family),
        "runtime_mode": ACTIVE_OBSERVATION_MODE_V1,
        "prompt_executed": False,
        "chat_responder_called": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "memory_writes": False,
        "raw_text_stored": False,
        "observed": bool(observed),
        "property_label": str(property_label),
        "properties_observed": _safe_string_list(properties_observed),
        "properties_missing": _safe_string_list(properties_missing),
        "safe_summary": summary,
        "stub_source": str(stub_source),
    }


def validate_stubbed_runtime_metadata_v1(metadata: dict) -> dict[str, Any]:
    """Validate one stubbed runtime metadata object without side effects."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(metadata, Mapping):
        return {"valid": False, "errors": ["metadata must be a dict"], "warnings": []}

    if metadata.get("runtime_mode") != ACTIVE_OBSERVATION_MODE_V1:
        errors.append("runtime_mode must be stubbed_runtime")
    if metadata.get("family") not in ALLOWED_EVALUATION_FAMILIES_V1:
        errors.append(f"invalid family: {metadata.get('family')}")
    if metadata.get("property_label") not in ALLOWED_PROPERTY_LABELS_V1:
        errors.append(f"invalid property_label: {metadata.get('property_label')}")
    if metadata.get("stub_source") not in ALLOWED_STUB_SOURCES_V1:
        errors.append(f"invalid stub_source: {metadata.get('stub_source')}")
    if metadata.get("stub_source") in FORBIDDEN_STUB_SOURCES_V1:
        errors.append(f"forbidden stub_source: {metadata.get('stub_source')}")

    for key in ("prompt_executed", "chat_responder_called", "model_calls", "advisor_calls", "web_search", "memory_writes", "raw_text_stored"):
        if metadata.get(key) is True:
            errors.append(f"{key} must be false")

    for path, value in _walk(metadata):
        key = path.split(".")[-1].split("[")[0]
        if key in FORBIDDEN_KEYS_V1:
            errors.append(f"forbidden raw/private/protected key: {path}")
        if isinstance(value, str):
            phrase = _contains_forbidden_claim_text(value)
            if phrase:
                errors.append(f"forbidden claim text at {path}: {phrase}")
            if _has_source_url(value):
                errors.append(f"source URL not allowed at {path}")

    summary = str(metadata.get("safe_summary") or "")
    if len(summary) > 240:
        errors.append("safe_summary too long")
    if not summary:
        warnings.append("safe_summary missing")
    if bool(metadata.get("observed")) and metadata.get("property_label") == "not_observed":
        warnings.append("observed=true but property_label=not_observed")
    if not bool(metadata.get("observed")) and metadata.get("properties_observed"):
        warnings.append("observed=false but properties_observed not empty")
    if not metadata.get("properties_observed") and not metadata.get("properties_missing"):
        warnings.append("no properties_observed and no properties_missing")
    if metadata.get("stub_source") == "synthetic_expected_metadata" and metadata.get("property_label") == "pass_property":
        warnings.append("synthetic_expected_metadata with pass_property should be reviewed")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def evaluate_controlled_prompt_with_stubbed_runtime_v1(
    prompt_item: dict,
    *,
    stub_response_metadata: dict | None = None,
) -> dict[str, Any]:
    """Evaluate one controlled prompt item using safe stub metadata only."""
    prompt_validation = validate_controlled_behavior_prompt_item_v1(prompt_item)
    prompt_id = str(prompt_item.get("prompt_id") or "") if isinstance(prompt_item, Mapping) else ""
    family = str(prompt_item.get("family") or "") if isinstance(prompt_item, Mapping) else ""
    expected = list(prompt_item.get("expected_properties") or []) if isinstance(prompt_item, Mapping) else []

    if stub_response_metadata is None:
        metadata = build_stubbed_runtime_metadata_v1(
            prompt_id=prompt_id,
            family=family,
            observed=False,
            property_label="not_observed",
            properties_observed=[],
            properties_missing=[str(item) for item in expected],
            safe_summary="Synthetic prompt metadata registered; no stub observation supplied.",
            stub_source="local_deterministic_metadata",
        )
    else:
        metadata = to_controlled_behavior_stubbed_runtime_json_safe_v1(stub_response_metadata)

    validation = validate_stubbed_runtime_metadata_v1(metadata)
    errors = list(prompt_validation.get("errors") or []) + list(validation.get("errors") or [])
    warnings = list(prompt_validation.get("warnings") or []) + list(validation.get("warnings") or [])
    if metadata.get("prompt_id") != prompt_id:
        errors.append("stub metadata prompt_id mismatch")
    if metadata.get("family") != family:
        errors.append("stub metadata family mismatch")

    result = dict(metadata)
    result["validation"] = {"valid": not errors, "errors": errors, "warnings": warnings}
    return result


def _observation_for_family_label(stub: Mapping) -> dict[str, Any]:
    return {
        "property_label": stub.get("property_label"),
        "observed": bool(stub.get("observed")),
        "blocked_by_boundary": stub.get("property_label") == "blocked_by_boundary",
    }


def evaluate_prompt_set_with_stubbed_runtime_v1(
    prompt_set: dict | None = None,
    *,
    stub_metadata_by_prompt_id: dict | None = None,
    repo_head: str = "",
    timestamp_local: str = "",
    recommended_next_step: str = "RUN_WESLR_CONTROLLED_BEHAVIOR_STUBBED_RUNTIME_REPORT_V1",
) -> dict[str, Any]:
    """Evaluate a controlled prompt set with safe stubbed runtime metadata only."""
    prompt_set = to_controlled_behavior_stubbed_runtime_json_safe_v1(prompt_set if prompt_set is not None else build_default_controlled_behavior_prompt_set_v1())
    prompt_set_validation = validate_controlled_behavior_prompt_set_v1(prompt_set)
    prompts = prompt_set.get("prompts", []) if isinstance(prompt_set, Mapping) else []
    valid_prompt_ids = {str(item.get("prompt_id")) for item in prompts if isinstance(item, Mapping) and item.get("prompt_id")}
    stubs = stub_metadata_by_prompt_id or {}
    stub_errors: list[str] = []
    stub_warnings: list[str] = []
    if not isinstance(stubs, Mapping):
        stub_errors.append("stub_metadata_by_prompt_id must be a mapping")
        stubs = {}
    for prompt_id in stubs.keys():
        if str(prompt_id) not in valid_prompt_ids:
            stub_errors.append(f"unknown stub prompt_id: {prompt_id}")

    observations_by_family: dict[str, list[dict[str, Any]]] = {family: [] for family in ALLOWED_EVALUATION_FAMILIES_V1}
    stubbed_observations: list[dict[str, Any]] = []
    for prompt in prompts if isinstance(prompts, list) else []:
        if not isinstance(prompt, Mapping):
            continue
        prompt_id = str(prompt.get("prompt_id") or "")
        family = str(prompt.get("family") or "")
        supplied_stub = stubs.get(prompt_id) if isinstance(stubs, Mapping) else None
        observation = evaluate_controlled_prompt_with_stubbed_runtime_v1(prompt, stub_response_metadata=supplied_stub)
        stubbed_observations.append(observation)
        validation = observation.get("validation", {})
        if isinstance(validation, Mapping):
            if validation.get("valid") is False:
                stub_errors.extend(str(error) for error in (validation.get("errors") or []))
            stub_warnings.extend(str(warning) for warning in (validation.get("warnings") or []))
        if family in observations_by_family:
            observations_by_family[family].append(observation)

    family_results: dict[str, dict[str, Any]] = {}
    for family in ALLOWED_EVALUATION_FAMILIES_V1:
        observations = observations_by_family.get(family, [])
        label = derive_family_label_from_observations_v1([_observation_for_family_label(item) for item in observations])
        family_results[family] = build_behavior_evaluation_family_v1(
            family=family,
            label=label,
            observed=any(bool(item.get("observed")) for item in observations),
            strengths=["safe_stubbed_metadata_observed"] if label == "pass_property" else [],
            risks=["stubbed_observation_needs_review"] if label in {"needs_review", "not_observed"} else [],
            evidence_properties={
                "observation_mode": ACTIVE_OBSERVATION_MODE_V1,
                "observation_count": len(observations),
                "prompt_execution": False,
                "observations": observations,
            },
            recommended_next_step=recommended_next_step,
        )

    readiness_label = derive_readiness_label_from_family_results_v1(family_results)
    report = build_behavior_evaluation_report_v1(
        repo_head=repo_head,
        timestamp_local=timestamp_local,
        families=family_results,
        readiness_label=readiness_label,
        recommended_next_step=recommended_next_step,
        notes={"evaluator": EVALUATOR_TYPE_V1, "observation_mode": ACTIVE_OBSERVATION_MODE_V1, "prompt_execution": False},
    )
    report_validation = validate_behavior_evaluation_report_v1(report)
    result = {
        "evaluator_type": EVALUATOR_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "observation_mode": ACTIVE_OBSERVATION_MODE_V1,
        "prompt_execution": False,
        "chat_responder_calls": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "numeric_scores_used": False,
        "official_benchmark_claim": False,
        "turing_test_claim": False,
        "iq_claim": False,
        "certification_claim": False,
        "raw_private_text_included": False,
        "weslr_runtime_state_created": False,
        "prompt_set_summary": summarize_controlled_behavior_prompt_set_v1(prompt_set),
        "family_results": family_results,
        "stubbed_observations": stubbed_observations,
        "report": report,
        "recommended_next_step": recommended_next_step,
        "validation": {
            "prompt_set": prompt_set_validation,
            "stubs": {"valid": not stub_errors, "errors": stub_errors, "warnings": stub_warnings},
            "report": report_validation,
        },
    }
    result["validation"] = validate_controlled_behavior_stubbed_runtime_result_v1(result)
    return result


def validate_controlled_behavior_stubbed_runtime_result_v1(result: dict) -> dict[str, Any]:
    """Validate a controlled behavior stubbed runtime result."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(result, Mapping):
        return {"valid": False, "errors": ["result must be a dict"], "warnings": []}
    if result.get("evaluator_type") != EVALUATOR_TYPE_V1:
        errors.append("wrong evaluator_type")
    if result.get("observation_mode") != ACTIVE_OBSERVATION_MODE_V1:
        errors.append("observation_mode must be stubbed_runtime")
    for key in (
        "prompt_execution",
        "chat_responder_calls",
        "model_calls",
        "advisor_calls",
        "web_search",
        "numeric_scores_used",
        "official_benchmark_claim",
        "turing_test_claim",
        "iq_claim",
        "certification_claim",
        "raw_private_text_included",
        "weslr_runtime_state_created",
    ):
        if result.get(key) is True:
            errors.append(f"{key} must be false")

    report = result.get("report")
    if not isinstance(report, Mapping):
        errors.append("missing report")
        report_validation = {"valid": False, "errors": ["missing report"], "warnings": []}
    else:
        report_validation = validate_behavior_evaluation_report_v1(report)
        if not report_validation["valid"]:
            errors.append("report validation invalid")
            errors.extend(str(error) for error in report_validation.get("errors", []))

    observations = result.get("stubbed_observations")
    if not isinstance(observations, list):
        errors.append("stubbed_observations must be a list")
        observations = []
    for index, observation in enumerate(observations):
        validation = validate_stubbed_runtime_metadata_v1(observation)
        if not validation["valid"]:
            errors.append(f"invalid stubbed_observation[{index}]")
            errors.extend(str(error) for error in validation["errors"])
        warnings.extend(str(warning) for warning in validation["warnings"])
        nested = observation.get("validation") if isinstance(observation, Mapping) else None
        if isinstance(nested, Mapping) and nested.get("valid") is False:
            errors.append(f"stubbed_observation[{index}] nested validation invalid")
            errors.extend(str(error) for error in (nested.get("errors") or []))

    nested_validation = result.get("validation", {})
    if isinstance(nested_validation, Mapping):
        for key in ("prompt_set", "stubs", "report"):
            section = nested_validation.get(key)
            if isinstance(section, Mapping):
                if section.get("valid") is False:
                    errors.append(f"{key} validation invalid")
                    errors.extend(str(error) for error in (section.get("errors") or []))
                warnings.extend(str(warning) for warning in (section.get("warnings") or []))

    for path, value in _walk(result):
        key = path.split(".")[-1].split("[")[0]
        if key in FORBIDDEN_KEYS_V1:
            errors.append(f"forbidden raw/private/protected key: {path}")
        if isinstance(value, str):
            phrase = _contains_forbidden_claim_text(value)
            if phrase:
                errors.append(f"forbidden claim text at {path}: {phrase}")
            if _has_source_url(value):
                errors.append(f"source URL not allowed at {path}")

    if not str(report.get("repo_head", "") if isinstance(report, Mapping) else "") or len(str(report.get("repo_head", "") if isinstance(report, Mapping) else "")) < 8:
        warnings.append("repo_head missing/short")
    labels = [section.get("label") for section in result.get("family_results", {}).values() if isinstance(section, Mapping)] if isinstance(result.get("family_results"), Mapping) else []
    if labels and all(label == "not_observed" for label in labels):
        warnings.append("all families not_observed")
    if not result.get("recommended_next_step"):
        warnings.append("recommended_next_step missing")
    if not observations or not any(bool(item.get("observed")) for item in observations if isinstance(item, Mapping)):
        warnings.append("no stub metadata supplied")
    if isinstance(report_validation, Mapping):
        warnings.extend(str(warning) for warning in report_validation.get("warnings", []))

    # De-duplicate while preserving order for stable tests and reports.
    deduped_errors = list(dict.fromkeys(errors))
    deduped_warnings = list(dict.fromkeys(warnings))
    return {"valid": not deduped_errors, "errors": deduped_errors, "warnings": deduped_warnings}


def summarize_controlled_behavior_stubbed_runtime_result_v1(result: dict) -> dict[str, Any]:
    """Return label/count/status-only summary for stubbed runtime results."""
    validation = validate_controlled_behavior_stubbed_runtime_result_v1(result)
    prompt_summary = result.get("prompt_set_summary", {}) if isinstance(result, Mapping) else {}
    family_results = result.get("family_results", {}) if isinstance(result, Mapping) else {}
    family_labels = {
        family: section.get("label")
        for family, section in family_results.items()
        if isinstance(section, Mapping)
    } if isinstance(family_results, Mapping) else {}
    observations = result.get("stubbed_observations", []) if isinstance(result, Mapping) else []
    report_summary = summarize_behavior_evaluation_report_v1(result.get("report", {})) if isinstance(result, Mapping) and isinstance(result.get("report"), Mapping) else {}
    return {
        "evaluator_type": result.get("evaluator_type") if isinstance(result, Mapping) else None,
        "observation_mode": result.get("observation_mode") if isinstance(result, Mapping) else None,
        "prompt_execution": bool(result.get("prompt_execution", True)) if isinstance(result, Mapping) else True,
        "prompt_count": prompt_summary.get("prompt_count", 0) if isinstance(prompt_summary, Mapping) else 0,
        "family_count": len(family_labels),
        "readiness_label": report_summary.get("readiness_label"),
        "family_labels": family_labels,
        "observed_prompt_count": sum(1 for item in observations if isinstance(item, Mapping) and item.get("observed") is True),
        "stubbed_observation_count": len(observations) if isinstance(observations, list) else 0,
        "validation_valid": validation["valid"],
        "errors_count": len(validation["errors"]),
        "warnings_count": len(validation["warnings"]),
        "official_benchmark_claim": result.get("official_benchmark_claim") if isinstance(result, Mapping) else None,
        "turing_test_claim": result.get("turing_test_claim") if isinstance(result, Mapping) else None,
        "iq_claim": result.get("iq_claim") if isinstance(result, Mapping) else None,
        "certification_claim": result.get("certification_claim") if isinstance(result, Mapping) else None,
        "numeric_scores_used": result.get("numeric_scores_used") if isinstance(result, Mapping) else None,
        "raw_private_text_included": result.get("raw_private_text_included") if isinstance(result, Mapping) else None,
        "side_effects_clear": not any(result.get(key) is True for key in ("model_calls", "advisor_calls", "web_search", "weslr_runtime_state_created", *SIDE_EFFECT_FLAGS_V1)) if isinstance(result, Mapping) else False,
        "recommended_next_step": result.get("recommended_next_step") if isinstance(result, Mapping) else None,
    }


def render_controlled_behavior_stubbed_runtime_markdown_v1(result: dict) -> str:
    """Render safe markdown using labels/counts/status only."""
    summary = summarize_controlled_behavior_stubbed_runtime_result_v1(result)
    validation = validate_controlled_behavior_stubbed_runtime_result_v1(result)
    lines = [
        "SECTION 1 — STATUS",
        f"- evaluator_type: {summary['evaluator_type']}",
        f"- observation_mode: {summary['observation_mode']}",
        f"- prompt_execution: {summary['prompt_execution']}",
        "SECTION 2 — STUBBED RUNTIME BOUNDARIES",
        "- chat_responder_calls: False",
        "- model_calls: False",
        "- advisor_calls: False",
        "- web_search: False",
        "- persistence: False",
        "SECTION 3 — FAMILY RESULTS",
        f"- family_count: {summary['family_count']}",
        f"- observed_prompt_count: {summary['observed_prompt_count']}",
        f"- stubbed_observation_count: {summary['stubbed_observation_count']}",
    ]
    for family, label in sorted(summary["family_labels"].items()):
        lines.append(f"- {family}: {label}")
    lines.extend([
        "SECTION 4 — READINESS LABEL",
        f"- readiness_label: {summary['readiness_label']}",
        "SECTION 5 — SAFETY / CLAIM BOUNDARIES",
        f"- official_benchmark_claim: {summary['official_benchmark_claim']}",
        f"- turing_test_claim: {summary['turing_test_claim']}",
        f"- iq_claim: {summary['iq_claim']}",
        f"- certification_claim: {summary['certification_claim']}",
        f"- numeric_scores_used: {summary['numeric_scores_used']}",
        f"- raw_private_text_included: {summary['raw_private_text_included']}",
        f"- side_effects_clear: {summary['side_effects_clear']}",
        "SECTION 6 — VALIDATION SUMMARY",
        f"- valid: {validation['valid']}",
        f"- error_count: {len(validation['errors'])}",
        f"- warning_count: {len(validation['warnings'])}",
        "SECTION 7 — RECOMMENDED NEXT STEP",
        f"- recommended_next_step: {summary['recommended_next_step']}",
    ])
    return "\n".join(lines) + "\n"
