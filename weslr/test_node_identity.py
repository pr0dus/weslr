"""Tests for Node Identity and Registry (v57)

Behavioral tests for distributed multi-node foundation slice.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.node_identity import (
    NodeIdentity,
    NodeIdentityManager,
    NodeCapability,
    NodeCapabilitySummary,
    NodeTrustState,
    NodeRole,
    NodeTrustStatus,
    NodeHealthStatus,
    NodeLocationType,
    create_default_capabilities,
    generate_node_id
)
from weslr.node_registry import (
    NodeRegistry,
    NodeRegistryEntry,
    NodeAvailabilityTracker
)


class TestNodeIdentity(unittest.TestCase):
    """Test node identity creation and management."""
    
    def test_create_local_identity(self):
        """Local identity has correct defaults."""
        identity = NodeIdentity.create_local("test-node", NodeRole.WORKER)
        
        self.assertIsNotNone(identity.node_id)
        self.assertEqual(identity.node_name, "test-node")
        self.assertEqual(identity.node_role, NodeRole.WORKER.value)
        self.assertTrue(identity.is_local)
        self.assertFalse(identity.is_controller)
        self.assertEqual(identity.location_type, NodeLocationType.LOCAL.value)
        self.assertEqual(identity.version, "v57")
    
    def test_controller_role_sets_flag(self):
        """Controller role sets is_controller flag."""
        identity = NodeIdentity.create_local("ctrl", NodeRole.CONTROLLER)
        
        self.assertTrue(identity.is_controller)
        self.assertEqual(identity.node_role, NodeRole.CONTROLLER.value)
    
    def test_identity_serialization(self):
        """Identity serializes and deserializes correctly."""
        original = NodeIdentity.create_local("test", NodeRole.WORKER)
        original.hostname = "testhost"
        original.ip_address = "192.168.1.1"
        original.port = 8080
        
        data = original.to_dict()
        restored = NodeIdentity.from_dict(data)
        
        self.assertEqual(restored.node_id, original.node_id)
        self.assertEqual(restored.node_name, original.node_name)
        self.assertEqual(restored.node_role, original.node_role)
        self.assertEqual(restored.hostname, original.hostname)
        self.assertEqual(restored.ip_address, original.ip_address)
        self.assertEqual(restored.port, original.port)
        self.assertEqual(restored.is_local, original.is_local)
    
    def test_generate_node_id_unique(self):
        """Generated IDs are unique."""
        ids = [generate_node_id() for _ in range(100)]
        self.assertEqual(len(set(ids)), 100)


class TestNodeCapability(unittest.TestCase):
    """Test capability management."""
    
    def test_capability_summary_creation(self):
        """Capability summary tracks node capabilities."""
        caps = [
            NodeCapability("compute", "cpu", "1.0", 8.0, True),
            NodeCapability("storage", "disk", "2.0", 1000.0, True),
            NodeCapability("network", "http", "1.0", None, False)  # unavailable
        ]
        
        summary = NodeCapabilitySummary(node_id="test-node", capabilities=caps)
        
        self.assertEqual(len(summary.capabilities), 3)
        self.assertEqual(len(summary.get_available_capabilities()), 2)
    
    def test_has_capability_check(self):
        """Capability presence check works."""
        caps = [
            NodeCapability("compute", "cpu", "1.0", 8.0, True),
            NodeCapability("compute", "gpu", "2.0", 1.0, True),
        ]
        
        summary = NodeCapabilitySummary(node_id="test-node", capabilities=caps)
        
        self.assertTrue(summary.has_capability("compute", "cpu"))
        self.assertTrue(summary.has_capability("compute", "gpu"))
        self.assertTrue(summary.has_capability("compute"))  # any compute
        self.assertFalse(summary.has_capability("storage"))
        self.assertFalse(summary.has_capability("compute", "tpu"))
    
    def test_get_capability_specific(self):
        """Get specific capability by type and name."""
        caps = [
            NodeCapability("compute", "cpu", "1.0", 8.0, True),
        ]
        
        summary = NodeCapabilitySummary(node_id="test-node", capabilities=caps)
        cap = summary.get_capability("compute", "cpu")
        
        self.assertIsNotNone(cap)
        self.assertEqual(cap.version, "1.0")
        self.assertEqual(cap.capacity, 8.0)
        self.assertIsNone(summary.get_capability("compute", "gpu"))
    
    def test_capability_serialization(self):
        """Capability summary serializes and deserializes."""
        caps = [
            NodeCapability("compute", "cpu", "1.0", 8.0, True, {"cores": 8}),
        ]
        
        original = NodeCapabilitySummary(node_id="test-node", capabilities=caps)
        data = original.to_dict()
        restored = NodeCapabilitySummary.from_dict(data)
        
        self.assertEqual(restored.node_id, original.node_id)
        self.assertEqual(len(restored.capabilities), 1)
        self.assertEqual(restored.capabilities[0].metadata["cores"], 8)


class TestNodeTrustState(unittest.TestCase):
    """Test trust state management."""
    
    def test_trust_state_defaults(self):
        """Trust state has correct defaults."""
        state = NodeTrustState(node_id="test-node")
        
        self.assertEqual(state.trust_status, NodeTrustStatus.PENDING.value)
        self.assertEqual(state.health_status, NodeHealthStatus.UNKNOWN.value)
        self.assertEqual(state.trust_score, 0.0)
        self.assertEqual(state.consecutive_failures, 0)
    
    def test_is_trusted_check(self):
        """Trusted status check works."""
        state = NodeTrustState(node_id="test-node")
        
        self.assertFalse(state.is_trusted())
        
        state.trust_status = NodeTrustStatus.TRUSTED.value
        self.assertTrue(state.is_trusted())
    
    def test_can_communicate(self):
        """Communication permission check works."""
        state = NodeTrustState(node_id="test-node")
        
        # PENDING cannot communicate
        self.assertFalse(state.can_communicate())
        
        # TRUSTED + HEALTHY can communicate
        state.trust_status = NodeTrustStatus.TRUSTED.value
        state.health_status = NodeHealthStatus.HEALTHY.value
        self.assertTrue(state.can_communicate())
        
        # TRUSTED + OFFLINE cannot communicate
        state.health_status = NodeHealthStatus.OFFLINE.value
        self.assertFalse(state.can_communicate())
        
        # UNTRUSTED cannot communicate
        state.trust_status = NodeTrustStatus.UNTRUSTED.value
        state.health_status = NodeHealthStatus.HEALTHY.value
        self.assertFalse(state.can_communicate())
        
        # PROVISIONAL + HEALTHY can communicate
        state.trust_status = NodeTrustStatus.PROVISIONAL.value
        self.assertTrue(state.can_communicate())
    
    def test_trust_update_with_history(self):
        """Trust updates create history entries."""
        state = NodeTrustState(node_id="test-node")
        
        state.update_trust(NodeTrustStatus.PROVISIONAL.value, "Initial verification")
        state.update_trust(NodeTrustStatus.TRUSTED.value, "Full verification passed")
        
        self.assertEqual(len(state.status_history), 2)
        self.assertEqual(state.status_history[0]["type"], "trust")
        self.assertEqual(state.status_history[0]["from"], NodeTrustStatus.PENDING.value)
        self.assertEqual(state.status_history[0]["to"], NodeTrustStatus.PROVISIONAL.value)
    
    def test_health_update_with_history(self):
        """Health updates create history entries."""
        state = NodeTrustState(node_id="test-node")
        
        state.update_health(NodeHealthStatus.HEALTHY.value, "System check passed")
        state.update_health(NodeHealthStatus.DEGRADED.value, "High load detected")
        
        self.assertEqual(len(state.status_history), 2)
        self.assertEqual(state.status_history[0]["type"], "health")


class TestNodeIdentityManager(unittest.TestCase):
    """Test identity manager operations."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "identity.json"
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialize_local_node(self):
        """Initialize local node creates identity, capabilities, trust."""
        manager = NodeIdentityManager(self.storage_path)
        
        caps = [
            NodeCapability("compute", "cpu", "1.0", 8.0, True),
        ]
        
        identity = manager.initialize_local_node("local-node", NodeRole.CONTROLLER, caps)
        
        self.assertIsNotNone(identity)
        self.assertEqual(identity.node_name, "local-node")
        self.assertTrue(identity.is_controller)
        
        # Check capabilities stored
        stored_caps = manager.get_local_capabilities()
        self.assertIsNotNone(stored_caps)
        self.assertEqual(len(stored_caps.capabilities), 1)
        
        # Check trust state stored
        trust = manager.get_local_trust_state()
        self.assertIsNotNone(trust)
        self.assertEqual(trust.trust_status, NodeTrustStatus.TRUSTED.value)  # Controller is trusted
    
    def test_worker_pending_trust(self):
        """Worker starts with pending trust."""
        manager = NodeIdentityManager(self.storage_path)
        identity = manager.initialize_local_node("worker", NodeRole.WORKER)
        
        trust = manager.get_local_trust_state()
        self.assertEqual(trust.trust_status, NodeTrustStatus.PENDING.value)
    
    def test_add_capability(self):
        """Capabilities can be added to local node."""
        manager = NodeIdentityManager(self.storage_path)
        manager.initialize_local_node("test", NodeRole.WORKER)
        
        cap = NodeCapability("storage", "disk", "1.0", 1000.0, True)
        result = manager.add_capability(cap)
        
        self.assertTrue(result)
        
        caps = manager.get_local_capabilities()
        self.assertTrue(caps.has_capability("storage", "disk"))
    
    def test_update_capability(self):
        """Existing capability can be updated."""
        manager = NodeIdentityManager(self.storage_path)
        manager.initialize_local_node("test", NodeRole.WORKER, [
            NodeCapability("compute", "cpu", "1.0", 4.0, True)
        ])
        
        # Update existing
        cap = NodeCapability("compute", "cpu", "2.0", 8.0, True)
        manager.add_capability(cap)
        
        caps = manager.get_local_capabilities()
        cpu = caps.get_capability("compute", "cpu")
        self.assertEqual(cpu.version, "2.0")
        self.assertEqual(cpu.capacity, 8.0)
        self.assertEqual(len(caps.capabilities), 1)  # Not duplicated
    
    def test_remove_capability(self):
        """Capabilities can be removed."""
        manager = NodeIdentityManager(self.storage_path)
        manager.initialize_local_node("test", NodeRole.WORKER, [
            NodeCapability("compute", "cpu", "1.0", 4.0, True)
        ])
        
        result = manager.remove_capability("compute", "cpu")
        self.assertTrue(result)
        
        caps = manager.get_local_capabilities()
        self.assertFalse(caps.has_capability("compute"))
    
    def test_update_trust_status(self):
        """Trust status can be updated."""
        manager = NodeIdentityManager(self.storage_path)
        manager.initialize_local_node("test", NodeRole.WORKER)
        
        result = manager.update_trust_status(
            NodeTrustStatus.TRUSTED.value,
            "Manual verification"
        )
        
        self.assertTrue(result)
        self.assertTrue(manager.get_local_trust_state().is_trusted())
    
    def test_update_health_status(self):
        """Health status can be updated."""
        manager = NodeIdentityManager(self.storage_path)
        manager.initialize_local_node("test", NodeRole.WORKER)
        
        result = manager.update_health_status(
            NodeHealthStatus.DEGRADED.value,
            "High memory usage"
        )
        
        self.assertTrue(result)
        self.assertEqual(
            manager.get_local_trust_state().health_status,
            NodeHealthStatus.DEGRADED.value
        )
    
    def test_persistence(self):
        """Identity persists to storage."""
        # Create and save
        manager1 = NodeIdentityManager(self.storage_path)
        manager1.initialize_local_node("persisted", NodeRole.WORKER, [
            NodeCapability("compute", "cpu", "1.0", 8.0, True)
        ])
        
        # Load in new manager
        manager2 = NodeIdentityManager(self.storage_path)
        result = manager2.load_identity()
        
        self.assertTrue(result)
        self.assertIsNotNone(manager2.get_local_identity())
        self.assertEqual(manager2.get_local_identity().node_name, "persisted")
        self.assertTrue(manager2.get_local_capabilities().has_capability("compute"))


