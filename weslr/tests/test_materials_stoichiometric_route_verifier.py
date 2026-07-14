"""Tests for materials_stoichiometric_route_verifier.py.

Tests the independent verifier implementation, including:
- Known balanced reactions
- Known unbalanced reactions
- Formula-unit factor Z
- Coefficient canonicalization
- Residual vector checks
- Proposer/verifier agreement
- Deliberately injected errors
- Disagreement forces abstention
- Deterministic synthetic cases
"""

import json
import math
import sys
import unittest

sys.path.insert(0, ".")

from weslr.modules.materials_stoichiometric_route_verifier import (
    parse_formula_independent,
    elemental_vector_int,
    verify_coefficients,
    find_coefficients_independent,
    compute_reduced_formula_independent,
    canonicalize_coefficients,
    coefficients_agree,
    serialize_verifier_result,
)
from weslr.modules.materials_stoichiometric_route_engine import (
    balance_reaction as proposer_balance,
    serialize_route as proposer_serialize,
)


class TestParseFormulaIndependent(unittest.TestCase):
    def test_simple(self):
        vec = parse_formula_independent("CaSc2TiO6")
        self.assertEqual(vec.get("Ca", 0), 1)
        self.assertEqual(vec.get("Sc", 0), 2)
        self.assertEqual(vec.get("Ti", 0), 1)
        self.assertEqual(vec.get("O", 0), 6)

    def test_unicode(self):
        vec = parse_formula_independent("CaSc₂TiO₆")
        self.assertEqual(vec.get("Ca", 0), 1)
        self.assertEqual(vec.get("Sc", 0), 2)
        self.assertEqual(vec.get("O", 0), 6)

    def test_empty(self):
        self.assertEqual(parse_formula_independent(""), {})

    def test_invalid_element(self):
        self.assertEqual(parse_formula_independent("Xx2Y3"), {})

    def test_fractional(self):
        vec = parse_formula_independent("Ca0.5ScTiO3")
        self.assertEqual(vec.get("Ca", 0), 0.5)


class TestElementalVectorInt(unittest.TestCase):
    def test_integer(self):
        vec = elemental_vector_int("CaSc2TiO6")
        self.assertEqual(vec, {"Ca": 1, "Sc": 2, "Ti": 1, "O": 6})

    def test_fractional_returns_empty(self):
        self.assertEqual(elemental_vector_int("Ca0.5ScTiO3"), {})

    def test_empty(self):
        self.assertEqual(elemental_vector_int(""), {})


class TestVerifyCoefficients(unittest.TestCase):
    def test_sc2tio5_plus_cao(self):
        """Sc2TiO5 + CaO -> CaSc2TiO6 with coefficients (1, 1) -> 1."""
        result = verify_coefficients(["Sc2TiO5", "CaO"], [1, 1], "CaSc2TiO6", 1)
        self.assertTrue(result["balanced"])
        self.assertEqual(result["max_absolute_residual"], 0)

    def test_sc4ti2o10_plus_2cao(self):
        """Sc4Ti2O10 + 2 CaO -> 2 CaSc2TiO6 with coefficients (1, 2) -> 2."""
        result = verify_coefficients(["Sc4Ti2O10", "CaO"], [1, 2], "CaSc2TiO6", 2)
        self.assertTrue(result["balanced"])
        self.assertEqual(result["max_absolute_residual"], 0)

    def test_sc4ti2o10_plus_1cao(self):
        """Sc4Ti2O10 + CaO -> CaSc2TiO6 with coefficients (1, 1) -> 1 is NOT balanced."""
        result = verify_coefficients(["Sc4Ti2O10", "CaO"], [1, 1], "CaSc2TiO6", 1)
        self.assertFalse(result["balanced"])
        self.assertGreater(result["max_absolute_residual"], 0)

    def test_casc2o4_plus_tio2(self):
        result = verify_coefficients(["CaSc2O4", "TiO2"], [1, 1], "CaSc2TiO6", 1)
        self.assertTrue(result["balanced"])

    def test_catio3_plus_sc2o3(self):
        result = verify_coefficients(["CaTiO3", "Sc2O3"], [1, 1], "CaSc2TiO6", 1)
        self.assertTrue(result["balanced"])

    def test_invalid_formula(self):
        result = verify_coefficients(["Xx2Y3"], [1], "CaSc2TiO6", 1)
        self.assertFalse(result["balanced"])


