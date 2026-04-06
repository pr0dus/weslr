"""Tests for Remote Node Handshake Protocol (v65)

Behavioral tests for handshake/session-establishment layer.
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.remote_node_handshake import (
    HandshakeRequest,
    HandshakeResponse,
    HandshakeState,
    HandshakeEventType,
    NodeIdentityConfirmation,
    TrustHealthEligibility,
    ProtocolCompatibility,
    SessionAcceptanceRefusal,
    HandshakeAuditTrace,
    HandshakeCorrelation,
    HandshakeProtocol,
)
from weslr.node_identity import (
    NodeIdentity,
    NodeTrustState,
    NodeRole,
    NodeTrustStatus,
    NodeHealthStatus,
)
from weslr.node_registry import NodeRegistry


class TestHandshakeRequest(unittest.TestCase):
    """Test handshake request model."""

    def test_creation_defaults(self):
        """Request created with required fields."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="node-a",
            target_node_id="node-b",
            protocol_version="1.0.0"
        )
        
        self.assertEqual(request.handshake_id, "hs-1")
        self.assertEqual(request.source_node_id, "node-a")
        self.assertEqual(request.target_node_id, "node-b")
        self.assertEqual(request.protocol_version, "1.0.0")

    def test_mark_sent(self):
        """Sent timestamp recorded."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="node-a",
            target_node_id="node-b",
            protocol_version="1.0.0"
        )
        
        request.mark_sent()
        
        self.assertIsNotNone(request.sent_at)

    def test_is_expired(self):
        """Expiry checked correctly."""
        past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat().replace("+00:00", "Z")
        
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="node-a",
            target_node_id="node-b",
            protocol_version="1.0.0",
            expires_at=past
        )
        
        self.assertTrue(request.is_expired())

    def test_serialization(self):
        """Round-trip serialization works."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="node-a",
            target_node_id="node-b",
            protocol_version="1.0.0",
            supported_versions=["1.0.0", "0.9.0"],
            message="Hello"
        )
        
        data = request.to_dict()
        restored = HandshakeRequest.from_dict(data)
        
        self.assertEqual(restored.handshake_id, "hs-1")
        self.assertEqual(restored.supported_versions, ["1.0.0", "0.9.0"])


class TestHandshakeResponse(unittest.TestCase):
    """Test handshake response model."""

    def test_creation_defaults(self):
        """Response created with acceptance status."""
        response = HandshakeResponse(
            response_id="resp-1",
            handshake_id="hs-1",
            source_node_id="node-b",
            target_node_id="node-a",
            accepted=True
        )
        
        self.assertEqual(response.response_id, "resp-1")
        self.assertTrue(response.accepted)
        self.assertEqual(response.current_state, HandshakeState.PENDING.value)

    def test_mark_sent(self):
        """Sent transitions state."""
        response = HandshakeResponse(
            response_id="resp-1",
            handshake_id="hs-1",
            source_node_id="node-b",
            target_node_id="node-a",
            accepted=True
        )
        
        response.mark_sent()
        
        self.assertIsNotNone(response.sent_at)
        self.assertEqual(response.current_state, HandshakeState.SENT.value)

    def test_mark_received(self):
        """Received transitions state."""
        response = HandshakeResponse(
            response_id="resp-1",
            handshake_id="hs-1",
            source_node_id="node-b",
            target_node_id="node-a",
            accepted=True
        )
        
        response.mark_received()
        
        self.assertIsNotNone(response.received_at)
        self.assertEqual(response.current_state, HandshakeState.RECEIVED.value)

    def test_is_terminal(self):
        """Terminal states detected."""
        # Terminal states are COMPLETED, FAILED, REFUSED, EXPIRED
        for state in [HandshakeState.COMPLETED.value, HandshakeState.FAILED.value, 
                      HandshakeState.REFUSED.value, HandshakeState.EXPIRED.value]:
            response = HandshakeResponse(
                response_id=f"resp-{state}",
                handshake_id="hs-1",
                source_node_id="node-b",
                target_node_id="node-a",
                accepted=True
            )
            response.current_state = state
            self.assertTrue(response.is_terminal(), f"State {state} should be terminal")

    def test_serialization(self):
        """Round-trip serialization works."""
        response = HandshakeResponse(
            response_id="resp-1",
            handshake_id="hs-1",
            source_node_id="node-b",
            target_node_id="node-a",
            accepted=True,
            session_id="sess-1",
            protocol_version="1.0.0"
        )
        
        data = response.to_dict()
        restored = HandshakeResponse.from_dict(data)
        
        self.assertEqual(restored.session_id, "sess-1")
        self.assertEqual(restored.protocol_version, "1.0.0")


