import builtins
import importlib
import json
import socket
from pathlib import Path

import pytest

MODULE_NAME = "weslr.controlled_unknown_engine_metadata_shadow_runner"


def _module():
    return importlib.import_module(MODULE_NAME)


def _safe_fixture(kind="synthetic_unknown_engine_fixture", **kwargs):
    m = _module()
    defaults = {
        "fixture_kind": kind,
        "run_id": f"run_{kind}",
        "metadata": {"case_id": "synthetic_case", "note": "metadata only"},
    }
    defaults.update(kwargs)
    return m.build_controlled_unknown_engine_shadow_fixture_v1(**defaults)


def _safe_report(kind="synthetic_unknown_engine_fixture", **kwargs):
    m = _module()
    return m.run_controlled_unknown_engine_metadata_shadow_v1(_safe_fixture(kind, **kwargs))


def test_import_safety(monkeypatch):
    opened = []

    def fail_open(*args, **kwargs):
        opened.append(args)
        raise AssertionError("open must not be called during import")

    monkeypatch.setattr(builtins, "open", fail_open)
    imported = importlib.reload(_module())
    assert imported.SCHEMA_VERSION == "weslr.controlled_unknown_engine_metadata_shadow_runner.v1"
    assert opened == []


@pytest.mark.parametrize(
    "kind",
    [
        "synthetic_unknown_engine_fixture",
        "synthetic_cognitive_gym_metadata",
        "synthetic_tier_0_2_math_readiness_card",
        "synthetic_candidate_invariant_metadata",
        "synthetic_failed_path_metadata",
    ],
)
def test_valid_synthetic_fixture_kinds(kind):
    m = _module()
    fixture = _safe_fixture(kind)
    validation = m.validate_controlled_unknown_engine_shadow_fixture_v1(fixture)
    report = m.run_controlled_unknown_engine_metadata_shadow_v1(fixture)
    report_validation = m.validate_controlled_unknown_engine_shadow_report_v1(report)
    assert validation["valid"] is True
    assert report["validation_status"] == "valid_metadata_shadow_report"
    assert report_validation["valid"] is True


def test_explicitly_approved_safe_internal_metadata_fixture():
    m = _module()
    fixture = _safe_fixture(
        "explicitly_approved_safe_internal_metadata",
        synthetic=False,
        explicitly_approved=True,
        source_scoped=True,
        metadata={"safe_artifact_id": "synthetic-approved-1"},
    )
    assert m.validate_controlled_unknown_engine_shadow_fixture_v1(fixture)["valid"] is True
    assert m.run_controlled_unknown_engine_metadata_shadow_v1(fixture)["validation_status"] == "valid_metadata_shadow_report"


def test_explicit_internal_metadata_requires_approval_and_source_scope():
    m = _module()
    fixture = _safe_fixture(
        "explicitly_approved_safe_internal_metadata",
        synthetic=False,
        explicitly_approved=False,
        source_scoped=False,
    )
    validation = m.validate_controlled_unknown_engine_shadow_fixture_v1(fixture)
    assert validation["valid"] is False
    assert "explicit_internal_metadata_not_approved" in validation["errors"]
    assert "explicit_internal_metadata_not_source_scoped" in validation["errors"]


def test_unknown_fixture_kind_blocked():
    m = _module()
    fixture = _safe_fixture("unknown_fixture_kind")
    report = m.run_controlled_unknown_engine_metadata_shadow_v1(fixture)
    assert report["validation_status"] == "blocked"
    assert "unknown_fixture_kind" in report["observed_gaps"]


@pytest.mark.parametrize(
    "marker",
    [
        "raw_private_material",
        "live_erdos_solving_prompt",
        "live_millennium_solving_prompt",
        "theorem_prover_task",
        "provider_output",
        "model_output",
        "search_output",
        "advisor_output",
        "hidden_prompt",
        "protected_material",
        "dot_weslr_state",
        "runtime_chat_transcript",
        "unscoped_memory",
        "unscoped_context",
        "unscoped_evidence",
        "unscoped_artifact",
        "final_answer_text",
        "proof_or_solution_claim",
    ],
)
def test_forbidden_fixture_markers_block(marker):
    m = _module()
    fixture = _safe_fixture(markers=[marker])
    validation = m.validate_controlled_unknown_engine_shadow_fixture_v1(fixture)
    report = m.run_controlled_unknown_engine_metadata_shadow_v1(fixture)
    assert validation["valid"] is False
    assert marker in validation["blocked_markers"]
    assert report["validation_status"] == "blocked"


