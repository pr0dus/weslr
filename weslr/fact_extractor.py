"""
WESLR Fact Extractor V1 — Multi-Tenant

Deterministic extraction of subject-predicate-object triples from session summary text.
Uses 10 high-precision pattern rules for generic extraction, plus domain-specific
pattern files for clinical trial and research document extraction.

Authority: extracted_from_timeline / extracted_from_document
No raw prompts stored. No hidden learning. No automatic execution.

Multi-tenant: all file paths are resolved through tenant_context.
When no tenant is active, falls back to workspace-root paths (backward compatible).
"""

from __future__ import annotations

import json
import pathlib
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from weslr.tenant_context import (
    get_current_tenant,
    is_default_tenant,
    resolve_path,
)

# Legacy constant — kept for source compatibility
DEFAULT_FACT_STORE_PATH = ".weslr/fact_assertions.jsonl"


# ──────────────────────────────────────────────────────────────────────────────
# Fallback Generic Patterns (10 original session-summary patterns)
# ──────────────────────────────────────────────────────────────────────────────

# Used by extract_triples_from_summary() — the original session-summary extractor.
# Each entry: (pattern_id, regex_string, predicate_template)
_FALLBACK_PATTERNS: List[tuple[str, str, str]] = [
    ("generic.discussed",      r"^(.+?)\s+discussed\s+(.+)$",                       "discussed"),
    ("generic.said_about",    r"^(.+?)\s+said\s+(.+?)\s+about\s+(.+)$",              "said_about"),
    ("generic.worked_on",     r"^(.+?)\s+worked\s+on\s+(.+)$",                        "worked_on"),
    ("generic.has_importance",r"^(.+?)\s+is\s+important\s+for\s+(.+)$",              "has_importance"),
    ("generic.depends_on",    r"^(.+?)\s+depends\s+on\s+(.+)$",                       "depends_on"),
    ("generic.part_of",       r"^(.+?)\s+is\s+part\s+of\s+(.+)$",                    "part_of"),
    ("generic.uses",          r"^(.+?)\s+uses\s+(.+)$",                               "uses"),
    ("generic.created",       r"^(.+?)\s+created\s+(.+)$",                            "created"),
    ("generic.tested",        r"^(.+?)\s+tested\s+(.+)$",                             "tested"),
    ("generic.upgraded",      r"^(.+?)\s+upgraded\s+(.+)$",                            "upgraded"),
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
        {"pattern_id": "generic.discussed",    "regex": r"^(.+?)\s+discussed\s+(.+)$",                  "confidence": 0.8, "groups": {"subject": 1, "object": 2}},
        {"pattern_id": "generic.said_about",   "regex": r"^(.+?)\s+said\s+(.+?)\s+about\s+(.+)$",       "confidence": 0.8, "groups": {"subject": 1, "object": 3}},
        {"pattern_id": "generic.worked_on",    "regex": r"^(.+?)\s+worked\s+on\s+(.+)$",               "confidence": 0.8, "groups": {"subject": 1, "object": 2}},
        {"pattern_id": "generic.has_importance","regex": r"^(.+?)\s+is\s+important\s+for\s+(.+)$",      "confidence": 0.8, "groups": {"subject": 1, "object": 2}},
        {"pattern_id": "generic.depends_on",   "regex": r"^(.+?)\s+depends\s+on\s+(.+)$",              "confidence": 0.8, "groups": {"subject": 1, "object": 2}},
        {"pattern_id": "generic.part_of",      "regex": r"^(.+?)\s+is\s+part\s+of\s+(.+)$",           "confidence": 0.8, "groups": {"subject": 1, "object": 2}},
        {"pattern_id": "generic.uses",         "regex": r"^(.+?)\s+uses\s+(.+)$",                       "confidence": 0.8, "groups": {"subject": 1, "object": 2}},
        {"pattern_id": "generic.created",      "regex": r"^(.+?)\s+created\s+(.+)$",                  "confidence": 0.8, "groups": {"subject": 1, "object": 2}},
        {"pattern_id": "generic.tested",       "regex": r"^(.+?)\s+tested\s+(.+)$",                    "confidence": 0.8, "groups": {"subject": 1, "object": 2}},
        {"pattern_id": "generic.upgraded",     "regex": r"^(.+?)\s+upgraded\s+(.+)$",                  "confidence": 0.8, "groups": {"subject": 1, "object": 2}},
    ]


