"""
WESLR Document Ingestor — Phase 4.1

Pure-python document ingestion layer.
No external API calls. Uses pypdf for PDF text extraction.
Multi-tenant: file paths resolved through tenant_context.resolve_path().
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from weslr.tenant_context import resolve_path

# ─── Constants ────────────────────────────────────────────────────────────────

TRUST_BASELINES: Dict[str, float] = {
    "paper": 0.9,
    "clinical_trial": 0.95,
    "internal_note": 0.3,
    "conference_abstract": 0.4,
    "preprint": 0.5,
    "user_note": 0.2,
    "external_database": 0.85,
}

DATA_DIR = ".weslr"
DOCUMENTS_FILE = "documents.jsonl"
FACT_STORE_REL = ".weslr/fact_assertions.jsonl"


def _resolve_doc_store(doc_store_path: Optional[Path | str]) -> Path:
    """Resolve document store path: explicit override or tenant-context resolved."""
    if doc_store_path is None:
        return resolve_path(str(Path(DATA_DIR) / DOCUMENTS_FILE))
    p = Path(doc_store_path)
    if p.is_absolute():
        return p
    return resolve_path(str(p))


def _resolve_fact_store(fact_store_path: Optional[Path | str]) -> Path:
    """Resolve fact store path: explicit override or tenant-context resolved."""
    if fact_store_path is None:
        return resolve_path(FACT_STORE_REL)
    p = Path(fact_store_path)
    if p.is_absolute():
        return p
    return resolve_path(str(p))

# ─── Utility: SHA-256 file hash ───────────────────────────────────────────────

def hash_file(path: Path | str) -> str:
    """Return SHA-256 hash of a file as 'sha256:<hex>'."""
    h = hashlib.sha256()
    p = Path(path)
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def is_duplicate(file_hash: str, doc_store_path: Path | str | None = None) -> bool:
    """Return True if a document with the given hash already exists in the store."""
    if doc_store_path is None:
        doc_store_path = Path(DATA_DIR) / DOCUMENTS_FILE
    else:
        doc_store_path = Path(doc_store_path)

    if not doc_store_path.exists():
        return False

    try:
        with doc_store_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("hash") == file_hash:
                    return True
    except OSError:
        pass

    return False


# ─── PDF text extraction ──────────────────────────────────────────────────────

def extract_text_from_pdf(path: Path | str) -> Tuple[str, List[Dict[str, Any]]]:
    """Extract text from a PDF.

    Returns:
        full_text: concatenated page texts separated by '\\f' (form feed)
        page_metadata: list of dicts with {page_num, text, line_count, char_count}
    """
    import pypdf

    p = Path(path)
    page_metadata: List[Dict[str, Any]] = []
    full_parts: List[str] = []

    try:
        reader = pypdf.PdfReader(str(p))
    except Exception as e:
        raise RuntimeError(f"Failed to open PDF '{p}': {e}") from e

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            pass  # try without password; if still fails, read anyway

    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from page {i} of '{p}': {e}") from e

        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [ln for ln in text.split("\n") if ln.strip()]
        line_count = len(lines)
        char_count = len(text)

        page_metadata.append({
            "page_num": i,
            "text": text,
            "line_count": line_count,
            "char_count": char_count,
        })
        full_parts.append(text)

    full_text = "\f".join(full_parts)
    return full_text, page_metadata


# ─── TXT text extraction ───────────────────────────────────────────────────────

def extract_text_from_txt(path: Path | str) -> Tuple[str, List[Dict[str, Any]]]:
    """Extract text from a plain-text file.

    Returns:
        full_text: the complete file content
        metadata: single-entry list with {page_num=1, text, line_count, char_count}
    """
    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = p.read_text(encoding="latin-1")
    except Exception as e:
        raise RuntimeError(f"Failed to read text file '{p}': {e}") from e

    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln for ln in text.split("\n") if ln.strip()]
    line_count = len(lines)
    char_count = len(text)

    metadata = [{
        "page_num": 1,
        "text": text,
        "line_count": line_count,
        "char_count": char_count,
    }]
    return text, metadata


# ─── Section segmentation ─────────────────────────────────────────────────────

_SECTION_PATTERNS = [
    (re.compile(r"^\s*abstract\s*$", re.IGNORECASE), "abstract"),
    (re.compile(r"^\s*methods?\s*$", re.IGNORECASE), "methods"),
    (re.compile(r"^\s*results?\s*$", re.IGNORECASE), "results"),
    (re.compile(r"^\s*conclusion\s*$", re.IGNORECASE), "conclusion"),
    (re.compile(r"^\s*discussion\s*$", re.IGNORECASE), "discussion"),
]


def segment_sections(text: str, page_map: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Split document text into named sections.

    Args:
        text: full concatenated document text
        page_map: page metadata list from extract_text_from_pdf / extract_text_from_txt

    Returns:
        list of dicts with {section, text, page}
        Sections with no matched header fall under "default" until a header is seen.
    """
    if not text:
        return []

    all_lines = text.split("\n")
    sections: List[Dict[str, Any]] = []
    current_section = "default"
    current_lines: List[str] = []

    for line in all_lines:
        matched = False
        for pattern, name in _SECTION_PATTERNS:
            if pattern.match(line):
                if current_lines or current_section != "default":
                    sections.append({
                        "section": current_section,
                        "text": "\n".join(current_lines).strip(),
                        "page": _find_page_for_offset(text, "\n".join(current_lines[:1])),
                    })
                current_section = name
                current_lines = []
                matched = True
                break
        if not matched:
            current_lines.append(line)

    if current_lines or current_section != "default":
        sections.append({
            "section": current_section,
            "text": "\n".join(current_lines).strip(),
            "page": _find_page_for_offset(text, "\n".join(current_lines[:1])),
        })

    return sections


