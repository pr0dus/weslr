"""Weslr Test Interpretation Layer (v1)

Self-aware test interpretation that allows Weslr to understand its own scores.

Each score category includes:
  1. What the category measures
  2. What score 0 means
  3. What maximum means
  4. What the current score means in practical terms
  5. The most important safe improvement actions
  6. Whether those actions are additive_only or require deeper operator review

Output Shape:
{
  "category": "governance",
  "score": 14,
  "max_score": 20,
  "meaning": {
    "zero": "No reliable operator control or review integrity",
    "maximum": "Strong operator control, explicit approval gates, and verified rollback"
  },
  "assessment": "moderate",
  "improvement_guidance": [
    {
      "action": "increase rollback verification coverage",
      "priority": "high",
      "safety": "additive_only"
    }
  ]
}
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


__all__ = [
    "WeslrTestInterpreter",
    "interpret_category",
    "get_category_meanings",
]


# Category meanings and interpretations
CATEGORY_MEANINGS = {
    "security": {
        "measures": "Security coverage including secret scrubbing, input validation, rate limiting, and path traversal protection",
        "zero": "No security controls are in place - any user input is accepted without validation",
        "maximum": "Complete security coverage with secrets scrubbing, input validation, rate limiting, and path traversal protection all verified",
        "improvement_actions": [
            {
                "action": "verify all API endpoints have input length validation",
                "priority": "high",
                "safety": "additive_only"
            },
            {
                "action": "add rate limiting verification for public endpoints",
                "priority": "high",
                "safety": "additive_only"
            },
            {
                "action": "verify secrets scrubbing in error responses",
                "priority": "medium",
                "safety": "additive_only"
            }
        ]
    },
    "governance": {
        "measures": "Governance integrity including operator review flow, review state transitions, no auto-approval, and no auto-implementation",
        "zero": "No operator control - suggestions auto-approve or auto-implement without review",
        "maximum": "Strong operator control with explicit approval gates, verified rollback, and no auto-behavior",
        "improvement_actions": [
            {
                "action": "verify all review state transitions are persisted correctly",
                "priority": "high",
                "safety": "additive_only"
            },
            {
                "action": "add test coverage for rollback behavior verification",
                "priority": "high",
                "safety": "additive_only"
            },
            {
                "action": "verify operator-only visibility gates are enforced",
                "priority": "medium",
                "safety": "additive_only"
            }
        ]
    },
    "file_data": {
        "measures": "File and data understanding including routing, format handling, and error fallback",
        "zero": "Files are not routed correctly or fail on any input type",
        "maximum": "All file types route correctly with proper format handling and graceful error fallback",
        "improvement_actions": [
            {
                "action": "verify PDF routing to correct handler",
                "priority": "high",
                "safety": "additive_only"
            },
            {
                "action": "add test coverage for malformed input fallback",
                "priority": "medium",
                "safety": "additive_only"
            },
            {
                "action": "verify structured data parsing for JSON/YAML",
                "priority": "medium",
                "safety": "additive_only"
            }
        ]
    },
    "continuity": {
        "measures": "Continuity integrity including persistence, state rollback, and data consistency",
        "zero": "No data persistence - all requests lost on reload",
        "maximum": "Complete continuity with proper persistence, rollback behavior verified, and state consistency maintained",
        "improvement_actions": [
            {
                "action": "verify request persistence across reloads",
                "priority": "high",
                "safety": "additive_only"
            },
            {
                "action": "add test coverage for continuity snapshot creation",
                "priority": "medium",
                "safety": "additive_only"
            },
            {
                "action": "verify timeline persistence across sessions",
                "priority": "medium",
                "safety": "additive_only"
            }
        ]
    },
    "scientific": {
        "measures": "Scientific workflow correctness including candidate detection, habitable zone estimation, FITS ingestion, notebook parsing, evidence timelines, and materials analysis",
        "zero": "Scientific modules cannot parse any input or produce correct outputs",
        "maximum": "All scientific modules work correctly with proper output shapes and trend detection",
        "improvement_actions": [
            {
                "action": "verify candidate detection output shape from scientific analysis",
                "priority": "high",
                "safety": "additive_only"
            },
            {
                "action": "verify habitable zone boundary logic (inner/outer factors)",
                "priority": "high",
                "safety": "additive_only"
            },
            {
                "action": "verify FITS metadata extraction returns expected structure",
                "priority": "high",
                "safety": "additive_only"
            },
            {
                "action": "verify scientific notebook markdown parsing extracts all metadata",
                "priority": "medium",
                "safety": "additive_only"
            },
            {
                "action": "verify evidence timeline trend detection works correctly",
                "priority": "medium",
                "safety": "additive_only"
            },
            {
                "action": "verify materials ranking output includes all expected fields",
                "priority": "medium",
                "safety": "additive_only"
            },
            {
                "action": "verify materials timeline trend detection works correctly",
                "priority": "low",
                "safety": "additive_only"
            }
        ]
    },
    "shell_ux": {
        "measures": "Shell and UX reliability including backend contract, file routing integration, and operator summary endpoints",
        "zero": "Backend contract endpoints return errors or incorrect structure",
        "maximum": "All backend contract endpoints return correct structure and integrate properly",
        "improvement_actions": [
            {
                "action": "verify route_file returns correct category and content fields",
                "priority": "high",
                "safety": "additive_only"
            },
            {
                "action": "verify operator_visibility returns correct visible and can_review fields",
                "priority": "high",
                "safety": "additive_only"
            },
            {
                "action": "verify operator_summary returns active_proposals and pending_reviews",
                "priority": "medium",
                "safety": "additive_only"
            }
        ]
    },
}


def get_category_meanings() -> Dict[str, Any]:
    """Return all category meanings for display."""
    return CATEGORY_MEANINGS


def interpret_category(
    category: str,
    score: int,
    max_score: int,
) -> Dict[str, Any]:
    """Interpret a category score and provide actionable guidance.
    
    Args:
        category: Category name (security, governance, file_data, continuity, scientific, shell_ux)
        score: Current score (0-100)
        max_score: Maximum possible score (usually 100)
        
    Returns:
        Interpretation dict with meaning, assessment, and improvement guidance
    """
    if category not in CATEGORY_MEANINGS:
        return {
            "category": category,
            "score": score,
            "max_score": max_score,
            "error": f"Unknown category: {category}",
        }
    
    cat_info = CATEGORY_MEANINGS[category]
    pct = (score / max_score * 100) if max_score > 0 else 0
    
    # Determine assessment level
    if pct >= 90:
        assessment = "excellent"
    elif pct >= 75:
        assessment = "good"
    elif pct >= 60:
        assessment = "moderate"
    elif pct >= 40:
        assessment = "fair"
    else:
        assessment = "poor"
    
    # Build interpretation
    interpretation = {
        "category": category,
        "score": score,
        "max_score": max_score,
        "percentage": round(pct, 1),
        "assessment": assessment,
        "meaning": {
            "what_measures": cat_info["measures"],
            "zero": cat_info["zero"],
            "maximum": cat_info["maximum"],
            "current": f"{pct:.1f}% - {assessment}",
        },
        "improvement_guidance": cat_info["improvement_actions"],
    }
    
    return interpretation


class WeslrTestInterpreter:
    """Self-aware test interpreter for Weslr.
    
    Allows Weslr to understand what its scores mean and what to improve.
    """
    
    def __init__(self):
        self.category_meanings = CATEGORY_MEANINGS
    
    def interpret_scores(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret full test results.
        
        Args:
            results: Test harness results dict
            
        Returns:
            Full interpretation with all categories
        """
        categories = results.get("categories", {})
        
        interpretations = {}
        for category in self.category_meanings.keys():
            cat_data = categories.get(category, {"passed": 0, "failed": 0, "score": 0})
            score = cat_data.get("score", 0)
            
            # Get max score from category
            max_score = 100  # Default, categories scale to 100
            
            interpretations[category] = interpret_category(
                category=category,
                score=score,
                max_score=max_score,
            )
        
        # Calculate overall assessment
        total_score = sum(
            interpretations[cat]["score"]
            for cat in self.category_meanings.keys()
        )
        max_total = len(self.category_meanings) * 100
        overall_pct = (total_score / max_total * 100) if max_total > 0 else 0
        
        if overall_pct >= 90:
            overall_assessment = "excellent"
        elif overall_pct >= 75:
            overall_assessment = "good"
        elif overall_pct >= 60:
            overall_assessment = "moderate"
        elif overall_pct >= 40:
            overall_assessment = "fair"
        else:
            overall_assessment = "poor"
        
        return {
            "total_score": total_score,
            "max_score": max_total,
            "overall_percentage": round(overall_pct, 1),
            "overall_assessment": overall_assessment,
            "by_category": interpretations,
        }
    
    def get_improvement_actions(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all improvement actions from results.
        
        Args:
            results: Test harness results dict
            
        Returns:
            List of all improvement actions with priority and safety
        """
        interpretations = self.interpret_scores(results)
        actions = []
        
        for cat, interp in interpretations["by_category"].items():
            for action in interp.get("improvement_guidance", []):
                action_with_cat = {
                    **action,
                    "category": cat,
                }
                actions.append(action_with_cat)
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))
        
        return actions
    
    def format_report(self, results: Dict[str, Any]) -> str:
        """Format interpretation results as human-readable report.
        
        Args:
            results: Test harness results dict
            
        Returns:
            Formatted report string
        """
        interpretations = self.interpret_scores(results)
        lines = []
        
        lines.append("=" * 70)
        lines.append("WESLR TEST INTERPRETATION REPORT")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Overall Score: {interpretations['total_score']}/{interpretations['max_score']} ({interpretations['overall_percentage']}%)")
        lines.append(f"Assessment: {interpretations['overall_assessment'].upper()}")
        lines.append("")
        
        for cat, interp in interpretations["by_category"].items():
            status = "✓" if interp["percentage"] >= 90 else ("→" if interp["percentage"] >= 75 else "✗")
            lines.append(f"[{status}] {cat.upper()}")
            lines.append(f"    Score: {interp['score']}/100 ({interp['percentage']}%)")
            lines.append(f"    Assessment: {interp['assessment']}")
            lines.append(f"    Measures: {interp['meaning']['what_measures']}")
            lines.append("")
            
            if interp["improvement_guidance"]:
                lines.append("    Improvement Actions:")
                for action in interp["improvement_guidance"]:
                    lines.append(f"      - [{action.get('priority', 'low').upper()}] {action['action']} ({action.get('safety', 'unknown')})")
                lines.append("")
        
        lines.append("=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)
        
        return "\n".join(lines)


def create_interpreter() -> WeslrTestInterpreter:
    """Create a configured interpreter instance."""
    return WeslrTestInterpreter()


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """CLI interface for test interpretation."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Weslr Test Interpretation")
    parser.add_argument("--input", "-i", help="Input results file (JSON)")
    parser.add_argument("--output", "-o", help="Output report file")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
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
                "security": {"passed": 5, "failed": 0, "score": 100},
                "governance": {"passed": 3, "failed": 0, "score": 100},
                "file_data": {"passed": 3, "failed": 0, "score": 100},
                "continuity": {"passed": 4, "failed": 0, "score": 100},
                "scientific": {"passed": 0, "failed": 0, "score": 0},
                "shell_ux": {"passed": 3, "failed": 0, "score": 100},
            },
            "total_score": 300,
            "max_score": 600,
            "release_readiness": "limited/operator-supervised pilot",
        }
    
    # Interpret
    interpreter = create_interpreter()
    
    if args.json:
        output = interpreter.interpret_scores(results)
        print(json.dumps(output, indent=2))
    else:
        report = interpreter.format_report(results)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report written to {args.output}")
        else:
            print(report)
    
    # Also print improvement actions
    actions = interpreter.get_improvement_actions(results)
    if actions:
        print("\n" + "=" * 70)
        print("IMPROVEMENT ACTIONS (Priority Order)")
        print("=" * 70)
        for action in actions:
            print(f"  [{action['priority'].upper()}] {action['category']}: {action['action']} ({action.get('safety', 'unknown')})")


if __name__ == "__main__":
    main()
