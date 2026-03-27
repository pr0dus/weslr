"""First-class handoff state module for CircleForge.

Provides structured handoff tracking between agents and internal processes.

Key improvements:
- Handoff notes are now first-class state (stored, tracked, queried)
- Handoff quality metrics (acceptance rate, feedback, follow-ups)
- Multi-agent coordination tracking
- Handoff history for debugging and learning
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


# Default handoff state path
DEFAULT_HANDOFF_STATE_PATH = "handoffs.json"


def create_handoff_note(
    from_agent: str,
    to_agent: str,
    topic: str,
    context: dict,
    handoff_type: str = "task",
    priority: float = 0.5,
    timeout_seconds: int = 3600,
    metadata: dict | None = None,
) -> dict:
    """Create a handoff note with full state and tracking.

    This is the core improvement: handoffs are now first-class state.
    """
    now_ts = int(time.time())
    handoff_id = f"handoff-{from_agent}-to-{to_agent}-{now_ts}"

    handoff = {
        "id": handoff_id,
        "timestamp": now_ts,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "topic": topic,
        "handoff_type": handoff_type,
        "priority": priority,
        "timeout_at": now_ts + timeout_seconds,
        "context": dict(context),
        "metadata": dict(metadata or {}),
        "status": "pending",
        "claims": [],
        "evidence": [],
        "feedback": [],
        "acceptance": None,
        "resolution": None,
        "completed_at": None,
    }

    return handoff


def log_handoff_claim(handoff: dict, claim: str, evidence: str | None = None) -> dict:
    """Add a claim with supporting evidence to a handoff.

    Claims are assertions the from-agent makes that the to-agent should address.
    """
    claim_id = f"claim-{len(handoff.get('claims', [])) + 1}"
    note = {
        "id": claim_id,
        "text": str(claim),
        "evidence": str(evidence or ""),
        "logged_at": int(time.time()),
    }

    handoff.setdefault("claims", []).append(note)

    if evidence:
        handoff.setdefault("evidence", []).append({
            "claim_id": claim_id,
            "evidence": str(evidence),
        })

    return handoff


def record_handoff_feedback(
    handoff: dict,
    feedback_type: str,
    feedback_text: str,
    from_agent: str,
) -> dict:
    """Record feedback on a handoff (acceptance, rejection, questions)."""
    feedback = {
        "id": f"feedback-{len(handoff.get('feedback', [])) + 1}",
        "type": feedback_type,  # "accept", "reject", "question", "clarify"
        "text": str(feedback_text),
        "from_agent": from_agent,
        "timestamp": int(time.time()),
    }

    handoff.setdefault("feedback", []).append(feedback)

    # Update status based on feedback
    if feedback_type == "accept":
        handoff["status"] = "accepted"
        handoff["acceptance"] = {"at": int(time.time()), "by": from_agent}
    elif feedback_type == "reject":
        handoff["status"] = "rejected"
        handoff["acceptance"] = {"at": int(time.time()), "by": from_agent, "reason": feedback_text}

    return handoff


def resolve_handoff(handoff: dict, resolution: str, completed_by: str) -> dict:
    """Mark a handoff as resolved with a summary."""
    now_ts = int(time.time())
    handoff["status"] = "resolved"
    handoff["resolution"] = {
        "summary": str(resolution),
        "completed_by": completed_by,
        "completed_at": now_ts,
    }
    handoff["completed_at"] = now_ts
    return handoff


def find_pending_handoffs(
    handoffs: List[dict],
    for_agent: str | None = None,
    due_before: int | None = None,
) -> List[dict]:
    """Find handoffs that are still pending/active.

    Optionally filter by agent or due time.
    """
    now_ts = int(time.time())
    due_before = due_before or now_ts

    pending = []
    for handoff in handoffs:
        status = str(handoff.get("status", "pending")).lower()
        if status not in {"pending", "accepted", "active"}:
            continue

        if for_agent:
            if handoff.get("to_agent") != for_agent and handoff.get("from_agent") != for_agent:
                continue

        if handoff.get("timeout_at", 0) > due_before:
            pending.append(handoff)

    return pending


def find_overdue_handoffs(
    handoffs: List[dict],
    now_ts: int | None = None,
) -> List[dict]:
    """Find handoffs that have exceeded their timeout."""
    now_ts = now_ts or int(time.time())

    overdue = []
    for handoff in handoffs:
        if handoff.get("timeout_at", 0) > 0 and handoff.get("timeout_at", 0) < now_ts:
            if str(handoff.get("status", "pending")).lower() in {"pending", "accepted", "active"}:
                overdue.append(handoff)

    return overdue


def build_handoff_summary(
    handoffs: List[dict],
    limit: int = 10,
) -> dict:
    """Build a summary of handoff state for meta_reflection and self-audit."""
    now_ts = int(time.time())

    total = len(handoffs)
    pending = len([h for h in handoffs if str(h.get("status", "pending")).lower() in {"pending", "accepted", "active"}])
    resolved = len([h for h in handoffs if str(h.get("status", "pending")).lower() == "resolved"])
    rejected = len([h for h in handoffs if str(h.get("status", "pending")).lower() == "rejected"])

    acceptance_rate = resolved / (resolved + rejected) if (resolved + rejected) > 0 else 1.0

    # Track most active agents
    from_agents = {}
    to_agents = {}
    for h in handoffs:
        from_agents[h.get("from_agent", "unknown")] = from_agents.get(h.get("from_agent", "unknown"), 0) + 1
        to_agents[h.get("to_agent", "unknown")] = to_agents.get(h.get("to_agent", "unknown"), 0) + 1

    most_active_from = sorted(from_agents.items(), key=lambda x: x[1], reverse=True)[:5]
    most_active_to = sorted(to_agents.items(), key=lambda x: x[1], reverse=True)[:5]

    overdue_count = len(find_overdue_handoffs(handoffs, now_ts))

    return {
        "total_handoffs": total,
        "pending_handoffs": pending,
        "resolved_handoffs": resolved,
        "rejected_handoffs": rejected,
        "acceptance_rate": round(acceptance_rate, 3),
        "overdue_count": overdue_count,
        "most_active_from": most_active_from,
        "most_active_to": most_active_to,
        "average_timeout_seconds": sum(h.get("timeout_at", 0) - h.get("timestamp", 0) for h in handoffs) // max(1, total),
        "timestamp": now_ts,
    }


def export_handoff_note(handoff: dict, path: Path) -> None:
    """Export a handoff note to a JSON file for debugging."""
    path.write_text(json.dumps(handoff, indent=2))


def load_handoff_notes(path: Path) -> List[dict]:
    """Load handoff notes from a JSON file."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def save_handoff_notes(handoffs: List[dict], path: Path) -> None:
    """Save handoff notes to a JSON file."""
    path.write_text(json.dumps(handoffs, indent=2))


