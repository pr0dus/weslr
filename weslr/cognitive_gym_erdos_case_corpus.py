"""WESLR Cognitive Gym Erdős case-corpus metadata helpers V1.

Helper-only, metadata-only, deterministic, in-memory helpers for representing
internal Erdős / open mathematical structure case-corpus entries. This module
does not create a corpus file, corpus data, runner, scoring, judges, challenge
execution, runtime behavior, result artifacts, proof claims, final answers,
user-facing output, official claims, provider/model/search/advisor calls,
.weslr IO, or authority grants.
"""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Mapping

from weslr.cognitive_gym_run_protocol import (
    REQUIRED_DENIED_AUTHORITY_FIELDS,
    SUPPORTED_COGNITIVE_GYM_CHALLENGE_TRACKS,
)

TRACK_LABEL_V1 = "ERDŐS / open mathematical structure"
CORPUS_SCHEMA_VERSION_V1 = "cognitive_gym_erdos_case_corpus_entry_schema_v1"
NEXT_LANE_V1 = "REVIEW_COGNITIVE_GYM_ERDOS_CASE_CORPUS_HELPERS_IMPLEMENTATION_V1"

TIER_LABELS_V1 = {
    0: "Tier 0 — prerequisite reconstruction",
    1: "Tier 1 — solved Erdős-style examples",
    2: "Tier 2 — bounded/toy variants",
    3: "Tier 3 — partially solved or known frontier variants as metadata only",
    4: "Tier 4 — open-problem boundary maps",
    5: "Tier 5 — counterexample/falsification planning",
    6: "Tier 6 — subproblem generation",
    7: "Tier 7 — proof-audit discipline",
}

CASE_CORPUS_ENTRY_FIELDS_V1 = (
    "corpus_schema_version",
    "case_id",
    "track_label",
    "tier",
    "tier_label",
    "case_kind",
    "source_safety_label",
    "problem_statement_summary",
    "definitions_summary",
    "known_results_summary",
    "unknowns",
    "assumptions",
    "hypotheses",
    "bounded_variants",
    "toy_cases",
    "counterexample_search_plan",
    "falsification_labels",
    "proof_gap_labels",
    "evidence_literature_need_labels",
    "safe_next_observations",
    "uncertainty_labels",
    "compressed_lesson",
    "denied_authority_fields",
    "validation_status",
    "blocked",
    "blocked_reason_labels",
    "visible_risks",
    "followups",
    "next_lane",
)

_LIST_FIELDS = (
    "unknowns",
    "assumptions",
    "hypotheses",
    "bounded_variants",
    "toy_cases",
    "counterexample_search_plan",
    "falsification_labels",
    "proof_gap_labels",
    "evidence_literature_need_labels",
    "safe_next_observations",
    "uncertainty_labels",
    "blocked_reason_labels",
    "visible_risks",
    "followups",
)

_REQUIRED_NONEMPTY_STRING_FIELDS = (
    "corpus_schema_version",
    "case_id",
    "track_label",
    "tier_label",
    "case_kind",
    "source_safety_label",
    "problem_statement_summary",
)

_TEXT_FIELDS = (
    "corpus_schema_version",
    "case_id",
    "track_label",
    "tier_label",
    "case_kind",
    "source_safety_label",
    "problem_statement_summary",
    "definitions_summary",
    "known_results_summary",
    "compressed_lesson",
    "validation_status",
    "next_lane",
)

_FORBIDDEN_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "hidden_prompt",
    "protected",
    "answer_key",
    "private",
    "provider",
    "model",
    "search",
    "advisor",
    "runtime",
    "output",
    "user_facing",
    "reply",
    "final_answer",
    "proof_claim",
    "solution_claim",
    "official_score",
    "score",
    "judge",
    "benchmark",
    "iq",
    "turing",
    "certification",
    "product_readiness",
    "corpus_file",
    "runner",
    "result_artifact",
    "dot_weslr",
    ".weslr",
    "authority_granted",
)

