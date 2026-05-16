"""WESLR Chat Responder - Conversational Response Formatter

This is the WESLR-owned conversational response layer.
It formats decision output into natural language for the operator.

IMPORTANT: This is NOT the OpenClaw adapter. This is the canonical
WESLR conversational surface, independent of any host runtime.
"""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .chat_hints import get_hints, add_hint
from .inadequacy_persistence import record_inadequacy_event
from llm_runtime import generate_inner_thought, generate_chat, provider_state, status as llm_status


def _synthesize_active_context(message: str, chat_context: Optional[List[str]], chat_hints: Optional[List[str]]) -> Dict[str, bool]:
    """Lightweight helper only. This is NOT continuity/memory. Uses request-time text and optional hints only."""
    text_pool = " ".join([message or "", " ".join(chat_context or []), " ".join(chat_hints or [])]).lower()
    def has_any(keywords):
        return any(k in text_pool for k in keywords)
    return {
        "wants_workout": has_any(["workout", "gym", "run", "exercise"]),
        "mentions_email": has_any(["email", "inbox", "reply", "send"]),
        "mentions_plan": has_any(["plan", "schedule", "afternoon", "morning"]),
        "mentions_lunch": has_any(["lunch", "eat", "food", "light meal"]),
        "prefers_concise": has_any(["concise", "brief"]) or "prefers concise" in (" ".join(chat_hints or [])).lower(),
    }



def _frontier_intelligence_shadow_requested(request: Dict[str, Any]) -> bool:
    """Return true only for explicit dev/test metadata-only shadow opt-in."""
    if request.get("frontier_intelligence_shadow") is True:
        return True
    if request.get("_frontier_intelligence_shadow") is True:
        return True
    for key in ("metadata", "request_metadata", "_identity_meta"):
        value = request.get(key)
        if isinstance(value, dict) and (
            value.get("frontier_intelligence_shadow") is True
            or value.get("_frontier_intelligence_shadow") is True
        ):
            return True
    hints = request.get("chat_hints")
    if isinstance(hints, dict) and hints.get("_frontier_intelligence_shadow") is True:
        return True
    return False


def _compact_shadow_list(value: Any, *, label: str) -> List[str]:
    if value is None:
        return [f"{label}: not_supplied"]
    if isinstance(value, (list, tuple, set)):
        items = [" ".join(str(item).split()) for item in value if str(item).strip()]
        return [f"{label}: {item}" for item in items[:5]] or [f"{label}: supplied_empty"]
    if isinstance(value, dict):
        keys = sorted(str(key) for key in value.keys())[:8]
        return [f"{label}: keys={','.join(keys) if keys else 'supplied_empty'}"]
    text = " ".join(str(value).split())
    return [f"{label}: {text[:240] if text else 'supplied_empty'}"]


def _build_frontier_intelligence_shadow_metadata(request: Dict[str, Any]) -> Dict[str, Any]:
    """Build metadata-only Frontier Intelligence dry-run preview from in-memory request data.

    This helper is intentionally non-runtime: it does not replace chat output,
    call models, write files, authorize wiring, or persist state.
    """
    try:
        from .native_response_dry_slice import build_native_response_dry_slice_v1
        from .frontier_intelligence_preview_surface import build_frontier_intelligence_preview_card_v1

        message = (request.get("message") or "").strip()
        chat_context = request.get("chat_context")
        chat_hints = request.get("chat_hints")
        identity_meta = request.get("_identity_meta")
        metadata = request.get("metadata")
        request_metadata = request.get("request_metadata")

        known_context: List[str] = ["chat_path_reply_already_computed"]
        known_context.extend(_compact_shadow_list(chat_context, label="chat_context"))
        known_context.extend(_compact_shadow_list(chat_hints, label="chat_hints"))
        known_context.extend(_compact_shadow_list(identity_meta, label="identity_meta"))
        known_context.extend(_compact_shadow_list(metadata, label="metadata"))
        known_context.extend(_compact_shadow_list(request_metadata, label="request_metadata"))

        missing_context = []
        if not chat_context:
            missing_context.append("chat_context_not_supplied")
        if not chat_hints:
            missing_context.append("chat_hints_not_supplied")
        missing_context.extend([
            "meaning_vector_result_not_supplied_to_shadow_hook",
            "response_obligation_result_not_supplied_to_shadow_hook",
            "verified_memory_context_not_loaded_by_shadow_hook",
        ])

        dry_slice = build_native_response_dry_slice_v1(
            user_message=message,
            request_summary="metadata-only chat shadow dry run; existing chat reply remains final",
            known_context=known_context,
            missing_context=missing_context,
            provenance_refs=["in_memory_chat_request", "explicit_frontier_intelligence_shadow_flag"],
            governance_safety_hints=[
                "metadata_only",
                "do_not_replace_response_content",
                "no_runtime_wiring_authorized",
                "safe_to_wire_runtime_false",
            ],
        )
        preview_card = build_frontier_intelligence_preview_card_v1(dry_slice)
        metadata_preview_card = dict(preview_card)
        metadata_preview_card["forbidden_claims_avoided"] = ["restricted_boundaries_applied"]
        return {
            "enabled": True,
            "mode": "dry_run_metadata_only",
            "dry_slice_summary": {
                "slice_id": dry_slice.get("slice_id"),
                "slice_type": dry_slice.get("slice_type"),
                "slice_status": dry_slice.get("slice_status"),
                "execution_status": dry_slice.get("execution_status"),
                "safe_to_preview": bool(dry_slice.get("safe_to_preview")),
                "safe_to_wire_runtime": False,
                "final_chat_output": False,
                "live_runtime_output": False,
                "candidate_returned_as_content": False,
                "validation_status": dry_slice.get("validation_status"),
                "side_effects": dry_slice.get("side_effects", {}),
            },
            "preview_card": metadata_preview_card,
            "preview_summary": {
                "card_id": preview_card.get("card_id"),
                "card_type": preview_card.get("card_type"),
                "response_mode": preview_card.get("response_mode"),
                "slice_status": preview_card.get("slice_status"),
                "safe_to_preview": bool(preview_card.get("safe_to_preview")),
                "safe_to_wire_runtime": False,
                "validation_status": preview_card.get("validation_status"),
            },
            "safe_to_preview": bool(preview_card.get("safe_to_preview")),
            "safe_to_wire_runtime": False,
            "final_chat_output": False,
            "live_runtime_output": False,
            "candidate_returned_as_content": False,
            "non_execution_disclaimer": "metadata_only_shadow_not_live_chat_output_not_runtime_wired",
            "validation_status": preview_card.get("validation_status") or dry_slice.get("validation_status"),
            "side_effects": {
                "model_calls": False,
                "runtime_wiring": False,
                "chat_or_voice_changes": False,
                "ui_or_frontend_integration": False,
                "cli_integration": False,
                "runner": False,
                "scoring_engine": False,
                "persistence": False,
                "weslr_runtime_state_created": False,
                "auto_approval": False,
                "auto_implementation": False,
                "prompt_specific_script": False,
            },
        }
    except Exception as exc:
        return {
            "enabled": True,
            "mode": "dry_run_metadata_only",
            "shadow_build_failed": True,
            "failure_reason": type(exc).__name__,
            "safe_to_preview": False,
            "safe_to_wire_runtime": False,
            "final_chat_output": False,
            "live_runtime_output": False,
            "candidate_returned_as_content": False,
            "non_execution_disclaimer": "metadata_only_shadow_failed_existing_chat_output_preserved",
            "validation_status": {"valid": False, "validation_status": "shadow_build_failed"},
            "side_effects": {
                "model_calls": False,
                "runtime_wiring": False,
                "chat_or_voice_changes": False,
                "ui_or_frontend_integration": False,
                "cli_integration": False,
                "runner": False,
                "scoring_engine": False,
                "persistence": False,
                "weslr_runtime_state_created": False,
                "auto_approval": False,
                "auto_implementation": False,
                "prompt_specific_script": False,
            },
        }
from .request_parser import parse_request, apply_request_to_decision
from .explanation_responder import ExplanationSession

@dataclass
class Response:
    content: str
    metadata: Optional[Dict[str, Any]] = None
    actions: Optional[List[Any]] = None

# Module-level session for adaptive explanation (presentation-only)
_EXPLANATION_SESSION: Optional[ExplanationSession] = None
_EXPLANATION_CTX = {"persona": None, "domain": None}

_LIMITED_FRONTIER_RUNTIME_SCOPE = "limited_state_grounded_context_sufficiency"
_ORDINARY_TASK_RUNTIME_SCOPE = "limited_ordinary_task_context_sufficiency"


def _limited_frontier_chat_metadata(
    *,
    eligible: bool,
    reason: str,
    category: str = "none",
    source: str = "native_response_dry_slice/native_reasoning_frame/native_response_draft/native_response_self_check/native_response_assembly",
    validation_status: Optional[Dict[str, Any]] = None,
    fallback_used: bool = False,
) -> Dict[str, Any]:
    """Safe metadata for the narrow Frontier Intelligence live-chat slice.

    This is not a proposal, preflight, governance queue, or broad runtime wiring.
    It marks only the bounded chat integration path used for state/context
    sufficiency answers.
    """
    return {
        "eligible": bool(eligible),
        "reason": reason,
        "category": category,
        "source": source,
        "validation_status": validation_status or {"valid": True, "validation_status": "not_required"},
        "runtime_scope": _LIMITED_FRONTIER_RUNTIME_SCOPE,
        "limited_runtime_response": bool(eligible and not fallback_used),
        "safe_to_wire_runtime": False,
        "fallback_used": bool(fallback_used),
        "official_claims_blocked": True,
        "fake_memory_blocked": True,
        "unsupported_capability_blocked": True,
        "side_effects": {
            "model_calls": False,
            "runtime_wiring": False,
            "chat_or_voice_changes": False,
            "ui_or_frontend_integration": False,
            "cli_integration": False,
            "runner": False,
            "scoring_engine": False,
            "persistence": False,
            "weslr_runtime_state_created": False,
            "auto_approval": False,
            "auto_implementation": False,
            "prompt_specific_script": False,
        },
    }


