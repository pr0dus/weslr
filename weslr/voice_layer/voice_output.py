"""
voice_output.py - TTS output layer for Weslr voice layer

Converts modulated text to voice output, with parameters
for TTS providers (ElevenLabs, system TTS, etc.).

v1.0 — 2026-05-06
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class VoiceOutput:
    """Final voice output — ready for TTS."""
    text: str
    voice_parameters: Dict[str, Any]
    modulation: Dict[str, Any]  # Store modulation for logging
    timestamp: str
    thought_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "voice_parameters": self.voice_parameters,
            "modulation": self.modulation,
            "timestamp": self.timestamp,
            "thought_id": self.thought_id,
        }


class VoiceOutputLayer:
    """
    Voice output — final stage before TTS.
    
    Takes formatted text + voice parameters and prepares
    for TTS conversion. Does NOT call TTS directly —
    returns VoiceOutput with all parameters needed by
    whatever TTS integration exists downstream.
    
    Supports:
    - Direct text output (for CLI/testing)
    - TTS parameter generation (for ElevenLabs, etc.)
    - Audio file generation hint
    """

    def __init__(self, tenant_id: str, storage_path: Optional[Path] = None):
        self.tenant_id = tenant_id
        self.storage_path = storage_path
        self.profile = self._load_profile()
        self._output_history: List[VoiceOutput] = []
        self._tts_callback: Optional[Callable[[VoiceOutput], None]] = None
        
        # TTS configuration
        self._tts_config = self._load_tts_config()

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

    def _load_tts_config(self) -> Dict[str, Any]:
        """Load TTS configuration from environment/config."""
        # Check environment variables for TTS settings
        return {
            "provider": "elevenlabs",  # Default provider
            "voice_id": self.profile.get("voice", {}).get("elevenlabs_voice_id", "default"),
            "model": "elevenlabs",
            "temperature": 0.7,
        }

    def output(
        self,
        text: str,
        voice_parameters: Dict[str, Any],
        modulation: Dict[str, Any],
        thought_id: Optional[str] = None,
    ) -> VoiceOutput:
        """
        Prepare text for voice output.
        
        Returns VoiceOutput with all parameters needed for TTS.
        """
        # Final text cleanup
        text = self._clean_text(text)
        
        # Build output
        output = VoiceOutput(
            text=text,
            voice_parameters=self._build_voice_parameters(voice_parameters),
            modulation=modulation,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            thought_id=thought_id,
        )
        
        # Store in history
        self._output_history.append(output)
        if len(self._output_history) > 100:
            self._output_history = self._output_history[-100:]
        
        # If TTS callback is registered, invoke it
        if self._tts_callback:
            try:
                self._tts_callback(output)
            except Exception:
                pass
        
        return output

    def _clean_text(self, text: str) -> str:
        """Clean text for TTS."""
        # Remove multiple spaces
        text = " ".join(text.split())
        
        # Remove markdown formatting
        text = text.replace("**", "").replace("*", "")
        
        # Ensure proper punctuation
        if text and text[-1] not in ".?!":
            text += "."
        
        # Limit length (TTS becomes unnatural beyond ~500 chars)
        if len(text) > 500:
            # Truncate at last complete sentence before 500
            last_period = text[:500].rfind(".")
            if last_period > 200:
                text = text[:last_period + 1]
            else:
                text = text[:497] + "..."
        
        return text

    def _build_voice_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build final voice parameters for TTS."""
        return {
            "speed_wpm": params.get("speed_wpm", 130),
            "pause_before_ms": params.get("pause_before_ms", 400),
            "pitch_hint": params.get("pitch_hint", "baritone"),
            "tone": params.get("tone", "calm"),
            "warmth": params.get("warmth", 0.4),
            "dryness": params.get("dryness", 0.6),
            "urgency": params.get("urgency", False),
            "provider": self._tts_config["provider"],
            "voice_id": self._tts_config["voice_id"],
        }

    def register_tts_callback(self, callback: Callable[[VoiceOutput], None]) -> None:
        """
        Register a callback for TTS processing.
        
        The callback receives VoiceOutput and should handle
        TTS conversion (ElevenLabs API call, system TTS, etc.)
        """
        self._tts_callback = callback

    def speak(self, text: str, voice_params: Optional[Dict[str, Any]] = None) -> VoiceOutput:
        """
        Convenience method: modulate + output in one step.
        For use when personality_modulator already applied.
        """
        if voice_params is None:
            voice_params = {}
        
        return self.output(
            text=text,
            voice_parameters=voice_params,
            modulation={},
        )

    def get_output_history(self, limit: int = 20) -> List[VoiceOutput]:
        """Get recent output history."""
        return self._output_history[-limit:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "tts_config": self._tts_config,
            "last_output": self._output_history[-1].to_dict() if self._output_history else None,
        }


# ============================================================================
# VOICE OUTPUT INTEGRATION HELPERS
# ============================================================================

def elevenlabs_output(
    output: VoiceOutput,
    api_key: Optional[str] = None,
) -> bytes:
    """
    Convert VoiceOutput to audio using ElevenLabs API.
    
    Returns audio bytes.
    
    Requires:
    - elevenlabs package installed
    - API key set via ELEVENLABS_API_KEY env var or passed as arg
    """
    try:
        import os
        from elevenlabs import generate, play
        
        api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ElevenLabs API key not found")
        
        params = output.voice_parameters
        
        audio = generate(
            text=output.text,
            voice=params.get("voice_id", "default"),
            model=params.get("model", "elevenlabs"),
            stability=params.get("temperature", 0.7),
        )
        return audio
    except ImportError:
        raise ImportError("elevenlabs package not installed: pip install elevenlabs")
    except Exception as e:
        raise RuntimeError(f"ElevenLabs TTS failed: {e}")


def system_tts_output(output: VoiceOutput) -> None:
    """
    Output VoiceOutput via system TTS (for Linux/Android/Termux).
    
    Uses espeak or similar system TTS engine.
    """
    import subprocess
    
    params = output.voice_parameters
    speed = params.get("speed_wpm", 130)
    
    # espeak parameters
    cmd = [
        "espeak",
        "-s", str(int(speed * 0.8)),  # espeak uses words per minute differently
        "-p", "80",  # pitch (standard)
        "-a", "100",  # amplitude
        "-v", "en",  # English
    ]
    
    try:
        proc = subprocess.run(
            cmd + [output.text],
            capture_output=True,
            timeout=30,
        )
    except FileNotFoundError:
        raise RuntimeError("System TTS (espeak) not found. Install with: pkg install espeak")
    except Exception as e:
        raise RuntimeError(f"System TTS failed: {e}")


def get_voice_output(tenant_id: str, storage_path: Optional[Path] = None) -> VoiceOutputLayer:
    """Get or create voice output layer for tenant."""
    return VoiceOutputLayer(tenant_id=tenant_id, storage_path=storage_path)