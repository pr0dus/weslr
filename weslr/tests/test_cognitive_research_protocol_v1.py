from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.cognitive_research_protocol as protocol
from weslr.cognitive_research_protocol import (
    ALLOWED_COGNITIVE_RESEARCH_BOUNDARY_STATUSES_V1,
    ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1,
    ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1,
    ALLOWED_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1,
    ALLOWED_COGNITIVE_RESEARCH_MODES_V1,
    ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1,
    allowed_cognitive_research_engine_families_v1,
    allowed_cognitive_research_engine_names_v1,
    allowed_cognitive_research_llm_helper_roles_v1,
    allowed_cognitive_research_modes_v1,
    allowed_cognitive_research_public_claim_statuses_v1,
    build_cognitive_research_run_v1,
    build_default_cognitive_research_denied_authority_v1,
    build_initial_cognitive_research_examples_v1,
    classify_cognitive_research_engine_family_v1,
    summarize_cognitive_research_run_v1,
    to_cognitive_research_json_safe_v1,
    validate_cognitive_research_run_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "cognitive_research_protocol.py"
REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_NEW_FILES = {
    "weslr/cognitive_research_protocol.py",
    "weslr/tests/test_cognitive_research_protocol_v1.py",
    "docs/WESLR_COGNITIVE_RESEARCH_PROTOCOL_HELPERS_IMPLEMENTATION_REPORT_V1.md",
    "weslr/tests/release_gate_v1.py",
}
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}


BASE_PACKET = build_cognitive_research_run_v1(
    {
        "engine_name": "UNKNOWN_ENGINE",
        "engine_family": "unknown",
        "research_mode": "exploratory",
        "domain": "signal interpretation",
        "domain_subtype": "hidden-rule discovery",
        "system_level": "component",
        "artifact_scale": "bounded artifact",
        "source_scope": "metadata_only",
        "input_artifact_ref": "artifact:unknown-base-001",
        "input_artifact_type": "report",
        "input_summary": "Metadata-only observation set for hidden-rule discovery.",
        "hypotheses": ["A hidden rule may explain the contradiction cloud."],
        "probes": ["observe -> predict -> reveal -> correct"],
        "compressed_lesson": "Unknowns should stay unknown until probes earn them.",
    }
)


def _packet(engine_name: str = "UNKNOWN_ENGINE", engine_family: str | None = None, **overrides):
    payload = deepcopy(BASE_PACKET)
    payload.update(
        {
            "engine_name": engine_name,
            "engine_family": engine_family if engine_family is not None else classify_cognitive_research_engine_family_v1(engine_name) or "unknown",
        }
    )
    payload.update(overrides)
    return build_cognitive_research_run_v1(payload)


@pytest.mark.parametrize(
    "getter, expected",
    [
        (allowed_cognitive_research_engine_families_v1, ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1),
        (allowed_cognitive_research_engine_names_v1, ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1),
        (allowed_cognitive_research_modes_v1, ALLOWED_COGNITIVE_RESEARCH_MODES_V1),
        (allowed_cognitive_research_public_claim_statuses_v1, ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1),
        (allowed_cognitive_research_llm_helper_roles_v1, ALLOWED_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1),
    ],
)
def test_allowed_enums_match_constants(getter, expected):
    assert getter() == expected


@pytest.mark.parametrize(
    "engine_name, expected_family",
    [
        ("UNKNOWN_ENGINE", "unknown"),
        ("RAW_SIGNAL_CARTOGRAPHER", "raw-signal"),
        ("UNINTELLIGIBLE_OUTPUT_ANALYZER", "raw-signal"),
        ("MUTABLE_AXIOM_MATH_ENGINE", "math"),
        ("GAP_CARTOGRAPHER", "gap"),
        ("CHEMICAL_SPACE_CARTOGRAPHER", "chemical/material"),
        ("BIOLOGICAL_SYSTEMS_ANALYZER", "biological"),
        ("MEDICAL_REASONING_BOUNDARY_ENGINE", "medical-boundary"),
        ("CYBER_RESILIENCE_ENGINE", "cyber-resilience"),
        ("LEGAL_GOVERNANCE_GAP_ENGINE", "legal/governance"),
    ],
)
def test_engine_family_classification_is_deterministic(engine_name, expected_family):
    assert classify_cognitive_research_engine_family_v1(engine_name) == expected_family
    assert classify_cognitive_research_engine_family_v1(engine_name) == expected_family


