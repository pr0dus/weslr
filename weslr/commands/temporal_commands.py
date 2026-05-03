"""
weslr/commands/temporal_commands.py
===================================
Phase 6.6 — Command handlers for temporal reasoning commands.

Commands:
- /timeseries decompose <variable> [period] [model] — decompose into trend/seasonal/residual
- /timeseries lag <x> <y> [max_lag] — cross-correlation + best lag
- /timeseries stationarity <variable> — ADF test
- /forecast <variable> [horizon] [method] — Holt-Winters forecast with CI
- /alert on forecast <variable> > <value> — set forecast threshold alert
"""

from __future__ import annotations

import re
from typing import Optional

from weslr.modules.temporal_reasoning import (
    decompose,
    autocorr,
    cross_corr,
    granger_cause,
    forecast as temporal_forecast,
    detect_temporal_patterns,
    format_decompose_table,
    format_forecast_table,
    DecomposeResult,
    ForecastResult,
    GrangerResult,
    TemporalPatterns,
)


# ── Dataset registry (in-memory, per-session) ───────────────────────────────

# {variable_name: [values]}
_DATASETS: dict[str, list[float]] = {
    "sales_daily": [
        100.0, 105.0, 102.0, 108.0, 110.0, 115.0, 120.0,
        118.0, 125.0, 122.0, 128.0, 130.0, 135.0, 140.0,
        138.0, 145.0, 142.0, 148.0, 150.0, 155.0, 153.0,
        160.0, 158.0, 165.0, 162.0, 168.0, 170.0, 175.0,
        173.0, 180.0,
    ],
    "temperature": [
        15.0, 14.5, 13.8, 13.0, 12.5, 12.0, 12.2,
        12.8, 13.5, 14.2, 15.0, 15.8, 16.5, 17.0,
        17.5, 18.0, 18.5, 19.0, 19.2, 19.5, 19.8,
        20.0, 20.2, 20.5, 20.8, 21.0, 21.2, 21.5,
        21.8, 22.0,
    ],
}

# Active alert conditions: {alert_id: {variable, threshold, direction, fired}}
_ALERTS: dict[str, dict] = {}
_ALERT_COUNTER = 1


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_series(name: str) -> Optional[list[float]]:
    """Resolve variable name to data series (builtin or user-defined)."""
    # Built-in
    if name in _DATASETS:
        return list(_DATASETS[name])
    # TODO: resolve from fact store / entity memory (Phase 6.6 integration)
    return None


def _format_acf(series_name: str, acf_vals: list[float]) -> str:
    """Format ACF as ASCII bar chart (lags 1-20)."""
    lines = [f"Autocorrelation (ACF) for '{series_name}':", "Lag | ACF"]
    lines.append("-----|---------")
    max_show = min(20, len(acf_vals) - 1)
    for i in range(1, max_show + 1):
        val = acf_vals[i]
        bar_len = int(abs(val) * 40)
        sign = "+" if val >= 0 else "-"
        bar = sign + "|" * bar_len
        lines.append(f"{i:4d} | {val:+.4f}  {bar}")
    return "\n".join(lines)


def _format_cross_corr(result: dict) -> str:
    lag = result["best_lag"]
    corr = result["best_corr"]
    direction = "y lagged by x" if lag > 0 else "x lagged by y"
    sign = "+" if corr >= 0 else ""
    return (
        f"Cross-correlation: best lag = {lag} ({direction})\n"
        f"Correlation at best lag: {sign}{corr:.4f}\n"
        f"Note: positive lag means y follows x (x → y)"
    )


def _format_granger(result: GrangerResult, x_name: str, y_name: str) -> str:
    arrow = f"{x_name} → {y_name}"
    if result.causes:
        return (
            f"Granger causality: {arrow}  (lag {result.best_lag})\n"
            f"  p-value: {result.p_value:.4f}  (significance={result.significance})\n"
            f"  F-statistic: {result.f_stat:.4f}\n"
            f"  → Past values of {x_name} help predict {y_name} beyond its own past.\n"
            f"⚠ Disclaimer: Granger causality is not true causality — it only indicates predictive precedence."
        )
    else:
        return (
            f"No significant Granger causality: {x_name} ↛ {y_name}\n"
            f"  best p-value: {result.p_value:.4f}  (significance={result.significance})\n"
            f"⚠ Disclaimer: Granger causality is not true causality."
        )


def _format_temporal_patterns(series_name: str, patterns: TemporalPatterns) -> str:
    trend_map = {1: "upward ↑", -1: "downward ↓", 0: "flat —"}
    trend = trend_map.get(patterns.trend_direction, "unknown")
    stationarity = patterns.stationarity_via_adf.replace("_", " ")
    return (
        f"Temporal patterns for '{series_name}':\n"
        f"  Trend: {trend}\n"
        f"  Seasonality: {'yes' if patterns.seasonality_present else 'no'} "
        f"(period≈{patterns.seasonality_period} steps)\n"
        f"  ADF test: {stationarity}  (p={patterns.adf_p_value:.4f}, t={patterns.adf_test_stat:.4f})"
    )


