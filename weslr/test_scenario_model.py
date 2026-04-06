# test_scenario_model.py - Tests for Self-Architecture Core v6: Scenario Comparison Layer
# Scenario creation, comparison, and tradeoff reasoning.

from __future__ import annotations

import unittest
from scenario_model import (
    Scenario,
    ScenarioProposal,
    ScenarioScore,
    RoadmapTradeoffEngine,
    create_scenario,
    create_quick_win_scenario,
    create_strategic_scenario,
    StrategicHorizon,
    TradeoffSummary,
)


class TestScenarioCreation(unittest.TestCase):
    """Test scenario creation and basic properties."""
    
    def test_create_basic_scenario(self):
        """Can create a basic scenario."""
        proposal = ScenarioProposal(
            id="p1",
            title="Add logging",
            description="Add structured logging to state module",
            affected_subsystems=["state"],
        )
        scenario = create_scenario(
            title="Logging Foundation",
            description="Improve observability",
            proposals=[proposal],
        )
        
        self.assertEqual(scenario.title, "Logging Foundation")
        self.assertEqual(len(scenario.proposals), 1)
        self.assertEqual(scenario.proposals[0].title, "Add logging")
    
    def test_add_proposal(self):
        """Can add proposals to an existing scenario."""
        scenario = create_scenario(
            title="Test Scenario",
            description="For testing",
        )
        
        proposal1 = ScenarioProposal(
            id="p1",
            title="First change",
            description="First",
            effort=3.0,
            risk=2.0,
        )
        proposal2 = ScenarioProposal(
            id="p2",
            title="Second change",
            description="Second",
            effort=4.0,
            risk=3.0,
        )
        
        scenario.add_proposal(proposal1)
        scenario.add_proposal(proposal2)
        
        self.assertEqual(len(scenario.proposals), 2)
        # Default effort is 5.0, plus 50% of proposal effort/risk
        self.assertAlmostEqual(scenario.effort, 8.5, places=1)  # 5 + 1.5 + 2.0
        self.assertAlmostEqual(scenario.risk, 7.5, places=1)    # 5 + 1.0 + 1.5
    
    def test_scoring_computation(self):
        """Scenario scores are computed correctly."""
        scenario = create_scenario(
            title="Score Test",
            description="Testing scores",
        )
        scenario.effort = 5.0
        scenario.risk = 4.0
        scenario.fitness_gains = 6.0
        scenario.strategic_value = 7.0
        scenario.quick_win_score = 5.0
        scenario.coherence_score = 6.0
        
        score = scenario.compute_scores()
        
        self.assertEqual(score.effort, 5.0)
        self.assertEqual(score.risk, 4.0)
        self.assertEqual(score.fitness_gains, 6.0)  # base + proposals impact
        self.assertEqual(score.strategic_value, 7.0)
        self.assertEqual(score.quick_win_score, 5.0)
        self.assertEqual(score.coherence_score, 6.0)


