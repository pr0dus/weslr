# TIA Collector Skeleton

## Overview

Ein Windows-basierter Read-Only Collector für TIA Portal V20, der Projekte ausliest und in neutrales JSON exportiert. Keine TIA-Schreiboperationen, keine OpenClaw-Abhängigkeit.

---

## Architektur

```
TiaCollector.Solution/
├── TiaCollector.Core/           # Kernlogik, Interfaces
├── TiaCollector.TiaApi/         # TIA Portal Openness API Wrapper
├── TiaCollector.Export/         # JSON-Export-Pipeline
├── TiaCollector.Cli/            # CLI-Entry-Point
└── TiaCollector.Config/         # Konfigurationsmanagement
```

---

## Verantwortlichkeiten (Kernprinzipien)

| Modul | Zuständigkeiten | Nichts
|-------|-----------------|-------
| `IImporter` | TIA-Daten importieren (via Openness API) | Keine Validation, kein Export
| `ICollector` | Koordination, Import-Orchestrierung | Keine TIA-Logik, kein Export
| `IExporter` | JSON-Serialization, Format-Neutralität | Keine TIA-Import-Logik
| `IValidator` | Datenintegrität prüfen | Keine Schreiboperationen
| `Collector` | Orchestrierung (Import → Validate → Export) | Keine Spezialisierung

---

## Klassenübersicht (C#)

### Interfaces (TiaCollector.Core)

```csharp
// TiaCollector.Core/IImporter.cs
public interface IImporter
{
    Task<TiaProject> ImportProjectAsync(string tiaPath, CancellationToken ct);
    Task<IEnumerable<TiaPlc>> ImportPlcsAsync(string tiaPath, CancellationToken ct);
    Task<IEnumerable<TiaModule>> ImportModulesAsync(string tiaPlcId, CancellationToken ct);
}

// TiaCollector.Core/ICollector.cs
public interface ICollector
{
    Task<TiaProject> CollectAsync(string tiaPath, CancellationToken ct);
}

// TiaCollector.Core/IExporter.cs
public interface IExporter
{
    Task<string> ExportToJsonAsync(TiaProject project, CancellationToken ct);
    Task ExportToFileAsync(TiaProject project, string outputPath, CancellationToken ct);
}

// TiaCollector.Core/IValidator.cs
public interface IValidator
{
    ValidationResult Validate(TiaProject project);
    Task<bool> ValidateAsync(TiaProject project, CancellationToken ct);
}

// TiaCollector.Core/IDataModel.cs (TIA-Datenmodelle)
public record TiaProject(string Id, string Name, string Version, DateTime CreatedAt);
public record TiaPlc(string Id, string Name, string Type, string Version);
public record TiaModule(string Id, string Name, string Type, int Slot);
public record TiaParameter(string Id, string Name, string DataType, object Value);
```

---

## Dateiübersicht

```
tia-collector/
├── TiaCollector.sln                  # Visual Studio Solution
├── README.md                         # Kurzbeschreibung
├── TIA-COLLECTOR-SKELETON.md         # Dieses Dokument
├── TiaCollector.Core/
│   ├── IImporter.cs
│   ├── ICollector.cs
│   ├── IExporter.cs
│   ├── IValidator.cs
│   ├── IDataModel.cs                # Data Models (record structs)
│   ├── ValidationResult.cs
│   └── TiaCollector.Core.csproj
├── TiaCollector.TiaApi/
│   ├── TiaOpennessClient.cs         # TIA Portal Openness API Wrapper
│   ├── TiaApiImporter.cs            # Implementierung von IImporter
│   └── TiaCollector.TiaApi.csproj
├── TiaCollector.Export/
│   ├── JsonExporter.cs              # Implementierung von IExporter
│   ├── ExportConfig.cs              # Export-Konfiguration
│   └── TiaCollector.Export.csproj
├── TiaCollector.Cli/
│   ├── Program.cs                   # CLI Entry Point
│   ├── CliOptions.cs                # CLI Argument Parsing
│   └── TiaCollector.Cli.csproj
├── TiaCollector.Config/
│   ├── CollectorConfig.cs           # Gesamtkonfiguration
│   └── TiaCollector.Config.csproj
├── samples/
│   └── sample-config.json           # Beispiel-Konfiguration
└── build/
    ├── build.sh
    └── build.ps1
```

---

## Exportfluss (Data Flow)

```
TIA Project File (.ap18/.ap20)
        ↓
[ TiaOpennessClient ]  // TIA Portal Openness API (COM/.NET Wrapper)
        ↓
[ TiaApiImporter ] → TiaProject (Core Model)
        ↓
[ Validator ] → Validate (Read-Only Checks)
        ↓
[ JsonExporter ] → JSON String / File
```

