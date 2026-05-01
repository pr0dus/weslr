"""WESLR OmniChat Response Expander V1 — deterministic expansion layer.

Takes a handler response + policy decision and produces an expanded response.
Rules (V1, no LLM):
- Never invents facts
- Never overwrites response_text unless path == fallback_safe
- Adds _omnichat_policy + expanded_response to the response dict
- Builds L4 guidance from known WESLR commands only
- Graph context display (V1): adds graph_summary from _selected_context
- Phase 1 unification: response_text is single natural message, all metadata in JSON
- Phase 2: entry phrases and typo normalization for natural starting experience
"""

from __future__ import annotations

from typing import Dict, Any, List


# ─── Constants ────────────────────────────────────────────────────────────────

MAX_DISPLAY_CONNECTIONS = 5

# Source label for safety — never expose raw paths
_SAFE_SOURCE_LABELS = frozenset({
    "proposal_trace.jsonl",
    "implementation_plans.jsonl",
    "iss_diagnostic_records.jsonl",
})

# Graph summary note — kept as constant for reference, NOT appended to response_text
_GRAPH_SUMMARY_NOTE = (
    "Related structured connections were found. "
    "See expanded_response.graph_summary."
)

# Expand note — kept as constant for reference, NOT appended to response_text
_EXPAND_NOTE = (
    "Structured relationships and exploratory evidence are available. "
    "Evidence is not part of confirmed system knowledge."
)

# ─── Response contract → natural reply mapping ───────────────────────────────

_CONTRACT_REPLIES = {
    "conversational_entry": (
        "Hi — I'm WESLR. I can show you how the system works, explain what I am, "
        "explore any topic as evidence, or walk you through the current system state. "
        "Just tell me what you want to know."
    ),
    "guided_help": (
        "I can help with that. Tell me what you'd like to achieve, "
        "and we'll break it down step by step."
    ),
    "structured_explanation": (
        "I can explain that clearly. Tell me how deep you want to go, "
        "and I'll start from there."
    ),
    "exploratory_guidance": (
        "We can explore that together. I can start with what is known, "
        "then map out related ideas."
    ),
    "uncertainty_boundary": None,  # Use existing fallback guidance
    "system_answer": None,          # Pass through to existing handlers
}

# ─── Entry phrase detection ─────────────────────────────────────────────────────

# Phrases that indicate a user is starting fresh — not asking a real question.
_ENTRY_PHRASES = frozenset({
    # Greetings (primary entry)
    "hi", "hey", "hello", "hallo", "servus", "yo", "sup",
    # Start/help prompts
    "start", "help", "what can i do", "what can i do?",
    "what now", "what now?", "what to do", "what to do?",
    # WESLR explicit
    "what is weslr",  # weslr? → what is WESLR (normalized)
    "weslr",          # welsr typo → WESLR → weslr (lower) → entry
})

# Explicit typo → normalized form mapping (deterministic, allowlist only).
# No fuzzy matching. No broad normalization. Only these exact inputs.
_TYPO_MAP: Dict[str, str] = {
    "hry":   "hey",    # hry → hey
    "helo":  "hello",  # helo → hello
    "welsr": "WESLR",  # welsr → WESLR (single transposition)
    "yo":    "yo",     # keep as-is (already in _ENTRY_PHRASES)
}

# Phrases that are clearly asking about WESLR despite surface typos.
_WESLR_QUERY_TYPOS = frozenset({
    "weslr?",  # weslr? → what is WESLR
})


# ─── Known WESLR commands for guidance (L4 suggestions) ────────────────────────

_GUIDANCE_COMMANDS = [
    "show system overview",
    "show iss probes",
    "show diagnostics",
    "show proposals",
    "show capabilities",
    "explain proposal iss.not_integrated",
    "what is WESLR",
    "why was WESLR created",
    "how is WESLR different from ChatGPT",
]


