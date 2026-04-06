# governance_scorecard.py - Self-Architecture v18: Governance Decision Scorecard / Benchmark Layer
# Measures governance decision quality over time.
# Additive only, operator-first, evidence-driven. No architecture redesign.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from governance_invocation import invoke_governance_single, invoke_governance_compare


# ============================================================================
# DECISION RECORD
# ============================================================================

@dataclass
class GovernanceDecisionRecord:
    """Record of a governance decision for later scoring."""
    
    decision_id: str
    decision_type: str  # "execute", "defer", "blockers", "review"
    proposal_id: str
    timestamp: str
    operator: str = "operator"
    reasoning: str = ""
    confidence: float = 0.0
    status_at_decision: str = ""
    actual_outcome: Optional[str] = None  # Later: "success", "failure", "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp,
            "operator": self.operator,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "status_at_decision": self.status_at_decision,
            "actual_outcome": self.actual_outcome,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GovernanceDecisionRecord:
        return cls(**data)


# ============================================================================
# SCORECARD MODEL
# ============================================================================

@dataclass
class GovernanceScorecard:
    """Scorecard that tracks governance decision quality."""
    
    card_id: str
    created_at: str
    decisions: List[GovernanceDecisionRecord] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Recalculate metrics after initialization."""
        self._recalculate_metrics()
    
    def add_decision(self, decision: GovernanceDecisionRecord) -> None:
        """Add a decision to the scorecard."""
        self.decisions.append(decision)
        self._recalculate_metrics()
    
    def _recalculate_metrics(self) -> None:
        """Recalculate metrics from all decisions."""
        if not self.decisions:
            self.metrics = {
                "total_decisions": 0,
                "execute_decisions": 0,
                "defer_decisions": 0,
                "blockers_decisions": 0,
                "review_decisions": 0,
                "success_rate": None,
                "false_ready_rate": None,
                "false_blocked_rate": None,
            }
            return
        
        total = len(self.decisions)
        execute_count = sum(1 for d in self.decisions if d.decision_type == "execute")
        defer_count = sum(1 for d in self.decisions if d.decision_type == "defer")
        blockers_count = sum(1 for d in self.decisions if d.decision_type == "blockers")
        review_count = sum(1 for d in self.decisions if d.decision_type == "review")
        
        # Calculate success rate (decisions with outcomes)
        decisions_with_outcomes = [d for d in self.decisions if d.actual_outcome is not None]
        if decisions_with_outcomes:
            success_count = sum(1 for d in decisions_with_outcomes 
                               if d.actual_outcome == "success" or d.actual_outcome == "ready")
            self.metrics["success_rate"] = success_count / len(decisions_with_outcomes)
        else:
            self.metrics["success_rate"] = None
        
        # Placeholder for false ready / false blocked detection
        self.metrics["false_ready_rate"] = None
        self.metrics["false_blocked_rate"] = None
        
        self.metrics.update({
            "total_decisions": total,
            "execute_decisions": execute_count,
            "defer_decisions": defer_count,
            "blockers_decisions": blockers_count,
            "review_decisions": review_count,
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "created_at": self.created_at,
            "total_decisions": len(self.decisions),
            "decisions": [d.to_dict() for d in self.decisions],
            "metrics": self.metrics,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GovernanceScorecard:
        decisions = [GovernanceDecisionRecord.from_dict(d) for d in data.get("decisions", [])]
        data["decisions"] = decisions
        # Don't pass total_decisions to __init__ - recalculate from decisions list
        data.pop("total_decisions", None)
        return cls(**data)
    
    def format_for_display(self) -> str:
        """Format scorecard for human-readable display."""
        lines = [
            "=" * 70,
            f"GOVERNANCE SCORECARD: {self.card_id}",
            "=" * 70,
            "",
            "SUMMARY:",
            f"  Total Decisions: {len(self.decisions)}",
            "",
            "DECISION BREAKDOWN:",
            f"  Execute: {self.metrics.get('execute_decisions', 0)}",
            f"  Defer: {self.metrics.get('defer_decisions', 0)}",
            f"  Blockers: {self.metrics.get('blockers_decisions', 0)}",
            f"  Review: {self.metrics.get('review_decisions', 0)}",
            "",
            "RELIABILITY METRICS:",
        ]
        
        success_rate = self.metrics.get("success_rate")
        if success_rate is not None:
            lines.append(f"  Success Rate: {success_rate:.1%}")
        else:
            lines.append("  Success Rate: N/A (no outcomes recorded)")
        
        false_ready = self.metrics.get("false_ready_rate")
        if false_ready is not None:
            lines.append(f"  False Ready Rate: {false_ready:.1%}")
        
        false_blocked = self.metrics.get("false_blocked_rate")
        if false_blocked is not None:
            lines.append(f"  False Blocked Rate: {false_blocked:.1%}")
        
        lines.extend([
            "",
            "CALIBRATION DRIFT:",
            "  (drift indicators will be tracked over time)",
            "",
            "=" * 70,
        ])
        return "\n".join(lines)


# ============================================================================
# BENCHMARK ENGINE
# ============================================================================

class GovernanceBenchmarkEngine:
    """Engine that scores governance decisions and identifies weak zones."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("continuity/governance_scorecards.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.scorecards: Dict[str, GovernanceScorecard] = {}
        self._load_scorecards()
    
    def _load_scorecards(self) -> None:
        """Load scorecards from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.scorecards = {
                        k: GovernanceScorecard.from_dict(v)
                        for k, v in data.get("scorecards", {}).items()
                    }
            except (json.JSONDecodeError, IOError):
                self.scorecards = {}
    
    def _save_scorecards(self) -> None:
        """Save scorecards to storage."""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({
                "scorecards": {k: v.to_dict() for k, v in self.scorecards.items()},
                "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }, f, indent=2)
    
    def create_scorecard(self, card_id: str) -> GovernanceScorecard:
        """Create a new scorecard."""
        scorecard = GovernanceScorecard(
            card_id=card_id,
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        self.scorecards[card_id] = scorecard
        self._save_scorecards()
        return scorecard
    
    def get_scorecard(self, card_id: str) -> Optional[GovernanceScorecard]:
        """Get a scorecard by ID."""
        return self.scorecards.get(card_id)
    
    def record_decision(
        self,
        card_id: str,
        decision_type: str,
        proposal_id: str,
        reasoning: str,
        confidence: float = 0.0,
        status_at_decision: str = "",
        operator: str = "operator",
    ) -> GovernanceDecisionRecord:
        """Record a decision and add it to the scorecard."""
        scorecard = self.get_scorecard(card_id)
        if not scorecard:
            scorecard = self.create_scorecard(card_id)
        
        decision_id = f"dec-{len(scorecard.decisions) + 1:04d}"
        decision = GovernanceDecisionRecord(
            decision_id=decision_id,
            decision_type=decision_type,
            proposal_id=proposal_id,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            operator=operator,
            reasoning=reasoning,
            confidence=confidence,
            status_at_decision=status_at_decision,
        )
        scorecard.add_decision(decision)
        self._save_scorecards()
        return decision
    
    def set_outcome(
        self,
        card_id: str,
        decision_id: str,
        outcome: str,
    ) -> bool:
        """Set the outcome of a decision (success/failure/pending)."""
        scorecard = self.get_scorecard(card_id)
        if not scorecard:
            return False
        
        for decision in scorecard.decisions:
            if decision.decision_id == decision_id:
                decision.actual_outcome = outcome
                scorecard._recalculate_metrics()
                self._save_scorecards()
                return True
        return False
    
    def get_reliability_report(self, card_id: str) -> Dict[str, Any]:
        """Get reliability report for a scorecard."""
        scorecard = self.get_scorecard(card_id)
        if not scorecard:
            return {"error": f"Scorecard not found: {card_id}"}
        
        metrics = scorecard.metrics
        decisions = scorecard.decisions
        
        # Analyze weak zones
        weak_zones = []
        
        if metrics.get("execute_decisions", 0) == 0:
            weak_zones.append("No execute decisions recorded")
        
        if metrics.get("success_rate") is None:
            weak_zones.append("No outcomes recorded yet")
        
        if len(decisions) < 5:
            weak_zones.append("Insufficient data for reliable metrics (< 5 decisions)")
        
        # Confidence distribution
        confidence_values = [d.confidence for d in decisions if d.confidence > 0]
        if confidence_values:
            avg_confidence = sum(confidence_values) / len(confidence_values)
            weak_zones.append(f"Average confidence: {avg_confidence:.1%} (target: > 80%)")
        
        return {
            "card_id": card_id,
            "total_decisions": len(decisions),
            "metrics": metrics,
            "weak_zones": weak_zones,
            "recommendations": self._generate_recommendations(metrics, weak_zones),
        }
    
    def _generate_recommendations(
        self,
        metrics: Dict[str, Any],
        weak_zones: List[str],
    ) -> List[str]:
        """Generate recommendations based on metrics."""
        recommendations = []
        
        if metrics.get("success_rate") and metrics["success_rate"] < 0.7:
            recommendations.append("Increase decision confidence threshold")
        
        if not weak_zones:
            recommendations.append("Continue current decision pattern")
        
        return recommendations
    
    def get_all_scorecards(self) -> Dict[str, GovernanceScorecard]:
        """Get all scorecards."""
        return self.scorecards


def create_governance_scorecard(
    card_id: str,
    storage_path: Optional[Path] = None,
) -> GovernanceScorecard:
    """Convenience function to create a scorecard."""
    engine = GovernanceBenchmarkEngine(storage_path=storage_path)
    return engine.create_scorecard(card_id)


def score_governance_decision(
    card_id: str,
    decision_type: str,
    proposal_id: str,
    reasoning: str,
    confidence: float = 0.0,
    status_at_decision: str = "",
    storage_path: Optional[Path] = None,
) -> GovernanceDecisionRecord:
    """Convenience function to record a decision."""
    engine = GovernanceBenchmarkEngine(storage_path=storage_path)
    return engine.record_decision(
        card_id=card_id,
        decision_type=decision_type,
        proposal_id=proposal_id,
        reasoning=reasoning,
        confidence=confidence,
        status_at_decision=status_at_decision,
    )


def get_governance_reliability_report(
    card_id: str,
    storage_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Convenience function to get reliability report."""
    engine = GovernanceBenchmarkEngine(storage_path=storage_path)
    return engine.get_reliability_report(card_id)


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python governance_scorecard.py <command> [args]")
        print("Commands:")
        print("  create <card_id>")
        print("  record <card_id> <decision_type> <proposal_id> <reasoning> [confidence] [status]")
        print("  outcome <card_id> <decision_id> <outcome>")
        print("  report <card_id>")
        print("  list")
        sys.exit(1)
    
    command = sys.argv[1]
    engine = GovernanceBenchmarkEngine()
    
    if command == "create":
        if len(sys.argv) < 3:
            print("Usage: python governance_scorecard.py create <card_id>")
            sys.exit(1)
        card_id = sys.argv[2]
        scorecard = engine.create_scorecard(card_id)
        print(f"Created scorecard: {card_id}")
        print(scorecard.format_for_display())
    
    elif command == "record":
        if len(sys.argv) < 6:
            print("Usage: python governance_scorecard.py record <card_id> <decision_type> <proposal_id> <reasoning> [confidence] [status]")
            sys.exit(1)
        card_id = sys.argv[2]
        decision_type = sys.argv[3]
        proposal_id = sys.argv[4]
        reasoning = sys.argv[5]
        confidence = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
        status = sys.argv[7] if len(sys.argv) > 7 else ""
        
        decision = engine.record_decision(
            card_id=card_id,
            decision_type=decision_type,
            proposal_id=proposal_id,
            reasoning=reasoning,
            confidence=confidence,
            status_at_decision=status,
        )
        print(f"Recorded decision: {decision.decision_id}")
    
    elif command == "outcome":
        if len(sys.argv) < 5:
            print("Usage: python governance_scorecard.py outcome <card_id> <decision_id> <outcome>")
            sys.exit(1)
        card_id = sys.argv[2]
        decision_id = sys.argv[3]
        outcome = sys.argv[4]
        
        if engine.set_outcome(card_id, decision_id, outcome):
            print(f"Set outcome: {outcome}")
        else:
            print(f"Failed to set outcome")
    
    elif command == "report":
        if len(sys.argv) < 3:
            print("Usage: python governance_scorecard.py report <card_id>")
            sys.exit(1)
        card_id = sys.argv[2]
        report = engine.get_reliability_report(card_id)
        print(json.dumps(report, indent=2))
    
    elif command == "list":
        scorecards = engine.get_all_scorecards()
        if not scorecards:
            print("No scorecards found")
        else:
            for card_id, scorecard in scorecards.items():
                print(f"- {card_id}: {len(scorecard.decisions)} decisions")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
