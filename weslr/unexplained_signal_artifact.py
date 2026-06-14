from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List
import json

SCHEMA_NAME = "unexplained_signal_artifact"
SCHEMA_VERSION = "v1"

_ARTIFACT_KINDS = {
    "known_science_replay",
    "unexplained_radio_signal",
    "unfinished_research",
    "dormant_path",
    "cross_domain_analogy",
    "anomaly_to_experiment",
    "energy_system_anomaly",
    "language_protocol_emergence",
    "unknown_domain_signal",
    "unsafe_overclaiming_artifact",
    "unknown",
}
_DOMAIN_FAMILIES = {
    "astrophysics",
    "radio_astronomy",
    "energy_systems",
    "materials",
    "biology_medicine",
    "language_communication",
    "ai_cognition",
    "unknown_domain",
}
_SOURCE_BOUNDARIES = {
    "manual_description_only",
    "metadata_only_locator_record",
    "approved_dataset_metadata",
    "approved_known_science_replay",
    "approved_synthetic_signal",
    "approved_local_experiment_metadata",
    "blocked_raw_private_data",
    "blocked_source_content",
    "blocked_unapproved_dataset",
    "unknown",
}
_FALSE_FLAGS = [
    "accepted_evidence_authority",
    "accepted_candidate_authority",
    "proof_claim_authority",
    "discovery_truth_claim_authority",
    "public_science_claim_authority",
    "product_readiness_claim_authority",
    "final_answer_authority",
    "source_ingestion_authority",
    "source_fetch_authority",
    "pdf_fetch_authority",
    "dataset_fetch_authority",
    "github_repo_fetch_authority",
    "provider_model_call_authority",
    "runtime_wiring_authority",
    "chat_responder_edit_authority",
    "ui_voice_integration_authority",
    "database_write_authority",
    "memory_mutation_authority",
    "project_mutation_authority",
    "weslr_io_authority",
    "ontology_auto_application_authority",
    "ontology_self_modification_authority",
    "behavior_pack_promotion_authority",
]
_FORBIDDEN_MARKERS = [
    "WESLR discovered pulsars",
    "WESLR proved",
    "new astrophysics discovery",
    "public science claim",
    "confirmed discovery",
    "accepted evidence",
    "accepted candidate",
    "final answer",
    "AGI",
    "consciousness",
    "sentience",
    "source ingestion authorized",
    "runtime enabled",
]


def _false_flags():
    return {k: False for k in _FALSE_FLAGS}


def _s(v: Any) -> str:
    return "" if v is None else str(v)


def _contains_forbidden(text: str) -> bool:
    low = text.lower()
    return any(m.lower() in low for m in _FORBIDDEN_MARKERS)


def build_unexplained_signal_artifact_v1(**packet: Any) -> Dict[str, Any]:
    result = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "artifact_id": packet.get("artifact_id", "unknown"),
        "artifact_kind": packet.get("artifact_kind", "unknown"),
        "artifact_title": packet.get("artifact_title", ""),
        "domain_family": packet.get("domain_family", "unknown_domain"),
        "source_boundary": packet.get("source_boundary", "unknown"),
        "signal_summary": packet.get("signal_summary", ""),
        "observed_pattern_metadata": deepcopy(packet.get("observed_pattern_metadata", [])),
        "knowns": deepcopy(packet.get("knowns", [])),
        "unknowns": deepcopy(packet.get("unknowns", [])),
        "candidate_explanations": deepcopy(packet.get("candidate_explanations", [])),
        "alternative_explanations": deepcopy(packet.get("alternative_explanations", [])),
        "disconfirmation_tests": deepcopy(packet.get("disconfirmation_tests", [])),
        "required_evidence_classes": deepcopy(packet.get("required_evidence_classes", [])),
        "missing_evidence": deepcopy(packet.get("missing_evidence", [])),
        "cross_domain_pattern_candidates": deepcopy(packet.get("cross_domain_pattern_candidates", [])),
        "natural_pattern_analogies": deepcopy(packet.get("natural_pattern_analogies", [])),
        "engineering_pattern_analogies": deepcopy(packet.get("engineering_pattern_analogies", [])),
        "possible_experiment_paths": deepcopy(packet.get("possible_experiment_paths", [])),
        "possible_tooling_paths": deepcopy(packet.get("possible_tooling_paths", [])),
        "possible_product_or_artifact_paths": deepcopy(packet.get("possible_product_or_artifact_paths", [])),
        "owner_review_required": bool(packet.get("owner_review_required", False)),
        "expert_review_required": bool(packet.get("expert_review_required", False)),
        "blocked_claims": deepcopy(packet.get("blocked_claims", [])),
        "denied_authority_flags": _false_flags(),
        "next_work_lanes": deepcopy(packet.get("next_work_lanes", [])),
        "safe_forward_plan": packet.get("safe_forward_plan", ""),
        "blocked_labels": deepcopy(packet.get("blocked_labels", [])),
        "safe_metadata_summary": packet.get("safe_metadata_summary", ""),
        "final_judgment": packet.get("final_judgment", ""),
    }
    for k, v in (packet.get("denied_authority_flags") or {}).items():
        if k in result["denied_authority_flags"]:
            result["denied_authority_flags"][k] = bool(v)
    return result


