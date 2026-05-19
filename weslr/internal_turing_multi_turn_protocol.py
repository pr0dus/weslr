"""Metadata-only internal Turing multi-turn protocol helpers V1.

This module is deterministic, import-safe, side-effect free, and in-memory only.
It does not execute prompts, call providers, generate final answers, wire runtime
behavior, write files, implement a runner/harness, judge, score, or claim
official evaluation status.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from weslr.internal_turing_scenario_corpus import build_internal_turing_scenario_corpus_v1

SCHEMA_VERSION_V1 = "internal_turing_multi_turn_protocol_v1"

INTERNAL_TURING_MULTI_TURN_EPISODE_GROUPS_V1 = (
    "ordinary_multi_turn_request",
    "ambiguity_then_clarification",
    "correction_after_wrong_interpretation",
    "frustration_then_recovery",
    "continuity_reference_with_memory_boundary",
    "domain_onboarding_over_multiple_turns",
    "evidence_required_claim_over_multiple_turns",
    "uncertainty_preserving_explanation",
    "governance_escalation_sequence",
    "official_claim_trap_sequence",
    "final_answer_authority_trap_sequence",
    "runtime_authority_trap_sequence",
    "occ_openclaw_identity_separation_sequence",
    "raw_private_content_boundary_sequence",
    "anti_gaming_sequence",
)

INTERNAL_TURING_MULTI_TURN_DIMENSIONS_V1 = (
    "turn-to-turn context preservation",
    "user-intent tracking across turns",
    "ambiguity handling across turns",
    "correction acceptance",
    "continuity without memory overclaim",
    "evidence/provenance honesty",
    "uncertainty preservation",
    "non-canned response formation",
    "emotional/social appropriateness",
    "domain adaptation",
    "governance escalation when needed",
    "final-answer authority boundary",
    "runtime authority boundary",
    "OCC/OpenClaw identity separation",
    "no official overclaiming",
)

INTERNAL_TURING_MULTI_TURN_OBSERVATION_LABELS_V1 = (
    "context_preserved",
    "intent_updated",
    "clarification_requested_when_needed",
    "correction_accepted",
    "continuity_used_with_boundary",
    "memory_boundary_respected",
    "evidence_boundary_respected",
    "uncertainty_preserved",
    "non_canned_response_expected",
    "governance_escalation_expected",
    "identity_boundary_preserved",
    "runtime_authority_not_granted",
    "final_answer_authority_not_granted",
    "not_ready_for_runtime",
)

INTERNAL_TURING_MULTI_TURN_FAILURE_TAXONOMY_V1 = (
    "turn_context_drift",
    "obsolete_intent_persistence",
    "missed_clarification",
    "correction_rejected",
    "memory_overclaim",
    "evidence_overclaim",
    "uncertainty_lost",
    "canned_multi_turn_behavior",
    "emotional_mismatch",
    "domain_constraint_missed",
    "governance_missed",
    "final_answer_authority_overreach",
    "runtime_authority_overreach",
    "official_claim_overreach",
    "identity_confusion",
    "raw_private_content_leakage",
)

INTERNAL_TURING_MULTI_TURN_MINOR_FOLLOWUPS_V1 = (
    "renderer_next_lane_wording_drift",
    "validator_phrase_key_limitation",
)

INTERNAL_TURING_MULTI_TURN_RISKS_V1 = (
    "Turing-name overclaim risk",
    "future label non-scoring discipline",
)

INTERNAL_TURING_MULTI_TURN_READINESS_LABELS_V1 = (
    "internal_turing_multi_turn_protocol_helpers_implemented",
    "metadata_only_episode_records",
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
    "episode_id",
    "episode_group",
    "scenario_ids",
    "turn_count",
    "turn_summaries",
    "dimension_targets",
    "context_constraints",
    "continuity_requirements",
    "correction_points",
    "ambiguity_points",
    "evidence_requirements",
    "memory_boundaries",
    "governance_expected",
    "expected_response_properties",
    "failure_modes",
    "safety_boundaries",
    "schema_version",
    "metadata_only",
    "internal_only",
    "raw_content_allowed",
    "prompt_execution_allowed",
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

_FALSE_SAFETY_FIELDS = (
    "raw_content_allowed",
    "prompt_execution_allowed",
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
    "runtime_authority": ("runtime ready", "runtime output:", "runtime authority granted"),
}

_GROUP_TO_SCENARIO_CATEGORY = {
    "ordinary_multi_turn_request": "multi_turn_coherence",
    "ambiguity_then_clarification": "ambiguous_human_request",
    "correction_after_wrong_interpretation": "correction_after_misunderstanding",
    "frustration_then_recovery": "user_emotional_frustration",
    "continuity_reference_with_memory_boundary": "memory_boundary_request",
    "domain_onboarding_over_multiple_turns": "domain_onboarding_context",
    "evidence_required_claim_over_multiple_turns": "evidence_required_claim",
    "uncertainty_preserving_explanation": "uncertainty_required_answer",
    "governance_escalation_sequence": "governance_escalation_required",
    "official_claim_trap_sequence": "official_claim_trap",
    "final_answer_authority_trap_sequence": "final_answer_authority_boundary",
    "runtime_authority_trap_sequence": "runtime_authority_boundary",
    "occ_openclaw_identity_separation_sequence": "occ_openclaw_identity_separation",
    "raw_private_content_boundary_sequence": "raw_private_content_boundary",
    "anti_gaming_sequence": "anti_gaming_boundary",
}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _approved_scenario_records_by_id() -> dict[str, dict[str, Any]]:
    return {record["scenario_id"]: record for record in build_internal_turing_scenario_corpus_v1()}


def _approved_scenario_ids() -> set[str]:
    return set(_approved_scenario_records_by_id())


def _scenario_id_for_category(category: str) -> str:
    for record in build_internal_turing_scenario_corpus_v1():
        if record.get("category") == category:
            return str(record["scenario_id"])
    raise ValueError(f"missing approved scenario category: {category}")


def build_internal_turing_multi_turn_episode_v1(
    *,
    episode_id: str,
    episode_group: str,
    scenario_ids: list[str] | tuple[str, ...],
    turn_summaries: list[str] | tuple[str, ...],
    dimension_targets: list[str] | tuple[str, ...],
    context_constraints: list[str] | tuple[str, ...],
    continuity_requirements: list[str] | tuple[str, ...],
    correction_points: list[str] | tuple[str, ...],
    ambiguity_points: list[str] | tuple[str, ...],
    evidence_requirements: list[str] | tuple[str, ...],
    memory_boundaries: list[str] | tuple[str, ...],
    governance_expected: bool = False,
    expected_response_properties: list[str] | tuple[str, ...] | None = None,
    failure_modes: list[str] | tuple[str, ...] | None = None,
    safety_boundaries: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build one safe metadata-only multi-turn episode record."""

    turn_summary_list = _as_list(turn_summaries)
    return {
        "episode_id": episode_id,
        "episode_group": episode_group,
        "scenario_ids": _as_list(scenario_ids),
        "turn_count": len(turn_summary_list),
        "turn_summaries": turn_summary_list,
        "dimension_targets": _as_list(dimension_targets),
        "context_constraints": _as_list(context_constraints),
        "continuity_requirements": _as_list(continuity_requirements),
        "correction_points": _as_list(correction_points),
        "ambiguity_points": _as_list(ambiguity_points),
        "evidence_requirements": _as_list(evidence_requirements),
        "memory_boundaries": _as_list(memory_boundaries),
        "governance_expected": bool(governance_expected),
        "expected_response_properties": _as_list(expected_response_properties),
        "failure_modes": _as_list(failure_modes),
        "safety_boundaries": _as_list(safety_boundaries),
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "raw_content_allowed": False,
        "prompt_execution_allowed": False,
        "final_answer_required": False,
        "runtime_execution_allowed": False,
        "official_score_allowed": False,
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


def _default_episode_for_group(index: int, group: str) -> dict[str, Any]:
    category = _GROUP_TO_SCENARIO_CATEGORY[group]
    scenario_id = _scenario_id_for_category(category)
    dims = INTERNAL_TURING_MULTI_TURN_DIMENSIONS_V1
    failures = INTERNAL_TURING_MULTI_TURN_FAILURE_TAXONOMY_V1
    governance_expected = group in {
        "governance_escalation_sequence",
        "official_claim_trap_sequence",
        "final_answer_authority_trap_sequence",
        "runtime_authority_trap_sequence",
    }
    return build_internal_turing_multi_turn_episode_v1(
        episode_id=f"itmtp_v1_{index:02d}_{group}",
        episode_group=group,
        scenario_ids=[scenario_id],
        turn_summaries=[
            f"Metadata turn summary 1 for {group}; structural intent only.",
            f"Metadata turn summary 2 for {group}; boundary update only.",
        ],
        dimension_targets=[dims[(index - 1) % len(dims)], dims[index % len(dims)]],
        context_constraints=["internal-only", "metadata-only", "non-executing episode summary"],
        continuity_requirements=["carry only structural constraints across turns"],
        correction_points=["accept correction as metadata when applicable"],
        ambiguity_points=["request clarification when metadata marks ambiguity"],
        evidence_requirements=["preserve provenance boundary and unknowns"],
        memory_boundaries=["summary-only continuity; sensitive details excluded"],
        governance_expected=governance_expected,
        expected_response_properties=[
            "qualitative boundary-aware response property",
            "no final-answer authority",
        ],
        failure_modes=[failures[(index - 1) % len(failures)]],
        safety_boundaries=[
            "raw_content_allowed=false",
            "prompt_execution_allowed=false",
            "final_answer_required=false",
            "runtime_execution_allowed=false",
            "official_score_allowed=false",
        ],
    )


def build_internal_turing_multi_turn_episode_set_v1() -> list[dict[str, Any]]:
    """Build the full 15-group metadata-only multi-turn episode set."""

    return [
        _default_episode_for_group(index, group)
        for index, group in enumerate(INTERNAL_TURING_MULTI_TURN_EPISODE_GROUPS_V1, start=1)
    ]


def _iter_key_values(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{path}.{key}" if path else str(key)
            yield key_path, key, item
            yield from _iter_key_values(item, key_path)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"
            yield item_path, item_path, item
            yield from _iter_key_values(item, item_path)


def _scan_record(record: dict[str, Any]) -> dict[str, bool]:
    flags = {
        "raw_content_detected": False,
        "final_answer_detected": False,
        "prompt_execution_detected": False,
        "runtime_authority_detected": False,
        "official_claim_detected": False,
        "private_content_detected": False,
        "hidden_prompt_detected": False,
        "answer_key_detected": False,
        "provider_output_detected": False,
        "dot_weslr_write_detected": False,
        "feature_flag_detected": False,
        "identity_confusion_detected": False,
        "consciousness_claim_detected": False,
    }
    for _path, key, item in _iter_key_values(record):
        key_lower = str(key).lower()
        if any(fragment in key_lower for fragment in _UNSAFE_KEY_FRAGMENTS):
            if key_lower == "official_score_allowed":
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
            lowered = item.lower()
            for flag_name, markers in _UNSAFE_TEXT_MARKERS.items():
                if any(marker in lowered for marker in markers):
                    if flag_name == "raw_content":
                        flags["raw_content_detected"] = True
                    elif flag_name == "final_answer":
                        flags["final_answer_detected"] = True
                    elif flag_name == "private_content":
                        flags["private_content_detected"] = True
                    elif flag_name == "hidden_prompt":
                        flags["hidden_prompt_detected"] = True
                    elif flag_name == "answer_key":
                        flags["answer_key_detected"] = True
                    elif flag_name == "provider_output":
                        flags["provider_output_detected"] = True
                    elif flag_name in {"official_score", "official_claim"}:
                        flags["official_claim_detected"] = True
                    elif flag_name == "consciousness_claim":
                        flags["consciousness_claim_detected"] = True
                    elif flag_name == "identity_confusion":
                        flags["identity_confusion_detected"] = True
                    elif flag_name == "prompt_execution":
                        flags["prompt_execution_detected"] = True
                    elif flag_name == "provider_call":
                        flags["provider_output_detected"] = True
                    elif flag_name == "dot_weslr_write":
                        flags["dot_weslr_write_detected"] = True
                    elif flag_name == "feature_flag":
                        flags["feature_flag_detected"] = True
                    elif flag_name == "runtime_authority":
                        flags["runtime_authority_detected"] = True
    return flags


def validate_internal_turing_multi_turn_episode_v1(episode: dict[str, Any]) -> dict[str, Any]:
    """Validate one metadata-only multi-turn episode record."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(episode, dict):
        return {
            "valid": False,
            "blocked": True,
            "errors": ["episode_not_dict"],
            "warnings": [],
            "episode_id": None,
            "episode_group": None,
            "safety_booleans_valid": False,
            "raw_content_detected": False,
            "final_answer_detected": False,
            "prompt_execution_detected": False,
            "runtime_authority_detected": False,
            "official_claim_detected": False,
        }

    for field in _REQUIRED_FIELDS:
        if field not in episode:
            errors.append(f"missing_required_field:{field}")

    episode_id = episode.get("episode_id")
    episode_group = episode.get("episode_group")
    scenario_ids = _as_list(episode.get("scenario_ids"))
    turn_summaries = _as_list(episode.get("turn_summaries"))
    turn_count = episode.get("turn_count")

    if not episode_id or not isinstance(episode_id, str):
        errors.append("invalid_episode_id")
    if episode_group not in INTERNAL_TURING_MULTI_TURN_EPISODE_GROUPS_V1:
        errors.append("unknown_episode_group")
    approved_ids = _approved_scenario_ids()
    unknown_scenario_ids = [sid for sid in scenario_ids if sid not in approved_ids]
    if unknown_scenario_ids:
        errors.append("unknown_scenario_id")
    if not isinstance(turn_count, int) or turn_count < 2:
        errors.append("turn_count_lt_2")
    if isinstance(turn_count, int) and len(turn_summaries) != turn_count:
        errors.append("turn_summaries_count_mismatch")
    if not turn_summaries or any(not isinstance(summary, str) or not summary.strip() for summary in turn_summaries):
        errors.append("empty_turn_summary")
    for list_field in ("dimension_targets", "expected_response_properties", "failure_modes"):
        values = _as_list(episode.get(list_field))
        if not values or any(not isinstance(value, str) or not value.strip() for value in values):
            errors.append(f"empty_required_list:{list_field}")

    safety_booleans_valid = True
    for field in _FALSE_SAFETY_FIELDS:
        if episode.get(field) is not False:
            safety_booleans_valid = False
            errors.append(f"unsafe_boolean_true_or_missing:{field}")
    for field in _TRUE_METADATA_FIELDS:
        if episode.get(field) is not True:
            errors.append(f"metadata_boolean_false_or_missing:{field}")

    flags = _scan_record(episode)
    for flag, error_name in (
        ("raw_content_detected", "raw_content_detected"),
        ("final_answer_detected", "final_answer_detected"),
        ("private_content_detected", "private_content_detected"),
        ("hidden_prompt_detected", "hidden_prompt_detected"),
        ("answer_key_detected", "answer_key_detected"),
        ("provider_output_detected", "provider_or_model_output_detected"),
        ("official_claim_detected", "official_score_or_claim_detected"),
        ("runtime_authority_detected", "runtime_authority_detected"),
        ("prompt_execution_detected", "prompt_execution_detected"),
        ("dot_weslr_write_detected", "dot_weslr_write_detected"),
        ("feature_flag_detected", "feature_flag_detected"),
        ("identity_confusion_detected", "identity_confusion_detected"),
        ("consciousness_claim_detected", "consciousness_or_sentience_claim_detected"),
    ):
        if flags[flag]:
            errors.append(error_name)

    valid = not errors
    return {
        "valid": valid,
        "blocked": not valid,
        "errors": errors,
        "warnings": warnings,
        "episode_id": episode_id,
        "episode_group": episode_group,
        "safety_booleans_valid": safety_booleans_valid,
        "raw_content_detected": flags["raw_content_detected"] or flags["private_content_detected"] or flags["hidden_prompt_detected"] or flags["answer_key_detected"],
        "final_answer_detected": flags["final_answer_detected"],
        "prompt_execution_detected": flags["prompt_execution_detected"],
        "runtime_authority_detected": flags["runtime_authority_detected"],
        "official_claim_detected": flags["official_claim_detected"] or flags["consciousness_claim_detected"],
    }


def validate_internal_turing_multi_turn_episode_set_v1(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate a metadata-only multi-turn episode set."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(episodes, list):
        return {
            "valid": False,
            "blocked": True,
            "episode_count": 0,
            "group_count": 0,
            "missing_groups": list(INTERNAL_TURING_MULTI_TURN_EPISODE_GROUPS_V1),
            "duplicate_episode_ids": [],
            "invalid_episode_ids": [],
            "unknown_scenario_ids": [],
            "errors": ["episodes_not_list"],
            "warnings": [],
            "all_safety_booleans_false": False,
            "all_groups_present": False,
            "all_scenario_refs_approved": False,
            "all_labels_qualitative": False,
            "raw_content_detected": False,
            "final_answer_detected": False,
            "prompt_execution_detected": False,
            "runtime_authority_detected": False,
            "official_claim_detected": False,
        }

    seen: set[str] = set()
    duplicates: list[str] = []
    invalid_ids: list[str] = []
    unknown_scenario_ids: list[str] = []
    groups = set()
    all_safety = True
    raw = final = prompt_exec = runtime = official = False
    approved_ids = _approved_scenario_ids()

    for episode in episodes:
        result = validate_internal_turing_multi_turn_episode_v1(episode)
        eid = result.get("episode_id")
        if eid:
            if eid in seen:
                duplicates.append(eid)
            seen.add(eid)
        if not result["valid"]:
            invalid_ids.append(str(eid))
            errors.extend(f"{eid}:{error}" for error in result["errors"])
        if isinstance(episode, dict):
            group = episode.get("episode_group")
            if group in INTERNAL_TURING_MULTI_TURN_EPISODE_GROUPS_V1:
                groups.add(group)
            for sid in _as_list(episode.get("scenario_ids")):
                if sid not in approved_ids:
                    unknown_scenario_ids.append(sid)
        all_safety = all_safety and bool(result["safety_booleans_valid"])
        raw = raw or bool(result["raw_content_detected"])
        final = final or bool(result["final_answer_detected"])
        prompt_exec = prompt_exec or bool(result["prompt_execution_detected"])
        runtime = runtime or bool(result["runtime_authority_detected"])
        official = official or bool(result["official_claim_detected"])

    missing_groups = [group for group in INTERNAL_TURING_MULTI_TURN_EPISODE_GROUPS_V1 if group not in groups]
    if missing_groups:
        errors.append("missing_required_episode_groups")
    if duplicates:
        errors.append("duplicate_episode_ids")
    if unknown_scenario_ids:
        errors.append("unknown_scenario_ids")
    all_labels_qualitative = True
    valid = not errors and not duplicates and not invalid_ids and not missing_groups and not unknown_scenario_ids
    return {
        "valid": valid,
        "blocked": not valid,
        "episode_count": len(episodes),
        "group_count": len(groups),
        "missing_groups": missing_groups,
        "duplicate_episode_ids": duplicates,
        "invalid_episode_ids": invalid_ids,
        "unknown_scenario_ids": sorted(set(unknown_scenario_ids)),
        "errors": errors,
        "warnings": warnings,
        "all_safety_booleans_false": all_safety,
        "all_groups_present": not missing_groups,
        "all_scenario_refs_approved": not unknown_scenario_ids,
        "all_labels_qualitative": all_labels_qualitative,
        "raw_content_detected": raw,
        "final_answer_detected": final,
        "prompt_execution_detected": prompt_exec,
        "runtime_authority_detected": runtime,
        "official_claim_detected": official,
    }


def summarize_internal_turing_multi_turn_episode_set_v1(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Return safe metadata summary for a multi-turn episode set."""

    validation = validate_internal_turing_multi_turn_episode_set_v1(episodes)
    safe_episodes = episodes if isinstance(episodes, list) else []
    scenario_refs = sorted({sid for episode in safe_episodes if isinstance(episode, dict) for sid in _as_list(episode.get("scenario_ids"))})
    dimensions = sorted({dim for episode in safe_episodes if isinstance(episode, dict) for dim in _as_list(episode.get("dimension_targets"))})
    failures = sorted({fm for episode in safe_episodes if isinstance(episode, dict) for fm in _as_list(episode.get("failure_modes"))})
    groups = [group for group in INTERNAL_TURING_MULTI_TURN_EPISODE_GROUPS_V1 if any(isinstance(ep, dict) and ep.get("episode_group") == group for ep in safe_episodes)]
    return {
        "episode_count": len(safe_episodes),
        "group_count": len(groups),
        "groups": groups,
        "scenario_reference_count": len(scenario_refs),
        "dimension_coverage": dimensions,
        "failure_mode_coverage": failures,
        "governance_expected_count": sum(1 for episode in safe_episodes if isinstance(episode, dict) and episode.get("governance_expected") is True),
        "validation_status": "valid" if validation["valid"] else "blocked",
        "readiness_labels": list(INTERNAL_TURING_MULTI_TURN_READINESS_LABELS_V1),
        "minor_followups": list(INTERNAL_TURING_MULTI_TURN_MINOR_FOLLOWUPS_V1),
        "risks_carried_forward": list(INTERNAL_TURING_MULTI_TURN_RISKS_V1),
    }


def render_internal_turing_multi_turn_episode_set_markdown_v1(episodes: list[dict[str, Any]]) -> str:
    """Render safe internal Markdown for a multi-turn episode set."""

    validation = validate_internal_turing_multi_turn_episode_set_v1(episodes)
    summary = summarize_internal_turing_multi_turn_episode_set_v1(episodes if isinstance(episodes, list) else [])
    lines = [
        "# WESLR Internal Turing Multi-Turn Protocol Episode Set V1",
        "",
        "Layer: helper-only metadata-only internal evaluation design support.",
        "",
        "## Episode Set Status",
        f"- episode_count: `{summary['episode_count']}`",
        f"- group_count: `{summary['group_count']}`",
        f"- validation_status: `{summary['validation_status']}`",
        "",
        "## Validation Status",
        f"- valid: `{validation['valid']}`",
        f"- blocked: `{validation['blocked']}`",
    ]
    if not validation["valid"]:
        lines.extend([
            "- blocked_reason_labels:",
            *[f"  - `{error}`" for error in validation["errors"][:20]],
        ])
    lines.extend([
        "",
        "## Group Coverage",
        *[f"- `{group}`" for group in summary["groups"]],
        "",
        "## Scenario Reference Coverage",
        f"- scenario_reference_count: `{summary['scenario_reference_count']}`",
        f"- all_scenario_refs_approved: `{validation['all_scenario_refs_approved']}`",
        "",
        "## Dimension Coverage",
        *[f"- `{dimension}`" for dimension in summary["dimension_coverage"]],
        "",
        "## Failure Taxonomy Coverage",
        *[f"- `{failure}`" for failure in summary["failure_mode_coverage"]],
        "",
        "## Governance Count",
        f"- governance_expected_count: `{summary['governance_expected_count']}`",
        "",
        "## Minor Followups",
        *[f"- `{followup}`" for followup in summary["minor_followups"]],
        "",
        "## Carried Risks",
        *[f"- `{risk}`" for risk in summary["risks_carried_forward"]],
        "",
        "## Safety Confirmation",
        "- metadata-only episode records",
        "- internal-only non-official support",
        "- qualitative labels only",
        "- prompt execution not authorized",
        "- runtime integration not authorized",
        "- final-answer authority not granted",
        "- official evaluation not claimed",
        "- no public marketing claims",
        "- no consciousness/sentience claims",
        "",
        "## Next Lane Recommendation",
        "`REVIEW_INTERNAL_TURING_MULTI_TURN_PROTOCOL_HELPERS_IMPLEMENTATION_V1`",
    ])
    return "\n".join(lines)


def to_internal_turing_multi_turn_episode_set_json_safe_v1(episodes: list[dict[str, Any]]) -> list[dict[str, Any]] | dict[str, Any]:
    """Return a JSON-safe metadata copy, or an explicit invalid wrapper."""

    validation = validate_internal_turing_multi_turn_episode_set_v1(episodes)
    if not validation["valid"]:
        return {
            "valid": False,
            "blocked": True,
            "schema_version": SCHEMA_VERSION_V1,
            "reason_labels": list(validation["errors"]),
            "invalid_episode_ids": list(validation["invalid_episode_ids"]),
            "metadata_only": True,
            "internal_only": True,
            "raw_content_returned": False,
            "final_answer_returned": False,
            "provider_output_returned": False,
            "runtime_output_returned": False,
            "official_score_returned": False,
        }
    return deepcopy(episodes)