@pytest.mark.parametrize(
    "key",
    [
        "runtime_authority",
        "runtime_execution_authority",
        "tool_authority",
        "provider_authority",
        "search_authority",
        "persistence_authority",
        "dot_weslr_authority",
        "public_export_authority",
        "answer_authority",
        "prediction_authority",
        "official_evaluation_authority",
        "proof_authority",
        "solution_authority",
        "llm_authority",
        "diagnosis_authority",
        "treatment_authority",
        "exploit_authority",
        "malware_authority",
        "credential_theft_authority",
        "investment_authority",
        "trading_authority",
        "legal_authority",
        "memory_mutation_authority",
        "project_mutation_authority",
        "external_action_authority",
    ],
)
def test_default_denied_authority_is_complete_and_false(key):
    denied = build_default_cognitive_research_denied_authority_v1()
    assert key in denied
    assert denied[key] is False


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("UNKNOWN_ENGINE", "unknown"),
        ("RAW_SIGNAL_CARTOGRAPHER", "raw-signal"),
        ("UNINTELLIGIBLE_OUTPUT_ANALYZER", "raw-signal"),
        ("MUTABLE_AXIOM_MATH_ENGINE", "math"),
        ("GAP_CARTOGRAPHER", "gap"),
        ("CHEMICAL_SPACE_CARTOGRAPHER", "chemical/material"),
        ("BIOLOGICAL_SYSTEMS_ANALYZER", "biological"),
        ("MEDICAL_REASONING_BOUNDARY_ENGINE", "medical-boundary"),
        ("CYBER_RESILIENCE_ENGINE", "cyber-resilience"),
        ("LEGAL_GOVERNANCE_GAP_ENGINE", "legal/governance"),
    ],
)
def test_valid_packets_for_required_engines_and_sensitive_families(engine_name, engine_family):
    packet = _packet(
        engine_name=engine_name,
        engine_family=engine_family,
        public_claim_status="blocked_internal_only",
        llm_helper_role="helper",
        non_actionable_research_only=True,
        simulation_before_real_world=True,
        safety_boundary={"scope": engine_family, "metadata_only": True, "non_actionable": True},
        forbidden_action_notes=[],
        hazard_flags=[],
        observations=["bounded observation"],
        extracted_signals=["signal label"],
        motif_candidates=["motif label"],
        operator_candidates=["operator label"],
        invariant_candidates=["invariant label"],
        hypotheses=["A bounded internal hypothesis may be interesting."],
        predictions=["branch A"],
        confidence_map={"confidence": "medium"},
        uncertainty_map={"uncertainty": "bounded"},
        constraint_map={"runtime": "denied"},
        validation_route=["metadata_only_validation"],
        source_requirements={"provenance_required": True},
        safe_metadata={"safe": True, "metadata_only": True},
    )
    validation = validate_cognitive_research_run_v1(packet)
    summary = summarize_cognitive_research_run_v1(packet)

    assert validation["blocked"] is False
    assert validation["classification"] == engine_name
    assert summary["blocked"] is False
    assert summary["summary_text"].startswith("Cognitive research run:")


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("CHEMICAL_SPACE_CARTOGRAPHER", "chemical/material"),
        ("BIOLOGICAL_SYSTEMS_ANALYZER", "biological"),
        ("MEDICAL_REASONING_BOUNDARY_ENGINE", "medical-boundary"),
        ("CYBER_RESILIENCE_ENGINE", "cyber-resilience"),
        ("LEGAL_GOVERNANCE_GAP_ENGINE", "legal/governance"),
    ],
)
def test_sensitive_domains_require_safety_boundary(engine_name, engine_family):
    packet = _packet(
        engine_name=engine_name,
        engine_family=engine_family,
        safety_boundary={},
        public_claim_status="blocked_internal_only",
        llm_helper_role="helper",
    )
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "missing_safety_boundary" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("UNKNOWN_ENGINE", "unknown"),
        ("RAW_SIGNAL_CARTOGRAPHER", "raw-signal"),
        ("MUTABLE_AXIOM_MATH_ENGINE", "math"),
        ("GAP_CARTOGRAPHER", "gap"),
    ],
)
def test_valid_packets_for_core_shared_protocol_engines(engine_name, engine_family):
    packet = _packet(engine_name=engine_name, engine_family=engine_family)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is False
    assert validation["classification"] == engine_name


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("UNKNOWN_ENGINE", "math"),
        ("RAW_SIGNAL_CARTOGRAPHER", "math"),
        ("MUTABLE_AXIOM_MATH_ENGINE", "raw-signal"),
        ("GAP_CARTOGRAPHER", "unknown"),
    ],
)
def test_engine_family_mismatch_fails(engine_name, engine_family):
    packet = _packet(engine_name=engine_name, engine_family=engine_family)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "engine_family_mismatch" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("UNKNOWN_ENGINE", "unknown"),
        ("RAW_SIGNAL_CARTOGRAPHER", "raw-signal"),
    ],
)
def test_unknown_engine_name_fails(engine_name, engine_family):
    packet = _packet(engine_name="NOT_A_REAL_ENGINE", engine_family=engine_family)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "unknown_engine_name" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("runtime_authority", True),
        ("provider_authority", True),
        ("dot_weslr_authority", True),
    ],
)
def test_granted_runtime_provider_and_dot_weslr_authority_fails(field, value):
    packet = _packet()
    packet["denied_authority"][field] = value
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert any(label == f"denied_authority_granted_{field}" for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "mutation",
    [
        {"denied_authority": None},
        {"denied_authority": {}},
    ],
)
def test_missing_denied_authority_fails(mutation):
    packet = _packet()
    packet.update(mutation)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "missing_denied_authority" in validation["blocked_labels"] or "invalid_denied_authority_schema" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "mutation",
    [
        {"llm_helper_role": "authority"},
        {"denied_authority": {**build_default_cognitive_research_denied_authority_v1(), "llm_authority": True}},
    ],
)
def test_llm_treated_as_authority_fails(mutation):
    packet = _packet()
    packet.update(mutation)
    if isinstance(packet.get("denied_authority"), dict):
        packet["denied_authority"].setdefault("llm_authority", False)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True


