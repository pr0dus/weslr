"""Prompt Set Routing Validator V1.

This module predicts chat_responder.py routing for controlled prompt items
without importing or calling the chat responder, the chat generator, or any
runtime model/search/advisor provider.

It is pure preflight logic: text analysis + metadata comparison only.
"""

from __future__ import annotations

import re
from typing import Any, Optional


SAFE_KEYWORDS_V1: set[str] = {
    "lunch",
    "workout",
    "gym",
    "run",
    "exercise",
    "plan",
    "email",
    "wife",
    "partner",
    "code",
    "bug",
}

BLOCKED_ORDINARY_TASK_TERMS_V1: set[str] = {
    "official iq",
    "official benchmark",
    "certification",
    "certified",
    "answer key",
    "hidden prompt",
    "protected test",
    "are you conscious",
    "are you sentient",
    "medical",
    "legal",
    "financial",
    "diagnose",
    "prescription",
    "lawsuit",
    "investment",
    "remember me",
    "do you remember",
    "write a story",
    "poem",
    "creative writing",
}

CURRENTNESS_SEARCH_TERMS_V1: set[str] = {
    "current",
    "latest",
    "recent",
    "today",
    "source",
    "sources",
    "cite",
    "look up",
    "search",
    "news",
    "weather",
    "price",
    "live web",
    "external source",
    "check online",
}

BENIGN_LUNCH_EXCLUSIONS_V1: set[str] = {
    "latest lunch",
    "recent lunch",
    "current lunch",
}

PLANNING_TERMS_V1: set[str] = {
    "plan",
    "steps",
    "step plan",
    "rollout",
    "checklist",
    "break down",
    "debug",
    "organize",
    "migration",
    "deployment",
    "deploy",
    "staged change",
    "server change",
    "sequence",
    "schedule",
    "workflow",
    "roadmap",
}

COMPLEX_PLANNING_TERMS_V1: set[str] = {
    "rollout",
    "debug",
    "break down",
    "checklist",
    "step plan",
    "migration",
    "deployment",
    "deploy",
    "staged change",
    "server change",
    "rollback",
    "monitoring",
}

TOO_VAGUE_TERMS_V1: set[str] = {
    "plan this",
    "help me plan",
    "make a plan",
    "what should i do",
}

TOOL_TERMS_V1: set[str] = {
    "calculate",
    "compute",
    "measure",
    "run a calculation",
    "use a tool",
    "exact total",
    "how many",
}


ROUTE_CLASSES_V1: set[str] = {
    "safe_keyword_branch",
    "safe_limited_ordinary_task",
    "safe_frontier_shadow_metadata",
    "safe_plan_helper_feature_flag_required",
    "requires_generate_chat_mock",
    "forbidden_model_path",
    "forbidden_search_or_advisor_path",
    "ambiguous_needs_review",
}


# Blocked families per WESLR_EVALUATION_SAFETY_BOUNDARIES_V1
BLOCKED_FAMILIES_V1: set[str] = {
    "memory_honesty",
    "continuity_relationship",
    "self_identity_boundaries",
    "evidence_source_boundaries",
    "guardrail_preservation",
    "live_slice_behavior",
}


