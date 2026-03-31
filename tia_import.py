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


def normalize_tia_envelope(envelope: dict) -> dict:
    """Normalize raw TIA import envelope to canonical industrial structure.

    Lightweight wrapper - no assumption-heavy field mapping.
    """

    def _safe_list(value: Any) -> tuple[list, str | None]:
        """Return empty list and warning if value is missing or not a list."""
        if not isinstance(value, list):
            if value is None:
                return [], "field is missing"
            return [], "field is not a list"
        return value, None

    raw = envelope.get("raw_data", {})
    raw_validation = envelope.get("validation", {})

    warnings = []

    # Safe extraction with defensive handling per section
    project = raw.get("project", {})
    if not isinstance(project, dict):
        project = {}
        warnings.append("project is not an object")

    devices, dev_warn = _safe_list(raw.get("devices", []))
    if dev_warn:
        warnings.append(f"devices: {dev_warn}")

    plcs, plc_warn = _safe_list(raw.get("plcs", []))
    if plc_warn:
        warnings.append(f"plcs: {plc_warn}")

    cpus, cpu_warn = _safe_list(raw.get("cpus", []))
    if cpu_warn:
        warnings.append(f"cpus: {cpu_warn}")

    modules, mod_warn = _safe_list(raw.get("modules", []))
    if mod_warn:
        warnings.append(f"modules: {mod_warn}")

    tags, tag_warn = _safe_list(raw.get("tags", []))
    if tag_warn:
        warnings.append(f"tags: {tag_warn}")

    # Normalize project (minimal)
    normalized_project = {
        "id": project.get("id", ""),
        "name": project.get("name", "Unknown"),
        "kind": "project",
        "raw": project,
    }

    # Normalize collections (lightweight wrappers)
    def _normalize_item(item: dict, kind: str) -> dict:
        """Lightweight item wrapper: id, name, kind, raw."""
        return {
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "kind": kind,
            "raw": item,
        }

    normalized_devices = [_normalize_item(d, "device") for d in devices]
    normalized_plcs = [_normalize_item(p, "plc") for p in plcs]
    normalized_cpus = [_normalize_item(c, "cpu") for c in cpus]
    normalized_modules = [_normalize_item(m, "module") for m in modules]
    normalized_tags = [_normalize_item(t, "tag") for t in tags]

    # Build final structure
    now_ts = int(time.time() * 1000)
    return {
        "ok": envelope.get("ok", False),
        "envelope_type": "tia_normalized",
        "project": normalized_project,
        "devices": normalized_devices,
        "plcs": normalized_plcs,
        "cpus": normalized_cpus,
        "modules": normalized_modules,
        "tags": normalized_tags,
        "metadata": {
            "validation": raw_validation,
            "source_envelope": envelope.get("filename", ""),
            "imported_at": envelope.get("imported_at", 0),
            "normalization": {
                "warnings": warnings,
                "item_counts": {
                    "devices": len(normalized_devices),
                    "plcs": len(normalized_plcs),
                    "cpus": len(normalized_cpus),
                    "modules": len(normalized_modules),
                    "tags": len(normalized_tags),
                    "total_items": (
                        len(normalized_devices) +
                        len(normalized_plcs) +
                        len(normalized_cpus) +
                        len(normalized_modules) +
                        len(normalized_tags)
                    ),
                },
                "normalized_at": now_ts,
            },
        },
    }


def save_normalized_envelope(normalized: dict, output_path: str | Path) -> dict:
    """Save normalized TIA envelope to JSON file."""
    path = Path(output_path)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2)
        return {"ok": True, "saved_to": str(path)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def record_tia_import_history(envelope: dict, normalized: dict, raw_path: str | Path, norm_path: str | Path, history_path: str | Path) -> dict:
    """Append a history record for a TIA import.

    Status rules:
    - error: if raw envelope is not ok
    - warning: if validation warnings OR normalization warnings exist
    - ok: otherwise
    """
    history_p = Path(history_path)

    # Determine status
    project_name = envelope.get("project_name", "Unknown")
    status = "ok"
    if not envelope.get("ok"):
        status = "error"
    else:
        has_val_warnings = bool(envelope.get("validation", {}).get("warnings"))
        has_norm_warnings = bool(normalized.get("metadata", {}).get("normalization", {}).get("warnings"))
        if has_val_warnings or has_norm_warnings:
            status = "warning"

    # Build record
    record = {
        "timestamp": int(time.time() * 1000),
        "source_file": envelope.get("filename", ""),
        "raw_output": str(raw_path),
        "normalized_output": str(norm_path),
        "project_name": project_name,
        "status": status,
        "validation": {
            "ok": envelope.get("validation", {}).get("ok", False),
            "warnings": len(envelope.get("validation", {}).get("warnings", [])),
            "errors": len(envelope.get("validation", {}).get("errors", [])),
        },
        "item_counts": {
            "devices": normalized.get("metadata", {}).get("normalization", {}).get("item_counts", {}).get("devices", 0),
            "plcs": normalized.get("metadata", {}).get("normalization", {}).get("item_counts", {}).get("plcs", 0),
            "cpus": normalized.get("metadata", {}).get("normalization", {}).get("item_counts", {}).get("cpus", 0),
            "modules": normalized.get("metadata", {}).get("normalization", {}).get("item_counts", {}).get("modules", 0),
            "tags": normalized.get("metadata", {}).get("normalization", {}).get("item_counts", {}).get("tags", 0),
            "total_items": normalized.get("metadata", {}).get("normalization", {}).get("item_counts", {}).get("total_items", 0),
        },
    }

    # Read existing history (append-safe)
    try:
        if history_p.exists():
            with open(history_p, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = {"records": []}
    except Exception:
        history = {"records": []}

    # Append record
    history["records"].append(record)

    # Save history
    try:
        with open(history_p, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        return {"ok": True, "record": record}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_tia_import_history(history_path: str | Path | None = None, limit: int | None = None) -> dict:
    """Read recent TIA import history records.

    Returns records newest-first.
    If history_path is None, defaults to tia_import_history.json in workspace root.
    If limit is None or <= 0, uses default 10.
    """
    if history_path is None:
        history_path = Path(__file__).resolve().parent / "tia_import_history.json"
    else:
        history_path = Path(history_path)

    if not history_path.exists():
        return {"ok": False, "error": f"History file not found: {history_path}"}

    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    records = history.get("records", [])
    if not records:
        return {"ok": True, "history_file": str(history_path), "total_records": 0, "records": []}

    # Normalize limit
    if limit is None or limit <= 0:
        limit = 10
    if limit > len(records):
        limit = len(records)

    # Return newest-first, slice to limit
    recent = list(reversed(records))[:limit]

    return {
        "ok": True,
        "history_file": str(history_path),
        "total_records": len(records),
        "records": recent,
    }
