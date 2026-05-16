"""Compatibility shim for the old aggregate meaning/obligation import path.

The implementation now lives in split modules. This file intentionally only
re-exports the public functions expected by legacy callers.
"""

from weslr.linguistic_meaning import analyze_meaning
from weslr.response_obligation import determine_response_obligation

__all__ = ["analyze_meaning", "determine_response_obligation"]
