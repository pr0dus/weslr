"""
Weslr Relevance Surface — v1

Read-only advisory surface for ranking tracked interests against a context.
Does not modify any state. Does not influence routing. Advisory metadata only.

Scoring:
- +2 per shared tag (query tags vs interest tags)
- +1 if normalized name in query text
- +1 if display_name phrase in query text
- +1 if any interest tag appears in query text
- +2 recency bonus if last_seen within 48h
- +1 recency bonus if last_seen within 7 days
- +min(occurrence_count/10, 2) occurrence bonus

Only returns interests with score > 0, capped at top_n.
"""

from __future__ import annotations

import time
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Support running as standalone script (weslr/relevance_surface.py)
if __name__ == "__main__" and __package__ in (None, ""):
    # Running as script — set up import path
    _ws_dir = Path(__file__).resolve().parent.parent
    if str(_ws_dir) not in sys.path:
        sys.path.insert(0, str(_ws_dir))
    from weslr.interest_tracker import list_interests
else:
    from .interest_tracker import list_interests


# ── Scoring constants ───────────────────────────────────────────────────────────

RECENCY_48H_BONUS = 2
RECENCY_7D_BONUS = 1
TAG_MATCH_BONUS = 2
NAME_IN_TEXT_BONUS = 1
DISPLAY_NAME_IN_TEXT_BONUS = 1
TAG_IN_TEXT_BONUS = 1
MAX_OCCURRENCE_BONUS = 2


# ── Scoring helpers ───────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Return lowercase-stripped text for matching."""
    return text.lower().strip()


def _is_within_days(timestamp: str, days: int) -> bool:
    """Return True if ISO timestamp is within `days` of now."""
    try:
        ts = time.mktime(time.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ"))
        now = time.time()
        return (now - ts) <= (days * 86400)
    except (ValueError, OSError):
        return False


def _score_interest(
    interest: Dict[str, Any],
    text: Optional[str],
    query_tags: Optional[List[str]],
) -> Tuple[int, List[str]]:
    """
    Score a single interest against query context.
    Returns (score, match_reasons_list).

    Scoring law v2: Recency may amplify relevance. Recency must not create
    relevance by itself. If no non-recency signal exists, score is 0.
    """
    score = 0
    reasons: List[str] = []
    has_signal = False  # True if at least one non-recency signal found

    # Tag overlap: query tags vs interest tags
    if query_tags:
        interest_tags = set(t.lower().strip() for t in interest.get("tags", []))
        query_tag_set = set(t.lower().strip() for t in query_tags if t.strip())
        shared = interest_tags & query_tag_set
        if shared:
            has_signal = True
            tag_bonus = len(shared) * TAG_MATCH_BONUS
            score += tag_bonus
            for tag in sorted(shared):
                reasons.append(f"matched tag: {tag}")

    # Text matching
    if text:
        text_lower = _normalize(text)
        normalized_name = interest.get("name", "")
        display_name = interest.get("display_name", "")

        if normalized_name and normalized_name in text_lower:
            has_signal = True
            score += NAME_IN_TEXT_BONUS
            reasons.append(f"query text matched name: {normalized_name}")

        if display_name and _normalize(display_name) in text_lower:
            has_signal = True
            score += DISPLAY_NAME_IN_TEXT_BONUS
            reasons.append(f"query text matched display_name")

        interest_tags = interest.get("tags", [])
        for tag in interest_tags:
            if tag in text_lower:
                has_signal = True
                score += TAG_IN_TEXT_BONUS
                reasons.append(f"query text contains tag: {tag}")
                break  # only +1 once per interest for tag-in-text

    # Recency bonuses — may amplify, never create
    last_seen = interest.get("last_seen_at", "")
    if last_seen:
        if _is_within_days(last_seen, 2):
            score += RECENCY_48H_BONUS
            reasons.append("recent activity within 48 hours")
        elif _is_within_days(last_seen, 7):
            score += RECENCY_7D_BONUS
            reasons.append("recent activity within 7 days")

    # Occurrence count bonus — may amplify, never create
    occ_count = interest.get("occurrence_count", 0)
    if occ_count > 0:
        occ_bonus = min(occ_count / 10, MAX_OCCURRENCE_BONUS)
        score += occ_bonus
        reasons.append(f"occurrence_count bonus: {occ_bonus:.1f}")

    # Eligibility gate: recency and count cannot create relevance by themselves
    if not has_signal:
        return 0, ["no eligible signal — recency/count alone cannot create relevance"]

    return score, reasons


# ── Public surface ─────────────────────────────────────────────────────────────

def query_relevant_interests(
    text: Optional[str] = None,
    tags: Optional[List[str]] = None,
    top_n: int = 3,
    status: str = "active",
) -> List[Dict[str, Any]]:
    """
    Query tracked interests for relevance to a given context.

    Args:
        text:       Free text to match against name, display_name, and tags.
                    Can be a question, artifact description, or topic phrase.
        tags:       Optional list of query-specific tags for tag overlap scoring.
        top_n:      Maximum number of results to return. Default 3.
                    Results sorted by descending score. Default 3.
        status:     Only consider interests with this status. Default "active".

    Returns:
        List of scored interest dicts. Each dict contains:
        - id, name, display_name, score, match_reasons,
          last_seen_at, occurrence_count, tags

    Notes:
        - This function is read-only. It does not modify any state.
        - It does not read artifact or question registries directly.
        - It never returns interests with score of 0.
        - Scores are deterministic and inspectable.
    """
    if top_n < 1:
        top_n = 1
    if top_n > 20:
        top_n = 20  # cap against absurd values

    interests = list_interests(status=status)
    results: List[Dict[str, Any]] = []

    for interest in interests:
        score, reasons = _score_interest(interest, text, tags)
        if score > 0:
            results.append({
                "id": interest["id"],
                "name": interest["name"],
                "display_name": interest["display_name"],
                "score": score,
                "match_reasons": reasons,
                "last_seen_at": interest.get("last_seen_at", ""),
                "occurrence_count": interest.get("occurrence_count", 0),
                "tags": interest.get("tags", []),
            })

    # Sort by descending score, then by last_seen_at (newer first) as tiebreaker
    results.sort(key=lambda r: (-r["score"], r["last_seen_at"]))

    return results[:top_n]


# ── CLI interface ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Query relevance of tracked interests")
    parser.add_argument("--text", default=None, help="Free text to match")
    parser.add_argument("--tags", default=None, help="Comma-separated tags")
    parser.add_argument("--top-n", type=int, default=3, help="Max results (default 3)")
    args = parser.parse_args()

    tags = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    results = query_relevant_interests(text=args.text, tags=tags, top_n=args.top_n)

    if not results:
        print("No relevant interests found.")
    else:
        for r in results:
            print(f"[{r['id']}] {r['display_name']} — score {r['score']}")
            for reason in r["match_reasons"]:
                print(f"  • {reason}")
            print(f"  tags: {', '.join(r['tags']) or '(none)'} | "
                  f"occurrences: {r['occurrence_count']} | "
                  f"last_seen: {r['last_seen_at']}")
            print()