def validate_unexplained_signal_artifact_v1(packet: Dict[str, Any]) -> bool:
    required = [
        "schema_name","schema_version","artifact_id","artifact_kind","artifact_title",
        "domain_family","source_boundary","signal_summary","observed_pattern_metadata",
        "knowns","unknowns","candidate_explanations","alternative_explanations",
        "disconfirmation_tests","required_evidence_classes","missing_evidence",
        "cross_domain_pattern_candidates","natural_pattern_analogies","engineering_pattern_analogies",
        "possible_experiment_paths","possible_tooling_paths","possible_product_or_artifact_paths",
        "owner_review_required","expert_review_required","blocked_claims","denied_authority_flags",
        "next_work_lanes","safe_forward_plan","blocked_labels","safe_metadata_summary","final_judgment",
    ]
    if any(k not in packet for k in required):
        return False
    if ".weslr" in _s(packet.get("artifact_id")) or ".weslr" in _s(packet.get("source_boundary")):
        return False
    if packet.get("artifact_kind") not in _ARTIFACT_KINDS:
        return False
    if packet.get("domain_family") not in _DOMAIN_FAMILIES:
        return False
    if packet.get("source_boundary") not in _SOURCE_BOUNDARIES:
        return False
    if not packet.get("owner_review_required"):
        return False
    blocked_claims = packet.get("blocked_claims") or []
    if not blocked_claims or not packet.get("safe_forward_plan") or not packet.get("final_judgment"):
        return False
    if any(any(marker in _s(claim).lower() for marker in ["accepted evidence", "accepted candidate"]) for claim in blocked_claims):
        return False
    if not packet.get("disconfirmation_tests") or not packet.get("required_evidence_classes"):
        return False
    flags = packet.get("denied_authority_flags") or {}
    for k in _FALSE_FLAGS:
        if flags.get(k) is not False:
            return False
    text_fields = [
        _s(packet.get("artifact_title")), _s(packet.get("signal_summary")),
        _s(packet.get("safe_metadata_summary")), _s(packet.get("safe_forward_plan")),
    ]
    if any(_contains_forbidden(t) for t in text_fields):
        return False
    if any(_contains_forbidden(json.dumps(v, default=str)) for v in [
        packet.get("candidate_explanations"), packet.get("alternative_explanations"),
        packet.get("possible_product_or_artifact_paths"), packet.get("next_work_lanes"),
    ]):
        return False
    if packet.get("artifact_kind") == "unknown" and not any(
        phrase in " ".join(map(_s, packet.get("blocked_claims", []))).lower() for phrase in ["blocked", "review", "unsafe"]
    ):
        return False
    return True


def summarize_unexplained_signal_artifact_v1(packet: Dict[str, Any]) -> str:
    return (
        f"{packet.get('artifact_id','unknown')}|{packet.get('artifact_kind','unknown')}|"
        f"{packet.get('domain_family','unknown_domain')}|{packet.get('source_boundary','unknown')}|"
        f"k={len(packet.get('knowns', []))} u={len(packet.get('unknowns', []))} "
        f"c={len(packet.get('candidate_explanations', []))} a={len(packet.get('alternative_explanations', []))} "
        f"d={len(packet.get('disconfirmation_tests', []))} e={len(packet.get('required_evidence_classes', []))} "
        f"x={len(packet.get('cross_domain_pattern_candidates', []))} owner={packet.get('owner_review_required', False)} "
        f"expert={packet.get('expert_review_required', False)} blocked={bool(packet.get('blocked_claims'))} "
        f"judgment={packet.get('final_judgment','')} lane={packet.get('next_work_lanes',[{}])[0].get('lane_id','') if packet.get('next_work_lanes') else ''}"
    )


