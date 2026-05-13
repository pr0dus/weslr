from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_DESIGN_V1.md",
    "weslr/tests/test_local_scan_only_advisor_review_adapter_design_v1.py",
}
FORBIDDEN_CHANGED = {
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


class LocalScanOnlyAdvisorReviewAdapterDesignV1Tests(unittest.TestCase):
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
        self.assertIn("Local Scan Only Advisor Review Adapter Design V1", self.doc_text)
        self.assertIn("design_only", self.doc_text)
        self.assertIn("execution_allowed = false", self.doc_text)
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_one_shot_local_scan_present(self):
        self.assertIn("one-shot local scan", self.doc_lower)
        self.assertIn("detect advisor-review needs", self.doc_lower)
        self.assertIn("without calling external models", self.doc_lower)

    def test_forbidden_behavior_present(self):
        for phrase in [
            "no external model calls",
            "no automatic advisor calls",
            "no automatic implementation",
            "no automatic prompt mutation",
            "no provider activation",
            "no runtime/config changes",
            "no memory mutation",
            "no governance override",
            "no answer selection",
            "no truth/soundness claim",
            "no official score",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_inputs_and_detection_scope_present(self):
        for phrase in [
            "advisor prompt template library",
            "advisor provider registry records",
            "advisor review queue items",
            "recent weslr capability checkpoints",
            "release gate/check results",
            "unsupported-gap trends",
            "stale prompt-template versions",
            "provider health notes",
            "monthly/quarterly/manual review is due",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_queue_integration_defaults_present(self):
        self.assertIn("AdvisorReviewQueueItem", self.doc_text)
        self.assertIn("local_scan_only", self.doc_text)
        self.assertIn("advisor_call_allowed = false", self.doc_text)
        self.assertIn("requires_operator_approval = true", self.doc_text)
        self.assertIn("AdvisorReviewQueueSafetyFlags", self.doc_text)

    def test_operator_flow_present(self):
        self.assertIn("local scan → queue suggestion → operator review → optional advisor call approval → advisor records/proposals/tests later", self.doc_text)

    def test_institution_client_on_prem_air_gapped_policy_present(self):
        self.assertIn("institution/client", self.doc_lower)
        self.assertIn("on-prem", self.doc_lower)
        self.assertIn("air-gapped", self.doc_lower)
        self.assertIn("manual-only", self.doc_lower)
        self.assertIn("monthly", self.doc_lower)
        self.assertIn("quarterly", self.doc_lower)
        self.assertIn("external advisor calls require separate operator/institution approval", self.doc_lower)

    def test_agentic_next_step_review_principle_present(self):
        self.assertIn("agentic next-step review principle", self.doc_lower)
        self.assertIn("the next bottleneck", self.doc_lower)
        self.assertIn("the safest next operator decision", self.doc_lower)
        self.assertIn("what should explicitly not be done yet", self.doc_lower)
        self.assertIn("must not implement the suggestion without operator approval", self.doc_lower)

    def test_future_phase_names_present(self):
        for phase in [
            "APPROVE_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_SCHEMA_ONLY",
            "APPROVE_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_HELPERS_ONLY",
            "APPROVE_ADVISOR_REVIEW_QUEUE_PERSISTENCE_DESIGN_ONLY",
            "APPROVE_OPERATOR_APPROVED_ADVISOR_CALL_FLOW_DESIGN_ONLY",
            "APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phase, self.doc_text)

    def test_non_goals_present(self):
        for phrase in [
            "no implementation in this phase",
            "no file persistence design beyond conceptual queue item creation",
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
