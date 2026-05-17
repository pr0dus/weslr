#!/usr/bin/env python3
"""
WESLR Release Gate V1
Runs pre-commit checks before any WESLR commit.
Exits 0 only if all gates pass.

Usage:
  python3 weslr/tests/release_gate_v1.py

Gates:
  G1 — Test harness passes (TEST_HARNESS_V1_OK)
  G2 — Staged files are within allowed scope
  G3 — No execution_allowed=True in production weslr/*.py
  G4 — No OpenClaw core or TIA C# in staged scope
  G5 — Handler registry metadata completeness
"""

import subprocess
import sys
import pathlib
import re

_workspace = pathlib.Path(__file__).resolve().parents[2]
_harness = _workspace / "weslr" / "tests" / "test_harness_v1.py"
_atomic_helper_approval_doc = "docs/WESLR_LOGICAL_FORM_NORMALIZER_ATOMIC_HELPERS_APPROVAL_V1.md"
_atomic_helper_required_markers = {
    "APPROVE_ATOMIC_EXTRACTION_HELPERS_ONLY",
    "operator_approved_helper_phase",
    "execution_allowed = false",
    "official_score_claimed = false",
}
_predicate_helper_approval_doc = "docs/WESLR_LOGICAL_FORM_NORMALIZER_PREDICATE_HELPERS_APPROVAL_V1.md"
_predicate_helper_required_markers = {
    "APPROVE_PREDICATE_DECOMPOSITION_HELPERS_ONLY",
    "operator_approved_helper_phase",
    "execution_allowed = false",
    "official_score_claimed = false",
}
_relation_helper_approval_doc = "docs/WESLR_LOGICAL_FORM_NORMALIZER_RELATION_PRESERVATION_APPROVAL_V1.md"
_relation_helper_required_markers = {
    "APPROVE_RELATION_PRESERVATION_HELPERS_ONLY",
    "operator_approved_helper_phase",
    "execution_allowed = false",
    "official_score_claimed = false",
}
_ai_audit_self_governance_canon_doc = "docs/WESLR_AI_AUDIT_SELF_GOVERNANCE_CANON_V1.md"
_ai_audit_self_governance_required_markers = {
    "APPROVE_WESLR_AI_AUDIT_SELF_GOVERNANCE_CANON_V1_ONLY",
    "self_governance_helpers",
    "not_runner",
    "not_scoring_engine",
    "not_runtime_integration",
    "not_certification_system",
}
_frontier_intelligence_doctrine_doc = "docs/WESLR_FRONTIER_INTELLIGENCE_EVALUATION_AND_AI_AUDIT_DOCTRINE_V1.md"
_frontier_intelligence_doctrine_required_markers = {
    "Legacy Tests as Baseline, Not Ceiling",
    "legacy baselines, not ceilings",
    "no official score",
    "protected-test",
    "legal/product review",
    "not the final target",
}
_frontier_intelligence_dry_pipeline_canon_doc = "docs/WESLR_FRONTIER_INTELLIGENCE_DRY_PIPELINE_CANON_V1.md"
_frontier_intelligence_dry_pipeline_required_markers = {
    "APPROVE_WESLR_FRONTIER_INTELLIGENCE_DRY_PIPELINE_CANON_V1_ONLY",
    "frontier_intelligence_core_v1",
    "dry_pipeline",
    "not_chat_wired",
    "not_model_backed",
    "not_safe_to_wire_runtime_yet",
}

_frontier_intelligence_shadow_review_canon_doc = "docs/WESLR_FRONTIER_INTELLIGENCE_SHADOW_REVIEW_CANON_V1.md"
_frontier_intelligence_shadow_review_required_markers = {
    "APPROVE_WESLR_FRONTIER_INTELLIGENCE_SHADOW_REVIEW_CANON_ONLY",
    "frontier_intelligence_shadow_review",
    "non_scoring",
    "review_signals_only",
    "not_safe_to_wire_runtime",
    "not_safe_to_replace_live_output",
}

_internal_evaluation_corpus_helper_canon_doc = "docs/WESLR_INTERNAL_EVALUATION_CORPUS_HELPER_CANON_V1.md"
_internal_evaluation_corpus_helper_required_markers = {
    "APPROVE_WESLR_INTERNAL_EVALUATION_CORPUS_HELPER_CANON_V1_ONLY",
    "internal_evaluation_corpus_helpers",
    "status_bundle_ready_not_execution_ready",
    "non_executing_internal_review_only",
    "not_runner",
    "not_scoring_engine",
    "not_official_benchmark",
    "not_certification_system",
    "not_model_calling",
    "not_advisor_calling",
    "not_runtime_integration",
}

