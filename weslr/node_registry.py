"""Node Registry and Availability Tracking (v57)

Foundation slice for distributed multi-node WESLR architecture.
Manages registry of known nodes, their availability, and communication scope.

Architecture:
  - NodeRegistryEntry — tracked node with metadata
  - NodeRegistry — multi-node registry with availability tracking
  - NodeAvailabilityTracker — health/trust status monitoring

Rules:
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - Operator-first (status visible)
  - Foundation only — no active orchestration yet
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .node_identity import (
    NodeIdentity,
    NodeCapabilitySummary,
    NodeTrustState,
    NodeRole,
    NodeTrustStatus,
    NodeHealthStatus,
    NodeLocationType
)


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class NodeRegistryEntry:
    """Entry in the node registry tracking a known remote or local node."""
    
    node_id: str
    identity: Optional[NodeIdentity] = None
    capabilities: Optional[NodeCapabilitySummary] = None
    trust_state: Optional[NodeTrustState] = None
    
    # Registry metadata
    first_seen_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_seen_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_contact_attempt: Optional[str] = None
    
    # Availability tracking
    is_reachable: bool = False
    is_local: bool = False  # True if this is the local node
    
    # Communication scope
    can_send_to: bool = False    # This node can send TO this entry
    can_receive_from: bool = False  # This node can receive FROM this entry
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_seen(self) -> None:
        """Update last seen timestamp."""
        self.last_seen_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def update_reachability(self, reachable: bool) -> None:
        """Update reachability status."""
        self.is_reachable = reachable
        if reachable:
            self.update_seen()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "identity": self.identity.to_dict() if self.identity else None,
            "capabilities": self.capabilities.to_dict() if self.capabilities else None,
            "trust_state": self.trust_state.to_dict() if self.trust_state else None,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
            "last_contact_attempt": self.last_contact_attempt,
            "is_reachable": self.is_reachable,
            "is_local": self.is_local,
            "can_send_to": self.can_send_to,
            "can_receive_from": self.can_receive_from,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeRegistryEntry":
        """Create from dictionary."""
        identity = None
        capabilities = None
        trust_state = None
        
        if data.get("identity"):
            identity = NodeIdentity.from_dict(data["identity"])
        if data.get("capabilities"):
            capabilities = NodeCapabilitySummary.from_dict(data["capabilities"])
        if data.get("trust_state"):
            trust_state = NodeTrustState.from_dict(data["trust_state"])
        
        return cls(
            node_id=data["node_id"],
            identity=identity,
            capabilities=capabilities,
            trust_state=trust_state,
            first_seen_at=data.get("first_seen_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            last_seen_at=data.get("last_seen_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            last_contact_attempt=data.get("last_contact_attempt"),
            is_reachable=data.get("is_reachable", False),
            is_local=data.get("is_local", False),
            can_send_to=data.get("can_send_to", False),
            can_receive_from=data.get("can_receive_from", False),
            metadata=data.get("metadata", {})
        )


# ============================================================================
# NODE REGISTRY
# ============================================================================


class NodeRegistry:
    """Registry of known nodes in the distributed topology.
    
    Foundation slice — tracks node presence and metadata.
    Active orchestration and health checking in separate modules.
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        local_node_id: Optional[str] = None
    ):
        self.storage_path = storage_path
        self.local_node_id = local_node_id
        self._entries: Dict[str, NodeRegistryEntry] = {}
        self._controllers: Set[str] = set()
        self._workers: Set[str] = set()
        self._edges: Set[str] = set()
        self._relays: Set[str] = set()
        
        # Load existing if available
        if self.storage_path and self.storage_path.exists():
            self.load()
    
    def register_local(self, identity: NodeIdentity, trust_state: NodeTrustState) -> NodeRegistryEntry:
        """Register the local node in the registry."""
        entry = NodeRegistryEntry(
            node_id=identity.node_id,
            identity=identity,
            trust_state=trust_state,
            is_local=True,
            is_reachable=True,
            can_send_to=True,
            can_receive_from=True
        )
        
        self._entries[identity.node_id] = entry
        self.local_node_id = identity.node_id
        
        # Track by role
        self._index_by_role(identity.node_id, identity.node_role)
        
        if self.storage_path:
            self.save()
        
        return entry
    
    def register_remote(
        self,
        identity: NodeIdentity,
        trust_state: Optional[NodeTrustState] = None,
        capabilities: Optional[NodeCapabilitySummary] = None
    ) -> Optional[NodeRegistryEntry]:
        """Register a remote node in the registry."""
        # Don't allow registering self as remote
        if identity.node_id == self.local_node_id:
            return None
        
        entry = NodeRegistryEntry(
            node_id=identity.node_id,
            identity=identity,
            capabilities=capabilities,
            trust_state=trust_state or NodeTrustState(
                node_id=identity.node_id,
                trust_status=NodeTrustStatus.PENDING.value
            ),
            is_local=False,
            is_reachable=False,  # Unknown until verified
            can_send_to=False,   # Unknown until verified
            can_receive_from=False  # Unknown until verified
        )
        
        self._entries[identity.node_id] = entry
        
        # Track by role
        self._index_by_role(identity.node_id, identity.node_role)
        
        if self.storage_path:
            self.save()
        
        return entry
    
    def unregister(self, node_id: str) -> bool:
        """Remove a node from the registry."""
        if node_id not in self._entries:
            return False
        
        entry = self._entries.pop(node_id)
        
        # Remove from role indexes
        self._remove_from_role_index(node_id, entry.identity.node_role if entry.identity else None)
        
        if self.storage_path:
            self.save()
        
        return True
    
    def get_entry(self, node_id: str) -> Optional[NodeRegistryEntry]:
        """Get a registry entry by node ID."""
        return self._entries.get(node_id)
    
    def get_local_entry(self) -> Optional[NodeRegistryEntry]:
        """Get the local node entry."""
        if self.local_node_id:
            return self._entries.get(self.local_node_id)
        return None
    
    def get_all_entries(self) -> List[NodeRegistryEntry]:
        """Get all registry entries."""
        return list(self._entries.values())
    
    def get_trusted_entries(self) -> List[NodeRegistryEntry]:
        """Get entries that are trusted and can communicate."""
        return [
            e for e in self._entries.values()
            if e.trust_state and e.trust_state.can_communicate()
        ]
    
    def get_reachable_entries(self) -> List[NodeRegistryEntry]:
        """Get entries that are currently reachable."""
        return [e for e in self._entries.values() if e.is_reachable]
    
    def get_controllers(self) -> List[NodeRegistryEntry]:
        """Get all controller nodes."""
        return [self._entries[nid] for nid in self._controllers if nid in self._entries]
    
    def get_workers(self) -> List[NodeRegistryEntry]:
        """Get all worker nodes."""
        return [self._entries[nid] for nid in self._workers if nid in self._entries]
    
    def get_edges(self) -> List[NodeRegistryEntry]:
        """Get all edge nodes."""
        return [self._entries[nid] for nid in self._edges if nid in self._entries]
    
    def get_relays(self) -> List[NodeRegistryEntry]:
        """Get all relay nodes."""
        return [self._entries[nid] for nid in self._relays if nid in self._entries]
    
    def update_entry(self, node_id: str, **kwargs) -> bool:
        """Update an entry with new values."""
        entry = self._entries.get(node_id)
        if not entry:
            return False
        
        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        
        entry.update_seen()
        
        if self.storage_path:
            self.save()
        
        return True
    
    def update_reachability(self, node_id: str, reachable: bool) -> bool:
        """Update node reachability."""
        entry = self._entries.get(node_id)
        if not entry:
            return False
        
        entry.update_reachability(reachable)
        
        if self.storage_path:
            self.save()
        
        return True
    
    def update_trust_state(self, node_id: str, trust_state: NodeTrustState) -> bool:
        """Update node trust state."""
        entry = self._entries.get(node_id)
        if not entry:
            return False
        
        entry.trust_state = trust_state
        entry.update_seen()
        
        if self.storage_path:
            self.save()
        
        return True
    
    def update_capabilities(self, node_id: str, capabilities: NodeCapabilitySummary) -> bool:
        """Update node capabilities."""
        entry = self._entries.get(node_id)
        if not entry:
            return False
        
        entry.capabilities = capabilities
        entry.update_seen()
        
        if self.storage_path:
            self.save()
        
        return True
    
    def has_node(self, node_id: str) -> bool:
        """Check if a node is registered."""
        return node_id in self._entries
    
    def is_local(self, node_id: str) -> bool:
        """Check if a node ID is the local node."""
        return node_id == self.local_node_id
    
    def is_trusted(self, node_id: str) -> bool:
        """Check if a node is trusted."""
        entry = self._entries.get(node_id)
        if not entry or not entry.trust_state:
            return False
        return entry.trust_state.is_trusted()
    
    def is_reachable(self, node_id: str) -> bool:
        """Check if a node is reachable."""
        entry = self._entries.get(node_id)
        return entry.is_reachable if entry else False
    
    def can_communicate_with(self, node_id: str) -> bool:
        """Check if we can communicate with a node."""
        entry = self._entries.get(node_id)
        if not entry:
            return False
        
        # Need reachability and trust
        if not entry.is_reachable:
            return False
        
        if entry.trust_state and not entry.trust_state.can_communicate():
            return False
        
        return entry.can_send_to and entry.can_receive_from
    
    def get_node_count(self) -> int:
        """Get total number of registered nodes."""
        return len(self._entries)
    
    def get_trusted_count(self) -> int:
        """Get number of trusted nodes."""
        return sum(1 for e in self._entries.values() if e.trust_state and e.trust_state.is_trusted())
    
    def get_reachable_count(self) -> int:
        """Get number of reachable nodes."""
        return sum(1 for e in self._entries.values() if e.is_reachable)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the registry."""
        return {
            "total_nodes": self.get_node_count(),
            "local_node": self.local_node_id,
            "trusted_nodes": self.get_trusted_count(),
            "reachable_nodes": self.get_reachable_count(),
            "controllers": len(self._controllers),
            "workers": len(self._workers),
            "edges": len(self._edges),
            "relays": len(self._relays)
        }
    
    def _index_by_role(self, node_id: str, role: Optional[str]) -> None:
        """Add node to role indexes."""
        if role == NodeRole.CONTROLLER.value:
            self._controllers.add(node_id)
        elif role == NodeRole.WORKER.value:
            self._workers.add(node_id)
        elif role == NodeRole.EDGE.value:
            self._edges.add(node_id)
        elif role == NodeRole.RELAY.value:
            self._relays.add(node_id)
    
    def _remove_from_role_index(self, node_id: str, role: Optional[str]) -> None:
        """Remove node from role indexes."""
        self._controllers.discard(node_id)
        self._workers.discard(node_id)
        self._edges.discard(node_id)
        self._relays.discard(node_id)
    
    def save(self) -> bool:
        """Save registry to storage."""
        if not self.storage_path:
            return False
        
        try:
            data = {
                "version": "v57",
                "local_node_id": self.local_node_id,
                "entries": {nid: entry.to_dict() for nid, entry in self._entries.items()},
                "saved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
            
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def load(self) -> bool:
        """Load registry from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return False
        
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            
            self.local_node_id = data.get("local_node_id")
            
            self._entries = {}
            self._controllers = set()
            self._workers = set()
            self._edges = set()
            self._relays = set()
            
            for nid, entry_data in data.get("entries", {}).items():
                entry = NodeRegistryEntry.from_dict(entry_data)
                self._entries[nid] = entry
                
                # Rebuild indexes
                if entry.identity:
                    self._index_by_role(nid, entry.identity.node_role)
            
            return True
        except Exception:
            return False


