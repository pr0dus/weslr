"""
WESLR Reminder Handler V1

Self-contained in-process reminder scheduler using threading.Timer.
Stores reminders in .weslr/reminders.jsonl (append-only).
Fires into the pending_messages_queue for /chat delivery.

Pattern:
  1. "remind me in N minutes to <message>" → calculate due_at, store, schedule Timer
  2. "remind me at HH:MM to <message>" → store, schedule Timer if not yet past
  3. "show my reminders" → list pending from JSONL
  4. "cancel reminder <id>" → update status, cancel Timer

Polling fallback: a background thread wakes every 60s to catch
missed reminders after process restarts.

Authority: reminder_system
No Ollama, no execution, no raw prompts stored (only the reminder message itself).
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────────

def _workspace() -> Path:
    return Path(os.environ.get("WESLR_WORKSPACE", "/data/data/com.termux/files/home/.openclaw/workspace"))

def _reminder_path() -> Path:
    return _workspace() / ".weslr" / "reminders.jsonl"

def _reminder_log_path() -> Path:
    return _workspace() / ".weslr" / "reminder_events.jsonl"

# ── Dataclass ─────────────────────────────────────────────────────────────────

@dataclass
class Reminder:
    reminder_id: str
    created_at: str
    due_at: str
    message: str
    status: str  # pending | fired | cancelled | failed
    session_id: str
    authority: str = "reminder_system"
    automatic_change: bool = False
    hidden_learning: bool = False
    raw_prompt_stored: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Reminder":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

# ── Timer registry ─────────────────────────────────────────────────────────

# Maps reminder_id → threading.Timer (for cancel)
_ACTIVE_TIMERS: dict[str, threading.Timer] = {}
_TIMER_LOCK = threading.Lock()

# ── ID generation ─────────────────────────────────────────────────────────────

def _generate_id() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = _reminder_path()
    idx = 1
    if path.exists():
        try:
            with open(path) as f:
                for line in f:
                    try:
                        e = json.loads(line.strip())
                        rid = e.get("reminder_id", "")
                        if rid.startswith(f"REM-{today}"):
                            n = int(rid.split("-")[-1])
                            if n >= idx:
                                idx = n + 1
                    except (json.JSONDecodeError, ValueError, IndexError):
                        pass
        except Exception:
            pass
    return f"REM-{today}-{idx:03d}"

# ── Persistence ───────────────────────────────────────────────────────────────

def _append_reminder(reminder: Reminder) -> None:
    path = _reminder_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(reminder.to_dict(), ensure_ascii=False) + "\n")


def _append_event(event_type: str, reminder_id: str, **extra) -> None:
    path = _reminder_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "record_type": f"reminder_{event_type}_v1",
        "reminder_id": reminder_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _load_pending() -> list[Reminder]:
    """Load all pending reminders from file."""
    path = _reminder_path()
    if not path.exists():
        return []
    pending = []
    try:
        with open(path) as f:
            for line in f:
                try:
                    r = Reminder.from_dict(json.loads(line.strip()))
                    if r.status == "pending":
                        pending.append(r)
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
    except Exception:
        pass
    return pending


def _update_status(reminder_id: str, new_status: str) -> bool:
    """Update status of a reminder in file. Returns True if found."""
    path = _reminder_path()
    if not path.exists():
        return False
    updated = []
    found = False
    try:
        with open(path) as f:
            for line in f:
                try:
                    r = json.loads(line.strip())
                    if r.get("reminder_id") == reminder_id:
                        r["status"] = new_status
                        found = True
                    updated.append(r)
                except json.JSONDecodeError:
                    updated.append(json.loads(line))
    except Exception:
        return False

    try:
        with open(path, "w") as f:
            for r in updated:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except Exception:
        return False

    return found


def _cancel_timer(reminder_id: str) -> None:
    with _TIMER_LOCK:
        timer = _ACTIVE_TIMERS.pop(reminder_id, None)
        if timer:
            timer.cancel()

# ── Timer firing ─────────────────────────────────────────────────────────────

def _fire_reminder(reminder_id: str, message: str, session_id: str) -> None:
    """Called when a timer fires. Log, enqueue to pending_messages, mark fired."""
    # Log the firing event
    _append_event("fired", reminder_id, message=message, session_id=session_id)

    # Mark as fired in storage
    _update_status(reminder_id, "fired")

    # Enqueue for /chat delivery
    try:
        from weslr.pending_messages_queue import enqueue_reminder
        enqueue_reminder(
            message=message,
            reminder_id=reminder_id,
            session_id=session_id,
        )
    except Exception:
        # Enqueue failure should not crash — still mark fired
        pass

    # Remove timer from registry
    with _TIMER_LOCK:
        _ACTIVE_TIMERS.pop(reminder_id, None)


# ── Scheduling ───────────────────────────────────────────────────────────────

def schedule_reminder(reminder: Reminder) -> None:
    """Schedule a threading.Timer for a pending reminder."""
    try:
        due = datetime.fromisoformat(reminder.due_at.replace("Z", "+00:00"))
    except ValueError:
        due = datetime.fromisoformat(reminder.due_at)
    now = datetime.now(timezone.utc)
    delta = (due - now).total_seconds()

    if delta <= 0:
        # Already due — fire immediately in a background thread
        t = threading.Thread(
            target=_fire_reminder,
            args=(reminder.reminder_id, reminder.message, reminder.session_id),
            daemon=True,
        )
        t.start()
        return

    def timer_callback(rid=reminder.reminder_id, msg=reminder.message, sid=reminder.session_id):
        _fire_reminder(rid, msg, sid)

    with _TIMER_LOCK:
        _ACTIVE_TIMERS[reminder.reminder_id] = threading.Timer(delta, timer_callback)
        _ACTIVE_TIMERS[reminder.reminder_id].daemon = True
        _ACTIVE_TIMERS[reminder.reminder_id].start()


# ── Parse user input ─────────────────────────────────────────────────────────

def parse_reminder_request(message: str) -> Optional[dict]:
    """Parse 'remind me in N minutes to <msg>' or 'remind me at HH:MM to <msg>'.

    Returns dict with keys: {type: "relative"|"absolute", due_at, message}
    or None if the message doesn't match either pattern.
    """
    text = message.strip()

    # "in N minutes to <msg>"
    m = re.match(
        r"^remind\s+me\s+in\s+(\d+)\s+(minutes?|mins?|hours?|hrs?)\s+to\s+(.{1,500})$",
        text,
        re.IGNORECASE,
    )
    if m:
        count, unit, reminder_text = m.groups()
        count = int(count)
        unit = unit.lower()
        if unit.startswith("hour"):
            delta = timedelta(hours=count)
        else:
            delta = timedelta(minutes=count)
        due = datetime.now(timezone.utc) + delta
        return {
            "type": "relative",
            "due_at": due.isoformat(),
            "message": reminder_text.strip(),
        }

    # "at HH:MM to <msg>" (24h, today assumed)
    m = re.match(
        r"^remind\s+me\s+at\s+(\d{1,2}:\d{2})\s+to\s+(.{1,500})$",
        text,
        re.IGNORECASE,
    )
    if m:
        time_str, reminder_text = m.groups()
        parts = time_str.split(":")
        hour, minute = int(parts[0]), int(parts[1])
        now = datetime.now(timezone.utc)
        due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        # If the time has already passed today, assume tomorrow
        if due <= now:
            due += timedelta(days=1)
        return {
            "type": "absolute",
            "due_at": due.isoformat(),
            "message": reminder_text.strip(),
        }

    return None


# ── Public API ───────────────────────────────────────────────────────────────

def set_reminder(
    message: str,
    due_at: str,
    session_id: str = "default",
    user_id: str = "arthur",
) -> dict:
    """Store and schedule a reminder. Returns dict with reminder details."""
    reminder_id = _generate_id()
    created_at = datetime.now(timezone.utc).isoformat()

    reminder = Reminder(
        reminder_id=reminder_id,
        created_at=created_at,
        due_at=due_at,
        message=message,
        status="pending",
        session_id=session_id,
    )

    _append_reminder(reminder)
    _append_event("created", reminder_id, message=message, due_at=due_at, session_id=session_id)
    schedule_reminder(reminder)

    return {
        "reminder_id": reminder_id,
        "created_at": created_at,
        "due_at": due_at,
        "message": message,
        "status": "pending",
        "authority": "reminder_system",
        "automatic_change": False,
        "raw_prompt_stored": False,
        "hidden_learning": False,
    }


def list_reminders(session_id: str = "default") -> list[dict]:
    """List all pending reminders for session_id."""
    pending = _load_pending()
    return [
        {
            "reminder_id": r.reminder_id,
            "created_at": r.created_at,
            "due_at": r.due_at,
            "message": r.message,
            "status": r.status,
        }
        for r in pending
        if r.session_id == session_id
    ]


def cancel_reminder(reminder_id: str) -> dict:
    """Cancel a pending reminder. Returns success dict."""
    _cancel_timer(reminder_id)
    found = _update_status(reminder_id, "cancelled")
    if found:
        _append_event("cancelled", reminder_id)
    return {
        "reminder_id": reminder_id,
        "status": "cancelled" if found else "not_found",
        "authority": "reminder_system",
        "automatic_change": False,
        "raw_prompt_stored": False,
        "hidden_learning": False,
    }


# ── Deterministic handler ────────────────────────────────────────────────────

def handle_reminder_command(message: str, lowered: str) -> dict:
    """Handle reminder commands from the chat. Returns a dict with response info."""
    from weslr.response_formatter import build_deterministic_response

    # "show my reminders"
    if re.search(r"show\s+(my\s+)?reminders?", lowered):
        reminders = list_reminders()
        if not reminders:
            return build_deterministic_response(
                message=message,
                path="reminder_list",
                response_text="You have no pending reminders.",
                confidence="high",
                suggested_mode="direct",
            )
        lines = ["Your pending reminders:"]
        for r in reminders:
            lines.append(
                f"  [{r['reminder_id']}] {r['message']} — due {r['due_at'][:16].replace('T', ' ')}"
            )
        return build_deterministic_response(
            message=message,
            path="reminder_list",
            response_text="\n".join(lines),
            confidence="high",
            suggested_mode="direct",
        )

    # "cancel reminder <id>"
    m = re.search(r"cancel\s+reminder\s+([Rr][Ee][Mm]-\S+)", lowered)
    if m:
        rid = m.group(1).strip()
        result = cancel_reminder(rid)
        if result["status"] == "cancelled":
            return build_deterministic_response(
                message=message,
                path="reminder_cancel",
                response_text=f"Reminder {rid} cancelled.",
                confidence="high",
                suggested_mode="direct",
            )
        return build_deterministic_response(
            message=message,
            path="reminder_cancel",
            response_text=f"Reminder {rid} not found or already processed.",
            confidence="high",
            suggested_mode="direct",
        )

    # "remind me in N minutes/hours to <msg>"
    parsed = parse_reminder_request(message)
    if parsed:
        result = set_reminder(
            message=parsed["message"],
            due_at=parsed["due_at"],
        )
        rid = result["reminder_id"]
        return build_deterministic_response(
            message=message,
            path="reminder_set",
            response_text=f"Reminder set: [{rid}] {parsed['message']} — will fire at {parsed['due_at'][:16].replace('T', ' ')} UTC",
            confidence="high",
            suggested_mode="direct",
        )

    return {"handled": False}


# ── Startup scheduler ────────────────────────────────────────────────────────

def restore_pending_timers() -> None:
    """On import/server start, re-schedule all pending reminders."""
    pending = _load_pending()
    for r in pending:
        try:
            schedule_reminder(r)
        except Exception:
            pass


# ── Polling fallback ─────────────────────────────────────────────────────────

_POLL_INTERVAL = 60.0  # seconds

def _poll_loop() -> None:
    """Background thread: every _POLL_INTERVAL, check for missed reminders."""
    while True:
        time.sleep(_POLL_INTERVAL)
        pending = _load_pending()
        now = datetime.now(timezone.utc)
        for r in pending:
            try:
                due = datetime.fromisoformat(r.due_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            if due <= now:
                _fire_reminder(r.reminder_id, r.message, r.session_id)


def start_poll_thread() -> None:
    """Start the polling fallback thread. Idempotent."""
    t = threading.Thread(target=_poll_loop, daemon=True)
    t.start()


# ── Module startup ───────────────────────────────────────────────────────────

def _init() -> None:
    """Call once on import. Restore timers and start poll thread."""
    restore_pending_timers()
    start_poll_thread()


_init()