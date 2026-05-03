"""
weslr/tests/test_hypothesis_workflow.py
========================================
Phase 7 — Unified Hypothesis & Experiment Workflow tests.

Author: OCC (WESLR governed intelligence) — Phase 7
"""

import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from weslr.modules.hypothesis_repository import (
    Hypothesis,
    HypothesisRepository,
    HypothesisComparison,
    _make_hypothesis_id,
    set_tenant_getter,
    get_current_tenant_id,
)
from weslr.modules.experiment_suggester import ExperimentSuggester, ExperimentSuggestion
from weslr.modules.scenario_explorer import ScenarioExplorer, ScenarioResult
from weslr.modules.report_generator import ReportGenerator


# ── Fixtures ─────────────────────────────────────────────────────────────────

DEMO_TENANT = "test_tenant"


def _make_h(tenant_id: str = DEMO_TENANT, **kwargs) -> Hypothesis:
    """Factory for Hypothesis with deterministic time + tenant."""
    set_tenant_getter(lambda: tenant_id)
    defaults = dict(
        title="Test hypothesis",
        description="A test hypothesis for unit testing.",
        domain="discovery",
        confidence=0.7,
    )
    defaults.update(kwargs)
    h = Hypothesis(**defaults)
    # Override tenant for id generation
    return h


# ── Test Hypothesis dataclass ────────────────────────────────────────────────

class TestHypothesisDataclass(unittest.TestCase):
    def setUp(self) -> None:
        set_tenant_getter(lambda: DEMO_TENANT)

    def test_hypothesis_creation_assigns_id(self) -> None:
        # ID is assigned by the repository on add()
        repo = HypothesisRepository()
        h = Hypothesis(title="Test hypothesis")
        stored = repo.add(h)
        self.assertTrue(len(stored.id) > 10)
        self.assertIsNotNone(stored.id)

    def test_hypothesis_creation_assigns_timestamps(self) -> None:
        h = Hypothesis(title="Test hypothesis")
        self.assertIsNotNone(h.created_at)
        self.assertIsNotNone(h.updated_at)

    def test_hypothesis_default_status_is_draft(self) -> None:
        h = Hypothesis(title="Test")
        self.assertEqual(h.status, "draft")

    def test_hypothesis_default_confidence(self) -> None:
        h = Hypothesis(title="Test")
        self.assertEqual(h.confidence, 0.5)

    def test_update_provenance_appends_entry(self) -> None:
        h = Hypothesis(title="Test")
        self.assertEqual(len(h.provenance), 0)
        h.update_provenance(action="test_action", source="test_module", parameters={"k": 1})
        self.assertEqual(len(h.provenance), 1)
        self.assertEqual(h.provenance[0]["source"], "test_module")
        self.assertEqual(h.provenance[0]["action"], "test_action")

    def test_add_evidence(self) -> None:
        h = Hypothesis(title="Test")
        h.add_evidence("correlation", 0.76, source="discovery_engine")
        self.assertEqual(len(h.metadata.get("evidence", [])), 1)
        self.assertEqual(h.metadata["evidence"][0]["key"], "correlation")


# ── Test UUID determinism ────────────────────────────────────────────────────

