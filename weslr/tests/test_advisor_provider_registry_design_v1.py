from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_ADVISOR_PROVIDER_REGISTRY_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_ADVISOR_PROVIDER_REGISTRY_DESIGN_V1.md",
    "weslr/tests/test_advisor_provider_registry_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/advisor_prompt_templates.py",
    "weslr/llm_advisor_mode.py",
    "weslr/logic_teaching_spine.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}


class AdvisorProviderRegistryDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc_text = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
        cls.doc_lower = cls.doc_text.lower()

    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_doc_exists_and_status_markers_present(self):
        self.assertTrue(DOC_PATH.exists())
        self.assertIn("Advisor Provider Registry Design V1", self.doc_text)
        self.assertIn("design_only", self.doc_text)
        self.assertIn("execution_allowed = false", self.doc_text)
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_supports_institution_on_premise_and_air_gapped_models(self):
        for phrase in ["institution-owned llms", "on-premise models", "air-gapped models"]:
            self.assertIn(phrase, self.doc_lower)

    def test_supports_provider_neutral_registry(self):
        self.assertIn("provider-neutral registry", self.doc_lower)
        for phrase in ["openai", "openai-codex", "ollama local", "ollama cloud", "openrouter", "github copilot", "local private models", "domain-specific expert models"]:
            self.assertIn(phrase, self.doc_lower)

    def test_advisor_output_authority_boundary(self):
        self.assertIn("non-authoritative", self.doc_lower)
        self.assertIn("proposal source only", self.doc_lower)
        self.assertIn("requires validation", self.doc_lower)
        self.assertIn("requires operator/institution approval", self.doc_lower)
        self.assertIn("not runtime truth", self.doc_lower)
        self.assertIn("proposal input only", self.doc_lower)

    def test_prompt_template_lifecycle_present(self):
        self.assertIn("prompt-template lifecycle", self.doc_lower)
        self.assertIn("advisor prompt templates are versioned", self.doc_lower)
        self.assertIn("prompts must be revisited as weslr gains capabilities", self.doc_lower)
        for phrase in [
            "new reasoning lane",
            "new domain module",
            "new memory/governance behavior",
            "new runtime actions",
            "changes safety policy",
            "domain-specific advisor",
            "stale or incomplete",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_registry_safety_policy_forbids_required_items(self):
        for phrase in [
            "answer selection",
            "truth/soundness authority",
            "official score claims",
            "answer-key use",
            "benchmark-specific tuning",
            "secrets/api keys/tokens",
            "private user data by default",
            "runtime/config mutation",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_multi_provider_policy_warns_about_routing_and_fallbacks(self):
        self.assertIn("2–5 advisor models", self.doc_text)
        self.assertIn("record model identity", self.doc_lower)
        self.assertIn("record provider identity", self.doc_lower)
        self.assertIn("record failures/timeouts", self.doc_lower)
        self.assertIn("avoid long fallback chains", self.doc_lower)
        self.assertIn("avoid auto-routing when traceability is required", self.doc_lower)

    def test_client_and_institution_support_present(self):
        self.assertIn("institutions may register their own advisor llms", self.doc_lower)
        self.assertIn("bring your own advisor model", self.doc_lower)
        self.assertIn("client-owned advisor models", self.doc_lower)
        self.assertIn("institution-owned advisor models", self.doc_lower)
        self.assertIn("advisor output remains proposal input", self.doc_lower)

    def test_future_phase_names_present(self):
        for phase in [
            "APPROVE_ADVISOR_PROVIDER_REGISTRY_SCHEMA_ONLY",
            "APPROVE_ADVISOR_PROMPT_TEMPLATE_REVIEW_CADENCE_ONLY",
            "APPROVE_OFFLINE_ADVISOR_REVIEW_RUNNER_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phase, self.doc_text)

    def test_no_forbidden_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