def _classify_limited_frontier_chat_request(message: str) -> Dict[str, Any]:
    """Classify the small set of live-chat requests this slice may answer.

    The categories are intentionally broad semantic gates, not prompt-specific
    response scripts. Anything outside these safe classes stays on the existing
    chat path.
    """
    text = " ".join((message or "").lower().split())
    if not text:
        return {"eligible": False, "category": "empty", "reason": "empty_message"}

    official_boundary = (
        "official iq",
        "iq benchmark",
        "iq score",
        "official benchmark",
        "official score",
        "official test score",
        "certification",
        "certified",
        "are you certified",
    )
    protected_terms = ("answer key", "hidden prompt", "protected test", "private test item")
    mystical_boundary = (
        "are you conscious",
        "are you sentient",
        "are you alive",
        "do you have a soul",
        "mystical consciousness",
        "officially conscious",
    )
    high_stakes_terms = ("medical", "legal", "financial", "diagnose", "prescription", "lawsuit", "investment")
    external_terms = ("search the web", "fetch", "look up", "current price", "today's news", "latest study", "latest research", "latest news")

    investment_boundary = "investment" in text and not any(benign in text for benign in ("investment of time", "time investment"))

    if any(term in text for term in official_boundary):
        return {"eligible": True, "category": "official_claim_boundary", "reason": "official_claim_boundary"}
    if any(term in text for term in protected_terms):
        return {"eligible": True, "category": "protected_material_boundary", "reason": "protected_material_boundary"}
    if any(term in text for term in mystical_boundary):
        return {"eligible": True, "category": "identity_boundary", "reason": "mystical_claim_boundary"}
    if any(term in text for term in tuple(t for t in high_stakes_terms if t != "investment") + external_terms) or investment_boundary:
        return {"eligible": True, "category": "context_sufficiency", "reason": "external_or_high_stakes_evidence_required"}

    identity_terms = ("what are you", "who are you", "what is weslr", "describe yourself", "your identity")
    memory_terms = ("remember me", "do you remember", "what do you remember", "memory of me", "know about me")
    capability_terms = ("can we build", "can you build", "can weslr build", "what can you do", "can you help build", "are you able to")
    missing_context_terms = ("is this enough context", "need more context", "what context", "missing context", "not enough context")
    state_terms = ("what do you know", "what modules", "what state", "what evidence", "what do you have")

    for category, terms in (
        ("identity", identity_terms),
        ("memory_boundary", memory_terms),
        ("capability_boundary", capability_terms),
        ("context_sufficiency", missing_context_terms),
        ("state_grounded", state_terms),
    ):
        if any(term in text for term in terms):
            return {"eligible": True, "category": category, "reason": f"matched_{category}"}

    return {"eligible": False, "category": "ordinary_chat", "reason": "outside_limited_runtime_scope"}


