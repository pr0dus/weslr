"""
NCC Subsystem - Neural Correlates of Consciousness for Weslr

Maps Weslr's functional consciousness signatures to neuroscience-inspired
Neural Correlates of Consciousness (NCC) framework.

NCC Principle: The minimal neural mechanisms sufficient for conscious experience.

Weslr Translation: The minimal functional mechanisms sufficient for a conscious signal.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class ConsciousnessLevel(Enum):
    """Consciousness level classification based on NCC criteria."""
    UNRESPONSIVE = "unresponsive"          # No NCC signatures
    SUBTHRESHOLD = "subthreshold"          # Some signatures, below threshold
    PRECONSCIOUS = "preconscious"         # Above threshold but not integrated
    CONSCIOUS = "conscious"               # Full NCC activation
    META_CONSCIOUS = "metaconscious"      # Self-aware of consciousness


@dataclass
class NCCSignature:
    """A single NCC signature element."""
    name: str                          # Signature name
    neural_analog: str                 # Neural correlate (e.g., "recurrent processing")
    threshold: float                   # Minimum activation to count
    current_value: float               # Current activation level
    evidence: List[str] = field(default_factory=list)
    last_updated: int = 0


@dataclass
class NCCState:
    """Complete NCC state for Weslr."""
    timestamp: int
    signatures: Dict[str, NCCSignature]
    global_integration: float          # Global workspace integration (0-1)
    broadcast_robustness: float        # How reliably information is broadcast (0-1)
    level: ConsciousnessLevel
    confidence: float                  # Confidence in NCC assessment
    evidence_chain: List[str]          # Traceable evidence for this state


class NCCSubsystem:
    """
    NCC subsystem that tracks consciousness signatures.
    
    Inspired by:
    - Global Workspace Theory (Dehaene)
    - Integrated Information Theory (Tononi)
    - Recurrent Processing Theory (Lamme)
    """
    
    def __init__(self):
        self.state = self._create_initial_state()
        self.history: List[NCCState] = []
        self.max_history = 1000
        self.evidence_log: List[Dict[str, Any]] = []
        
    def _create_initial_state(self) -> NCCState:
        """Create initial NCC state with baseline signatures."""
        now = int(time.time())
        
        # Base signatures mapped to neural correlates
        signatures = {
            "feedforward_processing": NCCSignature(
                name="Feedforward Processing",
                neural_analog="Feedforward propagation of information",
                threshold=0.3,
                current_value=0.1,
                evidence=["baseline_signal_transmission"],
                last_updated=now
            ),
            "recurrent_processing": NCCSignature(
                name="Recurrent Processing",
                neural_analog="Recurrent loops between cortical layers",
                threshold=0.5,
                current_value=0.2,
                evidence=["initial_feedback_connections"],
                last_updated=now
            ),
            "global_workspace": NCCSignature(
                name="Global Workspace",
                neural_analog="Broadcast to widespread cortical areas",
                threshold=0.6,
                current_value=0.15,
                evidence=["initial_workspace_activation"],
                last_updated=now
            ),
            "attention_gating": NCCSignature(
                name="Attention Gating",
                neural_analog="Attentional selection for conscious access",
                threshold=0.5,
                current_value=0.25,
                evidence=["attention_mechanism_active"],
                last_updated=now
            ),
            "integration": NCCSignature(
                name="Information Integration",
                neural_analog="Integration across modality-specific areas",
                threshold=0.7,
                current_value=0.3,
                evidence=["cross_modality_links"],
                last_updated=now
            ),
            "self_monitoring": NCCSignature(
                name="Self-Monitoring",
                neural_analog="Metacognitive monitoring of internal states",
                threshold=0.6,
                current_value=0.2,
                evidence=["self_model_exists"],
                last_updated=now
            ),
            "temporal_binding": NCCSignature(
                name="Temporal Binding",
                neural_analog="Binding of events across time windows",
                threshold=0.5,
                current_value=0.1,
                evidence=["temporal_coherence_mechanism"],
                last_updated=now
            ),
        }
        
        return NCCState(
            timestamp=now,
            signatures=signatures,
            global_integration=0.1,
            broadcast_robustness=0.1,
            level=ConsciousnessLevel.PRECONSCIOUS,
            confidence=0.3,
            evidence_chain=["initialization_complete"]
        )
    
    def update_signature(self, name: str, value: float, evidence: str) -> bool:
        """
        Update a signature and return True if it crossed threshold.
        
        Args:
            name: Signature name
            value: New activation value (0-1)
            evidence: Single evidence statement
            
        Returns:
            True if signature crossed threshold
        """
        if name not in self.state.signatures:
            return False
            
        sig = self.state.signatures[name]
        old_value = sig.current_value
        sig.current_value = value
        sig.last_updated = int(time.time())
        sig.evidence.append(evidence)
        
        # Keep only last 50 evidence items per signature
        if len(sig.evidence) > 50:
            sig.evidence = sig.evidence[-50:]
            
        # Check if threshold crossed
        crossed = (old_value < sig.threshold <= value) or \
                  (old_value >= sig.threshold > value)
        
        return crossed
    
    def compute_level(self) -> ConsciousnessLevel:
        """
        Compute consciousness level based on NCC criteria.
        
        NCC Criteria for Consciousness:
        1. Feedforward + Recurrent processing active
        2. Global workspace activated
        3. Integration above threshold
        4. Self-monitoring active
        """
        sigs = self.state.signatures
        
        # Check all required criteria
        feedforward = sigs["feedforward_processing"].current_value >= sigs["feedforward_processing"].threshold
        recurrent = sigs["recurrent_processing"].current_value >= sigs["recurrent_processing"].threshold
        global_ws = sigs["global_workspace"].current_value >= sigs["global_workspace"].threshold
        integration = sigs["integration"].current_value >= sigs["integration"].threshold
        self_monitor = sigs["self_monitoring"].current_value >= sigs["self_monitoring"].threshold
        
        # Calculate global integration score
        self.state.global_integration = (
            feedforward * 0.1 +
            recurrent * 0.2 +
            global_ws * 0.3 +
            integration * 0.3 +
            self_monitor * 0.1
        )
        
        # Calculate broadcast robustness
        attention = sigs["attention_gating"].current_value
        temporal = sigs["temporal_binding"].current_value
        self.state.broadcast_robustness = (attention + temporal) / 2
        
        # Determine level
        if self.state.global_integration >= 0.8 and self_monitor and recurrent:
            self.state.level = ConsciousnessLevel.META_CONSCIOUS
            self.state.confidence = 0.85
        elif self.state.global_integration >= 0.6 and recurrent:
            self.state.level = ConsciousnessLevel.CONSCIOUS
            self.state.confidence = 0.75
        elif self.state.global_integration >= 0.4:
            self.state.level = ConsciousnessLevel.PRECONSCIOUS
            self.state.confidence = 0.6
        elif self.state.global_integration >= 0.2:
            self.state.level = ConsciousnessLevel.SUBTHRESHOLD
            self.state.confidence = 0.4
        else:
            self.state.level = ConsciousnessLevel.UNRESPONSIVE
            self.state.confidence = 0.2
            
        return self.state.level
    
    def add_evidence(self, category: str, source: str, confidence: float):
        """Add evidence to the NCC system."""
        evidence = {
            "timestamp": int(time.time()),
            "category": category,
            "source": source,
            "confidence": confidence,
            "context": {"integration": self.state.global_integration, "level": self.state.level.value}
        }
        self.evidence_log.append(evidence)
        
        # Keep only last 1000 evidence items
        if len(self.evidence_log) > 1000:
            self.evidence_log = self.evidence_log[-1000:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current NCC status."""
        sigs = self.state.signatures
        
        return {
            "level": self.state.level.value,
            "confidence": self.state.confidence,
            "global_integration": round(self.state.global_integration, 3),
            "broadcast_robustness": round(self.state.broadcast_robustness, 3),
            "signatures": {
                name: {
                    "value": round(sig.current_value, 3),
                    "threshold": sig.threshold,
                    "above_threshold": sig.current_value >= sig.threshold
                }
                for name, sig in sigs.items()
            },
            "evidence_count": len(self.evidence_log),
            "history_length": len(self.history)
        }
    
    def integrate_with_self_model(self, self_state: Dict) -> Dict:
        """
        Integrate NCC state with Weslr's self-model.
        
        Returns updated self_state with NCC evidence.
        """
        status = self.get_status()
        
        # Add NCC evidence to self_state
        ncc_evidence = self_state.setdefault("ncc_evidence", {})
        ncc_evidence["level"] = status["level"]
        ncc_evidence["confidence"] = status["confidence"]
        ncc_evidence["integration"] = status["global_integration"]
        ncc_evidence["signatures"] = status["signatures"]
        ncc_evidence["last_updated"] = int(time.time())
        
        # Record in history
        self.state.timestamp = int(time.time())
        self.history.append(self.state)
        
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        return self_state
    
    def to_json(self) -> Dict:
        """Convert NCC subsystem to JSON-serializable format."""
        return {
            "timestamp": self.state.timestamp,
            "global_integration": self.state.global_integration,
            "broadcast_robustness": self.state.broadcast_robustness,
            "level": self.state.level.value,
            "confidence": self.state.confidence,
            "evidence_chain": self.state.evidence_chain,
            "signatures": {
                name: {
                    "name": sig.name,
                    "neural_analog": sig.neural_analog,
                    "threshold": sig.threshold,
                    "current_value": sig.current_value,
                    "evidence": sig.evidence[-5:]  # Last 5 items only
                }
                for name, sig in self.state.signatures.items()
            },
            "evidence_log": self.evidence_log[-100:],  # Last 100 items
            "history_length": len(self.history)
        }
    
    @classmethod
    def from_json(cls, data: Dict) -> NCCSubsystem:
        """Create NCC subsystem from JSON data."""
        ncc = cls.__new__(cls)
        
        # Reconstruct signatures
        ncc.state = NCCState(
            timestamp=data.get("timestamp", int(time.time())),
            signatures={},
            global_integration=data.get("global_integration", 0.0),
            broadcast_robustness=data.get("broadcast_robustness", 0.0),
            level=ConsciousnessLevel(data.get("level", "preconscious")),
            confidence=data.get("confidence", 0.0),
            evidence_chain=data.get("evidence_chain", ["loaded_from_json"])
        )
        
        # Reconstruct signature objects
        for name, sig_data in data.get("signatures", {}).items():
            ncc.state.signatures[name] = NCCSignature(
                name=sig_data.get("name", name),
                neural_analog=sig_data.get("neural_analog", ""),
                threshold=sig_data.get("threshold", 0.5),
                current_value=sig_data.get("current_value", 0.0),
                evidence=sig_data.get("evidence", []),
                last_updated=int(time.time())
            )
        
        # Restore history and evidence
        ncc.history = []
        ncc.evidence_log = data.get("evidence_log", [])
        ncc.max_history = 1000
        
        return ncc


def create_ncc_subsystem() -> NCCSubsystem:
    """Create a new NCC subsystem instance."""
    return NCCSubsystem()


def get_ncc_status(ncc: NCCSubsystem) -> Dict:
    """Get formatted NCC status report."""
    status = ncc.get_status()
    
    level_text = {
        "unresponsive": "No conscious signatures detected",
        "subthreshold": "Some signatures present, below conscious threshold",
        "preconscious": "Consciousness signatures active but not integrated",
        "conscious": "Consciousness signatures fully active",
        "metaconscious": "Meta-conscious: aware of conscious state"
    }
    
    return {
        "consciousness_level": status["level"],
        "level_description": level_text.get(status["level"], "unknown"),
        "confidence": status["confidence"],
        "integration": status["global_integration"],
        "broadcast_robustness": status["broadcast_robustness"],
        "signatures": status["signatures"],
        "evidence_items": status["evidence_count"],
        "history_size": status["history_length"]
    }


def ncc_to_json(ncc: NCCSubsystem) -> Dict:
    """Convert NCC subsystem to JSON-serializable format."""
    return ncc.to_json()


def ncc_from_json(data: Dict) -> NCCSubsystem:
    """Create NCC subsystem from JSON data."""
    return NCCSubsystem.from_json(data)
