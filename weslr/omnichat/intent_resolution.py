"""
WESLR OmniChat Intent Resolution V1

Deterministic scored intent model for short follow-up inputs.
No LLM. Pure rule-based scoring.

Scores four intent axes:
- affirm: user agrees or wants to proceed
- decline: user refuses or cancels
- redirect: user redirects to a different topic
- unclear: intent cannot be determined

Thresholds:
  affirm  → resolved when affirm_score >= 0.7 AND decline_score < 0.3
  decline → resolved when decline_score >= 0.7
  redirect → resolved when redirect_score >= 0.6
  unclear → everything else
"""

from __future__ import annotations

from typing import NamedTuple


# ─── Constants ────────────────────────────────────────────────────────────────

# Thresholds
AFFIRM_THRESHOLD = 0.7
DECLINE_THRESHOLD = 0.7
REDIRECT_THRESHOLD = 0.6
DECLINE_CANCELLATION = 0.3  # decline must be below this to affirm


# ─── Intent result ───────────────────────────────────────────────────────────

class IntentResult(NamedTuple):
    affirm_score: float
    decline_score: float
    redirect_score: float
    unclear_score: float
    strength_modifier: float
    confidence: float
    resolved_intent: str

    def is_affirm(self) -> bool:
        return self.resolved_intent == "affirm"

    def is_decline(self) -> bool:
        return self.resolved_intent == "decline"

    def is_redirect(self) -> bool:
        return self.resolved_intent == "redirect"

    def is_unclear(self) -> bool:
        return self.resolved_intent == "unclear"

    def is_clear(self) -> bool:
        """Return True if intent is affirm, decline, or redirect (not unclear)."""
        return self.resolved_intent != "unclear"


# ─── Keyword scoring ──────────────────────────────────────────────────────────

# Each entry: (keyword, base_score, strength_modifier)
# Keywords are matched with word boundary (\b) on the normalised input.

_AFFIRM_KEYWORDS = [
    # Core yes
    ("yes",       1.0,  0.0),
    ("yeah",      0.95, 0.0),
    ("yep",       0.95, 0.0),
    ("yea",       0.9,  0.0),
    ("sure",      0.9,  0.1),
    # OK variants
    ("ok",        0.85, 0.0),
    ("okay",      0.85, 0.0),
    ("alright",   0.8,  0.0),
    # Action confirmations
    ("do it",     0.95, 0.2),
    ("go ahead",  0.95, 0.2),
    ("please do", 0.9,  0.2),
    ("lets do it", 0.9, 0.1),
    ("let's do it", 0.9, 0.1),
    ("absolutely", 0.95, 0.1),
    ("definitely", 0.95, 0.1),
    ("count me in", 0.85, 0.1),
]

_DECLINE_KEYWORDS = [
    # Core no
    ("no",        1.0,  0.0),
    ("nope",      0.95, 0.0),
    ("nah",       0.9,  0.0),
    # Negative
    ("don't",     0.8,  0.0),
    ("dont",      0.8,  0.0),
    ("not really", 0.75, -0.1),
    ("skip",      0.7,  0.0),
    ("cancel",    0.7,  0.0),
    # "never" contexts
    ("never mind",  0.7, -0.1),
    ("nevermind",   0.7, -0.1),
    ("forget it",   0.7, -0.1),
]

_REDIRECT_KEYWORDS = [
    # Redirect phrases
    ("actually ",  0.8,  0.0),   # "actually tell me about X"
    ("instead",    0.9,  0.0),
    ("actually",   0.7,  0.0),
    ("tell me about",  0.85, 0.0),
    ("can you tell me", 0.8, 0.0),
    ("wait",       0.6,  0.0),
    ("hold on",    0.6,  0.0),
    ("before that", 0.5, 0.0),
    ("actually can you", 0.75, 0.0),
    ("actually i want", 0.75, 0.0),
    ("actually i need", 0.75, 0.0),
]

