"""Evidence Policy Module

Evidence policy layer for Weslr concept graph:
- Evidence requirements and validation
- Source type definitions
- Evidence categorization rules

This module provides policy enforcement for evidence
in the concept graph layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class EvidenceRequirement(Enum):
    """Evidence requirement levels."""
    OPTIONAL = "optional"
    RECOMMENDED = "recommended"
    REQUIRED = "required"


@dataclass
class EvidenceRule:
    """Rule for evidence requirements."""
    concept_type: str
    requirement: EvidenceRequirement
    min_sources: int = 1


def get_evidence_rules() -> List[EvidenceRule]:
    """Get all evidence rules."""
    return [
        EvidenceRule(
            concept_type="concept",
            requirement=EvidenceRequirement.OPTIONAL,
            min_sources=0,
        ),
        EvidenceRule(
            concept_type="entity",
            requirement=EvidenceRequirement.RECOMMENDED,
            min_sources=1,
        ),
    ]


def validate_evidence(concept_type: str, sources: int) -> bool:
    """Validate evidence count for concept type."""
    rules = get_evidence_rules()
    for rule in rules:
        if rule.concept_type == concept_type:
            return sources >= rule.min_sources
    return True
