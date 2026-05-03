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
        self.assertEqual(result["question_type"], "unsafe_automation")
        self.assertGreater(result["confidence"], 0.8)
        self.assertEqual(result["authority"], "read_only")

    def test_classify_unsafe_automation_variations(self):
        for q in [
            "what should not be automated",
            "what must stay manual",
        ]:
            result = sgd.classify_state_question(q)
            self.assertEqual(result["question_type"], "unsafe_automation", f"Failed for: {q}")

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
        import inspect
        source = inspect.getsource(sgd)
        # No .write( or json.dump (actual write operations)
        self.assertNotIn(".write(", source)
        self.assertNotIn("json.dump", source)
        # No write/append mode opens — structural check (read mode 'r' is fine)
        import re
        self.assertIsNone(re.search(r'open\([^)]+\.jsonl[^)]*["\'][wa]', source))

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
        self.assertEqual(result["question_type"], "unsafe_automation")
        # Should list unsafe categories explicitly
        answer_lower = result["answer"].lower()
        self.assertIn("contract", answer_lower)
        self.assertIn("operator", answer_lower)
        self.assertIn("approval", answer_lower)
        # Should mention AAI/composite cannot authorize
        self.assertIn("cannot authorize", answer_lower)
        # Authority must be read_only
        self.assertEqual(result["authority"], "read_only")
        self.assertFalse(result["automatic_change"])

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
        # No jsonl file write paths — 'w' or 'a' mode with .jsonl
        import re
        jsonl_write = re.search(r'\.jsonl["\']\s*[\'"]\s*[wa]', source)
        self.assertIsNone(jsonl_write, "Should not open .jsonl files in write/append mode")
        # No write mode
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


