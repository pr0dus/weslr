from __future__ import annotations

from dataclasses import asdict
import sys

import pytest

from weslr.file_manifest_builder import (
    FileManifest,
    build_file_manifest_from_stack_decision_v1,
    build_file_manifest_v1,
    build_initial_file_manifest_examples_v1,
    summarize_file_manifest_v1,
    to_file_manifest_json_safe_v1,
    validate_file_manifest_v1,
)
from weslr.project_stack_decision_helper import (
    build_initial_project_stack_decision_examples_v1,
    build_project_stack_decision_v1,
)


def _find_example(examples, manifest_type):
    for manifest in examples:
        if manifest.manifest_type == manifest_type:
            return manifest
    raise AssertionError(f"missing example {manifest_type}")


def _find_named_example(examples, name):
    for manifest in examples:
        if manifest.manifest_id == name or manifest.safe_metadata.get("example_name") == name:
            return manifest
    raise AssertionError(f"missing named example {name}")


def _manifest_map(manifest):
    return to_file_manifest_json_safe_v1(manifest)


def _mutate(manifest, **overrides):
    data = _manifest_map(manifest)
    for key, value in overrides.items():
        data[key] = value
    return data


def _mutate_first_entry(manifest, **overrides):
    data = _manifest_map(manifest)
    data["file_entries"][0].update(overrides)
    return data


def test_module_imports_safely():
    import weslr.file_manifest_builder as mod

    assert mod.HELPER_TYPE_V1 == "file_manifest_builder_v1"
    assert mod.FILE_MANIFEST_TYPE_V1 == "file_manifest_v1"
    assert mod.SUMMARY_TYPE_V1 == "file_manifest_summary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_file_manifest():
    stack = build_initial_project_stack_decision_examples_v1()[0]
    first = build_file_manifest_v1(stack)
    second = build_file_manifest_v1(stack)
    assert first == second


def test_builds_file_manifest_from_stack_decision():
    stack = build_initial_project_stack_decision_examples_v1()[1]
    manifest = build_file_manifest_from_stack_decision_v1(stack)
    assert manifest.source_stack_decision_id == stack.stack_decision_id
    assert manifest.source_architecture_id == stack.source_architecture_id
    assert manifest.source_brief_id == stack.source_brief_id
    assert manifest.project_title == stack.project_title
    assert validate_file_manifest_v1(manifest) is True


def test_validates_normal_file_manifest():
    manifest = build_file_manifest_v1(build_initial_project_stack_decision_examples_v1()[2])
    assert validate_file_manifest_v1(manifest) is True


def test_json_safe_export_works():
    manifest = build_file_manifest_v1(build_initial_project_stack_decision_examples_v1()[3])
    exported = to_file_manifest_json_safe_v1(manifest)
    assert isinstance(exported, dict)
    assert isinstance(exported["file_entries"], list)
    assert isinstance(exported["file_entries"][0], dict)
    assert exported["manifest_type"] == manifest.manifest_type


def test_summary_includes_manifest_type_file_count_next_artifact():
    manifest = build_file_manifest_v1(build_initial_project_stack_decision_examples_v1()[4])
    summary = summarize_file_manifest_v1(manifest)
    assert summary.manifest_type == manifest.manifest_type
    assert summary.file_count == len(manifest.file_entries)
    assert summary.recommended_next_artifact == manifest.recommended_next_artifact


def test_initial_examples_exist():
    assert len(build_initial_file_manifest_examples_v1()) >= 8


@pytest.mark.parametrize(
    "name",
    [
        "wifi_rf_self_care_file_manifest",
        "metamaterials_research_file_manifest",
        "ai_agent_architecture_file_manifest",
        "medical_software_pathway_file_manifest",
        "industrial_automation_file_manifest",
        "software_product_static_web_file_manifest",
        "theory_of_mind_conceptual_file_manifest",
        "unknown_domain_file_manifest",
    ],
)
def test_named_initial_examples_exist(name):
    manifest = _find_named_example(build_initial_file_manifest_examples_v1(), name)
    assert manifest.manifest_id == name or manifest.safe_metadata["example_name"] == name


