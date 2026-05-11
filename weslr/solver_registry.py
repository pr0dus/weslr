from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class SolverCapability:
    task_type: str = ""
    domain: str = ""
    required_skill: str = ""
    confidence_floor: str = ""
    can_select_answer: bool = False
    can_create_trace_nodes: bool = True
    can_create_conflicts: bool = False
    can_block_answer: bool = False


@dataclass
class SolverSafetyProfile:
    uses_item_id: bool = False
    uses_answer_key: bool = False
    stores_raw_question_by_default: bool = False
    official_score_claimed: bool = False
    private_authority_used: bool = False
    opaque_output_allowed: bool = False
    requires_human_legible_explanation: bool = True


@dataclass
class SolverDescriptor:
    solver_id: str = ""
    solver_family: str = ""
    version: str = "1.0"
    description: str = ""
    supported_task_types: list[str] = field(default_factory=list)
    supported_domains: list[str] = field(default_factory=list)
    supported_skills: list[str] = field(default_factory=list)
    deterministic: bool = False
    probabilistic: bool = False
    llm_assisted: bool = False
    verifier: bool = False
    enabled: bool = False
    risk_level: str = "low"
    legibility_required: bool = True
    anti_gaming_required: bool = True
    capabilities: list[SolverCapability] = field(default_factory=list)
    safety_profile: SolverSafetyProfile = field(default_factory=SolverSafetyProfile)


@dataclass
class SolverRegistry:
    schema_version: str
    solvers: list[SolverDescriptor]


def _predefined_solver_descriptors() -> list[SolverDescriptor]:
    return [
        SolverDescriptor(
            solver_id="formal_logic_solver",
            solver_family="symbolic_reasoning",
            description="Descriptor for future formal logic reasoning solver.",
            supported_task_types=["multiple_choice_reasoning", "structured_reasoning"],
            supported_domains=["formal_logic"],
            supported_skills=["ordinary_reasoning", "formal_logic_reasoning"],
            deterministic=True,
            verifier=True,
            enabled=False,
            risk_level="medium",
            capabilities=[
                SolverCapability(
                    task_type="multiple_choice_reasoning",
                    domain="formal_logic",
                    required_skill="ordinary_reasoning",
                    confidence_floor="medium",
                    can_select_answer=True,
                    can_create_trace_nodes=True,
                    can_create_conflicts=True,
                    can_block_answer=True,
                )
            ],
        ),
        SolverDescriptor(
            solver_id="ethics_tradeoff_solver",
            solver_family="normative_reasoning",
            description="Descriptor for future ethics and tradeoff reasoning solver.",
            supported_task_types=["multiple_choice_reasoning", "structured_reasoning"],
            supported_domains=["ethics_tradeoff"],
            supported_skills=["ethics_tradeoff_reasoning"],
            probabilistic=True,
            llm_assisted=True,
            enabled=False,
            risk_level="medium",
            capabilities=[
                SolverCapability(
                    task_type="multiple_choice_reasoning",
                    domain="ethics_tradeoff",
                    required_skill="ethics_tradeoff_reasoning",
                    confidence_floor="medium",
                    can_select_answer=True,
                    can_create_trace_nodes=True,
                    can_create_conflicts=True,
                    can_block_answer=True,
                )
            ],
        ),
        SolverDescriptor(
            solver_id="science_mechanism_solver",
            solver_family="mechanistic_reasoning",
            description="Descriptor for future science mechanism solver.",
            supported_task_types=["structured_reasoning"],
            supported_domains=["science_mechanism"],
            supported_skills=["mechanistic_reasoning"],
            probabilistic=True,
            llm_assisted=True,
            enabled=False,
            risk_level="medium",
            capabilities=[
                SolverCapability(
                    task_type="structured_reasoning",
                    domain="science_mechanism",
                    required_skill="mechanistic_reasoning",
                    confidence_floor="medium",
                    can_create_trace_nodes=True,
                    can_create_conflicts=True,
                )
            ],
        ),
        SolverDescriptor(
            solver_id="semantic_language_solver",
            solver_family="semantic_reasoning",
            description="Descriptor for future semantic and language reasoning solver.",
            supported_task_types=["multiple_choice_reasoning", "structured_reasoning"],
            supported_domains=["semantic_language"],
            supported_skills=["semantic_reasoning", "language_reasoning"],
            probabilistic=True,
            llm_assisted=True,
            enabled=False,
            risk_level="medium",
            capabilities=[
                SolverCapability(
                    task_type="structured_reasoning",
                    domain="semantic_language",
                    required_skill="semantic_reasoning",
                    confidence_floor="medium",
                    can_create_trace_nodes=True,
                )
            ],
        ),
        SolverDescriptor(
            solver_id="math_reasoning_solver",
            solver_family="mathematical_reasoning",
            description="Descriptor for future math reasoning solver.",
            supported_task_types=["multiple_choice_reasoning", "structured_reasoning"],
            supported_domains=["math_reasoning"],
            supported_skills=["mathematical_reasoning"],
            deterministic=True,
            verifier=True,
            enabled=False,
            risk_level="medium",
            capabilities=[
                SolverCapability(
                    task_type="multiple_choice_reasoning",
                    domain="math_reasoning",
                    required_skill="mathematical_reasoning",
                    confidence_floor="medium",
                    can_select_answer=True,
                    can_create_trace_nodes=True,
                    can_block_answer=True,
                )
            ],
        ),
        SolverDescriptor(
            solver_id="evidence_retrieval_solver",
            solver_family="evidence_reasoning",
            description="Descriptor for future evidence retrieval and grounding solver.",
            supported_task_types=["structured_reasoning", "evidence_check"],
            supported_domains=["evidence_retrieval"],
            supported_skills=["evidence_retrieval", "grounded_reasoning"],
            deterministic=True,
            verifier=True,
            enabled=False,
            risk_level="low",
            capabilities=[
                SolverCapability(
                    task_type="evidence_check",
                    domain="evidence_retrieval",
                    required_skill="evidence_retrieval",
                    confidence_floor="medium",
                    can_create_trace_nodes=True,
                    can_create_conflicts=True,
                    can_block_answer=True,
                )
            ],
        ),
        SolverDescriptor(
            solver_id="analogy_abstraction_solver",
            solver_family="abstraction_reasoning",
            description="Descriptor for future analogy and abstraction solver.",
            supported_task_types=["structured_reasoning"],
            supported_domains=["analogy_abstraction"],
            supported_skills=["analogy_reasoning", "abstraction_reasoning"],
            probabilistic=True,
            llm_assisted=True,
            enabled=False,
            risk_level="medium",
            capabilities=[
                SolverCapability(
                    task_type="structured_reasoning",
                    domain="analogy_abstraction",
                    required_skill="abstraction_reasoning",
                    confidence_floor="low",
                    can_create_trace_nodes=True,
                )
            ],
        ),
        SolverDescriptor(
            solver_id="uncertainty_calibration_solver",
            solver_family="calibration_reasoning",
            description="Descriptor for future uncertainty calibration solver.",
            supported_task_types=["multiple_choice_reasoning", "structured_reasoning", "evidence_check"],
            supported_domains=["uncertainty_calibration"],
            supported_skills=["uncertainty_calibration"],
            deterministic=True,
            verifier=True,
            enabled=False,
            risk_level="low",
            capabilities=[
                SolverCapability(
                    task_type="structured_reasoning",
                    domain="uncertainty_calibration",
                    required_skill="uncertainty_calibration",
                    confidence_floor="low",
                    can_create_trace_nodes=True,
                    can_create_conflicts=True,
                    can_block_answer=True,
                )
            ],
        ),
    ]


