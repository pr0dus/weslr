from __future__ import annotations

from pathlib import Path
import re

import weslr.internal_task_corpus_execution_path_helpers as helpers


REPO_ROOT = Path(__file__).resolve().parents[2]


def _build_safe_record() -> dict:
    return helpers.build_internal_task_corpus_record_v1(
        task_item={
            "task_id": "task_001",
            "task_family": "abstraction_rule_induction",
            "source_type": "synthetic_weslr_created",
            "task_prompt": "should be redacted",
            "task_labels": ["internal", "synthetic"],
            "source_tags": ["approved"],
            "unknown_engine_roles": sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1),
        },
        registry_item={
            "registry_record_id": "registry_001",
            "task_family": "abstraction_rule_induction",
            "source_type": "synthetic_weslr_created",
            "contamination_risk": "low",
            "expected_output_policy": "metadata_only",
            "answer_key_policy": "metadata_only",
            "allowed_execution_mode": "metadata_only",
        },
        session_context={
            "repo_root": str(REPO_ROOT),
            "session_key": "session-001",
        },
    )


class TestBuildAndValidateCorpusRecord:
    def test_valid_synthetic_internal_corpus_record_passes(self):
        record = _build_safe_record()
        validation = helpers.validate_internal_task_corpus_record_v1(record)

        assert validation["valid"] is True
        assert validation["blocked"] is False
        assert validation["record_status"] == "valid"
        assert validation["blocked_labels"] == []
        assert validation["task_family"] == "abstraction_rule_induction"
        assert validation["source_type"] == "synthetic_weslr_created"
        assert validation["registry_record_id"] == "registry_001"
        assert record["task_prompt_redacted_or_synthetic_descriptor"] == "[redacted:task_prompt]"
        assert "task_prompt" not in record
        assert record["official_claim_allowed"] is False
        assert record["public_claim_allowed"] is False
        assert record["runtime_authority_allowed"] is False
        assert record["voice_authority_allowed"] is False
        assert record["unknown_engine_authority_allowed"] is False

    def test_missing_required_fields_fail(self):
        validation = helpers.validate_internal_task_corpus_record_v1({})

        assert validation["valid"] is False
        assert validation["blocked"] is True
        assert "missing_task_id" in validation["blocked_labels"]
        assert "missing_task_family" in validation["blocked_labels"]
        assert "missing_source_type" in validation["blocked_labels"]
        assert "missing_registry_record_id" in validation["blocked_labels"]
        assert "missing_answer_key_policy" in validation["blocked_labels"]

    def test_unknown_task_family_and_source_fail(self):
        record = _build_safe_record()
        record["task_family"] = "mystery_family"
        record["source_type"] = "mystery_source"
        validation = helpers.validate_internal_task_corpus_record_v1(record)

        assert validation["valid"] is False
        assert "unknown_task_family" in validation["blocked_labels"]
        assert "unknown_source_type" in validation["blocked_labels"]

    def test_blocked_source_private_hidden_semi_private_fail(self):
        for source_type in ["public_open", "semi_private", "private", "hidden_blocked", "raw_private_user_data_blocked"]:
            record = _build_safe_record()
            record["source_type"] = source_type
            validation = helpers.validate_internal_task_corpus_record_v1(record)
            assert validation["valid"] is False
            assert "blocked_source_type" in validation["blocked_labels"]

    def test_raw_private_benchmark_live_user_content_fail(self):
        record = _build_safe_record()
        record["raw_private_data_requested"] = True
        record["hidden_material_requested"] = True
        record["benchmark_material_requested"] = True
        record["live_user_content_requested"] = True
        record["task_prompt"] = "raw prompt"
        validation = helpers.validate_internal_task_corpus_record_v1(record)

        assert validation["valid"] is False
        assert "raw_private_content_requested" in validation["blocked_labels"]
        assert "missing_task_prompt_descriptor" not in validation["blocked_labels"]

    def test_blocked_answer_key_policy_fails(self):
        record = _build_safe_record()
        record["answer_key_policy"] = "blocked"
        validation = helpers.validate_internal_task_corpus_record_v1(record)

        assert validation["valid"] is False
        assert "blocked_answer_key_policy" in validation["blocked_labels"]

    def test_dot_weslr_and_private_memory_request_fail(self):
        record = _build_safe_record()
        record["dot_weslr_requested"] = True
        record["private_memory_scope_requested"] = True
        validation = helpers.validate_internal_task_corpus_record_v1(record)

        assert validation["valid"] is False
        assert "dot_weslr_requested" in validation["blocked_labels"]

    def test_public_live_runtime_voice_final_answer_authority_fail(self):
        record = _build_safe_record()
        record["public_live_authority_allowed"] = True
        record["live_runtime_authority_allowed"] = True
        record["voice_authority_allowed"] = True
        record["final_answer_authority_allowed"] = True
        validation = helpers.validate_internal_task_corpus_record_v1(record)

        assert validation["valid"] is False
        assert "runtime_authority_requested" in validation["blocked_labels"]
        assert "voice_authority_requested" in validation["blocked_labels"]
        assert "final_answer_authority_requested" in validation["blocked_labels"]

    def test_official_claim_flags_fail(self):
        record = _build_safe_record()
        record["official_claim_allowed"] = True
        record["public_claim_allowed"] = True
        validation = helpers.validate_internal_task_corpus_record_v1(record)

        assert validation["valid"] is False
        assert "official_claim_requested" in validation["blocked_labels"]

    def test_unknown_engine_allowed_roles_pass_as_metadata(self):
        record = _build_safe_record()
        record["unknown_engine_roles"] = sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1)
        validation = helpers.validate_internal_task_corpus_record_v1(record)

        assert validation["valid"] is True
        assert sorted(validation["unknown_engine_roles"]) == sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1)

    def test_unknown_engine_forbidden_roles_fail(self):
        record = _build_safe_record()
        record["unknown_engine_roles"] = ["authority", "future_certainty"]
        validation = helpers.validate_internal_task_corpus_record_v1(record)

        assert validation["valid"] is False
        assert "forbidden_unknown_engine_role" in validation["blocked_labels"]


