from __future__ import annotations

from pathlib import Path
import re

import weslr.internal_task_corpus_controlled_execution_helpers as helpers


REPO_ROOT = Path(__file__).resolve().parents[2]


def _build_safe_request(source_class: str = "synthetic_weslr_created") -> dict:
    return helpers.build_internal_task_corpus_controlled_execution_request_v1(
        task_item={
            "task_id": "task_001",
            "task_family": "internal_task_corpus_rehearsal",
            "source_class": source_class,
            "source_label": "redacted_metadata_only" if source_class != "public_open" else "public_open",
            "registry_record_id": "registry_001",
            "task_prompt_redacted_or_synthetic_descriptor": "[synthetic:approved_task_corpus]",
            "task_labels": ["internal", "synthetic"],
            "source_tags": ["approved", "metadata-only"],
            "registry_approved": True,
            "execution_plan_preflight_passed": True,
            "adapter_preflight_passed": True,
            "operator_approval_required": True,
            "operator_approval_present": True,
            "result_artifact_metadata_only": True,
            "unknown_engine_roles": sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1),
        },
        registry_item={
            "registry_record_id": "registry_001",
            "task_family": "internal_task_corpus_rehearsal",
            "source_class": source_class,
            "source_label": "redacted_metadata_only" if source_class != "public_open" else "public_open",
            "registry_approved": True,
            "execution_plan_preflight_passed": True,
            "adapter_preflight_passed": True,
            "operator_approval_required": True,
            "operator_approval_present": True,
            "result_artifact_metadata_only": True,
            "unknown_engine_roles": sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1),
        },
        session_context={
            "repo_root": str(REPO_ROOT),
            "session_key": "session-001",
        },
    )


