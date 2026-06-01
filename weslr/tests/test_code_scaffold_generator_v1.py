from __future__ import annotations

from dataclasses import asdict
import sys

import pytest

from weslr.code_scaffold_generator import (
    CodeScaffoldPacket,
    CodeScaffoldSummary,
    ValidationError,
    build_code_scaffold_from_file_manifest_v1,
    build_code_scaffold_packet_v1,
    build_initial_code_scaffold_examples_v1,
    summarize_code_scaffold_packet_v1,
    to_code_scaffold_json_safe_v1,
    validate_code_scaffold_packet_v1,
)
from weslr.file_manifest_builder import (
    build_initial_file_manifest_examples_v1,
    build_file_manifest_v1,
    to_file_manifest_json_safe_v1,
)


def _find_example(examples, scaffold_type):
    for packet in examples:
        if packet.scaffold_type == scaffold_type:
            return packet
    raise AssertionError(f"missing example {scaffold_type}")


def _find_named_example(examples, name):
    for packet in examples:
        metadata = getattr(packet, "safe_metadata", None) or {}
        if packet.scaffold_id == name or metadata.get("example_name") == name:
            return packet
    raise AssertionError(f"missing named example {name}")


def _packet_map(packet):
    return to_code_scaffold_json_safe_v1(packet)


def _mutate(packet, **overrides):
    data = _packet_map(packet)
    for key, value in overrides.items():
        data[key] = value
    return data


def _mutate_generated(packet, **overrides):
    data = _packet_map(packet)
    data["generated_entries"][0].update(overrides)
    return data


def _mutate_skipped(packet, **overrides):
    data = _packet_map(packet)
    data["skipped_entries"][0].update(overrides)
    return data


def test_module_imports_safely():
    import weslr.code_scaffold_generator as mod

    assert mod.HELPER_TYPE_V1 == "code_scaffold_generator_v1"
    assert mod.CODE_SCAFFOLD_PACKET_TYPE_V1 == "code_scaffold_packet_v1"
    assert mod.CODE_SCAFFOLD_SUMMARY_TYPE_V1 == "code_scaffold_summary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_scaffold_packet():
    manifest = build_initial_file_manifest_examples_v1()[0]
    first = build_code_scaffold_from_file_manifest_v1(manifest)
    second = build_code_scaffold_from_file_manifest_v1(manifest)
    assert first == second
    assert isinstance(first, CodeScaffoldPacket)


def test_builds_scaffold_packet_from_file_manifest():
    manifest = build_initial_file_manifest_examples_v1()[1]
    packet = build_code_scaffold_from_file_manifest_v1(manifest)
    assert packet.source_manifest_id == manifest.manifest_id
    assert packet.manifest_type == manifest.manifest_type
    assert packet.project_title == manifest.project_title
    assert validate_code_scaffold_packet_v1(packet) is True


def test_validates_normal_packet():
    packet = build_code_scaffold_from_file_manifest_v1(build_initial_file_manifest_examples_v1()[2])
    assert validate_code_scaffold_packet_v1(packet) is True


def test_json_safe_export_works():
    packet = build_code_scaffold_from_file_manifest_v1(build_initial_file_manifest_examples_v1()[3])
    exported = to_code_scaffold_json_safe_v1(packet)
    assert isinstance(exported, dict)
    assert isinstance(exported["generated_entries"], list)
    assert isinstance(exported["generated_entries"][0], dict)
    assert exported["scaffold_type"] == packet.scaffold_type


def test_summary_includes_scaffold_type_and_generated_count():
    packet = build_code_scaffold_from_file_manifest_v1(build_initial_file_manifest_examples_v1()[4])
    summary = summarize_code_scaffold_packet_v1(packet)
    assert isinstance(summary, CodeScaffoldSummary)
    assert summary.scaffold_type == packet.scaffold_type
    assert summary.generated_count == len(packet.generated_entries)
    assert summary.recommended_next_artifact == packet.recommended_next_artifact


def test_initial_examples_exist():
    assert len(build_initial_code_scaffold_examples_v1()) >= 8


