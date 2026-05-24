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
    "denied authority fields",
    "blocked execution behavior",
    "visible risks/followups",
    "abort conditions",
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
    "denied authority fields",
    "blocked execution behavior",
    "visible risks/followups",
    "abort conditions",
    "future implementation/review sequence",
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
    "forbidden real-user/live/raw/provider/runtime inputs",
    "relationship to existing answer formation helpers",
    "relationship to dry-run result artifact",
    "validation-before-controlled-execution policy",
    "no-final-answer policy",
    "no-answer-composition policy",
    "no-runtime policy",
    "safe Markdown policy",
    "JSON-safe policy",
    "blocked artifact behavior",
    "denied authority fields",
    "visible risks/followups",
    "abort conditions",
    "future implementation/review sequence",
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
    "forbidden real-user/live/raw/provider/runtime inputs",
    "validation-before-result-writing policy",
    "safe Markdown result policy",
    "JSON-safe result policy",
    "blocked result behavior",
    "exact no-final-answer boundary",
    "exact no-answer-composition boundary",
    "exact no-runtime boundary",
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
    "forbidden real-user/live/raw/provider/runtime inputs",
    "exact no-live-chat boundary",
    "exact no-runtime boundary",
    "exact no-ChatResponder/respond_chat/generate_chat boundary",
    "exact no-provider/search/advisor boundary",
    "exact no-official-claims boundary",
    "validation-before-user-facing-output policy",
    "controlled user-facing-output artifact shape for a future lane",
    "denied authority fields",
    "blocked user-facing-output behavior",
    "visible risks/followups",
    "abort conditions",
    "future implementation/review sequence",
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
    "forbidden real-user/live/raw/provider/runtime inputs",
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
    "denied authority fields",
    "visible risks/followups",
    "abort conditions",
    "future implementation/review sequence",
    "No blocking design gaps were found.",
    "AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_CONTROLLED_USER_FACING_OUTPUT_HELPERS_V1",
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