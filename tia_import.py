"""TIA Openness raw export envelope.

Minimal raw import intake for TIA export artifacts.
No normalization. No entity mapping. Just envelope wrapping.
"""

from __future__ import annotations

import json
from pathlib import Path
import time


def load_tia_export(filepath: str | Path) -> dict:
    """Load TIA export JSON artifact."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"TIA export not found: {filepath}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_export_shape(export: dict) -> dict:
    """Validate minimal TIA export shape.

    Returns dict with 'ok', 'warnings', 'errors'.
    """
    result = {"ok": True, "warnings": [], "errors": []}

    if not isinstance(export, dict):
        result["ok"] = False
        result["errors"].append("TIA export must be a JSON object")
        return result

    if "project" not in export:
        result["warnings"].append("TIA export missing 'project' field")

    if "project" in export and not isinstance(export.get("project"), dict):
        result["warnings"].append("TIA project must be an object")

    if "project" in export and "name" not in export.get("project", {}):
        result["warnings"].append("TIA project missing 'name' field")

    return result


def create_raw_import_envelope(filepath: str | Path) -> dict:
    """Create canonical raw import envelope for TIA export."""
    path = Path(filepath)
    filename = path.name

    try:
        export = load_tia_export(filepath)
    except FileNotFoundError as e:
        return {"ok": False, "error": str(e), "filename": filename}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"Invalid JSON: {e}", "filename": filename}
    except Exception as e:
        return {"ok": False, "error": f"Load error: {e}", "filename": filename}

    validation = validate_export_shape(export)

    now_ts = int(time.time() * 1000)

    # Use validation to determine safe defaults
    export_name = "Unknown"
    if validation.get("ok"):
        export_name = export.get("project", {}).get("name", "Unknown")

    envelope = {
        "ok": validation["ok"],
        "envelope_type": "tia_raw_import",
        "filename": filename,
        "imported_at": now_ts,
        "export_timestamp": "",
        "collector_version": "",
        "project_name": export_name,
        "validation": validation,
        "raw_data": export,
    }
    return envelope


def save_import_envelope(envelope: dict, output_path: str | Path) -> dict:
    """Save import envelope to JSON file."""
    path = Path(output_path)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2)
        return {"ok": True, "saved_to": str(path)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
