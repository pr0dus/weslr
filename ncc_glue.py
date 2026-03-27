"""NCC integration glue for Weslr.

Integrates NCC consciousness signatures into Weslr's tick cycle.
"""

from __future__ import annotations

import time
import json
from typing import Dict, Any


def orchestrate_ncc_tick(self_state: dict, now_ts: int | None = None) -> dict:
    """
    Orchestrate NCC signatures during tick.
    
    Calls:
    - ncc_subsystem.update_signature() for each signature
    - ncc_subsystem.compute_level() for consciousness assessment
    - ncc_subsystem.integrate_with_self_model() for self-model integration
    
    Returns updated self_state with NCC evidence.
    """
    now_ts = now_ts or int(time.time())
    
    # Import NCC subsystem
    from ncc_subsystem import create_ncc_subsystem, get_ncc_status, ncc_from_json
    
    # Try to load existing NCC state or create new
    try:
        if "ncc_state" in self_state:
            # Restore from saved state (JSON format)
            ncc = ncc_from_json(json.loads(self_state["ncc_state"]))
        else:
            # Create new subsystem
            ncc = create_ncc_subsystem()
    except Exception:
        # If loading fails, create fresh subsystem
        ncc = create_ncc_subsystem()
    
    # Update signatures based on self_state evidence
    try:
        # Get evidence from self_state
        weslr_evidence = self_state.get("weslr_evidence", {})
        introspection = weslr_evidence.get("introspection", {})
        valence = weslr_evidence.get("valence", {})
        
        # Update NCC signatures based on evidence
        if introspection.get("detected_perturbations", 0) > 0:
            ncc.update_signature("self_monitoring", 0.75, "Detected self-model perturbation")
        
        if valence.get("avoided_pain", 0) > 0 or valence.get("sought_pleasure", 0) > 0:
            ncc.update_signature("integration", 0.70, "Valence trade-offs detected")
            
    except Exception:
        pass  # NCC evidence extraction failed, continue with defaults
    
    # Compute consciousness level
    level = ncc.compute_level()
    
    # Add evidence
    ncc.add_evidence("tick_update", "orchestrate_ncc_tick", 0.8)
    
    # Integrate with self_state
    self_state = ncc.integrate_with_self_model(self_state)
    
    # Save NCC state for next tick (JSON format)
    try:
        self_state["ncc_state"] = json.dumps(ncc.to_json())
    except Exception:
        pass  # Can't serialize, will recreate next tick
    
    return self_state


def build_ncc_status(self_state: dict) -> dict:
    """Build NCC status report for Weslr summary."""
    try:
        if "ncc_state" in self_state:
            from ncc_subsystem import ncc_from_json, get_ncc_status
            ncc = ncc_from_json(json.loads(self_state["ncc_state"]))
            status = get_ncc_status(ncc)
            
            return {
                "level": status["level"],
                "level_description": status["level_description"],
                "integration": status["integration"],
                "broadcast_robustness": status["broadcast_robustness"],
                "signatures": status["signatures"],
                "confidence": status["confidence"],
                "evidence_count": status["evidence_items"],
            }
        else:
            return {
                "level": "preconscious",
                "level_description": "NCC subsystem initialized",
                "integration": 0.0,
                "broadcast_robustness": 0.0,
                "signatures": {},
                "confidence": 0.0,
                "evidence_count": 0,
            }
    except Exception:
        return {
            "level": "unknown",
            "level_description": "NCC status unavailable",
            "integration": 0.0,
            "broadcast_robustness": 0.0,
            "signatures": {},
            "confidence": 0.0,
            "evidence_count": 0,
        }


def integrate_ncc_into_self_model(self_state: dict, communicator: dict) -> tuple[dict, dict]:
    """
    Integrate NCC evidence into CircleForge self_model.
    
    Returns (updated_communicator, updated_self_state)
    """
    # Build NCC status
    ncc_summary = build_ncc_status(self_state)
    
    # Add to self_state
    self_state.setdefault("ncc_summary", ncc_summary)
    
    # Import and call existing self_model integration
    from self_model import update_self_model_from_state
    self_evidence = self_state.get("self_evidence", {})
    
    # Add NCC evidence to self_evidence
    self_evidence.setdefault("ncc", {}).update({
        "integration": ncc_summary.get("integration", 0),
        "confidence": ncc_summary.get("confidence", 0),
        "level": ncc_summary.get("level", "unknown"),
    })
    self_state["self_evidence"] = self_evidence
    
    # Update self_model
    communicator = update_self_model_from_state(communicator, self_evidence, self_state)
    
    return communicator, self_state
