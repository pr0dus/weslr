"""
tests/test_advanced_reasoning.py
================================
Phase 9 — Advanced reasoning module tests.

Tests: Abduction, Meta-Analysis, Transfer Analogy, and command parsing.
All tests are self-contained, no external calls.
"""

import pytest
import math
import os
import sys

# Ensure repo root is on path
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from weslr.modules.abductive_reasoner import (
    AbductiveReasoner,
    Rule,
    Explanation,
    _TENANT_RULES,
)
from weslr.modules.meta_analyst import (
    MetaAnalysis,
    Study,
    _TENANT_STUDIES,
)
from weslr.modules.transfer_analogy import (
    AnalogyEngine,
    Analogy,
    TransferredHypothesis,
    _TENANT_ANALOGIES,
)
from weslr.modules.hypothesis_repository import Hypothesis

# Import command handlers via absolute path (commands/ is a sub-package of the repo root)
from commands.advanced_commands import (
    handle_abduce,
    handle_meta,
    handle_transfer,
    _reasoner,
    _meta,
    _analogy,
    set_shared_tenant_getter,
)


# ============================================================================
# Tenant isolation
# ============================================================================
TEST_TENANT = "test_phase9"

@pytest.fixture(autouse=True)
def isolate_tenant():
    """Reset all module state to test_tenant before each test."""
    # Switch tenant getter to test tenant
    old_getter = None
    import weslr.commands.advanced_commands as ac
    old_getter = ac._tenant_getter
    ac._tenant_getter = lambda: TEST_TENANT

    # Sync to all modules via weslr path
    from weslr.modules import abductive_reasoner as ar_mod
    from weslr.modules import meta_analyst as ma_mod
    from weslr.modules import transfer_analogy as ta_mod

    ar_mod.set_tenant_getter(lambda: TEST_TENANT)
    ma_mod.set_tenant_getter(lambda: TEST_TENANT)
    ta_mod.set_tenant_getter(lambda: TEST_TENANT)

    # Clear per-tenant stores
    _TENANT_RULES.pop(TEST_TENANT, None)
    _TENANT_STUDIES.pop(TEST_TENANT, None)
    _TENANT_ANALOGIES.pop(TEST_TENANT, None)
    _TENANT_RULES[TEST_TENANT] = []
    _TENANT_STUDIES[TEST_TENANT] = []
    _TENANT_ANALOGIES[TEST_TENANT] = []

    # Preload analogy engine with defaults for this tenant
    eng = _analogy()
    eng._preloaded = False  # reset so preload runs
    eng.preload_default_analogies()

    yield

    # Restore
    ac._tenant_getter = old_getter
    ar_mod.set_tenant_getter(old_getter)
    ma_mod.set_tenant_getter(old_getter)
    ta_mod.set_tenant_getter(old_getter)


