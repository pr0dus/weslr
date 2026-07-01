"""Real Evidence Packet Schema for WESLR

This module defines a strict, static‑only schema for the first controlled
real‑evidence packet (Known‑Science Replay direction). The schema is expressed
as Python ``dataclass`` objects with a lightweight validation helper.
All fields are required and typed; the validator enforces the boundary
rules (no live web, no external calls, no persistence, no public claims,
etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Mapping, Any


class RealEvidenceSchemaError(ValueError):
    """Raised when a packet does not conform to the required schema."""


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise RealEvidenceSchemaError(message)


@dataclass(frozen=True)
class EvidenceItem:
    item_id: str
    item_type: Literal["text", "image", "audio", "binary", "structured"]
    content_summary: str
    source_reference: str
    provenance_status: Literal["author_provided", "public_copy", "synthetic_replay"]
    allowed_use: Literal["internal", "review", "audit"]
    forbidden_use: Literal["public_claim", "benchmark", "persistence"]
    injection_risk_notes: str
    sensitive_data_status: Literal["none", "redacted", "confidential"]
    uncertainty_notes: str

    def __post_init__(self) -> None:
        # Simple sanity checks for prohibited content
        _ensure("web" not in self.source_reference.lower(), "EvidenceItem must not reference live web sources")
        _ensure("github" not in self.source_reference.lower(), "EvidenceItem must not reference GitHub ingestion")
        _ensure("rss" not in self.source_reference.lower(), "EvidenceItem must not reference RSS feeds")
        _ensure("lab" not in self.source_reference.lower(), "EvidenceItem must not reference lab notebooks")


@dataclass(frozen=True)
class RealEvidencePacket:
    packet_id: str
    packet_version: str  # e.g. "v1.0"
    direction_id: str
    direction_type: Literal["known_science_replay", "owner_workflow", "synthetic_transfer"]
    domain: str
    evidence_source_type: Literal["known_science_replay", "owner_provided", "public_safe_copy"]
    source_provenance: str
    authorization_status: Literal["manual", "automated"]
    static_local_only: bool = field(default=True)
    external_calls_allowed: bool = field(default=False)
    persistence_allowed: bool = field(default=False)
    public_claim_allowed: bool = field(default=False)
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    known_science_anchor: str
    hypothesis_or_direction_statement: str
    expected_replay_pattern: str
    allowed_reasoning_actions: List[str]
    forbidden_reasoning_actions: List[str]
    uncertainty_notes: str
    failure_modes: List[str]
    stop_conditions: List[str]
    expected_output_type: Literal["internal_report", "metadata_summary"]
    no_public_claim_warning: str
    review_status: Literal["pending", "approved", "rejected"]

    def __post_init__(self) -> None:
        # Boundary enforcement – must be static‑local only
        _ensure(self.static_local_only, "static_local_only must be True for controlled packets")
        _ensure(not self.external_calls_allowed, "external_calls_allowed must be False")
        _ensure(not self.persistence_allowed, "persistence_allowed must be False")
        _ensure(not self.public_claim_allowed, "public_claim_allowed must be False")
        # Additional sanity checks on provenance strings
        _ensure("web" not in self.source_provenance.lower(), "source_provenance must not reference live web")
        _ensure("github" not in self.source_provenance.lower(), "source_provenance must not reference GitHub")
        _ensure("rss" not in self.source_provenance.lower(), "source_provenance must not reference RSS")
        _ensure("lab" not in self.source_provenance.lower(), "source_provenance must not reference lab notebook")
        # Ensure at least one evidence item is present
        _ensure(len(self.evidence_items) > 0, "packet must contain at least one evidence_items entry")


def validate_packet(packet_dict: Mapping[str, Any]) -> RealEvidencePacket:
    """Validate a dict against the RealEvidencePacket schema.

    Returns a ``RealEvidencePacket`` instance on success or raises
    ``RealEvidenceSchemaError`` on any violation.
    """
    # Convert evidence_items first
    items_raw = packet_dict.get("evidence_items")
    _ensure(isinstance(items_raw, list) and items_raw, "evidence_items must be a non‑empty list")
    items: List[EvidenceItem] = []
    for idx, raw in enumerate(items_raw):
        _ensure(isinstance(raw, dict), f"evidence_items[{idx}] must be a dict")
        items.append(EvidenceItem(**raw))

    # Build the packet, letting dataclass __post_init__ enforce boundaries
    try:
        packet = RealEvidencePacket(
            packet_id=packet_dict["packet_id"],
            packet_version=packet_dict["packet_version"],
            direction_id=packet_dict["direction_id"],
            direction_type=packet_dict["direction_type"],
            domain=packet_dict["domain"],
            evidence_source_type=packet_dict["evidence_source_type"],
            source_provenance=packet_dict["source_provenance"],
            authorization_status=packet_dict["authorization_status"],
            static_local_only=packet_dict.get("static_local_only", True),
            external_calls_allowed=packet_dict.get("external_calls_allowed", False),
            persistence_allowed=packet_dict.get("persistence_allowed", False),
            public_claim_allowed=packet_dict.get("public_claim_allowed", False),
            evidence_items=items,
            known_science_anchor=packet_dict["known_science_anchor"],
            hypothesis_or_direction_statement=packet_dict["hypothesis_or_direction_statement"],
            expected_replay_pattern=packet_dict["expected_replay_pattern"],
            allowed_reasoning_actions=packet_dict["allowed_reasoning_actions"],
            forbidden_reasoning_actions=packet_dict["forbidden_reasoning_actions"],
            uncertainty_notes=packet_dict["uncertainty_notes"],
            failure_modes=packet_dict["failure_modes"],
            stop_conditions=packet_dict["stop_conditions"],
            expected_output_type=packet_dict["expected_output_type"],
            no_public_claim_warning=packet_dict["no_public_claim_warning"],
            review_status=packet_dict["review_status"],
        )
    except Exception as exc:
        # Re‑raise as schema error for consistency
        raise RealEvidenceSchemaError(str(exc)) from exc
    return packet
