#!/usr/bin/env python3
"""Live WESLR Architecture Decision Evaluation."""

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent))

from change_proposals import ExecutionGate
from governance_surface import GovernanceAggregationEngine, format_governance_view
from governance_invocation import invoke_governance_single, invoke_governance_compare, format_invocation_result
from governance_scorecard import GovernanceBenchmarkEngine, GovernanceDecisionRecord, GovernanceScorecard


def create_architecture_proposal(gate: ExecutionGate, title: str, description: str, 
                                  risk_level: str, calibration_confidence: float,
                                  affected_subsystems: list, validation_requirements: list,
                                  rollback_expectations: list, forecast_summary: str,
                                  rationale: str) -> tuple:
    """Create and submit an architecture proposal."""
    proposal = gate.create_proposal(
        title=title,
        description=description,
        risk_level=risk_level,
        calibration_confidence=calibration_confidence,
        affected_subsystems=affected_subsystems,
        validation_requirements=validation_requirements,
        rollback_expectations=rollback_expectations,
    )
    proposal.forecast_summary = forecast_summary
    proposal.rationale = rationale
    proposal.estimated_effort = 100 if risk_level == "high" else (50 if risk_level == "medium" else 20)
    
    gate.review_proposal(proposal.proposal_id, "approve", "operator")
    
    return proposal


def run_architecture_comparison():
    """Run full governance chain for architecture comparison."""
    print("=" * 70)
    print("LIVE WESLR ARCHITECTURE DECISION EVALUATION")
    print("=" * 70)
    print()
    print("Decision: Should WESLR move toward a more deterministic core?")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "proposals.json"
        
        gate = ExecutionGate(storage_path=storage_path)
        
        # OPTION A: Current mixed architecture
        print("=" * 70)
        print("OPTION A: Current Mixed Architecture")
        print("=" * 70)
        print("Description: Current governance + LLM-assisted interpretation")
        print()
        
        proposal_a = gate.create_proposal(
            title="Maintain Current Mixed Architecture",
            description="Continue with current governance + LLM-assisted interpretation model",
            risk_level="low",
            calibration_confidence=0.75,
            affected_subsystems=["state", "forecast", "narrative"],
            validation_requirements=["architecture_review"],
            rollback_expectations=["revert config"],
        )
        proposal_a.forecast_summary = "Maintains current balance between determinism and flexibility"
        proposal_a.rationale = "Current architecture provides good tradeoff between reliability and adaptability"
        gate.review_proposal(proposal_a.proposal_id, "approve", "operator")
        
        # OPTION B: More deterministic core
        print("=" * 70)
        print("OPTION B: More Deterministic Core")
        print("=" * 70)
        print("Description: Graph + radar + governance + scoring deterministic, LLM only for semantic interpretation")
        print()
        
        proposal_b = gate.create_proposal(
            title="More Deterministic Core",
            description="Graph + radar + governance + scoring deterministic, LLM only for semantic interpretation",
            risk_level="medium",
            calibration_confidence=0.82,
            affected_subsystems=["core", "graph", "radar", "governance", "forecast"],
            validation_requirements=["architecture_review", "performance_benchmark", "LLM_integration_test"],
            rollback_expectations=["gradual migration", "fallback to mixed"],
        )
        proposal_b.forecast_summary = "Higher reliability with reduced LLM dependency, LLM reserved for NL interpretation"
        proposal_b.rationale = "Deterministic core improves predictability while LLM handles natural language edge cases"
        gate.review_proposal(proposal_b.proposal_id, "approve", "operator")
        
        # OPTION C: Aggressive deterministic migration
        print("=" * 70)
        print("OPTION C: Aggressive Deterministic Migration")
        print("=" * 70)
        print("Description: Minimize LLM dependency as much as practical")
        print()
        
        proposal_c = gate.create_proposal(
            title="Aggressive Deterministic Migration",
            description="Minimize LLM dependency as much as practical",
            risk_level="high",
            calibration_confidence=0.65,
            affected_subsystems=["core", "graph", "radar", "forecast", "narrative"],
            validation_requirements=["risk_review", "team_capacity", "training_plan", "full_test_coverage"],
            rollback_expectations=["gradual migration", "LLM fallback"],
        )
        proposal_c.forecast_summary = "Maximum predictability but requires significant effort and LLM fallback complexity"
        proposal_c.rationale = "If we can move 95%+ to deterministic, it's worth the migration effort"
        gate.review_proposal(proposal_c.proposal_id, "approve", "operator")
        
        # Run governance surface for each option
        engine = GovernanceAggregationEngine(storage_path=storage_path)
        
        print("=" * 70)
        print("GOVERNANCE SURFACE: OPTION A (Current)")
        print("=" * 70)
        view_a = engine.get_governance_view(proposal_a.proposal_id)
        print(view_a.format_for_display())
        
        print("=" * 70)
        print("GOVERNANCE SURFACE: OPTION B (More Deterministic)")
        print("=" * 70)
        view_b = engine.get_governance_view(proposal_b.proposal_id)
        print(view_b.format_for_display())
        
        print("=" * 70)
        print("GOVERNANCE SURFACE: OPTION C (Aggressive)")
        print("=" * 70)
        view_c = engine.get_governance_view(proposal_c.proposal_id)
        print(view_c.format_for_display())
        
        # Run governance invocation comparison
        print("=" * 70)
        print("GOVERNANCE COMPARISON: All Options")
        print("=" * 70)
        result = invoke_governance_compare(
            [proposal_a.proposal_id, proposal_b.proposal_id, proposal_c.proposal_id],
            storage_path,
        )
        # Note: invoke_governance_compare only handles 2 proposals, so compare pairs
        print()
        print("Pairwise Comparison Results:")
        print()
        
        print("--- Option A vs Option B ---")
        result_ab = invoke_governance_compare([proposal_a.proposal_id, proposal_b.proposal_id], storage_path)
        print(format_invocation_result(result_ab))
        
        print()
        print("--- Option B vs Option C ---")
        result_bc = invoke_governance_compare([proposal_b.proposal_id, proposal_c.proposal_id], storage_path)
        print(format_invocation_result(result_bc))
        
        # Record benchmark
        print("=" * 70)
        print("BENCHMARK RECORDING")
        print("=" * 70)
        bench_engine = GovernanceBenchmarkEngine(storage_path=storage_path)
        
        # Record decision for Option B (most deterministic with reasonable confidence)
        scorecard = bench_engine.create_scorecard("architecture-decision")
        decision = GovernanceDecisionRecord(
            decision_id="dec-arch-001",
            decision_type="execute",
            proposal_id=proposal_b.proposal_id,
            timestamp="2026-04-06T12:40:00Z",
            operator="operator",
            reasoning="Option B provides best balance of determinism and practicality",
            confidence=0.82,
            status_at_decision="ready",
        )
        scorecard.add_decision(decision)
        bench_engine.set_outcome("architecture-decision", decision.decision_id, "success")
        
        print(f"Recorded decision: {decision.decision_id}")
        print(f"Recommended action: {result_ab['recommendation']['recommendation']}")
        
        summary = engine.get_benchmark_summary("architecture-decision")
        if summary:
            print(f"  Total decisions: {summary['total_decisions']}")
            print(f"  Reliability score: {summary['reliability_score']:.1%}")


if __name__ == "__main__":
    run_architecture_comparison()
