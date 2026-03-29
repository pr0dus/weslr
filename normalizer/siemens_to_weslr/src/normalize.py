"""
Normalizer – Transformation TIA Export → Weslr Normalized Graph (MVP).

Diese Module transformiert Rohexporte aus TIA Portal V20 in das
Weslr-konforme Normalized Graph Format.

Keine externen Abhängigkeiten – nur Standard-Library.
Keine Dateizugriffe – reine In-Memory-Transformation.
Keine CLI – reine Transformationslogik.
"""

import uuid
from datetime import datetime
from typing import Any

from .models import NormalizedEntity, NormalizedRelation, NormalizedGraph


def _normalize_id(raw_id: str | None, prefix: str = "obj") -> str:
    """
    Normalisiert eine ID für das Weslr-Format (4-16 chars, lowercase alphanumeric).
    
    - Falls raw_id nicht geeignet ist, wird eine UUID generiert.
    - Der Prefix hilft bei der Typzuordnung (plc, dev, tag, etc.).
    """
    if raw_id:
        normalized = raw_id.lower().replace("-", "_").replace(".", "_").replace(" ", "_")
        # Kürzen auf 16 chars
        if len(normalized) > 16:
            normalized = normalized[:16]
        if len(normalized) < 4:
            normalized = f"{prefix}_{uuid.uuid4().hex[:12]}"
        if normalized.isalnum():
            return normalized
    # Generiere neue ID, falls raw_id nicht geeignet ist
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _create_entity(
    raw_obj: dict,
    entity_type: str,
    source_file: str,
    source_id: str
) -> NormalizedEntity:
    """
    Erstellt eine NormalizedEntity aus einem Raw-Objekt.
    
    Wandelt Rohtagwerte in Weslr-konforme Attribute um.
    """
    raw_id = raw_obj.get("id", "")
    raw_name = raw_obj.get("name", "")
    
    entity = NormalizedEntity(
        id=_normalize_id(raw_id, prefix=entity_type[:3]),
        name=raw_name,
        type=entity_type,
        attributes=raw_obj.copy(),  # alle Raw-Attribute beibehalten
        confidence=raw_obj.get("confidence", 0.95),
        evidence=raw_obj.get("evidence", []),
        source_file=source_file,
        source_id=source_id
    )
    
    # Entferne重复 Felder, die wir extrahiert haben
    entity.attributes.pop("id", None)
    entity.attributes.pop("name", None)
    entity.attributes.pop("confidence", None)
    entity.attributes.pop("evidence", None)
    
    return entity


def _create_relation(
    raw_rel: dict,
    source_file: str,
    source_id: str
) -> NormalizedRelation:
    """
    Erstellt eine NormalizedRelation aus einem Raw-Relation-Objekt.
    """
    raw_source_id = raw_rel.get("source_id", "")
    raw_target_id = raw_rel.get("target_id", "")
    
    return NormalizedRelation(
        id=_normalize_id(raw_rel.get("id", ""), prefix="rel"),
        source_id=_normalize_id(raw_source_id, prefix="src"),
        target_id=_normalize_id(raw_target_id, prefix="tgt"),
        type=raw_rel.get("type", "connects"),
        strength=raw_rel.get("strength", 1.0),
        provenance=raw_rel.get("provenance"),
        source_file=source_file,
        source_id=source_id
    )


def _extract_project(raw: dict) -> list[NormalizedEntity]:
    """Extrahiert ProjectSnapshots aus dem Raw Export."""
    entities = []
    
    project = raw.get("project", {})
    if project:
        entity = _create_entity(project, "project", source_file="", source_id="")
        entity.type = "project"  # Projekt-Entity hat Typ "project"
        entities.append(entity)
    
    return entities


def _extract_devices(raw: dict) -> list[NormalizedEntity]:
    """Extrahiert Devices aus dem Raw Export."""
    entities = []
    
    for device in raw.get("devices", []):
        entity = _create_entity(device, "device", source_file="", source_id="")
        entities.append(entity)
    
    return entities


def _extract_plcs(raw: dict) -> list[NormalizedEntity]:
    """Extrahiert PLCs aus dem Raw Export."""
    entities = []
    
    for plc in raw.get("plcs", []):
        entity = _create_entity(plc, "plc", source_file="", source_id="")
        entities.append(entity)
    
    return entities


def _extract_cpus(raw: dict) -> list[NormalizedEntity]:
    """Extrahiert CPUs aus dem Raw Export."""
    entities = []
    
    for cpu in raw.get("cpus", []):
        entity = _create_entity(cpu, "cpu", source_file="", source_id="")
        entities.append(entity)
    
    return entities


def _extract_modules(raw: dict) -> list[NormalizedEntity]:
    """Extrahiert Modules (z. B. SM, PS) aus dem Raw Export."""
    entities = []
    
    for module in raw.get("modules", []):
        entity = _create_entity(module, "module", source_file="", source_id="")
        entities.append(entity)
    
    return entities


def _extract_tag_tables(raw: dict) -> list[NormalizedEntity]:
    """Extrahiert Tag-Tables aus dem Raw Export."""
    entities = []
    
    for table in raw.get("tag_tables", []):
        entity = _create_entity(table, "tag_table", source_file="", source_id="")
        entities.append(entity)
    
    return entities