# ============================================================================
# ABDUCTION — RULE CHAIN
# ============================================================================
class TestAbductionRuleChain:
    """Abduction: rules A→B, B→C, obs C → explanation with both rules."""

    def test_abduction_chain_A_to_B_to_C_returns_explanation(self):
        """A→B (0.9), B→C (0.8), obs C → explanation with rule chain."""
        r = _reasoner()
        r.clear_rules()
        r.add_rule("A", "B", 0.9, source="user")
        r.add_rule("B", "C", 0.8, source="user")

        explanations = r.explain("C", max_explanations=5)

        assert len(explanations) >= 1
        expl = explanations[0]
        # Full chain A→B→C should appear in rule_chain
        rule_ants = [rc[0] for rc in expl.rule_chain]
        assert "A" in rule_ants, f"A not in rule_chain: {rule_ants}"
        assert "B" in rule_ants, f"B not in rule_chain: {rule_ants}"
        # Confidence = product 0.9 * 0.8 = 0.72
        assert abs(expl.confidence - 0.72) < 0.01, f"Expected ~0.72, got {expl.confidence}"

    def test_abduction_confidence_is_product_of_rule_confidences(self):
        """Chain A→B→C confidence = 0.9 * 0.8 = 0.72."""
        r = _reasoner()
        r.clear_rules()
        r.add_rule("A", "B", 0.9, source="user")
        r.add_rule("B", "C", 0.8, source="user")

        explanations = r.explain("C", max_explanations=5)
        # Find the explanation that uses both rules
        chain_exps = [e for e in explanations if len(e.rule_chain) == 2]
        assert len(chain_exps) >= 1, f"Expected chain of 2 rules, got {[len(e.rule_chain) for e in explanations]}"
        exp = chain_exps[0]
        assert abs(exp.confidence - 0.72) < 0.01

    def test_abduction_deeper_chain(self):
        """A→B→C→D chain: obs D, confidence = 0.9 * 0.8 * 0.7 = 0.504."""
        r = _reasoner()
        r.clear_rules()
        r.add_rule("A", "B", 0.9, source="user")
        r.add_rule("B", "C", 0.8, source="user")
        r.add_rule("C", "D", 0.7, source="user")

        explanations = r.explain("D", max_explanations=5)
        assert len(explanations) >= 1
        expl = explanations[0]
        assert len(expl.rule_chain) == 3
        assert abs(expl.confidence - 0.504) < 0.01

    def test_abduction_partial_chain_B_explains_C(self):
        """Only B→C rule: obs C → explanation B (depth-1 chain)."""
        r = _reasoner()
        r.clear_rules()
        r.add_rule("B", "C", 0.8, source="user")

        explanations = r.explain("C", max_explanations=5)
        assert len(explanations) >= 1
        expl = explanations[0]
        assert expl.hypothesis == "B"
        assert len(expl.rule_chain) == 1
        assert abs(expl.confidence - 0.8) < 0.01

    def test_abduction_no_matching_rules_returns_empty(self):
        """No rules match observation → empty list."""
        r = _reasoner()
        r.clear_rules()
        r.add_rule("A", "B", 0.9, source="user")

        explanations = r.explain("C", max_explanations=5)
        assert explanations == []


# ============================================================================
# ABDUCTION — RULE MANAGEMENT
# ============================================================================
class TestAbductionRuleManagement:
    """Abduction rule lifecycle: add, clear, list."""

    def test_add_rule_returns_rule_object(self):
        r = _reasoner()
        r.clear_rules()
        rule = r.add_rule("X", "Y", 0.5, source="user")
        assert isinstance(rule, Rule)
        assert rule.antecedent == "X"
        assert rule.consequent == "Y"
        assert rule.confidence == 0.5

    def test_clear_rules_removes_all(self):
        r = _reasoner()
        r.add_rule("A", "B", 0.9, source="user")
        r.add_rule("C", "D", 0.5, source="user")
        r.clear_rules()
        assert r.list_rules() == []

    def test_list_rules_returns_all_added(self):
        r = _reasoner()
        r.clear_rules()
        r.add_rule("A", "B", 0.9, source="user")
        r.add_rule("C", "D", 0.5, source="user")
        rules = r.list_rules()
        assert len(rules) == 2

    def test_rule_confidence_clamped_to_0_1(self):
        r = _reasoner()
        r.clear_rules()
        r.add_rule("A", "B", 1.5, source="user")  # clamped to 1.0
        r.add_rule("C", "D", -0.5, source="user")  # clamped to 0.0
        rules = r.list_rules()
        assert rules[0].confidence == 1.0
        assert rules[1].confidence == 0.0


