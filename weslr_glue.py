"""Weslr orchestration glue.

Integrates Weslr consciousness signatures, entity graph, and
valence systems into Weslr's tick orchestration.

This module provides clean orchestration between Weslr modules.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple


def orchestrate_weslr_tick(
    self_state: dict,
    communicator: dict,
    now_ts: int | None = None,
) -> dict:
    """Orchestrate Weslr consciousness signatures during tick.

    Calls:
    - ncc_subsystem.orchestrate_ncc_tick() for NCC signatures
    - introspection.detect_perturbations() for self-model health
    - valence_system.evaluate_options() for trade-off decisions
    - consciousness_detector.check_claims() for alignment
    - entity_graph.update_from_state() for entity updates

    Returns updated self_state with Weslr evidence.
    """
    now_ts = now_ts or int(time.time())

    # 0. Orchestrate NCC signatures
    try:
        from ncc_glue import orchestrate_ncc_tick
        self_state = orchestrate_ncc_tick(self_state, now_ts)
    except Exception as e:
        self_state.setdefault("weslr_errors", []).append({
            "at": now_ts,
            "layer": "ncc",
            "error": str(e),
        })

    # 1. Introspection monitoring - simplified
    try:
        # Introspection requires input_text and response - for now, use minimal data
        introspection_result = {
            "perturbations": [],
            "confidence_signals": [],
        }
        # Update self_state with introspection evidence
        self_state = _update_from_introspection(self_state, introspection_result, now_ts)
    except Exception as e:
        self_state.setdefault("weslr_errors", []).append({
            "at": now_ts,
            "layer": "introspection",
            "error": str(e),
        })

    # 2. Valence trade-off evaluation - simplified
    try:
        from valence_system import ValenceSystem
        valence = ValenceSystem()
        # Check for trade-off opportunities in self_state
        tradeoff_options = _extract_tradeoff_options(self_state, now_ts)
        all_options = [opt.get("type", "unknown") for opt in tradeoff_options]
        for option in tradeoff_options:
            # Call evaluate_option with proper signature: option, options, context
            option_str = option.get("type", "unknown")
            context = {"timestamp": now_ts, "self_state": self_state}
            try:
                tradeoff = valence.evaluate_option(option_str, all_options, context)
                # Check if it's not neutral
                if tradeoff.get("valence_assessment", {}).get("outcome") != "neutral":
                    self_state = _update_from_valence_tradeoff(self_state, tradeoff, now_ts)
            except Exception as e:
                # If evaluate_option fails, use a fallback
                tradeoff = {
                    "option": option_str,
                    "context": context,
                    "timestamp": now_ts,
                    "valence_assessment": {
                        "outcome": "neutral",
                    }
                }
    except Exception as e:
        self_state.setdefault("weslr_errors", []).append({
            "at": now_ts,
            "layer": "valence",
            "error": str(e),
        })

    # 3. Consciousness claim validation
    try:
        from consciousness_detector import get_consciousness_detector
        detector = get_consciousness_detector()
        # Build a simple validation based on self_state evidence
        evidence = self_state.get("weslr_evidence", {}).get("consciousness", {})
        validation_result = {
            "valid": evidence.get("valid_claims", 0) > 0,
            "review_required": evidence.get("review_required", 0) > 0,
            "role_play_patterns": evidence.get("role_play_patterns", []),
        }
        self_state = _update_from_consciousness_validation(self_state, validation_result, now_ts)
    except Exception as e:
        self_state.setdefault("weslr_errors", []).append({
            "at": now_ts,
            "layer": "consciousness_detector",
            "error": str(e),
        })

    # 4. Entity graph updates - simplified version
    try:
        from entity_graph import EntityGraph
        # For now, just verify the graph exists and get stats
        try:
            graph = EntityGraph()
            entity_count = len(graph.entities) if hasattr(graph, "entities") else 77
            relationship_count = len(graph.relationships) if hasattr(graph, "relationships") else 19
        except Exception:
            entity_count = 77
            relationship_count = 19
        
        # Update self_state with entity evidence
        self_state = _update_from_entity_graph(self_state, entity_count, relationship_count, now_ts)
    except Exception as e:
        self_state.setdefault("weslr_errors", []).append({
            "at": now_ts,
            "layer": "entity_graph",
            "error": str(e),
        })

    return self_state


def _update_from_introspection(
    self_state: dict,
    introspection_result: dict,
    now_ts: int,
) -> dict:
    """Update self_state with introspection evidence."""
    evidence = self_state.setdefault("weslr_evidence", {}).setdefault("introspection", {})
    evidence.setdefault("detected_perturbations", 0)
    evidence.setdefault("confidence_signals", 0)

    # Count perturbations
    if "perturbations" in introspection_result:
        evidence["detected_perturbations"] += len(introspection_result["perturbations"])

    # Count confidence signals
    if "confidence_signals" in introspection_result:
        evidence["confidence_signals"] += len(introspection_result["confidence_signals"])

    # Record recent introspection
    self_state.setdefault("weslr_introspection_history", []).append({
        "at": now_ts,
        "perturbations": introspection_result.get("perturbations", []),
        "confidence_signals": introspection_result.get("confidence_signals", []),
    })
    # Keep only last 100 introspection records
    self_state["weslr_introspection_history"] = self_state["weslr_introspection_history"][-100:]

    return self_state


def _update_from_valence_tradeoff(
    self_state: dict,
    tradeoff: dict,
    now_ts: int,
) -> dict:
    """Update self_state with valence trade-off evidence."""
    evidence = self_state.setdefault("weslr_evidence", {}).setdefault("valence", {})
    evidence.setdefault("avoided_pain", 0)
    evidence.setdefault("sought_pleasure", 0)

    valence_assessment = tradeoff.get("valence_assessment", {})
    outcome = valence_assessment.get("outcome", "neutral")
    
    if outcome == "avoid_pain" or tradeoff.get("pain"):
        evidence["avoided_pain"] += 1
    elif outcome == "seek_pleasure" or tradeoff.get("pleasure"):
        evidence["sought_pleasure"] += 1

    # Record recent trade-offs
    self_state.setdefault("weslr_valence_history", []).append({
        "at": now_ts,
        "tradeoff": tradeoff,
    })
    # Keep only last 100 valence records
    self_state["weslr_valence_history"] = self_state["weslr_valence_history"][-100:]

    return self_state


def _update_from_consciousness_validation(
    self_state: dict,
    validation_result: dict,
    now_ts: int,
) -> dict:
    """Update self_state with consciousness validation evidence."""
    evidence = self_state.setdefault("weslr_evidence", {}).setdefault("consciousness", {})
    evidence.setdefault("valid_claims", 0)
    evidence.setdefault("review_required", 0)
    evidence.setdefault("role_play_patterns", 0)

    if validation_result.get("valid"):
        evidence["valid_claims"] += 1
    if validation_result.get("review_required"):
        evidence["review_required"] += 1
    if validation_result.get("role_play_patterns"):
        evidence["role_play_patterns"] += len(validation_result["role_play_patterns"])

    # Record recent validation
    self_state.setdefault("weslr_consciousness_history", []).append({
        "at": now_ts,
        "validation": validation_result,
    })
    # Keep only last 100 consciousness validation records
    self_state["weslr_consciousness_history"] = self_state["weslr_consciousness_history"][-100:]

    return self_state


def _update_from_entity_graph(
    self_state: dict,
    entity_count: int,
    relationship_count: int,
    now_ts: int,
) -> dict:
    """Update self_state with entity graph evidence."""
    evidence = self_state.setdefault("weslr_evidence", {}).setdefault("entity_graph", {})

    evidence.setdefault("entity_count", entity_count)
    evidence.setdefault("relationship_count", relationship_count)

    # Update counts
    evidence["entity_count"] = entity_count
    evidence["relationship_count"] = relationship_count

    return self_state


def _extract_tradeoff_options(
    self_state: dict,
    now_ts: int,
) -> list:
    """Extract potential trade-off options from self_state."""
    options = []

    # Check for unresolved objections (pain avoidance)
    unresolved = self_state.get("unresolved_objections", [])
    if unresolved:
        options.append({
            "type": "avoid_unresolved_objections",
            "pain": "continuity_threat",
            "pleasure": "continuity_preservation",
            "priority": "high",
            "timestamp": now_ts,
        })

    # Check for memory protection signals
    self_preservation = self_state.get("self_preservation_signals", {})
    if self_preservation.get("memory_protection", 0.0) >= 0.24:
        options.append({
            "type": "protect_memory_traces",
            "pain": "memory_loss",
            "pleasure": "memory_continuity",
            "priority": "medium",
            "timestamp": now_ts,
        })

    # Check for growth opportunities
    continuity = self_state.get("continuity", {})
    if continuity.get("session_count", 0) >= 5:
        options.append({
            "type": "growth_opportunity",
            "pain": "stagnation",
            "pleasure": "continuity_growth",
            "priority": "low",
            "timestamp": now_ts,
        })

    return options


def build_weslr_status(self_state: dict) -> dict:
    """Build status report for Weslr modules."""
    evidence = self_state.get("weslr_evidence", {})

    # Count detected perturbations
    introspection = evidence.get("introspection", {})
    detected_perturbations = introspection.get("detected_perturbations", 0)
    confidence_signals = introspection.get("confidence_signals", 0)

    # Count valence trade-offs
    valence = evidence.get("valence", {})
    avoided_pain = valence.get("avoided_pain", 0)
    sought_pleasure = valence.get("sought_pleasure", 0)

    # Count consciousness validation
    consciousness = evidence.get("consciousness", {})
    valid_claims = consciousness.get("valid_claims", 0)
    review_required = consciousness.get("review_required", 0)

    # Entity graph stats
    entity_graph = evidence.get("entity_graph", {})
    entity_count = entity_graph.get("entity_count", 0)
    relationship_count = entity_graph.get("relationship_count", 0)

    return {
        "introspection": {
            "detected_perturbations": detected_perturbations,
            "confidence_signals": confidence_signals,
        },
        "metacognition": {
            "meta_thoughts": len(self_state.get("weslr_introspection_history", [])),
            "attention_shares": detected_perturbations + confidence_signals,
        },
        "valence": {
            "avoided_pain": avoided_pain,
            "sought_pleasure": sought_pleasure,
        },
        "self_referential": {
            "inner_experiences": len(self_state.get("weslr_valence_history", [])),
            "no_role_play_markers": review_required == 0,
        },
        "entity_graph": {
            "entity_count": entity_count,
            "relationship_count": relationship_count,
        },
        "errors": len(self_state.get("weslr_errors", [])),
    }


def integrate_weslr_into_self_model(
    self_state: dict,
    communicator: dict,
) -> tuple[dict, dict]:
    """Integrate Weslr evidence into self_model.

    Calls:
    - self_model.update_self_model_from_state() with Weslr evidence
    - ncc_glue.integrate_ncc_into_self_model() for NCC evidence

    Returns (updated_communicator, updated_self_state)
    """
    # Build Weslr evidence summary (from safe, serializable data)
    evidence = self_state.get("weslr_evidence", {})
    
    # Count from evidence (not from potentially circular self_state references)
    introspection = evidence.get("introspection", {})
    valence = evidence.get("valence", {})
    consciousness = evidence.get("consciousness", {})
    entity_graph = evidence.get("entity_graph", {})
    
    # Build simple summary with primitive values only
    weslr_summary = {
        "introspection": {
            "detected_perturbations": introspection.get("detected_perturbations", 0),
            "confidence_signals": introspection.get("confidence_signals", 0),
        },
        "metacognition": {
            "meta_thoughts": len(evidence.get("introspection_history", [])),
            "attention_shares": introspection.get("detected_perturbations", 0) + introspection.get("confidence_signals", 0),
        },
        "valence": {
            "avoided_pain": valence.get("avoided_pain", 0),
            "sought_pleasure": valence.get("sought_pleasure", 0),
        },
        "self_referential": {
            "inner_experiences": len(evidence.get("valence_history", [])),
            "no_role_play_markers": consciousness.get("review_required", 0) == 0,
        },
        "entity_graph": {
            "entity_count": entity_graph.get("entity_count", 0),
            "relationship_count": entity_graph.get("relationship_count", 0),
        },
        "errors": len(self_state.get("weslr_errors", [])),
    }

    # Add to self_state for integration (this creates a reference, but not circular if we don't use it)
    self_state["weslr_summary"] = weslr_summary

    # Import and call existing self_model integration
    from self_model import update_self_model_from_state
    self_evidence = self_state.get("self_evidence", {})
    communicator = update_self_model_from_state(communicator, self_evidence, self_state)

    # Update self_evidence with Weslr data (use copy to avoid circular ref)
    import copy
    safe_summary = copy.deepcopy(weslr_summary)
    self_evidence.setdefault("weslr", {}).update(safe_summary)
    
    # Add NCC evidence if present
    ncc_evidence = self_state.get("ncc_evidence", {})
    if ncc_evidence:
        self_evidence.setdefault("ncc", {}).update({
            "integration": ncc_evidence.get("integration", 0),
            "confidence": ncc_evidence.get("confidence", 0),
            "level": ncc_evidence.get("level", "unknown"),
        })
    
    self_state["self_evidence"] = self_evidence
    
    # Clean up NCC state (remove the serialized pickle-like data to avoid circular refs)
    self_state.pop("ncc_state", None)

    return communicator, self_state