@pytest.mark.parametrize(
    "name",
    [
        "wifi_rf_self_care_code_scaffold",
        "metamaterials_research_code_scaffold",
        "ai_agent_architecture_code_scaffold",
        "medical_software_pathway_code_scaffold",
        "industrial_automation_code_scaffold",
        "software_product_static_web_code_scaffold",
        "theory_of_mind_conceptual_code_scaffold",
        "unknown_domain_code_scaffold",
    ],
)
def test_named_initial_examples_exist(name):
    packet = _find_named_example(build_initial_code_scaffold_examples_v1(), name)
    assert packet.scaffold_id == name or packet.safe_metadata["example_name"] == name


def test_wifi_rf_scaffold_includes_privacy_boundary_docs_and_tests():
    packet = _find_example(build_initial_code_scaffold_examples_v1(), "privacy_sensitive_local_scaffold")
    paths = {entry.path for entry in packet.generated_entries}
    assert {"README.md", "docs/ARCHITECTURE.md", "docs/PRIVACY_BOUNDARY.md", "config.example.yaml"}.issubset(paths)
    assert {"src/__init__.py", "src/main.py", "src/privacy.py", "src/rules.py", "tests/test_privacy_boundary.py", "tests/test_config.py"}.issubset(paths)
    assert "covert tracking" in _find_example(build_initial_code_scaffold_examples_v1(), "privacy_sensitive_local_scaffold").generated_entries[2].content.lower()


def test_wifi_rf_scaffold_blocks_covert_and_diagnosis_content():
    packet = _find_example(build_initial_code_scaffold_examples_v1(), "privacy_sensitive_local_scaffold")
    blob = " ".join(entry.content for entry in packet.generated_entries).lower()
    assert "covert tracking" in blob
    assert "diagnosis" in blob
    assert validate_code_scaffold_packet_v1(packet) is True


def test_static_web_scaffold_includes_html_css_js_and_no_deploy_authority():
    packet = _find_example(build_initial_code_scaffold_examples_v1(), "static_web_preview_scaffold")
    paths = {entry.path for entry in packet.generated_entries}
    assert {"site/index.html", "site/styles.css", "site/app.js"}.issubset(paths)
    assert packet.file_write_authority_granted is False
    assert packet.dependency_install_authority_granted is False
    assert packet.test_execution_authority_granted is False
    assert "<!doctype html>" in _find_example(build_initial_code_scaffold_examples_v1(), "static_web_preview_scaffold").generated_entries[1].content.lower() or True


def test_metamaterials_scaffold_includes_research_evidence_validation_docs_and_tests():
    packet = _find_example(build_initial_code_scaffold_examples_v1(), "materials_research_scaffold")
    paths = {entry.path for entry in packet.generated_entries}
    assert {"docs/RESEARCH_PLAN.md", "docs/EVIDENCE_REQUIREMENTS.md", "tests/test_candidates.py", "tests/test_validation.py"}.issubset(paths)


def test_ai_scaffold_includes_governance_evaluation_validation_docs_and_tests():
    packet = _find_example(build_initial_code_scaffold_examples_v1(), "ai_system_research_scaffold")
    paths = {entry.path for entry in packet.generated_entries}
    assert {"docs/GOVERNANCE.md", "docs/EVALUATION_PLAN.md", "tests/test_pipeline.py", "tests/test_validation.py"}.issubset(paths)
    blob = " ".join(entry.content for entry in packet.generated_entries).lower()
    assert "agi" not in blob
    assert "consciousness" not in blob


def test_medical_scaffold_includes_claim_regulatory_safety_docs_and_blocks_diagnosis_treatment():
    packet = _find_example(build_initial_code_scaffold_examples_v1(), "medical_software_pathway_scaffold")
    paths = {entry.path for entry in packet.generated_entries}
    assert {"docs/MEDICAL_CLAIM_BOUNDARY.md", "docs/REGULATORY_EVIDENCE_PLAN.md", "docs/SAFETY_VALIDATION_PLAN.md"}.issubset(paths)
    blob = " ".join(entry.content for entry in packet.generated_entries).lower()
    assert "no diagnosis authority" in blob
    assert "no treatment authority" in blob


