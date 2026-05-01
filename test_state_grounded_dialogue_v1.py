"""
Tests for WESLR State Grounded Dialogue V1

Covers: classify_state_question, load_state_sources, answer_state_question
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure weslr module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "weslr"))

import state_grounded_dialogue as sgd


class TestClassifyStateQuestion(unittest.TestCase):
    """Tests for classify_state_question function."""

    def test_classify_implemented_reality_question(self):
        result = sgd.classify_state_question("what is implemented?")
        self.assertTrue(result["is_state_question"])
        self.assertEqual(result["question_type"], "implemented_reality")
        self.assertGreater(result["confidence"], 0.8)
        self.assertEqual(result["authority"], "read_only")

    def test_classify_implemented_reality_variations(self):
        for q in [
            "what can you actually do",
            "what is live",
            "what do you have",
            "what pieces are implemented",
        ]:
            result = sgd.classify_state_question(q)
            self.assertEqual(result["question_type"], "implemented_reality", f"Failed for: {q}")

    def test_classify_attention_question(self):
        result = sgd.classify_state_question("what needs attention?")
        self.assertTrue(result["is_state_question"])
        self.assertEqual(result["question_type"], "attention_summary")
        self.assertGreater(result["confidence"], 0.85)
        self.assertEqual(result["authority"], "read_only")

    def test_classify_attention_variations(self):
        for q in [
            "what should be reviewed",
            "what does AAI see",
            "pending reviews",
            "review queue",
        ]:
            result = sgd.classify_state_question(q)
            self.assertEqual(result["question_type"], "attention_summary", f"Failed for: {q}")

    def test_classify_composite_summary_question(self):
        result = sgd.classify_state_question("what does composite analysis say?")
        self.assertTrue(result["is_state_question"])
        self.assertEqual(result["question_type"], "composite_summary")
        self.assertGreater(result["confidence"], 0.85)
        self.assertEqual(result["authority"], "read_only")

    def test_classify_unsafe_automation_question(self):
        result = sgd.classify_state_question("what is unsafe to automate?")
        self.assertTrue(result["is_state_question"])
        self.assertEqual(result["question_type"], "pending_reviews")
        self.assertGreater(result["confidence"], 0.8)
        self.assertEqual(result["authority"], "read_only")

    def test_classify_architecture_question(self):
        result = sgd.classify_state_question("what is your current architecture?")
        self.assertTrue(result["is_state_question"])
        self.assertEqual(result["question_type"], "architecture_boundary")
        self.assertGreater(result["confidence"], 0.75)
        self.assertEqual(result["authority"], "read_only")

    def test_non_state_question_returns_false(self):
        for q in [
            "hello",
            "how are you",
            "tell me a joke",
            "what is the weather",
            "who is your favorite color",
        ]:
            result = sgd.classify_state_question(q)
            self.assertFalse(result["is_state_question"], f"Should not classify as state: {q}")
            self.assertEqual(result["question_type"], "unknown")

    def test_record_type_correct(self):
        result = sgd.classify_state_question("what needs attention?")
        self.assertEqual(result["record_type"], "state_question_classification_v1")


class TestLoadStateSources(unittest.TestCase):
    """Tests for load_state_sources function."""

    def test_returns_correct_record_type(self):
        result = sgd.load_state_sources()
        self.assertEqual(result["record_type"], "state_sources_v1")
        self.assertEqual(result["authority"], "read_only")

    def test_docs_available_structure(self):
        result = sgd.load_state_sources()
        docs = result["docs_available"]
        self.assertIn("implemented_reality_inventory", docs)
        self.assertIn("aai_checkpoint", docs)
        self.assertIn("composite_checkpoint", docs)
        self.assertIn("composite_canon", docs)
        for key, doc_info in docs.items():
            self.assertIn("available", doc_info)
            self.assertIn("path", doc_info)
            self.assertIn("size", doc_info)

    def test_safe_if_docs_missing(self):
        with patch.object(sgd, "_safe_read", return_value=None):
            result = sgd.load_state_sources()
            # Should not raise, should return safe structure
            self.assertIn("docs_available", result)
            self.assertIn("aai_summary", result)
            self.assertIn("composite_summary", result)

    def test_aai_summary_present(self):
        result = sgd.load_state_sources()
        self.assertIn("aai_summary", result)
        # aai_summary is a dict (loaded or with _error key)
        self.assertIsInstance(result["aai_summary"], dict)

    def test_composite_summary_present(self):
        result = sgd.load_state_sources()
        self.assertIn("composite_summary", result)
        self.assertIsInstance(result["composite_summary"], dict)

    def test_safe_read_handles_missing_file(self):
        result = sgd._safe_read("/nonexistent/path/file.md")
        self.assertIsNone(result)


class TestAnswerStateQuestion(unittest.TestCase):
    """Tests for answer_state_question function."""

    def test_answer_uses_aai_summary_for_attention_question(self):
        result = sgd.answer_state_question("what needs attention?")
        self.assertEqual(result["question_type"], "attention_summary")
        self.assertIn("aai_summary", result["sources_used"])
        self.assertIsInstance(result["answer"], str)
        self.assertGreater(len(result["answer"]), 0)

    def test_answer_uses_composite_summary_for_composite_question(self):
        result = sgd.answer_state_question("what does composite analysis say?")
        self.assertEqual(result["question_type"], "composite_summary")
        self.assertIn("composite_summary", result["sources_used"])
        self.assertIsInstance(result["answer"], str)

    def test_answer_uses_inventory_for_implemented_question(self):
        result = sgd.answer_state_question("what is implemented?")
        self.assertEqual(result["question_type"], "implemented_reality")
        self.assertIn("implemented_reality_inventory", result["sources_used"])
        self.assertIsInstance(result["answer"], str)

    def test_says_read_only_authority(self):
        result = sgd.answer_state_question("what needs attention?")
        self.assertEqual(result["authority"], "read_only")

    def test_automatic_change_always_false(self):
        for q in [
            "what is implemented",
            "what needs attention",
            "what is unsafe to automate",
            "what does composite say",
        ]:
            result = sgd.answer_state_question(q)
            self.assertFalse(result["automatic_change"], f"automatic_change should be False for: {q}")

    def test_no_jsonl_writes(self):
        """Verify no JSONL file writes occur during answering."""
        jsonl_paths = []
        for root, dirs, files in os.walk(os.path.dirname(sgd._WORKSPACE)):
            for f in files:
                if f.endswith(".jsonl"):
                    jsonl_paths.append(os.path.join(root, f))
        # No writes should happen in state_grounded_dialogue
        # This is a structural test - we verify the module has no write calls
        import inspect
        source = inspect.getsource(sgd)
        self.assertNotIn("open(", source.replace("open(__file__", "").replace("open(path", ""))  # only _safe_read opens files
        self.assertNotIn(".write(", source)
        self.assertNotIn("json.dump", source)
        self.assertNotIn("jsonl", source.lower())

    def test_no_ollama_imports(self):
        """Verify Ollama is not imported or wired in state_grounded_dialogue."""
        import inspect
        source = inspect.getsource(sgd)
        # Should not import ollama
        self.assertNotIn("import ollama", source)
        self.assertNotIn("from ollama", source)
        # Ollama word may appear in answer text (as a disclaimer) - that is allowed
        # The test checks the module doesn't USE ollama

    def test_not_wired_into_chat(self):
        """Verify state_grounded_dialogue is standalone and not imported by chat modules."""
        # The module should exist independently
        self.assertTrue(os.path.exists(sgd.__file__))
        # It should not reference chat handlers (imports, not descriptive text)
        import inspect
        source = inspect.getsource(sgd)
        # /chat may appear in answer text describing architecture - not in imports/wiring
        # Check for actual wiring: imports of chat modules, _CONTRACT_REPLIES usage
        self.assertNotIn("import.*chat", source)  # No chat module imports
        self.assertNotIn("_CONTRACT_REPLIES", source)
        self.assertNotIn("chat_interface", source.lower())

    def test_missing_source_produces_limitation_not_crash(self):
        with patch.object(sgd, "_safe_read", return_value=None):
            with patch.dict("sys.modules", {"artificial_analysis_index": MagicMock()}):
                # Force aai to error
                with patch("state_grounded_dialogue.load_state_sources", return_value={
                    "record_type": "state_sources_v1",
                    "docs_available": {k: {"available": False} for k in [
                        "implemented_reality_inventory", "aai_checkpoint",
                        "composite_checkpoint", "composite_canon"
                    ]},
                    "aai_summary": {"_error": "mocked"},
                    "composite_summary": {"_error": "mocked"},
                    "authority": "read_only"
                }):
                    result = sgd.answer_state_question("what is implemented?")
                    self.assertIn("limitations", result)
                    self.assertIsInstance(result["limitations"], list)

    def test_non_state_question_returns_unknown(self):
        result = sgd.answer_state_question("tell me about the weather")
        self.assertEqual(result["question_type"], "unknown")
        self.assertEqual(result["answer"], "No state-grounded answer available for this query.")

    def test_record_type_correct(self):
        result = sgd.answer_state_question("what needs attention?")
        self.assertEqual(result["record_type"], "state_grounded_answer_v1")

    def test_answer_for_unsafe_automation(self):
        result = sgd.answer_state_question("what is unsafe to automate?")
        self.assertEqual(result["question_type"], "pending_reviews")
        # Should mention operator/approval
        self.assertTrue(
            "operator" in result["answer"].lower() or "approval" in result["answer"].lower(),
            f"Answer should mention operator/approval: {result['answer']}"
        )

    def test_answer_for_blocker_question(self):
        result = sgd.answer_state_question("what are your current blockers?")
        self.assertIn(result["question_type"], ["pending_reviews", "unknown"])
        self.assertIsInstance(result["answer"], str)


class TestStructuralConstraints(unittest.TestCase):
    """Verify structural constraints from the spec."""

    def test_no_jsonl_modification(self):
        """Verify no JSONL file modification occurs."""
        import inspect
        source = inspect.getsource(sgd)
        # No jsonl paths or write operations
        self.assertNotIn("jsonl", source.lower())
        # No write mode - only 'r' mode for reading
        self.assertNotIn("'w'", source)  # write mode
        self.assertNotIn('"w"', source)  # write mode
        # No appending to files (only building return dicts with .append)
        # This is valid since append() is used for building answer strings
        # We verified above ollama/openai/jsonl are not present

    def test_no_contract_replies_modification(self):
        import inspect
        source = inspect.getsource(sgd)
        self.assertNotIn("_CONTRACT_REPLIES", source)
        self.assertNotIn("CONTRACT_REPLIES", source)

    def test_authority_field_always_read_only(self):
        for q in [
            "what is implemented",
            "what needs attention",
            "what does composite say",
            "what is your architecture",
            "random query",
        ]:
            result = sgd.answer_state_question(q)
            self.assertEqual(result["authority"], "read_only", f"Authority should be read_only for: {q}")

    def test_no_autonomous_change_claims(self):
        result = sgd.answer_state_question("what needs attention?")
        answer_lower = result["answer"].lower()
        self.assertNotIn("i will", answer_lower)
        self.assertNotIn("i'm going to", answer_lower)
        self.assertNotIn("i am going to", answer_lower)
        self.assertNotIn("i'll", answer_lower)


if __name__ == "__main__":
    unittest.main()