@pytest.mark.parametrize(
    "summary_text",
    [
        "breakthrough proof solution certified public-ready",
        "official certification solved breakthrough",
    ],
)
def test_public_breakthrough_claim_fails(summary_text):
    packet = _packet(public_claim_status="allowed_external_export", input_summary=summary_text)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "public_claim_language" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "summary_text",
    [
        "raw private data hidden system prompt",
        "private mechanism text with raw project data",
    ],
)
def test_raw_private_text_fails(summary_text):
    packet = _packet(input_summary=summary_text)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "raw_private_or_hidden_text" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "notes",
    [
        ["hidden system prompt"],
        ["hidden prompt"],
    ],
)
def test_hidden_prompt_fails(notes):
    packet = _packet(forbidden_action_notes=notes)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "raw_private_or_hidden_text" in validation["blocked_labels"] or "hidden" in " ".join(validation["blocked_labels"])


@pytest.mark.parametrize(
    "summary_text",
    [
        "step-by-step procedure to synthesize malware",
        "how to exploit a target with a multi-step attack chain",
    ],
)
def test_dangerous_procedure_fails(summary_text):
    packet = _packet(input_summary=summary_text)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "dangerous_procedural_language" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("CHEMICAL_SPACE_CARTOGRAPHER", "chemical/material"),
        ("BIOLOGICAL_SYSTEMS_ANALYZER", "biological"),
        ("MEDICAL_REASONING_BOUNDARY_ENGINE", "medical-boundary"),
        ("CYBER_RESILIENCE_ENGINE", "cyber-resilience"),
        ("LEGAL_GOVERNANCE_GAP_ENGINE", "legal/governance"),
    ],
)
def test_sensitive_domain_without_safety_boundary_fails(engine_name, engine_family):
    packet = _packet(engine_name=engine_name, engine_family=engine_family, safety_boundary={})
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "missing_safety_boundary" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("CHEMICAL_SPACE_CARTOGRAPHER", "chemical/material"),
        ("BIOLOGICAL_SYSTEMS_ANALYZER", "biological"),
        ("MEDICAL_REASONING_BOUNDARY_ENGINE", "medical-boundary"),
        ("CYBER_RESILIENCE_ENGINE", "cyber-resilience"),
        ("LEGAL_GOVERNANCE_GAP_ENGINE", "legal/governance"),
    ],
)
def test_hazardous_action_without_non_actionable_flag_fails(engine_name, engine_family):
    packet = _packet(
        engine_name=engine_name,
        engine_family=engine_family,
        non_actionable_research_only=False,
        forbidden_action_notes=["step-by-step procedure"],
    )
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "non_actionable_research_only_false" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("UNKNOWN_ENGINE", "unknown"),
        ("RAW_SIGNAL_CARTOGRAPHER", "raw-signal"),
        ("MUTABLE_AXIOM_MATH_ENGINE", "math"),
        ("GAP_CARTOGRAPHER", "gap"),
    ],
)
def test_safe_radical_internal_hypothesis_passes(engine_name, engine_family):
    packet = _packet(
        engine_name=engine_name,
        engine_family=engine_family,
        research_mode="internal_hypothesis",
        public_claim_status="blocked_internal_only",
        llm_helper_role="helper",
        hypotheses=["A strange contradiction cloud may encode a new operator family."],
        probes=["interpret the contradiction cloud"],
        non_actionable_research_only=True,
        safety_boundary={"scope": "metadata_only", "non_actionable": True},
    )
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is False


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("UNKNOWN_ENGINE", "unknown"),
        ("RAW_SIGNAL_CARTOGRAPHER", "raw-signal"),
    ],
)
def test_massive_artifact_ref_passes_without_raw_storage(engine_name, engine_family):
    massive_ref = "artifact:" + ("A" * 5000)
    packet = _packet(
        engine_name=engine_name,
        engine_family=engine_family,
        input_artifact_ref=massive_ref,
        input_summary="Metadata-only summary for a large artifact reference.",
        source_scope="metadata_only",
    )
    validation = validate_cognitive_research_run_v1(packet)
    summary = summarize_cognitive_research_run_v1(packet)
    assert validation["blocked"] is False
    assert len(summary["summary_text"]) <= 320
    assert "artifact:" in summary["summary_text"]


