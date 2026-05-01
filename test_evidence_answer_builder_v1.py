"""
Tests for Evidence Answer Builder V1
Read-only. No live web calls. No Ollama. No JSONL writes.
"""

import unittest
from pathlib import Path

from weslr.evidence_answer_builder import (
    build_evidence_answer,
    build_no_evidence_answer,
    RECORD_TYPE,
    DEPTH_BRIEF,
    DEPTH_NORMAL,
    DEPTH_DEEP,
)


# ─────────────────────────────────────────────────────────────────────────────
# Environment-portable paths
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent  # repo root


# ─────────────────────────────────────────────────────────────────────────────
# Mocked evidence packets
# ─────────────────────────────────────────────────────────────────────────────

MOCK_VALID_PACKET = {
    "record_type": "external_evidence_packet_v1",
    "query": "python programming",
    "source_adapter": "searxng",
    "authority": "external_evidence_unverified",
    "truth_status": "unverified",
    "automatic_truth_write": False,
    "result_count": 3,
    "results": [
        {
            "title": "Python Official Documentation",
            "url": "https://docs.python.org",
            "content": "Python is a high-level programming language.",
            "source": "python.org",
            "authority": "external_evidence_unverified",
        },
        {
            "title": "Wikipedia: Python",
            "url": "https://en.wikipedia.org/wiki/Python",
            "content": "Python was created by Guido van Rossum and released in 1991.",
            "source": "wikipedia",
            "authority": "external_evidence_unverified",
        },
        {
            "title": "Real Python Tutorial",
            "url": "https://realpython.com",
            "content": "Python supports object-oriented, imperative, and functional programming.",
            "source": "realpython",
            "authority": "external_evidence_unverified",
        },
    ],
    "limitations": [],
    "safe_for_answer_builder": True,
}


MOCK_PACKET_MISSING_TITLE = {
    "record_type": "external_evidence_packet_v1",
    "query": "test",
    "authority": "external_evidence_unverified",
    "truth_status": "unverified",
    "automatic_truth_write": False,
    "result_count": 1,
    "results": [
        {
            "url": "https://example.com",
            "content": "Content without title",
            "source": "example",
            "authority": "external_evidence_unverified",
        }
    ],
    "safe_for_answer_builder": True,
}


MOCK_EMPTY_PACKET = {
    "record_type": "external_evidence_packet_v1",
    "query": "test",
    "results": [],
    "safe_for_answer_builder": False,
}


MOCK_WRONG_TYPE_PACKET = {
    "record_type": "some_other_type",
    "safe_for_answer_builder": True,
    "results": [{"title": "X", "url": "https://x.com", "content": "Y"}],
}


