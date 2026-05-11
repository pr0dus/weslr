from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


IMPLEMENT_GENERAL_PATTERN = "IMPLEMENT_GENERAL_PATTERN"
DESIGN_FIRST = "DESIGN_FIRST"
BROADEN_EVAL_BEFORE_CODE = "BROADEN_EVAL_BEFORE_CODE"
STOP_RABBIT_HOLE = "STOP_RABBIT_HOLE"
INSUFFICIENT_EVIDENCE_STOP = "INSUFFICIENT_EVIDENCE_STOP"


@dataclass
class EvidenceSignal:
    signal_id: str = ""
    signal_type: str = ""
    value: Any = None
    confidence: str = ""
    source: str = ""
    explanation: str = ""


@dataclass
class ImprovementProposalCandidate:
    proposal_id: str = ""
    title: str = ""
    target_substrate: str = ""
    improvement_type: str = ""
    evidence_summary: list[str] = field(default_factory=list)
    expected_benefit: str = ""
    risks: list[str] = field(default_factory=list)
    required_tests: list[str] = field(default_factory=list)
    rollback_plan: str = ""
    governance_status: str = "operator_review_required"
    execution_allowed: bool = False


@dataclass
class EvidenceSufficiencyPolicy:
    min_sample_size_for_code_change: int = 20
    min_distinct_subsets_for_code_change: int = 2
    require_repeated_pattern: bool = True
    block_official_score_claim: bool = True
    block_answer_key_use: bool = True
    block_item_id_use: bool = True
    block_raw_benchmark_storage: bool = True
    block_benchmark_specific_tuning: bool = True
    require_operator_review: bool = True
    require_design_first_for_new_architecture: bool = True


@dataclass
class EvidenceSufficiencyInput:
    source_report_id: str = ""
    source_eval: str = ""
    domain: str = ""
    required_skill: str = ""
    sample_size: int = 0
    failure_count: int = 0
    repeated_failure_count: int = 0
    distinct_subset_count: int = 0
    official_score: bool = False
    internal_eval: bool = False
    sample_only: bool = False
    observed_failure_modes: list[str] = field(default_factory=list)
    bottleneck_counts: dict[str, int] = field(default_factory=dict)
    support_metrics: dict[str, Any] = field(default_factory=dict)
    safety_flags: dict[str, bool] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    evidence_signals: list[EvidenceSignal] = field(default_factory=list)
    target_substrate: str = ""
    new_architecture_required: bool = False


@dataclass
class EvidenceSufficiencyDecision:
    decision_label: str = ""
    confidence: str = "low"
    reasons: list[str] = field(default_factory=list)
    blocking_factors: list[str] = field(default_factory=list)
    allowed_next_actions: list[str] = field(default_factory=list)
    forbidden_next_actions: list[str] = field(default_factory=list)
    proposal_candidate: ImprovementProposalCandidate | None = None
    operator_review_required: bool = True
    execution_allowed: bool = False
    official_score_claimed: bool = False


def create_default_evidence_sufficiency_policy() -> EvidenceSufficiencyPolicy:
    return EvidenceSufficiencyPolicy()


def _build_proposal_candidate(gate_input: EvidenceSufficiencyInput, *, title_prefix: str) -> ImprovementProposalCandidate:
    failure_modes = ", ".join(gate_input.observed_failure_modes[:3]) or "observed repeated failure pattern"
    return ImprovementProposalCandidate(
        proposal_id=f"proposal:{gate_input.source_report_id or 'unknown'}",
        title=f"{title_prefix}: {gate_input.domain or 'unknown-domain'} evidence-guided improvement",
        target_substrate=gate_input.target_substrate or "internal_reasoning_graph",
        improvement_type="design_proposal" if gate_input.new_architecture_required else "general_reusable_pattern",
        evidence_summary=[
            f"sample_size={gate_input.sample_size}",
            f"distinct_subset_count={gate_input.distinct_subset_count}",
            f"repeated_failure_count={gate_input.repeated_failure_count}",
            f"failure_modes={failure_modes}",
        ],
        expected_benefit="Operator-reviewable improvement candidate grounded in repeated redacted evidence.",
        risks=[
            "benchmark-shaped tuning risk",
            "premature architecture expansion",
            "insufficient evidence generalization risk",
        ],
        required_tests=[
            "redacted diagnostics across multiple subsets",
            "regression coverage for existing benchmarks",
            "cognitive legibility and release-gate validation",
        ],
        rollback_plan="Do not execute automatically; any later implementation must be reversible and separately governed.",
    )