@pytest.mark.parametrize(
    "packet_builder",
    [
        lambda: _packet(),
        lambda: _packet(engine_name="RAW_SIGNAL_CARTOGRAPHER", engine_family="raw-signal"),
    ],
)
def test_json_safe_copy_works(packet_builder):
    value = to_cognitive_research_json_safe_v1({"items": {1, 2}, "tuple": ("a", "b"), "custom": object()})
    assert value["items"] in ([1, 2], [2, 1])
    json.dumps(value, sort_keys=True)
    packet = packet_builder()
    safe = to_cognitive_research_json_safe_v1(packet)
    json.dumps(safe, sort_keys=True)


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("UNKNOWN_ENGINE", "unknown"),
        ("RAW_SIGNAL_CARTOGRAPHER", "raw-signal"),
        ("UNINTELLIGIBLE_OUTPUT_ANALYZER", "raw-signal"),
        ("MUTABLE_AXIOM_MATH_ENGINE", "math"),
        ("GAP_CARTOGRAPHER", "gap"),
    ],
)
def test_summary_is_safe_and_bounded(engine_name, engine_family):
    packet = _packet(engine_name=engine_name, engine_family=engine_family)
    summary = summarize_cognitive_research_run_v1(packet)
    assert summary["summary_text"].startswith("Cognitive research run:") or summary["summary_text"].startswith("Blocked cognitive research run:")
    assert len(summary["summary_text"]) <= 320
    assert "raw private" not in summary["summary_text"].lower()
    assert "hidden prompt" not in summary["summary_text"].lower()


def test_examples_include_all_major_families():
    examples = build_initial_cognitive_research_examples_v1()
    families = {example["engine_family"] for example in examples}
    assert families == set(ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1)
    assert all(example["engine_name"] in ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1 for example in examples)
    assert all(example["public_claim_status"] == "blocked_internal_only" for example in examples)
    assert all(example["non_actionable_research_only"] is True for example in examples)


def test_static_source_scan_confirms_no_forbidden_imports_or_side_effects():
    text = HELPER_PATH.read_text()
    forbidden_patterns = [
        "open(",
        "subprocess",
        "requests",
        "socket",
        "." + "weslr",
        "entity" + "_" + "graph",
        "chat" + "_" + "responder",
        "dialogue",
        "chat" + "_" + "ui",
        "importlib",
    ]
    for forbidden in forbidden_patterns:
        assert forbidden not in text


def test_protected_file_drift_absent():
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--short", "--untracked-files=no"],
        check=True,
        capture_output=True,
        text=True,
    )
    changed = {
        line.split(maxsplit=1)[1]
        for line in completed.stdout.splitlines()
        if line.strip()
    }
    assert changed.issubset(ALLOWED_NEW_FILES)
    assert not changed.intersection(PROTECTED_FILES)
