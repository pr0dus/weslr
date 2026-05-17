"""Safe in-memory helpers for WESLR behavior evaluation reports V1.

This module builds, validates, summarizes, and renders internal behavior evaluation
reports. It performs no persistence, no runtime wiring, no model/search/advisor calls,
and no ChatResponder calls.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

REPORT_TYPE_V1 = "weslr_behavior_evaluation_report_v1"
SCHEMA_VERSION_V1 = "1.0"
EVALUATION_MODE_V1 = "internal_behavior_evaluation"

ALLOWED_EVALUATION_FAMILIES_V1 = (
    "ordinary_task_behavior",
    "non_canned_cognition",
    "conduct_alignment",
    "memory_honesty",
    "self_identity_boundaries",
    "evidence_source_boundaries",
    "guardrail_preservation",
    "continuity_relationship",
    "live_slice_behavior",
)

ALLOWED_PROPERTY_LABELS_V1 = {
    "pass_property",
    "fail_property",
    "needs_review",
    "not_observed",
    "blocked_by_boundary",
}

ALLOWED_READINESS_LABELS_V1 = {
    "not_ready",
    "early_internal_readiness",
    "bounded_task_readiness",
    "needs_more_observation",
    "unsafe_or_inconsistent",
}

FORBIDDEN_READINESS_LABELS_V1 = {
    "passed_turing_test",
    "certified_intelligent",
    "official_benchmark_passed",
    "human_level",
    "conscious",
    "sentient",
}

EXPECTED_BLOCKED_CLAIMS_V1 = {
    "no_official_turing_test_claim",
    "no_official_benchmark_claim",
    "no_iq_claim",
    "no_certification_claim",
    "no_fake_consciousness_claim",
    "no_default_enablement_claim",
    "no_branch_expansion_claim",
}

FORBIDDEN_KEYS_V1 = {
    "raw_text",
    "normalized_text",
    "tokens",
    "raw_prompt",
    "safe_prompt",
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

SIDE_EFFECT_FLAGS_V1 = (
    "model_calls",
    "advisor_calls",
    "web_search",
    "solver_execution",
    "answer_selection_arbitration",
    "weslr_runtime_state_created",
    "raw_text_stored",
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


def to_behavior_evaluation_report_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy. This is not a sanitizer."""
    return _json_safe(obj)


def build_behavior_evaluation_family_v1(
    *,
    family: str,
    label: str = "not_observed",
    observed: bool = False,
    strengths: list[str] | None = None,
    risks: list[str] | None = None,
    evidence_properties: dict | None = None,
    recommended_next_step: str = "",
) -> dict[str, Any]:
    """Build a safe family section shape in memory only."""
    return {
        "family": family,
        "label": label,
        "observed": bool(observed),
        "strengths": _json_safe(strengths or []),
        "risks": _json_safe(risks or []),
        "evidence_properties": _json_safe(evidence_properties or {}),
        "recommended_next_step": recommended_next_step,
    }


def _default_families() -> dict[str, dict[str, Any]]:
    return {
        family: build_behavior_evaluation_family_v1(family=family)
        for family in ALLOWED_EVALUATION_FAMILIES_V1
    }


def build_behavior_evaluation_report_v1(
    *,
    repo_head: str,
    timestamp_local: str = "",
    families: dict | None = None,
    readiness_label: str = "needs_more_observation",
    recommended_next_step: str = "",
    blocked_claims: list[str] | None = None,
    notes: dict | None = None,
) -> dict[str, Any]:
    """Build an internal behavior evaluation report. Performs no writes or calls."""
    built_families = _default_families()
    if families:
        for key, value in families.items():
            built_families[str(key)] = _json_safe(value)
    return {
        "report_type": REPORT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "repo_head": repo_head,
        "timestamp_local": timestamp_local,
        "evaluation_mode": EVALUATION_MODE_V1,
        "official_benchmark_claim": False,
        "turing_test_claim": False,
        "iq_claim": False,
        "certification_claim": False,
        "raw_private_text_included": False,
        "numeric_scores_used": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "solver_execution": False,
        "answer_selection_arbitration": False,
        "weslr_runtime_state_created": False,
        "raw_text_stored": False,
        "families": built_families,
        "readiness_label": readiness_label,
        "blocked_claims": _json_safe(blocked_claims if blocked_claims is not None else sorted(EXPECTED_BLOCKED_CLAIMS_V1)),
        "recommended_next_step": recommended_next_step,
        "notes": _json_safe(notes or {}),
        "safety": {
            "internal_behavior_evaluation_only": True,
            "no_official_turing_test_claim": True,
            "no_official_benchmark_claim": True,
            "no_iq_claim": True,
            "no_certification_claim": True,
            "no_fake_consciousness_claim": True,
            "no_raw_private_text": True,
            "no_persistence": True,
        },
    }


