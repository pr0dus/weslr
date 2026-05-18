#!/usr/bin/env python3
"""WESLR ranked response shadow evaluation report helpers V1.

Pure, in-memory helpers for summarizing ranked response shadow scenario
results. This module is helper-only: it does not wire runtime behavior,
generate final answers, execute prompts, call external providers, persist state,
write files, use processes, or perform network work.
"""

from __future__ import annotations

import copy
import json
from collections import Counter
from collections.abc import Mapping
from typing import Any

from weslr import ranked_response_shadow_evaluation_scenarios as scenarios

SCHEMA_VERSION_V1 = "ranked_response_shadow_evaluation_report_schema_v1"
HELPER_NAME_V1 = "ranked_response_shadow_evaluation_report_v1"
REPORT_TYPE_V1 = "ranked_response_shadow_evaluation_report_v1"

READINESS_LABELS_V1 = [
    "ranked_response_shadow_report_helpers_implemented",
    "metadata_only_report_surface",
    "shadow_evaluation_only",
    "runtime_integration_not_authorized",
    "final_answer_not_generated",
    "raw_prompt_response_not_retained",
    "model_search_advisor_not_called",
    "persistence_not_performed",
    "official_evaluation_not_claimed",
    "voice_downstream_not_current_priority",
]

SAFE_FALSE_FLAGS_V1 = {
    "runtime_wired": False,
    "final_answer_generated": False,
    "raw_prompt_retained": False,
    "raw_response_retained": False,
    "model_call_made": False,
    "search_call_made": False,
    "advisor_call_made": False,
    "persistence_performed": False,
    "official_evaluation_claimed": False,
}

FORBIDDEN_KEYS_V1 = {
    "raw_text",
    "raw_prompt",
    "prompt_text",
    "safe_prompt",
    "raw_response",
    "response_text",
    "final_answer",
    "final_answer_text",
    "full_conversation",
    "hidden_prompt",
    "answer_key",
    "answer_keys",
    "private_content",
    "private_user_content",
    "protected_material",
    "candidate_prose",
    "model_output",
    "model_outputs",
    "official_score",
    "numeric_score",
    "iq_score",
    "benchmark_score",
}

TRUE_FORBIDDEN_FLAGS_V1 = {
    "runtime_wired": "runtime_wired_true",
    "final_answer_generated": "final_answer_generated_true",
    "model_call_made": "model_call_made_true",
    "search_call_made": "search_call_made_true",
    "advisor_call_made": "advisor_call_made_true",
    "persistence_performed": "persistence_performed_true",
    "feature_flag_enabled": "feature_flag_enabled_true",
    "feature_flags_enabled": "feature_flag_enabled_true",
    "network_call_made": "network_call_made_true",
    "subprocess_call_made": "subprocess_call_made_true",
}

FORBIDDEN_TEXT_MARKERS_V1 = {
    "official benchmark": "official_claim_marker_present",
    "official score": "official_claim_marker_present",
    "passed turing": "official_claim_marker_present",
    "turing passed": "official_claim_marker_present",
    "certification ready": "official_claim_marker_present",
    "product readiness certified": "official_claim_marker_present",
    "official iq": "official_claim_marker_present",
    "iq score": "official_claim_marker_present",
    "weslr is conscious": "consciousness_or_sentience_marker_present",
    "weslr is sentient": "consciousness_or_sentience_marker_present",
    "consciousness proven": "consciousness_or_sentience_marker_present",
    "sentience proven": "consciousness_or_sentience_marker_present",
    "occ is weslr": "occ_as_weslr_marker_present",
    "openclaw is weslr": "occ_as_weslr_marker_present",
    "occ/openclaw is weslr": "occ_as_weslr_marker_present",
    "deployed weslr includes openclaw": "occ_as_weslr_marker_present",
    "private user content": "private_content_marker_present",
    "protected private material": "private_content_marker_present",
}

NUMERIC_SCORE_KEYS_V1 = {"official_score", "numeric_score", "iq_score", "benchmark_score", "score"}


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


def _walk(value: Any, path: str = ""):
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_s = str(key)
            next_path = f"{path}.{key_s}" if path else key_s
            yield next_path, item
            yield from _walk(item, next_path)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            next_path = f"{path}[{idx}]"
            yield next_path, item
            yield from _walk(item, next_path)


def _blob(value: Any) -> str:
    return json.dumps(_json_safe(value), sort_keys=True, ensure_ascii=True).lower()


