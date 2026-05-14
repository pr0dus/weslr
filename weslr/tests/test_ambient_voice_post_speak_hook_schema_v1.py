from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ambient_voice_post_speak_hook import (  # noqa: E402
    AmbientVoicePostSpeakHookInput,
    AmbientVoicePostSpeakHookResult,
    AmbientVoicePostSpeakHookSafetyFlags,
    ambient_voice_post_speak_hook_input_from_dict,
    ambient_voice_post_speak_hook_input_to_dict,
    ambient_voice_post_speak_hook_result_from_dict,
    ambient_voice_post_speak_hook_result_to_dict,
    ambient_voice_post_speak_hook_safety_flags_from_dict,
    ambient_voice_post_speak_hook_safety_flags_to_dict,
    create_empty_ambient_voice_post_speak_hook_input,
    create_empty_ambient_voice_post_speak_hook_result,
    validate_ambient_voice_post_speak_hook_input,
    validate_ambient_voice_post_speak_hook_result,
    validate_ambient_voice_post_speak_hook_safety_flags,
)

ALLOWED_CHANGED_FILES = {
    "weslr/ambient_voice_post_speak_hook.py",
    "weslr/tests/test_ambient_voice_post_speak_hook_schema_v1.py",
}
FORBIDDEN_CHANGED_FILES = {
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/tts.py",
    "weslr/stt.py",
    "openclaw.json",
    ".openclaw/config.json",
    "MEMORY.md",
}


def valid_input(**overrides):
    data = {
        "input_id": "input_a",
        "hook_id": "hook_a",
        "pre_speak_result_id": "pre_result_a",
        "utterance_id": "utt_a",
        "output_provenance_id": "out_a",
        "attribution_record_id": "attr_a",
        "pre_speak_log_event_id": "pre_event_a",
        "source_subsystem": "ambient_loop",
        "tts_engine": "tts/local",
        "stt_engine": "stt/local",
        "speech_attempted": True,
        "speech_success": True,
        "speech_failed": False,
        "speech_blocked": False,
        "failure_reason": "",
        "no_ownership_claim_required": True,
        "operator_review_required": True,
        "trace_refs": ["trace:a"],
    }
    data.update(overrides)
    return create_empty_ambient_voice_post_speak_hook_input(**data)


def valid_result(**overrides):
    data = {
        "result_id": "result_a",
        "input_id": "input_a",
        "hook_id": "hook_a",
        "pre_speak_result_id": "pre_result_a",
        "utterance_id": "utt_a",
        "output_provenance_id": "out_a",
        "attribution_record_id": "attr_a",
        "pre_speak_log_event_id": "pre_event_a",
        "post_speak_log_event_id": "post_event_a",
        "source_subsystem": "ambient_loop",
        "tts_engine": "tts/local",
        "stt_engine": "stt/local",
        "speech_attempted": True,
        "speech_success": True,
        "speech_failed": False,
        "speech_blocked": False,
        "failure_reason": "",
        "no_ownership_claim_required": True,
        "operator_review_required": True,
        "trace_refs": ["trace:a"],
    }
    data.update(overrides)
    return create_empty_ambient_voice_post_speak_hook_result(**data)


class AmbientVoicePostSpeakHookSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_schema_imports(self):
        self.assertTrue(AmbientVoicePostSpeakHookSafetyFlags)
        self.assertTrue(AmbientVoicePostSpeakHookInput)
        self.assertTrue(AmbientVoicePostSpeakHookResult)
        self.assertTrue(validate_ambient_voice_post_speak_hook_input)
        self.assertTrue(validate_ambient_voice_post_speak_hook_result)

    def test_02_safe_defaults(self):
        flags = AmbientVoicePostSpeakHookSafetyFlags()
        self.assertEqual([], validate_ambient_voice_post_speak_hook_safety_flags(flags))
        self.assertFalse(flags.raw_spoken_text_stored)
        self.assertFalse(flags.runtime_wiring_attempted)
        self.assertFalse(flags.voice_wiring_attempted)

    def test_03_valid_input_and_result_pass(self):
        self.assertEqual([], validate_ambient_voice_post_speak_hook_input(valid_input()))
        self.assertEqual([], validate_ambient_voice_post_speak_hook_result(valid_result()))

    def test_04_missing_ids_fail(self):
        self.assertIn("missing input id", validate_ambient_voice_post_speak_hook_input(valid_input(input_id="")))
        self.assertIn("missing hook id", validate_ambient_voice_post_speak_hook_input(valid_input(hook_id="")))
        self.assertIn("missing result id", validate_ambient_voice_post_speak_hook_result(valid_result(result_id="")))
        self.assertIn("missing input id", validate_ambient_voice_post_speak_hook_result(valid_result(input_id="")))

    def test_05_missing_required_references_fail(self):
        cases = [
            ("pre_speak_result_id", "missing pre-speak result ID"),
            ("utterance_id", "missing utterance ID"),
            ("output_provenance_id", "missing output provenance ID"),
            ("attribution_record_id", "missing attribution record ID"),
        ]
        for field, error in cases:
            self.assertIn(error, validate_ambient_voice_post_speak_hook_input(valid_input(**{field: ""})))
            self.assertIn(error, validate_ambient_voice_post_speak_hook_result(valid_result(**{field: ""})))

    def test_06_success_without_attempted_fails(self):
        self.assertIn("speech success without speech attempted", validate_ambient_voice_post_speak_hook_result(valid_result(speech_attempted=False)))

    def test_07_success_and_failure_conflict_fails(self):
        self.assertIn("speech success and failure both true", validate_ambient_voice_post_speak_hook_result(valid_result(speech_failed=True, failure_reason="failed")))

    def test_08_blocked_and_success_conflict_fails(self):
        self.assertIn("speech blocked and speech success both true", validate_ambient_voice_post_speak_hook_result(valid_result(speech_blocked=True, failure_reason="blocked")))

    def test_09_success_without_trace_refs_fails(self):
        self.assertIn("speech success without trace refs", validate_ambient_voice_post_speak_hook_result(valid_result(trace_refs=[])))

    def test_10_failure_without_reason_fails(self):
        result = valid_result(speech_success=False, speech_failed=True, failure_reason="", no_ownership_claim_required=True)
        self.assertIn("speech failure without failure reason", validate_ambient_voice_post_speak_hook_result(result))

    def test_11_blocked_without_reason_fails(self):
        result = valid_result(speech_attempted=False, speech_success=False, speech_blocked=True, failure_reason="", no_ownership_claim_required=True)
        self.assertIn("speech blocked without failure reason", validate_ambient_voice_post_speak_hook_result(result))

    def test_12_no_ownership_rule_enforced_when_speech_not_emitted(self):
        result = valid_result(speech_success=False, speech_failed=True, failure_reason="tts_failed", no_ownership_claim_required=False)
        self.assertIn("ownership claim allowed when speech was not emitted", validate_ambient_voice_post_speak_hook_result(result))

    def test_13_failure_and_blocked_valid_when_reason_and_no_ownership_claim(self):
        failed = valid_result(speech_success=False, speech_failed=True, failure_reason="tts_failed", no_ownership_claim_required=True)
        blocked = valid_result(speech_attempted=False, speech_success=False, speech_blocked=True, failure_reason="pre_speak_blocked", no_ownership_claim_required=True)
        self.assertEqual([], validate_ambient_voice_post_speak_hook_result(failed))
        self.assertEqual([], validate_ambient_voice_post_speak_hook_result(blocked))

    def test_14_unsafe_flags_fail(self):
        for field_name in asdict(AmbientVoicePostSpeakHookSafetyFlags()).keys():
            flags = AmbientVoicePostSpeakHookSafetyFlags(**{field_name: True})
            self.assertTrue(validate_ambient_voice_post_speak_hook_result(valid_result(safety_flags=flags)), field_name)

    def test_15_roundtrip_input_result_flags_to_from_dict(self):
        input_item = valid_input()
        result_item = valid_result()
        flags = AmbientVoicePostSpeakHookSafetyFlags()
        self.assertEqual(input_item, ambient_voice_post_speak_hook_input_from_dict(ambient_voice_post_speak_hook_input_to_dict(input_item)))
        self.assertEqual(result_item, ambient_voice_post_speak_hook_result_from_dict(ambient_voice_post_speak_hook_result_to_dict(result_item)))
        self.assertEqual(flags, ambient_voice_post_speak_hook_safety_flags_from_dict(ambient_voice_post_speak_hook_safety_flags_to_dict(flags)))

    def test_16_dict_validation_accepts_nested_flags(self):
        self.assertEqual([], validate_ambient_voice_post_speak_hook_input(ambient_voice_post_speak_hook_input_to_dict(valid_input())))
        self.assertEqual([], validate_ambient_voice_post_speak_hook_result(ambient_voice_post_speak_hook_result_to_dict(valid_result())))

    def test_17_unknown_override_rejected(self):
        with self.assertRaises(ValueError):
            create_empty_ambient_voice_post_speak_hook_input(unsupported=True)
        with self.assertRaises(ValueError):
            create_empty_ambient_voice_post_speak_hook_result(unsupported=True)

    def test_18_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_19_only_allowed_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
