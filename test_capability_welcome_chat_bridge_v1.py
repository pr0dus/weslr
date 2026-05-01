"""Tests for WESLR Capability Welcome Chat Bridge V1."""

import unittest
from unittest.mock import patch
from pathlib import Path
import sys
import re

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from weslr.capability_welcome_chat_bridge import (
    is_capability_welcome_query,
    maybe_answer_with_capability_welcome,
)


class TestIsCapabilityWelcomeQuery(unittest.TestCase):
    """Tests for is_capability_welcome_query()."""

    def _true_cases(self):
        return [
            "what can you do",
            "What can you do?",
            "what can you help me with",
            "what should i try",
            "Help",
            "welcome",
            "besides these",
            "what else can you do",
            "/help",
            "/HELP",
            "/capabilities",
        ]

    def _false_cases(self):
        return [
            "what is weslr",
            "what are you",
            "what is entropy",
            "explain entropy",
            "what is unsafe to automate",
            "what are the sources",
            "/evidence",
            "/system",
            "/governance",
            "/attention",
            "/sources",
            "who are you",
            "tell me about yourself",
            "show sources",
        ]

    def test_true_cases(self):
        for msg in self._true_cases():
            with self.subTest(msg=msg):
                self.assertTrue(
                    is_capability_welcome_query(msg),
                    f"Expected True for: {msg!r}",
                )

    def test_false_cases(self):
        for msg in self._false_cases():
            with self.subTest(msg=msg):
                self.assertFalse(
                    is_capability_welcome_query(msg),
                    f"Expected False for: {msg!r}",
                )

    def test_empty_message_false(self):
        self.assertFalse(is_capability_welcome_query(""))
        self.assertFalse(is_capability_welcome_query(None))

    def test_near_miss_what_is_weslr(self):
        """'what is weslr' is identity, not capability overview."""
        self.assertFalse(is_capability_welcome_query("what is weslr"))
        self.assertFalse(is_capability_welcome_query("what is WESLR?"))

    def test_slash_evidence_blocked(self):
        self.assertFalse(is_capability_welcome_query("/evidence"))
        self.assertFalse(is_capability_welcome_query("/evidence search"))

    def test_slash_system_blocked(self):
        self.assertFalse(is_capability_welcome_query("/system"))
        self.assertFalse(is_capability_welcome_query("/state"))

    def test_slash_governance_blocked(self):
        self.assertFalse(is_capability_welcome_query("/governance"))
        self.assertFalse(is_capability_welcome_query("/governance boundaries"))

    def test_capability_welcome_query_besides_these(self):
        """'besides these' is a capability overview trigger."""
        self.assertTrue(is_capability_welcome_query("besides these"))
        self.assertTrue(is_capability_welcome_query("besides these?"))


