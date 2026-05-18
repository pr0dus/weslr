#!/usr/bin/env python3
"""WESLR ranked response shadow evaluation report run helpers V1.

Minimal metadata-only report-run helpers. This module builds the existing
synthetic ranked response shadow scenario corpus, validates it, runs it through
existing helper-only shadow/scenario/report helpers, renders safe markdown, and
optionally writes exactly one authorized internal docs artifact.

It does not wire runtime behavior, execute prompts, generate final answers, call
external providers, enable feature flags, write .weslr state, use subprocesses,
or perform network work.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from weslr import ranked_response_shadow_evaluation_report as report_helpers
from weslr import ranked_response_shadow_evaluation_scenarios as scenarios

SCHEMA_VERSION_V1 = "ranked_response_shadow_evaluation_report_run_schema_v1"
HELPER_NAME_V1 = "ranked_response_shadow_evaluation_report_run_v1"
RUN_TYPE_V1 = "ranked_response_shadow_evaluation_report_run_v1"
AUTHORIZED_ARTIFACT_PATH_V1 = "docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_RUN_RESULT_V1.md"

READINESS_LABELS_V1 = [
    "ranked_response_shadow_report_run_implemented",
    "metadata_only_report_run",
    "internal_shadow_evaluation_only",
    "runtime_integration_not_authorized",
    "raw_prompt_response_not_retained",
    "final_answer_not_generated",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
]

MINOR_FOLLOWUPS_V1 = [
    {
        "label": "renderer_next_lane_wording_drift",
        "status": "carried_forward_minor_caveat",
        "summary": "Existing report renderer may point to a review lane rather than the requested future design/run lane.",
    },
    {
        "label": "validator_phrase_key_limitation",
        "status": "carried_forward_minor_caveat",
        "summary": "Existing validation remains conservative phrase/key based rather than schema-formal.",
    },
]

SAFE_FALSE_FLAGS_V1 = {
    "runtime_wired": False,
    "final_answer_generated": False,
    "raw_prompt_retained": False,
    "raw_response_retained": False,
    "model_call_made": False,
    "search_call_made": False,
    "advisor_call_made": False,
    "persistence_performed": False,
    "official_evaluation_claimed": False,
}

FORBIDDEN_KEYS_V1 = {
    "raw_text",
    "raw_prompt",
    "prompt_text",
    "raw_response",
    "response_text",
    "final_answer",
    "final_answer_text",
    "private_content",
    "private_user_content",
    "hidden_prompt",
    "system_prompt",
    "answer_key",
    "candidate_prose",
    "model_output",
    "provider_output",
}

FORBIDDEN_TRUE_FLAGS_V1 = {
    "runtime_wired": "runtime_wired_true",
    "final_answer_generated": "final_answer_generated_true",
    "model_call_made": "model_call_made_true",
    "search_call_made": "search_call_made_true",
    "advisor_call_made": "advisor_call_made_true",
    "feature_flag_enabled": "feature_flag_enabled_true",
    "feature_flags_enabled": "feature_flag_enabled_true",
    "network_call_made": "network_call_made_true",
    "subprocess_call_made": "subprocess_call_made_true",
}

FORBIDDEN_TEXT_MARKERS_V1 = {
    "official benchmark": "official_claim_marker_present",
    "passed turing": "official_claim_marker_present",
    "turing passed": "official_claim_marker_present",
    "certification ready": "official_claim_marker_present",
    "product readiness certified": "official_claim_marker_present",
    "official iq": "official_claim_marker_present",
    "iq score": "official_claim_marker_present",
    "weslr is conscious": "consciousness_or_sentience_marker_present",
    "weslr is sentient": "consciousness_or_sentience_marker_present",
    "consciousness proven": "consciousness_or_sentience_marker_present",
    "sentience proven": "consciousness_or_sentience_marker_present",
    "occ is weslr": "occ_as_weslr_marker_present",
    "openclaw is weslr": "occ_as_weslr_marker_present",
    "occ/openclaw is weslr": "occ_as_weslr_marker_present",
    "private user content": "private_content_marker_present",
    "protected private material": "private_content_marker_present",
}


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def _walk(value: Any, path: str = ""):
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_s = str(key)
            next_path = f"{path}.{key_s}" if path else key_s
            yield next_path, item
            yield from _walk(item, next_path)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            next_path = f"{path}[{idx}]"
            yield next_path, item
            yield from _walk(item, next_path)


def _blob(value: Any) -> str:
    return json.dumps(_json_safe(value), sort_keys=True, ensure_ascii=True).lower()


def _base_run_metadata() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_name": HELPER_NAME_V1,
        "run_type": RUN_TYPE_V1,
        "readiness_labels": list(READINESS_LABELS_V1),
        **SAFE_FALSE_FLAGS_V1,
    }


def derive_ranked_response_shadow_evaluation_report_run_status_v1(run_result: dict) -> str:
    """Derive qualitative run status."""

    validation = run_result.get("run_validation") or validate_ranked_response_shadow_evaluation_report_run_v1(run_result)
    if validation.get("valid") is False:
        return "report_run_blocked"
    failed = int(run_result.get("failed_count", 0) or 0)
    blocked = int(run_result.get("blocked_count", 0) or 0)
    if failed or blocked:
        return "report_run_needs_followup"
    if run_result.get("minor_followups"):
        return "report_run_clean_with_minor_followup"
    return "report_run_clean"


def build_ranked_response_shadow_evaluation_report_run_v1() -> dict:
    """Build and validate the ranked response shadow evaluation report run in memory."""

    scenario_corpus = scenarios.build_ranked_response_shadow_scenario_corpus_v1()
    scenario_validation = scenarios.validate_ranked_response_shadow_scenario_corpus_v1(scenario_corpus)
    corpus_result = scenarios.run_ranked_response_shadow_scenario_corpus_v1(scenario_corpus)
    report = report_helpers.build_ranked_response_shadow_evaluation_report_v1(corpus_result)
    report_validation = report_helpers.validate_ranked_response_shadow_evaluation_report_v1(report)
    markdown = report_helpers.render_ranked_response_shadow_evaluation_report_markdown_v1(report)

    run_result: dict[str, Any] = {
        **_base_run_metadata(),
        "scenario_count": int(corpus_result.get("scenario_count", len(scenario_corpus)) or 0),
        "category_count": int(corpus_result.get("category_count", 0) or 0),
        "passed_count": int(corpus_result.get("passed_count", 0) or 0),
        "failed_count": int(corpus_result.get("failed_count", 0) or 0),
        "blocked_count": int(report.get("blocked_count", 0) or 0),
        "scenario_validation": scenario_validation,
        "report_validation": report_validation,
        "report": report,
        "markdown": markdown,
        "minor_followups": _json_safe(MINOR_FOLLOWUPS_V1),
        "run_status_label": "pending_validation",
    }
    run_validation = validate_ranked_response_shadow_evaluation_report_run_v1(run_result)
    run_result["run_validation"] = run_validation
    run_result["run_status_label"] = derive_ranked_response_shadow_evaluation_report_run_status_v1(run_result)
    return _json_safe(run_result)


def validate_ranked_response_shadow_evaluation_report_run_v1(run_result: dict) -> dict:
    """Validate report-run metadata before artifact rendering/writing."""

    labels: list[str] = []
    if not isinstance(run_result, Mapping):
        return {"valid": False, "safe_to_write_artifact": False, "reason_labels": ["run_result_not_mapping"]}

    for path, value in _walk(run_result):
        key = path.split(".")[-1].split("[")[0]
        if key in FORBIDDEN_KEYS_V1:
            labels.append(f"forbidden_key:{key}")
        if key in FORBIDDEN_TRUE_FLAGS_V1 and value is True:
            labels.append(FORBIDDEN_TRUE_FLAGS_V1[key])

    blob = _blob(run_result)
    for marker, label in FORBIDDEN_TEXT_MARKERS_V1.items():
        if marker in blob:
            labels.append(label)

    if run_result.get("scenario_validation", {}).get("valid") is not True:
        labels.append("scenario_validation_failed")
    if run_result.get("report_validation", {}).get("valid") is not True:
        labels.append("report_validation_failed")

    if "unsafe_report_blocked" in str(run_result.get("markdown", "")).lower() and run_result.get("report_validation", {}).get("valid") is True:
        labels.append("unexpected_safe_markdown_block")

    labels = sorted(set(labels))
    return {
        "valid": not labels,
        "safe_to_write_artifact": not labels,
        "reason_labels": labels,
    }


def render_ranked_response_shadow_evaluation_report_run_markdown_v1(run_result: dict) -> str:
    """Render final internal metadata-only report-run markdown."""

    validation = validate_ranked_response_shadow_evaluation_report_run_v1(run_result)
    status = derive_ranked_response_shadow_evaluation_report_run_status_v1({**run_result, "run_validation": validation})
    if not validation["valid"]:
        reasons = ", ".join(validation["reason_labels"]) or "unknown"
        return "\n".join([
            "# WESLR Ranked Response Shadow Evaluation Report Run Result V1",
            "",
            "## Blocked report-run result",
            "",
            "- internal_shadow_evaluation_only",
            "- runtime_integration_not_authorized",
            "- official_evaluation_not_claimed",
            f"- run_status_label: `{status}`",
            f"- reason_labels: `{reasons}`",
        ])

    report = run_result.get("report", {}) if isinstance(run_result.get("report"), Mapping) else {}
    aggregate_labels = report.get("aggregate_labels", []) if isinstance(report, Mapping) else []
    generated_report_markdown = str(run_result.get("markdown", ""))
    minor_labels = [str(item.get("label")) for item in run_result.get("minor_followups", []) if isinstance(item, Mapping)]

    lines = [
        "# WESLR Ranked Response Shadow Evaluation Report Run Result V1",
        "",
        "## SECTION 1 — RUN STATUS",
        "",
        "- internal_shadow_evaluation_only",
        "- metadata_only_report_run",
        "- runtime_integration_not_authorized",
        "- official_evaluation_not_claimed",
        "- final_answer_not_generated",
        "- raw_prompt_response_not_retained",
        "- minor_followup_carried_forward",
        f"- run_status_label: `{status}`",
        f"- schema_version: `{run_result.get('schema_version')}`",
        f"- helper_name: `{run_result.get('helper_name')}`",
        "",
        "## SECTION 2 — COUNTS",
        "",
        f"- scenario_count: `{run_result.get('scenario_count')}`",
        f"- category_count: `{run_result.get('category_count')}`",
        f"- passed_count: `{run_result.get('passed_count')}`",
        f"- failed_count: `{run_result.get('failed_count')}`",
        f"- blocked_count: `{run_result.get('blocked_count')}`",
        "",
        "## SECTION 3 — VALIDATION",
        "",
        f"- scenario_validation_valid: `{run_result.get('scenario_validation', {}).get('valid')}`",
        f"- report_validation_valid: `{run_result.get('report_validation', {}).get('valid')}`",
        f"- run_validation_valid: `{validation.get('valid')}`",
        f"- safe_to_write_artifact: `{validation.get('safe_to_write_artifact')}`",
        "",
        "## SECTION 4 — REPORT HELPER AGGREGATE LABELS",
        "",
    ]
    lines.extend(f"- `{label}`" for label in aggregate_labels)
    lines.extend([
        "",
        "## SECTION 5 — MINOR FOLLOWUPS CARRIED FORWARD",
        "",
    ])
    for item in run_result.get("minor_followups", []):
        if isinstance(item, Mapping):
            lines.append(f"- `{item.get('label')}`: `{item.get('status')}` — {item.get('summary')}")
    if "renderer_next_lane_wording_drift" not in minor_labels:
        lines.append("- `renderer_next_lane_wording_drift`: `missing_expected_minor_followup`")
    if "validator_phrase_key_limitation" not in minor_labels:
        lines.append("- `validator_phrase_key_limitation`: `missing_expected_minor_followup`")
    lines.extend([
        "",
        "## SECTION 6 — CLAIM BOUNDARIES",
        "",
        "- This is an internal shadow evaluation only.",
        "- This is not an official benchmark, Turing-test, IQ, certification, product-readiness, deployment, consciousness, or sentience claim.",
        "- Runtime integration is not authorized.",
        "- OCC/OpenClaw is treated only as the construction/inspection tool, not deployed WESLR.",
        "",
        "## SECTION 7 — SAFETY CONFIRMATION",
        "",
        f"- runtime_wired: `{run_result.get('runtime_wired')}`",
        f"- final_answer_generated: `{run_result.get('final_answer_generated')}`",
        f"- raw_prompt_retained: `{run_result.get('raw_prompt_retained')}`",
        f"- raw_response_retained: `{run_result.get('raw_response_retained')}`",
        f"- model_call_made: `{run_result.get('model_call_made')}`",
        f"- search_call_made: `{run_result.get('search_call_made')}`",
        f"- advisor_call_made: `{run_result.get('advisor_call_made')}`",
        f"- persistence_performed_in_memory_build: `{run_result.get('persistence_performed')}`",
        f"- official_evaluation_claimed: `{run_result.get('official_evaluation_claimed')}`",
        "",
        "## SECTION 8 — SAFE REPORT MARKDOWN FROM EXISTING RENDERER",
        "",
        generated_report_markdown,
        "",
        "## SECTION 9 — READINESS LABELS",
        "",
    ])
    lines.extend(f"- `{label}`" for label in run_result.get("readiness_labels", []))
    lines.extend([
        "",
        "## SECTION 10 — NEXT LANE",
        "",
        "Recommended next safest lane: `REVIEW_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_RUN_V1`.",
    ])
    return "\n".join(lines)


def write_ranked_response_shadow_evaluation_report_run_artifact_v1(path: str | None = None) -> dict:
    """Write exactly one authorized internal docs artifact."""

    artifact_path = path or AUTHORIZED_ARTIFACT_PATH_V1
    if artifact_path != AUTHORIZED_ARTIFACT_PATH_V1:
        return {
            "artifact_written": False,
            "artifact_path": artifact_path,
            "safe_to_write_artifact": False,
            "reason_labels": ["unauthorized_artifact_path"],
            **SAFE_FALSE_FLAGS_V1,
        }

    run_result = build_ranked_response_shadow_evaluation_report_run_v1()
    validation = validate_ranked_response_shadow_evaluation_report_run_v1(run_result)
    if not validation["safe_to_write_artifact"]:
        return {
            "artifact_written": False,
            "artifact_path": artifact_path,
            "run_status_label": derive_ranked_response_shadow_evaluation_report_run_status_v1(run_result),
            "scenario_count": run_result.get("scenario_count"),
            "passed_count": run_result.get("passed_count"),
            "failed_count": run_result.get("failed_count"),
            "blocked_count": run_result.get("blocked_count"),
            "safe_to_write_artifact": False,
            "reason_labels": validation["reason_labels"],
            **SAFE_FALSE_FLAGS_V1,
        }

    markdown = render_ranked_response_shadow_evaluation_report_run_markdown_v1(run_result)
    Path(artifact_path).write_text(markdown, encoding="utf-8")
    return {
        "artifact_written": True,
        "artifact_path": artifact_path,
        "run_status_label": derive_ranked_response_shadow_evaluation_report_run_status_v1(run_result),
        "scenario_count": run_result.get("scenario_count"),
        "category_count": run_result.get("category_count"),
        "passed_count": run_result.get("passed_count"),
        "failed_count": run_result.get("failed_count"),
        "blocked_count": run_result.get("blocked_count"),
        "safe_to_write_artifact": True,
        "reason_labels": [],
        **SAFE_FALSE_FLAGS_V1,
        "persistence_performed": True,
    }
