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


def format_what_matters_now(items: List[Dict[str, Any]]) -> str:
    """Format what_matters_now items conversationally with reasoning surface."""
    if not items:
        return "Nothing urgent right now."
    
    lines = ["Here's what matters now:"]
    for item in items:
        title = item.get("title", "Untitled")
        confidence = item.get("confidence", 0)
        lines.append(f"• **{title}** ({confidence:.0%} confidence)")
        
        # Add reasoning surface for transparency
        reasoning = format_reasoning_surface(item)
        for r in reasoning[:2]:  # Limit to 2 reasoning lines per item
            lines.append(f"  {r}")
    
    return "\n".join(lines)


def format_blocked_items(items: List[Dict[str, Any]]) -> str:
    """Format blocked items conversationally."""
    if not items:
        return "No blocked items."
    
    lines = [f"Currently blocked ({len(items)} items):"]
    for item in items:
        title = item.get("title", "Untitled")
        reason = item.get("reason", "")
        lines.append(f"• {title}")
        if reason:
            lines.append(f"  _{reason}_")
    
    return "\n".join(lines)


def format_next_actions(items: List[Dict[str, Any]]) -> str:
    """Format next actions conversationally."""
    if not items:
        return "No pending actions."
    
    lines = ["Recommended next actions:"]
    for i, item in enumerate(items, 1):
        title = item.get("title", "Untitled")
        lines.append(f"{i}. {title}")
    
    return "\n".join(lines)


def format_approval_queue(items: List[Dict[str, Any]]) -> str:
    """Format approval queue conversationally."""
    if not items:
        return "No items awaiting approval."
    
    lines = [f"**{len(items)} item(s) awaiting your approval:**"]
    for item in items:
        title = item.get("title", "Untitled")
        reason = item.get("reason", "")
        lines.append(f"• {title}")
        if reason:
            lines.append(f"  {reason}")
    
    lines.append("\n_Use `/approve <id>` to approve, or ask for details._")
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
**status** — See what matters right now
**blocked** — See what's stuck
**escalations** — See pending escalations

What would you like to know?"""


def format_help() -> str:
    """Generate help message."""
    return """**Available commands:**

**Status & Overview:**
• `status` or `what's happening` — Current decision summary
• `escalations` — Pending escalations
• `approvals` — Items awaiting approval
• `blocked` — Current blocked items

**Actions:**
• `approve <id>` — Approve an escalation (future)
• `clear` — Clear escalation state

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
    return f" — {reason}" if reason else ""


def format_status_summary(decision: Dict[str, Any]) -> str:
    """Format a conversational status summary with reasoning surface and provenance cues."""
    what_matters = decision.get("what_matters_now", [])
    blocked = decision.get("blocked_items", [])
    actions = decision.get("next_actions", [])
    approvals = decision.get("approval_queue", [])
    
    if not what_matters and not blocked and not approvals:
        return "Everything looks clear. No urgent priorities or blockers right now.\n\nWant me to check anything specific?"
    
    lines = []
    
    if what_matters:
        if len(what_matters) == 1:
            lines.append("There's **1 thing** needing your attention:")
        else:
            lines.append(f"There are **{len(what_matters)} things** needing attention:")
        for item in what_matters[:3]:
            title = item.get("title", "Untitled")
            title = title.replace("_", " ").capitalize()
            confidence_note = _format_confidence_note(item, decision.get("confidence", 0.6))
            lines.append(f"• {title}{_format_reason(item)}{confidence_note}")
            # Add reasoning surface for transparency
            reasoning = format_reasoning_surface(item)
            for r in reasoning[:2]:  # Limit to 2 reasoning lines per item
                lines.append(f"  {r}")
        
        if len(what_matters) > 3:
            lines.append(f"• ...and {len(what_matters) - 3} more")
    
    if blocked:
        lines.append("")
        if len(blocked) == 1:
            lines.append("There's **1 thing blocked** right now:")
        else:
            lines.append(f"There are **{len(blocked)} things blocked**:")
        for item in blocked[:5]:
            title = item.get("title", "Untitled")
            lines.append(f"• {title}{_format_reason(item)}")
        if len(blocked) > 5:
            lines.append(f"• ...and {len(blocked) - 5} more")
    
    if approvals:
        lines.append("")
        if len(approvals) == 1:
            lines.append("There's **1 item** waiting for your approval:")
        else:
            lines.append(f"There are **{len(approvals)} items** waiting for approval:")
        for item in approvals[:5]:
            lines.append(f"• {item.get('title', 'Untitled')}{_format_reason(item)}")
        if len(approvals) > 5:
            lines.append(f"• ...and {len(approvals) - 5} more")
    
    if actions:
        lines.append("")
        lines.append("Next actions (top 3):")
        for i, act in enumerate(actions[:3], 1):
            if isinstance(act, dict):
                title = act.get("title", "Untitled")
                lines.append(f"{i}. {title}{_format_reason(act)}")
            else:
                lines.append(f"{i}. {act}")
    
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


def handle_request(request: Dict[str, Any], persona: str = "general user", domain: str = "general") -> Response:
    """Minimal live request handler: compute decision then render via adaptive explanation.
    
    Keeps truth/governance intact; exposes blockers/approvals/next actions to operator.
    """
    try:
        from .decision_layer import DecisionLayer
    except Exception:
        # Fallback: no decision layer available
        return Response(content="Decision layer unavailable", metadata=None, actions=[])

    layer = DecisionLayer()
    decision = layer.compute_with_signals(request)
    # Render for operator
    resp = render_decision_for_operator(
        decision,
        persona=persona,
        domain=domain,
        explanation_overrides=request.get("explanation_overrides"),
        explanation_signals={"confidence": decision.get("confidence")},
    )
    # Attach actions explicitly
    resp.actions = decision.get("next_actions", [])
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
) -> Response:
    """Render decision output through adaptive explanation for operator-facing clarity.

    Truth/governance unchanged; surfaces what_matters_now, blockers, and approvals via
    the existing status formatter, then applies explanation session styling.
    """
    summary = format_status_summary(decision)
    confidence = decision.get("confidence")
    signals = explanation_signals or {}
    if confidence is not None:
        signals = {**signals, "confidence": confidence}
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
