"""Distributed Multi-Node Execution Coordinator (v70)

Multi-node distributed execution coordination layer for WESLR.
Enables true multi-node distributed operation beyond envelope-based execution.

Architecture:
  - MultiNodeCoordinator — orchestrates multi-node distributed execution
  - NodeSelectionStrategy — selects optimal nodes for execution
  - ExecutionShard — partitions execution across nodes
  - ShardAggregator — aggregates results from shards
  - CrossNodeContinuity — maintains continuity across nodes

Rules:
  - Multi-node orchestration only — no single-node logic
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - Uses v64-v69 distributed stack
  - No scheduler/task engine
  - No TIA/C#
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple

from .node_registry import NodeRegistry
from .node_identity import (
    NodeIdentity,
    NodeTrustState,
    NodeTrustStatus,
    NodeHealthStatus,
    NodeRole,
)
from .distributed_execution_integration import (
    ExecutionOrchestrator,
    ExecutionFlowState,
    TelemetryEventEmitter,
)


# ============================================================================
# NODE SELECTION CONTEXT
# ============================================================================


class NodeSelectionContext:
    """Context for node selection decision."""
    
    def __init__(
        self,
        available_nodes: List[NodeIdentity],
        registry: Optional[NodeRegistry] = None,
        required_capabilities: Optional[List[str]] = None,
        trust_threshold: float = 0.5,
        health_threshold: float = 0.5
    ):
        self.available_nodes = available_nodes
        self.registry = registry
        self.required_capabilities = required_capabilities
        self.trust_threshold = trust_threshold
        self.health_threshold = health_threshold
    
    def _get_node_trust_state(self, node: NodeIdentity) -> Optional[NodeTrustState]:
        """Get trust state for a node from registry."""
        if self.registry:
            entry = self.registry.get_entry(node.node_id)
            if entry and entry.trust_state:
                return entry.trust_state
        return None
    
    def filter_by_trust(self, nodes: List[NodeIdentity]) -> List[NodeIdentity]:
        """Filter nodes by trust threshold."""
        result = []
        for n in nodes:
            ts = self._get_node_trust_state(n)
            # Check registry trust state first, then direct trust_state attribute
            trust_state = ts if ts else getattr(n, 'trust_state', None)
            if trust_state and trust_state.trust_status == NodeTrustStatus.TRUSTED.value:
                result.append(n)
        return result
    
    def filter_by_health(self, nodes: List[NodeIdentity]) -> List[NodeIdentity]:
        """Filter nodes by health threshold."""
        result = []
        for n in nodes:
            ts = self._get_node_trust_state(n)
            # Check registry trust state first, then direct trust_state attribute
            trust_state = ts if ts else getattr(n, 'trust_state', None)
            health_status = getattr(trust_state, 'health_status', None) if trust_state else getattr(n, 'health_status', None)
            if health_status and health_status == NodeHealthStatus.HEALTHY.value:
                result.append(n)
        return result
    
    def filter_by_capability(self, nodes: List[NodeIdentity], capability: str) -> List[NodeIdentity]:
        """Filter nodes by required capability."""
        result = []
        for n in nodes:
            # Check direct capabilities attribute
            capabilities = getattr(n, 'capabilities', None)
            if capabilities:
                cap_list = getattr(capabilities, 'capabilities', [])
                if capability in cap_list:
                    result.append(n)
        return result


# ============================================================================
# NODE SELECTION STRATEGIES
# ============================================================================


class NodeSelectionStrategy(str, Enum):
    """Strategy for selecting nodes for distributed execution."""
    RANDOM = "random"                       # Random node selection
    LEAST_LOADED = "least_loaded"           # Select least loaded node
    HIGHEST_TRUST = "highest_trust"         # Select highest trust node
    NEAREST = "nearest"                     # Select nearest node (latency)
    CAPABILITY_MATCH = "capability_match"   # Select node matching capabilities
    BALANCED = "balanced"                   # Distribute load across nodes


# ============================================================================
# EXECUTION SHARD
# ============================================================================


@dataclass
class ExecutionShard:
    """A shard of distributed execution assigned to a specific node."""
    
    shard_id: str
    node_id: str
    execution_intent: str
    execution_parameters: Dict[str, Any]
    assigned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    status: str = "pending"  # pending, in_progress, completed, failed
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def mark_completed(self, result: Dict[str, Any]) -> None:
        """Mark shard as completed."""
        self.status = "completed"
        self.result = result
    
    def mark_failed(self, error: str) -> None:
        """Mark shard as failed."""
        self.status = "failed"
        self.error = error


# ============================================================================
# SHARD AGGREGATOR
# ============================================================================


class ShardAggregator:
    """Aggregates results from distributed execution shards."""
    
    def __init__(self, shard_ids: List[str]):
        self.shard_ids = shard_ids
        self.shards: Dict[str, ExecutionShard] = {}
        self.combined_result: Optional[Dict[str, Any]] = None
        self.aggregation_timestamp: Optional[str] = None
    
    def add_shard(self, shard: ExecutionShard) -> None:
        """Add a shard to the aggregator."""
        self.shards[shard.shard_id] = shard
    
    def get_shard(self, shard_id: str) -> Optional[ExecutionShard]:
        """Get a specific shard by ID."""
        return self.shards.get(shard_id)
    
    def get_completed_shards(self) -> List[ExecutionShard]:
        """Get all completed shards."""
        return [s for s in self.shards.values() if s.status == "completed"]
    
    def get_failed_shards(self) -> List[ExecutionShard]:
        """Get all failed shards."""
        return [s for s in self.shards.values() if s.status == "failed"]
    
    def is_all_completed(self) -> bool:
        """Check if all shards are completed."""
        return all(s.status in ("completed", "failed") for s in self.shards.values())
    
    def aggregate_results(self, aggregator_fn: Optional[Callable[[List[Dict[str, Any]]], Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """Aggregate results from all shards."""
        completed = self.get_completed_shards()
        if not completed:
            return None
        
        results = [s.result for s in completed if s.result]
        if not results:
            return None
        
        if aggregator_fn:
            self.combined_result = aggregator_fn(results)
        else:
            # Default aggregation: merge results
            merged: Dict[str, Any] = {}
            for result in results:
                merged.update(result)
            self.combined_result = merged
        
        self.aggregation_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self.combined_result
    
    def get_aggregation_stats(self) -> Dict[str, Any]:
        """Get aggregation statistics."""
        return {
            "total_shards": len(self.shards),
            "completed_shards": len(self.get_completed_shards()),
            "failed_shards": len(self.get_failed_shards()),
            "has_combined_result": self.combined_result is not None,
            "aggregation_timestamp": self.aggregation_timestamp
        }


# ============================================================================
# DISTRIBUTED EXECUTION COORDINATOR
# ============================================================================


class MultiNodeCoordinator:
    """Coordinates distributed execution across multiple nodes.
    
    Orchestrates multi-node execution using the v64-v69 distributed stack.
    Provides execution partitioning, node selection, and result aggregation.
    """
    
    def __init__(
        self,
        registry: NodeRegistry,
        local_node_id: str,
        node_selection_strategy: NodeSelectionStrategy = NodeSelectionStrategy.BALANCED,
        telemetry: Optional[TelemetryEventEmitter] = None
    ):
        self.registry = registry
        self.local_node_id = local_node_id
        self.node_selection_strategy = node_selection_strategy
        self.telemetry = telemetry or TelemetryEventEmitter()
        
        # Execution tracking
        self._coordinations: Dict[str, Dict[str, Any]] = {}
        self._aggregators: Dict[str, ShardAggregator] = {}
    
    def _get_node_trust_state(self, node: NodeIdentity) -> Optional[NodeTrustState]:
        """Get trust state for a node from registry."""
        if self.registry:
            entry = self.registry.get_entry(node.node_id)
            if entry and entry.trust_state:
                return entry.trust_state
        return None
    
    def get_available_nodes(self) -> List[NodeIdentity]:
        """Get all available remote nodes."""
        entries = self.registry.get_all_entries()
        return [
            e.identity for e in entries
            if e.identity and not e.is_local
        ]
    
    def select_nodes(
        self,
        available: List[NodeIdentity],
        count: int,
        required_capabilities: Optional[List[str]] = None
    ) -> List[NodeIdentity]:
        """Select nodes for distributed execution."""
        context = NodeSelectionContext(
            available_nodes=available,
            registry=self.registry,
            required_capabilities=required_capabilities
        )
        
        # Filter by trust and health
        filtered = context.filter_by_trust(available)
        filtered = context.filter_by_health(filtered)
        
        # Filter by capability if specified
        if required_capabilities:
            for cap in required_capabilities:
                filtered = context.filter_by_capability(filtered, cap)
        
        if not filtered:
            return []
        
        # Apply selection strategy
        if self.node_selection_strategy == NodeSelectionStrategy.RANDOM:
            import random
            return random.sample(filtered, min(count, len(filtered)))
        elif self.node_selection_strategy == NodeSelectionStrategy.LEAST_LOADED:
            # Sort by least loaded (placeholder - would need load metrics)
            return filtered[:count]
        elif self.node_selection_strategy == NodeSelectionStrategy.HIGHEST_TRUST:
            # Sort by trust status using registry lookup
            return sorted(
                filtered,
                key=lambda n: self._get_node_trust_state(n).trust_status if self._get_node_trust_state(n) else "",
                reverse=True
            )[:count]
        elif self.node_selection_strategy == NodeSelectionStrategy.NEAREST:
            # Sort by latency (placeholder - would need latency metrics)
            return filtered[:count]
        elif self.node_selection_strategy == NodeSelectionStrategy.BALANCED:
            # Round-robin distribution
            return filtered[:count]
        else:
            return filtered[:count]
    
    def create_execution_coordination(
        self,
        coordination_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new execution coordination context."""
        coord_id = coordination_id or str(uuid.uuid4())
        
        coordination = {
            "coordination_id": coord_id,
            "shards": [],
            "aggregator": None,
            "started_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "completed_at": None,
            "status": "pending"
        }
        
        self._coordinations[coord_id] = coordination
        return coordination
    
    def partition_execution(
        self,
        coordination_id: str,
        total_tasks: int,
        nodes: List[NodeIdentity],
        execution_intent: str,
        execution_parameters: Dict[str, Any]
    ) -> List[ExecutionShard]:
        """Partition execution across nodes."""
        coordination = self._coordinations.get(coordination_id)
        if not coordination:
            raise ValueError(f"Coordination {coordination_id} not found")
        
        shards = []
        tasks_per_node = total_tasks // len(nodes) if nodes else 0
        
        for i, node in enumerate(nodes):
            shard = ExecutionShard(
                shard_id=f"{coordination_id}-shard-{i}",
                node_id=node.node_id,
                execution_intent=execution_intent,
                execution_parameters={
                    **execution_parameters,
                    "shard_index": i,
                    "total_shards": len(nodes),
                    "tasks_to_execute": tasks_per_node
                }
            )
            shards.append(shard)
            coordination["shards"].append(shard.shard_id)
        
        # Create aggregator
        aggregator = ShardAggregator([s.shard_id for s in shards])
        for shard in shards:
            aggregator.add_shard(shard)
        
        self._aggregators[coordination_id] = aggregator
        coordination["aggregator"] = coordination_id
        
        return shards
    
    def execute_shard(
        self,
        coordination_id: str,
        shard: ExecutionShard,
        target_node_id: str,
        orchestrator: Optional[ExecutionOrchestrator] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Execute a shard on a target node.
        
        Returns execution flow ID or error.
        """
        # Create orchestrator if not provided
        if orchestrator is None:
            orchestrator = ExecutionOrchestrator(
                local_node_id=self.local_node_id,
                registry=self.registry
            )
        
        # This would integrate with v64-v69 execution flow
        # For now, returns a placeholder execution flow ID
        execution_flow_id = f"{coordination_id}-{shard.node_id}-flow"
        
        # Emit telemetry event
        self.telemetry.create_event(
            event_type="execution_shard_started",
            flow_id=execution_flow_id,
            properties={"shard_id": shard.shard_id, "node_id": shard.node_id}
        )
        
        return execution_flow_id, None
    
    def aggregate_results(
        self,
        coordination_id: str,
        aggregator_fn: Optional[Callable[[List[Dict[str, Any]]], Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """Aggregate results from all shards."""
        aggregator = self._aggregators.get(coordination_id)
        if not aggregator:
            raise ValueError(f"Aggregator for {coordination_id} not found")
        
        result = aggregator.aggregate_results(aggregator_fn)
        
        # Update coordination status
        coordination = self._coordinations.get(coordination_id)
        if coordination:
            coordination["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            if result:
                coordination["status"] = "completed"
            else:
                coordination["status"] = "partial"
        
        return result
    
    def get_coordination_status(self, coordination_id: str) -> Dict[str, Any]:
        """Get status of a coordination."""
        coordination = self._coordinations.get(coordination_id)
        aggregator = self._aggregators.get(coordination_id)
        
        if not coordination:
            return {"error": "Coordination not found"}
        
        status = {
            "coordination_id": coordination_id,
            "status": coordination["status"],
            "started_at": coordination["started_at"],
            "completed_at": coordination.get("completed_at"),
            "shard_count": len(coordination.get("shards", [])),
            "aggregation_stats": aggregator.get_aggregation_stats() if aggregator else {}
        }
        
        if aggregator:
            status["combined_result_available"] = aggregator.combined_result is not None
            status["aggregation_timestamp"] = aggregator.aggregation_timestamp
        
        return status
    
    def get_all_coordination_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all coordinations."""
        return {
            coord_id: self.get_coordination_status(coord_id)
            for coord_id in self._coordinations.keys()
        }
