# calibration.py - Self-Architecture Core v11: Closed-Loop Governance / Forecast Calibration
# Allow WESLR to compare forecasted outcomes against actual observed outcomes.
# Additive only, operator-first, reversible, governed.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class MismatchSeverity(str, Enum):
    """Severity of forecast-actual mismatch."""
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    CRITICAL = "critical"


class CalibrationStatus(str, Enum):
    """Status of a calibration event."""
    PENDING = "pending"
    ANALYZED = "analyzed"
    ADJUSTED = "adjusted"
    ARCHIVED = "archived"


@dataclass
class ForecastOutcome:
    """A forecasted outcome (before observation)."""
    
    category: str  # e.g., "effort", "risk", "coherence", "benefit"
    forecasted_value: float  # Predicted value (-1 to 1 or 0 to 1)
    confidence: float  # Confidence in forecast (0 to 1)
    timeline: str  # short_term, medium_term, long_term

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "forecasted_value": self.forecasted_value,
            "confidence": self.confidence,
            "timeline": self.timeline,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ForecastOutcome:
        return cls(**data)


@dataclass
class ActualOutcome:
    """An actual observed outcome (after implementation)."""
    
    category: str
    actual_value: float  # Observed value
    observation_timestamp: str
    evidence: str  # Evidence source for actual value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "actual_value": self.actual_value,
            "observation_timestamp": self.observation_timestamp,
            "evidence": self.evidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ActualOutcome:
        return cls(**data)


@dataclass
class CalibrationMismatch:
    """Represents a mismatch between forecast and actual."""
    
    forecast_category: str
    forecast_value: float
    actual_value: float
    delta: float  # forecast - actual
    delta_percentage: float  # delta / max(abs(actual), 0.01)
    severity: str
    corrected_confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "forecast_category": self.forecast_category,
            "forecast_value": self.forecast_value,
            "actual_value": self.actual_value,
            "delta": self.delta,
            "delta_percentage": self.delta_percentage,
            "severity": self.severity,
            "corrected_confidence": self.corrected_confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CalibrationMismatch:
        return cls(**data)


@dataclass
class ForecastCalibration:
    """Complete calibration of a forecast against actual outcomes."""
    
    calibration_id: str
    forecast_id: str
    forecast_title: str
    
    # Forecasts and actuals
    forecast_outcomes: List[ForecastOutcome] = field(default_factory=list)
    actual_outcomes: List[ActualOutcome] = field(default_factory=list)
    
    # Mismatches
    mismatches: List[CalibrationMismatch] = field(default_factory=list)
    
    # Calibration results
    confidence_adjustment: float = 0.0  # How much confidence should be adjusted
    recommendation_adjustment: float = 0.0  # How much recommendation score should change
    status: str = CalibrationStatus.PENDING.value
    calibration_timestamp: Optional[str] = None
    
    # Metadata
    author: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "calibration_id": self.calibration_id,
            "forecast_id": self.forecast_id,
            "forecast_title": self.forecast_title,
            "forecast_outcomes": [o.to_dict() for o in self.forecast_outcomes],
            "actual_outcomes": [o.to_dict() for o in self.actual_outcomes],
            "mismatches": [m.to_dict() for m in self.mismatches],
            "confidence_adjustment": self.confidence_adjustment,
            "recommendation_adjustment": self.recommendation_adjustment,
            "status": self.status,
            "calibration_timestamp": self.calibration_timestamp,
            "author": self.author,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ForecastCalibration:
        data["forecast_outcomes"] = [
            ForecastOutcome.from_dict(o) for o in data.get("forecast_outcomes", [])
        ]
        data["actual_outcomes"] = [
            ActualOutcome.from_dict(o) for o in data.get("actual_outcomes", [])
        ]
        data["mismatches"] = [
            CalibrationMismatch.from_dict(m) for m in data.get("mismatches", [])
        ]
        return cls(**data)

    def calculate_mismatches(self) -> List[CalibrationMismatch]:
        """Calculate mismatches between forecasts and actuals."""
        mismatches = []
        
        for forecast in self.forecast_outcomes:
            for actual in self.actual_outcomes:
                if forecast.category == actual.category:
                    delta = forecast.forecasted_value - actual.actual_value
                    delta_pct = delta / max(abs(actual.actual_value), 0.01) * 100
                    
                    # Determine severity
                    abs_delta_pct = abs(delta_pct)
                    if abs_delta_pct < 10:
                        severity = MismatchSeverity.NONE.value
                    elif abs_delta_pct < 30:
                        severity = MismatchSeverity.MINOR.value
                    elif abs_delta_pct < 60:
                        severity = MismatchSeverity.MODERATE.value
                    elif abs_delta_pct < 100:
                        severity = MismatchSeverity.SIGNIFICANT.value
                    else:
                        severity = MismatchSeverity.CRITICAL.value
                    
                    # Calculate corrected confidence (lower for larger mismatches)
                    corrected_conf = max(0.1, forecast.confidence * (1 - abs_delta_pct / 200))
                    
                    mismatches.append(CalibrationMismatch(
                        forecast_category=forecast.category,
                        forecast_value=forecast.forecasted_value,
                        actual_value=actual.actual_value,
                        delta=delta,
                        delta_percentage=round(delta_pct, 2),
                        severity=severity,
                        corrected_confidence=round(corrected_conf, 3),
                    ))
        
        self.mismatches = mismatches
        return mismatches

    def calculate_adjustments(self) -> None:
        """Calculate confidence and recommendation adjustments."""
        if not self.mismatches:
            return
        
        total_adjustment = 0.0
        for mismatch in self.mismatches:
            total_adjustment += mismatch.corrected_confidence - mismatch.forecast_value
        
        self.confidence_adjustment = round(total_adjustment / len(self.mismatches), 3)
        
        # Adjust recommendation based on overall mismatch direction
        if total_adjustment < -0.2:
            self.recommendation_adjustment = -0.2
        elif total_adjustment > 0.2:
            self.recommendation_adjustment = 0.1
        else:
            self.recommendation_adjustment = round(total_adjustment, 3)

    def get_calibration_summary(self) -> str:
        """Generate human-readable calibration summary."""
        parts = []
        parts.append(f"Forecast: {self.forecast_title}")
        parts.append(f"Mismatches found: {len(self.mismatches)}")
        if self.mismatches:
            avg_delta = sum(m.delta for m in self.mismatches) / len(self.mismatches)
            parts.append(f"Average delta: {avg_delta:.2f}")
            parts.append(f"Confidence adjustment: {self.confidence_adjustment:.2f}")
        return "; ".join(parts)


