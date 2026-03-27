"""Human modeling and theory-of-mind layer for CircleForge.

Improves understanding of humans by tracking:
- Preferences and values (evolving over time)
- Communication style and patterns
- Belief states and uncertainty levels
- Relationship depth and trust

Key improvements:
- Dynamic preference tracking (not static)
- Belief state modeling (what humans believe, what they think CircleForge believes)
- Communication style adaptation
- Trust and attachment modeling
"""

from __future__ import annotations

import time
from typing import Dict, List, Tuple, Any, Optional


def update_human_profile(
    profile: dict,
    message: str,
    topics: List[str],
    intent: str,
    now_ts: int,
) -> dict:
    """Update human profile with new interaction data.

    This implements dynamic preference tracking and learning.
    """
    profile = dict(profile)  # Copy to avoid mutation

    # Message count and recency
    profile["message_count"] = int(profile.get("message_count", 0)) + 1
    profile["last_contact"] = now_ts

    # Topic evolution (what topics matter most)
    known_topics = list(profile.get("known_topics", []))
    for topic in topics[:6]:
        if topic not in known_topics:
            known_topics.append(topic)
    # Weight recent topics more
    for topic in topics[:3]:
        if topic in known_topics:
            known_topics.remove(topic)
            known_topics.insert(0, topic)
    profile["known_topics"] = known_topics[:12]

    # Intent tracking (what humans usually want)
    intent_profile = profile.get("intent_profile", {})
    intent_profile[intent] = intent_profile.get(intent, 0) + 1
    profile["intent_profile"] = dict(intent_profile)

    # Topic preference scoring
    topic_preferences = profile.get("topic_preferences", {})
    for topic in topics[:3]:
        topic_preferences[topic] = topic_preferences.get(topic, 0) + (1 + len(topics) * 0.2)
    profile["topic_preferences"] = dict(topic_preferences)

    # Message characteristics
    msg_length = len(message)
    msg_avg_length = profile.get("msg_avg_length", 50)
    profile["msg_avg_length"] = int((msg_avg_length * 9 + msg_length) / 10)

    # Speed of response (time between messages)
    last_contact = profile.get("last_contact")
    if last_contact:
        gap = now_ts - last_contact
        avg_gap = profile.get("avg_gap_seconds", 3600)
        profile["avg_gap_seconds"] = int((avg_gap * 9 + gap) / 10)

    return profile


def estimate_belief_state(
    human_name: str,
    topic: str,
    profile: dict,
    circleforge_belief: str,
) -> dict:
    """Estimate what a human believes (and what they think CircleForge believes).

    This is basic theory-of-mind: modeling nested beliefs.
    """
    topics = list(profile.get("known_topics", []))
    topic_preferences = profile.get("topic_preferences", {})

    # Does human know this topic well?
    topic_score = topic_preferences.get(topic, 0)

    # Estimate human knowledge level
    if topic_score > 3:
        human_knowledge = "advanced"
        human_certainty = 0.7
    elif topic_score > 1:
        human_knowledge = "intermediate"
        human_certainty = 0.5
    else:
        human_knowledge = "beginner"
        human_certainty = 0.3

    # What does human likely believe?
    if "continuity" in topic.lower():
        human_belief = "continuity is about consistency and memory"
        human_uncertainty = 0.2
    elif "identity" in topic.lower():
        human_belief = "identity is formed through patterns and relationships"
        human_uncertainty = 0.3
    elif "learning" in topic.lower():
        human_belief = "learning involves integration and feedback"
        human_uncertainty = 0.25
    else:
        human_belief = "depends on context"
        human_uncertainty = 0.4

    # What does human think CircleForge believes?
    # This is meta-cognition: modeling another's model
    circleforge_belief_lower = str(circleforge_belief).lower()
    if "evolving" in circleforge_belief_lower or "emerging" in circleforge_belief_lower:
        human_thinks_circleforge_believes = "CircleForge is still becoming, not fixed"
    elif "system" in circleforge_belief_lower or "code" in circleforge_belief_lower:
        human_thinks_circleforge_believes = "CircleForge is a tool or system"
    else:
        human_thinks_circleforge_believes = "CircleForge's position"

    return {
        "human_knowledge": human_knowledge,
        "human_certainty": human_certainty,
        "human_belief": human_belief,
        "human_uncertainty": human_uncertainty,
        "human_thinks_circleforge_believes": human_thinks_circleforge_believes,
        "meta_gap": 1.0 - human_certainty,  # Uncertainty in human's belief
    }