class TestScenarioComparison(unittest.TestCase):
    """Test scenario-to-scenario comparison."""
    
    def test_compare_scenarios_quick_win_vs_strategic(self):
        """Can compare quick-win vs strategic scenarios."""
        # Quick-win scenario
        qwp1 = ScenarioProposal(
            id="qwp1",
            title="Fix typo in docs",
            description="Fix a typo in README",
            quick_win=True,
            effort=1.0,
            risk=0.5,
        )
        quick_win = create_quick_win_scenario(
            title="Quick Win",
            description="One small fix",
            proposals=[qwp1],
        )
        
        # Strategic scenario
        sp1 = ScenarioProposal(
            id="sp1",
            title="Architectural refactor",
            description="Major refactoring",
            strategic=True,
            effort=8.0,
            risk=7.0,
        )
        strategic = create_strategic_scenario(
            title="Strategic",
            description="Big picture change",
            proposals=[sp1],
        )
        
        # Compare
        result = RoadmapTradeoffEngine.compare_scenarios(quick_win, strategic)
        
        self.assertEqual(result.better_scenario, "scenario_a")  # Quick win wins on effort/risk
        self.assertTrue(result.quick_win_interpretation)
        self.assertFalse(result.strategic_interpretation)
        self.assertIn("effort", " ".join(result.tradeoffs))
    
    def test_compare_scenarios_equal_risk_different_strategic_value(self):
        """Comparison works when risk is equal but strategic value differs."""
        # Scenario A: higher strategic value
        a1 = ScenarioProposal(
            id="a1",
            title="A change",
            description="A",
            strategic=True,
        )
        scenario_a = create_scenario("A", "A desc", [a1])
        scenario_a.strategic_value = 8.0
        
        # Scenario B: lower strategic value
        b1 = ScenarioProposal(
            id="b1",
            title="B change",
            description="B",
        )
        scenario_b = create_scenario("B", "B desc", [b1])
        scenario_b.strategic_value = 5.0
        
        # Same effort and risk
        scenario_a.effort = 5.0
        scenario_b.effort = 5.0
        scenario_a.risk = 5.0
        scenario_b.risk = 5.0
        
        result = RoadmapTradeoffEngine.compare_scenarios(scenario_a, scenario_b)
        
        # Strategy wins when effort/risk are equal
        self.assertEqual(result.better_scenario, "scenario_a")
        self.assertTrue(result.strategic_interpretation)
    
    def test_compare_scenarios_coherence_matters(self):
        """Coherence scoring affects comparison."""
        # Scenario A: coherent bundle
        a1 = ScenarioProposal(
            id="a1",
            title="Refactor state",
            description="State refactoring",
            affected_subsystems=["state"],
        )
        a2 = ScenarioProposal(
            id="a2",
            title="Update continuity",
            description="Update continuity",
            affected_subsystems=["continuity"],
        )
        scenario_a = create_scenario("A", "A", [a1, a2])
        scenario_a.coherence_score = 8.0  # Bundle together
        scenario_a.effort = 6.0
        scenario_a.risk = 5.0
        
        # Scenario B: scattered changes
        b1 = ScenarioProposal(
            id="b1",
            title="Random change",
            description="B",
            affected_subsystems=["other"],
        )
        scenario_b = create_scenario("B", "B", [b1])
        scenario_b.coherence_score = 3.0
        scenario_b.effort = 5.0
        scenario_b.risk = 4.0
        
        result = RoadmapTradeoffEngine.compare_scenarios(scenario_a, scenario_b)
        
        # Coherence should help scenario A - check tradeoff mentions coherence
        tradeoff_str = " ".join(result.tradeoffs).lower()
        self.assertIn("coherence", tradeoff_str)


class TestTradeoffSummary(unittest.TestCase):
    """Test tradeoff summary output."""
    
    def test_tradeoff_summary_structure(self):
        """Tradeoff summary has expected fields."""
        summary = TradeoffSummary(
            better_scenario="scenario_a",
            tradeoffs=["effort: A better", "risk: A better"],
            rationale="A wins on most criteria",
            timing_recommendation="Immediate execution",
            quick_win_interpretation=True,
            strategic_interpretation=False,
        )
        
        dict_rep = summary.to_dict()
        
        self.assertEqual(dict_rep["better_scenario"], "scenario_a")
        self.assertEqual(len(dict_rep["tradeoffs"]), 2)
        self.assertTrue(dict_rep["quick_win_interpretation"])
        self.assertFalse(dict_rep["strategic_interpretation"])
    
    def test_from_dict_roundtrip(self):
        """Can serialize and deserialize tradeoff summary."""
        summary = TradeoffSummary(
            better_scenario="scenario_b",
            tradeoffs=["effort: B better"],
            rationale="B is better",
            timing_recommendation="Phased rollout",
        )
        
        dict_rep = summary.to_dict()
        restored = TradeoffSummary.from_dict(dict_rep)
        
        self.assertEqual(restored.better_scenario, "scenario_b")
        self.assertEqual(len(restored.tradeoffs), 1)


