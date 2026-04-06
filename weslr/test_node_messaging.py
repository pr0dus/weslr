"""Tests for Active Node Transport / Messaging Layer (v60)

Behavioral tests for node-to-node messaging.
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.node_messaging import (
    MessageEnvelope,
    MessageHeaders,
    MessageType,
    DeliveryStatus,
    TransportMode,
    TrustVerification,
    TimeoutRetryPolicy,
    MessageQueueState,
    QueuedMessage,
    MessagingTransport,
    DegradedPartitionHandler,
)
from weslr.node_identity import (
    NodeIdentity,
    NodeTrustState,
    NodeRole,
    NodeTrustStatus,
    NodeHealthStatus,
)


class TestMessageHeaders(unittest.TestCase):
    """Test message headers."""

    def test_headers_creation(self):
        """Headers store basic message metadata."""
        headers = MessageHeaders(
            message_id="msg-1",
            message_type=MessageType.HEARTBEAT.value,
            sender_node_id="node-a",
            receiver_node_id="node-b"
        )

        self.assertEqual(headers.message_id, "msg-1")
        self.assertEqual(headers.message_type, MessageType.HEARTBEAT.value)
        self.assertEqual(headers.sender_node_id, "node-a")
        self.assertEqual(headers.receiver_node_id, "node-b")

    def test_headers_serialization(self):
        """Headers serialize and deserialize."""
        headers = MessageHeaders(
            message_id="msg-1",
            correlation_id="corr-1",
            message_type=MessageType.STATE_SYNC.value,
            sender_node_id="node-a",
            sender_sequence=5,
            receiver_node_id="node-b",
            priority=10
        )

        data = headers.to_dict()
        restored = MessageHeaders.from_dict(data)

        self.assertEqual(restored.message_id, headers.message_id)
        self.assertEqual(restored.correlation_id, headers.correlation_id)
        self.assertEqual(restored.priority, headers.priority)


class TestMessageEnvelope(unittest.TestCase):
    """Test message envelope."""

    def test_envelope_creation(self):
        """Envelope wraps headers and payload."""
        headers = MessageHeaders(message_id="msg-1", sender_node_id="node-a")
        envelope = MessageEnvelope(
            headers=headers,
            payload={"data": "value"}
        )

        self.assertEqual(envelope.headers.message_id, "msg-1")
        self.assertEqual(envelope.payload["data"], "value")

    def test_expiration_detection(self):
        """Expired messages are detected."""
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat().replace("+00:00", "Z")

        headers = MessageHeaders(
            message_id="msg-1",
            sender_node_id="node-a",
            sender_timestamp=old_time,
            ttl_seconds=300
        )
        envelope = MessageEnvelope(headers=headers)

        self.assertTrue(envelope.is_expired())

    def test_serialization(self):
        """Envelope serializes and deserializes."""
        headers = MessageHeaders(message_id="msg-1", sender_node_id="node-a")
        envelope = MessageEnvelope(
            headers=headers,
            payload={"key": "value"}
        )

        data = envelope.to_dict()
        restored = MessageEnvelope.from_dict(data)

        self.assertEqual(restored.headers.message_id, "msg-1")
        self.assertEqual(restored.payload["key"], "value")


class TestTrustVerification(unittest.TestCase):
    """Test trust verification."""

    def setUp(self):
        self.verifier = TrustVerification(local_node_id="local")

    def test_verify_trusted_sender(self):
        """Trusted sender passes verification."""
        headers = MessageHeaders(message_id="msg-1", sender_node_id="trusted-node")
        envelope = MessageEnvelope(headers=headers)

        trust = NodeTrustState(
            node_id="trusted-node",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        ok, reason = self.verifier.verify_sender(envelope, trust)
        self.assertTrue(ok)

    def test_reject_mismatched_identity(self):
        """Sender identity mismatch is rejected."""
        headers = MessageHeaders(message_id="msg-1", sender_node_id="claimed-id")
        envelope = MessageEnvelope(headers=headers)

        trust = NodeTrustState(
            node_id="actual-id",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        ok, reason = self.verifier.verify_sender(envelope, trust)
        self.assertFalse(ok)
        self.assertIn("mismatch", reason.lower())

    def test_reject_untrusted_sender(self):
        """Untrusted sender is rejected."""
        headers = MessageHeaders(message_id="msg-1", sender_node_id="untrusted")
        envelope = MessageEnvelope(headers=headers)

        trust = NodeTrustState(
            node_id="untrusted",
            trust_status=NodeTrustStatus.UNTRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        ok, reason = self.verifier.verify_sender(envelope, trust)
        self.assertFalse(ok)
        self.assertIn("trust", reason.lower())

    def test_reject_unhealthy_sender(self):
        """Unhealthy sender is rejected."""
        headers = MessageHeaders(message_id="msg-1", sender_node_id="sick-node")
        envelope = MessageEnvelope(headers=headers)

        trust = NodeTrustState(
            node_id="sick-node",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.UNHEALTHY.value
        )

        ok, reason = self.verifier.verify_sender(envelope, trust)
        self.assertFalse(ok)
        self.assertIn("health", reason.lower())

    def test_verify_pair_both_directions(self):
        """Pair verification checks both sender and receiver."""
        sender = NodeTrustState(
            node_id="sender",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        receiver = NodeTrustState(
            node_id="receiver",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        ok, reason = self.verifier.verify_pair(sender, receiver)
        self.assertTrue(ok)


class TestTimeoutRetryPolicy(unittest.TestCase):
    """Test timeout and retry policy."""

    def setUp(self):
        self.policy = TimeoutRetryPolicy(
            initial_timeout_ms=1000,
            max_timeout_ms=10000,
            timeout_multiplier=2.0,
            max_retries=3,
            retry_delay_ms=500,
            retry_delay_multiplier=2.0
        )

    def test_timeout_calculation(self):
        """Timeout increases exponentially."""
        t0 = self.policy.calculate_timeout(0)
        t1 = self.policy.calculate_timeout(1)
        t2 = self.policy.calculate_timeout(2)

        self.assertEqual(t0, 1000)
        self.assertEqual(t1, 2000)
        self.assertEqual(t2, 4000)

    def test_timeout_max_cap(self):
        """Timeout is capped at max."""
        t5 = self.policy.calculate_timeout(5)
        self.assertEqual(t5, 10000)  # Capped at max

    def test_retry_delay_calculation(self):
        """Retry delay increases exponentially."""
        d0 = self.policy.calculate_retry_delay(0)
        d1 = self.policy.calculate_retry_delay(1)

        self.assertEqual(d0, 500)
        self.assertEqual(d1, 1000)

    def test_should_retry_within_limit(self):
        """Retry allowed within max_retries."""
        self.assertTrue(self.policy.should_retry(0, 10))
        self.assertTrue(self.policy.should_retry(2, 10))
        self.assertFalse(self.policy.should_retry(3, 10))  # At limit
        self.assertFalse(self.policy.should_retry(4, 10))  # Over limit

    def test_should_retry_expired_age(self):
        """Retry denied for old messages."""
        self.assertFalse(self.policy.should_retry(0, 400))  # Old message


class TestMessageQueueState(unittest.TestCase):
    """Test message queue operations."""

    def setUp(self):
        self.queue = MessageQueueState(destination_node_id="remote")

    def test_enqueue_dequeue(self):
        """Messages can be enqueued and dequeued."""
        headers = MessageHeaders(message_id="msg-1", sender_node_id="local")
        envelope = MessageEnvelope(headers=headers)

        msg_id = self.queue.enqueue(envelope)
        self.assertEqual(msg_id, "msg-1")

        queued = self.queue.dequeue()
        self.assertIsNotNone(queued)
        self.assertEqual(queued.envelope.headers.message_id, "msg-1")

    def test_dequeue_priority_order(self):
        """Higher priority messages dequeued first."""
        low = MessageEnvelope(headers=MessageHeaders(message_id="low", priority=0, sender_node_id="local"))
        high = MessageEnvelope(headers=MessageHeaders(message_id="high", priority=10, sender_node_id="local"))

        self.queue.enqueue(low)
        self.queue.enqueue(high)

        first = self.queue.dequeue()
        self.assertEqual(first.envelope.headers.message_id, "high")

    def test_queue_full(self):
        """Queue returns None when full."""
        small_queue = MessageQueueState(destination_node_id="remote", max_queue_size=2)

        small_queue.enqueue(MessageEnvelope(headers=MessageHeaders(message_id="1", sender_node_id="local")))
        small_queue.enqueue(MessageEnvelope(headers=MessageHeaders(message_id="2", sender_node_id="local")))

        result = small_queue.enqueue(MessageEnvelope(headers=MessageHeaders(message_id="3", sender_node_id="local")))
        self.assertIsNone(result)

    def test_mark_delivered(self):
        """Messages can be marked delivered."""
        envelope = MessageEnvelope(headers=MessageHeaders(message_id="msg-1", sender_node_id="local"))
        self.queue.enqueue(envelope)
        self.queue.dequeue().mark_sent()

        result = self.queue.mark_delivered("msg-1")
        self.assertTrue(result)

        msg = self.queue.get_message("msg-1")
        self.assertEqual(msg.status, DeliveryStatus.DELIVERED.value)

    def test_mark_failed_with_retry(self):
        """Failed messages can be scheduled for retry."""
        envelope = MessageEnvelope(headers=MessageHeaders(message_id="msg-1", sender_node_id="local"))
        self.queue.enqueue(envelope)

        self.queue.mark_failed("msg-1", "Timeout")

        msg = self.queue.get_message("msg-1")
        self.assertEqual(msg.status, DeliveryStatus.RETRYING.value)
        self.assertIsNotNone(msg.next_retry_at)

    def test_retry_due_check(self):
        """Retry due check works."""
        envelope = MessageEnvelope(headers=MessageHeaders(message_id="msg-1", sender_node_id="local"))
        self.queue.enqueue(envelope)

        self.queue.mark_failed("msg-1", "Timeout")
        msg = self.queue.get_message("msg-1")

        # Initially not due (scheduled in future)
        self.assertFalse(msg.is_retry_due())

    def test_cleanup_expired(self):
        """Expired messages are cleaned up."""
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat().replace("+00:00", "Z")

        expired = MessageEnvelope(headers=MessageHeaders(
            message_id="old",
            sender_node_id="local",
            sender_timestamp=old_time,
            ttl_seconds=300
        ))
        fresh = MessageEnvelope(headers=MessageHeaders(message_id="new", sender_node_id="local"))

        self.queue.enqueue(expired)
        self.queue.enqueue(fresh)

        removed = self.queue.cleanup_expired()
        self.assertEqual(removed, 1)
        self.assertIsNone(self.queue.get_message("old"))
        self.assertIsNotNone(self.queue.get_message("new"))

    def test_queue_stats(self):
        """Queue statistics are accurate."""
        self.queue.enqueue(MessageEnvelope(headers=MessageHeaders(message_id="1", sender_node_id="local")))
        self.queue.enqueue(MessageEnvelope(headers=MessageHeaders(message_id="2", sender_node_id="local")))

        stats = self.queue.get_stats()
        self.assertEqual(stats["destination"], "remote")
        self.assertEqual(stats["total_messages"], 2)


class TestMessagingTransport(unittest.TestCase):
    """Test messaging transport."""

    def setUp(self):
        self.local = NodeIdentity.create_local("local", NodeRole.WORKER)
        self.transport = MessagingTransport(self.local)

    def test_create_message(self):
        """Can create messages with proper headers."""
        envelope = self.transport.create_message(
            message_type=MessageType.HEARTBEAT.value,
            receiver_node_id="remote",
            payload={"status": "ok"},
            priority=5
        )

        self.assertEqual(envelope.headers.message_type, MessageType.HEARTBEAT.value)
        self.assertEqual(envelope.headers.receiver_node_id, "remote")
        self.assertEqual(envelope.headers.priority, 5)
        self.assertEqual(envelope.payload["status"], "ok")
        self.assertEqual(envelope.headers.sender_node_id, self.local.node_id)

    def test_send_to_trusted_receiver(self):
        """Can send to trusted receiver."""
        envelope = self.transport.create_message(
            message_type=MessageType.STATE_SYNC.value,
            receiver_node_id="remote",
            payload={"data": "value"}
        )

        receiver = NodeTrustState(
            node_id="remote",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        ok, reason = self.transport.send(envelope, receiver)
        self.assertTrue(ok)

    def test_send_rejected_untrusted(self):
        """Send rejected to untrusted receiver."""
        envelope = self.transport.create_message(
            message_type=MessageType.STATE_SYNC.value,
            receiver_node_id="untrusted",
            payload={}
        )

        receiver = NodeTrustState(
            node_id="untrusted",
            trust_status=NodeTrustStatus.UNTRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        ok, reason = self.transport.send(envelope, receiver)
        self.assertFalse(ok)
        self.assertIn("trust", reason.lower())

    def test_receive_from_trusted_sender(self):
        """Can receive from trusted sender."""
        envelope = MessageEnvelope(headers=MessageHeaders(
            message_id="msg-1",
            sender_node_id="trusted-sender"
        ))

        sender = NodeTrustState(
            node_id="trusted-sender",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        ok, reason = self.transport.receive(envelope, sender)
        self.assertTrue(ok)
        self.assertIsNotNone(envelope.headers.receiver_timestamp)

    def test_receive_rejects_expired(self):
        """Expired messages are rejected."""
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat().replace("+00:00", "Z")

        envelope = MessageEnvelope(headers=MessageHeaders(
            message_id="old",
            sender_node_id="sender",
            sender_timestamp=old_time,
            ttl_seconds=300
        ))

        sender = NodeTrustState(
            node_id="sender",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        ok, reason = self.transport.receive(envelope, sender)
        self.assertFalse(ok)
        self.assertIn("expired", reason.lower())

    def test_partitioned_mode_queues_only(self):
        """In partitioned mode, messages are queued only."""
        self.transport.set_mode(TransportMode.PARTITIONED.value)

        envelope = self.transport.create_message(
            message_type=MessageType.HEARTBEAT.value,
            receiver_node_id="remote",
            payload={}
        )

        receiver = NodeTrustState(
            node_id="remote",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        ok, reason = self.transport.send(envelope, receiver)
        self.assertTrue(ok)
        self.assertIn("queued", reason.lower())
        self.assertIn("partitioned", reason.lower())

    def test_process_outbound_returns_ready(self):
        """Process outbound returns messages ready to send."""
        envelope = self.transport.create_message(
            message_type=MessageType.HEARTBEAT.value,
            receiver_node_id="remote",
            payload={}
        )

        receiver = NodeTrustState(
            node_id="remote",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        self.transport.send(envelope, receiver)

        ready = self.transport.process_outbound("remote")
        self.assertIsNotNone(ready)
        self.assertEqual(ready.status, DeliveryStatus.IN_FLIGHT.value)


class TestDegradedPartitionHandler(unittest.TestCase):
    """Test partition handling."""

    def setUp(self):
        self.local = NodeIdentity.create_local("local", NodeRole.WORKER)
        self.transport = MessagingTransport(self.local)
        self.handler = DegradedPartitionHandler(self.transport)

    def test_mark_partitioned(self):
        """Node can be marked as partitioned."""
        self.handler.mark_partitioned("remote-1")
        self.assertTrue(self.handler.is_partitioned("remote-1"))
        self.assertIn("remote-1", self.handler.get_partitioned_nodes())

    def test_mode_changes_on_partition(self):
        """Transport mode changes to degraded on partition."""
        self.handler.mark_partitioned("remote-1")
        self.assertEqual(self.transport._mode, TransportMode.DEGRADED.value)

    def test_mark_healed(self):
        """Node can be marked as healed."""
        self.handler.mark_partitioned("remote-1")
        self.handler.mark_healed("remote-1")

        self.assertFalse(self.handler.is_partitioned("remote-1"))

    def test_mode_restores_when_all_healed(self):
        """Transport mode restores to full when all healed."""
        self.handler.mark_partitioned("remote-1")
        self.handler.mark_partitioned("remote-2")

        self.handler.mark_healed("remote-1")
        self.assertEqual(self.transport._mode, TransportMode.DEGRADED.value)

        self.handler.mark_healed("remote-2")
        self.assertEqual(self.transport._mode, TransportMode.FULL.value)

    def test_queued_messages_retried_on_heal(self):
        """Queued messages are retried when partition heals."""
        # Queue a message
        envelope = MessageEnvelope(headers=MessageHeaders(
            message_id="msg-1",
            sender_node_id="local"
        ))
        queue = self.transport._get_or_create_queue("remote-1")
        queue.enqueue(envelope)
        queue.mark_failed("msg-1", "Partition")

        # Mark partitioned then healed
        self.handler.mark_partitioned("remote-1")
        self.handler.mark_healed("remote-1")

        # Message should be back to pending
        msg = queue.get_message("msg-1")
        self.assertEqual(msg.status, DeliveryStatus.PENDING.value)

    def test_heal_callback(self):
        """Heal callback is triggered on partition heal."""
        healed_nodes = []

        def on_heal(node_id):
            healed_nodes.append(node_id)

        self.handler.on_heal(on_heal)
        self.handler.mark_partitioned("remote-1")
        self.handler.mark_healed("remote-1")

        self.assertIn("remote-1", healed_nodes)


if __name__ == "__main__":
    unittest.main()
