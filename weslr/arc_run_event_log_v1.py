"""ARC-AGI-2 run event log V1.

Structured JSONL event log for synthetic benchmark runs.
No public ARC data, no scoring, no submission.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

# Forbidden metadata keys — these must never appear in event metadata
FORBIDDEN_METADATA_KEYS_V1: frozenset[str] = frozenset({
    "raw_grid",
    "raw_grids",
    "train_grid",
    "test_grid",
    "expected_output",
    "expected_output_grid",
    "expected_outputs",
    "solution_grid",
    "answer_key",
    "public_solution",
})

ALLOWED_LEVELS_V1: frozenset[str] = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "SUMMARY"})

REQUIRED_PHASES_V1: tuple[str, ...] = (
    "run_start",
    "generation",
    "solver_execution",
    "evaluation",
    "failure_classification",
    "audit",
    "run_summary",
    "run_end",
)

REQUIRED_EVENT_TYPES_V1: tuple[str, ...] = (
    "run_started",
    "benchmark_config",
    "split_started",
    "task_started",
    "task_generated",
    "solver_packet_created",
    "primitive_discovery_summary",
    "family_discovery_summary",
    "selected_family",
    "fallback_used",
    "attempts_emitted",
    "exact_two_output_check",
    "task_solved",
    "task_unsolved",
    "adversarial_rejection",
    "malformed_output",
    "exception",
    "expected_output_isolation_check",
    "deterministic_replay_check",
    "split_summary",
    "run_summary",
    "run_finished",
)


def _check_metadata_safe(metadata: Mapping[str, Any], context: str = "") -> None:
    """Raise ValueError if metadata contains forbidden keys or non-JSON-safe values."""
    for key in metadata:
        if key in FORBIDDEN_METADATA_KEYS_V1:
            raise ValueError(
                f"Forbidden metadata key '{key}' in {context}. "
                f"Allowed keys must not include raw grids or expected output."
            )
        value = metadata[key]
        if not _is_json_safe(value):
            raise ValueError(
                f"Non-JSON-safe value for key '{key}' in {context}: {type(value).__name__}"
            )


def _is_json_safe(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, (list, tuple)):
        return all(_is_json_safe(v) for v in value)
    if isinstance(value, Mapping):
        return all(isinstance(k, str) and _is_json_safe(v) for k, v in value.items())
    return False


def _make_timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class ArcRunEventLogV1:
    """Structured JSONL event log for a single ARC-AGI-2 synthetic benchmark run."""

    def __init__(
        self,
        run_id: str,
        log_dir: str | Path,
        *,
        write_text_log: bool = True,
        write_jsonl: bool = True,
        write_summary: bool = True,
    ) -> None:
        self.run_id = run_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._write_text_log = write_text_log
        self._write_jsonl = write_jsonl
        self._write_summary = write_summary
        self._events: list[dict[str, Any]] = []
        self._text_lines: list[str] = []
        self._start_time: float | None = None
        self._event_count: int = 0

        if write_jsonl:
            self._jsonl_path = self.log_dir / "events.jsonl"
            self._jsonl_file = open(self._jsonl_path, "w", encoding="utf-8")
        else:
            self._jsonl_path = None
            self._jsonl_file = None

        if write_text_log:
            self._text_path = self.log_dir / "run.log"
            self._text_file = open(self._text_path, "w", encoding="utf-8")
        else:
            self._text_path = None
            self._text_file = None

    @property
    def jsonl_path(self) -> str | None:
        return str(self._jsonl_path) if self._jsonl_path else None

    @property
    def text_path(self) -> str | None:
        return str(self._text_path) if self._text_path else None

    @property
    def summary_path(self) -> str | None:
        p = self.log_dir / "summary.json"
        return str(p) if self._write_summary else None

    def emit(
        self,
        level: str,
        phase: str,
        event_type: str,
        message: str,
        metadata: Mapping[str, Any] | None = None,
        *,
        elapsed: float | None = None,
    ) -> None:
        """Emit a structured event."""
        if level not in ALLOWED_LEVELS_V1:
            raise ValueError(f"Unknown level '{level}'. Allowed: {sorted(ALLOWED_LEVELS_V1)}")
        if phase not in REQUIRED_PHASES_V1:
            raise ValueError(f"Unknown phase '{phase}'. Allowed: {REQUIRED_PHASES_V1}")
        if event_type not in REQUIRED_EVENT_TYPES_V1:
            raise ValueError(f"Unknown event_type '{event_type}'. Allowed: {REQUIRED_EVENT_TYPES_V1}")

        safe_metadata = dict(metadata) if metadata else {}
        _check_metadata_safe(safe_metadata, context=f"event {event_type}")

        if self._start_time is None:
            elapsed_sec = 0.0
        elif elapsed is not None:
            elapsed_sec = elapsed
        else:
            elapsed_sec = time.time() - self._start_time

        event = {
            "run_id": self.run_id,
            "timestamp_utc": _make_timestamp_utc(),
            "elapsed_sec": round(elapsed_sec, 4),
            "level": level,
            "phase": phase,
            "event_type": event_type,
            "message": message,
            "metadata": safe_metadata,
        }

        self._events.append(event)
        self._event_count += 1

        if self._jsonl_file is not None:
            self._jsonl_file.write(json.dumps(event, sort_keys=True) + "\n")
            self._jsonl_file.flush()

        if self._text_file is not None:
            text_line = self._format_text_line(event)
            self._text_file.write(text_line + "\n")
            self._text_file.flush()

    def _format_text_line(self, event: dict[str, Any]) -> str:
        elapsed = f"{event['elapsed_sec']:.2f}s"
        level = event["level"]
        event_type = event["event_type"]
        message = event["message"]
        meta = event.get("metadata", {})
        parts = [elapsed, level, event_type, message]
        if meta:
            meta_str = " ".join(f"{k}={v}" for k, v in sorted(meta.items()) if not isinstance(v, (list, dict)))
            if meta_str:
                parts.append(meta_str)
        return " ".join(parts)

    def start_run(self, config: Mapping[str, Any] | None = None) -> None:
        """Emit run_started event and start the timer."""
        self._start_time = time.time()
        self.emit("INFO", "run_start", "run_started", "Benchmark run started", config)

    def finish_run(self, summary: Mapping[str, Any] | None = None) -> None:
        """Emit run_finished event and write summary."""
        self.emit("SUMMARY", "run_end", "run_finished", "Benchmark run finished", summary)
        if self._write_summary:
            self._write_summary_file(summary)

    def _write_summary_file(self, summary: Mapping[str, Any] | None = None) -> None:
        summary_path = self.log_dir / "summary.json"
        summary_data: dict[str, Any] = {
            "run_id": self.run_id,
            "event_count": self._event_count,
        }
        if summary:
            summary_data["summary"] = dict(summary)
        summary_path.write_text(json.dumps(summary_data, indent=2, sort_keys=True))

    def close(self) -> None:
        """Close file handles."""
        if self._jsonl_file is not None:
            self._jsonl_file.close()
        if self._text_file is not None:
            self._text_file.close()

    def __enter__(self) -> ArcRunEventLogV1:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def make_run_id(prefix: str = "arc-synth") -> str:
    """Generate a deterministic-ish run ID with timestamp."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{prefix}-{ts}"


__all__ = [
    "FORBIDDEN_METADATA_KEYS_V1",
    "ALLOWED_LEVELS_V1",
    "REQUIRED_PHASES_V1",
    "REQUIRED_EVENT_TYPES_V1",
    "ArcRunEventLogV1",
    "make_run_id",
]