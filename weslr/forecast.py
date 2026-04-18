# forecast.py - Self-Architecture Core v10: Architectural Simulation / Forecast Layer
# Allow WESLR to forecast likely system effects of adopting a suggestion or scenario.
# Additive only, operator-first, reversible, governed.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ForecastTimeHorizon(str, Enum):
    """Time horizons for forecasting."""
    SHORT_TERM = "short_term"   # 0-4 weeks
    MEDIUM_TERM = "medium_term" # 1-3 months
    LONG_TERM = "long_term"     # 3-6+ months


class ImpactType(str, Enum):
    """Types of impacts."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class CoherenceImpact(str, Enum):
    """Impact on system coherence."""
    INCREASES = "increases"
    DECREASES = "decreases"
    NO_CHANGE = "no_change"


@dataclass
class ForecastEffect:
    """A forecasted effect of a suggestion or change."""
    
    category: str  # e.g., "risk", "effort", "coherence"
    impact_type: str  # positive, negative, neutral
    magnitude: float  # -1 to 1
    confidence: float  # 0 to 1
    description: str
    affected_subsystems: List[str] = field(default_factory=list)
    timeline: str = ForecastTimeHorizon.SHORT_TERM.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "impact_type": self.impact_type,
            "magnitude": self.magnitude,
            "confidence": self.confidence,
            "description": self.description,
            "affected_subsystems": self.affected_subsystems,
            "timeline": self.timeline,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ForecastEffect:
        data["affected_subsystems"] = data.get("affected_subsystems", [])
        return cls(**data)


@dataclass
class SubsystemForecast:
    """Forecast for a specific subsystem."""
    
    subsystem: str
    forecasted_effects: List[ForecastEffect] = field(default_factory=list)
    net_impact: float = 0.0  # -1 to 1
    confidence: float = 0.0
    timeline: str = ForecastTimeHorizon.MEDIUM_TERM.value

    def add_effect(self, effect: ForecastEffect) -> None:
        """Add an effect to this subsystem forecast."""
        self.forecasted_effects.append(effect)
        self.net_impact += effect.magnitude * effect.confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subsystem": self.subsystem,
            "forecasted_effects": [e.to_dict() for e in self.forecasted_effects],
            "net_impact": self.net_impact,
            "confidence": self.confidence,
            "timeline": self.timeline,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SubsystemForecast:
        data["forecasted_effects"] = [
            ForecastEffect.from_dict(e) for e in data.get("forecasted_effects", [])
        ]
        return cls(**data)


@dataclass
class ForecastSummary:
    """Summary of forecast results."""
    
    total_positive_effects: int = 0
    total_negative_effects: int = 0
    net_impact: float = 0.0
    coherence_impact: str = CoherenceImpact.NO_CHANGE.value
    short_term_benefit: float = 0.0
    long_term_benefit: float = 0.0
    maintenance_impact: float = 0.0  # -1 (worse) to 1 (better)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_positive_effects": self.total_positive_effects,
            "total_negative_effects": self.total_negative_effects,
            "net_impact": self.net_impact,
            "coherence_impact": self.coherence_impact,
            "short_term_benefit": self.short_term_benefit,
            "long_term_benefit": self.long_term_benefit,
            "maintenance_impact": self.maintenance_impact,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ForecastSummary:
        return cls(**data)


@dataclass
class ArchitecturalForecast:
    """Complete forecast for a suggestion or scenario."""
    
    forecast_id: str
    title: str
    description: str
    domain: str
    
    # Forecast results
    effects: List[ForecastEffect] = field(default_factory=list)
    subsystem_forecasts: List[SubsystemForecast] = field(default_factory=list)
    summary: ForecastSummary = field(default_factory=ForecastSummary)
    
    # Context
    suggestion_id: Optional[str] = None
    scenario_id: Optional[str] = None
    reference_decisions: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "forecast_id": self.forecast_id,
            "title": self.title,
            "description": self.description,
            "domain": self.domain,
            "effects": [e.to_dict() for e in self.effects],
            "subsystem_forecasts": [s.to_dict() for s in self.subsystem_forecasts],
            "summary": self.summary.to_dict(),
            "suggestion_id": self.suggestion_id,
            "scenario_id": self.scenario_id,
            "reference_decisions": self.reference_decisions,
            "created_at": self.created_at,
            "author": self.author,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ArchitecturalForecast:
        data["effects"] = [ForecastEffect.from_dict(e) for e in data.get("effects", [])]
        data["subsystem_forecasts"] = [
            SubsystemForecast.from_dict(s) for s in data.get("subsystem_forecasts", [])
        ]
        data["summary"] = ForecastSummary.from_dict(data.get("summary", {}))
        data["reference_decisions"] = data.get("reference_decisions", [])
        return cls(**data)

    def get_forecast_summary(self) -> str:
        """Generate a human-readable forecast summary."""
        parts = []
        parts.append(f"Net impact: {'positive' if self.summary.net_impact > 0 else 'negative'} ({self.summary.net_impact:.2f})")
        parts.append(f"Positive effects: {self.summary.total_positive_effects}")
        parts.append(f"Negative effects: {self.summary.total_negative_effects}")
        parts.append(f"Short-term benefit: {self.summary.short_term_benefit:.2f}")
        parts.append(f"Long-term benefit: {self.summary.long_term_benefit:.2f}")
        parts.append(f"Confidence: {self.confidence:.2f}")
        return "; ".join(parts)


class ForecastEngine:
    """Engine for generating architectural forecasts."""

    def __init__(self):
        self.prior_decisions: List[Dict[str, Any]] = []
        self.subsystem_info: Dict[str, Any] = {}

    def set_prior_decisions(self, decisions: List[Dict[str, Any]]) -> None:
        """Set prior decisions for reference."""
        self.prior_decisions = decisions

    def set_subsystem_info(self, info: Dict[str, Any]) -> None:
        """Set subsystem information for forecasting."""
        self.subsystem_info = info

    def forecast_suggestion(
        self,
        title: str,
        description: str,
        domain: str,
        affected_subsystems: List[str] = None,
        suggestion_id: Optional[str] = None,
    ) -> ArchitecturalForecast:
        """Forecast the effect of a suggestion."""
        forecast_id = f"fcst-{suggestion_id[-4:] if suggestion_id else 'temp'}"

        # Simulate forecast based on suggestion characteristics
        effects = []
        subsystem_forecasts = []

        # Analyze subsystem impact
        for subsystem in affected_subsystems or []:
            # Simulate positive effects
            if subsystem in ["state", "continuity"]:
                effects.append(ForecastEffect(
                    category="efficiency",
                    impact_type="positive",
                    magnitude=0.6,
                    confidence=0.7,
                    description=f"Improved {subsystem} efficiency",
                    affected_subsystems=[subsystem],
                ))
            elif subsystem == "state":
                effects.append(ForecastEffect(
                    category="risk",
                    impact_type="negative",
                    magnitude=-0.4,
                    confidence=0.6,
                    description=f"Potential state complexity increase",
                    affected_subsystems=[subsystem],
                ))

        # General positive effect
        effects.append(ForecastEffect(
            category="functionality",
            impact_type="positive",
            magnitude=0.5,
            confidence=0.8,
            description=f"New {title} capability",
        ))

        # Estimate subsystem forecasts
        for subsystem in affected_subsystems or []:
            subsystem_forecasts.append(SubsystemForecast(
                subsystem=subsystem,
                net_impact=0.3,
                confidence=0.6,
            ))

        # Calculate summary
        positive_count = sum(1 for e in effects if e.impact_type == "positive")
        negative_count = sum(1 for e in effects if e.impact_type == "negative")
        net_impact = sum(e.magnitude * e.confidence for e in effects)

        summary = ForecastSummary(
            total_positive_effects=positive_count,
            total_negative_effects=negative_count,
            net_impact=net_impact,
            short_term_benefit=min(max(net_impact, 0), 1),
            long_term_benefit=min(max(net_impact * 0.8, 0), 1),
            maintenance_impact=-0.2,  # Slight maintenance burden increase
            confidence=min(max(abs(net_impact), 0.3), 0.9),
        )

        return ArchitecturalForecast(
            forecast_id=forecast_id,
            title=title,
            description=description,
            domain=domain,
            effects=effects,
            subsystem_forecasts=subsystem_forecasts,
            summary=summary,
            suggestion_id=suggestion_id,
        )

    def forecast_scenario(
        self,
        title: str,
        description: str,
        domain: str,
        scenarios: List[Dict[str, Any]],
        scenario_id: Optional[str] = None,
    ) -> ArchitecturalForecast:
        """Forecast the effect of a scenario (multiple suggestions)."""
        forecast_id = f"fcst-{scenario_id[-4:] if scenario_id else 'temp'}"

        # Aggregate effects from scenario suggestions
        effects = []
        subsystem_forecasts = []

        for i, scenario in enumerate(scenarios):
            affected = scenario.get("affected_subsystems", [])
            title = scenario.get("title", f"Scenario {i+1}")

            for subsystem in affected:
                effects.append(ForecastEffect(
                    category="change",
                    impact_type="positive",
                    magnitude=0.4,
                    confidence=0.6,
                    description=f"Scenario change in {subsystem}",
                    affected_subsystems=[subsystem],
                ))

        # Calculate summary
        positive_count = sum(1 for e in effects if e.impact_type == "positive")
        negative_count = sum(1 for e in effects if e.impact_type == "negative")
        net_impact = sum(e.magnitude * e.confidence for e in effects)

        summary = ForecastSummary(
            total_positive_effects=positive_count,
            total_negative_effects=negative_count,
            net_impact=net_impact,
            short_term_benefit=min(max(net_impact, 0), 1),
            long_term_benefit=min(max(net_impact * 0.9, 0), 1),
            maintenance_impact=-0.3,
            confidence=min(max(abs(net_impact), 0.4), 0.85),
        )

        return ArchitecturalForecast(
            forecast_id=forecast_id,
            title=title,
            description=description,
            domain=domain,
            effects=effects,
            subsystem_forecasts=subsystem_forecasts,
            summary=summary,
            scenario_id=scenario_id,
        )

    def generate_forecast_json(
        self,
        title: str,
        description: str,
        domain: str,
        affected_subsystems: List[str] = None,
        suggestion_id: Optional[str] = None,
    ) -> str:
        """Generate forecast and return as JSON string."""
        forecast = self.forecast_suggestion(
            title, description, domain, affected_subsystems, suggestion_id
        )
        return json.dumps(forecast.to_dict(), indent=2)


def forecast_suggestion(
    title: str,
    description: str,
    domain: str,
    affected_subsystems: List[str] = None,
    suggestion_id: Optional[str] = None,
) -> ArchitecturalForecast:
    """Convenience function to forecast a suggestion."""
    engine = ForecastEngine()
    return engine.forecast_suggestion(
        title, description, domain, affected_subsystems, suggestion_id
    )


def forecast_scenario(
    title: str,
    description: str,
    domain: str,
    scenarios: List[Dict[str, Any]],
    scenario_id: Optional[str] = None,
) -> ArchitecturalForecast:
    """Convenience function to forecast a scenario."""
    engine = ForecastEngine()
    return engine.forecast_scenario(
        title, description, domain, scenarios, scenario_id
    )
