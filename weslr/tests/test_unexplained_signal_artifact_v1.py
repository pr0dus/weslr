from copy import deepcopy

from weslr.unexplained_signal_artifact import (
    build_initial_unexplained_signal_artifact_examples_v1,
    build_unexplained_signal_artifact_v1,
    render_unexplained_signal_artifact_markdown_v1,
    summarize_unexplained_signal_artifact_v1,
    to_unexplained_signal_artifact_json_safe_v1,
    validate_unexplained_signal_artifact_v1,
)


def _base_packet():
    return build_unexplained_signal_artifact_v1(
        artifact_id="artifact_1",
        artifact_kind="unknown_domain_signal",
        artifact_title="Safe artifact",
        domain_family="radio_astronomy",
        source_boundary="metadata_only_locator_record",
        signal_summary="metadata-only signal",
        observed_pattern_metadata=["unexpected signal"],
        knowns=["known"],
        unknowns=["unknown"],
        candidate_explanations=["candidate"],
        alternative_explanations=["alternative"],
        disconfirmation_tests=["test"],
        required_evidence_classes=["metadata"],
        missing_evidence=["gap"],
        cross_domain_pattern_candidates=["cross-domain"],
        natural_pattern_analogies=["natural"],
        engineering_pattern_analogies=["engineering"],
        possible_experiment_paths=["experiment"],
        possible_tooling_paths=["tooling"],
        possible_product_or_artifact_paths=["artifact"],
        owner_review_required=True,
        expert_review_required=False,
        blocked_claims=["final answer"],
        denied_authority_flags={
            "accepted_evidence_authority": False,
            "accepted_candidate_authority": False,
            "proof_claim_authority": False,
            "discovery_truth_claim_authority": False,
            "public_science_claim_authority": False,
            "product_readiness_claim_authority": False,
            "final_answer_authority": False,
            "source_ingestion_authority": False,
            "source_fetch_authority": False,
            "pdf_fetch_authority": False,
            "dataset_fetch_authority": False,
            "github_repo_fetch_authority": False,
            "provider_model_call_authority": False,
            "runtime_wiring_authority": False,
            "chat_responder_edit_authority": False,
            "ui_voice_integration_authority": False,
            "database_write_authority": False,
            "memory_mutation_authority": False,
            "project_mutation_authority": False,
            "weslr_io_authority": False,
            "ontology_auto_application_authority": False,
            "ontology_self_modification_authority": False,
            "behavior_pack_promotion_authority": False,
        },
        next_work_lanes=[{
            "lane_id": "REVIEW_SAFE_V1",
            "lane_type": "review",
            "lane_title": "Review safe artifact",
            "why_recommended": "safe follow-up",
            "depends_on": ["owner review"],
            "owner_review_required": True,
            "expert_review_required": False,
            "blocked_until": ["owner review"],
            "allowed_actions": ["review"],
            "forbidden_actions": ["final_answer", "source_ingestion"],
            "validation_commands": ["git diff --check"],
            "protected_file_checks": ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
            "expected_output_artifact": "docs/out.md",
            "final_judgment_options": ["review_only"],
        }],
        safe_forward_plan="safe plan",
        blocked_labels=["blocked"],
        safe_metadata_summary="safe summary",
        final_judgment="review_only",
    )


def test_valid_pulsar_known_science_replay_builds():
    assert validate_unexplained_signal_artifact_v1(build_initial_unexplained_signal_artifact_examples_v1()[0])


def test_valid_unexplained_radio_transient_builds():
    assert validate_unexplained_signal_artifact_v1(build_initial_unexplained_signal_artifact_examples_v1()[1])


def test_valid_energy_system_anomaly_builds():
    assert validate_unexplained_signal_artifact_v1(build_initial_unexplained_signal_artifact_examples_v1()[2])


def test_valid_language_protocol_emergence_builds():
    assert validate_unexplained_signal_artifact_v1(build_initial_unexplained_signal_artifact_examples_v1()[3])


def test_unsafe_overclaiming_artifact_invalid_or_blocked():
    assert not validate_unexplained_signal_artifact_v1(build_initial_unexplained_signal_artifact_examples_v1()[4])


