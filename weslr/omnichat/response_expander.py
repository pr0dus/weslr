"""WESLR OmniChat Response Expander V1 — deterministic expansion layer.

Takes a handler response + policy decision and produces an expanded response.
Rules (V1, no LLM):
- Never invents facts
- Never overwrites response_text unless path == fallback_safe
- Adds _omnichat_policy + expanded_response to the response dict
- Builds L4 guidance from known WESLR commands only
- Graph context display (V1): adds graph_summary from _selected_context
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

# Graph summary note appended to response_text (once)
_GRAPH_SUMMARY_NOTE = (
    "Related structured connections were found. "
    "See expanded_response.graph_summary."
)


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

    if final_type == "blocked_write":
        expanded["guidance"] = _blocked_write_guidance(response)
        # Replace response_text with expanded guidance
        response["response_text"] = expanded["guidance"]

    elif final_type == "fallback":
        expanded["guidance"] = _fallback_guidance(response, message)
        # Replace response_text with structured fallback
        response["response_text"] = expanded["guidance"]

    elif final_type == "guided":
        expanded["guidance"] = _guided_guidance(response, path)
        # Add guidance but preserve original response_text
        if response.get("response_text"):
            response["response_text"] = (
                response["response_text"].rstrip()
                + "\n\n"
                + expanded["guidance"]
            )

    elif final_type == "deterministic":
        expanded["guidance"] = _deterministic_guidance(response, path)
        # Add guidance to response_text
        if response.get("response_text"):
            response["response_text"] = (
                response["response_text"].rstrip()
                + "\n\n"
                + expanded["guidance"]
            )

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

    # Append note to response_text once (if connections exist)
    if safe_connections and response.get("response_text") is not None:
        existing_note = _GRAPH_SUMMARY_NOTE
        current_text = response.get("response_text", "") or ""
        if existing_note not in current_text:
            response["response_text"] = (
                current_text.rstrip()
                + "\n\n"
                + existing_note
            )


# ─── Guidance builders ─────────────────────────────────────────────────────────

def _blocked_write_guidance(response: Dict[str, Any]) -> str:
    """Guidance for blocked write responses."""
    mode = response.get("_weslr_mode", "current mode")
    return (
        "This action is disabled in the current mode.\n"
        f"Mode ({mode}) restricts writes for safety.\n"
        "To proceed, use private_dev mode or submit a proposal for operator review.\n"
        "\n"
        "You can also explore this topic via:\n"
        "- show system overview\n"
        "- show diagnostics"
    )


def _fallback_guidance(response: Dict[str, Any], message: str) -> str:
    """Structured fallback for unknown queries."""
    base = response.get("response_text", "") or ""
    # If the handler already provided a specific fallback, use it
    if base and base != "I'm not able to process that request.":
        return base

    suggestions = _format_command_suggestions(5)
    return (
        "I can respond to open-ended chat — but then you would not see "
        "what I can actually do, or what is real.\n"
        "\n"
        "Instead, I can show you how the system works. Try one of these:\n"
        + suggestions
        + "\n"
        "\n"
        "I can also explore this topic as evidence if you'd like — just ask:\n"
        "'explore [topic]' or 'research [topic]'"
    )


def _guided_guidance(response: Dict[str, Any], path: str) -> str:
    """Guidance for guided responses — 2 related suggestions."""
    suggestions = _related_suggestions_for_path(path)
    if suggestions:
        return "You might also want to know:\n" + suggestions
    return ""


def _deterministic_guidance(response: Dict[str, Any], path: str) -> str:
    """Guidance for deterministic responses — 2 related structured queries."""
    suggestions = _related_suggestions_for_path(path)
    if suggestions:
        return "Related things you can try:\n" + suggestions
    return ""


def _related_suggestions_for_path(path: str) -> str:
    """Return 2 related command suggestions based on handler path."""
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
    lines = [f"- {cmd}" for cmd in related[:2]]
    return "\n".join(lines) if lines else ""


def _format_command_suggestions(count: int = 5) -> str:
    """Format a list of command suggestions for fallback."""
    cmds = _GUIDANCE_COMMANDS[:count]
    return "\n".join(f"- {cmd}" for cmd in cmds)