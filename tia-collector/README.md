# TIA Collector v1.0

Read-only TIA Portal V20 Project Exporter (Windows, .NET Framework 4.8)

## Status: Skeleton 1.0 — 2026-03-29

## Overview

- **Read-only**: Kein Schreiben in TIA
- **Neutral JSON**: Platform-unabhängiges Exportformat
- **Windows-only**: TIA Portal Openness API requires Windows
- **Standalone**: Keine OpenClaw-Abhängigkeit

## Architecture

```
TiaCollector.Solution/
├── TiaCollector.Core/     # Interfaces + Data Models
├── TiaCollector.TiaApi/   # TIA Openness API Wrapper
├── TiaCollector.Export/   # Export Pipeline (JSON)
├── TiaCollector.Cli/      # CLI Entry Point
└── TiaCollector.Config/   # Configuration Management
```

## Core Interfaces

| Interface | Responsibility |
|-----------|----------------|
| `IImporter` | TIA import (via Openness API) |
| `ICollector` | Orchestration (import → validate → export) |
| `IExporter` | JSON export (neutral format) |
| `IValidator` | Data integrity (read-only checks) |

## Data Models

- `TiaProject`: Project ID, Name, Version, Timestamps
- `TiaPlc`: PLC ID, Name, Type, Version
- `TiaModule`: Module ID, Name, Type, Slot
- `TiaParameter`: Parameter ID, Name, DataType, Value

## Build & Run

### Requirements

- Windows 10/11 or Windows Server 2016+
- .NET Framework 4.8
- TIA Portal V20+ (with Openness API)
- Visual Studio 2022 or `dotnet CLI`

### Build

```bash
# .NET CLI
dotnet build TiaCollector.sln
```

### Run

```bash
# CLI
dotnet run --project TiaCollector.Cli -- --input "C:\TIA Projects\MyProject.ap20" --output "./exports"
```

### CLI Options

```
--input      Path to TIA project file (.ap20, .ap18) [REQUIRED]
--output     Output file path or directory [default: ./exports]
--config     Path to configuration file [default: ./collector-config.json]
--validate   Only validate project (no export)
```

## Export Flow

```
TIA Project File → TIA Openness API → TiaProject → Validate → JSON
```

## Logging

- **Framework**: NLog
- **Category**: `Importer`, `Exporter`, `Validator`, `CLI`
- **Level**: `Info`, `Warn`, `Error`

## Configuration (`collector-config.json`)

```json
{
  "collector": { "timeoutSeconds": 300, "readOnly": true, "validateBeforeExport": true },
  "export": { "format": "neutral-json", "indent": true, "includeMetadata": true },
  "logging": { "level": "Info", "filePath": "./logs/collector.log" }
}
```

## Future Scope

| Phase | Status | Description |
|-------|--------|-------------|
| Skeleton | ✅ | This file |
| TIA API Integration | 🚧 | COM wrapper for TIA Openness API |
| Export Tests | 🚧 | JSON export validation |
| CLI Tests | 🚧 | Unit tests for CLI |
| Documentation | 🚧 | API docs, README |

## Known Limitations

- **Platform**: Windows-only (TIA Portal Openness API requirement)
- **TIA Version**: Requires TIA Portal V20+ (Openness API v18+)
- **Export**: Only project metadata currently (PLCs, modules, parameters pending)

## License

MIT — See `LICENSE` file.

---

**Status**: Skeleton — Ready for TIA API Integration  
**Platform**: Windows only (TIA Portal)  
**Dependencies**: TIA Portal Openness API v20+, .NET Framework 4.8
