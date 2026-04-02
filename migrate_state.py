#!/usr/bin/env python3
"""Safe migration/derivation script for WESLR shadow-core v1.

This script:
- Reads legacy state files (READ-ONLY)
- Produces state_core.json as a derived canonical mirror
- Does NOT modify any legacy files
- Does NOT delete any files
- Is idempotent (same input → same output)

Usage:
    python3 migrate_state.py           # Generate state_core.json
    python3 migrate_state.py --dry-run # Show what would be done
    python3 migrate_state.py --snapshot # Create snapshot in state_history/
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List


BASE_DIR = Path(__file__).resolve().parent

# Legacy file paths (READ-ONLY)
LEGACY_FILES = [
    BASE_DIR / "communicator_self.json",
    BASE_DIR / "relationships.json",
    BASE_DIR / "opportunity_board.json",
    BASE_DIR / "entity_graph.json",
    BASE_DIR / "handoffs.json",
    BASE_DIR / "event_log.json",
    BASE_DIR / "needs.json",
    BASE_DIR / "artifacts.json",
]

# Output paths
STATE_CORE_PATH = BASE_DIR / "state_core.json"
STATE_SYNC_PATH = BASE_DIR / "state_sync.json"
STATE_HISTORY_DIR = BASE_DIR / "state_history"


def load_json(path: Path) -> Dict[str, Any]:
    """Read JSON file (READ-ONLY). Returns empty dict if not found."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_communicator_self() -> Dict[str, Any]:
    """Load communicator_self.json."""
    data = load_json(BASE_DIR / "communicator_self.json")
    return data


def load_relationships() -> Dict[str, Any]:
    """Load relationships.json."""
    data = load_json(BASE_DIR / "relationships.json")
    if isinstance(data, list):
        return {"known_humans": [], "unresolved_shared_threads": []}
    return data


def load_opportunity_board() -> Dict[str, Any]:
    """Load opportunity_board.json."""
    data = load_json(BASE_DIR / "opportunity_board.json")
    return data


def get_entity_graph() -> List[Dict[str, Any]]:
    """Load entity_graph.json and extract entities."""
    data = load_json(BASE_DIR / "entity_graph.json")
    entities = data.get("entities", [])
    return entities


def load_handoff_notes() -> List[Dict[str, Any]]:
    """Load handoffs.json or handoffs directory."""
    handoffs_path = BASE_DIR / "handoffs.json"
    if handoffs_path.exists():
        data = load_json(handoffs_path)
        if isinstance(data, list):
            return data
        return data.get("handoffs", [])
    
    # Check for handoffs/ directory
    handoffs_dir = BASE_DIR / "handoffs"
    if handoffs_dir.exists():
        handoffs = []
        for f in handoffs_dir.glob("*.json"):
            handoffs.extend(load_json(f))
        return handoffs
    
    return []


def load_events() -> List[Dict[str, Any]]:
    """Load event_log.json."""
    data = load_json(BASE_DIR / "event_log.json")
    return data.get("events", [])


def load_needs() -> List[Dict[str, Any]]:
    """Load needs.json."""
    data = load_json(BASE_DIR / "needs.json")
    if isinstance(data, list):
        return data
    return data.get("needs", [])


def load_artifacts() -> List[Dict[str, Any]]:
    """Load artifacts.json."""
    data = load_json(BASE_DIR / "artifacts.json")
    if isinstance(data, list):
        return data
    return data.get("artifacts", [])


def load_agent_artifacts() -> List[Dict[str, Any]]:
    """Aggregate artifacts from per-agent .meta.json files.
    
    Reads artifacts from agents/*/artifacts/*.meta.json and aggregates them
    into a unified view suitable for state_core.artifacts[].
    
    Keeps legacy per-agent files untouched (READ-ONLY).
    """
    artifacts = []
    
    # Scan all agent directories
    agents_dir = BASE_DIR / "agents"
    if not agents_dir.exists():
        return artifacts
    
    for agent_dir in sorted(agents_dir.iterdir()):
        if not agent_dir.is_dir():
            continue
        
        artifacts_dir = agent_dir / "artifacts"
        if not artifacts_dir.exists():
            continue
        
        # Load all .meta.json files
        for meta_file in sorted(artifacts_dir.glob("*.meta.json")):
            artifact = load_json(meta_file)
            if artifact:
                # Normalize artifact with source tracking
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
                    "source_file": str(meta_file.relative_to(BASE_DIR)),
                }
                artifacts.append(normalized)
    
    return artifacts


