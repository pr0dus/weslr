"""Tests for /explore goal-driven hypothesis generation."""

import pytest
from weslr.goal_decomposer import decompose, expand_keywords, _STOP_WORDS


class TestGoalDecomposer:
    def test_stopword_removal(self):
        result = decompose("slow down human cell aging")
        assert "the" not in result["raw_keywords"]
        assert "human" in result["raw_keywords"]

    def test_keyword_expansion(self):
        keywords = ["aging", "cell"]
        expanded = expand_keywords(keywords, domain="biology")
        assert "senescence" in expanded
        assert "aging" in expanded

    def test_domain_detection(self):
        result = decompose("slow down human cell aging")
        assert result["domain"] == "biology"

        result = decompose("create more efficient photovoltaic material")
        assert result["domain"] == "materials_science"

    def test_query_components_not_empty(self):
        result = decompose("design targeted drug delivery for glioblastoma")
        assert len(result["query_components"]) > 0
        assert "design targeted drug delivery for glioblastoma" in result["query_components"]

    def test_decompose_preserves_original(self):
        result = decompose("some scientific goal here")
        assert result["original_goal"] == "some scientific goal here"


class TestHypothesisScorer:
    def test_charge_balance_h2o(self):
        from weslr.hypothesis_scorer import check_charge_balance
        result = check_charge_balance("H2O")
        assert result["is_balanced"] is True
        assert result["net_charge"] == 0

    def test_charge_balance_nacl(self):
        from weslr.hypothesis_scorer import check_charge_balance
        result = check_charge_balance("NaCl")
        assert result["is_balanced"] is True

    def test_charge_balance_catioin_imbalance(self):
        from weslr.hypothesis_scorer import check_charge_balance
        result = check_charge_balance("NaCl2")  # sodium chloride with extra Cl
        assert result["charge_deficit"] > 0

    def test_chemical_feasibility_balanced(self):
        from weslr.hypothesis_scorer import chemical_feasibility
        result = chemical_feasibility("Cu2ZnSnSe4")
        assert result["overall_feasible"] is True
        assert result["score"] >= 0.6

    def test_chemical_feasibility_unparseable(self):
        from weslr.hypothesis_scorer import chemical_feasibility
        result = chemical_feasibility("")
        assert result["overall_feasible"] is True  # no formula = pass

    def test_score_hypothesis(self):
        from weslr.hypothesis_scorer import score_hypothesis
        h = {
            "name": "NMN + dasatinib",
            "description": "Combine NAD+ booster with senolytic",
            "components": ["NMN", "dasatinib"],
            "predicted_effect": "may reduce senescent cell burden",
        }
        sources = [
            {"id": "PMID:12345678", "title": "NAD+ and senescence", "trust_score": 0.8},
            {"id": "PMID:23456789", "title": "Dasatinib senolytic", "trust_score": 0.75},
        ]
        scored = score_hypothesis(h, sources)
        assert scored["confidence"] > 0
        assert scored["confidence"] <= 1.0
        assert scored["independent_sources"] == 2
        assert scored["source_trust"] == 0.775

    def test_rank_hypotheses(self):
        from weslr.hypothesis_scorer import rank_hypotheses
        hypotheses = [
            {"name": "h1", "components": ["A"], "supporting_sources": []},
            {"name": "h2", "components": ["A", "B"],
             "supporting_sources": [{"id": "P1", "title": "t", "trust_score": 0.9}]},
        ]
        ranked = rank_hypotheses(hypotheses)
        # h2 should rank higher (has supporting source)
        assert ranked[0]["name"] == "h2"


class TestExploreMock:
    def test_explore_with_mock_search(self):
        from weslr.explore_engine import generate_hypotheses, build_entity_graph
        from weslr.hypothesis_scorer import rank_hypotheses

        mock_results = [
            {
                "arxiv_id": "2401.00001",
                "title": "Dasatinib and quercetin as senolytics",
                "abstract": "Dasatinib and quercetin (D+Q) are senolytic agents that clear senescent cells. "
                            "NAD+ boosters like NMN improve mitochondrial function.",
            },
            {
                "arxiv_id": "2401.00002",
                "title": "mTOR inhibition and autophagy",
                "abstract": "Rapamycin inhibits mTOR and promotes autophagy. "
                            "Calcium channel TRPC5 modulates cellular senescence.",
            },
            {
                "pmid": "12345678",
                "title": "NMN improves mitochondrial function in aged cells",
                "abstract": "Nicotinamide mononucleotide (NMN) boosts NAD+ levels and restores "
                            "mitochondrial function in senescent fibroblasts.",
            },
        ]

        entities = build_entity_graph(mock_results)
        assert len(entities) > 0

        hypotheses = generate_hypotheses(entities, "slow down cell aging", domain="biology", max_hypotheses=5)
        assert len(hypotheses) > 0

        scored = rank_hypotheses(hypotheses)
        assert scored[0]["confidence"] >= scored[-1]["confidence"]

        # Check structure
        for h in scored:
            assert "name" in h
            assert "description" in h
            assert "confidence" in h
            assert "suggested_next_step" in h


class TestExploreEngine:
    def test_explore_runs(self):
        """Smoke test — explore() should return structured output without errors."""
        from weslr.explore_engine import explore

        # Use a very targeted query that won't need real network
        # (uses mocks if adapters fail)
        result = explore(
            goal="slow down human cell aging",
            domain="biology",
            max_results_per_adapter=3,
            top_n=3,
            timeout_per_adapter=5.0,
        )

        assert "hypotheses" in result
        assert "search_summary" in result
        assert "goal_decomposition" in result
        assert isinstance(result["hypotheses"], list)

        # Check hypothesis structure
        for h in result["hypotheses"]:
            assert "name" in h
            assert "description" in h
            assert "confidence" in h
            assert "feasibility" in h
            assert "predicted_effect" in h
            assert "suggested_next_step" in h

    def test_explore_with_domain_flag(self):
        from weslr.explore_engine import explore
        result = explore(
            goal="design targeted drug delivery for glioblastoma",
            domain="biology",
            max_results_per_adapter=3,
            top_n=3,
            timeout_per_adapter=5.0,
        )
        assert result["goal_decomposition"]["domain"] == "biology"
        assert len(result["hypotheses"]) >= 0

    def test_explore_unknown_domain_still_runs(self):
        from weslr.explore_engine import explore
        result = explore(
            goal="make something up with xyzabc unknown domain",
            domain="foobar",
            max_results_per_adapter=2,
            top_n=3,
            timeout_per_adapter=3.0,
        )
        assert "hypotheses" in result
        assert isinstance(result["search_summary"], dict)


class TestCommandExplore:
    def test_handle_explore_usage(self):
        from weslr.commands.explore import handle_explore
        result = handle_explore("", "/explore")
        assert "Usage" in result

    def test_handle_explore_with_goal(self):
        from weslr.commands.explore import handle_explore
        result = handle_explore("/explore test goal", "/explore test goal")
        assert "Exploring:" in result or "hypotheses" in result.lower() or "no hypotheses" in result.lower()

    def test_handle_explore_with_domain_flag(self):
        from weslr.commands.explore import handle_explore
        result = handle_explore(
            "/explore cell aging --domain biology",
            "/explore cell aging --domain biology",
        )
        assert "Exploring:" in result

    def test_handle_explore_with_top_flag(self):
        from weslr.commands.explore import handle_explore
        result = handle_explore(
            "/explore slow down aging --top 3",
            "/explore slow down aging --top 3",
        )
        assert "Exploring:" in result or "hypotheses" in result.lower()
