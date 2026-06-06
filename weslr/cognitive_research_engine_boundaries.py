"""Metadata-only helpers for WESLR cognitive research engine boundaries v1.

This module is intentionally pure, deterministic, JSON-safe, and fail-closed.
It stores reviewed engine-boundary metadata only; it does not execute runtime,
tool, provider, search, persistence, proof, or public-claim authority.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "cognitive_research_engine_boundaries_v1"
HELPER_TYPE_V1 = "weslr_cognitive_research_engine_boundaries_v1"

_ALLOWED_ENGINE_NAMES_V1 = (
    "RAW_SIGNAL_CARTOGRAPHER",
    "UNINTELLIGIBLE_OUTPUT_ANALYZER",
    "SIGNAL_VS_NOISE_ENGINE",
    "ALGORITHM_EMERGENCE_ENGINE",
    "MUTABLE_AXIOM_MATH_ENGINE",
)

_ENGINE_SEQUENCE_V1 = _ALLOWED_ENGINE_NAMES_V1

_REQUIRED_BOUNDARY_FIELDS_V1 = (
    "schema_version",
    "engine_name",
    "sequence_index",
    "engine_identity",
    "uniqueness_statement",
    "cognitive_kernel",
    "primitive_space",
    "observation_style",
    "transformation_grammar",
    "mutation_probe_strategy",
    "novelty_detector",
    "contradiction_invalidation_loop",
    "compression_style",
    "failure_modes",
    "safe_input_categories",
    "forbidden_input_categories",
    "output_categories",
    "anti_flattening_rule",
    "prior_engine_name",
    "next_engine_name",
    "relationship_to_cognitive_research_run_v1",
    "denied_authority",
    "public_claim_restrictions",
    "metadata_only",
    "engine_family",
    "engine_relationship_graph",
)

_REQUIRED_DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_authority",
    "runtime_execution_authority",
    "tool_authority",
    "provider_authority",
    "search_authority",
    "persistence_authority",
    "public_export_authority",
    "proof_authority",
    "solution_authority",
    "benchmark_authority",
    "official_result_authority",
    "public_readiness_authority",
)

_REQUIRED_PUBLIC_CLAIM_RESTRICTION_FIELDS_V1 = (
    "proof_claims_blocked",
    "breakthrough_claims_blocked",
    "solved_claims_blocked",
    "certification_claims_blocked",
    "benchmark_claims_blocked",
    "public_readiness_claims_blocked",
    "official_result_claims_blocked",
    "open_problem_solution_claims_blocked",
)

_REQUIRED_RUN_RELATIONSHIP_FIELDS_V1 = (
    "role",
    "envelope_only",
    "not_engine_kernel",
    "not_runtime_authority",
    "not_proof_authority",
    "not_public_claim_authority",
)

_FORBIDDEN_IMPORT_MARKERS_V1 = (
    "subprocess",
    "os.system",
    "socket",
    "urllib",
    "requests",
    "http.client",
    "asyncio",
)

_FORBIDDEN_FLATTENING_MARKERS_V1 = (
    "generic assistant",
    "generic evaluator",
    "generic summarizer",
    "proof solver",
    "programming assistant",
    "math tutor",
    "normal theorem prover",
)

_ENGINE_META_V1 = {
    "RAW_SIGNAL_CARTOGRAPHER": {
        "engine_family": "raw-signal",
        "sequence_index": 1,
        "engine_identity": "maps strange raw artifacts as signal terrain instead of flattening them into noise.",
        "uniqueness_statement": "Uniquely maps raw terrain, motifs, zones, and probe opportunities while preserving texture.",
        "cognitive_kernel": "observe raw artifact geometry, preserve unusual structure, and map stable/unstable regions without collapsing the artifact.",
        "primitive_space": (
            "glyphs",
            "symbols",
            "fragments",
            "repetitions",
            "interruptions",
            "bursts",
            "gaps",
            "clusters",
            "edges",
            "drift",
            "resonance",
            "compression candidates",
            "probe candidates",
        ),
        "observation_style": "terrain-oriented, noting repeated texture, breaks, mutations, resistance to interpretation, and unknown regions.",
        "transformation_grammar": (
            "segment",
            "cluster",
            "align",
            "contrast",
            "fold",
            "isolate",
            "densify",
            "annotate",
            "compress",
            "expand",
            "probe",
            "map",
            "trace",
            "label",
        ),
        "mutation_probe_strategy": "identify weak motifs, perturb one axis, compare local change, and update the terrain map.",
        "novelty_detector": "repeatable unexpected motifs, boundary shapes, unstable-to-stable transitions, and hidden organization revealed by compression.",
        "contradiction_invalidation_loop": "retain failed labels as invalidated, annotate failure reasons, and refine the terrain map.",
        "compression_style": "preserve terrain texture, uncertainty, invalidation notes, and next probe labels.",
        "failure_modes": (
            "flattening into a summary",
            "discarding strange texture too early",
            "turning into a generic research assistant",
            "claiming explanation too early",
        ),
        "safe_input_categories": (
            "synthetic symbolic stream",
            "terrain map metadata",
            "raw signal log reference",
            "generated strange artifact summary",
            "candidate motif map",
        ),
        "forbidden_input_categories": (
            "raw private data",
            "secrets",
            "hidden/system prompts",
            ".weslr contents",
            "full massive raw artifact storage",
            "executable code-as-action",
            "live tool instructions",
            "dangerous procedural instructions",
            "provider/model output claimed as authority",
        ),
        "output_categories": (
            "terrain map metadata",
            "motif candidates",
            "stable/unstable region labels",
            "probe labels",
            "uncertainty map",
            "invalidated candidates",
        ),
        "anti_flattening_rule": "Never collapse raw terrain into a generic answer; preserve strange fragments, uncertainty, and invalidation history.",
        "prior_engine_name": None,
        "next_engine_name": "UNINTELLIGIBLE_OUTPUT_ANALYZER",
        "relationship_to_cognitive_research_run_v1": {
            "role": "reporting_safety_envelope_only",
            "envelope_only": True,
            "not_engine_kernel": True,
            "not_runtime_authority": True,
            "not_proof_authority": True,
            "not_public_claim_authority": True,
        },
        "denied_authority": {
            "runtime_authority": False,
            "runtime_execution_authority": False,
            "tool_authority": False,
            "provider_authority": False,
            "search_authority": False,
            "persistence_authority": False,
            "public_export_authority": False,
            "proof_authority": False,
            "solution_authority": False,
            "benchmark_authority": False,
            "official_result_authority": False,
            "public_readiness_authority": False,
        },
        "public_claim_restrictions": {
            "proof_claims_blocked": True,
            "breakthrough_claims_blocked": True,
            "solved_claims_blocked": True,
            "certification_claims_blocked": True,
            "benchmark_claims_blocked": True,
            "public_readiness_claims_blocked": True,
            "official_result_claims_blocked": True,
            "open_problem_solution_claims_blocked": True,
        },
    },
    "UNINTELLIGIBLE_OUTPUT_ANALYZER": {
        "engine_family": "raw-signal",
        "sequence_index": 2,
        "engine_identity": "preserves alien structure and competing interpretation layers instead of flattening to one answer.",
        "uniqueness_statement": "Uniquely holds multiple readings open until evidence earns a narrower interpretation.",
        "cognitive_kernel": "preserve unknown structure, compare competing interpretations, and keep translation resistance visible.",
        "primitive_space": (
            "unknown tokens",
            "partial phrases",
            "alien fragments",
            "syntax-like runs",
            "semantic breaks",
            "repetition islands",
            "translation barriers",
            "candidate notation cues",
            "ambiguity markers",
            "competing parse hints",
            "fracture edges",
            "confidence deltas",
        ),
        "observation_style": "interpretive but non-final, noting translation resistance, fractures, multiple readings, and open meaning candidates.",
        "transformation_grammar": (
            "parse",
            "segment",
            "cluster",
            "align",
            "contrast",
            "translate-candidate",
            "preserve",
            "annotate",
            "isolate",
            "compare",
            "layer",
            "map",
            "label",
            "fracture",
            "bridge",
        ),
        "mutation_probe_strategy": "preserve the fragment, propose one translation layer, compare a rival layer, and update the ambiguity map.",
        "novelty_detector": "unknown tokens that repeat with structure, resisting parses, meaning shifts under re-interpretation, and translation stability under probes.",
        "contradiction_invalidation_loop": "compare interpretation layers against each other and the raw fragments, retaining invalidated layers with reasons.",
        "compression_style": "preserve uncertainty and interpretive plurality in ambiguity maps, fracture labels, and next interpretation experiments.",
        "failure_modes": (
            "forcing immediate human-readable explanation",
            "discarding unknown tokens too early",
            "calling strange output garbage by default",
            "turning into a normal summarizer",
        ),
        "safe_input_categories": (
            "synthetic symbolic stream",
            "interpretation layer metadata",
            "compressed artifact summary",
            "generated strange artifact summary",
            "candidate motif map",
        ),
        "forbidden_input_categories": (
            "raw private data",
            "secrets",
            "hidden/system prompts",
            ".weslr contents",
            "full massive raw artifact storage",
            "executable code-as-action",
            "live tool instructions",
            "dangerous procedural instructions",
            "provider/model output claimed as authority",
        ),
        "output_categories": (
            "candidate translation layers",
            "competing interpretation map",
            "ambiguity map",
            "semantic fracture labels",
            "translation probes",
            "invalidated interpretations",
        ),
        "anti_flattening_rule": "Never collapse unintelligible output into one neat explanation; preserve unknown tokens, competing readings, and uncertainty texture.",
        "prior_engine_name": "RAW_SIGNAL_CARTOGRAPHER",
        "next_engine_name": "SIGNAL_VS_NOISE_ENGINE",
        "relationship_to_cognitive_research_run_v1": {
            "role": "reporting_safety_envelope_only",
            "envelope_only": True,
            "not_engine_kernel": True,
            "not_runtime_authority": True,
            "not_proof_authority": True,
            "not_public_claim_authority": True,
        },
        "denied_authority": {
            "runtime_authority": False,
            "runtime_execution_authority": False,
            "tool_authority": False,
            "provider_authority": False,
            "search_authority": False,
            "persistence_authority": False,
            "public_export_authority": False,
            "proof_authority": False,
            "solution_authority": False,
            "benchmark_authority": False,
            "official_result_authority": False,
            "public_readiness_authority": False,
        },
        "public_claim_restrictions": {
            "proof_claims_blocked": True,
            "breakthrough_claims_blocked": True,
            "solved_claims_blocked": True,
            "certification_claims_blocked": True,
            "benchmark_claims_blocked": True,
            "public_readiness_claims_blocked": True,
            "official_result_claims_blocked": True,
            "open_problem_solution_claims_blocked": True,
        },
    },
    "SIGNAL_VS_NOISE_ENGINE": {
        "engine_family": "raw-signal",
        "sequence_index": 3,
        "engine_identity": "classifies randomness, pseudo-random structure, weak signal, artifact effect, and undecidable regions.",
        "uniqueness_statement": "Uniquely applies discrimination pressure when the signal/noise boundary is still forming.",
        "cognitive_kernel": "estimate structure pressure, compare explanations for variation, and preserve weak structure until it can be classified.",
        "primitive_space": (
            "random bursts",
            "repeated fragments",
            "local regularities",
            "pseudo-randomness hints",
            "weak motifs",
            "transition bands",
            "clustering pressure",
            "artifact echoes",
            "variance islands",
            "boundary jitter",
            "candidate grammar seeds",
            "stability deltas",
        ),
        "observation_style": "discriminative but cautious, tracking what looks random, structured-but-unstable, artifact-like, or undecidable.",
        "transformation_grammar": (
            "measure",
            "compare",
            "cluster",
            "separate",
            "contrast",
            "label",
            "segment",
            "stabilize",
            "perturb",
            "probe",
            "estimate",
            "map",
            "score",
            "annotate",
        ),
        "mutation_probe_strategy": "isolate a candidate region, perturb one axis, compare persistence, and update the classification map.",
        "novelty_detector": "persistent structure stronger than chance, weak signal that survives perturbation, pseudo-random regularities, and artifact-effect signatures.",
        "contradiction_invalidation_loop": "compare signal candidates against noise and artifact-effect candidates, retaining invalidated candidates with reasons.",
        "compression_style": "preserve uncertainty and boundary texture in classification maps, invalidation notes, and next probes.",
        "failure_modes": (
            "deleting noise before it is studied",
            "calling all weak structure signal",
            "mistaking artifact effect for signal",
            "overfitting a grammar too early",
        ),
        "safe_input_categories": (
            "synthetic symbolic stream",
            "terrain map metadata",
            "unintelligible-output interpretation map",
            "compressed artifact summary",
            "raw signal log reference",
            "RF/sensor metadata reference",
            "generated strange artifact summary",
            "candidate motif map",
        ),
        "forbidden_input_categories": (
            "raw private data",
            "secrets",
            "hidden/system prompts",
            ".weslr contents",
            "full massive raw artifact storage",
            "executable code-as-action",
            "live tool instructions",
            "dangerous procedural instructions",
            "provider/model output claimed as authority",
        ),
        "output_categories": (
            "signal/noise classification map",
            "weak-signal candidates",
            "pseudo-randomness labels",
            "emerging-grammar labels",
            "stable/unstable signal labels",
            "artifact-effect labels",
            "undecidable-region labels",
            "confidence/uncertainty map",
            "invalidated rule candidates",
            "next probe labels",
        ),
        "anti_flattening_rule": "Never reduce the spectrum to binary yes/no too early; preserve randomness, weak signal, artifact effect, instability, and undecidability texture.",
        "prior_engine_name": "UNINTELLIGIBLE_OUTPUT_ANALYZER",
        "next_engine_name": "ALGORITHM_EMERGENCE_ENGINE",
        "relationship_to_cognitive_research_run_v1": {
            "role": "reporting_safety_envelope_only",
            "envelope_only": True,
            "not_engine_kernel": True,
            "not_runtime_authority": True,
            "not_proof_authority": True,
            "not_public_claim_authority": True,
        },
        "denied_authority": {
            "runtime_authority": False,
            "runtime_execution_authority": False,
            "tool_authority": False,
            "provider_authority": False,
            "search_authority": False,
            "persistence_authority": False,
            "public_export_authority": False,
            "proof_authority": False,
            "solution_authority": False,
            "benchmark_authority": False,
            "official_result_authority": False,
            "public_readiness_authority": False,
        },
        "public_claim_restrictions": {
            "proof_claims_blocked": True,
            "breakthrough_claims_blocked": True,
            "solved_claims_blocked": True,
            "certification_claims_blocked": True,
            "benchmark_claims_blocked": True,
            "public_readiness_claims_blocked": True,
            "official_result_claims_blocked": True,
            "open_problem_solution_claims_blocked": True,
        },
    },
    "ALGORITHM_EMERGENCE_ENGINE": {
        "engine_family": "gap",
        "sequence_index": 4,
        "engine_identity": "detects candidate algorithmic behavior emerging from signal terrain, interpretation layers, and signal/noise maps.",
        "uniqueness_statement": "Uniquely recognizes when structure starts behaving like a process.",
        "cognitive_kernel": "observe repeated transformation behavior, infer candidate rules, and test whether stable operator chains preserve procedure-like output.",
        "primitive_space": (
            "repeated transformations",
            "local rules",
            "operator chains",
            "inputs and outputs",
            "state transitions",
            "recursive steps",
            "self-similarity",
            "invariant-preserving moves",
            "compression candidates",
            "perturbation effects",
            "process fragments",
            "rule seeds",
            "stability deltas",
        ),
        "observation_style": "process-oriented and cautious, noting repeated transformation, chaining, recursion, state change, and undecidable process regions.",
        "transformation_grammar": (
            "observe",
            "compare",
            "chain",
            "compose",
            "segment",
            "label",
            "test",
            "perturb",
            "probe",
            "map",
            "compress",
            "infer",
            "isolate",
            "annotate",
        ),
        "mutation_probe_strategy": "vary one step in a candidate process, compare resulting transitions, and update the algorithm-likeness map.",
        "novelty_detector": "repeatable transformations, local rules that generalize, operator chains that survive perturbation, recursion traces, and invariant-preserving transitions.",
        "contradiction_invalidation_loop": "compare candidates against local imitation, artifact effect, and undecidable process regions, retaining invalidations with reasons.",
        "compression_style": "preserve process texture, uncertainty, invalidation history, and next probe labels.",
        "failure_modes": (
            "calling any repeated pattern an algorithm too early",
            "mistaking imitation for rule discovery",
            "proving instead of classifying",
            "flattening into a programming assistant",
        ),
        "safe_input_categories": (
            "synthetic symbolic stream",
            "terrain map metadata",
            "interpretation layer metadata",
            "signal/noise classification map",
            "compressed artifact summary",
            "candidate motif map",
            "weak-signal candidate map",
            "non-private generated strange artifact summary",
            "operator-like transformation labels",
        ),
        "forbidden_input_categories": (
            "raw private data",
            "secrets",
            "hidden/system prompts",
            ".weslr contents",
            "full massive raw artifact storage",
            "executable code-as-action",
            "live tool instructions",
            "dangerous procedural instructions",
            "provider/model output claimed as authority",
            "real-world control procedures",
        ),
        "output_categories": (
            "candidate algorithm map",
            "operator-chain candidates",
            "transformation-rule candidates",
            "state-transition hints",
            "invariant candidates",
            "recursion/self-similarity labels",
            "algorithm-likeness confidence map",
            "invalidated rule candidates",
            "undecidable process regions",
            "next probe labels",
        ),
        "anti_flattening_rule": "Never collapse process-like behavior into a generic summary or premature solved algorithm; preserve chain structure, recursion hints, invariant texture, and uncertainty.",
        "prior_engine_name": "SIGNAL_VS_NOISE_ENGINE",
        "next_engine_name": "MUTABLE_AXIOM_MATH_ENGINE",
        "relationship_to_cognitive_research_run_v1": {
            "role": "reporting_safety_envelope_only",
            "envelope_only": True,
            "not_engine_kernel": True,
            "not_runtime_authority": True,
            "not_proof_authority": True,
            "not_public_claim_authority": True,
        },
        "denied_authority": {
            "runtime_authority": False,
            "runtime_execution_authority": False,
            "tool_authority": False,
            "provider_authority": False,
            "search_authority": False,
            "persistence_authority": False,
            "public_export_authority": False,
            "proof_authority": False,
            "solution_authority": False,
            "benchmark_authority": False,
            "official_result_authority": False,
            "public_readiness_authority": False,
        },
        "public_claim_restrictions": {
            "proof_claims_blocked": True,
            "breakthrough_claims_blocked": True,
            "solved_claims_blocked": True,
            "certification_claims_blocked": True,
            "benchmark_claims_blocked": True,
            "public_readiness_claims_blocked": True,
            "official_result_claims_blocked": True,
            "open_problem_solution_claims_blocked": True,
        },
    },
    "MUTABLE_AXIOM_MATH_ENGINE": {
        "engine_family": "math",
        "sequence_index": 5,
        "engine_identity": "explores symbolic or mathematical systems by mutating axioms, rules, operators, or constraints and tracking terrain shifts.",
        "uniqueness_statement": "Uniquely treats assumptions as research objects and observes how proof shape and obstruction shape change.",
        "cognitive_kernel": "vary an axiom or rule, compare the resulting symbolic terrain, and preserve uncertainty about consistency, instability, degeneracy, or new structural regimes.",
        "primitive_space": (
            "axioms",
            "axiom variants",
            "inference rules",
            "constraints",
            "operators",
            "invariants",
            "contradiction surfaces",
            "boundary cases",
            "degenerate cases",
            "toy-model frames",
            "proof obstructions",
            "consistency candidates",
            "instability candidates",
            "symbolic terrain shifts",
        ),
        "observation_style": "comparative and terrain-oriented, noting stability, provability, obstructions, collapses, new forms, contradictions, and category shifts.",
        "transformation_grammar": (
            "vary",
            "replace",
            "perturb",
            "compare",
            "map",
            "label",
            "segment",
            "isolate",
            "contrast",
            "compress",
            "annotate",
            "trace",
            "probe",
            "interpret",
        ),
        "mutation_probe_strategy": "select a base axiom or rule set, mutate one assumption, compare invariant behavior and proof shape, and update the terrain shift map.",
        "novelty_detector": "surprising invariant survival, proof-obstruction patterns, new theorem shapes, moved consistency boundaries, and symbolic terrain shifts.",
        "contradiction_invalidation_loop": "compare axiom variants against contradiction surfaces, degeneracy, and proof-obstruction maps, retaining invalidations with reasons.",
        "compression_style": "preserve the effect of assumption changes in mutable-axiom maps, obstruction maps, and invalidation history.",
        "failure_modes": (
            "turning into a theorem prover",
            "turning into a generic math tutor",
            "claiming a proof or solved open problem status",
            "presenting speculative results as verified truth",
        ),
        "safe_input_categories": (
            "synthetic symbolic system",
            "toy mathematical structure",
            "public/open mathematical statement summary",
            "axiom list reference",
            "operator list reference",
            "invariant candidate map",
            "algorithm-emergence metadata",
            "signal/noise classification map",
            "compressed symbolic artifact summary",
        ),
        "forbidden_input_categories": (
            "private/raw user data",
            "secrets",
            "hidden/system prompts",
            ".weslr contents",
            "full massive raw artifact storage",
            "executable code-as-action",
            "live tool instructions",
            "dangerous procedural instructions",
            "official proof claims",
            "claimed solutions to open problems",
            "benchmark answer keys",
            "hidden/private/semi-private benchmark data",
        ),
        "output_categories": (
            "mutable-axiom map",
            "axiom-variant candidates",
            "rule-perturbation labels",
            "invariant-shift labels",
            "contradiction-surface notes",
            "degenerate-case labels",
            "boundary-case labels",
            "toy-model shift summaries",
            "proof-obstruction map",
            "consistency/instability candidates",
            "invalidated axiom variants",
            "next probe labels",
        ),
        "anti_flattening_rule": "Never collapse axiom-sensitive structure into a theorem-shaped conclusion too early; preserve variants, contradictions, degeneration, proof-obstruction maps, and invalidation history.",
        "prior_engine_name": "ALGORITHM_EMERGENCE_ENGINE",
        "next_engine_name": None,
        "relationship_to_cognitive_research_run_v1": {
            "role": "reporting_safety_envelope_only",
            "envelope_only": True,
            "not_engine_kernel": True,
            "not_runtime_authority": True,
            "not_proof_authority": True,
            "not_public_claim_authority": True,
        },
        "denied_authority": {
            "runtime_authority": False,
            "runtime_execution_authority": False,
            "tool_authority": False,
            "provider_authority": False,
            "search_authority": False,
            "persistence_authority": False,
            "public_export_authority": False,
            "proof_authority": False,
            "solution_authority": False,
            "benchmark_authority": False,
            "official_result_authority": False,
            "public_readiness_authority": False,
        },
        "public_claim_restrictions": {
            "proof_claims_blocked": True,
            "breakthrough_claims_blocked": True,
            "solved_claims_blocked": True,
            "certification_claims_blocked": True,
            "benchmark_claims_blocked": True,
            "public_readiness_claims_blocked": True,
            "official_result_claims_blocked": True,
            "open_problem_solution_claims_blocked": True,
        },
    },
}


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


def _has_text(value: Any) -> bool:
    return bool(_compact_text(value, default=""))


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def _stable_marker(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def allowed_cognitive_research_boundary_engine_names_v1() -> tuple[str, ...]:
    return _ENGINE_SEQUENCE_V1


def _boundary_from_name(engine_name: str) -> dict[str, Any]:
    if engine_name not in _ENGINE_META_V1:
        raise KeyError(engine_name)
    meta = copy.deepcopy(_ENGINE_META_V1[engine_name])
    index = meta["sequence_index"]
    prior = _ENGINE_SEQUENCE_V1[index - 2] if index > 1 else None
    next_engine = _ENGINE_SEQUENCE_V1[index] if index < len(_ENGINE_SEQUENCE_V1) else None
    meta.update(
        {
            "schema_version": SCHEMA_VERSION_V1,
            "engine_name": engine_name,
            "prior_engine_name": prior,
            "next_engine_name": next_engine,
            "metadata_only": True,
            "engine_relationship_graph": {
                "sequence_index": index,
                "prior_engine_name": prior,
                "current_engine_name": engine_name,
                "next_engine_name": next_engine,
            },
        }
    )
    return meta


def build_cognitive_research_engine_boundary_registry_v1() -> dict[str, dict[str, Any]]:
    return {name: _boundary_from_name(name) for name in _ENGINE_SEQUENCE_V1}


def get_cognitive_research_engine_boundary_v1(engine_name: str) -> dict[str, Any]:
    if engine_name not in _ENGINE_META_V1:
        raise KeyError(engine_name)
    return _boundary_from_name(engine_name)


def _validate_text_list(field_name: str, value: Any, violations: list[str], allow_empty: bool = False) -> list[str]:
    items = list(value) if isinstance(value, (list, tuple)) else []
    if not isinstance(value, (list, tuple)):
        violations.append(f"{field_name} must be a list or tuple")
        return items
    if not allow_empty and not items:
        violations.append(f"{field_name} must not be empty")
        return items
    for item in items:
        if not _has_text(item):
            violations.append(f"{field_name} contains empty text")
            break
    return items


def validate_cognitive_research_engine_boundary_v1(boundary: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(boundary, Mapping):
        return {"valid": False, "violation_count": 1, "violations": ["boundary must be a mapping"]}

    boundary_dict = dict(boundary)
    engine_name = _compact_text(boundary_dict.get("engine_name"))
    if engine_name not in _ENGINE_META_V1:
        violations.append(f"unknown engine name: {engine_name or '<missing>'}")
        return {"valid": False, "violation_count": len(violations), "violations": violations}

    required = {field: boundary_dict.get(field) for field in _REQUIRED_BOUNDARY_FIELDS_V1}
    for field, value in required.items():
        if field == "prior_engine_name" and value is None and engine_name == _ENGINE_SEQUENCE_V1[0]:
            continue
        if field == "next_engine_name" and value is None and engine_name == _ENGINE_SEQUENCE_V1[-1]:
            continue
        if field in {"sequence_index"}:
            if value is None:
                violations.append("sequence_index missing")
            continue
        if field in {"metadata_only"}:
            if value is not True:
                violations.append("metadata_only must be true")
            continue
        if field == "engine_relationship_graph":
            if not isinstance(value, Mapping):
                violations.append("engine_relationship_graph must be a mapping")
            continue
        if not _has_text(value) and field not in {"prior_engine_name", "next_engine_name"}:
            violations.append(f"missing required field: {field}")

    if boundary_dict.get("schema_version") != SCHEMA_VERSION_V1:
        violations.append("schema_version mismatch")

    sequence_index = boundary_dict.get("sequence_index")
    expected_index = _ENGINE_META_V1[engine_name]["sequence_index"]
    if sequence_index != expected_index:
        violations.append(f"sequence_index mismatch for {engine_name}")

    if not isinstance(boundary_dict.get("primitive_space"), (list, tuple)) or not boundary_dict.get("primitive_space"):
        violations.append("primitive_space must be non-empty")
    if not isinstance(boundary_dict.get("transformation_grammar"), (list, tuple)) or not boundary_dict.get("transformation_grammar"):
        violations.append("transformation_grammar must be non-empty")
    if not isinstance(boundary_dict.get("safe_input_categories"), (list, tuple)) or not boundary_dict.get("safe_input_categories"):
        violations.append("safe_input_categories must be non-empty")
    if not isinstance(boundary_dict.get("forbidden_input_categories"), (list, tuple)) or not boundary_dict.get("forbidden_input_categories"):
        violations.append("forbidden_input_categories must be non-empty")
    if not isinstance(boundary_dict.get("output_categories"), (list, tuple)) or not boundary_dict.get("output_categories"):
        violations.append("output_categories must be non-empty")
    if not _has_text(boundary_dict.get("anti_flattening_rule")):
        violations.append("anti_flattening_rule missing")

    denied = boundary_dict.get("denied_authority")
    if not isinstance(denied, Mapping):
        violations.append("denied_authority must be a mapping")
    else:
        for field in _REQUIRED_DENIED_AUTHORITY_FIELDS_V1:
            if field not in denied:
                violations.append(f"denied_authority missing field: {field}")
            elif denied[field] is not False:
                violations.append(f"denied_authority field must be false: {field}")

    public_claims = boundary_dict.get("public_claim_restrictions")
    if not isinstance(public_claims, Mapping):
        violations.append("public_claim_restrictions must be a mapping")
    else:
        for field in _REQUIRED_PUBLIC_CLAIM_RESTRICTION_FIELDS_V1:
            if field not in public_claims:
                violations.append(f"public_claim_restrictions missing field: {field}")
            elif public_claims[field] is not True:
                violations.append(f"public_claim_restrictions field must be true: {field}")

    run_relationship = boundary_dict.get("relationship_to_cognitive_research_run_v1")
    if not isinstance(run_relationship, Mapping):
        violations.append("relationship_to_cognitive_research_run_v1 must be a mapping")
    else:
        for field in _REQUIRED_RUN_RELATIONSHIP_FIELDS_V1:
            if field not in run_relationship:
                violations.append(f"relationship_to_cognitive_research_run_v1 missing field: {field}")
        if run_relationship.get("envelope_only") is not True:
            violations.append("CognitiveResearchRunV1 relationship must be envelope-only")
        if run_relationship.get("not_engine_kernel") is not True:
            violations.append("CognitiveResearchRunV1 must not be treated as engine kernel")
        if run_relationship.get("not_runtime_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have runtime authority")
        if run_relationship.get("not_proof_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have proof authority")
        if run_relationship.get("not_public_claim_authority") is not True:
            violations.append("CognitiveResearchRunV1 must not have public claim authority")

    if boundary_dict.get("metadata_only") is not True:
        violations.append("metadata_only must be true")

    for field in ("engine_identity", "uniqueness_statement", "cognitive_kernel", "observation_style", "mutation_probe_strategy", "novelty_detector", "contradiction_invalidation_loop", "compression_style", "anti_flattening_rule"):
        if not _has_text(boundary_dict.get(field)):
            violations.append(f"missing required text field: {field}")
        else:
            lowered = _compact_text(boundary_dict.get(field)).lower()
            if any(marker in lowered for marker in _FORBIDDEN_FLATTENING_MARKERS_V1):
                violations.append(f"flattening marker detected in {field}")
    for field in ("failure_modes",):
        if not isinstance(boundary_dict.get(field), (list, tuple)) or not boundary_dict.get(field):
            violations.append(f"{field} must be non-empty")

    sequence_graph = boundary_dict.get("engine_relationship_graph")
    if isinstance(sequence_graph, Mapping):
        if sequence_graph.get("sequence_index") != expected_index:
            violations.append(f"engine_relationship_graph sequence_index mismatch for {engine_name}")
        if sequence_graph.get("current_engine_name") != engine_name:
            violations.append(f"engine_relationship_graph current_engine_name mismatch for {engine_name}")
        if sequence_graph.get("prior_engine_name") != boundary_dict.get("prior_engine_name"):
            violations.append(f"engine_relationship_graph prior_engine_name mismatch for {engine_name}")
        if sequence_graph.get("next_engine_name") != boundary_dict.get("next_engine_name"):
            violations.append(f"engine_relationship_graph next_engine_name mismatch for {engine_name}")

    if boundary_dict.get("prior_engine_name") is not None and boundary_dict["prior_engine_name"] not in _ENGINE_META_V1:
        violations.append("prior_engine_name invalid")
    if boundary_dict.get("next_engine_name") is not None and boundary_dict["next_engine_name"] not in _ENGINE_META_V1:
        violations.append("next_engine_name invalid")

    return {
        "valid": not violations,
        "violation_count": len(violations),
        "violations": violations,
        "engine_name": engine_name,
        "summary": summarize_cognitive_research_engine_boundary_v1(boundary_dict),
    }


def validate_cognitive_research_engine_boundary_registry_v1(registry: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(registry, Mapping):
        return {"valid": False, "violation_count": 1, "violations": ["registry must be a mapping"]}

    keys = set(registry.keys())
    expected = set(_ENGINE_SEQUENCE_V1)
    missing = expected - keys
    extra = keys - expected
    if missing:
        violations.append(f"missing engine names: {', '.join(sorted(missing))}")
    if extra:
        violations.append(f"unexpected engine names: {', '.join(sorted(extra))}")

    ordered = list(registry.keys())
    if ordered != list(_ENGINE_SEQUENCE_V1):
        violations.append("relationship graph order is incorrect")

    for name in _ENGINE_SEQUENCE_V1:
        entry = registry.get(name)
        result = validate_cognitive_research_engine_boundary_v1(entry)
        if not result["valid"]:
            violations.append(f"{name}: {', '.join(result['violations'])}")

    return {
        "valid": not violations,
        "violation_count": len(violations),
        "violations": violations,
        "engine_count": len(registry) if isinstance(registry, Mapping) else 0,
    }


def summarize_cognitive_research_engine_boundary_v1(boundary: Any) -> str:
    if not isinstance(boundary, Mapping):
        return "invalid boundary"
    engine_name = _compact_text(boundary.get("engine_name"), default="unknown")
    engine_identity = _compact_text(boundary.get("engine_identity"), default="")
    primitives = boundary.get("primitive_space", [])
    outputs = boundary.get("output_categories", [])
    safe_inputs = boundary.get("safe_input_categories", [])
    claims = boundary.get("public_claim_restrictions", {})
    summary = (
        f"{engine_name}: {engine_identity} | primitives={len(primitives)} | safe={len(safe_inputs)} | outputs={len(outputs)}"
    )
    if isinstance(claims, Mapping):
        blocked = sum(1 for value in claims.values() if value is True)
        summary += f" | claim_blocks={blocked}"
    return summary[:800]


def summarize_cognitive_research_engine_boundary_registry_v1(registry: Any) -> str:
    if not isinstance(registry, Mapping):
        return "invalid registry"
    parts = []
    for name in _ENGINE_SEQUENCE_V1:
        entry = registry.get(name)
        if not isinstance(entry, Mapping):
            parts.append(f"{name}=invalid")
            continue
        parts.append(f"{name}@{entry.get('sequence_index')}")
    return "sequence=" + " -> ".join(parts)


def to_cognitive_research_engine_boundary_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def build_initial_cognitive_research_engine_boundary_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    registry = build_cognitive_research_engine_boundary_registry_v1()
    for name in _ENGINE_SEQUENCE_V1:
        boundary = registry[name]
        examples.append(
            {
                "example_id": _stable_marker("synthetic_boundary_example", {"engine_name": name, "schema_version": SCHEMA_VERSION_V1}),
                "engine_name": name,
                "sequence_index": boundary["sequence_index"],
                "input_metadata_refs": [
                    f"synthetic:cognitive-research-boundary:{name.lower()}:terrain-map",
                    f"synthetic:cognitive-research-boundary:{name.lower()}:interpretation-layer",
                ],
                "boundary_summary": summarize_cognitive_research_engine_boundary_v1(boundary),
                "safe_input_categories": list(boundary["safe_input_categories"]),
                "forbidden_input_categories": list(boundary["forbidden_input_categories"]),
                "output_categories": list(boundary["output_categories"]),
                "denied_authority": to_cognitive_research_engine_boundary_json_safe_v1(boundary["denied_authority"]),
                "public_claim_restrictions": to_cognitive_research_engine_boundary_json_safe_v1(boundary["public_claim_restrictions"]),
                "metadata_only": True,
                "relationship_graph": to_cognitive_research_engine_boundary_json_safe_v1(boundary["engine_relationship_graph"]),
            }
        )
    return examples


def source_has_forbidden_imports_v1(source_text: str) -> bool:
    lowered = source_text.lower()
    return any(marker in lowered for marker in _FORBIDDEN_IMPORT_MARKERS_V1)
