import json
import os
import sqlite3
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from weslr.file_router import create_file_router


class TestFileDataInterpretationScorecardV1(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.router = create_file_router(workspace_dir=str(self.workspace))

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make_sqlite_db(self, name: str = "score.sqlite") -> Path:
        path = self.workspace / name
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE compounds (id INTEGER PRIMARY KEY, name TEXT, formula TEXT)")
        conn.execute("INSERT INTO compounds (name, formula) VALUES (?, ?)", ("water", "H2O"))
        conn.commit()
        conn.close()
        return path

    def _make_xyz(self) -> Path:
        path = self.workspace / "water.xyz"
        path.write_text(
            "3\nwater\nO 0 0 0\nH 0 0 1\nH 1 0 0\n",
            encoding="utf-8",
        )
        return path

    def _make_cif(self) -> Path:
        path = self.workspace / "sample.cif"
        path.write_text(
            "data_test\n_cell_length_a 5.0\n_cell_length_b 5.0\n_cell_length_c 5.0\n_cell_angle_alpha 90\n_cell_angle_beta 90\n_cell_angle_gamma 90\n_chemical_formula_sum 'Ca Sc2 Ti O6'\nloop_\n_atom_site_type_symbol\nCa\nSc\nSc\nTi\nO\nO\nO\nO\nO\nO\n",
            encoding="utf-8",
        )
        return path

    def _make_poscar(self) -> Path:
        path = self.workspace / "POSCAR"
        path.write_text(
            "CaSc2TiO6\n1.0\n5.0 0.0 0.0\n0.0 5.0 0.0\n0.0 0.0 5.0\nCa Sc Ti O\n1 2 1 6\nDirect\n0 0 0\n0.25 0.25 0.25\n0.5 0.5 0.5\n0.75 0.75 0.75\n0.1 0.1 0.1\n0.2 0.2 0.2\n0.3 0.3 0.3\n0.4 0.4 0.4\n0.5 0.5 0.5\n0.6 0.6 0.6\n",
            encoding="utf-8",
        )
        return path

    def _make_json(self) -> Path:
        path = self.workspace / "sample.json"
        path.write_text(json.dumps({"name": "alpha", "items": [1, 2]}), encoding="utf-8")
        return path

    def _make_csv(self) -> Path:
        path = self.workspace / "sample.csv"
        path.write_text("name,value\nalpha,1\n", encoding="utf-8")
        return path

    def _make_markdown(self) -> Path:
        path = self.workspace / "notes.md"
        path.write_text("# Notes\nhello file router\n", encoding="utf-8")
        return path

    def _make_fits_placeholder(self) -> Path:
        path = self.workspace / "sample.fits"
        path.write_bytes(b"not-a-real-fits")
        self.router._fits_ingestion = types.SimpleNamespace(
            FITSIngestionError=Exception,
            create_fits_ingestor=lambda workspace_dir=None: types.SimpleNamespace(
                ingest=lambda filepath, user_query="", task_context=None: {
                    "file_type": ".fits",
                    "category": "fits_dataset",
                    "relevance": "high",
                    "relevance_reason": "FITS dataset ingested",
                    "metadata": {
                        "source_file": Path(filepath).name,
                        "parsed_successfully": True,
                        "parse_error": None,
                        "width": 12,
                        "height": 34,
                    },
                    "structured_output": "[FITS DATASET INGESTION]\nread_only: true\nDimensions: 12 x 34 pixels",
                    "parsed_data": {
                        "width": 12,
                        "height": 34,
                        "analysis_type": "fits_ingestion",
                        "fits_info": {
                            "naxis": 2,
                            "object": "TestObject",
                            "telescope": "TestScope",
                            "instrument": "TestCam",
                        },
                    },
                }
            ),
        )
        return path

    def _make_scientific_hint_zip(self) -> Path:
        path = self.workspace / "bundle.zip"
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr("tia/export.json", "{}")
            zf.writestr("plc/tags.json", "{}")
            zf.writestr("structures/POSCAR", "Si\n1.0\n1 0 0\n0 1 0\n0 0 1\nSi\n1\nDirect\n0 0 0\n")
            zf.writestr("data/sample.fits", "placeholder")
            zf.writestr("materials/sample.cif", "data_x")
        return path

    def _make_unsafe_zip(self) -> Path:
        path = self.workspace / "unsafe.zip"
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr("../evil.txt", "nope")
            zf.writestr("safe/readme.md", "ok")
        return path

    def _workspace_snapshot(self):
        return sorted(
            str(p.relative_to(self.workspace))
            for p in self.workspace.rglob("*")
        )

    def _run_case(self, name: str, path: Path, expected_category: str, extra_check=None):
        before_snapshot = self._workspace_snapshot()
        before_mtime = path.stat().st_mtime_ns
        result = self.router.route(str(path), "scorecard")
        after_snapshot = self._workspace_snapshot()
        after_mtime = path.stat().st_mtime_ns

        warnings = []
        if "warnings:" in result.content:
            warnings.append(result.content.split("warnings:", 1)[1].strip())
        if result.metadata.get("parse_error"):
            warnings.append(str(result.metadata["parse_error"]))

        case = {
            "name": name,
            "status": "passed",
            "category": result.category,
            "expected_category": expected_category,
            "read_only": result.read_only,
            "safety_warnings": warnings,
            "missing_capabilities": [],
        }

        try:
            self.assertEqual(result.category, expected_category)
            self.assertTrue(result.read_only)
            self.assertEqual(before_snapshot, after_snapshot)
            self.assertEqual(before_mtime, after_mtime)
            if extra_check:
                extra_check(result, case)
        except AssertionError as exc:
            case["status"] = "failed"
            case["missing_capabilities"].append(str(exc))

        return case

    def test_file_data_interpretation_scorecard_v1(self):
        cases = []

        json_path = self._make_json()
        cases.append(self._run_case("json", json_path, "structured"))

        csv_path = self._make_csv()
        cases.append(self._run_case("csv", csv_path, "structured"))

        md_path = self._make_markdown()
        cases.append(self._run_case("markdown", md_path, "text"))

        sqlite_path = self._make_sqlite_db()
        cases.append(self._run_case(
            "sqlite",
            sqlite_path,
            "sqlite",
            extra_check=lambda result, case: self.assertGreaterEqual(result.metadata.get("table_count", 0), 1),
        ))

        xyz_path = self._make_xyz()
        cases.append(self._run_case(
            "xyz",
            xyz_path,
            "scientific_structure",
            extra_check=lambda result, case: self.assertGreaterEqual(result.metadata.get("atom_count", 0), 3),
        ))

        cif_path = self._make_cif()
        cases.append(self._run_case(
            "cif",
            cif_path,
            "scientific_structure",
            extra_check=lambda result, case: self.assertIn("formula", result.metadata),
        ))

        poscar_path = self._make_poscar()
        cases.append(self._run_case(
            "poscar",
            poscar_path,
            "scientific_structure",
            extra_check=lambda result, case: self.assertGreaterEqual(result.metadata.get("atom_count", 0), 1),
        ))

        fits_path = self._make_fits_placeholder()
        cases.append(self._run_case(
            "fits",
            fits_path,
            "fits",
            extra_check=lambda result, case: self.assertIn("fits_dataset", result.labels),
        ))
        self.router._fits_ingestion = None

        archive_path = self._make_scientific_hint_zip()
        cases.append(self._run_case(
            "archive_hints",
            archive_path,
            "archive",
            extra_check=lambda result, case: (
                self.assertIn("scientific_dataset_bundle_candidate", result.metadata.get("package_hints", [])),
                self.assertIn("industrial_tia_export_candidate", result.metadata.get("package_hints", [])),
            ),
        ))

        unsafe_archive_path = self._make_unsafe_zip()
        cases.append(self._run_case(
            "archive_unsafe",
            unsafe_archive_path,
            "archive",
            extra_check=lambda result, case: self.assertGreaterEqual(result.metadata.get("unsafe_entry_count", 0), 1),
        ))

        total_cases = len(cases)
        passed_cases = sum(1 for case in cases if case["status"] == "passed")
        score = passed_cases / total_cases if total_cases else 0.0
        missing = [
            {"name": case["name"], "issues": case["missing_capabilities"]}
            for case in cases
            if case["missing_capabilities"]
        ]

        scorecard = {
            "total_cases": total_cases,
            "passed_cases": passed_cases,
            "score": round(score, 3),
            "per_case_status": cases,
            "missing_capabilities": missing,
        }

        print(json.dumps(scorecard, indent=2))

        self.assertGreaterEqual(score, 0.85)
        self.assertEqual(passed_cases, total_cases)
        self.assertTrue(all(case["read_only"] for case in cases))
        unsafe_case = next(case for case in cases if case["name"] == "archive_unsafe")
        self.assertEqual(unsafe_case["status"], "passed")


if __name__ == "__main__":
    unittest.main()