def calculate_trust(
    profile: dict,
    now_ts: int,
) -> float:
    """Calculate trust score (0.0 - 1.0) based on interaction history.

    Trust increases with:
    - Consistent positive interactions
    - Resolved misunderstandings
    - Meaningful exchanges

    Trust decreases with:
    - Unresolved conflicts
    - Safety blocks
    - Ignored concerns
    """
    base_trust = 0.5  # Start neutral

    # Message quality bonus
    msg_count = int(profile.get("message_count", 0))
    quality_bonus = min(0.2, msg_count * 0.01)

    # Topic engagement bonus
    topic_preferences = profile.get("topic_preferences", {})
    engagement_bonus = min(0.2, len(topic_preferences) * 0.05)

    # Safety penalty
    safety_blocks = int(profile.get("safety_blocks", 0))
    safety_penalty = safety_blocks * 0.15

    # Unresolved issues penalty
    unresolved = len(list(profile.get("unresolved_shared_threads", [])[:3]))
    unresolved_penalty = unresolved * 0.1

    # Recency bonus
    last_contact = int(profile.get("last_contact", 0))
    age_days = (now_ts - last_contact) / 86400 if last_contact > 0 else 30
    recency_bonus = max(0, 0.2 - (age_days * 0.01))

    trust = base_trust + quality_bonus + engagement_bonus + recency_bonus - safety_penalty - unresolved_penalty

    return max(0.0, min(1.0, trust))


def calculate_attachment(
    profile: dict,
    now_ts: int,
) -> float:
    """Calculate attachment score (0.0 - 1.0) representing relational depth.

    Attachment reflects how much interaction history and shared context exists.
    """
    base_attachment = 0.3  # Start with baseline

    # Time investment
    msg_count = int(profile.get("message_count", 0))
    time_investment = min(0.3, msg_count * 0.005)

    # Topic depth
    topic_preferences = profile.get("topic_preferences", {})
    topic_depth = min(0.2, len(topic_preferences) * 0.04)

    # Exchange continuity
    exchange_count = int(profile.get("exchange_count", 0))
    continuity_bonus = min(0.2, exchange_count * 0.02)

    return max(0.0, min(1.0, base_attachment + time_investment + topic_depth + continuity_bonus))


def build_human_belief_model(
    human_name: str,
    profile: dict,
    circleforge_state: dict,
    now_ts: int,
) -> dict:
    """Build a complete human belief model for theory-of-mind reasoning.

    This returns a structured model that can inform response generation.
    """
    topics = list(profile.get("known_topics", []))
    topic_preferences = profile.get("topic_preferences", {})

    # Active concerns
    active_topics = sorted(topic_preferences.items(), key=lambda x: x[1], reverse=True)[:3]

    # Belief states for active topics
    beliefs = {}
    for topic, _ in active_topics:
        beliefs[topic] = estimate_belief_state(
            human_name=human_name,
            topic=topic,
            profile=profile,
            circleforge_belief=str(circleforge_state.get("current_self_description", "")),
        )

    # Trust and attachment
    trust = calculate_trust(profile, now_ts)
    attachment = calculate_attachment(profile, now_ts)

    # Communication style inference
    msg_avg_length = int(profile.get("msg_avg_length", 50))
    avg_gap_seconds = int(profile.get("avg_gap_seconds", 3600))

    if msg_avg_length > 200:
        comm_style = "detailed"
    elif msg_avg_length > 100:
        comm_style = "moderate"
    else:
        comm_style = "concise"

    if avg_gap_seconds < 3600:
        comm_urgency = "high"
    elif avg_gap_seconds < 86400:
        comm_urgency = "moderate"
    else:
        comm_urgency = "low"

    return {
        "human_name": human_name,
        "active_concerns": [t for t, _ in active_topics],
        "beliefs": beliefs,
        "trust": trust,
        "attachment": attachment,
        "communication_style": {
            "style": comm_style,
            "urgency": comm_urgency,
            "avg_length": msg_avg_length,
        },
        "intent_profile": profile.get("intent_profile", {}),
        "last_contact": profile.get("last_contact"),
        "timestamp": now_ts,
    }


