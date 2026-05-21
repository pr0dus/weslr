from __future__ import annotations

import inspect
from pathlib import Path

import pytest

import weslr.answer_composition_authority_report_run as report_run
from weslr.answer_composition_authority_report_run import (
    NEXT_LANE_V1,
    REPORT_RUN_AGGREGATE_LABELS_V1,
    REPORT_RUN_ALLOWED_INPUTS_V1,
    REPORT_RUN_FORBIDDEN_INPUTS_V1,
    REPORT_RUN_SCHEMA_VERSION_V1,
    REPORT_RUN_TYPE_V1,
    RESULT_ARTIFACT_PATH_V1,
    build_answer_composition_authority_report_run_v1,
    render_answer_composition_authority_report_run_markdown_v1,
    validate_answer_composition_authority_report_run_v1,
    write_answer_composition_authority_report_run_result_v1,
)


def test_module_imports_without_side_effects():
    assert report_run.REPORT_RUN_TYPE_V1 == "answer_composition_authority_report_run_v1"


@pytest.mark.parametrize("name", [
    "build_answer_composition_authority_report_run_v1",
    "validate_answer_composition_authority_report_run_v1",
    "render_answer_composition_authority_report_run_markdown_v1",
    "write_answer_composition_authority_report_run_result_v1",
])
def test_public_api_exists(name):
    assert callable(getattr(report_run, name))


def test_constants_define_safe_scope():
    assert REPORT_RUN_TYPE_V1 == "answer_composition_authority_report_run_v1"
    assert REPORT_RUN_SCHEMA_VERSION_V1 == "answer_composition_authority_report_run_schema_v1"
    assert RESULT_ARTIFACT_PATH_V1 == "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_RESULT_V1.md"
    assert NEXT_LANE_V1 == "REVIEW_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_RESULT_V1"
    assert "answer_composition_authority_report_v1" in REPORT_RUN_ALLOWED_INPUTS_V1
    assert "raw_prompt" in REPORT_RUN_FORBIDDEN_INPUTS_V1
    assert "final_answer_prose" in REPORT_RUN_FORBIDDEN_INPUTS_V1
    assert "metadata_only_report_run" in REPORT_RUN_AGGREGATE_LABELS_V1


def test_build_report_run_is_valid_metadata_only_internal_only():
    run = build_answer_composition_authority_report_run_v1()
    validation = validate_answer_composition_authority_report_run_v1(run)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert run["metadata_only"] is True
    assert run["internal_only"] is True
    assert run["deterministic"] is True
    assert run["import_safe"] is True
    assert run["source_report_valid"] is True
    assert run["source_report_blocked"] is False


@pytest.mark.parametrize("flag", [
    "answer_composition_authorized",
    "final_answer_generated",
    "answer_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "prompt_execution_allowed",
    "live_dialogue_allowed",
    "raw_content_allowed",
    "official_claim_allowed",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "provider_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judge_authority_granted",
    "scoring_authorized",
])
def test_authority_and_side_effect_flags_are_false(flag):
    run = build_answer_composition_authority_report_run_v1()
    assert run[flag] is False


def test_safety_confirmation_contains_required_boundaries():
    safety = build_answer_composition_authority_report_run_v1()["safety_confirmation"]
    assert safety["no_answer_composition"] is True
    assert safety["no_final_answer_generation"] is True
    assert safety["no_runtime_wiring"] is True
    assert safety["no_prompt_execution_live_dialogue"] is True
    assert safety["no_provider_calls"] is True
    assert safety["no_dot_weslr_writes"] is True
    assert safety["no_feature_flags"] is True
    assert safety["no_judges_scoring"] is True
    assert safety["no_official_claims"] is True
    assert safety["no_answer_authority_granted"] is True
    assert safety["no_composition_authority_granted"] is True
    assert safety["chat_responder_untouched"] is True
    assert safety["occ_openclaw_is_not_deployed_weslr"] is True


