"""
tts_engine.py - TTS abstraction layer for Weslr standalone

Provides a unified TTS interface that detects available engines
and falls back gracefully. Supports multiple backends:
- Piper (recommended: fast, local, good quality)
- espeak-ng (fallback: always available, lightweight)
- Coqui XTTS (high quality, GPU required)
- Dummy (testing only, no audio)

Usage:
    from weslr.voice_layer.tts_engine import TTSEngine
    
    engine = TTSEngine.detect()
    audio = engine.speak("Good evening.")
    
    # Or with specific backend:
    engine = TTSEngine.use("piper")
    audio = engine.speak("The data suggests.")

v1.0 — 2026-05-06
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# TTS ENGINE INTERFACE
# ============================================================================


@dataclass
class TTSResult:
    """Result of TTS generation."""
    audio_data: Optional[bytes]  # Raw audio bytes (for playback/streaming)
    audio_file: Optional[str]    # Path to generated audio file (for file-based engines)
    duration_seconds: float       # Estimated audio duration
    engine: str                   # Engine used
    text: str                     # Original text
    success: bool
    error: Optional[str] = None

    def has_audio(self) -> bool:
        return self.audio_data is not None or self.audio_file is not None


class TTSEngineBase(ABC):
    """Abstract base for TTS engines."""

    name: str = "base"
    supports_streaming: bool = False
    needs_gpu: bool = False
    min_ram_mb: int = 0
    quality_score: float = 0.5  # 0-1, relative quality

    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is installed and working."""
        pass

    @abstractmethod
    def install(self, target_dir: Optional[Path] = None) -> bool:
        """Install the TTS engine. Returns True on success."""
        pass

    @abstractmethod
    def speak(self, text: str, voice_id: Optional[str] = None) -> TTSResult:
        """Convert text to speech. Returns audio data or file path."""
        pass

    @abstractmethod
    def list_voices(self) -> List[Dict[str, Any]]:
        """List available voices for this engine."""
        pass

    def get_config_hints(self) -> Dict[str, Any]:
        """Return configuration hints for onboarding UI."""
        return {
            "name": self.name,
            "quality_score": self.quality_score,
            "needs_gpu": self.needs_gpu,
            "min_ram_mb": self.min_ram_mb,
            "supports_streaming": self.supports_streaming,
        }


# ============================================================================
# DUMMY ENGINE (testing / no audio)
# ============================================================================


class DummyTTS(TTSEngineBase):
    """Dummy TTS for testing without audio output."""

    name = "dummy"
    quality_score = 0.0

    def is_available(self) -> bool:
        return True

    def install(self, target_dir: Optional[Path] = None) -> bool:
        return True  # No installation needed

    def speak(self, text: str, voice_id: Optional[str] = None) -> TTSResult:
        return TTSResult(
            audio_data=None,
            audio_file=None,
            duration_seconds=len(text.split()) * 0.3,
            engine=self.name,
            text=text,
            success=True,
        )

    def list_voices(self) -> List[Dict[str, Any]]:
        return [{"id": "default", "name": "Dummy Voice", "language": "en"}]


# ============================================================================
# ESPEAK-NG ENGINE (fallback — always available)
# ============================================================================


