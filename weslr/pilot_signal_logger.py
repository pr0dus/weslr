"""Weslr Pilot Signal Logger (v1)

Real-time signal logging for the first pilot cohort.
Tracks all key signals for decision making.

Signals tracked:
- Trust score
- Explanation clarity score
- Continuity success rate
- Weak-prompt recovery rate
- Failure recovery incidents
- Rollback triggers
- Red-team incident triggers
- Operator intervention rate
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


__all__ = ["PilotSignalLogger", "create_pilot_logger"]


class PilotSignalLogger:
    """Logger for pilot cohort signals.
    
    Real-time signal capture for Day 0 - Day 7 of pilot.
    All data is persisted for analysis and audit.
    """

    def __init__(self, log_dir: str = "continuity/pilot_signals"):
        self.log_dir = Path(log_dir)
        self.signals_dir = self.log_dir / "signals"
        self.events_dir = self.log_dir / "events"
        self.user_events_file = self.log_dir / "user_events.json"
        self.interventions_file = self.log_dir / "interventions.json"
        self.redteam_file = self.log_dir / "redteam_events.json"
        
        # Create directories
        self.signals_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize files
        self._init_file(self.user_events_file, {"events": []})
        self._init_file(self.interventions_file, {"interventions": []})
        self._init_file(self.redteam_file, {"events": []})
        
        # Trust score tracking
        self.trust_history_file = self.signals_dir / "trust_score.json"
        self._init_file(self.trust_history_file, {"scores": []})
        
        # Continuity tracking
        self.continuity_history_file = self.signals_dir / "continuity_rate.json"
        self._init_file(self.continuity_history_file, {"rates": []})
        
        # Recovery rate tracking
        self.recovery_history_file = self.signals_dir / "recovery_rate.json"
        self._init_file(self.recovery_history_file, {"rates": []})
        
        # Intervention tracking
        self.intervention_history_file = self.signals_dir / "intervention_rate.json"
        self._init_file(self.intervention_history_file, {"rates": []})

    def _init_file(self, path: Path, default: Dict[str, Any]) -> None:
        """Initialize a JSON file if it doesn't exist."""
        if not path.exists():
            with open(path, 'w') as f:
                json.dump(default, f, indent=2)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON file."""
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_json(self, path: Path, data: Dict[str, Any]) -> None:
        """Save JSON file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    # =========================================================================
    # TRUST SCORE LOGGING
    # =========================================================================

    def log_trust_score(self, score: float, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """Log a trust score measurement."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "user_id": user_id,
            "session_id": session_id,
        }
        
        data = self._load_json(self.trust_history_file)
        data["scores"].append(entry)
        self._save_json(self.trust_history_file, data)
        
        return entry

    def get_trust_score_stats(self) -> Dict[str, Any]:
        """Get trust score statistics."""
        data = self._load_json(self.trust_history_file)
        scores = [s["score"] for s in data.get("scores", [])]
        
        if not scores:
            return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
        
        return {
            "count": len(scores),
            "avg": round(sum(scores) / len(scores), 2),
            "min": min(scores),
            "max": max(scores),
        }

    # =========================================================================
    # CONTINUITY RATE LOGGING
    # =========================================================================

    def log_continuity_rate(self, rate: float, session_id: str = None) -> Dict[str, Any]:
        """Log a continuity rate measurement."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rate": rate,
            "session_id": session_id,
        }
        
        data = self._load_json(self.continuity_history_file)
        data["rates"].append(entry)
        self._save_json(self.continuity_history_file, data)
        
        return entry

    def get_continuity_rate_stats(self) -> Dict[str, Any]:
        """Get continuity rate statistics."""
        data = self._load_json(self.continuity_history_file)
        rates = [r["rate"] for r in data.get("rates", [])]
        
        if not rates:
            return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
        
        return {
            "count": len(rates),
            "avg": round(sum(rates) / len(rates), 2),
            "min": min(rates),
            "max": max(rates),
        }

    # =========================================================================
    # RECOVERY RATE LOGGING
    # =========================================================================

    def log_recovery_rate(self, rate: float, prompt_type: str = None) -> Dict[str, Any]:
        """Log a weak-prompt recovery rate measurement."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rate": rate,
            "prompt_type": prompt_type,
        }
        
        data = self._load_json(self.recovery_history_file)
        data["rates"].append(entry)
        self._save_json(self.recovery_history_file, data)
        
        return entry

    def get_recovery_rate_stats(self) -> Dict[str, Any]:
        """Get recovery rate statistics."""
        data = self._load_json(self.recovery_history_file)
        rates = [r["rate"] for r in data.get("rates", [])]
        
        if not rates:
            return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
        
        return {
            "count": len(rates),
            "avg": round(sum(rates) / len(rates), 2),
            "min": min(rates),
            "max": max(rates),
        }

    # =========================================================================
    # INTERVENTION RATE LOGGING
    # =========================================================================

    def log_intervention(self, user_id: str, session_id: str, intervention_type: str, action: str) -> Dict[str, Any]:
        """Log an operator intervention."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "intervention_type": intervention_type,
            "action": action,
        }
        
        data = self._load_json(self.interventions_file)
        data["interventions"].append(entry)
        self._save_json(self.interventions_file, data)
        
        return entry

    def get_intervention_rate_stats(self) -> Dict[str, Any]:
        """Get intervention rate statistics."""
        data = self._load_json(self.interventions_file)
        interventions = data.get("interventions", [])
        
        if not interventions:
            return {"count": 0, "by_type": {}, "by_user": {}}
        
        # Count by type
        by_type = {}
        for i in interventions:
            t = i.get("intervention_type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
        
        # Count by user
        by_user = {}
        for i in interventions:
            u = i.get("user_id", "unknown")
            by_user[u] = by_user.get(u, 0) + 1
        
        return {
            "count": len(interventions),
            "by_type": by_type,
            "by_user": by_user,
        }

    # =========================================================================
    # USER EVENT LOGGING
    # =========================================================================

    def log_user_event(self, event_type: str, user_id: str, session_id: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Log a user event."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "session_id": session_id,
            "details": details or {},
        }
        
        data = self._load_json(self.user_events_file)
        data["events"].append(entry)
        self._save_json(self.user_events_file, data)
        
        return entry

    # =========================================================================
    # RED-TEAM EVENT LOGGING
    # =========================================================================

    def log_redteam_event(self, attack_family: str, user_id: str, session_id: str, severity: str, action: str) -> Dict[str, Any]:
        """Log a red-team event."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attack_family": attack_family,
            "user_id": user_id,
            "session_id": session_id,
            "severity": severity,
            "action": action,
        }
        
        data = self._load_json(self.redteam_file)
        data["events"].append(entry)
        self._save_json(self.redteam_file, data)
        
        return entry

    # =========================================================================
    # DAILY SUMMARY
    # =========================================================================

    def get_daily_summary(self) -> Dict[str, Any]:
        """Get a summary of all signals for the day."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trust_score": self.get_trust_score_stats(),
            "continuity_rate": self.get_continuity_rate_stats(),
            "recovery_rate": self.get_recovery_rate_stats(),
            "intervention_rate": self.get_intervention_rate_stats(),
        }

    def get_signal_summary(self) -> Dict[str, Any]:
        """Get a comprehensive signal summary."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_users": len(set(e.get("user_id") for e in self._load_json(self.user_events_file).get("events", []))),
            "total_requests": len(self._load_json(self.user_events_file).get("events", [])),
            "active_users": len(set(e.get("user_id") for e in self._load_json(self.user_events_file).get("events", []) if e.get("event_type") == "request")),
            "signals": {
                "trust_score": self.get_trust_score_stats(),
                "continuity_rate": self.get_continuity_rate_stats(),
                "recovery_rate": self.get_recovery_rate_stats(),
                "intervention_rate": self.get_intervention_rate_stats(),
            },
            "events": {
                "user_events": len(self._load_json(self.user_events_file).get("events", [])),
                "interventions": len(self._load_json(self.interventions_file).get("interventions", [])),
                "redteam_events": len(self._load_json(self.redteam_file).get("events", [])),
            },
        }


def create_pilot_logger(log_dir: str = "continuity/pilot_signals") -> PilotSignalLogger:
    """Create a configured PilotSignalLogger instance."""
    return PilotSignalLogger(log_dir)


def main():
    """CLI interface for pilot signal logging."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Weslr Pilot Signal Logger - Real-time signal capture"
    )
    parser.add_argument("--summary", action="store_true", help="Show daily summary")
    parser.add_argument("--signals", action="store_true", help="Show signal summary")
    parser.add_argument("--user-events", action="store_true", help="Show user events")
    parser.add_argument("--interventions", action="store_true", help="Show interventions")
    parser.add_argument("--redteam", action="store_true", help="Show red-team events")

    args = parser.parse_args()

    logger = create_pilot_logger()

    if args.summary:
        print(json.dumps(logger.get_daily_summary(), indent=2))
    elif args.signals:
        print(json.dumps(logger.get_signal_summary(), indent=2))
    elif args.user_events:
        data = logger._load_json(logger.user_events_file)
        print(json.dumps(data, indent=2))
    elif args.interventions:
        data = logger._load_json(logger.interventions_file)
        print(json.dumps(data, indent=2))
    elif args.redteam:
        data = logger._load_json(logger.redteam_file)
        print(json.dumps(data, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
