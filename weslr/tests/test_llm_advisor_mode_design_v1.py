from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_LLM_ADVISOR_MODE_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_LLM_ADVISOR_MODE_DESIGN_V1.md",
    "weslr/tests/test_llm_advisor_mode_design_v1.py",
}
FORBIDDEN_CHANGED = {
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


class LlmAdvisorModeDesignV1Tests(unittest.TestCase):
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
        self.assertIn("LLM Advisor Mode Design V1", self.doc_text)
        for phrase in [
            "design_only",
            "execution_allowed = false",
            "official_score_claimed = false",
            "no_runtime_integration",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_core_doctrine_present(self):
        self.assertIn("LLMs advise; WESLR decides through governance", self.doc_text)
        self.assertIn("LLM output is proposal input, not truth", self.doc_text)
        self.assertIn("LLM output cannot mutate memory, contracts, policies, or runtime behavior directly", self.doc_text)

    def test_allowed_advisor_tasks_present(self):
        for phrase in [
            "architecture review",
            "failure diagnosis",
            "style review",
            "test suggestion",
            "synthetic example suggestion",
            "reasoning-pattern review",
            "gap taxonomy review",
            "wording-risk review",
            "alternative design proposals",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_forbidden_advisor_tasks_present(self):
        for phrase in [
            "answer selection",
            "truth/soundness authority",
            "official score claim",
            "benchmark-specific tuning",
            "answer-key use",
            "hidden state mutation",
            "memory overwrite",
            "policy/governance override",
            "runtime action without operator approval",
            "using advisor output as final proof",
            "extracting/copying model internals",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_input_rules_forbid_sensitive_and_raw_inputs(self):
        for phrase in [
            "no raw benchmark text by default",
            "no secrets",
            "no private user data unless explicitly approved",
            "no API keys/tokens/config secrets",
            "prefer diagnostics/counts/schema summaries over raw data",
        ]:
            self.assertIn(phrase.lower(), self.doc_lower)

    def test_output_handling_is_non_authoritative(self):
        for phrase in [
            "non_authoritative",
            "proposal_candidate",
            "requires_validation",
            "requires_operator_review",
            "not_runtime_truth",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_multi_model_review_policy_present(self):
        self.assertIn("Multi-Model Review Policy", self.doc_text)
        self.assertIn("use 2–5 advisors", self.doc_text)
        self.assertIn("do not use long fallback chains", self.doc_text)
        self.assertIn("do not let auto-routing hide which model answered", self.doc_text)

    def test_advisor_record_fields_present(self):
        for field in [
            "advisor_review_id",
            "advisor_model",
            "advisor_provider",
            "task_type",
            "input_summary_hash",
            "response_summary",
            "recommendations",
            "risks",
            "disagreements",
            "consensus_group",
            "safety_flags",
            "operator_decision",
            "accepted_items",
            "rejected_items",
            "created_tests",
            "created_proposals",
            "created_diagnostics",
            "timestamp",
        ]:
            self.assertIn(field, self.doc_text)

    def test_governance_flow_present(self):
        self.assertIn(
            "diagnostic/problem → advisor prompt → advisor responses → consensus summary → WESLR proposal/test → validation → operator decision → implementation",
            self.doc_text,
        )

    def test_connects_to_synthetic_teaching_lane(self):
        self.assertIn("Connection to Current Synthetic Teaching Lane", self.doc_text)
        self.assertIn("synthetic curriculum → proof step → teaching explanation", self.doc_text)
        for phrase in [
            "explanation style",
            "gap taxonomy",
            "test coverage",
            "synthetic curriculum expansion",
            "proof-step pattern mapping",
            "but only as proposal input",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_operator_decisions_present(self):
        for phrase in [
            "APPROVE_LLM_ADVISOR_RECORD_SCHEMA_ONLY",
            "APPROVE_ADVISOR_PROMPT_TEMPLATE_LIBRARY_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_no_forbidden_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