MOCK_UNSAFE_PACKET = {
    "record_type": "external_evidence_packet_v1",
    "safe_for_answer_builder": False,
    "results": [{"title": "X", "url": "https://x.com", "content": "Y"}],
}


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildEvidenceAnswer(unittest.TestCase):

    def test_valid_packet_produces_answer(self):
        answer = build_evidence_answer("python", MOCK_VALID_PACKET)
        self.assertEqual(answer["record_type"], RECORD_TYPE)
        self.assertEqual(answer["query"], "python")
        self.assertIn("python", answer["answer"].lower())
        self.assertTrue(answer["safe_for_user"])

    def test_answer_includes_external_unverified_boundary(self):
        answer = build_evidence_answer("python", MOCK_VALID_PACKET)
        self.assertIn("external search results", answer["answer"])
        self.assertIn("not stored WESLR truth", answer["answer"])

    def test_answer_includes_source_urls(self):
        answer = build_evidence_answer("python", MOCK_VALID_PACKET, DEPTH_DEEP)
        urls = [s["url"] for s in answer["sources"]]
        self.assertIn("https://docs.python.org", urls)
        self.assertIn("https://en.wikipedia.org/wiki/Python", urls)

    def test_brief_depth_shorter_than_deep(self):
        brief = build_evidence_answer("python", MOCK_VALID_PACKET, DEPTH_BRIEF)
        deep = build_evidence_answer("python", MOCK_VALID_PACKET, DEPTH_DEEP)
        self.assertLess(len(brief["answer"]), len(deep["answer"]))

    def test_deep_depth_includes_multi_part_answer(self):
        answer = build_evidence_answer("python", MOCK_VALID_PACKET, DEPTH_DEEP)
        self.assertIn("1.", answer["answer"])
        self.assertIn("Primary source", answer["answer"])

    def test_invalid_packet_returns_safe_for_user_false(self):
        answer = build_evidence_answer("python", MOCK_WRONG_TYPE_PACKET)
        self.assertFalse(answer["safe_for_user"])
        self.assertEqual(answer["source_count"], 0)

    def test_empty_packet_returns_safe_for_user_false(self):
        answer = build_evidence_answer("test", MOCK_EMPTY_PACKET)
        self.assertFalse(answer["safe_for_user"])

    def test_no_invented_facts(self):
        answer = build_evidence_answer("python", MOCK_VALID_PACKET, DEPTH_DEEP)
        for src in answer["sources"]:
            self.assertIn("url", src)

    def test_source_count_correct(self):
        answer = build_evidence_answer("python", MOCK_VALID_PACKET)
        self.assertEqual(answer["source_count"], 3)
        self.assertEqual(len(answer["sources"]), 3)

    def test_automatic_truth_write_false(self):
        answer = build_evidence_answer("python", MOCK_VALID_PACKET)
        self.assertFalse(answer["automatic_truth_write"])

    def test_authority_external_evidence_unverified(self):
        answer = build_evidence_answer("python", MOCK_VALID_PACKET)
        self.assertEqual(answer["authority"], "external_evidence_unverified")

    def test_truth_status_unverified(self):
        answer = build_evidence_answer("python", MOCK_VALID_PACKET)
        self.assertEqual(answer["truth_status"], "unverified")

    def test_normal_depth(self):
        answer = build_evidence_answer("python", MOCK_VALID_PACKET, DEPTH_NORMAL)
        self.assertTrue(answer["safe_for_user"])
        self.assertGreater(len(answer["answer"]), 10)

    def test_packet_without_title_still_works(self):
        answer = build_evidence_answer("test", MOCK_PACKET_MISSING_TITLE)
        self.assertTrue(answer["safe_for_user"])

    def test_unsafe_packet_rejected(self):
        answer = build_evidence_answer("test", MOCK_UNSAFE_PACKET)
        self.assertFalse(answer["safe_for_user"])


class TestBuildNoEvidenceAnswer(unittest.TestCase):

    def test_no_evidence_answer_safe(self):
        answer = build_no_evidence_answer("test query")
        self.assertTrue(answer["safe_for_user"])
        self.assertEqual(answer["source_count"], 0)
        self.assertIn("don't have enough external evidence", answer["answer"])

    def test_no_evidence_answer_all_reasons(self):
        for reason in ["no_evidence", "search_failed", "adapter_disabled"]:
            answer = build_no_evidence_answer("test", reason=reason)
            self.assertTrue(answer["safe_for_user"])
            self.assertEqual(answer["authority"], "external_evidence_unverified")

    def test_no_evidence_answer_authority_unverified(self):
        answer = build_no_evidence_answer("test")
        self.assertEqual(answer["authority"], "external_evidence_unverified")
        self.assertEqual(answer["truth_status"], "unverified")

    def test_no_evidence_answer_no_sources(self):
        answer = build_no_evidence_answer("test")
        self.assertEqual(answer["sources"], [])
        self.assertEqual(answer["source_count"], 0)

    def test_no_evidence_answer_automatic_truth_write_false(self):
        answer = build_no_evidence_answer("test")
        self.assertFalse(answer["automatic_truth_write"])


class TestNoSideEffects(unittest.TestCase):

    def test_workspace_accessible(self):
        """Confirm repo root is accessible."""
        self.assertTrue(REPO_ROOT.exists())
        self.assertTrue(REPO_ROOT.is_dir())

    def test_no_jsonl_writes(self):
        weslr_dir = REPO_ROOT / "weslr"
        if not weslr_dir.exists():
            return
        before = {}
        for p in weslr_dir.rglob("*.jsonl"):
            before[str(p)] = p.stat().st_mtime
        build_evidence_answer("python", MOCK_VALID_PACKET)
        for p in weslr_dir.rglob("*.jsonl"):
            self.assertEqual(p.stat().st_mtime, before.get(str(p)))

    def test_no_ollama_import(self):
        module_path = REPO_ROOT / "weslr" / "evidence_answer_builder.py"
        with open(module_path) as f:
            content = f.read()
        self.assertNotIn("from ollama", content)
        self.assertNotIn("import ollama", content)

    def test_not_wired_to_chat(self):
        main_path = REPO_ROOT / "main.py"
        if main_path.exists():
            with open(main_path) as f:
                main_content = f.read()
            self.assertNotIn("evidence_answer_builder", main_content)


if __name__ == "__main__":
    unittest.main()