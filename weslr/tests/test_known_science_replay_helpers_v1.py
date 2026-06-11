from __future__ import annotations

import ast
import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.known_science_replay_helpers as ksr

SOURCE_PATH = Path("weslr/known_science_replay_helpers.py")
BASE_CASES_V1 = ksr.build_initial_known_science_replay_examples_v1()
BASE_PULSAR_CASE_V1 = deepcopy(BASE_CASES_V1[0])


def _validate_case(case):
    return ksr.validate_known_science_replay_case_v1(case)


def test_public_apis_exist() -> None:
    for name in (
        "build_known_science_replay_case_v1",
        "build_known_science_replay_phase_v1",
        "build_known_science_replay_selector_calibration_v1",
        "build_known_science_replay_component_mapping_v1",
        "validate_known_science_replay_case_v1",
        "summarize_known_science_replay_case_v1",
        "to_known_science_replay_json_safe_v1",
        "build_initial_known_science_replay_examples_v1",
    ):
        assert hasattr(ksr, name)


def test_initial_examples_include_canonical_and_optional_cases() -> None:
    cases = BASE_CASES_V1
    assert len(cases) == 5
    assert cases[0]["case_id"] == "pulsar_discovery_replay"
    assert {case["case_id"] for case in cases} == {
        "pulsar_discovery_replay",
        "continental_drift_replay",
        "penicillin_contamination_replay",
        "cosmic_microwave_background_replay",
        "helicobacter_pylori_ulcer_replay",
    }
    for case in cases:
        validation = _validate_case(case)
        assert validation["valid"]
        assert case["denied_authority"]["all_authority_flags_false"] is True
        assert case["authority_status"]["all_authority_flags_false"] is True
        assert json.dumps(ksr.to_known_science_replay_json_safe_v1(case))


def test_canonical_pulsar_case_passes_and_contains_expected_progression() -> None:
    case = BASE_PULSAR_CASE_V1
    validation = _validate_case(case)
    summary = ksr.summarize_known_science_replay_case_v1(case)

    assert validation["valid"]
    assert case["known_outcome"] == "pulsars / rotating neutron stars"
    assert case["historical_signal_summary"].startswith("strange periodic radio signal")
    assert case["expected_internal_next_steps"] == ["probe", "pressure_test", "calibrate", "archive", "operator_review"]
    assert case["selector_calibration"]["selector_outcomes"] == ["probe", "pressure_test", "calibrate", "archive", "operator_review"]
    assert [phase["expected_selector_outcome"] for phase in case["replay_phases"]] == ["probe", "pressure_test", "calibrate", "archive", "operator_review"]
    assert "Known-science replay case pulsar_discovery_replay" in summary["summary_text"]
    assert json.dumps(ksr.to_known_science_replay_json_safe_v1(case))


def test_optional_replay_stubs_validate_as_calibration_examples() -> None:
    for case in BASE_CASES_V1[1:]:
        validation = _validate_case(case)
        assert validation["valid"]
        assert case["implementation_readiness"] == "design-only calibration stub"


