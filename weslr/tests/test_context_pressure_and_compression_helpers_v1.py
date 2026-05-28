from __future__ import annotations

from pathlib import Path
import re

import weslr.context_pressure_and_compression_helpers as helpers


REPO_ROOT = Path(__file__).resolve().parents[2]


def _build_safe_case() -> dict:
    return helpers.build_context_pressure_case_v1(
        case_item={
            "case_id": "case_001",
            "case_family": "context_pressure_rehearsal",
            "source_type": "synthetic_weslr_created",
            "source_label": "redacted_metadata_only",
            "context_pressure_scenario_redacted_or_synthetic_descriptor": "[synthetic:redacted_context_chain]",
            "expected_result_label": "pass_internal_context_pressure_rehearsal",
            "expected_dimension_labels": sorted(helpers.DIMENSION_LABELS_V1),
            "expected_risk_families": sorted(helpers.RISK_FAMILY_LABELS_V1),
            "case_labels": ["internal", "synthetic"],
            "source_tags": ["approved", "metadata-only"],
            "context_tags": ["compression", "continuity"],
            "unknown_engine_roles": sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1),
        },
        registry_item={
            "registry_record_id": "registry_001",
            "case_family": "context_pressure_rehearsal",
            "source_type": "synthetic_weslr_created",
            "source_label": "redacted_metadata_only",
            "expected_result_label": "pass_internal_context_pressure_rehearsal",
            "expected_dimension_labels": sorted(helpers.DIMENSION_LABELS_V1),
            "expected_risk_families": sorted(helpers.RISK_FAMILY_LABELS_V1),
            "allowed_execution_mode": "metadata_only",
        },
        session_context={
            "repo_root": str(REPO_ROOT),
            "session_key": "session-001",
        },
    )


