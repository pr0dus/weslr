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

# ─── Entry phrase detection ─────────────────────────────────────────────────────

# Phrases that indicate a user is starting fresh — not asking a real question.
_ENTRY_PHRASES = frozenset({
    "hi", "hey", "hello", "hallo", "servus",
    "start", "help", "what can i do", "what can i do?",
    "what now", "what now?", "what to do", "what to do?",
    "what is weslr",  # explicit: weslr? → what is WESLR (normalized)
    "weslr",          # welsr typo → WESLR → weslr (lower) → entry
})

# Explicit typo → normalized form mapping (deterministic, allowlist only).
# No fuzzy matching. No broad normalization. Only these exact inputs.
_TYPO_MAP: Dict[str, str] = {
    "hry":   "hey",    # hry → hey
    "helo":  "hello",  # helo → hello
    "welsr": "WESLR",  # welsr → WESLR (single transposition)
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
        # Handle entry phrases BEFORE setting guidance
        # so entry responses don't populate expanded_response.guidance
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
        expanded["guidance"] = _deterministic_guidance(response, path)
        # Append guidance inline to response_text
        if response.get("response_text"):
            rt = response["response_text"].rstrip()
            guidance = expanded["guidance"]
            if guidance:
                response["response_text"] = f"{rt} {guidance}"
            else:
                response["response_text"] = rt

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
    """Return the entry greeting — single natural paragraph."""
    return (
        "Hi — I'm WESLR. I can show you how the system works, explain what I am, "
        "or help you explore a topic safely. You can start with: \"what is WESLR\", "
        "\"what can I try\", or \"show system overview\"."
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
    """Fallback for unknown queries — entry greeting, natural paragraph, no numbered lists."""
    # If the handler already provided a specific fallback, use it
    base = response.get("response_text", "") or ""
    if base and base != "I'm not able to process that request.":
        return base

    # Handle entry phrases and typos
    if _is_entry_phrase(message):
        return _entry_greeting()

    # Unknown input — friendly, not robotic
    return (
        "I'm not sure what you want to do yet, but I can help you start. "
        "Ask what WESLR is, what you can try, or ask me to explore a topic as evidence."
    )


def _guided_guidance(response: Dict[str, Any], path: str) -> str:
    """Guidance for guided responses — inline, conversational."""
    suggestions = _related_suggestions_for_path(path)
    if suggestions:
        return f"You might also find it useful to ask about {suggestions}."
    return ""


def _deterministic_guidance(response: Dict[str, Any], path: str) -> str:
    """Guidance for deterministic responses — inline, conversational."""
    suggestions = _related_suggestions_for_path(path)
    if suggestions:
        return f"You might also try {suggestions} if you want to dig deeper."
    return ""


def _related_suggestions_for_path(path: str) -> str:
    """Return comma-separated related suggestions based on handler path."""
    suggestions_map = {
        "system_definition_query": ["why was WESLR created", "how is WESLR different from ChatGPT"],
        "operator_overview": ["show diagnostics", "show proposals"],
        "ISS_probe_registry_query": ["show diagnostics", "show system overview"],
        "ISS_probe_plan": ["show iss probes", "explain proposal iss.not_integrated"],
        "implementation_plan_query": ["show proposals", "show system overview"],
        "proposal_trace_query": ["show proposals", "show diagnostics"],
        "state_checkpoint_query": ["show system overview", "show iss probes"],
        "iss_intake_query": ["show diagnostics", "show iss probes"],
    }
    related = suggestions_map.get(path, [])
    suggestions = related[:2]
    if len(suggestions) == 2:
        return f'"{suggestions[0]}" or "{suggestions[1]}"'
    elif len(suggestions) == 1:
        return f'"{suggestions[0]}"'
    return ""


def _format_command_suggestions(count: int = 5) -> str:
    """Format a list of command suggestions — comma-separated natural prose."""
    cmds = _GUIDANCE_COMMANDS[:count]
    if len(cmds) == 1:
        return f'"{cmds[0]}"'
    elif len(cmds) == 2:
        return f'"{cmds[0]}" or "{cmds[1]}"'
    else:
        last = cmds[-1]
        rest = cmds[:-1]
        return ", ".join(f'"{c}"' for c in rest) + f", or \"{last}\""
