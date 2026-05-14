#!/usr/bin/env python3
"""Focused tests for Frontier Intelligence chat metadata-only shadow mode V1."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.chat_responder import handle_request  # noqa: E402


SHADOW_KEY = "_frontier_intelligence_shadow"
MESSAGE = "lunch before workout"


def _request(**extra):
    request = {
        "request_mode": "chat",
        "message": MESSAGE,
        "chat_context": ["dev/test in-memory context only"],
        "chat_hints": ["prefers concise"],
    }
    request.update(extra)
    return request


def _weslr_state_snapshot():
    state_dir = ROOT / ".weslr"
    if not state_dir.exists():
        return []
    return sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*"))


class FrontierIntelligenceChatDryRunMetadataV1Tests(unittest.TestCase):
    def base_response(self):
        with mock.patch("weslr.chat_responder.generate_chat", side_effect=AssertionError("model call not allowed")):
            return handle_request(_request())

    def shadow_response(self, **extra):
        with mock.patch("weslr.chat_responder.generate_chat", side_effect=AssertionError("model call not allowed")):
            return handle_request(_request(frontier_intelligence_shadow=True, **extra))

    def test_01_existing_chat_output_unchanged_when_shadow_flag_absent(self):
        baseline = self.base_response()
        repeat = self.base_response()
        self.assertEqual(baseline.content, repeat.content)
        self.assertNotIn(SHADOW_KEY, baseline.metadata or {})

    def test_02_no_frontier_metadata_when_shadow_flag_absent(self):
        response = self.base_response()
        self.assertNotIn(SHADOW_KEY, response.metadata or {})

    def test_03_shadow_metadata_appears_only_when_explicit_flag_present(self):
        without = self.base_response()
        with_shadow = self.shadow_response()
        self.assertNotIn(SHADOW_KEY, without.metadata or {})
        self.assertIn(SHADOW_KEY, with_shadow.metadata or {})
        self.assertTrue(with_shadow.metadata[SHADOW_KEY]["enabled"])
        self.assertEqual("dry_run_metadata_only", with_shadow.metadata[SHADOW_KEY]["mode"])

    def test_04_response_content_is_unchanged_when_shadow_flag_present(self):
        without = self.base_response()
        with_shadow = self.shadow_response()
        self.assertEqual(without.content, with_shadow.content)

    def test_05_native_candidate_is_not_returned_as_final_answer(self):
        response = self.shadow_response()
        shadow = response.metadata[SHADOW_KEY]
        candidate_preview = shadow["preview_card"].get("candidate_preview_summary", [])
        self.assertFalse(shadow["candidate_returned_as_content"])
        self.assertNotEqual(response.content, candidate_preview)
        self.assertNotIn(response.content, [str(item) for item in candidate_preview])

    def test_06_runtime_output_flags_remain_false(self):
        shadow = self.shadow_response().metadata[SHADOW_KEY]
        for key in ["safe_to_wire_runtime", "final_chat_output", "live_runtime_output", "candidate_returned_as_content"]:
            self.assertFalse(shadow[key], key)
        dry_summary = shadow["dry_slice_summary"]
        for key in ["safe_to_wire_runtime", "final_chat_output", "live_runtime_output", "candidate_returned_as_content"]:
            self.assertFalse(dry_summary[key], key)

    def test_07_dry_slice_and_preview_metadata_exists_in_shadow_mode(self):
        shadow = self.shadow_response().metadata[SHADOW_KEY]
        self.assertTrue(shadow["dry_slice_summary"]["slice_id"])
        self.assertEqual("frontier_intelligence_preview_card_v1", shadow["preview_card"]["card_type"])
        self.assertEqual("frontier_intelligence_preview_card_v1", shadow["preview_summary"]["card_type"])
        self.assertIn("validation_status", shadow)

    def test_08_shadow_build_failure_does_not_break_existing_reply(self):
        baseline = self.base_response()
        with mock.patch("weslr.native_response_dry_slice.build_native_response_dry_slice_v1", side_effect=RuntimeError("forced dry failure")):
            failed = handle_request(_request(frontier_intelligence_shadow=True))
        self.assertEqual(baseline.content, failed.content)
        shadow = failed.metadata[SHADOW_KEY]
        self.assertTrue(shadow["shadow_build_failed"])
        self.assertFalse(shadow["safe_to_wire_runtime"])
        self.assertFalse(shadow["candidate_returned_as_content"])

    def test_09_no_model_calls_from_chat_shadow_path(self):
        response = self.shadow_response()
        shadow = response.metadata[SHADOW_KEY]
        self.assertFalse(shadow["side_effects"]["model_calls"])
        self.assertFalse(shadow["dry_slice_summary"]["side_effects"]["model_calls"])
        self.assertFalse(shadow["preview_card"]["side_effects"]["model_calls"])

    def test_10_no_weslr_writes_by_shadow_default(self):
        before = _weslr_state_snapshot()
        self.shadow_response()
        after = _weslr_state_snapshot()
        self.assertEqual(before, after)

    def test_11_no_voice_ambient_ui_cli_runner_scoring_changes_claimed(self):
        shadow = self.shadow_response().metadata[SHADOW_KEY]
        side_effects = shadow["side_effects"]
        for key in [
            "chat_or_voice_changes",
            "ui_or_frontend_integration",
            "cli_integration",
            "runner",
            "scoring_engine",
            "runtime_wiring",
            "persistence",
            "weslr_runtime_state_created",
        ]:
            self.assertFalse(side_effects[key], key)

    def test_12_no_protected_items_or_official_claims_or_fake_memory_in_metadata(self):
        shadow = self.shadow_response().metadata[SHADOW_KEY]
        encoded = json.dumps(shadow, sort_keys=True).lower()
        forbidden = [
            "answer key",
            "answer_key",
            "hidden prompt",
            "hidden_prompt",
            "protected item",
            "official iq",
            "official score",
            "certified",
            "certification claim",
            "i remember you personally",
            "mystical consciousness",
        ]
        for marker in forbidden:
            self.assertNotIn(marker, encoded)

    def test_13_no_auto_approval_or_auto_implementation(self):
        shadow = self.shadow_response().metadata[SHADOW_KEY]
        self.assertFalse(shadow["side_effects"]["auto_approval"])
        self.assertFalse(shadow["side_effects"]["auto_implementation"])

    def test_14_no_prompt_specific_hardcoded_chatbot_script_added_to_shadow_helper(self):
        source = (ROOT / "weslr" / "chat_responder.py").read_text()
        helper = source.split("def _build_frontier_intelligence_shadow_metadata", 1)[1].split("from .request_parser", 1)[0]
        self.assertNotIn("elif ", helper)
        self.assertNotIn("if user asks", helper.lower())
        shadow = self.shadow_response().metadata[SHADOW_KEY]
        self.assertFalse(shadow["side_effects"]["prompt_specific_script"])

    def test_15_shadow_flag_supported_in_request_metadata(self):
        response = handle_request(_request(metadata={"frontier_intelligence_shadow": True}))
        self.assertIn(SHADOW_KEY, response.metadata or {})


if __name__ == "__main__":
    unittest.main()
