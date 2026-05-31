from __future__ import annotations

import inspect

import pytest

from weslr.project_architecture_planner import build_initial_project_architecture_examples_v1
from weslr.project_stack_decision_helper import (
    StackDecision,
    build_initial_project_stack_decision_examples_v1,
    build_project_stack_decision_from_architecture_v1,
    build_project_stack_decision_v1,
    summarize_project_stack_decision_v1,
    to_project_stack_decision_json_safe_v1,
    validate_project_stack_decision_v1,
)



def _find_example(examples, stack_decision_type):
    for decision in examples:
        if decision.stack_decision_type == stack_decision_type:
            return decision
    raise AssertionError(f"missing example {stack_decision_type}")



def _example_map():
    return {
        decision.stack_decision_type: decision
        for decision in build_initial_project_stack_decision_examples_v1()
    }



def _architecture_example_by_type(architecture_type):
    for architecture in build_initial_project_architecture_examples_v1():
        if architecture.architecture_type == architecture_type:
            return architecture
    raise AssertionError(f"missing architecture example {architecture_type}")



def test_module_imports_safely():
    import weslr.project_stack_decision_helper as mod

    assert mod.HELPER_TYPE_V1 == "project_stack_decision_helper_v1"
    assert mod.STACK_DECISION_TYPE_V1 == "project_stack_decision_v1"
    assert mod.SUMMARY_TYPE_V1 == "project_stack_decision_summary_v1"



def test_builds_deterministic_stack_decision():
    architecture = _architecture_example_by_type("privacy_sensitive_assistive_architecture")
    first = build_project_stack_decision_v1(architecture)
    second = build_project_stack_decision_v1(architecture)
    assert first == second



def test_builds_stack_decision_from_architecture_plan():
    architecture = _architecture_example_by_type("software_product_architecture")
    decision = build_project_stack_decision_from_architecture_v1(architecture)
    assert decision.source_architecture_id == architecture.architecture_id
    assert decision.source_brief_id == architecture.source_brief_id
    assert decision.project_title == architecture.project_title
    assert decision.architecture_type == architecture.architecture_type
    assert validate_project_stack_decision_v1(decision) is True



def test_validates_normal_stack_decision():
    decision = build_project_stack_decision_v1(_architecture_example_by_type("ai_system_architecture"))
    assert validate_project_stack_decision_v1(decision) is True



def test_json_safe_export_works():
    decision = build_project_stack_decision_v1(_architecture_example_by_type("materials_research_architecture"))
    exported = to_project_stack_decision_json_safe_v1(decision)
    assert isinstance(exported, dict)
    assert exported["stack_decision_type"] == decision.stack_decision_type
    assert isinstance(exported["artifact_targets"], list)



def test_summary_includes_stack_type_primary_language_runtime_target_next_artifact():
    decision = build_project_stack_decision_v1(_architecture_example_by_type("industrial_automation_architecture"))
    summary = summarize_project_stack_decision_v1(decision)
    assert summary.stack_decision_type == decision.stack_decision_type
    assert summary.primary_language == decision.primary_language
    assert summary.runtime_target == decision.runtime_target
    assert summary.recommended_next_artifact == decision.recommended_next_artifact



def test_initial_examples_exist():
    assert len(build_initial_project_stack_decision_examples_v1()) >= 8