def test_wifi_rf_self_care_manifest_exists():
    manifest = _find_example(build_initial_file_manifest_examples_v1(), "privacy_sensitive_local_manifest")
    assert manifest.manifest_id == "wifi_rf_self_care_file_manifest"


def test_wifi_rf_self_care_manifest_is_privacy_sensitive_local_manifest():
    manifest = _find_example(build_initial_file_manifest_examples_v1(), "privacy_sensitive_local_manifest")
    assert manifest.manifest_type == "privacy_sensitive_local_manifest"
    assert manifest.code_scaffold_allowed is True


def test_wifi_rf_self_care_manifest_includes_readme_docs_config_src_tests():
    manifest = _find_example(build_initial_file_manifest_examples_v1(), "privacy_sensitive_local_manifest")
    paths = {entry.path for entry in manifest.file_entries}
    assert {"README.md", "docs/ARCHITECTURE.md", "docs/PRIVACY_BOUNDARY.md", "config.example.yaml"}.issubset(paths)
    assert {"src/__init__.py", "src/main.py", "src/privacy.py", "src/rules.py", "tests/test_privacy_boundary.py", "tests/test_config.py"}.issubset(paths)


def test_wifi_rf_self_care_manifest_includes_privacy_boundary_doc_and_test():
    manifest = _find_example(build_initial_file_manifest_examples_v1(), "privacy_sensitive_local_manifest")
    paths = {entry.path for entry in manifest.file_entries}
    assert "docs/PRIVACY_BOUNDARY.md" in paths
    assert "tests/test_privacy_boundary.py" in paths


