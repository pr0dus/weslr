"""Metadata-only helpers for RAW_SIGNAL_CARTOGRAPHER v1.

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

SCHEMA_VERSION_V1 = "raw_signal_cartography_v1"
ENGINE_NAME_V1 = "RAW_SIGNAL_CARTOGRAPHER"
HELPER_TYPE_V1 = "weslr_raw_signal_cartographer_helpers_v1"

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
)

_REQUIRED_PACKET_FIELDS_V1 = (
    "schema_version",
    "engine_name",
    "source_boundary_engine_name",
    "input_category",
    "artifact_reference",
    "artifact_summary",
    "terrain_primitives",
    "motif_candidates",
    "weak_signal_labels",
    "stable_region_labels",
    "unstable_region_labels",
    "noise_region_labels",
    "boundary_region_labels",
    "candidate_grammar_labels",
    "operator_transformation_labels",
    "uncertainty_map",
    "probe_suggestions",
    "invalidation_notes",
    "compression_summary",
    "next_experiment_labels",
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
    blob = " \n".join(_iter_text_values(value)).lower()
    return any(marker in blob for marker in _FORBIDDEN_TEXT_MARKERS_V1)



def _base_relationship() -> dict[str, Any]:
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



def _base_safe_metadata(boundary_summary: str) -> dict[str, Any]:
    return {
        "metadata_only": True,
        "non_executing": True,
        "json_safe": True,
        "non_public": True,
        "engine_family": "raw-signal",
        "boundary_summary": boundary_summary,
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



def build_raw_signal_cartography_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    boundary = get_cognitive_research_engine_boundary_v1(ENGINE_NAME_V1)
    boundary_summary = summarize_cognitive_research_engine_boundary_v1(boundary)
    base = {
        "schema_version": SCHEMA_VERSION_V1,
        "engine_name": ENGINE_NAME_V1,
        "source_boundary_engine_name": ENGINE_NAME_V1,
        "input_category": "synthetic symbolic stream",
        "artifact_reference": "synthetic:raw-signal-cartography:artifact:001",
        "artifact_summary": "Synthetic raw-signal terrain packet with motifs, weak signals, and invalidation notes.",
        "terrain_primitives": ["glyphs", "symbols", "fragments", "gaps", "clusters", "edges"],
        "motif_candidates": ["repeat clusters", "boundary tension"],
        "weak_signal_labels": ["weak motif", "uncertain drift"],
        "stable_region_labels": ["stable zone"],
        "unstable_region_labels": ["unstable zone"],
        "noise_region_labels": ["noise cluster"],
        "boundary_region_labels": ["transition band"],
        "candidate_grammar_labels": ["segment", "cluster", "contrast", "probe"],
        "operator_transformation_labels": ["compress", "expand", "trace", "label"],
        "uncertainty_map": {"terrain": "unknown", "confidence": "bounded", "residual": "tracked"},
        "probe_suggestions": ["compare local motif density", "perturb one axis and re-map"],
        "invalidation_notes": ["flattening rejected", "failed labels preserved"],
        "compression_summary": "Preserve texture, uncertainty, and invalidation history while keeping the packet bounded.",
        "next_experiment_labels": ["probe boundary shift", "test motif persistence"],
        "relationship_to_cognitive_research_run": _base_relationship(),
        "safe_metadata": _base_safe_metadata(boundary_summary),
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
    if not isinstance(data.get("relationship_to_cognitive_research_run"), Mapping):
        data["relationship_to_cognitive_research_run"] = _base_relationship()
    else:
        relationship = _base_relationship()
        relationship.update(dict(data["relationship_to_cognitive_research_run"]))
        data["relationship_to_cognitive_research_run"] = relationship
    if not isinstance(data.get("safe_metadata"), Mapping):
        data["safe_metadata"] = _base_safe_metadata(boundary_summary)
    else:
        safe_metadata = _base_safe_metadata(boundary_summary)
        safe_metadata.update(dict(data["safe_metadata"]))
        data["safe_metadata"] = safe_metadata
    denied = build_default_cognitive_research_denied_authority_v1()
    if isinstance(data.get("denied_authority"), Mapping):
        denied.update({str(k): bool(v) for k, v in dict(data["denied_authority"]).items() if k in denied})
    data["denied_authority"] = denied
    data.setdefault("public_claim_status", "blocked_internal_only")
    return data



def validate_raw_signal_cartography_packet_v1(packet: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(packet, Mapping):
        return {"valid": False, "violation_count": 1, "violations": ["packet must be a mapping"]}

    packet_dict = dict(packet)
    registry = build_cognitive_research_engine_boundary_registry_v1()
    boundary = registry.get(ENGINE_NAME_V1)
    if boundary is None:
        violations.append("boundary registry missing RAW_SIGNAL_CARTOGRAPHER")
        boundary_valid = False
    else:
        boundary_result = validate_cognitive_research_engine_boundary_v1(boundary)
        boundary_valid = bool(boundary_result.get("valid"))
        if not boundary_valid:
            violations.append("source boundary metadata invalid")

    if packet_dict.get("engine_name") != ENGINE_NAME_V1:
        violations.append("engine_name must be RAW_SIGNAL_CARTOGRAPHER")
    if packet_dict.get("source_boundary_engine_name") != ENGINE_NAME_V1:
        violations.append("source_boundary_engine_name must be RAW_SIGNAL_CARTOGRAPHER")

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
        "compression_summary",
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

    compression_summary = _compact_text(packet_dict.get("compression_summary"))
    if len(compression_summary) > 700:
        violations.append("compression_summary must remain bounded")

    for field in ("terrain_primitives", "motif_candidates", "weak_signal_labels", "stable_region_labels", "unstable_region_labels", "noise_region_labels", "boundary_region_labels", "candidate_grammar_labels", "operator_transformation_labels", "probe_suggestions", "invalidation_notes", "next_experiment_labels"):
        value = packet_dict.get(field)
        if not isinstance(value, (list, tuple)) or not _coerce_sequence(value):
            violations.append(f"{field} must be non-empty")

    uncertainty_map = packet_dict.get("uncertainty_map")
    if not isinstance(uncertainty_map, Mapping):
        violations.append("uncertainty_map must be a mapping")

    relationship = packet_dict.get("relationship_to_cognitive_research_run")
    if not isinstance(relationship, Mapping):
        violations.append("relationship_to_cognitive_research_run must be a mapping")
    else:
        for field in _REQUIRED_RELATIONSHIP_FIELDS_V1:
            if field not in relationship:
                violations.append(f"relationship_to_cognitive_research_run missing field: {field}")
        if relationship.get("envelope_only") is not True:
            violations.append("CognitiveResearchRunV1 must remain envelope only")
        if relationship.get("not_engine_kernel") is not True:
            violations.append("CognitiveResearchRunV1 must not be engine kernel")
        if relationship.get("not_runtime_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have runtime authority")
        if relationship.get("not_tool_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have tool authority")
        if relationship.get("not_provider_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have provider authority")
        if relationship.get("not_search_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have search authority")
        if relationship.get("not_proof_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have proof authority")
        if relationship.get("not_public_claim_authority") is not True:
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

    flattened_summary = f"{packet_dict.get('artifact_summary', '')} {packet_dict.get('compression_summary', '')}".lower()
    if any(marker in flattened_summary for marker in ("generic summary", "generic assistant", "generic evaluator", "generic summarizer", "proof solver", "math tutor", "programming assistant")):
        violations.append("packet flattens into a generic summary")

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
        "summary": summarize_raw_signal_cartography_packet_v1(packet_dict),
    }



def summarize_raw_signal_cartography_packet_v1(packet: Any) -> str:
    if not isinstance(packet, Mapping):
        return "invalid raw signal cartography packet"
    engine_name = _compact_text(packet.get("engine_name"), default=ENGINE_NAME_V1)
    ref = _compact_text(packet.get("artifact_reference"), default="ref:unknown")
    input_category = _compact_text(packet.get("input_category"), default="unknown")
    terrain_count = len(_coerce_sequence(packet.get("terrain_primitives")))
    motif_count = len(_coerce_sequence(packet.get("motif_candidates")))
    probe_count = len(_coerce_sequence(packet.get("probe_suggestions")))
    next_count = len(_coerce_sequence(packet.get("next_experiment_labels")))
    public_status = _compact_text(packet.get("public_claim_status"), default="blocked_internal_only")
    summary = (
        f"{engine_name} packet | input={input_category} | ref={ref} | terrain={terrain_count} | motifs={motif_count} | probes={probe_count} | next={next_count} | public={public_status}"
    )
    if isinstance(packet.get("safe_metadata"), Mapping):
        boundary_summary = _compact_text(packet["safe_metadata"].get("boundary_summary"), default="")
        if boundary_summary:
            summary += f" | boundary={boundary_summary}"
    return summary[:900]



def to_raw_signal_cartography_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def build_initial_raw_signal_cartography_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    specs = [
        {
            "input_category": "synthetic symbolic stream",
            "artifact_reference": "synthetic:raw-signal-cartography:artifact:terrain-001",
            "artifact_summary": "Synthetic terrain fragment with repeated clusters and a narrow uncertainty band.",
            "terrain_primitives": ["glyphs", "fragments", "clusters", "edges"],
            "motif_candidates": ["repeated cluster"],
            "uncertainty_map": {"terrain": "unknown", "band": "narrow"},
        },
        {
            "input_category": "synthetic signal log reference",
            "artifact_reference": "synthetic:raw-signal-cartography:artifact:terrain-002",
            "artifact_summary": "Synthetic log excerpt with a weak recurring edge and preserved invalidation notes.",
            "terrain_primitives": ["bursts", "gaps", "edges", "drift"],
            "motif_candidates": ["weak recurring edge"],
            "uncertainty_map": {"terrain": "unknown", "residual": "tracked"},
        },
        {
            "input_category": "synthetic generated artifact summary",
            "artifact_reference": "synthetic:raw-signal-cartography:artifact:terrain-003",
            "artifact_summary": "Synthetic summary preserving strange texture, unstable transitions, and probe suggestions.",
            "terrain_primitives": ["symbols", "interruptions", "clusters", "resonance"],
            "motif_candidates": ["unstable transition"],
            "uncertainty_map": {"terrain": "unknown", "stability": "mixed"},
        },
    ]
    for index, spec in enumerate(specs, start=1):
        packet = build_raw_signal_cartography_packet_v1(spec)
        packet["example_id"] = _payload_marker("raw_signal_cartography_example", {"index": index, "artifact_reference": packet["artifact_reference"]})
        packet["example_label"] = f"raw_signal_cartography_example_{index}"
        examples.append(packet)
    return examples
