# siemens_to_weslr – Normalizer (MVP)

Dieses Modul transformiert Rohexporte aus Siemens TIA Portal V20 in das
Weslr-konforme Normalized Graph Format.

## Zweck

Das **siemens_to_weslr**-Modul ist Teil des TIA Portal V20 Plugins für Weslr.
Es dient als Normalizer-Engine und transformiert Rohdaten aus TIA Portal V20
in das Weslr-Entity-Modell.

## Eingabe

- **Format**: JSON (Raw Export nach `tia_export.schema.json`)
- **Inhalt**: PLCs, CPUs, Devices, Tags, Alarme, Topologie
- **Quelle**: TIA-Collector (Windows, In-Process)

## Ausgabe

- **Format**: Normalized Graph (nach `normalized_graph.schema.json`)
- **Inhalt**: Entities, Relations, Metadaten
- **Ziel**: Import in Weslr (Main-Repo)

## Was die erste Implementierung kann

- **Entity-Extraktion**:
  - Project
  - Device
  - PLC
  - CPU
  - Module (SM, PS, IM)
  - Tag-Table
  - Tag
  - Program Block (OB, FC, FB, DB)
  - Alarm

- **Relation-Extraktion**:
  - Topology (Netzwerkverbindungen)

- **ID-Normalisierung**:
  - Wandelt Collector-IDs in Weslr-konforme IDs (4-16 chars, lowercase alphanumeric)

- **Metadata-Tracking**:
  - source_file (Ursprungsdatei)
  - source_id (Collector-ID)
  - confidence (Vertrauenswürdigkeit)

## Was sie bewusst noch nicht kann

- Keine SPS-Kommunikation (nur offline-Export)
- Keine Online-Daten (keine Laufzeit-Informationen)
- Keine Safety-Transformierung (nur lesender Zugriff)
- Keine automatische Fehlerkorrektur
- Keine Komprimierung oder Optimierung
- Keine Dateizugriffe (reine In-Memory-Transformation)
- Keine CLI (reine Transformationslogik)

## Beispiel

```python
from siemens_to_weslr.src.normalize import normalize_tia_export, to_dict
from siemens_to_weslr.src.models import NormalizedGraph

# Raw Export laden (simuliert)
raw_export = {
    "project": {"id": "proj-001", "name": "LineControl"},
    "devices": [{"id": "dev-001", "name": "Control-Panel-A", "type": "plc_device"}],
    "plcs": [{"id": "plc-001", "name": "CPU-1511-1-PN", "rack": 0, "slot": 1}],
    "tags": [{"id": "tag-001", "name": "Global-Variables.MachineSpeed", "data_type": "REAL"}],
    "topology": [{"id": "topo-001", "source_id": "dev-001", "target_id": "plc-001", "type": "profinet"}]
}

# Transformieren
graph: NormalizedGraph = normalize_tia_export(raw_export)

# In Dict umwandeln (für JSON-Serialization)
output = to_dict(graph)
```

## Struktur

```
siemens_to_weslr/
├── src/
│   ├── models.py    # Datenmodelle (NormalizedEntity, NormalizedRelation, NormalizedGraph)
│   └── normalize.py # Transformationslogik (normalize_tia_export, to_dict)
└── README.md        # Diese Datei
```

## Requirements

- Python 3.11+
- Keine externen Abhängigkeiten (Standard-Library only)
- Keine externen Bibliotheken (nur dataclasses)

---

*Letzte Aktualisierung: 2026-03-29*