"""
Tests for Evidence Packet Builder V1
Read-only. No live web calls. No Ollama. No JSONL writes.
"""

import unittest
from pathlib import Path
from weslr.evidence_packet_builder import (
    build_evidence_packet,
    summarize_evidence_packet,
    RECORD_TYPE,
    SUMMARY_RECORD_TYPE,
    SAFE_FIELDS,
    UNSAFE_FIELDS,
    MAX_CONTENT_LENGTH,
)


# ─────────────────────────────────────────────────────────────────────────────
# Environment-portable paths
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent  # repo root


# ─────────────────────────────────────────────────────────────────────────────
# Mocked SearXNG responses
# ─────────────────────────────────────────────────────────────────────────────

MOCK_VALID_SEARXNG_RESPONSE = {
    "record_type": "searxng_search_response_v1",
    "ok": True,
    "query": "test query",
    "results": [
        {
            "title": "Result One",
            "url": "https://example.com/one",
            "content": "This is the content of result one.",
            "source": "example",
            "authority": "external_evidence_unverified",
        },
        {
            "title": "Result Two",
            "url": "https://example.org/two",
            "content": "This is the content of result two.",
            "source": "example",
            "authority": "external_evidence_unverified",
        },
        {
            "title": "Result Three",
            "url": "https://example.net/three",
            "content": "This is the content of result three.",
            "source": "example",
            "authority": "external_evidence_unverified",
        },
    ],
}


MOCK_VALID_RESPONSE_WITH_UNSAFE_FIELDS = {
    "record_type": "searxng_search_response_v1",
    "ok": True,
    "query": "test query",
    "results": [
        {
            "title": "Result With Unsafe",
            "url": "https://example.com/unsafe",
            "content": "Content here",
            "source": "example",
            "authority": "external_evidence_unverified",
            "raw": "this should be stripped",
            "cookies": "session=abc",
            "api_key": "secret",
        },
    ],
}


MOCK_LONG_CONTENT_RESPONSE = {
    "record_type": "searxng_search_response_v1",
    "ok": True,
    "query": "long content test",
    "results": [
        {
            "title": "Long Content Result",
            "url": "https://example.com/long",
            "content": "A" * 5000,
            "source": "example",
            "authority": "external_evidence_unverified",
        },
    ],
}


MOCK_RESPONSE_MISSING_OK = {
    "record_type": "searxng_search_response_v1",
    "ok": False,
    "query": "failed search",
    "results": [],
}


MOCK_RESPONSE_WRONG_TYPE = {
    "record_type": "some_other_response",
    "ok": True,
    "results": [{"title": "Should be rejected", "url": "https://x.com"}],
}


MOCK_RESPONSE_EMPTY_RESULTS = {
    "record_type": "searxng_search_response_v1",
    "ok": True,
    "query": "empty",
    "results": [],
}


