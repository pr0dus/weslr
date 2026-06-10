"""WESLR Unknown Engine adapter metadata helpers V1.

Helper-only, metadata-only, deterministic, JSON-safe Unknown Engine packets
built on top of the shared CognitiveResearchRunV1 protocol. This module does
not execute runtime behavior, providers, models, tools, search, persistence,
.weslr IO, memory/project mutation, behavior-pack promotion, public claims,
final-answer generation, or authority grants.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any, Mapping

from weslr.cognitive_research_protocol import (
    ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1,
    ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1,
    build_cognitive_research_run_v1,
    build_default_cognitive_research_denied_authority_v1,
    summarize_cognitive_research_run_v1,
    validate_cognitive_research_run_v1,
)
from weslr.forecast_calibration_bridge import (
    build_forecast_calibration_packet_from_research_run_v1,
    validate_forecast_calibration_record_v1,
)

HELPER_TYPE_V1 = "weslr_unknown_engine_adapter_v1"
SCHEMA_VERSION_V1 = "unknown_engine_adapter_v1"
ENGINE_NAME_V1 = "unknown_engine"
ENGINE_FAMILY_V1 = "unknown_modeling"

ALLOWED_WORLD_FAMILIES_V1 = (
    "symbolic_sequence",
    "operator_algebra",
    "graph_transition",
    "cellular_grid",
    "toy_physics",
    "mutable_axiom_world",
    "contradiction_cloud",
    "noise_mixed_signal",
    "unknown",
)
ALLOWED_MATCH_STATUSES_V1 = (
    "matched",
    "partially_matched",
    "failed",
    "contradicted",
    "inconclusive",
    "blocked",
    "not_revealed",
)
ALLOWED_MUTATION_TYPES_V1 = (
    "noise_increase",
    "noise_decrease",
    "rule_shift",
    "operator_substitution",
    "delayed_causality",
    "hidden_variable_inserted",
    "false_pattern_inserted",
    "scale_transition",
    "axiom_mutation",
    "random_control",
)
ALLOWED_ERROR_TYPES_V1 = (
    "none",
    "overfit_to_signal",
    "ignored_uncertainty",
    "missing_context",
    "wrong_assumption",
    "scope_mismatch",
    "noise_treated_as_signal",
    "signal_treated_as_noise",
    "operator_overreach",
    "translation_overreach",
    "mutation_fragility",
    "unknown",
)
ALLOWED_PUBLIC_CLAIM_STATUSES_V1 = (
    "not_public_claim",
    "internal_candidate_only",
    "public_export_blocked",
)

_REQUIRED_SAFE_METADATA_FLAGS_V1 = (
    "safe",
    "metadata_only",
    "json_safe",
    "non_public",
    "no_runtime_wiring",
    "no_provider_calls",
    "no_tool_execution",
    "no_persistence",
    "no_memory_mutation",
    "no_project_mutation",
    "no_behavior_pack_promotion",
    "no_final_answer",
    "no_public_claims",
)

_FORBIDDEN_KEY_FRAGMENTS_V1 = (
    "raw_prompt",
    "raw_response",
    "raw_observation",
    "hidden_prompt",
    "private_blob",
    "private_content",
    "secret",
    "password",
    "api_key",
    "provider",
    "model",
    "search",
    "advisor",
    "runtime",
    "tool",
    "final_answer",
    "answer_draft",
    "reply_output",
    "preview_output",
    "public_discovery",
    "proof",
    "breakthrough",
    "behavior_pack",
    "promotion",
    "memory_mutation",
    "project_mutation",
    ".weslr",
)

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw prompt:",
    "raw_response:",
    "system prompt:",
    "developer prompt:",
    "hidden prompt",
    "private content:",
    "confidential:",
    "secret:",
    "password:",
    "api key",
    "raw observation",
    "final answer:",
    "final-answer",
    "answer draft:",
    "reply output:",
    "preview output:",
    "provider output:",
    "model output:",
    "search output:",
    "advisor output:",
    "tool execution",
    "tool authority",
    "provider authority",
    "runtime authority",
    "llm authority",
    "public discovery",
    "proof claim",
    "breakthrough",
    "behavior pack",
    "promotion",
    "memory mutation authority",
    "project mutation authority",
    ".weslr",
    "live ingestion",
    "network feed",
    "github rss",
    "lab notebook",
    "executable code-as-action",
)

_ALLOWED_SAFE_TOP_LEVEL_KEYS_V1 = {
    "schema_version",
    "run_id",
    "engine_name",
    "engine_family",
    "research_mode",
    "source_scope",
    "input_artifact_ref",
    "input_artifact_type",
    "input_summary",
    "source_signal",
    "normalization_summary",
    "ingestion_summary",
    "observations",
    "extracted_signals",
    "motif_candidates",
    "operator_candidates",
    "invariant_candidates",
    "resonance_candidates",
    "nonlinear_inspiration_candidates",
    "hypotheses",
    "predictions",
    "confidence_map",
    "uncertainty_map",
    "verification_steps",
    "human_verification_steps",
    "machine_verification_steps",
    "falsification_probes",
    "probes",
    "mutations",
    "generated_source_signals",
    "rule_pressure_tests",
    "perspicuity_score",
    "trend_score",
    "outcomes",
    "corrections",
    "compressed_lesson",
    "next_experiments",
    "suggestion_store_updates",
    "calibration_record",
    "llm_helper_role",
    "public_claim_status",
    "public_gap_card_status",
    "boundary_status",
    "denied_authority",
    "safe_metadata",
    "domain",
    "domain_subtype",
    "system_level",
    "artifact_scale",
    "constraint_map",
    "safety_boundary",
    "hazard_flags",
    "validation_route",
    "required_expert_review",
    "source_requirements",
    "experiment_type",
    "simulation_before_real_world",
    "non_actionable_research_only",
    "forbidden_action_notes",
    "cross_domain_analogies",
    "candidate_transfer_patterns",
    "failure_mode_map",
    "measurement_gap_map",
    "operator_gap_map",
    "language_gap_map",
    "unknown_unknowns",
    "world_packet",
    "observation_packets",
    "prediction_packets",
    "reveal_packets",
    "mutation_packets",
    "correction_packets",
    "forecast_calibration_packet",
    "unknown_engine_metadata",
    "relationship_to_raw_signal_cartographer",
    "relationship_to_unintelligible_output_analyzer",
    "relationship_to_cognitive_research_run",
}

_ALLOWED_SAFE_PACKET_KEYS_V1 = {
    "world_id",
    "world_family",
    "world_seed_ref",
    "hidden_rule_ref",
    "hidden_rule_content_included",
    "observation_surface",
    "observation_count",
    "hidden_state_count",
    "noise_level",
    "mutation_mode",
    "difficulty_label",
    "truth_reveal_policy",
    "public_claim_status",
    "safe_metadata",
    "denied_authority",
    "observation_id",
    "time_index",
    "visible_state_summary",
    "hidden_state_ref",
    "raw_observation_included",
    "operator_markers",
    "motif_markers",
    "uncertainty_markers",
    "prediction_id",
    "prediction_statement",
    "predicted_next_state",
    "predicted_hidden_rule",
    "confidence",
    "confidence_basis",
    "assumptions",
    "uncertainty_factors",
    "invalidation_signals",
    "next_best_probe",
    "reveal_id",
    "revealed_state_summary",
    "revealed_rule_summary",
    "matched_prediction",
    "match_status",
    "contradiction_detected",
    "outcome_status",
    "calibration_ready",
    "mutation_id",
    "mutation_type",
    "mutation_target",
    "mutation_reason",
    "mutation_summary",
    "expected_pressure",
    "target_uncertainty",
    "safe_to_reingest",
    "correction_id",
    "failed_assumption",
    "model_update_summary",
    "compressed_lesson",
    "future_adjustment",
    "calibration_record_ref",
    "world_packet",
    "observation_packets",
    "prediction_packets",
    "reveal_packets",
    "mutation_packets",
    "correction_packets",
    "forecast_calibration_packet",
    "world_metadata",
    "observation_metadata",
    "prediction_metadata",
    "reveal_metadata",
    "mutation_metadata",
    "correction_metadata",
}

_WORLD_DEFAULTS_V1: dict[str, dict[str, Any]] = {
    "symbolic_sequence": {
        "world_seed_ref": "seed:unknown-engine:symbolic-sequence",
        "hidden_rule_ref": "rule:unknown-engine:symbolic-sequence",
        "observation_surface": "A bounded symbolic sequence with a hidden operator rule and repeated motifs.",
        "observation_count": 3,
        "hidden_state_count": 1,
        "noise_level": "low",
        "mutation_mode": "operator_substitution",
        "difficulty_label": "bounded",
        "truth_reveal_policy": "delayed_reveal",
    },
    "operator_algebra": {
        "world_seed_ref": "seed:unknown-engine:operator-algebra",
        "hidden_rule_ref": "rule:unknown-engine:operator-algebra",
        "observation_surface": "An operator algebra with one hidden rewrite rule and stable local notation.",
        "observation_count": 4,
        "hidden_state_count": 1,
        "noise_level": "medium",
        "mutation_mode": "rule_shift",
        "difficulty_label": "moderate",
        "truth_reveal_policy": "partial_reveal",
    },
    "graph_transition": {
        "world_seed_ref": "seed:unknown-engine:graph-transition",
        "hidden_rule_ref": "rule:unknown-engine:graph-transition",
        "observation_surface": "A graph transition world where local edges change under a hidden constraint.",
        "observation_count": 4,
        "hidden_state_count": 2,
        "noise_level": "medium",
        "mutation_mode": "scale_transition",
        "difficulty_label": "moderate",
        "truth_reveal_policy": "delayed_reveal",
    },
    "cellular_grid": {
        "world_seed_ref": "seed:unknown-engine:cellular-grid",
        "hidden_rule_ref": "rule:unknown-engine:cellular-grid",
        "observation_surface": "A cellular grid with local neighborhoods, one hidden update rule, and delayed reveal.",
        "observation_count": 5,
        "hidden_state_count": 1,
        "noise_level": "low",
        "mutation_mode": "noise_increase",
        "difficulty_label": "moderate",
        "truth_reveal_policy": "delayed_reveal",
    },
    "toy_physics": {
        "world_seed_ref": "seed:unknown-engine:toy-physics",
        "hidden_rule_ref": "rule:unknown-engine:toy-physics",
        "observation_surface": "A toy physics world with discretized motion, bounded forces, and hidden constraints.",
        "observation_count": 4,
        "hidden_state_count": 2,
        "noise_level": "medium",
        "mutation_mode": "delayed_causality",
        "difficulty_label": "hard",
        "truth_reveal_policy": "partial_reveal",
    },
    "mutable_axiom_world": {
        "world_seed_ref": "seed:unknown-engine:mutable-axiom-world",
        "hidden_rule_ref": "rule:unknown-engine:mutable-axiom-world",
        "observation_surface": "A mutable axiom world where a core assumption can shift under pressure.",
        "observation_count": 3,
        "hidden_state_count": 1,
        "noise_level": "low",
        "mutation_mode": "axiom_mutation",
        "difficulty_label": "hard",
        "truth_reveal_policy": "delayed_reveal",
    },
    "contradiction_cloud": {
        "world_seed_ref": "seed:unknown-engine:contradiction-cloud",
        "hidden_rule_ref": "rule:unknown-engine:contradiction-cloud",
        "observation_surface": "A contradiction cloud with competing readings and a hidden consistency boundary.",
        "observation_count": 3,
        "hidden_state_count": 2,
        "noise_level": "high",
        "mutation_mode": "false_pattern_inserted",
        "difficulty_label": "hard",
        "truth_reveal_policy": "partial_reveal",
    },
    "noise_mixed_signal": {
        "world_seed_ref": "seed:unknown-engine:noise-mixed-signal",
        "hidden_rule_ref": "rule:unknown-engine:noise-mixed-signal",
        "observation_surface": "A mixed signal with weak motifs, noise pressure, and one hidden stable pattern.",
        "observation_count": 4,
        "hidden_state_count": 1,
        "noise_level": "high",
        "mutation_mode": "random_control",
        "difficulty_label": "moderate",
        "truth_reveal_policy": "delayed_reveal",
    },
    "unknown": {
        "world_seed_ref": "seed:unknown-engine:unknown",
        "hidden_rule_ref": "rule:unknown-engine:unknown",
        "observation_surface": "An unknown hidden-rule world with bounded metadata only.",
        "observation_count": 3,
        "hidden_state_count": 1,
        "noise_level": "medium",
        "mutation_mode": "random_control",
        "difficulty_label": "unknown",
        "truth_reveal_policy": "delayed_reveal",
    },
}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(deepcopy(value))
    if isinstance(value, set):
        return sorted(deepcopy(value), key=repr)
    return [deepcopy(value)]


def _append_unique(target: list[str], label: str) -> None:
    if label not in target:
        target.append(label)


def _compact_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("`", " ").replace("\n", " ").replace("\r", " ").strip()
    while "  " in text:
        text = text.replace("  ", " ")
    return text[:240]


def _is_json_safe(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, bool)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_safe(item) for key, item in value.items())
    if isinstance(value, list):
        return all(_is_json_safe(item) for item in value)
    return False


def _json_safe(value: Any) -> Any:
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else "non_json_safe_float_replaced"
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return "non_json_safe_value_replaced"


def _walk(value: Any, path: str = ""):
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child = f"{path}.{key_text}" if path else key_text
            yield child, item
            yield from _walk(item, child)
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            child = f"{path}[{index}]"
            yield child, item
            yield from _walk(item, child)


def _stable_digest(data: Any) -> str:
    payload = json.dumps(_json_safe(data), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _default_safe_metadata() -> dict[str, Any]:
    return {
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
    }


def _normalize_denied_authority(value: Any = None) -> dict[str, bool]:
    denied = build_default_cognitive_research_denied_authority_v1()
    if isinstance(value, Mapping):
        for key in denied:
            denied[key] = bool(value.get(key, False))
    return denied


def _build_packet_common(packet: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(packet)
    data.setdefault("public_claim_status", "not_public_claim")
    data.setdefault("safe_metadata", _default_safe_metadata())
    data.setdefault("denied_authority", _normalize_denied_authority())
    data["safe_metadata"] = _json_safe(data["safe_metadata"])
    data["denied_authority"] = _normalize_denied_authority(data["denied_authority"])
    return data


def _lookup_world_defaults(world_family: str) -> dict[str, Any]:
    return deepcopy(_WORLD_DEFAULTS_V1.get(world_family, _WORLD_DEFAULTS_V1["unknown"]))


def _seed_world_family(world_family: Any) -> str:
    value = _compact_text(world_family).lower()
    return value if value in ALLOWED_WORLD_FAMILIES_V1 else "unknown"


def _safe_packet_base(kind: str, payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any]
    if payload is None:
        data = {}
    elif isinstance(payload, Mapping):
        data = dict(payload)
    else:
        data = {kind: payload}
    data.update(overrides)
    return data


def _safe_list_text(value: Any, fallback: str) -> list[str]:
    items = [_compact_text(item) for item in _ensure_list(value)]
    items = [item for item in items if item]
    return items or [fallback]


def _clean_prediction_like_text(value: Any, fallback: str) -> str:
    text = _compact_text(value)
    return text if text else fallback


def _world_template(world_family: str, world_id: str | None = None) -> dict[str, Any]:
    family = _seed_world_family(world_family)
    defaults = _lookup_world_defaults(family)
    world_id = _compact_text(world_id) or f"world:{family}:001"
    return {
        "world_id": world_id,
        "world_family": family,
        "world_seed_ref": defaults["world_seed_ref"],
        "hidden_rule_ref": defaults["hidden_rule_ref"],
        "hidden_rule_content_included": False,
        "observation_surface": defaults["observation_surface"],
        "observation_count": defaults["observation_count"],
        "hidden_state_count": defaults["hidden_state_count"],
        "noise_level": defaults["noise_level"],
        "mutation_mode": defaults["mutation_mode"],
        "difficulty_label": defaults["difficulty_label"],
        "truth_reveal_policy": defaults["truth_reveal_policy"],
        "public_claim_status": "not_public_claim",
        "safe_metadata": _default_safe_metadata(),
        "denied_authority": _normalize_denied_authority(),
    }


def build_unknown_engine_world_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _safe_packet_base("world_packet", payload, **overrides)
    family = _seed_world_family(data.get("world_family"))
    world = _world_template(family, data.get("world_id"))
    world.update({k: v for k, v in data.items() if k not in {"world_family"}})
    world["world_family"] = family
    world["hidden_rule_content_included"] = bool(world.get("hidden_rule_content_included", False))
    world["observation_surface"] = _clean_prediction_like_text(world.get("observation_surface"), _lookup_world_defaults(family)["observation_surface"])
    world["world_seed_ref"] = _clean_prediction_like_text(world.get("world_seed_ref"), _lookup_world_defaults(family)["world_seed_ref"])
    world["hidden_rule_ref"] = _clean_prediction_like_text(world.get("hidden_rule_ref"), _lookup_world_defaults(family)["hidden_rule_ref"])
    world["observation_count"] = int(world.get("observation_count", 0) or 0)
    world["hidden_state_count"] = int(world.get("hidden_state_count", 0) or 0)
    world["noise_level"] = _compact_text(world.get("noise_level")) or "medium"
    world["mutation_mode"] = _compact_text(world.get("mutation_mode")) or "random_control"
    world["difficulty_label"] = _compact_text(world.get("difficulty_label")) or "unknown"
    world["truth_reveal_policy"] = _compact_text(world.get("truth_reveal_policy")) or "delayed_reveal"
    world["public_claim_status"] = _compact_text(world.get("public_claim_status")) or "not_public_claim"
    world["safe_metadata"] = _default_safe_metadata() if not isinstance(world.get("safe_metadata"), Mapping) else {**_default_safe_metadata(), **{str(k): v for k, v in world["safe_metadata"].items()}}
    world["denied_authority"] = _normalize_denied_authority(world.get("denied_authority"))
    return _json_safe(world)


def build_unknown_engine_observation_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _safe_packet_base("observation_packet", payload, **overrides)
    observation = {
        "observation_id": _compact_text(data.get("observation_id")) or f"observation:{_stable_digest(data)[:12]}",
        "time_index": int(data.get("time_index", 0) or 0),
        "visible_state_summary": _clean_prediction_like_text(
            data.get("visible_state_summary"),
            "Visible state summary is metadata-only and bounded.",
        ),
        "hidden_state_ref": _clean_prediction_like_text(data.get("hidden_state_ref"), "hidden-state:reference-only"),
        "raw_observation_included": bool(data.get("raw_observation_included", False)),
        "operator_markers": _safe_list_text(data.get("operator_markers"), "operator-marker:unknown"),
        "motif_markers": _safe_list_text(data.get("motif_markers"), "motif-marker:unknown"),
        "uncertainty_markers": _safe_list_text(data.get("uncertainty_markers"), "uncertainty-marker:unknown"),
        "safe_metadata": _default_safe_metadata() if not isinstance(data.get("safe_metadata"), Mapping) else {**_default_safe_metadata(), **{str(k): v for k, v in data["safe_metadata"].items()}},
        "denied_authority": _normalize_denied_authority(data.get("denied_authority")),
    }
    return _json_safe(observation)


def build_unknown_engine_prediction_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _safe_packet_base("prediction_packet", payload, **overrides)
    confidence = data.get("confidence", 0.5)
    if isinstance(confidence, str):
        confidence_value: float | str = _compact_text(confidence).lower() or "unknown"
    else:
        confidence_value = float(confidence)
    prediction = {
        "prediction_id": _compact_text(data.get("prediction_id")) or f"prediction:{_stable_digest(data)[:12]}",
        "prediction_statement": _clean_prediction_like_text(
            data.get("prediction_statement"),
            "A hidden rule will remain bounded by the current evidence.",
        ),
        "predicted_next_state": _clean_prediction_like_text(
            data.get("predicted_next_state"),
            "next-state:bounded_change",
        ),
        "predicted_hidden_rule": _clean_prediction_like_text(
            data.get("predicted_hidden_rule"),
            "hidden-rule:bounded_candidate",
        ),
        "confidence": confidence_value,
        "confidence_basis": _clean_prediction_like_text(
            data.get("confidence_basis"),
            "Metadata-only basis from observed structure and uncertainty markers.",
        ),
        "assumptions": _safe_list_text(data.get("assumptions"), "assumption:bounded-world"),
        "uncertainty_factors": _safe_list_text(data.get("uncertainty_factors"), "uncertainty:partial_visibility"),
        "invalidation_signals": _safe_list_text(data.get("invalidation_signals"), "invalidation:missing_reveal"),
        "next_best_probe": _clean_prediction_like_text(data.get("next_best_probe"), "probe the next hidden transition"),
        "safe_metadata": _default_safe_metadata() if not isinstance(data.get("safe_metadata"), Mapping) else {**_default_safe_metadata(), **{str(k): v for k, v in data["safe_metadata"].items()}},
        "denied_authority": _normalize_denied_authority(data.get("denied_authority")),
        "public_claim_status": _compact_text(data.get("public_claim_status")) or "internal_candidate_only",
    }
    return _json_safe(prediction)


def build_unknown_engine_reveal_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _safe_packet_base("reveal_packet", payload, **overrides)
    match_status = _compact_text(data.get("match_status")).lower() or "not_revealed"
    reveal = {
        "reveal_id": _compact_text(data.get("reveal_id")) or f"reveal:{_stable_digest(data)[:12]}",
        "prediction_id": _compact_text(data.get("prediction_id")),
        "revealed_state_summary": _clean_prediction_like_text(data.get("revealed_state_summary"), "" if match_status == "not_revealed" else "revealed-state:bounded"),
        "revealed_rule_summary": _clean_prediction_like_text(data.get("revealed_rule_summary"), "" if match_status == "not_revealed" else "revealed-rule:bounded"),
        "matched_prediction": _compact_text(data.get("matched_prediction")) or _compact_text(data.get("prediction_id")),
        "match_status": match_status,
        "contradiction_detected": bool(data.get("contradiction_detected", False)),
        "outcome_status": _compact_text(data.get("outcome_status")) or match_status,
        "calibration_ready": bool(data.get("calibration_ready", False)),
        "safe_metadata": _default_safe_metadata() if not isinstance(data.get("safe_metadata"), Mapping) else {**_default_safe_metadata(), **{str(k): v for k, v in data["safe_metadata"].items()}},
        "denied_authority": _normalize_denied_authority(data.get("denied_authority")),
        "public_claim_status": _compact_text(data.get("public_claim_status")) or "internal_candidate_only",
    }
    return _json_safe(reveal)


def build_unknown_engine_mutation_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _safe_packet_base("mutation_packet", payload, **overrides)
    mutation = {
        "mutation_id": _compact_text(data.get("mutation_id")) or f"mutation:{_stable_digest(data)[:12]}",
        "mutation_type": _compact_text(data.get("mutation_type")) or "random_control",
        "mutation_target": _clean_prediction_like_text(data.get("mutation_target"), "hidden-rule:reference-only"),
        "mutation_reason": _clean_prediction_like_text(data.get("mutation_reason"), _clean_prediction_like_text(data.get("mutation_summary"), "Mutation metadata only.")),
        "mutation_summary": _clean_prediction_like_text(data.get("mutation_summary"), "Metadata-only mutation pressure record."),
        "expected_pressure": _clean_prediction_like_text(data.get("expected_pressure"), "Pressure on boundary stability and inference narrowing."),
        "target_uncertainty": _clean_prediction_like_text(data.get("target_uncertainty"), "uncertainty:bounded"),
        "safe_to_reingest": bool(data.get("safe_to_reingest", False)),
        "safe_metadata": _default_safe_metadata() if not isinstance(data.get("safe_metadata"), Mapping) else {**_default_safe_metadata(), **{str(k): v for k, v in data["safe_metadata"].items()}},
        "denied_authority": _normalize_denied_authority(data.get("denied_authority")),
        "public_claim_status": _compact_text(data.get("public_claim_status")) or "internal_candidate_only",
    }
    return _json_safe(mutation)


def build_unknown_engine_correction_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _safe_packet_base("correction_packet", payload, **overrides)
    correction = {
        "correction_id": _compact_text(data.get("correction_id")) or f"correction:{_stable_digest(data)[:12]}",
        "prediction_id": _compact_text(data.get("prediction_id")),
        "error_type": _compact_text(data.get("error_type")) or "unknown",
        "failed_assumption": _clean_prediction_like_text(data.get("failed_assumption"), "failed-assumption:bounded"),
        "model_update_summary": _clean_prediction_like_text(data.get("model_update_summary"), "Model update remains metadata-only and bounded."),
        "compressed_lesson": _clean_prediction_like_text(data.get("compressed_lesson"), "Keep the adapter bounded, private, and calibration-ready."),
        "future_adjustment": _clean_prediction_like_text(data.get("future_adjustment"), "Adjust probe selection and uncertainty handling next time."),
        "calibration_record_ref": _clean_prediction_like_text(data.get("calibration_record_ref"), "calibration-record:reference-only"),
        "safe_metadata": _default_safe_metadata() if not isinstance(data.get("safe_metadata"), Mapping) else {**_default_safe_metadata(), **{str(k): v for k, v in data["safe_metadata"].items()}},
        "denied_authority": _normalize_denied_authority(data.get("denied_authority")),
        "public_claim_status": _compact_text(data.get("public_claim_status")) or "internal_candidate_only",
    }
    return _json_safe(correction)


def _default_observation_for_world(world: Mapping[str, Any]) -> dict[str, Any]:
    return build_unknown_engine_observation_v1(
        observation_id=f"observation:{_compact_text(world.get('world_id')) or 'world-001'}:001",
        time_index=0,
        visible_state_summary=_compact_text(world.get("observation_surface")) or "Visible state summary is metadata-only and bounded.",
        hidden_state_ref=_compact_text(world.get("hidden_rule_ref")) or "hidden-state:reference-only",
        raw_observation_included=False,
        operator_markers=["operator:bounded_rule"],
        motif_markers=["motif:repeated_pattern"],
        uncertainty_markers=["uncertainty:hidden_rule"],
    )


def _default_prediction_for_world(world: Mapping[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
    family = _compact_text(world.get("world_family")) or "unknown"
    return build_unknown_engine_prediction_v1(
        prediction_id=f"prediction:{_compact_text(world.get('world_id')) or 'world-001'}:001",
        prediction_statement=f"The {family} world will reveal a bounded next transition after one more probe.",
        predicted_next_state=f"next-state:{family}:bounded",
        predicted_hidden_rule=_compact_text(world.get("hidden_rule_ref")) or "hidden-rule:reference-only",
        confidence=0.62,
        confidence_basis="Observation markers, motif markers, and bounded uncertainty only.",
        assumptions=[_compact_text(observation.get("visible_state_summary")) or "visible-state-summary"] ,
        uncertainty_factors=["partial visibility", "hidden rule not revealed"],
        invalidation_signals=["contradictory reveal", "failed probe"],
        next_best_probe="request a reveal for the next transition",
    )


def _default_reveal_for_prediction(prediction: Mapping[str, Any]) -> dict[str, Any]:
    return build_unknown_engine_reveal_v1(
        reveal_id=f"reveal:{_compact_text(prediction.get('prediction_id')) or 'prediction-001'}:001",
        prediction_id=_compact_text(prediction.get("prediction_id")),
        revealed_state_summary="revealed-state:bounded next transition",
        revealed_rule_summary="revealed-rule:bounded hidden rule confirmed",
        matched_prediction=_compact_text(prediction.get("prediction_id")),
        match_status="matched",
        contradiction_detected=False,
        outcome_status="matched",
        calibration_ready=True,
    )


def _default_mutation_for_world(world: Mapping[str, Any]) -> dict[str, Any]:
    return build_unknown_engine_mutation_v1(
        mutation_id=f"mutation:{_compact_text(world.get('world_id')) or 'world-001'}:001",
        mutation_type=_compact_text(world.get("mutation_mode")) or "random_control",
        mutation_target=_compact_text(world.get("hidden_rule_ref")) or "hidden-rule:reference-only",
        mutation_reason="Introduce controlled pressure without revealing hidden content.",
        mutation_summary="Controlled mutation pressure only; no runtime effect.",
        expected_pressure="The next transition should become narrower or more uncertain.",
        target_uncertainty="uncertainty:boundary-pressure",
        safe_to_reingest=False,
    )


def _default_correction_for_prediction(prediction: Mapping[str, Any], reveal: Mapping[str, Any], calibration_ref: str) -> dict[str, Any]:
    return build_unknown_engine_correction_v1(
        correction_id=f"correction:{_compact_text(prediction.get('prediction_id')) or 'prediction-001'}:001",
        prediction_id=_compact_text(prediction.get("prediction_id")),
        error_type="none",
        failed_assumption="The initial probe was sufficient.",
        model_update_summary="Observed reveal stayed aligned with the bounded prediction.",
        compressed_lesson="Keep the next probe narrow, private, and calibration-ready.",
        future_adjustment="Adjust confidence only after a mismatch or sharper reveal.",
        calibration_record_ref=calibration_ref,
    )


def build_unknown_engine_research_run_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _safe_packet_base("research_run", payload, **overrides)
    world = build_unknown_engine_world_packet_v1(data.get("world_packet") or {
        "world_id": data.get("world_id"),
        "world_family": data.get("world_family", "unknown"),
        "public_claim_status": data.get("public_claim_status", "not_public_claim"),
        "safe_metadata": data.get("safe_metadata"),
        "denied_authority": data.get("denied_authority"),
    })
    observation_packets = _ensure_list(data.get("observation_packets"))
    if not observation_packets:
        observation_packets = [_default_observation_for_world(world)]
    observation_packets = [build_unknown_engine_observation_v1(item) if not isinstance(item, Mapping) else build_unknown_engine_observation_v1(item) for item in observation_packets]

    prediction_packets = _ensure_list(data.get("prediction_packets"))
    if not prediction_packets:
        prediction_packets = [_default_prediction_for_world(world, observation_packets[0])]
    prediction_packets = [build_unknown_engine_prediction_v1(item) if not isinstance(item, Mapping) else build_unknown_engine_prediction_v1(item) for item in prediction_packets]

    reveal_packets = _ensure_list(data.get("reveal_packets"))
    if not reveal_packets:
        reveal_packets = [_default_reveal_for_prediction(prediction_packets[0])]
    reveal_packets = [build_unknown_engine_reveal_v1(item) if not isinstance(item, Mapping) else build_unknown_engine_reveal_v1(item) for item in reveal_packets]

    mutation_packets = _ensure_list(data.get("mutation_packets"))
    if not mutation_packets:
        mutation_packets = [_default_mutation_for_world(world)]
    mutation_packets = [build_unknown_engine_mutation_v1(item) if not isinstance(item, Mapping) else build_unknown_engine_mutation_v1(item) for item in mutation_packets]

    calibrated_reveal = reveal_packets[0]
    primary_prediction = prediction_packets[0]
    calibration_result = build_forecast_calibration_packet_from_research_run_v1(
        {
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": data.get("research_mode", "calibration_replay"),
            "source_scope": "metadata_only",
            "input_artifact_ref": _compact_text(world.get("world_seed_ref")) or "artifact:unknown-engine:calibration",
            "input_artifact_type": "unknown-engine-world",
            "input_summary": _compact_text(world.get("observation_surface")) or "Unknown Engine world metadata only.",
            "predictions": [primary_prediction["prediction_statement"]],
            "hypotheses": primary_prediction["assumptions"],
            "probes": [primary_prediction["next_best_probe"]],
            "outcomes": [calibrated_reveal["revealed_state_summary"]],
            "compressed_lesson": "Unknown Engine calibration stays metadata-only and private.",
            "public_claim_status": "internal_candidate_only",
            "public_gap_card_status": "public_export_blocked",
            "llm_helper_role": "candidate_generator_only",
            "safe_metadata": _default_safe_metadata(),
            "denied_authority": _normalize_denied_authority(),
        },
        prediction_id=_compact_text(primary_prediction.get("prediction_id")) or f"prediction:{_stable_digest(primary_prediction)[:12]}",
        prediction_statement=_compact_text(primary_prediction.get("prediction_statement")) or "metadata-only prediction statement",
        prediction_type="hidden_rule_prediction",
        prediction_scope="metadata_only",
        confidence_before=primary_prediction.get("confidence", 0.5),
        confidence_after=primary_prediction.get("confidence", 0.5),
        confidence_basis=_compact_text(primary_prediction.get("confidence_basis")) or "metadata-only basis",
        uncertainty_factors=primary_prediction.get("uncertainty_factors"),
        invalidation_signals=primary_prediction.get("invalidation_signals"),
        expected_outcome=_compact_text(calibrated_reveal.get("revealed_state_summary")) or "outcome pending",
        observed_outcome=_compact_text(calibrated_reveal.get("revealed_state_summary")),
        outcome_status=_compact_text(calibrated_reveal.get("outcome_status")) or "matched",
        calibration_result="well_calibrated",
        error_type="none",
        assumptions_used=primary_prediction.get("assumptions"),
        assumptions_failed=[],
        missing_signals=[],
        conflicting_signals=[],
        correction="Observed reveal matched the bounded prediction.",
        compressed_lesson="Calibration stays bounded and private.",
        future_adjustment="Keep confidence tied to reveal quality and uncertainty markers.",
        behavior_change_authorized=False,
        memory_mutation_authorized=False,
        project_mutation_authorized=False,
        public_claim_authorized=False,
    )

    correction_packets = _ensure_list(data.get("correction_packets"))
    if not correction_packets:
        correction_packets = [
            _default_correction_for_prediction(primary_prediction, calibrated_reveal, _compact_text(calibration_result.get("record_id")) or "calibration-record:reference-only")
        ]
    correction_packets = [build_unknown_engine_correction_v1(item) if not isinstance(item, Mapping) else build_unknown_engine_correction_v1(item) for item in correction_packets]

    research_run = build_cognitive_research_run_v1(
        {
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": _compact_text(data.get("research_mode")) or "internal_exploration",
            "source_scope": "metadata_only",
            "input_artifact_ref": _compact_text(world.get("world_seed_ref")) or "artifact:unknown-engine:world",
            "input_artifact_type": "unknown-engine-world",
            "input_summary": _compact_text(world.get("observation_surface")) or "Unknown Engine metadata-only world.",
            "observations": [item["visible_state_summary"] for item in observation_packets],
            "extracted_signals": [marker for item in observation_packets for marker in item.get("motif_markers", [])],
            "motif_candidates": [marker for item in observation_packets for marker in item.get("motif_markers", [])],
            "operator_candidates": [marker for item in observation_packets for marker in item.get("operator_markers", [])],
            "invariant_candidates": ["bounded hidden rule"],
            "resonance_candidates": ["calibration-ready reveal"],
            "nonlinear_inspiration_candidates": ["hidden rule remains private"],
            "hypotheses": [primary_prediction["predicted_hidden_rule"]],
            "predictions": [primary_prediction["prediction_statement"]],
            "confidence_map": {"primary": primary_prediction.get("confidence", 0.5)},
            "uncertainty_map": {"markers": primary_prediction.get("uncertainty_factors", [])},
            "verification_steps": ["observe", "predict", "reveal", "correct"],
            "human_verification_steps": ["operator review"],
            "machine_verification_steps": ["py_compile", "pytest", "release_gate", "release_check"],
            "falsification_probes": [primary_prediction["next_best_probe"]],
            "probes": [primary_prediction["next_best_probe"]],
            "mutations": [item["mutation_summary"] for item in mutation_packets],
            "outcomes": [calibrated_reveal["revealed_state_summary"]],
            "corrections": [item["compressed_lesson"] for item in correction_packets],
            "compressed_lesson": correction_packets[0]["compressed_lesson"],
            "next_experiments": [primary_prediction["next_best_probe"]],
            "suggestion_store_updates": [{"suggestion_id": f"suggestion:{_stable_digest(primary_prediction)[:12]}", "note": "metadata-only calibration lane"}],
            "calibration_record": calibration_result,
            "llm_helper_role": "candidate_generator_only",
            "public_claim_status": _compact_text(data.get("public_claim_status")) or world["public_claim_status"],
            "public_gap_card_status": "public_export_blocked",
            "boundary_status": {
                "status": "metadata_only",
                "generator_loop": "cognitive_research_generator_loop_v1",
                "dialectic_loop": "cognitive_research_dialectic_generator_loop_v1",
                "runtime_wiring_authority": False,
                "chat_responder_authority": False,
                "final_answer_generation_authority": False,
                "public_claim_authority": False,
                "provider_model_call_authority": False,
                "retrieval_tool_authority": False,
                "filesystem_authority": False,
                "network_authority": False,
                "subprocess_authority": False,
                "weslr_io_authority": False,
                "persistence_database_write_authority": False,
                "real_memory_mutation_authority": False,
                "real_project_mutation_authority": False,
                "behavior_pack_promotion_authority": False,
                "autonomous_self_modification_authority": False,
                "official_intelligence_claim_authority": False,
                "public_discovery_claim_authority": False,
                "boundary_notes": "metadata-only; fail closed; no runtime, provider, tool, persistence, or public-export authority",
            },
            "denied_authority": _normalize_denied_authority(data.get("denied_authority")),
            "safe_metadata": _default_safe_metadata(),
            "domain": "unknown engine adapter",
            "domain_subtype": "metadata-only hidden-rule world",
            "system_level": "component",
            "artifact_scale": "bounded artifact",
            "constraint_map": {"runtime": "denied", "tool": "denied", "provider": "denied", "search": "denied", "persistence": "denied", "public_claims": "blocked", "answer_authority": "denied"},
            "safety_boundary": {"mode": "metadata_only", "non_actionable": True},
            "hazard_flags": ["no_live_runtime", "no_public_claims", "no_tool_execution"],
            "validation_route": ["metadata_only_validation", "fail_closed_safety_validation", "json_safe_copy_validation"],
            "required_expert_review": False,
            "source_requirements": {"provenance_required": True, "raw_storage_allowed": False, "side_effect_free": True},
            "experiment_type": "metadata_only",
            "simulation_before_real_world": True,
            "non_actionable_research_only": True,
            "forbidden_action_notes": ["no runtime", "no provider calls", "no persistence"],
            "cross_domain_analogies": ["raw signal cartography", "unintelligible output analysis"],
            "candidate_transfer_patterns": ["bounded probe", "reveal and correct"],
            "failure_mode_map": ["overfit to signal", "ignored uncertainty"],
            "measurement_gap_map": ["hidden rule not yet revealed"],
            "operator_gap_map": ["missing reveal operator"],
            "language_gap_map": ["unreadable hidden rule symbols"],
            "unknown_unknowns": ["future reveal content"],
            "world_packet": world,
            "observation_packets": observation_packets,
            "prediction_packets": prediction_packets,
            "reveal_packets": reveal_packets,
            "mutation_packets": mutation_packets,
            "correction_packets": correction_packets,
            "forecast_calibration_packet": calibration_result,
            "relationship_to_raw_signal_cartographer": {
                "role": "motif_and_operator_metadata",
                "not_final_authority": True,
                "not_runtime_authority": True,
                "not_tool_authority": True,
            },
            "relationship_to_unintelligible_output_analyzer": {
                "role": "interpretation_and_translation_metadata",
                "not_final_authority": True,
                "not_runtime_authority": True,
                "not_tool_authority": True,
            },
            "relationship_to_cognitive_research_run": {
                "role": "protocol_compatible_metadata_only_run",
                "not_runtime_authority": True,
                "not_provider_authority": True,
                "not_public_claim_authority": True,
            },
        }
    )
    research_run["world_packet"] = world
    research_run["observation_packets"] = observation_packets
    research_run["prediction_packets"] = prediction_packets
    research_run["reveal_packets"] = reveal_packets
    research_run["mutation_packets"] = mutation_packets
    research_run["correction_packets"] = correction_packets
    research_run["forecast_calibration_packet"] = calibration_result
    research_run["world_metadata"] = world
    research_run["observation_metadata"] = observation_packets[0]
    research_run["prediction_metadata"] = primary_prediction
    research_run["reveal_metadata"] = calibrated_reveal
    research_run["mutation_metadata"] = mutation_packets[0]
    research_run["correction_metadata"] = correction_packets[0]
    research_run["run_id"] = _compact_text(research_run.get("run_id")) or f"unknown-engine-{_stable_digest({'world': world, 'prediction': primary_prediction, 'reveal': calibrated_reveal})[:16]}"
    return _json_safe(research_run)


def _validate_safe_metadata(packet: Mapping[str, Any]) -> list[str]:
    safe = packet.get("safe_metadata")
    if not isinstance(safe, Mapping):
        return ["missing_safe_metadata"]
    blocked: list[str] = []
    for key in _REQUIRED_SAFE_METADATA_FLAGS_V1:
        if not bool(safe.get(key, False)):
            blocked.append(f"unsafe_safe_metadata:{key}")
    return blocked


def _validate_denied_authority(packet: Mapping[str, Any]) -> list[str]:
    denied = packet.get("denied_authority")
    if not isinstance(denied, Mapping):
        return ["missing_denied_authority"]
    if any(bool(value) for value in denied.values()):
        return [f"denied_authority_granted:{key}" for key, value in denied.items() if bool(value)]
    return []


def _validate_world_packet(packet: Mapping[str, Any]) -> list[str]:
    world = packet.get("world_packet")
    if not isinstance(world, Mapping):
        return ["missing_world_packet"]
    violations: list[str] = []
    if not _compact_text(world.get("world_id")):
        violations.append("missing_world_id")
    if _compact_text(world.get("world_family")).lower() not in ALLOWED_WORLD_FAMILIES_V1:
        violations.append("invalid_world_family")
    if not _compact_text(world.get("world_seed_ref")):
        violations.append("missing_world_seed_ref")
    if not _compact_text(world.get("hidden_rule_ref")):
        violations.append("missing_hidden_rule_ref")
    if bool(world.get("hidden_rule_content_included", False)):
        violations.append("hidden_rule_content_included_inline")
    if not _compact_text(world.get("observation_surface")):
        violations.append("missing_observation_surface")
    if int(world.get("observation_count", 0) or 0) <= 0:
        violations.append("missing_observation_count")
    if int(world.get("hidden_state_count", 0) or 0) <= 0:
        violations.append("missing_hidden_state_count")
    if _compact_text(world.get("public_claim_status")) not in ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        violations.append("public_export_marked_safe")
    return violations


def _validate_observation_packet(item: Any, index: int) -> list[str]:
    if not isinstance(item, Mapping):
        return [f"invalid_observation_packet:{index}"]
    violations: list[str] = []
    if not _compact_text(item.get("observation_id")):
        violations.append(f"missing_observation_id:{index}")
    if not isinstance(item.get("time_index"), int):
        violations.append(f"missing_time_index:{index}")
    if not _compact_text(item.get("visible_state_summary")):
        violations.append(f"missing_visible_state_summary:{index}")
    if not _compact_text(item.get("hidden_state_ref")):
        violations.append(f"missing_hidden_state_ref:{index}")
    if bool(item.get("raw_observation_included", False)):
        violations.append(f"raw_observation_included_inline:{index}")
    if not isinstance(item.get("operator_markers"), list):
        violations.append(f"missing_operator_markers:{index}")
    if not isinstance(item.get("motif_markers"), list):
        violations.append(f"missing_motif_markers:{index}")
    if not isinstance(item.get("uncertainty_markers"), list):
        violations.append(f"missing_uncertainty_markers:{index}")
    return violations


def _validate_prediction_packet(item: Any, index: int) -> list[str]:
    if not isinstance(item, Mapping):
        return [f"invalid_prediction_packet:{index}"]
    violations: list[str] = []
    if not _compact_text(item.get("prediction_id")):
        violations.append(f"missing_prediction_id:{index}")
    if not _compact_text(item.get("prediction_statement")):
        violations.append(f"missing_prediction_statement:{index}")
    if not _compact_text(item.get("predicted_next_state")):
        violations.append(f"missing_predicted_next_state:{index}")
    if not _compact_text(item.get("predicted_hidden_rule")):
        violations.append(f"missing_predicted_hidden_rule:{index}")
    confidence = item.get("confidence")
    if not isinstance(confidence, (int, float)):
        violations.append(f"missing_confidence:{index}")
    else:
        confidence_value = float(confidence)
        if not 0.0 <= confidence_value <= 1.0:
            violations.append(f"invalid_confidence_range:{index}")
    if not _compact_text(item.get("confidence_basis")):
        violations.append(f"missing_confidence_basis:{index}")
    if not _ensure_list(item.get("assumptions")):
        violations.append(f"missing_assumptions:{index}")
    if not _ensure_list(item.get("uncertainty_factors")):
        violations.append(f"missing_uncertainty_factors:{index}")
    if not _ensure_list(item.get("invalidation_signals")):
        violations.append(f"missing_invalidation_signals:{index}")
    if not _compact_text(item.get("next_best_probe")):
        violations.append(f"missing_next_best_probe:{index}")
    return violations


def _validate_reveal_packet(item: Any, index: int) -> list[str]:
    if not isinstance(item, Mapping):
        return [f"invalid_reveal_packet:{index}"]
    violations: list[str] = []
    prediction_id = _compact_text(item.get("prediction_id"))
    match_status = _compact_text(item.get("match_status")).lower()
    if not _compact_text(item.get("reveal_id")):
        violations.append(f"missing_reveal_id:{index}")
    if match_status not in ALLOWED_MATCH_STATUSES_V1:
        violations.append(f"invalid_match_status:{index}")
    if match_status == "matched" and not prediction_id:
        violations.append(f"matched_reveal_without_prediction_id:{index}")
    if match_status != "not_revealed" and not _compact_text(item.get("revealed_state_summary")):
        violations.append(f"missing_revealed_state_summary:{index}")
    if match_status != "not_revealed" and not _compact_text(item.get("revealed_rule_summary")):
        violations.append(f"missing_revealed_rule_summary:{index}")
    if bool(item.get("calibration_ready", False)) and (match_status == "not_revealed" or not _compact_text(item.get("revealed_state_summary")) or not _compact_text(item.get("revealed_rule_summary"))):
        violations.append(f"calibration_ready_without_revealed_outcome:{index}")
    if not _compact_text(item.get("outcome_status")):
        violations.append(f"missing_outcome_status:{index}")
    if not _compact_text(item.get("matched_prediction")) and match_status != "not_revealed":
        violations.append(f"missing_matched_prediction:{index}")
    return violations


def _validate_mutation_packet(item: Any, index: int) -> list[str]:
    if not isinstance(item, Mapping):
        return [f"invalid_mutation_packet:{index}"]
    violations: list[str] = []
    if not _compact_text(item.get("mutation_id")):
        violations.append(f"missing_mutation_id:{index}")
    if _compact_text(item.get("mutation_type")) not in ALLOWED_MUTATION_TYPES_V1:
        violations.append(f"invalid_mutation_type:{index}")
    if not _compact_text(item.get("mutation_target")):
        violations.append(f"missing_mutation_target:{index}")
    if not _compact_text(item.get("mutation_summary")):
        violations.append(f"missing_mutation_summary:{index}")
    if not _compact_text(item.get("expected_pressure")):
        violations.append(f"missing_expected_pressure:{index}")
    if not _compact_text(item.get("target_uncertainty")):
        violations.append(f"missing_target_uncertainty:{index}")
    if bool(item.get("safe_to_reingest", False)) and (not _compact_text(item.get("mutation_reason")) or not _compact_text(item.get("target_uncertainty"))):
        violations.append(f"unsafe_safe_to_reingest_without_reason:{index}")
    return violations


def _validate_correction_packet(item: Any, index: int) -> list[str]:
    if not isinstance(item, Mapping):
        return [f"invalid_correction_packet:{index}"]
    violations: list[str] = []
    if not _compact_text(item.get("correction_id")):
        violations.append(f"missing_correction_id:{index}")
    if not _compact_text(item.get("prediction_id")):
        violations.append(f"missing_prediction_id:{index}")
    if _compact_text(item.get("error_type")) not in ALLOWED_ERROR_TYPES_V1:
        violations.append(f"invalid_error_type:{index}")
    if not _compact_text(item.get("failed_assumption")):
        violations.append(f"missing_failed_assumption:{index}")
    if not _compact_text(item.get("model_update_summary")):
        violations.append(f"missing_model_update_summary:{index}")
    if not _compact_text(item.get("compressed_lesson")):
        violations.append(f"missing_compressed_lesson:{index}")
    if not _compact_text(item.get("calibration_record_ref")):
        violations.append(f"missing_calibration_record_ref:{index}")
    return violations


def _validate_packet_sets(packet: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    if not _ensure_list(packet.get("observation_packets")):
        violations.append("missing_observation_packets")
    if not _ensure_list(packet.get("prediction_packets")):
        violations.append("missing_prediction_packets")
    if not _ensure_list(packet.get("reveal_packets")):
        violations.append("missing_reveal_packets")
    if not _ensure_list(packet.get("mutation_packets")):
        violations.append("missing_mutation_packets")
    if not _ensure_list(packet.get("correction_packets")):
        violations.append("missing_correction_packets")
    return violations


def _validate_public_claims(packet: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    text_blobs = _collect_text_violations(packet)
    for label in text_blobs:
        if label in {"public_breakthrough_claim_blocked", "public_proof_claim_blocked", "final_answer_authority_claim", "llm_authority_claim", "runtime_provider_tool_persistence_implication", "dot_weslr_implication", "live_ingestion_network_implication", "memory_mutation_authority", "project_mutation_authority", "behavior_pack_promotion_implication", "unsafe_or_missing_denied_authority", "unsafe_or_missing_safe_metadata", "hidden_rule_content_inline", "raw_observation_inline"}:
            _append_unique(violations, label)
    return violations


def _summary_text_from_packet(packet: Mapping[str, Any], blocked: bool, violations: list[str] | None = None) -> str:
    raw = packet if isinstance(packet, Mapping) else {}
    world = _as_mapping(raw.get("world_packet"))
    predictions = _ensure_list(raw.get("prediction_packets"))
    reveals = _ensure_list(raw.get("reveal_packets"))
    calibration_ready = bool(reveals and _as_mapping(reveals[0]).get("calibration_ready", False))
    summary_text = (
        f"Unknown-engine research run: world={_compact_text(world.get('world_family')) or 'unknown'}; "
        f"mode={_compact_text(raw.get('research_mode')) or 'internal_exploration'}; "
        f"observations={len(_ensure_list(raw.get('observation_packets')))}; "
        f"predictions={len(predictions)}; reveals={len(reveals)}; "
        f"calibration_ready={calibration_ready}; "
        f"public={_compact_text(raw.get('public_claim_status')) or 'not_public_claim'}."
    )
    if blocked:
        preview = ", ".join((violations or [])[:4])
        return f"Blocked unknown-engine research run: {preview or 'validation failed'}. {summary_text}"
    return summary_text


def _collect_text_violations(value: Any, path: str = "") -> list[str]:
    violations: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}" if path else key_text
            lowered_key = key_text.lower()
            if lowered_key in {"hidden_rule_content", "hidden_rule_text"}:
                _append_unique(violations, "hidden_rule_content_inline")
            if lowered_key == "raw_observation_included" and bool(item):
                _append_unique(violations, "raw_observation_inline")
            if lowered_key in {"public_export_authorized", "public_claim_authorized"} and bool(item):
                _append_unique(violations, "public_export_marked_safe")
            if lowered_key in {"final_answer_authority", "llm_authority", "runtime_wiring_authority", "provider_model_call_authority", "retrieval_tool_authority", "persistence_database_write_authority", "tool_authority", "provider_authority", "memory_mutation_authority", "project_mutation_authority", "behavior_pack_promotion_authority"} and bool(item):
                _append_unique(violations, f"{lowered_key}_true")
            if lowered_key in {"safe_metadata"} and isinstance(item, Mapping):
                if not bool(item.get("safe", False)):
                    _append_unique(violations, "unsafe_or_missing_safe_metadata")
            if lowered_key in {"denied_authority"} and isinstance(item, Mapping):
                if any(bool(v) for v in item.values()):
                    _append_unique(violations, "unsafe_or_missing_denied_authority")
            violations.extend(_collect_text_violations(item, child_path))
        return violations
    if isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            violations.extend(_collect_text_violations(item, child_path))
        return violations
    text = _compact_text(value).lower()
    if not text:
        return violations
    for marker in _FORBIDDEN_TEXT_MARKERS_V1:
        if marker in text:
            if marker in {"public discovery", "proof claim", "breakthrough"}:
                _append_unique(violations, "public_breakthrough_claim_blocked")
            elif marker in {"final answer:", "final-answer"}:
                _append_unique(violations, "final_answer_authority_claim")
            elif marker in {"llm authority", "runtime authority", "tool authority", "provider authority"}:
                _append_unique(violations, f"{marker.replace(' ', '_').replace(':', '').replace('-', '_')}_claim")
            elif marker in {"live ingestion", "network feed", "github rss", "lab notebook"}:
                _append_unique(violations, "live_ingestion_network_implication")
            elif marker == ".weslr":
                _append_unique(violations, "dot_weslr_implication")
            elif marker in {"memory mutation authority"}:
                _append_unique(violations, "memory_mutation_authority")
            elif marker in {"project mutation authority"}:
                _append_unique(violations, "project_mutation_authority")
            elif marker in {"behavior pack", "promotion"}:
                _append_unique(violations, "behavior_pack_promotion_implication")
            elif marker in {"tool execution", "tool authority", "provider authority", "runtime authority", "provider output:", "model output:", "search output:", "advisor output:"}:
                _append_unique(violations, "runtime_provider_tool_persistence_implication")
            elif marker in {"raw prompt:", "raw_response:", "system prompt:", "developer prompt:", "hidden prompt", "secret:", "password:", "api key", "private content:", "confidential:"}:
                _append_unique(violations, "hidden_rule_content_inline")
            elif marker in {"executable code-as-action"}:
                _append_unique(violations, "executable_code_as_action_implication")
            else:
                _append_unique(violations, f"forbidden_text_marker:{marker}")
    return violations


def validate_unknown_engine_research_run_v1(packet: Any) -> dict[str, Any]:
    base = validate_cognitive_research_run_v1(packet)
    raw = packet if isinstance(packet, Mapping) else {}
    violations: list[str] = []

    if not isinstance(packet, Mapping):
        violations.append("invalid_packet_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "helper_type": HELPER_TYPE_V1,
            "valid": False,
            "blocked": True,
            "violations": violations,
            "violation_count": len(violations),
            "protocol_valid": False,
            "protocol_blocked_labels": [],
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": "internal_exploration",
            "public_claim_status": "not_public_claim",
            "summary_text": "Blocked unknown-engine research run: invalid packet type.",
        }

    if base.get("blocked"):
        for label in base.get("blocked_labels", []):
            _append_unique(violations, f"protocol:{label}")

    if _compact_text(raw.get("engine_name")) != ENGINE_NAME_V1:
        _append_unique(violations, "invalid_engine_name")
    if _compact_text(raw.get("engine_family")) != ENGINE_FAMILY_V1:
        _append_unique(violations, "invalid_engine_family")
    if _compact_text(raw.get("public_claim_status")) not in ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        _append_unique(violations, "public_export_marked_safe")

    violations.extend(_validate_safe_metadata(raw))
    violations.extend(_validate_denied_authority(raw))
    violations.extend(_validate_world_packet(raw))
    violations.extend(_validate_packet_sets(raw))

    for index, item in enumerate(_ensure_list(raw.get("observation_packets"))):
        violations.extend(_validate_observation_packet(item, index))
    for index, item in enumerate(_ensure_list(raw.get("prediction_packets"))):
        violations.extend(_validate_prediction_packet(item, index))
    for index, item in enumerate(_ensure_list(raw.get("reveal_packets"))):
        violations.extend(_validate_reveal_packet(item, index))
    for index, item in enumerate(_ensure_list(raw.get("mutation_packets"))):
        violations.extend(_validate_mutation_packet(item, index))
    for index, item in enumerate(_ensure_list(raw.get("correction_packets"))):
        violations.extend(_validate_correction_packet(item, index))

    calibration_packet = raw.get("forecast_calibration_packet")
    if calibration_packet is not None:
        calibration_validation = validate_forecast_calibration_record_v1(calibration_packet)
        if not calibration_validation.get("valid", False):
            _append_unique(violations, "invalid_forecast_calibration_packet")

    violations.extend(_collect_text_violations(raw))
    blocked = bool(violations)
    summary_text = _summary_text_from_packet(raw, blocked, list(dict.fromkeys(violations)))
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "valid": not blocked,
        "blocked": blocked,
        "violations": list(dict.fromkeys(violations)),
        "violation_count": len(list(dict.fromkeys(violations))),
        "protocol_valid": bool(base.get("blocked") is False),
        "protocol_blocked_labels": list(base.get("blocked_labels", [])),
        "engine_name": _compact_text(raw.get("engine_name")) or ENGINE_NAME_V1,
        "engine_family": _compact_text(raw.get("engine_family")) or ENGINE_FAMILY_V1,
        "research_mode": _compact_text(raw.get("research_mode")) or "internal_exploration",
        "public_claim_status": _compact_text(raw.get("public_claim_status")) or "not_public_claim",
        "safe_metadata_contained": isinstance(raw.get("safe_metadata"), Mapping),
        "denied_authority_contained": isinstance(raw.get("denied_authority"), Mapping),
        "summary_text": _compact_text(summary_text)[:360],
    }


def summarize_unknown_engine_research_run_v1(packet: Any) -> dict[str, Any]:
    validation = validate_unknown_engine_research_run_v1(packet)
    raw = packet if isinstance(packet, Mapping) else {}
    world = _as_mapping(raw.get("world_packet"))
    summary_text = _summary_text_from_packet(raw, validation["blocked"], validation["violations"])
    reveals = _ensure_list(raw.get("reveal_packets"))
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "summary_text": summary_text[:360],
        "blocked": validation["blocked"],
        "violations": validation["violations"],
        "violation_count": validation["violation_count"],
        "engine_name": validation["engine_name"],
        "engine_family": validation["engine_family"],
        "research_mode": validation["research_mode"],
        "public_claim_status": validation["public_claim_status"],
        "world_family": _compact_text(world.get("world_family")) or "unknown",
        "calibration_ready": bool(reveals and _as_mapping(reveals[0]).get("calibration_ready", False)),
    }


def _sanitize_for_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            if lowered not in _ALLOWED_SAFE_TOP_LEVEL_KEYS_V1 and any(fragment in lowered for fragment in _FORBIDDEN_KEY_FRAGMENTS_V1):
                continue
            sanitized[key_text] = _sanitize_for_json(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_for_json(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_for_json(item) for item in value]
    if isinstance(value, set):
        return [_sanitize_for_json(item) for item in sorted(value, key=repr)]
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _FORBIDDEN_TEXT_MARKERS_V1):
            return "redacted"
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else "non_json_safe_float_replaced"
    if value is None or isinstance(value, (int, bool)):
        return value
    return str(value)


def to_unknown_engine_json_safe_v1(packet: Any) -> dict[str, Any]:
    safe = _sanitize_for_json(packet)
    return _json_safe(safe)


def build_initial_unknown_engine_examples_v1() -> list[dict[str, Any]]:
    specs = [
        {"world_family": "symbolic_sequence", "world_id": "world:symbolic-sequence:001", "research_mode": "internal_exploration"},
        {"world_family": "operator_algebra", "world_id": "world:operator-algebra:001", "research_mode": "synthetic_test"},
        {"world_family": "graph_transition", "world_id": "world:graph-transition:001", "research_mode": "calibration_replay"},
        {"world_family": "noise_mixed_signal", "world_id": "world:noise-mixed-signal:001", "research_mode": "internal_exploration"},
        {"world_family": "cellular_grid", "world_id": "world:cellular-grid:001", "research_mode": "synthetic_test"},
        {"world_family": "toy_physics", "world_id": "world:toy-physics:001", "research_mode": "internal_exploration"},
    ]
    return [build_unknown_engine_research_run_v1(spec) for spec in specs]


__all__ = (
    "ENGINE_FAMILY_V1",
    "ENGINE_NAME_V1",
    "HELPER_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "ALLOWED_WORLD_FAMILIES_V1",
    "ALLOWED_MATCH_STATUSES_V1",
    "ALLOWED_MUTATION_TYPES_V1",
    "ALLOWED_ERROR_TYPES_V1",
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
)
