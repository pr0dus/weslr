"""Internal Reasoning Graph (v94b)

WESLR internal architecture reasoning layer.
Supports self-study, proposal generation, and governance.
Never mutates architecture silently.

Architecture:
  graph models   — Node, Edge, Evidence, Governance classes
  graph store    — Persistence, validation, governance hooks
  governance     — Rules for mutation, proposals, validation

Features:
  - 9 node types (subsystem, capability, bottleneck, policy, workflow, dependency, proposal, research_finding, trust_gate)
  - 8 edge types (depends_on, strengthens, replaces, bottleneck_for, governed_by, proposes_change_to, validated_by, conflicts_with)
  - Governance by default — no silent mutation
  - Operator review required for all proposals
  - Reusable from concept_graph infrastructure

This module is additive and reversible.
"""

__version__ = "1.0.0"

from .models import (
    Node,
    Edge,
    NodeSubtype,
    GovernanceStatus,
    ProposalStatus,
    ValidationStatus,
)

__all__ = [
    "Node",
    "Edge",
    "NodeSubtype",
    "GovernanceStatus",
    "ProposalStatus",
    "ValidationStatus",
]
