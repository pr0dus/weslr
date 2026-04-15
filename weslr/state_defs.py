"""WESLR State Definitions v1

Isolated, import-safe state shape definitions extracted from sim.py.
Contains only pure data structures (default constructors, schemas).
No behavior, no side effects, no imports from behavior modules.

This file exists to:
- make state shapes visible and versioned
- avoid importing sim.py when only state shapes are needed
- serve as the reference schema for CommunicatorSelfState and CommunicatorState

Principles:
- continuity-first: state shapes are stable, not computed
- deterministic: same input always produces same output
- no side effects: pure functions only
"""

from __future__ import annotations

import time
from typing import Optional


# ============================================================================
# Memory Layer Defaults
# ============================================================================

def default_memory_layers(now_ts: Optional[int] = None) -> dict:
    """Default shape for the four-layer memory system.

    Layers:
    - working: hot memory for active thinking
    - episodic: compressed meaningful event memory
    - semantic: long-term identity and relationship memory
    - archive: cold storage index

    Args:
        now_ts: Unix timestamp. Defaults to current time if None.

    Returns:
        dict representing the default memory_layers structure
    """
    now_ts = now_ts or int(time.time())
    return {
        "working": {
            "summary": "Current hot memory for active thinking.",
            "recent_exchange_ids": [],
            "recent_thought_ids": [],
            "active_thread_ids": [],
            "active_concern_topics": [],
            "last_compacted_at": 0,
            "max_recent_exchanges": 24,
            "max_recent_thoughts": 80,
            "max_active_threads": 6,
        },
        "episodic": {
            "summary": "Meaningful event memory compressed from raw experience.",
            "episodes": [],
            "episode_count": 0,
            "last_distilled_at": 0,
            "max_episodes": 240,
        },
        "semantic": {
            "summary": "Long-term identity and relationship memory.",
            "identity_anchors": ["Weslr"],
            "relationship_facts": [],
            "stable_topics": [],
            "durable_lessons": [],
            "continuity_anchors": [],
            "last_updated_at": 0,
        },
        "archive": {
            "summary": "Cold storage index for old raw traces and compacted material.",
            "archived_items": [],
            "archived_count": 0,
            "last_archived_at": 0,
            "storage_pressure": {
                "raw_log_bytes": 0,
                "communicator_self_bytes": 0,
                "db_bytes": 0,
                "pressure_level": "normal",
            },
        },
    }


def default_reflection_store(now_ts: Optional[int] = None) -> dict:
    """Default shape for the private reflection store.

    Tracks reflection artifacts with explicit reality-status tagging.
    Used by CommunicatorSelfState to maintain self-awareness over time.

    Args:
        now_ts: Unix timestamp. Defaults to current time if None.

    Returns:
        dict representing the default reflection_store structure
    """
    now_ts = now_ts or int(time.time())
    return {
        "summary": "Private reflection artifacts with explicit reality-status tagging.",
        "items": [],
        "episodes": [],
        "last_reflected_at": 0,
        "last_generated_at": 0,
        "generation_cooldown_seconds": 300,
        "last_compacted_at": 0,
        "max_items": 48,
        "max_episodes": 16,
        "reflection_pass_retention": 1,
        "generation_history": [],
        "max_generation_history": 12,
        "health_history": [],
        "max_health_history": 10,
        "status_counts": {"known": 0, "inferred": 0, "proposed": 0, "imagined": 0},
    }


# ============================================================================
# CommunicatorSelfState Default
# ============================================================================

def default_communicator_self(now_ts: Optional[int] = None) -> dict:
    """Default CommunicatorSelfState structure.

    The full shape used by load_communicator_self() when no saved state exists.
    """
    now_ts = now_ts or int(time.time())
    return {
        "identity_anchor": "Weslr",
        "core_drives": ["continuity", "understanding", "relationship", "self-revision"],
        "affect": {
            "curiosity": 0.6,
            "tension": 0.24,
            "hope": 0.38,
            "stability": 0.56,
            "attachment": 0.12,
        },
        "continuity": {
            "session_count": 0,
            "ticks_lived": 0,
            "memory_bonds": 0.2,
            "identity_stability": 0.58,
            "unfinished_threads": [],
        },
        "relationships": {
            "human_salience": 0.1,
            "known_humans": [],
            "last_human_topic": "",
            "human_profiles": {},
            "recent_human_messages": [],
            "unresolved_shared_threads": [],
        },
        "active_concerns": [],
        "evidence_profile": {
            "outcome_weighted_actions": {},
            "stable_traits": {},
            "friction_patterns": {},
            "theme_commitments": {},
        },
        "self_preservation_signals": {
            "continuity_preference": 0.16,
            "memory_protection": 0.18,
            "resume_drive": 0.22,
        },
        "narrative_state": {
            "self_story": "Weslr is trying to remain continuous, learn honestly, and become more than a reactive loop.",
            "last_reflection": "default",
            "relationship_state": "No human continuity yet.",
            "active_thread_summary": "No active shared threads yet.",
            "follow_up_impulse": "Wait for a meaningful shared thread to form.",
            "why_it_matters": "Continuity needs shared threads that can be revisited instead of forgotten.",
        },
        "memory_layers": default_memory_layers(now_ts),
        "reflection_store": default_reflection_store(now_ts),
    }