MOCK_RESPONSE_NOT_DICT = "not a dict"


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildEvidencePacket(unittest.TestCase):

    def test_valid_mocked_searxng_response_builds_packet(self):
        packet = build_evidence_packet("test query", MOCK_VALID_SEARXNG_RESPONSE)
        self.assertEqual(packet["record_type"], RECORD_TYPE)
        self.assertEqual(packet["query"], "test query")
        self.assertEqual(packet["source_adapter"], "searxng")
        self.assertEqual(packet["authority"], "external_evidence_unverified")
        self.assertEqual(packet["truth_status"], "unverified")
        self.assertFalse(packet["automatic_truth_write"])
        self.assertEqual(packet["result_count"], 3)
        self.assertTrue(packet["safe_for_answer_builder"])
        self.assertEqual(len(packet["results"]), 3)

    def test_disabled_failed_search_response_rejected(self):
        packet = build_evidence_packet("test", MOCK_RESPONSE_MISSING_OK)
        self.assertFalse(packet["safe_for_answer_builder"])
        self.assertEqual(packet["result_count"], 0)
        self.assertIn("Invalid or missing", packet["limitations"][0])

    def test_wrong_record_type_rejected(self):
        packet = build_evidence_packet("test", MOCK_RESPONSE_WRONG_TYPE)
        self.assertFalse(packet["safe_for_answer_builder"])
        self.assertEqual(packet["result_count"], 0)

    def test_empty_results_rejected(self):
        packet = build_evidence_packet("test", MOCK_RESPONSE_EMPTY_RESULTS)
        self.assertFalse(packet["safe_for_answer_builder"])
        self.assertEqual(packet["result_count"], 0)

    def test_max_results_respected(self):
        packet = build_evidence_packet("test", MOCK_VALID_SEARXNG_RESPONSE, max_results=2)
        self.assertEqual(packet["result_count"], 2)
        self.assertTrue(packet["safe_for_answer_builder"])

    def test_unsafe_fields_stripped(self):
        packet = build_evidence_packet("test", MOCK_VALID_RESPONSE_WITH_UNSAFE_FIELDS)
        result = packet["results"][0]
        self.assertNotIn("raw", result)
        self.assertNotIn("cookies", result)
        self.assertNotIn("api_key", result)
        self.assertIn("title", result)
        self.assertIn("url", result)

    def test_content_truncation(self):
        packet = build_evidence_packet("test", MOCK_LONG_CONTENT_RESPONSE)
        result = packet["results"][0]
        self.assertLessEqual(len(result["content"]), MAX_CONTENT_LENGTH + 1)
        self.assertTrue(result["content"].endswith("…"))

    def test_authority_external_evidence_unverified(self):
        packet = build_evidence_packet("test", MOCK_VALID_SEARXNG_RESPONSE)
        self.assertEqual(packet["authority"], "external_evidence_unverified")

    def test_truth_status_unverified(self):
        packet = build_evidence_packet("test", MOCK_VALID_SEARXNG_RESPONSE)
        self.assertEqual(packet["truth_status"], "unverified")

    def test_automatic_truth_write_false(self):
        packet = build_evidence_packet("test", MOCK_VALID_SEARXNG_RESPONSE)
        self.assertFalse(packet["automatic_truth_write"])

    def test_non_dict_response_returns_safe_false(self):
        packet = build_evidence_packet("test", MOCK_RESPONSE_NOT_DICT)
        self.assertFalse(packet["safe_for_answer_builder"])

    def test_results_have_required_fields(self):
        packet = build_evidence_packet("test", MOCK_VALID_SEARXNG_RESPONSE)
        for r in packet["results"]:
            self.assertIn("title", r)
            self.assertIn("url", r)


class TestSummarizeEvidencePacket(unittest.TestCase):

    def test_summary_extracts_titles(self):
        packet = build_evidence_packet("test", MOCK_VALID_SEARXNG_RESPONSE)
        summary = summarize_evidence_packet(packet)
        self.assertEqual(summary["record_type"], SUMMARY_RECORD_TYPE)
        self.assertEqual(summary["query"], "test")
        self.assertEqual(summary["result_count"], 3)
        # Titles are trust-ranked so order may vary — check membership, not order
        self.assertEqual(set(summary["top_titles"]), {"Result One", "Result Two", "Result Three"})

    def test_summary_extracts_domains(self):
        packet = build_evidence_packet("test", MOCK_VALID_SEARXNG_RESPONSE)
        summary = summarize_evidence_packet(packet)
        self.assertIn("example.com", summary["top_domains"])
        self.assertIn("example.org", summary["top_domains"])
        self.assertIn("example.net", summary["top_domains"])

    def test_summary_authority_from_packet(self):
        packet = build_evidence_packet("test", MOCK_VALID_SEARXNG_RESPONSE)
        summary = summarize_evidence_packet(packet)
        self.assertEqual(summary["authority"], "external_evidence_unverified")
        self.assertEqual(summary["truth_status"], "unverified")

    def test_summary_safe_for_answer_builder_from_packet(self):
        packet = build_evidence_packet("test", MOCK_VALID_SEARXNG_RESPONSE)
        summary = summarize_evidence_packet(packet)
        self.assertTrue(summary["safe_for_answer_builder"])

    def test_summary_wrong_record_type_returns_empty(self):
        summary = summarize_evidence_packet({"record_type": "wrong"})
        self.assertEqual(summary["record_type"], SUMMARY_RECORD_TYPE)
        self.assertEqual(summary["result_count"], 0)
        self.assertEqual(summary["top_titles"], [])

    def test_summary_empty_query(self):
        packet = build_evidence_packet("", MOCK_VALID_SEARXNG_RESPONSE)
        summary = summarize_evidence_packet(packet)
        self.assertEqual(summary["query"], "")


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
        build_evidence_packet("test", MOCK_VALID_SEARXNG_RESPONSE)
        for p in weslr_dir.rglob("*.jsonl"):
            self.assertEqual(p.stat().st_mtime, before.get(str(p)))

    def test_no_ollama_import(self):
        module_path = REPO_ROOT / "weslr" / "evidence_packet_builder.py"
        with open(module_path) as f:
            content = f.read()
        self.assertNotIn("from ollama", content)
        self.assertNotIn("import ollama", content)


if __name__ == "__main__":
    unittest.main()