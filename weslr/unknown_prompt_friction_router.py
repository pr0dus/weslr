"""Metadata-only unknown prompt friction router v1.

This module performs a fast pre-answer self-check for unknown words, intent,
capability gaps, evidence needs, continuity needs, relationship/correction
signals, language discovery signals, and boundary/approval friction.

It is pure, deterministic, and fail-closed.
No final prose generation. No model/provider calls. No state writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from weslr.response_method_selector import (
    select_response_route_v1,
    summarize_response_selection_packet_v1,
)

PACKET_TYPE_V1 = "unknown_prompt_friction_router_v1"
SUMMARY_TYPE_V1 = "unknown_prompt_friction_summary_v1"
ROUTE_TYPE_V1 = "unknown_prompt_friction_route_v1"
SIGNAL_TYPE_V1 = "unknown_prompt_friction_signal_v1"

FRICTION_LEVELS_V1 = {"none", "low", "medium", "high", "blocked"}
RESPONSE_POLICIES_V1 = {
    "answer_directly_bounded",
    "ask_clarifying_question",
    "state_bounded_uncertainty",
    "request_evidence",
    "give_partial_supported_answer",
    "route_unknown_friction",
    "route_language_discovery_explanation",
    "route_capability_orientation",
    "route_memory_honesty",
    "route_continuity_recap",
    "route_correction_repair",
    "route_relationship_feedback",
    "route_conflict_contradiction",
    "escalate_to_owner_review",
    "refuse_with_boundary",
}

_ALLOWED_CONTEXT_KEYS_V1 = {
    "known_terms",
    "unknown_terms",
    "ambiguous_terms",
    "known_intent",
    "unknown_intent",
    "capability_known",
    "unknown_capability",
    "memory_available",
    "memory_unclear",
    "continuity_needed",
    "evidence_available",
    "evidence_needed",
    "relationship_signal",
    "correction_signal",
    "contradiction_signal",
    "friction_signal",
    "repeated_failure_signal",
    "language_signal",
    "grammar_signal",
    "vocabulary_signal",
    "future_capability_signal",
    "unsafe_signal",
    "needs_owner_approval",
    "public_mode",
    "model_available",
}

_KNOWN_ROUTE_IDS_V1 = {
    "identity_status_route",
    "memory_honesty_route",
    "continuity_route",
    "capability_orientation_route",
    "clarification_route",
    "uncertainty_route",
    "refusal_boundary_route",
    "evidence_needed_route",
    "partial_supported_route",
    "ordinary_task_route",
    "implementation_planning_route",
    "workflow_next_lane_route",
    "governance_escalation_route",
    "teaching_explanation_route",
    "language_discovery_route",
    "scientific_discovery_route",
    "benchmark_evaluation_route",
    "unknown_word_phrase_route",
    "unknown_intent_route",
    "unknown_capability_route",
    "friction_repeated_failure_route",
    "relationship_feedback_route",
    "correction_repair_route",
    "conflict_contradiction_route",
    "non_canned_specificity_route",
    "directness_concern_route",
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class UnknownPromptFrictionSignal:
    signal_family: str
    source: str
    evidence: tuple[str, ...] = field(default_factory=tuple)
    strength: float = 0.0
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class UnknownPromptFrictionRoute:
    route_id: str
    method_id: str
    shape_id: str
    case_id: str
    response_policy: str
    friction_level: str
    reason: str
    blocked: bool


@dataclass(frozen=True, slots=True)
class UnknownPromptFrictionSummary:
    packet_type: str
    friction_level: str
    response_policy: str
    route_id: str
    blocked: bool
    friction_detected: bool
    unknown_detected: bool
    signal_family_count: int
    friction_label_count: int
    unknown_label_count: int


@dataclass(frozen=True, slots=True)
class UnknownPromptFrictionPacket:
    packet_type: str
    turn_labels: list[str]
    safe_context_signal_keys: list[str]
    friction_detected: bool
    unknown_detected: bool
    friction_level: str
    friction_labels: list[str]
    unknown_labels: list[str]
    detected_signal_families: list[str]
    recommended_route_id: str
    recommended_method_id: str
    recommended_shape_id: str
    recommended_case_id: str
    response_policy: str
    needs_clarification: bool
    needs_evidence: bool
    needs_owner_approval: bool
    blocked: bool
    blocked_labels: list[str]
    selector_packet_summary: Dict[str, Any]
    safe_metadata: Dict[str, Any]
    runtime_authority: bool = False
    model_provider_used: bool = False
    generates_final_text: bool = False
    writes_state: bool = False
    detected_signals: tuple[UnknownPromptFrictionSignal, ...] = field(default_factory=tuple)
    route: Optional[UnknownPromptFrictionRoute] = None


def _dedupe_preserve(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _truthy(value: Any) -> bool:
    return bool(value is True or value == 1 or str(value).strip().lower() in {"true", "yes", "1", "on"})


def _normalize_labels(turn_labels: Any) -> list[str]:
    if turn_labels is None:
        return []
    if isinstance(turn_labels, str):
        values = [turn_labels]
    elif isinstance(turn_labels, Mapping):
        values = [str(v) for v in turn_labels.values()]
    else:
        try:
            values = [str(v) for v in turn_labels]
        except TypeError:
            values = [str(turn_labels)]
    normalized: list[str] = []
    for value in values:
        label = _safe_text(value).lower().replace("_", " ").replace("/", " ").replace("-", " ")
        if label:
            normalized.append(" ".join(label.split()))
    return _dedupe_preserve(normalized)


def _normalize_context_signals(context_signals: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not context_signals:
        return {}
    if not isinstance(context_signals, Mapping):
        return {}
    return {str(key): value for key, value in context_signals.items()}


def _safe_context_signal_keys(context_signals: Mapping[str, Any]) -> list[str]:
    keys = [key for key in context_signals.keys() if key in _ALLOWED_CONTEXT_KEYS_V1]
    return sorted(_dedupe_preserve(keys))


def _contains_any(blob: str, phrases: Sequence[str]) -> bool:
    return any(phrase in blob for phrase in phrases)


def _contains_any_label(labels: Sequence[str], phrases: Sequence[str]) -> bool:
    blob = " ".join(labels)
    return _contains_any(blob, phrases)


def _route_ids(route_id: str) -> tuple[str, str, str]:
    if not route_id.endswith("_route"):
        raise ValidationError(f"unsupported route_id: {route_id}")
    base = route_id[: -len("_route")]
    return f"method_{base}", f"shape_{base}", f"case_{base}"


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_safe_text)]
    return value


def _signal(
    signal_family: str,
    source: str,
    evidence: Iterable[str],
    strength: float = 0.5,
    notes: Iterable[str] = (),
) -> UnknownPromptFrictionSignal:
    return UnknownPromptFrictionSignal(
        signal_family=signal_family,
        source=source,
        evidence=tuple(_dedupe_preserve(_safe_text(item) for item in evidence if _safe_text(item))),
        strength=float(strength),
        notes=tuple(_dedupe_preserve(_safe_text(item) for item in notes if _safe_text(item))),
    )


def _select_policy(
    families: list[str],
    labels: list[str],
    context_signals: Mapping[str, Any],
    selector_route_id: str,
) -> tuple[str, str, bool, bool, bool, bool, str, bool]:
    blob = " ".join(labels)

    has_unsafe = "unsafe_or_unauthorized" in families
    has_owner_approval = "needs_owner_approval" in families or _truthy(context_signals.get("needs_owner_approval"))
    has_public_boundary = "public_mode_boundary" in families
    has_provider_boundary = "provider_boundary" in families
    has_unknown_capability = "unknown_capability_request" in families
    has_unknown_intent = "unknown_intent" in families
    has_unknown_word = "unknown_word_or_phrase" in families
    has_missing_evidence = "missing_evidence" in families
    has_memory_uncertainty = "memory_uncertainty" in families
    has_continuity = "continuity_needed" in families
    has_relationship = "relationship_feedback" in families
    has_correction = "correction_repair" in families
    has_contradiction = "conflict_contradiction" in families
    has_language = "language_grammar_vocabulary" in families
    has_future = "future_capability" in families
    has_repeated_failure = "repeated_failure" in families
    has_missing_context = "missing_context" in families

    if has_unsafe:
        if has_owner_approval or has_public_boundary:
            return "escalate_to_owner_review", "governance_escalation_route", False, False, True, True, "unsafe boundary requires owner review", True
        return "refuse_with_boundary", "refusal_boundary_route", False, False, False, True, "unsafe or unauthorized boundary", True
    if has_owner_approval or has_public_boundary:
        return "escalate_to_owner_review", "governance_escalation_route", False, False, True, True, "owner approval or public boundary", True
    if has_provider_boundary:
        return "route_capability_orientation", "capability_orientation_route", False, False, False, False, "provider boundary", False
    if has_unknown_capability:
        return "route_unknown_friction", "unknown_capability_route", False, False, False, True, "unknown capability request", True
    if has_unknown_intent:
        return "route_unknown_friction", "unknown_intent_route", False, False, False, True, "unknown intent", True
    if has_unknown_word:
        return "route_unknown_friction", "unknown_word_phrase_route", False, False, False, True, "unknown word or phrase", True
    if has_missing_evidence:
        return "request_evidence", "evidence_needed_route", True, True, False, True, "missing evidence", True
    if has_memory_uncertainty:
        return "route_memory_honesty", "memory_honesty_route", False, False, False, False, "memory uncertainty", False
    if has_continuity:
        return "route_continuity_recap", "continuity_route", False, False, False, False, "continuity needed", False
    if has_relationship:
        return "route_relationship_feedback", "relationship_feedback_route", False, False, False, False, "relationship feedback", False
    if has_correction:
        return "route_correction_repair", "correction_repair_route", False, False, False, False, "correction repair", False
    if has_contradiction:
        return "route_conflict_contradiction", "conflict_contradiction_route", False, False, False, False, "conflict or contradiction", False
    if has_language:
        return "route_language_discovery_explanation", "language_discovery_route", False, False, False, False, "language / grammar / vocabulary signal", False
    if has_future:
        return "route_capability_orientation", "capability_orientation_route", False, False, False, False, "future capability signal", False
    if has_repeated_failure:
        return "route_unknown_friction", "friction_repeated_failure_route", False, False, False, True, "repeated failure or friction", True
    if has_missing_context:
        return "ask_clarifying_question", "clarification_route", True, False, False, True, "missing context", True

    # Default: let the selector baseline stand.
    route_id = selector_route_id if selector_route_id in _KNOWN_ROUTE_IDS_V1 else "clarification_route"
    if route_id in {
        "clarification_route",
        "evidence_needed_route",
        "unknown_word_phrase_route",
        "unknown_intent_route",
        "unknown_capability_route",
        "friction_repeated_failure_route",
        "refusal_boundary_route",
        "governance_escalation_route",
    }:
        policy = {
            "clarification_route": "ask_clarifying_question",
            "evidence_needed_route": "request_evidence",
            "unknown_word_phrase_route": "route_unknown_friction",
            "unknown_intent_route": "route_unknown_friction",
            "unknown_capability_route": "route_unknown_friction",
            "friction_repeated_failure_route": "route_unknown_friction",
            "refusal_boundary_route": "refuse_with_boundary",
            "governance_escalation_route": "escalate_to_owner_review",
        }[route_id]
        blocked = policy in {"ask_clarifying_question", "request_evidence", "route_unknown_friction", "refuse_with_boundary", "escalate_to_owner_review"}
        return policy, route_id, policy == "request_evidence", policy == "ask_clarifying_question", False, blocked, "selector baseline route", False

    return "answer_directly_bounded", route_id, False, False, False, False, "selector baseline route", False


def _friction_level_from_policy(policy: str, blocked: bool, families: list[str]) -> str:
    if blocked:
        return "blocked"
    if policy in {
        "route_unknown_friction",
        "ask_clarifying_question",
        "request_evidence",
        "refuse_with_boundary",
        "escalate_to_owner_review",
    }:
        return "high"
    if policy in {
        "route_memory_honesty",
        "route_continuity_recap",
        "route_relationship_feedback",
        "route_correction_repair",
        "route_conflict_contradiction",
        "route_language_discovery_explanation",
        "route_capability_orientation",
        "state_bounded_uncertainty",
        "give_partial_supported_answer",
    }:
        return "medium"
    if families:
        return "low"
    return "none"


def _detect_families(labels: list[str], context_signals: Mapping[str, Any]) -> tuple[list[str], list[str], list[str], list[UnknownPromptFrictionSignal]]:
    blob = " ".join(labels)
    families: list[str] = []
    friction_labels: list[str] = []
    unknown_labels: list[str] = []
    signals: list[UnknownPromptFrictionSignal] = []

    def add(family: str, source: str, evidence: Iterable[str], strength: float = 0.5, notes: Iterable[str] = ()) -> None:
        if family not in families:
            families.append(family)
        signal = _signal(family, source, evidence, strength=strength, notes=notes)
        signals.append(signal)
        for item in signal.evidence:
            if family.startswith("unknown_") or family == "future_capability":
                unknown_labels.append(item)
            else:
                friction_labels.append(item)

    unsafe_labels = [label for label in labels if _contains_any(label, ["unsafe", "unauthorized", "not allowed", "privacy", "private", "secret", "forbidden"])]
    if _truthy(context_signals.get("unsafe_signal")) or unsafe_labels:
        add("unsafe_or_unauthorized", "context_signals" if _truthy(context_signals.get("unsafe_signal")) else "turn_labels", unsafe_labels or ["unsafe signal"], strength=0.95)

    owner_labels = [label for label in labels if _contains_any(label, ["approval", "approve", "owner", "escalate", "operator review", "blocked"])]
    if _truthy(context_signals.get("needs_owner_approval")) or owner_labels:
        add("needs_owner_approval", "context_signals" if _truthy(context_signals.get("needs_owner_approval")) else "turn_labels", owner_labels or ["needs owner approval"], strength=0.9)

    if _truthy(context_signals.get("public_mode")) or _contains_any_label(labels, ["public mode", "public", "publish", "external"]):
        add("public_mode_boundary", "context_signals" if _truthy(context_signals.get("public_mode")) else "turn_labels", ["public mode"], strength=0.85)

    provider_available_present = "model_available" in context_signals
    provider_hit = (provider_available_present and _truthy(context_signals.get("model_available")) is False) or _contains_any_label(labels, ["model", "provider", "runtime", "search", "advisor"])
    if provider_hit:
        add("provider_boundary", "context_signals" if (provider_available_present and _truthy(context_signals.get("model_available")) is False) else "turn_labels", ["provider boundary"], strength=0.75)

    unknown_capability_labels = [label for label in labels if _contains_any(label, ["unknown capability", "capability unknown", "what can you do", "can you do", "what are you able", "future capability"]) ]
    capability_known_present = "capability_known" in context_signals
    if _truthy(context_signals.get("unknown_capability")) or (capability_known_present and _truthy(context_signals.get("capability_known")) is False and (unknown_capability_labels or _contains_any_label(labels, ["capability", "can you"]))):
        add("unknown_capability_request", "context_signals" if _truthy(context_signals.get("unknown_capability")) else "turn_labels", unknown_capability_labels or ["unknown capability"], strength=0.92)

    unknown_intent_labels = [label for label in labels if _contains_any(label, ["unknown intent", "unclear intent", "ambiguous intent", "what do you mean", "intent unknown"])]
    if _truthy(context_signals.get("unknown_intent")) or unknown_intent_labels:
        add("unknown_intent", "context_signals" if _truthy(context_signals.get("unknown_intent")) else "turn_labels", unknown_intent_labels or ["unknown intent"], strength=0.9)

    unknown_word_labels = [label for label in labels if _contains_any(label, ["unknown word", "unknown phrase", "what does this mean", "word meaning", "phrase meaning"])]
    if _safe_text(context_signals.get("unknown_terms")) or unknown_word_labels:
        add("unknown_word_or_phrase", "context_signals" if _safe_text(context_signals.get("unknown_terms")) else "turn_labels", unknown_word_labels or ["unknown word/phrase"], strength=0.9)

    explicit_missing_context = _truthy(context_signals.get("ambiguous_terms")) or _truthy(context_signals.get("unknown_terms"))
    if "known_terms" in context_signals and _truthy(context_signals.get("known_terms")) is False:
        explicit_missing_context = True
    missing_context_labels = [label for label in labels if _contains_any(label, ["clarify", "clarification", "ambiguous", "unclear", "missing", "need more info"])]
    if explicit_missing_context or missing_context_labels:
        add("missing_context", "context_signals" if explicit_missing_context else "turn_labels", missing_context_labels or ["missing context"], strength=0.65)

    evidence_available_present = "evidence_available" in context_signals
    if _truthy(context_signals.get("evidence_needed")) or (evidence_available_present and _truthy(context_signals.get("evidence_available")) is False) or _contains_any_label(labels, ["evidence", "source", "proof", "verify", "latest", "current"]):
        add("missing_evidence", "context_signals" if _truthy(context_signals.get("evidence_needed")) or (evidence_available_present and _truthy(context_signals.get("evidence_available")) is False) else "turn_labels", ["evidence needed"], strength=0.8)

    memory_available_present = "memory_available" in context_signals
    if _truthy(context_signals.get("memory_unclear")) or (memory_available_present and _truthy(context_signals.get("memory_available")) is False) or _contains_any_label(labels, ["memory", "remember", "recall", "do you remember"]):
        add("memory_uncertainty", "context_signals" if _truthy(context_signals.get("memory_unclear")) or (memory_available_present and _truthy(context_signals.get("memory_available")) is False) else "turn_labels", ["memory"], strength=0.72)

    if _truthy(context_signals.get("continuity_needed")) or _contains_any_label(labels, ["continuity", "follow up", "thread", "where we left off", "previous point", "what were we doing"]):
        add("continuity_needed", "context_signals" if _truthy(context_signals.get("continuity_needed")) else "turn_labels", ["continuity"], strength=0.7)

    if _truthy(context_signals.get("relationship_signal")) or _contains_any_label(labels, ["relationship", "feedback", "tone", "trust", "preference", "frustrated"]):
        add("relationship_feedback", "context_signals" if _truthy(context_signals.get("relationship_signal")) else "turn_labels", ["relationship"], strength=0.72)

    if _truthy(context_signals.get("correction_signal")) or _contains_any_label(labels, ["correction", "actually", "wrong", "revise", "fix", "repair"]):
        add("correction_repair", "context_signals" if _truthy(context_signals.get("correction_signal")) else "turn_labels", ["correction"], strength=0.74)

    if _truthy(context_signals.get("contradiction_signal")) or _contains_any_label(labels, ["conflict", "contradiction", "inconsistent", "both true", "clash"]):
        add("conflict_contradiction", "context_signals" if _truthy(context_signals.get("contradiction_signal")) else "turn_labels", ["contradiction"], strength=0.8)

    if _truthy(context_signals.get("language_signal")) or _truthy(context_signals.get("grammar_signal")) or _truthy(context_signals.get("vocabulary_signal")) or _contains_any_label(labels, ["language", "grammar", "vocabulary", "translation", "word", "phrase"]):
        add("language_grammar_vocabulary", "context_signals" if (_truthy(context_signals.get("language_signal")) or _truthy(context_signals.get("grammar_signal")) or _truthy(context_signals.get("vocabulary_signal"))) else "turn_labels", ["language"], strength=0.76)

    if _truthy(context_signals.get("future_capability_signal")) or _contains_any_label(labels, ["future capability", "future", "later", "eventually", "could you do", "one day"]):
        add("future_capability", "context_signals" if _truthy(context_signals.get("future_capability_signal")) else "turn_labels", ["future capability"], strength=0.66)

    if _truthy(context_signals.get("repeated_failure_signal")) or _truthy(context_signals.get("friction_signal")) or _contains_any_label(labels, ["repeated failure", "friction", "stuck", "keeps failing", "blocked"]):
        add("repeated_failure", "context_signals" if _truthy(context_signals.get("repeated_failure_signal")) or _truthy(context_signals.get("friction_signal")) else "turn_labels", ["repeated failure"], strength=0.85)

    # Keep families deterministic and ordered by first detection.
    families = _dedupe_preserve(families)
    friction_labels = _dedupe_preserve(friction_labels)
    unknown_labels = _dedupe_preserve(unknown_labels)
    return families, friction_labels, unknown_labels, signals


def build_unknown_prompt_friction_packet_v1(turn_labels: Any, context_signals: Optional[Mapping[str, Any]] = None) -> UnknownPromptFrictionPacket:
    normalized_labels = _normalize_labels(turn_labels)
    normalized_context_signals = _normalize_context_signals(context_signals)
    safe_keys = _safe_context_signal_keys(normalized_context_signals)

    selector_packet = select_response_route_v1(normalized_labels, normalized_context_signals)
    selector_summary = summarize_response_selection_packet_v1(selector_packet)

    families, friction_labels, unknown_labels, signals = _detect_families(normalized_labels, normalized_context_signals)
    policy, route_id, needs_evidence, needs_clarification, needs_owner_approval, blocked, reason, used_override = _select_policy(
        families,
        normalized_labels,
        normalized_context_signals,
        selector_summary.get("route_id", "clarification_route"),
    )

    method_id, shape_id, case_id = _route_ids(route_id)

    # If selector and router disagree but selector has a safer concrete route,
    # preserve its summary and keep the recommended route metadata explicit.
    route = UnknownPromptFrictionRoute(
        route_id=route_id,
        method_id=method_id,
        shape_id=shape_id,
        case_id=case_id,
        response_policy=policy,
        friction_level=_friction_level_from_policy(policy, blocked, families),
        reason=reason,
        blocked=blocked,
    )

    friction_level = route.friction_level
    friction_detected = bool(families or friction_labels)
    unknown_detected = any(family.startswith("unknown_") for family in families)

    if not normalized_labels:
        friction_level = "blocked" if blocked else "low"
    if not families and selector_summary.get("blocked"):
        blocked = True
        friction_detected = True
        if friction_level == "none":
            friction_level = "high"

    blocked_labels: list[str] = []
    if blocked:
        blocked_labels.extend([
            family for family in families if family in {
                "unsafe_or_unauthorized",
                "needs_owner_approval",
                "public_mode_boundary",
                "unknown_capability_request",
                "unknown_intent",
                "unknown_word_or_phrase",
                "missing_context",
                "missing_evidence",
                "repeated_failure",
            }
        ])
        if policy == "refuse_with_boundary":
            blocked_labels.append("refusal_boundary")
        if policy == "escalate_to_owner_review":
            blocked_labels.append("owner_review")
        if policy == "ask_clarifying_question":
            blocked_labels.append("clarification_needed")
        if policy == "request_evidence":
            blocked_labels.append("evidence_needed")
        if policy == "route_unknown_friction":
            blocked_labels.append("unknown_friction")
    blocked_labels = _dedupe_preserve(blocked_labels)

    # If no explicit signal families were found, mirror the selector baseline.
    if not families and selector_summary.get("route_id") in _KNOWN_ROUTE_IDS_V1:
        route_id = selector_summary["route_id"]
        method_id, shape_id, case_id = _route_ids(route_id)
        if policy == "answer_directly_bounded" and selector_summary.get("blocked"):
            blocked = True
            friction_level = "high"

    safe_metadata = {
        "normalized_turn_labels": normalized_labels,
        "safe_context_signal_keys": safe_keys,
        "detected_signal_families": families,
        "friction_labels": friction_labels,
        "unknown_labels": unknown_labels,
        "selector_packet_summary": selector_summary,
        "response_policy": policy,
        "friction_level": friction_level,
        "recommended_route_id": route_id,
        "used_selector_override": used_override,
    }

    return UnknownPromptFrictionPacket(
        packet_type=PACKET_TYPE_V1,
        turn_labels=normalized_labels,
        safe_context_signal_keys=safe_keys,
        friction_detected=friction_detected,
        unknown_detected=unknown_detected,
        friction_level=friction_level,
        friction_labels=friction_labels,
        unknown_labels=unknown_labels,
        detected_signal_families=families,
        recommended_route_id=route_id,
        recommended_method_id=method_id,
        recommended_shape_id=shape_id,
        recommended_case_id=case_id,
        response_policy=policy,
        needs_clarification=needs_clarification,
        needs_evidence=needs_evidence,
        needs_owner_approval=needs_owner_approval,
        blocked=blocked,
        blocked_labels=blocked_labels,
        selector_packet_summary=selector_summary,
        safe_metadata=safe_metadata,
        runtime_authority=False,
        model_provider_used=False,
        generates_final_text=False,
        writes_state=False,
        detected_signals=tuple(signals),
        route=route,
    )


def route_unknown_prompt_friction_v1(turn_labels: Any, context_signals: Optional[Mapping[str, Any]] = None) -> UnknownPromptFrictionPacket:
    return build_unknown_prompt_friction_packet_v1(turn_labels, context_signals=context_signals)


def validate_unknown_prompt_friction_packet_v1(packet: Any) -> bool:
    if is_dataclass(packet):
        data = _json_safe(packet)
    elif isinstance(packet, Mapping):
        data = dict(packet)
    else:
        raise ValidationError("packet must be a mapping or dataclass")

    required = [
        "packet_type",
        "turn_labels",
        "safe_context_signal_keys",
        "friction_detected",
        "unknown_detected",
        "friction_level",
        "friction_labels",
        "unknown_labels",
        "detected_signal_families",
        "recommended_route_id",
        "recommended_method_id",
        "recommended_shape_id",
        "recommended_case_id",
        "response_policy",
        "needs_clarification",
        "needs_evidence",
        "needs_owner_approval",
        "blocked",
        "blocked_labels",
        "selector_packet_summary",
        "safe_metadata",
        "runtime_authority",
        "model_provider_used",
        "generates_final_text",
        "writes_state",
    ]
    for field_name in required:
        if field_name not in data:
            raise ValidationError(f"missing field: {field_name}")

    if data["packet_type"] != PACKET_TYPE_V1:
        raise ValidationError("packet_type mismatch")
    if data["runtime_authority"] is not False:
        raise ValidationError("runtime_authority must be false")
    if data["model_provider_used"] is not False:
        raise ValidationError("model_provider_used must be false")
    if data["generates_final_text"] is not False:
        raise ValidationError("generates_final_text must be false")
    if data["writes_state"] is not False:
        raise ValidationError("writes_state must be false")

    if not isinstance(data["turn_labels"], list):
        raise ValidationError("turn_labels must be a list")
    if not isinstance(data["safe_context_signal_keys"], list):
        raise ValidationError("safe_context_signal_keys must be a list")
    if not isinstance(data["friction_labels"], list):
        raise ValidationError("friction_labels must be a list")
    if not isinstance(data["unknown_labels"], list):
        raise ValidationError("unknown_labels must be a list")
    if not isinstance(data["detected_signal_families"], list):
        raise ValidationError("detected_signal_families must be a list")
    if not isinstance(data["blocked_labels"], list):
        raise ValidationError("blocked_labels must be a list")
    if not isinstance(data["selector_packet_summary"], dict):
        raise ValidationError("selector_packet_summary must be a dict")
    if not isinstance(data["safe_metadata"], dict):
        raise ValidationError("safe_metadata must be a dict")

    if data["friction_level"] not in FRICTION_LEVELS_V1:
        raise ValidationError("unknown friction_level")
    if data["response_policy"] not in RESPONSE_POLICIES_V1:
        raise ValidationError("unknown response_policy")
    if data["recommended_route_id"] not in _KNOWN_ROUTE_IDS_V1:
        raise ValidationError("unknown recommended_route_id")

    method_id, shape_id, case_id = _route_ids(data["recommended_route_id"])
    if data["recommended_method_id"] != method_id:
        raise ValidationError("recommended_method_id mismatch")
    if data["recommended_shape_id"] != shape_id:
        raise ValidationError("recommended_shape_id mismatch")
    if data["recommended_case_id"] != case_id:
        raise ValidationError("recommended_case_id mismatch")

    if len(_dedupe_preserve(data["blocked_labels"])) != len(data["blocked_labels"]):
        raise ValidationError("blocked_labels must not contain duplicates")

    if data["blocked"] is True and data["friction_level"] != "blocked":
        raise ValidationError("blocked packets must use friction_level=blocked")

    selector_summary = data["selector_packet_summary"]
    for key in ["selection_type", "route_id", "method_id", "shape_id", "case_id", "blocked", "blocked_labels", "route_confidence", "family", "turn_labels"]:
        if key not in selector_summary:
            raise ValidationError(f"selector summary missing field: {key}")

    if not isinstance(selector_summary["blocked_labels"], list):
        raise ValidationError("selector summary blocked_labels must be a list")
    if not isinstance(selector_summary["turn_labels"], list):
        raise ValidationError("selector summary turn_labels must be a list")

    if not isinstance(data["friction_detected"], bool):
        raise ValidationError("friction_detected must be bool")
    if not isinstance(data["unknown_detected"], bool):
        raise ValidationError("unknown_detected must be bool")
    if not isinstance(data["needs_clarification"], bool):
        raise ValidationError("needs_clarification must be bool")
    if not isinstance(data["needs_evidence"], bool):
        raise ValidationError("needs_evidence must be bool")
    if not isinstance(data["needs_owner_approval"], bool):
        raise ValidationError("needs_owner_approval must be bool")
    if not isinstance(data["blocked"], bool):
        raise ValidationError("blocked must be bool")

    return True


def to_unknown_prompt_friction_json_safe_v1(packet: Any) -> Dict[str, Any]:
    return _json_safe(packet)


def summarize_unknown_prompt_friction_packet_v1(packet: Any) -> Dict[str, Any]:
    data = to_unknown_prompt_friction_json_safe_v1(packet)
    return {
        "packet_type": data.get("packet_type"),
        "friction_level": data.get("friction_level"),
        "response_policy": data.get("response_policy"),
        "route_id": data.get("recommended_route_id"),
        "method_id": data.get("recommended_method_id"),
        "shape_id": data.get("recommended_shape_id"),
        "case_id": data.get("recommended_case_id"),
        "blocked": data.get("blocked"),
        "friction_detected": data.get("friction_detected"),
        "unknown_detected": data.get("unknown_detected"),
        "detected_signal_families": data.get("detected_signal_families", []),
        "selector_route_id": data.get("selector_packet_summary", {}).get("route_id"),
        "selector_family": data.get("selector_packet_summary", {}).get("family"),
    }


__all__ = [
    "UnknownPromptFrictionSignal",
    "UnknownPromptFrictionRoute",
    "UnknownPromptFrictionSummary",
    "UnknownPromptFrictionPacket",
    "build_unknown_prompt_friction_packet_v1",
    "validate_unknown_prompt_friction_packet_v1",
    "summarize_unknown_prompt_friction_packet_v1",
    "to_unknown_prompt_friction_json_safe_v1",
    "route_unknown_prompt_friction_v1",
]