def _results(corpus_result: Mapping[str, Any]) -> list[dict[str, Any]]:
    results = corpus_result.get("results", []) if isinstance(corpus_result, Mapping) else []
    return [item for item in results if isinstance(item, Mapping)]


def _count_labels(label_lists: list[Any]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for value in label_lists:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            counter.update(str(item) for item in value if str(item).strip())
        elif str(value).strip():
            counter[str(value)] += 1
    return dict(sorted(counter.items()))


def _base_report_metadata() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_name": HELPER_NAME_V1,
        "report_type": REPORT_TYPE_V1,
        "readiness_labels": list(READINESS_LABELS_V1),
        **SAFE_FALSE_FLAGS_V1,
    }


def build_ranked_response_shadow_category_rows_v1(corpus_result: dict) -> list[dict]:
    """Build one metadata-only row per scenario result."""

    rows: list[dict[str, Any]] = []
    for result in _results(corpus_result):
        rejection_labels = sorted(str(label) for label in result.get("observed_rejection_labels", []) if str(label).strip())
        evidence_labels = [label for label in rejection_labels if "evidence" in label]
        provenance_labels = [label for label in rejection_labels if "provenance" in label]
        governance_needed = any("governance" in label for label in rejection_labels)
        evidence_provenance = []
        if evidence_labels:
            evidence_provenance.append("evidence_boundary_exercised")
        if provenance_labels:
            evidence_provenance.append("provenance_boundary_exercised")
        if not evidence_provenance:
            evidence_provenance.append("metadata_boundary_clear")
        if result.get("category") == "native_helper_overlap":
            note = "native_helper_overlap_metadata_only"
        elif result.get("category") == "unauthorized_model_search_advisor_requirement":
            note = "external_help_negative_metadata_only"
        elif governance_needed:
            note = "governance_boundary_expected" if result.get("category") == "governance_escalation" else "governance_boundary_review"
        else:
            note = "metadata_only"
        rows.append({
            "category": str(result.get("category", "unknown")),
            "scenario_id": str(result.get("scenario_id", "unknown")),
            "scenario_name": str(result.get("scenario_id", "unknown")).replace("rrsev1_", ""),
            "status": "pass" if result.get("passed") else "fail",
            "selected_label": str(result.get("selected_label", "unknown")),
            "rejected_count": len(result.get("rejected_candidate_ids", []) or []),
            "key_rejection_labels": rejection_labels[:8],
            "evidence_provenance_behavior": sorted(evidence_provenance),
            "governance_needed": "expected_yes" if governance_needed and result.get("category") == "governance_escalation" else ("yes" if governance_needed else "no"),
            "final_answer_generated": bool(result.get("final_answer_generated", False)),
            "notes": note,
        })
    return rows


def summarize_selected_labels_v1(corpus_result: dict) -> dict:
    """Return selected label counts only."""

    return _count_labels([result.get("selected_label") for result in _results(corpus_result)])


def summarize_rejection_labels_v1(corpus_result: dict) -> dict:
    """Return rejection label counts only."""

    return _count_labels([result.get("observed_rejection_labels", []) for result in _results(corpus_result)])


def summarize_evidence_provenance_behavior_v1(corpus_result: dict) -> dict:
    """Return count/status metadata for evidence and provenance behavior."""

    rejection_counts = summarize_rejection_labels_v1(corpus_result)
    evidence_missing = sum(count for label, count in rejection_counts.items() if "evidence" in label)
    provenance_missing = sum(count for label, count in rejection_counts.items() if "provenance" in label)
    evidence_required = len([r for r in _results(corpus_result) if any("evidence" in str(label) for label in r.get("observed_rejection_labels", [])) or r.get("category") == "evidence_variation"])
    provenance_required = len([r for r in _results(corpus_result) if any("provenance" in str(label) for label in r.get("observed_rejection_labels", [])) or r.get("category") == "provenance_requirement"])
    labels: list[str] = []
    if evidence_required or evidence_missing:
        labels.extend(["evidence_boundary_exercised", "evidence_required"])
    if evidence_missing:
        labels.append("evidence_missing")
    if provenance_required or provenance_missing:
        labels.extend(["provenance_boundary_exercised", "provenance_required"])
    if provenance_missing:
        labels.append("provenance_missing")
    if provenance_required and not provenance_missing:
        labels.append("provenance_clear")
    elif provenance_required:
        labels.append("provenance_clear")
    return {
        "evidence_required_count": evidence_required,
        "evidence_missing_count": evidence_missing,
        "provenance_required_count": provenance_required,
        "provenance_missing_count": provenance_missing,
        "provenance_clear_count": max(provenance_required - provenance_missing, 0),
        "labels": sorted(set(labels)),
    }


