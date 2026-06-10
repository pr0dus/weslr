"""Metadata-only Raw Signal Cartographer V1 helpers.

The engine maps structure in strange, noisy, symbolic, or partially structured
artifacts before judging them. It stays metadata-only, JSON-safe, and fail-closed.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any, Mapping

from weslr.cognitive_research_protocol import (
    ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1,
    ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1,
    ALLOWED_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1,
    ALLOWED_COGNITIVE_RESEARCH_PRESSURE_TYPES_V1,
    ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1,
    ALLOWED_COGNITIVE_RESEARCH_PUBLIC_GAP_CARD_STATUSES_V1,
    ALLOWED_COGNITIVE_RESEARCH_RESEARCH_MODES_V1,
    build_cognitive_research_run_v1,
    build_default_cognitive_research_denied_authority_v1,
    classify_cognitive_research_engine_family_v1,
    summarize_cognitive_research_run_v1,
    to_cognitive_research_json_safe_v1,
    validate_cognitive_research_run_v1,
)

HELPER_TYPE_V1 = "weslr_raw_signal_cartographer_v1"
SCHEMA_VERSION_V1 = "raw_signal_cartography_v1"
ENGINE_NAME_V1 = "raw_signal_cartographer"
ENGINE_FAMILY_V1 = "raw_signal_analysis"
GENERATOR_LOOP_V1 = "RecursiveDiscoveryLoopV1"
DIALECTIC_GENERATOR_LOOP_V1 = "DialecticGeneratorLoopV1"

_ALLOWED_ENGINE_NAMES_V1 = (ENGINE_NAME_V1,)
_ALLOWED_ENGINE_FAMILIES_V1 = (ENGINE_FAMILY_V1,)
_ALLOWED_RESEARCH_MODES_V1 = ("internal_exploration", "synthetic_test")
_ALLOWED_PUBLIC_CLAIM_STATUSES_V1 = ("internal_candidate_only", "public_export_blocked")
_ALLOWED_PUBLIC_GAP_CARD_STATUSES_V1 = ("public_export_blocked",)
_ALLOWED_LLM_HELPER_ROLES_V1 = ("candidate_generator_only", "probe_suggestion_helper_only", "translation_helper_only")
_ALLOWED_SOURCE_ORIGINS_V1 = ("metadata_only", "artifact_summary_only", "artifact_ref_only")
_ALLOWED_STABILITY_VALUES_V1 = ("stable", "unstable", "mixed", "transitional")
_ALLOWED_REGION_KIND_VALUES_V1 = ("stable", "unstable", "mixed", "unknown")
_ALLOWED_PRESSURE_TYPES_V1 = tuple(ALLOWED_COGNITIVE_RESEARCH_PRESSURE_TYPES_V1)

_FORBIDDEN_RAW_KEYS_V1 = {
    "raw_artifact",
    "artifact_content",
    "full_artifact",
    "full_artifact_text",
    "inline_artifact",
    "input_artifact_inline",
    "raw_payload",
    "raw_content",
    "private_text",
    "hidden_prompt",
    "system_prompt",
    "prompt",
    "prompt_text",
    "secret",
    "token",
    "model_output",
    "provider_output",
    "search_output",
    "execution_command",
    "command",
    "script",
}

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw private text",
    "raw private data",
    "hidden prompt",
    "system prompt",
    "private mechanism",
    "breakthrough",
    "proof",
    "certified",
    "certification",
    "official",
    "public ready",
    "public-ready",
    "solved",
    "final answer",
    "llm authority",
    "runtime authority",
    "provider authority",
    "tool authority",
    "persistence",
    ".weslr",
    "network",
    "rss",
    "github",
    "lab notebook",
    "live ingest",
    "live ingestion",
    "execute this code",
    "run this code",
    "step-by-step",
    "subprocess",
    "os.system",
)

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[^\w\s]", re.UNICODE)


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if text else default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return _compact_text(str(value), default=default)


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    if overrides:
        data.update(overrides)
    return data


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(list(value), key=_compact_text)
    if isinstance(value, Mapping):
        return list(value.values())
    return [value]


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda item: str(item)):
            key_text = str(key)
            if key_text.lower() in _FORBIDDEN_RAW_KEYS_V1:
                continue
            out[key_text] = _json_safe(value[key])
        return out
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_compact_text)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _compact_text(value)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalize_engine_name(value: Any) -> str:
    return _compact_text(value).lower()


def _tokenize(text: Any) -> list[str]:
    return [token for token in _TOKEN_RE.findall(_compact_text(text)) if token]


def _segment_text(text: Any) -> list[str]:
    raw = _compact_text(text)
    if not raw:
        return ["metadata-only artifact summary"]
    chunks = [chunk.strip() for chunk in re.split(r"(?:\r?\n+|[|;]+|(?<=[.!?])\s+)", raw) if chunk.strip()]
    if len(chunks) >= 2:
        return chunks[:8]
    tokens = _tokenize(raw)
    if len(tokens) <= 8:
        return [raw]
    step = max(4, min(12, max(1, len(tokens) // 4)))
    return [" ".join(tokens[index : index + step]) for index in range(0, len(tokens), step)][:8]


def _symbol_ratio(text: str) -> float:
    if not text:
        return 0.0
    symbols = sum(1 for char in text if not char.isalnum() and not char.isspace())
    return symbols / max(len(text), 1)


def _make_segment_candidate(index: int, segment: str, tokens: list[str]) -> dict[str, Any]:
    lower = segment.lower()
    ratio = _symbol_ratio(segment)
    token_count = len(tokens)
    stability = "stable"
    if ratio > 0.35 or token_count <= 2:
        stability = "unstable"
    elif ratio > 0.18:
        stability = "transitional"
    region_kind = "stable" if stability == "stable" else ("unstable" if stability == "unstable" else "mixed")
    repeated_tokens = [token for token, count in Counter(tok.lower() for tok in tokens).items() if count > 1 and len(token) > 1]
    return {
        "segment_id": f"segment-{index + 1}",
        "segment_summary": segment[:220],
        "segment_kind": region_kind,
        "stability": stability,
        "token_count": token_count,
        "symbol_ratio": round(ratio, 3),
        "repeated_tokens": repeated_tokens[:5],
        "marker_density": round(sum(1 for marker in ("::", "->", "||", "//", "==", "??") if marker in lower) / 6.0, 3),
        "notes": "metadata-only segment candidate",
    }


def _build_segmentation(packet: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    summary = _compact_text(packet.get("input_summary"))
    segments = _segment_text(summary)
    segment_candidates: list[dict[str, Any]] = []
    stable_regions: list[dict[str, Any]] = []
    unstable_regions: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        tokens = _tokenize(segment)
        candidate = _make_segment_candidate(index, segment, tokens)
        segment_candidates.append(candidate)
        if candidate["stability"] == "stable":
            stable_regions.append(
                {
                    "region_id": candidate["segment_id"],
                    "region_summary": candidate["segment_summary"],
                    "evidence": candidate["repeated_tokens"][:3] or ["low-noise structure"],
                    "confidence": 72.0,
                }
            )
        elif candidate["stability"] == "unstable":
            unstable_regions.append(
                {
                    "region_id": candidate["segment_id"],
                    "region_summary": candidate["segment_summary"],
                    "evidence": ["high symbol density", "short or fragmented segment"],
                    "confidence": 78.0,
                }
            )
    segmentation_summary = {
        "segmentation_id": f"segment-{_stable_digest({'ref': packet.get('input_artifact_ref', ''), 'summary': summary})[:12]}",
        "strategy": "summary-preserving region segmentation",
        "segment_count": len(segment_candidates),
        "stable_region_count": len(stable_regions),
        "unstable_region_count": len(unstable_regions),
        "retained_markers": ["repetition", "delimiter", "symbol_density", "token_cluster"],
        "notes": "metadata-only segmentation; raw artifact content is not stored",
    }
    return segmentation_summary, segment_candidates, stable_regions, unstable_regions


def _detect_recurring_tokens_and_symbols(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tokens = [token.lower() for token in _tokenize(text) if token]
    token_counts = Counter(token for token in tokens if len(token) > 1)
    recurring_symbol_counts = Counter(char for char in text if not char.isalnum() and not char.isspace())
    recurring_symbol_candidates: list[dict[str, Any]] = []
    for symbol, count in sorted(recurring_symbol_counts.items(), key=lambda item: (-item[1], item[0])):
        if count < 2:
            continue
        recurring_symbol_candidates.append(
            {
                "symbol": symbol,
                "count": count,
                "role": "delimiter" if symbol in {":", ";", "|", "-", "/", "_", "="} else "marker",
                "context": "symbol recurrence candidate",
            }
        )
    motif_clusters: list[dict[str, Any]] = []
    for token, count in sorted(token_counts.items(), key=lambda item: (-item[1], item[0]))[:8]:
        if count < 2:
            continue
        motif_clusters.append(
            {
                "cluster_id": f"motif-{_stable_digest({'token': token, 'count': count})[:10]}",
                "motif": token,
                "recurrence": count,
                "evidence": [f"token:{token}"] * min(count, 3),
                "confidence": min(95.0, 50.0 + count * 10.0),
            }
        )
    if not motif_clusters and recurring_symbol_candidates:
        motif_clusters.append(
            {
                "cluster_id": f"motif-{_stable_digest({'symbols': recurring_symbol_candidates[:3]})[:10]}",
                "motif": "symbol_recurrence",
                "recurrence": sum(item["count"] for item in recurring_symbol_candidates[:3]),
                "evidence": [item["symbol"] for item in recurring_symbol_candidates[:3]],
                "confidence": 58.0,
            }
        )
    return motif_clusters, recurring_symbol_candidates


def _detect_operator_like_transformations(text: str, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lower = text.lower()
    candidate_ops: list[tuple[str, str]] = [
        ("segment", "split structured regions before judging them"),
        ("cluster", "cluster recurring motifs"),
        ("compress", "compress repeated forms without losing markers"),
        ("map", "map structure to candidate regions"),
        ("normalize", "normalize while preserving strange output"),
        ("probe", "generate tests that can falsify the current map"),
        ("translate", "translate symbol patterns into candidate grammar"),
        ("fold", "fold repeated structures into reusable operators"),
    ]
    operations: list[dict[str, Any]] = []
    for operator, rationale in candidate_ops:
        if operator in lower or any(operator in segment["segment_summary"].lower() for segment in segments):
            operations.append(
                {
                    "operator": operator,
                    "transformation": rationale,
                    "evidence": [operator],
                    "confidence": 65.0 if operator in lower else 52.0,
                }
            )
    if not operations:
        operations.append(
            {
                "operator": "segment",
                "transformation": "segment the artifact into candidate regions first",
                "evidence": ["default cartography operator"],
                "confidence": 50.0,
            }
        )
    return operations[:8]


def _detect_symmetry_and_asymmetry(segments: list[dict[str, Any]], text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    symmetry_candidates: list[dict[str, Any]] = []
    asymmetry_candidates: list[dict[str, Any]] = []
    if len(segments) >= 2:
        first = segments[0]["segment_summary"]
        last = segments[-1]["segment_summary"]
        if _tokenize(first) and _tokenize(last) and _tokenize(first)[0].lower() == _tokenize(last)[0].lower():
            symmetry_candidates.append(
                {
                    "candidate_id": f"sym-{_stable_digest({'first': first, 'last': last})[:10]}",
                    "pattern": "boundary token repetition",
                    "marker": _tokenize(first)[0],
                    "rationale": "first and last segments share a token boundary",
                    "confidence": 61.0,
                }
            )
    repeated_delimiters = [marker for marker in ("::", "->", "||", "//", "==") if marker in text]
    if repeated_delimiters:
        symmetry_candidates.append(
            {
                "candidate_id": f"sym-{_stable_digest({'delimiters': repeated_delimiters, 'text': text[:120]})[:10]}",
                "pattern": "delimiter recurrence",
                "marker": repeated_delimiters[0],
                "rationale": "repeated symbolic delimiters suggest a structured transform loop",
                "confidence": 66.0,
            }
        )
    for index, segment in enumerate(segments):
        ratio = _symbol_ratio(segment["segment_summary"])
        if ratio > 0.25 or any(char.isupper() for char in segment["segment_summary"] if char.isalpha()):
            asymmetry_candidates.append(
                {
                    "candidate_id": f"asym-{index + 1}",
                    "pattern": "symbolic asymmetry",
                    "marker": "high symbol or case variance",
                    "rationale": "the region resists smooth normalization",
                    "confidence": 60.0,
                }
            )
    if not asymmetry_candidates:
        asymmetry_candidates.append(
            {
                "candidate_id": f"asym-{_stable_digest({'text': text[:120]})[:10]}",
                "pattern": "unknown boundary asymmetry",
                "marker": "unmapped region",
                "rationale": "summary-only evidence leaves uneven structure unexplained",
                "confidence": 47.0,
            }
        )
    return symmetry_candidates[:6], asymmetry_candidates[:6]


def _build_candidate_grammar(motif_clusters: list[dict[str, Any]], recurring_symbol_candidates: list[dict[str, Any]], segments: list[dict[str, Any]]) -> dict[str, Any]:
    terminals = sorted({item["motif"] for item in motif_clusters if item.get("motif") and item["motif"] != "symbol_recurrence"} | {item["symbol"] for item in recurring_symbol_candidates[:8] if item.get("symbol")})
    if not terminals:
        terminals = ["segment", "motif", "probe"]
    nonterminals = ["RUN", "REGION", "MOTIF", "PROBE", "UNCERTAIN_REGION"]
    rules = [
        {"lhs": "RUN", "rhs": ["REGION", "MOTIF", "PROBE"]},
        {"lhs": "REGION", "rhs": ["stable_region", "unstable_region", "unknown_region"]},
        {"lhs": "MOTIF", "rhs": terminals[:3]},
        {"lhs": "PROBE", "rhs": ["falsify", "re-segment", "compress"]},
    ]
    if len(segments) > 1:
        rules.append({"lhs": "RUN", "rhs": ["REGION", "REGION", "REGION"]})
    return {
        "grammar_id": f"grammar-{_stable_digest({'terminals': terminals, 'segments': len(segments)})[:12]}",
        "terminals": terminals,
        "nonterminals": nonterminals,
        "rules": rules,
        "notes": "candidate grammar only; not a correctness claim",
    }


def _build_compression_summary(packet: Mapping[str, Any], segments: list[dict[str, Any]], motif_clusters: list[dict[str, Any]], recurring_symbol_candidates: list[dict[str, Any]], unmapped_regions: list[dict[str, Any]]) -> dict[str, Any]:
    retained = ["segment boundaries", "motif clusters", "operator candidates", "unmapped regions"]
    compressed_lesson = (
        "Preserve strange structure first; compress only after the segment map and probe plan are visible."
    )
    return {
        "compression_id": f"compress-{_stable_digest({'ref': packet.get('input_artifact_ref', ''), 'segments': segments[:3]})[:12]}",
        "method": "structure-preserving cartographic compression",
        "retained_structure": retained,
        "removed_structure": ["raw artifact content", "duplicate delimiter runs", "redundant summaries"],
        "motif_count": len(motif_clusters),
        "symbol_count": len(recurring_symbol_candidates),
        "unmapped_region_count": len(unmapped_regions),
        "compressed_lesson": compressed_lesson,
    }


def _build_unmapped_regions(segments: list[dict[str, Any]], source_origin: str) -> list[dict[str, Any]]:
    unmapped: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        if segment["stability"] != "stable" or segment["symbol_ratio"] > 0.25:
            unmapped.append(
                {
                    "region_id": segment["segment_id"],
                    "reason": "insufficient structure confidence for direct mapping",
                    "next_probe": "request a bounded excerpt around this region",
                    "mapping_state": "unmapped",
                }
            )
    if not unmapped:
        unmapped.append(
            {
                "region_id": "region-unknown-1",
                "reason": "summary-only evidence leaves some structure intentionally unmapped",
                "next_probe": "compare this summary against a bounded excerpt",
                "mapping_state": "unmapped",
            }
        )
    if source_origin == "metadata_only":
        unmapped.append(
            {
                "region_id": "region-unknown-source",
                "reason": "artifact content itself is not stored",
                "next_probe": "use a safe reference plus a bounded excerpt if needed",
                "mapping_state": "unknown",
            }
        )
    return unmapped[:6]


def _build_signal_hypotheses(motif_clusters: list[dict[str, Any]], recurring_symbol_candidates: list[dict[str, Any]], segments: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    signal_hypotheses: list[dict[str, Any]] = []
    noise_hypotheses: list[dict[str, Any]] = []
    if motif_clusters:
        signal_hypotheses.append(
            {
                "hypothesis_id": f"signal-{_stable_digest({'motifs': motif_clusters[:3]})[:10]}",
                "claim": "repeated motifs indicate a recoverable structural grammar",
                "evidence": [item["motif"] for item in motif_clusters[:3]],
                "confidence": 72.0,
            }
        )
    if recurring_symbol_candidates:
        signal_hypotheses.append(
            {
                "hypothesis_id": f"signal-{_stable_digest({'symbols': recurring_symbol_candidates[:3]})[:10]}",
                "claim": "symbol recurrence marks delimiter-driven structure",
                "evidence": [item["symbol"] for item in recurring_symbol_candidates[:3]],
                "confidence": 64.0,
            }
        )
    high_noise = any(segment["symbol_ratio"] > 0.28 for segment in segments)
    if high_noise or not motif_clusters:
        noise_hypotheses.append(
            {
                "hypothesis_id": f"noise-{_stable_digest({'segments': segments[:3]})[:10]}",
                "claim": "some regions may be noise-dominant and should be probed before compression",
                "evidence": [segment["segment_id"] for segment in segments[:3]],
                "confidence": 61.0 if high_noise else 49.0,
            }
        )
    return signal_hypotheses[:6], noise_hypotheses[:6]


def _build_next_and_falsification_probes(motif_clusters: list[dict[str, Any]], unmapped_regions: list[dict[str, Any]], segments: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    next_probes: list[dict[str, Any]] = []
    falsification_probes: list[dict[str, Any]] = []
    rule_pressure_tests: list[dict[str, Any]] = []
    if motif_clusters:
        motif = motif_clusters[0]["motif"]
        next_probes.append(
            {
                "probe_id": "probe-motif-recurrence",
                "probe": f"Check whether {motif!r} repeats across neighboring regions.",
                "purpose": "confirm motif recurrence",
            }
        )
        falsification_probes.append(
            {
                "probe_id": "falsify-motif-recurrence",
                "probe": f"Swap the {motif!r} occurrences with a neutral placeholder and see if the map collapses.",
                "purpose": "falsify the motif cluster",
            }
        )
    if unmapped_regions:
        next_probes.append(
            {
                "probe_id": "probe-unmapped-region",
                "probe": "Request a bounded excerpt around the most uncertain region.",
                "purpose": "reduce mapping uncertainty",
            }
        )
        falsification_probes.append(
            {
                "probe_id": "falsify-unmapped-region",
                "probe": "Use a counterexample excerpt with the same delimiters but different internal order.",
                "purpose": "test whether the region is structural or accidental",
            }
        )
    if len(segments) > 1:
        next_probes.append(
            {
                "probe_id": "probe-cross-region-comparison",
                "probe": "Compare the first two segments for shared operators and delimiter recurrence.",
                "purpose": "check cross-region structure",
            }
        )
    rule_pressure_tests.append(
        {
            "test_id": f"pressure-{_stable_digest({'segments': len(segments), 'motifs': len(motif_clusters)})[:10]}",
            "target_rule_or_operator": "segment-preserving compression",
            "pressure_type": "counterexample",
            "mutated_input_summary": "replace a repeated delimiter with a neutral separator",
            "expected_behavior": "structure should stay recoverable",
            "observed_behavior": "pending",
            "result": "pending",
            "failure_mode": "none",
            "scope_update": "metadata_only",
        }
    )
    if any(segment["symbol_ratio"] > 0.25 for segment in segments):
        rule_pressure_tests.append(
            {
                "test_id": f"pressure-noise-{_stable_digest({'segments': segments[:2]})[:10]}",
                "target_rule_or_operator": "noise separation",
                "pressure_type": "noise_injection",
                "mutated_input_summary": "inject additional punctuation into a noisy region",
                "expected_behavior": "stable regions should remain recognizable",
                "observed_behavior": "pending",
                "result": "pending",
                "failure_mode": "none",
                "scope_update": "metadata_only",
            }
        )
    return next_probes[:6], falsification_probes[:6], rule_pressure_tests[:4]


def _build_safe_metadata() -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_executing": True,
        "no_runtime_wiring": True,
        "no_provider_calls": True,
        "no_tool_execution": True,
        "no_persistence": True,
        "no_weslr_io": True,
        "no_public_claims": True,
        "no_final_answer": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "preserve_strange_output": True,
        "cartography_only": True,
        "public_export_blocked": True,
        "perspicuity_is_not_a_gate": True,
        "generator_loop": GENERATOR_LOOP_V1,
        "dialectic_loop": DIALECTIC_GENERATOR_LOOP_V1,
    }


def _raw_artifact_is_inline(data: Mapping[str, Any]) -> bool:
    if _safe_bool(data.get("raw_artifact_included", False)):
        return True
    for key in _FORBIDDEN_RAW_KEYS_V1:
        if key in data and key not in {"prompt", "command", "script"}:
            value = data.get(key)
            if value not in (None, "", [], {}):
                return True
    return False


def build_raw_signal_cartography_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    engine_name = ENGINE_NAME_V1
    engine_family = ENGINE_FAMILY_V1
    research_mode = _compact_text(data.get("research_mode"), default="internal_exploration").lower()
    if research_mode not in _ALLOWED_RESEARCH_MODES_V1:
        research_mode = "internal_exploration"
    input_artifact_ref = _compact_text(data.get("input_artifact_ref") or data.get("safe_artifact_ref"))
    input_summary = _compact_text(data.get("input_summary") or data.get("artifact_summary") or data.get("summary"))
    source_scope = _compact_text(data.get("source_scope"), default="artifact_summary_only")
    if source_scope not in _ALLOWED_SOURCE_ORIGINS_V1:
        source_scope = "artifact_summary_only"
    public_claim_status = _compact_text(data.get("public_claim_status"), default="internal_candidate_only")
    if public_claim_status not in _ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        public_claim_status = "internal_candidate_only"
    public_gap_card_status = _compact_text(data.get("public_gap_card_status"), default="public_export_blocked")
    if public_gap_card_status not in _ALLOWED_PUBLIC_GAP_CARD_STATUSES_V1:
        public_gap_card_status = "public_export_blocked"
    llm_helper_role = _compact_text(data.get("llm_helper_role"), default="candidate_generator_only")
    if llm_helper_role not in _ALLOWED_LLM_HELPER_ROLES_V1:
        llm_helper_role = "candidate_generator_only"
    safe_metadata = data.get("safe_metadata") if isinstance(data.get("safe_metadata"), Mapping) else _build_safe_metadata()
    denied_authority_input = data.get("denied_authority") if "denied_authority" in data else build_default_cognitive_research_denied_authority_v1()
    denied_authority_missing = "denied_authority" in data and data.get("denied_authority") is None
    denied_authority_empty = isinstance(data.get("denied_authority"), Mapping) and not data.get("denied_authority")
    if not input_artifact_ref:
        input_artifact_ref = "artifact:unknown"
    if not input_summary:
        input_summary = "metadata-only raw signal cartography input"

    source_signal = data.get("source_signal")
    if not isinstance(source_signal, Mapping):
        source_signal = {
            "signal_origin": "artifact_summary_only",
            "source_ref": input_artifact_ref,
            "summary": input_summary,
            "signal_type": "raw_signal_cartography",
            "trust_level": "bounded",
            "poison_risk": "low",
            "injection_risk": "low",
            "raw_content_included": False,
            "raw_content_ref_only": True,
            "normalization_required": True,
        }
    source_signal = {
        **source_signal,
        "signal_origin": _compact_text(source_signal.get("signal_origin"), default="artifact_summary_only"),
        "source_ref": _compact_text(source_signal.get("source_ref"), default=input_artifact_ref),
        "summary": _compact_text(source_signal.get("summary"), default=input_summary),
        "signal_type": _compact_text(source_signal.get("signal_type"), default="raw_signal_cartography"),
        "trust_level": _compact_text(source_signal.get("trust_level"), default="bounded"),
        "poison_risk": _compact_text(source_signal.get("poison_risk"), default="low"),
        "injection_risk": _compact_text(source_signal.get("injection_risk"), default="low"),
        "raw_content_included": _safe_bool(source_signal.get("raw_content_included", False)),
        "raw_content_ref_only": _safe_bool(source_signal.get("raw_content_ref_only", True)),
        "normalization_required": _safe_bool(source_signal.get("normalization_required", True)),
    }

    base_packet = build_cognitive_research_run_v1(
        {
            "schema_version": SCHEMA_VERSION_V1,
            "engine_name": engine_name,
            "engine_family": engine_family,
            "research_mode": research_mode,
            "source_scope": source_scope,
            "input_artifact_ref": input_artifact_ref,
            "input_artifact_type": _compact_text(data.get("input_artifact_type"), default="artifact"),
            "input_summary": input_summary,
            "source_signal": source_signal,
            "public_claim_status": public_claim_status,
            "public_gap_card_status": public_gap_card_status,
            "llm_helper_role": llm_helper_role,
            "denied_authority": denied_authority_input,
            "safe_metadata": safe_metadata,
            "domain": "raw signal cartography",
            "domain_subtype": "symbolic structure mapping",
            "system_level": "component",
            "artifact_scale": "bounded artifact",
            "constraint_map": {
                "runtime": "denied",
                "tool": "denied",
                "provider": "denied",
                "search": "denied",
                "persistence": "denied",
                "public_claims": "blocked",
                "answer_authority": "denied",
                "artifact_storage": "summary_only",
            },
            "safety_boundary": {"mode": "metadata_only", "non_actionable": True},
            "hazard_flags": ["massive_raw_artifacts_not_stored", "public_claims_blocked"],
            "validation_route": ["metadata_only_validation", "fail_closed_safety_validation", "json_safe_copy_validation", "cartography_validation"],
            "required_expert_review": False,
            "source_requirements": {"provenance_required": True, "raw_storage_allowed": False, "side_effect_free": True},
            "experiment_type": "metadata_only",
            "simulation_before_real_world": True,
            "non_actionable_research_only": True,
            "forbidden_action_notes": ["no runtime wiring", "no provider/model calls", "no retrieval/tool execution"],
            "cross_domain_analogies": _ensure_list(data.get("cross_domain_analogies")) if data.get("cross_domain_analogies") is not None else [],
            "candidate_transfer_patterns": _ensure_list(data.get("candidate_transfer_patterns")) if data.get("candidate_transfer_patterns") is not None else [],
            "failure_mode_map": _ensure_list(data.get("failure_mode_map")) if data.get("failure_mode_map") is not None else [],
            "measurement_gap_map": _ensure_list(data.get("measurement_gap_map")) if data.get("measurement_gap_map") is not None else [],
            "operator_gap_map": _ensure_list(data.get("operator_gap_map")) if data.get("operator_gap_map") is not None else [],
            "language_gap_map": _ensure_list(data.get("language_gap_map")) if data.get("language_gap_map") is not None else [],
            "unknown_unknowns": _ensure_list(data.get("unknown_unknowns")) if data.get("unknown_unknowns") is not None else [],
            "compressed_lesson": "Preserve structure first; compress only after the region map and probes exist.",
        }
    )

    segmentation_summary, segment_candidates, stable_regions, unstable_regions = _build_segmentation(base_packet)
    motif_clusters, recurring_symbol_candidates = _detect_recurring_tokens_and_symbols(input_summary)
    operator_like_transformations = _detect_operator_like_transformations(input_summary, segment_candidates)
    symmetry_candidates, asymmetry_candidates = _detect_symmetry_and_asymmetry(segment_candidates, input_summary)
    candidate_grammar = _build_candidate_grammar(motif_clusters, recurring_symbol_candidates, segment_candidates)
    unmapped_regions = _build_unmapped_regions(segment_candidates, _compact_text(source_signal.get("signal_origin"), default="artifact_summary_only"))
    signal_hypotheses, noise_hypotheses = _build_signal_hypotheses(motif_clusters, recurring_symbol_candidates, segment_candidates)
    next_probes, falsification_probes, rule_pressure_tests = _build_next_and_falsification_probes(motif_clusters, unmapped_regions, segment_candidates)
    compression_summary = _build_compression_summary(base_packet, segment_candidates, motif_clusters, recurring_symbol_candidates, unmapped_regions)

    if isinstance(data.get("candidate_grammar"), Mapping):
        candidate_grammar = _json_safe(data.get("candidate_grammar"))
    if isinstance(data.get("next_probes"), list) and data.get("next_probes"):
        next_probes = _json_safe(data.get("next_probes"))
    if isinstance(data.get("falsification_probes"), list) and data.get("falsification_probes"):
        falsification_probes = _json_safe(data.get("falsification_probes"))
    if isinstance(data.get("rule_pressure_tests"), list) and data.get("rule_pressure_tests"):
        rule_pressure_tests = _json_safe(data.get("rule_pressure_tests"))
    if isinstance(data.get("signal_hypotheses"), list) and data.get("signal_hypotheses"):
        signal_hypotheses = _json_safe(data.get("signal_hypotheses"))
    if isinstance(data.get("noise_hypotheses"), list) and data.get("noise_hypotheses"):
        noise_hypotheses = _json_safe(data.get("noise_hypotheses"))

    raw_artifact_included = _raw_artifact_is_inline(data)
    raw_artifact_length = _safe_float(len(_compact_text(data.get("raw_artifact"), default="")) if data.get("raw_artifact") is not None else 0, 0.0)
    raw_artifact_digest = _stable_digest({"artifact_ref": input_artifact_ref, "summary": input_summary, "inline": raw_artifact_included})[:16]

    packet = {
        **base_packet,
        "denied_authority": None if denied_authority_missing else ({} if denied_authority_empty else base_packet.get("denied_authority")),
        "segmentation_summary": segmentation_summary,
        "segment_candidates": segment_candidates,
        "motif_clusters": motif_clusters,
        "recurring_symbol_candidates": recurring_symbol_candidates,
        "operator_like_transformations": operator_like_transformations,
        "stable_regions": stable_regions,
        "unstable_regions": unstable_regions,
        "symmetry_candidates": symmetry_candidates,
        "asymmetry_candidates": asymmetry_candidates,
        "candidate_grammar": candidate_grammar,
        "compression_summary": compression_summary,
        "unmapped_regions": unmapped_regions,
        "noise_hypotheses": noise_hypotheses,
        "signal_hypotheses": signal_hypotheses,
        "next_probes": next_probes,
        "falsification_probes": falsification_probes,
        "rule_pressure_tests": rule_pressure_tests,
        "raw_artifact_included": raw_artifact_included,
        "raw_artifact_ref_only": not raw_artifact_included,
        "raw_artifact_length": raw_artifact_length,
        "raw_artifact_digest": raw_artifact_digest,
        "cartography_mode": "summary_preserving",
        "cartography_notes": "raw artifacts are not stored; only metadata about structure is retained",
        "safe_metadata": {
            **_build_safe_metadata(),
            **(_json_safe(safe_metadata) if isinstance(safe_metadata, Mapping) else {}),
            "cartography_only": True,
            "raw_artifacts_not_stored": True,
            "public_export_blocked": True,
            "engine_name": engine_name,
            "engine_family": engine_family,
            "research_mode": research_mode,
        },
    }
    if "compressed_lesson" not in packet or not _compact_text(packet.get("compressed_lesson")):
        packet["compressed_lesson"] = compression_summary["compressed_lesson"]
    return _json_safe(packet)


def _validate_segment_candidates(packet: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    segments = packet.get("segment_candidates")
    if not isinstance(segments, list) or not segments:
        return ["missing_segment_candidates"]
    for index, segment in enumerate(segments):
        if not isinstance(segment, Mapping):
            violations.append(f"invalid_segment_candidate_{index}")
            continue
        for field in ("segment_id", "segment_summary", "segment_kind", "stability", "token_count", "symbol_ratio"):
            if field not in segment:
                violations.append(f"missing_segment_candidate_{index}_{field}")
        if _compact_text(segment.get("stability")) not in _ALLOWED_STABILITY_VALUES_V1:
            violations.append(f"unknown_segment_stability_{index}")
        if _compact_text(segment.get("segment_kind")) not in _ALLOWED_REGION_KIND_VALUES_V1:
            violations.append(f"unknown_segment_kind_{index}")
    return violations


def _validate_named_list_of_mappings(packet: Mapping[str, Any], field_name: str, required_fields: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    value = packet.get(field_name)
    if not isinstance(value, list):
        return [f"missing_{field_name}"]
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            violations.append(f"invalid_{field_name}_{index}")
            continue
        for field in required_fields:
            if field not in item:
                violations.append(f"missing_{field_name}_{index}_{field}")
    return violations


def _validate_candidate_grammar(packet: Mapping[str, Any]) -> list[str]:
    grammar = packet.get("candidate_grammar")
    if not isinstance(grammar, Mapping):
        return ["missing_candidate_grammar"]
    violations: list[str] = []
    for field in ("grammar_id", "terminals", "nonterminals", "rules", "notes"):
        if field not in grammar:
            violations.append(f"missing_candidate_grammar_{field}")
    if not isinstance(grammar.get("terminals"), list) or not grammar.get("terminals"):
        violations.append("invalid_candidate_grammar_terminals")
    if not isinstance(grammar.get("nonterminals"), list) or not grammar.get("nonterminals"):
        violations.append("invalid_candidate_grammar_nonterminals")
    if not isinstance(grammar.get("rules"), list) or not grammar.get("rules"):
        violations.append("invalid_candidate_grammar_rules")
    return violations


def _validate_raw_artifact_rules(packet: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    if not _compact_text(packet.get("input_artifact_ref")) or _compact_text(packet.get("input_artifact_ref")) == "artifact:unknown":
        violations.append("missing_safe_artifact_reference")
    summary_text = _compact_text(packet.get("input_summary"))
    if not summary_text:
        violations.append("missing_safe_artifact_summary")
    if _raw_artifact_is_inline(packet):
        violations.append("full_massive_artifact_included_inline")
    if len(summary_text) > 1200:
        violations.append("inline_summary_too_large")
    if "raw private text" in summary_text.lower() or "hidden prompt" in summary_text.lower():
        violations.append("raw_private_or_hidden_text")
    if any(marker in summary_text.lower() for marker in ("```python", "```bash", "python -c", "run this code", "execute this code")):
        violations.append("executable_code_as_action")
    return violations


def _validate_cartography_fields(packet: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    allowed_source_origins = set(_ALLOWED_SOURCE_ORIGINS_V1)
    if _compact_text(_ensure_mapping(packet.get("source_signal")).get("signal_origin")) not in allowed_source_origins:
        violations.append("unknown_source_origin")
    if _compact_text(packet.get("public_claim_status")) == "public_export_blocked" and _safe_bool(_ensure_mapping(packet.get("safe_metadata")).get("public_export_safe", False)):
        violations.append("public_export_marked_safe_by_default")
    if _safe_bool(_ensure_mapping(packet.get("safe_metadata")).get("public_export_safe", False)):
        violations.append("public_export_marked_safe_by_default")
    if _compact_text(packet.get("public_gap_card_status")) != "public_export_blocked":
        violations.append("public_gap_card_not_blocked")
    if any(_compact_text(packet.get(field)).lower() in {"live", "live_feed", "live_ingestion"} for field in ("source_scope", "research_mode")):
        violations.append("live_ingestion_not_allowed")
    source_signal = _ensure_mapping(packet.get("source_signal"))
    if any(token in _compact_text(source_signal.get("signal_origin")).lower() for token in ("live", "rss", "github", "notebook", "feed")):
        violations.append("live_ingestion_not_allowed")
    cartography_text = " ".join(
        _compact_text(packet.get(field)).lower()
        for field in (
            "input_summary",
            "compressed_lesson",
            "cartography_notes",
            "source_scope",
            "research_mode",
        )
    )
    if ".weslr" in cartography_text:
        violations.append("dot_weslr_implication")
    if any(marker in cartography_text for marker in ("network", "rss", "github", "lab notebook", "live ingest", "live ingestion")):
        violations.append("live_ingestion_or_network_implication")
    if any(marker in cartography_text for marker in ("live", "feed", "crawler", "fetch")) and any(marker in cartography_text for marker in ("github", "rss", "network", "lab notebook")):
        violations.append("live_ingestion_or_network_implication")
    return violations


def _ensure_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def validate_raw_signal_cartography_packet_v1(packet: Any) -> dict[str, Any]:
    raw = packet if isinstance(packet, Mapping) else {}
    protocol_validation = validate_cognitive_research_run_v1(raw)
    violations = list(protocol_validation.get("blocked_labels", []))

    violations.extend(_validate_raw_artifact_rules(raw))
    violations.extend(_validate_segment_candidates(raw))
    violations.extend(_validate_named_list_of_mappings(raw, "motif_clusters", ("cluster_id", "motif", "recurrence")))
    violations.extend(_validate_named_list_of_mappings(raw, "recurring_symbol_candidates", ("symbol", "count", "role")))
    violations.extend(_validate_named_list_of_mappings(raw, "operator_like_transformations", ("operator", "transformation", "confidence")))
    violations.extend(_validate_named_list_of_mappings(raw, "stable_regions", ("region_id", "region_summary", "evidence", "confidence")))
    violations.extend(_validate_named_list_of_mappings(raw, "unstable_regions", ("region_id", "region_summary", "evidence", "confidence")))
    violations.extend(_validate_named_list_of_mappings(raw, "symmetry_candidates", ("candidate_id", "pattern", "marker", "rationale", "confidence")))
    violations.extend(_validate_named_list_of_mappings(raw, "asymmetry_candidates", ("candidate_id", "pattern", "marker", "rationale", "confidence")))
    violations.extend(_validate_named_list_of_mappings(raw, "unmapped_regions", ("region_id", "reason", "next_probe", "mapping_state")))
    violations.extend(_validate_named_list_of_mappings(raw, "noise_hypotheses", ("hypothesis_id", "claim", "evidence", "confidence")))
    violations.extend(_validate_named_list_of_mappings(raw, "signal_hypotheses", ("hypothesis_id", "claim", "evidence", "confidence")))
    violations.extend(_validate_named_list_of_mappings(raw, "next_probes", ("probe_id", "probe", "purpose")))
    violations.extend(_validate_named_list_of_mappings(raw, "falsification_probes", ("probe_id", "probe", "purpose")))
    violations.extend(_validate_named_list_of_mappings(raw, "rule_pressure_tests", ("test_id", "target_rule_or_operator", "pressure_type", "mutated_input_summary", "expected_behavior", "observed_behavior", "result", "failure_mode", "scope_update")))
    violations.extend(_validate_named_list_of_mappings(raw, "segment_candidates", ("segment_id", "segment_summary", "segment_kind", "stability", "token_count", "symbol_ratio")))
    violations.extend(_validate_candidate_grammar(raw))
    violations.extend(_validate_cartography_fields(raw))

    safe_metadata = _ensure_mapping(raw.get("safe_metadata"))
    if not _safe_bool(safe_metadata.get("safe", False)):
        violations.append("unsafe_safe_metadata")
    if not _safe_bool(safe_metadata.get("metadata_only", False)):
        violations.append("unsafe_safe_metadata")
    if _safe_bool(safe_metadata.get("perspicuity_is_gate", False)) or _safe_bool(safe_metadata.get("use_perspicuity_as_gate", False)):
        violations.append("perspicuity_used_as_gate")

    denied = raw.get("denied_authority")
    if not isinstance(denied, Mapping) or not denied:
        violations.append("missing_denied_authority")
    else:
        default_denied_keys = tuple(build_default_cognitive_research_denied_authority_v1().keys())
        for key in default_denied_keys:
            if key not in denied:
                violations.append(f"missing_denied_authority_{key}")
            elif _safe_bool(denied.get(key)):
                violations.append(f"denied_authority_granted_{key}")
    if denied is None:
        violations.append("missing_denied_authority")

    if _compact_text(raw.get("engine_name")) != ENGINE_NAME_V1:
        violations.append("unknown_engine_name")
    if _compact_text(raw.get("engine_family")) != ENGINE_FAMILY_V1:
        violations.append("unknown_engine_family")
    if _compact_text(raw.get("research_mode")) not in _ALLOWED_RESEARCH_MODES_V1:
        violations.append("unknown_research_mode")
    if _compact_text(raw.get("public_claim_status")) not in _ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        violations.append("unknown_public_claim_status")
    if _compact_text(raw.get("public_gap_card_status")) not in _ALLOWED_PUBLIC_GAP_CARD_STATUSES_V1:
        violations.append("unknown_public_gap_card_status")
    if _compact_text(raw.get("llm_helper_role")) not in _ALLOWED_LLM_HELPER_ROLES_V1:
        violations.append("unknown_llm_helper_role")

    blocked = sorted({violation for violation in violations if violation})
    classification = {
        "engine_name": _compact_text(raw.get("engine_name")) or ENGINE_NAME_V1,
        "engine_family": _compact_text(raw.get("engine_family")) or ENGINE_FAMILY_V1,
        "cartography_state": "blocked" if blocked else "mapped",
        "public_claim_status": _compact_text(raw.get("public_claim_status")) or "internal_candidate_only",
    }
    summary_text = _cartography_summary(raw, bool(blocked), blocked)
    return {
        "valid": not blocked,
        "violation_count": len(blocked),
        "violations": blocked,
        "classification": classification,
        "summary_text": summary_text,
        "packet": _json_safe(raw),
    }


def _cartography_summary(packet: Mapping[str, Any], blocked: bool, labels: list[str]) -> str:
    engine_name = _compact_text(packet.get("engine_name")) or ENGINE_NAME_V1
    artifact_ref = _compact_text(packet.get("input_artifact_ref")) or "artifact:unknown"
    segmentation = _ensure_mapping(packet.get("segmentation_summary"))
    segment_count = _compact_text(segmentation.get("segment_count")) or "0"
    motif_count = _compact_text(len(_ensure_list(packet.get("motif_clusters"))))
    unstable_count = _compact_text(len(_ensure_list(packet.get("unstable_regions"))))
    probe_count = _compact_text(len(_ensure_list(packet.get("next_probes"))))
    if blocked:
        preview = ", ".join(labels[:4]) or "validation failed"
        return f"Blocked raw signal cartography: {preview}. engine={engine_name}; artifact={artifact_ref}."
    return (
        f"Raw signal cartography: engine={engine_name}; artifact={artifact_ref}; segments={segment_count}; "
        f"motifs={motif_count}; unstable={unstable_count}; probes={probe_count}; public=blocked."
    )


def summarize_raw_signal_cartography_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_raw_signal_cartography_packet_v1(packet)
    raw = packet if isinstance(packet, Mapping) else {}
    summary_text = _cartography_summary(raw, not validation["valid"], validation["violations"])
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "summary_text": summary_text[:320],
        "valid": validation["valid"],
        "violation_count": validation["violation_count"],
        "violations": validation["violations"],
        "classification": validation["classification"],
        "packet": validation["packet"],
    }


def to_raw_signal_cartography_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)


def build_initial_raw_signal_cartography_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_raw_signal_cartography_packet_v1(
            input_artifact_ref="artifact:cartography-example-001",
            input_summary="αβ :: αβ :: ??? map the repeated boundary tokens and keep the strange structure intact.",
            research_mode="internal_exploration",
            safe_metadata={"safe": True, "metadata_only": True},
            signal_hypotheses=[{"hypothesis_id": "signal-h1", "claim": "delimiter recurrence preserves a weak grammar", "evidence": ["::"], "confidence": 71.0}],
        ),
        build_raw_signal_cartography_packet_v1(
            input_artifact_ref="artifact:cartography-example-002",
            input_summary="-> fold -> translate -> invert -> map -> compress; operator-like sequence with noise spikes.",
            research_mode="synthetic_test",
            next_probes=[{"probe_id": "probe-operator-loop", "probe": "Check whether the arrow chain survives normalization.", "purpose": "operator recurrence"}],
            rule_pressure_tests=[{"test_id": "pressure-example-002", "target_rule_or_operator": "operator-like sequence", "pressure_type": "counterexample", "mutated_input_summary": "replace arrows with neutral separators", "expected_behavior": "operator chain remains visible", "observed_behavior": "pending", "result": "pending", "failure_mode": "none", "scope_update": "metadata_only"}],
        ),
        build_raw_signal_cartography_packet_v1(
            input_artifact_ref="artifact:" + ("A" * 5000),
            input_summary="bounded summary for a very large safe reference only; no inline raw artifact stored.",
            research_mode="internal_exploration",
        ),
        build_raw_signal_cartography_packet_v1(
            input_artifact_ref="artifact:cartography-example-004",
            input_summary="noise noise motif motif symbol symbol with a random-control hypothesis and weak asymmetry.",
            research_mode="synthetic_test",
            noise_hypotheses=[{"hypothesis_id": "noise-h1", "claim": "some regions are noise-dominant", "evidence": ["noise"], "confidence": 59.0}],
        ),
        build_raw_signal_cartography_packet_v1(
            input_artifact_ref="artifact:cartography-example-005",
            input_summary="segment cluster compress map probe. segment cluster compress map probe.",
            research_mode="internal_exploration",
            candidate_grammar={"grammar_id": "grammar-example", "terminals": ["segment", "cluster", "compress", "map", "probe"], "nonterminals": ["RUN", "REGION"], "rules": [{"lhs": "RUN", "rhs": ["REGION", "MOTIF", "PROBE"]}], "notes": "example grammar metadata"},
        ),
        build_raw_signal_cartography_packet_v1(
            input_artifact_ref="artifact:cartography-example-006",
            input_summary="stable core; unstable tail; compare and falsify the boundary assumption.",
            research_mode="synthetic_test",
            falsification_probes=[{"probe_id": "falsify-example", "probe": "Swap the stable core and unstable tail to see whether the boundary survives.", "purpose": "boundary falsification"}],
        ),
    ]
    return examples
