"""
weslr/proactive_suggestions.py
==============================
Proactive Suggestions — V1 (First Safe Jarvis-like Suggestion Experiment)

Generates one optional, safe next-step suggestion from recent user timeline summaries.
Read-only — no writes, no execution, no background loops.

Purpose:
    First step toward Jarvis-like proactive behavior — WESLR can suggest
    a useful next step without being asked. Can later be surfaced via chat or voice.

Rules (strict):
    - No writes to any file
    - No JSONL writes
    - No action execution
    - No Ollama or external calls
    - No background loop
    - No /chat integration
    - Suggestion always phrased as optional ("You could...", "Would you like to...")
    - Never says "I will do this"

Author: OCC (WESLR governed intelligence)
Version: 1.0.0
"""

from __future__ import annotations

from typing import Dict, List, Optional

from weslr.user_timeline_memory import load_recent_session_summaries

# ── Theme detection ─────────────────────────────────────────────────────────

_THEME_PATTERNS: Dict[str, List[str]] = {
    "continuity": ["jarvis", "memory", "continuity", "timeline", "recall", "remember", "last time"],
    "evidence": ["evidence", "search", "source", "citation", "prove", "research"],
    "capability_discovery": ["help", "capability", "command", "what can", "available"],
    "experiment": ["test", "experiment", "try", "validate", "checkpoint"],
    "governance": ["governance", "safety", "approval", "operator", "scope", "doctrine"],
}

_SUGGESTION_MAP: Dict[str, dict] = {
    "continuity": {
        "suggestion": "You could test the continuity note bridge to confirm WESLR recalls your recent session correctly.",
        "reason": "Your recent sessions involved continuity and memory experiments.",
        "related_capability": "continuity_note_chat_bridge",
        "operator_approval_required": False,
    },
    "evidence": {
        "suggestion": "You could run a source-quality check — try /evidence on a topic and review whether citations feel grounded.",
        "reason": "Your recent sessions included evidence and search-related work.",
        "related_capability": "evidence.search",
        "operator_approval_required": False,
    },
    "capability_discovery": {
        "suggestion": "Would you like to explore what WESLR capabilities are available? Try asking \"what can you do?\"",
        "reason": "Your recent sessions involved capability discovery and command exploration.",
        "related_capability": "capability.discovery",
        "operator_approval_required": False,
    },
    "experiment": {
        "suggestion": "You could define one small concrete experiment — pick a specific behavior to test and a success criterion.",
        "reason": "Your recent sessions referenced testing and experiments.",
        "related_capability": "experiments.plan",
        "operator_approval_required": False,
    },
    "governance": {
        "suggestion": "You could review the current governance boundaries — check REPO_GUARD and the Jarvis gap assessment.",
        "reason": "Your recent sessions involved governance and safety considerations.",
        "related_capability": "governance.review",
        "operator_approval_required": True,
    },
}


def classify_timeline_theme(summary_text: str) -> dict:
    """Detect the theme of a summary string using deterministic keyword matching.

    Args:
        summary_text: Raw summary string

    Returns:
        dict with keys: theme (str), confidence (float 0.0-1.0), matched_terms (list)
    """
    if not summary_text or not isinstance(summary_text, str):
        return {"theme": "unknown", "confidence": 0.0, "matched_terms": []}

    text_lower = summary_text.lower()
    matched: List[str] = []

    for theme, keywords in _THEME_PATTERNS.items():
        hits = [kw for kw in keywords if kw in text_lower]
        if hits:
            matched.append(theme)

    if not matched:
        return {"theme": "unknown", "confidence": 0.0, "matched_terms": []}

    # Return the first matching theme with confidence based on number of hits
    primary_theme = matched[0]
    keyword_hits = [kw for kw in _THEME_PATTERNS[primary_theme] if kw in text_lower]
    confidence = min(0.3 + 0.2 * len(keyword_hits), 1.0)

    return {
        "theme": primary_theme,
        "confidence": round(confidence, 2),
        "matched_terms": keyword_hits,
    }


def build_suggestion_from_theme(theme: str) -> Optional[dict]:
    """Map a theme to a pre-defined safe suggestion.

    Args:
        theme: One of the defined theme keys

    Returns:
        dict with suggestion fields, or None if theme is unknown
    """
    if theme == "unknown" or theme not in _SUGGESTION_MAP:
        return None

    entry = _SUGGESTION_MAP[theme].copy()
    entry["operator_approval_required"] = entry.get("operator_approval_required", False)
    return entry


def build_proactive_suggestion(
    user_id: str = "arthur",
    base_dir: str = ".weslr/timelines",
) -> dict:
    """Build one optional next-step suggestion from recent user timeline summaries.

    Read-only — no writes, no execution, no JSONL, no background loop.

    Args:
        user_id: Which user timeline to read
        base_dir: Timeline base directory

    Returns:
        dict with:
            record_type: "proactive_suggestion_v1"
            user_id, suggestion_available, suggestion, reason,
            related_capability, source, authority,
            automatic_action=False, operator_approval_required,
            hidden_learning=False, raw_prompt_stored=False
    """
    events = load_recent_session_summaries(user_id, limit=5, base_dir=base_dir)

    if not events:
        return {
            "record_type": "proactive_suggestion_v1",
            "user_id": user_id,
            "suggestion_available": False,
            "suggestion": None,
            "reason": "No recent timeline summaries found.",
            "related_capability": None,
            "source": "user_timeline_memory",
            "authority": "suggestion_only",
            "automatic_action": False,
            "operator_approval_required": False,
            "hidden_learning": False,
            "raw_prompt_stored": False,
        }

    # Classify each summary, pick the most confident theme
    theme_scores: Dict[str, float] = {}
    for event in events:
        result = classify_timeline_theme(event.get("summary", ""))
        theme = result["theme"]
        if theme == "unknown":
            continue
        confidence = result["confidence"]
        if theme not in theme_scores or confidence > theme_scores[theme]:
            theme_scores[theme] = confidence

    if not theme_scores:
        return {
            "record_type": "proactive_suggestion_v1",
            "user_id": user_id,
            "suggestion_available": False,
            "suggestion": None,
            "reason": "Recent summaries found but no strong theme detected.",
            "related_capability": None,
            "source": "user_timeline_memory",
            "authority": "suggestion_only",
            "automatic_action": False,
            "operator_approval_required": False,
            "hidden_learning": False,
            "raw_prompt_stored": False,
        }

    # Pick the highest-scoring theme
    best_theme = max(theme_scores, key=lambda t: theme_scores[t])
    suggestion_data = build_suggestion_from_theme(best_theme)

    if not suggestion_data:
        return {
            "record_type": "proactive_suggestion_v1",
            "user_id": user_id,
            "suggestion_available": False,
            "suggestion": None,
            "reason": f"Theme '{best_theme}' detected but no suggestion available.",
            "related_capability": None,
            "source": "user_timeline_memory",
            "authority": "suggestion_only",
            "automatic_action": False,
            "operator_approval_required": False,
            "hidden_learning": False,
            "raw_prompt_stored": False,
        }

    return {
        "record_type": "proactive_suggestion_v1",
        "user_id": user_id,
        "suggestion_available": True,
        "suggestion": suggestion_data["suggestion"],
        "reason": suggestion_data["reason"],
        "related_capability": suggestion_data["related_capability"],
        "source": "user_timeline_memory",
        "authority": "suggestion_only",
        "automatic_action": False,
        "operator_approval_required": suggestion_data.get("operator_approval_required", False),
        "hidden_learning": False,
        "raw_prompt_stored": False,
    }