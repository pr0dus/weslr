"""Metadata-only helpers for MUTABLE_AXIOM_MATH_ENGINE v1.

This module is intentionally pure, deterministic, JSON-safe, and fail-closed.
It consumes the reviewed cognitive research boundary registry only as read-only
metadata and does not execute runtime, tool, provider, search, persistence, or
public-facing behavior.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

from weslr.cognitive_research_engine_boundaries import (
    build_cognitive_research_engine_boundary_registry_v1,
    get_cognitive_research_engine_boundary_v1,
    summarize_cognitive_research_engine_boundary_v1,
    validate_cognitive_research_engine_boundary_v1,
)
from weslr.cognitive_research_protocol import (
    ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1,
    build_default_cognitive_research_denied_authority_v1,
)

SCHEMA_VERSION_V1 = "mutable_axiom_math_v1"
ENGINE_NAME_V1 = "MUTABLE_AXIOM_MATH_ENGINE"
UPSTREAM_RAW_SIGNAL_ENGINE_NAME_V1 = "RAW_SIGNAL_CARTOGRAPHER"
UPSTREAM_INTERPRETIVE_ENGINE_NAME_V1 = "UNINTELLIGIBLE_OUTPUT_ANALYZER"
UPSTREAM_SIGNAL_NOISE_ENGINE_NAME_V1 = "SIGNAL_VS_NOISE_ENGINE"
UPSTREAM_ALGORITHM_EMERGENCE_ENGINE_NAME_V1 = "ALGORITHM_EMERGENCE_ENGINE"
HELPER_TYPE_V1 = "weslr_mutable_axiom_math_engine_helpers_v1"

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw private data",
    "raw private text",
    "private/raw",
    "secret",
    "hidden/system prompt",
    "hidden prompt",
    "system prompt",
    ".weslr",
    "executable code-as-action",
    "live tool instructions",
    "provider/model output",
    "model output claimed as authority",
    "provider authority",
    "tool authority",
    "search authority",
    "dangerous procedural instructions",
    "step-by-step",
    "how to exploit",
    "exploit chain",
    "malware",
    "credential theft",
    "benchmark answer key",
    "hidden benchmark data",
    "private benchmark data",
    "semi-private benchmark data",
    "theorem prover",
    "proof solver",
    "math tutor",
    "benchmark runner",
    "answer generator",
    "generic theorem prover",
    "generic math tutor",
    "generic answer generator",
    "generic benchmark runner",
    "official mathematical result",
    "open-problem solution",
    "open problem solution",
    "confirmed algorithm discovery",
    "algorithm discovery",
)

_FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1 = (
    "solved",
    "breakthrough",
    "certification",
    "benchmark",
    "public ready",
    "public-ready",
    "official result",
    "official mathematical result",
    "open-problem solution",
    "open problem solution",
    "confirmed algorithm discovery",
    "algorithm discovery",
)

_FORBIDDEN_FLATTENING_MARKERS_V1 = (
    "theorem prover",
    "proof solver",
    "math tutor",
    "benchmark runner",
    "answer generator",
    "generic theorem prover",
    "generic math tutor",
    "generic answer generator",
    "generic benchmark runner",
    "confirmed algorithm discovery",
    "algorithm discovery",
)

_REQUIRED_PACKET_FIELDS_V1 = (
    "schema_version",
    "engine_name",
    "source_boundary_engine_name",
    "input_category",
    "artifact_reference",
    "artifact_summary",
    "mutable_axiom_map",
    "axiom_variant_candidates",
    "rule_perturbation_labels",
    "invariant_shift_labels",
    "contradiction_surface_notes",
    "degenerate_case_labels",
    "boundary_case_labels",
    "toy_model_shift_summaries",
    "proof_obstruction_map",
    "consistency_instability_candidates",
    "invalidated_axiom_variants",
    "next_probe_labels",
    "relationship_to_raw_signal_cartographer",
    "relationship_to_unintelligible_output_analyzer",
    "relationship_to_signal_vs_noise",
    "relationship_to_algorithm_emergence",
    "relationship_to_cognitive_research_run",
    "safe_metadata",
    "denied_authority",
    "public_claim_status",
)

_REQUIRED_RELATIONSHIP_FIELDS_V1 = (
    "role",
    "envelope_only",
    "not_engine_kernel",
    "not_runtime_authority",
    "not_tool_authority",
    "not_provider_authority",
    "not_search_authority",
    "not_proof_authority",
    "not_public_claim_authority",
)

_REQUIRED_RAW_SIGNAL_RELATIONSHIP_FIELDS_V1 = (
    "role",
    "upstream_engine_name",
    "preserves_unknown_tokens",
    "preserves_competing_layers",
    "not_final_meaning_authority",
    "not_runtime_authority",
    "not_tool_authority",
    "not_provider_authority",
    "not_search_authority",
    "not_proof_authority",
    "not_public_claim_authority",
)

_REQUIRED_INTERPRETIVE_RELATIONSHIP_FIELDS_V1 = (
    "role",
    "upstream_engine_name",
    "preserves_competing_interpretations",
    "preserves_weak_structure",
    "not_final_meaning_authority",
    "not_runtime_authority",
    "not_tool_authority",
    "not_provider_authority",
    "not_search_authority",
    "not_proof_authority",
    "not_public_claim_authority",
)

_REQUIRED_SIGNAL_NOISE_RELATIONSHIP_FIELDS_V1 = (
    "role",
    "upstream_engine_name",
    "preserves_signal_noise_classification",
    "preserves_weak_signal_candidates",
    "preserves_pseudo_randomness_labels",
    "preserves_artifact_effect_labels",
    "preserves_undecidable_regions",
    "not_final_algorithm_authority",
    "not_runtime_authority",
    "not_tool_authority",
    "not_provider_authority",
    "not_search_authority",
    "not_proof_authority",
    "not_public_claim_authority",
)

_REQUIRED_ALGORITHM_EMERGENCE_RELATIONSHIP_FIELDS_V1 = (
    "role",
    "upstream_engine_name",
    "preserves_candidate_algorithm_map",
    "preserves_operator_chain_candidates",
    "preserves_transformation_rule_candidates",
    "preserves_invariant_candidates",
    "preserves_invalidated_rule_history",
    "preserves_terrain_shift_context",
    "not_final_math_authority",
    "not_runtime_authority",
    "not_tool_authority",
    "not_provider_authority",
    "not_search_authority",
    "not_proof_authority",
    "not_public_claim_authority",
)

_REQUIRED_PUBLIC_CLAIM_STATUS_V1 = set(ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1)


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return " ".join(str(value).split())


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


def _payload_marker(prefix: str, payload: Mapping[str, Any]) -> str:
    blob = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"synthetic:{prefix}:{hashlib.sha256(blob.encode('utf-8')).hexdigest()[:12]}"


def _iter_text_values(value: Any):
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_text_values(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _iter_text_values(item)
    elif value is not None:
        yield _compact_text(value)


def _has_forbidden_markers(value: Any) -> bool:
    blob = "\n".join(_iter_text_values(value)).lower()
    return any(marker in blob for marker in _FORBIDDEN_TEXT_MARKERS_V1)


def _base_relationship_to_raw_signal() -> dict[str, Any]:
    return {
        "role": "axiom_mutation_after_raw_signal",
        "upstream_engine_name": UPSTREAM_RAW_SIGNAL_ENGINE_NAME_V1,
        "preserves_unknown_tokens": True,
        "preserves_competing_layers": True,
        "not_final_meaning_authority": True,
        "not_runtime_authority": True,
        "not_tool_authority": True,
        "not_provider_authority": True,
        "not_search_authority": True,
        "not_proof_authority": True,
        "not_public_claim_authority": True,
    }


def _base_relationship_to_unintelligible_output() -> dict[str, Any]:
    return {
        "role": "axiom_mutation_after_interpretive_preservation",
        "upstream_engine_name": UPSTREAM_INTERPRETIVE_ENGINE_NAME_V1,
        "preserves_competing_interpretations": True,
        "preserves_weak_structure": True,
        "not_final_meaning_authority": True,
        "not_runtime_authority": True,
        "not_tool_authority": True,
        "not_provider_authority": True,
        "not_search_authority": True,
        "not_proof_authority": True,
        "not_public_claim_authority": True,
    }


def _base_relationship_to_signal_vs_noise() -> dict[str, Any]:
    return {
        "role": "axiom_mutation_after_signal_noise_discrimination",
        "upstream_engine_name": UPSTREAM_SIGNAL_NOISE_ENGINE_NAME_V1,
        "preserves_signal_noise_classification": True,
        "preserves_weak_signal_candidates": True,
        "preserves_pseudo_randomness_labels": True,
        "preserves_artifact_effect_labels": True,
        "preserves_undecidable_regions": True,
        "not_final_algorithm_authority": True,
        "not_runtime_authority": True,
        "not_tool_authority": True,
        "not_provider_authority": True,
        "not_search_authority": True,
        "not_proof_authority": True,
        "not_public_claim_authority": True,
    }


def _base_relationship_to_algorithm_emergence() -> dict[str, Any]:
    return {
        "role": "axiom_mutation_after_algorithm_emergence",
        "upstream_engine_name": UPSTREAM_ALGORITHM_EMERGENCE_ENGINE_NAME_V1,
        "preserves_candidate_algorithm_map": True,
        "preserves_operator_chain_candidates": True,
        "preserves_transformation_rule_candidates": True,
        "preserves_invariant_candidates": True,
        "preserves_invalidated_rule_history": True,
        "preserves_terrain_shift_context": True,
        "not_final_math_authority": True,
        "not_runtime_authority": True,
        "not_tool_authority": True,
        "not_provider_authority": True,
        "not_search_authority": True,
        "not_proof_authority": True,
        "not_public_claim_authority": True,
    }


def _base_relationship_to_run() -> dict[str, Any]:
    return {
        "role": "reporting_safety_envelope_only",
        "envelope_only": True,
        "not_engine_kernel": True,
        "not_runtime_authority": True,
        "not_tool_authority": True,
        "not_provider_authority": True,
        "not_search_authority": True,
        "not_proof_authority": True,
        "not_public_claim_authority": True,
    }


def _base_safe_metadata(boundary_summary: str, raw_signal_summary: str, interpretive_summary: str, signal_noise_summary: str, algorithm_emergence_summary: str) -> dict[str, Any]:
    return {
        "helper_type": HELPER_TYPE_V1,
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "boundary_summary": boundary_summary,
        "raw_signal_summary": raw_signal_summary,
        "interpretive_summary": interpretive_summary,
        "signal_noise_summary": signal_noise_summary,
        "algorithm_emergence_summary": algorithm_emergence_summary,
    }


def _coerce_sequence(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, set):
        return list(sorted(value, key=_compact_text))
    return []


def _validate_non_empty_mapping(field_name: str, value: Any, violations: list[str]) -> None:
    if not isinstance(value, Mapping) or not dict(value):
        violations.append(f"{field_name} must be a non-empty mapping")


def _validate_sequence_field(field_name: str, value: Any, violations: list[str]) -> None:
    if not isinstance(value, (list, tuple, set)) or not _coerce_sequence(value):
        violations.append(f"{field_name} must be non-empty")


def _validate_relationship(
    field_name: str,
    value: Any,
    required_fields: tuple[str, ...],
    upstream_engine_name: str | None,
    violations: list[str],
) -> None:
    if not isinstance(value, Mapping):
        violations.append(f"{field_name} must be a mapping")
        return
    for field in required_fields:
        if field not in value:
            violations.append(f"{field_name} missing field: {field}")
    if upstream_engine_name is not None and value.get("upstream_engine_name") != upstream_engine_name:
        violations.append(f"{field_name} upstream engine mismatch")
    for key in value:
        if key.startswith("not_") and value.get(key) is not True:
            violations.append(f"{field_name} must keep {key} true")


def build_mutable_axiom_math_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    boundary = get_cognitive_research_engine_boundary_v1(ENGINE_NAME_V1)
    boundary_summary = summarize_cognitive_research_engine_boundary_v1(boundary)
    raw_signal_boundary = get_cognitive_research_engine_boundary_v1(UPSTREAM_RAW_SIGNAL_ENGINE_NAME_V1)
    raw_signal_summary = summarize_cognitive_research_engine_boundary_v1(raw_signal_boundary)
    interpretive_boundary = get_cognitive_research_engine_boundary_v1(UPSTREAM_INTERPRETIVE_ENGINE_NAME_V1)
    interpretive_summary = summarize_cognitive_research_engine_boundary_v1(interpretive_boundary)
    signal_noise_boundary = get_cognitive_research_engine_boundary_v1(UPSTREAM_SIGNAL_NOISE_ENGINE_NAME_V1)
    signal_noise_summary = summarize_cognitive_research_engine_boundary_v1(signal_noise_boundary)
    algorithm_emergence_boundary = get_cognitive_research_engine_boundary_v1(UPSTREAM_ALGORITHM_EMERGENCE_ENGINE_NAME_V1)
    algorithm_emergence_summary = summarize_cognitive_research_engine_boundary_v1(algorithm_emergence_boundary)
    base = {
        "schema_version": SCHEMA_VERSION_V1,
        "engine_name": ENGINE_NAME_V1,
        "source_boundary_engine_name": ENGINE_NAME_V1,
        "input_category": "synthetic symbolic math terrain",
        "artifact_reference": "synthetic:mutable-axiom-math:artifact:001",
        "artifact_summary": "Synthetic axiom-mutation packet preserving mutable axiom maps, contradiction surfaces, proof obstructions, and terrain shifts.",
        "mutable_axiom_map": {
            "base_axiom": "stable assumption frame",
            "variant_a": "weaken one constraint",
            "variant_b": "strengthen one rule",
        },
        "axiom_variant_candidates": ["variant-a", "variant-b"],
        "rule_perturbation_labels": ["perturb rule one", "perturb rule two"],
        "invariant_shift_labels": ["invariant shift hint", "stability shift hint"],
        "contradiction_surface_notes": ["contradiction surface note one", "contradiction surface note two"],
        "degenerate_case_labels": ["degenerate case one", "degenerate case two"],
        "boundary_case_labels": ["boundary case one", "boundary case two"],
        "toy_model_shift_summaries": ["toy-model shift summary one", "toy-model shift summary two"],
        "proof_obstruction_map": {
            "obstruction_a": "proof path blocked by variant change",
            "obstruction_b": "alternative obstruction pattern retained",
        },
        "consistency_instability_candidates": {
            "consistency_candidate": "bounded consistency pocket",
            "instability_candidate": "instability boundary under mutation",
        },
        "invalidated_axiom_variants": ["variant rejected by contradiction surface"],
        "next_probe_labels": ["vary one axiom", "compare obstruction map", "test nearby boundary case"],
        "relationship_to_raw_signal_cartographer": _base_relationship_to_raw_signal(),
        "relationship_to_unintelligible_output_analyzer": _base_relationship_to_unintelligible_output(),
        "relationship_to_signal_vs_noise": _base_relationship_to_signal_vs_noise(),
        "relationship_to_algorithm_emergence": _base_relationship_to_algorithm_emergence(),
        "relationship_to_cognitive_research_run": _base_relationship_to_run(),
        "safe_metadata": _base_safe_metadata(
            boundary_summary,
            raw_signal_summary,
            interpretive_summary,
            signal_noise_summary,
            algorithm_emergence_summary,
        ),
        "denied_authority": build_default_cognitive_research_denied_authority_v1(),
        "public_claim_status": "blocked_internal_only",
    }
    data = copy.deepcopy(base)
    if isinstance(payload, Mapping):
        data.update(copy.deepcopy(dict(payload)))
    if overrides:
        data.update(copy.deepcopy(overrides))
    data["schema_version"] = SCHEMA_VERSION_V1
    data["engine_name"] = ENGINE_NAME_V1
    data["source_boundary_engine_name"] = ENGINE_NAME_V1
    if not isinstance(data.get("mutable_axiom_map"), Mapping):
        data["mutable_axiom_map"] = copy.deepcopy(base["mutable_axiom_map"])
    else:
        mutable_axiom_map = copy.deepcopy(base["mutable_axiom_map"])
        mutable_axiom_map.update(dict(data["mutable_axiom_map"]))
        data["mutable_axiom_map"] = mutable_axiom_map
    for field, base_value in (
        ("relationship_to_raw_signal_cartographer", _base_relationship_to_raw_signal()),
        ("relationship_to_unintelligible_output_analyzer", _base_relationship_to_unintelligible_output()),
        ("relationship_to_signal_vs_noise", _base_relationship_to_signal_vs_noise()),
        ("relationship_to_algorithm_emergence", _base_relationship_to_algorithm_emergence()),
        ("relationship_to_cognitive_research_run", _base_relationship_to_run()),
    ):
        if not isinstance(data.get(field), Mapping):
            data[field] = copy.deepcopy(base_value)
        else:
            rel = copy.deepcopy(base_value)
            rel.update(dict(data[field]))
            data[field] = rel
    if not isinstance(data.get("safe_metadata"), Mapping):
        data["safe_metadata"] = _base_safe_metadata(
            boundary_summary,
            raw_signal_summary,
            interpretive_summary,
            signal_noise_summary,
            algorithm_emergence_summary,
        )
    else:
        safe_metadata = _base_safe_metadata(
            boundary_summary,
            raw_signal_summary,
            interpretive_summary,
            signal_noise_summary,
            algorithm_emergence_summary,
        )
        safe_metadata.update(dict(data["safe_metadata"]))
        data["safe_metadata"] = safe_metadata
    denied = build_default_cognitive_research_denied_authority_v1()
    if isinstance(data.get("denied_authority"), Mapping):
        denied.update({str(k): bool(v) for k, v in dict(data["denied_authority"]).items() if k in denied})
    data["denied_authority"] = denied
    data.setdefault("public_claim_status", "blocked_internal_only")
    return data


def validate_mutable_axiom_math_packet_v1(packet: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(packet, Mapping):
        return {"valid": False, "violation_count": 1, "violations": ["packet must be a mapping"]}

    packet_dict = dict(packet)
    registry = build_cognitive_research_engine_boundary_registry_v1()
    boundary = registry.get(ENGINE_NAME_V1)
    if boundary is None:
        violations.append("boundary registry missing MUTABLE_AXIOM_MATH_ENGINE")
        boundary_valid = False
    else:
        boundary_result = validate_cognitive_research_engine_boundary_v1(boundary)
        boundary_valid = bool(boundary_result.get("valid"))
        if not boundary_valid:
            violations.append("source boundary metadata invalid")

    if packet_dict.get("engine_name") != ENGINE_NAME_V1:
        violations.append("engine_name must be MUTABLE_AXIOM_MATH_ENGINE")
    if packet_dict.get("source_boundary_engine_name") != ENGINE_NAME_V1:
        violations.append("source_boundary_engine_name must be MUTABLE_AXIOM_MATH_ENGINE")

    for field in _REQUIRED_PACKET_FIELDS_V1:
        if field not in packet_dict:
            violations.append(f"missing required field: {field}")

    text_fields = [
        "schema_version",
        "engine_name",
        "source_boundary_engine_name",
        "input_category",
        "artifact_reference",
        "artifact_summary",
        "public_claim_status",
    ]
    for field in text_fields:
        text = _compact_text(packet_dict.get(field))
        if not text:
            violations.append(f"missing required text field: {field}")
            continue
        if _has_forbidden_markers(text):
            violations.append(f"forbidden marker detected in {field}")

    if packet_dict.get("schema_version") != SCHEMA_VERSION_V1:
        violations.append("schema_version mismatch")

    artifact_reference = _compact_text(packet_dict.get("artifact_reference"))
    if len(artifact_reference) > 240 or "\n" in str(packet_dict.get("artifact_reference", "")):
        violations.append("artifact_reference must be a short reference, not pasted raw artifact")

    artifact_summary = _compact_text(packet_dict.get("artifact_summary"))
    if len(artifact_summary) > 900 or artifact_summary.count("\n") > 2:
        violations.append("artifact_summary must remain bounded")

    for field in (
        "axiom_variant_candidates",
        "rule_perturbation_labels",
        "invariant_shift_labels",
        "contradiction_surface_notes",
        "degenerate_case_labels",
        "boundary_case_labels",
        "toy_model_shift_summaries",
        "invalidated_axiom_variants",
        "next_probe_labels",
    ):
        _validate_sequence_field(field, packet_dict.get(field), violations)

    _validate_non_empty_mapping("mutable_axiom_map", packet_dict.get("mutable_axiom_map"), violations)
    _validate_non_empty_mapping("proof_obstruction_map", packet_dict.get("proof_obstruction_map"), violations)
    _validate_non_empty_mapping(
        "consistency_instability_candidates",
        packet_dict.get("consistency_instability_candidates"),
        violations,
    )

    _validate_relationship(
        "relationship_to_raw_signal_cartographer",
        packet_dict.get("relationship_to_raw_signal_cartographer"),
        _REQUIRED_RAW_SIGNAL_RELATIONSHIP_FIELDS_V1,
        UPSTREAM_RAW_SIGNAL_ENGINE_NAME_V1,
        violations,
    )
    _validate_relationship(
        "relationship_to_unintelligible_output_analyzer",
        packet_dict.get("relationship_to_unintelligible_output_analyzer"),
        _REQUIRED_INTERPRETIVE_RELATIONSHIP_FIELDS_V1,
        UPSTREAM_INTERPRETIVE_ENGINE_NAME_V1,
        violations,
    )
    _validate_relationship(
        "relationship_to_signal_vs_noise",
        packet_dict.get("relationship_to_signal_vs_noise"),
        _REQUIRED_SIGNAL_NOISE_RELATIONSHIP_FIELDS_V1,
        UPSTREAM_SIGNAL_NOISE_ENGINE_NAME_V1,
        violations,
    )
    _validate_relationship(
        "relationship_to_algorithm_emergence",
        packet_dict.get("relationship_to_algorithm_emergence"),
        _REQUIRED_ALGORITHM_EMERGENCE_RELATIONSHIP_FIELDS_V1,
        UPSTREAM_ALGORITHM_EMERGENCE_ENGINE_NAME_V1,
        violations,
    )
    _validate_relationship(
        "relationship_to_cognitive_research_run",
        packet_dict.get("relationship_to_cognitive_research_run"),
        _REQUIRED_RELATIONSHIP_FIELDS_V1,
        None,
        violations,
    )

    public_claim_status = _compact_text(packet_dict.get("public_claim_status"))
    if public_claim_status not in _REQUIRED_PUBLIC_CLAIM_STATUS_V1:
        violations.append("public_claim_status must be an allowed restricted status")
    if any(marker in public_claim_status.lower() for marker in _FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        violations.append("public claim drift detected")

    denied_authority = packet_dict.get("denied_authority")
    if not isinstance(denied_authority, Mapping):
        violations.append("denied_authority must be a mapping")
    else:
        default_denied = build_default_cognitive_research_denied_authority_v1()
        for key in default_denied:
            if key not in denied_authority:
                violations.append(f"denied_authority missing key: {key}")
            elif denied_authority.get(key) is not False:
                violations.append(f"denied_authority key must remain false: {key}")

    safe_metadata = packet_dict.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        violations.append("safe_metadata must be a mapping")
    else:
        if safe_metadata.get("metadata_only") is not True:
            violations.append("safe_metadata must remain metadata_only")

    if not isinstance(packet_dict.get("mutable_axiom_map"), Mapping) or len(packet_dict.get("mutable_axiom_map", {})) < 2:
        violations.append("mutable_axiom_map must preserve multiple axiom variants")

    if _has_forbidden_markers(packet_dict):
        violations.append("forbidden marker detected in packet")

    if any(marker in _compact_text(packet_dict.get("artifact_summary")).lower() for marker in _FORBIDDEN_FLATTENING_MARKERS_V1):
        violations.append("flattening marker detected in artifact_summary")

    if not boundary_valid:
        violations.append("source boundary validation failed")

    return {
        "valid": not violations,
        "violation_count": len(violations),
        "violations": violations,
        "summary": summarize_mutable_axiom_math_packet_v1(packet_dict),
    }


def summarize_mutable_axiom_math_packet_v1(packet: Any) -> str:
    if not isinstance(packet, Mapping):
        return "invalid mutable axiom math packet"
    engine_name = _compact_text(packet.get("engine_name"), default=ENGINE_NAME_V1)
    ref = _compact_text(packet.get("artifact_reference"), default="ref:unknown")
    input_category = _compact_text(packet.get("input_category"), default="unknown")
    variants = len(_coerce_sequence(packet.get("axiom_variant_candidates")))
    perturbations = len(_coerce_sequence(packet.get("rule_perturbation_labels")))
    invariants = len(_coerce_sequence(packet.get("invariant_shift_labels")))
    contradictions = len(_coerce_sequence(packet.get("contradiction_surface_notes")))
    degenerates = len(_coerce_sequence(packet.get("degenerate_case_labels")))
    boundaries = len(_coerce_sequence(packet.get("boundary_case_labels")))
    toys = len(_coerce_sequence(packet.get("toy_model_shift_summaries")))
    public_status = _compact_text(packet.get("public_claim_status"), default="blocked_internal_only")
    summary = (
        f"{engine_name} packet | input={input_category} | ref={ref} | variants={variants} | perturbations={perturbations} | invariants={invariants} | contradictions={contradictions} | degenerates={degenerates} | boundaries={boundaries} | toy_models={toys} | public={public_status}"
    )
    if isinstance(packet.get("safe_metadata"), Mapping):
        boundary_summary = _compact_text(packet["safe_metadata"].get("boundary_summary"), default="")
        if boundary_summary:
            summary += f" | boundary={boundary_summary}"
    return summary[:900]


def to_mutable_axiom_math_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def build_initial_mutable_axiom_math_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    specs = [
        {
            "artifact_reference": "synthetic:mutable-axiom-math:artifact:layer-001",
            "artifact_summary": "Synthetic axiom-mutation fragment with contradiction surfaces, proof obstructions, and boundary cases.",
            "mutable_axiom_map": {
                "base_axiom": "stable assumption frame",
                "variant_a": "weaken one constraint",
                "variant_b": "strengthen one rule",
            },
            "axiom_variant_candidates": ["variant-a", "variant-b"],
            "rule_perturbation_labels": ["perturb rule one", "perturb rule two"],
            "invariant_shift_labels": ["invariant shift hint", "stability shift hint"],
            "contradiction_surface_notes": ["contradiction surface note one", "contradiction surface note two"],
            "degenerate_case_labels": ["degenerate case one", "degenerate case two"],
            "boundary_case_labels": ["boundary case one", "boundary case two"],
            "toy_model_shift_summaries": ["toy-model shift summary one", "toy-model shift summary two"],
            "proof_obstruction_map": {
                "obstruction_a": "proof path blocked by variant change",
                "obstruction_b": "alternative obstruction pattern retained",
            },
            "consistency_instability_candidates": {
                "consistency_candidate": "bounded consistency pocket",
                "instability_candidate": "instability boundary under mutation",
            },
            "invalidated_axiom_variants": ["variant rejected by contradiction surface"],
            "next_probe_labels": ["vary one axiom", "compare obstruction map"],
        },
        {
            "artifact_reference": "synthetic:mutable-axiom-math:artifact:layer-002",
            "artifact_summary": "Synthetic terrain map emphasizing toy-model shifts, invalidation history, and boundary-case labels.",
            "mutable_axiom_map": {
                "base_axiom": "symbolic premise",
                "variant_a": "shift quantifier scope",
                "variant_b": "replace operator rule",
            },
            "axiom_variant_candidates": ["variant-c", "variant-d"],
            "rule_perturbation_labels": ["perturb operator arity", "perturb inference order"],
            "invariant_shift_labels": ["preserved invariant", "shifted invariant"],
            "contradiction_surface_notes": ["surface remains thin", "surface thickens under mutation"],
            "degenerate_case_labels": ["collapse to degenerate toy frame", "boundary degeneracy"],
            "boundary_case_labels": ["hard boundary case", "soft boundary case"],
            "toy_model_shift_summaries": ["toy model becomes unstable", "toy model stabilizes locally"],
            "proof_obstruction_map": {
                "obstruction_a": "proof obstruction persists across variants",
                "obstruction_b": "new obstruction appears after perturbation",
            },
            "consistency_instability_candidates": {
                "consistency_candidate": "small consistency region",
                "instability_candidate": "consistency breaks beyond threshold",
            },
            "invalidated_axiom_variants": ["variant dropped after inconsistency"],
            "next_probe_labels": ["compare nearby boundary cases", "track invalidation reasons"],
        },
        {
            "artifact_reference": "synthetic:mutable-axiom-math:artifact:layer-003",
            "artifact_summary": "Synthetic axiom packet preserving contradiction notes, proof obstruction maps, and uncertainty.",
            "mutable_axiom_map": {
                "base_axiom": "reference assumption",
                "variant_a": "weaken a side condition",
                "variant_b": "introduce bounded exception",
            },
            "axiom_variant_candidates": ["variant-e", "variant-f"],
            "rule_perturbation_labels": ["perturb side condition", "perturb boundary rule"],
            "invariant_shift_labels": ["invariant survives", "invariant fractures"],
            "contradiction_surface_notes": ["contradiction surface expands", "contradiction surface recedes"],
            "degenerate_case_labels": ["degenerate proof frame", "degenerate boundary frame"],
            "boundary_case_labels": ["boundary case with unstable semantics", "boundary case with stable semantics"],
            "toy_model_shift_summaries": ["toy model reveals a shifted regime", "toy model keeps a local pocket"],
            "proof_obstruction_map": {
                "obstruction_a": "local proof path blocked",
                "obstruction_b": "alternative proof path remains obstructed",
            },
            "consistency_instability_candidates": {
                "consistency_candidate": "localized consistency",
                "instability_candidate": "localized instability",
            },
            "invalidated_axiom_variants": ["variant ruled out by contradiction history"],
            "next_probe_labels": ["probe a nearby variant", "re-check proof obstruction map"],
        },
    ]
    for spec in specs:
        examples.append(build_mutable_axiom_math_packet_v1(spec))
    return examples
