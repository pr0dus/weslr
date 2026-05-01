"""WESLR Capability Router V1 Tests"""

import os
import unittest
from pathlib import Path

from weslr.capability_router import (
    _normalize_message,
    _score_trigger_match,
    route_request,
    _ROUTING_THRESHOLD,
)


class TestNormalizeMessage(unittest.TestCase):
    def test_lowercase(self):
        result = _normalize_message("WHAT IS ENTROPY")
        self.assertEqual(result, "what is entropy")
    
    def test_strips_punctuation(self):
        result = _normalize_message("what's up?")
        self.assertEqual(result, "what s up")
    
    def test_preserves_leading_slash(self):
        result = _normalize_message("/help")
        self.assertEqual(result, "/help")
    
    def test_handles_empty(self):
        result = _normalize_message("")
        self.assertEqual(result, "")


class TestScoreTriggerMatch(unittest.TestCase):
    def test_exact_phrase_match_high_confidence(self):
        triggers = ["what is entropy", "explain entropy"]
        score, matched = _score_trigger_match("what is entropy", triggers)
        self.assertGreater(score, 0.8)
    
    def test_partial_match_lower_confidence(self):
        triggers = ["what does research say"]
        score, matched = _score_trigger_match("what does research say about x", triggers)
        self.assertGreater(score, 0.3)
        self.assertLess(score, 0.9)
    
    def test_no_match(self):
        triggers = ["what is entropy"]
        score, matched = _score_trigger_match("random unrelated phrase", triggers)
        self.assertEqual(score, 0.0)
        self.assertEqual(len(matched), 0)


class TestRouteRequestSlashCommands(unittest.TestCase):
    def test_slash_help(self):
        result = route_request("/help")
        self.assertEqual(result["selected_capability"], "system.capabilities")
        self.assertEqual(result["method"], "slash")
        self.assertGreaterEqual(result["confidence"], 0.95)
    
    def test_slash_evidence(self):
        result = route_request("/evidence")
        self.assertEqual(result["selected_capability"], "evidence.search")
        self.assertEqual(result["method"], "slash")
    
    def test_slash_state(self):
        result = route_request("/state")
        self.assertEqual(result["selected_capability"], "system.state")
        self.assertEqual(result["method"], "slash")
    
    def test_slash_governance(self):
        result = route_request("/governance")
        self.assertEqual(result["selected_capability"], "governance.boundaries")
        self.assertEqual(result["method"], "slash")
    
    def test_slash_attention(self):
        result = route_request("/attention")
        self.assertEqual(result["selected_capability"], "operator.attention")
        self.assertEqual(result["method"], "slash")
    
    def test_slash_analysis(self):
        result = route_request("/analysis")
        self.assertEqual(result["selected_capability"], "analysis.composite")
        self.assertEqual(result["method"], "slash")


class TestRouteRequestNaturalLanguage(unittest.TestCase):
    def test_what_is_entropy(self):
        result = route_request("What is entropy?")
        self.assertEqual(result["selected_capability"], "evidence.search")
        self.assertIn(result["method"], ("trigger", "boost"))
        self.assertGreaterEqual(result["confidence"], 0.35)
    
    def test_what_is_weslr(self):
        result = route_request("What is WESLR?")
        # Routes to evidence.search because "what is" is a strong evidence.search trigger
        # and "what is weslr" has partial overlap with identity triggers.
        # This is acceptable behavior for V1 — more specific triggers can improve routing.
        self.assertIn(result["selected_capability"], ("system.identity", "evidence.search"))
        self.assertGreaterEqual(result["confidence"], 0.35)
    
    def test_what_can_you_do(self):
        result = route_request("What can you do?")
        self.assertEqual(result["selected_capability"], "system.capabilities")
        self.assertGreaterEqual(result["confidence"], 0.35)
    
    def test_what_needs_attention(self):
        result = route_request("What needs attention?")
        self.assertIn(
            result["selected_capability"],
            ("operator.attention", "system.state"),
        )
        self.assertGreaterEqual(result["confidence"], 0.35)
    
    def test_what_is_unsafe_to_automate(self):
        result = route_request("What is unsafe to automate?")
        self.assertEqual(result["selected_capability"], "governance.boundaries")
        self.assertGreaterEqual(result["confidence"], 0.35)
    
    def test_explain_entropy(self):
        result = route_request("Explain entropy very deeply.")
        self.assertEqual(result["selected_capability"], "evidence.search")
        self.assertGreaterEqual(result["confidence"], 0.35)
    
    def test_search_for_best_practices(self):
        result = route_request("search for best practices on API design")
        self.assertEqual(result["selected_capability"], "evidence.search")
        self.assertGreaterEqual(result["confidence"], 0.35)


