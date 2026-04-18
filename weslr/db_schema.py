"""WESLR DB + Schema Utilities v1

Isolated DB initialization and schema migration utilities extracted from sim.py.
Contains only:
- connect() — DB connection with schema version management
- run_schema_migration() — schema version migration

No simulation behavior. No side effects on state files.
"""

from __future__ import annotations

import sqlite3

from config import DB_PATH, SCHEMA_VERSION

SCHEMA = '''
CREATE TABLE IF NOT EXISTS world (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agents (
    name TEXT PRIMARY KEY,
    energy INTEGER NOT NULL,
    storage INTEGER NOT NULL,
    gpu_quota INTEGER NOT NULL,
    reputation REAL NOT NULL,
    last_inspect_at INTEGER NOT NULL,
    last_trade_at INTEGER NOT NULL,
    age_ticks INTEGER NOT NULL,
    next_due_tick INTEGER NOT NULL DEFAULT 0,
    wake_reason TEXT NOT NULL DEFAULT 'initial',
    cadence_interval INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tick INTEGER NOT NULL,
    agent_name TEXT NOT NULL,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    summary TEXT NOT NULL,
    raw_output TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS artifact_proof (
    artifact_id TEXT PRIMARY KEY,
    first_seen_tick INTEGER NOT NULL,
    last_seen_tick INTEGER NOT NULL,
    appearances INTEGER NOT NULL,
    top_pack_hits INTEGER NOT NULL,
    review_exports INTEGER NOT NULL,
    human_approvals INTEGER NOT NULL,
    real_usage_hits INTEGER NOT NULL DEFAULT 0,
    buyer_fit_votes INTEGER NOT NULL DEFAULT 0,
    handoff_acceptances INTEGER NOT NULL DEFAULT 0,
    handoff_rejections INTEGER NOT NULL DEFAULT 0,
    external_validation_state TEXT NOT NULL DEFAULT 'unvalidated',
    last_status TEXT NOT NULL
);
'''


def run_schema_migration(conn: sqlite3.Connection, from_version: int, to_version: int) -> None:
    """Run schema migrations from old to new version."""
    cursor = conn.cursor()

    # Example migration: add new tables or columns between versions
    if from_version < 1:
        # Current version 1 - no migrations yet
        pass

    conn.commit()


def connect() -> sqlite3.Connection:
    """Open a connection to the world DB, running schema setup/migration as needed."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)

    # Handle schema version
    cursor = conn.cursor()

    # Try to read schema version from meta table, then world table
    schema_version = None
    try:
        cursor.execute("SELECT value FROM meta WHERE key = 'schema_version'")
        row = cursor.fetchone()
        if row:
            schema_version = int(row[0])
    except sqlite3.OperationalError:
        # meta table doesn't exist, check world table
        try:
            cursor.execute("SELECT value FROM world WHERE key = 'schema_version'")
            row = cursor.fetchone()
            if row:
                schema_version = int(row[0])
        except sqlite3.OperationalError:
            # Neither table exists, this is a new world
            pass

    if schema_version is None:
        # This is a new world or old world without schema version
        cursor.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        conn.commit()
        schema_version = SCHEMA_VERSION
    elif schema_version < SCHEMA_VERSION:
        # Run migration if needed
        run_schema_migration(conn, schema_version, SCHEMA_VERSION)
        cursor.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        conn.commit()
        schema_version = SCHEMA_VERSION
    elif schema_version > SCHEMA_VERSION:
        # Future schema - halt with error
        raise RuntimeError(
            f"Weslr schema version mismatch: DB has {schema_version}, "
            f"code expects {SCHEMA_VERSION}. Run a newer version or reset."
        )

    columns = {row["name"] for row in conn.execute("PRAGMA table_info(agents)").fetchall()}
    if "next_due_tick" not in columns:
        conn.execute("ALTER TABLE agents ADD COLUMN next_due_tick INTEGER NOT NULL DEFAULT 0")
    if "wake_reason" not in columns:
        conn.execute("ALTER TABLE agents ADD COLUMN wake_reason TEXT NOT NULL DEFAULT 'initial'")
    if "cadence_interval" not in columns:
        conn.execute("ALTER TABLE agents ADD COLUMN cadence_interval INTEGER NOT NULL DEFAULT 1")

    return conn