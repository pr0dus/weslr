"""Weslr Platform Core (v1)

Portable agent platform, runtime-agnostic.

Core modules:
- adapters: Runtime adapters (OpenClaw, Claude, OpenAI)
- continuity: Continuity state management
- contracts: Contract layer for state management
- concept_graph: Concept graph layer (linked knowledge)
- evidence_policy: Evidence policy and requirements
- file_ingestion: Text file ingestion
- file_router: Unified file routing
- request_intelligence: Request intelligence layer
- state: WESLR state management
- structured_data: Structured data handling
- task_anchor: Task anchors for continuity
- scenario_model: Self-Architecture Core v6 - Scenario comparison / Roadmap tradeoff layer
- architecture_memory: Self-Architecture Core v7 - Longitudinal architecture memory / consistency layer
- narrative: Self-Architecture Core v8-v9 - Operator narrative layer (memory-aware assessment)
- forecast: Self-Architecture Core v10 - Architectural simulation / forecast layer
- calibration: Self-Architecture Core v11 - Closed-loop governance / forecast calibration layer
- intervention_timing: Self-Architecture Core v36 - Intervention timing / Surfacing policy layer
- trust_dynamics: Self-Architecture Core v37 - Trust / Relationship dynamics layer
- multi_timescale_planning: Self-Architecture Core v38 - Multi-timescale planning / Trajectory layer
- deployment_persona: Self-Architecture Core v39 - Role / Deployment persona layer (additive, role-based, transparent)
- recommendation_presentation_mode: Self-Architecture Core v53 - Recommendation presentation mode layer (context-aware, adaptive)
- final_decision_explainability: Self-Architecture Core v54 - Final decision explainability layer (operator-readable explanation bundles)
- domain_adaptive_reasoning: Self-Architecture Core v55 - Domain adaptive reasoning hardening layer (domain identification, adaptation, transfer, constraints)
- model_assisted_not_model_dependent: Self-Architecture Core v56 - Model-assisted not model-dependent hardening layer (fallback chains, deterministic logic, operator-assisted operation)
"""

__version__ = "1.0.0"

from . import adapters
from . import continuity
from . import contracts
from . import concept_graph
from . import evidence_policy
from . import file_ingestion
from . import file_router
from . import request_intelligence
from . import scenario_model
from . import architecture_memory
from . import narrative
from . import forecast
from . import calibration
from . import intervention_timing
from . import trust_dynamics
from . import multi_timescale_planning
from . import deployment_persona
from . import state
from . import structured_data
from . import task_anchor
from . import constraint_invariant
from . import alternative_path_recovery
from . import state_transition
from . import operator_lifecycle
from . import final_decision_composer
from . import recommendation_delivery
from . import recommendation_presentation_mode
from . import final_decision_explainability
from . import domain_adaptive_reasoning
from . import model_assisted_not_model_dependent

__all__ = [
    "adapters",
    "continuity",
    "contracts",
    "concept_graph",
    "evidence_policy",
    "file_ingestion",
    "file_router",
    "request_intelligence",
    "scenario_model",
    "architecture_memory",
    "narrative",
    "forecast",
    "calibration",
    "intervention_timing",
    "trust_dynamics",
    "multi_timescale_planning",
    "deployment_persona",
    "state",
    "structured_data",
    "task_anchor",
    "constraint_invariant",
    "alternative_path_recovery",
    "state_transition",
    "operator_lifecycle",
    "final_decision_composer",
    "recommendation_delivery",
    "recommendation_presentation_mode",
    "final_decision_explainability",
    "domain_adaptive_reasoning",
    "model_assisted_not_model_dependent",
]
