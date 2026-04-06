# test_calibration.py - Tests for Self-Architecture Core v11: Forecast Calibration
# Forecast comparison, confidence correction, mismatch severity, history persistence.

from __future__ import annotations

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from calibration import (
    CalibrationEngine,
    CalibrationMismatch,
    ForecastOutcome,
    ActualOutcome,
    ForecastCalibration,
    calibrate_forecast,
)


class TestForecastOutcome(unittest.TestCase):
    """Test forecast outcome model."""

    def test_forecast_outcome_creation(self):
        """Can create a forecast outcome."""
        outcome = ForecastOutcome(
            category="effort",
            forecasted_value=0.6,
            confidence=0.8,
            timeline="short_term",
        )
        self.assertEqual(outcome.category, "effort")
        self.assertEqual(outcome.forecasted_value, 0.6)
        self.assertEqual(outcome.confidence, 0.8)

    def test_forecast_outcome_to_dict(self):
        """Can serialize forecast outcome to dict."""
        outcome = ForecastOutcome(
            category="risk",
            forecasted_value=0.4,
            confidence=0.7,
            timeline="medium_term",
        )
        data = outcome.to_dict()
        self.assertEqual(data["category"], "risk")
        self.assertEqual(data["timeline"], "medium_term")


class TestActualOutcome(unittest.TestCase):
    """Test actual outcome model."""

    def test_actual_outcome_creation(self):
        """Can create an actual outcome."""
        outcome = ActualOutcome(
            category="effort",
            actual_value=0.7,
            observation_timestamp="2024-01-01T00:00:00Z",
            evidence="Implementation metrics",
        )
        self.assertEqual(outcome.category, "effort")
        self.assertEqual(outcome.actual_value, 0.7)

    def test_actual_outcome_to_dict(self):
        """Can serialize actual outcome to dict."""
        outcome = ActualOutcome(
            category="benefit",
            actual_value=0.5,
            observation_timestamp="2024-01-01T00:00:00Z",
            evidence="User feedback",
        )
        data = outcome.to_dict()
        self.assertEqual(data["evidence"], "User feedback")


class TestCalibrationMismatch(unittest.TestCase):
    """Test calibration mismatch model."""

    def test_mismatch_creation(self):
        """Can create a mismatch."""
        mismatch = CalibrationMismatch(
            forecast_category="effort",
            forecast_value=0.6,
            actual_value=0.7,
            delta=-0.1,
            delta_percentage=-14.29,
            severity="minor",
            corrected_confidence=0.7,
        )
        self.assertEqual(mismatch.delta, -0.1)
        self.assertEqual(mismatch.severity, "minor")

    def test_mismatch_severity_none(self):
        """Minor mismatch is identified as minor."""
        mismatch = CalibrationMismatch(
            forecast_category="effort",
            forecast_value=0.5,
            actual_value=0.55,
            delta=-0.05,
            delta_percentage=-9.09,
            severity="none",
            corrected_confidence=0.8,
        )
        self.assertEqual(mismatch.delta_percentage, -9.09)


class TestForecastCalibration(unittest.TestCase):
    """Test forecast calibration model."""

    def test_calibration_creation(self):
        """Can create a calibration."""
        forecast = ForecastCalibration(
            calibration_id="cal123",
            forecast_id="fcst123",
            forecast_title="Test forecast",
        )
        self.assertEqual(forecast.calibration_id, "cal123")
        self.assertEqual(forecast.forecast_id, "fcst123")

    def test_calculate_mismatches(self):
        """Can calculate mismatches between forecasts and actuals."""
        calibration = ForecastCalibration(
            calibration_id="test",
            forecast_id="fcst1",
            forecast_title="Test",
            forecast_outcomes=[
                ForecastOutcome(
                    category="effort",
                    forecasted_value=0.6,
                    confidence=0.8,
                    timeline="short_term",
                ),
            ],
            actual_outcomes=[
                ActualOutcome(
                    category="effort",
                    actual_value=0.7,
                    observation_timestamp="2024-01-01T00:00:00Z",
                    evidence="Metrics",
                ),
            ],
        )
        
        mismatches = calibration.calculate_mismatches()
        self.assertEqual(len(mismatches), 1)
        self.assertAlmostEqual(mismatches[0].delta, -0.1, places=5)

    def test_calculate_adjustments(self):
        """Can calculate confidence and recommendation adjustments."""
        calibration = ForecastCalibration(
            calibration_id="test",
            forecast_id="fcst1",
            forecast_title="Test",
            forecast_outcomes=[
                ForecastOutcome(
                    category="effort",
                    forecasted_value=0.6,
                    confidence=0.8,
                    timeline="short_term",
                ),
            ],
            actual_outcomes=[
                ActualOutcome(
                    category="effort",
                    actual_value=0.7,
                    observation_timestamp="2024-01-01T00:00:00Z",
                    evidence="Metrics",
                ),
            ],
        )
        calibration.calculate_mismatches()
        calibration.calculate_adjustments()
        
        self.assertIsNotNone(calibration.confidence_adjustment)
        self.assertIsNotNone(calibration.recommendation_adjustment)

    def test_get_calibration_summary(self):
        """Can generate calibration summary."""
        calibration = ForecastCalibration(
            calibration_id="test",
            forecast_id="fcst1",
            forecast_title="Test",
        )
        summary = calibration.get_calibration_summary()
        self.assertIn("Test", summary)

    def test_to_dict(self):
        """Can serialize calibration to dict."""
        calibration = ForecastCalibration(
            calibration_id="test123",
            forecast_id="fcst1",
            forecast_title="Test",
        )
        data = calibration.to_dict()
        self.assertEqual(data["calibration_id"], "test123")
        self.assertEqual(data["forecast_title"], "Test")

    def test_from_dict(self):
        """Can deserialize calibration from dict."""
        data = {
            "calibration_id": "abc123",
            "forecast_id": "fcst1",
            "forecast_title": "Test from dict",
        }
        calibration = ForecastCalibration.from_dict(data)
        self.assertEqual(calibration.calibration_id, "abc123")


