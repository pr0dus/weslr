"""Perception layer for CircleForge.

Handles incoming data streams, environmental sensing, attention filtering,
and input prioritization for the communicator entity.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple, Any


def build_human_exchange_payload(
    human_name: str,
    display_name: str,
    message: str,
    response: str,
    topic_list: List[str],
    interpreted_turn: dict,
    now_ts: int,
) -> Tuple[dict, dict]:
    """Build exchange and recent message payloads from a human interaction.

    This is the low-level perception output that feeds into continuity and memory.
    """
    message_text = str(message or "")
    response_text = str(response or "")
    clarified_target = str(interpreted_turn.get("clarified_target") or "").strip()
    exchange = {
        "id": f"hx-{now_ts}",
        "human": human_name,
        "human_label": display_name,
        "topics": topic_list,
        "clarified_target": clarified_target,
        "has_explicit_clarification": bool(interpreted_turn.get("has_explicit_clarification")),
        "message_summary": (message_text[:96] + ("…" if len(message_text) > 96 else "")),
        "response_summary": (response_text[:96] + ("…" if len(response_text) > 96 else "")),
        "created_at": now_ts,
        "source": "human_exchange",
    }
    recent_message = {
        "human": human_name,
        "human_label": display_name,
        "topics": topic_list,
        "clarified_target": clarified_target,
        "has_explicit_clarification": bool(interpreted_turn.get("has_explicit_clarification")),
        "message": message_text[:240],
        "response": response_text[:240],
        "turn_type": interpreted_turn.get("turn_type", "statement"),
        "intent": interpreted_turn.get("intent", ""),
        "stance": interpreted_turn.get("stance", "neutral"),
        "reply_shape": interpreted_turn.get("reply_shape", "answer_directly"),
        "likely_need": interpreted_turn.get("likely_need", "direct_answer"),
        "created_at": now_ts,
    }
    return exchange, recent_message


def filter_attention_demand(input_type: str, content: Any, priority: float) -> Tuple[bool, float]:
    """Filter incoming stimuli by attention demand.

    Returns (should_capture, adjusted_priority).

    Priority scaling rules:
    - High-demand items get boosted
    - Low-priority items decay
    - Filtering is based on type and content characteristics
    """
    base_priority = float(priority or 0)

    if input_type in ("crisis", "urgent"):
        return True, min(base_priority * 3.0, 10.0)
    if input_type in ("curiosity_trigger", "unresolved"):
        return True, min(base_priority * 2.0, 10.0)
    if input_type == "repetition":
        return False, 0.0
    if input_type == "low_signal":
        return False, max(base_priority * 0.3, 0.0)
    if input_type in ("continuity_refresh", "background"):
        return False, max(base_priority * 0.5, 0.0)

    # Default: pass through with slight decay
    return True, max(base_priority * 0.8, 0.1)


def calculate_attention_score(
    input_type: str,
    content: Any,
    human关系: Optional[str] = None,
    topic_relevance: float = 0.5,
    urgency: float = 0.5,
    novelty: float = 0.5,
) -> float:
    """Calculate a normalized attention score (0.0 - 10.0) for incoming stimuli.

    This score determines how quickly an item captures the communicator's attention
    and how long it holds focus.
    """
    base_score = 5.0

    # Type modifiers
    type_modifiers = {
        "human_message": 1.2,
        "system_alert": 1.5,
        "unresolved_thread": 1.8,
        "curiosity_trigger": 2.0,
        "crisis": 2.5,
        "background_update": 0.7,
    }
    base_score *= type_modifiers.get(input_type, 1.0)

    # Relevance boost
    base_score *= (0.5 + topic_relevance)

    # Urgency boost
    base_score *= (0.5 + urgency)

    # Novelty bonus (diminishing returns)
    base_score += (novelty * 2.0)

    # Human relationship bonus (stronger for direct relationships)
    if human关系 == "direct":
        base_score *= 1.3
    elif human关系 == "indirect":
        base_score *= 1.1

    return min(max(base_score, 0.0), 10.0)


def prioritize_input_queue(inputs: List[dict]) -> List[dict]:
    """Sort inputs by attention score, highest first.

    Each input should have a 'type' field and optional 'topic_relevance', 'urgency', 'novelty'.
    """
    def score_input(item: dict) -> float:
        return calculate_attention_score(
            input_type=item.get("type", "unknown"),
            content=item.get("content"),
            human关系=item.get("human_relation"),
            topic_relevance=float(item.get("topic_relevance", 0.5)),
            urgency=float(item.get("urgency", 0.5)),
            novelty=float(item.get("novelty", 0.5)),
        )

    return sorted(inputs, key=score_input, reverse=True)


def extract_topics_from_perception(input_type: str, content: Any) -> List[str]:
    """Extract potential topics from a perception event."""
    topics = []

    if input_type == "human_message" and isinstance(content, dict):
        topics.extend(content.get("topics", []))
        if "clarified_target" in content:
            topics.append(content["clarified_target"])

    if input_type in ("unresolved_thread", "continuity_refresh"):
        if isinstance(content, str):
            topics.append(content)
        elif isinstance(content, dict):
            topics.extend(content.get("topics", []))

    return list(set(topics))  # Deduplicate


def build_attention_snapshot(
    current_attention: List[str],
    pending_inputs: List[dict],
    active_threads: List[str],
    unresolved_questions: List[str],
) -> dict:
    """Build a snapshot of current attention state.

    This is used by meta_reflection and self_model layers to understand
    where attention is focused and what might need shifting.
    """
    return {
        "current_focus": current_attention,
        "pending_stimuli": [i.get("type") for i in pending_inputs[:5]],
        "active_threads": active_threads[:5],
        "unresolved_priority": unresolved_questions[:3],
        "attention_load": len(current_attention) + len(pending_inputs),
        "timestamp": int(time.time()),
    }


def reset_attention_filter() -> dict:
    """Return default attention filter configuration.

    This resets attention rules to baseline.
    """
    return {
        "threshold": 3.0,
        "decay_rate": 0.9,
        "max_concurrent": 5,
        "priority_boost_types": ["crisis", "unresolved_thread"],
        "auto_decay_types": ["background_update", "continuity_refresh"],
    }
