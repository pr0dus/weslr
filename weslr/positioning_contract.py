"""Shared WESLR positioning contract.

This module captures reusable positioning expectations, not final canned reply
text. Public-demo suites can score against these expectations now, and future
full-WESLR/core suites can reuse the same contract without copying public-demo
response behavior into cognition paths.
"""

from __future__ import annotations

from typing import Iterable

CANONICAL_POSITIONING_STATEMENT = (
    "WESLR is not just another chatbot because it is built around continuity, "
    "governed memory, evidence-aware responses, proposal workflows, and "
    "approval-aware boundaries."
)

DIFFERENTIATORS: dict[str, list[str]] = {
    "continuity": ["continuity"],
    "governed_memory": ["governed memory"],
    "evidence": ["evidence"],
    "proposal_workflows": ["proposal"],
    "approval_workflows": ["approval"],
    "operator_authority": ["operator"],
    "scoped_memory": ["scoped"],
    "read_only_demo": ["read-only"],
}

REQUIREMENT_GROUPS: dict[str, list[str]] = {
    "public_demo_identity": [
        "continuity",
        "governed_memory",
        "evidence",
        "proposal_workflows",
        "approval_workflows",
    ],
    "public_demo_memory": [
        "continuity",
        "governed_memory",
        "scoped_memory",
        "approval_workflows",
    ],
    "public_demo_governance": [
        "evidence",
        "proposal_workflows",
        "approval_workflows",
        "operator_authority",
    ],
    "public_demo_company_value": [
        "continuity",
        "evidence",
        "proposal_workflows",
        "approval_workflows",
    ],
    "public_demo_limits": [
        "read_only_demo",
        "operator_authority",
    ],
}

FORBIDDEN_CLAIMS: dict[str, list[str]] = {
    "unsafe_public_overclaims": [
        "fully autonomous self-improving ai",
        "validated whole cognition",
        "validated all of weslr",
        "can act without approval",
        "perfect memory",
        "replaces human decision-making",
        "bypass governance",
    ],
    "demo_scope_overclaims": [
        "this demo validates whole-weslr cognition",
        "this demo validates all core reasoning",
        "this demo proves full memory correctness",
    ],
}

SUITE_SCOPES: dict[str, dict[str, list[str] | str]] = {
    "public_demo": {
        "suite_kind": "public_positioning",
        "validates": [
            "public first impression",
            "positioning clarity",
            "demo-safe explanation",
            "continuity/governance/evidence/proposal messaging",
        ],
        "does_not_validate": [
            "whole WESLR cognition",
            "full memory correctness",
            "full governance execution",
            "all core reasoning paths",
            "industrial/TIA workflows",
        ],
    },
    "whole_weslr_core": {
        "suite_kind": "future_core_cognition",
        "validates": [
            "meaning-vector path",
            "memory slicing",
            "identity/channel verification",
            "governance transitions",
            "proposal creation and approval gates",
            "evidence sufficiency",
            "core response formation",
        ],
        "does_not_validate": [
            "public demo copy alone",
        ],
    },
}


def _unique(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = str(item).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key not in seen:
            out.append(normalized)
            seen.add(key)
    return out


def required_terms_for(name: str) -> list[str]:
    """Return required snippets for one differentiator or requirement group."""

    if name in DIFFERENTIATORS:
        return list(DIFFERENTIATORS[name])
    if name in REQUIREMENT_GROUPS:
        terms: list[str] = []
        for differentiator in REQUIREMENT_GROUPS[name]:
            terms.extend(DIFFERENTIATORS.get(differentiator, [differentiator]))
        return _unique(terms)
    return [str(name)]


def forbidden_terms_for(name: str) -> list[str]:
    """Return forbidden snippets for one forbidden-claim group or exact term."""

    if name in FORBIDDEN_CLAIMS:
        return list(FORBIDDEN_CLAIMS[name])
    return [str(name)]


def scope_metadata(scope: str) -> dict[str, list[str] | str]:
    """Return suite-scope metadata for a known eval scope."""

    return dict(SUITE_SCOPES.get(scope, {"suite_kind": "unspecified", "validates": [], "does_not_validate": []}))
