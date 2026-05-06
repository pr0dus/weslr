"""
personality_modulator.py - Personality and delivery modulation for Weslr voice layer

Shapes the final delivery of thoughts based on personality profile,
relationship depth, and contextual hints from surface_decision.

v1.0 — 2026-05-06
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DeliveryModulation:
    """Modulation parameters for voice output."""
    speed_multiplier: float = 1.0
    pause_before_ms: int = 400
    tone: str = "calm"
    warmth: float = 0.4
    dryness: float = 0.6
    verbosity: str = "balanced"  # "brief", "balanced", "detailed"
    include_prefix: bool = True
    prefix_phrase: str = ""
    include_suffix: bool = False
    suffix_phrase: str = ""


class PersonalityModulator:
    """
    Shapes how thoughts are delivered — voice parameters, tone, phrasing.
    
    Takes output from surface_decision (phrasing_hints) and applies
    the personality profile to generate the final delivery parameters.
    
    Blends Gandalf wisdom + Optimus Prime clarity:
    - Purposeful, not verbose
    - Speaks with warmth, not sentimentality
    - Direct when needed, patient otherwise
    """

    def __init__(self, tenant_id: str, storage_path: Optional[Path] = None):
        self.tenant_id = tenant_id
        self.storage_path = storage_path
        self.profile = self._load_profile()
        self._last_delivery_tone = "calm"
        self._consecutive_brief = 0

    def _load_profile(self) -> Dict[str, Any]:
        """Load personality profile."""
        search_paths = [
            Path("/data/data/com.termux/files/home/.openclaw/workspace/weslr/voice_layer/personality_profile.json"),
            Path(__file__).parent / "personality_profile.json",
        ]
        for path in search_paths:
            if path.exists():
                return json.loads(path.read_text())
        return {}

    def modulate(
        self,
        thought_content: str,
        phrasing_hints: Dict[str, Any],
        relationship_depth: float = 0.5,
        context_tags: Optional[List[str]] = None,
    ) -> DeliveryModulation:
        """
        Modulate delivery based on personality + context.
        
        Returns DeliveryModulation with voice parameters.
        """
        modulation = DeliveryModulation()
        ctx_tags = context_tags or []
        
        # Base from profile
        voice_cfg = self.profile.get("voice", {})
        char_cfg = self.profile.get("character", {})
        response_cfg = self.profile.get("response_modulation", {})
        phrase_markers = self.profile.get("phrase_markers", {})
        
        # Tone from phrasing hints
        tone_hint = phrasing_hints.get("tone", "calm")
        modulation.tone = tone_hint
        
        # Map tone to response modulation
        if tone_hint in response_cfg:
            rm = response_cfg[tone_hint]
            modulation.speed_multiplier = rm.get("speed_multiplier", 1.0)
            modulation.pause_before_ms = rm.get("pause_before_speaking_ms", 400)
            modulation.tone = rm.get("tone", tone_hint)
        
        # Relationship depth affects warmth/dryness
        if relationship_depth > 0.7:
            modulation.warmth = 0.5
            modulation.dryness = 0.5
        elif relationship_depth > 0.4:
            modulation.warmth = 0.4
            modulation.dryness = 0.6
        else:
            modulation.warmth = 0.3
            modulation.dryness = 0.7
        
        # Context tags affect verbosity
        if "tired" in ctx_tags or "late" in ctx_tags:
            modulation.verbosity = "brief"
            self._consecutive_brief += 1
        elif "relaxed" in ctx_tags or "available" in ctx_tags:
            modulation.verbosity = "balanced"
            self._consecutive_brief = 0
        else:
            modulation.verbosity = "balanced"
        
        # Limit consecutive brief to avoid being cold
        if self._consecutive_brief > 3:
            modulation.verbosity = "balanced"
            self._consecutive_brief = 0
        
        # Phrasing hints override
        lead_with = phrasing_hints.get("lead_with", "observation")
        max_statements = phrasing_hints.get("max_statements", 3)
        
        # Build prefix based on thought type and lead_with
        if phrasing_hints.get("include_context", True) and self._should_add_prefix(lead_with):
            prefix = self._select_prefix(lead_with, phrase_markers)
            modulation.include_prefix = True
            modulation.prefix_phrase = prefix
        
        # Build suffix if ask_before_elaborate
        if phrasing_hints.get("ask_before_elaborate", False):
            modulation.include_suffix = True
            modulation.suffix_phrase = " — want me to elaborate?"
        
        # Special handling for certain tones
        if tone_hint == "caring":
            modulation.warmth = 0.6
            modulation.dryness = 0.4
        elif tone_hint == "measured":
            modulation.pause_before_ms = max(modulation.pause_before_ms, 600)
            modulation.speed_multiplier = 0.85
        
        # Track for continuity
        self._last_delivery_tone = modulation.tone
        
        return modulation

    def _should_add_prefix(self, lead_with: str) -> bool:
        """Decide if prefix should be added."""
        return lead_with in ("observation", "insight", "concern")

    def _select_prefix(self, lead_with: str, phrase_markers: Dict[str, Any]) -> str:
        """Select appropriate prefix phrase."""
        prefixes = phrase_markers.get("introduction", [
            "Let me think.",
            "I've been considering.",
            "Something has come to my attention.",
        ])
        
        if lead_with == "observation":
            prefixes = phrase_markers.get("sharing_insight", [
                "I've observed.",
                "The data suggests.",
                "There's something worth noting.",
            ])
        elif lead_with == "concern":
            prefixes = ["I've been thinking about.", "Something concerns me."]
        
        # Avoid repetition
        selected = random.choice(prefixes)
        return selected

    def format_thought(
        self,
        thought_content: str,
        modulation: DeliveryModulation,
    ) -> str:
        """
        Format thought content with prefix/suffix and apply verbosity.
        """
        result = thought_content
        
        # Apply prefix
        if modulation.include_prefix and modulation.prefix_phrase:
            result = f"{modulation.prefix_phrase} {result}"
        
        # Apply suffix
        if modulation.include_suffix and modulation.suffix_phrase:
            result = f"{result}{modulation.suffix_phrase}"
        
        # Apply verbosity truncation (only for brief)
        if modulation.verbosity == "brief":
            # Truncate to first sentence, max 20 words
            words = result.split()
            if len(words) > 20:
                result = " ".join(words[:20]) + "."
        
        return result

    def get_voice_parameters(
        self,
        modulation: DeliveryModulation,
    ) -> Dict[str, Any]:
        """
        Get voice parameters for TTS layer.
        Maps personality + modulation to TTS hints.
        """
        profile = self.profile.get("voice", {})
        
        base_pace = profile.get("pace_words_per_minute", 130)
        base_pause = profile.get("pause_before_speaking_ms", 400)
        base_warmth = profile.get("warmth", 0.4)
        
        return {
            "speed_wpm": int(base_pace * modulation.speed_multiplier),
            "pause_before_ms": modulation.pause_before_ms,
            "pitch_hint": "slightly_low",  # Baritone with bass
            "tone": modulation.tone,
            "warmth": modulation.warmth,
            "dryness": modulation.dryness,
            "urgency": modulation.tone in ("controlled", "urgent"),
        }

    def get_greeting_modulation(
        self,
        greeting_style: str,
        relationship_depth: float,
    ) -> DeliveryModulation:
        """Get modulation specifically for greeting."""
        modulation = DeliveryModulation()
        
        if greeting_style == "minimal":
            modulation.verbosity = "brief"
            modulation.pause_before_ms = 200
            modulation.include_prefix = False
        elif greeting_style == "warm":
            modulation.verbosity = "balanced"
            modulation.warmth = 0.6
            modulation.include_prefix = True
            modulation.prefix_phrase = "Good to have you home."
        else:
            modulation.verbosity = "balanced"
            modulation.include_prefix = False
        
        return modulation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "last_tone": self._last_delivery_tone,
        }