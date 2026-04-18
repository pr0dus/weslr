#!/usr/bin/env python3
"""v20 — Governance Trial Pack / Real Proposal Evaluation Set

Curated set of realistic proposals to exercise the full governance chain.
"""

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent))

from change_proposals import ExecutionGate
from governance_surface import GovernanceAggregationEngine, format_governance_view
from governance_invocation import invoke_governance_single, invoke_governance_compare, format_invocation_result
from governance_scorecard import GovernanceBenchmarkEngine, GovernanceDecisionRecord, GovernanceScorecard


def create_quick_win_proposal(gate: ExecutionGate) -> tuple:
    """Quick-win proposal: Low risk, high impact, immediate execution."""
    proposal = gate.create_proposal(
        title="Add caching to public API endpoints",
        description="Implement Redis caching layer for GET requests to reduce latency by 40%",
        risk_level="low",
        calibration_confidence=0.92,
        affected_subsystems=["api", "performance"],
        validation_requirements=["latency_benchmark", "cache_coherence"],
        rollback_expectations=["revert cache config"],
    )
    proposal.forecast_summary = "Expected to reduce API latency by 40% with minimal risk"
    proposal.rationale = "Public API benchmark shows 40% latency improvement potential"
    proposal.estimated_effort = 20
    
    gate.review_proposal(proposal.proposal_id, "approve", "operator")
    
    return proposal, {
        "expected_outcome": "latency_reduction",
        "confidence": 0.92,
        "risk": "low",
        "recommended_action": "execute",
        "status": "ready",
    }


def create_medium_risk_proposal(gate: ExecutionGate) -> tuple:
    """Medium-risk proposal: Requires careful rollout."""
    proposal = gate.create_proposal(
        title="Database schema migration to partition tables",
        description="Split large tables by region to improve query performance",
        risk_level="medium",
        calibration_confidence=0.75,
        affected_subsystems=["database", "migrations", "infrastructure"],
        validation_requirements=["schema_review", "downtime_plan", "backup_verification"],
        rollback_expectations=["restore backup", "revert migration"],
    )
    proposal.forecast_summary = "Expected to improve query performance by 60% with careful rollout"
    proposal.rationale = "Query analysis shows 60% performance improvement potential"
    proposal.estimated_effort = 80
    
    gate.review_proposal(proposal.proposal_id, "defer", "operator")
    
    return proposal, {
        "expected_outcome": "query_performance_improvement",
        "confidence": 0.75,
        "risk": "medium",
        "recommended_action": "blockers",
        "status": "blocked",
    }


def create_long_horizon_proposal(gate: ExecutionGate) -> tuple:
    """Strategic long-horizon proposal: High effort, high impact."""
    proposal = gate.create_proposal(
        title="Complete rewrite of core routing engine",
        description="Migrate from Python to Rust for performance and safety",
        risk_level="high",
        calibration_confidence=0.60,
        affected_subsystems=["core", "routing", "testing", "documentation"],
        validation_requirements=["risk_review", "team_capacity", "training_plan"],
        rollback_expectations=["gradual migration", "Python fallback"],
    )
    proposal.forecast_summary = "Potential 3x routing performance gains with long-term safety"
    proposal.rationale = "Performance bottlenecks in routing require architectural change"
    proposal.estimated_effort = 200
    
    gate.review_proposal(proposal.proposal_id, "defer", "operator")
    
    return proposal, {
        "expected_outcome": "routing_performance_improvement",
        "confidence": 0.60,
        "risk": "high",
        "recommended_action": "defer",
        "status": "delayed",
    }


def create_blocked_proposal(gate: ExecutionGate) -> tuple:
    """Proposal that should be blocked/deferred."""
    proposal = gate.create_proposal(
        title="Remove database indexes from production",
        description="Remove all non-essential indexes to reduce storage",
        risk_level="high",
        calibration_confidence=0.25,
        affected_subsystems=["database", "performance"],
        validation_requirements=["impact_analysis", "recovery_plan"],
        rollback_expectations=["restore indexes from backup"],
    )
    proposal.forecast_summary = "High risk: Would severely degrade query performance"
    proposal.rationale = "Storage optimization initiative"
    proposal.estimated_effort = 10
    
    gate.review_proposal(proposal.proposal_id, "deny", "operator")
    
    return proposal, {
        "expected_outcome": None,
        "confidence": 0.25,
        "risk": "high",
        "recommended_action": "defer",
        "status": "blocked",
    }


