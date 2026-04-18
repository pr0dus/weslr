"""Weslr Improvement Engine (v1)

Governed continuous improvement engine for Weslr.
Designed to be additive and reversible — no production modifications.

IMPORTANT:
This is NOT autonomous self-modification.
This is a GOVERNED improvement engine.

RULES:
- Additive only
- NO automatic code patching
- NO file deletion
- NO self-rewrite
- NO production logic mutation
- Operator approval required for every improvement path
- Recommendations only
- Full audit trail required
- Rollback path required

==================================================
INPUT SOURCES:
==================================================
- test_reflection (normal reflection)
- security_reflection (red-team analysis)
- operator review history
- suggestion_box requests
- failed / weakest categories
- degraded input patterns
- explainability gaps

==================================================
OUTPUT FORMAT:
==================================================
{
    "improvement_id": "imp-xxx",
    "priority": "high|medium|low",
    "safety": "additive_only|operator_review_required",
    "risk_level": "low|medium|high",
    "expected_gain": "Description of improvement impact",
    "affected_subsystem": "Which Weslr component",
    "description": "What improvement is proposed",
    "rationale": "Why this improvement is needed",
    "affected_categories": ["category1", "category2"],
    "rollback_path": "How to revert if needed",
    "audit": {
        "source": "Source of signal (reflection, suggestion, etc.)",
        "signal_id": "ID of original signal",
        "timestamp": "When signal was received",
        "reviewed": False,
        "approved": False,
    }
}

==================================================
CONTINUITY PERSISTENCE:
==================================================
continuity/improvement_engine/
- recommendations.json (proposed improvements)
- approved.json (approved improvements)
- rejected.json (rejected improvements)
- duplicates.json (duplicate detection)
- history.json (full audit trail)
- trends.json (improvement trends over time)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


__all__ = [
    "WeslrImprovementEngine",
    "create_improvement_engine",
]


class WeslrImprovementEngine:
    """Governed improvement engine for Weslr.
    
    Converts test reflection, security reflection, and other signals
    into operator-reviewed improvement proposals.
    
    NO AUTONOMOUS IMPROVEMENTS.
    NO AUTO-PATCHING.
    NO AUTO-DELETION.
    
    EVERY IMPROVEMENT REQUIRES OPERATOR REVIEW AND APPROVAL.
    """
    
    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
        persistence_dir: Optional[Path] = None,
    ):
        """Initialize the improvement engine.
        
        Args:
            workspace_dir: Weslr workspace directory
            persistence_dir: Directory for persistence (continuity/improvement_engine/)
        """
        self.workspace_dir = workspace_dir or Path(__file__).resolve().parent
        self.persistence_dir = persistence_dir or (
            Path("continuity") / "improvement_engine"
        )
        
        # Ensure persistence directory exists
        self.persistence_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage files
        self.recommendations_file = self.persistence_dir / "recommendations.json"
        self.approved_file = self.persistence_dir / "approved.json"
        self.rejected_file = self.persistence_dir / "rejected.json"
        self.duplicates_file = self.persistence_dir / "duplicates.json"
        self.history_file = self.persistence_dir / "history.json"
        self.trends_file = self.persistence_dir / "trends.json"
        
        # Load existing data
        self._recommendations = self._load_json(self.recommendations_file, [])
        self._approved = self._load_json(self.approved_file, [])
        self._rejected = self._load_json(self.rejected_file, [])
        self._duplicates = self._load_json(self.duplicates_file, [])
        self._history = self._load_json(self.history_file, [])
        self._trends = self._load_json(self.trends_file, [])
    
    def _load_json(self, path: Path, default: Any) -> Any:
        """Load JSON file if it exists, return default otherwise."""
        try:
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return default
    
    def _save_json(self, path: Path, data: Any) -> None:
        """Save data to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    # =========================================================================
    # SIGNAL COLLECTION
    # =========================================================================
    
    def collect_improvement_signals(
        self,
        test_reflection: Optional[Dict[str, Any]] = None,
        security_reflection: Optional[Dict[str, Any]] = None,
        operator_reviews: Optional[List[Dict[str, Any]]] = None,
        suggestion_requests: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Collect improvement signals from various sources.
        
        Args:
            test_reflection: From WeslrTestReflection
            security_reflection: From WeslrSecurityReflection
            operator_reviews: Operator review history
            suggestion_requests: Suggestion box requests
            
        Returns:
            List of improvement signals
        """
        signals = []
        timestamp = datetime.utcnow().isoformat()
        
        # From test reflection
        if test_reflection:
            signals.extend(self._from_test_reflection(test_reflection, timestamp))
        
        # From security reflection
        if security_reflection:
            signals.extend(self._from_security_reflection(security_reflection, timestamp))
        
        # From operator reviews
        if operator_reviews:
            signals.extend(self._from_operator_reviews(operator_reviews, timestamp))
        
        # From suggestion requests
        if suggestion_requests:
            signals.extend(self._from_suggestion_requests(suggestion_requests, timestamp))
        
        return signals
    
    def _from_test_reflection(
        self,
        reflection: Dict[str, Any],
        timestamp: str,
    ) -> List[Dict[str, Any]]:
        """Generate signals from test reflection results."""
        signals = []
        
        # Weakest categories
        for weakest in reflection.get("weakest_categories", []):
            category = weakest.get("name", "unknown")
            score = weakest.get("percentage", 0)
            
            signals.append({
                "signal_id": f"test-weak-{uuid.uuid4().hex[:8]}",
                "source": "test_reflection",
                "type": "weak_category",
                "category": category,
                "signal_data": {
                    "score": score,
                    "meaning": weakest.get("meaning", ""),
                },
                "timestamp": timestamp,
                "improvement": self._build_recommendation(
                    category=category,
                    type="strengthen_test_coverage",
                    signal_id=f"test-weak-{uuid.uuid4().hex[:8]}",
                    source="test_reflection",
                    safety="additive_only",
                    expected_gain=f"Increase {category} category pass rate to 90%+",
                ),
            })
        
        return signals
    
    def _from_security_reflection(
        self,
        reflection: Dict[str, Any],
        timestamp: str,
    ) -> List[Dict[str, Any]]:
        """Generate signals from security reflection results."""
        signals = []
        
        summary = reflection.get("summary", {})
        is_hardened = summary.get("is_hardened", False)
        
        if not is_hardened:
            # Security needs hardening
            signals.append({
                "signal_id": f"sec-hard-{uuid.uuid4().hex[:8]}",
                "source": "security_reflection",
                "type": "security_hardening_needed",
                "signal_data": {
                    "pass_rate": summary.get("pass_rate", 0),
                    "status": summary.get("status", "unknown"),
                },
                "timestamp": timestamp,
                "improvement": self._build_recommendation(
                    category="security",
                    type="security_hardening",
                    signal_id=f"sec-hard-{uuid.uuid4().hex[:8]}",
                    source="security_reflection",
                    safety="operator_review_required",
                    expected_gain="Reduce attack surface, prevent exploitation",
                    risk_level="high",
                ),
            })
        
        # Check attack coverage
        for attack_family, info in reflection.get("attack_summary", {}).items():
            if info.get("status") == "covered":
                signals.append({
                    "signal_id": f"sec-cover-{uuid.uuid4().hex[:8]}",
                    "source": "security_reflection",
                    "type": "attack_family_covered",
                    "signal_data": {
                        "attack_family": attack_family,
                        "name": info.get("name", "unknown"),
                    },
                    "timestamp": timestamp,
                    "improvement": self._build_recommendation(
                        category="security",
                        type="document_attack_family",
                        signal_id=f"sec-cover-{uuid.uuid4().hex[:8]}",
                        source="security_reflection",
                        safety="additive_only",
                        expected_gain="Document security posture, improve visibility",
                    ),
                })
        
        return signals
    
    def _from_operator_reviews(
        self,
        reviews: List[Dict[str, Any]],
        timestamp: str,
    ) -> List[Dict[str, Any]]:
        """Generate signals from operator review history."""
        signals = []
        
        # Look for patterns in reviews
        categories_with_issues = set()
        for review in reviews:
            status = review.get("status", "unknown")
            category = review.get("category", "unknown")
            
            if status == "needs_improvement":
                categories_with_issues.add(category)
        
        for category in categories_with_issues:
            signals.append({
                "signal_id": f"review-{uuid.uuid4().hex[:8]}",
                "source": "operator_reviews",
                "type": "operator_needs_improvement",
                "category": category,
                "signal_data": {
                    "operator_concern": "Operator flagged need for improvement",
                },
                "timestamp": timestamp,
                "improvement": self._build_recommendation(
                    category=category,
                    type="address_operator_concern",
                    signal_id=f"review-{uuid.uuid4().hex[:8]}",
                    source="operator_reviews",
                    safety="additive_only",
                    expected_gain="Address operator feedback, improve quality",
                ),
            })
        
        return signals
    
    def _from_suggestion_requests(
        self,
        suggestions: List[Dict[str, Any]],
        timestamp: str,
    ) -> List[Dict[str, Any]]:
        """Generate signals from suggestion box requests."""
        signals = []
        
        for suggestion in suggestions:
            category = suggestion.get("category", "unknown")
            request_type = suggestion.get("request_type", "unknown")
            
            signals.append({
                "signal_id": f"sugg-{uuid.uuid4().hex[:8]}",
                "source": "suggestion_requests",
                "type": "suggestion_request",
                "category": category,
                "signal_data": {
                    "request_type": request_type,
                    "requester": suggestion.get("requester_type", "unknown"),
                },
                "timestamp": timestamp,
                "improvement": self._build_recommendation(
                    category=category,
                    type="process_suggestion",
                    signal_id=f"sugg-{uuid.uuid4().hex[:8]}",
                    source="suggestion_requests",
                    safety="additive_only",
                    expected_gain="Address suggestion request, improve functionality",
                ),
            })
        
        return signals
    
    # =========================================================================
    # IMPROVEMENT PROCESSING
    # =========================================================================
    
    def merge_duplicate_signals(
        self,
        signals: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge duplicate signals based on content similarity.
        
        Args:
            signals: List of improvement signals
            
        Returns:
            Deduplicated list of signals
        """
        seen = set()
        deduped = []
        
        for signal in signals:
            # Create signature based on key attributes
            signature = (
                signal.get("source", ""),
                signal.get("type", ""),
                signal.get("category", ""),
            )
            
            if signature not in seen:
                seen.add(signature)
                deduped.append(signal)
            else:
                # Record duplicate
                self._duplicates.append({
                    "original_id": signal.get("signal_id"),
                    "duplicate_id": self._duplicates[-1].get("signal_id") if self._duplicates else None,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                self._save_json(self.duplicates_file, self._duplicates)
        
        return deduped
    
    def rank_improvements(
        self,
        signals: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Rank improvements by priority and impact.
        
        Args:
            signals: List of improvement signals
            
        Returns:
            Ranked list of improvements with scores
        """
        ranked = []
        
        for signal in signals:
            improvement = signal.get("improvement", {})
            
            # Calculate score based on factors
            score = 0
            
            # Priority from signal
            priority = improvement.get("priority", "medium")
            if priority == "high":
                score += 30
            elif priority == "medium":
                score += 20
            else:
                score += 10
            
            # Risk level
            risk = improvement.get("risk_level", "low")
            if risk == "high":
                score -= 10
            elif risk == "medium":
                score -= 5
            
            # Source weight
            source = signal.get("source", "")
            if source == "security_reflection":
                score += 20  # Security is critical
            
            # Category weight
            category = improvement.get("category", "")
            if category == "security":
                score += 15
            elif category == "governance":
                score += 10
            
            ranked.append({
                **signal,
                "improvement": improvement,
                "score": score,
                "rank": len(ranked) + 1,
            })
        
        # Sort by score (descending)
        ranked.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Assign ranks
        for i, item in enumerate(ranked):
            item["rank"] = i + 1
        
        return ranked
    
    def build_operator_proposals(
        self,
        ranked_improvements: List[Dict[str, Any]],
        max_proposals: int = 10,
    ) -> List[Dict[str, Any]]:
        """Build operator review proposals from ranked improvements.
        
        Args:
            ranked_improvements: Ranked list of improvements
            max_proposals: Maximum number of proposals
            
        Returns:
            Operator review proposals
        """
        proposals = []
        
        for item in ranked_improvements[:max_proposals]:
            improvement = item.get("improvement", {})
            
            proposal = {
                "proposal_id": f"prop-{uuid.uuid4().hex[:8]}",
                "improvement_id": improvement.get("improvement_id"),
                "title": f"Improve {improvement.get('category', 'unknown')}: {improvement.get('type', 'unknown')}",
                "description": improvement.get("description", ""),
                "rationale": improvement.get("rationale", ""),
                "expected_gain": improvement.get("expected_gain", ""),
                "affected_subsystem": improvement.get("affected_subsystem", "unknown"),
                "safety": improvement.get("safety", "operator_review_required"),
                "risk_level": improvement.get("risk_level", "medium"),
                "priority": improvement.get("priority", "medium"),
                "affected_categories": improvement.get("affected_categories", []),
                "rollback_path": improvement.get("rollback_path", ""),
                "audit": {
                    "source": item.get("source", "unknown"),
                    "signal_id": item.get("signal_id", ""),
                    "created_at": item.get("timestamp", ""),
                    "reviewed": False,
                    "approved": False,
                    "reviewed_at": None,
                    "approved_at": None,
                    "reviewer": None,
                    "rejection_reason": None,
                },
            }
            
            proposals.append(proposal)
            
            # Track in history
            self._history.append({
                "proposal_id": proposal["proposal_id"],
                "type": "proposal_created",
                "timestamp": datetime.utcnow().isoformat(),
                "source": item.get("source"),
                "signal_id": item.get("signal_id"),
            })
        
        self._save_json(self.history_file, self._history)
        self._save_json(self.recommendations_file, proposals)
        
        return proposals
    
    # =========================================================================
    # IMPROVEMENT TRACKING
    # =========================================================================
    
    def track_improvement_history(
        self,
        proposal: Dict[str, Any],
        action: str,
        reviewed_by: Optional[str] = None,
        rejection_reason: Optional[str] = None,
    ) -> None:
        """Track improvement proposal actions.
        
        Args:
            proposal: Proposal to track
            action: "approved" or "rejected"
            reviewed_by: Operator who reviewed
            rejection_reason: Reason for rejection (if applicable)
        """
        timestamp = datetime.utcnow().isoformat()
        
        if action == "approved":
            self._approved.append({
                "proposal_id": proposal.get("proposal_id"),
                "improvement_id": proposal.get("improvement_id"),
                "approved_at": timestamp,
                "reviewed_by": reviewed_by,
                "details": proposal,
            })
            
            self._save_json(self.approved_file, self._approved)
            
        elif action == "rejected":
            self._rejected.append({
                "proposal_id": proposal.get("proposal_id"),
                "improvement_id": proposal.get("improvement_id"),
                "rejected_at": timestamp,
                "reviewed_by": reviewed_by,
                "rejection_reason": rejection_reason,
                "details": proposal,
            })
            
            self._save_json(self.rejected_file, self._rejected)
        
        # Log to history
        self._history.append({
            "proposal_id": proposal.get("proposal_id"),
            "type": f"proposal_{action}",
            "timestamp": timestamp,
            "reviewed_by": reviewed_by,
            "rejection_reason": rejection_reason,
        })
        
        self._save_json(self.history_file, self._history)
        
        # Update trends
        self._update_trends()
    
    def _update_trends(self) -> None:
        """Update improvement trends."""
        trends = {
            "total_proposals": len(self._history),
            "approved_count": len(self._approved),
            "rejected_count": len(self._rejected),
            "pending_count": len(self._recommendations) - len(self._approved) - len(self._rejected),
            "last_24h": 0,  # Would need timestamp filtering
        }
        
        self._trends.append({
            "timestamp": datetime.utcnow().isoformat(),
            **trends,
        })
        
        # Keep only last 100 trend entries
        if len(self._trends) > 100:
            self._trends = self._trends[-100:]
        
        self._save_json(self.trends_file, self._trends)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _build_recommendation(
        self,
        category: str,
        type: str,
        signal_id: str,
        source: str,
        safety: str,
        expected_gain: str,
        risk_level: str = "medium",
    ) -> Dict[str, Any]:
        """Build a recommendation dict."""
        return {
            "improvement_id": f"imp-{signal_id.split('-')[-1]}",
            "category": category,
            "type": type,
            "description": self._get_description(category, type),
            "rationale": self._get_rationale(category, type),
            "expected_gain": expected_gain,
            "affected_subsystem": self._get_affected_subsystem(category),
            "affected_categories": [category],
            "safety": safety,
            "risk_level": risk_level,
            "priority": self._get_priority(category, risk_level),
            "rollback_path": self._get_rollback_path(category, type),
        }
    
    def _get_description(self, category: str, type: str) -> str:
        """Get description for recommendation."""
        descriptions = {
            "security": {
                "security_hardening": "Add red-team test coverage to strengthen security posture",
                "document_attack_family": "Document attack family coverage in security report",
            },
            "default": {
                "default": f"Improve {category} category test coverage",
                "address_operator_concern": "Address operator feedback for {category}",
                "process_suggestion": "Process suggestion request for {category}",
            }
        }
        
        cat_desc = descriptions.get(category, descriptions.get("default", {}))
        return cat_desc.get(type, cat_desc.get("default", f"Improve {category}")).format(category=category)
    
    def _get_rationale(self, category: str, type: str) -> str:
        """Get rationale for recommendation."""
        rationales = {
            "security": {
                "security_hardening": "Security is critical - gaps must be addressed first",
                "document_attack_family": "Visibility into security posture enables better decisions",
            },
            "default": {
                "default": f"Category {category} score below 90% threshold",
                "address_operator_concern": "Operator identified this as needing improvement",
                "process_suggestion": "Requester identified this as valuable",
            }
        }
        
        cat_rat = rationales.get(category, rationales.get("default", {}))
        return cat_rat.get(type, cat_rat.get("default", f"Improve {category}")).format(category=category)
    
    def _get_affected_subsystem(self, category: str) -> str:
        """Get affected subsystem for category."""
        subsystems = {
            "security": "Security layer",
            "governance": "Governance workflow",
            "file_data": "File handling",
            "continuity": "Continuity state",
            "scientific": "Scientific analysis",
            "shell_ux": "Shell/UX interface",
            "non_deterministic": "Stability layer",
            "privacy": "Privacy layer",
            "failure_monitoring": "Monitoring layer",
            "data_quality": "Data quality layer",
            "explainability": "Explainability layer",
        }
        return subsystems.get(category, "Unknown subsystem")
    
    def _get_priority(self, category: str, risk_level: str) -> str:
        """Get priority based on category and risk."""
        priorities = {
            "security": "high",
            "governance": "high",
            "continuity": "medium",
        }
        
        if category in priorities:
            return priorities[category]
        
        if risk_level == "high":
            return "high"
        elif risk_level == "medium":
            return "medium"
        else:
            return "low"
    
    def _get_rollback_path(self, category: str, type: str) -> str:
        """Get rollback path for improvement."""
        return (
            f"Remove {type} test from weslr/tests/test_{category}.py "
            f"and revert test_harness.py category inference"
        )


def create_improvement_engine(
    workspace_dir: Optional[Path] = None,
    persistence_dir: Optional[Path] = None,
) -> WeslrImprovementEngine:
    """Create a configured improvement engine instance."""
    return WeslrImprovementEngine(workspace_dir, persistence_dir)


def run_improvement_engine(
    test_reflection: Optional[Dict[str, Any]] = None,
    security_reflection: Optional[Dict[str, Any]] = None,
    operator_reviews: Optional[List[Dict[str, Any]]] = None,
    suggestion_requests: Optional[List[Dict[str, Any]]] = None,
    workspace_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Convenience function to run improvement engine.
    
    Args:
        test_reflection: From WeslrTestReflection
        security_reflection: From WeslrSecurityReflection
        operator_reviews: Operator review history
        suggestion_requests: Suggestion box requests
        workspace_dir: Weslr workspace directory
        
    Returns:
        Operator proposals
    """
    engine = create_improvement_engine(workspace_dir)
    
    # Collect signals
    signals = engine.collect_improvement_signals(
        test_reflection=test_reflection,
        security_reflection=security_reflection,
        operator_reviews=operator_reviews,
        suggestion_requests=suggestion_requests,
    )
    
    # Deduplicate
    deduped = engine.merge_duplicate_signals(signals)
    
    # Rank
    ranked = engine.rank_improvements(deduped)
    
    # Build proposals
    proposals = engine.build_operator_proposals(ranked)
    
    return {
        "proposals": proposals,
        "total_signals": len(signals),
        "after_dedup": len(deduped),
        "ranked_count": len(ranked),
        "proposals_count": len(proposals),
    }