class TestSequencing(unittest.TestCase):
    """Test sequencing recommendations."""
    
    def test_recommend_sequencing_by_quick_win(self):
        """Sequencing prefers quick wins."""
        scenario_1 = create_scenario("1", "Fast", [])
        scenario_1.effort = 2.0
        scenario_1.risk = 2.0
        scenario_1.quick_win_score = 8.0
        
        scenario_2 = create_scenario("2", "Slow", [])
        scenario_2.effort = 8.0
        scenario_2.risk = 7.0
        scenario_2.quick_win_score = 3.0
        
        scenario_3 = create_scenario("3", "Medium", [])
        scenario_3.effort = 5.0
        scenario_3.risk = 5.0
        scenario_3.quick_win_score = 6.0
        
        ordered = RoadmapTradeoffEngine.recommend_sequencing([scenario_1, scenario_2, scenario_3])
        
        # Quick win first, then by risk
        self.assertEqual(ordered[0], scenario_1.id)
    
    def test_sequencing_handles_equal_quick_wins(self):
        """When quick wins equal, lower risk wins."""
        # Same quick win, different risk
        s1 = create_scenario("s1", "Low risk", [])
        s1.quick_win_score = 7.0
        s1.risk = 2.0
        
        s2 = create_scenario("s2", "High risk", [])
        s2.quick_win_score = 7.0
        s2.risk = 6.0
        
        s3 = create_scenario("s3", "Med risk", [])
        s3.quick_win_score = 7.0
        s3.risk = 4.0
        
        ordered = RoadmapTradeoffEngine.recommend_sequencing([s3, s1, s2])
        
        # s1 (low risk) should come first
        self.assertEqual(ordered[0], s1.id)


class TestFactoryFunctions(unittest.TestCase):
    """Test scenario factory functions."""
    
    def test_create_quick_win_scenario(self):
        """Quick win scenario sets correct defaults."""
        proposal = ScenarioProposal(
            id="qwp1",
            title="Quick fix",
            description="Quick",
            quick_win=True,
        )
        scenario = create_quick_win_scenario(
            title="Quick Win",
            description="For testing",
            proposals=[proposal],
        )
        
        self.assertEqual(scenario.strategic_horizon, StrategicHorizon.IMMEDIATE.value)
        self.assertEqual(scenario.quick_win_score, 8.0)
    
    def test_create_strategic_scenario(self):
        """Strategic scenario sets correct defaults."""
        proposal = ScenarioProposal(
            id="sp1",
            title="Strategic change",
            description="Strategic",
            strategic=True,
        )
        scenario = create_strategic_scenario(
            title="Strategic",
            description="For testing",
            proposals=[proposal],
        )
        
        self.assertEqual(scenario.strategic_horizon, StrategicHorizon.LONG_TERM.value)
        self.assertEqual(scenario.strategic_value, 8.0)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that scenario model works with existing suggestion structures."""
    
    def test_scenario_with_no_proposals(self):
        """Scenario can exist without proposals (edge case)."""
        scenario = create_scenario(
            title="Empty",
            description="No proposals yet",
        )
        
        self.assertEqual(len(scenario.proposals), 0)
        self.assertEqual(scenario.effort, 5.0)
        self.assertEqual(scenario.risk, 5.0)
    
    def test_scenario_from_dict_compatibility(self):
        """Can create scenario from dict (e.g., stored JSON)."""
        data = {
            "id": "abc123",
            "title": "Test from dict",
            "description": "Loaded from dict",
            "proposals": [],
            "effort": 4.0,
            "risk": 3.0,
            "fitness_gains": 5.0,
            "strategic_value": 6.0,
            "quick_win_score": 4.0,
            "coherence_score": 5.0,
            "strategic_horizon": "short_term",
            "sequencing_assumptions": ["Assumption 1"],
            "rationale": "Because",
            "author": "operator",
        }
        
        scenario = Scenario.from_dict(data)
        
        self.assertEqual(scenario.id, "abc123")
        self.assertEqual(len(scenario.sequencing_assumptions), 1)
        self.assertEqual(scenario.rationale, "Because")


if __name__ == "__main__":
    unittest.main()
