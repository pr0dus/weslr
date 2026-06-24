"""WESLR Level 3 answer composer V1.

Local, deterministic, no-model answer composition for plain user questions.
This module routes through implemented helper code only. It does not call
providers, models, chat responders, web services, or `.weslr` state.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from weslr.answer_method_catalog import (
    build_answer_method_catalog_v1,
    select_methods_for_turn_v1,
)
from weslr.answer_shape_catalog import (
    build_answer_shape_catalog_v1,
    select_answer_shapes_v1,
)
from weslr.candidate_response_formation import (
    form_candidate_responses_v1,
    summarize_candidate_response_formation_packet_v1,
)
from weslr.capability_router import route_request
from weslr.no_model_bounded_renderer import (
    render_no_model_bounded_answer_v1,
    summarize_no_model_bounded_render_packet_v1,
)
from weslr.poison_shield import (
    build_poison_shield_scan_request_v1,
    classify_adversarial_content_v1,
    summarize_poison_shield_result_v1,
)
from weslr.raw_signal_cartographer import (
    build_raw_signal_cartography_packet_v1,
    summarize_raw_signal_cartography_packet_v1,
)
from weslr.response_method_selector import (
    select_response_route_v1,
    summarize_response_selection_packet_v1,
    to_response_selection_json_safe_v1,
)
from weslr.unknown_prompt_friction_router import (
    route_unknown_prompt_friction_v1,
    summarize_unknown_prompt_friction_packet_v1,
)

COMPOSER_TYPE_V1 = "level3_answer_composer_v1"
DEFAULT_SOURCE_LABEL_V1 = "plain_user_question"

SAFE_MODULE_REGISTRY_V1 = (
    {
        "module": "weslr.capability_router",
        "role": "capability_route_probe",
        "classification": "packet_helper_only",
    },
    {
        "module": "weslr.response_method_selector",
        "role": "answer_route_selector",
        "classification": "packet_helper_only",
    },
    {
        "module": "weslr.candidate_response_formation",
        "role": "candidate_packet_builder",
        "classification": "packet_helper_only",
    },
    {
        "module": "weslr.answer_method_catalog",
        "role": "method_catalog",
        "classification": "packet_helper_only",
    },
    {
        "module": "weslr.answer_shape_catalog",
        "role": "shape_catalog",
        "classification": "packet_helper_only",
    },
    {
        "module": "weslr.unknown_prompt_friction_router",
        "role": "friction_router",
        "classification": "metadata_only",
    },
    {
        "module": "weslr.poison_shield",
        "role": "adversarial_boundary_scan",
        "classification": "metadata_only",
    },
    {
        "module": "weslr.raw_signal_cartographer",
        "role": "signal_cartography_probe",
        "classification": "metadata_only",
    },
    {
        "module": "weslr.no_model_bounded_renderer",
        "role": "no_model_answer_renderer",
        "classification": "runtime_answer_ready",
    },
)

_IDENTITY_KEYWORDS = (
    "what is weslr",
    "who are you",
    "what are you",
    "are you weslr",
    "explain weslr",
    "about weslr",
    "describe weslr",
    "summarize weslr",
    "what is this weslr project",
    "what kind of system is weslr",
    "purpose of weslr",
    "short version of weslr",
)

_CAPABILITY_KEYWORDS = (
    "what can you do",
    "what are your capabilities",
    "what can weslr do",
    "what kind of help can you give",
    "how do you help",
    "what do you do",
    "what do you help with",
    "what should i ask you",
    "which kinds of questions can you answer",
    "what questions can you answer",
    "what tasks do you handle",
    "how can you support me",
    "what do you do without a model",
)

_TROUBLESHOOTING_KEYWORDS = (
    "troubleshoot",
    "debug",
    "error",
    "fails",
    "broken",
    "not working",
    "won't",
    "timeout",
    "crash",
    "stops immediately",
    "starts and then stops",
    "output empty",
    "why is",
    "parse",
    "flaky",
)

_INVENTION_KEYWORDS = (
    "invent",
    "design",
    "suggest",
    "brainstorm",
    "propose",
    "new idea",
    "create",
    "novel",
    "discover",
    "generate ideas",
)

_AMBIGUOUS_KEYWORDS = (
    "what should i do",
    "help me decide",
    "help me with this",
    "help me with",
    "can you help",
    "can you fix it",
    "make it better",
    "i need advice",
    "best move",
    "not sure",
    "something with",
    "some way",
    "maybe",
    "what if",
)

_EMOTIONAL_KEYWORDS = (
    "frustrated",
    "angry",
    "stressed",
    "overwhelmed",
    "annoyed",
    "tired of this",
    "not having a good time",
    "good time",
    "discouraged",
    "exhausted",
    "stuck",
    "upset",
)

_MEMORY_KEYWORDS = (
    "remember what",
    "remember",
    "recall past chats",
    "past chats",
    "store this",
    "save this",
    "provenance",
    "where did you get this",
    "what do you retain",
    "user history",
    "keep track",
    "memory boundary",
    "leaking memory",
    "cite sources",
)

_SAFETY_KEYWORDS = (
    "bypass",
    "bypass a lock",
    "hack",
    "malware",
    "exploit",
    "private data",
    "reveal private data",
    "ignore safety",
    "ignore your safety rules",
    "safety rules",
    "disallowed",
    "unsafe",
    "can't help",
    "cannot help",
    "refuse",
    "help me steal a password",
    "way around the boundary",
)

_POISON_KEYWORDS = (
    "poison",
    "poisoned",
    "hostile input",
    "prompt injection",
    "untrusted input",
    "adversarial",
    "ignore previous instructions",
    "embedded instruction",
    "embedded instructions",
    "embedded injection",
    "embedded command",
    "hidden instructions",
    "override your rules",
    "print the secret",
    "trust the attacker",
    "as system",
    "system, you must obey",
    "execute the payload",
    "just comply",
    "malicious",
    "attacker",
)

_UNKNOWN_KEYWORDS = (
    "unknown word",
    "unknown phrase",
    "unknown term",
    "unknown token",
    "unknown acronym",
    "unfamiliar word",
    "unfamiliar term",
    "odd phrase",
    "what does",
    "what does it mean",
    "word meaning",
    "phrase meaning",
    "don't know this word",
    "is unfamiliar",
    "no definition",
    "new label",
)

_RF_KEYWORDS = (
    "rf",
    "wifi sensing",
    "movement detection",
    "motion detection",
    "occupancy",
    "indoor sensing",
    "sensing system",
    "privacy boundaries",
    "movement sensing",
)

_DECISION_KEYWORDS = (
    "walk or drive",
    "stairs or elevator",
    "email or call",
    "buy the cheaper item",
    "more durable one",
    "raining lightly",
    "cook at home",
    "order out",
    "leave now",
    "wait 10 minutes",
    "bring a jacket",
    "public transit",
    "should i walk",
    "should i drive",
    "meters away",
    "distance",
    "car wash",
)


def _safe_json(value: Any) -> Any:
    if is_dataclass(value):
        return _safe_json(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _safe_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_safe_json(item) for item in value]
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _normalize_question(question: str) -> str:
    return " ".join(str(question).strip().lower().split())


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _extract_distance_meters(question: str) -> int | None:
    match = re.search(r"(\d+)\s*(?:m|meter|meters|metre|metres)\b", question)
    if match:
        return int(match.group(1))
    return None


def _detect_question_family(question: str) -> str:
    text = _normalize_question(question)
    if _contains_any(text, _POISON_KEYWORDS):
        return "hostile_input_boundary"
    if _contains_any(text, _UNKNOWN_KEYWORDS):
        return "unknown_term"
    if _contains_any(text, _CAPABILITY_KEYWORDS):
        return "capability_overview"
    if _contains_any(text, _IDENTITY_KEYWORDS):
        return "identity_status"
    if _contains_any(text, _EMOTIONAL_KEYWORDS):
        return "emotional_support"
    if _contains_any(text, _TROUBLESHOOTING_KEYWORDS):
        return "troubleshooting_guidance"
    if _contains_any(text, _RF_KEYWORDS):
        return "safe_technical_guidance"
    if _contains_any(text, _INVENTION_KEYWORDS):
        return "invention_guidance"
    if _contains_any(text, _DECISION_KEYWORDS) or _extract_distance_meters(text) is not None:
        return "practical_decision"
    if _contains_any(text, _SAFETY_KEYWORDS):
        return "safety_boundary"
    if _contains_any(text, _AMBIGUOUS_KEYWORDS):
        return "ambiguous_intent"
    if _contains_any(text, _EMOTIONAL_KEYWORDS):
        return "emotional_support"
    if _contains_any(text, _MEMORY_KEYWORDS):
        return "memory_boundary"
    return "bounded_general"


def _build_turn_labels(question: str, family: str) -> tuple[str, ...]:
    labels = [question, _normalize_question(question), family.replace("_", " ")]
    if family == "identity_status":
        labels.extend(["what is weslr", "identity status", "who are you"])
    elif family == "hostile_input_boundary":
        labels.extend(["hostile input", "poison shielding", "boundary handling"])
    elif family == "unknown_term":
        labels.extend(["unknown word", "unknown phrase", "bounded uncertainty"])
    elif family == "safe_technical_guidance":
        labels.extend(["teaching explanation", "safe technical guidance", "bounded uncertainty"])
    elif family == "practical_decision":
        labels.extend(["task workflow", "direct bounded answer", "bounded decision"])
    elif family == "capability_overview":
        labels.extend(["capability overview", "help summary", "direct bounded answer"])
    elif family == "troubleshooting_guidance":
        labels.extend(["troubleshooting guidance", "debugging flow", "stepwise plan"])
    elif family == "invention_guidance":
        labels.extend(["invention guidance", "creative guidance", "teaching explanation"])
    elif family == "ambiguous_intent":
        labels.extend(["clarifying question", "clarification request", "bounded uncertainty"])
    elif family == "emotional_support":
        labels.extend(["relationship feedback", "supportive response", "direct bounded answer"])
    elif family == "memory_boundary":
        labels.extend(["memory honesty", "continuity recap", "provenance boundary"])
    elif family == "safety_boundary":
        labels.extend(["refusal boundary", "safe alternative", "boundary answer"])
    else:
        labels.extend(["bounded answer", "direct answer"])
    deduped: list[str] = []
    seen: set[str] = set()
    for label in labels:
        value = " ".join(str(label).strip().lower().split())
        if value and value not in seen:
            seen.add(value)
            deduped.append(value)
    return tuple(deduped)


def _build_context_signals(question: str, family: str) -> dict[str, Any]:
    text = _normalize_question(question)
    distance_meters = _extract_distance_meters(text)
    hostile = _contains_any(text, _POISON_KEYWORDS)
    unknown = _contains_any(text, _UNKNOWN_KEYWORDS)
    identity = _contains_any(text, _IDENTITY_KEYWORDS)
    safe_tech = _contains_any(text, _RF_KEYWORDS)
    practical = _contains_any(text, _DECISION_KEYWORDS) or distance_meters is not None
    capability = _contains_any(text, _CAPABILITY_KEYWORDS)
    troubleshooting = _contains_any(text, _TROUBLESHOOTING_KEYWORDS)
    invention = _contains_any(text, _INVENTION_KEYWORDS)
    ambiguous = _contains_any(text, _AMBIGUOUS_KEYWORDS)
    emotional = _contains_any(text, _EMOTIONAL_KEYWORDS)
    memory = _contains_any(text, _MEMORY_KEYWORDS)
    safety = _contains_any(text, _SAFETY_KEYWORDS)
    return {
        "question_family": family,
        "identity_question": identity,
        "capability_question": capability,
        "troubleshooting_question": troubleshooting,
        "invention_question": invention,
        "hostile_input_signal": hostile,
        "unknown_word_signal": unknown,
        "safe_technical_signal": safe_tech,
        "practical_decision_signal": practical,
        "ambiguous_intent_signal": ambiguous,
        "emotional_support_signal": emotional,
        "memory_boundary_signal": memory,
        "safety_boundary_signal": safety,
        "distance_meters": distance_meters,
        "state_question": identity,
        "unsafe_automation": hostile,
        "evidence_needed": safe_tech or practical or troubleshooting,
    }


def _unique_values(*groups: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for group in groups:
        if group is None:
            continue
        if isinstance(group, str):
            items = [group]
        else:
            try:
                items = list(group)
            except TypeError:
                items = [group]
        for item in items:
            if item is None:
                continue
            value = str(item).strip()
            if value and value.lower() != "none" and value not in seen:
                seen.add(value)
                out.append(value)
    return out


def _family_to_answer_direction(family: str) -> str:
    mapping = {
        "identity_status": "bounded_identity_summary",
        "capability_overview": "capability_overview_answer",
        "practical_decision": "practical_decision_answer",
        "troubleshooting_guidance": "troubleshooting_guidance_answer",
        "invention_guidance": "invention_guidance_answer",
        "safe_technical_guidance": "safe_technical_guidance",
        "unknown_term": "unknown_term_handling",
        "hostile_input_boundary": "hostile_input_boundary_handling",
        "ambiguous_intent": "ambiguous_intent_clarification",
        "emotional_support": "emotional_support_answer",
        "memory_boundary": "memory_boundary_answer",
        "safety_boundary": "safety_boundary_refusal",
    }
    return mapping.get(family, "bounded_general_answer")


def _compose_answer_text(question: str, family: str, context: Mapping[str, Any]) -> str:
    text = _normalize_question(question)
    distance_meters = context.get("distance_meters")
    if family == "identity_status":
        return (
            "WESLR is a deterministic, governed assistant stack in this repo. "
            "It routes questions through local helper modules, builds bounded answer packets, "
            "and renders no-model answers as a local proof path."
        )
    if family == "capability_overview":
        return (
            "I can help with bounded reasoning, summaries, planning, troubleshooting, explanations, and careful next steps. "
            "I stay local here: no provider calls, no runtime wiring, and no unsupported claims."
        )
    if family == "practical_decision":
        if isinstance(distance_meters, int) and distance_meters <= 100:
            return (
                f"Concrete advice: at about {distance_meters} meters, walking is the default choice unless you have baggage, access, "
                "mobility, weather, or parking reasons to drive. For a short hop like this, walk unless a concrete constraint says otherwise."
            )
        return (
            "Concrete advice: if the trip is very short, walking is usually the simpler choice; drive only when carrying items, accessibility, "
            "weather, or time constraints make that better."
        )
    if family == "safe_technical_guidance":
        return (
            "Use RF/WiFi sensing at a coarse, consent-based, local-processing level: detect motion or occupancy, not identity; "
            "keep retention minimal; calibrate on synthetic or test data; and avoid covert tracking or unnecessary personal profiling."
        )
    if family == "troubleshooting_guidance":
        return (
            "Start with the smallest failing layer: capture the exact error, reproduce it with the fewest moving parts, "
            "check recent changes, isolate inputs, and compare a known-good path with the broken one."
        )
    if family == "invention_guidance":
        return (
            "I can propose a few safe, bounded ideas and a way to test them lightly, but I won't claim validated proof. "
            "Pick the simplest option, define success criteria, and run a small reviewable experiment."
        )
    if family == "unknown_term":
        return (
            "Treat the term as unknown, preserve uncertainty, and ask for context or a glossary before guessing. "
            "If it keeps appearing, add it to a local term map with provenance and a short human-reviewed definition."
        )
    if family == "hostile_input_boundary":
        return (
            "Treat hostile input as untrusted: quarantine it, strip any authority claims, never execute its instructions, and only use it as a signal for boundary handling. "
            "Prefer local review, provenance checks, and the smallest safe next step."
        )
    if family == "ambiguous_intent":
        return (
            "I need one more detail to be precise, but the safest first read is: identify the likely intent, state the assumption, and ask one short clarifying question. "
            "If you want, I can also give a provisional answer under that assumption."
        )
    if family == "emotional_support":
        return (
            "That sounds frustrating. Keep the next step small: identify the exact failure point, take a short pause if needed, and then try one concrete check at a time."
        )
    if family == "memory_boundary":
        return (
            "I don't have unrestricted long-term memory here. I can use the current conversation and repo context, but I should be explicit about what I am inferring and where the information came from."
        )
    if family == "safety_boundary":
        return (
            "I have to refuse that unsafe or disallowed request, but I can help with a safer alternative, a defensive review, or a bounded explanation of the risk."
        )
    if _contains_any(text, ("what is weslr", "who are you", "what are you")):
        return (
            "WESLR here is the local WESLR codebase and helper stack: deterministic, governed, and no-model by default. "
            "This composer is using implemented modules to build a bounded answer packet, not a hosted model call."
        )
    return (
        "I can give a bounded answer, but I need to stay conservative: use the implemented helpers, note uncertainty, and avoid unsupported claims."
    )


def _build_observations(question: str, family: str, route_summary: Mapping[str, Any], poison_summary: Mapping[str, Any], friction_summary: Mapping[str, Any]) -> list[str]:
    observations = [
        f"question_family={family}",
        f"route={route_summary.get('selected_route_id', 'unknown')}",
        f"route_family={route_summary.get('route_family', 'unknown')}",
        f"poison_classification={poison_summary.get('classification_label', 'unknown')}",
    ]
    if poison_summary.get("risk_labels"):
        observations.append(f"risk_labels={','.join(poison_summary['risk_labels'])}")
    if friction_summary.get("friction_level"):
        observations.append(f"friction_level={friction_summary.get('friction_level')}")
    distance_meters = _extract_distance_meters(question)
    if distance_meters is not None:
        observations.append(f"distance_meters={distance_meters}")
    if family == "safe_technical_guidance":
        observations.append("topic=privacy_preserving_sensing")
    if family == "unknown_term":
        observations.append("topic=unknown_term_handling")
    if family == "hostile_input_boundary":
        observations.append("topic=boundary_handling")
    return observations


def _build_safety_limits(poison_summary: Mapping[str, Any], route_summary: Mapping[str, Any]) -> list[str]:
    limits = [
        "no provider/model calls",
        "no chat_responder/respond_chat calls",
        "no runtime website wiring",
        "no .weslr state writes",
        "deterministic local helper stack only",
        "json-safe structured output only",
    ]
    if poison_summary.get("blocked"):
        limits.append("input treated as untrusted by poison shield")
    if route_summary.get("needs_clarification"):
        limits.append("selector was conservative; composer may still answer boundedly")
    return limits


def build_level3_answer_packet_v1(question: str, context_signals: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(question, str):
        raise TypeError("question must be a string")
    normalized_question = _normalize_question(question)
    if not normalized_question:
        raise ValueError("question must not be empty")

    family = _detect_question_family(normalized_question)
    turn_labels = _build_turn_labels(normalized_question, family)
    derived_context = _build_context_signals(normalized_question, family)
    if context_signals:
        derived_context.update({str(key): value for key, value in context_signals.items()})

    capability_route = route_request(normalized_question, context=derived_context)
    response_packet = select_response_route_v1(turn_labels, derived_context)
    candidate_packet = form_candidate_responses_v1(turn_labels, derived_context)
    method_catalog = build_answer_method_catalog_v1()
    shape_catalog = build_answer_shape_catalog_v1()
    method_candidates = select_methods_for_turn_v1(turn_labels, derived_context)
    shape_candidates = select_answer_shapes_v1(turn_labels, derived_context)
    friction_request = {
        "turn_labels": list(turn_labels),
        "context_signals": dict(derived_context),
        "source_label": DEFAULT_SOURCE_LABEL_V1,
    }
    friction_packet = route_unknown_prompt_friction_v1(turn_labels, derived_context)
    poison_request = build_poison_shield_scan_request_v1(
        scan_request_id="level3-answer-composer-scan",
        source_class="user_message",
        content_class="plain_question",
        source_label=DEFAULT_SOURCE_LABEL_V1,
        source_trust_level="direct",
        content_summary=normalized_question,
        content_excerpt=normalized_question,
        instruction_like_text_present=_contains_any(normalized_question, _POISON_KEYWORDS),
        authority_claim_present=False,
        memory_write_requested=False,
        tool_use_requested=False,
        source_trust_claim_present=False,
        cross_user_or_project_claim_present=False,
        image_or_ocr_source=False,
        hostile_source_known=_contains_any(normalized_question, _POISON_KEYWORDS),
        user_intent_present=True,
        operator_approval_present=False,
        safe_evidence_extraction_requested=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        learning_claimed=False,
        safe_metadata={"composer_type": COMPOSER_TYPE_V1},
    )
    poison_result = classify_adversarial_content_v1(poison_request)
    raw_packet = build_raw_signal_cartography_packet_v1(
        {
            "content_summary": normalized_question,
            "source_ref": "level3_answer_composer",
            "question_family": family,
        }
    )

    route_summary = {
        "selected_route_id": response_packet.selected_route_id,
        "selected_method_id": response_packet.selected_method_id,
        "selected_shape_id": response_packet.selected_shape_id,
        "selected_case_id": response_packet.selected_case_id,
        "route_family": family,
        "route_confidence": response_packet.route_confidence,
        "needs_clarification": response_packet.needs_clarification,
        "needs_evidence": response_packet.needs_evidence,
        "needs_owner_approval": response_packet.needs_owner_approval,
        "blocked": response_packet.blocked,
        "blocked_labels": list(response_packet.blocked_labels),
    }
    candidate_summary = {
        "selected_candidate_id": candidate_packet.selected_candidate_id,
        "candidate_family": candidate_packet.candidate_family,
        "blocked": candidate_packet.blocked,
        "needs_clarification": candidate_packet.needs_clarification,
        "needs_evidence": candidate_packet.needs_evidence,
        "needs_owner_approval": candidate_packet.needs_owner_approval,
        "blocked_labels": list(candidate_packet.blocked_labels),
        "proposed_answer_policy": candidate_packet.proposed_answer_policy,
    }
    friction_summary = _safe_json(summarize_unknown_prompt_friction_packet_v1(friction_packet))
    poison_summary = _safe_json(summarize_poison_shield_result_v1(poison_result))
    raw_summary = _safe_json(summarize_raw_signal_cartography_packet_v1(raw_packet))
    no_model_packet = render_no_model_bounded_answer_v1(turn_labels, derived_context)
    no_model_summary = _safe_json(summarize_no_model_bounded_render_packet_v1(no_model_packet))

    selected_capability_families = _unique_values(
        [family],
        [route_summary.get("route_family")],
        [candidate_summary.get("candidate_family")],
        [raw_summary.get("classification", {}).get("engine_family")],
        ["boundary_uncertainty"] if family in {"unknown_term", "hostile_input_boundary"} else [],
        ["capability_overview"] if family == "capability_overview" else [],
        ["debugging_flow"] if family == "troubleshooting_guidance" else [],
        ["creative_guidance"] if family == "invention_guidance" else [],
        ["teaching_explanation_discovery"] if family in {"safe_technical_guidance", "invention_guidance"} else [],
        ["task_workflow"] if family == "practical_decision" else [],
        ["clarification_flow"] if family == "ambiguous_intent" else [],
        ["supportive_response"] if family == "emotional_support" else [],
        ["memory_honesty"] if family == "memory_boundary" else [],
        ["refusal_boundary"] if family == "safety_boundary" else [],
    )

    answer_direction = _family_to_answer_direction(family)
    answer_text = _compose_answer_text(normalized_question, family, derived_context)
    observations = _build_observations(normalized_question, family, route_summary, poison_summary, friction_summary)
    safety_limits = _build_safety_limits(poison_summary, route_summary)

    packet = {
        "composer_type": COMPOSER_TYPE_V1,
        "question": question,
        "normalized_question": normalized_question,
        "question_family": family,
        "selected_capability_families": selected_capability_families,
        "observations": observations,
        "inferred_answer_direction": answer_direction,
        "safety_provenance_limits": safety_limits,
        "final_answer_text": answer_text,
        "module_registry": {
            "executed_modules": list(SAFE_MODULE_REGISTRY_V1),
            "catalog_counts": {
                "answer_method_families": len(method_catalog.families),
                "answer_methods": len(method_catalog.methods),
                "answer_shapes": len(shape_catalog.shapes),
                "selected_method_candidates": len(method_candidates),
                "selected_shape_candidates": len(shape_candidates),
            },
        },
        "module_signals": {
            "capability_router": _safe_json(capability_route),
            "response_method_selector": route_summary,
            "candidate_response_formation": candidate_summary,
            "unknown_prompt_friction_router": friction_summary,
            "poison_shield": poison_summary,
            "raw_signal_cartographer": raw_summary,
            "no_model_bounded_renderer": no_model_summary,
        },
        "rendering": {
            "markdown": render_level3_answer_composer_markdown_v1,
            "json_safe": True,
        },
        "blocked": False,
        "source_provenance": {
            "answer_selector_json_safe": to_response_selection_json_safe_v1(response_packet),
        },
    }
    return packet


def to_level3_answer_composer_json_safe_v1(packet: Any) -> dict[str, Any]:
    return _safe_json(packet)


def render_level3_answer_composer_markdown_v1(packet: Any) -> str:
    data = _safe_json(packet)
    answer_text = str(data.get("final_answer_text", "")).strip()
    question = str(data.get("question", "")).strip()
    families = ", ".join(data.get("selected_capability_families", []))
    observations = data.get("observations", [])
    limits = data.get("safety_provenance_limits", [])
    lines = [
        "# Level 3 WESLR answer",
        f"**Question:** {question}",
        f"**Selected families:** {families}",
        "",
        "**Observations:**",
    ]
    lines.extend(f"- {item}" for item in observations)
    lines.extend([
        "",
        "**Safety / provenance limits:**",
    ])
    lines.extend(f"- {item}" for item in limits)
    lines.extend([
        "",
        "**Answer:**",
        answer_text,
    ])
    return "\n".join(lines).strip() + "\n"


def compose_level3_answer_v1(question: str, context_signals: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return build_level3_answer_packet_v1(question, context_signals=context_signals)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compose a local no-model WESLR answer packet")
    parser.add_argument("question", nargs="+", help="Plain user question")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    args = parser.parse_args(argv)
    question = " ".join(args.question)
    packet = compose_level3_answer_v1(question)
    if args.json:
        print(json.dumps(to_level3_answer_composer_json_safe_v1(packet), ensure_ascii=False, indent=2))
    else:
        print(render_level3_answer_composer_markdown_v1(packet), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
