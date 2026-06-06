"""Metadata-only helpers for SIGNAL_VS_NOISE_ENGINE v1.

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

SCHEMA_VERSION_V1 = "signal_vs_noise_v1"
ENGINE_NAME_V1 = "SIGNAL_VS_NOISE_ENGINE"
UPSTREAM_RAW_SIGNAL_ENGINE_NAME_V1 = "RAW_SIGNAL_CARTOGRAPHER"
UPSTREAM_INTERPRETIVE_ENGINE_NAME_V1 = "UNINTELLIGIBLE_OUTPUT_ANALYZER"
HELPER_TYPE_V1 = "weslr_signal_vs_noise_engine_helpers_v1"

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
    "generic cleanup",
    "cleanup assistant",
    "noise deletion",
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

_FORBIDDEN_FLATTENING_MARKERS_V1 = (
    "binary only",
    "binary-only",
    "generic cleanup",
    "cleanup assistant",
    "cleanup",
    "noise deletion",
    "simple yes/no",
    "normalizer",
    "generic summary",
    "generic assistant",
)

_REQUIRED_PACKET_FIELDS_V1 = (
    "schema_version",
    "engine_name",
    "source_boundary_engine_name",
    "input_category",
    "artifact_reference",
    "artifact_summary",
    "signal_noise_classification_map",
    "weak_signal_candidates",
    "pseudo_randomness_labels",
    "emerging_grammar_labels",
    "stable_signal_labels",
    "unstable_signal_labels",
    "artifact_effect_labels",
    "undecidable_region_labels",
    "confidence_uncertainty_map",
    "invalidation_notes",
    "next_probe_labels",
    "relationship_to_raw_signal_cartographer",
    "relationship_to_unintelligible_output_analyzer",
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
        "role": "classification_pressure_after_raw_signal",
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
        "role": "classification_pressure_after_interpretation_preservation",
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



def _base_safe_metadata(boundary_summary: str, raw_signal_summary: str, interpretive_summary: str) -> dict[str, Any]:
    return {
        "metadata_only": True,
        "non_executing": True,
        "json_safe": True,
        "non_public": True,
        "engine_family": "raw-signal",
        "boundary_summary": boundary_summary,
        "upstream_raw_signal_summary": raw_signal_summary,
        "upstream_interpretive_summary": interpretive_summary,
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



def build_signal_vs_noise_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    boundary = get_cognitive_research_engine_boundary_v1(ENGINE_NAME_V1)
    boundary_summary = summarize_cognitive_research_engine_boundary_v1(boundary)
    raw_signal_boundary = get_cognitive_research_engine_boundary_v1(UPSTREAM_RAW_SIGNAL_ENGINE_NAME_V1)
    raw_signal_summary = summarize_cognitive_research_engine_boundary_v1(raw_signal_boundary)
    interpretive_boundary = get_cognitive_research_engine_boundary_v1(UPSTREAM_INTERPRETIVE_ENGINE_NAME_V1)
    interpretive_summary = summarize_cognitive_research_engine_boundary_v1(interpretive_boundary)
    base = {
        "schema_version": SCHEMA_VERSION_V1,
        "engine_name": ENGINE_NAME_V1,
        "source_boundary_engine_name": ENGINE_NAME_V1,
        "input_category": "synthetic symbolic stream",
        "artifact_reference": "synthetic:signal-vs-noise:artifact:001",
        "artifact_summary": "Synthetic signal-vs-noise packet preserving weak structure, artifact effects, and undecidable regions.",
        "signal_noise_classification_map": {
            "signal_candidates": ["candidate signal region"],
            "noise_candidates": ["candidate noise region"],
            "weak_signal_candidates": ["weak signal candidate"],
            "pseudo_randomness_labels": ["pseudo-randomness hint"],
            "artifact_effect_labels": ["artifact-effect candidate"],
            "undecidable_region_labels": ["undecidable band"],
        },
        "weak_signal_candidates": ["weak motif survives perturbation"],
        "pseudo_randomness_labels": ["pseudo-random cluster"],
        "emerging_grammar_labels": ["candidate grammar seed"],
        "stable_signal_labels": ["stable local signal"],
        "unstable_signal_labels": ["unstable local signal"],
        "artifact_effect_labels": ["artifact-effect signature"],
        "undecidable_region_labels": ["undecidable boundary band"],
        "confidence_uncertainty_map": {"signal": "bounded", "noise": "bounded", "artifact": "tracked", "undecidable": "tracked"},
        "invalidation_notes": ["binary-only flattening rejected"],
        "next_probe_labels": ["perturb candidate region", "compare persistence under one-axis shift"],
        "relationship_to_raw_signal_cartographer": _base_relationship_to_raw_signal(),
        "relationship_to_unintelligible_output_analyzer": _base_relationship_to_unintelligible_output(),
        "relationship_to_cognitive_research_run": _base_relationship_to_run(),
        "safe_metadata": _base_safe_metadata(boundary_summary, raw_signal_summary, interpretive_summary),
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
    if not isinstance(data.get("signal_noise_classification_map"), Mapping):
        data["signal_noise_classification_map"] = copy.deepcopy(base["signal_noise_classification_map"])
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
    if not isinstance(data.get("relationship_to_cognitive_research_run"), Mapping):
        data["relationship_to_cognitive_research_run"] = _base_relationship_to_run()
    else:
        rel = _base_relationship_to_run()
        rel.update(dict(data["relationship_to_cognitive_research_run"]))
        data["relationship_to_cognitive_research_run"] = rel
    if not isinstance(data.get("safe_metadata"), Mapping):
        data["safe_metadata"] = _base_safe_metadata(boundary_summary, raw_signal_summary, interpretive_summary)
    else:
        safe_metadata = _base_safe_metadata(boundary_summary, raw_signal_summary, interpretive_summary)
        safe_metadata.update(dict(data["safe_metadata"]))
        data["safe_metadata"] = safe_metadata
    denied = build_default_cognitive_research_denied_authority_v1()
    if isinstance(data.get("denied_authority"), Mapping):
        denied.update({str(k): bool(v) for k, v in dict(data["denied_authority"]).items() if k in denied})
    data["denied_authority"] = denied
    data.setdefault("public_claim_status", "blocked_internal_only")
    return data



def validate_signal_vs_noise_packet_v1(packet: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(packet, Mapping):
        return {"valid": False, "violation_count": 1, "violations": ["packet must be a mapping"]}

    packet_dict = dict(packet)
    registry = build_cognitive_research_engine_boundary_registry_v1()
    boundary = registry.get(ENGINE_NAME_V1)
    if boundary is None:
        violations.append("boundary registry missing SIGNAL_VS_NOISE_ENGINE")
        boundary_valid = False
    else:
        boundary_result = validate_cognitive_research_engine_boundary_v1(boundary)
        boundary_valid = bool(boundary_result.get("valid"))
        if not boundary_valid:
            violations.append("source boundary metadata invalid")

    if packet_dict.get("engine_name") != ENGINE_NAME_V1:
        violations.append("engine_name must be SIGNAL_VS_NOISE_ENGINE")
    if packet_dict.get("source_boundary_engine_name") != ENGINE_NAME_V1:
        violations.append("source_boundary_engine_name must be SIGNAL_VS_NOISE_ENGINE")

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
        "weak_signal_candidates",
        "pseudo_randomness_labels",
        "emerging_grammar_labels",
        "stable_signal_labels",
        "unstable_signal_labels",
        "artifact_effect_labels",
        "undecidable_region_labels",
        "invalidation_notes",
        "next_probe_labels",
    ):
        value = packet_dict.get(field)
        if not isinstance(value, (list, tuple)) or not _coerce_sequence(value):
            violations.append(f"{field} must be non-empty")

    classification_map = packet_dict.get("signal_noise_classification_map")
    if not isinstance(classification_map, Mapping):
        violations.append("signal_noise_classification_map must be a mapping")
    else:
        for key in (
            "signal_candidates",
            "noise_candidates",
            "weak_signal_candidates",
            "pseudo_randomness_labels",
            "artifact_effect_labels",
            "undecidable_region_labels",
        ):
            value = classification_map.get(key)
            if not isinstance(value, (list, tuple)) or not _coerce_sequence(value):
                violations.append(f"signal_noise_classification_map missing {key}")

    relationship = packet_dict.get("relationship_to_raw_signal_cartographer")
    if not isinstance(relationship, Mapping):
        violations.append("relationship_to_raw_signal_cartographer must be a mapping")
    else:
        for field in _REQUIRED_RAW_SIGNAL_RELATIONSHIP_FIELDS_V1:
            if field not in relationship:
                violations.append(f"relationship_to_raw_signal_cartographer missing field: {field}")
        if relationship.get("upstream_engine_name") != UPSTREAM_RAW_SIGNAL_ENGINE_NAME_V1:
            violations.append("relationship_to_raw_signal_cartographer upstream engine mismatch")
        if relationship.get("preserves_unknown_tokens") is not True:
            violations.append("relationship_to_raw_signal_cartographer must preserve unknown tokens")
        if relationship.get("preserves_competing_layers") is not True:
            violations.append("relationship_to_raw_signal_cartographer must preserve competing layers")
        if relationship.get("not_final_meaning_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not claim final meaning authority")
        if relationship.get("not_runtime_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not have runtime authority")
        if relationship.get("not_tool_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not have tool authority")
        if relationship.get("not_provider_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not have provider authority")
        if relationship.get("not_search_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not have search authority")
        if relationship.get("not_proof_authority") is not True:
            violations.append("relationship_to_raw_signal_cartographer must not have proof authority")
        if relationship.get("not_public_claim_authority") is not True:
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
        "signal_noise_classification_map": packet_dict.get("signal_noise_classification_map"),
        "weak_signal_candidates": packet_dict.get("weak_signal_candidates"),
        "pseudo_randomness_labels": packet_dict.get("pseudo_randomness_labels"),
        "artifact_effect_labels": packet_dict.get("artifact_effect_labels"),
        "undecidable_region_labels": packet_dict.get("undecidable_region_labels"),
    }), sort_keys=True, ensure_ascii=True).lower()
    if any(marker in flattening_blob for marker in _FORBIDDEN_FLATTENING_MARKERS_V1):
        violations.append("packet flattens signal/noise classification too early")

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
        "summary": summarize_signal_vs_noise_packet_v1(packet_dict),
    }



def summarize_signal_vs_noise_packet_v1(packet: Any) -> str:
    if not isinstance(packet, Mapping):
        return "invalid signal vs noise packet"
    engine_name = _compact_text(packet.get("engine_name"), default=ENGINE_NAME_V1)
    ref = _compact_text(packet.get("artifact_reference"), default="ref:unknown")
    input_category = _compact_text(packet.get("input_category"), default="unknown")
    weak = len(_coerce_sequence(packet.get("weak_signal_candidates")))
    pseudo = len(_coerce_sequence(packet.get("pseudo_randomness_labels")))
    emerge = len(_coerce_sequence(packet.get("emerging_grammar_labels")))
    stable = len(_coerce_sequence(packet.get("stable_signal_labels")))
    unstable = len(_coerce_sequence(packet.get("unstable_signal_labels")))
    artifact = len(_coerce_sequence(packet.get("artifact_effect_labels")))
    undecidable = len(_coerce_sequence(packet.get("undecidable_region_labels")))
    public_status = _compact_text(packet.get("public_claim_status"), default="blocked_internal_only")
    summary = (
        f"{engine_name} packet | input={input_category} | ref={ref} | weak={weak} | pseudo={pseudo} | emerging={emerge} | stable={stable} | unstable={unstable} | artifact={artifact} | undecidable={undecidable} | public={public_status}"
    )
    if isinstance(packet.get("safe_metadata"), Mapping):
        boundary_summary = _compact_text(packet["safe_metadata"].get("boundary_summary"), default="")
        if boundary_summary:
            summary += f" | boundary={boundary_summary}"
    return summary[:900]



def to_signal_vs_noise_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def build_initial_signal_vs_noise_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    specs = [
        {
            "artifact_reference": "synthetic:signal-vs-noise:artifact:layer-001",
            "artifact_summary": "Synthetic stream with weak motifs, pseudo-randomness hints, and undecidable bands.",
            "weak_signal_candidates": ["weak motif survives perturbation", "cluster persistence hint"],
            "pseudo_randomness_labels": ["pseudo-random cluster", "noise-like but structured"],
            "emerging_grammar_labels": ["candidate grammar seed"],
            "stable_signal_labels": ["stable local signal"],
            "unstable_signal_labels": ["unstable local signal"],
            "artifact_effect_labels": ["artifact-effect signature"],
            "undecidable_region_labels": ["undecidable boundary band"],
        },
        {
            "artifact_reference": "synthetic:signal-vs-noise:artifact:layer-002",
            "artifact_summary": "Synthetic classification map preserving noise, artifact-effect, and weak-signal candidates.",
            "weak_signal_candidates": ["repeating but weak motif"],
            "pseudo_randomness_labels": ["random-looking local texture"],
            "emerging_grammar_labels": ["grammar seed under pressure", "local rule hint"],
            "stable_signal_labels": ["stable cluster"],
            "unstable_signal_labels": ["unstable cluster"],
            "artifact_effect_labels": ["measurement artifact signature"],
            "undecidable_region_labels": ["still undecidable"],
        },
        {
            "artifact_reference": "synthetic:signal-vs-noise:artifact:layer-003",
            "artifact_summary": "Synthetic undecidable region packet with bounded confidence and invalidation notes.",
            "weak_signal_candidates": ["borderline weak structure"],
            "pseudo_randomness_labels": ["pseudo-random drift"],
            "emerging_grammar_labels": ["emergent grammar pressure"],
            "stable_signal_labels": ["stable island"],
            "unstable_signal_labels": ["unstable island"],
            "artifact_effect_labels": ["artifact effect edge"],
            "undecidable_region_labels": ["undecidable edge zone"],
        },
    ]
    for index, spec in enumerate(specs, start=1):
        packet = build_signal_vs_noise_packet_v1(spec)
        packet["example_id"] = _payload_marker("signal_vs_noise_example", {"index": index, "artifact_reference": packet["artifact_reference"]})
        packet["example_label"] = f"signal_vs_noise_example_{index}"
        examples.append(packet)
    return examples