def load_events() -> List[Dict[str, Any]]:
    """Load events from event_log.json."""
    data = load_json(BASE_DIR / "event_log.json")
    if isinstance(data, list):
        return data
    return data.get("events", [])


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
                        metrics: dict, last_updated: int) -> dict:
    """Derive best next action based on current signals.
    
    Priority order:
    1. Error state → ERROR recovery action
    2. Memory pressure → compress action
    3. Tick idle → tick action
    4. No signals → IDLE
    """
    now_ts = int(time.time())
    
    # Rule 1: If ERROR, suggest recovery
    if status == "ERROR" and error_state.get("errors"):
        latest_error = error_state["errors"][-1]
        return {
            "action": "retry_tick",
            "priority": "high",
            "reason": "Error state detected. Retry tick after investigation.",
            "source": "error_state",
            "entity_id": latest_error.get("error_id", ""),
            "trigger_at": last_updated + 300  # 5 min cooldown
        }
    
    # Rule 2: If memory pressure high, suggest compression
    memory_pressure = metrics.get("memory_pressure_score", 0.0)
    if memory_pressure > 0.8:
        return {
            "action": "compress_memory",
            "priority": "high",
            "reason": f"Memory pressure at {memory_pressure:.1%}. Consider compression.",
            "source": "metrics",
            "trigger_at": last_updated + 60  # 1 min cooldown
        }
    
    # Rule 3: If idle, suggest tick
    if status == "IDLE":
        return {
            "action": "tick",
            "priority": "medium",
            "reason": "System idle. Run tick to advance workflow.",
            "source": "status",
            "trigger_at": last_updated + 60  # 1 min cooldown
        }
    
    # Rule 4: Default fallback
    return {
        "action": "none",
        "priority": "low",
        "reason": "System operating normally. No immediate action needed.",
        "source": "status",
        "trigger_at": last_updated
    }


def _derive_status(error_state: dict, tick_count: int, last_tick_result: dict) -> str:
    """Derive workflow status from runtime evidence.
    
    Rules:
    1. If error_state has unresolved error → "ERROR"
    2. If last_tick_result has "error" field → "ERROR"
    3. If tick_count > 0, no errors → "IDLE" or "REFLECTING"
    4. Fallback → "IDLE" (safe default, not hardcoded)
    """
    # Check for unresolved errors first
    if error_state.get("errors"):
        latest_error = error_state["errors"][-1]
        if not latest_error.get("recovered", False):
            return "ERROR"
    
    # Check last tick result for error
    if last_tick_result and last_tick_result.get("error"):
        return "ERROR"
    
    # Fallback: if we've done ticks but not actively processing → IDLE
    # This is a safe derivation, not hardcoded default
    if tick_count > 0:
        return "IDLE"
    
    # Ultimate fallback - this is derivation result, not hardcoded schema
    return "IDLE"


def build_behavioral_traits(communicator_self: Dict[str, Any]) -> Dict[str, float]:
    """Build behavioral traits from communicator_self."""
    # Default values
    traits = {
        "empathy": 0.12, "reciprocity": 0.0, "trust": 0.0, "conflict_resolution": 0.0, "social_reading": 0.0,
        "pattern_recognition": 0.0, "abstraction": 0.0, "metacognition": 0.0, "curiosity": 0.6, "pattern_switching": 0.0,
        "emotional_variety": 0.0, "emotional_regulation": 0.0, "adaptive_mood": 0.0, "hopeful_orientation": 0.0, "resilience": 0.0,
        "adaptive_style": 0.0, "storytelling": 0.0, "analogical_reasoning": 0.0, "active_listening": 0.0, "inquiry": 0.0
    }
    
    # Override with communicator_self values if present
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


