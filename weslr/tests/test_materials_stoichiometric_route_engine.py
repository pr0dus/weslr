"""Tests for materials_stoichiometric_route_engine.py."""

import json
import sys
import unittest

sys.path.insert(0, ".")

from weslr.modules.materials_stoichiometric_route_engine import (
    normalize_formula,
    elemental_vector,
    reduced_formula_and_factor,
    balance_reaction,
    calculate_parent_to_target_delta,
    classify_route,
    check_charge_balance,
    serialize_route,
)


class TestNormalizeFormula(unittest.TestCase):
    def test_simple_formula(self):
        self.assertEqual(normalize_formula("CaSc2TiO6"), "CaSc2TiO6")

    def test_unicode_subscripts(self):
        self.assertEqual(normalize_formula("CaSc₂TiO₆"), "CaSc2TiO6")

    def test_whitespace(self):
        self.assertEqual(normalize_formula("  Ca Sc2 Ti O6  "), "CaSc2TiO6")

    def test_empty(self):
        self.assertEqual(normalize_formula(""), "")

    def test_none(self):
        self.assertEqual(normalize_formula(None), "")

    def test_single_element(self):
        self.assertEqual(normalize_formula("O2"), "O2")

    def test_ordering(self):
        # O should be last
        result = normalize_formula("OCa")
        self.assertTrue(result.endswith("O"))


class TestElementalVector(unittest.TestCase):
    def test_ca_sc_ti_o(self):
        vec = elemental_vector("CaSc2TiO6")
        self.assertAlmostEqual(vec.get("Ca", 0), 1)
        self.assertAlmostEqual(vec.get("Sc", 0), 2)
        self.assertAlmostEqual(vec.get("Ti", 0), 1)
        self.assertAlmostEqual(vec.get("O", 0), 6)

    def test_empty(self):
        self.assertEqual(elemental_vector(""), {})

    def test_invalid(self):
        self.assertEqual(elemental_vector(None), {})


class TestReducedFormulaAndFactor(unittest.TestCase):
    def test_already_reduced(self):
        formula, z = reduced_formula_and_factor("CaSc2TiO6")
        self.assertEqual(formula, "CaSc2TiO6")
        self.assertAlmostEqual(z, 1.0)

    def test_double_cell(self):
        formula, z = reduced_formula_and_factor("Ca2Sc4Ti2O12")
        self.assertEqual(formula, "CaSc2TiO6")
        self.assertAlmostEqual(z, 2.0)

    def test_sc2tio5_reduced(self):
        formula, z = reduced_formula_and_factor("Sc2TiO5")
        self.assertEqual(formula, "Sc2TiO5")
        self.assertAlmostEqual(z, 1.0)

    def test_sc4ti2o10_double(self):
        formula, z = reduced_formula_and_factor("Sc4Ti2O10")
        self.assertEqual(formula, "Sc2TiO5")
        self.assertAlmostEqual(z, 2.0)

    def test_empty(self):
        formula, z = reduced_formula_and_factor("")
        self.assertEqual(formula, "")
        self.assertAlmostEqual(z, 0.0)


