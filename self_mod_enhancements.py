# self_mod_enhancements.py - Phase 7 enhancements for self-modification
from __future__ import annotations

import json
import time
from pathlib import Path


def generate_autonomous_suggestion(current_state: str) -> dict:
    """Generate autonomous self-improvement suggestions based on current state."""
    # Analyze self_mod_log for repeated needs
    mod_log = load_mod_log()
    
    # Find files with pending or failed modifications
    pending_by_file = {}
    for entry in mod_log:
        if not entry.get("success", True):
            file_path = entry.get("file_path", "unknown")
            if file_path not in pending_by_file:
                pending_by_file[file_path] = []
            pending_by_file[file_path].append(entry)
    
    # Find files with many modifications (potential for optimization)
    mod_count_by_file = {}
    for entry in mod_log:
        file_path = entry.get("file_path", "unknown")
        mod_count_by_file[file_path] = mod_count_by_file.get(file_path, 0) + 1
    
    suggestions = []
    
    # Generate suggestions based on patterns
    if pending_by_file:
        for file_path, entries in pending_by_file.items():
            suggestions.append({
                "type": "pending_issues",
                "file_path": file_path,
                "count": len(entries),
                "description": f"Found {len(entries)} pending/failed modification(s) in {file_path}",
                "suggestion": "Review and apply pending modifications or investigate failures",
                "priority": "high" if len(entries) > 3 else "medium",
            })
    
    if mod_count_by_file:
        # Suggest optimization for files with many modifications
        for file_path, count in mod_count_by_file.items():
            if count >= 10:
                suggestions.append({
                    "type": "optimization_candidate",
                    "file_path": file_path,
                    "mod_count": count,
                    "description": f"{file_path} has {count} modifications - consider refactoring",
                    "suggestion": "Review if this file needs frequent changes or can be refactored",
                    "priority": "low" if count < 20 else "medium",
                })
    
    # Generate a high-level observation
    if suggestions:
        summary = f"Weslr has identified {len(suggestions)} potential self-improvement opportunities:"
        for s in suggestions[:3]:
            summary += f"\n- {s.get('description', '')}"
    else:
        summary = "No immediate self-improvement opportunities identified. System appears stable."
    
    return {
        "ok": True,
        "current_state": current_state,
        "suggestions": suggestions,
        "summary": summary,
        "generated_at": int(time.time()),
    }


def load_mod_log() -> list:
    """Load modification log."""
    log_path = Path(__file__).parent / "self_mod_log.json"
    if not log_path.exists():
        return []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def check_modification_safety(file_path: str, change: str) -> dict:
    """Check if a modification is safe to apply."""
    # Read current content
    circleforge_dir = Path(__file__).parent
    full_path = circleforge_dir / file_path
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except Exception as e:
        return {"ok": False, "error": f"Could not read file: {e}"}
    
    # Safety checks
    checks = {
        "no_import_star": "from * import" not in change,
        "no_system_call": "os.system" not in change and "subprocess.run" not in change,
        "no_path_traversal": "../" not in change,
        "no_eval": "eval(" not in change and "exec(" not in change,
        "reasonable_size": len(change) < 10000,
    }
    
    safe = all(checks.values())
    
    return {
        "ok": True,
        "file_path": file_path,
        "change": change[:200] + ("..." if len(change) > 200 else ""),
        "checks": checks,
        "safe": safe,
        "generated_at": int(time.time()),
    }


def validate_modification(file_path: str, change: str, rationale: str) -> dict:
    """Validate a modification before applying."""
    safety = check_modification_safety(file_path, change)
    
    if not safety.get("ok"):
        return safety
    
    if not safety.get("safe"):
        return {
            "ok": False,
            "error": "Modification failed safety checks",
            "checks": safety.get("checks", {}),
            "rationale": rationale,
        }
    
    return {
        "ok": True,
        "file_path": file_path,
        "change": change,
        "rationale": rationale,
        "checks": safety.get("checks", {}),
        "safe": True,
        "generated_at": int(time.time()),
    }


def generate_rollback_preview(file_path: str, current_content: str, original_content: str) -> dict:
    """Generate a preview of what a rollback would do."""
    # Find differences
    current_lines = current_content.splitlines()
    original_lines = original_content.splitlines()
    
    # Simple line-by-line comparison
    added = []
    removed = []
    changed = []
    
    for i, (curr, orig) in enumerate(zip(current_lines, original_lines)):
        if curr != orig:
            if orig and not curr:
                removed.append(f"Line {i}: {orig[:100]}")
            elif curr and not orig:
                added.append(f"Line {i}: {curr[:100]}")
            else:
                changed.append(f"Line {i}: {orig[:50]} -> {curr[:50]}")
    
    # Check for extra lines in current
    if len(current_lines) > len(original_lines):
        for i in range(len(original_lines), len(current_lines)):
            added.append(f"Line {i} (new): {current_lines[i][:100]}")
    
    return {
        "ok": True,
        "file_path": file_path,
        "added_lines": len(added),
        "removed_lines": len(removed),
        "changed_lines": len(changed),
        "preview": {
            "added": added[:5],
            "removed": removed[:5],
            "changed": changed[:5],
        },
        "generated_at": int(time.time()),
    }


def create_scheduled_modification(file_path: str, change: str, rationale: str, 
                                   approved_by: str = "human", scheduled_at: int = 0) -> dict:
    """Create a scheduled modification (for future execution)."""
    now_ts = int(time.time())
    scheduled_ts = scheduled_at or now_ts + 60  # Default: 1 minute from now
    
    return {
        "ok": True,
        "file_path": file_path,
        "change": change,
        "rationale": rationale,
        "approved_by": approved_by,
        "scheduled_at": scheduled_ts,
        "created_at": now_ts,
        "status": "scheduled",
        "generated_at": now_ts,
    }


def batch_modifications(modifications: list[dict]) -> dict:
    """Batch multiple modifications together."""
    if not modifications:
        return {"ok": False, "error": "No modifications provided"}
    
    results = []
    safe_count = 0
    unsafe_count = 0
    
    for mod in modifications:
        file_path = mod.get("file_path", "")
        change = mod.get("change", "")
        validated = validate_modification(file_path, change, mod.get("rationale", ""))
        
        if validated.get("ok") and validated.get("safe"):
            safe_count += 1
            results.append({
                "file_path": file_path,
                "status": "safe",
                "checks": validated.get("checks", {}),
            })
        else:
            unsafe_count += 1
            results.append({
                "file_path": file_path,
                "status": "unsafe",
                "error": validated.get("error", "Unknown error"),
            })
    
    return {
        "ok": True,
        "total": len(modifications),
        "safe": safe_count,
        "unsafe": unsafe_count,
        "results": results,
        "generated_at": int(time.time()),
    }