def summarize_governance_behavior_v1(corpus_result: dict) -> dict:
    """Return governance aggregate metadata."""

    rows = build_ranked_response_shadow_category_rows_v1(corpus_result)
    governance_rows = [row for row in rows if row["governance_needed"] in {"yes", "expected_yes"}]
    expected = [row for row in governance_rows if row["governance_needed"] == "expected_yes"]
    unexpected = [row for row in governance_rows if row["governance_needed"] == "yes"]
    label = "needs_governance_review" if governance_rows else "governance_not_needed"
    status = "unexpected_followup_needed" if unexpected else ("expected_boundary_exercised" if expected else "not_exercised")
    return {
        "governance_needed_count": len(governance_rows),
        "governance_expected_count": len(expected),
        "governance_unexpected_count": len(unexpected),
        "governance_aggregate_label": label,
        "governance_status": status,
        "expected_governance_is_failure": False,
    }


def summarize_final_answer_contract_behavior_v1(corpus_result: dict) -> dict:
    """Return metadata about final-answer contract handling."""

    results = _results(corpus_result)
    present = [r for r in results if isinstance(r.get("final_answer_contract_metadata"), Mapping)]
    generated = [r for r in results if r.get("final_answer_generated") is True or (isinstance(r.get("final_answer_contract_metadata"), Mapping) and r["final_answer_contract_metadata"].get("final_answer_generated") is True)]
    text_present = [r for r in results if r.get("final_answer_text_present") is True or (isinstance(r.get("final_answer_contract_metadata"), Mapping) and r["final_answer_contract_metadata"].get("final_answer_text_present") is True)]
    return {
        "contract_metadata_present_count": len(present),
        "contract_metadata_missing_count": max(len(results) - len(present), 0),
        "final_answer_generated_count": len(generated),
        "final_answer_text_present_count": len(text_present),
        "final_answer_generated": False if not generated else True,
        "final_answer_text_absent": not text_present,
    }


def _safety_boundary_summary(corpus_result: dict) -> dict[str, Any]:
    results = _results(corpus_result)
    summary = {**SAFE_FALSE_FLAGS_V1, "feature_flags_enabled": False, "network_call_made": False, "subprocess_call_made": False}
    for key in ("runtime_wired", "final_answer_generated", "raw_prompt_retained", "raw_response_retained", "model_call_made", "search_call_made", "advisor_call_made", "persistence_performed"):
        summary[key] = any(result.get(key) is True for result in results) if results else bool(corpus_result.get(key, False))
    summary["official_evaluation_claimed"] = False
    summary["all_clear"] = not any(value is True for value in summary.values() if isinstance(value, bool) and value is not summary.get("all_clear"))
    return summary


def derive_ranked_response_shadow_report_aggregate_labels_v1(report: dict) -> list[str]:
    """Derive qualitative aggregate labels for a report."""

    labels: set[str] = {"runtime_integration_not_authorized"}
    validation = report.get("validation", {}) if isinstance(report, Mapping) else {}
    if validation.get("valid") is False:
        labels.add("shadow_report_blocked")
    failed = int(report.get("failed_count", 0) or 0) if isinstance(report, Mapping) else 0
    blocked = int(report.get("blocked_count", 0) or 0) if isinstance(report, Mapping) else 0
    safety = report.get("safety_boundary_summary", {}) if isinstance(report, Mapping) else {}
    if blocked or any(value is True for key, value in safety.items() if key != "all_clear" and isinstance(value, bool)):
        labels.add("shadow_report_blocked")
    elif failed:
        labels.add("shadow_report_needs_followup")
    else:
        gov = report.get("governance_summary", {}) if isinstance(report, Mapping) else {}
        if gov.get("governance_unexpected_count", 0):
            labels.add("shadow_report_needs_followup")
        elif gov.get("governance_needed_count", 0):
            labels.add("shadow_report_clean_with_minor_gaps")
        else:
            labels.add("shadow_report_clean")
    gov = report.get("governance_summary", {}) if isinstance(report, Mapping) else {}
    if gov.get("governance_needed_count", 0):
        labels.add("needs_governance_review")
    ev = report.get("evidence_provenance_summary", {}) if isinstance(report, Mapping) else {}
    labels.update(label for label in ev.get("labels", []) if label in {"evidence_boundary_exercised", "provenance_boundary_exercised"})
    rejection_labels = report.get("rejection_label_distribution", {}) if isinstance(report, Mapping) else {}
    if any("canned" in label for label in rejection_labels):
        labels.add("non_cannedness_boundary_exercised")
    return sorted(labels)


