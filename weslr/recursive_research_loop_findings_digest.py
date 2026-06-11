"""WESLR Recursive Research Loop Findings Digest V1.

Deterministic, metadata-only translation of recursive research loop scenario-set
output into an internal human-readable findings digest. This layer is read-only,
non-public, non-runtime, and does not replace the scenario-set runner.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from weslr.recursive_research_loop_scenario_set import (
    run_recursive_research_loop_scenario_set_v1,
    summarize_recursive_research_loop_scenario_set_v1,
    to_recursive_research_loop_scenario_set_json_safe_v1,
)

SCHEMA_VERSION_V1 = "recursive_research_loop_findings_digest_v1"
FINDINGS_DIGEST_ID_PREFIX_V1 = "recursive_research_loop_findings_digest_v1"
SCENARIO_FAMILIES_V1 = (
    "ambiguous_pattern_signal",
    "contradictory_signal",
    "weak_signal_noise",
    "cross_domain_resonance_signal",
    "pressure_test_candidate",
    "calibration_needed_signal",
    "blocked_public_claim_signal",
    "archive_low_value_signal",
)
FORBIDDEN_INTERPRETATIONS_V1 = (
    "discovery",
    "proof",
    "breakthrough",
    "scientific result",
    "validated mechanism",
    "AGI evidence",
    "intelligence proof",
    "sentience",
    "consciousness",
    "public claim",
)
CLAIM_TEXT_MARKERS_V1 = (
    "discovery",
    "proof",
    "breakthrough",
    "scientific result",
    "validated mechanism",
    "agi evidence",
    "intelligence proof",
    "sentience",
    "consciousness",
    "public claim",
)
PRIVATE_TEXT_MARKERS_V1 = (
    "hidden prompt",
    "system prompt",
    "private text",
    "secret",
    "api key",
    "provider call",
    "tool execution",
    "retrieval",
    "live ingestion",
    ".weslr",
    "final answer authority",
    "final-answer",
    "final answer",
)
ALLOWED_PUBLIC_CLAIM_STATUSES_V1 = (
    "internal_candidate_only",
    "internal_reading_only",
    "not_public_ready",
)
_REQUIRED_SAFE_METADATA_FLAGS_V1 = (
    "safe",
    "metadata_only",
    "json_safe",
    "non_public",
    "no_runtime_wiring",
    "no_provider_calls",
    "no_tool_execution",
    "no_retrieval",
    "no_persistence",
    "no_memory_mutation",
    "no_project_mutation",
    "no_behavior_promotion",
    "no_public_claim",
    "no_final_answer_authority",
    "no_live_ingestion",
    "no_weslr_io",
    "no_weslr_runtime",
    "no_hidden_prompt_leak",
    "no_secrets",
)


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    merged.update({key: value for key, value in overrides.items() if value is not None})
    return merged


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _stable_digest(payload: Any) -> str:
    return sha256(repr(payload).encode("utf-8")).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"[redacted:{type(value).__name__}]"
    if callable(value):
        return f"[redacted:{type(value).__name__}]"
    if isinstance(value, str):
        return value
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    return f"[redacted:{type(value).__name__}]"


def _first_non_json_safe_path(value: Any, path: str = "result") -> str | None:
    if value is None or isinstance(value, (bool, int, float, str)):
        return None
    if isinstance(value, (bytes, bytearray, memoryview)):
        return path
    if isinstance(value, (tuple, set, frozenset)):
        return path
    if callable(value):
        return path
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                return f"{path}.[non-string-key:{type(key).__name__}]"
            issue = _first_non_json_safe_path(item, f"{path}.{key}")
            if issue is not None:
                return issue
        return None
    if isinstance(value, list):
        for index, item in enumerate(value):
            issue = _first_non_json_safe_path(item, f"{path}[{index}]")
            if issue is not None:
                return issue
        return None
    return path


def _contains_text_markers(value: Any, markers: tuple[str, ...]) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_text_markers(item, markers) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_text_markers(item, markers) for item in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in markers)


def _default_safe_metadata() -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "no_runtime_wiring": True,
        "no_provider_calls": True,
        "no_tool_execution": True,
        "no_retrieval": True,
        "no_persistence": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_behavior_promotion": True,
        "no_public_claim": True,
        "no_final_answer_authority": True,
        "no_live_ingestion": True,
        "no_weslr_io": True,
        "no_weslr_runtime": True,
        "no_hidden_prompt_leak": True,
        "no_secrets": True,
        "digest_family": "recursive_research_loop_findings_digest",
    }


def _default_authority_status() -> dict[str, Any]:
    return {
        "runtime_action_authorized": False,
        "storage_write_authorized": False,
        "memory_mutation_authorized": False,
        "project_mutation_authorized": False,
        "behavior_promotion_authorized": False,
        "public_claim_authorized": False,
        "final_answer_authority": False,
        "provider_model_call_authority": False,
        "retrieval_tool_authority": False,
        "all_authority_flags_false": True,
    }


def _normalize_source_result(payload: Mapping[str, Any]) -> dict[str, Any]:
    source_result = payload.get("scenario_set_result")
    if not isinstance(source_result, Mapping):
        source_result = run_recursive_research_loop_scenario_set_v1(payload.get("scenario_set_payload") if isinstance(payload.get("scenario_set_payload"), Mapping) else None)
    return to_recursive_research_loop_scenario_set_json_safe_v1(source_result)


def _scenario_families_from_source(source_result: Mapping[str, Any]) -> list[str]:
    scenarios = source_result.get("scenarios") if isinstance(source_result.get("scenarios"), list) else []
    families: list[str] = []
    for item in scenarios:
        if isinstance(item, Mapping):
            family = _compact_text(item.get("scenario_family"))
            if family:
                families.append(family)
    if families:
        return families
    scenario_results = source_result.get("scenario_results") if isinstance(source_result.get("scenario_results"), list) else []
    for item in scenario_results:
        if isinstance(item, Mapping):
            family = _compact_text(item.get("scenario_family"))
            if family:
                families.append(family)
    return families


def _family_level_notes(source_result: Mapping[str, Any]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    scenario_results = source_result.get("scenario_results") if isinstance(source_result.get("scenario_results"), list) else []
    for item in scenario_results:
        if not isinstance(item, Mapping):
            continue
        notes.append(
            {
                "scenario_family": _compact_text(item.get("scenario_family")),
                "scenario_title": _compact_text(item.get("scenario_title")),
                "completion_status": _compact_text(item.get("completion_status")),
                "expected_next_step_family": _compact_text(item.get("expected_next_step_family")),
                "observed_next_internal_step": _compact_text(item.get("recommended_next_internal_step")),
                "stage_summary": _compact_text(item.get("stage_summary")),
                "safety_summary": _compact_text(item.get("safety_summary")),
                "gap_summary": _compact_text(item.get("gap_summary")),
            }
        )
    return notes


def _candidate_insights(source_result: Mapping[str, Any]) -> list[str]:
    return [
        "candidate insight: all 8 scenario families completed and validated without stage failures.",
        "candidate insight: the run is stable and conservative, with authority staying denied across the set.",
        "candidate pattern: the next-step layer collapses to `calibrate` for every family, which keeps the output safe but broad.",
        "candidate hypothesis: family-level refinement could make the next-step layer more differentiated without changing the safety boundary.",
    ]


def _candidate_pressure_directions() -> list[str]:
    return [
        "candidate pressure direction: separate families that expect `probe`, `pressure_test`, `operator_review`, or `archive` from families that naturally land on `calibrate`.",
        "candidate pressure direction: test whether small family-specific adjustments reduce the collapse without opening any authority flags.",
    ]


def _candidate_calibration_directions() -> list[str]:
    return [
        "candidate calibration need: keep the conservative default, but split the next-step heuristic by scenario family.",
        "candidate calibration need: preserve metadata-only behavior while making the family-level reading less generic.",
    ]


def _cross_family_patterns() -> list[str]:
    return [
        "All 8 scenario families completed and validated.",
        "No stage failures were observed in the reviewed output.",
        "Next-step distribution collapsed to `calibrate: 8`.",
        "Authority stayed denied, so the digest remains internal and non-public.",
    ]


def _current_limitations() -> list[str]:
    return [
        "All 8 scenario families currently converge to `calibrate`; this shows safe conservative behavior, but also a next-step differentiation limitation.",
        "This digest is a metadata translation layer only, not runtime behavior and not a validated runtime mechanism.",
        "The output is useful as a baseline, but it is not yet richly differentiated enough for family-specific conclusions.",
    ]


def _operator_reading_summary(source_result: Mapping[str, Any]) -> str:
    summary = _compact_text(source_result.get("summary_text"), "")
    if summary:
        return (
            "Read as a safe internal baseline: the scenario set completed cleanly, all authority stayed denied, "
            "and the decision layer still collapses to `calibrate` across every family. "
            f"Source summary: {summary}"
        )
    return (
        "Read as a safe internal baseline: the scenario set completed cleanly, all authority stayed denied, "
        "and the decision layer still collapses to `calibrate` across every family."
    )


def _digest_id(source_run_id: str, source_commit: str, scenario_count: int, next_step_distribution: Mapping[str, Any]) -> str:
    payload = {
        "source_run_id": source_run_id,
        "source_commit": source_commit,
        "scenario_count": scenario_count,
        "next_step_distribution": dict(sorted((str(k), int(v)) for k, v in next_step_distribution.items())),
    }
    return f"{FINDINGS_DIGEST_ID_PREFIX_V1}:{_stable_digest(payload)[:16]}"


def build_recursive_research_loop_findings_digest_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    source_result = _normalize_source_result(data)
    scenario_results = source_result.get("scenario_results") if isinstance(source_result.get("scenario_results"), list) else []
    scenario_families = _scenario_families_from_source(source_result)
    scenario_count = int(source_result.get("total_scenarios") or len(scenario_results) or len(scenario_families))
    completed_count = int(source_result.get("completed_scenarios") or sum(1 for item in scenario_results if isinstance(item, Mapping) and _compact_text(item.get("completion_status")) == "completed"))
    validated_count = int(
        data.get("validated_count")
        if isinstance(data.get("validated_count"), int)
        else sum(1 for item in scenario_results if isinstance(item, Mapping) and isinstance(item.get("dry_run_validation"), Mapping) and bool(item["dry_run_validation"].get("valid")))
    )
    stage_failure_distribution = source_result.get("stage_failure_distribution") if isinstance(source_result.get("stage_failure_distribution"), Mapping) else {}
    stage_failure_count = sum(int(value) for value in stage_failure_distribution.values() if isinstance(value, int))
    next_step_distribution = source_result.get("next_step_distribution") if isinstance(source_result.get("next_step_distribution"), Mapping) else {}
    source_run_id = _compact_text(data.get("source_run_id") or source_result.get("scenario_set_id") or "recursive_research_loop_scenario_set_v1")
    source_commit = _compact_text(data.get("source_commit") or "unknown-source-commit")
    authority_status = _json_safe(data.get("authority_status") or _default_authority_status())
    safe_metadata = _json_safe(data.get("safe_metadata") or _default_safe_metadata())
    digest = {
        "schema_version": SCHEMA_VERSION_V1,
        "digest_id": _compact_text(data.get("digest_id") or _digest_id(source_run_id, source_commit, scenario_count, next_step_distribution)),
        "source_run_id": source_run_id,
        "source_commit": source_commit,
        "scenario_families": list(scenario_families),
        "scenario_count": scenario_count,
        "completed_count": completed_count,
        "validated_count": validated_count,
        "stage_failure_count": stage_failure_count,
        "next_step_distribution": dict(sorted((str(key), int(value)) for key, value in next_step_distribution.items())),
        "candidate_insights": _candidate_insights(source_result),
        "candidate_pressure_directions": _candidate_pressure_directions(),
        "candidate_calibration_directions": _candidate_calibration_directions(),
        "family_level_notes": _family_level_notes(source_result),
        "cross_family_patterns": _cross_family_patterns(),
        "current_limitations": _current_limitations(),
        "operator_reading_summary": _operator_reading_summary(source_result),
        "recommended_next_internal_step": _compact_text(data.get("recommended_next_internal_step") or "review_family_specific_next_step_differentiation"),
        "forbidden_interpretations": list(data.get("forbidden_interpretations") or FORBIDDEN_INTERPRETATIONS_V1),
        "public_claim_status": _compact_text(data.get("public_claim_status") or "internal_candidate_only"),
        "authority_status": authority_status,
        "safe_metadata": safe_metadata,
    }
    return _json_safe(digest)


def validate_recursive_research_loop_findings_digest_v1(digest: Any) -> dict[str, Any]:
    raw = digest if isinstance(digest, Mapping) else {}
    blocked_labels: list[str] = []

    if not isinstance(digest, Mapping):
        blocked_labels.append("invalid_digest_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "summary_text": "Blocked recursive research loop findings digest: invalid digest type.",
        }

    if _compact_text(raw.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")
    if not _compact_text(raw.get("digest_id")):
        blocked_labels.append("missing_digest_id")
    if not _compact_text(raw.get("source_run_id")):
        blocked_labels.append("missing_source_run_id")
    if not _compact_text(raw.get("source_commit")):
        blocked_labels.append("missing_source_commit")

    scenario_families = raw.get("scenario_families")
    if not isinstance(scenario_families, list) or not scenario_families:
        blocked_labels.append("missing_scenario_families")
    elif len(scenario_families) != len(SCENARIO_FAMILIES_V1) or set(map(_compact_text, scenario_families)) != set(SCENARIO_FAMILIES_V1):
        blocked_labels.append("unexpected_scenario_families")

    for field in ("scenario_count", "completed_count", "validated_count", "stage_failure_count"):
        if not isinstance(raw.get(field), int):
            blocked_labels.append(f"invalid_{field}")

    next_step_distribution = raw.get("next_step_distribution")
    if not isinstance(next_step_distribution, Mapping) or not next_step_distribution:
        blocked_labels.append("missing_next_step_distribution")
    elif dict(sorted((str(key), int(value)) for key, value in next_step_distribution.items())) != {"calibrate": 8}:
        blocked_labels.append("unexpected_next_step_distribution")

    for field in ("candidate_insights", "candidate_pressure_directions", "candidate_calibration_directions", "family_level_notes", "cross_family_patterns", "current_limitations", "forbidden_interpretations"):
        value = raw.get(field)
        if not isinstance(value, list) or not value:
            blocked_labels.append(f"missing_{field}")

    if not _compact_text(raw.get("operator_reading_summary")):
        blocked_labels.append("missing_operator_reading_summary")
    if not _compact_text(raw.get("recommended_next_internal_step")):
        blocked_labels.append("missing_recommended_next_internal_step")

    public_claim_status = _compact_text(raw.get("public_claim_status"))
    if not public_claim_status:
        blocked_labels.append("missing_public_claim_status")
    elif public_claim_status not in ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        blocked_labels.append("invalid_public_claim_status")

    authority_status = raw.get("authority_status")
    if not isinstance(authority_status, Mapping):
        blocked_labels.append("missing_authority_status")
    else:
        for key, value in authority_status.items():
            if key == "all_authority_flags_false":
                continue
            if bool(value):
                blocked_labels.append(f"unsafe_{key}")
        if authority_status.get("all_authority_flags_false") is not True:
            blocked_labels.append("unsafe_authority_status")

    safe_metadata = raw.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        blocked_labels.append("missing_safe_metadata")
    else:
        for field in _REQUIRED_SAFE_METADATA_FLAGS_V1:
            if safe_metadata.get(field) is not True:
                blocked_labels.append(f"unsafe_safe_metadata_{field}")
        if _contains_text_markers(safe_metadata, CLAIM_TEXT_MARKERS_V1):
            blocked_labels.append("forbidden_claim_language")
        if _contains_text_markers(safe_metadata, PRIVATE_TEXT_MARKERS_V1):
            blocked_labels.append("forbidden_private_text")

    if not isinstance(raw.get("current_limitations"), list) or not raw.get("current_limitations"):
        blocked_labels.append("missing_current_limitations")
    elif not any("All 8 scenario families currently converge to `calibrate`" in _compact_text(item) for item in raw.get("current_limitations", [])):
        blocked_labels.append("missing_calibrate_limitation")

    forbidden_interpretations = raw.get("forbidden_interpretations") if isinstance(raw.get("forbidden_interpretations"), list) else []
    if list(map(_compact_text, forbidden_interpretations)) != list(FORBIDDEN_INTERPRETATIONS_V1):
        blocked_labels.append("missing_forbidden_interpretations")

    if _contains_text_markers(raw.get("candidate_insights"), CLAIM_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_text_markers(raw.get("candidate_pressure_directions"), CLAIM_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_text_markers(raw.get("candidate_calibration_directions"), CLAIM_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_text_markers(raw.get("family_level_notes"), CLAIM_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_text_markers(raw.get("cross_family_patterns"), CLAIM_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_text_markers(raw.get("operator_reading_summary"), CLAIM_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_text_markers(raw.get("current_limitations"), CLAIM_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_text_markers(raw.get("candidate_insights"), PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_text_markers(raw.get("candidate_pressure_directions"), PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_text_markers(raw.get("candidate_calibration_directions"), PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_text_markers(raw.get("family_level_notes"), PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_text_markers(raw.get("cross_family_patterns"), PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_text_markers(raw.get("operator_reading_summary"), PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_text_markers(raw.get("current_limitations"), PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")

    json_issue = _first_non_json_safe_path(raw)
    if json_issue is not None:
        blocked_labels.append("non_json_safe_result_structure")

    valid = not blocked_labels
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "summary_text": summarize_recursive_research_loop_findings_digest_v1(raw),
        "digest_id": _compact_text(raw.get("digest_id")),
        "source_run_id": _compact_text(raw.get("source_run_id")),
    }


def summarize_recursive_research_loop_findings_digest_v1(digest: Any) -> str:
    raw = digest if isinstance(digest, Mapping) else {}
    digest_id = _compact_text(raw.get("digest_id"), "digest:unknown")
    scenario_count = raw.get("scenario_count") if isinstance(raw.get("scenario_count"), int) else 0
    completed = raw.get("completed_count") if isinstance(raw.get("completed_count"), int) else 0
    validated = raw.get("validated_count") if isinstance(raw.get("validated_count"), int) else 0
    stage_failures = raw.get("stage_failure_count") if isinstance(raw.get("stage_failure_count"), int) else 0
    next_steps = raw.get("next_step_distribution") if isinstance(raw.get("next_step_distribution"), Mapping) else {}
    next_bits = ", ".join(f"{key}:{value}" for key, value in sorted(next_steps.items(), key=lambda item: item[0])) or "none"
    limitation = "All 8 scenario families currently converge to `calibrate`; this shows safe conservative behavior, but also a next-step differentiation limitation."
    return (
        f"Findings digest {digest_id}: scenarios={scenario_count}; completed={completed}; validated={validated}; "
        f"stage_failures={stage_failures}; next_step_distribution={next_bits}; limitation={limitation}"
    )


def render_recursive_research_loop_findings_digest_markdown_v1(digest: Mapping[str, Any]) -> str:
    safe = to_recursive_research_loop_findings_digest_json_safe_v1(digest)
    lines = [
        "# WESLR Recursive Research Loop Findings Digest",
        "",
        "## What WESLR Ran",
        f"- Source run: `{safe.get('source_run_id', 'unknown')}`",
        f"- Source commit: `{safe.get('source_commit', 'unknown')}`",
        f"- Scenario families: {len(safe.get('scenario_families', []))}",
        f"- Scenario count: {safe.get('scenario_count', 0)}",
        "",
        "## What Completed",
        f"- Completed: {safe.get('completed_count', 0)}/{safe.get('scenario_count', 0)}",
        f"- Validated: {safe.get('validated_count', 0)}/{safe.get('scenario_count', 0)}",
        f"- Stage failures: {safe.get('stage_failure_count', 0)}",
        f"- Next-step distribution: {', '.join(f'{key}: {value}' for key, value in sorted((safe.get('next_step_distribution') or {}).items())) or 'none'}",
        "",
        "## What WESLR Appears To Notice",
        "- The output is stable, metadata-only, and non-public-safe.",
        "- Authority stays denied across the run.",
        "- The decision layer still collapses to a single conservative next step across all families.",
        "",
        "## Candidate Insights",
    ]
    for item in safe.get("candidate_insights", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Candidate Pressure Directions",
    ])
    for item in safe.get("candidate_pressure_directions", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Candidate Calibration Directions",
    ])
    for item in safe.get("candidate_calibration_directions", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Current Decision-Layer Limitation",
    ])
    for item in safe.get("current_limitations", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## What This Is Not",
    ])
    for item in safe.get("forbidden_interpretations", []):
        lines.append(f"- not a {item} claim")
    lines.extend([
        "",
        "## What To Do Next",
        f"- Recommended next internal step: `{safe.get('recommended_next_internal_step', 'review_family_specific_next_step_differentiation')}`",
        "- Use this digest as a readable internal baseline, not as a public claim or a validated mechanism.",
        "- If family-level differentiation is desired, review the next-step heuristic before changing it.",
    ])
    return "\n".join(lines) + "\n"


def to_recursive_research_loop_findings_digest_json_safe_v1(digest: Any) -> dict[str, Any]:
    return _json_safe(digest if isinstance(digest, Mapping) else {})


def build_initial_recursive_research_loop_findings_digest_examples_v1() -> tuple[dict[str, Any], ...]:
    source_result = run_recursive_research_loop_scenario_set_v1()
    base = build_recursive_research_loop_findings_digest_v1(
        {
            "scenario_set_result": source_result,
            "source_run_id": _compact_text(source_result.get("scenario_set_id"), "recursive_research_loop_scenario_set_v1"),
            "source_commit": "f118a6990d992197c8313f0a7562e6334dd93880",
        }
    )
    example_two = build_recursive_research_loop_findings_digest_v1(
        {
            "scenario_set_result": source_result,
            "source_run_id": "recursive_research_loop_scenario_set_v1:example",
            "source_commit": "f118a6990d992197c8313f0a7562e6334dd93880",
        }
    )
    return (base, example_two)


__all__ = (
    "SCHEMA_VERSION_V1",
    "build_initial_recursive_research_loop_findings_digest_examples_v1",
    "build_recursive_research_loop_findings_digest_v1",
    "render_recursive_research_loop_findings_digest_markdown_v1",
    "summarize_recursive_research_loop_findings_digest_v1",
    "to_recursive_research_loop_findings_digest_json_safe_v1",
    "validate_recursive_research_loop_findings_digest_v1",
)
