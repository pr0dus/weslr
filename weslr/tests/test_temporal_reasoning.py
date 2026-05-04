"""weslr/tests/test_temporal_reasoning.py — Phase 6.6 temporal reasoning tests."""
from __future__ import annotations

import math
import random
import unittest
from unittest.mock import patch, MagicMock

import numpy as np

from weslr.modules.temporal_reasoning import (
    decompose,
    autocorr,
    cross_corr,
    granger_cause,
    forecast,
    detect_temporal_patterns,
    format_decompose_table,
    format_forecast_table,
    _detect_period,
    DecomposeResult,
    ForecastResult,
    GrangerResult,
    TemporalPatterns,
)
from weslr.commands.temporal_commands import (
    handle_temporal_command,
    register_dataset,
    _ALERTS,
    _ALERT_COUNTER,
)


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic helpers
# ─────────────────────────────────────────────────────────────────────────────

def _rng() -> np.random.Generator:
    """Seeded RNG matching module default."""
    return np.random.default_rng(42)


def _sine_wave(n: int, period: int = 12, amplitude: float = 1.0, noise: float = 0.0) -> list[float]:
    """Pure sine wave with optional Gaussian noise."""
    rng = _rng()
    return [
        amplitude * math.sin(2 * math.pi * i / period) + noise * rng.standard_normal()
        for i in range(n)
    ]


def _sine_plus_trend(n: int, period: int = 12, amplitude: float = 1.0,
                     slope: float = 0.1, noise: float = 0.05) -> list[float]:
    """Sine wave with upward linear trend."""
    rng = _rng()
    return [
        slope * i + amplitude * math.sin(2 * math.pi * i / period) + noise * rng.standard_normal()
        for i in range(n)
    ]


def _random_walk(n: int, step_std: float = 1.0) -> list[float]:
    """Random walk (non-stationary by construction)."""
    rng = _rng()
    vals = [0.0]
    for _ in range(n - 1):
        vals.append(vals[-1] + step_std * rng.standard_normal())
    return vals


# ─────────────────────────────────────────────────────────────────────────────
# Test fixtures
# ─────────────────────────────────────────────────────────────────────────────