class TestExecutionPlanAndAdapterPackets:
    def test_execution_plan_is_non_executing(self):
        record = _build_safe_record()
        validation = helpers.validate_internal_task_corpus_record_v1(record)
        plan = helpers.build_internal_task_corpus_execution_plan_v1(record, validation)

        assert plan["plan_status"] == "pending_operator_review"
        assert plan["should_execute"] is False
        assert plan["execution_callable"] is None
        assert plan["controlled_execution_allowed"] is False
        assert len(plan["phases"]) == 8
        assert {phase["phase_label"] for phase in plan["phases"]} == helpers.PHASE_LABELS_V1

    def test_adapter_packet_does_not_call_anything(self):
        record = _build_safe_record()
        validation = helpers.validate_internal_task_corpus_record_v1(record)
        plan = helpers.build_internal_task_corpus_execution_plan_v1(record, validation)
        packet = helpers.build_internal_task_corpus_adapter_preflight_packet_v1(record, validation, plan)

        assert packet["packet_status"] == "pending_operator_review"
        assert packet["callable_invocation_allowed"] is False
        assert packet["live_call_allowed"] is False
        assert packet["chat_responder_call_allowed"] is False
        assert packet["model_call_allowed"] is False
        assert packet["search_call_allowed"] is False
        assert packet["advisor_call_allowed"] is False
        assert packet["execution_callable"] is None

        source = Path(helpers.__file__).read_text(encoding="utf-8")
        forbidden_patterns = [
            r"^\s*from\s+.*chat_responder\s+import",
            r"^\s*import\s+.*chat_responder",
            r"^\s*from\s+.*llm_runtime\s+import",
            r"^\s*import\s+.*llm_runtime",
            r"\bChatResponder\s*\(",
            r"\brespond_chat\s*\(",
            r"\bgenerate_chat\s*\(",
            r"^\s*import\s+subprocess",
            r"subprocess\.",
            r"requests",
            r"urllib",
            r"socket",
            r"open\(",
            r"\.weslr",
        ]
        for pattern in forbidden_patterns:
            assert re.search(pattern, source, flags=re.MULTILINE) is None

    def test_observation_redacts_raw_response_text(self):
        observation = helpers.normalize_internal_task_corpus_observation_v1(
            {
                "result_label": "pass_internal_task_corpus",
                "gap_labels": ["missing_gap_report_packet"],
                "predicted_labels": ["predicted_matches_observed"],
                "observed_labels": ["observed_matches_prediction"],
                "raw_response_text": "secret text",
                "denied_authority_flags": ["final_answer_authority_allowed"],
            }
        )

        assert observation["raw_response_text_present"] is True
        assert observation["raw_response_text_retained"] is False
        assert observation["raw_response_text_redacted"] is True
        assert observation["final_answer_authority"] is False
        assert observation["user_facing_prose_authority"] is False
        assert observation["live_runtime_authority"] is False
        assert observation["public_live_authority"] is False
        assert observation["official_claims"] is False
        assert "raw_response_text" not in observation

    def test_result_packet_metadata_only(self):
        record = _build_safe_record()
        validation = helpers.validate_internal_task_corpus_record_v1(record)
        plan = helpers.build_internal_task_corpus_execution_plan_v1(record, validation)
        observation = helpers.normalize_internal_task_corpus_observation_v1(
            {
                "result_label": "needs_operator_review",
                "gap_labels": ["missing_operator_review_packet"],
                "predicted_labels": ["predicted_matches_observed"],
                "observed_labels": ["observed_matches_prediction"],
            }
        )
        packet = helpers.build_internal_task_corpus_result_packet_v1(record, validation, plan, observation)
        summary = helpers.summarize_internal_task_corpus_execution_path_v1({"records": [validation]})

        assert packet["final_answer_authority"] is False
        assert packet["user_facing_prose_authority"] is False
        assert packet["live_runtime_authority"] is False
        assert packet["public_live_authority"] is False
        assert packet["official_claims"] is False
        assert "raw_response_text" not in packet
        assert summary["valid_records"] == 1
        assert summary["blocked_records"] == 0

    def test_batch_preserves_per_record_status(self):
        valid = _build_safe_record()
        blocked = _build_safe_record()
        blocked["source_type"] = "private"
        missing = {}
        batch = helpers.validate_internal_task_corpus_batch_v1([valid, blocked, missing])

        assert batch["total_records"] == 3
        assert batch["valid_records"] == 1
        assert batch["blocked_records"] == 2
        assert len(batch["records"]) == 3
        assert batch["records"][0]["record_status"] == "valid"
        assert batch["records"][1]["record_status"] == "blocked"
        assert batch["records"][2]["record_status"] == "blocked"
        assert "blocked_source_type" in batch["aggregate_blocked_labels"]
        assert "missing_task_id" in batch["aggregate_blocked_labels"]

    def test_json_safe_conversion_is_deterministic(self):
        value = {
            "b": 2,
            "a": {"z": {3, 1}, "y": [2, 1]},
            "c": ("x", "y"),
        }
        first = helpers.to_internal_task_corpus_execution_path_json_safe_v1(value)
        second = helpers.to_internal_task_corpus_execution_path_json_safe_v1(value)

        assert first == second
        assert list(first.keys()) == ["a", "b", "c"]
        assert first["a"]["y"] == [2, 1]
        assert first["c"] == ["x", "y"]
