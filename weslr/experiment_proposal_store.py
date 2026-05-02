"""
WESLR Experiment Proposal Store V1

Append-only proposal queue. Read/query API. No execution, no external calls.

Schema:
  weslr/experiment_proposals.jsonl

Rules:
- Append-only — never mutate existing JSONL lines
- Malformed lines ignored silently
- Missing file returns empty list
- Deduplication before append
- No Ollama, no external services

Author: OCC (WESLR governed intelligence)
Version: 1.0.0
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Optional

from weslr.experiment_proposal_schema import (
    generate_experiment_proposal_id,
    validate_experiment_proposal,
)

# ---------------------------------------------------------------------------
# Default path
# ---------------------------------------------------------------------------

def get_default_experiment_proposal_path() -> pathlib.Path:
    """Return the default path for the experiment proposals queue."""
    return pathlib.Path("weslr/experiment_proposals.jsonl")


# ---------------------------------------------------------------------------
# 1. Load proposals
# ---------------------------------------------------------------------------

def load_experiment_proposals(
    path: Optional[str | pathlib.Path] = None,
    status: Optional[str] = None,
    type_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Load proposals from JSONL, with optional status and type filters.

    Args:
        path: Path to JSONL file. Defaults to get_default_experiment_proposal_path().
        status: Filter by execution_status (exact match, case-insensitive).
        type_filter: Filter by type (exact match, case-insensitive).

    Returns:
        List of proposal dicts, most recent first (by file order = append order).
    """
    if path is None:
        path = get_default_experiment_proposal_path()
    p = pathlib.Path(path)

    if not p.exists():
        return []

    records: List[Dict[str, Any]] = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Filter by record_type (skip status/result events)
            if rec.get("record_type") != "experiment_proposal_v1":
                continue

            # Filter by status
            if status is not None:
                if rec.get("execution_status", "").lower() != status.lower():
                    continue

            # Filter by type
            if type_filter is not None:
                if rec.get("type", "").lower() != type_filter.lower():
                    continue

            records.append(rec)

    return records


# ---------------------------------------------------------------------------
# 2. Deduplication key
# ---------------------------------------------------------------------------

def proposal_dedup_key(record: dict) -> str:
    """Build a deduplication key for a proposal record.

    Key components:
      type + title (normalized lowercase) + timeline_id + related_capability

    Two proposals are considered duplicates if their dedup keys match.
    """
    parts = [
        record.get("type", "").lower(),
        _normalize_for_dedup(record.get("title", "")),
        str(record.get("timeline_id") or ""),
        str(record.get("related_capability") or ""),
    ]
    return "|".join(parts)


def _normalize_for_dedup(text: str) -> str:
    """Normalize a string for deduplication comparison."""
    text = text.lower()
    # Collapse whitespace
    text = " ".join(text.split())
    return text.strip()


# ---------------------------------------------------------------------------
# 3. Check if proposal exists
# ---------------------------------------------------------------------------

def proposal_exists(
    record: dict,
    path: Optional[str | pathlib.Path] = None,
) -> bool:
    """Return True if a proposal with the same dedup key already exists in the queue."""
    key = proposal_dedup_key(record)
    existing = load_experiment_proposals(path=path)
    for rec in existing:
        if proposal_dedup_key(rec) == key:
            return True
    return False


# ---------------------------------------------------------------------------
# 4. Append proposal
# ---------------------------------------------------------------------------

def append_experiment_proposal(
    record: dict,
    path: Optional[str | pathlib.Path] = None,
) -> Dict[str, Any]:
    """Validate and append a single proposal to the JSONL queue.

    Args:
        record: Proposal dict (experiment_proposal_v1)
        path: Target JSONL file. Defaults to get_default_experiment_proposal_path().

    Returns:
        dict with keys: status ("appended"), path, proposal_id

    Raises:
        ValueError: If validation fails
    """
    if path is None:
        path = get_default_experiment_proposal_path()
    p = pathlib.Path(path)

    # Validate first
    valid, errors = validate_experiment_proposal(record)
    if not valid:
        raise ValueError(f"Proposal validation failed: {'; '.join(errors)}")

    # Create parent dir if needed
    p.parent.mkdir(parents=True, exist_ok=True)

    # Append
    line = json.dumps(record, ensure_ascii=False)
    with open(p, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return {
        "status": "appended",
        "path": str(p),
        "proposal_id": record.get("proposal_id"),
    }


# ---------------------------------------------------------------------------
# 5. Append if not duplicate
# ---------------------------------------------------------------------------

def append_if_new(
    record: dict,
    path: Optional[str | pathlib.Path] = None,
) -> Dict[str, Any]:
    """Append only if dedup key is not already present in the queue.

    Args:
        record: Proposal dict
        path: Target JSONL file

    Returns:
        dict with keys: status ("appended" | "skipped_duplicate"),
                        path, proposal_id
    """
    if path is None:
        path = get_default_experiment_proposal_path()

    if proposal_exists(record, path=path):
        return {
            "status": "skipped_duplicate",
            "path": str(pathlib.Path(path)),
            "proposal_id": record.get("proposal_id"),
        }

    result = append_experiment_proposal(record, path=path)
    result["status"] = "appended"
    return result