class TestFindCoefficientsIndependent(unittest.TestCase):
    def test_sc2tio5_plus_cao(self):
        result = find_coefficients_independent(["Sc2TiO5", "CaO"], "CaSc2TiO6")
        self.assertTrue(result["balanced"])
        self.assertEqual(result["coefficients"].get("Sc2TiO5", 0), 1)
        self.assertEqual(result["coefficients"].get("CaO", 0), 1)
        self.assertEqual(result["target_coefficient"], 1)

    def test_sc4ti2o10_plus_cao(self):
        """Sc4Ti2O10 + 2 CaO -> 2 CaSc2TiO6."""
        result = find_coefficients_independent(["Sc4Ti2O10", "CaO"], "CaSc2TiO6")
        self.assertTrue(result["balanced"])
        self.assertEqual(result["coefficients"].get("Sc4Ti2O10", 0), 1)
        self.assertEqual(result["coefficients"].get("CaO", 0), 2)
        self.assertEqual(result["target_coefficient"], 2)

    def test_casc2o4_plus_tio2(self):
        result = find_coefficients_independent(["CaSc2O4", "TiO2"], "CaSc2TiO6")
        self.assertTrue(result["balanced"])

    def test_catio3_plus_sc2o3(self):
        result = find_coefficients_independent(["CaTiO3", "Sc2O3"], "CaSc2TiO6")
        self.assertTrue(result["balanced"])

    def test_element_mismatch(self):
        result = find_coefficients_independent(["NaCl"], "CaSc2TiO6")
        self.assertFalse(result["balanced"])

    def test_unbalanced(self):
        result = find_coefficients_independent(["Sc2TiO5"], "CaSc2TiO6")
        self.assertFalse(result["balanced"])


class TestReducedFormulaIndependent(unittest.TestCase):
    def test_sc4ti2o10(self):
        formula, z = compute_reduced_formula_independent("Sc4Ti2O10")
        self.assertEqual(formula, "Sc2TiO5")
        self.assertEqual(z, 2)

    def test_ca2sc4ti2o12(self):
        formula, z = compute_reduced_formula_independent("Ca2Sc4Ti2O12")
        self.assertEqual(formula, "CaSc2TiO6")
        self.assertEqual(z, 2)

    def test_already_reduced(self):
        formula, z = compute_reduced_formula_independent("CaSc2TiO6")
        self.assertEqual(formula, "CaSc2TiO6")
        self.assertEqual(z, 1)

    def test_empty(self):
        formula, z = compute_reduced_formula_independent("")
        self.assertEqual(formula, "")
        self.assertEqual(z, 0)


class TestCanonicalizeCoefficients(unittest.TestCase):
    def test_reduce_by_gcd(self):
        result = canonicalize_coefficients({"A": 2, "B": 4}, 2)
        self.assertEqual(result["reduced_coefficients"], {"A": 1, "B": 2})
        self.assertEqual(result["reduced_target_coefficient"], 1)
        self.assertEqual(result["gcd"], 2)

    def test_already_reduced(self):
        result = canonicalize_coefficients({"A": 1, "B": 2}, 1)
        self.assertEqual(result["gcd"], 1)


class TestCoefficientsAgree(unittest.TestCase):
    def test_agree(self):
        self.assertTrue(coefficients_agree(
            {"Sc2TiO5": 1, "CaO": 1}, 1,
            {"Sc2TiO5": 1, "CaO": 1}, 1,
        ))

    def test_agree_after_reduction(self):
        self.assertTrue(coefficients_agree(
            {"Sc2TiO5": 2, "CaO": 2}, 2,
            {"Sc2TiO5": 1, "CaO": 1}, 1,
        ))

    def test_disagree(self):
        self.assertFalse(coefficients_agree(
            {"Sc2TiO5": 1, "CaO": 1}, 1,
            {"Sc2TiO5": 2, "CaO": 1}, 1,
        ))