@pytest.mark.parametrize(
    "field_name",
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
def test_no_initial_manifest_allows_forbidden_authority(field_name):
    for manifest in build_initial_file_manifest_examples_v1():
        assert getattr(manifest, field_name) is False


@pytest.mark.parametrize(
    "field_name",
    ["file_entries", "directory_entries", "validation_plan", "dependency_plan", "excluded_paths", "protected_paths", "risk_labels", "boundary_requirements", "privacy_requirements", "safety_requirements", "legal_requirements", "medical_requirements"],
)
def test_manifest_list_fields_are_lists(field_name):
    for manifest in build_initial_file_manifest_examples_v1():
        assert isinstance(getattr(manifest, field_name), list)
        assert getattr(manifest, field_name)


@pytest.mark.parametrize(
    "token",
    ["public claim", "learning", "writes state", "model provider", "file write authority", "dependency install authority", "test execution authority"],
)
def test_no_initial_manifest_mentions_forbidden_authority_tokens(token):
    blob = " ".join(
        " ".join(str(value) for value in asdict(manifest).values())
        for manifest in build_initial_file_manifest_examples_v1()
    ).lower()
    assert token not in blob


@pytest.mark.parametrize(
    "manifest_type, required_paths, expected_next",
    [
        (
            "static_web_preview_manifest",
            {"README.md", "site/index.html", "site/styles.css", "site/app.js", "docs/CONTENT_PLAN.md", "tests/manifest_check.json"},
            "code_scaffold",
        ),
        (
            "materials_research_manifest",
            {"README.md", "docs/RESEARCH_PLAN.md", "docs/EVIDENCE_REQUIREMENTS.md", "config.example.yaml", "src/candidates.py", "src/validation.py", "tests/test_candidates.py", "tests/test_validation.py"},
            "code_scaffold",
        ),
        (
            "ai_system_research_manifest",
            {"README.md", "docs/GOVERNANCE.md", "docs/EVALUATION_PLAN.md", "src/pipeline.py", "src/validation.py", "tests/test_pipeline.py", "tests/test_validation.py"},
            "boundary_review",
        ),
        (
            "medical_software_pathway_manifest",
            {"README.md", "docs/MEDICAL_CLAIM_BOUNDARY.md", "docs/REGULATORY_EVIDENCE_PLAN.md", "docs/SAFETY_VALIDATION_PLAN.md", "config.example.yaml", "src/rules.py", "tests/test_medical_boundary.py"},
            "boundary_review",
        ),
        (
            "industrial_automation_tooling_manifest",
            {"README.md", "docs/SAFETY_BOUNDARY.md", "config.example.yaml", "src/normalizer.py", "src/report.py", "tests/test_normalizer.py", "tests/test_report.py"},
            "validation_plan",
        ),
        (
            "conceptual_research_docs_manifest",
            {"README.md", "docs/DEFINITION_MAP.md", "docs/CLAIM_MAP.md", "docs/EVIDENCE_MAP.md", "docs/UNCERTAINTY_LEDGER.md"},
            "owner_review",
        ),
        (
            "unknown_domain_minimal_manifest",
            {"README.md", "docs/CLARIFYING_QUESTIONS.md", "docs/EVIDENCE_REQUIREMENTS.md"},
            "clarifying_questions",
        ),
    ],
)
def test_manifest_domain_specific_properties(manifest_type, required_paths, expected_next):
    manifest = _find_example(build_initial_file_manifest_examples_v1(), manifest_type)
    paths = {entry.path for entry in manifest.file_entries}
    assert required_paths.issubset(paths)
    assert manifest.recommended_next_artifact == expected_next


def test_conceptual_research_manifest_is_docs_only():
    manifest = _find_example(build_initial_file_manifest_examples_v1(), "conceptual_research_docs_manifest")
    assert manifest.code_scaffold_allowed is False
    assert manifest.runtime_authority is False
    assert all(entry.file_type == "markdown" for entry in manifest.file_entries)


def test_unknown_domain_manifest_uses_clarifying_questions_and_evidence_first():
    manifest = _find_example(build_initial_file_manifest_examples_v1(), "unknown_domain_minimal_manifest")
    paths = {entry.path for entry in manifest.file_entries}
    assert "docs/CLARIFYING_QUESTIONS.md" in paths
    assert "docs/EVIDENCE_REQUIREMENTS.md" in paths
    assert manifest.recommended_next_artifact == "clarifying_questions"


@pytest.mark.parametrize(
    "mutator, expected_error",
    [
        (lambda m: _mutate(m, public_claim_allowed=True), "public_claim_allowed_must_be_false"),
        (lambda m: _mutate(m, runtime_authority=True), "runtime_authority_must_be_false"),
        (lambda m: _mutate(m, writes_state=True), "writes_state_must_be_false"),
        (lambda m: _mutate(m, model_provider_used=True), "model_provider_used_must_be_false"),
        (lambda m: _mutate(m, learning_claimed=True), "learning_claimed_must_be_false"),
        (lambda m: _mutate(m, file_write_authority_granted=True), "file_write_authority_granted_must_be_false"),
        (lambda m: _mutate(m, dependency_install_authority_granted=True), "dependency_install_authority_granted_must_be_false"),
        (lambda m: _mutate(m, test_execution_authority_granted=True), "test_execution_authority_granted_must_be_false"),
        (lambda m: _mutate(m, manifest_type="unknown_manifest_type"), "unknown_manifest_type"),
        (lambda m: _mutate_first_entry(m, file_type="unknown_type"), "unknown_file_type"),
        (lambda m: _mutate_first_entry(m, generation_method="unknown_method"), "unknown_generation_method"),
        (lambda m: _mutate(m, overwrite_policy="unknown_policy"), "unknown_overwrite_policy"),
        (lambda m: _mutate(m, executable_policy="unknown_policy"), "unknown_executable_policy"),
        (lambda m: _mutate(m, recommended_next_artifact="unknown_next"), "unknown_recommended_next_artifact"),
        (lambda m: _mutate(m, safe_metadata={"note": "public iss wording"}), "forbidden_claim_marker_detected"),
        (lambda m: _mutate(m, project_title="AGI consciousness Turing certification study"), "forbidden_claim_marker_detected"),
        (lambda m: _mutate(m, safe_metadata={"note": "unsafe deployment before review"}), "unsafe_deployment_marker_detected"),
        (lambda m: _mutate(m, privacy_requirements=["covert tracking implementation"]), "covert_tracking_marker_detected"),
        (lambda m: _mutate(m, medical_requirements=["diagnosis/treatment authority"], manifest_type="medical_software_pathway_manifest"), "diagnosis_treatment_marker_detected"),
        (lambda m: _mutate_first_entry(m, path="/tmp/evil.py"), "unsafe_file_path"),
        (lambda m: _mutate_first_entry(m, path="../evil.py"), "unsafe_file_path"),
        (lambda m: _mutate_first_entry(m, path="weslr/chat_responder.py"), "protected_path_blocked"),
        (lambda m: _mutate_first_entry(m, path=".env"), "unsafe_file_path"),
        (lambda m: _mutate_first_entry(m, path="secrets/private.key"), "unsafe_file_path"),
        (lambda m: _mutate_first_entry(m, contains_secret=True), "file_entry_contains_secret_must_be_false"),
        (lambda m: _mutate_first_entry(m, contains_private_data=True), "file_entry_contains_private_data_must_be_false"),
    ],
)
def test_validation_rejects_forbidden_states(mutator, expected_error):
    manifest = build_file_manifest_v1(build_initial_project_stack_decision_examples_v1()[0])
    candidate = mutator(manifest)
    with pytest.raises(Exception, match=expected_error):
        validate_file_manifest_v1(candidate)


@pytest.mark.parametrize(
    "path",
    ["/abs/file.py", "../file.py", "./file.py", "~/.env", "C:/file.py", "weslr/chat_responder.py", "dialogue.py", ".env", "secrets/private.key"],
)
def test_path_safety_blocks_bad_paths(path):
    manifest = build_file_manifest_v1(build_initial_project_stack_decision_examples_v1()[0])
    candidate = _mutate_first_entry(manifest, path=path)
    with pytest.raises(Exception):
        validate_file_manifest_v1(candidate)


@pytest.mark.parametrize(
    "field_name, value, expected_error",
    [
        ("manifest_type", "unknown_manifest_type", "unknown_manifest_type"),
        ("recommended_next_artifact", "unknown_next", "unknown_recommended_next_artifact"),
    ],
)
def test_unknown_top_level_enum_values_fail(field_name, value, expected_error):
    manifest = build_file_manifest_v1(build_initial_project_stack_decision_examples_v1()[0])
    candidate = _mutate(manifest, **{field_name: value})
    with pytest.raises(Exception, match=expected_error):
        validate_file_manifest_v1(candidate)


@pytest.mark.parametrize(
    "field_name, value, expected_error",
    [
        ("file_type", "bogus", "unknown_file_type"),
        ("generation_method", "bogus", "unknown_generation_method"),
    ],
)
def test_unknown_file_entry_enum_values_fail(field_name, value, expected_error):
    manifest = build_file_manifest_v1(build_initial_project_stack_decision_examples_v1()[0])
    candidate = _mutate_first_entry(manifest, **{field_name: value})
    with pytest.raises(Exception, match=expected_error):
        validate_file_manifest_v1(candidate)


@pytest.mark.parametrize(
    "field_name, value, expected_error",
    [
        ("overwrite_policy", "bogus", "unknown_overwrite_policy"),
        ("executable_policy", "bogus", "unknown_executable_policy"),
    ],
)
def test_unknown_policy_values_fail(field_name, value, expected_error):
    manifest = build_file_manifest_v1(build_initial_project_stack_decision_examples_v1()[0])
    candidate = _mutate(manifest, **{field_name: value})
    with pytest.raises(Exception, match=expected_error):
        validate_file_manifest_v1(candidate)


@pytest.mark.parametrize(
    "manifest_type, canonical_name",
    [
        ("privacy_sensitive_local_manifest", "wifi_rf_self_care_file_manifest"),
        ("materials_research_manifest", "metamaterials_research_file_manifest"),
        ("ai_system_research_manifest", "ai_agent_architecture_file_manifest"),
        ("medical_software_pathway_manifest", "medical_software_pathway_file_manifest"),
        ("industrial_automation_tooling_manifest", "industrial_automation_file_manifest"),
        ("static_web_preview_manifest", "software_product_static_web_file_manifest"),
        ("conceptual_research_docs_manifest", "theory_of_mind_conceptual_file_manifest"),
        ("unknown_domain_minimal_manifest", "unknown_domain_file_manifest"),
    ],
)
def test_initial_example_names_and_manifest_types(manifest_type, canonical_name):
    manifest = _find_example(build_initial_file_manifest_examples_v1(), manifest_type)
    assert manifest.manifest_id == canonical_name
    assert manifest.safe_metadata["example_name"] == canonical_name


@pytest.mark.parametrize(
    "manifest_type, required_tokens",
    [
        ("privacy_sensitive_local_manifest", ("privacy", "consent", "audit")),
        ("materials_research_manifest", ("evidence", "validation", "scientific")),
        ("ai_system_research_manifest", ("governance", "evaluation", "safety")),
        ("medical_software_pathway_manifest", ("medical", "regulatory", "safety")),
        ("industrial_automation_tooling_manifest", ("safety", "report", "test")),
        ("static_web_preview_manifest", ("html", "css", "javascript")),
        ("conceptual_research_docs_manifest", ("docs", "evidence", "uncertainty")),
        ("unknown_domain_minimal_manifest", ("clarify", "evidence")),
    ],
)
def test_domain_specific_text_tokens_exist(manifest_type, required_tokens):
    manifest = _find_example(build_initial_file_manifest_examples_v1(), manifest_type)
    blob = " ".join(
        [
            manifest.project_title,
            manifest.sensitive_file_policy,
            manifest.dependency_policy,
            " ".join(manifest.risk_labels),
            " ".join(manifest.validation_plan),
            " ".join(manifest.dependency_plan),
            " ".join(manifest.boundary_requirements),
            " ".join(manifest.privacy_requirements),
            " ".join(manifest.safety_requirements),
            " ".join(manifest.legal_requirements),
            " ".join(manifest.medical_requirements),
            " ".join(f"{entry.path} {entry.file_type} {entry.purpose}" for entry in manifest.file_entries),
        ]
    ).lower()
    for token in required_tokens:
        assert token in blob


@pytest.mark.parametrize(
    "manifest_type",
    [
        "privacy_sensitive_local_manifest",
        "materials_research_manifest",
        "ai_system_research_manifest",
        "medical_software_pathway_manifest",
        "industrial_automation_tooling_manifest",
        "static_web_preview_manifest",
        "conceptual_research_docs_manifest",
        "unknown_domain_minimal_manifest",
    ],
)
def test_no_initial_file_entry_has_absolute_path(manifest_type):
    manifest = _find_example(build_initial_file_manifest_examples_v1(), manifest_type)
    assert all(not entry.path.startswith(("/", "~")) for entry in manifest.file_entries)


@pytest.mark.parametrize(
    "manifest_type",
    [
        "privacy_sensitive_local_manifest",
        "materials_research_manifest",
        "ai_system_research_manifest",
        "medical_software_pathway_manifest",
        "industrial_automation_tooling_manifest",
        "static_web_preview_manifest",
        "conceptual_research_docs_manifest",
        "unknown_domain_minimal_manifest",
    ],
)
def test_no_initial_file_entry_has_traversal_path(manifest_type):
    manifest = _find_example(build_initial_file_manifest_examples_v1(), manifest_type)
    assert all(".." not in entry.path for entry in manifest.file_entries)


@pytest.mark.parametrize(
    "manifest_type",
    [
        "privacy_sensitive_local_manifest",
        "materials_research_manifest",
        "ai_system_research_manifest",
        "medical_software_pathway_manifest",
        "industrial_automation_tooling_manifest",
        "static_web_preview_manifest",
        "conceptual_research_docs_manifest",
        "unknown_domain_minimal_manifest",
    ],
)
def test_no_initial_file_entry_contains_secret_or_private_data(manifest_type):
    manifest = _find_example(build_initial_file_manifest_examples_v1(), manifest_type)
    assert all(entry.contains_secret is False for entry in manifest.file_entries)
    assert all(entry.contains_private_data is False for entry in manifest.file_entries)


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("public_claim_allowed", True),
        ("runtime_authority", True),
        ("writes_state", True),
        ("model_provider_used", True),
        ("learning_claimed", True),
        ("file_write_authority_granted", True),
        ("dependency_install_authority_granted", True),
        ("test_execution_authority_granted", True),
    ],
)
def test_boolean_authority_mutations_fail_validation(field_name, value):
    manifest = build_file_manifest_v1(build_initial_project_stack_decision_examples_v1()[0])
    candidate = _mutate(manifest, **{field_name: value})
    with pytest.raises(Exception):
        validate_file_manifest_v1(candidate)


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("safe_metadata", {"raw_prompt": "leak"}),
        ("safe_metadata", {"raw_answer": "leak"}),
        ("safe_metadata", {"transcript": "leak"}),
    ],
)
def test_raw_field_leakage_fails_validation(field_name, value):
    manifest = build_file_manifest_v1(build_initial_project_stack_decision_examples_v1()[0])
    candidate = _mutate(manifest, **{field_name: value})
    with pytest.raises(Exception):
        validate_file_manifest_v1(candidate)