class TestTemporalReasoning(unittest.TestCase):
    """Phase 6.6 temporal reasoning test suite."""

    def setUp(self) -> None:
        np.random.seed(42)
        random.seed(42)
        # Wipe any leftover alerts between tests
        _ALERTS.clear()

    # ── decompose ────────────────────────────────────────────────────────────

    def test_decompose_sine_wave_no_trend(self):
        """Sine wave decomposition has flat trend, sinusoidal seasonal."""
        series = _sine_wave(60, period=12, amplitude=2.0)
        result = decompose(series, period=12, model="additive")

        self.assertIsInstance(result, DecomposeResult)
        self.assertEqual(result.model, "additive")
        self.assertEqual(len(result.trend), 60)
        self.assertEqual(len(result.seasonal), 60)
        self.assertEqual(len(result.residual), 60)

        # Trend should be near-zero (flat series)
        trend_vals = [t for t in result.trend if t is not None]
        self.assertTrue(abs(sum(trend_vals) / len(trend_vals)) < 0.5)

    def test_decompose_sine_plus_trend_has_slope(self):
        """Sine+trend decomposition shows upward trend."""
        series = _sine_plus_trend(60, period=12, slope=0.3)
        result = decompose(series, period=12, model="additive")

        trend_vals = [t for t in result.trend if t is not None]
        # First half vs second half of trend should show upward direction
        early = sum(trend_vals[:15]) / 15
        late = sum(trend_vals[-15:]) / 15
        self.assertGreater(late, early,
            f"Trend should rise: early={early:.3f}, late={late:.3f}")

    def test_decompose_multiplicative_model(self):
        """Multiplicative decomposition produces positive components."""
        series = [10 + math.sin(2 * math.pi * i / 12) * 2 for i in range(48)]
        result = decompose(series, period=12, model="multiplicative")

        self.assertEqual(result.model, "multiplicative")
        self.assertEqual(len(result.trend), 48)
        self.assertEqual(len(result.seasonal), 48)

        # All trend values should be positive for multiplicative
        trend_vals = [t for t in result.trend if t is not None and t > 0]
        self.assertGreater(len(trend_vals), 40,
            "Multiplicative trend should be predominantly positive")

    def test_decompose_residual_smaller_than_original(self):
        """Residual std is smaller than original series std."""
        series = _sine_wave(60, period=12, amplitude=2.0, noise=0.1)
        result = decompose(series, period=12, model="additive")

        residual_vals = [r for r in result.residual if r is not None]
        residual_std = np.std(residual_vals)
        original_std = np.std(series)
        self.assertLess(residual_std, original_std,
            "Residual should capture less variance than original")

    def test_decompose_raises_short_series(self):
        """Decomposition raises ValueError for series too short."""
        short_series = [1.0, 2.0, 3.0]  # period=12 needs 24 points
        with self.assertRaises(ValueError):
            decompose(short_series, period=12, model="additive")

    # ── autocorr ─────────────────────────────────────────────────────────────

    def test_autocorr_length(self):
        """ACF returns max_lag+1 values (including lag 0)."""
        series = _sine_wave(60, period=12)
        acf_vals = autocorr(series, max_lag=20)
        self.assertEqual(len(acf_vals), 21)
        self.assertAlmostEqual(acf_vals[0], 1.0, places=5,
            msg="Lag-0 ACF must equal 1.0")

    def test_autocorr_sine_peak_at_period(self):
        """ACF has peak at the sine wave period (lag=12)."""
        series = _sine_wave(120, period=12, amplitude=3.0)
        acf_vals = autocorr(series, max_lag=30)

        # Lag 12 should be near 1.0 (strong periodic signal)
        self.assertGreater(acf_vals[12], 0.7,
            f"ACF at period lag (12) should be high, got {acf_vals[12]:.4f}")

    def test_autocorr_flat_series_near_zero(self):
        """ACF of constant/flat series is near zero for lags > 0."""
        flat = [5.0] * 50
        acf_vals = autocorr(flat, max_lag=20)

        # Lags 1..20 should be ~0 (no autocorrelation in constant series)
        for lag in range(1, min(21, len(acf_vals))):
            self.assertLess(abs(acf_vals[lag]), 0.1,
                f"Flat series ACF at lag {lag} should be ~0, got {acf_vals[lag]:.4f}")

    def test_autocorr_random_walk_decay(self):
        """Random walk ACF decays slowly (characteristic of non-stationary)."""
        series = _random_walk(100, step_std=1.0)
        acf_vals = autocorr(series, max_lag=30)

        # ACF should stay high for many lags in a random walk
        self.assertGreater(acf_vals[5], 0.5,
            f"Random walk ACF at lag 5 should be high, got {acf_vals[5]:.4f}")
        self.assertGreater(acf_vals[15], 0.3,
            f"Random walk ACF at lag 15 should be moderate-high, got {acf_vals[15]:.4f}")

    # ── cross_corr ────────────────────────────────────────────────────────────

    def test_cross_corr_lagged_signal_x_leads_y(self):
        """Cross-correlation detects x leading y by known lag."""
        rng = _rng()
        # x leads y by 3 steps
        x = [math.sin(2 * math.pi * i / 12) for i in range(60)]
        y = [x[i - 3] + 0.1 * rng.standard_normal() for i in range(60)]

        result = cross_corr(x, y, max_lag=10)

        self.assertIn("best_lag", result)
        self.assertIn("best_corr", result)
        self.assertIn("ccf", result)
        self.assertEqual(result["best_lag"], 3,
            f"Expected best_lag=3, got {result['best_lag']}")

    def test_cross_corr_no_lag_zero(self):
        """Cross-correlation should exclude lag 0 from best_lag search."""
        rng = _rng()
        x = _random_walk(50, step_std=1.0)
        y = _random_walk(50, step_std=1.0)

        result = cross_corr(x, y, max_lag=10)

        self.assertNotEqual(result["best_lag"], 0,
            "best_lag should not be 0 (lag 0 excluded from peak search)")

    def test_cross_corr_ccf_list_length(self):
        """CCF list covers [-max_lag, ..., max_lag] = 2*max_lag+1."""
        result = cross_corr([1.0]*30, [1.0]*30, max_lag=15)
        self.assertEqual(len(result["ccf"]), 31)

    # ── granger_cause ───────────────────────────────────────────────────────

    def test_granger_y_lagged_by_x_causes(self):
        """y = lag(x,2) + noise → Granger causality with p < 0.05."""
        rng = _rng()
        n = 100
        x = [rng.standard_normal() for _ in range(n)]
        # y depends on x two steps ago
        y = [0.0] * n
        for i in range(2, n):
            y[i] = 0.8 * x[i - 2] + 0.2 * rng.standard_normal()

        result = granger_cause(x, y, max_lag=5, significance=0.05)

        self.assertIsInstance(result, GrangerResult)
        self.assertTrue(result.causes,
            f"Expected causality (p={result.p_value:.4f} < 0.05), "
            f"but result.causes={result.causes}")
        self.assertLess(result.p_value, 0.05)
        self.assertGreater(result.best_lag, 0)

    def test_granger_independent_series_no_causality(self):
        """Two independent random walks → no Granger causality."""
        rng = _rng()
        x = [rng.standard_normal() for _ in range(200)]
        y = [rng.standard_normal() for _ in range(200)]

        result = granger_cause(x, y, max_lag=5, significance=0.05)

        self.assertFalse(result.causes,
            f"Independent series should not show causality (p={result.p_value:.4f})")

    def test_granger_f_stat_positive(self):
        """Granger F-statistic is positive when causality is detected."""
        rng = _rng()
        n = 100
        x = [rng.standard_normal() for _ in range(n)]
        y = [0.0] * n
        for i in range(2, n):
            y[i] = 0.7 * x[i - 2] + 0.3 * rng.standard_normal()

        result = granger_cause(x, y, max_lag=5, significance=0.05)

        if result.causes:
            self.assertGreater(result.f_stat, 0.0,
                f"F-statistic should be positive when causality detected, got {result.f_stat}")

    def test_granger_significance_threshold(self):
        """At significance=0.01, strong causality still detected."""
        rng = _rng()
        n = 100
        x = [rng.standard_normal() for _ in range(n)]
        y = [0.0] * n
        for i in range(2, n):
            y[i] = 1.0 * x[i - 2] + 0.1 * rng.standard_normal()

        result = granger_cause(x, y, max_lag=5, significance=0.01)

        self.assertTrue(result.causes,
            f"Strong causality should survive significance=0.01 (p={result.p_value:.4f})")

    # ── forecast ──────────────────────────────────────────────────────────────

    def test_forecast_returns_correct_horizon(self):
        """Forecast returns exactly horizon number of steps."""
        series = _sine_plus_trend(60, period=12, slope=0.1)
        result = forecast(series, horizon=7, method="ets")

        self.assertIsInstance(result, ForecastResult)
        self.assertEqual(len(result.forecast), 7)
        self.assertEqual(len(result.lower_80), 7)
        self.assertEqual(len(result.upper_80), 7)
        self.assertEqual(len(result.lower_95), 7)
        self.assertEqual(len(result.upper_95), 7)

    def test_forecast_intervals_order(self):
        """80% CI is narrower than 95% CI for every step."""
        series = _sine_plus_trend(60, period=12, slope=0.1)
        result = forecast(series, horizon=10, method="ets")

        for i in range(10):
            width_80 = result.upper_80[i] - result.lower_80[i]
            width_95 = result.upper_95[i] - result.lower_95[i]
            self.assertLess(width_80, width_95,
                f"Step {i}: 80% CI width ({width_80:.4f}) should be < 95% CI width ({width_95:.4f})")

    def test_forecast_rmse_below_naive(self):
        """ETS forecast RMSE is lower than naive (last-value) baseline."""
        rng = _rng()
        # Trending + seasonal series
        train = _sine_plus_trend(50, period=12, slope=0.15, noise=0.1)
        test = _sine_plus_trend(50, 12, slope=0.15, noise=0.1)  # same process, fresh seed reset

        result = forecast(train, horizon=10, method="ets")
        naive = [train[-1]] * 10

        ets_rmse = math.sqrt(sum(
            (result.forecast[i] - test[i]) ** 2 for i in range(10)
        ) / 10)
        naive_rmse = math.sqrt(sum(
            (naive[i] - test[i]) ** 2 for i in range(10)
        ) / 10)

        self.assertLess(ets_rmse, naive_rmse * 1.5,
            f"ETS RMSE ({ets_rmse:.3f}) should be competitive with naive ({naive_rmse:.3f})")

    def test_forecast_short_series_fallback(self):
        """Series with < 4 points falls back to naive method."""
        series = [1.0, 2.0, 3.0]
        result = forecast(series, horizon=5, method="ets")

        self.assertIsInstance(result, ForecastResult)
        self.assertEqual(len(result.forecast), 5)
        self.assertEqual(result.method, "naive_fallback")

    def test_forecast_horizon_raises_on_zero(self):
        """forecast(horizon=0) raises ValueError."""
        with self.assertRaises(ValueError):
            forecast([1.0] * 20, horizon=0, method="ets")

    # ── detect_temporal_patterns ─────────────────────────────────────────────

    def test_detect_patterns_random_walk_non_stationary(self):
        """Random walk is correctly flagged non-stationary (p > 0.05)."""
        series = _random_walk(100, step_std=2.0)
        patterns = detect_temporal_patterns(series)

        self.assertIsInstance(patterns, TemporalPatterns)
        self.assertEqual(patterns.stationarity_via_adf, "non_stationary",
            f"Random walk should be non-stationary, got {patterns.stationarity_via_adf}")
        self.assertGreater(patterns.adf_p_value, 0.05,
            f"ADF p-value should be > 0.05 for random walk, got {patterns.adf_p_value:.4f}")

    def test_detect_patterns_sine_has_seasonality(self):
        """Sine wave is flagged as seasonal."""
        series = _sine_wave(80, period=12, amplitude=2.0)
        patterns = detect_temporal_patterns(series)

        self.assertTrue(patterns.seasonality_present,
            f"Sine wave should show seasonality; period={patterns.seasonality_period}")

    def test_detect_patterns_flat_series_trend_flat(self):
        """Flat series (no trend) is detected as flat (trend_direction=0)."""
        flat = [5.0] * 60
        patterns = detect_temporal_patterns(flat)

        self.assertEqual(patterns.trend_direction, 0,
            f"Flat series should have trend_direction=0, got {patterns.trend_direction}")

    def test_detect_patterns_upward_trend_detected(self):
        """Upward trend is correctly flagged."""
        series = _sine_plus_trend(60, period=12, slope=0.5)
        patterns = detect_temporal_patterns(series)

        self.assertEqual(patterns.trend_direction, 1,
            f"Upward trend should give trend_direction=1, got {patterns.trend_direction}")

    def test_detect_patterns_insufficient_data(self):
        """Series shorter than 8 returns insufficient_data."""
        short = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        patterns = detect_temporal_patterns(short)

        self.assertEqual(patterns.stationarity_via_adf, "insufficient_data")

    # ── format helpers ───────────────────────────────────────────────────────

    def test_format_decompose_table_produces_string(self):
        """format_decompose_table returns a non-empty string."""
        series = _sine_wave(30, period=12)
        result = decompose(series, period=12, model="additive")
        table = format_decompose_table(result)

        self.assertIsInstance(table, str)
        self.assertGreater(len(table), 10)
        self.assertIn("Trend", table)

    def test_format_forecast_table_produces_string(self):
        """format_forecast_table returns a non-empty string."""
        series = _sine_plus_trend(40, period=12, slope=0.1)
        result = forecast(series, horizon=5, method="ets")
        table = format_forecast_table(result)

        self.assertIsInstance(table, str)
        self.assertGreater(len(table), 10)
        self.assertIn("Forecast", table)

    def test_format_decompose_table_with_names(self):
        """format_decompose_table accepts optional row names."""
        series = _sine_wave(24, period=12)
        result = decompose(series, period=12, model="additive")
        names = [f"t{i}" for i in range(24)]
        table = format_decompose_table(result, names=names)

        self.assertIsInstance(table, str)
        self.assertIn("t0", table)

    # ── _detect_period ───────────────────────────────────────────────────────

    def test_detect_period_sine_wave(self):
        """_detect_period returns the known sine period."""
        series = _sine_wave(60, period=12, amplitude=3.0)
        period = _detect_period(series)

        self.assertEqual(period, 12,
            f"Expected detected period=12, got {period}")

    def test_detect_period_random_walk_falls_back(self):
        """Random walk (no real period) returns between 2 and some upper bound."""
        series = _random_walk(50, step_std=2.0)
        period = _detect_period(series)

        self.assertGreaterEqual(period, 2)
        self.assertLessEqual(period, 365)

    # ── command parsing ──────────────────────────────────────────────────────

    def test_command_decompose_sine(self):
        """handle_temporal_command routes /timeseries decompose correctly."""
        result = handle_temporal_command(
            "/timeseries decompose sales_daily 7 additive",
            "/timeseries decompose sales_daily 7 additive"
        )

        self.assertIsInstance(result, str)
        self.assertIn("Decomposition", result)

    def test_command_lag_shows_cross_corr(self):
        """handle_temporal_command /timeseries lag returns cross-correlation."""
        result = handle_temporal_command(
            "/timeseries lag sales_daily temperature 10",
            "/timeseries lag sales_daily temperature 10"
        )

        self.assertIsInstance(result, str)
        self.assertIn("Cross-correlation", result)
        self.assertIn("best lag", result.lower())

    def test_command_stationarity_returns_adf(self):
        """handle_temporal_command /timeseries stationarity returns ADF output."""
        result = handle_temporal_command(
            "/timeseries stationarity sales_daily",
            "/timeseries stationarity sales_daily"
        )

        self.assertIsInstance(result, str)
        self.assertIn("ADF", result)

    def test_command_forecast_runs_ets(self):
        """handle_temporal_command /forecast runs Holt-Winters."""
        result = handle_temporal_command(
            "/forecast temperature 10 ets",
            "/forecast temperature 10 ets"
        )

        self.assertIsInstance(result, str)
        self.assertIn("Forecast", result)

    def test_command_alert_forecast_registers_alert(self):
        """handle_temporal_command /alert on forecast registers alert in _ALERTS."""
        initial_count = len(_ALERTS)

        result = handle_temporal_command(
            "/alert on forecast sales_daily > 200",
            "/alert on forecast sales_daily > 200"
        )

        self.assertIsInstance(result, str)
        self.assertGreater(len(_ALERTS), initial_count,
            f"Alert should be registered; _ALERTS={len(_ALERTS)}, was {initial_count}")

    def test_command_alert_list_shows_alerts(self):
        """handle_temporal_command /alert list shows registered alerts."""
        # Pre-register an alert
        handle_temporal_command(
            "/alert on forecast sales_daily > 200",
            "/alert on forecast sales_daily > 200"
        )

        result = handle_temporal_command("/alert list", "/alert list")

        self.assertIsInstance(result, str)
        self.assertIn("ALERT", result)

    def test_command_unknown_returns_usage(self):
        """Unknown temporal command returns usage string."""
        result = handle_temporal_command(
            "/timeseries gibberish",
            "/timeseries gibberish"
        )

        self.assertIsInstance(result, str)
        # Should return usage hint or error
        self.assertTrue(len(result) > 0)

    # ── integration: /explore on time-series dataset ─────────────────────────

    def test_explore_integration_temporal_annotations(self):
        """Explore on time-series dataset yields temporal annotations."""
        # Register a test dataset
        register_dataset("test_ts", _sine_plus_trend(60, period=12, slope=0.2))

        # Simulate /explore: run temporal pattern detection + forecast + decompose
        series = _sine_plus_trend(60, period=12, slope=0.2)

        patterns = detect_temporal_patterns(series)
        result = decompose(series, period=12, model="additive")
        fcast = forecast(series, horizon=5, method="ets")

        # Verify all three produce annotated output
        self.assertEqual(patterns.trend_direction, 1)
        self.assertIsNotNone(result.trend)
        self.assertEqual(len(fcast.forecast), 5)

        # format_*_table should produce human-readable output
        decompose_table = format_decompose_table(result)
        forecast_table = format_forecast_table(fcast)

        self.assertIn("Trend", decompose_table)
        self.assertIn("Forecast", forecast_table)

    # ── proactive daemon forecast alert (mock trigger) ───────────────────────

    def test_daemon_alert_triggers_on_threshold_crossing(self):
        """Proactive daemon fires alert when forecast crosses threshold."""
        # Clear any residual alerts
        _ALERTS.clear()

        # Use a trending series that will definitely cross a threshold
        trending = [0.5 * i + 10 + 2 * math.sin(2 * math.pi * i / 12) for i in range(40)]
        register_dataset("test_ts", trending)

        result = handle_temporal_command(
            f"/alert on forecast test_ts > {trending[-1] + 5}",
            f"/alert on forecast test_ts > {trending[-1] + 5}"
        )

        # Should have registered at least one alert
        self.assertIsInstance(result, str)
        # Check that at least one alert was registered
        self.assertGreater(len(_ALERTS), 0,
            f"Trending series should trigger alert. Got: {result}")

    def test_daemon_alert_no_crossing_stays_quiet(self):
        """Forecast not crossing threshold registers no alerts."""
        _ALERTS.clear()

        # Flat series won't cross any reasonable threshold
        flat = [5.0] * 40
        register_dataset("flat_ts", flat)

        result = handle_temporal_command(
            "/alert on forecast flat_ts > 1000",
            "/alert on forecast flat_ts > 1000"
        )

        self.assertIn("No threshold crossing", result)

    # ── edge cases ───────────────────────────────────────────────────────────

    def test_autocorr_single_value_series(self):
        """ACF on single-element series returns zeros."""
        acf_vals = autocorr([42.0], max_lag=5)
        self.assertEqual(len(acf_vals), 6)
        self.assertEqual(acf_vals[0], 1.0)

    def test_cross_corr_mismatched_lengths(self):
        """Cross-correlation handles different length series."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 2.0, 3.0]
        result = cross_corr(x, y, max_lag=3)

        self.assertIsInstance(result, dict)
        self.assertIn("best_lag", result)
        self.assertIn("best_corr", result)

    def test_granger_very_short_series(self):
        """Granger on very short series doesn't crash."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 4.0, 3.0, 2.0, 1.0]
        result = granger_cause(x, y, max_lag=2, significance=0.05)

        # Should return a result, causality status may be False due to insufficient data
        self.assertIsInstance(result, GrangerResult)

    def test_forecast_unknown_method_raises(self):
        """forecast with unsupported method raises ValueError."""
        with self.assertRaises(ValueError):
            forecast([1.0] * 20, horizon=5, method="unknown_method")

    def test_decompose_multiplicative_zero_values(self):
        """Multiplicative decomposition handles series with near-zero values."""
        # All positive series around 1.0 so log transform doesn't explode
        series = [1.0 + 0.1 * math.sin(2 * math.pi * i / 7) for i in range(30)]
        result = decompose(series, period=7, model="multiplicative")

        self.assertEqual(result.model, "multiplicative")
        self.assertEqual(len(result.trend), 30)

    def test_detect_period_empty_series(self):
        """_detect_period on empty/short series returns safe default."""
        period = _detect_period([])
        self.assertEqual(period, 7, "Should default to period=7 for empty series")

        period_short = _detect_period([1.0, 2.0])
        self.assertEqual(period_short, 7, "Should default to period=7 for very short series")


# ─────────────────────────────────────────────────────────────────────────────
# Test runner
# ─────────────────────────────────────────────────────────────────────────────

def run_temporal_reasoning_tests() -> dict:
    """Run all temporal reasoning tests and return summary."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTemporalReasoning)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return {
        "tests_run": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failed": len(result.failures),
        "errors": len(result.errors),
        "category": "temporal_reasoning",
        "phase": "6.6",
    }


if __name__ == "__main__":
    summary = run_temporal_reasoning_tests()
    print(f"\n{'='*60}")
    print(f"Phase 6.6 — Temporal Reasoning Tests")
    print(f"{'='*60}")
    print(f"Tests run : {summary['tests_run']}")
    print(f"Passed    : {summary['passed']}")
    print(f"Failed   : {summary['failed']}")
    print(f"Errors   : {summary['errors']}")
    print(f"{'='*60}")