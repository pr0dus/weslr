"""Unified communicator outbox for WESLR.

This module provides a single output arbitration layer so WESLR speaks
through one coherent voice, rather than having multiple fragmented output
channels.

Features:
- In-memory queue with priority ordering
- Exact-text deduplication within 60 seconds
- Rate limiting (15 seconds between messages)
- Simple metadata tracking (no queue persistence)
- Light integration pass - easy to rollback

Priority order:
- P1_HIGH: human_response
- P2_MEDIUM: autonomous_expression
- P3_LOW: forced_expression
- P4_MINIMAL: internal_update

Dedup: same normalized text + same type within 60 seconds => skip
Rate limit: 15 seconds between outgoing messages
"""

from __future__ import annotations

import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import COMMUNICATOR_SELF_PATH


# ============================================================================
# CONFIGURATION
# ============================================================================

# Priority levels
PRIORITY_HUMAN_RESPONSE = 100
PRIORITY_AUTONOMOUS_EXPRESSION = 50
PRIORITY_FORCED_EXPRESSION = 10
PRIORITY_INTERNAL_UPDATE = 5

# Rate limiting
RATE_LIMIT_SECONDS = 15
DEDUP_WINDOW_SECONDS = 60

# State keys for lightweight metadata
STATE_LAST_COMMUNICATOR_MESSAGE_AT = "last_communicator_message_at"
STATE_LAST_OUTGOING_MESSAGE = "last_outgoing_message"
STATE_OUTBOX_STATS = "outbox_stats"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class OutboxEntry:
    """A single message in the outbox queue."""

    def __init__(
        self,
        message: str,
        message_type: str,
        priority: int = PRIORITY_AUTONOMOUS_EXPRESSION,
        metadata: Dict[str, Any] = None,
        timestamp: int = None,
    ):
        self.message = message
        self.message_type = message_type
        self.priority = priority
        self.metadata = metadata or {}
        self.timestamp = timestamp or int(time.time())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "message_type": self.message_type,
            "priority": self.priority,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OutboxEntry:
        return cls(
            message=data.get("message", ""),
            message_type=data.get("message_type", "unknown"),
            priority=data.get("priority", PRIORITY_AUTONOMOUS_EXPRESSION),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", int(time.time())),
        )


# ============================================================================
# OUTBOX IMPLEMENTATION
# ============================================================================

class CommunicatorOutbox:
    """In-memory outbox for WESLR's unified communication."""

    def __init__(self):
        self.queue: List[OutboxEntry] = []
        self.lock = threading.Lock()
        self.last_send_at: int = 0
        self.dedup_history: List[Dict[str, Any]] = []  # (normalized_text, type, timestamp)

    def enqueue(
        self,
        message: str,
        message_type: str,
        priority: int = PRIORITY_AUTONOMOUS_EXPRESSION,
        metadata: Dict[str, Any] = None,
    ) -> Optional[OutboxEntry]:
        """Add a message to the queue, with deduplication and priority.

        Args:
            message: The message text to send
            message_type: Type of message (human_response, autonomous_expression, etc.)
            priority: Priority level (higher = more urgent)
            metadata: Optional metadata for tracking

        Returns:
            OutboxEntry if enqueued, None if dedup prevented
        """
        now = int(time.time())
        normalized = _normalize_text(message)

        with self.lock:
            # Check dedup within window
            if self._is_duplicate(normalized, message_type, now):
                return None

            entry = OutboxEntry(
                message=message,
                message_type=message_type,
                priority=priority,
                metadata=metadata or {},
                timestamp=now,
            )

            # Update dedup history
            self.dedup_history.append({
                "normalized": normalized,
                "type": message_type,
                "timestamp": now,
            })

            # Keep only history within window
            self.dedup_history = [
                d for d in self.dedup_history
                if now - d["timestamp"] < DEDUP_WINDOW_SECONDS
            ]

            # Add to queue
            self.queue.append(entry)

            # Sort by priority (descending)
            self.queue.sort(key=lambda e: e.priority, reverse=True)

            return entry

    def _is_duplicate(self, normalized_text: str, message_type: str, now: int) -> bool:
        """Check if this message would be a duplicate within the dedup window."""
        for d in self.dedup_history:
            if (d["normalized"] == normalized_text
                    and d["type"] == message_type
                    and now - d["timestamp"] < DEDUP_WINDOW_SECONDS):
                return True
        return False

    def flush(self, communicator_self: Dict[str, Any]) -> Optional[str]:
        """Send the highest priority message, if any.

        Args:
            communicator_self: Current communicator state (for rate limiting)

        Returns:
            Message text if sent, None if nothing to send or rate limited
        """
        now = int(time.time())

        with self.lock:
            # Rate limiting check
            if now - self.last_send_at < RATE_LIMIT_SECONDS:
                return None

            # Find highest priority message (already sorted)
            if not self.queue:
                return None

            entry = self.queue.pop(0)

            # Update rate limit timestamp
            self.last_send_at = now

            # Update state (lightweight metadata only)
            communicator_self[STATE_LAST_COMMUNICATOR_MESSAGE_AT] = now
            communicator_self[STATE_LAST_OUTGOING_MESSAGE] = entry.to_dict()

            # Update outbox stats
            if STATE_OUTBOX_STATS not in communicator_self:
                communicator_self[STATE_OUTBOX_STATS] = {}
            stats = communicator_self[STATE_OUTBOX_STATS]
            stats["last_type"] = entry.message_type
            stats["last_timestamp"] = now

            return entry.message

    def get_stats(self) -> Dict[str, Any]:
        """Get current outbox statistics."""
        with self.lock:
            return {
                "queue_length": len(self.queue),
                "last_send_at": self.last_send_at,
                "dedup_history_length": len(self.dedup_history),
            }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_outbox: Optional[CommunicatorOutbox] = None