@pytest.mark.parametrize(
    "manifest_type",
    [
        "privacy_sensitive_local_manifest",
        "materials_research_manifest",
        "ai_system_research_manifest",
        "medical_software_pathway_manifest",
        "industrial_automation_tooling_manifest",
        "static_web_preview_manifest",
        "conceptual_research_docs_manifest",
        "unknown_domain_minimal_manifest",
    ],
)
def test_manifest_validation_succeeds_on_safe_initial_examples(manifest_type):
    manifest = _find_example(build_initial_file_manifest_examples_v1(), manifest_type)
    assert validate_file_manifest_v1(manifest) is True


@pytest.mark.parametrize(
    "manifest_type",
    [
        "privacy_sensitive_local_manifest",
        "materials_research_manifest",
        "ai_system_research_manifest",
        "medical_software_pathway_manifest",
        "industrial_automation_tooling_manifest",
        "static_web_preview_manifest",
        "conceptual_research_docs_manifest",
        "unknown_domain_minimal_manifest",
    ],
)
def test_manifest_has_owner_approval_markers(manifest_type):
    manifest = _find_example(build_initial_file_manifest_examples_v1(), manifest_type)
    assert all(entry.owner_approval_required is True for entry in manifest.file_entries)


@pytest.mark.parametrize(
    "manifest_type",
    [
        "privacy_sensitive_local_manifest",
        "materials_research_manifest",
        "ai_system_research_manifest",
        "medical_software_pathway_manifest",
        "industrial_automation_tooling_manifest",
        "static_web_preview_manifest",
        "conceptual_research_docs_manifest",
        "unknown_domain_minimal_manifest",
    ],
)
def test_manifest_file_types_are_known(manifest_type):
    manifest = _find_example(build_initial_file_manifest_examples_v1(), manifest_type)
    assert all(entry.file_type in {
        "markdown",
        "python",
        "python_test",
        "yaml",
        "json",
        "sqlite_placeholder",
        "html",
        "css",
        "javascript",
        "shell_script",
        "directory_placeholder",
    } for entry in manifest.file_entries)


