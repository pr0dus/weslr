"""
WESLR Contract Insufficiency Detector V1

Read-only pattern detector — reads from contract_observations.jsonl,
detects stable insufficient contract outcomes, logs evidence locally.

Does NOT:
- change behavior
- create proposals
- write to production truth files
- use LLM inference
- modify public_signals.jsonl
"""

from __future__ import annotations

import json
import pathlib
from collections import defaultdict

# ---------------------------------------------------------------------------
# Storage configuration
# ---------------------------------------------------------------------------

DEFAULT_OBSERVATION_PATH = "weslr/contract_observations.jsonl"
DEFAULT_INSUFFICIENCY_LOG_PATH = "weslr/contract_insufficiency_log.jsonl"
DEFAULT_WINDOW_SIZE = 50
DEFAULT_MIN_RECORDS = 10
DEFAULT_STABILITY_THRESHOLD = 3

# ---------------------------------------------------------------------------
# Insufficiency criteria (AND logic — all must be true)
# ---------------------------------------------------------------------------

IC1_MIN_OCCURRENCES = 3      # same contract fires >= 3 times in window
IC4_WEAK_FRAMES = frozenset({"entry", "unknown"})  # weak frame classification
IC4_WEAK_SIGNALS = frozenset({None, "S4"})          # no S1/S2 improvement

# ---------------------------------------------------------------------------
# Pattern types
# ---------------------------------------------------------------------------

PATTERN_WEAK_ENTRY_REPETITION = "weak_entry_repetition"
PATTERN_FALLBACK_REPETITION = "fallback_repetition"
PATTERN_TASK_HELP_DEGRADATION = "task_help_degradation"
PATTERN_EXPLANATION_DEGRADATION = "explanation_degradation"
PATTERN_UNKNOWN_FRAME_STABILIZATION = "unknown_frame_stabilization"

_PATTERN_BY_CONTRACT = {
    "conversational_entry": PATTERN_WEAK_ENTRY_REPETITION,
    "fallback_safe": PATTERN_FALLBACK_REPETITION,
    "task_help": PATTERN_TASK_HELP_DEGRADATION,
    "structured_explanation": PATTERN_EXPLANATION_DEGRADATION,
    "unknown": PATTERN_UNKNOWN_FRAME_STABILIZATION,
}

# ---------------------------------------------------------------------------
# Sliding window reader
# ---------------------------------------------------------------------------

def _read_tail(path: str, n: int) -> list[dict]:
    """Read last n lines from a JSONL file. Returns list of parsed dicts."""
    p = pathlib.Path(path)
    if not p.exists():
        return []
    with open(p) as f:
        lines = [line.strip() for line in f if line.strip()]
    records = []
    for line in lines[-n:]:
        try:
            records.append(json.loads(line))
        except Exception:
            continue
    return records


# ---------------------------------------------------------------------------
# Insufficiency detection
# ---------------------------------------------------------------------------

