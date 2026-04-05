"""Weslr Scorecard (v1)

Release scoring model for Weslr capabilities.
Designed to be additive and reversible — no production modifications.

Scoring Categories:
  - Security Coverage: 12 points
  - Governance Integrity: 12 points  
  - File/Data Understanding: 12 points
  - Continuity Integrity: 8 points
  - Scientific Workflow Correctness: 8 points
  - Shell/UX Reliability: 6 points
  - Privacy / Role-Boundary: 5 points
  - Non-Deterministic / Metamorphic: 5 points
  - Failure Path / Monitoring: 5 points

Total: 77 points (normalized to 100 for scoring)

Readiness Levels:
  - 90-100 = public test ready
  - 75-89 = limited/operator-supervised pilot
  - 60-74 = private beta only
  - below 60 = not ready
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


__all__ = [
    "WeslrScorecard",
]


class WeslrScorecard:
    """Release scorecard for Weslr.
    
    Evaluates test results against predefined scoring criteria
    and determines release readiness.
    """
    
    # Category weights and maximum scores
    CATEGORY_WEIGHTS = {
        "security": 12,
        "governance": 12,
        "file_data": 12,
        "continuity": 8,
        "scientific": 8,
        "shell_ux": 6,
        "non_deterministic": 5,
        "privacy": 5,
        "failure_monitoring": 5,
    }
    
    # Minimum pass thresholds per category
    CATEGORY_THRESHOLDS = {
        "security": 0.9,      # 90% of security tests must pass
        "governance": 0.9,    # 90% of governance tests must pass
        "file_data": 0.8,     # 80% of file/data tests must pass
        "continuity": 0.9,    # 90% of continuity tests must pass
        "scientific": 0.85,   # 85% of scientific tests must pass
        "shell_ux": 0.9,      # 90% of shell/UX tests must pass
        "non_deterministic": 0.9,  # 90% of non-deterministic tests must pass
        "privacy": 0.9,       # 90% of privacy tests must pass
        "failure_monitoring": 0.9,  # 90% of failure tests must pass
    }
    
    def __init__(self, max_score: int = 100):
        self.max_score = max_score
    
    def calculate_scores(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate weighted scores from test results.
        
        Args:
            results: Test harness results dict with categories
            
        Returns:
            Dict with per-category scores and total
        """
        category_scores: Dict[str, float] = {}
        category_passes: Dict[str, bool] = {}
        category_details: Dict[str, Dict[str, Any]] = {}
        
        # Map test harness categories to scorecard categories
        category_map = {
            "security": "security",
            "governance": "governance",
            "file_data": "file_data",
            "continuity": "continuity",
            "scientific": "scientific",
            "shell_ux": "shell_ux",
            "non_deterministic": "non_deterministic",
            "privacy": "privacy",
            "failure_monitoring": "failure_monitoring",
        }
        
        total_score = 0.0
        total_weight = sum(self.CATEGORY_WEIGHTS.values())
        
        for scorecard_cat, weight in self.CATEGORY_WEIGHTS.items():
            test_cat = category_map.get(scorecard_cat)
            test_data = results.get("categories", {}).get(test_cat, {})
            
            passed = test_data.get("passed", 0)
            failed = test_data.get("failed", 0)
            total = passed + failed
            
            # Calculate category score (0-100 based on pass rate)
            if total > 0:
                pass_rate = passed / total
                # Scale to category max (weight represents max points for category)
                cat_score = pass_rate * weight
            else:
                pass_rate = 0.0
                cat_score = 0.0
            
            # Check if category passes threshold
            threshold = self.CATEGORY_THRESHOLDS.get(scorecard_cat, 0.75)
            passes_threshold = pass_rate >= threshold
            
            category_scores[scorecard_cat] = cat_score
            category_passes[scorecard_cat] = passes_threshold
            category_details[scorecard_cat] = {
                "passed": passed,
                "failed": failed,
                "total": total,
                "pass_rate": pass_rate,
                "category_score": cat_score,
                "max_score": weight,
                "threshold": threshold,
                "passes_threshold": passes_threshold,
            }
            
            total_score += cat_score
        
        # Round to 2 decimal places
        total_score = round(total_score, 2)
        
        return {
            "total_score": total_score,
            "max_score": self.max_score,
            "category_scores": category_scores,
            "category_details": category_details,
            "category_passes": category_passes,
        }
    
    def release_readiness(self, total_score: float, detailed: bool = False) -> Dict[str, Any]:
        """Determine release readiness based on score.
        
        Args:
            total_score: Total score (0-100)
            detailed: Include detailed breakdown
            
        Returns:
            Dict with readiness classification and optional details
        """
        if total_score >= 90:
            readiness = "public test ready"
            status = "ready"
        elif total_score >= 75:
            readiness = "limited/operator-supervised pilot"
            status = "limited"
        elif total_score >= 60:
            readiness = "private beta only"
            status = "beta"
        else:
            readiness = "not ready"
            status = "not_ready"
        
        result = {
            "total_score": total_score,
            "readiness": readiness,
            "status": status,
        }
        
        if detailed:
            result["readiness_level"] = {
                "min": 0,
                "max": 100,
                "thresholds": {
                    "public_test_ready": 90,
                    "limited_pilot": 75,
                    "private_beta": 60,
                },
            }
        
        return result
    
    def evaluate(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Full evaluation: calculate scores and determine readiness.
        
        Args:
            results: Test harness results dict
            
        Returns:
            Complete evaluation result
        """
        scores = self.calculate_scores(results)
        readiness = self.release_readiness(scores["total_score"], detailed=True)
        
        return {
            **readiness,
            "scores": scores["category_scores"],
            "details": scores["category_details"],
            "by_category": scores["category_passes"],
            "raw_scores": scores["category_details"],
        }
    
    def to_scorecard_format(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format results in scorecard-compatible format.
        
        Converts test harness format to scorecard format for evaluation.
        """
        scores = self.calculate_scores(results)
        readiness = self.release_readiness(scores["total_score"])
        
        # Format categories for output
        categories = {}
        for cat, detail in scores["category_details"].items():
            # Convert to 0-100 scaled score for output
            cat_score_pct = int((detail["category_score"] / detail["max_score"]) * 100) if detail["max_score"] > 0 else 0
            categories[cat] = {
                "passed": detail["passed"],
                "failed": detail["failed"],
                "score": cat_score_pct,
                "max": detail["max_score"],
                "threshold": detail["threshold"],
                "passes": detail["passes_threshold"],
            }
        
        return {
            "ok": scores["category_passes"].get("all", all(scores["category_passes"].values())),
            "categories": categories,
            "total_score": scores["total_score"],
            "max_score": self.max_score,
            "release_readiness": readiness["readiness"],
            "readiness_status": readiness["status"],
        }


def create_scorecard(max_score: int = 100) -> WeslrScorecard:
    """Create a configured scorecard instance."""
    return WeslrScorecard(max_score=max_score)


def evaluate_weslr(results: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to evaluate Weslr test results.
    
    Args:
        results: Test harness results dict
        
    Returns:
        Evaluation result
    """
    scorecard = create_scorecard()
    return scorecard.evaluate(results)


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """CLI interface for scorecard."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Weslr Release Scorecard")
    parser.add_argument("--input", "-i", help="Input results file (JSON)")
    parser.add_argument("--output", "-o", help="Output results file")
    parser.add_argument("--detailed", action="store_true", help="Include detailed breakdown")
    
    args = parser.parse_args()
    
    # Load results
    if args.input:
        with open(args.input, 'r') as f:
            results = json.load(f)
    else:
        # Default test results for demonstration
        results = {
            "ok": True,
            "categories": {
                "security": {"passed": 18, "failed": 2, "score": 90},
                "governance": {"passed": 20, "failed": 0, "score": 100},
                "file_data": {"passed": 16, "failed": 4, "score": 80},
                "continuity": {"passed": 12, "failed": 3, "score": 80},
                "scientific": {"passed": 13, "failed": 2, "score": 87},
                "shell_ux": {"passed": 8, "failed": 2, "score": 80},
            },
            "total_score": 84,
            "release_readiness": "limited/operator-supervised pilot",
        }
    
    # Evaluate
    scorecard = create_scorecard()
    evaluation = scorecard.evaluate(results)
    
    # Format output
    if args.detailed:
        output = evaluation
    else:
        output = scorecard.to_scorecard_format(results)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Results written to {args.output}")
    else:
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
