from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ambient_voice_provenance_wiring import (  # noqa: E402
    ALLOWED_AMBIENT_VOICE_PROVENANCE_HOOK_TYPES,
    AmbientVoiceProvenanceHookRecord,
    AmbientVoiceProvenanceWiringSafetyFlags,
    ambient_voice_provenance_hook_record_from_dict,
    ambient_voice_provenance_hook_record_to_dict,
    ambient_voice_provenance_wiring_safety_flags_from_dict,
    ambient_voice_provenance_wiring_safety_flags_to_dict,
    create_empty_ambient_voice_provenance_hook_record,
    validate_ambient_voice_provenance_hook_record,
    validate_ambient_voice_provenance_wiring_safety_flags,
)

ALLOWED_CHANGED_FILES = {
    "weslr/ambient_voice_provenance_wiring.py",
    "weslr/tests/test_ambient_voice_provenance_wiring_schema_v1.py",
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


def hook(**overrides):
    data = {
        "hook_id": "hook_a",
        "hook_type": "pre_speak",
        "source_subsystem": "ambient_loop",
        "trigger_type": "proactive_suggestion",
        "intended_output_channel": "voice",
        "trace_refs": ["trace:a"],
    }
    data.update(overrides)
    return create_empty_ambient_voice_provenance_hook_record(**data)


class AmbientVoiceProvenanceWiringSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_schema_imports(self):
        self.assertTrue(AmbientVoiceProvenanceWiringSafetyFlags)
        self.assertTrue(AmbientVoiceProvenanceHookRecord)
        self.assertTrue(create_empty_ambient_voice_provenance_hook_record)
        self.assertTrue(validate_ambient_voice_provenance_hook_record)

    def test_02_safe_defaults(self):
        item = hook()
        self.assertEqual([], validate_ambient_voice_provenance_hook_record(item))
        self.assertEqual([], validate_ambient_voice_provenance_wiring_safety_flags(item.safety_flags))
        self.assertTrue(item.requires_pre_speak_attribution)
        self.assertTrue(item.requires_output_provenance)
        self.assertTrue(item.requires_source_registry_entry)
        self.assertTrue(item.requires_post_speak_confirmation)
        self.assertTrue(item.requires_append_only_log)
        self.assertTrue(item.operator_review_required)

    def test_03_all_hook_types_validate(self):
        for hook_type in ALLOWED_AMBIENT_VOICE_PROVENANCE_HOOK_TYPES:
            item = hook(hook_type=hook_type, source_subsystem="ambient_loop", trace_refs=["trace:a"])
            self.assertEqual([], validate_ambient_voice_provenance_hook_record(item), hook_type)

    def test_04_invalid_hook_type_fails(self):
        self.assertIn("invalid hook type", validate_ambient_voice_provenance_hook_record(hook(hook_type="runtime_wire_now")))

    def test_05_missing_hook_id_fails(self):
        self.assertIn("missing hook id", validate_ambient_voice_provenance_hook_record(hook(hook_id="")))

    def test_06_missing_source_subsystem_fails(self):
        self.assertIn("missing source subsystem", validate_ambient_voice_provenance_hook_record(hook(source_subsystem="")))
        self.assertIn("missing source subsystem", validate_ambient_voice_provenance_hook_record(hook(source_subsystem="unknown")))

    def test_07_llm_assisted_without_provider_model_fails(self):
        errors = validate_ambient_voice_provenance_hook_record(hook(llm_assisted=True, model_provider="", model_name=""))
        self.assertIn("LLM-assisted hook requires provider/model", errors)

    def test_08_llm_assisted_with_provider_model_validates(self):
        self.assertEqual([], validate_ambient_voice_provenance_hook_record(hook(llm_assisted=True, model_provider="local", model_name="small-model")))

    def test_09_post_speak_without_trace_fails(self):
        for hook_type in ["post_speak_success", "post_speak_failure"]:
            errors = validate_ambient_voice_provenance_hook_record(hook(hook_type=hook_type, trace_refs=[]))
            self.assertIn("missing trace refs for post-speak hook", errors)

    def test_10_disabling_provenance_requirements_fails(self):
        for field_name in [
            "requires_pre_speak_attribution",
            "requires_output_provenance",
            "requires_source_registry_entry",
            "requires_post_speak_confirmation",
            "requires_append_only_log",
        ]:
            errors = validate_ambient_voice_provenance_hook_record(hook(**{field_name: False}))
            self.assertIn(f"required provenance field disabled: {field_name}", errors)

    def test_11_unsafe_flags_fail(self):
        for field_name in asdict(AmbientVoiceProvenanceWiringSafetyFlags()).keys():
            flags = AmbientVoiceProvenanceWiringSafetyFlags(**{field_name: True})
            errors = validate_ambient_voice_provenance_hook_record(hook(safety_flags=flags))
            self.assertTrue(errors, field_name)

    def test_12_roundtrip_hook_to_from_dict(self):
        item = hook(hook_type="post_speak_success", llm_assisted=True, model_provider="provider", model_name="model")
        restored = ambient_voice_provenance_hook_record_from_dict(ambient_voice_provenance_hook_record_to_dict(item))
        self.assertEqual(item, restored)
        self.assertEqual([], validate_ambient_voice_provenance_hook_record(restored))

    def test_13_roundtrip_safety_flags_to_from_dict(self):
        flags = AmbientVoiceProvenanceWiringSafetyFlags()
        restored = ambient_voice_provenance_wiring_safety_flags_from_dict(ambient_voice_provenance_wiring_safety_flags_to_dict(flags))
        self.assertEqual(flags, restored)

    def test_14_dict_validation_accepts_nested_safety_flags(self):
        data = ambient_voice_provenance_hook_record_to_dict(hook())
        self.assertEqual([], validate_ambient_voice_provenance_hook_record(data))

    def test_15_unknown_override_rejected(self):
        with self.assertRaises(ValueError):
            create_empty_ambient_voice_provenance_hook_record(hook_id="x", unsupported=True)

    def test_16_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_17_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
