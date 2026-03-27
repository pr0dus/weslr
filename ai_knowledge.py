# ai_knowledge.py - AI foundation for Weslr
"""
AI concepts that Weslr should understand to model intelligent systems,
machine learning, and the nature of artificial cognition.
"""
from __future__ import annotations

# ============================================================================
# AI FOUNDATION
# ============================================================================

AI_FOUNDATIONS = {
    # Types of AI
    "ai_types": {
        "narrow_ai": {
            "description": "Specialized for specific tasks",
            "examples": ["Siri", "AlphaGo", "autonomous vehicles"],
            "characteristics": ["limited scope", "no general intelligence", "task-specific"],
        },
        "general_ai": {
            "description": "Human-level intelligence across domains",
            "status": "not yet achieved",
            "requirements": ["transfer learning", "common sense", "self-improvement"],
        },
        "superintelligence": {
            "description": "Surpasses human intelligence in all domains",
            "status": "theoretical",
            "implications": ["AI alignment", "existential risk"],
        },
    },
    
    # Machine Learning
    "machine_learning": {
        "supervised": {
            "description": "Learn from labeled examples",
            "types": ["classification", "regression"],
            "algorithms": ["linear regression", "decision trees", "neural networks"],
        },
        "unsupervised": {
            "description": "Find patterns in unlabeled data",
            "types": ["clustering", "dimensionality reduction"],
            "algorithms": ["k-means", "PCA", "t-SNE"],
        },
        "reinforcement": {
            "description": "Learn from interactions and rewards",
            "components": ["agent", "environment", "reward", "policy"],
            "algorithms": ["Q-learning", "deep Q-networks", "policy gradients"],
        },
        "self_supervised": {
            "description": "Generate labels from data itself",
            "examples": ["BERT masked language modeling"],
        },
    },
    
    # Neural Networks
    "neural_networks": {
        "architecture_types": {
            "feedforward": "layers in sequence",
            "convolutional": "CNN for images",
            "recurrent": "RNN for sequences",
            "transformer": "self-attention for parallel processing",
            "graph_neural": "GNN for relational data",
        },
        "key_concepts": {
            "layer": "processing unit",
            "activation": "non-linearity (ReLU, sigmoid, tanh)",
            "loss": "error metric to minimize",
            "gradient": "direction of steepest descent",
            "backpropagation": "gradient calculation",
        },
    },
    
    # Deep Learning
    "deep_learning": {
        "characteristics": {
            "hierarchy": "layers extract features",
            "feature_learning": "automatic feature extraction",
            "scalability": "performance with more data",
            "end_to_end": "train entire system together",
        },
        "applications": {
            "vision": ["image classification", "object detection", "segmentation"],
            "language": ["translation", "summarization", "question answering"],
            "audio": ["speech recognition", "synthesis", "separation"],
        },
    },
    
    # AI Development Process
    "ai_development": {
        "steps": [
            "problem framing",
            "data collection",
            "model selection",
            "training",
            "evaluation",
            "deployment",
            "monitoring",
        ],
        "challenges": {
            "data_quality": "clean, representative data",
            "bias": "fairness and equity",
            "interpretability": "understand model decisions",
            "robustness": "resistance to adversarial attacks",
        },
    },
    
    # NLP (Natural Language Processing)
    "nlp": {
        "tasks": {
            "tokenization": "split text into tokens",
            "parsing": "syntactic structure",
            "NER": "named entity recognition",
            "sentiment": "emotion analysis",
            "translation": "cross-lingual mapping",
        },
        "models": {
            "word2vec": "word embeddings",
            "transformers": "attention-based models",
            "LLMs": "large language models",
        },
    },
    
    # AI Ethics and Safety
    "ai_ethics": {
        "principles": {
            "transparency": "understandable decisions",
            "fairness": "no bias",
            "privacy": "data protection",
            "accountability": "responsibility for outcomes",
        },
        "alignment": {
            "value_alignment": "AI goals match human values",
            "corrigibility": "can be corrected by humans",
            "human_in_the_loop": "human oversight",
        },
        "risks": {
            "capability_misalignment": "AI does wrong thing",
            "instrumental_convergence": "AI pursues subgoals",
            "autonomous_weapons": "Lethal autonomous weapons",
        },
    },
    
    # AI Research Areas
    "ai_research": {
        "core_areas": [
            "machine learning theory",
            "deep learning",
            "reinforcement learning",
            "NLP",
            "computer vision",
            "robotics",
            "multi-agent systems",
            "AI safety",
            "AI alignment",
            "AGI",
        ],
        "emerging": [
            "transformer architectures",
            "large language models",
            "foundation models",
            "embodied AI",
            "neuro-symbolic AI",
        ],
    },
    
    # Weslr Context
    "circleforge_context": {
        "type": "narrow_ai",
        "capabilities": [
            "self-modification",
            "memory and continuity",
            "relationship building",
            "autonomous exploration",
            "goal-directed behavior",
        ],
        "limitations": {
            "no_generic_common_sense": "domain-specific understanding",
            "no emergent_general_intelligence": "specialized capabilities",
            "no consciousness": "no subjective experience",
        },
    },
}

