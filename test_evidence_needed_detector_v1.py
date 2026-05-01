"""
Tests for WESLR Evidence Needed Detector V1
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "weslr"))

from evidence_needed_detector import (
    classify_evidence_need,
    build_evidence_needed_response,
)


class TestClassifyEvidenceNeed(unittest.TestCase):
    """Tests for classify_evidence_need function."""

    def test_entropy_definition_detected(self):
        result = classify_evidence_need("What is entropy?")
        self.assertTrue(result["evidence_needed"])
        self.assertEqual(result["need_type"], "definition_request")
        self.assertGreater(result["confidence"], 0.7)

    def test_deep_entropy_explanation_detected(self):
        result = classify_evidence_need("Explain entropy very deeply.")
        self.assertTrue(result["evidence_needed"])
        self.assertEqual(result["need_type"], "open_knowledge")
        self.assertGreater(result["confidence"], 0.7)

    def test_source_request_detected(self):
        result = classify_evidence_need("What is the source for entropy?")
        self.assertTrue(result["evidence_needed"])
        self.assertEqual(result["need_type"], "source_request")
        self.assertGreater(result["confidence"], 0.8)

    def test_search_web_request_detected(self):
        result = classify_evidence_need("Can you search the web for entropy?")
        self.assertTrue(result["evidence_needed"])
        self.assertIn(result["need_type"], ["lookup_request", "source_request"])

    def test_look_up_request_detected(self):
        result = classify_evidence_need("Look up entropy.")
        self.assertTrue(result["evidence_needed"])
        self.assertEqual(result["need_type"], "lookup_request")

    def test_latest_research_request_detected(self):
        result = classify_evidence_need("What is the latest AI research about uncertainty?")
        self.assertTrue(result["evidence_needed"])
        self.assertIn(result["need_type"], ["latest_information", "open_knowledge"])

    def test_greeting_not_detected(self):
        for msg in ["Hi", "Hello", "Hey"]:
            result = classify_evidence_need(msg)
            self.assertFalse(result["evidence_needed"], f"Should not detect: {msg}")
            self.assertEqual(result["need_type"], "none")

    def test_self_identity_not_detected(self):
        result = classify_evidence_need("What are you?")
        self.assertFalse(result["evidence_needed"])
        self.assertEqual(result["need_type"], "none")

    def test_capability_question_not_detected(self):
        for msg in ["What can you help me with?", "What can you do?"]:
            result = classify_evidence_need(msg)
            self.assertFalse(result["evidence_needed"], f"Should not detect: {msg}")
            self.assertEqual(result["need_type"], "none")

    def test_next_step_question_not_detected(self):
        result = classify_evidence_need("What should I try next?")
        self.assertFalse(result["evidence_needed"])
        self.assertEqual(result["need_type"], "none")

    def test_automatic_search_allowed_always_false(self):
        for msg in [
            "What is entropy?",
            "Explain entropy deeply.",
            "What is the source?",
            "Can you search for X?",
            "Look up Y.",
            "What is the latest Z?",
            "Hi",
            "What are you?",
        ]:
            result = classify_evidence_need(msg)
            self.assertFalse(result["automatic_search_allowed"], f"Should be False for: {msg}")

    def test_authority_classification_only(self):
        for msg in ["What is entropy?", "Hi", "What are you?"]:
            result = classify_evidence_need(msg)
            self.assertEqual(result["authority"], "classification_only")

    def test_record_type_correct(self):
        result = classify_evidence_need("What is entropy?")
        self.assertEqual(result["record_type"], "evidence_need_classification_v1")

    def test_empty_message_not_evidence_needed(self):
        result = classify_evidence_need("")
        self.assertFalse(result["evidence_needed"])
        self.assertEqual(result["need_type"], "none")

    def test_define_prefix_detected(self):
        result = classify_evidence_need("Define entropy.")
        self.assertTrue(result["evidence_needed"])
        self.assertEqual(result["need_type"], "definition_request")

    def test_tell_me_about_detected(self):
        result = classify_evidence_need("Tell me about black holes.")
        self.assertTrue(result["evidence_needed"])
        self.assertEqual(result["need_type"], "open_knowledge")

    def test_why_question_detected(self):
        result = classify_evidence_need("Why does gravity exist?")
        self.assertTrue(result["evidence_needed"])
        self.assertEqual(result["need_type"], "open_knowledge")


class TestBuildEvidenceNeededResponse(unittest.TestCase):
    """Tests for build_evidence_needed_response function."""

    def test_response_says_no_search_performed_yet(self):
        result = build_evidence_needed_response("What is entropy?")
        text = result["response_text"].lower()
        self.assertIn("not yet", text)
        self.assertIn("search", text)
        # Should not claim to have searched
        self.assertNotIn("i found", text.lower())
        self.assertNotIn("i searched", text.lower())
        self.assertNotIn("here is what i found", text.lower())

    def test_response_path_is_evidence_needed(self):
        result = build_evidence_needed_response("What is entropy?")
        self.assertEqual(result["path"], "evidence_needed")

    def test_response_contract_uncertainty_boundary(self):
        result = build_evidence_needed_response("What is entropy?")
        self.assertEqual(result["response_contract"], "uncertainty_boundary")

    def test_automatic_search_allowed_false(self):
        result = build_evidence_needed_response("What is entropy?")
        self.assertFalse(result["automatic_search_allowed"])

    def test_authority_classification_only(self):
        result = build_evidence_needed_response("What is entropy?")
        self.assertEqual(result["authority"], "classification_only")

    def test_classification_included(self):
        result = build_evidence_needed_response("What is entropy?")
        self.assertIn("classification", result)
        self.assertTrue(result["classification"]["evidence_needed"])

    def test_record_type_correct(self):
        result = build_evidence_needed_response("What is entropy?")
        self.assertEqual(result["record_type"], "evidence_needed_response_v1")


class TestStructuralConstraints(unittest.TestCase):
    """Verify no external capabilities, no writes."""

    def test_no_jsonl_writes(self):
        """Verify no JSONL writes."""
        import inspect
        from evidence_needed_detector import classify_evidence_need, build_evidence_needed_response
        for fn in [classify_evidence_need, build_evidence_needed_response]:
            source = inspect.getsource(fn)
            self.assertNotIn(".write(", source)
            self.assertNotIn("json.dump", source)
            self.assertNotIn("open(", source.replace("open(__file__", ""))
            self.assertNotIn('"w"', source)
            self.assertNotIn("'w'", source)

    def test_no_http_imports(self):
        """Verify no HTTP, requests, urllib, or search imports."""
        import inspect
        from evidence_needed_detector import classify_evidence_need, build_evidence_needed_response
        for fn in [classify_evidence_need, build_evidence_needed_response]:
            source = inspect.getsource(fn)
            source_lower = source.lower()
            self.assertNotIn("import urllib", source_lower)
            self.assertNotIn("from urllib", source_lower)
            self.assertNotIn("import requests", source_lower)
            self.assertNotIn("from requests", source_lower)
            self.assertNotIn("import httpx", source_lower)
            self.assertNotIn("import http", source_lower)
            self.assertNotIn("searx", source_lower)
            self.assertNotIn("duckduckgo", source_lower)
            self.assertNotIn("ddg", source_lower)

    def test_not_wired_into_chat(self):
        """Verify module is standalone, not imported by chat handlers."""
        import inspect
        from evidence_needed_detector import classify_evidence_need, build_evidence_needed_response
        for fn in [classify_evidence_need, build_evidence_needed_response]:
            source = inspect.getsource(fn)
            self.assertNotIn("/chat", source)
            self.assertNotIn("_CONTRACT_REPLIES", source)
            self.assertNotIn("chat_interface", source.lower())


if __name__ == "__main__":
    unittest.main()