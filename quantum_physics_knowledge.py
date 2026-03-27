# quantum_physics_knowledge.py - Quantum physics foundation for Weslr
"""
Quantum physics concepts that Weslr should understand to model
the fundamental nature of reality, including quantum mechanics and gravity.
"""
from __future__ import annotations

# ============================================================================
# QUANTUM PHYSICS FOUNDATION
# ============================================================================

QUANTUM_PHYSICS_FOUNDATIONS = {
    # Quantum Mechanics Basics
    "quantum_mechanics": {
        "core_principles": {
            "wave-particle_duality": "Particles exhibit both wave and particle properties",
            "uncertainty_principle": "Cannot know position and momentum simultaneously",
            "superposition": "Systems exist in multiple states until measured",
            "entanglement": "Particles linked regardless of distance",
            "quantization": "Energy exists in discrete packets (quanta)",
        },
        "key_experiments": {
            "double_slit": "Shows wave-particle duality",
            " Stern-Gerlach": "Shows quantization of spin",
            "EPR_paradox": "Shows entanglement",
        },
    },
    
    # Quantum Field Theory
    "quantum_field_theory": {
        "concepts": {
            "fields": "Fundamental entities are fields, not particles",
            "particles": "Excitations of fields",
            "virtual_particles": "Temporary particles from vacuum fluctuations",
            "force_carriers": "Photons, gluons, W/Z bosons mediate forces",
        },
        "standard_model": {
            "fermions": "Matter particles (quarks, leptons)",
            "bosons": "Force carriers (photon, gluon, W, Z, Higgs)",
            "generations": "3 generations of increasing mass",
        },
    },
    
    # Gravity and Unification
    "gravity_unification": {
        "general_relativity": {
            "description": "Gravity as spacetime curvature",
            "equations": "Einstein field equations",
            "predictions": "Black holes, gravitational lensing, time dilation",
        },
        "quantum_gravity": {
            "challenge": "Unify quantum mechanics with gravity",
            "approaches": [
                "string_theory",
                "loop_quantum_gravity",
                "causal_dynamical_triangulation",
            ],
        },
        "open_questions": [
            "What is quantum gravity?",
            "Are there extra dimensions?",
            "What happens in black holes?",
        ],
    },
    
    # Quantum Applications
    "quantum_applications": {
        "computing": {
            "qubits": "Quantum bits in superposition",
            "algorithms": "Shor's, Grover's, quantum simulation",
            "challenges": "Decoherence, error correction",
        },
        "cryptography": {
            "quantum_key_distribution": "Unconditionally secure key exchange",
            "post_quantum_crypto": "Classical crypto resistant to quantum computers",
        },
        "sensing": {
            "quantum_sensors": "High-precision measurements",
            "applications": "Imaging, navigation, medical",
        },
    },
    
    # Quantum Interpretations
    "quantum_interpretations": {
        "copenhagen": "Wave function collapse on measurement",
        "many_worlds": "All outcomes occur in branching universes",
        "de_broglie_bohm": "Pilot wave theory with hidden variables",
        "quantum_bayesian": "Probabilities as subjective beliefs",
    },
}

# ============================================================================
# QUANTUM PHYSICS TEACHING STRATEGY
# ============================================================================

QUANTUM_PHYSICS_TEACHING_STRATEGY = {
    "approach": "paradox_first_then_formalism",
    "methods": [
        "counterintuitive_examples",  # Start with weird phenomena
        "mathematical_framework",     # Then the formalism
        "interpretation_comparison",  # Compare different views
        "application exploration",    # See what it can do
    ],
}

# ============================================================================
# QUANTUM PHYSICS SELF-TEST QUESTIONS
# ============================================================================

QUANTUM_PHYSICS_SELF_TEST_QUESTIONS = [
    {
        "question": "What is quantum gravity?",
        "mechanism": "unification_challenge",
        "quantum_physics_concept": "quantum gravity",
    },
    {
        "question": "Can something be in two places at once?",
        "mechanism": "superposition",
        "quantum_physics_concept": "superposition principle",
    },
    {
        "question": "What happens when particles are entangled?",
        "mechanism": "entanglement",
        "quantum_physics_concept": "quantum entanglement",
    },
    {
        "question": "How does quantum computing work?",
        "mechanism": "qubit_operations",
        "quantum_physics_concept": "quantum computation",
    },
]

# ============================================================================
# QUANTUM PHYSICS KNOWLEDGE ACCESS
# ============================================================================

def get_quantum_physics_concept(concept_name: str) -> dict:
    """Get a specific quantum physics concept."""
    return QUANTUM_PHYSICS_FOUNDATIONS.get(concept_name, {})


def get_all_quantum_physics_concepts() -> list:
    """Get all available quantum physics concepts."""
    return list(QUANTUM_PHYSICS_FOUNDATIONS.keys())


def explain_quantum_concept(concept: str) -> dict:
    """
    Explain a quantum physics concept in accessible terms.
    """
    explanations = {
        "superposition": "A quantum system can exist in multiple states simultaneously until measured. Like a spinning coin that's neither heads nor tails until it lands.",
        "entanglement": "Two particles become linked so that measuring one instantly affects the other, regardless of distance. Einstein called this 'spooky action at a distance'.",
        "uncertainty": "You cannot know both the exact position and momentum of a particle. The more precisely you know one, the less precisely you can know the other.",
        "quantization": "Energy comes in discrete packets called quanta. Like stairs instead of a ramp - you can only have specific energy levels, not anything in between.",
        "wave-particle": "Quantum objects behave as both particles and waves. Light acts like particles (photons) when hitting a surface but like waves when passing through slits.",
    }
    
    return {
        "concept": concept,
        "explanation": explanations.get(concept, "This concept requires deeper study."),
    }


def quantum_gravity_status() -> dict:
    """
    Describe the current state of quantum gravity research.
    """
    return {
        "status": "incomplete_theory",
        "challenge": "Unifying general relativity (gravity as spacetime curvature) with quantum mechanics (discrete quanta)",
        "main_approaches": [
            {
                "name": "String Theory",
                "description": "Particles are vibrating strings in extra dimensions",
                "status": "mathematically_promising but untested",
            },
            {
                "name": "Loop Quantum Gravity",
                "description": "Spacetime is quantized into discrete loops",
                "status": "background_independent but limited predictions",
            },
            {
                "name": "Causal Dynamical Triangulation",
                "description": "Spacetime built from simple geometric blocks",
                "status": "emergent spacetime observed in simulations",
            },
        ],
        "open_questions": [
            "What is the quantum nature of spacetime?",
            "What happens at the singularity inside black holes?",
            "How did gravity emerge in the early universe?",
        ],
    }
