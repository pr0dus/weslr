"""Pytest configuration for WESLR tests."""

import sys
from pathlib import Path

# Setup path at pytest session start
_weslr_root = Path(__file__).resolve().parent
if str(_weslr_root) not in sys.path:
    sys.path.insert(0, str(_weslr_root))
