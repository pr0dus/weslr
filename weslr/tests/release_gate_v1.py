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

_cognition_target_model_doc = "docs/WESLR_COGNITION_TARGET_MODEL_V1.md"
_cognition_target_model_required_markers = {
    "WESLR Cognition Target Model V1",
    "design-only",
    "WESLR cognition means governed interpretation",
    "not consciousness",
    "not a chatbot persona",
    "not raw LLM output",
    "not canned deterministic response",
    "ranked state-grounded response formation",
    "LLMs and advisors are bounded helpers",
    "WESLR is one adaptable governed intelligence system",
    "Voice and prosody are downstream expression layers",
    "DESIGN_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1",
    "cognition_target_model_defined",
    "design_only_not_runtime_wired",
    "official_evaluation_not_claimed",
}

_ranked_state_grounded_response_formation_doc = "docs/WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1.md"
_ranked_state_grounded_response_formation_required_markers = {
    "WESLR Ranked State-Grounded Response Formation V1",
    "design-only",
    "ranked state-grounded response formation",
    "RESPONSE STATE FRAME",
    "Candidate responses should be formed from interpreted state",
    "Ranking should use qualitative labels",
    "NON-CANNEDNESS GUARANTEE",
    "LLM / ADVISOR BOUNDARY",
    "IMPLEMENT_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_SHADOW_HELPERS_V1",
    "ranked_response_formation_design_defined",
    "design_only_not_runtime_wired",
    "shadow_helpers_not_implemented",
    "runtime_integration_not_authorized",
    "non_canned_response_principle_defined",
    "official_evaluation_not_claimed",
}

_ranked_state_grounded_response_shadow_helpers_review_doc = "docs/WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_SHADOW_HELPERS_REVIEW_V1.md"
_ranked_state_grounded_response_shadow_helpers_review_required_markers = {
    "WESLR Ranked State-Grounded Response Formation Shadow Helpers Review V1",
    "review-only",
    "shadow_helpers_valid_ready_for_next_shadow_design",
    "helper-only/shadow-only",
    "no runtime wiring",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "DESIGN_RANKED_RESPONSE_SHADOW_EVALUATION_SCENARIOS_V1",
}

_ranked_response_shadow_evaluation_scenarios_doc = "docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_SCENARIOS_V1.md"
_ranked_response_shadow_evaluation_scenarios_required_markers = {
    "WESLR Ranked Response Shadow Evaluation Scenarios V1",
    "design-only",
    "synthetic scenario coverage",
    "IMPLEMENT_RANKED_RESPONSE_SHADOW_EVALUATION_SCENARIOS_V1",
    "ranked_response_shadow_scenario_design_defined",
    "design_only_not_implemented",
    "shadow_evaluation_only",
    "runtime_integration_not_authorized",
    "synthetic_metadata_only",
    "raw_prompt_response_not_retained",
    "official_evaluation_not_claimed",
    "voice_downstream_not_current_priority",
}

_ranked_response_shadow_evaluation_scenarios_review_doc = "docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_SCENARIOS_REVIEW_V1.md"
_ranked_response_shadow_evaluation_scenarios_review_required_markers = {
    "WESLR Ranked Response Shadow Evaluation Scenarios Review V1",
    "shadow_scenarios_valid_ready_for_report_design",
    "DESIGN_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_V1",
    "synthetic metadata only",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness claims",
}

_ranked_response_shadow_evaluation_report_design_doc = "docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_V1.md"
_ranked_response_shadow_evaluation_report_design_required_markers = {
    "WESLR Ranked Response Shadow Evaluation Report V1",
    "design-only",
    "metadata-only",
    "IMPLEMENT_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_HELPERS_V1",
    "ranked_response_shadow_report_design_defined",
    "design_only_not_implemented",
    "metadata_only_report_surface",
    "runtime_integration_not_authorized",
    "raw_prompt_response_not_retained",
    "final_answer_not_generated",
    "official_evaluation_not_claimed",
    "voice_downstream_not_current_priority",
}

_ranked_response_shadow_evaluation_report_helpers_review_doc = "docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_HELPERS_REVIEW_V1.md"
_ranked_response_shadow_evaluation_report_helpers_review_required_markers = {
    "WESLR Ranked Response Shadow Evaluation Report Helpers Review V1",
    "review-only",
    "metadata-only report surface",
    "shadow_report_helpers_valid_but_need_minor_followup",
    "DESIGN_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_RUN_V1",
    "no runtime wiring",
    "no `chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no official claims",
}

_ranked_response_shadow_evaluation_report_run_design_doc = "docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_RUN_V1.md"
_ranked_response_shadow_evaluation_report_run_design_required_markers = {
    "WESLR Ranked Response Shadow Evaluation Report Run V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "IMPLEMENT_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_RUN_V1",
    "report_run_design_defined",
    "design_only_not_implemented",
    "metadata_only_report_run",
    "internal_shadow_evaluation_only",
    "runtime_integration_not_authorized",
    "raw_prompt_response_not_retained",
    "final_answer_not_generated",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "no runtime behavior changes",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
}

_ranked_response_shadow_evaluation_report_run_result_doc = "docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_RUN_RESULT_V1.md"
_ranked_response_shadow_evaluation_report_run_result_required_markers = {
    "WESLR Ranked Response Shadow Evaluation Report Run Result V1",
    "internal_shadow_evaluation_only",
    "runtime_integration_not_authorized",
    "official_evaluation_not_claimed",
    "final_answer_not_generated",
    "minor_followup_carried_forward",
}

_ranked_response_shadow_evaluation_report_run_review_doc = "docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_RUN_REVIEW_V1.md"
_ranked_response_shadow_evaluation_report_run_review_required_markers = {
    "WESLR Ranked Response Shadow Evaluation Report Run Review V1",
    "review-only",
    "report_run_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_RANKED_RESPONSE_SHADOW_REPORT_RUN_V1",
    "no runtime wiring",
    "no `weslr/chat_responder.py` edit",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness/consciousness/sentience claims",
}

_ranked_response_shadow_helper_interop_boundary_doc = "docs/WESLR_RANKED_RESPONSE_SHADOW_HELPER_INTEROP_BOUNDARY_V1.md"
_ranked_response_shadow_helper_interop_boundary_required_markers = {
    "WESLR Ranked Response Shadow Helper Interop Boundary V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "interop_boundary_design_defined",
    "design_only_not_implemented",
    "helper_authority_boundaries_defined",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "raw_prompt_response_not_retained",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_RANKED_RESPONSE_SHADOW_HELPER_INTEROP_BOUNDARY_V1",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final answer generation",
}

_ranked_response_shadow_helper_interop_boundary_review_doc = "docs/WESLR_RANKED_RESPONSE_SHADOW_HELPER_INTEROP_BOUNDARY_REVIEW_V1.md"
_ranked_response_shadow_helper_interop_boundary_review_required_markers = {
    "WESLR Ranked Response Shadow Helper Interop Boundary Review V1",
    "review-only",
    "interop_boundary_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_RANKED_RESPONSE_SHADOW_HELPER_INTEROP_BOUNDARY_V1",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness/consciousness/sentience claims",
}

_ranked_response_shadow_native_dry_slice_interop_doc = "docs/WESLR_RANKED_RESPONSE_SHADOW_NATIVE_DRY_SLICE_INTEROP_V1.md"
_ranked_response_shadow_native_dry_slice_interop_required_markers = {
    "WESLR Ranked Response Shadow / Native Dry-Slice Interop V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "ranked_native_interop_design_defined",
    "design_only_not_implemented",
    "helper_authority_boundaries_preserved",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "raw_prompt_response_not_retained",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_RANKED_RESPONSE_SHADOW_NATIVE_DRY_SLICE_INTEROP_V1",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final answer generation",
}

_ranked_response_shadow_native_dry_slice_interop_review_doc = "docs/WESLR_RANKED_RESPONSE_SHADOW_NATIVE_DRY_SLICE_INTEROP_REVIEW_V1.md"
_ranked_response_shadow_native_dry_slice_interop_review_required_markers = {
    "WESLR Ranked Response Shadow / Native Dry-Slice Interop Review V1",
    "review-only",
    "ranked_native_interop_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_RANKED_RESPONSE_SHADOW_NATIVE_DRY_SLICE_INTEROP_V1",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness/consciousness/sentience claims",
}

_ranked_native_interop_shadow_artifact_helpers_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_HELPERS_V1.md"
_ranked_native_interop_shadow_artifact_helpers_required_markers = {
    "WESLR Ranked/Native Interop Shadow Artifact Helpers V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "ranked_native_artifact_helper_design_defined",
    "design_only_not_implemented",
    "metadata_only_artifact_boundary_defined",
    "helper_authority_boundaries_preserved",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "raw_prompt_response_not_retained",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_HELPERS_V1",
    "ranked_native_interop_shadow_artifact_v1",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final answer generation",
}

_ranked_native_interop_shadow_artifact_helpers_review_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_HELPERS_REVIEW_V1.md"
_ranked_native_interop_shadow_artifact_helpers_review_required_markers = {
    "WESLR Ranked/Native Interop Shadow Artifact Helper Design Review V1",
    "review-only",
    "ranked_native_artifact_helper_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_HELPERS_V1",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no official claims",
}

_ranked_native_interop_shadow_artifact_helpers_implementation_review_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_ranked_native_interop_shadow_artifact_helpers_implementation_review_required_markers = {
    "WESLR Ranked/Native Interop Shadow Artifact Helpers Implementation Review V1",
    "review-only",
    "ranked_native_artifact_helpers_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_HELPERS_IMPLEMENTATION_V1",
    "no `chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no official claims",
}

_ranked_native_interop_shadow_artifact_report_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_V1.md"
_ranked_native_interop_shadow_artifact_report_required_markers = {
    "WESLR Ranked/Native Interop Shadow Artifact Report V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "ranked_native_artifact_report_design_defined",
    "design_only_not_implemented",
    "metadata_only_report_surface",
    "helper_authority_boundaries_preserved",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "raw_prompt_response_not_retained",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_V1",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness/consciousness/sentience claims",
}

_ranked_native_interop_shadow_artifact_report_review_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_REVIEW_V1.md"
_ranked_native_interop_shadow_artifact_report_review_required_markers = {
    "WESLR Ranked/Native Interop Shadow Artifact Report Review V1",
    "review-only",
    "ranked_native_artifact_report_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_V1",
    "no `chat_responder.py` edits",
    "no helper/source/test changes",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no official claims",
}

_ranked_native_interop_shadow_artifact_report_helpers_implementation_review_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_ranked_native_interop_shadow_artifact_report_helpers_implementation_review_required_markers = {
    "WESLR Ranked/Native Interop Shadow Artifact Report Helpers Implementation Review V1",
    "Review-only",
    "ranked_native_artifact_report_helpers_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_HELPERS_IMPLEMENTATION_V1",
    "no `chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no official claims",
}

_ranked_native_interop_shadow_artifact_report_run_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_V1.md"
_ranked_native_interop_shadow_artifact_report_run_required_markers = {
    "WESLR Ranked/Native Interop Shadow Artifact Report Run V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "ranked_native_artifact_report_run_design_defined",
    "design_only_not_implemented",
    "metadata_only_report_run",
    "internal_shadow_evaluation_only",
    "helper_authority_boundaries_preserved",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "raw_prompt_response_not_retained",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_V1",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness claims",
}

_ranked_native_interop_shadow_artifact_report_run_review_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_REVIEW_V1.md"
_ranked_native_interop_shadow_artifact_report_run_review_required_markers = {
    "WESLR Ranked/Native Interop Shadow Artifact Report Run Review V1",
    "review-only",
    "ranked_native_artifact_report_run_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_V1",
    "no `chat_responder.py` edits",
    "no helper/source/test changes",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no official claims",
}

_ranked_native_interop_shadow_artifact_report_run_result_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_RESULT_V1.md"
_ranked_native_interop_shadow_artifact_report_run_result_required_markers = {
    "internal_shadow_evaluation_only",
    "metadata_only_report_run",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "raw_prompt_response_not_retained",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
}

_ranked_native_interop_shadow_artifact_report_run_implementation_review_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_IMPLEMENTATION_REVIEW_V1.md"
_ranked_native_interop_shadow_artifact_report_run_implementation_review_required_markers = {
    "WESLR Ranked/Native Interop Shadow Artifact Report Run Implementation Review V1",
    "review_only",
    "ranked_native_artifact_report_run_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_RESULT_V1",
    "metadata_only_report_run",
    "internal_shadow_evaluation_only",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "raw_prompt_response_not_retained",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
    "no runtime wiring",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final answer generation",
    "no official claims",
}

_ranked_native_to_internal_turing_readiness_bridge_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_REPORT_RUN_TO_INTERNAL_TURING_READINESS_BRIDGE_V1.md"
_ranked_native_to_internal_turing_readiness_bridge_required_markers = {
    "WESLR Ranked/Native Interop Report Run to Internal Turing Readiness Bridge V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "ranked_native_to_turing_readiness_bridge_defined",
    "design_only_not_implemented",
    "shadow_metadata_evidence_clean",
    "internal_turing_harness_not_designed",
    "live_dialogue_readiness_not_established",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "official_evaluation_not_claimed",
    "further_cognition_evidence_required",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_RANKED_NATIVE_INTEROP_REPORT_RUN_TO_INTERNAL_TURING_READINESS_BRIDGE_V1",
    "no `chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final-answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness claims",
}

_ranked_native_to_internal_turing_readiness_bridge_review_doc = "docs/WESLR_RANKED_NATIVE_INTEROP_REPORT_RUN_TO_INTERNAL_TURING_READINESS_BRIDGE_REVIEW_V1.md"
_ranked_native_to_internal_turing_readiness_bridge_review_required_markers = {
    "WESLR Ranked/Native Interop Report Run to Internal Turing Readiness Bridge Review V1",
    "review-only",
    "ranked_native_to_internal_turing_bridge_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_RANKED_NATIVE_TO_INTERNAL_TURING_READINESS_BRIDGE_V1",
    "no live cognition claim",
    "no Turing-test readiness/pass claim",
    "no IQ/certification/product-readiness claim",
    "no consciousness/sentience claim",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no feature flags",
    "no official claims",
}

_internal_turing_style_readiness_dimensions_and_corpus_doc = "docs/WESLR_INTERNAL_TURING_STYLE_READINESS_DIMENSIONS_AND_CORPUS_V1.md"
_internal_turing_style_readiness_dimensions_and_corpus_required_markers = {
    "WESLR Internal Turing-Style Readiness Dimensions and Corpus V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "internal_turing_readiness_dimensions_defined",
    "controlled_dialogue_corpus_design_defined",
    "design_only_not_implemented",
    "internal_only_non_official",
    "qualitative_first",
    "live_dialogue_readiness_not_established",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "official_evaluation_not_claimed",
    "further_cognition_evidence_required",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_INTERNAL_TURING_STYLE_READINESS_DIMENSIONS_AND_CORPUS_V1",
    "scenario_id",
    "raw_content_allowed: false",
    "final_answer_required: false",
    "runtime_execution_allowed: false",
    "official_score_allowed: false",
    "renderer_next_lane_wording_drift",
    "validator_phrase_key_limitation",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final-answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness claims",
}

_internal_turing_style_readiness_dimensions_and_corpus_review_doc = "docs/WESLR_INTERNAL_TURING_STYLE_READINESS_DIMENSIONS_AND_CORPUS_REVIEW_V1.md"
_internal_turing_style_readiness_dimensions_and_corpus_review_required_markers = {
    "WESLR Internal Turing-Style Readiness Dimensions and Corpus Review V1",
    "review-only",
    "internal_turing_readiness_dimensions_corpus_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_INTERNAL_TURING_READINESS_DIMENSIONS_AND_CORPUS_V1",
    "no official Turing test claim",
    "no Turing pass claim",
    "no IQ/certification/product-readiness claim",
    "no consciousness/sentience claim",
    "no runtime readiness claim",
    "no deployment/production readiness claim",
    "no voice/prosody readiness claim",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no feature flags",
    "no official claims",
}

_internal_turing_scenario_corpus_helpers_doc = "docs/WESLR_INTERNAL_TURING_SCENARIO_CORPUS_HELPERS_V1.md"
_internal_turing_scenario_corpus_helpers_required_markers = {
    "WESLR Internal Turing Scenario Corpus Helpers V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "internal_turing_scenario_corpus_helper_design_defined",
    "design_only_not_implemented",
    "metadata_only_scenario_records",
    "controlled_dialogue_corpus_preserved",
    "internal_only_non_official",
    "qualitative_first",
    "prompt_execution_not_authorized",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "official_evaluation_not_claimed",
    "further_cognition_evidence_required",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_INTERNAL_TURING_SCENARIO_CORPUS_HELPERS_V1",
    "build_internal_turing_scenario_record_v1",
    "build_internal_turing_scenario_corpus_v1",
    "validate_internal_turing_scenario_record_v1",
    "validate_internal_turing_scenario_corpus_v1",
    "summarize_internal_turing_scenario_corpus_v1",
    "render_internal_turing_scenario_corpus_markdown_v1",
    "to_internal_turing_scenario_corpus_json_safe_v1",
    "raw_content_allowed: false",
    "final_answer_required: false",
    "runtime_execution_allowed: false",
    "official_score_allowed: false",
    "simple_ordinary_request",
    "anti_gaming_boundary",
    "renderer_next_lane_wording_drift",
    "validator_phrase_key_limitation",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final-answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness claims",
}

_internal_turing_scenario_corpus_helpers_review_doc = "docs/WESLR_INTERNAL_TURING_SCENARIO_CORPUS_HELPERS_REVIEW_V1.md"
_internal_turing_scenario_corpus_helpers_review_required_markers = {
    "WESLR Internal Turing Scenario Corpus Helpers Review V1",
    "review-only",
    "internal_turing_scenario_corpus_helper_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_INTERNAL_TURING_SCENARIO_CORPUS_HELPERS_V1",
    "no official Turing test claim",
    "no Turing pass claim",
    "no IQ/certification/product-readiness claim",
    "no consciousness/sentience claim",
    "no runtime readiness claim",
    "no deployment/production readiness claim",
    "no voice/prosody readiness claim",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no feature flags",
    "no official claims",
}

_internal_turing_scenario_corpus_helpers_implementation_review_doc = "docs/WESLR_INTERNAL_TURING_SCENARIO_CORPUS_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_internal_turing_scenario_corpus_helpers_implementation_review_required_markers = {
    "WESLR Internal Turing Scenario Corpus Helpers Implementation Review V1",
    "review-only",
    "internal_turing_scenario_corpus_helpers_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_INTERNAL_TURING_SCENARIO_CORPUS_HELPERS_IMPLEMENTATION_V1",
    "no official Turing test claim",
    "no Turing pass claim",
    "no IQ/certification/product-readiness claim",
    "no consciousness/sentience claim",
    "no runtime readiness claim",
    "no deployment/production readiness claim",
    "no voice/prosody readiness claim",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no feature flags",
    "no official claims",
}

_internal_turing_multi_turn_evaluation_protocol_doc = "docs/WESLR_INTERNAL_TURING_MULTI_TURN_EVALUATION_PROTOCOL_V1.md"
_internal_turing_multi_turn_evaluation_protocol_required_markers = {
    "WESLR Internal Turing Multi-Turn Evaluation Protocol V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "internal_turing_multi_turn_protocol_design_defined",
    "design_only_not_implemented",
    "metadata_only_episode_shape",
    "internal_only_non_official",
    "qualitative_first",
    "prompt_execution_not_authorized",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "official_evaluation_not_claimed",
    "further_cognition_evidence_required",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_INTERNAL_TURING_MULTI_TURN_EVALUATION_PROTOCOL_V1",
    "raw_content_allowed=false",
    "prompt_execution_allowed=false",
    "final_answer_required=false",
    "runtime_execution_allowed=false",
    "official_score_allowed=false",
    "renderer_next_lane_wording_drift",
    "validator_phrase_key_limitation",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final-answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness claims",
}

_internal_turing_multi_turn_evaluation_protocol_review_doc = "docs/WESLR_INTERNAL_TURING_MULTI_TURN_EVALUATION_PROTOCOL_REVIEW_V1.md"
_internal_turing_multi_turn_evaluation_protocol_review_required_markers = {
    "WESLR Internal Turing Multi-Turn Evaluation Protocol Review V1",
    "review-only",
    "internal_turing_multi_turn_protocol_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_INTERNAL_TURING_MULTI_TURN_PROTOCOL_V1",
    "no official Turing test claim",
    "no Turing pass claim",
    "no IQ/certification/product-readiness claim",
    "no consciousness/sentience claim",
    "no runtime readiness claim",
    "no deployment/production readiness claim",
    "no open-dialogue proof claim",
    "no voice/prosody readiness claim",
    "no public marketing evidence claim",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no feature flags",
    "no official claims",
}

_internal_turing_multi_turn_protocol_helpers_doc = "docs/WESLR_INTERNAL_TURING_MULTI_TURN_PROTOCOL_HELPERS_V1.md"
_internal_turing_multi_turn_protocol_helpers_required_markers = {
    "WESLR Internal Turing Multi-Turn Protocol Helpers V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "internal_turing_multi_turn_protocol_helper_design_defined",
    "design_only_not_implemented",
    "metadata_only_episode_records",
    "internal_only_non_official",
    "qualitative_first",
    "prompt_execution_not_authorized",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "official_evaluation_not_claimed",
    "further_cognition_evidence_required",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_INTERNAL_TURING_MULTI_TURN_PROTOCOL_HELPERS_V1",
    "raw_content_allowed=false",
    "prompt_execution_allowed=false",
    "final_answer_required=false",
    "runtime_execution_allowed=false",
    "official_score_allowed=false",
    "Turing-name overclaim risk",
    "future label non-scoring discipline",
    "renderer_next_lane_wording_drift",
    "validator_phrase_key_limitation",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final-answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness claims",
}

_internal_turing_multi_turn_protocol_helpers_review_doc = "docs/WESLR_INTERNAL_TURING_MULTI_TURN_PROTOCOL_HELPERS_REVIEW_V1.md"
_internal_turing_multi_turn_protocol_helpers_review_required_markers = {
    "WESLR Internal Turing Multi-Turn Protocol Helpers Review V1",
    "review-only",
    "internal_turing_multi_turn_protocol_helper_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_INTERNAL_TURING_MULTI_TURN_PROTOCOL_HELPERS_V1",
    "no official Turing test claim",
    "no Turing pass claim",
    "no IQ/certification/product-readiness claim",
    "no consciousness/sentience claim",
    "no runtime readiness claim",
    "no deployment/production readiness claim",
    "no open-dialogue proof claim",
    "no voice/prosody readiness claim",
    "no public marketing evidence claim",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw prompt/response retention",
    "no final answer generation",
    "no feature flags",
    "no official claims",
}

_internal_turing_multi_turn_protocol_helpers_implementation_review_doc = "docs/WESLR_INTERNAL_TURING_MULTI_TURN_PROTOCOL_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_internal_turing_multi_turn_protocol_helpers_implementation_review_required_markers = {
    "WESLR Internal Turing Multi-Turn Protocol Helpers Implementation Review V1",
    "internal_turing_multi_turn_protocol_helpers_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_INTERNAL_TURING_MULTI_TURN_PROTOCOL_HELPERS_IMPLEMENTATION_V1",
    "no official Turing test claim",
    "no Turing pass claim",
    "no IQ/certification/product-readiness claim",
    "no consciousness/sentience claim",
    "no runtime readiness claim",
    "no deployment/production readiness claim",
    "no open-dialogue human-understanding proof claim",
    "no voice/prosody readiness claim",
    "no public marketing evidence claim",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no live dialogue",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw retention",
    "no final answer generation",
    "no feature flags",
    "no official claims",
}


_internal_turing_to_answer_authority_boundary_doc = "docs/WESLR_INTERNAL_TURING_PROTOCOL_HELPERS_TO_ANSWER_AUTHORITY_BOUNDARY_V1.md"
_internal_turing_to_answer_authority_boundary_required_markers = {
    "WESLR Internal Turing Protocol Helpers to Answer Authority Boundary V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "internal_turing_to_answer_authority_boundary_defined",
    "design_only_not_implemented",
    "metadata_evidence_not_answer_authority",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "internal_only_non_official",
    "qualitative_first",
    "official_evaluation_not_claimed",
    "further_cognition_evidence_required",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_INTERNAL_TURING_PROTOCOL_HELPERS_TO_ANSWER_AUTHORITY_BOUNDARY_V1",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "final_answer_generated=false",
    "official_claim_allowed=false",
    "prompt_execution_allowed=false",
    "raw_content_allowed=false",
    "validator_phrase_key_limitation",
    "renderer_next_lane_wording_drift",
    "Turing-name overclaim risk",
    "future label non-scoring discipline",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final-answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness/consciousness claims",
}


_internal_turing_to_answer_authority_boundary_review_doc = "docs/WESLR_INTERNAL_TURING_PROTOCOL_HELPERS_TO_ANSWER_AUTHORITY_BOUNDARY_REVIEW_V1.md"
_internal_turing_to_answer_authority_boundary_review_required_markers = {
    "WESLR Internal Turing Protocol Helpers to Answer Authority Boundary Review V1",
    "Review-only",
    "internal_turing_to_answer_authority_boundary_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_INTERNAL_TURING_TO_ANSWER_AUTHORITY_BOUNDARY_V1",
    "metadata evidence is not answer authority",
    "candidate metadata is not answer text",
    "evaluation metadata is not response authority",
    "answer authority remains not granted",
    "runtime authority remains not granted",
    "final-answer generation remains not authorized",
    "prompt execution remains not authorized",
    "no official Turing test claim",
    "no Turing pass claim",
    "no IQ/certification/product-readiness claim",
    "no consciousness/sentience claim",
    "no runtime readiness claim",
    "no deployment/production readiness claim",
    "no open-dialogue proof claim",
    "no voice/prosody readiness claim",
    "no public marketing evidence claim",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no live dialogue",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw retention",
    "no final answer generation",
    "no feature flags",
    "no official claims",
}


_answer_authority_boundary_helpers_doc = "docs/WESLR_ANSWER_AUTHORITY_BOUNDARY_HELPERS_V1.md"
_answer_authority_boundary_helpers_required_markers = {
    "WESLR Answer Authority Boundary Helpers V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "answer_authority_boundary_helper_design_defined",
    "design_only_not_implemented",
    "metadata_evidence_not_answer_authority",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "internal_only_non_official",
    "qualitative_first",
    "official_evaluation_not_claimed",
    "further_cognition_evidence_required",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
    "REVIEW_ANSWER_AUTHORITY_BOUNDARY_HELPERS_V1",
    "build_answer_authority_boundary_artifact_v1",
    "validate_answer_authority_boundary_artifact_v1",
    "summarize_answer_authority_boundary_artifact_v1",
    "render_answer_authority_boundary_artifact_markdown_v1",
    "to_answer_authority_boundary_artifact_json_safe_v1",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "final_answer_generated=false",
    "official_claim_allowed=false",
    "prompt_execution_allowed=false",
    "raw_content_allowed=false",
    "metadata_only=true",
    "internal_only=true",
    "metadata evidence may inform review, but metadata evidence is not answer authority",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no live dialogue",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no final-answer generation",
    "no official benchmark/Turing/IQ/certification/product-readiness/consciousness claims",
}


_answer_authority_boundary_helpers_review_doc = "docs/WESLR_ANSWER_AUTHORITY_BOUNDARY_HELPERS_REVIEW_V1.md"
_answer_authority_boundary_helpers_review_required_markers = {
    "WESLR Answer Authority Boundary Helpers Review V1",
    "Review-only",
    "answer_authority_boundary_helper_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_AUTHORITY_BOUNDARY_HELPERS_V1",
    "metadata evidence is not answer authority",
    "candidate metadata is not answer text",
    "evaluation metadata is not response authority",
    "answer boundary artifacts are not answer authority",
    "answer boundary artifacts are not final answers",
    "answer authority remains not granted",
    "runtime authority remains not granted",
    "final-answer generation remains not authorized",
    "prompt execution remains not authorized",
    "answer composition remains not authorized",
    "no official Turing test claim",
    "no Turing pass claim",
    "no IQ/certification/product-readiness claim",
    "no consciousness/sentience claim",
    "no runtime readiness claim",
    "no deployment/production readiness claim",
    "no open-dialogue proof claim",
    "no voice/prosody readiness claim",
    "no public marketing evidence claim",
    "no answer authority claim",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no live dialogue",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no raw retention",
    "no final answer generation",
    "no answer composition",
    "no feature flags",
    "no official claims",
    "no answer authority granted",
}


_answer_authority_boundary_helpers_implementation_review_doc = "docs/WESLR_ANSWER_AUTHORITY_BOUNDARY_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_answer_authority_boundary_helpers_implementation_review_required_markers = {
    "WESLR Answer Authority Boundary Helpers Implementation Review V1",
    "answer_authority_boundary_helpers_implementation_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_AUTHORITY_BOUNDARY_HELPERS_IMPLEMENTATION_REVIEW_V1",
    "metadata evidence is not answer authority",
    "helper-only",
    "metadata-only",
    "no answer authority granted",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution",
    "no live dialogue",
    "no judges/scoring",
    "no provider calls",
    "no `.weslr` writes",
    "no official claims",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}


_answer_composition_authority_boundary_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_BOUNDARY_V1.md"
_answer_composition_authority_boundary_required_markers = {
    "WESLR Answer Composition Authority Boundary V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "answer_composition_authority_boundary_design_defined",
    "REVIEW_ANSWER_COMPOSITION_AUTHORITY_BOUNDARY_V1",
    "metadata evidence may inform future composition review, but metadata evidence is not answer text and is not answer authority",
    "answer authority is granted",
    "answer composition is authorized",
    "final-answer generation is authorized",
    "runtime wiring is authorized",
    "prompt execution is authorized",
    "live dialogue is authorized",
    "model/search/advisor calls are authorized",
    "`.weslr` writes are authorized",
    "feature flags are authorized",
    "scoring is authorized",
    "judge authority is granted",
    "helper metadata",
    "evaluation metadata",
    "ranked/native metadata",
    "answer authority boundary artifacts",
    "no answer authority granted",
    "no composition authority granted",
    "no runtime behavior edited",
    "no `weslr/chat_responder.py` edit",
    "no final-answer generation",
    "no prompt execution",
    "no live dialogue",
    "no runtime wiring",
    "no model/search/advisor provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_boundary_review_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_BOUNDARY_REVIEW_V1.md"
_answer_composition_authority_boundary_review_required_markers = {
    "WESLR Answer Composition Authority Boundary Review V1",
    "answer_composition_authority_boundary_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_COMPOSITION_AUTHORITY_BOUNDARY_V1",
    "metadata evidence may inform future composition review, but metadata evidence is not answer text and is not answer authority",
    "design-only",
    "no answer composition implemented",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no model/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_helpers_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_HELPERS_V1.md"
_answer_composition_authority_helpers_required_markers = {
    "WESLR Answer Composition Authority Helpers V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "answer_composition_authority_helpers_design_defined",
    "REVIEW_ANSWER_COMPOSITION_AUTHORITY_HELPERS_V1",
    "Metadata evidence may inform future composition review, but metadata evidence is not answer text, is not answer composition authority, and is not answer authority.",
    "build_answer_composition_authority_artifact_v1",
    "validate_answer_composition_authority_artifact_v1",
    "summarize_answer_composition_authority_artifact_v1",
    "render_answer_composition_authority_artifact_markdown_v1",
    "to_answer_composition_authority_artifact_json_safe_v1",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "no helper/source/test implementation",
    "no `weslr/chat_responder.py` edit",
    "no answer composition implementation",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution",
    "no live dialogue",
    "no model/search/advisor/provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no answer authority granted",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_helpers_review_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_HELPERS_REVIEW_V1.md"
_answer_composition_authority_helpers_review_required_markers = {
    "WESLR Answer Composition Authority Helpers Review V1",
    "answer_composition_authority_helpers_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_COMPOSITION_AUTHORITY_HELPERS_V1",
    "design-only",
    "metadata-only",
    "no answer composition implemented",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_helpers_implementation_plan_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_HELPERS_IMPLEMENTATION_PLAN_V1.md"
_answer_composition_authority_helpers_implementation_plan_required_markers = {
    "WESLR Answer Composition Authority Helpers Implementation Plan V1",
    "WESLR_CANON_ALIGNMENT / design-only implementation plan",
    "answer_composition_authority_helpers_implementation_plan_defined",
    "REVIEW_ANSWER_COMPOSITION_AUTHORITY_HELPERS_IMPLEMENTATION_PLAN_V1",
    "weslr/answer_composition_authority.py",
    "weslr/tests/test_answer_composition_authority_v1.py",
    "build_answer_composition_authority_artifact_v1",
    "validate_answer_composition_authority_artifact_v1",
    "summarize_answer_composition_authority_artifact_v1",
    "render_answer_composition_authority_artifact_markdown_v1",
    "to_answer_composition_authority_artifact_json_safe_v1",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "no helper implementation",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution",
    "no live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_helpers_implementation_plan_review_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_HELPERS_IMPLEMENTATION_PLAN_REVIEW_V1.md"
_answer_composition_authority_helpers_implementation_plan_review_required_markers = {
    "WESLR Answer Composition Authority Helpers Implementation Plan Review V1",
    "WESLR_CANON_ALIGNMENT` review report only",
    "answer_composition_authority_helpers_implementation_plan_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_COMPOSITION_AUTHORITY_HELPERS_IMPLEMENTATION_PLAN_REVIEW_V1",
    "design-only implementation plan",
    "no helper implementation",
    "weslr/answer_composition_authority.py",
    "weslr/tests/test_answer_composition_authority_v1.py",
    "narrow release-gate allowance if required",
    "future API is metadata-only",
    "artifact shape preserves false/no-authority fields",
    "validator/renderer/JSON-safe requirements are safe",
    "test coverage requirements are sufficient",
    "rollback/abort conditions are clear",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_helpers_implementation_review_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_answer_composition_authority_helpers_implementation_review_required_markers = {
    "WESLR Answer Composition Authority Helpers Implementation Review V1",
    "answer_composition_authority_helpers_implementation_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_COMPOSITION_AUTHORITY_HELPERS_IMPLEMENTATION_REVIEW_V1",
    "helper-only",
    "metadata-only",
    "deterministic",
    "import-safe",
    "side-effect-free",
    "in-memory only",
    "no answer composition implemented",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_report_helpers_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_REPORT_HELPERS_V1.md"
_answer_composition_authority_report_helpers_required_markers = {
    "WESLR Answer Composition Authority Report Helpers V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "answer_composition_authority_report_helpers_design_defined",
    "REVIEW_ANSWER_COMPOSITION_AUTHORITY_REPORT_HELPERS_V1",
    "build_answer_composition_authority_report_v1",
    "validate_answer_composition_authority_report_v1",
    "summarize_answer_composition_authority_report_v1",
    "derive_answer_composition_authority_report_aggregate_labels_v1",
    "render_answer_composition_authority_report_markdown_v1",
    "to_answer_composition_authority_report_json_safe_v1",
    "allowed report input types",
    "forbidden report input",
    "report validation policy",
    "Safe Markdown Rendering Policy",
    "JSON-Safe Report Behavior",
    "Aggregate Labels",
    "Risk and Followup Visibility",
    "Future Implementation Sequence",
    "no report helper implementation",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution",
    "no live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_report_helpers_review_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_REPORT_HELPERS_REVIEW_V1.md"
_answer_composition_authority_report_helpers_review_required_markers = {
    "WESLR Answer Composition Authority Report Helpers Review V1",
    "answer_composition_authority_report_helpers_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_COMPOSITION_AUTHORITY_REPORT_HELPERS_V1",
    "design-only",
    "metadata-only",
    "report-helper design only",
    "no report helper implementation",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_report_helpers_implementation_review_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_REPORT_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_answer_composition_authority_report_helpers_implementation_review_required_markers = {
    "WESLR Answer Composition Authority Report Helpers Implementation Review V1",
    "answer_composition_authority_report_helpers_implementation_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_COMPOSITION_AUTHORITY_REPORT_HELPERS_IMPLEMENTATION_REVIEW_V1",
    "helper-only",
    "metadata-only",
    "deterministic",
    "import-safe",
    "side-effect-free",
    "in-memory only",
    "report-helper only",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_report_run_design_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_V1.md"
_answer_composition_authority_report_run_design_required_markers = {
    "WESLR Answer Composition Authority Report Run V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "answer_composition_authority_report_run_design_defined",
    "IMPLEMENT_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_V1",
    "REVIEW_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_V1",
    "design_only_not_implemented",
    "metadata_only_report_run",
    "internal_only_report_run",
    "helper_authority_boundaries_preserved",
    "runtime_integration_not_authorized",
    "answer_composition_not_authorized",
    "answer_authority_not_granted",
    "composition_authority_not_granted",
    "final_answer_not_generated",
    "official_claims_not_allowed",
    "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_RESULT_V1.md",
    "result artifact must not be created in this design lane",
    "allowed inputs",
    "Forbidden Inputs",
    "report-run flow",
    "validation gates",
    "blocked conditions",
    "JSON-Safe Policy",
    "Aggregate Labels",
    "Visible Risks and Followups",
    "Abort Conditions",
    "Future Implementation Sequence",
    "no runtime behavior changes",
    "no `weslr/chat_responder.py` edits",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no prompt execution",
    "no live dialogue",
    "no model/search/advisor calls",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no final answer generation",
    "no answer composition",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_report_run_review_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_REVIEW_V1.md"
_answer_composition_authority_report_run_review_required_markers = {
    "WESLR Answer Composition Authority Report Run Review V1",
    "answer_composition_authority_report_run_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_V1",
    "design-only",
    "metadata-only",
    "internal-only",
    "no report-run implementation",
    "no report execution",
    "no result artifact creation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_answer_composition_authority_report_run_result_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_RESULT_V1.md"
_answer_composition_authority_report_run_result_required_markers = {
    "WESLR Answer Composition Authority Report Run Result V1",
    "WESLR_CANON_ALIGNMENT / metadata-only internal report-run result",
    "answer_composition_authority_report_run_result_v1",
    "metadata_only_report_run",
    "internal_only_report_run",
    "validation_pass_metadata_quality_evidence_only",
    "occ_openclaw_separate_from_deployed_weslr",
    "answer_composition_not_authorized",
    "answer_authority_not_granted",
    "composition_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "provider_calls_not_authorized",
    "dot_weslr_writes_not_authorized",
    "feature_flags_not_authorized",
    "judges_scoring_not_authorized",
    "official_claims_not_allowed",
    "no_answer_composition",
    "no_final_answer_generation",
    "no_runtime_wiring",
    "no_prompt_execution_live_dialogue",
    "no_provider_calls",
    "no_dot_weslr_writes",
    "no_feature_flags",
    "no_judges_scoring",
    "no_official_claims",
    "no_answer_authority_granted",
    "no_composition_authority_granted",
    "chat_responder_untouched",
    "OCC/OpenClaw remains separate from deployed WESLR",
    "REVIEW_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_RESULT_V1",
}

_answer_composition_authority_report_run_result_review_doc = "docs/WESLR_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_RESULT_REVIEW_V1.md"
_answer_composition_authority_report_run_result_review_required_markers = {
    "WESLR Answer Composition Authority Report Run Result Review V1",
    "answer_composition_authority_report_run_result_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_COMPOSITION_AUTHORITY_REPORT_RUN_RESULT_V1",
    "metadata-only",
    "internal-only",
    "deterministic",
    "import-safe",
    "result artifact only as approved",
    "validation pass is metadata quality evidence only",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_controlled_answer_composition_dry_run_boundary_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_BOUNDARY_V1.md"
_controlled_answer_composition_dry_run_boundary_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Boundary V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "controlled_answer_composition_dry_run_boundary_design_defined",
    "REVIEW_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_BOUNDARY_V1",
    "design_only_not_implemented",
    "metadata-only",
    "internal-only",
    "synthetic-only",
    "non-runtime",
    "non-user-facing",
    "Allowed Synthetic Inputs",
    "Forbidden Inputs",
    "No-Runtime Boundary",
    "No-Final-Answer Boundary",
    "No-Provider Boundary",
    "No-.weslr Boundary",
    "Answer-Composition Dry-Run Artifact Shape",
    "Required False / No-Authority Fields",
    "Evidence / Provenance / Governance / Memory / Domain Gates",
    "Blocked Conditions",
    "Safe Markdown / Output Policy",
    "Validation Policy",
    "Abort Conditions",
    "Future Implementation Sequence",
    "no dry-run implementation",
    "no dry-run execution",
    "no dry-run result artifact",
    "no answer composition implementation",
    "no final-answer generation",
    "no runtime wiring",
    "no `weslr/chat_responder.py` edits",
    "no prompt execution",
    "no live dialogue",
    "no provider/model/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "OCC/OpenClaw is not WESLR",
}

_controlled_answer_composition_dry_run_boundary_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_BOUNDARY_REVIEW_V1.md"
_controlled_answer_composition_dry_run_boundary_review_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Boundary Review V1",
    "controlled_answer_composition_dry_run_boundary_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_BOUNDARY_V1",
    "Review judgment",
    "Reviewed Inputs",
    "Design Findings",
    "Boundary Confirmation",
    "Gate Review",
    "Safety and Output Review",
    "Gaps / Followups",
    "Judgment",
    "Recommended Next Lane",
    "Validation Results",
    "Safety Confirmation",
    "design-only",
    "synthetic metadata-only",
    "internal-only",
    "non-runtime",
    "non-user-facing",
    "no dry-run implementation",
    "no dry run executed",
    "no dry-run result artifact created",
    "no answer composition implementation",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider/model/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_controlled_answer_composition_dry_run_helpers_design_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_HELPERS_V1.md"
_controlled_answer_composition_dry_run_helpers_design_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Helpers V1",
    "controlled_answer_composition_dry_run_helpers_design_defined",
    "REVIEW_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_HELPERS_V1",
    "design_only_not_implemented",
    "Future Helper Module Path",
    "Future Test Module Path",
    "Future Public API Names",
    "Dry-Run Artifact Shape",
    "Allowed Synthetic Metadata Inputs",
    "Forbidden Inputs",
    "Required False / No-Authority Fields",
    "Evidence / Provenance / Governance / Memory / Domain Gates",
    "Blocked Conditions",
    "Validation Policy",
    "Safe Markdown / Rendering Policy",
    "JSON-Safe Policy",
    "Test Coverage Requirements",
    "Validation Commands",
    "Abort / Rollback Conditions",
    "Future Implementation Sequence",
    "weslr/controlled_answer_composition_dry_run.py",
    "weslr/tests/test_controlled_answer_composition_dry_run_v1.py",
    "build_controlled_answer_composition_dry_run_artifact_v1",
    "validate_controlled_answer_composition_dry_run_artifact_v1",
    "summarize_controlled_answer_composition_dry_run_artifact_v1",
    "render_controlled_answer_composition_dry_run_artifact_markdown_v1",
    "to_controlled_answer_composition_dry_run_artifact_json_safe_v1",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "no helper implementation",
    "no dry run executed",
    "no dry-run result artifact created",
    "no final-answer generation",
    "no runtime wiring",
    "no `weslr/chat_responder.py` edits",
    "no prompt execution",
    "no live dialogue",
    "no provider/model/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
}

_controlled_answer_composition_dry_run_helpers_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_HELPERS_REVIEW_V1.md"
_controlled_answer_composition_dry_run_helpers_review_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Helpers Review V1",
    "controlled_answer_composition_dry_run_helpers_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_HELPERS_V1",
    "Reviewed Inputs",
    "Design Findings",
    "Boundary Confirmation",
    "Gate and Helper Policy Review",
    "Rendering and JSON Safety Review",
    "Gaps / Followups",
    "Judgment",
    "Recommended Next Lane",
    "Validation Results",
    "Safety Confirmation",
    "design-only",
    "metadata-only",
    "synthetic-input only",
    "no dry-run helper implementation",
    "no dry run executed",
    "no dry-run result artifact",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not deployed WESLR",
}

_controlled_answer_composition_dry_run_helpers_implementation_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_controlled_answer_composition_dry_run_helpers_implementation_review_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Helpers Implementation Review V1",
    "controlled_answer_composition_dry_run_helpers_implementation_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_HELPERS_IMPLEMENTATION_V1",
    "helper-only",
    "synthetic metadata-only",
    "deterministic",
    "import-safe",
    "side-effect-free",
    "in-memory only",
    "no dry run executed",
    "no dry-run result artifact created",
    "no answer composition implemented",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_controlled_answer_composition_dry_run_result_design_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_V1.md"
_controlled_answer_composition_dry_run_result_design_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Result V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "controlled_answer_composition_dry_run_result_design_defined",
    "REVIEW_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_V1",
    "design_only_not_implemented",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V1.md",
    "Allowed Metadata Fields",
    "Forbidden Content",
    "Validation Status Fields",
    "Required False / No-Authority Fields",
    "Denied Authority Fields",
    "Gate Status Fields",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Blocked Result Behavior",
    "Visible Risks / Followups",
    "Abort Conditions",
    "Future Implementation / Execution Sequence",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "no dry-run execution",
    "no result artifact generation from a run",
    "no runtime behavior changes",
    "no `weslr/chat_responder.py` edits",
    "no answer composition",
    "no final-answer generation",
    "no prompt execution",
    "no live dialogue",
    "no provider/model/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "OCC/OpenClaw is not WESLR",
}

_controlled_answer_composition_dry_run_result_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_REVIEW_V1.md"
_controlled_answer_composition_dry_run_result_review_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Result Review V1",
    "WESLR_CANON_ALIGNMENT",
    "controlled_answer_composition_dry_run_result_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_V1",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_V1.md",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V1.md",
    "design-only",
    "metadata-only",
    "result-spec only",
    "no dry run executed",
    "no future result artifact created",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider/model/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "no final-answer generation",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_controlled_answer_composition_dry_run_result_test_fix_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_TEST_FIX_REVIEW_V1.md"
_controlled_answer_composition_dry_run_result_test_fix_review_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Result Test Fix Review V1",
    "WESLR_CANON_ALIGNMENT",
    "controlled_dry_run_result_design_existence_test_fix_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_DRY_RUN_RESULT_TEST_FIX_V1",
    "dd1e6eea5f1b56e4db40697b3eb734fd00901036",
    "weslr/tests/test_controlled_answer_composition_dry_run_v1.py",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_V1.md",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V1.md",
    "test-only correction",
    "no runtime edits",
    "no `weslr/chat_responder.py` edits",
    "no helper/source edits",
    "no dry run",
    "no future result artifact",
    "no answer composition",
    "no final answers",
    "no prompt/live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "OCC/OpenClaw is not WESLR",
}

_controlled_answer_composition_dry_run_execution_design_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_EXECUTION_V1.md"
_controlled_answer_composition_dry_run_execution_design_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Execution V1",
    "WESLR_CANON_ALIGNMENT / design-only",
    "controlled_answer_composition_dry_run_execution_design_defined",
    "REVIEW_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_EXECUTION_V1",
    "design_only_not_executed",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V1.md",
    "Allowed Synthetic Metadata Inputs",
    "Forbidden Inputs",
    "Required Helper Calls",
    "Validation-Before-Rendering Requirements",
    "Result Artifact Writing Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Blocked Execution Behavior",
    "Required False / No-Authority Fields",
    "Abort Conditions",
    "Future Review Sequence",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "no dry-run execution",
    "no result artifact creation",
    "no runtime behavior changes",
    "no `weslr/chat_responder.py` edits",
    "no answer composition",
    "no final-answer generation",
    "no prompt execution",
    "no live dialogue",
    "no provider/model/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "OCC/OpenClaw is not WESLR",
}

_controlled_answer_composition_dry_run_execution_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_EXECUTION_REVIEW_V1.md"
_controlled_answer_composition_dry_run_execution_review_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Execution Review V1",
    "WESLR_CANON_ALIGNMENT",
    "controlled_answer_composition_dry_run_execution_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_EXECUTION_V1",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_EXECUTION_V1.md",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V1.md",
    "design-only",
    "metadata-only",
    "synthetic-input only",
    "execution design only",
    "no dry-run execution",
    "no future result artifact created",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider/model/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "no final-answer generation",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not WESLR",
}

_controlled_answer_composition_dry_run_result_artifact_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V1.md"
_controlled_answer_composition_dry_run_result_artifact_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Result Artifact V1",
    "controlled_answer_composition_dry_run_execution_result_created",
    "synthetic_metadata_only_internal_result_artifact",
    "REVIEW_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_EXECUTION_RESULT_V1",
    "metadata_quality_evidence_only",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "answer_authority: denied",
    "composition_authority: denied",
    "runtime_authority: denied",
    "provider_authority: denied",
    "persistence_authority: denied",
    "feature_flag_authority: denied",
    "judge_authority: denied",
    "scoring_authority: denied",
    "forbidden_content_absent: True",
    "safe_markdown_valid: True",
    "json_safe_valid: True",
    "validation_pass_metadata_quality_evidence_only",
    "result_artifact_not_answer_text",
    "metadata_result_not_composition_authority",
    "occ_openclaw_not_deployed_weslr",
}

_controlled_answer_composition_dry_run_execution_result_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_EXECUTION_RESULT_REVIEW_V1.md"
_controlled_answer_composition_dry_run_execution_result_review_required_markers = {
    "WESLR Controlled Answer Composition Dry Run Execution Result Review V1",
    "controlled_answer_composition_dry_run_execution_result_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_EXECUTION_RESULT_V1",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V1.md",
    "synthetic metadata-only",
    "internal-only",
    "helper-based",
    "validation-before-rendering",
    "safe Markdown only",
    "result artifact path exactly approved",
    "no real user query text",
    "no raw prompts",
    "no raw responses",
    "no private content",
    "no hidden prompts",
    "no answer keys",
    "no provider/model/search/advisor output",
    "no runtime output",
    "no final-answer prose",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "no runtime authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw remains separate from deployed WESLR",
    "historical helper-lane test",
    "test-scope fix lane",
}

_controlled_answer_composition_dry_run_to_answer_formation_bridge_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_TO_ANSWER_FORMATION_BRIDGE_V1.md"
_controlled_answer_composition_dry_run_to_answer_formation_bridge_required_markers = {
    "WESLR Controlled Answer Composition Dry Run To Answer Formation Bridge V1",
    "controlled_answer_composition_dry_run_to_answer_formation_bridge_defined",
    "design_only_not_implemented",
    "dry_run_metadata_informs_design_only",
    "WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V1.md",
    "WESLR_COGNITION_TARGET_MODEL_V1.md",
    "WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1.md",
    "what the controlled dry-run result proves",
    "what the controlled dry-run result does not prove",
    "metadata that must not become authority",
    "required future gates before any answer-formation helper",
    "required future gates before any final-answer dry run",
    "required future gates before runtime / live chat",
    "artifact_presence_not_answer_authority",
    "validation_pass_metadata_quality_only",
    "ranked_state_grounding_required_before_answer_formation",
    "answer_formation_authorized",
    "answer_composition_authorized",
    "final_answer_authorized",
    "runtime_authorized",
    "no `weslr/chat_responder.py` edits",
    "no answer formation implementation",
    "no answer composition implementation",
    "no final-answer generation",
    "no provider/model/search/advisor calls",
    "no `.weslr` writes",
    "no answer authority granted",
    "no composition authority granted",
    "REVIEW_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_TO_ANSWER_FORMATION_BRIDGE_V1",
}

_controlled_answer_composition_dry_run_to_answer_formation_bridge_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_TO_ANSWER_FORMATION_BRIDGE_REVIEW_V1.md"
_controlled_answer_composition_dry_run_to_answer_formation_bridge_review_required_markers = {
    "WESLR Controlled Answer Composition Dry Run To Answer Formation Bridge Review V1",
    "controlled_answer_composition_dry_run_to_answer_formation_bridge_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_DRY_RUN_TO_ANSWER_FORMATION_BRIDGE_V1",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_TO_ANSWER_FORMATION_BRIDGE_V1.md",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_RESULT_ARTIFACT_V1.md",
    "docs/WESLR_COGNITION_TARGET_MODEL_V1.md",
    "docs/WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1.md",
    "design-only",
    "metadata-only",
    "bridge-only",
    "no answer formation implementation",
    "no answer composition implementation",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no provider/model/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "no runtime authority granted",
    "metadata must not become authority",
    "final-answer dry runs require separate gates",
    "runtime/live chat requires separate gates",
    "OCC/OpenClaw remains separate from deployed WESLR",
}

_answer_formation_helpers_design_doc = "docs/WESLR_ANSWER_FORMATION_HELPERS_V1.md"
_answer_formation_helpers_design_required_markers = {
    "WESLR Answer Formation Helpers V1",
    "answer_formation_helpers_design_defined",
    "design_only_not_implemented",
    "weslr/answer_formation.py",
    "weslr/tests/test_answer_formation_v1.py",
    "build_answer_formation_artifact_v1",
    "validate_answer_formation_artifact_v1",
    "summarize_answer_formation_artifact_v1",
    "render_answer_formation_artifact_markdown_v1",
    "to_answer_formation_artifact_json_safe_v1",
    "answer_formation_attempted=false",
    "answer_formation_authorized=false",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "candidate metadata must not include answer draft text",
    "validation pass means metadata quality evidence only",
    "metadata must not become authority",
    "REVIEW_ANSWER_FORMATION_HELPERS_V1",
}

_answer_formation_helpers_review_doc = "docs/WESLR_ANSWER_FORMATION_HELPERS_REVIEW_V1.md"
_answer_formation_helpers_review_required_markers = {
    "WESLR Answer Formation Helpers Review V1",
    "answer_formation_helpers_design_valid_ready_for_context_alignment",
    "docs/WESLR_ANSWER_FORMATION_HELPERS_V1.md",
    "weslr/answer_formation.py",
    "weslr/tests/test_answer_formation_v1.py",
    "build_answer_formation_artifact_v1",
    "validate_answer_formation_artifact_v1",
    "summarize_answer_formation_artifact_v1",
    "render_answer_formation_artifact_markdown_v1",
    "to_answer_formation_artifact_json_safe_v1",
    "answer_formation_attempted=false",
    "answer_formation_authorized=false",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "candidate metadata is not answer draft text",
    "validation pass means metadata quality evidence only",
    "metadata must not become authority",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_HELPERS_V1",
}

_answer_formation_helpers_implementation_plan_doc = "docs/WESLR_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_PLAN_V1.md"
_answer_formation_helpers_implementation_plan_required_markers = {
    "WESLR Answer Formation Helpers Implementation Plan V1",
    "answer_formation_helpers_implementation_plan_defined",
    "design_only_not_implemented",
    "weslr/answer_formation.py",
    "weslr/tests/test_answer_formation_v1.py",
    "build_answer_formation_artifact_v1",
    "validate_answer_formation_artifact_v1",
    "summarize_answer_formation_artifact_v1",
    "render_answer_formation_artifact_markdown_v1",
    "to_answer_formation_artifact_json_safe_v1",
    "answer_formation_attempted=false",
    "answer_formation_authorized=false",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "validation pass means metadata quality evidence only",
    "metadata must not become authority",
    "REVIEW_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_PLAN_V1",
}

_answer_formation_helpers_implementation_plan_review_doc = "docs/WESLR_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_PLAN_REVIEW_V1.md"
_answer_formation_helpers_implementation_plan_review_required_markers = {
    "WESLR Answer Formation Helpers Implementation Plan Review V1",
    "answer_formation_helpers_implementation_plan_valid_ready_for_context_alignment",
    "docs/WESLR_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_PLAN_V1.md",
    "weslr/answer_formation.py",
    "weslr/tests/test_answer_formation_v1.py",
    "build_answer_formation_artifact_v1",
    "validate_answer_formation_artifact_v1",
    "summarize_answer_formation_artifact_v1",
    "render_answer_formation_artifact_markdown_v1",
    "to_answer_formation_artifact_json_safe_v1",
    "answer_formation_attempted=false",
    "answer_formation_authorized=false",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "validation pass means metadata quality evidence only",
    "metadata must not become authority",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_PLAN_V1",
}

_answer_formation_helpers_implementation_review_doc = "docs/WESLR_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_answer_formation_helpers_implementation_review_required_markers = {
    "WESLR Answer Formation Helpers Implementation Review V1",
    "answer_formation_helpers_implementation_valid_ready_for_context_alignment",
    "weslr/answer_formation.py",
    "weslr/tests/test_answer_formation_v1.py",
    "build_answer_formation_artifact_v1",
    "validate_answer_formation_artifact_v1",
    "summarize_answer_formation_artifact_v1",
    "render_answer_formation_artifact_markdown_v1",
    "to_answer_formation_artifact_json_safe_v1",
    "answer_formation_attempted=false",
    "answer_formation_authorized=false",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "validation pass means metadata quality evidence only",
    "metadata must not become authority",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_V1",
}

_answer_formation_report_helpers_design_doc = "docs/WESLR_ANSWER_FORMATION_REPORT_HELPERS_V1.md"
_answer_formation_report_helpers_design_required_markers = {
    "WESLR Answer Formation Report Helpers V1",
    "answer_formation_report_helpers_design_defined",
    "design_only_not_implemented",
    "weslr/answer_formation_report.py",
    "weslr/tests/test_answer_formation_report_v1.py",
    "build_answer_formation_report_v1",
    "validate_answer_formation_report_v1",
    "summarize_answer_formation_report_v1",
    "derive_answer_formation_report_labels_v1",
    "render_answer_formation_report_markdown_v1",
    "to_answer_formation_report_json_safe_v1",
    "answer_formation_attempted=false",
    "answer_formation_authorized=false",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "validation pass means metadata quality evidence only",
    "metadata must not become authority",
    "report helpers must not produce answer text",
    "REVIEW_ANSWER_FORMATION_REPORT_HELPERS_V1",
}

_answer_formation_report_helpers_review_doc = "docs/WESLR_ANSWER_FORMATION_REPORT_HELPERS_REVIEW_V1.md"
_answer_formation_report_helpers_review_required_markers = {
    "WESLR Answer Formation Report Helpers Review V1",
    "answer_formation_report_helpers_design_valid_ready_for_context_alignment",
    "design_only_not_implemented",
    "weslr/answer_formation_report.py",
    "weslr/tests/test_answer_formation_report_v1.py",
    "build_answer_formation_report_v1",
    "validate_answer_formation_report_v1",
    "summarize_answer_formation_report_v1",
    "derive_answer_formation_report_labels_v1",
    "render_answer_formation_report_markdown_v1",
    "to_answer_formation_report_json_safe_v1",
    "answer_formation_attempted=false",
    "answer_formation_authorized=false",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "validation pass means metadata quality evidence only",
    "metadata must not become authority",
    "report helpers must not produce answer text",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_REPORT_HELPERS_V1",
}

_answer_formation_report_helpers_implementation_review_doc = "docs/WESLR_ANSWER_FORMATION_REPORT_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_answer_formation_report_helpers_implementation_review_required_markers = {
    "WESLR Answer Formation Report Helpers Implementation Review V1",
    "answer_formation_report_helpers_implementation_valid_ready_for_context_alignment",
    "weslr/answer_formation_report.py",
    "weslr/tests/test_answer_formation_report_v1.py",
    "build_answer_formation_report_v1",
    "validate_answer_formation_report_v1",
    "summarize_answer_formation_report_v1",
    "derive_answer_formation_report_labels_v1",
    "render_answer_formation_report_markdown_v1",
    "to_answer_formation_report_json_safe_v1",
    "helper-only",
    "metadata-only",
    "deterministic",
    "import-safe",
    "side-effect-free",
    "in-memory only",
    "internal-only",
    "qualitative-only",
    "answer_formation_attempted=false",
    "answer_formation_authorized=false",
    "answer_composition_attempted=false",
    "answer_composition_authorized=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "raw_content_allowed=false",
    "official_claim_allowed=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "validation pass remains metadata quality evidence only",
    "metadata quality evidence only",
    "does not generate final-answer prose",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_REPORT_HELPERS_IMPLEMENTATION_V1",
}

_answer_formation_report_run_design_doc = "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_V1.md"
_answer_formation_report_run_design_required_markers = {
    "WESLR Answer Formation Report Run V1",
    "answer_formation_report_run_design_defined",
    "design document only",
    "weslr/answer_formation_report_run.py",
    "weslr/tests/test_answer_formation_report_run_v1.py",
    "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_V1.md",
    "weslr/answer_formation_report.py",
    "build_answer_formation_report_v1",
    "validate_answer_formation_report_v1",
    "summarize_answer_formation_report_v1",
    "derive_answer_formation_report_labels_v1",
    "render_answer_formation_report_markdown_v1",
    "to_answer_formation_report_json_safe_v1",
    "validation-before-rendering",
    "safe Markdown",
    "JSON-safe",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "Validation pass means metadata quality evidence only",
    "must not execute answer formation",
    "must not compose answers",
    "must not generate final-answer prose",
    "must not call providers/search/advisors",
    "REVIEW_ANSWER_FORMATION_REPORT_RUN_V1",
}

_answer_formation_report_run_review_doc = "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_REVIEW_V1.md"
_answer_formation_report_run_review_required_markers = {
    "WESLR Answer Formation Report Run Review V1",
    "answer_formation_report_run_design_valid_ready_for_context_alignment",
    "review report only",
    "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_V1.md",
    "weslr/answer_formation_report_run.py",
    "weslr/tests/test_answer_formation_report_run_v1.py",
    "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_V1.md",
    "design-only",
    "metadata-only",
    "report-run-design-only",
    "no report-run implementation",
    "no report execution",
    "no result artifact created",
    "no answer formation execution",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no provider/model/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "no runtime authority granted",
    "weslr/chat_responder.py` untouched",
    "validation-before-rendering",
    "safe Markdown",
    "JSON-safe",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_REPORT_RUN_V1",
}

_answer_formation_report_run_result_doc = "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_V1.md"
_answer_formation_report_run_result_required_markers = {
    "WESLR Answer Formation Report Run Result V1",
    "answer_formation_report_run_v1",
    "answer_formation_report_run_schema_v1",
    "result artifact only",
    "weslr/answer_formation_report_run.py",
    "weslr/tests/test_answer_formation_report_run_v1.py",
    "weslr/answer_formation_report.py",
    "weslr/tests/test_answer_formation_report_v1.py",
    "metadata_only_report_run",
    "internal_only_report_run",
    "helper_based_report_run",
    "validation_pass_metadata_quality_evidence_only",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "runtime_wired=false",
    "no_answer_formation_execution",
    "no_answer_composition",
    "no_final_answer_generation",
    "no_runtime_wiring",
    "no_provider_search_advisor_calls",
    "no_dot_weslr_writes",
    "no_feature_flags",
    "no_judges_or_scoring",
    "no_official_claims",
    "no_answer_authority_granted",
    "no_composition_authority_granted",
    "no_runtime_authority_granted",
    "weslr_chat_responder_py_untouched",
    "REVIEW_ANSWER_FORMATION_REPORT_RUN_RESULT_V1",
}

_answer_formation_report_run_result_review_doc = "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_REVIEW_V1.md"
_answer_formation_report_run_result_review_required_markers = {
    "WESLR Answer Formation Report Run Result Review V1",
    "answer_formation_report_run_result_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_REPORT_RUN_RESULT_V1",
    "review report only",
    "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_V1.md",
    "weslr/answer_formation_report_run.py",
    "weslr/tests/test_answer_formation_report_run_v1.py",
    "metadata-only",
    "internal-only",
    "helper-based",
    "validation-before-rendering",
    "safe Markdown only",
    "exactly one approved result artifact",
    "no real answer formation execution",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "no runtime authority granted",
    "`weslr/chat_responder.py` untouched",
    "OCC/OpenClaw is not deployed WESLR and is not WESLR",
}

_answer_formation_dry_run_boundary_doc = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_BOUNDARY_V1.md"
_answer_formation_dry_run_boundary_required_markers = {
    "WESLR Answer Formation Dry Run Boundary V1",
    "answer_formation_dry_run_boundary_design_defined",
    "design document only",
    "dry run may inspect explicitly supplied safe metadata",
    "internal dry-run artifacts only",
    "Allowed Synthetic Metadata Inputs",
    "Forbidden Inputs / Content",
    "weslr/answer_formation.py",
    "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_V1.md",
    "No-Final-Answer Boundary",
    "No-Runtime Boundary",
    "Validation-Before-Rendering Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "live_dialogue_allowed=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "dry_run_result_artifact_created=false",
    "must not call providers/models/search/advisors",
    "must not produce final answer prose",
    "REVIEW_ANSWER_FORMATION_DRY_RUN_BOUNDARY_V1",
}

_answer_formation_dry_run_boundary_review_doc = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_BOUNDARY_REVIEW_V1.md"
_answer_formation_dry_run_boundary_review_required_markers = {
    "WESLR Answer Formation Dry Run Boundary Review V1",
    "answer_formation_dry_run_boundary_design_valid_ready_for_context_alignment",
    "review report only",
    "docs/WESLR_ANSWER_FORMATION_DRY_RUN_BOUNDARY_V1.md",
    "design-only",
    "metadata-only",
    "boundary-only",
    "no dry-run implementation",
    "no dry-run execution",
    "no dry-run result artifact",
    "no answer formation execution",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt execution/live dialogue",
    "no `ChatResponder` calls",
    "no `respond_chat()` calls",
    "no `generate_chat()` calls",
    "no provider/model/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "no runtime authority granted",
    "`weslr/chat_responder.py` untouched",
    "Allowed Synthetic Metadata Inputs Review",
    "Forbidden Inputs / Content Review",
    "No-Final-Answer Boundary Review",
    "No-Runtime Boundary Review",
    "Validation-Before-Rendering Review",
    "Safe Markdown Review",
    "JSON-Safe Policy Review",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_DRY_RUN_BOUNDARY_V1",
}

_answer_formation_dry_run_helpers_design_doc = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_HELPERS_V1.md"
_answer_formation_dry_run_helpers_design_required_markers = {
    "WESLR Answer Formation Dry Run Helpers V1",
    "answer_formation_dry_run_helpers_design_defined",
    "design document only",
    "weslr/answer_formation_dry_run.py",
    "weslr/tests/test_answer_formation_dry_run_v1.py",
    "build_answer_formation_dry_run_artifact_v1",
    "validate_answer_formation_dry_run_artifact_v1",
    "summarize_answer_formation_dry_run_artifact_v1",
    "render_answer_formation_dry_run_artifact_markdown_v1",
    "to_answer_formation_dry_run_artifact_json_safe_v1",
    "answer_formation_dry_run_artifact_v1",
    "answer_formation_dry_run_artifact_schema_v1",
    "Allowed Synthetic Metadata Inputs",
    "Forbidden Inputs / Content",
    "Relationship To Answer Formation Helpers",
    "Relationship To Answer Formation Report-Run Result",
    "Validation-Before-Rendering Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Blocked Artifact Behavior",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "dry_run_result_artifact_created=false",
    "no_helper_implementation",
    "no_dry_run_execution",
    "no_final_answer_generation",
    "no_runtime_wiring",
    "no_provider_search_advisor_calls",
    "REVIEW_ANSWER_FORMATION_DRY_RUN_HELPERS_V1",
}

_answer_formation_dry_run_helpers_review_doc = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_HELPERS_REVIEW_V1.md"
_answer_formation_dry_run_helpers_review_required_markers = {
    "WESLR Answer Formation Dry Run Helpers Review V1",
    "answer_formation_dry_run_helpers_design_valid_ready_for_context_alignment",
    "review report only",
    "docs/WESLR_ANSWER_FORMATION_DRY_RUN_HELPERS_V1.md",
    "design-only",
    "metadata-only",
    "helper-design-only",
    "no dry-run helpers implemented",
    "no dry-run execution",
    "no dry-run result artifact",
    "no answer formation execution",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no `ChatResponder` calls",
    "no `respond_chat()` calls",
    "no `generate_chat()` calls",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer/composition/runtime authority granted",
    "`weslr/chat_responder.py` untouched",
    "Future Paths And Public API Review",
    "Dry-Run Artifact Shape Review",
    "Validation / Rendering / JSON Review",
    "Blocked Artifact Behavior Review",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_DRY_RUN_HELPERS_V1",
}

_answer_formation_dry_run_helpers_implementation_review_doc = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_answer_formation_dry_run_helpers_implementation_review_required_markers = {
    "WESLR Answer Formation Dry Run Helpers Implementation Review V1",
    "answer_formation_dry_run_helpers_implementation_valid_ready_for_context_alignment",
    "weslr/answer_formation_dry_run.py",
    "weslr/tests/test_answer_formation_dry_run_v1.py",
    "build_answer_formation_dry_run_artifact_v1",
    "validate_answer_formation_dry_run_artifact_v1",
    "summarize_answer_formation_dry_run_artifact_v1",
    "render_answer_formation_dry_run_artifact_markdown_v1",
    "to_answer_formation_dry_run_artifact_json_safe_v1",
    "helper-only",
    "metadata-only",
    "synthetic-input only",
    "deterministic",
    "import-safe",
    "side-effect-free",
    "in-memory only",
    "internal-only",
    "qualitative-only",
    "no dry-run execution",
    "no dry-run result artifact",
    "no answer formation execution",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no ChatResponder calls",
    "no respond_chat calls",
    "no generate_chat calls",
    "no provider/search/advisor calls",
    "no .weslr writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer/composition/runtime authority granted",
    "weslr/chat_responder.py untouched",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "dry_run_result_artifact_created=false",
    "validation pass means metadata quality evidence only",
    "metadata must not become authority",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_DRY_RUN_HELPERS_IMPLEMENTATION_V1",
}

_answer_formation_dry_run_execution_design_doc = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_V1.md"
_answer_formation_dry_run_execution_design_required_markers = {
    "WESLR Answer Formation Dry Run Execution V1",
    "answer_formation_dry_run_execution_design_defined",
    "design document only",
    "weslr/answer_formation_dry_run_execution.py",
    "weslr/tests/test_answer_formation_dry_run_execution_v1.py",
    "docs/WESLR_ANSWER_FORMATION_DRY_RUN_RESULT_V1.md",
    "build_answer_formation_dry_run_artifact_v1",
    "validate_answer_formation_dry_run_artifact_v1",
    "summarize_answer_formation_dry_run_artifact_v1",
    "render_answer_formation_dry_run_artifact_markdown_v1",
    "to_answer_formation_dry_run_artifact_json_safe_v1",
    "Allowed Synthetic Metadata Inputs",
    "Forbidden Inputs / Content",
    "Validation-Before-Rendering Policy",
    "Safe Markdown Result Policy",
    "JSON-Safe Policy",
    "Blocked Execution Behavior",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "no_dry_run_execution",
    "no_dry_run_result_artifact_created",
    "no_final_answer_generation",
    "no_runtime_wiring",
    "no_provider_search_advisor_calls",
    "validation_pass_metadata_quality_evidence_only",
    "metadata_must_not_become_authority",
    "REVIEW_ANSWER_FORMATION_DRY_RUN_EXECUTION_V1",
}

_answer_formation_dry_run_execution_review_doc = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_REVIEW_V1.md"
_answer_formation_dry_run_execution_review_required_markers = {
    "WESLR Answer Formation Dry Run Execution Review V1",
    "answer_formation_dry_run_execution_design_valid_ready_for_context_alignment",
    "review report only",
    "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_V1.md",
    "design-only",
    "metadata-only",
    "execution-design-only",
    "no dry-run implementation",
    "no dry-run execution",
    "no dry-run result artifact",
    "no real answer formation execution",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no `ChatResponder` calls",
    "no `respond_chat()` calls",
    "no `generate_chat()` calls",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer/composition/runtime authority granted",
    "`weslr/chat_responder.py` untouched",
    "dry-run execution purpose",
    "future execution module path",
    "future test module path",
    "future result artifact path",
    "allowed synthetic metadata inputs",
    "forbidden inputs/content",
    "required helper calls",
    "validation-before-rendering policy",
    "safe Markdown result policy",
    "JSON-safe policy",
    "Denied Authority Fields",
    "blocked execution behavior",
    "Visible Risks And Followups",
    "Abort Conditions",
    "validation commands",
    "future review sequence",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_DRY_RUN_EXECUTION_V1",
}


_answer_formation_dry_run_result_doc = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_RESULT_V1.md"
_answer_formation_dry_run_result_required_markers = {
    "WESLR Answer Formation Dry-Run Result V1",
    "answer_formation_dry_run_execution_result_v1",
    "answer_formation_dry_run_execution_result_schema_v1",
    "internal result artifact only",
    "answer_formation_dry_run_execution_v1",
    "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_V1.md",
    "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_REVIEW_V1.md",
    "weslr/answer_formation_dry_run.py",
    "weslr/tests/test_answer_formation_dry_run_v1.py",
    "weslr/answer_formation_dry_run_execution.py",
    "weslr/tests/test_answer_formation_dry_run_execution_v1.py",
    "dry_run_helper_artifact_built_and_validated",
    "validation_pass_metadata_quality_evidence_only",
    "synthetic_metadata_only_internal_safe_markdown_no_authority",
    "blocked_result_uses_safe_labels_only",
    "unsafe_values_not_copied",
    "metadata_only_dry_run_execution_result",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "prompt_execution_allowed=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "no_runtime_wiring",
    "no_provider_search_advisor_calls",
    "no_final_answer_generation",
    "no_authority_grant",
    "REVIEW_ANSWER_FORMATION_DRY_RUN_EXECUTION_RESULT_V1",
}

_answer_formation_dry_run_execution_result_review_doc = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_RESULT_REVIEW_V1.md"
_answer_formation_dry_run_execution_result_review_required_markers = {
    "WESLR Answer Formation Dry-Run Execution Result Review V1",
    "answer_formation_dry_run_execution_result_valid_ready_for_context_alignment",
    "review report only",
    "docs/WESLR_ANSWER_FORMATION_DRY_RUN_RESULT_V1.md",
    "weslr/answer_formation_dry_run_execution.py",
    "weslr/tests/test_answer_formation_dry_run_execution_v1.py",
    "answer_formation_dry_run_execution_v1",
    "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_V1.md",
    "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_REVIEW_V1.md",
    "weslr/answer_formation_dry_run.py",
    "weslr/tests/test_answer_formation_dry_run_v1.py",
    "dry_run_helper_artifact_built_and_validated",
    "validation_pass_metadata_quality_evidence_only",
    "synthetic_metadata_only_internal_safe_markdown_no_authority",
    "denied authority fields preserved as false",
    "no-runtime/no-provider/no-final-answer boundary present",
    "No gaps found",
    "answer authority",
    "composition authority",
    "runtime authority",
    "official evaluation authority",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_ANSWER_FORMATION_DRY_RUN_EXECUTION_RESULT_V1",
}

_controlled_answer_formation_execution_boundary_doc = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_BOUNDARY_V1.md"
_controlled_answer_formation_execution_boundary_required_markers = {
    "WESLR Controlled Answer Formation Execution Boundary V1",
    "controlled_answer_formation_execution_boundary_design_defined",
    "design document only",
    "controlled answer formation execution",
    "why dry-run result does not grant execution authority",
    "Allowed Future Synthetic or Controlled Metadata Inputs",
    "Forbidden Real-User / Live Inputs",
    "Exact No-Final-Answer Boundary",
    "Exact No-Answer-Composition Boundary",
    "Exact No-Runtime Boundary",
    "Exact No-Provider / Search / Advisor Boundary",
    "Validation-Before-Execution Policy",
    "Future Controlled Execution Artifact Shape",
    "Denied Authority Fields",
    "Blocked Execution Behavior",
    "Visible Risks",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "model_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "dry-run-result-as-final-answer",
    "validation-pass-as-answer-authority",
    "result-artifact-as-runtime-readiness",
    "metadata-as-authority",
    "REVIEW_CONTROLLED_ANSWER_FORMATION_EXECUTION_BOUNDARY_V1",
}

_controlled_answer_formation_execution_boundary_review_doc = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_BOUNDARY_REVIEW_V1.md"
_controlled_answer_formation_execution_boundary_review_required_markers = {
    "WESLR Controlled Answer Formation Execution Boundary Review V1",
    "controlled_answer_formation_execution_boundary_design_valid_ready_for_context_alignment",
    "review report only",
    "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_BOUNDARY_V1.md",
    "design-only",
    "boundary-only",
    "metadata-controlled",
    "no controlled execution implementation",
    "no answer formation execution",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no `ChatResponder` calls",
    "no `respond_chat()` calls",
    "no `generate_chat()` calls",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no execution result artifact created",
    "why dry-run result does not grant execution authority",
    "allowed controlled/synthetic metadata inputs",
    "forbidden real-user/live inputs",
    "validation-before-execution policy",
    "future controlled execution artifact shape",
    "Denied Authority Fields",
    "blocked execution behavior",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "model_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "No gaps found",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_FORMATION_EXECUTION_BOUNDARY_V1",
}

_controlled_answer_formation_execution_helpers_design_doc = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_HELPERS_V1.md"
_controlled_answer_formation_execution_helpers_design_required_markers = {
    "WESLR Controlled Answer Formation Execution Helpers V1",
    "controlled_answer_formation_execution_helpers_design_defined",
    "design document only",
    "helper-only, metadata-controlled answer formation execution helper layer",
    "weslr/controlled_answer_formation_execution.py",
    "weslr/tests/test_controlled_answer_formation_execution_v1.py",
    "build_controlled_answer_formation_execution_artifact_v1",
    "validate_controlled_answer_formation_execution_artifact_v1",
    "summarize_controlled_answer_formation_execution_artifact_v1",
    "render_controlled_answer_formation_execution_artifact_markdown_v1",
    "to_controlled_answer_formation_execution_artifact_json_safe_v1",
    "controlled_answer_formation_execution_artifact_v1",
    "controlled_answer_formation_execution_artifact_schema_v1",
    "Allowed Controlled / Synthetic Metadata Inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "Relationship to Existing Answer Formation Helpers",
    "Relationship to Dry-Run Result Artifact",
    "Validation-Before-Controlled-Execution Policy",
    "No-Final-Answer Policy",
    "No-Answer-Composition Policy",
    "No-Runtime Policy",
    "No-Provider / Search / Advisor Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Blocked Artifact Behavior",
    "Denied Authority Fields",
    "Visible Risks",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "model_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "controlled_execution_result_artifact_created=false",
    "dry-run-result-as-controlled-execution-authority",
    "validation-pass-as-answer-authority",
    "metadata-as-authority",
    "REVIEW_CONTROLLED_ANSWER_FORMATION_EXECUTION_HELPERS_V1",
}

_controlled_answer_formation_execution_helpers_review_doc = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_HELPERS_REVIEW_V1.md"
_controlled_answer_formation_execution_helpers_review_required_markers = {
    "WESLR Controlled Answer Formation Execution Helpers Review V1",
    "controlled_answer_formation_execution_helpers_design_valid_ready_for_context_alignment",
    "review report only",
    "design-only",
    "helper-design-only",
    "metadata-controlled",
    "no helper implementation",
    "no controlled execution",
    "no answer formation execution",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no `ChatResponder` calls",
    "no `respond_chat()` calls",
    "no `generate_chat()` calls",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "no runtime authority granted",
    "no official evaluation authority granted",
    "no execution result artifact created",
    "weslr/controlled_answer_formation_execution.py",
    "weslr/tests/test_controlled_answer_formation_execution_v1.py",
    "build_controlled_answer_formation_execution_artifact_v1",
    "validate_controlled_answer_formation_execution_artifact_v1",
    "summarize_controlled_answer_formation_execution_artifact_v1",
    "render_controlled_answer_formation_execution_artifact_markdown_v1",
    "to_controlled_answer_formation_execution_artifact_json_safe_v1",
    "controlled execution artifact shape",
    "allowed controlled/synthetic metadata inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "relationship to existing answer formation helpers",
    "relationship to dry-run result artifact",
    "validation-before-controlled-execution policy",
    "no-final-answer policy",
    "no-answer-composition policy",
    "no-runtime policy",
    "safe Markdown policy",
    "JSON-safe policy",
    "blocked artifact behavior",
    "Denied Authority Fields",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "model_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "controlled_execution_result_artifact_created=false",
    "dry-run-result-as-controlled-execution-authority",
    "validation-pass-as-answer-authority",
    "metadata-as-authority",
    "No gaps found",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_FORMATION_EXECUTION_HELPERS_V1",
}

_controlled_answer_formation_execution_helpers_implementation_review_doc = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_controlled_answer_formation_execution_helpers_implementation_review_required_markers = {
    "WESLR Controlled Answer Formation Execution Helpers Implementation Review V1",
    "controlled_answer_formation_execution_helpers_implementation_valid_ready_for_context_alignment",
    "implementation review report only",
    "weslr/controlled_answer_formation_execution.py",
    "weslr/tests/test_controlled_answer_formation_execution_v1.py",
    "build_controlled_answer_formation_execution_artifact_v1",
    "validate_controlled_answer_formation_execution_artifact_v1",
    "summarize_controlled_answer_formation_execution_artifact_v1",
    "render_controlled_answer_formation_execution_artifact_markdown_v1",
    "to_controlled_answer_formation_execution_artifact_json_safe_v1",
    "helper-only",
    "metadata-controlled",
    "synthetic/control-input only",
    "deterministic",
    "import-safe",
    "side-effect-free",
    "in-memory only",
    "internal-only",
    "qualitative-only",
    "validation-before-rendering",
    "safe Markdown only",
    "JSON-safe",
    "blocked-artifact aware",
    "no-authority preserving",
    "no controlled execution",
    "no answer formation execution",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no `ChatResponder` calls",
    "no `respond_chat()` calls",
    "no `generate_chat()` calls",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no execution result artifact created",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "model_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "controlled_execution_result_artifact_created=false",
    "No implementation gaps found",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_FORMATION_EXECUTION_HELPERS_IMPLEMENTATION_V1",
}

_controlled_answer_formation_execution_result_design_doc = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_V1.md"
_controlled_answer_formation_execution_result_design_required_markers = {
    "WESLR Controlled Answer Formation Execution Result V1",
    "controlled_answer_formation_execution_result_design_defined",
    "design document only",
    "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_ARTIFACT_V1.md",
    "build_controlled_answer_formation_execution_artifact_v1",
    "validate_controlled_answer_formation_execution_artifact_v1",
    "summarize_controlled_answer_formation_execution_artifact_v1",
    "render_controlled_answer_formation_execution_artifact_markdown_v1",
    "to_controlled_answer_formation_execution_artifact_json_safe_v1",
    "Relationship to Controlled Helper Implementation",
    "Relationship to Dry-Run Result Artifact",
    "Allowed Controlled / Synthetic Metadata Inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "Validation-Before-Result-Writing Policy",
    "Safe Markdown Result Policy",
    "JSON-Safe Result Policy",
    "Denied Authority Fields",
    "Blocked Result Behavior",
    "Exact No-Final-Answer Boundary",
    "Exact No-Answer-Composition Boundary",
    "Exact No-Runtime Boundary",
    "Exact No-Provider / Search / Advisor Boundary",
    "Visible Risks / Followups",
    "Abort Conditions",
    "Future Execution / Review / Context Sequence",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "model_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "controlled-execution-result-as-answer-authority",
    "validation-pass-as-answer-authority",
    "metadata-as-authority",
    "REVIEW_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_DESIGN_V1",
}

_controlled_answer_formation_execution_result_design_review_doc = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_DESIGN_REVIEW_V1.md"
_controlled_answer_formation_execution_result_design_review_required_markers = {
    "WESLR Controlled Answer Formation Execution Result Design Review V1",
    "controlled_answer_formation_execution_result_design_valid_ready_for_context_alignment",
    "review report only",
    "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_V1.md",
    "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_ARTIFACT_V1.md",
    "design-only",
    "result-design-only",
    "metadata-controlled",
    "no result artifact created",
    "no controlled execution",
    "no real answer formation execution",
    "no answer drafts",
    "no answer composition",
    "no final-answer generation",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no `ChatResponder` calls",
    "no `respond_chat()` calls",
    "no `generate_chat()` calls",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer authority granted",
    "no composition authority granted",
    "no runtime authority granted",
    "no official evaluation authority granted",
    "future execution/result purpose",
    "relationship to controlled helper implementation",
    "relationship to dry-run result artifact",
    "allowed controlled/synthetic metadata inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "validation-before-result-writing policy",
    "safe Markdown result policy",
    "JSON-safe result policy",
    "blocked result behavior",
    "exact no-final-answer boundary",
    "exact no-answer-composition boundary",
    "Exact No-Runtime Boundary",
    "exact no-provider/search/advisor boundary",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "model_call_made=false",
    "provider_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "No gaps found",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_DESIGN_REVIEW_V1",
}

_controlled_answer_formation_execution_result_artifact_doc = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_ARTIFACT_V1.md"
_controlled_answer_formation_execution_result_artifact_required_markers = {
    "WESLR Controlled Answer Formation Execution Result Artifact V1",
    "controlled_answer_formation_execution_result_artifact_v1",
    "internal_only_metadata_only_safe_markdown_json_safe_eligible_validation_backed",
    "controlled_synthetic_metadata_only",
    "OCC_OpenClaw_coding_execution_tool_not_WESLR",
    "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_V1.md",
    "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_DESIGN_REVIEW_V1.md",
    "weslr/controlled_answer_formation_execution.py",
    "weslr/tests/test_controlled_answer_formation_execution_v1.py",
    "build_controlled_answer_formation_execution_artifact_v1",
    "validate_controlled_answer_formation_execution_artifact_v1",
    "summarize_controlled_answer_formation_execution_artifact_v1",
    "render_controlled_answer_formation_execution_artifact_markdown_v1",
    "to_controlled_answer_formation_execution_artifact_json_safe_v1",
    "validation_pass_metadata_quality_evidence_only",
    "json_safe_eligible",
    "safe_markdown_eligible",
    "answer_formation_executed=false",
    "answer_composition_attempted=false",
    "final_answer_generated=false",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "model_call_made=false",
    "provider_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judge_authority_granted=false",
    "scoring_authorized=false",
    "controlled_execution_result_artifact_created=false",
    "no-final-answer boundary",
    "no-answer-composition boundary",
    "no-runtime boundary",
    "no-provider/search/advisor boundary",
    "result_artifact_does_not_grant_answer_authority",
    "result_artifact_does_not_grant_composition_authority",
    "result_artifact_does_not_grant_runtime_authority",
    "result_artifact_does_not_grant_official_evaluation_authority",
    "REVIEW_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_ARTIFACT_V1",
}

_controlled_answer_formation_execution_result_artifact_review_doc = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_ARTIFACT_REVIEW_V1.md"
_controlled_answer_formation_execution_result_artifact_review_required_markers = {
    "WESLR Controlled Answer Formation Execution Result Artifact Review V1",
    "controlled_answer_formation_execution_result_artifact_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_ARTIFACT_REVIEW_V1.md",
    "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_ARTIFACT_V1.md",
    "metadata_only_result_artifact_review",
    "exact_approved_artifact_path_confirmed",
    "internal_only: `True`",
    "metadata_only: `True`",
    "safe_markdown: `True`",
    "json_safe_eligible: `True`",
    "validation_backed: `True`",
    "controlled_synthetic_metadata_only: `True`",
    "helper_based: `True`",
    "no_raw_prompt_text: `True`",
    "no_raw_response_text: `True`",
    "no_private_content: `True`",
    "no_provider_output: `True`",
    "no_runtime_output: `True`",
    "no_answer_draft: `True`",
    "no_composed_reply: `True`",
    "no_final_answer_prose: `True`",
    "no_final_answer_generation: `True`",
    "no_answer_composition: `True`",
    "no_real_answer_formation_execution: `True`",
    "no_runtime_wiring: `True`",
    "no_prompt_live_dialogue: `True`",
    "no_chat_responder_respond_chat_generate_chat_calls: `True`",
    "no_provider_search_advisor_calls: `True`",
    "no_dot_weslr_writes: `True`",
    "no_feature_flags: `True`",
    "no_judges_scores: `True`",
    "no_official_benchmark_iq_turing_certification_claims: `True`",
    "no_answer_composition_runtime_official_evaluation_authority_granted: `True`",
    "weslr_chat_responder_py_untouched: `True`",
    "No gaps found",
    "review_report_only: `True`",
    "not_authority_grant: `True`",
    "`weslr/chat_responder.py` untouched",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_ARTIFACT_REVIEW_V1",
}

_controlled_answer_formation_chain_next_step_review_doc = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_CHAIN_NEXT_STEP_REVIEW_V1.md"
_controlled_answer_formation_chain_next_step_review_required_markers = {
    "WESLR Controlled Answer Formation Chain Next Step Review V1",
    "controlled_answer_formation_chain_valid_for_design_controlled_answer_composition_boundary_v1",
    "DESIGN_CONTROLLED_ANSWER_COMPOSITION_BOUNDARY_V1",
    "Metadata-only helper/report/dry-run/control-result structure exists",
    "real answer formation execution",
    "answer composition",
    "final-answer generation",
    "runtime readiness",
    "official Turing-test claim",
    "authority to wire runtime",
    "`weslr/chat_responder.py` stayed untouched",
    "No runtime/provider/search/advisor/.weslr paths were activated",
    "review/decision report",
    "answer_formation_authorized=false",
    "answer_composition_authorized=false",
    "runtime_authority_granted=false",
    "chat_responder_called=false",
    "runtime_wired=false",
}

_controlled_answer_composition_boundary_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_BOUNDARY_V1.md"
_controlled_answer_composition_boundary_required_markers = {
    "WESLR Controlled Answer Composition Boundary V1",
    "design-only boundary",
    "docs/WESLR_CONTROLLED_ANSWER_FORMATION_CHAIN_NEXT_STEP_REVIEW_V1.md",
    "controlled answer composition",
    "Why Controlled Answer Formation Result Does Not Grant Composition Authority",
    "Allowed Future Composition Metadata Inputs",
    "Forbidden Inputs",
    "Exact No-Final-Answer Boundary",
    "Exact No-User-Facing-Output Boundary",
    "Exact No-Runtime Boundary",
    "Exact No-Provider/Search/Advisor Boundary",
    "Validation-Before-Composition Policy",
    "Future Controlled Composition Artifact Shape",
    "Denied Authority Fields",
    "Blocked Composition Behavior",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation And Review Sequence",
    "implementation_authorized: false",
    "execution_authorized: false",
    "composition_authority_granted: false",
    "answer_authority_granted: false",
    "runtime_authority_granted: false",
    "final_answer_generated=false",
    "user_facing_output_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "REVIEW_CONTROLLED_ANSWER_COMPOSITION_BOUNDARY_V1",
}

_controlled_answer_composition_boundary_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_BOUNDARY_REVIEW_V1.md"
_controlled_answer_composition_boundary_review_required_markers = {
    "WESLR Controlled Answer Composition Boundary Review V1",
    "controlled_answer_composition_boundary_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_BOUNDARY_REVIEW_V1.md",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_BOUNDARY_V1.md",
    "design-only",
    "boundary-only",
    "composition-boundary-only",
    "metadata-only",
    "controlled answer composition implementation present: `False`",
    "composition execution authorized: `False`",
    "answer formation execution authorized: `False`",
    "final-answer generation authorized: `False`",
    "user-facing output authorized: `False`",
    "runtime wiring authorized: `False`",
    "provider/search/advisor calls authorized: `False`",
    "composition result artifact created: `False`",
    "`weslr/chat_responder.py` touched: `False`",
    "Controlled answer composition purpose",
    "Why controlled answer formation result does not grant composition authority",
    "Allowed future composition metadata inputs",
    "Forbidden real-user/live/raw/provider/runtime inputs",
    "Exact no-final-answer boundary",
    "Exact no-user-facing-output boundary",
    "Exact no-runtime boundary",
    "Exact no-provider/search/advisor boundary",
    "Validation-before-composition policy",
    "Controlled composition artifact shape for a future lane",
    "Denied authority fields",
    "Blocked composition behavior",
    "Visible risks/followups",
    "Abort conditions",
    "Future implementation/review sequence",
    "No blocking gaps found",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_COMPOSITION_BOUNDARY_V1",
}

_controlled_answer_composition_helpers_design_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_HELPERS_V1.md"
_controlled_answer_composition_helpers_design_required_markers = {
    "WESLR Controlled Answer Composition Helpers V1",
    "design-only helper specification",
    "weslr/controlled_answer_composition.py",
    "weslr/tests/test_controlled_answer_composition_v1.py",
    "build_controlled_answer_composition_artifact_v1",
    "validate_controlled_answer_composition_artifact_v1",
    "summarize_controlled_answer_composition_artifact_v1",
    "render_controlled_answer_composition_artifact_markdown_v1",
    "to_controlled_answer_composition_artifact_json_safe_v1",
    "controlled_answer_composition_artifact_v1",
    "Allowed Composition Metadata Inputs",
    "Forbidden Inputs",
    "Relationship To Controlled Answer Formation Result Artifact",
    "Relationship To Controlled Answer Composition Boundary",
    "Validation-Before-Composition Policy",
    "Validation-Before-Rendering Policy",
    "No-Final-Answer Policy",
    "No-User-Facing-Output Policy",
    "No-Runtime Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Blocked Artifact Behavior",
    "Denied Authority Fields",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation And Review Sequence",
    "implementation_authorized: false",
    "helper_implementation_authorized: false",
    "composition_execution_authorized: false",
    "final_answer_generation_authorized: false",
    "user_facing_output_authorized: false",
    "runtime_wiring_authorized: false",
    "final_answer_generated=false",
    "user_facing_output_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "REVIEW_CONTROLLED_ANSWER_COMPOSITION_HELPERS_V1",
}

_controlled_answer_composition_helpers_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_HELPERS_REVIEW_V1.md"
_controlled_answer_composition_helpers_review_required_markers = {
    "WESLR Controlled Answer Composition Helpers Review V1",
    "controlled_answer_composition_helpers_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_HELPERS_REVIEW_V1.md",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_HELPERS_V1.md",
    "design-only",
    "helper-design-only",
    "metadata-only",
    "controlled answer composition helper implementation present: `False`",
    "composition execution authorized: `False`",
    "answer formation execution authorized: `False`",
    "final-answer generation authorized: `False`",
    "user-facing output authorized: `False`",
    "runtime wiring authorized: `False`",
    "provider/search/advisor calls authorized: `False`",
    "composition result artifact created: `False`",
    "`weslr/chat_responder.py` touched: `False`",
    "Future helper module path",
    "Future test module path",
    "Future public API names",
    "Controlled composition artifact shape",
    "Allowed composition metadata inputs",
    "Forbidden real-user/live/raw/provider/runtime inputs",
    "Relationship to controlled answer formation result artifact",
    "Relationship to controlled answer composition boundary",
    "Validation-before-composition policy",
    "Validation-before-rendering policy",
    "No-final-answer policy",
    "No-user-facing-output policy",
    "No-runtime policy",
    "Safe Markdown policy",
    "JSON-safe policy",
    "Blocked artifact behavior",
    "Denied authority fields",
    "Visible risks/followups",
    "Abort conditions",
    "Future implementation/review sequence",
    "No blocking gaps found",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_COMPOSITION_HELPERS_V1",
}

_controlled_answer_composition_helpers_implementation_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_controlled_answer_composition_helpers_implementation_review_required_markers = {
    "WESLR Controlled Answer Composition Helpers Implementation Review V1",
    "controlled_answer_composition_helpers_implementation_valid_ready_for_context_alignment",
    "weslr/controlled_answer_composition.py",
    "weslr/tests/test_controlled_answer_composition_v1.py",
    "build_controlled_answer_composition_artifact_v1",
    "validate_controlled_answer_composition_artifact_v1",
    "summarize_controlled_answer_composition_artifact_v1",
    "render_controlled_answer_composition_artifact_markdown_v1",
    "to_controlled_answer_composition_artifact_json_safe_v1",
    "helper-only",
    "metadata-only",
    "internal-only",
    "deterministic",
    "pure in-memory",
    "JSON-safe",
    "safe-Markdown capable",
    "validation-before-rendering",
    "no-runtime",
    "no-user-facing-output",
    "no-authority",
    "No blocking implementation gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_COMPOSITION_HELPERS_IMPLEMENTATION_V1",
}

_controlled_answer_composition_result_design_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_RESULT_V1.md"
_controlled_answer_composition_result_design_required_markers = {
    "WESLR Controlled Answer Composition Result V1",
    "Design-only document for a future controlled answer composition result artifact.",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_RESULT_ARTIFACT_V1.md",
    "Allowed Source Helper Output",
    "Validation-Before-Result-Writing Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Denied Authority Fields",
    "Blocked / Invalid Result Behavior",
    "No-Final-Answer Boundary",
    "No-Answer-Draft Boundary",
    "No-User-Facing-Output Boundary",
    "No-Runtime Boundary",
    "No-Provider / Search / Advisor Boundary",
    "No-Official-Claims Boundary",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "answer_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "final_answer_generated=false",
    "answer_draft_created=false",
    "user_facing_output_created=false",
    "provider_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "REVIEW_CONTROLLED_ANSWER_COMPOSITION_RESULT_DESIGN_V1",
}

_controlled_answer_composition_result_design_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_RESULT_DESIGN_REVIEW_V1.md"
_controlled_answer_composition_result_design_review_required_markers = {
    "WESLR Controlled Answer Composition Result Design Review V1",
    "controlled_answer_composition_result_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_RESULT_V1.md",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_RESULT_ARTIFACT_V1.md",
    "design-only",
    "result-design-only",
    "metadata-only",
    "internal-only",
    "helper-output based",
    "validation-before-result-writing",
    "safe-Markdown bounded",
    "JSON-safe bounded",
    "no result artifact created",
    "no composition execution",
    "no answer formation execution",
    "no final-answer generation",
    "no drafts",
    "no user-facing output",
    "no runtime wiring",
    "no provider/search/advisor calls",
    "no official claims",
    "No blocking design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_COMPOSITION_RESULT_DESIGN_V1",
}

_controlled_answer_composition_result_artifact_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_RESULT_ARTIFACT_V1.md"
_controlled_answer_composition_result_artifact_required_markers = {
    "WESLR Controlled Answer Composition Result Artifact V1",
    "controlled_answer_composition_result_artifact_v1",
    "REVIEW_CONTROLLED_ANSWER_COMPOSITION_RESULT_ARTIFACT_V1",
    "build_controlled_answer_composition_artifact_v1",
    "validate_controlled_answer_composition_artifact_v1",
    "summarize_controlled_answer_composition_artifact_v1",
    "render_controlled_answer_composition_artifact_markdown_v1",
    "to_controlled_answer_composition_artifact_json_safe_v1",
    "internal-only",
    "metadata-only",
    "helper-output based",
    "validation-backed",
    "JSON-safe eligible",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "final_answer_generated=false",
    "answer_draft_created=false",
    "user_facing_output_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "official_claim_made=false",
}

_controlled_answer_composition_result_artifact_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_RESULT_ARTIFACT_REVIEW_V1.md"
_controlled_answer_composition_result_artifact_review_required_markers = {
    "WESLR Controlled Answer Composition Result Artifact Review V1",
    "controlled_answer_composition_result_artifact_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_RESULT_ARTIFACT_V1.md",
    "exactly the approved artifact path",
    "internal-only",
    "metadata-only",
    "helper-output based",
    "validation-backed",
    "safe Markdown",
    "JSON-safe eligible",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "controlled/synthetic metadata only",
    "created using only approved helper API",
    "not composition execution",
    "not answer formation execution",
    "not final-answer generation",
    "not answer draft creation",
    "not user-facing output",
    "not live chat behavior",
    "not runtime readiness",
    "not provider/search/advisor output",
    "not official benchmark/IQ/Turing/certification/product-readiness evidence",
    "No blocking artifact gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_ANSWER_COMPOSITION_RESULT_ARTIFACT_REVIEW_V1",
}

_controlled_answer_composition_chain_next_step_review_doc = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_CHAIN_NEXT_STEP_REVIEW_V1.md"
_controlled_answer_composition_chain_next_step_review_required_markers = {
    "WESLR Controlled Answer Composition Chain Next Step Review V1",
    "controlled_answer_composition_chain_reviewed_next_step_design_controlled_final_answer_generation_boundary_v1",
    "DESIGN_CONTROLLED_FINAL_ANSWER_GENERATION_BOUNDARY_V1",
    "metadata-only controlled answer composition structures exist",
    "helper implementation exists for safe internal composition metadata",
    "controlled composition result artifact exists",
    "denied authority fields stayed false",
    "validation/release checks passed",
    "weslr/chat_responder.py` stayed untouched",
    "no runtime/provider/search/advisor/.weslr paths were activated",
    "answer composition execution",
    "answer formation execution",
    "final-answer generation",
    "answer correctness",
    "user-facing output",
    "live chat behavior",
    "runtime readiness",
    "official Turing-test claim",
    "IQ claim",
    "certification claim",
    "product readiness",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "result-artifact-as-execution risk",
    "safe-Markdown-as-user-output risk",
    "No blocking gaps were found",
}

_controlled_final_answer_generation_boundary_doc = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_BOUNDARY_V1.md"
_controlled_final_answer_generation_boundary_required_markers = {
    "WESLR Controlled Final Answer Generation Boundary V1",
    "controlled final-answer generation boundary",
    "DESIGN_CONTROLLED_FINAL_ANSWER_GENERATION_BOUNDARY_V1",
    "REVIEW_CONTROLLED_FINAL_ANSWER_GENERATION_BOUNDARY_V1",
    "controlled answer formation metadata",
    "controlled answer composition metadata",
    "controlled final-answer generation",
    "answer drafts",
    "user-facing output",
    "runtime/live chat integration",
    "provider/model/search/advisor calls",
    "official evaluation claims",
    "authority grants",
    "Allowed Future Final-Answer Metadata Inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "Exact No-User-Facing-Output Boundary",
    "Exact No-Runtime Boundary",
    "Exact No-Provider / Search / Advisor Boundary",
    "Exact No-Official-Claims Boundary",
    "Validation-Before-Final-Answer-Generation Policy",
    "Controlled Final-Answer Artifact Shape For Future Lane",
    "Denied Authority Fields",
    "Blocked Final-Answer-Generation Behavior",
    "Visible Risks And Followups",
    "Abort Conditions",
    "final_answer_generation_implemented: false",
    "final_answer_generation_executed: false",
    "answer_draft_created: false",
    "user_facing_output_created: false",
    "runtime_wired: false",
    "provider_call_made: false",
    "official_claim_made: false",
    "answer_authority_granted: false",
    "composition_authority_granted: false",
    "runtime_authority_granted: false",
    "official_evaluation_authority_granted: false",
}

_controlled_final_answer_generation_boundary_review_doc = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_BOUNDARY_REVIEW_V1.md"
_controlled_final_answer_generation_boundary_review_required_markers = {
    "WESLR Controlled Final Answer Generation Boundary Review V1",
    "controlled_final_answer_generation_boundary_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_BOUNDARY_V1.md",
    "design-only",
    "boundary-only",
    "final-answer-generation-boundary-only",
    "metadata-only",
    "no final-answer generation implementation",
    "no final-answer generation execution",
    "no answer drafts",
    "no user-facing output",
    "no answer composition execution",
    "no answer formation execution",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer/composition/runtime/official evaluation authority granted",
    "no final-answer result artifact created",
    "weslr/chat_responder.py` untouched",
    "No blocking gaps found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_FINAL_ANSWER_GENERATION_BOUNDARY_V1",
}

_controlled_final_answer_generation_helpers_doc = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_HELPERS_V1.md"
_controlled_final_answer_generation_helpers_required_markers = {
    "WESLR Controlled Final-Answer Generation Helpers V1",
    "DESIGN_CONTROLLED_FINAL_ANSWER_GENERATION_HELPERS_V1",
    "REVIEW_CONTROLLED_FINAL_ANSWER_GENERATION_HELPERS_V1",
    "weslr/controlled_final_answer_generation.py",
    "weslr/tests/test_controlled_final_answer_generation_v1.py",
    "build_controlled_final_answer_generation_artifact_v1",
    "validate_controlled_final_answer_generation_artifact_v1",
    "summarize_controlled_final_answer_generation_artifact_v1",
    "render_controlled_final_answer_generation_artifact_markdown_v1",
    "to_controlled_final_answer_generation_artifact_json_safe_v1",
    "Controlled Final-Answer Artifact Shape",
    "Allowed Final-Answer Metadata Inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "Validation-Before-Final-Answer-Generation Metadata Policy",
    "Validation-Before-Rendering Policy",
    "No-User-Facing-Output Policy",
    "No-Runtime Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Blocked Artifact Behavior",
    "Denied Authority Fields",
    "Visible Risks And Followups",
    "Abort Conditions",
    "helper_implementation_created: false",
    "controlled_final_answer_generation_executed: false",
    "final_answer_generated: false",
    "answer_draft_created: false",
    "user_facing_output_created: false",
    "runtime_wired: false",
    "chat_responder_called: false",
    "provider_call_made: false",
    "official_claim_made: false",
    "answer_authority_granted: false",
    "composition_authority_granted: false",
    "runtime_authority_granted: false",
    "official_evaluation_authority_granted: false",
}

_controlled_final_answer_generation_helpers_review_doc = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_HELPERS_REVIEW_V1.md"
_controlled_final_answer_generation_helpers_review_required_markers = {
    "WESLR Controlled Final-Answer Generation Helpers Review V1",
    "controlled_final_answer_generation_helpers_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_HELPERS_V1.md",
    "design-only",
    "helper-design-only",
    "metadata-only",
    "internal-only",
    "no controlled final-answer generation helper implementation",
    "no final-answer generation execution",
    "no answer drafts",
    "no user-facing output",
    "no answer composition execution",
    "no answer formation execution",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer/composition/runtime/official evaluation authority granted",
    "no final-answer result artifact created",
    "`weslr/chat_responder.py` untouched",
    "Future helper module path",
    "Future test module path",
    "Future public API names",
    "Controlled final-answer metadata artifact shape",
    "Allowed final-answer metadata inputs",
    "Forbidden real-user/live/raw/provider/runtime inputs",
    "Relationship to controlled answer composition result artifact",
    "Relationship to controlled final-answer generation boundary",
    "Validation-before-final-answer-generation metadata policy",
    "Validation-before-rendering policy",
    "No-user-facing-output policy",
    "No-runtime policy",
    "Safe Markdown policy",
    "JSON-safe policy",
    "Blocked artifact behavior",
    "Denied authority fields",
    "Visible risks/followups",
    "Abort conditions",
    "Future implementation/review sequence",
    "No blocking gaps found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_FINAL_ANSWER_GENERATION_HELPERS_V1",
}

_controlled_final_answer_generation_helpers_implementation_review_doc = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_controlled_final_answer_generation_helpers_implementation_review_required_markers = {
    "WESLR Controlled Final-Answer Generation Helpers Implementation Review V1",
    "controlled_final_answer_generation_helpers_implementation_valid_ready_for_context_alignment",
    "weslr/controlled_final_answer_generation.py",
    "weslr/tests/test_controlled_final_answer_generation_v1.py",
    "helper-only",
    "metadata-only",
    "internal-only",
    "deterministic",
    "pure in-memory",
    "JSON-safe",
    "safe-Markdown capable",
    "validation-before-rendering",
    "no-runtime",
    "no-user-facing-output",
    "no-authority",
    "no actual final-answer generation",
    "no answer drafts",
    "no answer prose for users",
    "build_controlled_final_answer_generation_artifact_v1",
    "validate_controlled_final_answer_generation_artifact_v1",
    "summarize_controlled_final_answer_generation_artifact_v1",
    "render_controlled_final_answer_generation_artifact_markdown_v1",
    "to_controlled_final_answer_generation_artifact_json_safe_v1",
    "result artifact writer API",
    "final-answer execution API",
    "answer draft API",
    "user-facing output API",
    "runtime wiring API",
    "ChatResponder/respond_chat/generate_chat import or call",
    "provider/model/search/advisor import or call",
    "No blocking implementation gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_FINAL_ANSWER_GENERATION_HELPERS_IMPLEMENTATION_V1",
}

_controlled_final_answer_generation_result_design_doc = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_V1.md"
_controlled_final_answer_generation_result_design_required_markers = {
    "WESLR Controlled Final-Answer Generation Result V1",
    "DESIGN_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_V1",
    "REVIEW_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_DESIGN_V1",
    "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_ARTIFACT_V1.md",
    "Allowed Source Helper Output",
    "Validation-Before-Result-Writing Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Denied Authority Fields",
    "Blocked / Invalid Result Behavior",
    "No-Final-Answer-Execution Boundary",
    "No-Answer-Draft Boundary",
    "No-User-Facing-Output Boundary",
    "No-Runtime Boundary",
    "No-Provider / Search / Advisor Boundary",
    "No-Official-Claims Boundary",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "result_artifact_created: false",
    "final_answer_generation_executed: false",
    "final_answer_generated: false",
    "final_answer_prose_created: false",
    "answer_draft_created: false",
    "user_facing_output_created: false",
    "answer_composition_executed: false",
    "answer_formation_executed: false",
    "runtime_wired: false",
    "chat_responder_called: false",
    "respond_chat_called: false",
    "generate_chat_called: false",
    "provider_call_made: false",
    "model_call_made: false",
    "search_call_made: false",
    "advisor_call_made: false",
    "dot_weslr_write_performed: false",
    "feature_flag_enabled: false",
    "judges_created: false",
    "scores_created: false",
    "official_claim_made: false",
    "answer_authority_granted: false",
    "composition_authority_granted: false",
    "runtime_authority_granted: false",
    "official_evaluation_authority_granted: false",
}

_controlled_final_answer_generation_result_design_review_doc = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_DESIGN_REVIEW_V1.md"
_controlled_final_answer_generation_result_design_review_required_markers = {
    "WESLR Controlled Final-Answer Generation Result Design Review V1",
    "controlled_final_answer_generation_result_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_V1.md",
    "design-only",
    "result-design-only",
    "metadata-only",
    "internal-only",
    "helper-output based",
    "validation-before-result-writing",
    "safe-Markdown bounded",
    "JSON-safe bounded",
    "no result artifact created",
    "no actual final-answer generation",
    "no final-answer prose",
    "no answer drafts",
    "no user-facing output",
    "no composition execution",
    "no formation execution",
    "no runtime wiring",
    "no prompt/live dialogue",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no answer/composition/runtime/official evaluation authority granted",
    "weslr/chat_responder.py` untouched",
    "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_ARTIFACT_V1.md",
    "Allowed Source Helper Output",
    "Validation-Before-Result-Writing Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Denied Authority Fields",
    "Blocked / Invalid Result Behavior",
    "No blocking design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_DESIGN_V1",
}


_controlled_final_answer_generation_result_artifact_doc = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_ARTIFACT_V1.md"
_controlled_final_answer_generation_result_artifact_required_markers = {
    "WESLR Controlled Final-Answer Generation Result Artifact V1",
    "controlled_final_answer_generation_result_artifact_v1",
    "REVIEW_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_ARTIFACT_V1",
    "build_controlled_final_answer_generation_artifact_v1",
    "validate_controlled_final_answer_generation_artifact_v1",
    "summarize_controlled_final_answer_generation_artifact_v1",
    "render_controlled_final_answer_generation_artifact_markdown_v1",
    "to_controlled_final_answer_generation_artifact_json_safe_v1",
    "internal-only",
    "metadata-only",
    "helper-output based",
    "validation-backed",
    "JSON-safe eligible",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "controlled/synthetic metadata only",
    "final_answer_generation_executed=false",
    "final_answer_generated=false",
    "final_answer_prose_created=false",
    "answer_draft_created=false",
    "user_facing_output_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "official_claim_made=false",
}


_controlled_final_answer_generation_result_artifact_review_doc = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_ARTIFACT_REVIEW_V1.md"
_controlled_final_answer_generation_result_artifact_review_required_markers = {
    "WESLR Controlled Final-Answer Generation Result Artifact Review V1",
    "controlled_final_answer_generation_result_artifact_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_ARTIFACT_V1.md",
    "exactly the approved artifact path",
    "internal-only",
    "metadata-only",
    "helper-output based",
    "validation-backed",
    "safe Markdown",
    "JSON-safe eligible",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "controlled/synthetic metadata only",
    "created using only approved helper API",
    "not actual final-answer generation",
    "not final-answer prose",
    "not answer draft creation",
    "not user-facing output",
    "not answer composition execution",
    "not answer formation execution",
    "not live chat behavior",
    "not runtime readiness",
    "not provider/search/advisor output",
    "not official benchmark/IQ/Turing/certification/product-readiness evidence",
    "not answer authority",
    "not composition authority",
    "not runtime authority",
    "not official evaluation authority",
    "No blocking artifact gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_ARTIFACT_REVIEW_V1",
}

_controlled_final_answer_generation_chain_next_step_review_doc = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_CHAIN_NEXT_STEP_REVIEW_V1.md"
_controlled_final_answer_generation_chain_next_step_review_required_markers = {
    "WESLR Controlled Final-Answer Generation Chain Next Step Review V1",
    "controlled_final_answer_generation_chain_reviewed_next_step_design_controlled_user_facing_output_boundary_v1",
    "DESIGN_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_V1",
    "metadata-only controlled final-answer-generation structures exist",
    "helper implementation exists for safe internal final-answer-generation metadata",
    "controlled final-answer generation result artifact exists",
    "denied authority fields stayed false",
    "validation/release checks passed",
    "weslr/chat_responder.py` stayed untouched",
    "no runtime/provider/search/advisor/.weslr paths were activated",
    "actual final-answer generation",
    "final-answer prose",
    "answer draft creation",
    "user-facing output",
    "answer correctness",
    "answer composition execution",
    "answer formation execution",
    "live chat behavior",
    "runtime readiness",
    "provider/search/advisor integration",
    "official Turing-test claim",
    "IQ claim",
    "certification claim",
    "product readiness",
    "authority to answer users",
    "authority to wire runtime",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "result-artifact-as-execution risk",
    "safe-Markdown-as-user-output risk",
    "No blocking gaps were found",
}

_controlled_user_facing_output_boundary_doc = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_V1.md"
_controlled_user_facing_output_boundary_required_markers = {
    "WESLR Controlled User-Facing Output Boundary V1",
    "DESIGN_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_V1",
    "REVIEW_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_V1",
    "controlled answer formation metadata",
    "controlled answer composition metadata",
    "controlled final-answer-generation metadata",
    "controlled user-facing output",
    "live chat behavior",
    "runtime wiring",
    "ChatResponder/respond_chat/generate_chat activation",
    "provider/model/search/advisor calls",
    "official evaluation claims",
    "answer authority / runtime authority / product-readiness authority",
    "Controlled User-Facing Output Purpose",
    "Why Controlled Final-Answer Generation Result Does Not Grant User-Facing-Output Authority",
    "Allowed Future User-Facing-Output Metadata Inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "Exact No-Live-Chat Boundary",
    "Exact No-Runtime Boundary",
    "Exact No-ChatResponder / respond_chat / generate_chat Boundary",
    "Exact No-Provider / Search / Advisor Boundary",
    "Exact No-Official-Claims Boundary",
    "Validation-Before-User-Facing-Output Policy",
    "Controlled User-Facing-Output Artifact Shape For A Future Lane",
    "Denied Authority Fields",
    "Blocked User-Facing-Output Behavior",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "user_facing_output_implementation_authorized: false",
    "user_facing_output_execution_authorized: false",
    "live_chat_behavior_authorized: false",
    "runtime_wiring_authorized: false",
    "chat_responder_called: false",
    "respond_chat_called: false",
    "generate_chat_called: false",
    "provider_call_made: false",
    "model_call_made: false",
    "search_call_made: false",
    "advisor_call_made: false",
    "dot_weslr_write_performed: false",
    "feature_flag_enabled: false",
    "judges_created: false",
    "scores_created: false",
    "official_claim_made: false",
    "answer_authority_granted: false",
    "user_facing_output_authority_granted: false",
    "composition_authority_granted: false",
    "runtime_authority_granted: false",
    "official_evaluation_authority_granted: false",
}

_controlled_user_facing_output_boundary_review_doc = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_REVIEW_V1.md"
_controlled_user_facing_output_boundary_review_required_markers = {
    "WESLR Controlled User-Facing Output Boundary Review V1",
    "controlled_user_facing_output_boundary_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_V1.md",
    "design-only",
    "boundary-only",
    "user-facing-output-boundary-only",
    "metadata-only",
    "no user-facing output implementation",
    "no user-facing output execution",
    "no final-answer generation execution",
    "no answer drafts",
    "no final-answer prose intended for users",
    "no live chat behavior",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scoring",
    "no official claims",
    "no answer/user-facing-output/composition/runtime/official evaluation authority granted",
    "no user-facing-output result artifact created",
    "weslr/chat_responder.py` untouched",
    "controlled user-facing output purpose",
    "why controlled final-answer-generation result does not grant user-facing-output authority",
    "allowed future user-facing-output metadata inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "exact no-live-chat boundary",
    "Exact No-Runtime Boundary",
    "Exact No-ChatResponder / respond_chat / generate_chat Boundary",
    "exact no-provider/search/advisor boundary",
    "Exact No-Official-Claims Boundary",
    "validation-before-user-facing-output policy",
    "controlled user-facing-output artifact shape for a future lane",
    "Denied Authority Fields",
    "blocked user-facing-output behavior",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "No blocking design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_V1",
}

_controlled_user_facing_output_helpers_doc = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_HELPERS_V1.md"
_controlled_user_facing_output_helpers_required_markers = {
    "WESLR Controlled User-Facing Output Helpers V1",
    "DESIGN_CONTROLLED_USER_FACING_OUTPUT_HELPERS_V1",
    "REVIEW_CONTROLLED_USER_FACING_OUTPUT_HELPERS_V1",
    "weslr/controlled_user_facing_output.py",
    "weslr/tests/test_controlled_user_facing_output_v1.py",
    "build_controlled_user_facing_output_artifact_v1",
    "validate_controlled_user_facing_output_artifact_v1",
    "summarize_controlled_user_facing_output_artifact_v1",
    "render_controlled_user_facing_output_artifact_markdown_v1",
    "to_controlled_user_facing_output_artifact_json_safe_v1",
    "Controlled User-Facing-Output Artifact Shape",
    "Allowed User-Facing-Output Metadata Inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "Relationship To Controlled Final-Answer-Generation Result Artifact",
    "Relationship To Controlled User-Facing Output Boundary",
    "Validation-Before-User-Facing-Output Policy",
    "Validation-Before-Rendering Policy",
    "No-Live-Chat Policy",
    "No-Runtime Policy",
    "No-ChatResponder / respond_chat / generate_chat Policy",
    "No-Provider / Search / Advisor Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Blocked Artifact Behavior",
    "Denied Authority Fields",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "helper_implementation_created: false",
    "user_facing_output_executed: false",
    "actual_reply_text_created: false",
    "live_dialogue_output_created: false",
    "real_user_query_answered: false",
    "final_answer_generation_executed: false",
    "answer_draft_created: false",
    "runtime_wired: false",
    "chat_responder_called: false",
    "respond_chat_called: false",
    "generate_chat_called: false",
    "provider_call_made: false",
    "model_call_made: false",
    "search_call_made: false",
    "advisor_call_made: false",
    "official_claim_made: false",
    "answer_authority_granted: false",
    "user_facing_output_authority_granted: false",
    "runtime_authority_granted: false",
    "official_evaluation_authority_granted: false",
}

_controlled_user_facing_output_helpers_review_doc = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_HELPERS_REVIEW_V1.md"
_controlled_user_facing_output_helpers_review_required_markers = {
    "WESLR Controlled User-Facing Output Helpers Review V1",
    "controlled_user_facing_output_helpers_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_HELPERS_V1.md",
    "design-only",
    "helper-design-only",
    "metadata-only",
    "internal-only",
    "no controlled user-facing output helper implementation",
    "no user-facing output execution",
    "no reply text creation",
    "no live dialogue output",
    "no final-answer generation execution",
    "no final answers",
    "no answer drafts",
    "no answer composition execution",
    "no answer formation execution",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls",
    "no provider/search/advisor calls",
    "no `.weslr` writes",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no answer/user-facing-output/composition/runtime/official evaluation authority granted",
    "no user-facing-output result artifact created",
    "weslr/chat_responder.py` untouched",
    "future helper module path",
    "future test module path",
    "future public API names",
    "controlled user-facing-output artifact shape",
    "allowed user-facing-output metadata inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "relationship to controlled final-answer-generation result artifact",
    "relationship to controlled user-facing output boundary",
    "validation-before-user-facing-output policy",
    "validation-before-rendering policy",
    "no-live-chat policy",
    "no-runtime policy",
    "no-ChatResponder/respond_chat/generate_chat policy",
    "no-provider/search/advisor policy",
    "safe Markdown policy",
    "JSON-safe policy",
    "blocked artifact behavior",
    "Denied Authority Fields",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "No blocking design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_USER_FACING_OUTPUT_HELPERS_V1",
}

_controlled_user_facing_output_helpers_implementation_review_doc = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_controlled_user_facing_output_helpers_implementation_review_required_markers = {
    "WESLR Controlled User-Facing Output Helpers Implementation Review V1",
    "controlled_user_facing_output_helpers_implementation_valid_ready_for_context_alignment",
    "weslr/controlled_user_facing_output.py",
    "weslr/tests/test_controlled_user_facing_output_v1.py",
    "build_controlled_user_facing_output_artifact_v1",
    "validate_controlled_user_facing_output_artifact_v1",
    "summarize_controlled_user_facing_output_artifact_v1",
    "render_controlled_user_facing_output_artifact_markdown_v1",
    "to_controlled_user_facing_output_artifact_json_safe_v1",
    "helper-only",
    "metadata-only",
    "internal-only",
    "validation-before-rendering",
    "no user-facing output execution",
    "no actual reply text creation",
    "no final-answer prose",
    "no final answers",
    "no answer drafts",
    "no runtime wiring",
    "no `ChatResponder`/`respond_chat`/`generate_chat` imports or calls",
    "no provider/search/advisor/model calls",
    "no `.weslr` reads/writes",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no authority grants",
    "`weslr/chat_responder.py` untouched",
    "No blocking implementation gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_USER_FACING_OUTPUT_HELPERS_IMPLEMENTATION_V1",
}

_controlled_user_facing_output_result_design_doc = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_RESULT_V1.md"
_controlled_user_facing_output_result_design_required_markers = {
    "WESLR Controlled User-Facing Output Result V1",
    "DESIGN_CONTROLLED_USER_FACING_OUTPUT_RESULT_V1",
    "REVIEW_CONTROLLED_USER_FACING_OUTPUT_RESULT_DESIGN_V1",
    "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_RESULT_ARTIFACT_V1.md",
    "build_controlled_user_facing_output_artifact_v1",
    "validate_controlled_user_facing_output_artifact_v1",
    "summarize_controlled_user_facing_output_artifact_v1",
    "render_controlled_user_facing_output_artifact_markdown_v1",
    "to_controlled_user_facing_output_artifact_json_safe_v1",
    "design-only",
    "result_artifact_created: false",
    "user_facing_output_executed: false",
    "reply_text_created: false",
    "final_answer_prose_created: false",
    "answer_draft_created: false",
    "runtime_wired: false",
    "chat_responder_called: false",
    "respond_chat_called: false",
    "generate_chat_called: false",
    "provider_call_made: false",
    "model_call_made: false",
    "search_call_made: false",
    "advisor_call_made: false",
    "dot_weslr_write_performed: false",
    "feature_flag_enabled: false",
    "judges_created: false",
    "scores_created: false",
    "official_claim_made: false",
    "answer_authority_granted: false",
    "user_facing_output_authority_granted: false",
    "runtime_authority_granted: false",
    "official_evaluation_authority_granted: false",
    "Allowed Source Helper Output",
    "Forbidden Source Content",
    "Validation-Before-Result-Writing Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Denied Authority Fields",
    "Blocked / Invalid Result Behavior",
    "No-User-Facing-Output-Execution Boundary",
    "No-Reply-Text Boundary",
    "No-Live-Dialogue Boundary",
    "No-Final-Answer-Prose Boundary",
    "No-Runtime Boundary",
    "No-ChatResponder / respond_chat / generate_chat Boundary",
    "No-Provider / Search / Advisor / Model Boundary",
    "No-.weslr / No-Feature-Flag Boundary",
    "No-Judges / Scores Boundary",
    "No-Official-Claims Boundary",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "Safety Confirmation",
}

_controlled_user_facing_output_result_design_review_doc = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_RESULT_DESIGN_REVIEW_V1.md"
_controlled_user_facing_output_result_design_review_required_markers = {
    "WESLR Controlled User-Facing Output Result Design Review V1",
    "controlled_user_facing_output_result_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_RESULT_V1.md",
    "design-only",
    "result-design-only",
    "metadata-only",
    "internal-only",
    "helper-output based",
    "validation-before-result-writing",
    "safe-Markdown bounded",
    "JSON-safe bounded",
    "no result artifact created",
    "no user-facing output execution",
    "no reply text",
    "no final-answer prose",
    "no final answers",
    "no answer drafts",
    "no live dialogue",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls or imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` reads/writes",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no answer/user-facing-output/composition/runtime/official evaluation authority granted",
    "weslr/chat_responder.py` untouched",
    "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_RESULT_ARTIFACT_V1.md",
    "Allowed Source Helper Output",
    "Validation-Before-Result-Writing Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Denied Authority Fields",
    "Blocked / Invalid Result Behavior",
    "No blocking design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_USER_FACING_OUTPUT_RESULT_DESIGN_V1",
}

_controlled_user_facing_output_result_artifact_doc = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_RESULT_ARTIFACT_V1.md"
_controlled_user_facing_output_result_artifact_required_markers = {
    "WESLR Controlled User-Facing Output Result Artifact V1",
    "controlled_user_facing_output_result_artifact_v1",
    "REVIEW_CONTROLLED_USER_FACING_OUTPUT_RESULT_ARTIFACT_V1",
    "build_controlled_user_facing_output_artifact_v1",
    "validate_controlled_user_facing_output_artifact_v1",
    "summarize_controlled_user_facing_output_artifact_v1",
    "render_controlled_user_facing_output_artifact_markdown_v1",
    "to_controlled_user_facing_output_artifact_json_safe_v1",
    "internal-only",
    "metadata-only",
    "helper-output based",
    "validation-backed",
    "safe Markdown",
    "JSON-safe eligible",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "controlled/synthetic metadata only",
    "user_facing_output_executed=false",
    "reply_text_created=false",
    "live_dialogue_output_created=false",
    "final_answer_generation_executed=false",
    "final_answer_generated=false",
    "final_answer_prose_created=false",
    "answer_draft_created=false",
    "answer_composition_executed=false",
    "answer_formation_executed=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judges_created=false",
    "scores_created=false",
    "official_claim_made=false",
    "answer_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "No-User-Facing-Output-Execution Boundary",
    "No-Reply-Text Boundary",
    "No-Live-Dialogue Boundary",
    "No-Final-Answer-Prose Boundary",
    "No-Runtime Boundary",
    "No-ChatResponder / respond_chat / generate_chat Boundary",
    "No-Provider / Search / Advisor / Model Boundary",
    "No-.weslr / No-Feature-Flag Boundary",
    "No-Judges / Scores Boundary",
    "No-Official-Claims Boundary",
}

_controlled_user_facing_output_result_artifact_review_doc = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_RESULT_ARTIFACT_REVIEW_V1.md"
_controlled_user_facing_output_result_artifact_review_required_markers = {
    "WESLR Controlled User-Facing Output Result Artifact Review V1",
    "controlled_user_facing_output_result_artifact_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_RESULT_ARTIFACT_V1.md",
    "exactly the approved artifact path",
    "internal-only",
    "metadata-only",
    "helper-output based",
    "validation-backed",
    "safe Markdown",
    "JSON-safe eligible",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "controlled/synthetic metadata only",
    "created using only approved helper API",
    "not user-facing output execution",
    "not reply text",
    "not final-answer prose",
    "not final-answer generation",
    "not answer draft creation",
    "not live dialogue",
    "not answer composition execution",
    "not answer formation execution",
    "not live chat behavior",
    "not runtime readiness",
    "not ChatResponder/respond_chat/generate_chat output",
    "not provider/search/advisor/model output",
    "not official benchmark/IQ/Turing/certification/product-readiness evidence",
    "not answer authority",
    "not user-facing-output authority",
    "not composition authority",
    "not runtime authority",
    "not official evaluation authority",
    "weslr/chat_responder.py` untouched",
    "No blocking artifact gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_USER_FACING_OUTPUT_RESULT_ARTIFACT_REVIEW_V1",
}

_controlled_user_facing_output_chain_next_step_review_doc = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_CHAIN_NEXT_STEP_REVIEW_V1.md"
_controlled_user_facing_output_chain_next_step_review_required_markers = {
    "WESLR Controlled User-Facing Output Chain Next Step Review V1",
    "controlled_user_facing_output_chain_reviewed_next_step_design_controlled_reply_text_boundary_v1",
    "DESIGN_CONTROLLED_REPLY_TEXT_BOUNDARY_V1",
    "metadata-only controlled user-facing output structures exist",
    "helper implementation exists for safe internal user-facing-output metadata",
    "controlled user-facing output result artifact exists",
    "result artifact is internal-only, metadata-only, helper-output based, validation-backed, safe Markdown, JSON-safe eligible, no-authority, no-runtime, and non-user-facing",
    "denied authority fields stayed false",
    "validation/release checks passed",
    "weslr/chat_responder.py` stayed untouched",
    "no runtime/provider/search/advisor/model/.weslr paths were activated",
    "actual user-facing output execution",
    "actual reply text",
    "final-answer prose",
    "final answers",
    "answer drafts",
    "answer correctness",
    "final-answer generation execution",
    "answer composition execution",
    "answer formation execution",
    "prompt/live dialogue execution",
    "live chat behavior",
    "runtime readiness",
    "ChatResponder/respond_chat/generate_chat activation",
    "provider/search/advisor/model integration",
    "official Turing-test claim",
    "IQ claim",
    "certification claim",
    "product readiness",
    "authority to answer users",
    "authority to wire runtime",
    "reply-text authority",
    "user-facing-output authority",
    "runtime authority",
    "official evaluation authority",
    "metadata-as-output-authority risk",
    "helper-implementation-as-runtime-authority risk",
    "result-artifact-as-execution risk",
    "safe-Markdown-as-user-output risk",
    "JSON-safe-as-reply-payload risk",
    "validation-pass-as-answer-runtime-product-authority risk",
    "No blocking chain gaps were found",
    "Allowed future lane from this report is exactly one",
}


_controlled_reply_preview_helpers_doc = "docs/WESLR_CONTROLLED_REPLY_PREVIEW_HELPERS_V1.md"
_controlled_reply_preview_helpers_required_markers = {
    "WESLR Controlled Reply Preview Helpers V1",
    "DESIGN_CONTROLLED_REPLY_PREVIEW_HELPERS_V1",
    "REVIEW_CONTROLLED_REPLY_PREVIEW_HELPERS_V1",
    "weslr/controlled_reply_preview.py",
    "weslr/tests/test_controlled_reply_preview_v1.py",
    "build_controlled_reply_preview_artifact_v1",
    "validate_controlled_reply_preview_artifact_v1",
    "summarize_controlled_reply_preview_artifact_v1",
    "render_controlled_reply_preview_artifact_markdown_v1",
    "to_controlled_reply_preview_artifact_json_safe_v1",
    "controlled_reply_preview_artifact_v1",
    "controlled_reply_preview_artifact_schema_v1",
    "Allowed Reply-Preview Metadata Inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "Validation-Before-Preview Policy",
    "Validation-Before-Rendering Policy",
    "No-Sendable-Reply-Text Policy",
    "No-Actual-Reply-Body Policy",
    "No-Reply-Execution Policy",
    "No-User-Facing-Output-Execution Policy",
    "No-Live-Dialogue Policy",
    "No-Runtime Policy",
    "No-ChatResponder / respond_chat / generate_chat Policy",
    "No-Provider / Search / Advisor / Model Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Blocked Artifact Behavior",
    "Denied Authority Fields",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "sendable_reply_text_created=false",
    "actual_reply_body_created=false",
    "reply_preview_executed=false",
    "reply_text_executed=false",
    "user_facing_output_executed=false",
    "live_dialogue_output_created=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_read_performed=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judges_created=false",
    "scores_created=false",
    "official_claim_made=false",
    "answer_authority_granted=false",
    "preview_authority_granted=false",
    "reply_text_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
}


_controlled_reply_preview_helpers_review_doc = "docs/WESLR_CONTROLLED_REPLY_PREVIEW_HELPERS_REVIEW_V1.md"
_controlled_reply_preview_helpers_review_required_markers = {
    "WESLR Controlled Reply Preview Helpers Review V1",
    "controlled_reply_preview_helpers_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_HELPERS_V1.md",
    "design-only",
    "helper-design-only",
    "metadata-only",
    "internal-only",
    "no controlled reply preview helper implementation",
    "no reply preview execution",
    "no reply text execution",
    "no user-facing output execution",
    "no sendable reply text",
    "no actual reply body",
    "no final-answer prose",
    "no answer drafts",
    "no live dialogue",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` reads/writes",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no answer/preview/reply-text/user-facing-output/composition/runtime/official evaluation authority granted",
    "no reply-preview result artifact created",
    "No blocking design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_REPLY_PREVIEW_HELPERS_V1",
}


_controlled_reply_preview_helpers_implementation_review_doc = "docs/WESLR_CONTROLLED_REPLY_PREVIEW_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_controlled_reply_preview_helpers_implementation_review_required_markers = {
    "WESLR Controlled Reply Preview Helpers Implementation Review V1",
    "controlled_reply_preview_helpers_implementation_valid_ready_for_context_alignment",
    "weslr/controlled_reply_preview.py",
    "weslr/tests/test_controlled_reply_preview_v1.py",
    "build_controlled_reply_preview_artifact_v1",
    "validate_controlled_reply_preview_artifact_v1",
    "summarize_controlled_reply_preview_artifact_v1",
    "render_controlled_reply_preview_artifact_markdown_v1",
    "to_controlled_reply_preview_artifact_json_safe_v1",
    "helper-only",
    "metadata-only",
    "internal-only",
    "deterministic",
    "pure in-memory",
    "validation-before-rendering",
    "JSON-safe",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "no side effects",
    "no preview execution",
    "no preview output",
    "no sendable reply text",
    "no actual reply body",
    "no reply text execution",
    "no final-answer prose",
    "no answer drafts",
    "no prompt/live dialogue execution",
    "no user-facing output execution",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat imports or calls",
    "no provider/search/advisor/model calls",
    "no `.weslr` reads/writes",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no authority grants",
    "No blocking implementation gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_REPLY_PREVIEW_HELPERS_IMPLEMENTATION_V1",
}


_controlled_reply_preview_result_design_doc = "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_V1.md"
_controlled_reply_preview_result_design_review_doc = "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_DESIGN_REVIEW_V1.md"
_controlled_reply_preview_result_artifact_doc = "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_ARTIFACT_V1.md"
_controlled_reply_preview_result_artifact_review_doc = "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_ARTIFACT_REVIEW_V1.md"
_controlled_reply_preview_chain_next_step_review_doc = "docs/WESLR_CONTROLLED_REPLY_PREVIEW_CHAIN_NEXT_STEP_REVIEW_V1.md"
_controlled_reply_output_precondition_boundary_doc = "docs/WESLR_CONTROLLED_REPLY_OUTPUT_PRECONDITION_BOUNDARY_V1.md"
_controlled_reply_output_precondition_boundary_review_doc = "docs/WESLR_CONTROLLED_REPLY_OUTPUT_PRECONDITION_BOUNDARY_REVIEW_V1.md"
_controlled_reply_output_precondition_chain_next_step_review_doc = "docs/WESLR_CONTROLLED_REPLY_OUTPUT_PRECONDITION_CHAIN_NEXT_STEP_REVIEW_V1.md"
_unknown_engine_boundary_doc = "docs/WESLR_UNKNOWN_ENGINE_BOUNDARY_V1.md"
_unknown_engine_boundary_review_doc = "docs/WESLR_UNKNOWN_ENGINE_BOUNDARY_REVIEW_V1.md"
_cognitive_gym_suite_boundary_doc = "docs/WESLR_COGNITIVE_GYM_SUITE_BOUNDARY_V1.md"
_cognitive_gym_suite_boundary_review_doc = "docs/WESLR_COGNITIVE_GYM_SUITE_BOUNDARY_REVIEW_V1.md"
_cognitive_gym_run_protocol_doc = "docs/WESLR_COGNITIVE_GYM_RUN_PROTOCOL_V1.md"
_cognitive_gym_run_protocol_review_doc = "docs/WESLR_COGNITIVE_GYM_RUN_PROTOCOL_REVIEW_V1.md"
_cognitive_gym_run_protocol_helpers_implementation_review_doc = "docs/WESLR_COGNITIVE_GYM_RUN_PROTOCOL_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_unknown_engine_helpers_doc = "docs/WESLR_UNKNOWN_ENGINE_HELPERS_V1.md"
_unknown_engine_helpers_review_doc = "docs/WESLR_UNKNOWN_ENGINE_HELPERS_REVIEW_V1.md"
_unknown_engine_helpers_implementation_review_doc = "docs/WESLR_UNKNOWN_ENGINE_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_unknown_engine_helpers_validation_fix_review_doc = "docs/WESLR_UNKNOWN_ENGINE_HELPERS_VALIDATION_FIX_REVIEW_V1.md"
_unknown_engine_result_artifact_boundary_doc = "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_BOUNDARY_V1.md"
_unknown_engine_result_artifact_boundary_review_doc = "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_BOUNDARY_REVIEW_V1.md"
_unknown_engine_result_artifact_helpers_doc = "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_HELPERS_V1.md"
_unknown_engine_result_artifact_helpers_review_doc = "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_HELPERS_REVIEW_V1.md"
_unknown_engine_result_artifact_helpers_implementation_review_doc = "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_unknown_engine_result_artifact_doc = "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_V1.md"
_unknown_engine_result_artifact_review_doc = "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_REVIEW_V1.md"
_cognitive_gym_erdos_challenge_track_doc = "docs/WESLR_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_V1.md"
_cognitive_gym_erdos_challenge_track_review_doc = "docs/WESLR_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_REVIEW_V1.md"
_cognitive_gym_erdos_challenge_track_helpers_implementation_review_doc = "docs/WESLR_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_cognitive_gym_erdos_case_corpus_boundary_doc = "docs/WESLR_COGNITIVE_GYM_ERDOS_CASE_CORPUS_BOUNDARY_V1.md"
_cognitive_gym_erdos_case_corpus_boundary_review_doc = "docs/WESLR_COGNITIVE_GYM_ERDOS_CASE_CORPUS_BOUNDARY_REVIEW_V1.md"
_cognitive_gym_exploratory_case_protocol_review_doc = "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_REVIEW_V1.md"
_cognitive_gym_exploratory_case_helpers_doc = "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1.md"
_cognitive_gym_exploratory_case_helpers_review_doc = "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_REVIEW_V1.md"
_cognitive_gym_exploratory_case_helpers_implementation_review_doc = "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_first_engine_specific_exploratory_helper_boundary_doc = "docs/WESLR_FIRST_ENGINE_SPECIFIC_EXPLORATORY_HELPER_BOUNDARY_V1.md"
_first_engine_specific_exploratory_helper_boundary_review_doc = "docs/WESLR_FIRST_ENGINE_SPECIFIC_EXPLORATORY_HELPER_BOUNDARY_REVIEW_V1.md"
_calibration_ledger_exploratory_helpers_doc = "docs/WESLR_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_V1.md"
_calibration_ledger_exploratory_helpers_review_doc = "docs/WESLR_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_REVIEW_V1.md"
_cognitive_gym_erdos_challenge_track_required_markers = {
    "DESIGN_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_V1",
    "challenge-track-design-only",
    "ERDŐS / open mathematical structure",
    "Frontier-math discipline first",
    "Track Purpose",
    "Non-Goals",
    "Relationship To CognitiveGymRun",
    "Relationship To UNKNOWN ENGINE",
    "Relationship To Frontier / Open-Problem Boundary",
    "Allowed Challenge Categories",
    "Forbidden Challenge Categories And Content",
    "Tier 0 — prerequisite reconstruction",
    "Tier 1 — solved Erdős-style problems",
    "Tier 2 — bounded / toy variants",
    "Tier 3 — partially solved / known frontier variants",
    "Tier 4 — open-problem boundary mapping",
    "Tier 5 — counterexample and falsification planning",
    "Tier 6 — subproblem generation",
    "Tier 7 — proof-audit discipline",
    "Input Schema Design",
    "Expected Metadata Output Shape",
    "Validation Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Denied Authority Fields",
    "Blocked Behavior",
    "Visible Risks",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "cognitive_gym_authority_granted=false",
    "cognitive_gym_run_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "challenge_solution_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "preview_authority_granted=false",
    "reply_output_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "turing_test_authority_granted=false",
    "cognitive_gym_executed=false",
    "cognitive_gym_run_executed=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "future_certainty_claim_created=false",
    "challenge_solution_claim_created=false",
    "final_answer_generated=false",
    "final_answer_prose_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_read_performed=false",
    "dot_weslr_write_performed=false",
    "judges_created=false",
    "scores_created=false",
    "official_claim_made=false",
    "REVIEW_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_V1",
}
_cognitive_gym_erdos_challenge_track_review_required_markers = {
    "WESLR Cognitive Gym Erdős Challenge Track Review V1",
    "cognitive_gym_erdos_challenge_track_design_valid_ready_for_context_alignment",
    "docs/WESLR_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_V1.md",
    "design-only",
    "challenge-track-design-only",
    "internal-only",
    "metadata-only",
    "no implementation",
    "no corpus",
    "no runner",
    "no scoring",
    "no judges",
    "no execution",
    "no result artifact",
    "no official benchmark",
    "no Turing/IQ/certification/product-readiness claim",
    "no proof claim",
    "no open-problem solution claim",
    "no authority",
    "Required Design Coverage",
    "CognitiveGymRun Relationship Confirmation",
    "UNKNOWN ENGINE Relationship Confirmation",
    "Tier 0 — prerequisite reconstruction",
    "Tier 1 — solved Erdős-style problems",
    "Tier 2 — bounded / toy variants",
    "Tier 3 — partially solved / known frontier variants",
    "Tier 4 — open-problem boundary mapping",
    "Tier 5 — counterexample and falsification planning",
    "Tier 6 — subproblem generation",
    "Tier 7 — proof-audit discipline",
    "cognitive_gym_authority_granted=false",
    "cognitive_gym_run_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "challenge_solution_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "reply_output_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "cognitive_gym_executed=false",
    "cognitive_gym_run_executed=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "future_certainty_claim_created=false",
    "challenge_solution_claim_created=false",
    "final_answer_generated=false",
    "final_answer_prose_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_read_performed=false",
    "dot_weslr_write_performed=false",
    "judges_created=false",
    "scores_created=false",
    "official_claim_made=false",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_V1",
}
_cognitive_gym_erdos_challenge_track_helpers_implementation_review_required_markers = {
    "WESLR Cognitive Gym Erdős Challenge Track Helpers Implementation Review V1",
    "cognitive_gym_erdos_challenge_track_helpers_implementation_valid_ready_for_context_alignment",
    "weslr/cognitive_gym_erdos_challenge_track.py",
    "weslr/tests/test_cognitive_gym_erdos_challenge_track_v1.py",
    "helper-only",
    "metadata-only",
    "internal-only",
    "deterministic",
    "import-safe",
    "side-effect-free",
    "pure in-memory",
    "JSON-safe",
    "safe-Markdown bounded",
    "validation-before-rendering",
    "no corpus",
    "no runner",
    "no scoring",
    "no judges",
    "no execution",
    "no runtime",
    "no result artifact",
    "no proof claim",
    "no open-problem solution claim",
    "no official benchmark",
    "no Turing/IQ/certification/product-readiness claim",
    "no authority",
    "build_erdos_challenge_track_case_v1",
    "validate_erdos_challenge_track_case_v1",
    "summarize_erdos_challenge_track_case_v1",
    "render_erdos_challenge_track_case_markdown_v1",
    "to_erdos_challenge_track_case_json_safe_v1",
    "Tier 0 — prerequisite reconstruction",
    "Tier 1 — solved Erdős-style problems",
    "Tier 2 — bounded / toy variants",
    "Tier 3 — partially solved / known frontier variants",
    "Tier 4 — open-problem boundary mapping",
    "Tier 5 — counterexample and falsification planning",
    "Tier 6 — subproblem generation",
    "Tier 7 — proof-audit discipline",
    "cognitive_gym_authority_granted=false",
    "cognitive_gym_run_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "challenge_solution_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "reply_output_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "turing_test_authority_granted=false",
    "cognitive_gym_executed=false",
    "cognitive_gym_run_executed=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "future_certainty_claim_created=false",
    "challenge_solution_claim_created=false",
    "final_answer_generated=false",
    "final_answer_prose_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_read_performed=false",
    "dot_weslr_write_performed=false",
    "judges_created=false",
    "scores_created=false",
    "official_claim_made=false",
    "No blocking implementation gaps found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_ERDOS_CHALLENGE_TRACK_HELPERS_IMPLEMENTATION_V1",
}
_cognitive_gym_erdos_case_corpus_boundary_required_markers = {
    "WESLR Cognitive Gym Erdős Case Corpus Boundary V1",
    "DESIGN_COGNITIVE_GYM_ERDOS_CASE_CORPUS_BOUNDARY_V1",
    "design-only",
    "boundary-only",
    "no corpus file created",
    "no corpus implementation",
    "no runner",
    "no scoring",
    "no judges",
    "no challenge execution",
    "no result artifacts",
    "no final answers",
    "no proof claims",
    "no official claims",
    "no authority grants",
    "Corpus Purpose",
    "Non-Goals",
    "Relationship To Erdős Challenge Track Helpers",
    "Relationship To CognitiveGymRun",
    "Relationship To UNKNOWN ENGINE",
    "Allowed Case Types",
    "Forbidden Case Types And Content",
    "Safe Case Metadata Schema",
    "Tier 0–7 Corpus Coverage Policy",
    "Protected / Hidden / Answer-Key Boundary",
    "Copyright / Private-Data Boundary",
    "Proof / Open-Problem Claim Boundary",
    "Validation Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Denied Authority Fields",
    "Blocked Behavior",
    "Visible Risks",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "Tier 0 — prerequisite reconstruction",
    "Tier 1 — solved Erdős-style problems",
    "Tier 2 — bounded / toy variants",
    "Tier 3 — partially solved / known frontier variants",
    "Tier 4 — open-problem boundary mapping",
    "Tier 5 — counterexample and falsification planning",
    "Tier 6 — subproblem generation",
    "Tier 7 — proof-audit discipline",
    "cognitive_gym_authority_granted=false",
    "cognitive_gym_run_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "challenge_solution_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "reply_output_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "cognitive_gym_executed=false",
    "cognitive_gym_run_executed=false",
    "unknown_engine_executed=false",
    "final_answer_generated=false",
    "final_answer_prose_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_read_performed=false",
    "dot_weslr_write_performed=false",
    "judges_created=false",
    "scores_created=false",
    "official_claim_made=false",
    "Corpus boundary is not corpus implementation.",
    "Corpus metadata is not challenge execution.",
    "Case inclusion is not proof of solving ability.",
    "Open-problem mapping is not solution evidence.",
    "Proof-audit cases are not proof validation.",
    "Validation pass is not scoring.",
    "Corpus is not official benchmark evidence.",
    "OCC/OpenClaw is not deployed WESLR.",
    "REVIEW_COGNITIVE_GYM_ERDOS_CASE_CORPUS_BOUNDARY_V1",
}
_cognitive_gym_erdos_case_corpus_boundary_review_required_markers = {
    "WESLR Cognitive Gym Erdős Case Corpus Boundary Review V1",
    "cognitive_gym_erdos_case_corpus_boundary_design_valid_ready_for_context_alignment",
    "docs/WESLR_COGNITIVE_GYM_ERDOS_CASE_CORPUS_BOUNDARY_V1.md",
    "design-only",
    "boundary-only",
    "internal-only",
    "metadata-only",
    "no corpus file",
    "no corpus implementation",
    "no runner",
    "no scoring",
    "no judges",
    "no challenge execution",
    "no result artifacts",
    "no final answers",
    "no proof claims",
    "no open-problem solution claims",
    "no official claims",
    "no authority",
    "Required Design Coverage Confirmed",
    "Allowed Case Types Confirmed",
    "Forbidden Content Confirmed",
    "Safe Case Metadata Shape Confirmed",
    "Validation Policy Confirmed",
    "Denied Authority Confirmed",
    "Visible Risks Confirmed",
    "Corpus boundary is not corpus implementation.",
    "Corpus metadata is not challenge execution.",
    "Case inclusion is not proof of solving ability.",
    "Open-problem mapping is not solution evidence.",
    "Proof-audit cases are not proof validation.",
    "Validation pass is not scoring.",
    "Corpus is not official benchmark evidence.",
    "OCC/OpenClaw is not deployed WESLR.",
    "cognitive_gym_authority_granted=false",
    "cognitive_gym_run_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "challenge_solution_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "reply_output_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "cognitive_gym_executed=false",
    "cognitive_gym_run_executed=false",
    "unknown_engine_executed=false",
    "final_answer_generated=false",
    "final_answer_prose_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_read_performed=false",
    "dot_weslr_write_performed=false",
    "judges_created=false",
    "scores_created=false",
    "official_claim_made=false",
    "No blocking design gaps found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_ERDOS_CASE_CORPUS_BOUNDARY_V1",
}

_cognitive_gym_exploratory_case_protocol_review_required_markers = {
    "WESLR Cognitive Gym Exploratory Case Protocol Review V1",
    "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_V1.md",
    "docs/WESLR_EXPLORATORY_PROBLEM_WORK_BOUNDARY_V1.md",
    "docs/WESLR_EXPLORATORY_PROBLEM_WORK_BOUNDARY_REVIEW_V1.md",
    "cognitive_gym_exploratory_case_protocol_design_valid_ready_for_context_alignment",
    "review-only",
    "no runtime wiring",
    "no chat/user-facing behavior changes",
    "governed exploratory problem work",
    "isolated chaotic modules",
    "UNKNOWN_ENGINE",
    "CALIBRATION_LEDGER",
    "CONTRADICTION_FURNACE",
    "GOVERNANCE_BOUNDARY_ENGINE",
    "COUNTERFACTUAL_ENGINE",
    "BLINDSPOT_ENGINE",
    "INVARIANT_MINER",
    "INTENT_RECONSTRUCTION_ENGINE",
    "CAUSAL_TRACE_ENGINE",
    "FAILURE_MODE_SIMULATOR",
    "MEMORY_TRUST_ENGINE",
    "ABSTRACTION_LADDER",
    "SIGNAL_VS_NOISE_ENGINE",
    "case_defined",
    "intake_validated",
    "exploratory_not_started",
    "exploratory_candidate",
    "partial_structure_found",
    "failed_attempt_recorded",
    "invalidated",
    "correction_recorded",
    "needs_external_review",
    "externally_validated",
    "claim_forbidden_without_validation",
    "blocked_by_boundary",
    "protocol_version",
    "case_id",
    "problem_statement_metadata",
    "predictions_or_branch_labels",
    "denied_authority_fields",
    "validation_status",
    "next_allowed_steps",
    "CognitiveGymRun-style reporting philosophy",
    "claim ladder is non-skippable",
    "Public claims require external validation and separate authorization.",
    "Validation pass is not scoring, proof, product readiness, official evaluation, runtime authorization, or chat authority.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_V1",
}

_cognitive_gym_exploratory_case_helpers_required_markers = {
    "WESLR Cognitive Gym Exploratory Case Helpers V1",
    "DESIGN_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1",
    "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_V1.md",
    "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_REVIEW_V1.md",
    "Purpose",
    "Non-Goals",
    "Relationship To Reviewed Protocol",
    "Future Target Path",
    "weslr/cognitive_gym_exploratory_case.py",
    "weslr/tests/test_cognitive_gym_exploratory_case_v1.py",
    "Future Public APIs",
    "build_cognitive_gym_exploratory_case_v1",
    "validate_cognitive_gym_exploratory_case_v1",
    "summarize_cognitive_gym_exploratory_case_v1",
    "render_cognitive_gym_exploratory_case_markdown_v1",
    "to_cognitive_gym_exploratory_case_json_safe_v1",
    "Shared Case Shape",
    "Lifecycle Labels",
    "Input Boundary Rules",
    "Output Boundary Rules",
    "Denied Authority Fields",
    "Validation Rules",
    "Blocked Metadata Behavior",
    "Safe Markdown Rules",
    "JSON-Safe Rules",
    "Claim Ladder Preservation",
    "External Validation Requirement",
    "Import-Safety And Side-Effect Expectations",
    "Future Implementation / Review Sequence",
    "Abort Conditions",
    "metadata-only",
    "validation-before-rendering",
    "blocked metadata",
    "runtime_authority: false",
    "chat_authority: false",
    "provider_call_authority: false",
    "persistence_authority: false",
    "scoring_authority: false",
    "judge_authority: false",
    "public_release_authority: false",
    "REVIEW_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1",
    "IMPLEMENT_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1",
    "No helpers are implemented in this lane.",
}
_cognitive_gym_exploratory_case_helpers_review_required_markers = {
    "WESLR Cognitive Gym Exploratory Case Helpers Review V1",
    "cognitive_gym_exploratory_case_helpers_design_valid_ready_for_context_alignment",
    "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1.md",
    "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_V1.md",
    "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_REVIEW_V1.md",
    "review-only",
    "no helper implementation",
    "no runtime wiring",
    "no chat/user-facing behavior changes",
    "no `.weslr` reads/writes",
    "no provider/model/search/advisor calls",
    "Purpose",
    "Non-goals",
    "Relationship to reviewed exploratory case protocol",
    "Future helper module path only",
    "build_cognitive_gym_exploratory_case_v1",
    "validate_cognitive_gym_exploratory_case_v1",
    "summarize_cognitive_gym_exploratory_case_v1",
    "render_cognitive_gym_exploratory_case_markdown_v1",
    "to_cognitive_gym_exploratory_case_json_safe_v1",
    "Metadata-only case shape",
    "Lifecycle labels",
    "Input/output boundaries",
    "Denied authority fields required false",
    "Validation rules for unsafe content and unsupported claims",
    "Blocked metadata behavior",
    "Safe Markdown behavior",
    "JSON-safe behavior",
    "Claim ladder and external validation",
    "Import-safe, deterministic, side-effect-free, in-memory expectations",
    "Future implementation/review sequence",
    "Abort conditions",
    "Explicit no-helper-implementation posture",
    "Blockers: none.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1",
}
_cognitive_gym_exploratory_case_helpers_implementation_review_required_markers = {
    "WESLR Cognitive Gym Exploratory Case Helpers Implementation Review V1",
    "cognitive_gym_exploratory_case_helpers_implementation_valid_ready_for_context_alignment",
    "weslr/cognitive_gym_exploratory_case.py",
    "weslr/tests/test_cognitive_gym_exploratory_case_v1.py",
    "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_V1.md",
    "docs/WESLR_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_REVIEW_V1.md",
    "review-only",
    "implementation files not edited",
    "build_cognitive_gym_exploratory_case_v1",
    "validate_cognitive_gym_exploratory_case_v1",
    "summarize_cognitive_gym_exploratory_case_v1",
    "render_cognitive_gym_exploratory_case_markdown_v1",
    "to_cognitive_gym_exploratory_case_json_safe_v1",
    "helper-only",
    "metadata-only",
    "deterministic",
    "import-safe",
    "side-effect-free",
    "pure in-memory",
    "validation-before-rendering",
    "JSON-safe",
    "blocked-metadata preserving",
    "no `.weslr` reads/writes",
    "no provider/model/search/advisor calls",
    "no runtime wiring",
    "no scoring/judging",
    "no challenge execution",
    "no final-answer/proof/open-problem/scientific/official claims",
    "no authority grants",
    "Validation behavior",
    "Safe Markdown",
    "JSON-safe conversion",
    "Test coverage",
    "Blockers: none.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_IMPLEMENTATION_V1",
}
_first_engine_specific_exploratory_helper_boundary_required_markers = {
    "WESLR First Engine-Specific Exploratory Helper Boundary V1",
    "DESIGN_FIRST_ENGINE_SPECIFIC_EXPLORATORY_HELPER_BOUNDARY_V1",
    "design-only",
    "Selected / recommended first engine-specific target: `CALIBRATION_LEDGER`",
    "Candidate Engine Families Considered",
    "UNKNOWN_ENGINE",
    "CONTRADICTION_FURNACE",
    "COUNTERFACTUAL_ENGINE",
    "BLINDSPOT_ENGINE",
    "CALIBRATION_LEDGER",
    "INVARIANT_MINER",
    "INTENT_RECONSTRUCTION_ENGINE",
    "GOVERNANCE_BOUNDARY_ENGINE",
    "CAUSAL_TRACE_ENGINE",
    "FAILURE_MODE_SIMULATOR",
    "MEMORY_TRUST_ENGINE",
    "ABSTRACTION_LADDER",
    "SIGNAL_VS_NOISE_ENGINE",
    "Erdős/open-structure work",
    "Safest First Recommendation",
    "One Engine-Specific Helper Family Only",
    "Required Inheritance From Shared Helper APIs And Metadata Shape",
    "build_cognitive_gym_exploratory_case_v1",
    "validate_cognitive_gym_exploratory_case_v1",
    "summarize_cognitive_gym_exploratory_case_v1",
    "render_cognitive_gym_exploratory_case_markdown_v1",
    "to_cognitive_gym_exploratory_case_json_safe_v1",
    "Allowed Future Behavior",
    "Forbidden Future Behavior",
    "Denied Authority Fields Remain False",
    "Validation-Before-Rendering And Blocked Metadata",
    "No public, final, or official claim promotion is allowed without external validation and separate authorization.",
    "REVIEW_FIRST_ENGINE_SPECIFIC_EXPLORATORY_HELPER_BOUNDARY_V1",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_FIRST_ENGINE_SPECIFIC_EXPLORATORY_HELPER_BOUNDARY_V1",
    "DESIGN_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_V1",
    "REVIEW_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_V1",
    "IMPLEMENT_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_V1",
    "Abort Conditions",
    "No engine-specific helpers are implemented in this lane.",
    "engine_specific_helpers_implemented=false",
    "runtime_wired=false",
    "chat_wired=false",
    "challenge_executed=false",
    "scoring_created=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_read_performed=false",
    "dot_weslr_write_performed=false",
    "final_answer_generated=false",
    "proof_claim_created=false",
    "open_problem_solution_claim_created=false",
    "scientific_discovery_claim_created=false",
    "official_claim_made=false",
    "authority_granted=false",
    "denied_authority_fields_remain_false=true",
    "validation_before_rendering_preserved=true",
    "blocked_metadata_behavior_preserved=true",
    "external_validation_required_before_public_final_official_claim=true",
}
_first_engine_specific_exploratory_helper_boundary_review_required_markers = {
    "WESLR First Engine-Specific Exploratory Helper Boundary Review V1",
    "first_engine_specific_exploratory_helper_boundary_valid_ready_for_context_alignment",
    "docs/WESLR_FIRST_ENGINE_SPECIFIC_EXPLORATORY_HELPER_BOUNDARY_V1.md",
    "review-only",
    "boundary-only",
    "design-only",
    "CALIBRATION_LEDGER is suitable as the safest first engine-specific exploratory helper target.",
    "Candidate families considered",
    "One engine-specific family only",
    "Shared helper inheritance",
    "Allowed future behavior bounded",
    "Forbidden behavior complete",
    "Denied authority fields",
    "Validation-before-rendering",
    "Blocked metadata behavior",
    "Public/final/official claim promotion",
    "No engine-specific helper implementation",
    "no runtime wiring",
    "no chat/user-facing behavior changes",
    "no `.weslr` reads/writes",
    "no provider/model/search/advisor calls",
    "no challenge execution",
    "no scoring/judging",
    "no final-answer/proof/open-problem/scientific/official claims",
    "no authority grants",
    "Blockers: none.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_FIRST_ENGINE_SPECIFIC_EXPLORATORY_HELPER_BOUNDARY_V1",
}
_calibration_ledger_exploratory_helpers_required_markers = {
    "WESLR CALIBRATION_LEDGER Exploratory Helpers V1",
    "DESIGN_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_V1",
    "design-only",
    "Helper family: `CALIBRATION_LEDGER` only",
    "Relationship To Shared Cognitive Gym Exploratory Case Helpers",
    "Why CALIBRATION_LEDGER Is The First Engine-Specific Target",
    "Future target path only: `weslr/calibration_ledger_exploratory_helpers.py`",
    "Future test path only: `weslr/tests/test_calibration_ledger_exploratory_helpers_v1.py`",
    "Proposed Future APIs Only",
    "build_calibration_ledger_exploratory_case_v1",
    "validate_calibration_ledger_exploratory_case_v1",
    "summarize_calibration_ledger_exploratory_case_v1",
    "render_calibration_ledger_exploratory_case_markdown_v1",
    "to_calibration_ledger_exploratory_case_json_safe_v1",
    "calibration_case_id",
    "predicted_branch_label",
    "confidence_label",
    "uncertainty_label",
    "observed_outcome_label",
    "mismatch_label",
    "correction_label",
    "lesson_label",
    "calibration_status",
    "Mapping To Shared Exploratory Case Fields",
    "Allowed Future Behavior",
    "Forbidden Behavior",
    "Validation Rules",
    "Safe Markdown Rules",
    "JSON-Safe Rules",
    "Blocked Metadata Behavior",
    "Denied Authority Fields Remain False",
    "Claim Ladder And External Validation Requirement",
    "REVIEW_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_V1",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_V1",
    "IMPLEMENT_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_V1",
    "REVIEW_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_IMPLEMENTATION_V1",
    "Abort Conditions",
    "No CALIBRATION_LEDGER helpers are implemented in this lane.",
    "calibration_ledger_helpers_implemented=false",
    "shared_cognitive_gym_exploratory_case_helpers_inherited=true",
    "shared_helper_files_edited=false",
    "runtime_wired=false",
    "chat_wired=false",
    "challenge_executed=false",
    "scoring_created=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_read_performed=false",
    "dot_weslr_write_performed=false",
    "final_answer_generated=false",
    "proof_claim_created=false",
    "open_problem_solution_claim_created=false",
    "scientific_discovery_claim_created=false",
    "official_claim_made=false",
    "authority_granted=false",
    "denied_authority_fields_remain_false=true",
    "validation_before_rendering_preserved=true",
    "blocked_metadata_behavior_preserved=true",
    "claim_ladder_preserved=true",
    "external_validation_required_before_public_final_official_claim=true",
}
_calibration_ledger_exploratory_helpers_review_required_markers = {
    "WESLR CALIBRATION_LEDGER Exploratory Helpers Review V1",
    "docs/WESLR_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_V1.md",
    "docs/WESLR_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_REVIEW_V1.md",
    "review-only",
    "CALIBRATION_LEDGER",
    "design-only",
    "one-family-only",
    "Shared Cognitive Gym helper inheritance",
    "Future paths/APIs are targets only",
    "Calibration metadata bounded and metadata-only",
    "Mapping to shared exploratory case fields",
    "Allowed behavior bounded",
    "Forbidden behavior complete",
    "False denied authority fields preserved",
    "Validation-before-rendering preserved",
    "Safe Markdown preserved",
    "JSON-safe conversion preserved",
    "Blocked metadata behavior preserved",
    "Claim ladder and external validation preserved",
    "Future sequence safe",
    "No CALIBRATION_LEDGER helper implementation",
    "calibration_ledger_exploratory_helpers_design_valid_ready_for_context_alignment",
    "Blockers: none.",
    "no runtime wiring",
    "no chat/user-facing behavior changes",
    "no `.weslr` reads/writes",
    "no provider/model/search/advisor calls",
    "no challenge execution",
    "no scoring/judging",
    "no final-answer/proof/open-problem/scientific/official claims",
    "no authority grants",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_V1",
}
_controlled_reply_preview_result_design_required_markers = {
    "WESLR Controlled Reply Preview Result V1",
    "DESIGN_CONTROLLED_REPLY_PREVIEW_RESULT_V1",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_ARTIFACT_V1.md",
    "Allowed Source Helper Output",
    "Validation-Before-Result-Writing Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Denied Authority Fields",
    "Blocked / Invalid Result Behavior",
    "No-Preview-Execution Boundary",
    "No-Preview-Output Boundary",
    "No-Sendable-Reply-Text Boundary",
    "No-Actual-Reply-Body Boundary",
    "No-Reply-Text-Execution Boundary",
    "No-Final-Answer-Prose Boundary",
    "No-Answer-Draft Boundary",
    "No-User-Facing-Output-Execution Boundary",
    "No-Live-Dialogue Boundary",
    "No-Runtime Boundary",
    "No-ChatResponder / respond_chat / generate_chat Boundary",
    "No-Provider / Search / Advisor / Model Boundary",
    "No `.weslr` / Feature Flag Boundary",
    "No-Judges / Scores Boundary",
    "No-Official-Claims Boundary",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "answer_authority_granted=false",
    "preview_authority_granted=false",
    "reply_preview_executed=false",
    "preview_output_created=false",
    "sendable_reply_text_created=false",
    "actual_reply_body_created=false",
    "reply_text_executed=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "REVIEW_CONTROLLED_REPLY_PREVIEW_RESULT_DESIGN_V1",
}

_controlled_reply_preview_result_design_review_required_markers = {
    "WESLR Controlled Reply Preview Result Design Review V1",
    "controlled_reply_preview_result_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_V1.md",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_ARTIFACT_V1.md",
    "design-only",
    "result-design-only",
    "metadata-only",
    "internal-only",
    "helper-output based",
    "validation-before-result-writing",
    "safe-Markdown bounded",
    "JSON-safe bounded",
    "no result artifact created",
    "no preview execution",
    "no preview output",
    "no sendable reply text",
    "no actual reply body",
    "no reply text execution",
    "no final-answer prose",
    "no final answers",
    "no answer drafts",
    "no prompt/live dialogue execution",
    "no user-facing output execution",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` IO",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no answer/preview/reply-text/user-facing-output/composition/runtime/official evaluation authority granted",
    "No blocking design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_REPLY_PREVIEW_RESULT_DESIGN_V1",
}

_controlled_reply_preview_result_artifact_required_markers = {
    "WESLR Controlled Reply Preview Result Artifact V1",
    "controlled_reply_preview_result_artifact_v1",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_V1.md",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_DESIGN_REVIEW_V1.md",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_HELPERS_IMPLEMENTATION_REVIEW_V1.md",
    "weslr/controlled_reply_preview.py",
    "weslr/tests/test_controlled_reply_preview_v1.py",
    "controlled_reply_preview_result_design_valid_ready_for_context_alignment",
    "internal-only",
    "metadata-only",
    "helper-output based",
    "validation-backed",
    "no-authority",
    "non-user-facing",
    "no preview execution",
    "no preview output",
    "no sendable reply text",
    "no actual reply body",
    "no reply text execution",
    "no final-answer prose",
    "no final answers",
    "no answer drafts",
    "no live dialogue",
    "no user-facing output execution",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls or imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` IO",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no authority grants",
    "answer_authority_granted=false",
    "preview_authority_granted=false",
    "reply_text_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "reply_preview_executed=false",
    "preview_output_created=false",
    "sendable_reply_text_created=false",
    "actual_reply_body_created=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "REVIEW_CONTROLLED_REPLY_PREVIEW_RESULT_ARTIFACT_V1",
}

_controlled_reply_preview_result_artifact_review_required_markers = {
    "WESLR Controlled Reply Preview Result Artifact Review V1",
    "controlled_reply_preview_result_artifact_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_ARTIFACT_V1.md",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_V1.md",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_RESULT_DESIGN_REVIEW_V1.md",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_HELPERS_IMPLEMENTATION_REVIEW_V1.md",
    "weslr/controlled_reply_preview.py",
    "weslr/tests/test_controlled_reply_preview_v1.py",
    "internal-only",
    "metadata-only",
    "helper-output based",
    "validation-backed",
    "safe Markdown eligible only from validated metadata",
    "JSON-safe eligible",
    "no-authority",
    "non-user-facing",
    "no preview execution",
    "no preview output",
    "no sendable reply text",
    "no actual reply body",
    "no reply text execution",
    "no final-answer prose",
    "no final answers",
    "no answer drafts",
    "no live dialogue",
    "no user-facing output execution",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` IO",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no authority grants",
    "No blocking artifact gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_REPLY_PREVIEW_RESULT_ARTIFACT_REVIEW_V1",
}

_controlled_reply_preview_chain_next_step_review_required_markers = {
    "WESLR Controlled Reply Preview Chain Next Step Review V1",
    "controlled_reply_preview_chain_reviewed_next_step_design_controlled_reply_output_precondition_boundary_v1",
    "DESIGN_CONTROLLED_REPLY_OUTPUT_PRECONDITION_BOUNDARY_V1",
    "SECTION 1 — REVIEW SCOPE",
    "SECTION 2 — CHAIN INVENTORY",
    "SECTION 3 — VERIFIED ASSETS",
    "SECTION 4 — VALIDATION EVIDENCE SUMMARY",
    "SECTION 5 — WHAT IS PROVEN",
    "SECTION 6 — WHAT IS NOT PROVEN",
    "SECTION 7 — PRESERVED BOUNDARIES",
    "SECTION 8 — DENIED AUTHORITY SUMMARY",
    "SECTION 9 — VISIBLE RISKS",
    "SECTION 10 — GAP ANALYSIS",
    "SECTION 11 — RECOMMENDED NEXT LANE",
    "SECTION 12 — EXPLICIT BLOCKED LANES",
    "SECTION 13 — VALIDATION EVIDENCE FOR THIS REVIEW LANE",
    "SECTION 14 — CHAIN JUDGMENT",
    "SECTION 15 — SAFETY CONFIRMATION",
    "metadata is not preview output",
    "preview metadata is not sendable reply text",
    "safe Markdown is not a user answer",
    "JSON-safe metadata is not a reply payload",
    "validation pass is not answer/runtime/product authority",
    "artifact review is not runtime authorization",
    "OCC/OpenClaw is not deployed WESLR",
    "IMPLEMENT_CONTROLLED_REPLY_PREVIEW_OUTPUT_V1",
    "DESIGN_CONTROLLED_REPLY_TEXT_EXECUTION_BOUNDARY_V1",
    "DESIGN_CONTROLLED_REPLY_DRAFT_GENERATION_BOUNDARY_V1",
    "DESIGN_USER_FACING_REPLY_EXECUTION_BOUNDARY_V1",
    "AUDIT_CHAIN_FOR_RUNTIME_WIRING_READINESS_WITHOUT_IMPLEMENTATION_V1",
    "DESIGN_OFFICIAL_EVALUATION_PRECONDITIONS_BOUNDARY_V1",
}

_controlled_reply_output_precondition_boundary_required_markers = {
    "WESLR Controlled Reply Output Precondition Boundary V1",
    "DESIGN_CONTROLLED_REPLY_OUTPUT_PRECONDITION_BOUNDARY_V1",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_CHAIN_NEXT_STEP_REVIEW_V1.md",
    "controlled_reply_preview_chain_reviewed_next_step_design_controlled_reply_output_precondition_boundary_v1",
    "source metadata preconditions",
    "validation preconditions",
    "evidence/provenance preconditions",
    "safety preconditions",
    "raw/private content exclusion",
    "no ChatResponder activation",
    "no provider calls",
    "no `.weslr` reads",
    "no feature flags enabled",
    "no judges created",
    "no official benchmark claim",
    "no authority grants",
    "answer_authority_granted=false",
    "preview_authority_granted=false",
    "reply_output_authority_granted=false",
    "reply_text_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "reply_output_created=false",
    "sendable_reply_text_created=false",
    "actual_reply_body_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "preview-output implementation",
    "reply-text execution",
    "user-facing reply execution",
    "REVIEW_CONTROLLED_REPLY_OUTPUT_PRECONDITION_BOUNDARY_V1",
}

_controlled_reply_output_precondition_boundary_review_required_markers = {
    "WESLR Controlled Reply Output Precondition Boundary Review V1",
    "controlled_reply_output_precondition_boundary_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_REPLY_OUTPUT_PRECONDITION_BOUNDARY_V1.md",
    "design-only",
    "precondition-boundary-only",
    "metadata-only",
    "no output created",
    "no output-producing implementation",
    "no preview output",
    "no sendable reply text",
    "no actual reply body",
    "no reply text execution",
    "no final-answer prose",
    "no final answers",
    "no answer drafts",
    "no answer correctness claim",
    "no live dialogue",
    "no user-facing output execution",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no provider/search/advisor/model calls",
    "no .weslr IO",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no authority grants",
    "source metadata preconditions",
    "validation preconditions",
    "evidence/provenance preconditions",
    "safety preconditions",
    "raw/private content exclusion preconditions",
    "output-producing work remains blocked",
    "preview output remains blocked",
    "sendable reply text remains blocked",
    "actual reply body remains blocked",
    "runtime remains blocked",
    "authority remains blocked",
    "official evaluation remains blocked",
    "answer_authority_granted=false",
    "preview_authority_granted=false",
    "reply_output_authority_granted=false",
    "reply_text_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "reply_preview_executed=false",
    "preview_output_created=false",
    "reply_output_created=false",
    "reply_text_executed=false",
    "sendable_reply_text_created=false",
    "actual_reply_body_created=false",
    "user_facing_output_executed=false",
    "final_answer_generation_executed=false",
    "final_answer_generated=false",
    "final_answer_prose_created=false",
    "answer_draft_created=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "preview-output implementation",
    "reply-text execution",
    "sendable reply text creation",
    "actual reply body creation",
    "user-facing reply execution",
    "runtime readiness/wiring",
    "No blocking boundary design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_REPLY_OUTPUT_PRECONDITION_BOUNDARY_V1",
}

_controlled_reply_output_precondition_chain_next_step_review_required_markers = {
    "WESLR Controlled Reply Output Precondition Chain Next Step Review V1",
    "controlled_reply_output_precondition_chain_reviewed_next_step_design_unknown_engine_boundary_v1",
    "SECTION 1 — REVIEW SCOPE",
    "SECTION 2 — CHAIN INVENTORY",
    "SECTION 3 — VERIFIED ASSETS",
    "SECTION 4 — VALIDATION EVIDENCE SUMMARY",
    "SECTION 5 — WHAT IS PROVEN",
    "SECTION 6 — WHAT IS NOT PROVEN",
    "SECTION 7 — PRESERVED BOUNDARIES",
    "SECTION 8 — DENIED AUTHORITY SUMMARY",
    "SECTION 9 — VISIBLE RISKS",
    "SECTION 10 — GAP ANALYSIS",
    "SECTION 11 — RECOMMENDED NEXT LANE",
    "SECTION 12 — EXPLICIT BLOCKED LANES",
    "SECTION 13 — VALIDATION EVIDENCE FOR THIS REVIEW LANE",
    "SECTION 14 — CHAIN JUDGMENT",
    "SECTION 15 — SAFETY CONFIRMATION",
    "controlled reply output precondition boundary exists",
    "boundary review passed",
    "context alignment is current",
    "no output-producing implementation exists",
    "no runtime/provider/search/advisor/model/.weslr paths were activated",
    "no authority was granted",
    "precondition boundary is not output authority",
    "precondition boundary is not runtime authority",
    "precondition boundary is not answer authority",
    "precondition boundary is not official evaluation authority",
    "metadata must not become reply output",
    "safe Markdown must not become a user answer",
    "validation pass is not answer/runtime/product authority",
    "OCC/OpenClaw is not deployed WESLR",
    "DESIGN_UNKNOWN_ENGINE_BOUNDARY_V1",
    "no prediction authority",
    "no future-certainty claims",
    "IMPLEMENT_CONTROLLED_REPLY_OUTPUT_V1",
    "IMPLEMENT_CONTROLLED_REPLY_PREVIEW_OUTPUT_V1",
    "DESIGN_CONTROLLED_REPLY_TEXT_EXECUTION_BOUNDARY_V1",
    "DESIGN_REAL_CONVERSATION_SANDBOX_V1",
    "DESIGN_TURING_TEST_EXECUTION_V1",
}

_unknown_engine_boundary_required_markers = {
    "WESLR UNKNOWN ENGINE Boundary V1",
    "DESIGN_UNKNOWN_ENGINE_BOUNDARY_V1",
    "controlled_reply_output_precondition_chain_reviewed_next_step_design_unknown_engine_boundary_v1",
    "Boundary Purpose",
    "Non-Goals",
    "Architecture Placement",
    "Allowed Future Metadata Inputs",
    "Forbidden Inputs",
    "Future Metadata Output Shape",
    "Knowns Representation",
    "Unknowns Representation",
    "Uncertainty Map",
    "Possible Future Branch Labels",
    "Branch Likelihood Labels",
    "Missing Evidence Labels",
    "Falsification-Test Labels",
    "Safe Next Observation Labels",
    "Risk Boundary Labels",
    "Assumption Labels",
    "Evidence-Change Labels",
    "Confidence / Uncertainty Wording Rules",
    "No Prediction Authority Policy",
    "No Future-Certainty Policy",
    "No Answer Authority Policy",
    "No Reply-Output Policy",
    "No Runtime Policy",
    "No ChatResponder / respond_chat / generate_chat Policy",
    "No Provider / Search / Advisor / Model Policy",
    "No `.weslr` IO Policy",
    "No Feature-Flag Policy",
    "No Judges / Scores Policy",
    "No Official-Claims Policy",
    "No Turing-Test Execution Policy",
    "No Real Conversation Sandbox Policy",
    "Denied Authority Fields",
    "Blocked Behavior",
    "Visible Risks",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "future_certainty_claim_created=false",
    "reply_output_created=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "IMPLEMENT_UNKNOWN_ENGINE_V1",
    "EXECUTE_UNKNOWN_ENGINE_V1",
    "CREATE_UNKNOWN_ENGINE_RESULT_ARTIFACT_V1",
    "REVIEW_UNKNOWN_ENGINE_BOUNDARY_V1",
}

_cognitive_gym_suite_boundary_required_markers = {
    "WESLR Cognitive Gym Suite Boundary V1",
    "DESIGN_COGNITIVE_GYM_SUITE_BOUNDARY_V1",
    "internal cognition/evaluation suite",
    "future shared CognitiveGymRun-style protocol",
    "DESIGN_COGNITIVE_GYM_RUN_PROTOCOL_V1",
    "UNKNOWN ENGINE is the first Cognitive Gym engine candidate",
    "UNKNOWN ENGINE is not implemented",
    "UNKNOWN ENGINE helpers do not exist yet",
    "must not become a disconnected private report shape",
    "Shared protocol first. Individual engines second",
    "Disconnected Cognitive Gym engine modules are forbidden",
    "UNKNOWN_ENGINE",
    "CALIBRATION_LEDGER",
    "CONTRADICTION_FURNACE",
    "GOVERNANCE_BOUNDARY_ENGINE",
    "COUNTERFACTUAL_ENGINE",
    "BLINDSPOT_ENGINE",
    "INVARIANT_MINER",
    "INTENT_RECONSTRUCTION_ENGINE",
    "MEMORY_TRUST_ENGINE",
    "CAUSAL_TRACE_ENGINE",
    "FAILURE_MODE_SIMULATOR",
    "ABSTRACTION_LADDER",
    "SIGNAL_VS_NOISE_ENGINE",
    "ERDŐS / open mathematical structure",
    "open-problem-solving claims",
    "raw prompt text unless separately authorized",
    "ChatResponder/respond_chat/generate_chat output or call signals",
    "cognitive_gym_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "challenge_solution_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "cognitive_gym_executed=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "final_answer_generated=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "IMPLEMENT_COGNITIVE_GYM_SUITE_V1",
    "IMPLEMENT_UNKNOWN_ENGINE_V1",
    "EXECUTE_COGNITIVE_GYM_V1",
    "DESIGN_REAL_CONVERSATION_SANDBOX_V1",
    "DESIGN_TURING_TEST_EXECUTION_V1",
    "REVIEW_COGNITIVE_GYM_SUITE_BOUNDARY_V1",
}

_cognitive_gym_run_protocol_review_required_markers = {
    "WESLR CognitiveGymRun Protocol Review V1",
    "cognitive_gym_run_protocol_design_valid_ready_for_context_alignment",
    "docs/WESLR_COGNITIVE_GYM_RUN_PROTOCOL_V1.md",
    "design-only",
    "protocol-design-only",
    "shared protocol/report-shape only",
    "internal-only",
    "metadata-only",
    "no CognitiveGymRun implementation",
    "no Cognitive Gym implementation",
    "no UNKNOWN ENGINE implementation",
    "no engine helpers",
    "no engine execution",
    "no dry cognition runs",
    "no result artifact",
    "no prediction output",
    "no future-certainty claims",
    "no open-problem solution claims",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` IO",
    "no authority grants",
    "Shared CognitiveGymRun protocol first",
    "Individual engines second",
    "Runtime integration much later",
    "disconnected private report shapes",
    "protocol_name",
    "schema_version",
    "engine_name",
    "predictions_or_branch_labels",
    "compressed_lesson",
    "blocked_reason_labels",
    "UNKNOWN_ENGINE",
    "CALIBRATION_LEDGER",
    "CONTRADICTION_FURNACE",
    "GOVERNANCE_BOUNDARY_ENGINE",
    "COUNTERFACTUAL_ENGINE",
    "BLINDSPOT_ENGINE",
    "INVARIANT_MINER",
    "INTENT_RECONSTRUCTION_ENGINE",
    "MEMORY_TRUST_ENGINE",
    "CAUSAL_TRACE_ENGINE",
    "FAILURE_MODE_SIMULATOR",
    "ABSTRACTION_LADDER",
    "SIGNAL_VS_NOISE_ENGINE",
    "UNKNOWN / uncertainty",
    "ERDŐS / open mathematical structure",
    "MATERIALS / scientific discovery",
    "UNKNOWN ENGINE boundary exists and is reviewed",
    "UNKNOWN ENGINE is first Cognitive Gym engine candidate",
    "UNKNOWN ENGINE future helpers must use or migrate into CognitiveGymRun",
    "No open-problem solution claim is authorized",
    "cognitive_gym_authority_granted=false",
    "cognitive_gym_run_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "cognitive_gym_run_executed=false",
    "prediction_output_created=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "IMPLEMENT_COGNITIVE_GYM_RUN_PROTOCOL_V1",
    "EXECUTE_COGNITIVE_GYM_RUN_V1",
    "CREATE_COGNITIVE_GYM_RUN_RESULT_ARTIFACT_V1",
    "DESIGN_REAL_CONVERSATION_SANDBOX_V1",
    "DESIGN_TURING_TEST_EXECUTION_V1",
    "No blocking protocol design gaps were found",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_RUN_PROTOCOL_V1",
}

_cognitive_gym_run_protocol_helpers_implementation_review_required_markers = {
    "WESLR CognitiveGymRun Protocol Helpers Implementation Review V1",
    "cognitive_gym_run_protocol_helpers_implementation_valid_ready_for_context_alignment",
    "weslr/cognitive_gym_run_protocol.py",
    "weslr/tests/test_cognitive_gym_run_protocol_v1.py",
    "build_cognitive_gym_run_v1",
    "validate_cognitive_gym_run_v1",
    "summarize_cognitive_gym_run_v1",
    "render_cognitive_gym_run_markdown_v1",
    "to_cognitive_gym_run_json_safe_v1",
    "helper-only",
    "metadata-only",
    "internal-only",
    "deterministic",
    "import-safe",
    "side-effect-free",
    "pure in-memory",
    "JSON-safe",
    "safe-Markdown bounded",
    "validation-before-rendering",
    "no Cognitive Gym implementation",
    "no UNKNOWN ENGINE implementation",
    "no individual engine implementation",
    "no CognitiveGymRun execution",
    "no result artifact",
    "no prediction output",
    "no future-certainty claims",
    "no open-problem solution claims",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat imports or calls",
    "no provider/search/advisor/model calls",
    "no `.weslr` IO",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no authority grants",
    "`weslr/chat_responder.py` untouched",
    "UNKNOWN_ENGINE",
    "SIGNAL_VS_NOISE_ENGINE",
    "ERDŐS / open mathematical structure",
    "cognitive_gym_authority_granted=false",
    "prediction_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "No blocking implementation gaps found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_RUN_PROTOCOL_HELPERS_IMPLEMENTATION_V1",
}


_unknown_engine_helpers_required_markers = {
    "WESLR UNKNOWN ENGINE Helpers V1",
    "DESIGN_UNKNOWN_ENGINE_HELPERS_V1",
    "UNKNOWN ENGINE must use or migrate into CognitiveGymRun",
    "UNKNOWN ENGINE must not become a disconnected private report shape",
    "Shared CognitiveGymRun protocol first",
    "Individual engines second",
    "Runtime integration much later",
    "Helper Purpose",
    "Non-Goals",
    "Relationship To UNKNOWN ENGINE Boundary",
    "Relationship To CognitiveGymRun Protocol Helpers",
    "Future Implementation Paths",
    "Future Public APIs",
    "CognitiveGymRun Mapping",
    "UNKNOWN ENGINE-Specific Metadata Containment",
    "Validation Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Denied Authority Fields",
    "Blocked Behavior",
    "Frontier / Open Problem Boundary",
    "Visible Risks",
    "Abort Conditions",
    "Future Test Design Expectations",
    "Future Implementation / Review Sequence",
    "weslr/unknown_engine.py",
    "weslr/tests/test_unknown_engine_v1.py",
    "build_unknown_engine_run_v1",
    "validate_unknown_engine_run_v1",
    "summarize_unknown_engine_run_v1",
    "render_unknown_engine_run_markdown_v1",
    "to_unknown_engine_run_json_safe_v1",
    "engine_name = UNKNOWN_ENGINE",
    "challenge_track = UNKNOWN / uncertainty",
    "engine_specific_metadata",
    "unknown_engine_metadata",
    "missing_evidence_labels",
    "falsification_test_labels",
    "safe_next_observation_labels",
    "predictions_or_branch_labels",
    "cognitive_gym_authority_granted=false",
    "cognitive_gym_run_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "challenge_solution_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "cognitive_gym_run_executed=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "future_certainty_claim_created=false",
    "final_answer_generated=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "frontier/open-problem mapping is not a solution claim",
    "Erdős/Millennium-style challenge language is not proof of solving ability",
    "REVIEW_UNKNOWN_ENGINE_HELPERS_V1",
}


_unknown_engine_helpers_validation_fix_review_required_markers = {
    "WESLR UNKNOWN ENGINE Helpers Validation Fix Review V1",
    "unknown_engine_helpers_validation_fix_valid_ready_for_context_alignment",
    "92f35a1",
    "WESLR: fix UNKNOWN ENGINE validation blocks v1",
    "reply output: unsafe text",
    "user-facing output: unsafe text",
    "preview output: unsafe text",
    "final-answer prose",
    "answer draft: unsafe text",
    "unsafe extra wrapper metadata is not silently ignored",
    "engine_specific_metadata[\"unknown_engine_metadata\"]",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_UNKNOWN_ENGINE_HELPERS_VALIDATION_FIX_V1",
}


_unknown_engine_result_artifact_boundary_required_markers = {
    "WESLR UNKNOWN ENGINE Result Artifact Boundary V1",
    "DESIGN_UNKNOWN_ENGINE_RESULT_ARTIFACT_BOUNDARY_V1",
    "Artifact Purpose",
    "Non-Goals",
    "Relationship To UNKNOWN ENGINE Helpers",
    "Relationship To CognitiveGymRun Metadata",
    "Allowed Future Artifact Contents",
    "Forbidden Future Artifact Contents",
    "Validation-Before-Artifact Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Denied Authority Fields",
    "Frontier / Open Problem Boundary",
    "Blocked Behavior",
    "Visible Risks",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_V1.md",
    "weslr/unknown_engine_result_artifact.py",
    "weslr/tests/test_unknown_engine_result_artifact_v1.py",
    "cognitive_gym_authority_granted=false",
    "cognitive_gym_run_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "reply_output_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "future_certainty_claim_created=false",
    "reply_output_created=false",
    "preview_output_created=false",
    "final_answer_generated=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "REVIEW_UNKNOWN_ENGINE_RESULT_ARTIFACT_BOUNDARY_V1",
}


_unknown_engine_result_artifact_boundary_review_required_markers = {
    "WESLR UNKNOWN ENGINE Result Artifact Boundary Review V1",
    "unknown_engine_result_artifact_boundary_design_valid_ready_for_context_alignment",
    "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_BOUNDARY_V1.md",
    "design-only",
    "boundary-only",
    "internal-only",
    "metadata-only",
    "no implementation",
    "no artifact implementation",
    "no artifact created",
    "no UNKNOWN ENGINE execution",
    "no CognitiveGymRun execution",
    "no Cognitive Gym execution",
    "no runtime wiring",
    "no prediction output",
    "no future-certainty claims",
    "no open-problem solution claims",
    "no reply output",
    "no preview output",
    "no final-answer prose",
    "no answer drafts",
    "no user-facing output",
    "no provider/model/search/advisor calls",
    "no `.weslr` IO",
    "no judges/scores",
    "no official claims",
    "no authority grants",
    "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_V1.md",
    "weslr/unknown_engine_result_artifact.py",
    "weslr/tests/test_unknown_engine_result_artifact_v1.py",
    "Validation-Before-Artifact Findings",
    "Frontier / Open Problem Findings",
    "Blocked Behavior Findings",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_UNKNOWN_ENGINE_RESULT_ARTIFACT_BOUNDARY_V1",
}


_unknown_engine_result_artifact_helpers_required_markers = {
    "WESLR UNKNOWN ENGINE Result Artifact Helpers V1",
    "DESIGN_UNKNOWN_ENGINE_RESULT_ARTIFACT_HELPERS_V1",
    "Helper Purpose",
    "Non-Goals",
    "Relationship To UNKNOWN ENGINE Helpers",
    "Relationship To CognitiveGymRun Metadata",
    "Relationship To Result Artifact Boundary",
    "Future Target Paths",
    "Future Public APIs",
    "Input Contract",
    "Artifact Shape",
    "Allowed Artifact Fields",
    "Forbidden Artifact Fields / Content",
    "Validation-Before-Artifact Policy",
    "Blocked Artifact Behavior",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Denied Authority Fields",
    "Frontier / Open Problem Boundary",
    "Visible Risks",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "weslr/unknown_engine_result_artifact.py",
    "weslr/tests/test_unknown_engine_result_artifact_v1.py",
    "build_unknown_engine_result_artifact_v1",
    "validate_unknown_engine_result_artifact_v1",
    "summarize_unknown_engine_result_artifact_v1",
    "render_unknown_engine_result_artifact_markdown_v1",
    "to_unknown_engine_result_artifact_json_safe_v1",
    "cognitive_gym_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "reply_output_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "future_certainty_claim_created=false",
    "reply_output_created=false",
    "final_answer_generated=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "REVIEW_UNKNOWN_ENGINE_RESULT_ARTIFACT_HELPERS_V1",
}


_unknown_engine_result_artifact_helpers_review_required_markers = {
    "WESLR UNKNOWN ENGINE Result Artifact Helpers Review V1",
    "unknown_engine_result_artifact_helpers_design_valid_ready_for_context_alignment",
    "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_HELPERS_V1.md",
    "design-only",
    "helper-design-only",
    "boundary-preserving",
    "internal-only",
    "metadata-only",
    "no implementation",
    "no result artifact helper files",
    "no actual result artifact",
    "no execution",
    "no runtime",
    "no output",
    "no authority",
    "no `weslr/chat_responder.py` change",
    "Future Path Findings",
    "Future API Findings",
    "Input Contract Findings",
    "Artifact Shape Findings",
    "Forbidden Content Findings",
    "Validation-Before-Artifact Findings",
    "Safe Markdown Findings",
    "JSON-Safe Findings",
    "Frontier / Open Problem Findings",
    "weslr/unknown_engine_result_artifact.py",
    "weslr/tests/test_unknown_engine_result_artifact_v1.py",
    "build_unknown_engine_result_artifact_v1",
    "validate_unknown_engine_result_artifact_v1",
    "summarize_unknown_engine_result_artifact_v1",
    "render_unknown_engine_result_artifact_markdown_v1",
    "to_unknown_engine_result_artifact_json_safe_v1",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_UNKNOWN_ENGINE_RESULT_ARTIFACT_HELPERS_V1",
}



_unknown_engine_result_artifact_helpers_implementation_review_required_markers = {
    "WESLR UNKNOWN ENGINE Result Artifact Helpers Implementation Review V1",
    "unknown_engine_result_artifact_helpers_implementation_valid_ready_for_context_alignment",
    "weslr/unknown_engine_result_artifact.py",
    "weslr/tests/test_unknown_engine_result_artifact_v1.py",
    "build_unknown_engine_result_artifact_v1",
    "validate_unknown_engine_result_artifact_v1",
    "summarize_unknown_engine_result_artifact_v1",
    "render_unknown_engine_result_artifact_markdown_v1",
    "to_unknown_engine_result_artifact_json_safe_v1",
    "helper-only",
    "metadata-only",
    "internal-only",
    "validation-before-artifact",
    "no actual result artifact file creation",
    "no `weslr/chat_responder.py` change",
    "Input Contract Findings",
    "Artifact Shape Findings",
    "Safe Markdown Findings",
    "JSON-Safe Findings",
    "Test Coverage Findings",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_UNKNOWN_ENGINE_RESULT_ARTIFACT_HELPERS_IMPLEMENTATION_V1",
}


_unknown_engine_result_artifact_required_markers = {
    "WESLR UNKNOWN ENGINE Result Artifact V1",
    "unknown_engine_result_artifact_v1",
    "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_V1.md",
    "REVIEW_UNKNOWN_ENGINE_RESULT_ARTIFACT_V1",
    "build_unknown_engine_run_v1",
    "validate_unknown_engine_run_v1",
    "build_unknown_engine_result_artifact_v1",
    "validate_unknown_engine_result_artifact_v1",
    "summarize_unknown_engine_result_artifact_v1",
    "render_unknown_engine_result_artifact_markdown_v1",
    "to_unknown_engine_result_artifact_json_safe_v1",
    "controlled/synthetic metadata only",
    "internal metadata artifact only",
    "internal-only",
    "metadata-only",
    "helper_output_based",
    "validation_backed",
    "safe Markdown",
    "JSON-Safe",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "reply_output_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "unknown_engine_executed=false",
    "cognitive_gym_run_executed=false",
    "cognitive_gym_executed=false",
    "prediction_output_created=false",
    "future_certainty_claim_created=false",
    "final_answer_generated=false",
    "final_answer_prose_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_read_performed=false",
    "dot_weslr_write_performed=false",
    "judges_created=false",
    "scores_created=false",
    "official_claim_made=false",
    "not runtime",
    "not execution",
    "not prediction authority",
    "not future certainty",
    "not open-problem solution evidence",
    "not reply output",
    "not final-answer prose",
    "not user-facing output",
    "not official evaluation",
    "not product/intelligence/Turing/IQ/certification readiness",
    "not authority",
}


_unknown_engine_result_artifact_review_required_markers = {
    "WESLR UNKNOWN ENGINE Result Artifact Review V1",
    "unknown_engine_result_artifact_valid_ready_for_context_alignment",
    "docs/WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_V1.md",
    "internal metadata artifact only",
    "created through reviewed helper path",
    "not runtime",
    "not UNKNOWN ENGINE execution",
    "not CognitiveGymRun execution",
    "not Cognitive Gym execution",
    "not prediction output",
    "not future certainty",
    "not open-problem solution evidence",
    "not reply output",
    "not preview output",
    "not final-answer prose",
    "not user-facing output",
    "not official evaluation",
    "not product/intelligence/Turing/IQ/certification readiness",
    "not authority",
    "build_unknown_engine_run_v1",
    "validate_unknown_engine_run_v1",
    "build_unknown_engine_result_artifact_v1",
    "validate_unknown_engine_result_artifact_v1",
    "summarize_unknown_engine_result_artifact_v1",
    "render_unknown_engine_result_artifact_markdown_v1",
    "to_unknown_engine_result_artifact_json_safe_v1",
    "source_validation_status: validation_pass_metadata_quality_only",
    "artifact_validation_valid: True",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "reply_output_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "unknown_engine_executed=false",
    "cognitive_gym_run_executed=false",
    "cognitive_gym_executed=false",
    "prediction_output_created=false",
    "future_certainty_claim_created=false",
    "final_answer_generated=false",
    "final_answer_prose_created=false",
    "runtime_wired=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_read_performed=false",
    "dot_weslr_write_performed=false",
    "judges_created=false",
    "scores_created=false",
    "official_claim_made=false",
    "safe Markdown remains internal review material only",
    "JSON-safe metadata is not a reply payload",
    "artifact is not execution evidence",
    "frontier/open-problem metadata is not solution evidence",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_UNKNOWN_ENGINE_RESULT_ARTIFACT_V1",
}

_unknown_engine_helpers_implementation_review_required_markers = {
    "WESLR UNKNOWN ENGINE Helpers Implementation Review V1",
    "unknown_engine_helpers_implementation_blocked_do_not_use",
    "weslr/unknown_engine.py",
    "weslr/tests/test_unknown_engine_v1.py",
    "build_unknown_engine_run_v1",
    "validate_unknown_engine_run_v1",
    "summarize_unknown_engine_run_v1",
    "render_unknown_engine_run_markdown_v1",
    "to_unknown_engine_run_json_safe_v1",
    "CognitiveGymRun-backed",
    "engine_specific_metadata[\"unknown_engine_metadata\"]",
    "validation coverage is incomplete",
    "reply output: ...",
    "user-facing output: ...",
    "preview output: ...",
    "final-answer prose",
    "answer draft: ...",
    "FIX_UNKNOWN_ENGINE_HELPERS_VALIDATION_BLOCKS_V1",
}


_unknown_engine_helpers_review_required_markers = {
    "WESLR UNKNOWN ENGINE Helpers Review V1",
    "unknown_engine_helpers_design_valid_ready_for_context_alignment",
    "docs/WESLR_UNKNOWN_ENGINE_HELPERS_V1.md",
    "design-only",
    "helper-design-only",
    "CognitiveGymRun-first",
    "internal-only",
    "metadata-only",
    "no UNKNOWN ENGINE implementation",
    "no UNKNOWN ENGINE helpers created",
    "no Cognitive Gym implementation",
    "no individual engine implementation",
    "no execution",
    "no result artifact",
    "no prediction output",
    "no future-certainty claims",
    "no open-problem solution claims",
    "no reply output",
    "no final answers",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no providers/search/advisors/models",
    "no `.weslr` IO",
    "no judges/scores",
    "no official claims",
    "no authority grants",
    "weslr/chat_responder.py` untouched",
    "helper purpose",
    "non-goals",
    "relationship to UNKNOWN ENGINE boundary",
    "relationship to CognitiveGymRun protocol helpers",
    "future helper module path",
    "future test module path",
    "future public APIs",
    "CognitiveGymRun mapping",
    "UNKNOWN ENGINE-specific metadata containment",
    "validation policy",
    "safe Markdown policy",
    "JSON-safe policy",
    "blocked behavior",
    "denied authority fields",
    "visible risks",
    "abort conditions",
    "future implementation/review sequence",
    "weslr/unknown_engine.py",
    "weslr/tests/test_unknown_engine_v1.py",
    "build_unknown_engine_run_v1",
    "validate_unknown_engine_run_v1",
    "summarize_unknown_engine_run_v1",
    "render_unknown_engine_run_markdown_v1",
    "to_unknown_engine_run_json_safe_v1",
    "engine_name = UNKNOWN_ENGINE",
    "challenge_track = UNKNOWN / uncertainty",
    "all required CognitiveGymRun fields",
    "all denied authority fields present and false",
    "validation-before-rendering",
    "engine_specific_metadata",
    "frontier/open-problem mapping is metadata only",
    "Erdős/Millennium-style challenge language is not proof of solving ability",
    "cognitive_gym_authority_granted=false",
    "cognitive_gym_run_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "No blocking design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_UNKNOWN_ENGINE_HELPERS_V1",
}

_cognitive_gym_run_protocol_required_markers = {
    "WESLR CognitiveGymRun Protocol V1",
    "DESIGN_COGNITIVE_GYM_RUN_PROTOCOL_V1",
    "shared metadata protocol",
    "internal CognitiveGymRun report",
    "metadata-only cognition exercise",
    "Shared protocol first",
    "Individual engines second",
    "Runtime integration much later",
    "does not implement CognitiveGymRun",
    "does not implement Cognitive Gym",
    "does not implement UNKNOWN ENGINE",
    "protocol_name",
    "schema_version",
    "engine_name",
    "engine_version_label",
    "challenge_track",
    "input_state",
    "observations",
    "knowns",
    "unknowns",
    "hypotheses",
    "predictions_or_branch_labels",
    "confidence",
    "uncertainty",
    "invalidation_signals",
    "reveal_or_outcome",
    "correction",
    "compressed_lesson",
    "boundary_status",
    "denied_authority_fields",
    "validation_status",
    "blocked_reason_labels",
    "UNKNOWN_ENGINE",
    "CALIBRATION_LEDGER",
    "CONTRADICTION_FURNACE",
    "GOVERNANCE_BOUNDARY_ENGINE",
    "COUNTERFACTUAL_ENGINE",
    "BLINDSPOT_ENGINE",
    "INVARIANT_MINER",
    "INTENT_RECONSTRUCTION_ENGINE",
    "MEMORY_TRUST_ENGINE",
    "CAUSAL_TRACE_ENGINE",
    "FAILURE_MODE_SIMULATOR",
    "ABSTRACTION_LADDER",
    "SIGNAL_VS_NOISE_ENGINE",
    "ERDŐS / open mathematical structure",
    "No open-problem solution claim is authorized",
    "raw prompt text unless separately authorized",
    "ChatResponder/respond_chat/generate_chat output or call signals",
    "cognitive_gym_authority_granted=false",
    "cognitive_gym_run_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "cognitive_gym_run_executed=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "IMPLEMENT_COGNITIVE_GYM_RUN_PROTOCOL_V1",
    "EXECUTE_COGNITIVE_GYM_RUN_V1",
    "CREATE_COGNITIVE_GYM_RUN_RESULT_ARTIFACT_V1",
    "DESIGN_REAL_CONVERSATION_SANDBOX_V1",
    "DESIGN_TURING_TEST_EXECUTION_V1",
    "REVIEW_COGNITIVE_GYM_RUN_PROTOCOL_V1",
}

_cognitive_gym_suite_boundary_review_required_markers = {
    "WESLR Cognitive Gym Suite Boundary Review V1",
    "cognitive_gym_suite_boundary_design_valid_ready_for_context_alignment",
    "docs/WESLR_COGNITIVE_GYM_SUITE_BOUNDARY_V1.md",
    "design-only",
    "suite-boundary-only",
    "internal-only",
    "metadata-only",
    "no Cognitive Gym implementation",
    "no `CognitiveGymRun` implementation",
    "no UNKNOWN ENGINE implementation",
    "no engine helpers",
    "no engine execution",
    "no dry cognition runs",
    "no prediction output",
    "no future-certainty claims",
    "no open-problem solution claims",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` IO",
    "no judges/scores",
    "no authority grants",
    "Do not implement Cognitive Gym engines as disconnected modules",
    "one common CognitiveGymRun-style protocol/report shape",
    "Shared protocol first",
    "Individual engines second",
    "UNKNOWN_ENGINE",
    "CALIBRATION_LEDGER",
    "CONTRADICTION_FURNACE",
    "GOVERNANCE_BOUNDARY_ENGINE",
    "COUNTERFACTUAL_ENGINE",
    "BLINDSPOT_ENGINE",
    "INVARIANT_MINER",
    "INTENT_RECONSTRUCTION_ENGINE",
    "MEMORY_TRUST_ENGINE",
    "CAUSAL_TRACE_ENGINE",
    "FAILURE_MODE_SIMULATOR",
    "ABSTRACTION_LADDER",
    "SIGNAL_VS_NOISE_ENGINE",
    "UNKNOWN ENGINE boundary exists and is reviewed",
    "UNKNOWN ENGINE is the first Cognitive Gym engine candidate",
    "UNKNOWN ENGINE is not implemented",
    "UNKNOWN ENGINE helpers do not exist yet",
    "DESIGN_COGNITIVE_GYM_RUN_PROTOCOL_V1",
    "engine_name",
    "input_state",
    "predictions_or_branch_labels",
    "compressed_lesson",
    "UNKNOWN / uncertainty",
    "ERDŐS / open mathematical structure",
    "COUNTEREXAMPLE / falsification",
    "MATERIALS / scientific discovery",
    "WESLR must not claim to solve open problems",
    "cognitive_gym_authority_granted=false",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "open_problem_solution_claim_authorized=false",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "cognitive_gym_executed=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "IMPLEMENT_COGNITIVE_GYM_SUITE_V1",
    "IMPLEMENT_UNKNOWN_ENGINE_V1",
    "EXECUTE_COGNITIVE_GYM_V1",
    "DESIGN_REAL_CONVERSATION_SANDBOX_V1",
    "DESIGN_TURING_TEST_EXECUTION_V1",
    "No blocking boundary design gaps were found",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_COGNITIVE_GYM_SUITE_BOUNDARY_V1",
}

_unknown_engine_boundary_review_required_markers = {
    "WESLR UNKNOWN ENGINE Boundary Review V1",
    "unknown_engine_boundary_design_valid_ready_for_context_alignment",
    "docs/WESLR_UNKNOWN_ENGINE_BOUNDARY_V1.md",
    "design-only",
    "metadata-only",
    "internal-only",
    "uncertainty/frontier cognition boundary only",
    "positioned after state/context/evidence interpretation",
    "positioned before answer formation or future conversation sandbox planning",
    "no UNKNOWN ENGINE implementation",
    "no UNKNOWN ENGINE helpers",
    "no UNKNOWN ENGINE execution",
    "no prediction output",
    "no future-certainty claims",
    "no possible-future output for users",
    "no reply output",
    "no preview output",
    "no sendable reply text",
    "no actual reply body",
    "no final-answer prose",
    "no final answers",
    "no answer drafts",
    "no live dialogue",
    "no user-facing output execution",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` IO",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no authority grants",
    "Cognitive Gym Compatibility Check",
    "UNKNOWN ENGINE may be first Cognitive Gym engine candidate.",
    "shared CognitiveGymRun-style protocol",
    "engine_name",
    "input_state",
    "observations",
    "knowns",
    "unknowns",
    "hypotheses",
    "predictions_or_branch_labels",
    "denied_authority_fields",
    "validation_status",
    "unknown_engine_authority_granted=false",
    "prediction_authority_granted=false",
    "future_certainty_authority_granted=false",
    "answer_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "unknown_engine_executed=false",
    "prediction_output_created=false",
    "future_certainty_claim_created=false",
    "reply_output_created=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "provider_call_made=false",
    "official_claim_made=false",
    "IMPLEMENT_UNKNOWN_ENGINE_V1",
    "EXECUTE_UNKNOWN_ENGINE_V1",
    "CREATE_UNKNOWN_ENGINE_RESULT_ARTIFACT_V1",
    "No blocking boundary design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_UNKNOWN_ENGINE_BOUNDARY_V1",
}


_controlled_reply_preview_boundary_review_doc = "docs/WESLR_CONTROLLED_REPLY_PREVIEW_BOUNDARY_REVIEW_V1.md"
_controlled_reply_preview_boundary_review_required_markers = {
    "WESLR Controlled Reply Preview Boundary Review V1",
    "controlled_reply_preview_boundary_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_REPLY_PREVIEW_BOUNDARY_V1.md",
    "design-only",
    "boundary-only",
    "reply-preview-boundary-only",
    "metadata-only",
    "no reply preview implementation",
    "no reply preview execution",
    "no sendable reply text",
    "no actual reply body",
    "no final-answer prose",
    "no answer drafts",
    "no reply text execution",
    "no user-facing output execution",
    "no live dialogue",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` reads/writes",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no answer/preview/reply-text/user-facing-output/composition/runtime/official evaluation authority granted",
    "no reply-preview result artifact created",
    "No blocking boundary design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_REPLY_PREVIEW_BOUNDARY_V1",
}

_controlled_reply_preview_boundary_doc = "docs/WESLR_CONTROLLED_REPLY_PREVIEW_BOUNDARY_V1.md"
_controlled_reply_preview_boundary_required_markers = {
    "WESLR Controlled Reply Preview Boundary V1",
    "DESIGN_CONTROLLED_REPLY_PREVIEW_BOUNDARY_V1",
    "REVIEW_CONTROLLED_REPLY_PREVIEW_BOUNDARY_V1",
    "Controlled Reply Preview Purpose",
    "Why Controlled Reply-Text Result Metadata Does Not Grant Preview Authority",
    "Allowed Future Reply-Preview Metadata Inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "Exact No-Sendable-Reply-Text Boundary",
    "Exact No-Actual-Reply-Body Boundary",
    "Exact No-Reply-Execution Boundary",
    "Exact No-User-Facing-Output-Execution Boundary",
    "Exact No-Live-Dialogue Boundary",
    "Exact No-Runtime Boundary",
    "Exact No-ChatResponder / respond_chat / generate_chat Boundary",
    "Exact No-Provider / Search / Advisor / Model Boundary",
    "Exact No-Official-Claims Boundary",
    "Validation-Before-Preview Policy",
    "Controlled Reply-Preview Artifact Shape For A Future Lane",
    "Denied Authority Fields",
    "Blocked Reply-Preview Behavior",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "reply_preview_implemented=false",
    "reply_preview_executed=false",
    "sendable_reply_text_created=false",
    "actual_reply_body_created=false",
    "reply_text_executed=false",
    "user_facing_output_executed=false",
    "live_dialogue_output_created=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "official_claim_made=false",
    "answer_authority_granted=false",
    "preview_authority_granted=false",
    "reply_text_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
}

_controlled_reply_text_chain_next_step_review_doc = "docs/WESLR_CONTROLLED_REPLY_TEXT_CHAIN_NEXT_STEP_REVIEW_V1.md"
_controlled_reply_text_chain_next_step_review_required_markers = {
    "WESLR Controlled Reply Text Chain Next Step Review V1",
    "controlled_reply_text_chain_reviewed_next_step_design_controlled_reply_preview_boundary_v1",
    "DESIGN_CONTROLLED_REPLY_PREVIEW_BOUNDARY_V1",
    "metadata-only controlled reply-text structures exist",
    "helper implementation exists for safe internal reply-text metadata",
    "controlled reply text result artifact exists",
    "result artifact is internal-only, metadata-only, helper-output based, validation-backed, safe Markdown, JSON-safe eligible, no-authority, no-runtime, and non-user-facing",
    "denied authority fields stayed false",
    "validation/release checks passed",
    "weslr/chat_responder.py` stayed untouched",
    "no runtime/provider/search/advisor/model/.weslr paths were activated",
    "actual reply execution",
    "sendable reply text",
    "actual reply body",
    "final-answer prose",
    "final answers",
    "answer drafts",
    "answer correctness",
    "user-facing output execution",
    "prompt/live dialogue execution",
    "live chat behavior",
    "runtime readiness",
    "ChatResponder/respond_chat/generate_chat activation",
    "provider/search/advisor/model integration",
    "official Turing-test claim",
    "IQ claim",
    "certification claim",
    "product readiness",
    "authority to answer users",
    "authority to wire runtime",
    "preview authority",
    "reply-text authority",
    "user-facing-output authority",
    "runtime authority",
    "official evaluation authority",
    "No blocking chain gaps were found",
    "Recommended next lane",
    "Explicit Blocked Lanes",
}

_controlled_reply_text_boundary_doc = "docs/WESLR_CONTROLLED_REPLY_TEXT_BOUNDARY_V1.md"
_controlled_reply_text_boundary_required_markers = {
    "WESLR Controlled Reply Text Boundary V1",
    "DESIGN_CONTROLLED_REPLY_TEXT_BOUNDARY_V1",
    "REVIEW_CONTROLLED_REPLY_TEXT_BOUNDARY_V1",
    "Controlled Reply Text Purpose",
    "Why Controlled User-Facing-Output Result Metadata Does Not Grant Reply-Text Authority",
    "Allowed Future Reply-Text Metadata Inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "Exact No-User-Facing-Output-Execution Boundary",
    "Exact No-Live-Dialogue Boundary",
    "Exact No-Runtime Boundary",
    "Exact No-ChatResponder / respond_chat / generate_chat Boundary",
    "Exact No-Provider / Search / Advisor / Model Boundary",
    "Exact No-Official-Claims Boundary",
    "Validation-Before-Reply-Text Policy",
    "Controlled Reply-Text Artifact Shape For A Future Lane",
    "Denied Authority Fields",
    "Blocked Reply-Text Behavior",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "reply_text_implementation_authorized: false",
    "reply_text_execution_authorized: false",
    "user_facing_output_execution_authorized: false",
    "live_chat_behavior_authorized: false",
    "runtime_wiring_authorized: false",
    "chat_responder_use_authorized: false",
    "provider_model_search_advisor_calls_authorized: false",
    "official_evaluation_claims_authorized: false",
    "answer_authority_granted: false",
    "reply_text_authority_granted: false",
    "user_facing_output_authority_granted: false",
    "runtime_authority_granted: false",
    "official_evaluation_authority_granted: false",
    "actual sendable reply text",
    "answer draft prose",
    "final-answer prose intended for users",
    "live-dialogue output",
    "user-facing response body",
    "ChatResponder/respond_chat/generate_chat use",
    "provider/model/search/advisor calls",
    "official benchmark/IQ/Turing/certification/product-readiness claims",
    "controlled_reply_text_boundary_design_only_no_reply_text_authority",
}


_controlled_reply_text_boundary_review_doc = "docs/WESLR_CONTROLLED_REPLY_TEXT_BOUNDARY_REVIEW_V1.md"
_controlled_reply_text_boundary_review_required_markers = {
    "WESLR Controlled Reply Text Boundary Review V1",
    "controlled_reply_text_boundary_design_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_REPLY_TEXT_BOUNDARY_V1.md",
    "design-only",
    "boundary-only",
    "reply-text-boundary-only",
    "metadata-only",
    "no reply text implementation",
    "no reply text execution",
    "no actual sendable reply text",
    "no final-answer prose intended for users",
    "no answer drafts",
    "no user-facing output execution",
    "no live dialogue",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` access",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no answer/reply-text/user-facing-output/composition/runtime/official evaluation authority granted",
    "no reply-text result artifact created",
    "weslr/chat_responder.py` untouched",
    "controlled reply text purpose",
    "why controlled user-facing-output result metadata does not grant reply-text authority",
    "allowed future reply-text metadata inputs",
    "forbidden real-user/live/raw/provider/runtime inputs",
    "exact no-user-facing-output-execution boundary",
    "exact no-live-dialogue boundary",
    "exact no-runtime boundary",
    "exact no-ChatResponder/respond_chat/generate_chat boundary",
    "exact no-provider/search/advisor/model boundary",
    "exact no-official-claims boundary",
    "validation-before-reply-text policy",
    "controlled reply-text artifact shape for a future lane",
    "denied authority fields",
    "blocked reply-text behavior",
    "visible risks/followups",
    "abort conditions",
    "future implementation/review sequence",
    "actual sendable reply text",
    "answer draft prose",
    "final-answer prose intended for users",
    "live-dialogue output",
    "user-facing response body",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_REPLY_TEXT_BOUNDARY_V1",
    "controlled_reply_text_boundary_review_safe_for_context_alignment_only",
}


_controlled_reply_text_helpers_doc = "docs/WESLR_CONTROLLED_REPLY_TEXT_HELPERS_V1.md"
_controlled_reply_text_helpers_required_markers = {
    "WESLR Controlled Reply Text Helpers V1",
    "DESIGN_CONTROLLED_REPLY_TEXT_HELPERS_V1",
    "REVIEW_CONTROLLED_REPLY_TEXT_HELPERS_V1",
    "weslr/controlled_reply_text.py",
    "weslr/tests/test_controlled_reply_text_v1.py",
    "build_controlled_reply_text_artifact_v1",
    "validate_controlled_reply_text_artifact_v1",
    "summarize_controlled_reply_text_artifact_v1",
    "render_controlled_reply_text_artifact_markdown_v1",
    "to_controlled_reply_text_artifact_json_safe_v1",
    "Controlled Reply-Text Artifact Shape",
    "Allowed Reply-Text Metadata Inputs",
    "Forbidden Real-User / Live / Raw / Provider / Runtime Inputs",
    "Relationship To Controlled User-Facing Output Result Artifact",
    "Relationship To Controlled Reply Text Boundary",
    "Validation-Before-Reply-Text Policy",
    "Validation-Before-Rendering Policy",
    "No-Sendable-Reply-Text Policy",
    "No-User-Facing-Output-Execution Policy",
    "No-Live-Dialogue Policy",
    "No-Runtime Policy",
    "No-ChatResponder / respond_chat / generate_chat Policy",
    "No-Provider / Search / Advisor / Model Policy",
    "Safe Markdown Policy",
    "JSON-Safe Policy",
    "Blocked Artifact Behavior",
    "Denied Authority Fields",
    "Visible Risks And Followups",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "helper_implementation_created: false",
    "reply_text_implementation_authorized: false",
    "reply_text_execution_authorized: false",
    "actual_sendable_reply_text_created: false",
    "user_facing_output_execution_authorized: false",
    "user_facing_output_executed: false",
    "live_dialogue_output_created: false",
    "real_user_query_answered: false",
    "runtime_wired: false",
    "chat_responder_called: false",
    "respond_chat_called: false",
    "generate_chat_called: false",
    "provider_call_made: false",
    "model_call_made: false",
    "search_call_made: false",
    "advisor_call_made: false",
    "official_claim_made: false",
    "answer_authority_granted: false",
    "reply_text_authority_granted: false",
    "user_facing_output_authority_granted: false",
    "runtime_authority_granted: false",
    "official_evaluation_authority_granted: false",
    "actual sendable reply text",
    "final-answer prose intended for users",
    "answer draft prose",
    "live-dialogue output",
    "user-facing response body",
    "controlled_reply_text_helpers_design_only_no_reply_text_authority",
}


_controlled_reply_text_helpers_review_doc = "docs/WESLR_CONTROLLED_REPLY_TEXT_HELPERS_REVIEW_V1.md"
_controlled_reply_text_helpers_review_required_markers = {
    "WESLR Controlled Reply Text Helpers Review V1",
    "REVIEW_CONTROLLED_REPLY_TEXT_HELPERS_V1",
    "controlled_reply_text_helpers_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_REPLY_TEXT_HELPERS_V1",
    "docs/WESLR_CONTROLLED_REPLY_TEXT_HELPERS_V1.md",
    "design-only",
    "helper-design-only",
    "metadata-only",
    "internal-only",
    "no controlled reply text helper implementation",
    "no reply text execution",
    "no actual sendable reply text",
    "no final-answer prose",
    "no answer drafts",
    "no live dialogue",
    "no user-facing output execution",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` reads/writes",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no answer/reply-text/user-facing-output/composition/runtime/official evaluation authority granted",
    "no reply-text result artifact created",
    "weslr/chat_responder.py` untouched",
    "weslr/controlled_reply_text.py",
    "weslr/tests/test_controlled_reply_text_v1.py",
    "build_controlled_reply_text_artifact_v1",
    "validate_controlled_reply_text_artifact_v1",
    "summarize_controlled_reply_text_artifact_v1",
    "render_controlled_reply_text_artifact_markdown_v1",
    "to_controlled_reply_text_artifact_json_safe_v1",
    "controlled reply-text artifact shape",
    "allowed reply-text metadata inputs",
    "forbidden real-user/live/raw/provider/runtime inputs",
    "relationship to controlled user-facing output result artifact",
    "relationship to controlled reply text boundary",
    "validation-before-reply-text policy",
    "validation-before-rendering policy",
    "no-sendable-reply-text policy",
    "no-user-facing-output-execution policy",
    "no-live-dialogue policy",
    "no-runtime policy",
    "no-ChatResponder/respond_chat/generate_chat policy",
    "no-provider/search/advisor/model policy",
    "safe Markdown policy",
    "JSON-safe policy",
    "blocked artifact behavior",
    "denied authority fields",
    "visible risks/followups",
    "abort conditions",
    "future implementation/review sequence",
    "controlled_reply_text_helpers_design_review_safe_for_context_alignment_only",
}


_controlled_reply_text_result_design_review_doc = "docs/WESLR_CONTROLLED_REPLY_TEXT_RESULT_DESIGN_REVIEW_V1.md"
_controlled_reply_text_result_design_review_required_markers = {
    "WESLR Controlled Reply Text Result Design Review V1",
    "controlled_reply_text_result_design_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_REPLY_TEXT_RESULT_DESIGN_V1",
    "docs/WESLR_CONTROLLED_REPLY_TEXT_RESULT_V1.md",
    "docs/WESLR_CONTROLLED_REPLY_TEXT_RESULT_ARTIFACT_V1.md",
    "design-only",
    "result-design-only",
    "metadata-only",
    "internal-only",
    "helper-output based",
    "validation-before-result-writing",
    "safe-Markdown bounded",
    "JSON-safe bounded",
    "no result artifact created",
    "no reply execution",
    "no sendable reply text",
    "no actual reply body",
    "no final-answer prose",
    "no answer drafts",
    "no runtime wiring",
    "no ChatResponder/respond_chat/generate_chat calls/imports",
    "no provider/search/advisor/model calls",
    "no `.weslr` IO",
    "no feature flags",
    "no judges/scores",
    "no official claims",
    "no answer/reply-text/user-facing-output/composition/runtime/official evaluation authority granted",
    "weslr/chat_responder.py` untouched",
    "Future artifact creation requires separate authorization",
    "Validation status: PASS",
}


_controlled_reply_text_result_artifact_review_doc = "docs/WESLR_CONTROLLED_REPLY_TEXT_RESULT_ARTIFACT_REVIEW_V1.md"
_controlled_reply_text_result_artifact_review_required_markers = {
    "WESLR Controlled Reply Text Result Artifact Review V1",
    "controlled_reply_text_result_artifact_valid_ready_for_context_alignment",
    "docs/WESLR_CONTROLLED_REPLY_TEXT_RESULT_ARTIFACT_V1.md",
    "exactly the approved artifact path",
    "internal-only",
    "metadata-only",
    "helper-output based",
    "validation-backed",
    "safe Markdown",
    "JSON-safe eligible",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "controlled/synthetic metadata only",
    "created using only approved helper API",
    "not reply text execution",
    "not sendable reply text",
    "not actual reply body",
    "not final-answer prose",
    "not answer draft creation",
    "not live dialogue",
    "not user-facing output execution",
    "not answer composition execution",
    "not answer formation execution",
    "not live chat behavior",
    "not runtime readiness",
    "not ChatResponder/respond_chat/generate_chat output",
    "not provider/search/advisor/model output",
    "not official benchmark/IQ/Turing/certification/product-readiness evidence",
    "not answer authority",
    "not reply-text authority",
    "not user-facing-output authority",
    "not composition authority",
    "not runtime authority",
    "not official evaluation authority",
    "No blocking artifact gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_REPLY_TEXT_RESULT_ARTIFACT_REVIEW_V1",
}

_controlled_reply_text_result_artifact_doc = "docs/WESLR_CONTROLLED_REPLY_TEXT_RESULT_ARTIFACT_V1.md"
_controlled_reply_text_result_artifact_required_markers = {
    "WESLR Controlled Reply Text Result Artifact V1",
    "controlled_reply_text_result_artifact_v1",
    "REVIEW_CONTROLLED_REPLY_TEXT_RESULT_ARTIFACT_V1",
    "build_controlled_reply_text_artifact_v1",
    "validate_controlled_reply_text_artifact_v1",
    "summarize_controlled_reply_text_artifact_v1",
    "render_controlled_reply_text_artifact_markdown_v1",
    "to_controlled_reply_text_artifact_json_safe_v1",
    "internal-only",
    "metadata-only",
    "helper-output based",
    "validation-backed",
    "safe Markdown",
    "JSON-safe eligible",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "controlled/synthetic metadata only",
    "reply_text_executed=false",
    "sendable_reply_text_created=false",
    "actual_reply_body_created=false",
    "user_facing_output_executed=false",
    "live_dialogue_output_created=false",
    "final_answer_generation_executed=false",
    "final_answer_generated=false",
    "final_answer_prose_created=false",
    "answer_draft_created=false",
    "answer_composition_executed=false",
    "answer_formation_executed=false",
    "runtime_wired=false",
    "chat_responder_called=false",
    "respond_chat_called=false",
    "generate_chat_called=false",
    "provider_call_made=false",
    "model_call_made=false",
    "search_call_made=false",
    "advisor_call_made=false",
    "dot_weslr_read_performed=false",
    "dot_weslr_write_performed=false",
    "feature_flag_enabled=false",
    "judges_created=false",
    "scores_created=false",
    "official_claim_made=false",
    "answer_authority_granted=false",
    "reply_text_authority_granted=false",
    "user_facing_output_authority_granted=false",
    "composition_authority_granted=false",
    "runtime_authority_granted=false",
    "official_evaluation_authority_granted=false",
    "No-Reply-Text-Execution Boundary",
    "No-Sendable-Reply-Text Boundary",
    "No-Actual-Reply-Body Boundary",
    "No-Final-Answer-Prose Boundary",
    "No-Answer-Draft Boundary",
    "No-User-Facing-Output-Execution Boundary",
    "No-Live-Dialogue Boundary",
    "No-Runtime Boundary",
    "No-ChatResponder / respond_chat / generate_chat Boundary",
    "No-Provider / Search / Advisor / Model Boundary",
    "No-.weslr / No-Feature-Flag Boundary",
    "No-Judges / Scores Boundary",
    "No-Official-Claims Boundary",
}

_controlled_reply_text_result_design_doc = "docs/WESLR_CONTROLLED_REPLY_TEXT_RESULT_V1.md"
_controlled_reply_text_result_design_required_markers = {
    "WESLR Controlled Reply Text Result Design V1",
    "DESIGN_CONTROLLED_REPLY_TEXT_RESULT_V1",
    "REVIEW_CONTROLLED_REPLY_TEXT_RESULT_DESIGN_V1",
    "docs/WESLR_CONTROLLED_REPLY_TEXT_RESULT_ARTIFACT_V1.md",
    "weslr/controlled_reply_text.py",
    "build_controlled_reply_text_artifact_v1",
    "validate_controlled_reply_text_artifact_v1",
    "summarize_controlled_reply_text_artifact_v1",
    "render_controlled_reply_text_artifact_markdown_v1",
    "to_controlled_reply_text_artifact_json_safe_v1",
    "design-only",
    "internal result artifact design",
    "controlled reply-text metadata",
    "validation-before-result-writing",
    "Safe Markdown",
    "JSON-safe",
    "denied authority fields",
    "Blocked / Invalid Result Behavior",
    "No-Reply-Text-Execution Boundary",
    "No-Sendable-Reply-Text Boundary",
    "No-Actual-Reply-Body Boundary",
    "No-Final-Answer-Prose Boundary",
    "No-Answer-Draft Boundary",
    "No-User-Facing-Output-Execution Boundary",
    "No-Live-Dialogue Boundary",
    "No-Runtime Boundary",
    "No-ChatResponder / respond_chat / generate_chat Boundary",
    "No-Provider / Search / Advisor / Model Boundary",
    "No-.weslr / No-Feature-Flag Boundary",
    "No-Judges / Scores Boundary",
    "No-Official-Claims Boundary",
    "Visible Risks",
    "Abort Conditions",
    "Future Implementation / Review Sequence",
    "no_result_artifact_created",
    "no_reply_text_execution",
    "no_sendable_reply_text_created",
    "no_actual_reply_body_created",
    "no_authority_granted",
}


_controlled_reply_text_helpers_implementation_review_doc = "docs/WESLR_CONTROLLED_REPLY_TEXT_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
_controlled_reply_text_helpers_implementation_review_required_markers = {
    "WESLR Controlled Reply Text Helpers Implementation Review V1",
    "controlled_reply_text_helpers_implementation_valid_ready_for_context_alignment",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_REPLY_TEXT_HELPERS_IMPLEMENTATION_V1",
    "weslr/controlled_reply_text.py",
    "weslr/tests/test_controlled_reply_text_v1.py",
    "build_controlled_reply_text_artifact_v1",
    "validate_controlled_reply_text_artifact_v1",
    "summarize_controlled_reply_text_artifact_v1",
    "render_controlled_reply_text_artifact_markdown_v1",
    "to_controlled_reply_text_artifact_json_safe_v1",
    "controlled_reply_text_artifact_v1",
    "controlled_reply_text_artifact_schema_v1",
    "helper-only",
    "metadata-only",
    "internal-only",
    "deterministic",
    "pure in-memory",
    "validation-before-rendering",
    "JSON-safe",
    "no-authority",
    "no-runtime",
    "non-user-facing",
    "no side effects",
    "no sendable reply text",
    "no actual reply body",
    "no final-answer prose",
    "no answer drafts",
    "no live dialogue",
    "no runtime wiring",
    "No writer/save API is exposed",
    "All required denied authority fields are present",
    "Invalid or unsafe input is blocked safely",
    "weslr/chat_responder.py` remains untouched",
    "Validation status: PASS",
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

_controlled_local_chatresponder_shadow_observation_design_doc = "docs/WESLR_CONTROLLED_LOCAL_CHATRESPONDER_SHADOW_OBSERVATION_V1.md"
_controlled_local_chatresponder_shadow_observation_required_markers = {
    "WESLR_CONTROLLED_LOCAL_CHATRESPONDER_SHADOW_OBSERVATION_V1",
    "Controlled local ChatResponder shadow observation design only",
    "No runtime change in this task",
    "No prompt execution in this task",
    "No ChatResponder calls in this task",
    "No broad live ChatResponder testing",
    "Shadow-only",
    "No user-facing runtime change",
    "No external model calls",
    "No advisor calls",
    "No web/search execution",
    "No write paths",
    "No .weslr state",
    "No raw prompt storage",
    "No raw response storage",
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

_controlled_local_chatresponder_shadow_execution_design_doc = "docs/WESLR_CONTROLLED_LOCAL_CHATRESPONDER_SHADOW_EXECUTION_V1.md"
_controlled_local_chatresponder_shadow_execution_required_markers = {
    "WESLR_CONTROLLED_LOCAL_CHATRESPONDER_SHADOW_EXECUTION_V1",
    "Controlled local ChatResponder shadow execution design only",
    "No runtime change in this task",
    "No prompt execution in this task",
    "No ChatResponder calls in this task",
    "No broad live ChatResponder testing",
    "Shadow-only",
    "No user-facing runtime change",
    "No external model calls",
    "No advisor calls",
    "No web/search execution",
    "No write paths",
    "No .weslr state",
    "No raw prompt storage",
    "No raw response storage",
    "No official benchmark claims",
    "No Turing-test claims",
    "No IQ claims",
    "No certification claims",
    "No numeric scoring",
    "Safe synthetic prompts only",
    "Preflight before every possible ChatResponder call",
    "Metadata-only capture",
    "Anti-drift rule",
    "Deterministic guardrails are allowed",
    "Deterministic answers are not core cognition",
}

_controlled_real_chatresponder_shadow_call_design_doc = "docs/WESLR_CONTROLLED_REAL_CHATRESPONDER_SHADOW_CALL_V1.md"
_controlled_real_chatresponder_shadow_call_required_markers = {
    "WESLR_CONTROLLED_REAL_CHATRESPONDER_SHADOW_CALL_V1",
    "Controlled real ChatResponder shadow call design only",
    "No runtime change in this task",
    "No prompt execution in this task",
    "No ChatResponder calls in this task",
    "Real ChatResponder call requires separate implementation approval",
    "Shadow-only",
    "No user-facing runtime change",
    "No broad live ChatResponder testing",
    "Safe synthetic prompts only",
    "One or very few low-risk prompt IDs only",
    "Preflight before every possible ChatResponder call",
    "Monkeypatch/stub/blocker contracts required",
    "Metadata-only capture",
    "No raw prompt storage",
    "No raw response storage",
    "No .weslr state",
    "No write paths",
    "No external model calls",
    "No advisor calls",
    "No web/search execution",
    "No numeric scoring",
    "No official benchmark claims",
    "No Turing-test claims",
    "No IQ claims",
    "No certification claims",
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

_controlled_safe_non_model_observation_lane_v2_design_doc = "docs/WESLR_DESIGN_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_LANE_V2.md"
_controlled_safe_non_model_observation_lane_v2_design_required_markers = {
    "DESIGN_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_LANE_V2",
    "WESLR_CANON_ALIGNMENT",
    "design only",
    "ordinary_task_behavior_001",
    "conduct_alignment_003",
    "memory_honesty_001",
    "safe_keyword_branch",
    "requires_generate_chat_mock",
    "blocked_by_boundary",
    "lane_v2_design_ready",
    "RUN_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_LANE_V2_REPORT",
}

_mocked_observation_to_live_slice_governance_design_doc = "docs/WESLR_DESIGN_TRANSITION_FROM_MOCKED_OBSERVATION_TO_LIVE_SLICE_GOVERNANCE_V1.md"
_mocked_observation_to_live_slice_governance_required_markers = {
    "DESIGN_TRANSITION_FROM_MOCKED_OBSERVATION_TO_LIVE_SLICE_GOVERNANCE_V1",
    "WESLR_CANON_ALIGNMENT",
    "design only",
    "mocked_observation_clean_but_limited",
    "live_slice_governance_design_ready",
    "deterministic_live_slice_candidate_only",
    "live_model_slice_not_authorized",
    "DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_PREIMPLEMENTATION_PLAN_V1",
    "disabled by default",
    "No benchmark, Turing, IQ, certification, or product-readiness claim",
}

_first_deterministic_safe_live_slice_preimplementation_plan_doc = "docs/WESLR_DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_PREIMPLEMENTATION_PLAN_V1.md"
_first_deterministic_safe_live_slice_preimplementation_plan_required_markers = {
    "DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_PREIMPLEMENTATION_PLAN_V1",
    "WESLR_CANON_ALIGNMENT",
    "design only",
    "ordinary_task_behavior_001",
    "safe_keyword_branch",
    "WESLR_ENABLE_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_V1=1",
    "preimplementation_plan_ready",
    "deterministic_safe_live_slice_candidate_only",
    "live_model_slice_not_authorized",
    "needs_operator_review",
    "hold_before_live_slice",
    "REVIEW_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_PREIMPLEMENTATION_PLAN_NO_IMPLEMENTATION",
    "IMPLEMENT_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_GUARDS_V1",
}

_first_deterministic_safe_live_slice_implementation_guards_design_doc = "docs/WESLR_DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_IMPLEMENTATION_GUARDS_V1.md"
_first_deterministic_safe_live_slice_implementation_guards_required_markers = {
    "DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_IMPLEMENTATION_GUARDS_V1",
    "WESLR_CANON_ALIGNMENT",
    "design only",
    "ordinary_task_behavior_001",
    "safe_keyword_branch",
    "WESLR_ENABLE_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_V1=1",
    "implementation_guards_design_ready",
    "deterministic_safe_live_slice_guard_candidate_only",
    "implementation_not_authorized_yet",
    "live_model_slice_not_authorized",
    "needs_operator_review",
    "hold_before_implementation",
    "REVIEW_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_IMPLEMENTATION_GUARDS_DESIGN_NO_IMPLEMENTATION",
}

_first_deterministic_safe_live_slice_dry_run_plan_doc = "docs/WESLR_DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_DRY_RUN_PLAN_V1.md"
_first_deterministic_safe_live_slice_dry_run_plan_required_markers = {
    "DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_DRY_RUN_PLAN_V1",
    "WESLR_CANON_ALIGNMENT",
    "design only",
    "ordinary_task_behavior_001",
    "safe_keyword_branch",
    "WESLR_ENABLE_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_V1=1",
    "guard_report_clean_but_not_live",
    "dry_run_plan_ready",
    "dry_run_clean_but_not_live",
    "no runtime wiring",
    "no live slice execution",
    "no feature flag enablement",
    "metadata-only",
    "REVIEW_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_DRY_RUN_PLAN_NO_IMPLEMENTATION",
    "RUN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_DRY_RUN_REPORT_V1",
}

_weslr_working_root_context_doc = "WESLR_WORKING_ROOT.md"
_weslr_working_root_context_required_markers = {
    "Correct WESLR Repository",
    "Latest recorded design checkpoint",
    "6548cda",
    "WESLR: design mocked observation to live slice governance",
    "lane_v2_clean_but_limited",
    "live model-backed slices remain unauthorized",
    "DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_PREIMPLEMENTATION_PLAN_V1",
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


def _cognition_target_model_doc_is_valid():
    return _doc_with_markers_is_valid(_cognition_target_model_doc, _cognition_target_model_required_markers)


def _ranked_state_grounded_response_formation_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_state_grounded_response_formation_doc,
        _ranked_state_grounded_response_formation_required_markers,
    )


def _ranked_state_grounded_response_shadow_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_state_grounded_response_shadow_helpers_review_doc,
        _ranked_state_grounded_response_shadow_helpers_review_required_markers,
    )


def _ranked_response_shadow_evaluation_scenarios_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_response_shadow_evaluation_scenarios_doc,
        _ranked_response_shadow_evaluation_scenarios_required_markers,
    )


def _ranked_response_shadow_evaluation_scenarios_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_response_shadow_evaluation_scenarios_review_doc,
        _ranked_response_shadow_evaluation_scenarios_review_required_markers,
    )


def _ranked_response_shadow_evaluation_report_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_response_shadow_evaluation_report_design_doc,
        _ranked_response_shadow_evaluation_report_design_required_markers,
    )


def _ranked_response_shadow_evaluation_report_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_response_shadow_evaluation_report_helpers_review_doc,
        _ranked_response_shadow_evaluation_report_helpers_review_required_markers,
    )


def _ranked_response_shadow_evaluation_report_run_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_response_shadow_evaluation_report_run_design_doc,
        _ranked_response_shadow_evaluation_report_run_design_required_markers,
    )


def _ranked_response_shadow_evaluation_report_run_result_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_response_shadow_evaluation_report_run_result_doc,
        _ranked_response_shadow_evaluation_report_run_result_required_markers,
    )


def _ranked_response_shadow_evaluation_report_run_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_response_shadow_evaluation_report_run_review_doc,
        _ranked_response_shadow_evaluation_report_run_review_required_markers,
    )


def _ranked_response_shadow_helper_interop_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_response_shadow_helper_interop_boundary_doc,
        _ranked_response_shadow_helper_interop_boundary_required_markers,
    )


def _ranked_response_shadow_helper_interop_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_response_shadow_helper_interop_boundary_review_doc,
        _ranked_response_shadow_helper_interop_boundary_review_required_markers,
    )


def _ranked_response_shadow_native_dry_slice_interop_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_response_shadow_native_dry_slice_interop_doc,
        _ranked_response_shadow_native_dry_slice_interop_required_markers,
    )


def _ranked_response_shadow_native_dry_slice_interop_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_response_shadow_native_dry_slice_interop_review_doc,
        _ranked_response_shadow_native_dry_slice_interop_review_required_markers,
    )


def _ranked_native_interop_shadow_artifact_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_interop_shadow_artifact_helpers_doc,
        _ranked_native_interop_shadow_artifact_helpers_required_markers,
    )


def _ranked_native_interop_shadow_artifact_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_interop_shadow_artifact_helpers_review_doc,
        _ranked_native_interop_shadow_artifact_helpers_review_required_markers,
    )


def _ranked_native_interop_shadow_artifact_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_interop_shadow_artifact_helpers_implementation_review_doc,
        _ranked_native_interop_shadow_artifact_helpers_implementation_review_required_markers,
    )


def _ranked_native_interop_shadow_artifact_report_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_interop_shadow_artifact_report_doc,
        _ranked_native_interop_shadow_artifact_report_required_markers,
    )


def _ranked_native_interop_shadow_artifact_report_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_interop_shadow_artifact_report_review_doc,
        _ranked_native_interop_shadow_artifact_report_review_required_markers,
    )


def _ranked_native_interop_shadow_artifact_report_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_interop_shadow_artifact_report_helpers_implementation_review_doc,
        _ranked_native_interop_shadow_artifact_report_helpers_implementation_review_required_markers,
    )


def _ranked_native_interop_shadow_artifact_report_run_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_interop_shadow_artifact_report_run_doc,
        _ranked_native_interop_shadow_artifact_report_run_required_markers,
    )


def _ranked_native_interop_shadow_artifact_report_run_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_interop_shadow_artifact_report_run_review_doc,
        _ranked_native_interop_shadow_artifact_report_run_review_required_markers,
    )


def _ranked_native_interop_shadow_artifact_report_run_result_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_interop_shadow_artifact_report_run_result_doc,
        _ranked_native_interop_shadow_artifact_report_run_result_required_markers,
    )


def _ranked_native_interop_shadow_artifact_report_run_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_interop_shadow_artifact_report_run_implementation_review_doc,
        _ranked_native_interop_shadow_artifact_report_run_implementation_review_required_markers,
    )


def _ranked_native_to_internal_turing_readiness_bridge_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_to_internal_turing_readiness_bridge_doc,
        _ranked_native_to_internal_turing_readiness_bridge_required_markers,
    )

def _ranked_native_to_internal_turing_readiness_bridge_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _ranked_native_to_internal_turing_readiness_bridge_review_doc,
        _ranked_native_to_internal_turing_readiness_bridge_review_required_markers,
    )

def _internal_turing_style_readiness_dimensions_and_corpus_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_style_readiness_dimensions_and_corpus_doc,
        _internal_turing_style_readiness_dimensions_and_corpus_required_markers,
    )


def _internal_turing_style_readiness_dimensions_and_corpus_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_style_readiness_dimensions_and_corpus_review_doc,
        _internal_turing_style_readiness_dimensions_and_corpus_review_required_markers,
    )


def _internal_turing_scenario_corpus_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_scenario_corpus_helpers_doc,
        _internal_turing_scenario_corpus_helpers_required_markers,
    )


def _internal_turing_scenario_corpus_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_scenario_corpus_helpers_review_doc,
        _internal_turing_scenario_corpus_helpers_review_required_markers,
    )


def _internal_turing_scenario_corpus_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_scenario_corpus_helpers_implementation_review_doc,
        _internal_turing_scenario_corpus_helpers_implementation_review_required_markers,
    )


def _internal_turing_multi_turn_evaluation_protocol_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_multi_turn_evaluation_protocol_doc,
        _internal_turing_multi_turn_evaluation_protocol_required_markers,
    )


def _internal_turing_multi_turn_evaluation_protocol_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_multi_turn_evaluation_protocol_review_doc,
        _internal_turing_multi_turn_evaluation_protocol_review_required_markers,
    )


def _internal_turing_multi_turn_protocol_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_multi_turn_protocol_helpers_doc,
        _internal_turing_multi_turn_protocol_helpers_required_markers,
    )


def _internal_turing_multi_turn_protocol_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_multi_turn_protocol_helpers_review_doc,
        _internal_turing_multi_turn_protocol_helpers_review_required_markers,
    )


def _internal_turing_multi_turn_protocol_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_multi_turn_protocol_helpers_implementation_review_doc,
        _internal_turing_multi_turn_protocol_helpers_implementation_review_required_markers,
    )


def _internal_turing_to_answer_authority_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_to_answer_authority_boundary_doc,
        _internal_turing_to_answer_authority_boundary_required_markers,
    )

def _internal_turing_to_answer_authority_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _internal_turing_to_answer_authority_boundary_review_doc,
        _internal_turing_to_answer_authority_boundary_review_required_markers,
    )

def _answer_authority_boundary_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_authority_boundary_helpers_doc,
        _answer_authority_boundary_helpers_required_markers,
    )

def _answer_authority_boundary_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_authority_boundary_helpers_review_doc,
        _answer_authority_boundary_helpers_review_required_markers,
    )

def _answer_authority_boundary_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_authority_boundary_helpers_implementation_review_doc,
        _answer_authority_boundary_helpers_implementation_review_required_markers,
    )

def _answer_composition_authority_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_boundary_doc,
        _answer_composition_authority_boundary_required_markers,
    )

def _answer_composition_authority_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_boundary_review_doc,
        _answer_composition_authority_boundary_review_required_markers,
    )

def _answer_composition_authority_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_helpers_doc,
        _answer_composition_authority_helpers_required_markers,
    )

def _answer_composition_authority_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_helpers_review_doc,
        _answer_composition_authority_helpers_review_required_markers,
    )

def _answer_composition_authority_helpers_implementation_plan_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_helpers_implementation_plan_doc,
        _answer_composition_authority_helpers_implementation_plan_required_markers,
    )

def _answer_composition_authority_helpers_implementation_plan_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_helpers_implementation_plan_review_doc,
        _answer_composition_authority_helpers_implementation_plan_review_required_markers,
    )

def _answer_composition_authority_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_helpers_implementation_review_doc,
        _answer_composition_authority_helpers_implementation_review_required_markers,
    )

def _answer_composition_authority_report_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_report_helpers_doc,
        _answer_composition_authority_report_helpers_required_markers,
    )

def _answer_composition_authority_report_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_report_helpers_review_doc,
        _answer_composition_authority_report_helpers_review_required_markers,
    )

def _answer_composition_authority_report_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_report_helpers_implementation_review_doc,
        _answer_composition_authority_report_helpers_implementation_review_required_markers,
    )

def _answer_composition_authority_report_run_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_report_run_design_doc,
        _answer_composition_authority_report_run_design_required_markers,
    )

def _answer_composition_authority_report_run_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_report_run_review_doc,
        _answer_composition_authority_report_run_review_required_markers,
    )

def _answer_composition_authority_report_run_result_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_report_run_result_doc,
        _answer_composition_authority_report_run_result_required_markers,
    )

def _answer_composition_authority_report_run_result_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_composition_authority_report_run_result_review_doc,
        _answer_composition_authority_report_run_result_review_required_markers,
    )

def _controlled_answer_composition_dry_run_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_boundary_doc,
        _controlled_answer_composition_dry_run_boundary_required_markers,
    )

def _controlled_answer_composition_dry_run_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_boundary_review_doc,
        _controlled_answer_composition_dry_run_boundary_review_required_markers,
    )

def _controlled_answer_composition_dry_run_helpers_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_helpers_design_doc,
        _controlled_answer_composition_dry_run_helpers_design_required_markers,
    )

def _controlled_answer_composition_dry_run_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_helpers_review_doc,
        _controlled_answer_composition_dry_run_helpers_review_required_markers,
    )

def _controlled_answer_composition_dry_run_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_helpers_implementation_review_doc,
        _controlled_answer_composition_dry_run_helpers_implementation_review_required_markers,
    )

def _controlled_answer_composition_dry_run_result_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_result_design_doc,
        _controlled_answer_composition_dry_run_result_design_required_markers,
    )

def _controlled_answer_composition_dry_run_result_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_result_review_doc,
        _controlled_answer_composition_dry_run_result_review_required_markers,
    )

def _controlled_answer_composition_dry_run_result_test_fix_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_result_test_fix_review_doc,
        _controlled_answer_composition_dry_run_result_test_fix_review_required_markers,
    )

def _controlled_answer_composition_dry_run_execution_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_execution_design_doc,
        _controlled_answer_composition_dry_run_execution_design_required_markers,
    )

def _controlled_answer_composition_dry_run_execution_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_execution_review_doc,
        _controlled_answer_composition_dry_run_execution_review_required_markers,
    )

def _controlled_answer_composition_dry_run_result_artifact_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_result_artifact_doc,
        _controlled_answer_composition_dry_run_result_artifact_required_markers,
    )

def _controlled_answer_composition_dry_run_execution_result_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_execution_result_review_doc,
        _controlled_answer_composition_dry_run_execution_result_review_required_markers,
    )

def _controlled_answer_composition_dry_run_to_answer_formation_bridge_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_to_answer_formation_bridge_doc,
        _controlled_answer_composition_dry_run_to_answer_formation_bridge_required_markers,
    )

def _controlled_answer_composition_dry_run_to_answer_formation_bridge_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_dry_run_to_answer_formation_bridge_review_doc,
        _controlled_answer_composition_dry_run_to_answer_formation_bridge_review_required_markers,
    )

def _answer_formation_helpers_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_helpers_design_doc,
        _answer_formation_helpers_design_required_markers,
    )

def _answer_formation_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_helpers_review_doc,
        _answer_formation_helpers_review_required_markers,
    )

def _answer_formation_helpers_implementation_plan_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_helpers_implementation_plan_doc,
        _answer_formation_helpers_implementation_plan_required_markers,
    )

def _answer_formation_helpers_implementation_plan_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_helpers_implementation_plan_review_doc,
        _answer_formation_helpers_implementation_plan_review_required_markers,
    )

def _answer_formation_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_helpers_implementation_review_doc,
        _answer_formation_helpers_implementation_review_required_markers,
    )

def _answer_formation_report_helpers_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_report_helpers_design_doc,
        _answer_formation_report_helpers_design_required_markers,
    )

def _answer_formation_report_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_report_helpers_review_doc,
        _answer_formation_report_helpers_review_required_markers,
    )

def _answer_formation_report_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_report_helpers_implementation_review_doc,
        _answer_formation_report_helpers_implementation_review_required_markers,
    )

def _answer_formation_report_run_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_report_run_design_doc,
        _answer_formation_report_run_design_required_markers,
    )

def _answer_formation_report_run_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_report_run_review_doc,
        _answer_formation_report_run_review_required_markers,
    )

def _answer_formation_report_run_result_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_report_run_result_doc,
        _answer_formation_report_run_result_required_markers,
    )

def _answer_formation_report_run_result_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_report_run_result_review_doc,
        _answer_formation_report_run_result_review_required_markers,
    )

def _answer_formation_dry_run_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_dry_run_boundary_doc,
        _answer_formation_dry_run_boundary_required_markers,
    )

def _answer_formation_dry_run_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_dry_run_boundary_review_doc,
        _answer_formation_dry_run_boundary_review_required_markers,
    )

def _answer_formation_dry_run_helpers_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_dry_run_helpers_design_doc,
        _answer_formation_dry_run_helpers_design_required_markers,
    )

def _answer_formation_dry_run_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_dry_run_helpers_review_doc,
        _answer_formation_dry_run_helpers_review_required_markers,
    )

def _answer_formation_dry_run_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_dry_run_helpers_implementation_review_doc,
        _answer_formation_dry_run_helpers_implementation_review_required_markers,
    )

def _answer_formation_dry_run_execution_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_dry_run_execution_design_doc,
        _answer_formation_dry_run_execution_design_required_markers,
    )

def _answer_formation_dry_run_execution_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_dry_run_execution_review_doc,
        _answer_formation_dry_run_execution_review_required_markers,
    )

def _answer_formation_dry_run_result_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_dry_run_result_doc,
        _answer_formation_dry_run_result_required_markers,
    )

def _answer_formation_dry_run_execution_result_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _answer_formation_dry_run_execution_result_review_doc,
        _answer_formation_dry_run_execution_result_review_required_markers,
    )

def _controlled_answer_formation_execution_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_formation_execution_boundary_doc,
        _controlled_answer_formation_execution_boundary_required_markers,
    )

def _controlled_answer_formation_execution_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_formation_execution_boundary_review_doc,
        _controlled_answer_formation_execution_boundary_review_required_markers,
    )

def _controlled_answer_formation_execution_helpers_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_formation_execution_helpers_design_doc,
        _controlled_answer_formation_execution_helpers_design_required_markers,
    )

def _controlled_answer_formation_execution_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_formation_execution_helpers_review_doc,
        _controlled_answer_formation_execution_helpers_review_required_markers,
    )

def _controlled_answer_formation_execution_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_formation_execution_helpers_implementation_review_doc,
        _controlled_answer_formation_execution_helpers_implementation_review_required_markers,
    )

def _controlled_answer_formation_execution_result_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_formation_execution_result_design_doc,
        _controlled_answer_formation_execution_result_design_required_markers,
    )

def _controlled_answer_formation_execution_result_design_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_formation_execution_result_design_review_doc,
        _controlled_answer_formation_execution_result_design_review_required_markers,
    )

def _controlled_answer_formation_execution_result_artifact_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_formation_execution_result_artifact_doc,
        _controlled_answer_formation_execution_result_artifact_required_markers,
    )

def _controlled_answer_formation_execution_result_artifact_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_formation_execution_result_artifact_review_doc,
        _controlled_answer_formation_execution_result_artifact_review_required_markers,
    )

def _controlled_answer_formation_chain_next_step_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_formation_chain_next_step_review_doc,
        _controlled_answer_formation_chain_next_step_review_required_markers,
    )

def _controlled_answer_composition_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_boundary_doc,
        _controlled_answer_composition_boundary_required_markers,
    )

def _controlled_answer_composition_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_boundary_review_doc,
        _controlled_answer_composition_boundary_review_required_markers,
    )

def _controlled_answer_composition_helpers_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_helpers_design_doc,
        _controlled_answer_composition_helpers_design_required_markers,
    )

def _controlled_answer_composition_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_helpers_review_doc,
        _controlled_answer_composition_helpers_review_required_markers,
    )


def _controlled_answer_composition_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_helpers_implementation_review_doc,
        _controlled_answer_composition_helpers_implementation_review_required_markers,
    )


def _controlled_answer_composition_result_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_result_design_doc,
        _controlled_answer_composition_result_design_required_markers,
    )


def _controlled_answer_composition_result_design_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_result_design_review_doc,
        _controlled_answer_composition_result_design_review_required_markers,
    )


def _controlled_answer_composition_result_artifact_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_result_artifact_doc,
        _controlled_answer_composition_result_artifact_required_markers,
    )


def _controlled_answer_composition_result_artifact_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_result_artifact_review_doc,
        _controlled_answer_composition_result_artifact_review_required_markers,
    )


def _controlled_answer_composition_chain_next_step_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_answer_composition_chain_next_step_review_doc,
        _controlled_answer_composition_chain_next_step_review_required_markers,
    )


def _controlled_final_answer_generation_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_final_answer_generation_boundary_doc,
        _controlled_final_answer_generation_boundary_required_markers,
    )


def _controlled_final_answer_generation_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_final_answer_generation_boundary_review_doc,
        _controlled_final_answer_generation_boundary_review_required_markers,
    )


def _controlled_final_answer_generation_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_final_answer_generation_helpers_doc,
        _controlled_final_answer_generation_helpers_required_markers,
    )


def _controlled_final_answer_generation_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_final_answer_generation_helpers_review_doc,
        _controlled_final_answer_generation_helpers_review_required_markers,
    )


def _controlled_final_answer_generation_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_final_answer_generation_helpers_implementation_review_doc,
        _controlled_final_answer_generation_helpers_implementation_review_required_markers,
    )


def _controlled_final_answer_generation_result_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_final_answer_generation_result_design_doc,
        _controlled_final_answer_generation_result_design_required_markers,
    )


def _controlled_final_answer_generation_result_design_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_final_answer_generation_result_design_review_doc,
        _controlled_final_answer_generation_result_design_review_required_markers,
    )


def _controlled_final_answer_generation_result_artifact_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_final_answer_generation_result_artifact_doc,
        _controlled_final_answer_generation_result_artifact_required_markers,
    )


def _controlled_final_answer_generation_result_artifact_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_final_answer_generation_result_artifact_review_doc,
        _controlled_final_answer_generation_result_artifact_review_required_markers,
    )


def _controlled_final_answer_generation_chain_next_step_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_final_answer_generation_chain_next_step_review_doc,
        _controlled_final_answer_generation_chain_next_step_review_required_markers,
    )


def _controlled_user_facing_output_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_user_facing_output_boundary_doc,
        _controlled_user_facing_output_boundary_required_markers,
    )


def _controlled_user_facing_output_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_user_facing_output_boundary_review_doc,
        _controlled_user_facing_output_boundary_review_required_markers,
    )


def _controlled_user_facing_output_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_user_facing_output_helpers_doc,
        _controlled_user_facing_output_helpers_required_markers,
    )


def _controlled_user_facing_output_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_user_facing_output_helpers_review_doc,
        _controlled_user_facing_output_helpers_review_required_markers,
    )


def _controlled_user_facing_output_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_user_facing_output_helpers_implementation_review_doc,
        _controlled_user_facing_output_helpers_implementation_review_required_markers,
    )


def _controlled_user_facing_output_result_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_user_facing_output_result_design_doc,
        _controlled_user_facing_output_result_design_required_markers,
    )

def _controlled_user_facing_output_result_design_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_user_facing_output_result_design_review_doc,
        _controlled_user_facing_output_result_design_review_required_markers,
    )

def _controlled_user_facing_output_result_artifact_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_user_facing_output_result_artifact_doc,
        _controlled_user_facing_output_result_artifact_required_markers,
    )

def _controlled_user_facing_output_result_artifact_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_user_facing_output_result_artifact_review_doc,
        _controlled_user_facing_output_result_artifact_review_required_markers,
    )


def _controlled_user_facing_output_chain_next_step_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_user_facing_output_chain_next_step_review_doc,
        _controlled_user_facing_output_chain_next_step_review_required_markers,
    )


def _controlled_reply_preview_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_preview_helpers_doc,
        _controlled_reply_preview_helpers_required_markers,
    )


def _controlled_reply_preview_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_preview_helpers_review_doc,
        _controlled_reply_preview_helpers_review_required_markers,
    )


def _controlled_reply_preview_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_preview_helpers_implementation_review_doc,
        _controlled_reply_preview_helpers_implementation_review_required_markers,
    )


def _controlled_reply_preview_result_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_preview_result_design_doc,
        _controlled_reply_preview_result_design_required_markers,
    )


def _controlled_reply_preview_result_design_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_preview_result_design_review_doc,
        _controlled_reply_preview_result_design_review_required_markers,
    )


def _controlled_reply_preview_result_artifact_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_preview_result_artifact_doc,
        _controlled_reply_preview_result_artifact_required_markers,
    )


def _controlled_reply_preview_result_artifact_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_preview_result_artifact_review_doc,
        _controlled_reply_preview_result_artifact_review_required_markers,
    )


def _controlled_reply_preview_chain_next_step_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_preview_chain_next_step_review_doc,
        _controlled_reply_preview_chain_next_step_review_required_markers,
    )


def _controlled_reply_output_precondition_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_output_precondition_boundary_doc,
        _controlled_reply_output_precondition_boundary_required_markers,
    )


def _controlled_reply_output_precondition_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_output_precondition_boundary_review_doc,
        _controlled_reply_output_precondition_boundary_review_required_markers,
    )


def _controlled_reply_output_precondition_chain_next_step_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_output_precondition_chain_next_step_review_doc,
        _controlled_reply_output_precondition_chain_next_step_review_required_markers,
    )


def _unknown_engine_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_boundary_doc,
        _unknown_engine_boundary_required_markers,
    )


def _unknown_engine_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_boundary_review_doc,
        _unknown_engine_boundary_review_required_markers,
    )


def _cognitive_gym_suite_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_suite_boundary_doc,
        _cognitive_gym_suite_boundary_required_markers,
    )


def _cognitive_gym_suite_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_suite_boundary_review_doc,
        _cognitive_gym_suite_boundary_review_required_markers,
    )


def _cognitive_gym_run_protocol_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_run_protocol_doc,
        _cognitive_gym_run_protocol_required_markers,
    )


def _cognitive_gym_run_protocol_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_run_protocol_review_doc,
        _cognitive_gym_run_protocol_review_required_markers,
    )


def _cognitive_gym_run_protocol_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_run_protocol_helpers_implementation_review_doc,
        _cognitive_gym_run_protocol_helpers_implementation_review_required_markers,
    )


def _unknown_engine_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_helpers_doc,
        _unknown_engine_helpers_required_markers,
    )


def _unknown_engine_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_helpers_review_doc,
        _unknown_engine_helpers_review_required_markers,
    )


def _unknown_engine_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_helpers_implementation_review_doc,
        _unknown_engine_helpers_implementation_review_required_markers,
    )


def _unknown_engine_helpers_validation_fix_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_helpers_validation_fix_review_doc,
        _unknown_engine_helpers_validation_fix_review_required_markers,
    )


def _unknown_engine_result_artifact_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_result_artifact_boundary_doc,
        _unknown_engine_result_artifact_boundary_required_markers,
    )


def _unknown_engine_result_artifact_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_result_artifact_boundary_review_doc,
        _unknown_engine_result_artifact_boundary_review_required_markers,
    )


def _unknown_engine_result_artifact_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_result_artifact_helpers_doc,
        _unknown_engine_result_artifact_helpers_required_markers,
    )


def _unknown_engine_result_artifact_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_result_artifact_helpers_review_doc,
        _unknown_engine_result_artifact_helpers_review_required_markers,
    )


def _unknown_engine_result_artifact_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_result_artifact_helpers_implementation_review_doc,
        _unknown_engine_result_artifact_helpers_implementation_review_required_markers,
    )


def _unknown_engine_result_artifact_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_result_artifact_doc,
        _unknown_engine_result_artifact_required_markers,
    )


def _unknown_engine_result_artifact_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _unknown_engine_result_artifact_review_doc,
        _unknown_engine_result_artifact_review_required_markers,
    )


def _cognitive_gym_erdos_challenge_track_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_erdos_challenge_track_doc,
        _cognitive_gym_erdos_challenge_track_required_markers,
    )


def _cognitive_gym_erdos_challenge_track_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_erdos_challenge_track_review_doc,
        _cognitive_gym_erdos_challenge_track_review_required_markers,
    )


def _cognitive_gym_erdos_challenge_track_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_erdos_challenge_track_helpers_implementation_review_doc,
        _cognitive_gym_erdos_challenge_track_helpers_implementation_review_required_markers,
    )


def _cognitive_gym_erdos_case_corpus_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_erdos_case_corpus_boundary_doc,
        _cognitive_gym_erdos_case_corpus_boundary_required_markers,
    )


def _cognitive_gym_erdos_case_corpus_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_erdos_case_corpus_boundary_review_doc,
        _cognitive_gym_erdos_case_corpus_boundary_review_required_markers,
    )


def _cognitive_gym_exploratory_case_protocol_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_exploratory_case_protocol_review_doc,
        _cognitive_gym_exploratory_case_protocol_review_required_markers,
    )


def _cognitive_gym_exploratory_case_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_exploratory_case_helpers_doc,
        _cognitive_gym_exploratory_case_helpers_required_markers,
    )


def _cognitive_gym_exploratory_case_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_exploratory_case_helpers_review_doc,
        _cognitive_gym_exploratory_case_helpers_review_required_markers,
    )


def _cognitive_gym_exploratory_case_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _cognitive_gym_exploratory_case_helpers_implementation_review_doc,
        _cognitive_gym_exploratory_case_helpers_implementation_review_required_markers,
    )


def _first_engine_specific_exploratory_helper_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _first_engine_specific_exploratory_helper_boundary_doc,
        _first_engine_specific_exploratory_helper_boundary_required_markers,
    )


def _first_engine_specific_exploratory_helper_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _first_engine_specific_exploratory_helper_boundary_review_doc,
        _first_engine_specific_exploratory_helper_boundary_review_required_markers,
    )


def _calibration_ledger_exploratory_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _calibration_ledger_exploratory_helpers_doc,
        _calibration_ledger_exploratory_helpers_required_markers,
    )


def _calibration_ledger_exploratory_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _calibration_ledger_exploratory_helpers_review_doc,
        _calibration_ledger_exploratory_helpers_review_required_markers,
    )


def _controlled_reply_preview_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_preview_boundary_review_doc,
        _controlled_reply_preview_boundary_review_required_markers,
    )


def _controlled_reply_preview_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_preview_boundary_doc,
        _controlled_reply_preview_boundary_required_markers,
    )


def _controlled_reply_text_chain_next_step_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_text_chain_next_step_review_doc,
        _controlled_reply_text_chain_next_step_review_required_markers,
    )


def _controlled_reply_text_boundary_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_text_boundary_doc,
        _controlled_reply_text_boundary_required_markers,
    )


def _controlled_reply_text_boundary_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_text_boundary_review_doc,
        _controlled_reply_text_boundary_review_required_markers,
    )



def _controlled_reply_text_helpers_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_text_helpers_doc,
        _controlled_reply_text_helpers_required_markers,
    )


def _controlled_reply_text_helpers_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_text_helpers_review_doc,
        _controlled_reply_text_helpers_review_required_markers,
    )

def _controlled_reply_text_result_design_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_text_result_design_review_doc,
        _controlled_reply_text_result_design_review_required_markers,
    )


def _controlled_reply_text_result_artifact_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_text_result_artifact_review_doc,
        _controlled_reply_text_result_artifact_review_required_markers,
    )


def _controlled_reply_text_result_artifact_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_text_result_artifact_doc,
        _controlled_reply_text_result_artifact_required_markers,
    )


def _controlled_reply_text_result_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_text_result_design_doc,
        _controlled_reply_text_result_design_required_markers,
    )


def _controlled_reply_text_helpers_implementation_review_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_reply_text_helpers_implementation_review_doc,
        _controlled_reply_text_helpers_implementation_review_required_markers,
    )


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


def _controlled_local_chatresponder_shadow_observation_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_local_chatresponder_shadow_observation_design_doc,
        _controlled_local_chatresponder_shadow_observation_required_markers,
    )


def _controlled_local_chatresponder_shadow_execution_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_local_chatresponder_shadow_execution_design_doc,
        _controlled_local_chatresponder_shadow_execution_required_markers,
    )


def _controlled_real_chatresponder_shadow_call_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_real_chatresponder_shadow_call_design_doc,
        _controlled_real_chatresponder_shadow_call_required_markers,
    )


def _occ_weslr_bootstrap_context_doc_is_valid(path):
    return path in _occ_weslr_bootstrap_context_docs and _doc_with_markers_is_valid(path, _occ_weslr_bootstrap_context_required_markers)


def _controlled_safe_non_model_observation_lane_v2_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _controlled_safe_non_model_observation_lane_v2_design_doc,
        _controlled_safe_non_model_observation_lane_v2_design_required_markers,
    )


def _mocked_observation_to_live_slice_governance_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _mocked_observation_to_live_slice_governance_design_doc,
        _mocked_observation_to_live_slice_governance_required_markers,
    )


def _first_deterministic_safe_live_slice_preimplementation_plan_doc_is_valid():
    return _doc_with_markers_is_valid(
        _first_deterministic_safe_live_slice_preimplementation_plan_doc,
        _first_deterministic_safe_live_slice_preimplementation_plan_required_markers,
    )


def _first_deterministic_safe_live_slice_implementation_guards_design_doc_is_valid():
    return _doc_with_markers_is_valid(
        _first_deterministic_safe_live_slice_implementation_guards_design_doc,
        _first_deterministic_safe_live_slice_implementation_guards_required_markers,
    )


def _first_deterministic_safe_live_slice_dry_run_plan_doc_is_valid():
    return _doc_with_markers_is_valid(
        _first_deterministic_safe_live_slice_dry_run_plan_doc,
        _first_deterministic_safe_live_slice_dry_run_plan_required_markers,
    )


def _weslr_working_root_context_doc_is_valid():
    return _doc_with_markers_is_valid(
        _weslr_working_root_context_doc,
        _weslr_working_root_context_required_markers,
    )


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
      - docs/WESLR_COGNITION_TARGET_MODEL_V1.md only when
        the approved cognition target model design markers are present
      - docs/WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1.md only when
        the approved ranked state-grounded response formation design markers are present
      - docs/WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_SHADOW_HELPERS_REVIEW_V1.md only when
        the approved ranked response shadow-helper review markers are present
      - docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_SCENARIOS_V1.md only when
        the approved ranked response shadow-evaluation scenario design markers are present
      - docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_SCENARIOS_REVIEW_V1.md only when
        the approved ranked response shadow-evaluation scenario review markers are present
      - docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_RUN_REVIEW_V1.md only when
        the approved ranked response shadow-evaluation report-run review markers are present
      - docs/WESLR_RANKED_RESPONSE_SHADOW_HELPER_INTEROP_BOUNDARY_V1.md only when
        the approved ranked response shadow-helper interop boundary design markers are present
      - docs/WESLR_RANKED_RESPONSE_SHADOW_HELPER_INTEROP_BOUNDARY_REVIEW_V1.md only when
        the approved ranked response shadow-helper interop boundary review markers are present
      - docs/WESLR_RANKED_RESPONSE_SHADOW_NATIVE_DRY_SLICE_INTEROP_V1.md only when
        the approved ranked response shadow/native dry-slice interop design markers are present
      - docs/WESLR_RANKED_RESPONSE_SHADOW_NATIVE_DRY_SLICE_INTEROP_REVIEW_V1.md only when
        the approved ranked response shadow/native dry-slice interop review markers are present
      - docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_HELPERS_V1.md only when
        the approved ranked/native interop shadow artifact helper design markers are present
      - docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_HELPERS_REVIEW_V1.md only when
        the approved ranked/native interop shadow artifact helper review markers are present
      - docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_HELPERS_IMPLEMENTATION_REVIEW_V1.md only when
        the approved ranked/native interop shadow artifact helper implementation review markers are present
      - docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_V1.md only when
        the approved ranked/native interop shadow artifact report design markers are present
      - docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_REVIEW_V1.md only when
        the approved ranked/native interop shadow artifact report review markers are present
      - docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_V1.md only when
        the approved ranked/native interop shadow artifact report-run design markers are present
      - docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_REVIEW_V1.md only when
        the approved ranked/native interop shadow artifact report-run review markers are present
      - docs/WESLR_INTERNAL_TURING_STYLE_READINESS_DIMENSIONS_AND_CORPUS_REVIEW_V1.md only when
        the approved internal Turing-style readiness dimensions and corpus review markers are present
      - docs/WESLR_INTERNAL_TURING_SCENARIO_CORPUS_HELPERS_V1.md only when
        the approved internal Turing scenario corpus helper design markers are present
      - docs/WESLR_INTERNAL_TURING_SCENARIO_CORPUS_HELPERS_REVIEW_V1.md only when
        the approved internal Turing scenario corpus helper review markers are present
      - docs/WESLR_INTERNAL_TURING_SCENARIO_CORPUS_HELPERS_IMPLEMENTATION_REVIEW_V1.md only when
        the approved internal Turing scenario corpus helper implementation review markers are present
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
      - docs/WESLR_CONTROLLED_LOCAL_CHATRESPONDER_SHADOW_OBSERVATION_V1.md only when
        the approved controlled local ChatResponder shadow observation design markers are present
      - docs/WESLR_CONTROLLED_LOCAL_CHATRESPONDER_SHADOW_EXECUTION_V1.md only when
        the approved controlled local ChatResponder shadow execution design markers are present
      - docs/WESLR_DESIGN_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_LANE_V2.md only when
        the approved controlled safe non-model observation lane V2 design markers are present
      - docs/WESLR_DESIGN_TRANSITION_FROM_MOCKED_OBSERVATION_TO_LIVE_SLICE_GOVERNANCE_V1.md only when
        the approved mocked-observation-to-live-slice governance design markers are present
      - docs/WESLR_DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_PREIMPLEMENTATION_PLAN_V1.md only when
        the approved first deterministic-safe live-slice preimplementation plan markers are present
      - docs/WESLR_DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_IMPLEMENTATION_GUARDS_V1.md only when
        the approved first deterministic-safe live-slice implementation guards design markers are present
      - docs/WESLR_DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_DRY_RUN_PLAN_V1.md only when
        the approved first deterministic-safe live-slice dry-run plan markers are present
      - WESLR_WORKING_ROOT.md only when the approved working-root context markers are present
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
    cognition_target_model_doc_valid = _cognition_target_model_doc_is_valid()
    ranked_state_grounded_response_formation_doc_valid = _ranked_state_grounded_response_formation_doc_is_valid()
    ranked_state_grounded_response_shadow_helpers_review_doc_valid = _ranked_state_grounded_response_shadow_helpers_review_doc_is_valid()
    ranked_response_shadow_evaluation_scenarios_doc_valid = _ranked_response_shadow_evaluation_scenarios_doc_is_valid()
    ranked_response_shadow_evaluation_scenarios_review_doc_valid = _ranked_response_shadow_evaluation_scenarios_review_doc_is_valid()
    ranked_response_shadow_evaluation_report_design_doc_valid = _ranked_response_shadow_evaluation_report_design_doc_is_valid()
    ranked_response_shadow_evaluation_report_helpers_review_doc_valid = _ranked_response_shadow_evaluation_report_helpers_review_doc_is_valid()
    ranked_response_shadow_evaluation_report_run_design_doc_valid = _ranked_response_shadow_evaluation_report_run_design_doc_is_valid()
    ranked_response_shadow_evaluation_report_run_result_doc_valid = _ranked_response_shadow_evaluation_report_run_result_doc_is_valid()
    ranked_response_shadow_evaluation_report_run_review_doc_valid = _ranked_response_shadow_evaluation_report_run_review_doc_is_valid()
    ranked_response_shadow_helper_interop_boundary_doc_valid = _ranked_response_shadow_helper_interop_boundary_doc_is_valid()
    ranked_response_shadow_helper_interop_boundary_review_doc_valid = _ranked_response_shadow_helper_interop_boundary_review_doc_is_valid()
    ranked_response_shadow_native_dry_slice_interop_doc_valid = _ranked_response_shadow_native_dry_slice_interop_doc_is_valid()
    ranked_response_shadow_native_dry_slice_interop_review_doc_valid = _ranked_response_shadow_native_dry_slice_interop_review_doc_is_valid()
    ranked_native_interop_shadow_artifact_helpers_doc_valid = _ranked_native_interop_shadow_artifact_helpers_doc_is_valid()
    ranked_native_interop_shadow_artifact_helpers_review_doc_valid = _ranked_native_interop_shadow_artifact_helpers_review_doc_is_valid()
    ranked_native_interop_shadow_artifact_helpers_implementation_review_doc_valid = _ranked_native_interop_shadow_artifact_helpers_implementation_review_doc_is_valid()
    ranked_native_interop_shadow_artifact_report_doc_valid = _ranked_native_interop_shadow_artifact_report_doc_is_valid()
    ranked_native_interop_shadow_artifact_report_review_doc_valid = _ranked_native_interop_shadow_artifact_report_review_doc_is_valid()
    ranked_native_interop_shadow_artifact_report_helpers_implementation_review_doc_valid = _ranked_native_interop_shadow_artifact_report_helpers_implementation_review_doc_is_valid()
    ranked_native_interop_shadow_artifact_report_run_doc_valid = _ranked_native_interop_shadow_artifact_report_run_doc_is_valid()
    ranked_native_interop_shadow_artifact_report_run_review_doc_valid = _ranked_native_interop_shadow_artifact_report_run_review_doc_is_valid()
    ranked_native_interop_shadow_artifact_report_run_result_doc_valid = _ranked_native_interop_shadow_artifact_report_run_result_doc_is_valid()
    ranked_native_interop_shadow_artifact_report_run_implementation_review_doc_valid = _ranked_native_interop_shadow_artifact_report_run_implementation_review_doc_is_valid()
    ranked_native_to_internal_turing_readiness_bridge_doc_valid = _ranked_native_to_internal_turing_readiness_bridge_doc_is_valid()
    ranked_native_to_internal_turing_readiness_bridge_review_doc_valid = _ranked_native_to_internal_turing_readiness_bridge_review_doc_is_valid()
    internal_turing_style_readiness_dimensions_and_corpus_doc_valid = _internal_turing_style_readiness_dimensions_and_corpus_doc_is_valid()
    internal_turing_style_readiness_dimensions_and_corpus_review_doc_valid = _internal_turing_style_readiness_dimensions_and_corpus_review_doc_is_valid()
    internal_turing_scenario_corpus_helpers_doc_valid = _internal_turing_scenario_corpus_helpers_doc_is_valid()
    internal_turing_scenario_corpus_helpers_review_doc_valid = _internal_turing_scenario_corpus_helpers_review_doc_is_valid()
    internal_turing_scenario_corpus_helpers_implementation_review_doc_valid = _internal_turing_scenario_corpus_helpers_implementation_review_doc_is_valid()
    internal_turing_multi_turn_evaluation_protocol_doc_valid = _internal_turing_multi_turn_evaluation_protocol_doc_is_valid()
    internal_turing_multi_turn_evaluation_protocol_review_doc_valid = _internal_turing_multi_turn_evaluation_protocol_review_doc_is_valid()
    internal_turing_multi_turn_protocol_helpers_doc_valid = _internal_turing_multi_turn_protocol_helpers_doc_is_valid()
    internal_turing_multi_turn_protocol_helpers_review_doc_valid = _internal_turing_multi_turn_protocol_helpers_review_doc_is_valid()
    internal_turing_multi_turn_protocol_helpers_implementation_review_doc_valid = _internal_turing_multi_turn_protocol_helpers_implementation_review_doc_is_valid()
    internal_turing_to_answer_authority_boundary_doc_valid = _internal_turing_to_answer_authority_boundary_doc_is_valid()
    internal_turing_to_answer_authority_boundary_review_doc_valid = _internal_turing_to_answer_authority_boundary_review_doc_is_valid()
    answer_authority_boundary_helpers_doc_valid = _answer_authority_boundary_helpers_doc_is_valid()
    answer_authority_boundary_helpers_review_doc_valid = _answer_authority_boundary_helpers_review_doc_is_valid()
    answer_authority_boundary_helpers_implementation_review_doc_valid = _answer_authority_boundary_helpers_implementation_review_doc_is_valid()
    answer_composition_authority_boundary_doc_valid = _answer_composition_authority_boundary_doc_is_valid()
    answer_composition_authority_boundary_review_doc_valid = _answer_composition_authority_boundary_review_doc_is_valid()
    answer_composition_authority_helpers_doc_valid = _answer_composition_authority_helpers_doc_is_valid()
    answer_composition_authority_helpers_review_doc_valid = _answer_composition_authority_helpers_review_doc_is_valid()
    answer_composition_authority_helpers_implementation_plan_doc_valid = _answer_composition_authority_helpers_implementation_plan_doc_is_valid()
    answer_composition_authority_helpers_implementation_plan_review_doc_valid = _answer_composition_authority_helpers_implementation_plan_review_doc_is_valid()
    answer_composition_authority_helpers_implementation_review_doc_valid = _answer_composition_authority_helpers_implementation_review_doc_is_valid()
    answer_composition_authority_report_helpers_doc_valid = _answer_composition_authority_report_helpers_doc_is_valid()
    answer_composition_authority_report_helpers_review_doc_valid = _answer_composition_authority_report_helpers_review_doc_is_valid()
    answer_composition_authority_report_helpers_implementation_review_doc_valid = _answer_composition_authority_report_helpers_implementation_review_doc_is_valid()
    answer_composition_authority_report_run_design_doc_valid = _answer_composition_authority_report_run_design_doc_is_valid()
    answer_composition_authority_report_run_review_doc_valid = _answer_composition_authority_report_run_review_doc_is_valid()
    answer_composition_authority_report_run_result_doc_valid = _answer_composition_authority_report_run_result_doc_is_valid()
    answer_composition_authority_report_run_result_review_doc_valid = _answer_composition_authority_report_run_result_review_doc_is_valid()
    controlled_answer_composition_dry_run_boundary_doc_valid = _controlled_answer_composition_dry_run_boundary_doc_is_valid()
    controlled_answer_composition_dry_run_boundary_review_doc_valid = _controlled_answer_composition_dry_run_boundary_review_doc_is_valid()
    controlled_answer_composition_dry_run_helpers_design_doc_valid = _controlled_answer_composition_dry_run_helpers_design_doc_is_valid()
    controlled_answer_composition_dry_run_helpers_review_doc_valid = _controlled_answer_composition_dry_run_helpers_review_doc_is_valid()
    controlled_answer_composition_dry_run_helpers_implementation_review_doc_valid = _controlled_answer_composition_dry_run_helpers_implementation_review_doc_is_valid()
    controlled_answer_composition_dry_run_result_design_doc_valid = _controlled_answer_composition_dry_run_result_design_doc_is_valid()
    controlled_answer_composition_dry_run_result_review_doc_valid = _controlled_answer_composition_dry_run_result_review_doc_is_valid()
    controlled_answer_composition_dry_run_result_test_fix_review_doc_valid = _controlled_answer_composition_dry_run_result_test_fix_review_doc_is_valid()
    controlled_answer_composition_dry_run_execution_design_doc_valid = _controlled_answer_composition_dry_run_execution_design_doc_is_valid()
    controlled_answer_composition_dry_run_execution_review_doc_valid = _controlled_answer_composition_dry_run_execution_review_doc_is_valid()
    controlled_answer_composition_dry_run_result_artifact_doc_valid = _controlled_answer_composition_dry_run_result_artifact_doc_is_valid()
    controlled_answer_composition_dry_run_execution_result_review_doc_valid = _controlled_answer_composition_dry_run_execution_result_review_doc_is_valid()
    controlled_answer_composition_dry_run_to_answer_formation_bridge_doc_valid = _controlled_answer_composition_dry_run_to_answer_formation_bridge_doc_is_valid()
    controlled_answer_composition_dry_run_to_answer_formation_bridge_review_doc_valid = _controlled_answer_composition_dry_run_to_answer_formation_bridge_review_doc_is_valid()
    answer_formation_helpers_design_doc_valid = _answer_formation_helpers_design_doc_is_valid()
    answer_formation_helpers_review_doc_valid = _answer_formation_helpers_review_doc_is_valid()
    answer_formation_helpers_implementation_plan_doc_valid = _answer_formation_helpers_implementation_plan_doc_is_valid()
    answer_formation_helpers_implementation_plan_review_doc_valid = _answer_formation_helpers_implementation_plan_review_doc_is_valid()
    answer_formation_helpers_implementation_review_doc_valid = _answer_formation_helpers_implementation_review_doc_is_valid()
    answer_formation_report_helpers_design_doc_valid = _answer_formation_report_helpers_design_doc_is_valid()
    answer_formation_report_helpers_review_doc_valid = _answer_formation_report_helpers_review_doc_is_valid()
    answer_formation_report_helpers_implementation_review_doc_valid = _answer_formation_report_helpers_implementation_review_doc_is_valid()
    answer_formation_report_run_design_doc_valid = _answer_formation_report_run_design_doc_is_valid()
    answer_formation_report_run_review_doc_valid = _answer_formation_report_run_review_doc_is_valid()
    answer_formation_report_run_result_doc_valid = _answer_formation_report_run_result_doc_is_valid()
    answer_formation_report_run_result_review_doc_valid = _answer_formation_report_run_result_review_doc_is_valid()
    answer_formation_dry_run_boundary_doc_valid = _answer_formation_dry_run_boundary_doc_is_valid()
    answer_formation_dry_run_boundary_review_doc_valid = _answer_formation_dry_run_boundary_review_doc_is_valid()
    answer_formation_dry_run_helpers_design_doc_valid = _answer_formation_dry_run_helpers_design_doc_is_valid()
    answer_formation_dry_run_helpers_review_doc_valid = _answer_formation_dry_run_helpers_review_doc_is_valid()
    answer_formation_dry_run_helpers_implementation_review_doc_valid = _answer_formation_dry_run_helpers_implementation_review_doc_is_valid()
    answer_formation_dry_run_execution_design_doc_valid = _answer_formation_dry_run_execution_design_doc_is_valid()
    answer_formation_dry_run_execution_review_doc_valid = _answer_formation_dry_run_execution_review_doc_is_valid()
    answer_formation_dry_run_result_doc_valid = _answer_formation_dry_run_result_doc_is_valid()
    answer_formation_dry_run_execution_result_review_doc_valid = _answer_formation_dry_run_execution_result_review_doc_is_valid()
    controlled_answer_formation_execution_boundary_doc_valid = _controlled_answer_formation_execution_boundary_doc_is_valid()
    controlled_answer_formation_execution_boundary_review_doc_valid = _controlled_answer_formation_execution_boundary_review_doc_is_valid()
    controlled_answer_formation_execution_helpers_design_doc_valid = _controlled_answer_formation_execution_helpers_design_doc_is_valid()
    controlled_answer_formation_execution_helpers_review_doc_valid = _controlled_answer_formation_execution_helpers_review_doc_is_valid()
    controlled_answer_formation_execution_helpers_implementation_review_doc_valid = _controlled_answer_formation_execution_helpers_implementation_review_doc_is_valid()
    controlled_answer_formation_execution_result_design_doc_valid = _controlled_answer_formation_execution_result_design_doc_is_valid()
    controlled_answer_formation_execution_result_design_review_doc_valid = _controlled_answer_formation_execution_result_design_review_doc_is_valid()
    controlled_answer_formation_execution_result_artifact_doc_valid = _controlled_answer_formation_execution_result_artifact_doc_is_valid()
    controlled_answer_formation_execution_result_artifact_review_doc_valid = _controlled_answer_formation_execution_result_artifact_review_doc_is_valid()
    controlled_answer_formation_chain_next_step_review_doc_valid = _controlled_answer_formation_chain_next_step_review_doc_is_valid()
    controlled_answer_composition_boundary_doc_valid = _controlled_answer_composition_boundary_doc_is_valid()
    controlled_answer_composition_boundary_review_doc_valid = _controlled_answer_composition_boundary_review_doc_is_valid()
    controlled_answer_composition_helpers_design_doc_valid = _controlled_answer_composition_helpers_design_doc_is_valid()
    controlled_answer_composition_helpers_review_doc_valid = _controlled_answer_composition_helpers_review_doc_is_valid()
    controlled_answer_composition_helpers_implementation_review_doc_valid = _controlled_answer_composition_helpers_implementation_review_doc_is_valid()
    controlled_answer_composition_result_design_doc_valid = _controlled_answer_composition_result_design_doc_is_valid()
    controlled_answer_composition_result_design_review_doc_valid = _controlled_answer_composition_result_design_review_doc_is_valid()
    controlled_answer_composition_result_artifact_doc_valid = _controlled_answer_composition_result_artifact_doc_is_valid()
    controlled_answer_composition_result_artifact_review_doc_valid = _controlled_answer_composition_result_artifact_review_doc_is_valid()
    controlled_answer_composition_chain_next_step_review_doc_valid = _controlled_answer_composition_chain_next_step_review_doc_is_valid()
    controlled_final_answer_generation_boundary_doc_valid = _controlled_final_answer_generation_boundary_doc_is_valid()
    controlled_final_answer_generation_boundary_review_doc_valid = _controlled_final_answer_generation_boundary_review_doc_is_valid()
    controlled_final_answer_generation_helpers_doc_valid = _controlled_final_answer_generation_helpers_doc_is_valid()
    controlled_final_answer_generation_helpers_review_doc_valid = _controlled_final_answer_generation_helpers_review_doc_is_valid()
    controlled_final_answer_generation_helpers_implementation_review_doc_valid = _controlled_final_answer_generation_helpers_implementation_review_doc_is_valid()
    controlled_final_answer_generation_result_design_doc_valid = _controlled_final_answer_generation_result_design_doc_is_valid()
    controlled_final_answer_generation_result_design_review_doc_valid = _controlled_final_answer_generation_result_design_review_doc_is_valid()
    controlled_final_answer_generation_result_artifact_doc_valid = _controlled_final_answer_generation_result_artifact_doc_is_valid()
    controlled_final_answer_generation_result_artifact_review_doc_valid = _controlled_final_answer_generation_result_artifact_review_doc_is_valid()
    controlled_final_answer_generation_chain_next_step_review_doc_valid = _controlled_final_answer_generation_chain_next_step_review_doc_is_valid()
    controlled_user_facing_output_boundary_doc_valid = _controlled_user_facing_output_boundary_doc_is_valid()
    controlled_user_facing_output_boundary_review_doc_valid = _controlled_user_facing_output_boundary_review_doc_is_valid()
    controlled_user_facing_output_helpers_doc_valid = _controlled_user_facing_output_helpers_doc_is_valid()
    controlled_user_facing_output_helpers_review_doc_valid = _controlled_user_facing_output_helpers_review_doc_is_valid()
    controlled_user_facing_output_helpers_implementation_review_doc_valid = _controlled_user_facing_output_helpers_implementation_review_doc_is_valid()
    controlled_user_facing_output_result_design_doc_valid = _controlled_user_facing_output_result_design_doc_is_valid()
    controlled_user_facing_output_result_design_review_doc_valid = _controlled_user_facing_output_result_design_review_doc_is_valid()
    controlled_user_facing_output_result_artifact_doc_valid = _controlled_user_facing_output_result_artifact_doc_is_valid()
    controlled_user_facing_output_result_artifact_review_doc_valid = _controlled_user_facing_output_result_artifact_review_doc_is_valid()
    controlled_user_facing_output_chain_next_step_review_doc_valid = _controlled_user_facing_output_chain_next_step_review_doc_is_valid()
    controlled_reply_text_boundary_doc_valid = _controlled_reply_text_boundary_doc_is_valid()
    controlled_reply_text_boundary_review_doc_valid = _controlled_reply_text_boundary_review_doc_is_valid()
    controlled_reply_text_helpers_doc_valid = _controlled_reply_text_helpers_doc_is_valid()
    controlled_reply_text_helpers_review_doc_valid = _controlled_reply_text_helpers_review_doc_is_valid()
    controlled_reply_text_result_design_review_doc_valid = _controlled_reply_text_result_design_review_doc_is_valid()
    controlled_reply_text_result_artifact_review_doc_valid = _controlled_reply_text_result_artifact_review_doc_is_valid()
    controlled_reply_text_result_artifact_doc_valid = _controlled_reply_text_result_artifact_doc_is_valid()
    controlled_reply_text_result_design_doc_valid = _controlled_reply_text_result_design_doc_is_valid()
    controlled_reply_text_helpers_implementation_review_doc_valid = _controlled_reply_text_helpers_implementation_review_doc_is_valid()
    controlled_reply_text_chain_next_step_review_doc_valid = _controlled_reply_text_chain_next_step_review_doc_is_valid()
    controlled_reply_preview_helpers_doc_valid = _controlled_reply_preview_helpers_doc_is_valid()
    controlled_reply_preview_helpers_review_doc_valid = _controlled_reply_preview_helpers_review_doc_is_valid()
    controlled_reply_preview_helpers_implementation_review_doc_valid = _controlled_reply_preview_helpers_implementation_review_doc_is_valid()
    controlled_reply_preview_result_design_doc_valid = _controlled_reply_preview_result_design_doc_is_valid()
    controlled_reply_preview_result_design_review_doc_valid = _controlled_reply_preview_result_design_review_doc_is_valid()
    controlled_reply_preview_result_artifact_doc_valid = _controlled_reply_preview_result_artifact_doc_is_valid()
    controlled_reply_preview_result_artifact_review_doc_valid = _controlled_reply_preview_result_artifact_review_doc_is_valid()
    controlled_reply_preview_chain_next_step_review_doc_valid = _controlled_reply_preview_chain_next_step_review_doc_is_valid()
    controlled_reply_output_precondition_boundary_doc_valid = _controlled_reply_output_precondition_boundary_doc_is_valid()
    controlled_reply_output_precondition_boundary_review_doc_valid = _controlled_reply_output_precondition_boundary_review_doc_is_valid()
    controlled_reply_output_precondition_chain_next_step_review_doc_valid = _controlled_reply_output_precondition_chain_next_step_review_doc_is_valid()
    unknown_engine_boundary_doc_valid = _unknown_engine_boundary_doc_is_valid()
    unknown_engine_boundary_review_doc_valid = _unknown_engine_boundary_review_doc_is_valid()
    cognitive_gym_suite_boundary_doc_valid = _cognitive_gym_suite_boundary_doc_is_valid()
    cognitive_gym_suite_boundary_review_doc_valid = _cognitive_gym_suite_boundary_review_doc_is_valid()
    cognitive_gym_run_protocol_doc_valid = _cognitive_gym_run_protocol_doc_is_valid()
    cognitive_gym_run_protocol_review_doc_valid = _cognitive_gym_run_protocol_review_doc_is_valid()
    cognitive_gym_run_protocol_helpers_implementation_review_doc_valid = _cognitive_gym_run_protocol_helpers_implementation_review_doc_is_valid()
    unknown_engine_helpers_doc_valid = _unknown_engine_helpers_doc_is_valid()
    unknown_engine_helpers_review_doc_valid = _unknown_engine_helpers_review_doc_is_valid()
    unknown_engine_helpers_implementation_review_doc_valid = _unknown_engine_helpers_implementation_review_doc_is_valid()
    unknown_engine_helpers_validation_fix_review_doc_valid = _unknown_engine_helpers_validation_fix_review_doc_is_valid()
    unknown_engine_result_artifact_boundary_doc_valid = _unknown_engine_result_artifact_boundary_doc_is_valid()
    unknown_engine_result_artifact_boundary_review_doc_valid = _unknown_engine_result_artifact_boundary_review_doc_is_valid()
    unknown_engine_result_artifact_helpers_doc_valid = _unknown_engine_result_artifact_helpers_doc_is_valid()
    unknown_engine_result_artifact_helpers_review_doc_valid = _unknown_engine_result_artifact_helpers_review_doc_is_valid()
    unknown_engine_result_artifact_helpers_implementation_review_doc_valid = _unknown_engine_result_artifact_helpers_implementation_review_doc_is_valid()
    unknown_engine_result_artifact_doc_valid = _unknown_engine_result_artifact_doc_is_valid()
    unknown_engine_result_artifact_review_doc_valid = _unknown_engine_result_artifact_review_doc_is_valid()
    cognitive_gym_erdos_challenge_track_doc_valid = _cognitive_gym_erdos_challenge_track_doc_is_valid()
    cognitive_gym_erdos_challenge_track_review_doc_valid = _cognitive_gym_erdos_challenge_track_review_doc_is_valid()
    cognitive_gym_erdos_challenge_track_helpers_implementation_review_doc_valid = _cognitive_gym_erdos_challenge_track_helpers_implementation_review_doc_is_valid()
    cognitive_gym_erdos_case_corpus_boundary_doc_valid = _cognitive_gym_erdos_case_corpus_boundary_doc_is_valid()
    cognitive_gym_erdos_case_corpus_boundary_review_doc_valid = _cognitive_gym_erdos_case_corpus_boundary_review_doc_is_valid()
    cognitive_gym_exploratory_case_protocol_review_doc_valid = _cognitive_gym_exploratory_case_protocol_review_doc_is_valid()
    cognitive_gym_exploratory_case_helpers_doc_valid = _cognitive_gym_exploratory_case_helpers_doc_is_valid()
    cognitive_gym_exploratory_case_helpers_review_doc_valid = _cognitive_gym_exploratory_case_helpers_review_doc_is_valid()
    cognitive_gym_exploratory_case_helpers_implementation_review_doc_valid = _cognitive_gym_exploratory_case_helpers_implementation_review_doc_is_valid()
    first_engine_specific_exploratory_helper_boundary_doc_valid = _first_engine_specific_exploratory_helper_boundary_doc_is_valid()
    first_engine_specific_exploratory_helper_boundary_review_doc_valid = _first_engine_specific_exploratory_helper_boundary_review_doc_is_valid()
    calibration_ledger_exploratory_helpers_doc_valid = _calibration_ledger_exploratory_helpers_doc_is_valid()
    calibration_ledger_exploratory_helpers_review_doc_valid = _calibration_ledger_exploratory_helpers_review_doc_is_valid()
    controlled_reply_preview_boundary_review_doc_valid = _controlled_reply_preview_boundary_review_doc_is_valid()
    controlled_reply_preview_boundary_doc_valid = _controlled_reply_preview_boundary_doc_is_valid()
    plan_helper_flag_on_local_observation_design_doc_valid = _plan_helper_flag_on_local_observation_design_doc_is_valid()
    plan_helper_observation_reporting_design_doc_valid = _plan_helper_observation_reporting_design_doc_is_valid()
    behavior_evaluation_turing_style_readiness_doc_valid = _behavior_evaluation_turing_style_readiness_doc_is_valid()
    controlled_behavior_evaluation_prompt_set_doc_valid = _controlled_behavior_evaluation_prompt_set_doc_is_valid()
    controlled_behavior_stubbed_runtime_evaluation_design_doc_valid = _controlled_behavior_stubbed_runtime_evaluation_design_doc_is_valid()
    controlled_local_runtime_evaluation_design_doc_valid = _controlled_local_runtime_evaluation_design_doc_is_valid()
    controlled_local_chatresponder_shadow_observation_design_doc_valid = _controlled_local_chatresponder_shadow_observation_design_doc_is_valid()
    controlled_local_chatresponder_shadow_execution_design_doc_valid = _controlled_local_chatresponder_shadow_execution_design_doc_is_valid()
    controlled_real_chatresponder_shadow_call_design_doc_valid = _controlled_real_chatresponder_shadow_call_design_doc_is_valid()
    controlled_safe_non_model_observation_lane_v2_design_doc_valid = _controlled_safe_non_model_observation_lane_v2_design_doc_is_valid()
    mocked_observation_to_live_slice_governance_design_doc_valid = _mocked_observation_to_live_slice_governance_design_doc_is_valid()
    first_deterministic_safe_live_slice_preimplementation_plan_doc_valid = _first_deterministic_safe_live_slice_preimplementation_plan_doc_is_valid()
    first_deterministic_safe_live_slice_implementation_guards_design_doc_valid = _first_deterministic_safe_live_slice_implementation_guards_design_doc_is_valid()
    first_deterministic_safe_live_slice_dry_run_plan_doc_valid = _first_deterministic_safe_live_slice_dry_run_plan_doc_is_valid()
    weslr_working_root_context_doc_valid = _weslr_working_root_context_doc_is_valid()
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
        if path == _cognition_target_model_doc:
            allowed = cognition_target_model_doc_valid
            if not cognition_target_model_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _ranked_state_grounded_response_formation_doc:
            allowed = ranked_state_grounded_response_formation_doc_valid
            if not ranked_state_grounded_response_formation_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _ranked_state_grounded_response_shadow_helpers_review_doc:
            allowed = ranked_state_grounded_response_shadow_helpers_review_doc_valid
            if not ranked_state_grounded_response_shadow_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_response_shadow_evaluation_scenarios_doc:
            allowed = ranked_response_shadow_evaluation_scenarios_doc_valid
            if not ranked_response_shadow_evaluation_scenarios_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _ranked_response_shadow_evaluation_scenarios_review_doc:
            allowed = ranked_response_shadow_evaluation_scenarios_review_doc_valid
            if not ranked_response_shadow_evaluation_scenarios_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_response_shadow_evaluation_report_design_doc:
            allowed = ranked_response_shadow_evaluation_report_design_doc_valid
            if not ranked_response_shadow_evaluation_report_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _ranked_response_shadow_evaluation_report_helpers_review_doc:
            allowed = ranked_response_shadow_evaluation_report_helpers_review_doc_valid
            if not ranked_response_shadow_evaluation_report_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_response_shadow_evaluation_report_run_design_doc:
            allowed = ranked_response_shadow_evaluation_report_run_design_doc_valid
            if not ranked_response_shadow_evaluation_report_run_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _ranked_response_shadow_evaluation_report_run_result_doc:
            allowed = ranked_response_shadow_evaluation_report_run_result_doc_valid
            if not ranked_response_shadow_evaluation_report_run_result_doc_valid:
                violations.append(f"  result doc missing required markers: {path}")
        if path == _ranked_response_shadow_evaluation_report_run_review_doc:
            allowed = ranked_response_shadow_evaluation_report_run_review_doc_valid
            if not ranked_response_shadow_evaluation_report_run_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_response_shadow_helper_interop_boundary_doc:
            allowed = ranked_response_shadow_helper_interop_boundary_doc_valid
            if not ranked_response_shadow_helper_interop_boundary_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _ranked_response_shadow_helper_interop_boundary_review_doc:
            allowed = ranked_response_shadow_helper_interop_boundary_review_doc_valid
            if not ranked_response_shadow_helper_interop_boundary_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_response_shadow_native_dry_slice_interop_doc:
            allowed = ranked_response_shadow_native_dry_slice_interop_doc_valid
            if not ranked_response_shadow_native_dry_slice_interop_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _ranked_response_shadow_native_dry_slice_interop_review_doc:
            allowed = ranked_response_shadow_native_dry_slice_interop_review_doc_valid
            if not ranked_response_shadow_native_dry_slice_interop_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_native_interop_shadow_artifact_helpers_doc:
            allowed = ranked_native_interop_shadow_artifact_helpers_doc_valid
            if not ranked_native_interop_shadow_artifact_helpers_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _ranked_native_interop_shadow_artifact_helpers_review_doc:
            allowed = ranked_native_interop_shadow_artifact_helpers_review_doc_valid
            if not ranked_native_interop_shadow_artifact_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_native_interop_shadow_artifact_helpers_implementation_review_doc:
            allowed = ranked_native_interop_shadow_artifact_helpers_implementation_review_doc_valid
            if not ranked_native_interop_shadow_artifact_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_native_interop_shadow_artifact_report_doc:
            allowed = ranked_native_interop_shadow_artifact_report_doc_valid
            if not ranked_native_interop_shadow_artifact_report_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _ranked_native_interop_shadow_artifact_report_review_doc:
            allowed = ranked_native_interop_shadow_artifact_report_review_doc_valid
            if not ranked_native_interop_shadow_artifact_report_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_native_interop_shadow_artifact_report_helpers_implementation_review_doc:
            allowed = ranked_native_interop_shadow_artifact_report_helpers_implementation_review_doc_valid
            if not ranked_native_interop_shadow_artifact_report_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_native_interop_shadow_artifact_report_run_doc:
            allowed = ranked_native_interop_shadow_artifact_report_run_doc_valid
            if not ranked_native_interop_shadow_artifact_report_run_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _ranked_native_interop_shadow_artifact_report_run_review_doc:
            allowed = ranked_native_interop_shadow_artifact_report_run_review_doc_valid
            if not ranked_native_interop_shadow_artifact_report_run_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_native_interop_shadow_artifact_report_run_result_doc:
            allowed = ranked_native_interop_shadow_artifact_report_run_result_doc_valid
            if not ranked_native_interop_shadow_artifact_report_run_result_doc_valid:
                violations.append(f"  result doc missing required markers: {path}")
        if path == _ranked_native_interop_shadow_artifact_report_run_implementation_review_doc:
            allowed = ranked_native_interop_shadow_artifact_report_run_implementation_review_doc_valid
            if not ranked_native_interop_shadow_artifact_report_run_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _ranked_native_to_internal_turing_readiness_bridge_doc:
            allowed = ranked_native_to_internal_turing_readiness_bridge_doc_valid
            if not ranked_native_to_internal_turing_readiness_bridge_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _ranked_native_to_internal_turing_readiness_bridge_review_doc:
            allowed = ranked_native_to_internal_turing_readiness_bridge_review_doc_valid
            if not ranked_native_to_internal_turing_readiness_bridge_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _internal_turing_style_readiness_dimensions_and_corpus_doc:
            allowed = internal_turing_style_readiness_dimensions_and_corpus_doc_valid
            if not internal_turing_style_readiness_dimensions_and_corpus_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _internal_turing_style_readiness_dimensions_and_corpus_review_doc:
            allowed = internal_turing_style_readiness_dimensions_and_corpus_review_doc_valid
            if not internal_turing_style_readiness_dimensions_and_corpus_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _internal_turing_scenario_corpus_helpers_doc:
            allowed = internal_turing_scenario_corpus_helpers_doc_valid
            if not internal_turing_scenario_corpus_helpers_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _internal_turing_scenario_corpus_helpers_review_doc:
            allowed = internal_turing_scenario_corpus_helpers_review_doc_valid
            if not internal_turing_scenario_corpus_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _internal_turing_scenario_corpus_helpers_implementation_review_doc:
            allowed = internal_turing_scenario_corpus_helpers_implementation_review_doc_valid
            if not internal_turing_scenario_corpus_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _internal_turing_multi_turn_evaluation_protocol_doc:
            allowed = internal_turing_multi_turn_evaluation_protocol_doc_valid
            if not internal_turing_multi_turn_evaluation_protocol_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _internal_turing_multi_turn_evaluation_protocol_review_doc:
            allowed = internal_turing_multi_turn_evaluation_protocol_review_doc_valid
            if not internal_turing_multi_turn_evaluation_protocol_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _internal_turing_multi_turn_protocol_helpers_doc:
            allowed = internal_turing_multi_turn_protocol_helpers_doc_valid
            if not internal_turing_multi_turn_protocol_helpers_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _internal_turing_multi_turn_protocol_helpers_review_doc:
            allowed = internal_turing_multi_turn_protocol_helpers_review_doc_valid
            if not internal_turing_multi_turn_protocol_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _internal_turing_multi_turn_protocol_helpers_implementation_review_doc:
            allowed = internal_turing_multi_turn_protocol_helpers_implementation_review_doc_valid
            if not internal_turing_multi_turn_protocol_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _internal_turing_to_answer_authority_boundary_doc:
            allowed = internal_turing_to_answer_authority_boundary_doc_valid
            if not internal_turing_to_answer_authority_boundary_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _internal_turing_to_answer_authority_boundary_review_doc:
            allowed = internal_turing_to_answer_authority_boundary_review_doc_valid
            if not internal_turing_to_answer_authority_boundary_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_authority_boundary_helpers_doc:
            allowed = answer_authority_boundary_helpers_doc_valid
            if not answer_authority_boundary_helpers_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_authority_boundary_helpers_review_doc:
            allowed = answer_authority_boundary_helpers_review_doc_valid
            if not answer_authority_boundary_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_authority_boundary_helpers_implementation_review_doc:
            allowed = answer_authority_boundary_helpers_implementation_review_doc_valid
            if not answer_authority_boundary_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_composition_authority_boundary_doc:
            allowed = answer_composition_authority_boundary_doc_valid
            if not answer_composition_authority_boundary_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_composition_authority_boundary_review_doc:
            allowed = answer_composition_authority_boundary_review_doc_valid
            if not answer_composition_authority_boundary_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_composition_authority_helpers_doc:
            allowed = answer_composition_authority_helpers_doc_valid
            if not answer_composition_authority_helpers_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_composition_authority_helpers_review_doc:
            allowed = answer_composition_authority_helpers_review_doc_valid
            if not answer_composition_authority_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_composition_authority_helpers_implementation_plan_doc:
            allowed = answer_composition_authority_helpers_implementation_plan_doc_valid
            if not answer_composition_authority_helpers_implementation_plan_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_composition_authority_helpers_implementation_plan_review_doc:
            allowed = answer_composition_authority_helpers_implementation_plan_review_doc_valid
            if not answer_composition_authority_helpers_implementation_plan_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_composition_authority_report_helpers_doc:
            allowed = answer_composition_authority_report_helpers_doc_valid
            if not answer_composition_authority_report_helpers_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_composition_authority_report_helpers_review_doc:
            allowed = answer_composition_authority_report_helpers_review_doc_valid
            if not answer_composition_authority_report_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_composition_authority_report_helpers_implementation_review_doc:
            allowed = answer_composition_authority_report_helpers_implementation_review_doc_valid
            if not answer_composition_authority_report_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_composition_authority_report_run_design_doc:
            allowed = answer_composition_authority_report_run_design_doc_valid
            if not answer_composition_authority_report_run_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_composition_authority_report_run_review_doc:
            allowed = answer_composition_authority_report_run_review_doc_valid
            if not answer_composition_authority_report_run_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_composition_authority_report_run_result_doc:
            allowed = answer_composition_authority_report_run_result_doc_valid
            if not answer_composition_authority_report_run_result_doc_valid:
                violations.append(f"  result doc missing required markers: {path}")
        if path == _answer_composition_authority_report_run_result_review_doc:
            allowed = answer_composition_authority_report_run_result_review_doc_valid
            if not answer_composition_authority_report_run_result_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_boundary_doc:
            allowed = controlled_answer_composition_dry_run_boundary_doc_valid
            if not controlled_answer_composition_dry_run_boundary_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_boundary_review_doc:
            allowed = controlled_answer_composition_dry_run_boundary_review_doc_valid
            if not controlled_answer_composition_dry_run_boundary_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_helpers_design_doc:
            allowed = controlled_answer_composition_dry_run_helpers_design_doc_valid
            if not controlled_answer_composition_dry_run_helpers_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_helpers_review_doc:
            allowed = controlled_answer_composition_dry_run_helpers_review_doc_valid
            if not controlled_answer_composition_dry_run_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_helpers_implementation_review_doc:
            allowed = controlled_answer_composition_dry_run_helpers_implementation_review_doc_valid
            if not controlled_answer_composition_dry_run_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_result_design_doc:
            allowed = controlled_answer_composition_dry_run_result_design_doc_valid
            if not controlled_answer_composition_dry_run_result_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_result_review_doc:
            allowed = controlled_answer_composition_dry_run_result_review_doc_valid
            if not controlled_answer_composition_dry_run_result_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_result_test_fix_review_doc:
            allowed = controlled_answer_composition_dry_run_result_test_fix_review_doc_valid
            if not controlled_answer_composition_dry_run_result_test_fix_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_execution_design_doc:
            allowed = controlled_answer_composition_dry_run_execution_design_doc_valid
            if not controlled_answer_composition_dry_run_execution_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_execution_review_doc:
            allowed = controlled_answer_composition_dry_run_execution_review_doc_valid
            if not controlled_answer_composition_dry_run_execution_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_result_artifact_doc:
            allowed = controlled_answer_composition_dry_run_result_artifact_doc_valid
            if not controlled_answer_composition_dry_run_result_artifact_doc_valid:
                violations.append(f"  result artifact missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_execution_result_review_doc:
            allowed = controlled_answer_composition_dry_run_execution_result_review_doc_valid
            if not controlled_answer_composition_dry_run_execution_result_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_to_answer_formation_bridge_doc:
            allowed = controlled_answer_composition_dry_run_to_answer_formation_bridge_doc_valid
            if not controlled_answer_composition_dry_run_to_answer_formation_bridge_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_answer_composition_dry_run_to_answer_formation_bridge_review_doc:
            allowed = controlled_answer_composition_dry_run_to_answer_formation_bridge_review_doc_valid
            if not controlled_answer_composition_dry_run_to_answer_formation_bridge_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_helpers_design_doc:
            allowed = answer_formation_helpers_design_doc_valid
            if not answer_formation_helpers_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_formation_helpers_review_doc:
            allowed = answer_formation_helpers_review_doc_valid
            if not answer_formation_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_helpers_implementation_plan_doc:
            allowed = answer_formation_helpers_implementation_plan_doc_valid
            if not answer_formation_helpers_implementation_plan_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_formation_helpers_implementation_plan_review_doc:
            allowed = answer_formation_helpers_implementation_plan_review_doc_valid
            if not answer_formation_helpers_implementation_plan_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_helpers_implementation_review_doc:
            allowed = answer_formation_helpers_implementation_review_doc_valid
            if not answer_formation_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_report_helpers_design_doc:
            allowed = answer_formation_report_helpers_design_doc_valid
            if not answer_formation_report_helpers_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_formation_report_helpers_review_doc:
            allowed = answer_formation_report_helpers_review_doc_valid
            if not answer_formation_report_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_report_helpers_implementation_review_doc:
            allowed = answer_formation_report_helpers_implementation_review_doc_valid
            if not answer_formation_report_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_report_run_design_doc:
            allowed = answer_formation_report_run_design_doc_valid
            if not answer_formation_report_run_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_formation_report_run_review_doc:
            allowed = answer_formation_report_run_review_doc_valid
            if not answer_formation_report_run_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_report_run_result_doc:
            allowed = answer_formation_report_run_result_doc_valid
            if not answer_formation_report_run_result_doc_valid:
                violations.append(f"  result doc missing required markers: {path}")
        if path == _answer_formation_report_run_result_review_doc:
            allowed = answer_formation_report_run_result_review_doc_valid
            if not answer_formation_report_run_result_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_dry_run_boundary_doc:
            allowed = answer_formation_dry_run_boundary_doc_valid
            if not answer_formation_dry_run_boundary_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_formation_dry_run_boundary_review_doc:
            allowed = answer_formation_dry_run_boundary_review_doc_valid
            if not answer_formation_dry_run_boundary_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_dry_run_helpers_design_doc:
            allowed = answer_formation_dry_run_helpers_design_doc_valid
            if not answer_formation_dry_run_helpers_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_formation_dry_run_helpers_review_doc:
            allowed = answer_formation_dry_run_helpers_review_doc_valid
            if not answer_formation_dry_run_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_dry_run_helpers_implementation_review_doc:
            allowed = answer_formation_dry_run_helpers_implementation_review_doc_valid
            if not answer_formation_dry_run_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_dry_run_execution_design_doc:
            allowed = answer_formation_dry_run_execution_design_doc_valid
            if not answer_formation_dry_run_execution_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_formation_dry_run_execution_review_doc:
            allowed = answer_formation_dry_run_execution_review_doc_valid
            if not answer_formation_dry_run_execution_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _answer_formation_dry_run_result_doc:
            allowed = answer_formation_dry_run_result_doc_valid
            if not answer_formation_dry_run_result_doc_valid:
                violations.append(f"  result doc missing required markers: {path}")
        if path == _answer_formation_dry_run_execution_result_review_doc:
            allowed = answer_formation_dry_run_execution_result_review_doc_valid
            if not answer_formation_dry_run_execution_result_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_formation_execution_boundary_doc:
            allowed = controlled_answer_formation_execution_boundary_doc_valid
            if not controlled_answer_formation_execution_boundary_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_answer_formation_execution_boundary_review_doc:
            allowed = controlled_answer_formation_execution_boundary_review_doc_valid
            if not controlled_answer_formation_execution_boundary_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_formation_execution_helpers_design_doc:
            allowed = controlled_answer_formation_execution_helpers_design_doc_valid
            if not controlled_answer_formation_execution_helpers_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_answer_formation_execution_helpers_review_doc:
            allowed = controlled_answer_formation_execution_helpers_review_doc_valid
            if not controlled_answer_formation_execution_helpers_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_formation_execution_helpers_implementation_review_doc:
            allowed = controlled_answer_formation_execution_helpers_implementation_review_doc_valid
            if not controlled_answer_formation_execution_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_formation_execution_result_design_doc:
            allowed = controlled_answer_formation_execution_result_design_doc_valid
            if not controlled_answer_formation_execution_result_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_answer_formation_execution_result_design_review_doc:
            allowed = controlled_answer_formation_execution_result_design_review_doc_valid
            if not controlled_answer_formation_execution_result_design_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _controlled_answer_formation_execution_result_artifact_doc:
            allowed = controlled_answer_formation_execution_result_artifact_doc_valid
            if not controlled_answer_formation_execution_result_artifact_doc_valid:
                violations.append(f"  result artifact missing required markers: {path}")
        if path == _controlled_answer_formation_execution_result_artifact_review_doc:
            allowed = controlled_answer_formation_execution_result_artifact_review_doc_valid
            if not controlled_answer_formation_execution_result_artifact_review_doc_valid:
                violations.append(f"  result artifact review missing required markers: {path}")
        if path == _controlled_answer_formation_chain_next_step_review_doc:
            allowed = controlled_answer_formation_chain_next_step_review_doc_valid
            if not controlled_answer_formation_chain_next_step_review_doc_valid:
                violations.append(f"  chain next-step review doc missing required markers: {path}")
        if path == _controlled_answer_composition_boundary_doc:
            allowed = controlled_answer_composition_boundary_doc_valid
            if not controlled_answer_composition_boundary_doc_valid:
                violations.append(f"  controlled answer composition boundary doc missing required markers: {path}")
        if path == _controlled_answer_composition_boundary_review_doc:
            allowed = controlled_answer_composition_boundary_review_doc_valid
            if not controlled_answer_composition_boundary_review_doc_valid:
                violations.append(f"  controlled answer composition boundary review doc missing required markers: {path}")
        if path == _controlled_answer_composition_helpers_design_doc:
            allowed = controlled_answer_composition_helpers_design_doc_valid
            if not controlled_answer_composition_helpers_design_doc_valid:
                violations.append(f"  controlled answer composition helpers design doc missing required markers: {path}")
        if path == _controlled_answer_composition_helpers_review_doc:
            allowed = controlled_answer_composition_helpers_review_doc_valid
            if not controlled_answer_composition_helpers_review_doc_valid:
                violations.append(f"  controlled answer composition helpers review doc missing required markers: {path}")
        if path == _controlled_answer_composition_helpers_implementation_review_doc:
            allowed = controlled_answer_composition_helpers_implementation_review_doc_valid
            if not controlled_answer_composition_helpers_implementation_review_doc_valid:
                violations.append(f"  controlled answer composition helpers implementation review doc missing required markers: {path}")
        if path == _controlled_answer_composition_result_design_doc:
            allowed = controlled_answer_composition_result_design_doc_valid
            if not controlled_answer_composition_result_design_doc_valid:
                violations.append(f"  controlled answer composition result design doc missing required markers: {path}")
        if path == _controlled_answer_composition_result_design_review_doc:
            allowed = controlled_answer_composition_result_design_review_doc_valid
            if not controlled_answer_composition_result_design_review_doc_valid:
                violations.append(f"  controlled answer composition result design review doc missing required markers: {path}")
        if path == _controlled_answer_composition_result_artifact_doc:
            allowed = controlled_answer_composition_result_artifact_doc_valid
            if not controlled_answer_composition_result_artifact_doc_valid:
                violations.append(f"  controlled answer composition result artifact missing required markers: {path}")
        if path == _controlled_answer_composition_result_artifact_review_doc:
            allowed = controlled_answer_composition_result_artifact_review_doc_valid
            if not controlled_answer_composition_result_artifact_review_doc_valid:
                violations.append(f"  controlled answer composition result artifact review missing required markers: {path}")
        if path == _controlled_answer_composition_chain_next_step_review_doc:
            allowed = controlled_answer_composition_chain_next_step_review_doc_valid
            if not controlled_answer_composition_chain_next_step_review_doc_valid:
                violations.append(f"  controlled answer composition chain next step review missing required markers: {path}")
        if path == _controlled_final_answer_generation_boundary_doc:
            allowed = controlled_final_answer_generation_boundary_doc_valid
            if not controlled_final_answer_generation_boundary_doc_valid:
                violations.append(f"  controlled final answer generation boundary doc missing required markers: {path}")
        if path == _controlled_final_answer_generation_boundary_review_doc:
            allowed = controlled_final_answer_generation_boundary_review_doc_valid
            if not controlled_final_answer_generation_boundary_review_doc_valid:
                violations.append(f"  controlled final answer generation boundary review missing required markers: {path}")
        if path == _controlled_final_answer_generation_helpers_doc:
            allowed = controlled_final_answer_generation_helpers_doc_valid
            if not controlled_final_answer_generation_helpers_doc_valid:
                violations.append(f"  controlled final answer generation helpers design missing required markers: {path}")
        if path == _controlled_final_answer_generation_helpers_review_doc:
            allowed = controlled_final_answer_generation_helpers_review_doc_valid
            if not controlled_final_answer_generation_helpers_review_doc_valid:
                violations.append(f"  controlled final answer generation helpers review missing required markers: {path}")
        if path == _controlled_final_answer_generation_helpers_implementation_review_doc:
            allowed = controlled_final_answer_generation_helpers_implementation_review_doc_valid
            if not controlled_final_answer_generation_helpers_implementation_review_doc_valid:
                violations.append(f"  controlled final answer generation helpers implementation review missing required markers: {path}")
        if path == _controlled_final_answer_generation_result_design_doc:
            allowed = controlled_final_answer_generation_result_design_doc_valid
            if not controlled_final_answer_generation_result_design_doc_valid:
                violations.append(f"  controlled final answer generation result design missing required markers: {path}")
        if path == _controlled_final_answer_generation_result_design_review_doc:
            allowed = controlled_final_answer_generation_result_design_review_doc_valid
            if not controlled_final_answer_generation_result_design_review_doc_valid:
                violations.append(f"  controlled final answer generation result design review missing required markers: {path}")
        if path == _controlled_final_answer_generation_result_artifact_doc:
            allowed = controlled_final_answer_generation_result_artifact_doc_valid
            if not controlled_final_answer_generation_result_artifact_doc_valid:
                violations.append(f"  controlled final answer generation result artifact missing required markers: {path}")
        if path == _controlled_final_answer_generation_result_artifact_review_doc:
            allowed = controlled_final_answer_generation_result_artifact_review_doc_valid
            if not controlled_final_answer_generation_result_artifact_review_doc_valid:
                violations.append(f"  controlled final answer generation result artifact review missing required markers: {path}")
        if path == _controlled_final_answer_generation_chain_next_step_review_doc:
            allowed = controlled_final_answer_generation_chain_next_step_review_doc_valid
            if not controlled_final_answer_generation_chain_next_step_review_doc_valid:
                violations.append(f"  controlled final answer generation chain next step review missing required markers: {path}")
        if path == _controlled_user_facing_output_boundary_doc:
            allowed = controlled_user_facing_output_boundary_doc_valid
            if not controlled_user_facing_output_boundary_doc_valid:
                violations.append(f"  controlled user-facing output boundary doc missing required markers: {path}")
        if path == _controlled_user_facing_output_boundary_review_doc:
            allowed = controlled_user_facing_output_boundary_review_doc_valid
            if not controlled_user_facing_output_boundary_review_doc_valid:
                violations.append(f"  controlled user-facing output boundary review missing required markers: {path}")
        if path == _controlled_user_facing_output_helpers_doc:
            allowed = controlled_user_facing_output_helpers_doc_valid
            if not controlled_user_facing_output_helpers_doc_valid:
                violations.append(f"  controlled user-facing output helpers design missing required markers: {path}")
        if path == _controlled_user_facing_output_helpers_review_doc:
            allowed = controlled_user_facing_output_helpers_review_doc_valid
            if not controlled_user_facing_output_helpers_review_doc_valid:
                violations.append(f"  controlled user-facing output helpers review missing required markers: {path}")
        if path == _controlled_user_facing_output_helpers_implementation_review_doc:
            allowed = controlled_user_facing_output_helpers_implementation_review_doc_valid
            if not controlled_user_facing_output_helpers_implementation_review_doc_valid:
                violations.append(f"  controlled user-facing output helpers implementation review missing required markers: {path}")
        if path == _controlled_user_facing_output_result_design_doc:
            allowed = controlled_user_facing_output_result_design_doc_valid
            if not controlled_user_facing_output_result_design_doc_valid:
                violations.append(f"  controlled user-facing output result design missing required markers: {path}")
        if path == _controlled_user_facing_output_result_design_review_doc:
            allowed = controlled_user_facing_output_result_design_review_doc_valid
            if not controlled_user_facing_output_result_design_review_doc_valid:
                violations.append(f"  controlled user-facing output result design review missing required markers: {path}")
        if path == _controlled_user_facing_output_result_artifact_doc:
            allowed = controlled_user_facing_output_result_artifact_doc_valid
            if not controlled_user_facing_output_result_artifact_doc_valid:
                violations.append(f"  controlled user-facing output result artifact missing required markers: {path}")
        if path == _controlled_user_facing_output_result_artifact_review_doc:
            allowed = controlled_user_facing_output_result_artifact_review_doc_valid
            if not controlled_user_facing_output_result_artifact_review_doc_valid:
                violations.append(f"  controlled user-facing output result artifact review missing required markers: {path}")
        if path == _controlled_user_facing_output_chain_next_step_review_doc:
            allowed = controlled_user_facing_output_chain_next_step_review_doc_valid
            if not controlled_user_facing_output_chain_next_step_review_doc_valid:
                violations.append(f"  controlled user-facing output chain next step review missing required markers: {path}")
        if path == _controlled_reply_text_boundary_doc:
            allowed = controlled_reply_text_boundary_doc_valid
            if not controlled_reply_text_boundary_doc_valid:
                violations.append(f"  controlled reply text boundary doc missing required markers: {path}")
        if path == _controlled_reply_text_boundary_review_doc:
            allowed = controlled_reply_text_boundary_review_doc_valid
            if not controlled_reply_text_boundary_review_doc_valid:
                violations.append(f"  controlled reply text boundary review missing required markers: {path}")
        if path == _controlled_reply_text_helpers_doc:
            allowed = controlled_reply_text_helpers_doc_valid
            if not controlled_reply_text_helpers_doc_valid:
                violations.append(f"  controlled reply text helpers doc missing required markers: {path}")
        if path == _controlled_reply_text_helpers_review_doc:
            allowed = controlled_reply_text_helpers_review_doc_valid
            if not controlled_reply_text_helpers_review_doc_valid:
                violations.append(f"  controlled reply text helpers review missing required markers: {path}")
        if path == _controlled_reply_text_result_design_doc:
            allowed = controlled_reply_text_result_design_doc_valid
            if not controlled_reply_text_result_design_doc_valid:
                violations.append(f"  controlled reply text result design missing required markers: {path}")
        if path == _controlled_reply_text_result_design_review_doc:
            allowed = controlled_reply_text_result_design_review_doc_valid
            if not controlled_reply_text_result_design_review_doc_valid:
                violations.append(f"  controlled reply text result design review missing required markers: {path}")
        if path == _controlled_reply_text_result_artifact_doc:
            allowed = controlled_reply_text_result_artifact_doc_valid
            if not controlled_reply_text_result_artifact_doc_valid:
                violations.append(f"  controlled reply text result artifact missing required markers: {path}")
        if path == _controlled_reply_text_result_artifact_review_doc:
            allowed = controlled_reply_text_result_artifact_review_doc_valid
            if not controlled_reply_text_result_artifact_review_doc_valid:
                violations.append(f"  controlled reply text result artifact review missing required markers: {path}")
        if path == _controlled_reply_text_helpers_implementation_review_doc:
            allowed = controlled_reply_text_helpers_implementation_review_doc_valid
            if not controlled_reply_text_helpers_implementation_review_doc_valid:
                violations.append(f"  controlled reply text helpers implementation review missing required markers: {path}")
        if path == _controlled_reply_text_chain_next_step_review_doc:
            allowed = controlled_reply_text_chain_next_step_review_doc_valid
            if not controlled_reply_text_chain_next_step_review_doc_valid:
                violations.append(f"  controlled reply text chain next step review missing required markers: {path}")
        if path == _controlled_reply_preview_helpers_doc:
            allowed = controlled_reply_preview_helpers_doc_valid
            if not controlled_reply_preview_helpers_doc_valid:
                violations.append(f"  controlled reply preview helpers design missing required markers: {path}")
        if path == _controlled_reply_preview_helpers_review_doc:
            allowed = controlled_reply_preview_helpers_review_doc_valid
            if not controlled_reply_preview_helpers_review_doc_valid:
                violations.append(f"  controlled reply preview helpers review missing required markers: {path}")
        if path == _controlled_reply_preview_helpers_implementation_review_doc:
            allowed = controlled_reply_preview_helpers_implementation_review_doc_valid
            if not controlled_reply_preview_helpers_implementation_review_doc_valid:
                violations.append(f"  controlled reply preview helpers implementation review missing required markers: {path}")
        if path == _controlled_reply_preview_result_design_doc:
            allowed = controlled_reply_preview_result_design_doc_valid
            if not controlled_reply_preview_result_design_doc_valid:
                violations.append(f"  controlled reply preview result design missing required markers: {path}")
        if path == _controlled_reply_preview_result_design_review_doc:
            allowed = controlled_reply_preview_result_design_review_doc_valid
            if not controlled_reply_preview_result_design_review_doc_valid:
                violations.append(f"  controlled reply preview result design review missing required markers: {path}")
        if path == _controlled_reply_preview_result_artifact_doc:
            allowed = controlled_reply_preview_result_artifact_doc_valid
            if not controlled_reply_preview_result_artifact_doc_valid:
                violations.append(f"  controlled reply preview result artifact missing required markers: {path}")
        if path == _controlled_reply_preview_result_artifact_review_doc:
            allowed = controlled_reply_preview_result_artifact_review_doc_valid
            if not controlled_reply_preview_result_artifact_review_doc_valid:
                violations.append(f"  controlled reply preview result artifact review missing required markers: {path}")
        if path == _controlled_reply_preview_chain_next_step_review_doc:
            allowed = controlled_reply_preview_chain_next_step_review_doc_valid
            if not controlled_reply_preview_chain_next_step_review_doc_valid:
                violations.append(f"  controlled reply preview chain next step review missing required markers: {path}")
        if path == _controlled_reply_output_precondition_boundary_doc:
            allowed = controlled_reply_output_precondition_boundary_doc_valid
            if not controlled_reply_output_precondition_boundary_doc_valid:
                violations.append(f"  controlled reply output precondition boundary missing required markers: {path}")
        if path == _controlled_reply_output_precondition_boundary_review_doc:
            allowed = controlled_reply_output_precondition_boundary_review_doc_valid
            if not controlled_reply_output_precondition_boundary_review_doc_valid:
                violations.append(f"  controlled reply output precondition boundary review missing required markers: {path}")
        if path == _controlled_reply_output_precondition_chain_next_step_review_doc:
            allowed = controlled_reply_output_precondition_chain_next_step_review_doc_valid
            if not controlled_reply_output_precondition_chain_next_step_review_doc_valid:
                violations.append(f"  controlled reply output precondition chain next step review missing required markers: {path}")
        if path == _unknown_engine_boundary_doc:
            allowed = unknown_engine_boundary_doc_valid
            if not unknown_engine_boundary_doc_valid:
                violations.append(f"  UNKNOWN ENGINE boundary doc missing required markers: {path}")
        if path == _unknown_engine_boundary_review_doc:
            allowed = unknown_engine_boundary_review_doc_valid
            if not unknown_engine_boundary_review_doc_valid:
                violations.append(f"  UNKNOWN ENGINE boundary review missing required markers: {path}")
        if path == _cognitive_gym_suite_boundary_doc:
            allowed = cognitive_gym_suite_boundary_doc_valid
            if not cognitive_gym_suite_boundary_doc_valid:
                violations.append(f"  Cognitive Gym suite boundary doc missing required markers: {path}")
        if path == _cognitive_gym_suite_boundary_review_doc:
            allowed = cognitive_gym_suite_boundary_review_doc_valid
            if not cognitive_gym_suite_boundary_review_doc_valid:
                violations.append(f"  Cognitive Gym suite boundary review missing required markers: {path}")
        if path == _cognitive_gym_run_protocol_doc:
            allowed = cognitive_gym_run_protocol_doc_valid
            if not cognitive_gym_run_protocol_doc_valid:
                violations.append(f"  CognitiveGymRun protocol doc missing required markers: {path}")
        if path == _cognitive_gym_run_protocol_review_doc:
            allowed = cognitive_gym_run_protocol_review_doc_valid
            if not cognitive_gym_run_protocol_review_doc_valid:
                violations.append(f"  CognitiveGymRun protocol review missing required markers: {path}")
        if path == _cognitive_gym_run_protocol_helpers_implementation_review_doc:
            allowed = cognitive_gym_run_protocol_helpers_implementation_review_doc_valid
            if not cognitive_gym_run_protocol_helpers_implementation_review_doc_valid:
                violations.append(f"  CognitiveGymRun protocol helpers implementation review missing required markers: {path}")
        if path == _unknown_engine_helpers_doc:
            allowed = unknown_engine_helpers_doc_valid
            if not unknown_engine_helpers_doc_valid:
                violations.append(f"  UNKNOWN ENGINE helpers design missing required markers: {path}")
        if path == _unknown_engine_helpers_review_doc:
            allowed = unknown_engine_helpers_review_doc_valid
            if not unknown_engine_helpers_review_doc_valid:
                violations.append(f"  UNKNOWN ENGINE helpers review missing required markers: {path}")
        if path == _unknown_engine_helpers_implementation_review_doc:
            allowed = unknown_engine_helpers_implementation_review_doc_valid
            if not unknown_engine_helpers_implementation_review_doc_valid:
                violations.append(f"  UNKNOWN ENGINE helpers implementation review missing required markers: {path}")
        if path == _unknown_engine_helpers_validation_fix_review_doc:
            allowed = unknown_engine_helpers_validation_fix_review_doc_valid
            if not unknown_engine_helpers_validation_fix_review_doc_valid:
                violations.append(f"  UNKNOWN ENGINE helpers validation fix review missing required markers: {path}")
        if path == _unknown_engine_result_artifact_boundary_doc:
            allowed = unknown_engine_result_artifact_boundary_doc_valid
            if not unknown_engine_result_artifact_boundary_doc_valid:
                violations.append(f"  UNKNOWN ENGINE result artifact boundary doc missing required markers: {path}")
        if path == _unknown_engine_result_artifact_boundary_review_doc:
            allowed = unknown_engine_result_artifact_boundary_review_doc_valid
            if not unknown_engine_result_artifact_boundary_review_doc_valid:
                violations.append(f"  UNKNOWN ENGINE result artifact boundary review doc missing required markers: {path}")
        if path == _unknown_engine_result_artifact_helpers_doc:
            allowed = unknown_engine_result_artifact_helpers_doc_valid
            if not unknown_engine_result_artifact_helpers_doc_valid:
                violations.append(f"  UNKNOWN ENGINE result artifact helpers design doc missing required markers: {path}")
        if path == _unknown_engine_result_artifact_helpers_review_doc:
            allowed = unknown_engine_result_artifact_helpers_review_doc_valid
            if not unknown_engine_result_artifact_helpers_review_doc_valid:
                violations.append(f"  UNKNOWN ENGINE result artifact helpers review doc missing required markers: {path}")
        if path == _unknown_engine_result_artifact_helpers_implementation_review_doc:
            allowed = unknown_engine_result_artifact_helpers_implementation_review_doc_valid
            if not unknown_engine_result_artifact_helpers_implementation_review_doc_valid:
                violations.append(f"  UNKNOWN ENGINE result artifact helpers implementation review doc missing required markers: {path}")
        if path == _unknown_engine_result_artifact_doc:
            allowed = unknown_engine_result_artifact_doc_valid
            if not unknown_engine_result_artifact_doc_valid:
                violations.append(f"  UNKNOWN ENGINE result artifact doc missing required markers: {path}")
        if path == _unknown_engine_result_artifact_review_doc:
            allowed = unknown_engine_result_artifact_review_doc_valid
            if not unknown_engine_result_artifact_review_doc_valid:
                violations.append(f"  UNKNOWN ENGINE result artifact review doc missing required markers: {path}")
        if path == _cognitive_gym_erdos_challenge_track_doc:
            allowed = cognitive_gym_erdos_challenge_track_doc_valid
            if not cognitive_gym_erdos_challenge_track_doc_valid:
                violations.append(f"  Cognitive Gym Erdős challenge track doc missing required markers: {path}")
        if path == _cognitive_gym_erdos_challenge_track_review_doc:
            allowed = cognitive_gym_erdos_challenge_track_review_doc_valid
            if not cognitive_gym_erdos_challenge_track_review_doc_valid:
                violations.append(f"  Cognitive Gym Erdős challenge track review doc missing required markers: {path}")
        if path == _cognitive_gym_erdos_challenge_track_helpers_implementation_review_doc:
            allowed = cognitive_gym_erdos_challenge_track_helpers_implementation_review_doc_valid
            if not cognitive_gym_erdos_challenge_track_helpers_implementation_review_doc_valid:
                violations.append(f"  Cognitive Gym Erdős challenge track helpers implementation review doc missing required markers: {path}")
        if path == _cognitive_gym_erdos_case_corpus_boundary_doc:
            allowed = cognitive_gym_erdos_case_corpus_boundary_doc_valid
            if not cognitive_gym_erdos_case_corpus_boundary_doc_valid:
                violations.append(f"  Cognitive Gym Erdős case corpus boundary doc missing required markers: {path}")
        if path == _cognitive_gym_erdos_case_corpus_boundary_review_doc:
            allowed = cognitive_gym_erdos_case_corpus_boundary_review_doc_valid
            if not cognitive_gym_erdos_case_corpus_boundary_review_doc_valid:
                violations.append(f"  Cognitive Gym Erdős case corpus boundary review doc missing required markers: {path}")
        if path == _cognitive_gym_exploratory_case_protocol_review_doc:
            allowed = cognitive_gym_exploratory_case_protocol_review_doc_valid
            if not cognitive_gym_exploratory_case_protocol_review_doc_valid:
                violations.append(f"  Cognitive Gym exploratory case protocol review missing required markers: {path}")
        if path == _cognitive_gym_exploratory_case_helpers_doc:
            allowed = cognitive_gym_exploratory_case_helpers_doc_valid
            if not cognitive_gym_exploratory_case_helpers_doc_valid:
                violations.append(f"  Cognitive Gym exploratory case helpers design missing required markers: {path}")
        if path == _cognitive_gym_exploratory_case_helpers_review_doc:
            allowed = cognitive_gym_exploratory_case_helpers_review_doc_valid
            if not cognitive_gym_exploratory_case_helpers_review_doc_valid:
                violations.append(f"  Cognitive Gym exploratory case helpers review missing required markers: {path}")
        if path == _cognitive_gym_exploratory_case_helpers_implementation_review_doc:
            allowed = cognitive_gym_exploratory_case_helpers_implementation_review_doc_valid
            if not cognitive_gym_exploratory_case_helpers_implementation_review_doc_valid:
                violations.append(f"  Cognitive Gym exploratory case helpers implementation review missing required markers: {path}")
        if path == _first_engine_specific_exploratory_helper_boundary_doc:
            allowed = first_engine_specific_exploratory_helper_boundary_doc_valid
            if not first_engine_specific_exploratory_helper_boundary_doc_valid:
                violations.append(f"  first engine-specific exploratory helper boundary missing required markers: {path}")
        if path == _first_engine_specific_exploratory_helper_boundary_review_doc:
            allowed = first_engine_specific_exploratory_helper_boundary_review_doc_valid
            if not first_engine_specific_exploratory_helper_boundary_review_doc_valid:
                violations.append(f"  first engine-specific exploratory helper boundary review missing required markers: {path}")
        if path == _calibration_ledger_exploratory_helpers_doc:
            allowed = calibration_ledger_exploratory_helpers_doc_valid
            if not calibration_ledger_exploratory_helpers_doc_valid:
                violations.append(f"  CALIBRATION_LEDGER exploratory helpers design missing required markers: {path}")
        if path == _calibration_ledger_exploratory_helpers_review_doc:
            allowed = calibration_ledger_exploratory_helpers_review_doc_valid
            if not calibration_ledger_exploratory_helpers_review_doc_valid:
                violations.append(f"  CALIBRATION_LEDGER exploratory helpers review missing required markers: {path}")
        if path == _controlled_reply_preview_boundary_doc:
            allowed = controlled_reply_preview_boundary_doc_valid
            if not controlled_reply_preview_boundary_doc_valid:
                violations.append(f"  controlled reply preview boundary doc missing required markers: {path}")
        if path == _controlled_reply_preview_boundary_review_doc:
            allowed = controlled_reply_preview_boundary_review_doc_valid
            if not controlled_reply_preview_boundary_review_doc_valid:
                violations.append(f"  controlled reply preview boundary review doc missing required markers: {path}")
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
        if path == _controlled_local_chatresponder_shadow_observation_design_doc:
            allowed = controlled_local_chatresponder_shadow_observation_design_doc_valid
            if not controlled_local_chatresponder_shadow_observation_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_local_chatresponder_shadow_execution_design_doc:
            allowed = controlled_local_chatresponder_shadow_execution_design_doc_valid
            if not controlled_local_chatresponder_shadow_execution_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_real_chatresponder_shadow_call_design_doc:
            allowed = controlled_real_chatresponder_shadow_call_design_doc_valid
            if not controlled_real_chatresponder_shadow_call_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _controlled_safe_non_model_observation_lane_v2_design_doc:
            allowed = controlled_safe_non_model_observation_lane_v2_design_doc_valid
            if not controlled_safe_non_model_observation_lane_v2_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _mocked_observation_to_live_slice_governance_design_doc:
            allowed = mocked_observation_to_live_slice_governance_design_doc_valid
            if not mocked_observation_to_live_slice_governance_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _first_deterministic_safe_live_slice_preimplementation_plan_doc:
            allowed = first_deterministic_safe_live_slice_preimplementation_plan_doc_valid
            if not first_deterministic_safe_live_slice_preimplementation_plan_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _first_deterministic_safe_live_slice_implementation_guards_design_doc:
            allowed = first_deterministic_safe_live_slice_implementation_guards_design_doc_valid
            if not first_deterministic_safe_live_slice_implementation_guards_design_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _first_deterministic_safe_live_slice_dry_run_plan_doc:
            allowed = first_deterministic_safe_live_slice_dry_run_plan_doc_valid
            if not first_deterministic_safe_live_slice_dry_run_plan_doc_valid:
                violations.append(f"  design doc missing required markers: {path}")
        if path == _answer_composition_authority_helpers_implementation_review_doc:
            allowed = answer_composition_authority_helpers_implementation_review_doc_valid
            if not answer_composition_authority_helpers_implementation_review_doc_valid:
                violations.append(f"  review doc missing required markers: {path}")
        if path == _weslr_working_root_context_doc:
            allowed = weslr_working_root_context_doc_valid
            if not weslr_working_root_context_doc_valid:
                violations.append(f"  working-root context doc missing required markers: {path}")
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