def load_patterns(domain: str = "cancer_research") -> List[Dict[str, Any]]:
    """Load extraction patterns for the given domain.

    Loads from weslr/fact_patterns/<domain>.json (workspace-level, shared).
    Falls back to generic patterns if file not found.
    Caches after first load per domain.
    """
    if domain in _DOMAIN_PATTERN_CACHE:
        return _DOMAIN_PATTERN_CACHE[domain]

    pattern_file = pathlib.Path(__file__).parent / "fact_patterns" / f"{domain}.json"
    if not pattern_file.exists():
        patterns = _get_fallback_patterns()
    else:
        with open(pattern_file, encoding="utf-8") as f:
            data = json.load(f)
        patterns = data.get("patterns", [])

    _DOMAIN_PATTERN_CACHE[domain] = patterns
    return patterns


# ──────────────────────────────────────────────────────────────────────────────
# Path Resolution Helper
# ──────────────────────────────────────────────────────────────────────────────

def _resolve_fact_store_path(path: Optional[str], tenant_id: Optional[str]) -> pathlib.Path:
    """Resolve a fact store path for the given tenant.

    If path is explicitly provided, treat it as tenant-relative.
    If not provided, use the default tenant-aware path.
    """
    if path:
        return resolve_path(path, tenant_id)
    # Default path resolves through tenant_context
    return resolve_path(DEFAULT_FACT_STORE_PATH, tenant_id)


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
    return normalized or "unknown"


def _make_triple(subject: str, predicate: str, obj: str) -> Dict[str, str]:
    return {"subject": _normalize_entity(subject), "predicate": _normalize_entity(predicate), "object": _normalize_entity(obj)}


def extract_triples_from_summary(
    summary_text: str,
    default_subject: str = "user",
) -> List[Dict[str, str]]:
    """Extract structured triples from a session summary string.

    Uses the 10 deterministic generic patterns. Each match produces one triple.
    """
    if not summary_text or not isinstance(summary_text, str):
        return []

    triples: List[Dict[str, str]] = []
    for pid, pat_re, pred in _FALLBACK_PATTERNS:
        m = re.match(pat_re, summary_text.strip(), re.IGNORECASE)
        if m:
            subj = m.group(1).strip()
            triples.append(_make_triple(
                subj if subj.lower() != "we" else default_subject, pred, m.group(2).strip()
            ))
            return triples
    return []


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

    Returns enriched fact dicts with character offsets and structured data.
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
        groups_map = pat.get("groups", {})

        try:
            compiled = re.compile(pat_regex, re.IGNORECASE)
        except re.PatternError:
            continue

        for m in compiled.finditer(text):
            fact_data: Dict[str, Any] = {}
            for field_name, group_idx in groups_map.items():
                try:
                    val = m.group(group_idx)
                    if val is not None:
                        fact_data[field_name] = val.strip()
                except (IndexError, TypeError):
                    pass

            cs, ce = m.start(), m.end()
            ls = text[:cs].count("\n") + line_start
            le = text[:ce].count("\n") + line_start

            predicate_normalized = _normalize_entity(pat.get("predicate", pat_id.replace(".", "_")))

            first_field = list(groups_map.keys())[0] if groups_map else None
            subj_raw = fact_data.get(first_field, domain) if first_field else domain
            subject_normalized = _normalize_entity(subj_raw)

            second_field = list(groups_map.keys())[1] if len(groups_map) > 1 else None
            obj_raw = fact_data.get(second_field, m.group(0)[:50]) if second_field else m.group(0)[:50]
            object_normalized = _normalize_entity(obj_raw)

            facts.append({
                "pattern_id": pat_id, "subject": subject_normalized,
                "predicate": predicate_normalized, "object": object_normalized,
                "fact_data": fact_data, "confidence": confidence,
                "char_start": cs, "char_end": ce, "line_start": ls, "line_end": le,
                "page": page,
            })

    return facts


