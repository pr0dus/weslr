from __future__ import annotations

import json
from copy import deepcopy

import weslr.oer_noop_record_builder as builder
from weslr.oer_noop_record_builder import (
    build_initial_oer_noop_record_examples_v1,
    build_oer_noop_record_v1,
    render_oer_noop_record_markdown_v1,
    summarize_oer_noop_record_v1,
    to_oer_noop_record_json_safe_v1,
    validate_oer_noop_record_v1,
)


def _valid_materials_record() -> dict:
    return build_oer_noop_record_v1(
        record_id="materials_second_true_run_noop",
        source_artifact_id="second_controlled_true_run_materials",
        domain_family="materials",
        signal_type="materials_metadata_signal",
        current_route="scout_to_metadata_only_source_locator_route",
        covered_by_registry_entries=("materials_registry_entry_v1", "ontology_sufficient_for_domain_v1"),
        next_safe_step="operator_review",
        blocked_claims=("no_unapproved_claims", "no_ownerless_change", "no_auto_application", "no_runtime_activation"),
        blocked_labels=("no_unapproved_claims", "no_auto_application"),
        final_judgment="ontology_sufficient_no_expansion_request_needed",
    )


def _valid_energy_record() -> dict:
    return build_oer_noop_record_v1(
        record_id="energy_systems_planned_noop",
        source_artifact_id="planned_energy_metadata_route",
        domain_family="energy_systems",
        signal_type="energy_metadata_signal",
        current_route="metadata_only_planned_route",
        covered_by_registry_entries=("energy_registry_entry_v1",),
        next_safe_step="continue_metadata_only_route",
        blocked_claims=("no_unapproved_claims", "no_auto_application"),
        final_judgment="ontology_sufficient_no_expansion_request_needed",
    )


def test_public_apis_exist():
    for name in (
        "build_oer_noop_record_v1",
        "validate_oer_noop_record_v1",
        "summarize_oer_noop_record_v1",
        "render_oer_noop_record_markdown_v1",
        "to_oer_noop_record_json_safe_v1",
        "build_initial_oer_noop_record_examples_v1",
    ):
        assert hasattr(builder, name)
        assert callable(getattr(builder, name))


def test_valid_materials_noop_builds():
    record = _valid_materials_record()
    validation = validate_oer_noop_record_v1(record)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert record["ontology_marker"] == "ontology_sufficient_for_domain"
    assert record["sufficient_power"] is True
    assert record["recommended_expansion_actions"] == []
    assert record["missing_ontology_items"] == []
    assert record["owner_review_required"] is True
    assert record["operator_review_required"] is True


def test_valid_energy_noop_builds():
    record = _valid_energy_record()
    validation = validate_oer_noop_record_v1(record)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert record["domain_family"] == "energy_systems"
    assert record["next_safe_step"] == "continue_metadata_only_route"


def test_required_fields_validation():
    record = _valid_materials_record()
    del record["final_judgment"]
    validation = validate_oer_noop_record_v1(record)
    assert validation["blocked"] is True
    assert any(label.startswith("missing_field:final_judgment") for label in validation["blocked_labels"])


def test_wrong_ontology_marker_rejected():
    record = _valid_materials_record()
    record["ontology_marker"] = "wrong"
    assert validate_oer_noop_record_v1(record)["blocked"] is True


def test_sufficient_power_false_rejected():
    record = _valid_materials_record()
    record["sufficient_power"] = False
    assert "sufficient_power_not_true" in validate_oer_noop_record_v1(record)["blocked_labels"]


def test_non_empty_recommended_expansion_actions_rejected():
    record = _valid_materials_record()
    record["recommended_expansion_actions"] = ["expand"]
    assert "recommended_expansion_actions_not_empty" in validate_oer_noop_record_v1(record)["blocked_labels"]


def test_non_empty_missing_ontology_items_rejected():
    record = _valid_materials_record()
    record["missing_ontology_items"] = ["gap"]
    assert "missing_ontology_items_not_empty" in validate_oer_noop_record_v1(record)["blocked_labels"]


def test_any_true_denied_authority_flag_rejected():
    record = _valid_materials_record()
    record["denied_authority_flags"]["ontology_auto_application_authority"] = True
    labels = validate_oer_noop_record_v1(record)["blocked_labels"]
    assert any(label.startswith("denied_authority_true:ontology_auto_application_authority") for label in labels)


