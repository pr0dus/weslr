"""
WESLR Signal Pattern Observer V1

Read-only layer that groups observed signals into repeatable patterns
WITHOUT inferring values, classifying pressure categories, or modifying behavior.

This module operates inside the controlled observation environment only.
It is NOT part of the production system.

Purpose: Answer "do patterns exist?" — not "what do they mean?"
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field


# ----------------------------------------------------------------------
# Data Structures
# ----------------------------------------------------------------------

@dataclass
class RawSignal:
    """A raw signal observation from a single event."""

    signal_id: str
    signal_type: str  # S1, S2, S3, S4, S5, S6
    session_id: str
    timestamp: float
    topic_normalized: str | None = None
    frequency_count: int = 1
    session_diversity: int = 1
    growth_trend: str = "stable"
    first_seen: float | None = None
    last_seen: float | None = None
    confidence: float = 0.5
    extra: dict | None = None

    @classmethod
    def from_dict(cls, d: dict) -> RawSignal:
        return cls(
            signal_id=str(d.get("signal_id", "")),
            signal_type=str(d.get("signal_type", "")),
            session_id=str(d.get("session_id", "")),
            timestamp=float(d.get("timestamp", time.time())),
            topic_normalized=d.get("topic_normalized"),
            frequency_count=int(d.get("frequency_count", 1)),
            session_diversity=int(d.get("session_diversity", 1)),
            growth_trend=str(d.get("growth_trend", "stable")),
            first_seen=_try_float(d.get("first_seen")),
            last_seen=_try_float(d.get("last_seen")),
            confidence=float(d.get("confidence", 0.5)),
            extra=d.get("extra"),
        )


@dataclass
class PatternGroup:
    """A group of signals sharing the same type and normalized topic."""

    pattern_id: str
    signal_type: str
    topic_normalized: str | None
    frequency: int
    session_diversity: int
    time_span: float  # seconds between first and last occurrence
    consistency: float  # 0.0 to 1.0 — ratio of observed vs possible repetitions
    sessions: list[str] = field(default_factory=list)
    timestamps: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pattern_id": self.pattern_id,
            "signal_type": self.signal_type,
            "topic_normalized": self.topic_normalized,
            "frequency": self.frequency,
            "session_diversity": self.session_diversity,
            "time_span": round(self.time_span, 3),
            "consistency": round(self.consistency, 4),
        }


@dataclass
class PatternObservationResult:
    """Full output of the pattern observation layer."""

    patterns: list[PatternGroup]
    total_signals_observed: int
    observation_session_id: str
    observation_timestamp: float

    def to_dict(self) -> dict:
        return {
            "patterns": [p.to_dict() for p in self.patterns],
            "total_signals_observed": self.total_signals_observed,
            "observation_session_id": self.observation_session_id,
            "observation_timestamp": self.observation_timestamp,
        }


# ----------------------------------------------------------------------
# Pure Functions
# ----------------------------------------------------------------------

def _try_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _normalize_signal_type(signal_type: str) -> str:
    """Normalize signal type to canonical form (e.g. S1, S2)."""
    s = signal_type.strip().upper()
    if not s.startswith("S"):
        s = "S" + s
    return s


def _make_pattern_id(signal_type: str, topic: str | None) -> str:
    """Generate a deterministic pattern ID from signal type and topic."""
    key = f"{signal_type}::{topic or ''}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def group_signals(signals: list[RawSignal]) -> list[PatternGroup]:
    """
    Group signals by type and topic.
    Returns list of PatternGroup — one per unique (signal_type, topic_normalized) pair.
    """
    buckets: dict[str, list[RawSignal]] = {}

    for sig in signals:
        key = f"{_normalize_signal_type(sig.signal_type)}::{sig.topic_normalized or ''}"
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(sig)

    groups: list[PatternGroup] = []

    for key, bucket in buckets.items():
        signal_type = _normalize_signal_type(bucket[0].signal_type)
        topic = bucket[0].topic_normalized

        timestamps = sorted(sig.timestamp for sig in bucket)
        unique_sessions = list(dict.fromkeys(sig.session_id for sig in bucket))  # preserve order, dedupe

        frequency = len(bucket)
        session_diversity = len(unique_sessions)

        first_ts = timestamps[0]
        last_ts = timestamps[-1]
        time_span = last_ts - first_ts if len(timestamps) > 1 else 0.0

        # Consistency: actual observations / possible observations in time span
        # If all signals occur in a single session, consistency = 1.0 (perfect repetition)
        # If signals are spread over time with gaps, consistency decreases
        if time_span > 0 and session_diversity > 0:
            # Simple model: consistency = (frequency / session_diversity) / (1 + normalized_time_span)
            # Clamp to [0, 1]
            raw = (frequency / session_diversity) / (1 + (time_span / (86400 * 30)))  # normalized to ~30 days
            consistency = min(1.0, max(0.0, raw))
        else:
            consistency = 1.0 if frequency <= session_diversity else session_diversity / frequency

        pattern_id = _make_pattern_id(signal_type, topic)

        group = PatternGroup(
            pattern_id=pattern_id,
            signal_type=signal_type,
            topic_normalized=topic,
            frequency=frequency,
            session_diversity=session_diversity,
            time_span=time_span,
            consistency=round(consistency, 4),
            sessions=unique_sessions,
            timestamps=timestamps,
        )
        groups.append(group)

    return groups


def calculate_pattern_metrics(signals: list[RawSignal]) -> dict:
    """
    Calculate aggregate metrics across all signals.
    Returns raw numbers only — no classification, no ranking.
    """
    if not signals:
        return {
            "total_signals": 0,
            "by_type": {},
            "total_sessions": 0,
            "time_span": 0.0,
        }

    by_type: dict[str, int] = {}
    sessions: set[str] = set()
    timestamps: list[float] = []

    for sig in signals:
        st = _normalize_signal_type(sig.signal_type)
        by_type[st] = by_type.get(st, 0) + 1
        sessions.add(sig.session_id)
        timestamps.append(sig.timestamp)

    timestamps.sort()
    time_span = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0.0

    return {
        "total_signals": len(signals),
        "by_type": by_type,
        "total_sessions": len(sessions),
        "time_span": round(time_span, 3),
    }


def observe_patterns(
    signals: list[dict],
    session_id: str,
    timestamp: float | None = None,
) -> PatternObservationResult:
    """
    Main entry point. Accepts list of raw signal dicts, returns pattern observation result.

    This is a pure function — no side effects, no writes, no state carryover.

    WHAT IT ANSWERS: "Do patterns exist?"
    WHAT IT DOES NOT ANSWER: "What do they mean?" / "What pressure category?" / "What value?"
    """
    ts = timestamp if timestamp is not None else time.time()

    raw_signals: list[RawSignal] = []
    for s in signals:
        if isinstance(s, dict):
            raw_signals.append(RawSignal.from_dict(s))
        elif isinstance(s, RawSignal):
            raw_signals.append(s)

    groups = group_signals(raw_signals)
    total = len(raw_signals)

    return PatternObservationResult(
        patterns=groups,
        total_signals_observed=total,
        observation_session_id=session_id,
        observation_timestamp=ts,
    )


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    help_text = """WESLR Signal Pattern Observer V1

