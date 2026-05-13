from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_ADVISOR_REVIEW_QUEUE_ADAPTER_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_ADVISOR_REVIEW_QUEUE_ADAPTER_DESIGN_V1.md",
    "weslr/tests/test_advisor_review_queue_adapter_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/advisor_prompt_templates.py",
    "weslr/llm_advisor_mode.py",
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_discovery/review.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}


class AdvisorReviewQueueAdapterDesignV1Tests(unittest.TestCase):
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
        self.assertIn("Advisor Review Queue Adapter Design V1", self.doc_text)
        self.assertIn("design_only", self.doc_text)
        self.assertIn("execution_allowed = false", self.doc_text)
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_one_shot_and_no_daemon_boundaries_present(self):
        self.assertIn("one-shot adapter", self.doc_lower)
        self.assertIn("no resident advisor daemon in v1", self.doc_lower)
        self.assertIn("no new daemon", self.doc_lower)
        self.assertIn("no background loop", self.doc_lower)
        self.assertIn("no cron job in this design phase", self.doc_lower)

    def test_existing_suggestion_and_review_queues_mentioned(self):
        for phrase in [
            "pending_messages_queue",
            "capability discovery review queue",
            "review_queue.json",
            "suggestion box / proposal review surfaces",
            "continuity/suggestion_box",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_advisor_call_modes_present(self):
        self.assertIn("local_scan_only", self.doc_text)
        self.assertIn("operator_approved_advisor_call", self.doc_text)

    def test_forbidden_automatic_behavior_present(self):
        for phrase in [
            "no automatic model calls unless operator-approved",
            "no automatic implementation",
            "no automatic prompt mutation",
            "no automatic provider activation",
            "no runtime/config changes",
            "no memory mutation",
            "no governance override",
            "no answer selection",
            "no truth/soundness claim",
            "no official score",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_queue_item_fields_present(self):
        for field in [
            "suggestion_id",
            "suggestion_type",
            "source",
            "trigger_reason",
            "affected_templates",
            "affected_providers",
            "capability_scope",
            "risk_level",
            "recommended_action",
            "requires_operator_approval",
            "advisor_call_allowed",
            "created_at",
            "status",
        ]:
            self.assertIn(field, self.doc_text)

    def test_institution_and_client_policy_present(self):
        self.assertIn("institutions may choose manual-only, monthly, or quarterly review", self.doc_lower)
        self.assertIn("institution/client policy", self.doc_lower)
        self.assertIn("operator/institution review items", self.doc_lower)
        self.assertIn("no hidden external calls", self.doc_lower)

    def test_on_prem_and_air_gapped_restrictions_present(self):
        self.assertIn("on-prem", self.doc_lower)
        self.assertIn("air-gapped", self.doc_lower)
        self.assertIn("internal advisors", self.doc_lower)

    def test_future_cadence_prerequisites_present(self):
        self.assertIn("cadence is not implemented here", self.doc_lower)
        for phrase in [
            "registry schema exists",
            "queue schema exists",
            "operator approval policy exists",
            "redaction policy exists",
            "scheduling design is approved",
        ]:
            self.assertIn(phrase, self.doc_lower)

    def test_future_phase_names_present(self):
        for phase in [
            "APPROVE_ADVISOR_REVIEW_QUEUE_SCHEMA_ONLY",
            "APPROVE_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_ONLY",
            "APPROVE_OPERATOR_APPROVED_ADVISOR_CALL_FLOW_DESIGN_ONLY",
            "APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY",
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
