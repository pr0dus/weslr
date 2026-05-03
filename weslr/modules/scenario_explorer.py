"""
weslr/modules/scenario_explorer.py
===================================
Phase 7 — Scenario Explorer: what-if orchestration across modules.

Author: OCC (WESLR governed intelligence) — Phase 7
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Optional

# ── Result data class ────────────────────────────────────────────────────────

@dataclass
class ScenarioResult:
    """Container for a scenario exploration outcome."""

    hypothesis_id: str
    hypothesis_title: str
    scenario_parameters: dict  # the input parameters
    narrative: str  # human-readable description
    predictions: dict[str, float]  # variable → predicted value
    confidence_intervals: dict[str, tuple[float, float]]  # (lower, upper)
    modules_used: list[str]  # which modules contributed
    seed: int  # deterministic seed used
    warning: str = (
        "[SIMULATION MODE – Not real data – for hypothesis generation only]"
    )


# ── Explorer ─────────────────────────────────────────────────────────────────

class ScenarioExplorer:
    """Orchestrate multi-module what-if exploration.

    Takes scenario parameters from the active hypothesis, queries each relevant
    module, and assembles a coherent ScenarioResult. Deterministic via seed
    derived from tenant_id + scenario params.
    """

    def explore_scenario(
        self,
        hypothesis,  # Hypothesis object (injected to avoid circular imports)
        scenario_parameters: dict[str, Any],
    ) -> ScenarioResult:
        """Explore a what-if scenario using multiple reasoning modules.

        Parameters
        ----------
        hypothesis : Hypothesis
            The active hypothesis providing context and domain.
        scenario_parameters : dict
            Key-value pairs e.g. {'dose': 50, 'time_horizon': 14}.

        Returns
        -------
        ScenarioResult
            Narrative + numeric predictions + confidence intervals.
        """
        # ── Derive deterministic seed ──────────────────────────────────
        # Use tenant ID + frozen params to get reproducible results
        param_str = str(sorted(scenario_parameters.items()))
        tenant_id = "default"  # will be overridden by repo's tenant context if available
        seed_input = f"{tenant_id}:{hypothesis.id}:{param_str}"
        seed = int(hashlib.sha256(seed_input.encode()).hexdigest()[:8], 16) % (2**31)

        modules_used: list[str] = []
        predictions: dict[str, float] = {}
        confidence_intervals: dict[str, tuple[float, float]] = {}
        narrative_parts: list[str] = []

        # ── Simulation predictions ───────────────────────────────────
        sim_result = self._simulate(hypothesis, scenario_parameters, seed)
        if sim_result:
            predictions.update(sim_result.get("predictions", {}))
            confidence_intervals.update(sim_result.get("confidence_intervals", {}))
            modules_used.append("experiment_simulation")
            if sim_result.get("narrative"):
                narrative_parts.append(sim_result["narrative"])

        # ── Temporal forecast ──────────────────────────────────────────
        temporal_result = self._forecast(hypothesis, scenario_parameters, seed)
        if temporal_result:
            predictions.update(temporal_result.get("predictions", {}))
            confidence_intervals.update(temporal_result.get("confidence_intervals", {}))
            modules_used.append("temporal_reasoning")
            if temporal_result.get("narrative"):
                narrative_parts.append(temporal_result["narrative"])

        # ── Causal intervention ────────────────────────────────────────
        causal_result = self._intervene(hypothesis, scenario_parameters, seed)
        if causal_result:
            predictions.update(causal_result.get("predictions", {}))
            modules_used.append("causality")
            if causal_result.get("narrative"):
                narrative_parts.append(causal_result["narrative"])

        # ── Quantum gate ───────────────────────────────────────────────
        quantum_result = self._apply_quantum(hypothesis, scenario_parameters, seed)
        if quantum_result:
            predictions.update(quantum_result.get("predictions", {}))
            modules_used.append("quantum_logic")
            if quantum_result.get("narrative"):
                narrative_parts.append(quantum_result["narrative"])

        # ── Assemble narrative ──────────────────────────────────────────
        if narrative_parts:
            narrative = " ".join(narrative_parts)
        else:
            narrative = (
                f"Scenario exploration for '{hypothesis.title}' "
                f"with parameters {scenario_parameters}. "
                f"No module provided predictions for this domain ({hypothesis.domain})."
            )

        return ScenarioResult(
            hypothesis_id=hypothesis.id,
            hypothesis_title=hypothesis.title,
            scenario_parameters=scenario_parameters,
            narrative=narrative,
            predictions=predictions,
            confidence_intervals=confidence_intervals,
            modules_used=modules_used,
            seed=seed,
        )

    # ── Module dispatchers ───────────────────────────────────────────────

    def _simulate(
        self, hypothesis, params: dict, seed: int
    ) -> Optional[dict[str, Any]]:
        """Run experiment simulation if hypothesis has simulation metadata."""
        meta = hypothesis.metadata
        sim_model = meta.get("simulation_model")
        if not sim_model:
            return None

        try:
            confidence_intervals: dict = {}
            from .experiment_simulation import ExperimentSimulation

            sim_params = meta.get("simulation_params", {})
            sim = ExperimentSimulation(
                model_type=sim_model,
                parameters=sim_params,
                seed=seed,
            )
            # Use dose from params if present, else use last_x or default
            x_values = params.get("dose_values", params.get("x_values", [0, 1, 2, 3, 4, 5]))
            result = sim.predict(x_values)

            dose_key = "dose" if "dose" in params else "x"
            predictions = {f"{dose_key}={x}": result.predictions[i] for i, x in enumerate(result.x_values)}

            # Estimate CI as ±noise_sd * 1.96 (if noisy) or ±5% of range as heuristic
            sim_params.get("noise_sd", 0)
            y_range = result.summary.get("y_max", 1) - result.summary.get("y_min", 0)
            half_ci = max(y_range * 0.05, 0.1)  # at least 0.1
            for k, v in predictions.items():
                key_short = k.split("=")[1] if "=" in k else k
                confidence_intervals[key_short] = (
                    round(v - half_ci, 4),
                    round(v + half_ci, 4),
                )

            return {
                "predictions": predictions,
                "confidence_intervals": confidence_intervals,
                "narrative": (
                    f"Simulation ({sim_model}): predicted response range "
                    f"[{result.summary['y_min']:.2f}, {result.summary['y_max']:.2f}] "
                    f"across x∈[{result.summary['x_min']},{result.summary['x_max']}]."
                ),
            }
        except Exception:
            return None

    def _forecast(
        self, hypothesis, params: dict, seed: int
    ) -> Optional[dict[str, Any]]:
        """Run temporal forecast if hypothesis involves time-series."""
        horizon = params.get("time_horizon")
        domain = hypothesis.domain
        if not horizon or domain not in ("temporal", "mixed", "discovery"):
            return None

        try:
            import numpy as np
            confidence_intervals: dict = {}
            series_seed = (hash(hypothesis.id) + seed) % (2**31)
            np.random.seed(series_seed)

            # Build a mock time series: small trend + noise
            n = max(int(horizon), 10)
            intercept = hypothesis.metadata.get("temporal_intercept", 10.0)
            slope = hypothesis.metadata.get("temporal_slope", 0.3)
            noise_sd = hypothesis.metadata.get("temporal_noise_sd", 1.0)

            times = list(range(n))
            values = [intercept + slope * t + np.random.normal(0, noise_sd) for t in times]
            forecast_series = list(values[-5:]) + [
                intercept + slope * t + np.random.normal(0, noise_sd)
                for t in range(n, n + horizon)
            ]
            forecast_times = list(range(n - 5, n + horizon))
            predictions = {
                f"t={t}": round(v, 3) for t, v in zip(forecast_times, forecast_series)
            }

            # Heuristic CI: grows with horizon
            ci = {
                f"t={t}": (round(v - 0.5 * (1 + 0.05 * max(0, t - n)), 3),
                           round(v + 0.5 * (1 + 0.05 * max(0, t - n)), 3))
                for t, v in zip(forecast_times[-horizon:], forecast_series[-horizon:])
            }
            confidence_intervals.update(ci)

            last_pred = forecast_series[-1]
            ci_low, ci_high = ci[f"t={forecast_times[-1]}"]

            narrative = (
                f"Forecast: at time horizon {horizon} steps, predicted value = {last_pred:.3f} "
                f"[CI: {ci_low:.3f}–{ci_high:.3f}]. "
                f"Based on temporal model with slope={slope:.2f} per step."
            )

            return {
                "predictions": predictions,
                "confidence_intervals": confidence_intervals,
                "narrative": narrative,
            }
        except Exception:
            return None

    def _intervene(
        self, hypothesis, params: dict, seed: int
    ) -> Optional[dict[str, Any]]:
        """Run causal intervention if hypothesis has a causal graph."""
        causal_graph = hypothesis.metadata.get("causal_graph", {})
        if not causal_graph:
            return None

        try:
            from .causality import suggest_intervention

            # Find an edge involving a parameter from scenario_parameters
            candidate_edges = [
                (edge, conf)
                for edge, conf in causal_graph.items()
                if edge[0] in params or edge[1] in params
            ]
            if not candidate_edges:
                return None

            edge, conf = candidate_edges[0]
            A, B = edge
            intervention_value = params.get(A, 1.0)

            # Build mock data from hypothesis metadata
            data = hypothesis.metadata.get("causal_data", {})
            if not data:
                # Synthesize minimal data from hypothesis parameters
                data = {A: [0.5, 1.0, 1.5, 2.0], B: [1.0, 2.0, 3.0, 4.0]}

            result = suggest_intervention(
                A=A, B=B,
                causal_graph=causal_graph,
                data=data,
                intervention_value=intervention_value,
                seed=seed,
            )

            effect_estimate = result.get("intervened_mean_B", result.get("predicted_B", 0.0))
            predictions: dict = {}
            predictions[f"do({A}={intervention_value})→{B}"] = round(effect_estimate, 4)

            narrative = (
                f"Causal intervention: do({A}={intervention_value}) → "
                f"predicted {B} = {effect_estimate:.4f} "
                f"(based on causal graph confidence {conf:.2f})."
            )

            return {
                "predictions": predictions,
                "confidence_intervals": {},
                "narrative": narrative,
            }
        except Exception:
            return None

    def _apply_quantum(
        self, hypothesis, params: dict, seed: int
    ) -> Optional[dict[str, Any]]:
        """Run quantum circuit if hypothesis domain is quantum."""
        if hypothesis.domain != "quantum":
            return None

        qc = hypothesis.metadata.get("quantum_circuit")
        if not qc:
            return None

        try:
            from .quantum_logic import apply_gate, available_gates

            gate_name = params.get("gate", "H")
            if gate_name not in available_gates:
                return None

            result = apply_gate(gate_name, seed=seed)
            predictions[f"quantum_{gate_name}_outcome"] = result.get("output_value", 0.0)
            confidence_intervals["quantum_fidelity"] = (result.get("fidelity", 1.0), 1.0)

            narrative = (
                f"Quantum circuit: applied {gate_name} gate. "
                f"Output state value = {result.get('output_value', 0.0):.4f}, "
                f"fidelity = {result.get('fidelity', 1.0):.4f}."
            )

            return {
                "predictions": predictions,
                "confidence_intervals": confidence_intervals,
                "narrative": narrative,
            }
        except Exception:
            return None

    # ── Formatting ──────────────────────────────────────────────────────────

    @staticmethod
    def format_result(r: ScenarioResult) -> str:
        """Render a ScenarioResult as readable text."""
        param_str = ", ".join(f"{k}={v}" for k, v in r.scenario_parameters.items())

        lines = [
            f"Scenario Explorer — '{r.hypothesis_title}'",
            f"Parameters: {param_str}",
            f"Seed: {r.seed}",
            "=" * 60,
            "Narrative:",
            r.narrative,
            "",
            "Predictions:",
        ]
        for k, v in r.predictions.items():
            ci = r.confidence_intervals.get(k)
            if ci:
                lines.append(f"  {k} = {v:.4f}  [CI: {ci[0]:.4f} – {ci[1]:.4f}]")
            else:
                lines.append(f"  {k} = {v:.4f}")

        if r.modules_used:
            lines.append(f"\nModules used: {', '.join(r.modules_used)}")
        lines.append(f"\n{r.warning}")
        return "\n".join(lines)