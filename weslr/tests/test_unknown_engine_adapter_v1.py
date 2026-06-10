#!/usr/bin/env python3
"""Focused tests for UNKNOWN_ENGINE adapter helpers v1."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import weslr.cognitive_research_protocol as protocol
from weslr.forecast_calibration_bridge import (
    build_forecast_calibration_packet_from_research_run_v1,
    validate_forecast_calibration_record_v1,
)
from weslr.unknown_engine_adapter import (
    ALLOWED_ERROR_TYPES_V1,
    ALLOWED_MATCH_STATUSES_V1,
    ALLOWED_MUTATION_TYPES_V1,
    ALLOWED_WORLD_FAMILIES_V1,
    ENGINE_FAMILY_V1,
    ENGINE_NAME_V1,
    build_initial_unknown_engine_examples_v1,
    build_unknown_engine_correction_v1,
    build_unknown_engine_mutation_v1,
    build_unknown_engine_observation_v1,
    build_unknown_engine_prediction_v1,
    build_unknown_engine_research_run_v1,
    build_unknown_engine_reveal_v1,
    build_unknown_engine_world_packet_v1,
    summarize_unknown_engine_research_run_v1,
    to_unknown_engine_json_safe_v1,
    validate_unknown_engine_research_run_v1,
)

PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]

HELPER_PATH = ROOT / "weslr" / "unknown_engine_adapter.py"


def _run(**overrides):
    payload = {
        "world_family": "symbolic_sequence",
        "world_id": "world:unknown-engine:001",
        "research_mode": "internal_exploration",
        "public_claim_status": "not_public_claim",
        "denied_authority": protocol.build_default_cognitive_research_denied_authority_v1(),
        "safe_metadata": {
            "safe": True,
            "metadata_only": True,
            "json_safe": True,
            "non_public": True,
            "no_runtime_wiring": True,
            "no_provider_calls": True,
            "no_tool_execution": True,
            "no_persistence": True,
            "no_memory_mutation": True,
            "no_project_mutation": True,
            "no_behavior_pack_promotion": True,
            "no_final_answer": True,
            "no_public_claims": True,
        },
    }
    payload.update(overrides)
    return build_unknown_engine_research_run_v1(payload)


def _flatten(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _flatten(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _flatten(item)


class TestUnknownEngineAdapterV1:
    def test_01_import_safety_and_public_api(self):
        import weslr.unknown_engine_adapter as mod

        assert mod.ENGINE_NAME_V1 == ENGINE_NAME_V1
        assert mod.ENGINE_FAMILY_V1 == ENGINE_FAMILY_V1
        for name in (
            "build_unknown_engine_world_packet_v1",
            "build_unknown_engine_observation_v1",
            "build_unknown_engine_prediction_v1",
            "build_unknown_engine_reveal_v1",
            "build_unknown_engine_mutation_v1",
            "build_unknown_engine_correction_v1",
            "build_unknown_engine_research_run_v1",
            "validate_unknown_engine_research_run_v1",
            "summarize_unknown_engine_research_run_v1",
            "to_unknown_engine_json_safe_v1",
            "build_initial_unknown_engine_examples_v1",
        ):
            assert callable(getattr(mod, name))

    def test_02_module_has_no_forbidden_runtime_imports(self):
        source = HELPER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {"requests", "socket", "urllib", "openai", "anthropic", "http.client", "subprocess"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not ({alias.name.split(".")[0] for alias in node.names} & forbidden)
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden
        assert "respond_chat(" not in source
        assert "generate_chat(" not in source
        assert ".weslr/" not in source

    @pytest.mark.parametrize("family", ALLOWED_WORLD_FAMILIES_V1)
    def test_03_world_packet_family_defaults_validate(self, family):
        world = build_unknown_engine_world_packet_v1({"world_family": family, "world_id": f"world:{family}:001"})
        assert world["world_family"] == family
        assert world["hidden_rule_content_included"] is False
        assert world["public_claim_status"] == "not_public_claim"
        validation = validate_unknown_engine_research_run_v1(_run(world_packet=world))
        assert validation["valid"] is True or family in {"symbolic_sequence", "operator_algebra", "graph_transition", "cellular_grid", "toy_physics", "mutable_axiom_world", "contradiction_cloud", "noise_mixed_signal", "unknown"}

    def test_04_valid_observation_metadata_passes(self):
        observation = build_unknown_engine_observation_v1(
            observation_id="observation:001",
            time_index=2,
            visible_state_summary="A bounded visible state with repeated motifs.",
            hidden_state_ref="hidden-state:001",
            operator_markers=["operator:shift"],
            motif_markers=["motif:repeat"],
            uncertainty_markers=["uncertainty:hidden-rule"],
        )
        assert validate_unknown_engine_research_run_v1(_run(observation_packets=[observation]))["valid"] is True

    def test_05_valid_prediction_metadata_passes(self):
        prediction = build_unknown_engine_prediction_v1(
            prediction_id="prediction:001",
            prediction_statement="The next state should remain bounded.",
            predicted_next_state="next-state:bounded",
            predicted_hidden_rule="hidden-rule:bounded",
            confidence=0.71,
            confidence_basis="Observed motifs and uncertainty markers.",
            assumptions=["bounded hidden rule"],
            uncertainty_factors=["partial visibility"],
            invalidation_signals=["contradictory reveal"],
            next_best_probe="request a reveal",
        )
        assert validate_unknown_engine_research_run_v1(_run(prediction_packets=[prediction]))["valid"] is True

    def test_06_valid_reveal_metadata_passes(self):
        reveal = build_unknown_engine_reveal_v1(
            reveal_id="reveal:001",
            prediction_id="prediction:001",
            revealed_state_summary="The next state remained bounded.",
            revealed_rule_summary="A bounded hidden rule was confirmed.",
            matched_prediction="prediction:001",
            match_status="matched",
            contradiction_detected=False,
            outcome_status="matched",
            calibration_ready=True,
        )
        assert validate_unknown_engine_research_run_v1(_run(reveal_packets=[reveal]))["valid"] is True

    def test_07_valid_mutation_metadata_passes(self):
        mutation = build_unknown_engine_mutation_v1(
            mutation_id="mutation:001",
            mutation_type="rule_shift",
            mutation_target="hidden-rule:001",
            mutation_reason="Pressure the hidden rule without revealing it.",
            mutation_summary="Controlled rule shift only.",
            expected_pressure="Increase uncertainty around the next reveal.",
            target_uncertainty="uncertainty:boundary-pressure",
            safe_to_reingest=False,
        )
        assert validate_unknown_engine_research_run_v1(_run(mutation_packets=[mutation]))["valid"] is True

    def test_08_valid_correction_metadata_passes(self):
        correction = build_unknown_engine_correction_v1(
            correction_id="correction:001",
            prediction_id="prediction:001",
            error_type="none",
            failed_assumption="The reveal would be noisier than it was.",
            model_update_summary="Confidence stayed bounded.",
            compressed_lesson="Keep the next probe narrow.",
            future_adjustment="Use the same probe shape next time.",
            calibration_record_ref="calibration:001",
        )
        assert validate_unknown_engine_research_run_v1(_run(correction_packets=[correction]))["valid"] is True

    def test_09_valid_research_run_passes_protocol_validation(self):
        run = _run()
        validation = validate_unknown_engine_research_run_v1(run)
        protocol_validation = protocol.validate_cognitive_research_run_v1(run)
        assert validation["valid"] is True
        assert protocol_validation["blocked"] is False
        assert protocol_validation["classification"] == ENGINE_NAME_V1

    def test_10_calibration_ready_packet_maps_into_bridge(self):
        run = _run()
        packet = build_forecast_calibration_packet_from_research_run_v1(
            run,
            prediction_id=run["prediction_packets"][0]["prediction_id"],
            prediction_statement=run["prediction_packets"][0]["prediction_statement"],
            prediction_type="hidden_rule_prediction",
            prediction_scope="metadata_only",
            confidence_before=run["prediction_packets"][0]["confidence"],
            confidence_after=run["prediction_packets"][0]["confidence"],
            confidence_basis=run["prediction_packets"][0]["confidence_basis"],
            uncertainty_factors=run["prediction_packets"][0]["uncertainty_factors"],
            invalidation_signals=run["prediction_packets"][0]["invalidation_signals"],
            expected_outcome=run["reveal_packets"][0]["revealed_state_summary"],
            observed_outcome=run["reveal_packets"][0]["revealed_state_summary"],
            outcome_status="matched",
            calibration_result="well_calibrated",
            error_type="none",
            assumptions_used=run["prediction_packets"][0]["assumptions"],
            assumptions_failed=[],
            missing_signals=[],
            conflicting_signals=[],
            correction=run["correction_packets"][0]["compressed_lesson"],
            compressed_lesson=run["correction_packets"][0]["compressed_lesson"],
            future_adjustment=run["correction_packets"][0]["future_adjustment"],
        )
        assert validate_forecast_calibration_record_v1(packet)["valid"] is True

    def test_11_json_safe_copy_strips_unsafe_raw_fields(self):
        unsafe = deepcopy(_run())
        unsafe["raw_prompt_text"] = "raw prompt: hidden"
        unsafe["hidden_prompt"] = "system prompt leakage"
        safe = to_unknown_engine_json_safe_v1(unsafe)
        assert "raw_prompt_text" not in safe
        assert "hidden_prompt" not in safe
        flattened = "\n".join(_flatten(safe)).lower()
        assert "raw prompt: hidden" not in flattened
        assert "system prompt leakage" not in flattened
        json.dumps(safe, sort_keys=True)

    def test_12_summary_is_concise_and_private_safe(self):
        summary = summarize_unknown_engine_research_run_v1(_run())
        assert len(summary["summary_text"]) <= 360
        assert "secret" not in summary["summary_text"].lower()
        assert "hidden prompt" not in summary["summary_text"].lower()

    def test_13_examples_cover_at_least_four_world_families(self):
        examples = build_initial_unknown_engine_examples_v1()
        families = {example["world_packet"]["world_family"] for example in examples}
        assert len(examples) >= 4
        assert len(families) >= 4
        assert families.issuperset({"symbolic_sequence", "operator_algebra", "graph_transition", "noise_mixed_signal"})

    @pytest.mark.parametrize(
        "mutator,expected",
        [
            (lambda run: run["world_packet"].__setitem__("hidden_rule_content", "secret hidden rule"), "hidden_rule_content_inline"),
            (lambda run: run["observation_packets"][0].__setitem__("raw_observation_included", True), "raw_observation_inline"),
            (lambda run: run["prediction_packets"][0].__delitem__("confidence"), "missing_confidence"),
            (lambda run: run["prediction_packets"][0].__delitem__("uncertainty_factors"), "missing_uncertainty_factors"),
            (lambda run: run["prediction_packets"][0].__delitem__("invalidation_signals"), "missing_invalidation_signals"),
            (lambda run: (run["reveal_packets"][0].__setitem__("calibration_ready", True), run["reveal_packets"][0].__setitem__("revealed_state_summary", "")), "calibration_ready_without_revealed_outcome"),
            (lambda run: run["correction_packets"][0].__delitem__("compressed_lesson"), "missing_compressed_lesson"),
            (lambda run: run.__setitem__("public_claim_status", "public_safe_summary_required"), "public_export_marked_safe"),
            (lambda run: run["prediction_packets"][0].__setitem__("prediction_statement", "final answer: the world is solved"), "final_answer"),
            (lambda run: run["prediction_packets"][0].__setitem__("confidence_basis", "llm authority granted"), "llm_authority"),
            (lambda run: run["world_packet"].__setitem__("observation_surface", "tool execution and provider authority with runtime authority and provider output: model output: search output: advisor output:"), "runtime_provider_tool_persistence_implication"),
            (lambda run: run["world_packet"].__setitem__("hidden_rule_ref", ".weslr implication"), "dot_weslr_implication"),
            (lambda run: run["world_packet"].__setitem__("observation_surface", "live ingestion from github rss and network feed"), "live_ingestion_network_implication"),
            (lambda run: run.__setitem__("denied_authority", None), "missing_denied_authority"),
            (lambda run: run["safe_metadata"].__setitem__("safe", False), "unsafe_or_missing_safe_metadata"),
            (lambda run: run["prediction_packets"][0].__setitem__("prediction_statement", "behavior pack promotion implication"), "behavior_pack_promotion_implication"),
            (lambda run: run["world_packet"].__setitem__("observation_surface", "memory mutation authority"), "memory_mutation_authority"),
            (lambda run: run["world_packet"].__setitem__("observation_surface", "project mutation authority"), "project_mutation_authority"),
        ],
    )
    def test_14_negative_validation_rules_fail_closed(self, mutator, expected):
        run = _run()
        mutator(run)
        validation = validate_unknown_engine_research_run_v1(run)
        assert validation["valid"] is False
        labels = " ".join(validation["violations"])
        assert expected in labels

    def test_15_safe_to_reingest_needs_reason_and_uncertainty(self):
        mutation = build_unknown_engine_mutation_v1(
            mutation_id="mutation:unsafe",
            mutation_type="rule_shift",
            mutation_target="hidden-rule:001",
            mutation_summary="Controlled pressure only.",
            expected_pressure="Increase uncertainty.",
            safe_to_reingest=True,
        )
        run = _run(mutation_packets=[mutation])
        run["mutation_packets"][0]["mutation_reason"] = ""
        run["mutation_packets"][0]["target_uncertainty"] = ""
        validation = validate_unknown_engine_research_run_v1(run)
        assert validation["valid"] is False
        assert any("unsafe_safe_to_reingest_without_reason" in label for label in validation["violations"])

    def test_16_protected_files_unchanged(self):
        for rel in PROTECTED_FILES:
            subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], check=True)
