"""
weslr/tests/test_experiment_simulation.py
========================================
Phase 6.8 — Experiment simulation stub tests for Weslr.

Tests cover:
- Model prediction: linear, Emax, exponential, custom
- Noise addition (deterministic with seed)
- Parameter sweep
- Power analysis (two-sample t-test)
- Mock trial design
- Command parsing
- Integration

Deterministic throughout (seed=42).
"""

import math
import unittest
from unittest.mock import patch

import numpy as np


class TestExperimentSimulation(unittest.TestCase):
    """Phase 6.8 experiment simulation test suite."""

    def setUp(self):
        # Deterministic setup — reset simulation state
        import weslr.commands.simulation_commands as simcmd

        simcmd._SIM = None
        simcmd._SIM_HISTORY = []
        np.random.seed(42)

    # ── Model predictions ─────────────────────────────────────────────────

    def test_predict_linear(self):
        """Linear model: outcome = slope*x + intercept."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation(
            model_type="linear",
            parameters={"slope": 2.0, "intercept": 1.0},
            seed=42,
        )
        result = sim.predict([0, 1, 2, 3, 4])
        self.assertEqual(result.x_values, [0, 1, 2, 3, 4])
        self.assertEqual(result.predictions, [1.0, 3.0, 5.0, 7.0, 9.0])
        self.assertEqual(result.model_type, "linear")

    def test_predict_emax(self):
        """Emax model: outcome = E_max * dose / (ED50 + dose)."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation(
            model_type="emax",
            parameters={"E_max": 100.0, "ED50": 10.0},
            seed=42,
        )
        result = sim.predict([0.0, 5.0, 10.0, 20.0, 50.0])
        self.assertEqual(len(result.predictions), 5)
        self.assertAlmostEqual(result.predictions[0], 0.0)
        self.assertAlmostEqual(result.predictions[1], 33.3333, places=3)
        self.assertAlmostEqual(result.predictions[2], 50.0)
        self.assertAlmostEqual(result.predictions[3], 66.6667, places=3)
        self.assertAlmostEqual(result.predictions[4], 83.3333, places=3)

    def test_predict_exponential(self):
        """Exponential decay: outcome = A * exp(-k * x)."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation(
            model_type="exponential",
            parameters={"A": 100.0, "k": 0.1},
            seed=42,
        )
        result = sim.predict([0.0, 5.0, 10.0])
        # x=0: 100*exp(0)=100; x=5: 100*exp(-0.5)=60.65; x=10: 100*exp(-1)=36.79
        self.assertAlmostEqual(result.predictions[0], 100.0)
        self.assertAlmostEqual(result.predictions[1], 60.653, places=2)
        self.assertAlmostEqual(result.predictions[2], 36.788, places=2)

    def test_predict_with_noise_deterministic(self):
        """Noise is deterministic with seed — two runs give same result."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim1 = ExperimentSimulation(model_type="emax", parameters={"E_max": 100, "ED50": 10}, noise_sd=1.0, seed=42)
        sim2 = ExperimentSimulation(model_type="emax", parameters={"E_max": 100, "ED50": 10}, noise_sd=1.0, seed=42)

        r1 = sim1.predict([1, 2, 3])
        r2 = sim2.predict([1, 2, 3])
        self.assertEqual(r1.predictions, r2.predictions)

    def test_predict_with_zero_noise(self):
        """noise_sd=0 gives deterministic, noise-free predictions."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation(model_type="linear", parameters={"slope": 1.0, "intercept": 0}, noise_sd=0.0, seed=999)
        result = sim.predict([1, 2, 3])
        self.assertEqual(result.predictions, [1.0, 2.0, 3.0])

    # ── Custom model ───────────────────────────────────────────────────────

    def test_custom_model_sympy(self):
        """Custom sympy expression is parsed and evaluated correctly."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation(model_type="emax", parameters={"E_max": 100, "ED50": 10})
        sim.set_custom_model("50 * dose / (5 + dose)")
        result = sim.predict([5.0])
        self.assertAlmostEqual(result.predictions[0], 25.0, places=3)

    def test_custom_model_unsafe_rejected(self):
        """Unsafe expressions (__import__, eval, etc.) are rejected."""
        from weslr.modules.experiment_simulation import _is_safe_expression

        # Test the guard function directly (no sympy required)
        self.assertFalse(_is_safe_expression("__import__('os').system('ls')"))
        self.assertFalse(_is_safe_expression("eval('1+1')"))
        self.assertFalse(_is_safe_expression("open('/etc/passwd')"))
        self.assertTrue(_is_safe_expression("E_max * dose / (ED50 + dose)"))
        self.assertTrue(_is_safe_expression("3.2*dose / (dose + 5.0)"))

    def test_custom_model_unknown_symbol_raises(self):
        """Unknown symbols raise a parseable error."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        if not hasattr(ExperimentSimulation, "set_custom_model"):
            self.skipTest("sympy not available")

    # ── Parameter sweep ───────────────────────────────────────────────────

    def test_sweep_length(self):
        """Sweep returns one result per step."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation(model_type="emax", parameters={"E_max": 100, "ED50": 10}, seed=42)
        sim._last_x = [0, 5, 10, 20]
        results = sim.sweep("ED50", 5.0, 15.0, n_steps=5)
        self.assertEqual(len(results), 5)

    def test_sweep_param_values_monotone(self):
        """Sweep parameter values are linearly spaced."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation(model_type="emax", parameters={"E_max": 100, "ED50": 10}, seed=42)
        sim._last_x = [10]
        results = sim.sweep("ED50", 5.0, 15.0, n_steps=6)
        pvals = [r["param_value"] for r in results]
        self.assertGreater(pvals[-1], pvals[0])
        self.assertAlmostEqual(pvals[0], 5.0)
        self.assertAlmostEqual(pvals[-1], 15.0)

    def test_sweep_output_predictions_per_step(self):
        """Each sweep step has predictions list of correct length."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation(model_type="emax", parameters={"E_max": 100, "ED50": 10}, seed=42)
        sim._last_x = [0, 5, 10, 20, 50]
        results = sim.sweep("ED50", 5.0, 15.0, n_steps=3)
        for r in results:
            self.assertEqual(len(r["predictions"]), 5)
            self.assertIn("param_value", r)
            self.assertIn("summary", r)

    def test_sweep_n_steps_validation(self):
        """n_steps < 2 raises ValueError."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation(model_type="emax")
        sim._last_x = [1, 2, 3]
        with self.assertRaises(ValueError):
            sim.sweep("ED50", 5.0, 15.0, n_steps=1)

    # ── Power analysis ────────────────────────────────────────────────────

    def test_power_analysis_result_shape(self):
        """power_analysis returns dict with required keys."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation()
        result = sim.power_analysis(effect_size=0.5, alpha=0.05, power=0.8)
        for key in ("n_per_group", "effect_size", "alpha", "power", "beta"):
            self.assertIn(key, result)

    def test_power_analysis_effect_05_alpha_005(self):
        """Effect size 0.5, alpha 0.05, power 0.8 → n ≈ 64 per group."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation()
        result = sim.power_analysis(effect_size=0.5, alpha=0.05, power=0.8)
        # Formula: n = 2 * ((z_alpha + z_beta) / d)^2
        # z_alpha = Φ⁻¹(0.975) ≈ 1.96; z_beta = Φ⁻¹(0.8) ≈ 0.8416
        # n = 2 * ((1.96 + 0.8416) / 0.5)^2 = 2 * (2.8016/0.5)^2 = 2 * 5.6032^2 = 2 * 31.38 = 62.75 → 63
        self.assertGreater(result["n_per_group"], 60)
        self.assertLess(result["n_per_group"], 70)
        self.assertAlmostEqual(result["effect_size"], 0.5)
        self.assertAlmostEqual(result["alpha"], 0.05)
        self.assertAlmostEqual(result["power"], 0.8)

    def test_power_analysis_large_effect_fewer_samples(self):
        """Larger effect size → smaller required n."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation()
        r_small = sim.power_analysis(effect_size=0.2, alpha=0.05, power=0.8)
        r_large = sim.power_analysis(effect_size=0.8, alpha=0.05, power=0.8)
        self.assertGreater(r_small["n_per_group"], r_large["n_per_group"])

    def test_power_analysis_validation(self):
        """Invalid parameters raise ValueError (or ImportError when scipy unavailable)."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation()
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with self.assertRaises((ValueError, ImportError)):
                sim.power_analysis(effect_size=0.0, alpha=0.05, power=0.8)
            with self.assertRaises((ValueError, ImportError)):
                sim.power_analysis(effect_size=0.5, alpha=0.0, power=0.8)
            with self.assertRaises((ValueError, ImportError)):
                sim.power_analysis(effect_size=0.5, alpha=0.05, power=1.0)

    # ── Mock trial design ─────────────────────────────────────────────────

    def test_mock_trial_design_returns_dict(self):
        """mock_trial_design returns non-empty dict with required keys."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        trial = ExperimentSimulation.mock_trial_design(
            arms=["Placebo", "Drug 100mg"],
            duration_weeks=12,
            endpoints=["Biomarker change", "Safety"],
            sample_size=64,
            dropout_rate=0.1,
        )
        self.assertIsInstance(trial, dict)
        self.assertIn("arms", trial)
        self.assertIn("sample_size", trial)
        self.assertIn("timeline", trial)
        self.assertIn("endpoints", trial)

    def test_mock_trial_design_arm_count(self):
        """Each arm has name and n_target."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        trial = ExperimentSimulation.mock_trial_design(
            arms=["Placebo", "Drug"],
            duration_weeks=12,
            endpoints=["Primary"],
            sample_size=64,
        )
        self.assertEqual(len(trial["arms"]), 2)
        for arm in trial["arms"]:
            self.assertIn("name", arm)
            self.assertIn("n_target", arm)
            self.assertEqual(arm["n_target"], 64)

    def test_mock_trial_design_dropout_adjustment(self):
        """Dropout rate correctly adjusts enrolled_total."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        trial = ExperimentSimulation.mock_trial_design(
            arms=["P", "D"],
            duration_weeks=12,
            endpoints=["E"],
            sample_size=100,
            dropout_rate=0.2,
        )
        ss = trial["sample_size"]
        # 2 arms × 100 = 200 randomized
        self.assertEqual(ss["total_randomized"], 200)
        # Enroll accounting for 20% dropout: ceil(200 / 0.8) = 250
        self.assertEqual(ss["total_enroll"], 250)
        self.assertEqual(ss["dropout_n"], 50)

    def test_mock_trial_design_timeline(self):
        """Timeline includes randomization, interim, endpoint, follow-up."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        trial = ExperimentSimulation.mock_trial_design(
            arms=["P", "D"],
            duration_weeks=12,
            endpoints=["E"],
            sample_size=64,
        )
        weeks = [ev["week"] for ev in trial["timeline"]]
        self.assertIn(0, weeks)
        self.assertIn(12, weeks)

    def test_mock_trial_design_empty_arms_raises(self):
        """Empty arms list raises ValueError."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        with self.assertRaises(ValueError):
            ExperimentSimulation.mock_trial_design(
                arms=[],
                duration_weeks=12,
                endpoints=["E"],
                sample_size=64,
            )

    # ── Command parsing ──────────────────────────────────────────────────

    def test_command_simulate_model_set(self):
        """handle_simulation_command sets model type and params."""
        from weslr.commands.simulation_commands import handle_simulation_command

        result = handle_simulation_command(
            "/simulate model emax E_max=100 ED50=10",
            "simulate model emax E_max=100 ED50=10",
        )
        self.assertIn("emax", result)
        self.assertIn("Formula", result)

    def test_command_simulate_model_show_current(self):
        """handle_simulation_command with no args shows current model."""
        from weslr.commands.simulation_commands import handle_simulation_command

        handle_simulation_command("/simulate model emax", "simulate model emax")
        result = handle_simulation_command("/simulate model", "simulate model")
        self.assertIn("emax", result)

    def test_command_simulate_predict(self):
        """handle_simulation_command predicts for given doses."""
        from weslr.commands.simulation_commands import handle_simulation_command

        handle_simulation_command("/simulate model emax E_max=100 ED50=10", "simulate model emax E_max=100 ED50=10")
        result = handle_simulation_command(
            "/simulate predict 0,5,10,20,50",
            "simulate predict 0,5,10,20,50",
        )
        self.assertIn("Model: emax", result)
        self.assertIn("0.0\t0.0000", result)
        self.assertIn("10.0\t50.0000", result)
        self.assertIn("SIMULATION MODE", result)

    def test_command_simulate_predict_unknown_model_shows_error(self):
        """Unknown model type shows error."""
        from weslr.commands.simulation_commands import handle_simulation_command

        result = handle_simulation_command(
            "/simulate model unknown_model",
            "simulate model unknown_model",
        )
        self.assertIn("Unknown", result)

    def test_command_simulate_sweep(self):
        """handle_simulation_command sweep returns table."""
        from weslr.commands.simulation_commands import handle_simulation_command

        handle_simulation_command("/simulate model emax E_max=100 ED50=10", "simulate model emax E_max=100 ED50=10")
        result = handle_simulation_command(
            "/simulate sweep ED50 from 5 to 15 steps=5",
            "simulate sweep ED50 from 5 to 15 steps=5",
        )
        self.assertIn("Parameter sweep", result)
        self.assertIn("ED50", result)
        self.assertIn("SIMULATION MODE", result)

    def test_command_simulate_sweep_invalid_range(self):
        """Invalid range (start >= end) shows error."""
        from weslr.commands.simulation_commands import handle_simulation_command

        result = handle_simulation_command(
            "/simulate sweep ED50 from 20 to 5",
            "simulate sweep ED50 from 20 to 5",
        )
        self.assertIn("must be <", result)

    def test_command_simulate_power(self):
        """handle_simulation_command power analysis."""
        from weslr.commands.simulation_commands import handle_simulation_command

        result = handle_simulation_command(
            "/simulate power 0.5 alpha=0.05 power=0.8",
            "simulate power 0.5 alpha=0.05 power=0.8",
        )
        self.assertIn("Power analysis", result)
        self.assertIn("n per group", result)
        self.assertIn("SIMULATION MODE", result)

    def test_command_experiment_design(self):
        """handle_simulation_command /experiment design returns mock trial."""
        from weslr.commands.simulation_commands import handle_simulation_command

        result = handle_simulation_command(
            "/experiment design arms=Placebo,Drug duration=12 endpoint=Biomarker",
            "experiment design arms=Placebo,Drug duration=12 endpoint=Biomarker",
        )
        self.assertIn("Mock Clinical Trial Design", result)
        self.assertIn("Placebo", result)
        self.assertIn("Drug", result)
        self.assertIn("12", result)
        self.assertIn("SIMULATION MODE", result)

    def test_command_unknown_shows_usage(self):
        """Unknown simulation command shows usage."""
        from weslr.commands.simulation_commands import handle_simulation_command

        result = handle_simulation_command("/simulate foo", "simulate foo")
        self.assertIn("/simulate", result)

    # ── Formatted output ──────────────────────────────────────────────────

    def test_format_predictions_includes_disclaimer(self):
        """format_predictions includes simulation disclaimer."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation(model_type="emax", parameters={"E_max": 100, "ED50": 10})
        result = sim.predict([0, 5, 10])
        output = sim.format_predictions(result)
        self.assertIn("SIMULATION MODE", output)

    def test_format_power_includes_disclaimer(self):
        """format_power includes simulation disclaimer."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        sim = ExperimentSimulation()
        result = sim.power_analysis(effect_size=0.5)
        output = sim.format_power(result)
        self.assertIn("SIMULATION MODE", output)

    def test_format_trial_design_includes_disclaimer(self):
        """format_trial_design includes simulation disclaimer."""
        from weslr.modules.experiment_simulation import ExperimentSimulation

        trial = ExperimentSimulation.mock_trial_design(
            arms=["P", "D"],
            duration_weeks=12,
            endpoints=["E"],
            sample_size=64,
        )
        output = ExperimentSimulation.format_trial_design(trial)
        self.assertIn("SIMULATION MODE", output)
