"""
WESLR OmniChat Ephemeral Context V1

Provides in-memory, per-session continuity for short follow-up inputs
like "yes", "no", "ok", "do it" that relate to the immediately previous turn.

Rules:
- Stored in runtime only — never persisted to disk or JSONL
- Expires after one follow-up turn or any unrelated query
- Never leaks context to user
- Never overrides explicit user intent
- Never affects structured state
"""

from __future__ import annotations

from typing import Optional


# ─── Consent and refusal keywords ────────────────────────────────────────────

# User says YES — evidence exploration proceeds
CONSENT_KEYWORDS: frozenset = frozenset({
    "yes", "yeah", "yep", "yea",
    "ok", "okay", "sure", "do it",
    "go ahead", "please do", "lets do_it",
})

# User says NO — offer is cancelled, context cleared
REFUSAL_KEYWORDS: frozenset = frozenset({
    "no", "nope", "nah", "don't",
    "skip", "never mind", "nevermind",
    "cancel",
})


# ─── Offer types ──────────────────────────────────────────────────────────────

OFFER_TYPE_EVIDENCE: str = "evidence_offer"


# ─── Ephemeral context ────────────────────────────────────────────────────────

class EphemeralContext:
    """
    Lightweight in-memory record of the last turn's offer.
    Never persisted. Expires after one follow-up.
    """
    __slots__ = ("_intent_type", "_topic", "_offer_type", "_turn_id")

    def __init__(
        self,
        intent_type: str,
        topic: str,
        offer_type: str,
        turn_id: int = 0,
    ) -> None:
        self._intent_type = intent_type
        self._topic = topic
        self._offer_type = offer_type
        self._turn_id = turn_id

    @property
    def intent_type(self) -> str:
        return self._intent_type

    @property
    def topic(self) -> str:
        return self._topic

    @property
    def offer_type(self) -> str:
        return self._offer_type

    @property
    def turn_id(self) -> int:
        return self._turn_id

    def to_dict(self) -> dict:
        return {
            "intent_type": self._intent_type,
            "topic": self._topic,
            "offer_type": self._offer_type,
            "turn_id": self._turn_id,
        }


class EphemeralStore:
    """
    Per-session ephemeral context store.

    Thread-unsafe by design — WESLR is single-threaded per session.
    Replace with a thread-safe variant if WESLR adds concurrency.
    """

    def __init__(self) -> None:
        self._context: Optional[EphemeralContext] = None
        self._turn_counter: int = 0

    # ── Core API ──────────────────────────────────────────────────────────────

    def store_offer(
        self,
        intent_type: str,
        topic: str,
        offer_type: str,
    ) -> None:
        """
        Record that an offer was made in the current turn.

        Call this when WESLR presents an evidence offer to the user.
        The store holds it until the user's next turn.
        """
        self._turn_counter += 1
        self._context = EphemeralContext(
            intent_type=intent_type,
            topic=topic,
            offer_type=offer_type,
            turn_id=self._turn_counter,
        )

    def check_follow_up(self, user_input: str) -> Optional[dict]:
        """
        Check if user_input is a follow-up to a stored offer.

        Returns:
            - None if no active context or input is unrelated
            - {"action": "consent", "topic": <str>, "rewritten": <str>}
              if input is a consent keyword and offer was evidence_offer
            - {"action": "refusal"} if input is a refusal keyword
              (context is cleared)
            - {"action": "unrelated"} if input is neither consent nor refusal
              (context is cleared)
        """
        if self._context is None:
            return None

        normalized = user_input.strip().lower()

        # Consent — rewrite into evidence exploration request
        if normalized in CONSENT_KEYWORDS:
            result = {
                "action": "consent",
                "topic": self._context.topic,
                "rewritten": f"explore evidence for {self._context.topic}",
                "offer_type": self._context.offer_type,
            }
            # Consume context after use (one follow-up only)
            self._context = None
            return result

        # Refusal — clear context
        if normalized in REFUSAL_KEYWORDS:
            self._context = None
            return {"action": "refusal"}

        # Unrelated input — clear context, let routing handle normally
        self._context = None
        return {"action": "unrelated"}

    def has_active_offer(self) -> bool:
        """Return True if there is an unconsumed offer in the current turn."""
        return self._context is not None

    def get_active_offer(self) -> Optional[EphemeralContext]:
        """Return the active offer, or None."""
        return self._context

    def clear(self) -> None:
        """Clear all stored context. Call on session reset."""
        self._context = None
        self._turn_counter = 0

    # ── Convenience check ──────────────────────────────────────────────────────

    def is_consent(self, user_input: str) -> bool:
        """Return True if user_input is a consent keyword."""
        return user_input.strip().lower() in CONSENT_KEYWORDS

    def is_refusal(self, user_input: str) -> bool:
        """Return True if user_input is a refusal keyword."""
        return user_input.strip().lower() in REFUSAL_KEYWORDS


# ─── Module-level singleton ────────────────────────────────────────────────────

# One store per session. Replaced on session reset.
_store: EphemeralStore = EphemeralStore()


def get_store() -> EphemeralStore:
    """Return the current session's ephemeral store."""
    return _store


def reset_store() -> None:
    """Reset the ephemeral store. Call on session reset or mode switch."""
    _store.clear()
