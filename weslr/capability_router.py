"""WESLR Capability Router V1 — Deterministic Request Classifier

Classifies user messages into WESLR capability IDs using deterministic keyword
matching against the Capability Registry. No LLM calls, no execution.

Routing strategy:
1. Normalize: lowercase, strip punctuation except leading slash
2. Slash match: exact slash command → capability (confidence 0.95)
3. Trigger scoring: exact phrase > partial phrase > keyword overlap
4. Context boosts: evidence_needed, state_question, unsafe_automation
5. Threshold: confidence < 0.35 → selected_capability = null

Safety:
- Router does NOT execute capabilities
- Router does NOT search
- Router does NOT write to JSONL
- Router does NOT call LLM
- Router does NOT bypass governance
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .capability_registry import (
    load_registry,
    get_by_slash_command,
    search_by_trigger,
)

# Minimum confidence threshold for a valid routing decision
_ROUTING_THRESHOLD = 0.35

# Context boost keys that influence routing
_BOOST_CONTEXT_KEYS = (
    "evidence_needed",
    "state_question",
    "unsafe_automation",
)


def _normalize_message(message: str) -> str:
    """Normalize message for routing: lowercase, strip punctuation, preserve leading slash."""
    if not message:
        return ""
    
    # Check if message starts with a slash command
    is_slash = message.startswith("/")
    
    # Lowercase, strip trailing punctuation
    normalized = message.lower().strip()
    
    # Remove most punctuation except spaces — but preserve the slash for detection
    # We handle slash separately, so strip punctuation here
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    
    return ("/" + normalized) if is_slash else normalized


def _score_trigger_match(phrase: str, triggers: List[str]) -> tuple[float, List[str]]:
    """Score a phrase against trigger phrases, returning (confidence, matched_triggers).
    
    Scoring:
    - Exact phrase match: 0.9
    - All trigger words in phrase: 0.7
    - Partial overlap (≥50% words): 0.5
    - Any single word overlap: 0.3
    """
    if not phrase or not triggers:
        return 0.0, []
    
    phrase_words = set(phrase.split())
    matched = []
    
    for trigger in triggers:
        trigger_words = set(trigger.split())
        
        # Exact phrase match
        if phrase == trigger:
            matched.append(trigger)
            continue
        
        # All trigger words present in phrase
        if trigger_words and trigger_words.issubset(phrase_words):
            matched.append(trigger)
            continue
        
        # Partial overlap: at least half of trigger words
        if trigger_words:
            overlap = phrase_words & trigger_words
            if len(overlap) >= len(trigger_words) * 0.5 and len(overlap) >= 1:
                matched.append(trigger)
                continue
            
            # Single word overlap
            if len(overlap) >= 1:
                matched.append(trigger)
    
    if not matched:
        return 0.0, []
    
    # Calculate confidence based on best match type
    best_trigger = matched[0]
    best_words = set(best_trigger.split())
    
    if phrase == best_trigger:
        base_score = 0.9
    elif best_words and best_words.issubset(phrase_words):
        base_score = 0.7
    elif best_words and len(phrase_words & best_words) >= len(best_words) * 0.5:
        base_score = 0.5
    else:
        base_score = 0.3
    
    # Scale by how many triggers matched vs total
    coverage = len(matched) / len(triggers)
    
    confidence = base_score * (0.5 + 0.5 * coverage)
    confidence = min(confidence, 0.95)
    
    return round(confidence, 3), matched


def _apply_context_boosts(
    candidates: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Apply context-based boosts to candidate capabilities.
    
    Context keys:
    - evidence_needed: bool → boost evidence.search
    - state_question: bool → boost system.state
    - unsafe_automation: bool → boost governance.boundaries
    """
    if not context:
        return candidates
    
    boost_map = {
        "evidence_needed": "evidence.search",
        "state_question": "system.state",
        "unsafe_automation": "governance.boundaries",
    }
    
    for key, target_capability_id in boost_map.items():
        if context.get(key):
            for candidate in candidates:
                if candidate["capability"].get("capability_id") == target_capability_id:
                    candidate["confidence"] = min(candidate["confidence"] + 0.2, 0.98)
    
    return candidates


def route_request(
    user_message: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Route a user message to a capability using deterministic keyword matching.
    
    Args:
        user_message: The raw user message or query
        context: Optional routing context with evidence_needed, state_question, etc.
    
    Returns:
        Dict with:
            - record_type: "capability_route_v1"
            - selected_capability: capability_id or null
            - confidence: float 0.0-1.0
            - method: "slash" | "trigger" | "boost" | "fallback"
            - matched_triggers: list of matched trigger phrases
            - category: category of selected capability or null
            - authority: "routing_only"
            - automatic_change: false
            - operator_required: bool
    """
    context = context or {}
    normalized = _normalize_message(user_message)
    
    # ---- Step 1: Slash command exact match ----
    if normalized.startswith("/"):
        slash_candidate = get_by_slash_command(normalized)
        if slash_candidate:
            return {
                "record_type": "capability_route_v1",
                "selected_capability": slash_candidate["capability_id"],
                "confidence": 0.95,
                "method": "slash",
                "matched_triggers": [],
                "category": slash_candidate.get("category"),
                "authority": "routing_only",
                "automatic_change": False,
                "operator_required": slash_candidate.get("operator_required", False),
            }
    
    # ---- Step 2: Trigger scoring ----
    all_entries = load_registry()
    trigger_results = search_by_trigger(normalized, all_entries)
    
    candidates = []
    for result in trigger_results:
        entry = result["capability"]
        matched_triggers = result["matched_triggers"]
        triggers = entry.get("natural_triggers", [])
        
        confidence, _ = _score_trigger_match(normalized, triggers)
        
        if confidence >= 0.3:
            candidates.append({
                "capability": entry,
                "confidence": confidence,
                "matched_triggers": matched_triggers,
            })
    
    # ---- Step 3: Apply context boosts ----
    candidates = _apply_context_boosts(candidates, context)
    
    # ---- Step 4: Select best candidate above threshold ----
    if candidates:
        candidates.sort(key=lambda x: x["confidence"], reverse=True)
        best = candidates[0]
        
        if best["confidence"] >= _ROUTING_THRESHOLD:
            entry = best["capability"]
            return {
                "record_type": "capability_route_v1",
                "selected_capability": entry["capability_id"],
                "confidence": best["confidence"],
                "method": "boost" if context and any(context.get(k) for k in _BOOST_CONTEXT_KEYS) else "trigger",
                "matched_triggers": best["matched_triggers"],
                "category": entry.get("category"),
                "authority": "routing_only",
                "automatic_change": False,
                "operator_required": entry.get("operator_required", False),
            }
    
    # ---- Step 5: Fallback — no match above threshold ----
    return {
        "record_type": "capability_route_v1",
        "selected_capability": None,
        "confidence": 0.0,
        "method": "fallback",
        "matched_triggers": [],
        "category": None,
        "authority": "routing_only",
        "automatic_change": False,
        "operator_required": False,
    }
