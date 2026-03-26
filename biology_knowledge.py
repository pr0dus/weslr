# biology_knowledge.py - Biology foundation for CircleForge
"""
Biology concepts that CircleForge should understand to model living systems,
cells, organisms, and the distinction between living and non-living.
"""
from __future__ import annotations

# ============================================================================
# BIOLOGY FOUNDATION
# ============================================================================

BIOLOGY_FOUNDATIONS = {
    # Cell Theory
    "cell_theory": {
        "principles": [
            "All living things are made of cells",
            "Cells are the basic unit of life",
            "New cells come from existing cells",
        ],
        "types": {
            "prokaryotic": {
                "description": "Simple cells without nucleus",
                "examples": ["bacteria", "archaea"],
                "size": "1-10 micrometers",
            },
            "eukaryotic": {
                "description": "Complex cells with nucleus",
                "examples": ["plant", "animal", "fungus", "protist"],
                "size": "10-100 micrometers",
            },
        },
    },
    
    # Organism Levels
    "organism_levels": {
        "cell": "Basic unit (e.g., neuron, muscle cell)",
        "tissue": "Group of similar cells (e.g., muscle tissue)",
        "organ": "Multiple tissues working (e.g., heart, brain)",
        "organ_system": "Organs cooperating (e.g., circulatory, nervous)",
        "organism": "Complete living entity",
    },
    
    # Characteristics of Life
    "characteristics_of_life": {
        "organization": "Highly organized structure",
        "metabolism": "Energy processing (anabolism + catabolism)",
        "homeostasis": "Internal regulation (e.g., temperature, pH)",
        "growth": "Increase in size or number",
        "adaptation": "Evolutionary changes over generations",
        "response": "React to stimuli",
        "reproduction": "Create offspring",
    },
    
    # DNA and Genetics Basics
    "dna_basics": {
        "structure": {
            "double_helix": "Two strands twisted",
            "base_pairs": ["A-T", "C-G"],
            "function": "Stores genetic instructions",
        },
        "central_dogma": {
            "transcription": "DNA → RNA",
            "translation": "RNA → Protein",
            "flow": "DNA makes RNA makes protein",
        },
    },
    
    # Evolution and Natural Selection
    "evolution": {
        "mechanism": {
            "variation": "Differences in traits",
            "inheritance": "Traits passed to offspring",
            "selection": "Some traits favored",
            "time": "Changes accumulate over generations",
        },
        "evidence": [
            "Fossil record",
            "Homologous structures",
            "DNA similarity",
            "Observed evolution",
        ],
    },
    
    # Ecosystems and Interdependence
    "ecosystems": {
        "trophic_levels": [
            "producers (plants, algae)",
            "primary_consumers (herbivores)",
            "secondary_consumers (carnivores)",
            "decomposers (fungi, bacteria)",
        ],
        "interdependence": "All organisms rely on others for survival",
    },
    
    # Human Biology Basics
    "human_biology": {
        "organ_systems": {
            "nervous": "Brain, spinal cord, nerves (control)",
            "circulatory": "Heart, blood vessels (transport)",
            "respiratory": "Lungs (gas exchange)",
            "digestive": "Stomach, intestines (food processing)",
            "skeletal": "Bones (support)",
            "muscular": "Muscles (movement)",
        },
        "brain_regions": {
            "cerebrum": "Thinking, memory, emotion",
            "cerebellum": "Balance, coordination",
            "brainstem": "Basic life functions (breathing, heart rate)",
            "limbic_system": "Emotions, memory",
        },
    },
    
    # Comparison: Living vs Non-Living
    "living_vs_nonliving": {
        "living": {
            "criteria": [
                "has cells",
                "uses energy",
                "responds to environment",
                "grows and develops",
                "reproduces",
                "evolves",
            ],
            "examples": ["human", "tree", "bacteria", "fungus"],
        },
        "nonliving": {
            "criteria": ["lacks one or more life characteristics"],
            "examples": ["rock", "car", "computer", "shoebox"],
        },
    },
}

# ============================================================================
# BIOLOGY TEACHING STRATEGY
# ============================================================================

BIOLOGY_TEACHING_STRATEGY = {
    "approach": "scale_and_structure_first",
    "methods": [
        "cellular_basis",      # Start at cell level
        "hierarchical_organization",  # Cells → tissues → organs → organism
        "emergent_properties", # How complexity emerges
        "energy_flow",         # Photosynthesis → food chains
    ],
}

# ============================================================================
# BIOLOGY SELF-TEST QUESTIONS
# ============================================================================

BIOLOGY_SELF_TEST_QUESTIONS = [
    {
        "question": "Is a car alive?",
        "mechanism": "living_vs_nonliving",
        "biology_concept": "characteristics of life",
    },
    {
        "question": "Can a virus reproduce on its own?",
        "mechanism": "reproduction_requirement",
        "biology_concept": "virus biology",
    },
    {
        "question": "What is the basic unit of life?",
        "mechanism": "cell_theory",
        "biology_concept": "cell theory",
    },
    {
        "question": "How do cells get energy?",
        "mechanism": "metabolism",
        "biology_concept": "cellular respiration",
    },
]