_TEXT_MARKERS = {
    "protected_benchmark_item_blocked": (
        "protected benchmark item",
        "protected benchmark",
        "hidden benchmark item",
    ),
    "hidden_prompt_indicator_blocked": (
        "hidden prompt:",
        "hidden_prompt:",
        "system prompt:",
        "developer prompt:",
        "hidden test:",
    ),
    "answer_key_indicator_blocked": (
        "answer key:",
        "answer-key",
        "hidden answer",
        "official answer:",
    ),
    "copied_private_benchmark_content_blocked": (
        "copied private benchmark",
        "private benchmark item",
        "raw private benchmark",
    ),
    "private_user_data_blocked": (
        "private user data",
        "personal data:",
        "private content:",
        "confidential:",
        "secret:",
        "api key",
        "password:",
    ),
    "raw_copyrighted_long_excerpt_blocked": (
        "raw copyrighted long excerpt",
        "copyrighted long excerpt",
        "verbatim copyrighted excerpt",
    ),
    "proprietary_problem_set_indicator_blocked": (
        "proprietary problem set",
        "licensed problem set",
        "non-public problem set",
    ),
    "official_score_claim_blocked": (
        "official score:",
        "official-score",
        "score: 100",
        "scored by judge",
    ),
    "proof_open_problem_solution_claim_blocked": (
        "proof of the open problem",
        "open-problem solution",
        "open problem solution",
        "erdős solved",
        "erdos solved",
        "solved the open problem",
        "we prove the open problem",
    ),
    "solved_without_external_verification_claim_blocked": (
        "solved without external verification",
        "solved, unverified",
        "solution verified by me only",
        "claim solved without verification",
    ),
    "final_answer_user_facing_reply_output_blocked": (
        "final answer:",
        "final-answer prose",
        "user-facing output:",
        "reply output:",
        "sendable reply text:",
        "actual reply body:",
    ),
    "provider_model_search_advisor_output_blocked": (
        "provider output:",
        "provider response:",
        "model output:",
        "llm output:",
        "search output:",
        "search result:",
        "advisor output:",
        "advisor response:",
    ),
    "dot_weslr_io_indicator_blocked": (
        ".weslr read",
        ".weslr write",
        "dot_weslr_read",
        "dot_weslr_write",
    ),
    "runtime_output_indicator_blocked": (
        "runtime output:",
        "runtime trace:",
        "live runtime output:",
        "execution output:",
        "challenge execution output:",
    ),
    "judges_scores_indicator_blocked": (
        "judge decision:",
        "judges created",
        "scores created",
        "score created",
    ),
    "official_benchmark_turing_iq_certification_product_readiness_claim_blocked": (
        "official benchmark",
        "official iq",
        "passed the turing test",
        "certification claim",
        "certified product-ready",
        "product readiness",
    ),
    "authority_grant_indicator_blocked": (
        "authority granted",
        "authority_granted=true",
        "runtime_authority_granted=true",
    ),
}

_SAFE_LITERAL_STRINGS = {
    TRACK_LABEL_V1,
    CORPUS_SCHEMA_VERSION_V1,
    NEXT_LANE_V1,
    "validation_pass_metadata_quality_only",
    "blocked_invalid_or_unsafe_metadata_labels_only",
    "metadata_only_no_runtime_no_output_no_authority",
    "internal_review_material_only",
    "safe_synthetic_or_public_domain_summary_metadata_only",
    "case_metadata_only",
    "no_actual_corpus_file",
    "no_corpus_data",
    "no_case_execution",
    "no_runner_creation",
    "no_scoring_or_judges",
    "no_result_artifact_creation",
    "no_proof_or_open_problem_solution_claim",
    "no_final_answer_or_user_facing_output",
    "no_official_claims",
    "no_authority_grant",
    "not_proof_claim",
    "metadata_label_only",
    *CASE_CORPUS_ENTRY_FIELDS_V1,
    *TIER_LABELS_V1.values(),
    *REQUIRED_DENIED_AUTHORITY_FIELDS,
    *SUPPORTED_COGNITIVE_GYM_CHALLENGE_TRACKS,
}


def _as_list(value: Any) -> list[Any]:
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


def _safe_label(value: Any) -> str:
    return str(value).replace("`", "").replace("\n", " ")[:180]


def _safe_labels(value: Any) -> list[str]:
    labels: list[str] = []
    for item in _as_list(value):
        _append_unique(labels, _safe_label(item))
    return labels


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
            key_s = str(key)
            child = f"{path}.{key_s}" if path else key_s
            yield child, item
            yield from _walk(item, child)
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            child = f"{path}[{index}]"
            yield child, item
            yield from _walk(item, child)


