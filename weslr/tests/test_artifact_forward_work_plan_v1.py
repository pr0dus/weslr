from copy import deepcopy

from weslr.artifact_forward_work_plan import (
    build_artifact_forward_work_plan_v1,
    build_initial_artifact_forward_work_plan_examples_v1,
    render_artifact_forward_work_plan_markdown_v1,
    summarize_artifact_forward_work_plan_v1,
    to_artifact_forward_work_plan_json_safe_v1,
    validate_artifact_forward_work_plan_v1,
)


def _valid_packet():
    return build_artifact_forward_work_plan_v1(
        plan_id="plan_v1",
        artifact_id="artifact_1",
        artifact_kind="true_run_result",
        artifact_title="Reviewed second controlled true run result",
        artifact_source_path="docs/example.md",
        artifact_status="reviewed_valid",
        artifact_summary="metadata-only result",
        interesting_result_summary="sparse scout buckets",
        visible_gaps=["gap"],
        blocked_actions=["source_ingestion", "final_answer"],
        recommended_next_lanes=[{
            "lane_id": "PLAN_WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_V1",
            "lane_type": "design",
            "lane_title": "Plan third controlled true run on non-materials domain",
            "why_recommended": "improve follow-up",
            "depends_on": ["reviewed_valid"],
            "owner_approval_required": False,
            "operator_review_required": True,
            "blocked_until": ["owner approval"],
            "allowed_actions": ["review"],
            "forbidden_actions": ["execute", "source_ingestion", "final_answer"],
            "validation_commands": ["git diff --check"],
            "protected_file_checks": ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
            "expected_output_artifact": "docs/out.md",
            "final_judgment_options": ["ready_for_owner_approval"],
        }],
        recommended_first_lane={
            "lane_id": "PLAN_WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_V1",
            "lane_type": "design",
            "lane_title": "Plan third controlled true run on non-materials domain",
            "why_recommended": "improve follow-up",
            "depends_on": ["reviewed_valid"],
            "owner_approval_required": False,
            "operator_review_required": True,
            "blocked_until": ["owner approval"],
            "allowed_actions": ["review"],
            "forbidden_actions": ["execute", "source_ingestion", "final_answer"],
            "validation_commands": ["git diff --check"],
            "protected_file_checks": ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
            "expected_output_artifact": "docs/out.md",
            "final_judgment_options": ["ready_for_owner_approval"],
        },
        owner_approval_required=False,
        operator_review_required=True,
        validation_plan=["git diff --check"],
        protected_file_checks=["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
        safe_metadata_summary="safe summary",
        blocked_labels=["no_execution_authority"],
        final_judgment="reviewed_valid",
    )


def test_valid_plan_builds():
    packet = _valid_packet()
    assert validate_artifact_forward_work_plan_v1(packet)


def test_required_fields_validation():
    packet = _valid_packet()
    del packet["final_judgment"]
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_weslr_path_rejected():
    packet = _valid_packet()
    packet["artifact_source_path"] = "foo/.weslr/bar"
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_all_authority_flags_false():
    packet = _valid_packet()
    assert all(v is False for v in packet["authority_status"].values())


def test_true_authority_flag_rejected():
    packet = _valid_packet()
    packet["authority_status"]["public_claim_authority"] = True
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_claim_language_rejected():
    packet = _valid_packet()
    packet["artifact_summary"] = "proof of discovery claim"
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_agi_language_rejected():
    packet = _valid_packet()
    packet["artifact_summary"] = "AGI consciousness sentience"
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_runtime_chat_ui_voice_authority_rejected():
    packet = _valid_packet()
    packet["authority_status"]["runtime_wiring_authority"] = True
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_provider_model_source_ingestion_rejected():
    packet = _valid_packet()
    packet["authority_status"]["provider_model_call_authority"] = True
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_missing_validation_plan_rejected():
    packet = _valid_packet()
    packet["validation_plan"] = []
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_missing_protected_file_checks_rejected():
    packet = _valid_packet()
    packet["protected_file_checks"] = []
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_recommended_lane_without_forbidden_actions_rejected():
    packet = _valid_packet()
    packet["recommended_next_lanes"][0]["forbidden_actions"] = []
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_recommended_lane_granting_execution_authority_rejected():
    packet = _valid_packet()
    packet["recommended_next_lanes"][0]["allowed_actions"] = ["execute"]
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_owner_approval_required_for_run_lanes():
    packet = _valid_packet()
    packet["recommended_next_lanes"][0]["lane_type"] = "run"
    packet["recommended_next_lanes"][0]["owner_approval_required"] = False
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_example_third_true_run_plan_blocked_until_owner_approval():
    examples = build_initial_artifact_forward_work_plan_examples_v1()
    packet = examples[1]
    assert packet["owner_approval_required"] is True
    assert validate_artifact_forward_work_plan_v1(packet)


def test_example_reviewed_true_run_result_recommends_third_run_plan():
    packet = build_initial_artifact_forward_work_plan_examples_v1()[0]
    assert packet["recommended_first_lane"]["lane_id"] == "PLAN_WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_V1"
    assert validate_artifact_forward_work_plan_v1(packet)


def test_oer_noop_example_recommends_design_lane_not_auto_application():
    packet = build_initial_artifact_forward_work_plan_examples_v1()[2]
    assert packet["recommended_first_lane"]["lane_type"] == "design"
    assert "ontology_auto_application" in packet["blocked_actions"]
    assert validate_artifact_forward_work_plan_v1(packet)


def test_richer_signal_shape_example_forbids_source_ingestion_snippets():
    packet = build_initial_artifact_forward_work_plan_examples_v1()[3]
    assert "source_ingestion" in packet["blocked_actions"]
    assert "snippets_as_evidence" in packet["recommended_first_lane"]["forbidden_actions"]
    assert validate_artifact_forward_work_plan_v1(packet)


def test_unsafe_example_invalid_blocked():
    packet = build_initial_artifact_forward_work_plan_examples_v1()[4]
    assert not validate_artifact_forward_work_plan_v1(packet)


def test_json_safe_copy_deterministic_and_non_mutating():
    packet = _valid_packet()
    original = deepcopy(packet)
    out = to_artifact_forward_work_plan_json_safe_v1(packet)
    assert out == to_artifact_forward_work_plan_json_safe_v1(packet)
    assert packet == original


def test_markdown_renderer_includes_required_sections():
    packet = _valid_packet()
    md = render_artifact_forward_work_plan_markdown_v1(packet)
    assert "Recommended next lane" in md
    assert "Validation plan" in md
    assert "Blocked actions" in md
    assert "Authority summary" in md


def test_markdown_renderer_excludes_raw_private_final_answer_fields():
    packet = _valid_packet()
    md = render_artifact_forward_work_plan_markdown_v1(packet)
    assert "final answer" not in md.lower()


def test_summary_safe_and_compact():
    packet = _valid_packet()
    s = summarize_artifact_forward_work_plan_v1(packet)
    assert len(s) < 200
    assert "true_run_result" in s


def test_examples_validate_except_intentionally_unsafe():
    examples = build_initial_artifact_forward_work_plan_examples_v1()
    assert validate_artifact_forward_work_plan_v1(examples[0])
    assert validate_artifact_forward_work_plan_v1(examples[1])
    assert validate_artifact_forward_work_plan_v1(examples[2])
    assert validate_artifact_forward_work_plan_v1(examples[3])
    assert not validate_artifact_forward_work_plan_v1(examples[4])