_UNCLEAR_KEYWORDS = [
    ("maybe",     0.6,  0.0),
    ("i'm not sure", 0.5, 0.0),
    ("not sure",    0.6,  0.0),
    ("idk",         0.7,  0.0),
    ("i dont know", 0.6,  0.0),
    ("i don't know", 0.6, 0.0),
    ("perhaps",   0.5,  0.0),
    ("possibly",  0.5,  0.0),
    ("whatever",  0.3,  0.0),
]


# ─── Scoring engine ────────────────────────────────────────────────────────────

def score_input(user_input: str) -> IntentResult:
    """
    Score a user input on four intent axes and return an IntentResult.

    Pure deterministic rule-based scoring. No LLM.
    """
    normalized = _normalise(user_input)

    # Calculate raw scores
    aff = _score_category(normalized, _AFFIRM_KEYWORDS)
    dec = _score_category(normalized, _DECLINE_KEYWORDS)
    red = _score_category(normalized, _REDIRECT_KEYWORDS)
    unc = _score_category(normalized, _UNCLEAR_KEYWORDS)

    # Sum modifiers from all matched keywords
    modifier = (
        _sum_modifiers(normalized, _AFFIRM_KEYWORDS)
        + _sum_modifiers(normalized, _DECLINE_KEYWORDS)
        + _sum_modifiers(normalized, _REDIRECT_KEYWORDS)
        + _sum_modifiers(normalized, _UNCLEAR_KEYWORDS)
    )
    modifier = max(-1.0, min(1.0, modifier))

    # Confidence: how strongly did the best category score?
    top_score = max(aff, dec, red, unc)
    confidence = top_score

    # Resolve intent using thresholds
    resolved = _resolve(aff, dec, red, unc)

    return IntentResult(
        affirm_score=round(aff, 3),
        decline_score=round(dec, 3),
        redirect_score=round(red, 3),
        unclear_score=round(unc, 3),
        strength_modifier=round(modifier, 3),
        confidence=round(confidence, 3),
        resolved_intent=resolved,
    )


def _normalise(text: str) -> str:
    """Normalise input: lowercase, strip punctuation, trim whitespace."""
    import re
    text = text.strip().lower()
    # Remove trailing punctuation (but keep internal punctuation)
    text = re.sub(r'[.!?]+$', '', text)
    return text


def _score_category(normalized: str, keywords: list) -> float:
    """Return the highest matching score for a category, or 0.0."""
    best = 0.0
    for keyword, score, _ in keywords:
        # Use word-boundary aware matching
        # Phrases containing a trailing space are multi-word and matched as-is
        if ' ' in keyword:
            if keyword in normalized:
                best = max(best, score)
        else:
            import re
            if re.search(r'\b' + re.escape(keyword) + r'\b', normalized):
                best = max(best, score)
    return best


def _sum_modifiers(normalized: str, keywords: list) -> float:
    """Sum modifiers for all matched keywords."""
    total = 0.0
    for keyword, _, modifier in keywords:
        if ' ' in keyword:
            if keyword in normalized:
                total += modifier
        else:
            import re
            if re.search(r'\b' + re.escape(keyword) + r'\b', normalized):
                total += modifier
    return total


def _resolve(aff: float, dec: float, red: float, unc: float) -> str:
    """
    Apply threshold rules to resolve intent.

    Priority: decline > redirect > affirm > unclear
    """
    if dec >= DECLINE_THRESHOLD:
        return "decline"
    if aff >= AFFIRM_THRESHOLD and dec < DECLINE_CANCELLATION:
        return "affirm"
    if red >= REDIRECT_THRESHOLD:
        return "redirect"
    return "unclear"


# ─── Convenience resolver ─────────────────────────────────────────────────────

def resolve_intent(user_input: str) -> IntentResult:
    """
    Main entry point. Returns an IntentResult with resolved intent.

    Example:
        result = resolve_intent("yes please")
        if result.is_affirm():
            print("User wants to proceed")
    """
    return score_input(user_input)