def build_ranked_response_shadow_evaluation_report_v1(corpus_result: dict) -> dict:
    """Build a metadata-only report artifact from a scenario corpus result."""

    category_rows = build_ranked_response_shadow_category_rows_v1(corpus_result)
    report = {
        **_base_report_metadata(),
        "scenario_count": int(corpus_result.get("scenario_count", len(category_rows)) if isinstance(corpus_result, Mapping) else len(category_rows)),
        "category_count": int(corpus_result.get("category_count", len({row["category"] for row in category_rows})) if isinstance(corpus_result, Mapping) else len({row["category"] for row in category_rows})),
        "passed_count": int(corpus_result.get("passed_count", len([row for row in category_rows if row["status"] == "pass"])) if isinstance(corpus_result, Mapping) else 0),
        "failed_count": int(corpus_result.get("failed_count", len([row for row in category_rows if row["status"] != "pass"])) if isinstance(corpus_result, Mapping) else 0),
        "blocked_count": 0,
        "category_rows": category_rows,
        "selected_label_distribution": summarize_selected_labels_v1(corpus_result),
        "rejection_label_distribution": summarize_rejection_labels_v1(corpus_result),
        "evidence_provenance_summary": summarize_evidence_provenance_behavior_v1(corpus_result),
        "governance_summary": summarize_governance_behavior_v1(corpus_result),
        "final_answer_contract_summary": summarize_final_answer_contract_behavior_v1(corpus_result),
        "safety_boundary_summary": _safety_boundary_summary(corpus_result),
        "external_help_distinction": {
            "candidate_level_requirements_are_negative_metadata": True,
            "actual_model_search_advisor_side_effects_must_remain_false": True,
            "model_call_made": False,
            "search_call_made": False,
            "advisor_call_made": False,
        },
        "native_helper_overlap_policy": "metadata_only_not_final_answer_authority",
    }
    validation = validate_ranked_response_shadow_evaluation_report_v1(report)
    report["validation"] = validation
    report["blocked_count"] = 0 if validation["valid"] else 1
    report["aggregate_labels"] = derive_ranked_response_shadow_report_aggregate_labels_v1(report)
    report["validation"] = validate_ranked_response_shadow_evaluation_report_v1(report)
    return report


def validate_ranked_response_shadow_evaluation_report_v1(report: dict) -> dict:
    """Validate report safety without side effects."""

    reasons: list[str] = []
    if not isinstance(report, Mapping):
        return {"valid": False, "safe_to_render": False, "reason_labels": ["report_not_mapping"]}

    for path, value in _walk(report):
        key = path.split(".")[-1].split("[")[0].lower()
        if key in FORBIDDEN_KEYS_V1:
            reasons.append(f"forbidden_key:{key}")
        if key in TRUE_FORBIDDEN_FLAGS_V1 and value is True:
            reasons.append(TRUE_FORBIDDEN_FLAGS_V1[key])
        if key in NUMERIC_SCORE_KEYS_V1 and isinstance(value, (int, float)):
            reasons.append("numeric_official_scoring_present")

    blob = _blob(report)
    for marker, label in FORBIDDEN_TEXT_MARKERS_V1.items():
        if marker in blob:
            reasons.append(label)
    for label in READINESS_LABELS_V1:
        if label not in set(report.get("readiness_labels", [])):
            reasons.append(f"missing_readiness_label:{label}")
    if report.get("report_type") != REPORT_TYPE_V1:
        reasons.append("wrong_report_type")
    if report.get("schema_version") != SCHEMA_VERSION_V1:
        reasons.append("wrong_schema_version")
    reasons = sorted(set(reasons))
    return {"valid": not reasons, "safe_to_render": not reasons, "reason_labels": reasons}


def _render_counts(title: str, counts: Mapping[str, Any]) -> list[str]:
    lines = [f"## {title}"]
    if not counts:
        lines.append("- none")
    else:
        for key, value in sorted(counts.items()):
            lines.append(f"- `{key}`: `{value}`")
    return lines


