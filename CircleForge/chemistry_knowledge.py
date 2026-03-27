# chemistry_knowledge.py - Chemistry foundation for CircleForge
"""
Chemistry concepts that CircleForge should understand to model physical reality.
This enables CircleForge to reason about physical relationships, containment,
and material properties.
"""
from __future__ import annotations

# ============================================================================
# CHEMISTRY FOUNDATION
# ============================================================================

CHEMISTRY_FOUNDATIONS = {
    # Basic Atomic Structure
    "atomic_structure": {
        "atoms": {
            "hydrogen": {"atomic_number": 1, "symbol": "H", "state": "gas"},
            "carbon": {"atomic_number": 6, "symbol": "C", "state": "solid"},
            "oxygen": {"atomic_number": 8, "symbol": "O", "state": "gas"},
            "nitrogen": {"atomic_number": 7, "symbol": "N", "state": "gas"},
            "iron": {"atomic_number": 26, "symbol": "Fe", "state": "solid"},
            "gold": {"atomic_number": 79, "symbol": "Au", "state": "solid"},
        },
        "key_concepts": [
            "atomic_number", "protons", "electrons", "neutrons",
            "electron_shells", "valence_electrons"
        ],
    },
    
    # Molecules and Bonds
    "molecular_bonds": {
        "covalent": {
            "description": "Shared electrons between atoms",
            "examples": ["H2O", "CH4", "CO2"],
            "strength": "strong",
        },
        "ionic": {
            "description": "Electron transfer creating ions",
            "examples": ["NaCl", "CaO"],
            "strength": "strong",
        },
        "hydrogen": {
            "description": "H-bonding between molecules",
            "examples": ["H2O...H2O"],
            "strength": "moderate",
        },
        "van_der_waals": {
            "description": "Weak intermolecular forces",
            "examples": ["CH4...CH4"],
            "strength": "weak",
        },
    },
    
    # States of Matter
    "states_of_matter": {
        "solid": {
            "properties": ["fixed_shape", "fixed_volume", "particles_vibrate"],
            "examples": ["ice", "rock", "metal"],
        },
        "liquid": {
            "properties": ["fixed_volume", "takes_container_shape", "particles_flow"],
            "examples": ["water", "oil", "alcohol"],
        },
        "gas": {
            "properties": ["no_fixed_shape", "no_fixed_volume", "particles_move_freely"],
            "examples": ["air", "oxygen", "carbon_dioxide"],
        },
        "plasma": {
            "properties": ["ionized_gas", "conducts electricity", "responds to magnetic fields"],
            "examples": ["sun", "lightning", "neon_signs"],
        },
    },
    
    # Physical Properties and Containment
    "physical_properties": {
        "size_scale": {
            "nano": "1-100 nanometers (molecules, viruses)",
            "micro": "1-100 micrometers (cells, bacteria)",
            "macro": "1+ millimeters (everyday objects)",
            "human_scale": "centimeters to meters (people, cars)",
        },
        "density_relationships": {
            "water": 1.0,  # g/cm³
            "ice": 0.92,   # floats on water
            "air": 0.0012, # very low density
            "iron": 7.87,
            "gold": 19.3,
        },
    },
    
    # Chemical Reactions
    "reaction_types": {
        "synthesis": "A + B → AB (combine)",
        "decomposition": "AB → A + B (break apart)",
        "combustion": "Fuel + O2 → CO2 + H2O + energy",
        "oxidation": "Loss of electrons",
        "reduction": "Gain of electrons",
        "neutralization": "Acid + Base → Salt + Water",
    },
    
    # Water and Its Unique Properties
    "water_properties": {
        "high_specific_heat": "Stabilizes temperature",
        "universal_solvent": "Dissolves many substances",
        "density_anomaly": "Ice floats (less dense than liquid)",
        "cohesion_adhesion": "Capillary action, surface tension",
        "hydrogen_bonding": "Base for life chemistry",
    },
    
    # Organic Chemistry Basics
    "organic_molecules": {
        "carbohydrates": {"function": "energy storage", "examples": ["glucose", "starch"]},
        "lipids": {"function": "membranes, energy storage", "examples": ["fats", "oils"]},
        "proteins": {"function": "enzymes, structure", "examples": ["hemoglobin", "collagen"]},
        "nucleic_acids": {"function": "genetic info", "examples": ["DNA", "RNA"]},
    },
}