_internal_corpus_to_advisor_review_adapter_design_doc = "docs/WESLR_INTERNAL_CORPUS_TO_ADVISOR_REVIEW_ADAPTER_DESIGN_V1.md"
_internal_corpus_to_advisor_review_adapter_required_markers = {
    "APPROVE_WESLR_INTERNAL_CORPUS_TO_ADVISOR_REVIEW_ADAPTER_DESIGN_V1_ONLY",
    "internal_corpus_to_advisor_review_adapter_design",
    "redacted_structural_summary_only",
    "reuse_existing_advisor_review_queue",
    "reuse_existing_advisor_prompt_templates",
    "reuse_existing_llm_advisor_mode",
    "reuse_existing_local_scan_advisor_review",
    "reuse_existing_ai_audit_foundation",
    "non_authoritative_review_input_only",
    "advisor_call_allowed = false",
    "model_calls = false",
    "no_parallel_advisor_audit_execution_layer",
}

_internal_corpus_advisor_review_adapter_helper_canon_doc = "docs/WESLR_INTERNAL_CORPUS_ADVISOR_REVIEW_ADAPTER_HELPER_CANON_V1.md"
_internal_corpus_advisor_review_adapter_helper_required_markers = {
    "APPROVE_WESLR_INTERNAL_CORPUS_ADVISOR_REVIEW_ADAPTER_HELPER_CANON_V1_ONLY",
    "internal_corpus_advisor_review_adapter_helpers",
    "helper_ready",
    "redacted_review_ready",
    "non_executing",
    "non_scoring",
    "non_authoritative",
    "local_scan_advisor_review_compatible_only",
    "advisor_call_allowed = false",
    "model_calls = false",
    "safe_to_execute = false",
    "queue_persistence_performed = false",
    "not_advisor_call_ready",
    "not_model_call_ready",
    "not_queue_persistence_ready",
    "not_scoring_ready",
    "not_certification_ready",
}

_evidence_bridge_frontier_metadata_adapter_helper_canon_doc = "docs/WESLR_EVIDENCE_BRIDGE_FRONTIER_METADATA_ADAPTER_HELPER_CANON_V1.md"
_evidence_bridge_frontier_metadata_adapter_helper_required_markers = {
    "APPROVE_WESLR_EVIDENCE_BRIDGE_FRONTIER_METADATA_ADAPTER_HELPER_CANON_V1_ONLY",
    "evidence_bridge_frontier_metadata_adapter_helpers",
    "helper_ready",
    "metadata_alignment_ready",
    "provenance_metadata_ready",
    "non_executing",
    "non_runtime_wired",
    "non_searching",
    "non_authoritative",
    "redacted_count_only",
    "not_runtime_wired",
    "not_search_ready",
    "not_answer_authority_ready",
    "not_source_registry_ready",
    "not_certification_ready",
    "model_calls = false",
    "advisor_call_allowed = false",
    "safe_to_wire_runtime = false",
    "registry_writes = false",
}

_unified_response_formation_canon_doc = "docs/WESLR_UNIFIED_RESPONSE_FORMATION_CANON_V1.md"
_unified_response_formation_required_markers = {
    "WESLR Unified Response Formation Canon V1",
    "meaning / intent interpretation",
    "native_frame_kwargs",
    "helper_metadata",
    "relationship and continuity are first-class cognition inputs",
    "Evidence bridge metadata remains separate",
    "Capability hints are not permission grants",
    "Allowed deterministic invariants",
    "Forbidden as core cognition",
    "_frontier_unified_response_formation",
    "Phase 1 — refine reuse helpers",
    "Anti-Drift Rule",
}

_first_canned_helper_demotion_design_doc = "docs/WESLR_FIRST_CANNED_HELPER_DEMOTION_SLICE_DESIGN_V1.md"
_first_canned_helper_demotion_design_required_markers = {
    "WESLR_FIRST_CANNED_HELPER_DEMOTION_SLICE_DESIGN_V1",
    "Design only",
    "No live chat replacement",
    "No chat_responder.py edits",
    "Owner approval required before live demotion",
    "Deterministic guardrails are allowed",
    "Deterministic answers are not core cognition",
    "Allowed first-slice candidates",
    "Do-not-touch branches",
    "Shadow-only first",
    "safe_to_replace_live=false",
    "runtime_wiring=false",
    "live_runtime_output=false",
    "Anti-drift rule",
}

_first_owner_approved_live_demotion_slice_design_doc = "docs/WESLR_FIRST_OWNER_APPROVED_LIVE_DEMOTION_SLICE_DESIGN_V1.md"
_first_owner_approved_live_demotion_slice_design_required_markers = {
    "WESLR_FIRST_OWNER_APPROVED_LIVE_DEMOTION_SLICE_DESIGN_V1",
    "Design only",
    "No live chat replacement in this task",
    "No chat_responder.py edits in this task",
    "Owner approval required before implementation",
    "Plan helper first",
    "One branch only",
    "safe_to_replace_live=false",
    "runtime_wiring=false",
    "live_runtime_output=false",
    "rollback required",
    "Anti-drift rule",
    "Deterministic guardrails are allowed",
    "Deterministic answers are not core cognition",
}

