"""
WESLR Hybrid Turn Arbiter V1

Read-only turn analysis module that decides which layer should answer a user message.
Does NOT execute, mutate JSONL, store prompts, call external services, or use Ollama.

Authority: routing_analysis_only — pure classification, no writes.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Valid turn kinds and layers
# ---------------------------------------------------------------------------

_VALID_TURN_KINDS = (
    "continuity",
    "workplace",
    "capability_help",
    "evidence_question",
    "system_identity",
    "governance",
    "experiment",
    "action_candidate",
    "unknown",
)

_VALID_TARGET_SCOPES = (
    "user_workplace",
    "external_world",
    "weslr_self",
    "prior_context",
    "operator_system",
    "ambiguous",
)

_VALID_SELECTED_LAYERS = (
    "continuity",
    "workplace",
    "capability_welcome",
    "evidence",
    "clarification",
    "fallback",
)

_VALID_AMBIGUITY_LEVELS = ("none", "low", "medium", "high")


# ---------------------------------------------------------------------------
# Zero-context detection
# ---------------------------------------------------------------------------

def _has_active_context(context: Optional[dict]) -> bool:
    """Return True if context contains meaningful prior state."""
    if not context:
        return False
    if context.get("recent_timeline_events"):
        return True
    if context.get("workplace_overview"):
        return True
    return False


def _is_bare_collective_question(message: str) -> bool:
    """Return True if message is a bare collective 'what should we do' style question."""
    lower = message.lower().strip()
    bare_patterns = (
        r"^what (should|can) we do\??$",
        r"^what do we do\??$",
        r"^how should we proceed\??$",
        r"^what next\??$",
        r"^what now\??$",
        r"^what to do\??$",
    )
    for pattern in bare_patterns:
        if re.search(pattern, lower):
            return True
    return False


# ---------------------------------------------------------------------------
# External topic extraction
# ---------------------------------------------------------------------------

_WESLR_INTERNAL_TERMS = {
    "weslr", "workplace", "experiment", "proposal", "capability", "evidence",
    "continuity", "timeline", "operator", "governance", "proactive", "signature",
    "entity", "graph", "consciousness", "jarvis", "agent", "layer", "bridge",
    "proposal", "review", "surface", "router", "registry", "inventory", "status",
    "unsafe", "automate", "approval", "human",
}


def _extract_external_topic(message: str) -> Optional[str]:
    """Extract a real-world noun phrase from a question that is NOT WESLR-internal.

    Returns the extracted topic string or None if no clear external topic found.
    """
    lower = message.lower().strip()

    # Patterns that introduce an external topic
    topic_intro_patterns = [
        r"what (is|are|was|were|do you know) (about |for |the |a )?(.+?)\??$",
        r"tell me about (.+?)\??$",
        r"explain (.+?)\??$",
        r"how (does|do) (.+?) work\??$",
        r"why does (.+?)\??$",
        r"what happens (with|during|to |in )(.+?)\??$",
        r"about (.+?)\??$",
        r"for (.+?)\??$",
    ]

    for pattern in topic_intro_patterns:
        m = re.search(pattern, lower)
        if m:
            topic = " ".join(g for g in m.groups() if g).strip()
            if topic and len(topic) > 2:
                # Check it's not purely WESLR-internal (word-level check)
                words = set(topic.split())
                internal_count = len(words & _WESLR_INTERNAL_TERMS)
                if internal_count <= len(words) * 0.3:
                    return topic
    return None


# ---------------------------------------------------------------------------
# Workplace scope detection
# ---------------------------------------------------------------------------

_WORKPLACE_SCOPE_PATTERNS = (
    r"\bour project\b",
    r"\bour workshop\b",
    r"\bour workplace\b",
    r"\bour team\b",
    r"\bour work\b",
    r"\bthe workplace\b",
    r"\bpending ideas?\b",
    r"\bpending experiments?\b",
    r"\bwhat are we working on\b",
    r"\bour recent\b",
)


def _is_workplace_scope(message: str, context: Optional[dict]) -> bool:
    """Return True if message or context indicates workplace/project scope."""
    lower = message.lower()
    for pattern in _WORKPLACE_SCOPE_PATTERNS:
        if re.search(pattern, lower):
            return True
    if context and context.get("workplace_overview"):
        if _is_bare_collective_question(message):
            return True
    return False


# ---------------------------------------------------------------------------
# Continuity scope detection
# ---------------------------------------------------------------------------

_CONTINUITY_PATTERNS = (
    r"\blast time\b",
    r"\byesterday\b",
    r"\bprevious session\b",
    r"\bremember when\b",
    r"\bwhat did we (work on|do|discuss|talk about)\b",
    r"\bwhat we (worked on|did|discussed|talked about)\b",
    r"\bpast (session|work|discussions)\b",
)


def _is_continuity_scope(message: str) -> bool:
    """Return True if message asks about prior context."""
    lower = message.lower()
    for pattern in _CONTINUITY_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False


# ---------------------------------------------------------------------------
# WESLR self scope detection
# ---------------------------------------------------------------------------

_WESLR_SELF_PATTERNS = (
    r"\bwhat can you do\b",
    r"\bwhat can you help me with\b",
    r"\bwhat is weslr\b",
    r"\bwho are you\b",
    r"\btell me about yourself\b",
    r"\bhow do you work\b",
    r"\bwhat is your (name|nature|capabilities)\b",
    r"\bwhat should i try\b",
    r"\bwhat do you (know|remember)\b",
    r"\bi need help\b",
    r"\bhelp me\b",
)


def _is_weslr_self_scope(message: str) -> bool:
    """Return True if message asks about WESLR's identity or capabilities."""
    lower = message.lower()
    for pattern in _WESLR_SELF_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False


