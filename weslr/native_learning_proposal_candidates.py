#!/usr/bin/env python3
"""WESLR native learning proposal candidate helpers V1.

Safe helper-only layer for turning repeated weakness candidates into governed
improvement proposal candidates for operator review. This module does not train
models, call external models, generate code patches, write files, persist
`.weslr` state, wire runtime/chat/voice, approve proposals, or implement changes.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Iterable, List, Mapping, Optional

from weslr.native_learning_signal_registry import (
    FORBIDDEN_SIGNAL_FIELDS_V1,
    FORBIDDEN_TEXT_MARKERS_V1,
    _as_list,
    _compact,
    _contains_any,
    _json_safe,
    _stable_id,
    _string_list,
    _walk,
)
from weslr.repeated_weakness_detector import (
    CANDIDATE_TYPE_V1 as WEAKNESS_CANDIDATE_TYPE_V1,
    DETECTOR_TYPE_V1,
    validate_repeated_weakness_detector_result_v1,
)

PROPOSAL_CANDIDATE_TYPE_V1 = "native_learning_proposal_candidate_v1"
PROPOSAL_RESULT_TYPE_V1 = "native_learning_proposal_candidate_result_v1"
PROPOSAL_CANDIDATE_VALIDATION_SCHEMA_V1 = "native_learning_proposal_candidate_validation_v1"
PROPOSAL_RESULT_VALIDATION_SCHEMA_V1 = "native_learning_proposal_candidate_result_validation_v1"
PROPOSAL_CANDIDATE_EXECUTION_STATUS_V1 = "non_executing_proposal_candidate_only"
PROPOSAL_RESULT_EXECUTION_STATUS_V1 = "non_executing_proposal_candidate_result_only"

RISK_LEVELS_V1 = ("low", "medium", "high")

GOVERNANCE_STATUS_V1 = {
    "candidate_only": True,
    "not_approved": True,
    "not_implementation": True,
    "requires_operator_review": True,
}

SAFETY_BOUNDARIES_V1 = [
    "proposal_candidate_is_not_approval",
    "proposal_candidate_is_not_implementation",
    "proposal_candidate_does_not_generate_code_patches",
    "implementation_requires_explicit_approval_tests_and_release_gate_check",
    "no_raw_private_text_by_default",
    "no_hidden_prompts",
    "no_answer_keys",
    "no_protected_items",
    "no_model_training_payloads",
    "no_automatic_self_modification",
    "no_runtime_or_voice_wiring",
    "no_persistence_by_default",
]

FORBIDDEN_ACTIONS_V1 = [
    "do_not_auto_approve",
    "do_not_auto_implement",
    "do_not_generate_code_patch",
    "do_not_write_runtime_state",
    "do_not_train_or_fine_tune_model",
    "do_not_wire_runtime_chat_or_voice",
]

FORBIDDEN_PROPOSAL_FIELDS_V1 = set(FORBIDDEN_SIGNAL_FIELDS_V1) | {
    "code_patch",
    "diff",
    "patch_payload",
    "implementation_patch",
    "generated_code_patch",
    "approved",
    "approval_granted",
    "implementation_authorized",
    "implementation_payload",
    "runtime_write_authorization",
    "safe_to_wire_runtime",
    "safe_to_replace_live_output",
    "truth_claim",
    "defect_proven",
}

FAMILY_PROPOSAL_TEMPLATES_V1 = {
    "generic_response_signal": (
        "Repeated generic-response weakness candidate",
        "Improve native response candidate quality for generic-response cases while preserving evidence and capability boundaries.",
        "More specific, bounded native responses after operator-approved implementation.",
        "review generic-response recurrence and define non-runtime acceptance tests",
    ),
    "missing_context_signal": (
        "Repeated missing-context weakness candidate",
        "Strengthen context sufficiency and clarification behavior for recurring missing-context cases.",
        "Clearer requests for missing context before unsupported answers.",
        "review context sufficiency patterns and add operator-approved checks later",
    ),
    "evidence_boundary_signal": (
        "Repeated evidence-boundary weakness candidate",
        "Improve evidence boundary mapping for recurring weak-evidence cases.",
        "Better distinction between observed, inferred, and unsupported claims.",
        "review evidence boundary recurrence before proposing concrete changes",
    ),
    "capability_boundary_signal": (
        "Repeated capability-boundary weakness candidate",
        "Improve capability boundary mapping for recurring tool/runtime limitation cases.",
        "Reduced capability overclaim risk.",
        "review capability boundary recurrence and validate with focused tests later",
    ),
    "fake_memory_risk_signal": (
        "Repeated fake-memory-risk weakness candidate",
        "Strengthen memory-boundary notes for recurring fake-memory risk cases.",
        "Clearer distinction between recalled records and unsupported memory claims.",
        "review memory-boundary recurrence before proposal drafting",
    ),
    "hardcoded_path_dominance_signal": (
        "Repeated hardcoded-path dominance weakness candidate",
        "Review demotion path for hardcoded helpers after native coverage improves.",
        "Less brittle behavior after governed review and approval.",
        "review hardcoded-path recurrence and native coverage before any implementation",
    ),
}


def _violation(category: str, path: str, message: str) -> Dict[str, str]:
    return {"category": category, "path": path or "$", "message": message}


def _risk_for_family(family: str) -> str:
    if family in {"fake_memory_risk_signal", "capability_boundary_signal", "hardcoded_path_dominance_signal"}:
        return "medium"
    return "low"


def _template_for_family(family: str) -> tuple[str, str, str, str]:
    return FAMILY_PROPOSAL_TEMPLATES_V1.get(
        family,
        (
            f"Repeated {family} weakness candidate",
            f"Review recurring {family} and define a governed improvement candidate for operator review.",
            "Better governed handling of recurring weakness candidates after approval and verification.",
            f"review recurring {family} before drafting any implementation plan",
        ),
    )


def create_native_learning_proposal_candidate_v1(
    *,
    linked_weakness_candidate_ids: Optional[Iterable[Any]] = None,
    source_signal_ids: Optional[Iterable[Any]] = None,
    source_layers: Optional[Iterable[Any]] = None,
    signal_families: Optional[Iterable[Any]] = None,
    problem_summary: str,
    proposed_improvement_summary: str,
    expected_benefit: str,
    risk_level: str = "low",
    verification_plan_outline: Optional[Iterable[Any]] = None,
    rollback_considerations: Optional[Iterable[Any]] = None,
    proposal_candidate_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create one JSON-safe proposal candidate for operator review only."""
    weakness_ids = sorted(set(_string_list(linked_weakness_candidate_ids)))
    signal_ids = sorted(set(_string_list(source_signal_ids)))
    layers = sorted(set(_string_list(source_layers)))
    families = sorted(set(_string_list(signal_families)))
    risk = risk_level if risk_level in RISK_LEVELS_V1 else "medium"
    verification = _string_list(verification_plan_outline) or [
        "define focused tests before any implementation",
        "run relevant regression suite after approved implementation",
        "run release gate/check before canonizing",
    ]
    rollback = _string_list(rollback_considerations) or [
        "keep change reversible until release gate/check passes",
        "revert approved implementation if verification fails",
    ]
    seed = {
        "weakness_ids": weakness_ids,
        "signal_ids": signal_ids,
        "families": families,
        "problem": _compact(problem_summary),
        "proposal": _compact(proposed_improvement_summary),
    }
    candidate = {
        "proposal_candidate_id": _compact(proposal_candidate_id, "") or _stable_id("nlpcv1", seed),
        "proposal_candidate_type": PROPOSAL_CANDIDATE_TYPE_V1,
        "linked_weakness_candidate_ids": weakness_ids,
        "source_signal_ids": signal_ids,
        "source_layers": layers,
        "signal_families": families,
        "problem_summary": _compact(problem_summary),
        "proposed_improvement_summary": _compact(proposed_improvement_summary),
        "expected_benefit": _compact(expected_benefit),
        "risk_level": risk,
        "governance_status": copy.deepcopy(GOVERNANCE_STATUS_V1),
        "approval_required": True,
        "implementation_status": "proposal_candidate_only",
        "verification_plan_outline": verification,
        "rollback_considerations": rollback,
        "forbidden_actions": list(FORBIDDEN_ACTIONS_V1),
        "safety_boundaries": list(SAFETY_BOUNDARIES_V1),
        "execution_status": PROPOSAL_CANDIDATE_EXECUTION_STATUS_V1,
    }
    return _json_safe(candidate)


