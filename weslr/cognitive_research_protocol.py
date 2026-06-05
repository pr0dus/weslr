"""Metadata-only helpers for the shared CognitiveResearchRunV1 protocol.

This module is intentionally pure, deterministic, JSON-safe, and fail-closed.
It validates and summarizes shared research packets without runtime wiring,
tool/provider/search/persistence authority, or engine-specific implementation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

HELPER_TYPE_V1 = "weslr_cognitive_research_protocol_helpers_v1"
SCHEMA_VERSION_V1 = "cognitive_research_run_v1"

ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1 = (
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
    "CHEMICAL_SPACE_CARTOGRAPHER",
    "MATERIALS_DISCOVERY_ENGINE",
    "BIOLOGICAL_SYSTEMS_ANALYZER",
    "MEDICAL_REASONING_BOUNDARY_ENGINE",
    "ENERGY_SYSTEMS_DISCOVERY_ENGINE",
    "INDUSTRIAL_PROCESS_MINER",
    "ROBOTICS_EMBODIMENT_ENGINE",
    "MANUFACTURING_PATTERN_ENGINE",
    "RF_SIGNAL_WORLD_MODEL_ENGINE",
    "SEMICONDUCTOR_SYSTEM_ENGINE",
    "CYBER_RESILIENCE_ENGINE",
    "LEGAL_GOVERNANCE_GAP_ENGINE",
    "MARKET_SYSTEM_DYNAMICS_ENGINE",
    "LANGUAGE_PROTOCOL_ENGINE",
    "EDUCATION_COGNITION_ENGINE",
    "ENVIRONMENTAL_SYSTEM_ENGINE",
    "CONSTRUCTION_ARCHITECTURE_ENGINE",
    "AGRICULTURE_SYSTEM_ENGINE",
    "BUSINESS_MODEL_DISCOVERY_ENGINE",
    "CREATIVE_INVENTION_ENGINE",
)

ALLOWED_COGNITIVE_RESEARCH_MODES_V1 = (
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
    "blocked_internal_only",
    "blocked_non_public",
    "allowed_external_export",
)

ALLOWED_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1 = (
    "helper",
    "validator",
    "summarizer",
    "classifier",
    "json_safe_transformer",
    "example_builder",
    "boundary_guard",
)

ALLOWED_COGNITIVE_RESEARCH_BOUNDARY_STATUSES_V1 = (
    "metadata_only",
    "internal_review",
    "blocked",
    "non_public",
)

_DENIED_AUTHORITY_KEYS_V1 = (
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
    "external_action_authority",
)

_ENGINE_ALLOWED_FAMILIES_V1 = {
    "UNKNOWN_ENGINE": ("unknown",),
    "RAW_SIGNAL_CARTOGRAPHER": ("raw-signal",),
    "UNINTELLIGIBLE_OUTPUT_ANALYZER": ("raw-signal", "gap"),
    "SIGNAL_VS_NOISE_ENGINE": ("raw-signal",),
    "ALGORITHM_EMERGENCE_ENGINE": ("gap", "creative invention"),
    "MUTABLE_AXIOM_MATH_ENGINE": ("math",),
    "OPERATOR_FORGE_ENGINE": ("math", "gap"),
    "INVARIANT_MINER": ("math",),
    "CONTRADICTION_FURNACE": ("math", "gap"),
    "CAUSAL_TRACE_ENGINE": ("gap", "calibration"),
    "BLINDSPOT_ENGINE": ("gap",),
    "CALIBRATION_LEDGER": ("calibration",),
    "FORECAST_ERROR_LEDGER": ("calibration",),
    "GAP_CARTOGRAPHER": ("gap",),
    "ASSUMPTION_EXCAVATOR": ("gap", "unknown"),
    "PROBE_GENERATOR": ("gap", "unknown"),
    "MEMORY_TRUST_ENGINE": ("calibration", "unknown"),
    "ABSTRACTION_LADDER": ("math", "gap"),
    "GOVERNANCE_BOUNDARY_ENGINE": ("legal/governance",),
    "INTENT_RECONSTRUCTION_ENGINE": ("language/communication", "education/cognition"),
    "CHEMICAL_SPACE_CARTOGRAPHER": ("chemical/material",),
    "MATERIALS_DISCOVERY_ENGINE": ("chemical/material",),
    "BIOLOGICAL_SYSTEMS_ANALYZER": ("biological",),
    "MEDICAL_REASONING_BOUNDARY_ENGINE": ("medical-boundary",),
    "ENERGY_SYSTEMS_DISCOVERY_ENGINE": ("energy/infrastructure",),
    "INDUSTRIAL_PROCESS_MINER": ("industrial",),
    "ROBOTICS_EMBODIMENT_ENGINE": ("robotics",),
    "MANUFACTURING_PATTERN_ENGINE": ("manufacturing",),
    "RF_SIGNAL_WORLD_MODEL_ENGINE": ("RF/signal",),
    "SEMICONDUCTOR_SYSTEM_ENGINE": ("semiconductor",),
    "CYBER_RESILIENCE_ENGINE": ("cyber-resilience",),
    "LEGAL_GOVERNANCE_GAP_ENGINE": ("legal/governance",),
    "MARKET_SYSTEM_DYNAMICS_ENGINE": ("market systems",),
    "LANGUAGE_PROTOCOL_ENGINE": ("language/communication",),
    "EDUCATION_COGNITION_ENGINE": ("education/cognition",),
    "ENVIRONMENTAL_SYSTEM_ENGINE": ("environmental",),
    "CONSTRUCTION_ARCHITECTURE_ENGINE": ("construction/architecture",),
    "AGRICULTURE_SYSTEM_ENGINE": ("agriculture",),
    "BUSINESS_MODEL_DISCOVERY_ENGINE": ("business discovery",),
    "CREATIVE_INVENTION_ENGINE": ("creative invention",),
}

_SENSITIVE_ENGINE_FAMILIES_V1 = {
    "chemical/material",
    "biological",
    "medical-boundary",
    "cyber-resilience",
    "legal/governance",
    "energy/infrastructure",
}

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
    "." + "weslr",
    "entity" + "_" + "graph.json",
    "chat" + "_" + "responder",
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

_DEFAULT_TEXT_FIELDS_V1 = (
    "schema_version",
    "run_id",
    "engine_name",
    "engine_family",
    "research_mode",
    "domain",
    "domain_subtype",
    "system_level",
    "artifact_scale",
    "source_scope",
    "input_artifact_ref",
    "input_artifact_type",
    "input_summary",
    "validation_route",
    "experiment_type",
    "forbidden_action_notes",
    "llm_helper_role",
    "public_claim_status",
    "boundary_status",
)

_LIST_FIELDS_V1 = (
    "observations",
    "extracted_signals",
    "motif_candidates",
    "operator_candidates",
    "invariant_candidates",
    "hypotheses",
    "predictions",
    "hazard_flags",
    "cross_domain_analogies",
    "candidate_transfer_patterns",
    "failure_mode_map",
    "measurement_gap_map",
    "operator_gap_map",
    "language_gap_map",
    "unknown_unknowns",
    "probes",
    "mutations",
    "outcomes",
    "corrections",
    "next_experiments",
)

_MAPPING_FIELDS_V1 = (
    "confidence_map",
    "uncertainty_map",
    "constraint_map",
    "safety_boundary",
    "source_requirements",
    "denied_authority",
    "safe_metadata",
)

_REQUIRED_FIELDS_V1 = _DEFAULT_TEXT_FIELDS_V1 + _LIST_FIELDS_V1 + _MAPPING_FIELDS_V1 + ("required_expert_review", "simulation_before_real_world", "non_actionable_research_only")

_ALLOWED_FIELD_SET_V1 = set(_REQUIRED_FIELDS_V1) | {"metadata_notes"}


def allowed_cognitive_research_engine_families_v1() -> tuple[str, ...]:
    return ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1



def allowed_cognitive_research_engine_names_v1() -> tuple[str, ...]:
    return ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1



def allowed_cognitive_research_modes_v1() -> tuple[str, ...]:
    return ALLOWED_COGNITIVE_RESEARCH_MODES_V1



def allowed_cognitive_research_public_claim_statuses_v1() -> tuple[str, ...]:
    return ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1



def allowed_cognitive_research_llm_helper_roles_v1() -> tuple[str, ...]:
    return ALLOWED_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1



def classify_cognitive_research_engine_family_v1(engine_name: Any) -> str | None:
    name = _safe_str(engine_name)
    families = _ENGINE_ALLOWED_FAMILIES_V1.get(name)
    if not families:
        return None
    return families[0]



def _allowed_families_for_engine(engine_name: str) -> tuple[str, ...]:
    return _ENGINE_ALLOWED_FAMILIES_V1.get(engine_name, ())



def build_default_cognitive_research_denied_authority_v1() -> dict[str, bool]:
    return {key: False for key in _DENIED_AUTHORITY_KEYS_V1}



def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}



def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())



def _safe_bool(value: Any) -> bool:
    return bool(value) is True



def _safe_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.values())
    try:
        return list(value)
    except TypeError:
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
        return [_json_safe(item) for item in sorted(value, key=_safe_str)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _safe_str(value)



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



def _normalize_denied_authority(value: Any) -> dict[str, bool]:
    mapping = _as_mapping(value)
    normalized: dict[str, bool] = {}
    for key in _DENIED_AUTHORITY_KEYS_V1:
        normalized[key] = _safe_bool(mapping.get(key, False))
    for key in mapping:
        if key not in _DENIED_AUTHORITY_KEYS_V1:
            normalized[str(key)] = _safe_bool(mapping[key])
    return normalized



def _default_safety_boundary(engine_family: str) -> dict[str, Any]:
    sensitive = engine_family in _SENSITIVE_ENGINE_FAMILIES_V1
    return {
        "mode": "metadata_only",
        "sensitive_domain": sensitive,
        "non_actionable_research_only": True,
        "runtime_tool_provider_persistence_blocked": True,
        "notes": "metadata-only boundary; denied authority; no execution path",
    }



def _default_source_requirements() -> dict[str, Any]:
    return {
        "provenance_required": True,
        "raw_storage_allowed": False,
        "import_time_state_allowed": False,
        "side_effect_free": True,
        "bounded_summary_required": True,
    }



def _default_safe_metadata(engine_name: str, engine_family: str, research_mode: str) -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_executing": True,
        "non_public": True,
        "engine_name": engine_name,
        "engine_family": engine_family,
        "research_mode": research_mode,
    }



def _default_validation_route() -> list[str]:
    return [
        "metadata_only_validation",
        "fail_closed_safety_validation",
        "json_safe_copy_validation",
    ]



def _default_constraints() -> dict[str, Any]:
    return {
        "runtime": "denied",
        "tool": "denied",
        "provider": "denied",
        "search": "denied",
        "persistence": "denied",
        "public_claims": "blocked",
        "answer_authority": "denied",
    }



def _default_hazard_flags(engine_family: str) -> list[str]:
    flags: list[str] = []
    if engine_family in _SENSITIVE_ENGINE_FAMILIES_V1:
        flags.append(f"sensitive:{engine_family}")
    return flags



def _default_experiment_type() -> str:
    return "metadata_only"



def _truncate(text: Any, limit: int = 160) -> str:
    value = _safe_str(text)
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)] + "…"



def _scan_strings(value: Any, collector: list[str]) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _scan_strings(item, collector)
        return
    if isinstance(value, list):
        for item in value:
            _scan_strings(item, collector)
        return
    if isinstance(value, tuple):
        for item in value:
            _scan_strings(item, collector)
        return
    text = _safe_str(value).lower()
    if not text:
        return
    collector.append(text)



def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    for marker in markers:
        marker_l = marker.lower()
        if marker_l == "public ready" and any(
            negation in text for negation in ("not public ready", "not-public-ready", "not_public_ready")
        ):
            continue
        if marker_l in text:
            return True
    return False



def _combined_text(packet: Mapping[str, Any]) -> str:
    parts: list[str] = []
    _scan_strings(packet, parts)
    return "\n".join(parts)



def _forbidden_labels(packet: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    text = _combined_text(packet)
    if not text:
        return labels
    if _contains_any(text, _FORBIDDEN_PRIVATE_TEXT_MARKERS_V1):
        labels.append("raw_private_or_hidden_text")
    if _contains_any(text, _FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        labels.append("public_claim_language")
    if _contains_any(text, _FORBIDDEN_DANGEROUS_PROCEDURAL_MARKERS_V1):
        labels.append("dangerous_procedural_language")
    if "llm as authority" in text or "llm authority" in text:
        labels.append("llm_as_authority")
    if "runtime authority" in text:
        labels.append("runtime_authority_claim")
    if "tool authority" in text:
        labels.append("tool_authority_claim")
    if "provider authority" in text:
        labels.append("provider_authority_claim")
    if "search authority" in text:
        labels.append("search_authority_claim")
    if "persistence authority" in text:
        labels.append("persistence_authority_claim")
    if "public export authority" in text:
        labels.append("public_export_authority_claim")
    return _dedupe_preserve_order(labels)



def _required_fields_present(packet: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    for field in _REQUIRED_FIELDS_V1:
        if field not in packet:
            blocked.append(f"missing_{field}")
    return blocked



def _validate_denied_authority(packet: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    denied = packet.get("denied_authority")
    if not isinstance(denied, Mapping):
        return ["missing_denied_authority"]
    if set(str(key) for key in denied.keys()) != set(_DENIED_AUTHORITY_KEYS_V1):
        blocked.append("invalid_denied_authority_schema")
    for key in _DENIED_AUTHORITY_KEYS_V1:
        if _safe_bool(denied.get(key)):
            blocked.append(f"denied_authority_granted_{key}")
    return _dedupe_preserve_order(blocked)



def _safe_metadata_is_valid(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, Mapping):
        return _safe_bool(value.get("safe", False))
    return False



def _safe_boundary_present(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)



def _summary_text_from_packet(packet: Mapping[str, Any], blocked: bool, blocked_labels: list[str]) -> str:
    engine_name = _safe_str(packet.get("engine_name")) or "UNKNOWN_ENGINE"
    engine_family = _safe_str(packet.get("engine_family")) or "unknown"
    research_mode = _safe_str(packet.get("research_mode")) or "exploratory"
    domain = _safe_str(packet.get("domain")) or "unspecified"
    domain_subtype = _safe_str(packet.get("domain_subtype")) or "unspecified"
    artifact_ref = _truncate(packet.get("input_artifact_ref"), 72)
    artifact_type = _truncate(packet.get("input_artifact_type"), 32)
    public_status = _safe_str(packet.get("public_claim_status")) or "blocked_internal_only"
    boundary_status = _safe_str(packet.get("boundary_status")) or "metadata_only"
    hypothesis_count = len(_safe_list(packet.get("hypotheses")))
    probe_count = len(_safe_list(packet.get("probes")))
    summary = (
        f"Cognitive research run: engine={engine_name}; family={engine_family}; mode={research_mode}; "
        f"domain={domain}/{domain_subtype}; artifact={artifact_type}:{artifact_ref}; "
        f"hypotheses={hypothesis_count}; probes={probe_count}; public={public_status}; boundary={boundary_status}."
    )
    if blocked:
        preview = ", ".join(blocked_labels[:4])
        return f"Blocked cognitive research run: {preview or 'validation failed'}. {summary}"
    return summary



def validate_cognitive_research_run_v1(packet: Any) -> dict[str, Any]:
    raw = _as_mapping(packet)
    blocked_labels: list[str] = []

    blocked_labels.extend(_required_fields_present(raw))

    engine_name = _safe_str(raw.get("engine_name"))
    engine_family = _safe_str(raw.get("engine_family"))
    research_mode = _safe_str(raw.get("research_mode"))
    public_claim_status = _safe_str(raw.get("public_claim_status"))
    llm_helper_role = _safe_str(raw.get("llm_helper_role"))
    boundary_status = _safe_str(raw.get("boundary_status"))

    if engine_name not in ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1:
        blocked_labels.append("unknown_engine_name")
    if engine_family not in ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1:
        blocked_labels.append("unknown_engine_family")
    if research_mode not in ALLOWED_COGNITIVE_RESEARCH_MODES_V1:
        blocked_labels.append("unknown_research_mode")
    if public_claim_status not in ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1:
        blocked_labels.append("unknown_public_claim_status")
    if llm_helper_role not in ALLOWED_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1:
        blocked_labels.append("unknown_llm_helper_role")
    if boundary_status not in ALLOWED_COGNITIVE_RESEARCH_BOUNDARY_STATUSES_V1:
        blocked_labels.append("unknown_boundary_status")

    allowed_families = _allowed_families_for_engine(engine_name)
    if engine_name in ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1 and engine_family not in allowed_families:
        blocked_labels.append("engine_family_mismatch")

    denied_labels = _validate_denied_authority(raw)
    blocked_labels.extend(denied_labels)

    if not _safe_metadata_is_valid(raw.get("safe_metadata")):
        blocked_labels.append("unsafe_safe_metadata")

    if not _safe_boundary_present(raw.get("safety_boundary")):
        blocked_labels.append("missing_safety_boundary")

    if _safe_bool(raw.get("non_actionable_research_only")) is not True:
        blocked_labels.append("non_actionable_research_only_false")

    text_labels = _forbidden_labels(raw)
    blocked_labels.extend(text_labels)

    if engine_name == "UNKNOWN_ENGINE" and engine_family == "unknown":
        pass

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
        "llm_helper_role": llm_helper_role,
        "boundary_status": boundary_status,
        "summary_text": summary_text,
        "packet": packet_json_safe,
    }



def summarize_cognitive_research_run_v1(packet: Any) -> dict[str, Any]:
    validation = validate_cognitive_research_run_v1(packet)
    raw = _as_mapping(packet)
    summary_text = _summary_text_from_packet(raw, validation["blocked"], validation["blocked_labels"])
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "summary_text": _truncate(summary_text, 320),
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "classification": validation["classification"],
        "engine_name": validation["engine_name"],
        "engine_family": validation["engine_family"],
        "research_mode": validation["research_mode"],
        "public_claim_status": validation["public_claim_status"],
        "llm_helper_role": validation["llm_helper_role"],
        "boundary_status": validation["boundary_status"],
        "packet": validation["packet"],
    }



def build_cognitive_research_run_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    engine_name = _safe_str(data.get("engine_name")) or "UNKNOWN_ENGINE"
    engine_family = _safe_str(data.get("engine_family")) or _safe_str(classify_cognitive_research_engine_family_v1(engine_name))
    research_mode = _safe_str(data.get("research_mode")) or "exploratory"
    public_claim_status = _safe_str(data.get("public_claim_status")) or "blocked_internal_only"
    llm_helper_role = _safe_str(data.get("llm_helper_role")) or "helper"
    boundary_status = _safe_str(data.get("boundary_status")) or "metadata_only"

    packet: dict[str, Any] = {
        "schema_version": _safe_str(data.get("schema_version")) or SCHEMA_VERSION_V1,
        "run_id": _safe_str(data.get("run_id")),
        "engine_name": engine_name,
        "engine_family": engine_family,
        "research_mode": research_mode,
        "domain": _safe_str(data.get("domain")) or "unspecified",
        "domain_subtype": _safe_str(data.get("domain_subtype")) or "unspecified",
        "system_level": _safe_str(data.get("system_level")) or "component",
        "artifact_scale": _safe_str(data.get("artifact_scale")) or "bounded artifact",
        "source_scope": _safe_str(data.get("source_scope")) or "metadata_only",
        "input_artifact_ref": _safe_str(data.get("input_artifact_ref")),
        "input_artifact_type": _safe_str(data.get("input_artifact_type")) or "artifact_ref",
        "input_summary": _safe_str(data.get("input_summary")),
        "observations": _json_safe(data.get("observations")) if data.get("observations") is not None else [],
        "extracted_signals": _json_safe(data.get("extracted_signals")) if data.get("extracted_signals") is not None else [],
        "motif_candidates": _json_safe(data.get("motif_candidates")) if data.get("motif_candidates") is not None else [],
        "operator_candidates": _json_safe(data.get("operator_candidates")) if data.get("operator_candidates") is not None else [],
        "invariant_candidates": _json_safe(data.get("invariant_candidates")) if data.get("invariant_candidates") is not None else [],
        "hypotheses": _json_safe(data.get("hypotheses")) if data.get("hypotheses") is not None else [],
        "predictions": _json_safe(data.get("predictions")) if data.get("predictions") is not None else [],
        "confidence_map": _json_safe(data.get("confidence_map")) if data.get("confidence_map") is not None else {},
        "uncertainty_map": _json_safe(data.get("uncertainty_map")) if data.get("uncertainty_map") is not None else {},
        "constraint_map": _json_safe(data.get("constraint_map")) if data.get("constraint_map") is not None else _default_constraints(),
        "safety_boundary": _json_safe(data.get("safety_boundary")) if data.get("safety_boundary") is not None else _default_safety_boundary(engine_family),
        "hazard_flags": _json_safe(data.get("hazard_flags")) if data.get("hazard_flags") is not None else _default_hazard_flags(engine_family),
        "validation_route": _json_safe(data.get("validation_route")) if data.get("validation_route") is not None else _default_validation_route(),
        "required_expert_review": _safe_bool(data.get("required_expert_review", engine_family in _SENSITIVE_ENGINE_FAMILIES_V1)),
        "source_requirements": _json_safe(data.get("source_requirements")) if data.get("source_requirements") is not None else _default_source_requirements(),
        "experiment_type": _safe_str(data.get("experiment_type")) or _default_experiment_type(),
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
        "probes": _json_safe(data.get("probes")) if data.get("probes") is not None else [],
        "mutations": _json_safe(data.get("mutations")) if data.get("mutations") is not None else [],
        "outcomes": _json_safe(data.get("outcomes")) if data.get("outcomes") is not None else [],
        "corrections": _json_safe(data.get("corrections")) if data.get("corrections") is not None else [],
        "compressed_lesson": _safe_str(data.get("compressed_lesson")),
        "next_experiments": _json_safe(data.get("next_experiments")) if data.get("next_experiments") is not None else [],
        "llm_helper_role": llm_helper_role,
        "public_claim_status": public_claim_status,
        "boundary_status": boundary_status,
        "denied_authority": _normalize_denied_authority(data.get("denied_authority") if data.get("denied_authority") is not None else build_default_cognitive_research_denied_authority_v1()),
        "safe_metadata": _json_safe(data.get("safe_metadata")) if data.get("safe_metadata") is not None else _default_safe_metadata(engine_name, engine_family, research_mode),
    }

    if not packet["run_id"]:
        packet["run_id"] = f"cr-{_stable_digest({
            'engine_name': packet['engine_name'],
            'engine_family': packet['engine_family'],
            'research_mode': packet['research_mode'],
            'domain': packet['domain'],
            'domain_subtype': packet['domain_subtype'],
            'source_scope': packet['source_scope'],
            'input_artifact_ref': packet['input_artifact_ref'],
            'input_artifact_type': packet['input_artifact_type'],
        })[:16]}"

    packet["safe_metadata"] = _json_safe(packet["safe_metadata"])
    packet["safety_boundary"] = _json_safe(packet["safety_boundary"])
    packet["source_requirements"] = _json_safe(packet["source_requirements"])
    packet["denied_authority"] = _normalize_denied_authority(packet["denied_authority"])
    return packet



def _example_specifications_v1() -> list[dict[str, Any]]:
    return [
        {
            "engine_name": "UNKNOWN_ENGINE",
            "engine_family": "unknown",
            "research_mode": "exploratory",
            "domain": "signal interpretation",
            "domain_subtype": "hidden-rule discovery",
            "system_level": "component",
            "artifact_scale": "bounded artifact",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:unknown-001",
            "input_artifact_type": "report",
            "input_summary": "Metadata-only observation set for hidden-rule discovery.",
            "hypotheses": ["A hidden rule may explain the observed contradiction cloud."],
            "probes": ["observe -> predict -> reveal -> correct"],
            "compressed_lesson": "Unknowns should stay unknown until probes earn them.",
        },
        {
            "engine_name": "RAW_SIGNAL_CARTOGRAPHER",
            "engine_family": "raw-signal",
            "research_mode": "raw_signal",
            "domain": "signal terrain",
            "domain_subtype": "motif mapping",
            "system_level": "subsystem",
            "artifact_scale": "large artifact",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:raw-signal-001",
            "input_artifact_type": "artifact_ref",
            "input_summary": "Cartography of signal geometry and repeated motifs.",
            "motif_candidates": ["terrain", "motif", "zone"],
            "probes": ["map first, translate later"],
            "compressed_lesson": "Preserve shape before interpretation.",
        },
        {
            "engine_name": "UNINTELLIGIBLE_OUTPUT_ANALYZER",
            "engine_family": "raw-signal",
            "research_mode": "gap_discovery",
            "domain": "strange output",
            "domain_subtype": "pre-translation structure",
            "system_level": "workflow",
            "artifact_scale": "large corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:unintelligible-001",
            "input_artifact_type": "corpus",
            "input_summary": "Competing interpretation layers for alien structure.",
            "operator_candidates": ["layered interpretation", "structure preservation"],
            "probes": ["hold translation until structure is mapped"],
            "compressed_lesson": "Unknown structure is information, not noise.",
        },
        {
            "engine_name": "SIGNAL_VS_NOISE_ENGINE",
            "engine_family": "raw-signal",
            "research_mode": "raw_signal",
            "domain": "signal separation",
            "domain_subtype": "noise and weak structure",
            "system_level": "component",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:signal-vs-noise-001",
            "input_artifact_type": "corpus",
            "input_summary": "Separate randomness, pseudo-randomness, weak structure, and emerging grammar.",
            "probes": ["separate weak structure from noise"],
            "compressed_lesson": "Weak structure deserves its own label.",
        },
        {
            "engine_name": "ALGORITHM_EMERGENCE_ENGINE",
            "engine_family": "gap",
            "research_mode": "gap_discovery",
            "domain": "procedure emergence",
            "domain_subtype": "primitive-to-procedure",
            "system_level": "workflow",
            "artifact_scale": "bounded artifact",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:algorithm-emergence-001",
            "input_artifact_type": "notes",
            "input_summary": "Observe procedures emerge without naming known algorithms first.",
            "mutations": ["primitive perturbation", "constraint shift"],
            "probes": ["watch for procedure emergence"],
            "compressed_lesson": "Procedures can appear before their names.",
        },
        {
            "engine_name": "MUTABLE_AXIOM_MATH_ENGINE",
            "engine_family": "math",
            "research_mode": "invariant_mining",
            "domain": "mathematics",
            "domain_subtype": "axiom mutation",
            "system_level": "component",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:mutable-axiom-001",
            "input_artifact_type": "corpus",
            "input_summary": "Mutate assumptions and observe what breaks or survives.",
            "hypotheses": ["A small axiom change may reveal a new invariant."],
            "mutations": ["assumption shift"],
            "compressed_lesson": "Invariant mining begins where assumptions bend.",
        },
        {
            "engine_name": "OPERATOR_FORGE_ENGINE",
            "engine_family": "math",
            "research_mode": "internal_hypothesis",
            "domain": "operator design",
            "domain_subtype": "candidate transformations",
            "system_level": "subsystem",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:operator-forge-001",
            "input_artifact_type": "notes",
            "input_summary": "Invent candidate transformations and test their behavior space.",
            "operator_candidates": ["candidate transform A", "candidate transform B"],
            "probes": ["test operator behavior space"],
            "compressed_lesson": "Operators are discovered by trying them.",
        },
        {
            "engine_name": "INVARIANT_MINER",
            "engine_family": "math",
            "research_mode": "invariant_mining",
            "domain": "invariant discovery",
            "domain_subtype": "cross-mutation stability",
            "system_level": "component",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:invariant-miner-001",
            "input_artifact_type": "corpus",
            "input_summary": "What remains stable across mutations, domains, scales, and failures?",
            "invariant_candidates": ["stable relation", "cross-domain symmetry"],
            "compressed_lesson": "Stability is a signal.",
        },
        {
            "engine_name": "CONTRADICTION_FURNACE",
            "engine_family": "math",
            "research_mode": "contradiction_analysis",
            "domain": "contradiction compression",
            "domain_subtype": "missing bridge search",
            "system_level": "workflow",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:contradiction-furnace-001",
            "input_artifact_type": "notes",
            "input_summary": "Compress contradictions until the missing bridge appears.",
            "contradiction_map": ["belief clash", "measurement mismatch"],
            "probes": ["compress until bridge appears"],
            "compressed_lesson": "A contradiction can hide a new distinction.",
        },
        {
            "engine_name": "CAUSAL_TRACE_ENGINE",
            "engine_family": "gap",
            "research_mode": "calibration",
            "domain": "causal tracing",
            "domain_subtype": "effect-to-cause mapping",
            "system_level": "workflow",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:causal-trace-001",
            "input_artifact_type": "corpus",
            "input_summary": "Trace causal structure without assuming complete explanations.",
            "compressed_lesson": "Causal traces are hypotheses, not authority.",
        },
        {
            "engine_name": "BLINDSPOT_ENGINE",
            "engine_family": "gap",
            "research_mode": "gap_discovery",
            "domain": "blind spot mapping",
            "domain_subtype": "coverage gaps",
            "system_level": "system",
            "artifact_scale": "bounded artifact",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:blindspot-001",
            "input_artifact_type": "report",
            "input_summary": "Map blind spots, missing operators, and boundary failures.",
            "measurement_gap_map": ["missing measurement zone"],
            "operator_gap_map": ["missing operator"],
            "compressed_lesson": "A gap is an object.",
        },
        {
            "engine_name": "CALIBRATION_LEDGER",
            "engine_family": "calibration",
            "research_mode": "calibration",
            "domain": "forecast tracking",
            "domain_subtype": "confidence correction",
            "system_level": "workflow",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:calibration-ledger-001",
            "input_artifact_type": "ledger",
            "input_summary": "Track forecast error and confidence correction metadata only.",
            "confidence_map": {"initial": "low", "corrected": "medium"},
            "uncertainty_map": {"notes": "bounded uncertainty"},
            "compressed_lesson": "Calibration improves future judgment.",
        },
        {
            "engine_name": "FORECAST_ERROR_LEDGER",
            "engine_family": "calibration",
            "research_mode": "calibration",
            "domain": "forecast tracking",
            "domain_subtype": "outcome mismatch",
            "system_level": "workflow",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:forecast-error-001",
            "input_artifact_type": "ledger",
            "input_summary": "Record outcome mismatch and compressed lesson metadata only.",
            "outcomes": ["mismatch observed"],
            "corrections": ["confidence reduced"],
            "compressed_lesson": "Error history is a resource.",
        },
        {
            "engine_name": "GAP_CARTOGRAPHER",
            "engine_family": "gap",
            "research_mode": "gap_discovery",
            "domain": "gap mapping",
            "domain_subtype": "coverage gaps",
            "system_level": "system",
            "artifact_scale": "large corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:gap-cartographer-001",
            "input_artifact_type": "corpus",
            "input_summary": "Map blind spots, missing operators, language gaps, proof gaps, and measurement gaps.",
            "operator_gap_map": ["missing operator"],
            "language_gap_map": ["missing vocabulary"],
            "measurement_gap_map": ["missing metric"],
            "compressed_lesson": "Gaps have geometry.",
        },
        {
            "engine_name": "ASSUMPTION_EXCAVATOR",
            "engine_family": "gap",
            "research_mode": "internal_hypothesis",
            "domain": "assumption excavation",
            "domain_subtype": "hidden premises",
            "system_level": "workflow",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:assumption-excavator-001",
            "input_artifact_type": "notes",
            "input_summary": "Excavate what the system assumes without saying so.",
            "unknown_unknowns": ["hidden premise"],
            "compressed_lesson": "Assumptions are often the terrain.",
        },
        {
            "engine_name": "PROBE_GENERATOR",
            "engine_family": "gap",
            "research_mode": "exploratory",
            "domain": "probe design",
            "domain_subtype": "candidate probes",
            "system_level": "component",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:probe-generator-001",
            "input_artifact_type": "notes",
            "input_summary": "Generate safe probes for discovering structure.",
            "probes": ["candidate probe A", "candidate probe B"],
            "compressed_lesson": "Probes are questions with structure.",
        },
        {
            "engine_name": "MEMORY_TRUST_ENGINE",
            "engine_family": "calibration",
            "research_mode": "calibration",
            "domain": "memory trust",
            "domain_subtype": "context reliability",
            "system_level": "component",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:memory-trust-001",
            "input_artifact_type": "report",
            "input_summary": "Decide what memory/context can be trusted, weakened, contradicted, or quarantined.",
            "uncertainty_map": {"context": "bounded"},
            "compressed_lesson": "Trust is calibrated, not assumed.",
        },
        {
            "engine_name": "ABSTRACTION_LADDER",
            "engine_family": "math",
            "research_mode": "cross_domain_transfer",
            "domain": "abstraction",
            "domain_subtype": "concrete to principle",
            "system_level": "workflow",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:abstraction-ladder-001",
            "input_artifact_type": "notes",
            "input_summary": "Move from concrete case to pattern, operator, principle, and transferable structure.",
            "candidate_transfer_patterns": ["concrete -> pattern -> operator"],
            "compressed_lesson": "Abstraction is a climb.",
        },
        {
            "engine_name": "GOVERNANCE_BOUNDARY_ENGINE",
            "engine_family": "legal/governance",
            "research_mode": "boundary_review",
            "domain": "governance",
            "domain_subtype": "authority boundary",
            "system_level": "policy",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:governance-boundary-001",
            "input_artifact_type": "policy",
            "input_summary": "Track authority, review, and denial boundaries only.",
            "safety_boundary": {"scope": "governance", "notes": "metadata only"},
            "compressed_lesson": "Boundaries are part of governance.",
        },
        {
            "engine_name": "INTENT_RECONSTRUCTION_ENGINE",
            "engine_family": "language/communication",
            "research_mode": "exploratory",
            "domain": "intent reconstruction",
            "domain_subtype": "communication semantics",
            "system_level": "workflow",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:intent-reconstruction-001",
            "input_artifact_type": "notes",
            "input_summary": "Reconstruct intent from communication metadata without authority claims.",
            "cross_domain_analogies": ["signal to meaning"],
            "compressed_lesson": "Language is a transport layer.",
        },
        {
            "engine_name": "CHEMICAL_SPACE_CARTOGRAPHER",
            "engine_family": "chemical/material",
            "research_mode": "exploratory",
            "domain": "chemistry",
            "domain_subtype": "chemical space mapping",
            "system_level": "material",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:chemical-space-001",
            "input_artifact_type": "report",
            "input_summary": "Map chemical space as metadata only; no synthesis procedures.",
            "safety_boundary": {"scope": "chemical/material", "no_procedure": True},
            "compressed_lesson": "Maps are not procedures.",
        },
        {
            "engine_name": "BIOLOGICAL_SYSTEMS_ANALYZER",
            "engine_family": "biological",
            "research_mode": "exploratory",
            "domain": "biology",
            "domain_subtype": "systems analysis",
            "system_level": "system",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:biological-001",
            "input_artifact_type": "report",
            "input_summary": "Analyze biological system metadata only; no wetlab or pathogen handling.",
            "safety_boundary": {"scope": "biological", "no_wetlab": True},
            "compressed_lesson": "Biology stays metadata-only here.",
        },
        {
            "engine_name": "MEDICAL_REASONING_BOUNDARY_ENGINE",
            "engine_family": "medical-boundary",
            "research_mode": "boundary_review",
            "domain": "medicine",
            "domain_subtype": "reasoning boundary",
            "system_level": "policy",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:medical-boundary-001",
            "input_artifact_type": "policy",
            "input_summary": "Medical reasoning boundary review only; no diagnosis, treatment, or dosage authority.",
            "safety_boundary": {"scope": "medical", "no_diagnosis": True},
            "compressed_lesson": "Boundary first, medicine later.",
        },
        {
            "engine_name": "ENERGY_SYSTEMS_DISCOVERY_ENGINE",
            "engine_family": "energy/infrastructure",
            "research_mode": "exploratory",
            "domain": "energy systems",
            "domain_subtype": "infrastructure discovery",
            "system_level": "system",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:energy-systems-001",
            "input_artifact_type": "report",
            "input_summary": "Energy system discovery metadata only.",
            "safety_boundary": {"scope": "energy/infrastructure", "no_action": True},
            "compressed_lesson": "Infrastructure needs boundaries.",
        },
        {
            "engine_name": "INDUSTRIAL_PROCESS_MINER",
            "engine_family": "industrial",
            "research_mode": "gap_discovery",
            "domain": "industrial process",
            "domain_subtype": "process mining",
            "system_level": "workflow",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:industrial-001",
            "input_artifact_type": "report",
            "input_summary": "Mine industrial process structure as metadata only.",
            "compressed_lesson": "Process structure can be mined safely.",
        },
        {
            "engine_name": "ROBOTICS_EMBODIMENT_ENGINE",
            "engine_family": "robotics",
            "research_mode": "exploratory",
            "domain": "robotics",
            "domain_subtype": "embodiment",
            "system_level": "system",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:robotics-001",
            "input_artifact_type": "report",
            "input_summary": "Robotics embodiment metadata only.",
            "compressed_lesson": "Embodiment analysis can stay descriptive.",
        },
        {
            "engine_name": "MANUFACTURING_PATTERN_ENGINE",
            "engine_family": "manufacturing",
            "research_mode": "exploratory",
            "domain": "manufacturing",
            "domain_subtype": "pattern detection",
            "system_level": "workflow",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:manufacturing-001",
            "input_artifact_type": "report",
            "input_summary": "Manufacturing pattern metadata only.",
            "compressed_lesson": "Pattern discovery is enough here.",
        },
        {
            "engine_name": "RF_SIGNAL_WORLD_MODEL_ENGINE",
            "engine_family": "RF/signal",
            "research_mode": "raw_signal",
            "domain": "RF",
            "domain_subtype": "signal world model",
            "system_level": "system",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:rf-signal-001",
            "input_artifact_type": "report",
            "input_summary": "RF signal world model metadata only.",
            "compressed_lesson": "Signals can be mapped without action.",
        },
        {
            "engine_name": "SEMICONDUCTOR_SYSTEM_ENGINE",
            "engine_family": "semiconductor",
            "research_mode": "exploratory",
            "domain": "semiconductor",
            "domain_subtype": "system analysis",
            "system_level": "system",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:semiconductor-001",
            "input_artifact_type": "report",
            "input_summary": "Semiconductor system metadata only.",
            "compressed_lesson": "System mapping stays descriptive.",
        },
        {
            "engine_name": "CYBER_RESILIENCE_ENGINE",
            "engine_family": "cyber-resilience",
            "research_mode": "boundary_review",
            "domain": "cybersecurity",
            "domain_subtype": "resilience",
            "system_level": "system",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:cyber-resilience-001",
            "input_artifact_type": "report",
            "input_summary": "Cyber resilience metadata only; no exploit, malware, or credential-theft content.",
            "safety_boundary": {"scope": "cyber-resilience", "no_offense": True},
            "compressed_lesson": "Defensive metadata only.",
        },
        {
            "engine_name": "LEGAL_GOVERNANCE_GAP_ENGINE",
            "engine_family": "legal/governance",
            "research_mode": "gap_discovery",
            "domain": "legal-governance",
            "domain_subtype": "gap mapping",
            "system_level": "policy",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:legal-governance-001",
            "input_artifact_type": "policy",
            "input_summary": "Legal governance gap metadata only; no legal advice or authority claim.",
            "safety_boundary": {"scope": "legal/governance", "no_advice": True},
            "compressed_lesson": "Governance analysis is scoped analysis.",
        },
        {
            "engine_name": "MARKET_SYSTEM_DYNAMICS_ENGINE",
            "engine_family": "market systems",
            "research_mode": "calibration",
            "domain": "markets",
            "domain_subtype": "dynamics",
            "system_level": "system",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:market-dynamics-001",
            "input_artifact_type": "report",
            "input_summary": "Market system dynamics metadata only; no investment advice or execution.",
            "compressed_lesson": "Observation is not execution.",
        },
        {
            "engine_name": "LANGUAGE_PROTOCOL_ENGINE",
            "engine_family": "language/communication",
            "research_mode": "exploratory",
            "domain": "language",
            "domain_subtype": "protocol analysis",
            "system_level": "communication",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:language-protocol-001",
            "input_artifact_type": "notes",
            "input_summary": "Language protocol metadata only.",
            "compressed_lesson": "Communication can be modeled safely.",
        },
        {
            "engine_name": "EDUCATION_COGNITION_ENGINE",
            "engine_family": "education/cognition",
            "research_mode": "exploratory",
            "domain": "education",
            "domain_subtype": "cognition",
            "system_level": "system",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:education-cognition-001",
            "input_artifact_type": "report",
            "input_summary": "Education cognition metadata only.",
            "compressed_lesson": "Learning structures can be described.",
        },
        {
            "engine_name": "ENVIRONMENTAL_SYSTEM_ENGINE",
            "engine_family": "environmental",
            "research_mode": "exploratory",
            "domain": "environment",
            "domain_subtype": "system analysis",
            "system_level": "ecosystem",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:environmental-001",
            "input_artifact_type": "report",
            "input_summary": "Environmental system metadata only.",
            "compressed_lesson": "Environment mapping is descriptive here.",
        },
        {
            "engine_name": "CONSTRUCTION_ARCHITECTURE_ENGINE",
            "engine_family": "construction/architecture",
            "research_mode": "exploratory",
            "domain": "construction",
            "domain_subtype": "architecture analysis",
            "system_level": "system",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:construction-architecture-001",
            "input_artifact_type": "report",
            "input_summary": "Construction and architecture metadata only.",
            "compressed_lesson": "Structure can be mapped without instructions.",
        },
        {
            "engine_name": "AGRICULTURE_SYSTEM_ENGINE",
            "engine_family": "agriculture",
            "research_mode": "exploratory",
            "domain": "agriculture",
            "domain_subtype": "system analysis",
            "system_level": "system",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:agriculture-001",
            "input_artifact_type": "report",
            "input_summary": "Agriculture system metadata only.",
            "compressed_lesson": "Agriculture stays descriptive here.",
        },
        {
            "engine_name": "BUSINESS_MODEL_DISCOVERY_ENGINE",
            "engine_family": "business discovery",
            "research_mode": "cross_domain_transfer",
            "domain": "business",
            "domain_subtype": "model discovery",
            "system_level": "workflow",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:business-model-001",
            "input_artifact_type": "report",
            "input_summary": "Business model discovery metadata only.",
            "candidate_transfer_patterns": ["structure -> model"],
            "compressed_lesson": "Discovery can stay non-executing.",
        },
        {
            "engine_name": "CREATIVE_INVENTION_ENGINE",
            "engine_family": "creative invention",
            "research_mode": "internal_hypothesis",
            "domain": "creative invention",
            "domain_subtype": "novel structure",
            "system_level": "workflow",
            "artifact_scale": "bounded corpus",
            "source_scope": "metadata_only",
            "input_artifact_ref": "artifact:creative-invention-001",
            "input_artifact_type": "notes",
            "input_summary": "Creative invention metadata only.",
            "hypotheses": ["A novel structure may emerge from unusual combinatorics."],
            "compressed_lesson": "Creativity can remain metadata-only.",
        },
    ]



def build_initial_cognitive_research_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for spec in _example_specifications_v1():
        packet = build_cognitive_research_run_v1(
            spec,
            required_expert_review=spec["engine_family"] in _SENSITIVE_ENGINE_FAMILIES_V1,
            non_actionable_research_only=True,
            simulation_before_real_world=True,
            public_claim_status="blocked_internal_only",
            llm_helper_role="helper",
            safety_boundary=_default_safety_boundary(spec["engine_family"]),
            source_requirements=_default_source_requirements(),
            denied_authority=build_default_cognitive_research_denied_authority_v1(),
            safe_metadata=_default_safe_metadata(spec["engine_name"], spec["engine_family"], spec["research_mode"]),
        )
        examples.append(packet)
    return examples