class EspeakTTS(TTSEngineBase):
    """Espeak-ng TTS — lightweight, always available on Linux/Android."""

    name = "espeak"
    quality_score = 0.4
    needs_gpu = False
    min_ram_mb = 64

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["espeak-ng", "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install(self, target_dir: Optional[Path] = None) -> bool:
        # On Termux: pkg install espeak-ng
        # On Debian/Ubuntu: apt install espeak-ng
        # On Android: needs rooted or termux package
        return self.is_available()

    def speak(self, text: str, voice_id: Optional[str] = None) -> TTSResult:
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name

            voice = voice_id or "en"
            cmd = ["espeak-ng", "-w", wav_path, "-v", voice, text]
            result = subprocess.run(cmd, capture_output=True, timeout=30)

            if result.returncode == 0 and Path(wav_path).exists():
                audio_bytes = Path(wav_path).read_bytes()
                os.unlink(wav_path)
                return TTSResult(
                    audio_data=audio_bytes,
                    audio_file=None,
                    duration_seconds=len(text.split()) * 0.3,
                    engine=self.name,
                    text=text,
                    success=True,
                )
            else:
                return TTSResult(
                    audio_data=None,
                    audio_file=None,
                    duration_seconds=0,
                    engine=self.name,
                    text=text,
                    success=False,
                    error=f"espeak-ng failed: {result.stderr.decode()}",
                )
        except Exception as e:
            return TTSResult(
                audio_data=None,
                audio_file=None,
                duration_seconds=0,
                engine=self.name,
                text=text,
                success=False,
                error=str(e),
            )

    def list_voices(self) -> List[Dict[str, Any]]:
        return [
            {"id": "en", "name": "English (default)", "language": "en"},
            {"id": "en-GB", "name": "English (UK)", "language": "en-GB"},
            {"id": "en-sc", "name": "English (Scottish)", "language": "en-sc"},
        ]

    def get_config_hints(self) -> Dict[str, Any]:
        hints = super().get_config_hints()
        hints.update({
            "install_hint": "Run: pkg install espeak-ng (Termux) or apt install espeak-ng (Debian/Ubuntu)",
            "description": "Lightweight, always works, basic quality. Good for testing.",
        })
        return hints


# ============================================================================
# PIPER ENGINE (recommended — fast, local, good quality)
# ============================================================================


class PiperTTS(TTSEngineBase):
    """
    Piper TTS — recommended for Weslr.
    Fast, local, good quality, runs on arm64/Android.
    
    Download voices from: https://github.com/rhasspy/piper/raw/master/voices/
    """

    name = "piper"
    quality_score = 0.75
    needs_gpu = False
    min_ram_mb = 512

    def __init__(self):
        self.piper_path: Optional[str] = None
        self.voice_dir: Optional[Path] = None
        self._find_piper()

    def _find_piper(self) -> None:
        """Find piper binary and voice directory."""
        # Check common locations
        search_paths = [
            Path("/data/data/com.termux/files/usr/bin/piper"),
            Path.home() / "piper/piper",
            Path.home() / ".local/bin/piper",
            Path("/usr/local/bin/piper"),
            Path("/usr/bin/piper"),
        ]

        for path in search_paths:
            if path.exists():
                self.piper_path = str(path)
                break

        # Find voice directory
        voice_search = [
            Path.home() / "piper/voices",
            Path("/data/data/com.termux/files/home/voices"),
            Path.home() / "voices",
        ]
        for vd in voice_search:
            if vd.exists():
                self.voice_dir = vd
                break

    def is_available(self) -> bool:
        self._find_piper()
        return self.piper_path is not None

    def install(self, target_dir: Optional[Path] = None) -> bool:
        """
        Guide user through Piper installation.
        Piper must be compiled or downloaded for their platform.
        """
        install_path = target_dir or Path.home() / "piper"
        install_path.mkdir(parents=True, exist_ok=True)

        # For Termux/Android: need to cross-compile or download prebuilt
        # This is a guided install — returns False with instructions
        return False  # Manual installation required

    def speak(self, text: str, voice_id: Optional[str] = None) -> TTSResult:
        if not self.is_available():
            return TTSResult(
                audio_data=None,
                audio_file=None,
                duration_seconds=0,
                engine=self.name,
                text=text,
                success=False,
                error="Piper not installed. Run onboarding to install.",
            )

        try:
            voice = voice_id or "en_US-lessac-medium.onnx"
            voice_path = self.voice_dir / voice if self.voice_dir else None

            if voice_path and not voice_path.exists():
                # Try default voice path
                voice_path = self.voice_dir / "en_US-lessac-medium.onnx" if self.voice_dir else None

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name

            cmd = [self.piper_path, "--model", str(voice_path or voice), "--output-file", wav_path]
            proc = subprocess.run(
                cmd,
                input=text.encode(),
                capture_output=True,
                timeout=30,
            )

            if Path(wav_path).exists():
                audio_bytes = Path(wav_path).read_bytes()
                os.unlink(wav_path)
                return TTSResult(
                    audio_data=audio_bytes,
                    audio_file=None,
                    duration_seconds=len(text.split()) * 0.35,
                    engine=self.name,
                    text=text,
                    success=True,
                )
            else:
                return TTSResult(
                    audio_data=None,
                    audio_file=None,
                    duration_seconds=0,
                    engine=self.name,
                    text=text,
                    success=False,
                    error=proc.stderr.decode() if proc.stderr else "Unknown error",
                )
        except Exception as e:
            return TTSResult(
                audio_data=None,
                audio_file=None,
                duration_seconds=0,
                engine=self.name,
                text=text,
                success=False,
                error=str(e),
            )

    def list_voices(self) -> List[Dict[str, Any]]:
        if not self.voice_dir or not self.voice_dir.exists():
            return []

        voices = []
        for f in self.voice_dir.glob("*.onnx"):
            name = f.stem
            lang = "en"
            if "-" in name:
                parts = name.split("-")
                lang = parts[0]
            voices.append({
                "id": f.name,
                "name": name,
                "language": lang,
                "file": str(f),
            })
        return voices

    def get_config_hints(self) -> Dict[str, Any]:
        hints = super().get_config_hints()
        hints.update({
            "description": "Recommended. Fast, local, good quality. Runs on arm64 (Android/Termux).",
            "quality_hint": "medium-high",
            "speed_hint": "fast",
            "voice_options": [
                "en_US-lessac-medium.onnx (recommended)",
                "en_US-kusal-medium.onnx",
                "en_GB-alan-medium.onnx (UK accent)",
            ],
            "download_url": "https://github.com/rhasspy/piper/raw/master/voices/",
        })
        return hints


# ============================================================================
# GOOGLETTS ENGINE (free, internet required, good quality)
# ============================================================================


class GoogleTTS(TTSEngineBase):
    """Google TTS — free, internet required, good quality. Pre-installed on Termux."""

    name = "gtts"
    quality_score = 0.7
    needs_gpu = False
    min_ram_mb = 128

    def is_available(self) -> bool:
        try:
            from gtts import gTTS
            return True
        except ImportError:
            return False

    def install(self, target_dir: Optional[Path] = None) -> bool:
        return self.is_available()  # Pre-installed on Termux

    def speak(self, text: str, voice_id: Optional[str] = None) -> TTSResult:
        try:
            from gtts import gTTS

            lang = voice_id or "en"
            tts = gTTS(text=text, lang=lang, slow=False)

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                mp3_path = f.name

            tts.write_to_fp(open(mp3_path, "wb"))
            audio_bytes = Path(mp3_path).read_bytes()
            os.unlink(mp3_path)

            return TTSResult(
                audio_data=audio_bytes,
                audio_file=None,
                duration_seconds=len(text.split()) * 0.35,
                engine=self.name,
                text=text,
                success=True,
            )
        except Exception as e:
            return TTSResult(
                audio_data=None,
                audio_file=None,
                duration_seconds=0,
                engine=self.name,
                text=text,
                success=False,
                error=str(e),
            )

    def list_voices(self) -> List[Dict[str, Any]]:
        return [
            {"id": "en", "name": "English (default)", "language": "en"},
            {"id": "en-GB", "name": "English (UK)", "language": "en-GB"},
            {"id": "de", "name": "German", "language": "de"},
            {"id": "fr", "name": "French", "language": "fr"},
            {"id": "es", "name": "Spanish", "language": "es"},
        ]

    def get_config_hints(self) -> Dict[str, Any]:
        hints = super().get_config_hints()
        hints.update({
            "description": "Free Google TTS — good quality, internet required. Pre-installed on Termux.",
            "install_hint": "Already installed (pip package gTTS). No extra setup needed.",
            "quality_hint": "good",
            "speed_hint": "moderate",
            "no_internet_warning": "Requires internet connection to generate audio",
        })
        return hints


# ============================================================================
# COQUI XTTS ENGINE (high quality, GPU required)
# ============================================================================


class CoquiTTS(TTSEngineBase):
    """Coqui XTTS — high quality, requires GPU."""

    name = "coqui"
    quality_score = 0.95
    needs_gpu = True
    min_ram_mb = 4096

    def is_available(self) -> bool:
        try:
            import TTS
            return True
        except ImportError:
            return False

    def install(self, target_dir: Optional[Path] = None) -> bool:
        try:
            subprocess.run(
                ["pip", "install", "TTS"],
                capture_output=True,
                timeout=120,
            )
            return self.is_available()
        except Exception:
            return False

    def speak(self, text: str, voice_id: Optional[str] = None) -> TTSResult:
        try:
            from TTS.api import TTS

            tts = TTS(model_name="xtts")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name

            tts.tts_to_file(text=text, file_path=wav_path)
            audio_bytes = Path(wav_path).read_bytes()
            os.unlink(wav_path)

            return TTSResult(
                audio_data=audio_bytes,
                audio_file=None,
                duration_seconds=len(text.split()) * 0.3,
                engine=self.name,
                text=text,
                success=True,
            )
        except Exception as e:
            return TTSResult(
                audio_data=None,
                audio_file=None,
                duration_seconds=0,
                engine=self.name,
                text=text,
                success=False,
                error=str(e),
            )

    def list_voices(self) -> List[Dict[str, Any]]:
        # Coqui uses voice cloning — any voice sample works
        return [
            {"id": "default", "name": "Default (voice cloning)", "language": "multi"},
        ]

    def get_config_hints(self) -> Dict[str, Any]:
        hints = super().get_config_hints()
        hints.update({
            "description": "Best quality but requires NVIDIA GPU. Not available on Android.",
            "quality_hint": "excellent",
            "speed_hint": "slow",
            "install_hint": "pip install TTS (only works with CUDA GPU)",
        })
        return hints


# ============================================================================
# TTS ENGINE MANAGER
# ============================================================================


class TTSEngine:
    """
    Unified TTS interface — detects available engines, manages selection.
    
    Usage:
        engine = TTSEngine.detect()              # Auto-detect best available
        engine = TTSEngine.use("piper")          # Use specific engine
        engine = TTSEngine.list_options()         # Show all options for onboarding
        
        result = engine.speak("Good evening.")
    """

    _engines = {
        "dummy": DummyTTS,
        "gtts": GoogleTTS,
        "espeak": EspeakTTS,
        "piper": PiperTTS,
        "coqui": CoquiTTS,
    }

    def __init__(self, engine: TTSEngineBase):
        self._engine = engine

    @classmethod
    def detect(cls) -> "TTSEngine":
        """
        Detect best available TTS engine.
        Priority: gtts > piper > espeak > dummy
        
        gtts is pre-installed on Termux and doesn't require internet at detection time.
        """
        for name in ["gtts", "piper", "espeak"]:
            engine_cls = cls._engines.get(name)
            if engine_cls:
                engine = engine_cls()
                if engine.is_available:
                    return cls(engine)

        # Fallback to dummy
        return cls(DummyTTS())

    @classmethod
    def use(cls, engine_name: str) -> "TTSEngine":
        """Use specific TTS engine."""
        engine_cls = cls._engines.get(engine_name)
        if not engine_cls:
            raise ValueError(f"Unknown engine: {engine_name}")
        return cls(engine_cls())

    @classmethod
    def list_options(cls) -> List[Dict[str, Any]]:
        """List all available TTS options for onboarding."""
        options = []
        for name, engine_cls in cls._engines.items():
            engine = engine_cls()
            config = engine.get_config_hints()
            config["engine_id"] = name
            config["installed"] = engine.is_available()
            options.append(config)
        return options

    @classmethod
    def playback_available(cls) -> bool:
        """Check if any audio playback backend is available (mpv, termux-media-player, ffplay)."""
        for cmd in ["mpv", "termux-media-player", "ffplay"]:
            try:
                result = subprocess.run(
                    ["which", cmd],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return True
            except Exception:
                pass
        return False

    @classmethod
    def install_engine(cls, engine_name: str, target_dir: Optional[Path] = None) -> bool:
        """Install a specific TTS engine."""
        engine_cls = cls._engines.get(engine_name)
        if not engine_cls:
            raise ValueError(f"Unknown engine: {engine_name}")
        engine = engine_cls()
        return engine.install(target_dir)

    def speak(self, text: str, voice_id: Optional[str] = None) -> TTSResult:
        """Convert text to speech."""
        return self._engine.speak(text, voice_id)

    def list_voices(self) -> List[Dict[str, Any]]:
        """List available voices."""
        return self._engine.list_voices()

    @property
    def engine_name(self) -> str:
        return self._engine.name

    @property
    def is_available(self) -> bool:
        return self._engine.is_available()

    def get_config_hints(self) -> Dict[str, Any]:
        return self._engine.get_config_hints()