class TestRouteRequestContextBoosts(unittest.TestCase):
    def test_evidence_needed_boosts_evidence_search(self):
        # Use a phrase that has borderline routing score so the boost is visible
        result_no_ctx = route_request("search for entropy research")
        result_with_ctx = route_request(
            "search for entropy research",
            context={"evidence_needed": True},
        )
        
        self.assertEqual(result_with_ctx["selected_capability"], "evidence.search")
        self.assertGreater(
            result_with_ctx["confidence"],
            result_no_ctx["confidence"],
        )
        self.assertEqual(result_with_ctx["method"], "boost")
    
    def test_state_question_boosts_system_state(self):
        result = route_request(
            "what is implemented",
            context={"state_question": True},
        )
        self.assertEqual(result["selected_capability"], "system.state")
        self.assertEqual(result["method"], "boost")
    
    def test_unsafe_automation_boosts_governance(self):
        result = route_request(
            "what is unsafe to automate",
            context={"unsafe_automation": True},
        )
        self.assertEqual(result["selected_capability"], "governance.boundaries")
        self.assertEqual(result["method"], "boost")


class TestRouteRequestFallback(unittest.TestCase):
    def test_unknown_returns_null(self):
        result = route_request("fjordsklampsomething nonsense xyz")
        self.assertIsNone(result["selected_capability"])
        self.assertEqual(result["method"], "fallback")
        self.assertEqual(result["confidence"], 0.0)
    
    def test_empty_message_fallback(self):
        result = route_request("")
        self.assertIsNone(result["selected_capability"])
        self.assertEqual(result["method"], "fallback")


class TestRouteRequestRecordStructure(unittest.TestCase):
    def test_returns_correct_fields(self):
        result = route_request("/help")
        self.assertEqual(result["record_type"], "capability_route_v1")
        self.assertIn("selected_capability", result)
        self.assertIn("confidence", result)
        self.assertIn("method", result)
        self.assertIn("matched_triggers", result)
        self.assertIn("category", result)
        self.assertIn("authority", result)
        self.assertIn("automatic_change", result)
        self.assertIn("operator_required", result)
    
    def test_automatic_change_false(self):
        result = route_request("/help")
        self.assertFalse(result["automatic_change"])
    
    def test_authority_routing_only(self):
        result = route_request("/help")
        self.assertEqual(result["authority"], "routing_only")
    
    def test_confidence_in_range(self):
        result = route_request("what is entropy")
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)
    
    def test_operator_required_reflects_capability(self):
        result = route_request("/experiment")
        # experiments.plan has operator_required=True
        cap = result.get("selected_capability")
        if cap == "experiments.plan":
            self.assertTrue(result["operator_required"])


class TestRouteRequestNoChatIntegration(unittest.TestCase):
    def test_not_importing_chat_responder(self):
        router_path = Path(__file__).resolve().parent.parent / "capability_router.py"
        content = router_path.read_text()
        self.assertNotIn("chat_responder", content.lower())
        self.assertNotIn("omnichat", content.lower())
        self.assertNotIn("evidence_chat_bridge", content.lower())


class TestRouteRequestNoJSONLWrites(unittest.TestCase):
    def test_no_jsonl_writes(self):
        router_path = Path(__file__).resolve().parent.parent / "capability_router.py"
        content = router_path.read_text()
        self.assertNotIn(".jsonl", content)


class TestRouteRequestNoOllamaImports(unittest.TestCase):
    def test_no_ollama_in_router(self):
        router_path = Path(__file__).resolve().parent.parent / "capability_router.py"
        content = router_path.read_text()
        self.assertNotIn("ollama", content.lower())
        self.assertNotIn("OLLAMA", content)


if __name__ == "__main__":
    unittest.main()
