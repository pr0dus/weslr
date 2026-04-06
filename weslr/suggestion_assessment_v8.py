# suggestion_assessment_v8.py - Weslr Capability Slice: Internal Assessment Layer with Memory
# Provides internal Weslr assessment of suggestion requests with architecture memory context.
# Memory integration shows prior accepted/denied items, consistency status, and recommendations.

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Self-Architecture Core v7 imports
from architecture_memory import (
    ArchitectureMemory,
    ConsistencyEngine,
    DecisionStatus,
    create_decision,
)

# Self-Architecture Core v8 imports - extend v7
from suggestion_assessment import (
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    FIT_SCORE_MIN,
    FIT_SCORE_MAX,
    WeslrAssessment,
)


class MemoryAwareAssessment(WeslrAssessment):
    """Internal assessment with architecture memory context integration."""

    def __init__(self):
        super().__init__()
        self.memory: Optional[ArchitectureMemory] = None

    def set_memory(self, memory: ArchitectureMemory) -> None:
        """Set the architecture memory instance for consistency checking."""
        self.memory = memory

    def assess_with_memory(
        self,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess a request with architecture memory context.

        Integrates architecture memory to check consistency with prior decisions.

        Args:
            request: Suggestion request dict

        Returns:
            Assessment dict with memory-aware context
        """
        base_assessment = self.assess_request(request)

        # Initialize memory context
        memory_context = {
            "prior_accepted": [],
            "prior_denied": [],
            "consistency_type": "unknown",
            "drift_status": "none",
            "reopen_recommendation": False,
            "delay_recommendation": False,
            "archive_recommendation": False,
        }

        if self.memory is not None:
            # Create a temporary decision to compare against memory
            decision = create_decision(
                title=request.get("requested_capability", "Untitled"),
                description=request.get("problem_statement", ""),
                affected_subsystems=[request.get("domain", "unknown")],
            )

            # Evaluate consistency
            report = ConsistencyEngine.evaluate_consistency(decision, self.memory)

            memory_context["consistency_type"] = report.consistency_type
            memory_context["matching_decisions"] = report.matching_decisions
            memory_context["strength_ratio"] = report.strength_ratio
            memory_context["drift_direction"] = report.drift_direction
            memory_context["drift_magnitude"] = report.drift_magnitude
            memory_context["reopen_recommendation"] = report.should_reopen
            memory_context["archive_recommendation"] = report.should_archive
            memory_context["delay_recommendation"] = (
                not report.should_accept
                and not report.should_reopen
                and not report.should_archive
            )

            # Get prior decisions for display
            memory_context["prior_accepted"] = [
                {"id": d.id, "title": d.title, "status": d.status}
                for d in self.memory.get_accepted_decisions()[:3]
            ]
            memory_context["prior_denied"] = [
                {"id": d.id, "title": d.title, "status": d.status}
                for d in self.memory.get_denied_decisions()[:3]
            ]

        base_assessment["weslr_assessment"]["memory_context"] = memory_context
        return base_assessment

    def assess_candidate_with_memory(
        self,
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess a proposal candidate with architecture memory context."""
        base_assessment = self.assess_candidate(candidate)

        # Extract data from candidate
        source = candidate.get("source", {})
        original_data = source.get("original_data", {})
        request = {
            "domain": original_data.get("domain", "unknown"),
            "requested_capability": original_data.get("requested_capability", ""),
            "problem_statement": original_data.get("problem_statement", ""),
        }

        memory_context = {
            "prior_accepted": [],
            "prior_denied": [],
            "consistency_type": "unknown",
            "drift_status": "none",
            "reopen_recommendation": False,
            "delay_recommendation": False,
            "archive_recommendation": False,
        }

        if self.memory is not None:
            decision = create_decision(
                title=original_data.get("requested_capability", "Untitled"),
                description=original_data.get("problem_statement", ""),
                affected_subsystems=[original_data.get("domain", "unknown")],
            )

            report = ConsistencyEngine.evaluate_consistency(decision, self.memory)

            memory_context["consistency_type"] = report.consistency_type
            memory_context["matching_decisions"] = report.matching_decisions
            memory_context["strength_ratio"] = report.strength_ratio
            memory_context["drift_direction"] = report.drift_direction
            memory_context["drift_magnitude"] = report.drift_magnitude
            memory_context["reopen_recommendation"] = report.should_reopen
            memory_context["archive_recommendation"] = report.should_archive
            memory_context["delay_recommendation"] = (
                not report.should_accept
                and not report.should_reopen
                and not report.should_archive
            )

            memory_context["prior_accepted"] = [
                {"id": d.id, "title": d.title, "status": d.status}
                for d in self.memory.get_accepted_decisions()[:3]
            ]
            memory_context["prior_denied"] = [
                {"id": d.id, "title": d.title, "status": d.status}
                for d in self.memory.get_denied_decisions()[:3]
            ]

        base_assessment["weslr_assessment"]["memory_context"] = memory_context
        return base_assessment


def get_memory_aware_recommendations(
    candidates: List[Dict[str, Any]],
    memory: Optional[ArchitectureMemory] = None,
) -> List[Dict[str, Any]]:
    """Get memory-aware assessment recommendations for candidates."""
    assessment = MemoryAwareAssessment()
    if memory is not None:
        assessment.set_memory(memory)

    recommendations = []

    for cand in candidates:
        result = assessment.assess_candidate_with_memory(cand)
        rec = {
            "candidate_id": cand.get("id"),
            "assessment": result["weslr_assessment"],
            "recommended_action": result["weslr_assessment"].get("recommended_action"),
        }

        # Add memory context info for operator review
        memory_context = result["weslr_assessment"].get("memory_context", {})
        if memory_context.get("prior_accepted"):
            rec["memory_note"] = (
                f"Similar to {len(memory_context['prior_accepted'])} prior accepted decision(s)"
            )
        elif memory_context.get("prior_denied"):
            rec["memory_note"] = (
                f"Resembles {len(memory_context['prior_denied'])} prior denied decision(s)"
            )

        if memory_context.get("consistency_type") == "consistent":
            rec["consistency_note"] = "Consistent with prior accepted direction"
        elif memory_context.get("consistency_type") == "divergent":
            rec["consistency_note"] = "Moves away from prior direction"
        elif memory_context.get("consistency_type") == "contradictory":
            rec["consistency_note"] = "Directly opposes prior accepted direction"

        recommendations.append(rec)

    return recommendations


def build_operator_review_output(
    candidates: List[Dict[str, Any]],
    memory: Optional[ArchitectureMemory] = None,
) -> Dict[str, Any]:
    """Build memory-aware review output for operator.

    Returns structured output showing:
    - Assessment details
    - Prior accepted items
    - Prior denied items
    - Consistency status
    - Drift/delay/archive recommendations
    """
    assessment = MemoryAwareAssessment()
    if memory is not None:
        assessment.set_memory(memory)

    output = {
        "review_timestamp": datetime.utcnow().isoformat() + "Z",
        "total_candidates": len(candidates),
        "candidates": [],
    }

    for cand in candidates:
        result = assessment.assess_candidate_with_memory(cand)

        candidate_output = {
            "candidate_id": cand.get("id"),
            "title": cand.get("source", {}).get("original_data", {}).get("requested_capability", "Untitled"),
            "assessment": result["weslr_assessment"],
            "memory_summary": {
                "consistency_type": result["weslr_assessment"]["memory_context"]["consistency_type"],
                "prior_accepted_count": len(
                    result["weslr_assessment"]["memory_context"]["prior_accepted"]
                ),
                "prior_denied_count": len(
                    result["weslr_assessment"]["memory_context"]["prior_denied"]
                ),
                "drift_status": result["weslr_assessment"]["memory_context"].get("drift_status", "none"),
            },
            "recommendations": {
                "should_accept": result["weslr_assessment"]["memory_context"].get("should_accept", False),
                "should_reopen": result["weslr_assessment"]["memory_context"].get("should_reopen", False),
                "should_delay": result["weslr_assessment"]["memory_context"].get("delay_recommendation", False),
                "should_archive": result["weslr_assessment"]["memory_context"].get("archive_recommendation", False),
            },
        }

        # Add memory details for review
        if result["weslr_assessment"]["memory_context"]["prior_accepted"]:
            candidate_output["prior_accepted_examples"] = result["weslr_assessment"]["memory_context"]["prior_accepted"][:2]
        if result["weslr_assessment"]["memory_context"]["prior_denied"]:
            candidate_output["prior_denied_examples"] = result["weslr_assessment"]["memory_context"]["prior_denied"][:2]

        output["candidates"].append(candidate_output)

    # Overall summary
    if memory is not None:
        output["memory_summary"] = {
            "total_accepted": len(memory.get_accepted_decisions()),
            "total_denied": len(memory.get_denied_decisions()),
            "drift_detected": ConsistencyEngine.detect_drift(memory).get("drift_detected", False),
        }

    return output
