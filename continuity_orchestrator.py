"""Silent Continuity Orchestrator v1 - WESLR anchored.

This is now a compatibility shim that delegates to weslr.continuity.
WESLR is the platform; this adapter ensures backward compatibility.

Phase 1: Foundation (snapshot load/write, confidence/debt, restore plans)
Phase 2: Live snapshot integration (auto-write after state_core.json)
Phase 3: Restore decision logic (conservative partial restore)
Phase 5: Observability metrics (internal only)
"""

from __future__ import annotations

import sys
import os

# Add workspace root to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weslr.continuity import (
    load_weslr_continuity_state,
    build_snapshot,
    save_snapshot,
    load_snapshot,
    list_snapshots,
    calculate_confidence,
    calculate_continuity_debt,
    build_restore_plan,
    get_current_snapshot_info,
    restore_from_plan,
    RESTORE_NO_RESTORE,
    RESTORE_PARTIAL_RESTORE,
    RESTORE_BLOCKED,
    RESTORE_SKIPPED_STALE,
    load_latest_snapshot,
    get_snapshot_age_hours,
    should_attempt_restore,
    check_restore_conditions,
    apply_partial_restore,
    load_continuity_metrics,
    save_continuity_metrics,
    update_metrics_after_snapshot,
    update_metrics_after_restore,
)

# Keep BASE_DIR for backward compatibility
BASE_DIR = "/data/data/com.termux/files/home/.openclaw/workspace"
CONTINUITY_DIR = os.path.join(BASE_DIR, "continuity")
SNAPSHOT_DIR = os.path.join(CONTINUITY_DIR, "snapshots")
