"""ARC-AGI-2 synthetic run log analyzer V1.

Reads events.jsonl produced by ArcRunEventLogV1 and produces
structured analysis: counts, summaries, leakage checks, consistency.
No public ARC data, no scoring, no submission.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from weslr.arc_run_event_log_v1 import FORBIDDEN_METADATA_KEYS_V1


def load_events(path: str | Path) -> list[dict[str, Any]]:
    """Load events from a JSONL file."""
    events: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def load_summary(path: str | Path) -> dict[str, Any]:
    """Load summary JSON file."""
    return json.loads(Path(path).read_text())


def count_by_level(events: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Count events by level."""
    return dict(Counter(e.get("level", "UNKNOWN") for e in events))


def count_by_phase(events: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Count events by phase."""
    return dict(Counter(e.get("phase", "UNKNOWN") for e in events))


def count_by_type(events: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Count events by event_type."""
    return dict(Counter(e.get("event_type", "UNKNOWN") for e in events))


def split_summaries(events: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Extract split summaries from split_summary events."""
    summaries: dict[str, dict[str, Any]] = {}
    for e in events:
        if e.get("event_type") == "split_summary":
            meta = e.get("metadata", {})
            split = str(meta.get("split_name", "unknown"))
            summaries[split] = dict(meta)
    return summaries


def count_solved_unsolved(events: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Count task_solved and task_unsolved events."""
    solved = sum(1 for e in events if e.get("event_type") == "task_solved")
    unsolved = sum(1 for e in events if e.get("event_type") == "task_unsolved")
    return {"solved": solved, "unsolved": unsolved}


def count_fallback(events: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Count fallback_used events."""
    fallback = sum(1 for e in events if e.get("event_type") == "fallback_used")
    return {"fallback_used": fallback}


def count_malformed(events: Sequence[Mapping[str, Any]]) -> int:
    """Count malformed_output events."""
    return sum(1 for e in events if e.get("event_type") == "malformed_output")


def count_exceptions(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """List exception events with metadata."""
    return [dict(e) for e in events if e.get("event_type") == "exception"]


def adversarial_summary(events: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Summarize adversarial rejection events."""
    adv_pass = sum(1 for e in events if e.get("event_type") == "adversarial_rejection" and e.get("metadata", {}).get("rejected") is True)
    adv_fail = sum(1 for e in events if e.get("event_type") == "adversarial_rejection" and e.get("metadata", {}).get("rejected") is False)
    return {"adversarial_rejection_pass": adv_pass, "adversarial_rejection_fail": adv_fail}


def top_fallback_families(events: Sequence[Mapping[str, Any]], top_n: int = 5) -> list[tuple[str, int]]:
    """Find top fallback families from fallback_used events."""
    families: Counter[str] = Counter()
    for e in events:
        if e.get("event_type") == "fallback_used":
            meta = e.get("metadata", {})
            family = str(meta.get("family_label", "unknown"))
            families[family] += 1
    return families.most_common(top_n)


def top_failure_categories(events: Sequence[Mapping[str, Any]], top_n: int = 5) -> list[tuple[str, int]]:
    """Find top failure categories from task_unsolved events."""
    categories: Counter[str] = Counter()
    for e in events:
        if e.get("event_type") == "task_unsolved":
            meta = e.get("metadata", {})
            cat = str(meta.get("failure_category", "unknown"))
            categories[cat] += 1
    return categories.most_common(top_n)


def check_missing_events(events: Sequence[Mapping[str, Any]]) -> list[str]:
    """Check for missing required events."""
    issues: list[str] = []
    event_types = {e.get("event_type") for e in events}
    if "run_started" not in event_types:
        issues.append("Missing run_started event")
    if "run_finished" not in event_types:
        issues.append("Missing run_finished event")
    if "run_summary" not in event_types:
        issues.append("Missing run_summary event")
    return issues


def check_task_count_mismatch(events: Sequence[Mapping[str, Any]], expected_count: int | None = None) -> list[str]:
    """Check for task count mismatch between task_started and task_solved+task_unsolved."""
    issues: list[str] = []
    started = sum(1 for e in events if e.get("event_type") == "task_started")
    solved = sum(1 for e in events if e.get("event_type") == "task_solved")
    unsolved = sum(1 for e in events if e.get("event_type") == "task_unsolved")
    if started != solved + unsolved:
        issues.append(f"Task count mismatch: started={started}, solved+unsolved={solved + unsolved}")
    if expected_count is not None and started != expected_count:
        issues.append(f"Expected {expected_count} tasks, got {started}")
    return issues


def check_exception_task_ids(events: Sequence[Mapping[str, Any]]) -> list[str]:
    """Check that exception events have task_id in metadata."""
    issues: list[str] = []
    for e in events:
        if e.get("event_type") == "exception":
            meta = e.get("metadata", {})
            if "task_id" not in meta:
                issues.append(f"Exception event missing task_id: {e.get('message', '')}")
    return issues


def check_unsafe_metadata(events: Sequence[Mapping[str, Any]]) -> list[str]:
    """Check for forbidden metadata keys in any event."""
    issues: list[str] = []
    for e in events:
        meta = e.get("metadata", {})
        for key in meta:
            if key in FORBIDDEN_METADATA_KEYS_V1:
                issues.append(
                    f"Forbidden metadata key '{key}' in event {e.get('event_type')} "
                    f"(phase={e.get('phase')}, message={e.get('message', '')})"
                )
    return issues


def check_expected_output_leakage(events: Sequence[Mapping[str, Any]]) -> list[str]:
    """Check for expected_output leakage in solver_execution phase events."""
    issues: list[str] = []
    for e in events:
        if e.get("phase") == "solver_execution":
            meta = e.get("metadata", {})
            for key in meta:
                if "expected_output" in key.lower():
                    issues.append(
                        f"Expected output leakage in solver_execution phase: key='{key}' "
                        f"in event {e.get('event_type')}"
                    )
    return issues


def check_raw_grid_leakage(events: Sequence[Mapping[str, Any]]) -> list[str]:
    """Check for raw grid leakage in any metadata."""
    issues: list[str] = []
    grid_keywords = ["grid", "grids", "train", "test_input", "output"]
    for e in events:
        meta = e.get("metadata", {})
        for key in meta:
            key_lower = key.lower()
            if any(kw in key_lower for kw in grid_keywords):
                value = meta[key]
                if isinstance(value, list) and value and isinstance(value[0], list):
                    issues.append(
                        f"Raw grid leakage in event {e.get('event_type')}: key='{key}' "
                        f"contains list-of-list grid data"
                    )
    return issues


def check_summary_consistency(
    events: Sequence[Mapping[str, Any]],
    summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Check consistency between events and summary JSON."""
    issues: list[str] = []
    if summary is None:
        return issues
    summary_data = summary.get("summary", {})
    if not summary_data:
        return issues
    # Check event count
    summary_event_count = summary.get("event_count", 0)
    actual_event_count = len(events)
    if summary_event_count != actual_event_count:
        issues.append(f"Summary event_count={summary_event_count} != actual events={actual_event_count}")
    return issues


def analyze_events(events: Sequence[Mapping[str, Any]], summary: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Full analysis of events."""
    return {
        "event_count": len(events),
        "by_level": count_by_level(events),
        "by_phase": count_by_phase(events),
        "by_type": count_by_type(events),
        "split_summaries": split_summaries(events),
        "solved_unsolved": count_solved_unsolved(events),
        "fallback": count_fallback(events),
        "malformed_count": count_malformed(events),
        "exception_count": len(count_exceptions(events)),
        "exceptions": count_exceptions(events),
        "adversarial": adversarial_summary(events),
        "top_fallback_families": top_fallback_families(events),
        "top_failure_categories": top_failure_categories(events),
        "missing_events": check_missing_events(events),
        "task_count_mismatch": check_task_count_mismatch(events),
        "exception_task_ids": check_exception_task_ids(events),
        "unsafe_metadata": check_unsafe_metadata(events),
        "expected_output_leakage": check_expected_output_leakage(events),
        "raw_grid_leakage": check_raw_grid_leakage(events),
        "summary_consistency": check_summary_consistency(events, summary),
        "leakage_audit_pass": (
            len(check_unsafe_metadata(events)) == 0
            and len(check_expected_output_leakage(events)) == 0
            and len(check_raw_grid_leakage(events)) == 0
        ),
    }


__all__ = [
    "load_events",
    "load_summary",
    "count_by_level",
    "count_by_phase",
    "count_by_type",
    "split_summaries",
    "count_solved_unsolved",
    "count_fallback",
    "count_malformed",
    "count_exceptions",
    "adversarial_summary",
    "top_fallback_families",
    "top_failure_categories",
    "check_missing_events",
    "check_task_count_mismatch",
    "check_exception_task_ids",
    "check_unsafe_metadata",
    "check_expected_output_leakage",
    "check_raw_grid_leakage",
    "check_summary_consistency",
    "analyze_events",
]