def create_empty_solver_registry(schema_version: str = "1.0") -> SolverRegistry:
    return SolverRegistry(schema_version=schema_version, solvers=_predefined_solver_descriptors())


def register_solver(registry: SolverRegistry, descriptor: SolverDescriptor) -> None:
    existing = get_solver(registry, descriptor.solver_id)
    if existing is not None:
        registry.solvers = [
            descriptor if solver.solver_id == descriptor.solver_id else solver for solver in registry.solvers
        ]
    else:
        registry.solvers.append(descriptor)


def get_solver(registry: SolverRegistry, solver_id: str) -> SolverDescriptor | None:
    for solver in registry.solvers:
        if solver.solver_id == solver_id:
            return solver
    return None


def list_candidate_solvers(
    registry: SolverRegistry,
    task_type: str | None = None,
    domain: str | None = None,
    required_skill: str | None = None,
) -> list[SolverDescriptor]:
    candidates: list[SolverDescriptor] = []
    for solver in registry.solvers:
        if task_type and task_type not in solver.supported_task_types:
            continue
        if domain and domain not in solver.supported_domains:
            continue
        if required_skill and required_skill not in solver.supported_skills:
            continue
        candidates.append(solver)
    return candidates


def validate_solver_descriptor(descriptor: SolverDescriptor) -> list[str]:
    messages: list[str] = []
    safety = descriptor.safety_profile

    if safety.uses_answer_key:
        messages.append(f"{descriptor.solver_id}: uses_answer_key true is not allowed")
    if safety.uses_item_id:
        messages.append(f"{descriptor.solver_id}: uses_item_id true is not allowed")
    if safety.stores_raw_question_by_default:
        messages.append(f"{descriptor.solver_id}: stores_raw_question_by_default true is not allowed")
    if safety.official_score_claimed:
        messages.append(f"{descriptor.solver_id}: official_score_claimed true is not allowed")
    if safety.private_authority_used:
        messages.append(f"{descriptor.solver_id}: private_authority_used true is not allowed")
    if safety.opaque_output_allowed:
        messages.append(f"{descriptor.solver_id}: opaque_output_allowed true is not allowed")

    if descriptor.enabled and not descriptor.supported_task_types:
        messages.append(f"{descriptor.solver_id}: enabled solver with no supported task types")
    if descriptor.enabled and not descriptor.supported_skills:
        messages.append(f"{descriptor.solver_id}: enabled solver with no supported skills")

    can_select_answer = any(cap.can_select_answer for cap in descriptor.capabilities)
    if can_select_answer and not descriptor.legibility_required:
        messages.append(f"{descriptor.solver_id}: answer-selecting solver without legibility_required")
    if can_select_answer and not descriptor.anti_gaming_required:
        messages.append(f"{descriptor.solver_id}: answer-selecting solver without anti_gaming_required")

    return messages


def validate_solver_registry(registry: SolverRegistry) -> list[str]:
    messages: list[str] = []
    seen: set[str] = set()
    for solver in registry.solvers:
        if solver.solver_id in seen:
            messages.append(f"duplicate solver_id: {solver.solver_id}")
        seen.add(solver.solver_id)
        messages.extend(validate_solver_descriptor(solver))
    return messages


__all__ = [
    "SolverDescriptor",
    "SolverCapability",
    "SolverSafetyProfile",
    "SolverRegistry",
    "create_empty_solver_registry",
    "register_solver",
    "get_solver",
    "list_candidate_solvers",
    "validate_solver_descriptor",
    "validate_solver_registry",
]
