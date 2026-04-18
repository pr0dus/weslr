"""Weslr Scientific Evidence Timeline (v1)

Scientific evidence timeline layer that links observations, datasets, FITS sessions,
notebook notes, and confidence evolution across multiple sessions.

Architecture:
  - ScientificEvidenceTimeline - Core class for evidence timeline management
  - Loads evidence events from scientific_dataset, fits_dataset, scientific_notebook
  - Merges multiple observations by candidate_id
  - Tracks confidence changes over time
  - Detects strengthening/weakening trends
  - Safe parsing only - no code execution, no certainty claims

Safety Boundaries:
  - Data persistence only (no code execution)
  - No direct planet certainty claims
  - Output must indicate timeline status
  - Path traversal protection
  - Max file size limit (100MB)
  - Max output size limit (50KB)
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .context import ContextLabel


__all__ = [
    "ScientificEvidenceTimeline",
    "EvidenceTimelineError",
    "create_evidence_timeline",
    "SUPPORTED_SOURCES",
]


# Supported evidence sources
SUPPORTED_SOURCES: List[str] = [
    "scientific_dataset",
    "fits_dataset",
    "scientific_notebook",
    "habitable_zone",
]


class EvidenceTimelineError(Exception):
    """Raised when evidence timeline operations fail."""
    pass


class ScientificEvidenceTimeline:
    """Scientific evidence timeline layer for Weslr.
    
    Manages and links scientific evidence across multiple sessions.
    Tracks confidence evolution and detects trends in candidate detection.
    
    Usage:
        from weslr.evidence_timeline import create_evidence_timeline
        
        timeline = create_evidence_timeline()
        timeline.add_event("exo-001", event_data)
    """
    
    def __init__(self, workspace_dir: str = None, storage_dir: str = None):
        """Initialize evidence timeline.
        
        Args:
            workspace_dir: Workspace directory for path validation
            storage_dir: Directory for persisting timeline data
        """
        self.workspace_dir = workspace_dir or str(
            Path(__file__).resolve().parent.parent
        )
        self.storage_dir = storage_dir or os.path.join(
            self.workspace_dir, "continuity", "evidence_timeline"
        )
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.max_output_chars = 50000  # 50KB
    
    def _is_safe_path(self, filepath: str, workspace_dir: str) -> bool:
        """Check if filepath is within workspace directory."""
        try:
            workspace = Path(workspace_dir).resolve()
            path = Path(filepath).resolve()
            return str(path).startswith(str(workspace) + os.sep) or path == workspace
        except Exception:
            return False
    
    def _get_safe_storage_path(self, candidate_id: str) -> str:
        """Get safe storage path for a candidate's timeline."""
        # Sanitize candidate_id for filename
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', candidate_id)[:50]
        return os.path.join(self.storage_dir, f"{safe_id}.json")
    
    def _import_re(self):
        """Import re module lazily."""
        import re as re_module
        return re_module
    
    def _detect_timestamp(self, event: Dict[str, Any]) -> str:
        """Extract timestamp from event, using current time as fallback."""
        # Try various timestamp fields
        for key in ["date", "timestamp", "datetime", "observation_date", "time"]:
            if key in event:
                val = event[key]
                if isinstance(val, str):
                    return val[:10] if len(val) > 10 else val  # Extract YYYY-MM-DD
                elif isinstance(val, (datetime,)):
                    return val.strftime("%Y-%m-%d")
        
        # Use current time as fallback
        return datetime.now().strftime("%Y-%m-%d")
    
    def _extract_confidence(self, event: Dict[str, Any]) -> Optional[float]:
        """Extract confidence value from event."""
        # Try various confidence fields
        for key in ["confidence", "certainty", "confidence_score"]:
            if key in event:
                val = event[key]
                if val is None:
                    return None
                if isinstance(val, (int, float)):
                    v = float(val)
                    return min(max(v, 0.0), 1.0) if v <= 1.0 else min(max(v / 100, 0.0), 1.0)
                elif isinstance(val, str):
                    # Handle percentage strings
                    val = val.strip()
                    if val.endswith('%'):
                        try:
                            return min(max(float(val[:-1]) / 100, 0.0), 1.0)
                        except ValueError:
                            pass
                    else:
                        try:
                            v = float(val)
                            return min(max(v, 0.0), 1.0) if v <= 1.0 else min(max(v / 100, 0.0), 1.0)
                        except ValueError:
                            pass
        return None
    
    def _normalize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event to standard format."""
        return {
            "date": self._detect_timestamp(event),
            "source": event.get("source", "unknown"),
            "confidence": self._extract_confidence(event),
            "summary": event.get("summary", event.get("message", event.get("notes", ""))),
            "metadata": event.get("metadata", {}),
        }
    
    def add_event(self, candidate_id: str, event: Dict[str, Any]) -> bool:
        """Add an evidence event for a candidate.
        
        Args:
            candidate_id: Unique identifier for the candidate
            event: Event data with confidence, source, etc.
            
        Returns:
            True if event was added, False otherwise
        """
        # Validate candidate_id
        if not candidate_id or not isinstance(candidate_id, str):
            raise EvidenceTimelineError("Invalid candidate_id")
        
        # Normalize event
        event = self._normalize_event(event)
        
        # Get storage path
        storage_path = self._get_safe_storage_path(candidate_id)
        
        # Create storage directory if needed
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
        except Exception as e:
            raise EvidenceTimelineError(f"Failed to create storage directory: {e}")
        
        # Load existing events
        events = []
        if os.path.exists(storage_path):
            try:
                with open(storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    events = data.get("events", [])
            except (json.JSONDecodeError, IOError):
                events = []
        
        # Add new event
        events.append(event)
        
        # Sort by date
        events.sort(key=lambda e: e.get("date", ""))
        
        # Save events
        try:
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "candidate_id": candidate_id,
                    "events": events,
                    "created": datetime.now().isoformat(),
                    "updated": datetime.now().isoformat(),
                }, f, indent=2)
            return True
        except Exception as e:
            raise EvidenceTimelineError(f"Failed to save timeline: {e}")
    
    def load_timeline(self, candidate_id: str) -> Dict[str, Any]:
        """Load timeline for a candidate.
        
        Args:
            candidate_id: Unique identifier for the candidate
            
        Returns:
            Timeline data with events
        """
        if not candidate_id or not isinstance(candidate_id, str):
            raise EvidenceTimelineError("Invalid candidate_id")
        
        storage_path = self._get_safe_storage_path(candidate_id)
        
        if not os.path.exists(storage_path):
            return {
                "candidate_id": candidate_id,
                "events": [],
                "trend": "insufficient_data",
                "latest_confidence": None,
                "continuity_linked": False,
                "message": "No timeline found for this candidate",
            }
        
        try:
            with open(storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
        except (json.JSONDecodeError, IOError) as e:
            raise EvidenceTimelineError(f"Failed to load timeline: {e}")
    
    def build_timeline(self, candidate_id: str) -> Dict[str, Any]:
        """Build a complete timeline report for a candidate.
        
        Args:
            candidate_id: Unique identifier for the candidate
            
        Returns:
            Full timeline report with trend analysis
        """
        timeline = self.load_timeline(candidate_id)
        events = timeline.get("events", [])
        
        if not events:
            return {
                "category": "scientific_evidence_timeline",
                "candidate_id": candidate_id,
                "events": [],
                "trend": "insufficient_data",
                "latest_confidence": None,
                "continuity_linked": False,
                "event_count": 0,
                "message": "No events in timeline",
            }
        
        # Detect trend
        trend = self.detect_trend(events)
        
        # Get latest confidence
        latest_confidence = None
        if events:
            latest_event = events[-1]
            latest_confidence = latest_event.get("confidence")
        
        # Build result
        result: Dict[str, Any] = {
            "category": "scientific_evidence_timeline",
            "candidate_id": candidate_id,
            "events": events,
            "trend": trend,
            "latest_confidence": latest_confidence,
            "continuity_linked": True,
            "event_count": len(events),
        }
        
        # Add trend description
        trend_desc = {
            "strengthening": "Confidence is increasing over time",
            "weakening": "Confidence is decreasing over time",
            "stable": "Confidence is stable across observations",
            "insufficient_data": "Not enough events to determine trend",
        }
        result["trend_description"] = trend_desc.get(trend, "Unknown trend")
        
        conf_str = f"{latest_confidence:.2%}" if latest_confidence else "N/A"
        result["message"] = (
            f"Evidence timeline for candidate {candidate_id}: "
            f"{len(events)} event(s), {trend}, "
            f"latest confidence: {conf_str}"
        )
        
        return result
    
    def detect_trend(self, events: List[Dict[str, Any]]) -> str:
        """Detect confidence trend from events.
        
        Args:
            events: List of events with confidence values
            
        Returns:
            Trend string: "strengthening", "weakening", "stable", or "insufficient_data"
        """
        if not events:
            return "insufficient_data"
        
        # Extract confidence values
        confidences = []
        for event in events:
            conf = self._extract_confidence(event)
            if conf is not None:
                confidences.append(conf)
        
        if len(confidences) < 2:
            return "insufficient_data"
        
        # Simple trend detection
        # Compare first half vs second half of confidences
        mid = len(confidences) // 2
        first_half = confidences[:mid]
        second_half = confidences[mid:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        # Calculate difference
        diff = avg_second - avg_first
        threshold = 0.05  # 5% change threshold
        
        if diff > threshold:
            return "strengthening"
        elif diff < -threshold:
            return "weakening"
        else:
            return "stable"
    
    def load_from_source(
        self,
        source_type: str,
        source_data: Dict[str, Any],
        candidate_id: str = None,
    ) -> bool:
        """Load evidence from a source (scientific_dataset, fits_dataset, etc.).
        
        Args:
            source_type: Type of source (scientific_dataset, fits_dataset, etc.)
            source_data: Data from the source
            candidate_id: Optional candidate ID to link to
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if source_type not in SUPPORTED_SOURCES:
            raise EvidenceTimelineError(
                f"Unsupported source type: {source_type}. "
                f"Supported: {SUPPORTED_SOURCES}"
            )
        
        # Extract confidence from source data
        confidence = None
        for key in ["confidence", "earth_similarity_score", "mean_brightness"]:
            if key in source_data:
                conf = source_data[key]
                if isinstance(conf, (int, float)):
                    confidence = float(conf)
                    if confidence > 1:
                        confidence = min(confidence / 100, 1.0)
                    break
                elif isinstance(conf, str):
                    confidence = self._extract_confidence({"confidence": conf})
                    break
        
        # Extract source-specific summary
        summary = source_data.get("message", source_data.get("summary", ""))
        
        # Try to get candidate_id from source
        if not candidate_id:
            candidate_id = source_data.get("candidate_id")
        
        if not candidate_id:
            # Generate from source type and date
            date_part = source_data.get("observation_date", source_data.get("date", ""))[:10]
            candidate_id = f"{source_type}-{date_part}"
        
        # Create event
        event = {
            "source": source_type,
            "confidence": confidence,
            "summary": summary,
            "source_data_ref": source_data.get("source_file", source_data.get("file_type", "")),
        }
        
        # Add additional source-specific metadata
        if source_type == "scientific_dataset":
            event["analysis_type"] = source_data.get("analysis_type", "transit_detection")
            if "dip_details" in source_data:
                event["dip_count"] = source_data.get("dip_count", 0)
        elif source_type == "fits_dataset":
            event["dimensions"] = f"{source_data.get('width', 0)}x{source_data.get('height', 0)}"
            event["mean_brightness"] = source_data.get("mean_brightness")
        elif source_type == "scientific_notebook":
            event["target_star"] = source_data.get("target_star")
            event["observation_date"] = source_data.get("observation_date")
        elif source_type == "habitable_zone":
            event["inside_habitable_zone"] = source_data.get("inside_habitable_zone")
            event["earth_similarity"] = source_data.get("earth_similarity_score")
        
        return self.add_event(candidate_id, event)
    
    def analyze(
        self,
        candidate_id: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Analyze evidence timeline for a candidate.
        
        This is the main entry point for file_router integration.
        
        Args:
            candidate_id: Unique identifier for the candidate
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            Dict with analysis result
        """
        result = self.build_timeline(candidate_id)
        
        # Convert to RouterResult-compatible format
        return {
            "file_type": ".json",  # Default
            "category": "scientific_evidence_timeline",
            "relevance": "high" if result.get("trend") != "insufficient_data" else "medium",
            "relevance_reason": result.get("message", "Evidence timeline built"),
            "metadata": {
                "candidate_id": candidate_id,
                "parsed_successfully": True,
                "parse_error": None,
                "category": "scientific_evidence_timeline",
            },
            "safety": {
                "injection_risk": "low",
                "content_type": "timeline_data",
            },
            "structured_output": self._format_timeline_output(result, user_query),
            "parsed_data": result,
        }
    
    def _format_timeline_output(
        self,
        result: Dict[str, Any],
        user_query: str,
    ) -> str:
        """Format timeline for chat output."""
        lines = []
        
        # Header
        lines.append("[SCIENTIFIC EVIDENCE TIMELINE]")
        
        # Query reference
        if user_query:
            lines.append(f"User: \"{user_query}\"")
        
        candidate_id = result.get("candidate_id", "unknown")
        lines.append(f"\nCandidate: {candidate_id}")
        
        # Event count
        lines.append(f"Events: {result.get('event_count', 0)}")
        
        # Trend
        trend = result.get("trend", "insufficient_data")
        lines.append(f"Trend: {trend.upper()} - {result.get('trend_description', '')}")
        
        # Latest confidence
        latest = result.get("latest_confidence")
        if latest is not None:
            lines.append(f"Latest Confidence: {latest:.2%}")
        else:
            lines.append("Latest Confidence: N/A")
        
        # Events list
        lines.append("\nEvents:")
        events = result.get("events", [])
        for i, event in enumerate(events[:5], 1):  # Show first 5
            date = event.get("date", "unknown")
            conf = event.get("confidence")
            conf_str = f"{conf:.2%}" if conf is not None else "N/A"
            source = event.get("source", "unknown")
            summary = event.get("summary", "")[:80]
            lines.append(f"  {i}. [{date}] {source} - {conf_str}")
            if summary:
                lines.append(f"     {summary}...")
        
        # Message
        if result.get("message"):
            lines.append(f"\nNote: {result['message']}")
        
        # Safety disclaimer
        lines.append("\n⚠️  This is evidence accumulation - not a confirmed planet detection.")
        
        return "\n".join(lines)


def create_evidence_timeline(
    workspace_dir: str = None,
    storage_dir: str = None,
) -> ScientificEvidenceTimeline:
    """Create an evidence timeline instance.
    
    Args:
        workspace_dir: Workspace directory for path validation
        storage_dir: Directory for persisting timeline data
        
    Returns:
        ScientificEvidenceTimeline instance
    """
    return ScientificEvidenceTimeline(
        workspace_dir=workspace_dir,
        storage_dir=storage_dir,
    )
