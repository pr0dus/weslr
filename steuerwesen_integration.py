"""Integration module for Weslr Steuer (German tax law) with core Weslr systems."""

from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))


def load_steuerwesen_module():
    """Load the steuerwesen plugin module."""
    try:
        # Try loading from plugins directory
        import plugins
        result = plugins.load_plugin("steuerwesen")
        if result.get("ok"):
            return sys.modules["steuerwesen"]
    except Exception:
        pass
    
    # Fallback: direct import
    try:
        import steuerwesen
        return steuerwesen
    except ImportError:
        return None


def get_steuerwesen_domains():
    """Get list of available tax domains."""
    module = load_steuerwesen_module()
    if module:
        return [d["name"] for d in module.list_domains()]
    return []


def search_tax_laws(query: str, domain: str = None):
    """Search across tax law documentation."""
    module = load_steuerwesen_module()
    if module:
        return module.search_laws(query, domain=domain)
    return []


def integrate_with_entity_graph():
    """Integrate tax law entities into Weslr's entity graph."""
    module = load_steuerwesen_module()
    if not module:
        return {"error": "Steuerwesen module not loaded"}
    
    try:
        from entity_graph import get_entity_graph, Entity
        graph = get_entity_graph()
        
        # Extract domain entities from tax documentation
        domains_data = module.list_domains()
        # Extract domain names from the list of dicts
        domains = [d["name"] for d in domains_data]
        created_entities = []
        print(f"  Found {len(domains)} tax domains to integrate")
        
        # First, check which entities already exist
        existing_domains = set()
        existing_laws = set()
        
        for entity in graph.entities.values():
            if entity.name.startswith("tax_") or entity.name in ["estg", "ustg", "kstg", "erbstg", "gewstg"]:
                existing_domains.add(entity.name)
        
        # Create domain entities
        for domain in domains:
            if domain in existing_domains:
                print(f"  Domain {domain} already exists, skipping")
                continue
                
            domain_id = f"tax_{domain}"
            entity = graph.add_entity(
                name=domain,
                entity_type="concept",
                aliases=[domain],
                confidence=0.9,
                is_ghost=False,
                metadata={
                    "domain_type": "tax",
                    "source": "steuerwesen_plugin",
                    "german_name": module.get_translation("de", domain, domain),
                    "english_name": module.get_translation("en", domain, domain)
                }
            )
            entity.add_evidence(
                source="steuerwesen_integration",
                content=f"Tax domain: {domain} - {module.get_translation('de', domain, '')}",
                confidence_boost=0.2
            )
            print(f"  Created domain entity: {domain} (ID: {entity.id})")
            created_entities.append(entity.id)
        
        # Create legal framework entities
        laws = [
            ("estg", "Einkommensteuergesetz", "EStG", "Income Tax Act"),
            ("ustg", "Umsatzsteuergesetz", "UStG", "VAT Act"),
            ("kstg", "Körperschaftsteuergesetz", "KStG", "Corporate Income Tax Act"),
            ("erbstg", "Erbschaftsteuergesetz", "ErbStG", "Inheritance Tax Act"),
            ("gewstg", "Gewerbesteuergesetz", "GewStG", "Business Tax Act"),
        ]
        
        for law_key, de_name, en_name, en_full in laws:
            if law_key in existing_laws:
                print(f"  Law {law_key} already exists, skipping")
                continue
                
            entity = graph.add_entity(
                name=law_key,
                entity_type="concept",
                aliases=[de_name, en_name],
                confidence=0.95,
                is_ghost=False,
                metadata={
                    "law_type": "tax_law",
                    "source": "steuerwesen_plugin",
                    "german_name": de_name,
                    "english_name": en_full
                }
            )
            entity.add_evidence(
                source="steuerwesen_integration",
                content=f"Legal framework: {de_name} ({en_full})",
                confidence_boost=0.25
            )
            print(f"  Created law entity: {law_key} (ID: {entity.id})")
            created_entities.append(entity.id)
        
        # Create relationships between domains and laws
        domain_law_map = {
            "einkommensteuer": ["estg"],
            "umsatzsteuer": ["ustg"],
            "korporationssteuer": ["kstg"],
            "erbschaftsteuer": ["erbstg"],
            "gewerbesteuer": ["gewstg"],
        }
        
        relationships_created = 0
        for domain, laws_list in domain_law_map.items():
            domain_entity = graph.get_entity_by_name(domain)
            if not domain_entity:
                print(f"  Warning: Domain entity '{domain}' not found, skipping relationships")
                continue
            
            for law_key in laws_list:
                law_entity = graph.get_entity_by_name(law_key)
                if not law_entity:
                    print(f"  Warning: Law entity '{law_key}' not found, skipping relationship")
                    continue
                
                # Check if relationship already exists
                existing_rels = graph.get_relationships_for_entity(domain_entity.id)
                # Convert to list for iteration
                rel_list = list(existing_rels) if existing_rels else []
                already_exists = False
                for rel in existing_rels:
                    if (rel.source_id == domain_entity.id and rel.target_id == law_entity.id and 
                        rel.type == "part_of"):
                        already_exists = True
                        break
                
                if already_exists:
                    print(f"  Relationship {domain} -> {law_key} already exists")
                    continue
                
                rel = graph.add_relationship(
                    source_id=domain_entity.id,
                    target_id=law_entity.id,
                    rel_type="part_of",
                    strength=0.85,
                    provenance={
                        "source": "steuerwesen_integration",
                        "timestamp": int(time.time()),
                        "traceable": True
                    }
                )
                if rel:
                    print(f"  Created relationship: {domain} -> {law_key} (ID: {rel.id})")
                    relationships_created += 1
        
        return {
            "ok": True,
            "domains": len(domains),
            "laws": len(laws),
            "entities_created": len(created_entities),
            "relationships_created": relationships_created
        }
        
    except Exception as e:
        import traceback
        return {"error": f"Integration failed: {str(e)}", "traceback": traceback.format_exc()}