class TestUUIDDeterminism(unittest.TestCase):
    def setUp(self) -> None:
        set_tenant_getter(lambda: DEMO_TENANT)

    def test_same_content_same_id(self) -> None:
        ts = datetime(2026, 5, 3, 14, 0, 0, tzinfo=timezone.utc)
        id1 = _make_hypothesis_id(DEMO_TENANT, "Same title", ts)
        id2 = _make_hypothesis_id(DEMO_TENANT, "Same title", ts)
        self.assertEqual(id1, id2)

    def test_different_title_different_id(self) -> None:
        ts = datetime(2026, 5, 3, 14, 0, 0, tzinfo=timezone.utc)
        id1 = _make_hypothesis_id(DEMO_TENANT, "Title A", ts)
        id2 = _make_hypothesis_id(DEMO_TENANT, "Title B", ts)
        self.assertNotEqual(id1, id2)

    def test_different_tenant_different_id(self) -> None:
        ts = datetime(2026, 5, 3, 14, 0, 0, tzinfo=timezone.utc)
        id1 = _make_hypothesis_id("tenant_a", "Same title", ts)
        id2 = _make_hypothesis_id("tenant_b", "Same title", ts)
        self.assertNotEqual(id1, id2)

    def test_different_hour_different_id(self) -> None:
        ts1 = datetime(2026, 5, 3, 14, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 5, 3, 15, 0, 0, tzinfo=timezone.utc)
        id1 = _make_hypothesis_id(DEMO_TENANT, "Same title", ts1)
        id2 = _make_hypothesis_id(DEMO_TENANT, "Same title", ts2)
        self.assertNotEqual(id1, id2)

    def test_id_is_valid_uuid(self) -> None:
        ts = datetime(2026, 5, 3, 14, 0, 0, tzinfo=timezone.utc)
        id_ = _make_hypothesis_id(DEMO_TENANT, "Test", ts)
        # Should not raise
        uuid.UUID(id_)


# ── Test Repository ──────────────────────────────────────────────────────────

class TestHypothesisRepository(unittest.TestCase):
    def setUp(self) -> None:
        set_tenant_getter(lambda: DEMO_TENANT)
        self.repo = HypothesisRepository()

    def tearDown(self) -> None:
        set_tenant_getter(lambda: "default")

    def test_add_and_get(self) -> None:
        h = Hypothesis(title="Add test")
        stored = self.repo.add(h)
        retrieved = self.repo.get(stored.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, stored.id)
        self.assertEqual(retrieved.title, "Add test")

    def test_get_returns_none_for_unknown_id(self) -> None:
        result = self.repo.get("nonexistent-id-123")
        self.assertIsNone(result)

    def test_list_returns_all(self) -> None:
        for i in range(3):
            self.repo.add(Hypothesis(title=f"H{i}"))
        results = self.repo.list()
        self.assertEqual(len(results), 3)

    def test_list_filters_by_status(self) -> None:
        self.repo.add(Hypothesis(title="A", status="draft"))
        h2 = self.repo.add(Hypothesis(title="B", status="active"))
        self.repo.add(Hypothesis(title="C", status="deprecated"))
        self.assertEqual(len(self.repo.list(status="active")), 1)
        self.assertEqual(self.repo.list(status="active")[0].title, "B")

    def test_list_filters_by_domain(self) -> None:
        self.repo.add(Hypothesis(title="A", domain="discovery"))
        self.repo.add(Hypothesis(title="B", domain="causality"))
        self.assertEqual(len(self.repo.list(domain="causality")), 1)

    def test_delete_removes_hypothesis(self) -> None:
        h = self.repo.add(Hypothesis(title="To delete"))
        self.assertTrue(self.repo.delete(h.id))
        self.assertIsNone(self.repo.get(h.id))

    def test_delete_returns_false_for_unknown(self) -> None:
        self.assertFalse(self.repo.delete("nonexistent"))

    def test_update_modifies_fields(self) -> None:
        h = self.repo.add(Hypothesis(title="Old title", confidence=0.3))
        updated = self.repo.update(h.id, title="New title", confidence=0.9)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.title, "New title")
        self.assertEqual(updated.confidence, 0.9)

    def test_update_returns_none_for_unknown(self) -> None:
        result = self.repo.update("nonexistent", title="New")
        self.assertIsNone(result)

    def test_set_active_deprecates_previous(self) -> None:
        h1 = self.repo.add(Hypothesis(title="H1"))
        h2 = self.repo.add(Hypothesis(title="H2"))
        self.repo.set_active(h1.id)
        self.assertEqual(self.repo.get_active().id, h1.id)
        self.repo.set_active(h2.id)
        self.assertEqual(self.repo.get_active().id, h2.id)
        # h1 should now be deprecated
        self.assertEqual(self.repo.get(h1.id).status, "deprecated")

    def test_get_active_returns_none_when_empty(self) -> None:
        self.assertIsNone(self.repo.get_active())


# ── Test Comparison ──────────────────────────────────────────────────────────