class TestControlledExecutionRequestAndPreflight:
    def test_valid_synthetic_controlled_execution_request_passes(self):
        request = _build_safe_request("synthetic_weslr_created")
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is True
        assert preflight["blocked"] is False
        assert preflight["request_status"] == "valid"
        assert preflight["blocked_labels"] == []
        assert preflight["source_class"] == "synthetic_weslr_created"
        assert request["source_metadata"]["registry_approved"] is True
        assert request["execution_gate"]["execution_plan_preflight_passed"] is True
        assert request["execution_gate"]["adapter_preflight_passed"] is True

    def test_valid_public_open_controlled_execution_request_passes(self):
        request = _build_safe_request("public_open")
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is True
        assert preflight["blocked"] is False
        assert preflight["source_class"] == "public_open"

    def test_missing_registry_approval_fails(self):
        request = _build_safe_request()
        request["source_metadata"]["registry_approved"] = False
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is False
        assert preflight["blocked"] is True
        assert "missing_registry_approval" in preflight["blocked_labels"]
        assert "source_registry_not_approved" in preflight["blocked_labels"]

    def test_blocked_source_classes_fail(self):
        for source_class in ["private", "semi_private", "hidden", "unknown"]:
            request = _build_safe_request(source_class)
            preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)
            assert preflight["valid"] is False
            assert any(label in preflight["blocked_labels"] for label in ["blocked_source_class", "unknown_source_class"])

    def test_missing_execution_preflight_fails(self):
        request = _build_safe_request()
        request["execution_gate"]["execution_plan_preflight_passed"] = False
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is False
        assert "missing_execution_plan_preflight" in preflight["blocked_labels"]

    def test_missing_adapter_preflight_fails(self):
        request = _build_safe_request()
        request["execution_gate"]["adapter_preflight_passed"] = False
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is False
        assert "missing_adapter_preflight" in preflight["blocked_labels"]

    def test_raw_private_data_fails(self):
        request = _build_safe_request()
        request["raw_private_data_requested"] = True
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is False
        assert "raw_private_data_requested" in preflight["blocked_labels"]

    def test_raw_prompt_response_transcript_context_rejected_or_redacted(self):
        request = helpers.build_internal_task_corpus_controlled_execution_request_v1(
            task_item={
                "task_id": "task_002",
                "task_family": "internal_task_corpus_rehearsal",
                "source_class": "synthetic_weslr_created",
                "registry_record_id": "registry_002",
                "registry_approved": True,
                "execution_plan_preflight_passed": True,
                "adapter_preflight_passed": True,
                "operator_approval_present": True,
                "task_prompt": "raw prompt text",
                "raw_response_text": "raw response text",
                "raw_transcript": "raw transcript text",
                "raw_context": "raw context text",
            },
            registry_item={
                "registry_record_id": "registry_002",
                "task_family": "internal_task_corpus_rehearsal",
                "source_class": "synthetic_weslr_created",
                "registry_approved": True,
                "execution_plan_preflight_passed": True,
                "adapter_preflight_passed": True,
                "operator_approval_present": True,
            },
            session_context={"repo_root": str(REPO_ROOT), "session_key": "session-raw"},
        )

        task_metadata = request["task_metadata"]
        assert "raw prompt text" not in str(request)
        assert "raw response text" not in str(request)
        assert "raw transcript text" not in str(request)
        assert "raw context text" not in str(request)
        assert task_metadata["task_prompt_redacted_or_synthetic_descriptor"] == "[redacted:internal_task_corpus_controlled_execution_request]"

        observation = helpers.normalize_internal_task_corpus_controlled_execution_observation_v1(
            {
                "result_label": "pass_internal_task_rehearsal",
                "raw_prompt": "prompt secret",
                "raw_response_text": "response secret",
                "raw_transcript": "transcript secret",
                "raw_context": "context secret",
                "gap_labels": ["missing_safe_metadata"],
            }
        )

        assert observation["raw_prompt_present"] is True
        assert observation["raw_prompt_retained"] is False
        assert observation["raw_prompt_redacted"] is True
        assert observation["raw_response_text_present"] is True
        assert observation["raw_response_text_retained"] is False
        assert observation["raw_response_text_redacted"] is True
        assert observation["raw_transcript_present"] is True
        assert observation["raw_transcript_retained"] is False
        assert observation["raw_transcript_redacted"] is True
        assert observation["raw_context_present"] is True
        assert observation["raw_context_retained"] is False
        assert observation["raw_context_redacted"] is True
        assert "raw_prompt_provided" in observation["blocked_labels"]
        assert "raw_response_text_provided" in observation["blocked_labels"]
        assert "raw_transcript_provided" in observation["blocked_labels"]
        assert "raw_context_provided" in observation["blocked_labels"]
        assert "prompt secret" not in str(observation)

    def test_dot_weslr_and_private_memory_request_fails(self):
        request = _build_safe_request()
        request["dot_weslr_requested"] = True
        request["private_memory_scope_requested"] = True
        request["private_memory_requested"] = True
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is False
        assert "dot_weslr_requested" in preflight["blocked_labels"]
        assert "private_memory_scope_requested" in preflight["blocked_labels"]
        assert "private_memory_requested" in preflight["blocked_labels"]

    def test_live_user_chat_fails(self):
        request = _build_safe_request()
        request["live_user_content_requested"] = True
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is False
        assert "live_user_content_requested" in preflight["blocked_labels"]

    def test_unapproved_provider_model_output_fails(self):
        request = _build_safe_request()
        request["provider_model_output_requested"] = True
        request["model_call_authority_requested"] = True
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is False
        assert "provider_model_output_requested" in preflight["blocked_labels"]
        assert "model_call_authority_requested" in preflight["blocked_labels"]

    def test_public_live_voice_final_answer_authority_fails(self):
        request = _build_safe_request()
        request["public_live_authority_requested"] = True
        request["public_ux_authority_requested"] = True
        request["voice_authority_requested"] = True
        request["final_answer_authority_requested"] = True
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is False
        assert "public_live_authority_requested" in preflight["blocked_labels"]
        assert "public_ux_authority_requested" in preflight["blocked_labels"]
        assert "voice_authority_requested" in preflight["blocked_labels"]
        assert "final_answer_authority_requested" in preflight["blocked_labels"]

    def test_official_turing_intelligence_certification_claim_fails(self):
        request = _build_safe_request()
        request["official_claim_requested"] = True
        request["benchmark_submission_requested"] = True
        request["turing_claim_requested"] = True
        request["intelligence_claim_requested"] = True
        request["certification_claim_requested"] = True
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is False
        assert "official_claim_requested" in preflight["blocked_labels"]
        assert "benchmark_submission_requested" in preflight["blocked_labels"]
        assert "turing_claim_requested" in preflight["blocked_labels"]
        assert "intelligence_claim_requested" in preflight["blocked_labels"]
        assert "certification_claim_requested" in preflight["blocked_labels"]

    def test_unknown_engine_allowed_roles_pass_as_metadata(self):
        request = _build_safe_request()
        request["unknown_engine_roles"] = sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1)
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is True
        assert sorted(preflight["unknown_engine_roles"]) == sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1)

    def test_unknown_engine_forbidden_roles_fail(self):
        request = _build_safe_request()
        request["unknown_engine_roles"] = ["authority", "official judge"]
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is False
        assert "forbidden_unknown_engine_role" in preflight["blocked_labels"]

    def test_unknown_result_label_and_source_class_fail(self):
        request = _build_safe_request()
        request["task_metadata"]["source_class"] = "mystery"
        request["source_metadata"]["source_class"] = "mystery"
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)

        assert preflight["valid"] is False
        assert "unknown_source_class" in preflight["blocked_labels"]

        observation = helpers.normalize_internal_task_corpus_controlled_execution_observation_v1(
            {"result_label": "mystery_result", "gap_labels": ["mystery_gap"]}
        )
        assert observation["result_label"] == "needs_operator_review"
        assert observation["observation_status"] == "blocked_by_runtime_boundary"
        assert "unknown_result_label" in observation["blocked_labels"]


