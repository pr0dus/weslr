"""Weslr Adapter: OpenClaw Runtime (v0.1)

OpenClaw runtime adapter for Weslr platform.
This adapter provides OpenClaw-specific paths and configuration
while maintaining compatibility with the platform contract.

Phase 1: Path injection only (minimal, no breaking changes)
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..contracts import RunResult
from . import AdapterPaths, AdapterRuntime, AdapterCommands, AdapterConfig


class OpenClawPaths(AdapterPaths):
    """OpenClaw path resolution adapter.
    
    Resolves Weslr paths to OpenClaw runtime locations.
    Uses environment variables for flexibility, defaults to typical OpenClaw setup.
    """
    
    def __init__(self, runtime_dir: str = None):
        """Initialize with optional runtime directory override."""
        self._runtime_dir = runtime_dir or self._detect_runtime_dir()
        self._base_dir = self._resolve_base_dir()
    
    def _detect_runtime_dir(self) -> str:
        """Detect OpenClaw runtime directory from environment."""
        # Try to detect from environment
        env_dir = os.getenv("OPENCLAW_RUNTIME_DIR")
        if env_dir:
            return env_dir
        # Default to OpenClaw workspace (current workspace)
        # This is the safest default for now
        return "/data/data/com.termux/files/home/.openclaw/workspace"
    
    def _resolve_base_dir(self) -> str:
        """Resolve Weslr workspace base directory."""
        # Try multiple detection methods
        # 1. Environment variable
        env_base = os.getenv("WESLR_BASE_DIR")
        if env_base:
            return env_base
        
        # 2. Check if running from Weslr CLI
        try:
            # If weslr_main.py is in parent, use that directory
            import sys
            if len(sys.argv) > 0:
                script_path = Path(sys.argv[0]).resolve()
                if script_path.name == "weslr_main.py":
                    return str(script_path.parent)
        except Exception:
            pass
        
        # 3. Check for config.py in workspace
        try:
            candidate = Path(self._runtime_dir) / "config.py"
            if candidate.exists():
                return str(Path(self._runtime_dir))
        except Exception:
            pass
        
        # 4. Default to runtime directory (fallback)
        return self._runtime_dir
    
    # ===== AdapterPaths Interface =====
    def base_dir(self) -> str:
        """Get Weslr workspace root."""
        return self._base_dir
    
    def state_dir(self) -> str:
        """Get state storage directory."""
        return self._base_dir
    
    def continuity_dir(self) -> str:
        """Get continuity snapshots directory."""
        return os.path.join(self._base_dir, "continuity")
    
    def agent_dir(self) -> str:
        """Get agent data directory."""
        return os.path.join(self._base_dir, "agents")
    
    def log_dir(self) -> str:
        """Get log storage directory."""
        return os.path.join(self._base_dir, "logs")


class OpenClawRuntime(AdapterRuntime):
    """OpenClaw runtime environment adapter.
    
    Provides runtime-specific information about the execution environment.
    """
    
    def __init__(self, paths: OpenClawPaths = None):
        """Initialize with path adapter for context."""
        self._paths = paths or OpenClawPaths()
    
    def version(self) -> str:
        """Get OpenClaw runtime version."""
        return os.getenv("OPENCLAW_VERSION", "unknown")
    
    def name(self) -> str:
        """Get runtime name."""
        return "OpenClaw"
    
    def timezone(self) -> str:
        """Get runtime timezone."""
        return os.getenv("TZ", "UTC")
    
    def cpu_count(self) -> int:
        """Get available CPU cores."""
        return os.cpu_count() or 1
    
    def memory_bytes(self) -> int:
        """Get available memory (approximate)."""
        # Simplified for now - could use /proc/meminfo on Linux
        return 1024 * 1024 * 1024  # 1GB default


class OpenClawCommands(AdapterCommands):
    """OpenClaw command execution adapter.
    
    Provides runtime-specific command execution via subprocess.
    """
    
    def __init__(self, paths: OpenClawPaths = None):
        """Initialize with path adapter for working directory."""
        self._paths = paths or OpenClawPaths()
    
    def run_python(self, script: str, args: List[str]) -> RunResult:
        """Execute Python script via subprocess."""
        start_time = time.time()
        try:
            result = subprocess.run(
                ["python3", script] + args,
                cwd=self._paths.base_dir(),
                capture_output=True,
                text=True,
                timeout=300  # 5 min default
            )
            duration_ms = int((time.time() - start_time) * 1000)
            return RunResult(
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                duration_ms=duration_ms
            )
        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            return RunResult(
                stdout="",
                stderr="Command timed out after 300 seconds",
                return_code=1,
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return RunResult(
                stdout="",
                stderr=str(e),
                return_code=1,
                duration_ms=duration_ms
            )
    
    def run_command(self, cmd: str, args: List[str]) -> RunResult:
        """Execute shell command via subprocess."""
        start_time = time.time()
        try:
            result = subprocess.run(
                [cmd] + args,
                cwd=self._paths.base_dir(),
                capture_output=True,
                text=True,
                timeout=300
            )
            duration_ms = int((time.time() - start_time) * 1000)
            return RunResult(
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                duration_ms=duration_ms
            )
        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            return RunResult(
                stdout="",
                stderr="Command timed out after 300 seconds",
                return_code=1,
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return RunResult(
                stdout="",
                stderr=str(e),
                return_code=1,
                duration_ms=duration_ms
            )
    
    def spawn_process(self, cmd: str, args: List[str], callback=None) -> Any:
        """Spawn a background process (returns Popen object)."""
        import subprocess
        return subprocess.Popen(
            [cmd] + args,
            cwd=self._paths.base_dir(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


class OpenClawConfig(AdapterConfig):
    """OpenClaw configuration adapter.
    
    Provides configuration access via environment variables.
    """
    
    def __init__(self, paths: OpenClawPaths = None):
        """Initialize with path adapter for context."""
        self._paths = paths or OpenClawPaths()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value from environment."""
        return os.getenv(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value (session only)."""
        os.environ[key] = str(value)
    
    def get_secret(self, key: str) -> str:
        """Get a sensitive configuration value (secret)."""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Secret '{key}' not found in environment")
        return value


# Convenience factory functions
def create_adapter(paths_dir: str = None) -> Dict[str, Any]:
    """Create all OpenClaw adapters with path context.
    
    This is a convenience function that creates all adapter instances
    sharing the same path context, which is the common case.
    """
    paths = OpenClawPaths(paths_dir)
    return {
        "paths": paths,
        "runtime": OpenClawRuntime(paths),
        "commands": OpenClawCommands(paths),
        "config": OpenClawConfig(paths),
    }