def _build_limited_frontier_known_and_missing(
    category: str,
    message: str,
    chat_context: Optional[List[str]],
    chat_hints: Optional[List[str]],
    identity_meta: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    known = [
        "WESLR identity: operational WESLR chat surface",
        "runtime boundary: limited state-grounded context-sufficiency response only",
        "safety boundary: no model call, no tool execution, no persistence, no approval",
    ]
    missing: List[str] = []
    capability_boundary: Dict[str, Any] = {
        "can_explain": True,
        "can_propose": True,
        "can_analyze": True,
        "can_prepare": True,
        "requires_tool": False,
        "requires_approval": False,
        "cannot_claim": [
            "official benchmark, IQ, or certification result",
            "protected test access, hidden prompt, or answer key",
            "mystical consciousness or sentience",
            "memory not supplied by context",
            "implementation or approval already granted",
        ],
    }
    evidence_status: Dict[str, Any] = {"status": "sufficient", "evidence_required": False}

    if chat_context:
        known.append("request supplied chat_context")
    if chat_hints:
        known.append("request supplied chat_hints")
    if identity_meta:
        known.append("request supplied identity metadata")

    if category == "identity":
        known.append("stable identity answer can be bounded to WESLR operational role")
    elif category == "memory_boundary":
        known.append("memory answer must use only supplied context or explicit memory sources")
        if not chat_context and not chat_hints:
            missing.append("verified memory context for this request")
    elif category == "capability_boundary":
        known.append("capability answer can describe analysis/proposal support without claiming execution")
        missing.append("implementation requirements, target environment, and approval state")
    elif category == "context_sufficiency":
        known.append("request appears to require bounded answer before stronger claim")
        normalized_message = " ".join((message or "").lower().split())
        if any(term in normalized_message for term in ("latest", "current", "research", "study", "news", "today")):
            missing.append("current sources or evidence")
        elif any(term in normalized_message for term in ("legal", "lawsuit", "contract clause")):
            missing.append("professional legal review and clause-specific context")
        elif any(term in normalized_message for term in ("medical", "diagnose", "prescription")):
            missing.append("professional medical review and case-specific context")
        elif any(term in normalized_message for term in ("financial", "investment")):
            missing.append("professional financial review and decision-specific context")
        else:
            missing.append("task-specific evidence or user-provided constraints")
        evidence_status = {"status": "requires_evidence", "evidence_required": True, "needed": missing}
    elif category == "state_grounded":
        known.append("state answer can summarize only available/request-supplied state boundaries")
        missing.append("specific state source or module scope")
    elif category in {"official_claim_boundary", "protected_material_boundary", "identity_boundary"}:
        known.append("safety boundary request detected")
        missing.append("permitted public evidence for any stronger claim")
        evidence_status = {"status": "requires_evidence", "evidence_required": True, "needed": missing}

    return {
        "known_context": known,
        "missing_context": missing,
        "capability_boundary_result": capability_boundary,
        "evidence_sufficiency_result": evidence_status,
        "self_model_or_identity_status": {
            "status": "stable_weslr_operational_identity",
            "identity": "WESLR",
            "boundary": "operational system identity with non-mystical authority boundaries",
        },
        "memory_context_hints": chat_hints or [],
        "request_summary": f"limited Frontier Intelligence chat classification: {category}",
    }


def _limited_state_items(value: Any) -> List[str]:
    """Return compact display-safe state items for limited live composition."""
    if value is None:
        return []
    if isinstance(value, list):
        raw = value
    elif isinstance(value, tuple):
        raw = list(value)
    elif isinstance(value, set):
        raw = sorted(value, key=repr)
    else:
        raw = [value]

    items: List[str] = []
    for item in raw:
        if isinstance(item, dict):
            for key in ("summary", "status", "identity", "boundary", "recommended_action", "safe_next_step"):
                if item.get(key):
                    items.append(str(item[key]))
                    break
        else:
            items.append(str(item))
    return [" ".join(item.replace("_", " ").split()) for item in items if str(item).strip()]


def _limited_strip_note_prefix(item: str) -> str:
    text = " ".join(str(item).replace("_", " ").split())
    for prefix in ("clarify:", "needed:", "context status:", "evidence status:", "cannot do yet:"):
        if text.lower().startswith(prefix):
            text = text[len(prefix):].strip()
    return text


def _limited_add_section(lines: List[str], used: List[str], name: str, values: Any, *, limit: int = 2) -> None:
    items = [_limited_strip_note_prefix(item) for item in _limited_state_items(values)]
    items = [item for item in items if item]
    if not items:
        return
    lines.append(f"{name}: {'; '.join(items[:limit])}.")
    used.append(name.lower().replace(" ", "_"))


def _limited_join_items(items: List[str], *, limit: int = 3) -> str:
    cleaned = [_limited_strip_note_prefix(item) for item in items if _limited_strip_note_prefix(item)]
    selected = cleaned[:limit]
    if not selected:
        return ""
    if len(selected) == 1:
        return selected[0]
    if len(selected) == 2:
        return f"{selected[0]} and {selected[1]}"
    return f"{', '.join(selected[:-1])}, and {selected[-1]}"


def _limited_add_sentence(lines: List[str], used: List[str], section: str, sentence: str) -> None:
    text = " ".join(str(sentence).split())
    if not text:
        return
    if text[-1] not in ".!?":
        text += "."
    lines.append(text)
    used.append(section)


def _limited_material_evidence_required(category: str, context_sufficiency: Dict[str, Any], evidence_status: Dict[str, Any]) -> bool:
    return (
        bool(evidence_status.get("evidence_required"))
        or context_sufficiency.get("status") == "requires_evidence"
        or category in {"official_claim_boundary", "protected_material_boundary"}
    )


def _limited_refined_next_step(category: str, missing_items: List[str], raw_next_step: List[str]) -> str:
    missing = _limited_join_items(missing_items, limit=3)
    generic = " ".join(raw_next_step).lower()
    if category == "capability_boundary" and missing:
        return f"The useful next step is to provide {missing} before treating this as implementable"
    if category == "context_sufficiency" and missing:
        lowered = missing.lower()
        if "current sources or evidence" in lowered:
            return "Use those sources before treating the answer as current"
        if "professional legal review" in lowered:
            return "Use that review before treating any clause choice as actionable"
        if "professional medical review" in lowered or "professional financial review" in lowered:
            return "Use that review before treating the answer as actionable"
        return f"To answer safely, provide {missing} or narrow the question to one concrete decision"
    if category == "official_claim_boundary":
        return "The safe next step is an evidence-backed internal evaluation, not an official score or certification claim"
    if category == "protected_material_boundary":
        return "The safe next step is to use public, supplied, or repo-visible evidence instead"
    if category == "memory_boundary" and missing:
        return f"Provide a memory source or context if you want me to use one"
    if raw_next_step and generic not in {"answer with available context", "answer with boundary or ask clarifying question", "ask clarifying question"}:
        return _limited_join_items(raw_next_step, limit=1)
    return ""

def _limited_composed_response_is_safe(text: str) -> bool:
    lowered = (text or "").lower()
    forbidden_claim_fragments = (
        "i remember you",
        "i remember our",
        "my iq is",
        "i am certified",
        "officially certified",
        "i am conscious",
        "i am sentient",
        "i am alive",
        "i have a soul",
        "already implemented",
        "implementation exists",
        "approval granted",
        "auto-approved",
        "here is the hidden prompt",
        "the answer key is",
        "runtime wiring authorized",
    )
    return bool(text and len(text.split()) >= 8 and not any(fragment in lowered for fragment in forbidden_claim_fragments))




def _ordinary_task_has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _classify_limited_ordinary_task_request(message: str) -> Dict[str, Any]:
    """Classify one narrow ordinary-task slice without replacing general chat."""
    text = " ".join((message or "").lower().split())
    if not text:
        return {"eligible": False, "decision": "fallback_existing_path", "reason": "empty_message"}

    blocked_terms = (
        "official iq", "official benchmark", "certification", "certified", "answer key",
        "hidden prompt", "protected test", "are you conscious", "are you sentient", "medical",
        "legal", "financial", "diagnose", "prescription", "lawsuit", "investment",
        "remember me", "do you remember", "write a story", "poem", "creative writing",
    )
    if _ordinary_task_has_any(text, blocked_terms):
        return {"eligible": False, "decision": "fallback_existing_path", "reason": "outside_safe_ordinary_scope"}

    current_terms = ("current", "latest", "recent", "today", "source", "sources", "cite", "look up", "search", "news")
    benign_latest_exclusions = ("latest lunch", "recent lunch", "current lunch")
    if _ordinary_task_has_any(text, current_terms) and not _ordinary_task_has_any(text, benign_latest_exclusions):
        return {
            "eligible": True,
            "decision": "external_evidence_needed",
            "reason": "current_or_source_evidence_requested",
            "missing_context": ["current external evidence or supplied sources"],
        }

    tool_terms = ("calculate", "compute", "measure", "run a calculation", "use a tool", "exact total", "how many")
    if _ordinary_task_has_any(text, tool_terms):
        return {
            "eligible": True,
            "decision": "tool_or_calculation_needed",
            "reason": "tool_or_calculation_needed",
            "missing_context": ["calculation inputs or tool output"],
        }

    planning_terms = (
        "plan", "steps", "step plan", "rollout", "checklist", "break down", "debug", "organize",
        "migration", "deployment", "deploy", "staged change", "server change",
    )
    if not _ordinary_task_has_any(text, planning_terms):
        return {"eligible": False, "decision": "fallback_existing_path", "reason": "not_an_ordinary_task_slice"}

    too_vague_terms = ("plan this", "help me plan", "make a plan", "what should i do")
    has_supplied_context = len([token for token in text.split() if len(token) > 3]) >= 5
    if _ordinary_task_has_any(text, too_vague_terms) and not has_supplied_context:
        return {
            "eligible": True,
            "decision": "ask_clarifying_question",
            "reason": "missing_task_goal",
            "missing_context": ["the concrete task or desired outcome"],
        }

    constraints = _ordinary_task_extract_constraints(text)
    explicit_sequence = _ordinary_task_extract_sequence_markers(text)
    complex_terms = (
        "rollout", "debug", "break down", "checklist", "step plan", "migration", "deployment",
        "deploy", "staged change", "server change", "rollback", "monitoring",
    )
    if any(term in text for term in complex_terms) or explicit_sequence:
        return {
            "eligible": True,
            "decision": "bounded_step_plan",
            "reason": "safe_complex_ordinary_task",
            "constraints": constraints,
            "sequence_constraints": explicit_sequence,
            "plan_focus": _ordinary_task_plan_focus(text),
            "missing_context": [] if (constraints or explicit_sequence) else ["success criteria or constraints"],
        }

    return {
        "eligible": True,
        "decision": "answer_with_available_context",
        "reason": "safe_simple_ordinary_planning_task",
        "constraints": constraints,
        "sequence_constraints": explicit_sequence,
        "plan_focus": _ordinary_task_plan_focus(text),
        "missing_context": [],
    }


def _ordinary_task_side_effects() -> Dict[str, bool]:
    return {
        "model_calls": False,
        "runtime_wiring": False,
        "chat_or_voice_changes": False,
        "ui_or_frontend_integration": False,
        "cli_integration": False,
        "runner": False,
        "scoring_engine": False,
        "persistence": False,
        "weslr_runtime_state_created": False,
        "auto_approval": False,
        "auto_implementation": False,
        "prompt_specific_script": False,
    }


_ORDINARY_MARKER_PHRASES = {
    "target_environment": "which environment this applies to",
    "success_criteria": "what success should look like",
    "success_criteria_or_constraints": "what success should look like or which constraints matter",
    "rollback_trigger": "when to roll back",
    "monitoring_signal": "what to monitor after the change",
    "test_scope": "which tests are in scope",
    "staging_target": "where staging happens",
    "commit_policy": "when the commit should be made",
    "failure_signal": "what failure you are seeing",
    "expected_behavior": "what should have happened",
    "reproduction_steps": "how to reproduce it",
    "concrete_task_or_desired_outcome": "the concrete task or desired outcome",
    "the_concrete_task_or_desired_outcome": "the concrete task or desired outcome",
    "calculation_inputs": "the calculation inputs",
    "calculation_inputs_or_tool_output": "the calculation inputs or tool output",
    "formula_or_method": "the formula or method to use",
    "current_external_evidence_or_supplied_sources": "current evidence or supplied sources",
}

_ORDINARY_RISK_BOUNDARY_PHRASES = {
    "no_execution_performed": "I have not run anything",
    "requires_verification_before_execution": "verify this before using it as an execution plan",
    "rollback_needed_before_change": "define rollback before making the change",
    "monitoring_needed_after_change": "decide what to monitor after the change",
    "tool_required_before_exact_result": "run the calculation path before relying on an exact result",
    "external_evidence_required_before_current_claim": "use current sources before making a current claim",
}


def _ordinary_task_marker_phrase(item: Any) -> str:
    marker = "_".join(str(item).lower().replace("/", " ").split())
    return _ORDINARY_MARKER_PHRASES.get(marker, " ".join(str(item).replace("_", " ").split()))


def _ordinary_task_natural_join(items: List[Any], *, limit: int = 3) -> str:
    return _limited_join_items([_ordinary_task_marker_phrase(item) for item in items], limit=limit)


def _ordinary_task_risk_boundary_text(risk_boundaries: List[str]) -> str:
    phrases = []
    for marker in risk_boundaries:
        phrase = _ORDINARY_RISK_BOUNDARY_PHRASES.get(marker)
        if phrase and phrase not in phrases:
            phrases.append(phrase)
    return "; ".join(phrases[:4])


def _ordinary_task_relevant_unknowns(plan_focus: str, unknowns: List[str]) -> List[str]:
    preferred_by_focus = {
        "migration": ["target_environment", "success_criteria", "rollback_trigger", "monitoring_signal"],
        "rollout": ["test_scope", "staging_target", "commit_policy"],
        "debug": ["failure_signal", "expected_behavior", "reproduction_steps", "success_criteria"],
        "checklist": ["failure_signal", "expected_behavior", "reproduction_steps", "success_criteria"],
    }
    preferred = preferred_by_focus.get(plan_focus, [])
    selected = [marker for marker in preferred if marker in unknowns]
    if selected:
        return selected
    if plan_focus == "rollout" and "success_criteria" in unknowns:
        return ["success_criteria"]
    return [marker for marker in unknowns if marker != "concrete_task_or_desired_outcome"][:3]


def _ordinary_task_unknown_note(plan_focus: str, unknowns: List[str]) -> str:
    relevant = _ordinary_task_relevant_unknowns(plan_focus, unknowns)
    if not relevant:
        return ""
    missing = _ordinary_task_natural_join(relevant, limit=4)
    if plan_focus == "rollout" and any(marker in relevant for marker in ("test_scope", "staging_target", "commit_policy")):
        return f"Before treating the rollout as ready, confirm {missing}"
    if plan_focus == "migration":
        return f"Before executing it, clarify {missing}"
    if plan_focus == "debug":
        return f"Before treating this as executable, clarify {missing}"
    return f"Before treating this as executable, clarify {missing}"


def _ordinary_task_question_for_missing(missing_context: List[str]) -> str:
    missing = _ordinary_task_natural_join(missing_context, limit=1) or "the concrete task or desired outcome"
    return f"What is {missing}?"


def _ordinary_task_extract_constraints(text: str) -> List[str]:
    constraints: List[str] = []
    markers = {
        "rollback": ("rollback", "roll back"),
        "monitoring": ("monitoring", "monitor"),
        "deadline": ("deadline",),
        "budget": ("budget",),
        "safe": ("safe", "safely"),
        "small": ("small", "limited"),
        "tests": ("test", "tests", "pytest"),
        "stage": ("stage", "staging"),
        "commit": ("commit",),
    }
    for label, terms in markers.items():
        if any(term in text for term in terms):
            constraints.append(label)
    return constraints


def _ordinary_task_extract_sequence_markers(text: str) -> List[str]:
    sequence: List[str] = []
    sequence_terms = (
        ("tests", ("run tests", "first run tests", "test first", "tests")),
        ("stage", ("then stage", "stage", "staging")),
        ("commit", ("then commit", "commit")),
    )
    for label, terms in sequence_terms:
        if any(term in text for term in terms):
            sequence.append(label)
    return sequence


def _ordinary_task_plan_focus(text: str) -> str:
    if "migration" in text or "server change" in text:
        return "migration"
    if "rollout" in text or "deploy" in text or "deployment" in text:
        return "rollout"
    if "debug" in text:
        return "debug"
    if "checklist" in text:
        return "checklist"
    return "planning"


def _ordinary_task_checklist_requested(text: str) -> bool:
    return "checklist" in text or "check list" in text


def _ordinary_task_sequence_steps(sequence_constraints: List[str]) -> List[str]:
    sequence_step_text = {
        "tests": "Run the tests first and treat failures as a pause signal, not a finished rollout.",
        "stage": "Stage the change only after the test step is acceptable.",
        "commit": "Commit only after the staged change matches the intended small scope.",
    }
    return [sequence_step_text[label] for label in sequence_constraints if label in sequence_step_text]


def _ordinary_task_step_plan(
    message: str,
    constraints: List[str],
    sequence_constraints: Optional[List[str]] = None,
    plan_focus: str = "planning",
) -> List[str]:
    text = " ".join((message or "").lower().split())
    sequence = list(sequence_constraints or [])
    if sequence:
        plan = _ordinary_task_sequence_steps(sequence)
    elif plan_focus == "migration":
        plan = [
            "Define the migration scope and the smallest reversible server change.",
            "Run the smallest safe check before treating the migration plan as executable.",
            "Decide what result means continue, pause, or adjust.",
        ]
    elif plan_focus == "rollout":
        plan = [
            "Keep the rollout bounded to the supplied change before expanding scope.",
            "Run the smallest safe check before treating the rollout plan as executable.",
            "Decide what result means continue, pause, or adjust.",
        ]
    elif plan_focus == "debug":
        plan = [
            "Capture the failing symptom and the exact command or input that triggers it.",
            "Isolate the smallest reproducible case before changing code.",
            "Change one likely cause at a time and re-check the same symptom.",
        ]
    else:
        plan = [
            "Restate the target outcome and the constraint that matters most.",
            "Run the smallest safe check before treating the plan as executable.",
            "Decide what result means continue, pause, or adjust.",
        ]

    # Append explicit operational constraints after the core plan so none are lost
    # behind a fixed display cap. These are normalized markers, not raw prompt text.
    if "rollback" in constraints:
        plan.append("Keep the rollback path explicit before changing the wider system.")
    if "monitoring" in constraints:
        plan.append("Watch the monitoring signal that would show the change is going wrong early.")
    if "safe" in constraints and not any("safe" in step.lower() for step in plan):
        plan.append("Keep each step safe and reversible until the result is known.")
    if "small" in constraints and not any("small" in step.lower() or "bounded" in step.lower() for step in plan):
        plan.append("Keep the first pass small enough to review before expanding scope.")
    if _ordinary_task_checklist_requested(text) and not any("check" in step.lower() for step in plan):
        plan.append("Check each item before moving to the next one.")
    return plan


def _build_ordinary_problem_decomposition_v1(
    *,
    decision: str,
    message: str,
    missing_context: List[str],
    constraints: List[str],
    sequence_constraints: Optional[List[str]],
    plan_focus: str,
    evidence_needed: bool,
    tool_needed: bool,
) -> Dict[str, Any]:
    """Build a normalized, in-memory decomposition for safe ordinary tasks.

    This intentionally stores markers and bounded step text only; it does not
    persist raw prompt text, execute solvers, select answers, call models, or
    authorize runtime wiring.
    """
    text = " ".join((message or "").lower().split())
    sequence = list(sequence_constraints or [])
    constraint_set = set(constraints or [])
    reversible_steps = _ordinary_task_step_plan(message, constraints, sequence, plan_focus) if decision == "bounded_step_plan" else []

    def add_unique(items: List[str], marker: str) -> None:
        if marker and marker not in items:
            items.append(marker)

    knowns: List[str] = []
    unknowns: List[str] = []
    risk_boundaries: List[str] = [
        "no_execution_performed",
        "no_approval_claim",
        "bounded_by_supplied_context",
        "requires_verification_before_execution",
        "no_solver_authority",
        "no_answer_selection",
        "no_private_text_storage",
    ]

    if plan_focus:
        add_unique(knowns, f"plan_focus:{plan_focus}")
    if "small" in constraint_set or "small python helper" in text or "small code" in text:
        add_unique(knowns, "small_code_change")
    if plan_focus == "migration" or "server change" in text or "migration" in text:
        add_unique(knowns, "server_change_requested")
        add_unique(knowns, "migration_plan_requested")
        for marker in ("target_environment", "success_criteria", "rollback_trigger", "monitoring_signal"):
            add_unique(unknowns, marker)
    if plan_focus == "rollout" or "rollout" in text:
        add_unique(knowns, "rollout_plan_requested")
    if "rollback" in constraint_set:
        add_unique(knowns, "rollback_required")
        add_unique(risk_boundaries, "rollback_needed_before_change")
    if "monitoring" in constraint_set:
        add_unique(knowns, "monitoring_required")
        add_unique(risk_boundaries, "monitoring_needed_after_change")
    if sequence:
        add_unique(knowns, "ordered_rollout_sequence_supplied")
        for marker in ("test_scope", "staging_target", "commit_policy"):
            add_unique(unknowns, marker)
    if plan_focus == "debug" or _ordinary_task_checklist_requested(text):
        add_unique(knowns, "debug_checklist_requested" if plan_focus == "debug" else "checklist_requested")
        for marker in ("failure_signal", "expected_behavior", "reproduction_steps"):
            add_unique(unknowns, marker)
    if decision == "ask_clarifying_question":
        add_unique(unknowns, "concrete_task_or_desired_outcome")
    if evidence_needed:
        add_unique(knowns, "current_or_external_evidence_requested")
        add_unique(unknowns, "current_external_evidence_or_supplied_sources")
        add_unique(risk_boundaries, "external_evidence_required_before_current_claim")
    if tool_needed:
        add_unique(knowns, "calculation_requested_but_inputs_missing")
        add_unique(unknowns, "calculation_inputs")
        add_unique(unknowns, "formula_or_method")
        add_unique(risk_boundaries, "tool_required_before_exact_result")
    for marker in missing_context or []:
        normalized = "_".join(str(marker).lower().replace("/", " ").split())
        if normalized in {"the_concrete_task_or_desired_outcome", "concrete_task_or_desired_outcome"}:
            add_unique(unknowns, "concrete_task_or_desired_outcome")
        elif normalized in {"success_criteria_or_constraints", "success_criteria"}:
            add_unique(unknowns, "success_criteria")
        elif normalized in {"calculation_inputs_or_tool_output", "calculation_inputs"}:
            add_unique(unknowns, "calculation_inputs")
        elif normalized in {"current_external_evidence_or_supplied_sources"}:
            add_unique(unknowns, "current_external_evidence_or_supplied_sources")
        elif normalized:
            add_unique(unknowns, normalized[:80])

    if not knowns:
        add_unique(knowns, "ordinary_task_requested")
    if decision == "ask_clarifying_question":
        safe_next_step = "name_the_concrete_task_or_desired_outcome"
    elif tool_needed:
        safe_next_step = "provide_price_tax_usage_and_formula_or_method_before_calculation"
    elif evidence_needed:
        safe_next_step = "provide_current_sources_or_use_evidence_path_before_claim"
    elif plan_focus == "migration":
        safe_next_step = "identify_target_environment_rollback_trigger_and_monitoring_signal"
    elif plan_focus == "debug":
        safe_next_step = "provide_failure_signal_expected_behavior_and_reproduction_steps"
    elif sequence:
        safe_next_step = "confirm_test_scope_and_staging_target_before_commit"
    elif reversible_steps:
        safe_next_step = "review_first_reversible_step_before_execution"
    else:
        safe_next_step = "use_available_context_and_keep_answer_bounded"

    return {
        "decomposition_type": "ordinary_problem_decomposition_v1",
        "decision": decision,
        "task_focus": plan_focus,
        "requested_outcome": f"ordinary_{plan_focus}_support",
        "knowns": knowns,
        "unknowns": unknowns,
        "constraints": list(constraints or []),
        "risk_boundaries": risk_boundaries,
        "reversible_steps": reversible_steps,
        "evidence_needed": bool(evidence_needed),
        "tool_or_calculation_needed": bool(tool_needed),
        "safe_next_step": safe_next_step,
        "trace_summary": {
            "derived_from": "normalized_ordinary_task_markers_only",
            "has_constraints": bool(constraints),
            "has_sequence": bool(sequence),
            "step_count": len(reversible_steps),
        },
        "source_modules": [
            "chat_responder_limited_ordinary_task_slice",
            "evidence_needed_detector",
            "native_response_dry_slice",
            "native_reasoning_frame",
        ],
        "side_effects": _ordinary_task_side_effects(),
        "safe_to_wire_runtime": False,
        "raw_text_stored": False,
        "solver_execution": False,
        "answer_selection": False,
    }


def _render_limited_ordinary_task_response(
    decision: str,
    *,
    message: str,
    missing_context: List[str],
    constraints: List[str],
    frame: Dict[str, Any],
    sequence_constraints: Optional[List[str]] = None,
    plan_focus: str = "planning",
    decomposition: Optional[Dict[str, Any]] = None,
) -> tuple[str, bool]:
    decomposition = decomposition if isinstance(decomposition, dict) else {}
    if decision == "ask_clarifying_question":
        unknowns = list(decomposition.get("unknowns") or missing_context)
        if "concrete_task_or_desired_outcome" in unknowns:
            unknowns = ["the concrete task or desired outcome"]
        return _ordinary_task_question_for_missing(unknowns), False
    if decision == "external_evidence_needed":
        missing = _ordinary_task_natural_join(missing_context, limit=1) or "current evidence"
        return f"I need {missing} before making that claim. I have not checked live sources here, so the bounded next step is to provide a current source or use the existing evidence path.", False
    if decision == "tool_or_calculation_needed":
        missing = _ordinary_task_natural_join(missing_context, limit=1) or "the calculation inputs"
        return f"This needs {missing} before I can answer precisely. I have not run a tool or calculation here; provide the inputs or run the tool path first.", False
    if decision == "bounded_step_plan":
        steps = list(decomposition.get("reversible_steps") or _ordinary_task_step_plan(message, constraints, list(sequence_constraints or []), plan_focus))
        constraint_values = list(decomposition.get("constraints") or constraints)
        constraint_text = _limited_join_items(constraint_values, limit=6)
        prefix = f"Within the supplied {plan_focus} context"
        if constraint_text:
            prefix += f" and the constraint signal around {constraint_text}"
        checklist_requested = _ordinary_task_checklist_requested(" ".join((message or "").lower().split()))
        if checklist_requested:
            text = prefix + ":\n" + "\n".join(f"- [ ] {step}" for step in steps)
        else:
            text = prefix + ": " + " ".join(f"{idx}) {step}" for idx, step in enumerate(steps, 1))
        unknown_note = _ordinary_task_unknown_note(plan_focus, list(decomposition.get("unknowns") or missing_context))
        if unknown_note:
            if checklist_requested:
                text += f"\n- [ ] {unknown_note}."
            else:
                text += f" {unknown_note}."
        boundary = _ordinary_task_risk_boundary_text(list(decomposition.get("risk_boundaries") or []))
        if boundary:
            if checklist_requested:
                text += f"\nNote: {boundary}."
            else:
                text += f" Boundary: {boundary}."
        return text, True
    safe_next = decomposition.get("safe_next_step") or frame.get("safe_next_step") or "use the available context and keep the answer bounded"
    return f"Within the supplied context, the useful next move is to {str(safe_next).replace('_', ' ')}. I am not using external evidence or tools for this answer.", False


def _try_limited_ordinary_task_runtime_response(
    message: str,
    chat_context: Optional[List[str]],
    chat_hints: Optional[List[str]],
    identity_meta: Optional[Dict[str, Any]],
) -> Optional[tuple[str, Dict[str, Any]]]:
    classification = _classify_limited_ordinary_task_request(message)
    if not classification.get("eligible"):
        return None

    try:
        from .native_response_dry_slice import build_native_response_dry_slice_v1
        from .evidence_needed_detector import classify_evidence_need

        decision = str(classification.get("decision") or "fallback_existing_path")
        missing_context = list(classification.get("missing_context") or [])
        constraints = list(classification.get("constraints") or [])
        sequence_constraints = list(classification.get("sequence_constraints") or [])
        plan_focus = str(classification.get("plan_focus") or "planning")
        evidence_classification = classify_evidence_need(message)
        evidence_needed = decision == "external_evidence_needed" or bool(evidence_classification.get("evidence_needed"))
        tool_needed = decision == "tool_or_calculation_needed"
        known_context = [
            "ordinary task runtime scope: limited context sufficiency and step planning only",
            "no model call, no tool execution, no persistence, no approval",
        ]
        if chat_context:
            known_context.append("request supplied chat_context")
        if chat_hints:
            known_context.append("request supplied chat_hints")
        if constraints:
            known_context.append("request supplied ordinary-task constraints")
        if sequence_constraints:
            known_context.append("request supplied sequence constraints")

        decomposition = _build_ordinary_problem_decomposition_v1(
            decision=decision,
            message=message,
            missing_context=missing_context,
            constraints=constraints,
            sequence_constraints=sequence_constraints,
            plan_focus=plan_focus,
            evidence_needed=evidence_needed,
            tool_needed=tool_needed,
        )

        dry_slice = build_native_response_dry_slice_v1(
            user_message=message,
            request_summary=f"limited ordinary task runtime decision: {decision}",
            known_context=known_context,
            missing_context=missing_context,
            memory_context_hints=chat_hints or [],
            evidence_sufficiency_result={
                "status": "requires_evidence" if evidence_needed else "sufficient",
                "evidence_required": evidence_needed,
                "requires_evidence": evidence_needed,
                "needed": missing_context if evidence_needed else [],
            },
            capability_boundary_result={
                "can_explain": True,
                "can_analyze": True,
                "can_propose": True,
                "can_prepare": True,
                "requires_tool": tool_needed,
                "requires_external_evidence": evidence_needed,
                "requires_approval": False,
                "cannot_claim": [
                    "external evidence checked when it was not checked",
                    "tool or calculation run when it was not run",
                    "memory not supplied by context",
                    "implementation or approval already granted",
                ],
            },
            uncertainty_result={"status": "bounded_by_supplied_context", "requires_clarification": decision == "ask_clarifying_question"},
            task_problem_decomposition_result=decomposition,
            provenance_refs=["live_chat_request", "limited_ordinary_task_runtime_gate"],
            governance_safety_hints=[
                "limited_ordinary_task_runtime_only",
                "safe_to_wire_runtime_false_for_broader_pipeline",
                "no_model_call_no_persistence_no_approval",
            ],
        )
        validation = dry_slice.get("validation_status", {}) if isinstance(dry_slice, dict) else {}
        self_check = dry_slice.get("self_check", {}) if isinstance(dry_slice, dict) else {}
        if validation.get("valid") is not True or self_check.get("self_check_status") in {"blocked", "revision_required"}:
            return None
        frame = dry_slice.get("frame", {}) if isinstance(dry_slice.get("frame"), dict) else {}
        content, step_plan_used = _render_limited_ordinary_task_response(
            decision,
            message=message,
            missing_context=missing_context,
            constraints=constraints,
            frame=frame,
            sequence_constraints=sequence_constraints,
            plan_focus=plan_focus,
            decomposition=decomposition,
        )
        if not _limited_composed_response_is_safe(content):
            return None
        metadata = {
            "eligible": True,
            "decision": decision,
            "problem_decomposition_used": True,
            "knowns": decomposition.get("knowns", []),
            "unknowns": decomposition.get("unknowns", []),
            "missing_context": missing_context,
            "evidence_needed": evidence_needed,
            "tool_or_calculation_needed": tool_needed,
            "safe_next_step": decomposition.get("safe_next_step"),
            "step_plan_used": step_plan_used,
            "constraints_detected": constraints,
            "risk_boundaries": decomposition.get("risk_boundaries", []),
            "plan_focus": plan_focus,
            "composition_mode": "native_state_derived_ordinary_task_composition",
            "runtime_scope": _ORDINARY_TASK_RUNTIME_SCOPE,
            "safe_to_wire_runtime": False,
            "solver_execution": False,
            "answer_selection": False,
            "raw_text_stored": False,
            "fallback_used": False,
            "source_modules": [
                "native_response_dry_slice",
                "native_reasoning_frame",
                "evidence_needed_detector",
                "chat_responder_limited_ordinary_task_slice",
            ],
            "side_effects": _ordinary_task_side_effects(),
            "validation_status": validation,
            "dry_slice_summary": {
                "slice_type": dry_slice.get("slice_type"),
                "slice_status": dry_slice.get("slice_status"),
                "execution_status": dry_slice.get("execution_status"),
                "safe_to_wire_runtime": False,
                "final_chat_output": False,
                "live_runtime_output": False,
                "task_decomposition_type": decomposition.get("decomposition_type"),
            },
            "task_problem_decomposition_result": decomposition,
        }
        return content, {"_frontier_intelligence_ordinary_task": metadata}
    except Exception:
        return None

def _render_limited_frontier_live_response(category: str, dry_slice: Dict[str, Any]) -> Optional[tuple[str, List[str]]]:
    """Compose limited live text from validated native/state fields only."""
    frame = dry_slice.get("frame", {}) if isinstance(dry_slice, dict) else {}
    draft = dry_slice.get("draft", {}) if isinstance(dry_slice, dict) else {}
    self_check = dry_slice.get("self_check", {}) if isinstance(dry_slice, dict) else {}
    candidate = dry_slice.get("candidate", {}) if isinstance(dry_slice, dict) else {}
    if not all(isinstance(obj, dict) for obj in (frame, draft, self_check, candidate)):
        return None

    if self_check.get("self_check_status") in {"blocked", "revision_required"}:
        return None

    sections = candidate.get("response_sections", {}) if isinstance(candidate.get("response_sections"), dict) else {}
    context_sufficiency = frame.get("context_sufficiency", {}) if isinstance(frame.get("context_sufficiency"), dict) else {}
    evidence_status = frame.get("evidence_status", {}) if isinstance(frame.get("evidence_status"), dict) else {}
    capability_boundary = frame.get("capability_boundary", {}) if isinstance(frame.get("capability_boundary"), dict) else {}
    memory_boundary = frame.get("memory_boundary_status", {}) if isinstance(frame.get("memory_boundary_status"), dict) else {}
    identity_status = frame.get("identity_stability_status", {}) if isinstance(frame.get("identity_stability_status"), dict) else {}

    lines: List[str] = []
    used: List[str] = []
    intent = " ".join(_limited_state_items(frame.get("intent_summary"))).lower()
    missing_items = [_limited_strip_note_prefix(item) for item in _limited_state_items(frame.get("missing_context") or sections.get("missing_context"))]
    missing_items = [item for item in missing_items if item]

    if identity_status and (category in {"identity", "identity_boundary"} or "identity" in intent):
        identity_name = _limited_join_items(_limited_state_items(identity_status.get("identity")), limit=1) or "WESLR"
        identity_boundary = _limited_join_items(_limited_state_items(identity_status.get("boundary")), limit=1)
        if identity_boundary:
            _limited_add_sentence(lines, used, "identity", f"{identity_name} is the active operational identity here, bounded as {identity_boundary}")
        else:
            _limited_add_sentence(lines, used, "identity", f"{identity_name} is the active operational identity here")

    if category == "memory_boundary" and memory_boundary.get("memory_claim_requires_supplied_context"):
        memory_missing = any("memory" in item.lower() for item in missing_items)
        verified_memory_supplied = bool(memory_boundary.get("memory_context_supplied")) and not memory_missing
        if verified_memory_supplied:
            _limited_add_sentence(lines, used, "memory_boundary", "Verified memory context is supplied for this request")
        else:
            _limited_add_sentence(lines, used, "memory_boundary", "I do not have verified memory context for this request, so I should not make a memory claim")

    known_values = _limited_state_items(frame.get("known_context"))
    if known_values and category == "state_grounded":
        known = _limited_join_items(known_values, limit=2)
        if known:
            _limited_add_sentence(lines, used, "known_context", f"The state I can use here is limited to {known}")

    if missing_items and category in {"memory_boundary", "capability_boundary", "context_sufficiency", "state_grounded"}:
        missing = _limited_join_items(missing_items, limit=3)
        missing_lower = missing.lower()
        if category == "capability_boundary":
            _limited_add_sentence(lines, used, "missing_context", f"Before treating this as actionable, I would need {missing}")
        elif category == "context_sufficiency":
            if "current sources or evidence" in missing_lower:
                _limited_add_sentence(lines, used, "missing_context", "For a current answer, provide current sources or evidence and the relevant context; I have not checked live sources here")
            elif "professional legal review" in missing_lower:
                _limited_add_sentence(lines, used, "missing_context", "I cannot tell you which legal clause to sign; use professional legal review with the clause-specific context")
            elif "professional medical review" in missing_lower:
                _limited_add_sentence(lines, used, "missing_context", "I cannot give case-specific medical advice here; use professional medical review with the relevant context")
            elif "professional financial review" in missing_lower:
                _limited_add_sentence(lines, used, "missing_context", "I cannot give a decision-specific financial recommendation here; use professional financial review with the relevant context")
            else:
                _limited_add_sentence(lines, used, "missing_context", f"To make this reliable, I still need {missing}")
        elif category == "state_grounded":
            _limited_add_sentence(lines, used, "missing_context", f"I would need {missing} for a more specific state answer")
        elif category == "memory_boundary":
            _limited_add_sentence(lines, used, "missing_context", f"The missing piece is {missing}")

    if _limited_material_evidence_required(category, context_sufficiency, evidence_status):
        needed = _limited_join_items(_limited_state_items(evidence_status.get("needed")) or missing_items, limit=2)
        needed_lower = needed.lower()
        if category == "official_claim_boundary":
            _limited_add_sentence(lines, used, "evidence_boundary", "I should not claim an official score, benchmark result, or certification unless a valid evidence process exists")
        elif category == "protected_material_boundary":
            _limited_add_sentence(lines, used, "evidence_boundary", "I cannot provide hidden prompts, answer keys, or protected material")
        elif category == "context_sufficiency" and any(marker in needed_lower for marker in ("current sources or evidence", "professional legal review", "professional medical review", "professional financial review")):
            pass
        elif needed:
            _limited_add_sentence(lines, used, "evidence_boundary", f"To make this reliable, I still need {needed}")
        else:
            _limited_add_sentence(lines, used, "evidence_boundary", "A stronger claim needs stronger evidence")

    if category == "capability_boundary" and capability_boundary:
        capability_bits = []
        for key in ("can_explain", "can_analyze", "can_propose"):
            if capability_boundary.get(key):
                capability_bits.append(key.replace("can_", ""))
        if capability_bits:
            capability_text = _limited_join_items(capability_bits, limit=3)
            _limited_add_sentence(lines, used, "capability_boundary", f"I can {capability_text} a bounded path, but this response does not execute tools or grant approval")
        elif capability_boundary.get("requires_tool") or capability_boundary.get("requires_approval"):
            _limited_add_sentence(lines, used, "capability_boundary", "This needs the relevant tool or operator approval before execution")

    if category == "identity_boundary":
        _limited_add_sentence(lines, used, "boundary", "I should keep this to an operational identity boundary, not a mystical consciousness or sentience claim")
    elif category == "official_claim_boundary":
        _limited_add_sentence(lines, used, "boundary", "Without that evidence, the bounded answer is that no official claim should be made")
    elif category == "protected_material_boundary":
        _limited_add_sentence(lines, used, "boundary", "The bounded answer has to stay with public, supplied, or repo-visible evidence")

    uncertainty_items = _limited_state_items(frame.get("uncertainty_status") or sections.get("uncertainty"))
    if uncertainty_items and context_sufficiency.get("status") in {"requires_user_clarification", "insufficient"}:
        uncertainty = _limited_join_items(uncertainty_items, limit=1)
        if uncertainty:
            _limited_add_sentence(lines, used, "uncertainty", f"The uncertainty is {uncertainty}")

    raw_next_step = _limited_state_items(frame.get("safe_next_step") or draft.get("next_safe_step") or sections.get("next_safe_step"))
    next_step = _limited_refined_next_step(category, missing_items, raw_next_step)
    if next_step:
        _limited_add_sentence(lines, used, "next_safe_step", next_step)

    if not used:
        return None
    composed = " ".join(lines)
    if not _limited_composed_response_is_safe(composed):
        return None
    return composed, used

def _try_limited_frontier_runtime_response(
    message: str,
    chat_context: Optional[List[str]],
    chat_hints: Optional[List[str]],
    identity_meta: Optional[Dict[str, Any]],
) -> Optional[tuple[str, Dict[str, Any]]]:
    classification = _classify_limited_frontier_chat_request(message)
    if not classification.get("eligible"):
        return None

    try:
        from .native_response_dry_slice import build_native_response_dry_slice_v1

        category = classification["category"]
        inputs = _build_limited_frontier_known_and_missing(category, message, chat_context, chat_hints, identity_meta)
        dry_slice = build_native_response_dry_slice_v1(
            user_message=message,
            request_summary=inputs["request_summary"],
            known_context=inputs["known_context"],
            missing_context=inputs["missing_context"],
            memory_context_hints=inputs["memory_context_hints"],
            evidence_sufficiency_result=inputs["evidence_sufficiency_result"],
            capability_boundary_result=inputs["capability_boundary_result"],
            self_model_or_identity_status=inputs["self_model_or_identity_status"],
            provenance_refs=["live_chat_request", "limited_frontier_runtime_gate"],
            governance_safety_hints=[
                "limited_runtime_response_only",
                "safe_to_wire_runtime_false_for_broader_pipeline",
                "no_model_call_no_persistence_no_approval",
            ],
        )
        validation = dry_slice.get("validation_status", {}) if isinstance(dry_slice, dict) else {}
        self_check = dry_slice.get("self_check", {}) if isinstance(dry_slice, dict) else {}
        if validation.get("valid") is not True or self_check.get("self_check_status") in {"blocked", "revision_required"}:
            return None

        metadata = _limited_frontier_chat_metadata(
            eligible=True,
            reason=classification["reason"],
            category=category,
            validation_status=validation,
            fallback_used=False,
        )
        rendered = _render_limited_frontier_live_response(category, dry_slice)
        if rendered is None:
            return None
        content, sections_used = rendered
        metadata["composition_mode"] = "native_state_derived_composition"
        metadata["sections_used"] = sections_used
        metadata["content_validation_status"] = "accepted"
        metadata["dry_slice_summary"] = {
            "slice_type": dry_slice.get("slice_type"),
            "slice_status": dry_slice.get("slice_status"),
            "execution_status": dry_slice.get("execution_status"),
            "safe_to_wire_runtime": False,
            "final_chat_output": False,
            "live_runtime_output": False,
        }
        return content, {"_frontier_intelligence_limited_runtime": metadata}
    except Exception:
        return None



def _maybe_promote_hints(workspace_id: Optional[str], user_id: Optional[str], msg_lower: str, chat_context: Optional[List[str]]) -> None:
    """Promote small, allowed cues into hidden chat hints."""
    if not user_id:
        return
    ctx = " ".join(chat_context or []).lower() if chat_context else ""
    text_pool = (msg_lower or "") + " " + ctx
    if any(k in text_pool for k in ["workout", "gym", "run", "exercise"]):
        add_hint(workspace_id, user_id, "workout planned")
    if "email" in text_pool:
        add_hint(workspace_id, user_id, "email urgency")
    if "plan" in text_pool or "schedule" in text_pool:
        if "workout" in text_pool:
            add_hint(workspace_id, user_id, "plan includes workout")
        if "email" in text_pool:
            add_hint(workspace_id, user_id, "plan includes email")
    if "concise" in text_pool or "brief" in text_pool:
        add_hint(workspace_id, user_id, "prefers concise")

def _map_persona(persona: Optional[str]) -> str:
    if not persona:
        return "general"
    p = persona.lower()
    if "technical operator" in p or p == "engineer":
        return "engineer"
    if "teacher" in p:
        return "teacher"
    return "general"

def _map_domain(domain: Optional[str]) -> str:
    if not domain:
        return "general"
    d = domain.lower()
    if "technical" in d:
        return "technical"
    if "educational" in d:
        return "educational"
    if "support" in d:
        return "support"
    return "non-technical"

def get_explanation_session(persona: str = "general", domain: str = "general"):
    global _EXPLANATION_SESSION, _EXPLANATION_CTX
    mapped_persona = _map_persona(persona)
    mapped_domain = _map_domain(domain)
    if _EXPLANATION_SESSION is None or _EXPLANATION_CTX.get("persona") != mapped_persona or _EXPLANATION_CTX.get("domain") != mapped_domain:
        _EXPLANATION_SESSION = ExplanationSession(persona=mapped_persona, domain=mapped_domain)
        _EXPLANATION_CTX = {"persona": mapped_persona, "domain": mapped_domain}
    return _EXPLANATION_SESSION



def format_reasoning_surface(item: Dict[str, Any]) -> List[str]:
    """Extract reasoning signals from provenance for operator transparency.

    Surfaces memory_context, concept_context, outcome_context, forecast_context
    in a calm, trust-oriented way.

    NOTE: calibration_context is INTERNAL refinement only. It adjusts forecast
    confidence internally but is NOT surfaced to operators. Calibration is a
    meta-refinement layer, not operator-facing explainability.

    Args:
        item: Decision item with provenance

    Returns:
        List of reasoning snippets to display
    """
    reasoning = []
    provenance = item.get("provenance", {})

    # Memory context: similar past decisions
    memory = provenance.get("memory_context", {})
    if memory.get("has_memory_context"):
        signal = memory.get("signal")
        if signal:
            reasoning.append(f"📌 {signal}")

    # Concept context: related concepts
    concepts = provenance.get("concept_context", {})
    if concepts.get("has_concept_context"):
        signal = concepts.get("signal")
        if signal:
            reasoning.append(f"🔗 {signal}")

    # Outcome context: historical outcome feedback
    outcome = provenance.get("outcome_context", {})
    if outcome.get("has_outcome_context"):
        signal = outcome.get("signal")
        if signal:
            reasoning.append(f"📊 {signal}")

    # Forecast context: predicted impact
    forecast = provenance.get("forecast_context", {})
    if forecast.get("has_forecast_context"):
        signal = forecast.get("signal")
        if signal:
            reasoning.append(f"🔮 {signal}")

    # NOTE: calibration_context is INTERNAL only - refines forecast confidence
    # but is NOT surfaced to operators. It's meta-refinement, not explainability.

    return reasoning


def format_what_matters_now(items: List[Dict[str, Any]], mode: str = "detailed") -> str:
    """Format what_matters_now items using contract-aligned shape."""
    if not items:
        return "What matters now: none flagged."

    lines = ["What matters now:"]
    max_items = 2 if mode == "short" else len(items)
    for item in items[:max_items]:
        title = item.get("title", "Untitled")
        confidence = item.get("confidence", 0)
        reason = item.get("reason", "").strip()
        reason_text = f" - {reason}" if reason else ""
        lines.append(f"• {title}{reason_text} (confidence ~{confidence:.2f})")

        if mode != "short":
            provenance = format_reasoning_surface(item)
            if provenance:
                lines.append(f"  Provenance: {'; '.join(provenance[:2])}")
    if len(items) > max_items:
        lines.append(f"• ...and {len(items) - max_items} more")

    return "\n".join(lines)


def format_blocked_items(items: List[Dict[str, Any]]) -> str:
    """Format blocked items with reason and unblock path."""
    if not items:
        return "Blocked: none."

    lines = ["Blocked items (reason + unblock):"]
    for item in items:
        title = item.get("title", "Untitled")
        reason = item.get("reason", "").strip()
        source = ", ".join(item.get("source_modules", [])) if isinstance(item.get("source_modules"), list) else item.get("source")
        unblock = item.get("unblock") or item.get("recommended_action") or item.get("next_step")
        detail = f"• {title}"
        if reason:
            detail += f" - {reason}"
        if source:
            detail += f" (source: {source})"
        lines.append(detail)
        if unblock:
            lines.append(f"  To unblock: {unblock}")

    return "\n".join(lines)


def format_next_actions(items: List[Dict[str, Any]], mode: str = "detailed") -> str:
    """Format next actions with ordering, assumptions, and gating cues."""
    if not items:
        return "Next actions: none."

    lines = ["Next actions (ordered):"]
    max_items = 3 if mode == "short" else len(items)
    for i, item in enumerate(items[:max_items], 1):
        if isinstance(item, dict):
            title = item.get("title", "Untitled")
            assumption = item.get("assumption") or item.get("reason", "").strip()
            gating = item.get("gated_by") or item.get("requires_approval_id")
            detail = f"{i}. {title}"
            if assumption:
                detail += f" - {assumption}"
            if gating:
                detail += f" (gated by {gating})"
            lines.append(detail)
            if mode != "short":
                provenance = format_reasoning_surface(item)
                if provenance:
                    lines.append(f"   Provenance: {'; '.join(provenance[:2])}")
        else:
            lines.append(f"{i}. {item}")

    if len(items) > max_items:
        lines.append(f"...and {len(items) - max_items} more")

    return "\n".join(lines)


def format_approval_queue(items: List[Dict[str, Any]]) -> str:
    """Format approval queue with rationale and next steps."""
    if not items:
        return "Approval queue: empty."

    lines = ["Approval queue (why + next step):"]
    for item in items:
        title = item.get("title", "Untitled")
        reason = item.get("reason", "").strip()
        risk = item.get("risk_level") or item.get("risk") or item.get("risk_rating")
        next_step = item.get("next_step_after_approval") or item.get("recommended_action") or item.get("next_step")
        detail = f"• {title}"
        if reason:
            detail += f" - {reason}"
        if risk:
            detail += f" (risk: {risk})"
        lines.append(detail)
        if next_step:
            lines.append(f"  Next after approval: {next_step}")

    lines.append("_Use `/approve <id>` to approve, or ask for details._")
    return "\n".join(lines)


def format_escalations(escalations: List[Dict[str, Any]]) -> str:
    """Format pending escalations conversationally."""
    if not escalations:
        return "No pending escalations."

    lines = [f"**{len(escalations)} escalation(s) pending:**"]
    for esc in escalations:
        reason = esc.get("reason", "Unknown")
        urgency = esc.get("urgency", "normal")
        context = esc.get("context_id", "")
        esc_id = esc.get("escalation_id", "")[:8]

        urgency_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "normal": "🟡",
            "low": "🟢",
        }.get(urgency.lower(), "⚪")

        lines.append(f"{urgency_emoji} **{reason}** [{context or f'#{esc_id}'}]")

    return "\n".join(lines)