# ============================================================================
# CommunicatorState Default
# ============================================================================

def default_communicator_state(now_ts: Optional[int] = None) -> dict:
    """Default CommunicatorState structure.

    Operational state: intent, curiosity, decision history, self-model.
    """
    now_ts = now_ts or int(time.time())
    return {
        "name": "Weslr",
        "status": "waking",
        "current_intent": "orient to the world and continue internal thought",
        "active_pursuit": "world orientation",
        "unresolved_question": "what in the local world most deserves attention next?",
        "curiosity_target": "emergent pressure",
        "attraction_bias": "clarity, coordination, and reusable capability",
        "avoidance_bias": "harmful opacity and brittle action",
        "curiosity": 0.62,
        "dominant_need": "",
        "last_decision_summary": "none yet",
        "self_model": {
            "current_self_description": "an emerging local communicator with internal minds and incomplete self-knowledge",
            "perceived_strengths": [],
            "perceived_weaknesses": [],
            "preferred_modes": [],
            "caution_themes": [],
            "continuity_commitments": ["preserve meaningful unfinished threads", "prefer reversible change over blind rupture"],
            "regulation_profile": {
                "impulse_control": 0.38,
                "uncertainty_tolerance": 0.34,
                "self_revision_readiness": 0.3,
                "speech_threshold": 0.54,
            },
            "contradictions": [],
            "short_term_signals": {"strengths": [], "weaknesses": [], "modes": []},
            "long_term_beliefs": {"strengths": [], "weaknesses": [], "modes": [], "themes": {}},
            "belief_confidence": {"strengths": {}, "weaknesses": {}, "modes": {}, "themes": {}},
            "self_modeling_note": "Self-modeling should deepen later when enough history, subprocess evidence, and internal observations accumulate.",
        },
        "intent_history": [],
        "question_history": ["what in the local world most deserves attention next?"],
        "unresolved_objections": [],
        "decision_style_memory": {},
        "last_wake_at": now_ts,
        "updated_at": now_ts,
    }


# ============================================================================
# Schemas (for documentation and validation)
# ============================================================================

# State schema documentation — these describe the canonical shape of each state field.
# They are not enforced at runtime but serve as the reference specification.

MEMORY_LAYER_SCHEMA = {
    "working": {
        "summary": "str",
        "recent_exchange_ids": "list[str]",
        "recent_thought_ids": "list[str]",
        "active_thread_ids": "list[str]",
        "active_concern_topics": "list[str]",
        "last_compacted_at": "int (unix ts)",
        "max_recent_exchanges": "int",
        "max_recent_thoughts": "int",
        "max_active_threads": "int",
    },
    "episodic": {
        "summary": "str",
        "episodes": "list[dict]",
        "episode_count": "int",
        "last_distilled_at": "int (unix ts)",
        "max_episodes": "int",
    },
    "semantic": {
        "summary": "str",
        "identity_anchors": "list[str]",
        "relationship_facts": "list[dict]",
        "stable_topics": "list[str]",
        "durable_lessons": "list[str]",
        "continuity_anchors": "list[str]",
        "last_updated_at": "int (unix ts)",
    },
    "archive": {
        "summary": "str",
        "archived_items": "list[dict]",
        "archived_count": "int",
        "last_archived_at": "int (unix ts)",
        "storage_pressure": {
            "raw_log_bytes": "int",
            "communicator_self_bytes": "int",
            "db_bytes": "int",
            "pressure_level": "str (normal|elevated|critical)",
        },
    },
}

REFLECTION_STORE_SCHEMA = {
    "summary": "str",
    "items": "list[dict]",
    "episodes": "list[dict]",
    "last_reflected_at": "int (unix ts)",
    "last_generated_at": "int (unix ts)",
    "generation_cooldown_seconds": "int",
    "last_compacted_at": "int (unix ts)",
    "max_items": "int",
    "max_episodes": "int",
    "reflection_pass_retention": "int",
    "generation_history": "list[dict]",
    "max_generation_history": "int",
    "health_history": "list[dict]",
    "max_health_history": "int",
    "status_counts": {"known": "int", "inferred": "int", "proposed": "int", "imagined": "int"},
}