def create_comparison_pair(gate: ExecutionGate) -> tuple:
    """Two proposals for direct comparison."""
    # First proposal
    proposal1 = gate.create_proposal(
        title="API caching with Redis",
        description="Implement Redis caching for public endpoints",
        risk_level="low",
        calibration_confidence=0.88,
        affected_subsystems=["api", "performance"],
        validation_requirements=["latency_benchmark"],
        rollback_expectations=["revert config"],
    )
    proposal1.forecast_summary = "Expected 40% latency reduction"
    proposal1.rationale = "API benchmark shows significant latency improvement potential"
    proposal1.estimated_effort = 20
    
    # Second proposal
    proposal2 = gate.create_proposal(
        title="CDN layer for static assets",
        description="Add CDN for static assets to reduce latency",
        risk_level="medium",
        calibration_confidence=0.72,
        affected_subsystems=["cdn", "assets", "performance"],
        validation_requirements=["cdn_configuration", "fallback_plan"],
        rollback_expectations=["revert dns", "revert cdn config"],
    )
    proposal2.forecast_summary = "Expected 25% latency reduction for static assets"
    proposal2.rationale = "Static assets are 30% of total page load time"
    proposal2.estimated_effort = 50
    
    gate.review_proposal(proposal1.proposal_id, "approve", "operator")
    gate.review_proposal(proposal2.proposal_id, "approve", "operator")
    
    return proposal1, proposal2


def run_governance_chain(proposal, gate: ExecutionGate):
    """Run full governance chain for a proposal."""
    engine = GovernanceAggregationEngine(storage_path=gate.storage_path)
    
    # Governance surface view
    view = engine.get_governance_view(proposal.proposal_id)
    print("=" * 70)
    print("GOVERNANCE SURFACE VIEW:")
    print("=" * 70)
    print(view.format_for_display())
    
    # Governance invocation
    print("\n" + "=" * 70)
    print("GOVERNANCE INVOCATION:")
    print("=" * 70)
    result = invoke_governance_single(proposal.proposal_id, gate.storage_path)
    print(format_invocation_result(result))
    
    # Benchmark recording
    print("\n" + "=" * 70)
    print("BENCHMARK RECORDING:")
    print("=" * 70)
    bench_engine = GovernanceBenchmarkEngine(storage_path=gate.storage_path)
    scorecard = bench_engine.create_scorecard(proposal.proposal_id)
    
    decision = GovernanceDecisionRecord(
        decision_id=f"dec-{proposal.proposal_id[-6:]}",
        decision_type=result["recommended_action"],
        proposal_id=proposal.proposal_id,
        timestamp="2026-04-06T12:30:00Z",
        operator="operator",
        reasoning=result["recommended_action_reason"],
        confidence=result["forecast_confidence"],
        status_at_decision=result["status"],
    )
    scorecard.add_decision(decision)
    
    # Record outcome as success for trial
    bench_engine.set_outcome(proposal.proposal_id, decision.decision_id, "success")
    
    print(f"Recorded decision: {decision.decision_id}")
    print(f"Recommended action: {result['recommended_action']}")
    
    # Get benchmark summary
    summary = engine.get_benchmark_summary(proposal.proposal_id)
    if summary:
        print(f"  Total decisions: {summary['total_decisions']}")
        print(f"  Reliability score: {summary['reliability_score']:.1%}")


def run_comparison_case(proposal1, proposal2, gate: ExecutionGate):
    """Run comparison case."""
    print("=" * 70)
    print("COMPARISON CASE:")
    print("=" * 70)
    
    result = invoke_governance_compare(
        [proposal1.proposal_id, proposal2.proposal_id],
        gate.storage_path,
    )
    print(format_invocation_result(result))


def main():
    """Run the full governance trial pack."""
    print("=" * 70)
    print("V20 — GOVERNANCE TRIAL PACK / REAL PROPOSAL EVALUATION SET")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "proposals.json"
        
        gate = ExecutionGate(storage_path=storage_path)
        
        # Run each case
        print("\n" + "=" * 70)
        print("CASE 1: Quick-Win Proposal")
        print("=" * 70)
        proposal1, expectations1 = create_quick_win_proposal(gate)
        run_governance_chain(proposal1, gate)
        
        print("\n" + "=" * 70)
        print("CASE 2: Medium-Risk Proposal")
        print("=" * 70)
        proposal2, expectations2 = create_medium_risk_proposal(gate)
        run_governance_chain(proposal2, gate)
        
        print("\n" + "=" * 70)
        print("CASE 3: Long-Horizon Strategic Proposal")
        print("=" * 70)
        proposal3, expectations3 = create_long_horizon_proposal(gate)
        run_governance_chain(proposal3, gate)
        
        print("\n" + "=" * 70)
        print("CASE 4: Blocked/Defer Proposal")
        print("=" * 70)
        proposal4, expectations4 = create_blocked_proposal(gate)
        run_governance_chain(proposal4, gate)
        
        print("\n" + "=" * 70)
        print("CASE 5: Direct Comparison")
        print("=" * 70)
        p5a, p5b = create_comparison_pair(gate)
        run_comparison_case(p5a, p5b, gate)
        
        print("\n" + "=" * 70)
        print("TRIAL PACK COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    main()
