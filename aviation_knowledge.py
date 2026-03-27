# aviation_knowledge.py - Aviation knowledge base for Weslr
"""
Aviation knowledge modules for Weslr to understand flight operations,
safety protocols, aircraft systems, and aviation-specific decision making.
"""
from __future__ import annotations

import random
from typing import List, Dict, Any, Optional


# ============================================================================
# AVIATION CONCEPTS
# ============================================================================

AVIATION_CONCEPTS = {
    "flight_phases": [
        "taxi", "takeoff", "climb", "cruise", "descent", "approach", "landing"
    ],
    "aircraft_systems": [
        "propulsion", "flight controls", "hydraulics", "electrical",
        "fuel", "environmental control", "navigational", "communication"
    ],
    "flight_rules": [
        "VFR (Visual Flight Rules)", "IFR (Instrument Flight Rules)",
        "MVFR (Marginal VFR)", "Special VFR"
    ],
    "emergency_procedures": [
        "engine failure", "fire", "lost communication", "navigation failure",
        "pressurization failure", "structural damage", "fuel emergency"
    ],
    "aircraft_categories": [
        "single-engine land", "multi-engine land", "single-engine sea",
        "multi-engine sea", "rotorcraft", "glider", "balloon"
    ],
    "weather_phenomena": [
        "turbulence", "icing", "wind shear", "microburst", "thunderstorms",
        "fog", "low visibility", "crosswind"
    ],
    "airspace_classes": [
        "Class A (18000+ ft)", "Class B (busy airports)",
        "Class C (moderate traffic)", "Class D (controlled airports)",
        "Class E (controlled airspace)", "Class G (uncontrolled)"
    ],
    "navigation_systems": [
        "VOR (VHF Omnidirectional Range)", "ILS (Instrument Landing System)",
        "GPS (Global Positioning System)", "DME (Distance Measuring Equipment)",
        "NDB (Non-Directional Beacon)", "RNAV (Area Navigation)"
    ],
    "communication_procedures": [
        "readback", "hold short", "cleared to land", "go around",
        "squawk", "transponder codes", "frequency changes"
    ],
    "regulatory_bodies": [
        "FAA (US)", "EASA (Europe)", "ICAO (International)",
        "Transport Canada", "CASA (Australia)", "CAAC (China)"
    ]
}


def get_aviation_concept(concept: str) -> dict:
    """Get a specific aviation concept."""
    if concept in AVIATION_CONCEPTS:
        return {
            "name": concept,
            "values": AVIATION_CONCEPTS[concept],
            "category": "knowledge",
            "source": "aviation_knowledge.py"
        }
    
    # Search for concept in values
    for category, concepts in AVIATION_CONCEPTS.items():
        if concept.lower() in [c.lower() for c in concepts]:
            return {
                "name": concept,
                "category": category,
                "description": f"Found in {category} aviation concepts",
                "source": "aviation_knowledge.py"
            }
    
    return {
        "name": concept,
        "error": "Concept not found",
        "source": "aviation_knowledge.py"
    }


def get_all_aviation_concepts() -> list:
    """Get all available aviation concepts."""
    return list(AVIATION_CONCEPTS.keys())


def get_flight_procedures(phase: str) -> dict:
    """Get procedures for a specific flight phase."""
    procedures = {
        "taxi": [
            "Confirm clearance before taxiing",
            "Monitor ATC instructions",
            "Maintain safe distance from other aircraft",
            "Use checklist for before taxi"
        ],
        "takeoff": [
            "Set correct takeoff power",
            "Verifyairspeed", "Monitor pitch attitude",
            "Maintain runway centerline",
            "Rotate at Vr speed"
        ],
        "cruise": [
            "Set cruise power and pitch",
            "Monitor fuel consumption",
            "Check navigation accuracy",
            "Contact next ATC facility"
        ],
        "landing": [
            "Configure for landing (gear down, flaps)",
            "Follow approach procedure",
            "Maintain glide slope",
            "Touch down in proper runway zone"
        ]
    }
    
    return {
        "phase": phase,
        "procedures": procedures.get(phase, ["Procedure not defined"]),
        "source": "aviation_knowledge.py"
    }


def get_emergency_checklist(emergency_type: str) -> dict:
    """Get emergency checklist for a specific scenario."""
    checklists = {
        "engine_failure": {
            "immediate": [
                "Maintain aircraft control",
                "Identify failed engine (multi-engine)",
                "Feather dead engine (if applicable)",
                "Check fuel and ignition"
            ],
            "后续": [
                "Declare emergency if needed",
                "Select suitable landing site",
                "Communicate with ATC",
                "Prepare for forced landing"
            ]
        },
        "fire": {
            "immediate": [
                "Identify fire location",
                "Use appropriate fire extinguisher",
                "Close fuel valveclose",
                "Cut electrical bus if needed"
            ],
            "后续": [
                "Declare emergency",
                "Prepare for immediate landing",
                "Evacuate passengers if required"
            ]
        },
        "lost_communication": {
            "VFR": "Maintain VFR, land as soon as practicable",
            "IFR": "Follow last received clearance, proceed to planned destination",
            "squawk": "Set transponder to 7600"
        }
    }
    
    return {
        "emergency_type": emergency_type,
        "checklist": checklists.get(emergency_type, {"error": "Emergency not found"}),
        "source": "aviation_knowledge.py"
    }


