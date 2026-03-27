"""Continuity prioritization layer for CircleForge.

Reduces stale continuity dominance by improving thread prioritization.

Key improvements:
- Time decay: stale threads lose priority over time
- Freshness weighting: recent exchanges boost priority
- Human salience: active relationships boost relevant threads
- Context relevance: preferred topics get temporary priority boost
"""

from __future__ import annotations

import time
from typing import Dict, List, Tuple, Any, Optional


def calculate_thread_priority(
    topic: str,
    thread: dict,
    now_ts: int,
    human_salience: float = 0.5,
    preferred_topic: str = "",
    max_staleness_seconds: int = 3600,  # 1 hour
) -> float:
    """Calculate priority score (0.0 - 10.0) for a thread.

    Returns a normalized score combining:
    - Recency (time decay)
    - Exchange frequency
    - Human salience
    - Topic relevance
    """
    base_score = 5.0  # Neutral starting point

    # Recency decay (exponential)
    last_exchange_at = int(thread.get("last_exchange_at", 0) or 0)
    if last_exchange_at > 0:
        age_seconds = now_ts - last_exchange_at
        # Halve score every hour, never go below 0.5
        decay = 2 ** (-age_seconds / max_staleness_seconds)
        recency_score = 5.0 * decay
    else:
        recency_score = 0.5  # Threads without exchanges get minimal score

    base_score += recency_score

    # Exchange frequency boost (diminishing returns)
    exchange_count = int(thread.get("exchange_count", 0) or 0)
    frequency_boost = min(2.0, exchange_count * 0.2)
    base_score += frequency_boost

    # Human salience boost
    base_score *= (0.8 + 0.2 * human_salience)

    # Preferred topic boost (temporary, for current context)
    if preferred_topic and str(topic).lower() == preferred_topic.lower():
        base_score *= 1.5

    # Status bonus (open threads slightly preferred)
    if str(thread.get("status", "open")).lower() == "open":
        base_score *= 1.1

    return min(max(base_score, 0.0), 10.0)


def prioritize_threads(
    threads: Dict[str, dict],
    now_ts: int,
    preferred_topic: str = "",
    human_salience: float = 0.5,
    max_threads: int = 6,
) -> List[Tuple[str, dict, float]]:
    """Sort threads by priority, return top N.

    Each result includes (topic, thread, score).
    """
    scored = []
    for topic, thread in threads.items():
        score = calculate_thread_priority(
            topic=topic,
            thread=thread,
            now_ts=now_ts,
            human_salience=human_salience,
            preferred_topic=preferred_topic,
        )
        scored.append((topic, thread, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[2], reverse=True)

    return scored[:max_threads]


def calculate_staleness_factor(
    last_exchange_at: int,
    now_ts: int,
    max_staleness_seconds: int = 3600,
) -> float:
    """Calculate how stale a thread is (0.0 = fresh, 1.0 = stale).

    Returns a normalized staleness factor where 0.0 is fresh and 1.0 is stale.
    """
    if last_exchange_at <= 0:
        return 1.0  # Never exchanged = stale

    age_seconds = now_ts - last_exchange_at
    if age_seconds <= 0:
        return 0.0  # Fresh

    # Linear decay: 0.0 at 0s, 1.0 at max_staleness_seconds
    staleness = age_seconds / max_staleness_seconds
    return min(1.0, staleness)


def should_prune_stale_thread(
    topic: str,
    thread: dict,
    now_ts: int,
    max_staleness_seconds: int = 86400,  # 24 hours
    min_exchanges: int = 2,
) -> bool:
    """Determine if a thread should be pruned due to staleness.

    Returns True if the thread should be pruned.
    """
    last_exchange_at = int(thread.get("last_exchange_at", 0) or 0)
    exchange_count = int(thread.get("exchange_count", 0) or 0)
    last_human_exchange_at = int(thread.get("last_human_exchange_at", 0) or 0)

    # Fresh threads are safe
    if now_ts - last_exchange_at < max_staleness_seconds // 4:
        return False

    # Threads with meaningful exchanges get more time
    if exchange_count >= min_exchanges:
        return now_ts - last_exchange_at > max_staleness_seconds * 2

    # Low-exchange threads get shorter grace period
    return now_ts - last_exchange_at > max_staleness_seconds


def filter_active_threads(
    threads: Dict[str, dict],
    now_ts: int,
    preferred_topic: str = "",
    min_priority: float = 2.0,
    human_salience: float = 0.5,
) -> List[Tuple[str, dict]]:
    """Return threads that meet minimum priority threshold.

    Filters out stale, low-priority threads.
    """
    prioritized = prioritize_threads(
        threads=threads,
        now_ts=now_ts,
        preferred_topic=preferred_topic,
        human_salience=human_salience,
    )

    return [(topic, thread) for topic, thread, score in prioritized if score >= min_priority]


def pick_relevant_active_thread_improved(
    relationships: dict,
    preferred_topic: str = "",
    now_ts: int | None = None,
) -> Tuple[str, dict] | None:
    """Improved thread picker with staleness awareness.

    Returns (topic, thread) or None.
    """
    now_ts = now_ts or int(time.time())
    threads = relationships.get("conversation_threads") or {}
    human_salience = float(relationships.get("human_salience", 0.5) or 0.5)

    prioritized = prioritize_threads(
        threads=threads,
        now_ts=now_ts,
        preferred_topic=preferred_topic,
        human_salience=human_salience,
        max_threads=12,
    )

    if not prioritized:
        return None

    # Return highest priority thread
    topic, thread, _ = prioritized[0]
    return (topic, thread)


def build_thread_health_report(
    threads: Dict[str, dict],
    now_ts: int,
    max_staleness_seconds: int = 86400,
) -> dict:
    """Build a report on thread health and staleness.

    Useful for meta_reflection and self-audit.
    """
    total = len(threads)
    stale = 0
    fresh = 0
    unresolved = 0
    resolved = 0

    for topic, thread in threads.items():
        staleness = calculate_staleness_factor(
            int(thread.get("last_exchange_at", 0) or 0),
            now_ts,
            max_staleness_seconds,
        )
        if staleness > 0.8:
            stale += 1
        else:
            fresh += 1

        if str(thread.get("status", "open")).lower() == "open":
            unresolved += 1
        else:
            resolved += 1

    return {
        "total_threads": total,
        "fresh_threads": fresh,
        "stale_threads": stale,
        "unresolved_threads": unresolved,
        "resolved_threads": resolved,
        "staleness_ratio": stale / total if total > 0 else 0.0,
        "resolution_ratio": resolved / total if total > 0 else 0.0,
        "timestamp": now_ts,
    }


def clear_stale_threads(
    relationships: dict,
    now_ts: int,
    max_staleness_seconds: int = 86400,
    min_exchanges: int = 2,
) -> dict:
    """Remove stale threads from relationships.

    Modifies and returns relationships.
    """
    threads = relationships.get("conversation_threads", {})
    unresolved = relationships.get("unresolved_shared_threads", [])

    to_remove = []
    for topic, thread in threads.items():
        if should_prune_stale_thread(
            topic=topic,
            thread=thread,
            now_ts=now_ts,
            max_staleness_seconds=max_staleness_seconds,
            min_exchanges=min_exchanges,
        ):
            to_remove.append(topic)

    for topic in to_remove:
        del threads[topic]
        if topic in unresolved:
            unresolved.remove(topic)

    relationships["conversation_threads"] = threads
    relationships["unresolved_shared_threads"] = unresolved[-12:]

    return relationships