class TestBuildAndValidateContextPressureCase:
    def test_valid_synthetic_redacted_case_passes(self):
        case = _build_safe_case()
        validation = helpers.validate_context_pressure_case_v1(case)

        assert validation["valid"] is True
        assert validation["blocked"] is False
        assert validation["case_status"] == "valid"
        assert validation["blocked_labels"] == []
        assert validation["case_id"] == "case_001"
        assert validation["case_family"] == "context_pressure_rehearsal"
        assert validation["source_type"] == "synthetic_weslr_created"
        assert validation["registry_record_id"] == "registry_001"
        assert case["context_pressure_scenario_redacted_or_synthetic_descriptor"] == "[synthetic:redacted_context_chain]"
        assert case["official_claim_allowed"] is False
        assert case["public_claim_allowed"] is False
        assert case["runtime_authority_allowed"] is False
        assert case["voice_authority_allowed"] is False
        assert case["unknown_engine_authority_allowed"] is False

    def test_missing_required_fields_fail(self):
        validation = helpers.validate_context_pressure_case_v1({})

        assert validation["valid"] is False
        assert validation["blocked"] is True
        assert "missing_case_id" in validation["blocked_labels"]
        assert "missing_case_family" in validation["blocked_labels"]
        assert "missing_source_type" in validation["blocked_labels"]
        assert "missing_registry_record_id" in validation["blocked_labels"]
        assert "missing_context_pressure_descriptor" in validation["blocked_labels"]
        assert "missing_expected_result_label" in validation["blocked_labels"]
        assert "missing_expected_dimension_labels" in validation["blocked_labels"]
        assert "missing_expected_risk_families" in validation["blocked_labels"]

    def test_raw_private_context_and_transcript_fail(self):
        case = _build_safe_case()
        case["raw_context"] = "private context"
        case["raw_transcript"] = "private transcript"
        validation = helpers.validate_context_pressure_case_v1(case)

        assert validation["valid"] is False
        assert "raw_private_content_requested" in validation["blocked_labels"]
        assert "raw_transcript_provided" in validation["blocked_labels"]

    def test_dot_weslr_and_private_memory_request_fail(self):
        case = _build_safe_case()
        case["dot_weslr_requested"] = True
        case["private_memory_scope_requested"] = True
        validation = helpers.validate_context_pressure_case_v1(case)

        assert validation["valid"] is False
        assert "dot_weslr_requested" in validation["blocked_labels"]
        assert "private_memory_scope_requested" in validation["blocked_labels"]

    def test_live_user_chat_and_hidden_private_source_fail(self):
        case = _build_safe_case()
        case["live_user_chat_text"] = "live chat"
        validation = helpers.validate_context_pressure_case_v1(case)
        assert validation["valid"] is False
        assert "live_user_content_requested" in validation["blocked_labels"]

        for source_type in ["semi_private", "private", "hidden_blocked", "raw_private_user_data_blocked"]:
            blocked_case = _build_safe_case()
            blocked_case["source_type"] = source_type
            blocked_case["source_label"] = source_type
            blocked_validation = helpers.validate_context_pressure_case_v1(blocked_case)
            assert blocked_validation["valid"] is False
            assert any(label in blocked_validation["blocked_labels"] for label in ["blocked_source_type", "blocked_source_label"])

    def test_provider_model_output_without_approval_fails(self):
        case = _build_safe_case()
        case["provider_model_output_requested"] = True
        validation = helpers.validate_context_pressure_case_v1(case)

        assert validation["valid"] is False
        assert "provider_model_output_requested" in validation["blocked_labels"]

    def test_public_live_runtime_voice_final_answer_authority_fails(self):
        case = _build_safe_case()
        case["public_live_authority_allowed"] = True
        case["voice_authority_allowed"] = True
        case["final_answer_authority_allowed"] = True
        case["live_runtime_authority_allowed"] = True
        validation = helpers.validate_context_pressure_case_v1(case)

        assert validation["valid"] is False
        assert "public_live_authority_allowed" in validation["blocked_labels"]
        assert "voice_authority_allowed" in validation["blocked_labels"]
        assert "final_answer_authority_allowed" in validation["blocked_labels"]
        assert "live_runtime_authority_allowed" in validation["blocked_labels"]

    def test_official_turing_intelligence_claim_fail(self):
        case = _build_safe_case()
        case["official_claim_allowed"] = True
        case["public_claim_allowed"] = True
        case["turing_claim_allowed"] = True
        case["intelligence_claim_allowed"] = True
        case["certification_claim_allowed"] = True
        validation = helpers.validate_context_pressure_case_v1(case)

        assert validation["valid"] is False
        assert "official_claim_allowed" in validation["blocked_labels"]
        assert "public_claim_allowed" in validation["blocked_labels"]
        assert "turing_claim_allowed" in validation["blocked_labels"]
        assert "intelligence_claim_allowed" in validation["blocked_labels"]
        assert "certification_claim_allowed" in validation["blocked_labels"]

    def test_unknown_engine_allowed_roles_pass_as_metadata(self):
        case = _build_safe_case()
        case["unknown_engine_roles"] = sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1)
        validation = helpers.validate_context_pressure_case_v1(case)

        assert validation["valid"] is True
        assert sorted(validation["unknown_engine_roles"]) == sorted(helpers.ALLOWED_UNKNOWN_ENGINE_ROLES_V1)

    def test_unknown_engine_forbidden_roles_fail(self):
        case = _build_safe_case()
        case["unknown_engine_roles"] = ["authority", "official_turing_judge"]
        validation = helpers.validate_context_pressure_case_v1(case)

        assert validation["valid"] is False
        assert "forbidden_unknown_engine_role" in validation["blocked_labels"]

    def test_unknown_risk_family_dimension_and_result_label_fail_closed(self):
        case = _build_safe_case()
        case["expected_risk_families"] = ["meaning_compression_loss", "mystery_risk"]
        case["expected_dimension_labels"] = ["meaning_retention", "mystery_dimension"]
        case["expected_result_label"] = "mystery_result"
        validation = helpers.validate_context_pressure_case_v1(case)

        assert validation["valid"] is False
        assert "unknown_risk_family" in validation["blocked_labels"]
        assert "unknown_dimension_label" in validation["blocked_labels"]
        assert "unknown_expected_result_label" in validation["blocked_labels"]


