# self_test.py - Self-integrity test suite for CircleForge
"""
Run self-integrity checks:
1. DB integrity (SQLite PRAGMA)
2. Key files exist
3. Checkpoints readable
4. Schema version check
5. Runtime self-diagnosis (memory pressure, state consistency)
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any

from config import (
    BASE_DIR,
    DB_PATH,
    CHECKPOINT_DIR,
    COMMUNICATOR_STATE_PATH,
    COMMUNICATOR_SELF_PATH,
    PUBLIC_MEMORY_PATH,
    RELATIONSHIPS_PATH,
    SCHEMA_VERSION,
    TICKS_PER_SECOND_LIMIT,
    TICK_TIME_LIMIT_SECONDS,
    CIRCLEFORGE_FAILSAFE_STATE_PATH,
)


def check_db_integrity() -> Dict[str, Any]:
    """Check SQLite database integrity."""
    result = {"check": "db_integrity", "status": "pass", "details": {}}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # PRAGMA integrity_check
        integrity = cursor.execute("PRAGMA integrity_check").fetchall()
        result["details"]["integrity_check"] = "ok" if all(r[0] == "ok" for r in integrity) else "fail"
        
        # Check schema version
        cursor.execute("SELECT value FROM meta WHERE key = 'schema_version'")
        row = cursor.fetchone()
        schema_version = int(row[0]) if row else 0
        result["details"]["schema_version"] = schema_version
        result["details"]["expected_version"] = SCHEMA_VERSION
        
        if schema_version < SCHEMA_VERSION:
            result["status"] = "warn"
            result["details"]["message"] = f"Schema version mismatch: {schema_version} < {SCHEMA_VERSION}"
        elif schema_version > SCHEMA_VERSION:
            result["status"] = "error"
            result["details"]["message"] = f"Schema version mismatch: {schema_version} > {SCHEMA_VERSION}"
        
        conn.close()
        
    except Exception as e:
        result["status"] = "error"
        result["details"]["exception"] = str(e)
    
    return result


def check_key_files() -> Dict[str, Any]:
    """Check if key runtime files exist."""
    result = {"check": "key_files", "status": "pass", "files": {}}
    
    key_files = [
        COMMUNICATOR_STATE_PATH,
        COMMUNICATOR_SELF_PATH,
        PUBLIC_MEMORY_PATH,
        RELATIONSHIPS_PATH,
        CIRCLEFORGE_FAILSAFE_STATE_PATH,
    ]
    
    missing = []
    for f in key_files:
        exists = f.exists() if isinstance(f, Path) else os.path.exists(f)
        path_str = str(f)
        result["files"][path_str] = {"exists": exists}
        if not exists:
            missing.append(path_str)
            result["status"] = "warn"
    
    if missing:
        result["details"] = {"missing": missing}
    
    return result


def check_checkpoints() -> Dict[str, Any]:
    """Check if checkpoints directory exists and is readable."""
    result = {"check": "checkpoints", "status": "pass", "details": {}}
    
    checkpoint_dir = BASE_DIR / "checkpoints"
    if not checkpoint_dir.exists():
        result["status"] = "warn"
        result["details"]["message"] = "Checkpoints directory does not exist"
        return result
    
    try:
        files = list(checkpoint_dir.glob("*.bak"))
        result["details"]["count"] = len(files)
        result["details"]["files"] = [str(f) for f in files[:5]]  # First 5
        
        # Try to read one checkpoint
        if files:
            test_file = files[0]
            try:
                with open(test_file, "r") as f:
                    content = f.read()
                result["details"]["readable"] = True
                result["details"]["sample_length"] = len(content)
            except Exception as e:
                result["status"] = "error"
                result["details"]["readable"] = False
                result["details"]["error"] = str(e)
                
    except Exception as e:
        result["status"] = "error"
        result["details"]["exception"] = str(e)
    
    return result


def run_runtime_self_diagnosis() -> Dict[str, Any]:
    """Runtime self-diagnosis: memory pressure, state consistency."""
    result = {"check": "runtime_diagnosis", "status": "pass", "details": {}}
    
    # Memory pressure check
    try:
        from sim import load_public_memory, load_relationships
        
        public_memory = load_public_memory()
        relationships = load_relationships()
        
        # Handle both dict and list return types
        if isinstance(public_memory, dict):
            entries = public_memory.get("entries", [])
            result["details"]["public_memory_entries"] = len(entries)
        else:
            # If it's a list, treat it as entries directly
            result["details"]["public_memory_entries"] = len(public_memory) if isinstance(public_memory, list) else 0
        result["details"]["relationships_count"] = len(relationships)
        
        # Check for state consistency
        if result["details"]["public_memory_entries"] > 1000:
            result["status"] = "warn"
            result["details"]["memory_pressure"] = "high"
        else:
            result["details"]["memory_pressure"] = "normal"
            
    except Exception as e:
        result["status"] = "error"
        result["details"]["exception"] = str(e)
    
    return result


def check_circuit_breakers() -> Dict[str, Any]:
    """Check circuit breaker configuration."""
    result = {"check": "circuit_breakers", "status": "pass", "details": {}}
    
    result["details"]["tick_time_limit_seconds"] = TICK_TIME_LIMIT_SECONDS
    result["details"]["ticks_per_second_limit"] = TICKS_PER_SECOND_LIMIT
    
    # Load failsafe state to check if circuit breaker is active
    try:
        if CIRCLEFORGE_FAILSAFE_STATE_PATH.exists():
            with open(CIRCLEFORGE_FAILSAFE_STATE_PATH, "r") as f:
                failsafe = json.load(f)
            result["details"]["failsafe_state"] = failsafe.get("state", "unknown")
            result["details"]["circuit_breaker_active"] = failsafe.get("circuit_breaker_active", False)
            
            if failsafe.get("circuit_breaker_active", False):
                result["status"] = "warn"
                result["details"]["message"] = "Circuit breaker is active"
        else:
            result["details"]["failsafe_state"] = "no_state_file"
    except Exception as e:
        result["status"] = "error"
        result["details"]["exception"] = str(e)
    
    return result


def run_self_test() -> Dict[str, Any]:
    """Run all self-integrity tests and return summary."""
    start_time = time.time()
    
    tests = [
        ("db_integrity", check_db_integrity),
        ("key_files", check_key_files),
        ("checkpoints", check_checkpoints),
        ("runtime_diagnosis", run_runtime_self_diagnosis),
        ("circuit_breakers", check_circuit_breakers),
    ]
    
    results = []
    overall_status = "pass"
    
    for name, check_func in tests:
        result = check_func()
        results.append(result)
        if result["status"] == "error":
            overall_status = "error"
        elif result["status"] == "warn" and overall_status != "error":
            overall_status = "warn"
    
    total_time = time.time() - start_time
    
    return {
        "overall_status": overall_status,
        "tests_run": len(tests),
        "results": results,
        "duration_seconds": round(total_time, 3),
    }
