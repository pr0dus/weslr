from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_LOCAL_SCAN_ADVISOR_QUEUE_MAPPING_HELPERS_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_LOCAL_SCAN_ADVISOR_QUEUE_MAPPING_HELPERS_DESIGN_V1.md",
    "weslr/tests/test_local_scan_advisor_queue_mapping_helpers_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/local_scan_advisor_review.py",
    "weslr/advisor_review_queue.py",
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_discovery/review.py",
    "weslr/advisor_prompt_templates.py",
    "weslr/llm_advisor_mode.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}


class LocalScanAdvisorQueueMappingHelpersDesignV1Tests(unittest.TestCase):
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
        self.assertIn("Local Scan Advisor Queue Mapping Helpers Design V1", self.doc_text)
        self.assertIn("design_only", self.doc_text)
        self.assertIn("execution_allowed = false", self.doc_text)
        self.assertIn("official_score_claimed = false", self.doc_text)
        self.assertIn("no_queue_writes", self.doc_text)
        self.assertIn("no_external_model_calls", self.doc_text)

    def test_source_target_mapping_present(self):
        self.assertIn("LocalScanFinding / LocalScanReport → AdvisorReviewQueueItem", self.doc_text)
        for phrase in [
            "finding_id can become linked note/source reference",
            "finding_type maps to suggestion_type",
            "trigger_reason maps to trigger_reason",
            "affected_templates maps to affected_templates",
            "affected_providers maps to affected_providers",
            "capability_scope maps to capability_scope",
            "risk_level maps to risk_level",
            "recommended_action maps to recommended_action",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_safe_defaults_present(self):
        self.assertIn("advisor_call_mode = local_scan_only", self.doc_text)
        self.assertIn("advisor_call_allowed = false", self.doc_text)
        self.assertIn("requires_operator_approval = true", self.doc_text)
        self.assertIn("source = local_scan", self.doc_text)
        self.assertIn("review_status = pending_review", self.doc_text)
        self.assertIn("operator_decision = pending_review", self.doc_text)

    def test_forbidden_behaviors_present(self):
        for phrase in [
            "no file writes",
            "no persistence",
            "no queue mutation",
            "no model calls",
            "no advisor calls",
            "no cron/daemon scheduling",
            "no runtime/config changes",
            "no prompt mutation",
            "no provider activation",
            "no memory mutation",
            "no governance override",
            "no answer selection",
            "no truth/soundness claim",
            "no official score",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_validation_failure_creates_no_queue_proposal(self):
        self.assertIn("If either validation fails, helper returns validation errors and creates no queue proposal.", self.doc_text)
        self.assertIn("source LocalScanFinding", self.doc_text)
        self.assertIn("target AdvisorReviewQueueItem", self.doc_text)
        self.assertIn("fail closed", self.doc_lower)

    def test_candidate_preview_not_queue_creation(self):
        self.assertIn("in-memory AdvisorReviewQueueItem proposals", self.doc_text)
        self.assertIn("candidate queue item previews only", self.doc_lower)
        self.assertIn("not actual queue creation", self.doc_lower)

    def test_redaction_requirements_present(self):
        for phrase in [
            "redacted/count-only",
            "raw benchmark text",
            "secrets",
            "api keys",
            "tokens",
            "private user data",
            "answer keys",
            "official scores",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_future_phase_names_present(self):
        for phase in [
            "APPROVE_LOCAL_SCAN_ADVISOR_QUEUE_MAPPING_HELPERS_ONLY",
            "APPROVE_ADVISOR_REVIEW_QUEUE_PERSISTENCE_DESIGN_ONLY",
            "APPROVE_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_HELPERS_ONLY",
            "APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phase, self.doc_text)

    def test_non_goals_present(self):
        for phrase in [
            "no helper implementation in this phase",
            "no file persistence design beyond in-memory candidate previews",
            "no queue writing behavior",
            "no local scan execution",
            "no scheduler/cron/daemon",
            "no model calls",
            "no runtime integration",
            "no openclaw config changes",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_no_forbidden_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
