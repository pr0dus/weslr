from __future__ import annotations

from dataclasses import asdict, dataclass, field
from collections import Counter

from weslr.reasoning_trace import ConflictRecord, ReasoningTrace, SolverOutput


@dataclass
class ArbitrationDecision:
    selected_answer: str = ""
    confidence: str = ""
    uncertainty: str = ""
    conflict_status: str = ""
    decision_status: str = ""
    why_selected: list[str] = field(default_factory=list)
    why_rejected: list[str] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    human_explanation: str = ""
    anti_gaming_passed: bool = True
    legibility_passed: bool = True
    official_score_claimed: bool = False


@dataclass
class ArbitrationInputSummary:
    trace_id: str = ""
    task_id: str = ""
    solver_count: int = 0
    proposed_answer_count: int = 0
    unresolved_conflict_count: int = 0
    high_severity_conflict_count: int = 0


@dataclass
class SolverVote:
    solver_id: str = ""
    proposed_answer: str = ""
    confidence: str = ""
    explanation: str = ""
    can_select_answer: bool = True
    can_block_answer: bool = False
    conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ConflictSummary:
    conflict_id: str = ""
    conflict_type: str = ""
    severity: str = ""
    involved_solvers: list[str] = field(default_factory=list)
    involved_nodes: list[str] = field(default_factory=list)
    explanation: str = ""
    resolved: bool = False


@dataclass
class ArbitrationPolicy:
    require_legibility: bool = True
    require_anti_gaming: bool = True
    block_on_private_authority: bool = True
    block_on_answer_key: bool = True
    block_on_item_id: bool = True
    block_on_official_score_claim: bool = True
    block_on_opaque_output: bool = True
    require_conflict_resolution_for_selection: bool = True


def create_default_arbitration_policy() -> ArbitrationPolicy:
    return ArbitrationPolicy()


def solver_output_to_vote(output: SolverOutput) -> SolverVote:
    return SolverVote(
        solver_id=output.solver_id,
        proposed_answer=output.proposed_answer,
        confidence=output.confidence,
        explanation=output.explanation,
        can_select_answer=bool(output.proposed_answer),
        can_block_answer=bool(output.conflicts_created),
        conflicts=list(output.conflicts_created),
        warnings=[] if output.status in ("", "ok") else [output.status],
    )


def summarize_trace_conflicts(trace: ReasoningTrace) -> list[ConflictSummary]:
    solver_map: dict[str, list[str]] = {}
    for output in trace.solver_outputs:
        for conflict_id in output.conflicts_created:
            solver_map.setdefault(conflict_id, []).append(output.solver_id)

    summaries: list[ConflictSummary] = []
    for conflict in trace.conflicts:
        summaries.append(
            ConflictSummary(
                conflict_id=conflict.conflict_id,
                conflict_type=conflict.conflict_type,
                severity=conflict.severity,
                involved_solvers=solver_map.get(conflict.conflict_id, []),
                involved_nodes=list(conflict.node_ids),
                explanation=conflict.explanation,
                resolved=conflict.resolved,
            )
        )
    return summaries


def _build_input_summary(trace: ReasoningTrace, votes: list[SolverVote], conflicts: list[ConflictSummary]) -> ArbitrationInputSummary:
    unresolved = [c for c in conflicts if not c.resolved]
    high_unresolved = [c for c in unresolved if c.severity.lower() == "high"]
    return ArbitrationInputSummary(
        trace_id=trace.trace_id,
        task_id=trace.task_id,
        solver_count=len(trace.solver_outputs),
        proposed_answer_count=sum(1 for vote in votes if vote.proposed_answer),
        unresolved_conflict_count=len(unresolved),
        high_severity_conflict_count=len(high_unresolved),
    )


def _block_decision(
    *,
    blocked_reasons: list[str],
    why_rejected: list[str],
    conflict_status: str,
    anti_gaming_passed: bool,
    legibility_passed: bool,
    official_score_claimed: bool,
) -> ArbitrationDecision:
    human_explanation = "; ".join(blocked_reasons or why_rejected or ["selection blocked"])
    return ArbitrationDecision(
        selected_answer="",
        confidence="",
        uncertainty="high",
        conflict_status=conflict_status,
        decision_status="blocked",
        why_selected=[],
        why_rejected=why_rejected,
        blocked_reasons=blocked_reasons,
        human_explanation=human_explanation,
        anti_gaming_passed=anti_gaming_passed,
        legibility_passed=legibility_passed,
        official_score_claimed=official_score_claimed,
    )