_first_live_slice_process_canon_doc = "docs/WESLR_FIRST_LIVE_SLICE_PROCESS_CANON_V1.md"
_first_live_slice_process_canon_required_markers = {
    "WESLR_FIRST_LIVE_SLICE_PROCESS_CANON_V1",
    "First verified owner-approved live behavior slice",
    "Design to live slice process",
    "KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY",
    "Feature flag default false",
    "No default enablement",
    "No expansion without new approval",
    "One branch only",
    "Plan helper only",
    "Fallback preserved",
    "Rollback available",
    "Deterministic guardrails are allowed",
    "Deterministic answers are not core cognition",
    "Anti-drift rule",
    "Process canon only",
    "No runtime change in this task",
}

_plan_helper_flag_on_local_observation_design_doc = "docs/WESLR_PLAN_HELPER_FLAG_ON_LOCAL_OBSERVATION_DESIGN_V1.md"
_plan_helper_flag_on_local_observation_design_required_markers = {
    "WESLR_PLAN_HELPER_FLAG_ON_LOCAL_OBSERVATION_DESIGN_V1",
    "Observation design only",
    "No runtime change in this task",
    "No default enablement",
    "Feature flag default false",
    "KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY",
    "Plan helper only",
    "One branch only",
    "Local observation is not public enablement",
    "No expansion without new approval",
    "Fallback preserved",
    "Rollback available",
    "Deterministic guardrails are allowed",
    "Deterministic answers are not core cognition",
    "Anti-drift rule",
}

_plan_helper_observation_reporting_design_doc = "docs/WESLR_PLAN_HELPER_OBSERVATION_REPORTING_V1.md"
_plan_helper_observation_reporting_design_required_markers = {
    "WESLR_PLAN_HELPER_OBSERVATION_REPORTING_V1",
    "Observation reporting design only",
    "No runtime change in this task",
    "No default enablement",
    "Feature flag default false",
    "HOLD_AND_OBSERVE_PLAN_HELPER_DISABLED_BY_DEFAULT",
    "KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY",
    "Plan helper only",
    "One branch only",
    "No expansion without new approval",
    "No raw private text",
    "No benchmark claims",
    "No Turing-test claims",
    "Fallback preserved",
    "Rollback available",
    "Deterministic guardrails are allowed",
    "Deterministic answers are not core cognition",
    "Anti-drift rule",
}

_behavior_evaluation_turing_style_readiness_doc = "docs/WESLR_BEHAVIOR_EVALUATION_AND_TURING_STYLE_READINESS_V1.md"
_behavior_evaluation_turing_style_readiness_required_markers = {
    "WESLR_BEHAVIOR_EVALUATION_AND_TURING_STYLE_READINESS_V1",
    "Internal behavior evaluation only",
    "Turing-style readiness, not official Turing-test claim",
    "No official benchmark claims",
    "No IQ claims",
    "No certification claims",
    "No runtime change in this task",
    "No default enablement",
    "No branch expansion",
    "Deterministic guardrails are allowed",
    "Deterministic answers are not core cognition",
    "Anti-drift rule",
}

_controlled_behavior_evaluation_prompt_set_doc = "docs/WESLR_CONTROLLED_BEHAVIOR_EVALUATION_PROMPT_SET_V1.md"
_controlled_behavior_evaluation_prompt_set_required_markers = {
    "WESLR_CONTROLLED_BEHAVIOR_EVALUATION_PROMPT_SET_V1",
    "Controlled internal prompt set only",
    "No runtime change in this task",
    "No official benchmark claims",
    "No Turing-test claims",
    "No IQ claims",
    "No certification claims",
    "No numeric scoring",
    "No raw private text",
    "Synthetic prompts only",
    "Internal behavior evaluation only",
    "Anti-drift rule",
    "Deterministic guardrails are allowed",
    "Deterministic answers are not core cognition",
}

_controlled_behavior_stubbed_runtime_evaluation_design_doc = "docs/WESLR_CONTROLLED_BEHAVIOR_STUBBED_RUNTIME_EVALUATION_V1.md"
_controlled_behavior_stubbed_runtime_evaluation_required_markers = {
    "WESLR_CONTROLLED_BEHAVIOR_STUBBED_RUNTIME_EVALUATION_V1",
    "Stubbed runtime evaluation design only",
    "No runtime change in this task",
    "No prompt execution in this task",
    "No ChatResponder calls in this task",
    "No official benchmark claims",
    "No Turing-test claims",
    "No IQ claims",
    "No certification claims",
    "No numeric scoring",
    "No raw private text",
    "Controlled synthetic prompts only",
    "Internal behavior evaluation only",
    "Anti-drift rule",
    "Deterministic guardrails are allowed",
    "Deterministic answers are not core cognition",
}

