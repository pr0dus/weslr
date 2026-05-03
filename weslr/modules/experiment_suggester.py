"""
weslr/modules/experiment_suggester.py
======================================
Phase 7 — Experiment Suggester: rule-based next-experiment recommendations.

Author: OCC (WESLR governed intelligence) — Phase 7
"""

from __future__ import annotations

import math
import numpy as np
from dataclasses import dataclass
from typing import Optional

from .hypothesis_repository import Hypothesis


# ── Suggestion data class ────────────────────────────────────────────────────

@dataclass
class ExperimentSuggestion:
    """A single suggested experiment."""

    description: str
    rationale: str
    estimated_impact: str  # low | medium | high
    required_resources: str  # simulation only | in silico | lab experiment
    parameters: dict  # suggested experiment parameters


# ── Suggester ────────────────────────────────────────────────────────────────

class ExperimentSuggester:
    """Rule-based experiment suggestion engine.

    Analyzes the active hypothesis (its metadata and provenance) to identify
    gaps and recommend concrete follow-up experiments. No ML — pure heuristics.
    """

    def suggest_next_experiments(
        self,
        hypothesis: Hypothesis,
        max_suggestions: int = 3,
    ) -> list[ExperimentSuggestion]:
        """Generate experiment suggestions for a hypothesis.

        Returns up to max_suggestions, ordered by estimated impact.
        """
        suggestions: list[tuple[int, ExperimentSuggestion]] = []

        # ── Causal gap analysis ─────────────────────────────────────────
        causal_gap = self._causal_suggestions(hypothesis)
        suggestions.extend(causal_gap)

        # ── Simulation / model uncertainty ─────────────────────────────
        sim_gap = self._simulation_suggestions(hypothesis)
        suggestions.extend(sim_gap)

        # ── Temporal calibration ────────────────────────────────────────
        temporal_gap = self._temporal_suggestions(hypothesis)
        suggestions.extend(temporal_gap)

        # ── Spatial geometry ────────────────────────────────────────────
        spatial_gap = self._spatial_suggestions(hypothesis)
        suggestions.extend(spatial_gap)

        # ── Quantum circuit depth / fidelity ───────────────────────────
        quantum_gap = self._quantum_suggestions(hypothesis)
        suggestions.extend(quantum_gap)

        # Sort by impact (high=0, medium=1, low=2) then return top N
        suggestions.sort(key=lambda x: x[0])
        return [s for _, s in suggestions[:max_suggestions]]

    # ── Domain-specific helpers ─────────────────────────────────────────────

    def _causal_suggestions(
        self, h: Hypothesis
    ) -> list[tuple[int, ExperimentSuggestion]]:
        """Suggest intervention experiments when causal evidence is weak."""
        suggestions: list[tuple[int, ExperimentSuggestion]] = []
        meta = h.metadata

        # Check if there's a causal graph with low-confidence edges
        causal_graph = meta.get("causal_graph", {})
        if causal_graph:
            low_confidence_edges = [
                (edge, conf) for edge, conf in causal_graph.items()
                if conf < 0.7
            ]
            if low_confidence_edges:
                edge, conf = low_confidence_edges[0]
                cause, effect = edge
                suggestions.append(
                    (
                        0 if conf < 0.4 else 1,  # impact: high if very low conf
                        ExperimentSuggestion(
                            description=(
                                f"Intervention experiment: set {cause} to a range of "
                                f"values and measure change in {effect}"
                            ),
                            rationale=(
                                f"Causal edge ({cause} → {effect}) has low confidence "
                                f"({conf:.2f}). Direct intervention is the gold standard "
                                f"for establishing causality."
                            ),
                            estimated_impact="high" if conf < 0.4 else "medium",
                            required_resources="lab experiment",
                            parameters={
                                "intervention_variable": cause,
                                "outcome_variable": effect,
                                "value_range": [0.5, 1.0, 1.5, 2.0],
                                "n_measurements_per_level": 10,
                            },
                        ),
                    )
                )
        else:
            # No causal graph at all — suggest building one
            suggestions.append(
                (
                    2,  # lower impact — this is exploratory
                    ExperimentSuggestion(
                        description="Establish a causal graph from observational data",
                        rationale=(
                            "No causal graph present in hypothesis metadata. "
                            "Run causal discovery (e.g., PC algorithm) on available data "
                            "to identify potential causal relationships before intervention."
                        ),
                        estimated_impact="medium",
                        required_resources="in silico",
                        parameters={
                            "method": "pc_algorithm",
                            "alpha": 0.05,
                        },
                    ),
                )
            )

        # Check for missing temporal precedence in causal claims
        has_temporal = any(
            p["source"] == "temporal_reasoning" for p in h.provenance
        )
        if not has_temporal and h.domain in ("causality", "mixed"):
            suggestions.append(
                (
                    1,
                    ExperimentSuggestion(
                        description="Collect time-course data to establish temporal precedence",
                        rationale=(
                            "Causal claims benefit from showing that cause precedes effect. "
                            "Time-series data would strengthen this hypothesis."
                        ),
                        estimated_impact="medium",
                        required_resources="lab experiment",
                        parameters={
                            "time_points": list(range(0, 30, 3)),  # every 3 days, 30 days
                            "variables": ["cause", "effect"],
                        },
                    ),
                )
            )

        return suggestions

    def _simulation_suggestions(
        self, h: Hypothesis
    ) -> list[tuple[int, ExperimentSuggestion]]:
        """Suggest parameter refinement when simulation uncertainty is high."""
        suggestions: list[tuple[int, ExperimentSuggestion]] = []
        meta = h.metadata

        # Check for simulation model + parameter ranges
        sim_model = meta.get("simulation_model")
        sim_params = meta.get("simulation_params", {})
        if sim_model:
            # Heuristic: if params are at boundary values, need refinement
            boundary_params = []
            for param, value in sim_params.items():
                if isinstance(value, (int, float)):
                    ref = meta.get("simulation_reference", {}).get(param)
                    if ref is not None and value in (ref * 0.1, ref * 10):
                        boundary_params.append(param)

            if boundary_params:
                suggestions.append(
                    (
                        0,
                        ExperimentSuggestion(
                            description=f"Refine simulation parameters: {', '.join(boundary_params)}",
                            rationale=(
                                f"Parameters {boundary_params} are at extreme values relative "
                                f"to reference ranges. Suggest a parameter sweep to map "
                                f"the response surface more finely."
                            ),
                            estimated_impact="high",
                            required_resources="simulation only",
                            parameters={
                                "parameter_to_sweep": boundary_params[0],
                                "range_multiplier": [0.1, 0.5, 1.0, 2.0, 10.0],
                            },
                        ),
                    )
                )

            # Check for wide prediction intervals (heuristic: no CI stored)
            if "confidence_interval" not in meta and "prediction_sd" in meta:
                suggestions.append(
                    (
                        1,
                        ExperimentSuggestion(
                            description="Run Monte Carlo simulation to establish prediction intervals",
                            rationale=(
                                "No confidence intervals available for simulation predictions. "
                                "Monte Carlo with perturbed parameters would quantify uncertainty."
                            ),
                            estimated_impact="medium",
                            required_resources="simulation only",
                            parameters={
                                "n_simulations": 1000,
                                "parameter_distributions": "normal",
                            },
                        ),
                    )
                )

        return suggestions

    def _temporal_suggestions(
        self, h: Hypothesis
    ) -> list[tuple[int, ExperimentSuggestion]]:
        """Suggest time-series enrichment when temporal model may be underpowered."""
        suggestions: list[tuple[int, ExperimentSuggestion]] = []
        meta = h.metadata

        forecast_horizon = meta.get("forecast_horizon")
        n_time_points = meta.get("n_time_points")
        temporal_model = meta.get("temporal_model")

        if n_time_points is not None and n_time_points < 20:
            suggestions.append(
                (
                    1,
                    ExperimentSuggestion(
                        description=f"Collect more time points (currently {n_time_points})",
                        rationale=(
                            f"Only {n_time_points} time points available. "
                            f"ARIMA/forecasting models benefit from ≥20 observations "
                            f"for stable seasonal decomposition."
                        ),
                        estimated_impact="medium",
                        required_resources="lab experiment",
                        parameters={
                            "additional_time_points_needed": max(0, 20 - n_time_points),
                            "frequency": meta.get("sampling_interval_days", 1),
                        },
                    ),
                )
            )

        if forecast_horizon and forecast_horizon > 2 * (n_time_points or 10):
            suggestions.append(
                (
                    0,
                    ExperimentSuggestion(
                        description=(
                            f"Forecast horizon ({forecast_horizon} days) is >2× the data length. "
                            "Validate with hold-out temporal data."
                        ),
                        rationale=(
                            "Extrapolating far beyond the observed time range produces "
                            "unreliable forecasts. Collecting longer time series or using "
                            "a shorter horizon would improve reliability."
                        ),
                        estimated_impact="high",
                        required_resources="in silico",
                        parameters={
                            "suggested_horizon_days": (n_time_points or 10) * 2,
                        },
                    ),
                )
            )

        return suggestions

    def _spatial_suggestions(
        self, h: Hypothesis
    ) -> list[tuple[int, ExperimentSuggestion]]:
        """Suggest geometry validation when spatial structure is unknown."""
        suggestions: list[tuple[int, ExperimentSuggestion]] = []

        if h.domain == "spatial" and "molecular_geometry" in h.metadata:
            geom = h.metadata["molecular_geometry"]
            if not geom.get("has_3d_coordinates"):
                suggestions.append(
                    (
                        0,
                        ExperimentSuggestion(
                            description="Obtain 3D molecular structure (X-ray crystallography or NMR)",
                            rationale=(
                                "Hypothesis involves spatial/molecular properties but "
                                "no experimental 3D structure is available. "
                                "X-ray crystallography is the gold standard for "
                                "determining precise bond lengths and angles."
                            ),
                            estimated_impact="high",
                            required_resources="lab experiment",
                            parameters={
                                "method": "xray_crystallography",
                                "sample_preparation": "crystallise compound",
                            },
                        ),
                    )
                )
            elif not geom.get("has_chirality_assigned"):
                suggestions.append(
                    (
                        1,
                        ExperimentSuggestion(
                            description="Assign absolute stereochemistry (R/S) to chiral centers",
                            rationale=(
                                "Chiral centers are present but not assigned. "
                                "Electronic circular dichroism (ECD) or VCD can "
                                "determine absolute configuration experimentally."
                            ),
                            estimated_impact="medium",
                            required_resources="lab experiment",
                            parameters={"method": "ecd_spectroscopy"},
                        ),
                    )
                )

        return suggestions

    def _quantum_suggestions(
        self, h: Hypothesis
    ) -> list[tuple[int, ExperimentSuggestion]]:
        """Suggest quantum circuit improvements."""
        suggestions: list[tuple[int, ExperimentSuggestion]] = []
        meta = h.metadata

        qc = meta.get("quantum_circuit")
        if qc:
            depth = meta.get("quantum_depth", 0)
            if depth > 50:
                suggestions.append(
                    (
                        1,
                        ExperimentSuggestion(
                            description=f"Reduce circuit depth (currently {depth})",
                            rationale=(
                                f"Circuit depth of {depth} exceeds typical NISQ device limits "
                                "(≈50 gates). Suggest circuit simplification or transpilation "
                                "with gate fusion and cancellation."
                            ),
                            estimated_impact="medium",
                            required_resources="in silico",
                            parameters={"max_depth": 50, "optimisation_level": 3},
                        ),
                    )
                )
            fidelity = meta.get("estimated_fidelity", 1.0)
            if fidelity < 0.7:
                suggestions.append(
                    (
                        0,
                        ExperimentSuggestion(
                            description=f"Improve circuit fidelity (currently {fidelity:.2f})",
                            rationale=(
                                f"Estimated fidelity {fidelity:.2f} is below 0.70. "
                                "Suggest error mitigation (zero-noise extrapolation) "
                                "or circuit redesign to avoid high-error gates."
                            ),
                            estimated_impact="high",
                            required_resources="in silico",
                            parameters={"error_mitigation": "zne", "scale_factors": [1, 2, 3]},
                        ),
                    )
                )

        return suggestions

    # ── Formatting ──────────────────────────────────────────────────────────

    @staticmethod
    def format_suggestions(suggestions: list[ExperimentSuggestion]) -> str:
        """Render suggestions as a numbered list."""
        if not suggestions:
            return "No experiment suggestions available for this hypothesis."

        impact_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        lines = ["Suggested Experiments", "=" * 50]

        for i, s in enumerate(suggestions, 1):
            emoji = impact_emoji.get(s.estimated_impact, "⚪")
            lines.append(f"\n{i}. {emoji} {s.description}")
            lines.append(f"   Rationale: {s.rationale}")
            lines.append(f"   Impact: {s.estimated_impact.upper()}  |  Resources: {s.required_resources}")
            if s.parameters:
                param_str = ", ".join(
                    f"{k}={v}" for k, v in list(s.parameters.items())[:3]
                )
                lines.append(f"   Parameters: {param_str}")

        lines.append(
            "\n[SIMULATION MODE – Not real data – for hypothesis generation only]"
        )
        return "\n".join(lines)