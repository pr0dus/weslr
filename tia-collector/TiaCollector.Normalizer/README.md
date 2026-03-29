# Siemens → Weslr Normalizer v1.0

Konvertiert TIA-Collector-Rohdaten in das Weslr-Entity/Relationship-Modell.

## Status: Skeleton 1.0 — 2026-03-29

## Overview

- **Input**: TIA-Collector JSON (neutral export)
- **Output**: Weslr Entity/Relationship Graph (JSON)
- **Rules**: 1:1 Mapping, keine komplexe Analyse
- **Standalone**: Kein Hauptrepo-Einbau, separates Plugin-Repo

## Mapping-Regeln (v1)

| TIA-Objekt | Weslr-Entity | Entity-Type | ID-Mapping | Name-Mapping |
|------------|--------------|-------------|------------|--------------|
| `TiaProject` | `project-{id}` | `tia-project` | `project.Id` | `project.Name` |
| `TiaPlc` | `plc-{id}` | `plc` | `plc.Id` | `plc.Name` |
| `TiaModule` | `module-{id}` | `hardware-module` | `module.Id` | `module.Name` |
| `TiaParameter` | `parameter-{id}` | `configuration-parameter` | `parameter.Id` | `parameter.Name` |
| `TiaTag` | `tag-{id}` | `process-tag` | `tag.Id` | `tag.Name` |
| `TiaBlock` | `block-{id}` | `tia-block` | `block.Id` | `block.Name` |

### Beziehungstypen

| Source | Target | Relationship-Type |
|--------|--------|-------------------|
| Project | PLC | `contains-plc` |
| Project | Module | `contains-module` |
| PLC | Module | `has-module` |
| PLC | Parameter | `has-parameter` |
| PLC | Tag | `has-tag` |
| PLC | Block | `has-block` |

### Entity-Eigenschaften

Jedes Weslr-Entity erhält:
- `entity_type`: Wie oben (z.B. `tia-project`, `plc`)
- `source_system`: `siemens-tia-v20`
- `created_by`: `collector-1.0.0`
- `last_imported`: `ISO-8601 Timestamp`

---

## Beispiel Input/Output

### Input (TIA-Collector JSON)

```json
{
  "Id": "proj-123",
  "Name": "MyTIAProject",
  "Version": "V20",
  "CreatedAt": "2026-03-29T10:00:00Z",
  "Owner": "John Doe",
  "Plcs": [
    {
      "Id": "plc-456",
      "Name": "PLC_Station1",
      "Type": "S7-1500",
      "Version": "V4.2"
    }
  ],
  "Modules": [
    {
      "Id": "mod-789",
      "Name": "IM 0",
      "Type": "6ES7 314-1AG13-0AB0",
      "Slot": 0
    }
  ]
}
```

### Output (Weslr Entity Graph JSON)

```json
{
  "entities": [
    {
      "id": "project-proj-123",
      "name": "MyTIAProject",
      "type": "tia-project",
      "aliases": ["MyTIAProject", "proj-123"],
      "metadata": {
        "source_system": "siemens-tia-v20",
        "created_by": "normalizer-1.0.0",
        "last_imported": "2026-03-29T10:44:00Z",
        "version": "V20",
        "owner": "John Doe"
      }
    },
    {
      "id": "plc-plc-456",
      "name": "PLC_Station1",
      "type": "plc",
      "aliases": ["PLC_Station1", "plc-456"],
      "metadata": {
        "source_system": "siemens-tia-v20",
        "created_by": "normalizer-1.0.0",
        "last_imported": "2026-03-29T10:44:00Z",
        "hardware_type": "S7-1500",
        "firmware_version": "V4.2"
      }
    },
    {
      "id": "module-mod-789",
      "name": "IM 0",
      "type": "hardware-module",
      "aliases": ["IM 0", "mod-789"],
      "metadata": {
        "source_system": "siemens-tia-v20",
        "created_by": "normalizer-1.0.0",
        "last_imported": "2026-03-29T10:44:00Z",
        "hardware_type": "6ES7 314-1AG13-0AB0",
        "slot": 0
      }
    }
  ],
  "relationships": [
    {
      "source_id": "project-proj-123",
      "target_id": "plc-plc-456",
      "type": "contains-plc",
      "strength": 1.0
    },
    {
      "source_id": "project-proj-123",
      "target_id": "module-mod-789",
      "type": "contains-module",
      "strength": 1.0
    }
  ]
}
```

---

## Dateiübersicht (Skeleton)

```
tia-collector/TiaCollector.Normalizer/
├── README.md                      # Dieses Dokument
├── MappingRules.md                # Detaillierte Mapping-Regeln
├── TiaCollector.Normalizer.csproj
├── INormalizer.cs                 # Interface
├── TiaSiemensNormalizer.cs        # Implementierung
├── Data/
│   ├── TiaProjectEntity.cs
│   ├── PlcEntity.cs
│   ├── ModuleEntity.cs
│   ├── ParameterEntity.cs
│   ├── TagEntity.cs
│   └── BlockEntity.cs
├── Relationships/
│   ├── ProjectPlcRelationship.cs
│   ├── ProjectModuleRelationship.cs
│   └── PlcModuleRelationship.cs
├── ErrorHandling/
│   ├── MappingException.cs
│   └── NormalizerException.cs
└── samples/
    ├── sample-input.json
    └── sample-output.json
```

---

## Fehlerbehandlung

| Fehlerklasse | Scenario | Handhabung |
|--------------|----------|------------|
| `MappingException` | Daten konnten nicht zugeordnet werden | Log + skip (warn) |
| `NormalizerException` | Systemfehler (z.B. IO) | Log + throw |
| `ValidationException` | Input-JSON ungültig | Log + abort |

### Logging (NLog)

- **Category**: `Normalizer`
- **Level**: `Warn`, `Error`
- **Format**: `[{level}] Normalizer: {message} | Input: {inputId}`

---

## Nächste Schritte (Future)

| Phase | Status | Description |
|-------|--------|-------------|
| Skeleton | ✅ | Dieses Dokument |
| Entity-Mapping | 🚧 | Implementierung der Konverter |
| Relationship-Mapping | 🚧 | Verbindungen erzeugen |
| Weslr-Import | 🚧 | Export in Weslr-Format |
| Tests | 🚧 | Unit-Tests |

---

**Status**: Skeleton — Ready for Implementation  
**Dependencies**: TIA-Collector Export, Weslr Entity Model  
**Platform**: Windows (TIA-Collector Requirement)
