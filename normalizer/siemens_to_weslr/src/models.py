"""
Python-Datenmodelle für den Normalizer (MVP).

Diese Modelle entsprechen dem Weslr Normalized Graph Schema
(schemas/normalized_graph.schema.json) und dienen als zentrale
Datenstruktur für die Transformation von TIA Export nach Weslr-Format.

Keine externen Abhängigkeiten – reine Standard-Library (dataclasses).
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class NormalizedEntity:
    """
    Repräsentiert eine Weslr-Entity nach dem Normalized Graph Schema.
    
    Ein Entity ist ein Engineering-Objekt aus dem TIA-Export:
    - PLCs
    - Devices
    - CPUs
    - Tags
    - Alarme
    - etc.
    """
    id: str  # eindeutige ID (4-16 chars, lowercase alphanumeric)
    name: str  # Bezeichner des Objekts
    type: str  # entity type: plc, device, tag, alarm, relationship, etc.
    attributes: dict[str, Any] = field(default_factory=dict)
    # zusätzliche Attribute spezifisch für den Entity-Typ
    
    confidence: float = 1.0  # 0.0 bis 1.0 – Vertrauenswürdigkeit der Daten
    evidence: list[str] = field(default_factory=list)
    # Quellen für diese Entity (z. B. "plc_read", "symbol_table")
    
    created_at: Optional[str] = None  # ISO 8601 timestamp (wird bei Import gesetzt)
    last_seen: Optional[str] = None   # ISO 8601 timestamp
    
    # interne Metadaten (nicht im Schema, aber für Normalizer nützlich)
    source_file: Optional[str] = None  # Ursprungsdatei (Raw Export)
    source_id: Optional[str] = None    # ID im Raw Export (Collector-ID)


@dataclass
class NormalizedRelation:
    """
    Repräsentiert eine Beziehung zwischen zwei Entities im Normalized Graph.
    
    Relationen verknüpfen Entities (z. B. PLC enthält Device, Tag löst Alarm aus).
    """
    id: str  # eindeutige ID der Relation
    source_id: str  # ID des Quell-Entities
    target_id: str  # ID des Ziel-Entities
    type: str  # relation type: contains, connects, monitors, triggers, depends_on
    
    strength: float = 1.0  # 0.0 bis 1.0 – Stärke der Beziehung
    provenance: Optional[str] = None
    # Quelle dieser Relation (z. B. "plc_io_configuration", "symbol_mapping")
    
    created_at: Optional[str] = None  # ISO 8601 timestamp
    updated_at: Optional[str] = None  # ISO 8601 timestamp


@dataclass
class NormalizedGraph:
    """
    Der gesamte Normalized Graph – das Resultat der Transformation.
    
    Enthält alle Entities, Relationen und Metadaten für den Weslr-Import.
    """
    entities: list[NormalizedEntity] = field(default_factory=list)
    relations: list[NormalizedRelation] = field(default_factory=list)
    
    metadata: dict[str, Any] = field(default_factory=lambda: {
        "version": "1.0.0",
        "generated_at": None,  # ISO 8601 timestamp (wird gesetzt beim Export)
        "source": None  # Quelle (z. B. "normalized_graph_export")
    })
    
    # interne Metadaten (nicht im Schema, aber für Normalizer nützlich)
    source_file: Optional[str] = None  # Ursprungsdatei (Raw Export)
    original_entities_count: int = 0   # Anzahl Entities im Raw Export
    original_relations_count: int = 0  # Anzahl Relations im Raw Export