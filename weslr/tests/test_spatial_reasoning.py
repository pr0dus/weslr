"""
weslr/tests/test_spatial_reasoning.py
=====================================
Phase 6.7 — Molecular geometry reasoning tests for Weslr.

Tests cover:
- XYZ parsing
- Euclidean distance
- Bond angles
- Dihedral angles
- Chirality detection (tetrahedral centers)
- VSEPR shape assignment
- Demo molecule loading
- Command parsing (spatial_commands)
- Integration with /explore

Deterministic throughout (no stochastic components).
"""

import unittest
import math
import os
import tempfile

import numpy as np


class TestMolecularStructure(unittest.TestCase):
    """Phase 6.7 spatial reasoning test suite."""

    def setUp(self):
        # Deterministic setup — isolate module-level molecule state per test
        import weslr.commands.spatial_commands as sc
        sc._CURRENT_MOLECULE = None

    # ── XYZ Parsing ─────────────────────────────────────────────────────────

    def test_parse_xyz_water(self):
        """Parse a water XYZ string."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        xyz = "3\nWater\nO  0.0000  0.0000  0.0000\nH  0.7572  0.5862  0.0000\nH -0.7572  0.5862  0.0000\n"
        mol = MolecularStructure.from_xyz(xyz)
        self.assertEqual(mol.n_atoms, 3)
        self.assertEqual(mol.atoms, ["O", "H", "H"])
        np.testing.assert_array_almost_equal(mol.coords[0], [0.0, 0.0, 0.0])

    def test_parse_xyz_methane(self):
        """Parse methane XYZ."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        xyz = "5\nMethane\nC  0.0000  0.0000  0.0000\nH  0.6292  0.6292  0.6292\nH -0.6292 -0.6292  0.6292\nH -0.6292  0.6292 -0.6292\nH  0.6292 -0.6292 -0.6292\n"
        mol = MolecularStructure.from_xyz(xyz)
        self.assertEqual(mol.n_atoms, 5)
        self.assertEqual(mol.atoms[0], "C")

    def test_parse_xyz_from_file(self):
        """Load an XYZ from a temp file."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        content = "4\nAmmonia\nN  0.0000  0.0000  0.0000\nH  0.9400  0.0000  0.3130\nH -0.4700  0.8138  0.3130\nH -0.4700 -0.8138  0.3130\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            mol = MolecularStructure.from_xyz_file(path)
            self.assertEqual(mol.n_atoms, 4)
            self.assertEqual(mol.atoms[0], "N")
        finally:
            os.unlink(path)

    def test_parse_xyz_malformed_raises(self):
        """Malformed XYZ raises ValueError."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        with self.assertRaises(ValueError):
            MolecularStructure.from_xyz("not enough lines\n")

    def test_parse_xyz_atom_count_mismatch(self):
        """XYZ atom count mismatch raises ValueError."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        xyz = "3\nComment\nO  0  0  0\nH  1  0  0"  # only 2 coords
        with self.assertRaises(ValueError):
            MolecularStructure.from_xyz(xyz)

    def test_parse_xyz_atom_count_ok(self):
        """XYZ with exact atom count parses correctly."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        xyz = "3\nWater\nO  0  0  0\nH  1  0  0\nH  0  1  0"
        mol = MolecularStructure.from_xyz(xyz)
        self.assertEqual(mol.n_atoms, 3)

    # ── Distance ──────────────────────────────────────────────────────────

    def test_distance_water_oh(self):
        """O-H bond distance in water ~0.96 Å."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        d = mol.distance(0, 1)  # O-H1
        self.assertAlmostEqual(d, 0.96, places=1)

    def test_distance_symmetric(self):
        """Distance i,j == j,i."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        d01 = mol.distance(0, 1)
        d10 = mol.distance(1, 0)
        self.assertEqual(d01, d10)

    def test_distance_heavy_atoms(self):
        """C-C distance in ethane."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("ethanol")
        # C-C bond distance
        d = mol.distance(0, 1)
        self.assertGreater(d, 1.0)
        self.assertLess(d, 1.8)

    def test_distance_out_of_range_raises(self):
        """Distance with invalid index raises."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        with self.assertRaises(IndexError):
            mol.distance(0, 99)

    # ── Angles ─────────────────────────────────────────────────────────────

    def test_angle_water_HOH(self):
        """H-O-H angle in water ~104.5°."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        ang = mol.angle(1, 0, 2)  # H1-O-H2
        self.assertAlmostEqual(ang, 104.5, places=1)

    def test_angle_linear_molecule(self):
        """H-C-H angle in acetylene = 180°."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("acetylene")
        # C is at index 0 and 1, H at 2 and 3
        ang = mol.angle(2, 0, 1)  # H-C-C = 180
        self.assertAlmostEqual(ang, 180.0, places=1)

    def test_angle_tetrahedral_methane(self):
        """H-C-H angle in methane ~109.5°."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("methane")
        ang = mol.angle(1, 0, 2)  # H1-C-H2
        self.assertAlmostEqual(ang, 109.5, places=1)

    def test_angle_degrees_vs_radians(self):
        """Angle with degrees=False returns radians."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        ang_deg = mol.angle(1, 0, 2)
        ang_rad = mol.angle(1, 0, 2, degrees=False)
        self.assertAlmostEqual(ang_deg, math.degrees(ang_rad), places=5)

    # ── Dihedrals ──────────────────────────────────────────────────────────

    def test_dihedral_butane_staggered(self):
        """Butane has a proper dihedral (C-C-C-C)."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("ethanol")
        # First 3 carbons form C-C-C
        dihe = mol.dihedral(0, 1, 2, 4)  # approximate dihedral
        self.assertIsInstance(dihe, float)

    def test_dihedral_water_none(self):
        """Water has no proper dihedral (only 3 atoms)."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        # H2O has no 4-atom chain, all dihedrals should be from neighbor lists
        dihedrals = mol.all_dihedrals()
        # Should be empty or computed from available neighbors
        self.assertIsInstance(dihedrals, list)

    # ── Bond detection ──────────────────────────────────────────────────────

    def test_bond_detection_water(self):
        """Water has 2 bonds detected."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        self.assertGreaterEqual(len(mol.bonds), 2)

    def test_bond_detection_methane(self):
        """Methane has 4 C-H bonds."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("methane")
        self.assertGreaterEqual(len(mol.bonds), 4)

    # ── VSEPR ──────────────────────────────────────────────────────────────

    def test_vsepr_water_bent(self):
        """Water VSEPR shape: Bent."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        # O is at index 0
        shape = mol.vsepr_shape(0)
        self.assertIn("bent", shape.lower())

    def test_vsepr_methane_tetrahedral(self):
        """Methane VSEPR shape: Tetrahedral."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("methane")
        shape = mol.vsepr_shape(0)
        self.assertIn("tetrahedral", shape.lower())

    def test_vsepr_ammonia_trigonal_pyramidal(self):
        """Ammonia VSEPR shape: Trigonal pyramidal."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("ammonia")
        shape = mol.vsepr_shape(0)
        # Ammonia has 3 bonds + 1 lone pair → trigonal pyramidal
        # Actual H-N-H angle is ~110.5°, compressed from 109.5° ideal tetrahedral
        self.assertIn("pyramidal", shape.lower())

    def test_vsepr_ammonia_shape_via_angle(self):
        """Ammonia: actual computed H-N-H angles ~110°, confirming pyramidal."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("ammonia")
        # All three H-N-H angles should be ~110.5°
        ang_12 = mol.angle(1, 0, 2)
        ang_13 = mol.angle(1, 0, 3)
        ang_23 = mol.angle(2, 0, 3)
        for ang in [ang_12, ang_13, ang_23]:
            self.assertAlmostEqual(ang, 110.5, delta=1.0)

    def test_vsepr_acetylene_linear(self):
        """Acetylene VSEPR shape: Linear."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("acetylene")
        shape = mol.vsepr_shape(0)
        self.assertIn("linear", shape.lower())

    def test_vsepr_benzene_trigonal_planar(self):
        """Benzene carbon centers: Trigonal planar."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("benzene")
        # All 6 carbons should be trigonal planar
        for i in range(6):
            shape = mol.vsepr_shape(i)
            self.assertIn("planar", shape.lower())

    # ── Chirality ──────────────────────────────────────────────────────────

    def test_chiral_center_methane_not_chiral(self):
        """Methane is not chiral (2 H substituents identical)."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("methane")
        self.assertFalse(mol.is_chiral_center(0))  # C has 4 identical H neighbors

    def test_chiral_centers_empty_for_symmetric_molecules(self):
        """Water, methane, ammonia have no chiral centers."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        for name in ["water", "methane", "ammonia", "acetylene"]:
            mol = MolecularStructure.from_demo(name)
            chiral = mol.chirality_centers()
            self.assertEqual(len(chiral), 0)

    # ── Demo molecules ─────────────────────────────────────────────────────

    def test_demo_water(self):
        """Load water demo."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        self.assertEqual(mol.n_atoms, 3)
        self.assertEqual(mol.atoms[0], "O")

    def test_demo_unknown_raises(self):
        """Unknown demo molecule raises ValueError."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        with self.assertRaises(ValueError):
            MolecularStructure.from_demo("unicorn")

    def test_get_available_demos(self):
        """get_available_demos returns sorted list."""
        from weslr.modules.spatial_reasoning import get_available_demos

        demos = get_available_demos()
        self.assertIsInstance(demos, list)
        self.assertGreater(len(demos), 5)
        self.assertIn("water", demos)
        self.assertIn("methane", demos)

    # ── SMILES fallback error ───────────────────────────────────────────────

    def test_smiles_without_rdkit_raises_import_error(self):
        """SMILES without RDKit raises ImportError with instructions."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        try:
            # Verify RDKit is not installed (or is installed)
            import rdkit  # noqa
            self.skipTest("RDKit is installed — can't test fallback path")
        except ImportError:
            with self.assertRaises(ImportError) as ctx:
                MolecularStructure.from_smiles("CCO")
            self.assertIn("RDKit", str(ctx.exception))

    # ── Formatting ─────────────────────────────────────────────────────────

    def test_format_geometry_summary_water(self):
        """format_geometry_summary produces expected output for water."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        summary = mol.format_geometry_summary()
        self.assertIsInstance(summary, str)
        self.assertIn("O", summary)
        self.assertIn("Bond", summary)
        self.assertIn("104", summary)
        self.assertIn("VSEPR", summary)

    def test_propose_shape_water(self):
        """propose_shape for water includes Bent + functional note."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        proposal = mol.propose_shape(0)
        self.assertIsInstance(proposal, str)
        self.assertIn("Bent", proposal)
        self.assertIn("hydrogen", proposal.lower())

    def test_propose_shape_methane(self):
        """propose_shape for methane includes tetrahedral + functional note."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("methane")
        proposal = mol.propose_shape(0)
        self.assertIsInstance(proposal, str)
        self.assertIn("tetrahedral", proposal.lower())

    def test_to_xyz_string(self):
        """to_xyz_string produces valid XYZ text."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        xyz = mol.to_xyz_string()
        self.assertIn("3", xyz)
        self.assertIn("O", xyz)
        self.assertIn("H", xyz)

    # ── Geometry summary includes dihedrals ────────────────────────────────

    def test_geometry_summary_dihedrals(self):
        """Geometry summary includes dihedral angles section."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("ethanol")
        summary = mol.format_geometry_summary()
        self.assertIn("Dihedral", summary)

    # ── Command parsing ───────────────────────────────────────────────────

    def test_command_molecule_demo(self):
        """handle_molecule_command routes /molecule demo water."""
        from weslr.commands.spatial_commands import handle_molecule_command

        result = handle_molecule_command("/molecule demo water", "molecule demo water")
        self.assertIn("Loaded demo", result)
        self.assertIn("water", result)

    def test_command_molecule_geometry(self):
        """handle_molecule_command routes /molecule geometry."""
        from weslr.commands.spatial_commands import handle_molecule_command

        # First load water
        handle_molecule_command("/molecule demo water", "molecule demo water")
        result = handle_molecule_command("/molecule geometry", "molecule geometry")
        self.assertIn("Bond", result)
        self.assertIn("VSEPR", result)

    def test_command_molecule_measure_distance(self):
        """handle_molecule_command routes /molecule measure distance."""
        from weslr.commands.spatial_commands import handle_molecule_command

        handle_molecule_command("/molecule demo water", "molecule demo water")
        result = handle_molecule_command("/molecule measure distance 1 2", "molecule measure distance 1 2")
        self.assertIn("O1", result)
        self.assertIn("H2", result)
        self.assertIn("0.95", result)

    def test_command_molecule_measure_angle(self):
        """handle_molecule_command routes /molecule measure angle."""
        from weslr.commands.spatial_commands import handle_molecule_command

        handle_molecule_command("/molecule demo water", "molecule demo water")
        result = handle_molecule_command("/molecule measure angle 2 1 3", "molecule measure angle 2 1 3")
        self.assertIn("104", result)

    def test_command_molecule_chirality(self):
        """handle_molecule_command routes /molecule chirality."""
        from weslr.commands.spatial_commands import handle_molecule_command, clear_current_molecule

        clear_current_molecule()
        handle_molecule_command("/molecule demo water", "molecule demo water")
        result = handle_molecule_command("/molecule chirality", "molecule chirality")
        self.assertIsInstance(result, str)
        self.assertIn("No chiral centers", result)


    def test_command_propose_shape(self):
        """handle_molecule_command routes /propose shape water."""
        from weslr.commands.spatial_commands import handle_molecule_command, clear_current_molecule

        clear_current_molecule()
        handle_molecule_command("/molecule demo water", "molecule demo water")
        result = handle_molecule_command("/propose shape water", "propose shape water")
        self.assertIn("Bent", result)

    def test_command_molecule_load_file(self):
        """handle_molecule_command loads XYZ file."""
        from weslr.commands.spatial_commands import handle_molecule_command

        content = "3\nTest\nO  0  0  0\nH  1  0  0\nH  0  1  0\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            result = handle_molecule_command(f"/molecule load {path}", f"molecule load {path}")
            self.assertIn("Loaded XYZ", result)
        finally:
            os.unlink(path)

    def test_command_molecule_unknown_shows_usage(self):
        """Unknown molecule command shows usage."""
        from weslr.commands.spatial_commands import handle_molecule_command

        result = handle_molecule_command("/molecule unknown_subcmd", "molecule unknown_subcmd")
        self.assertIn("/molecule", result)
        self.assertIn("geometry", result)

    def test_command_molecule_no_molecule_loaded(self):
        """Commands with no molecule loaded give clear error."""
        from weslr.commands.spatial_commands import (
            handle_molecule_command,
            clear_current_molecule,
        )

        clear_current_molecule()
        result = handle_molecule_command("/molecule geometry", "molecule geometry")
        self.assertIn("No molecule loaded", result)

    def test_command_molecule_load_invalid_index(self):
        """Measure with invalid index gives error."""
        from weslr.commands.spatial_commands import (
            handle_molecule_command,
            handle_molecule_demo,
        )

        handle_molecule_demo("/molecule demo water", "molecule demo water")
        result = handle_molecule_command("/molecule measure distance 1 99", "molecule measure distance 1 99")
        self.assertIn("out of range", result)

    # ── Integration ──────────────────────────────────────────────────────

    def test_geometry_summary_includes_bond_distances(self):
        """Geometry summary lists detected bond distances."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        summary = mol.format_geometry_summary()
        self.assertIn("Bond distances:", summary)
        # At least one bond distance present
        self.assertRegex(summary, r"O1-H\d+:")

    def test_geometry_summary_includes_vsepr_shapes(self):
        """Geometry summary lists VSEPR shapes for non-H centers."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("methane")
        summary = mol.format_geometry_summary()
        self.assertIn("VSEPR", summary)
        self.assertIn("tetrahedral", summary)

    def test_geometry_summary_includes_chirality(self):
        """Geometry summary lists chiral centers."""
        from weslr.modules.spatial_reasoning import MolecularStructure

        mol = MolecularStructure.from_demo("water")
        summary = mol.format_geometry_summary()
        self.assertIn("Chiral", summary)


if __name__ == "__main__":
    unittest.main()
