from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_PROVENANCE_SOURCE_REGISTRY_LIFECYCLE_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_PROVENANCE_SOURCE_REGISTRY_LIFECYCLE_DESIGN_V1.md",
    "weslr/tests/test_provenance_source_registry_lifecycle_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/output_provenance.py",
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_router.py",
    "weslr/capability_welcome_surface.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
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


class ProvenanceSourceRegistryLifecycleDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc_text = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
        cls.doc_lower = cls.doc_text.lower()

    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_doc_exists_and_status_markers(self):
        self.assertTrue(DOC_PATH.exists())
        for phrase in [
            "Provenance Source Registry Lifecycle Design V1",
            "design_only",
            "self_improvement_aware",
            "execution_allowed = false",
            "official_score_claimed = false",
            "no_self_activation",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_living_versioned_registry_principle(self):
        for phrase in [
            "registry is not a fixed final list",
            "versioned registration system",
            "future WESLR modules must extend",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_source_entry_and_self_improvement_fields(self):
        for phrase in [
            "source_id",
            "display_name",
            "module_path",
            "source_type",
            "authority_boundary",
            "allowed_outputs",
            "forbidden_outputs",
            "related_docs",
            "related_tests",
            "proposed_by",
            "origin_type",
            "approval_status",
            "created_from_proposal_id",
            "created_from_advisor_review_id",
            "created_from_queue_item_id",
            "activation_allowed",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_origin_categories_present(self):
        for phrase in [
            "operator_added",
            "institution_added",
            "advisor_suggested",
            "local_scan_suggested",
            "weslr_self_review_suggested",
            "self_improvement_proposed",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_self_suggested_and_self_improvement_boundaries(self):
        for phrase in [
            "WESLR-self-suggested modules",
            "self-improvement-derived modules",
            "No self-added capability may bypass registration",
            "operator-approved",
            "automatic activation",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_unknown_unregistered_source_policy(self):
        for phrase in [
            "Unknown/unregistered source policy",
            "authority must be `unknown`",
            "operator review required",
            "no automatic activation",
            "provenance is incomplete",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_registration_contract_and_review_queue_integration(self):
        self.assertIn("Registration contract", self.doc_text)
        self.assertIn("self-improvement-derived modules", self.doc_text)
        self.assertIn("Missing/stale/unsafe source registry coverage should become review queue suggestions", self.doc_text)
        self.assertIn("not automatic changes", self.doc_text)

    def test_llm_advisor_and_institution_extensions(self):
        for phrase in [
            "LLM Advisor integration",
            "LLM advisor output is non-authoritative proposal input",
            "Institution/client extension",
            "on-premise models",
            "air-gapped models",
            "private workflows",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_safety_boundaries_present(self):
        for phrase in [
            "hidden LLM authority",
            "provenance guessing",
            "unregistered voice/proactive output",
            "unregistered self-improvement output",
            "hidden memory mutation",
            "hidden queue writes",
            "hidden runtime actions",
            "answer selection",
            "truth/soundness authority",
            "official score",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_future_phase_names_present(self):
        for phrase in [
            "APPROVE_PROVENANCE_SOURCE_REGISTRY_SCHEMA_ONLY",
            "APPROVE_PROVENANCE_SOURCE_REGISTRY_INITIAL_SEED_ONLY",
            "APPROVE_UNREGISTERED_SOURCE_DETECTION_DESIGN_ONLY",
            "APPROVE_PROVENANCE_SOURCE_REGISTRY_LOCAL_SCAN_HELPERS_ONLY",
            "APPROVE_SELF_IMPROVEMENT_SOURCE_REGISTRATION_DESIGN_ONLY",
            "APPROVE_VOICE_SOURCE_ATTRIBUTION_DESIGN_ONLY",
            "APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY",
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
