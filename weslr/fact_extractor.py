"""
WESLR Fact Extractor V1

Deterministic extraction of subject-predicate-object triples from session summary text.
Uses 10 high-precision pattern rules for generic extraction, plus domain-specific
pattern files for clinical trial and research document extraction.

Authority: extracted_from_timeline / extracted_from_document
No raw prompts stored. No hidden learning. No automatic execution.
"""

from __future__ import annotations

import json
import pathlib
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Path to fact assertions store
DEFAULT_FACT_STORE_PATH = ".weslr/fact_assertions.jsonl"


# ──────────────────────────────────────────────────────────────────────────────
# Fallback Generic Patterns (10 original session-summary patterns)
# ──────────────────────────────────────────────────────────────────────────────

# Used by extract_triples_from_summary() — the original session-summary extractor.
# Each entry: (pattern_id, regex_string, predicate_template)
_FALLBACK_PATTERNS: List[tuple[str, str, str]] = [
    ("generic.discussed",      r"^(.+?)\s+discussed\s+(.+)$",                       "discussed"),
    ("generic.said_about",     r"^(.+?)\s+said\s+(.+?)\s+about\s+(.+)$",              "said_about"),
    ("generic.worked_on",      r"^(.+?)\s+worked\s+on\s+(.+)$",                        "worked_on"),
    ("generic.has_importance", r"^(.+?)\s+is\s+important\s+for\s+(.+)$",              "has_importance"),
    ("generic.depends_on",     r"^(.+?)\s+depends\s+on\s+(.+)$",                       "depends_on"),
    ("generic.part_of",        r"^(.+?)\s+is\s+part\s+of\s+(.+)$",                    "part_of"),
    ("generic.uses",           r"^(.+?)\s+uses\s+(.+)$",                               "uses"),
    ("generic.created",        r"^(.+?)\s+created\s+(.+)$",                            "created"),
    ("generic.tested",         r"^(.+?)\s+tested\s+(.+)$",                             "tested"),
    ("generic.upgraded",       r"^(.+?)\s+upgraded\s+(.+)$",                            "upgraded"),
]


# ──────────────────────────────────────────────────────────────────────────────
# Domain Pattern Loader
# ──────────────────────────────────────────────────────────────────────────────

# In-memory cache: domain → list of pattern dicts
_DOMAIN_PATTERN_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def _get_fallback_patterns() -> List[Dict[str, Any]]:
    """Return the 10 original generic session-summary patterns as dicts.

    Used when a domain pattern file is not found.
    Each dict has the same structure as a domain pattern:
      pattern_id, regex, confidence, groups.
    """
    return [
        {
            "pattern_id": "generic.discussed",
            "regex": r"^(.+?)\s+discussed\s+(.+)$",
            "confidence": 0.8,
            "groups": {"subject": 1, "object": 2},
        },
        {
            "pattern_id": "generic.said_about",
            "regex": r"^(.+?)\s+said\s+(.+?)\s+about\s+(.+)$",
            "confidence": 0.8,
            "groups": {"subject": 1, "object": 3},
        },
        {
            "pattern_id": "generic.worked_on",
            "regex": r"^(.+?)\s+worked\s+on\s+(.+)$",
            "confidence": 0.8,
            "groups": {"subject": 1, "object": 2},
        },
        {
            "pattern_id": "generic.has_importance",
            "regex": r"^(.+?)\s+is\s+important\s+for\s+(.+)$",
            "confidence": 0.8,
            "groups": {"subject": 1, "object": 2},
        },
        {
            "pattern_id": "generic.depends_on",
            "regex": r"^(.+?)\s+depends\s+on\s+(.+)$",
            "confidence": 0.8,
            "groups": {"subject": 1, "object": 2},
        },
        {
            "pattern_id": "generic.part_of",
            "regex": r"^(.+?)\s+is\s+part\s+of\s+(.+)$",
            "confidence": 0.8,
            "groups": {"subject": 1, "object": 2},
        },
        {
            "pattern_id": "generic.uses",
            "regex": r"^(.+?)\s+uses\s+(.+)$",
            "confidence": 0.8,
            "groups": {"subject": 1, "object": 2},
        },
        {
            "pattern_id": "generic.created",
            "regex": r"^(.+?)\s+created\s+(.+)$",
            "confidence": 0.8,
            "groups": {"subject": 1, "object": 2},
        },
        {
            "pattern_id": "generic.tested",
            "regex": r"^(.+?)\s+tested\s+(.+)$",
            "confidence": 0.8,
            "groups": {"subject": 1, "object": 2},
        },
        {
            "pattern_id": "generic.upgraded",
            "regex": r"^(.+?)\s+upgraded\s+(.+)$",
            "confidence": 0.8,
            "groups": {"subject": 1, "object": 2},
        },
    ]


