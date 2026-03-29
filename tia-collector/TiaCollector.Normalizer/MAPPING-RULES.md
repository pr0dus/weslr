# Mapping Rules — Siemens → Weslr Normalizer v1.0

## Overview

1:1 Mapping von TIA-Collector-Objekten zu Weslr Entities und Relationships.

---

## Entity-Mapping

| TIA-Objekt | Weslr Entity ID | Weslr Entity Type | Entity Name |
|------------|-----------------|-------------------|-------------|
| `TiaProject` | `project-{project.Id}` | `tia-project` | `project.Name` |
| `TiaPlc` | `plc-{plc.Id}` | `plc` | `plc.Name` |
| `TiaModule` | `module-{module.Id}` | `hardware-module` | `module.Name` |
| `TiaParameter` | `parameter-{parameter.Id}` | `configuration-parameter` | `parameter.Name` |
| `TiaTag` | `tag-{tag.Id}` | `process-tag` | `tag.Name` |
| `TiaBlock` | `block-{block.Id}` | `tia-block` | `block.Name` |

### Entity-Metadaten

Jedes Weslr-Entity erhält folgende Metadaten:

```csharp
{
  "source_system": "siemens-tia-v20",
  "created_by": "normalizer-1.0.0",
  "last_imported": "ISO-8601 Timestamp",
  // Objekt-spezifische Metadaten (siehe unten)
}
```

#### TiaProject → tia-project

| TIA-Feld | Weslr-Metadata-Key | Kommentar |
|----------|-------------------|-----------|
| `project.Name` | `name` | Primary name |
| `project.Version` | `version` | TIA Portal version |
| `project.Owner` | `owner` | Project owner |
| `project.Comment` | `comment` | Project comment |
| `project.TiaPath` | `tia_path` | Original file path |

#### TiaPlc → plc

| TIA-Feld | Weslr-Metadata-Key | Kommentar |
|----------|-------------------|-----------|
| `plc.Name` | `name` | Primary name |
| `plc.Type` | `hardware_type` | PLC hardware type |
| `plc.Version` | `firmware_version` | PLC firmware version |
| `plc.Rack` | `rack` | Rack number (optional) |
| `plc.Slot` | `slot` | Slot number (optional) |

#### TiaModule → hardware-module

| TIA-Feld | Weslr-Metadata-Key | Kommentar |
|----------|-------------------|-----------|
| `module.Name` | `name` | Primary name |
| `module.Type` | `hardware_type` | Module hardware type |
| `module.Slot` | `slot` | Module slot number |
| `module.SerialNumber` | `serial_number` | Optional |
| `module.PartNumber` | `part_number` | Optional |

#### TiaParameter → configuration-parameter

| TIA-Feld | Weslr-Metadata-Key | Kommentar |
|----------|-------------------|-----------|
| `parameter.Name` | `name` | Primary name |
| `parameter.DataType` | `data_type` | Wstring, Int, Bool, etc. |
| `parameter.Value` | `value` | Configuration value (string) |
| `parameter.IsReadOnly` | `is_read_only` | bool |
| `parameter.IsProtected` | `is_protected` | bool |

#### TiaTag → process-tag

| TIA-Feld | Weslr-Metadata-Key | Kommentar |
|----------|-------------------|-----------|
| `tag.Name` | `name` | Primary name |
| `tag.DataType` | `data_type` | Wstring, Int, Bool, etc. |
| `tag.Address` | `address` | Memory address (e.g. "DB1.DBX0.0") |
| `tag.IsRetain` | `is_retain` | bool |
| `tag.IsPermanent` | `is_permanent` | bool |

#### TiaBlock → tia-block

| TIA-Feld | Weslr-Metadata-Key | Kommentar |
|----------|-------------------|-----------|
| `block.Name` | `name` | Primary name |
| `block.Type` | `block_type` | OB, FB, FC, SFB, SFC |
| `block.Number` | `block_number` | Block number (int) |
| `block.NetworkCount` | `network_count` | Optional |
| `block.LineCount` | `line_count` | Optional |

