"""Weslr SQLite Inspection (v1A)

Safe, read-only inspection of SQLite databases for Weslr.
Uses Python stdlib sqlite3 only and never executes user SQL.

Safety Boundaries:
  - Read-only connection via SQLite URI mode=ro
  - Path traversal protection
  - No writes, no schema changes
  - Bounded table list / column list / warning list
  - No row dumping by default
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

__all__ = [
    "SQLiteInspectionError",
    "inspect_sqlite_database",
]


SQLITE_EXTENSIONS = {".sqlite", ".sqlite3", ".db"}
MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_TABLES = 20
MAX_COLUMNS = 50
MAX_WARNINGS = 10
MAX_ROW_COUNT_TABLES = 10


class SQLiteInspectionError(Exception):
    """Raised when SQLite inspection fails."""


def _is_safe_path(filepath: str, workspace_dir: str) -> bool:
    try:
        workspace = Path(workspace_dir).resolve()
        path = Path(filepath).resolve()
        return str(path).startswith(str(workspace) + os.sep) or path == workspace
    except Exception:
        return False


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _format_columns(columns: List[Dict[str, Any]]) -> str:
    return ", ".join(col.get("name", "?") for col in columns[:8])


def _format_sqlite_summary(result: Dict[str, Any]) -> str:
    lines = [
        f"[SQLITE DATABASE] {result.get('table_count', 0)} table(s)",
        "read_only: true",
    ]

    tables = result.get("tables", [])
    if tables:
        lines.append("Tables:")
        for table in tables[:MAX_TABLES]:
            line = f"- {table.get('name', '?')}: columns [{_format_columns(table.get('columns', []))}]"
            if table.get("row_count") is not None:
                line += f", rows {table['row_count']}"
            lines.append(line)

    warnings = result.get("warnings", [])
    if warnings:
        lines.append("Warnings:")
        for warning in warnings[:MAX_WARNINGS]:
            lines.append(f"- {warning}")

    return "\n".join(lines)


def inspect_sqlite_database(filepath: str, workspace_dir: str | None = None) -> Dict[str, Any]:
    workspace = workspace_dir or str(Path(__file__).resolve().parent.parent)

    if not _is_safe_path(filepath, workspace):
        raise SQLiteInspectionError(
            f"Path traversal attempt: {filepath} is outside workspace"
        )

    path = Path(filepath)
    ext = path.suffix.lower()
    if ext not in SQLITE_EXTENSIONS:
        raise SQLiteInspectionError(f"Unsupported SQLite file extension: {ext}")
    if not path.exists():
        raise SQLiteInspectionError(f"File not found: {filepath}")
    if path.is_dir():
        raise SQLiteInspectionError(f"Is a directory, not a file: {filepath}")

    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        raise SQLiteInspectionError(
            f"File too large: {size} bytes (max {MAX_FILE_SIZE})"
        )

    result: Dict[str, Any] = {
        "type": "sqlite_database",
        "read_only": True,
        "table_count": 0,
        "tables": [],
        "warnings": [],
        "metadata": {
            "source_file": path.name,
            "file_size": size,
            "parsed_successfully": False,
            "parse_error": None,
        },
    }

    uri = f"file:{path.resolve()}?mode=ro"
    conn = None
    try:
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row

        table_rows = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        table_names = [str(row[0]) for row in table_rows]
        result["table_count"] = len(table_names)
        if len(table_names) > MAX_TABLES:
            result["warnings"].append(
                f"Table list truncated to first {MAX_TABLES} of {len(table_names)} tables"
            )

        for index, table_name in enumerate(table_names[:MAX_TABLES]):
            table_info: Dict[str, Any] = {
                "name": table_name,
                "columns": [],
                "row_count": None,
            }

            pragma_rows = conn.execute(
                f"PRAGMA table_info({_quote_identifier(table_name)})"
            ).fetchall()
            columns = []
            for row in pragma_rows[:MAX_COLUMNS]:
                columns.append(
                    {
                        "name": row[1],
                        "type": row[2],
                        "notnull": bool(row[3]),
                        "default": row[4],
                        "primary_key": bool(row[5]),
                    }
                )
            if len(pragma_rows) > MAX_COLUMNS:
                result["warnings"].append(
                    f"Column list truncated for table '{table_name}'"
                )
            table_info["columns"] = columns

            if index < MAX_ROW_COUNT_TABLES:
                try:
                    row_count = conn.execute(
                        f"SELECT COUNT(*) FROM {_quote_identifier(table_name)}"
                    ).fetchone()
                    table_info["row_count"] = int(row_count[0]) if row_count else 0
                except Exception:
                    result["warnings"].append(
                        f"Row count unavailable for table '{table_name}'"
                    )

            result["tables"].append(table_info)

        result["metadata"]["parsed_successfully"] = True
    except sqlite3.Error as e:
        result["warnings"].append(f"SQLite inspection failed: {e}")
        result["metadata"]["parse_error"] = str(e)
    finally:
        if conn is not None:
            conn.close()

    result["summary"] = _format_sqlite_summary(result)
    result["structured_output"] = result["summary"]
    return result
