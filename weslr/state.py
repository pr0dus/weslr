"""Weslr Platform: Canonical State Derivation (v1)

Weslr-native state derivation, portable across runtimes.
Reads legacy files (READ-ONLY) and produces canonical state_core.json.

No runtime-specific dependencies.
No user-facing behavior.
Base-dir aware for multi-runtime support.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import contracts

# Default paths (override via BASE_DIR parameter in functions)
DEFAULT_BASE_DIR = "/data/data/com.termux/files/home/.openclaw/workspace"

# Legacy file paths (READ-ONLY)
LEGACY_FILES = [
    "communicator_self.json",
    "relationships.json",
    "opportunity_board.json",
    "entity_graph.json",
    "handoffs.json",
    "event_log.json",
    "needs.json",
    "artifacts.json",
]

# Output paths
STATE_CORE_PATH = "state_core.json"
STATE_SYNC_PATH = "state_sync.json"
STATE_HISTORY_DIR = "state_history"

# Continuity snapshot directories (WESLR anchored)
CONTINUITY_DIR = "continuity"
SNAPSHOT_DIR = os.path.join(CONTINUITY_DIR, "snapshots")


def get_paths(base_dir: str = None) -> tuple[str, str, str, str, str]:
    """Get state derivation paths, configurable via base_dir."""
    base_dir = base_dir or DEFAULT_BASE_DIR
    state_history_dir = os.path.join(base_dir, STATE_HISTORY_DIR)
    continuity_dir = os.path.join(base_dir, CONTINUITY_DIR)
    snapshot_dir = os.path.join(continuity_dir, SNAPSHOT_DIR)
    state_core_path = os.path.join(base_dir, STATE_CORE_PATH)
    state_sync_path = os.path.join(base_dir, STATE_SYNC_PATH)
    return base_dir, state_history_dir, continuity_dir, snapshot_dir, state_core_path, state_sync_path


def load_json(path: str, base_dir: str = None) -> Dict[str, Any]:
    """Read JSON file (READ-ONLY). Returns empty dict if not found."""
    full_path = os.path.join(base_dir or DEFAULT_BASE_DIR, path)
    if not os.path.exists(full_path):
        return {}
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_communicator_self(base_dir: str = None) -> Dict[str, Any]:
    """Load communicator_self.json."""
    return load_json("communicator_self.json", base_dir)


def load_relationships(base_dir: str = None) -> Dict[str, Any]:
    """Load relationships.json."""
    data = load_json("relationships.json", base_dir)
    if isinstance(data, list):
        return {"known_humans": [], "unresolved_shared_threads": []}
    return data


def load_opportunity_board(base_dir: str = None) -> Dict[str, Any]:
    """Load opportunity_board.json."""
    return load_json("opportunity_board.json", base_dir)


def get_entity_graph(base_dir: str = None) -> List[Dict[str, Any]]:
    """Load entity_graph.json and extract entities."""
    data = load_json("entity_graph.json", base_dir)
    entities = data.get("entities", [])
    if isinstance(entities, dict):
        entities = list(entities.values())
    elif not isinstance(entities, list):
        entities = []
    return entities


def load_agent_entities(base_dir: str = None) -> List[Dict[str, Any]]:
    """Load entities from entity_graph.json and normalize to state_core format.
    
    Reads from entity_graph.json and converts to simplified entity objects
    suitable for state_core.entities[].
    
    Keeps legacy entity files untouched (READ-ONLY).
    """
    entities = []
    data = load_json("entity_graph.json", base_dir)
    raw_entities = data.get("entities", {})
    
    if isinstance(raw_entities, dict):
        raw_entities = list(raw_entities.values())
    
    for raw_entity in raw_entities:
        if not isinstance(raw_entity, dict):
            continue
        
        entity = {
            "id": raw_entity.get("id", ""),
            "name": raw_entity.get("name", ""),
            "type": raw_entity.get("type", "other"),
            "confidence": float(raw_entity.get("confidence", 0.0)),
            "status": "authoritative" if not raw_entity.get("is_ghost", True) else "ghost",
            "is_ghost": raw_entity.get("is_ghost", True),
            "created_at": raw_entity.get("created_at", 0),
            "last_seen": raw_entity.get("last_seen", 0),
            "relationship_count": len(raw_entity.get("relationships", [])),
            "evidence_count": len(raw_entity.get("evidence", [])),
            "metadata": raw_entity.get("metadata", {}),
        }
        entities.append(entity)
    
    return entities


def load_agent_handoffs(base_dir: str = None) -> List[Dict[str, Any]]:
    """Load handoffs from handoffs.json and normalize to state_core format.
    
    Reads from handoffs.json if it exists, otherwise returns empty list.
    
    Keeps legacy handoff files untouched (READ-ONLY).
    """
    handoffs = []
    handoffs_path = os.path.join(base_dir or DEFAULT_BASE_DIR, "handoffs.json")
    if not os.path.exists(handoffs_path):
        return handoffs
    
    data = load_json("handoffs.json", base_dir)
    if isinstance(data, list):
        handoffs = data
    elif isinstance(data, dict):
        handoffs = data.get("handoffs", [])
    
    normalized = []
    for handoff in handoffs:
        if not isinstance(handoff, dict):
            continue
        normalized.append({
            "id": handoff.get("id", ""),
            "from_agent": handoff.get("from_agent", "unknown"),
            "to_agent": handoff.get("to_agent", "unknown"),
            "topic": handoff.get("topic", "unspecified"),
            "handoff_type": handoff.get("handoff_type", "task"),
            "priority": float(handoff.get("priority", 0.5)),
            "status": handoff.get("status", "pending"),
            "timestamp": handoff.get("timestamp", 0),
            "timeout_at": handoff.get("timeout_at", 0),
            "context": handoff.get("context", {}),
        })
    return normalized


def load_handoff_notes(base_dir: str = None) -> List[Dict[str, Any]]:
    """Load handoffs.json or handoffs directory."""
    handoffs_path = os.path.join(base_dir or DEFAULT_BASE_DIR, "handoffs.json")
    if os.path.exists(handoffs_path):
        data = load_json("handoffs.json", base_dir)
        if isinstance(data, list):
            return data
        return data.get("handoffs", [])
    
    # Check for handoffs/ directory
    handoffs_dir = os.path.join(base_dir or DEFAULT_BASE_DIR, "handoffs")
    if os.path.exists(handoffs_dir):
        handoffs = []
        for f in Path(handoffs_dir).glob("*.json"):
            handoffs.extend(load_json(str(f), base_dir))
        return handoffs
    
    return []


def load_events(base_dir: str = None) -> List[Dict[str, Any]]:
    """Load event_log.json."""
    data = load_json("event_log.json", base_dir)
    return data.get("events", [])


def load_needs(base_dir: str = None) -> List[Dict[str, Any]]:
    """Load needs.json."""
    data = load_json("needs.json", base_dir)
    if isinstance(data, list):
        return data
    return data.get("needs", [])


def load_artifacts(base_dir: str = None) -> List[Dict[str, Any]]:
    """Load artifacts.json."""
    data = load_json("artifacts.json", base_dir)
    if isinstance(data, list):
        return data
    return data.get("artifacts", [])


def load_agent_artifacts(base_dir: str = None) -> List[Dict[str, Any]]:
    """Aggregate artifacts from per-agent .meta.json files.
    
    Reads artifacts from agents/*/artifacts/*.meta.json and aggregates them
    into a unified view suitable for state_core.artifacts[].
    
    Keeps legacy per-agent files untouched (READ-ONLY).
    """
    artifacts = []
    agents_dir = os.path.join(base_dir or DEFAULT_BASE_DIR, "agents")
    if not os.path.exists(agents_dir):
        return artifacts
    
    for agent_dir in sorted(Path(agents_dir).iterdir()):
        if not agent_dir.is_dir():
            continue
        
        artifacts_dir = agent_dir / "artifacts"
        if not artifacts_dir.exists():
            continue
        
        for meta_file in sorted(artifacts_dir.glob("*.meta.json")):
            artifact = load_json(str(meta_file), base_dir)
            if artifact:
                normalized = {
                    "id": artifact.get("id", meta_file.stem),
                    "agent_name": artifact.get("agent_name", "unknown"),
                    "title": artifact.get("title", meta_file.stem.replace("_", " ").title()),
                    "artifact_type": artifact.get("artifact_type", "unknown"),
                    "category": artifact.get("category", "uncategorized"),
                    "status": artifact.get("status", "prototype"),
                    "lifecycle_stage": artifact.get("lifecycle_stage", "prototype"),
                    "review_status": artifact.get("review_status", "unreviewed"),
                    "clarity_score": artifact.get("clarity_score", 0.0),
                    "reusability_score": artifact.get("reusability_score", 0.0),
                    "novelty_score": artifact.get("novelty_score", 0.0),
                    "sellability_score": artifact.get("sellability_score", 0.0),
                    "human_proposed_score": artifact.get("human_proposed_score", 0.0),
                    "commercial_readiness_score": artifact.get("commercial_readiness_score", 0.0),
                    "price_band_guess": artifact.get("price_band_guess", "needs packaging"),
                    "delivery_mode": artifact.get("delivery_mode", "internal_component"),
                    "target_user": artifact.get("target_user", "technical builders"),
                    "source_file": str(meta_file.relative_to(Path(base_dir or DEFAULT_BASE_DIR))),
                }
                artifacts.append(normalized)
    
    return artifacts


def _derive_events(event_log: dict, opportunities: dict, handoffs: list, last_updated: int) -> List[Dict[str, Any]]:
    """Derive normalized events from current history sources.
    
    Sources:
    - event_log.json → event_log.events[]
    - opportunity_board.json → opportunity lifecycle events
    - handoffs.json → handoff lifecycle events
    
    Returns unified event list suitable for operator display.
    """
    events = []
    
    # 1. Events from event_log.json
    for event in event_log.get("events", []):
        events.append({
            "id": event.get("id", f"ev-{int(time.time() * 1000)}"),
            "timestamp": event.get("timestamp", last_updated),
            "type": event.get("kind", "unknown"),
            "agent": event.get("agent_name", ""),
            "action": event.get("action", ""),
            "status": event.get("status", "unknown"),
            "summary": event.get("summary", ""),
            "source": "event_log"
        })
    
    # 2. Events from opportunity board
    if opportunities:
        for theme_name, theme_data in opportunities.get("themes", {}).items():
            events.append({
                "id": f"opportunity-{theme_name}",
                "timestamp": theme_data.get("updated_at", last_updated),
                "type": "opportunity_update",
                "agent": "",
                "action": "lifecycle_change",
                "status": theme_data.get("lifecycle", "pending"),
                "summary": f"Opportunity '{theme_name}' updated: {theme_data.get('lifecycle', 'pending')}",
                "source": "opportunity_board"
            })
    
    # 3. Events from handoffs
    for handoff in handoffs:
        events.append({
            "id": handoff.get("id", f"handoff-{handoff.get('timestamp', 0)}"),
            "timestamp": handoff.get("timestamp", last_updated),
            "type": "handoff_update",
            "agent": handoff.get("to_agent", ""),
            "action": "status_change",
            "status": handoff.get("status", "pending"),
            "summary": f"Handoff from {handoff.get('from_agent', '')} to {handoff.get('to_agent', '')}: {handoff.get('status', 'pending')}",
            "source": "handoffs"
        })
    
    # Sort by timestamp descending (newest first)
    events.sort(key=lambda e: e["timestamp"], reverse=True)
    
    # Limit to last 50 events for display
    return events[:50]


def _derive_next_action(status: str, validation: dict, error_state: dict, 
                        metrics: dict, last_updated: int,
                        artifacts: List[Dict] = None,
                        handoffs: List[Dict] = None,
                        topics: List[Dict] = None,
                        entities: List[Dict] = None) -> dict:
    """Derive best next action based on current signals with traceability.
    
    Priority order:
    1. Error state → ERROR recovery action
    2. Pending handoffs → review handoff action
    3. High-pressure topics → investigate topic action
    4. Review-worthy artifacts → review artifact action
    5. Stale/idle system → tick action
    6. No signals → IDLE
    
    Returns next_action with traceability for operator understanding.
    """
    now_ts = int(time.time())
    
    # Collect all considered signals with scores (for traceability)
    all_signals = []
    
    # Score error state
    if error_state.get("errors"):
        latest_error = error_state["errors"][-1]
        all_signals.append({
            "type": "error",
            "action": "retry_tick",
            "score": 1.0,
            "reason": "Unresolved error detected",
            "data": {"error_id": latest_error.get("error_id", "")}
        })
    
    # Score pending handoffs
    if handoffs and len(handoffs) > 0:
        pending = [h for h in handoffs if h.get("status") in {"pending", "accepted", "active"}]
        if pending:
            all_signals.append({
                "type": "handoffs",
                "action": "review_handoffs",
                "score": 0.9,
                "reason": f"{len(pending)} pending handoff(s)",
                "data": {"pending_count": len(pending)}
            })
    
    # Score high-pressure topics
    if topics:
        high_pressure = [t for t in topics if t.get("pressure", 0) > 0.8]
        if high_pressure:
            all_signals.append({
                "type": "topics",
                "action": "investigate_topics",
                "score": 0.8,
                "reason": f"{len(high_pressure)} high-pressure topic(s)",
                "data": {"high_pressure_count": len(high_pressure), "pressure_values": [t.get("pressure", 0) for t in high_pressure[:3]]}
            })
    
    # Score review-worthy artifacts
    if artifacts:
        reviewable = [a for a in artifacts if a.get("sellability_score", 0) >= 0.2]
        if reviewable:
            all_signals.append({
                "type": "artifacts",
                "action": "review_artifacts",
                "score": 0.8,
                "reason": f"{len(reviewable)} artifact(s) ready for review",
                "data": {"reviewable_count": len(reviewable), "max_sellability": max(a.get("sellability_score", 0) for a in reviewable)}
            })
    
    # Score memory pressure
    memory_pressure = metrics.get("memory_pressure_score", 0.0)
    if memory_pressure > 0.8:
        all_signals.append({
            "type": "memory",
            "action": "compress_memory",
            "score": 0.9,
            "reason": f"Memory pressure at {memory_pressure:.1%}",
            "data": {"pressure_score": memory_pressure}
        })
    
    # Score idle status
    if status == "IDLE":
        all_signals.append({
            "type": "status",
            "action": "tick",
            "score": 0.7,
            "reason": "System idle",
            "data": {"status": "IDLE", "ticks_since_last_action": 0}
        })
    
    # Determine which signal(s) to act on
    selected_signal = None
    if all_signals:
        sorted_signals = sorted(all_signals, key=lambda s: s.get("score", 0), reverse=True)
        selected_signal = sorted_signals[0]
    
    # Build the next_action response
    result = {
        "action": "none",
        "priority": "low",
        "reason": "No signals require immediate action.",
        "source": "status",
    }
    
    result["chosen_because"] = ""
    result["signals_considered"] = all_signals
    result["signals_not_selected"] = [s for s in all_signals if s != selected_signal]
    
    if selected_signal:
        result["action"] = selected_signal["action"]
        result["priority"] = "high" if selected_signal["score"] >= 0.9 else "medium"
        result["reason"] = selected_signal["reason"]
        result["source"] = selected_signal["type"]
        result["chosen_because"] = f"Best signal: {selected_signal['type']} ({selected_signal['reason']})"
    
    return result


def _derive_status(error_state: dict, tick_count: int, last_tick_result: dict) -> str:
    """Derive workflow status from runtime evidence.
    
    Rules:
    1. If error_state has unresolved error → "ERROR"
    2. If last_tick_result has "error" field → "ERROR"
    3. If tick_count > 0, no errors → "IDLE" or "REFLECTING"
    4. Fallback → "IDLE" (safe default, not hardcoded)
    """
    if error_state.get("errors"):
        latest_error = error_state["errors"][-1]
        if not latest_error.get("recovered", False):
            return "ERROR"
    
    if last_tick_result and last_tick_result.get("error"):
        return "ERROR"
    
    if tick_count > 0:
        return "IDLE"
    
    return "IDLE"


def build_behavioral_traits(communicator_self: Dict[str, Any]) -> Dict[str, float]:
    """Build behavioral traits from communicator_self."""
    traits = {
        "empathy": 0.12, "reciprocity": 0.0, "trust": 0.0, "conflict_resolution": 0.0, "social_reading": 0.0,
        "pattern_recognition": 0.0, "abstraction": 0.0, "metacognition": 0.0, "curiosity": 0.6, "pattern_switching": 0.0,
        "emotional_variety": 0.0, "emotional_regulation": 0.0, "adaptive_mood": 0.0, "hopeful_orientation": 0.0, "resilience": 0.0,
        "adaptive_style": 0.0, "storytelling": 0.0, "analogical_reasoning": 0.0, "active_listening": 0.0, "inquiry": 0.0
    }
    
    identity_state = communicator_self.get("identity_state", {})
    if identity_state:
        core_traits = identity_state.get("behavioral_traits", {})
        traits.update(core_traits)
    
    return traits


def build_narrative_state(communicator_self: Dict[str, Any]) -> Dict[str, str]:
    """Build narrative_state from communicator_self."""
    narrative = {
        "active_thread": "",
        "last_topic": "",
        "last_research_topic": "",
        "last_research_summary": "",
        "last_research_source": "",
        "last_decision_summary": ""
    }
    
    narrative_state = communicator_self.get("narrative_state", {})
    if narrative_state:
        narrative.update(narrative_state)
    
    return narrative


def build_memory_layers(communicator_self: Dict[str, Any]) -> Dict[str, Any]:
    """Build memory_layers from communicator_self."""
    memory_layers = {
        "working": {"count": 0, "topics": []},
        "episodic": {"count": 0},
        "semantic": {"count": 0, "active_concern_topics": [], "continuity_anchors": [], "stable_topics": []},
        "archive": {"count": 0}
    }
    
    memory = communicator_self.get("memory_layers", {})
    if memory:
        working = memory.get("working", {})
        memory_layers["working"] = {
            "count": working.get("count", 0),
            "topics": working.get("topics", [])
        }
        
        episodic = memory.get("episodic", {})
        memory_layers["episodic"] = {"count": episodic.get("count", 0)}
        
        semantic = memory.get("semantic", {})
        memory_layers["semantic"] = {
            "count": semantic.get("count", 0),
            "active_concern_topics": semantic.get("active_concern_topics", []),
            "continuity_anchors": semantic.get("continuity_anchors", []),
            "stable_topics": semantic.get("stable_topics", [])
        }
        
        archive = memory.get("archive", {})
        memory_layers["archive"] = {"count": archive.get("count", 0)}
    
    return memory_layers


def build_topics(opportunity_board: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build topics from opportunity_board."""
    topics = []
    themes = opportunity_board.get("themes", {})
    
    for theme_name, theme_data in themes.items():
        topics.append({
            "id": f"topic-{theme_name}",
            "name": theme_name,
            "pressure": theme_data.get("pressure", 0.0),
            "lifecycle": theme_data.get("lifecycle", "pending"),
            "evidence": theme_data.get("evidence", 0),
            "acceptances": theme_data.get("acceptances", 0),
            "rejections": theme_data.get("rejections", 0),
            "created_at": theme_data.get("created_at", 0),
            "updated_at": theme_data.get("updated_at", 0)
        })
    
    return topics


def derive_state_core(dry_run: bool = False, base_dir: str = None) -> Dict[str, Any]:
    """Derive state_core.json from legacy files.
    
    This is a READ-ONLY operation on legacy files.
    No legacy file is modified or deleted.
    Base-dir aware for runtime-agnostic operation.
    """
    now_ts = int(time.time())
    
    # Read legacy files (READ-ONLY)
    communicator_self = load_communicator_self(base_dir)
    relationships = load_relationships(base_dir)
    opportunity_board = load_opportunity_board(base_dir)
    entities = load_agent_entities(base_dir)
    handoffs = load_agent_handoffs(base_dir)
    events = load_events(base_dir)
    artifacts = load_agent_artifacts(base_dir)
    
    # Load error_state to derive status
    error_state = load_json("error_state.json", base_dir)
    if isinstance(error_state, list):
        error_state = {"errors": error_state, "schema_version": "1.0.0", "last_updated": now_ts}
    
    # Derive status from runtime evidence
    status = _derive_status(error_state, tick_count=0, last_tick_result=None)
    
    # Derive events from multiple sources
    events = _derive_events(
        event_log=load_json("event_log.json", base_dir),
        opportunities=opportunity_board,
        handoffs=handoffs,
        last_updated=now_ts
    )
    
    # Build topics list for next_action derivation
    topics = build_topics(opportunity_board)
    
    # Derive next_action based on current signals
    next_action = _derive_next_action(
        status=status,
        validation={"ok": True, "errors": [], "warnings": []},
        error_state=error_state,
        metrics={"tick_count": 0, "last_tick_duration_ms": 0, "memory_pressure_score": 0.0},
        last_updated=now_ts,
        artifacts=artifacts,
        handoffs=handoffs,
        topics=topics,
        entities=entities if isinstance(entities, list) else []
    )
    
    # Build state_core using contract helpers for default structures
    state_core = {
        "schema_version": "1.0.0",
        "timestamp": now_ts,
        "identity_anchor": "Weslr",
        "status": status,
        "continuity": {
            "session_count": communicator_self.get("continuity", {}).get("session_count", 0),
            "last_message_at": communicator_self.get("continuity", {}).get("last_message_at", 0),
            "known_humans": relationships.get("known_humans", []),
            "unresolved_shared_threads": relationships.get("unresolved_shared_threads", [])
        },
        "behavioral_traits": build_behavioral_traits(communicator_self),
        "curiosity": communicator_self.get("dynamic_mind_state", {}).get("curiosity", 0.5),
        "uncertainty": communicator_self.get("dynamic_mind_state", {}).get("uncertainty", 0.5),
        "narrative_state": build_narrative_state(communicator_self),
        "unresolved_shared_threads": relationships.get("unresolved_shared_threads", []),
        "memory_layers": build_memory_layers(communicator_self),
        "topics": topics,
        "artifacts": artifacts,
        "handoffs": handoffs,
        "entities": entities if isinstance(entities, list) else [],
        "events": events,
        "next_action": next_action,
        "metrics": contracts.create_empty_metrics(),
        "derived_from": {
            "state_core_generated_at": now_ts,
            "legacy_files_read": LEGACY_FILES,
            "migrated_at": 0,
            "migrated_by": "weslr.state"
        },
        "validation": contracts.create_empty_validation()
    }
    
    return state_core


def save_state_core(state_core: Dict[str, Any], base_dir: str = None) -> str:
    """Save state_core.json."""
    _, _, _, _, state_core_path, _ = get_paths(base_dir)
    Path(state_core_path).write_text(json.dumps(state_core, indent=2) + "\n")
    return state_core_path


def save_state_sync(state_core: Dict[str, Any], base_dir: str = None) -> str:
    """Update state_sync.json as a mirror."""
    _, _, _, _, _, state_sync_path = get_paths(base_dir)
    checksum = hash(json.dumps(state_core, sort_keys=True))
    
    state_sync = {
        "schema_version": "1.0.0",
        "timestamp": int(time.time()),
        "mirror_of": "state_core.json",
        "last_sync_at": int(time.time()),
        "last_sync_checksum": str(checksum),
        "events": []
    }
    
    Path(state_sync_path).write_text(json.dumps(state_sync, indent=2) + "\n")
    return state_sync_path


def create_snapshot(state_core: Dict[str, Any], base_dir: str = None) -> str:
    """Create a timestamped snapshot in state_history/."""
    _, state_history_dir, _, _, _, _ = get_paths(base_dir)
    Path(state_history_dir).mkdir(parents=True, exist_ok=True)
    
    now_ts = int(time.time())
    snapshot_name = f"state_core-{now_ts}.json"
    snapshot_path = os.path.join(state_history_dir, snapshot_name)
    
    snapshot = {
        "schema_version": state_core["schema_version"],
        "timestamp": state_core["timestamp"],
        "identity_anchor": state_core["identity_anchor"],
        "status": state_core["status"],
        "continuity": state_core["continuity"],
        "behavioral_traits": state_core["behavioral_traits"],
        "curiosity": state_core["curiosity"],
        "uncertainty": state_core["uncertainty"],
        "narrative_state": state_core["narrative_state"],
        "memory_layers": state_core["memory_layers"],
        "topics": state_core["topics"],
        "artifacts": state_core["artifacts"],
        "handoffs": state_core["handoffs"],
        "entities": state_core["entities"],
        "events": state_core["events"],
        "metrics": state_core["metrics"]
    }
    
    Path(snapshot_path).write_text(json.dumps(snapshot, indent=2) + "\n")
    return snapshot_path


def write_silent_continuity_snapshot(state_core: Dict[str, Any], base_dir: str = None) -> None:
    """Write a silent continuity snapshot after state_core.json is successfully written.
    
    This function:
    - Validates critical continuity fields exist
    - Uses atomic write (temp file → rename)
    - Skips snapshot if state is invalid or incomplete
    - Does not expose behavior to users
    - Does not trigger restore
    """
    required_fields = ["identity_anchor", "continuity", "status"]
    missing = [f for f in required_fields if f not in state_core]
    if missing:
        return
    
    _, continuity_dir, snapshot_dir, _, _, _ = get_paths(base_dir)
    Path(snapshot_dir).mkdir(parents=True, exist_ok=True)
    
    snapshot = {
        "session_id": "state_change",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "identity_anchor": state_core.get("identity_anchor"),
        "status": state_core.get("status"),
        "continuity": state_core.get("continuity", {}),
        "unresolved_shared_threads": state_core.get("unresolved_shared_threads", []),
        "narrative_state": state_core.get("narrative_state", {}),
        "continuity_markers": {
            "source": "state_core_update",
            "validated": True,
            "fields": ["identity_anchor", "status", "continuity", "unresolved_shared_threads", "narrative_state"],
        },
    }
    
    temp_path = os.path.join(snapshot_dir, "temp_snapshot.json")
    final_path = os.path.join(snapshot_dir, "latest.json")
    
    try:
        Path(temp_path).write_text(json.dumps(snapshot, indent=2) + "\n")
        Path(temp_path).rename(final_path)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return


def main() -> None:
    """Main entry point for CLI usage."""
    import sys
    args = sys.argv[1:]
    
    dry_run = "--dry-run" in args
    create_snapshot_flag = "--snapshot" in args
    now_ts = int(time.time())
    
    base_dir = None
    for i, arg in enumerate(args):
        if arg == "--base-dir" and i + 1 < len(args):
            base_dir = args[i + 1]
            break
    
    # Ensure state_history directory exists
    _, state_history_dir, _, _, _, _ = get_paths(base_dir)
    Path(state_history_dir).mkdir(parents=True, exist_ok=True)
    
    # Derive state_core.json
    state_core = derive_state_core(dry_run=dry_run, base_dir=base_dir)
    
    if dry_run:
        print("=== DRY RUN ===")
        print("Would write state_core.json")
        print(f"  Identity: {state_core['identity_anchor']}")
        print(f"  Status: {state_core['status']}")
        print(f"  Topics: {len(state_core['topics'])}")
        print(f"  Entities: {len(state_core['entities'])}")
        print(f"  Artifacts: {len(state_core['artifacts'])}")
        print("No files modified (dry-run)")
        return
    
    # Log migration (before restore to track the attempt)
    log = {
        "migration_at": now_ts,
        "migrated_by": "weslr.state",
        "state_core_path": os.path.join(base_dir or DEFAULT_BASE_DIR, STATE_CORE_PATH),
        "state_sync_path": os.path.join(base_dir or DEFAULT_BASE_DIR, STATE_SYNC_PATH),
        "snapshot_path": None,
        "legacy_files_read": LEGACY_FILES,
        "validation": {
            "ok": True,
            "errors": [],
            "warnings": []
        },
        "restore_attempted": False,
        "restore_result": None,
    }
    
    # Attempt conservative partial restore if needed
    # (Delegated to continuity_orchestrator for backward compatibility)
    try:
        sys.path.insert(0, str(Path(base_dir or DEFAULT_BASE_DIR).parent))
        from continuity_orchestrator import apply_partial_restore
        restore_result = apply_partial_restore(base_dir)
        log["restore_attempted"] = True
        log["restore_result"] = {
            "status": restore_result.get("status"),
            "fields_restored": restore_result.get("fields_restored", []),
            "fields_skipped": restore_result.get("fields_skipped", []),
        }
        print(f"  Restore: {restore_result.get('status', 'error')}")
    except Exception:
        pass
    
    # Save state_core.json
    save_state_core(state_core, base_dir)
    print(f"✓ Saved state_core.json")
    
    # Save state_sync.json
    save_state_sync(state_core, base_dir)
    print(f"✓ Saved state_sync.json")
    
    # Create snapshot if requested
    if create_snapshot_flag:
        snapshot_path = create_snapshot(state_core, base_dir)
        print(f"✓ Created snapshot: {snapshot_path}")
        log["snapshot_path"] = snapshot_path
    
    # Write silent continuity snapshot
    write_silent_continuity_snapshot(state_core, base_dir)
    
    # Update log with final restore result and save
    if log["restore_result"]:
        log_path = os.path.join(base_dir or DEFAULT_BASE_DIR, "migrate_state_log.json")
        Path(log_path).write_text(json.dumps(log, indent=2) + "\n")
        print(f"✓ Saved migration log: {log_path}")
    
    # Update observability metrics
    try:
        sys.path.insert(0, str(Path(base_dir or DEFAULT_BASE_DIR).parent))
        from continuity_orchestrator import update_metrics_after_restore, update_metrics_after_snapshot
        from continuity_orchestrator import load_snapshot, get_current_snapshot_info
        if log["restore_result"]:
            update_metrics_after_restore(log["restore_result"])
        snapshot = get_current_snapshot_info(base_dir)
        if snapshot:
            markers = snapshot.get("continuity_markers", {})
            update_metrics_after_snapshot(
                confidence=markers.get("confidence", 100.0),
                debt=markers.get("debt", 0.0),
                base_dir=base_dir
            )
    except Exception:
        pass
    
    print("\n✓ Canonical state derivation complete")


if __name__ == "__main__":
    main()