def build_handoff_payload(
    from_agent: str,
    to_agent: str,
    topic: str,
    task: str,
    context: dict | None = None,
) -> dict:
    """Build a handoff payload for agent_runtime integration.

    This is the structured state that gets passed between agents.
    """
    now_ts = int(time.time())

    return {
        "kind": "handoff",
        "handoff_id": f"handoff-{from_agent}-to-{to_agent}-{now_ts}",
        "timestamp": now_ts,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "topic": topic,
        "task": task,
        "context": dict(context or {}),
        "instructions": [
            f"Address the topic: {topic}",
            f"Task description: {task}",
            f"Context: {json.dumps(context or {}, indent=2)[:500]}",
        ],
        "expected_outcome": f"A response or action that advances understanding of {topic}",
        "timeout_seconds": 3600,
    }


def create_agent_handoff_chain(
    agents: List[str],
    topic: str,
    task_sequence: List[str],
    context: dict | None = None,
) -> List[dict]:
    """Create a chain of handoffs across multiple agents.

    Useful for multi-step reasoning or complex tasks.
    """
    now_ts = int(time.time())
    handoffs = []

    for i, agent in enumerate(agents):
        # Determine next agent in chain (or None for final)
        next_agent = agents[i + 1] if i + 1 < len(agents) else None

        handoff = create_handoff_note(
            from_agent=agent,
            to_agent=next_agent or "communicator",
            topic=topic,
            context={
                **(context or {}),
                "chain_position": i,
                "total_chain_length": len(agents),
                "step": task_sequence[i] if i < len(task_sequence) else "final_summary",
            },
            handoff_type="chain" if next_agent else "final",
            priority=0.7 if i < len(task_sequence) // 2 else 0.5,
        )

        # Add claim about the task
        if i < len(task_sequence):
            handoff = log_handoff_claim(
                handoff,
                f"Complete step {i + 1}: {task_sequence[i]}",
                f"This is step {i + 1} of {len(task_sequence)} in the chain",
            )

        handoffs.append(handoff)

    return handoffs
