"""
WESLR Proactive File-Based Daemon V1

Background thread that periodically generates proactive suggestions
and writes them to .weslr/pending_messages.jsonl for /chat delivery.

Read-only suggestion generation. Write-only to the pending messages queue.
Daemon thread exits with the main process (daemon=True).

Configuration (env vars):
    WESLR_PROACTIVE_DAEMON_ENABLED  (default: false)
    WESLR_PROACTIVE_INTERVAL_MINUTES (default: 60)
    WESLR_OPERATOR_ID               (default: "operator")

Constraints:
    - No hidden learning, no raw prompt storage
    - No action execution — only writes to the queue
    - No Ollama calls
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from weslr.pending_messages_queue import enqueue
from weslr.proactive_suggestions import build_proactive_suggestion

# ── Configuration ────────────────────────────────────────────────────────────

_ENABLED: bool = os.environ.get("WESLR_PROACTIVE_DAEMON_ENABLED", "false").lower() in ("1", "true", "yes")
_INTERVAL_MINUTES: int = int(os.environ.get("WESLR_PROACTIVE_INTERVAL_MINUTES", "60"))
_OPERATOR_ID: str = os.environ.get("WESLR_OPERATOR_ID", "operator")

# ── Deduplication cache ───────────────────────────────────────────────────────
#
# Stores (message_text, timestamp) tuples for proactive messages sent in the
# last 24 hours. Size-capped at 5 entries to bound memory use.
# On startup the daemon seeds this from the last 10 entries of the queue file.

_DEDUP_CACHE: list[tuple[str, datetime]] = []
_DEDUP_LOCK = threading.Lock()
_DEDUP_MAX = 5
_DEDUP_TTL = timedelta(hours=24)


def _load_recent_proactive_messages(queue_path: Path, limit: int = 10) -> list[dict]:
    """Read the last N proactive messages from the queue file (if it exists)."""
    if not queue_path.exists():
        return []
    try:
        lines = queue_path.read_text().strip().split("\n")
        entries = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("queue_type") == "proactive":
                entries.append(e)
            if len(entries) >= limit:
                break
        return entries
    except Exception:
        return []


def _seed_dedup_cache(queue_path: Path) -> None:
    """On startup, seed dedup cache from recent queue entries."""
    recent = _load_recent_proactive_messages(queue_path, limit=10)
    now = datetime.now(timezone.utc)
    cutoff = now - _DEDUP_TTL
    for entry in reversed(recent):
        try:
            enqueued_at = datetime.fromisoformat(entry.get("enqueued_at", "").replace("Z", "+00:00"))
        except ValueError:
            enqueued_at = now
        if enqueued_at >= cutoff:
            with _DEDUP_LOCK:
                _DEDUP_CACHE.append((entry["message"], enqueued_at))
    # Trim to _DEDUP_MAX
    with _DEDUP_LOCK:
        while len(_DEDUP_CACHE) > _DEDUP_MAX:
            _DEDUP_CACHE.pop(0)


def _is_duplicate(message_text: str) -> bool:
    """Return True if the message text was sent within the last 24 hours."""
    now = datetime.now(timezone.utc)
    cutoff = now - _DEDUP_TTL
    with _DEDUP_LOCK:
        for text, ts in _DEDUP_CACHE:
            if text == message_text and ts >= cutoff:
                return True
        return False


def _mark_sent(message_text: str) -> None:
    """Record a sent message in the dedup cache. Size-capped at _DEDUP_MAX."""
    now = datetime.now(timezone.utc)
    with _DEDUP_LOCK:
        # Remove expired entries first
        cutoff = now - _DEDUP_TTL
        _DEDUP_CACHE[:] = [(t, ts) for t, ts in _DEDUP_CACHE if ts >= cutoff]
        _DEDUP_CACHE.append((message_text, now))
        while len(_DEDUP_CACHE) > _DEDUP_MAX:
            _DEDUP_CACHE.pop(0)


# ── Queue path ────────────────────────────────────────────────────────────────

def _queue_path() -> Path:
    return Path(".weslr/pending_messages.jsonl")


# ── Daemon loop ───────────────────────────────────────────────────────────────

_STOP_EVENT = threading.Event()
_THREAD: Optional[threading.Thread] = None


def _daemon_loop(interval_seconds: float) -> None:
    """Proactive suggestion daemon loop. Runs until stop() is called."""
    queue_path = _queue_path()

    # Seed dedup cache from recent history
    _seed_dedup_cache(queue_path)

    while not _STOP_EVENT.is_set():
        _STOP_EVENT.wait(timeout=interval_seconds)
        if _STOP_EVENT.is_set():
            break

        # Generate exactly one suggestion per tick
        result = build_proactive_suggestion(user_id=_OPERATOR_ID)
        if not result.get("suggestion_available"):
            continue

        suggestion_text = result["suggestion"]
        if not suggestion_text or not isinstance(suggestion_text, str):
            continue

        if _is_duplicate(suggestion_text):
            continue

        try:
            enqueue(
                queue_type="proactive",
                message=f"Hey – by the way: {suggestion_text}",
                session_id=_OPERATOR_ID,
                ttl_minutes=60,
                priority="medium",
            )
            _mark_sent(suggestion_text)
        except Exception:
            # Queue write failure must not crash the daemon
            pass


def start_proactive_daemon(
    interval_minutes: int = _INTERVAL_MINUTES,
    enabled: bool = _ENABLED,
) -> Optional[threading.Thread]:
    """Start the proactive daemon thread. Idempotent — returns existing thread if already started."""
    global _THREAD

    if not enabled:
        return None

    if _THREAD is not None and _THREAD.is_alive():
        return _THREAD

    _STOP_EVENT.clear()
    _THREAD = threading.Thread(
        target=_daemon_loop,
        args=(interval_minutes * 60.0,),
        name="proactive-daemon",
        daemon=True,
    )
    _THREAD.start()
    return _THREAD


def stop_proactive_daemon(timeout: float = 5.0) -> bool:
    """Signal the daemon to stop and wait for it to exit. Idempotent."""
    global _THREAD
    _STOP_EVENT.set()
    if _THREAD is not None:
        _THREAD.join(timeout=timeout)
        _THREAD = None
    return True
