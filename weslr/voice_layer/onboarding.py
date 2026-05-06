"""
onboarding.py - Onboarding system for Weslr standalone

Handles new tenant setup, TTS engine selection, and configuration.
Modular — supports adding new installation options over time.

v1.0 — 2026-05-06
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================

class OnboardingStage(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class OSType(str, Enum):
    ANDROID = "android"      # Termux on Android
    LINUX = "linux"          # Desktop Linux
    LINUX_SERVER = "linux_server"  # Headless Linux server
    UNKNOWN = "unknown"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class TTSInstallOption:
    """A TTS engine option available in onboarding."""
    engine_id: str           # "piper", "espeak", etc.
    name: str                 # Display name
    description: str         # What this engine offers
    quality_score: float     # 0-1 quality rating
    is_recommended: bool     # Show as recommended option
    is_installed: bool        # Currently available on system
    install_instructions: str # How to install
    post_install_hint: Optional[str] = None


@dataclass
class OnboardingConfig:
    """Configuration collected during onboarding."""
    tenant_id: str
    tenant_name: str
    language: str = "en"
    
    # OS detection
    os_type: str = OSType.UNKNOWN.value
    has_gpu: bool = False
    total_ram_mb: int = 0
    
    # TTS selection
    tts_engine: str = "espeak"  # Default fallback
    tts_voice: str = "en"
    
    # Personality (from voice layer)
    personality_profile: str = "default"
    
    # Capabilities to enable
    enable_stt: bool = False
    enable_voice_io: bool = False
    enable_ws_server: bool = False
    
    # Paths
    weslr_home: Optional[str] = None
    storage_path: Optional[str] = None
    voice_dir: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "language": self.language,
            "os_type": self.os_type,
            "has_gpu": self.has_gpu,
            "total_ram_mb": self.total_ram_mb,
            "tts_engine": self.tts_engine,
            "tts_voice": self.tts_voice,
            "personality_profile": self.personality_profile,
            "enable_stt": self.enable_stt,
            "enable_voice_io": self.enable_voice_io,
            "enable_ws_server": self.enable_ws_server,
            "weslr_home": self.weslr_home,
            "storage_path": self.storage_path,
            "voice_dir": self.voice_dir,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OnboardingConfig:
        return cls(**data)


@dataclass
class OnboardingState:
    """Current state of onboarding for a tenant."""
    tenant_id: str
    stage: str = OnboardingStage.PENDING.value
    current_step: int = 0
    total_steps: int = 6
    step_name: str = ""
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    config: Optional[OnboardingConfig] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "stage": self.stage,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "step_name": self.step_name,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "config": self.config.to_dict() if self.config else None,
        }


@dataclass
class OnboardingStep:
    """A single step in the onboarding process."""
    id: int
    name: str
    description: str
    action: str  # "detect", "select", "install", "configure", "verify", "complete"
    optional: bool = False
    can_retry: bool = True


# ============================================================================
# ONBOARDING STEPS DEFINITION
# ============================================================================

ONBOARDING_STEPS = [
    OnboardingStep(1, "System Detection", "Detecting OS, hardware capabilities", "detect"),
    OnboardingStep(2, "TTS Engine", "Select speech synthesis engine", "select"),
    OnboardingStep(3, "TTS Installation", "Install TTS engine if needed", "install"),
    OnboardingStep(4, "Voice Selection", "Choose voice characteristics", "select"),
    OnboardingStep(5, "Capabilities", "Enable optional capabilities (STT, WebSocket)", "configure"),
    OnboardingStep(6, "Verification", "Verify installation and create config", "verify"),
]


# ============================================================================
# ONBOARDING ENGINE
# ============================================================================


class OnboardingEngine:
    """
    Handles tenant onboarding for Weslr standalone.
    
    Usage:
        engine = OnboardingEngine(tenant_id="pr0dus")
        state = engine.start()
        
        # Step-by-step:
        step = engine.get_current_step()
        result = engine.execute_step(step_id, options)
        engine.next_step()
        
        # Or auto:
        config = engine.run_complete()
    """

    def __init__(self, tenant_id: str, weslr_home: Optional[Path] = None):
        self.tenant_id = tenant_id
        self.weslr_home = weslr_home or Path.home() / ".weslr"
        self.weslr_home.mkdir(parents=True, exist_ok=True)
        
        self.state: Optional[OnboardingState] = None
        self._load_state()

    def _state_file(self) -> Path:
        return self.weslr_home / f"onboarding_{self.tenant_id}.json"

    def _load_state(self) -> None:
        """Load existing onboarding state."""
        sf = self._state_file()
        if sf.exists():
            try:
                data = json.loads(sf.read_text())
                self.state = OnboardingState(
                    tenant_id=data["tenant_id"],
                    stage=data.get("stage", OnboardingStage.PENDING.value),
                    current_step=data.get("current_step", 0),
                    total_steps=data.get("total_steps", 6),
                    step_name=data.get("step_name", ""),
                    error=data.get("error"),
                    started_at=data.get("started_at"),
                    completed_at=data.get("completed_at"),
                    config=OnboardingConfig.from_dict(data["config"]) if data.get("config") else None,
                )
            except Exception:
                self.state = None

    def _save_state(self) -> None:
        """Save onboarding state."""
        if self.state:
            self._state_file().write_text(json.dumps(self.state.to_dict(), indent=2))

    def start(self) -> OnboardingState:
        """Start or resume onboarding."""
        if not self.state:
            self.state = OnboardingState(
                tenant_id=self.tenant_id,
                stage=OnboardingStage.RUNNING.value,
                current_step=0,
                started_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            )
        else:
            self.state.stage = OnboardingStage.RUNNING.value
            self.state.error = None
        
        self._save_state()
        return self.state

    def get_current_step(self) -> Optional[OnboardingStep]:
        """Get current onboarding step."""
        if not self.state:
            return None
        if self.state.current_step >= len(ONBOARDING_STEPS):
            return None
        return ONBOARDING_STEPS[self.state.current_step]

    def execute_step(self, step_id: int, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a specific onboarding step.
        
        Returns result dict with:
        - success: bool
        - step_data: varies by step
        - hints: for UI display
        """
        opts = options or {}
        
        if step_id == 1:
            return self._step_system_detection(opts)
        elif step_id == 2:
            return self._step_tts_engine_selection(opts)
        elif step_id == 3:
            return self._step_tts_installation(opts)
        elif step_id == 4:
            return self._step_voice_selection(opts)
        elif step_id == 5:
            return self._step_capabilities(opts)
        elif step_id == 6:
            return self._step_verification(opts)
        else:
            return {"success": False, "error": f"Unknown step {step_id}"}

    def _step_system_detection(self, opts: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Detect OS and hardware."""
        os_type = self._detect_os()
        has_gpu = self._detect_gpu()
        total_ram = self._detect_ram()
        
        # Initialize config if needed
        if not self.state.config:
            self.state.config = OnboardingConfig(
                tenant_id=self.tenant_id,
                tenant_name=opts.get("tenant_name", self.tenant_id),
            )
        
        self.state.config.os_type = os_type.value
        self.state.config.has_gpu = has_gpu
        self.state.config.total_ram_mb = total_ram
        self.state.config.weslr_home = str(self.weslr_home)
        
        # Determine recommended TTS based on OS
        if os_type == OSType.ANDROID:
            recommended_tts = "gtts"
        elif has_gpu:
            recommended_tts = "coqui"
        else:
            recommended_tts = "espeak"

        self.state.step_name = ONBOARDING_STEPS[0].name
        self._save_state()

        return {
            "success": True,
            "step_data": {
                "os_type": os_type.value,
                "has_gpu": has_gpu,
                "total_ram_mb": total_ram,
            },
            "hints": {
                "detected_os": os_type.value,
                "recommended_tts": recommended_tts,
                "recommended_playback": self._detect_playback_backend(),
            }
        }

    def _step_tts_engine_selection(self, opts: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Show TTS engine options for selection."""
        from .tts_engine import TTSEngine
        
        options = TTSEngine.list_options()
        tts_options = []
        
        for opt in options:
            os_hint = ""
            if self.state.config:
                if self.state.config.os_type == OSType.ANDROID.value:
                    if opt["engine_id"] == "coqui":
                        os_hint = "Requires GPU — not available on Android"
                    elif opt["engine_id"] == "gtts":
                        os_hint = "Recommended — pre-installed on Termux, no setup needed"
                    elif opt["engine_id"] == "piper":
                        os_hint = "Fast & local, but requires manual cross-compilation for arm64"
                    elif opt["engine_id"] == "espeak":
                        os_hint = "Lightweight fallback — pkg install espeak-ng"
                elif self.state.config.os_type in (OSType.LINUX.value, OSType.LINUX_SERVER.value):
                    if opt["engine_id"] == "coqui" and not self.state.config.has_gpu:
                        os_hint = "Requires NVIDIA GPU"
                    elif opt["engine_id"] == "gtts":
                        os_hint = "Good quality, internet required"
                    elif opt["engine_id"] == "piper":
                        os_hint = "Recommended for Linux (pre-built binaries available)"
            
            # Recommended: gtts on Android, piper on Linux, espeak on server
            if self.state.config and self.state.config.os_type == OSType.ANDROID.value:
                is_rec = opt["engine_id"] == "gtts"
            elif self.state.config and self.state.config.os_type in (OSType.LINUX.value,):
                is_rec = opt["engine_id"] == "piper"
            else:
                is_rec = opt["engine_id"] == "espeak"
            
            tts_options.append(TTSInstallOption(
                engine_id=opt["engine_id"],
                name=opt.get("name", opt["engine_id"]),
                description=opt.get("description", ""),
                quality_score=opt.get("quality_score", 0.5),
                is_recommended=is_rec,
                is_installed=opt.get("installed", False),
                install_instructions=opt.get("install_hint", ""),
                post_install_hint=opt.get("post_install_hint"),
            ))
        
        return {
            "success": True,
            "step_data": {
                "options": [
                    {
                        "engine_id": o.engine_id,
                        "name": o.name,
                        "description": o.description,
                        "quality_score": o.quality_score,
                        "is_recommended": o.is_recommended,
                        "is_installed": o.is_installed,
                        "install_instructions": o.install_instructions,
                    }
                    for o in tts_options
                ]
            },
            "hints": {
                "selected_default": "gtts" if self.state.config and self.state.config.os_type == OSType.ANDROID.value else "espeak",
            }
        }

    def _step_tts_installation(self, opts: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Install TTS engine if needed."""
        engine_id = opts.get("tts_engine", self.state.config.tts_engine if self.state.config else "espeak")
        
        if self.state.config:
            self.state.config.tts_engine = engine_id
        
        # Check if already installed
        from .tts_engine import TTSEngine
        engine = TTSEngine.use(engine_id)
        
        if engine.is_available:
            return {
                "success": True,
                "step_data": {"installed": True, "engine": engine_id},
            }
        
        # Attempt installation
        target_dir = self.weslr_home / "tts"
        success = TTSEngine.install_engine(engine_id, target_dir)
        
        if not success:
            return {
                "success": False,
                "step_data": {"installed": False, "engine": engine_id},
                "hints": {
                    "install_command": self._get_install_command(engine_id),
                    "can_skip": True,  # User can skip and use fallback
                }
            }
        
        self._save_state()
        return {"success": True, "step_data": {"installed": True, "engine": engine_id}}

    def _step_voice_selection(self, opts: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Select voice characteristics."""
        from .tts_engine import TTSEngine
        
        engine_id = self.state.config.tts_engine if self.state.config else "espeak"
        engine = TTSEngine.use(engine_id)
        voices = engine.list_voices()
        
        return {
            "success": True,
            "step_data": {
                "voices": voices,
                "selected_default": voices[0]["id"] if voices else "en",
            },
        }

    def _step_capabilities(self, opts: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Enable optional capabilities."""
        if self.state.config:
            self.state.config.enable_stt = opts.get("enable_stt", False)
            self.state.config.enable_voice_io = opts.get("enable_voice_io", True)
            self.state.config.enable_ws_server = opts.get("enable_ws_server", True)
        
        self._save_state()
        return {"success": True}

    def _step_verification(self, opts: Dict[str, Any]) -> Dict[str, Any]:
        """Step 6: Verify installation and write final config."""
        from .tts_engine import TTSEngine
        
        # Final TTS check
        engine_id = self.state.config.tts_engine if self.state.config else "espeak"
        engine = TTSEngine.use(engine_id)
        
        if not engine.is_available:
            # Fall back to espeak
            engine = TTSEngine.use("espeak")
            if self.state.config:
                self.state.config.tts_engine = "espeak"
        
        # Create config file
        config_path = self.weslr_home / f"config_{self.tenant_id}.json"
        config_path.write_text(json.dumps(self.state.config.to_dict(), indent=2))
        
        self.state.stage = OnboardingStage.COMPLETE.value
        self.state.completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._save_state()
        
        # Test TTS
        test_result = engine.speak("Weslr is online.")
        
        return {
            "success": True,
            "step_data": {
                "config_file": str(config_path),
                "tts_test_success": test_result.success,
                "engine": engine.engine_name,
            },
        }

    def _detect_os(self) -> OSType:
        """Detect operating system type."""
        if Path("/data/data/com.termux/files/home").exists():
            return OSType.ANDROID
        elif Path("/etc/os-release").exists():
            if Path("/etc/debian_version").exists():
                return OSType.LINUX
            return OSType.LINUX_SERVER
        return OSType.UNKNOWN

    def _detect_gpu(self) -> bool:
        """Detect if GPU is available."""
        # Check for NVIDIA
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check for CUDA
        if os.environ.get("CUDA_VISIBLE_DEVICES"):
            return True
        
        return False

    def _detect_ram(self) -> int:
        """Detect total RAM in MB."""
        try:
            with open("/proc/meminfo") as f:
                line = f.readline()
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return kb // 1024
        except Exception:
            pass
        return 0

    def _detect_playback_backend(self) -> Optional[str]:
        """Detect available audio playback backend."""
        import subprocess
        for cmd in ["mpv", "termux-media-player", "ffplay"]:
            try:
                result = subprocess.run(
                    ["which", cmd],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return cmd
            except Exception:
                pass
        return None

    def test_tts_playback(self, engine_name: str) -> Dict[str, Any]:
        """Test TTS generation with a given engine (no actual playback)."""
        from .tts_engine import TTSEngine
        test_phrase = "Weslr voice layer initialized. All systems nominal."
        try:
            engine = TTSEngine.use(engine_name)
            result = engine.speak(test_phrase)
            return {
                "engine": engine_name,
                "success": result.success,
                "audio_size": len(result.audio_data) if result.audio_data else 0,
                "duration": result.duration_seconds,
                "error": result.error,
            }
        except Exception as e:
            return {
                "engine": engine_name,
                "success": False,
                "audio_size": 0,
                "duration": 0.0,
                "error": str(e),
            }

    def _get_install_command(self, engine_id: str) -> str:
        """Get installation command for TTS engine."""
        commands = {
            "gtts": "Already installed on Termux — no extra installation needed",
            "piper": "Download from https://github.com/rhasspy/piper (compile for arm64 on Android)",
            "espeak": "pkg install espeak-ng (Termux) or apt install espeak-ng (Debian/Ubuntu)",
            "coqui": "pip install TTS (requires NVIDIA GPU with CUDA)",
        }
        return commands.get(engine_id, "")

    def next_step(self) -> None:
        """Advance to next step."""
        if self.state:
            self.state.current_step += 1
            self.state.step_name = ""
            self.state.error = None
            self._save_state()

    def get_status(self) -> Dict[str, Any]:
        """Get current onboarding status."""
        if not self.state:
            return {"stage": "not_started"}
        return self.state.to_dict()


# ============================================================================
# FACTORY
# ============================================================================

def get_onboarding_engine(tenant_id: str, weslr_home: Optional[Path] = None) -> OnboardingEngine:
    """Get onboarding engine for tenant."""
    return OnboardingEngine(tenant_id=tenant_id, weslr_home=weslr_home)