def calculate_headwind_crosswind(wind_dir: int, wind_speed: float, runway_dir: int) -> dict:
    """Calculate headwind and crosswind components."""
    import math
    
    # Calculate angle difference
    angle_diff = abs(wind_dir - runway_dir)
    if angle_diff > 180:
        angle_diff = 360 - angle_diff
    
    # Convert to radians
    angle_rad = math.radians(angle_diff)
    
    # Calculate components
    headwind = wind_speed * math.cos(angle_rad)
    crosswind = wind_speed * math.sin(angle_rad)
    
    return {
        "wind_direction": wind_dir,
        "wind_speed_knots": wind_speed,
        "runway_direction": runway_dir,
        "headwind_knots": round(headwind, 1),
        "crosswind_knots": round(crosswind, 1),
        "angle_from_runway": angle_diff,
        "source": "aviation_knowledge.py"
    }


def get_airspace_restrictions(airspace_class: str) -> dict:
    """Get requirements for a specific airspace class."""
    requirements = {
        "Class A": {
            "IFR_only": True,
            "clearance_required": True,
            "transponder_required": "Mode C",
            "communication_required": "Continuous with ATC"
        },
        "Class B": {
            "IFR_or_VFR": True,
            "clearance_required": True,
            "transponder_required": "Mode C (within 30NM)",
            "communication_required": "Two-way radio with ATC"
        },
        "Class C": {
            "IFR_or_VFR": True,
            "clearance_required": False,
            "transponder_required": "Mode C (within 10NM)",
            "communication_required": "Two-way radio with ATC"
        },
        "Class D": {
            "IFR_or_VFR": True,
            "clearance_required": False,
            "transponder_required": None,
            "communication_required": "Two-way radio with ATC"
        }
    }
    
    return {
        "airspace_class": airspace_class,
        "requirements": requirements.get(airspace_class, {"error": "Class not found"}),
        "source": "aviation_knowledge.py"
    }


def integrate_aviation_into_self_model(self_state: dict) -> dict:
    """
    Integrate aviation knowledge into Weslr's self-model.
    
    Adds aviation-specific capabilities:
    - Flight phase awareness
    - Emergency procedure templates
    - Navigation calculations
    """
    aviation_mind = self_state.setdefault("aviation_mind", {
        "flight_phases_tracked": [],
        "systems_monitoring": [],
        "procedures_available": 0,
        "last_flight_update": 0
    })
    
    # Count available procedures
    aviation_mind["procedures_available"] = sum(
        len(procs) for procs in [
            AVIATION_CONCEPTS["flight_phases"],
            AVIATION_CONCEPTS["emergency_procedures"],
            AVIATION_CONCEPTS["airspace_classes"]
        ]
    )
    
    self_state["aviation_mind"] = aviation_mind
    
    return self_state


def generate_aviation_self_description(self_state: dict) -> str:
    """Generate aviation-related self-description for Weslr."""
    aviation_mind = self_state.get("aviation_mind", {})
    
    capabilities = [
        "Flight phase management",
        "Emergency procedure retrieval",
        "Wind calculations for takeoff/landing",
        "Airspace requirements guidance"
    ]
    
    return (
        f"I can assist with aviation operations including: "
        f"{', '.join(capabilities[:3])}. "
        f"I've tracked {aviation_mind.get('procedures_available', 0)} aviation procedures."
    )


# ============================================================================
# SPIRAL EXPANSION - ADDITIONAL AERONAUTICS KNOWLEDGE
# ============================================================================

def get_spiral_expansion(base_knowledge: dict) -> dict:
    """Expand aviation knowledge into related aeronautics domains."""
    return {
        "aerodynamics": [
            "Lift generation principles",
            "Drag types and reduction",
            "Stall characteristics",
            "Pitch/yaw/roll dynamics"
        ],
        "meteorology": [
            "Weather pattern recognition",
            "Turbulence prediction",
            "Icing conditions",
            "Wind shear detection"
        ],
        "navigation": [
            "Route planning",
            "Fuel calculation",
            "Contingency routing",
            "Approach procedure selection"
        ],
        "human_factors": [
            "Crew resource management",
            "Decision making under stress",
            "Situational awareness",
            "Fatigue management"
        ]
    }


# ============================================================================
# INTEGRATION WITH EXISTING MODULES
# ============================================================================

# Import existing knowledge modules
from psychology_knowledge import (
    integrate_psychology_into_self_model,
    get_psychology_concept,
    get_all_concepts as get_all_psychology_concepts
)


def get_all_aviation_concepts_extended() -> list:
    """Get all aviation concepts including psychology integration."""
    # Start with aviation concepts
    concepts = list(AVIATION_CONCEPTS.keys())
    
    # Add psychology concepts that apply to aviation
    aviation_psychology = [
        "stress_response",
        "decision_making",
        "fatigue",
        "situational_awareness",
        "crew_communication"
    ]
    
    concepts.extend(aviation_psychology)
    
    return concepts


def get_aviation_psychology_concept(concept: str) -> dict:
    """Get psychology concept with aviation context."""
    # First try as aviation concept
    result = get_aviation_concept(concept)
    if "error" not in result:
        return result
    
    # Then try as psychology concept
    psych_result = get_psychology_concept(concept)
    if "error" not in psych_result:
        return {
            **psych_result,
            "aviation_context": "Applicable to aviation psychology"
        }
    
    return psych_result


# ============================================================================
# END OF AVIATION KNOWLEDGE MODULE
# ============================================================================
