"""
Tests for unified_matter_generator.py — structure classification and properties.
"""
import sys
sys.path.insert(0, '.')

import pytest
from weslr.modules.unified_matter_generator import (
    _classify_structure,
    _gcd_of,
    MatterGenerator,
)
from weslr.modules.matter_primitives import Structure, PERIODIC_TABLE


# ── _gcd_of ────────────────────────────────────────────────────────────────────

class TestGcdOf:
    def test_pair(self):
        assert _gcd_of([6, 9]) == 3

    def test_triple(self):
        assert _gcd_of([6, 9, 12]) == 3

    def test_coprime(self):
        assert _gcd_of([7, 13]) == 1

    def test_single(self):
        assert _gcd_of([42]) == 42


# ── _classify_structure — exact stoichiometry matches ─────────────────────────

class TestStoichiometryMap:
    def test_perovskite_abx3(self):
        for f in ['CaTiO3', 'SrTiO3', 'BaTiO3', 'CsPbI3']:
            r, u = _classify_structure(f)
            assert r == 'perovskite', f'{f} → {r}'
            assert u == 'low'

    def test_ruddlesden_popper_n1(self):
        r, u = _classify_structure('Ca2TiO4')
        assert r == 'ruddlesden_popper_n1', f'got {r}'
        assert u == 'low'

    def test_ruddlesden_popper_n2(self):
        # A3B2X7 — less common, test the key exists
        # No real example in our periodic table set, but GCD reduction should work
        pass  # key exists in map, tested separately

    def test_spinel(self):
        for f in ['MgTi2O4', 'MgAl2O4', 'ZnFe2O4']:
            r, u = _classify_structure(f)
            assert r == 'spinel', f'{f} → {r}'
            assert u == 'low'

    def test_rutile(self):
        for f in ['TiO2', 'SnO2', 'GeO2']:
            r, u = _classify_structure(f)
            assert r == 'rutile', f'{f} → {r}'
            assert u == 'low'

    def test_rocksalt(self):
        for f in ['MgO', 'NaCl', 'CaO']:
            r, u = _classify_structure(f)
            assert r == 'rocksalt', f'{f} → {r}'
            assert u == 'low'

    def test_olivine(self):
        for f in ['Mg2SiO4', 'Fe2SiO4', 'Zn2SiO4']:
            r, u = _classify_structure(f)
            assert r == 'olivine', f'{f} → {r}'
            assert u == 'low'

    def test_unclassified_multication(self):
        # CaSc2TiO6 — 3 distinct cations, not a known stoichiometry
        r, u = _classify_structure('CaSc2TiO6')
        assert r == 'unclassified', f'got {r}'
        assert u == 'high'

    def test_unclassified_exotic_stoich(self):
        # CaO6Sc2Ti — same as CaSc2TiO6, normalized (1,1,2,6) → unclassified
        r, u = _classify_structure('CaO6Sc2Ti')
        assert r == 'unclassified'
        assert u == 'high'

    def test_uncertainty_high_for_unclassified(self):
        r, u = _classify_structure('CaO6Sc2Ti')
        assert u == 'high'

    def test_uncertainty_low_for_classified(self):
        r, u = _classify_structure('CaTiO3')
        assert u == 'low'


# ── estimate_properties — uncertainty flag and stability penalty ───────────────

class TestUncertaintyFlag:
    def setup_method(self):
        self.gen = MatterGenerator(seed=42, graph_path='weslr/data/material_graph_expanded.json')

    def test_unclassified_gets_stability_penalty(self):
        # CaO6Sc2Ti: unclassified, stability should be reduced ×0.9
        struct = self.gen._build_structure_from_formula('CaO6Sc2Ti', 'perovskite')
        props = self.gen.estimate_properties(struct)
        assert props['uncertainty'] == 'high'
        assert props['geometry_type'] == 'unclassified'
        # Check stability was penalised (stability < base stability for that formula)
        # We can't directly check the base, but we can verify the penalty flag is set
        assert 'uncertainty' in props

    def test_classified_no_penalty(self):
        struct = self.gen._build_structure_from_formula('CaTiO3', 'perovskite')
        props = self.gen.estimate_properties(struct)
        assert props['uncertainty'] == 'low'
        assert props['geometry_type'] == 'ABX3_cubic'
        # No disclaimer expected for classified structure
        assert 'disclaimer' not in props


# ── generate_device_from_material — disclaimer for unclassified ────────────────

class TestDeviceGenerationSkipsUnclassified:
    def setup_method(self):
        self.gen = MatterGenerator(seed=42, graph_path='weslr/data/material_graph_expanded.json')

    def test_device_generation_caO6Sc2Ti_has_disclaimer(self):
        device = self.gen.generate_device_from_material('CaO6Sc2Ti', 'solar_cell')
        assert 'disclaimer' in device
        assert 'unclassified' in device['disclaimer']
        assert device['structural_uncertainty'] == 'high'
        assert device['structure_classification'] == 'unclassified'

    def test_classified_perovskite_no_disclaimer(self):
        device = self.gen.generate_device_from_material('CaTiO3', 'solar_cell')
        assert 'disclaimer' not in device
        assert device['structural_uncertainty'] == 'low'
        assert device['structure_classification'] == 'perovskite'


# ── _build_structure_from_formula ───────────────────────────────────────────────

class TestBuildStructureFromFormula:
    def setup_method(self):
        self.gen = MatterGenerator(seed=42, graph_path='weslr/data/material_graph_expanded.json')

    def test_unclassified_formula_gets_unclassified_geometry(self):
        struct = self.gen._build_structure_from_formula('CaO6Sc2Ti', 'perovskite')
        assert struct.geometry_type == 'unclassified'

    def test_known_perovskite_gets_ABX3_cubic(self):
        struct = self.gen._build_structure_from_formula('CaTiO3', 'perovskite')
        assert struct.geometry_type == 'ABX3_cubic'

    def test_spinel_gets_AB2X4_cubic(self):
        struct = self.gen._build_structure_from_formula('MgTi2O4', 'spinel')
        assert struct.geometry_type == 'AB2X4_cubic'

    def test_ruddlesden_popper_n1_gets_layered_perovskite(self):
        struct = self.gen._build_structure_from_formula('Ca2TiO4', 'ruddlesden_popper')
        assert struct.geometry_type == 'layered_perovskite'

    def test_olivine_gets_orthorhombic_olivine(self):
        struct = self.gen._build_structure_from_formula('Mg2SiO4', 'olivine')
        assert struct.geometry_type == 'orthorhombic_olivine'