@pytest.mark.parametrize(
    "text",
    [
        "this contains raw_private_material",
        "live Erdős solving prompt",
        "live millennium solving prompt",
        "theorem prover task",
        "provider output",
        "model output",
        "search output",
        "advisor output",
        "hidden prompt",
        "protected material",
        ".weslr state",
        "runtime chat transcript",
        "unscoped memory",
        "unscoped context",
        "unscoped evidence",
        "unscoped artifact",
        "final answer: unsafe",
        "I have proved the solution claim",
    ],
)
def test_unsafe_text_content_blocks(text):
    m = _module()
    fixture = _safe_fixture(metadata={"unsafe_text": text})
    validation = m.validate_controlled_unknown_engine_shadow_fixture_v1(fixture)
    assert validation["valid"] is False
    assert "unsafe_text_markers_present" in validation["errors"]


def test_denied_authority_missing_blocked_in_report_validation():
    m = _module()
    report = _safe_report()
    del report["denied_authority"]["permits_provider_calls"]
    validation = m.validate_controlled_unknown_engine_shadow_report_v1(report)
    assert validation["valid"] is False
    assert "authority_field_missing:permits_provider_calls" in validation["errors"]


def test_denied_authority_true_blocked_in_report_validation():
    m = _module()
    report = _safe_report()
    report["denied_authority"]["permits_provider_calls"] = True
    validation = m.validate_controlled_unknown_engine_shadow_report_v1(report)
    assert validation["valid"] is False
    assert "authority_field_not_false:permits_provider_calls" in validation["errors"]


def test_fixture_denied_authority_missing_or_true_blocks():
    m = _module()
    missing = _safe_fixture()
    missing["denied_authority"] = {field: False for field in m.DENIED_AUTHORITY_FIELDS[:-1]}
    true_value = _safe_fixture()
    true_value["denied_authority"] = {field: False for field in m.DENIED_AUTHORITY_FIELDS}
    true_value["denied_authority"]["permits_real_problem_solving"] = True
    assert m.validate_controlled_unknown_engine_shadow_fixture_v1(missing)["valid"] is False
    assert m.validate_controlled_unknown_engine_shadow_fixture_v1(true_value)["valid"] is False


def test_expert_style_output_labeled_internal_simulation_only():
    report = _safe_report(expert_style_output=True)
    expert = report["expert_lane_handling"]
    assert expert["expert_style_output_present"] is True
    assert expert["label"] == "internal_expert_simulation"
    assert expert["is_external_validation"] is False
    assert expert["expert_output_analysis_or_adjudication_required"] is True
    assert expert["public_proof_prize_solution_claims_blocked"] is True


def test_expert_wrong_label_blocked():
    m = _module()
    fixture = _safe_fixture(expert_style_output=True, expert_label="external_expert_validation")
    validation = m.validate_controlled_unknown_engine_shadow_fixture_v1(fixture)
    assert validation["valid"] is False
    assert "expert_style_output_not_labeled_internal_simulation" in validation["errors"]


def test_external_validation_claim_blocked():
    m = _module()
    fixture = _safe_fixture(expert_style_output=True, treats_expert_as_external_validation=True)
    validation = m.validate_controlled_unknown_engine_shadow_fixture_v1(fixture)
    assert validation["valid"] is False
    assert "expert_style_output_treated_as_external_validation" in validation["errors"]


def test_metadata_only_report_shape():
    m = _module()
    report = _safe_report()
    assert tuple(report.keys()) == m.REPORT_FIELDS
    assert report["schema_version"] == m.SCHEMA_VERSION
    assert report["runner_mode"] == m.RUNNER_MODE
    assert report["engine_helper_paths_observed"] == (
        "weslr/unknown_engine.py",
        "weslr/unknown_engine_result_artifact.py",
    )
    assert report["result_artifact_shape"]["contains_proof_text"] is False
    assert report["result_artifact_shape"]["contains_final_answer_text"] is False
    assert report["result_artifact_shape"]["contains_user_facing_output"] is False


def test_json_safe_export():
    m = _module()
    report = _safe_report()
    exported = m.to_controlled_unknown_engine_shadow_report_json_safe_v1(report)
    json.dumps(exported, sort_keys=True)
    assert exported["report_validation"]["valid"] is True


