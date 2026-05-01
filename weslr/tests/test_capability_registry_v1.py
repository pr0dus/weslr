"""WESLR Capability Registry V1 Tests"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from weslr.capability_registry import (
    _is_valid_entry,
    _normalize_for_search,
    _trigger_matches,
    load_registry,
    list_capabilities,
    get_capability,
    get_by_slash_command,
    search_by_trigger,
    group_capabilities_by_category,
    get_registry_summary,
    _load_raw_entries,
)


class TestIsValidEntry(unittest.TestCase):
    def test_valid_entry(self):
        entry = {
            "capability_id": "test.capability",
            "category": "test/category",
            "label": "Test Capability",
            "status": "live",
            "risk_level": "low",
            "authority": "deterministic",
        }
        self.assertTrue(_is_valid_entry(entry))
    
    def test_missing_capability_id(self):
        entry = {
            "category": "test/category",
            "label": "Test",
            "status": "live",
            "risk_level": "low",
            "authority": "deterministic",
        }
        self.assertFalse(_is_valid_entry(entry))
    
    def test_not_a_dict(self):
        self.assertFalse(_is_valid_entry("not a dict"))
        self.assertFalse(_is_valid_entry(None))
        self.assertFalse(_is_valid_entry(42))


class TestNormalizeForSearch(unittest.TestCase):
    def test_lowercase(self):
        result = _normalize_for_search("WHAT IS THIS")
        self.assertEqual(result, "what is this")
    
    def test_strip_punctuation(self):
        # Apostrophes within words are preserved, standalone punctuation removed
        result = _normalize_for_search("what's up?")
        self.assertEqual(result, "what's up")
    
    def test_preserve_apostrophe(self):
        result = _normalize_for_search("what's")
        self.assertEqual(result, "what's")
    
    def test_multiple_spaces(self):
        result = _normalize_for_search("what   is    this")
        self.assertEqual(result, "what is this")


class TestTriggerMatches(unittest.TestCase):
    def test_exact_phrase_match(self):
        triggers = ["what is entropy", "explain entropy"]
        score, matched = _trigger_matches("what is entropy", triggers)
        self.assertEqual(score, 2)
    
    def test_all_trigger_words_in_phrase(self):
        triggers = ["what is entropy"]
        score, matched = _trigger_matches("can you tell me what is entropy", triggers)
        self.assertEqual(score, 1)
    
    def test_partial_overlap(self):
        triggers = ["what does research say"]
        score, matched = _trigger_matches("what does research say about entropy", triggers)
        self.assertGreater(score, 0)
    
    def test_no_match(self):
        # "fjordsklamps" has no word overlap with any reasonable trigger
        score, matched = _trigger_matches("fjordsklamps xyz nonsense", ["what is entropy"])
        self.assertEqual(score, 0)


class TestLoadRegistry(unittest.TestCase):
    def test_load_registry_default(self):
        entries = load_registry()
        self.assertGreaterEqual(len(entries), 10)
    
    def test_load_registry_returns_list(self):
        entries = load_registry()
        self.assertIsInstance(entries, list)
    
    def test_registry_paths_exist(self):
        entries = load_registry()
        self.assertGreater(len(entries), 0)
        
        for entry in entries:
            self.assertIn("capability_id", entry)
            self.assertIn("category", entry)
            self.assertIn("label", entry)
            self.assertIn("status", entry)


class TestListCapabilities(unittest.TestCase):
    def test_filter_by_category(self):
        results = list_capabilities(category="evidence")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIn("evidence", r["category"].lower())
    
    def test_filter_by_status(self):
        results = list_capabilities(status="live")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertEqual(r["status"], "live")
    
    def test_filter_by_category_and_status(self):
        results = list_capabilities(category="system", status="read_only")
        for r in results:
            self.assertIn("system", r["category"].lower())
            self.assertEqual(r["status"], "read_only")
    
    def test_no_matching_category_returns_empty(self):
        results = list_capabilities(category="nonexistent_category_xyz")
        self.assertEqual(len(results), 0)


class TestGetCapability(unittest.TestCase):
    def test_get_known_capability(self):
        entry = get_capability("evidence.search")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["capability_id"], "evidence.search")
    
    def test_get_unknown_capability(self):
        entry = get_capability("nonexistent.capability")
        self.assertIsNone(entry)
    
    def test_capability_fields(self):
        entry = get_capability("system.capabilities")
        self.assertIsNotNone(entry)
        self.assertIn("slash_commands", entry)
        self.assertIn("natural_triggers", entry)
        self.assertIn("modules", entry)


class TestGetBySlashCommand(unittest.TestCase):
    def test_slash_help(self):
        entry = get_by_slash_command("/help")
        self.assertIsNotNone(entry)
        self.assertIn("/help", entry["slash_commands"])
    
    def test_slash_help_without_leading_slash(self):
        entry = get_by_slash_command("help")
        self.assertIsNotNone(entry)
    
    def test_slash_evidence(self):
        entry = get_by_slash_command("/evidence")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["capability_id"], "evidence.search")
    
    def test_unknown_slash(self):
        entry = get_by_slash_command("/nonexistent")
        self.assertIsNone(entry)


class TestSearchByTrigger(unittest.TestCase):
    def test_search_what_is(self):
        results = search_by_trigger("What is entropy?")
        self.assertGreater(len(results), 0)
        # evidence.search should be prominent
        cap_ids = [r["capability"]["capability_id"] for r in results]
        self.assertIn("evidence.search", cap_ids)
    
    def test_search_capabilities_help(self):
        results = search_by_trigger("what can you do")
        self.assertGreater(len(results), 0)
        cap_ids = [r["capability"]["capability_id"] for r in results]
        self.assertIn("system.capabilities", cap_ids)
    
    def test_search_governance(self):
        results = search_by_trigger("what is unsafe to automate")
        self.assertGreater(len(results), 0)
        cap_ids = [r["capability"]["capability_id"] for r in results]
        self.assertIn("governance.boundaries", cap_ids)
    
    def test_search_identity(self):
        results = search_by_trigger("what is weslr")
        self.assertGreater(len(results), 0)
        cap_ids = [r["capability"]["capability_id"] for r in results]
        self.assertIn("system.identity", cap_ids)


class TestGroupCapabilitiesByCategory(unittest.TestCase):
    def test_groups_exist(self):
        groups = group_capabilities_by_category()
        self.assertGreater(len(groups), 0)
    
    def test_categories_are_strings(self):
        groups = group_capabilities_by_category()
        for category in groups:
            self.assertIsInstance(category, str)
    
    def test_system_state_has_entries(self):
        groups = group_capabilities_by_category()
        if "system/state" in groups:
            self.assertGreater(len(groups["system/state"]), 0)


class TestGetRegistrySummary(unittest.TestCase):
    def test_summary_returns_dict(self):
        summary = get_registry_summary()
        self.assertIsInstance(summary, dict)
    
    def test_summary_has_counts(self):
        summary = get_registry_summary()
        self.assertIn("total_entries", summary)
        self.assertIn("by_category", summary)
        self.assertIn("by_status", summary)
        self.assertGreaterEqual(summary["total_entries"], 10)


class TestMalformedEntriesSkipped(unittest.TestCase):
    def test_malformed_json_returns_empty(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json{{")
            temp_path = Path(f.name)
        
        try:
            entries = _load_raw_entries(temp_path)
            self.assertEqual(len(entries), 0)
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_malformed_entries_in_array_skipped(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([
                {
                    "capability_id": "good.capability",
                    "category": "test",
                    "label": "Good",
                    "status": "live",
                    "risk_level": "low",
                    "authority": "deterministic",
                },
                "not a dict",
                {
                    "category": "missing_id",
                    "label": "Bad",
                    "status": "live",
                    "risk_level": "low",
                    "authority": "deterministic",
                },
                {
                    "capability_id": "another.good",
                    "category": "test",
                    "label": "Another Good",
                    "status": "live",
                    "risk_level": "low",
                    "authority": "deterministic",
                },
            ], f)
            temp_path = Path(f.name)
        
        try:
            entries = _load_raw_entries(temp_path)
            cap_ids = [e["capability_id"] for e in entries]
            self.assertIn("good.capability", cap_ids)
            self.assertIn("another.good", cap_ids)
            self.assertNotIn("not a dict", cap_ids)
        finally:
            temp_path.unlink(missing_ok=True)


class TestNoJSONLWrites(unittest.TestCase):
    def test_no_jsonl_extension_in_code(self):
        registry_path = Path(__file__).resolve().parent.parent / "capability_registry.py"
        content = registry_path.read_text()
        self.assertNotIn(".jsonl", content)


class TestNoOllamaImports(unittest.TestCase):
    def test_no_ollama_in_registry(self):
        registry_path = Path(__file__).resolve().parent.parent / "capability_registry.py"
        content = registry_path.read_text()
        self.assertNotIn("ollama", content.lower())
        self.assertNotIn("OLLAMA", content)


if __name__ == "__main__":
    unittest.main()