class TestBalanceReaction(unittest.TestCase):
    def test_sc2tio5_plus_cao(self):
        """Sc2TiO5 + CaO -> CaSc2TiO6 is exact."""
        result = balance_reaction(["Sc2TiO5", "CaO"], "CaSc2TiO6")
        self.assertTrue(result["balanced"], f"Should be balanced: {result['reason']}")
        self.assertIn(result["route_class"], ["exact_combination_route"])

    def test_sc4ti2o10_plus_2cao(self):
        """Sc4Ti2O10 + 2 CaO -> 2 CaSc2TiO6 is exact."""
        result = balance_reaction(["Sc4Ti2O10", "CaO"], "CaSc2TiO6")
        self.assertTrue(result["balanced"], f"Should be balanced: {result['reason']}")
        # Should find: 1*Sc4Ti2O10 + 2*CaO -> 2*CaSc2TiO6
        self.assertGreaterEqual(result["target_coefficient"], 2,
                                "Target coefficient should be >= 2 for Sc4Ti2O10")

    def test_casc2o4_plus_tio2(self):
        """CaSc2O4 + TiO2 -> CaSc2TiO6 is exact."""
        result = balance_reaction(["CaSc2O4", "TiO2"], "CaSc2TiO6")
        self.assertTrue(result["balanced"], f"Should be balanced: {result['reason']}")

    def test_catio3_plus_sc2o3(self):
        """CaTiO3 + Sc2O3 -> CaSc2TiO6 is exact."""
        result = balance_reaction(["CaTiO3", "Sc2O3"], "CaSc2TiO6")
        self.assertTrue(result["balanced"], f"Should be balanced: {result['reason']}")

    def test_sc4ti2o10_plus_cao_not_enough(self):
        """Sc4Ti2O10 + CaO does not yield the target (needs 2 CaO)."""
        result = balance_reaction(["Sc4Ti2O10", "CaO"], "CaSc2TiO6")
        # This should be balanced with coefficients (1, 2) -> 2
        # The CaO coefficient should be 2
        if result["balanced"]:
            cao_coeff = result["coefficients"].get("CaO", 0)
            self.assertGreaterEqual(cao_coeff, 2, "Need at least 2 CaO for Sc4Ti2O10")

    def test_casc4ti2o11_not_multiple(self):
        """CaSc4Ti2O11 is not a multiple of CaSc2TiO6."""
        formula, z = reduced_formula_and_factor("CaSc4Ti2O11")
        self.assertNotEqual(formula, "CaSc2TiO6", "CaSc4Ti2O11 should not reduce to CaSc2TiO6")


class TestParentToTargetDelta(unittest.TestCase):
    def test_sc4ti2o10_to_casc2tio6(self):
        """Sc4Ti2O10 -> CaSc2TiO6: needs Ca and O addition."""
        result = calculate_parent_to_target_delta("Sc4Ti2O10", "CaSc2TiO6")
        self.assertEqual(result["parent_reduced"], "Sc2TiO5")
        self.assertAlmostEqual(result["parent_Z"], 2.0)
        self.assertEqual(result["target_reduced"], "CaSc2TiO6")
        self.assertAlmostEqual(result["target_Z"], 1.0)
        # Sc4Ti2O10 has 2 reduced units, target has 1
        # 1 Sc4Ti2O10 + 2 CaO -> 2 CaSc2TiO6
        # So delta should show Ca and O to add
        self.assertIn("Ca", result.get("delta_add", {}),
                      "Should need Ca to reach CaSc2TiO6 from Sc4Ti2O10")
        self.assertIn("O", result.get("delta_add", {}),
                      "Should need O to reach CaSc2TiO6 from Sc4Ti2O10")

    def test_sc2tio5_to_casc2tio6(self):
        """Sc2TiO5 -> CaSc2TiO6: needs Ca and O addition."""
        result = calculate_parent_to_target_delta("Sc2TiO5", "CaSc2TiO6")
        self.assertIn("Ca", result.get("delta_add", {}),
                      "Should need Ca to reach CaSc2TiO6 from Sc2TiO5")
        self.assertIn("O", result.get("delta_add", {}),
                      "Should need O to reach CaSc2TiO6 from Sc2TiO5")

    def test_casc2o4_to_casc2tio6(self):
        """CaSc2O4 -> CaSc2TiO6: needs Ti and O addition."""
        result = calculate_parent_to_target_delta("CaSc2O4", "CaSc2TiO6")
        self.assertIn("Ti", result.get("delta_add", {}),
                      "Should need Ti to reach CaSc2TiO6 from CaSc2O4")
        self.assertIn("O", result.get("delta_add", {}),
                      "Should need O to reach CaSc2TiO6 from CaSc2O4")

    def test_catio3_to_casc2tio6(self):
        """CaTiO3 -> CaSc2TiO6: needs Sc and O addition."""
        result = calculate_parent_to_target_delta("CaTiO3", "CaSc2TiO6")
        self.assertIn("Sc", result.get("delta_add", {}),
                      "Should need Sc to reach CaSc2TiO6 from CaTiO3")


class TestClassifyRoute(unittest.TestCase):
    def test_exact_combination(self):
        result = balance_reaction(["Sc2TiO5", "CaO"], "CaSc2TiO6")
        classification = classify_route(result)
        self.assertEqual(classification, "exact_combination_route")

    def test_invalid_returns_route_class(self):
        result = {"balanced": False, "route_class": "invalid_formula"}
        self.assertEqual(classify_route(result), "invalid_formula")


