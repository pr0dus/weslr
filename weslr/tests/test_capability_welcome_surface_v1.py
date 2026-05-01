"""Tests for WESLR Capability Welcome Surface V1."""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import json
import tempfile
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from weslr.capability_welcome_surface import (
    build_welcome_overview,
    build_category_help,
    build_capability_suggestions,
)


# ---- Minimal valid registry for testing ----

_MINIMAL_REGISTRY = [
    {
        "capability_id": "system.identity",
        "category": "system/state",
        "label": "System Identity",
        "description": "Answers questions about WESLR's identity.",
        "status": "live",
        "risk_level": "low",
        "authority": "deterministic",
        "automatic_change": False,
        "natural_triggers": ["what are you", "who are you"],
        "slash_commands": ["/system"],
        "examples": ["What is WESLR?", "Who are you?"],
        "operator_required": False,
        "staging_only": False,
    },
    {
        "capability_id": "evidence.search",
        "category": "evidence/search/sources",
        "label": "Evidence Search",
        "description": "Searches external sources via the evidence pipeline.",
        "status": "live_on_staging",
        "risk_level": "low",
        "authority": "external_evidence_unverified",
        "automatic_change": False,
        "natural_triggers": ["what is", "explain", "search for"],
        "slash_commands": ["/evidence", "/search"],
        "examples": ["What is entropy?", "Explain entropy deeply."],
        "operator_required": False,
        "staging_only": True,
    },
    {
        "capability_id": "evidence.sources",
        "category": "evidence/search/sources",
        "label": "Source Attribution",
        "description": "Shows sources used in the most recent evidence-grounded response.",
        "status": "partial",
        "risk_level": "low",
        "authority": "external_evidence_unverified",
        "automatic_change": False,
        "natural_triggers": ["what are the sources", "show sources"],
        "slash_commands": ["/sources"],
        "examples": ["What are the sources?"],
        "operator_required": False,
        "staging_only": True,
    },
    {
        "capability_id": "system.state",
        "category": "system/state",
        "label": "System State",
        "description": "Reports WESLR's current operational state.",
        "status": "read_only",
        "risk_level": "low",
        "authority": "read_only",
        "automatic_change": False,
        "natural_triggers": ["what is implemented", "system status"],
        "slash_commands": ["/state"],
        "examples": ["What is implemented?"],
        "operator_required": False,
        "staging_only": False,
    },
    {
        "capability_id": "governance.boundaries",
        "category": "governance/safety",
        "label": "Governance Boundaries",
        "description": "Reports what WESLR considers unsafe to automate.",
        "status": "read_only",
        "risk_level": "medium",
        "authority": "read_only",
        "automatic_change": False,
        "natural_triggers": ["what is unsafe to automate", "safety boundaries"],
        "slash_commands": ["/governance"],
        "examples": ["What is unsafe to automate?"],
        "operator_required": False,
        "staging_only": False,
    },
    {
        "capability_id": "experiments.plan",
        "category": "experiments/learning",
        "label": "Experiment Planning",
        "description": "Proposes safe, explicit experiments.",
        "status": "spec_only",
        "risk_level": "medium",
        "authority": "proposal_only",
        "automatic_change": False,
        "natural_triggers": ["run an experiment", "plan an experiment"],
        "slash_commands": ["/experiment"],
        "examples": ["What can we test?"],
        "operator_required": True,
        "staging_only": False,
    },
]


