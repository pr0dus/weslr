"""Recovery Recommendation Export + Replay Correlation (v76)

Read-only export of v75 recovery recommendations into diagnostic trace chain.
Correlates by flow_id, request_id, handshake_id, deadline_id.

Architecture:
  - RecoveryRecommendationExporter — export recommendations with correlation
  - RecoveryRecommendationReplay — replay summaries for operator consumption
  - RecoveryRecommendationSummaryBuilder — build operator-readable summaries

Rules:
  - Read-only export only (no modification of recommendations)
  - Additive only (no breaking changes to v75)
  - Reversible (single file removal)
  - No orchestration, sharding, aggregation
  - No scheduler/task engine
  - No TIA/C#
  - Backward compatible with v72-v75
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .recovery_recommendation_service import RecoveryRecommendationService
from .distributed_diagnostic_hooks import (
    FailureStage,
    FailureType,
    DiagnosticHooks,
    CrossStageCorrelation,
)


# ============================================================================
# RECOVERY RECOMMENDATION EXPORTER
# ============================================================================


class RecoveryRecommendationExporter:
    """Export recovery recommendations into diagnostic trace chain.
    
    Provides read-only export of v75 recommendations with correlation IDs.
    Does NOT modify the underlying recommendations.
    """
    
    def __init__(self, service: RecoveryRecommendationService):
        """Initialize exporter with service reference."""
        self._service = service
    
    def export_all_recommendations(self) -> List[Dict[str, Any]]:
        """Export all recommendations as structured dictionaries.
        
        Returns:
            List of recommendation dicts with correlation IDs
        """
        recommendations = self._service.get_all_recommendations()
        return [self._export_recommendation(rec) for rec in recommendations]
    
    def _export_recommendation(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Export a single recommendation with correlation trace.
        
        Args:
            recommendation: Recommendation dict from v75 service
            
        Returns:
            Export-ready dict with correlation IDs and metadata
        """
        correlation_ids = recommendation.get("correlation_ids", {})
        
        return {
            "recommendation_id": recommendation.get("recommendation_id"),
            "stage": recommendation.get("stage"),
            "failure_type": recommendation.get("failure_type"),
            "likely_cause": recommendation.get("likely_cause"),
            "contributing_factors": recommendation.get("contributing_factors", []),
            "recovery_hint": recommendation.get("recovery_hint"),
            "confidence": recommendation.get("confidence"),
            "hint_certainty": recommendation.get("hint_certainty", "suggestion"),
            "generated_at": recommendation.get("generated_at"),
            # Correlation trace
            "correlation_trace": {
                "flow_id": correlation_ids.get("flow_id"),
                "request_id": correlation_ids.get("request_id"),
                "handshake_id": correlation_ids.get("handshake_id"),
                "deadline_id": correlation_ids.get("deadline_id"),
            },
        }
    
    def export_by_flow(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export recommendations grouped by flow ID.
        
        Returns:
            Dict mapping flow_id to list of recommendations
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        recommendations = self._service.get_all_recommendations()
        
        for rec in recommendations:
            correlation_ids = rec.get("correlation_ids", {})
            flow_id = correlation_ids.get("flow_id")
            
            if flow_id:
                if flow_id not in result:
                    result[flow_id] = []
                result[flow_id].append(self._export_recommendation(rec))
        
        return result
    
    def export_by_stage(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export recommendations grouped by failure stage.
        
        Returns:
            Dict mapping stage name to list of recommendations
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        recommendations = self._service.get_all_recommendations()
        
        for rec in recommendations:
            stage = rec.get("stage", "unknown")
            if stage not in result:
                result[stage] = []
            result[stage].append(self._export_recommendation(rec))
        
        return result
    
    def export_json(self, pretty: bool = False) -> str:
        """Export all recommendations as JSON string.
        
        Args:
            pretty: Format with indentation if True
            
        Returns:
            JSON string of all recommendations
        """
        data = self.export_all_recommendations()
        indent = 2 if pretty else None
        return json.dumps(data, indent=indent, default=str)
    
    def export_with_correlations(
        self,
        correlations: List[CrossStageCorrelation]
    ) -> List[Dict[str, Any]]:
        """Export recommendations correlated with cross-stage diagnostics.
        
        Args:
            correlations: List of CrossStageCorrelation objects
            
        Returns:
            List of recommendations with diagnostic correlation data
        """
        result = []
        recommendations = self._service.get_all_recommendations()
        
        for rec in recommendations:
            correlation_ids = rec.get("correlation_ids", {})
            flow_id = correlation_ids.get("flow_id")
            
            export = self._export_recommendation(rec)
            
            # Add diagnostic correlation if available
            for corr in correlations:
                if corr.flow_id == flow_id:
                    export["diagnostic_correlation"] = {
                        "primary_cause": corr.primary_cause,
                        "cascade_triggers": corr.cascade_triggers,
                        "recovery_hint": corr.recovery_hint,
                    }
                    break
            
            result.append(export)
        
        return result


# ============================================================================
# RECOVERY RECOMMENDATION REPLAY
# ============================================================================


class RecoveryRecommendationReplay:
    """Replay summaries for operator consumption.
    
    Provides operator-readable replay of recommendations
    with correlation trace and diagnostic context.
    """
    
    def __init__(self, exporter: RecoveryRecommendationExporter):
        """Initialize replay with exporter reference."""
        self._exporter = exporter
        self._recommendations: List[Dict[str, Any]] = []
    
    def build_replay_summary(self) -> Dict[str, Any]:
        """Build operator-readable replay summary.
        
        Returns:
            Summary dict with recommendation count and breakdown
        """
        recommendations = self._exporter.export_all_recommendations()
        
        # Count by confidence level
        confidence_dist: Dict[str, int] = {}
        for rec in recommendations:
            conf = rec.get("confidence", "unknown")
            confidence_dist[conf] = confidence_dist.get(conf, 0) + 1
        
        # Count by stage
        stage_dist: Dict[str, int] = {}
        for rec in recommendations:
            stage = rec.get("stage", "unknown")
            stage_dist[stage] = stage_dist.get(stage, 0) + 1
        
        # Count by failure type
        type_dist: Dict[str, int] = {}
        for rec in recommendations:
            ftype = rec.get("failure_type", "unknown")
            type_dist[ftype] = type_dist.get(ftype, 0) + 1
        
        # Deduplicate recovery hints
        recovery_hints = list(set(
            rec.get("recovery_hint", "")
            for rec in recommendations
            if rec.get("recovery_hint")
        ))
        
        return {
            "total_recommendations": len(recommendations),
            "confidence_distribution": confidence_dist,
            "stage_distribution": stage_dist,
            "failure_type_distribution": type_dist,
            "unique_recovery_hints": recovery_hints,
        }
    
    def build_operator_readable_summary(self) -> str:
        """Build human-readable operator replay summary.
        
        Returns:
            Multi-line string for operator console
        """
        summary = self.build_replay_summary()
        
        lines = [
            "=== RECOVERY RECOMMENDATION REPLAY SUMMARY ===",
            f"Total Recommendations: {summary['total_recommendations']}",
            "",
            "=== CONFIDENCE DISTRIBUTION (Operator Guidance) ===",
        ]
        
        for conf, count in sorted(summary["confidence_distribution"].items()):
            lines.append(f"  {conf}: {count}")
        
        lines.append("")
        lines.append("=== STAGE DISTRIBUTION ===")
        for stage, count in sorted(summary["stage_distribution"].items()):
            lines.append(f"  {stage}: {count}")
        
        lines.append("")
        lines.append("=== FAILURE TYPE DISTRIBUTION ===")
        for ftype, count in sorted(summary["failure_type_distribution"].items()):
            lines.append(f"  {ftype}: {count}")
        
        if summary["unique_recovery_hints"]:
            lines.append("")
            lines.append("=== UNIQUE RECOVERY HINTS ===")
            for hint in summary["unique_recovery_hints"]:
                lines.append(f"  - {hint}")
        
        return "\n".join(lines)
    
    def export_replay_json(self, pretty: bool = False) -> str:
        """Export replay summary as JSON string.
        
        Args:
            pretty: Format with indentation if True
            
        Returns:
            JSON string of replay summary
        """
        summary = self.build_replay_summary()
        indent = 2 if pretty else None
        return json.dumps(summary, indent=indent, default=str)


# ============================================================================
# RECOVERY RECOMMENDATION SUMMARY BUILDER
# ============================================================================


class RecoveryRecommendationSummaryBuilder:
    """Build comprehensive summary of recovery recommendations.
    
    Provides both operator-readable text and machine-readable JSON summaries.
    """
    
    def __init__(self, service: RecoveryRecommendationService):
        """Initialize builder with service reference."""
        self._service = service
        self._exporter = RecoveryRecommendationExporter(service)
    
    def build_summary(self) -> Dict[str, Any]:
        """Build comprehensive summary dict.
        
        Returns:
            Summary dict with all recommendation data
        """
        recommendations = self._service.get_all_recommendations()
        
        if not recommendations:
            return {
                "total_recommendations": 0,
                "recommendations": [],
                "confidence_distribution": {},
                "stage_distribution": {},
                "failure_type_distribution": {},
                "unique_recovery_hints": [],
                "correlation_trace_summary": {
                    "flow_ids": [],
                    "request_ids": [],
                    "handshake_ids": [],
                    "deadline_ids": [],
                },
            }
        
        # Count confidence levels
        confidence_dist: Dict[str, int] = {}
        for rec in recommendations:
            conf = rec.get("confidence", "unknown")
            confidence_dist[conf] = confidence_dist.get(conf, 0) + 1
        
        # Count stages
        stage_dist: Dict[str, int] = {}
        for rec in recommendations:
            stage = rec.get("stage", "unknown")
            stage_dist[stage] = stage_dist.get(stage, 0) + 1
        
        # Count failure types
        type_dist: Dict[str, int] = {}
        for rec in recommendations:
            ftype = rec.get("failure_type", "unknown")
            type_dist[ftype] = type_dist.get(ftype, 0) + 1
        
        # Collect correlation IDs
        flow_ids = set()
        request_ids = set()
        handshake_ids = set()
        deadline_ids = set()
        
        for rec in recommendations:
            correlation_ids = rec.get("correlation_ids", {})
            if correlation_ids.get("flow_id"):
                flow_ids.add(correlation_ids["flow_id"])
            if correlation_ids.get("request_id"):
                request_ids.add(correlation_ids["request_id"])
            if correlation_ids.get("handshake_id"):
                handshake_ids.add(correlation_ids["handshake_id"])
            if correlation_ids.get("deadline_id"):
                deadline_ids.add(correlation_ids["deadline_id"])
        
        # Deduplicate recovery hints
        recovery_hints = list(set(
            rec.get("recovery_hint", "")
            for rec in recommendations
            if rec.get("recovery_hint")
        ))
        
        # Export recommendations with correlation trace
        exported = self._exporter.export_all_recommendations()
        
        return {
            "total_recommendations": len(recommendations),
            "recommendations": exported,
            "confidence_distribution": confidence_dist,
            "stage_distribution": stage_dist,
            "failure_type_distribution": type_dist,
            "unique_recovery_hints": recovery_hints,
            "correlation_trace_summary": {
                "flow_ids": list(flow_ids),
                "request_ids": list(request_ids),
                "handshake_ids": list(handshake_ids),
                "deadline_ids": list(deadline_ids),
            },
        }
    
    def build_operator_readable_summary(self) -> str:
        """Build human-readable summary string.
        
        Returns:
            Multi-line string for operator console
        """
        summary = self.build_summary()
        
        lines = [
            "=== RECOVERY RECOMMENDATION SUMMARY ===",
            f"Total Recommendations: {summary['total_recommendations']}",
            "",
            "=== CONFIDENCE DISTRIBUTION (Operator Guidance) ===",
        ]
        
        for conf, count in sorted(summary["confidence_distribution"].items()):
            lines.append(f"  {conf}: {count}")
        
        lines.append("")
        lines.append("=== STAGE DISTRIBUTION ===")
        for stage, count in sorted(summary["stage_distribution"].items()):
            lines.append(f"  {stage}: {count}")
        
        lines.append("")
        lines.append("=== FAILURE TYPE DISTRIBUTION ===")
        for ftype, count in sorted(summary["failure_type_distribution"].items()):
            lines.append(f"  {ftype}: {count}")
        
        if summary["unique_recovery_hints"]:
            lines.append("")
            lines.append("=== UNIQUE RECOVERY HINTS ===")
            for hint in summary["unique_recovery_hints"]:
                lines.append(f"  - {hint}")
        
        # Correlation trace summary
        corr = summary.get("correlation_trace_summary", {})
        if corr.get("flow_ids") or corr.get("request_ids") or corr.get("handshake_ids") or corr.get("deadline_ids"):
            lines.append("")
            lines.append("=== CORRELATION TRACE ===")
            if corr.get("flow_ids"):
                lines.append(f"  Flow IDs: {', '.join(corr['flow_ids'])}")
            if corr.get("request_ids"):
                lines.append(f"  Request IDs: {', '.join(corr['request_ids'])}")
            if corr.get("handshake_ids"):
                lines.append(f"  Handshake IDs: {', '.join(corr['handshake_ids'])}")
            if corr.get("deadline_ids"):
                lines.append(f"  Deadline IDs: {', '.join(corr['deadline_ids'])}")
        
        return "\n".join(lines)
    
    def export_json(self, pretty: bool = False) -> str:
        """Export summary as JSON string.
        
        Args:
            pretty: Format with indentation if True
            
        Returns:
            JSON string of summary
        """
        summary = self.build_summary()
        indent = 2 if pretty else None
        return json.dumps(summary, indent=indent, default=str)


# ============================================================================
# INTEGRATION HOOKS
# ============================================================================


def create_recommendation_exporter(
    service: RecoveryRecommendationService = None
) -> RecoveryRecommendationExporter:
    """Factory function to create recommendation exporter.
    
    Args:
        service: Optional service instance (creates new if None)
        
    Returns:
        RecoveryRecommendationExporter instance
    """
    if service is None:
        service = RecoveryRecommendationService()
    return RecoveryRecommendationExporter(service)


def create_recommendation_replay(
    exporter: RecoveryRecommendationExporter = None,
    service: RecoveryRecommendationService = None
) -> RecoveryRecommendationReplay:
    """Factory function to create recommendation replay.
    
    Args:
        exporter: Optional exporter instance
        service: Optional service instance (used if exporter is None)
        
    Returns:
        RecoveryRecommendationReplay instance
    """
    if exporter is None:
        exporter = create_recommendation_exporter(service)
    return RecoveryRecommendationReplay(exporter)


def create_recommendation_summary_builder(
    service: RecoveryRecommendationService = None
) -> RecoveryRecommendationSummaryBuilder:
    """Factory function to create summary builder.
    
    Args:
        service: Optional service instance (creates new if None)
        
    Returns:
        RecoveryRecommendationSummaryBuilder instance
    """
    if service is None:
        service = RecoveryRecommendationService()
    return RecoveryRecommendationSummaryBuilder(service)


def integrate_with_diagnostics(
    diagnostics: DiagnosticHooks,
    service: RecoveryRecommendationService = None
) -> Dict[str, Any]:
    """Integrate recommendations with diagnostic hooks.
    
    Correlates recovery recommendations with cross-stage diagnostics.
    
    Args:
        diagnostics: DiagnosticHooks instance
        service: Optional service instance (creates new if None)
        
    Returns:
        Combined recommendations with diagnostic correlation
    """
    if service is None:
        service = RecoveryRecommendationService()
    
    exporter = RecoveryRecommendationExporter(service)
    correlations = diagnostics._correlator.correlate_all_flows()
    
    return exporter.export_with_correlations(correlations)