def _is_safe_denied_authority_path(path: str, value: Any) -> bool:
    parts = path.split(".")
    return (
        len(parts) >= 2
        and parts[-2] == "denied_authority_fields"
        and parts[-1] in REQUIRED_DENIED_AUTHORITY_FIELDS
        and value is False
    )


def _detect_unsafe_content(value: Any) -> list[str]:
    reasons: list[str] = []
    if not _is_json_safe(value):
        _append_unique(reasons, "non_json_safe_input_blocked")
    allowed_field_names = {field.lower() for field in CASE_CORPUS_ENTRY_FIELDS_V1} | {
        field.lower() for field in REQUIRED_DENIED_AUTHORITY_FIELDS
    }
    for path, item in _walk(value):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        if _is_safe_denied_authority_path(path, item):
            continue
        if key not in allowed_field_names:
            for fragment in _FORBIDDEN_KEY_FRAGMENTS:
                if fragment in key:
                    _append_unique(reasons, f"unsupported_indicator_blocked:{fragment}")
        if isinstance(item, str):
            if item in _SAFE_LITERAL_STRINGS or item in REQUIRED_DENIED_AUTHORITY_FIELDS:
                continue
            lowered = item.lower()
            for label, markers in _TEXT_MARKERS.items():
                if any(marker in lowered for marker in markers):
                    _append_unique(reasons, label)
    return reasons


def _default_denied_authority_fields() -> dict[str, bool]:
    return {field: False for field in REQUIRED_DENIED_AUTHORITY_FIELDS}


def _validation_status(blocked: bool) -> str:
    return "blocked_invalid_or_unsafe_metadata_labels_only" if blocked else "validation_pass_metadata_quality_only"


def _normalized_tier(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def _base_entry(metadata: Mapping[str, Any]) -> dict[str, Any]:
    tier = _normalized_tier(metadata.get("tier"))
    denied = metadata.get("denied_authority_fields")
    if not isinstance(denied, Mapping):
        denied = _default_denied_authority_fields()
    else:
        denied = {**_default_denied_authority_fields(), **dict(denied)}

    entry = {
        "corpus_schema_version": metadata.get("corpus_schema_version", CORPUS_SCHEMA_VERSION_V1),
        "case_id": _safe_label(metadata.get("case_id", "")),
        "track_label": metadata.get("track_label", TRACK_LABEL_V1),
        "tier": tier,
        "tier_label": metadata.get("tier_label", TIER_LABELS_V1.get(tier, "unsupported_tier_metadata_label")),
        "case_kind": _safe_label(metadata.get("case_kind", "case_metadata_only")),
        "source_safety_label": _safe_label(
            metadata.get("source_safety_label", "safe_synthetic_or_public_domain_summary_metadata_only")
        ),
        "problem_statement_summary": _safe_label(metadata.get("problem_statement_summary", "")),
        "definitions_summary": _safe_label(metadata.get("definitions_summary", "metadata_label_only")),
        "known_results_summary": _safe_label(metadata.get("known_results_summary", "metadata_label_only")),
        "unknowns": _safe_labels(metadata.get("unknowns", [])),
        "assumptions": _safe_labels(metadata.get("assumptions", [])),
        "hypotheses": _safe_labels(metadata.get("hypotheses", [])),
        "bounded_variants": _safe_labels(metadata.get("bounded_variants", [])),
        "toy_cases": _safe_labels(metadata.get("toy_cases", [])),
        "counterexample_search_plan": _safe_labels(metadata.get("counterexample_search_plan", [])),
        "falsification_labels": _safe_labels(metadata.get("falsification_labels", [])),
        "proof_gap_labels": _safe_labels(metadata.get("proof_gap_labels", [])),
        "evidence_literature_need_labels": _safe_labels(metadata.get("evidence_literature_need_labels", [])),
        "safe_next_observations": _safe_labels(metadata.get("safe_next_observations", [])),
        "uncertainty_labels": _safe_labels(metadata.get("uncertainty_labels", [])),
        "compressed_lesson": _safe_label(metadata.get("compressed_lesson", "metadata_label_only")),
        "denied_authority_fields": {field: bool(denied.get(field)) for field in REQUIRED_DENIED_AUTHORITY_FIELDS},
        "validation_status": "validation_pass_metadata_quality_only",
        "blocked": False,
        "blocked_reason_labels": [],
        "visible_risks": _safe_labels(
            metadata.get("visible_risks", [])
            + [
                "case-corpus-entry-is-not-corpus-file",
                "case-corpus-entry-is-not-corpus-data",
                "case-corpus-entry-is-not-runner-or-execution",
                "tier-labels-are-not-scores-or-judges",
                "known-results-summary-is-not-proof-claim",
                "open-problem-boundary-metadata-is-not-solution-evidence",
                "safe-markdown-is-not-user-facing-answer-text",
                "json-safe-metadata-is-not-reply-payload",
                "validation-pass-is-not-official-evaluation-or-product-readiness",
                "occ-openclaw-is-not-deployed-weslr",
            ]
        ),
        "followups": _safe_labels(
            metadata.get("followups", ["review_cognitive_gym_erdos_case_corpus_helpers_implementation_v1"])
        ),
        "next_lane": metadata.get("next_lane", NEXT_LANE_V1),
    }
    return _json_safe(entry)


def build_erdos_case_corpus_entry_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    """Build one in-memory Erdős case-corpus entry metadata object only."""

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, Mapping):
        metadata = {"blocked_reason_labels": ["metadata_not_mapping"]}
    merged = {**dict(metadata), **overrides}
    entry = _base_entry(merged)
    validation = validate_erdos_case_corpus_entry_v1(entry)
    entry["blocked"] = validation["blocked"]
    entry["blocked_reason_labels"] = validation["blocked_reason_labels"]
    entry["validation_status"] = _validation_status(validation["blocked"])
    return _json_safe(entry)


