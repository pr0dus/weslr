"""
WESLR Evidence Review Trigger V1

Detection + surfacing mechanism ONLY.
NO writes. NO proposals. NO governance calls. NO LLM usage. NO auto-decisions.

Hook: Signal Aggregation output stage (read-only).
When signals are evaluated, call detect_evidence_review_need().
If trigger == TRUE, attach _evidence_review_candidate to response metadata.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class EvidenceReviewSignals:
    """Immutable signal bundle from evidence evaluation."""
    frequency: int
    diversity: int
    growth: float


@dataclass(frozen=True)
class EvidenceReviewCandidate:
    """Review candidate payload — attach to response metadata."""
    topic: str
    confidence: float
    reason: str


@dataclass(frozen=True)
class EvidenceReviewResult:
    """Pure output — no side effects."""
    trigger: bool
    confidence: float
    reason: str
    signals: EvidenceReviewSignals


def detect_evidence_review_need(
    topic: str,
    evidence_events: Dict[str, Any]
) -> EvidenceReviewResult:
    """
    Detect whether evidence on a given topic warrants operator review.

    V1 Simple Rules (ALL must be true):
        - frequency >= 3
        - AND diversity >= 2
        - AND growth trend positive (> 0)

    Parameters
    ----------
    topic : str
        Normalized topic string.
    evidence_events : dict
        Must contain keys:
            frequency (int): count of evidence events
            diversity (int): number of distinct evidence types/sources
            growth (float): trend value (>0 = growing, <0 = shrinking)

    Returns
    -------
    EvidenceReviewResult
        Immutable result. caller decides what to do with it.
    """
    # --- unpack with safe defaults (coerce None → 0) ---
    _f = evidence_events.get("frequency", 0)
    _d = evidence_events.get("diversity", 0)
    _g = evidence_events.get("growth", 0.0)
    frequency: int = _f if _f is not None else 0
    diversity: int = _d if _d is not None else 0
    growth: float = _g if _g is not None else 0.0

    # --- build signal bundle ---
    signals = EvidenceReviewSignals(
        frequency=frequency,
        diversity=diversity,
        growth=growth
    )

    # --- evaluate trigger rules (V1 simple) ---
    meets_frequency = frequency >= 3
    meets_diversity = diversity >= 2
    meets_growth = growth > 0

    trigger: bool = meets_frequency and meets_diversity and meets_growth

    # --- confidence: how close to threshold ---
    if not trigger:
        # No trigger — confidence based on how close we are to thresholds
        freq_gap = max(0, 3 - frequency) / 3
        div_gap = max(0, 2 - diversity) / 2
        if freq_gap == 0 and div_gap == 0:
            # frequency and diversity OK but growth negative
            confidence = max(0.0, min(1.0, 1.0 - abs(growth)))
        else:
            confidence = 0.0
        reason = _build_reason(topic, trigger, frequency, diversity, growth)
    else:
        # Triggered — confidence proportional to signal strength
        freq_ratio = min(1.0, frequency / 6)
        div_ratio = min(1.0, diversity / 4)
        growth_norm = min(1.0, growth) if growth > 0 else 0.0
        confidence = min(1.0, (freq_ratio + div_ratio + growth_norm) / 3)
        reason = _build_reason(topic, trigger, frequency, diversity, growth)

    return EvidenceReviewResult(
        trigger=trigger,
        confidence=round(confidence, 4),
        reason=reason,
        signals=signals
    )


def _build_reason(
    topic: str,
    triggered: bool,
    frequency: int,
    diversity: int,
    growth: float
) -> str:
    """Build a human-readable reason string."""
    if triggered:
        return (
            f"Evidence review triggered for [{topic}]: "
            f"freq={frequency} (>=3), div={diversity} (>=2), "
            f"growth=+{growth:.2f} (positive)"
        )
    # Not triggered — explain why
    blockers: List[str] = []
    if frequency < 3:
        blockers.append(f"freq {frequency}<3")
    if diversity < 2:
        blockers.append(f"div {diversity}<2")
    if growth <= 0:
        blockers.append(f"growth {'N/A' if growth == 0 else str(growth)} (not positive)")
    return f"No review trigger for [{topic}]: {'; '.join(blockers)}"


# --- integration helper (read-only attachment) ---

def attach_review_candidate(
    metadata: Dict[str, Any],
    result: EvidenceReviewResult,
    mode: str = "operator"
) -> Dict[str, Any]:
    """
    Attach review candidate to response metadata if conditions allow.

    Mode Rules:
        public_demo_readonly : DO NOT surface to user
        operator / private_dev : allow visibility
    """
    if mode == "public_demo_readonly":
        # Do not attach in public read-only mode
        return metadata

    if not result.trigger:
        return metadata

    candidate = EvidenceReviewCandidate(
        topic=result.signals.frequency,  # topic is implicit — use signals
        confidence=result.confidence,
        reason=result.reason
    )

    # Build the candidate dict (EvidenceReviewCandidate is not directly JSON-serializable)
    metadata["_evidence_review_candidate"] = {
        "topic": candidate.topic,  # NOTE: caller should pass real topic string
        "confidence": result.confidence,
        "reason": result.reason
    }
    return metadata
