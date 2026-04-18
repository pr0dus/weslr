#!/usr/bin/env python3
"""
influence.py - Weslr personality enrichment v1

Identity-aware reply helper with:
- Short, dry identity templates
- Optional brief humor
- Anti-repetition (simple recent-match skip)
- Seriousness suppression (safety/correction/repair contexts)

All data embedded in module - no file I/O, no dynamic imports.

No hidden global state reads - all inputs passed explicitly.

Note: Identity query detection is done in dialogue.py, not here.
This helper is called ONLY when identity questions are detected.
"""

from __future__ import annotations


# ============================================================================
# EMBEDDED STATIC DATA (no file I/O, no markdown parsing)
# ============================================================================

# Identity templates - short and dry (for identity-aware replies)
IDENTITY_TEMPLATES = [
    "Me, Weslr.",
    "Me, Weslr. Still here.",
    "Me, Weslr. I checked.",
    "Me, Weslr. Same thread, newer sentence.",
]

# Humor templates - brief and dry (for optional humor, context-gated)
HUMOR_TEMPLATES = [
    "I'm like a flashlight — I illuminate, but I also cast shadows.",
    "I'm in energy-saving mode. With high expectations.",
]

# Seriousness keywords for suppression
SERIOUSNESS_KEYWORDS = [
    "safety",
    "risk",
    "danger",
    "unsafe",
    "error",
    "failure",
    "crisis",
    "broken",
    "repair",
    "correction",
]


# ============================================================================
# MAIN PUBLIC FUNCTION
# ============================================================================

def get_identity_reply(
    lower_message: str,
    communicator_self: dict,
    communicator_state: dict,
    last_messages: list[str],
) -> str | None:
    """
    Return identity reply if applicable, None to use original behavior.
    
    All inputs are explicit - no hidden global state reads.
    
    Args:
        lower_message: Lowercase human message (already known to be identity query)
        communicator_self: Current communicator self state
        communicator_state: Current communicator state
        last_messages: Recent messages for anti-repetition check
    
    Returns:
        Short identity reply string if appropriate, None otherwise.
    """
    # Check seriousness context first - highest priority
    if _check_seriousness_context(communicator_state):
        # In serious context, return None for original behavior
        return None
    
    # Get humor capacity from communicator_self
    humor_threshold = float(
        communicator_self.get("identity_state", {})
        .get("style_profile", {})
        .get("humor", 0.0)
    )
    
    # Check if humor is allowed
    allow_humor = humor_threshold > 0.18
    
    # Build template list: identity always, humor optionally
    templates = IDENTITY_TEMPLATES[:]
    if allow_humor:
        templates = templates + HUMOR_TEMPLATES
    
    # Find a template that hasn't been used too recently
    for template in templates:
        if not _check_anti_repetition(last_messages, template):
            return template
    
    # All templates would repeat too recently - fall through to original behavior
    return None


# ============================================================================
# HELPER FUNCTIONS (internal, no hidden state reads)
# ============================================================================

def _check_seriousness_context(communicator_state: dict) -> bool:
    """Check if serious context detected using only passed communicator_state."""
    unresolved = str(communicator_state.get("unresolved_question", "")).lower()
    
    for kw in SERIOUSNESS_KEYWORDS:
        if kw in unresolved:
            return True
    
    # Also check for correction/repair in last decision
    last_decision = str(communicator_state.get("last_decision_summary", "")).lower()
    if "correction" in last_decision or "repair" in last_decision:
        return True
    
    return False


def _check_anti_repetition(last_messages: list[str], template: str) -> bool:
    """Check if template would repeat too recently using only passed last_messages."""
    if not last_messages:
        return False
    
    template_lower = template.lower().strip()
    
    # Count recent matches (exact lowercase match)
    matching_count = 0
    for msg in last_messages:
        msg_lower = str(msg).lower().strip()
        if msg_lower == template_lower:
            matching_count += 1
    
    # If same template used >=3 times, suppress it
    return matching_count >= 3