def load_patterns(domain: str = "cancer_research") -> List[Dict[str, Any]]:
    """Load extraction patterns for the given domain.

    Loads from weslr/fact_patterns/<domain>.json.
    Falls back to empty list if file not found (upstream caller handles fallback).

    Caches after first load per domain.

    Each pattern dict has keys:
      - pattern_id: str
      - regex: str (Python regex, case-insensitive via (?i) in pattern or re.IGNORECASE)
      - confidence: float (0.5–1.0)
      - groups: dict mapping field name → group index (1-based)
    """
    if domain in _DOMAIN_PATTERN_CACHE:
        return _DOMAIN_PATTERN_CACHE[domain]

    pattern_file = pathlib.Path(__file__).parent / "fact_patterns" / f"{domain}.json"
    if not pattern_file.exists():
        return _get_fallback_patterns()

    with open(pattern_file, encoding="utf-8") as f:
        data = json.load(f)

    patterns = data.get("patterns", [])
    _DOMAIN_PATTERN_CACHE[domain] = patterns
    return patterns


# ──────────────────────────────────────────────────────────────────────────────
# Generic Triple Extraction (session-summary path — unchanged)
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_entity(text: str) -> str:
    """Normalize a string into a stable entity reference."""
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


def extract_triples_from_summary(
    summary_text: str,
    default_subject: str = "user",
) -> List[Dict[str, str]]:
    """Extract structured triples from a session summary string.

    Uses the 10 deterministic generic patterns. Each match produces one triple.

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

    for pid, pat_re, pred in _FALLBACK_PATTERNS:
        m = re.match(pat_re, text, re.IGNORECASE)
        if m:
            subj = m.group(1).strip()
            triples.append(_make_triple(
                subj if subj.lower() != "we" else default_subject,
                pred,
                m.group(2).strip(),
            ))
            return triples  # Only one pattern fires per summary for precision

    return triples


# ──────────────────────────────────────────────────────────────────────────────
# Domain-Aware Fact Extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_facts_with_positions(
    text: str,
    page: int = 1,
    line_start: int = 0,
    domain: str = "cancer_research",
) -> List[Dict[str, Any]]:
    """Extract structured facts from arbitrary text using domain patterns.

    Loads patterns from fact_patterns/<domain>.json and applies each regex.
    Returns enriched fact dicts with character offsets and structured data.

    Args:
        text: Text to extract from.
        page: Page number (for provenance).
        line_start: Starting line number (for provenance).
        domain: Domain name for pattern loading (default: cancer_research).

    Returns:
        List of dicts with keys:
          - pattern_id: str
          - subject, predicate, object: str (normalized entity strings)
          - fact_data: dict (structured fields from regex group captures)
          - confidence: float (from pattern config)
          - char_start, char_end: int (character offsets in text)
          - line_start, line_end: int (line numbers in text)
          - page: int
    """
    if not text or not isinstance(text, str):
        return []

    patterns = load_patterns(domain)
    if not patterns:
        return []

    facts: List[Dict[str, Any]] = []

    for pat in patterns:
        pat_id = pat.get("pattern_id", "unknown")
        pat_regex = pat.get("regex", "")
        confidence = pat.get("confidence", 0.8)
        groups_map = pat.get("groups", {})  # field_name -> group_index (1-based)

        try:
            compiled = re.compile(pat_regex, re.IGNORECASE)
        except re.PatternError:
            continue

        for m in compiled.finditer(text):
            # Build structured fact_data from named group captures
            fact_data: Dict[str, Any] = {}
            for field_name, group_idx in groups_map.items():
                try:
                    val = m.group(group_idx)
                    if val is not None:
                        fact_data[field_name] = val.strip()
                except (IndexError, TypeError):
                    pass

            # Compute line range from character offsets
            cs = m.start()
            ce = m.end()
            ls = text[:cs].count("\n") + line_start
            le = text[:ce].count("\n") + line_start

            # Extract subject, predicate, object for triple compat
            # Predicate is normalized pattern_id (e.g. "survival_rate")
            predicate_normalized = _normalize_entity(
                pat.get("predicate", pat_id.replace(".", "_"))
            )

            # Subject: first capture group value or domain name
            if groups_map:
                first_field = list(groups_map.keys())[0]
                subj_raw = fact_data.get(first_field, domain)
            else:
                subj_raw = domain
            subject_normalized = _normalize_entity(subj_raw)

            # Object: second capture group value or generic placeholder
            if len(groups_map) > 1:
                second_field = list(groups_map.keys())[1]
                obj_raw = fact_data.get(second_field, m.group(0)[:50])
            else:
                obj_raw = m.group(0)[:50]
            object_normalized = _normalize_entity(obj_raw)

            facts.append({
                "pattern_id": pat_id,
                "subject": subject_normalized,
                "predicate": predicate_normalized,
                "object": object_normalized,
                "fact_data": fact_data,
                "confidence": confidence,
                "char_start": cs,
                "char_end": ce,
                "line_start": ls,
                "line_end": le,
                "page": page,
            })

    return facts


# ──────────────────────────────────────────────────────────────────────────────
# Append Fact Assertion (enriched — for domain extractions)
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
        source_event_ref: Reference to the source timeline event
        fact_store_path: Path to the JSONL store
        project_id: Optional project scope

    Returns:
        dict with keys: event, path, status: "appended"
    """
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