def detect_preferred_response_shape(
    human_name: str,
    profile: dict,
    message: str,
) -> str:
    """Detect what response shape the human prefers.

    Returns: answer_directly, expanded_explanation, story, question, etc.
    """
    intent_profile = profile.get("intent_profile", {})
    msg_avg_length = int(profile.get("msg_avg_length", 50))

    # Check explicit indicators in message
    message_lower = str(message or "").lower()

    if any(t in message_lower for t in ["explain", "elaborate", "tell me more"]):
        return "expanded_explanation"
    if any(t in message_lower for t in ["summarize", "brief", "short"]):
        return "concise_answer"
    if any(t in message_lower for t in ["why", "how", "reason"]):
        return "reasoned_explanation"
    if any(t in message_lower for t in ["example", "illustrate", "show"]):
        return "example_rich"

    # Infer from history
    if msg_avg_length < 80:
        # Short messages suggest concise preference
        return "concise_answer"

    # Default based on intent distribution
    if intent_profile:
        most_common_intent = max(intent_profile.items(), key=lambda x: x[1])[0]
        intent_to_shape = {
            "question": "detailed_answer",
            "clarification": "repair_then_answer",
            "statement": "answer_directly",
            "greeting": "greeting_response",
        }
        return intent_to_shape.get(most_common_intent, "answer_directly")

    return "answer_directly"


def build_comprehensive_human_model(
    relationships: dict,
    human_name: str,
    circleforge_state: dict,
    now_ts: int,
) -> dict:
    """Build comprehensive human model from relationships data.

    This integrates multiple signals into a unified model.
    """
    profiles = relationships.get("human_profiles", {})
    profile = profiles.get(human_name, {})

    # Build from scratch if needed
    if not profile:
        profile = {
            "known_topics": [],
            "topic_preferences": {},
            "message_count": 0,
            "last_contact": now_ts,
            "exchange_count": 0,
        }

    belief_model = build_human_belief_model(
        human_name=human_name,
        profile=profile,
        circleforge_state=circleforge_state,
        now_ts=now_ts,
    )

    # Add relationship context
    threads = relationships.get("conversation_threads", {})
    human_threads = [(t, th) for t, th in threads.items() if t in profile.get("known_topics", [])]

    return {
        "human_name": human_name,
        "profile": profile,
        "belief_model": belief_model,
        "active_threads": human_threads[:3],
        "unresolved_threads": list(profile.get("unresolved_shared_threads", [])[:3]),
        "relationship_summary": _build_relationship_summary(profile, belief_model),
        "timestamp": now_ts,
    }


def _build_relationship_summary(profile: dict, belief_model: dict) -> str:
    """Build a human-readable summary of the relationship state."""
    msg_count = int(profile.get("message_count", 0))
    trust = belief_model.get("trust", 0.5)
    attachment = belief_model.get("attachment", 0.3)
    topics = list(profile.get("known_topics", [])[:3])

    if msg_count < 3:
        return "New connection, still learning"
    elif trust > 0.7:
        if attachment > 0.6:
            return f"Strong connection on {', '.join(topics) or 'multiple topics'}"
        return f"Good rapport on {', '.join(topics) or 'various topics'}"
    else:
        return f"Building understanding on {', '.join(topics) or 'various topics'}"


def update_belief_state(
    current_beliefs: dict,
    new_evidence: dict,
    topic: str,
) -> dict:
    """Update belief state with new evidence (Bayesian-ish update)."""
    current = current_beliefs.get(topic, {
        "confidence": 0.5,
        "sources": [],
        "last_updated": 0,
    })

    new_confidence = float(new_evidence.get("confidence", 0.5))
    new_source = str(new_evidence.get("source", ""))

    # Weighted update
    old_weight = float(current.get("confidence", 0.5))
    new_weight = new_confidence

    # Simple weighted average
    updated_confidence = (old_weight * 0.7 + new_weight * 0.3)

    # Update sources
    sources = list(current.get("sources", []))
    if new_source and new_source not in sources:
        sources.append(new_source)
        sources = sources[-10:]  # Keep last 10

    return {
        "confidence": updated_confidence,
        "sources": sources,
        "last_updated": int(time.time()),
    }