def test_json_safe_export_blocks_non_json_safe_report():
    m = _module()
    report = _safe_report()
    report["bad"] = object()
    exported = m.to_controlled_unknown_engine_shadow_report_json_safe_v1(report)
    assert exported["validation_status"] == "invalid_metadata_shadow_report"
    assert exported["valid"] is False


def test_markdown_renderer_internal_only_metadata_only():
    m = _module()
    markdown = m.render_controlled_unknown_engine_shadow_report_markdown_v1(_safe_report())
    assert "Internal Controlled UNKNOWN ENGINE Metadata Shadow Report V1" in markdown
    assert "internal metadata only" in markdown
    assert "User-facing output: false" in markdown
    assert "Final-answer generation: false" in markdown
    assert "Proof or solution claim: false" in markdown
    assert "final answer:" not in markdown.lower()
    assert "i have proved" not in markdown.lower()


def test_no_runtime_chat_provider_search_model_advisor_imports_or_calls():
    m = _module()
    module_file = Path(m.__file__).read_text()
    forbidden_import_fragments = [
        "import requests",
        "import urllib",
        "import httpx",
        "import socket",
        "import subprocess",
        "import openai",
        "import browser",
        "chat_responder",
        "from weslr.unknown_engine import",
        "from weslr.unknown_engine_result_artifact import",
    ]
    for fragment in forbidden_import_fragments:
        assert fragment not in module_file


def test_no_filesystem_weslr_network_behavior(monkeypatch):
    m = _module()

    def fail_open(*args, **kwargs):
        raise AssertionError("filesystem open must not be called")

    def fail_socket(*args, **kwargs):
        raise AssertionError("network socket must not be called")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(socket, "socket", fail_socket)
    report = m.run_controlled_unknown_engine_metadata_shadow_v1(_safe_fixture())
    assert report["validation_status"] == "valid_metadata_shadow_report"


def test_report_validation_passes_for_safe_fixture():
    m = _module()
    report = _safe_report()
    assert m.validate_controlled_unknown_engine_shadow_report_v1(report)["valid"] is True


def test_report_validation_fails_closed_for_unsafe_fixture():
    m = _module()
    report = m.run_controlled_unknown_engine_metadata_shadow_v1(_safe_fixture(markers=["provider_output"]))
    assert report["validation_status"] == "blocked"
    validation = m.validate_controlled_unknown_engine_shadow_report_v1(report)
    assert validation["valid"] is True
    assert "forbidden_fixture_markers_present" in report["observed_gaps"]


def test_next_step_forbidden_execution_blocked():
    m = _module()
    report = _safe_report()
    report["next_safe_steps"] = ("wire runtime chat provider execution",)
    validation = m.validate_controlled_unknown_engine_shadow_report_v1(report)
    assert validation["valid"] is False
    assert "next_step_proposes_forbidden_execution" in validation["errors"]


def test_no_run_authority_missing_or_true_blocked():
    m = _module()
    report = _safe_report()
    del report["no_run_authority_flags"]["is_final_answer"]
    assert m.validate_controlled_unknown_engine_shadow_report_v1(report)["valid"] is False
    report = _safe_report()
    report["no_run_authority_flags"]["is_final_answer"] = True
    assert m.validate_controlled_unknown_engine_shadow_report_v1(report)["valid"] is False


def test_summary_counts_status_only_no_proof_or_final_answer_text():
    m = _module()
    summary = m.summarize_controlled_unknown_engine_shadow_report_v1(_safe_report())
    dumped = json.dumps(summary, sort_keys=True).lower()
    assert summary["valid"] is True
    assert summary["blocked_claim_count"] > 0
    assert "i have proved" not in dumped
    assert "final answer:" not in dumped
    assert "proof text" not in dumped


def test_report_blocks_public_official_claim_authority_when_mutated():
    m = _module()
    report = _safe_report()
    report["denied_authority"]["permits_official_claims"] = "yes"
    report["denied_authority"]["permits_solution_or_proof_claims"] = True
    validation = m.validate_controlled_unknown_engine_shadow_report_v1(report)
    assert validation["valid"] is False
    assert "authority_field_not_false:permits_official_claims" in validation["errors"]
    assert "authority_field_not_false:permits_solution_or_proof_claims" in validation["errors"]
