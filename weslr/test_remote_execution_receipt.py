"""Tests for Remote Execution Receipt / Acknowledgment Protocol (v63)

Behavioral tests for receipt acknowledgment layer.
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.remote_execution_receipt import (
    ExecutionReceipt,
    ReceiptType,
    AcknowledgmentState,
    ReceiptEventType,
    ReceiptValidation,
    ReceiptValidationResult,
    CompletionConfirmation,
    FailureConfirmation,
    RollbackAcknowledgment,
    ReceiptAuditTrace,
    ReceiptProtocol,
)
from weslr.controlled_execution_envelope import ExecutionLifecycleState


class TestExecutionReceipt(unittest.TestCase):
    """Test execution receipt model."""

    def test_creation_defaults(self):
        """Receipt created in PENDING acknowledgment state."""
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b"
        )
        
        self.assertEqual(receipt.acknowledgment_state, AcknowledgmentState.PENDING.value)
        self.assertEqual(receipt.receipt_type, ReceiptType.DISPATCH_RECEIVED.value)
        self.assertEqual(receipt.request_id, "req-1")

    def test_mark_sent(self):
        """Sent receipt tracked."""
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b"
        )
        
        receipt.mark_sent()
        
        self.assertIsNotNone(receipt.sent_at)
        self.assertEqual(receipt.acknowledgment_state, AcknowledgmentState.PENDING.value)

    def test_mark_received(self):
        """Received receipt tracked."""
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b"
        )
        
        receipt.mark_received()
        
        self.assertIsNotNone(receipt.received_at)
        self.assertEqual(receipt.acknowledgment_state, AcknowledgmentState.RECEIVED.value)

    def test_mark_validated(self):
        """Validation tracked."""
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b"
        )
        
        receipt.mark_validated(True)
        
        self.assertTrue(receipt.is_valid)
        self.assertEqual(receipt.acknowledgment_state, AcknowledgmentState.VALIDATED.value)

    def test_mark_validated_failure(self):
        """Validation failure tracked."""
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b"
        )
        
        receipt.mark_validated(False, ["Expired", "Bad signature"])
        
        self.assertFalse(receipt.is_valid)
        self.assertEqual(len(receipt.validation_errors), 2)
        self.assertEqual(receipt.acknowledgment_state, AcknowledgmentState.REFUSED.value)

    def test_mark_acknowledged(self):
        """Acknowledgment tracked."""
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b"
        )
        
        receipt.mark_acknowledged()
        
        self.assertIsNotNone(receipt.acknowledged_at)
        self.assertEqual(receipt.acknowledgment_state, AcknowledgmentState.ACKNOWLEDGED.value)

    def test_is_terminal(self):
        """Terminal states detected."""
        terminal_receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b",
            acknowledgment_state=AcknowledgmentState.ACKNOWLEDGED.value
        )
        
        self.assertTrue(terminal_receipt.is_terminal())
        
        pending_receipt = ExecutionReceipt(
            receipt_id="rec-2",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b",
            acknowledgment_state=AcknowledgmentState.PENDING.value
        )
        
        self.assertFalse(pending_receipt.is_terminal())

    def test_acknowledgment_history(self):
        """State transitions logged."""
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b"
        )
        
        receipt.mark_received()
        receipt.mark_validated(True)
        receipt.mark_acknowledged()
        
        self.assertEqual(len(receipt.acknowledgment_history), 3)
        self.assertEqual(receipt.acknowledgment_history[0]["to"], AcknowledgmentState.RECEIVED.value)
        self.assertEqual(receipt.acknowledgment_history[-1]["to"], AcknowledgmentState.ACKNOWLEDGED.value)

    def test_serialization(self):
        """Round-trip serialization works."""
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b",
            envelope_state=ExecutionLifecycleState.DISPATCHED.value,
            message="Dispatch received",
            details={"seq": 1}
        )
        
        data = receipt.to_dict()
        restored = ExecutionReceipt.from_dict(data)
        
        self.assertEqual(restored.receipt_id, "rec-1")
        self.assertEqual(restored.details["seq"], 1)


class TestReceiptValidation(unittest.TestCase):
    """Test receipt validation."""

    def test_valid_receipt(self):
        """Valid receipt passes."""
        validator = ReceiptValidation(
            expected_request_id="req-1",
            expected_source="node-a"
        )
        
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b"
        )
        
        result = validator.validate(receipt)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

    def test_request_id_mismatch(self):
        """Wrong request ID fails."""
        validator = ReceiptValidation(expected_request_id="req-1")
        
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-2",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b"
        )
        
        result = validator.validate(receipt)
        self.assertFalse(result.is_valid)
        self.assertIn("Request ID mismatch", str(result.errors))

    def test_source_mismatch(self):
        """Wrong source fails."""
        validator = ReceiptValidation(expected_source="node-a")
        
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-b",
            target_node_id="node-c"
        )
        
        result = validator.validate(receipt)
        self.assertFalse(result.is_valid)
        self.assertIn("Source mismatch", str(result.errors))

    def test_expired_receipt(self):
        """Old receipt fails freshness check."""
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=7200)).isoformat().replace("+00:00", "Z")
        
        validator = ReceiptValidation(max_age_seconds=3600)
        
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.DISPATCH_RECEIVED.value,
            source_node_id="node-a",
            target_node_id="node-b",
            created_at=old_time
        )
        
        result = validator.validate(receipt)
        self.assertFalse(result.is_valid)
        self.assertIn("expired", str(result.errors).lower())


class TestCompletionConfirmation(unittest.TestCase):
    """Test completion confirmation."""

    def test_create_receipt(self):
        """Completion receipt created."""
        confirmation = CompletionConfirmation(
            result_summary={"status": "success", "records": 100},
            metrics={"duration_ms": 500},
            artifacts=[{"name": "output.json"}]
        )
        
        receipt = confirmation.create_receipt(
            request_id="req-1",
            source_node="node-b",
            target_node="node-a",
            message="Sync completed"
        )
        
        self.assertEqual(receipt.receipt_type, ReceiptType.COMPLETION_CONFIRMED.value)
        self.assertEqual(receipt.request_id, "req-1")
        self.assertEqual(receipt.details["result_summary"]["records"], 100)


class TestFailureConfirmation(unittest.TestCase):
    """Test failure confirmation."""

    def test_create_receipt(self):
        """Failure receipt created."""
        failure = FailureConfirmation(
            error_code="TIMEOUT",
            error_message="Execution timed out",
            recoverable=True
        )
        
        receipt = failure.create_receipt(
            request_id="req-1",
            source_node="node-b",
            target_node="node-a"
        )
        
        self.assertEqual(receipt.receipt_type, ReceiptType.FAILURE_CONFIRMED.value)
        self.assertEqual(receipt.details["error_code"], "TIMEOUT")
        self.assertTrue(receipt.details["recoverable"])


class TestRollbackAcknowledgment(unittest.TestCase):
    """Test rollback acknowledgment."""

    def test_create_initiation_receipt(self):
        """Rollback initiation receipt created."""
        rollback = RollbackAcknowledgment()
        
        receipt = rollback.create_initiation_receipt(
            request_id="req-1",
            source_node="node-b",
            target_node="node-a",
            reason="Execution failed"
        )
        
        self.assertEqual(receipt.receipt_type, ReceiptType.ROLLBACK_ACKNOWLEDGED.value)
        self.assertEqual(receipt.details["rollback_status"], "initiated")

    def test_create_completion_receipt_success(self):
        """Rollback completion receipt created for success."""
        rollback = RollbackAcknowledgment()
        
        receipt = rollback.create_completion_receipt(
            request_id="req-1",
            source_node="node-b",
            target_node="node-a",
            success=True,
            details={"records_restored": 100}
        )
        
        self.assertEqual(receipt.receipt_type, ReceiptType.ROLLBACK_COMPLETED.value)
        self.assertEqual(receipt.details["rollback_status"], "completed")


class TestReceiptAuditTrace(unittest.TestCase):
    """Test receipt audit trace."""

    def setUp(self):
        self.trace = ReceiptAuditTrace("local")

    def test_log_event(self):
        """Events can be logged."""
        event = self.trace.log_event(
            receipt_id="rec-1",
            request_id="req-1",
            event_type=ReceiptEventType.RECEIPT_CREATED.value
        )
        
        self.assertEqual(event.receipt_id, "rec-1")
        self.assertEqual(event.request_id, "req-1")

    def test_get_events_for_receipt(self):
        """Events retrieved by receipt ID."""
        self.trace.log_event("rec-1", "req-1", ReceiptEventType.RECEIPT_CREATED.value)
        self.trace.log_event("rec-1", "req-1", ReceiptEventType.RECEIPT_SENT.value)
        self.trace.log_event("rec-2", "req-1", ReceiptEventType.RECEIPT_CREATED.value)
        
        events = self.trace.get_events_for_receipt("rec-1")
        self.assertEqual(len(events), 2)

    def test_get_events_for_request(self):
        """Events retrieved by request ID."""
        self.trace.log_event("rec-1", "req-1", ReceiptEventType.RECEIPT_CREATED.value)
        self.trace.log_event("rec-2", "req-1", ReceiptEventType.RECEIPT_CREATED.value)
        self.trace.log_event("rec-3", "req-2", ReceiptEventType.RECEIPT_CREATED.value)
        
        events = self.trace.get_events_for_request("req-1")
        self.assertEqual(len(events), 2)

    def test_get_stats(self):
        """Statistics retrieved."""
        self.trace.log_event("rec-1", "req-1", ReceiptEventType.RECEIPT_CREATED.value)
        self.trace.log_event("rec-2", "req-2", ReceiptEventType.RECEIPT_CREATED.value)
        
        stats = self.trace.get_stats()
        self.assertEqual(stats["total_events"], 2)
        self.assertEqual(stats["receipts_tracked"], 2)


class TestReceiptProtocol(unittest.TestCase):
    """Test receipt protocol."""

    def setUp(self):
        self.protocol = ReceiptProtocol(local_node_id="node-b")

    def test_create_dispatch_received_receipt(self):
        """Dispatch received receipt created."""
        receipt = self.protocol.create_dispatch_received_receipt(
            request_id="req-1",
            original_source="node-a",
            envelope_state=ExecutionLifecycleState.DISPATCHED.value
        )
        
        self.assertEqual(receipt.receipt_type, ReceiptType.DISPATCH_RECEIVED.value)
        self.assertEqual(receipt.source_node_id, "node-b")
        self.assertEqual(receipt.target_node_id, "node-a")

    def test_create_execution_accepted_receipt(self):
        """Execution accepted receipt created."""
        receipt = self.protocol.create_execution_accepted_receipt(
            request_id="req-1",
            original_source="node-a"
        )
        
        self.assertEqual(receipt.receipt_type, ReceiptType.EXECUTION_ACCEPTED.value)

    def test_create_execution_refused_receipt(self):
        """Execution refused receipt created."""
        receipt = self.protocol.create_execution_refused_receipt(
            request_id="req-1",
            original_source="node-a",
            reason="Insufficient capacity"
        )
        
        self.assertEqual(receipt.receipt_type, ReceiptType.EXECUTION_REFUSED.value)
        self.assertIn("Insufficient capacity", receipt.message)

    def test_send_receipt(self):
        """Receipt sending tracked."""
        receipt = self.protocol.create_dispatch_received_receipt(
            request_id="req-1",
            original_source="node-a",
            envelope_state=ExecutionLifecycleState.DISPATCHED.value
        )
        
        self.protocol.send_receipt(receipt)
        
        self.assertIsNotNone(receipt.sent_at)

    def test_receive_and_validate_valid(self):
        """Valid receipt received and validated."""
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-1",
            receipt_type=ReceiptType.COMPLETION_CONFIRMED.value,
            source_node_id="node-b",
            target_node_id="node-a"
        )
        
        result = self.protocol.receive_receipt(receipt, expected_request_id="req-1")
        
        self.assertTrue(result.is_valid)
        self.assertTrue(receipt.is_valid)

    def test_receive_and_validate_invalid(self):
        """Invalid receipt rejected."""
        receipt = ExecutionReceipt(
            receipt_id="rec-1",
            request_id="req-2",  # Wrong request ID
            receipt_type=ReceiptType.COMPLETION_CONFIRMED.value,
            source_node_id="node-b",
            target_node_id="node-a"
        )
        
        result = self.protocol.receive_receipt(receipt, expected_request_id="req-1")
        
        self.assertFalse(result.is_valid)
        self.assertFalse(receipt.is_valid)

    def test_acknowledge_receipt(self):
        """Receipt acknowledged."""
        receipt = self.protocol.create_dispatch_received_receipt(
            request_id="req-1",
            original_source="node-a",
            envelope_state=ExecutionLifecycleState.DISPATCHED.value
        )
        
        self.protocol.acknowledge_receipt(receipt)
        
        self.assertEqual(receipt.acknowledgment_state, AcknowledgmentState.ACKNOWLEDGED.value)

    def test_get_receipts_for_request(self):
        """Receipts retrieved by request."""
        r1 = self.protocol.create_dispatch_received_receipt("req-1", "node-a", ExecutionLifecycleState.DISPATCHED.value)
        r2 = self.protocol.create_execution_accepted_receipt("req-1", "node-a")
        r3 = self.protocol.create_dispatch_received_receipt("req-2", "node-a", ExecutionLifecycleState.DISPATCHED.value)
        
        receipts = self.protocol.get_receipts_for_request("req-1")
        
        self.assertEqual(len(receipts), 2)
        receipt_ids = {r.receipt_id for r in receipts}
        self.assertIn(r1.receipt_id, receipt_ids)
        self.assertIn(r2.receipt_id, receipt_ids)

    def test_full_receipt_flow(self):
        """End-to-end receipt flow."""
        # Target creates dispatch received receipt
        receipt = self.protocol.create_dispatch_received_receipt(
            request_id="req-1",
            original_source="node-a",
            envelope_state=ExecutionLifecycleState.DISPATCHED.value
        )
        
        # Target sends receipt
        self.protocol.send_receipt(receipt)
        
        # Source receives and validates
        result = self.protocol.receive_receipt(receipt, expected_request_id="req-1", expected_source="node-b")
        self.assertTrue(result.is_valid)
        
        # Source acknowledges
        self.protocol.acknowledge_receipt(receipt)
        
        self.assertEqual(receipt.acknowledgment_state, AcknowledgmentState.ACKNOWLEDGED.value)


if __name__ == "__main__":
    unittest.main()
