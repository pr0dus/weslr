"""Distributed Diagnostic Trace Export (v72)

Structured trace export for failure sequence reconstruction, replay validation,
and operator-readable summaries. Maintains backward compatibility with v70/v71 exports.

Architecture:
  - TraceExportRecord — structured trace export record
  - FailureTraceReconstructor — rebuilds failure sequences from trace data
  - TraceExportValidator — validates correlation (flow/request/handshake/deadline IDs)
  - ExportConsistencyChecker — validates timestamp ordering, stage progression, consistency score
  - ReplaySummaryGenerator — generates operator-readable replay summaries
  - TraceExporter — machine-readable replay exports

Rules:
  - Read-only trace export only
  - Correlation validation across flow/request/handshake/deadline IDs
  - Backward compatible with v70/v71 exports
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
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .distributed_diagnostic_hooks import (
    DiagnosticHooks,
    FailureClassification,
    StageDiagnosis,
    CrossStageCorrelation,
    FailureStage,
    FailureType,
)
from .diagnostic_export import (
    DiagnosticExportHooks,
    DiagnosticSummaryExporter,
    FailureChainExporter,
    RecoveryHintExporter,
)
from .execution_telemetry import (
    TelemetryEventEmitter,
    TelemetryEvent,
    TelemetryEventType,
)


# ============================================================================
# TRACE EXPORT RECORD
# ============================================================================


class ExportVersion(str, Enum):
    """Export format versions."""
    V70 = "v70.0.0"
    V71 = "v71.0.0"
    V72 = "v72.0.0"


class ExportFormat(str, Enum):
    """Export format types."""
    OPERATOR_READABLE = "operator_readable"
    MACHINE_READABLE = "machine_readable"
    REPLAY_EXPORT = "replay_export"


@dataclass
class TraceExportRecord:
    """Structured trace export record.
    
    Core data structure for diagnostic trace exports with correlation context.
    Maintains backward compatibility across versions.
    """
    
    # Core identification
    record_id: str
    export_version: str
    export_format: str = field(default_factory=lambda: ExportFormat.MACHINE_READABLE.value)
    
    # Correlation context
    flow_id: Optional[str] = None
    request_id: Optional[str] = None
    handshake_id: Optional[str] = None
    deadline_id: Optional[str] = None
    
    # Timing
    exported_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    correlation_start: Optional[str] = None
    correlation_end: Optional[str] = None
    
    # Failure/trace data
    failure_type: Optional[str] = None
    failure_stage: Optional[str] = None
    observed_error: Optional[str] = None
    observed_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Correlation IDs
    correlation_ids: Dict[str, str] = field(default_factory=dict)
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Validation scores
    correlation_score: float = 1.0
    timestamp_valid: bool = True
    stage_progression_valid: bool = True
    
    # Backward compatibility fields
    v70_compatibility: Optional[Dict[str, Any]] = None
    v71_compatibility: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize record to dict."""
        return {
            "record_id": self.record_id,
            "export_version": self.export_version,
            "export_format": self.export_format,
            "flow_id": self.flow_id,
            "request_id": self.request_id,
            "handshake_id": self.handshake_id,
            "deadline_id": self.deadline_id,
            "exported_at": self.exported_at,
            "correlation_start": self.correlation_start,
            "correlation_end": self.correlation_end,
            "failure_type": self.failure_type,
            "failure_stage": self.failure_stage,
            "observed_error": self.observed_error,
            "observed_events": self.observed_events,
            "correlation_ids": self.correlation_ids,
            "context": self.context,
            "correlation_score": self.correlation_score,
            "timestamp_valid": self.timestamp_valid,
            "stage_progression_valid": self.stage_progression_valid,
            "v70_compatibility": self.v70_compatibility,
            "v71_compatibility": self.v71_compatibility,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceExportRecord":
        """Deserialize record from dict."""
        return cls(
            record_id=data.get("record_id", str(uuid.uuid4())),
            export_version=data.get("export_version", ExportVersion.V72.value),
            export_format=data.get("export_format", ExportFormat.MACHINE_READABLE.value),
            flow_id=data.get("flow_id"),
            request_id=data.get("request_id"),
            handshake_id=data.get("handshake_id"),
            deadline_id=data.get("deadline_id"),
            exported_at=data.get("exported_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            correlation_start=data.get("correlation_start"),
            correlation_end=data.get("correlation_end"),
            failure_type=data.get("failure_type"),
            failure_stage=data.get("failure_stage"),
            observed_error=data.get("observed_error"),
            observed_events=data.get("observed_events", []),
            correlation_ids=data.get("correlation_ids", {}),
            context=data.get("context", {}),
            correlation_score=data.get("correlation_score", 1.0),
            timestamp_valid=data.get("timestamp_valid", True),
            stage_progression_valid=data.get("stage_progression_valid", True),
            v70_compatibility=data.get("v70_compatibility"),
            v71_compatibility=data.get("v71_compatibility"),
        )
    
    def to_json(self) -> str:
        """Serialize record to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "TraceExportRecord":
        """Deserialize record from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def is_valid_correlation(self) -> bool:
        """Check if this record has valid correlation context."""
        return (
            self.correlation_score >= 0.8
            and self.timestamp_valid
            and self.stage_progression_valid
        )
    
    def get_all_correlation_ids(self) -> Dict[str, str]:
        """Get all correlation IDs including v70/v71 compatibility."""
        ids = self.correlation_ids.copy()
        if self.flow_id:
            ids["flow_id"] = self.flow_id
        if self.request_id:
            ids["request_id"] = self.request_id
        if self.handshake_id:
            ids["handshake_id"] = self.handshake_id
        if self.deadline_id:
            ids["deadline_id"] = self.deadline_id
        
        # Add v70/v71 compatibility IDs if present
        if self.v70_compatibility:
            for key, value in self.v70_compatibility.get("correlation_ids", {}).items():
                if key not in ids:
                    ids[key] = value
        
        if self.v71_compatibility:
            for key, value in self.v71_compatibility.get("correlation_ids", {}).items():
                if key not in ids:
                    ids[key] = value
        
        return ids


# ============================================================================
# FAILURE TRACE RECONSTRUCTOR
# ============================================================================


class FailureTraceReconstructor:
    """Rebuilds failure sequences from trace data.
    
    Analyzes trace exports to reconstruct the sequence of events that led to failure.
    """
    
    def __init__(self):
        """Initialize the reconstructor."""
        self._traces: List[TraceExportRecord] = []
    
    def add_trace(self, trace: TraceExportRecord) -> None:
        """Add a trace record to rebuild."""
        self._traces.append(trace)
    
    def add_traces(self, traces: List[TraceExportRecord]) -> None:
        """Add multiple trace records."""
        self._traces.extend(traces)
    
    def rebuild_failure_sequence(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Rebuild failure sequence for a specific flow.
        
        Args:
            flow_id: The flow ID to reconstruct
            
        Returns:
            Dictionary with reconstructed failure sequence or None if not found
        """
        # Find traces for this flow
        flow_traces = [
            t for t in self._traces
            if t.flow_id == flow_id or flow_id in t.correlation_ids.values()
        ]
        
        if not flow_traces:
            return None
        
        # Sort by exported_at timestamp
        sorted_traces = sorted(flow_traces, key=lambda t: t.exported_at)
        
        # Reconstruct sequence
        sequence: List[Dict[str, Any]] = []
        for trace in sorted_traces:
            event = {
                "timestamp": trace.exported_at,
                "stage": trace.failure_stage,
                "failure_type": trace.failure_type,
                "error": trace.observed_error,
                "correlation_ids": trace.correlation_ids,
                "events": trace.observed_events,
            }
            sequence.append(event)
        
        # Build summary
        stages = [s.get("stage") for s in sequence if s.get("stage")]
        failure_types = [s.get("failure_type") for s in sequence if s.get("failure_type")]
        
        return {
            "flow_id": flow_id,
            "reconstructed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "sequence": sequence,
            "stages_affected": list(dict.fromkeys(stages)),  # unique, preserve order
            "failure_types": list(dict.fromkeys(failure_types)),
            "total_events": sum(len(t.observed_events) for t in flow_traces),
        }
    
    def rebuild_all_failure_sequences(self) -> Dict[str, Dict[str, Any]]:
        """Rebuild failure sequences for all flows.
        
        Returns:
            Dictionary mapping flow IDs to reconstructed sequences
        """
        sequences = {}
        flow_ids = set()
        
        for trace in self._traces:
            if trace.flow_id:
                flow_ids.add(trace.flow_id)
            for key, value in trace.correlation_ids.items():
                if key == "flow_id":
                    flow_ids.add(value)
        
        for flow_id in flow_ids:
            sequence = self.rebuild_failure_sequence(flow_id)
            if sequence:
                sequences[flow_id] = sequence
        
        return sequences
    
    def get_failure_timeline(self, flow_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get a timeline of events for a specific flow.
        
        Args:
            flow_id: The flow ID to build timeline for
            
        Returns:
            List of events sorted by timestamp or None
        """
        sequence = self.rebuild_failure_sequence(flow_id)
        if not sequence:
            return None
        
        return sequence.get("sequence", [])
    
    def get_root_cause(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get the root cause of failure for a specific flow.
        
        Args:
            flow_id: The flow ID to analyze
            
        Returns:
            Root cause information or None
        """
        sequence = self.rebuild_failure_sequence(flow_id)
        if not sequence or not sequence.get("sequence"):
            return None
        
        first_failure = sequence["sequence"][0]
        return {
            "stage": first_failure.get("stage"),
            "failure_type": first_failure.get("failure_type"),
            "error": first_failure.get("error"),
        }


# ============================================================================
# TRACE EXPORT VALIDATOR
# ============================================================================


class TraceExportValidator:
    """Validates correlation across flow/request/handshake/deadline IDs.
    
    Ensures trace exports have valid correlation context for replay.
    """
    
    def __init__(self):
        """Initialize the validator."""
        self._errors: List[Dict[str, Any]] = []
    
    def validate_record(self, record: TraceExportRecord) -> Tuple[bool, List[str]]:
        """Validate a single trace export record.
        
        Args:
            record: The record to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check required correlation IDs
        correlation_ids = record.get_all_correlation_ids()
        
        if not correlation_ids.get("flow_id"):
            errors.append("Missing flow_id correlation")
        
        # Check handshake ID if handshake stage is present
        if record.failure_stage == FailureStage.HANDSHAKE.value:
            if not correlation_ids.get("handshake_id"):
                errors.append("Handshake stage requires handshake_id correlation")
        
        # Check deadline ID if deadline stage is present
        if record.failure_stage == FailureStage.DEADLINE.value:
            if not correlation_ids.get("deadline_id"):
                errors.append("Deadline stage requires deadline_id correlation")
        
        # Check request ID consistency
        if record.failure_stage in [FailureStage.PROPOSAL.value, FailureStage.ENVELOPE.value]:
            if not correlation_ids.get("request_id"):
                errors.append("Proposal/Envelope stage requires request_id correlation")
        
        return len(errors) == 0, errors
    
    def validate_records(self, records: List[TraceExportRecord]) -> Dict[str, Any]:
        """Validate multiple trace export records.
        
        Args:
            records: The records to validate
            
        Returns:
            Validation results with summary
        """
        valid_count = 0
        invalid_count = 0
        all_errors: List[Dict[str, Any]] = []
        
        for record in records:
            is_valid, errors = self.validate_record(record)
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                all_errors.append({
                    "record_id": record.record_id,
                    "flow_id": record.flow_id,
                    "errors": errors,
                })
        
        return {
            "total": len(records),
            "valid": valid_count,
            "invalid": invalid_count,
            "error_details": all_errors,
            "validity_ratio": valid_count / len(records) if records else 0,
        }
    
    def validate_correlation_chain(self, records: List[TraceExportRecord]) -> Dict[str, Any]:
        """Validate correlation chain across multiple records.
        
        Ensures that correlation IDs link records together properly.
        
        Args:
            records: Records to validate as a chain
            
        Returns:
            Chain validation results
        """
        if not records:
            return {
                "valid": True,
                "message": "No records to validate",
            }
        
        # Build correlation graph
        flow_ids = set()
        request_ids = set()
        handshake_ids = set()
        deadline_ids = set()
        
        for record in records:
            correlation_ids = record.get_all_correlation_ids()
            if correlation_ids.get("flow_id"):
                flow_ids.add(correlation_ids["flow_id"])
            if correlation_ids.get("request_id"):
                request_ids.add(correlation_ids["request_id"])
            if correlation_ids.get("handshake_id"):
                handshake_ids.add(correlation_ids["handshake_id"])
            if correlation_ids.get("deadline_id"):
                deadline_ids.add(correlation_ids["deadline_id"])
        
        # Check for consistency
        valid = (
            len(flow_ids) <= 1
            and len(request_ids) <= 1
            and len(handshake_ids) <= 1
            and len(deadline_ids) <= 1
        )
        
        return {
            "valid": valid,
            "flow_id_count": len(flow_ids),
            "request_id_count": len(request_ids),
            "handshake_id_count": len(handshake_ids),
            "deadline_id_count": len(deadline_ids),
            "unique_flow_ids": list(flow_ids),
            "unique_request_ids": list(request_ids),
            "unique_handshake_ids": list(handshake_ids),
            "unique_deadline_ids": list(deadline_ids),
        }


# ============================================================================
# EXPORT CONSISTENCY CHECKER
# ============================================================================


class ExportConsistencyChecker:
    """Validates timestamp ordering, stage progression, and computes consistency scores.
    
    Ensures trace exports are internally consistent for replay.
    """
    
    def __init__(self):
        """Initialize the consistency checker."""
        self._flow_ordering: Dict[str, List[datetime]] = {}
    
    def _parse_timestamp(self, timestamp: str) -> datetime:
        """Parse ISO timestamp string to datetime."""
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)
    
    def validate_timestamp_ordering(
        self,
        records: List[TraceExportRecord]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Validate timestamp ordering within and across records.
        
        Checks that timestamps are in chronological order as provided in the list.
        
        Args:
            records: Records to validate
            
        Returns:
            Tuple of (is_valid, list of ordering issues)
        """
        issues: List[Dict[str, Any]] = []
        
        if len(records) < 2:
            return True, issues
        
        # Check for ordering violations without reordering
        for i in range(1, len(records)):
            prev_record = records[i - 1]
            curr_record = records[i]
            
            prev_time = self._parse_timestamp(prev_record.exported_at)
            curr_time = self._parse_timestamp(curr_record.exported_at)
            
            # Timestamps should be strictly increasing (allow small tolerance for clock skew)
            tolerance_ms = 100  # 100ms tolerance
            if curr_time.timestamp() * 1000 < (prev_time.timestamp() * 1000 - tolerance_ms):
                issues.append({
                    "type": "timestamp_reorder",
                    "prev_record_id": prev_record.record_id,
                    "curr_record_id": curr_record.record_id,
                    "prev_timestamp": prev_record.exported_at,
                    "curr_timestamp": curr_record.exported_at,
                })
        
        return len(issues) == 0, issues
    
    def validate_stage_progression(
        self,
        records: List[TraceExportRecord]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Validate stage progression follows execution lifecycle.
        
        Stages should progress in order: proposal -> handshake -> envelope -> receipt -> deadline -> completed
        
        Args:
            records: Records to validate
            
        Returns:
            Tuple of (is_valid, list of progression issues)
        """
        issues: List[Dict[str, Any]] = []
        
        # Define valid stage order
        stage_order = {
            FailureStage.PROPOSAL.value: 0,
            FailureStage.HANDSHAKE.value: 1,
            FailureStage.ENVELOPE.value: 2,
            FailureStage.RECEIPT.value: 3,
            FailureStage.DEADLINE.value: 4,
            FailureStage.COMPLETED.value: 5,
        }
        
        # Group records by flow
        by_flow: Dict[str, List[TraceExportRecord]] = {}
        for record in records:
            flow_id = record.flow_id
            if not flow_id:
                # Check correlation IDs
                correlation_ids = record.get_all_correlation_ids()
                flow_id = correlation_ids.get("flow_id", "unknown")
            
            if flow_id not in by_flow:
                by_flow[flow_id] = []
            by_flow[flow_id].append(record)
        
        # Check each flow's stage progression
        for flow_id, flow_records in by_flow.items():
            sorted_flow = sorted(
                flow_records,
                key=lambda r: self._parse_timestamp(r.exported_at)
            )
            
            prev_stage_idx = -1
            for record in sorted_flow:
                stage = record.failure_stage or FailureStage.UNKNOWN.value
                curr_stage_idx = stage_order.get(stage, -1)
                
                if curr_stage_idx >= 0 and prev_stage_idx >= 0:
                    if curr_stage_idx < prev_stage_idx:
                        issues.append({
                            "type": "stage_regression",
                            "flow_id": flow_id,
                            "prev_stage": sorted_flow[sorted_flow.index(record) - 1].failure_stage if sorted_flow.index(record) > 0 else None,
                            "curr_stage": stage,
                        })
                
                prev_stage_idx = curr_stage_idx
        
        return len(issues) == 0, issues
    
    def compute_consistency_score(
        self,
        records: List[TraceExportRecord]
    ) -> Dict[str, Any]:
        """Compute overall consistency score for trace exports.
        
        Considers:
        - Timestamp ordering
        - Stage progression
        - Correlation completeness
        - Event coverage
        
        Args:
            records: Records to score
            
        Returns:
            Consistency score with breakdown
        """
        # Validate components
        timestamp_valid, timestamp_issues = self.validate_timestamp_ordering(records)
        stage_valid, stage_issues = self.validate_stage_progression(records)
        
        # Check correlation completeness
        correlation_scores = []
        for record in records:
            correlation_ids = record.get_all_correlation_ids()
            expected_ids = ["flow_id", "request_id", "handshake_id", "deadline_id"]
            
            present_ids = [k for k in expected_ids if correlation_ids.get(k)]
            score = len(present_ids) / len(expected_ids) if expected_ids else 1.0
            correlation_scores.append(score)
        
        avg_correlation = sum(correlation_scores) / len(correlation_scores) if correlation_scores else 1.0
        
        # Compute overall score (weighted average)
        timestamp_score = 1.0 if timestamp_valid else 0.0
        stage_score = 1.0 if stage_valid else 0.0
        
        # Weight correlation more heavily
        overall_score = (
            timestamp_score * 0.2 +
            stage_score * 0.2 +
            avg_correlation * 0.6
        )
        
        # Handle empty records case - no failures means perfect score
        if len(records) == 0:
            overall_score = 1.0
        
        return {
            "overall_score": round(overall_score, 3),
            "timestamp_valid": timestamp_valid,
            "timestamp_issues": len(timestamp_issues),
            "stage_valid": stage_valid,
            "stage_issues": len(stage_issues),
            "avg_correlation": round(avg_correlation, 3),
            "total_records": len(records),
        }


# ============================================================================
# REPLAY SUMMARY GENERATOR
# ============================================================================


class ReplaySummaryGenerator:
    """Generates operator-readable replay summaries from trace exports.
    
    Creates summaries that operators can use to understand and replay failures.
    """
    
    def __init__(self):
        """Initialize the summary generator."""
        self._reconstructor = FailureTraceReconstructor()
    
    def generate_summary(self, records: List[TraceExportRecord]) -> str:
        """Generate a replay summary for operator consumption.
        
        Args:
            records: Trace export records to summarize
            
        Returns:
            Multi-line string summary for operator console
        """
        if not records:
            return "=== REPLAY SUMMARY ===\nNo trace records available.\n"
        
        # Add records to reconstructor
        self._reconstructor.add_traces(records)
        
        # Get unique flow IDs (filter for actual strings)
        flow_ids = set()
        for record in records:
            if record.flow_id and isinstance(record.flow_id, str):
                flow_ids.add(record.flow_id)
            correlation_ids = record.get_all_correlation_ids()
            if correlation_ids.get("flow_id") and isinstance(correlation_ids.get("flow_id"), str):
                flow_ids.add(correlation_ids["flow_id"])
        
        lines = [
            "=== REPLAY SUMMARY ===",
            f"Total Records: {len(records)}",
            f"Unique Flows: {len(flow_ids)}",
            "",
        ]
        
        if not flow_ids:
            lines.append("No flow IDs found in records.")
            return "\n".join(lines)
        
        # Summary for each flow (filter to ensure only strings)
        valid_flow_ids = [f for f in flow_ids if isinstance(f, str)]
        for flow_id in sorted(valid_flow_ids):
            sequence = self._reconstructor.rebuild_failure_sequence(flow_id)
            
            lines.append(f"--- Flow: {flow_id} ---")
            
            if sequence:
                lines.append(f"  Stages Affected: {', '.join(sequence.get('stages_affected', []))}")
                lines.append(f"  Failure Types: {', '.join(sequence.get('failure_types', []))}")
                lines.append(f"  Total Events: {sequence.get('total_events', 0)}")
            else:
                lines.append("  No failure sequence reconstructed")
            
            lines.append("")
        
        # Summary statistics
        lines.append("=== TIMELINE SUMMARY ===")
        timestamps = [r.exported_at for r in records]
        if timestamps:
            sorted_ts = sorted(timestamps)
            lines.append(f"  First Event: {sorted_ts[0]}")
            lines.append(f"  Last Event: {sorted_ts[-1]}")
        
        lines.append("")
        lines.append("=== CORRELATION SUMMARY ===")
        
        # Count by type
        failure_types: Dict[str, int] = {}
        stages: Dict[str, int] = {}
        for record in records:
            ft = record.failure_type or "none"
            failure_types[ft] = failure_types.get(ft, 0) + 1
            
            fs = record.failure_stage or "none"
            stages[fs] = stages.get(fs, 0) + 1
        
        lines.append("  Failure Types:")
        for ft, count in sorted(failure_types.items()):
            lines.append(f"    {ft}: {count}")
        
        lines.append("  Stages:")
        for stage, count in sorted(stages.items()):
            lines.append(f"    {stage}: {count}")
        
        return "\n".join(lines)
    
    def generate_operator_report(self, records: List[TraceExportRecord]) -> Dict[str, Any]:
        """Generate structured operator report.
        
        Args:
            records: Trace export records
            
        Returns:
            Structured dictionary with report data
        """
        summary = self.generate_summary(records)
        
        return {
            "summary": summary,
            "record_count": len(records),
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }


# ============================================================================
# TRACE EXPORTER
# ============================================================================


class TraceExporter:
    """Machine-readable replay exporter for diagnostic traces.
    
    Produces structured exports suitable for replay systems and analysis tools.
    """
    
    def __init__(self, hooks: DiagnosticHooks):
        """Initialize exporter with diagnostic hooks reference."""
        self._hooks = hooks
        self._validator = TraceExportValidator()
        self._consistency_checker = ExportConsistencyChecker()
        self._summary_generator = ReplaySummaryGenerator()
        self._reconstructor = FailureTraceReconstructor()
    
    def export_trace(self, flow_id: str, include_v70_compat: bool = False, include_v71_compat: bool = False) -> Optional[TraceExportRecord]:
        """Export a trace for a specific flow.
        
        Args:
            flow_id: The flow ID to export
            include_v70_compat: Include v70 compatibility data
            include_v71_compat: Include v71 compatibility data
            
        Returns:
            TraceExportRecord or None if no failure
        """
        # Get detailed diagnosis
        detailed = self._hooks.get_detailed_diagnosis(flow_id)
        if not detailed:
            return None
        
        # Build correlation IDs
        correlation_ids = detailed.get("correlation_ids", {})
        
        # Get all events for this flow
        emitter = self._hooks._correlator._emitter
        events = emitter.get_events_by_flow(flow_id)
        events_data = [e.to_dict() for e in events]
        
        # Determine failure stage and type
        failures_by_stage = detailed.get("failures_by_stage", {})
        primary_stage = None
        primary_failure_type = None
        
        for stage, diagnosis_data in failures_by_stage.items():
            primary_stage = stage
            # Handle both StageDiagnosis objects and dict representations
            if hasattr(diagnosis_data, 'failure_type'):
                primary_failure_type = diagnosis_data.failure_type
            elif isinstance(diagnosis_data, dict):
                primary_failure_type = diagnosis_data.get('failure_type')
            break
        
        # Build record
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            export_format=ExportFormat.MACHINE_READABLE.value,
            flow_id=flow_id,
            correlation_start=detailed.get("event_timeline", [{}])[-1].get("timestamp", "") if detailed.get("event_timeline") else None,
            failure_stage=primary_stage,
            failure_type=primary_failure_type,
            observed_error=detailed.get("primary_cause"),
            observed_events=events_data,
            correlation_ids=correlation_ids,
            context=detailed,
        )
        
        # Add compatibility data
        if include_v70_compat:
            record.v70_compatibility = self._build_v70_compatibility(flow_id)
        
        if include_v71_compat:
            record.v71_compatibility = self._build_v71_compatibility(flow_id)
        
        return record
    
    def _build_v70_compatibility(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Build v70 compatibility data from flow diagnosis."""
        classification = self._hooks._classifier.classify_flow_failure(flow_id)
        if not classification:
            return None
        
        return {
            "export_version": ExportVersion.V70.value,
            "export_format": ExportFormat.OPERATOR_READABLE.value,
            "correlation_ids": classification.correlation_ids,
            "failure_classification": {
                "failure_type": classification.failure_type,
                "stage": classification.stage,
                "observed_error": classification.observed_error,
                "context": classification.context,
            },
        }
    
    def _build_v71_compatibility(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Build v71 compatibility data from chain export."""
        detailed = self._hooks.get_detailed_diagnosis(flow_id)
        if not detailed:
            return None
        
        return {
            "export_version": ExportVersion.V71.value,
            "export_format": ExportFormat.OPERATOR_READABLE.value,
            "correlation_ids": detailed.get("correlation_ids", {}),
            "chain_data": {
                "primary_cause": detailed.get("primary_cause"),
                "cascade_triggers": detailed.get("cascade_triggers", []),
                "recovery_hint": detailed.get("recovery_hint"),
            },
        }
    
    def export_all_traces(self, include_v70_compat: bool = False, include_v71_compat: bool = False) -> List[TraceExportRecord]:
        """Export all traces.
        
        Args:
            include_v70_compat: Include v70 compatibility data
            include_v71_compat: Include v71 compatibility data
            
        Returns:
            List of trace export records
        """
        traces = []
        flows = self._hooks._correlator._emitter.get_all_flows()
        
        for flow_id in flows:
            trace = self.export_trace(flow_id, include_v70_compat, include_v71_compat)
            if trace:
                traces.append(trace)
        
        return traces
    
    def export_as_dict(self, flow_id: Optional[str] = None, include_v70_compat: bool = False, include_v71_compat: bool = False) -> Dict[str, Any]:
        """Export traces as structured dictionary.
        
        Args:
            flow_id: Optional specific flow ID
            include_v70_compat: Include v70 compatibility data
            include_v71_compat: Include v71 compatibility data
            
        Returns:
            Dictionary with trace data and metadata
        """
        if flow_id:
            traces = [self.export_trace(flow_id, include_v70_compat, include_v71_compat)]
            traces = [t for t in traces if t]
        else:
            traces = self.export_all_traces(include_v70_compat, include_v71_compat)
        
        # Validate and check consistency
        validation = self._validator.validate_records(traces)
        consistency = self._consistency_checker.compute_consistency_score(traces)
        summary = self._summary_generator.generate_operator_report(traces)
        
        return {
            "export_metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "export_version": ExportVersion.V72.value,
                "flow_count": len(traces),
            },
            "traces": [t.to_dict() for t in traces],
            "validation": validation,
            "consistency": consistency,
            "summary": summary,
        }
    
    def export_as_json(self, flow_id: Optional[str] = None, pretty: bool = False, include_v70_compat: bool = False, include_v71_compat: bool = False) -> str:
        """Export traces as JSON string.
        
        Args:
            flow_id: Optional specific flow ID
            pretty: If True, format with indentation
            include_v70_compat: Include v70 compatibility data
            include_v71_compat: Include v71 compatibility data
            
        Returns:
            JSON string with trace data
        """
        data = self.export_as_dict(flow_id, include_v70_compat, include_v71_compat)
        
        if pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)
    
    def export_replayable(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Export trace in replayable format.
        
        Includes all data needed to replay the failure scenario.
        
        Args:
            flow_id: The flow ID to export
            
        Returns:
            Replayable export dict or None
        """
        trace = self.export_trace(flow_id, include_v70_compat=True, include_v71_compat=True)
        if not trace:
            return None
        
        # Build replay data
        sequence = self._reconstructor.rebuild_failure_sequence(flow_id)
        
        return {
            "export_metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "export_version": ExportVersion.V72.value,
                "export_format": ExportFormat.REPLAY_EXPORT.value,
            },
            "record_id": trace.record_id,
            "flow_id": trace.flow_id,
            "correlation_ids": trace.correlation_ids,
            "failure_context": {
                "stage": trace.failure_stage,
                "type": trace.failure_type,
                "error": trace.observed_error,
            },
            "event_timeline": trace.observed_events,
            "reconstructed_sequence": sequence,
            "validation": {
                "correlation_valid": trace.is_valid_correlation(),
                "timestamp_valid": trace.timestamp_valid,
                "stage_progression_valid": trace.stage_progression_valid,
            },
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================


def create_trace_exporter(emitter: TelemetryEventEmitter) -> TraceExporter:
    """Factory function to create trace exporter.
    
    Args:
        emitter: TelemetryEventEmitter for event data
        
    Returns:
        TraceExporter instance
    """
    from .distributed_diagnostic_hooks import DiagnosticHooks
    diagnostic_hooks = DiagnosticHooks(emitter)
    return TraceExporter(diagnostic_hooks)


def create_reconstructor() -> FailureTraceReconstructor:
    """Factory function to create failure trace reconstructor.
    
    Returns:
        FailureTraceReconstructor instance
    """
    return FailureTraceReconstructor()


def create_validator() -> TraceExportValidator:
    """Factory function to create trace export validator.
    
    Returns:
        TraceExportValidator instance
    """
    return TraceExportValidator()


def create_consistency_checker() -> ExportConsistencyChecker:
    """Factory function to create export consistency checker.
    
    Returns:
        ExportConsistencyChecker instance
    """
    return ExportConsistencyChecker()


def create_summary_generator() -> ReplaySummaryGenerator:
    """Factory function to create replay summary generator.
    
    Returns:
        ReplaySummaryGenerator instance
    """
    return ReplaySummaryGenerator()
