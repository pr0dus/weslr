"""Weslr Platform Core (v1)

Portable agent platform, runtime-agnostic.
"""

__version__ = "1.0.0"

from . import continuity
from . import state
from . import task_anchor

__all__ = ["continuity", "state", "task_anchor"]