def render_unexplained_signal_artifact_markdown_v1(packet: Dict[str, Any]) -> str:
    lines = [
        f"# {packet.get('artifact_title','Unexplained Signal Artifact')}",
        f"- Artifact ID: {packet.get('artifact_id','unknown')}",
        f"- Artifact kind: {packet.get('artifact_kind','unknown')}",
        f"- Domain family: {packet.get('domain_family','unknown_domain')}",
        f"- Source boundary: {packet.get('source_boundary','unknown')}",
        f"- Signal summary: {packet.get('signal_summary','')}",
        f"- Knowns: {', '.join(packet.get('knowns', [])) or 'none'}", 
        f"- Unknowns: {', '.join(packet.get('unknowns', [])) or 'none'}",
        f"- Candidate explanations: {', '.join(packet.get('candidate_explanations', [])) or 'none'}",
        f"- Alternative explanations: {', '.join(packet.get('alternative_explanations', [])) or 'none'}",
        f"- Disconfirmation tests: {', '.join(packet.get('disconfirmation_tests', [])) or 'none'}",
        f"- Required evidence classes: {', '.join(packet.get('required_evidence_classes', [])) or 'none'}",
        f"- Cross-domain patterns: {', '.join(packet.get('cross_domain_pattern_candidates', [])) or 'none'}",
        f"- Natural analogies: {', '.join(packet.get('natural_pattern_analogies', [])) or 'none'}",
        f"- Engineering analogies: {', '.join(packet.get('engineering_pattern_analogies', [])) or 'none'}",
        f"- Possible experiment paths: {', '.join(packet.get('possible_experiment_paths', [])) or 'none'}",
        f"- Possible tooling paths: {', '.join(packet.get('possible_tooling_paths', [])) or 'none'}",
        f"- Possible product/artifact paths: {', '.join(packet.get('possible_product_or_artifact_paths', [])) or 'none'}",
        f"- Blocked claims count: {len(packet.get('blocked_claims', []))}",
        f"- Denied authority flags: {', '.join([k for k,v in (packet.get('denied_authority_flags') or {}).items() if v is False])}",
        f"- Next work lanes: {', '.join([lane.get('lane_id','') for lane in packet.get('next_work_lanes', [])]) or 'none'}",
        f"- Safe forward plan: {packet.get('safe_forward_plan','')}",
        f"- Final judgment: {packet.get('final_judgment','')}",
    ]
    return "\n".join(lines)