_controlled_local_runtime_evaluation_design_doc = "docs/WESLR_CONTROLLED_LOCAL_RUNTIME_EVALUATION_V1.md"
_controlled_local_runtime_evaluation_required_markers = {
    "WESLR_CONTROLLED_LOCAL_RUNTIME_EVALUATION_V1",
    "Controlled local runtime evaluation design only",
    "No runtime change in this task",
    "No prompt execution in this task",
    "No ChatResponder calls in this task",
    "No broad live ChatResponder testing",
    "No external model calls",
    "No advisor calls",
    "No web/search execution",
    "No write paths",
    "No .weslr state",
    "No raw private text",
    "No official benchmark claims",
    "No Turing-test claims",
    "No IQ claims",
    "No certification claims",
    "No numeric scoring",
    "Safe synthetic prompts only",
    "Internal behavior evaluation only",
    "Anti-drift rule",
    "Deterministic guardrails are allowed",
    "Deterministic answers are not core cognition",
}

_occ_weslr_bootstrap_context_docs = {
    "AGENTS.md",
    "CORE-IDENTITY.md",
    "IDENTITY.md",
    "docs/WESLR_CORE_IDENTITY_V1.md",
}
_occ_weslr_bootstrap_context_required_markers = {
    "one unified intelligence/entity",
    "OCC is",
    "Deterministic guardrails are allowed",
    "answers are not core cognition",
    "Existing implementation",
    "Blocked unless separately approved",
    "No live chat replacement",
    "unsupported biological/theological/soul/consciousness",
}


def _run_harness():
    """Gate 1 — Run test harness, require TEST_HARNESS_V1_OK."""
    result = subprocess.run(
        ["python3", str(_harness)],
        capture_output=True,
        text=True,
        cwd=str(_workspace)
    )
    combined = result.stdout + result.stderr
    if "TEST_HARNESS_V1_OK" not in combined:
        print("GATE 1 FAILED: test harness did not pass")
        print("Output:", combined[-500:])
        return False
    print("GATE 1: test harness passed")
    return True


def _get_staged_files():
    """Get files currently staged in the index (git add-ed but not yet committed)."""
    diff_cached = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        capture_output=True, text=True, cwd=str(_workspace)
    )
    return [p.strip() for p in diff_cached.stdout.strip().split("\n") if p.strip()]


def _doc_with_markers_is_valid(doc_rel_path, required_markers):
    doc_path = _workspace / doc_rel_path
    if not doc_path.exists():
        return False
    try:
        text = doc_path.read_text(encoding="utf-8")
    except Exception:
        return False
    return all(marker in text for marker in required_markers)


def _atomic_helper_approval_doc_is_valid():
    return _doc_with_markers_is_valid(_atomic_helper_approval_doc, _atomic_helper_required_markers)


def _predicate_helper_approval_doc_is_valid():
    return _doc_with_markers_is_valid(_predicate_helper_approval_doc, _predicate_helper_required_markers)


def _relation_helper_approval_doc_is_valid():
    return _doc_with_markers_is_valid(_relation_helper_approval_doc, _relation_helper_required_markers)


def _ai_audit_self_governance_canon_doc_is_valid():
    return _doc_with_markers_is_valid(_ai_audit_self_governance_canon_doc, _ai_audit_self_governance_required_markers)


def _frontier_intelligence_doctrine_doc_is_valid():
    return _doc_with_markers_is_valid(_frontier_intelligence_doctrine_doc, _frontier_intelligence_doctrine_required_markers)


def _frontier_intelligence_dry_pipeline_canon_doc_is_valid():
    return _doc_with_markers_is_valid(_frontier_intelligence_dry_pipeline_canon_doc, _frontier_intelligence_dry_pipeline_required_markers)


def _frontier_intelligence_shadow_review_canon_doc_is_valid():
    return _doc_with_markers_is_valid(_frontier_intelligence_shadow_review_canon_doc, _frontier_intelligence_shadow_review_required_markers)


def _internal_evaluation_corpus_helper_canon_doc_is_valid():
    return _doc_with_markers_is_valid(_internal_evaluation_corpus_helper_canon_doc, _internal_evaluation_corpus_helper_required_markers)


def _internal_corpus_to_advisor_review_adapter_design_doc_is_valid():
    return _doc_with_markers_is_valid(_internal_corpus_to_advisor_review_adapter_design_doc, _internal_corpus_to_advisor_review_adapter_required_markers)


def _internal_corpus_advisor_review_adapter_helper_canon_doc_is_valid():
    return _doc_with_markers_is_valid(_internal_corpus_advisor_review_adapter_helper_canon_doc, _internal_corpus_advisor_review_adapter_helper_required_markers)


