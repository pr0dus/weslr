"""
weslr/modules/report_generator.py
===================================
Phase 7 — Report Generator: human-readable and JSON hypothesis reports.

Author: OCC (WESLR governed intelligence) — Phase 7
"""

from __future__ import annotations

import json
import textwrap
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Optional

from .hypothesis_repository import Hypothesis


class ReportGenerator:
    """Generates formatted reports from hypotheses and their metadata."""

    def generate_report(
        self,
        hypothesis: Hypothesis,
        format: str = "text",
        include_suggestions: bool = True,
    ) -> str | dict:
        """Generate a report for a hypothesis.

        Parameters
        ----------
        hypothesis : Hypothesis
            The hypothesis to report on.
        format : str
            'text' (human-readable) or 'json' (structured dict).
        include_suggestions : bool
            Whether to include experiment suggestions (skipped in JSON for
            portability; caller can fetch separately).

        Returns
        -------
        str (format='text') or dict (format='json')
        """
        if format == "json":
            return self._generate_json(hypothesis)
        return self._generate_text(hypothesis, include_suggestions)

    # ── Text format ─────────────────────────────────────────────────────────

    def _generate_text(
        self, h: Hypothesis, include_suggestions: bool
    ) -> str:
        lines = [
            self._section_rule(),
            f"  WESLR HYPOTHESIS REPORT — {h.id[:8]}",
            self._section_rule(),
            "",
            "IDENTIFICATION",
            f"  ID:         {h.id}",
            f"  Title:      {h.title}",
            f"  Status:     {h.status.upper()}",
            f"  Domain:     {h.domain}",
            f"  Confidence: {h.confidence:.2f} ({self._confidence_label(h.confidence)})",
            f"  Created:    {h.created_at.strftime('%Y-%m-%d %H:%M UTC') if h.created_at else 'unknown'}",
            f"  Updated:    {h.updated_at.strftime('%Y-%m-%d %H:%M UTC') if h.updated_at else 'unknown'}",
            "",
        ]

        if h.description:
            lines.extend(["DESCRIPTION", textwrap.fill(h.description, width=70, subsequent_indent="  "), ""])

        if h.provenance:
            lines.extend(["PROVENANCE TRAIL", self._format_provenance(h.provenance), ""])

        if h.metadata:
            lines.extend(["EVIDENCE & METADATA", self._format_metadata(h.metadata), ""])

        if include_suggestions:
            suggestions = self._get_suggestions(h)
            if suggestions:
                lines.extend(["SUGGESTED NEXT EXPERIMENTS", suggestions, ""])

        lines.extend([
            self._section_rule(),
            "END OF REPORT",
            "",
            "This report is generated from simulated hypotheses – not for real-world decision making.",
            "[SIMULATION MODE – Not real data – for hypothesis generation only]",
        ])
        return "\n".join(lines)

    def _section_rule(self) -> str:
        return "=" * 68

    def _confidence_label(self, c: float) -> str:
        if c >= 0.8:
            return "HIGH"
        if c >= 0.5:
            return "MEDIUM"
        return "LOW"

    def _format_provenance(self, provenance: list[dict]) -> str:
        if not provenance:
            return "  (no provenance recorded)"
        lines = []
        for i, p in enumerate(provenance, 1):
            ts = p.get("timestamp", "")
            ts_str = ts[11:16] if len(ts) > 16 else ts  # HH:MM only
            source = p.get("source", "unknown")
            action = p.get("action", "?")
            params = p.get("parameters", {})
            param_str = ", ".join(f"{k}={v}" for k, v in list(params.items())[:4])
            lines.append(
                f"  {i}. [{source}] {action}"
                + (f" ({param_str})" if param_str else "")
                + (f" @ {ts_str}" if ts_str else "")
            )
        return "\n".join(lines)

    def _format_metadata(self, meta: dict) -> str:
        lines = []
        for key, value in meta.items():
            if key in ("causal_graph",):
                lines.append(f"  {key}: (graph with {len(value)} edges)")
            elif key in ("evidence",):
                lines.append(f"  {key}: {len(value)} evidence item(s)")
            elif key == "simulation_params":
                lines.append(f"  {key}: {json.dumps(value)}")
            elif isinstance(value, dict):
                lines.append(f"  {key}: (dict with {len(value)} keys)")
            elif isinstance(value, list):
                lines.append(f"  {key}: {len(value)} item(s)")
            else:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines) if lines else "  (no metadata)"

    def _get_suggestions(self, h: Hypothesis) -> str:
        try:
            from .experiment_suggester import ExperimentSuggester
            suggester = ExperimentSuggester()
            suggestions = suggester.suggest_next_experiments(h, max_suggestions=3)
            return ExperimentSuggester.format_suggestions(suggestions)
        except Exception:
            return "  (suggestions unavailable)"

    # ── JSON format ─────────────────────────────────────────────────────────

    def _generate_json(self, h: Hypothesis) -> dict[str, Any]:
        return {
            "report_id": f"rpt_{h.id[:8]}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "hypothesis": {
                "id": h.id,
                "title": h.title,
                "description": h.description,
                "domain": h.domain,
                "confidence": h.confidence,
                "confidence_label": self._confidence_label(h.confidence),
                "status": h.status,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "updated_at": h.updated_at.isoformat() if h.updated_at else None,
            },
            "provenance": [
                {
                    "source": p.get("source"),
                    "timestamp": p.get("timestamp"),
                    "action": p.get("action"),
                    "parameters": p.get("parameters", {}),
                }
                for p in h.provenance
            ],
            "evidence": [
                {"key": e.get("key"), "value": e.get("value"), "source": e.get("source")}
                for e in h.metadata.get("evidence", [])
            ],
            "metadata": {
                k: v
                for k, v in h.metadata.items()
                if k != "evidence"
            },
            "safety_warning": (
                "This report is generated from simulated hypotheses – not for "
                "real-world decision making. [SIMULATION MODE – Not real data]"
            ),
        }