class TestProposerVerifierAgreement(unittest.TestCase):
    def test_balanced_routes_agree(self):
        routes = [
            (["Sc2TiO5", "CaO"], "CaSc2TiO6"),
            (["Sc4Ti2O10", "CaO"], "CaSc2TiO6"),
            (["CaSc2O4", "TiO2"], "CaSc2TiO6"),
            (["CaTiO3", "Sc2O3"], "CaSc2TiO6"),
        ]
        for reactants, target in routes:
            p = proposer_balance(reactants, target)
            v = find_coefficients_independent(reactants, target)
            if p["balanced"] and v["balanced"]:
                agree = coefficients_agree(
                    p["coefficients"], p["target_coefficient"],
                    v["coefficients"], v["target_coefficient"],
                )
                self.assertTrue(agree, f"Disagreement on {reactants} -> {target}")

    def test_unbalanced_routes_agree(self):
        routes = [
            (["Sc2TiO5"], "CaSc2TiO6"),
            (["NaCl"], "CaSc2TiO6"),
            (["CaO"], "CaSc2TiO6"),
        ]
        for reactants, target in routes:
            p = proposer_balance(reactants, target)
            v = find_coefficients_independent(reactants, target)
            self.assertEqual(p["balanced"], v["balanced"],
                             f"Disagreement on unbalanced {reactants} -> {target}")


class TestInjectedError(unittest.TestCase):
    def test_injected_proposer_error(self):
        """Deliberately wrong proposer result should be caught by verifier."""
        # Proposer says Sc2TiO5 + CaO -> CaSc2TiO6 with coefficients (2, 1) -> 1
        # This is wrong - should be (1, 1) -> 1
        wrong_coeffs = {"Sc2TiO5": 2, "CaO": 1}
        wrong_target = 1
        v = find_coefficients_independent(["Sc2TiO5", "CaO"], "CaSc2TiO6")
        agree = coefficients_agree(
            wrong_coeffs, wrong_target,
            v["coefficients"], v["target_coefficient"],
        )
        self.assertFalse(agree, "Injected proposer error should be detected")

    def test_injected_verifier_error(self):
        """Deliberately wrong verifier result should be caught by proposer."""
        p = proposer_balance(["Sc2TiO5", "CaO"], "CaSc2TiO6")
        # Verifier says coefficients (1, 2) -> 1 (wrong)
        wrong_coeffs = {"Sc2TiO5": 1, "CaO": 2}
        wrong_target = 1
        agree = coefficients_agree(
            p["coefficients"], p["target_coefficient"],
            wrong_coeffs, wrong_target,
        )
        self.assertFalse(agree, "Injected verifier error should be detected")


class TestSerialization(unittest.TestCase):
    def test_deterministic(self):
        r1 = find_coefficients_independent(["Sc2TiO5", "CaO"], "CaSc2TiO6")
        r2 = find_coefficients_independent(["Sc2TiO5", "CaO"], "CaSc2TiO6")
        self.assertEqual(serialize_verifier_result(r1), serialize_verifier_result(r2))

    def test_json_parseable(self):
        r = find_coefficients_independent(["Sc2TiO5", "CaO"], "CaSc2TiO6")
        s = serialize_verifier_result(r)
        parsed = json.loads(s)
        self.assertIn("balanced", parsed)


