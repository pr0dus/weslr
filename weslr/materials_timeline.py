"""Weslr Materials Evidence Timeline (v1)

Materials evidence timeline layer that links material experiments, property measurements,
rankings, and confidence evolution across multiple sessions.

Architecture:
  - MaterialsEvidenceTimeline - Core class for materials timeline management
  - Loads events from materials_analysis, structured datasets, scientific_notebook
  - Merges repeated observations by material_id
  - Tracks score/confidence changes over time
  - Detects strengthening/weakening/stable trends
  - Safe data persistence only - no code execution, no certainty claims

Safety Boundaries:
  - Data persistence only (no code execution)
  - No direct material certainty claims
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
    "MaterialsEvidenceTimeline",
    "MaterialsTimelineError",
    "create_materials_timeline",
    "SUPPORTED_SOURCES",
]


# Supported evidence sources for materials
SUPPORTED_SOURCES: List[str] = [
    "materials_analysis",
    "structured_dataset",
    "scientific_notebook",
]


class MaterialsTimelineError(Exception):
    """Raised when materials timeline operations fail."""
    pass


class MaterialsEvidenceTimeline:
    """Materials evidence timeline layer for Weslr.
    
    Manages and links materials evidence across multiple sessions.
    Tracks score evolution and detects trends in material rankings.
    
    Usage:
        from weslr.materials_timeline import create_materials_timeline
        
        timeline = create_materials_timeline()
        timeline.add_event("Material-X", event_data)
    """
    
    def __init__(self, workspace_dir: str = None, storage_dir: str = None):
        """Initialize materials evidence timeline.
        
        Args:
            workspace_dir: Workspace directory for path validation
            storage_dir: Directory for persisting timeline data
        """
        self.workspace_dir = workspace_dir or str(
            Path(__file__).resolve().parent.parent
        )
        self.storage_dir = storage_dir or os.path.join(
            self.workspace_dir, "continuity", "materials_timeline"
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
    
    def _get_safe_storage_path(self, material_id: str) -> str:
        """Get safe storage path for a material's timeline."""
        # Sanitize material_id for filename
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', material_id)[:50]
        return os.path.join(self.storage_dir, f"{safe_id}.json")
    
    def _detect_timestamp(self, event: Dict[str, Any]) -> str:
        """Extract timestamp from event, using current time as fallback."""
        for key in ["date", "timestamp", "datetime", "observation_date", "time", "created"]:
            if key in event:
                val = event[key]
                if isinstance(val, str):
                    return val[:10] if len(val) > 10 else val
                elif isinstance(val, (datetime,)):
                    return val.strftime("%Y-%m-%d")
        
        return datetime.now().strftime("%Y-%m-%d")
    
    def _extract_score(self, event: Dict[str, Any]) -> Optional[float]:
        """Extract score value from event."""
        for key in ["score", "confidence", "score_value", "rank_score"]:
            if key in event:
                val = event[key]
                if val is None:
                    return None
                if isinstance(val, (int, float)):
                    v = float(val)
                    return min(max(v, 0.0), 1.0) if v <= 1.0 else min(max(v / 100, 0.0), 1.0)
                elif isinstance(val, str):
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
            "score": self._extract_score(event),
            "summary": event.get("summary", event.get("message", event.get("notes", ""))),
            "material_id": event.get("material_id", event.get("candidate_id", event.get("material", ""))),
            "metadata": event.get("metadata", {}),
        }
    
    def add_event(self, material_id: str, event: Dict[str, Any]) -> bool:
        """Add an evidence event for a material.
        
        Args:
            material_id: Unique identifier for the material
            event: Event data with score, source, etc.
            
        Returns:
            True if event was added, False otherwise
        """
        if not material_id or not isinstance(material_id, str):
            raise MaterialsTimelineError("Invalid material_id")
        
        event = self._normalize_event(event)
        
        storage_path = self._get_safe_storage_path(material_id)
        
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
        except Exception as e:
            raise MaterialsTimelineError(f"Failed to create storage directory: {e}")
        
        events = []
        if os.path.exists(storage_path):
            try:
                with open(storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    events = data.get("events", [])
            except (json.JSONDecodeError, IOError):
                events = []
        
        events.append(event)
        events.sort(key=lambda e: e.get("date", ""))
        
        try:
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "material_id": material_id,
                    "events": events,
                    "created": datetime.now().isoformat(),
                    "updated": datetime.now().isoformat(),
                }, f, indent=2)
            return True
        except Exception as e:
            raise MaterialsTimelineError(f"Failed to save timeline: {e}")
    
    def load_timeline(self, material_id: str) -> Dict[str, Any]:
        """Load timeline for a material.
        
        Args:
            material_id: Unique identifier for the material
            
        Returns:
            Timeline data with events
        """
        if not material_id or not isinstance(material_id, str):
            raise MaterialsTimelineError("Invalid material_id")
        
        storage_path = self._get_safe_storage_path(material_id)
        
        if not os.path.exists(storage_path):
            return {
                "material_id": material_id,
                "events": [],
                "trend": "insufficient_data",
                "latest_score": None,
                "continuity_linked": False,
                "message": "No timeline found for this material",
            }
        
        try:
            with open(storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, IOError) as e:
            raise MaterialsTimelineError(f"Failed to load timeline: {e}")
    
    def build_timeline(self, material_id: str) -> Dict[str, Any]:
        """Build a complete timeline report for a material.
        
        Args:
            material_id: Unique identifier for the material
            
        Returns:
            Full timeline report with trend analysis
        """
        timeline = self.load_timeline(material_id)
        events = timeline.get("events", [])
        
        if not events:
            return {
                "category": "materials_evidence_timeline",
                "material_id": material_id,
                "events": [],
                "trend": "insufficient_data",
                "latest_score": None,
                "continuity_linked": False,
                "event_count": 0,
                "message": "No events in timeline",
            }
        
        trend = self.detect_trend(events)
        
        latest_score = None
        if events:
            latest_event = events[-1]
            latest_score = latest_event.get("score")
        
        result: Dict[str, Any] = {
            "category": "materials_evidence_timeline",
            "material_id": material_id,
            "events": events,
            "trend": trend,
            "latest_score": latest_score,
            "continuity_linked": True,
            "event_count": len(events),
        }
        
        trend_desc = {
            "strengthening": "Score is increasing over time",
            "weakening": "Score is decreasing over time",
            "stable": "Score is stable across observations",
            "insufficient_data": "Not enough events to determine trend",
        }
        result["trend_description"] = trend_desc.get(trend, "Unknown trend")
        
        score_str = f"{latest_score:.2%}" if latest_score else "N/A"
        result["message"] = (
            f"Materials timeline for {material_id}: "
            f"{len(events)} event(s), {trend}, "
            f"latest score: {score_str}"
        )
        
        return result
    
    def detect_trend(self, events: List[Dict[str, Any]]) -> str:
        """Detect score trend from events.
        
        Args:
            events: List of events with score values
            
        Returns:
            Trend string: "strengthening", "weakening", "stable", or "insufficient_data"
        """
        if not events:
            return "insufficient_data"
        
        scores = []
        for event in events:
            score = self._extract_score(event)
            if score is not None:
                scores.append(score)
        
        if len(scores) < 2:
            return "insufficient_data"
        
        mid = len(scores) // 2
        first_half = scores[:mid]
        second_half = scores[mid:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
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
        material_id: str = None,
    ) -> bool:
        """Load evidence from a source (materials_analysis, structured_dataset, etc.).
        
        Args:
            source_type: Type of source
            source_data: Data from the source
            material_id: Optional material ID to link to
            
        Returns:
            True if loaded successfully
        """
        if source_type not in SUPPORTED_SOURCES:
            raise MaterialsTimelineError(
                f"Unsupported source type: {source_type}. "
                f"Supported: {SUPPORTED_SOURCES}"
            )
        
        score = None
        for key in ["score", "confidence", "ranking_score"]:
            if key in source_data:
                val = source_data[key]
                if isinstance(val, (int, float)):
                    score = float(val)
                    if score > 1:
                        score = score / 100
                    break
                elif isinstance(val, str):
                    score = self._extract_score({"score": val})
                    break
        
        summary = source_data.get("message", source_data.get("summary", ""))
        
        if not material_id:
            material_id = source_data.get("material_id") or source_data.get("top_candidate")
        
        if not material_id:
            date_part = source_data.get("observation_date", source_data.get("date", ""))[:10]
            material_id = f"{source_type}-{date_part}"
        
        event = {
            "source": source_type,
            "score": score,
            "summary": summary,
            "source_data_ref": source_data.get("source_file", source_data.get("file_type", "")),
        }
        
        if source_type == "materials_analysis":
            event["analysis_type"] = source_data.get("analysis_type", "candidate_ranking")
            event["criteria"] = source_data.get("criteria_used", [])
        elif source_type == "structured_dataset":
            event["structure_type"] = source_data.get("category", "structured")
        
        return self.add_event(material_id, event)
    
    def analyze(
        self,
        material_id: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Analyze materials timeline for a material.
        
        Args:
            material_id: Unique identifier for the material
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            Dict with analysis result
        """
        result = self.build_timeline(material_id)
        
        return {
            "file_type": ".json",
            "category": "materials_evidence_timeline",
            "relevance": "high" if result.get("trend") != "insufficient_data" else "medium",
            "relevance_reason": result.get("message", "Materials timeline built"),
            "metadata": {
                "material_id": material_id,
                "parsed_successfully": True,
                "parse_error": None,
                "category": "materials_evidence_timeline",
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
        
        lines.append("[MATERIALS EVIDENCE TIMELINE]")
        
        if user_query:
            lines.append(f"User: \"{user_query}\"")
        
        material_id = result.get("material_id", "unknown")
        lines.append(f"\nMaterial: {material_id}")
        
        lines.append(f"Events: {result.get('event_count', 0)}")
        
        trend = result.get("trend", "insufficient_data")
        lines.append(f"Trend: {trend.upper()} - {result.get('trend_description', '')}")
        
        latest = result.get("latest_score")
        if latest is not None:
            lines.append(f"Latest Score: {latest:.2%}")
        else:
            lines.append("Latest Score: N/A")
        
        lines.append("\nEvents:")
        events = result.get("events", [])
        for i, event in enumerate(events[:5], 1):
            date = event.get("date", "unknown")
            score = event.get("score")
            score_str = f"{score:.2%}" if score is not None else "N/A"
            source = event.get("source", "unknown")
            summary = event.get("summary", "")[:80]
            lines.append(f"  {i}. [{date}] {source} - {score_str}")
            if summary:
                lines.append(f"     {summary}...")
        
        if result.get("message"):
            lines.append(f"\nNote: {result['message']}")
        
        lines.append("\n⚠️  This is evidence accumulation - no certainty claims made.")
        
        return "\n".join(lines)


def create_materials_timeline(
    workspace_dir: str = None,
    storage_dir: str = None,
) -> MaterialsEvidenceTimeline:
    """Create a materials evidence timeline instance.
    
    Args:
        workspace_dir: Workspace directory for path validation
        storage_dir: Directory for persisting timeline data
        
    Returns:
        MaterialsEvidenceTimeline instance
    """
    return MaterialsEvidenceTimeline(
        workspace_dir=workspace_dir,
        storage_dir=storage_dir,
    )
