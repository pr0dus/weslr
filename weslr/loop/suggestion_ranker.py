"""
WESLR Suggestion Ranker

Ranks candidate suggestions by confidence, domain relevance, and evidence quality.
Used by the Research Work Loop to order suggestions before writing to pending store.

V1: Rule-based. No ML. No external calls.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoredSuggestion:
    """A suggestion with its score and ranking metadata."""
    text: str
    confidence: float
    domain_relevance: float
    evidence_count: int
    mission_id: str
    source: str
    provenance: str
    combined_score: float


class SuggestionRanker:
    """
    Ranks suggestions by weighted combination of confidence, relevance, and evidence.

    V1 scoring:
        combined_score = (0.5 * confidence) + (0.3 * domain_relevance) + (0.2 * evidence_bonus)

    where evidence_bonus = min(evidence_count / 3, 1.0)
    """

    DEFAULT_CONFIDENCE = 0.5
    DEFAULT_RELEVANCE = 0.5
    DEFAULT_EVIDENCE_COUNT = 0

    def __init__(
        self,
        confidence_weight: float = 0.5,
        relevance_weight: float = 0.3,
        evidence_weight: float = 0.2,
    ):
        self.confidence_weight = confidence_weight
        self.relevance_weight = relevance_weight
        self.evidence_weight = evidence_weight

    def score(
        self,
        confidence: float,
        domain_relevance: float,
        evidence_count: int,
    ) -> float:
        """
        Calculate combined score.

        Args:
            confidence: 0.0–1.0, how confident the suggestion is
            domain_relevance: 0.0–1.0, how relevant to mission domain
            evidence_count: Number of evidence links supporting the suggestion

        Returns:
            Combined score 0.0–1.0
        """
        confidence = max(0.0, min(1.0, confidence))
        domain_relevance = max(0.0, min(1.0, domain_relevance))
        evidence_bonus = min(evidence_count / 3.0, 1.0)

        return (
            self.confidence_weight * confidence
            + self.relevance_weight * domain_relevance
            + self.evidence_weight * evidence_bonus
        )

    def rank(
        self,
        candidates: list[dict],
        domain_tags: Optional[list[str]] = None,
    ) -> list[ScoredSuggestion]:
        """
        Rank a list of candidate suggestions.

        Args:
            candidates: List of dicts with keys: text, confidence, domain_relevance,
                       evidence_count, mission_id, source, provenance
            domain_tags: Optional domain tags for relevance calculation

        Returns:
            List of ScoredSuggestion objects, sorted by combined_score descending
        """
        scored = []

        for c in candidates:
            confidence = c.get("confidence", self.DEFAULT_CONFIDENCE)
            relevance = c.get("domain_relevance", self.DEFAULT_RELEVANCE)
            evidence_count = c.get("evidence_count", self.DEFAULT_EVIDENCE_COUNT)

            combined = self.score(confidence, relevance, evidence_count)

            scored.append(ScoredSuggestion(
                text=c["text"],
                confidence=confidence,
                domain_relevance=relevance,
                evidence_count=evidence_count,
                mission_id=c["mission_id"],
                source=c["source"],
                provenance=c["provenance"],
                combined_score=combined,
            ))

        scored.sort(key=lambda x: x.combined_score, reverse=True)
        return scored

    def top(
        self,
        candidates: list[dict],
        n: int = 5,
        domain_tags: Optional[list[str]] = None,
    ) -> list[ScoredSuggestion]:
        """
        Return top N ranked suggestions.

        Args:
            candidates: List of candidate dicts
            n: Number of top suggestions to return
            domain_tags: Optional domain tags

        Returns:
            Top N ScoredSuggestion objects
        """
        return self.rank(candidates, domain_tags)[:n]


# Default global ranker instance
_default_ranker: Optional[SuggestionRanker] = None


def get_ranker() -> SuggestionRanker:
    """Get the default ranker instance."""
    global _default_ranker
    if _default_ranker is None:
        _default_ranker = SuggestionRanker()
    return _default_ranker


def rank_suggestions(
    candidates: list[dict],
    n: int = 5,
    domain_tags: Optional[list[str]] = None,
) -> list[ScoredSuggestion]:
    """
    Convenience function — rank and return top N suggestions.

    Args:
        candidates: List of candidate dicts
        n: Number to return
        domain_tags: Optional domain tags

    Returns:
        Top N ScoredSuggestion objects
    """
    return get_ranker().top(candidates, n=n, domain_tags=domain_tags)