Usage:
  python signal_pattern_observer.py observe <signals_json>
  python signal_pattern_observer.py group <signals_json>
  python signal_pattern_observer.py metrics <signals_json>

Examples:
  echo '[{"signal_type":"S1","session_id":"s1","timestamp":1000}]' | python signal_pattern_observer.py observe -
"""

    def read_input(arg: str) -> list[dict]:
        if arg == "-":
            return json.load(sys.stdin)
        with open(arg) as f:
            return json.load(f)

    if len(sys.argv) < 2:
        print(help_text)
        sys.exit(0)

    cmd = sys.argv[1]
    if len(sys.argv) < 3:
        print("Error: requires <signals_json> argument")
        sys.exit(1)

    raw_input = sys.argv[2]
    signals = read_input(raw_input)

    if cmd == "observe":
        signals = signals if isinstance(signals, list) else [signals]
        result = observe_patterns(signals, session_id="cli", timestamp=None)
        print(json.dumps(result.to_dict(), indent=2))
    elif cmd == "group":
        signals = signals if isinstance(signals, list) else [signals]
        raw = [RawSignal.from_dict(s) for s in signals]
        groups = group_signals(raw)
        print(json.dumps([g.to_dict() for g in groups], indent=2))
    elif cmd == "metrics":
        signals = signals if isinstance(signals, list) else [signals]
        raw = [RawSignal.from_dict(s) for s in signals]
        m = calculate_pattern_metrics(raw)
        print(json.dumps(m, indent=2))
    else:
        print(f"Unknown command: {cmd}")
        print(help_text)
        sys.exit(1)