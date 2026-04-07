"""Distributed Diagnostic Export Hooks (v71)

Structured export hooks for diagnostic summaries, correlated failure chains,
and recovery hints from v70 diagnostic reasoning.

Architecture:
  - DiagnosticSummaryExporter — diagnostic summary export
  - FailureChainExporter — correlated failure-chain export
  - RecoveryHintExporter — recovery-hint export with correlation
  - DiagnosticExportHooks — unified read-only API surface

Rules:
  - Read-only diagnostics export only
  - Correlation by flow/request/handshake/deadline IDs
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No telemetry backend/service
  - No scheduler/task engine
  - No consensus
  - No orchestration, sharding, aggregation
  - No TIA/C#
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .distributed_diagnostic_hooks import (
    DiagnosticHooks,
    FailureClassification,
    StageDiagnosis,
    CrossStageCorrelation,
    DiagnosticSummary,
    FailureClassifier,
    StageDiagnosisBuilder,
    CrossStageCorrelator,
    DiagnosticSummaryBuilder,
)


# ============================================================================
# DIAGNOSTIC SUMMARY EXPORTER
# ============================================================================


class DiagnosticSummaryExporter:
    """Export diagnostic summaries as structured data for operator readability.
    
    Provides read-only export of diagnostic summaries with correlation context.
    """
    
    def __init__(self, hooks: DiagnosticHooks):
        """Initialize exporter with diagnostic hooks reference."""
        self._hooks = hooks
    
    def export_summary(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Export diagnostic summary for a specific flow.
        
        Args:
            flow_id: The flow ID to export
            
        Returns:
            Summary dict or None if no failures
        """
        summary = self._hooks.get_failure_summary(flow_id)
        if not summary:
            return None
        
        return self._enrich_summary(summary, flow_id)
    
    def export_all_summaries(self) -> List[Dict[str, Any]]:
        """Export all diagnostic summaries.
        
        Returns:
            List of summary dicts
        """
        summaries = self._hooks.get_all_failure_summaries()
        return [self._enrich_summary(s, s.get("flow_id", "")) for s in summaries]
    
    def export_by_correlation(
        self,
        correlation_id: str,
        correlation_type: str = "flow_id"
    ) -> List[Dict[str, Any]]:
        """Export summaries filtered by correlation ID.
        
        Args:
            correlation_id: The correlation ID to filter by
            correlation_type: Type of correlation (flow_id, request_id, handshake_id, deadline_id)
            
        Returns:
            List of matching summary dicts
        """
        summaries = self.export_all_summaries()
        return [
            s for s in summaries
            if correlation_id == s.get("flow_id")
            or correlation_id in s.get("correlation_ids", {}).values()
        ]
    
    def export_json(
        self,
        flow_id: Optional[str] = None,
        pretty: bool = False
    ) -> str:
        """Export summaries as JSON string.
        
        Args:
            flow_id: Optional specific flow ID to export
            pretty: If True, format with indentation
            
        Returns:
            JSON string with summary data
        """
        if flow_id:
            summary = self.export_summary(flow_id)
            data = [summary] if summary else []
        else:
            data = self.export_all_summaries()
        
        if pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)
    
    def _enrich_summary(
        self,
        summary: Dict[str, Any],
        flow_id: str
    ) -> Dict[str, Any]:
        """Enrich summary with export metadata."""
        return {
            "export_metadata": {
                "exported_at": summary.get("summary_created_at", ""),
                "export_version": "v71.0.0",
                "export_format": "operator_readable"
            },
            **summary
        }
    
    def get_operator_readable_summary(self) -> str:
        """Get human-readable operator summary of all failures.
        
        Returns:
            Multi-line string for operator console
        """
        summaries = self.export_all_summaries()
        
        lines = [
            "=== DIAGNOSTIC SUMMARY EXPORT ===",
            f"Total Flows with Failures: {len(summaries)}",
            "",
        ]
        
        if not summaries:
            lines.append("No failures to report.")
            return "\n".join(lines)
        
        for i, summary in enumerate(summaries, 1):
            flow_id = summary.get("flow_id", "unknown")
            status = summary.get("status", "unknown")
            root_causes = summary.get("root_cause_summary", [])
            recovery_hints = summary.get("recovery_hints", [])
            
            lines.append(f"--- Flow {i}: {flow_id} ---")
            lines.append(f"  Status: {status}")
            
            if root_causes:
                lines.append("  Root Causes:")
                for cause in root_causes:
                    lines.append(f"    - {cause}")
            
            if recovery_hints:
                lines.append("  Recovery Hints:")
                for hint in recovery_hints:
                    lines.append(f"    - {hint}")
            
            lines.append("")
        
        return "\n".join(lines)