### Export-Schritte:

1. **Import** → `TIA Project Path` → `TiaProject` (via TIA Openness API)
2. **Validation** → `TiaProject` → `ValidationResult` (integrity checks only)
3. **Export** → `TiaProject` → JSON (neutral, schema-based)

---

## Logging-Konzept

### Strategie

- **Ziel:** Strukturierte Logs, leichtgewichtig
- **Framework:** NLog oder Serilog (wahlweise, vorschlag: NLog für .NET Framework 4.8)
- **Zielplattform:** Windows (Desktop/Server), keine OpenClaw-Abhängigkeit

### Log-Kategorien

| Kategorie | Level | Inhalt |
|-----------|-------|--------|
| `Importer` | Info/Warn/Error | Import-Status, Timeouts, API-Fehler |
| `Exporter` | Info/Warn/Error | Export-Progress, Schema-Änderungen |
| `Validator` | Info/Warn/Error | Validierungs-Resultate |
| `CLI` | Info/Error | CLI-Argumente, Start/Stop |

### Beispiel (NLog.config)

```xml
<?xml version="1.0" encoding="utf-8" ?>
<nlog xmlns="http://www.nlog-project.org/schemas/NLog.xsd"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <targets>
    <target xsi:type="File" name="file" fileName="logs/collector.log"
            layout="${longdate} ${level:uppercase=true} ${logger} ${message}" />
    <target xsi:type="Console" name="console" layout="${longdate} ${level:uppercase=true} ${message}" />
  </targets>
  <rules>
    <logger name="*" minlevel="Info" writeTo="file,console" />
  </rules>
</nlog>
```

---

## Konfigurations-Schema

### `collector-config.json`

```json
{
  "collector": {
    "timeoutSeconds": 300,
    "readOnly": true,
    "validateBeforeExport": true
  },
  "export": {
    "format": "neutral-json",
    "indent": true,
    "includeMetadata": true,
    "outputDirectory": "./exports"
  },
  "logging": {
    "level": "Info",
    "filePath": "./logs/collector.log"
  }
}
```

---

## CLI-Entry-Point (Program.cs)

```csharp
// TiaCollector.Cli/Program.cs
using TiaCollector.Core;
using TiaCollector.TiaApi;
using TiaCollector.Export;
using TiaCollector.Config;

var config = ConfigurationReader.Load("collector-config.json");

var importer = new TiaApiImporter();
var validator = new Validator();
var exporter = new JsonExporter();

var collector = new Collector(importer, validator, exporter);

var options = ParseCommandLine(args);
var project = await collector.CollectAsync(options.InputPath, ct);
await exporter.ExportToFileAsync(project, options.OutputPath, ct);
```

### CLI-Argumente

```
TiaCollector.exe --input "C:\TIA Projects\MyProject.ap20" --output "./exports/myproject.json"
TiaCollector.exe --input "C:\TIA Projects\MyProject.ap20" --validate --config "custom-config.json"
```

---

## TIA Openness API Wrapper (TiaCollector.TiaApi)

### TiaOpennessClient.cs

```csharp
public class TiaOpennessClient : IDisposable
{
    private readonly Application _tiaApp;
    
    public TiaOpennessClient() => _tiaApp = new Application();
    public void Dispose() => _tiaApp?.Dispose();
    
    public Project OpenProject(string path) => _tiaApp.Projects.Open(path);
    public void CloseProject(Project project) => project.Close();
}
```

**Hinweis:** TIA Portal Openness API ist COM-basiert → Requires TIA Portal V20+ installiert.

---

## Build & Run (Windows)

### Build

```powershell
# PowerShell
dotnet build TiaCollector.sln
```

### Run

```powershell
# CLI
dotnet run --project TiaCollector.Cli -- --input "C:\TIA Projects\MyProject.ap20" --output "./exports"
```

### Requirements

- Windows 10/11 oder Windows Server 2016+
- .NET Framework 4.8
- TIA Portal V20+ (mit Openness API)
- Schreibrechte für Output-Verzeichnis

---

## Nächste Schritte (Future Scope)

| Phase | Status | Hinweis |
|-------|--------|---------|
| Skeleton | ✅ | Diese Datei |
| TIA API Integration | 🚧 | COM Wrapper für TIA Openness API |
| Export-Tests | 🚧 | JSON-Export Validierung |
| CLI-Tests | 🚧 | Unit-Tests für CLI |
| Documentation | 🚧 | API Docs, README |

---

**Status:** Skizze 1.0 — 2026-03-29  
**Platform:** Windows-only, .NET Framework 4.8  
**Dependencies:** TIA Portal Openness API v20+, .NET Framework 4.8
