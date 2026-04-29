"""
WESLR Context Decay Policy V1 — Non-destructive relevance aging

Pure classification only. NO deletion. NO writes. NO LLM. NO auto-forgetting.

classify_context_decay(last_seen_days, access_count, source_type, mode)
-> ContextDecayResult
"""

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_AGE_FRESH = 7
_AGE_AGING = 30
_AGE_STALE = 90

_ACCESS_THRESHOLD = 5


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ContextDecayResult:
    """Immutable decay classification. destructive_action_allowed is ALWAYS False."""
    status: str                    # "fresh" | "aging" | "stale" | "archival"
    decay_score: float            # 0.0 (fresh) → 1.0 (archival)
    reason: str
    recommended_action: str       # "keep" | "deprioritize" | "archive_candidate"
    destructive_action_allowed: bool  # ALWAYS False


# ---------------------------------------------------------------------------
# Core classifier
# ---------------------------------------------------------------------------
def classify_context_decay(
    last_seen_days: int,
    access_count: int,
    source_type: str,
    mode: str = "private_dev"
) -> ContextDecayResult:
    """
    Classify context freshness and relevance age.

    Parameters
    ----------
    last_seen_days : int
        Days since last access.
    access_count : int
        Number of times the context has been accessed.
    source_type : str
        One of: "governance" | "proposal" | "evidence" | "signal" | "memory" | "other"
    mode : str
        "public_demo_readonly" → no archive_candidate recommendations
        anything else         → full classification

    Returns
    -------
    ContextDecayResult
        Immutable. destructive_action_allowed is always False.
    """
    # --- normalize None / negative ---
    days = _int(last_seen_days)
    days = max(0, days)
    access = max(0, _int(access_count))

    # --- access count adjusts effective age ---
    effective_days = _effective_age(days, access)

    # --- classify age bucket ---
    status = _age_status(effective_days)

    # --- decay score: linear 0.0 → 1.0 over 0 → 90+ days ---
    decay_score = min(1.0, effective_days / _AGE_STALE)

    # --- source type constraints ---
    protected = source_type in ("governance", "proposal")
    evidence_like = source_type in ("evidence", "signal")

    # --- build reason ---
    reason = _build_reason(status, effective_days, access, source_type)

    # --- recommended action ---
    action, destructive = _recommend_action(
        status, source_type, protected, evidence_like, mode
    )

    return ContextDecayResult(
        status=status,
        decay_score=round(decay_score, 4),
        reason=reason,
        recommended_action=action,
        destructive_action_allowed=False   # ALWAYS False — core invariant
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _int(val) -> int:
    if val is None:
        return 0
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _effective_age(days: int, access: int) -> int:
    """
    Access count >= 5 reduces effective age.
    No floor constraints — reduction shifts bucket naturally.
    """
    if access >= _ACCESS_THRESHOLD:
        if days > _AGE_STALE:
            return days - 120     # archival → large reduction; may still be archival
        elif days > _AGE_AGING:
            return days - 30       # stale → aging boundary
        elif days > _AGE_FRESH:
            return days - 50       # aging → fresh boundary
        else:
            return days - 7      # fresh → stays fresh
    return days


def _age_status(days: int) -> str:
    if days <= _AGE_FRESH:
        return "fresh"
    elif days <= _AGE_AGING:
        return "aging"
    elif days <= _AGE_STALE:
        return "stale"
    else:
        return "archival"


def _build_reason(status: str, effective_days: int, access: int, source_type: str) -> str:
    access_note = f" access={access}(>={_ACCESS_THRESHOLD}→age reduced)" if access >= _ACCESS_THRESHOLD else f" access={access}"
    return (
        f"[{status.upper()}] age={effective_days} days"
        f"({effective_days}→{status}){access_note}"
        f" source={source_type}"
    )


def _recommend_action(
    status: str,
    source_type: str,
    protected: bool,
    evidence_like: bool,
    mode: str
) -> tuple[str, bool]:
    """
    Returns (recommended_action, destructive_action_allowed).
    destructive_action_allowed is ALWAYS False.
    """
    # Governance and proposal are never destroyed
    if protected:
        if status == "archival":
            action = "deprioritize"
        else:
            action = "keep"
        return action, False

    # In public mode, never recommend archive
    if mode == "public_demo_readonly":
        if status in ("stale", "archival"):
            return "deprioritize", False
        return "keep", False

    # private_dev / operator mode
    if status == "archival" and evidence_like:
        return "archive_candidate", False
    elif status == "archival":
        return "archive_candidate", False
    elif status == "stale":
        return "deprioritize", False
    elif status == "aging":
        return "deprioritize", False
    return "keep", False
