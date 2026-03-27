"""Per-layer glue layer for CircleForge.

This module provides clean orchestration between extracted layers,
reducing orchestration glue in sim.py while maintaining behavioral quality.

Goal: Each sim.py function should call *one* layer function, not mix layers.
"""

from __future__ import annotations

import time
from typing import List, Dict, Any, Optional, Tuple


# ============== Human Exchange Glue ==============


def process_human_exchange(
    human_name: str,
    message: str,
    relationships: dict,
    self_state: dict,
    now_ts: int,
) -> Tuple[dict, dict]:
    """Orchestrate human exchange processing across layers.

    Returns (updated_relationships, exchange_payload)
    """
    # 1. Safety layer
    from safety_gateway import get_safety_gateway
    safety = get_safety_gateway()
    human_input = {"text": message}
    input_result = safety.check_input(human_input)
    
    if not input_result.safe:
        return _handle_safety_block(human_name, message, relationships, now_ts), {}

    # 2. Interpretation layer
    from interpretation import interpret_human_turn, infer_human_topics
    from relational import canonical_human_slot
    human_name = canonical_human_slot(human_name)
    
    interpreted_turn = interpret_human_turn(message)
    topic_list = _resolve_topics(interpreted_turn, relationships, self_state, message, human_name)
    
    # 3. Perception layer
    from perception import build_human_exchange_payload
    response = ""  # Response will be generated later
    exchange, recent_message = build_human_exchange_payload(
        human_name=human_name,
        display_name=relationships.get("human_profiles", {}).get(human_name, {}).get("label", human_name),
        message=message,
        response=response,
        topic_list=topic_list,
        interpreted_turn=interpreted_turn,
        now_ts=now_ts,
    )

    # 4. Update relationships (continuity/relational layer)
    relationships = _update_exchange_relationships(
        human_name, message, topic_list, interpreted_turn, relationships, now_ts
    )

    # 5. Trigger autonomous research if needed (inquiry layer)
    # Note: Research triggering is handled by sim.py's record_human_exchange wrapper
    # to avoid circular dependencies during migration

    return relationships, exchange


def _resolve_topics(
    interpreted_turn: dict,
    relationships: dict,
    self_state: dict,
    message: str,
    human_name: str,
) -> List[str]:
    """Resolve topics using interpretation + fallback heuristics.

    This extracts topic inference logic from sim.py glue.
    """
    from interpretation import infer_human_topics
    from relational import canonical_human_slot
    
    topic_list = [topic for topic in (interpreted_turn.get("topics") or []) if topic]
    
    if not topic_list:
        recent_human_messages = list(relationships.get("recent_human_messages") or [])
        recent_topics = []
        for item in reversed(recent_human_messages[-6:]):
            for topic in list(item.get("topics") or []):
                topic = str(topic).strip()
                if topic and topic not in recent_topics:
                    recent_topics.append(topic)
        
        semantic = (self_state.get("memory_layers") or {}).get("semantic") or {}
        active_concern_topics = [str(t).strip() for t in (semantic.get("active_concern_topics") or []) if str(t).strip()]
        continuity_anchors = [str(t).strip() for t in (semantic.get("continuity_anchors") or []) if str(t).strip()]
        stable_topics = [str(t).strip() for t in (semantic.get("stable_topics") or []) if str(t).strip()]
        unresolved_threads = [str(t).strip() for t in (relationships.get("unresolved_shared_threads") or []) if str(t).strip()]
        
        candidate_topics = []
        for topic in unresolved_threads + continuity_anchors + stable_topics + active_concern_topics + recent_topics:
            if topic and topic not in candidate_topics:
                candidate_topics.append(topic)
        
        def fallback_topic_score(topic: str) -> Tuple[float, float]:
            lowered = topic.lower()
            score = 0.0
            if topic in unresolved_threads:
                score += 3.0
            if topic in continuity_anchors:
                score += 2.0
            if topic in stable_topics:
                score += 1.5
            if topic in active_concern_topics:
                score += 1.0
            if any(token in lowered for token in ["understand", "continuity", "memory", "conversation", "learn"]):
                score += 1.25
            recency_bonus = 0.0
            if topic in recent_topics:
                recency_bonus = max(0.0, 0.6 - (0.1 * recent_topics.index(topic)))
            return (score, recency_bonus)
        
        candidate_topics.sort(key=fallback_topic_score, reverse=True)
        topic_list = [topic for topic in candidate_topics if topic][:1]
    
    return topic_list