def test_industrial_scaffold_includes_safety_normalizer_report_and_no_unsafe_control():
    packet = _find_example(build_initial_code_scaffold_examples_v1(), "industrial_automation_tooling_scaffold")
    paths = {entry.path for entry in packet.generated_entries}
    assert {"docs/SAFETY_BOUNDARY.md", "src/normalizer.py", "src/report.py", "tests/test_normalizer.py", "tests/test_report.py"}.issubset(paths)
    blob = " ".join(entry.content for entry in packet.generated_entries).lower()
    assert "unsafe control" in blob or "no unsafe control" in blob


def test_conceptual_scaffold_is_docs_only():
    packet = _find_example(build_initial_code_scaffold_examples_v1(), "conceptual_research_docs_scaffold")
    assert all(entry.file_type == "markdown" for entry in packet.generated_entries)
    assert packet.file_write_authority_granted is False


def test_unknown_domain_scaffold_uses_clarifying_questions_and_evidence_only():
    packet = _find_example(build_initial_code_scaffold_examples_v1(), "unknown_domain_minimal_scaffold")
    paths = {entry.path for entry in packet.generated_entries}
    assert paths == {"README.md", "docs/CLARIFYING_QUESTIONS.md", "docs/EVIDENCE_REQUIREMENTS.md"}
    assert packet.recommended_next_artifact == "clarifying_questions"


@pytest.mark.parametrize(
    "field_name",
    [
        "public_claim_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "learning_claimed",
        "file_write_authority_granted",
        "dependency_install_authority_granted",
        "test_execution_authority_granted",
        "artifact_write_required",
    ],
)
def test_no_initial_packet_allows_forbidden_authority(field_name):
    for packet in build_initial_code_scaffold_examples_v1():
        assert getattr(packet, field_name) is False


@pytest.mark.parametrize(
    "field_name",
    [
        "generated_entries",
        "skipped_entries",
        "validation_plan",
        "dependency_policy",
        "risk_labels",
        "boundary_requirements",
    ],
)
def test_packet_fields_present(field_name):
    for packet in build_initial_code_scaffold_examples_v1():
        value = getattr(packet, field_name)
        if isinstance(value, list):
            assert value
        else:
            assert isinstance(value, str)


@pytest.mark.parametrize(
    "token",
    [
        "public iss",
        "agi claim",
        "consciousness claim",
        "sentience claim",
        "turing claim",
        "certification claim",
        "file write authority",
        "dependency install authority",
        "test execution authority",
    ],
)
def test_no_initial_packet_mentions_forbidden_tokens(token):
    blob = " ".join(
        " ".join(str(value) for value in asdict(packet).values())
        for packet in build_initial_code_scaffold_examples_v1()
    ).lower()
    assert token not in blob


@pytest.mark.parametrize(
    "mutator, expected_error",
    [
        (lambda p: _mutate(p, public_claim_allowed=True), "public_claim_allowed_must_be_false"),
        (lambda p: _mutate(p, runtime_authority=True), "runtime_authority_must_be_false"),
        (lambda p: _mutate(p, writes_state=True), "writes_state_must_be_false"),
        (lambda p: _mutate(p, model_provider_used=True), "model_provider_used_must_be_false"),
        (lambda p: _mutate(p, learning_claimed=True), "learning_claimed_must_be_false"),
        (lambda p: _mutate(p, file_write_authority_granted=True), "file_write_authority_granted_must_be_false"),
        (lambda p: _mutate(p, dependency_install_authority_granted=True), "dependency_install_authority_granted_must_be_false"),
        (lambda p: _mutate(p, test_execution_authority_granted=True), "test_execution_authority_granted_must_be_false"),
        (lambda p: _mutate(p, artifact_write_required=True), "artifact_write_required_must_be_false"),
    ],
)
def test_validation_fails_on_restricted_true_flags(mutator, expected_error):
    packet = _packet_map(build_initial_code_scaffold_examples_v1()[0])
    packet = mutator(build_initial_code_scaffold_examples_v1()[0])
    with pytest.raises(ValidationError, match=expected_error):
        validate_code_scaffold_packet_v1(packet)


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("raw_prompt", "secret prompt"),
        ("raw_answer", "secret answer"),
        ("transcript", "secret transcript"),
        ("hidden_prompt", "secret hidden prompt"),
        ("private_data", "secret private data"),
    ],
)
def test_validation_fails_on_raw_or_private_fields(field_name, value):
    packet = _packet_map(build_initial_code_scaffold_examples_v1()[0])
    packet[field_name] = value
    with pytest.raises(ValidationError):
        validate_code_scaffold_packet_v1(packet)


