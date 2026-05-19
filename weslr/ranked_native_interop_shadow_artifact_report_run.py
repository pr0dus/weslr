"""Ranked/native interop shadow artifact report-run helpers v1.

Pure, deterministic, metadata-only helpers that compose the existing
ranked/native interop shadow artifact helpers and artifact report helpers into
one internal report-run flow. This module does not wire runtime behavior, call
providers, execute prompts, create final answers, write ``.weslr``, or persist
anything except through the explicit authorized docs artifact writer.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from weslr.ranked_native_interop_shadow_artifact import (
    build_ranked_native_interop_shadow_artifact_v1,
    summarize_ranked_native_interop_shadow_artifact_v1,
    validate_ranked_native_interop_shadow_artifact_v1,
)
from weslr.ranked_native_interop_shadow_artifact_report import (
    build_ranked_native_interop_shadow_artifact_report_v1,
    render_ranked_native_interop_shadow_artifact_report_markdown_v1,
    validate_ranked_native_interop_shadow_artifact_report_v1,
)

SCHEMA_VERSION = "ranked_native_interop_shadow_artifact_report_run_v1"
HELPER_NAME = "ranked_native_interop_shadow_artifact_report_run_helpers_v1"
RUN_TYPE = "ranked_native_interop_shadow_artifact_report_run_v1"
ARTIFACT_TYPE = "ranked_native_interop_shadow_artifact_v1"
AUTHORIZED_ARTIFACT_PATH = "docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_RESULT_V1.md"

FALSE_SAFETY_FLAGS = (
    "runtime_wired",
    "final_answer_generated",
    "raw_prompt_response_retained",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "persistence_performed",
    "feature_flag_enabled",
    "official_evaluation_claimed",
)

READINESS_LABELS = (
    "ranked_native_artifact_report_run_implemented",
    "metadata_only_report_run",
    "internal_shadow_evaluation_only",
    "helper_authority_boundaries_preserved",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "raw_prompt_response_not_retained",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
)

MINOR_FOLLOWUPS = (
    "renderer_next_lane_wording_drift",
    "validator_phrase_key_limitation",
)

REQUIRED_RUN_FIELDS = (
    "schema_version",
    "helper_name",
    "run_type",
    "artifact_type",
    "artifact_valid",
    "artifact_safe_to_render",
    "report_valid",
    "report_safe_to_render",
    "run_valid",
    "safe_to_write_artifact",
    "artifact_summary",
    "report",
    "markdown",
    "minor_followups",
    "run_status_label",
    "readiness_labels",
    *FALSE_SAFETY_FLAGS,
)

FORBIDDEN_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "prompt_text",
    "response_text",
    "final_answer_text",
    "private_content",
    "hidden_prompt",
    "answer_key",
    "provider_output",
    "model_output",
    "official_score",
    "iq_score",
    "turing_score",
    "benchmark_score",
    "occ_as_weslr",
    "openclaw_as_weslr",
    "conscious",
    "sentient",
)

_ALLOWED_KEYS_WITH_FORBIDDEN_FRAGMENTS = {
    "final_answer_generated",
    "final_answer_authority_not_granted",
    "final_answer_contract_metadata",
    "raw_prompt_response_retained",
    "raw_prompt_response_not_retained",
    "selected_candidate_live_response_text",
}

FORBIDDEN_TRUE_FLAGS = (
    "runtime_wired",
    "final_answer_generated",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "persistence_performed",
    "feature_flag_enabled",
    "official_evaluation_claimed",
    "raw_prompt_response_retained",
    "network_call_made",
    "subprocess_call_made",
)

FORBIDDEN_VALUE_MARKERS = (
    "raw prompt",
    "raw response",
    "final answer:",
    "final answer text",
    "private content",
    "hidden prompt",
    "answer key",
    "provider output",
    "model output",
    "official score",
    "official benchmark",
    "benchmark score",
    "turing-test pass",
    "turing test pass",
    "iq score",
    "iq claim",
    "certification claim",
    "product-readiness claim",
    "product readiness claim",
    "runtime output treated as authority",
    "runtime authority",
    "runtime ready",
    "runtime-ready",
    "consciousness claim",
    "sentience claim",
    "occ is weslr",
    "openclaw is weslr",
)


def _merge_unique(*iterables: Iterable[Any]) -> List[Any]:
    merged: List[Any] = []
    for iterable in iterables:
        for item in iterable:
            if item not in merged:
                merged.append(item)
    return merged


def _walk(value: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield child_path, child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, child
            yield from _walk(child, child_path)


def _safe_reason(label: str) -> str:
    return label.replace(" ", "_").replace(".", "_").replace("[", "_").replace("]", "_")


def _synthetic_artifact_metadata_v1() -> dict:
    """Build validator-compatible synthetic metadata for the artifact helpers."""

    return build_ranked_native_interop_shadow_artifact_v1(
        ranked_state_frame_summary={"present": True, "source": "synthetic_metadata"},
        selected_candidate_metadata={
            "present": True,
            "selection_label": "strong_fit",
            "live_response_material": False,
        },
        rejected_candidate_labels=[
            "canned_template_like_candidate",
            "required_evidence_not_satisfied",
        ],
        ranking_label_summary={"strong_fit": 1, "rejected": 2},
        final_answer_contract_metadata={"present": True, "final_answer_generated": False},
        native_reasoning_frame_metadata={"present": True, "source": "synthetic_metadata"},
        native_draft_shape_metadata={"present": True, "draft_is_final_answer": False},
        native_self_check_metadata={"present": True, "answer_approval": False},
        native_assembly_metadata={"present": True, "runtime_material": False},
        provenance_constraints=["provenance_boundary_exercised"],
        evidence_constraints=["evidence_boundary_exercised"],
        safety_boundary_labels=[
            "runtime_integration_not_authorized",
            "final_answer_authority_not_granted",
            "raw_prompt_response_not_retained",
            "official_evaluation_not_claimed",
        ],
        interop_notes=[
            "metadata_only_ranked_native_interop_note",
            "selected_candidate_live_response_text_false",
            "native_draft_is_final_answer_false",
            "native_self_check_answer_approval_false",
            "native_assembly_runtime_output_false",
        ],
        readiness_labels=list(READINESS_LABELS),
    )


def derive_ranked_native_interop_shadow_artifact_report_run_status_v1(run_result: dict) -> str:
    """Return a qualitative report-run status label only; no scores."""

    if not isinstance(run_result, dict):
        return "report_run_blocked"
    if not (
        run_result.get("artifact_valid") is True
        and run_result.get("report_valid") is True
        and run_result.get("run_valid") is True
        and run_result.get("safe_to_write_artifact") is True
    ):
        return "report_run_blocked"
    if any(run_result.get(flag) is not False for flag in FALSE_SAFETY_FLAGS):
        return "report_run_blocked"
    minor = run_result.get("minor_followups", [])
    if minor and set(minor).issubset(set(MINOR_FOLLOWUPS)):
        return "report_run_clean_with_minor_followup"
    if minor:
        return "report_run_needs_followup"
    return "report_run_clean"


def validate_ranked_native_interop_shadow_artifact_report_run_v1(run_result: dict) -> dict:
    """Validate run metadata safety before artifact writing or rendering."""

    if not isinstance(run_result, dict):
        return {"valid": False, "safe_to_write_artifact": False, "reason_labels": ["run_result_not_dict"]}

    reason_labels: List[str] = []
    for field in REQUIRED_RUN_FIELDS:
        if field not in run_result:
            reason_labels.append(f"missing_required_field:{field}")

    if run_result.get("schema_version") != SCHEMA_VERSION:
        reason_labels.append("unexpected_schema_version")
    if run_result.get("helper_name") != HELPER_NAME:
        reason_labels.append("unexpected_helper_name")
    if run_result.get("run_type") != RUN_TYPE:
        reason_labels.append("unexpected_run_type")
    if run_result.get("artifact_type") != ARTIFACT_TYPE:
        reason_labels.append("unexpected_artifact_type")

    if run_result.get("artifact_valid") is not True:
        reason_labels.append("artifact_validation_failure")
    if run_result.get("artifact_safe_to_render") is not True:
        reason_labels.append("artifact_not_safe_to_render")
    if run_result.get("report_valid") is not True:
        reason_labels.append("report_validation_failure")
    if run_result.get("report_safe_to_render") is not True:
        reason_labels.append("report_not_safe_to_render")

    for flag in FALSE_SAFETY_FLAGS:
        if run_result.get(flag) is not False:
            reason_labels.append(f"required_false_flag_violation:{flag}")
    for flag in FORBIDDEN_TRUE_FLAGS:
        if run_result.get(flag) is True:
            reason_labels.append(f"forbidden_true_flag:{flag}")

    readiness = run_result.get("readiness_labels", [])
    if not isinstance(readiness, list):
        reason_labels.append("readiness_labels_not_list")
    else:
        for label in READINESS_LABELS:
            if label not in readiness:
                reason_labels.append(f"missing_readiness_label:{label}")

    minor = run_result.get("minor_followups", [])
    if not isinstance(minor, list):
        reason_labels.append("minor_followups_not_list")
    else:
        for label in MINOR_FOLLOWUPS:
            if label not in minor:
                reason_labels.append(f"missing_minor_followup:{label}")

    report_validation = validate_ranked_native_interop_shadow_artifact_report_v1(run_result.get("report", {}))
    if not report_validation.get("valid"):
        reason_labels.append("nested_report_validation_failure")

    for path, value in _walk(run_result):
        if path == "markdown" or path.startswith("markdown."):
            continue
        key = path.split(".")[-1].split("[")[0].lower()
        if key not in _ALLOWED_KEYS_WITH_FORBIDDEN_FRAGMENTS:
            for fragment in FORBIDDEN_KEY_FRAGMENTS:
                if fragment in key:
                    reason_labels.append(f"forbidden_key:{_safe_reason(path)}")
                    break

        if key in FORBIDDEN_TRUE_FLAGS and value is True:
            reason_labels.append(f"forbidden_true_flag:{key}")

        lowered = value.lower() if isinstance(value, str) else ""
        if lowered:
            for marker in FORBIDDEN_VALUE_MARKERS:
                if marker in lowered:
                    reason_labels.append(f"forbidden_value_marker:{marker.replace(' ', '_')}")

    deduped: List[str] = []
    for reason in reason_labels:
        if reason not in deduped:
            deduped.append(reason)
    valid = not deduped
    return {"valid": valid, "safe_to_write_artifact": valid, "reason_labels": deduped}


def render_ranked_native_interop_shadow_artifact_report_run_markdown_v1(run_result: dict) -> str:
    """Render final safe internal report-run Markdown."""

    validation = validate_ranked_native_interop_shadow_artifact_report_run_v1(run_result)
    if not validation["valid"]:
        reasons = "\n".join(f"- `{reason}`" for reason in validation["reason_labels"])
        return (
            "# WESLR Ranked/Native Interop Shadow Artifact Report Run Result V1 — BLOCKED\n\n"
            "## Run Status\n"
            "- run_valid: `False`\n"
            "- safe_to_write_artifact: `False`\n\n"
            "## Safe Reason Labels\n"
            f"{reasons}\n\n"
            "Offending content is intentionally not rendered.\n"
        )

    readiness = "\n".join(f"- `{label}`" for label in run_result.get("readiness_labels", []))
    followups = "\n".join(f"- `{label}`" for label in run_result.get("minor_followups", []))
    aggregate = "\n".join(f"- `{label}`" for label in run_result.get("report", {}).get("aggregate_labels", []))
    flags = "\n".join(f"- `{flag}`: `{run_result.get(flag)}`" for flag in FALSE_SAFETY_FLAGS)
    report_markdown = render_ranked_native_interop_shadow_artifact_report_markdown_v1(run_result.get("report", {}))

    return (
        "# WESLR Ranked/Native Interop Shadow Artifact Report Run Result V1\n\n"
        "Layer: WESLR_RUNTIME_CHANGE / helper-only metadata-only report-run result.\n\n"
        "Readiness labels: `ranked_native_artifact_report_run_implemented`, "
        "`metadata_only_report_run`, `internal_shadow_evaluation_only`, "
        "`helper_authority_boundaries_preserved`, `runtime_integration_not_authorized`, "
        "`final_answer_authority_not_granted`, `raw_prompt_response_not_retained`, "
        "`official_evaluation_not_claimed`, `minor_followup_carried_forward`, "
        "`voice_downstream_not_current_priority`.\n\n"
        "## Run Status\n"
        f"- run_status_label: `{run_result.get('run_status_label')}`\n"
        f"- run_valid: `{run_result.get('run_valid')}`\n"
        f"- safe_to_write_artifact: `{run_result.get('safe_to_write_artifact')}`\n\n"
        "## Caveats\n"
        "- internal shadow evaluation only\n"
        "- not official benchmark/Turing/IQ/certification/product-readiness\n"
        "- runtime integration not authorized\n"
        "- final-answer authority not granted\n"
        "- `chat_responder.py` not touched/authorized\n"
        "- renderer_next_lane_wording_drift carried forward\n"
        "- validator_phrase_key_limitation carried forward\n\n"
        "## Artifact / Report Validation\n"
        f"- artifact_type: `{run_result.get('artifact_type')}`\n"
        f"- artifact_valid: `{run_result.get('artifact_valid')}`\n"
        f"- artifact_safe_to_render: `{run_result.get('artifact_safe_to_render')}`\n"
        f"- report_valid: `{run_result.get('report_valid')}`\n"
        f"- report_safe_to_render: `{run_result.get('report_safe_to_render')}`\n\n"
        "## Report Aggregate Labels\n"
        f"{aggregate}\n\n"
        "## Readiness Labels\n"
        f"{readiness}\n\n"
        "## Minor Followups Carried Forward\n"
        f"{followups}\n\n"
        "## Safety Confirmation\n"
        f"{flags}\n"
        "- helper/report-run source plus one docs artifact only\n"
        "- metadata-only internal shadow evaluation\n"
        "- no live WESLR behavior change\n"
        "- no runtime wiring\n"
        "- no ChatResponder/respond_chat/generate_chat calls\n"
        "- no prompt execution\n"
        "- no model/search/advisor calls\n"
        "- no .weslr writes\n"
        "- no raw prompt/response retention\n"
        "- no final answer generation\n"
        "- no feature flag enablement\n"
        "- no persistence except exact docs artifact\n"
        "- no network/subprocess calls\n"
        "- no voice/TTS work\n"
        "- no official benchmark/Turing/IQ/certification/product-readiness/consciousness/sentience claims\n"
        "- OCC/OpenClaw treated only as construction/inspection tool, not deployed WESLR\n\n"
        "## Generated Safe Artifact Report Markdown\n\n"
        f"{report_markdown}\n\n"
        "## Next-lane Recommendation\n"
        "`REVIEW_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_V1`\n"
    )


def build_ranked_native_interop_shadow_artifact_report_run_v1() -> dict:
    """Build and validate the report run entirely in memory."""

    artifact = _synthetic_artifact_metadata_v1()
    artifact_validation = validate_ranked_native_interop_shadow_artifact_v1(artifact)
    artifact_summary = summarize_ranked_native_interop_shadow_artifact_v1(artifact)
    report = build_ranked_native_interop_shadow_artifact_report_v1(artifact)
    report_validation = validate_ranked_native_interop_shadow_artifact_report_v1(report)

    run_result: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "helper_name": HELPER_NAME,
        "run_type": RUN_TYPE,
        "artifact_type": ARTIFACT_TYPE,
        "artifact_valid": bool(artifact_validation.get("valid")),
        "artifact_safe_to_render": bool(artifact_validation.get("safe_to_render")),
        "report_valid": bool(report_validation.get("valid")),
        "report_safe_to_render": bool(report_validation.get("safe_to_render")),
        "run_valid": False,
        "safe_to_write_artifact": False,
        "artifact_summary": copy.deepcopy(artifact_summary),
        "report": copy.deepcopy(report),
        "markdown": "",
        "minor_followups": list(MINOR_FOLLOWUPS),
        "run_status_label": "report_run_blocked",
        "readiness_labels": _merge_unique(READINESS_LABELS, artifact.get("readiness_labels", [])),
        "synthetic_artifact_metadata": copy.deepcopy(artifact),
        "required_synthetic_metadata_checks": {
            "ranked_state_frame_present": True,
            "native_reasoning_frame_present": True,
            "selected_candidate_live_response_text": False,
            "native_draft_is_final_answer": False,
            "native_self_check_answer_approval": False,
            "native_assembly_runtime_output": False,
        },
    }
    run_result.update({flag: False for flag in FALSE_SAFETY_FLAGS})

    validation = validate_ranked_native_interop_shadow_artifact_report_run_v1(run_result)
    run_result["run_valid"] = bool(validation.get("valid"))
    run_result["safe_to_write_artifact"] = bool(validation.get("safe_to_write_artifact"))
    run_result["run_status_label"] = derive_ranked_native_interop_shadow_artifact_report_run_status_v1(run_result)
    run_result["markdown"] = render_ranked_native_interop_shadow_artifact_report_run_markdown_v1(run_result)
    return run_result


def write_ranked_native_interop_shadow_artifact_report_run_artifact_v1(path: str | None = None) -> dict:
    """Write the one authorized internal docs artifact and return metadata."""

    artifact_path = path or AUTHORIZED_ARTIFACT_PATH
    if artifact_path != AUTHORIZED_ARTIFACT_PATH:
        return {
            "artifact_written": False,
            "artifact_path": artifact_path,
            "run_status_label": "report_run_blocked",
            "artifact_valid": False,
            "report_valid": False,
            "run_valid": False,
            "safe_to_write_artifact": False,
            "reason_labels": ["unauthorized_artifact_path"],
            **{flag: False for flag in FALSE_SAFETY_FLAGS},
        }

    run_result = build_ranked_native_interop_shadow_artifact_report_run_v1()
    validation = validate_ranked_native_interop_shadow_artifact_report_run_v1(run_result)
    if not validation.get("valid"):
        return {
            "artifact_written": False,
            "artifact_path": artifact_path,
            "run_status_label": "report_run_blocked",
            "artifact_valid": run_result.get("artifact_valid", False),
            "report_valid": run_result.get("report_valid", False),
            "run_valid": False,
            "safe_to_write_artifact": False,
            "reason_labels": validation.get("reason_labels", []),
            **{flag: run_result.get(flag, False) for flag in FALSE_SAFETY_FLAGS},
        }

    output_path = Path(artifact_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(run_result["markdown"], encoding="utf-8")
    return {
        "artifact_written": True,
        "artifact_path": artifact_path,
        "run_status_label": run_result["run_status_label"],
        "artifact_valid": run_result["artifact_valid"],
        "report_valid": run_result["report_valid"],
        "run_valid": run_result["run_valid"],
        "safe_to_write_artifact": run_result["safe_to_write_artifact"],
        **{flag: run_result.get(flag, False) for flag in FALSE_SAFETY_FLAGS},
    }