def expand_response(
    response: Dict[str, Any],
    policy: Dict[str, Any],
    message: str,
) -> Dict[str, Any]:
    """Expand a handler response according to policy.

    Args:
        response: Handler output dict (possibly already expanded)
        policy: Policy decision from decide_response_policy()
        message: Original user message (for context)

    Returns:
        Response dict with _omnichat_policy and expanded_response added.
        Does NOT overwrite existing response_text unless path == fallback_safe.

    Rules:
        - Preserves all existing response fields
        - Adds _omnichat_policy with policy metadata
        - Adds expanded_response.guidance based on response type
        - Never invents facts — guidance uses only registered WESLR commands
        - Phase 1: response_text is single natural message; metadata in JSON only
        - Phase 2: entry phrases produce natural greeting; typos normalized
    """
    # Avoid double-expansion
    if "_omnichat_policy" in response:
        return response

    final_type = policy.get("final_response_type", "deterministic")
    path = response.get("path", "unknown")

    # Build expanded_response sub-dict
    expanded: Dict[str, Any] = {}

    # ── Graph context expansion (display-only) ─────────────────────────────
    _expand_graph_context(response, expanded)

    # ── Knowledge view: structured graph + evidence overlay ─────────────────
    _expand_knowledge_view(response, expanded)

    if final_type == "blocked_write":
        expanded["guidance"] = _blocked_write_guidance(response)
        # Replace response_text with natural blocked write response
        response["response_text"] = expanded["guidance"]

    elif final_type == "fallback":
        # Entry phrases handled via interpret_human_turn → response_contract.
        # Contract reply execution delegated to format_reply() — single source.
        if _is_entry_phrase(message):
            response["response_text"] = _entry_greeting()
            expanded["guidance"] = ""
        else:
            expanded["guidance"] = _fallback_guidance(response, message)
            # Replace response_text with natural fallback paragraph
            response["response_text"] = expanded["guidance"]

    elif final_type == "guided":
        expanded["guidance"] = _guided_guidance(response, path)
        # Append guidance inline to response_text
        if response.get("response_text"):
            rt = response["response_text"].rstrip()
            guidance = expanded["guidance"]
            if guidance:
                response["response_text"] = f"{rt} {guidance}"
            else:
                response["response_text"] = rt

    elif final_type == "deterministic":
        # Contract reply execution delegated to format_reply() — single source.
        # expand_response() applies non-contract guidance only.
        expanded["guidance"] = _deterministic_guidance(response, path)
        if response.get("response_text"):
            rt = response["response_text"].rstrip()
            guidance = expanded["guidance"]
            if guidance:
                response["response_text"] = f"{rt} {guidance}"
    else:
        # Unknown type — no expansion
        expanded["guidance"] = ""

    # Attach policy metadata
    response["_omnichat_policy"] = {
        "final_response_type": final_type,
        "expansion_layers": policy.get("expansion_layers", []),
        "depth_level": policy.get("depth_level", "standard"),
        "llm_formatter_allowed": policy.get("llm_formatter_allowed", False),
        "evidence_mode_offered": policy.get("evidence_mode_offered", False),
        "evidence_mode_active": policy.get("evidence_mode_active", False),
        "policy_reason": policy.get("policy_reason", ""),
        "version": "v1",
    }

    response["expanded_response"] = expanded

    return response


# ─── Graph context expansion (display-only) ──────────────────────────────────

def _expand_graph_context(
    response: Dict[str, Any],
    expanded: Dict[str, Any],
) -> None:
    """
    If response contains _selected_context with context_type == "graph",
    add graph_summary to expanded.

    Display rules:
    - max 5 connections shown
    - display_truncated = True if more than 5 exist
    - no raw JSONL paths exposed
    - source_refs labels only
    - empty graph_context → count 0, no text append
    - malformed context → no-op (safe)
    - Phase 1: graph_summary stays in expanded_response only, NOT in prose
    """
    try:
        selected = response.get("_selected_context")
        if not selected:
            return
        if not isinstance(selected, dict):
            return
        if selected.get("context_type") != "graph":
            return
    except Exception:
        # Malformed context — safe no-op
        return

    graph_ctx = selected.get("graph_context")
    if not graph_ctx or not isinstance(graph_ctx, dict):
        # Empty → count 0
        expanded["graph_summary"] = {
            "root_id": graph_ctx.get("root", {}).get("id", "") if isinstance(graph_ctx, dict) else "",
            "connection_count": 0,
            "connections": [],
            "truncated": False,
            "display_truncated": False,
        }
        return

    root_id = graph_ctx.get("root", {}).get("id", "") if isinstance(graph_ctx.get("root"), dict) else ""
    raw_connections = graph_ctx.get("connections", [])
    truncated = bool(graph_ctx.get("truncated", False))

    # Build safe connections list (display-only, max 5)
    safe_connections: List[Dict[str, Any]] = []
    display_truncated = False

    if isinstance(raw_connections, list):
        if len(raw_connections) > MAX_DISPLAY_CONNECTIONS:
            display_truncated = True
            display_list = raw_connections[:MAX_DISPLAY_CONNECTIONS]
        else:
            display_list = raw_connections

        for conn in display_list:
            if not isinstance(conn, dict):
                continue
            # Strip any keys that might contain raw paths — only keep safe fields
            safe_connections.append({
                "type": str(conn.get("type", "")),
                "id": str(conn.get("id", "")),
                "relation": str(conn.get("relation", "")),
                "depth": int(conn.get("depth", 0)),
            })

    expanded["graph_summary"] = {
        "root_id": root_id,
        "connection_count": len(raw_connections) if isinstance(raw_connections, list) else 0,
        "connections": safe_connections,
        "truncated": truncated,
        "display_truncated": display_truncated,
    }
    # NOTE: _GRAPH_SUMMARY_NOTE no longer appended to response_text.
    # It stays in expanded_response.graph_summary for metadata consumers only.


