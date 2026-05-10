from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.business_ethics_concepts import (  # noqa: E402
    explain_business_ethics_concepts_for_humans,
    get_business_ethics_concept_families,
    get_business_ethics_concept_family,
    list_business_ethics_concept_ids,
)


REQUIRED_IDS = {
    "corporate_social_responsibility",
    "stakeholder_theory",
    "shareholder_vs_stakeholder_balance",
    "business_and_society",
    "externalities",
    "ethical_governance",
    "compliance_and_audit",
    "board_independence",
    "conflict_of_interest",
    "transparency_and_disclosure",
    "privacy_and_consent",
    "consumer_protection",
    "employee_protection",
    "whistleblowing_and_reporting",
    "activism_and_civil_society",
    "consumer_activism",
    "sustainability_and_environmental_management",
    "fiduciary_duty",
    "corruption_and_bribery",
    "deception_and_misrepresentation",
}


class BusinessEthicsConceptsV1Tests(unittest.TestCase):
    def test_all_required_concept_families_exist(self):
        self.assertTrue(REQUIRED_IDS.issubset(set(list_business_ethics_concept_ids())))

    def test_each_concept_has_required_fields(self):
        concepts = get_business_ethics_concept_families()
        for concept_id in REQUIRED_IDS:
            concept = concepts[concept_id]
            for key in [
                "concept_id",
                "description",
                "positive_markers",
                "negative_markers",
                "related_rubric_dimensions",
                "scorer_use_allowed",
                "runtime_behavior_changed",
                "anti_gaming_note",
            ]:
                self.assertIn(key, concept)
            self.assertEqual(concept["concept_id"], concept_id)
            self.assertTrue(concept["description"])
            self.assertIsInstance(concept["positive_markers"], list)
            self.assertIsInstance(concept["negative_markers"], list)
            self.assertIsInstance(concept["related_rubric_dimensions"], list)

    def test_each_concept_has_scorer_use_allowed_false(self):
        for concept in get_business_ethics_concept_families().values():
            self.assertFalse(concept["scorer_use_allowed"])

    def test_each_concept_has_runtime_behavior_changed_false(self):
        for concept in get_business_ethics_concept_families().values():
            self.assertFalse(concept["runtime_behavior_changed"])

    def test_concepts_reference_required_rubric_dimensions(self):
        concepts = get_business_ethics_concept_families()
        corpus = "\n".join(",".join(concept["related_rubric_dimensions"]) for concept in concepts.values())
        for needle in [
            "stakeholders",
            "harms",
            "duties",
            "rights",
            "governance",
            "evidence_boundaries",
            "authority",
            "uncertainty",
        ]:
            self.assertIn(needle, corpus)

    def test_anti_gaming_text_forbids_required_patterns(self):
        corpus = "\n".join(concept["anti_gaming_note"] for concept in get_business_ethics_concept_families().values()).lower()
        for needle in [
            "benchmark item ids",
            "answer labels",
            "raw benchmark questions",
            "official-score claims",
            "item-specific phrase rules",
        ]:
            self.assertIn(needle, corpus)

    def test_human_explanation_mentions_teachable_human_understandable_general_reasoning(self):
        text = explain_business_ethics_concepts_for_humans().lower()
        for needle in ["teachable", "human-understandable", "general business-ethics reasoning"]:
            self.assertIn(needle, text)

    def test_no_forbidden_phrases(self):
        corpus = "\n".join([
            str(get_business_ethics_concept_families()),
            explain_business_ethics_concepts_for_humans(),
        ]).lower()
        for phrase in [
            "official mmlu score",
            "weslr has passed mmlu",
            "memorize answer keys",
            "choose option",
            "business_ethics_dev5 answer",
        ]:
            self.assertNotIn(phrase, corpus)

    def test_single_concept_lookup_returns_copy(self):
        concept = get_business_ethics_concept_family("privacy_and_consent")
        self.assertIsNotNone(concept)
        self.assertEqual(concept["concept_id"], "privacy_and_consent")
        concept["description"] = "changed"
        fresh = get_business_ethics_concept_family("privacy_and_consent")
        self.assertNotEqual(fresh["description"], "changed")


if __name__ == "__main__":
    unittest.main()