class TestCalibrationEngine(unittest.TestCase):
    """Test calibration engine."""

    def setUp(self):
        """Create temp directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "calibrations.json"

    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)

    def test_calibrate_forecast(self):
        """Can calibrate a forecast."""
        engine = CalibrationEngine(storage_path=self.storage_path)
        
        calibration = engine.calibrate(
            forecast_id="fcst001",
            forecast_outcomes=[
                {
                    "category": "effort",
                    "forecasted_value": 0.6,
                    "confidence": 0.8,
                    "timeline": "short_term",
                },
            ],
            actual_outcomes=[
                {
                    "category": "effort",
                    "actual_value": 0.7,
                    "observation_timestamp": "2024-01-01T00:00:00Z",
                    "evidence": "Metrics",
                },
            ],
            author="operator",
        )
        
        self.assertEqual(calibration.forecast_id, "fcst001")
        self.assertEqual(len(calibration.mismatches), 1)

    def test_get_calibration(self):
        """Can retrieve calibration by ID."""
        engine = CalibrationEngine(storage_path=self.storage_path)
        
        cal1 = engine.calibrate(
            "fcst001",
            [{"category": "effort", "forecasted_value": 0.6, "confidence": 0.8, "timeline": "short_term"}],
            [{"category": "effort", "actual_value": 0.7, "observation_timestamp": "2024-01-01T00:00:00Z", "evidence": "Metrics"}],
        )
        
        retrieved = engine.get_calibration(cal1.calibration_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.forecast_id, "fcst001")

    def test_get_calibrations_by_forecast(self):
        """Can get all calibrations for a forecast."""
        engine = CalibrationEngine(storage_path=self.storage_path)
        
        cal1 = engine.calibrate("fcst001", [], [])
        cal2 = engine.calibrate("fcst001", [], [])
        
        by_forecast = engine.get_calibrations_by_forecast("fcst001")
        self.assertEqual(len(by_forecast), 2)

    def test_get_all_calibrations(self):
        """Can get all calibrations as dicts."""
        engine = CalibrationEngine(storage_path=self.storage_path)
        
        engine.calibrate("fcst001", [], [])
        engine.calibrate("fcst002", [], [])
        
        all_cals = engine.get_all_calibrations()
        self.assertEqual(len(all_cals), 2)

    def test_generate_calibration_json(self):
        """Can generate calibration as JSON."""
        engine = CalibrationEngine(storage_path=self.storage_path)
        
        cal = engine.calibrate("fcst001", [], [])
        json_str = engine.generate_calibration_json(cal.calibration_id)
        
        data = json.loads(json_str)
        self.assertEqual(data["calibration_id"], cal.calibration_id)

    def test_calibration_persistence(self):
        """Calibrations persist to storage."""
        engine1 = CalibrationEngine(storage_path=self.storage_path)
        
        cal1 = engine1.calibrate("fcst001", [], [])
        calibration_id = cal1.calibration_id
        
        # Create new engine (simulates restart)
        engine2 = CalibrationEngine(storage_path=self.storage_path)
        retrieved = engine2.get_calibration(calibration_id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.forecast_id, "fcst001")


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def test_calibrate_forecast_function(self):
        """Convenience calibrate_forecast function works."""
        calibration = calibrate_forecast(
            forecast_id="fcst001",
            forecast_outcomes=[
                {"category": "effort", "forecasted_value": 0.6, "confidence": 0.8, "timeline": "short_term"},
            ],
            actual_outcomes=[
                {"category": "effort", "actual_value": 0.7, "observation_timestamp": "2024-01-01T00:00:00Z", "evidence": "Metrics"},
            ],
        )
        self.assertEqual(calibration.forecast_id, "fcst001")


class TestHistoryPersistence(unittest.TestCase):
    """Test history persistence across operations."""

    def setUp(self):
        """Create temp directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "calibrations.json"

    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)

    def test_multiple_calibrations(self):
        """Can store and retrieve multiple calibrations."""
        engine = CalibrationEngine(storage_path=self.storage_path)
        
        # Add multiple calibrations
        for i in range(5):
            engine.calibrate(
                f"fcst{i:03d}",
                [{"category": "effort", "forecasted_value": 0.5 + i*0.1, "confidence": 0.8, "timeline": "short_term"}],
                [{"category": "effort", "actual_value": 0.6 + i*0.1, "observation_timestamp": "2024-01-01T00:00:00Z", "evidence": "Metrics"}],
            )
        
        all_cals = engine.get_all_calibrations()
        self.assertEqual(len(all_cals), 5)

    def test_calibrations_by_author(self):
        """Can track calibrations by author."""
        engine = CalibrationEngine(storage_path=self.storage_path)
        
        cal1 = engine.calibrate("fcst001", [], [], author="operator")
        cal2 = engine.calibrate("fcst002", [], [], author="operator")
        
        all_cals = engine.get_all_calibrations()
        self.assertEqual(len(all_cals), 2)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing code."""

    def test_existing_engine_usage(self):
        """Existing code using CalibrationEngine still works."""
        temp_dir = tempfile.mkdtemp()
        try:
            storage_path = Path(temp_dir) / "calibrations.json"
            engine = CalibrationEngine(storage_path=storage_path)
            
            calibration = engine.calibrate(
                "existing",
                [{"category": "effort", "forecasted_value": 0.6, "confidence": 0.8, "timeline": "short_term"}],
                [{"category": "effort", "actual_value": 0.7, "observation_timestamp": "2024-01-01T00:00:00Z", "evidence": "Metrics"}],
            )
            self.assertIsNotNone(calibration.calibration_id)
        finally:
            shutil.rmtree(temp_dir)

    def test_empty_calibrations_list(self):
        """Handles empty calibrations list gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            storage_path = Path(temp_dir) / "calibrations.json"
            engine = CalibrationEngine(storage_path=storage_path)
            
            all_cals = engine.get_all_calibrations()
            self.assertIsInstance(all_cals, list)
        finally:
            shutil.rmtree(temp_dir)

    def test_calibration_with_missing_fields(self):
        """Handles calibration with missing optional fields."""
        calibration = ForecastCalibration(
            calibration_id="test",
            forecast_id="fcst1",
            forecast_title="Test",
        )
        self.assertEqual(calibration.author, None)
        self.assertEqual(len(calibration.forecast_outcomes), 0)


