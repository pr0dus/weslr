"""Metadata-only helpers for ALGORITHM_EMERGENCE_ENGINE v1.

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

SCHEMA_VERSION_V1 = "algorithm_emergence_v1"
ENGINE_NAME_V1 = "ALGORITHM_EMERGENCE_ENGINE"
UPSTREAM_RAW_SIGNAL_ENGINE_NAME_V1 = "RAW_SIGNAL_CARTOGRAPHER"
UPSTREAM_INTERPRETIVE_ENGINE_NAME_V1 = "UNINTELLIGIBLE_OUTPUT_ANALYZER"
UPSTREAM_SIGNAL_NOISE_ENGINE_NAME_V1 = "SIGNAL_VS_NOISE_ENGINE"
HELPER_TYPE_V1 = "weslr_algorithm_emergence_engine_helpers_v1"

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw private data",
    "raw private text",
    "secret",
    "hidden/system prompt",
    "hidden prompt",
    "system prompt",
    ".weslr",
    "executable code-as-action",
    "live tool instructions",
    "provider/model output",
    "model output claimed as authority",
    "dangerous procedural instructions",
    "step-by-step",
    "how to exploit",
    "exploit chain",
    "malware",
    "credential theft",
    "programming assistant",
    "proof solver",
    "math solver",
    "generic pattern summary",
    "confirmed algorithm discovery",
    "algorithm discovery",
)

_FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1 = (
    "proof",
    "solved",
    "breakthrough",
    "certification",
    "benchmark",
    "public ready",
    "public-ready",
    "official result",
    "confirmed algorithm discovery",
    "algorithm discovery",
)

_FORBIDDEN_FLATTENING_MARKERS_V1 = (
    "programming assistant",
    "proof solver",
    "math solver",
    "generic pattern summary",
    "generic assistant",
    "normalizer",
    "solved algorithm",
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
    "candidate_algorithm_map",
    "operator_chain_candidates",
    "transformation_rule_candidates",
    "state_transition_hints",
    "invariant_candidates",
    "recursion_self_similarity_labels",
    "algorithm_likeness_confidence_map",
    "invalidated_rule_candidates",
    "undecidable_process_regions",
    "next_probe_labels",
    "relationship_to_raw_signal_cartographer",
    "relationship_to_unintelligible_output_analyzer",
    "relationship_to_signal_vs_noise",
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
        "role": "algorithm_inference_after_raw_signal",
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
        "role": "algorithm_inference_after_interpretation_preservation",
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
        "role": "algorithm_inference_after_signal_noise_discrimination",
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



def _base_relationship_to_run() -> dict[str, Any]:
    return {
        "role": "metadata_only_envelope",
        "envelope_only": True,
        "not_engine_kernel": True,
        "not_runtime_authority": True,
        "not_tool_authority": True,
        "not_provider_authority": True,
        "not_search_authority": True,
        "not_proof_authority": True,
        "not_public_claim_authority": True,
    }



def _base_safe_metadata(boundary_summary: str, raw_signal_summary: str, interpretive_summary: str, signal_noise_summary: str) -> dict[str, Any]:
    return {
        "metadata_only": True,
        "non_executing": True,
        "json_safe": True,
        "non_public": True,
        "engine_family": "gap",
        "boundary_summary": boundary_summary,
        "upstream_raw_signal_summary": raw_signal_summary,
        "upstream_interpretive_summary": interpretive_summary,
        "upstream_signal_noise_summary": signal_noise_summary,
    }



def _coerce_sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]



def build_algorithm_emergence_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    boundary = get_cognitive_research_engine_boundary_v1(ENGINE_NAME_V1)
    boundary_summary = summarize_cognitive_research_engine_boundary_v1(boundary)
    raw_signal_boundary = get_cognitive_research_engine_boundary_v1(UPSTREAM_RAW_SIGNAL_ENGINE_NAME_V1)
    raw_signal_summary = summarize_cognitive_research_engine_boundary_v1(raw_signal_boundary)
    interpretive_boundary = get_cognitive_research_engine_boundary_v1(UPSTREAM_INTERPRETIVE_ENGINE_NAME_V1)
    interpretive_summary = summarize_cognitive_research_engine_boundary_v1(interpretive_boundary)
    signal_noise_boundary = get_cognitive_research_engine_boundary_v1(UPSTREAM_SIGNAL_NOISE_ENGINE_NAME_V1)
    signal_noise_summary = summarize_cognitive_research_engine_boundary_v1(signal_noise_boundary)
    base = {
        "schema_version": SCHEMA_VERSION_V1,
        "engine_name": ENGINE_NAME_V1,
        "source_boundary_engine_name": ENGINE_NAME_V1,
        "input_category": "synthetic symbolic stream",
        "artifact_reference": "synthetic:algorithm-emergence:artifact:001",
        "artifact_summary": "Synthetic algorithm-emergence packet preserving operator chains, invariants, recursion hints, and undecidable process regions.",
        "candidate_algorithm_map": {
            "candidate_a": "process-like chain with repeated operator transitions",
            "candidate_b": "structured rule path with invariant-preserving steps",
        },
        "operator_chain_candidates": ["chain-a", "chain-b"],
        "transformation_rule_candidates": ["rule-a", "rule-b"],
        "state_transition_hints": ["transition hint one", "transition hint two"],
        "invariant_candidates": ["invariant candidate one", "invariant candidate two"],
        "recursion_self_similarity_labels": ["self-similarity hint", "recursion hint"],
        "algorithm_likeness_confidence_map": {"likeness": "bounded", "confidence": "mixed", "uncertainty": "tracked"},
        "invalidated_rule_candidates": ["rule candidate rejected"],
        "undecidable_process_regions": ["undecidable process band"],
        "next_probe_labels": ["vary one step", "compare operator-chain persistence"],
        "relationship_to_raw_signal_cartographer": _base_relationship_to_raw_signal(),
        "relationship_to_unintelligible_output_analyzer": _base_relationship_to_unintelligible_output(),
        "relationship_to_signal_vs_noise": _base_relationship_to_signal_vs_noise(),
        "relationship_to_cognitive_research_run": _base_relationship_to_run(),
        "safe_metadata": _base_safe_metadata(boundary_summary, raw_signal_summary, interpretive_summary, signal_noise_summary),
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
    if not isinstance(data.get("candidate_algorithm_map"), Mapping):
        data["candidate_algorithm_map"] = copy.deepcopy(base["candidate_algorithm_map"])
    if not isinstance(data.get("relationship_to_raw_signal_cartographer"), Mapping):
        data["relationship_to_raw_signal_cartographer"] = _base_relationship_to_raw_signal()
    else:
        rel = _base_relationship_to_raw_signal()
        rel.update(dict(data["relationship_to_raw_signal_cartographer"]))
        data["relationship_to_raw_signal_cartographer"] = rel
    if not isinstance(data.get("relationship_to_unintelligible_output_analyzer"), Mapping):
        data["relationship_to_unintelligible_output_analyzer"] = _base_relationship_to_unintelligible_output()
    else:
        rel = _base_relationship_to_unintelligible_output()
        rel.update(dict(data["relationship_to_unintelligible_output_analyzer"]))
        data["relationship_to_unintelligible_output_analyzer"] = rel
    if not isinstance(data.get("relationship_to_signal_vs_noise"), Mapping):
        data["relationship_to_signal_vs_noise"] = _base_relationship_to_signal_vs_noise()
    else:
        rel = _base_relationship_to_signal_vs_noise()
        rel.update(dict(data["relationship_to_signal_vs_noise"]))
        data["relationship_to_signal_vs_noise"] = rel
    if not isinstance(data.get("relationship_to_cognitive_research_run"), Mapping):
        data["relationship_to_cognitive_research_run"] = _base_relationship_to_run()
    else:
        rel = _base_relationship_to_run()
        rel.update(dict(data["relationship_to_cognitive_research_run"]))
        data["relationship_to_cognitive_research_run"] = rel
    if not isinstance(data.get("safe_metadata"), Mapping):
        data["safe_metadata"] = _base_safe_metadata(boundary_summary, raw_signal_summary, interpretive_summary, signal_noise_summary)
    else:
        safe_metadata = _base_safe_metadata(boundary_summary, raw_signal_summary, interpretive_summary, signal_noise_summary)
        safe_metadata.update(dict(data["safe_metadata"]))
        data["safe_metadata"] = safe_metadata
    denied = build_default_cognitive_research_denied_authority_v1()
    if isinstance(data.get("denied_authority"), Mapping):
        denied.update({str(k): bool(v) for k, v in dict(data["denied_authority"]).items() if k in denied})
    data["denied_authority"] = denied
    data.setdefault("public_claim_status", "blocked_internal_only")
    return data



def validate_algorithm_emergence_packet_v1(packet: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(packet, Mapping):
        return {"valid": False, "violation_count": 1, "violations": ["packet must be a mapping"]}

    packet_dict = dict(packet)
    registry = build_cognitive_research_engine_boundary_registry_v1()
    boundary = registry.get(ENGINE_NAME_V1)
    if boundary is None:
        violations.append("boundary registry missing ALGORITHM_EMERGENCE_ENGINE")
        boundary_valid = False
    else:
        boundary_result = validate_cognitive_research_engine_boundary_v1(boundary)
        boundary_valid = bool(boundary_result.get("valid"))
        if not boundary_valid:
            violations.append("source boundary metadata invalid")

    if packet_dict.get("engine_name") != ENGINE_NAME_V1:
        violations.append("engine_name must be ALGORITHM_EMERGENCE_ENGINE")
    if packet_dict.get("source_boundary_engine_name") != ENGINE_NAME_V1:
        violations.append("source_boundary_engine_name must be ALGORITHM_EMERGENCE_ENGINE")

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
        "operator_chain_candidates",
        "transformation_rule_candidates",
        "state_transition_hints",
        "invariant_candidates",
        "recursion_self_similarity_labels",
        "invalidated_rule_candidates",
        "undecidable_process_regions",
        "next_probe_labels",
    ):
        value = packet_dict.get(field)
        if not isinstance(value, (list, tuple)) or not _coerce_sequence(value):
            violations.append(f"{field} must be non-empty")

    candidate_algorithm_map = packet_dict.get("candidate_algorithm_map")
    if not isinstance(candidate_algorithm_map, Mapping) or len(candidate_algorithm_map) < 2:
        violations.append("candidate_algorithm_map must preserve multiple algorithm candidates")

    algorithm_confidence = packet_dict.get("algorithm_likeness_confidence_map")
    if not isinstance(algorithm_confidence, Mapping):
        violations.append("algorithm_likeness_confidence_map must be a mapping")

    raw_signal_relationship = packet_dict.get("relationship_to_raw_signal_cartographer")
    if not isinstance(raw_signal_relationship, Mapping):
        violations.append("relationship_to_raw_signal_cartographer must be a mapping")
    else:
        for field in _REQUIRED_RAW_SIGNAL_RELATIONSHIP_FIELDS_V1:
            if field not in raw_signal_relationship:
                violations.append(f"relationship_to_raw_signal_cartographer missing field: {field}")
        if raw_signal_relationship.get("upstream_engine_name") != UPSTREAM_RAW_SIGNAL_ENGINE_NAME_V1:
            violations.append("relationship_to_raw_signal_cartographer upstream engine mismatch")
        if raw_signal_relationship.get("preserves_unknown_tokens") is not True:
            violations.append("relationship_to_raw_signal_cartographer must preserve unknown tokens")
        if raw_signal_relationship.get("preserves_competing_layers") is not True:
            violations.append("relationship_to_raw_signal_cartographer must preserve competing layers")
        if raw_signal_relationship.get("not_final_meaning_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not claim final meaning authority")
        if raw_signal_relationship.get("not_runtime_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not have runtime authority")
        if raw_signal_relationship.get("not_tool_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not have tool authority")
        if raw_signal_relationship.get("not_provider_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not have provider authority")
        if raw_signal_relationship.get("not_search_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not have search authority")
        if raw_signal_relationship.get("not_proof_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not have proof authority")
        if raw_signal_relationship.get("not_public_claim_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not have public claim authority")

    interpretive_relationship = packet_dict.get("relationship_to_unintelligible_output_analyzer")
    if not isinstance(interpretive_relationship, Mapping):
        violations.append("relationship_to_unintelligible_output_analyzer must be a mapping")
    else:
        for field in _REQUIRED_INTERPRETIVE_RELATIONSHIP_FIELDS_V1:
            if field not in interpretive_relationship:
                violations.append(f"relationship_to_unintelligible_output_analyzer missing field: {field}")
        if interpretive_relationship.get("upstream_engine_name") != UPSTREAM_INTERPRETIVE_ENGINE_NAME_V1:
            violations.append("relationship_to_unintelligible_output_analyzer upstream engine mismatch")
        if interpretive_relationship.get("preserves_competing_interpretations") is not True:
            violations.append("relationship_to_unintelligible_output_analyzer must preserve competing interpretations")
        if interpretive_relationship.get("preserves_weak_structure") is not True:
            violations.append("relationship_to_unintelligible_output_analyzer must preserve weak structure")
        if interpretive_relationship.get("not_final_meaning_authority") is not True:
            violations.append("relationship_to_unintelligible_output_analyzer must not claim final meaning authority")
        if interpretive_relationship.get("not_runtime_authority") is not True:
            violations.append("relationship_to_unintelligible_output_analyzer must not have runtime authority")
        if interpretive_relationship.get("not_tool_authority") is not True:
            violations.append("relationship_to_unintelligible_output_analyzer must not have tool authority")
        if interpretive_relationship.get("not_provider_authority") is not True:
            violations.append("relationship_to_unintelligible_output_analyzer must not have provider authority")
        if interpretive_relationship.get("not_search_authority") is not True:
            violations.append("relationship_to_unintelligible_output_analyzer must not have search authority")
        if interpretive_relationship.get("not_proof_authority") is not True:
            violations.append("relationship_to_unintelligible_output_analyzer must not have proof authority")
        if interpretive_relationship.get("not_public_claim_authority") is not True:
            violations.append("relationship_to_unintelligible_output_analyzer must not have public claim authority")

    signal_noise_relationship = packet_dict.get("relationship_to_signal_vs_noise")
    if not isinstance(signal_noise_relationship, Mapping):
        violations.append("relationship_to_signal_vs_noise must be a mapping")
    else:
        for field in _REQUIRED_SIGNAL_NOISE_RELATIONSHIP_FIELDS_V1:
            if field not in signal_noise_relationship:
                violations.append(f"relationship_to_signal_vs_noise missing field: {field}")
        if signal_noise_relationship.get("upstream_engine_name") != UPSTREAM_SIGNAL_NOISE_ENGINE_NAME_V1:
            violations.append("relationship_to_signal_vs_noise upstream engine mismatch")
        if signal_noise_relationship.get("preserves_signal_noise_classification") is not True:
            violations.append("relationship_to_signal_vs_noise must preserve signal/noise classification")
        if signal_noise_relationship.get("preserves_weak_signal_candidates") is not True:
            violations.append("relationship_to_signal_vs_noise must preserve weak signal candidates")
        if signal_noise_relationship.get("preserves_pseudo_randomness_labels") is not True:
            violations.append("relationship_to_signal_vs_noise must preserve pseudo-randomness labels")
        if signal_noise_relationship.get("preserves_artifact_effect_labels") is not True:
            violations.append("relationship_to_signal_vs_noise must preserve artifact-effect labels")
        if signal_noise_relationship.get("preserves_undecidable_regions") is not True:
            violations.append("relationship_to_signal_vs_noise must preserve undecidable regions")
        if signal_noise_relationship.get("not_final_algorithm_authority") is not True:
            violations.append("relationship_to_signal_vs_noise must not claim final algorithm authority")
        if signal_noise_relationship.get("not_runtime_authority") is not True:
            violations.append("relationship_to_signal_vs_noise must not have runtime authority")
        if signal_noise_relationship.get("not_tool_authority") is not True:
            violations.append("relationship_to_signal_vs_noise must not have tool authority")
        if signal_noise_relationship.get("not_provider_authority") is not True:
            violations.append("relationship_to_signal_vs_noise must not have provider authority")
        if signal_noise_relationship.get("not_search_authority") is not True:
            violations.append("relationship_to_signal_vs_noise must not have search authority")
        if signal_noise_relationship.get("not_proof_authority") is not True:
            violations.append("relationship_to_signal_vs_noise must not have proof authority")
        if signal_noise_relationship.get("not_public_claim_authority") is not True:
            violations.append("relationship_to_signal_vs_noise must not have public claim authority")

    run_relationship = packet_dict.get("relationship_to_cognitive_research_run")
    if not isinstance(run_relationship, Mapping):
        violations.append("relationship_to_cognitive_research_run must be a mapping")
    else:
        for field in _REQUIRED_RELATIONSHIP_FIELDS_V1:
            if field not in run_relationship:
                violations.append(f"relationship_to_cognitive_research_run missing field: {field}")
        if run_relationship.get("envelope_only") is not True:
            violations.append("CognitiveResearchRunV1 must remain envelope only")
        if run_relationship.get("not_engine_kernel") is not True:
            violations.append("CognitiveResearchRunV1 must not be engine kernel")
        if run_relationship.get("not_runtime_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have runtime authority")
        if run_relationship.get("not_tool_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have tool authority")
        if run_relationship.get("not_provider_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have provider authority")
        if run_relationship.get("not_search_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have search authority")
        if run_relationship.get("not_proof_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have proof authority")
        if run_relationship.get("not_public_claim_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have public claim authority")

    denied = packet_dict.get("denied_authority")
    if not isinstance(denied, Mapping):
        violations.append("denied_authority must be a mapping")
    else:
        if not denied:
            violations.append("denied_authority must not be empty")
        for key, value in denied.items():
            if value is not False:
                violations.append(f"denied_authority field must be false: {key}")

    public_status = _compact_text(packet_dict.get("public_claim_status"))
    if public_status not in _REQUIRED_PUBLIC_CLAIM_STATUS_V1:
        violations.append("public_claim_status must be a blocked or internal-only status")
    if any(marker in public_status.lower() for marker in _FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        violations.append("public_claim_status suggests forbidden public claim drift")

    flattening_blob = json.dumps(_json_safe({
        "candidate_algorithm_map": packet_dict.get("candidate_algorithm_map"),
        "operator_chain_candidates": packet_dict.get("operator_chain_candidates"),
        "transformation_rule_candidates": packet_dict.get("transformation_rule_candidates"),
        "state_transition_hints": packet_dict.get("state_transition_hints"),
        "invariant_candidates": packet_dict.get("invariant_candidates"),
        "recursion_self_similarity_labels": packet_dict.get("recursion_self_similarity_labels"),
        "invalidated_rule_candidates": packet_dict.get("invalidated_rule_candidates"),
        "undecidable_process_regions": packet_dict.get("undecidable_process_regions"),
    }), sort_keys=True, ensure_ascii=True).lower()
    if any(marker in flattening_blob for marker in _FORBIDDEN_FLATTENING_MARKERS_V1):
        violations.append("packet flattens algorithm emergence into a generic solver or summary too early")

    if _has_forbidden_markers(packet_dict):
        violations.append("forbidden marker detected in packet")

    safe_metadata = packet_dict.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        violations.append("safe_metadata must be a mapping")
    else:
        if safe_metadata.get("metadata_only") is not True:
            violations.append("safe_metadata must remain metadata_only")

    if not boundary_valid:
        violations.append("source boundary validation failed")

    return {
        "valid": not violations,
        "violation_count": len(violations),
        "violations": violations,
        "summary": summarize_algorithm_emergence_packet_v1(packet_dict),
    }



def summarize_algorithm_emergence_packet_v1(packet: Any) -> str:
    if not isinstance(packet, Mapping):
        return "invalid algorithm emergence packet"
    engine_name = _compact_text(packet.get("engine_name"), default=ENGINE_NAME_V1)
    ref = _compact_text(packet.get("artifact_reference"), default="ref:unknown")
    input_category = _compact_text(packet.get("input_category"), default="unknown")
    candidates = len(packet.get("candidate_algorithm_map", {})) if isinstance(packet.get("candidate_algorithm_map"), Mapping) else 0
    chains = len(_coerce_sequence(packet.get("operator_chain_candidates")))
    rules = len(_coerce_sequence(packet.get("transformation_rule_candidates")))
    invariants = len(_coerce_sequence(packet.get("invariant_candidates")))
    recursion = len(_coerce_sequence(packet.get("recursion_self_similarity_labels")))
    undecidable = len(_coerce_sequence(packet.get("undecidable_process_regions")))
    public_status = _compact_text(packet.get("public_claim_status"), default="blocked_internal_only")
    summary = (
        f"{engine_name} packet | input={input_category} | ref={ref} | candidates={candidates} | chains={chains} | rules={rules} | invariants={invariants} | recursion={recursion} | undecidable={undecidable} | public={public_status}"
    )
    if isinstance(packet.get("safe_metadata"), Mapping):
        boundary_summary = _compact_text(packet["safe_metadata"].get("boundary_summary"), default="")
        if boundary_summary:
            summary += f" | boundary={boundary_summary}"
    return summary[:900]



def to_algorithm_emergence_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def build_initial_algorithm_emergence_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    specs = [
        {
            "artifact_reference": "synthetic:algorithm-emergence:artifact:layer-001",
            "artifact_summary": "Synthetic process-like fragment with chain candidates, invariant hints, and undecidable regions.",
            "candidate_algorithm_map": {
                "candidate_a": "rule-like chain with repeated state transitions",
                "candidate_b": "structured path with invariant preservation",
            },
            "operator_chain_candidates": ["chain-a", "chain-b"],
            "transformation_rule_candidates": ["rule-a", "rule-b"],
            "state_transition_hints": ["transition hint one", "transition hint two"],
            "invariant_candidates": ["invariant candidate one", "invariant candidate two"],
            "recursion_self_similarity_labels": ["self-similarity hint", "recursion hint"],
            "algorithm_likeness_confidence_map": {"likeness": "bounded", "confidence": "mixed"},
            "invalidated_rule_candidates": ["rule candidate rejected"],
            "undecidable_process_regions": ["undecidable process band"],
        },
        {
            "artifact_reference": "synthetic:algorithm-emergence:artifact:layer-002",
            "artifact_summary": "Synthetic operator-chain packet preserving recursive hints and invalidated rules.",
            "candidate_algorithm_map": {
                "candidate_a": "chain with repeated operators",
                "candidate_b": "chain with state shift and invariant survival",
            },
            "operator_chain_candidates": ["chain-one", "chain-two"],
            "transformation_rule_candidates": ["replace-step", "perturb-step"],
            "state_transition_hints": ["state shift hint"],
            "invariant_candidates": ["invariant survival hint"],
            "recursion_self_similarity_labels": ["recursive pattern hint"],
            "algorithm_likeness_confidence_map": {"likeness": "mixed", "uncertainty": "tracked"},
            "invalidated_rule_candidates": ["generic summary rejected"],
            "undecidable_process_regions": ["undecidable loop"],
        },
        {
            "artifact_reference": "synthetic:algorithm-emergence:artifact:layer-003",
            "artifact_summary": "Synthetic algorithm-emergence summary that keeps undecidable process texture and rule invalidation notes.",
            "candidate_algorithm_map": {
                "candidate_a": "rule path under pressure",
                "candidate_b": "alternate operator path",
            },
            "operator_chain_candidates": ["chain-alpha", "chain-beta"],
            "transformation_rule_candidates": ["rule-alpha", "rule-beta"],
            "state_transition_hints": ["transition alpha"],
            "invariant_candidates": ["invariant alpha"],
            "recursion_self_similarity_labels": ["self-similarity alpha"],
            "algorithm_likeness_confidence_map": {"likeness": "uncertain", "confidence": "bounded"},
            "invalidated_rule_candidates": ["operator chain rejected"],
            "undecidable_process_regions": ["undecidable edge zone"],
        },
    ]
    for index, spec in enumerate(specs, start=1):
        packet = build_algorithm_emergence_packet_v1(spec)
        packet["example_id"] = _payload_marker("algorithm_emergence_example", {"index": index, "artifact_reference": packet["artifact_reference"]})
        packet["example_label"] = f"algorithm_emergence_example_{index}"
        examples.append(packet)
    return examples
