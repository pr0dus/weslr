"""Initial WESLR Provenance Source Registry Seed V1.

Seed-only helpers for a governed in-memory baseline of known provenance source
entries. This module does not create persistent registry files, scan sources,
write queues, call advisors/models, activate self-improvement, wire
runtime/chat/voice/proactive behavior, select answers, claim truth/soundness,
or claim benchmark authority.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import fields
from typing import Any

from weslr.provenance_source_registry import (
    ProvenanceSourceEntry,
    ProvenanceSourceSafetyFlags,
    create_empty_provenance_source_entry,
    summarize_provenance_source_entries,
    validate_provenance_source_entry,
)

LIFECYCLE_DOC = "docs/WESLR_PROVENANCE_SOURCE_REGISTRY_LIFECYCLE_DESIGN_V1.md"
SCHEMA_TEST = "weslr/tests/test_provenance_source_registry_schema_v1.py"
SEED_TEST = "weslr/tests/test_provenance_source_registry_initial_seed_v1.py"

_COMMON_FORBIDDEN_OUTPUTS = [
    "automatic activation",
    "runtime action",
    "queue write",
    "memory mutation",
    "answer selection",
    "truth or soundness authority",
    "benchmark authority claims",
]


def _entry(
    *,
    source_id: str,
    display_name: str,
    module_path: str = "",
    source_type: str,
    authority_boundary: str,
    allowed_outputs: list[str],
    related_tests: list[str],
    capability_scope: list[str] | None = None,
    related_docs: list[str] | None = None,
) -> ProvenanceSourceEntry:
    """Create one safe experimental seed entry."""
    return create_empty_provenance_source_entry(
        source_id=source_id,
        display_name=display_name,
        module_path=module_path,
        source_type=source_type,
        authority_boundary=authority_boundary,
        allowed_outputs=allowed_outputs,
        forbidden_outputs=list(_COMMON_FORBIDDEN_OUTPUTS),
        llm_assisted=False,
        advisor_assisted=False,
        operator_review_required=True,
        introduced_in_commit="84e9376",
        last_reviewed_commit="84e9376",
        capability_scope=capability_scope or ["provenance_source_registry_seed_v1"],
        status="experimental",
        owner="operator",
        related_docs=related_docs or [LIFECYCLE_DOC],
        related_tests=related_tests,
        proposed_by="operator",
        origin_type="operator_added",
        approval_status="approved",
        operator_decision="approved",
        validation_required=True,
        tests_required=True,
        activation_allowed=False,
        safety_flags=ProvenanceSourceSafetyFlags(),
    )


def load_initial_provenance_source_entries_v1() -> list[ProvenanceSourceEntry]:
    """Return the governed in-memory V1 baseline seed entries.

    The returned list is a starting baseline only. It is not a fixed final
    registry and it is not persisted by this helper.
    """
    return [
        _entry(
            source_id="capability_registry",
            display_name="Capability Registry",
            module_path="weslr.capability_registry",
            source_type="capability_guidance",
            authority_boundary="Describes governed capability metadata only; does not activate capabilities.",
            allowed_outputs=["capability metadata summaries", "capability boundary descriptions"],
            related_tests=["weslr/tests/test_capability_registry_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="capability_welcome_surface",
            display_name="Capability Welcome Surface",
            module_path="weslr.capability_welcome_surface",
            source_type="capability_guidance",
            authority_boundary="Presents capability guidance only; does not route or execute runtime behavior.",
            allowed_outputs=["welcome capability guidance", "operator-facing capability summaries"],
            related_tests=["weslr/tests/test_capability_welcome_surface_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="proactive_suggestions",
            display_name="Proactive Suggestions",
            module_path="weslr.proactive_suggestions",
            source_type="proactive_suggestion",
            authority_boundary="Produces operator-reviewable suggestions only; no autonomous action authority.",
            allowed_outputs=["governed suggestion records", "operator-reviewable next-step proposals"],
            related_tests=["weslr/tests/test_proactive_suggestions_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="proactive_daemon",
            display_name="Proactive Daemon",
            module_path="weslr.proactive_daemon",
            source_type="proactive_suggestion",
            authority_boundary="May surface governed proactive suggestion context only; no automatic action authority in this seed.",
            allowed_outputs=["proactive context summaries", "review-required suggestion notices"],
            related_tests=["weslr/tests/test_proactive_daemon_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="voice_gateway",
            display_name="Voice Gateway",
            module_path="weslr.voice_gateway",
            source_type="voice_surface",
            authority_boundary="Voice surface attribution only; no unregistered voice output authority.",
            allowed_outputs=["voice routing metadata", "voice attribution summaries"],
            related_tests=["weslr/tests/test_voice_session_routing_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="ambient_voice_loop",
            display_name="Ambient Voice Loop",
            source_type="ambient_loop",
            authority_boundary="Ambient-loop design baseline only; no runtime loop activation authority.",
            allowed_outputs=["ambient voice source attribution plans", "review-required ambient loop metadata"],
            related_tests=["weslr/tests/test_voice_session_routing_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="llm_advisor_mode",
            display_name="LLM Advisor Mode",
            module_path="weslr.llm_advisor_mode",
            source_type="advisor_review",
            authority_boundary="Advisor output remains non-authoritative proposal input requiring operator review.",
            allowed_outputs=["advisor review records", "non-authoritative improvement proposals"],
            related_tests=["weslr/tests/test_llm_advisor_mode_design_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="advisor_prompt_templates",
            display_name="Advisor Prompt Templates",
            module_path="weslr.advisor_prompt_templates",
            source_type="advisor_review",
            authority_boundary="Defines bounded advisor prompt templates only; does not call external models.",
            allowed_outputs=["advisor prompt template metadata", "review prompt structures"],
            related_tests=["weslr/tests/test_advisor_prompt_template_library_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="advisor_review_queue",
            display_name="Advisor Review Queue",
            module_path="weslr.advisor_review_queue",
            source_type="advisor_review",
            authority_boundary="Defines review queue schema and items only; this seed performs no queue writes.",
            allowed_outputs=["advisor review queue item schemas", "queue item summaries"],
            related_tests=["weslr/tests/test_advisor_review_queue_schema_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="local_scan_advisor_review",
            display_name="Local Scan Advisor Review",
            module_path="weslr.local_scan_advisor_review",
            source_type="advisor_review",
            authority_boundary="Maps local scan findings to review concepts only; no scanner execution here.",
            allowed_outputs=["local scan review metadata", "review-required finding summaries"],
            related_tests=["weslr/tests/test_local_scan_advisor_review_schema_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="advisor_review_queue_cli",
            display_name="Advisor Review Queue CLI",
            module_path="weslr.advisor_review_queue_cli",
            source_type="operator_cli",
            authority_boundary="Operator CLI review surface only; no hidden queue writes in this seed.",
            allowed_outputs=["operator review command metadata", "redacted queue summaries"],
            related_tests=["weslr/tests/test_advisor_review_queue_operator_cli_schema_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="synthetic_teaching_lane",
            display_name="Synthetic Teaching Lane",
            source_type="teaching_explanation",
            authority_boundary="Synthetic teaching guidance only; no benchmark authority or answer selection.",
            allowed_outputs=["synthetic teaching explanations", "diagnostic learning notes"],
            related_tests=["weslr/tests/test_synthetic_teaching_lane_canon_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="output_provenance",
            display_name="Output Provenance",
            module_path="weslr.output_provenance",
            source_type="self_review",
            authority_boundary="Captures output provenance metadata only; does not certify truth or soundness.",
            allowed_outputs=["output provenance envelopes", "redacted provenance summaries"],
            related_tests=["weslr/tests/test_output_provenance_envelope_schema_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="provenance_source_registry",
            display_name="Provenance Source Registry",
            module_path="weslr.provenance_source_registry",
            source_type="self_review",
            authority_boundary="Defines registry schema and validation only; does not persist or activate registry entries.",
            allowed_outputs=["registry source entries", "registry validation summaries"],
            related_tests=["weslr/tests/test_provenance_source_registry_schema_v1.py", SEED_TEST],
        ),
        _entry(
            source_id="state_checkpoint",
            display_name="State Checkpoint",
            module_path="weslr.state_checkpoint",
            source_type="state_checkpoint",
            authority_boundary="Records checkpoint metadata only; does not restore, mutate, or run state transitions.",
            allowed_outputs=["checkpoint metadata", "checkpoint summaries"],
            related_tests=["weslr/tests/test_benchmark_reasoning_engine_checkpoint_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="memory_capture",
            display_name="Memory Capture",
            module_path="weslr.memory_capture",
            source_type="memory_capture",
            authority_boundary="Memory capture provenance only; no hidden memory mutation authority.",
            allowed_outputs=["memory capture metadata", "redacted memory provenance summaries"],
            related_tests=["weslr/tests/test_user_timeline_memory_v1.py", "weslr/tests/test_entity_timeline_memory_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="proposal_traceability",
            display_name="Proposal Traceability",
            module_path="weslr.proposal_traceability",
            source_type="self_review",
            authority_boundary="Links proposals to review metadata only; does not approve or execute proposals.",
            allowed_outputs=["proposal trace metadata", "proposal review summaries"],
            related_tests=["weslr/tests/test_proposal_realization.py", "weslr/tests/test_operator_proposal_review.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="reasoning_trace",
            display_name="Reasoning Trace",
            module_path="weslr.reasoning_trace",
            source_type="self_review",
            authority_boundary="Records reasoning trace metadata only; does not assert final correctness.",
            allowed_outputs=["reasoning trace metadata", "reasoning context summaries"],
            related_tests=["weslr/tests/test_reasoning_trace_schema_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="audit_ledger",
            display_name="Audit Ledger",
            module_path="weslr.audit_ledger",
            source_type="self_review",
            authority_boundary="Audit metadata baseline only; does not silently write ledger records from this seed.",
            allowed_outputs=["audit metadata", "redacted audit summaries"],
            related_tests=["weslr/tests/test_change_proposals.py", SCHEMA_TEST, SEED_TEST],
        ),
        _entry(
            source_id="suggestion_box",
            display_name="Suggestion Box",
            module_path="weslr.suggestion_box",
            source_type="proactive_suggestion",
            authority_boundary="Suggestion intake metadata only; suggestions require operator review before use.",
            allowed_outputs=["suggestion metadata", "operator-reviewable suggestion summaries"],
            related_tests=["weslr/tests/test_experiment_proposal_generator_v1.py", SCHEMA_TEST, SEED_TEST],
        ),
    ]


def validate_initial_provenance_source_seed_v1() -> list[str]:
    """Return validation errors for the initial seed list."""
    entries = load_initial_provenance_source_entries_v1()
    errors: list[str] = []
    seen: set[str] = set()

    for entry in entries:
        if entry.source_id in seen:
            errors.append(f"duplicate source_id: {entry.source_id}")
        seen.add(entry.source_id)
        for error in validate_provenance_source_entry(entry):
            errors.append(f"{entry.source_id}: {error}")

    return errors


def summarize_initial_provenance_source_seed_v1() -> dict[str, Any]:
    """Return a redacted/count-only summary of the initial seed baseline."""
    entries = load_initial_provenance_source_entries_v1()
    base_summary = summarize_provenance_source_entries(entries)
    invalid_entry_count = sum(1 for entry in entries if validate_provenance_source_entry(entry))
    activation_allowed_count = sum(1 for entry in entries if entry.activation_allowed)
    llm_assisted_count = sum(1 for entry in entries if entry.llm_assisted)
    advisor_assisted_count = sum(1 for entry in entries if entry.advisor_assisted)
    unsafe_safety_flag_count = sum(
        1
        for entry in entries
        for safety_field in fields(entry.safety_flags)
        if getattr(entry.safety_flags, safety_field.name)
    )

    return {
        "schema_version": "1.0",
        "summary_mode": "redacted_count_only",
        "total_entries": len(entries),
        "source_type_counts": dict(Counter(entry.source_type for entry in entries)),
        "origin_type_counts": dict(Counter(entry.origin_type for entry in entries)),
        "status_counts": dict(Counter(entry.status for entry in entries)),
        "operator_review_required_count": sum(1 for entry in entries if entry.operator_review_required),
        "activation_allowed_count": activation_allowed_count,
        "llm_assisted_count": llm_assisted_count,
        "advisor_assisted_count": advisor_assisted_count,
        "missing_docs_count": base_summary["missing_docs_count"],
        "missing_tests_count": base_summary["missing_tests_count"],
        "invalid_entry_count": invalid_entry_count,
        "unsafe_safety_flag_count": unsafe_safety_flag_count,
    }


def summary_initial_provenance_source_seed_v1() -> dict[str, Any]:
    """Compatibility alias for the initial seed summary helper."""
    return summarize_initial_provenance_source_seed_v1()
