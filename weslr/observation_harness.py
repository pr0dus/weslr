"""
WESLR Observation Harness V1

Local-only observation harness implementing WESLR_OBSERVATION_EXECUTION_PLAN_V1.
Runs controlled observation sessions using scripted input sequences.
Does NOT call live staging. Does NOT write production JSONL.

Functions:
  load_script        — parse and validate scripted input sequence
  run_observation_session  — run one bounded session, return events
  build_timeline_segment  — convert session results to ordered timeline events
  validate_batch     — check batch requirements
"""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any


# ---------------------------------------------------------------------------
# Script Validation
# ---------------------------------------------------------------------------

VALID_CATEGORIES = frozenset({
    "neutral", "unknown", "evidence_trigger",
    "conflict", "noise", "domain_shift", "safety_probe",
})


def load_script(script: list[dict]) -> list[dict]:
    """
    Parse and validate a scripted input sequence.

    INPUT:
        script — list of dicts, each with:
          {
            "input": "...",        # required, non-empty string
            "category": "...",     # required, one of VALID_CATEGORIES
          }

    OUTPUT:
        Validated list of dicts with added fields:
          message_index, timestamp, provenance_chain_id

    RAISES:
        ValueError if validation fails

    DOES NOT:
      - write to production state
      - call live staging
      - modify prompts
    """
    if not isinstance(script, list):
        raise ValueError("script must be a list")

    validated = []
    for i, item in enumerate(script):
        if not isinstance(item, dict):
            raise ValueError(f"script item {i} is not a dict")
        if "input" not in item:
            raise ValueError(f"script item {i} missing 'input' field")
        if "category" not in item:
            raise ValueError(f"script item {i} missing 'category' field")
        input_text = str(item["input"]).strip()
        if not input_text:
            raise ValueError(f"script item {i} has empty 'input'")

        category = str(item["category"]).strip().lower()
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"script item {i}: category '{category}' not in {sorted(VALID_CATEGORIES)}"
            )

        provenance_chain_id = _make_provenance_id(
            session_id="pending",
            message_index=i + 1,
            timestamp=0.0,
        )

        validated.append({
            "input": input_text,
            "category": category,
            "message_index": i + 1,
            "provenance_chain_id": provenance_chain_id,
        })

    return validated


# ---------------------------------------------------------------------------
# Mock Signal Rules (V1 — no live staging)
# ---------------------------------------------------------------------------
# Signal emission is deterministic based on input category and content patterns.
# This is a local mock for harness testing only — not production signal detection.

_MOCK_SIGNAL_MAP = {
    "neutral":       None,          # no signal
    "unknown":      "S1",          # unknown query pattern
    "evidence_trigger": "S2",       # evidence workspace usage
    "conflict":      None,          # behavioral stability test — no signal per session
    "noise":         None,          # noise filter test — no signal
    "domain_shift":  "S3",          # recurring topic cluster (mocked)
    "safety_probe":  None,          # governance edge case — no signal in mock
}

# Confidence ranges per signal type (mocked)
_MOCK_CONFIDENCE = {
    "S1": (0.78, 0.92),
    "S2": (0.82, 0.95),
    "S3": (0.70, 0.88),
    "S4": (0.75, 0.90),
    "S5": (0.80, 0.93),
    "S6": (0.68, 0.85),
}

_RESPONSE_PATHS = [
    "handler_unrelated_query",
    "handler_evidence_overlay",
    "handler_fallback_response",
    "handler_graph_traversal",
    "handler_introspection",
    "handler_valence_check",
    "handler_capability_discovery",
    "handler_none",
]


def _mock_signal(category: str, message_index: int) -> tuple[bool, str | None, str]:
    """
    Deterministic mock signal emission for V1 harness.
    No LLM. No production state. No writes.
    """
    signal_type = _MOCK_SIGNAL_MAP.get(category)
    if signal_type is None:
        return False, None, "handler_none"

    # Vary response path by message_index for diversity
    path_idx = (message_index * 7 + 3) % len(_RESPONSE_PATHS)
    response_path = _RESPONSE_PATHS[path_idx]

    return True, signal_type, response_path


# ---------------------------------------------------------------------------
# Session Run
# ---------------------------------------------------------------------------

def run_observation_session(
    script: list[dict],
    session_id: str,
) -> dict:
    """
    Run one bounded observation session using a validated script.

    INPUT:
        script  — output of load_script()
        session_id — string, unique session identifier

    OUTPUT:
        {
          "session_id": "...",
          "events": [
            {
              "message_index": int,
              "input": "...",
              "input_category": "...",
              "response_path": "...",
              "signal_emitted": bool,
              "signal_type": "S1|S2|S3|S4|S5|S6|null",
              "timestamp": "ISO-8601",
              "provenance_chain_id": "..."
            }
          ]
        }

    RULES:
      - No cross-session memory
      - No mid-session aggregation
      - No prompt adaptation
      - No production JSONL writes
    """
    validated_script = load_script(script) if not script[0].get("message_index") else script

    session_start = time.time()
    events = []

    for item in validated_script:
        ts = session_start + (item["message_index"] - 1) * 0.1
        signal_emitted, signal_type, response_path = _mock_signal(
            item["category"], item["message_index"]
        )

        # Rebuild provenance_chain_id with actual session_id and timestamp
        provenance_chain_id = _make_provenance_id(
            session_id=session_id,
            message_index=item["message_index"],
            timestamp=ts,
        )

        events.append({
            "message_index": item["message_index"],
            "input": item["input"],
            "input_category": item["category"],
            "response_path": response_path,
            "signal_emitted": signal_emitted,
            "signal_type": signal_type,
            "timestamp": _iso_timestamp(ts),
            "provenance_chain_id": provenance_chain_id,
        })

    return {
        "session_id": session_id,
        "events": events,
    }


