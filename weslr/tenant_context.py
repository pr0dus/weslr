"""
Tenant Context — Phase 4.4

Provides thread-safe tenant isolation via thread-local storage.
All Weslr file I/O routes through this module to ensure tenant separation.

Usage:
    set_current_tenant("oncology_team")   # set for current thread
    tenant_id = get_current_tenant()      # get current tenant or None
    is_default_tenant()                   # True if using fallback (no tenant set)
    get_tenant_dir()                      # absolute Path to tenant directory
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Optional

# Thread-local storage for tenant context
_local = threading.local()

# Environment variable names
_TENANT_ENV = "WESLR_TENANT_ID"
_TENANT_DIR_ENV = "WESLR_TENANT_DIR"

# Fallback: workspace-relative directory for single-tenant / legacy mode
_WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
_DEFAULT_WESLR_DIR = _WORKSPACE_ROOT / ".weslr"


def set_current_tenant(tenant_id: Optional[str]) -> None:
    """Set the current tenant ID for this thread."""
    if tenant_id is None:
        _local.tenant_id = None
    else:
        _local.tenant_id = tenant_id.strip()


def get_current_tenant() -> Optional[str]:
    """Return the current tenant ID for this thread, or None if not set."""
    return getattr(_local, "tenant_id", None)


def is_default_tenant() -> bool:
    """Return True if no tenant is set (legacy single-tenant mode)."""
    return get_current_tenant() is None


def get_tenant_root() -> Path:
    """Return the root directory for tenants.

    Uses WESLR_TENANT_DIR env var if set, otherwise <workspace>/tenants/.
    """
    if _TENANT_DIR_ENV in os.environ:
        return Path(os.environ[_TENANT_DIR_ENV]).resolve()
    return _WORKSPACE_ROOT / "tenants"


def get_tenant_dir(tenant_id: Optional[str] = None) -> Path:
    """Return the tenant directory for the given tenant (or current).

    Creates the directory (and parents) if it doesn't exist.
    """
    tid = tenant_id or get_current_tenant()
    if tid is None:
        # Legacy mode: return the default .weslr directory
        return _DEFAULT_WESLR_DIR
    tenant_path = get_tenant_root() / tid
    tenant_path.mkdir(parents=True, exist_ok=True)
    return tenant_path


def get_tenant_config_path(tenant_id: Optional[str] = None) -> Path:
    """Return path to tenant_config.json for the given tenant."""
    return get_tenant_dir(tenant_id) / "tenant_config.json"


def resolve_path(relative_path: str, tenant_id: Optional[str] = None) -> Path:
    """Resolve a workspace-relative path into an absolute tenant-path.

    Example:
        resolve_path(".weslr/fact_assertions.jsonl")
        → <tenant_dir>/.weslr/fact_assertions.jsonl

    For default tenant (no tenant set), uses workspace root:
        <workspace>/.weslr/fact_assertions.jsonl
    """
    tid = tenant_id or get_current_tenant()
    if tid is None:
        # Legacy single-tenant
        return _WORKSPACE_ROOT / relative_path
    base = get_tenant_dir(tid)
    return base / relative_path


def list_tenants() -> list[str]:
    """Return sorted list of tenant IDs that have a tenant_config.json."""
    root = get_tenant_root()
    if not root.exists():
        return []
    tenants = []
    for item in root.iterdir():
        if item.is_dir() and (item / "tenant_config.json").exists():
            tenants.append(item.name)
    return sorted(tenants)


def has_tenant(tenant_id: str) -> bool:
    """Return True if a tenant with this ID exists."""
    return get_tenant_config_path(tenant_id).exists()