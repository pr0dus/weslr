"""
WESLR Frontier Daemon V1

Background thread that periodically generates high-breakthrough material
candidates via the unified matter generator and enqueues notifications.

Configuration (env vars):
    WESLR_FRONTIER_DAEMON_ENABLED   (default: false)
    WESLR_FRONTIER_INTERVAL_HOURS   (default: 24)
    WESLR_FRONTIER_MAX_CANDIDATES   (default: 20)
    WESLR_FRONTIER_BREAKTHROUGH_MIN (default: 0.7)
    WESLR_FRONTIER_NOVELTY_CHECKS   (default: 3)  # max live PubMed/arXiv calls per run

Constraints:
    - Runs as a daemon thread (daemon=True) — exits with main process
    - Read-only generation (no experiment execution)
    - Respects rate limits for novelty checks
    - Tenant-isolated via tenant_context
"""

from __future__ import annotations

import json
import os
import threading
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_ENABLED: bool = os.environ.get("WESLR_FRONTIER_DAEMON_ENABLED", "false").lower() in ("1", "true", "yes")
_INTERVAL_HOURS: float = float(os.environ.get("WESLR_FRONTIER_INTERVAL_HOURS", "24"))
_MAX_CANDIDATES: int = int(os.environ.get("WESLR_FRONTIER_MAX_CANDIDATES", "20"))
_BREAKTHROUGH_MIN: float = float(os.environ.get("WESLR_FRONTIER_BREAKTHROUGH_MIN", "0.7"))
_NOVELTY_CHECKS_MAX: int = int(os.environ.get("WESLR_FRONTIER_NOVELTY_CHECKS", "3"))

_DAEMON_STATE_PATH = ".weslr/daemon_frontier.json"
_DEDUP_CACHE_SIZE = 10

# ── Daemon state (process-global, not tenant-specific) ──────────────────────

class _DaemonState:
    running: bool = False
    last_run: Optional[str] = None
    thread: Optional[threading.Thread] = None
    lock = threading.Lock()

    def to_dict(self) -> dict:
        return {"running": self.running, "last_run": self.last_run}

    def save(self) -> None:
        path = Path(_DAEMON_STATE_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls) -> "_DaemonState":
        state = cls()
        p = Path(_DAEMON_STATE_PATH)
        if p.exists():
            try:
                data = json.loads(p.read_text())
                state.running = data.get("running", False)
                state.last_run = data.get("last_run")
            except Exception:
                pass
        return state


_DAEMON_STATE = _DaemonState.load()


def _enqueue_frontier_notification(message: str, tenant_id: str = "default") -> None:
    """Enqueue a frontier discovery notification via the pending messages queue."""
    try:
        from weslr.pending_messages_queue import enqueue_proactive
        enqueue_proactive(f"🔮 [Frontier Daemon] {message}", session_id=tenant_id)
    except Exception:
        pass  # Never let enqueue failures stop the daemon


