#!/usr/bin/env python3
"""
WESLR JSONL Archiver Tests V1
Uses temporary directories and files only — does not touch real weslr/*.jsonl.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

_workspace = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_workspace))
sys.path.insert(0, str(_workspace / "weslr"))

from weslr.jsonl_archive_policy import (
    classify_jsonl_file,
    get_jsonl_archive_policy,
    plan_jsonl_archives,
)
from weslr.jsonl_archiver import archive_jsonl_file, archive_jsonl_files


class TestJsonlArchivePolicy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_classify_allowed_files(self):
        allowed = [
            "weslr/public_signals.jsonl",
            "weslr/contract_observations.jsonl",
            "weslr/operator_feedback_log.jsonl",
            "weslr/iss/iss_diagnostic_records.jsonl",
        ]
        for p in allowed:
            result = classify_jsonl_file(p)
            self.assertTrue(result["archive_allowed"], f"{p} should be allowed")
            self.assertEqual(result["reason"], "allowed_low_risk")

    def test_classify_protected_governance(self):
        protected = [
            "weslr/contract_insufficiency_log.jsonl",
            "weslr/contract_proposal_review_log.jsonl",
            "weslr/proposal_trace.jsonl",
            "weslr/implementation_plans.jsonl",
        ]
        for p in protected:
            result = classify_jsonl_file(p)
            self.assertFalse(result["archive_allowed"], f"{p} should be protected")
            self.assertEqual(result["reason"], "protected_governance")

    def test_classify_unknown_file(self):
        result = classify_jsonl_file("weslr/nonexistent.jsonl")
        self.assertFalse(result["archive_allowed"])
        self.assertEqual(result["reason"], "unknown_file")

        result2 = classify_jsonl_file("weslr/some_new_file.jsonl")
        self.assertFalse(result2["archive_allowed"])
        self.assertEqual(result2["reason"], "unknown_file")

    def test_get_policy_returns_structure(self):
        policy = get_jsonl_archive_policy()
        self.assertEqual(policy["version"], "v1")
        self.assertGreater(policy["default_threshold_lines"], 0)
        self.assertGreater(policy["default_keep_tail_lines"], 0)
        self.assertEqual(len(policy["allowed_low_risk"]), 4)
        self.assertEqual(len(policy["protected_governance"]), 4)


class TestJsonlArchiverPlanOnly(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def _make_jsonl(self, name: str, lines: list[str]) -> Path:
        # name is relative like "weslr/public_signals.jsonl"
        p = Path(self.tmp) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            for line in lines:
                fh.write(json.dumps(line) + "\n")
        return p

    def test_plan_does_not_write(self):
        # Create file at self.tmp/weslr/public_signals.jsonl
        # plan_jsonl_archives scans root=tmp and finds it via rglob
        # It then computes relative_to(tmp) -> "weslr/public_signals.jsonl"
        # which classify_jsonl_file can match against allowed_low_risk
        fake_root = Path(self.tmp)  # root is the temp dir itself
        weslr_dir = fake_root / "weslr"
        weslr_dir.mkdir()
        p = weslr_dir / "public_signals.jsonl"
        with open(p, "w", encoding="utf-8") as fh:
            for item in [{"a": 1}] * 10:
                fh.write(json.dumps(item) + "\n")

        plan = plan_jsonl_archives(root=str(fake_root))
        pub_plan = next((p for p in plan["plans"] if "public_signals" in p["path"]), None)
        self.assertIsNotNone(pub_plan, f"public_signals not found in plans: {[pl['path'] for pl in plan['plans']]}")
        self.assertEqual(pub_plan["status"], "skipped")
        self.assertEqual(pub_plan["skip_reason"], "below_threshold")

    def test_plan_below_threshold_skipped(self):
        fake_root = Path(self.tmp)  # root = temp dir
        weslr_dir = fake_root / "weslr"
        weslr_dir.mkdir()
        p = weslr_dir / "public_signals.jsonl"
        with open(p, "w", encoding="utf-8") as fh:
            for item in [{"x": i} for i in range(5)]:
                fh.write(json.dumps(item) + "\n")

        plan = plan_jsonl_archives(root=str(fake_root), threshold_lines=1000)
        pub_plan = next((p for p in plan["plans"] if "public_signals" in p["path"]), None)
        self.assertIsNotNone(pub_plan)
        self.assertEqual(pub_plan["status"], "skipped")
        self.assertEqual(pub_plan["skip_reason"], "below_threshold")
        self.assertEqual(pub_plan["line_count"], 5)


class TestJsonlArchiverArchive(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def _make_jsonl(self, name: str, lines: list[str]) -> Path:
        # name is relative like "weslr/public_signals.jsonl"
        p = Path(self.tmp) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            for line in lines:
                fh.write(json.dumps(line) + "\n")
        return p

    def test_dry_run_does_not_modify_file(self):
        # Create file at self.tmp/weslr/public_signals.jsonl
        p = self._make_jsonl("weslr/public_signals.jsonl", [{"i": i} for i in range(1200)])
        orig_content = p.read_bytes()

        # Pass the absolute path so the archiver finds it
        result = archive_jsonl_file(
            str(p),
            archive_root=str(Path(self.tmp) / "archive"),
            threshold_lines=1000,
            keep_tail_lines=300,
            dry_run=True,
        )

        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["dry_run"], True)
        self.assertEqual(p.read_bytes(), orig_content)

    def test_real_archive_creates_archive_and_keeps_tail(self):
        archive_root = Path(self.tmp) / "archive"
        p = self._make_jsonl("weslr/public_signals.jsonl", [{"i": i} for i in range(1200)])

        result = archive_jsonl_file(
            str(p),  # absolute path; classify uses suffix matching so "weslr/..." matches
            archive_root=str(archive_root),
            threshold_lines=1000,
            keep_tail_lines=300,
            dry_run=False,
        )

        self.assertEqual(result["status"], "archived")
        self.assertEqual(result["kept_line_count"], 300)
        self.assertEqual(result["archived_line_count"], 900)
        self.assertIsNotNone(result["sha256_archive"])
        self.assertIsNotNone(result["sha256_after"])

        with open(p) as fh:
            active_lines = [l for l in fh if l.strip()]
        self.assertEqual(len(active_lines), 300)

        archive_file = Path(result["archive_file"])
        self.assertTrue(archive_file.exists())
        with open(archive_file) as fh:
            archived_lines = [l for l in fh if l.strip()]
        self.assertEqual(len(archived_lines), 900)

        manifest_file = archive_file.parent / "manifest.jsonl"
        self.assertTrue(manifest_file.exists())
        with open(manifest_file) as fh:
            manifest = json.loads(fh.read().strip())
        # source_file is the path as passed; classify normalizes it for classification
        self.assertEqual(manifest["source_file"], str(p))
        self.assertIsNotNone(manifest["sha256_before"])

    def test_protected_file_never_archived_even_above_threshold(self):
        p = self._make_jsonl("weslr/proposal_trace.jsonl", [{"i": i} for i in range(1200)])
        orig_content = p.read_bytes()

        result = archive_jsonl_file(
            str(p),
            archive_root=str(Path(self.tmp) / "archive"),
            threshold_lines=100,
            keep_tail_lines=50,
            dry_run=False,
        )

        self.assertIn(result["status"], ("skipped_protected", "skipped_unknown"))
        self.assertEqual(p.read_bytes(), orig_content)

    def test_unknown_file_never_archived(self):
        p = self._make_jsonl("weslr/unknown_file.jsonl", [{"i": i} for i in range(1200)])
        orig_content = p.read_bytes()

        result = archive_jsonl_file(
            str(p),
            archive_root=str(Path(self.tmp) / "archive"),
            threshold_lines=100,
            keep_tail_lines=50,
            dry_run=False,
        )

        self.assertIn(result["status"], ("skipped_protected", "skipped_unknown"))
        self.assertEqual(p.read_bytes(), orig_content)

    def test_archive_manifest_has_required_fields(self):
        archive_root = Path(self.tmp) / "archive"
        p = self._make_jsonl("weslr/contract_observations.jsonl", [{"i": i} for i in range(1100)])

        result = archive_jsonl_file(
            str(p),
            archive_root=str(archive_root),
            threshold_lines=1000,
            keep_tail_lines=300,
            dry_run=False,
        )

        required_fields = [
            "source_file",
            "archive_file",
            "original_line_count",
            "archived_line_count",
            "kept_line_count",
            "sha256_before",
            "sha256_archive",
            "sha256_after",
            "timestamp",
            "dry_run",
            "status",
        ]
        for field in required_fields:
            self.assertIn(field, result, f"manifest missing field: {field}")

    def test_archive_jsonl_files_batch_dry_run(self):
        # Create files at self.tmp/weslr/<name>
        p1 = self._make_jsonl("weslr/public_signals.jsonl", [{"i": i} for i in range(1200)])
        p2 = self._make_jsonl("weslr/contract_observations.jsonl", [{"i": i} for i in range(1200)])
        p3 = self._make_jsonl("weslr/proposal_trace.jsonl", [{"i": i} for i in range(1200)])

        results = archive_jsonl_files(
            paths=[str(p1), str(p2), str(p3)],
            archive_root=str(Path(self.tmp) / "archive"),
            threshold_lines=1000,
            keep_tail_lines=300,
            dry_run=True,
        )

        self.assertEqual(results["dry_run"], True)
        self.assertGreaterEqual(results["summary"]["planned"], 2)
        # protected should be skipped
        self.assertGreaterEqual(results["summary"]["skipped_protected"], 1)

    def test_no_deletion_of_archived_records(self):
        """Verify archived lines exist in archive file, not deleted."""
        archive_root = Path(self.tmp) / "archive"
        p = self._make_jsonl("weslr/public_signals.jsonl", [{"i": i} for i in range(1100)])

        result = archive_jsonl_file(
            str(p),
            archive_root=str(archive_root),
            threshold_lines=1000,
            keep_tail_lines=300,
            dry_run=False,
        )

        archive_file = Path(result["archive_file"])
        with open(archive_file) as fh:
            archived_data = [json.loads(l) for l in fh if l.strip()]

        # All 800 archived lines should be present
        self.assertEqual(len(archived_data), 800)
        # Verify content (line 0 should be {"i": 0})
        self.assertEqual(archived_data[0], {"i": 0})
        self.assertEqual(archived_data[-1], {"i": 799})

    def test_sha256_checksums_present(self):
        archive_root = Path(self.tmp) / "archive"
        p = self._make_jsonl("weslr/contract_observations.jsonl", [{"i": i} for i in range(1100)])

        result = archive_jsonl_file(
            str(p),
            archive_root=str(archive_root),
            threshold_lines=1000,
            keep_tail_lines=300,
            dry_run=False,
        )

        self.assertIsNotNone(result.get("sha256_before"))
        self.assertIsNotNone(result.get("sha256_archive"))
        self.assertIsNotNone(result.get("sha256_after"))
        # All should be 64-char hex strings
        for field in ["sha256_before", "sha256_archive", "sha256_after"]:
            self.assertEqual(len(result[field]), 64)


class TestJsonlArchiverNoOllama(unittest.TestCase):
    def test_no_ollama_imports(self):
        """Verify neither archiver nor policy imports Ollama."""
        import ast
        import inspect

        for module in ["weslr.jsonl_archive_policy", "weslr.jsonl_archiver"]:
            src = inspect.getsource(sys.modules[module])
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(
                            "ollama",
                            alias.name.lower(),
                            f"{module} imports ollama",
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.assertNotIn(
                            "ollama",
                            node.module.lower(),
                            f"{module} imports from ollama",
                        )


if __name__ == "__main__":
    unittest.main()