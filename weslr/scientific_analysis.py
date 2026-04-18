"""Weslr Scientific Dataset Analysis (v1)

Context-aware scientific dataset analysis for astronomy and exoplanet candidate detection.
Produces transit light curve analysis with candidate detection, not certainty claims.

Architecture:
  - ScientificDatasetAnalyzer - Core class for scientific dataset analysis
  - Supported types: numeric CSV/JSON/TXT/TSV
  - Safe numeric only - no image analysis, no direct planet certainty claims

Safety Boundaries:
  - Numeric datasets only
  - No image analysis yet
  - No direct planet certainty claims
  - Output must say candidate detection only
  - Path traversal protection
  - Max file size limit (10MB)
  - Max output size limit (50KB)
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .context import ContextLabel


__all__ = [
    "ScientificDatasetAnalyzer",
    "ScientificAnalysisError",
    "create_scientific_analyzer",
    "supported_scientific_extensions",
]


# Supported scientific data file extensions
supported_scientific_extensions: List[str] = [
    ".csv",
    ".json",
    ".txt",
    ".tsv",
]


class ScientificAnalysisError(Exception):
    """Raised when scientific dataset analysis fails."""
    pass


class ScientificDatasetAnalyzer:
    """Context-aware scientific dataset analysis for Weslr.
    
    Focus: Transit light curve analysis for exoplanet candidate detection.
    
    Usage:
        from weslr.scientific_analysis import create_scientific_analyzer
        
        analyzer = create_scientific_analyzer()
        result = analyzer.detect_transit_candidates("/path/to/light_curve.csv")
    """
    
    def __init__(self, workspace_dir: str = None):
        """Initialize scientific dataset analyzer.
        
        Args:
            workspace_dir: Workspace directory for path validation
        """
        self.workspace_dir = workspace_dir or str(
            Path(__file__).resolve().parent.parent
        )
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_output_chars = 50000  # 50KB
        # Transit detection thresholds
        self.min_dip_depth = 0.001  # 0.1% brightness dip
        self.min_dip_count = 2  # Minimum repeating dips for period estimate
        self.max_dip_width = 0.1  # Max dip width in normalized time units
    
    def _is_safe_path(self, filepath: str, workspace_dir: str) -> bool:
        """Check if filepath is within workspace directory."""
        try:
            workspace = Path(workspace_dir).resolve()
            path = Path(filepath).resolve()
            return str(path).startswith(str(workspace) + os.sep) or path == workspace
        except Exception:
            return False
    
    def _get_file_extension(self, filepath: str) -> str:
        """Get file extension."""
        return Path(filepath).suffix.lower()
    
    def _is_supported_type(self, ext: str) -> bool:
        """Check if extension is supported."""
        return ext in supported_scientific_extensions
    
    def _load_numeric_data(self, filepath: str) -> List[List[float]]:
        """Load numeric data from file.
        
        Returns list of rows, each row is a list of numeric values.
        """
        ext = self._get_file_extension(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            raise ScientificAnalysisError(f"Failed to read file: {e}")
        
        # Truncate if too large
        if len(content) > self.max_output_chars:
            content = content[:self.max_output_chars] + "\n... [truncated]"
        
        data_rows: List[List[float]] = []
        
        try:
            if ext == ".csv":
                reader = csv.reader(io.StringIO(content))
                for row in reader:
                    numeric_row = self._parse_numeric_row(row)
                    if numeric_row:
                        data_rows.append(numeric_row)
            elif ext == ".tsv":
                reader = csv.reader(io.StringIO(content), delimiter='\t')
                for row in reader:
                    numeric_row = self._parse_numeric_row(row)
                    if numeric_row:
                        data_rows.append(numeric_row)
            elif ext == ".json":
                parsed = json.loads(content)
                data_rows = self._extract_numeric_rows_from_json(parsed)
            elif ext in (".txt",):
                # Try to parse as whitespace-delimited or columnar data
                for line in content.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Try to split on whitespace or common delimiters
                    parts = re.split(r'[,\s]+', line)
                    numeric_row = self._parse_numeric_row(parts)
                    if numeric_row:
                        data_rows.append(numeric_row)
        except Exception as e:
            raise ScientificAnalysisError(f"Failed to parse numeric data: {e}")
        
        return data_rows
    
    def _parse_numeric_row(self, row: List[str]) -> Optional[List[float]]:
        """Parse a row of strings to floats, skip if non-numeric found."""
        try:
            floats = []
            for val in row:
                val = val.strip()
                if not val:
                    continue
                # Skip common header indicators
                if val.lower() in ('nan', 'inf', 'null', 'none', 'na', 'n/a', '-'):
                    continue
                floats.append(float(val))
            return floats if floats else None
        except (ValueError, TypeError):
            return None
    
    def _extract_numeric_rows_from_json(self, data: Any) -> List[List[float]]:
        """Extract numeric rows from JSON data."""
        rows: List[List[float]] = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, list):
                    numeric_row = self._parse_numeric_row([str(v) for v in item])
                    if numeric_row:
                        rows.append(numeric_row)
                elif isinstance(item, dict):
                    # Try to extract numeric values from dict
                    numeric_values = []
                    for v in item.values():
                        if isinstance(v, (int, float)):
                            numeric_values.append(v)
                        elif isinstance(v, str):
                            try:
                                numeric_values.append(float(v))
                            except ValueError:
                                pass
                    if len(numeric_values) >= 1:
                        rows.append(numeric_values)
        elif isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    numeric_row = self._parse_numeric_row([str(x) for x in v])
                    if numeric_row:
                        rows.append(numeric_row)
        
        return rows
    
    def _extract_light_curve_data(self, data_rows: List[List[float]]) -> Tuple[List[float], List[float]]:
        """Extract time and brightness columns from data rows.
        
        Assumes first column is time, second is brightness/flux.
        """
        if not data_rows:
            return [], []
        
        # Find rows with at least 2 numeric columns
        valid_rows = [row for row in data_rows if len(row) >= 2]
        if not valid_rows:
            return [], []
        
        # Take first two columns as time and brightness
        times = [row[0] for row in valid_rows]
        brightness = [row[1] for row in valid_rows]
        
        return times, brightness
    
    def _normalize_brightness(self, brightness: List[float]) -> List[float]:
        """Normalize brightness to 0-1 range."""
        if not brightness:
            return []
        
        min_val = min(brightness)
        max_val = max(brightness)
        
        if max_val - min_val < 1e-10:
            # Flat light curve
            return [0.5] * len(brightness)
        
        return [(b - min_val) / (max_val - min_val) for b in brightness]
    
    def _find_brightness_dips(
        self,
        times: List[float],
        brightness: List[float],
        normalized: bool = False,
    ) -> List[Dict[str, float]]:
        """Find brightness dips in light curve.
        
        Returns list of dip events with start time, end time, depth, and duration.
        """
        if len(times) < 3 or len(brightness) < 3:
            return []
        
        if not normalized:
            brightness = self._normalize_brightness(brightness)
        
        dips = []
        n = len(brightness)
        
        # Find local minima that exceed minimum dip threshold
        i = 1
        while i < n - 1:
            # Look for a dip (local minimum)
            if (brightness[i] < brightness[i-1] and 
                brightness[i] < brightness[i+1] and
                brightness[i] < (1.0 - self.min_dip_depth)):
                
                # Find the start of the dip
                start_idx = i
                while start_idx > 0 and brightness[start_idx] < brightness[start_idx - 1]:
                    start_idx -= 1
                
                # Find the end of the dip
                end_idx = i
                while end_idx < n - 1 and brightness[end_idx] < brightness[end_idx + 1]:
                    end_idx += 1
                
                # Calculate dip properties
                min_brightness = min(brightness[start_idx:end_idx+1])
                max_brightness = max(brightness[start_idx:end_idx+1])
                depth = max_brightness - min_brightness if max_brightness > min_brightness else 0
                
                dip_duration = times[end_idx] - times[start_idx] if end_idx > start_idx else 0
                
                # Only record if depth exceeds threshold
                if depth >= self.min_dip_depth:
                    dips.append({
                        "start_time": times[start_idx],
                        "end_time": times[end_idx],
                        "min_brightness": min_brightness,
                        "max_brightness": max_brightness,
                        "depth": depth,
                        "duration": dip_duration,
                        "center_time": times[i],
                    })
                
                # Move past this dip
                i = end_idx + 1
            else:
                i += 1
        
        return dips
    
    def _estimate_period_from_dips(self, dips: List[Dict[str, float]]) -> Optional[float]:
        """Estimate orbital period from repeating dip events.
        
        Uses simple spacing analysis between consecutive dips.
        """
        if len(dips) < self.min_dip_count:
            return None
        
        # Calculate intervals between dip centers
        intervals = []
        for i in range(1, len(dips)):
            interval = dips[i]["center_time"] - dips[i-1]["center_time"]
            if interval > 0:
                intervals.append(interval)
        
        if not intervals:
            return None
        
        # Return mean interval as period estimate
        return sum(intervals) / len(intervals)
    
    def _assess_confidence(
        self,
        dips: List[Dict[str, float]],
        period_estimate: Optional[float],
        times: List[float],
        brightness: List[float],
    ) -> float:
        """Assess confidence in transit candidate detection.
        
        Returns value between 0 and 1.
        """
        if not dips:
            return 0.0
        
        confidence = 0.0
        
        # Base confidence from dip count
        dip_score = min(len(dips) / 10, 1.0) * 0.3  # Up to 30% from dip count
        
        # Confidence from dip regularity (period consistency)
        period_score = 0.0
        if period_estimate and len(dips) >= 2:
            intervals = []
            for i in range(1, len(dips)):
                interval = dips[i]["center_time"] - dips[i-1]["center_time"]
                if interval > 0:
                    intervals.append(interval)
            
            if intervals:
                mean_interval = sum(intervals) / len(intervals)
                variance = sum((i - mean_interval) ** 2 for i in intervals) / len(intervals)
                std_dev = variance ** 0.5
                # Lower std_dev = more regular = higher confidence
                regularity = 1.0 - min(std_dev / mean_interval, 1.0)
                period_score = regularity * 0.3  # Up to 30%
        
        # Confidence from dip depth consistency
        depth_score = 0.0
        if len(dips) >= 2:
            depths = [d["depth"] for d in dips]
            mean_depth = sum(depths) / len(depths)
            variance = sum((d - mean_depth) ** 2 for d in depths) / len(depths)
            std_dev = variance ** 0.5
            # Lower depth variance = more consistent = higher confidence
            consistency = 1.0 - min(std_dev / mean_depth, 1.0) if mean_depth > 0 else 0
            depth_score = consistency * 0.2  # Up to 20%
        
        # Minimum depth contribution
        depth_contrib = 0.2 * min(max(dips[-1]["depth"], self.min_dip_depth * 2) / (self.min_dip_depth * 10), 1.0)
        
        confidence = dip_score + period_score + depth_score + depth_contrib
        return min(confidence, 1.0)
    
    def detect_transit_candidates(
        self,
        filepath: str,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Detect transit light curve candidates in scientific dataset.
        
        Args:
            filepath: Path to file (must be within workspace)
            query: Optional user query for context
            
        Returns:
            Dict with analysis result following strict output format:
            {
                "category": "scientific_dataset",
                "candidate_detected": bool,
                "period_estimate": float | None,
                "dip_count": int,
                "confidence": float,
                "analysis_type": "transit_detection"
            }
        """
        # Validate path
        if not self._is_safe_path(filepath, self.workspace_dir):
            raise ScientificAnalysisError(
                f"Path traversal attempt: {filepath} is outside workspace"
            )
        
        # Check file exists
        if not os.path.exists(filepath):
            raise ScientificAnalysisError(f"File not found: {filepath}")
        
        # Check it's a file, not a directory
        if os.path.isdir(filepath):
            raise ScientificAnalysisError(f"Is a directory, not a file: {filepath}")
        
        # Check file size
        try:
            size = os.path.getsize(filepath)
            if size > self.max_file_size:
                raise ScientificAnalysisError(
                    f"File too large: {size} bytes (max {self.max_file_size})"
                )
        except Exception as e:
            raise ScientificAnalysisError(f"Failed to check file size: {e}")
        
        # Load and parse data
        data_rows = self._load_numeric_data(filepath)
        
        if not data_rows:
            return {
                "category": "scientific_dataset",
                "candidate_detected": False,
                "period_estimate": None,
                "dip_count": 0,
                "confidence": 0.0,
                "analysis_type": "transit_detection",
                "message": "No numeric data found in file",
            }
        
        # Extract light curve
        times, brightness = self._extract_light_curve_data(data_rows)
        
        if len(times) < 3 or len(brightness) < 3:
            return {
                "category": "scientific_dataset",
                "candidate_detected": False,
                "period_estimate": None,
                "dip_count": 0,
                "confidence": 0.0,
                "analysis_type": "transit_detection",
                "message": "Insufficient data points for analysis",
            }
        
        # Normalize brightness
        normalized_brightness = self._normalize_brightness(brightness)
        
        # Find dips
        dips = self._find_brightness_dips(times, normalized_brightness, normalized=True)
        
        # Estimate period if we have enough dips
        period_estimate = self._estimate_period_from_dips(dips)
        
        # Assess confidence
        confidence = self._assess_confidence(dips, period_estimate, times, brightness)
        
        # Build result following strict output format
        # NOTE: candidate_detected is True if we found dips meeting minimum threshold
        # We DO NOT claim planet certainty - only candidate detection
        candidate_detected = len(dips) >= self.min_dip_count
        
        result: Dict[str, Any] = {
            "category": "scientific_dataset",
            "candidate_detected": candidate_detected,
            "period_estimate": period_estimate,
            "dip_count": len(dips),
            "confidence": confidence,
            "analysis_type": "transit_detection",
        }
        
        # Add details for transparency
        if dips:
            result["dip_details"] = [
                {
                    "time": d["center_time"],
                    "depth": d["depth"],
                    "duration": d["duration"],
                }
                for d in dips[:5]  # Limit to first 5 dips
            ]
        
        if period_estimate:
            result["period_estimate_description"] = (
                f"Estimated period from {len(dips)} dip events: "
                f"{period_estimate:.6f} time units"
            )
        
        if not candidate_detected:
            result["message"] = (
                "No transit candidate detected. "
                f"Found {len(dips)} dip events (minimum {self.min_dip_count} required)."
            )
        else:
            result["message"] = (
                f"Transit candidate detected with {len(dips)} dip events. "
                "Note: This is a candidate detection only - not a confirmed planet detection."
            )
        
        return result
    
    def analyze(
        self,
        filepath: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Analyze scientific dataset file in context.
        
        This is the main entry point for file_router integration.
        
        Args:
            filepath: Path to file (must be within workspace)
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            Dict with analysis result matching StructuredData output format
        """
        result = self.detect_transit_candidates(filepath, user_query)
        
        # Convert to RouterResult-compatible format
        return {
            "file_type": self._get_file_extension(filepath),
            "category": "scientific_dataset",
            "relevance": "high" if result["candidate_detected"] else "medium",
            "relevance_reason": result.get("message", "Scientific analysis complete"),
            "metadata": {
                "source_file": Path(filepath).name,
                "parsed_successfully": True,
                "parse_error": None,
                "category": "scientific_dataset",
            },
            "safety": {
                "injection_risk": "low",
                "content_type": "scientific_data",
            },
            "structured_output": self._format_scientific_output(result, user_query),
            "parsed_data": result,
        }
    
    def _format_scientific_output(
        self,
        result: Dict[str, Any],
        user_query: str,
    ) -> str:
        """Format scientific analysis result for chat output."""
        parts = []
        
        # Header
        parts.append("[SCIENTIFIC ANALYSIS - Transit Detection]")
        
        # Query reference
        if user_query:
            parts.append(f"User: \"{user_query}\"")
        
        # Basic result
        if result["candidate_detected"]:
            parts.append(f"\nTransit candidate DETECTED")
        else:
            parts.append(f"\nNo transit candidate detected")
        
        parts.append(f"\nAnalysis Type: {result.get('analysis_type', 'transit_detection')}")
        parts.append(f"Dip Events Found: {result.get('dip_count', 0)}")
        parts.append(f"Confidence: {result.get('confidence', 0):.2%}")
        
        # Period estimate
        if result.get("period_estimate"):
            parts.append(f"Period Estimate: {result['period_estimate']:.6f} time units")
            if result.get("period_estimate_description"):
                parts.append(result["period_estimate_description"])
        
        # Message
        if result.get("message"):
            parts.append(f"\nNote: {result['message']}")
        
        # Dip details
        if result.get("dip_details"):
            parts.append("\nDip Events:")
            for i, dip in enumerate(result["dip_details"][:5], 1):
                parts.append(
                    f"  {i}. Time: {dip['time']:.4f}, "
                    f"Depth: {dip['depth']:.4f}, "
                    f"Duration: {dip['duration']:.4f}"
                )
        
        # Safety disclaimer
        parts.append("\n⚠️  This is a candidate detection only - not a confirmed planet detection.")
        
        return "\n".join(parts)


def create_scientific_analyzer(workspace_dir: str = None) -> ScientificDatasetAnalyzer:
    """Create a scientific dataset analyzer instance.
    
    Args:
        workspace_dir: Workspace directory for path validation
        
    Returns:
        ScientificDatasetAnalyzer instance
    """
    return ScientificDatasetAnalyzer(workspace_dir=workspace_dir)