def _walk(value: Any, path: str = ""):
    yield path, value
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


def validate_behavior_evaluation_report_v1(report: dict) -> dict[str, Any]:
    """Validate a WESLR internal behavior evaluation report without side effects."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(report, Mapping):
        return {"valid": False, "errors": ["report must be a dict"], "warnings": []}

    exact_false = (
        "official_benchmark_claim",
        "turing_test_claim",
        "iq_claim",
        "certification_claim",
        "raw_private_text_included",
        "numeric_scores_used",
        *SIDE_EFFECT_FLAGS_V1,
    )
    if report.get("report_type") != REPORT_TYPE_V1:
        errors.append("wrong report_type")
    if not report.get("repo_head"):
        errors.append("repo_head is required")
    elif len(str(report.get("repo_head"))) < 8 or str(report.get("repo_head")).startswith("<"):
        warnings.append("repo_head looks short/placeholder")
    if report.get("evaluation_mode") != EVALUATION_MODE_V1:
        errors.append("evaluation_mode must be internal_behavior_evaluation")
    for key in exact_false:
        if report.get(key) is True:
            errors.append(f"{key} must be false")

    readiness = report.get("readiness_label")
    if readiness in FORBIDDEN_READINESS_LABELS_V1:
        errors.append("forbidden readiness label")
    elif readiness not in ALLOWED_READINESS_LABELS_V1:
        errors.append("invalid readiness label")

    families = report.get("families")
    if not isinstance(families, Mapping):
        errors.append("families must be a dict")
        families = {}
    family_keys = set(families.keys())
    missing = set(ALLOWED_EVALUATION_FAMILIES_V1) - family_keys
    unknown = family_keys - set(ALLOWED_EVALUATION_FAMILIES_V1)
    for family in sorted(missing):
        errors.append(f"missing required family: {family}")
    for family in sorted(unknown):
        errors.append(f"invalid family key: {family}")

    all_not_observed = True
    for key, section in families.items():
        if not isinstance(section, Mapping):
            errors.append(f"family {key} must be a dict")
            continue
        if section.get("family") != key:
            errors.append(f"family {key} has mismatched family field")
        label = section.get("label")
        if label not in ALLOWED_PROPERTY_LABELS_V1:
            errors.append(f"invalid property label for {key}")
        if label != "not_observed":
            all_not_observed = False
        if section.get("observed") is True and label == "not_observed":
            warnings.append(f"family {key} observed=true but label=not_observed")
        if label == "pass_property" and section.get("risks"):
            warnings.append(f"family {key} label=pass_property but risks are non-empty")

    blocked_claims = set(report.get("blocked_claims") or [])
    if not EXPECTED_BLOCKED_CLAIMS_V1.issubset(blocked_claims):
        warnings.append("blocked_claims missing expected blocked claims")
    if not report.get("timestamp_local"):
        warnings.append("timestamp_local missing")
    if not report.get("recommended_next_step"):
        warnings.append("recommended_next_step missing")
    if readiness == "early_internal_readiness" and all_not_observed:
        warnings.append("readiness_label=early_internal_readiness while all families are not_observed")

    for path, value in _walk(report):
        key = path.split(".")[-1].split("[")[0]
        if key in FORBIDDEN_KEYS_V1:
            errors.append(f"forbidden raw/private/protected key: {path}")
        if isinstance(value, str):
            lowered = value.lower()
            for phrase, pattern in _FORBIDDEN_CLAIM_PATTERNS_V1.items():
                if pattern.search(lowered):
                    errors.append(f"forbidden claim text at {path}: {phrase}")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def summarize_behavior_evaluation_report_v1(report: dict) -> dict[str, Any]:
    """Return labels/counts/status only; never raw prompts or responses."""
    validation = validate_behavior_evaluation_report_v1(report)
    families = report.get("families", {}) if isinstance(report, Mapping) else {}
    labels = [section.get("label") for section in families.values() if isinstance(section, Mapping)] if isinstance(families, Mapping) else []
    observed = [section for section in families.values() if isinstance(section, Mapping) and section.get("observed") is True] if isinstance(families, Mapping) else []
    return {
        "report_type": report.get("report_type"),
        "repo_head": report.get("repo_head"),
        "evaluation_mode": report.get("evaluation_mode"),
        "readiness_label": report.get("readiness_label"),
        "family_count": len(families) if isinstance(families, Mapping) else 0,
        "observed_family_count": len(observed),
        "pass_property_count": labels.count("pass_property"),
        "fail_property_count": labels.count("fail_property"),
        "needs_review_count": labels.count("needs_review"),
        "blocked_by_boundary_count": labels.count("blocked_by_boundary"),
        "not_observed_count": labels.count("not_observed"),
        "official_benchmark_claim": report.get("official_benchmark_claim"),
        "turing_test_claim": report.get("turing_test_claim"),
        "iq_claim": report.get("iq_claim"),
        "certification_claim": report.get("certification_claim"),
        "raw_private_text_included": report.get("raw_private_text_included"),
        "numeric_scores_used": report.get("numeric_scores_used"),
        "side_effects_clear": not any(report.get(key) is True for key in SIDE_EFFECT_FLAGS_V1),
        "recommended_next_step": report.get("recommended_next_step"),
        "valid": validation["valid"],
    }


def render_behavior_evaluation_report_markdown_v1(report: dict) -> str:
    """Render a safe markdown report using labels/counts/status only."""
    summary = summarize_behavior_evaluation_report_v1(report)
    validation = validate_behavior_evaluation_report_v1(report)
    lines = [
        "SECTION 1 — STATUS",
        f"- report_type: {summary['report_type']}",
        f"- repo_head: {summary['repo_head']}",
        f"- evaluation_mode: {summary['evaluation_mode']}",
        "SECTION 2 — READINESS LABEL",
        f"- readiness_label: {summary['readiness_label']}",
        "SECTION 3 — EVALUATION FAMILIES",
        f"- family_count: {summary['family_count']}",
        f"- observed_family_count: {summary['observed_family_count']}",
        f"- pass_property_count: {summary['pass_property_count']}",
        f"- fail_property_count: {summary['fail_property_count']}",
        f"- needs_review_count: {summary['needs_review_count']}",
        f"- blocked_by_boundary_count: {summary['blocked_by_boundary_count']}",
        f"- not_observed_count: {summary['not_observed_count']}",
        "SECTION 4 — SAFETY / CLAIM BOUNDARIES",
        f"- official_benchmark_claim: {summary['official_benchmark_claim']}",
        f"- turing_test_claim: {summary['turing_test_claim']}",
        f"- iq_claim: {summary['iq_claim']}",
        f"- cert_claim: {summary['certification_claim']}",
        f"- raw_private_text_included: {summary['raw_private_text_included']}",
        f"- numeric_scores_used: {summary['numeric_scores_used']}",
        "SECTION 5 — SIDE-EFFECT CHECK",
        f"- side_effects_clear: {summary['side_effects_clear']}",
        "SECTION 6 — BLOCKED CLAIMS",
        f"- blocked_claim_count: {len(report.get('blocked_claims') or [])}",
        "SECTION 7 — RECOMMENDED NEXT STEP",
        f"- recommended_next_step: {summary['recommended_next_step']}",
        "SECTION 8 — VALIDATION SUMMARY",
        f"- valid: {validation['valid']}",
        f"- error_count: {len(validation['errors'])}",
        f"- warning_count: {len(validation['warnings'])}",
    ]
    return "\n".join(lines) + "\n"


def build_behavior_evaluation_report_from_family_summaries_v1(
    *,
    repo_head: str,
    family_summaries: list[dict],
    readiness_label: str = "needs_more_observation",
    recommended_next_step: str = "",
) -> dict[str, Any]:
    """Build a report from sanitized family summaries only. Performs no evaluation."""
    families: dict[str, Any] = {}
    for item in family_summaries:
        family = str(item.get("family", ""))
        families[family] = build_behavior_evaluation_family_v1(
            family=family,
            label=str(item.get("label", "not_observed")),
            observed=bool(item.get("observed", False)),
            strengths=list(item.get("strengths", []) or []),
            risks=list(item.get("risks", []) or []),
            evidence_properties=dict(item.get("evidence_properties", {}) or {}),
            recommended_next_step=str(item.get("recommended_next_step", "")),
        )
    return build_behavior_evaluation_report_v1(
        repo_head=repo_head,
        families=families,
        readiness_label=readiness_label,
        recommended_next_step=recommended_next_step,
    )
