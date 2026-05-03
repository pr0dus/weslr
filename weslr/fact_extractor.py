"""
WESLR Fact Extractor V1

Deterministic extraction of subject-predicate-object triples from session summary text.
Uses 10 high-precision pattern rules. No probabilistic inference.

Authority: extracted_from_timeline
No raw prompts stored. No hidden learning. No automatic execution.
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any, Dict, List, Optional

# Path to fact assertions store
DEFAULT_FACT_STORE_PATH = ".weslr/fact_assertions.jsonl"


# ──────────────────────────────────────────────────────────────────────────────
# 10 Extraction Patterns
# ──────────────────────────────────────────────────────────────────────────────

def extract_triples_from_summary(
    summary_text: str,
    default_subject: str = "user",
) -> List[Dict[str, str]]:
    """Extract structured triples from a session summary string.

    Uses 10 deterministic regex patterns. Each match produces one triple.

    Args:
        summary_text: The session summary text to analyze.
        default_subject: Fallback subject when none detected.

    Returns:
        List of dicts with keys: subject, predicate, object (all normalized strings)
    """
    if not summary_text or not isinstance(summary_text, str):
        return []

    text = summary_text.strip()
    triples: List[Dict[str, str]] = []

    # Pattern 1: "X discussed Y" → (X, discussed, Y)
    m = re.match(r"^(.+?)\s+discussed\s+(.+)$", text, re.IGNORECASE)
    if m:
        subj = m.group(1).strip()
        triples.append(_make_triple(subj if subj.lower() != "we" else default_subject, "discussed", m.group(2).strip()))
        return triples  # Only one pattern fires per summary for precision

    # Pattern 2: "X said Y about Z" → (X, said_about, Z)
    m = re.match(r"^(.+?)\s+said\s+(.+?)\s+about\s+(.+)$", text, re.IGNORECASE)
    if m:
        triples.append(_make_triple(m.group(1).strip(), "said_about", m.group(3).strip()))
        return triples

    # Pattern 3: "X worked on Y" → (user, worked_on, Y)
    m = re.match(r"^(.+?)\s+worked\s+on\s+(.+)$", text, re.IGNORECASE)
    if m:
        subj = m.group(1).strip()
        triples.append(_make_triple(subj if subj != "we" else default_subject, "worked_on", m.group(2).strip()))
        return triples

    # Pattern 4: "X is important for Y" → (Y, has_importance, X)
    m = re.match(r"^(.+?)\s+is\s+important\s+for\s+(.+)$", text, re.IGNORECASE)
    if m:
        triples.append(_make_triple(m.group(2).strip(), "has_importance", m.group(1).strip()))
        return triples

    # Pattern 5: "X depends on Y" → (X, depends_on, Y)
    m = re.match(r"^(.+?)\s+depends\s+on\s+(.+)$", text, re.IGNORECASE)
    if m:
        triples.append(_make_triple(m.group(1).strip(), "depends_on", m.group(2).strip()))
        return triples

    # Pattern 6: "X is part of Y" → (X, part_of, Y)
    m = re.match(r"^(.+?)\s+is\s+part\s+of\s+(.+)$", text, re.IGNORECASE)
    if m:
        triples.append(_make_triple(m.group(1).strip(), "part_of", m.group(2).strip()))
        return triples

    # Pattern 7: "X uses Y" → (X, uses, Y)
    m = re.match(r"^(.+?)\s+uses\s+(.+)$", text, re.IGNORECASE)
    if m:
        triples.append(_make_triple(m.group(1).strip(), "uses", m.group(2).strip()))
        return triples

    # Pattern 8: "X created Y" → (X, created, Y)
    m = re.match(r"^(.+?)\s+created\s+(.+)$", text, re.IGNORECASE)
    if m:
        triples.append(_make_triple(m.group(1).strip(), "created", m.group(2).strip()))
        return triples

    # Pattern 9: "X tested Y" → (X, tested, Y)
    m = re.match(r"^(.+?)\s+tested\s+(.+)$", text, re.IGNORECASE)
    if m:
        triples.append(_make_triple(m.group(1).strip(), "tested", m.group(2).strip()))
        return triples

    # Pattern 10: "X upgraded Y" → (X, upgraded, Y)
    m = re.match(r"^(.+?)\s+upgraded\s+(.+)$", text, re.IGNORECASE)
    if m:
        triples.append(_make_triple(m.group(1).strip(), "upgraded", m.group(2).strip()))
        return triples

    return triples


def _normalize_entity(text: str) -> str:
    """Normalize a string into a stable entity reference.

    - Lowercase
    - Collapse whitespace/underscores/hyphens to single underscore
    - Strip leading/trailing underscores
    """
    if not text:
        return "unknown"
    normalized = text.lower().strip()
    normalized = re.sub(r"[-:_\s]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        return "unknown"
    return normalized


def _make_triple(subject: str, predicate: str, obj: str) -> Dict[str, str]:
    """Create a normalized triple dict."""
    return {
        "subject": _normalize_entity(subject),
        "predicate": _normalize_entity(predicate),
        "object": _normalize_entity(obj),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Append Fact Assertion
# ──────────────────────────────────────────────────────────────────────────────

def append_fact_assertion(
    triple: Dict[str, str],
    source_event_ref: str,
    fact_store_path: str = DEFAULT_FACT_STORE_PATH,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a fact triple as a JSONL record to fact_assertions.jsonl.

    Args:
        triple: Dict with subject, predicate, object (all normalized strings)
        source_event_ref: Reference to the source timeline event (e.g. "user_arthur:2026-05-02T14:48:20Z")
        fact_store_path: Path to the JSONL store
        project_id: Optional project scope

    Returns:
        dict with keys: event, path, status: "appended"
    """
    import time
    if not triple or not all(k in triple for k in ("subject", "predicate", "object")):
        raise ValueError("triple must have subject, predicate, object keys")

    event = {
        "record_type": "fact_assertion_v1",
        "subject": triple["subject"],
        "predicate": triple["predicate"],
        "object": triple["object"],
        "source_event_ref": source_event_ref,
        "project_id": project_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "authority": "extracted_from_timeline",
        "automatic_action": False,
        "hidden_learning": False,
        "raw_prompt_stored": False,
    }

    path = pathlib.Path(fact_store_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(event, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return {"event": event, "path": str(path), "status": "appended"}


# ──────────────────────────────────────────────────────────────────────────────
# Load Facts
# ──────────────────────────────────────────────────────────────────────────────

def load_facts(
    subject: Optional[str] = None,
    predicate: Optional[str] = None,
    obj: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 100,
    fact_store_path: str = DEFAULT_FACT_STORE_PATH,
) -> List[Dict[str, Any]]:
    """Load fact assertions with optional filters.

    Args:
        subject: Match subject (normalized, substring match)
        predicate: Match predicate (normalized, substring match)
        obj: Match object (normalized, substring match)
        project_id: If set, only return facts scoped to this project
        limit: Maximum number of records to return
        fact_store_path: Path to the JSONL store

    Returns:
        List of fact assertion dicts
    """
    path = pathlib.Path(fact_store_path)
    if not path.exists():
        return []

    results: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Apply filters
                if subject and subject not in record.get("subject", ""):
                    continue
                if predicate and predicate not in record.get("predicate", ""):
                    continue
                if obj and obj not in record.get("object", ""):
                    continue
                if project_id is not None and record.get("project_id") != project_id:
                    continue

                results.append(record)
                if len(results) >= limit:
                    break
    except OSError:
        pass

    return results
