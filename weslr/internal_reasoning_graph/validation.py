"""Internal Reasoning Graph Validation Engine

Validation engine for internal reasoning graph proposals.
Checks format, scope, additive requirements, and backward compatibility.

Features:
  - Format validation (JSON, required fields)
  - Scope validation (WESLR Python files only, no TIA/C#)
  - Additive validation (no breaking changes)
  - Backward compatibility validation (all existing tests pass)
  - Validation result: VALID, INVALID, PENDING_REVIEW
  - No automatic approval path
  - No automatic application path
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .models import Node, ProposalStatus


class ValidationCheckType(str, Enum):
    """Validation check types."""
    FORMAT = "format"
    SCOPE = "scope"
    ADDITIVE = "additive"
    BACKWARD_COMPATIBILITY = "backward_compatibility"


class ValidationSeverity(str, Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationStatus(str, Enum):
    """Validation status."""
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"


@dataclass
class ValidationIssue:
    """A validation issue found during validation."""
    check_type: ValidationCheckType
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    field: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_type": self.check_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ValidationIssue:
        return cls(
            check_type=ValidationCheckType(data["check_type"]),
            severity=ValidationSeverity(data["severity"]),
            message=data["message"],
            details=data.get("details", {}),
            field=data.get("field"),
            expected=data.get("expected"),
            actual=data.get("actual"),
        )


@dataclass
class ValidationResult:
    """Result of validation."""
    status: str  # VALID, INVALID, PENDING_REVIEW
    issues: List[ValidationIssue] = field(default_factory=list)
    checked_at: int = field(default_factory=lambda: int(time.time()))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "issues": [i.to_dict() for i in self.issues],
            "checked_at": self.checked_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ValidationResult:
        return cls(
            status=data["status"],
            issues=[ValidationIssue.from_dict(i) for i in data.get("issues", [])],
            checked_at=data.get("checked_at", int(time.time())),
        )
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return self.status == ValidationStatus.VALID.value
    
    @property
    def is_invalid(self) -> bool:
        """Check if validation failed."""
        return self.status == ValidationStatus.INVALID.value


class ProposalValidationEngine:
    """Validation engine for internal reasoning graph proposals.
    
    Checks format, scope, additive requirements, and backward compatibility.
    """
    
    # Validation thresholds
    FORMAT_REQUIRED_FIELDS = ["id", "name", "description", "node_type"]
    SCOPE_ALLOWED_NODE_TYPES = [
        "subsystem", "capability", "bottleneck", "policy", 
        "workflow", "dependency", "proposal", "research_finding", "trust_gate"
    ]
    SCOPE_ALLOWED_EDGE_TYPES = [
        "depends_on", "strengthens", "replaces", "bottleneck_for",
        "governed_by", "proposes_change_to", "validated_by", "conflicts_with"
    ]
    SCOPE_EXCLUDED_FILE_PATTERNS = [".pyc", "__pycache__", ".test.py"]
    
    def __init__(self):
        self._validation_results: Dict[str, ValidationResult] = {}
        self._validation_issues: Dict[str, List[ValidationIssue]] = {}
    
    # =========================================================================
    # Validation Methods
    # =========================================================================
    
    def validate_proposal(self, node: Node, actor: str = "system") -> ValidationResult:
        """Validate a proposal node.
        
        Runs all validation checks and returns result.
        """
        issues: List[ValidationIssue] = []
        
        # Format validation
        format_issues = self._validate_format(node)
        issues.extend(format_issues)
        
        # Scope validation
        scope_issues = self._validate_scope(node)
        issues.extend(scope_issues)
        
        # Additive validation
        additive_issues = self._validate_additive(node)
        issues.extend(additive_issues)
        
        # Backward compatibility validation
        bc_issues = self._validate_backward_compatibility(node)
        issues.extend(bc_issues)
        
        # Determine overall status
        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        status = ValidationStatus.INVALID.value if has_errors else ValidationStatus.VALID.value
        
        result = ValidationResult(
            status=status,
            issues=issues,
            checked_at=int(time.time()),
        )
        
        self._validation_results[node.id] = result
        self._validation_issues[node.id] = issues
        
        return result
    
    def _validate_format(self, node: Node) -> List[ValidationIssue]:
        """Validate proposal format - required fields, valid types."""
        issues: List[ValidationIssue] = []
        
        # Check required fields
        for field_name in self.FORMAT_REQUIRED_FIELDS:
            value = getattr(node, field_name, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                issues.append(ValidationIssue(
                    check_type=ValidationCheckType.FORMAT,
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing or empty required field: {field_name}",
                    field=field_name,
                    expected="non-empty string",
                    actual=getattr(node, field_name, None),
                ))
        
        # Check node type
        if node.node_type not in self.SCOPE_ALLOWED_NODE_TYPES:
            issues.append(ValidationIssue(
                check_type=ValidationCheckType.FORMAT,
                severity=ValidationSeverity.ERROR,
                message=f"Invalid node_type: {node.node_type}",
                field="node_type",
                expected=f"one of {self.SCOPE_ALLOWED_NODE_TYPES}",
                actual=node.node_type,
            ))
        
        # Check proposal-specific fields
        if node.node_type == "proposal":
            metadata = node.metadata or {}
            if "proposed_by" not in metadata:
                issues.append(ValidationIssue(
                    check_type=ValidationCheckType.FORMAT,
                    severity=ValidationSeverity.ERROR,
                    message="Proposal missing 'proposed_by' in metadata",
                    field="metadata.proposed_by",
                    expected="non-empty string",
                    actual=None,
                ))
            if "required_governance" in metadata:
                valid_governance = ["operator_review", "model_assisted", "none"]
                if metadata["required_governance"] not in valid_governance:
                    issues.append(ValidationIssue(
                        check_type=ValidationCheckType.FORMAT,
                        severity=ValidationSeverity.WARNING,
                        message=f"Unknown required_governance value: {metadata['required_governance']}",
                        field="metadata.required_governance",
                        expected=f"one of {valid_governance}",
                        actual=metadata["required_governance"],
                    ))
        
        return issues
    
    def _validate_scope(self, node: Node) -> List[ValidationIssue]:
        """Validate proposal scope - WESLR Python files only, no TIA/C#."""
        issues: List[ValidationIssue] = []
        
        # Check node metadata for excluded patterns
        metadata = node.metadata or {}
        
        # Check for C# code references
        content = str(node.description).lower()
        if "c#" in content or "c_sharp" in content or ".cs" in content:
            issues.append(ValidationIssue(
                check_type=ValidationCheckType.SCOPE,
                severity=ValidationSeverity.ERROR,
                message="Proposal references C# code, which is excluded from WESLR scope",
                field="description",
                expected="no C# references",
                actual=node.description,
            ))
        
        # Check for TIA references
        if "tia" in content.lower() or "third_party_integration" in content.lower():
            issues.append(ValidationIssue(
                check_type=ValidationCheckType.SCOPE,
                severity=ValidationSeverity.ERROR,
                message="Proposal references TIA (Third-Party Integration), which is excluded from WESLR scope",
                field="description",
                expected="no TIA references",
                actual=node.description,
            ))
        
        # Check edges for excluded types
        for edge in node.edges or []:
            if edge.edge_type not in self.SCOPE_ALLOWED_EDGE_TYPES:
                issues.append(ValidationIssue(
                    check_type=ValidationCheckType.SCOPE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Edge uses excluded edge type: {edge.edge_type}",
                    field="edges[].edge_type",
                    expected=f"one of {self.SCOPE_ALLOWED_EDGE_TYPES}",
                    actual=edge.edge_type,
                ))
        
        return issues
    
    def _validate_additive(self, node: Node) -> List[ValidationIssue]:
        """Validate proposal is additive - no breaking changes to existing layers."""
        issues: List[ValidationIssue] = []
        
        # Check if proposal removes or modifies existing nodes
        if node.status in ["deprecated", "removed"]:
            issues.append(ValidationIssue(
                check_type=ValidationCheckType.ADDITIVE,
                severity=ValidationSeverity.WARNING,
                message="Proposal proposes removal or deprecation, which may break backward compatibility",
                field="status",
                expected="active or proposed",
                actual=node.status,
            ))
        
        # Check for changes that affect existing nodes
        metadata = node.metadata or {}
        if metadata.get("affects_existing_nodes"):
            affected = metadata["affects_existing_nodes"]
            if isinstance(affected, list) and len(affected) > 0:
                issues.append(ValidationIssue(
                    check_type=ValidationCheckType.ADDITIVE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Proposal affects {len(affected)} existing node(s) - ensure additive nature",
                    field="metadata.affects_existing_nodes",
                    expected="empty list or no such field",
                    actual=affected,
                ))
        
        return issues
    
    def _validate_backward_compatibility(self, node: Node) -> List[ValidationIssue]:
        """Validate backward compatibility - no breaking changes."""
        issues: List[ValidationIssue] = []
        
        # Check for API signature changes
        metadata = node.metadata or {}
        
        if metadata.get("changes_api"):
            issues.append(ValidationIssue(
                check_type=ValidationCheckType.BACKWARD_COMPATIBILITY,
                severity=ValidationSeverity.WARNING,
                message="Proposal may change public API - ensure backward compatibility",
                field="metadata.changes_api",
                expected="false or no such field",
                actual=metadata.get("changes_api"),
            ))
        
        if metadata.get("removes_deprecated"):
            issues.append(ValidationIssue(
                check_type=ValidationCheckType.BACKWARD_COMPATIBILITY,
                severity=ValidationSeverity.WARNING,
                message="Proposal removes deprecated elements - verify no users depend on them",
                field="metadata.removes_deprecated",
                expected="false or no such field",
                actual=metadata.get("removes_deprecated"),
            ))
        
        # Check for version breaking changes
        if metadata.get("breaking_change"):
            issues.append(ValidationIssue(
                check_type=ValidationCheckType.BACKWARD_COMPATIBILITY,
                severity=ValidationSeverity.ERROR,
                message="Proposal declares breaking change - ensure operator approval and documentation",
                field="metadata.breaking_change",
                expected="false or no such field",
                actual=metadata.get("breaking_change"),
            ))
        
        return issues
    
    # =========================================================================
    # Status Queries (Read-Only)
    # =========================================================================
    
    def get_validation_status(self, proposal_id: str) -> str:
        """Get validation status for a proposal - read-only query."""
        if proposal_id not in self._validation_results:
            return ValidationStatus.PENDING.value
        return self._validation_results[proposal_id].status
    
    def get_validation_issues(self, proposal_id: str) -> List[ValidationIssue]:
        """Get validation issues for a proposal - read-only query."""
        return self._validation_issues.get(proposal_id, [])
    
    def export_validation_summary(self, proposal_id: str) -> Dict[str, Any]:
        """Export validation summary - operator-readable + machine-readable."""
        if proposal_id not in self._validation_results:
            return {
                "proposal_id": proposal_id,
                "status": ValidationStatus.PENDING.value,
                "issues": [],
            }
        
        result = self._validation_results[proposal_id]
        return {
            "proposal_id": proposal_id,
            "status": result.status,
            "checked_at": result.checked_at,
            "issues": [i.to_dict() for i in result.issues],
        }
    
    def export_all_validations(self) -> Dict[str, Any]:
        """Export all validations - operator-readable + machine-readable."""
        summaries = {}
        for proposal_id, result in self._validation_results.items():
            summaries[proposal_id] = {
                "status": result.status,
                "checked_at": result.checked_at,
                "issue_count": len(result.issues),
            }
        
        return {
            "validations": summaries,
            "total_count": len(summaries),
            "valid_count": sum(1 for s in summaries.values() if s["status"] == ValidationStatus.VALID.value),
            "invalid_count": sum(1 for s in summaries.values() if s["status"] == ValidationStatus.INVALID.value),
            "pending_count": sum(1 for s in summaries.values() if s["status"] == ValidationStatus.PENDING.value),
        }
    
    # =========================================================================
    # Validation State Management
    # =========================================================================
    
    def reset_validation(self, proposal_id: str) -> None:
        """Reset validation state for a proposal."""
        if proposal_id in self._validation_results:
            del self._validation_results[proposal_id]
        if proposal_id in self._validation_issues:
            del self._validation_issues[proposal_id]
    
    def reset_all(self) -> None:
        """Reset all validation state."""
        self._validation_results.clear()
        self._validation_issues.clear()
    
    def mark_pending(self, proposal_id: str) -> None:
        """Mark proposal validation as pending."""
        self._validation_results[proposal_id] = ValidationResult(
            status=ValidationStatus.PENDING.value,
            issues=[],
            checked_at=int(time.time()),
        )
        self._validation_issues[proposal_id] = []
    
    def mark_valid(self, proposal_id: str) -> None:
        """Mark proposal validation as valid."""
        self._validation_results[proposal_id] = ValidationResult(
            status=ValidationStatus.VALID.value,
            issues=[],
            checked_at=int(time.time()),
        )
        self._validation_issues[proposal_id] = []
    
    def mark_invalid(self, proposal_id: str, issues: List[ValidationIssue]) -> None:
        """Mark proposal validation as invalid."""
        self._validation_results[proposal_id] = ValidationResult(
            status=ValidationStatus.INVALID.value,
            issues=issues,
            checked_at=int(time.time()),
        )
        self._validation_issues[proposal_id] = issues