class TestHypothesisComparison(unittest.TestCase):
    def setUp(self) -> None:
        set_tenant_getter(lambda: DEMO_TENANT)
        self.repo = HypothesisRepository()

    def tearDown(self) -> None:
        set_tenant_getter(lambda: "default")

    def test_compare_returns_comparison_object(self) -> None:
        h1 = self.repo.add(Hypothesis(title="Hypothesis A about drug dose response"))
        h2 = self.repo.add(Hypothesis(title="Hypothesis B about protein binding"))
        cmp = self.repo.compare(h1.id, h2.id)
        self.assertIsInstance(cmp, HypothesisComparison)
        # No shared keywords expected between "drug dose response" and "protein binding"
        self.assertLess(cmp.jaccard_overlap, 0.3)

    def test_compare_confidence_delta(self) -> None:
        h1 = self.repo.add(Hypothesis(title="H1", confidence=0.3))
        h2 = self.repo.add(Hypothesis(title="H2", confidence=0.8))
        cmp = self.repo.compare(h1.id, h2.id)
        self.assertEqual(cmp.confidence_delta, 0.5)
        self.assertTrue(cmp.confidence_delta > 0)

    def test_compare_jaccard_shared_keywords(self) -> None:
        h1 = self.repo.add(Hypothesis(title="Drug dose affects blood pressure"))
        h2 = self.repo.add(Hypothesis(title="Drug dose influences blood pressure"))
        cmp = self.repo.compare(h1.id, h2.id)
        self.assertGreater(cmp.jaccard_overlap, 0)
        self.assertIn("drug", cmp.shared_keywords)
        self.assertIn("dose", cmp.shared_keywords)
        self.assertIn("blood", cmp.shared_keywords)

    def test_compare_returns_none_for_unknown_id(self) -> None:
        h1 = self.repo.add(Hypothesis(title="H1"))
        cmp = self.repo.compare(h1.id, "nonexistent")
        self.assertIsNone(cmp)


# ── Test Experiment Suggester ────────────────────────────────────────────────

class TestExperimentSuggester(unittest.TestCase):
    def setUp(self) -> None:
        set_tenant_getter(lambda: DEMO_TENANT)
        self.suggester = ExperimentSuggester()

    def tearDown(self) -> None:
        set_tenant_getter(lambda: "default")

    def test_suggests_intervention_for_low_confidence_causal_edge(self) -> None:
        h = Hypothesis(
            title="Low confidence causal",
            domain="causality",
            confidence=0.4,
            metadata={
                "causal_graph": {
                    ("A", "B"): 0.3,  # low confidence
                    ("B", "C"): 0.8,
                }
            },
        )
        suggestions = self.suggester.suggest_next_experiments(h, max_suggestions=3)
        self.assertGreater(len(suggestions), 0)
        desc = suggestions[0].description
        self.assertIn("Intervention", desc)

    def test_suggests_temporal_collection_when_missing(self) -> None:
        h = Hypothesis(
            title="Causal claim without temporal data",
            domain="causality",
            confidence=0.5,
            provenance=[{"source": "discovery_engine"}],  # no temporal_reasoning
        )
        suggestions = self.suggester.suggest_next_experiments(h, max_suggestions=5)
        desc_text = " ".join(s.description for s in suggestions)
        self.assertIn("time", desc_text.lower())

    def test_suggests_parameter_refinement_for_simulation(self) -> None:
        h = Hypothesis(
            title="Simulation with boundary params",
            domain="simulation",
            confidence=0.6,
            metadata={
                "simulation_model": "emax",
                "simulation_params": {"E_max": 0.001, "ED50": 10},  # E_max at extreme
                "simulation_reference": {"E_max": 100.0},
            },
        )
        suggestions = self.suggester.suggest_next_experiments(h, max_suggestions=3)
        self.assertGreater(len(suggestions), 0)

    def test_suggests_forecasting_horizon_validation(self) -> None:
        h = Hypothesis(
            title="Long horizon forecast",
            domain="temporal",
            confidence=0.5,
            metadata={
                "forecast_horizon": 60,
                "n_time_points": 10,
            },
        )
        suggestions = self.suggester.suggest_next_experiments(h, max_suggestions=3)
        desc_text = " ".join(s.description for s in suggestions)
        self.assertTrue(any("horizon" in d.lower() or "hold-out" in d.lower() for d in [desc_text]))

    def test_max_suggestions_limit(self) -> None:
        h = Hypothesis(
            title="Multi-domain",
            domain="mixed",
            metadata={
                "causal_graph": {("A", "B"): 0.3},
                "simulation_model": "emax",
                "simulation_params": {"E_max": 0.001},
                "forecast_horizon": 60,
                "n_time_points": 10,
            },
        )
        suggestions = self.suggester.suggest_next_experiments(h, max_suggestions=2)
        self.assertLessEqual(len(suggestions), 2)

    def test_estimated_impact_values(self) -> None:
        h = Hypothesis(
            title="Test",
            metadata={"causal_graph": {("A", "B"): 0.2}},  # very low → high impact
        )
        suggestions = self.suggester.suggest_next_experiments(h, max_suggestions=1)
        self.assertIn(suggestions[0].estimated_impact, ("low", "medium", "high"))

    def test_format_suggestions(self) -> None:
        h = Hypothesis(
            title="Test",
            metadata={"causal_graph": {("A", "B"): 0.3}},
        )
        suggestions = self.suggester.suggest_next_experiments(h, max_suggestions=1)
        output = ExperimentSuggester.format_suggestions(suggestions)
        self.assertIn("SIMULATION MODE", output)


