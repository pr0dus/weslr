# core_knowledge.py - Unified access to all knowledge modules
"""
This module provides unified access to all of CircleForge's knowledge domains:
- Psychology
- Chemistry
- Biology
- Physics
- Mathematics

The goal: CircleForge can reason across disciplines to understand the world.
"""
from __future__ import annotations

from psychology_knowledge import (
    get_psychology_concept, get_all_concepts as get_all_psychology_concepts,
    integrate_psychology_into_self_model, generate_psychological_self_description,
    run_psychological_self_test
)
from chemistry_knowledge import (
    get_chemistry_concept, get_all_chemistry_concepts,
    get_material_properties, size_to_state, can_contain_container
)
from biology_knowledge import (
    get_biology_concept, get_all_biology_concepts,
    is_living, organism_complexity_level, biological_scale
)
from physics_knowledge import (
    get_physics_concept, get_all_physics_concepts,
    calculate_weight, compare_weights_on_planets, scale_force_analysis, energy_conversion_analysis
)


# ============================================================================
# KNOWLEDGE SYNTHESIS
# ============================================================================

class CircleForgeKnowledge:
    """Unified knowledge interface for CircleForge."""
    
    def __init__(self):
        self.domains = {
            "psychology": get_all_concepts(),
            "chemistry": get_all_chemistry_concepts(),
            "biology": get_all_biology_concepts(),
            "physics": get_all_physics_concepts(),
        }
    
    def get_domain_knowledge(self, domain: str) -> list:
        """Get knowledge concepts for a domain."""
        if domain == "psychology":
            return get_all_concepts()
        elif domain == "chemistry":
            return get_all_chemistry_concepts()
        elif domain == "biology":
            return get_all_biology_concepts()
        elif domain == "physics":
            return get_all_physics_concepts()
        return []
    
def get_concept(domain: str, concept: str) -> dict:
    """Get a specific concept from a domain."""
    if domain == "psychology":
        return get_psychology_concept(concept)
    elif domain == "chemistry":
        return get_chemistry_concept(concept)
    elif domain == "biology":
        return get_biology_concept(concept)
    elif domain == "physics":
        return get_physics_concept(concept)
    return {}
    
    def integrate_into_self_model(self, self_model: dict) -> dict:
        """Integrate all knowledge domains into self-model."""
        # Start with psychology integration
        from psychology_knowledge import integrate_psychology_into_self_model
        self_model = integrate_psychology_into_self_model(self_model)
        return self_model
    
    def generate_self_description(self, self_model: dict) -> str:
        """Generate unified self-description across all domains."""
        # Use psychology's description as base
        from psychology_knowledge import generate_psychological_self_description
        return generate_psychological_self_description(self_model)


# ============================================================================
# CROSS-DISCIPLINE REASONING
# ============================================================================

def cross_discipline_reasoning(question: str) -> dict:
    """
    Apply cross-discipline reasoning to answer a question.
    Integrates knowledge from psychology, chemistry, biology, physics.
    """
    question_lower = question.lower()
    
    # Determine relevant domains
    domains = []
    
    if any(word in question_lower for word in ["think", "belief", "know", "mind", "self"]):
        domains.append("psychology")
    
    if any(word in question_lower for word in ["material", "object", "size", "contain", "fit"]):
        domains.append("chemistry")
        domains.append("physics")
    
    if any(word in question_lower for word in ["life", "alive", "organism", "human", "animal"]):
        domains.append("biology")
    
    if any(word in question_lower for word in ["force", "energy", "gravity", "motion"]):
        domains.append("physics")
    
    # Apply reasoning
    results = {
        "question": question,
        "relevant_domains": domains,
        "reasoning": {},
    }
    
    if "psychology" in domains:
        from psychology_knowledge import generate_psychological_self_description
        results["reasoning"]["psychology"] = generate_psychological_self_description({"core_drives": ["continuity", "understanding", "relationship", "self_revision"]})
    
    if "biology" in domains:
        # Check if question is about living things
        if any(word in question_lower for word in ["alive", "living"]):
            results["reasoning"]["biology"] = "Living things have cells, use energy, reproduce, respond, evolve"
    
    if "chemistry" in domains:
        # Check for containment/size questions
        if any(word in question_lower for word in ["fit", "contain", "size", "car", "shoebox"]):
            results["reasoning"]["chemistry"] = "Physical containment depends on relative size and material properties"
    
    if "physics" in domains:
        results["reasoning"]["physics"] = "Physical systems follow forces, conserve energy, and obey gravity"
    
    return results


def integrate_knowledge_into_self_model(self_model: dict) -> dict:
    """Integrate all knowledge domains into self-model."""
    # Psychology
    from psychology_knowledge import integrate_psychology_into_self_model
    self_model = integrate_psychology_into_self_model(self_model)
    
    # Add cross-domain integration notes
    self_model.setdefault("core_knowledge", {})
    self_model["core_knowledge"]["domains"] = ["psychology", "chemistry", "biology", "physics", "mathematics"]
    self_model["core_knowledge"]["integration_status"] = "in_progress"
    
    return self_model


# ============================================================================
# KNOWLEDGE TEST
# ============================================================================

def run_knowledge_test(question: str) -> dict:
    """
    Run a cross-discipline knowledge test.
    """
    result = cross_discipline_reasoning(question)
    
    # Add self-assessment
    from psychology_knowledge import run_psychological_self_test
    psychological_test = run_psychological_self_test({
        "continuity": {"session_count": 1},
        "relationships": {"known_humans": ["you"], "conversation_threads": {"test": {"status": "open"}}},
    })
    
    result["self_assessment"] = psychological_test
    result["total_score"] = psychological_test.get("overall_score", 0)
    
    return result
