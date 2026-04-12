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
        reason_text = f" — {reason}" if reason else ""
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
            detail += f" — {reason}"
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
                detail += f" — {assumption}"
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
            detail += f" — {reason}"
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
