"""Decision Output - WESLR Decision Layer v1

Output data models for the unified WESLR Decision Layer.
Every item carries provenance, confidence, and transparent reasoning.

Contract:
- WESLR synthesizes internal perspectives into one operator-facing judgment
- WESLR does not expose unresolved internal disagreement by default
- All outputs are read-only projections of existing WESLR layers
- No autonomous execution without operator approval

Scope:
- what_matters_now: top priority items requiring attention
- blocked_items: items that cannot proceed with explicit reason
- next_actions: ordered recommended actions with provenance
- approval_queue: items awaiting operator decision with context

Non-scope:
- human values, life meaning, emotional manipulation
- irreversible external actions without approval
- what the operator "should want"
- moral/ethical judgments

Additive only. No modifications to existing modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DecisionItem:
    """Single item in a decision output.
    
    Every item must include:
    - title: what this item is about
    - reason: why it appears in this output
    - source_modules: which WESLR modules contributed
    - confidence: 0.0-1.0 confidence level
    - recommended_action: what the operator should consider
    
    Optional:
    - judgment_note: synthesized WESLR judgment (agree/disagree/warn/prefer)
    - provenance: additional context about the item (outcome_feedback, forecast, etc.)
    
    Contract: judgment_note expresses the SYNTHESIZED view.
    If internal perspectives disagree, this explains the resolution,
    not the raw disagreement.
    """
    
    title: str
    reason: str
    source_modules: List[str]
    confidence: float  # 0.0-1.0
    recommended_action: str
    judgment_note: Optional[str] = None  # Future: calm WESLR judgment
    
    # Optional metadata
    item_id: Optional[str] = None
    urgency_level: Optional[str] = None  # "low", "normal", "high", "critical"
    risk_level: Optional[float] = None  # 0.0-1.0
    created_at: Optional[str] = None
    
    # Provenance context (outcome_feedback, forecast, etc.)
    provenance: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate confidence and risk_level bounds."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {self.confidence}")
        if self.risk_level is not None and not 0.0 <= self.risk_level <= 1.0:
            raise ValueError(f"risk_level must be 0.0-1.0, got {self.risk_level}")
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "title": self.title,
            "reason": self.reason,
            "source_modules": self.source_modules,
            "confidence": self.confidence,
            "recommended_action": self.recommended_action,
            "judgment_note": self.judgment_note,
            "item_id": self.item_id,
            "urgency_level": self.urgency_level,
            "risk_level": self.risk_level,
            "created_at": self.created_at,
            "provenance": self.provenance,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DecisionItem:
        """Deserialize from dictionary."""
        return cls(
            title=data["title"],
            reason=data["reason"],
            source_modules=data["source_modules"],
            confidence=data["confidence"],
            recommended_action=data["recommended_action"],
            judgment_note=data.get("judgment_note"),
            item_id=data.get("item_id"),
            urgency_level=data.get("urgency_level"),
            risk_level=data.get("risk_level"),
            created_at=data.get("created_at"),
            provenance=data.get("provenance", {}),
        )


@dataclass
class DecisionOutput:
    """Unified WESLR decision output.
    
    Contains exactly four outputs:
    - what_matters_now: top items requiring immediate attention
    - blocked_items: items that cannot proceed
    - next_actions: ordered recommended actions
    - approval_queue: items awaiting operator decision
    
    Contract: WESLR synthesizes perspectives into one transparent judgment.
    Each list contains DecisionItem objects with full provenance.
    """
    
    what_matters_now: List[DecisionItem] = field(default_factory=list)
    blocked_items: List[DecisionItem] = field(default_factory=list)
    next_actions: List[DecisionItem] = field(default_factory=list)
    approval_queue: List[DecisionItem] = field(default_factory=list)
    
    # Output metadata
    output_id: Optional[str] = None
    generated_at: Optional[str] = None
    synthesis_version: str = "v1"
    
    def __post_init__(self):
        """Set generated_at if not provided."""
        if self.generated_at is None:
            self.generated_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "what_matters_now": [item.to_dict() for item in self.what_matters_now],
            "blocked_items": [item.to_dict() for item in self.blocked_items],
            "next_actions": [item.to_dict() for item in self.next_actions],
            "approval_queue": [item.to_dict() for item in self.approval_queue],
            "output_id": self.output_id,
            "generated_at": self.generated_at,
            "synthesis_version": self.synthesis_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DecisionOutput:
        """Deserialize from dictionary."""
        return cls(
            what_matters_now=[DecisionItem.from_dict(item) for item in data.get("what_matters_now", [])],
            blocked_items=[DecisionItem.from_dict(item) for item in data.get("blocked_items", [])],
            next_actions=[DecisionItem.from_dict(item) for item in data.get("next_actions", [])],
            approval_queue=[DecisionItem.from_dict(item) for item in data.get("approval_queue", [])],
            output_id=data.get("output_id"),
            generated_at=data.get("generated_at"),
            synthesis_version=data.get("synthesis_version", "v1"),
        )
    
    def summary(self) -> Dict[str, int]:
        """Return count summary for each output."""
        return {
            "what_matters_now_count": len(self.what_matters_now),
            "blocked_items_count": len(self.blocked_items),
            "next_actions_count": len(self.next_actions),
            "approval_queue_count": len(self.approval_queue),
        }