class TestNodeIdentityConfirmation(unittest.TestCase):
    """Test identity confirmation."""

    def setUp(self):
        self.registry = NodeRegistry()
        self.local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=self.local.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        self.registry.register_local(self.local, local_trust)
        
        self.confirmation = NodeIdentityConfirmation(self.registry)

    def test_confirm_identity_success(self):
        """Identity confirmed for registered node."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id=self.local.node_id,
            target_node_id="remote",
            protocol_version="1.0.0"
        )
        
        result = self.confirmation.confirm_identity(request)
        
        self.assertTrue(result.confirmed)
        self.assertIsNotNone(result.identity)

    def test_confirm_identity_fails_unknown(self):
        """Identity fails for unknown node."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="unknown",
            target_node_id="local",
            protocol_version="1.0.0"
        )
        
        result = self.confirmation.confirm_identity(request)
        
        self.assertFalse(result.confirmed)
        self.assertIn("not in registry", result.errors[0])


class TestTrustHealthEligibility(unittest.TestCase):
    """Test trust/health eligibility."""

    def setUp(self):
        self.registry = NodeRegistry()
        
        # Trusted healthy node
        self.trusted = NodeIdentity.create_local("trusted", NodeRole.WORKER)
        self.trusted.node_id = "trusted-1"
        self.trusted.is_local = False
        trusted_trust = NodeTrustState(
            node_id="trusted-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(self.trusted, trusted_trust)
        
        # Provisional node
        self.provisional = NodeIdentity.create_local("provisional", NodeRole.WORKER)
        self.provisional.node_id = "provisional-1"
        self.provisional.is_local = False
        prov_trust = NodeTrustState(
            node_id="provisional-1",
            trust_status=NodeTrustStatus.PROVISIONAL.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(self.provisional, prov_trust)
        
        # Unhealthy node
        self.unhealthy = NodeIdentity.create_local("unhealthy", NodeRole.WORKER)
        self.unhealthy.node_id = "unhealthy-1"
        self.unhealthy.is_local = False
        unh_trust = NodeTrustState(
            node_id="unhealthy-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.UNHEALTHY.value
        )
        self.registry.register_remote(self.unhealthy, unh_trust)
        
        self.eligibility = TrustHealthEligibility(self.registry)

    def test_eligible_trusted_healthy(self):
        """Trusted healthy node is eligible."""
        result = self.eligibility.check_eligibility("trusted-1")
        
        self.assertTrue(result.eligible)
        self.assertTrue(result.trust_passed)
        self.assertTrue(result.health_passed)

    def test_ineligible_provisional(self):
        """Provisional trust level fails."""
        result = self.eligibility.check_eligibility("provisional-1")
        
        self.assertFalse(result.eligible)
        self.assertFalse(result.trust_passed)

    def test_ineligible_unhealthy(self):
        """Unhealthy status fails."""
        result = self.eligibility.check_eligibility("unhealthy-1")
        
        self.assertFalse(result.eligible)
        self.assertTrue(result.trust_passed)
        self.assertFalse(result.health_passed)

    def test_ineligible_unknown(self):
        """Unknown node fails."""
        result = self.eligibility.check_eligibility("unknown")
        
        self.assertFalse(result.eligible)
        self.assertIn("not in registry", result.errors[0])


class TestProtocolCompatibility(unittest.TestCase):
    """Test protocol compatibility."""

    def setUp(self):
        self.compat = ProtocolCompatibility(
            local_version="1.0.0",
            supported_versions=["1.0.0", "0.9.0"]
        )

    def test_version_compatible_exact(self):
        """Exact version match is compatible."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="node-a",
            target_node_id="node-b",
            protocol_version="1.0.0"
        )
        
        result = self.compat.check_version(request)
        
        self.assertTrue(result.compatible)
        self.assertEqual(result.agreed_version, "1.0.0")

    def test_version_compatible_common(self):
        """Common version found."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="node-a",
            target_node_id="node-b",
            protocol_version="0.9.0",
            supported_versions=["0.9.0", "0.8.0"]
        )
        
        result = self.compat.check_version(request)
        
        self.assertTrue(result.compatible)
        self.assertEqual(result.agreed_version, "0.9.0")

    def test_version_incompatible(self):
        """No common version is incompatible."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="node-a",
            target_node_id="node-b",
            protocol_version="2.0.0",
            supported_versions=["2.0.0", "1.5.0"]
        )
        
        result = self.compat.check_version(request)
        
        self.assertFalse(result.compatible)
        self.assertIsNone(result.agreed_version)

    def test_capabilities_match(self):
        """Capabilities matched correctly."""
        offered = [{"id": "cap-1"}, {"id": "cap-2"}, {"id": "cap-3"}]
        required = [{"id": "cap-1"}, {"id": "cap-2"}]
        
        accepted, rejected = self.compat.check_capabilities(offered, required)
        
        self.assertEqual(len(accepted), 2)
        self.assertEqual(len(rejected), 1)


class TestSessionAcceptanceRefusal(unittest.TestCase):
    """Test session acceptance/refusal."""

    def setUp(self):
        self.handler = SessionAcceptanceRefusal()

    def test_accept_session(self):
        """Session accepted with session ID."""
        result = self.handler.accept_session(
            handshake_id="hs-1",
            agreed_version="1.0.0",
            accepted_capabilities=[],
            metadata={"source": "node-a"}
        )
        
        self.assertTrue(result.accepted)
        self.assertIsNotNone(result.session_id)

    def test_refuse_session(self):
        """Session refused with reason."""
        result = self.handler.refuse_session(
            handshake_id="hs-1",
            reason="Trust insufficient"
        )
        
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "Trust insufficient")


class TestHandshakeAuditTrace(unittest.TestCase):
    """Test handshake audit trace."""

    def setUp(self):
        self.trace = HandshakeAuditTrace("local")

    def test_log_event(self):
        """Events can be logged."""
        event = self.trace.log_event(
            handshake_id="hs-1",
            event_type=HandshakeEventType.REQUEST_CREATED.value
        )
        
        self.assertEqual(event.handshake_id, "hs-1")
        self.assertEqual(event.event_type, HandshakeEventType.REQUEST_CREATED.value)

    def test_get_events(self):
        """Events retrieved by handshake ID."""
        self.trace.log_event("hs-1", HandshakeEventType.REQUEST_CREATED.value)
        self.trace.log_event("hs-1", HandshakeEventType.IDENTITY_CONFIRMED.value)
        self.trace.log_event("hs-2", HandshakeEventType.REQUEST_CREATED.value)
        
        events = self.trace.get_events("hs-1")
        self.assertEqual(len(events), 2)

    def test_get_trace(self):
        """Full trace retrieved."""
        self.trace.log_event("hs-1", HandshakeEventType.REQUEST_CREATED.value)
        self.trace.log_event("hs-1", HandshakeEventType.HANDSHAKE_ACCEPTED.value)
        
        trace = self.trace.get_trace("hs-1")
        self.assertEqual(len(trace), 2)

    def test_get_stats(self):
        """Statistics retrieved."""
        self.trace.log_event("hs-1", HandshakeEventType.REQUEST_CREATED.value)
        self.trace.log_event("hs-2", HandshakeEventType.REQUEST_CREATED.value)
        
        stats = self.trace.get_stats()
        self.assertEqual(stats["total_events"], 2)
        self.assertEqual(stats["handshakes_tracked"], 2)


class TestHandshakeCorrelation(unittest.TestCase):
    """Test handshake correlation."""

    def test_link_request(self):
        """Request linked to correlation."""
        corr = HandshakeCorrelation(handshake_id="hs-1")
        
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="node-a",
            target_node_id="node-b",
            protocol_version="1.0.0"
        )
        
        corr.link_request(request)
        
        self.assertEqual(corr.request_id, "hs-1")
        self.assertEqual(corr.source_node_id, "node-a")
        self.assertEqual(corr.target_node_id, "node-b")

    def test_link_response(self):
        """Response linked to correlation."""
        corr = HandshakeCorrelation(handshake_id="hs-1")
        
        response = HandshakeResponse(
            response_id="resp-1",
            handshake_id="hs-1",
            source_node_id="node-b",
            target_node_id="node-a",
            accepted=True,
            session_id="sess-1"
        )
        
        corr.link_response(response)
        
        self.assertEqual(corr.response_id, "resp-1")
        self.assertEqual(corr.session_id, "sess-1")


class TestHandshakeProtocol(unittest.TestCase):
    """Test handshake protocol."""

    def setUp(self):
        self.registry = NodeRegistry()
        
        # Source node
        self.source = NodeIdentity.create_local("source", NodeRole.CONTROLLER)
        self.source.node_id = "source-1"
        self.source.is_local = False
        source_trust = NodeTrustState(
            node_id="source-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(self.source, source_trust)
        
        # Target node (local)
        self.target = NodeIdentity.create_local("target", NodeRole.WORKER)
        target_trust = NodeTrustState(
            node_id="target",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_local(self.target, target_trust)
        
        # Protocol (as target)
        self.protocol = HandshakeProtocol(
            local_node_id="target",
            registry=self.registry,
            local_version="1.0.0",
            supported_versions=["1.0.0"]
        )

    def test_create_request(self):
        """Handshake request created."""
        request = self.protocol.create_request(
            target_node_id="source-1",
            message="Hello"
        )
        
        self.assertIsNotNone(request.handshake_id)
        self.assertEqual(request.source_node_id, "target")
        self.assertEqual(request.target_node_id, "source-1")

    def test_send_request(self):
        """Request sent tracked."""
        request = self.protocol.create_request(target_node_id="source-1")
        self.protocol.send_request(request)
        
        self.assertIsNotNone(request.sent_at)

    def test_receive_request_success(self):
        """Valid request received."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="source-1",
            target_node_id="target",
            protocol_version="1.0.0"
        )
        
        success, errors = self.protocol.receive_request(request)
        
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)

    def test_receive_request_expired(self):
        """Expired request rejected."""
        past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat().replace("+00:00", "Z")
        
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="source-1",
            target_node_id="target",
            protocol_version="1.0.0",
            expires_at=past
        )
        
        success, errors = self.protocol.receive_request(request)
        
        self.assertFalse(success)
        self.assertIn("expired", errors[0].lower())

    def test_evaluate_request_eligible(self):
        """Eligible request evaluated."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="source-1",
            target_node_id="target",
            protocol_version="1.0.0"
        )
        
        eligible, reason, agreed = self.protocol.evaluate_request(request)
        
        self.assertTrue(eligible)
        self.assertIsNone(reason)
        self.assertEqual(agreed, "1.0.0")

    def test_create_response_accepted(self):
        """Acceptance response created."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="source-1",
            target_node_id="target",
            protocol_version="1.0.0"
        )
        self.protocol._requests["hs-1"] = request
        
        response = self.protocol.create_response(
            request=request,
            accepted=True,
            agreed_version="1.0.0"
        )
        
        self.assertTrue(response.accepted)
        self.assertIsNotNone(response.session_id)

    def test_create_response_refused(self):
        """Refusal response created."""
        request = HandshakeRequest(
            handshake_id="hs-1",
            source_node_id="source-1",
            target_node_id="target",
            protocol_version="1.0.0"
        )
        
        response = self.protocol.create_response(
            request=request,
            accepted=False,
            reason="Trust insufficient"
        )
        
        self.assertFalse(response.accepted)
        self.assertEqual(response.reason, "Trust insufficient")
        self.assertIsNone(response.session_id)

    def test_end_to_end_handshake_accepted(self):
        """Complete accepted handshake flow."""
        # Create and send request (as source)
        source_protocol = HandshakeProtocol(
            local_node_id="source-1",
            registry=self.registry,
            local_version="1.0.0",
            supported_versions=["1.0.0"]
        )
        
        request = source_protocol.create_request(
            target_node_id="target",
            message="Hello from source"
        )
        source_protocol.send_request(request)
        
        # Receive request (as target)
        success, errors = self.protocol.receive_request(request)
        self.assertTrue(success)
        
        # Evaluate (as target)
        eligible, reason, agreed = self.protocol.evaluate_request(request)
        self.assertTrue(eligible)
        
        # Create and send response (as target)
        response = self.protocol.create_response(
            request=request,
            accepted=True,
            agreed_version=agreed
        )
        self.protocol.send_response(response)
        
        # Receive response (as source)
        success, errors = source_protocol.receive_response(response, expected_handshake_id=request.handshake_id)
        self.assertTrue(success)
        
        # Verify session established
        self.assertTrue(response.accepted)
        self.assertIsNotNone(response.session_id)


if __name__ == "__main__":
    unittest.main()