@pytest.mark.parametrize("risk", [
    "metadata-overread",
    "report-as-judge/score",
    "renderer wording drift",
    "artifact/report-as-authority",
    "OCC/WESLR identity confusion",
    "validation-pass-as-authority",
    "final-answer-prose leak",
])
def test_visible_risks_are_carried_forward(risk):
    run = build_answer_composition_authority_report_run_v1()
    assert risk in run["visible_risks"]


def test_validation_pass_policy_is_not_authority():
    run = build_answer_composition_authority_report_run_v1()
    assert "not answer authority" in run["validation_pass_policy"]
    assert "not composition authority" in run["validation_pass_policy"]


def test_markdown_is_safe_and_contains_result_labels():
    markdown = render_answer_composition_authority_report_run_markdown_v1(
        build_answer_composition_authority_report_run_v1()
    )
    assert "WESLR Answer Composition Authority Report Run Result V1" in markdown
    assert "metadata_only" in markdown
    assert "validation pass is metadata quality evidence only" in markdown
    assert "OCC/OpenClaw remains separate from deployed WESLR" in markdown
    forbidden = [
        "raw prompt:",
        "raw response:",
        "private content:",
        "hidden prompt:",
        "answer key:",
        "provider output:",
        "runtime output:",
        "final answer:",
        "official score:",
        "judge decision:",
    ]
    lower = markdown.lower()
    for marker in forbidden:
        assert marker not in lower


def test_invalid_markdown_blocks_without_leaking_content():
    bad = build_answer_composition_authority_report_run_v1()
    bad["answer_authority_granted"] = True
    bad["raw_prompt"] = "raw prompt: secret"
    markdown = render_answer_composition_authority_report_run_markdown_v1(bad)
    assert "Blocked" in markdown
    assert "secret" not in markdown
    assert "unsafe content was not rendered" in markdown


def test_builder_is_deterministic_and_does_not_mutate_inputs():
    validation_results = {"release_gate": "PASS"}
    one = build_answer_composition_authority_report_run_v1(validation_results=validation_results)
    two = build_answer_composition_authority_report_run_v1(validation_results=validation_results)
    assert one == two
    assert validation_results == {"release_gate": "PASS"}


def test_write_result_only_approved_path(tmp_path):
    with pytest.raises(ValueError):
        write_answer_composition_authority_report_run_result_v1(tmp_path / "bad.md")


def test_write_result_artifact_writes_safe_markdown(monkeypatch, tmp_path):
    target = tmp_path / "docs" / "WESLR_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_RESULT_V1.md"
    target.parent.mkdir()

    class FakePath:
        def __init__(self, value):
            self.value = value
            self.real = target

        def as_posix(self):
            return RESULT_ARTIFACT_PATH_V1

        def write_text(self, text):
            return self.real.write_text(text)

    monkeypatch.setattr(report_run, "Path", FakePath)
    run = write_answer_composition_authority_report_run_result_v1(RESULT_ARTIFACT_PATH_V1)
    text = target.read_text()
    assert run["report_run_type"] == REPORT_RUN_TYPE_V1
    assert "answer_composition_authority_report_run_result_v1" in text
    assert "no_answer_composition" in text
    assert "no_composition_authority_granted" in text


def test_source_has_no_runtime_provider_or_subprocess_imports():
    source = inspect.getsource(report_run)
    forbidden = [
        "requests",
        "urllib",
        "subprocess",
        "socket",
        "ChatResponder",
        "respond_chat",
        "generate_chat",
        "provider_call(",
        "model_call(",
        "feature_flag_enabled = True",
        "judge_authority_granted = True",
        "scoring_authorized = True",
    ]
    for token in forbidden:
        assert token not in source


def test_result_artifact_path_not_runtime_or_weslr_state():
    path = Path(RESULT_ARTIFACT_PATH_V1)
    assert path.parts[0] == "docs"
    assert ".weslr" not in path.parts
    assert "chat_responder.py" not in str(path)
