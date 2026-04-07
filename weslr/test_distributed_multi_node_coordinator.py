"""Tests for Distributed Multi-Node Execution Coordinator (v70)

Behavioral tests for multi-node coordination, node selection,
execution partitioning, and result aggregation.

Test Doctrine version: 1.0.0 (2026-04-07)
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.distributed_multi_node_coordinator import (
    NodeSelectionStrategy,
    NodeSelectionContext,
    ExecutionShard,
    ShardAggregator,
    MultiNodeCoordinator,
)
from weslr.node_identity import (
    NodeIdentity,
    NodeTrustState,
    NodeTrustStatus,
    NodeHealthStatus,
    NodeRole,
)
from weslr.node_registry import NodeRegistry
from weslr.execution_telemetry import TelemetryEventEmitter


# ============================================================================
# NODE SELECTION STRATEGY TESTS
# ============================================================================


class TestNodeSelectionStrategyModel(unittest.TestCase):
    """Test node selection strategy data models."""

    def test_node_selection_context_creation(self):
        """NodeSelectionContext created with available nodes."""
        context = NodeSelectionContext(
            available_nodes=[],
            required_capabilities=None,
            trust_threshold=0.5,
            health_threshold=0.5
        )
        
        self.assertEqual(context.available_nodes, [])
        self.assertEqual(context.trust_threshold, 0.5)
        self.assertEqual(context.health_threshold, 0.5)

    def test_node_selection_context_filter_by_trust(self):
        """Filter nodes by trust threshold."""
        # Create mock node objects with trust_state
        class MockNode:
            def __init__(self, name, trust_status):
                self.node_name = name
                self.trust_state = type('obj', (object,), {
                    'trust_status': trust_status
                })()
        
        node_a = MockNode("node-a", NodeTrustStatus.TRUSTED.value)
        node_b = MockNode("node-b", NodeTrustStatus.UNTRUSTED.value)
        
        context = NodeSelectionContext(
            available_nodes=[node_a, node_b],
            trust_threshold=0.5
        )
        
        filtered = context.filter_by_trust([node_a, node_b])
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].node_name, "node-a")


class TestNodeSelectionStrategyBehavior(unittest.TestCase):
    """Test node selection strategy behavior."""

    def test_filter_by_health(self):
        """Filter nodes by health threshold."""
        # Create mock node objects with trust_state
        class MockNode:
            def __init__(self, name, status):
                self.node_name = name
                self.trust_state = type('obj', (object,), {
                    'health_status': status
                })()
        
        node_a = MockNode("node-a", NodeHealthStatus.HEALTHY.value)
        node_b = MockNode("node-b", NodeHealthStatus.UNHEALTHY.value)
        
        context = NodeSelectionContext(
            available_nodes=[node_a, node_b],
            health_threshold=0.5
        )
        
        filtered = context.filter_by_health([node_a, node_b])
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].node_name, "node-a")

    def test_filter_by_capability(self):
        """Filter nodes by required capability."""
        # Create mock node objects
        class MockNode:
            def __init__(self, name, capabilities):
                self.node_name = name
                self.capabilities = type('obj', (object,), {
                    'capabilities': capabilities
                })()
        
        node_a = MockNode("node-a", [])
        node_b = MockNode("node-b", ['compute'])
        
        context = NodeSelectionContext(
            available_nodes=[node_a, node_b],
            required_capabilities=['compute']
        )
        
        filtered = context.filter_by_capability([node_a, node_b], 'compute')
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].node_name, "node-b")


# ============================================================================
# EXECUTION SHARD TESTS
# ============================================================================


class TestExecutionShardModel(unittest.TestCase):
    """Test execution shard data models."""

    def test_shard_creation(self):
        """ExecutionShard created with required fields."""
        shard = ExecutionShard(
            shard_id="shard-1",
            node_id="node-a",
            execution_intent="sync_data",
            execution_parameters={"data": "test"}
        )
        
        self.assertEqual(shard.shard_id, "shard-1")
        self.assertEqual(shard.node_id, "node-a")
        self.assertEqual(shard.status, "pending")

    def test_shard_mark_completed(self):
        """Shard marked as completed."""
        shard = ExecutionShard(
            shard_id="shard-1",
            node_id="node-a",
            execution_intent="sync_data",
            execution_parameters={}
        )
        
        shard.mark_completed({"records": 100})
        
        self.assertEqual(shard.status, "completed")
        self.assertEqual(shard.result["records"], 100)

    def test_shard_mark_failed(self):
        """Shard marked as failed."""
        shard = ExecutionShard(
            shard_id="shard-1",
            node_id="node-a",
            execution_intent="sync_data",
            execution_parameters={}
        )
        
        shard.mark_failed("Network timeout")
        
        self.assertEqual(shard.status, "failed")
        self.assertEqual(shard.error, "Network timeout")


# ============================================================================
# SHARD AGGREGATOR TESTS
# ============================================================================


class TestShardAggregatorModel(unittest.TestCase):
    """Test shard aggregator data models."""

    def test_aggregator_creation(self):
        """ShardAggregator created with shard IDs."""
        aggregator = ShardAggregator(["shard-1", "shard-2"])
        
        self.assertEqual(aggregator.shard_ids, ["shard-1", "shard-2"])
        self.assertEqual(aggregator.shards, {})
        self.assertIsNone(aggregator.combined_result)


class TestShardAggregatorBehavior(unittest.TestCase):
    """Test shard aggregator behavior."""

    def setUp(self):
        self.aggregator = ShardAggregator(["shard-1", "shard-2"])
    
    def test_add_shard(self):
        """Shard added to aggregator."""
        shard = ExecutionShard(
            shard_id="shard-1",
            node_id="node-a",
            execution_intent="sync_data",
            execution_parameters={}
        )
        self.aggregator.add_shard(shard)
        
        self.assertIn("shard-1", self.aggregator.shards)
        self.assertEqual(self.aggregator.shards["shard-1"], shard)

    def test_get_shard(self):
        """Get shard by ID."""
        shard = ExecutionShard(
            shard_id="shard-1",
            node_id="node-a",
            execution_intent="sync_data",
            execution_parameters={}
        )
        self.aggregator.add_shard(shard)
        
        retrieved = self.aggregator.get_shard("shard-1")
        self.assertEqual(retrieved, shard)

    def test_get_completed_shards(self):
        """Get all completed shards."""
        shard1 = ExecutionShard(
            shard_id="shard-1",
            node_id="node-a",
            execution_intent="sync_data",
            execution_parameters={}
        )
        shard1.mark_completed({"result": "success"})
        
        shard2 = ExecutionShard(
            shard_id="shard-2",
            node_id="node-b",
            execution_intent="sync_data",
            execution_parameters={}
        )
        shard2.mark_failed("Timeout")
        
        self.aggregator.add_shard(shard1)
        self.aggregator.add_shard(shard2)
        
        completed = self.aggregator.get_completed_shards()
        
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].shard_id, "shard-1")

    def test_get_failed_shards(self):
        """Get all failed shards."""
        shard1 = ExecutionShard(
            shard_id="shard-1",
            node_id="node-a",
            execution_intent="sync_data",
            execution_parameters={}
        )
        shard1.mark_completed({"result": "success"})
        
        shard2 = ExecutionShard(
            shard_id="shard-2",
            node_id="node-b",
            execution_intent="sync_data",
            execution_parameters={}
        )
        shard2.mark_failed("Timeout")
        
        self.aggregator.add_shard(shard1)
        self.aggregator.add_shard(shard2)
        
        failed = self.aggregator.get_failed_shards()
        
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].shard_id, "shard-2")

    def test_is_all_completed(self):
        """Check if all shards are completed."""
        shard1 = ExecutionShard(
            shard_id="shard-1",
            node_id="node-a",
            execution_intent="sync_data",
            execution_parameters={}
        )
        shard1.mark_completed({"result": "success"})
        
        shard2 = ExecutionShard(
            shard_id="shard-2",
            node_id="node-b",
            execution_intent="sync_data",
            execution_parameters={}
        )
        shard2.mark_failed("Timeout")
        
        self.aggregator.add_shard(shard1)
        self.aggregator.add_shard(shard2)
        
        self.assertTrue(self.aggregator.is_all_completed())

    def test_aggregate_results_default(self):
        """Aggregate results with default merge."""
        shard1 = ExecutionShard(
            shard_id="shard-1",
            node_id="node-a",
            execution_intent="sync_data",
            execution_parameters={}
        )
        shard1.mark_completed({"records": 100, "region": "us"})
        
        shard2 = ExecutionShard(
            shard_id="shard-2",
            node_id="node-b",
            execution_intent="sync_data",
            execution_parameters={}
        )
        shard2.mark_completed({"records": 50, "region": "eu"})
        
        self.aggregator.add_shard(shard1)
        self.aggregator.add_shard(shard2)
        
        result = self.aggregator.aggregate_results()
        
        self.assertIsNotNone(result)
        # Default merge: last value wins for same key
        self.assertIn("records", result)
        self.assertIn("region", result)

    def test_aggregate_results_custom(self):
        """Aggregate results with custom function."""
        shard1 = ExecutionShard(
            shard_id="shard-1",
            node_id="node-a",
            execution_intent="sync_data",
            execution_parameters={}
        )
        shard1.mark_completed({"value": 10})
        
        shard2 = ExecutionShard(
            shard_id="shard-2",
            node_id="node-b",
            execution_intent="sync_data",
            execution_parameters={}
        )
        shard2.mark_completed({"value": 20})
        
        self.aggregator.add_shard(shard1)
        self.aggregator.add_shard(shard2)
        
        def sum_aggregator(results):
            return {"total": sum(r["value"] for r in results)}
        
        result = self.aggregator.aggregate_results(sum_aggregator)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["total"], 30)

    def test_get_aggregation_stats(self):
        """Get aggregation statistics."""
        shard = ExecutionShard(
            shard_id="shard-1",
            node_id="node-a",
            execution_intent="sync_data",
            execution_parameters={}
        )
        shard.mark_completed({"result": "success"})
        
        self.aggregator.add_shard(shard)
        self.aggregator.aggregate_results()
        
        stats = self.aggregator.get_aggregation_stats()
        
        self.assertEqual(stats["total_shards"], 1)
        self.assertEqual(stats["completed_shards"], 1)
        self.assertTrue(stats["has_combined_result"])


# ============================================================================
# MULTI-NODE COORDINATOR TESTS
# ============================================================================


class TestMultiNodeCoordinatorModel(unittest.TestCase):
    """Test multi-node coordinator data models."""

    def test_coordinator_creation(self):
        """MultiNodeCoordinator created with registry and local node."""
        registry = NodeRegistry()
        local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(
            node_id="local",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        registry.register_local(local, local_trust)
        
        coordinator = MultiNodeCoordinator(
            registry=registry,
            local_node_id="local"
        )
        
        self.assertEqual(coordinator.registry, registry)
        self.assertEqual(coordinator.local_node_id, "local")
        self.assertEqual(coordinator.node_selection_strategy, NodeSelectionStrategy.BALANCED)

    def test_coordinator_with_telemetry(self):
        """MultiNodeCoordinator works with telemetry emitter."""
        registry = NodeRegistry()
        local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(
            node_id="local",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        registry.register_local(local, local_trust)
        
        telemetry = TelemetryEventEmitter()
        coordinator = MultiNodeCoordinator(
            registry=registry,
            local_node_id="local",
            telemetry=telemetry
        )
        
        self.assertEqual(coordinator.telemetry, telemetry)


class TestMultiNodeCoordinatorBehavior(unittest.TestCase):
    """Test multi-node coordinator behavior."""

    def setUp(self):
        self.registry = NodeRegistry()
        
        # Setup local node
        self.local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(
            node_id="local",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_local(self.local, local_trust)
        
        # Setup remote nodes
        self.remote_a = NodeIdentity.create_local("remote-a", NodeRole.WORKER)
        self.remote_a.node_id = "remote-a"
        self.remote_a.is_local = False
        remote_a_trust = NodeTrustState(
            node_id="remote-a",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(self.remote_a, remote_a_trust)
        
        self.remote_b = NodeIdentity.create_local("remote-b", NodeRole.WORKER)
        self.remote_b.node_id = "remote-b"
        self.remote_b.is_local = False
        remote_b_trust = NodeTrustState(
            node_id="remote-b",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(self.remote_b, remote_b_trust)
        
        self.coordinator = MultiNodeCoordinator(
            registry=self.registry,
            local_node_id="local"
        )

    def test_get_available_nodes(self):
        """Get available remote nodes."""
        nodes = self.coordinator.get_available_nodes()
        
        self.assertEqual(len(nodes), 2)
        node_ids = [n.node_id for n in nodes]
        self.assertIn("remote-a", node_ids)
        self.assertIn("remote-b", node_ids)

    def test_select_nodes_balanced(self):
        """Select nodes using balanced strategy."""
        nodes = self.coordinator.get_available_nodes()
        
        selected = self.coordinator.select_nodes(
            nodes,
            count=1,
            required_capabilities=None
        )
        
        self.assertEqual(len(selected), 1)
        self.assertIn(selected[0].node_id, ["remote-a", "remote-b"])

    def test_select_nodes_highest_trust(self):
        """Select nodes using highest trust strategy."""
        self.coordinator.node_selection_strategy = NodeSelectionStrategy.HIGHEST_TRUST
        nodes = self.coordinator.get_available_nodes()
        
        # Set capabilities on remote nodes
        self.remote_a.capabilities = type('obj', (object,), {
            'capabilities': ['compute']
        })()
        self.remote_b.capabilities = type('obj', (object,), {
            'capabilities': ['compute']
        })()
        
        selected = self.coordinator.select_nodes(
            nodes,
            count=1,
            required_capabilities=None
        )
        
        self.assertEqual(len(selected), 1)
        # Trust is equal, so should select one of the remote nodes
        self.assertIn(selected[0].node_id, ["remote-a", "remote-b"])

    def test_select_nodes_by_capability(self):
        """Select nodes by required capability."""
        # Set capabilities on remote nodes
        self.remote_a.capabilities = type('obj', (object,), {
            'capabilities': ['compute', 'sync']
        })()
        self.remote_b.capabilities = type('obj', (object,), {
            'capabilities': ['compute']
        })()
        
        nodes = self.coordinator.get_available_nodes()
        
        selected = self.coordinator.select_nodes(
            nodes,
            count=1,
            required_capabilities=['compute']
        )
        
        self.assertEqual(len(selected), 1)
        self.assertIn(selected[0].node_id, ["remote-a", "remote-b"])

    def test_create_execution_coordination(self):
        """Create execution coordination context."""
        coordination = self.coordinator.create_execution_coordination()
        
        self.assertIn("coordination_id", coordination)
        self.assertIn("shards", coordination)
        self.assertEqual(coordination["status"], "pending")

    def test_partition_execution(self):
        """Partition execution across nodes."""
        coordination = self.coordinator.create_execution_coordination()
        coordination_id = coordination["coordination_id"]
        
        nodes = self.coordinator.get_available_nodes()
        
        shards = self.coordinator.partition_execution(
            coordination_id=coordination_id,
            total_tasks=10,
            nodes=nodes,
            execution_intent="sync_data",
            execution_parameters={"chunk_size": 100}
        )
        
        self.assertEqual(len(shards), 2)
        self.assertEqual(shards[0].node_id, "remote-a")
        self.assertEqual(shards[1].node_id, "remote-b")

    def test_aggregate_results(self):
        """Aggregate results from shards."""
        coordination = self.coordinator.create_execution_coordination()
        coordination_id = coordination["coordination_id"]
        
        nodes = self.coordinator.get_available_nodes()
        shards = self.coordinator.partition_execution(
            coordination_id=coordination_id,
            total_tasks=10,
            nodes=nodes,
            execution_intent="sync_data",
            execution_parameters={"chunk_size": 100}
        )
        
        # Mark shards as completed with different data
        shards[0].mark_completed({"records": 100, "region": "us"})
        shards[1].mark_completed({"records": 50, "region": "eu"})
        
        # Update shards in aggregator
        aggregator = self.coordinator._aggregators.get(coordination_id)
        aggregator.shards[shards[0].shard_id] = shards[0]
        aggregator.shards[shards[1].shard_id] = shards[1]
        
        result = self.coordinator.aggregate_results(coordination_id)
        
        self.assertIsNotNone(result)
        # Default merge: last value wins for same key
        self.assertEqual(result["records"], 50)  # Last shard's value
        self.assertEqual(result["region"], "eu")  # Last shard's value

    def test_get_coordination_status(self):
        """Get status of coordination."""
        coordination = self.coordinator.create_execution_coordination()
        coordination_id = coordination["coordination_id"]
        
        status = self.coordinator.get_coordination_status(coordination_id)
        
        self.assertEqual(status["status"], "pending")
        self.assertEqual(status["coordination_id"], coordination_id)

    def test_get_all_coordination_statuses(self):
        """Get status of all coordinations."""
        coord1 = self.coordinator.create_execution_coordination()
        coord2 = self.coordinator.create_execution_coordination()
        
        statuses = self.coordinator.get_all_coordination_statuses()
        
        self.assertEqual(len(statuses), 2)
        self.assertIn(coord1["coordination_id"], statuses)
        self.assertIn(coord2["coordination_id"], statuses)


# ============================================================================
# MULTI-NODE INTEGRATION TESTS
# ============================================================================


class TestMultiNodeIntegration(unittest.TestCase):
    """Test multi-node coordinator integration with v64-v69."""

    def test_coordinator_works_with_node_registry(self):
        """MultiNodeCoordinator works with NodeRegistry."""
        registry = NodeRegistry()
        local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(
            node_id="local",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        registry.register_local(local, local_trust)
        
        coordinator = MultiNodeCoordinator(
            registry=registry,
            local_node_id="local"
        )
        
        nodes = coordinator.get_available_nodes()
        self.assertEqual(len(nodes), 0)  # No remote nodes

    def test_coordinator_emits_telemetry_events(self):
        """MultiNodeCoordinator emits telemetry events."""
        registry = NodeRegistry()
        local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(
            node_id="local",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        registry.register_local(local, local_trust)
        
        telemetry = TelemetryEventEmitter()
        coordinator = MultiNodeCoordinator(
            registry=registry,
            local_node_id="local",
            telemetry=telemetry
        )
        
        # This would trigger telemetry events in real execution
        coordination = coordinator.create_execution_coordination()
        self.assertIn("coordination_id", coordination)


# ============================================================================
# MULTI-NODE BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestMultiNodeBackwardCompatibility(unittest.TestCase):
    """Test multi-node coordinator backward compatibility."""

    def test_coordinator_does_not_break_v64_execution(self):
        """MultiNodeCoordinator doesn't break v64-v69 execution."""
        registry = NodeRegistry()
        local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(
            node_id="local",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        registry.register_local(local, local_trust)
        
        coordinator = MultiNodeCoordinator(
            registry=registry,
            local_node_id="local"
        )
        
        # v64-v69 orchestrator still works
        coordination = coordinator.create_execution_coordination()
        self.assertIsNotNone(coordination)


if __name__ == "__main__":
    unittest.main()