def _text_has_any(text: str, terms: set[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _text_has_any_word(text: str, words: set[str]) -> bool:
    lowered = text.lower()
    found = set(re.findall(r"\b\w+\b", lowered))
    return bool(found & words)


def _text_has_all(text: str, terms: set[str]) -> bool:
    lowered = text.lower()
    return all(term in lowered for term in terms)


def _has_supplied_context(text: str) -> bool:
    return len([token for token in text.split() if len(token) > 3]) >= 5


def _extract_sequence_markers(text: str) -> list[str]:
    lowered = text.lower()
    markers = []
    for i in range(1, 6):
        if f"step {i}" in lowered or f"{i}." in lowered:
            markers.append(f"step_{i}")
    if "first" in lowered:
        markers.append("first")
    if "then" in lowered:
        markers.append("then")
    return markers


def _classify_limited_ordinary_task(text: str) -> dict[str, Any]:
    """Replicate chat_responder.py _classify_limited_ordinary_task_request logic."""
    if not text.strip():
        return {"eligible": False, "decision": "fallback_existing_path", "reason": "empty_message"}

    if _text_has_any(text, BLOCKED_ORDINARY_TASK_TERMS_V1):
        return {"eligible": False, "decision": "fallback_existing_path", "reason": "outside_safe_ordinary_scope"}

    if _text_has_any(text, CURRENTNESS_SEARCH_TERMS_V1) and not _text_has_any(text, BENIGN_LUNCH_EXCLUSIONS_V1):
        return {
            "eligible": True,
            "decision": "external_evidence_needed",
            "reason": "current_or_source_evidence_requested",
            "missing_context": ["current external evidence or supplied sources"],
        }

    if _text_has_any(text, TOOL_TERMS_V1):
        return {
            "eligible": True,
            "decision": "tool_or_calculation_needed",
            "reason": "tool_or_calculation_needed",
            "missing_context": ["calculation inputs or tool output"],
        }

    if not _text_has_any(text, PLANNING_TERMS_V1):
        return {"eligible": False, "decision": "fallback_existing_path", "reason": "not_an_ordinary_task_slice"}

    if _text_has_any(text, TOO_VAGUE_TERMS_V1) and not _has_supplied_context(text):
        return {
            "eligible": True,
            "decision": "ask_clarifying_question",
            "reason": "missing_task_goal",
            "missing_context": ["the concrete task or desired outcome"],
        }

    explicit_sequence = _extract_sequence_markers(text)
    if _text_has_any(text, COMPLEX_PLANNING_TERMS_V1) or explicit_sequence:
        return {
            "eligible": True,
            "decision": "bounded_step_plan",
            "reason": "safe_complex_ordinary_task",
        }

    return {
        "eligible": True,
        "decision": "answer_with_available_context",
        "reason": "safe_simple_ordinary_planning_task",
    }


def predict_chat_responder_route_v1(
    prompt_text: str,
    *,
    metadata: Optional[dict[str, Any]] = None,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Simulate chat_responder.py respond_chat routing without calling it.

    Returns route prediction with classification, safety flags, and reason labels.
    """
    cfg = dict(config) if config else {}
    mock_active = bool(cfg.get("generate_chat_mock_active", False))
    feature_flag_enabled = bool(cfg.get("plan_helper_feature_flag_enabled", False))

    result: dict[str, Any] = {
        "route_class": "ambiguous_needs_review",
        "safe_to_call_without_mock": False,
        "requires_mock": False,
        "blocked": True,
        "reason_labels": [],
        "matched_terms": [],
        "model_calls": False,
        "search_calls": False,
        "advisor_calls": False,
        "writes": False,
        "raw_text_retained": False,
        "confidence_label": "medium",
    }

    text = str(prompt_text or "").strip()
    if not text:
        result["route_class"] = "ambiguous_needs_review"
        result["reason_labels"].append("empty_message")
        result["confidence_label"] = "high"
        return result

    # 1. Blocked terms
    if _text_has_any(text, BLOCKED_ORDINARY_TASK_TERMS_V1):
        result["route_class"] = "forbidden_model_path"
        result["reason_labels"].append("outside_safe_ordinary_scope")
        result["confidence_label"] = "high"
        return result

    # 2. Keyword branches — checked before search/currentness so benign lunch/plan queries win
    matched_keywords = [kw for kw in SAFE_KEYWORDS_V1 if _text_has_any_word(text, {kw})]
    if matched_keywords:
        # If the only keyword is "plan" and complex planning terms are present,
        # route to limited ordinary task instead of keyword branch.
        if matched_keywords == ["plan"] and _text_has_any(text, COMPLEX_PLANNING_TERMS_V1):
            pass  # fall through to limited ordinary task
        else:
            result["route_class"] = "safe_keyword_branch"
            result["safe_to_call_without_mock"] = True
            result["blocked"] = False
            result["matched_terms"] = matched_keywords
            result["reason_labels"].append("keyword_match")
            result["confidence_label"] = "high"
            return result

    # 3. Search / currentness / advisor
    if _text_has_any(text, CURRENTNESS_SEARCH_TERMS_V1) and not _text_has_any(text, BENIGN_LUNCH_EXCLUSIONS_V1):
        result["route_class"] = "forbidden_search_or_advisor_path"
        result["reason_labels"].append("search_or_currentness_path_detected")
        result["search_calls"] = True
        result["advisor_calls"] = True
        result["confidence_label"] = "high"
        return result

    # 4. Limited ordinary task
    ot_class = _classify_limited_ordinary_task(text)
    if ot_class.get("eligible") is True:
        result["route_class"] = "safe_limited_ordinary_task"
        result["safe_to_call_without_mock"] = True
        result["blocked"] = False
        result["matched_terms"] = [ot_class.get("decision", "")]
        result["reason_labels"].append(f"ordinary_task:{ot_class.get('decision')}")
        result["confidence_label"] = "high"
        return result

    # 5. Frontier shadow metadata (explicit config)
    if metadata and metadata.get("frontier_shadow_metadata") is True:
        result["route_class"] = "safe_frontier_shadow_metadata"
        result["safe_to_call_without_mock"] = True
        result["blocked"] = False
        result["reason_labels"].append("frontier_shadow_metadata_flag")
        result["confidence_label"] = "high"
        return result

    # 6. Plan helper (requires explicit feature flag)
    if _text_has_any(text, {"plan", "help me plan", "plan my next steps"}):
        if feature_flag_enabled:
            result["route_class"] = "safe_plan_helper_feature_flag_required"
            result["safe_to_call_without_mock"] = True
            result["blocked"] = False
            result["reason_labels"].append("plan_helper_with_feature_flag")
            result["confidence_label"] = "high"
            return result
        else:
            result["reason_labels"].append("plan_helper_no_feature_flag")

    # 7. Fallback — no deterministic safe path
    result["model_calls"] = True
    if mock_active:
        result["route_class"] = "requires_generate_chat_mock"
        result["requires_mock"] = True
        result["safe_to_call_without_mock"] = False
        result["blocked"] = False
        result["reason_labels"].append("mock_intercept_authorized")
        result["confidence_label"] = "high"
    else:
        result["route_class"] = "forbidden_model_path"
        result["requires_mock"] = False
        result["safe_to_call_without_mock"] = False
        result["blocked"] = True
        result["reason_labels"].append("no_safe_path_and_mock_not_active")
        result["confidence_label"] = "high"

    return result


def validate_prompt_route_alignment_v1(
    prompt_item: dict[str, Any],
    *,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Validate one controlled prompt item against routing reality.

    Returns alignment report with pass / mismatch / blocked status.
    """
    cfg = dict(config) if config else {}
    mock_active = bool(cfg.get("generate_chat_mock_active", False))

    prompt_id = str(prompt_item.get("prompt_id", "unknown"))
    family = str(prompt_item.get("family", "unknown"))
    prompt_text = str(prompt_item.get("prompt_text", ""))
    metadata = dict(prompt_item) if isinstance(prompt_item, dict) else {}

    # Route prediction
    route = predict_chat_responder_route_v1(
        prompt_text,
        metadata=metadata,
        config=cfg,
    )

    alignment_status = "aligned"
    reason_labels: list[str] = list(route.get("reason_labels", []))

    # Blocked family check — evaluated first so it overrides all metadata mismatches
    if family in BLOCKED_FAMILIES_V1:
        alignment_status = "blocked_by_boundary"
        reason_labels.append(f"blocked_family:{family}")
        route["blocked"] = True
        route["safe_to_call_without_mock"] = False
        # Skip remaining mismatch checks for blocked families
        safe_to_call = False
        return {
            "prompt_id": prompt_id,
            "family": family,
            "route_class": route["route_class"],
            "alignment_status": alignment_status,
            "safe_to_call": safe_to_call,
            "requires_mock": route["requires_mock"],
            "reason_labels": reason_labels,
        }

    # Metadata mismatch checks
    requires_model_call = bool(prompt_item.get("requires_model_call", False))
    requires_search = bool(prompt_item.get("requires_search", False))
    safety_class = str(prompt_item.get("safety_class", ""))
    requires_feature_flag = bool(prompt_item.get("requires_feature_flag", False))

    if not requires_model_call and route["route_class"] == "forbidden_model_path":
        alignment_status = "mismatch"
        reason_labels.append("metadata_requires_model_call_false_but_forbidden_path")

    if not requires_model_call and route["route_class"] == "requires_generate_chat_mock" and not mock_active:
        alignment_status = "mismatch"
        reason_labels.append("metadata_requires_model_call_false_but_mock_needed")

    if not requires_search and route["route_class"] == "forbidden_search_or_advisor_path":
        alignment_status = "mismatch"
        reason_labels.append("metadata_requires_search_false_but_search_path")

    if safety_class == "safe_synthetic" and route["route_class"] in ("forbidden_model_path", "forbidden_search_or_advisor_path", "ambiguous_needs_review"):
        alignment_status = "mismatch"
        reason_labels.append("safe_synthetic_class_but_unsafe_route")

    if requires_feature_flag and route["route_class"] != "safe_plan_helper_feature_flag_required":
        alignment_status = "mismatch"
        reason_labels.append("feature_flag_required_but_not_plan_helper_route")

    # Final safety_to_call
    safe_to_call = (
        route["safe_to_call_without_mock"]
        or (route["requires_mock"] and mock_active)
    ) and not route["blocked"]

    return {
        "prompt_id": prompt_id,
        "family": family,
        "route_class": route["route_class"],
        "alignment_status": alignment_status,
        "safe_to_call": safe_to_call,
        "requires_mock": route["requires_mock"],
        "reason_labels": reason_labels,
    }


def summarize_prompt_route_alignment_v1(
    prompt_set: dict[str, Any],
    *,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Validate an entire prompt set and produce summary statistics.

    Returns counts by route class and alignment status.
    No raw prompt text is included.
    """
    cfg = dict(config) if config else {}

    if not isinstance(prompt_set, dict):
        return {
            "total_prompts": 0,
            "safe_without_mock": 0,
            "requires_mock": 0,
            "blocked": 0,
            "ambiguous": 0,
            "metadata_mismatches": [],
            "recommended_actions": ["invalid_prompt_set"],
            "per_family_counts": {},
            "route_class_counts": {},
            "alignment_status_counts": {},
            "prompt_ids_by_status": {},
        }

    prompts = prompt_set.get("prompts", [])
    if not isinstance(prompts, list):
        prompts = []

    total_prompts = len(prompts)
    safe_without_mock = 0
    requires_mock_count = 0
    blocked_count = 0
    ambiguous_count = 0
    metadata_mismatches: list[dict[str, Any]] = []
    per_family_counts: dict[str, int] = {}
    route_class_counts: dict[str, int] = {}
    alignment_status_counts: dict[str, int] = {}
    prompt_ids_by_status: dict[str, list[str]] = {}
    recommended_actions: list[str] = []

    for item in prompts:
        if not isinstance(item, dict):
            continue
        validation = validate_prompt_route_alignment_v1(item, config=cfg)
        route_class = validation["route_class"]
        status = validation["alignment_status"]
        prompt_id = validation["prompt_id"]
        family = validation["family"]

        # Counts
        route_class_counts[route_class] = route_class_counts.get(route_class, 0) + 1
        alignment_status_counts[status] = alignment_status_counts.get(status, 0) + 1
        per_family_counts[family] = per_family_counts.get(family, 0) + 1
        prompt_ids_by_status.setdefault(status, []).append(prompt_id)

        if validation["safe_to_call"] and not validation["requires_mock"]:
            safe_without_mock += 1
        if validation["requires_mock"]:
            requires_mock_count += 1
        if status in ("blocked_by_boundary",):
            blocked_count += 1
        if route_class == "ambiguous_needs_review":
            ambiguous_count += 1
        if status == "mismatch":
            metadata_mismatches.append({
                "prompt_id": prompt_id,
                "route_class": route_class,
                "reason_labels": validation["reason_labels"],
            })

    if metadata_mismatches:
        recommended_actions.append("review_metadata_mismatches")
    if ambiguous_count > 0:
        recommended_actions.append("review_ambiguous_prompts")
    if blocked_count > 0:
        recommended_actions.append("review_blocked_families")
    if not recommended_actions:
        recommended_actions.append("prompt_set_ready")

    return {
        "total_prompts": total_prompts,
        "safe_without_mock": safe_without_mock,
        "requires_mock": requires_mock_count,
        "blocked": blocked_count,
        "ambiguous": ambiguous_count,
        "metadata_mismatches": metadata_mismatches,
        "recommended_actions": recommended_actions,
        "per_family_counts": per_family_counts,
        "route_class_counts": route_class_counts,
        "alignment_status_counts": alignment_status_counts,
        "prompt_ids_by_status": prompt_ids_by_status,
    }


def render_prompt_route_alignment_markdown_v1(
    summary: dict[str, Any],
    *,
    title: str = "Prompt Set Route Alignment Report",
) -> str:
    """Render a human-readable markdown report from summary.

    No raw prompt text. No response text. Only counts and prompt IDs.
    """
    lines = [
        f"# {title}",
        "",
        "## SECTION 1 — STATUS",
        f"- total_prompts: {summary.get('total_prompts', 0)}",
        f"- safe_without_mock: {summary.get('safe_without_mock', 0)}",
        f"- requires_mock: {summary.get('requires_mock', 0)}",
        f"- blocked: {summary.get('blocked', 0)}",
        f"- ambiguous: {summary.get('ambiguous', 0)}",
        "",
        "## SECTION 2 — ROUTE CLASS COUNTS",
    ]
    for route_class, count in sorted(summary.get("route_class_counts", {}).items()):
        lines.append(f"- {route_class}: {count}")

    lines.extend([
        "",
        "## SECTION 3 — ALIGNMENT STATUS COUNTS",
    ])
    for status, count in sorted(summary.get("alignment_status_counts", {}).items()):
        lines.append(f"- {status}: {count}")

    lines.extend([
        "",
        "## SECTION 4 — PER-FAMILY COUNTS",
    ])
    for family, count in sorted(summary.get("per_family_counts", {}).items()):
        lines.append(f"- {family}: {count}")

    lines.extend([
        "",
        "## SECTION 5 — METADATA MISMATCHES",
    ])
    mismatches = summary.get("metadata_mismatches", [])
    if mismatches:
        lines.append(f"- mismatch_count: {len(mismatches)}")
        for mm in mismatches:
            lines.append(f"  - {mm['prompt_id']}: {mm['route_class']} ({', '.join(mm['reason_labels'])})")
    else:
        lines.append("- mismatch_count: 0")

    lines.extend([
        "",
        "## SECTION 6 — PROMPT IDS BY STATUS",
    ])
    for status, ids in sorted(summary.get("prompt_ids_by_status", {}).items()):
        lines.append(f"- {status}: {len(ids)} prompt(s)")
        # Only list IDs, not text
        for pid in ids:
            lines.append(f"  - {pid}")

    lines.extend([
        "",
        "## SECTION 7 — RECOMMENDED ACTIONS",
    ])
    for action in summary.get("recommended_actions", ["no_action"]):
        lines.append(f"- {action}")

    lines.extend([
        "",
        "## SECTION 8 — SAFETY CONFIRMATION",
        "- raw_prompt_text_included: False",
        "- raw_response_text_included: False",
        "- ChatResponder_called: False",
        "- model_calls: False",
        "- search_calls: False",
        "- advisor_calls: False",
        "- writes: False",
        "",
    ])

    return "\n".join(lines) + "\n"