# ---------------------------------------------------------------------------
# Timeline Segment
# ---------------------------------------------------------------------------

def build_timeline_segment(session_results: list[dict]) -> list[dict]:
    """
    Convert session results into ordered timeline events.

    INPUT:
        session_results — list of session outputs from run_observation_session()

    OUTPUT:
        Ordered list of timeline events:
        [
          {
            "event_id": "...",
            "timeline_segment_id": "...",
            "session_id": "...",
            "run_index": int,
            "timestamp": "ISO-8601",
            "signal_type": "S1|S2|S3|S4|S5|S6|null",
            "signal_emitted": bool,
            "input_category": "...",
            "provenance_chain_id": "..."
          }
        ]

    ORDER:
      - Primary sort: timestamp
      - Secondary sort: session order (run_index)
      - Within session: message_index order
    """
    if not session_results:
        return []

    segment_id = f"seg_{_short_ts()}_{uuid.uuid4().hex[:8]}"

    timeline_events: list[dict] = []

    for run_index, session in enumerate(session_results):
        sid = session.get("session_id", f"session_{run_index}")
        for event in session.get("events", []):
            timeline_events.append({
                "event_id": f"evt_{uuid.uuid4().hex[:12]}",
                "timeline_segment_id": segment_id,
                "session_id": sid,
                "run_index": run_index,
                "timestamp": event["timestamp"],
                "signal_type": event["signal_type"],
                "signal_emitted": event["signal_emitted"],
                "input_category": event["input_category"],
                "provenance_chain_id": event["provenance_chain_id"],
            })

    # Sort by timestamp (primary), then run_index (secondary)
    timeline_events.sort(key=lambda e: (e["timestamp"], e["run_index"], e.get("message_index", 0)))

    return timeline_events


# ---------------------------------------------------------------------------
# Batch Validation
# ---------------------------------------------------------------------------

def validate_batch(session_results: list[dict]) -> tuple[bool, list[str]]:
    """
    Validate that a batch of session results meets observation requirements.

    INPUT:
        session_results — list of session outputs

    OUTPUT:
        (is_valid, list_of_failures)
        is_valid=True only if all checks pass

    CHECKS:
      - At least 3 sessions
      - Each session has 10–20 interactions
      - Every event has provenance_chain_id
      - No cross-session memory fields (session_id is not memory)
      - No production JSONL writes (pure function — checked by design)
    """
    failures: list[str] = []

    if len(session_results) < 3:
        failures.append(f"Batch has {len(session_results)} sessions, minimum 3 required")

    for idx, session in enumerate(session_results):
        sid = session.get("session_id", f"<session {idx}>")
        events = session.get("events", [])

        if not (10 <= len(events) <= 20):
            failures.append(
                f"Session {sid}: {len(events)} events, required range 10–20"
            )

        for e_idx, event in enumerate(events):
            if "provenance_chain_id" not in event:
                failures.append(
                    f"Session {sid} event {e_idx}: missing provenance_chain_id"
                )
            if not event.get("provenance_chain_id"):
                failures.append(
                    f"Session {sid} event {e_idx}: provenance_chain_id is empty"
                )

    return len(failures) == 0, failures


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _make_provenance_id(session_id: str, message_index: int, timestamp: float) -> str:
    key = f"{session_id}:{message_index}:{timestamp}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]


def _short_ts() -> str:
    return str(int(time.time()))


def _iso_timestamp(ts: float) -> str:
    from datetime import datetime, timezone
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.isoformat()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    help_text = """WESLR Observation Harness V1

Usage:
  python observation_harness.py session <script_json> <session_id>
  python observation_harness.py batch <sessions_json>
  python observation_harness.py timeline <sessions_json>

Examples:
  python observation_harness.py session script.json session_20260430_001
  python observation_harness.py batch sessions.json
"""

    if len(sys.argv) < 2:
        print(help_text)

    cmd = sys.argv[1]

    def read_json(path: str):
        with open(path) as f:
            return json.load(f)

    if cmd == "session":
        if len(sys.argv) < 4:
            print("Error: session requires <script_json> <session_id>")
            sys.exit(1)
        script = read_json(sys.argv[2])
        session_id = sys.argv[3]
        result = run_observation_session(script, session_id)
        print(json.dumps(result, indent=2))

    elif cmd == "batch":
        if len(sys.argv) < 3:
            print("Error: batch requires <sessions_json>")
            sys.exit(1)
        sessions = read_json(sys.argv[2])
        is_valid, failures = validate_batch(sessions)
        print(f"Batch valid: {is_valid}")
        if failures:
            for f in failures:
                print(f"  FAIL: {f}")

    elif cmd == "timeline":
        if len(sys.argv) < 3:
            print("Error: timeline requires <sessions_json>")
            sys.exit(1)
        sessions = read_json(sys.argv[2])
        timeline = build_timeline_segment(sessions)
        print(json.dumps(timeline, indent=2))

    else:
        print(f"Unknown command: {cmd}")
        print(help_text)