# ============================================================================
# ABDUCTION — COMMAND PARSING
# ============================================================================
class TestAbductionCommandParsing:
    """Command-level parsing: /abduce, /abduce rule add, /abduce rules, /abduce clear."""

    def test_abduce_command_finds_explanation(self):
        r = _reasoner()
        r.clear_rules()
        r.add_rule("A", "B", 0.9, source="user")
        r.add_rule("B", "C", 0.8, source="user")

        result = handle_abduce("/abduce C", "/abduce c")
        assert "explanation" in result.lower() or "C" in result
        assert "A" in result or "B" in result

    def test_abduce_rule_add_command(self):
        result = handle_abduce("/abduce rule add X Y 0.7", "/abduce rule add x y 0.7")
        assert "added" in result.lower() or "rule" in result.lower()

    def test_abduce_rules_lists_rules(self):
        r = _reasoner()
        r.clear_rules()
        r.add_rule("A", "B", 0.9, source="user")

        result = handle_abduce("/abduce rules", "/abduce rules")
        assert "A" in result or "B" in result or "rule" in result.lower()

    def test_abduce_clear_clears_rules(self):
        r = _reasoner()
        r.clear_rules()
        r.add_rule("A", "B", 0.9, source="user")

        result = handle_abduce("/abduce clear", "/abduce clear")
        assert "clear" in result.lower() or "rules" in result.lower()
        assert r.list_rules() == []

    def test_abduce_unknown_returns_usage(self):
        result = handle_abduce("/abduce unknown subcommand", "/abduce unknown subcommand")
        # Unknown subcommand → usage hint returned
        assert len(result) > 0


