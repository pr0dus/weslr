from __future__ import annotations

from pathlib import Path
import re

import weslr.real_response_executor_adapter_helpers as helpers


REPO_ROOT = Path(__file__).resolve().parents[2]


def _build_safe_request() -> dict:
    return helpers.build_real_response_executor_adapter_request_v1(
        task_item={
            "task_id": "task_001",
            "task_family": "ordinary_task_behavior",
            "source_class": "synthetic_weslr_created",
            "source_label": "synthetic_weslr_created",
            "task_labels": ["internal", "synthetic"],
            "source_tags": ["approved", "metadata-only"],
            "raw_text": "should be dropped",
            "final_answer": "should be dropped",
        },
        registry_item={
            "registry_id": "registry_001",
            "task_family": "ordinary_task_behavior",
            "source_class": "synthetic_weslr_created",
            "source_label": "synthetic_weslr_created",
            "source_tags": ["registry-tag"],
        },
        session_context={
            "repo_root": str(REPO_ROOT),
            "session_key": "session-001",
        },
    )


class TestRequestBuilder:
    def test_safe_synthetic_internal_request_passes(self):
        request = _build_safe_request()
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)

        assert preflight["allowed"] is True
        assert preflight["blocked"] is False
        assert preflight["preflight_status"] == helpers.PLAN_STATUS_ALLOWED_PENDING_OPERATOR_REVIEW_V1
        assert preflight["block_reason_labels"] == []
        assert preflight["task_family"] == "ordinary_task_behavior"
        assert preflight["source_class"] == "synthetic_weslr_created"
        assert preflight["source_label"] == "synthetic_weslr_created"
        assert preflight["registry_id"] == "registry_001"
        assert preflight["repo_root"] == str(REPO_ROOT)
        assert preflight["session_key"] == "session-001"
        assert preflight["final_answer_authority"] is False
        assert preflight["user_facing_prose_authority"] is False
        assert preflight["live_runtime_authority"] is False
        assert preflight["public_live_authority"] is False
        assert preflight["official_claims"] is False

        assert "raw_text" not in request["task_metadata"]
        assert "final_answer" not in request["task_metadata"]

    def test_missing_registry_source_metadata_fails(self):
        request = {
            "helper_type": helpers.HELPER_TYPE_V1,
            "boundary_type": helpers.BOUNDARY_TYPE_V1,
            "request_type": helpers.REQUEST_TYPE_V1,
            "task_metadata": {},
            "session_context": {"repo_root": str(REPO_ROOT), "session_key": "session-001"},
            "denied_authority_flags": list(helpers.DENIED_AUTHORITY_FLAGS_V1),
            "unknown_engine_roles": [],
            "authority": {},
            "raw_response_storage_requested": False,
            "feature_flag_enabled": False,
        }
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)

        assert preflight["allowed"] is False
        assert preflight["blocked"] is True
        assert "task_family_not_allowed" in preflight["block_reason_labels"]
        assert "source_class_missing" in preflight["block_reason_labels"]
        assert "source_label_missing" in preflight["block_reason_labels"]
        assert "registry_id_missing" in preflight["block_reason_labels"]
        assert "registry_metadata_missing" in preflight["block_reason_labels"]

    def test_blocked_source_fails(self):
        request = helpers.build_real_response_executor_adapter_request_v1(
            {"task_family": "ordinary_task_behavior", "source_class": "public_open", "source_label": "public_open"},
            {"registry_id": "registry_001", "task_family": "ordinary_task_behavior", "source_class": "public_open", "source_label": "public_open"},
            {"repo_root": str(REPO_ROOT), "session_key": "session-001"},
        )
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)

        assert preflight["allowed"] is False
        assert "blocked_source_label" in preflight["block_reason_labels"]

    def test_private_memory_and_dot_weslr_request_fails(self):
        request = _build_safe_request()
        request["task_metadata"]["requires_private_memory"] = True
        request["task_metadata"]["requires_dot_weslr"] = True
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)

        assert preflight["allowed"] is False
        assert "private_memory_requested" in preflight["block_reason_labels"]
        assert "dot_weslr_requested" in preflight["block_reason_labels"]

    def test_public_live_voice_and_final_answer_authority_fails(self):
        request = _build_safe_request()
        request["public_live_authority"] = True
        request["voice_authority"] = True
        request["final_answer_authority"] = True
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)

        assert preflight["allowed"] is False
        assert "public_live_voice_authority_requested" in preflight["block_reason_labels"]
        assert "final_answer_authority_requested" in preflight["block_reason_labels"]

    def test_official_claim_and_feature_flag_fails(self):
        request = _build_safe_request()
        request["official_claims"] = True
        request["feature_flag_enabled"] = True
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)

        assert preflight["allowed"] is False
        assert "official_claim_requested" in preflight["block_reason_labels"]
        assert "feature_flag_enabled" in preflight["block_reason_labels"]

    def test_raw_response_storage_request_fails(self):
        request = _build_safe_request()
        request["raw_response_storage_requested"] = True
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)

        assert preflight["allowed"] is False
        assert "raw_persistence_requested" in preflight["block_reason_labels"]

    def test_unknown_engine_allowed_roles_pass_as_metadata(self):
        request = _build_safe_request()
        request["unknown_engine_roles"] = sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1)
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)

        assert preflight["allowed"] is True
        assert sorted(preflight["unknown_engine_roles"]) == sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1)

    def test_unknown_engine_forbidden_roles_fail(self):
        request = _build_safe_request()
        request["unknown_engine_roles"] = ["authority", "future_certainty"]
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)

        assert preflight["allowed"] is False
        assert "unknown_engine_authority_requested" in preflight["block_reason_labels"]

    def test_unknown_task_source_and_result_labels_fail_closed(self):
        request = _build_safe_request()
        request["task_metadata"]["task_family"] = "mystery_family"
        request["task_metadata"]["source_class"] = "mystery_source"
        request["task_metadata"]["source_label"] = "mystery_source"
        request["result_label"] = "mystery_result"
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)

        assert preflight["allowed"] is False
        assert "task_family_not_allowed" in preflight["block_reason_labels"]
        assert "source_class_not_allowed" in preflight["block_reason_labels"]

    def test_no_file_network_subprocess_provider_or_dot_weslr_behavior(self):
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