@pytest.mark.parametrize(
    "manifest_type",
    [
        "privacy_sensitive_local_manifest",
        "materials_research_manifest",
        "ai_system_research_manifest",
        "medical_software_pathway_manifest",
        "industrial_automation_tooling_manifest",
        "static_web_preview_manifest",
        "conceptual_research_docs_manifest",
        "unknown_domain_minimal_manifest",
    ],
)
def test_manifest_entry_paths_are_relative_and_safe(manifest_type):
    manifest = _find_example(build_initial_file_manifest_examples_v1(), manifest_type)
    assert all(not entry.path.startswith(("/", "~")) for entry in manifest.file_entries)
    assert all(".." not in entry.path for entry in manifest.file_entries)
    assert all(not entry.path.startswith(".") or entry.path in {"README.md"} for entry in manifest.file_entries)


@pytest.mark.parametrize(
    "manifest_type",
    [
        "privacy_sensitive_local_manifest",
        "materials_research_manifest",
        "ai_system_research_manifest",
        "medical_software_pathway_manifest",
        "industrial_automation_tooling_manifest",
        "static_web_preview_manifest",
        "conceptual_research_docs_manifest",
        "unknown_domain_minimal_manifest",
    ],
)
def test_manifest_does_not_touch_protected_runtime_files(manifest_type):
    manifest = _find_example(build_initial_file_manifest_examples_v1(), manifest_type)
    protected = {"weslr/chat_responder.py", "weslr/main.py", "dialogue.py", "chat_ui.py", ".weslr", ".env"}
    assert all(entry.path not in protected for entry in manifest.file_entries)