---

## Relationship-Mapping

| Source Entity | Target Entity | Relationship-Type | Comment |
|---------------|---------------|-------------------|---------|
| `project-proj-id` | `plc-plc-id` | `contains-plc` | Project contains PLC |
| `project-proj-id` | `module-mod-id` | `contains-module` | Project contains Module (global) |
| `project-proj-id` | `parameter-param-id` | `contains-parameter` | Project contains Parameter (global) |
| `project-proj-id` | `tag-tag-id` | `contains-tag` | Project contains Tag (global) |
| `project-proj-id` | `block-block-id` | `contains-block` | Project contains Block (global) |
| `plc-plc-id` | `module-mod-id` | `has-module` | PLC has Module |
| `plc-plc-id` | `parameter-param-id` | `has-parameter` | PLC has Parameter |
| `plc-plc-id` | `tag-tag-id` | `has-tag` | PLC has Tag |
| `plc-plc-id` | `block-block-id` | `has-block` | PLC has Block |

### Relationship-Metadaten

```csharp
{
  "source_id": "project-proj-123",
  "target_id": "plc-plc-456",
  "type": "contains-plc",
  "strength": 1.0,
  "provenance": "siemens-tia-v20-normalizer-1.0.0",
  "created_at": "ISO-8601 Timestamp"
}
```

---

## Aliasing-Regeln

Weslr-Entities erhalten automatisch Aliase:

| Entity-Type | Aliase |
|-------------|--------|
| `tia-project` | `[original Name]`, `[project.Id]` |
| `plc` | `[plc.Name]`, `[plc.Id]` |
| `hardware-module` | `[module.Name]`, `[module.Id]` |
| `configuration-parameter` | `[parameter.Name]`, `[parameter.Id]` |
| `process-tag` | `[tag.Name]`, `[tag.Id]` |
| `tia-block` | `[block.Name]`, `[block.Id]` |

---

## Ausgeschlossene Felder (v1)

Folgende TIA-Felder sind **nicht** Teil des Mappings (künftige Erweiterung):

| TIA-Feld | Grund |
|----------|-------|
| `project.Devices` | Komplex → spätere Version |
| `plc.Blocks` | Block-Inhalte → spätere Version |
| `parameter.Value` (nicht serialisierbar) | Type-unsicher → spätere Version |

---

## Beziehungsgewichtung (Strength)

| Relationship-Type | Strength | Begründung |
|-------------------|----------|------------|
| `contains-plc` | `1.0` | Exklusivität |
| `contains-module` | `1.0` | Exklusivität |
| `has-module` | `1.0` | Exklusivität |
| `has-parameter` | `1.0` | Exklusivität |
| `has-tag` | `1.0` | Exklusivität |
| `has-block` | `1.0` | Exklusivität |

---

## Fehlerbehandlung (Mapping-Spezifik)

| Fehler | Scenario | Handhabung |
|--------|----------|------------|
| `NullReferenceException` | Missing TIA-Feld | Log `WARN`, Entity/Relationship überspringen |
| `InvalidCastException` | Wert-Typ inkongruent | Log `ERROR`, Exception werfen |
| `DuplicateIdException` | Doppelte Entity-ID | Log `WARN`, Entity mit Suffix `_v2` neu erzeugen |
| `MissingRequiredFieldException` | Pflichtfeld fehlt | Log `ERROR`, Exception werfen |

### Logging-Format

```
[WARN] Normalizer: Missing PLC name for ID 'plc-456' | Input: project-123
[ERROR] Normalizer: Invalid cast for parameter value | Input: project-123
```

---

## Konfiguration (optional, künftig)

```json
{
  "mapping": {
    "enableAliases": true,
    "includeMetadata": true,
    "relationshipStrength": {
      "contains-plc": 1.0,
      "has-module": 1.0
    },
    "excludedFields": []
  }
}
```

---

**Status**: Mapping-Spezifik v1 — Ready for Implementation  
**Version**: 1.0  
**Date**: 2026-03-29