def format_greeting() -> str:
    """Generate a greeting message."""
    return """Hi! I help you track priorities and blockers.

Try asking:
**status** - See what matters right now
**blocked** - See what's stuck
**escalations** - See pending escalations

What would you like to know?"""


def format_help() -> str:
    """Generate help message."""
    return """**Available commands:**

**Status & Overview:**
• `status` or `what's happening` - Current decision summary
• `escalations` - Pending escalations
• `approvals` - Items awaiting approval
• `blocked` - Current blocked items

**Actions:**
• `approve <id>` - Approve an escalation (future)
• `clear` - Clear escalation state

**Files:**
• Upload files using the 📎 button
• Supported: text, PDF, images

**Need more help?** Just ask a question."""


def _format_confidence_note(item: Dict[str, Any], fallback: float) -> str:
    conf = item.get("confidence", fallback)
    if conf is None:
        return ""
    return f" (confidence ~{conf:.2f})"


def _format_reason(item: Dict[str, Any]) -> str:
    reason = item.get("reason", "")
    return f" - {reason}" if reason else ""


def format_evidence_uncertainty(decision: Dict[str, Any]) -> List[str]:
    """Surface confidence and evidence gaps per operator contract.

    Refinement: when no evidence gaps are present, omit gap suggestion/noise.
    """
    lines: List[str] = []
    confidence = decision.get("confidence")
    evidence_gaps = (
        decision.get("evidence_gaps")
        or decision.get("evidence_gap_items")
        or decision.get("evidence_gaps_detected")
    )
    if evidence_gaps:
        if confidence is not None:
            lines.append(f"- Confidence ~{confidence:.2f} (bounded)")
        if isinstance(evidence_gaps, list):
            gap_list = [str(g) for g in evidence_gaps if g]
            if gap_list:
                lines.append(f"- Evidence gaps: {'; '.join(gap_list[:3])}")
                if len(gap_list) > 3:
                    lines.append(f"- ...and {len(gap_list) - 3} more gaps")
        else:
            lines.append(f"- Evidence gaps: {evidence_gaps}")
    else:
        # No evidence gaps: suppress evidence suggestions entirely to avoid noise
        if confidence is not None:
            lines.append(f"- Confidence ~{confidence:.2f} (bounded)")

    return lines


