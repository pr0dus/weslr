"""Generic calculation assurance types for non-self-trusting computation.

This module defines data structures and verification primitives for
calculation assurance. It does not perform any specific calculation.

Architectural principle:
A calculation engine must never be its own authority.
Every result must be independently verifiable through a materially
different implementation.

Stable statuses:
- verified
- rejected_by_invariant
- proposer_verifier_disagreement
- verifier_unavailable
- invalid_input
- insufficient_evidence
- abstain_due_to_verification_disagreement
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


# Stable verification statuses
VERIFIED = "verified"
REJECTED_BY_INVARIANT = "rejected_by_invariant"
PROPOSER_VERIFIER_DISAGREEMENT = "proposer_verifier_disagreement"
VERIFIER_UNAVAILABLE = "verifier_unavailable"
INVALID_INPUT = "invalid_input"
INSUFFICIENT_EVIDENCE = "insufficient_evidence"
ABSTAIN_DUE_TO_VERIFICATION_DISAGREEMENT = "abstain_due_to_verification_disagreement"

ALL_STATUSES = frozenset({
    VERIFIED,
    REJECTED_BY_INVARIANT,
    PROPOSER_VERIFIER_DISAGREEMENT,
    VERIFIER_UNAVAILABLE,
    INVALID_INPUT,
    INSUFFICIENT_EVIDENCE,
    ABSTAIN_DUE_TO_VERIFICATION_DISAGREEMENT,
})


@dataclass(frozen=True)
class CalculationInput:
    """Normalized input to a calculation."""
    calculation_type: str
    parameters: dict[str, Any] = field(default_factory=dict)
    formulas: list[str] = field(default_factory=list)
    coefficients: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def normalized_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)


@dataclass(frozen=True)
class CalculationResult:
    """Result from a single calculation engine."""
    engine_name: str
    calculation_type: str
    inputs: CalculationInput
    result: dict[str, Any]
    status: str = VERIFIED

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_name": self.engine_name,
            "calculation_type": self.calculation_type,
            "inputs": self.inputs.to_dict(),
            "result": self.result,
            "status": self.status,
        }


@dataclass(frozen=True)
class VerificationResult:
    """Result from an independent verifier."""
    verifier_name: str
    calculation_type: str
    inputs: CalculationInput
    proposer_result: dict[str, Any]
    verifier_result: dict[str, Any]
    agreement: bool
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier_name": self.verifier_name,
            "calculation_type": self.calculation_type,
            "inputs": self.inputs.to_dict(),
            "proposer_result": self.proposer_result,
            "verifier_result": self.verifier_result,
            "agreement": self.agreement,
            "status": self.status,
        }


@dataclass(frozen=True)
class InvariantResult:
    """Result from an invariant check."""
    invariant_name: str
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "invariant_name": self.invariant_name,
            "passed": self.passed,
            "details": self.details,
        }


def _canonical_json(obj: Any) -> str:
    """Serialize to canonical JSON with sorted keys and stable separators."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CalculationCertificate:
    """Complete certificate for a verified calculation.

    The certificate hash is computed from canonical JSON of all fields
    except certificate_sha256 itself.
    """
    calculation_id: str
    calculation_type: str
    normalized_inputs: dict[str, Any]
    proposer_name: str
    proposer_result: dict[str, Any]
    verifier_name: str
    verifier_result: dict[str, Any]
    invariant_results: list[dict[str, Any]]
    agreement: bool
    final_status: str
    exact_arithmetic: bool
    tool_versions: dict[str, str]
    source_paths: list[str]
    source_hashes: list[str]
    timestamp_utc: str
    certificate_sha256: str = ""

    def compute_hash(self) -> str:
        """Compute certificate SHA256 from all fields except itself."""
        payload = {
            "calculation_id": self.calculation_id,
            "calculation_type": self.calculation_type,
            "normalized_inputs": self.normalized_inputs,
            "proposer_name": self.proposer_name,
            "proposer_result": self.proposer_result,
            "verifier_name": self.verifier_name,
            "verifier_result": self.verifier_result,
            "invariant_results": self.invariant_results,
            "agreement": self.agreement,
            "final_status": self.final_status,
            "exact_arithmetic": self.exact_arithmetic,
            "tool_versions": self.tool_versions,
            "source_paths": self.source_paths,
            "source_hashes": self.source_hashes,
            "timestamp_utc": self.timestamp_utc,
        }
        return _sha256_hex(_canonical_json(payload))

    def to_dict(self) -> dict[str, Any]:
        d = {
            "calculation_id": self.calculation_id,
            "calculation_type": self.calculation_type,
            "normalized_inputs": self.normalized_inputs,
            "proposer_name": self.proposer_name,
            "proposer_result": self.proposer_result,
            "verifier_name": self.verifier_name,
            "verifier_result": self.verifier_result,
            "invariant_results": self.invariant_results,
            "agreement": self.agreement,
            "final_status": self.final_status,
            "exact_arithmetic": self.exact_arithmetic,
            "tool_versions": self.tool_versions,
            "source_paths": self.source_paths,
            "source_hashes": self.source_hashes,
            "timestamp_utc": self.timestamp_utc,
            "certificate_sha256": self.certificate_sha256,
        }
        return d


