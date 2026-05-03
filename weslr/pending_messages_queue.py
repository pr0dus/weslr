"""
WESLR Pending Messages Queue V1

Simple file-based FIFO queue for delivering messages from background
systems (reminders, proactive daemon) to the /chat endpoint.

Usage:
  - Write: enqueue(REMINDER, message) → appends to .weslr/pending_messages.jsonl
  - Read:  dequeue_all(session_id) → returns pending messages, marks them consumed

Format:
  Each line in pending_messages.jsonl is a JSON object:
  {
    "record_type": "pending_message_v1",
    "queue_type": "reminder" | "proactive_suggestion" | "system",
    "message": str,
    "session_id": str,
    "enqueued_at": "<ISO8601>",
    "expires_at": "<ISO8601>" | null,
    "priority": "high" | "normal" | "low",
    "authority": "queue_delivery",
    "automatic_change": false,
    "raw_prompt_stored": false,
    "hidden_learning": false
  }

Consuming: reads mark consumed entries by moving them to .weslr/pending_messages_consumed.jsonl.
The file-based consume avoids lost messages on process restarts.

Authority: queue_delivery
No execution, no Ollama, no raw prompts.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────────

def _workspace() -> Path:
    return Path(os.environ.get("WESLR_WORKSPACE", "/data/data/com.termux/files/home/.openclaw/workspace"))

def _queue_path() -> Path:
    return _workspace() / ".weslr" / "pending_messages.jsonl"

def _consumed_path() -> Path:
    return _workspace() / ".weslr" / "pending_messages_consumed.jsonl"

# ── Enqueue ──────────────────────────────────────────────────────────────────

def enqueue(
    queue_type: str,
    message: str,
    session_id: str = "default",
    ttl_minutes: Optional[int] = 30,
    priority: str = "normal",
) -> str:
    """Append a pending message to the queue. Returns message_id."""
    msg_id = f"msg_{int(time.time() * 1000)}"
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=ttl_minutes)).isoformat() if ttl_minutes else None

    entry = {
        "record_type": "pending_message_v1",
        "message_id": msg_id,
        "queue_type": queue_type,
        "message": message,
        "session_id": session_id,
        "enqueued_at": now.isoformat(),
        "expires_at": expires_at,
        "priority": priority,
        "authority": "queue_delivery",
        "automatic_change": False,
        "raw_prompt_stored": False,
        "hidden_learning": False,
    }

    queue_path = _queue_path()
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with open(queue_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return msg_id


def enqueue_reminder(message: str, reminder_id: str, session_id: str = "default") -> str:
    """Convenience: enqueue a reminder firing notification."""
    return enqueue(
        queue_type="reminder",
        message=message,
        session_id=session_id,
        ttl_minutes=60,
        priority="high",
    )


def enqueue_proactive(message: str, session_id: str = "default") -> str:
    """Convenience: enqueue a proactive suggestion."""
    return enqueue(
        queue_type="proactive_suggestion",
        message=message,
        session_id=session_id,
        ttl_minutes=30,
        priority="normal",
    )


# ── Dequeue ─────────────────────────────────────────────────────────────────

def dequeue_all(session_id: str = "default") -> list[dict]:
    """Read and return all unexpired pending messages for session_id.

    Consumed entries are moved to the consumed log (not deleted).
    Returns oldest-first. Expired entries are also moved to consumed and skipped.
    """
    queue_path = _queue_path()
    if not queue_path.exists():
        return []

    consumed_path = _consumed_path()
    consumed_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    result: list[dict] = []
    consumed_lines: list[str] = []

    try:
        with open(queue_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (FileNotFoundError, PermissionError, OSError):
        return []

    for line in lines:
        try:
            entry = json.loads(line.strip())
        except json.JSONDecodeError:
            consumed_lines.append(line)
            continue

        # Skip wrong session
        if entry.get("session_id") != session_id:
            continue

        # Skip expired
        expires_at = entry.get("expires_at")
        if expires_at:
            try:
                exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if exp < now:
                    consumed_lines.append(line)
                    continue
            except ValueError:
                pass

        result.append(entry)
        consumed_lines.append(line)

    # Rewrite queue without consumed lines
    try:
        with open(queue_path, "w", encoding="utf-8") as f:
            for line in lines:
                if line not in consumed_lines:
                    f.write(line)
    except (FileNotFoundError, PermissionError, OSError):
        pass

    # Append consumed entries
    if consumed_lines:
        try:
            with open(consumed_path, "a", encoding="utf-8") as f:
                for line in consumed_lines:
                    f.write(line)
        except (FileNotFoundError, PermissionError, OSError):
            pass

    return result


def flush_queue(session_id: str = "default") -> int:
    """Discard all pending messages for session_id without delivery. Returns count."""
    queue_path = _queue_path()
    if not queue_path.exists():
        return 0

    count = 0
    remaining: list[str] = []

    try:
        with open(queue_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (FileNotFoundError, PermissionError, OSError):
        return 0

    for line in lines:
        try:
            entry = json.loads(line.strip())
            if entry.get("session_id") == session_id:
                count += 1
            else:
                remaining.append(line)
        except json.JSONDecodeError:
            remaining.append(line)

    try:
        with open(queue_path, "w", encoding="utf-8") as f:
            f.writelines(remaining)
    except (FileNotFoundError, PermissionError, OSError):
        pass

    return count


def pending_count(session_id: str = "default") -> int:
    """Return count of pending messages for session_id (without consuming)."""
    queue_path = _queue_path()
    if not queue_path.exists():
        return 0

    now = datetime.now(timezone.utc)
    count = 0

    try:
        with open(queue_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("session_id") != session_id:
                        continue
                    expires_at = entry.get("expires_at")
                    if expires_at:
                        try:
                            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                            if exp < now:
                                continue
                        except ValueError:
                            pass
                    count += 1
                except json.JSONDecodeError:
                    pass
    except (FileNotFoundError, PermissionError, OSError):
        pass

    return count


def format_queue_messages(messages: list[dict]) -> str:
    """Format a list of pending messages into a prepended chat prefix."""
    if not messages:
        return ""

    parts = []
    for msg in messages:
        qt = msg.get("queue_type", "system")
        text = msg.get("message", "")
        if qt == "reminder":
            parts.append(f"[Reminder] {text}")
        elif qt == "proactive_suggestion":
            parts.append(f"[Suggestion] {text}")
        else:
            parts.append(text)

    if len(parts) == 1:
        return parts[0]

    lines = ["--- Pending messages ---"] + parts + ["---"]
    return "\n".join(lines)


if __name__ == "__main__":
    # Demo
    import sys

    q = enqueue_reminder("Test reminder — this is the fired message", "REM-20260503-001")
    print(f"Enqueued: {q}")
    msgs = dequeue_all()
    for m in msgs:
        print(f"Dequeued: {m['message']}")
    print(f"Count after: {pending_count()}")