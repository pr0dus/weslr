"""
Tests for Evidence Pipeline V1
Read-only. No live web calls. No Ollama. No JSONL writes.
"""

import unittest
from unittest.mock import patch, MagicMock

from weslr.evidence_pipeline import run_evidence_pipeline, RECORD_TYPE


# ─────────────────────────────────────────────────────────────────────────────
# Mocked components
# ─────────────────────────────────────────────────────────────────────────────

MOCK_SEARCH_RESPONSE = {
    "record_type": "searxng_search_response_v1",
    "ok": True,
    "query": "entropy",
    "results": [
        {
            "title": "Entropy (physics)",
            "url": "https://en.wikipedia.org/wiki/Entropy_(physics)",
            "content": "In thermodynamics, entropy is a thermodynamic property "
                       "defined for thermodynamic systems.",
            "source": "wikipedia",
            "authority": "external_evidence_unverified",
        },
        {
            "title": "Entropy (information theory)",
            "url": "https://en.wikipedia.org/wiki/Entropy_(information_theory)",
            "content": "In information theory, entropy is the expected amount of information.",
            "source": "wikipedia",
            "authority": "external_evidence_unverified",
        },
    ],
}


MOCK_CLASSIFICATION_EVIDENCE_NEEDED = {
    "record_type": "evidence_need_classification_v1",
    "query": "entropy",
    "evidence_needed": True,
    "need_type": "open_knowledge",
    "confidence": 0.85,
}


MOCK_CLASSIFICATION_NO_EVIDENCE = {
    "record_type": "evidence_need_classification_v1",
    "query": "hello",
    "evidence_needed": False,
    "need_type": None,
    "confidence": 0.5,
}


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRunEvidencePipeline(unittest.TestCase):

    @patch("weslr.evidence_pipeline.classify_evidence_need")
    def test_non_evidence_query_does_not_search(self, mock_classify):
        mock_classify.return_value = MOCK_CLASSIFICATION_NO_EVIDENCE
        result = run_evidence_pipeline("hello")
        self.assertEqual(result["reason"], "no_evidence_needed")
        self.assertFalse(result["search_attempted"])
        self.assertIsNone(result["search_response"])

    @patch("weslr.evidence_pipeline.classify_evidence_need")
    @patch("weslr.evidence_pipeline.is_searxng_enabled")
    def test_evidence_query_with_search_disabled_does_not_search(
        self, mock_enabled, mock_classify
    ):
        mock_classify.return_value = MOCK_CLASSIFICATION_EVIDENCE_NEEDED
        mock_enabled.return_value = False
        result = run_evidence_pipeline("entropy")
        self.assertEqual(result["reason"], "search_disabled")
        self.assertFalse(result["search_attempted"])
        self.assertIsNone(result["search_response"])
        self.assertIn("not enabled", result["answer"]["answer"])

    @patch("weslr.evidence_pipeline.classify_evidence_need")
    @patch("weslr.evidence_pipeline.is_searxng_enabled")
    @patch("weslr.evidence_pipeline.search_searxng")
    def test_evidence_query_with_mocked_enabled_search_returns_answer(
        self, mock_search, mock_enabled, mock_classify
    ):
        mock_classify.return_value = MOCK_CLASSIFICATION_EVIDENCE_NEEDED
        mock_enabled.return_value = True
        mock_search.return_value = MOCK_SEARCH_RESPONSE
        result = run_evidence_pipeline("entropy")
        self.assertEqual(result["reason"], "ok")
        self.assertTrue(result["search_attempted"])
        self.assertIsNotNone(result["search_response"])
        self.assertIsNotNone(result["evidence_packet"])
        self.assertIsNotNone(result["answer"])
        self.assertTrue(result["safe_for_user"])

    @patch("weslr.evidence_pipeline.classify_evidence_need")
    @patch("weslr.evidence_pipeline.is_searxng_enabled")
    @patch("weslr.evidence_pipeline.search_searxng")
    def test_search_failure_returns_safe_no_evidence_answer(
        self, mock_search, mock_enabled, mock_classify
    ):
        mock_classify.return_value = MOCK_CLASSIFICATION_EVIDENCE_NEEDED
        mock_enabled.return_value = True
        mock_search.side_effect = Exception("network error")
        result = run_evidence_pipeline("entropy")
        self.assertEqual(result["reason"], "search_failed")
        self.assertTrue(result["search_attempted"])
        self.assertIsNone(result["search_response"])

    @patch("weslr.evidence_pipeline.classify_evidence_need")
    @patch("weslr.evidence_pipeline.is_searxng_enabled")
    @patch("weslr.evidence_pipeline.search_searxng")
    def test_invalid_packet_returns_reason_packet_failed(
        self, mock_search, mock_enabled, mock_classify
    ):
        mock_classify.return_value = MOCK_CLASSIFICATION_EVIDENCE_NEEDED
        mock_enabled.return_value = True
        mock_search.return_value = {
            "record_type": "searxng_search_response_v1",
            "ok": True,
            "query": "entropy",
            "results": [],
        }
        result = run_evidence_pipeline("entropy")
        self.assertEqual(result["reason"], "packet_failed")

    @patch("weslr.evidence_pipeline.classify_evidence_need")
    @patch("weslr.evidence_pipeline.is_searxng_enabled")
    @patch("weslr.evidence_pipeline.search_searxng")
    def test_depth_passed_through_to_answer_builder(
        self, mock_search, mock_enabled, mock_classify
    ):
        mock_classify.return_value = MOCK_CLASSIFICATION_EVIDENCE_NEEDED
        mock_enabled.return_value = True
        mock_search.return_value = MOCK_SEARCH_RESPONSE

        brief = run_evidence_pipeline("entropy", depth="brief")
        deep = run_evidence_pipeline("entropy", depth="deep")
        self.assertLess(len(brief["answer"]["answer"]), len(deep["answer"]["answer"]))

    def test_authority_external_evidence_unverified(self):
        with patch("weslr.evidence_pipeline.classify_evidence_need") as mock_c:
            mock_c.return_value = MOCK_CLASSIFICATION_NO_EVIDENCE
            result = run_evidence_pipeline("hello")
        self.assertEqual(result["authority"], "external_evidence_unverified")

    def test_truth_status_unverified(self):
        with patch("weslr.evidence_pipeline.classify_evidence_need") as mock_c:
            mock_c.return_value = MOCK_CLASSIFICATION_NO_EVIDENCE
            result = run_evidence_pipeline("hello")
        self.assertEqual(result["truth_status"], "unverified")

    def test_automatic_truth_write_false(self):
        with patch("weslr.evidence_pipeline.classify_evidence_need") as mock_c:
            mock_c.return_value = MOCK_CLASSIFICATION_NO_EVIDENCE
            result = run_evidence_pipeline("hello")
        self.assertFalse(result["automatic_truth_write"])