def append_enriched_fact(
    fact: Dict[str, Any],
    fact_store_path: str = DEFAULT_FACT_STORE_PATH,
) -> Dict[str, Any]:
    """Append an enriched fact (from domain extraction) to fact_assertions.jsonl.

    Adds record_type, timestamp, and authority if not present.
    Stores all provenance fields (source_doc_id, source_reference, source_type,
    trust_score, domains, extraction_pattern).

    Args:
        fact: Dict with at least subject, predicate, object, source_reference,
              source_type, trust_score, extraction_pattern.
        fact_store_path: Path to the JSONL store.

    Returns:
        dict with status: "appended", path, fact_id
    """
    out: Dict[str, Any] = dict(fact)
    out.setdefault("record_type", "fact_assertion_v1")
    out.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    out.setdefault("authority", "extracted_from_document")
    out.setdefault("automatic_action", False)
    out.setdefault("hidden_learning", False)
    out.setdefault("raw_prompt_stored", False)

    if "fact_id" not in out:
        out["fact_id"] = f"f_{uuid.uuid4().hex[:8]}"

    path = pathlib.Path(fact_store_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(out, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return {"status": "appended", "path": str(path), "fact_id": out["fact_id"]}


# ──────────────────────────────────────────────────────────────────────────────
# Load Facts
# ──────────────────────────────────────────────────────────────────────────────

def load_facts(
    subject: Optional[str] = None,
    predicate: Optional[str] = None,
    obj: Optional[str] = None,
    project_id: Optional[str] = None,
    source_type: Optional[str] = None,
    limit: int = 100,
    fact_store_path: str = DEFAULT_FACT_STORE_PATH,
) -> List[Dict[str, Any]]:
    """Load fact assertions with optional filters.

    Args:
        subject: Match subject (normalized, substring match)
        predicate: Match predicate (normalized, substring match)
        obj: Match object (normalized, substring match)
        project_id: If set, only return facts scoped to this project
        source_type: If set, filter by source_type (e.g. "pubmed_abstract")
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

                if subject and subject not in record.get("subject", ""):
                    continue
                if predicate and predicate not in record.get("predicate", ""):
                    continue
                if obj and obj not in record.get("object", ""):
                    continue
                if project_id is not None and record.get("project_id") != project_id:
                    continue
                if source_type and record.get("source_type") != source_type:
                    continue

                results.append(record)
                if len(results) >= limit:
                    break
    except OSError:
        pass

    return results