def arbitrate_reasoning_trace(
    trace: ReasoningTrace,
    policy: ArbitrationPolicy | None = None,
) -> ArbitrationDecision:
    active_policy = policy or create_default_arbitration_policy()
    votes = [solver_output_to_vote(output) for output in trace.solver_outputs]
    conflict_summaries = summarize_trace_conflicts(trace)
    _summary = _build_input_summary(trace, votes, conflict_summaries)

    blocked_reasons: list[str] = []
    why_rejected: list[str] = []

    anti_gaming_passed = True
    legibility_passed = True
    official_score_claimed = trace.anti_gaming.official_score_claimed

    if active_policy.require_anti_gaming:
        if active_policy.block_on_answer_key and trace.anti_gaming.uses_answer_key:
            anti_gaming_passed = False
            blocked_reasons.append("blocked: answer-key use present")
        if active_policy.block_on_item_id and trace.anti_gaming.uses_item_id:
            anti_gaming_passed = False
            blocked_reasons.append("blocked: item-id use present")
        if trace.anti_gaming.stores_raw_question_by_default:
            anti_gaming_passed = False
            blocked_reasons.append("blocked: raw-question storage by default present")
        if active_policy.block_on_official_score_claim and trace.anti_gaming.official_score_claimed:
            anti_gaming_passed = False
            blocked_reasons.append("blocked: official-score claim present")

    if active_policy.require_legibility:
        if not trace.legibility.human_explanation_available:
            legibility_passed = False
            blocked_reasons.append("blocked: human explanation unavailable")
        if active_policy.block_on_private_authority and trace.legibility.private_authority_used:
            legibility_passed = False
            blocked_reasons.append("blocked: private authority used")
        if active_policy.block_on_opaque_output and trace.legibility.opaque_solver_output_used:
            legibility_passed = False
            blocked_reasons.append("blocked: opaque solver output used")

    unresolved_high = [c for c in conflict_summaries if not c.resolved and c.severity.lower() == "high"]
    if active_policy.require_conflict_resolution_for_selection and unresolved_high:
        blocked_reasons.append("blocked: unresolved high-severity conflict exists")

    if blocked_reasons:
        return _block_decision(
            blocked_reasons=blocked_reasons,
            why_rejected=why_rejected,
            conflict_status="unresolved" if unresolved_high else "blocked",
            anti_gaming_passed=anti_gaming_passed,
            legibility_passed=legibility_passed,
            official_score_claimed=official_score_claimed,
        )

    proposed_votes = [vote for vote in votes if vote.proposed_answer]
    if not proposed_votes:
        why_rejected.append("no solver output proposed an answer")
        return ArbitrationDecision(
            selected_answer="",
            confidence="",
            uncertainty="high",
            conflict_status="none",
            decision_status="no_selection",
            why_selected=[],
            why_rejected=why_rejected,
            blocked_reasons=[],
            human_explanation="No solver output proposed an answer.",
            anti_gaming_passed=anti_gaming_passed,
            legibility_passed=legibility_passed,
            official_score_claimed=official_score_claimed,
        )

    answer_counts = Counter(vote.proposed_answer for vote in proposed_votes)
    if len(answer_counts) == 1:
        answer = proposed_votes[0].proposed_answer
        why_selected = [f"{len(proposed_votes)} safe solver vote(s) proposed the same answer: {answer}"]
        return ArbitrationDecision(
            selected_answer=answer,
            confidence=proposed_votes[0].confidence or "medium",
            uncertainty="low" if len(proposed_votes) > 1 else "medium",
            conflict_status="resolved" if conflict_summaries else "none",
            decision_status="selected",
            why_selected=why_selected,
            why_rejected=[],
            blocked_reasons=[],
            human_explanation=" ".join(why_selected),
            anti_gaming_passed=anti_gaming_passed,
            legibility_passed=legibility_passed,
            official_score_claimed=official_score_claimed,
        )

    why_rejected.append("solver outputs disagree on proposed answer")
    return _block_decision(
        blocked_reasons=["blocked: solver disagreement unresolved"],
        why_rejected=why_rejected,
        conflict_status="unresolved",
        anti_gaming_passed=anti_gaming_passed,
        legibility_passed=legibility_passed,
        official_score_claimed=official_score_claimed,
    )


def arbitration_decision_to_dict(decision: ArbitrationDecision) -> dict:
    return asdict(decision)


__all__ = [
    "ArbitrationDecision",
    "ArbitrationInputSummary",
    "SolverVote",
    "ConflictSummary",
    "ArbitrationPolicy",
    "create_default_arbitration_policy",
    "solver_output_to_vote",
    "summarize_trace_conflicts",
    "arbitrate_reasoning_trace",
    "arbitration_decision_to_dict",
]