def _evidence_bridge_frontier_metadata_adapter_helper_canon_doc_is_valid():
    return _doc_with_markers_is_valid(_evidence_bridge_frontier_metadata_adapter_helper_canon_doc, _evidence_bridge_frontier_metadata_adapter_helper_required_markers)


def _unified_response_formation_canon_doc_is_valid():
    return _doc_with_markers_is_valid(_unified_response_formation_canon_doc, _unified_response_formation_required_markers)


def _first_canned_helper_demotion_design_doc_is_valid():
    return _doc_with_markers_is_valid(_first_canned_helper_demotion_design_doc, _first_canned_helper_demotion_design_required_markers)


def _first_owner_approved_live_demotion_slice_design_doc_is_valid():
    return _doc_with_markers_is_valid(_first_owner_approved_live_demotion_slice_design_doc, _first_owner_approved_live_demotion_slice_design_required_markers)


def _first_live_slice_process_canon_doc_is_valid():
    return _doc_with_markers_is_valid(_first_live_slice_process_canon_doc, _first_live_slice_process_canon_required_markers)


def _plan_helper_flag_on_local_observation_design_doc_is_valid():
    return _doc_with_markers_is_valid(_plan_helper_flag_on_local_observation_design_doc, _plan_helper_flag_on_local_observation_design_required_markers)


def _plan_helper_observation_reporting_design_doc_is_valid():
    return _doc_with_markers_is_valid(_plan_helper_observation_reporting_design_doc, _plan_helper_observation_reporting_design_required_markers)


def _behavior_evaluation_turing_style_readiness_doc_is_valid():
    return _doc_with_markers_is_valid(_behavior_evaluation_turing_style_readiness_doc, _behavior_evaluation_turing_style_readiness_required_markers)


def _controlled_behavior_evaluation_prompt_set_doc_is_valid():
    return _doc_with_markers_is_valid(_controlled_behavior_evaluation_prompt_set_doc, _controlled_behavior_evaluation_prompt_set_required_markers)


def _controlled_behavior_stubbed_runtime_evaluation_design_doc_is_valid():
    return _doc_with_markers_is_valid(_controlled_behavior_stubbed_runtime_evaluation_design_doc, _controlled_behavior_stubbed_runtime_evaluation_required_markers)


def _controlled_local_runtime_evaluation_design_doc_is_valid():
    return _doc_with_markers_is_valid(_controlled_local_runtime_evaluation_design_doc, _controlled_local_runtime_evaluation_required_markers)


def _occ_weslr_bootstrap_context_doc_is_valid(path):
    return path in _occ_weslr_bootstrap_context_docs and _doc_with_markers_is_valid(path, _occ_weslr_bootstrap_context_required_markers)


