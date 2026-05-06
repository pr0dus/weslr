"""
adaptive_greeting.py - Probabilistic greeting generator for Weslr voice layer

Generates greetings that vary by context, not fixed scripts.
Uses personality profile + presence state + elastic memory to shape greeting.

v1.0 — 2026-05-06
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional




@dataclass
class GreetingContext:
    """Context for greeting generation."""
    time_context: str          # "morning", "afternoon", "evening", "night"
    availability: str          # "available", "tired", "busy", "relaxed"
    arrival_anomaly: bool      # Was arrival anomalous (late/early)?
    anomaly_description: str  # "" if not anomalous
    arrival_count_today: int  # How many times arrived today
    relationship_depth: float # 0.0-1.0
    recent_interactions: int   # Interactions in last 24h
    last_greeting_style: str   # What style was used last time


class AdaptiveGreeting:
    """
    Generates contextually appropriate greetings.
    
    Not a fixed script — uses weighted selection based on:
    - Time of day
    - Human availability
    - Learned relationship patterns
    - Arrival anomalies
    - Recent conversation history
    
    Blends Gandalf wisdom with Optimus Prime clarity:
    - Speaks with purpose, not noise
    - Acknowledges context without over-explaining
    - Warm but not sentimental
    """

    def __init__(self, tenant_id: str, storage_path: Optional[Path] = None):
        self.tenant_id = tenant_id
        self.storage_path = storage_path
        self.profile = load_profile()
        self._last_greeting = ""
        self._last_greeting_time: Optional[str] = None
        self._recent_greeting_hashes: List[int] = []  # Last 3 greeting hashes for anti-repetition
        self._recent_greeting_timestamps: List[str] = []  # ISO timestamps for 24h window

    def generate(self, context: GreetingContext) -> str:
        """
        Generate a greeting based on context.
        
        Principles:
        - Calming, not perky
        - Acknowledges arrival without overdoing it
        - Can reference context (late, early, quiet day) if significant
        - Never robotic: "Good evening, sir" is wrong for Weslr
        - Never performative: no exclamation marks
        """
        # Determine greeting style
        style = self._determine_style(context)
        
        # Select greeting phrase
        greeting = self._select_phrase(style, context)
        
        # Add contextual nuance if warranted
        if context.arrival_anomaly and context.anomaly_description:
            greeting = self._add_anomaly_nuance(greeting, context)
        elif context.arrival_count_today > 1:
            greeting = self._add_return_nuance(greeting, context)
        
        # Track last greeting to avoid repetition
        self._last_greeting = greeting
        self._last_greeting_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        return greeting

    def _determine_style(self, context: GreetingContext) -> str:
        """
        Determine greeting style based on context.
        Returns: "minimal", "standard", "warm", "observant"
        """
        # Relationship depth drives warmth
        if context.relationship_depth < 0.3:
            style = "minimal"
        elif context.relationship_depth > 0.7:
            style = "warm" if context.availability in ("relaxed", "available") else "standard"
        else:
            style = "standard"
        
        # Anomaly increases perceptiveness
        if context.arrival_anomaly and context.arrival_count_today <= 1:
            style = "observant"
        
        # Very tired = minimal
        if context.availability == "tired":
            style = "minimal"
        
        # First arrival today can be slightly warmer
        if context.arrival_count_today == 1 and context.relationship_depth > 0.5:
            style = "warm"
        
        return style

    def _select_phrase(self, style: str, context: GreetingContext) -> str:
        """Select greeting phrase based on style."""
        
        # Minimal greetings — short, calm, no fuss
        minimal = [
            "Evening.",
            "You're home.",
            "Back.",
        ]
        
        # Standard greetings — balanced, acknowledging
        standard = [
            "Good evening.",
            "Welcome home.",
            "Evening.",
        ]
        
        # Warm greetings — genuine care, not sentimental
        warm = [
            "Good evening. The house was quiet without you.",
            "Welcome home. It's been a while.",
            "Evening. You look tired — everything alright?",
        ]
        
        # Observant greetings — note the anomaly/context
        observant = [
            "You're late — long day?",
            "Early this time. Everything alright?",
            "Back. I was beginning to wonder.",
        ]
        
        phrase_map = {
            "minimal": minimal,
            "standard": standard,
            "warm": warm,
            "observant": observant,
        }
        
        phrases = phrase_map.get(style, standard)
        
        # Avoid repeating the exact same greeting
        if self._last_greeting in phrases and len(phrases) > 1:
            phrases = [p for p in phrases if p != self._last_greeting]
        
        greeting = random.choice(phrases)
        
        # Track for per-style dedup on next call
        self._last_greeting = greeting

        return greeting

    def get_recent_greeting_count(self) -> int:
        """Count greetings in last 24 hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        count = 0
        for ts_str in self._recent_greeting_timestamps:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= cutoff:
                    count += 1
            except Exception:
                pass
        return count

    def _add_anomaly_nuance(self, greeting: str, context: GreetingContext) -> str:
        """Add contextual nuance for anomalous arrival."""
        anomaly = context.anomaly_description
        
        if "late" in anomaly:
            # Extract minutes late
            try:
                mins = int(anomaly.split("_")[1])
                if mins > 60:
                    return f"You're over an hour late. Everything alright?"
                elif mins > 30:
                    return f"Thirty minutes late — long day?"
                else:
                    return f"A bit late today. Everything alright?"
            except Exception:
                return f"You're late. Everything alright?"
        elif "early" in anomaly:
            return f"Early for once. Everything alright?"
        
        return greeting

    def _add_return_nuance(self, greeting: str, context: GreetingContext) -> str:
        """Add nuance for returning again same day."""
        count = context.arrival_count_today
        if count == 2:
            return "Back again. Busy day?"
        elif count >= 3:
            return "Third time back. Everything alright?"
        
        return greeting

    def get_alternative(self) -> str:
        """Get an alternative greeting if user didn't respond well."""
        alternatives = [
            "Still here when you need me.",
            "Take your time.",
        ]
        return random.choice(alternatives)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "last_greeting": self._last_greeting,
            "last_greeting_time": self._last_greeting_time,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], tenant_id: str, storage_path: Optional[Path] = None) -> AdaptiveGreeting:
        instance = cls(tenant_id, storage_path)
        instance._last_greeting = data.get("last_greeting", "")
        instance._last_greeting_time = data.get("last_greeting_time")
        return instance


# ============================================================================
# PROFILE LOADER
# ============================================================================

_profile_cache: Optional[Dict[str, Any]] = None


def load_profile() -> Dict[str, Any]:
    """Load personality profile from JSON."""
    global _profile_cache
    if _profile_cache:
        return _profile_cache
    
    # Try workspace paths
    search_paths = [
        Path("/data/data/com.termux/files/home/.openclaw/workspace/weslr/voice_layer/personality_profile.json"),
        Path(__file__).parent / "personality_profile.json",
    ]
    
    for path in search_paths:
        if path.exists():
            _profile_cache = json.loads(path.read_text())
            return _profile_cache
    
    # Default profile
    return {
        "voice": {
            "pace_words_per_minute": 130,
            "pause_before_speaking_ms": 400,
        },
        "character": {
            "deference": {
                "level": "high",
                "never_interrupt": ["busy", "stressed", "unavailable"],
            }
        },
        "phrase_markers": {
            "greeting_variants": ["Good evening.", "Welcome home.", "Evening."],
        }
    }