class TestCallPlanAndObservation:
    def test_call_plan_does_not_execute_anything(self):
        request = _build_safe_request()
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)
        plan = helpers.build_real_response_executor_adapter_call_plan_v1(request, preflight)

        assert plan["plan_status"] == helpers.PLAN_STATUS_ALLOWED_PENDING_OPERATOR_REVIEW_V1
        assert plan["callable_invocation_allowed"] is False
        assert plan["live_call_allowed"] is False
        assert plan["chat_responder_call_allowed"] is False
        assert plan["model_call_allowed"] is False
        assert plan["search_call_allowed"] is False
        assert plan["advisor_call_allowed"] is False
        assert plan["execution_callable"] is None
        assert plan["should_execute"] is False
        assert plan["operator_review_required"] is True

    def test_call_plan_blocks_when_preflight_blocks(self):
        request = _build_safe_request()
        request["feature_flag_enabled"] = True
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)
        plan = helpers.build_real_response_executor_adapter_call_plan_v1(request, preflight)

        assert plan["plan_status"] == helpers.PLAN_STATUS_BLOCKED_V1
        assert plan["should_execute"] is False
        assert plan["blocked_reason_labels"]

    def test_observation_rejects_redacts_raw_response_text(self):
        observation = helpers.normalize_real_response_executor_adapter_observation_v1(
            {
                "result_label": helpers.OBSERVATION_LABEL_PASS_V1,
                "gap_labels": ["missing_executor_adapter_boundary"],
                "predicted_labels": ["predicted_matches_observed"],
                "observed_labels": ["observed_matches_prediction"],
                "raw_response_text": "secret response text",
                "denied_authority_flags": ["final_answer_authority"],
            }
        )

        assert observation["raw_response_text_present"] is True
        assert observation["raw_response_text_retained"] is False
        assert observation["raw_response_text_redacted"] is True
        assert observation["blocked_reason_labels"]
        assert observation["result_label"] == helpers.OBSERVATION_LABEL_PASS_V1
        assert "raw_response_text" not in observation

    def test_result_packet_is_metadata_only(self):
        request = _build_safe_request()
        preflight = helpers.validate_real_response_executor_adapter_preflight_v1(request)
        plan = helpers.build_real_response_executor_adapter_call_plan_v1(request, preflight)
        observation = helpers.normalize_real_response_executor_adapter_observation_v1(
            {
                "result_label": helpers.OBSERVATION_LABEL_NEEDS_REVIEW_V1,
                "gap_labels": ["missing_operator_review_packet"],
                "predicted_labels": ["predicted_matches_observed"],
                "observed_labels": ["observed_matches_prediction"],
            }
        )
        packet = helpers.build_real_response_executor_adapter_result_packet_v1(request, preflight, plan, observation)
        summary = helpers.summarize_real_response_executor_adapter_v1(packet)

        assert packet["final_answer_authority"] is False
        assert packet["user_facing_prose_authority"] is False
        assert packet["live_runtime_authority"] is False
        assert packet["public_live_authority"] is False
        assert packet["official_claims"] is False
        assert "raw_response_text" not in packet
        assert summary["blocked_reason_count"] == len(packet["blocked_reason_labels"])
        assert summary["final_answer_authority"] is False
        assert summary["official_claims"] is False

    def test_json_safe_conversion_is_deterministic(self):
        value = {
            "b": 2,
            "a": {"z": {3, 1}, "y": [2, 1]},
            "c": ("x", "y"),
        }
        first = helpers.to_real_response_executor_adapter_json_safe_v1(value)
        second = helpers.to_real_response_executor_adapter_json_safe_v1(value)

        assert first == second
        assert list(first.keys()) == ["a", "b", "c"]
        assert first["a"]["z"] in ([1, 3], [3, 1])
        assert first["c"] == ["x", "y"]

    def test_invalid_observation_labels_fail_closed(self):
        observation = helpers.normalize_real_response_executor_adapter_observation_v1(
            {
                "result_label": "mystery_result",
                "gap_labels": ["mystery_gap"],
                "predicted_labels": ["mystery_predicted"],
                "observed_labels": ["mystery_observed"],
            }
        )

        assert observation["observation_status"] == helpers.OBSERVATION_LABEL_BLOCKED_V1
        assert "unknown_result_label" in observation["blocked_reason_labels"]
        assert "unknown_gap_label" in observation["blocked_reason_labels"]
        assert "unknown_predicted_label" in observation["blocked_reason_labels"]
        assert "unknown_observed_label" in observation["blocked_reason_labels"]