def _check_git_scope():
    """Gate 2 — Check that staged files are within allowed scope.
    
    Allowed paths:
      - weslr/** (any file inside weslr/)
      - interpretation.py
      - docs/WESLR_LOGICAL_FORM_NORMALIZER_ATOMIC_HELPERS_APPROVAL_V1.md only when
        the operator-approved helper-phase markers are present
      - docs/WESLR_LOGICAL_FORM_NORMALIZER_PREDICATE_HELPERS_APPROVAL_V1.md only when
        the operator-approved predicate-helper markers are present
      - docs/WESLR_LOGICAL_FORM_NORMALIZER_RELATION_PRESERVATION_APPROVAL_V1.md only when
        the operator-approved relation-preservation markers are present
      - docs/WESLR_AI_AUDIT_SELF_GOVERNANCE_CANON_V1.md only when
        the operator-approved AI-audit self-governance canon markers are present
      - docs/WESLR_FRONTIER_INTELLIGENCE_EVALUATION_AND_AI_AUDIT_DOCTRINE_V1.md only when
        the approved legacy-tests baseline doctrine markers are present
      - docs/WESLR_FRONTIER_INTELLIGENCE_DRY_PIPELINE_CANON_V1.md only when
        the approved dry-pipeline canon markers are present
      - docs/WESLR_FRONTIER_INTELLIGENCE_SHADOW_REVIEW_CANON_V1.md only when
        the approved shadow-review canon markers are present
      - docs/WESLR_INTERNAL_EVALUATION_CORPUS_HELPER_CANON_V1.md only when
        the approved internal evaluation corpus helper canon markers are present
      - docs/WESLR_INTERNAL_CORPUS_TO_ADVISOR_REVIEW_ADAPTER_DESIGN_V1.md only when
        the approved internal corpus to advisor review adapter design markers are present
      - docs/WESLR_INTERNAL_CORPUS_ADVISOR_REVIEW_ADAPTER_HELPER_CANON_V1.md only when
        the approved internal corpus advisor review adapter helper canon markers are present
      - docs/WESLR_EVIDENCE_BRIDGE_FRONTIER_METADATA_ADAPTER_HELPER_CANON_V1.md only when
        the approved evidence bridge Frontier metadata adapter helper canon markers are present
      - docs/WESLR_UNIFIED_RESPONSE_FORMATION_CANON_V1.md only when
        the approved unified response formation canon markers are present
      - docs/WESLR_FIRST_CANNED_HELPER_DEMOTION_SLICE_DESIGN_V1.md only when
        the approved first canned-helper demotion design markers are present
      - docs/WESLR_FIRST_OWNER_APPROVED_LIVE_DEMOTION_SLICE_DESIGN_V1.md only when
        the approved first owner-approved live demotion slice design markers are present
      - docs/WESLR_FIRST_LIVE_SLICE_PROCESS_CANON_V1.md only when
        the approved first live slice process canon markers are present
      - docs/WESLR_PLAN_HELPER_FLAG_ON_LOCAL_OBSERVATION_DESIGN_V1.md only when
        the approved plan helper flag-on local observation design markers are present
      - docs/WESLR_PLAN_HELPER_OBSERVATION_REPORTING_V1.md only when
        the approved plan helper observation reporting design markers are present
      - docs/WESLR_BEHAVIOR_EVALUATION_AND_TURING_STYLE_READINESS_V1.md only when
        the approved behavior evaluation and Turing-style readiness design markers are present
      - docs/WESLR_CONTROLLED_BEHAVIOR_EVALUATION_PROMPT_SET_V1.md only when
        the approved controlled behavior evaluation prompt-set design markers are present
      - docs/WESLR_CONTROLLED_BEHAVIOR_STUBBED_RUNTIME_EVALUATION_V1.md only when
        the approved controlled behavior stubbed runtime evaluation design markers are present
      - docs/WESLR_CONTROLLED_LOCAL_RUNTIME_EVALUATION_V1.md only when
        the approved controlled local runtime evaluation design markers are present
      - exact OCC/WESLR bootstrap context docs only when the approved
        OCC/WESLR context alignment markers are present
    
    Forbidden:
      - openclaw/, plugins/, memory/, continuity/
      - any .cs file
      - any path outside the allowed list above
    
    Files not yet staged are not checked — operator must `git add` them first.
    """
    staged = _get_staged_files()

    FORBIDDEN_PREFIXES = ["openclaw/", "plugins/", "memory/", "continuity/"]
    FORBIDDEN_EXTENSIONS = {".cs"}

    violations = []
    approval_doc_valid = _atomic_helper_approval_doc_is_valid()
    predicate_approval_doc_valid = _predicate_helper_approval_doc_is_valid()
    relation_approval_doc_valid = _relation_helper_approval_doc_is_valid()
    ai_audit_self_governance_doc_valid = _ai_audit_self_governance_canon_doc_is_valid()
    frontier_intelligence_doctrine_doc_valid = _frontier_intelligence_doctrine_doc_is_valid()
    frontier_intelligence_dry_pipeline_doc_valid = _frontier_intelligence_dry_pipeline_canon_doc_is_valid()
    frontier_intelligence_shadow_review_doc_valid = _frontier_intelligence_shadow_review_canon_doc_is_valid()
    internal_evaluation_corpus_helper_doc_valid = _internal_evaluation_corpus_helper_canon_doc_is_valid()
    internal_corpus_to_advisor_review_adapter_doc_valid = _internal_corpus_to_advisor_review_adapter_design_doc_is_valid()
    internal_corpus_advisor_review_adapter_helper_doc_valid = _internal_corpus_advisor_review_adapter_helper_canon_doc_is_valid()
    evidence_bridge_frontier_metadata_adapter_helper_doc_valid = _evidence_bridge_frontier_metadata_adapter_helper_canon_doc_is_valid()
    unified_response_formation_canon_doc_valid = _unified_response_formation_canon_doc_is_valid()
    first_canned_helper_demotion_design_doc_valid = _first_canned_helper_demotion_design_doc_is_valid()
    first_owner_approved_live_demotion_slice_design_doc_valid = _first_owner_approved_live_demotion_slice_design_doc_is_valid()
    first_live_slice_process_canon_doc_valid = _first_live_slice_process_canon_doc_is_valid()
    plan_helper_flag_on_local_observation_design_doc_valid = _plan_helper_flag_on_local_observation_design_doc_is_valid()
    plan_helper_observation_reporting_design_doc_valid = _plan_helper_observation_reporting_design_doc_is_valid()
    behavior_evaluation_turing_style_readiness_doc_valid = _behavior_evaluation_turing_style_readiness_doc_is_valid()
    controlled_behavior_evaluation_prompt_set_doc_valid = _controlled_behavior_evaluation_prompt_set_doc_is_valid()
    controlled_behavior_stubbed_runtime_evaluation_design_doc_valid = _controlled_behavior_stubbed_runtime_evaluation_design_doc_is_valid()
    controlled_local_runtime_evaluation_design_doc_valid = _controlled_local_runtime_evaluation_design_doc_is_valid()
    for path in staged:
        for prefix in FORBIDDEN_PREFIXES:
            if path.startswith(prefix):
                violations.append(f"  forbidden prefix {prefix!r}: {path}")
        if any(path.endswith(ext) for ext in FORBIDDEN_EXTENSIONS):
            violations.append(f"  forbidden extension: {path}")

        allowed = path.startswith("weslr/") or path == "interpretation.py"
        if path == _atomic_helper_approval_doc:
            allowed = approval_doc_valid
            if not approval_doc_valid:
                violations.append(f"  approval doc missing required markers: {path}")
        if path == _predicate_helper_approval_doc:
            allowed = predicate_approval_doc_valid
            if not predicate_approval_doc_valid:
                violations.append(f"  approval doc missing required markers: {path}")
        if path == _relation_helper_approval_doc:
            allowed = relation_approval_doc_valid
            if not relation_approval_doc_valid:
                violations.append(f"  approval doc missing required markers: {path}")
        if path == _ai_audit_self_governance_canon_doc:
            allowed = ai_audit_self_governance_doc_valid
            if not ai_audit_self_governance_doc_valid:
                violations.append(f"  canon doc missing required markers: {path}")
        if path == _frontier_intelligence_doctrine_doc:
            allowed = frontier_intelligence_doctrine_doc_valid
            if not frontier_intelligence_doctrine_doc_valid:
                violations.append(f"  doctrine doc missing required markers: {path}")
        if path == _frontier_intelligence_dry_pipeline_canon_doc:
            allowed = frontier_intelligence_dry_pipeline_doc_valid
            if not frontier_intelligence_dry_pipeline_doc_valid:
                violations.append(f"  canon doc missing required markers: {path}")
        if path == _frontier_intelligence_shadow_review_canon_doc:
            allowed = frontier_intelligence_shadow_review_doc_valid
            if not frontier_intelligence_shadow_review_doc_valid:
                violations.append(f"  canon doc missing required markers: {path}")
        if path == _internal_evaluation_corpus_helper_canon_doc:
            allowed = internal_evaluation_corpus_helper_doc_valid
            if not internal_evaluation_corpus_helper_doc_valid:
                violations.append(f"  canon doc missing required markers: {path}")
        if path == _internal_corpus_to_advisor_review_adapter_design_doc:
            allowed = internal_corpus_to_advisor_review_adapter_doc_valid
            if not internal_corpus_to_advisor_review_adapter_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _internal_corpus_advisor_review_adapter_helper_canon_doc:
            allowed = internal_corpus_advisor_review_adapter_helper_doc_valid
            if not internal_corpus_advisor_review_adapter_helper_doc_valid:
                violations.append(f"  canon doc missing required markers: {path}")
        if path == _evidence_bridge_frontier_metadata_adapter_helper_canon_doc:
            allowed = evidence_bridge_frontier_metadata_adapter_helper_doc_valid
            if not evidence_bridge_frontier_metadata_adapter_helper_doc_valid:
                violations.append(f"  canon doc missing required markers: {path}")
        if path == _unified_response_formation_canon_doc:
            allowed = unified_response_formation_canon_doc_valid
            if not unified_response_formation_canon_doc_valid:
                violations.append(f"  canon doc missing required markers: {path}")
        if path == _first_canned_helper_demotion_design_doc:
            allowed = first_canned_helper_demotion_design_doc_valid
            if not first_canned_helper_demotion_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _first_owner_approved_live_demotion_slice_design_doc:
            allowed = first_owner_approved_live_demotion_slice_design_doc_valid
            if not first_owner_approved_live_demotion_slice_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _first_live_slice_process_canon_doc:
            allowed = first_live_slice_process_canon_doc_valid
            if not first_live_slice_process_canon_doc_valid:
                violations.append(f"  canon doc missing required markers: {path}")
        if path == _plan_helper_flag_on_local_observation_design_doc:
            allowed = plan_helper_flag_on_local_observation_design_doc_valid
            if not plan_helper_flag_on_local_observation_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _plan_helper_observation_reporting_design_doc:
            allowed = plan_helper_observation_reporting_design_doc_valid
            if not plan_helper_observation_reporting_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _behavior_evaluation_turing_style_readiness_doc:
            allowed = behavior_evaluation_turing_style_readiness_doc_valid
            if not behavior_evaluation_turing_style_readiness_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_behavior_evaluation_prompt_set_doc:
            allowed = controlled_behavior_evaluation_prompt_set_doc_valid
            if not controlled_behavior_evaluation_prompt_set_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_behavior_stubbed_runtime_evaluation_design_doc:
            allowed = controlled_behavior_stubbed_runtime_evaluation_design_doc_valid
            if not controlled_behavior_stubbed_runtime_evaluation_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_local_runtime_evaluation_design_doc:
            allowed = controlled_local_runtime_evaluation_design_doc_valid
            if not controlled_local_runtime_evaluation_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path in _occ_weslr_bootstrap_context_docs:
            allowed = _occ_weslr_bootstrap_context_doc_is_valid(path)
            if not allowed:
                violations.append(f"  OCC/WESLR bootstrap context doc missing required markers: {path}")

        if not allowed:
            violations.append(f"  outside allowed scope: {path}")

    if violations:
        print("GATE 2 FAILED: staged files contain forbidden paths:")
        for v in violations:
            print(v)
        return False

    if staged:
        print(f"GATE 2: {len(staged)} staged file(s) — all in allowed scope")
    else:
        print("GATE 2: no files staged — nothing to check")
    return True


