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


def record_outcome(
    message_type: str,
    message_timestamp: int,
    outcome: str,
    pattern_matched: str,
    human: str = "unknown"
) -> Dict[str, Any]:
    """Record a communication outcome for feedback tracking.

    Args:
        message_type: Type of message (human_response, autonomous_expression, etc.)
        message_timestamp: When the message was sent
        outcome: "good", "bad", or "unclear"
        pattern_matched: The feedback pattern that triggered this outcome
        human: The human who provided feedback

    Returns:
        Outcome dict that can be stored in communicator_self state
    """
    now = int(time.time())

    outcome_data = {
        "message_type": message_type,
        "message_timestamp": message_timestamp,
        "outcome": outcome,
        "pattern_matched": pattern_matched,
        "feedback_at": now,
        "human": human,
    }

    # Load current state
    cs = load_communicator_self()

    # Update last_communicator_outcome
    cs["last_communicator_outcome"] = outcome_data

    # Update confidence score with conservative smoothing
    if "continuity" not in cs:
        cs["continuity"] = {}
    if "confidence_score" not in cs["continuity"]:
        cs["continuity"]["confidence_score"] = 0.5  # Default

    # Calculate new confidence (max change of 0.2 per outcome, bounded 0.25-0.95)
    old_score = float(cs["continuity"]["confidence_score"])
    if outcome == "good":
        feedback = 0.2
    elif outcome == "bad":
        feedback = -0.2
    else:  # unclear
        feedback = 0.0

    # Conservative smoothing: max change of 0.2 per outcome
    # Good feedback (+0.2) means: new = old + 0.2 * 0.2 = old + 0.04
    # Bad feedback (-0.2) means: new = old + (-0.2) * 0.2 = old - 0.04
    # Unclear (0.0) means: no change
    new_score = old_score + (feedback * 0.2)

    # Clamp to valid range
    new_score = max(0.25, min(0.95, new_score))

    cs["continuity"]["confidence_score"] = round(new_score, 3)

    # Save state
    save_communicator_self(cs)

    return outcome_data


def update_feedback_in_state(
    cs: Dict[str, Any],
    outcome: str
) -> Dict[str, Any]:
    """Update feedback score in a given state dict and return it.
    
    This allows sim.py to pass its own state dict and have it updated in-place,
    avoiding the issue of separate state instances.
    
    Args:
        cs: The communicator_self state dict (to modify in-place)
        outcome: "good", "bad", or "unclear"
    
    Returns:
        The modified state dict
    """
    # Update confidence score with conservative smoothing
    if "continuity" not in cs:
        cs["continuity"] = {}
    if "confidence_score" not in cs["continuity"]:
        cs["continuity"]["confidence_score"] = 0.5  # Default

    # Calculate new confidence (max change of 0.2 per outcome, bounded 0.25-0.95)
    old_score = float(cs["continuity"]["confidence_score"])
    if outcome == "good":
        feedback = 0.2
    elif outcome == "bad":
        feedback = -0.2
    else:  # unclear
        feedback = 0.0

    # Conservative smoothing: max change of 0.2 per outcome
    new_score = old_score + (feedback * 0.2)

    # Clamp to valid range
    cs["continuity"]["confidence_score"] = round(max(0.25, min(0.95, new_score)), 3)

    return cs


def record_outcome_from_human_message(
    human_message: str,
    state: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """Record outcome based on a human's message content.

    Looks for explicit feedback patterns in the human's message.

    Args:
        human_message: The human's message text
        state: Optional state dict to update with confidence score (in-place)

    Returns:
        Outcome dict if feedback detected, None otherwise
    """
    msg_lower = str(human_message).lower().strip()

    # Check for bad signals first (to avoid false positives from "incorrect" containing "correct")
    if any(p in msg_lower for p in ["wrong", "not right", "incorrect", "confused", "don't understand", "i don't understand"]):
        outcome_data = {
            "message_type": "unknown",
            "message_timestamp": int(time.time()),
            "outcome": "bad",
            "pattern_matched": "explicit_negative",
            "feedback_at": int(time.time()),
            "human": "human",
        }

        # Update confidence score in state if provided
        if state is not None:
            update_feedback_in_state(state, "bad")
        else:
            # Load state and update if no state passed
            cs = load_communicator_self()
            update_feedback_in_state(cs, "bad")
            save_communicator_self(cs)

        return outcome_data

    # Check for good signals
    if any(p in msg_lower for p in ["thanks", "thank you", "yes", "correct", "exactly", "👍", "👍🏻", "👍🏼", "👍🏽", "👍🏾", "👍🏿"]):
        outcome_data = {
            "message_type": "unknown",
            "message_timestamp": int(time.time()),
            "outcome": "good",
            "pattern_matched": "explicit_positive",
            "feedback_at": int(time.time()),
            "human": "human",
        }

        # Update confidence score in state if provided
        if state is not None:
            update_feedback_in_state(state, "good")
        else:
            # Load state and update if no state passed
            cs = load_communicator_self()
            update_feedback_in_state(cs, "good")
            save_communicator_self(cs)

        return outcome_data

    # Check for unclear signals (no change, just acknowledge)
    if any(p in msg_lower for p in ["ok", "okay", "i see", "got it"]):
        outcome_data = {
            "message_type": "unknown",
            "message_timestamp": int(time.time()),
            "outcome": "unclear",
            "pattern_matched": "acknowledgment",
            "feedback_at": int(time.time()),
            "human": "human",
        }

        # Update confidence score in state if provided
        if state is not None:
            update_feedback_in_state(state, "unclear")
        else:
            # Load state and update if no state passed
            cs = load_communicator_self()
            update_feedback_in_state(cs, "unclear")
            save_communicator_self(cs)

        return outcome_data

    return None


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 outbox.py <command> [args]")
        print("Commands:")
        print("  status                - Show outbox status")
        print("  enqueue <msg> <type> <priority> - Enqueue message")
        print("  flush                 - Flush and send highest priority message")
        print("  feedback <message>    - Record outcome from human message")
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

    elif command == "feedback":
        if len(sys.argv) < 3:
            print("Usage: python3 outbox.py feedback <human_message>")
            return
        message = sys.argv[2]
        result = record_outcome_from_human_message(message)
        import json
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
