# Siemens → Weslr Normalizer v1.0 — Implementation Status

## Overview

Konvertiert TIA-Collector-Rohdaten in das Weslr-Entity/Relationship-Modell.

---

## Status

| Komponente | Status | Hinweis |
|------------|--------|---------|
| README.md | ✅ | Overview |
| MAPPING-RULES.md | ✅ | 1:1 Mapping-Spezifikation |
| INormalizer.cs | ✅ | Interface |
| TiaSiemensNormalizer.cs | ✅ | Skeleton-Implementierung |
| ProjectEntity.cs | ✅ | Entity-Konverter |
| PlcEntity.cs | ✅ | Entity-Konverter |
| ModuleEntity.cs | ✅ | Entity-Konverter |
| ParameterEntity.cs | ✅ | Entity-Konverter |
| TagEntity.cs | ✅ | Entity-Konverter |
| BlockEntity.cs | ✅ | Entity-Konverter |
| ProjectPlcRelationship.cs | ✅ | Relationship-Konverter |
| CustomExceptions.cs | ✅ | Fehlerklassen |
| sample-input.json | ✅ | Beispiels-Eingabe |
| sample-output.json | ✅ | Beispiels-Ausgabe |
| TiaCollector.Normalizer.csproj | ✅ | .NET Projekt |

---

## Dateiübersicht

```
tia-collector/TiaCollector.Normalizer/
├── README.md
├── MAPPING-RULES.md
├── TiaCollector.Normalizer.csproj
├── INormalizer.cs
├── TiaSiemensNormalizer.cs
├── Entities/
│   ├── ProjectEntity.cs
│   ├── PlcEntity.cs
│   ├── ModuleEntity.cs
│   ├── ParameterEntity.cs
│   ├── TagEntity.cs
│   └── BlockEntity.cs
├── Relationships/
│   ├── ProjectPlcRelationship.cs
│   └── (erweiterbar)
├── ErrorHandling/
│   └── CustomExceptions.cs
└── samples/
    ├── sample-input.json
    └── sample-output.json
```

---

## Mapping-Regeln (Kern)

| TIA-Objekt | Weslr-Entity-Type | ID-Präfix |
|------------|-------------------|-----------|
| `TiaProject` | `tia-project` | `project-` |
| `TiaPlc` | `plc` | `plc-` |
| `TiaModule` | `hardware-module` | `module-` |
| `TiaParameter` | `configuration-parameter` | `parameter-` |
| `TiaTag` | `process-tag` | `tag-` |
| `TiaBlock` | `tia-block` | `block-` |

### Beziehungstypen

- `contains-plc`
- `contains-module`
- `contains-parameter`
- `contains-tag`
- `contains-block`
- `has-module`

---

## Fehlerbehandlung

| Exception | Scenario |
|-----------|----------|
| `MappingException` | Daten konnten nicht zugeordnet werden |
| `NormalizerException` | Systemfehler (z.B. IO) |
| `ValidationException` | Input-JSON ungültig |

---

## Build & Test (künftig)

```bash
# Build
dotnet build TiaCollector.Normalizer/TiaCollector.Normalizer.csproj

# Tests (künftig)
dotnet test
```

---

## Nächste Schritte

| Phase | Status | Description |
|-------|--------|-------------|
| Skeleton | ✅ | Dieses Dokument |
| Integration mit TIA-Collector | 🚧 | Import-Fluss finalisieren |
| Weslr-Export | 🚧 | Export in Weslr-Format |
| Tests | 🚧 | Unit-Tests |
| Documentation | 🚧 | API Docs |

---

**Status**: Skeleton — Ready for Integration  
**Version**: 1.0  
**Date**: 2026-03-29  
**Dependencies**: TIA-Collector Export, Weslr Entity Model  
**Platform**: Windows (TIA-Collector Requirement)