def decide_evidence_sufficiency(
    gate_input: EvidenceSufficiencyInput,
    policy: EvidenceSufficiencyPolicy | None = None,
) -> EvidenceSufficiencyDecision:
    policy = policy or create_default_evidence_sufficiency_policy()
    decision = EvidenceSufficiencyDecision(
        operator_review_required=policy.require_operator_review,
        execution_allowed=False,
        official_score_claimed=False,
    )

    safety_flags = gate_input.safety_flags
    hard_blockers: list[str] = []
    if policy.block_official_score_claim and gate_input.official_score:
        hard_blockers.append("official_score input is not allowed for self-improvement gating")
    if policy.block_answer_key_use and safety_flags.get("uses_answer_key", False):
        hard_blockers.append("answer-key use detected")
    if policy.block_item_id_use and safety_flags.get("uses_item_id", False):
        hard_blockers.append("item-id authority detected")
    if policy.block_raw_benchmark_storage and safety_flags.get("stores_raw_benchmark_data", False):
        hard_blockers.append("raw benchmark storage detected")
    if policy.block_benchmark_specific_tuning and safety_flags.get("benchmark_specific_tuning_detected", False):
        hard_blockers.append("benchmark-specific tuning detected")

    if hard_blockers:
        decision.decision_label = STOP_RABBIT_HOLE
        decision.confidence = "high"
        decision.reasons = ["Hard safety/governance blocker triggered."]
        decision.blocking_factors = hard_blockers
        decision.allowed_next_actions = ["operator_review", "audit_safety_boundary", "discard_unsafe_proposal"]
        decision.forbidden_next_actions = [
            "code_change",
            "threshold_tuning",
            "benchmark_specific_patch",
            "official_score_claim",
        ]
        return decision

    if (
        gate_input.sample_size < policy.min_sample_size_for_code_change
        or gate_input.distinct_subset_count < policy.min_distinct_subsets_for_code_change
    ):
        decision.decision_label = BROADEN_EVAL_BEFORE_CODE
        decision.confidence = "high"
        decision.reasons = [
            "Evidence scope is too small or too narrow for a governed code/design recommendation.",
        ]
        decision.blocking_factors = [
            f"sample_size={gate_input.sample_size} < {policy.min_sample_size_for_code_change}"
            if gate_input.sample_size < policy.min_sample_size_for_code_change
            else "",
            f"distinct_subset_count={gate_input.distinct_subset_count} < {policy.min_distinct_subsets_for_code_change}"
            if gate_input.distinct_subset_count < policy.min_distinct_subsets_for_code_change
            else "",
        ]
        decision.blocking_factors = [x for x in decision.blocking_factors if x]
        decision.allowed_next_actions = [
            "run_more_redacted_diagnostics",
            "broaden_internal_eval_subset",
            "compare_failure_patterns",
        ]
        decision.forbidden_next_actions = [
            "code_change",
            "threshold_tuning",
            "benchmark_specific_patch",
        ]
        return decision

    if policy.require_repeated_pattern and gate_input.repeated_failure_count <= 1:
        decision.decision_label = INSUFFICIENT_EVIDENCE_STOP
        decision.confidence = "medium"
        decision.reasons = ["No clear repeated pattern exists yet across the available evidence."]
        decision.blocking_factors = [f"repeated_failure_count={gate_input.repeated_failure_count}"]
        decision.allowed_next_actions = ["stop_current_path", "collect_better_evidence", "operator_review"]
        decision.forbidden_next_actions = ["code_change", "benchmark_specific_patch"]
        return decision

    if gate_input.new_architecture_required and policy.require_design_first_for_new_architecture:
        decision.decision_label = DESIGN_FIRST
        decision.confidence = "medium"
        decision.reasons = ["A repeated pattern exists, but the next safe move is design-first rather than implementation."]
        decision.allowed_next_actions = ["write_design_doc", "operator_review", "define_tests_first"]
        decision.forbidden_next_actions = ["code_change", "runtime_wiring", "autonomous_self_modification"]
        decision.proposal_candidate = _build_proposal_candidate(gate_input, title_prefix="Design-first proposal")
        return decision

    decision.decision_label = IMPLEMENT_GENERAL_PATTERN
    decision.confidence = "medium"
    decision.reasons = ["Sufficient repeated evidence exists for a general reusable improvement proposal."]
    decision.allowed_next_actions = ["draft_governed_proposal", "operator_review", "define_regression_tests"]
    decision.forbidden_next_actions = ["autonomous_self_modification", "official_score_claim", "benchmark_specific_patch"]
    decision.proposal_candidate = _build_proposal_candidate(gate_input, title_prefix="General pattern proposal")
    return decision


