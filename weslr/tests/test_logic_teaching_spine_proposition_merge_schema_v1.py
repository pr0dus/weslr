#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    PropositionMergeCandidate,
    create_empty_proposition_merge_candidate,
    proposition_merge_candidate_from_dict,
    proposition_merge_candidate_to_dict,
    summarize_proposition_merge_candidate,
    validate_proposition_merge_candidate,
)


FORBIDDEN_CHANGED = {
    "weslr/choice_stem_binding.py",
    "weslr/logical_form_normalizer.py",
    "weslr/formal_logic_parser.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}
ALLOWED_CHANGED = {
    "weslr/logic_teaching_spine.py",
    "weslr/tests/test_logic_teaching_spine_proposition_helpers_v1.py",
    "weslr/tests/test_logic_teaching_spine_proposition_merge_schema_v1.py",
}


class PropositionMergeSchemaV1Tests(unittest.TestCase):
    def test_instantiate_empty_merge_candidate(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1")
        self.assertIsInstance(candidate, PropositionMergeCandidate)
        self.assertEqual("merge:1", candidate.merge_id)

    def test_safe_anti_gaming_defaults(self):
        candidate = create_empty_proposition_merge_candidate()
        self.assertFalse(candidate.anti_gaming.uses_answer_key)
        self.assertFalse(candidate.anti_gaming.uses_item_id_as_authority)
        self.assertFalse(candidate.anti_gaming.uses_answer_position_bias)
        self.assertFalse(candidate.anti_gaming.claims_official_score)
        self.assertFalse(candidate.anti_gaming.benchmark_specific_tuning)
        self.assertTrue(candidate.anti_gaming.no_answer_selection)

    def test_safe_legibility_defaults(self):
        candidate = create_empty_proposition_merge_candidate()
        self.assertTrue(candidate.legibility.human_translation_available)
        self.assertTrue(candidate.legibility.redacted_summary_only)
        self.assertFalse(candidate.legibility.stores_raw_benchmark_text)
        self.assertFalse(candidate.legibility.hides_unsupported_assumptions)
        self.assertFalse(candidate.legibility.private_symbolic_authority)

    def test_to_from_dict_roundtrip(self):
        candidate = create_empty_proposition_merge_candidate(
            merge_id="merge:1",
            structural_signature="role=premise|s=a|r=is|o=b",
            source_proposition_ids=["prop:1", "prop:2"],
            source_origins=["predicate_derived", "binding_derived"],
            proposition_role="premise",
        )
        candidate.subject_canonical_hint = "a"
        candidate.relation_canonical_hint = "is"
        candidate.object_canonical_hint = "b"
        candidate.duplicate_count = 1
        candidate.human_explanation = "Redacted structural duplicate only."
        data = proposition_merge_candidate_to_dict(candidate)
        restored = proposition_merge_candidate_from_dict(data)
        self.assertEqual(data, proposition_merge_candidate_to_dict(restored))

    def test_redacted_summary(self):
        candidate = create_empty_proposition_merge_candidate(
            merge_id="merge:1",
            structural_signature="secret structural text",
            source_proposition_ids=["prop:1", "prop:2"],
            source_origins=["predicate_derived"],
        )
        candidate.human_explanation = "secret explanation"
        summary = summarize_proposition_merge_candidate(candidate)
        self.assertTrue(summary["has_structural_signature"])
        self.assertEqual(2, summary["source_proposition_count"])
        self.assertNotIn("structural_signature", summary)
        self.assertNotIn("human_explanation", summary)

    def test_validation_flags_missing_id(self):
        candidate = create_empty_proposition_merge_candidate(structural_signature="sig")
        self.assertIn("missing merge id", validate_proposition_merge_candidate(candidate))

    def test_validation_flags_missing_signature(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1")
        self.assertIn("missing structural signature", validate_proposition_merge_candidate(candidate))

    def test_validation_flags_invalid_source_origin(self):
        candidate = create_empty_proposition_merge_candidate(
            merge_id="merge:1",
            structural_signature="sig",
            source_origins=["answer_key_derived"],
        )
        self.assertIn("invalid source origin", validate_proposition_merge_candidate(candidate))

    def test_validation_flags_answer_key_use(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1", structural_signature="sig")
        candidate.anti_gaming.uses_answer_key = True
        self.assertIn("answer-key use is forbidden", validate_proposition_merge_candidate(candidate))

    def test_validation_flags_item_id_authority(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1", structural_signature="sig")
        candidate.anti_gaming.uses_item_id_as_authority = True
        self.assertIn("item-id authority is forbidden", validate_proposition_merge_candidate(candidate))

    def test_validation_flags_official_score_claim(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1", structural_signature="sig")
        candidate.anti_gaming.claims_official_score = True
        self.assertIn("official-score claim is forbidden", validate_proposition_merge_candidate(candidate))

    def test_validation_flags_answer_selection(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1", structural_signature="sig")
        candidate.anti_gaming.no_answer_selection = False
        self.assertIn("answer selection must remain disabled", validate_proposition_merge_candidate(candidate))

    def test_validation_flags_raw_benchmark_storage(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1", structural_signature="sig")
        candidate.legibility.stores_raw_benchmark_text = True
        self.assertIn("raw benchmark storage by default is forbidden", validate_proposition_merge_candidate(candidate))

    def test_validation_flags_private_symbolic_authority(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1", structural_signature="sig")
        candidate.legibility.private_symbolic_authority = True
        self.assertIn("private symbolic authority is forbidden", validate_proposition_merge_candidate(candidate))

    def test_validation_flags_hidden_unsupported_assumptions(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1", structural_signature="sig")
        candidate.legibility.hides_unsupported_assumptions = True
        self.assertIn("unsupported assumptions must remain visible", validate_proposition_merge_candidate(candidate))

    def test_validation_flags_invalid_confidence_summary(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1", structural_signature="sig")
        candidate.confidence_summary = "certain"
        self.assertIn("invalid confidence summary", validate_proposition_merge_candidate(candidate))

    def test_validation_flags_high_confidence_without_sources_or_explanation(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1", structural_signature="sig")
        candidate.confidence_summary = "high"
        findings = validate_proposition_merge_candidate(candidate)
        self.assertIn("empty source proposition ids for high-confidence merge candidate", findings)
        self.assertIn("missing human explanation for high-confidence merge candidate", findings)

    def test_can_store_predicate_and_binding_origins(self):
        candidate = create_empty_proposition_merge_candidate(
            merge_id="merge:1",
            structural_signature="sig",
            source_origins=["predicate_derived", "binding_derived"],
        )
        self.assertEqual(["predicate_derived", "binding_derived"], candidate.source_origins)
        self.assertNotIn("invalid source origin", validate_proposition_merge_candidate(candidate))

    def test_can_store_duplicate_count(self):
        candidate = create_empty_proposition_merge_candidate(merge_id="merge:1", structural_signature="sig")
        candidate.duplicate_count = 3
        self.assertEqual(3, summarize_proposition_merge_candidate(candidate)["duplicate_count"])

    def test_no_forbidden_files_changed(self):
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertTrue(changed.issubset(ALLOWED_CHANGED), changed)


if __name__ == "__main__":
    unittest.main()
