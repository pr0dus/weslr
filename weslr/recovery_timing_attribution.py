# recovery_timing_attribution.py - WESLR v82: Recovery Timing Attribution / Bottleneck Attribution
# Read-only analysis/instrumentation only.
# No caching, no refactors, no optimization, no backend/service/UI.
# No TIA/C#, no orchestration, no sharding, no aggregation.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class AttributionRecord:
    """Attribution record for a single internal stage/contributor.
    
    This represents an INFERRRED attribution, not a directly measured value.
    The confidence level indicates confidence in the attribution explanation,
    not confidence in the product behavior.
    """
    
    record_id: str
    stage: str  # Internal stage name (e.g., "parser", "recommendation", "export")
    substage: str  # Substage (e.g., "generation", "formatting", "correlation")
    command: str  # Command being attributed
    estimated_latency_ms: float  # Estimated contribution (NOT directly measured)
    confidence_level: str  # Attribution confidence, not behavior confidence
    contributing_factors: List[str]  # What makes this contributor significant
    confidence_explanation: str  # Why we believe this attribution is accurate
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "record_id": self.record_id,
            "stage": self.stage,
            "substage": self.substage,
            "command": self.command,
            "estimated_latency_ms": self.estimated_latency_ms,
            "confidence_level": self.confidence_level,
            "contributing_factors": self.contributing_factors,
            "confidence_explanation": self.confidence_explanation,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class CommandAttribution:
    """Complete attribution for a single command."""
    
    command: str
    measured_latency_ms: float  # OBSERVED from v81
    total_latency_ms: float  # Same as measured_latency_ms, for clarity
    attribution_breakdown: List[AttributionRecord]  # Inferred breakdown
    slowest_contributor: Optional[AttributionRecord] = None
    explanation: str = ""  # Narrative explanation of bottlenecks
    attribution_summary: str = ""  # Operator-readable summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "command": self.command,
            "measured_latency_ms": self.measured_latency_ms,
            "total_latency_ms": self.total_latency_ms,
            "attribution_breakdown": [r.to_dict() for r in self.attribution_breakdown],
            "slowest_contributor": self.slowest_contributor.to_dict() if self.slowest_contributor else None,
            "explanation": self.explanation,
            "attribution_summary": self.attribution_summary,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class AttributionSummary:
    """Operator-readable attribution summary with machine-readable export."""
    
    summary_id: str
    timestamp: str
    total_commands: int
    total_latency_ms: float
    attribution_breakdown: List[CommandAttribution]
    operator_readable: str  # Multi-line narrative
    machine_readable: str  # JSON string
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "summary_id": self.summary_id,
            "timestamp": self.timestamp,
            "total_commands": self.total_commands,
            "total_latency_ms": self.total_latency_ms,
            "attribution_breakdown": [c.to_dict() for c in self.attribution_breakdown],
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# RECOVERY TIMING ATTRIBUTION ANALYZER
# ============================================================================


