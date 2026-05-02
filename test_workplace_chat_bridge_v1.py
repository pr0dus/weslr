"""
WESLR Workplace Chat Bridge V1 — Tests

Tests:
- is_workplace_query detection
- is_workplace_query ignores non-workplace queries
- maybe_answer_with_workplace returns None for non-workplace
- maybe_answer_with_workplace returns dict for workplace queries
- response has correct structure and metadata
- no execution/approval/rejection
- no evidence pipeline imports/calls
- no Ollama imports
- registry contains workplace.overview
- staging server contains workplace_chat_bridge between continuity and capability welcome
"""

import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

WORKSPACE = pathlib.Path(__file__).resolve().parents[0]
sys.path.insert(0, str(WORKSPACE))

from weslr.workplace_chat_bridge import is_workplace_query, maybe_answer_with_workplace


class TestIsWorkplaceQuery(unittest.TestCase):

    TRIGGERS = [
        "what are we working on",
        "show my workplace",
        "workplace overview",
        "what ideas are pending",
        "what experiments are pending",
        "pending ideas",
        "pending experiments",
        "what should we continue",
        "/workplace",
        "/ideas",
        "/experiments",
    ]

    IGNORES = [
        "what is entropy",
        "what is WESLR",
        "what can you do",
        "do you remember what we worked on",
        "/evidence",
        "/state",
        "continuity note from last session",
    ]

    def test_triggers_detected(self):
        for msg in self.TRIGGERS:
            with self.subTest(msg=msg):
                self.assertTrue(is_workplace_query(msg), f"Expected True for: {msg}")

    def test_ignores_non_workplace(self):
        for msg in self.IGNORES:
            with self.subTest(msg=msg):
                self.assertFalse(is_workplace_query(msg), f"Expected False for: {msg}")


class TestMaybeAnswerWithWorkplace(unittest.TestCase):

    WORKPLACE_QUERIES = [
        "what are we working on",
        "/workplace",
        "/ideas",
        "/experiments",
    ]

    def test_non_workplace_returns_none(self):
        result = maybe_answer_with_workplace("what is entropy")
        self.assertIsNone(result)

    def test_workplace_query_returns_dict(self):
        for msg in self.WORKPLACE_QUERIES:
            with self.subTest(msg=msg):
                result = maybe_answer_with_workplace(msg)
                self.assertIsInstance(result, dict, f"Expected dict for: {msg}")

    def test_response_structure(self):
        result = maybe_answer_with_workplace("what are we working on")
        self.assertIn("path", result)
        self.assertIn("response_contract", result)
        self.assertIn("reply", result)
        self.assertIn("_workplace_metadata", result)

    def test_path_is_workplace_overview(self):
        result = maybe_answer_with_workplace("/workplace")
        self.assertEqual(result["path"], "workplace_overview")

    def test_response_contract_is_system_answer(self):
        result = maybe_answer_with_workplace("/workplace")
        self.assertEqual(result["response_contract"], "system_answer")

    def test_metadata_authority_read_only(self):
        result = maybe_answer_with_workplace("/workplace")
        meta = result["_workplace_metadata"]
        self.assertEqual(meta["authority"], "read_only_workplace")

    def test_metadata_safety_flags(self):
        result = maybe_answer_with_workplace("/workplace")
        meta = result["_workplace_metadata"]
        self.assertFalse(meta.get("automatic_action"))
        self.assertFalse(meta.get("hidden_learning"))
        self.assertFalse(meta.get("raw_prompt_stored"))

    def test_metadata_counts_present(self):
        result = maybe_answer_with_workplace("/workplace")
        meta = result["_workplace_metadata"]
        self.assertIn("pending_experiments", meta)
        self.assertIn("recent_ideas", meta)


class TestNoForbiddenImports(unittest.TestCase):

    def test_no_ollama_imports(self):
        bridge_path = WORKSPACE / "weslr" / "workplace_chat_bridge.py"
        content = bridge_path.read_text()
        self.assertNotIn("ollama", content.lower())
        self.assertNotIn("openai", content.lower())

    def test_no_evidence_pipeline_calls(self):
        bridge_path = WORKSPACE / "weslr" / "workplace_chat_bridge.py"
        content = bridge_path.read_text()
        self.assertNotIn("evidence_pipeline", content)
        self.assertNotIn("evidence_chat_bridge", content)


class TestCapabilityRegistry(unittest.TestCase):

    def test_workplace_overview_capability_exists(self):
        registry_path = WORKSPACE / "weslr" / "capability_registry.json"
        registry = json.loads(registry_path.read_text())
        ids = [c["capability_id"] for c in registry]
        self.assertIn("workplace.overview", ids)

    def test_workplace_capability_fields(self):
        registry_path = WORKSPACE / "weslr" / "capability_registry.json"
        registry = json.loads(registry_path.read_text())
        cap = next(c for c in registry if c["capability_id"] == "workplace.overview")
        self.assertEqual(cap["status"], "experimental")
        self.assertEqual(cap["risk_level"], "low")
        self.assertEqual(cap["authority"], "read_only_workplace")
        self.assertFalse(cap["automatic_change"])
        self.assertFalse(cap["operator_required"])


class TestStagingServerIntegration(unittest.TestCase):

    def test_workplace_bridge_in_staging_server(self):
        server_path = WORKSPACE / "deploy" / "staging" / "weslr_demo_server.py"
        content = server_path.read_text()
        self.assertIn("workplace_chat_bridge", content)

    def test_workplace_bridge_order(self):
        """workplace bridge must appear after continuity but before capability welcome."""
        server_path = WORKSPACE / "deploy" / "staging" / "weslr_demo_server.py"
        content = server_path.read_text()
        lines = content.split("\n")

        continuity_pos = None
        workplace_pos = None
        capability_pos = None

        for i, line in enumerate(lines):
            if "continuity_note_chat_bridge" in line and "from weslr" in line:
                continuity_pos = i
            if "workplace_chat_bridge" in line and "from weslr" in line:
                workplace_pos = i
            if "capability_welcome_chat_bridge" in line and "from weslr" in line:
                capability_pos = i

        self.assertIsNotNone(continuity_pos, "continuity_note_chat_bridge not found")
        self.assertIsNotNone(workplace_pos, "workplace_chat_bridge not found")
        self.assertIsNotNone(capability_pos, "capability_welcome_chat_bridge not found")

        self.assertGreater(workplace_pos, continuity_pos,
                           "workplace_chat_bridge must come AFTER continuity_note_chat_bridge")
        self.assertLess(workplace_pos, capability_pos,
                        "workplace_chat_bridge must come BEFORE capability_welcome_chat_bridge")


if __name__ == "__main__":
    unittest.main()