@pytest.mark.parametrize(
    "stack_type,expected_runtime,expected_language,required_tokens",
    [
        (
            "privacy_sensitive_local_stack",
            "local_python_with_static_dashboard",
            "python",
            ("privacy", "audit", "user control"),
        ),
        (
            "materials_research_stack",
            "local_python",
            "python",
            ("evidence", "validation", "scientific"),
        ),
        (
            "ai_system_research_stack",
            "local_python",
            "python",
            ("governance", "evaluation", "report"),
        ),
        (
            "medical_software_pathway_stack",
            "local_python",
            "python",
            ("clinical", "regulatory", "safety"),
        ),
        (
            "industrial_automation_tooling_stack",
            "local_python",
            "python",
            ("config", "report", "test"),
        ),
    ],
)
def test_wifi_rf_materials_ai_medical_industrial_stack_properties(stack_type, expected_runtime, expected_language, required_tokens):
    if stack_type == "privacy_sensitive_local_stack":
        decision = _find_example(build_initial_project_stack_decision_examples_v1(), stack_type)
    elif stack_type == "materials_research_stack":
        decision = _find_example(build_initial_project_stack_decision_examples_v1(), stack_type)
    elif stack_type == "ai_system_research_stack":
        decision = _find_example(build_initial_project_stack_decision_examples_v1(), stack_type)
    elif stack_type == "medical_software_pathway_stack":
        decision = _find_example(build_initial_project_stack_decision_examples_v1(), stack_type)
    else:
        decision = _find_example(build_initial_project_stack_decision_examples_v1(), stack_type)
    blob = " ".join([
        decision.stack_rationale,
        decision.privacy_stack_requirements,
        decision.safety_stack_requirements,
        decision.legal_stack_requirements,
        decision.medical_stack_requirements,
        decision.ui_strategy,
        decision.backend_strategy,
        decision.data_strategy,
        decision.test_strategy,
        " ".join(decision.validation_commands),
        " ".join(decision.artifact_targets),
    ]).lower()
    assert decision.runtime_target == expected_runtime
    assert decision.primary_language == expected_language
    for token in required_tokens:
        assert token in blob



def test_materials_research_stack_specific_properties():
    decision = _find_example(build_initial_project_stack_decision_examples_v1(), "materials_research_stack")
    blob = " ".join([decision.stack_rationale, decision.test_strategy, decision.dependency_policy]).lower()
    assert decision.primary_language == "python"
    assert "scientific" in blob
    assert "dependency" in blob
    assert "validation" in blob


@pytest.mark.parametrize(
    "check_name, token",
    [
        ("ai_governance", "governance"),
        ("ai_evaluation", "evaluation"),
        ("ai_reporting", "report"),
    ],
)
def test_ai_system_stack_specific_properties(check_name, token):
    decision = _find_example(build_initial_project_stack_decision_examples_v1(), "ai_system_research_stack")
    blob = " ".join([decision.stack_rationale, decision.ui_strategy, decision.safety_stack_requirements, decision.test_strategy]).lower()
    assert decision.primary_language == "python"
    assert token in blob
    assert "agi" not in blob


@pytest.mark.parametrize(
    "token",
    ["clinical", "regulatory"],
)
def test_medical_software_stack_specific_properties(token):
    decision = _find_example(build_initial_project_stack_decision_examples_v1(), "medical_software_pathway_stack")
    blob = " ".join([decision.stack_rationale, decision.medical_stack_requirements, decision.safety_stack_requirements, decision.validation_commands[2]]).lower()
    assert decision.primary_language == "python"
    assert token in blob
    assert "diagnosis" not in decision.stack_rationale.lower()


@pytest.mark.parametrize(
    "token",
    ["config", "report"],
)
def test_industrial_automation_stack_specific_properties(token):
    decision = _find_example(build_initial_project_stack_decision_examples_v1(), "industrial_automation_tooling_stack")
    blob = " ".join([decision.stack_rationale, decision.ui_strategy, decision.validation_commands[2], decision.validation_commands[3]]).lower()
    assert decision.primary_language == "python"
    assert token in blob
    assert "unsafe control" not in decision.rejected_stack_options[0]


@pytest.mark.parametrize(
    "token",
    ["static_html", "browser_javascript"],
)
def test_software_product_static_web_stack_specific_properties(token):
    decision = _find_example(build_initial_project_stack_decision_examples_v1(), "static_web_preview_stack")
    blob = " ".join(decision.artifact_targets + [decision.ui_strategy, decision.backend_strategy]).lower()
    assert decision.primary_language == "html"
    assert token in blob
    assert decision.runtime_target == "local_static_web"