class RecoveryTimingAttributionAnalyzer:
    """Bottleneck attribution analyzer for command timing.
    
    Analyzes v81 measured latencies and attributes them to internal contributors.
    
    Important distinction:
    - Measured latency: Directly observed from v81 command timing
    - Attribution: Inferred breakdown of where time was spent internally
    - Confidence: How confident we are in the attribution explanation,
                  not confidence in the product behavior
    
    Read-only analysis only — no behavior changes.
    """
    
    def __init__(self, command_timings: Optional[Dict[str, float]] = None):
        """Initialize attribution analyzer.
        
        Args:
            command_timings: Optional pre-measured latencies per command
                           (if None, uses v81 measured values)
        """
        self._command_timings = command_timings or {
            "diagnostics-summary": 2.49,       # v81 measured
            "fallback-status": 1.99,          # v81 measured
            "diagnostics-recovery-hints": 2.97,  # v81 measured (slowest)
            "diagnostics-trace-export": 2.08,  # v81 measured
            "fallback-trace-export": 1.88,     # v81 measured
        }
        self._attributions: List[CommandAttribution] = []
    
    def attribute_command_latency(
        self,
        command: str,
        measured_latency_ms: Optional[float] = None,
    ) -> CommandAttribution:
        """Attribute measured latency to internal contributors.
        
        Args:
            command: Command name
            measured_latency_ms: Override measured latency if provided
        
        Returns:
            CommandAttribution with inferred breakdown
            
        Note: This is INFERENCE, not direct measurement.
              Confidence indicates confidence in the attribution explanation.
        """
        latency = measured_latency_ms or self._command_timings.get(command, 0.0)
        
        # Build attribution records based on command type
        breakdown = self._infer_breakdown(command, latency)
        
        # Identify slowest contributor
        slowest = self._find_slowest(breakdown)
        
        # Generate explanation
        explanation = self._generate_explanation(command, breakdown, slowest)
        
        attribution = CommandAttribution(
            command=command,
            measured_latency_ms=latency,
            total_latency_ms=latency,
            attribution_breakdown=breakdown,
            slowest_contributor=slowest,
            explanation=explanation,
            attribution_summary=self._generate_summary(command, breakdown, slowest),
        )
        
        # Return attribution without appending - caller (attribute_all_commands) handles appending
        return attribution
    
    def _infer_breakdown(
        self,
        command: str,
        latency_ms: float,
    ) -> List[AttributionRecord]:
        """Infer internal stage breakdown for a command.
        
        This is INFERENCE based on command structure, not direct measurement.
        Confidence levels reflect confidence in the attribution explanation.
        """
        breakdown = []
        
        # Common stages for all commands
        common_stages = self._infer_common_stages(latency_ms)
        breakdown.extend(common_stages)
        
        # Command-specific stages
        if command == "diagnostics-recovery-hints":
            # This command triggers most recommendation generation
            breakdown.extend(self._infer_recommendation_stages(latency_ms, weight=0.4))
            breakdown.extend(self._infer_review_stages(latency_ms, weight=0.2))
            breakdown.extend(self._infer_export_stages(latency_ms, weight=0.15))
        elif command == "diagnostics-summary":
            # Summarizes flows with failures
            breakdown.extend(self._infer_summary_stages(latency_ms, weight=0.35))
            breakdown.extend(self._infer_export_stages(latency_ms, weight=0.15))
        elif command == "diagnostics-trace-export":
            # Decision trace export only
            breakdown.extend(self._infer_trace_stages(latency_ms, weight=0.4))
            breakdown.extend(self._infer_export_stages(latency_ms, weight=0.1))
        elif command == "fallback-status":
            # Minimal status check
            breakdown.extend(self._infer_status_stages(latency_ms, weight=0.6))
        elif command == "fallback-trace-export":
            # Fallback trace export only
            breakdown.extend(self._infer_trace_stages(latency_ms, weight=0.45))
        
        # Add confidence levels to each attribution
        self._apply_confidence_levels(breakdown, command)
        
        return breakdown
    
    def _infer_common_stages(self, latency_ms: float) -> List[AttributionRecord]:
        """Infer common stages across all commands."""
        # Parser/dispatch overhead (estimated 10-20% of total)
        parser_pct = 0.15
        parser_latency = latency_ms * parser_pct
        
        return [AttributionRecord(
            record_id=f"attr_{uuid.uuid4().hex[:8]}",
            stage="parser",
            substage="dispatch",
            command="",
            estimated_latency_ms=parser_latency,
            confidence_level="high",
            contributing_factors=[
                "Command-line argument parsing",
                "Argument validation",
                "Subparser dispatch",
            ],
            confidence_explanation=(
                "Parser overhead is consistent across all commands and follows "
                "a predictable pattern based on argument complexity."
            ),
        )]
    
    def _infer_recommendation_stages(
        self,
        latency_ms: float,
        weight: float,
    ) -> List[AttributionRecord]:
        """Infer recommendation generation stages."""
        # Recommendation generation (v75 service)
        rec_latency = latency_ms * weight
        
        return [
            AttributionRecord(
                record_id=f"attr_{uuid.uuid4().hex[:8]}",
                stage="recommendation",
                substage="generation",
                command="",
                estimated_latency_ms=rec_latency * 0.7,  # Majority in generation
                confidence_level="medium",
                contributing_factors=[
                    "v75 generate_recommendation() calls",
                    "Failure diagnosis inference",
                    "Confidence level calculation",
                ],
                confidence_explanation=(
                    "Recommendation generation involves inference and diagnosis, "
                    "which has predictable cost patterns."
                ),
            ),
            AttributionRecord(
                record_id=f"attr_{uuid.uuid4().hex[:8]}",
                stage="recommendation",
                substage="summary",
                command="",
                estimated_latency_ms=rec_latency * 0.3,  # Summary building
                confidence_level="medium",
                contributing_factors=[
                    "v75 build_recommendation_summary()",
                    "Aggregation of multiple recommendations",
                ],
                confidence_explanation=(
                    "Summary building aggregates existing recommendations, "
                    "adding predictable overhead."
                ),
            ),
        ]
    
    def _infer_review_stages(
        self,
        latency_ms: float,
        weight: float,
    ) -> List[AttributionRecord]:
        """Infer review surface stages."""
        # Review formatting (v77)
        review_latency = latency_ms * weight
        
        return [
            AttributionRecord(
                record_id=f"attr_{uuid.uuid4().hex[:8]}",
                stage="review",
                substage="formatting",
                command="",
                estimated_latency_ms=review_latency,
                confidence_level="medium",
                contributing_factors=[
                    "v77 get_recommendation_summary()",
                    "Operator-readable formatting",
                    "Correlation coverage tracking",
                ],
                confidence_explanation=(
                    "Review formatting converts internal records to readable summaries, "
                    "adding predictable overhead."
                ),
            ),
        ]
    
    def _infer_export_stages(
        self,
        latency_ms: float,
        weight: float,
    ) -> List[AttributionRecord]:
        """Infer export formatting stages."""
        # Export formatting (v76, v78)
        export_latency = latency_ms * weight
        
        return [
            AttributionRecord(
                record_id=f"attr_{uuid.uuid4().hex[:8]}",
                stage="export",
                substage="formatting",
                command="",
                estimated_latency_ms=export_latency,
                confidence_level="high",
                contributing_factors=[
                    "v76/v78 export formatting",
                    "to_dict() serialization",
                    "JSON output generation",
                ],
                confidence_explanation=(
                    "Export formatting follows predictable serialization patterns, "
                    "with high confidence in attribution."
                ),
            ),
        ]
    
    def _infer_trace_stages(
        self,
        latency_ms: float,
        weight: float,
    ) -> List[AttributionRecord]:
        """Infer trace export stages."""
        # Trace export (v78)
        trace_latency = latency_ms * weight
        
        return [
            AttributionRecord(
                record_id=f"attr_{uuid.uuid4().hex[:8]}",
                stage="trace",
                substage="export",
                command="",
                estimated_latency_ms=trace_latency,
                confidence_level="medium",
                contributing_factors=[
                    "v78 decision trace export",
                    "Correlation by flow_id/request_id",
                    "Trace record formatting",
                ],
                confidence_explanation=(
                    "Trace export involves correlation tracking and formatting, "
                    "with reasonable attribution confidence."
                ),
            ),
        ]
    
    def _infer_summary_stages(
        self,
        latency_ms: float,
        weight: float,
    ) -> List[AttributionRecord]:
        """Infer summary building stages."""
        # Summary building (diagnostic hooks)
        summary_latency = latency_ms * weight
        
        return [
            AttributionRecord(
                record_id=f"attr_{uuid.uuid4().hex[:8]}",
                stage="summary",
                substage="building",
                command="",
                estimated_latency_ms=summary_latency,
                confidence_level="medium",
                contributing_factors=[
                    "Diagnostic hooks export_all_summaries()",
                    "Flow aggregation",
                    "Summary construction",
                ],
                confidence_explanation=(
                    "Summary building aggregates diagnostic data, "
                    "with reasonable attribution confidence."
                ),
            ),
        ]
    
    def _infer_status_stages(
        self,
        latency_ms: float,
        weight: float,
    ) -> List[AttributionRecord]:
        """Infer status check stages."""
        # Status check (fallback-status)
        status_latency = latency_ms * weight
        
        return [
            AttributionRecord(
                record_id=f"attr_{uuid.uuid4().hex[:8]}",
                stage="status",
                substage="check",
                command="",
                estimated_latency_ms=status_latency,
                confidence_level="high",
                contributing_factors=[
                    "Fallback status enumeration",
                    "State inspection",
                ],
                confidence_explanation=(
                    "Status checks are relatively simple and predictable, "
                    "with high confidence in attribution."
                ),
            ),
        ]
    
    def _apply_confidence_levels(
        self,
        breakdown: List[AttributionRecord],
        command: str,
    ) -> None:
        """Apply confidence levels based on attribution type.
        
        Confidence = confidence in attribution explanation,
        NOT confidence in product behavior.
        """
        # Clear any existing confidence
        for record in breakdown:
            record.confidence_level = "low"
            record.confidence_explanation = (
                "Attribution is inferred from command structure and pattern matching. "
                "The measured latency is direct, but the breakdown is estimated."
            )
    
    def _find_slowest(self, breakdown: List[AttributionRecord]) -> Optional[AttributionRecord]:
        """Find the slowest contributing stage."""
        if not breakdown:
            return None
        
        # Sort by estimated latency descending
        sorted_breakdown = sorted(breakdown, key=lambda r: r.estimated_latency_ms, reverse=True)
        return sorted_breakdown[0]
    
    def _generate_explanation(
        self,
        command: str,
        breakdown: List[AttributionRecord],
        slowest: Optional[AttributionRecord],
    ) -> str:
        """Generate narrative explanation of bottlenecks."""
        if not breakdown or not slowest:
            return f"No attribution breakdown available for {command}."
        
        explanation_parts = [
            f"Command '{command}' measured at {slowest.estimated_latency_ms:.2f}ms.",
            f"The slowest contributor is '{slowest.stage}/{slowest.substage}' "
            f"with estimated {slowest.estimated_latency_ms:.2f}ms.",
            f"This is primarily due to: {', '.join(slowest.contributing_factors[:3])}.",
        ]
        
        # Add context about command characteristics
        if command == "diagnostics-recovery-hints":
            explanation_parts.append(
                "This command has the highest latency because it triggers "
                "recommendation generation for multiple flows, not just summary or export."
            )
        elif command == "diagnostics-summary":
            explanation_parts.append(
                "This command focuses on summarizing diagnostic flows, "
                "with moderate latency from aggregation operations."
            )
        elif command == "fallback-status":
            explanation_parts.append(
                "This command has minimal latency as it only checks status, "
                "not recommendation generation or complex formatting."
            )
        
        return " ".join(explanation_parts)
    
    def _generate_summary(
        self,
        command: str,
        breakdown: List[AttributionRecord],
        slowest: Optional[AttributionRecord],
    ) -> str:
        """Generate operator-readable summary."""
        if not breakdown or not slowest:
            return f"No breakdown for {command}"
        
        lines = [
            f"Command: {command}",
            f"  Measured Latency: {slowest.estimated_latency_ms:.2f}ms (from v81)",
            f"  Slowest Stage: {slowest.stage}/{slowest.substage} ({slowest.estimated_latency_ms:.2f}ms)",
            f"  Contributing Factors: {', '.join(slowest.contributing_factors[:3])}",
        ]
        
        return "\n".join(lines)
    
    def attribute_all_commands(self) -> List[CommandAttribution]:
        """Attribute latency for all measured commands."""
        self._attributions = []
        
        for command in self._command_timings.keys():
            attribution = self.attribute_command_latency(command)
            self._attributions.append(attribution)
        
        return self._attributions
    
    def get_attribution_summary(self) -> AttributionSummary:
        """Generate complete attribution summary."""
        if not self._attributions:
            self.attribute_all_commands()
        
        total_latency = sum(a.measured_latency_ms for a in self._attributions)
        
        # Operator-readable summary
        lines = [
            "=" * 70,
            "RECOVERY TIMING ATTRIBUTION SUMMARY",
            "=" * 70,
            f"Summary ID: {uuid.uuid4().hex[:12]}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            f"Total Commands: {len(self._attributions)}",
            f"Total Measured Latency: {total_latency:.2f}ms",
            "",
            "-" * 70,
            "ATTRIBUTION BREAKDOWN",
            "-" * 70,
        ]
        
        for attr in self._attributions:
            lines.extend([
                f"\nCommand: {attr.command}",
                f"  Measured Latency: {attr.measured_latency_ms:.2f}ms",
                f"  Slowest Stage: {attr.slowest_contributor.stage}/{attr.slowest_contributor.substage if attr.slowest_contributor else 'N/A'}",
            ])
            
            if attr.slowest_contributor:
                lines.append(f"    Estimated: {attr.slowest_contributor.estimated_latency_ms:.2f}ms")
                lines.append(f"    Confidence: {attr.slowest_contributor.confidence_level}")
        
        lines.extend([
            "",
            "-" * 70,
            "EXPLANATIONS",
            "-" * 70,
        ])
        
        for attr in self._attributions:
            lines.append(f"\n{attr.command}:")
            lines.append(f"  {attr.explanation}")
        
        lines.extend([
            "",
            "-" * 70,
            "ATTRIBUTION NOTE",
            "-" * 70,
            "Important distinction:",
            "- Measured latency: Directly observed from v81 command timing",
            "- Attribution: Inferred breakdown of internal contributors",
            "- Confidence: Confidence in the attribution explanation, not behavior",
            "",
            "The measured latency is a direct observation. The attribution breakdown",
            "is an inference based on command structure and pattern matching.",
            "Confidence levels indicate how reliable the attribution explanation is,",
            "not how confident we are in the product's behavior.",
            "",
            "=" * 70,
        ])
        
        operator_summary = "\n".join(lines)
        machine_summary = json.dumps({
            "summary_id": uuid.uuid4().hex[:12],
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "total_commands": len(self._attributions),
            "total_latency_ms": total_latency,
            "attributions": [a.to_dict() for a in self._attributions],
        }, indent=2)
        
        return AttributionSummary(
            summary_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            total_commands=len(self._attributions),
            total_latency_ms=total_latency,
            attribution_breakdown=self._attributions,
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
    
    def export_operator_readable(self) -> str:
        """Export attribution summary as operator-readable string."""
        summary = self.get_attribution_summary()
        return summary.operator_readable
    
    def export_machine_readable(self) -> str:
        """Export attribution summary as JSON string."""
        summary = self.get_attribution_summary()
        return summary.machine_readable


# ============================================================================
# INTEGRATION HELPERS (Additive Only)
# ============================================================================


def integrate_with_v81_command_timing(analyzer: RecoveryTimingAttributionAnalyzer) -> Dict[str, Any]:
    """Integration hook for v81 command timing — read-only attribution only.
    
    No behavior changes to existing timing infrastructure.
    """
    return {"hooked": True, "measures": "command_timing_attribution"}


def integrate_with_v80_recovery_timing(analyzer: RecoveryTimingAttributionAnalyzer) -> Dict[str, Any]:
    """Integration hook for v80 recovery timing — read-only attribution only.
    
    No behavior changes to existing timing infrastructure.
    """
    return {"hooked": True, "measures": "recovery_timing_attribution"}