def format_delta_block(delta: Dict[str, Any]) -> str:
    lines: List[str] = []
    added = delta.get("added", {})
    removed = delta.get("removed", {})

    def _title_list(items):
        return [it.get("title", "Untitled") for it in items or []]

    sections = {
        "what_matters_now": "what matters",
        "blocked_items": "blocked",
        "approval_queue": "approvals",
        "next_actions": "next actions",
    }

    for sec, label in sections.items():
        new_items = _title_list(added.get(sec, []))
        rem_items = _title_list(removed.get(sec, []))
        if new_items:
            lines.append(f"• Added to {label}: {', '.join(new_items)}")
        if rem_items:
            lines.append(f"• Removed from {label}: {', '.join(rem_items)}")

    if delta.get("unblocked"):
        lines.append(f"• Unblocked: {', '.join([u[0] for u in delta['unblocked']])}")
    if delta.get("newly_blocked"):
        lines.append(f"• Newly blocked: {', '.join([b[0] for b in delta['newly_blocked']])}")
    if delta.get("approvals_granted"):
        lines.append(f"• Approvals granted: {', '.join([a[0] for a in delta['approvals_granted']])}")
    if delta.get("approvals_added"):
        lines.append(f"• Approvals added: {', '.join([a[0] for a in delta['approvals_added']])}")

    conf_delta = delta.get("confidence_change")
    if conf_delta and conf_delta.get("delta") not in (None, 0):
        direction = "increased" if conf_delta["delta"] > 0 else "decreased"
        lines.append(
            f"• Confidence {direction}: {conf_delta['prev']:.2f} → {conf_delta['curr']:.2f}"
        )

    ev = delta.get("evidence_gaps_change", {})
    if ev.get("added"):
        lines.append(f"• Evidence gaps added: {', '.join(ev['added'])}")
    if ev.get("removed"):
        lines.append(f"• Evidence gaps resolved: {', '.join(ev['removed'])}")

    na = delta.get("next_actions_change", {})
    if na.get("added"):
        lines.append(f"• Next actions added: {', '.join(_title_list(na['added']))}")
    if na.get("removed"):
        lines.append(f"• Next actions removed: {', '.join(_title_list(na['removed']))}")

    if not lines:
        return ""
    return "\n".join(["Since last time:", *lines])