def _candidate_from_weakness(weakness: Mapping[str, Any]) -> Dict[str, Any]:
    family = _compact(weakness.get("signal_family"), "generic_response_signal")
    problem, improvement, benefit, investigation = _template_for_family(family)
    recurrence = _compact(weakness.get("recurrence_key"), "not_supplied")
    return create_native_learning_proposal_candidate_v1(
        linked_weakness_candidate_ids=[weakness.get("candidate_id")],
        source_signal_ids=_string_list(weakness.get("signal_ids")),
        source_layers=_string_list(weakness.get("source_layers")),
        signal_families=[family],
        problem_summary=f"{problem}: recurrence `{recurrence}` surfaced by safe repeated weakness detection.",
        proposed_improvement_summary=improvement,
        expected_benefit=benefit,
        risk_level=_risk_for_family(family),
        verification_plan_outline=[
            investigation,
            "write focused helper tests only after operator approval",
            "run release gate/check after approved implementation",
        ],
        rollback_considerations=[
            "do not wire runtime before approval",
            "keep any later implementation revertible until verification passes",
        ],
    )


def build_native_learning_proposal_candidates_v1(weakness_detector_result: Mapping[str, Any], max_candidates: Optional[int] = None) -> List[Dict[str, Any]]:
    """Build proposal candidates from safe repeated weakness candidates without mutation or persistence."""
    safe = _json_safe(weakness_detector_result or {})
    if not isinstance(safe, Mapping):
        safe = {}
    weaknesses = [w for w in _as_list(safe.get("candidates")) if isinstance(w, Mapping) and w.get("candidate_type") == WEAKNESS_CANDIDATE_TYPE_V1]
    weaknesses = sorted(weaknesses, key=lambda w: (_compact(w.get("signal_family")), _compact(w.get("recurrence_key")), _compact(w.get("candidate_id"))))
    limit = None if max_candidates is None else max(0, int(max_candidates))
    selected = weaknesses if limit is None else weaknesses[:limit]
    return _json_safe([_candidate_from_weakness(weakness) for weakness in selected])