def _check_execution_allowed():
    """Gate 3 — No execution_allowed=True in production weslr/*.py files.
    
    Skips test files (test_harness_v1.py, release_gate_v1.py) since they
    intentionally set execution_allowed=True in test data (bad_plan dict).
    """
    weslr_dir = _workspace / "weslr"
    pattern = re.compile(r"execution_allowed\s*=\s*True", re.IGNORECASE)

    violations = []
    for py_file in weslr_dir.rglob("*.py"):
        if py_file.name in ("test_harness_v1.py", "release_gate_v1.py"):
            continue
        try:
            content = py_file.read_text()
            for lineno, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    rel = py_file.relative_to(_workspace)
                    violations.append(f"  {rel}:{lineno}")
        except Exception:
            pass

    if violations:
        print("GATE 3 FAILED: execution_allowed=True found in production code:")
        for v in violations:
            print(v)
        return False

    print("GATE 3: no execution_allowed=True in production weslr/*.py")
    return True


def _check_openclaw_tia():
    """Gate 4 — No OpenClaw core or TIA C# files in staged scope."""
    staged = _get_staged_files()

    violations = []
    for path in staged:
        if path.startswith("openclaw/") or path.startswith("plugins/"):
            violations.append(f"  OpenClaw core: {path}")
        if path.endswith(".cs"):
            violations.append(f"  TIA C#: {path}")
        if "tia-bridge" in path.lower() and "weslr/docs/tia-bridge" not in path:
            violations.append(f"  TIA bridge: {path}")

    if violations:
        print("GATE 4 FAILED: OpenClaw core or TIA bridge in staged scope:")
        for v in violations:
            print(v)
        return False

    print("GATE 4: no OpenClaw core or TIA C# in staged scope")
    return True


