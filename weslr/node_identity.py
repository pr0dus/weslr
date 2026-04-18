"""Node Identity and Capability Management (v57)

Foundation slice for distributed multi-node WESLR architecture.
Defines node identity, roles, capabilities, trust/health status,
and local vs remote distinction for communication scope.

Architecture:
  - NodeRole enum — controller, worker, edge, relay
  - NodeTrustStatus enum — trusted, provisional, untrusted, revoked
  - NodeHealthStatus enum — healthy, degraded, unhealthy, unknown
  - NodeIdentity — canonical node identification
  - NodeCapabilitySummary — what this node can do
  - NodeTrustState — trust and health tracking
  - NodeIdentityManager — identity lifecycle

Rules:
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - Operator-first (status visible)
  - Foundation only — no orchestration yet
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ============================================================================
# ENUMS
# ============================================================================


class NodeRole(str, Enum):
    """Role of a node in the distributed topology."""
    CONTROLLER = "controller"    # Central coordination node
    WORKER = "worker"            # General compute node
    EDGE = "edge"                # Edge/latency-optimized node
    RELAY = "relay"              # Communication relay node
    OBSERVER = "observer"        # Read-only monitoring node


class NodeTrustStatus(str, Enum):
    """Trust status of a node in the distributed topology."""
    TRUSTED = "trusted"          # Fully trusted, all capabilities enabled
    PROVISIONAL = "provisional"  # Temporary trust, limited capabilities
    UNTRUSTED = "untrusted"      # Explicitly untrusted, no capabilities
    REVOKED = "revoked"          # Trust revoked, excluded from operations
    PENDING = "pending"          # Awaiting trust verification


class NodeHealthStatus(str, Enum):
    """Health status of a node."""
    HEALTHY = "healthy"          # All systems nominal
    DEGRADED = "degraded"        # Operating with reduced capacity
    UNHEALTHY = "unhealthy"      # Critical issues, minimal operation
    UNKNOWN = "unknown"          # Status not yet determined
    OFFLINE = "offline"          # Node unreachable


class NodeLocationType(str, Enum):
    """Physical/Network location type of a node."""
    LOCAL = "local"              # Same host/process
    LAN = "lan"                  # Same local network
    WAN = "wan"                  # Wide area network
    INTERNET = "internet"        # Public internet


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class NodeCapability:
    """Single capability that a node can provide."""
    capability_type: str         # e.g., "compute", "storage", "inference"
    capability_name: str         # e.g., "cpu-compute", "evidence-store"
    version: str = "1.0"         # Capability version
    capacity: Optional[float] = None  # Capacity metric (e.g., 8.0 for 8 cores)
    available: bool = True         # Currently available
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeCapabilitySummary:
    """Summary of all capabilities a node provides."""
    node_id: str
    capabilities: List[NodeCapability] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def get_capability(self, capability_type: str, capability_name: str) -> Optional[NodeCapability]:
        """Get a specific capability by type and name."""
        for cap in self.capabilities:
            if cap.capability_type == capability_type and cap.capability_name == capability_name:
                return cap
        return None
    
    def has_capability(self, capability_type: str, capability_name: Optional[str] = None) -> bool:
        """Check if node has a capability."""
        for cap in self.capabilities:
            if cap.capability_type == capability_type:
                if capability_name is None or cap.capability_name == capability_name:
                    return cap.available
        return False
    
    def get_available_capabilities(self) -> List[NodeCapability]:
        """Get list of currently available capabilities."""
        return [c for c in self.capabilities if c.available]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "capabilities": [
                {
                    "capability_type": c.capability_type,
                    "capability_name": c.capability_name,
                    "version": c.version,
                    "capacity": c.capacity,
                    "available": c.available,
                    "metadata": c.metadata
                }
                for c in self.capabilities
            ],
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeCapabilitySummary":
        """Create from dictionary."""
        caps = []
        for c in data.get("capabilities", []):
            caps.append(NodeCapability(
                capability_type=c["capability_type"],
                capability_name=c["capability_name"],
                version=c.get("version", "1.0"),
                capacity=c.get("capacity"),
                available=c.get("available", True),
                metadata=c.get("metadata", {})
            ))
        return cls(
            node_id=data["node_id"],
            capabilities=caps,
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        )


@dataclass
class NodeIdentity:
    """Canonical identity for a WESLR node."""
    
    # Core identity
    node_id: str                 # UUID-based unique identifier
    node_name: str               # Human-readable name
    node_role: str = NodeRole.WORKER.value
    
    # Network identity
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    location_type: str = NodeLocationType.LOCAL.value
    
    # Classification
    is_local: bool = True        # True if this is the local node
    is_controller: bool = False  # True if this node can coordinate others
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    version: str = "v57"         # Schema version
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_role": self.node_role,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "port": self.port,
            "location_type": self.location_type,
            "is_local": self.is_local,
            "is_controller": self.is_controller,
            "created_at": self.created_at,
            "version": self.version,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeIdentity":
        """Create from dictionary."""
        return cls(
            node_id=data["node_id"],
            node_name=data["node_name"],
            node_role=data.get("node_role", NodeRole.WORKER.value),
            hostname=data.get("hostname"),
            ip_address=data.get("ip_address"),
            port=data.get("port"),
            location_type=data.get("location_type", NodeLocationType.LOCAL.value),
            is_local=data.get("is_local", True),
            is_controller=data.get("is_controller", False),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            version=data.get("version", "v57"),
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def create_local(cls, node_name: str, role: NodeRole = NodeRole.WORKER) -> "NodeIdentity":
        """Create identity for the local node."""
        node_id = str(uuid.uuid4())
        return cls(
            node_id=node_id,
            node_name=node_name,
            node_role=role.value,
            is_local=True,
            is_controller=(role == NodeRole.CONTROLLER),
            location_type=NodeLocationType.LOCAL.value
        )


@dataclass
class NodeTrustState:
    """Trust and health state for a node."""
    
    node_id: str
    trust_status: str = NodeTrustStatus.PENDING.value
    health_status: str = NodeHealthStatus.UNKNOWN.value
    
    # Trust metrics
    trust_score: float = 0.0     # 0.0-1.0 trust score
    last_verified_at: Optional[str] = None
    verification_method: Optional[str] = None  # e.g., "manual", "token", "certificate"
    
    # Health metrics
    last_health_check: Optional[str] = None
    health_check_interval_ms: int = 30000     # 30 seconds default
    consecutive_failures: int = 0
    
    # Communication scope
    allowed_scopes: List[str] = field(default_factory=list)  # What this node can access
    restricted_scopes: List[str] = field(default_factory=list)  # What this node cannot access
    
    # Audit trail
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "trust_status": self.trust_status,
            "health_status": self.health_status,
            "trust_score": self.trust_score,
            "last_verified_at": self.last_verified_at,
            "verification_method": self.verification_method,
            "last_health_check": self.last_health_check,
            "health_check_interval_ms": self.health_check_interval_ms,
            "consecutive_failures": self.consecutive_failures,
            "allowed_scopes": self.allowed_scopes,
            "restricted_scopes": self.restricted_scopes,
            "status_history": self.status_history,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeTrustState":
        """Create from dictionary."""
        return cls(
            node_id=data["node_id"],
            trust_status=data.get("trust_status", NodeTrustStatus.PENDING.value),
            health_status=data.get("health_status", NodeHealthStatus.UNKNOWN.value),
            trust_score=data.get("trust_score", 0.0),
            last_verified_at=data.get("last_verified_at"),
            verification_method=data.get("verification_method"),
            last_health_check=data.get("last_health_check"),
            health_check_interval_ms=data.get("health_check_interval_ms", 30000),
            consecutive_failures=data.get("consecutive_failures", 0),
            allowed_scopes=data.get("allowed_scopes", []),
            restricted_scopes=data.get("restricted_scopes", []),
            status_history=data.get("status_history", []),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        )
    
    def is_trusted(self) -> bool:
        """Check if node is trusted."""
        return self.trust_status == NodeTrustStatus.TRUSTED.value
    
    def is_healthy(self) -> bool:
        """Check if node is healthy."""
        return self.health_status == NodeHealthStatus.HEALTHY.value
    
    def can_communicate(self) -> bool:
        """Check if node can participate in communication."""
        return (
            self.trust_status in (NodeTrustStatus.TRUSTED.value, NodeTrustStatus.PROVISIONAL.value)
            and self.health_status not in (NodeHealthStatus.OFFLINE.value, NodeHealthStatus.UNHEALTHY.value)
        )
    
    def update_trust(self, new_status: str, reason: str = "") -> None:
        """Update trust status with history tracking."""
        old_status = self.trust_status
        self.trust_status = new_status
        self.status_history.append({
            "type": "trust",
            "from": old_status,
            "to": new_status,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def update_health(self, new_status: str, reason: str = "") -> None:
        """Update health status with history tracking."""
        old_status = self.health_status
        self.health_status = new_status
        self.status_history.append({
            "type": "health",
            "from": old_status,
            "to": new_status,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ============================================================================
# NODE IDENTITY MANAGER
# ============================================================================


class NodeIdentityManager:
    """Manages node identities in the distributed topology.
    
    Foundation slice — manages local identity only.
    Multi-node registry in separate node_registry.py.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path
        self._local_identity: Optional[NodeIdentity] = None
        self._local_capabilities: Optional[NodeCapabilitySummary] = None
        self._local_trust: Optional[NodeTrustState] = None
    
    def initialize_local_node(
        self,
        node_name: str,
        role: NodeRole = NodeRole.WORKER,
        capabilities: Optional[List[NodeCapability]] = None
    ) -> NodeIdentity:
        """Initialize the local node identity."""
        identity = NodeIdentity.create_local(node_name, role)
        self._local_identity = identity
        
        # Initialize capabilities
        self._local_capabilities = NodeCapabilitySummary(
            node_id=identity.node_id,
            capabilities=capabilities or []
        )
        
        # Initialize trust state
        self._local_trust = NodeTrustState(
            node_id=identity.node_id,
            trust_status=NodeTrustStatus.TRUSTED.value if role == NodeRole.CONTROLLER else NodeTrustStatus.PENDING.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        if self.storage_path:
            self._save_identity()
        
        return identity
    
    def get_local_identity(self) -> Optional[NodeIdentity]:
        """Get the local node identity."""
        return self._local_identity
    
    def get_local_capabilities(self) -> Optional[NodeCapabilitySummary]:
        """Get local node capabilities."""
        return self._local_capabilities
    
    def get_local_trust_state(self) -> Optional[NodeTrustState]:
        """Get local node trust state."""
        return self._local_trust
    
    def add_capability(self, capability: NodeCapability) -> bool:
        """Add a capability to the local node."""
        if self._local_capabilities is None:
            return False
        
        # Check if already exists
        existing = self._local_capabilities.get_capability(
            capability.capability_type, capability.capability_name
        )
        if existing:
            # Update existing
            existing.version = capability.version
            existing.capacity = capability.capacity
            existing.available = capability.available
            existing.metadata.update(capability.metadata)
        else:
            self._local_capabilities.capabilities.append(capability)
        
        self._local_capabilities.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        if self.storage_path:
            self._save_identity()
        
        return True
    
    def remove_capability(self, capability_type: str, capability_name: str) -> bool:
        """Remove a capability from the local node."""
        if self._local_capabilities is None:
            return False
        
        self._local_capabilities.capabilities = [
            c for c in self._local_capabilities.capabilities
            if not (c.capability_type == capability_type and c.capability_name == capability_name)
        ]
        
        self._local_capabilities.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        if self.storage_path:
            self._save_identity()
        
        return True
    
    def update_trust_status(self, status: str, reason: str = "") -> bool:
        """Update the local node trust status."""
        if self._local_trust is None:
            return False
        
        self._local_trust.update_trust(status, reason)
        
        if self.storage_path:
            self._save_identity()
        
        return True
    
    def update_health_status(self, status: str, reason: str = "") -> bool:
        """Update the local node health status."""
        if self._local_trust is None:
            return False
        
        self._local_trust.update_health(status, reason)
        
        if self.storage_path:
            self._save_identity()
        
        return True
    
    def _save_identity(self) -> None:
        """Save identity to storage."""
        if self.storage_path is None:
            return
        
        data = {
            "identity": self._local_identity.to_dict() if self._local_identity else None,
            "capabilities": self._local_capabilities.to_dict() if self._local_capabilities else None,
            "trust_state": self._local_trust.to_dict() if self._local_trust else None
        }
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_identity(self) -> bool:
        """Load identity from storage."""
        if self.storage_path is None or not self.storage_path.exists():
            return False
        
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            
            if data.get("identity"):
                self._local_identity = NodeIdentity.from_dict(data["identity"])
            if data.get("capabilities"):
                self._local_capabilities = NodeCapabilitySummary.from_dict(data["capabilities"])
            if data.get("trust_state"):
                self._local_trust = NodeTrustState.from_dict(data["trust_state"])
            
            return True
        except Exception:
            return False


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def generate_node_id() -> str:
    """Generate a unique node identifier."""
    return str(uuid.uuid4())


def create_default_capabilities(role: NodeRole) -> List[NodeCapability]:
    """Create default capabilities for a node role."""
    capabilities = [
        NodeCapability("core", "identity", "1.0", 1.0, True),
        NodeCapability("core", "status-reporting", "1.0", 1.0, True),
    ]
    
    if role == NodeRole.CONTROLLER:
        capabilities.extend([
            NodeCapability("coordination", "node-registry", "1.0", 1.0, True),
            NodeCapability("coordination", "task-dispatch", "1.0", 1.0, True),
        ])
    
    if role == NodeRole.WORKER:
        capabilities.extend([
            NodeCapability("compute", "general", "1.0", 1.0, True),
            NodeCapability("compute", "weslr-core", "1.0", 1.0, True),
        ])
    
    if role == NodeRole.EDGE:
        capabilities.extend([
            NodeCapability("compute", "low-latency", "1.0", 1.0, True),
            NodeCapability("storage", "cache", "1.0", 1.0, True),
        ])
    
    if role == NodeRole.RELAY:
        capabilities.extend([
            NodeCapability("network", "message-routing", "1.0", 1.0, True),
            NodeCapability("network", "broadcast", "1.0", 1.0, True),
        ])
    
    return capabilities