def integrate_with_introspection():
    """Add introspection markers for tax law queries."""
    try:
        from introspection import get_introspection_monitor
        monitor = get_introspection_monitor()
        
        # Record confidence signal for tax law confidence
        signal = monitor.record_confidence_signal(
            context="tax_law_query",
            estimated_confidence=0.95  # High confidence for structured tax data
        )
        
        # Record no perturbations - tax laws are well-defined
        return {
            "ok": True,
            "confidence_signal": signal.id,
            "perturbations": 0
        }
    except Exception as e:
        import traceback
        return {"error": f"Introspection integration failed: {str(e)}", "traceback": traceback.format_exc()}


def integrate_with_weslr_cli():
    """Register Steuerwesen commands with Weslr CLI."""
    try:
        from commands import entities
        import inspect
        
        # Check if entities module has register_commands
        if hasattr(entities, "register_commands"):
            module = load_steuerwesen_module()
            if module and hasattr(module, "register_cli_commands"):
                cli_config = module.register_cli_commands()
                return {
                    "ok": True,
                    "commands_added": list(cli_config.get("steuerwesen", {}).get("commands", {}).keys()),
                    "description": cli_config.get("steuerwesen", {}).get("description", "")
                }
        return {"ok": False, "error": "CLI integration not available"}
    except Exception as e:
        import traceback
        return {"error": f"CLI integration failed: {str(e)}", "traceback": traceback.format_exc()}


def integrate_all():
    """Run all integration steps."""
    results = {
        "entity_graph": integrate_with_entity_graph(),
        "introspection": integrate_with_introspection(),
        "cli": integrate_with_weslr_cli(),
        "domains_available": get_steuerwesen_domains()
    }
    
    return results


if __name__ == "__main__":
    import json
    results = integrate_all()
    print(json.dumps(results, indent=2))
