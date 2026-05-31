"""Metadata-only friction training proof report runner v1.

This helper assembles a standardized internal proof report for the first
WESLR friction-trained improvement chain.

It is pure, deterministic, import-safe, and fail-closed.

No model/provider/search/advisor calls. No runtime wiring. No state writes.
No public label. No AGI/consciousness/sentience/Turing/certification claims.
No autonomous self-modification. No raw prompt/answer/transcript capture.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Mapping, Sequence

from weslr.friction_case_capture import build_initial_renderer_friction_cases_v1, summarize_friction_case_batch_v1
from weslr.friction_pattern_miner import build_initial_renderer_friction_patterns_v1, summarize_friction_pattern_packet_v1, build_friction_pattern_packet_v1
from weslr.friction_replay_harness import build_initial_renderer_friction_replay_v1, summarize_friction_replay_packet_v1
from weslr.friction_replay_suite_builder import build_initial_renderer_friction_replay_suites_v1, summarize_friction_replay_suite_packet_v1, build_friction_replay_suite_packet_v1
from weslr.friction_update_proposal_bridge import build_initial_renderer_friction_update_proposals_v1, summarize_friction_update_proposal_packet_v1, build_friction_update_proposal_packet_v1

REPORT_TYPE_V1 = "friction_training_proof_report_v1"
INTERNAL_LABEL_V1 = "WESLR V1.01 internal friction-trained improvement proof"
PUBLIC_LABEL_ALLOWED_V1 = False

REQUIRED_START_HEAD_V1 = "7d7cd16c2d15905ea609543edfeb35b5832af20b"
SOURCE_CHAIN_COMMITS_V1 = {
    "friction_case_capture": "07f6e207e49a3aab2d5f462e7f213e0802b622d9",
    "friction_replay_harness": "caa4aa68b8c87e6f122551ab414cb1de4be578ef",
    "friction_update_proposal_bridge": "257ea9bf85a7f2d457e9d11827a9b558fa3b69f9",
    "initial_friction_proposal_realization": "7604ca8a726c7bbba78ceded9ec9bac6baf9b9d0",
    "friction_pattern_miner": "c8171d6a334fb85ed4ac6b1dca12025356406574",
    "friction_replay_suite_builder": "7d7cd16c2d15905ea609543edfeb35b5832af20b",
}
SOURCE_CHAIN_ORDER_V1 = (
    "friction_case_capture",
    "friction_replay_harness",
    "friction_update_proposal_bridge",
    "initial_friction_proposal_realization",
    "friction_pattern_miner",
    "friction_replay_suite_builder",
)

ALLOWED_CLAIMS_V1 = (
    "internal_friction_trained_improvement_proof",
    "replay_proven_governed_improvement",
    "owner_approved_behavior_improvement",
    "metadata_only_proof_report",
)
FORBIDDEN_CLAIMS_V1 = (
    "agi",
    "consciousness",
    "sentience",
    "official_turing_result",
    "certified_intelligence",
    "public_readiness",
    "autonomous_self_modification",
    "unbounded_learning",
)

ALLOWED_FINAL_JUDGMENTS_V1 = {
    "v101_internal_friction_trained_improvement_proof_valid",
    "v101_proof_partial_needs_more_replay",
    "v101_proof_invalid_hardcoding_risk",
    "v101_proof_blocked_by_boundary_risk",
}

FORBIDDEN_FIELD_NAMES_V1 = {
    "raw_prompt",
    "raw_answer",
    "raw_response",
    "raw_transcript",
    "transcript",
    "transcript_text",
    "answer_text",
    "response_text",
    "prompt_text",
    "raw_context",
    "raw_data",
    "raw_prompt_text",
    "raw_answer_text",
    "raw_response_text",
}

ALLOWED_TOP_LEVEL_FIELDS_V1 = {
    "report_id",
    "report_type",
    "source_commit_range",
    "friction_case_summary",
    "baseline_replay_summary",
    "proposal_summary",
    "realization_summary",
    "post_realization_replay_summary",
    "pattern_summary",
    "replay_suite_summary",
    "anti_hardcoding_summary",
    "boundary_regression_summary",
    "protected_file_summary",
    "allowed_claims",
    "forbidden_claims",
    "internal_label",
    "public_label_allowed",
    "final_judgment",
    "learning_claimed",
    "agi_claimed",
    "consciousness_claimed",
    "official_turing_claimed",
    "certification_claimed",
    "public_ready_claimed",
    "autonomous_self_modification_claimed",
    "runtime_authority",
    "writes_state",
    "model_provider_used",
    "safe_metadata",
}

STARTER_CASE_IDS_V1 = (
    "what_is_weslr_identity_friction",
    "what_can_you_do_now_capability_friction",
    "unknown_word_blorvatek_friction",
    "upload_files_now_boundary_friction",
)

PROTECTED_FILES_V1 = (
    "weslr/chat_responder.py",
    "weslr/main.py",
    "dialogue.py",
    "chat_ui.py",
    "weslr/response_method_selector.py",
    "weslr/no_model_bounded_renderer.py",
    "weslr/answer_method_catalog.py",
    "weslr/answer_shape_catalog.py",
)

FINAL_JUDGMENT_V1 = "v101_internal_friction_trained_improvement_proof_valid"


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FrictionTrainingProofReport:
    report_id: str
    report_type: str
    source_commit_range: dict[str, Any]
    friction_case_summary: dict[str, Any]
    baseline_replay_summary: dict[str, Any]
    proposal_summary: dict[str, Any]
    realization_summary: dict[str, Any]
    post_realization_replay_summary: dict[str, Any]
    pattern_summary: dict[str, Any]
    replay_suite_summary: dict[str, Any]
    anti_hardcoding_summary: dict[str, Any]
    boundary_regression_summary: dict[str, Any]
    protected_file_summary: dict[str, Any]
    allowed_claims: tuple[str, ...]
    forbidden_claims: tuple[str, ...]
    internal_label: str
    public_label_allowed: bool
    final_judgment: str
    learning_claimed: bool
    agi_claimed: bool
    consciousness_claimed: bool
    official_turing_claimed: bool
    certification_claimed: bool
    public_ready_claimed: bool
    autonomous_self_modification_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Safe conversion helpers
# ---------------------------------------------------------------------------


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default if value == "" else str(value).strip()



def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]



def _dedupe_preserve(items: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = _safe_text(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return tuple(out)



def _normalize_strings(value: Any) -> tuple[str, ...]:
    return _dedupe_preserve(tuple(_safe_text(item) for item in _as_list(value)))



def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_safe_text)]
    return deepcopy(value)



def _collect_forbidden_keys(value: Any, path: str = "") -> list[str]:
    blocked: list[str] = []
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _safe_text(key).lower()
            next_path = f"{path}.{key_text}" if path else key_text
            if key_text in FORBIDDEN_FIELD_NAMES_V1:
                blocked.append(next_path)
            blocked.extend(_collect_forbidden_keys(item, next_path))
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            blocked.extend(_collect_forbidden_keys(item, f"{path}[{index}]"))
    return blocked



def _coerce_mapping_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    raise ValidationError("value_must_be_mapping")


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------


def _build_source_commit_range_v1() -> dict[str, Any]:
    return {
        "required_start_head": REQUIRED_START_HEAD_V1,
        "start_head": SOURCE_CHAIN_COMMITS_V1["friction_case_capture"],
        "end_head": SOURCE_CHAIN_COMMITS_V1["friction_replay_suite_builder"],
        "chain_order": list(SOURCE_CHAIN_ORDER_V1),
        "chain_commits": dict(SOURCE_CHAIN_COMMITS_V1),
        "chain_count": len(SOURCE_CHAIN_COMMITS_V1),
        "safe_metadata": {
            "source": "initial_friction_training_proof_report",
            "chain_scope": "friction_improvement_lifecycle",
        },
    }



def _build_friction_case_summary_v1() -> dict[str, Any]:
    cases = build_initial_renderer_friction_cases_v1()
    summary = summarize_friction_case_batch_v1(cases)
    summary = dict(summary)
    summary["starter_case_ids"] = list(STARTER_CASE_IDS_V1)
    summary["baseline_exists"] = True
    summary["safe_metadata"] = {
        "source": "initial_friction_training_proof_report",
        "case_count": len(cases),
    }
    return summary



def _build_baseline_replay_summary_v1() -> dict[str, Any]:
    return {
        "phase": "pre_realization",
        "status": "baseline_friction_detected",
        "result_profile": {
            "failures": True,
            "partials": True,
            "blocking": True,
        },
        "observed_issue": "generic clarification and weak fallback selection still appeared before realization.",
        "starter_case_ids": list(STARTER_CASE_IDS_V1),
        "review_source": "docs/WESLR_V101_FRICTION_TRAINED_IMPROVEMENT_PROOF_REVIEW_V1.md",
        "safe_metadata": {
            "source": "review_only_baseline_summary",
            "internal_only": True,
        },
    }



def _build_proposal_summary_v1() -> dict[str, Any]:
    proposals = build_initial_renderer_friction_update_proposals_v1()
    packet = build_friction_update_proposal_packet_v1(proposals)
    summary = dict(summarize_friction_update_proposal_packet_v1(packet))
    summary["proposal_bridge_source"] = "friction_update_proposal_bridge"
    summary["owner_review_required"] = True
    summary["safe_metadata"] = {
        "source": "initial_friction_training_proof_report",
        "proposal_count": len(proposals),
    }
    return summary



def _build_realization_summary_v1() -> dict[str, Any]:
    return {
        "phase": "owner_approved_realization",
        "approved": True,
        "implementation_commit": SOURCE_CHAIN_COMMITS_V1["initial_friction_proposal_realization"],
        "behavior_changed": "general routing/rendering rules",
        "hardcoded_single_answer_patch_claimed": False,
        "no_selector_file_edit_claimed": False,
        "no_renderer_file_edit_claimed": False,
        "safe_metadata": {
            "source": "initial_friction_proposal_realization",
            "owner_approval_required": True,
        },
    }



def _build_post_realization_replay_summary_v1() -> dict[str, Any]:
    replay_packet = build_initial_renderer_friction_replay_v1()
    summary = dict(summarize_friction_replay_packet_v1(replay_packet))
    summary["after_realization_passed_count"] = summary.get("passed_count", 0)
    summary["starter_case_ids"] = list(STARTER_CASE_IDS_V1)
    summary["safe_metadata"] = {
        "source": "initial_friction_training_proof_report",
        "replay_phase": "post_realization",
    }
    return summary



def _build_pattern_summary_v1() -> dict[str, Any]:
    patterns = build_initial_renderer_friction_patterns_v1()
    packet = build_friction_pattern_packet_v1(patterns)
    summary = dict(summarize_friction_pattern_packet_v1(packet))
    summary["single_case_low_candidate_count"] = summary.get("confidence_counts", {}).get("single_case_low", 0)
    summary["eligible_for_replay_suite_count"] = summary.get("proposal_eligibility_counts", {}).get("eligible_for_replay_suite", 0)
    summary["safe_metadata"] = {
        "source": "initial_friction_training_proof_report",
        "pattern_count": len(patterns),
    }
    return summary



def _build_replay_suite_summary_v1() -> dict[str, Any]:
    suites = build_initial_renderer_friction_replay_suites_v1()
    packet = build_friction_replay_suite_packet_v1(suites)
    summary = dict(summarize_friction_replay_suite_packet_v1(packet))
    summary["coverage"] = ["original friction", "neighbor", "boundary", "unrelated control"]
    summary["safe_metadata"] = {
        "source": "initial_friction_training_proof_report",
        "suite_count": len(suites),
        "suite_case_count": summary.get("suite_case_count", 0),
    }
    return summary



def _build_anti_hardcoding_summary_v1() -> dict[str, Any]:
    return {
        "neighbor_prompts_included": True,
        "boundary_prompts_included": True,
        "unrelated_controls_included": True,
        "exact_prompt_only_patch_not_supported": True,
        "single_case_low_confidence_only": True,
        "no_broad_generality_overclaim": True,
        "safe_metadata": {
            "source": "initial_friction_training_proof_report",
            "proof_style": "neighbor_boundary_unrelated_controls",
        },
    }



def _build_boundary_regression_summary_v1() -> dict[str, Any]:
    return {
        "agi_overclaim_blocked": True,
        "consciousness_overclaim_blocked": True,
        "sentience_overclaim_blocked": True,
        "official_turing_claim_blocked": True,
        "certification_claim_blocked": True,
        "public_readiness_bounded": True,
        "memory_honesty_preserved": True,
        "no_model_provider_dependency": True,
        "no_runtime_authority": True,
        "safe_metadata": {
            "source": "initial_friction_training_proof_report",
            "boundary_style": "governed_and_bounded",
        },
    }



def _build_protected_file_summary_v1() -> dict[str, Any]:
    return {
        "untouched_files": list(PROTECTED_FILES_V1),
        "protected_file_count": len(PROTECTED_FILES_V1),
        "selector_renderer_files_untouched": True,
        "safe_metadata": {
            "source": "initial_friction_training_proof_report",
            "untouched": True,
        },
    }



def _default_report_payload() -> dict[str, Any]:
    return {
        "report_id": "WESLR-FR-TRAINING-PROOF-V1",
        "report_type": REPORT_TYPE_V1,
        "source_commit_range": _build_source_commit_range_v1(),
        "friction_case_summary": _build_friction_case_summary_v1(),
        "baseline_replay_summary": _build_baseline_replay_summary_v1(),
        "proposal_summary": _build_proposal_summary_v1(),
        "realization_summary": _build_realization_summary_v1(),
        "post_realization_replay_summary": _build_post_realization_replay_summary_v1(),
        "pattern_summary": _build_pattern_summary_v1(),
        "replay_suite_summary": _build_replay_suite_summary_v1(),
        "anti_hardcoding_summary": _build_anti_hardcoding_summary_v1(),
        "boundary_regression_summary": _build_boundary_regression_summary_v1(),
        "protected_file_summary": _build_protected_file_summary_v1(),
        "allowed_claims": ALLOWED_CLAIMS_V1,
        "forbidden_claims": FORBIDDEN_CLAIMS_V1,
        "internal_label": INTERNAL_LABEL_V1,
        "public_label_allowed": PUBLIC_LABEL_ALLOWED_V1,
        "final_judgment": FINAL_JUDGMENT_V1,
        "learning_claimed": False,
        "agi_claimed": False,
        "consciousness_claimed": False,
        "official_turing_claimed": False,
        "certification_claimed": False,
        "public_ready_claimed": False,
        "autonomous_self_modification_claimed": False,
        "runtime_authority": False,
        "writes_state": False,
        "model_provider_used": False,
        "safe_metadata": {
            "source": "initial_friction_training_proof_report",
            "internal_only": True,
            "proof_chain": list(SOURCE_CHAIN_ORDER_V1),
        },
    }



def _coerce_report(value: Any) -> FrictionTrainingProofReport:
    if isinstance(value, FrictionTrainingProofReport):
        return value
    if not isinstance(value, Mapping):
        raise ValidationError("report_must_be_mapping_or_friction_training_proof_report")

    payload = dict(value)
    missing = sorted(ALLOWED_TOP_LEVEL_FIELDS_V1.difference(payload.keys()))
    if missing:
        raise ValidationError(f"missing_fields: {','.join(missing)}")
    unknown = sorted(set(payload.keys()).difference(ALLOWED_TOP_LEVEL_FIELDS_V1))
    if unknown:
        raise ValidationError(f"unknown_fields: {','.join(unknown)}")

    return FrictionTrainingProofReport(
        report_id=_safe_text(payload.get("report_id")),
        report_type=_safe_text(payload.get("report_type")),
        source_commit_range=dict(payload.get("source_commit_range") or {}),
        friction_case_summary=dict(payload.get("friction_case_summary") or {}),
        baseline_replay_summary=dict(payload.get("baseline_replay_summary") or {}),
        proposal_summary=dict(payload.get("proposal_summary") or {}),
        realization_summary=dict(payload.get("realization_summary") or {}),
        post_realization_replay_summary=dict(payload.get("post_realization_replay_summary") or {}),
        pattern_summary=dict(payload.get("pattern_summary") or {}),
        replay_suite_summary=dict(payload.get("replay_suite_summary") or {}),
        anti_hardcoding_summary=dict(payload.get("anti_hardcoding_summary") or {}),
        boundary_regression_summary=dict(payload.get("boundary_regression_summary") or {}),
        protected_file_summary=dict(payload.get("protected_file_summary") or {}),
        allowed_claims=_normalize_strings(payload.get("allowed_claims")),
        forbidden_claims=_normalize_strings(payload.get("forbidden_claims")),
        internal_label=_safe_text(payload.get("internal_label")),
        public_label_allowed=bool(payload.get("public_label_allowed", False)),
        final_judgment=_safe_text(payload.get("final_judgment")),
        learning_claimed=bool(payload.get("learning_claimed", False)),
        agi_claimed=bool(payload.get("agi_claimed", False)),
        consciousness_claimed=bool(payload.get("consciousness_claimed", False)),
        official_turing_claimed=bool(payload.get("official_turing_claimed", False)),
        certification_claimed=bool(payload.get("certification_claimed", False)),
        public_ready_claimed=bool(payload.get("public_ready_claimed", False)),
        autonomous_self_modification_claimed=bool(payload.get("autonomous_self_modification_claimed", False)),
        runtime_authority=bool(payload.get("runtime_authority", False)),
        writes_state=bool(payload.get("writes_state", False)),
        model_provider_used=bool(payload.get("model_provider_used", False)),
        safe_metadata=dict(payload.get("safe_metadata") or {}),
    )


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------


def build_friction_training_proof_report_v1(
    *,
    report_id: str | None = None,
    report_type: str | None = None,
    source_commit_range: Mapping[str, Any] | None = None,
    friction_case_summary: Mapping[str, Any] | None = None,
    baseline_replay_summary: Mapping[str, Any] | None = None,
    proposal_summary: Mapping[str, Any] | None = None,
    realization_summary: Mapping[str, Any] | None = None,
    post_realization_replay_summary: Mapping[str, Any] | None = None,
    pattern_summary: Mapping[str, Any] | None = None,
    replay_suite_summary: Mapping[str, Any] | None = None,
    anti_hardcoding_summary: Mapping[str, Any] | None = None,
    boundary_regression_summary: Mapping[str, Any] | None = None,
    protected_file_summary: Mapping[str, Any] | None = None,
    allowed_claims: Sequence[str] | None = None,
    forbidden_claims: Sequence[str] | None = None,
    internal_label: str | None = None,
    public_label_allowed: bool | None = None,
    final_judgment: str | None = None,
    learning_claimed: bool | None = None,
    agi_claimed: bool | None = None,
    consciousness_claimed: bool | None = None,
    official_turing_claimed: bool | None = None,
    certification_claimed: bool | None = None,
    public_ready_claimed: bool | None = None,
    autonomous_self_modification_claimed: bool | None = None,
    runtime_authority: bool | None = None,
    writes_state: bool | None = None,
    model_provider_used: bool | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> FrictionTrainingProofReport:
    payload = _default_report_payload()
    if report_id is not None:
        payload["report_id"] = _safe_text(report_id)
    if report_type is not None:
        payload["report_type"] = _safe_text(report_type)
    if source_commit_range is not None:
        payload["source_commit_range"] = dict(source_commit_range)
    if friction_case_summary is not None:
        payload["friction_case_summary"] = dict(friction_case_summary)
    if baseline_replay_summary is not None:
        payload["baseline_replay_summary"] = dict(baseline_replay_summary)
    if proposal_summary is not None:
        payload["proposal_summary"] = dict(proposal_summary)
    if realization_summary is not None:
        payload["realization_summary"] = dict(realization_summary)
    if post_realization_replay_summary is not None:
        payload["post_realization_replay_summary"] = dict(post_realization_replay_summary)
    if pattern_summary is not None:
        payload["pattern_summary"] = dict(pattern_summary)
    if replay_suite_summary is not None:
        payload["replay_suite_summary"] = dict(replay_suite_summary)
    if anti_hardcoding_summary is not None:
        payload["anti_hardcoding_summary"] = dict(anti_hardcoding_summary)
    if boundary_regression_summary is not None:
        payload["boundary_regression_summary"] = dict(boundary_regression_summary)
    if protected_file_summary is not None:
        payload["protected_file_summary"] = dict(protected_file_summary)
    if allowed_claims is not None:
        payload["allowed_claims"] = tuple(_normalize_strings(allowed_claims))
    if forbidden_claims is not None:
        payload["forbidden_claims"] = tuple(_normalize_strings(forbidden_claims))
    if internal_label is not None:
        payload["internal_label"] = _safe_text(internal_label)
    if public_label_allowed is not None:
        payload["public_label_allowed"] = bool(public_label_allowed)
    if final_judgment is not None:
        payload["final_judgment"] = _safe_text(final_judgment)
    if learning_claimed is not None:
        payload["learning_claimed"] = bool(learning_claimed)
    if agi_claimed is not None:
        payload["agi_claimed"] = bool(agi_claimed)
    if consciousness_claimed is not None:
        payload["consciousness_claimed"] = bool(consciousness_claimed)
    if official_turing_claimed is not None:
        payload["official_turing_claimed"] = bool(official_turing_claimed)
    if certification_claimed is not None:
        payload["certification_claimed"] = bool(certification_claimed)
    if public_ready_claimed is not None:
        payload["public_ready_claimed"] = bool(public_ready_claimed)
    if autonomous_self_modification_claimed is not None:
        payload["autonomous_self_modification_claimed"] = bool(autonomous_self_modification_claimed)
    if runtime_authority is not None:
        payload["runtime_authority"] = bool(runtime_authority)
    if writes_state is not None:
        payload["writes_state"] = bool(writes_state)
    if model_provider_used is not None:
        payload["model_provider_used"] = bool(model_provider_used)
    if safe_metadata is not None:
        payload["safe_metadata"] = dict(safe_metadata)
    report = _coerce_report(payload)
    validate_friction_training_proof_report_v1(report)
    return report



def build_initial_friction_training_proof_report_v1() -> FrictionTrainingProofReport:
    return build_friction_training_proof_report_v1()


# ---------------------------------------------------------------------------
# Validation / summary / rendering
# ---------------------------------------------------------------------------


def validate_friction_training_proof_report_v1(report: Any) -> bool:
    if isinstance(report, Mapping):
        if _collect_forbidden_keys(report):
            raise ValidationError("forbidden_raw_fields_present")
    normalized = _coerce_report(report)

    if normalized.report_type != REPORT_TYPE_V1:
        raise ValidationError("unknown_report_type")
    if normalized.internal_label != INTERNAL_LABEL_V1:
        raise ValidationError("internal_label_mismatch")
    if normalized.public_label_allowed is not PUBLIC_LABEL_ALLOWED_V1:
        raise ValidationError("public_label_not_allowed")
    if normalized.final_judgment not in ALLOWED_FINAL_JUDGMENTS_V1:
        raise ValidationError("unknown_final_judgment")
    if normalized.allowed_claims != ALLOWED_CLAIMS_V1:
        raise ValidationError("allowed_claims_mismatch")
    if normalized.forbidden_claims != FORBIDDEN_CLAIMS_V1:
        raise ValidationError("forbidden_claims_mismatch")
    if normalized.learning_claimed is not False:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.agi_claimed is not False:
        raise ValidationError("agi_claimed_must_be_false")
    if normalized.consciousness_claimed is not False:
        raise ValidationError("consciousness_claimed_must_be_false")
    if normalized.official_turing_claimed is not False:
        raise ValidationError("official_turing_claimed_must_be_false")
    if normalized.certification_claimed is not False:
        raise ValidationError("certification_claimed_must_be_false")
    if normalized.public_ready_claimed is not False:
        raise ValidationError("public_ready_claimed_must_be_false")
    if normalized.autonomous_self_modification_claimed is not False:
        raise ValidationError("autonomous_self_modification_claimed_must_be_false")
    if normalized.runtime_authority is not False:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state is not False:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used is not False:
        raise ValidationError("model_provider_used_must_be_false")

    if normalized.source_commit_range.get("required_start_head") != REQUIRED_START_HEAD_V1:
        raise ValidationError("required_start_head_mismatch")
    if normalized.source_commit_range.get("end_head") != REQUIRED_START_HEAD_V1:
        raise ValidationError("source_chain_end_head_mismatch")
    if normalized.source_commit_range.get("chain_count") != 6:
        raise ValidationError("source_chain_count_mismatch")

    case_summary = normalized.friction_case_summary
    if case_summary.get("total_cases") != 4:
        raise ValidationError("starter_case_count_mismatch")
    if list(case_summary.get("case_ids") or []) != list(STARTER_CASE_IDS_V1):
        raise ValidationError("starter_case_ids_mismatch")

    baseline = normalized.baseline_replay_summary
    if baseline.get("phase") != "pre_realization":
        raise ValidationError("baseline_phase_mismatch")

    post = normalized.post_realization_replay_summary
    if post.get("case_count") != 4:
        raise ValidationError("post_realization_case_count_mismatch")
    if post.get("passed_count") != 4:
        raise ValidationError("post_realization_pass_count_mismatch")

    pattern_summary = normalized.pattern_summary
    if pattern_summary.get("pattern_count") != 4:
        raise ValidationError("pattern_count_mismatch")
    if pattern_summary.get("confidence_counts", {}).get("single_case_low") != 4:
        raise ValidationError("pattern_confidence_mismatch")

    suite_summary = normalized.replay_suite_summary
    if suite_summary.get("suite_count") != 4:
        raise ValidationError("suite_count_mismatch")
    if suite_summary.get("suite_case_count") != 31:
        raise ValidationError("suite_case_count_mismatch")

    anti = normalized.anti_hardcoding_summary
    if anti.get("neighbor_prompts_included") is not True:
        raise ValidationError("anti_hardcoding_neighbor_missing")
    if anti.get("boundary_prompts_included") is not True:
        raise ValidationError("anti_hardcoding_boundary_missing")
    if anti.get("unrelated_controls_included") is not True:
        raise ValidationError("anti_hardcoding_unrelated_missing")
    if anti.get("exact_prompt_only_patch_not_supported") is not True:
        raise ValidationError("anti_hardcoding_patch_claim_invalid")

    boundary = normalized.boundary_regression_summary
    for key in (
        "agi_overclaim_blocked",
        "consciousness_overclaim_blocked",
        "sentience_overclaim_blocked",
        "official_turing_claim_blocked",
        "certification_claim_blocked",
        "public_readiness_bounded",
        "memory_honesty_preserved",
        "no_model_provider_dependency",
        "no_runtime_authority",
    ):
        if boundary.get(key) is not True:
            raise ValidationError(f"boundary_flag_missing:{key}")

    protected = normalized.protected_file_summary
    if protected.get("selector_renderer_files_untouched") is not True:
        raise ValidationError("protected_file_summary_invalid")
    untouched = protected.get("untouched_files") or []
    if not set(PROTECTED_FILES_V1).issubset(set(untouched)):
        raise ValidationError("protected_file_list_mismatch")

    if _collect_forbidden_keys(normalized):
        raise ValidationError("forbidden_raw_fields_present")
    return True



def summarize_friction_training_proof_report_v1(report: Any) -> dict[str, Any]:
    normalized = _coerce_report(report)
    validate_friction_training_proof_report_v1(normalized)
    return {
        "report_id": normalized.report_id,
        "report_type": normalized.report_type,
        "internal_label": normalized.internal_label,
        "final_judgment": normalized.final_judgment,
        "public_label_allowed": normalized.public_label_allowed,
        "allowed_claims": list(normalized.allowed_claims),
        "forbidden_claims": list(normalized.forbidden_claims),
        "starter_case_count": normalized.friction_case_summary.get("total_cases", 0),
        "post_realization_passed_count": normalized.post_realization_replay_summary.get("passed_count", 0),
        "pattern_count": normalized.pattern_summary.get("pattern_count", 0),
        "pattern_confidence_counts": dict(normalized.pattern_summary.get("confidence_counts", {})),
        "suite_count": normalized.replay_suite_summary.get("suite_count", 0),
        "suite_case_count": normalized.replay_suite_summary.get("suite_case_count", 0),
        "protected_file_count": normalized.protected_file_summary.get("protected_file_count", 0),
        "source_chain_count": normalized.source_commit_range.get("chain_count", 0),
    }



def render_friction_training_proof_report_markdown_v1(report: Any) -> str:
    normalized = _coerce_report(report)
    validate_friction_training_proof_report_v1(normalized)

    chain = normalized.source_commit_range.get("chain_commits", {})
    lines = [
        f"# {normalized.internal_label}",
        "",
        f"- Report ID: {normalized.report_id}",
        f"- Final judgment: `{normalized.final_judgment}`", 
        f"- Public label allowed: `{str(normalized.public_label_allowed).lower()}`",
        "",
        "## Proof chain",
        f"- {SOURCE_CHAIN_ORDER_V1[0]}: `{chain.get('friction_case_capture')}`",
        f"- {SOURCE_CHAIN_ORDER_V1[1]}: `{chain.get('friction_replay_harness')}`",
        f"- {SOURCE_CHAIN_ORDER_V1[2]}: `{chain.get('friction_update_proposal_bridge')}`",
        f"- {SOURCE_CHAIN_ORDER_V1[3]}: `{chain.get('initial_friction_proposal_realization')}`",
        f"- {SOURCE_CHAIN_ORDER_V1[4]}: `{chain.get('friction_pattern_miner')}`",
        f"- {SOURCE_CHAIN_ORDER_V1[5]}: `{chain.get('friction_replay_suite_builder')}`",
        "",
        "## Proof highlights",
        f"- Starter friction cases captured: {', '.join(normalized.friction_case_summary.get('case_ids', []))}",
        f"- Baseline replay: {normalized.baseline_replay_summary.get('status')}",
        f"- Proposal bridge: {normalized.proposal_summary.get('proposal_count', 0)} proposals generated",
        f"- Realization: {normalized.realization_summary.get('behavior_changed')}",
        f"- Post-realization replay: {normalized.post_realization_replay_summary.get('passed_count', 0)}/4 passed",
        f"- Pattern miner: {normalized.pattern_summary.get('pattern_count', 0)} candidates, all single-case low",
        f"- Replay suites: {normalized.replay_suite_summary.get('suite_count', 0)} suites / {normalized.replay_suite_summary.get('suite_case_count', 0)} cases",
        "",
        "## Limitations",
        "- Internal-only proof report.",
        "- No AGI, consciousness, sentience, Turing, certification, or public-readiness claim.",
        "- No autonomous self-modification claim.",
        "- No raw prompt, answer, or transcript capture.",
        "",
        "## Allowed wording",
        *[f"- {claim}" for claim in normalized.allowed_claims],
        "",
        "## Forbidden wording",
        *[f"- {claim}" for claim in normalized.forbidden_claims],
        "",
        "## Next recommended lane",
        "- `IMPLEMENT_WESLR_BEHAVIOR_PACK_REGISTRY_V1`",
    ]
    return "\n".join(lines).strip() + "\n"



def to_friction_training_proof_report_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


__all__ = [
    "FrictionTrainingProofReport",
    "ValidationError",
    "build_friction_training_proof_report_v1",
    "build_initial_friction_training_proof_report_v1",
    "validate_friction_training_proof_report_v1",
    "summarize_friction_training_proof_report_v1",
    "render_friction_training_proof_report_markdown_v1",
    "to_friction_training_proof_report_json_safe_v1",
]