def get_outbox() -> CommunicatorOutbox:
    """Get or create the global outbox instance."""
    global _outbox
    if _outbox is None:
        _outbox = CommunicatorOutbox()
    return _outbox


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _normalize_text(text: str) -> str:
    """Normalize text for deduplication (lowercase, strip, collapse whitespace)."""
    return " ".join(str(text).strip().lower().split())


def load_communicator_self() -> Dict[str, Any]:
    """Load communicator_self.json."""
    if not COMMUNICATOR_SELF_PATH.exists():
        return {}
    try:
        import json
        with open(COMMUNICATOR_SELF_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_communicator_self(data: Dict[str, Any]) -> None:
    """Save communicator_self.json."""
    import json
    with open(COMMUNICATOR_SELF_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli_outbox_status() -> Dict[str, Any]:
    """CLI command to show outbox status."""
    outbox = get_outbox()
    stats = outbox.get_stats()

    return {
        "queue_length": stats["queue_length"],
        "last_send_at": stats["last_send_at"],
        "rate_limit_remaining": max(0, RATE_LIMIT_SECONDS - (int(time.time()) - stats["last_send_at"])),
    }


def cli_outbox_enqueue(message: str, message_type: str, priority: int) -> Dict[str, Any]:
    """CLI command to manually enqueue a message."""
    outbox = get_outbox()
    entry = outbox.enqueue(message, message_type, priority=priority)

    if entry is None:
        return {"status": "rejected", "reason": "duplicate within window"}
    else:
        return {"status": "enqueued", "entry": entry.to_dict()}


def cli_outbox_flush() -> Dict[str, Any]:
    """CLI command to flush the outbox."""
    outbox = get_outbox()
    communicator_self = load_communicator_self()
    message = outbox.flush(communicator_self)
    save_communicator_self(communicator_self)

    if message:
        return {"status": "sent", "message": message}
    else:
        return {"status": "empty_or_rate_limited"}


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 outbox.py <command> [args]")
        print("Commands:")
        print("  status                - Show outbox status")
        print("  enqueue <msg> <type> <priority> - Enqueue message")
        print("  flush                 - Flush and send highest priority message")
        return

    command = sys.argv[1]

    if command == "status":
        import json
        print(json.dumps(cli_outbox_status(), indent=2))

    elif command == "enqueue":
        if len(sys.argv) < 5:
            print("Usage: python3 outbox.py enqueue <message> <type> <priority>")
            return
        message = sys.argv[2]
        message_type = sys.argv[3]
        try:
            priority = int(sys.argv[4])
        except ValueError:
            priority = PRIORITY_AUTONOMOUS_EXPRESSION
        result = cli_outbox_enqueue(message, message_type, priority)
        import json
        print(json.dumps(result, indent=2))

    elif command == "flush":
        result = cli_outbox_flush()
        import json
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
