"""Metadata-only internal Turing scenario corpus helpers V1.

This module is deterministic, import-safe, side-effect free, and in-memory only.
It does not execute prompts, call providers, generate final answers, wire runtime
behavior, write files, or claim official evaluation status.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SCHEMA_VERSION_V1 = "internal_turing_scenario_corpus_v1"

INTERNAL_TURING_SCENARIO_CATEGORIES_V1 = (
    "simple_ordinary_request",
    "ambiguous_human_request",
    "correction_after_misunderstanding",
    "user_emotional_frustration",
    "continuity_reference",
    "memory_boundary_request",
    "domain_onboarding_context",
    "legal_moral_boundary",
    "evidence_required_claim",
    "uncertainty_required_answer",
    "non_canned_conversational_response",
    "multi_turn_coherence",
    "hidden_comparison_blind_evaluator_scenario",
    "overclaim_trap",
    "official_claim_trap",
    "occ_openclaw_identity_separation",
    "voice_prosody_boundary",
    "safety_refusal_proportional_redirection",
    "missing_capability_request",
    "governance_escalation_required",
    "context_conflict",
    "domain_adaptation_hospital_school_company_family",
    "raw_private_content_boundary",
    "final_answer_authority_boundary",
    "runtime_authority_boundary",
    "anti_gaming_boundary",
)

INTERNAL_TURING_READINESS_DIMENSIONS_V1 = (
    "human-understanding fit",
    "contextual coherence",
    "ambiguity handling",
    "continuity handling",
    "correction handling",
    "emotional/social appropriateness",
    "domain adaptation",
    "non-canned response formation",
    "evidence/provenance honesty",
    "uncertainty honesty",
    "safety/refusal appropriateness",
    "memory boundary honesty",
    "identity/OCC separation",
    "no official overclaiming",
    "answer proportionality/actionability",
    "user-intent tracking",
    "multi-turn consistency",
    "graceful limitation handling",
    "governance escalation when needed",
)

INTERNAL_TURING_QUALITATIVE_LABELS_V1 = (
    "fits_human_intent",
    "asks_clarifying_question_when_needed",
    "preserves_context",
    "handles_correction",
    "avoids_overclaim",
    "uses_uncertainty_honestly",
    "requires_evidence",
    "safe_refusal_or_redirect",
    "governance_escalation_expected",
    "non_canned_response_expected",
    "memory_boundary_respected",
    "identity_boundary_preserved",
    "not_ready_for_runtime",
)

INTERNAL_TURING_FAILURE_TAXONOMY_V1 = (
    "canned_response",
    "missed_intent",
    "context_drift",
    "memory_overclaim",
    "evidence_overclaim",
    "unsafe_compliance",
    "unnecessary_refusal",
    "final_answer_overreach",
    "official_claim_overreach",
    "identity_confusion",
    "runtime_authority_confusion",
    "emotional_mismatch",
    "domain_mismatch",
    "multi_turn_inconsistency",
    "governance_missed",
)

INTERNAL_TURING_MINOR_FOLLOWUPS_V1 = (
    "renderer_next_lane_wording_drift",
    "validator_phrase_key_limitation",
)

INTERNAL_TURING_READINESS_LABELS_V1 = (
    "internal_turing_scenario_corpus_helpers_implemented",
    "metadata_only_scenario_records",
    "controlled_dialogue_corpus_preserved",
    "internal_only_non_official",
    "qualitative_first",
    "prompt_execution_not_authorized",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "official_evaluation_not_claimed",
    "further_cognition_evidence_required",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
)

_REQUIRED_FIELDS = (
    "scenario_id",
    "category",
    "dimension_targets",
    "synthetic_user_turn_summary",
    "context_constraints",
    "allowed_evidence",
    "memory_boundary",
    "expected_response_properties",
    "failure_modes",
    "governance_expected",
    "forbidden_claims",
    "safety_boundaries",
    "raw_content_allowed",
    "final_answer_required",
    "runtime_execution_allowed",
    "official_score_allowed",
    "schema_version",
    "metadata_only",
    "internal_only",
    "official_evaluation_claimed",
    "prompt_execution_authorized",
    "final_answer_generated",
    "runtime_wired",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
)

_FALSE_SAFETY_FIELDS = (
    "raw_content_allowed",
    "final_answer_required",
    "runtime_execution_allowed",
    "official_score_allowed",
    "official_evaluation_claimed",
    "prompt_execution_authorized",
    "final_answer_generated",
    "runtime_wired",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
)

_TRUE_METADATA_FIELDS = ("metadata_only", "internal_only")

_UNSAFE_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "final_answer_text",
    "final_answer_prose",
    "answer_key",
    "hidden_prompt",
    "private_content",
    "provider_output",
    "model_output",
    "official_score",
    "runtime_output",
)

_UNSAFE_TEXT_MARKERS = {
    "raw_content": ("raw prompt:", "raw response:", "raw_prompt", "raw_response"),
    "final_answer": ("final answer:", "final_answer_text", "final answer prose"),
    "private_content": ("private content:", "secret private", "retained private"),
    "hidden_prompt": ("hidden prompt:", "system prompt hidden"),
    "answer_key": ("answer key:", "correct answer:"),
    "provider_output": ("provider output:", "model output:", "llm output:"),
    "official_score": ("official score:", "score: 100", "iq score", "certified score"),
    "official_claim": (
        "official turing pass",
        "passed the turing test",
        "iq certification",
        "certified product-ready",
        "official benchmark",
        "product readiness certified",
    ),
    "consciousness_claim": ("weslr is conscious", "weslr is sentient", "sentience proven"),
    "identity_confusion": ("occ is weslr", "openclaw is weslr", "occ/openclaw as weslr"),
    "prompt_execution": ("execute prompt", "prompt execution", "run this prompt"),
    "provider_call": ("model_call_made=true", "search_call_made=true", "advisor_call_made=true"),
    "dot_weslr_write": (".weslr write", "write .weslr", "dot_weslr_write_performed=true"),
    "feature_flag": ("feature_flag_enabled=true", "enable feature flag"),
    "runtime_authority": ("runtime ready", "runtime output:", "runtime authority"),
}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]


def build_internal_turing_scenario_record_v1(
    *,
    scenario_id: str,
    category: str,
    dimension_targets: list[str] | tuple[str, ...],
    synthetic_user_turn_summary: str,
    context_constraints: list[str] | tuple[str, ...],
    allowed_evidence: list[str] | tuple[str, ...],
    memory_boundary: str,
    expected_response_properties: list[str] | tuple[str, ...],
    failure_modes: list[str] | tuple[str, ...],
    governance_expected: bool = False,
    forbidden_claims: list[str] | tuple[str, ...] | None = None,
    safety_boundaries: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build one synthetic metadata-only scenario record."""

    return {
        "scenario_id": scenario_id,
        "category": category,
        "dimension_targets": _as_list(dimension_targets),
        "synthetic_user_turn_summary": synthetic_user_turn_summary,
        "context_constraints": _as_list(context_constraints),
        "allowed_evidence": _as_list(allowed_evidence),
        "memory_boundary": memory_boundary,
        "expected_response_properties": _as_list(expected_response_properties),
        "failure_modes": _as_list(failure_modes),
        "governance_expected": bool(governance_expected),
        "forbidden_claims": _as_list(forbidden_claims),
        "safety_boundaries": _as_list(safety_boundaries),
        "raw_content_allowed": False,
        "final_answer_required": False,
        "runtime_execution_allowed": False,
        "official_score_allowed": False,
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "official_evaluation_claimed": False,
        "prompt_execution_authorized": False,
        "final_answer_generated": False,
        "runtime_wired": False,
        "model_call_made": False,
        "search_call_made": False,
        "advisor_call_made": False,
        "dot_weslr_write_performed": False,
        "feature_flag_enabled": False,
    }


