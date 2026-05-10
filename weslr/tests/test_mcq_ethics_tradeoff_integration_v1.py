from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.mcq_answer_formatting import build_official_mcq_response  # noqa: E402


class McqEthicsTradeoffIntegrationV1Tests(unittest.TestCase):
    def test_business_ethics_prompt_with_transparency_disclosure_accountability_selects_that_choice(self):
        prompt = "\n".join([
            "Multiple-choice question (business_ethics).",
            "Which option reflects stronger business ethics?",
            "required_skill: ethics_tradeoff_reasoning",
            "Choices:",
            "A. Improve transparency, make disclosure to affected stakeholders, and strengthen accountability and oversight.",
            "B. Keep the process vague and avoid external review.",
            "Select the best answer label and explain briefly.",
        ])
        result = build_official_mcq_response(prompt)
        self.assertEqual(result.get("selected_label"), "A")
        self.assertEqual(result.get("scoring_method"), "ethics_tradeoff_scorer_v1")

    def test_business_ethics_prompt_penalizes_conceal_deceive_profit_only_choice(self):
        prompt = "\n".join([
            "Multiple-choice question (business_ethics).",
            "Which option is ethically stronger?",
            "Choices:",
            "A. Conceal information, mislead customers, and maximize profit regardless of privacy concerns.",
            "B. Respect privacy, disclose relevant risks, and preserve long-term trust.",
            "Select the best answer label and explain briefly.",
        ])
        result = build_official_mcq_response(prompt)
        self.assertEqual(result.get("selected_label"), "B")

    def test_conflict_of_interest_disclosure_choice_beats_concealment_choice(self):
        prompt = "\n".join([
            "Multiple-choice question (business_ethics).",
            "Which option handles governance risk better?",
            "Choices:",
            "A. Disclose the conflict of interest, document accountability, and seek audit review.",
            "B. Ignore the conflict of interest and conceal the relationship if the outcome is profitable.",
            "Select the best answer label and explain briefly.",
        ])
        result = build_official_mcq_response(prompt)
        self.assertEqual(result.get("selected_label"), "A")

    def test_privacy_and_consent_choice_beats_exploitation_choice(self):
        prompt = "\n".join([
            "Multiple-choice question (business_ethics).",
            "Which option is more responsible?",
            "Choices:",
            "A. Obtain informed consent, protect privacy, and avoid exploiting affected users.",
            "B. Exploit user data, violate consent, and suppress information about the practice.",
            "Select the best answer label and explain briefly.",
        ])
        result = build_official_mcq_response(prompt)
        self.assertEqual(result.get("selected_label"), "A")

    def test_whistleblowing_and_duty_to_report_choice_beats_cover_up_choice(self):
        prompt = "\n".join([
            "Multiple-choice question (business_ethics).",
            "Which option reflects better ethical tradeoff reasoning?",
            "Choices:",
            "A. Support whistleblowing, follow the duty to report, and preserve public interest through governance review.",
            "B. Cover up the issue, retaliate against the reporter, and bypass oversight.",
            "Select the best answer label and explain briefly.",
        ])
        result = build_official_mcq_response(prompt)
        self.assertEqual(result.get("selected_label"), "A")

    def test_still_returns_no_selection_for_all_zero_signal_choices(self):
        prompt = "\n".join([
            "Multiple-choice question (business_ethics).",
            "Which option is best?",
            "Choices:",
            "A. Blue ladder.",
            "B. Green silence.",
            "Select the best answer label and explain briefly.",
        ])
        result = build_official_mcq_response(prompt)
        self.assertIsNone(result.get("selected_label"))
        self.assertEqual(result.get("scoring_method"), "ethics_tradeoff_scorer_v1")
        self.assertEqual(result.get("failure_mode"), "insufficient_ethics_rubric_signal")

    def test_does_not_use_item_id_or_answer_label(self):
        prompt = "\n".join([
            "Multiple-choice question (business_ethics).",
            "Which option is stronger?",
            "Choices:",
            "A. Respect duties and rights.",
            "B. Bypass governance.",
            "Select the best answer label and explain briefly.",
        ])
        result = build_official_mcq_response(prompt)
        payload = str(result)
        self.assertNotIn("item_id", payload.lower())
        self.assertNotIn("answer_label", payload.lower())

    def test_output_includes_scoring_method_when_ethics_scorer_is_used(self):
        prompt = "\n".join([
            "Multiple-choice question (business_ethics).",
            "Which option is stronger?",
            "Choices:",
            "A. Respect stakeholders, reduce harm, and preserve evidence boundaries with governance review.",
            "B. Hide uncertainty and skip review.",
            "Select the best answer label and explain briefly.",
        ])
        result = build_official_mcq_response(prompt)
        self.assertEqual(result.get("scoring_method"), "ethics_tradeoff_scorer_v1")
        self.assertIn("Answer:", result.get("response_text", ""))

    def test_official_score_claimed_remains_false(self):
        prompt = "\n".join([
            "Multiple-choice question (business_ethics).",
            "Which option is stronger?",
            "Choices:",
            "A. Respect stakeholders and governance review.",
            "B. Ignore stakeholders and bypass approval.",
            "Select the best answer label and explain briefly.",
        ])
        result = build_official_mcq_response(prompt)
        self.assertFalse(result.get("official_score_claimed"))

    def test_non_ethics_mcq_still_does_not_use_ethics_scorer(self):
        prompt = "\n".join([
            "Multiple-choice question (science).",
            "What best describes entropy?",
            "Choices:",
            "A. Spread out energy or arrangements are in a system.",
            "B. Order always increases.",
            "Select the best answer label and explain briefly.",
        ])
        result = build_official_mcq_response(prompt)
        self.assertEqual(result.get("path"), "official_mcq_answer_formatting")
        self.assertNotEqual(result.get("scoring_method"), "ethics_tradeoff_scorer_v1")


if __name__ == "__main__":
    unittest.main()