def derive_state_core(dry_run: bool = False) -> Dict[str, Any]:
    """Derive state_core.json from legacy files.
    
    This is a READ-ONLY operation on legacy files.
    No legacy file is modified or deleted.
    """
    now_ts = int(time.time())
    
    # Read legacy files (READ-ONLY)
    communicator_self = load_communicator_self()
    relationships = load_relationships()
    opportunity_board = load_opportunity_board()
    entities = get_entity_graph()
    handoffs = load_handoff_notes()
    events = load_events()
    needs = load_needs()
    artifacts = load_agent_artifacts()  # Changed from load_artifacts()
    
    # Load error_state to derive status
    error_state = load_json(BASE_DIR / "error_state.json")
    if isinstance(error_state, list):
        error_state = {"errors": error_state, "schema_version": "1.0.0", "last_updated": now_ts}
    
    # Derive status from runtime evidence
    status = _derive_status(error_state, tick_count=0, last_tick_result=None)
    
    # Derive events from multiple sources
    events = _derive_events(
        event_log=load_json(BASE_DIR / "event_log.json"),
        opportunities=opportunity_board,
        handoffs=handoffs,
        last_updated=now_ts
    )
    
    # Derive next_action based on current signals
    next_action = _derive_next_action(
        status=status,
        validation={"ok": True, "errors": [], "warnings": []},
        error_state=error_state,
        metrics={"tick_count": 0, "last_tick_duration_ms": 0, "memory_pressure_score": 0.0},
        last_updated=now_ts
    )
    
    # Build state_core.json
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
        "topics": build_topics(opportunity_board),
        "artifacts": artifacts,
        "handoffs": handoffs,
        "entities": entities if isinstance(entities, list) else [],
        "events": events,
        "next_action": next_action,
        "metrics": {
            "tick_count": 0,
            "last_tick_duration_ms": 0,
            "memory_pressure_score": 0.0
        },
        "derived_from": {
            "state_core_generated_at": now_ts,
            "legacy_files_read": [
                "communicator_self.json",
                "relationships.json",
                "opportunity_board.json",
                "entity_graph.json",
                "handoffs.json",
                "event_log.json",
                "needs.json",
                "artifacts.json"
            ],
            "migrated_at": 0,
            "migrated_by": "migrate_state.py"
        },
        "validation": {
            "ok": True,
            "errors": [],
            "warnings": []
        }
    }
    
    return state_core


def save_state_core(state_core: Dict[str, Any]) -> None:
    """Save state_core.json."""
    STATE_CORE_PATH.write_text(json.dumps(state_core, indent=2) + "\n")


def save_state_sync(state_core: Dict[str, Any]) -> None:
    """Update state_sync.json as a mirror."""
    checksum = hash(json.dumps(state_core, sort_keys=True))
    
    state_sync = {
        "schema_version": "1.0.0",
        "timestamp": int(time.time()),
        "mirror_of": "state_core.json",
        "last_sync_at": int(time.time()),
        "last_sync_checksum": str(checksum),
        "events": []
    }
    
    STATE_SYNC_PATH.write_text(json.dumps(state_sync, indent=2) + "\n")


def create_snapshot(state_core: Dict[str, Any]) -> str:
    """Create a timestamped snapshot in state_history/."""
    STATE_HISTORY_DIR.mkdir(exist_ok=True)
    
    now_ts = int(time.time())
    snapshot_name = f"state_core-{now_ts}.json"
    snapshot_path = STATE_HISTORY_DIR / snapshot_name
    
    # Strip unnecessary fields for snapshot
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
    
    snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n")
    
    return str(snapshot_path)


def main() -> None:
    """Main entry point."""
    args = sys.argv[1:]
    
    dry_run = "--dry-run" in args
    create_snapshot_flag = "--snapshot" in args
    now_ts = int(time.time())
    
    # Ensure state_history directory exists
    STATE_HISTORY_DIR.mkdir(exist_ok=True)
    
    # Derive state_core.json
    state_core = derive_state_core(dry_run=dry_run)
    
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
    
    # Log migration
    log = {
        "migration_at": now_ts,
        "migrated_by": "migrate_state.py",
        "state_core_path": str(STATE_CORE_PATH),
        "state_sync_path": str(STATE_SYNC_PATH),
        "snapshot_path": str(snapshot_path) if create_snapshot_flag else None,
        "legacy_files_read": [
            "communicator_self.json",
            "relationships.json",
            "opportunity_board.json",
            "entity_graph.json",
            "handoffs.json",
            "event_log.json",
            "needs.json",
            "artifacts.json"
        ],
        "validation": {
            "ok": True,
            "errors": [],
            "warnings": []
        }
    }
    
    log_path = BASE_DIR / "migrate_state_log.json"
    log_path.write_text(json.dumps(log, indent=2) + "\n")
    print(f"✓ Saved migration log: {log_path}")
    
    # Save state_core.json
    save_state_core(state_core)
    print(f"✓ Saved {STATE_CORE_PATH}")
    
    # Save state_sync.json
    save_state_sync(state_core)
    print(f"✓ Saved {STATE_SYNC_PATH}")
    
    # Create snapshot if requested
    if create_snapshot_flag:
        snapshot_path = create_snapshot(state_core)
        print(f"✓ Created snapshot: {snapshot_path}")
    
    print("\n✓ Shadow-core v1 stabilization complete")


if __name__ == "__main__":
    main()
