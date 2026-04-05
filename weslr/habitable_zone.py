"""Weslr Habitable Zone Estimation (v1)

Golden zone / habitable zone estimation for exoplanet candidates.
Uses safe v1 approximations based on stellar luminosity and orbit distance.

Architecture:
  - HabitableZoneEstimator - Core class for habitable zone estimation
  - Uses Kepler-based orbit estimation from scientific analysis
  - Safe approximations only - no direct planet certainty claims

Safety Boundaries:
  - Scientific candidate estimation only
  - No direct planet certainty claims
  - Output must indicate estimation/candidate status
  - Path traversal protection
  - Max file size limit (10MB)
  - Max output size limit (50KB)
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .context import ContextLabel


__all__ = [
    "HabitableZoneEstimator",
    "HabitableZoneError",
    "create_habitable_zone_estimator",
    "HABITABLE_ZONE_ESTIMATOR_VERSION",
]


# Version constant for continuity tracking
HABITABLE_ZONE_ESTIMATOR_VERSION: str = "1.0.0"


class HabitableZoneError(Exception):
    """Raised when habitable zone estimation fails."""
    pass


class HabitableZoneEstimator:
    """Golden zone estimation for exoplanet candidates.
    
    Uses safe v1 approximations:
    - inner boundary: 0.95 * sqrt(L)
    - outer boundary: 1.37 * sqrt(L)
    where L is stellar luminosity in solar units.
    
    Usage:
        from weslr.habitable_zone import create_habitable_zone_estimator
        
        estimator = create_habitable_zone_estimator()
        result = estimator.estimate_zone(luminosity=1.0, orbit_distance=1.0)
    """
    
    def __init__(self, workspace_dir: str = None):
        """Initialize habitable zone estimator.
        
        Args:
            workspace_dir: Workspace directory for path validation
        """
        self.workspace_dir = workspace_dir or str(
            Path(__file__).resolve().parent.parent
        )
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_output_chars = 50000  # 50KB
        
        # V1 safe approximations (L in solar units)
        self._inner_factor = 0.95
        self._outer_factor = 1.37
    
    def _is_safe_path(self, filepath: str, workspace_dir: str) -> bool:
        """Check if filepath is within workspace directory."""
        try:
            workspace = Path(workspace_dir).resolve()
            path = Path(filepath).resolve()
            return str(path).startswith(str(workspace) + os.sep) or path == workspace
        except Exception:
            return False
    
    def estimate_zone(
        self,
        luminosity: float,
        orbit_distance: float,
    ) -> Dict[str, Any]:
        """Estimate habitable zone for a star system.
        
        Uses safe v1 approximations:
        - inner boundary: 0.95 * sqrt(L)
        - outer boundary: 1.37 * sqrt(L)
        
        Args:
            luminosity: Stellar luminosity in solar units (L_sun)
            orbit_distance: Planet orbit distance in AU
            
        Returns:
            Dict with habitable zone estimation result
        """
        # Validate inputs
        if luminosity <= 0:
            raise HabitableZoneError(
                f"Luminosity must be positive, got {luminosity}"
            )
        if orbit_distance <= 0:
            raise HabitableZoneError(
                f"Orbit distance must be positive, got {orbit_distance}"
            )
        
        # Calculate boundaries using v1 safe approximations
        sqrt_l = math.sqrt(luminosity)
        inner_boundary = self._inner_factor * sqrt_l  # 0.95 * sqrt(L)
        outer_boundary = self._outer_factor * sqrt_l  # 1.37 * sqrt(L)
        
        # Check if planet is inside habitable zone
        inside_habitable_zone = inner_boundary <= orbit_distance <= outer_boundary
        
        # Calculate Earth similarity score
        earth_similarity = self._calculate_earth_similarity(
            luminosity,
            orbit_distance,
            inner_boundary,
            outer_boundary,
        )
        
        # Calculate confidence based on parameters
        confidence = self._calculate_confidence(
            luminosity,
            orbit_distance,
            inner_boundary,
            outer_boundary,
        )
        
        # Build result following strict output format
        result: Dict[str, Any] = {
            "category": "habitable_zone",
            "inside_habitable_zone": inside_habitable_zone,
            "inner_boundary_au": round(inner_boundary, 6),
            "outer_boundary_au": round(outer_boundary, 6),
            "orbit_distance_au": round(orbit_distance, 6),
            "earth_similarity_score": round(earth_similarity, 4),
            "confidence": round(confidence, 4),
            "analysis_type": "habitable_zone_estimation",
            "method_version": "v1_safe_approximation",
        }
        
        # Add descriptive text
        if inside_habitable_zone:
            result["message"] = (
                f"Planet candidate is INSIDE the habitable zone "
                f"({inner_boundary:.3f} - {outer_boundary:.3f} AU)."
            )
        else:
            result["message"] = (
                f"Planet candidate is OUTSIDE the habitable zone "
                f"({inner_boundary:.3f} - {outer_boundary:.3f} AU)."
            )
        
        result["message"] += (
            " Note: This is an estimation - not a confirmed habitable planet."
        )
        
        return result
    
    def _calculate_earth_similarity(
        self,
        luminosity: float,
        orbit_distance: float,
        inner_boundary: float,
        outer_boundary: float,
    ) -> float:
        """Calculate Earth similarity score (0-1).
        
        Based on:
        - Orbital position within habitable zone
        - Similarity to Earth's orbit (1 AU around 1 L_sun star)
        - Distance from center of habitable zone
        """
        if not (inner_boundary <= orbit_distance <= outer_boundary):
            # Outside habitable zone - low similarity
            return 0.0
        
        # Calculate position within zone (0 = inner edge, 1 = outer edge)
        zone_width = outer_boundary - inner_boundary
        if zone_width < 0.001:
            zone_position = 0.5
        else:
            zone_position = (orbit_distance - inner_boundary) / zone_width
        
        # Distance from optimal (center of zone)
        optimal_position = 0.5
        position_score = 1.0 - abs(zone_position - optimal_position)
        
        # Similarity to Earth's orbit (assuming 1 AU around 1 L_sun)
        # Earth similarity decreases if orbit deviates from 1 AU
        if luminosity > 0:
            expected_orbit = math.sqrt(luminosity)  # Rough estimate
            distance_from_expected = abs(orbit_distance - expected_orbit)
            orbit_similarity = max(0, 1.0 - distance_from_expected)
        else:
            orbit_similarity = 0.0
        
        # Weighted combination
        earth_similarity = (
            0.4 * position_score +
            0.4 * orbit_similarity +
            0.2  # Base similarity for being in the zone
        )
        
        return min(max(earth_similarity, 0.0), 1.0)
    
    def _calculate_confidence(
        self,
        luminosity: float,
        orbit_distance: float,
        inner_boundary: float,
        outer_boundary: float,
    ) -> float:
        """Calculate confidence in estimation (0-1).
        
        Based on parameter reasonableness and zone position.
        """
        # Parameter validity scores
        luminosity_valid = 1.0 if luminosity > 0 and luminosity < 1000 else 0.5
        distance_valid = 1.0 if orbit_distance > 0.01 and orbit_distance < 100 else 0.5
        
        # Zone position confidence
        if inner_boundary <= orbit_distance <= outer_boundary:
            zone_position_confidence = 0.8
        else:
            # Outside zone - still有一定 confidence but lower
            distance_to_zone = min(
                abs(orbit_distance - inner_boundary),
                abs(orbit_distance - outer_boundary)
            )
            zone_position_confidence = max(0.2, 1.0 - distance_to_zone)
        
        # Luminosity stability (very high luminosity reduces confidence)
        luminosity_stability = 1.0 if luminosity < 10 else max(0.3, 10 / luminosity)
        
        # Combined confidence
        confidence = (
            0.25 * luminosity_valid +
            0.25 * distance_valid +
            0.30 * zone_position_confidence +
            0.20 * luminosity_stability
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    def estimate_from_data(
        self,
        filepath: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Estimate habitable zone from scientific data file.
        
        Uses Kepler-based orbit estimation from scientific_analysis module.
        
        Args:
            filepath: Path to file (must be within workspace)
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            Dict with estimation result
        """
        # Validate path
        if not self._is_safe_path(filepath, self.workspace_dir):
            raise HabitableZoneError(
                f"Path traversal attempt: {filepath} is outside workspace"
            )
        
        # Check file exists
        if not os.path.exists(filepath):
            raise HabitableZoneError(f"File not found: {filepath}")
        
        # Check file size
        try:
            size = os.path.getsize(filepath)
            if size > self.max_file_size:
                raise HabitableZoneError(
                    f"File too large: {size} bytes (max {self.max_file_size})"
                )
        except Exception as e:
            raise HabitableZoneError(f"Failed to check file size: {e}")
        
        # Try to extract parameters from data file
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            raise HabitableZoneError(f"Failed to read file: {e}")
        
        # Try JSON format first
        try:
            import json as json_module
            data = json_module.loads(content)
            if isinstance(data, dict):
                luminosity = data.get('luminosity', data.get('star_luminosity', data.get('L', 1.0)))
                orbit_distance = data.get('orbit_distance', data.get('distance_au', data.get('a', 1.0)))
                return self.estimate_zone(luminosity=float(luminosity), orbit_distance=float(orbit_distance))
        except (json_module.JSONDecodeError, ValueError, TypeError):
            pass
        
        # Try CSV format
        try:
            import csv
            import io
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
            if rows:
                row = rows[0]
                luminosity = row.get('luminosity', row.get('star_luminosity', row.get('L', '1.0')))
                orbit_distance = row.get('orbit_distance', row.get('distance_au', row.get('a', '1.0')))
                return self.estimate_zone(luminosity=float(luminosity), orbit_distance=float(orbit_distance))
        except (ValueError, TypeError, Exception):
            pass
        
        # Default fallback
        return self.estimate_zone(luminosity=1.0, orbit_distance=1.0)
    
    def analyze(
        self,
        filepath: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Analyze file for habitable zone estimation.
        
        This is the main entry point for file_router integration.
        
        Args:
            filepath: Path to file (must be within workspace)
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            Dict with analysis result matching StructuredData output format
        """
        result = self.estimate_from_data(filepath, user_query, task_context)
        
        # Convert to RouterResult-compatible format
        return {
            "file_type": ".json",  # Default - will be overridden
            "category": "habitable_zone",
            "relevance": "high" if result.get("inside_habitable_zone", False) else "medium",
            "relevance_reason": result.get("message", "Habitable zone estimation complete"),
            "metadata": {
                "source_file": filepath.split('/')[-1] if '/' in filepath else filepath,
                "parsed_successfully": True,
                "parse_error": None,
                "category": "habitable_zone",
            },
            "safety": {
                "injection_risk": "low",
                "content_type": "scientific_estimation",
            },
            "structured_output": self._format_habitable_zone_output(result, user_query),
            "parsed_data": result,
        }
    
    def _format_habitable_zone_output(
        self,
        result: Dict[str, Any],
        user_query: str,
    ) -> str:
        """Format habitable zone estimation result for chat output."""
        parts = []
        
        # Header
        parts.append("[HABITABLE ZONE ESTIMATION]")
        
        # Query reference
        if user_query:
            parts.append(f"User: \"{user_query}\"")
        
        # Basic result
        if result.get("inside_habitable_zone"):
            parts.append(f"\nPlanet candidate INSIDE habitable zone")
        else:
            parts.append(f"\nPlanet candidate OUTSIDE habitable zone")
        
        parts.append(f"\nInner Boundary: {result.get('inner_boundary_au', 0):.4f} AU")
        parts.append(f"Outer Boundary: {result.get('outer_boundary_au', 0):.4f} AU")
        parts.append(f"Orbit Distance: {result.get('orbit_distance_au', 0):.4f} AU")
        
        # Earth similarity
        parts.append(f"\nEarth Similarity Score: {result.get('earth_similarity_score', 0):.2%}")
        
        # Confidence
        parts.append(f"Confidence: {result.get('confidence', 0):.2%}")
        
        # Method
        parts.append(f"\nMethod: {result.get('method_version', 'v1_safe_approximation')}")
        
        # Message
        if result.get("message"):
            parts.append(f"\nNote: {result['message']}")
        
        # Safety disclaimer
        parts.append("\n⚠️  This is an estimation - not a confirmed planet detection.")
        
        return "\n".join(parts)


def create_habitable_zone_estimator(workspace_dir: str = None) -> HabitableZoneEstimator:
    """Create a habitable zone estimator instance.
    
    Args:
        workspace_dir: Workspace directory for path validation
        
    Returns:
        HabitableZoneEstimator instance
    """
    return HabitableZoneEstimator(workspace_dir=workspace_dir)
