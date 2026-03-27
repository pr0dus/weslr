# physics_knowledge.py - Physics foundation for CircleForge
"""
Physics concepts that CircleForge should understand to model physical reality,
forces, energy, motion, and the relationship between matter and energy.
"""
from __future__ import annotations

# ============================================================================
# PHYSICS FOUNDATION
# ============================================================================

PHYSICS_FOUNDATIONS = {
    # Classical Mechanics
    "classical_mechanics": {
        "laws": {
            "newton_first": "Inertia - object at rest stays at rest unless acted upon",
            "newton_second": "F = ma - Force equals mass times acceleration",
            "newton_third": "Action-reaction - for every action there's an equal opposite reaction",
        },
        "concepts": [
            "force", "mass", "acceleration", "velocity", "momentum",
            "energy", "work", "power", "friction", "gravity"
        ],
    },
    
    # Energy and Conservation
    "energy_principles": {
        "forms": {
            "kinetic": "Motion energy (1/2 * m * v^2)",
            "potential": "Stored energy (height, compression, chemical)",
            "thermal": "Heat energy",
            "chemical": "Energy in chemical bonds",
            "nuclear": "Energy in atomic nuclei",
            "electromagnetic": "Light, radio waves, X-rays",
        },
        "conservation": "Energy cannot be created or destroyed, only transformed",
        "entropy": "Energy tends to spread out (disorder increases)",
    },
    
    # Matter and Mass
    "matter_concepts": {
        "mass_vs_weight": {
            "mass": "Amount of matter (constant)",
            "weight": "Force of gravity on mass (varies by location)",
        },
        "density": "Mass per unit volume (density = mass / volume)",
        "states_of_matter": ["solid", "liquid", "gas", "plasma", " Bose-Einstein condensate"],
    },
    
    # Space and Time
    "spacetime": {
        "relative": "Measurements depend on observer's motion",
        "speed_of_light": "299,792,458 m/s (universal speed limit)",
        "causality": "Cause must precede effect",
    },
    
    # Thermodynamics
    "thermodynamics": {
        "laws": {
            "first": "Energy conservation",
            "second": "Entropy increases in isolated systems",
            "third": "Absolute zero unattainable",
        },
        "heat_transfer": ["conduction", "convection", "radiation"],
    },
    
    # Forces and Fields
    "fundamental_forces": {
        "gravity": "Weakest, but infinite range, always attractive",
        "electromagnetism": "Electric and magnetic fields",
        "strong_nuclear": "Holds nuclei together",
        "weak_nuclear": "Radioactive decay",
    },
    
    # Scale and Scale Effects
    "scale_effects": {
        "small": "Surface forces dominate (surface tension, van der Waals)",
        "large": "Gravity dominates, structural integrity critical",
        "transition": "Around 1mm-1m, different forces become important",
    },
}

# ============================================================================
# PHYSICS TEACHING STRATEGY
# ============================================================================

PHYSICS_TEACHING_STRATEGY = {
    "approach": "scale_and_forces_first",
    "methods": [
        "force_analysis",      # What forces act on an object?
        "energy_accounting",   # Where does energy come/go?
        "scale_effects",       # How do effects change with size?
    ],
}

# ============================================================================
# PHYSICS SELF-TEST QUESTIONS
# ============================================================================

PHYSICS_SELF_TEST_QUESTIONS = [
    {
        "question": "What happens to weight on the Moon vs Earth?",
        "mechanism": "gravity_difference",
        "physics_concept": "gravity and weight",
    },
    {
        "question": "Why can't we exceed light speed?",
        "mechanism": "relativity_limit",
        "physics_concept": "speed of light limit",
    },
    {
        "question": "How does surface area affect falling objects?",
        "mechanism": "air_resistance",
        "physics_concept": "drag and terminal velocity",
    },
]

# ============================================================================
# PHYSICS KNOWLEDGE ACCESS
# ============================================================================

def get_physics_concept(concept_name: str) -> dict:
    """Get a specific physics concept."""
    return PHYSICS_FOUNDATIONS.get(concept_name, {})


def get_all_physics_concepts() -> list:
    """Get all available physics concepts."""
    return list(PHYSICS_FOUNDATIONS.keys())


def calculate_weight(mass_kg: float, gravity_m_s2: float = 9.8) -> float:
    """
    Calculate weight (force) from mass.
    F = m * g
    """
    return mass_kg * gravity_m_s2


def compare_weights_on_planets(mass_kg: float) -> dict:
    """Compare weight on different planets."""
    gravities = {
        "mercury": 3.7,
        "venus": 8.87,
        "earth": 9.81,
        "mars": 3.71,
        "jupiter": 24.79,
        "saturn": 10.44,
        "uranus": 8.69,
        "neptune": 11.15,
        "moon": 1.62,
    }
    
    results = {}
    for planet, g in gravities.items():
        weight = calculate_weight(mass_kg, g)
        earth_weight = calculate_weight(mass_kg, 9.81)
        ratio = weight / earth_weight
        results[planet] = {
            "weight_newtons": round(weight, 2),
            "earth_ratio": round(ratio, 2),
        }
    
    return results


def scale_force_analysis(size_m: float) -> dict:
    """
    Analyze which forces dominate at different scales.
    """
    if size_m < 0.001:  # < 1mm
        return {
            "dominant_forces": ["surface_tension", "van_der_waals", "electrostatic"],
            "gravity_relevant": False,
            "reason": "At small scales, surface forces dominate over gravity",
        }
    elif size_m < 1:  # 1mm - 1m
        return {
            "dominant_forces": ["friction", "normal", "gravity", "air_resistance"],
            "gravity_relevant": True,
            "reason": "Medium scales: both surface and gravitational forces matter",
        }
    else:  # > 1m
        return {
            "dominant_forces": ["gravity", "structural_compression", "tension"],
            "gravity_relevant": True,
            "reason": "Large scales: gravity dominates, structural integrity critical",
        }


def energy_conversion_analysis(from_form: str, to_form: str) -> dict:
    """
    Analyze feasibility of energy conversion.
    """
    valid_forms = ["kinetic", "potential", "thermal", "chemical", "nuclear", "electromagnetic"]
    
    if from_form not in valid_forms or to_form not in valid_forms:
        return {
            "valid": False,
            "error": f"Must use valid forms: {valid_forms}",
        }
    
    # Common conversions and their efficiencies
    conversions = {
        ("chemical", "thermal"): {"efficiency": 0.8-0.95, "examples": ["combustion", "fire"]},
        ("chemical", "kinetic"): {"efficiency": 0.2-0.4, "examples": ["car engine", "muscle"]},
        ("potential", "kinetic"): {"efficiency": 0.9, "examples": ["falling object", "water wheel"]},
        ("electromagnetic", "chemical"): {"efficiency": 0.1-0.3, "examples": ["photosynthesis"]},
        ("nuclear", "thermal"): {"efficiency": 0.9, "examples": ["nuclear reactor"]},
    }
    
    key = (from_form, to_form)
    
    if key in conversions:
        return {
            "valid": True,
            "from": from_form,
            "to": to_form,
            "conversion": conversions[key],
        }
    
    return {
        "valid": False,
        "reason": f"Direct conversion not common; would require intermediate steps",
    }