# ---------------------------------------------------------------------------
# Governance scope detection
# ---------------------------------------------------------------------------

_GOVERNANCE_PATTERNS = (
    r"\bwhat is unsafe to automate\b",
    r"\bwhat requires operator approval\b",
    r"\bgovernance boundaries\b",
    r"\bwhat can you not do\b",
    r"\bsafety boundaries\b",
    r"\bwhat needs human approval\b",
    r"\bwhat can you automate\b",
    r"\bwhat requires approval\b",
)


def _is_governance_scope(message: str) -> bool:
    """Return True if message asks about governance, safety, or approval boundaries."""
    lower = message.lower()
    for pattern in _GOVERNANCE_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False


# ---------------------------------------------------------------------------
# Action/experiment scope detection
# ---------------------------------------------------------------------------

_ACTION_PATTERNS = (
    r"\bshould we run\b",
    r"\brun the\b",
    r"\bstart experiment\b",
    r"\bexecute\b",
    r"\btry experiment\b",
    r"\bpropose experiment\b",
    r"\bchange the\b",
    r"\bimplement\b.*\bexperiment\b",
    r"\bproposal.*experiment\b",
)


def _is_action_scope(message: str) -> bool:
    """Return True if message proposes or queries an executable action."""
    lower = message.lower()
    for pattern in _ACTION_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False


# ---------------------------------------------------------------------------
# Capability scoring (tries real router, falls back to empty list)
# ---------------------------------------------------------------------------

def _score_capabilities(message: str, context: Optional[dict]) -> List[dict]:
    """Score capabilities for the message. Read-only, no writes."""
    try:
        from weslr.capability_router import route_request

        router_context: Dict[str, Any] = {}

        try:
            from weslr.evidence_needed_detector import classify_evidence_need

            evidence_class = classify_evidence_need(message)
            if evidence_class.get("evidence_needed"):
                router_context["evidence_needed"] = True
        except Exception:
            pass

        result = route_request(
            message,
            context=router_context if router_context else None,
        )

        selected = result.get("selected_capability")
        if not selected:
            return []

        return [{
            "capability_id": selected,
            "score": result.get("confidence", 0.0),
            "reason": f"router:{result.get('method', 'fallback')}",
        }]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Ambiguity scoring
# ---------------------------------------------------------------------------

def _score_ambiguity(
    message: str,
    selected_layer: str,
    candidate_count: int,
    strong_signal: bool,
) -> str:
    """Compute ambiguity level based on heuristics."""
    word_count = len(message.split())

    if strong_signal:
        return "none"
    if candidate_count > 2:
        return "medium"
    if word_count <= 5 and not message.strip().startswith("/") and candidate_count == 0:
        return "high"
    return "low"