# ============================================================================
# FAILURE CHAIN EXPORTER
# ============================================================================


class FailureChainExporter:
    """Export correlated failure chains with full context for analysis.
    
    Provides operator-readable failure chain export including:
    - Stage-by-stage failure breakdown
    - Event timeline
    - Cascade triggers
    - Primary cause hypothesis
    """
    
    def __init__(self, hooks: DiagnosticHooks):
        """Initialize exporter with diagnostic hooks reference."""
        self._hooks = hooks
    
    def export_chain(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Export failure chain for a specific flow.
        
        Args:
            flow_id: The flow ID to export
            
        Returns:
            Chain dict with stages, timeline, and recovery hints, or None
        """
        detailed = self._hooks.get_detailed_diagnosis(flow_id)
        if not detailed:
            return None
        
        return self._enrich_chain(detailed, flow_id)
    
    def export_all_chains(self) -> List[Dict[str, Any]]:
        """Export all failure chains.
        
        Returns:
            List of chain dicts
        """
        # Get all flows with failures
        correlations = []
        flows = self._hooks._correlator._emitter.get_all_flows()
        for flow_id in flows:
            chain = self.export_chain(flow_id)
            if chain:
                correlations.append(chain)
        return correlations
    
    def export_by_correlation(
        self,
        correlation_id: str,
        correlation_type: str = "flow_id"
    ) -> List[Dict[str, Any]]:
        """Export chains filtered by correlation ID.
        
        Args:
            correlation_id: The correlation ID to filter by
            correlation_type: Type of correlation (flow_id, request_id, handshake_id, deadline_id)
            
        Returns:
            List of matching chain dicts
        """
        chains = self.export_all_chains()
        return [
            c for c in chains
            if correlation_id == c.get("flow_id")
            or correlation_id in c.get("correlation_ids", {}).values()
            or correlation_id in c.get("correlation_ids", {}).keys()
            or correlation_id in str(c.get("correlation_ids", {}).values())
        ]
    
    def export_json(
        self,
        flow_id: Optional[str] = None,
        pretty: bool = False
    ) -> str:
        """Export chains as JSON string.
        
        Args:
            flow_id: Optional specific flow ID to export
            pretty: If True, format with indentation
            
        Returns:
            JSON string with chain data
        """
        if flow_id:
            chain = self.export_chain(flow_id)
            data = [chain] if chain else []
        else:
            data = self.export_all_chains()
        
        if pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)
    
    def _enrich_chain(
        self,
        chain: Dict[str, Any],
        flow_id: str
    ) -> Dict[str, Any]:
        """Enrich chain with export metadata."""
        return {
            "export_metadata": {
                "exported_at": chain.get("event_timeline", [{}])[-1].get("timestamp", "") if chain.get("event_timeline") else "",
                "export_version": "v71.0.0",
                "export_format": "operator_readable"
            },
            **chain
        }
    
    def get_operator_readable_summary(self) -> str:
        """Get human-readable operator summary of all failure chains.
        
        Returns:
            Multi-line string for operator console
        """
        chains = self.export_all_chains()
        
        lines = [
            "=== FAILURE CHAIN EXPORT ===",
            f"Total Chains: {len(chains)}",
            "",
        ]
        
        if not chains:
            lines.append("No failure chains to report.")
            return "\n".join(lines)
        
        for i, chain in enumerate(chains, 1):
            flow_id = chain.get("flow_id", "unknown")
            primary_cause = chain.get("primary_cause", "Unknown")
            cascade_triggers = chain.get("cascade_triggers", [])
            recovery_hint = chain.get("recovery_hint", "None")
            
            lines.append(f"--- Chain {i}: {flow_id} ---")
            lines.append(f"  Primary Cause: {primary_cause}")
            
            if cascade_triggers:
                lines.append("  Cascade Triggers:")
                for trigger in cascade_triggers:
                    lines.append(f"    - {trigger}")
            
            lines.append(f"  Recovery Hint: {recovery_hint}")
            lines.append("")
        
        return "\n".join(lines)


# ============================================================================
# RECOVERY HINT EXPORTER
# ============================================================================


class RecoveryHintExporter:
    """Export recovery hints with full correlation and context.
    
    Provides structured export of recovery hints derived from diagnostic analysis.
    Hints are suggestions, not certainty.
    """
    
    def __init__(self, hooks: DiagnosticHooks):
        """Initialize exporter with diagnostic hooks reference."""
        self._hooks = hooks
    
    def export_hint(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Export recovery hint for a specific flow.
        
        Args:
            flow_id: The flow ID to export
            
        Returns:
            Hint dict with correlation context or None if no failure
        """
        detailed = self._hooks.get_detailed_diagnosis(flow_id)
        if not detailed:
            return None
        
        recovery_hint = detailed.get("recovery_hint")
        if not recovery_hint:
            return None
        
        return {
            "flow_id": flow_id,
            "recovery_hint": recovery_hint,
            "correlation_ids": detailed.get("correlation_ids", {}),
            "stages_affected": list(detailed.get("failures_by_stage", {}).keys()),
            "likely_cause": detailed.get("primary_cause"),
            "export_metadata": {
                "exported_at": "",
                "export_version": "v71.0.0",
                "export_format": "operator_readable",
                "hint_certainty": "suggestion"
            }
        }
    
    def export_all_hints(self) -> List[Dict[str, Any]]:
        """Export all recovery hints.
        
        Returns:
            List of hint dicts
        """
        hints = []
        flows = self._hooks._correlator._emitter.get_all_flows()
        for flow_id in flows:
            hint = self.export_hint(flow_id)
            if hint:
                hints.append(hint)
        return hints
    
    def export_by_correlation(
        self,
        correlation_id: str,
        correlation_type: str = "flow_id"
    ) -> List[Dict[str, Any]]:
        """Export hints filtered by correlation ID.
        
        Args:
            correlation_id: The correlation ID to filter by
            correlation_type: Type of correlation (flow_id, request_id, handshake_id, deadline_id)
            
        Returns:
            List of matching hint dicts
        """
        hints = self.export_all_hints()
        return [
            h for h in hints
            if correlation_id in h.get("correlation_ids", {}).values()
            or correlation_id in h.get("correlation_ids", {}).keys()
        ]
    
    def export_json(
        self,
        flow_id: Optional[str] = None,
        pretty: bool = False
    ) -> str:
        """Export hints as JSON string.
        
        Args:
            flow_id: Optional specific flow ID to export
            pretty: If True, format with indentation
            
        Returns:
            JSON string with hint data
        """
        if flow_id:
            hint = self.export_hint(flow_id)
            data = [hint] if hint else []
        else:
            data = self.export_all_hints()
        
        if pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)
    
    def get_operator_readable_summary(self) -> str:
        """Get human-readable operator summary of all recovery hints.
        
        Returns:
            Multi-line string for operator console
        """
        hints = self.export_all_hints()
        
        lines = [
            "=== RECOVERY HINT EXPORT ===",
            f"Total Hints: {len(hints)}",
            "",
        ]
        
        if not hints:
            lines.append("No recovery hints to report.")
            return "\n".join(lines)
        
        for i, hint in enumerate(hints, 1):
            flow_id = hint.get("flow_id", "unknown")
            recovery_hint = hint.get("recovery_hint", "None")
            likely_cause = hint.get("likely_cause", "Unknown")
            stages = hint.get("stages_affected", [])
            
            lines.append(f"--- Hint {i}: {flow_id} ---")
            lines.append(f"  Likely Cause: {likely_cause}")
            lines.append(f"  Stages Affected: {', '.join(stages)}")
            lines.append(f"  Recovery Hint: {recovery_hint}")
            lines.append("")
        
        return "\n".join(lines)