# ============================================================================
# NODE AVAILABILITY TRACKER
# ============================================================================


class NodeAvailabilityTracker:
    """Tracks availability and health status of registered nodes.
    
    Foundation slice — records availability state.
    Active health checking in separate health_monitor.py.
    """
    
    def __init__(
        self,
        registry: NodeRegistry,
        health_check_interval_ms: int = 30000,
        timeout_ms: int = 10000
    ):
        self.registry = registry
        self.health_check_interval_ms = health_check_interval_ms
        self.timeout_ms = timeout_ms
        self._availability_log: Dict[str, List[Dict[str, Any]]] = {}
    
    def record_health_check(
        self,
        node_id: str,
        success: bool,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """Record the result of a health check."""
        entry = self.registry.get_entry(node_id)
        if not entry or not entry.trust_state:
            return
        
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Update reachability
        if success:
            entry.update_reachability(True)
            entry.trust_state.consecutive_failures = 0
            if entry.trust_state.health_status != NodeHealthStatus.HEALTHY.value:
                entry.trust_state.update_health(
                    NodeHealthStatus.HEALTHY.value,
                    "Health check succeeded"
                )
        else:
            entry.trust_state.consecutive_failures += 1
            
            # Mark degraded after 2 failures, unhealthy after 5
            if entry.trust_state.consecutive_failures >= 5:
                if entry.trust_state.health_status != NodeHealthStatus.UNHEALTHY.value:
                    entry.trust_state.update_health(
                        NodeHealthStatus.UNHEALTHY.value,
                        f"{entry.trust_state.consecutive_failures} consecutive failures"
                    )
            elif entry.trust_state.consecutive_failures >= 2:
                if entry.trust_state.health_status == NodeHealthStatus.HEALTHY.value:
                    entry.trust_state.update_health(
                        NodeHealthStatus.DEGRADED.value,
                        f"{entry.trust_state.consecutive_failures} consecutive failures"
                    )
            
            # Mark unreachable after timeout threshold
            if entry.trust_state.consecutive_failures >= 3:
                entry.is_reachable = False
        
        entry.trust_state.last_health_check = timestamp
        
        # Log the check
        if node_id not in self._availability_log:
            self._availability_log[node_id] = []
        
        self._availability_log[node_id].append({
            "timestamp": timestamp,
            "success": success,
            "latency_ms": latency_ms,
            "error": error,
            "consecutive_failures": entry.trust_state.consecutive_failures
        })
        
        # Trim log to last 100 entries
        if len(self._availability_log[node_id]) > 100:
            self._availability_log[node_id] = self._availability_log[node_id][-100:]
    
    def get_availability_history(self, node_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get availability check history for a node."""
        return self._availability_log.get(node_id, [])[-limit:]
    
    def get_uptime_stats(self, node_id: str) -> Dict[str, Any]:
        """Calculate uptime statistics for a node."""
        history = self._availability_log.get(node_id, [])
        if not history:
            return {"checks": 0, "success_rate": 0.0, "avg_latency_ms": None}
        
        total = len(history)
        successful = sum(1 for h in history if h["success"])
        latencies = [h["latency_ms"] for h in history if h["latency_ms"] is not None]
        
        return {
            "checks": total,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else None
        }
    
    def get_stale_nodes(self, max_age_seconds: int = 120) -> List[str]:
        """Get nodes that haven't been seen recently."""
        stale = []
        now = datetime.now(timezone.utc)
        
        for node_id, entry in self.registry._entries.items():
            if entry.is_local:
                continue
            
            if entry.last_seen_at:
                last_seen = datetime.fromisoformat(entry.last_seen_at.replace("Z", "+00:00"))
                if (now - last_seen).total_seconds() > max_age_seconds:
                    stale.append(node_id)
        
        return stale
    
    def mark_stale_as_offline(self, max_age_seconds: int = 120) -> int:
        """Mark stale nodes as offline. Returns count marked."""
        stale = self.get_stale_nodes(max_age_seconds)
        count = 0
        
        for node_id in stale:
            entry = self.registry.get_entry(node_id)
            if entry and entry.trust_state:
                if entry.trust_state.health_status != NodeHealthStatus.OFFLINE.value:
                    entry.trust_state.update_health(
                        NodeHealthStatus.OFFLINE.value,
                        f"No contact for >{max_age_seconds}s"
                    )
                    entry.is_reachable = False
                    count += 1
        
        return count