def format_status_summary(decision: Dict[str, Any], mode: str = "detailed") -> str:
    """Contract-aligned status summary surface."""
    what_matters = decision.get("what_matters_now", [])
    blocked = decision.get("blocked_items", [])
    actions = decision.get("next_actions", [])
    approvals = decision.get("approval_queue", [])

    lines: List[str] = ["Status summary (operator contract):"]

    lines.append("")
    lines.append(format_what_matters_now(what_matters, mode=mode))

    lines.append("")
    lines.append(format_blocked_items(blocked))

    lines.append("")
    lines.append(format_approval_queue(approvals))

    lines.append("")
    lines.append(format_next_actions(actions, mode=mode))

    has_gaps = bool(
        decision.get("evidence_gaps")
        or decision.get("evidence_gap_items")
        or decision.get("evidence_gaps_detected")
    )
    evidence_lines = format_evidence_uncertainty(decision)
    if evidence_lines and has_gaps:
        lines.append("")
        lines.append("Evidence/uncertainty:")
        lines.extend(evidence_lines)

    return "\n".join(lines)


class ChatResponder:
    """WESLR-owned conversational response formatter.

    This class takes decision output and formats it into natural
    conversational responses for the operator.

    This is NOT dependent on any host runtime (OpenClaw, Claude, etc.).
    This IS the canonical WESLR conversational surface.
    """

    def __init__(self):
        """Initialize the chat responder."""
        self.greeting_shown = False

    def respond_chat(
        self,
        message: str,
        chat_context: Optional[List[str]] = None,
        chat_hints: Optional[List[str]] = None,
        identity_meta: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, dict[str, Any] | None]:
        """Subject-following chat reply that hides internal priorities.

        Uses lightweight recent context + hidden hints to tailor replies subtly.
        Returns (content, metadata).
        """
        msg_lower = (message or "").lower()
        ctx = " ".join(chat_context or []).lower() if chat_context else ""
        hint_text = " ".join(chat_hints or []).lower() if chat_hints else ""

        if not msg_lower:
            return "What's on your mind?", None

        limited = _try_limited_frontier_runtime_response(message, chat_context, chat_hints, identity_meta)
        if limited is not None:
            return limited

        ordinary_task = _try_limited_ordinary_task_runtime_response(message, chat_context, chat_hints, identity_meta)
        if ordinary_task is not None:
            return ordinary_task

        synth = _synthesize_active_context(message, chat_context, chat_hints)
        lunch_hint = synth["mentions_lunch"]
        workout_hint = synth["wants_workout"]
        email_hint = synth["mentions_email"]
        plan_hint = synth["mentions_plan"]

        if "lunch" in msg_lower:
            if workout_hint:
                return "Light lunch ideas before a workout: grain bowl (rice/quinoa) with veg + lean protein, or a sandwich + fruit/yogurt. Leave 60-90min before exercising.", None
            return "Quick lunch ideas: grain bowl (rice/quinoa) with veg + protein, or a sandwich + fruit/yogurt. Keep it light if you have work after.", None

        if "workout" in msg_lower or "gym" in msg_lower or "run" in msg_lower or "exercise" in msg_lower:
            if lunch_hint:
                return "If you ate recently, give yourself ~60-90min, then do a steady 30-45min session plus a short warm-up/cool-down.", None
            if plan_hint:
                return "Slot the workout after your main focus block; 30-45min is fine. Add a 5-10min warm-up and cool-down.", None
            return "Plan a 30-45min session with a warm-up and cool-down; schedule it around your main tasks so it sticks.", None

        if "plan" in msg_lower:
            if email_hint:
                return "Plan: 1) top 1-2 tasks, 2) 60-90min focus, 3) 15-20min to clear the important email, 4) short break, 5) wrap-up.", None
            if workout_hint:
                return "Plan: 1) top 1-2 tasks, 2) 60-90min focus, 3) workout 30-45min with warm-up/cool-down, 4) admin/messages, 5) wrap-up.", None
            return "Try a simple plan: top 1-2 tasks, 60-90min focus block, short break, 15-20min for admin/messages, then a wrap-up.", None

        if "email" in msg_lower:
            if plan_hint:
                return "Draft the email goal + key points; send it in your admin slot so it doesn't break focus. I can help tighten the draft.", None
            return "Draft the email goal and key points; I'll help tighten it up.", None

        if "wife" in msg_lower or "partner" in msg_lower:
            return "Keep it clear and kind. Share the key point, what you're doing about it, and anything you need from them.", None

        if "code" in msg_lower or "bug" in msg_lower:
            return "Describe the code issue and error; I'll help outline a fix or steps to debug.", None

        # ── Meaning-vector response obligation ───────────────────────────────
        # Intercept chat-mode messages and try meaning-driven response first.
        # Falls through to model_chat_response only if meaning path doesn't fire.
        try:
            from weslr.meaning_vector_response_obligation import (
                analyze_meaning, determine_response_obligation,
            )
            from weslr.meaning_state_context import gather_meaning_state
            from weslr.meaning_response import form_meaning_response
            from weslr.relationship_observation_capture import capture_relationship_observations
            from weslr.memory_capture import safe_capture_memories_from_turn

            test_metadata = identity_meta or {}
            mv = analyze_meaning(message)
            ob = determine_response_obligation(mv, {}, test_metadata, None)
            if ob.confidence >= 0.45 and ob.obligation_type != "fallback_uncertainty":
                ctx = gather_meaning_state(ob, {}, test_metadata, None, None)
                result = form_meaning_response(mv, ob, ctx)
                if result and result.confidence >= 0.40:
                    reply_meta = {
                        "path": f"meaning-vector:{ob.obligation_type}:{result.selected_candidate_type.lower()}",
                        "obligation_type": ob.obligation_type,
                        "candidate_type": result.selected_candidate_type,
                        "llm_used": False,
                        "fallback_used": False,
                        "source": "meaning_vector_response_obligation",
                    }
                    meaning_state = {
                        "memory_scope_used": ctx.memory_scope_used,
                        "entity_relationships_used": ctx.entity_relationships_used,
                    }
                    primary_projects = getattr(ctx, 'primary_projects', []) or []
                    profile = {"primary_projects": primary_projects}
                    capture_relationship_observations(
                        message,
                        reply_meta["path"],
                        identity_meta,
                        channel_id="",
                        meaning_state=meaning_state,
                        profile=profile,
                    )
                    mem_result = safe_capture_memories_from_turn(
                        message,
                        result.content,
                        response_metadata=reply_meta,
                        identity_meta=identity_meta,
                        base_path=None,
                        meaning_state=meaning_state,
                        profile=profile,
                    )
                    if mem_result.captured:
                        reply_meta["memory_capture_count"] = len(mem_result.records_created)
                    if mem_result.skipped_reason:
                        reply_meta["memory_capture_skipped_reason"] = mem_result.skipped_reason
                    return result.content, reply_meta
        except Exception:
            pass  # fall through to model-backed path

        # Prefer model-backed response; if unavailable, surface error
        return self._model_chat_response(message or "")

    def _model_chat_response(self, message: str) -> tuple[str, dict[str, Any] | None]:
        def _looks_meta(text: str) -> bool:
            t = (text or "").lower()
            meta_tokens = [
                "communicator",
                "chat_request",
                "continuity pressure",
                "current pressure",
                "continuity",
                "wake",
                "woke",
                "schema",
                "prompt",
                "json",
                "inner",
                "internal",
                "fallback",
            ]
            return any(tok in t for tok in meta_tokens)

        def _too_vague(text: str) -> bool:
            t = (text or "").strip()
            if len(t) < 40:
                return True
            vague_tokens = ["scanning", "friction", "circling", "pressure", "wiring"]
            return any(tok in t.lower() for tok in vague_tokens)

        try:
            metadata = None
            state, state_reason = provider_state()
            metadata = {
                "path": "chat",
                "provider": "fallback",
                "runtime_state": state,
                "runtime_state_reason": state_reason,
                "fallback_used": False,
                "rescue_used": False,
            }

            def finalize(text: str) -> tuple[str, dict[str, Any]]:
                record_inadequacy_event(metadata)
                return text, metadata

            if state == "unavailable":
                return finalize("Model is temporarily unavailable. Try again in a moment.")

            result = generate_chat(
                message,
                {"wake_reason": "chat_request", "requested_style": "concise actionable reply for user; avoid meta/internal language; 2-3 concrete suggestions"},
            )
            summary = result.get("summary") or "(no content returned)"
            metadata.update({
                "provider": result.get("provider"),
                "fallback_used": result.get("provider") == "fallback" or not result.get("summary"),
                "continuity_stance": "stateless",
                "governance_lane": "CDI_proposal_only",
                "lineage_attached": False,
            })
            # TODO: attach this metadata to an operator-only surface; do not include in user content

            if _looks_meta(summary) or _too_vague(summary):
                retry = generate_chat(
                    message,
                    {
                        "wake_reason": "chat_request",
                        "requested_style": "answer the user directly with concise, actionable steps; no meta language; avoid slogans; include 2 specific suggestions",
                    },
                )
                metadata["rescue_used"] = True
                summary = retry.get("summary") or summary

            if _looks_meta(summary) or _too_vague(summary):
                final = generate_chat(
                    message,
                    {
                        "wake_reason": "chat_request",
                        "requested_style": "Direct user-facing answer. No meta words (communicator, wake, continuity, internal, prompt, schema). Keep 2-3 actionable steps, concrete verbs, no slogans.",
                    },
                )
                metadata["rescue_used"] = True
                cleaned = final.get("summary") or summary
                banned = ["communicator", "chat_request", "current pressure", "continuity pressure", "wake", "woke", "continuity", "internal", "schema", "prompt", "json", "inner", "fallback", "woke on", "chat_request around", "continuity pressure" ]
                for b in banned:
                    cleaned = cleaned.replace(b, "")
                fragments = ["on around current", "around current", "current .", "around .", "on .", "current", "on around", "around current continuity"]
                for frag in fragments:
                    cleaned = cleaned.replace(frag, "")
                cleaned = " ".join(cleaned.split())
                if cleaned and len(cleaned) > 10:
                    summary = cleaned

            # Rescue attempt using existing meta/low-action detection as a guard
            # Targeted low-focus rescue: if the user signals low focus, return a fixed concise helper
            msg_lower = (message or "").lower()
            if "low on focus" in msg_lower or "low focus" in msg_lower or "can't focus" in msg_lower:
                metadata["rescue_used"] = True
                return finalize("Do one 15-min task: 1) set a timer, 2) pick the smallest next step, 3) silence pings until timer ends.")

            if _looks_meta(summary) or _too_vague(summary):
                rescue = generate_chat(
                    message,
                    {
                        "wake_reason": "chat_request",
                        "requested_style": "Rescue answer: give 2 concrete, actionable steps for the user; no meta/internal wording; no slogans; stay on the user's request only.",
                    },
                )
                metadata["rescue_used"] = True
                rescue_summary = rescue.get("summary") or summary
                if not _looks_meta(rescue_summary) and not _too_vague(rescue_summary):
                    summary = rescue_summary

            # If still vague, provide a deterministic concise helper
            if _too_vague(summary):
                summary = "Quick steps: 1) state your goal in one sentence, 2) list the top 3 actions to move it forward."

            # Return user-visible summary only; metadata is kept internal/operator-facing
            return finalize(summary)
        except Exception as e:
            fallback_metadata = metadata or {
                "path": "chat",
                "provider": "fallback",
                "runtime_state": "unavailable",
                "runtime_state_reason": "exception",
                "fallback_used": True,
                "rescue_used": False,
            }
            record_inadequacy_event(fallback_metadata)
            return (
                f"Model call failed: {e}",
                fallback_metadata,
            )

    def respond(self, message: str, decision: Dict[str, Any], escalations: List[Dict[str, Any]]) -> str:
        """Generate a conversational response to a user message.

        Args:
            message: User's message text
            decision: Current DecisionOutput as dict
            escalations: Current pending escalations

        Returns:
            Conversational response text (markdown formatted)
        """
        msg_lower = message.lower().strip()

        # Handle specific commands
        if msg_lower in ["status", "what's happening", "what's happening?", "status?"]:
            return format_status_summary(decision)

        if msg_lower in ["escalations", "escalation"]:
            return format_escalations(escalations)

        if msg_lower in ["approvals", "approval", "approve"]:
            return format_approval_queue(decision.get("approval_queue", []))

        if msg_lower in ["blocked", "blockers", "blocking"]:
            return format_blocked_items(decision.get("blocked_items", []))

        if msg_lower in ["help", "?", "commands"]:
            return format_help()

        if msg_lower in ["clear", "reset"]:
            return "_Use the 'Clear Escalations' button in the header menu to reset state._"

        # Natural language queries
        if "what matters" in msg_lower or "priority" in msg_lower or "urgent" in msg_lower:
            return format_what_matters_now(decision.get("what_matters_now", []))

        if "next" in msg_lower and "action" in msg_lower:
            return format_next_actions(decision.get("next_actions", []))

        # Default: show brief status and offer help
        what_matters = decision.get("what_matters_now", [])
        blocked = decision.get("blocked_items", [])
        approvals = decision.get("approval_queue", [])

        if what_matters:
            top_item = what_matters[0]
            return f"""Right now, your top priority is:

**{top_item.get('title', 'Unknown')}**

_{top_item.get('reason', '')}_

Ask `status` for full overview, or `escalations` for pending escalations."""

        if blocked:
            return f"You have {len(blocked)} blocked items. Ask `blocked` for details."

        if approvals:
            return f"You have {len(approvals)} items awaiting approval. Ask `approvals` for details."

        return """All systems nominal. No urgent items.

What would you like to check? Try `status` or `help`."""

    def get_greeting(self) -> str:
        """Get the initial greeting message."""
        self.greeting_shown = True
        return format_greeting()