# ============================================================================
# DIAGNOSTIC EXPORT HOOKS
# ============================================================================


class DiagnosticExportHooks:
    """Unified read-only diagnostic export hooks for operator workflow.
    
    Provides structured export of diagnostic summaries, failure chains,
    and recovery hints without orchestration or aggregation.
    """
    
    def __init__(self, hooks: DiagnosticHooks):
        """Initialize export hooks with diagnostic hooks reference."""
        self._hooks = hooks
        self._summary_exporter = DiagnosticSummaryExporter(hooks)
        self._chain_exporter = FailureChainExporter(hooks)
        self._hint_exporter = RecoveryHintExporter(hooks)
    
    # --- Summary Export ---
    
    def export_summary(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Export diagnostic summary for a specific flow.
        
        Args:
            flow_id: The flow ID to export
            
        Returns:
            Summary dict or None if no failures
        """
        return self._summary_exporter.export_summary(flow_id)
    
    def export_all_summaries(self) -> List[Dict[str, Any]]:
        """Export all diagnostic summaries.
        
        Returns:
            List of summary dicts
        """
        return self._summary_exporter.export_all_summaries()
    
    def export_summaries_json(self, pretty: bool = False) -> str:
        """Export all summaries as JSON.
        
        Args:
            pretty: If True, format with indentation
        """
        return self._summary_exporter.export_json(pretty=pretty)
    
    # --- Chain Export ---
    
    def export_chain(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Export failure chain for a specific flow.
        
        Args:
            flow_id: The flow ID to export
            
        Returns:
            Chain dict or None if no failures
        """
        return self._chain_exporter.export_chain(flow_id)
    
    def export_all_chains(self) -> List[Dict[str, Any]]:
        """Export all failure chains.
        
        Returns:
            List of chain dicts
        """
        return self._chain_exporter.export_all_chains()
    
    def export_chains_json(self, pretty: bool = False) -> str:
        """Export all chains as JSON.
        
        Args:
            pretty: If True, format with indentation
        """
        return self._chain_exporter.export_json(pretty=pretty)
    
    # --- Hint Export ---
    
    def export_hint(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Export recovery hint for a specific flow.
        
        Args:
            flow_id: The flow ID to export
            
        Returns:
            Hint dict or None if no failure/hint
        """
        return self._hint_exporter.export_hint(flow_id)
    
    def export_all_hints(self) -> List[Dict[str, Any]]:
        """Export all recovery hints.
        
        Returns:
            List of hint dicts
        """
        return self._hint_exporter.export_all_hints()
    
    def export_hints_json(self, pretty: bool = False) -> str:
        """Export all hints as JSON.
        
        Args:
            pretty: If True, format with indentation
        """
        return self._hint_exporter.export_json(pretty=pretty)
    
    # --- Operator Readable Summaries ---
    
    def get_operator_readable_summary(self) -> str:
        """Get human-readable operator summary.
        
        Returns:
            Multi-line string for operator console
        """
        summary_lines = self._summary_exporter.get_operator_readable_summary()
        chain_lines = self._chain_exporter.get_operator_readable_summary()
        hint_lines = self._hint_exporter.get_operator_readable_summary()
        
        return "\n\n".join([summary_lines, chain_lines, hint_lines])
    
    # --- Export with Correlation Filtering ---
    
    def export_by_correlation(
        self,
        correlation_id: str,
        correlation_type: str = "flow_id"
    ) -> Dict[str, Any]:
        """Export diagnostics filtered by correlation ID.
        
        Args:
            correlation_id: The correlation ID to filter by
            correlation_type: Type of correlation (flow_id, request_id, handshake_id, deadline_id)
            
        Returns:
            Dict with summaries, chains, and hints matching the correlation
        """
        return {
            "summaries": self._summary_exporter.export_by_correlation(
                correlation_id, correlation_type
            ),
            "chains": self._chain_exporter.export_by_correlation(
                correlation_id, correlation_type
            ),
            "hints": self._hint_exporter.export_by_correlation(
                correlation_id, correlation_type
            )
        }
    
    def export_all_as_dict(self) -> Dict[str, Any]:
        """Export all diagnostics as a single structured dict.
        
        Returns:
            Dict with summaries, chains, and hints
        """
        return {
            "summaries": self.export_all_summaries(),
            "chains": self.export_all_chains(),
            "hints": self.export_all_hints()
        }
    
    def export_all_as_json(self, pretty: bool = False) -> str:
        """Export all diagnostics as JSON.
        
        Args:
            pretty: If True, format with indentation
            
        Returns:
            JSON string with all diagnostics
        """
        data = self.export_all_as_dict()
        if pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)


def create_diagnostic_export_hooks(emitter: Any) -> DiagnosticExportHooks:
    """Factory function to create diagnostic export hooks.
    
    Args:
        emitter: TelemetryEventEmitter for event data
        
    Returns:
        DiagnosticExportHooks instance
    """
    from .distributed_diagnostic_hooks import DiagnosticHooks
    diagnostic_hooks = DiagnosticHooks(emitter)
    return DiagnosticExportHooks(diagnostic_hooks)
