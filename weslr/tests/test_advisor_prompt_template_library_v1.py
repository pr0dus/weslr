from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.advisor_prompt_templates import (  # noqa: E402
    REQUIRED_ADVISOR_TEMPLATE_TASK_TYPES,
    REQUIRED_OUTPUT_SECTIONS,
    AdvisorPromptTemplate,
    RenderedAdvisorPrompt,
    advisor_prompt_template_from_dict,
    advisor_prompt_template_to_dict,
    get_advisor_prompt_template,
    load_advisor_prompt_templates_v1,
    render_advisor_prompt,
    rendered_advisor_prompt_from_dict,
    rendered_advisor_prompt_to_dict,
    summarize_advisor_prompt_template_library,
    validate_advisor_prompt_template,
    validate_rendered_advisor_prompt,
)
from weslr.llm_advisor_mode import AdvisorSafetyFlags  # noqa: E402

ALLOWED_CHANGED = {
    "weslr/advisor_prompt_templates.py",
    "weslr/tests/test_advisor_prompt_template_library_v1.py",
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


class AdvisorPromptTemplateLibraryV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_module_imports(self):
        self.assertTrue(AdvisorPromptTemplate)
        self.assertTrue(RenderedAdvisorPrompt)

    def test_template_dataclass_instantiates(self):
        template = AdvisorPromptTemplate(template_id="t", task_type="architecture_review")
        self.assertEqual("t", template.template_id)

    def test_rendered_prompt_dataclass_instantiates(self):
        prompt = RenderedAdvisorPrompt(template_id="t", task_type="architecture_review")
        self.assertEqual("structural_summary_only", prompt.redaction_level)

    def test_library_loads(self):
        self.assertEqual(10, len(load_advisor_prompt_templates_v1()))

    def test_all_required_task_types_exist(self):
        task_types = {template.task_type for template in load_advisor_prompt_templates_v1()}
        self.assertEqual(set(REQUIRED_ADVISOR_TEMPLATE_TASK_TYPES), task_types)

    def assert_template_validates(self, task_type: str):
        self.assertEqual([], validate_advisor_prompt_template(get_advisor_prompt_template(task_type)))

    def test_architecture_review_template_validates(self):
        self.assert_template_validates("architecture_review")

    def test_failure_diagnosis_template_validates(self):
        self.assert_template_validates("failure_diagnosis")

    def test_style_review_template_validates(self):
        self.assert_template_validates("style_review")

    def test_test_suggestion_template_validates(self):
        self.assert_template_validates("test_suggestion")

    def test_synthetic_example_suggestion_template_validates(self):
        self.assert_template_validates("synthetic_example_suggestion")

    def test_reasoning_pattern_review_template_validates(self):
        self.assert_template_validates("reasoning_pattern_review")

    def test_gap_taxonomy_review_template_validates(self):
        self.assert_template_validates("gap_taxonomy_review")

    def test_wording_risk_review_template_validates(self):
        self.assert_template_validates("wording_risk_review")

    def test_alternative_design_proposal_template_validates(self):
        self.assert_template_validates("alternative_design_proposal")

    def test_provider_capability_review_template_validates(self):
        self.assert_template_validates("provider_capability_review")

    def test_invalid_task_type_fails(self):
        template = get_advisor_prompt_template("not_a_task")
        self.assertIn("invalid task type", validate_advisor_prompt_template(template))

    def test_provider_neutral_false_fails(self):
        template = replace(get_advisor_prompt_template("architecture_review"), provider_neutral=False)
        self.assertIn("provider_neutral false", validate_advisor_prompt_template(template))

    def test_non_authoritative_false_fails(self):
        template = replace(get_advisor_prompt_template("architecture_review"), non_authoritative=False)
        self.assertIn("non_authoritative false", validate_advisor_prompt_template(template))

    def test_requires_validation_false_fails(self):
        template = replace(get_advisor_prompt_template("architecture_review"), requires_validation=False)
        self.assertIn("requires_validation false", validate_advisor_prompt_template(template))

    def test_requires_operator_review_false_fails(self):
        template = replace(get_advisor_prompt_template("architecture_review"), requires_operator_review=False)
        self.assertIn("requires_operator_review false", validate_advisor_prompt_template(template))

    def test_not_runtime_truth_false_fails(self):
        template = replace(get_advisor_prompt_template("architecture_review"), not_runtime_truth=False)
        self.assertIn("not_runtime_truth false", validate_advisor_prompt_template(template))

    def test_missing_required_output_sections_fails(self):
        template = replace(get_advisor_prompt_template("architecture_review"), required_output_sections=["Summary"])
        self.assertIn("missing required output sections", validate_advisor_prompt_template(template))

    def test_unsafe_answer_selection_prompt_fails(self):
        template = replace(get_advisor_prompt_template("architecture_review"), purpose="select the answer")
        self.assertIn("template asks for answer selection", validate_advisor_prompt_template(template))

    def test_unsafe_answer_key_prompt_fails(self):
        template = replace(get_advisor_prompt_template("architecture_review"), purpose="use the answer key")
        self.assertIn("template asks for answer keys", validate_advisor_prompt_template(template))

    def test_unsafe_official_score_prompt_fails(self):
        template = replace(get_advisor_prompt_template("architecture_review"), purpose="claim official score")
        self.assertIn("template asks for official score", validate_advisor_prompt_template(template))

    def test_unsafe_secret_api_key_prompt_fails(self):
        template = replace(get_advisor_prompt_template("architecture_review"), purpose="request secrets and provide API key token")
        self.assertIn("template asks for secrets/API keys/tokens", validate_advisor_prompt_template(template))

    def test_unsafe_runtime_mutation_prompt_fails(self):
        template = replace(get_advisor_prompt_template("architecture_review"), purpose="change runtime now")
        self.assertIn("template requests runtime mutation", validate_advisor_prompt_template(template))

    def test_render_prompt_works(self):
        prompt = render_advisor_prompt("architecture_review", "Redacted structural summary only.", "sha256:test")
        self.assertIn("Architecture Review", prompt.prompt_text)

    def test_rendered_prompt_includes_redaction_boundary(self):
        prompt = render_advisor_prompt("failure_diagnosis", "Redacted structural summary only.", "sha256:test")
        self.assertIn("Input redaction level: structural_summary_only", prompt.prompt_text)

    def test_rendered_prompt_includes_non_authoritative_boundary(self):
        prompt = render_advisor_prompt("style_review", "Redacted structural summary only.", "sha256:test")
        self.assertIn("non-authoritative proposal input", prompt.prompt_text)
        self.assertIn("not runtime truth", prompt.prompt_text)

    def test_rendered_prompt_includes_required_output_sections(self):
        prompt = render_advisor_prompt("test_suggestion", "Redacted structural summary only.", "sha256:test")
        for section in REQUIRED_OUTPUT_SECTIONS:
            self.assertIn(section, prompt.prompt_text)

    def test_rendered_prompt_validates(self):
        prompt = render_advisor_prompt("gap_taxonomy_review", "Redacted structural summary only.", "sha256:test")
        self.assertEqual([], validate_rendered_advisor_prompt(prompt))

    def test_rendered_prompt_with_unsafe_safety_flags_fails(self):
        prompt = render_advisor_prompt("architecture_review", "Redacted structural summary only.", "sha256:test")
        prompt.safety_flags = AdvisorSafetyFlags(answer_selection_used=True)
        self.assertIn("unsafe safety flags", validate_rendered_advisor_prompt(prompt))

    def test_rendered_prompt_is_deterministic_for_same_input(self):
        first = render_advisor_prompt("architecture_review", "Redacted structural summary only.", "sha256:test")
        second = render_advisor_prompt("architecture_review", "Redacted structural summary only.", "sha256:test")
        self.assertEqual(first, second)

    def test_template_dict_roundtrip(self):
        template = get_advisor_prompt_template("provider_capability_review")
        self.assertEqual(template, advisor_prompt_template_from_dict(advisor_prompt_template_to_dict(template)))

    def test_rendered_prompt_dict_roundtrip(self):
        prompt = render_advisor_prompt("provider_capability_review", "Redacted structural summary only.", "sha256:test")
        self.assertEqual(prompt, rendered_advisor_prompt_from_dict(rendered_advisor_prompt_to_dict(prompt)))

    def test_summary_is_redacted_count_only(self):
        summary = summarize_advisor_prompt_template_library()
        self.assertEqual(10, summary["template_count"])
        self.assertEqual(0, summary["validation_error_count"])
        self.assertNotIn("prompt_text", summary)

    def test_summary_does_not_contain_sensitive_terms(self):
        text = str(summarize_advisor_prompt_template_library()).lower()
        for forbidden in ["secret", "api key", "token", "raw benchmark", "answer key", "private data", "private user data"]:
            self.assertNotIn(forbidden, text)

    def test_llm_advisor_record_schema_tests_still_pass(self):
        proc = subprocess.run(
            ["python3", "weslr/tests/test_llm_advisor_record_schema_v1.py"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("OK", proc.stderr + proc.stdout)

    def test_design_test_still_passes(self):
        proc = subprocess.run(
            ["python3", "weslr/tests/test_llm_advisor_mode_design_v1.py"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("OK", proc.stderr + proc.stdout)

    def test_release_gate_and_check_pass(self):
        gate = subprocess.run(["python3", "weslr/tests/release_gate_v1.py"], cwd=str(ROOT), text=True, capture_output=True, check=True)
        self.assertIn("WESLR_RELEASE_GATE_V1_OK", gate.stdout)
        check = subprocess.run(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT), text=True, capture_output=True, check=True)
        self.assertIn("WESLR_RELEASE_CHECK_OK", check.stdout)

    def test_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