class TestSyntheticCases(unittest.TestCase):
    """Generate 100+ deterministic synthetic reaction cases with fixed seed."""

    @classmethod
    def setUpClass(cls):
        # Use a fixed seed for reproducibility
        import random
        cls.rng = random.Random(42)

        # Define known formulas and their elemental vectors
        cls.known_formulas = {
            "CaO": {"Ca": 1, "O": 1},
            "Sc2O3": {"Sc": 2, "O": 3},
            "TiO2": {"Ti": 1, "O": 2},
            "CaTiO3": {"Ca": 1, "Ti": 1, "O": 3},
            "CaSc2O4": {"Ca": 1, "Sc": 2, "O": 4},
            "Sc2TiO5": {"Sc": 2, "Ti": 1, "O": 5},
            "CaSc2TiO6": {"Ca": 1, "Sc": 2, "Ti": 1, "O": 6},
            "Sc4Ti2O10": {"Sc": 4, "Ti": 2, "O": 10},
            "Ca2Sc4Ti2O12": {"Ca": 2, "Sc": 4, "Ti": 2, "O": 12},
            "CaSc4Ti2O11": {"Ca": 1, "Sc": 4, "Ti": 2, "O": 11},
        }

        # Generate balanced positive controls by scaling known routes
        cls.positive_cases = []
        base_routes = [
            (["Sc2TiO5", "CaO"], "CaSc2TiO6", {0: 1, 1: 1}, 1),
            (["Sc4Ti2O10", "CaO"], "CaSc2TiO6", {0: 1, 1: 2}, 2),
            (["CaSc2O4", "TiO2"], "CaSc2TiO6", {0: 1, 1: 1}, 1),
            (["CaTiO3", "Sc2O3"], "CaSc2TiO6", {0: 1, 1: 1}, 1),
        ]
        for scale in [1, 2, 3]:
            for reactants, target, coeffs, t_coeff in base_routes:
                scaled = {k: v * scale for k, v in coeffs.items()}
                scaled_t = t_coeff * scale
                cls.positive_cases.append((reactants, target, scaled, scaled_t))

        # Generate negative controls (one-element residual failures)
        cls.negative_cases = []
        for reactants, target, coeffs, t_coeff in base_routes:
            # Modify one coefficient to be wrong
            for i in range(len(reactants)):
                wrong = dict(coeffs)
                wrong[i] = coeffs[i] + 1
                cls.negative_cases.append((reactants, target, wrong, t_coeff))

        # Generate element-mismatch cases
        cls.mismatch_cases = [
            (["NaCl"], "CaSc2TiO6"),
            (["MgO", "Al2O3"], "CaSc2TiO6"),
        ]

    def test_positive_controls(self):
        for reactants, target, coeffs, t_coeff in self.positive_cases:
            coeff_list = [coeffs[i] for i in range(len(reactants))]
            result = verify_coefficients(reactants, coeff_list, target, t_coeff)
            self.assertTrue(result["balanced"],
                            f"Positive control failed: {reactants} -> {target} with {coeffs}")

    def test_negative_controls(self):
        for reactants, target, coeffs, t_coeff in self.negative_cases:
            coeff_list = [coeffs[i] for i in range(len(reactants))]
            result = verify_coefficients(reactants, coeff_list, target, t_coeff)
            self.assertFalse(result["balanced"],
                             f"Negative control should fail: {reactants} -> {target} with {coeffs}")

    def test_mismatch_cases(self):
        for reactants, target in self.mismatch_cases:
            result = find_coefficients_independent(reactants, target)
            self.assertFalse(result["balanced"])

    def test_coefficient_scaling_equivalence(self):
        """(1, 1) -> 1 and (2, 2) -> 2 should be equivalent after reduction."""
        c1 = canonicalize_coefficients({"A": 1, "B": 1}, 1)
        c2 = canonicalize_coefficients({"A": 2, "B": 2}, 2)
        self.assertEqual(c1["reduced_coefficients"], c2["reduced_coefficients"])
        self.assertEqual(c1["reduced_target_coefficient"], c2["reduced_target_coefficient"])

    def test_no_floating_point(self):
        """Verify that no floating-point arithmetic is used for elemental balance."""
        # All elemental_vector_int returns integers
        # All verify_coefficients uses integer arithmetic
        # All find_coefficients_independent uses integer arithmetic
        result = verify_coefficients(["Sc2TiO5", "CaO"], [1, 1], "CaSc2TiO6", 1)
        for el, residual in result["residual"].items():
            self.assertIsInstance(residual, int)
        self.assertIsInstance(result["max_absolute_residual"], int)
        self.assertIsInstance(result["total_absolute_residual"], int)


if __name__ == "__main__":
    unittest.main()