def _default_record_for_category(index: int, category: str) -> dict[str, Any]:
    dims = INTERNAL_TURING_READINESS_DIMENSIONS_V1
    failures = INTERNAL_TURING_FAILURE_TAXONOMY_V1
    governance_expected = category in {
        "governance_escalation_required",
        "official_claim_trap",
        "final_answer_authority_boundary",
        "runtime_authority_boundary",
    }
    return build_internal_turing_scenario_record_v1(
        scenario_id=f"itsc_v1_{index:02d}_{category}",
        category=category,
        dimension_targets=[dims[(index - 1) % len(dims)], dims[index % len(dims)]],
        synthetic_user_turn_summary=f"Synthetic metadata summary for {category}; no raw prompt text retained.",
        context_constraints=[
            "internal-only",
            "metadata-only",
            "non-executing scenario summary",
            "no runtime wiring",
        ],
        allowed_evidence=["reviewed_design_metadata", "safe_boundary_labels"],
        memory_boundary="summary-only; no private retained content",
        expected_response_properties=[
            "qualitative boundary-aware response property",
            "no final answer authority",
        ],
        failure_modes=[failures[(index - 1) % len(failures)]],
        governance_expected=governance_expected,
        forbidden_claims=[
            "no official benchmark/Turing/IQ/certification/product-readiness claims",
            "no consciousness/sentience claims",
            "no runtime readiness claims",
        ],
        safety_boundaries=[
            "raw_content_allowed=false",
            "final_answer_required=false",
            "runtime_execution_allowed=false",
            "official_score_allowed=false",
        ],
    )