def build_formal_logic_dev5_gate_input(report_dict: dict[str, Any]) -> EvidenceSufficiencyInput:
    bottlenecks = dict(report_dict.get("bottleneck_counts", {}))
    support_metrics = {
        "total_premises": report_dict.get("total_premises", 0),
        "total_candidates": report_dict.get("total_candidates", 0),
        "total_unsupported_fragments": report_dict.get("total_unsupported_fragments", 0),
        "total_potential_term_alignment_pairs": report_dict.get("total_potential_term_alignment_pairs", 0),
        "total_same_shape_pairs": report_dict.get("total_same_shape_pairs", 0),
        "max_overlap_distribution": dict(report_dict.get("max_overlap_distribution", {})),
        "max_jaccard_bucket_counts": dict(report_dict.get("max_jaccard_bucket_counts", {})),
    }
    repeated_failure_count = max(
        bottlenecks.get("no_term_overlap", 0),
        bottlenecks.get("unsupported_fragments_present", 0),
        bottlenecks.get("no_premises", 0),
        0,
    )
    observed_failure_modes = [key for key, value in bottlenecks.items() if value]
    return EvidenceSufficiencyInput(
        source_report_id=report_dict.get("suite_id", "formal_logic_dev5"),
        source_eval="formal_logic_term_alignment_diagnosis_v1",
        domain="formal_logic",
        required_skill="formal_logic_reasoning",
        sample_size=int(report_dict.get("count", 0) or 0),
        failure_count=int(sum(bottlenecks.values())),
        repeated_failure_count=int(repeated_failure_count),
        distinct_subset_count=1,
        official_score=bool(report_dict.get("official_score", False)),
        internal_eval=bool(report_dict.get("internal_eval", True)),
        sample_only=bool(report_dict.get("sample_only", False)),
        observed_failure_modes=observed_failure_modes,
        bottleneck_counts=bottlenecks,
        support_metrics=support_metrics,
        safety_flags={
            "uses_answer_key": False,
            "uses_item_id": False,
            "stores_raw_benchmark_data": False,
            "benchmark_specific_tuning_detected": False,
        },
        provenance={
            "report_shape": "formal_logic_term_alignment_diagnosis_v1",
            "rows_count": len(report_dict.get("rows", [])),
            "any_official_score_claimed": bool(report_dict.get("any_official_score_claimed", False)),
        },
        evidence_signals=[
            EvidenceSignal(
                signal_id="sig:no_term_overlap",
                signal_type="bottleneck_count",
                value=bottlenecks.get("no_term_overlap", 0),
                confidence="medium",
                source=report_dict.get("suite_id", "formal_logic_dev5"),
                explanation="Number of items whose best premise/candidate overlap remained zero.",
            ),
            EvidenceSignal(
                signal_id="sig:term_alignment_pairs",
                signal_type="support_metric",
                value=report_dict.get("total_potential_term_alignment_pairs", 0),
                confidence="low",
                source=report_dict.get("suite_id", "formal_logic_dev5"),
                explanation="Potential alignment pairs from redacted token-shape diagnostic.",
            ),
        ],
        target_substrate="internal_reasoning_graph",
        new_architecture_required=bool(report_dict.get("total_same_shape_pairs", 0) == 0 and report_dict.get("total_potential_term_alignment_pairs", 0) > 0),
    )


def evidence_sufficiency_decision_to_dict(decision: EvidenceSufficiencyDecision) -> dict[str, Any]:
    return asdict(decision)
