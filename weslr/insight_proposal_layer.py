# insight_proposal_layer.py - WESLR v94h: Deterministic Insight Proposal Layer
# Read-only transformation layer that packages v94g deterministic synthesis outputs
# into governed insight proposal structures for operator review.
# Additive only, read-only only, no mutation, no auto-approval, no auto-application.
# No recommendations, no predictive modeling, no backend/service/UI.
# No TIA/C#/orchestration.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .deterministic_synthesis import (
    DeterministicSynthesisResult,
    PatternGrouping,
    ApprovalReasonGrouping,
    ProposalOutcomeGrouping,
    ConfidenceTrendSummary,
    BottleneckRecurrenceSummary,
)
from .change_proposals import ChangeProposal, ProposalState
from .audit_ledger import AuditLedgerEngine
from .operator_lifecycle import LifecycleTimeline, LifecycleTransition


# ============================================================================
# INSIGHT PROPOSAL PAYLOAD DATA MODELS
# ============================================================================


@dataclass
class InsightProposalPayload:
    """Governed insight proposal payload for operator review.
    
    Packages deterministic synthesis outputs as governed proposals.
    Read-only transformation only - no mutation, no recommendations.
    
    Contains:
    - Proposal context (proposal_id, title, description)
    - Proposal structure (synthesis_source, proposal_type, priority)
    - Synthesis data (pattern_summaries, grouped_rationale, etc.)
    - Governance metadata (validation_requirements, rollback_expectations)
    """
    
    proposal_id: str
    title: str
    description: str
    
    # Proposal structure
    proposal_type: str  # "pattern_summary", "rationale_grouping", "recurrence_summary", "confidence_summary"
    priority: str = "medium"  # low, medium, high
    synthesis_source: str = "v94g_deterministic_synthesis"
    
    # Synthesis data (read-only from v94g)
    pattern_summaries: List[Dict[str, Any]] = field(default_factory=list)
    grouped_rationale: List[Dict[str, Any]] = field(default_factory=list)
    recurrence_summaries: List[Dict[str, Any]] = field(default_factory=list)
    confidence_summaries: List[Dict[str, Any]] = field(default_factory=list)
    
    # Governance
    validation_requirements: List[str] = field(default_factory=list)
    rollback_expectations: List[str] = field(default_factory=list)
    
    # Evidence integration
    evidence_claim_ids: List[str] = field(default_factory=list)
    evidence_chain_ids: List[str] = field(default_factory=list)
    evidence_summary: str = ""
    evidence_confidence: float = 0.0
    
    # State
    current_state: str = "pending_review"
    approval_state: str = "pending"
    created_at: str = ""
    
    # Source tracking
    source_record_count: int = 0
    synthesis_scope: str = "global"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for export."""
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "description": self.description,
            "proposal_type": self.proposal_type,
            "priority": self.priority,
            "synthesis_source": self.synthesis_source,
            "pattern_summaries": self.pattern_summaries,
            "grouped_rationale": self.grouped_rationale,
            "recurrence_summaries": self.recurrence_summaries,
            "confidence_summaries": self.confidence_summaries,
            "validation_requirements": self.validation_requirements,
            "rollback_expectations": self.rollback_expectations,
            "evidence_claim_ids": self.evidence_claim_ids,
            "evidence_chain_ids": self.evidence_chain_ids,
            "evidence_summary": self.evidence_summary,
            "evidence_confidence": self.evidence_confidence,
            "current_state": self.current_state,
            "approval_state": self.approval_state,
            "created_at": self.created_at,
            "source_record_count": self.source_record_count,
            "synthesis_scope": self.synthesis_scope,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string for export."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# INSIGHT PROPOSAL EXPORTER
# ============================================================================


class InsightProposalExporter:
    """Export insight proposal payloads in governance-ready formats.
    
    Machine-readable JSON + operator-readable text formats.
    No recommendations, no predictive modeling.
    """
    
    @staticmethod
    def format_proposal(proposal: InsightProposalPayload) -> str:
        """Format proposal for operator readability."""
        lines = [
            "=" * 60,
            "INSIGHT PROPOSAL",
            "=" * 60,
            f"Proposal ID: {proposal.proposal_id}",
            f"Title: {proposal.title}",
            f"Type: {proposal.proposal_type}",
            f"Priority: {proposal.priority}",
            f"State: {proposal.current_state}",
            f"Approval: {proposal.approval_state}",
            "",
            f"Source Records: {proposal.source_record_count}",
            f"Synthesis Scope: {proposal.synthesis_scope}",
            "",
        ]
        
        # Pattern Summaries
        if proposal.pattern_summaries:
            lines.append("-" * 40)
            lines.append("PATTERN SUMMARIES")
            lines.append("-" * 40)
            for i, ps in enumerate(proposal.pattern_summaries, 1):
                lines.append(f"  Pattern {i}: {ps.get('pattern_type', 'unknown')}")
                lines.append(f"    Frequency: {ps.get('frequency', 0)}")
                lines.append(f"    Members: {ps.get('member_record_ids', [])}")
                lines.append("")
        
        # Grouped Rationale
        if proposal.grouped_rationale:
            lines.append("-" * 40)
            lines.append("GROUPED RATIONALE")
            lines.append("-" * 40)
            for i, gr in enumerate(proposal.grouped_rationale, 1):
                lines.append(f"  Reason {i}: {gr.get('reason_text', 'unknown')}")
                lines.append(f"    Frequency: {gr.get('frequency', 0)}")
                lines.append(f"    Approval Rate: {gr.get('approval_rate', 0):.1%}")
                lines.append("")
        
        # Recurrence Summaries
        if proposal.recurrence_summaries:
            lines.append("-" * 40)
            lines.append("RECURRENCE SUMMARIES")
            lines.append("-" * 40)
            for i, rs in enumerate(proposal.recurrence_summaries, 1):
                lines.append(f"  Recurrence {i}: {rs.get('bottleneck_type', 'unknown')}")
                lines.append(f"    Category: {rs.get('bottleneck_category', 'unknown')}")
                lines.append(f"    Frequency: {rs.get('frequency', 0)}")
                lines.append("")
        
        # Confidence Summaries
        if proposal.confidence_summaries:
            lines.append("-" * 40)
            lines.append("CONFIDENCE SUMMARIES")
            lines.append("-" * 40)
            for i, cs in enumerate(proposal.confidence_summaries, 1):
                lines.append(f"  Trend {i}: {cs.get('trend_type', 'unknown')}")
                lines.append(f"    Direction: {cs.get('confidence_direction', 'unknown')}")
                lines.append(f"    Before: {cs.get('before_confidence', 0):.2f}")
                lines.append(f"    After: {cs.get('after_confidence', 0):.2f}")
                lines.append("")
        
        # Governance
        lines.append("-" * 40)
        lines.append("GOVERNANCE")
        lines.append("-" * 40)
        lines.append(f"Validation Requirements: {len(proposal.validation_requirements)}")
        lines.append(f"Rollback Expectations: {len(proposal.rollback_expectations)}")
        lines.append(f"Evidence Confidence: {proposal.evidence_confidence:.2f}")
        lines.append("")
        
        return "\n".join(lines)
    
    @classmethod
    def export_to_json(cls, proposal: InsightProposalPayload, filepath: Optional[str] = None) -> str:
        """Export proposal to JSON format."""
        json_output = proposal.to_json()
        if filepath:
            with open(filepath, "w") as f:
                f.write(json_output)
        return json_output
    
    @classmethod
    def export_to_text(cls, proposal: InsightProposalPayload, filepath: Optional[str] = None) -> str:
        """Export proposal to text format for operator readability."""
        text_output = cls.format_proposal(proposal)
        if filepath:
            with open(filepath, "w") as f:
                f.write(text_output)
        return text_output


# ============================================================================
# INSIGHT PROPOSAL CONVERTER
# ============================================================================


class InsightProposalConverter:
    """Convert v94g deterministic synthesis outputs to v94h insight proposals.
    
    Read-only transformation only.
    No mutation, no recommendations, no predictive modeling.
    """
    
    def __init__(self, audit_ledger_engine: Optional[AuditLedgerEngine] = None):
        """Initialize converter."""
        self.audit_ledger_engine = audit_ledger_engine
        self._conversion_count: int = 0
    
    def convert(self, synthesis_result: DeterministicSynthesisResult) -> List[InsightProposalPayload]:
        """Convert v94g synthesis result to insight proposals.
        
        Read-only transformation of synthesis outputs.
        Each synthesis category becomes a separate proposal.
        No auto-approval, no auto-application.
        """
        proposals = []
        
        # Convert pattern groupings to proposals
        pattern_proposals = self._convert_pattern_groupings(synthesis_result)
        proposals.extend(pattern_proposals)
        
        # Convert approval reason groupings to proposals
        rationale_proposals = self._convert_approval_reasons(synthesis_result)
        proposals.extend(rationale_proposals)
        
        # Convert proposal outcome groupings to proposals
        outcome_proposals = self._convert_proposal_outcomes(synthesis_result)
        proposals.extend(outcome_proposals)
        
        # Convert confidence trend summaries to proposals
        confidence_proposals = self._convert_confidence_trends(synthesis_result)
        proposals.extend(confidence_proposals)
        
        # Convert bottleneck recurrence summaries to proposals
        bottleneck_proposals = self._convert_bottleneck_recurrences(synthesis_result)
        proposals.extend(bottleneck_proposals)
        
        self._conversion_count += len(proposals)
        return proposals
    
    def _convert_pattern_groupings(self, synthesis: DeterministicSynthesisResult) -> List[InsightProposalPayload]:
        """Convert pattern groupings to proposals."""
        if not synthesis.pattern_groupings:
            return []
        
        proposals = []
        for i, pg in enumerate(synthesis.pattern_groupings):
            proposal = InsightProposalPayload(
                proposal_id=f"proposal_pattern_{i:03d}",
                title=f"Pattern Summary: {pg.pattern_type}",
                description=f"Stable pattern grouping from {pg.frequency} records",
                proposal_type="pattern_summary",
                pattern_summaries=[pg.to_dict()],
                source_record_count=len(pg.member_record_ids),
                synthesis_scope=synthesis.synthesis_scope,
                created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                validation_requirements=["operator_review", "pattern_validation"],
                evidence_claim_ids=pg.member_record_ids,
                evidence_confidence=0.8,  # Stable patterns have high confidence
            )
            proposals.append(proposal)
        
        return proposals
    
    def _convert_approval_reasons(self, synthesis: DeterministicSynthesisResult) -> List[InsightProposalPayload]:
        """Convert approval reason groupings to proposals."""
        if not synthesis.approval_reason_groupings:
            return []
        
        proposals = []
        for i, arg in enumerate(synthesis.approval_reason_groupings):
            proposal = InsightProposalPayload(
                proposal_id=f"proposal_rationale_{i:03d}",
                title=f"Grouped Rationale: {arg.reason_type}",
                description=f"Approval reason grouping: {arg.reason_text}",
                proposal_type="rationale_grouping",
                grouped_rationale=[arg.to_dict()],
                source_record_count=len(arg.member_record_ids),
                synthesis_scope=synthesis.synthesis_scope,
                created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                validation_requirements=["operator_review", "rationale_validation"],
                evidence_claim_ids=arg.member_record_ids,
                evidence_confidence=arg.approval_rate,
            )
            proposals.append(proposal)
        
        return proposals
    
    def _convert_proposal_outcomes(self, synthesis: DeterministicSynthesisResult) -> List[InsightProposalPayload]:
        """Convert proposal outcome groupings to proposals."""
        if not synthesis.proposal_outcome_groupings:
            return []
        
        proposals = []
        for i, pog in enumerate(synthesis.proposal_outcome_groupings):
            proposal = InsightProposalPayload(
                proposal_id=f"proposal_outcome_{i:03d}",
                title=f"Proposal Outcome: {pog.outcome_category}",
                description=f"Recurring proposal outcome: {pog.frequency} proposals",
                proposal_type="outcome_summary",
                recurrence_summaries=[{
                    "outcome_category": pog.outcome_category,
                    "frequency": pog.frequency,
                    "member_ids": pog.member_proposal_ids,
                }],
                source_record_count=len(pog.member_proposal_ids),
                synthesis_scope=synthesis.synthesis_scope,
                created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                validation_requirements=["operator_review", "outcome_validation"],
                evidence_claim_ids=pog.member_proposal_ids,
                evidence_confidence=0.7,
            )
            proposals.append(proposal)
        
        return proposals
    
    def _convert_confidence_trends(self, synthesis: DeterministicSynthesisResult) -> List[InsightProposalPayload]:
        """Convert confidence trend summaries to proposals."""
        if not synthesis.confidence_trend_summaries:
            return []
        
        proposals = []
        for i, cts in enumerate(synthesis.confidence_trend_summaries):
            proposal = InsightProposalPayload(
                proposal_id=f"proposal_confidence_{i:03d}",
                title=f"Confidence Trend: {cts.confidence_direction}",
                description=f"Confidence trend: {cts.before_confidence:.2f} → {cts.after_confidence:.2f}",
                proposal_type="confidence_summary",
                confidence_summaries=[cts.to_dict()],
                source_record_count=len(cts.member_record_ids),
                synthesis_scope=synthesis.synthesis_scope,
                created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                validation_requirements=["operator_review", "confidence_validation"],
                evidence_claim_ids=cts.member_record_ids,
                evidence_confidence=abs(cts.confidence_change),
            )
            proposals.append(proposal)
        
        return proposals
    
    def _convert_bottleneck_recurrences(self, synthesis: DeterministicSynthesisResult) -> List[InsightProposalPayload]:
        """Convert bottleneck recurrence summaries to proposals."""
        if not synthesis.bottleneck_recurrence_summaries:
            return []
        
        proposals = []
        for i, brs in enumerate(synthesis.bottleneck_recurrence_summaries):
            proposal = InsightProposalPayload(
                proposal_id=f"proposal_bottleneck_{i:03d}",
                title=f"Bottleneck Recurrence: {brs.bottleneck_type}",
                description=f"Bottleneck category: {brs.bottleneck_category}",
                proposal_type="recurrence_summary",
                recurrence_summaries=[brs.to_dict()],
                source_record_count=len(brs.member_bottleneck_ids),
                synthesis_scope=synthesis.synthesis_scope,
                created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                validation_requirements=["operator_review", "bottleneck_validation"],
                evidence_claim_ids=brs.member_bottleneck_ids,
                evidence_confidence=0.6,  # Recurrences have moderate confidence
            )
            proposals.append(proposal)
        
        return proposals
    
    def get_conversion_count(self) -> int:
        """Get total conversion count (read-only counter)."""
        return self._conversion_count


# ============================================================================
# INSIGHT PROPOSAL LAYER (MAIN ENTRY POINT)
# ============================================================================


class InsightProposalLayer:
    """v94h Governed Insight Proposal Layer.
    
    Main entry point for insight-to-proposal transformation.
    Read-only transformation only.
    No mutation, no auto-approval, no auto-application.
    """
    
    def __init__(self, audit_ledger_engine: Optional[AuditLedgerEngine] = None):
        """Initialize layer."""
        self.audit_ledger_engine = audit_ledger_engine or AuditLedgerEngine()
        self.converter = InsightProposalConverter(self.audit_ledger_engine)
        self.exporter = InsightProposalExporter()
        self._last_proposals: List[InsightProposalPayload] = []
    
    def process_synthesis_result(self, synthesis_result: DeterministicSynthesisResult) -> List[InsightProposalPayload]:
        """Process v94g synthesis result and generate proposals.
        
        Read-only transformation.
        Returns list of governed insight proposals for operator review.
        """
        proposals = self.converter.convert(synthesis_result)
        self._last_proposals = proposals
        return proposals
    
    def export_proposals_to_json(self, proposals: Optional[List[InsightProposalPayload]] = None, 
                                  filepath: Optional[str] = None) -> str:
        """Export proposals to JSON format."""
        if proposals is None:
            proposals = self._last_proposals
        
        if len(proposals) == 1:
            return self.exporter.export_to_json(proposals[0], filepath)
        
        # Multiple proposals - export as array
        data = [p.to_dict() for p in proposals]
        json_output = json.dumps(data, indent=2)
        if filepath:
            with open(filepath, "w") as f:
                f.write(json_output)
        return json_output
    
    def export_proposals_to_text(self, proposals: Optional[List[InsightProposalPayload]] = None,
                                  filepath: Optional[str] = None) -> str:
        """Export proposals to text format for operator readability."""
        if proposals is None:
            proposals = self._last_proposals
        
        texts = []
        for i, proposal in enumerate(proposals, 1):
            text = f"=== PROPOSAL {i} ===\n\n"
            text += self.exporter.format_proposal(proposal)
            texts.append(text)
        
        combined = "\n\n".join(texts)
        if filepath:
            with open(filepath, "w") as f:
                f.write(combined)
        return combined
    
    def get_last_proposals(self) -> List[InsightProposalPayload]:
        """Get last generated proposals (read-only)."""
        return self._last_proposals
    
    def get_conversion_count(self) -> int:
        """Get total conversion count."""
        return self.converter.get_conversion_count()
