from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ambient_voice_pre_speak_hook import (  # noqa: E402
    AmbientVoicePreSpeakHookInput,
    AmbientVoicePreSpeakHookResult,
    AmbientVoicePreSpeakHookSafetyFlags,
    ambient_voice_pre_speak_hook_input_from_dict,
    ambient_voice_pre_speak_hook_input_to_dict,
    ambient_voice_pre_speak_hook_result_from_dict,
    ambient_voice_pre_speak_hook_result_to_dict,
    ambient_voice_pre_speak_hook_safety_flags_from_dict,
    ambient_voice_pre_speak_hook_safety_flags_to_dict,
    create_empty_ambient_voice_pre_speak_hook_input,
    create_empty_ambient_voice_pre_speak_hook_result,
    validate_ambient_voice_pre_speak_hook_input,
    validate_ambient_voice_pre_speak_hook_result,
    validate_ambient_voice_pre_speak_hook_safety_flags,
)

ALLOWED_CHANGED_FILES = {
    "weslr/ambient_voice_pre_speak_hook.py",
    "weslr/tests/test_ambient_voice_pre_speak_hook_schema_v1.py",
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
        "source_subsystem": "ambient_loop",
        "trigger": "proactive_suggestion",
        "output_channel": "voice",
        "intended_voice_tts_path": "tts/local",
        "output_provenance_id": "out_a",
        "source_registry_entry_id": "src_a",
        "trace_refs": ["trace:a"],
    }
    data.update(overrides)
    return create_empty_ambient_voice_pre_speak_hook_input(**data)


def valid_result(**overrides):
    data = {
        "result_id": "result_a",
        "input_id": "input_a",
        "hook_id": "hook_a",
        "source_subsystem": "ambient_loop",
        "trigger": "proactive_suggestion",
        "output_channel": "voice",
        "intended_voice_tts_path": "tts/local",
        "output_provenance_id": "out_a",
        "source_registry_entry_id": "src_a",
        "attribution_record_id": "attr_a",
        "pre_speak_log_event_id": "event_a",
        "attribution_created": True,
        "attribution_validated": True,
        "speech_allowed": True,
        "unattributed_unknown_required": False,
        "operator_review_required": True,
        "trace_refs": ["trace:a"],
    }
    data.update(overrides)
    return create_empty_ambient_voice_pre_speak_hook_result(**data)


class AmbientVoicePreSpeakHookSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_schema_imports(self):
        self.assertTrue(AmbientVoicePreSpeakHookSafetyFlags)
        self.assertTrue(AmbientVoicePreSpeakHookInput)
        self.assertTrue(AmbientVoicePreSpeakHookResult)
        self.assertTrue(validate_ambient_voice_pre_speak_hook_input)
        self.assertTrue(validate_ambient_voice_pre_speak_hook_result)

    def test_02_safe_defaults(self):
        flags = AmbientVoicePreSpeakHookSafetyFlags()
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_safety_flags(flags))
        self.assertFalse(flags.raw_spoken_text_stored)
        self.assertFalse(flags.runtime_wiring_attempted)
        self.assertFalse(flags.voice_wiring_attempted)

    def test_03_valid_input_and_result_pass(self):
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_input(valid_input()))
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_result(valid_result()))

    def test_04_missing_ids_fail(self):
        self.assertIn("missing input id", validate_ambient_voice_pre_speak_hook_input(valid_input(input_id="")))
        self.assertIn("missing hook id", validate_ambient_voice_pre_speak_hook_input(valid_input(hook_id="")))
        self.assertIn("missing result id", validate_ambient_voice_pre_speak_hook_result(valid_result(result_id="")))
        self.assertIn("missing input id", validate_ambient_voice_pre_speak_hook_result(valid_result(input_id="")))

    def test_05_missing_required_input_fields_fail(self):
        self.assertIn("missing source subsystem", validate_ambient_voice_pre_speak_hook_input(valid_input(source_subsystem="")))
        self.assertIn("missing trigger", validate_ambient_voice_pre_speak_hook_input(valid_input(trigger="")))
        self.assertIn("missing output channel", validate_ambient_voice_pre_speak_hook_input(valid_input(output_channel="")))

    def test_06_llm_assisted_without_provider_model_fails(self):
        self.assertIn("LLM-assisted hook requires provider/model", validate_ambient_voice_pre_speak_hook_input(valid_input(llm_assisted=True)))
        self.assertIn("LLM-assisted hook requires provider/model", validate_ambient_voice_pre_speak_hook_result(valid_result(llm_assisted=True)))

    def test_07_llm_assisted_with_provider_model_validates(self):
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_input(valid_input(llm_assisted=True, model_provider="provider", model_name="model")))
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_result(valid_result(llm_assisted=True, model_provider="provider", model_name="model")))

    def test_08_speech_allowed_without_attribution_fails(self):
        errors = validate_ambient_voice_pre_speak_hook_result(valid_result(attribution_created=False, attribution_validated=False))
        self.assertIn("speech allowed without attribution validated", errors)

    def test_09_speech_allowed_without_provenance_fails(self):
        self.assertIn("speech allowed without output provenance ID", validate_ambient_voice_pre_speak_hook_result(valid_result(output_provenance_id="")))
        self.assertIn("speech allowed without attribution record ID", validate_ambient_voice_pre_speak_hook_result(valid_result(attribution_record_id="")))

    def test_10_speech_allowed_without_trace_refs_fails(self):
        self.assertIn("speech allowed without trace refs", validate_ambient_voice_pre_speak_hook_result(valid_result(trace_refs=[])))

    def test_11_unattributed_unknown_path_validates_when_speech_not_allowed(self):
        item = valid_result(speech_allowed=False, attribution_created=False, attribution_validated=False, output_provenance_id="", attribution_record_id="", trace_refs=[], unattributed_unknown_required=True)
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_result(item))

    def test_12_unattributed_unknown_path_fails_when_not_marked_unknown(self):
        item = valid_result(speech_allowed=False, unattributed_unknown_required=False)
        self.assertIn("blocked speech must be marked unattributed/unknown", validate_ambient_voice_pre_speak_hook_result(item))

    def test_13_speech_allowed_while_unknown_required_fails(self):
        self.assertIn("speech allowed while unattributed/unknown required", validate_ambient_voice_pre_speak_hook_result(valid_result(unattributed_unknown_required=True)))

    def test_14_unsafe_flags_fail(self):
        for field_name in asdict(AmbientVoicePreSpeakHookSafetyFlags()).keys():
            flags = AmbientVoicePreSpeakHookSafetyFlags(**{field_name: True})
            self.assertTrue(validate_ambient_voice_pre_speak_hook_result(valid_result(safety_flags=flags)), field_name)

    def test_15_roundtrip_input_result_flags_to_from_dict(self):
        input_item = valid_input(llm_assisted=True, model_provider="provider", model_name="model")
        result_item = valid_result(llm_assisted=True, model_provider="provider", model_name="model")
        flags = AmbientVoicePreSpeakHookSafetyFlags()
        self.assertEqual(input_item, ambient_voice_pre_speak_hook_input_from_dict(ambient_voice_pre_speak_hook_input_to_dict(input_item)))
        self.assertEqual(result_item, ambient_voice_pre_speak_hook_result_from_dict(ambient_voice_pre_speak_hook_result_to_dict(result_item)))
        self.assertEqual(flags, ambient_voice_pre_speak_hook_safety_flags_from_dict(ambient_voice_pre_speak_hook_safety_flags_to_dict(flags)))

    def test_16_dict_validation_accepts_nested_flags(self):
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_input(ambient_voice_pre_speak_hook_input_to_dict(valid_input())))
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_result(ambient_voice_pre_speak_hook_result_to_dict(valid_result())))

    def test_17_unknown_override_rejected(self):
        with self.assertRaises(ValueError):
            create_empty_ambient_voice_pre_speak_hook_input(unsupported=True)
        with self.assertRaises(ValueError):
            create_empty_ambient_voice_pre_speak_hook_result(unsupported=True)

    def test_18_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_19_only_allowed_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