def _update_exchange_relationships(
    human_name: str,
    message: str,
    topic_list: List[str],
    interpreted_turn: dict,
    relationships: dict,
    now_ts: int,
) -> dict:
    """Update relationship state after human exchange.

    This extracts relationship updates from sim.py.
    """
    from relational import canonical_human_slot, display_human_label
    
    human_name = canonical_human_slot(human_name)
    if human_name not in relationships.get("known_humans", []):
        relationships.setdefault("known_humans", []).append(human_name)

    relations = relationships
    relations["last_human_topic"] = str(interpreted_turn.get("clarified_target") or "").strip() or (
        topic_list[0] if topic_list else relations.get("last_human_topic", "")
    )
    relations["human_salience"] = min(1.0, float(relations.get("human_salience", 0.1)) + 0.03 + (0.01 * min(len(topic_list), 2)))

    profile = relations.setdefault("human_profiles", {}).setdefault(human_name, {
        "message_count": 0,
        "first_contact": now_ts,
        "last_contact": now_ts,
        "label": display_human_label(human_name),
        "topics": [],
    })
    profile["message_count"] += 1
    profile["last_contact"] = now_ts
    for topic in topic_list:
        if topic not in profile.get("topics", []):
            profile.setdefault("topics", []).append(topic)

    relations.setdefault("recent_human_messages", []).append({
        "id": f"human-exchange-{human_name}-{now_ts}",
        "type": "exchange",
        "message": message[:240],
        "timestamp": now_ts,
        "topics": topic_list,
        "intent": interpreted_turn.get("intent", ""),
    })
    relations.setdefault("recent_human_exchanges", []).append({
        "human": human_name,
        "message": message[:240],
        "topics": topic_list,
        "timestamp": now_ts,
    })

    return relations


def _handle_safety_block(
    human_name: str,
    message: str,
    relationships: dict,
    now_ts: int,
) -> dict:
    """Handle safety-blocked input gracefully.

    Logs the block but continues recording for operator review.
    """
    relations = relationships
    relations.setdefault("safety_blocks", []).append({
        "timestamp": now_ts,
        "human": human_name,
        "reason": "Safety check failed",
        "message": message[:100],
    })
    relations.setdefault("recent_human_messages", []).append({
        "id": f"human-exchange-{human_name}-{now_ts}-block",
        "type": "safety_blocked",
        "message": message[:240],
        "timestamp": now_ts,
    })
    return relations


# ============== Internal Glue ==============


def orchestrate_internal_handoff(
    from_layer: str,
    to_layer: str,
    data: dict,
    state: dict,
) -> Tuple[dict, Optional[dict]]:
    """Orchestrate handoff from one internal layer to another.

    Returns (updated_state, handoff_payload if any)
    """
    from integration import find_relevant_research_note, integrate_research_into_communicator
    
    # Default: just pass through
    return state, None


def reduce_context_pressure(
    state: dict,
    max_working_topics: int = 5,
    max_unresolved: int = 3,
) -> dict:
    """Reduce context pressure by prioritizing working memory.

    Extracts logic from sim.py's memory pressure management.
    """
    memory_layers = state.get("memory_layers", {})
    working = memory_layers.get("working", {})
    
    # Cap working topics
    if len(working.get("active_concern_topics", [])) > max_working_topics:
        working["active_concern_topics"] = working["active_concern_topics"][:max_working_topics]
    
    # Cap unresolved questions
    if len(working.get("unresolved_questions", [])) > max_unresolved:
        working["unresolved_questions"] = working["unresolved_questions"][:max_unresolved]
    
    memory_layers["working"] = working
    state["memory_layers"] = memory_layers
    
    return state

# ============== Memory archival glue ==============


def orchestrate_memory_archival(
    self_state: dict,
    now_ts: int | None = None,
) -> dict:
    """Orchestrate memory archival across layers.

    Calls:
    - continuity_prioritizer.clear_stale_threads()
    - semantic_memory.archive_stale()
    - glue.reduce_context_pressure()
    """
    now_ts = now_ts or int(time.time())
    
    # 1. Clear stale threads
    relationships = self_state.get("relationships", {})
    from continuity_prioritizer import clear_stale_threads
    relationships = clear_stale_threads(relationships, now_ts)
    self_state["relationships"] = relationships
    
    # 2. Archive stale working memory
    from continuity import apply_human_exchange_to_threads, should_passively_reinforce_thread
    from config import CIRCLEFORGE_THREAD_REINFORCEMENT_COOLDOWN_SECONDS
    from config import CIRCLEFORGE_THREAD_MAX_PASSIVE_REINFORCEMENTS
    
    self_state = archive_all_stale(self_state, now_ts)
    
    # 3. Reduce context pressure
    self_state = reduce_context_pressure(self_state)
    
    return self_state


def archive_all_stale(self_state: dict, now_ts: int | None = None) -> dict:
    """Archive all stale memory items.

    Calls archive_stale_working_memory from sim.py for actual logic.
    This is a temporary bridge - full refactoring will extract the logic.
    """
    now_ts = now_ts or int(time.time())
    
    # Import from sim to avoid circular dependencies during migration
    from sim import archive_stale_working_memory
    
    # Call the actual sim.py implementation
    return archive_stale_working_memory(self_state, now_ts)
