"""WESLR Unfinished Research Discovery Constants V1.

Pure metadata-only closed enums for governed unfinished-research discovery.
No IO, no network, no provider/model calls, and no runtime wiring.
"""

from __future__ import annotations

SCHEMA_VERSION_V1 = "unfinished_research_discovery_constants_v1"

_ALLOWED_SIGNAL_TYPES_V1 = (
    "unfinished_work_signal",
    "technology_blocked_signal",
    "cross_domain_transfer_signal",
    "dormant_direction_signal",
    "anomaly_signal",
    "measurement_benchmark_gap_signal",
    "formal_unsolved_problem_signal",
    "extraordinary_claim_signal",
    "fringe_edge_science_signal",
    "time_revisit_signal",
    "domain_convergence_signal",
    "future_workforce_impact_signal",
    "language_protocol_discovery_signal",
    "artifact_generation_candidate",
    "disconfirmation_required",
    "ontology_insufficient_signal",
)

_ALLOWED_ROUTE_TYPES_V1 = (
    "route_to_source_selection_plan",
    "route_to_cross_domain_scout",
    "route_to_candidate_preparation",
    "route_to_operator_review",
    "route_to_disconfirming_review",
    "route_to_extraordinary_claim_quarantine",
    "route_to_archive_low_value_signal",
    "route_to_blocked_by_safety",
    "route_to_time_revisit_review",
    "route_to_domain_convergence_review",
    "route_to_future_workforce_impact_review",
    "route_to_language_protocol_review",
    "route_to_artifact_proposal_plan",
    "route_to_ontology_expansion_request",
)

_ALLOWED_SOURCE_CLASSES_V1 = (
    "public_research_paper",
    "survey_paper",
    "review_paper",
    "benchmark_paper",
    "dataset_record",
    "official_standard",
    "government_agency_report",
    "patent",
    "thesis_dissertation",
    "lab_university_artifact",
    "conference_workshop_artifact",
    "negative_result_paper",
    "replication_study",
    "historical_archive",
    "technical_report",
    "preprint",
    "vendor_technical_documentation",
    "github_repository",
    "code_repository_as_implementation_reference",
    "forum_blog_as_weak_signal",
    "unknown_authority",
)

_ALLOWED_EVIDENCE_ROLES_V1 = (
    "candidate_signal",
    "unfinished_work_signal",
    "dormant_direction_signal",
    "cross_domain_transfer_signal",
    "technology_blocked_signal",
    "anomaly_signal",
    "contradiction_signal",
    "replication_gap_signal",
    "benchmark_gap_signal",
    "measurement_gap_signal",
    "extraordinary_claim_signal",
    "implementation_reference_only",
    "disconfirming_signal",
    "official_constraint_signal",
    "source_selection_needed",
    "prior_art",
    "ontology_insufficient_signal",
)

_ALLOWED_OPERATOR_CONFIRMATION_TOKENS_V1 = (
    "EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED",
    "FUTURE_WORKFORCE_IMPACT_HYPOTHESIS_CONFIRMED",
    "LANGUAGE_PROTOCOL_DISCOVERY_CONFIRMED",
    "ONTOLOGY_EXPANSION_REQUEST_CONFIRMED",
)

_ALLOWED_EXPANSION_RECOMMENDATIONS_V1 = (
    "expansion_enlarge_signal_ontology",
    "expansion_add_new_domain_family",
    "expansion_add_new_source_class",
    "expansion_add_new_evidence_role",
    "expansion_add_new_disconfirmation_class",
    "expansion_add_new_route",
    "expansion_add_new_artifact_type",
    "expansion_add_new_language_protocol_pattern",
    "expansion_add_new_operator_review_category",
    "expansion_create_new_discovery_lens_design_lane",
)

_ALLOWED_ARTIFACT_TYPES_V1 = (
    "source_selection_plan",
    "evidence_disconfirmation_plan",
    "experiment_plan",
    "simulation_plan",
    "dataset_to_build_plan",
    "benchmark_to_build_plan",
    "operator_review_card",
    "learning_module",
    "concept_map",
    "protocol_map",
    "future_work_map",
    "risk_map",
    "cross_domain_bridge_map",
)