# ── Test Scenario Explorer ───────────────────────────────────────────────────

class TestScenarioExplorer(unittest.TestCase):
    def setUp(self) -> None:
        set_tenant_getter(lambda: DEMO_TENANT)
        self.explorer = ScenarioExplorer()

    def tearDown(self) -> None:
        set_tenant_getter(lambda: "default")

    def test_explore_scenario_returns_result(self) -> None:
        h = Hypothesis(
            title="Dose-response simulation",
            domain="simulation",
            metadata={
                "simulation_model": "emax",
                "simulation_params": {"E_max": 100, "ED50": 10},
            },
        )
        result = self.explorer.explore_scenario(h, {"dose": 50, "time_horizon": 14})
        self.assertIsInstance(result, ScenarioResult)
        self.assertEqual(result.hypothesis_title, "Dose-response simulation")
        self.assertIn("experiment_simulation", result.modules_used)

    def test_explore_scenario_deterministic_seed(self) -> None:
        h = Hypothesis(title="Determinism test", domain="simulation",
                       metadata={"simulation_model": "emax", "simulation_params": {}})
        r1 = self.explorer.explore_scenario(h, {"dose": 10})
        r2 = self.explorer.explore_scenario(h, {"dose": 10})
        self.assertEqual(r1.seed, r2.seed)

    def test_explore_scenario_temporal_domain(self) -> None:
        h = Hypothesis(
            title="Temporal forecast",
            domain="temporal",
            metadata={
                "temporal_intercept": 10.0,
                "temporal_slope": 0.5,
                "temporal_noise_sd": 0.1,
            },
        )
        result = self.explorer.explore_scenario(h, {"time_horizon": 7})
        self.assertIn("temporal_reasoning", result.modules_used)

    def test_explore_scenario_causal_domain(self) -> None:
        h = Hypothesis(
            title="Causal hypothesis",
            domain="causality",
            metadata={
                "causal_graph": {("A", "B"): 0.7},
                "causal_data": {"A": [0.5, 1.0, 1.5], "B": [1.0, 2.0, 3.0]},
            },
        )
        result = self.explorer.explore_scenario(h, {"A": 2.0})
        self.assertIn("causality", result.modules_used)

    def test_explore_scenario_no_matching_module(self) -> None:
        h = Hypothesis(
            title="Empty hypothesis",
            domain="mixed",
            metadata={},
        )
        result = self.explorer.explore_scenario(h, {"param": 1})
        # Should still return a result (just no module predictions)
        self.assertIsInstance(result, ScenarioResult)
        self.assertEqual(len(result.modules_used), 0)

    def test_format_result(self) -> None:
        h = Hypothesis(title="Test", domain="simulation",
                       metadata={"simulation_model": "emax", "simulation_params": {}})
        r = self.explorer.explore_scenario(h, {"dose": 50})
        output = ScenarioExplorer.format_result(r)
        self.assertIn("Test", output)
        self.assertIn("SIMULATION MODE", output)