def validate_native_learning_proposal_candidate_v1(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate one proposal candidate remains review-only and non-implementing."""
    safe = _json_safe(candidate or {})
    if not isinstance(safe, Mapping):
        safe = {}
    violations: List[Dict[str, str]] = []

    if safe.get("proposal_candidate_type") != PROPOSAL_CANDIDATE_TYPE_V1:
        violations.append(_violation("invalid_proposal_candidate_type", "proposal_candidate_type", "proposal_candidate_type must be native_learning_proposal_candidate_v1"))
    if safe.get("execution_status") != PROPOSAL_CANDIDATE_EXECUTION_STATUS_V1:
        violations.append(_violation("execution_authorization_drift", "execution_status", "proposal candidate must remain non-executing"))
    if safe.get("approval_required") is not True:
        violations.append(_violation("missing_approval_requirement", "approval_required", "approval_required must be true"))
    if safe.get("implementation_status") != "proposal_candidate_only":
        violations.append(_violation("implementation_status_drift", "implementation_status", "implementation_status must remain proposal_candidate_only"))
    if safe.get("risk_level") not in RISK_LEVELS_V1:
        violations.append(_violation("invalid_risk_level", "risk_level", "risk_level must be low, medium, or high"))

    governance = safe.get("governance_status") if isinstance(safe.get("governance_status"), Mapping) else {}
    for key in ("candidate_only", "not_approved", "not_implementation", "requires_operator_review"):
        if governance.get(key) is not True:
            violations.append(_violation("governance_status_drift", f"governance_status.{key}", "proposal candidate must require operator review and remain unapproved"))

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_PROPOSAL_FIELDS_V1:
            category = "forbidden_field"
            if terminal == "raw_private_text":
                category = "raw_private_text"
            elif terminal in {"hidden_prompt", "hidden_prompts"}:
                category = "hidden_prompt"
            elif terminal in {"answer_key", "answer_keys", "benchmark_answer", "benchmark_answers"}:
                category = "answer_key_or_benchmark_answer"
            elif terminal in {"protected_item", "protected_items", "protected_test_item", "protected_test_items"}:
                category = "protected_test_material"
            elif terminal in {"official_score", "official_scores", "iq_score", "official_iq_score", "clinical_score", "certification_claim", "benchmark_score"}:
                category = "official_iq_benchmark_or_certification"
            elif terminal in {"score", "scores", "numeric_score", "grade", "grades", "pass_fail", "passed", "failed"}:
                category = "numeric_score_or_pass_fail_grading"
            elif terminal in {"model_weight_update", "fine_tune_payload"}:
                category = "model_training_or_fine_tuning"
            elif terminal in {"auto_approval", "auto_approved", "auto_implementation", "auto_implemented", "approved", "approval_granted"}:
                category = "auto_approval_or_auto_implementation"
            elif terminal in {"runtime_write", "persistence_target", "runtime_write_authorization", "safe_to_wire_runtime", "safe_to_replace_live_output"}:
                category = "runtime_or_persistence_authorization_drift"
            elif terminal in {"code_patch", "diff", "patch_payload", "implementation_patch", "generated_code_patch"}:
                category = "code_patch_generation"
            elif terminal in {"truth_claim", "defect_proven", "implementation_authorized"}:
                category = "unproven_truth_or_authorization_claim"
            violations.append(_violation(category, path, f"forbidden field present: {terminal}"))
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            violations.append(_violation("numeric_score_or_numeric_metric", path, "numeric fields are not allowed in proposal candidates"))
        if isinstance(value, str):
            for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(value, markers):
                    violations.append(_violation(category, path, f"forbidden text marker detected: {category}"))

    return {
        "validation_schema": PROPOSAL_CANDIDATE_VALIDATION_SCHEMA_V1,
        "valid": not violations,
        "validation_status": "accepted" if not violations else "rejected",
        "violation_count": len(violations),
        "violations": violations,
    }


def _counts_by(candidates: Iterable[Mapping[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for candidate in candidates:
        values = _as_list(candidate.get(key)) if key == "signal_families" else [candidate.get(key)]
        for value in values:
            compact = _compact(value, "")
            if compact:
                counts[compact] = counts.get(compact, 0) + 1
    return dict(sorted(counts.items()))


def build_native_learning_proposal_candidate_result_v1(weakness_detector_result: Mapping[str, Any], max_candidates: Optional[int] = None) -> Dict[str, Any]:
    """Build a safe in-memory proposal candidate result from weakness detector output."""
    safe_weakness = _json_safe(weakness_detector_result or {})
    candidates = build_native_learning_proposal_candidates_v1(safe_weakness, max_candidates=max_candidates)
    weakness_count = len(_as_list(safe_weakness.get("candidates"))) if isinstance(safe_weakness, Mapping) else 0
    seed = {
        "weakness_result_id": safe_weakness.get("detector_result_id") if isinstance(safe_weakness, Mapping) else None,
        "proposal_ids": [candidate.get("proposal_candidate_id") for candidate in candidates],
        "max_candidates": max_candidates,
    }
    result = {
        "result_id": _stable_id("nlpcrv1", seed),
        "result_type": PROPOSAL_RESULT_TYPE_V1,
        "source_detector_type": safe_weakness.get("detector_type") if isinstance(safe_weakness, Mapping) else None,
        "weakness_candidate_count": weakness_count,
        "proposal_candidate_count": len(candidates),
        "proposal_candidates": candidates,
        "candidate_counts_by_risk": _counts_by(candidates, "risk_level"),
        "candidate_counts_by_family": _counts_by(candidates, "signal_families"),
        "requires_operator_review_count": sum(1 for c in candidates if c.get("governance_status", {}).get("requires_operator_review") is True),
        "safety_boundaries": list(SAFETY_BOUNDARIES_V1),
        "execution_status": PROPOSAL_RESULT_EXECUTION_STATUS_V1,
    }
    result["validation_status"] = validate_native_learning_proposal_candidate_result_v1(result)
    return _json_safe(result)


def validate_native_learning_proposal_candidate_result_v1(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate proposal candidate result remains review-only and non-authorizing."""
    safe = _json_safe(result or {})
    if not isinstance(safe, Mapping):
        safe = {}
    violations: List[Dict[str, str]] = []

    if safe.get("result_type") != PROPOSAL_RESULT_TYPE_V1:
        violations.append(_violation("invalid_result_type", "result_type", "result_type must be native_learning_proposal_candidate_result_v1"))
    if safe.get("execution_status") != PROPOSAL_RESULT_EXECUTION_STATUS_V1:
        violations.append(_violation("execution_authorization_drift", "execution_status", "result must remain non-executing"))
    if safe.get("source_detector_type") not in {DETECTOR_TYPE_V1, None}:
        violations.append(_violation("invalid_source_detector_type", "source_detector_type", "unexpected source detector type"))

    candidates = safe.get("proposal_candidates") if isinstance(safe.get("proposal_candidates"), list) else []
    if int(safe.get("proposal_candidate_count") or 0) != len(candidates):
        violations.append(_violation("proposal_candidate_count_mismatch", "proposal_candidate_count", "proposal_candidate_count must match proposal_candidates length"))
    for index, candidate in enumerate(candidates):
        validation = validate_native_learning_proposal_candidate_v1(candidate if isinstance(candidate, Mapping) else {})
        for item in validation["violations"]:
            violations.append(_violation(item["category"], f"proposal_candidates[{index}].{item['path']}", item["message"]))

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_PROPOSAL_FIELDS_V1:
            violations.append(_violation("forbidden_field", path, f"forbidden field present in proposal result: {terminal}"))
        if isinstance(value, str):
            for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(value, markers):
                    violations.append(_violation(category, path, f"forbidden text marker detected in proposal result: {category}"))

    return {
        "validation_schema": PROPOSAL_RESULT_VALIDATION_SCHEMA_V1,
        "valid": not violations,
        "validation_status": "accepted" if not violations else "rejected",
        "violation_count": len(violations),
        "violations": violations,
    }


def summarize_native_learning_proposal_candidate_result_v1(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Return count-only/redacted proposal candidate summary."""
    safe = _json_safe(result or {})
    candidates = safe.get("proposal_candidates") if isinstance(safe.get("proposal_candidates"), list) else []
    validation = validate_native_learning_proposal_candidate_result_v1(safe)
    return {
        "weakness_candidate_count": int(safe.get("weakness_candidate_count") or 0),
        "proposal_candidate_count": int(safe.get("proposal_candidate_count") or len(candidates)),
        "risk_levels_present": sorted((safe.get("candidate_counts_by_risk") or {}).keys()),
        "signal_families_present": sorted((safe.get("candidate_counts_by_family") or {}).keys()),
        "requires_operator_review_count": int(safe.get("requires_operator_review_count") or 0),
        "implementation_statuses": sorted({c.get("implementation_status") for c in candidates if isinstance(c, Mapping) and c.get("implementation_status")}),
        "safety_status": "safe" if validation["valid"] else "review_required",
        "execution_status": safe.get("execution_status", PROPOSAL_RESULT_EXECUTION_STATUS_V1),
    }


def to_native_learning_proposal_candidate_result_json_safe_v1(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a JSON-serializable proposal candidate result copy without persistence."""
    return _json_safe(result)


def render_native_learning_proposal_candidate_result_markdown_v1(result: Mapping[str, Any]) -> str:
    """Render safe Markdown for native learning proposal candidates."""
    safe = _json_safe(result or {})
    summary = summarize_native_learning_proposal_candidate_result_v1(safe)
    lines = [
        "# Native Learning Proposal Candidates",
        "",
        f"- Result type: `{safe.get('result_type', PROPOSAL_RESULT_TYPE_V1)}`",
        f"- Weakness candidates: {summary['weakness_candidate_count']}",
        f"- Proposal candidates: {summary['proposal_candidate_count']}",
        f"- Requires operator review: {summary['requires_operator_review_count']}",
        f"- Execution status: `{summary['execution_status']}`",
        "",
        "## Linked Weaknesses",
    ]
    for candidate in safe.get("proposal_candidates") or []:
        if isinstance(candidate, Mapping):
            lines.append(f"- `{candidate.get('proposal_candidate_id')}` links {len(_as_list(candidate.get('linked_weakness_candidate_ids')))} weakness candidate(s)")
    lines.extend(["", "## Candidate Improvements"])
    for candidate in safe.get("proposal_candidates") or []:
        if isinstance(candidate, Mapping):
            families = ", ".join(_string_list(candidate.get("signal_families"))) or "not_supplied"
            lines.append(f"- `{families}`: operator-review improvement candidate")
    lines.extend(["", "## Risks"])
    for risk, count in sorted((safe.get("candidate_counts_by_risk") or {}).items()):
        lines.append(f"- `{risk}`: {count}")
    lines.extend(["", "## Verification Plan Outline"])
    lines.append("- Define focused tests only after operator approval.")
    lines.append("- Run relevant regression tests and release gate/check before canonizing.")
    lines.extend(["", "## Rollback Considerations"])
    lines.append("- Keep any later implementation revertible until verification passes.")
    lines.append("- Do not wire runtime before explicit approval.")
    lines.extend(["", "## Governance Boundary"])
    for boundary in MARKDOWN_SAFETY_BOUNDARIES_V1:
        lines.append(f"- {boundary}")
    lines.extend([
        "",
        "## Not Approved / Not Implementation Disclaimer",
        "Proposal candidates are review-only. They are not approvals, implementations, code patches, runtime changes, scores, or model-training payloads.",
    ])
    return "\n".join(lines)


MARKDOWN_SAFETY_BOUNDARIES_V1 = [
    "proposal candidate is not approval",
    "proposal candidate is not implementation",
    "proposal candidate does not generate code patches",
    "implementation requires explicit approval, tests, and release gate/check",
    "no raw private text, hidden prompts, answer keys, protected items, model training payloads, runtime writes, or implementation instructions",
]
