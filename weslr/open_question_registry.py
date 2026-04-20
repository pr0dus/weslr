"""
Weslr Open Question Registry — v1
Minimal JSON-backed storage for persisting unresolved questions.
Additive only. No autonomous inference, no auto-asking.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Storage path ──────────────────────────────────────────────────────────────

def _registry_path() -> Path:
    base = os.environ.get("WESLR_STATE_DIR", "/data/data/com.termux/files/home/.openclaw/workspace")
    return Path(base) / "weslr" / "open_question_registry.json"


# ── Schema ─────────────────────────────────────────────────────────────────────

OPEN_ITEM_SCHEMA = {
    "id": "",          # uuid
    "question": "",    # the question text
    "context": "",     # surrounding context (what triggered it)
    "state": "open",   # always "open" for this list
    "created_at": "",  # ISO timestamp
    "source": "",      # "operator" | "weslr"
    "linked_artifact_or_version": None,
}

CLOSED_ITEM_SCHEMA = {
    "id": "",
    "question": "",
    "state": "",       # "answered" | "deferred" | "pruned"
    "created_at": "",
    "closed_at": "",
    "answer_summary": "",
}


# ── Core I/O ───────────────────────────────────────────────────────────────────

def load_registry() -> Dict[str, List[Dict[str, Any]]]:
    """Load the full registry. Returns empty structure if missing or corrupt."""
    path = _registry_path()
    if not path.exists():
        return {"open": [], "closed": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Validate basic structure
        if not isinstance(data, dict):
            return {"open": [], "closed": []}
        data.setdefault("open", [])
        data.setdefault("closed", [])
        return data
    except (json.JSONDecodeError, OSError):
        return {"open": [], "closed": []}


def save_registry(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Save the full registry atomically via rename."""
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write to temp then rename for atomicity
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.rename(path)


# ── Mutations ─────────────────────────────────────────────────────────────────

def add_question(
    question: str,
    context: str = "",
    source: str = "weslr",
    linked_artifact_or_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a new open question. Returns the created item."""
    if not question or not question.strip():
        raise ValueError("question cannot be empty")
    if source not in ("operator", "weslr"):
        raise ValueError(f"source must be 'operator' or 'weslr', got {source!r}")

    item = {
        "id": str(uuid.uuid4())[:8],
        "question": question.strip(),
        "context": context.strip(),
        "state": "open",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": source,
        "linked_artifact_or_version": linked_artifact_or_version,
    }

    data = load_registry()
    data["open"].insert(0, item)  # newest first

    # Prune if over cap
    _prune_internal(data, max_open=20)

    save_registry(data)
    return item


def mark_answered(question_id: str, answer_summary: str = "") -> bool:
    """Move an open question to closed with 'answered' state. Returns True if found."""
    return _close(question_id, "answered", answer_summary)


def mark_deferred(question_id: str, reason: str = "") -> bool:
    """Move an open question to closed with 'deferred' state. Returns True if found."""
    return _close(question_id, "deferred", reason)


def _close(question_id: str, target_state: str, summary: str) -> bool:
    data = load_registry()
    for i, item in enumerate(data["open"]):
        if item["id"] == question_id:
            closed = {
                **item,
                "state": target_state,
                "closed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "answer_summary": summary,
            }
            data["open"].pop(i)
            data["closed"].insert(0, closed)
            # Bound closed history to 100 items
            if len(data["closed"]) > 100:
                data["closed"] = data["closed"][:100]
            save_registry(data)
            return True
    return False


def get_open() -> List[Dict[str, Any]]:
    """Return all open questions, newest first."""
    return load_registry().get("open", [])


def prune_stale(max_open: int = 20) -> int:
    """Prune oldest open items to bring count within max_open. Returns count pruned."""
    data = load_registry()
    before = len(data["open"])
    _prune_internal(data, max_open=max_open)
    after = len(data["open"])
    pruned = before - after
    if pruned > 0:
        save_registry(data)
    return pruned


def _prune_internal(data: Dict[str, List[Dict[str, Any]]], max_open: int) -> None:
    """Prune without saving — caller decides when to save."""
    while len(data["open"]) > max_open:
        old = data["open"].pop()
        data["closed"].insert(0, {
            **old,
            "state": "pruned",
            "closed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "answer_summary": "",
        })
    # Bound closed history
    if len(data["closed"]) > 100:
        data["closed"] = data["closed"][:100]


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "add":
        question = sys.argv[2] if len(sys.argv) > 2 else ""
        if not question:
            print("Usage: open_question_registry.py add <question> [context] [source]")
            sys.exit(1)
        context = sys.argv[3] if len(sys.argv) > 3 else ""
        source = sys.argv[4] if len(sys.argv) > 4 else "weslr"
        item = add_question(question, context, source)
        print(f"Added: {item['id']} — {item['question']}")

    elif cmd == "list":
        open_items = get_open()
        print(f"Open questions: {len(open_items)}")
        for item in open_items:
            print(f"  [{item['id']}] {item['question']} (source={item['source']}, created={item['created_at']})")
            if item.get("context"):
                print(f"           context: {item['context']}")

    elif cmd == "answer":
        qid = sys.argv[2] if len(sys.argv) > 2 else ""
        summary = sys.argv[3] if len(sys.argv) > 3 else ""
        if not qid:
            print("Usage: open_question_registry.py answer <id> [summary]")
            sys.exit(1)
        ok = mark_answered(qid, summary)
        print(f"Marked answered: {ok}")

    elif cmd == "defer":
        qid = sys.argv[2] if len(sys.argv) > 2 else ""
        reason = sys.argv[3] if len(sys.argv) > 3 else ""
        if not qid:
            print("Usage: open_question_registry.py defer <id> [reason]")
            sys.exit(1)
        ok = mark_deferred(qid, reason)
        print(f"Marked deferred: {ok}")

    elif cmd == "prune":
        max_open = int(sys.argv[2] if len(sys.argv) > 2 else 20)
        n = prune_stale(max_open)
        print(f"Pruned {n} stale items")

    elif cmd == "status":
        data = load_registry()
        print(f"Open: {len(data['open'])} | Closed: {len(data['closed'])}")

    else:
        print("Commands: add <question> [context] [source] | list | answer <id> [summary] | defer <id> [reason] | prune [max_open] | status")