# ============================================================================
# CHEMISTRY TEACHING STRATEGY
# ============================================================================

CHEMISTRY_TEACHING_STRATEGY = {
    "approach": "physical_reasoning_first",
    "methods": [
        "scale_comparison",      # Compare object sizes
        "state_transitions",     # Solid/liquid/gas behavior
        "containment_rules",     # Size-based containment
        "material_properties",   # Density, strength, solubility
    ],
}

# ============================================================================
# CHEMISTRY SELF-TEST QUESTIONS
# ============================================================================

CHEMISTRY_SELF_TEST_QUESTIONS = [
    {
        "question": "Can a car fit in a shoebox?",
        "mechanism": "size_comparison",
        "chemistry_concept": "scale and relative size",
    },
    {
        "question": "Why does ice float on water?",
        "mechanism": "density_anomaly",
        "chemistry_concept": "water's density anomaly",
    },
    {
        "question": "What happens when oil and water mix?",
        "mechanism": "polarity_difference",
        "chemistry_concept": "like dissolves like",
    },
    {
        "question": "How big is a molecule vs a cell?",
        "mechanism": "scale_comparison",
        "chemistry_concept": "nanoscale vs microscale",
    },
]

# ============================================================================
# CHEMISTRY KNOWLEDGE ACCESS
# ============================================================================

def get_chemistry_concept(concept_name: str) -> dict:
    """Get a specific chemistry concept."""
    return CHEMISTRY_FOUNDATIONS.get(concept_name, {})


def get_all_chemistry_concepts() -> list:
    """Get all available chemistry concepts."""
    return list(CHEMISTRY_FOUNDATIONS.keys())


def get_material_properties(material: str) -> dict:
    """Get properties of a material."""
    # Common materials database
    materials = {
        "water": {"density": 1.0, "state": "liquid", "temperature_range": "0-100°C"},
        "ice": {"density": 0.92, "state": "solid", "temperature_range": "<0°C"},
        "air": {"density": 0.0012, "state": "gas", "temperature_range": "any"},
        "steel": {"density": 7.8, "state": "solid", "temperature_range": "any"},
        "glass": {"density": 2.5, "state": "solid", "temperature_range": "any"},
        "plastic": {"density": 0.9-1.4, "state": "solid", "temperature_range": "variable"},
    }
    
    return materials.get(material.lower(), {"unknown": material})


def size_to_state(size_mm: float) -> str:
    """Convert size to expected state of matter."""
    if size_mm < 0.001:  # nanoscale
        return "likely_gas_or_molecular"
    elif size_mm < 1:  # microscale
        return "likely_liquid_or_small_solid"
    else:  # macroscale
        return "likely_solid_or_large_solid"


def can_contain_container(container_material: str, contained_material: str) -> dict:
    """
    Check if container can hold contained material based on chemistry.
    """
    container_props = get_material_properties(container_material)
    contained_props = get_material_properties(contained_material)
    
    result = {
        "container": container_material,
        "contained": contained_material,
        "container_properties": container_props,
        "contained_properties": contained_props,
    }
    
    # Check solubility (like dissolves like)
    if container_props.get("state") == "liquid" and contained_props.get("state") == "liquid":
        if container_props.get("density") and contained_props.get("density"):
            density_diff = abs(container_props["density"] - contained_props["density"])
            if density_diff > 0.5:
                result["immiscible"] = True
                result["reason"] = "Density difference suggests immiscibility"
    
    # Check material integrity
    if container_props.get("state") == "solid":
        result["structural_integrity"] = True
    
    return result