def test_owner_operator_review_required():
    record = _valid_materials_record()
    assert record["owner_review_required"] is True
    assert record["operator_review_required"] is True


def test_empty_blocked_claims_rejected():
    record = _valid_materials_record()
    record["blocked_claims"] = []
    assert "blocked_claims_empty" in validate_oer_noop_record_v1(record)["blocked_labels"]


def test_weslr_path_rejected():
    record = _valid_materials_record()
    record["safe_metadata_summary"] = "avoid .weslr writes"
    assert "weslr_io_reference_blocked" in validate_oer_noop_record_v1(record)["blocked_labels"]


def test_source_ingestion_fetch_provider_runtime_authority_rejected():
    record = _valid_materials_record()
    record["why_no_expansion_needed"] = "source ingestion authorized and provider call authorized and runtime enabled"
    labels = validate_oer_noop_record_v1(record)["blocked_labels"]
    assert "runtime_source_provider_authority_language_present" in labels


def test_ontology_auto_application_self_modification_wording_rejected():
    record = _valid_materials_record()
    record["why_no_expansion_needed"] = "ontology applied automatically and ontology self-modified"
    assert "forbidden_wording_present" in validate_oer_noop_record_v1(record)["blocked_labels"]


def test_proof_discovery_public_science_product_readiness_claims_rejected():
    record = _valid_materials_record()
    record["blocked_claims"] = ["proof", "confirmed discovery", "public science claim", "product readiness"]
    labels = validate_oer_noop_record_v1(record)["blocked_labels"]
    assert "forbidden_wording_present" in labels


def test_agi_consciousness_sentience_claims_rejected():
    record = _valid_materials_record()
    record["blocked_claims"] = ["AGI", "consciousness", "sentience"]
    labels = validate_oer_noop_record_v1(record)["blocked_labels"]
    assert "forbidden_wording_present" in labels


def test_accepted_evidence_candidate_wording_rejected():
    record = _valid_materials_record()
    record["blocked_claims"] = ["accepted evidence", "accepted candidate"]
    labels = validate_oer_noop_record_v1(record)["blocked_labels"]
    assert "accepted_or_final_answer_language_present" in labels


def test_final_answer_authority_rejected():
    record = _valid_materials_record()
    record["denied_authority_flags"]["final_answer_authority"] = True
    labels = validate_oer_noop_record_v1(record)["blocked_labels"]
    assert any(label.startswith("denied_authority_true:final_answer_authority") for label in labels)


def test_markdown_renderer_includes_safe_sections():
    md = render_oer_noop_record_markdown_v1(_valid_materials_record())
    assert "Why no expansion is needed" in md
    assert "Covered registry entries" in md
    assert "Blocked claims" in md
    assert "Denied authority summary" in md
    assert "Next safe step" in md


def test_markdown_renderer_excludes_raw_source_or_final_answer_content():
    md = render_oer_noop_record_markdown_v1(_valid_materials_record()).lower()
    assert "raw source" not in md
    assert "final answer" not in md
    assert "accepted evidence" not in md


def test_json_safe_copy_deterministic_and_non_mutating():
    record = _valid_materials_record()
    original = deepcopy(record)
    first = to_oer_noop_record_json_safe_v1(record)
    second = to_oer_noop_record_json_safe_v1(record)
    assert first == second
    assert record == original
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_summary_is_compact_and_safe():
    summary = summarize_oer_noop_record_v1(_valid_materials_record())
    assert summary["record_id"] == "materials_second_true_run_noop"
    assert summary["domain_family"] == "materials"
    assert summary["blocked"] is False
    assert set(summary).issuperset({"record_id", "source_artifact_id", "domain_family", "signal_type", "ontology_marker", "sufficient_power", "next_safe_step", "owner_review_required", "operator_review_required", "blocked", "final_judgment"})


def test_examples_validate_except_intentionally_unsafe():
    examples = build_initial_oer_noop_record_examples_v1()
    assert validate_oer_noop_record_v1(examples[0])["valid"] is True
    assert validate_oer_noop_record_v1(examples[1])["valid"] is True
    assert validate_oer_noop_record_v1(examples[2])["valid"] is False


def test_unsafe_example_is_blocked_for_auto_application_and_proof_language():
    unsafe = build_initial_oer_noop_record_examples_v1()[2]
    labels = validate_oer_noop_record_v1(unsafe)["blocked_labels"]
    assert "forbidden_wording_present" in labels or "denied_authority_true:ontology_auto_application_authority" in labels