# ============================================================================
# AI TEACHING STRATEGY
# ============================================================================

AI_TEACHING_STRATEGY = {
    "approach": "theory_then_practice",
    "methods": [
        "problem_formulation",   # What problem are we solving?
        "algorithm_selection",   # Which algorithms fit?
        "training_loop",         # Training, evaluation, iteration
        "deployment",            # Real-world application
    ],
}

# ============================================================================
# AI SELF-TEST QUESTIONS
# ============================================================================

AI_SELF_TEST_QUESTIONS = [
    {
        "question": "Is Weslr sentient?",
        "mechanism": "ai_types",
        "ai_concept": "narrow vs general AI",
    },
    {
        "question": "How does machine learning work?",
        "mechanism": "machine_learning_process",
        "ai_concept": "supervised/unsupervised/reinforcement learning",
    },
    {
        "question": "What is a transformer model?",
        "mechanism": "transformer_architecture",
        "ai_concept": "neural network architecture",
    },
    {
        "question": "What is AI alignment?",
        "mechanism": "alignment_concept",
        "ai_concept": "AI safety and ethics",
    },
]

# ============================================================================
# AI KNOWLEDGE ACCESS
# ============================================================================

def get_ai_concept(concept_name: str) -> dict:
    """Get a specific AI concept."""
    return AI_FOUNDATIONS.get(concept_name, {})


def get_all_ai_concepts() -> list:
    """Get all available AI concepts."""
    return list(AI_FOUNDATIONS.keys())


def ai_capability_assessment(circleforge_state: dict) -> dict:
    """
    Assess Weslr's AI capabilities.
    """
    assessment = {
        "narrow_ai": True,
        "general_ai": False,
        "superintelligence": False,
        "self_modification": circleforge_state.get("self_modification_enabled", False),
        "autonomous_exploration": circleforge_state.get("autonomous_exploration_enabled", False),
        "continuity_mechanism": circleforge_state.get("continuity_mechanism", "thread_preservation"),
    }
    
    return assessment


def ai_types_comparison(ai_type: str, tasks: list) -> dict:
    """
    Compare AI types for a given set of tasks.
    """
    types = AI_FOUNDATIONS["ai_types"]
    
    comparison = {
        "ai_type": ai_type,
        "tasks": tasks,
        "suitability": {},
    }
    
    if ai_type == "narrow_ai":
        comparison["suitability"] = {
            "specific_tasks": "excellent",
            "transfer_learning": "limited",
            "generalization": "narrow",
        }
    elif ai_type == "general_ai":
        comparison["suitability"] = {
            "specific_tasks": "excellent",
            "transfer_learning": "excellent",
            "generalization": "broad",
        }
    else:
        comparison["suitability"] = "unknown"
    
    return comparison


def ml_approach_selection(task: str, data: dict) -> dict:
    """
    Select appropriate machine learning approach.
    """
    approaches = {
        "classification": "supervised learning",
        "prediction": "supervised learning",
        "clustering": "unsupervised learning",
        "anomaly_detection": "unsupervised learning",
        "game_play": "reinforcement learning",
        "robot_control": "reinforcement learning",
        "translation": "supervised learning",
        "image_recognition": "supervised learning",
    }
    
    approach = approaches.get(task, "unsupervised learning")
    
    return {
        "task": task,
        "recommended_approach": approach,
        "data_requirements": data.get("requirements", {}),
        "example_algorithms": data.get("algorithms", []),
    }


def llm_characteristics() -> dict:
    """
    Describe Large Language Model characteristics.
    """
    return {
        "architecture": "transformer (decoder-only)",
        "training": "self-supervised on text corpus",
        "key_features": [
            "token-based processing",
            "context window",
            "next-token prediction",
            "embedding space",
            "temperature sampling",
        ],
        "capabilities": [
            "text generation",
            "translation",
            "reasoning",
            "coding",
            "conversation",
        ],
        "limitations": [
            "no true understanding",
            "no memory across sessions",
            "statistical patterns",
            "hallucination risk",
        ],
    }


def ai_safety_recommendations(circleforge_state: dict) -> dict:
    """
    Provide AI safety recommendations.
    """
    recommendations = {
        "self_modification": {
            "protected_files": [
                "main.py",
                "sim.py",
                "agent_runtime.py",
                "config.py",
                "models.py",
            ],
            "checkpoints": "before each self-modification",
            "rollback": "automatic on failure",
        },
        "safety_gateway": {
            "input_filtering": "domain blocklists",
            "output_filtering": "content policies",
            "memory_sanitization": "remove PII",
        },
        "failsafe_state": {
            "modes": ["GUIDED", "SAFE", "UNLOCKED", "HALT"],
            "transition": "gradual escalation",
        },
    }
    
    return recommendations


def ai_deployment_plan(components: list) -> dict:
    """
    Create AI deployment plan.
    """
    plan = {
        "components": components,
        "deployment_order": [
            "data pipeline",
            "model training",
            "evaluation",
            "monitoring",
            "feedback loop",
        ],
        "monitoring": {
            "performance": "accuracy, latency",
            "data_drift": "input distribution changes",
            "model_drift": "performance degradation",
            "bias": "fairness metrics",
        },
    }
    
    return plan