def make_certificate(
    calculation_id: str,
    calculation_type: str,
    normalized_inputs: dict[str, Any],
    proposer_name: str,
    proposer_result: dict[str, Any],
    verifier_name: str,
    verifier_result: dict[str, Any],
    invariant_results: list[InvariantResult],
    agreement: bool,
    final_status: str,
    exact_arithmetic: bool,
    tool_versions: dict[str, str],
    source_paths: list[str],
    source_hashes: list[str],
) -> CalculationCertificate:
    """Create a CalculationCertificate with computed hash."""
    cert = CalculationCertificate(
        calculation_id=calculation_id,
        calculation_type=calculation_type,
        normalized_inputs=normalized_inputs,
        proposer_name=proposer_name,
        proposer_result=proposer_result,
        verifier_name=verifier_name,
        verifier_result=verifier_result,
        invariant_results=[ir.to_dict() for ir in invariant_results],
        agreement=agreement,
        final_status=final_status,
        exact_arithmetic=exact_arithmetic,
        tool_versions=tool_versions,
        source_paths=source_paths,
        source_hashes=source_hashes,
        timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    # Compute hash and return a new instance with it set
    h = cert.compute_hash()
    return CalculationCertificate(
        calculation_id=cert.calculation_id,
        calculation_type=cert.calculation_type,
        normalized_inputs=cert.normalized_inputs,
        proposer_name=cert.proposer_name,
        proposer_result=cert.proposer_result,
        verifier_name=cert.verifier_name,
        verifier_result=cert.verifier_result,
        invariant_results=cert.invariant_results,
        agreement=cert.agreement,
        final_status=cert.final_status,
        exact_arithmetic=cert.exact_arithmetic,
        tool_versions=cert.tool_versions,
        source_paths=cert.source_paths,
        source_hashes=cert.source_hashes,
        timestamp_utc=cert.timestamp_utc,
        certificate_sha256=h,
    )


def determine_final_status(
    proposer_status: str,
    verifier_status: str,
    invariant_results: list[InvariantResult],
    agreement: bool,
) -> str:
    """Determine the final verification status.

    Rules:
    1. If any invariant fails -> rejected_by_invariant
    2. If proposer and verifier disagree -> abstain_due_to_verification_disagreement
    3. If verifier unavailable -> verifier_unavailable
    4. If all agree and all invariants pass -> verified
    5. If input invalid -> invalid_input
    """
    # Check invariants first
    for ir in invariant_results:
        if not ir.passed:
            return REJECTED_BY_INVARIANT

    # Check agreement
    if not agreement:
        return ABSTAIN_DUE_TO_VERIFICATION_DISAGREEMENT

    # Check individual statuses
    if proposer_status == INVALID_INPUT or verifier_status == INVALID_INPUT:
        return INVALID_INPUT

    if verifier_status == VERIFIER_UNAVAILABLE:
        return VERIFIER_UNAVAILABLE

    if proposer_status == VERIFIED and verifier_status == VERIFIED:
        return VERIFIED

    return INSUFFICIENT_EVIDENCE