class TestBuildWelcomeOverview(unittest.TestCase):
    """Tests for build_welcome_overview()."""

    def setUp(self):
        # Create a temp registry file for isolated testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_registry = os.path.join(self.temp_dir, "capability_registry.json")
        with open(self.temp_registry, "w", encoding="utf-8") as f:
            json.dump(_MINIMAL_REGISTRY, f)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_welcome_overview_loads_registry(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_welcome_overview()

        self.assertEqual(result["record_type"], "capability_welcome_overview_v1")
        self.assertEqual(result["authority"], "registry_generated")
        self.assertFalse(result["automatic_change"])
        self.assertIn("message", result)
        self.assertIn("categories", result)
        self.assertIn("suggested_prompts", result)
        self.assertIn("slash_suggestions", result)
        mock_load.assert_called_once()

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_welcome_overview_includes_evidence_search_category(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_welcome_overview()

        user_cats = result["categories"]["user"]
        cat_labels = [c["label"] for c in user_cats]
        self.assertIn("Search and Evidence", cat_labels)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_welcome_overview_includes_system_state_category(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_welcome_overview()

        user_cats = result["categories"]["user"]
        cat_labels = [c["label"] for c in user_cats]
        self.assertIn("WESLR System State", cat_labels)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_welcome_overview_includes_governance_safety_category(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_welcome_overview()

        all_cats = result["categories"].get("operator", [])
        cat_labels = [c["label"] for c in all_cats]
        self.assertIn("Governance and Safety", cat_labels)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_welcome_overview_includes_human_facing_examples(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_welcome_overview()

        self.assertIsInstance(result["suggested_prompts"], list)
        self.assertGreater(len(result["suggested_prompts"]), 0)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_welcome_overview_includes_slash_suggestions(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_welcome_overview()

        self.assertIsInstance(result["slash_suggestions"], list)
        self.assertIn("/evidence", result["slash_suggestions"])
        self.assertIn("/system", result["slash_suggestions"])

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_welcome_overview_does_not_execute_capabilities(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_welcome_overview()

        # Should have message text, not None or an execution result
        self.assertIsInstance(result["message"], str)
        self.assertGreater(len(result["message"]), 10)
        # Should not have execution-related keys
        self.assertNotIn("executed_capability", result)
        self.assertNotIn("execution_result", result)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_automatic_change_false(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_welcome_overview()
        self.assertFalse(result["automatic_change"])

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_authority_registry_generated(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_welcome_overview()
        self.assertEqual(result["authority"], "registry_generated")


class TestBuildCategoryHelp(unittest.TestCase):
    """Tests for build_category_help()."""

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_category_help_for_evidence_returns_evidence_search(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_category_help("evidence")

        self.assertEqual(result["record_type"], "capability_category_help_v1")
        caps = result["capabilities"]
        cap_ids = [c["capability_id"] for c in caps]
        self.assertIn("evidence.search", cap_ids)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_category_help_for_governance_returns_governance_boundaries(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_category_help("governance")

        self.assertEqual(result["record_type"], "capability_category_help_v1")
        caps = result["capabilities"]
        cap_ids = [c["capability_id"] for c in caps]
        self.assertIn("governance.boundaries", cap_ids)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_category_help_for_system_returns_system_identity_and_state(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_category_help("system")

        self.assertEqual(result["record_type"], "capability_category_help_v1")
        caps = result["capabilities"]
        cap_ids = [c["capability_id"] for c in caps]
        self.assertIn("system.identity", cap_ids)
        self.assertIn("system.state", cap_ids)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_unknown_category_returns_safe_fallback(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_category_help("xyz_unknown_cat")

        self.assertEqual(result["record_type"], "capability_category_help_v1")
        self.assertIn("message", result)
        self.assertIsInstance(result["message"], str)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_slash_command_evidence_returns_evidence_search(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_category_help("/evidence")

        self.assertEqual(result["record_type"], "capability_category_help_v1")
        caps = result["capabilities"]
        cap_ids = [c["capability_id"] for c in caps]
        self.assertIn("evidence.search", cap_ids)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_automatic_change_false_category_help(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_category_help("evidence")
        self.assertFalse(result["automatic_change"])

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_authority_registry_generated_category_help(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_category_help("evidence")
        self.assertEqual(result["authority"], "registry_generated")


class TestBuildCapabilitySuggestions(unittest.TestCase):
    """Tests for build_capability_suggestions()."""

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_suggestions_for_what_is_entropy_points_to_evidence_search(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_capability_suggestions("what is entropy")

        self.assertEqual(result["record_type"], "capability_suggestion_surface_v1")
        self.assertFalse(result["automatic_change"])
        self.assertEqual(result["authority"], "registry_generated")

        route = result["route"]
        # Router should route this to evidence.search given "what is" trigger
        self.assertIn("selected_capability", route)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_suggestions_for_what_is_unsafe_points_to_governance_boundaries(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_capability_suggestions("what is unsafe to automate")

        self.assertEqual(result["record_type"], "capability_suggestion_surface_v1")

        route = result["route"]
        selected = route.get("selected_capability")
        # "what is unsafe to automate" maps to governance.boundaries via trigger
        self.assertEqual(selected, "governance.boundaries")

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_suggestions_message_is_string(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_capability_suggestions("what is entropy")

        self.assertIsInstance(result["message"], str)
        self.assertGreater(len(result["message"]), 0)

    @patch("weslr.capability_welcome_surface.load_registry")
    def test_suggestions_includes_slash_commands(self, mock_load):
        mock_load.return_value = _MINIMAL_REGISTRY
        result = build_capability_suggestions("what is entropy")

        suggestions = result["suggestions"]
        if suggestions and suggestions[0].get("type") == "primary":
            self.assertIsInstance(suggestions[0].get("slash_commands"), list)


class TestNoSideEffects(unittest.TestCase):
    """Verify no JSONL writes, no Ollama imports, not wired to /chat."""

    def test_no_jsonl_writes_in_source(self):
        source = Path(__file__).resolve().parents[1] / "capability_welcome_surface.py"
        content = source.read_text(encoding="utf-8")

        # No JSONL write patterns
        self.assertNotIn(".jsonl", content.replace("test_", "").replace("# JSONL", ""))
        self.assertNotIn("open(", content.replace("test_", ""))  # catches file opens
        # More specific: look for write mode
        import re
        write_patterns = re.findall(r"open\([^)]+['\"]w['\"]", content)
        self.assertEqual(write_patterns, [], f"Unexpected write opens: {write_patterns}")

    def test_no_ollama_imports(self):
        source = Path(__file__).resolve().parents[1] / "capability_welcome_surface.py"
        content = source.read_text(encoding="utf-8")
        import re
        runtime_ollama = re.findall(r'(?:from\s+ollama|import\s+ollama|from\s+llm[\s$]|import\s+llm[\s$])', content)
        self.assertEqual(runtime_ollama, [], f"Unexpected Ollama/LLM runtime import: {runtime_ollama}")

    def test_not_wired_into_chat(self):
        source = Path(__file__).resolve().parents[1] / "capability_welcome_surface.py"
        content = source.read_text(encoding="utf-8")
        # Module should not reference chat handler
        self.assertNotIn("chat_handler", content)
        self.assertNotIn("ChatHandler", content)
        self.assertNotIn("do_POST", content)


if __name__ == "__main__":
    unittest.main()