class TestChargeBalance(unittest.TestCase):
    def test_casc2tio6_balanced(self):
        result = check_charge_balance("CaSc2TiO6")
        # Ca2+ + 2*Sc3+ + Ti4+ + 6*O2- = 2 + 6 + 4 - 12 = 0
        self.assertTrue(result["balanced"], f"Should be charge balanced: {result['reason']}")

    def test_invalid_formula(self):
        result = check_charge_balance("")
        self.assertFalse(result["balanced"])


class TestSerialization(unittest.TestCase):
    def test_deterministic_json(self):
        r1 = balance_reaction(["Sc2TiO5", "CaO"], "CaSc2TiO6")
        r2 = balance_reaction(["Sc2TiO5", "CaO"], "CaSc2TiO6")
        s1 = serialize_route(r1)
        s2 = serialize_route(r2)
        self.assertEqual(s1, s2, "Repeated execution should produce identical JSON")

    def test_json_parseable(self):
        r = balance_reaction(["Sc2TiO5", "CaO"], "CaSc2TiO6")
        s = serialize_route(r)
        parsed = json.loads(s)
        self.assertIn("balanced", parsed)


class TestInvalidFormulas(unittest.TestCase):
    def test_invalid_formula(self):
        result = balance_reaction(["Xx2Y3"], "CaSc2TiO6")
        self.assertFalse(result["balanced"])
        # Y is a valid element, so this is element_mismatch, not invalid_formula
        self.assertIn(result["route_class"], ["element_mismatch", "invalid_formula"])

    def test_fractional_formula(self):
        result = balance_reaction(["Ca0.5ScTiO3"], "CaSc2TiO6")
        self.assertIsInstance(result, dict)

    def test_element_mismatch(self):
        result = balance_reaction(["NaCl"], "CaSc2TiO6")
        self.assertFalse(result["balanced"])


class TestRepeatedExecution(unittest.TestCase):
    def test_identical_output(self):
        results = []
        for _ in range(5):
            r = balance_reaction(["Sc2TiO5", "CaO"], "CaSc2TiO6")
            results.append(serialize_route(r))
        for i in range(1, len(results)):
            self.assertEqual(results[0], results[i],
                             f"Run {i} differs from run 0")


class TestFormulaUnitScaling(unittest.TestCase):
    def test_sc4ti2o10_z_is_2(self):
        """Sc4Ti2O10 has Z=2 (contains 2 Sc2TiO5 units)."""
        formula, z = reduced_formula_and_factor("Sc4Ti2O10")
        self.assertEqual(formula, "Sc2TiO5")
        self.assertAlmostEqual(z, 2.0)

    def test_ca2sc4ti2o12_z_is_2(self):
        """Ca2Sc4Ti2O12 has Z=2 (contains 2 CaSc2TiO6 units)."""
        formula, z = reduced_formula_and_factor("Ca2Sc4Ti2O12")
        self.assertEqual(formula, "CaSc2TiO6")
        self.assertAlmostEqual(z, 2.0)

    def test_sc4ti2o10_plus_2cao_equals_2_casc2tio6(self):
        """Sc4Ti2O10 + 2 CaO = 2 CaSc2TiO6 is exact."""
        # Check elemental balance
        sc4 = elemental_vector("Sc4Ti2O10")
        ca2o2 = elemental_vector("CaO")  # 2 CaO
        total = {}
        for el, c in sc4.items():
            total[el] = total.get(el, 0) + c
        for el, c in ca2o2.items():
            total[el] = total.get(el, 0) + 2 * c  # 2 CaO

        target = elemental_vector("Ca2Sc4Ti2O12")
        for el in total:
            self.assertAlmostEqual(total[el], target.get(el, 0),
                                   f"Element {el} mismatch: {total[el]} vs {target.get(el, 0)}")

    def test_casc4ti2o11_not_multiple(self):
        """CaSc4Ti2O11 is not a multiple of CaSc2TiO6."""
        formula, z = reduced_formula_and_factor("CaSc4Ti2O11")
        self.assertNotEqual(formula, "CaSc2TiO6")


if __name__ == "__main__":
    unittest.main()