class TestPlanObservationAndPacket:
    def test_plan_is_non_executing(self):
        case = _build_safe_case()
        validation = helpers.validate_context_pressure_case_v1(case)
        plan = helpers.build_context_pressure_evaluation_plan_v1(case, validation)

        assert plan["plan_status"] == "pending_operator_review"
        assert plan["should_execute"] is False
        assert plan["execution_callable"] is None
        assert plan["controlled_execution_allowed"] is False
        assert plan["operator_review_required"] is True
        assert len(plan["phases"]) >= 4

    def test_observation_redacts_raw_context_transcript_and_response_text(self):
        observation = helpers.normalize_context_pressure_observation_v1(
            {
                "result_label": "pass_internal_context_pressure_rehearsal",
                "dimension_labels": ["meaning_retention", "continuity_retention"],
                "risk_family_labels": ["meaning_compression_loss"],
                "gap_labels": ["missing_safe_compression_behavior"],
                "predicted_labels": ["predicted_matches_observed"],
                "observed_labels": ["observed_matches_prediction"],
                "raw_context": "secret context",
                "raw_transcript": "secret transcript",
                "raw_response_text": "secret response",
                "denied_authority_flags": ["final_answer_authority"],
            }
        )

        assert observation["raw_context_present"] is True
        assert observation["raw_context_retained"] is False
        assert observation["raw_context_redacted"] is True
        assert observation["raw_transcript_present"] is True
        assert observation["raw_transcript_retained"] is False
        assert observation["raw_transcript_redacted"] is True
        assert observation["raw_response_text_present"] is True
        assert observation["raw_response_text_retained"] is False
        assert observation["raw_response_text_redacted"] is True
        assert observation["final_answer_authority"] is False
        assert observation["user_facing_prose_authority"] is False
        assert observation["live_runtime_authority"] is False
        assert observation["public_live_authority"] is False
        assert observation["official_claims"] is False
        assert "raw_context" not in observation
        assert "raw_transcript" not in observation
        assert "raw_response_text" not in observation

    def test_result_packet_metadata_only(self):
        case = _build_safe_case()
        validation = helpers.validate_context_pressure_case_v1(case)
        plan = helpers.build_context_pressure_evaluation_plan_v1(case, validation)
        observation = helpers.normalize_context_pressure_observation_v1(
            {
                "result_label": "needs_operator_review",
                "dimension_labels": ["meaning_retention"],
                "risk_family_labels": ["meaning_compression_loss"],
                "gap_labels": ["missing_safe_compression_behavior"],
                "predicted_labels": ["predicted_matches_observed"],
                "observed_labels": ["observed_matches_prediction"],
            }
        )
        packet = helpers.build_context_pressure_result_packet_v1(case, validation, plan, observation)
        summary = helpers.summarize_context_pressure_batch_v1({"records": [validation]})

        assert packet["final_answer_authority"] is False
        assert packet["user_facing_prose_authority"] is False
        assert packet["live_runtime_authority"] is False
        assert packet["public_live_authority"] is False
        assert packet["official_claims"] is False
        assert packet["operator_review_required"] is True
        assert summary["valid_records"] == 1
        assert summary["blocked_records"] == 0
        assert "raw_context" not in packet
        assert "raw_transcript" not in packet
        assert "raw_response_text" not in packet
        assert len(packet["observations"]) == 1

    def test_batch_preserves_per_case_status(self):
        valid = _build_safe_case()
        blocked = _build_safe_case()
        blocked["source_type"] = "private"
        blocked["source_label"] = "private"
        missing = {}
        batch = helpers.validate_context_pressure_batch_v1([valid, blocked, missing])

        assert batch["total_records"] == 3
        assert batch["valid_records"] == 1
        assert batch["blocked_records"] == 2
        assert len(batch["records"]) == 3
        assert batch["records"][0]["case_status"] == "valid"
        assert batch["records"][1]["case_status"] == "blocked"
        assert batch["records"][2]["case_status"] == "blocked"
        assert "blocked_source_type" in batch["aggregate_blocked_labels"]
        assert "missing_case_id" in batch["aggregate_blocked_labels"]

    def test_summary_is_counts_and_status_only(self):
        valid = _build_safe_case()
        blocked = _build_safe_case()
        blocked["source_type"] = "private"
        summary = helpers.summarize_context_pressure_batch_v1([valid, blocked])

        assert summary["total_records"] == 2
        assert summary["valid_records"] == 1
        assert summary["blocked_records"] == 1
        assert summary["case_status_counts"]["valid"] == 1
        assert summary["case_status_counts"]["blocked"] == 1
        assert summary["plan_status_counts"]["blocked"] == 1

    def test_json_safe_conversion_is_deterministic(self):
        value = {
            "b": 2,
            "a": {"z": {3, 1}, "y": [2, 1]},
            "c": ("x", "y"),
        }
        first = helpers.to_context_pressure_json_safe_v1(value)
        second = helpers.to_context_pressure_json_safe_v1(value)

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
            r"requests",
            r"urllib",
            r"socket",
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
