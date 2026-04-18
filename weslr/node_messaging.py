"""Active Node Transport / Messaging Layer (v60)

Messaging substrate between WESLR nodes.
Provides message envelopes, trust verification, queueing,
delivery tracking, and partition handling.

Architecture:
  - MessageType — message categories
  - DeliveryStatus — delivery lifecycle states
  - MessageEnvelope — canonical message structure
  - SenderIdentity/ReceiverIdentity — verified identities
  - TrustVerification — pre-send trust validation
  - TimeoutRetryPolicy — retry configuration
  - MessageQueueState — per-destination queue
  - MessagingTransport — core transport layer
  - DegradedPartitionHandler — partition resilience

Rules:
  - Additive only (no breaking changes)
  - Transport only, no remote execution
  - Data messages only, no code execution
  - Trust verification before send/receive
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple

from .node_identity import (
    NodeIdentity,
    NodeTrustState,
    NodeTrustStatus,
    NodeHealthStatus
)


# ============================================================================
# ENUMS
# ============================================================================


class MessageType(str, Enum):
    """Categories of messages between nodes."""
    HEARTBEAT = "heartbeat"           # Keep-alive / presence
    STATE_SYNC = "state_sync"         # Continuity state synchronization
    GOVERNANCE_AWARENESS = "governance_awareness"  # Governance state broadcast
    CONTROL_SIGNAL = "control_signal" # Non-execution control (pause, resume)
    ACK = "ack"                       # Acknowledgment
    ERROR = "error"                   # Error notification
    DISCOVERY = "discovery"           # Node capability discovery


class DeliveryStatus(str, Enum):
    """Lifecycle states for message delivery."""
    PENDING = "pending"               # Queued, not yet sent
    IN_FLIGHT = "in_flight"           # Sent, awaiting acknowledgment
    DELIVERED = "delivered"           # Acknowledged by recipient
    FAILED = "failed"                 # Delivery failed, no retry
    RETRYING = "retrying"             # Failed but retry scheduled
    EXPIRED = "expired"               # Exceeded max retries/time
    REJECTED = "rejected"             # Rejected by recipient trust boundary


class TransportMode(str, Enum):
    """Transport connectivity mode."""
    FULL = "full"                     # Full connectivity
    DEGRADED = "degraded"             # Limited connectivity
    PARTITIONED = "partitioned"     # No connectivity, queue only


# ============================================================================
# MESSAGE ENVELOPE
# ============================================================================


@dataclass
class MessageHeaders:
    """Standard headers for all messages."""
    message_id: str
    correlation_id: Optional[str] = None  # For request/response pairing
    message_type: str = MessageType.HEARTBEAT.value
    
    sender_node_id: str = ""
    sender_timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    sender_sequence: int = 0            # Sequence number for ordering
    
    receiver_node_id: str = ""
    receiver_timestamp: Optional[str] = None  # Set on receipt
    
    priority: int = 0                   # Higher = more urgent
    ttl_seconds: int = 300              # Time to live
    
    # Trust verification
    sender_trust_hash: Optional[str] = None  # Hash of sender trust state
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "message_type": self.message_type,
            "sender_node_id": self.sender_node_id,
            "sender_timestamp": self.sender_timestamp,
            "sender_sequence": self.sender_sequence,
            "receiver_node_id": self.receiver_node_id,
            "receiver_timestamp": self.receiver_timestamp,
            "priority": self.priority,
            "ttl_seconds": self.ttl_seconds,
            "sender_trust_hash": self.sender_trust_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageHeaders":
        return cls(
            message_id=data["message_id"],
            correlation_id=data.get("correlation_id"),
            message_type=data.get("message_type", MessageType.HEARTBEAT.value),
            sender_node_id=data.get("sender_node_id", ""),
            sender_timestamp=data.get("sender_timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            sender_sequence=data.get("sender_sequence", 0),
            receiver_node_id=data.get("receiver_node_id", ""),
            receiver_timestamp=data.get("receiver_timestamp"),
            priority=data.get("priority", 0),
            ttl_seconds=data.get("ttl_seconds", 300),
            sender_trust_hash=data.get("sender_trust_hash")
        )


@dataclass
class MessageEnvelope:
    """Canonical message structure for node-to-node communication.
    
    Contains headers (metadata) and payload (data).
    Payload is opaque to transport layer.
    """
    
    headers: MessageHeaders
    payload: Dict[str, Any] = field(default_factory=dict)
    payload_checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "headers": self.headers.to_dict(),
            "payload": self.payload,
            "payload_checksum": self.payload_checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageEnvelope":
        return cls(
            headers=MessageHeaders.from_dict(data["headers"]),
            payload=data.get("payload", {}),
            payload_checksum=data.get("payload_checksum")
        )
    
    def is_expired(self) -> bool:
        """Check if message TTL has expired."""
        try:
            sent = datetime.fromisoformat(self.headers.sender_timestamp.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - sent).total_seconds()
            return age > self.headers.ttl_seconds
        except Exception:
            return True


# ============================================================================
# TRUST VERIFICATION
# ============================================================================


@dataclass
class TrustVerification:
    """Verifies trust between sender and receiver before messaging."""
    
    local_node_id: str
    min_trust_level: str = NodeTrustStatus.PROVISIONAL.value
    require_mutual: bool = True
    
    def verify_sender(
        self,
        envelope: MessageEnvelope,
        sender_trust: NodeTrustState
    ) -> Tuple[bool, str]:
        """Verify sender is trusted to send messages.
        
        Returns (verified, reason).
        """
        # Check sender matches envelope
        if sender_trust.node_id != envelope.headers.sender_node_id:
            return False, "Sender identity mismatch"
        
        # Check trust level
        trust_order = [
            NodeTrustStatus.REVOKED.value,
            NodeTrustStatus.UNTRUSTED.value,
            NodeTrustStatus.PENDING.value,
            NodeTrustStatus.PROVISIONAL.value,
            NodeTrustStatus.TRUSTED.value
        ]
        
        min_idx = trust_order.index(self.min_trust_level)
        sender_idx = trust_order.index(sender_trust.trust_status) \
            if sender_trust.trust_status in trust_order else 0
        
        if sender_idx < min_idx:
            return False, f"Sender trust {sender_trust.trust_status} below required {self.min_trust_level}"
        
        # Check health
        if sender_trust.health_status == NodeHealthStatus.UNHEALTHY.value:
            return False, "Sender health is unhealthy"
        
        return True, "Sender verified"
    
    def verify_receiver(
        self,
        receiver_trust: NodeTrustState
    ) -> Tuple[bool, str]:
        """Verify receiver is trusted to receive messages."""
        trust_order = [
            NodeTrustStatus.REVOKED.value,
            NodeTrustStatus.UNTRUSTED.value,
            NodeTrustStatus.PENDING.value,
            NodeTrustStatus.PROVISIONAL.value,
            NodeTrustStatus.TRUSTED.value
        ]
        
        min_idx = trust_order.index(self.min_trust_level)
        receiver_idx = trust_order.index(receiver_trust.trust_status) \
            if receiver_trust.trust_status in trust_order else 0
        
        if receiver_idx < min_idx:
            return False, f"Receiver trust {receiver_trust.trust_status} below required {self.min_trust_level}"
        
        if receiver_trust.health_status == NodeHealthStatus.UNHEALTHY.value:
            return False, "Receiver health is unhealthy"
        
        return True, "Receiver verified"
    
    def verify_pair(
        self,
        sender_trust: NodeTrustState,
        receiver_trust: NodeTrustState
    ) -> Tuple[bool, str]:
        """Verify both sender and receiver for message exchange."""
        # Dummy envelope for sender verification
        dummy_headers = MessageHeaders(
            message_id="verify",
            sender_node_id=sender_trust.node_id
        )
        dummy_envelope = MessageEnvelope(headers=dummy_headers)
        
        sender_ok, sender_reason = self.verify_sender(dummy_envelope, sender_trust)
        if not sender_ok:
            return False, f"Sender: {sender_reason}"
        
        receiver_ok, receiver_reason = self.verify_receiver(receiver_trust)
        if not receiver_ok:
            return False, f"Receiver: {receiver_reason}"
        
        return True, "Pair verified"


# ============================================================================
# TIMEOUT / RETRY POLICY
# ============================================================================


@dataclass
class TimeoutRetryPolicy:
    """Configuration for message timeout and retry behavior."""
    
    initial_timeout_ms: int = 5000        # 5 seconds initial
    max_timeout_ms: int = 60000          # 60 seconds max
    timeout_multiplier: float = 2.0      # Exponential backoff
    
    max_retries: int = 3                 # Max retry attempts
    retry_delay_ms: int = 1000           # Base delay between retries
    retry_delay_multiplier: float = 2.0  # Exponential backoff on delay
    
    max_message_age_seconds: int = 300  # Drop messages older than this
    
    def calculate_timeout(self, attempt: int) -> int:
        """Calculate timeout for a given attempt."""
        timeout = self.initial_timeout_ms * (self.timeout_multiplier ** attempt)
        return min(int(timeout), self.max_timeout_ms)
    
    def calculate_retry_delay(self, attempt: int) -> int:
        """Calculate delay before retry."""
        delay = self.retry_delay_ms * (self.retry_delay_multiplier ** attempt)
        return int(delay)
    
    def should_retry(self, attempt: int, age_seconds: int) -> bool:
        """Check if message should be retried."""
        if attempt >= self.max_retries:
            return False
        if age_seconds > self.max_message_age_seconds:
            return False
        return True


# ============================================================================
# MESSAGE QUEUE STATE
# ============================================================================


@dataclass
class QueuedMessage:
    """A message in the queue with delivery metadata."""
    
    envelope: MessageEnvelope
    status: str = DeliveryStatus.PENDING.value
    
    # Timing
    queued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    last_attempt_at: Optional[str] = None
    
    # Retry
    attempt_count: int = 0
    next_retry_at: Optional[str] = None
    
    # Result
    error_message: Optional[str] = None
    
    def mark_sent(self) -> None:
        """Mark as sent (in-flight)."""
        self.status = DeliveryStatus.IN_FLIGHT.value
        self.sent_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.last_attempt_at = self.sent_at
        self.attempt_count += 1
    
    def mark_delivered(self) -> None:
        """Mark as delivered."""
        self.status = DeliveryStatus.DELIVERED.value
        self.delivered_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def mark_failed(self, error: str, retry_scheduled: bool = False) -> None:
        """Mark as failed."""
        self.error_message = error
        if retry_scheduled:
            self.status = DeliveryStatus.RETRYING.value
        else:
            self.status = DeliveryStatus.FAILED.value
    
    def mark_rejected(self, reason: str) -> None:
        """Mark as rejected."""
        self.status = DeliveryStatus.REJECTED.value
        self.error_message = reason
    
    def schedule_retry(self, retry_at: str) -> None:
        """Schedule a retry."""
        self.status = DeliveryStatus.RETRYING.value
        self.next_retry_at = retry_at
    
    def is_retry_due(self) -> bool:
        """Check if retry is due."""
        if self.status != DeliveryStatus.RETRYING.value or not self.next_retry_at:
            return False
        try:
            retry_time = datetime.fromisoformat(self.next_retry_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) >= retry_time
        except Exception:
            return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "envelope": self.envelope.to_dict(),
            "status": self.status,
            "queued_at": self.queued_at,
            "sent_at": self.sent_at,
            "delivered_at": self.delivered_at,
            "last_attempt_at": self.last_attempt_at,
            "attempt_count": self.attempt_count,
            "next_retry_at": self.next_retry_at,
            "error_message": self.error_message
        }


class MessageQueueState:
    """Per-destination message queue with delivery tracking."""
    
    def __init__(
        self,
        destination_node_id: str,
        max_queue_size: int = 1000,
        policy: Optional[TimeoutRetryPolicy] = None
    ):
        self.destination_node_id = destination_node_id
        self.max_queue_size = max_queue_size
        self.policy = policy or TimeoutRetryPolicy()
        
        self._queue: Dict[str, QueuedMessage] = {}
        self._sequence = 0
    
    def enqueue(self, envelope: MessageEnvelope) -> Optional[str]:
        """Add message to queue. Returns message ID or None if full."""
        if len(self._queue) >= self.max_queue_size:
            return None
        
        message_id = envelope.headers.message_id
        queued = QueuedMessage(envelope=envelope)
        self._queue[message_id] = queued
        
        return message_id
    
    def dequeue(self) -> Optional[QueuedMessage]:
        """Get next message ready to send (highest priority, not expired)."""
        ready = [
            (msg_id, msg) for msg_id, msg in self._queue.items()
            if msg.status in (DeliveryStatus.PENDING.value, DeliveryStatus.RETRYING.value)
            and not msg.envelope.is_expired()
            and (msg.status != DeliveryStatus.RETRYING.value or msg.is_retry_due())
        ]
        
        if not ready:
            return None
        
        # Sort by priority (higher first), then by sequence
        ready.sort(key=lambda x: (-x[1].envelope.headers.priority, x[1].envelope.headers.sender_sequence))
        
        return ready[0][1]
    
    def get_message(self, message_id: str) -> Optional[QueuedMessage]:
        """Get specific message by ID."""
        return self._queue.get(message_id)
    
    def remove(self, message_id: str) -> bool:
        """Remove message from queue."""
        if message_id in self._queue:
            del self._queue[message_id]
            return True
        return False
    
    def mark_delivered(self, message_id: str) -> bool:
        """Mark message as delivered."""
        msg = self._queue.get(message_id)
        if msg:
            msg.mark_delivered()
            return True
        return False
    
    def mark_failed(self, message_id: str, error: str) -> bool:
        """Mark message as failed."""
        msg = self._queue.get(message_id)
        if not msg:
            return False
        
        # Check if should retry
        try:
            queued = datetime.fromisoformat(msg.queued_at.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - queued).total_seconds()
        except Exception:
            age = 0
        
        should_retry = self.policy.should_retry(msg.attempt_count, int(age))
        
        if should_retry:
            delay_ms = self.policy.calculate_retry_delay(msg.attempt_count)
            retry_at = (datetime.now(timezone.utc) + timedelta(milliseconds=delay_ms)).isoformat().replace("+00:00", "Z")
            msg.schedule_retry(retry_at)
        else:
            msg.mark_failed(error, retry_scheduled=False)
        
        return True
    
    def mark_rejected(self, message_id: str, reason: str) -> bool:
        """Mark message as rejected."""
        msg = self._queue.get(message_id)
        if msg:
            msg.mark_rejected(reason)
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """Remove expired messages. Returns count removed."""
        expired = [
            msg_id for msg_id, msg in self._queue.items()
            if msg.envelope.is_expired() or msg.status == DeliveryStatus.EXPIRED.value
        ]
        for msg_id in expired:
            del self._queue[msg_id]
        return len(expired)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        by_status = {}
        for msg in self._queue.values():
            by_status[msg.status] = by_status.get(msg.status, 0) + 1
        
        return {
            "destination": self.destination_node_id,
            "total_messages": len(self._queue),
            "by_status": by_status,
            "max_size": self.max_queue_size
        }


# ============================================================================
# MESSAGING TRANSPORT
# ============================================================================


class MessagingTransport:
    """Core transport layer for node-to-node messaging.
    
    Handles message queuing, trust verification, delivery tracking.
    Transport only - no remote execution.
    """
    
    def __init__(
        self,
        local_identity: NodeIdentity,
        trust_verification: Optional[TrustVerification] = None,
        retry_policy: Optional[TimeoutRetryPolicy] = None
    ):
        self.local_identity = local_identity
        self.trust_verification = trust_verification or TrustVerification(
            local_node_id=local_identity.node_id
        )
        self.retry_policy = retry_policy or TimeoutRetryPolicy()
        
        self._queues: Dict[str, MessageQueueState] = {}
        self._sequence = 0
        self._mode = TransportMode.FULL.value
        
        # Callbacks for external integration
        self._on_deliver: Optional[Callable[[MessageEnvelope], None]] = None
        self._on_receive: Optional[Callable[[MessageEnvelope], None]] = None
    
    def set_mode(self, mode: str) -> None:
        """Set transport mode."""
        self._mode = mode
    
    def create_message(
        self,
        message_type: str,
        receiver_node_id: str,
        payload: Dict[str, Any],
        priority: int = 0,
        correlation_id: Optional[str] = None
    ) -> MessageEnvelope:
        """Create a new message envelope."""
        self._sequence += 1
        
        headers = MessageHeaders(
            message_id=f"{self.local_identity.node_id}:{self._sequence}:{int(time.time())}",
            correlation_id=correlation_id,
            message_type=message_type,
            sender_node_id=self.local_identity.node_id,
            sender_sequence=self._sequence,
            receiver_node_id=receiver_node_id,
            priority=priority
        )
        
        return MessageEnvelope(
            headers=headers,
            payload=payload
        )
    
    def send(
        self,
        envelope: MessageEnvelope,
        receiver_trust: NodeTrustState
    ) -> Tuple[bool, str]:
        """Queue a message for delivery.
        
        Returns (queued, reason).
        """
        # Verify receiver trust
        verified, reason = self.trust_verification.verify_receiver(receiver_trust)
        if not verified:
            return False, f"Trust verification failed: {reason}"
        
        # In partitioned mode, queue only
        if self._mode == TransportMode.PARTITIONED.value:
            queue = self._get_or_create_queue(receiver_trust.node_id)
            msg_id = queue.enqueue(envelope)
            if msg_id:
                return True, "Queued (partitioned mode)"
            return False, "Queue full"
        
        # Get or create queue
        queue = self._get_or_create_queue(receiver_trust.node_id)
        msg_id = queue.enqueue(envelope)
        
        if msg_id:
            return True, "Queued"
        
        return False, "Queue full"
    
    def receive(
        self,
        envelope: MessageEnvelope,
        sender_trust: NodeTrustState
    ) -> Tuple[bool, str]:
        """Receive and validate an incoming message.
        
        Returns (accepted, reason).
        """
        # Check TTL
        if envelope.is_expired():
            return False, "Message expired"
        
        # Verify sender trust
        verified, reason = self.trust_verification.verify_sender(envelope, sender_trust)
        if not verified:
            return False, f"Trust verification failed: {reason}"
        
        # Update headers
        envelope.headers.receiver_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Callback
        if self._on_receive:
            self._on_receive(envelope)
        
        return True, "Accepted"
    
    def process_outbound(self, node_id: str) -> Optional[QueuedMessage]:
        """Process next outbound message for a node.
        
        Returns message ready to send, or None.
        """
        if self._mode == TransportMode.PARTITIONED.value:
            return None
        
        queue = self._queues.get(node_id)
        if not queue:
            return None
        
        msg = queue.dequeue()
        if msg:
            msg.mark_sent()
        
        return msg
    
    def mark_delivered(self, node_id: str, message_id: str) -> bool:
        """Mark a message as delivered."""
        queue = self._queues.get(node_id)
        if queue:
            return queue.mark_delivered(message_id)
        return False
    
    def mark_failed(self, node_id: str, message_id: str, error: str) -> bool:
        """Mark a message as failed (may retry)."""
        queue = self._queues.get(node_id)
        if queue:
            return queue.mark_failed(message_id, error)
        return False
    
    def _get_or_create_queue(self, node_id: str) -> MessageQueueState:
        """Get or create queue for destination."""
        if node_id not in self._queues:
            self._queues[node_id] = MessageQueueState(
                destination_node_id=node_id,
                policy=self.retry_policy
            )
        return self._queues[node_id]
    
    def get_queue_stats(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """Get queue statistics."""
        if node_id:
            queue = self._queues.get(node_id)
            return queue.get_stats() if queue else {}
        
        return {
            node_id: queue.get_stats()
            for node_id, queue in self._queues.items()
        }
    
    def cleanup(self) -> int:
        """Clean up expired messages across all queues."""
        total = 0
        for queue in self._queues.values():
            total += queue.cleanup_expired()
        return total
    
    def set_on_receive(self, callback: Callable[[MessageEnvelope], None]) -> None:
        """Set callback for received messages."""
        self._on_receive = callback
    
    def get_pending_count(self) -> int:
        """Get total pending messages across all queues."""
        total = 0
        for queue in self._queues.values():
            for msg in queue._queue.values():
                if msg.status in (DeliveryStatus.PENDING.value, DeliveryStatus.RETRYING.value):
                    total += 1
        return total


# ============================================================================
# DEGRADED PARTITION HANDLER
# ============================================================================


class DegradedPartitionHandler:
    """Handles messaging during network partitions.
    
    Queues messages when partitioned, retries when healed.
    """
    
    def __init__(self, transport: MessagingTransport):
        self.transport = transport
        self._partitioned_nodes: Set[str] = set()
        self._heal_callbacks: List[Callable[[str], None]] = []
    
    def mark_partitioned(self, node_id: str) -> None:
        """Mark a node as partitioned."""
        self._partitioned_nodes.add(node_id)
        self.transport.set_mode(TransportMode.DEGRADED.value)
    
    def mark_healed(self, node_id: str) -> None:
        """Mark a node as healed (connectivity restored)."""
        if node_id in self._partitioned_nodes:
            self._partitioned_nodes.discard(node_id)
            
            # Trigger retry of queued messages
            self._retry_queued(node_id)
            
            # Callbacks
            for callback in self._heal_callbacks:
                callback(node_id)
        
        # If no more partitioned nodes, restore full mode
        if not self._partitioned_nodes:
            self.transport.set_mode(TransportMode.FULL.value)
    
    def _retry_queued(self, node_id: str) -> int:
        """Retry queued messages for a healed node."""
        queue = self.transport._queues.get(node_id)
        if not queue:
            return 0
        
        count = 0
        for msg in queue._queue.values():
            if msg.status == DeliveryStatus.RETRYING.value:
                msg.status = DeliveryStatus.PENDING.value
                msg.next_retry_at = None
                count += 1
        
        return count
    
    def is_partitioned(self, node_id: str) -> bool:
        """Check if node is currently partitioned."""
        return node_id in self._partitioned_nodes
    
    def on_heal(self, callback: Callable[[str], None]) -> None:
        """Register callback for partition heal events."""
        self._heal_callbacks.append(callback)
    
    def get_partitioned_nodes(self) -> List[str]:
        """Get list of currently partitioned nodes."""
        return list(self._partitioned_nodes)
