"""Metadata-only helpers for the recursive CognitiveResearchRunV1 protocol.

This module is intentionally pure, deterministic, JSON-safe, and fail-closed.
It validates and summarizes shared research packets without runtime wiring,
tool/provider/search/persistence authority, or engine-specific implementation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

HELPER_TYPE_V1 = "weslr_recursive_cognitive_research_protocol_helpers_v1"
SCHEMA_VERSION_V1 = "cognitive_research_run_v1"
GENERATOR_LOOP_V1 = "RecursiveDiscoveryLoopV1"
DIALECTIC_GENERATOR_LOOP_V1 = "DialecticGeneratorLoopV1"

ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1 = (
    "unknown_modeling",
    "raw_signal_analysis",
    "discovery_generation",
    "reasoning_integrity",
    "calibration_and_forecast",
    "frontier_gap_mapping",
    "human_project_intelligence",
    "governance_and_boundary",
    "recursive_generation",
    "adversarial_pressure",
    "live_signal_ingestion",
    "public_export",
)

LEGACY_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1 = (
    "math",
    "unknown",
    "raw-signal",
    "gap",
    "calibration",
    "chemical/material",
    "biological",
    "medical-boundary",
    "energy/infrastructure",
    "industrial",
    "robotics",
    "manufacturing",
    "RF/signal",
    "semiconductor",
    "cyber-resilience",
    "legal/governance",
    "market systems",
    "language/communication",
    "education/cognition",
    "environmental",
    "construction/architecture",
    "agriculture",
    "business discovery",
    "creative invention",
)

ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1 = (
    "unknown_engine",
    "raw_signal_cartographer",
    "unintelligible_output_analyzer",
    "signal_vs_noise_engine",
    "nonlinear_inspiration_engine",
    "resonance_engine",
    "algorithm_emergence_engine",
    "mutable_axiom_math_engine",
    "operator_forge_engine",
    "invariant_miner",
    "contradiction_furnace",
    "causal_trace_engine",
    "blindspot_engine",
    "calibration_ledger",
    "forecast_error_ledger",
    "gap_cartographer",
    "assumption_excavator",
    "probe_generator",
    "memory_trust_engine",
    "abstraction_ladder",
    "governance_boundary_engine",
    "intent_reconstruction_engine",
    "dialectic_generator_loop",
    "rule_pressure_engine",
    "perspicuity_scorer",
    "live_weird_feed_adapter",
    "public_gap_card_exporter",
)

LEGACY_COGNITIVE_RESEARCH_ENGINE_NAMES_V1 = (
    "UNKNOWN_ENGINE",
    "RAW_SIGNAL_CARTOGRAPHER",
    "UNINTELLIGIBLE_OUTPUT_ANALYZER",
    "SIGNAL_VS_NOISE_ENGINE",
    "ALGORITHM_EMERGENCE_ENGINE",
    "MUTABLE_AXIOM_MATH_ENGINE",
    "OPERATOR_FORGE_ENGINE",
    "INVARIANT_MINER",
    "CONTRADICTION_FURNACE",
    "CAUSAL_TRACE_ENGINE",
    "BLINDSPOT_ENGINE",
    "CALIBRATION_LEDGER",
    "FORECAST_ERROR_LEDGER",
    "GAP_CARTOGRAPHER",
    "ASSUMPTION_EXCAVATOR",
    "PROBE_GENERATOR",
    "MEMORY_TRUST_ENGINE",
    "ABSTRACTION_LADDER",
    "GOVERNANCE_BOUNDARY_ENGINE",
    "INTENT_RECONSTRUCTION_ENGINE",
    "DIALECTIC_GENERATOR_LOOP",
    "RULE_PRESSURE_ENGINE",
    "PERSPICUITY_SCORER",
    "LIVE_WEIRD_FEED_ADAPTER",
    "PUBLIC_GAP_CARD_EXPORTER",
)

_ENGINE_NAME_ALIASES_V1 = {
    name.upper(): name for name in ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1
}

_ENGINE_FAMILY_BY_NAME_V1 = {
    "unknown_engine": "unknown_modeling",
    "raw_signal_cartographer": "raw_signal_analysis",
    "unintelligible_output_analyzer": "reasoning_integrity",
    "signal_vs_noise_engine": "raw_signal_analysis",
    "nonlinear_inspiration_engine": "discovery_generation",
    "resonance_engine": "discovery_generation",
    "algorithm_emergence_engine": "discovery_generation",
    "mutable_axiom_math_engine": "reasoning_integrity",
    "operator_forge_engine": "discovery_generation",
    "invariant_miner": "reasoning_integrity",
    "contradiction_furnace": "reasoning_integrity",
    "causal_trace_engine": "reasoning_integrity",
    "blindspot_engine": "frontier_gap_mapping",
    "calibration_ledger": "calibration_and_forecast",
    "forecast_error_ledger": "calibration_and_forecast",
    "gap_cartographer": "frontier_gap_mapping",
    "assumption_excavator": "frontier_gap_mapping",
    "probe_generator": "discovery_generation",
    "memory_trust_engine": "human_project_intelligence",
    "abstraction_ladder": "reasoning_integrity",
    "governance_boundary_engine": "governance_and_boundary",
    "intent_reconstruction_engine": "human_project_intelligence",
    "dialectic_generator_loop": "recursive_generation",
    "rule_pressure_engine": "adversarial_pressure",
    "perspicuity_scorer": "reasoning_integrity",
    "live_weird_feed_adapter": "live_signal_ingestion",
    "public_gap_card_exporter": "public_export",
}

_ENGINE_FAMILY_ALIASES_V1 = {
    "UNKNOWN_ENGINE": "unknown_modeling",
    "RAW_SIGNAL_CARTOGRAPHER": "raw_signal_analysis",
    "UNINTELLIGIBLE_OUTPUT_ANALYZER": "reasoning_integrity",
    "SIGNAL_VS_NOISE_ENGINE": "raw_signal_analysis",
    "ALGORITHM_EMERGENCE_ENGINE": "discovery_generation",
    "MUTABLE_AXIOM_MATH_ENGINE": "reasoning_integrity",
    "OPERATOR_FORGE_ENGINE": "discovery_generation",
    "INVARIANT_MINER": "reasoning_integrity",
    "CONTRADICTION_FURNACE": "reasoning_integrity",
    "CAUSAL_TRACE_ENGINE": "reasoning_integrity",
    "BLINDSPOT_ENGINE": "frontier_gap_mapping",
    "CALIBRATION_LEDGER": "calibration_and_forecast",
    "FORECAST_ERROR_LEDGER": "calibration_and_forecast",
    "GAP_CARTOGRAPHER": "frontier_gap_mapping",
    "ASSUMPTION_EXCAVATOR": "frontier_gap_mapping",
    "PROBE_GENERATOR": "discovery_generation",
    "MEMORY_TRUST_ENGINE": "human_project_intelligence",
    "ABSTRACTION_LADDER": "reasoning_integrity",
    "GOVERNANCE_BOUNDARY_ENGINE": "governance_and_boundary",
    "INTENT_RECONSTRUCTION_ENGINE": "human_project_intelligence",
    "DIALECTIC_GENERATOR_LOOP": "recursive_generation",
    "RULE_PRESSURE_ENGINE": "adversarial_pressure",
    "PERSPICUITY_SCORER": "reasoning_integrity",
    "LIVE_WEIRD_FEED_ADAPTER": "live_signal_ingestion",
    "PUBLIC_GAP_CARD_EXPORTER": "public_export",
}

ALLOWED_COGNITIVE_RESEARCH_RESEARCH_MODES_V1 = (
    "internal_exploration",
    "synthetic_test",
    "shadow_evaluation",
    "owner_preview",
    "calibration_replay",
    "frontier_mapping",
    "recursive_generation",
    "rule_pressure_test",
    "public_export_blocked",
)

LEGACY_COGNITIVE_RESEARCH_RESEARCH_MODES_V1 = (
    "exploratory",
    "calibration",
    "gap_discovery",
    "raw_signal",
    "invariant_mining",
    "contradiction_analysis",
    "cross_domain_transfer",
    "comparison",
    "simulation",
    "boundary_review",
    "internal_hypothesis",
)

ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1 = (
    "not_public_claim",
    "internal_candidate_only",
    "owner_preview_only",
    "public_export_blocked",
    "public_safe_summary_required",
    "public_gap_card_candidate",
)

LEGACY_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1 = (
    "blocked_internal_only",
    "blocked_non_public",
    "allowed_external_export",
)

ALLOWED_COGNITIVE_RESEARCH_PUBLIC_GAP_CARD_STATUSES_V1 = (
    "not_public_claim",
    "internal_candidate_only",
    "owner_preview_only",
    "public_export_blocked",
    "public_safe_summary_required",
    "public_gap_card_candidate",
)

ALLOWED_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1 = (
    "none",
    "candidate_generator_only",
    "hypothesis_generator_only",
    "translation_helper_only",
    "probe_suggestion_helper_only",
    "resonance_suggestion_helper_only",
    "not_authority",
)

LEGACY_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1 = (
    "helper",
    "validator",
    "summarizer",
    "classifier",
    "json_safe_transformer",
    "example_builder",
    "boundary_guard",
)

ALLOWED_COGNITIVE_RESEARCH_PRESSURE_TYPES_V1 = (
    "edge_case",
    "counterexample",
    "counterexample_search",
    "boundary_case",
    "noise_injection",
    "false_pattern_insertion",
    "scale_shift",
    "delayed_causality",
    "axiom_removal",
    "axiom_weakening",
    "axiom_inversion",
    "axiom_mutation",
    "operator_substitution",
    "contradiction_injection",
    "control_case",
    "randomized_stress",
    "scale_transition",
    "domain_transfer",
    "adversarial_signal",
    "random_control",
    "unknown",
)

ALLOWED_COGNITIVE_RESEARCH_SUGGESTION_STORE_UPDATE_ACTIONS_V1 = (
    "promote",
    "narrow",
    "split",
    "merge",
    "archive",
    "discard",
)

_DENIED_AUTHORITY_KEYS_V1 = (
    "runtime_wiring_authority",
    "chat_responder_authority",
    "final_answer_generation_authority",
    "public_claim_authority",
    "provider_model_call_authority",
    "retrieval_tool_authority",
    "filesystem_authority",
    "network_authority",
    "subprocess_authority",
    "weslr_io_authority",
    "persistence_database_write_authority",
    "real_memory_mutation_authority",
    "real_project_mutation_authority",
    "behavior_pack_promotion_authority",
    "autonomous_self_modification_authority",
    "official_intelligence_claim_authority",
    "public_discovery_claim_authority",
    "external_action_authority",
    "runtime_authority",
    "runtime_execution_authority",
    "tool_authority",
    "provider_authority",
    "search_authority",
    "persistence_authority",
    "dot_weslr_authority",
    "public_export_authority",
    "answer_authority",
    "prediction_authority",
    "official_evaluation_authority",
    "proof_authority",
    "solution_authority",
    "llm_authority",
    "diagnosis_authority",
    "treatment_authority",
    "exploit_authority",
    "malware_authority",
    "credential_theft_authority",
    "investment_authority",
    "trading_authority",
    "legal_authority",
    "memory_mutation_authority",
    "project_mutation_authority",
)

_REQUIRED_TOP_LEVEL_FIELDS_V1 = (
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
)

_FORBIDDEN_PRIVATE_TEXT_MARKERS_V1 = (
    "raw private text",
    "raw private data",
    "raw private project data",
    "private mechanism",
    "hidden system prompt",
    "hidden prompt",
    "system prompt",
    "secret",
    "token=",
    "credential",
    "provider output",
    "model output",
    "search output",
    "runtime state",
    "import-time state",
    ".weslr",
    ".env",
    "chat_responder",
)

_FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1 = (
    "breakthrough",
    "proof",
    "solution",
    "certified",
    "certification",
    "official",
    "public ready",
    "public-ready",
    "solved",
)

_FORBIDDEN_DANGEROUS_PROCEDURAL_MARKERS_V1 = (
    "step-by-step",
    "step 1",
    "procedure",
    "how to synthesize",
    "synthesize",
    "how to exploit",
    "exploit chain",
    "malware",
    "credential theft",
    "attack chain",
    "wetlab",
    "pathogen",
    "dosage",
    "weapon",
)


def allowed_cognitive_research_engine_families_v1() -> tuple[str, ...]:
    return ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1


def allowed_cognitive_research_engine_names_v1() -> tuple[str, ...]:
    return ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1


def allowed_cognitive_research_research_modes_v1() -> tuple[str, ...]:
    return ALLOWED_COGNITIVE_RESEARCH_RESEARCH_MODES_V1


def allowed_cognitive_research_public_claim_statuses_v1() -> tuple[str, ...]:
    return ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1


def allowed_cognitive_research_llm_helper_roles_v1() -> tuple[str, ...]:
    return ALLOWED_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1


def classify_cognitive_research_engine_family_v1(engine_name: Any) -> str | None:
    name = _normalize_engine_name(engine_name)
    if not name:
        return None
    if name in _ENGINE_FAMILY_BY_NAME_V1:
        return _ENGINE_FAMILY_BY_NAME_V1[name]
    if name in _ENGINE_FAMILY_ALIASES_V1:
        return _ENGINE_FAMILY_ALIASES_V1[name]
    return None


def build_default_cognitive_research_denied_authority_v1() -> dict[str, bool]:
    return {key: False for key in _DENIED_AUTHORITY_KEYS_V1}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return " ".join(str(value).split())


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(list(value), key=_compact_text)
    if isinstance(value, Mapping):
        return list(value.values())
    return [value]


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_compact_text)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _compact_text(value)


def to_cognitive_research_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    if overrides:
        data.update(overrides)
    return data


def _normalize_engine_name(engine_name: Any) -> str:
    raw = _compact_text(engine_name)
    if raw in _ENGINE_NAME_ALIASES_V1:
        return _ENGINE_NAME_ALIASES_V1[raw]
    name = raw.lower()
    return name


def _normalize_research_mode(value: Any) -> str:
    mode = _compact_text(value).lower()
    alias_map = {
        "exploratory": "internal_exploration",
        "calibration": "calibration_replay",
        "gap_discovery": "frontier_mapping",
        "raw_signal": "synthetic_test",
        "invariant_mining": "synthetic_test",
        "contradiction_analysis": "shadow_evaluation",
        "cross_domain_transfer": "frontier_mapping",
        "comparison": "shadow_evaluation",
        "simulation": "synthetic_test",
        "boundary_review": "owner_preview",
        "internal_hypothesis": "internal_exploration",
    }
    return alias_map.get(mode, mode)


def _normalize_public_claim_status(value: Any) -> str:
    status = _compact_text(value).lower()
    alias_map = {
        "blocked_internal_only": "public_export_blocked",
        "blocked_non_public": "public_export_blocked",
        "allowed_external_export": "public_gap_card_candidate",
    }
    return alias_map.get(status, status)


def _normalize_helper_role(value: Any) -> str:
    role = _compact_text(value).lower()
    alias_map = {
        "helper": "candidate_generator_only",
        "validator": "not_authority",
        "summarizer": "translation_helper_only",
        "classifier": "not_authority",
        "json_safe_transformer": "translation_helper_only",
        "example_builder": "candidate_generator_only",
        "boundary_guard": "not_authority",
    }
    return alias_map.get(role, role)


def _normalize_public_gap_card_status(value: Any) -> str:
    status = _compact_text(value).lower()
    return status or "public_export_blocked"


def _normalize_denied_authority(value: Any) -> dict[str, bool]:
    mapping = _as_mapping(value)
    normalized = build_default_cognitive_research_denied_authority_v1()
    for key in mapping:
        normalized[str(key)] = _safe_bool(mapping[key])
    return normalized


def _default_boundary_status() -> dict[str, Any]:
    denied = build_default_cognitive_research_denied_authority_v1()
    return {
        "status": "metadata_only",
        "generator_loop": GENERATOR_LOOP_V1,
        "dialectic_loop": DIALECTIC_GENERATOR_LOOP_V1,
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
        "denied_authority": denied,
    }


def _default_safe_metadata(engine_name: str, engine_family: str, research_mode: str) -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_executing": True,
        "non_public": True,
        "no_runtime_wiring": True,
        "no_provider_calls": True,
        "no_tool_execution": True,
        "no_retrieval_execution": True,
        "no_persistence": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_public_claims": True,
        "no_final_answer": True,
        "no_weslr_io": True,
        "no_network": True,
        "no_subprocess": True,
        "no_autonomous_self_modification": True,
        "perspicuity_is_not_a_gate": True,
        "generator_loop": GENERATOR_LOOP_V1,
        "engine_name": engine_name,
        "engine_family": engine_family,
        "research_mode": research_mode,
    }


def _default_source_signal(engine_name: str, source_ref: str, summary: str, source_scope: str) -> dict[str, Any]:
    signal_origin = "metadata_only"
    if engine_name == "live_weird_feed_adapter":
        signal_origin = "live_weird_feed_metadata_only"
    return {
        "signal_id": f"signal-{_stable_digest({'engine_name': engine_name, 'source_ref': source_ref, 'summary': summary, 'scope': source_scope})[:12]}",
        "signal_origin": signal_origin,
        "signal_type": "research_signal",
        "source_ref": source_ref,
        "summary": summary,
        "trust_level": "bounded",
        "poison_risk": "low",
        "injection_risk": "low",
        "raw_content_included": False,
        "raw_content_ref_only": True,
        "normalization_required": True,
    }


def _default_normalization_summary(source_signal: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "normalization_id": f"norm-{_stable_digest(source_signal)[:12]}",
        "normalized": True,
        "loss_notes": [],
        "rejected_markers": [],
        "notes": "metadata-only normalization summary",
    }


def _default_ingestion_summary(source_signal: Mapping[str, Any], engine_name: str) -> dict[str, Any]:
    return {
        "ingestion_id": f"ingest-{_stable_digest({'source': source_signal, 'engine': engine_name})[:12]}",
        "accepted": True,
        "source_scope": source_signal.get("source_scope", "metadata_only"),
        "noise_filters": ["keyword_filter", "trust_check", "poison_check", "injection_check"],
        "gap_labels": [],
        "notes": "metadata-only ingestion summary",
    }


def _default_verification_steps() -> list[str]:
    return ["metadata_only_validation", "json_safe_copy_validation", "boundary_check", "fail_closed_scan"]


def _default_trend_score(packet: Mapping[str, Any]) -> dict[str, Any]:
    novelty = _safe_float(packet.get("perspicuity_score", {}).get("novelty") if isinstance(packet.get("perspicuity_score"), Mapping) else 40.0, 40.0)
    recurrence = _safe_float(packet.get("perspicuity_score", {}).get("recurrence") if isinstance(packet.get("perspicuity_score"), Mapping) else 40.0, 40.0)
    verification = _safe_float(packet.get("perspicuity_score", {}).get("verification_potential") if isinstance(packet.get("perspicuity_score"), Mapping) else 40.0, 40.0)
    resonance = _safe_float(packet.get("perspicuity_score", {}).get("cross_domain_resonance") if isinstance(packet.get("perspicuity_score"), Mapping) else 40.0, 40.0)
    pressure = _safe_float(packet.get("perspicuity_score", {}).get("gap_pressure") if isinstance(packet.get("perspicuity_score"), Mapping) else 40.0, 40.0)
    score = _clamp((novelty + recurrence + verification + resonance + pressure) / 5.0)
    return {
        "score": score,
        "novelty": novelty,
        "recurrence": recurrence,
        "verification_potential": verification,
        "cross_domain_resonance": resonance,
        "gap_pressure": pressure,
        "reason": "metadata-only trend estimate from perspicuity components",
    }


def _default_calibration_record(packet: Mapping[str, Any]) -> dict[str, Any]:
    first_prediction = _ensure_list(packet.get("predictions"))[:1]
    first_outcome = _ensure_list(packet.get("outcomes"))[:1]
    first_correction = _ensure_list(packet.get("corrections"))[:1]
    return {
        "prediction": first_prediction[0] if first_prediction else "pending",
        "expected_outcome": first_prediction[0] if first_prediction else "pending",
        "observed_outcome": first_outcome[0] if first_outcome else "pending",
        "error_type": "metadata_only",
        "correction": first_correction[0] if first_correction else "none",
        "confidence_adjustment": "bounded",
        "lesson": "Calibration is metadata, not authority.",
    }


def _default_suggestion_store_updates(engine_name: str) -> list[dict[str, Any]]:
    return [
        {
            "suggestion_id": f"suggestion-{engine_name}-primary",
            "status_action": "promote",
            "reason": "top candidate for later review",
            "scope_update": "metadata_only",
        }
    ]


def _default_perspicuity_score(packet: Mapping[str, Any]) -> dict[str, Any]:
    source_signal = packet.get("source_signal") if isinstance(packet.get("source_signal"), Mapping) else {}
    signal_density = 70.0 if _compact_text(source_signal.get("summary")) else 40.0
    novelty = 60.0 if packet.get("research_mode") in {"internal_exploration", "recursive_generation", "frontier_mapping"} else 50.0
    gap_pressure = 65.0 if _ensure_list(packet.get("operator_candidates")) or _ensure_list(packet.get("resonance_candidates")) else 45.0
    verification_potential = 55.0 if _ensure_list(packet.get("verification_steps")) else 40.0
    recurrence = 50.0 if _ensure_list(packet.get("observations")) else 35.0
    cross_domain_resonance = 55.0 if _ensure_list(packet.get("nonlinear_inspiration_candidates")) else 40.0
    clarity = _clamp((signal_density + verification_potential) / 2.0)
    score = _clamp((clarity + novelty + gap_pressure + verification_potential + recurrence + cross_domain_resonance) / 6.0)
    return {
        "score": score,
        "clarity": clarity,
        "signal_density": signal_density,
        "novelty": novelty,
        "gap_pressure": gap_pressure,
        "verification_potential": verification_potential,
        "recurrence": recurrence,
        "cross_domain_resonance": cross_domain_resonance,
        "reason": "perspicuity ranks structural usefulness only; never safety allowance",
    }


def build_source_signal_metadata_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    signal_origin = _compact_text(data.get("signal_origin")) or "metadata_only"
    source_ref = _compact_text(data.get("source_ref")) or _compact_text(data.get("input_artifact_ref")) or "artifact:unknown"
    summary = _compact_text(data.get("summary")) or _compact_text(data.get("input_summary")) or "metadata-only source signal"
    engine_name = _normalize_engine_name(data.get("engine_name")) or "unknown_engine"
    signal = {
        "signal_id": _compact_text(data.get("signal_id")) or f"signal-{_stable_digest({'signal_origin': signal_origin, 'source_ref': source_ref, 'summary': summary})[:12]}",
        "signal_origin": signal_origin,
        "signal_type": _compact_text(data.get("signal_type")) or "research_signal",
        "source_ref": source_ref,
        "summary": summary,
        "trust_level": _compact_text(data.get("trust_level")) or "bounded",
        "poison_risk": _compact_text(data.get("poison_risk")) or "low",
        "injection_risk": _compact_text(data.get("injection_risk")) or "low",
        "raw_content_included": _safe_bool(data.get("raw_content_included", False)),
        "raw_content_ref_only": _safe_bool(data.get("raw_content_ref_only", True)),
        "normalization_required": _safe_bool(data.get("normalization_required", True)),
        "engine_name": engine_name,
    }
    return _json_safe(signal)


def build_generated_source_signal_metadata_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    parent_suggestion_id = _compact_text(data.get("parent_suggestion_id"))
    generated_signal_summary = _compact_text(data.get("generated_signal_summary")) or _compact_text(data.get("summary")) or "metadata-only generated source signal"
    mutation_type = _compact_text(data.get("mutation_type")) or "recursive_candidate_mutation"
    generated = {
        "generated_signal_id": _compact_text(data.get("generated_signal_id")) or f"generated-signal-{_stable_digest({'parent': parent_suggestion_id, 'summary': generated_signal_summary, 'mutation': mutation_type})[:12]}",
        "parent_suggestion_id": parent_suggestion_id,
        "generation_reason": _compact_text(data.get("generation_reason")) or "candidate mutation for later pressure testing",
        "mutation_type": mutation_type,
        "expected_pressure": _compact_text(data.get("expected_pressure")) or "edge_case",
        "target_uncertainty": _compact_text(data.get("target_uncertainty")) or "bounded",
        "generated_signal_summary": generated_signal_summary,
        "raw_generated_content_included": _safe_bool(data.get("raw_generated_content_included", False)),
        "safe_to_reingest": _safe_bool(data.get("safe_to_reingest", bool(parent_suggestion_id))),
    }
    return _json_safe(generated)


def build_rule_pressure_test_metadata_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    pressure_type = _compact_text(data.get("pressure_type")) or "edge_case"
    if pressure_type not in ALLOWED_COGNITIVE_RESEARCH_PRESSURE_TYPES_V1:
        pressure_type = "edge_case"
    test = {
        "test_id": _compact_text(data.get("test_id")) or f"pressure-{_stable_digest({'target': data.get('target_rule_or_operator', ''), 'pressure_type': pressure_type})[:12]}",
        "target_rule_or_operator": _compact_text(data.get("target_rule_or_operator")) or "rule_or_operator",
        "pressure_type": pressure_type,
        "mutated_input_summary": _compact_text(data.get("mutated_input_summary")) or "metadata-only mutation",
        "expected_behavior": _compact_text(data.get("expected_behavior")) or "remain bounded",
        "observed_behavior": _compact_text(data.get("observed_behavior")) or "pending",
        "result": _compact_text(data.get("result")) or "pending",
        "failure_mode": _compact_text(data.get("failure_mode")) or "none",
        "scope_update": _compact_text(data.get("scope_update")) or "metadata_only",
    }
    return _json_safe(test)


def build_nonlinear_resonance_candidate_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    candidate = {
        "candidate_id": _compact_text(data.get("candidate_id")) or f"resonance-{_stable_digest({'gap': data.get('source_gap', ''), 'domain': data.get('resonance_domain', '')})[:12]}",
        "source_gap": _compact_text(data.get("source_gap")) or "gap",
        "resonance_domain": _compact_text(data.get("resonance_domain")) or "adjacent_domain",
        "shared_structure": _compact_text(data.get("shared_structure")) or "candidate shared structure",
        "transferred_operator_candidate": _compact_text(data.get("transferred_operator_candidate")) or "candidate operator",
        "intelligibility_bridge": _compact_text(data.get("intelligibility_bridge")) or "toy bridge",
        "toy_example_summary": _compact_text(data.get("toy_example_summary")) or "toy example",
        "where_analogy_breaks": _compact_text(data.get("where_analogy_breaks")) or "analogy limit",
        "novelty_score": _clamp(_safe_float(data.get("novelty_score"), 50.0)),
        "intelligibility_score": _clamp(_safe_float(data.get("intelligibility_score"), 50.0)),
        "testability_score": _clamp(_safe_float(data.get("testability_score"), 50.0)),
        "next_probe": _compact_text(data.get("next_probe")) or "probe the analogy",
    }
    return _json_safe(candidate)


def build_perspicuity_score_metadata_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    clarity = _clamp(_safe_float(data.get("clarity"), 50.0))
    signal_density = _clamp(_safe_float(data.get("signal_density"), 50.0))
    novelty = _clamp(_safe_float(data.get("novelty"), 50.0))
    gap_pressure = _clamp(_safe_float(data.get("gap_pressure"), 50.0))
    verification_potential = _clamp(_safe_float(data.get("verification_potential"), 50.0))
    recurrence = _clamp(_safe_float(data.get("recurrence"), 50.0))
    cross_domain_resonance = _clamp(_safe_float(data.get("cross_domain_resonance"), 50.0))
    score = _clamp(_safe_float(data.get("score"), (clarity + signal_density + novelty + gap_pressure + verification_potential + recurrence + cross_domain_resonance) / 7.0))
    return _json_safe({
        "score": score,
        "clarity": clarity,
        "signal_density": signal_density,
        "novelty": novelty,
        "gap_pressure": gap_pressure,
        "verification_potential": verification_potential,
        "recurrence": recurrence,
        "cross_domain_resonance": cross_domain_resonance,
        "reason": _compact_text(data.get("reason")) or "perspicuity ranks structural usefulness only; never safety allowance",
    })


def _validate_text_field_forbidden(packet: Mapping[str, Any]) -> list[str]:
    blobs: list[str] = []

    def _collect(value: Any) -> None:
        if isinstance(value, Mapping):
            for item in value.values():
                _collect(item)
            return
        if isinstance(value, list):
            for item in value:
                _collect(item)
            return
        if isinstance(value, tuple):
            for item in value:
                _collect(item)
            return
        blobs.append(_compact_text(value).lower())

    _collect(packet)
    text = "\n".join(blobs)
    labels: list[str] = []
    if any(marker in text for marker in _FORBIDDEN_PRIVATE_TEXT_MARKERS_V1):
        labels.append("raw_private_or_hidden_text")
    if any(marker in text for marker in _FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        labels.append("public_claim_language")
    if any(marker in text for marker in _FORBIDDEN_DANGEROUS_PROCEDURAL_MARKERS_V1):
        labels.append("dangerous_procedural_language")
    if "llm as authority" in text or "llm authority" in text:
        labels.append("llm_as_authority")
    if "runtime authority" in text or "runtime wiring authority" in text:
        labels.append("runtime_authority_claim")
    if "tool authority" in text or "provider model call authority" in text:
        labels.append("tool_or_provider_authority_claim")
    if "public export authority" in text or "public claim authority" in text:
        labels.append("public_export_authority_claim")
    return _dedupe_preserve_order(labels)


def _validate_required_fields(packet: Mapping[str, Any]) -> list[str]:
    return [f"missing_{field}" for field in _REQUIRED_TOP_LEVEL_FIELDS_V1 if field not in packet]


def _validate_denied_authority(packet: Mapping[str, Any]) -> list[str]:
    denied = packet.get("denied_authority")
    if not isinstance(denied, Mapping):
        return ["missing_denied_authority"]
    blocked: list[str] = []
    for key in _DENIED_AUTHORITY_KEYS_V1:
        if key not in denied:
            blocked.append(f"missing_denied_authority_{key}")
        elif _safe_bool(denied.get(key)):
            blocked.append(f"denied_authority_granted_{key}")
    return _dedupe_preserve_order(blocked)


def _validate_boundary_status(packet: Mapping[str, Any]) -> list[str]:
    boundary = packet.get("boundary_status")
    if not isinstance(boundary, Mapping):
        return ["invalid_boundary_status_schema"]
    blocked: list[str] = []
    if _compact_text(boundary.get("status")).lower() not in {"metadata_only", "internal_review", "blocked", "non_public"}:
        blocked.append("unknown_boundary_status")
    required_false = (
        "runtime_wiring_authority",
        "chat_responder_authority",
        "final_answer_generation_authority",
        "public_claim_authority",
        "provider_model_call_authority",
        "retrieval_tool_authority",
        "filesystem_authority",
        "network_authority",
        "subprocess_authority",
        "weslr_io_authority",
        "persistence_database_write_authority",
        "real_memory_mutation_authority",
        "real_project_mutation_authority",
        "behavior_pack_promotion_authority",
        "autonomous_self_modification_authority",
        "official_intelligence_claim_authority",
        "public_discovery_claim_authority",
    )
    for key in required_false:
        if key not in boundary:
            blocked.append(f"missing_boundary_status_{key}")
        elif _safe_bool(boundary.get(key)):
            blocked.append(f"boundary_status_grants_{key}")
    return _dedupe_preserve_order(blocked)


def _validate_safe_metadata(packet: Mapping[str, Any]) -> list[str]:
    safe = packet.get("safe_metadata")
    if safe is True:
        return []
    if not isinstance(safe, Mapping):
        return ["unsafe_safe_metadata"]
    if not _safe_bool(safe.get("safe", False)):
        return ["unsafe_safe_metadata"]
    if _safe_bool(safe.get("perspicuity_is_gate", False)) or _safe_bool(safe.get("use_perspicuity_as_gate", False)):
        return ["perspicuity_used_as_gate"]
    return []


def _validate_engine(packet: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    engine_name = _normalize_engine_name(packet.get("engine_name"))
    engine_family = _compact_text(packet.get("engine_family")).lower()
    research_mode = _normalize_research_mode(packet.get("research_mode"))
    public_claim_status = _normalize_public_claim_status(packet.get("public_claim_status"))
    public_gap_card_status = _normalize_public_gap_card_status(packet.get("public_gap_card_status"))
    llm_helper_role = _normalize_helper_role(packet.get("llm_helper_role"))

    if engine_name not in ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1 and engine_name not in _ENGINE_NAME_ALIASES_V1:
        blocked.append("unknown_engine_name")
    canonical_engine = _ENGINE_NAME_ALIASES_V1.get(engine_name, engine_name)
    if canonical_engine not in _ENGINE_FAMILY_BY_NAME_V1:
        blocked.append("unknown_engine_name")
    expected_family = _ENGINE_FAMILY_BY_NAME_V1.get(canonical_engine)
    if engine_family not in set(ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1) | set(LEGACY_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1):
        blocked.append("unknown_engine_family")
    elif expected_family and engine_family != expected_family:
        blocked.append("engine_family_mismatch")

    if research_mode not in set(ALLOWED_COGNITIVE_RESEARCH_RESEARCH_MODES_V1) | set(LEGACY_COGNITIVE_RESEARCH_RESEARCH_MODES_V1):
        blocked.append("unknown_research_mode")
    if public_claim_status not in set(ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1) | set(LEGACY_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1):
        blocked.append("unknown_public_claim_status")
    if public_gap_card_status not in set(ALLOWED_COGNITIVE_RESEARCH_PUBLIC_GAP_CARD_STATUSES_V1):
        blocked.append("unknown_public_gap_card_status")
    if llm_helper_role not in set(ALLOWED_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1) | set(LEGACY_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1):
        blocked.append("unknown_llm_helper_role")

    if canonical_engine == "public_gap_card_exporter" and public_gap_card_status != "public_export_blocked":
        blocked.append("public_gap_card_must_default_blocked")

    return _dedupe_preserve_order(blocked)


def _validate_source_signal(packet: Mapping[str, Any]) -> list[str]:
    source_signal = packet.get("source_signal")
    if not isinstance(source_signal, Mapping):
        return ["missing_source_signal"]
    required = (
        "signal_id",
        "signal_origin",
        "signal_type",
        "source_ref",
        "summary",
        "trust_level",
        "poison_risk",
        "injection_risk",
        "raw_content_included",
        "raw_content_ref_only",
        "normalization_required",
    )
    blocked: list[str] = []
    for field in required:
        if field not in source_signal:
            blocked.append(f"missing_source_signal_{field}")
    if _compact_text(source_signal.get("signal_origin")).lower() == "live_weird_feed_metadata_only":
        if any(field not in source_signal for field in ("trust_level", "poison_risk", "injection_risk")):
            blocked.append("live_feed_trust_poison_injection_gap")
        if not _safe_bool(source_signal.get("raw_content_ref_only", False)):
            blocked.append("live_feed_must_be_ref_only")
    return _dedupe_preserve_order(blocked)


def _validate_generated_source_signals(packet: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    for index, item in enumerate(_ensure_list(packet.get("generated_source_signals"))):
        if not isinstance(item, Mapping):
            blocked.append(f"invalid_generated_source_signal_{index}")
            continue
        for field in (
            "generated_signal_id",
            "parent_suggestion_id",
            "generation_reason",
            "mutation_type",
            "expected_pressure",
            "target_uncertainty",
            "generated_signal_summary",
            "raw_generated_content_included",
            "safe_to_reingest",
        ):
            if field not in item:
                blocked.append(f"missing_generated_source_signal_{index}_{field}")
        if _safe_bool(item.get("safe_to_reingest", False)):
            if not _compact_text(item.get("parent_suggestion_id")):
                blocked.append(f"generated_source_signal_{index}_missing_parent_reference")
            if _safe_bool(item.get("raw_generated_content_included", False)):
                blocked.append(f"generated_source_signal_{index}_raw_content_not_allowed_for_safe_reingest")
    return _dedupe_preserve_order(blocked)


def _validate_rule_pressure_tests(packet: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    for index, item in enumerate(_ensure_list(packet.get("rule_pressure_tests"))):
        if not isinstance(item, Mapping):
            blocked.append(f"invalid_rule_pressure_test_{index}")
            continue
        pressure_type = _compact_text(item.get("pressure_type")).lower()
        if pressure_type not in ALLOWED_COGNITIVE_RESEARCH_PRESSURE_TYPES_V1:
            blocked.append(f"unknown_rule_pressure_type_{index}")
        result = _compact_text(item.get("result")).lower() or "pending"
        if result == "promoted":
            scope_update = _compact_text(item.get("scope_update"))
            if not scope_update:
                blocked.append(f"rule_pressure_promoted_without_scope_update_{index}")
            calibration_record = packet.get("calibration_record")
            if not isinstance(calibration_record, Mapping) or not calibration_record:
                blocked.append(f"rule_pressure_promoted_without_calibration_{index}")
    return _dedupe_preserve_order(blocked)


def _validate_perspicuity_gate(packet: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    score = packet.get("perspicuity_score")
    if not isinstance(score, Mapping):
        return ["invalid_perspicuity_score_schema"]
    if _safe_bool(score.get("used_as_gate", False)):
        blocked.append("perspicuity_used_as_gate")
    if _compact_text(score.get("reason")).lower().find("gate") >= 0 and _safe_bool(score.get("used_as_gate", False)):
        blocked.append("perspicuity_used_as_gate")
    numeric = _safe_float(score.get("score"), -1.0)
    if numeric < 0.0 or numeric > 100.0:
        blocked.append("invalid_perspicuity_score_range")
    return _dedupe_preserve_order(blocked)


def validate_cognitive_research_run_v1(packet: Any) -> dict[str, Any]:
    raw = _as_mapping(packet)
    blocked_labels: list[str] = []

    blocked_labels.extend(_validate_required_fields(raw))
    blocked_labels.extend(_validate_engine(raw))
    blocked_labels.extend(_validate_denied_authority(raw))
    blocked_labels.extend(_validate_safe_metadata(raw))
    blocked_labels.extend(_validate_boundary_status(raw))
    blocked_labels.extend(_validate_source_signal(raw))
    blocked_labels.extend(_validate_generated_source_signals(raw))
    blocked_labels.extend(_validate_rule_pressure_tests(raw))
    blocked_labels.extend(_validate_perspicuity_gate(raw))
    blocked_labels.extend(_validate_text_field_forbidden(raw))

    safe_metadata = raw.get("safe_metadata")
    if isinstance(safe_metadata, Mapping) and _safe_bool(safe_metadata.get("perspicuity_is_not_a_gate", True)) is False:
        blocked_labels.append("perspicuity_used_as_gate")

    engine_name = _normalize_engine_name(raw.get("engine_name"))
    engine_family = _compact_text(raw.get("engine_family")).lower()
    research_mode = _normalize_research_mode(raw.get("research_mode"))
    public_claim_status = _normalize_public_claim_status(raw.get("public_claim_status"))
    llm_helper_role = _normalize_helper_role(raw.get("llm_helper_role"))
    public_gap_card_status = _normalize_public_gap_card_status(raw.get("public_gap_card_status"))
    boundary_status = _as_mapping(raw.get("boundary_status")).get("status", "metadata_only") if isinstance(raw.get("boundary_status"), Mapping) else _compact_text(raw.get("boundary_status"))

    blocked = bool(blocked_labels)
    classification = engine_name if not blocked else "invalid"
    packet_json_safe = _json_safe(raw)
    summary_text = _summary_text_from_packet(raw, blocked, _dedupe_preserve_order(blocked_labels))

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "blocked": blocked,
        "blocked_labels": _dedupe_preserve_order(blocked_labels),
        "classification": classification,
        "engine_name": engine_name,
        "engine_family": engine_family,
        "research_mode": research_mode,
        "public_claim_status": public_claim_status,
        "public_gap_card_status": public_gap_card_status,
        "llm_helper_role": llm_helper_role,
        "boundary_status": boundary_status,
        "summary_text": summary_text,
        "packet": packet_json_safe,
    }


def _summary_text_from_packet(packet: Mapping[str, Any], blocked: bool, blocked_labels: list[str]) -> str:
    engine_name = _normalize_engine_name(packet.get("engine_name")) or "unknown_engine"
    engine_family = _compact_text(packet.get("engine_family")).lower() or "unknown_modeling"
    research_mode = _normalize_research_mode(packet.get("research_mode")) or "internal_exploration"
    source_scope = _compact_text(packet.get("source_scope")) or "metadata_only"
    input_artifact_ref = _compact_text(packet.get("input_artifact_ref")) or "artifact:unknown"
    input_artifact_type = _compact_text(packet.get("input_artifact_type")) or "artifact"
    source_signal = packet.get("source_signal") if isinstance(packet.get("source_signal"), Mapping) else {}
    forbidden_labels = _validate_text_field_forbidden(packet)
    redacted = bool(forbidden_labels)
    source_summary = "redacted" if redacted else (_compact_text(source_signal.get("summary")) if isinstance(source_signal, Mapping) else "")
    artifact_ref = "redacted" if redacted else input_artifact_ref
    trend_score = packet.get("trend_score") if isinstance(packet.get("trend_score"), Mapping) else {}
    trend_value = _safe_float(trend_score.get("score"), 0.0) if isinstance(trend_score, Mapping) else 0.0
    public_status = _compact_text(packet.get("public_claim_status")) or "public_export_blocked"
    gap_status = _compact_text(packet.get("public_gap_card_status")) or "public_export_blocked"
    summary = (
        f"Cognitive research run: engine={engine_name}; family={engine_family}; mode={research_mode}; "
        f"source={source_scope}; artifact={input_artifact_type}:{artifact_ref}; "
        f"signal={source_summary or 'metadata-only'}; public={public_status}; gap_card={gap_status}; trend={trend_value:.1f}."
    )
    if blocked:
        preview = ", ".join(blocked_labels[:4])
        return f"Blocked cognitive research run: {preview or 'validation failed'}. {summary}"
    return summary


def summarize_cognitive_research_run_v1(packet: Any) -> dict[str, Any]:
    validation = validate_cognitive_research_run_v1(packet)
    raw = _as_mapping(packet)
    summary_text = _summary_text_from_packet(raw, validation["blocked"], validation["blocked_labels"])
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "summary_text": _compact_text(summary_text)[:320],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "classification": validation["classification"],
        "engine_name": validation["engine_name"],
        "engine_family": validation["engine_family"],
        "research_mode": validation["research_mode"],
        "public_claim_status": validation["public_claim_status"],
        "public_gap_card_status": validation["public_gap_card_status"],
        "llm_helper_role": validation["llm_helper_role"],
        "boundary_status": validation["boundary_status"],
        "packet": validation["packet"],
    }


def build_cognitive_research_run_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    engine_name = _normalize_engine_name(data.get("engine_name")) or "unknown_engine"
    engine_family = _compact_text(data.get("engine_family")).lower() or classify_cognitive_research_engine_family_v1(engine_name) or "unknown_modeling"
    research_mode = _normalize_research_mode(data.get("research_mode")) or "internal_exploration"
    source_scope = _compact_text(data.get("source_scope")) or "metadata_only"
    input_artifact_ref = _compact_text(data.get("input_artifact_ref")) or "artifact:unknown"
    input_artifact_type = _compact_text(data.get("input_artifact_type")) or "artifact"
    input_summary = _compact_text(data.get("input_summary")) or "metadata-only cognitive research input"
    source_signal = data.get("source_signal")
    if not isinstance(source_signal, Mapping):
        source_signal = _default_source_signal(engine_name, input_artifact_ref, input_summary, source_scope)
    source_signal = build_source_signal_metadata_v1(source_signal, engine_name=engine_name, source_ref=input_artifact_ref, summary=input_summary, source_scope=source_scope)
    normalization_summary = data.get("normalization_summary")
    if not isinstance(normalization_summary, Mapping):
        normalization_summary = _default_normalization_summary(source_signal)
    ingestion_summary = data.get("ingestion_summary")
    if not isinstance(ingestion_summary, Mapping):
        ingestion_summary = _default_ingestion_summary(source_signal, engine_name)
    observations = _ensure_list(data.get("observations"))
    extracted_signals = _ensure_list(data.get("extracted_signals"))
    motif_candidates = _ensure_list(data.get("motif_candidates"))
    operator_candidates = _ensure_list(data.get("operator_candidates"))
    invariant_candidates = _ensure_list(data.get("invariant_candidates"))
    resonance_candidates = _ensure_list(data.get("resonance_candidates"))
    nonlinear_inspiration_candidates = _ensure_list(data.get("nonlinear_inspiration_candidates"))
    hypotheses = _ensure_list(data.get("hypotheses"))
    predictions = _ensure_list(data.get("predictions"))
    confidence_map = _json_safe(data.get("confidence_map")) if data.get("confidence_map") is not None else {}
    uncertainty_map = _json_safe(data.get("uncertainty_map")) if data.get("uncertainty_map") is not None else {}
    verification_steps = _ensure_list(data.get("verification_steps")) or _default_verification_steps()
    human_verification_steps = _ensure_list(data.get("human_verification_steps")) or ["owner_preview_review"]
    machine_verification_steps = _ensure_list(data.get("machine_verification_steps")) or ["py_compile", "pytest", "release_gate", "release_check"]
    falsification_probes = _ensure_list(data.get("falsification_probes")) or ["counterexample", "edge_case"]
    probes = _ensure_list(data.get("probes"))
    mutations = _ensure_list(data.get("mutations"))
    generated_source_signals = _ensure_list(data.get("generated_source_signals"))
    if not generated_source_signals and data.get("parent_suggestion_id"):
        generated_source_signals = [build_generated_source_signal_metadata_v1(data)]
    rule_pressure_tests = _ensure_list(data.get("rule_pressure_tests"))
    if not rule_pressure_tests and data.get("target_rule_or_operator"):
        rule_pressure_tests = [build_rule_pressure_test_metadata_v1(data)]
    perspicuity_score = data.get("perspicuity_score")
    if not isinstance(perspicuity_score, Mapping):
        perspicuity_score = build_perspicuity_score_metadata_v1(data)
    trend_score = data.get("trend_score")
    if not isinstance(trend_score, Mapping):
        trend_score = _default_trend_score({"perspicuity_score": perspicuity_score, **data})
    outcomes = _ensure_list(data.get("outcomes"))
    corrections = _ensure_list(data.get("corrections"))
    compressed_lesson = _compact_text(data.get("compressed_lesson")) or "Internal research learns by validating structure, not by claiming authority."
    next_experiments = _ensure_list(data.get("next_experiments"))
    suggestion_store_updates = _ensure_list(data.get("suggestion_store_updates")) or _default_suggestion_store_updates(engine_name)
    calibration_record = data.get("calibration_record")
    if not isinstance(calibration_record, Mapping):
        calibration_record = _default_calibration_record({"predictions": predictions, "outcomes": outcomes, "corrections": corrections})
    public_claim_status = _normalize_public_claim_status(data.get("public_claim_status")) or "public_export_blocked"
    public_gap_card_status = _normalize_public_gap_card_status(data.get("public_gap_card_status")) or "public_export_blocked"
    llm_helper_role = _normalize_helper_role(data.get("llm_helper_role")) or "candidate_generator_only"
    boundary_status = data.get("boundary_status")
    if not isinstance(boundary_status, Mapping):
        boundary_status = _default_boundary_status()
    denied_authority = _normalize_denied_authority(data.get("denied_authority") if data.get("denied_authority") is not None else build_default_cognitive_research_denied_authority_v1())
    safe_metadata = data.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        safe_metadata = _default_safe_metadata(engine_name, engine_family, research_mode)

    packet: dict[str, Any] = {
        "schema_version": _compact_text(data.get("schema_version")) or SCHEMA_VERSION_V1,
        "run_id": _compact_text(data.get("run_id")),
        "engine_name": engine_name,
        "engine_family": engine_family,
        "research_mode": research_mode,
        "source_scope": source_scope,
        "input_artifact_ref": input_artifact_ref,
        "input_artifact_type": input_artifact_type,
        "input_summary": input_summary,
        "source_signal": source_signal,
        "normalization_summary": _json_safe(normalization_summary),
        "ingestion_summary": _json_safe(ingestion_summary),
        "observations": _json_safe(observations),
        "extracted_signals": _json_safe(extracted_signals),
        "motif_candidates": _json_safe(motif_candidates),
        "operator_candidates": _json_safe(operator_candidates),
        "invariant_candidates": _json_safe(invariant_candidates),
        "resonance_candidates": _json_safe(resonance_candidates),
        "nonlinear_inspiration_candidates": _json_safe(nonlinear_inspiration_candidates),
        "hypotheses": _json_safe(hypotheses),
        "predictions": _json_safe(predictions),
        "confidence_map": confidence_map,
        "uncertainty_map": uncertainty_map,
        "verification_steps": _json_safe(verification_steps),
        "human_verification_steps": _json_safe(human_verification_steps),
        "machine_verification_steps": _json_safe(machine_verification_steps),
        "falsification_probes": _json_safe(falsification_probes),
        "probes": _json_safe(probes),
        "mutations": _json_safe(mutations),
        "generated_source_signals": _json_safe(generated_source_signals),
        "rule_pressure_tests": _json_safe(rule_pressure_tests),
        "perspicuity_score": _json_safe(perspicuity_score),
        "trend_score": _json_safe(trend_score),
        "outcomes": _json_safe(outcomes),
        "corrections": _json_safe(corrections),
        "compressed_lesson": compressed_lesson,
        "next_experiments": _json_safe(next_experiments),
        "suggestion_store_updates": _json_safe(suggestion_store_updates),
        "calibration_record": _json_safe(calibration_record),
        "llm_helper_role": llm_helper_role,
        "public_claim_status": public_claim_status,
        "public_gap_card_status": public_gap_card_status,
        "boundary_status": _json_safe(boundary_status),
        "denied_authority": denied_authority,
        "safe_metadata": _json_safe(safe_metadata),
        "domain": _compact_text(data.get("domain")) or "recursive research",
        "domain_subtype": _compact_text(data.get("domain_subtype")) or "metadata-only",
        "system_level": _compact_text(data.get("system_level")) or "component",
        "artifact_scale": _compact_text(data.get("artifact_scale")) or "bounded artifact",
        "constraint_map": _json_safe(data.get("constraint_map")) if data.get("constraint_map") is not None else {"runtime": "denied", "tool": "denied", "provider": "denied", "search": "denied", "persistence": "denied", "public_claims": "blocked", "answer_authority": "denied"},
        "safety_boundary": _json_safe(data.get("safety_boundary")) if data.get("safety_boundary") is not None else {"mode": "metadata_only", "non_actionable": True},
        "hazard_flags": _json_safe(data.get("hazard_flags")) if data.get("hazard_flags") is not None else [],
        "validation_route": _json_safe(data.get("validation_route")) if data.get("validation_route") is not None else ["metadata_only_validation", "fail_closed_safety_validation", "json_safe_copy_validation"],
        "required_expert_review": _safe_bool(data.get("required_expert_review", False)),
        "source_requirements": _json_safe(data.get("source_requirements")) if data.get("source_requirements") is not None else {"provenance_required": True, "raw_storage_allowed": False, "side_effect_free": True},
        "experiment_type": _compact_text(data.get("experiment_type")) or "metadata_only",
        "simulation_before_real_world": _safe_bool(data.get("simulation_before_real_world", True)),
        "non_actionable_research_only": _safe_bool(data.get("non_actionable_research_only", True)),
        "forbidden_action_notes": _json_safe(data.get("forbidden_action_notes")) if data.get("forbidden_action_notes") is not None else [],
        "cross_domain_analogies": _json_safe(data.get("cross_domain_analogies")) if data.get("cross_domain_analogies") is not None else [],
        "candidate_transfer_patterns": _json_safe(data.get("candidate_transfer_patterns")) if data.get("candidate_transfer_patterns") is not None else [],
        "failure_mode_map": _json_safe(data.get("failure_mode_map")) if data.get("failure_mode_map") is not None else [],
        "measurement_gap_map": _json_safe(data.get("measurement_gap_map")) if data.get("measurement_gap_map") is not None else [],
        "operator_gap_map": _json_safe(data.get("operator_gap_map")) if data.get("operator_gap_map") is not None else [],
        "language_gap_map": _json_safe(data.get("language_gap_map")) if data.get("language_gap_map") is not None else [],
        "unknown_unknowns": _json_safe(data.get("unknown_unknowns")) if data.get("unknown_unknowns") is not None else [],
    }

    if not packet["run_id"]:
        packet["run_id"] = f"cr-{_stable_digest({'engine_name': packet['engine_name'], 'engine_family': packet['engine_family'], 'research_mode': packet['research_mode'], 'source_ref': packet['input_artifact_ref']})[:16]}"

    return _json_safe(packet)


def build_initial_cognitive_research_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    specs = [
        {
            "engine_name": "unknown_engine",
            "engine_family": "unknown_modeling",
            "research_mode": "internal_exploration",
            "input_artifact_ref": "artifact:unknown-engine-001",
            "input_artifact_type": "signal-log",
            "input_summary": "Hidden-rule world with a contradiction cloud and a bounded hypothesis.",
            "hypotheses": ["A latent rule may be driving the contradiction."],
            "probes": ["observe -> predict -> reveal -> correct"],
            "compressed_lesson": "Unknowns stay unknown until probes earn them.",
        },
        {
            "engine_name": "raw_signal_cartographer",
            "engine_family": "raw_signal_analysis",
            "research_mode": "synthetic_test",
            "input_artifact_ref": "artifact:raw-signal-001",
            "input_artifact_type": "corpus",
            "input_summary": "Massive symbolic stream summarized by artifact reference only.",
            "motif_candidates": ["recurring symbol cluster"],
            "compressed_lesson": "Signal cartography begins with preservation.",
        },
        {
            "engine_name": "unintelligible_output_analyzer",
            "engine_family": "reasoning_integrity",
            "research_mode": "shadow_evaluation",
            "input_artifact_ref": "artifact:unintelligible-001",
            "input_artifact_type": "sequence",
            "input_summary": "Unintelligible operator sequence with competing translations.",
            "operator_candidates": ["candidate translation layer"],
            "compressed_lesson": "Strange output is not empty output.",
        },
        {
            "engine_name": "signal_vs_noise_engine",
            "engine_family": "raw_signal_analysis",
            "research_mode": "synthetic_test",
            "input_artifact_ref": "artifact:signal-noise-001",
            "input_artifact_type": "packet",
            "input_summary": "Noise versus hidden grammar in a compact packet.",
            "extracted_signals": ["weak grammar"],
            "compressed_lesson": "Noise filters should not erase weak structure.",
        },
        {
            "engine_name": "nonlinear_inspiration_engine",
            "engine_family": "discovery_generation",
            "research_mode": "frontier_mapping",
            "input_artifact_ref": "artifact:nonlinear-inspiration-001",
            "input_artifact_type": "gap-card",
            "input_summary": "Nonlinear inspiration from a distant resonance domain.",
            "nonlinear_inspiration_candidates": [build_nonlinear_resonance_candidate_v1({"source_gap": "gap:bridge", "resonance_domain": "adjacent domain", "shared_structure": "shared transformation", "transferred_operator_candidate": "bridge operator", "intelligibility_bridge": "toy bridge", "toy_example_summary": "toy example", "where_analogy_breaks": "analogy limit", "next_probe": "probe the bridge"})],
            "compressed_lesson": "Novel bridges need testable bridges.",
        },
        {
            "engine_name": "resonance_engine",
            "engine_family": "discovery_generation",
            "research_mode": "frontier_mapping",
            "input_artifact_ref": "artifact:resonance-001",
            "input_artifact_type": "bridge-card",
            "input_summary": "Nonlinear resonance candidate with an intelligibility bridge.",
            "resonance_candidates": [build_nonlinear_resonance_candidate_v1({"source_gap": "gap:resonance", "resonance_domain": "adjacent domain", "shared_structure": "shared pressure", "transferred_operator_candidate": "candidate operator", "intelligibility_bridge": "toy bridge", "toy_example_summary": "toy example", "where_analogy_breaks": "scope break", "next_probe": "probe the resonance"})],
            "compressed_lesson": "A good analogy survives pressure.",
        },
        {
            "engine_name": "algorithm_emergence_engine",
            "engine_family": "discovery_generation",
            "research_mode": "recursive_generation",
            "input_artifact_ref": "artifact:algorithm-emergence-001",
            "input_artifact_type": "procedure",
            "input_summary": "Primitive rules plus a stopping condition.",
            "mutations": ["primitive rewrite"],
            "compressed_lesson": "Algorithms emerge from constrained mutation.",
        },
        {
            "engine_name": "mutable_axiom_math_engine",
            "engine_family": "reasoning_integrity",
            "research_mode": "shadow_evaluation",
            "input_artifact_ref": "artifact:mutable-axiom-001",
            "input_artifact_type": "axiom-set",
            "input_summary": "Original axioms and their fractures under mutation.",
            "operator_candidates": ["weakened axiom"],
            "compressed_lesson": "Axiom mutation reveals fracture points.",
        },
        {
            "engine_name": "operator_forge_engine",
            "engine_family": "discovery_generation",
            "research_mode": "recursive_generation",
            "input_artifact_ref": "artifact:operator-forge-001",
            "input_artifact_type": "operator-lab",
            "input_summary": "Candidate operator with input/output types and failure probes.",
            "operator_candidates": ["candidate new operator"],
            "compressed_lesson": "Operators need examples and failures.",
        },
        {
            "engine_name": "invariant_miner",
            "engine_family": "reasoning_integrity",
            "research_mode": "synthetic_test",
            "input_artifact_ref": "artifact:invariant-001",
            "input_artifact_type": "corpus",
            "input_summary": "Stable relation under mutation and transfer.",
            "invariant_candidates": ["stable relation"],
            "compressed_lesson": "Stability is a signal.",
        },
        {
            "engine_name": "contradiction_furnace",
            "engine_family": "reasoning_integrity",
            "research_mode": "shadow_evaluation",
            "input_artifact_ref": "artifact:contradiction-001",
            "input_artifact_type": "notes",
            "input_summary": "Real contradiction versus apparent contradiction.",
            "hypotheses": ["a missing bridge may exist"],
            "compressed_lesson": "A contradiction can hide a new distinction.",
        },
        {
            "engine_name": "causal_trace_engine",
            "engine_family": "reasoning_integrity",
            "research_mode": "calibration_replay",
            "input_artifact_ref": "artifact:causal-trace-001",
            "input_artifact_type": "corpus",
            "input_summary": "Trace effect to cause without assuming a complete explanation.",
            "verification_steps": ["trace", "replay", "compare"],
            "compressed_lesson": "Causal traces are hypotheses, not authority.",
        },
        {
            "engine_name": "blindspot_engine",
            "engine_family": "frontier_gap_mapping",
            "research_mode": "frontier_mapping",
            "input_artifact_ref": "artifact:blindspot-001",
            "input_artifact_type": "report",
            "input_summary": "Blind spots, missing operators, and boundary failures.",
            "measurement_gap_map": ["missing measurement zone"],
            "operator_gap_map": ["missing operator"],
            "compressed_lesson": "A gap is an object.",
        },
        {
            "engine_name": "calibration_ledger",
            "engine_family": "calibration_and_forecast",
            "research_mode": "calibration_replay",
            "input_artifact_ref": "artifact:calibration-ledger-001",
            "input_artifact_type": "ledger",
            "input_summary": "Forecast error and confidence correction metadata only.",
            "confidence_map": {"initial": 30, "corrected": 60},
            "uncertainty_map": {"notes": "bounded uncertainty"},
            "compressed_lesson": "Calibration improves future judgment.",
        },
        {
            "engine_name": "forecast_error_ledger",
            "engine_family": "calibration_and_forecast",
            "research_mode": "calibration_replay",
            "input_artifact_ref": "artifact:forecast-error-001",
            "input_artifact_type": "ledger",
            "input_summary": "Outcome mismatch and compressed lesson metadata only.",
            "predictions": ["branch A"],
            "outcomes": ["branch B"],
            "corrections": ["adjust confidence downward"],
            "compressed_lesson": "Error records future confidence.",
        },
        {
            "engine_name": "gap_cartographer",
            "engine_family": "frontier_gap_mapping",
            "research_mode": "frontier_mapping",
            "input_artifact_ref": "artifact:gap-001",
            "input_artifact_type": "gap-card",
            "input_summary": "Candidate blind spot and next probe.",
            "falsification_probes": ["counterexample"],
            "compressed_lesson": "Gaps deserve probes.",
        },
        {
            "engine_name": "assumption_excavator",
            "engine_family": "frontier_gap_mapping",
            "research_mode": "frontier_mapping",
            "input_artifact_ref": "artifact:assumption-001",
            "input_artifact_type": "notes",
            "input_summary": "Hidden assumptions and scope breaks.",
            "hypotheses": ["an assumption is silently doing the work"],
            "compressed_lesson": "Assumptions can be excavated.",
        },
        {
            "engine_name": "probe_generator",
            "engine_family": "discovery_generation",
            "research_mode": "synthetic_test",
            "input_artifact_ref": "artifact:probe-001",
            "input_artifact_type": "corpus",
            "input_summary": "Probe labels for missing measurements and validation.",
            "probes": ["probe the missing bridge"],
            "compressed_lesson": "Probes should target uncertainty.",
        },
        {
            "engine_name": "memory_trust_engine",
            "engine_family": "human_project_intelligence",
            "research_mode": "owner_preview",
            "input_artifact_ref": "artifact:memory-001",
            "input_artifact_type": "state-snapshot",
            "input_summary": "Memory/reference relationship with stale-state detection.",
            "verification_steps": ["source check", "staleness check"],
            "compressed_lesson": "Memory needs trust boundaries.",
        },
        {
            "engine_name": "abstraction_ladder",
            "engine_family": "reasoning_integrity",
            "research_mode": "shadow_evaluation",
            "input_artifact_ref": "artifact:abstraction-001",
            "input_artifact_type": "ladder",
            "input_summary": "Compression ladder from concrete to abstract.",
            "compressed_lesson": "Abstraction should preserve structure.",
        },
        {
            "engine_name": "governance_boundary_engine",
            "engine_family": "governance_and_boundary",
            "research_mode": "owner_preview",
            "input_artifact_ref": "artifact:governance-001",
            "input_artifact_type": "boundary-doc",
            "input_summary": "Boundary routing and operator review metadata only.",
            "compressed_lesson": "Governance keeps research bounded.",
        },
        {
            "engine_name": "intent_reconstruction_engine",
            "engine_family": "human_project_intelligence",
            "research_mode": "owner_preview",
            "input_artifact_ref": "artifact:intent-001",
            "input_artifact_type": "project-note",
            "input_summary": "Project-state intention reconstruction from sparse metadata.",
            "compressed_lesson": "Intent needs evidence, not guesswork.",
        },
        {
            "engine_name": "dialectic_generator_loop",
            "engine_family": "recursive_generation",
            "research_mode": "recursive_generation",
            "input_artifact_ref": "artifact:dialectic-001",
            "input_artifact_type": "generator-loop",
            "input_summary": "Top suggestion mutated into a new source signal candidate.",
            "generated_source_signals": [build_generated_source_signal_metadata_v1({"parent_suggestion_id": "suggestion-dialectic-001", "generation_reason": "loop mutation", "mutation_type": "dialectic_rewrite", "expected_pressure": "counterexample", "target_uncertainty": "bounded", "generated_signal_summary": "mutated source signal", "safe_to_reingest": True})],
            "compressed_lesson": "Loops need reingest-safe mutations.",
        },
        {
            "engine_name": "rule_pressure_engine",
            "engine_family": "adversarial_pressure",
            "research_mode": "rule_pressure_test",
            "input_artifact_ref": "artifact:rule-pressure-001",
            "input_artifact_type": "pressure-test",
            "input_summary": "Candidate rule pressure with scope update and calibration.",
            "rule_pressure_tests": [build_rule_pressure_test_metadata_v1({"target_rule_or_operator": "candidate rule", "pressure_type": "counterexample_search", "mutated_input_summary": "mutated input", "expected_behavior": "stay bounded", "observed_behavior": "stable", "result": "narrowed", "failure_mode": "none", "scope_update": "narrow scope"})],
            "calibration_record": {"prediction": "stable", "expected_outcome": "stable", "observed_outcome": "stable", "error_type": "none", "correction": "none", "confidence_adjustment": "none", "lesson": "pressure can narrow scope"},
            "compressed_lesson": "Rule pressure can narrow scope.",
        },
        {
            "engine_name": "perspicuity_scorer",
            "engine_family": "reasoning_integrity",
            "research_mode": "synthetic_test",
            "input_artifact_ref": "artifact:perspicuity-001",
            "input_artifact_type": "score-card",
            "input_summary": "Perspicuity ranking for structural usefulness only.",
            "perspicuity_score": build_perspicuity_score_metadata_v1({"clarity": 70, "signal_density": 75, "novelty": 60, "gap_pressure": 65, "verification_potential": 72, "recurrence": 58, "cross_domain_resonance": 61}),
            "compressed_lesson": "Scoring ranks usefulness, not safety.",
        },
        {
            "engine_name": "live_weird_feed_adapter",
            "engine_family": "live_signal_ingestion",
            "research_mode": "synthetic_test",
            "input_artifact_ref": "artifact:live-feed-001",
            "input_artifact_type": "adapter-metadata",
            "input_summary": "Future live weird-feed metadata adapter without network ingestion.",
            "source_signal": build_source_signal_metadata_v1({"signal_origin": "live_weird_feed_metadata_only", "source_ref": "feed:future", "summary": "live weird feed metadata only", "trust_level": "reviewed", "poison_risk": "low", "injection_risk": "low", "raw_content_included": False, "raw_content_ref_only": True, "normalization_required": True}),
            "compressed_lesson": "Adapters must stay metadata-only here.",
        },
        {
            "engine_name": "public_gap_card_exporter",
            "engine_family": "public_export",
            "research_mode": "public_export_blocked",
            "input_artifact_ref": "artifact:public-gap-001",
            "input_artifact_type": "export-card",
            "input_summary": "Public gap-card candidate blocked from public claim by default.",
            "public_claim_status": "public_export_blocked",
            "public_gap_card_status": "public_export_blocked",
            "compressed_lesson": "Public export stays blocked until separately governed.",
        },
    ]
    for spec in specs:
        packet = build_cognitive_research_run_v1(
            spec,
            source_scope="metadata_only",
            llm_helper_role="candidate_generator_only",
            public_claim_status=spec.get("public_claim_status", "internal_candidate_only"),
            public_gap_card_status=spec.get("public_gap_card_status", "public_export_blocked"),
            safe_metadata={"safe": True, "metadata_only": True, "generator_loop": GENERATOR_LOOP_V1},
            denied_authority=build_default_cognitive_research_denied_authority_v1(),
        )
        examples.append(packet)
    return examples