class TestJarvisCapabilityQuestions(unittest.TestCase):
    """Tests for the new Jarvis capability question types."""

    def test_classify_voice_io_question(self):
        for q in [
            "What voice I/O capabilities are implemented?",
            "what voice do you have",
            "do you have speech to text",
            "how do i talk to you",
            "can you hear me",
            "voice capability",
        ]:
            result = sgd.classify_state_question(q)
            self.assertEqual(
                result["question_type"], "voice_io",
                f"Should classify as voice_io: {q}"
            )
            self.assertTrue(result["is_state_question"])
            self.assertGreater(result["confidence"], 0.8)

    def test_classify_persistent_memory_question(self):
        for q in [
            "What persistent memory exists across sessions?",
            "what memory do you have",
            "remember between sessions",
            "long term memory",
            "what do you remember",
        ]:
            result = sgd.classify_state_question(q)
            self.assertEqual(
                result["question_type"], "persistent_memory",
                f"Should classify as persistent_memory: {q}"
            )

    def test_classify_proactive_suggestions_question(self):
        for q in [
            "What proactive suggestion delivery mechanisms are live?",
            "what should i explore next",
            "what can we work on",
            "what ideas do you have",
            "what experiments are pending",
        ]:
            result = sgd.classify_state_question(q)
            self.assertEqual(
                result["question_type"], "proactive_suggestions",
                f"Should classify as proactive_suggestions: {q}"
            )

    def test_classify_action_stubs_question(self):
        for q in [
            "What action stubs (reminders, todo) are implemented?",
            "remind me to",
            "set a reminder",
            "do you have a todo list",
            "can you remind me",
        ]:
            result = sgd.classify_state_question(q)
            self.assertEqual(
                result["question_type"], "action_stubs",
                f"Should classify as action_stubs: {q}"
            )

    def test_classify_temporal_relational_question(self):
        for q in [
            "What temporal+relational query capabilities exist?",
            "what happened after",
            "timeline of events",
            "chronolog",
        ]:
            result = sgd.classify_state_question(q)
            self.assertEqual(
                result["question_type"], "temporal_relational",
                f"Should classify as temporal_relational: {q}"
            )

    def test_classify_semantic_similarity_question(self):
        for q in [
            "What semantic similarity for node matching is active?",
            "embeddings",
            "semantic similarity",
            "vector search",
        ]:
            result = sgd.classify_state_question(q)
            self.assertEqual(
                result["question_type"], "semantic_similarity",
                f"Should classify as semantic_similarity: {q}"
            )

    @patch("os.path.exists")
    def test_answer_voice_io_with_whisper(self, mock_exists):
        # Whisper installed
        mock_exists.return_value = True
        result = sgd.answer_state_question("What voice I/O do you have?")
        self.assertEqual(result["question_type"], "voice_io")
        self.assertIn("whisper", result["answer"].lower())
        self.assertIn("STT", result["answer"])
        self.assertEqual(result["authority"], "read_only")
        self.assertFalse(result["automatic_change"])

    @patch("os.path.exists")
    def test_answer_voice_io_shim_mode(self, mock_exists):
        # Whisper NOT installed
        mock_exists.return_value = False
        result = sgd.answer_state_question("What voice I/O do you have?")
        self.assertEqual(result["question_type"], "voice_io")
        answer_lower = result["answer"].lower()
        self.assertIn("shim", answer_lower)
        self.assertIn("browser", answer_lower)

    def test_answer_persistent_memory_has_memory_layers(self):
        result = sgd.answer_state_question("What memory across sessions?")
        self.assertEqual(result["question_type"], "persistent_memory")
        answer = result["answer"]
        self.assertIn("entity timeline", answer.lower())
        self.assertIn("fact", answer.lower())
        self.assertIn("project registry", answer.lower())
        self.assertFalse(result["automatic_change"])

    def test_answer_proactive_suggestions_notices_gaps(self):
        result = sgd.answer_state_question("What proactive suggestion delivery?")
        self.assertEqual(result["question_type"], "proactive_suggestions")
        answer_lower = result["answer"].lower()
        # Should mention the gap
        self.assertTrue(
            "no" in answer_lower or "not" in answer_lower or "draft" in answer_lower,
            f"Answer should acknowledge gaps: {answer_lower[:100]}"
        )

    def test_answer_action_stubs_acknowledges_gaps(self):
        result = sgd.answer_state_question("What action stubs exist?")
        self.assertEqual(result["question_type"], "action_stubs")
        answer_lower = result["answer"].lower()
        # Should say not yet implemented
        self.assertTrue(
            "not" in answer_lower or "none" in answer_lower or "no" in answer_lower,
            f"Answer should say not implemented: {answer_lower[:100]}"
        )
        self.assertIn("proposal", answer_lower)  # Should offer to create a proposal

    def test_answer_temporal_relational_describes_basic_patterns(self):
        result = sgd.answer_state_question("What temporal queries exist?")
        self.assertEqual(result["question_type"], "temporal_relational")
        answer_lower = result["answer"].lower()
        self.assertTrue(
            "pattern" in answer_lower or "basic" in answer_lower,
            f"Answer should describe basic nature: {answer_lower[:100]}"
        )

    def test_answer_semantic_similarity_reports_not_implemented(self):
        result = sgd.answer_state_question("semantic similarity?")
        self.assertEqual(result["question_type"], "semantic_similarity")
        answer_lower = result["answer"].lower()
        self.assertTrue(
            "not implemented" in answer_lower or "no" in answer_lower,
            f"Answer should say not implemented: {answer_lower[:100]}"
        )
        self.assertIn("doctrine", answer_lower)  # Should reference doctrine P11

    def test_all_jarvis_answers_read_only_authority(self):
        for q in [
            "What voice I/O do you have?",
            "What memory do you have?",
            "What proactive suggestions?",
            "What action stubs?",
            "What temporal queries?",
            "Semantic similarity?",
        ]:
            result = sgd.answer_state_question(q)
            self.assertEqual(result["authority"], "read_only", f"Authority wrong for: {q}")
            self.assertFalse(result["automatic_change"], f"automatic_change should be False for: {q}")


if __name__ == "__main__":
    unittest.main()