def detect_insufficiency(
    observation_path: str | None = None,
    insufficiency_log_path: str | None = None,
    window_size: int = DEFAULT_WINDOW_SIZE,
    min_records: int = DEFAULT_MIN_RECORDS,
) -> dict:
    """
    Detect insufficiency patterns in the contract observation sliding window.

    RETURN: {
        "checked_at": "...",
        "window_records": N,
        "insufficiency_found": bool,
        "contracts_checked": [...],
        "proposal_ready_patterns": [...]
    }
    """
    from datetime import datetime, timezone

    obs_path = observation_path or DEFAULT_OBSERVATION_PATH
    records = _read_tail(obs_path, window_size)

    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "window_records": len(records),
        "insufficiency_found": False,
        "contracts_checked": [],
        "proposal_ready_patterns": [],
    }

    if len(records) < min_records:
        return result

    # Group by response_contract
    by_contract: dict = defaultdict(list)
    for rec in records:
        contract = rec.get("response_contract", "unknown")
        by_contract[contract].append(rec)

    proposal_ready = []

    for contract, group in by_contract.items():
        if len(group) < IC1_MIN_OCCURRENCES:
            continue

        result["contracts_checked"].append(contract)

        # IC2: same response_path
        paths = set(r.get("response_path") for r in group)
        if len(paths) != 1:
            continue

        response_path = next(iter(paths))

        # IC3: all signal_types are null or S4
        signal_types = [r.get("signal_type") for r in group]
        if not all(s in IC4_WEAK_SIGNALS for s in signal_types):
            continue

        # IC4: frame distribution (all weak frames)
        frames = [r.get("interaction_frame", "unknown") for r in group]
        if not all(f in IC4_WEAK_FRAMES for f in frames):
            continue

        pattern_type = _PATTERN_BY_CONTRACT.get(contract, "generic_repetition")

        from collections import Counter
        frame_dist = dict(Counter(frames))
        signal_dist = dict(Counter(signal_types))

        evidence = {
            "record_type": "contract_insufficiency_v1",
            "pattern_type": pattern_type,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "window_size": window_size,
            "record_count_in_window": len(records),
            "contract": contract,
            "response_path": response_path,
            "occurrence_count": len(group),
            "signal_types_seen": signal_types,
            "frame_distribution": frame_dist,
            "signal_type_distribution": signal_dist,
            "insufficiency_confirmed": True,
        }

        # Wire stability tracker — updates consecutive count and proposal_ready
        stability = check_stability(pattern_type, contract, evidence)
        evidence["stable_across_checks"] = stability["consecutive_checks"]
        evidence["proposal_ready"] = stability["proposal_ready"]

        # Append evidence to insufficiency log
        _append_insufficiency_evidence(evidence, insufficiency_log_path=insufficiency_log_path)
        proposal_ready.append({
            "pattern_type": pattern_type,
            "contract": contract,
            "proposal_ready": stability["proposal_ready"],
            "stable_across_checks": stability["consecutive_checks"],
        })

    if proposal_ready:
        result["insufficiency_found"] = True
        result["proposal_ready_patterns"] = proposal_ready

    return result


def _append_insufficiency_evidence(evidence: dict, insufficiency_log_path: str | None = None) -> None:
    """Append insufficiency evidence to local log. Fire-and-forget."""
    try:
        path = insufficiency_log_path or DEFAULT_INSUFFICIENCY_LOG_PATH
        with open(path, "a") as f:
            f.write(json.dumps(evidence) + "\n")
    except Exception:
        pass  # fire-and-forget


# ---------------------------------------------------------------------------
# Stability tracker
# ---------------------------------------------------------------------------

_STABILITY_COUNTS: dict[str, int] = {}
_STABLE_PATTERNS: dict[str, dict] = {}


def _get_contract_key(record: dict) -> str | None:
    """Return contract key value, checking both 'contract' and 'response_contract'."""
    return record.get("contract") or record.get("response_contract")


def check_stability(
    pattern_type: str,
    contract: str,
    current_evidence: dict,
    min_checks: int = DEFAULT_STABILITY_THRESHOLD,
) -> dict:
    """
    Track stability of a detected insufficiency pattern across consecutive checks.

    A pattern becomes proposal_ready when it is detected >= min_checks times
    consecutively with the same pattern_type + contract.
    """
    key = f"{pattern_type}::{contract}"
    prev = _STABLE_PATTERNS.get(key)
    prev_contract = _get_contract_key(prev) if prev else None

    if prev is not None and prev_contract == contract:
        _STABILITY_COUNTS[key] = _STABILITY_COUNTS.get(key, 0) + 1
    else:
        _STABILITY_COUNTS[key] = 1

    _STABLE_PATTERNS[key] = current_evidence
    count = _STABILITY_COUNTS[key]
    stable = count >= min_checks

    result = {
        "pattern_type": pattern_type,
        "contract": contract,
        "consecutive_checks": count,
        "stable": stable,
        "proposal_ready": stable,
        "min_checks_required": min_checks,
    }

    if stable:
        # Mark the stored evidence as stable
        _STABLE_PATTERNS[key]["stable_across_checks"] = count
        _STABLE_PATTERNS[key]["proposal_ready"] = True


    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 contract_insufficiency_detector.py check [--window N]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "check":
        window = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else DEFAULT_WINDOW_SIZE
        result = detect_insufficiency(window_size=window)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python3 contract_insufficiency_detector.py check [--window N]")
        sys.exit(1)