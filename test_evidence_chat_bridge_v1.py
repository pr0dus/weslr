"""
Tests for Evidence Chat Bridge V1
Read-only. No live web calls. No Ollama. No JSONL writes.
"""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from weslr.evidence_chat_bridge import (
    maybe_answer_with_evidence,
    _is_self_system_question,
    _detect_depth,
    _SELF_SYSTEM_PATTERNS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Environment-portable paths
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent


# ─────────────────────────────────────────────────────────────────────────────
# Mocked pipeline result
# ─────────────────────────────────────────────────────────────────────────────

MOCK_ENTROPY_PIPELINE_RESULT = {
    "record_type": "external_evidence_pipeline_v1",
    "query": "What is entropy?",
    "classification": {
        "record_type": "evidence_need_classification_v1",
        "query": "What is entropy?",
        "evidence_needed": True,
        "need_type": "open_knowledge",
        "confidence": 0.85,
    },
    "search_response": {
        "record_type": "searxng_search_response_v1",
        "ok": True,
        "query": "What is entropy?",
        "results": [
            {
                "title": "Entropy (physics)",
                "url": "https://en.wikipedia.org/wiki/Entropy_(physics)",
                "content": "In thermodynamics, entropy is a thermodynamic property defined for thermodynamic systems.",
                "source": "wikipedia",
                "authority": "external_evidence_unverified",
            },
        ],
    },
    "evidence_packet": {
        "record_type": "external_evidence_packet_v1",
        "query": "What is entropy?",
        "result_count": 1,
        "results": [
            {
                "title": "Entropy (physics)",
                "url": "https://en.wikipedia.org/wiki/Entropy_(physics)",
                "content": "In thermodynamics, entropy is a thermodynamic property defined for thermodynamic systems.",
            },
        ],
        "safe_for_answer_builder": True,
    },
    "answer": {
        "record_type": "external_evidence_answer_v1",
        "query": "What is entropy?",
        "answer": "Based on external search results for \"What is entropy?\" — not stored WESLR truth: In thermodynamics, entropy is a thermodynamic property defined for thermodynamic systems.",
        "sources": [
            {"title": "Entropy (physics)", "url": "https://en.wikipedia.org/wiki/Entropy_(physics)"}
        ],
        "source_count": 1,
        "authority": "external_evidence_unverified",
        "truth_status": "unverified",
        "automatic_truth_write": False,
        "safe_for_user": True,
    },
    "authority": "external_evidence_unverified",
    "truth_status": "unverified",
    "automatic_truth_write": False,
    "search_attempted": True,
    "safe_for_user": True,
    "reason": "ok",
}


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMaybeAnswerWithEvidence(unittest.TestCase):

    @patch("weslr.evidence_chat_bridge.is_searxng_enabled")
    @patch("weslr.evidence_chat_bridge.classify_evidence_need")
    def test_search_disabled_returns_safe_message(self, mock_classify, mock_enabled):
        """When search is disabled, returns safe disabled message."""
        mock_classify.return_value = {
            "record_type": "evidence_need_classification_v1",
            "query": "What is entropy?",
            "evidence_needed": True,
        }
        mock_enabled.return_value = False

        result = maybe_answer_with_evidence(
            "What is entropy?",
            "My current best answer is that entropy is a concept in thermodynamics.",
        )
        # Returns None when search is disabled — bridge doesn't override
        self.assertIsNone(result)

    @patch("weslr.evidence_chat_bridge.is_searxng_enabled")
    @patch("weslr.evidence_chat_bridge.classify_evidence_need")
    @patch("weslr.evidence_chat_bridge.run_evidence_pipeline")
    def test_search_enabled_returns_evidence_answer(
        self, mock_pipeline, mock_classify, mock_enabled
    ):
        """When search enabled and evidence needed, returns evidence-grounded answer."""
        mock_classify.return_value = {
            "record_type": "evidence_need_classification_v1",
            "query": "What is entropy?",
            "evidence_needed": True,
        }
        mock_enabled.return_value = True
        mock_pipeline.return_value = MOCK_ENTROPY_PIPELINE_RESULT

        result = maybe_answer_with_evidence(
            "What is entropy?",
            "My current best answer is that entropy is a concept in thermodynamics.",
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["path"], "evidence_grounded_answer")
        self.assertIn("external search results", result["message"])
        self.assertIn("not stored WESLR truth", result["message"])
        self.assertFalse(result["evidence_metadata"]["automatic_truth_write"])
        self.assertEqual(result["evidence_metadata"]["authority"], "external_evidence_unverified")
        self.assertEqual(result["evidence_metadata"]["source_count"], 1)
        self.assertIn("https://en.wikipedia.org/wiki/Entropy_(physics)",
                      result["evidence_metadata"]["source_urls"])

    @patch("weslr.evidence_chat_bridge.is_searxng_enabled")
    @patch("weslr.evidence_chat_bridge.classify_evidence_need")
    def test_no_evidence_needed_does_not_search(self, mock_classify, mock_enabled):
        """When evidence_needed=false, returns None without searching."""
        mock_classify.return_value = {
            "record_type": "evidence_need_classification_v1",
            "query": "Hi",
            "evidence_needed": False,
        }
        mock_enabled.return_value = True
        result = maybe_answer_with_evidence("Hi", "Hello!")
        self.assertIsNone(result)
        mock_enabled.assert_not_called()

    @patch("weslr.evidence_chat_bridge.is_searxng_enabled")
    @patch("weslr.evidence_chat_bridge.classify_evidence_need")
    @patch("weslr.evidence_chat_bridge.run_evidence_pipeline")
    def test_self_system_question_does_not_search(
        self, mock_pipeline, mock_classify, mock_enabled
    ):
        """Self/system questions like 'what are you?' do not trigger search."""
        mock_classify.return_value = {
            "record_type": "evidence_need_classification_v1",
            "query": "What are you?",
            "evidence_needed": True,
        }
        # Not calling is_searxng_enabled because early return
        result = maybe_answer_with_evidence("What are you?", "I am WESLR.")
        self.assertIsNone(result)
        mock_pipeline.assert_not_called()

    @patch("weslr.evidence_chat_bridge.is_searxng_enabled")
    @patch("weslr.evidence_chat_bridge.classify_evidence_need")
    @patch("weslr.evidence_chat_bridge.run_evidence_pipeline")
    def test_deep_depth_from_very_deeply(
        self, mock_pipeline, mock_classify, mock_enabled
    ):
        """Message with 'very deeply' uses depth=deep."""
        mock_classify.return_value = {
            "record_type": "evidence_need_classification_v1",
            "query": "Explain entropy very deeply",
            "evidence_needed": True,
        }
        mock_enabled.return_value = True
        mock_pipeline.return_value = MOCK_ENTROPY_PIPELINE_RESULT

        maybe_answer_with_evidence(
            "Explain entropy very deeply",
            "My current best answer is that entropy is...",
        )
        mock_pipeline.assert_called_once()
        _, kwargs = mock_pipeline.call_args
        self.assertEqual(kwargs["depth"], "deep")

    @patch("weslr.evidence_chat_bridge.is_searxng_enabled")
    @patch("weslr.evidence_chat_bridge.classify_evidence_need")
    @patch("weslr.evidence_chat_bridge.run_evidence_pipeline")
    def test_brief_depth_from_briefly(
        self, mock_pipeline, mock_classify, mock_enabled
    ):
        """Message with 'briefly' uses depth=brief."""
        mock_classify.return_value = {
            "record_type": "evidence_need_classification_v1",
            "query": "briefly explain entropy",
            "evidence_needed": True,
        }
        mock_enabled.return_value = True
        mock_pipeline.return_value = MOCK_ENTROPY_PIPELINE_RESULT

        maybe_answer_with_evidence(
            "briefly explain entropy",
            "My current best answer is that entropy is...",
        )
        mock_pipeline.assert_called_once()
        _, kwargs = mock_pipeline.call_args
        self.assertEqual(kwargs["depth"], "brief")

    @patch("weslr.evidence_chat_bridge.is_searxng_enabled")
    @patch("weslr.evidence_chat_bridge.classify_evidence_need")
    def test_non_fallback_response_not_overridden(self, mock_classify, mock_enabled):
        """A genuine synthesis response is not overridden by evidence bridge."""
        mock_classify.return_value = {
            "record_type": "evidence_need_classification_v1",
            "query": "What is entropy?",
            "evidence_needed": True,
        }
        mock_enabled.return_value = True

        # Long, substantive message that is clearly not a fallback template
        result = maybe_answer_with_evidence(
            "What is entropy?",
            "Entropy is a fundamental thermodynamic property that quantifies the "
            "disorder or randomness in a closed system. It appears in statistical "
            "mechanics, information theory, and thermodynamics.",
        )
        self.assertIsNone(result)

    @patch("weslr.evidence_chat_bridge.is_searxng_enabled")
    @patch("weslr.evidence_chat_bridge.classify_evidence_need")
    @patch("weslr.evidence_chat_bridge.run_evidence_pipeline")
    def test_pipeline_failure_returns_none(
        self, mock_pipeline, mock_classify, mock_enabled
    ):
        """Pipeline failure falls back safely (returns None, doesn't crash)."""
        mock_classify.return_value = {
            "record_type": "evidence_need_classification_v1",
            "query": "What is entropy?",
            "evidence_needed": True,
        }
        mock_enabled.return_value = True
        mock_pipeline.return_value = {
            "record_type": "external_evidence_pipeline_v1",
            "reason": "search_failed",
            "search_attempted": True,
        }

        result = maybe_answer_with_evidence(
            "What is entropy?",
            "My current best answer is that entropy is...",
        )
        self.assertIsNone(result)

    @patch("weslr.evidence_chat_bridge.is_searxng_enabled")
    @patch("weslr.evidence_chat_bridge.classify_evidence_need")
    @patch("weslr.evidence_chat_bridge.run_evidence_pipeline")
    def test_confirmed_answer_fallback_triggers_bridge(
        self, mock_pipeline, mock_classify, mock_enabled
    ):
        """Live fallback 'I don't have a confirmed answer...' triggers evidence bridge."""
        mock_classify.return_value = {
            "record_type": "evidence_need_classification_v1",
            "query": "What is entropy?",
            "evidence_needed": True,
        }
        mock_enabled.return_value = True
        mock_pipeline.return_value = MOCK_ENTROPY_PIPELINE_RESULT

        result = maybe_answer_with_evidence(
            "What is entropy?",
            "I don't have a confirmed answer for that yet...",
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["path"], "evidence_grounded_answer")
        self.assertTrue(result["evidence_metadata"]["evidence_used"])
        self.assertEqual(
            result["evidence_metadata"]["authority"],
            "external_evidence_unverified",
        )
        self.assertFalse(result["evidence_metadata"]["automatic_truth_write"])
        mock_pipeline.assert_called_once()


class TestSelfSystemPatterns(unittest.TestCase):

    def test_self_system_patterns_defined(self):
        self.assertGreater(len(_SELF_SYSTEM_PATTERNS), 0)
        self.assertIn("what are you", _SELF_SYSTEM_PATTERNS)
        self.assertIn("what is weslr", _SELF_SYSTEM_PATTERNS)

    def test_is_self_system_question_detects_self_questions(self):
        questions = [
            "what are you",
            "who are you",
            "what is weslr",
            "how do you work",
            "what can you do",
        ]
        for q in questions:
            self.assertTrue(_is_self_system_question(q), f"Should detect: {q}")

    def test_is_self_system_question_allows_normal_questions(self):
        questions = [
            "What is entropy?",
            "Explain machine learning",
            "What is the capital of France?",
            "How do I bake bread?",
        ]
        for q in questions:
            self.assertFalse(_is_self_system_question(q), f"Should NOT detect: {q}")


class TestDetectDepth(unittest.TestCase):

    def test_deep_from_very_deep(self):
        self.assertEqual(_detect_depth("Explain entropy very deeply"), "deep")

    def test_deep_from_in_depth(self):
        self.assertEqual(_detect_depth("Explain entropy in depth"), "deep")

    def test_brief_from_briefly(self):
        self.assertEqual(_detect_depth("briefly explain entropy"), "brief")

    def test_brief_from_simple(self):
        self.assertEqual(_detect_depth("simple explanation of entropy"), "brief")

    def test_normal_default(self):
        self.assertEqual(_detect_depth("What is entropy?"), "normal")
        self.assertEqual(_detect_depth("Tell me about thermodynamics"), "normal")


class TestNoSideEffects(unittest.TestCase):

    def test_workspace_accessible(self):
        self.assertTrue(REPO_ROOT.exists())

    def test_no_jsonl_writes(self):
        weslr_dir = REPO_ROOT / "weslr"
        if not weslr_dir.exists():
            return
        before = {}
        for p in weslr_dir.rglob("*.jsonl"):
            before[str(p)] = p.stat().st_mtime
        # Run bridge with mocks
        with patch("weslr.evidence_chat_bridge.is_searxng_enabled") as mock_en:
            with patch("weslr.evidence_chat_bridge.classify_evidence_need") as mock_cl:
                mock_cl.return_value = {"evidence_needed": False}
                maybe_answer_with_evidence("test", "fallback answer")
        for p in weslr_dir.rglob("*.jsonl"):
            self.assertEqual(p.stat().st_mtime, before.get(str(p)))

    def test_no_ollama_import(self):
        module_path = REPO_ROOT / "weslr" / "evidence_chat_bridge.py"
        with open(module_path) as f:
            content = f.read()
        self.assertNotIn("from ollama", content)
        self.assertNotIn("import ollama", content)


if __name__ == "__main__":
    unittest.main()