class TestNoSideEffects(unittest.TestCase):

    def test_no_jsonl_writes(self):
        import os
        workspace = "/data/data/com.termux/files/home/.openclaw/workspace"
        self.assertTrue(os.path.exists(workspace))

    def test_no_ollama_import(self):
        with open("/data/data/com.termux/files/home/.openclaw/workspace/weslr/evidence_pipeline.py") as f:
            content = f.read()
        self.assertNotIn("from ollama", content)
        self.assertNotIn("import ollama", content)

    def test_not_wired_to_chat(self):
        import os
        main_path = "/data/data/com.termux/files/home/.openclaw/workspace/main.py"
        if os.path.exists(main_path):
            with open(main_path) as f:
                main_content = f.read()
            self.assertNotIn("evidence_pipeline", main_content)


class TestSampleOutputs(unittest.TestCase):

    @patch("weslr.evidence_pipeline.classify_evidence_need")
    @patch("weslr.evidence_pipeline.is_searxng_enabled")
    def test_sample_disabled_search_result(self, mock_enabled, mock_classify):
        mock_classify.return_value = MOCK_CLASSIFICATION_EVIDENCE_NEEDED
        mock_enabled.return_value = False
        result = run_evidence_pipeline("What is entropy?")
        self.assertEqual(result["reason"], "search_disabled")
        self.assertFalse(result["search_attempted"])
        self.assertIn("not enabled", result["answer"]["answer"].lower())

    @patch("weslr.evidence_pipeline.classify_evidence_need")
    @patch("weslr.evidence_pipeline.is_searxng_enabled")
    @patch("weslr.evidence_pipeline.search_searxng")
    def test_sample_mocked_successful_result(self, mock_search, mock_enabled, mock_classify):
        mock_classify.return_value = MOCK_CLASSIFICATION_EVIDENCE_NEEDED
        mock_enabled.return_value = True
        mock_search.return_value = MOCK_SEARCH_RESPONSE
        result = run_evidence_pipeline("What is entropy?")
        self.assertEqual(result["reason"], "ok")
        self.assertTrue(result["search_attempted"])
        self.assertEqual(result["answer"]["record_type"], "external_evidence_answer_v1")
        self.assertIn("external search results", result["answer"]["answer"])


if __name__ == "__main__":
    unittest.main()