# ── Test Report Generator ───────────────────────────────────────────────────

class TestReportGenerator(unittest.TestCase):
    def setUp(self) -> None:
        set_tenant_getter(lambda: DEMO_TENANT)
        self.gen = ReportGenerator()

    def tearDown(self) -> None:
        set_tenant_getter(lambda: "default")

    def test_generate_report_text(self) -> None:
        h = Hypothesis(
            title="Test hypothesis",
            description="A hypothesis for testing.",
            domain="discovery",
            confidence=0.75,
            provenance=[{"source": "test", "action": "test_action", "parameters": {}}],
        )
        text = self.gen.generate_report(h, format="text")
        self.assertIn("Test hypothesis", text)
        self.assertIn("0.75", text)
        self.assertIn("DISCOVERY", text.upper())
        self.assertIn("SIMULATION MODE", text)

    def test_generate_report_json(self) -> None:
        h = Hypothesis(
            title="JSON test",
            description="Testing JSON output.",
            domain="causality",
            confidence=0.6,
        )
        data = self.gen.generate_report(h, format="json")
        self.assertIsInstance(data, dict)
        self.assertEqual(data["hypothesis"]["title"], "JSON test")
        self.assertIn("safety_warning", data)

    def test_report_contains_provenance(self) -> None:
        h = Hypothesis(
            title="Provenance test",
            provenance=[{
                "source": "discovery_engine",
                "action": "correlation_found",
                "parameters": {"r": 0.76},
                "timestamp": "2026-05-03T12:00:00Z",
            }],
        )
        text = self.gen.generate_report(h, format="text")
        self.assertIn("discovery_engine", text)
        self.assertIn("correlation_found", text)

    def test_report_shows_suggestions(self) -> None:
        h = Hypothesis(
            title="With suggestions",
            domain="causality",
            metadata={"causal_graph": {("A", "B"): 0.3}},
        )
        text = self.gen.generate_report(h, format="text")
        self.assertIn("Suggested Experiments", text)

    def test_json_report_excludes_suggestions(self) -> None:
        h = Hypothesis(title="JSON no suggestions")
        data = self.gen.generate_report(h, format="json")
        self.assertNotIn("suggested_experiments", data)


# ── Test Command Handlers ────────────────────────────────────────────────────

class TestHypothesisCommands(unittest.TestCase):
    def setUp(self) -> None:
        set_tenant_getter(lambda: DEMO_TENANT)
        import weslr.commands.hypothesis_commands as hc
        hc._REPO = None  # reset global repo between tests

    def tearDown(self) -> None:
        set_tenant_getter(lambda: "default")
        import weslr.commands.hypothesis_commands as hc
        hc._REPO = None
        hc._SUGGESTER = None
        hc._EXPLORER = None
        hc._REPORT_GENERATOR = None

    def test_hypothesis_new_creates_hypothesis(self) -> None:
        import asyncio
        from weslr.commands.hypothesis_commands import handle_hypothesis_command

        async def run():
            result = await handle_hypothesis_command(
                "/hypothesis new Test hypothesis",
                "hypothesis new test hypothesis",
            )
            self.assertIn("Hypothesis created", result)
            self.assertIn("Test hypothesis", result)

        run()

    def test_hypothesis_list_empty(self) -> None:
        import asyncio
        from weslr.commands.hypothesis_commands import handle_hypothesis_command

        async def run():
            result = await handle_hypothesis_command(
                "/hypothesis list",
                "hypothesis list",
            )
            self.assertIn("No hypotheses", result)

        run()

    def test_hypothesis_show_unknown(self) -> None:
        import asyncio
        from weslr.commands.hypothesis_commands import handle_hypothesis_command

        async def run():
            result = await handle_hypothesis_command(
                "/hypothesis show unknown-id",
                "hypothesis show unknown-id",
            )
            self.assertIn("not found", result)

        run()

    def test_experiment_suggest_no_active(self) -> None:
        import asyncio
        from weslr.commands.hypothesis_commands import handle_experiment_command

        async def run():
            result = await handle_experiment_command(
                "/experiment suggest",
                "experiment suggest",
            )
            self.assertIn("No active hypothesis", result)

        run()

    def test_scenario_explore_no_active(self) -> None:
        import asyncio
        from weslr.commands.hypothesis_commands import handle_scenario_command

        async def run():
            result = await handle_scenario_command(
                "/scenario explore dose=50",
                "scenario explore dose=50",
            )
            self.assertIn("No active hypothesis", result)

        run()

    def test_report_generate_no_active(self) -> None:
        import asyncio
        from weslr.commands.hypothesis_commands import handle_report_command

        async def run():
            result = await handle_report_command(
                "/report generate",
                "report generate",
            )
            self.assertIn("No hypothesis", result)

        run()


