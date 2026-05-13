from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_SELF_USE_PROVENANCE_ARCHITECTURE_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_SELF_USE_PROVENANCE_ARCHITECTURE_DESIGN_V1.md",
    "weslr/tests/test_self_use_provenance_architecture_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_router.py",
    "weslr/capability_registry.py",
    "weslr/capability_welcome_surface.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_prompt_templates.py",
    "weslr/llm_advisor_mode.py",
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}


class SelfUseProvenanceArchitectureDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc_text = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
        cls.doc_lower = cls.doc_text.lower()

    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_doc_exists_and_has_status_markers(self):
        self.assertTrue(DOC_PATH.exists())
        for phrase in [
            "Self-Use Provenance Architecture Design V1",
            "design_only",
            "execution_allowed = false",
            "official_score_claimed = false",
            "no_runtime_integration",
            "no_external_model_calls",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_unified_output_provenance_envelope_fields_present(self):
        self.assertIn("Unified output provenance envelope", self.doc_text)
        for phrase in [
            "generated_by",
            "source_modules",
            "trigger",
            "authority_level",
            "llm_assisted",
            "advisor_assisted",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_source_registry_and_self_use_queries_present(self):
        self.assertIn("Source registry concept", self.doc_text)
        for phrase in [
            "who said that?",
            "what did you notice?",
            "why did you suggest this?",
            "which part of you generated this?",
            "where can this take me?",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_voice_proactive_attribution_rules_present(self):
        self.assertIn("Voice/proactive attribution", self.doc_text)
        self.assertIn("proactive/voice utterances require attribution", self.doc_text)
        self.assertIn("WESLR should answer from provenance records, not guess", self.doc_text)

    def test_capability_guidance_self_review_and_advisor_integration_present(self):
        self.assertIn("Capability guidance surface", self.doc_text)
        self.assertIn("Self-review and suggestion integration", self.doc_text)
        self.assertIn("LLM Advisor integration", self.doc_text)
        self.assertIn("LLM advisor output is non-authoritative proposal input only", self.doc_text)

    def test_safety_boundaries_present(self):
        for phrase in [
            "hidden LLM authority",
            "hidden memory mutation",
            "hidden queue writes",
            "hidden runtime actions",
            "provenance guessing",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_future_phase_names_present(self):
        for phrase in [
            "APPROVE_OUTPUT_PROVENANCE_ENVELOPE_SCHEMA_ONLY",
            "APPROVE_PROVENANCE_SOURCE_REGISTRY_DESIGN_ONLY",
            "APPROVE_VOICE_SOURCE_ATTRIBUTION_DESIGN_ONLY",
            "APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY",
            "APPROVE_CAPABILITY_GUIDANCE_SURFACE_V2_DESIGN_ONLY",
            "APPROVE_SELF_REVIEW_SUGGESTION_INTEGRATION_DESIGN_ONLY",
            "APPROVE_LLM_ADVISOR_PROVENANCE_REVIEW_TEMPLATE_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_no_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