def _extract_tags(raw: dict) -> list[NormalizedEntity]:
    """Extrahiert Tags aus dem Raw Export."""
    entities = []
    
    for tag in raw.get("tags", []):
        entity = _create_entity(tag, "tag", source_file="", source_id="")
        entities.append(entity)
    
    return entities


def _extract_program_blocks(raw: dict) -> list[NormalizedEntity]:
    """Extrahiert Program Blocks (OB, FC, FB, DB) aus dem Raw Export."""
    entities = []
    
    for block in raw.get("program_blocks", []):
        block_type = block.get("type", "ob")
        # Normalisiere Block-Typ (z. B. "ob" → "program_block")
        type_map = {
            "ob": "program_block",  # Organization Block
            "fc": "function_block",  # Function Block
            "fb": "function_block",  # Function Block (mit Speicher)
            "db": "data_block",      # Data Block
            "sg": "symbolic_tag",    # Symbolic Tag
            "dt": "data_type",       # Data Type
        }
        entity_type = type_map.get(block_type, "program_block")
        entity = _create_entity(block, entity_type, source_file="", source_id="")
        entities.append(entity)
    
    return entities


def _extract_alarms(raw: dict) -> list[NormalizedEntity]:
    """Extrahiert Alarme aus dem Raw Export."""
    entities = []
    
    for alarm in raw.get("alarms", []):
        entity = _create_entity(alarm, "alarm", source_file="", source_id="")
        entities.append(entity)
    
    return entities


def _extract_topology(raw: dict) -> list[NormalizedRelation]:
    """Extrahiert Topology-Relationen (Netzwerkverbindungen) aus dem Raw Export."""
    relations = []
    
    for topo in raw.get("topology", []):
        relation = _create_relation(topo, source_file="", source_id="")
        relations.append(relation)
    
    return relations


def _extract_relations(raw: dict) -> list[NormalizedRelation]:
    """Extrahiert alle Relations (auch nicht-topologische) aus dem Raw Export."""
    relations = []
    
    # TIA Export hat keine expliziten Relations außer topology
    # In zukünftigen Szenarien könnten hier weitere Relations kommen
    # (z. B. "contains", "monitors", "triggers")
    
    relations.extend(_extract_topology(raw))
    
    return relations


def _normalize_entities(raw: dict) -> list[NormalizedEntity]:
    """
    Extrahiert und normalisiert alle Entities aus dem Raw Export.
    
    Diese Funktion aggregiert alle spezifischen Extractor-Funktionen.
    """
    entities = []
    
    # Projekte
    entities.extend(_extract_project(raw))
    
    # Devices
    entities.extend(_extract_devices(raw))
    
    # PLCs
    entities.extend(_extract_plcs(raw))
    
    # CPUs
    entities.extend(_extract_cpus(raw))
    
    # Modules
    entities.extend(_extract_modules(raw))
    
    # Tag-Tables
    entities.extend(_extract_tag_tables(raw))
    
    # Tags
    entities.extend(_extract_tags(raw))
    
    # Program Blocks
    entities.extend(_extract_program_blocks(raw))
    
    # Alarme
    entities.extend(_extract_alarms(raw))
    
    return entities


def normalize_tia_export(raw: dict) -> NormalizedGraph:
    """
    Transformiert einen TIA Export (Raw) in einen Weslr Normalized Graph.
    
    Diese Funktion ist die Haupt-Eingabefunktion des Normalizers.
    
    Parameters:
        raw (dict): Roher TIA Export aus tia_export.schema.json
    
    Returns:
        NormalizedGraph: Weslr-konformer Graph mit Entities und Relations
    """
    # Entities extrahieren
    entities = _normalize_entities(raw)
    
    # Relations extrahieren
    relations = _extract_relations(raw)
    
    # Erstelle den Normalized Graph
    graph = NormalizedGraph(
        entities=entities,
        relations=relations,
        metadata={
            "version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": "siemens_to_weslr_normalizer_v1"
        },
        source_file=raw.get("metadata", {}).get("source_file", ""),
        original_entities_count=len(raw.get("devices", []) + raw.get("plcs", []) + 
                                       raw.get("cpus", []) + raw.get("tags", []) + 
                                       raw.get("alarms", [])),
        original_relations_count=len(raw.get("topology", []))
    )
    
    return graph


def to_dict(graph: NormalizedGraph) -> dict:
    """
    Wandelt einen NormalizedGraph in ein Dictionary um (für JSON-Serialization).
    
    Diese Funktion stellt sicher, dass die Ausgabe dem Schema entspricht:
    schemas/normalized_graph.schema.json
    """
    return {
        "entities": [
            {
                "id": e.id,
                "type": e.type,
                "attributes": e.attributes,
                "confidence": e.confidence,
                "evidence": e.evidence,
                "source_file": e.source_file,
                "source_id": e.source_id
            }
            for e in graph.entities
        ],
        "relations": [
            {
                "id": r.id,
                "source_id": r.source_id,
                "target_id": r.target_id,
                "type": r.type,
                "strength": r.strength,
                "provenance": r.provenance
            }
            for r in graph.relations
        ],
        "metadata": graph.metadata
    }