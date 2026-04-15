"""WESLR Operator Display Helpers v1

Pure display/formatter utilities for the operator dashboard, extracted from sim.py.
Contains only side-effect-free computational formatters:
- build_theme_trends: compute theme pressure trends for dashboard
- sparkline_for_series: render numeric series as unicode sparkline
- slugify: convert string to URL-safe slug

No simulation behavior. No state side effects. No external imports.
"""

from __future__ import annotations

from typing import Any


def slugify(value: str) -> str:
    """Convert a string to a URL-safe slug."""
    value = (value or "item").strip().lower()
    safe = "".join(ch if ch.isalnum() else "-" for ch in value)
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-") or "item"


def sparkline_for_series(series: list[float | int], *, normalize: bool = False) -> str:
    """Render a numeric series as a unicode sparkline string.

    Args:
        series: List of numeric values.
        normalize: If True, scale values to 0-1 range before rendering.

    Returns:
        Unicode sparkline (e.g. "▁▂▃▅▆▇█").
    """
    if not series:
        return "—"
    ticks = "▁▂▃▄▅▆▇█"
    values = [float(v) for v in series]
    if normalize:
        low = min(values)
        high = max(values)
        if abs(high - low) < 1e-9:
            return ticks[3] * len(values)
        scaled = [(v - low) / (high - low) for v in values]
    else:
        scaled = [min(1.0, max(0.0, v)) for v in values]
    return "".join(
        ticks[min(7, max(0, int(v * 8) - (0 if normalize else 1)))] for v in scaled
    )


def build_theme_trends(history: list[dict]) -> list[dict]:
    """Compute theme pressure trends from a history window for the operator dashboard.

    Args:
        history: List of history point dicts with theme_pressure data.

    Returns:
        List of theme trend dicts with sparkline bars, sorted by latest pressure.
    """
    if not history:
        return []
    names = {}
    for point in history[-8:]:
        for theme, pressure in point.get("theme_pressure", {}).items():
            names.setdefault(theme, []).append(round(float(pressure), 3))
    result = []
    for theme, series in names.items():
        delta = round(series[-1] - series[0], 3) if len(series) > 1 else 0.0
        bars = (
            "".join(
                "▁▂▃▄▅▆▇█"[min(7, max(0, int(v * 8) - 1))] for v in series
            )
            or "▁"
        )
        result.append({"theme": theme, "series": series, "delta": delta, "sparkline": bars})
    return sorted(result, key=lambda item: (item["series"][-1], item["delta"]), reverse=True)[
        :8
    ]