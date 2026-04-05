"""Runtime Write Bridge for Concept Graph

Integrates runtime events into the Concept Graph:
- Weather results → concepts + evidence
- System time results → concepts + evidence
- Unsupported outcomes → concepts + uncertainty tracking
- Bounded reflections → concepts + model-asserted evidence

All writes are:
- Additive only (no deletions)
- Reversible (tracked in bridge metadata)
- Non-invasive (no modification of runtime logic)
- Category-preserved evidence (source-backed, inferred, model-asserted, cached, user-provided)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add workspace root to path for imports
import sys
workspace_root = str(Path('/data/data/com.termux/files/home/.openclaw/workspace').resolve())
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from concept_graph import Concept, Evidence, Link
from concept_graph import store as concept_store
from concept_graph.bridge.evidence import EvidenceBridge
from concept_graph.semantics import EvidenceCategory


class RuntimeWriteBridge:
    """Write bridge from runtime events to Concept Graph.
    
    Maps runtime results to graph concepts and links.
    Preserves evidence categories from runtime sources.
    """
    
    def __init__(self, workspace_dir: str = None):
        """Initialize runtime write bridge."""
        self.workspace_dir = workspace_dir or str(
            Path('/data/data/com.termux/files/home/.openclaw/workspace')
        )
        self.runtime_write_log_path = Path(self.workspace_dir) / "weslr" / "concept_graph" / "bridge" / "runtime_writes.json"
        self._evidence_bridge = EvidenceBridge()
    
    def _get_graph_store(self) -> concept_store.ConceptGraphStore:
        """Get concept graph store (created if needed)."""
        store_path = Path(self.workspace_dir) / "weslr" / "concept_graph"
        return concept_store.ConceptGraphStore(graph_dir=store_path)
    
    def _load_write_log(self) -> Dict[str, Any]:
        """Load runtime write log for deduplication."""
        if self.runtime_write_log_path.exists():
            try:
                return json.loads(self.runtime_write_log_path.read_text())
            except Exception:
                pass
        return {"writes": [], "last_run": int(time.time())}
    
    def _record_write(self, event_id: str, event_type: str) -> None:
        """Record a write for deduplication."""
        log = self._load_write_log()
        log["writes"].append({
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": int(time.time()),
        })
        # Keep only last 1000 writes
        log["writes"] = log["writes"][-1000:]
        log["last_run"] = int(time.time())
        self.runtime_write_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.runtime_write_log_path.write_text(json.dumps(log, indent=2))
    
    def _check_duplicate(self, event_id: str, event_type: str) -> bool:
        """Check if event was already processed (deduplication)."""
        log = self._load_write_log()
        for w in log.get("writes", []):
            if w.get("event_id") == event_id and w.get("event_type") == event_type:
                return True
        return False
    
    def write_weather_result(
        self,
        location: str,
        weather_data: Dict[str, Any],
        source_id: str = None,
    ) -> Dict[str, Any]:
        """Write weather result to Concept Graph.
        
        Creates:
        - Weather concept (location-based)
        - Evidence from weather data
        - Temporal link to system time
        
        Args:
            location: Weather location
            weather_data: Weather observation data
            source_id: Optional event source identifier
        
        Returns:
            Write statistics
        """
        store = self._get_graph_store()
        
        # Deduplication check
        event_id = source_id or f"weather-{location}-{int(time.time())}"
        if self._check_duplicate(event_id, "weather"):
            return {"skipped": True, "reason": "duplicate"}
        
        # Create weather concept
        concept = Concept(
            id=f"weather-{location.lower().replace(' ', '-')}",
            name=f"Weather: {location}",
            type="concept",
            description=f"Current weather conditions for {location}",
            tags=["weather", "environment", "observation"],
            confidence=0.95,
            created_at=int(time.time()),
            last_updated=int(time.time()),
        )
        
        # Create evidence from weather data
        evidence = self._evidence_bridge.from_weather_source(
            location,
            weather_data,
            source_id=source_id,
        )
        concept.add_evidence(evidence)
        
        # Create temporal link to system time
        time_concept = Concept(
            id=f"time-{int(time.time()) // 3600}",  # Hourly bucket
            name=f"Time: {time.strftime('%Y-%m-%d %H:00')}",
            type="concept",
            description="Hourly time bucket",
            tags=["time", "temporal"],
            confidence=1.0,
        )
        
        # Link weather to time
        time_evidence = self._evidence_bridge.from_time_source(
            int(time.time()),
            source_id=f"time-{int(time.time())}",
        )
        
        weather_link = Link(
            source_id=concept.id,
            target_id=time_concept.id,
            link_type="observed_at",
            confidence=0.95,
            reason=f"Weather observation linked to temporal bucket",
            evidence=[evidence, time_evidence],
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        concept.add_link(weather_link)
        
        # Save concept
        store.save_concept(concept)
        
        # Record write
        self._record_write(event_id, "weather")
        
        return {
            "skipped": False,
            "concept_id": concept.id,
            "evidence_count": len(concept.evidence),
            "link_count": len(concept.links),
        }
    
    def write_time_result(
        self,
        timestamp: int = None,
        source_id: str = None,
    ) -> Dict[str, Any]:
        """Write system time result to Concept Graph.
        
        Creates:
        - Time concept (hourly bucket)
        - Evidence from system time
        
        Args:
            timestamp: Time reference (defaults to now)
            source_id: Optional event source identifier
        
        Returns:
            Write statistics
        """
        store = self._get_graph_store()
        
        ts = timestamp or int(time.time())
        bucket = ts // 3600  # Hourly bucket
        
        # Deduplication check
        event_id = source_id or f"time-{bucket}"
        if self._check_duplicate(event_id, "time"):
            return {"skipped": True, "reason": "duplicate"}
        
        # Create time concept
        concept = Concept(
            id=f"time-{bucket}",
            name=f"Time: {time.strftime('%Y-%m-%d %H:00', time.localtime(ts))}",
            type="concept",
            description="System time observation",
            tags=["time", "temporal", "observation"],
            confidence=1.0,
            created_at=ts,
            last_updated=ts,
        )
        
        # Create evidence
        evidence = self._evidence_bridge.from_time_source(
            ts,
            source_id=source_id,
        )
        concept.add_evidence(evidence)
        
        # Save concept
        store.save_concept(concept)
        
        # Record write
        self._record_write(event_id, "time")
        
        return {
            "skipped": False,
            "concept_id": concept.id,
            "evidence_count": len(concept.evidence),
        }
    
    def write_unsupported_outcome(
        self,
        query: str,
        reason: str,
        source_id: str = None,
    ) -> Dict[str, Any]:
        """Write unsupported/uncertainty outcome to Concept Graph.
        
        Creates:
        - Uncertainty concept
        - Evidence of unavailability
        
        Args:
            query: The unsupported query
            reason: Reason for unsupported status
            source_id: Optional event source identifier
        
        Returns:
            Write statistics
        """
        store = self._get_graph_store()
        
        # Deduplication check
        event_id = source_id or f"unsupported-{query[:50]}"
        if self._check_duplicate(event_id, "unsupported"):
            return {"skipped": True, "reason": "duplicate"}
        
        # Create uncertainty concept
        query_hash = hash(query) % 1000000
        concept = Concept(
            id=f"unsupported-{query_hash}",
            name=f"Unsupported: {query[:50]}",
            type="concept",
            description=f"Query cannot be answered without external evidence",
            tags=["uncertainty", "unsupported", "gap"],
            confidence=0.5,  # Low confidence - we can't verify
            created_at=int(time.time()),
            last_updated=int(time.time()),
        )
        
        # Create evidence
        evidence = Evidence(
            source_id=source_id or f"unsupported-{query_hash}",
            source_type="runtime",
            content=f"Query: {query}",
            confidence=0.8,
            timestamp=int(time.time()),
            category="inferred",
            traceable=True,
            reason=f"Unsupported outcome: {reason}",
            source_file="llm_runtime.py",
        )
        concept.add_evidence(evidence)
        
        # Save concept
        store.save_concept(concept)
        
        # Record write
        self._record_write(event_id, "unsupported")
        
        return {
            "skipped": False,
            "concept_id": concept.id,
            "evidence_count": len(concept.evidence),
        }
    
    def write_bounded_reflection(
        self,
        role: str,
        thought_data: Dict[str, Any],
        source_id: str = None,
    ) -> Dict[str, Any]:
        """Write bounded reflection to Concept Graph.
        
        Creates:
        - Reflection concept
        - Model-asserted evidence (bounded model reasoning)
        
        Args:
            role: The role generating the reflection
            thought_data: Inner thought data from runtime
            source_id: Optional event source identifier
        
        Returns:
            Write statistics
        """
        store = self._get_graph_store()
        
        # Deduplication check
        event_id = source_id or f"reflection-{role}-{thought_data.get('summary', '')[:50]}"
        if self._check_duplicate(event_id, "reflection"):
            return {"skipped": True, "reason": "duplicate"}
        
        # Create reflection concept
        summary_hash = hash(thought_data.get("summary", "")) % 1000000
        concept = Concept(
            id=f"reflection-{role[:3]}-{summary_hash}",
            name=f"Reflection: {role}",
            type="concept",
            description=f"Inner thought from {role} role",
            tags=["reflection", "self", "thought"],
            confidence=0.7,  # Model assertion, not verified
            created_at=int(time.time()),
            last_updated=int(time.time()),
        )
        
        # Create model-asserted evidence
        evidence = Evidence(
            source_id=source_id or f"reflection-{role[:3]}-{summary_hash}",
            source_type="model_reasoning",
            content=json.dumps(thought_data)[:500],
            confidence=thought_data.get("confidence", 0.7),
            timestamp=int(time.time()),
            category="model-asserted",
            traceable=True,
            reason=f"Inner thought from {role} role",
            source_file="llm_runtime.py",
        )
        concept.add_evidence(evidence)
        
        # Save concept
        store.save_concept(concept)
        
        # Record write
        self._record_write(event_id, "reflection")
        
        return {
            "skipped": False,
            "concept_id": concept.id,
            "evidence_count": len(concept.evidence),
        }


def write_weather_result(
    location: str,
    weather_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Convenience function: Write weather result."""
    bridge = RuntimeWriteBridge()
    return bridge.write_weather_result(location, weather_data)


def write_time_result(
    timestamp: int = None,
) -> Dict[str, Any]:
    """Convenience function: Write time result."""
    bridge = RuntimeWriteBridge()
    return bridge.write_time_result(timestamp)


def write_unsupported_outcome(
    query: str,
    reason: str,
) -> Dict[str, Any]:
    """Convenience function: Write unsupported outcome."""
    bridge = RuntimeWriteBridge()
    return bridge.write_unsupported_outcome(query, reason)


def write_bounded_reflection(
    role: str,
    thought_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Convenience function: Write bounded reflection."""
    bridge = RuntimeWriteBridge()
    return bridge.write_bounded_reflection(role, thought_data)
