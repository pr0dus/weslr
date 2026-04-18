"""Recovery Recommendation Export + Replay Correlation (v76)

Read-only export layer that integrates v75 recovery recommendations into
the diagnostic trace chain. Correlates by flow_id, request_id,
handshake_id, and deadline_id.

Architecture:
  - RecoveryRecommendationExportRecord — Export record with correlation
  - RecoveryRecommendationExporter — Export hooks for diagnostics
  - RecoveryRecommendationReconstructor — Replay trace reconstruction

Rules:
  - Read-only export only
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No orchestration, sharding, aggregation
  - No scheduler/task engine
  - No TIA/C#
  - No backend/service/UI
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .distributed_diagnostic_hooks import (
    DiagnosticHooks,
    FailureClassification,
    FailureStage,
    FailureType,
)
from .recovery_recommendation_service import RecoveryRecommendationService


# ============================================================================
# RECOVERY RECOMMENDATION EXPORT RECORD
# ============================================================================


@dataclass
class RecoveryRecommendationExportRecord:
    """Export record for recovery recommendation with correlation context.
    
    Links v75 recovery recommendations to distributed diagnostic trace
    chains via flow_id, request_id, handshake_id, and deadline_id.
    """
    
    export_id: str
    recommendation_id: str
    timestamp: str
    correlation_ids: Dict[str, str]
    recommendation_data: Dict[str, Any]
    
    # Diagnostics integration
    failure_classification: Optional[FailureClassification] = None
    recovery_hint: Optional[str] = None
    confidence_level: Optional[str] = None
    confidence_explanation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize record to dict."""
        return {
            "export_id": self.export_id,
            "recommendation_id": self.recommendation_id,
            "timestamp": self.timestamp,
            "correlation_ids": self.correlation_ids,
            "recommendation_data": self.recommendation_data,
            "failure_classification": (
                self.failure_classification.to_dict()
                if self.failure_classification
                else None
            ),
            "recovery_hint": self.recovery_hint,
            "confidence_level": self.confidence_level,
            "confidence_explanation": self.confidence_explanation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecoveryRecommendationExportRecord":
        """Deserialize record from dict."""
        return cls(
            export_id=data.get("export_id", str(uuid.uuid4())),
            recommendation_id=data.get("recommendation_id", ""),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            correlation_ids=data.get("correlation_ids", {}),
            recommendation_data=data.get("recommendation_data", {}),
            failure_classification=(
                FailureClassification.from_dict(data["failure_classification"])
                if data.get("failure_classification")
                else None
            ),
            recovery_hint=data.get("recovery_hint"),
            confidence_level=data.get("confidence_level"),
            confidence_explanation=data.get("confidence_explanation"),
        )

    def to_json(self, pretty: bool = True) -> str:
        """Serialize to JSON string."""
        if pretty:
            return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ============================================================================
# RECOVERY RECOMMENDATION EXPORTER
# ============================================================================


class RecoveryRecommendationExporter:
    """Export hooks for recovery recommendations into diagnostic trace chains.
    
    Provides read-only export of v75 recommendations with full correlation.
    Does NOT execute or orchestrate recovery actions.
    """
    
    def __init__(self, diagnostic_hooks: DiagnosticHooks):
        """Initialize exporter with diagnostic hooks reference."""
        self._diagnostic_hooks = diagnostic_hooks
        self._export_records: Dict[str, RecoveryRecommendationExportRecord] = {}
        self._recommendation_service = RecoveryRecommendationService()
    
    def export_recommendation(
        self,
        recommendation: Dict[str, Any],
        failure_classification: Optional[FailureClassification] = None,
    ) -> RecoveryRecommendationExportRecord:
        """Export a recovery recommendation to the diagnostic trace chain.
        
        Args:
            recommendation: Recommendation dict from RecoveryRecommendationService
            failure_classification: Optional failure classification for correlation
            
        Returns:
            Export record with correlation context
        """
        export_id = f"rec_export_{uuid.uuid4().hex[:8]}"
        correlation_ids = recommendation.get("correlation_ids", {})
        
        record = RecoveryRecommendationExportRecord(
            export_id=export_id,
            recommendation_id=recommendation.get("recommendation_id", ""),
            timestamp=recommendation.get("generated_at", ""),
            correlation_ids=correlation_ids,
            recommendation_data=recommendation,
            failure_classification=failure_classification,
            recovery_hint=recommendation.get("recovery_hint"),
            confidence_level=recommendation.get("confidence"),
            confidence_explanation=recommendation.get("confidence_explanation"),
        )
        
        self._export_records[export_id] = record
        return record
    
    def export_by_correlation(
        self,
        flow_id: Optional[str] = None,
        request_id: Optional[str] = None,
        handshake_id: Optional[str] = None,
        deadline_id: Optional[str] = None,
    ) -> List[RecoveryRecommendationExportRecord]:
        """Export recommendations filtered by correlation ID.
        
        Args:
            flow_id: Filter by flow ID
            request_id: Filter by request ID
            handshake_id: Filter by handshake ID
            deadline_id: Filter by deadline ID
            
        Returns:
            List of matching export records
        """
        matching: List[RecoveryRecommendationExportRecord] = []
        
        for record in self._export_records.values():
            rec_ids = record.correlation_ids
            
            if flow_id and rec_ids.get("flow_id") == flow_id:
                matching.append(record)
            elif request_id and rec_ids.get("request_id") == request_id:
                matching.append(record)
            elif handshake_id and rec_ids.get("handshake_id") == handshake_id:
                matching.append(record)
            elif deadline_id and rec_ids.get("deadline_id") == deadline_id:
                matching.append(record)
            elif not any([flow_id, request_id, handshake_id, deadline_id]):
                matching.append(record)
        
        return matching
    
    def export_operator_summary(self) -> str:
        """Generate operator-readable summary of all exports.
        
        Returns:
            Multi-line string with recommendation details
        """
        lines: List[str] = []
        lines.append("=== RECOVERY RECOMMENDATION EXPORT SUMMARY ===")
        
        if not self._export_records:
            lines.append("No recovery recommendations exported.")
            return "\n".join(lines)
        
        lines.append(f"Total Recommendations Exported: {len(self._export_records)}")
        lines.append("")
        
        for i, record in enumerate(self._export_records.values(), 1):
            lines.append(f"--- Export #{i} ---")
            lines.append(f"  Recommendation ID: {record.recommendation_id}")
            lines.append(f"  Timestamp: {record.timestamp}")
            
            correlation_parts = []
            if record.correlation_ids.get("flow_id"):
                correlation_parts.append(f"flow_id={record.correlation_ids['flow_id']}")
            if record.correlation_ids.get("request_id"):
                correlation_parts.append(f"request_id={record.correlation_ids['request_id']}")
            if record.correlation_ids.get("handshake_id"):
                correlation_parts.append(f"handshake_id={record.correlation_ids['handshake_id']}")
            if record.correlation_ids.get("deadline_id"):
                correlation_parts.append(f"deadline_id={record.correlation_ids['deadline_id']}")
            
            if correlation_parts:
                lines.append(f"  Correlations: {', '.join(correlation_parts)}")
            
            if record.recovery_hint:
                lines.append(f"  Recovery Hint: {record.recovery_hint}")
            if record.confidence_level:
                lines.append(f"  Confidence: {record.confidence_level}")
            if record.confidence_explanation:
                lines.append(f"  Confidence Explanation: {record.confidence_explanation}")
            lines.append("")
        
        return "\n".join(lines)
    
    def export_machine_readable(self) -> List[Dict[str, Any]]:
        """Export all records as machine-readable JSON-compatible list.
        
        Returns:
            List of export record dictionaries
        """
        return [record.to_dict() for record in self._export_records.values()]