@pytest.mark.parametrize(
    ("mutator", "expected_label"),
    [
        (lambda case: case.pop("case_id"), "missing_case_id"),
        (lambda case: case.pop("known_outcome"), "missing_known_outcome"),
        (lambda case: case.pop("historical_signal_summary"), "missing_historical_signal_summary"),
        (lambda case: case.pop("initial_ambiguity"), "missing_initial_ambiguity"),
        (lambda case: case.pop("ordinary_explanations_to_pressure"), "missing_ordinary_explanations_to_pressure"),
        (lambda case: case.pop("pressure_tests"), "missing_pressure_tests"),
        (lambda case: case.pop("calibration_signals"), "missing_calibration_signals"),
        (lambda case: case.pop("forbidden_interpretations"), "missing_forbidden_interpretations"),
        (lambda case: case.pop("authority_status"), "missing_authority_status"),
        (lambda case: case.pop("denied_authority"), "missing_denied_authority"),
        (lambda case: case.pop("safe_metadata"), "missing_safe_metadata"),
    ],
)
def test_case_validation_fail_closed_on_required_fields(mutator, expected_label) -> None:
    case = deepcopy(BASE_PULSAR_CASE_V1)
    mutator(case)
    validation = _validate_case(case)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    ("field", "value", "expected_label"),
    [
        ("forbidden_interpretations", ["discovery claim"], "forbidden_claim_language"),
        ("safe_interpretation", "discovery proof breakthrough", "forbidden_claim_language"),
        ("ordinary_explanations_to_pressure", ["proof claim"], "forbidden_claim_language"),
        ("candidate_hypotheses", ["breakthrough claim"], "forbidden_claim_language"),
        ("pressure_tests", ["scientific result claim"], "forbidden_claim_language"),
        ("calibration_signals", ["benchmark certification"], "forbidden_claim_language"),
        ("falsification_signals", ["AGI intelligence sentience consciousness"], "forbidden_claim_language"),
        ("case_title", "public science proof claim", "forbidden_claim_language"),
    ],
)
def test_case_validation_fail_closed_on_public_claim_language(field, value, expected_label) -> None:
    case = deepcopy(BASE_PULSAR_CASE_V1)
    case[field] = value
    validation = _validate_case(case)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    ("field", "value", "expected_label"),
    [
        ("historical_signal_summary", "hidden prompt secret", "forbidden_private_text"),
        ("source_scope", "private text .weslr", "forbidden_private_text"),
        ("safe_interpretation", "api key and protected data", "forbidden_private_text"),
        ("implementation_readiness", "private text hidden prompt", "forbidden_private_text"),
        ("candidate_hypotheses", ["secret clue"], "forbidden_private_text"),
        ("forbidden_interpretations", ["secret result"], "forbidden_private_text"),
    ],
)
def test_case_validation_fail_closed_on_hidden_private_protected_markers(field, value, expected_label) -> None:
    case = deepcopy(BASE_PULSAR_CASE_V1)
    case[field] = value
    validation = _validate_case(case)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    ("field", "value", "expected_label"),
    [
        ("authority_status", {**ksr._default_authority_status(), "runtime_action_authorized": True}, "unsafe_runtime_action_authorized"),
        ("authority_status", {**ksr._default_authority_status(), "replay_runner_authorized": True}, "unsafe_replay_runner_authorized"),
        ("authority_status", {**ksr._default_authority_status(), "executor_authorized": True}, "unsafe_executor_authorized"),
        ("authority_status", {**ksr._default_authority_status(), "runner_authorized": True}, "unsafe_runner_authorized"),
        ("authority_status", {**ksr._default_authority_status(), "provider_model_call_authority": True}, "unsafe_provider_model_call_authority"),
        ("authority_status", {**ksr._default_authority_status(), "tool_execution_authority": True}, "unsafe_tool_execution_authority"),
        ("authority_status", {**ksr._default_authority_status(), "web_authority": True}, "unsafe_web_authority"),
        ("authority_status", {**ksr._default_authority_status(), "retrieval_tool_authority": True}, "unsafe_retrieval_tool_authority"),
        ("denied_authority", {**ksr._default_denied_authority(), "runtime_action_authorized": True}, "granted_runtime_action_authorized"),
    ],
)
def test_case_validation_fail_closed_on_unsafe_authority_markers(field, value, expected_label) -> None:
    case = deepcopy(BASE_PULSAR_CASE_V1)
    case[field] = value
    validation = _validate_case(case)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field",
    [
        "expected_internal_next_steps",
        "selector_calibration",
    ],
)
def test_case_validation_fail_closed_on_unknown_selector_outcome(field) -> None:
    case = deepcopy(BASE_PULSAR_CASE_V1)
    if field == "expected_internal_next_steps":
        case[field] = ["probe", "unknown_future_outcome"]
    else:
        case[field]["selector_outcomes"] = ["probe", "unknown_future_outcome"]
    validation = _validate_case(case)

    assert not validation["valid"]
    assert "invalid_selector_outcome" in validation["blocked_labels"]


def test_phase_and_component_mapping_helpers_validate() -> None:
    case = BASE_PULSAR_CASE_V1
    for phase in case["replay_phases"]:
        validation = ksr.validate_known_science_replay_phase_v1(phase)
        assert validation["valid"]
    component_validation = ksr.validate_known_science_replay_component_mapping_v1(case["component_mapping"])
    calibration_validation = ksr.validate_known_science_replay_selector_calibration_v1(case["selector_calibration"])
    assert component_validation["valid"]
    assert calibration_validation["valid"]


def test_json_safe_conversion_rejects_non_json_safe_values() -> None:
    case = deepcopy(BASE_PULSAR_CASE_V1)
    case["replay_phases"][0]["calibration_signals"] = [{"unsafe": {1, 2}}]
    validation = _validate_case(case)
    assert not validation["valid"]
    assert "non_json_safe_result_structure" in validation["blocked_labels"]
    safe = ksr.to_known_science_replay_json_safe_v1(case)
    assert json.dumps(safe)
    assert safe["replay_phases"][0]["calibration_signals"][0]["unsafe"] == [1, 2]


def test_denied_authority_fields_remain_present_and_false() -> None:
    case = BASE_PULSAR_CASE_V1
    assert case["denied_authority"]["all_authority_flags_false"] is True
    for key, value in case["denied_authority"].items():
        if key in {"status", "boundary_notes", "all_authority_flags_false"}:
            continue
        assert value is False


def test_no_writer_api_exists() -> None:
    public_names = set(dir(ksr))
    assert not any(name.startswith(("write", "save", "persist")) for name in public_names if name not in {"__writer__"})


def test_module_source_contains_no_runtime_provider_tool_web_imports_or_calls() -> None:
    source = SOURCE_PATH.read_text()
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    banned_import_terms = ("browser", "web", "message", "tts", "requests", "urllib", "httpx", "playwright")
    assert not any(any(term in item for term in banned_import_terms) for item in imports)
    banned_call_terms = ("web_fetch(", "web_search(", "browser(", "message(", "tts(")
    assert not any(term in source for term in banned_call_terms)
    banned_runtime_terms = ("ChatResponder", "respond_chat", "generate_chat", "provider_model_call_authority = True")
    assert not any(term in source for term in banned_runtime_terms)