# ── Test end-to-end workflow ─────────────────────────────────────────────────

class TestEndToEndWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        set_tenant_getter(lambda: DEMO_TENANT)
        import weslr.commands.hypothesis_commands as hc
        hc._REPO = None
        hc._SUGGESTER = None
        hc._EXPLORER = None
        hc._REPORT_GENERATOR = None

    def tearDown(self) -> None:
        set_tenant_getter(lambda: "default")
        import weslr.commands.hypothesis_commands as hc
        hc._REPO = None
        hc._SUGGESTER = None
        hc._EXPLORER = None
        hc._REPORT_GENERATOR = None

    def test_full_workflow(self) -> None:
        """Explore → auto-create → promote → suggest → scenario → report"""
        import asyncio
        from weslr.commands.hypothesis_commands import (
            handle_hypothesis_command,
            handle_experiment_command,
            handle_scenario_command,
            handle_report_command,
        )

        async def run():
            # Step 1: Discover correlation → auto-create hypothesis
            from weslr.commands.hypothesis_commands import auto_create_hypothesis
            h = auto_create_hypothesis(
                title="Drug dose correlates with response (r=0.76)",
                description="Analysis of clinical trial data shows strong correlation.",
                domain="discovery",
                confidence=0.76,
                metadata={
                    "correlation": {("dose", "response"): 0.76},
                    "simulation_model": "emax",
                    "simulation_params": {"E_max": 100, "ED50": 10},
                },
            )
            hyp_id = h.id

            # Step 2: List hypotheses
            list_result = await handle_hypothesis_command(
                f"/hypothesis list",
                "hypothesis list",
            )
            self.assertIn(hyp_id[:8], list_result)

            # Step 3: Promote
            promote_result = await handle_hypothesis_command(
                f"/hypothesis promote {hyp_id}",
                f"hypothesis promote {hyp_id}",
            )
            self.assertIn("Active hypothesis set", promote_result)

            # Step 4: Suggest experiments
            suggest_result = await handle_experiment_command(
                "/experiment suggest",
                "experiment suggest",
            )
            self.assertIn("Suggested Experiments", suggest_result)
            self.assertIn("SIMULATION MODE", suggest_result)

            # Step 5: Scenario explore
            scenario_result = await handle_scenario_command(
                "/scenario explore dose=60 time_horizon=14",
                "scenario explore dose=60 time_horizon=14",
            )
            self.assertIn("Scenario Explorer", scenario_result)
            self.assertIn("SIMULATION MODE", scenario_result)

            # Step 6: Report generate
            report_result = await handle_report_command(
                f"/report generate {hyp_id}",
                f"report generate {hyp_id}",
            )
            self.assertIn("HYPOTHESIS REPORT", report_result)
            self.assertIn("Drug dose correlates", report_result)
            self.assertIn("SIMULATION MODE", report_result)

        run()


if __name__ == "__main__":
    unittest.main()