"""Decision Layer - WESLR v1 (Recovered - Clean Rebuild)

Unified decision layer that synthesizes WESLR state into operator-facing output.

This is a clean rebuild from the current active contract, not from corrupted history.

Contract:
- WESLR synthesizes internal perspectives into one transparent operator-facing judgment
- WESLR does not expose unresolved internal disagreement by default
- All outputs are read-only projections of existing WESLR layers
- No autonomous execution without operator approval

Scope:
- what_matters_now: top items requiring immediate attention
- blocked_items: items that cannot proceed with explicit reason
- next_actions: ordered recommended actions with provenance
- approval_queue: items awaiting operator decision with context

Non-scope:
- human values, life meaning, emotional manipulation
- irreversible external actions without approval
- what the operator "should want"
- moral/ethical judgments

Human-in-the-loop:
- WESLR synthesizes. Operator decides.
- All approval-requiring items need explicit operator approval
- Operator can override any priority ranking
- Only operator can accept risks above threshold

Additive only. No modifications to existing modules.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try relative imports first (for module context), then absolute
try:
    from .decision_output import DecisionItem, DecisionOutput
    from .prioritization_scorer import ScoringFactors, composite_score, score_with_explanation
except ImportError:
    from decision_output import DecisionItem, DecisionOutput
    from prioritization_scorer import ScoringFactors, composite_score, score_with_explanation


@dataclass
class DecisionLayerConfig:
    """Configuration for DecisionLayer."""
    
    # Paths to read-only state sources
    operator_state_path: Optional[str] = None
    
    # Limits on output size
    max_what_matters_now: int = 3
    max_next_actions: int = 5
    
    # Confidence thresholds
    confidence_threshold: float = 0.50
    
    # Source module identifiers
    source_modules: Dict[str, str] = field(default_factory=lambda: {
        "escalation": "weslr.escalation",
        "governance": "weslr.internal_reasoning_graph.governance",
        "proposals": "weslr.change_proposals",
        "capsule": "weslr.capsule_policy",
        "scorecard": "weslr.governance_scorecard",
        "proof": "weslr.proof_gate",
        "launch": "weslr.launch_gate",
        "trust": "weslr.trust_dynamics",
        "lifecycle": "weslr.operator_lifecycle",
        "capability": "weslr.capability_boundary",
        "state": "weslr.state",
    })


class DecisionLayer:
    """Unified WESLR decision layer.
    
    Synthesizes outputs from multiple WESLR layers into one transparent
    operator-facing decision output.
    
    Read-only. No state mutation. Pure synthesis.
    """
    
    def __init__(self, config: Optional[DecisionLayerConfig] = None):
        """Initialize decision layer with optional configuration.
        
        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or DecisionLayerConfig()
        self._loaded = False
        self._cache: Dict[str, Any] = {}
    
    # ========================================================================
    # Read-only adapters to existing WESLR modules
    # These consume existing outputs without modifying source modules
    # ========================================================================
    
    def _load_operator_state(self) -> Dict[str, Any]:
        """Load operator state from OPERATOR_STATE.json.
        
        Read-only adapter to operator state module.
        Returns current operator state without modification.
        
        Returns:
            Dict with operator state
        """
        try:
            state_path = self.config.operator_state_path or \
                Path(__file__).parent / "operator_control" / "OPERATOR_STATE.json"
            
            with open(state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # Graceful fallback if state unavailable
            return {
                "next_priority": None,
                "active_bottlenecks": {},
                "next_workflow_recommendation": {},
            }
    
    def _get_escalation_items(self) -> List[Dict[str, Any]]:
        """Get escalation items from escalation module.
        
        Read-only adapter to escalation module.
        Returns current escalations without modification.
        
        Returns:
            List of escalation items
        """
        try:
            from .escalation import get_escalations
            
            escalations = get_escalations()
            
            # Filter to only current escalations
            current = [esc for esc in escalations if esc.get("status", "active") == "active"]
            
            return current
        except Exception:
            # Graceful fallback if escalation unavailable
            return []
    
    def _get_governance_review_items(self) -> List[Dict[str, Any]]:
        """Get governance review items from governance module.
        
        Read-only adapter to governance module.
        Returns items needing governance review without modification.
        
        Returns:
            List of governance review items
        """
        try:
            from .change_proposals import get_execution_gate
            from .governance_surface import GovernanceEngine, ProposalGovernanceView
            
            gate = get_execution_gate()
            engine = GovernanceEngine()
            
            # Get pending proposals
            pending = gate.get_pending_proposals()
            
            # Get governance views for each proposal
            items = []
            for proposal in pending:
                view = engine.get_proposal_view(proposal.proposal_id)
                if view:
                    items.append(view)
            
            return items
        except Exception:
            # Graceful fallback if governance unavailable
            return []
    
    def _get_evidence_state(self) -> Dict[str, Any]:
        """Get evidence state from evidence_intake module.
        
        Read-only adapter to evidence_intake module.
        Returns current evidence state without modification.
        
        Returns:
            Dict with evidence state
        """
        try:
            from .evidence_intake import EvidenceIngestion
            
            ingestion = EvidenceIngestion()
            
            # Check routing state
            base_dir = Path(__file__).parent
            routing_file = base_dir.parent / "evidence_routing_state.json"
            
            if not routing_file.exists():
                return {
                    "requires_attention": False,
                    "pending_evidence": 0,
                    "approved_evidence": 0,
                    "rejected_evidence": 0,
                    "total_evidence": 0,
                }
            
            with open(routing_file, "r", encoding="utf-8") as f:
                routing_state = json.load(f)
            
            pending = routing_state.get("pending", [])
            evidence = routing_state.get("evidence", [])
            
            return {
                "requires_attention": len(pending) > 0,
                "pending_evidence": len(pending),
                "approved_evidence": len(evidence),
                "rejected_evidence": 0,
                "total_evidence": len(evidence) + len(pending),
                "routing_state": routing_state,
            }
        except Exception:
            # Graceful fallback if evidence state unavailable
            return {
                "requires_attention": False,
                "pending_evidence": 0,
                "approved_evidence": 0,
                "rejected_evidence": 0,
                "total_evidence": 0,
            }
    
    def _get_proposal_items(self) -> List[Dict[str, Any]]:
        """Get proposal items from change_proposals module.
        
        Read-only adapter to change_proposals module.
        Returns pending proposals without modification.
        
        Returns:
            List of proposal items
        """
        try:
            from .change_proposals import get_execution_gate
            
            gate = get_execution_gate()
            pending = gate.get_pending_proposals()
            
            return [p.to_dict() for p in pending]
        except Exception:
            # Graceful fallback if proposals unavailable
            return []
    
    def _get_capsule_state(self) -> Dict[str, Any]:
        """Get capsule state from capsule_policy module.
        
        Read-only adapter to capsule_policy module.
        Returns capsule freshness state without modification.
        
        Returns:
            Dict with capsule state
        """
        try:
            from .capsule_policy import CapsuleFreshnessPolicy
            
            policy = CapsuleFreshnessPolicy()
            result = policy.get_capsule_state()
            
            return {
                "capsule_state": result,
                "capsule_valid": result.get("status") == "fresh",
            }
        except Exception:
            # Graceful fallback if capsule unavailable
            return {
                "capsule_state": {},
                "capsule_valid": False,
            }
    
    def _get_capability_blocks(self) -> List[Dict[str, Any]]:
        """Get capability blocks from capability_boundary module.
        
        Read-only adapter to capability_boundary module.
        Returns capability blocks without modification.
        
        Returns:
            List of capability blocks
        """
        try:
            from .capability_boundary import CapabilityBoundaryEngine, CapabilityAction
            
            engine = CapabilityBoundaryEngine()
            default_boundary = engine.get_default_boundary()
            
            blocks = []
            
            # Get prohibited capabilities (highest severity)
            for cap in default_boundary.prohibited_capabilities:
                blocks.append({
                    "capability": cap.get("capability"),
                    "action": CapabilityAction.PROHIBIT.value,
                    "reason": "Capability prohibited by boundary policy",
                    "boundary_role": default_boundary.role,
                    "severity": "high",
                })
            
            # Get restricted capabilities (medium severity)
            for cap in default_boundary.restricted_capabilities:
                blocks.append({
                    "capability": cap.get("capability"),
                    "action": CapabilityAction.RESTRICT.value,
                    "reason": "Capability restricted by boundary policy",
                    "boundary_role": default_boundary.role,
                    "severity": "medium",
                })
            
            return blocks
        except Exception:
            # Graceful fallback if capability_boundary unavailable
            return []
    
    def _get_proof_blocks(self) -> List[Dict[str, Any]]:
        """Get proof blocks from proof_gate module.
        
        Read-only adapter to proof_gate module.
        Returns proof blocks without modification.
        
        Returns:
            List of proof blocks
        """
        try:
            from .proof_gate import ProofGateEngine, ProofStatus
            from .change_proposals import get_execution_gate
            
            gate = get_execution_gate()
            engine = ProofGateEngine(execution_gate=gate)
            
            # Get approved proposals to check proof status
            approved = gate.get_approved_proposals()
            
            blocks = []
            for proposal in approved:
                # Evaluate readiness for each approved proposal
                readiness = engine.evaluate_readiness(
                    plan_id=f"plan-{proposal.proposal_id[:8]}",
                    proposal_id=proposal.proposal_id,
                )
                
                # Add missing proofs as blocks
                for proof in readiness.proofs:
                    if proof.get("status") in [ProofStatus.NOT_REQUESTED.value, ProofStatus.REQUESTED.value]:
                        blocks.append({
                            "proof_type": proof.get("proof_type"),
                            "status": proof.get("status"),
                            "description": proof.get("description", "Proof required"),
                            "proposal_id": proposal.proposal_id,
                            "blocking": True,
                        })
            
            return blocks
        except Exception:
            # Graceful fallback if proof_gate unavailable
            return []
    
    def _get_outcome_feedback_context(
        self,
        recommendation_type: str,
        context_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Extract outcome feedback context for decision items.
        
        Read-only adapter to outcome_feedback module.
        Queries historical outcomes for similar decisions.
        
        Args:
            recommendation_type: Type of recommendation (e.g., "escalation", "priority")
            context_tags: Optional tags to match
            
        Returns:
            Dict with similar_recommendations, average_quality, signal
        """
        try:
            from .outcome_feedback import get_outcome_feedback
            
            # Query feedback for the recommendation type
            feedback = get_outcome_feedback(
                recommendation_type=recommendation_type,
                context_tags=context_tags or [],
            )
            
            # Extract summary
            similar_count = len(feedback.get("similar_recommendations", []))
            avg_quality = feedback.get("average_quality", 0.5)
            
            if similar_count > 0:
                signal = f"Found {similar_count} similar recommendations"
            else:
                signal = "No similar recommendations found"
            
            return {
                "has_outcome_context": similar_count > 0,
                "similar_recommendations": similar_count,
                "average_quality": avg_quality,
                "signal": signal,
            }
        except Exception:
            # Graceful fallback if outcome_feedback unavailable
            return {
                "has_outcome_context": False,
                "similar_recommendations": 0,
                "average_quality": 0.5,
                "signal": None,
            }
    
    def _get_calibration_context(self, domain: str = "decision") -> Dict[str, Any]:
        """Extract calibration context for domain.
        
        Read-only adapter to governance_scorecard module.
        Queries calibration confidence for a domain.
        
        Args:
            domain: Domain for calibration (e.g., "priority", "escalation")
            
        Returns:
            Dict with calibration_count, confidence_adjustment, ranking_adjustment
        """
        try:
            from .governance_scorecard import GovernanceBenchmarkEngine
            
            engine = GovernanceBenchmarkEngine()
            calibrations = engine.get_domain_calibrations(domain)
            
            total_adjustment = sum(
                cal.get("confidence_adjustment", 0.0) for cal in calibrations
            )
            total_ranking = sum(
                cal.get("recommendation_adjustment", 0.0) for cal in calibrations
            )
            
            avg_confidence_adj = total_adjustment / len(calibrations) if calibrations else 0.0
            avg_ranking_adj = total_ranking / len(calibrations) if calibrations else 0.0
            
            if avg_confidence_adj >= 0.1:
                signal = "Forecasts have been accurate"
            elif avg_confidence_adj >= -0.1:
                signal = "Forecasts are within tolerance"
            else:
                signal = "Forecasts need refinement"
            
            return {
                "has_calibration_context": len(calibrations) > 0,
                "calibration_count": len(calibrations),
                "confidence_adjustment": avg_confidence_adj,
                "ranking_adjustment": avg_ranking_adj,
                "signal": signal,
            }
        except Exception:
            # Graceful fallback if calibration unavailable
            return {
                "has_calibration_context": False,
                "calibration_count": 0,
                "confidence_adjustment": 0.0,
                "ranking_adjustment": 0.0,
                "signal": None,
            }
    
    def _get_forecast_context(
        self,
        item_title: str,
        item_description: str,
        domain: str = "decision",
        affected_subsystems: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Extract forecast context for a decision item.
        
        Read-only adapter to forecast module.
        Queries forecasted impact to adjust priority ordering.
        
        Args:
            item_title: Title of the decision item
            item_description: Description of the decision
            domain: Domain for forecasting
            affected_subsystems: Optional list of affected subsystems
        
        Returns:
            Dict with net_impact, confidence, positive/negative effects, signal
        """
        try:
            from .forecast import forecast_suggestion
            
            # Generate forecast for the decision item
            forecast = forecast_suggestion(
                title=item_title,
                description=item_description,
                domain=domain,
                affected_subsystems=affected_subsystems or [],
            )
            
            # Extract forecast summary
            net_impact = forecast.summary.net_impact
            confidence = forecast.confidence
            positive_effects = forecast.summary.total_positive_effects
            negative_effects = forecast.summary.total_negative_effects
            
            # Determine signal based on net impact
            if net_impact > 0.5:
                signal = "Forecast: strongly positive"
            elif net_impact > 0.2:
                signal = "Forecast: positive"
            elif net_impact > -0.2:
                signal = "Forecast: neutral"
            elif net_impact > -0.5:
                signal = "Forecast: negative"
            else:
                signal = "Forecast: strongly negative"
            
            # Calculate priority adjustment
            if net_impact > 0.5:
                priority_adjustment = 2
            elif net_impact > 0.2:
                priority_adjustment = 1
            elif net_impact > -0.2:
                priority_adjustment = 0
            elif net_impact > -0.5:
                priority_adjustment = -1
            else:
                priority_adjustment = -2
            
            return {
                "has_forecast_context": True,
                "net_impact": net_impact,
                "confidence": confidence,
                "positive_effects": positive_effects,
                "negative_effects": negative_effects,
                "priority_adjustment": priority_adjustment,
                "signal": signal,
                "short_term_benefit": forecast.summary.short_term_benefit,
                "long_term_benefit": forecast.summary.long_term_benefit,
            }
        except Exception as e:
            # Graceful fallback if forecast unavailable
            return {
                "has_forecast_context": False,
                "net_impact": 0.0,
                "confidence": 0.0,
                "priority_adjustment": 0,
                "signal": None,
                "error": str(e),
            }
    
    def _get_similar_decisions(
        self,
        context: str,
        item_type: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """Retrieve similar historical decisions from decision memory.
        
        Read-only adapter to decision_memory module.
        Surfaces similar decisions for provenance without altering confidence.
        
        Args:
            context: Context to match (e.g., item title, reason)
            item_type: Optional type filter (e.g., "escalation", "priority")
            limit: Maximum number of similar decisions to return
        
        Returns:
            Dict with similar_decisions list, similar_count, last_outcome, signal
        """
        try:
            from .decision_memory import (
                get_decision_history,
                get_recurring_patterns,
                DecisionRecord,
                ProposalPattern,
            )
            
            # Get decision history
            # Note: decision_memory requires proposal_id, so we search patterns
            patterns = get_recurring_patterns()
            
            # Find similar decisions by context matching
            similar_decisions = []
            
            # Match by context prefix (first 50 chars)
            context_prefix = context[:50].lower() if context else ""
            
            for pattern in patterns:
                if pattern.claim_text_prefix.lower() in context_prefix or context_prefix in pattern.claim_text_prefix.lower():
                    # Found matching pattern
                    last_outcome = "approved" if pattern.outcomes.get("approved", 0) > pattern.outcomes.get("rejected", 0) else "rejected"
                    
                    similar_decisions.append({
                        "decision_id": pattern.pattern_id,
                        "title": pattern.claim_text_prefix[:50] + "...",
                        "outcome": last_outcome,
                        "timestamp": pattern.last_update,
                        "resolution": f"{pattern.outcomes.get('approved', 0)} approved, {pattern.outcomes.get('rejected', 0)} rejected",
                        "approval_rate": pattern.approval_rate,
                        "total_count": pattern.total_count,
                    })
                    
                    if len(similar_decisions) >= limit:
                        break
            
            # If no patterns found, return empty but valid structure
            if not similar_decisions:
                return {
                    "has_memory_context": False,
                    "similar_count": 0,
                    "similar_decisions": [],
                    "last_similar_outcome": None,
                    "signal": "No similar decisions found",
                }
            
            # Determine signal based on outcomes
            last_outcome = similar_decisions[0].get("outcome", "unknown")
            total_similar = sum(d.get("total_count", 1) for d in similar_decisions)
            
            if last_outcome == "approved":
                signal = "Similar issue handled before (approved)"
            elif last_outcome == "rejected":
                signal = "Similar issue handled before (rejected)"
            else:
                signal = "Similar issue handled before"
            
            return {
                "has_memory_context": True,
                "similar_count": len(similar_decisions),
                "total_similar_occurrences": total_similar,
                "similar_decisions": similar_decisions[:limit],
                "last_similar_outcome": last_outcome,
                "signal": signal,
            }
        except Exception as e:
            # Graceful fallback if decision_memory unavailable
            return {
                "has_memory_context": False,
                "similar_count": 0,
                "similar_decisions": [],
                "last_similar_outcome": None,
                "signal": None,
                "error": str(e),
            }
    
    def _get_related_concepts(
        self,
        context: str,
        item_type: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """Retrieve related concepts from concept graph.
        
        Read-only adapter to concept_graph module.
        Surfaces related concepts for provenance without altering ranking.
        
        Args:
            context: Context to match (e.g., item title, reason)
            item_type: Optional type filter (e.g., "escalation", "priority")
            limit: Maximum number of related concepts
        
        Returns:
            Dict with related concepts, top_concepts, signal
        """
        try:
            from .concept_graph import get_related_concepts
            
            # Get related concepts from concept graph
            result = get_related_concepts(context, limit=limit)
            
            # If no concepts found, return empty but valid structure
            if not result.get("has_concept_context"):
                return {
                    "has_concept_context": False,
                    "related_count": 0,
                    "top_concepts": [],
                    "signal": "No related concepts found",
                }
            
            return {
                "has_concept_context": True,
                "related_count": result.get("related_count", 0),
                "top_concepts": result.get("top_concepts", []),
                "signal": result.get("signal"),
            }
        except Exception as e:
            # Graceful fallback if concept_graph unavailable
            return {
                "has_concept_context": False,
                "related_count": 0,
                "top_concepts": [],
                "signal": None,
                "error": str(e),
            }
    
    # ========================================================================
    # Synthesis methods
    # These synthesize internal perspectives into one transparent judgment
    # ========================================================================
    
    def _synthesize_what_matters_now(self) -> List[DecisionItem]:
        """Synthesize top priority items from escalation and governance.
        
        Contract: WESLR synthesizes perspectives into one transparent judgment.
        Each item includes full provenance and confidence.
        
        Returns:
            List of DecisionItem for top priority items
        """
        items = []
        
        # Check for escalations first (highest priority)
        escalation_items = self._get_escalation_items()
        for esc in escalation_items:
            urgency = esc.get("urgency", "normal")
            urgency_level = urgency if urgency in ["low", "normal", "high", "critical"] else "normal"
            
            # Determine confidence from handoff package
            handoff = esc.get("handoff_package", {})
            confidence = handoff.get("confidence", 0.5) if handoff else 0.5
            
            # Build operator-clear title
            context_id = esc.get("context_id", "")
            esc_id_short = esc.get("escalation_id", "unknown")[:8]
            reason_text = esc.get("reason", "Unknown")
            
            if context_id:
                disambig = context_id[:20]
            else:
                disambig = f"#{esc_id_short}"
            
            title = f"Escalation: {reason_text} [{disambig}]"
            
            # Add outcome feedback context
            outcome_context = self._get_outcome_feedback_context(
                recommendation_type="escalation",
                context_tags=[reason_text] if reason_text else None,
            )
            
            if outcome_context.get("has_outcome_context"):
                confidence = min(1.0, max(0.0, confidence + outcome_context.get("confidence_adjustment", 0.0)))
            
            item = DecisionItem(
                title=title,
                reason=f"Requires {esc.get('required_role', 'operator')} attention",
                source_modules=[self.config.source_modules.get("escalation", "weslr.escalation")],
                confidence=confidence,
                recommended_action=f"Review escalation {esc.get('escalation_id', '')}",
                item_id=esc.get("escalation_id", "escalation-unknown"),
                urgency_level=urgency_level,
            )
            
            if outcome_context.get("has_outcome_context"):
                item.provenance["outcome_context"] = {
                    "similar_recommendations": outcome_context.get("similar_recommendations", 0),
                    "average_quality": outcome_context.get("average_quality", 0.5),
                    "signal": outcome_context.get("signal"),
                }
            
            items.append(item)
        
        # Check for governance review items
        governance_items = self._get_governance_review_items()
        for gov in governance_items:
            risk = gov.get("risk_level", "unknown")
            urgency = "high" if risk == "high" else "normal"
            
            confidence = 0.85 if gov.get("can_proceed") else 0.60
            
            blocking = gov.get("blocking_reasons", [])
            reason = gov.get("why_surfaced", "Requires operator review")
            if blocking:
                reason = f"Blocked: {', '.join(blocking[:2])}"
            
            item = DecisionItem(
                title=f"Governance: {gov.get('title', 'Unknown proposal')}",
                reason=reason,
                source_modules=[self.config.source_modules.get("governance", "weslr.governance_surface")],
                confidence=confidence,
                recommended_action=gov.get("recommended_action", "review"),
                item_id=gov.get("proposal_id", "governance-unknown"),
                urgency_level=urgency,
            )
            items.append(item)

        # Evidence sufficiency visibility (bounded, non-invasive)
        evidence_state = self._get_evidence_state()
        try:
            evidence_count = evidence_state.get("evidence_count", 0)
            coverage = evidence_state.get("coverage_domains", []) or []
            has_gap = evidence_count < 3 or len(coverage) < 2
        except Exception:
            evidence_count = 0
            coverage = []
            has_gap = False

        if has_gap:
            reason_parts = []
            if evidence_count < 3:
                reason_parts.append(f"evidence count low ({evidence_count})")
            if len(coverage) < 2:
                reason_parts.append("coverage gap")
            reason = "; ".join(reason_parts) or "evidence gap"
            item = DecisionItem(
                title="Evidence gap",
                reason=reason,
                source_modules=[self.config.source_modules.get("state", "weslr.state")],
                confidence=0.55,
                recommended_action="Plan targeted evidence acquisition",
                item_id="evidence-gap",
                urgency_level="high" if evidence_count < 2 else "normal",
            )
            items.append(item)
        
        # Sort items by priority score
        def get_priority_score(item: DecisionItem) -> float:
            """Calculate priority score based on urgency, forecast, and confidence."""
            urgency_scores = {"critical": 4.0, "high": 3.0, "normal": 2.0, "low": 1.0}
            base_score = urgency_scores.get(item.urgency_level, 2.0)
            
            forecast_context = item.provenance.get("forecast_context", {})
            net_impact = forecast_context.get("net_impact", 0.0)
            
            confidence = item.confidence or 0.5
            
            return base_score + net_impact + (confidence * 0.5)
        
        items.sort(key=get_priority_score, reverse=True)
        
        return items[:self.config.max_what_matters_now]
    
    def _synthesize_blocked_items(self) -> List[DecisionItem]:
        """Synthesize blocked items from capability, proof, and other layers.
        
        Contract: WESLR identifies blocks with explicit reason and source.
        Each item explains why it is blocked.
        
        Returns:
            List of DecisionItem for blocked items
        """
        items = []
        
        # Capability boundary blocks
        capability_blocks = self._get_capability_blocks()
        for cap in capability_blocks:
            title = f"Capability block: {cap.get('capability', 'unknown')}"
            reason = cap.get("reason", "Capability boundary")
            action = cap.get("action", "restrict")
            severity = cap.get("severity", "medium")
            urgency_level = "critical" if severity == "critical" else "high" if severity == "high" else "normal"
            item = DecisionItem(
                title=title,
                reason=f"{reason} ({action})",
                source_modules=[self.config.source_modules.get("capability", "weslr.capability_boundary")],
                confidence=0.50,
                recommended_action="Operator review/override required",
                item_id=f"cap-block-{cap.get('capability', 'unknown')}",
                urgency_level=urgency_level,
            )
            items.append(item)

        # Check for proposals awaiting approval
        state = self._load_operator_state()
        active_bottlenecks = state.get("active_bottlenecks", {})
        
        for category, bottlenecks in active_bottlenecks.items():
            if isinstance(bottlenecks, list):
                for bottleneck in bottlenecks:
                    if isinstance(bottleneck, str):
                        item = DecisionItem(
                            title=f"Bottleneck: {bottleneck}",
                            reason=f"Active bottleneck in {category} requiring attention",
                            source_modules=[self.config.source_modules["state"]],
                            confidence=0.80,
                            recommended_action=f"Address {bottleneck} bottleneck in {category}",
                            item_id=f"bottleneck-{category}-{bottleneck}",
                            urgency_level="normal",
                        )
                        items.append(item)
        
        return items
    
    def _synthesize_next_actions(self) -> List[DecisionItem]:
        """Synthesize recommended next actions from multiple sources.
        
        Contract: WESLR recommends actions with clear provenance.
        Each action shows where the recommendation came from.
        
        Returns:
            List of DecisionItem for next actions
        """
        items = []
        
        # Use operator state next_workflow_recommendation
        state = self._load_operator_state()
        next_rec = state.get("next_workflow_recommendation", {})
        
        if isinstance(next_rec, dict):
            selected_priority = next_rec.get("selected_priority")
            reason = next_rec.get("reason")
            
            if selected_priority and reason:
                item = DecisionItem(
                    title=f"Next workflow: {selected_priority}",
                    reason=reason,
                    source_modules=[self.config.source_modules["state"]],
                    confidence=0.85,
                    recommended_action=f"Execute weslr implement for {selected_priority}",
                    item_id=f"workflow-{selected_priority}",
                    urgency_level="normal",
                )
                items.append(item)
        
        return items[:self.config.max_next_actions]
    
    def _synthesize_approval_queue(self) -> List[DecisionItem]:
        """Synthesize items awaiting operator approval.
        
        Contract: WESLR surfaces approval items with context package.
        Each item explains why approval is needed.
        
        Returns:
            List of DecisionItem for approval queue
        """
        items = []
        
        # Check for checkpoint-related approvals
        state = self._load_operator_state()
        latest_checkpoint = state.get("latest_checkpoint")
        latest_sealed = state.get("latest_sealed_commit")
        
        # If checkpoint exists but not sealed, may need seal approval
        if latest_checkpoint and not latest_sealed:
            item = DecisionItem(
                title="Approval: Seal checkpoint",
                reason=f"Checkpoint {latest_checkpoint} not yet sealed",
                source_modules=[self.config.source_modules["state"]],
                confidence=0.75,
                recommended_action="Seal checkpoint or defer",
                item_id=f"checkpoint-seal-{latest_checkpoint}",
                urgency_level="high",
            )
            items.append(item)

        # Governance approvals (read-only surface)
        governance_items = self._get_governance_review_items()
        for gov in governance_items:
            item = DecisionItem(
                title=f"Approval required: {gov.get('title', 'proposal')}",
                reason=gov.get("why_surfaced", "Operator approval required"),
                source_modules=[self.config.source_modules.get("governance", "weslr.governance_surface")],
                confidence=0.60,
                recommended_action=gov.get("recommended_action", "review"),
                item_id=gov.get("proposal_id", "governance-approval"),
                urgency_level="high" if gov.get("risk_level") == "high" else "normal",
            )
            items.append(item)
        
        return items
    
    # ========================================================================
    # Main compute method
    # ========================================================================
    
    def compute(self) -> DecisionOutput:
        """Compute unified decision output from all WESLR layers.
        
        This is the main entry point for the Decision Layer.
        Synthesizes internal perspectives into one transparent operator-facing judgment.
        
        Contract:
        - Read-only: No modification to any WESLR state
        - Transparent: All sources documented in source_modules
        - Synthesized: Internal perspectives resolved into one judgment
        - Actionable: Each item has recommended_action
        
        Returns:
            DecisionOutput with four unified outputs
        """
        # Synthesize each output
        what_matters_now = self._synthesize_what_matters_now()
        blocked_items = self._synthesize_blocked_items()
        next_actions = self._synthesize_next_actions()
        approval_queue = self._synthesize_approval_queue()
        
        # Generate output
        output = DecisionOutput(
            what_matters_now=what_matters_now,
            blocked_items=blocked_items,
            next_actions=next_actions,
            approval_queue=approval_queue,
            output_id=f"decision-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            synthesis_version="v2",  # V2: Escalation, governance, evidence integration
        )
        
        return output
    
    def compute_with_context(self) -> Dict[str, Any]:
        """Compute decision output with additional context for debugging.
        
        Returns the DecisionOutput plus:
        - source module summary
        - scoring explanations for prioritized items
        - timestamp and version info
        
        Returns:
            Dictionary with output and context
        """
        output = self.compute()
        
        context = {
            "source_modules": self.config.source_modules,
            "config": {
                "max_what_matters_now": self.config.max_what_matters_now,
                "max_next_actions": self.config.max_next_actions,
                "confidence_threshold": self.config.confidence_threshold,
            },
            "scoring_weights": {
                "urgency_weight": 0.30,
                "safety_impact_weight": 0.25,
                "trust_confidence_weight": 0.20,
                "evidence_weight": 0.10,
                "precedent_weight": 0.10,
                "launch_readiness_weight": 0.05,
            },
        }
        
        return {
            "output": output.to_dict(),
            "context": context,
        }

    def compute_with_signals(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Compute decision and apply background/scientific signals if provided.
        Keeps default compute() unchanged; applies overlays when signals present.
        """
        output = self.compute().to_dict()
        # Provide a baseline confidence for downstream overlays
        if "confidence" not in output:
            wm_conf = [i.get("confidence", 0.6) for i in output.get("what_matters_now", [])]
            output["confidence"] = wm_conf[0] if wm_conf else 0.6
        bg = request.get("background_signals") if isinstance(request, dict) else None
        sci = request.get("scientific_guidance") if isinstance(request, dict) else None
        if bg:
            output = apply_background_signals(output, bg)
        if sci:
            output = apply_scientific_guidance(output, sci)

        # If capability blocks are present, suppress execution-oriented next actions
        blocked_titles = "\n".join(str(b.get("title", b)) if isinstance(b, dict) else str(b) for b in output.get("blocked_items", []))
        if "Capability block" in blocked_titles:
            filtered_actions = []
            for act in output.get("next_actions", []):
                text = str(act).lower()
                if "run " in text or "execute" in text:
                    continue
                filtered_actions.append(act)
            output["next_actions"] = filtered_actions
        return output


# --- Minimal signal hooks for E2E maturity tests (stale_data, underpowered_test) ---
def apply_background_signals(decision: dict, signals: list):
    """Apply background signals (minimal slice) to decision dict.
    Current supported type: stale_data
    """
    import copy
    updated = copy.deepcopy(decision)
    wm = updated.get("what_matters_now", [])
    blocked = updated.setdefault("blocked_items", [])
    actions = updated.setdefault("next_actions", [])
    base_conf = updated.get("confidence", 1.0)
    # Dedup/preference: collect, then reconcile
    collected = []
    for sig in signals or []:
        collected.append(sig)
    # Preference: if both contradiction_detected and contradictory findings exist for same target, keep scientific conflict
    filtered = []
    targets_with_scientific_conflict = set()
    for sig in collected:
        if isinstance(sig, dict) and sig.get("type") == "contradictory_findings_reconciliation_required":
            targets_with_scientific_conflict.add(sig.get("target"))
    for sig in collected:
        if isinstance(sig, dict) and sig.get("type") == "contradiction_detected" and sig.get("target") in targets_with_scientific_conflict:
            continue
        filtered.append(sig)
    for sig in filtered:
        if isinstance(sig, dict) and sig.get("type") == "stale_data":
            new_conf = max(0.0, base_conf - 0.15)
            updated["confidence"] = new_conf
            if wm and isinstance(wm[0], dict):
                wm[0]["confidence"] = max(0.0, wm[0].get("confidence", base_conf) - 0.15)
                wm[0]["reason"] = (wm[0].get("reason", "") + " Stale telemetry detected.").strip()
            target = sig.get("target", "telemetry")
            msg = f"Refresh telemetry for {target} (freshness {sig.get('freshness_days', '?')}d)"
            actions.append(msg)
            blocked.append(msg)
        elif isinstance(sig, dict) and sig.get("type") == "evidence_gap_unexecuted_paths":
            target = sig.get("target", "module")
            new_conf = max(0.0, base_conf - 0.1)
            updated["confidence"] = new_conf
            if wm and isinstance(wm[0], dict):
                wm[0]["confidence"] = max(0.0, wm[0].get("confidence", base_conf) - 0.1)
                wm[0]["reason"] = (wm[0].get("reason", "") + " Evidence gap: unexecuted paths.").strip()
            msg_action = f"Run targeted tests/logs for {target}"
            actions.append(msg_action)
            blocked.append(msg_action)
        elif isinstance(sig, dict) and sig.get("type") == "contradiction_detected":
            target = sig.get("target", "signal")
            new_conf = max(0.0, base_conf - 0.12)
            updated["confidence"] = new_conf
            if wm and isinstance(wm[0], dict):
                wm[0]["confidence"] = max(0.0, wm[0].get("confidence", base_conf) - 0.12)
                wm[0]["reason"] = (wm[0].get("reason", "") + " Operational contradiction detected; reconcile runtime signals.").strip()
            msg_action = f"Review/reconcile conflicting operational signals for {target}"
            actions.append(msg_action)
            blocked.append(msg_action)
        elif isinstance(sig, dict) and sig.get("type") == "recurring_bottleneck_detected":
            target = sig.get("target", "bottleneck")
            if wm and isinstance(wm[0], dict):
                wm[0]["reason"] = (wm[0].get("reason", "") + " Recurring bottleneck detected.").strip()
            msg_action = f"Investigate/mitigate recurring bottleneck for {target}"
            actions.append(msg_action)
            blocked.append(msg_action)
        elif isinstance(sig, dict) and sig.get("type") == "repeated_override_detected":
            target = sig.get("target", "classification")
            new_conf = max(0.0, base_conf - 0.1)
            updated["confidence"] = new_conf
            if wm and isinstance(wm[0], dict):
                wm[0]["confidence"] = max(0.0, wm[0].get("confidence", base_conf) - 0.1)
                wm[0]["reason"] = (wm[0].get("reason", "") + " Repeated overrides detected; reassess criteria.").strip()
            msg_action = f"Review/rethink decision criteria for {target}"
            actions.append(msg_action)
            blocked.append(msg_action)
        elif isinstance(sig, dict) and sig.get("type") == "unresolved_aging_item_detected":
            target = sig.get("target", "item")
            age_days = sig.get("age_days")
            msg_block = f"Aging item unresolved: {target}"
            if age_days is not None:
                msg_block += f" ({age_days}d)"
            blocked.append(msg_block)
            msg_action = f"Review/resolve aging item {target}"
            actions.append(msg_action)
            new_conf = max(0.0, base_conf - 0.1)
            updated["confidence"] = new_conf
            if wm and isinstance(wm[0], dict):
                wm[0]["confidence"] = max(0.0, wm[0].get("confidence", base_conf) - 0.1)
                wm[0]["reason"] = (wm[0].get("reason", "") + " Aging item requires resolution.").strip()
    
    updated["what_matters_now"] = wm
    return updated


def apply_scientific_guidance(decision: dict, guidance: list):
    """Apply scientific guidance (minimal slice) to decision dict.
    Current supported type: underpowered_test
    """
    import copy
    updated = copy.deepcopy(decision)
    wm = updated.get("what_matters_now", [])
    blocked = updated.setdefault("blocked_items", [])
    actions = updated.setdefault("next_actions", [])
    base_conf = updated.get("confidence", 1.0)
    for sig in guidance or []:
        if isinstance(sig, dict) and sig.get("type") == "underpowered_test":
            target = sig.get("target", "experiment")
            required = sig.get("required_samples")
            planned = sig.get("planned_samples")
            msg_block = f"Underpowered: {target} needs {required} samples (planned {planned})"
            blocked.append(msg_block)
            msg_action = f"Increase sample size for {target} to {required} or redesign test"
            actions.append(msg_action)
            new_conf = min(base_conf, max(0.0, base_conf - 0.2))
            updated["confidence"] = new_conf
            if wm and isinstance(wm[0], dict):
                wm[0]["confidence"] = max(0.0, wm[0].get("confidence", base_conf) - 0.2)
                wm[0]["reason"] = (wm[0].get("reason", "") + " Underpowered test detected.").strip()
        elif isinstance(sig, dict) and sig.get("type") == "model_drift_required":
            target = sig.get("target", "model")
            msg_block = f"Drift check required for {target}"
            blocked.append(msg_block)
            msg_action = f"Run drift detection/monitoring for {target}"
            actions.append(msg_action)
            new_conf = min(base_conf, max(0.0, base_conf - 0.15))
            updated["confidence"] = new_conf
            if wm and isinstance(wm[0], dict):
                wm[0]["confidence"] = max(0.0, wm[0].get("confidence", base_conf) - 0.15)
                wm[0]["reason"] = (wm[0].get("reason", "") + " Drift check required.").strip()
        elif isinstance(sig, dict) and sig.get("type") == "domain_safety_constraint_required":
            target = sig.get("target", "change")
            msg_block = f"Safety constraint required for {target}"
            blocked.append(msg_block)
            msg_action = f"Run safety/compliance check for {target}"
            actions.append(msg_action)
            new_conf = min(base_conf, max(0.0, base_conf - 0.1))
            updated["confidence"] = new_conf
            if wm and isinstance(wm[0], dict):
                wm[0]["confidence"] = max(0.0, wm[0].get("confidence", base_conf) - 0.1)
                wm[0]["reason"] = (wm[0].get("reason", "") + " Safety constraint required.").strip()
        elif isinstance(sig, dict) and sig.get("type") == "causal_hypothesis_required":
            target = sig.get("target", "signal")
            msg_block = f"Causal hypothesis required for {target}"
            blocked.append(msg_block)
            msg_action = f"Run causal validation/ablation for {target}"
            actions.append(msg_action)
            new_conf = min(base_conf, max(0.0, base_conf - 0.1))
            updated["confidence"] = new_conf
            if wm and isinstance(wm[0], dict):
                wm[0]["confidence"] = max(0.0, wm[0].get("confidence", base_conf) - 0.1)
                wm[0]["reason"] = (wm[0].get("reason", "") + " Causal hypothesis required; correlation insufficient.").strip()
        elif isinstance(sig, dict) and sig.get("type") == "contradictory_findings_reconciliation_required":
            target = sig.get("target", "findings")
            msg_block = f"Reconcile contradictory findings for {target}"
            blocked.append(msg_block)
            msg_action = f"Compare/resolve conflicting findings for {target}"
            actions.append(msg_action)
            new_conf = min(base_conf, max(0.0, base_conf - 0.1))
            updated["confidence"] = new_conf
            if wm and isinstance(wm[0], dict):
                wm[0]["confidence"] = max(0.0, wm[0].get("confidence", base_conf) - 0.1)
                wm[0]["reason"] = (wm[0].get("reason", "") + " Reconcile contradictory findings (scientific).").strip()
            else:
                wm.append({"title": target, "confidence": new_conf, "reason": "Reconcile contradictory findings (scientific)."})
        elif isinstance(sig, dict) and sig.get("type") == "evidence_sufficiency_threshold_not_met":
            target = sig.get("target", "decision")
            msg_block = f"Evidence threshold not met for {target}"
            blocked.append(msg_block)
            msg_action = f"Gather additional evidence for {target} to reach sufficiency threshold"
            actions.append(msg_action)
            new_conf = min(base_conf, max(0.0, base_conf - 0.12))
            updated["confidence"] = new_conf
            if wm and isinstance(wm[0], dict):
                wm[0]["confidence"] = max(0.0, wm[0].get("confidence", base_conf) - 0.12)
                wm[0]["reason"] = (wm[0].get("reason", "") + " Evidence threshold not met.").strip()
            else:
                wm.append({"title": target, "confidence": new_conf, "reason": "Evidence threshold not met."})
    updated["what_matters_now"] = wm
    return updated