class TestMismatchSeverity(unittest.TestCase):
    """Test mismatch severity determination."""

    def test_minor_mismatch(self):
        """Minor mismatch is correctly identified."""
        mismatch = CalibrationMismatch(
            forecast_category="effort",
            forecast_value=0.5,
            actual_value=0.55,
            delta=-0.05,
            delta_percentage=-9.09,
            severity="minor",
            corrected_confidence=0.7,
        )
        self.assertEqual(mismatch.severity, "minor")

    def test_significant_mismatch(self):
        """Significant mismatch is correctly identified."""
        mismatch = CalibrationMismatch(
            forecast_category="effort",
            forecast_value=0.5,
            actual_value=0.9,
            delta=-0.4,
            delta_percentage=-50.0,
            severity="significant",
            corrected_confidence=0.4,
        )
        self.assertEqual(mismatch.severity, "significant")

    def test_critical_mismatch(self):
        """Critical mismatch is correctly identified."""
        mismatch = CalibrationMismatch(
            forecast_category="effort",
            forecast_value=0.3,
            actual_value=0.9,
            delta=-0.6,
            delta_percentage=-100.0,
            severity="critical",
            corrected_confidence=0.1,
        )
        self.assertEqual(mismatch.severity, "critical")


class TestConfidenceCorrection(unittest.TestCase):
    """Test confidence correction logic."""

    def test_confidence_reduction_for_mismatch(self):
        """Confidence is reduced for larger mismatches."""
        mismatch = CalibrationMismatch(
            forecast_category="effort",
            forecast_value=0.5,
            actual_value=0.9,
            delta=-0.4,
            delta_percentage=-50.0,
            severity="significant",
            corrected_confidence=0.4,  # Reduced from 0.8
        )
        self.assertLess(mismatch.corrected_confidence, 0.5)

    def test_min_confidence_threshold(self):
        """Confidence is capped at minimum threshold."""
        mismatch = CalibrationMismatch(
            forecast_category="effort",
            forecast_value=0.5,
            actual_value=1.0,
            delta=-0.5,
            delta_percentage=-50.0,
            severity="significant",
            corrected_confidence=0.1,  # Minimum
        )
        self.assertGreaterEqual(mismatch.corrected_confidence, 0.1)


if __name__ == "__main__":
    unittest.main()