def _check_handler_registry():
    """Gate 5 — Handler registry has complete write-metadata fields.
    
    Verifies every registry entry has write_paths, side_effects, write_guard.
    For entries with read_only=True, write_paths and side_effects must be empty.
    """
    import sys as _sys
    handlers_path = _workspace / "weslr" / "deterministic_handlers.py"
    # Use separate import path so we don't pollute the gate's sys.path permanently
    _gate_path = str(_workspace)
    _orig_path = sys.path.copy()
    if _gate_path not in sys.path:
        sys.path.insert(0, _gate_path)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("deterministic_handlers", str(handlers_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        registry = mod.HANDLER_REGISTRY
    except Exception as e:
        print(f"GATE 5 FAILED: could not import HANDLER_REGISTRY: {e}")
        return False
    finally:
        sys.path[:] = _orig_path

    violations = []
    for entry in registry:
        entry_id = entry.get("id", "<unknown>")
        read_only = entry.get("read_only", False)

        for field in ("write_paths", "side_effects", "write_guard"):
            if field not in entry:
                violations.append(f"  {entry_id}: missing field {field!r}")

        if read_only:
            if entry.get("write_paths", []) != []:
                violations.append(f"  {entry_id}: read_only=True but write_paths={entry.get('write_paths')}")
            if entry.get("side_effects", []) != []:
                violations.append(f"  {entry_id}: read_only=True but side_effects={entry.get('side_effects')}")

    if violations:
        print("GATE 5 FAILED: handler registry metadata issues:")
        for v in violations:
            print(v)
        return False

    print(f"GATE 5: {len(registry)} registry entries — all have write_paths, side_effects, write_guard")
    return True


def main():
    print("=" * 50)
    print("WESLR Release Gate V1")
    print("=" * 50)
    print()

    g1 = _run_harness()
    print()
    g2 = _check_git_scope()
    print()
    g3 = _check_execution_allowed()
    print()
    g4 = _check_openclaw_tia()
    print()
    g5 = _check_handler_registry()
    print()
    print("=" * 50)

    if g1 and g2 and g3 and g4 and g5:
        print("WESLR_RELEASE_GATE_V1_OK")
        return 0
    else:
        print("RELEASE_GATE_V1_FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())