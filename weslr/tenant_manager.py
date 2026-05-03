"""
Tenant Manager — Phase 4.4

Create, list, and manage tenants. Each tenant has isolated data directories,
configuration, and domain schema.

Usage:
    init_tenant("oncology_team", "cancer_research", {})
    list_tenants()           → ["astronomy_dept", "materials_lab"]
    get_tenant_info("materials_lab") → {...}
    switch_tenant("materials_lab")  → sets current thread's tenant
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from weslr.tenant_context import (
    get_current_tenant,
    get_tenant_config_path,
    get_tenant_dir,
    has_tenant,
    list_tenants as list_tenant_ids,
    set_current_tenant,
)

# Module-level workspace root (used to copy default schemas)
_WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()


def init_tenant(
    tenant_id: str,
    domain: str = "cancer_research",
    config_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new tenant directory with config and default schema.

    Args:
        tenant_id: unique alphanumeric identifier (a-z, 0-9, underscore)
        domain: initial domain schema (e.g., cancer_research, materials_science)
        config_overrides: optional dict to merge into the default config

    Returns:
        The full tenant config dict

    Raises:
        ValueError: if tenant_id is invalid or already exists
    """
    import re

    if not re.match(r"^[a-zA-Z0-9_]+$", tenant_id):
        raise ValueError(
            f"Tenant ID must be alphanumeric/underscore, got: {tenant_id!r}"
        )
    if has_tenant(tenant_id):
        raise ValueError(f"Tenant {tenant_id!r} already exists")

    if config_overrides is None:
        config_overrides = {}

    # Build tenant config
    config: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "domain": domain,
        "version": "1.0",
        "store_document_text": True,
        "monitor_literature": False,
        "search_sources": ["pubmed"],
        "fact_confidence_threshold": 0.3,
        "auto_ingest_enabled": False,
        "max_facts_per_source": 500,
        **config_overrides,
    }

    # Create tenant directory and write config
    tenant_dir = get_tenant_dir(tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    config_path = get_tenant_config_path(tenant_id)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    # Copy domain schema from workspace schemas/ into tenant space
    _copy_domain_schema(tenant_id, domain)

    # Create subdirectories
    for sub in (".weslr", "documents", "evidence_packets"):
        (tenant_dir / sub).mkdir(exist_ok=True)

    # Initialize empty fact store
    fact_store = tenant_dir / ".weslr" / "fact_assertions.jsonl"
    fact_store.touch()

    return config


def _copy_domain_schema(tenant_id: str, domain: str) -> None:
    """Copy the workspace schema file into the tenant directory."""
    schema_src = _WORKSPACE_ROOT / "weslr" / "schemas" / f"{domain}.json"
    if not schema_src.exists():
        schema_src = _WORKSPACE_ROOT / "weslr" / "schemas" / "base.json"
    schema_dst = get_tenant_dir(tenant_id) / "tenant_schema.json"
    shutil.copy2(schema_src, schema_dst)


def get_tenant_info(tenant_id: str) -> Optional[Dict[str, Any]]:
    """Load and return tenant config, or None if not found."""
    if not has_tenant(tenant_id):
        return None
    config_path = get_tenant_config_path(tenant_id)
    with open(config_path) as f:
        return json.load(f)


def switch_tenant(tenant_id: str) -> Dict[str, Any]:
    """Switch the current thread to the given tenant.

    Returns the tenant config.

    Raises:
        ValueError: if tenant does not exist
    """
    if not has_tenant(tenant_id):
        raise ValueError(f"Tenant {tenant_id!r} does not exist")
    set_current_tenant(tenant_id)
    return get_tenant_info(tenant_id)


def destroy_tenant(tenant_id: str, confirm: bool = False) -> None:
    """Delete a tenant directory and all its data.

    Requires confirm=True to prevent accidental deletion.
    """
    if not confirm:
        raise ValueError("Must pass confirm=True to destroy a tenant")
    import shutil
    tenant_dir = get_tenant_dir(tenant_id)
    if tenant_dir.exists():
        shutil.rmtree(tenant_dir)


def update_tenant_config(
    tenant_id: str, updates: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge updates into a tenant's config file."""
    if not has_tenant(tenant_id):
        raise ValueError(f"Tenant {tenant_id!r} does not exist")
    config = get_tenant_info(tenant_id)
    config.update(updates)
    config_path = get_tenant_config_path(tenant_id)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    return config


def list_tenants() -> List[Dict[str, Any]]:
    """Return list of all tenant info dicts (id, domain, active flag)."""
    current = get_current_tenant()
    results = []
    for tid in list_tenant_ids():
        info = get_tenant_info(tid)
        if info:
            info["is_active"] = tid == current
            results.append(info)
    return results