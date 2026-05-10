import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from weslr.file_router import create_file_router
from weslr.scientific_structure_ingestion import inspect_scientific_structure_file
from weslr.sqlite_ingestion import inspect_sqlite_database


class TestFileDataInterpretationV1(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.router = create_file_router(workspace_dir=str(self.workspace))

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make_sqlite_db(self, name: str = "sample.sqlite") -> Path:
        path = self.workspace / name
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE compounds (id INTEGER PRIMARY KEY, name TEXT, formula TEXT)")
        conn.execute("INSERT INTO compounds (name, formula) VALUES (?, ?)", ("water", "H2O"))
        conn.execute("CREATE TABLE measurements (compound_id INTEGER, value REAL)")
        conn.execute("INSERT INTO measurements (compound_id, value) VALUES (?, ?)", (1, 1.23))
        conn.commit()
        conn.close()
        return path

    def test_sqlite_read_only_inspection_returns_summary(self):
        path = self._make_sqlite_db()
        result = inspect_sqlite_database(str(path), workspace_dir=str(self.workspace))

        self.assertEqual(result["type"], "sqlite_database")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["table_count"], 2)
        table_names = [table["name"] for table in result["tables"]]
        self.assertEqual(table_names, ["compounds", "measurements"])
        compounds = result["tables"][0]
        column_names = [column["name"] for column in compounds["columns"]]
        self.assertIn("name", column_names)
        self.assertIn("formula", column_names)
        self.assertIn("read_only: true", result["summary"])

    def test_sqlite_inspection_does_not_mutate_db(self):
        path = self._make_sqlite_db("sample.db")
        before = path.read_bytes()
        before_mtime = path.stat().st_mtime_ns

        result = inspect_sqlite_database(str(path), workspace_dir=str(self.workspace))

        after = path.read_bytes()
        after_mtime = path.stat().st_mtime_ns
        self.assertTrue(result["read_only"])
        self.assertEqual(before, after)
        self.assertEqual(before_mtime, after_mtime)

    def test_xyz_file_returns_atom_and_species_summary(self):
        path = self.workspace / "water.xyz"
        path.write_text(
            "3\nwater\nO 0.000000 0.000000 0.000000\nH 0.757000 0.586000 0.000000\nH -0.757000 0.586000 0.000000\n",
            encoding="utf-8",
        )

        result = inspect_scientific_structure_file(str(path), workspace_dir=str(self.workspace))
        self.assertEqual(result["type"], "xyz_structure")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["atom_count"], 3)
        self.assertEqual(result["species_counts"], {"H": 2, "O": 1})
        self.assertEqual(result["formula"], "H2O")

    def test_cif_file_returns_cell_and_formula_metadata(self):
        path = self.workspace / "nacl.cif"
        path.write_text(
            "data_test\n_cell_length_a 5.6402\n_cell_length_b 5.6402\n_cell_length_c 5.6402\n_cell_angle_alpha 90\n_cell_angle_beta 90\n_cell_angle_gamma 90\n_chemical_formula_sum 'Na Cl'\nloop_\n_atom_site_type_symbol\n_atom_site_label\nNa Na1\nCl Cl1\n",
            encoding="utf-8",
        )

        result = inspect_scientific_structure_file(str(path), workspace_dir=str(self.workspace))
        self.assertEqual(result["type"], "cif_structure")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["species_counts"], {"Cl": 1, "Na": 1})
        self.assertEqual(result["cell_parameters"]["a"], 5.6402)
        self.assertIn("Na Cl", result["formula"])

    def test_poscar_file_returns_species_count_and_lattice(self):
        path = self.workspace / "POSCAR"
        path.write_text(
            "SiO2\n1.0\n5.0 0.0 0.0\n0.0 5.0 0.0\n0.0 0.0 5.0\nSi O\n1 2\nDirect\n0.0 0.0 0.0\n0.5 0.5 0.5\n0.25 0.25 0.25\n",
            encoding="utf-8",
        )

        result = inspect_scientific_structure_file(str(path), workspace_dir=str(self.workspace))
        self.assertEqual(result["type"], "poscar_structure")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["atom_count"], 3)
        self.assertEqual(result["species_counts"], {"Si": 1, "O": 2})
        self.assertEqual(result["formula"], "O2Si")
        self.assertEqual(result["cell_parameters"]["a"], 5.0)
        self.assertEqual(result["cell_parameters"]["gamma"], 90.0)

    def test_file_router_routes_sqlite_files(self):
        sqlite_path = self._make_sqlite_db("router.sqlite")
        db_path = self._make_sqlite_db("router.db")

        sqlite_result = self.router.route(str(sqlite_path))
        db_result = self.router.route(str(db_path))

        self.assertEqual(sqlite_result.category, "sqlite")
        self.assertEqual(db_result.category, "sqlite")
        self.assertTrue(sqlite_result.read_only)
        self.assertTrue(db_result.read_only)
        self.assertEqual(sqlite_result.metadata["table_count"], 2)

    def test_file_router_routes_scientific_structure_files(self):
        xyz_path = self.workspace / "methane.xyz"
        xyz_path.write_text(
            "5\nmethane\nC 0 0 0\nH 1 0 0\nH -1 0 0\nH 0 1 0\nH 0 -1 0\n",
            encoding="utf-8",
        )
        cif_path = self.workspace / "test.cif"
        cif_path.write_text(
            "data_t\n_cell_length_a 4\n_cell_length_b 4\n_cell_length_c 4\n_chemical_formula_sum 'C H4'\nloop_\n_atom_site_type_symbol\nC\nH\nH\nH\nH\n",
            encoding="utf-8",
        )
        poscar_path = self.workspace / "POSCAR"
        poscar_path.write_text(
            "C\n1.0\n4 0 0\n0 4 0\n0 0 4\nC\n1\nDirect\n0 0 0\n",
            encoding="utf-8",
        )

        xyz_result = self.router.route(str(xyz_path))
        cif_result = self.router.route(str(cif_path))
        poscar_result = self.router.route(str(poscar_path))

        self.assertEqual(xyz_result.category, "scientific_structure")
        self.assertEqual(cif_result.category, "scientific_structure")
        self.assertEqual(poscar_result.category, "scientific_structure")
        self.assertTrue(xyz_result.read_only)
        self.assertTrue(cif_result.read_only)
        self.assertTrue(poscar_result.read_only)
        self.assertEqual(xyz_result.metadata["atom_count"], 5)

    def test_bad_scientific_file_returns_safe_warning(self):
        path = self.workspace / "broken.cif"
        path.write_text("data_bad\nloop_\n_atom_site_type_symbol\n", encoding="utf-8")

        result = inspect_scientific_structure_file(str(path), workspace_dir=str(self.workspace))

        self.assertEqual(result["type"], "cif_structure")
        self.assertTrue(result["read_only"])
        self.assertIn("warnings", result)
        self.assertIn("read_only: true", result["summary"])

    def test_existing_json_csv_and_text_routing_still_works(self):
        json_path = self.workspace / "sample.json"
        json_path.write_text(json.dumps({"name": "alpha", "items": [1, 2]}), encoding="utf-8")
        csv_path = self.workspace / "sample.csv"
        csv_path.write_text("name,value\nalpha,1\n", encoding="utf-8")
        text_path = self.workspace / "notes.txt"
        text_path.write_text("hello file router", encoding="utf-8")

        json_result = self.router.route(str(json_path), "what is this?")
        csv_result = self.router.route(str(csv_path), "what is this?")
        text_result = self.router.route(str(text_path), "what is this?")

        self.assertEqual(json_result.category, "structured")
        self.assertEqual(csv_result.category, "structured")
        self.assertEqual(text_result.category, "text")
        self.assertTrue(json_result.read_only)
        self.assertTrue(csv_result.read_only)
        self.assertTrue(text_result.read_only)


if __name__ == "__main__":
    unittest.main()
