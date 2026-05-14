from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ambient_voice_pre_speak_hook import (  # noqa: E402
    AmbientVoicePreSpeakHookSafetyFlags,
    create_blocked_pre_speak_hook_result,
    create_pre_speak_hook_input_from_metadata,
    create_pre_speak_hook_result_from_input,
    summarize_pre_speak_hook_result,
    summarize_pre_speak_hook_results,
    validate_ambient_voice_pre_speak_hook_input,
    validate_ambient_voice_pre_speak_hook_result,
)

ALLOWED_CHANGED_FILES = {
    "weslr/ambient_voice_pre_speak_hook.py",
    "weslr/tests/test_ambient_voice_pre_speak_hook_helpers_v1.py",
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


def metadata(**overrides):
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
    return data


def valid_input(**overrides):
    return create_pre_speak_hook_input_from_metadata(**metadata(**overrides))


class AmbientVoicePreSpeakHookHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_helper_module_imports(self):
        self.assertTrue(create_pre_speak_hook_input_from_metadata)
        self.assertTrue(create_pre_speak_hook_result_from_input)
        self.assertTrue(create_blocked_pre_speak_hook_result)
        self.assertTrue(summarize_pre_speak_hook_result)
        self.assertTrue(summarize_pre_speak_hook_results)

    def test_02_valid_metadata_creates_input(self):
        item = valid_input()
        self.assertEqual("input_a", item.input_id)
        self.assertEqual("ambient_loop", item.source_subsystem)
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_input(item))

    def test_03_valid_input_creates_speech_allowed_result_only_with_attribution_provenance_trace_refs(self):
        result = create_pre_speak_hook_result_from_input(
            valid_input(),
            result_id="result_a",
            attribution_record_id="attr_a",
            pre_speak_log_event_id="event_a",
        )
        self.assertTrue(result.speech_allowed)
        self.assertFalse(result.unattributed_unknown_required)
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_result(result))

    def test_04_missing_attribution_blocks_speech(self):
        result = create_pre_speak_hook_result_from_input(valid_input(), result_id="result_a", attribution_record_id="")
        self.assertFalse(result.speech_allowed)
        self.assertTrue(result.unattributed_unknown_required)
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_result(result))

    def test_05_missing_provenance_blocks_speech(self):
        result = create_pre_speak_hook_result_from_input(valid_input(output_provenance_id=""), result_id="result_a", attribution_record_id="attr_a")
        self.assertFalse(result.speech_allowed)
        self.assertTrue(result.unattributed_unknown_required)
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_result(result))

    def test_06_missing_trace_refs_blocks_speech(self):
        result = create_pre_speak_hook_result_from_input(valid_input(trace_refs=[]), result_id="result_a", attribution_record_id="attr_a")
        self.assertFalse(result.speech_allowed)
        self.assertTrue(result.unattributed_unknown_required)
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_result(result))

    def test_07_llm_assisted_without_provider_model_fails(self):
        item = valid_input(llm_assisted=True, model_provider="", model_name="")
        self.assertIn("LLM-assisted hook requires provider/model", validate_ambient_voice_pre_speak_hook_input(item))
        result = create_pre_speak_hook_result_from_input(item, result_id="result_a", attribution_record_id="attr_a")
        self.assertFalse(result.speech_allowed)

    def test_08_blocked_result_validates(self):
        result = create_blocked_pre_speak_hook_result(valid_input(), result_id="blocked_a")
        self.assertFalse(result.speech_allowed)
        self.assertTrue(result.unattributed_unknown_required)
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_result(result))

    def test_09_unattributed_unknown_path_validates(self):
        result = create_pre_speak_hook_result_from_input(valid_input(), result_id="result_a")
        self.assertFalse(result.speech_allowed)
        self.assertTrue(result.unattributed_unknown_required)
        self.assertEqual([], validate_ambient_voice_pre_speak_hook_result(result))

    def test_10_summaries_are_redacted_count_only(self):
        allowed = create_pre_speak_hook_result_from_input(valid_input(), result_id="allowed", attribution_record_id="attr_a", pre_speak_log_event_id="event_a")
        blocked = create_blocked_pre_speak_hook_result(valid_input(), result_id="blocked")
        one = summarize_pre_speak_hook_result(allowed)
        many = summarize_pre_speak_hook_results([allowed, blocked])
        self.assertEqual("redacted_count_only", one["summary_mode"])
        self.assertEqual("redacted_count_only", many["summary_mode"])
        self.assertEqual(2, many["result_count"])
        rendered = json.dumps({"one": one, "many": many}).lower()
        for forbidden in ["api key", "token", "secret", "raw spoken", "transcript", "private user data"]:
            self.assertNotIn(forbidden, rendered)

    def test_11_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_12_no_runtime_voice_wiring_or_side_effects(self):
        result = create_pre_speak_hook_result_from_input(valid_input(), result_id="result_a", attribution_record_id="attr_a")
        summary = summarize_pre_speak_hook_result(result)
        self.assertFalse(summary["runtime_voice_wiring_performed"])
        self.assertFalse(summary["log_write_performed"])
        self.assertFalse(summary["queue_write_performed"])
        self.assertFalse(summary["memory_mutation_performed"])
        self.assertFalse(summary["model_call_performed"])

    def test_13_unsafe_flags_block_result(self):
        flags = AmbientVoicePreSpeakHookSafetyFlags(raw_spoken_text_stored=True)
        item = valid_input(safety_flags=flags)
        result = create_pre_speak_hook_result_from_input(item, result_id="result_a", attribution_record_id="attr_a")
        self.assertFalse(result.speech_allowed)
        self.assertIn("raw spoken text storage", validate_ambient_voice_pre_speak_hook_result(result))

    def test_14_only_allowed_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