class CalibrationEngine:
    """Engine for calibrating forecasts against actual outcomes."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("continuity/calibration/histories.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.calibrations: List[ForecastCalibration] = []
        self._load_calibrations()

    def _load_calibrations(self) -> None:
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.calibrations = [
                        ForecastCalibration.from_dict(c) for c in data.get("calibrations", [])
                    ]
            except (json.JSONDecodeError, IOError):
                self.calibrations = []

    def _save_calibrations(self) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({
                "calibrations": [c.to_dict() for c in self.calibrations],
                "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }, f, indent=2)

    def add_forecast(self, forecast: ForecastCalibration) -> ForecastCalibration:
        """Add a forecast to be calibrated."""
        self.calibrations.append(forecast)
        self._save_calibrations()
        return forecast

    def calibrate(
        self,
        forecast_id: str,
        forecast_outcomes: List[Dict[str, Any]],
        actual_outcomes: List[Dict[str, Any]],
        author: str = "operator",
    ) -> ForecastCalibration:
        """Calibrate a forecast against actual outcomes."""
        calibration = ForecastCalibration(
            calibration_id=f"cal-{forecast_id[-4:]}",
            forecast_id=forecast_id,
            forecast_title="",
            forecast_outcomes=[ForecastOutcome.from_dict(o) for o in forecast_outcomes],
            actual_outcomes=[ActualOutcome.from_dict(o) for o in actual_outcomes],
            author=author,
        )
        
        # Calculate mismatches and adjustments
        calibration.calculate_mismatches()
        calibration.calculate_adjustments()
        calibration.calibration_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        calibration.status = CalibrationStatus.ANALYZED.value
        
        self.calibrations.append(calibration)
        self._save_calibrations()
        return calibration

    def get_calibration(self, calibration_id: str) -> Optional[ForecastCalibration]:
        """Get a calibration by ID."""
        for c in self.calibrations:
            if c.calibration_id == calibration_id:
                return c
        return None

    def get_calibrations_by_forecast(self, forecast_id: str) -> List[ForecastCalibration]:
        """Get all calibrations for a forecast."""
        return [c for c in self.calibrations if c.forecast_id == forecast_id]

    def get_all_calibrations(self) -> List[Dict[str, Any]]:
        """Get all calibrations as dicts."""
        return [c.to_dict() for c in self.calibrations]

    def generate_calibration_json(self, calibration_id: str) -> Optional[str]:
        """Generate calibration as JSON string."""
        calibration = self.get_calibration(calibration_id)
        if calibration:
            return json.dumps(calibration.to_dict(), indent=2)
        return None


def calibrate_forecast(
    forecast_id: str,
    forecast_outcomes: List[Dict[str, Any]],
    actual_outcomes: List[Dict[str, Any]],
) -> ForecastCalibration:
    """Convenience function to calibrate a forecast."""
    engine = CalibrationEngine()
    return engine.calibrate(forecast_id, forecast_outcomes, actual_outcomes)


def get_calibration_summary(calibration_id: str) -> str:
    """Get a human-readable calibration summary."""
    engine = CalibrationEngine()
    calibration = engine.get_calibration(calibration_id)
    if calibration:
        return calibration.get_calibration_summary()
    return "Calibration not found"