@pytest.mark.parametrize(
    "token",
    ["docs", "runtime", "conceptual", "evidence"],
)
def test_theory_of_mind_conceptual_stack_specific_properties(token):
    decision = _find_example(build_initial_project_stack_decision_examples_v1(), "conceptual_research_docs_stack")
    blob = " ".join([decision.stack_rationale, decision.ui_strategy, decision.runtime_target]).lower()
    assert decision.primary_language == "markdown"
    assert token in blob


@pytest.mark.parametrize("field_name",
    [
        "public_claim_allowed",
        "learning_claimed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "file_write_authority_granted",
        "dependency_install_authority_granted",
        "test_execution_authority_granted",
    ],
)
def test_initial_stack_invariants_are_false(field_name):
    for decision in build_initial_project_stack_decision_examples_v1():
        assert getattr(decision, field_name) is False



def test_unknown_domain_stack_specific_properties():
    decision = _find_example(build_initial_project_stack_decision_examples_v1(), "unknown_domain_minimal_stack")
    assert decision.recommended_next_artifact == "clarifying_questions"
    assert decision.runtime_target == "unknown_pending_requirements"
    assert "clarification" in decision.stack_rationale.lower()


@pytest.mark.parametrize(
    "field_name, value, error_fragment",
    [
        ("public_claim_allowed", True, "public_claim_allowed_must_be_false"),
        ("runtime_authority", True, "runtime_authority_must_be_false"),
        ("writes_state", True, "writes_state_must_be_false"),
        ("model_provider_used", True, "model_provider_used_must_be_false"),
        ("learning_claimed", True, "learning_claimed_must_be_false"),
        ("file_write_authority_granted", True, "file_write_authority_granted_must_be_false"),
        ("dependency_install_authority_granted", True, "dependency_install_authority_granted_must_be_false"),
        ("test_execution_authority_granted", True, "test_execution_authority_granted_must_be_false"),
        ("raw_prompt", "leak", "forbidden_raw_fields_present"),
        ("raw_answer", "leak", "forbidden_raw_fields_present"),
        ("transcript", "leak", "forbidden_raw_fields_present"),
        ("stack_decision_type", "bad_stack_type", "unknown_stack_decision_type"),
        ("artifact_targets", ["bad_target"], "unknown"),
        ("runtime_target", "bad_runtime", "unknown_runtime_target"),
        ("storage_choice", "bad_storage", "unknown_storage_choice"),
        ("dependency_policy", "bad_policy", "unknown_dependency_policy"),
        ("recommended_next_artifact", "bad_next", "unknown_recommended_next_artifact"),
        ("stack_rationale", "public ISS wording", "forbidden_public_or_claim_language_present"),
        ("stack_rationale", "official AGI certification claim", "forbidden_public_or_claim_language_present"),
        ("ui_strategy", "unsafe deployment", "unsafe_deployment_marker_present"),
        ("privacy_stack_requirements", "covert tracking implementation", "covert_tracking_marker_present"),
        ("medical_stack_requirements", "diagnosis authority", "diagnosis_treatment_authority_marker_present"),
        ("prototype_allowed_level", "bad_level", "unknown_prototype_allowed_level"),
    ],
)
def test_validation_failure_cases(field_name, value, error_fragment):
    decision = to_project_stack_decision_json_safe_v1(build_initial_project_stack_decision_examples_v1()[0])
    decision[field_name] = value
    with pytest.raises(ValueError) as excinfo:
        validate_project_stack_decision_v1(decision)
    assert error_fragment in str(excinfo.value)


@pytest.mark.parametrize("protected_name", ["weslr.chat_responder", "weslr.main", "dialogue", "chat_ui"])
def test_module_does_not_import_or_call_protected_files(protected_name):
    source = inspect.getsource(__import__("weslr.project_stack_decision_helper", fromlist=["*"]))
    assert protected_name not in source