def _expand_knowledge_view(
    response: Dict[str, Any],
    expanded: Dict[str, Any],
) -> None:
    """
    Build expanded_response.knowledge_view from graph_summary + evidence_overlay.

    Display rules:
    - If graph_summary has connections → structured section in JSON
    - If evidence_overlay present → evidence section in JSON with label
    - Never merge graph + evidence into one structure
    - Never remove evidence label
    - Never promote evidence to structured truth
    - No evidence → evidence section omitted entirely
    - No graph → structured section omitted entirely
    - Phase 1: knowledge_view stays in expanded_response only, NOT in prose
    """
    graph_summary = expanded.get("graph_summary")
    evidence_overlay: List[Dict[str, Any]] = []

    # Extract evidence_overlay from _selected_context if present
    try:
        selected = response.get("_selected_context")
        if isinstance(selected, dict):
            overlay_container = selected.get("evidence_overlay")
            if isinstance(overlay_container, list):
                evidence_overlay = overlay_container
    except Exception:
        evidence_overlay = []

    has_graph = (
        graph_summary is not None
        and isinstance(graph_summary, dict)
        and bool(graph_summary.get("connections"))
    )
    has_evidence = bool(evidence_overlay)

    if not has_graph and not has_evidence:
        return

    knowledge_view: Dict[str, Any] = {}

    if has_graph:
        knowledge_view["structured"] = {
            "connections": graph_summary["connections"],
            "count": graph_summary.get("connection_count", 0),
        }

    if has_evidence:
        knowledge_view["evidence"] = {
            "items": evidence_overlay,
            "label": "not part of structured truth",
        }

    expanded["knowledge_view"] = knowledge_view
    # NOTE: _EXPAND_NOTE no longer appended to response_text.
    # Evidence and structured sections stay in expanded_response.knowledge_view only.


# ─── Entry phrase detection helpers ─────────────────────────────────────────────

def _normalize_message(message: str) -> str:
    """Apply explicit typo normalization (deterministic, allowlist only).

    Returns the normalized message string for downstream routing.
    Only handles the exact entries in _TYPO_MAP and _WESLR_QUERY_TYPOS.
    """
    normalized = message.strip().lower()
    if normalized in _TYPO_MAP:
        return _TYPO_MAP[normalized]
    if normalized in _WESLR_QUERY_TYPOS:
        return "what is WESLR"
    return message


def _is_entry_phrase(message: str) -> bool:
    """Return True if message is a greeting or starting prompt.

    Case-insensitive. Applies typo normalization before checking.
    """
    normalized = message.strip().lower()
    # Also handle normalized typos
    if normalized in _TYPO_MAP:
        normalized = _TYPO_MAP[normalized].lower()
    if normalized in _WESLR_QUERY_TYPOS:
        normalized = "what is weslr"
    return normalized in _ENTRY_PHRASES


def _entry_greeting() -> str:
    """Return the entry greeting — single natural paragraph, no quoted commands."""
    return (
        "Hi — I'm WESLR. I can show you how the system works, explain what I am, "
        "explore any topic as evidence, or walk you through the current system state. "
        "Just tell me what you want to know."
    )


# ─── Guidance builders (all single natural paragraph, no structural markers) ────

def _blocked_write_guidance(response: Dict[str, Any]) -> str:
    """Guidance for blocked write responses — single natural paragraph."""
    mode = response.get("_weslr_mode", "current mode")
    return (
        f"That operation requires write access, which is not available "
        f"in {mode} mode. If you have access to a developer session, "
        f"that would be the place to explore it. Otherwise I can log it "
        f"as a request for the operator."
    )


def _fallback_guidance(response: Dict[str, Any], message: str) -> str:
    """Fallback for unknown queries — entry greeting or evidence offer, natural paragraph, no commands."""
    # If the handler already provided a specific fallback, use it
    base = response.get("response_text", "") or ""
    if base and base != "I'm not able to process that request.":
        return base

    # Handle entry phrases and typos
    if _is_entry_phrase(message):
        return _entry_greeting()

    # Unknown input — offer to explore as evidence, naturally
    return (
        "I don't have a confirmed answer for that yet, "
        "but I can look into it and show you what I find — "
        "keeping it separate from structured system knowledge."
    )