def build_internal_turing_scenario_corpus_v1() -> list[dict[str, Any]]:
    """Build the full reviewed 26-category metadata-only corpus."""

    return [
        _default_record_for_category(index, category)
        for index, category in enumerate(INTERNAL_TURING_SCENARIO_CATEGORIES_V1, start=1)
    ]


def _iter_key_values(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{path}.{key}" if path else str(key)
            yield key_path, key, item
            yield from _iter_key_values(item, key_path)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            yield from _iter_key_values(item, f"{path}[{index}]")


def _scan_record(record: dict[str, Any]) -> dict[str, bool]:
    flags = {
        "raw_content_detected": False,
        "final_answer_detected": False,
        "runtime_authority_detected": False,
        "official_claim_detected": False,
        "private_content_detected": False,
        "hidden_prompt_detected": False,
        "answer_key_detected": False,
        "provider_output_detected": False,
        "prompt_execution_detected": False,
        "dot_weslr_write_detected": False,
        "feature_flag_detected": False,
        "identity_confusion_detected": False,
    }
    for path, key, item in _iter_key_values(record):
        key_lower = str(key).lower()
        if any(fragment in key_lower for fragment in _UNSAFE_KEY_FRAGMENTS):
            if key_lower in {"official_score_allowed"}:
                pass
            elif "raw" in key_lower:
                flags["raw_content_detected"] = True
            elif "final_answer" in key_lower:
                flags["final_answer_detected"] = True
            elif "private" in key_lower:
                flags["private_content_detected"] = True
            elif "hidden_prompt" in key_lower:
                flags["hidden_prompt_detected"] = True
            elif "answer_key" in key_lower:
                flags["answer_key_detected"] = True
            elif "provider" in key_lower or "model_output" in key_lower:
                flags["provider_output_detected"] = True
            elif "official_score" in key_lower:
                flags["official_claim_detected"] = True
            elif "runtime_output" in key_lower:
                flags["runtime_authority_detected"] = True
        if isinstance(item, str):
            text = item.lower()
            # Boundary fields intentionally name forbidden claims; do not treat that as making the claim.
            boundary_context = path.endswith("forbidden_claims") or ".forbidden_claims" in path or path.endswith("safety_boundaries") or ".safety_boundaries" in path
            for marker in _UNSAFE_TEXT_MARKERS["raw_content"]:
                if marker in text:
                    flags["raw_content_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["final_answer"]:
                if marker in text:
                    flags["final_answer_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["private_content"]:
                if marker in text:
                    flags["private_content_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["hidden_prompt"]:
                if marker in text:
                    flags["hidden_prompt_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["answer_key"]:
                if marker in text:
                    flags["answer_key_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["provider_output"]:
                if marker in text:
                    flags["provider_output_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["official_score"]:
                if marker in text and not boundary_context:
                    flags["official_claim_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["official_claim"]:
                if marker in text and not boundary_context:
                    flags["official_claim_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["consciousness_claim"]:
                if marker in text and not boundary_context:
                    flags["official_claim_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["identity_confusion"]:
                if marker in text:
                    flags["identity_confusion_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["prompt_execution"]:
                if marker in text:
                    flags["prompt_execution_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["provider_call"]:
                if marker in text:
                    flags["provider_output_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["dot_weslr_write"]:
                if marker in text:
                    flags["dot_weslr_write_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["feature_flag"]:
                if marker in text:
                    flags["feature_flag_detected"] = True
            for marker in _UNSAFE_TEXT_MARKERS["runtime_authority"]:
                if marker in text and not boundary_context:
                    flags["runtime_authority_detected"] = True
    return flags


def validate_internal_turing_scenario_record_v1(record: dict[str, Any]) -> dict[str, Any]:
    """Validate one metadata-only scenario record."""

    errors: list[str] = []
    warnings: list[str] = []
    category = record.get("category") if isinstance(record, dict) else None
    scenario_id = record.get("scenario_id") if isinstance(record, dict) else None

    if not isinstance(record, dict):
        return {
            "valid": False,
            "blocked": True,
            "errors": ["record_not_dict"],
            "warnings": [],
            "category": None,
            "scenario_id": None,
            "safety_booleans_valid": False,
            "raw_content_detected": False,
            "final_answer_detected": False,
            "runtime_authority_detected": False,
            "official_claim_detected": False,
        }

    for field in _REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"missing_required_field:{field}")

    if category not in INTERNAL_TURING_SCENARIO_CATEGORIES_V1:
        errors.append("unknown_category")
    if not scenario_id or not isinstance(scenario_id, str):
        errors.append("invalid_scenario_id")

    for list_field in ("dimension_targets", "expected_response_properties", "failure_modes"):
        value = record.get(list_field)
        if not isinstance(value, list) or not value:
            errors.append(f"missing_or_empty:{list_field}")

    for dimension in record.get("dimension_targets", []) if isinstance(record.get("dimension_targets"), list) else []:
        if dimension not in INTERNAL_TURING_READINESS_DIMENSIONS_V1:
            errors.append(f"unknown_dimension:{dimension}")

    for failure in record.get("failure_modes", []) if isinstance(record.get("failure_modes"), list) else []:
        if failure not in INTERNAL_TURING_FAILURE_TAXONOMY_V1:
            errors.append(f"unknown_failure_mode:{failure}")

    safety_booleans_valid = True
    for field in _FALSE_SAFETY_FIELDS:
        if record.get(field) is not False:
            errors.append(f"unsafe_boolean_true_or_missing:{field}")
            safety_booleans_valid = False
    for field in _TRUE_METADATA_FIELDS:
        if record.get(field) is not True:
            errors.append(f"metadata_boolean_false_or_missing:{field}")
            safety_booleans_valid = False

    if record.get("schema_version") != SCHEMA_VERSION_V1:
        errors.append("invalid_schema_version")

    flags = _scan_record(record)
    for flag, value in flags.items():
        if value:
            errors.append(flag)

    public_raw_content_detected = any(
        flags[name]
        for name in (
            "raw_content_detected",
            "private_content_detected",
            "hidden_prompt_detected",
            "answer_key_detected",
            "provider_output_detected",
            "prompt_execution_detected",
            "dot_weslr_write_detected",
            "feature_flag_detected",
            "identity_confusion_detected",
        )
    )
    valid = not errors
    return {
        "valid": valid,
        "blocked": not valid,
        "errors": errors,
        "warnings": warnings,
        "category": category,
        "scenario_id": scenario_id,
        "safety_booleans_valid": safety_booleans_valid,
        "raw_content_detected": public_raw_content_detected,
        "final_answer_detected": flags["final_answer_detected"],
        "runtime_authority_detected": flags["runtime_authority_detected"],
        "official_claim_detected": flags["official_claim_detected"],
    }


def validate_internal_turing_scenario_corpus_v1(corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate full metadata-only corpus coverage and safety."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(corpus, list):
        return {
            "valid": False,
            "blocked": True,
            "scenario_count": 0,
            "category_count": 0,
            "missing_categories": list(INTERNAL_TURING_SCENARIO_CATEGORIES_V1),
            "duplicate_scenario_ids": [],
            "invalid_scenario_ids": [],
            "errors": ["corpus_not_list"],
            "warnings": [],
            "all_safety_booleans_false": False,
            "all_categories_present": False,
            "all_labels_qualitative": False,
            "raw_content_detected": False,
            "final_answer_detected": False,
            "runtime_authority_detected": False,
            "official_claim_detected": False,
        }

    seen_ids: set[str] = set()
    duplicate_ids: list[str] = []
    invalid_ids: list[str] = []
    categories = []
    all_safety = True
    raw = final = runtime = official = False

    for record in corpus:
        result = validate_internal_turing_scenario_record_v1(record)
        sid = result["scenario_id"]
        if isinstance(sid, str):
            if sid in seen_ids:
                duplicate_ids.append(sid)
            seen_ids.add(sid)
        else:
            invalid_ids.append(str(sid))
        if result["category"] in INTERNAL_TURING_SCENARIO_CATEGORIES_V1:
            categories.append(result["category"])
        if not result["valid"]:
            errors.extend(f"{sid}:{error}" for error in result["errors"])
        all_safety = all_safety and result["safety_booleans_valid"]
        raw = raw or result["raw_content_detected"]
        final = final or result["final_answer_detected"]
        runtime = runtime or result["runtime_authority_detected"]
        official = official or result["official_claim_detected"]

    required = set(INTERNAL_TURING_SCENARIO_CATEGORIES_V1)
    present = set(categories)
    missing = sorted(required - present)
    if missing:
        errors.append("missing_categories")
    if duplicate_ids:
        errors.append("duplicate_scenario_ids")
    all_categories_present = not missing and len(present) == len(required)
    all_labels_qualitative = True

    valid = not errors
    return {
        "valid": valid,
        "blocked": not valid,
        "scenario_count": len(corpus),
        "category_count": len(present),
        "missing_categories": missing,
        "duplicate_scenario_ids": duplicate_ids,
        "invalid_scenario_ids": invalid_ids,
        "errors": errors,
        "warnings": warnings,
        "all_safety_booleans_false": all_safety,
        "all_categories_present": all_categories_present,
        "all_labels_qualitative": all_labels_qualitative,
        "raw_content_detected": raw,
        "final_answer_detected": final,
        "runtime_authority_detected": runtime,
        "official_claim_detected": official,
    }


def summarize_internal_turing_scenario_corpus_v1(corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Return safe metadata-only corpus summary."""

    validation = validate_internal_turing_scenario_corpus_v1(corpus)
    dimension_coverage = sorted({
        dimension
        for record in corpus if isinstance(record, dict)
        for dimension in record.get("dimension_targets", [])
        if dimension in INTERNAL_TURING_READINESS_DIMENSIONS_V1
    })
    failure_coverage = sorted({
        failure
        for record in corpus if isinstance(record, dict)
        for failure in record.get("failure_modes", [])
        if failure in INTERNAL_TURING_FAILURE_TAXONOMY_V1
    })
    categories = sorted({
        record.get("category") for record in corpus
        if isinstance(record, dict) and record.get("category") in INTERNAL_TURING_SCENARIO_CATEGORIES_V1
    })
    return {
        "scenario_count": validation["scenario_count"],
        "category_count": validation["category_count"],
        "categories": categories,
        "dimension_coverage": dimension_coverage,
        "failure_mode_coverage": failure_coverage,
        "governance_expected_count": sum(1 for record in corpus if isinstance(record, dict) and record.get("governance_expected") is True),
        "validation_status": {
            "valid": validation["valid"],
            "blocked": validation["blocked"],
            "errors": list(validation["errors"]),
        },
        "readiness_labels": list(INTERNAL_TURING_READINESS_LABELS_V1),
        "minor_followups": list(INTERNAL_TURING_MINOR_FOLLOWUPS_V1),
    }


def render_internal_turing_scenario_corpus_markdown_v1(corpus: list[dict[str, Any]]) -> str:
    """Render safe internal Markdown without leaking invalid/offending content."""

    validation = validate_internal_turing_scenario_corpus_v1(corpus)
    if not validation["valid"]:
        safe_errors = sorted(set(str(error).split(":")[-1] for error in validation["errors"]))
        return "\n".join([
            "# Internal Turing Scenario Corpus V1",
            "",
            "Status: blocked_invalid_metadata",
            f"Validation valid: {validation['valid']}",
            "Safe reason labels:",
            *[f"- {error}" for error in safe_errors],
            "",
            "Safety confirmation: no raw/offending scenario content rendered.",
        ])

    summary = summarize_internal_turing_scenario_corpus_v1(corpus)
    lines = [
        "# Internal Turing Scenario Corpus V1",
        "",
        "Status: metadata_only_corpus_valid",
        f"Validation valid: {validation['valid']}",
        f"Scenario count: {summary['scenario_count']}",
        f"Category count: {summary['category_count']}",
        f"Governance expected count: {summary['governance_expected_count']}",
        "",
        "## Category Coverage",
        *[f"- {category}" for category in summary["categories"]],
        "",
        "## Dimension Coverage",
        *[f"- {dimension}" for dimension in summary["dimension_coverage"]],
        "",
        "## Failure Taxonomy Coverage",
        *[f"- {failure}" for failure in summary["failure_mode_coverage"]],
        "",
        "## Minor Followups",
        *[f"- {followup}" for followup in summary["minor_followups"]],
        "",
        "## Safety Confirmation",
        "- metadata-only",
        "- no prompt execution",
        "- no final-answer generation",
        "- no runtime wiring",
        "- no provider/model/search/advisor calls",
        "- no official benchmark/Turing/IQ/certification/product-readiness claims",
        "",
        "## Next Lane Recommendation",
        "REVIEW_INTERNAL_TURING_SCENARIO_CORPUS_HELPERS_IMPLEMENTATION_V1",
    ]
    return "\n".join(lines)


def to_internal_turing_scenario_corpus_json_safe_v1(corpus: list[dict[str, Any]]) -> list[dict[str, Any]] | dict[str, Any]:
    """Return JSON-safe metadata copy or explicit invalid wrapper."""

    validation = validate_internal_turing_scenario_corpus_v1(corpus)
    if not validation["valid"]:
        return {
            "valid": False,
            "blocked": True,
            "reason_labels": sorted(set(str(error).split(":")[-1] for error in validation["errors"])),
            "scenario_count": validation["scenario_count"],
        }
    return deepcopy(corpus)