def _find_page_for_offset(full_text: str, snippet: str) -> int:
    """Guess which page a snippet starts in based on page_map char offsets."""
    if not snippet:
        return 1
    pos = full_text.find(snippet)
    if pos == -1:
        return 1
    return _char_offset_to_page(full_text, pos)


def _char_offset_to_page(full_text: str, char_offset: int) -> int:
    """Map a character offset to a 1-based page number using form-feed markers."""
    page = 1
    ff = "\f"
    idx = 0
    while idx < char_offset:
        idx = full_text.find(ff, idx)
        if idx == -1 or idx >= char_offset:
            break
        page += 1
        idx += 1
    return page


# ─── Fact extraction helpers ──────────────────────────────────────────────────

def extract_facts_with_positions(
    text: str,
    pattern_confidence: float = 0.8,
) -> List[Dict[str, Any]]:
    """Extract subject-predicate-object triples from arbitrary text with positions.

    Uses the same 10 deterministic regex patterns as fact_extractor.py
    but returns enriched dicts with character offsets.

    Args:
        text: text to extract from
        pattern_confidence: base confidence for all extracted facts

    Returns:
        list of dicts with {subject, predicate, object, char_start, char_end, pattern_confidence}
    """
    if not text or not isinstance(text, str):
        return []

    facts: List[Dict[str, Any]] = []

    # Pattern 1: "X discussed Y"
    for m in re.finditer(r"\b(.+?)\s+discussed\s+(.+)", text, re.IGNORECASE):
        facts.append(_make_fact(m, "discussed", text, pattern_confidence))

    # Pattern 2: "X said Y about Z"
    for m in re.finditer(r"\b(.+?)\s+said\s+(.+?)\s+about\s+(.+)", text, re.IGNORECASE):
        facts.append({
            "subject": _normalize_entity(m.group(1)),
            "predicate": _normalize_entity("said_about"),
            "object": _normalize_entity(m.group(3)),
            "char_start": m.start(),
            "char_end": m.end(),
            "pattern_confidence": pattern_confidence,
        })

    # Pattern 3: "X worked on Y"
    for m in re.finditer(r"\b(.+?)\s+worked\s+on\s+(.+)", text, re.IGNORECASE):
        facts.append(_make_fact(m, "worked_on", text, pattern_confidence))

    # Pattern 4: "X is important for Y"  →  (Y, has_importance, X)
    for m in re.finditer(r"\b(.+?)\s+is\s+important\s+for\s+(.+)", text, re.IGNORECASE):
        facts.append({
            "subject": _normalize_entity(m.group(2)),
            "predicate": _normalize_entity("has_importance"),
            "object": _normalize_entity(m.group(1)),
            "char_start": m.start(),
            "char_end": m.end(),
            "pattern_confidence": pattern_confidence,
        })

    # Pattern 5: "X depends on Y"
    for m in re.finditer(r"\b(.+?)\s+depends\s+on\s+(.+)", text, re.IGNORECASE):
        facts.append(_make_fact(m, "depends_on", text, pattern_confidence))

    # Pattern 6: "X is part of Y"
    for m in re.finditer(r"\b(.+?)\s+is\s+part\s+of\s+(.+)", text, re.IGNORECASE):
        facts.append(_make_fact(m, "part_of", text, pattern_confidence))

    # Pattern 7: "X uses Y"
    for m in re.finditer(r"\b(.+?)\s+uses\s+(.+)", text, re.IGNORECASE):
        facts.append(_make_fact(m, "uses", text, pattern_confidence))

    # Pattern 8: "X created Y"
    for m in re.finditer(r"\b(.+?)\s+created\s+(.+)", text, re.IGNORECASE):
        facts.append(_make_fact(m, "created", text, pattern_confidence))

    # Pattern 9: "X tested Y"
    for m in re.finditer(r"\b(.+?)\s+tested\s+(.+)", text, re.IGNORECASE):
        facts.append(_make_fact(m, "tested", text, pattern_confidence))

    # Pattern 10: "X upgraded Y"
    for m in re.finditer(r"\b(.+?)\s+upgraded\s+(.+)", text, re.IGNORECASE):
        facts.append(_make_fact(m, "upgraded", text, pattern_confidence))

    return facts