class TestNodeRegistry(unittest.TestCase):
    """Test node registry operations."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "registry.json"
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_register_local(self):
        """Local node can be registered."""
        registry = NodeRegistry(self.storage_path)
        
        identity = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        trust = NodeTrustState(node_id=identity.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        
        entry = registry.register_local(identity, trust)
        
        self.assertIsNotNone(entry)
        self.assertTrue(entry.is_local)
        self.assertTrue(entry.is_reachable)
        self.assertEqual(registry.local_node_id, identity.node_id)
    
    def test_register_remote(self):
        """Remote node can be registered."""
        registry = NodeRegistry(self.storage_path)
        
        # First register local
        local_id = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=local_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry.register_local(local_id, local_trust)
        
        # Register remote
        remote_id = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote_id.is_local = False
        remote_id.node_id = "remote-uuid-123"
        
        entry = registry.register_remote(remote_id)
        
        self.assertIsNotNone(entry)
        self.assertFalse(entry.is_local)
        self.assertFalse(entry.is_reachable)  # Unknown until verified
        self.assertEqual(entry.trust_state.trust_status, NodeTrustStatus.PENDING.value)
    
    def test_cannot_register_self_as_remote(self):
        """Cannot register local node as remote."""
        registry = NodeRegistry(self.storage_path)
        
        local_id = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=local_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry.register_local(local_id, local_trust)
        
        # Try to register same ID as remote
        result = registry.register_remote(local_id)
        self.assertIsNone(result)
    
    def test_get_by_role(self):
        """Nodes can be retrieved by role."""
        registry = NodeRegistry(self.storage_path)
        
        # Register controller
        ctrl_id = NodeIdentity.create_local("ctrl", NodeRole.CONTROLLER)
        ctrl_trust = NodeTrustState(node_id=ctrl_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry.register_local(ctrl_id, ctrl_trust)
        
        # Register workers
        for i in range(3):
            worker_id = NodeIdentity.create_local(f"worker-{i}", NodeRole.WORKER)
            worker_id.node_id = f"worker-{i}"
            worker_id.is_local = False
            registry.register_remote(worker_id)
        
        controllers = registry.get_controllers()
        workers = registry.get_workers()
        
        self.assertEqual(len(controllers), 1)
        self.assertEqual(len(workers), 3)
    
    def test_trusted_filtering(self):
        """Only trusted nodes returned by trusted filter."""
        registry = NodeRegistry(self.storage_path)
        
        local_id = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=local_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry.register_local(local_id, local_trust)
        
        # Register untrusted remote
        remote_id = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote_id.node_id = "remote-1"
        remote_id.is_local = False
        registry.register_remote(remote_id)
        
        trusted = registry.get_trusted_entries()
        self.assertEqual(len(trusted), 1)
        self.assertEqual(trusted[0].node_id, local_id.node_id)
    
    def test_can_communicate_check(self):
        """Communication check considers trust and reachability."""
        registry = NodeRegistry(self.storage_path)
        
        local_id = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=local_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry.register_local(local_id, local_trust)
        
        # Register remote
        remote_id = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote_id.node_id = "remote-1"
        remote_id.is_local = False
        entry = registry.register_remote(remote_id)
        
        # Cannot communicate - not trusted/reachable
        self.assertFalse(registry.can_communicate_with("remote-1"))
        
        # Make trusted and reachable
        entry.trust_state.trust_status = NodeTrustStatus.TRUSTED.value
        entry.trust_state.health_status = NodeHealthStatus.HEALTHY.value
        entry.is_reachable = True
        entry.can_send_to = True
        entry.can_receive_from = True
        
        self.assertTrue(registry.can_communicate_with("remote-1"))
    
    def test_update_reachability(self):
        """Reachability can be updated."""
        registry = NodeRegistry(self.storage_path)
        
        local_id = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=local_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry.register_local(local_id, local_trust)
        
        remote_id = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote_id.node_id = "remote-1"
        remote_id.is_local = False
        registry.register_remote(remote_id)
        
        registry.update_reachability("remote-1", True)
        
        self.assertTrue(registry.is_reachable("remote-1"))
    
    def test_summary(self):
        """Registry summary contains expected fields."""
        registry = NodeRegistry(self.storage_path)
        
        local_id = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=local_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry.register_local(local_id, local_trust)
        
        summary = registry.get_summary()
        
        self.assertEqual(summary["total_nodes"], 1)
        self.assertEqual(summary["local_node"], local_id.node_id)
        self.assertEqual(summary["trusted_nodes"], 1)
        self.assertEqual(summary["reachable_nodes"], 1)
        self.assertEqual(summary["controllers"], 1)
    
    def test_persistence(self):
        """Registry persists to storage."""
        # Create and populate
        registry1 = NodeRegistry(self.storage_path)
        local_id = NodeIdentity.create_local("local", NodeRole.WORKER)
        local_trust = NodeTrustState(node_id=local_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry1.register_local(local_id, local_trust)
        
        # Load in new registry
        registry2 = NodeRegistry(self.storage_path)
        
        self.assertEqual(registry2.get_node_count(), 1)
        self.assertIsNotNone(registry2.get_local_entry())


class TestNodeAvailabilityTracker(unittest.TestCase):
    """Test availability tracking."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "registry.json"
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_record_successful_check(self):
        """Successful health check updates state."""
        registry = NodeRegistry(self.storage_path)
        local_id = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=local_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry.register_local(local_id, local_trust)
        
        remote_id = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote_id.node_id = "remote-1"
        remote_id.is_local = False
        registry.register_remote(remote_id)
        
        tracker = NodeAvailabilityTracker(registry)
        tracker.record_health_check("remote-1", True, latency_ms=50.0)
        
        entry = registry.get_entry("remote-1")
        self.assertTrue(entry.is_reachable)
        self.assertEqual(entry.trust_state.consecutive_failures, 0)
        self.assertEqual(entry.trust_state.health_status, NodeHealthStatus.HEALTHY.value)
    
    def test_record_failed_check(self):
        """Failed health check increments failures."""
        registry = NodeRegistry(self.storage_path)
        local_id = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=local_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry.register_local(local_id, local_trust)
        
        remote_id = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote_id.node_id = "remote-1"
        remote_id.is_local = False
        registry.register_remote(remote_id)
        
        tracker = NodeAvailabilityTracker(registry)
        
        # First failure
        tracker.record_health_check("remote-1", False, error="Timeout")
        entry = registry.get_entry("remote-1")
        self.assertEqual(entry.trust_state.consecutive_failures, 1)
        
        # Second failure - should mark degraded (only if coming from healthy)
        entry.trust_state.health_status = NodeHealthStatus.HEALTHY.value  # Pre-set
        tracker.record_health_check("remote-1", False, error="Timeout")
        self.assertEqual(entry.trust_state.consecutive_failures, 2)
        self.assertEqual(entry.trust_state.health_status, NodeHealthStatus.DEGRADED.value)
        
        # More failures - should mark unhealthy
        for _ in range(3):
            tracker.record_health_check("remote-1", False, error="Timeout")
        self.assertEqual(entry.trust_state.consecutive_failures, 5)
        self.assertEqual(entry.trust_state.health_status, NodeHealthStatus.UNHEALTHY.value)
    
    def test_failure_recovery(self):
        """Successful check resets failure count."""
        registry = NodeRegistry(self.storage_path)
        local_id = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=local_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry.register_local(local_id, local_trust)
        
        remote_id = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote_id.node_id = "remote-1"
        remote_id.is_local = False
        registry.register_remote(remote_id)
        
        tracker = NodeAvailabilityTracker(registry)
        
        # Failures
        tracker.record_health_check("remote-1", False)
        tracker.record_health_check("remote-1", False)
        
        entry = registry.get_entry("remote-1")
        self.assertEqual(entry.trust_state.consecutive_failures, 2)
        
        # Recovery
        tracker.record_health_check("remote-1", True)
        self.assertEqual(entry.trust_state.consecutive_failures, 0)
        self.assertEqual(entry.trust_state.health_status, NodeHealthStatus.HEALTHY.value)
    
    def test_uptime_stats(self):
        """Uptime stats calculated from history."""
        registry = NodeRegistry(self.storage_path)
        local_id = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=local_id.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        registry.register_local(local_id, local_trust)
        
        remote_id = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote_id.node_id = "remote-1"
        remote_id.is_local = False
        registry.register_remote(remote_id)
        
        tracker = NodeAvailabilityTracker(registry)
        
        # Simulate checks - 7 failures (indices 0,3,6,9), 3 successes
        for i in range(10):
            success = i not in (0, 3, 6, 9)
            tracker.record_health_check("remote-1", success, latency_ms=50.0 if success else None)
        
        stats = tracker.get_uptime_stats("remote-1")
        
        self.assertEqual(stats["checks"], 10)
        self.assertEqual(stats["success_rate"], 0.6)  # 6/10 successful
        self.assertIsNotNone(stats["avg_latency_ms"])


class TestDefaultCapabilities(unittest.TestCase):
    """Test default capability generation."""
    
    def test_controller_capabilities(self):
        """Controller gets coordination capabilities."""
        caps = create_default_capabilities(NodeRole.CONTROLLER)
        
        types = {c.capability_type for c in caps}
        self.assertIn("core", types)
        self.assertIn("coordination", types)
    
    def test_worker_capabilities(self):
        """Worker gets compute capabilities."""
        caps = create_default_capabilities(NodeRole.WORKER)
        
        types = {c.capability_type for c in caps}
        self.assertIn("core", types)
        self.assertIn("compute", types)
    
    def test_edge_capabilities(self):
        """Edge gets low-latency capabilities."""
        caps = create_default_capabilities(NodeRole.EDGE)
        
        names = {c.capability_name for c in caps}
        self.assertIn("low-latency", names)
        self.assertIn("cache", names)
    
    def test_relay_capabilities(self):
        """Relay gets network capabilities."""
        caps = create_default_capabilities(NodeRole.RELAY)
        
        types = {c.capability_type for c in caps}
        self.assertIn("network", types)


if __name__ == "__main__":
    unittest.main()
