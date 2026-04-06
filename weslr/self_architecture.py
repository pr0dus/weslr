# self_architecture.py - WESLR Self-Architecture Core v1
# Represents, inspects, and evaluates WESLR's own architecture.
# Operator-first, additive only, reversible, governed.

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class SubsystemType(str, Enum):
    """Types of WESLR subsystems."""
    CAPABILITY_DISCOVERY = "capability_discovery"
    CONTINUITY = "continuity"
    EVIDENCE = "evidence"
    FILE_INGESTION = "file_ingestion"
    STATE = "state"
    TASK = "task"
    OTHER = "other"


class SubsystemStatus(str, Enum):
    """Status of a subsystem."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    UNDER_REVIEW = "under_review"
    SUGGESTED = "suggested"
    REMOVED = "removed"


class ChangeType(str, Enum):
    """Types of architectural changes."""
    NEW = "new"
    IMPROVEMENT = "improvement"
    DEPRECATION = "deprecation"
    REFACTOR = "refactor"
    REMOVAL = "removal"


class Recommendation(str, Enum):
    """Recommendation for a proposed change."""
    ACCEPT = "accept"
    ACCEPT_WITH_CONDITIONS = "accept_with_conditions"
    REJECT = "reject"
    SNOOZE = "snooze"
    PENDING = "pending"


@dataclass
class Subsystem:
    """A WESLR subsystem with metadata and dependencies."""
    name: str
    description: str
    version: str = "1.0.0"
    subsystem_type: str = SubsystemType.OTHER.value
    status: str = SubsystemStatus.ACTIVE.value
    depends_on: List[str] = field(default_factory=list)  # Names of dependent subsystems
    depended_by: List[str] = field(default_factory=list)  # Names of dependents
    
    # Fitness goals
    goals: List[str] = field(default_factory=list)
    bottlenecks: List[str] = field(default_factory=list)
    
    # Metrics
    lines_of_code: Optional[int] = None
    last_updated: Optional[str] = None
    
    # Metadata
    owner: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Subsystem:
        data["subsystem_type"] = SubsystemType(data.get("subsystem_type", "other")).value
        data["status"] = SubsystemStatus(data.get("status", "active")).value
        data["depends_on"] = data.get("depends_on", [])
        data["depended_by"] = data.get("depended_by", [])
        data["goals"] = data.get("goals", [])
        data["bottlenecks"] = data.get("bottlenecks", [])
        data["tags"] = data.get("tags", [])
        return cls(**data)


@dataclass
class ArchitecturalRisk:
    """An architectural risk."""
    id: str
    subsystem: str
    description: str
    severity: str = "medium"  # low, medium, high
    likelihood: str = "medium"  # low, medium, high
    mitigation: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    status: str = "open"  # open, mitigated, accepted

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ArchitecturalRisk:
        return cls(**data)


@dataclass
class ChangeProposal:
    """A proposed architectural change."""
    id: str
    title: str
    description: str
    change_type: str = "improvement"  # ChangeType.value
    affected_subsystems: List[str] = field(default_factory=list)
    expected_improvements: List[str] = field(default_factory=list)
    
    # Evaluation
    architectural_fit: Optional[str] = None
    risk_context: Optional[str] = None
    quick_win: bool = False
    strategic: bool = False
    speculative: bool = False
    
    # Recommendation
    recommendation: str = Recommendation.PENDING.value
    decision_reason: Optional[str] = None
    
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    submitted_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChangeProposal:
        data["affected_subsystems"] = data.get("affected_subsystems", [])
        data["expected_improvements"] = data.get("expected_improvements", [])
        return cls(**data)


@dataclass
class FitnessGoal:
    """An architectural fitness goal."""
    id: str
    name: str
    description: str
    subsystems: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    last_reviewed: Optional[str] = None
    status: str = "active"  # active, deprecated, achieved

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FitnessGoal:
        data["subsystems"] = data.get("subsystems", [])
        data["success_criteria"] = data.get("success_criteria", [])
        return cls(**data)


@dataclass
class SelfArchitecture:
    """Self-architectural representation of WESLR."""
    subsystems: Dict[str, Subsystem] = field(default_factory=dict)
    risks: Dict[str, ArchitecturalRisk] = field(default_factory=dict)
    proposals: Dict[str, ChangeProposal] = field(default_factory=dict)
    fitness_goals: Dict[str, FitnessGoal] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    version: str = "1.0.0"
    owner: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subsystems": {k: v.to_dict() for k, v in self.subsystems.items()},
            "risks": {k: v.to_dict() for k, v in self.risks.items()},
            "proposals": {k: v.to_dict() for k, v in self.proposals.items()},
            "fitness_goals": {k: v.to_dict() for k, v in self.fitness_goals.items()},
            "dependency_graph": self.dependency_graph,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "version": self.version,
            "owner": self.owner,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SelfArchitecture:
        subsystems = {k: Subsystem.from_dict(v) for k, v in data.get("subsystems", {}).items()}
        risks = {k: ArchitecturalRisk.from_dict(v) for k, v in data.get("risks", {}).items()}
        proposals = {k: ChangeProposal.from_dict(v) for k, v in data.get("proposals", {}).items()}
        fitness_goals = {k: FitnessGoal.from_dict(v) for k, v in data.get("fitness_goals", {}).items()}
        return cls(
            subsystems=subsystems,
            risks=risks,
            proposals=proposals,
            fitness_goals=fitness_goals,
            dependency_graph=data.get("dependency_graph", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            last_updated=data.get("last_updated", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            version=data.get("version", "1.0.0"),
            owner=data.get("owner"),
        )

    def register_subsystem(self, subsystem: Subsystem) -> Subsystem:
        """Register a subsystem in the architecture."""
        self.subsystems[subsystem.name] = subsystem
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Update dependency graph
        for dep in subsystem.depends_on:
            if dep not in self.dependency_graph:
                self.dependency_graph[dep] = []
            if subsystem.name not in self.dependency_graph[dep]:
                self.dependency_graph[dep].append(subsystem.name)
        
        return subsystem

    def register_risk(self, risk: ArchitecturalRisk) -> ArchitecturalRisk:
        """Register an architectural risk."""
        self.risks[risk.id] = risk
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return risk

    def register_proposal(self, proposal: ChangeProposal) -> ChangeProposal:
        """Register a change proposal."""
        self.proposals[proposal.id] = proposal
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return proposal

    def register_fitness_goal(self, goal: FitnessGoal) -> FitnessGoal:
        """Register a fitness goal."""
        self.fitness_goals[goal.id] = goal
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return goal

    def get_subsystem(self, name: str) -> Optional[Subsystem]:
        """Get a subsystem by name."""
        return self.subsystems.get(name)

    def get_subsystems_by_type(self, subsystem_type: str) -> List[Subsystem]:
        """Get all subsystems of a given type."""
        return [s for s in self.subsystems.values() if s.subsystem_type == subsystem_type]

    def get_subsystems_by_status(self, status: str) -> List[Subsystem]:
        """Get all subsystems with a given status."""
        return [s for s in self.subsystems.values() if s.status == status]

    def get_risks_by_severity(self, severity: str) -> List[ArchitecturalRisk]:
        """Get all risks with a given severity."""
        return [r for r in self.risks.values() if r.severity == severity]

    def get_active_proposals(self) -> List[ChangeProposal]:
        """Get all pending/active change proposals."""
        return [p for p in self.proposals.values() if p.recommendation in ("pending", "accept_with_conditions")]

    def get_recommendations(self, recommendation: str) -> List[ChangeProposal]:
        """Get all proposals with a given recommendation."""
        return [p for p in self.proposals.values() if p.recommendation == recommendation]


# ============================================================================
# RISK ASSESSOR
# ============================================================================

class RiskAssessor:
    """Assesses architectural risks and mitigation strategies."""

    @staticmethod
    def assess_severity(description: str, subsystem: str) -> str:
        """Assess risk severity based on content."""
        description_lower = description.lower()
        
        if any(kw in description_lower for kw in ["security", "data loss", "corruption"]):
            return "high"
        if any(kw in description_lower for kw in ["performance", "break", "unstable"]):
            return "high"
        if any(kw in description_lower for kw in ["deprecation", "migration", "breaking"]):
            return "medium"
        return "low"

    @staticmethod
    def assess_likelihood(description: str) -> str:
        """Assess risk likelihood based on content."""
        description_lower = description.lower()
        
        if any(kw in description_lower for kw in ["breaking", "removal", "removing"]):
            return "high"
        if any(kw in description_lower for kw in ["new", "experimental", "untested"]):
            return "medium"
        return "low"

    @staticmethod
    def generate_mitigation(description: str, subsystem: str) -> Optional[str]:
        """Generate a mitigation strategy."""
        description_lower = description.lower()
        
        if "breaking" in description_lower:
            return "Provide migration path with deprecation warnings"
        if "security" in description_lower:
            return "Add security review and access controls"
        if "performance" in description_lower:
            return "Benchmark before/after and add monitoring"
        if "removal" in description_lower:
            return "Deprecate first, provide migration guide"
        
        return "Monitor and iterate"


# ============================================================================
# PROPOSAL EVALUATOR
# ============================================================================

class ProposalEvaluator:
    """Evaluates change proposals against architectural goals."""

    def __init__(self, architecture: SelfArchitecture):
        self.architecture = architecture

    def evaluate(
        self,
        proposal: ChangeProposal,
        radar_suggestion: Optional[Any] = None,
    ) -> ChangeProposal:
        """Evaluate a change proposal.
        
        If radar_suggestion is provided, use it to populate proposal fields.
        """
        # Set affected subsystems from radar suggestion if available
        if radar_suggestion and hasattr(radar_suggestion, 'capability_type'):
            subsystems = self._map_capability_to_subsystems(radar_suggestion.capability_type)
            if subsystems and not proposal.affected_subsystems:
                proposal.affected_subsystems = subsystems
        
        # Set expected improvements from radar suggestion
        if radar_suggestion and hasattr(radar_suggestion, 'title'):
            if "improvement" in radar_suggestion.title.lower():
                proposal.expected_improvements.append("process improvement")
            if "automation" in radar_suggestion.title.lower():
                proposal.expected_improvements.append("automation capability")
            if "integration" in radar_suggestion.title.lower():
                proposal.expected_improvements.append("integration capacity")
        
        # Assess architectural fit
        if proposal.affected_subsystems:
            proposal.architectural_fit = "moderate"
            if len(proposal.affected_subsystems) <= 2:
                proposal.architectural_fit = "strong"
        
        # Risk context
        risks = []
        if proposal.affected_subsystems:
            risks.append(f"affects {len(proposal.affected_subsystems)} subsystem(s)")
        if proposal.change_type == ChangeType.REMOVAL.value:
            risks.append("breaking change risk")
        # Detect breaking change in description/title
        desc_lower = (proposal.description or "").lower() + (proposal.title or "").lower()
        if "breaking" in desc_lower or "remove" in desc_lower:
            risks.append("breaking change risk")
        proposal.risk_context = "; ".join(risks) if risks else "standard change"
        
        # Classification
        proposal.quick_win = len(proposal.affected_subsystems) <= 1 and "improvement" in proposal.description.lower()
        proposal.strategic = "strategic" in proposal.description.lower()
        proposal.speculative = "speculative" in proposal.description.lower() or (len(proposal.affected_subsystems) > 2 if proposal.affected_subsystems else False)
        
        # Recommendation
        proposal.recommendation = self._make_recommendation(proposal)
        
        proposal.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        return proposal

    def _map_capability_to_subsystems(self, capability_type: str) -> List[str]:
        """Map a capability type to affected subsystems."""
        mapping = {
            "ingestion": ["capability_discovery", "file_ingestion"],
            "analysis": ["capability_discovery"],
            "visualization": ["capability_discovery"],
            "automation": ["task", "state"],
            "integration": ["state", "continuity"],
            "storage": ["state"],
            "security": ["state"],
            "other": ["continuity"],
        }
        return mapping.get(capability_type, ["continuity"])

    def _make_recommendation(self, proposal: ChangeProposal) -> str:
        """Make a recommendation based on evaluation."""
        # High risk changes are rejected (check for breaking risk in context)
        if "breaking" in (proposal.risk_context or "") or "high" in (proposal.risk_context or ""):
            return Recommendation.REJECT.value
        
        # If quick win and low risk
        if proposal.quick_win and "high" not in (proposal.risk_context or ""):
            if "strategic" in proposal.description.lower() or proposal.strategic:
                return Recommendation.ACCEPT_WITH_CONDITIONS.value
            return Recommendation.ACCEPT.value
        
        # Strategic changes need review
        if proposal.strategic or proposal.speculative:
            return Recommendation.PENDING.value
        
        # High risk changes are rejected
        if "high" in (proposal.risk_context or ""):
            return Recommendation.REJECT.value
        
        # Default
        return Recommendation.PENDING.value


# ============================================================================
# RADAR INTEGRATION (Phase 8 prep)
# ============================================================================

def map_radar_suggestion_to_proposal(
    suggestion: Any,
    proposal_id: str,
) -> ChangeProposal:
    """Map a Capability Discovery Radar suggestion to a ChangeProposal.
    
    Args:
        suggestion: CapabilitySuggestion from radar
        proposal_id: Unique ID for the proposal
        
    Returns:
        ChangeProposal with mapped fields
    """
    from self_architecture import ChangeProposal, ChangeType
    from datetime import datetime, timezone
    
    # Determine affected subsystems from capability type
    subsystems = {
        "ingestion": ["capability_discovery", "file_ingestion"],
        "analysis": ["capability_discovery"],
        "visualization": ["capability_discovery"],
        "automation": ["task", "state"],
        "integration": ["state", "continuity"],
        "storage": ["state"],
        "security": ["state"],
        "other": ["continuity"],
    }
    cap_type = getattr(suggestion, 'capability_type', None)
    if cap_type and hasattr(cap_type, 'value'):
        cap_type_str = cap_type.value
    else:
        cap_type_str = "other"
    
    affected = subsystems.get(cap_type_str, ["continuity"])
    
    # Determine change type
    if "remove" in suggestion.title.lower() or "deprecate" in suggestion.title.lower():
        change_type = ChangeType.REMOVAL.value
    elif "refactor" in suggestion.title.lower():
        change_type = ChangeType.REFACTOR.value
    elif "new" in suggestion.title.lower():
        change_type = ChangeType.NEW.value
    else:
        change_type = ChangeType.IMPROVEMENT.value
    
    # Expected improvements
    improvements = []
    if "improvement" in suggestion.description.lower() or "better" in suggestion.description.lower():
        improvements.append("process improvement")
    if "automation" in suggestion.description.lower():
        improvements.append("automation capability")
    if "integration" in suggestion.description.lower():
        improvements.append("integration capacity")
    
    proposal = ChangeProposal(
        id=proposal_id,
        title=suggestion.title,
        description=suggestion.description or "",
        change_type=change_type,
        affected_subsystems=affected,
        expected_improvements=improvements or ["general improvement"],
        created_at=getattr(suggestion, 'created_at', datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
        updated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    
    return proposal


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI interface for self-architecture operations."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python self_architecture.py <command> [args]")
        print("Commands:")
        print("  register-subsystem <name> <description>")
        print("  register-risk <id> <subsystem> <description>")
        print("  register-proposal <id> <title> <description>")
        print("  list-subsystems")
        print("  list-risks")
        print("  list-proposals")
        print("  show <name>")
        sys.exit(1)
    
    command = sys.argv[1]
    arch = SelfArchitecture()
    
    if command == "register-subsystem":
        if len(sys.argv) < 4:
            print("Usage: python self_architecture.py register-subsystem <name> <description>")
            sys.exit(1)
        name = sys.argv[2]
        description = " ".join(sys.argv[3:])
        subsystem = Subsystem(
            name=name,
            description=description,
        )
        arch.register_subsystem(subsystem)
        print(f"Registered subsystem: {name}")
    
    elif command == "register-risk":
        if len(sys.argv) < 5:
            print("Usage: python self_architecture.py register-risk <id> <subsystem> <description>")
            sys.exit(1)
        risk_id = sys.argv[2]
        subsystem = sys.argv[3]
        description = " ".join(sys.argv[4:])
        risk = ArchitecturalRisk(
            id=risk_id,
            subsystem=subsystem,
            description=description,
            severity=RiskAssessor.assess_severity(description, subsystem),
            likelihood=RiskAssessor.assess_likelihood(description),
            mitigation=RiskAssessor.generate_mitigation(description, subsystem),
        )
        arch.register_risk(risk)
        print(f"Registered risk: {risk_id}")
    
    elif command == "register-proposal":
        if len(sys.argv) < 5:
            print("Usage: python self_architecture.py register-proposal <id> <title> <description>")
            sys.exit(1)
        proposal_id = sys.argv[2]
        title = sys.argv[3]
        description = " ".join(sys.argv[4:])
        proposal = ChangeProposal(
            id=proposal_id,
            title=title,
            description=description,
            change_type=ChangeType.IMPROVEMENT.value,
        )
        arch.register_proposal(proposal)
        print(f"Registered proposal: {proposal_id}")
    
    elif command == "list-subsystems":
        print("Subsystems:")
        for name, subsystem in arch.subsystems.items():
            print(f"  - {name} ({subsystem.version})")
    
    elif command == "list-risks":
        print("Risks:")
        for risk_id, risk in arch.risks.items():
            print(f"  - {risk_id}: {risk.description} [{risk.severity}]")
    
    elif command == "list-proposals":
        print("Proposals:")
        for proposal_id, proposal in arch.proposals.items():
            print(f"  - {proposal_id}: {proposal.title} [{proposal.recommendation}]")
    
    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: python self_architecture.py show <name>")
            sys.exit(1)
        name = sys.argv[2]
        subsystem = arch.get_subsystem(name)
        if subsystem:
            print(json.dumps(subsystem.to_dict(), indent=2))
        else:
            print(f"Subsystem not found: {name}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