def _make_fact(
    match: re.Match[str],
    predicate: str,
    text: str,
    pattern_confidence: float,
) -> Dict[str, Any]:
    """Build a fact dict from a regex match."""
    return {
        "subject": _normalize_entity(match.group(1)),
        "predicate": _normalize_entity(predicate),
        "object": _normalize_entity(match.group(2)),
        "char_start": match.start(),
        "char_end": match.end(),
        "pattern_confidence": pattern_confidence,
    }


def _normalize_entity(text: str) -> str:
    """Normalize a string into a stable entity reference."""
    if not text:
        return "unknown"
    normalized = text.lower().strip()
    normalized = re.sub(r"[-:_.\s]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "unknown"


def _line_range_for_offset(text: str, char_start: int, char_end: int) -> Tuple[int, int]:
    """Map a character range to 1-based (start_line, end_line)."""
    before = text[:char_start]
    start_line = before.count("\n") + 1
    end_line = text[:char_end].count("\n") + 1
    return start_line, end_line


# ─── Main ingest function ──────────────────────────────────────────────────────

def ingest_document(
    file_path: Path | str,
    source_type: str,
    domain: str,
    trust_baseline: Optional[float] = None,
    doc_store_path: Optional[Path | str] = None,
    fact_store_path: Optional[Path | str] = None,
) -> Dict[str, Any]:
    """Ingest a document into the Weslr store.

    Steps:
      1. Hash file with hash_file()
      2. Check is_duplicate(); skip if true
      3. Extract text (pdf or txt based on extension)
      4. Segment sections
      5. Write document record to documents.jsonl
      6. Extract facts per page with extract_facts_with_positions()
      7. Enrich facts with source metadata + trust score
      8. Append enriched facts to fact_assertions.jsonl
      9. Return summary dict

    Args:
        file_path: path to the document file
        source_type: one of the keys in TRUST_BASELINES
        domain: arbitrary domain string (e.g. "cardiology", "manufacturing")
        trust_baseline: override trust baseline; if None, looked up from TRUST_BASELINES
        doc_store_path: path to documents.jsonl; defaults to DATA_DIR/DOCUMENTS_FILE
        fact_store_path: path to fact_assertions.jsonl; defaults to FACT_STORE_PATH

    Returns:
        dict with keys: doc_id, filename, hash, duplicate_status, page_count,
                        section_count, fact_count, trust_score
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Document not found: {p}")

    # Resolve stores
    doc_store_path = _resolve_doc_store(doc_store_path)
    fact_store_path = _resolve_fact_store(fact_store_path)

    # Ensure directories exist
    doc_store_path.parent.mkdir(parents=True, exist_ok=True)
    fact_store_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Hash
    file_hash = hash_file(p)

    # 2. Duplicate check
    if is_duplicate(file_hash, doc_store_path):
        return {
            "doc_id": None,
            "filename": p.name,
            "hash": file_hash,
            "duplicate_status": True,
            "page_count": 0,
            "section_count": 0,
            "fact_count": 0,
            "trust_score": 0.0,
        }

    # 3. Extract text
    ext = p.suffix.lower()
    if ext == ".pdf":
        full_text, page_metadata = extract_text_from_pdf(p)
    elif ext in (".txt", ".text"):
        full_text, page_metadata = extract_text_from_txt(p)
    else:
        raise ValueError(f"Unsupported file extension: {ext} — expected .pdf or .txt")

    page_count = len(page_metadata)

    # 4. Segment sections
    sections = segment_sections(full_text, page_metadata)

    # 5. Build document record
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    trust = trust_baseline if trust_baseline is not None else TRUST_BASELINES.get(source_type, 0.5)

    # Extract abstract: first section named "abstract", else first 200 chars of text
    abstract_section = next((s for s in sections if s["section"] == "abstract"), None)
    if abstract_section:
        abstract = abstract_section["text"][:500]
    else:
        abstract = full_text[:200].strip()

    record = {
        "doc_id": doc_id,
        "filename": p.name,
        "hash": file_hash,
        "upload_date": datetime.now(timezone.utc).isoformat(),
        "source_type": source_type,
        "domain": domain,
        "trust_baseline": trust,
        "page_count": page_count,
        "abstract": abstract,
        "ingest_method": "pypdf" if ext == ".pdf" else "textfile",
        "store_text": False,
    }

    doc_store_path.parent.mkdir(parents=True, exist_ok=True)
    with doc_store_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # 6–8. Extract and enrich facts per page
    total_facts = 0
    with fact_store_path.open("a", encoding="utf-8") as fact_f:
        for page in page_metadata:
            page_text = page["text"]
            page_num = page["page_num"]

            raw_facts = extract_facts_with_positions(page_text, pattern_confidence=0.8)

            for fact in raw_facts:
                start_line, end_line = _line_range_for_offset(
                    page_text, fact["char_start"], fact["char_end"]
                )

                enriched = {
                    "record_type": "fact_assertion_v1",
                    "subject": fact["subject"],
                    "predicate": fact["predicate"],
                    "object": fact["object"],
                    "source_doc_id": doc_id,
                    "source_reference": {
                        "page": page_num,
                        "line_range": [start_line, end_line],
                    },
                    "source_type": source_type,
                    "domain": domain,
                    "trust_score": trust * fact["pattern_confidence"],
                    "char_start": fact["char_start"],
                    "char_end": fact["char_end"],
                    "pattern_confidence": fact["pattern_confidence"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "authority": "extracted_from_document",
                    "automatic_action": False,
                    "hidden_learning": False,
                    "raw_prompt_stored": False,
                }
                fact_f.write(json.dumps(enriched, ensure_ascii=False) + "\n")
                total_facts += 1

    # 9. Summary
    return {
        "doc_id": doc_id,
        "filename": p.name,
        "hash": file_hash,
        "duplicate_status": False,
        "page_count": page_count,
        "section_count": len(sections),
        "fact_count": total_facts,
        "trust_score": trust,
    }
