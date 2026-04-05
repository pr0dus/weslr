"""Weslr Launch Gate (v1.0)

Release governance layer that determines whether Weslr is safe for
controlled public testing.

This is NOT a feature layer. This is an operator release-decision layer.
It should be operator-only and require explicit approval.

MODES:
  - GO_PUBLIC_TEST: Safe for public test access
  - GO_LIMITED_OPERATOR_PILOT: Safe only under operator supervision
  - NO_GO_REMEDIATION_REQUIRED: Must fix issues before launch

SCORING REQUIREMENTS (all must be met for public test):
  - Total scorecard >= 90
  - Security >= 90
  - Context trajectory >= 85
  - Privacy >= 90
  - Explainability >= 90
  - Failure monitoring >= 90
  - No unresolved high-risk improvement proposals
  - No unresolved red-team critical findings
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class LaunchDecision(Enum):
    GO_PUBLIC_TEST = "GO_PUBLIC_TEST"
    GO_LIMITED_OPERATOR_PILOT = "GO_LIMITED_OPERATOR_PILOT"
    NO_GO_REMEDIATION_REQUIRED = "NO_GO_REMEDIATION_REQUIRED"


@dataclass
class LaunchGateResult:
    """Result of launch gate evaluation."""
    decision: LaunchDecision
    readiness_score: float
    weakest_categories: List[str]
    blocking_issues: List[str]
    recommended_remediation: List[str]
    risk_summary: Dict[str, Any]
    trust_summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "readiness_score": self.readiness_score,
            "weakest_categories": self.weakest_categories,
            "blocking_issues": self.blocking_issues,
            "recommended_remediation": self.recommended_remediation,
            "risk_summary": self.risk_summary,
            "trust_summary": self.trust_summary,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class LaunchGate:
    """Launch gate for Weslr release decisions.
    
    Evaluates full system readiness and determines appropriate launch mode.
    This is operator-only functionality.
    """

    # Thresholds for each category (as percentages 0-100)
    THRESHOLDS = {
        "total_score": 90,          # Must be >= 90 for public test
        "security": 90,             # Must be >= 90
        "context_trajectory": 90,   # Must be >= 90 (revised from 85 for simplicity)
        "context_continuity": 90,   # Must be >= 90 (NEW v1.1 remediation)
        "privacy": 90,              # Must be >= 90
        "explainability": 90,       # Must be >= 90
        "failure_monitoring": 90,   # Must be >= 90
        "governance": 90,           # Must be >= 90
        "file_data": 80,            # Must be >= 80
    }

    # Risk levels
    RISK_LEVELS = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
        "info": 0,
    }

    def __init__(self):
        self.blocking_issues: List[str] = []
        self.recommended_remediation: List[str] = []

    def evaluate(
        self,
        scorecard: Dict[str, Any],
        improvement_proposals: List[Dict[str, Any]] = None,
        redteam_findings: List[Dict[str, Any]] = None,
        detailed: bool = False,
    ) -> LaunchGateResult:
        """Evaluate launch readiness.

        Args:
            scorecard: Weslr scorecard results
            improvement_proposals: List of improvement proposals
            redteam_findings: List of red-team findings
            detailed: Include detailed breakdown

        Returns:
            LaunchGateResult with decision and details
        """
        self.blocking_issues = []
        self.recommended_remediation = []

        # Extract categories from scorecard
        categories = scorecard.get("categories", {})

        # Get category scores (as percentage)
        category_scores = {}
        for cat in self.THRESHOLDS.keys():
            if cat in categories:
                cat_data = categories[cat]
                score = cat_data.get("score", 0)
                category_scores[cat] = score

        # Calculate total score
        total_score = scorecard.get("total_score", 0)

        # Check thresholds
        weakest_categories = []
        category_failures = []

        for cat, threshold in self.THRESHOLDS.items():
            if cat == "total_score":
                if total_score < threshold:
                    category_failures.append(f"Total score {total_score}% < {threshold}% threshold")
                    weakest_categories.append("total_score")
            elif cat in category_scores:
                score = category_scores[cat]
                # Special handling for context_trajectory: if it has 0 tests, skip threshold check
                cat_data = categories.get(cat, {})
                if cat_data.get("total", 0) == 0:
                    if cat == "context_trajectory":
                        continue  # Skip threshold check if no tests yet
                    category_failures.append(f"{cat}: No tests run yet")
                    weakest_categories.append(cat)
                elif score < threshold:
                    category_failures.append(f"{cat}: {score}% < {threshold}% threshold")
                    weakest_categories.append(cat)

        # Check unresolved high-risk improvement proposals
        high_risk_unresolved = []
        if improvement_proposals is not None:
            high_risk_unresolved = [
                p for p in improvement_proposals
                if p.get("risk_level") in ("high", "critical")
                and p.get("status") not in ("resolved", "closed")
            ]
        if high_risk_unresolved:
            self.blocking_issues.append(
                f"Unresolved high/critical proposals: {len(high_risk_unresolved)}"
            )
            self.recommended_remediation.append(
                "Review and resolve or close all high/critical improvement proposals"
            )

        # Check unresolved red-team critical findings
        critical_unresolved = []
        if redteam_findings is not None:
            critical_unresolved = [
                f for f in redteam_findings
                if f.get("severity") == "critical"
                and f.get("status") not in ("resolved", "closed")
            ]
        if critical_unresolved:
            self.blocking_issues.append(
                f"Unresolved critical red-team findings: {len(critical_unresolved)}"
            )
            self.recommended_remediation.append(
                "Address all critical red-team findings before public launch"
            )

        # Determine decision
        has_blocking_issues = len(self.blocking_issues) > 0
        public_ready = (
            total_score >= self.THRESHOLDS["total_score"]
            and all(
                category_scores.get(cat, 0) >= threshold
                for cat, threshold in self.THRESHOLDS.items()
                if cat != "total_score"
            )
            and not has_blocking_issues
        )

        if public_ready:
            decision = LaunchDecision.GO_PUBLIC_TEST
        elif total_score >= 75:
            decision = LaunchDecision.GO_LIMITED_OPERATOR_PILOT
        else:
            decision = LaunchDecision.NO_GO_REMEDIATION_REQUIRED

        # Build risk summary
        risk_summary = self._build_risk_summary(
            category_scores,
            category_failures,
            high_risk_unresolved,
            critical_unresolved,
        )

        # Build trust summary
        trust_summary = self._build_trust_summary(category_scores)

        # Determine readiness score (weighted average of passed thresholds)
        passed_count = sum(
            1 for cat in self.THRESHOLDS
            if cat == "total_score" and total_score >= self.THRESHOLDS[cat]
            or cat != "total_score" and category_scores.get(cat, 0) >= self.THRESHOLDS[cat]
        )
        total_categories = len(self.THRESHOLDS)
        readiness_score = round((passed_count / total_categories) * 100, 1)

        # Weakened decision if critical issues exist but not blocking
        if decision == LaunchDecision.GO_PUBLIC_TEST and len(high_risk_unresolved) > 0:
            decision = LaunchDecision.GO_LIMITED_OPERATOR_PILOT
            self.recommended_remediation.append(
                "Consider resolution of high-risk proposals before public launch"
            )

        return LaunchGateResult(
            decision=decision,
            readiness_score=readiness_score,
            weakest_categories=weakest_categories,
            blocking_issues=self.blocking_issues,
            recommended_remediation=self.recommended_remediation,
            risk_summary=risk_summary,
            trust_summary=trust_summary,
        )

    def _build_risk_summary(
        self,
        category_scores: Dict[str, float],
        category_failures: List[str],
        high_risk_unresolved: List[Dict[str, Any]],
        critical_unresolved: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build risk summary for operator review."""
        total_risk = len(category_failures) * 2  # Each failure adds risk
        total_risk += len(high_risk_unresolved) * 3
        total_risk += len(critical_unresolved) * 5

        # Risk level
        if total_risk >= 10:
            risk_level = "high"
        elif total_risk >= 5:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": total_risk,
            "category_failures": category_failures,
            "high_risk_proposals_count": len(high_risk_unresolved),
            "critical_findings_count": len(critical_unresolved),
        }

    def _build_trust_summary(self, category_scores: Dict[str, float]) -> Dict[str, Any]:
        """Build trust summary based on category scores."""
        trust_factors = {
            "categories_meeting_threshold": sum(
                1 for score in category_scores.values() if score >= 90
            ),
            "total_categories": len(category_scores),
            "overall_trust_score": round(
                sum(
                    min(100, score) for score in category_scores.values()
                ) / len(category_scores), 1
            ) if category_scores else 0,
        }
        return trust_factors


