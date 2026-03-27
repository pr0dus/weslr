# self_mod_dashboard.py - Dashboard integration for Weslr self-modification
from __future__ import annotations

import json
import os
import time
from pathlib import Path


DASHBOARD_DIR = Path(__file__).parent / "dashboard"
SELF_MOD_DIR = DASHBOARD_DIR / "self-mod"


def ensure_self_mod_dashboard_dir() -> None:
    """Ensure the self-mod dashboard directory exists."""
    SELF_MOD_DIR.mkdir(parents=True, exist_ok=True)


def render_self_mod_dashboard() -> dict:
    """Render the self-modification dashboard HTML."""
    ensure_self_mod_dashboard_dir()

    # Load modification log
    mod_log = load_mod_log()
    checkpoints = list_checkpoints()
    pending = get_pending_modifications()

    dashboard_data = {
        "modifications": mod_log[-10:],
        "pending": pending,
        "checkpoints": checkpoints.get("checkpoints", []),
        "total_mods": len(mod_log),
        "total_checkpoints": checkpoints.get("total", 0),
        "generated_at": int(time.time()),
    }

    # Save JSON data for the dashboard
    json_path = SELF_MOD_DIR / "data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2)

    # Generate HTML
    html = generate_self_mod_dashboard_html(dashboard_data)

    # Save HTML
    html_path = SELF_MOD_DIR / "index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "ok": True,
        "json_path": str(json_path),
        "html_path": str(html_path),
        "generated_at": int(time.time()),
    }


def generate_self_mod_dashboard_html(data: dict) -> str:
    """Generate HTML for the self-modification dashboard."""
    mod_items = ""
    for mod in data.get("modifications", []):
        status = "applied" if mod.get("success") else "pending"
        mod_items += f"""
        <div class="mod-entry {status}">
            <h4>{mod.get("file_path", "unknown")}</h4>
            <p><strong>Rationale:</strong> {mod.get("rationale", "")[:100]}...</p>
            <p><small>{mod.get("timestamp", 0)}</small></p>
        </div>"""

    checkpoint_items = ""
    for cp in data.get("checkpoints", [])[:10]:
        checkpoint_items += f"<li>{cp}</li>"

    pending_items = ""
    for p in data.get("pending", [])[:5]:
        pending_items += f"""
        <div class="pending-mod">
            <h5>{p.get("file_path", "unknown")}</h5>
            <p>{p.get("change", "")[:80]}...</p>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Weslr Self-Modification Dashboard</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #1a1a2e; color: #eee; }}
        .mod-entry {{ background: #16213e; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .mod-entry.applied {{ border-left: 4px solid #4caf50; }}
        .mod-entry.pending {{ border-left: 4px solid #ff9800; }}
        .mod-entry h4 {{ margin: 0 0 5px 0; }}
        .mod-entry p {{ margin: 0; color: #aaa; }}
        .section {{ margin: 20px 0; }}
        .section h2 {{ color: #e94560; border-bottom: 1px solid #333; padding-bottom: 5px; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ background: #0f3460; padding: 8px; margin: 5px 0; border-radius: 3px; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat {{ background: #0f3460; padding: 15px; border-radius: 5px; }}
        .stat strong {{ font-size: 24px; color: #e94560; }}
        .stat span {{ font-size: 12px; color: #aaa; }}
    </style>
</head>
<body>
    <h1>Weslr Self-Modification Dashboard</h1>

    <div class="stats">
        <div class="stat">
            <strong>{data.get("total_mods", 0)}</strong>
            <span>Total Modifications</span>
        </div>
        <div class="stat">
            <strong>{data.get("total_checkpoints", 0)}</strong>
            <span>Total Checkpoints</span>
        </div>
    </div>

    <div class="section">
        <h2>Recent Modifications</h2>
        {mod_items or "<p>No modifications yet.</p>"}
    </div>

    <div class="section">
        <h2>Recent Checkpoints</h2>
        <ul>{checkpoint_items or "<li>No checkpoints yet.</li>"}</ul>
    </div>

    <div class="section">
        <h2>Pending Modifications</h2>
        {pending_items or "<p>No pending modifications.</p>"}
    </div>

    <p><small>Last updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('generated_at', 0)))}</small></p>
</body>
</html>"""


def load_mod_log() -> list:
    """Load modification log from the self-mod applier."""
    from self_mod_applier import load_mod_log as get_mod_log
    return get_mod_log()


def list_checkpoints() -> dict:
    """List checkpoints from the self-mod applier."""
    from self_mod_applier import list_checkpoints as get_checkpoints
    return get_checkpoints()


def get_pending_modifications() -> list:
    """Get pending modifications."""
    log = load_mod_log()
    return [m for m in log if not m.get("success", True)]


def update_dashboard() -> dict:
    """Update the self-modification dashboard."""
    return render_self_mod_dashboard()


def get_dashboard_status() -> dict:
    """Get status of the self-modification dashboard."""
    try:
        html_path = SELF_MOD_DIR / "index.html"
        json_path = SELF_MOD_DIR / "data.json"

        return {
            "ok": True,
            "html_exists": html_path.exists(),
            "json_exists": json_path.exists(),
            "html_path": str(html_path),
            "json_path": str(json_path),
            "last_updated": int(os.path.getmtime(html_path)) if html_path.exists() else 0,
            "generated_at": int(time.time()),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "generated_at": int(time.time()),
        }