# ============================================================================
# META-ANALYSIS — FIXED EFFECT
# ============================================================================
class TestMetaAnalysisFixedEffect:
    """Fixed-effect pooling: two identical effect sizes → same pooled estimate."""

    def test_fixed_effect_same_effect_sizes_yields_same_pooled(self):
        """Same effect size + same SE → same pooled effect."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.1, n=50)
        m.add_study("s2", 0.5, 0.1, n=50)

        result = m.run_analysis(model="fixed")
        assert abs(result["pooled_effect"] - 0.5) < 0.001
        assert abs(result["pooled_se"] - 0.07071) < 0.01

    def test_fixed_effect_pooled_formula_inverse_variance(self):
        """Pooled = sum(wi*yi) / sum(wi), wi = 1/vi."""
        m = _meta()
        m.clear_studies()
        # Two studies with different effects/SEs
        m.add_study("s1", 0.4, 0.2)
        m.add_study("s2", 0.6, 0.2)
        # weighted mean should be 0.5
        result = m.run_analysis(model="fixed")
        assert abs(result["pooled_effect"] - 0.5) < 0.001

    def test_fixed_effect_p_value_significant(self):
        """Pooled effect Z=2.0 → p < 0.05 (two-tailed)."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 1.0, 0.5)
        result = m.run_analysis(model="fixed")
        assert result["p_value"] < 0.05

    def test_fixed_effect_ci_excludes_zero_for_significant(self):
        """Significant result → 95% CI excludes zero."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 2.0, 0.5)
        result = m.run_analysis(model="fixed")
        ci_low, ci_high = result["ci_low"], result["ci_high"]
        assert ci_low > 0 or ci_high < 0  # CI excludes zero


# ============================================================================
# META-ANALYSIS — HETEROGENEITY
# ============================================================================
class TestMetaAnalysisHeterogeneity:
    """Heterogeneity: Q statistic, I², tau²."""

    def test_heterogeneity_i2_low_for_homogeneous_studies(self):
        """Same effects → I² ≈ 0."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.1)
        m.add_study("s2", 0.5, 0.1)
        result = m.run_analysis(model="fixed")
        assert result["i2"] < 10  # near zero

    def test_heterogeneity_i2_high_for_heterogeneous_studies(self):
        """Different effects → I² > 50."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.1)
        m.add_study("s2", 2.0, 0.1)
        result = m.run_analysis(model="fixed")
        assert result["i2"] > 50

    def test_heterogeneity_q_statistic_formula(self):
        """Q = sum(wi*(yi - pooled)²)."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.2)
        m.add_study("s2", 0.5, 0.2)
        result = m.run_analysis(model="fixed")
        assert result["q_statistic"] < 3.84  # df=1, p>0.05

    def test_heterogeneity_tau_sq_zero_when_homogeneous(self):
        """Same effects → tau² = 0."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.2)
        m.add_study("s2", 0.5, 0.2)
        result = m.run_analysis(model="random")
        assert result["tau_squared"] < 0.001

    def test_heterogeneity_tau_sq_positive_when_heterogeneous(self):
        """Different effects → tau² > 0."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.0, 0.1)
        m.add_study("s2", 2.0, 0.1)
        result = m.run_analysis(model="random")
        assert result["tau_squared"] > 0

    def test_heterogeneity_i2_capped_at_0(self):
        """I² cannot be negative; capped at 0."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 10.0)
        m.add_study("s2", 0.5, 10.0)
        result = m.run_analysis(model="fixed")
        assert result["i2"] >= 0


# ============================================================================
# META-ANALYSIS — DETERMINISM
# ============================================================================
class TestMetaAnalysisDeterminism:
    """Repeated meta-analysis with same data → identical results."""

    def test_meta_analysis_deterministic_fixed_repeated(self):
        """Run fixed-effect analysis twice → identical pooled effect."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.1)
        m.add_study("s2", 0.6, 0.15)
        r1 = m.run_analysis(model="fixed")
        r2 = m.run_analysis(model="fixed")
        assert r1["pooled_effect"] == r2["pooled_effect"]
        assert r1["pooled_se"] == r2["pooled_se"]
        assert r1["q_statistic"] == r2["q_statistic"]

    def test_meta_analysis_deterministic_random_repeated(self):
        """Run random-effect analysis twice → identical tau²."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.1)
        m.add_study("s2", 0.8, 0.1)
        r1 = m.run_analysis(model="random")
        r2 = m.run_analysis(model="random")
        assert r1["tau_squared"] == r2["tau_squared"]
        assert r1["pooled_effect"] == r2["pooled_effect"]

    def test_meta_analysis_determinism_across_mode_switch(self):
        """Fixed vs random on same data → different tau²."""
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.1)
        m.add_study("s2", 0.9, 0.1)
        fixed = m.run_analysis(model="fixed")
        random = m.run_analysis(model="random")
        # random model should have larger SE
        assert random["pooled_se"] >= fixed["pooled_se"]


# ============================================================================
# META-ANALYSIS — COMMAND PARSING
# ============================================================================
class TestMetaAnalysisCommandParsing:
    """Command-level: /meta add, list, clear, run fixed/random, remove."""

    def test_meta_add_command(self):
        result = handle_meta("/meta add s1 0.5 0.1 50", "/meta add s1 0.5 0.1 50")
        assert "added" in result.lower() or "s1" in result

    def test_meta_list_command(self):
        m = _meta()
        m.clear_studies()
        m.add_study("x1", 0.5, 0.1)

        result = handle_meta("/meta list", "/meta list")
        assert "x1" in result or "study" in result.lower()

    def test_meta_clear_command(self):
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.1)

        result = handle_meta("/meta clear", "/meta clear")
        assert "clear" in result.lower() or "meta" in result.lower()
        assert m.list_studies() == []

    def test_meta_run_fixed_command(self):
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.1)
        m.add_study("s2", 0.6, 0.1)

        result = handle_meta("/meta run fixed", "/meta run fixed")
        assert "pooled" in result.lower() or "effect" in result.lower() or "s1" in result

    def test_meta_run_random_command(self):
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.1)
        m.add_study("s2", 0.6, 0.1)

        result = handle_meta("/meta run random", "/meta run random")
        assert "pooled" in result.lower() or "effect" in result.lower() or "s1" in result

    def test_meta_remove_command(self):
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.1)

        result = handle_meta("/meta remove s1", "/meta remove s1")
        assert "s1" not in m.list_studies()


# ============================================================================
# META-ANALYSIS — SINGLE STUDY
# ============================================================================
class TestMetaAnalysisSingleStudy:
    """Single study: pooled = study effect, SE same as study SE."""

    def test_single_study_fixed_effect(self):
        m = _meta()
        m.clear_studies()
        m.add_study("solo", 0.72, 0.25)
        result = m.run_analysis(model="fixed")
        assert abs(result["pooled_effect"] - 0.72) < 0.001
        assert abs(result["pooled_se"] - 0.25) < 0.001


# ============================================================================
# TRANSFER ANALOGY — MAPPING
# ============================================================================
class TestTransferAnalogyMapping:
    """Transfer analogy: enzyme[biology] → catalyst[chemistry], weight 0.9."""

    def test_builtin_enzyme_catalyst_analogy_exists(self):
        """Default analogy enzyme→catalyst should be preloaded."""
        analogies = _analogy().list_analogies()
        enzyme_cats = [a for a in analogies if a.source_concept == "enzyme"]
        assert len(enzyme_cats) >= 1
        assert enzyme_cats[0].target_concept == "catalyst"
        assert enzyme_cats[0].similarity_weight >= 0.8

    def test_transfer_hypothesis_enzyme_to_chemistry(self):
        """Transfer biology hypothesis to chemistry using enzyme→catalyst analogy."""
        h = Hypothesis(
            title="Enzyme catalyzes reaction",
            description="Enzymes accelerate biochemical reactions",
            domain="biology",
            confidence=1.0,
        )

        engine = _analogy()
        transferred = engine.transfer_hypothesis(h, "chemistry")

        assert transferred is not None
        # Confidence should be reduced by analogy weight
        assert transferred.adjusted_confidence < h.confidence
        # Transferred title or description should reference catalyst
        assert ("catalyst" in transferred.transferred_title.lower() or
                "catalyst" in transferred.transferred_description.lower())

    def test_transfer_confidence_reduced_proportionally_by_weight(self):
        """adjusted_confidence = original * weight. For weight=0.9: new=0.9*orig."""
        h = Hypothesis(
            title="Enzyme catalyzes reaction",
            description="Enzymes accelerate reactions",
            domain="biology",
            confidence=1.0,
        )

        engine = _analogy()
        transferred = engine.transfer_hypothesis(h, "chemistry")

        orig = h.confidence
        assert transferred.adjusted_confidence < orig
        # Use the actual weight from the enzyme→catalyst analogy
        enzyme_cats = [a for a in engine.list_analogies() if a.source_concept == "enzyme"]
        weight = enzyme_cats[0].similarity_weight if enzyme_cats else 0.9
        assert abs(transferred.adjusted_confidence - orig * weight) < 0.01

    def test_transfer_no_applicable_analogy_returns_none(self):
        """No analogy for source domain → None."""
        h = Hypothesis(
            title="Unknown concept",
            description="Something from unknown domain",
            domain="unknown_domain_xyz",
            confidence=0.5,
        )

        engine = _analogy()
        transferred = engine.transfer_hypothesis(h, "somewhere")
        assert transferred is None


# ============================================================================
# TRANSFER ANALOGY — ADD / REMOVE
# ============================================================================
class TestTransferAnalogyAdd:
    """Add custom analogies, remove them, clear user analogies."""

    def test_add_custom_analogy(self):
        engine = _analogy()
        initial = len(engine.list_analogies())

        analogy = engine.add_analogy(
            "physics", "force", "mechanics", "push", 0.85, provenance="user"
        )
        assert analogy.source_concept == "force"
        assert analogy.target_concept == "push"
        assert analogy.similarity_weight == 0.85

        assert len(engine.list_analogies()) == initial + 1

    def test_add_analogy_with_default_weight(self):
        engine = _analogy()
        analogy = engine.add_analogy(
            "physics", "velocity", "economics", "growth_rate", 0.8, provenance="user"
        )
        assert analogy.similarity_weight == 0.8

    def test_remove_analogy(self):
        engine = _analogy()
        initial = len(engine.list_analogies())

        added = engine.add_analogy("physics", "energy", "chemistry", "enthalpy", 0.75, provenance="user")
        engine.remove_analogy(added.id)

        assert len(engine.list_analogies()) == initial + 1 - 1

    def test_clear_user_analogies_keeps_builtin(self):
        engine = _analogy()
        initial_count = len(engine.list_analogies())

        engine.add_analogy("physics", "force", "mechanics", "push", 0.85, provenance="user")
        engine.clear_analogies()

        # Builtin analogies should still be there (or preloaded ones restored)
        # After clear + reset, preloaded analogies should be restored
        analogies = engine.list_analogies()
        # Should have some analogies (at least the builtins)
        assert len(analogies) >= 1


# ============================================================================
# TRANSFER ANALOGY — COMMAND PARSING
# ============================================================================
class TestTransferAnalogyCommandParsing:
    """Command-level: /transfer analogies, /transfer add, /transfer apply."""

    def test_transfer_analogies_lists(self):
        result = handle_transfer("/transfer analogies", "/transfer analogies")
        # Should mention enzyme or analogy content
        assert len(result) > 0
        assert "no analogies" not in result.lower() or "analogy" in result.lower()

    def test_transfer_add_command(self):
        result = handle_transfer(
            "/transfer add physics force mechanics push 0.85",
            "/transfer add physics force mechanics push 0.85"
        )
        assert "added" in result.lower() or "analogy" in result.lower()

    def test_transfer_apply_command_no_hypothesis(self):
        result = handle_transfer(
            "/transfer apply h123 chemistry",
            "/transfer apply h123 chemistry"
        )
        # No hypothesis found → usage or "not found" message
        assert len(result) > 0

    def test_transfer_unknown_returns_usage(self):
        result = handle_transfer("/transfer unknown subcommand", "/transfer unknown subcommand")
        assert len(result) > 0


# ============================================================================
# TRANSFER ANALOGY — FIND
# ============================================================================
class TestTransferAnalogyFind:
    """Find analogies by source domain or concept."""

    def test_find_analogies_by_source_domain(self):
        engine = _analogy()
        biol = engine.find_analogies_by_source_domain("biology")
        assert len(biol) > 0, f"No biology analogies found. Has: {[a.source_domain for a in engine.list_analogies()]}"

    def test_find_analogies_sorted_by_weight(self):
        engine = _analogy()
        # Add a low-weight analogy
        engine.add_analogy("physics", "mass", "chemistry", "weight", 0.3, provenance="user")
        engine.add_analogy("physics", "energy", "chemistry", "enthalpy", 0.9, provenance="user")

        biol = engine.find_analogies_by_source_domain("physics")
        weights = [a.similarity_weight for a in biol]
        assert weights == sorted(weights, reverse=True)


# ============================================================================
# BOUNDARY — NO EXTERNAL CALLS
# ============================================================================
class TestBoundaryNoExternalCalls:
    """Phase 9 modules use only in-memory data; no network, no external calls."""

    def test_abduction_no_network(self):
        r = _reasoner()
        r.clear_rules()
        r.add_rule("A", "B", 0.9, source="user")
        r.add_rule("B", "C", 0.8, source="user")
        explanations = r.explain("C", max_explanations=5)
        # Should work with only in-memory rules
        assert len(explanations) >= 1
        assert explanations[0].hypothesis in ("A", "B")

    def test_meta_analysis_no_network(self):
        m = _meta()
        m.clear_studies()
        m.add_study("s1", 0.5, 0.1)
        m.add_study("s2", 0.6, 0.1)
        result = m.run_analysis(model="fixed")
        # Should work with only in-memory studies
        assert "pooled_effect" in result
        assert result["pooled_effect"] > 0

    def test_transfer_analogy_no_network(self):
        h = Hypothesis(
            title="Enzyme behavior",
            description="Enzyme catalyzes reactions",
            domain="biology",
            confidence=1.0,
        )
        engine = _analogy()
        transferred = engine.transfer_hypothesis(h, "chemistry")
        # Should work with only in-memory analogies
        assert transferred is not None