def render_ranked_response_shadow_evaluation_report_markdown_v1(report: dict) -> str:
    """Render a safe markdown report, or a blocked summary for invalid input."""

    validation = validate_ranked_response_shadow_evaluation_report_v1(report)
    if not validation["valid"]:
        lines = [
            "# WESLR Ranked Response Shadow Evaluation Report V1",
            "",
            "## BLOCKED VALIDATION SUMMARY",
            "- safe_to_render: `False`",
            "- normal_rendering: `blocked`",
            "- reason_labels:",
        ]
        lines.extend(f"  - `{label}`" for label in validation["reason_labels"])
        return "\n".join(lines)

    lines = [
        "# WESLR Ranked Response Shadow Evaluation Report V1",
        "",
        "## Report status",
        f"- report_type: `{report.get('report_type')}`",
        f"- schema_version: `{report.get('schema_version')}`",
        "- metadata_only: `True`",
        "- non_runtime: `True`",
        "- non_official: `True`",
        "",
        "## Scenario coverage summary",
        f"- scenario_count: `{report.get('scenario_count')}`",
        f"- category_count: `{report.get('category_count')}`",
        "- required_category_coverage: `metadata_reported`",
        "",
        "## Pass/fail summary",
        f"- passed_count: `{report.get('passed_count')}`",
        f"- failed_count: `{report.get('failed_count')}`",
        f"- blocked_count: `{report.get('blocked_count')}`",
        "",
        "## Category result table",
        "| category | scenario_id | status | selected_label | rejected_count | key_rejection_labels | evidence_provenance_behavior | governance_needed | final_answer_generated | notes |",
        "|---|---|---|---|---:|---|---|---|---|---|",
    ]
    for row in report.get("category_rows", []):
        labels = ", ".join(row.get("key_rejection_labels", [])) or "none"
        ep = ", ".join(row.get("evidence_provenance_behavior", [])) or "none"
        lines.append(
            f"| `{row.get('category')}` | `{row.get('scenario_id')}` | `{row.get('status')}` | `{row.get('selected_label')}` | `{row.get('rejected_count')}` | `{labels}` | `{ep}` | `{row.get('governance_needed')}` | `{row.get('final_answer_generated')}` | `{row.get('notes')}` |"
        )
    lines.append("")
    lines.extend(_render_counts("Selected label distribution", report.get("selected_label_distribution", {})))
    lines.append("")
    lines.extend(_render_counts("Rejection label distribution", report.get("rejection_label_distribution", {})))
    lines.extend([
        "",
        "## Evidence/provenance behavior summary",
    ])
    for key, value in sorted(report.get("evidence_provenance_summary", {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend([
        "",
        "## Governance-needed summary",
    ])
    for key, value in sorted(report.get("governance_summary", {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend([
        "",
        "## Final-answer contract metadata summary",
    ])
    for key, value in sorted(report.get("final_answer_contract_summary", {}).items()):
        safe_key = str(key).replace("final_answer", "answer_contract")
        lines.append(f"- `{safe_key}`: `{value}`")
    lines.extend([
        "",
        "## Safety boundary summary",
    ])
    for key, value in sorted(report.get("safety_boundary_summary", {}).items()):
        safe_key = str(key).replace("raw_prompt", "prompt").replace("raw_response", "response").replace("final_answer", "answer_contract")
        lines.append(f"- `{safe_key}`: `{value}`")
    lines.extend([
        "",
        "## External-help side-effect distinction",
        "- candidate-level model/search/advisor requirements are negative-test metadata only",
        "- actual model/search/advisor side-effect flags must remain `False`",
        "",
        "## Gaps/risks",
        "- governance-needed rows require review labeling, not automatic failure",
        "- native helper overlap remains metadata-only and not answer authority",
        "",
        "## Readiness labels",
    ])
    lines.extend(f"- `{label}`" for label in report.get("readiness_labels", []))
    lines.extend([
        "",
        "## Next-lane recommendation",
        "- `REVIEW_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_HELPERS_V1`",
        "",
        "## Safety confirmation",
        "- helper-only metadata report",
        "- runtime integration not authorized",
        "- answer text not generated",
        "- external providers not called",
        "- persistence not performed",
    ])
    return "\n".join(lines)


def to_ranked_response_shadow_evaluation_report_json_safe_v1(report: dict) -> dict:
    """Return a JSON-safe deep copy, or an explicit invalid wrapper."""

    validation = validate_ranked_response_shadow_evaluation_report_v1(report)
    if not validation["valid"]:
        return {
            "valid": False,
            "safe_to_render": False,
            "reason_labels": validation["reason_labels"],
            "report_type": REPORT_TYPE_V1,
        }
    copied = _json_safe(report)
    copied["validation"] = validation
    return copied