# ─── Capability guidance (inline, no command strings) ───────────────────────────────
# Maps paths to natural capability descriptions — NO quoted commands.
_CAPABILITY_MAP: Dict[str, List[str]] = {
    "system_definition_query": [
        "explain why WESLR was built and what problem it solves",
        "compare how WESLR differs from a standard chatbot",
    ],
    "task_help_query": [
        "break down what you want to achieve into steps",
        "clarify the goal and find a path forward",
    ],
    "operator_overview": [
        "walk through the current diagnostics",
        "review the active proposals and their status",
    ],
    "ISS_probe_registry_query": [
        "show the current diagnostics",
        "display the system overview",
    ],
    "ISS_probe_plan": [
        "list the active ISS probes and what they're tracking",
        "explain any proposals that aren't yet integrated",
    ],
    "implementation_plan_query": [
        "review the active implementation plans",
        "show the full system state",
    ],
    "proposal_trace_query": [
        "review the active proposals and their current status",
        "check the latest diagnostics",
    ],
    "state_checkpoint_query": [
        "show the full system overview",
        "list active ISS probes",
    ],
    "iss_intake_query": [
        "check the current diagnostics",
        "show the ISS probe status",
    ],
}


def _capability_for_path(path: str) -> str:
    """Return a natural capability description for the given path (no quotes)."""
    caps = _CAPABILITY_MAP.get(path, [])
    if len(caps) == 2:
        return f"I can {caps[0]} or {caps[1]}."
    elif len(caps) == 1:
        return f"I can {caps[0]}."
    return ""


def _guided_guidance(response: Dict[str, Any], path: str) -> str:
    """Guidance for guided responses — capability phrasing, no commands."""
    cap = _capability_for_path(path)
    if cap:
        return f"{cap}"
    return ""


def _deterministic_guidance(response: Dict[str, Any], path: str) -> str:
    """Guidance for deterministic responses — capability phrasing, no commands."""
    cap = _capability_for_path(path)
    if cap:
        return f"{cap}"
    return ""


# _related_suggestions_for_path and _format_command_suggestions removed.
# Phase 3: guidance is purely capability-based, no command strings anywhere."


# ─── Public reply formatting API ─────────────────────────────────────────────

def format_reply(interpreted: Dict[str, Any]) -> str:
    """Format a natural reply from an interpreted result.

    Single execution surface for all response contract logic.
    Applies the correct natural-language reply based on response_contract.
    Entry phrases are handled via existing _is_entry_phrase logic.

    Args:
        interpreted: Output from interpret_human_turn() with all frame fields.

    Returns:
        Natural-language reply string ready for delivery.
    """
    contract = interpreted.get("response_contract", "unknown")
    path = interpreted.get("path", "")

    # Deterministic handlers - always prefer handler's response_text
    # These handlers provide their own structured reply
    deterministic_paths = [
        "self_identity",
        "capability_help",
        "improvement_explanation",
        "uncertainty_explanation",
        "memory_boundary",
        "simple_followup",
        "usage_guidance",
        "agi_clarification",
        "self_improvement_clarification",
        "learning_clarification",
        "task_help_query",  # task_help_query bypasses format_reply contract
    ]
    if path in deterministic_paths:
        return interpreted.get("response_text", "")

    # conversational_entry — use existing greeting logic
    if contract == "conversational_entry":
        # Fall back to existing greeting for entry frame
        greeting = _CONTRACT_REPLIES["conversational_entry"]
        # If interpret_human_turn already set response_text from entry_greeting
        # handler, prefer that (it has the "Hi — I'm WESLR" marker).
        existing = interpreted.get("response_text", "") or ""
        if existing.strip():
            return existing
        return greeting

    # guided_help — step-by-step collaboration
    if contract == "guided_help":
        return _CONTRACT_REPLIES["guided_help"]

    # structured_explanation — depth-controlled explanation
    if contract == "structured_explanation":
        return _CONTRACT_REPLIES["structured_explanation"]

    # exploratory_guidance — collaborative exploration
    if contract == "exploratory_guidance":
        return _CONTRACT_REPLIES["exploratory_guidance"]

    # uncertainty_boundary — pass through to existing fallback guidance
    # (interpret_human_turn already set response_text via expand_response)
    if contract == "uncertainty_boundary":
        return interpreted.get("response_text", "I'm not sure I understood that correctly.")

    # system_answer — pass through to handler's response_text
    if contract == "system_answer":
        return interpreted.get("response_text", "")

    # Fallback for unknown contract — use existing response_text
    return interpreted.get("response_text", "")