# ---------------------------------------------------------------------------
# Clarification question generation
# ---------------------------------------------------------------------------

def _build_clarification_question(message: str, has_context: bool) -> str:
    """Generate an appropriate clarification question."""
    if not has_context:
        return (
            "We haven't worked together before. What would you like to do? "
            "I can explain what WESLR is, help with a project, "
            "search for information, or something else."
        )
    return (
        "I'm not sure what you're asking. Could you rephrase? "
        "I can help with your WESLR workplace, continuity from our last session, "
        "answer questions, or explain what I can do."
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyze_turn(message: str, context: Optional[dict] = None) -> dict:
    """Analyze a user message and recommend the best response layer.

    Read-only deterministic function. Does NOT execute, write, or call LLM.

    Args:
        message: The raw user message.
        context: Optional context dict with keys:
            - user_id: str
            - recent_timeline_events: list[dict] (optional)
            - workplace_overview: str (optional)
            - session_turn_history: list[dict] (optional)

    Returns:
        dict with keys:
            - record_type: "hybrid_turn_analysis_v1"
            - turn_kind: str
            - target_scope: str
            - external_topic: str | None
            - requires_evidence: bool
            - requires_memory: bool
            - requires_action: bool
            - candidate_capabilities: list[dict]
            - selected_layer: str
            - confidence: float
            - ambiguity: str
            - clarification_question: str | None
            - authority: "routing_analysis_only"
            - automatic_action: False
    """
    context = context or {}
    message = message.strip() if message else ""

    has_context = _has_active_context(context)

    # ── 1. Zero-context bare collective question → clarification ─────────────
    if not has_context and _is_bare_collective_question(message):
        return {
            "record_type": "hybrid_turn_analysis_v1",
            "turn_kind": "unknown",
            "target_scope": "ambiguous",
            "external_topic": None,
            "requires_evidence": False,
            "requires_memory": False,
            "requires_action": False,
            "candidate_capabilities": [],
            "selected_layer": "clarification",
            "confidence": 0.9,
            "ambiguity": "high",
            "clarification_question": _build_clarification_question(message, has_context),
            "authority": "routing_analysis_only",
            "automatic_action": False,
        }

    # ── 2. Workplace scope ───────────────────────────────────────────────
    if _is_workplace_scope(message, context):
        return {
            "record_type": "hybrid_turn_analysis_v1",
            "turn_kind": "workplace",
            "target_scope": "user_workplace",
            "external_topic": None,
            "requires_evidence": False,
            "requires_memory": False,
            "requires_action": False,
            "candidate_capabilities": _score_capabilities(message, context),
            "selected_layer": "workplace",
            "confidence": 0.85,
            "ambiguity": "none",
            "clarification_question": None,
            "authority": "routing_analysis_only",
            "automatic_action": False,
        }

    # ── 3. Continuity scope ──────────────────────────────────────────────
    if _is_continuity_scope(message):
        return {
            "record_type": "hybrid_turn_analysis_v1",
            "turn_kind": "continuity",
            "target_scope": "prior_context",
            "external_topic": None,
            "requires_evidence": False,
            "requires_memory": True,
            "requires_action": False,
            "candidate_capabilities": _score_capabilities(message, context),
            "selected_layer": "continuity",
            "confidence": 0.88,
            "ambiguity": "none",
            "clarification_question": None,
            "authority": "routing_analysis_only",
            "automatic_action": False,
        }

    # ── 4. Governance scope (before external_topic extraction) ───────────
    # Governance questions must not be swallowed by the generic external
    # topic detector first.
    if _is_governance_scope(message):
        return {
            "record_type": "hybrid_turn_analysis_v1",
            "turn_kind": "governance",
            "target_scope": "operator_system",
            "external_topic": None,
            "requires_evidence": False,
            "requires_memory": False,
            "requires_action": False,
            "candidate_capabilities": _score_capabilities(message, context),
            "selected_layer": "capability_welcome",
            "confidence": 0.88,
            "ambiguity": "none",
            "clarification_question": None,
            "authority": "routing_analysis_only",
            "automatic_action": False,
        }

    # ── 5. External topic detection ──────────────────────────────────────
    # Only fires when the topic is clearly about the external world and
    # contains no WESLR-internal terms.
    external_topic = _extract_external_topic(message)
    if external_topic:
        topic_words = set(external_topic.lower().split())
        # Only block if every word is internal — a partial match is OK
        if topic_words and not all(w in _WESLR_INTERNAL_TERMS for w in topic_words):
            return {
                "record_type": "hybrid_turn_analysis_v1",
                "turn_kind": "evidence_question",
                "target_scope": "external_world",
                "external_topic": external_topic,
                "requires_evidence": True,
                "requires_memory": False,
                "requires_action": False,
                "candidate_capabilities": _score_capabilities(message, context),
                "selected_layer": "evidence",
                "confidence": 0.85,
                "ambiguity": "none",
                "clarification_question": None,
                "authority": "routing_analysis_only",
                "automatic_action": False,
            }

    # ── 6. WESLR self scope ──────────────────────────────────────────────
    if _is_weslr_self_scope(message):
        identity_patterns = (
            r"\bwhat is weslr\b",
            r"\bwho are you\b",
            r"\btell me about yourself\b",
            r"\bwhat is your name\b",
            r"\bwhat are you\b",
        )
        is_identity = any(re.search(p, message.lower()) for p in identity_patterns)
        return {
            "record_type": "hybrid_turn_analysis_v1",
            "turn_kind": "system_identity" if is_identity else "capability_help",
            "target_scope": "weslr_self",
            "external_topic": None,
            "requires_evidence": False,
            "requires_memory": False,
            "requires_action": False,
            "candidate_capabilities": _score_capabilities(message, context),
            "selected_layer": "capability_welcome",
            "confidence": 0.90,
            "ambiguity": "none",
            "clarification_question": None,
            "authority": "routing_analysis_only",
            "automatic_action": False,
        }

    # ── 7. Action / experiment scope ───────────────────────────────────
    if _is_action_scope(message):
        return {
            "record_type": "hybrid_turn_analysis_v1",
            "turn_kind": "action_candidate",
            "target_scope": "operator_system",
            "external_topic": None,
            "requires_evidence": False,
            "requires_memory": False,
            "requires_action": True,
            "candidate_capabilities": _score_capabilities(message, context),
            "selected_layer": "capability_welcome",
            "confidence": 0.80,
            "ambiguity": "low",
            "clarification_question": None,
            "authority": "routing_analysis_only",
            "automatic_action": False,
        }

    # ── 8. Capability routing + ambiguity scoring ──────────────────────
    candidates = _score_capabilities(message, context)
    strong_signal = bool(candidates and candidates[0]["score"] >= 0.85)

    if candidates:
        candidates_sorted = sorted(candidates, key=lambda x: x["score"], reverse=True)
        top_score = candidates_sorted[0]["score"]

        if top_score >= 0.85:
            selected_layer = "capability_welcome"
            confidence = top_score
            ambiguity = "none"
        elif (len(candidates_sorted) > 1
              and (candidates_sorted[0]["score"] - candidates_sorted[1]["score"]) < 0.1):
            selected_layer = "capability_welcome"
            confidence = top_score
            ambiguity = "medium"
        else:
            selected_layer = "capability_welcome"
            confidence = top_score
            ambiguity = _score_ambiguity(message, selected_layer, len(candidates), strong_signal)
    else:
        selected_layer = "fallback"
        confidence = 0.3
        ambiguity = _score_ambiguity(message, selected_layer, 0, False)

    # ── 9. High-ambiguity fallback → clarification ──────────────────────
    clarification_question = None
    if ambiguity == "high" and selected_layer != "clarification":
        selected_layer = "clarification"
        clarification_question = _build_clarification_question(message, has_context)
        confidence = 0.4

    return {
        "record_type": "hybrid_turn_analysis_v1",
        "turn_kind": "unknown",
        "target_scope": "ambiguous",
        "external_topic": None,
        "requires_evidence": False,
        "requires_memory": False,
        "requires_action": False,
        "candidate_capabilities": candidates,
        "selected_layer": selected_layer,
        "confidence": confidence,
        "ambiguity": ambiguity,
        "clarification_question": clarification_question,
        "authority": "routing_analysis_only",
        "automatic_action": False,
    }