# ──────────────────────────────────────────────────────────────────────────────
# Append Fact Assertion (enriched — for domain extractions, multi-tenant)
# ──────────────────────────────────────────────────────────────────────────────

def append_fact_assertion(
    triple: Dict[str, str],
    source_event_ref: str,
    tenant_id: Optional[str] = None,
    fact_store_path: Optional[str] = None,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a fact triple as a JSONL record.

    Path resolved via tenant_context (or workspace root if no tenant).
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

    path = _resolve_fact_store_path(fact_store_path, tenant_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(event, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return {"event": event, "path": str(path), "status": "appended"}


def append_enriched_fact(
    fact: Dict[str, Any],
    tenant_id: Optional[str] = None,
    fact_store_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Append an enriched fact (from domain extraction) to fact_assertions.jsonl.

    Multi-tenant aware: path resolved through tenant_context.
    """
    out = dict(fact)
    out.setdefault("record_type", "fact_assertion_v1")
    out.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    out.setdefault("authority", "extracted_from_document")
    out.setdefault("automatic_action", False)
    out.setdefault("hidden_learning", False)
    out.setdefault("raw_prompt_stored", False)
    if "fact_id" not in out:
        out["fact_id"] = f"f_{uuid.uuid4().hex[:8]}"

    path = _resolve_fact_store_path(fact_store_path, tenant_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(out, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return {"status": "appended", "path": str(path), "fact_id": out["fact_id"]}


# ──────────────────────────────────────────────────────────────────────────────
# Load Facts (multi-tenant)
# ──────────────────────────────────────────────────────────────────────────────

def load_facts(
    subject: Optional[str] = None,
    predicate: Optional[str] = None,
    obj: Optional[str] = None,
    project_id: Optional[str] = None,
    source_type: Optional[str] = None,
    limit: int = 100,
    tenant_id: Optional[str] = None,
    fact_store_path: Optional[str] = None,
    after_year: Optional[int] = None,
    before_year: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Load fact assertions with optional filters.

    Multi-tenant aware: paths resolved through tenant_context.

    Args:
        after_year: Only include facts with publication_year >= this value.
        before_year: Only include facts with publication_year <= this value.
    """
    path = _resolve_fact_store_path(fact_store_path, tenant_id)
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
                if after_year is not None:
                    pub_year = record.get("publication_year") or record.get("year", 0)
                    try:
                        if int(pub_year) < after_year:
                            continue
                    except (TypeError, ValueError):
                        pass  # no year available, include it
                if before_year is not None:
                    pub_year = record.get("publication_year") or record.get("year", 9999)
                    try:
                        if int(pub_year) > before_year:
                            continue
                    except (TypeError, ValueError):
                        pass  # no year available, include it

                results.append(record)
                if len(results) >= limit:
                    break
    except OSError:
        pass

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Fact Deduplication & Merging (for cross-source deduplication)
# ──────────────────────────────────────────────────────────────────────────────

def find_duplicate_fact(
    new_fact: Dict[str, Any],
    tenant_id: Optional[str] = None,
    fact_store_path: Optional[str] = None,
    match_window: int = 50,
) -> Optional[Dict[str, Any]]:
    """Check if a fact with the same subject/predicate/object already exists.

    Returns the existing fact dict if found, else None.
    Uses normalized forms for comparison.
    """
    sub = _normalize_entity(new_fact.get("subject", ""))
    pred = _normalize_entity(new_fact.get("predicate", ""))
    obj = _normalize_entity(new_fact.get("object", ""))

    existing = load_facts(
        subject=sub, predicate=pred, obj=obj,
        limit=match_window, tenant_id=tenant_id, fact_store_path=fact_store_path
    )
    for candidate in existing:
        if (_normalize_entity(candidate.get("subject", "")) == sub
                and _normalize_entity(candidate.get("predicate", "")) == pred
                and _normalize_entity(candidate.get("object", "")) == obj):
            return candidate
    return None


def merge_duplicate_facts(
    existing: Dict[str, Any],
    new_fact: Dict[str, Any],
    tenant_id: Optional[str] = None,
    fact_store_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Merge a new fact into an existing one via trust score averaging.

    Updates the trust_score as weighted average: existing 70%, new 30%.
    Appends new source_reference to existing's source_references list.
    Does not rewrite existing record; returns merged dict for callers to log.
    """
    old_trust = existing.get("trust_score", 0.5)
    new_trust = new_fact.get("trust_score", 0.5)
    merged_trust = old_trust * 0.7 + new_trust * 0.3

    merged = dict(existing)
    merged["trust_score"] = round(merged_trust, 3)
    merged["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Collect source references
    sources: List[Dict[str, Any]] = []
    for src in existing.get("source_references", []):
        sources.append(src)
    if new_fact.get("source_reference"):
        sources.append(new_fact["source_reference"])
    if sources:
        merged["source_references"] = sources

    return merged


# ──────────────────────────────────────────────────────────────────────────────
# Numeric Range Validation
# ──────────────────────────────────────────────────────────────────────────────

# Predicate → (min, max, inclusive) tuples for validation
_NUMERIC_RANGES: Dict[str, tuple[float, float]] = {
    "survival_rate": (0.0, 1.0),
    "overall_survival": (0.0, 1.0),
    "response_rate": (0.0, 1.0),
    "p_value": (0.0, 1.0),
    "hazard_ratio": (0.0, 10.0),
    "objective_response_rate": (0.0, 1.0),
    "disease_control_rate": (0.0, 1.0),
    "enrollment": (1.0, 100000.0),
    "age": (0.0, 120.0),
}


def validate_numeric_fact(fact: Dict[str, Any]) -> Dict[str, Any]:
    """Check if a fact's object or fact_data numeric fields are within valid ranges.

    Adds validation.is_valid and validation.out_of_range fields.
    """
    pred = fact.get("predicate", "")
    obj_str = fact.get("object", "")
    result = dict(fact)
    result["validation"] = {"is_valid": True, "out_of_range": []}

    if pred in _NUMERIC_RANGES:
        lo, hi = _NUMERIC_RANGES[pred]
        try:
            val = float(obj_str)
            if not (lo <= val <= hi):
                result["validation"]["is_valid"] = False
                result["validation"]["out_of_range"].append({"field": "object", "value": val, "min": lo, "max": hi})
        except (ValueError, TypeError):
            pass

    # Also check fact_data numerics
    fact_data = fact.get("fact_data", {})
    for fk, fv in fact_data.items():
        key = f"{pred}.{fk}"
        if key in _NUMERIC_RANGES:
            lo, hi = _NUMERIC_RANGES[key]
            try:
                val = float(fv)
                if not (lo <= val <= hi):
                    result["validation"]["is_valid"] = False
                    result["validation"]["out_of_range"].append({"field": fk, "value": val, "min": lo, "max": hi})
            except (ValueError, TypeError):
                pass

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Negation Detection
# ──────────────────────────────────────────────────────────────────────────────

_NEGATION_PATTERNS = re.compile(
    r"\b(no|not|without|absence|declined|negative|ruled out|excluded|absent|never)\b",
    re.IGNORECASE
)


def check_negation(text: str, match_start: int, match_end: int) -> bool:
    """Return True if a negation word appears within 50 chars before the match.

    Scans text[max(0, match_start-50):match_start] for negation words.
    """
    prefix = text[max(0, match_start - 50):match_start]
    return bool(_NEGATION_PATTERNS.search(prefix))


def apply_negation(fact: Dict[str, Any]) -> Dict[str, Any]:
    """Mark a fact as negated and reduce trust score.

    Adds is_negated=True and reduces trust_score to 0.1 (unless already lower).
    """
    out = dict(fact)
    out["is_negated"] = True
    out["trust_score"] = min(out.get("trust_score", 1.0), 0.1)
    return out