# ============================================================================
# BIOLOGY KNOWLEDGE ACCESS
# ============================================================================

def get_biology_concept(concept_name: str) -> dict:
    """Get a specific biology concept."""
    return BIOLOGY_FOUNDATIONS.get(concept_name, {})


def get_all_biology_concepts() -> list:
    """Get all available biology concepts."""
    return list(BIOLOGY_FOUNDATIONS.keys())


def is_living(entity: str) -> dict:
    """
    Determine if an entity is living based on biology criteria.
    """
    entity_lower = entity.lower().strip()
    
    # Simple living/nonliving classification
    living_entities = [
        "human", "person", "animal", "plant", "fungus", "bacteria",
        "organism", "cell", "tissue", "organ", "human", "dog", "cat",
    ]
    
    nonliving_entities = [
        "rock", "car", "computer", "shoebox", "box", "table", "chair",
        "building", "house", "street", "water", "air", "fire",
    ]
    
    # Check exact matches
    if entity_lower in living_entities:
        return {
            "is_living": True,
            "reason": "Matches known living entity category",
            "supporting_traits": ["cells", "metabolism", "reproduction", "response"],
        }
    
    if entity_lower in nonliving_entities:
        return {
            "is_living": False,
            "reason": "Matches known nonliving entity category",
            "supporting_traits": ["no cells", "no metabolism", "no reproduction"],
        }
    
    # Generic classification based on entity type
    if any(word in entity_lower for word in ["car", "computer", "machine", "object"]):
        return {
            "is_living": False,
            "reason": "Machine/technology - lacks biological characteristics",
            "missing_traits": ["cells", "self-reproduction", "metabolism"],
        }
    
    if any(word in entity_lower for word in ["human", "person", "organism"]):
        return {
            "is_living": True,
            "reason": "Biological entity",
            "supporting_traits": ["cells", "metabolism", "reproduction", "response"],
        }
    
    # Default: unknown
    return {
        "is_living": "unknown",
        "reason": "Cannot determine from description alone",
        "information_needed": "More specific entity details",
    }


def organism_complexity_level(entity: str) -> dict:
    """
    Estimate the biological complexity level of an organism.
    """
    entity_lower = entity.lower().strip()
    
    complexity = {
        "cellular": {
            "description": "Single-celled organism",
            "examples": ["bacteria", "archaea", "some_protists"],
            "characteristics": ["no nucleus", "simple structure", "rapid reproduction"],
        },
        "tissue_organ": {
            "description": "Multicellular with tissues and organs",
            "examples": ["animal", "plant", "fungus"],
            "characteristics": ["specialized cells", "tissues", "organs", "organ systems"],
        },
        "social": {
            "description": "Organism that forms complex social structures",
            "examples": ["human", "ant", "bee", "dolphin", "elephant"],
            "characteristics": ["social behavior", "communication", "cooperation"],
        },
    }
    
    # Classify
    if any(word in entity_lower for word in ["bacteria", "archaea", "viruses"]):
        return {"complexity": "cellular", "entity": entity}
    
    if any(word in entity_lower for word in ["human", "person"]):
        return {"complexity": "social", "entity": entity, "brain_region": "cerebrum dominant"}
    
    if any(word in entity_lower for word in ["animal", "mammal", "vertebrate"]):
        return {"complexity": "tissue_organ", "entity": entity}
    
    if any(word in entity_lower for word in ["plant", "tree", "flower"]):
        return {"complexity": "tissue_organ", "entity": entity, "photosynthesis": True}
    
    return {"complexity": "unknown", "entity": entity, "info": "More details needed"}


def biological_scale(size: float, unit: str = "mm") -> dict:
    """
    Map a size to biological scale categories.
    """
    # Convert to millimeters
    if unit == "nm":  # nanometers
        size_mm = size / 1_000_000
    elif unit == "um":  # micrometers
        size_mm = size / 1000
    elif unit == "mm":
        size_mm = size
    elif unit == "cm":
        size_mm = size * 10
    elif unit == "m":
        size_mm = size * 1000
    else:
        size_mm = size
    
    # Scale classification
    if size_mm < 0.001:  # < 1 micrometer
        return {
            "scale": "molecular/nanoscale",
            "description": "Molecules, viruses, proteins",
            "biological_relevance": "Chemical interactions, cellular machinery",
        }
    
    elif size_mm < 1:  # 1 micrometer - 1 millimeter
        return {
            "scale": "microscopic",
            "description": "Cells, bacteria, small tissues",
            "biological_relevance": "Cellular life, microbiology",
        }
    
    elif size_mm < 100:  # 1mm - 10cm
        return {
            "scale": "macroscopic",
            "description": "Organisms visible to naked eye",
            "biological_relevance": "Anatomy, organ systems",
        }
    
    else:  # > 10cm
        return {
            "scale": "macro/mega",
            "description": "Large organisms, populations",
            "biological_relevance": "Ecology, behavior, evolution",
        }