class TestMaybeAnswerWithCapabilityWelcome(unittest.TestCase):
    """Tests for maybe_answer_with_capability_welcome()."""

    def _mock_overview(self, message="Test welcome message"):
        return {"message": message}

    @patch("weslr.capability_welcome_surface.build_welcome_overview")
    def test_bridge_returns_path_capability_welcome(self, mock_overview):
        mock_overview.return_value = {"message": "Test welcome message"}
        result = maybe_answer_with_capability_welcome("what can you do", {})
        self.assertIsNotNone(result)
        self.assertEqual(result["path"], "capability_welcome")

    @patch("weslr.capability_welcome_surface.build_welcome_overview")
    def test_reply_includes_human_facing_categories(self, mock_overview):
        mock_overview.return_value = {
            "message": (
                "Here are the main ways I can help:\n\n"
                "**Search and Evidence**\n  • Evidence Search\n"
                "**WESLR System State**\n  • System State\n"
                "**Governance and Safety**\n  • Governance Boundaries"
            )
        }
        result = maybe_answer_with_capability_welcome("what can you do", {})
        self.assertIn("Search and Evidence", result["reply"])
        self.assertIn("WESLR System State", result["reply"])
        self.assertIn("Governance and Safety", result["reply"])

    @patch("weslr.capability_welcome_surface.build_welcome_overview")
    def test_metadata_authority_registry_generated(self, mock_overview):
        mock_overview.return_value = {"message": "Test"}
        result = maybe_answer_with_capability_welcome("what can you do", {})
        self.assertEqual(
            result["_capability_metadata"]["authority"], "registry_generated"
        )

    @patch("weslr.capability_welcome_surface.build_welcome_overview")
    def test_metadata_automatic_change_false(self, mock_overview):
        mock_overview.return_value = {"message": "Test"}
        result = maybe_answer_with_capability_welcome("what can you do", {})
        self.assertFalse(result["_capability_metadata"]["automatic_change"])

    def test_non_welcome_message_returns_none(self):
        result = maybe_answer_with_capability_welcome("what is entropy", {})
        self.assertIsNone(result)

    @patch("weslr.capability_welcome_surface.build_welcome_overview")
    def test_fallback_when_build_overview_raises(self, mock_overview):
        mock_overview.side_effect = Exception("registry unavailable")
        result = maybe_answer_with_capability_welcome("what can you do", {})
        self.assertIsNotNone(result)
        self.assertEqual(result["path"], "capability_welcome")
        self.assertIn("Search and Evidence", result["reply"])

    @patch("weslr.capability_welcome_surface.build_welcome_overview")
    def test_response_contract_guided_help(self, mock_overview):
        mock_overview.return_value = {"message": "Test"}
        result = maybe_answer_with_capability_welcome("what can you do", {})
        self.assertEqual(result["response_contract"], "guided_help")


class TestNoSideEffects(unittest.TestCase):
    """Verify no JSONL writes, no Ollama imports, no evidence pipeline calls."""

    def _read_bridge_source(self):
        return (
            Path(__file__).resolve().parents[0]
            / "weslr"
            / "capability_welcome_chat_bridge.py"
        ).read_text(encoding="utf-8")

    def test_no_jsonl_writes_in_source(self):
        content = self._read_bridge_source()
        write_opens = re.findall(r"open\([^)]*['\"]w['\"]", content)
        self.assertEqual(write_opens, [], f"Unexpected JSONL write opens: {write_opens}")

    def test_no_ollama_imports(self):
        content = self._read_bridge_source()
        runtime_ollama = re.findall(
            r"(?:from\s+ollama|import\s+ollama|from\s+llm[\s$]|import\s+llm[\s$])",
            content,
        )
        self.assertEqual(
            runtime_ollama, [], f"Unexpected Ollama/LLM runtime import: {runtime_ollama}"
        )

    def test_no_evidence_pipeline_imports(self):
        content = self._read_bridge_source()
        self.assertNotIn("evidence_pipeline", content)
        self.assertNotIn("evidence_chat_bridge", content)


class TestStagingServerIntegration(unittest.TestCase):
    """Verify staging demo server contains capability welcome bridge call."""

    def _read_staging_server(self):
        return (
            Path(__file__).resolve().parents[0]
            / "deploy"
            / "staging"
            / "weslr_demo_server.py"
        ).read_text(encoding="utf-8")

    def test_staging_server_has_capability_welcome_bridge_before_evidence_bridge(self):
        content = self._read_staging_server()

        cw_pos = content.find("capability_welcome_chat_bridge")
        ev_pos = content.find("evidence_chat_bridge")

        self.assertNotEqual(
            cw_pos, -1, "capability_welcome_chat_bridge not found in staging server"
        )
        self.assertNotEqual(
            ev_pos, -1, "evidence_chat_bridge not found in staging server"
        )
        self.assertLess(
            cw_pos, ev_pos,
            "capability welcome bridge must appear BEFORE evidence bridge in staging server"
        )

    def test_staging_server_bridge_exception_safe(self):
        content = self._read_staging_server()

        # Capability welcome bridge block must be wrapped in try/except pass
        bridge_block = re.search(
            r"from weslr\.capability_welcome_chat_bridge import maybe_answer_with_capability_welcome"
            r".*?_bridge_result = maybe_answer_with_capability_welcome\("
            r".*?if _bridge_result.*?"
            r"except Exception:\s*pass",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(
            bridge_block, "capability welcome bridge try/except pass block not found"
        )


if __name__ == "__main__":
    unittest.main()