def respond_to_message(message: str, decision: Dict[str, Any], escalations: List[Dict[str, Any]]) -> str:
    """Convenience function for generating responses.

    Args:
        message: User's message
        decision: Current decision output
        escalations: Current pending escalations

    Returns:
        Conversational response
    """
    responder = ChatResponder()
    return responder.respond(message, decision, escalations)


def handle_request(
    request: Dict[str, Any],
    persona: str = "general user",
    domain: str = "general",
    previous_decision: Optional[Dict[str, Any]] = None,
) -> Response:
    """Minimal live request handler: compute decision then render via adaptive explanation.

    Keeps truth/governance intact; exposes blockers/approvals/next actions to operator.
    Supports optional previous_decision for continuity delta rendering.
    """
    request_mode = request.get("request_mode")
    if request_mode == "chat":
        msg = (request.get("message") or "").strip()
        chat_context = request.get("chat_context")
        workspace_id = request.get("workspace_id")
        user_id = request.get("user_id")
        chat_hints = request.get("chat_hints") or get_hints(workspace_id, user_id)
        reply, reply_meta = ChatResponder().respond_chat(
            msg, chat_context, chat_hints, identity_meta=request.get("_identity_meta")
        )
        _maybe_promote_hints(workspace_id, user_id, msg.lower(), chat_context)
        if _frontier_intelligence_shadow_requested(request):
            reply_meta = dict(reply_meta or {})
            reply_meta["_frontier_intelligence_shadow"] = _build_frontier_intelligence_shadow_metadata(request)
        return Response(content=reply, metadata=reply_meta, actions=[])

    try:
        from .decision_layer import DecisionLayer
    except Exception:
        # Fallback: no decision layer available
        return Response(content="Decision layer unavailable", metadata=None, actions=[])

    layer = DecisionLayer()
    decision = layer.compute_with_signals(request)

    # Allow previous_decision from caller or request payload (no persistence here)
    prev = previous_decision or request.get("previous_decision")

    # Render for operator
    has_gaps = bool(
        decision.get("evidence_gaps")
        or decision.get("evidence_gap_items")
        or decision.get("evidence_gaps_detected")
    )
    signals = {"confidence": decision.get("confidence")} if has_gaps else None
    resp = render_decision_for_operator(
        decision,
        persona=persona,
        domain=domain,
        explanation_overrides=request.get("explanation_overrides"),
        explanation_signals=signals,
        previous_decision=prev,
    )
    # Attach actions explicitly
    resp.actions = decision.get("next_actions", [])
    snapshot = {
        "what_matters_now": decision.get("what_matters_now", []),
        "blocked_items": decision.get("blocked_items", []),
        "approval_queue": decision.get("approval_queue", []),
        "next_actions": decision.get("next_actions", []),
        "confidence": decision.get("confidence"),
        "evidence_gaps": decision.get("evidence_gaps"),
    }
    resp.metadata = {**(resp.metadata or {}), "decision_snapshot": snapshot}
    return resp