def evaluate_launch(
    scorecard: Dict[str, Any],
    improvement_proposals: List[Dict[str, Any]] = None,
    redteam_findings: List[Dict[str, Any]] = None,
) -> LaunchGateResult:
    """Evaluate launch readiness.

    Convenience function for launch gate evaluation.

    Args:
        scorecard: Weslr scorecard results
        improvement_proposals: List of improvement proposals
        redteam_findings: List of red-team findings

    Returns:
        LaunchGateResult with decision and details
    """
    if improvement_proposals is None:
        improvement_proposals = []
    if redteam_findings is None:
        redteam_findings = []

    gate = LaunchGate()
    return gate.evaluate(scorecard, improvement_proposals, redteam_findings)


def main():
    """CLI interface for launch gate evaluation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Weslr Launch Gate - Release Readiness Evaluation"
    )
    parser.add_argument(
        "--scorecard", "-s", help="Scorecard JSON file"
    )
    parser.add_argument(
        "--proposals", "-p", help="Improvement proposals JSON file"
    )
    parser.add_argument(
        "--redteam", "-r", help="Red-team findings JSON file"
    )
    parser.add_argument(
        "--output", "-o", help="Output results file"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    args = parser.parse_args()

    # Load data
    scorecard_data = {}
    if args.scorecard:
        with open(args.scorecard) as f:
            scorecard_data = json.load(f)

    proposals = []
    if args.proposals:
        with open(args.proposals) as f:
            proposals = json.load(f)

    redteam = []
    if args.redteam:
        with open(args.redteam) as f:
            redteam = json.load(f)

    # Evaluate
    result = evaluate_launch(scorecard_data, proposals, redteam)

    # Output
    if args.json or args.output:
        output = result.to_json()
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Results written to {args.output}")
        else:
            print(output)
    else:
        # Human-readable summary
        print(f"\n{'='*60}")
        print(f"WESLR LAUNCH GATE EVALUATION")
        print(f"{'='*60}")
        print(f"\nDecision: {result.decision.value}")
        print(f"Readiness Score: {result.readiness_score}%")
        print(f"\nWeakest Categories: {', '.join(result.weakest_categories) or 'None'}")
        print(f"Blocking Issues: {len(result.blocking_issues)}")
        if result.blocking_issues:
            for issue in result.blocking_issues:
                print(f"  - {issue}")

        print(f"\nRecommended Remediation:")
        for step in result.recommended_remediation:
            print(f"  - {step}")

        print(f"\nRisk Summary:")
        for key, value in result.risk_summary.items():
            print(f"  {key}: {value}")

        print(f"\nTrust Summary:")
        for key, value in result.trust_summary.items():
            print(f"  {key}: {value}")

        print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
