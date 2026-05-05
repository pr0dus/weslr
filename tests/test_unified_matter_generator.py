"""Tests for unified_matter_generator + matter_primitives."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.modules.matter_primitives import Atom, Bond, Structure, PERIODIC_TABLE
from weslr.modules.unified_matter_generator import MatterGenerator, estimate_properties


def _formula(structure: Structure) -> str:
    """Get composition string from a Structure."""
    return structure.composition_string() if hasattr(structure, "composition_string") else str(structure)


def _charge(structure: Structure) -> int:
    """Compute total charge from each atom's primary oxidation state."""
    return sum(a.oxidation_states[0] for a in structure.atoms)


def test_perovskite_charge_balance():
    """plausible perovskites are charge-balanced and use known elements."""
    gen = MatterGenerator(seed=42)
    candidates = gen.generate_candidates(
        mode="plausible", max_candidates=20, constraints={"min_abundance": 0.0}
    )
    abx3 = [c for c in candidates if "ABX3" in c.geometry_type]
    assert len(abx3) > 0, f"No ABX3 candidates (got: {[c.geometry_type for c in candidates]})"
    for s in abx3:
        formula = _formula(s)
        charge = _charge(s)
        assert abs(charge) <= 1, (
            f"Formula {formula} not charge-balanced: charge={charge}. "
            f"Atoms: {[(a.symbol, a.oxidation_states) for a in s.atoms]}"
        )
        for a in s.atoms:
            assert a.symbol in PERIODIC_TABLE, f"Unknown element {a.symbol}"
    print(f"  ✓ perovskite charge balance: {len(abx3)} ABX3 candidates, all balanced — PASS")


def test_strangeness_unconventional_stoichiometry():
    """strangeness mode produces a variety of geometry types."""
    gen = MatterGenerator(seed=42)
    candidates = gen.generate_candidates(
        mode="strangeness", max_candidates=20, constraints={"min_abundance": 0.0}
    )
    assert len(candidates) > 0, "No strangeness candidates generated"

    formulas = [_formula(s) for s in candidates]
    dupes = [f for f in formulas if formulas.count(f) > 1]
    assert not dupes, f"Duplicate formulas: {set(dupes)}"

    geometry_types = set(c.geometry_type for c in candidates)
    assert len(geometry_types) > 1, "Only one geometry type in strangeness mode"

    print(f"  ✓ strangeness: {len(candidates)} candidates, {len(geometry_types)} geometry types — PASS")


def test_property_estimation_silicon_bandgap():
    """Si bandgap estimate within factor 2 of real value (1.1 eV)."""
    si_atom = PERIODIC_TABLE["Si"]
    structure = Structure(atoms=[si_atom]*2, bonds=[], geometry_type="0d_molecule", lattice_vectors=None)
    props = estimate_properties(structure)

    bandgap = props["bandgap_eV"]
    assert 0.5 <= bandgap <= 2.2, f"Si bandgap {bandgap} eV out of heuristic range [0.5, 2.2]"
    print(f"  ✓ Si bandgap: {bandgap:.2f} eV (real ~1.1 eV) — PASS")


def test_device_generation_multilayer():
    """generate_device_from_material produces a multi-layer structure."""
    gen = MatterGenerator()
    dev = gen.generate_device_from_material("CsPbI3", "solar_cell")

    assert "layers" in dev, "No layers key in device output"
    layers = dev["layers"]
    expected = {"ETL", "abs", "HTL", "metal"}
    missing = expected - layers.keys()
    assert not missing, f"Missing layers: {missing}"

    for layer_name, materials in layers.items():
        assert isinstance(materials, list), f"Layer {layer_name} materials not a list"
        assert len(materials) > 0, f"Layer {layer_name} has no materials"

    print(f"  ✓ solar_cell device: {list(layers.keys())} — PASS")


def test_determinism_same_seed():
    """Same seed yields identical candidates."""
    gen_a = MatterGenerator(seed=137)
    gen_b = MatterGenerator(seed=137)

    cands_a = gen_a.generate_candidates(mode="plausible", max_candidates=6, constraints={"min_abundance": 0.0})
    cands_b = gen_b.generate_candidates(mode="plausible", max_candidates=6, constraints={"min_abundance": 0.0})

    formulas_a = [_formula(s) for s in cands_a]
    formulas_b = [_formula(s) for s in cands_b]

    assert formulas_a == formulas_b, "Same seed produced different candidates"
    print(f"  ✓ determinism seed=137: identical {len(formulas_a)} candidates — PASS")


def test_duplicate_skipping():
    """Duplicate formulas are skipped within one generation run."""
    gen = MatterGenerator(seed=99)
    candidates = gen.generate_candidates(mode="strangeness", max_candidates=20, constraints={"min_abundance": 0.0})

    formulas = [_formula(s) for s in candidates]
    dupes = [f for f in formulas if formulas.count(f) > 1]
    assert not dupes, f"Duplicate formulas: {set(dupes)}"
    print(f"  ✓ no duplicates: {len(formulas)} unique from {len(candidates)} — PASS")


if __name__ == "__main__":
    print("\n=== unified_matter_generator tests ===\n")
    test_perovskite_charge_balance()
    test_strangeness_unconventional_stoichiometry()
    test_property_estimation_silicon_bandgap()
    test_device_generation_multilayer()
    test_determinism_same_seed()
    test_duplicate_skipping()
    print("\n✅ All tests passed.\n")