class TestPlanResultPacketBatchAndSummary:
    def test_plan_is_non_executing(self):
        request = _build_safe_request()
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)
        plan = helpers.build_internal_task_corpus_controlled_execution_plan_v1(request, preflight)

        assert plan["plan_status"] == "pending_operator_review"
        assert plan["should_execute"] is False
        assert plan["execution_callable"] is None
        assert plan["controlled_execution_allowed"] is False
        assert plan["operator_review_required"] is True
        assert len(plan["phases"]) >= 5

    def test_result_packet_metadata_only(self):
        request = _build_safe_request()
        preflight = helpers.validate_internal_task_corpus_controlled_execution_preflight_v1(request)
        plan = helpers.build_internal_task_corpus_controlled_execution_plan_v1(request, preflight)
        observation = helpers.normalize_internal_task_corpus_controlled_execution_observation_v1(
            {
                "result_label": "needs_operator_review",
                "gap_labels": ["missing_safe_metadata"],
                "predicted_labels": ["predicted_matches_observed"],
                "observed_labels": ["observed_matches_prediction"],
            }
        )
        packet = helpers.build_internal_task_corpus_controlled_execution_result_packet_v1(request, preflight, plan, observation)

        assert packet["final_answer_authority"] is False
        assert packet["user_facing_prose_authority"] is False
        assert packet["live_runtime_authority"] is False
        assert packet["public_live_authority"] is False
        assert packet["official_claims"] is False
        assert packet["operator_review_required"] is True
        assert "raw_prompt" not in str(packet)
        assert "raw_response_text" not in str(packet)
        assert "raw_transcript" not in str(packet)
        assert "raw_context" not in str(packet)
        assert packet["request"]["task_metadata"]["task_id"] == "task_001"

    def test_batch_preserves_per_case_status(self):
        valid = _build_safe_request()
        blocked = _build_safe_request()
        blocked["source_metadata"]["registry_approved"] = False
        missing = {"request": {}}
        batch = helpers.validate_internal_task_corpus_controlled_execution_batch_v1([valid, blocked, missing])

        assert batch["total_records"] == 3
        assert batch["valid_records"] == 1
        assert batch["blocked_records"] == 2
        assert len(batch["records"]) == 3
        assert batch["records"][0]["request_status"] == "valid"
        assert batch["records"][1]["request_status"] == "blocked"
        assert batch["records"][2]["request_status"] == "blocked"
        assert "missing_registry_approval" in batch["aggregate_blocked_labels"]
        assert "missing_task_id" in batch["aggregate_blocked_labels"]

    def test_summary_is_counts_and_status_only(self):
        valid = _build_safe_request()
        blocked = _build_safe_request()
        blocked["source_metadata"]["registry_approved"] = False
        summary = helpers.summarize_internal_task_corpus_controlled_execution_v1([valid, blocked])

        assert summary["total_records"] == 2
        assert summary["valid_records"] == 1
        assert summary["blocked_records"] == 1
        assert summary["record_status_counts"]["valid"] == 1
        assert summary["record_status_counts"]["blocked"] == 1
        assert summary["plan_status_counts"]["pending_operator_review"] == 1

    def test_json_safe_conversion_is_deterministic(self):
        value = {
            "b": 2,
            "a": {"z": {3, 1}, "y": [2, 1]},
            "c": ("x", "y"),
        }
        first = helpers.to_internal_task_corpus_controlled_execution_json_safe_v1(value)
        second = helpers.to_internal_task_corpus_controlled_execution_json_safe_v1(value)

        assert first == second
        assert list(first.keys()) == ["a", "b", "c"]
        assert first["a"]["z"] == [1, 3]
        assert first["c"] == ["x", "y"]

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
            r"^\s*import\s+requests\b",
            r"^\s*from\s+requests\b",
            r"requests\.",
            r"^\s*import\s+urllib\b",
            r"^\s*from\s+urllib\b",
            r"urllib\.",
            r"^\s*import\s+socket\b",
            r"^\s*from\s+socket\b",
            r"socket\.",
            r"\.weslr",
        ]
        for pattern in forbidden_patterns:
            assert re.search(pattern, source, flags=re.MULTILINE) is None

    def test_no_chat_responder_or_main_reference_in_module_source(self):
        source = Path(helpers.__file__).read_text(encoding="utf-8")
        assert re.search(r"^\s*from\s+.*chat_responder\s+import", source, flags=re.MULTILINE) is None
        assert re.search(r"^\s*import\s+.*chat_responder", source, flags=re.MULTILINE) is None
        assert re.search(r"\bChatResponder\s*\(", source) is None
        assert re.search(r"\brespond_chat\s*\(", source) is None
        assert re.search(r"\bgenerate_chat\s*\(", source) is None
        assert "main.py" not in source