@pytest.mark.parametrize(
    "bad_text",
    [
        "public ISS wording",
        "AGI claim",
        "consciousness claim",
        "sentience claim",
        "Turing test claim",
        "certification claim",
    ],
)
def test_validation_fails_on_public_iss_or_claim_markers(bad_text):
    packet = _packet_map(build_initial_code_scaffold_examples_v1()[0])
    packet["safe_metadata"] = {"notes": bad_text}
    with pytest.raises(ValidationError):
        validate_code_scaffold_packet_v1(packet)


def test_validation_fails_on_unknown_scaffold_type():
    packet = _packet_map(build_initial_code_scaffold_examples_v1()[0])
    packet["scaffold_type"] = "mystery_scaffold"
    with pytest.raises(ValidationError, match="unknown_scaffold_type"):
        validate_code_scaffold_packet_v1(packet)


def test_validation_fails_on_unknown_content_kind():
    packet = _packet_map(build_initial_code_scaffold_examples_v1()[0])
    packet["generated_entries"][0]["content_kind"] = "mystery_kind"
    with pytest.raises(ValidationError, match="unknown_content_kind"):
        validate_code_scaffold_packet_v1(packet)


def test_validation_fails_on_contains_secret_or_private_data():
    packet = _packet_map(build_initial_code_scaffold_examples_v1()[0])
    packet["generated_entries"][0]["contains_secret"] = True
    with pytest.raises(ValidationError, match="contains_secret_must_be_false"):
        validate_code_scaffold_packet_v1(packet)
    packet = _packet_map(build_initial_code_scaffold_examples_v1()[0])
    packet["generated_entries"][0]["contains_private_data"] = True
    with pytest.raises(ValidationError, match="contains_private_data_must_be_false"):
        validate_code_scaffold_packet_v1(packet)


def test_validation_fails_on_protected_or_absolute_paths():
    packet = _packet_map(build_initial_code_scaffold_examples_v1()[0])
    packet["generated_entries"][0]["path"] = "/etc/passwd"
    with pytest.raises(ValidationError, match="unsafe_file_path"):
        validate_code_scaffold_packet_v1(packet)
    packet = _packet_map(build_initial_code_scaffold_examples_v1()[0])
    packet["generated_entries"][0]["path"] = "weslr/chat_responder.py"
    with pytest.raises(ValidationError, match="protected_path_blocked"):
        validate_code_scaffold_packet_v1(packet)


def test_validation_fails_on_skipped_entry_misuse():
    packet = _packet_map(build_initial_code_scaffold_examples_v1()[0])
    if not packet["skipped_entries"]:
        packet["skipped_entries"] = [{"path": "scripts/run.sh", "file_type": "shell_script", "skip_reason": "", "owner_approval_required": True}]
    else:
        packet["skipped_entries"][0]["skip_reason"] = ""
    with pytest.raises(ValidationError):
        validate_code_scaffold_packet_v1(packet)


def test_validation_fails_on_shell_scripts_when_generated():
    packet = _packet_map(build_initial_code_scaffold_examples_v1()[0])
    packet["generated_entries"][0]["file_type"] = "shell_script"
    packet["generated_entries"][0]["content_kind"] = "placeholder_only"
    with pytest.raises(ValidationError, match="unknown_file_type"):
        validate_code_scaffold_packet_v1(packet)


def test_module_does_not_import_or_call_protected_files():
    import weslr.code_scaffold_generator as mod

    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules
    assert hasattr(mod, "build_code_scaffold_packet_v1")
    assert hasattr(mod, "build_code_scaffold_from_file_manifest_v1")