# ── Command handlers ─────────────────────────────────────────────────────────


def handle_timeseries_decompose(message: str, lowered: str) -> str:
    """Handle /timeseries decompose <variable> [period] [model]."""
    body = lowered
    for prefix in ("/timeseries decompose ", "timeseries decompose "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    parts = body.strip().split()
    if not parts:
        return "Usage: /timeseries decompose <variable> [period] [model]\n  model: additive (default) | multiplicative"

    variable = parts[0]
    period = int(parts[1]) if len(parts) > 1 else 7
    model = parts[2] if len(parts) > 2 else "additive"
    if model not in ("additive", "multiplicative"):
        model = "additive"

    series = _get_series(variable)
    if series is None:
        return f"Variable '{variable}' not found. Available: {', '.join(_DATASETS.keys())}"

    try:
        result = decompose(series, period, model)
    except ValueError as e:
        return f"Error: {e}"

    # Summary stats
    trend_vals = [v for v in result.trend if v is not None]
    seasonal_vals = [v for v in result.seasonal if v is not None]
    residual_vals = [v for v in result.residual if v is not None]

    summary = (
        f"Decomposition ({model}) for '{variable}' (period={period}):\n"
        f"  Trend:     mean={sum(trend_vals)/len(trend_vals):.4f}  "
        f"range=[{min(trend_vals):.4f}, {max(trend_vals):.4f}]\n"
        f"  Seasonal:  mean={sum(seasonal_vals)/len(seasonal_vals):.4f}  "
        f"range=[{min(seasonal_vals):.4f}, {max(seasonal_vals):.4f}]\n"
        f"  Residual:  std={(_std(residual_vals) if residual_vals else 0):.4f}\n\n"
        f"{format_decompose_table(result)}"
    )
    return summary


def handle_timeseries_lag(message: str, lowered: str) -> str:
    """Handle /timeseries lag <x> <y> [max_lag]."""
    body = lowered
    for prefix in ("/timeseries lag ", "timeseries lag "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    parts = body.strip().split()
    if len(parts) < 2:
        return "Usage: /timeseries lag <x> <y> [max_lag]"

    x_name = parts[0]
    y_name = parts[1]
    max_lag = int(parts[2]) if len(parts) > 2 else 10

    x_series = _get_series(x_name)
    y_series = _get_series(y_name)
    if x_series is None:
        return f"Variable '{x_name}' not found. Available: {', '.join(_DATASETS.keys())}"
    if y_series is None:
        return f"Variable '{y_name}' not found. Available: {', '.join(_DATASETS.keys())}"

    # Cross-correlation
    cc_result = cross_corr(x_series, y_series, max_lag)
    cc_text = _format_cross_corr(cc_result)

    # Granger causality
    granger_result = granger_cause(x_series, y_series, max_lag, significance=0.05)
    granger_text = _format_granger(granger_result, x_name, y_name)

    return f"{cc_text}\n\n{granger_text}"


def handle_timeseries_stationarity(message: str, lowered: str) -> str:
    """Handle /timeseries stationarity <variable>."""
    body = lowered
    for prefix in ("/timeseries stationarity ", "timeseries stationarity "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    variable = body.strip()
    if not variable:
        return "Usage: /timeseries stationarity <variable>"

    series = _get_series(variable)
    if series is None:
        return f"Variable '{variable}' not found. Available: {', '.join(_DATASETS.keys())}"

    patterns = detect_temporal_patterns(series)
    return (
        f"ADF Stationarity Test for '{variable}':\n"
        f"  Test statistic: {patterns.adf_test_stat:.4f}\n"
        f"  p-value: {patterns.adf_p_value:.4f}\n"
        f"  Conclusion: {patterns.stationarity_via_adf.replace('_', ' ')}\n"
        f"  (p < 0.05 → stationary; p >= 0.05 → non-stationary)"
    )


def handle_forecast(message: str, lowered: str) -> str:
    """Handle /forecast <variable> [horizon] [method]."""
    body = lowered
    for prefix in ("/forecast ", "forecast "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    parts = body.strip().split()
    if not parts:
        return "Usage: /forecast <variable> [horizon=10] [method=ets]"

    variable = parts[0]
    horizon = int(parts[1]) if len(parts) > 1 else 10
    method = parts[2] if len(parts) > 2 else "ets"

    series = _get_series(variable)
    if series is None:
        return f"Variable '{variable}' not found. Available: {', '.join(_DATASETS.keys())}"

    try:
        result = temporal_forecast(series, horizon, method)
    except ValueError as e:
        return f"Error: {e}"

    method_label = "Holt-Winters (ETS)" if result.method in ("holt_winters_statsmodels", "holt_winters_pure") else result.method.title()
    header = f"Forecast ({method_label}) for '{variable}':"

    return f"{header}\n{format_forecast_table(result)}"


def handle_alert_forecast(message: str, lowered: str) -> str:
    """Handle /alert on forecast <variable> > <value>."""
    global _ALERT_COUNTER

    body = lowered
    for prefix in ("/alert on forecast ", "alert on forecast "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    # Parse: <variable> > <value> or <variable> >= <value>
    match = re.match(r"(\S+)\s*([><]=?)\s*([\d.]+)", body.strip())
    if not match:
        return "Usage: /alert on forecast <variable> > <value>\n  Example: /alert on forecast sales > 200"

    variable = match.group(1)
    threshold = float(match.group(3))
    direction = match.group(2)

    series = _get_series(variable)
    if series is None:
        return f"Variable '{variable}' not found. Available: {', '.join(_DATASETS.keys())}"

    # Simple: run a 30-step forecast and check
    try:
        result = temporal_forecast(series, 30, "ets")
    except Exception as e:
        return f"Could not run forecast: {e}"

    alert_ids = []
    for i, val in enumerate(result.forecast):
        crossed = False
        if direction == ">":
            crossed = val > threshold
        elif direction == ">=":
            crossed = val >= threshold
        elif direction == "<":
            crossed = val < threshold
        elif direction == "<=":
            crossed = val <= threshold

        if crossed:
            alert_id = f"ALERT-{_ALERT_COUNTER:03d}"
            _ALERT_COUNTER += 1
            _ALERTS[alert_id] = {
                "alert_id": alert_id,
                "variable": variable,
                "threshold": threshold,
                "direction": direction,
                "step": i + 1,
                "forecast_value": round(val, 4),
                "fired": False,
                "message": (
                    f"Forecast alert: {variable} predicted to exceed {threshold} "
                    f"on Step {i+1} (value {val:.1f})."
                ),
            }
            alert_ids.append(alert_id)

    if alert_ids:
        lines = [f"Alert(s) registered ({len(alert_ids)}):"]
        for aid in alert_ids:
            a = _ALERTS[aid]
            lines.append(
                f"  [{aid}] Step {a['step']}: {a['variable']} {a['direction']} {a['threshold']} "
                f"→ predicted value {a['forecast_value']}"
            )
        lines.append("⚠ Alerts are checked by the proactive daemon on next tick.")
        return "\n".join(lines)
    else:
        return (
            f"No threshold crossing predicted for '{variable}' {direction} {threshold} "
            f"in next 30 steps.\n"
            f"Forecast range: [{min(result.forecast):.1f}, {max(result.forecast):.1f}]"
        )


def handle_alert_list(message: str, lowered: str) -> str:
    """Handle /alert list — show registered forecast alerts."""
    if not _ALERTS:
        return "No forecast alerts registered.\n  Usage: /alert on forecast <variable> > <value>"
    lines = [f"Registered forecast alerts ({len(_ALERTS)}):"]
    for aid, a in _ALERTS.items():
        status = "🔥" if a["fired"] else "⏳"
        lines.append(
            f"  {status} [{aid}] {a['variable']} {a['direction']} {a['threshold']} "
            f"→ fires Step {a['step']} (forecast={a['forecast_value']})"
        )
    return "\n".join(lines)


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return variance ** 0.5


# ── Public entry point (matches pattern of other command modules) ─────────────


def handle_temporal_command(message: str, lowered: str) -> str:
    """Route temporal command to appropriate handler."""
    if lowered.startswith("/timeseries decompose") or lowered.startswith("timeseries decompose"):
        return handle_timeseries_decompose(message, lowered)
    elif lowered.startswith("/timeseries lag") or lowered.startswith("timeseries lag"):
        return handle_timeseries_lag(message, lowered)
    elif lowered.startswith("/timeseries stationarity") or lowered.startswith("timeseries stationarity"):
        return handle_timeseries_stationarity(message, lowered)
    elif lowered.startswith("/alert list") or lowered.startswith("alert list"):
        return handle_alert_list(message, lowered)
    elif lowered.startswith("/alert on forecast") or lowered.startswith("alert on forecast"):
        return handle_alert_forecast(message, lowered)
    elif lowered.startswith("/forecast ") or lowered.startswith("forecast "):
        return handle_forecast(message, lowered)
    elif lowered.startswith("/timeseries ") or lowered.startswith("timeseries "):
        # Generic /timeseries → show usage
        return (
            "Temporal commands:\n"
            "  /timeseries decompose <variable> [period=7] [model=additive]\n"
            "  /timeseries lag <x> <y> [max_lag=10]\n"
            "  /timeseries stationarity <variable>\n"
            "  /forecast <variable> [horizon=10] [method=ets]\n"
            "  /alert on forecast <variable> > <value>\n"
            "  /alert list\n\n"
            "Built-in demo datasets: sales_daily, temperature"
        )
    return "Unknown temporal command. Try /timeseries for usage."


def register_dataset(name: str, values: list[float]) -> None:
    """Add a user dataset to the in-memory registry (for testing / demo)."""
    _DATASETS[name] = values