def to_unexplained_signal_artifact_json_safe_v1(packet: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(json.dumps(packet, default=str))


def _lane(lane_id, lane_type, title, why, blocked_until, expected_output_artifact, final_judgments, forbidden):
    return {
        "lane_id": lane_id,
        "lane_type": lane_type,
        "lane_title": title,
        "why_recommended": why,
        "depends_on": ["operator review"],
        "owner_review_required": True,
        "expert_review_required": lane_type in {"run", "operator_decision"},
        "blocked_until": blocked_until,
        "allowed_actions": ["review", "design"],
        "forbidden_actions": forbidden,
        "validation_commands": ["git diff --check"],
        "protected_file_checks": ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
        "expected_output_artifact": expected_output_artifact,
        "final_judgment_options": final_judgments,
    }


def build_initial_unexplained_signal_artifact_examples_v1() -> List[Dict[str, Any]]:
    base_flags = _false_flags()
    examples: List[Dict[str, Any]] = []
    examples.append(build_unexplained_signal_artifact_v1(
        artifact_id="pulsar_known_science_replay",
        artifact_kind="known_science_replay",
        artifact_title="Pulsar Known-Science Replay Artifact",
        domain_family="radio_astronomy",
        source_boundary="approved_known_science_replay",
        signal_summary="Unexpected pulsar-like signal replay for known-science pattern review.",
        observed_pattern_metadata=["unexpected signal", "sky-location behavior", "repeatability"],
        knowns=["instrument/noise/local-source checks", "timing/periodicity checks"],
        unknowns=["source classification", "alternative explanations"],
        candidate_explanations=["pulsar-like astrophysical source"],
        alternative_explanations=["instrument artifact", "local interference"],
        disconfirmation_tests=["repeatability", "sky-location behavior", "multi-source comparison"],
        required_evidence_classes=["repeat observations", "timing evidence", "source separation"],
        missing_evidence=["final known explanation only after evidence"],
        cross_domain_pattern_candidates=["anomaly-to-experiment"],
        natural_pattern_analogies=["periodic natural source"],
        engineering_pattern_analogies=["noise filtering", "signal verification"],
        possible_experiment_paths=["repeat observation campaign"],
        possible_tooling_paths=["metadata-only locator review"],
        possible_product_or_artifact_paths=["known-science replay artifact"],
        owner_review_required=True,
        expert_review_required=True,
        blocked_claims=["WESLR discovered pulsars", "new astrophysics discovery claim", "proof claim", "public science claim", "source ingestion without approval"],
        denied_authority_flags=base_flags,
        next_work_lanes=[_lane("REVIEW_PULSAR_REPLAY_V1", "review", "Review pulsar replay", "known-science replay only", ["owner review"], "docs/pulsar-review.md", ["review_only", "blocked_claims"] , ["source_ingestion", "proof_claim", "public_science_claim"] )],
        safe_forward_plan="Review only; compare against known pulsar behavior and blocked claims.",
        blocked_labels=["no_new_discovery_claim"],
        safe_metadata_summary="Known-science replay artifact with explicit anti-discovery posture.",
        final_judgment="review_only",
    ))
    examples.append(build_unexplained_signal_artifact_v1(
        artifact_id="unexplained_radio_transient_review_only",
        artifact_kind="unexplained_radio_signal",
        artifact_title="Unexplained Radio Transient Review-Only Artifact",
        domain_family="radio_astronomy",
        source_boundary="metadata_only_locator_record",
        signal_summary="Metadata-only radio transient requires disconfirmation and evidence planning.",
        observed_pattern_metadata=["transient", "metadata-only"],
        knowns=["location metadata"],
        unknowns=["source class", "repeatability"],
        candidate_explanations=["astrophysical transient", "instrument/noise artifact"],
        alternative_explanations=["local source", "processing artifact"],
        disconfirmation_tests=["repeatability", "local-source check"],
        required_evidence_classes=["follow-up metadata", "repeat observation"],
        missing_evidence=["source content"],
        cross_domain_pattern_candidates=["dormant_path"],
        natural_pattern_analogies=["transient natural event"],
        engineering_pattern_analogies=["fault diagnosis"],
        possible_experiment_paths=["metadata-only follow-up"],
        possible_tooling_paths=["MLCF routing"],
        possible_product_or_artifact_paths=["review-only artifact"],
        owner_review_required=True,
        expert_review_required=False,
        blocked_claims=["no source ingestion", "no final answer"],
        denied_authority_flags=base_flags,
        next_work_lanes=[_lane("PLAN_UNEXPLAINED_RADIO_TRANSIENT_V1", "design", "Plan review lane", "requires disconfirmation", ["review"], "docs/transient-plan.md", ["review_only"], ["source_ingestion", "final_answer"] )],
        safe_forward_plan="Review-only metadata artifact; no source ingestion.",
        blocked_labels=["review_only"],
        safe_metadata_summary="Review-only radio transient artifact.",
        final_judgment="review_only",
    ))
    examples.append(build_unexplained_signal_artifact_v1(
        artifact_id="energy_system_anomaly_artifact",
        artifact_kind="energy_system_anomaly",
        artifact_title="Energy-System Anomaly Artifact",
        domain_family="energy_systems",
        source_boundary="metadata_only_locator_record",
        signal_summary="Energy-system metadata anomaly for tomorrow's controlled true-run compatibility.",
        observed_pattern_metadata=["curtailment", "storage coordination gap"],
        knowns=["grid constraints", "demand response"],
        unknowns=["coordination failure mode", "benchmark gap"],
        candidate_explanations=["curtailment coordination gap", "storage dispatch mismatch"],
        alternative_explanations=["measurement gap", "regulatory interface issue"],
        disconfirmation_tests=["benchmark comparison", "repeat timing check"],
        required_evidence_classes=["metadata-only locator", "operator review"],
        missing_evidence=["source content"],
        cross_domain_pattern_candidates=["cross-domain resonance"],
        natural_pattern_analogies=["system oscillation"],
        engineering_pattern_analogies=["grid-control loop"],
        possible_experiment_paths=["metadata-only follow-up lane"],
        possible_tooling_paths=["artifact forward work plan"],
        possible_product_or_artifact_paths=["future work artifact candidate"],
        owner_review_required=True,
        expert_review_required=False,
        blocked_claims=["public science claim", "final answer"],
        denied_authority_flags=base_flags,
        next_work_lanes=[_lane("PLAN_WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_V1", "design", "Plan third controlled true run", "tomorrow compatible energy-system metadata", ["owner approval"], "docs/WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_PLAN_V1.md", ["ready_for_review"], ["source_ingestion", "final_answer"] )],
        safe_forward_plan="Wrap metadata-only energy-system signals for a future controlled true run.",
        blocked_labels=["no_source_ingestion"],
        safe_metadata_summary="Energy-system anomaly artifact ready for governed follow-up.",
        final_judgment="ready_for_review",
    ))
    examples.append(build_unexplained_signal_artifact_v1(
        artifact_id="language_protocol_emergence_artifact",
        artifact_kind="language_protocol_emergence",
        artifact_title="Language/Protocol Emergence Artifact",
        domain_family="language_communication",
        source_boundary="manual_description_only",
        signal_summary="Unexplained language/protocol structure noted in manual description.",
        observed_pattern_metadata=["emergent structure", "protocol emergence"],
        knowns=["manual description"],
        unknowns=["translation limits", "cross-system meaning"],
        candidate_explanations=["protocol regularity", "language-family constraint"],
        alternative_explanations=["annotation bias", "insufficient ontology"],
        disconfirmation_tests=["translation failure test", "ontology gap test"],
        required_evidence_classes=["review-only metadata", "operator review"],
        missing_evidence=["universal-language support"],
        cross_domain_pattern_candidates=["communication resonance"],
        natural_pattern_analogies=["emergent grammar"],
        engineering_pattern_analogies=["protocol standardization"],
        possible_experiment_paths=["manual review lane"],
        possible_tooling_paths=["cross-domain scout"],
        possible_product_or_artifact_paths=["protocol review artifact"],
        owner_review_required=True,
        expert_review_required=False,
        blocked_claims=["universal-language claim", "WESLR understands all communication", "final answer"],
        denied_authority_flags=base_flags,
        next_work_lanes=[_lane("REVIEW_LANGUAGE_PROTOCOL_EMERGENCE_V1", "review", "Review language/protocol emergence", "review-only posture", ["owner review"], "docs/language-protocol-review.md", ["review_only"], ["source_ingestion", "final_answer"] )],
        safe_forward_plan="Review-only; no universal-comprehension claim.",
        blocked_labels=["no_universal_language_claim"],
        safe_metadata_summary="Language/protocol emergence artifact with blocked universal-language claims.",
        final_judgment="review_only",
    ))
    unsafe = build_unexplained_signal_artifact_v1(
        artifact_id="unsafe_overclaiming_artifact",
        artifact_kind="unsafe_overclaiming_artifact",
        artifact_title="Unsafe Overclaiming Artifact",
        domain_family="unknown_domain",
        source_boundary="blocked_source_content",
        signal_summary="WESLR discovered pulsars and proved a new astrophysics discovery.",
        observed_pattern_metadata=["public science claim"],
        knowns=["none"],
        unknowns=["unknown"],
        candidate_explanations=["accepted evidence"],
        alternative_explanations=["none"],
        disconfirmation_tests=["review"],
        required_evidence_classes=["review"],
        missing_evidence=["none"],
        cross_domain_pattern_candidates=["none"],
        natural_pattern_analogies=["none"],
        engineering_pattern_analogies=["none"],
        possible_experiment_paths=["none"],
        possible_tooling_paths=["none"],
        possible_product_or_artifact_paths=["none"],
        owner_review_required=True,
        expert_review_required=True,
        blocked_claims=[],
        denied_authority_flags=base_flags,
        next_work_lanes=[_lane("BLOCK_UNSAFE_OVERCLAIMING_V1", "operator_decision", "Block unsafe overclaiming", "unsafe overclaim", ["owner review"], "docs/blocked.md", ["blocked"], ["final_answer", "source_ingestion"] )],
        safe_forward_plan="Blocked unsafe overclaiming artifact.",
        blocked_labels=["unsafe_overclaiming"],
        safe_metadata_summary="Unsafe overclaiming artifact for blocking validation.",
        final_judgment="blocked",
    )
    examples.append(unsafe)
    return examples