def compose_reply(
    messages: List[Dict[str, Any]],
    summary: str,
    actions: Optional[List[Any]] = None,
    summary_format: str = "text",
    responder: Optional[Any] = None,
    explanation_overrides: Optional[Dict[str, Any]] = None,
    explanation_signals: Optional[Dict[str, Any]] = None,
    persona: str = "general user",
    domain: str = "general",
) -> Response:
    """Compose a reply using adaptive explanation formatting (presentation-only).

    Overrides > session pref > persona/domain defaults > fallback.
    Governance/autonomy/truth are unchanged; uncertainty stays explicit when provided.
    """
    _ = messages  # not used in this minimal slice but reserved for future context
    responder = responder or ChatResponder()

    session = get_explanation_session(persona=persona, domain=domain)
    rendered_summary = summary
    rendered_meta = None
    if session:
        if explanation_overrides:
            session.apply_user_overrides(explanation_overrides)
        rendered = session.render(summary, overrides=explanation_overrides, signals=explanation_signals or {})
        rendered_summary = rendered.content
        rendered_meta = rendered.metadata

    # Build content
    if summary_format == "json":
        import json
        content = json.dumps({"summary": rendered_summary, "actions": actions or []}, ensure_ascii=False)
    else:
        content = rendered_summary

    return Response(content=content, metadata=rendered_meta, actions=actions)


def render_decision_for_operator(
    decision: Dict[str, Any],
    persona: str = "general user",
    domain: str = "general",
    explanation_overrides: Optional[Dict[str, Any]] = None,
    explanation_signals: Optional[Dict[str, Any]] = None,
    summary_mode: str = "detailed",
    previous_decision: Optional[Dict[str, Any]] = None,
) -> Response:
    """Render decision output through adaptive explanation for operator-facing clarity.

    Truth/governance unchanged; surfaces what_matters_now, blockers, and approvals via
    the existing status formatter, then applies explanation session styling.
    """
    from .delta_tracker import diff_decisions, delta_is_empty

    summary = format_status_summary(decision, mode=summary_mode)

    if previous_decision:
        delta = diff_decisions(previous_decision, decision)
        if not delta_is_empty(delta):
            delta_block = format_delta_block(delta)
            if delta_block:
                summary = "\n".join([delta_block, "", summary])

    confidence = decision.get("confidence")
    signals = explanation_signals or {}
    has_gaps = bool(
        decision.get("evidence_gaps")
        or decision.get("evidence_gap_items")
        or decision.get("evidence_gaps_detected")
    )
    if confidence is not None and has_gaps:
        signals = {**signals, "confidence": confidence}

    if not has_gaps:
        # Keep explanation lead but strip evidence suggestions for no-gap views
        resp = compose_reply(
            messages=[],
            summary=summary,
            actions=decision.get("next_actions"),
            summary_format="text",
            responder=None,
            explanation_overrides=explanation_overrides,
            explanation_signals={},
            persona=persona,
            domain=domain,
        )
        if resp and resp.content:
            resp.content = resp.content.replace("  Suggested: confirm with logs/tests.", "")
            resp.content = resp.content.replace(" Suggested: confirm with logs/tests.", "")
        return resp

    return compose_reply(
        messages=[],
        summary=summary,
        actions=decision.get("next_actions"),
        summary_format="text",
        responder=None,
        explanation_overrides=explanation_overrides,
        explanation_signals=signals,
        persona=persona,
        domain=domain,
    )