def _run_frontier_cycle(tenant_id: str = "default") -> None:
    """Run one frontier discovery cycle for a tenant."""
    try:
        from weslr.modules.frontier_proposer import (
            compute_breakthrough_potential,
            compute_strangeness_score,
            check_novelty,
            score_novelty,
        )
        from weslr.modules.unified_matter_generator import MatterGenerator
        from weslr.modules.frontier_store import FrontierProposalStore

        store = FrontierProposalStore(tenant_id=tenant_id)

        # Generate candidates in strangeness mode
        seed = int(datetime.now(timezone.utc).timestamp()) % 10000
        gen = MatterGenerator(seed=seed, graph_path="weslr/data/material_graph.json")

        candidates = gen.generate_candidates(
            mode="strangeness",
            max_candidates=_MAX_CANDIDATES,
            constraints={"min_abundance": 0.0},
        )

        novelty_checks_done = 0
        added_count = 0

        for struct in candidates:
            formula = struct.composition_string()

            # Compute scores
            novelty = 0.99  # assume novel; will check top candidates
            impact = 0.3
            strangeness = compute_strangeness_score({"name": formula, "description": "", "source_module": "unified_matter_generator"})
            breakthrough = compute_breakthrough_potential(novelty, strangeness, impact)

            if breakthrough < _BREAKTHROUGH_MIN:
                continue

            # Check novelty for top candidates only
            if novelty_checks_done < _NOVELTY_CHECKS_MAX:
                try:
                    lit = check_novelty(formula, domain="materials")
                    novelty = score_novelty(lit.get("count", 0))
                    breakthrough = compute_breakthrough_potential(novelty, strangeness, impact)
                    novelty_checks_done += 1
                except Exception:
                    novelty = 0.5

            if breakthrough < _BREAKTHROUGH_MIN:
                continue

            # Create a minimal proposal dict
            cand_dict = {
                "name": formula,
                "description": f"[Auto-generated] Strangeness candidate: {formula} ({struct.geometry_type}). Generated by frontier daemon.",
                "domain": "materials",
                "source_module": "unified_matter_generator",
                "_structure": struct,
                "_properties": {},
            }

            # Build a FrontierProposal-like dict for scoring
            feasibility = 0.5
            risk = 0.0
            difficulty = "★★★ Hard / high risk"

            from dataclasses import dataclass
            @dataclass
            class _MiniProposal:
                id: str = ""
                title: str = formula
                description: str = cand_dict["description"]
                domain: str = "materials"
                novelty_score: float = novelty
                feasibility_score: float = feasibility
                risk_score: float = risk
                impact_score: float = impact
                difficulty_level: str = difficulty
                proposed_experiment_summary: str = f"Auto-generated material candidate: {formula}"
                literature_check: dict = {}
                provenance: list = ["frontier_daemon"]
                created_at: str = datetime.now(timezone.utc).isoformat()
                strangeness_score: float = strangeness
                breakthrough_potential: float = breakthrough
                toxic_elements: list = []
                dual_use: bool = False
                status: str = "auto_generated"
                retry_count: int = 0
                last_novelty_check: Optional[str] = datetime.now(timezone.utc).isoformat()
                mission_id: Optional[str] = None

            try:
                store.add(_MiniProposal())
                added_count += 1
                _enqueue_frontier_notification(
                    f"High-breakthrough candidate: {formula} "
                    f"(strangeness={strangeness:.2f}, breakthrough={breakthrough:.2f})",
                    tenant_id=tenant_id,
                )
            except Exception:
                pass  # Skip duplicates (deterministic ID)

    except Exception as e:
        pass  # Never let cycle errors stop the daemon


def _poll_loop() -> None:
    """Main daemon poll loop."""
    interval_seconds = _INTERVAL_HOURS * 3600

    while True:
        with _DAEMON_STATE.lock:
            if not _DAEMON_STATE.running:
                break

        now = datetime.now(timezone.utc)
        print(f"[Frontier Daemon] Running cycle at {now.isoformat()}")

        try:
            # Get all configured tenants
            from weslr.tenant_context import list_tenants, get_current_tenant, set_current_tenant

            # Run for default tenant and any additional tenants
            tenants = ["default"]
            try:
                extra = list_tenants()
                tenants.extend([t for t in extra if t != "default"])
            except Exception:
                pass

            for tid in tenants:
                set_current_tenant(tid)
                _run_frontier_cycle(tid)

            _DAEMON_STATE.last_run = now.isoformat()
            _DAEMON_STATE.save()

        except Exception as e:
            print(f"[Frontier Daemon] Cycle error: {e}")

        # Sleep in short increments to allow early shutdown
        for _ in range(int(interval_seconds)):
            if not _DAEMON_STATE.running:
                break
            time.sleep(1)


def start() -> dict:
    """Start the frontier daemon thread. Returns status dict."""
    global _DAEMON_STATE
    with _DAEMON_STATE.lock:
        if _DAEMON_STATE.running:
            return {"status": "already_running", "last_run": _DAEMON_STATE.last_run}
        _DAEMON_STATE.running = True
        _DAEMON_STATE.save()
        t = threading.Thread(target=_poll_loop, name="frontier-daemon", daemon=True)
        _DAEMON_STATE.thread = t
        t.start()
        return {"status": "started", "last_run": _DAEMON_STATE.last_run}


def stop() -> dict:
    """Stop the frontier daemon thread."""
    global _DAEMON_STATE
    with _DAEMON_STATE.lock:
        if not _DAEMON_STATE.running:
            return {"status": "not_running"}
        _DAEMON_STATE.running = False
        _DAEMON_STATE.save()
    return {"status": "stopping", "last_run": _DAEMON_STATE.last_run}


def status() -> dict:
    """Return daemon status."""
    with _DAEMON_STATE.lock:
        return {
            "running": _DAEMON_STATE.running,
            "last_run": _DAEMON_STATE.last_run,
            "interval_hours": _INTERVAL_HOURS,
            "breakthrough_min": _BREAKTHROUGH_MIN,
            "max_candidates": _MAX_CANDIDATES,
        }


if __name__ == "__main__":
    # Manual trigger for testing
    print("Frontier Daemon status:", status())
    if _ENABLED:
        print("Starting daemon...")
        start()
    else:
        print("Daemon disabled (WESLR_FRONTIER_DAEMON_ENABLED=false)")
        print("Run with: WESLR_FRONTIER_DAEMON_ENABLED=true python -m weslr.frontier_daemon")