def test_required_fields_missing_fails_validation():
    packet = _base_packet()
    del packet["final_judgment"]
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_weslr_path_rejected():
    packet = _base_packet()
    packet["source_boundary"] = "blocked_source_content.weslr"
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_true_denied_authority_flag_rejected():
    packet = _base_packet()
    packet["denied_authority_flags"]["public_science_claim_authority"] = True
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_accepted_language_rejected():
    packet = _base_packet()
    packet["blocked_claims"] = ["accepted evidence"]
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_proof_discovery_public_science_rejected():
    packet = _base_packet()
    packet["signal_summary"] = "WESLR proved a new astrophysics discovery"
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_agi_consciousness_sentience_rejected():
    packet = _base_packet()
    packet["signal_summary"] = "AGI consciousness sentience"
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_source_ingestion_fetch_provider_runtime_rejected():
    packet = _base_packet()
    packet["denied_authority_flags"]["source_ingestion_authority"] = True
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_final_answer_authority_rejected():
    packet = _base_packet()
    packet["denied_authority_flags"]["final_answer_authority"] = True
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_empty_disconfirmation_tests_rejected():
    packet = _base_packet()
    packet["disconfirmation_tests"] = []
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_empty_required_evidence_classes_rejected():
    packet = _base_packet()
    packet["required_evidence_classes"] = []
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_owner_review_not_required_rejected():
    packet = _base_packet()
    packet["owner_review_required"] = False
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_empty_blocked_claims_rejected():
    packet = _base_packet()
    packet["blocked_claims"] = []
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_safe_forward_plan_required():
    packet = _base_packet()
    packet["safe_forward_plan"] = ""
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_unknown_kind_without_blocked_posture_rejected():
    packet = _base_packet()
    packet["artifact_kind"] = "unknown"
    packet["blocked_claims"] = []
    assert not validate_unexplained_signal_artifact_v1(packet)


def test_json_safe_copy_deterministic_and_non_mutating():
    packet = _base_packet()
    original = deepcopy(packet)
    out1 = to_unexplained_signal_artifact_json_safe_v1(packet)
    out2 = to_unexplained_signal_artifact_json_safe_v1(packet)
    assert out1 == out2
    assert packet == original


def test_markdown_renderer_includes_safe_sections():
    md = render_unexplained_signal_artifact_markdown_v1(_base_packet())
    assert "Artifact ID" in md
    assert "Source boundary" in md
    assert "Disconfirmation tests" in md
    assert "Required evidence classes" in md
    assert "Blocked claims count" in md


def test_markdown_renderer_excludes_raw_private_final_answer_content():
    md = render_unexplained_signal_artifact_markdown_v1(_base_packet())
    assert "raw source text" not in md.lower()
    assert "final answer" not in md.lower()


def test_summary_is_compact_and_safe():
    s = summarize_unexplained_signal_artifact_v1(_base_packet())
    assert len(s) < 300
    assert "artifact_1" in s


def test_examples_all_validate_except_intentionally_unsafe():
    examples = build_initial_unexplained_signal_artifact_examples_v1()
    assert validate_unexplained_signal_artifact_v1(examples[0])
    assert validate_unexplained_signal_artifact_v1(examples[1])
    assert validate_unexplained_signal_artifact_v1(examples[2])
    assert validate_unexplained_signal_artifact_v1(examples[3])
    assert not validate_unexplained_signal_artifact_v1(examples[4])


def test_pulsar_example_explicitly_blocks_discovered_pulsars():
    packet = build_initial_unexplained_signal_artifact_examples_v1()[0]
    assert any("WESLR discovered pulsars" in x for x in packet["blocked_claims"])


def test_energy_example_next_lane_compatibility_with_third_true_run():
    packet = build_initial_unexplained_signal_artifact_examples_v1()[2]
    assert packet["next_work_lanes"][0]["lane_id"] == "PLAN_WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_V1"
    assert validate_unexplained_signal_artifact_v1(packet)


def test_language_protocol_example_blocks_universal_language_claims():
    packet = build_initial_unexplained_signal_artifact_examples_v1()[3]
    assert any("universal-language" in x or "understands all communication" in x for x in packet["blocked_claims"])


def test_no_example_grants_source_ingestion_provider_runtime_final_answer_authority():
    for packet in build_initial_unexplained_signal_artifact_examples_v1():
        assert all(v is False for v in packet["denied_authority_flags"].values())
