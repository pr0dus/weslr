#!/usr/bin/env python3
"""Safe migration/derivation script for WESLR shadow-core v1.

This script is now a compatibility shim that delegates to weslr.state.
The actual implementation lives in weslr/state.py.

Usage:
    python3 migrate_state.py           # Generate state_core.json
    python3 migrate_state.py --dry-run # Show what would be done
    python3 migrate_state.py --snapshot # Create snapshot in state_history/
"""

from __future__ import annotations

import sys
import os

# Add workspace root to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weslr.state import main

if __name__ == "__main__":
    main()