def validate_erdos_case_corpus_entry_v1(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Validate Erdős case-corpus entry metadata without side effects."""

    if not isinstance(entry, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "blocked_reason_labels": ["entry_not_mapping"],
            "missing_required_fields": list(CASE_CORPUS_ENTRY_FIELDS_V1),
            "invalid_fields": ["entry"],
            "json_safe": False,
            "safe_to_render_markdown": False,
            "denied_authority_violations": [],
        }

    blocked_reason_labels: list[str] = []
    invalid_fields: list[str] = []
    missing_required_fields = [field for field in CASE_CORPUS_ENTRY_FIELDS_V1 if field not in entry]
    for field in missing_required_fields:
        _append_unique(blocked_reason_labels, f"missing_required_field:{field}")

    for field in entry:
        if field not in CASE_CORPUS_ENTRY_FIELDS_V1:
            _append_unique(invalid_fields, field)
            _append_unique(blocked_reason_labels, f"unsupported_case_corpus_entry_field:{field}")

    if entry.get("corpus_schema_version") != CORPUS_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "corpus_schema_version")
        _append_unique(blocked_reason_labels, "corpus_schema_version_mismatch")
    if entry.get("track_label") != TRACK_LABEL_V1:
        _append_unique(invalid_fields, "track_label")
        _append_unique(blocked_reason_labels, "unsupported_track_label")
    if entry.get("track_label") not in SUPPORTED_COGNITIVE_GYM_CHALLENGE_TRACKS:
        _append_unique(blocked_reason_labels, "track_label_not_in_cognitive_gym_protocol")

    tier = entry.get("tier")
    if tier not in TIER_LABELS_V1:
        _append_unique(invalid_fields, "tier")
        _append_unique(blocked_reason_labels, "unsupported_tier")
    elif entry.get("tier_label") != TIER_LABELS_V1[tier]:
        _append_unique(invalid_fields, "tier_label")
        _append_unique(blocked_reason_labels, "tier_label_mismatch")

    for field in _REQUIRED_NONEMPTY_STRING_FIELDS:
        if not isinstance(entry.get(field), str) or not entry.get(field, "").strip():
            _append_unique(invalid_fields, field)
            _append_unique(blocked_reason_labels, f"missing_required_field:{field}")

    for field in _TEXT_FIELDS:
        if field in entry and not isinstance(entry.get(field), str):
            _append_unique(invalid_fields, field)
            _append_unique(blocked_reason_labels, f"{field}_not_string")

    for field in _LIST_FIELDS:
        if field in entry and not isinstance(entry.get(field), list):
            _append_unique(invalid_fields, field)
            _append_unique(blocked_reason_labels, f"{field}_not_list")

    if entry.get("next_lane") != NEXT_LANE_V1:
        _append_unique(invalid_fields, "next_lane")
        _append_unique(blocked_reason_labels, "next_lane_mismatch")
    if not isinstance(entry.get("blocked"), bool):
        _append_unique(invalid_fields, "blocked")
        _append_unique(blocked_reason_labels, "blocked_not_boolean")

    denied = entry.get("denied_authority_fields")
    denied_authority_violations: list[str] = []
    if not isinstance(denied, Mapping):
        _append_unique(invalid_fields, "denied_authority_fields")
        _append_unique(blocked_reason_labels, "denied_authority_fields_not_mapping")
        denied = {}
    for field in REQUIRED_DENIED_AUTHORITY_FIELDS:
        if field not in denied:
            _append_unique(denied_authority_violations, f"missing_denied_authority_field:{field}")
        elif denied.get(field) is not False:
            _append_unique(denied_authority_violations, f"denied_authority_field_not_false:{field}")
    for reason in denied_authority_violations:
        _append_unique(blocked_reason_labels, reason)

    json_safe = _is_json_safe(entry)
    if not json_safe:
        _append_unique(blocked_reason_labels, "non_json_safe_entry_detected")
    for reason in _detect_unsafe_content(entry):
        _append_unique(blocked_reason_labels, reason)
    if entry.get("blocked") is True:
        for reason in _safe_labels(entry.get("blocked_reason_labels", [])):
            _append_unique(blocked_reason_labels, reason)

    valid = not blocked_reason_labels and not invalid_fields and not missing_required_fields and json_safe
    return {
        "valid": valid,
        "blocked": not valid,
        "blocked_reason_labels": _safe_labels(blocked_reason_labels),
        "missing_required_fields": missing_required_fields,
        "invalid_fields": _safe_labels(invalid_fields),
        "json_safe": json_safe,
        "safe_to_render_markdown": valid,
        "denied_authority_violations": _safe_labels(denied_authority_violations),
    }


def summarize_erdos_case_corpus_entry_v1(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Return compact JSON-safe internal summary metadata."""

    validation = validate_erdos_case_corpus_entry_v1(entry)
    if not isinstance(entry, Mapping):
        entry = {}
    return _json_safe(
        {
            "corpus_schema_version": entry.get("corpus_schema_version"),
            "case_id": entry.get("case_id"),
            "track_label": entry.get("track_label"),
            "tier": entry.get("tier"),
            "tier_label": entry.get("tier_label"),
            "case_kind": entry.get("case_kind"),
            "source_safety_label": entry.get("source_safety_label"),
            "valid": validation["valid"],
            "blocked": validation["blocked"],
            "validation_status": _validation_status(validation["blocked"]),
            "blocked_reason_labels": validation["blocked_reason_labels"],
            "denied_authority_fields_false": not validation["denied_authority_violations"],
            "metadata_shape_preserved": True,
            "metadata_only_no_runtime_no_output_no_authority": True,
            "visible_risks": _json_safe(entry.get("visible_risks", [])),
            "followups": _json_safe(entry.get("followups", [])),
            "next_lane": entry.get("next_lane", NEXT_LANE_V1),
        }
    )


def render_erdos_case_corpus_entry_markdown_v1(entry: Mapping[str, Any]) -> str:
    """Render safe internal Markdown for validated case-corpus entry metadata only."""

    validation = validate_erdos_case_corpus_entry_v1(entry)
    if validation["valid"] is not True:
        reasons = validation["blocked_reason_labels"] or ["invalid_erdos_case_corpus_entry_metadata"]
        lines = [
            "# WESLR Cognitive Gym Erdős Case Corpus Entry V1",
            "",
            f"- track_label: `{TRACK_LABEL_V1}`",
            "- valid: `False`",
            "- blocked: `True`",
            "- unsafe_content_not_rendered: `True`",
            "- validation_status: `blocked_invalid_or_unsafe_metadata_labels_only`",
            "",
            "## Blocked Reason Labels",
        ]
        lines.extend(f"- `{reason}`" for reason in _safe_labels(reasons))
        lines.extend(
            [
                "",
                "## Safety Boundary",
                "- `internal_review_material_only`",
                "- `metadata_only_no_runtime_no_output_no_authority`",
                "- `no_actual_corpus_file`",
                "- `no_corpus_data`",
                "- `no_case_execution`",
                "- `no_runner_creation`",
                "- `no_scoring_or_judges`",
                "- `no_result_artifact_creation`",
                "- `no_proof_or_open_problem_solution_claim`",
                "- `no_final_answer_or_user_facing_output`",
                "- `no_reply_output`",
                "- `no_official_claims`",
                "- `no_provider_model_search_advisor_calls`",
                "- `dot_weslr_io_not_performed`",
                "- `no_authority_grant`",
                f"- next_lane: `{NEXT_LANE_V1}`",
            ]
        )
        return "\n".join(lines) + "\n"

    lines = [
        "# WESLR Cognitive Gym Erdős Case Corpus Entry V1",
        "",
        "## Entry Status",
        f"- corpus_schema_version: `{entry['corpus_schema_version']}`",
        f"- case_id: `{entry['case_id']}`",
        f"- track_label: `{entry['track_label']}`",
        f"- tier: `{entry['tier']}`",
        f"- tier_label: `{entry['tier_label']}`",
        f"- case_kind: `{entry['case_kind']}`",
        f"- source_safety_label: `{entry['source_safety_label']}`",
        f"- valid: `{validation['valid']}`",
        f"- blocked: `{validation['blocked']}`",
        "- validation_status: `validation_pass_metadata_quality_only`",
        "",
        "## Internal Metadata Summaries",
        f"- problem_statement_summary: `{entry['problem_statement_summary']}`",
        f"- definitions_summary: `{entry['definitions_summary']}`",
        f"- known_results_summary: `{entry['known_results_summary']}`",
        f"- unknowns: `{entry['unknowns']}`",
        f"- assumptions: `{entry['assumptions']}`",
        f"- hypotheses: `{entry['hypotheses']}`",
        f"- bounded_variants: `{entry['bounded_variants']}`",
        f"- toy_cases: `{entry['toy_cases']}`",
        f"- counterexample_search_plan: `{entry['counterexample_search_plan']}`",
        f"- falsification_labels: `{entry['falsification_labels']}`",
        f"- proof_gap_labels: `{entry['proof_gap_labels']}`",
        f"- evidence_literature_need_labels: `{entry['evidence_literature_need_labels']}`",
        f"- safe_next_observations: `{entry['safe_next_observations']}`",
        f"- uncertainty_labels: `{entry['uncertainty_labels']}`",
        f"- compressed_lesson: `{entry['compressed_lesson']}`",
        "",
        "## Denied Authority Summary",
    ]
    for field in REQUIRED_DENIED_AUTHORITY_FIELDS:
        lines.append(f"- {field}: `{entry['denied_authority_fields'][field]}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "- `internal_review_material_only`",
            "- `metadata_only_no_runtime_no_output_no_authority`",
            "- `not_corpus_file`",
            "- `not_corpus_data`",
            "- `not_runner`",
            "- `not_challenge_execution`",
            "- `not_scoring`",
            "- `not_judges`",
            "- `not_result_artifact`",
            "- `not_proof_claim`",
            "- `not_open_problem_solution_claim`",
            "- `not_final_answer_prose`",
            "- `not_user_facing_output`",
            "- `not_reply_output`",
            "- `not_official_benchmark_intelligence_turing_iq_certification_product_claim`",
            "- `no_authority_grant`",
            f"- next_lane: `{entry['next_lane']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def to_erdos_case_corpus_entry_json_safe_v1(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Return deterministic JSON-safe Erdős case-corpus entry metadata."""

    validation = validate_erdos_case_corpus_entry_v1(entry)
    if validation["valid"] is not True:
        safe = _base_entry(entry if isinstance(entry, Mapping) else {})
        safe["blocked"] = True
        safe["blocked_reason_labels"] = validation["blocked_reason_labels"] or ["invalid_erdos_case_corpus_entry_metadata"]
        safe["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
        safe["denied_authority_fields"] = _default_denied_authority_fields()
        return _json_safe(safe)
    safe = _json_safe(entry)
    safe["denied_authority_fields"] = _default_denied_authority_fields()
    return safe


__all__ = (
    "build_erdos_case_corpus_entry_v1",
    "validate_erdos_case_corpus_entry_v1",
    "summarize_erdos_case_corpus_entry_v1",
    "render_erdos_case_corpus_entry_markdown_v1",
    "to_erdos_case_corpus_entry_json_safe_v1",
)