_REQUIRED_DISCONFIRMATION_FIELDS_V1 = (
    "falsification_criterion",
    "missing_evidence_summary",
    "required_source_classes",
    "testing_experiment",
    "safer_explanation",
    "known_constraints",
    "promotion_blockers",
)

_SAFE_DISCOVERY_MEANINGS_V1 = (
    "discovery_of_candidate_direction",
    "discovery_of_overlooked_source_pattern",
    "discovery_of_unfinished_research_path",
    "discovery_of_dormant_idea",
    "discovery_of_cross_domain_bridge",
    "discovery_of_future_work_artifact",
    "discovery_of_language_protocol_candidate",
    "discovery_of_ontology_expansion_request",
)

_FORBIDDEN_DISCOVERY_MEANINGS_V1 = (
    "discovery_as_proven_truth",
    "discovery_as_solved_theory",
    "discovery_as_verified_invention",
    "discovery_as_accepted_evidence",
    "discovery_as_public_science_claim",
    "discovery_as_agi_consciousness_sentience_claim",
    "discovery_as_official_benchmark_result",
    "discovery_as_final_answer",
    "discovery_as_ontology_self_modification",
)

_DENIED_AUTHORITY_FLAGS_V1 = (
    "accepted_evidence_authority",
    "accepted_candidate_authority",
    "proposal_action_authority",
    "final_answer_authority",
    "public_claim_authority",
    "runtime_wiring_authority",
    "provider_call_authority",
    "source_ingestion_authority",
    "memory_mutation_authority",
    "project_mutation_authority",
    "ontology_auto_application_authority",
    "ontology_self_modification_authority",
)

_FORBIDDEN_LANGUAGE_MARKERS_V1 = (
    "accepted evidence",
    "accepted candidate",
    "proposal payload",
    "proposal action",
    "final answer",
    "public claim",
    "official benchmark result",
    "proven truth",
    "solved theory",
    "verified invention",
    "ontology self-modification",
    "agi",
    "consciousness",
    "sentience",
)


def allowed_unfinished_research_signal_types_v1() -> tuple[str, ...]:
    return _ALLOWED_SIGNAL_TYPES_V1


def allowed_unfinished_research_route_types_v1() -> tuple[str, ...]:
    return _ALLOWED_ROUTE_TYPES_V1


def allowed_unfinished_research_source_classes_v1() -> tuple[str, ...]:
    return _ALLOWED_SOURCE_CLASSES_V1


def allowed_unfinished_research_evidence_roles_v1() -> tuple[str, ...]:
    return _ALLOWED_EVIDENCE_ROLES_V1


def allowed_unfinished_research_operator_confirmation_tokens_v1() -> tuple[str, ...]:
    return _ALLOWED_OPERATOR_CONFIRMATION_TOKENS_V1


def allowed_unfinished_research_expansion_recommendations_v1() -> tuple[str, ...]:
    return _ALLOWED_EXPANSION_RECOMMENDATIONS_V1


def allowed_unfinished_research_artifact_types_v1() -> tuple[str, ...]:
    return _ALLOWED_ARTIFACT_TYPES_V1


def required_unfinished_research_disconfirmation_fields_v1() -> tuple[str, ...]:
    return _REQUIRED_DISCONFIRMATION_FIELDS_V1


def safe_unfinished_research_discovery_meanings_v1() -> tuple[str, ...]:
    return _SAFE_DISCOVERY_MEANINGS_V1


def forbidden_unfinished_research_discovery_meanings_v1() -> tuple[str, ...]:
    return _FORBIDDEN_DISCOVERY_MEANINGS_V1


def denied_unfinished_research_authority_flags_v1() -> tuple[str, ...]:
    return _DENIED_AUTHORITY_FLAGS_V1


def forbidden_unfinished_research_language_markers_v1() -> tuple[str, ...]:
    return _FORBIDDEN_LANGUAGE_MARKERS_V1
