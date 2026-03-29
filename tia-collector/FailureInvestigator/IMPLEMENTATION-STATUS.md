# Failure Investigator v1.0 — Implementation Status

## Overview

MVP-Failure-Investigation für Siemens TIA-Portal-Systeme.

---

## Status

| Komponente | Status | Hinweis |
|------------|--------|---------|
| README.md | ✅ | Overview |
| IFailureInvestigator.cs | ✅ | Interface + Models |
| IAnalyzer.cs | ✅ | Analyzer-Interfaces |
| ISearchEngine.cs | ✅ | Search-Interface + FileSystemSearch |
| IOutputFormatter.cs | ✅ | Output-Interface + JsonOutputFormatter |
| Configuration.cs | ✅ | Configuration-Management |
| Program.cs | ✅ | CLI Entry Point (skeleton) |
| sample-config.json | ✅ | Beispiel-Konfiguration |
| sample-request.json | ✅ | Beispiel-Anfrage |
| sample-response.json | ✅ | Beispiel-Antwort |

---

## Analyseablauf (Kern)

```
[Input] → Validate → Parse → NormalizedInput
         ↓
[NormalizedInput] → SearchPaths → QueryResults
         ↓
[QueryResults] → Analyze → AnalysisResults
         ↓
[AnalysisResults] → Format → Output
```

### Suchpfade

| Suchpfad | Beschreibung |
|----------|--------------|
| `projects/{lineName}/stations/{stationName}/plcs/` | PLC-spezifisch |
| `projects/{lineName}/stations/{stationName}/tags/` | Tag-spezifisch |
| `projects/{lineName}/alarms/` | Alarm-spezifisch |
| `shared/hardware/` | Hardware-Katalog |
| `shared/alarms/` | Alarm-Katalog |

---

## Analysefunktionen (Skeleton)

| Funktion | Beschreibung | Status |
|----------|--------------|--------|
| `FindRelevantPlcs()` | Sucht PLCs basierend auf `plcName`, `stationName` | 🚧 |
| `FindCpuInfo()` | CPU-Modell, Firmware, Status | 🚧 |
| `FindDevices()` | Module basierend auf PLC-Name | 🚧 |
| `FindRelatedTags()` | Tags basierend auf `tagName`, `errorcode` | 🚧 |
| `FindRelatedBlocks()` | Bausteine basierend auf `blockName` | 🚧 |
| `FindRelatedAlarms()` | Alarme basierend auf `alarmText` | 🚧 |
| `FindSimilarFailurePatterns()` | Ähnliche Fehler basierend auf Alarmtext | 🚧 |
| `GetAffectedSection()` | Hierarchie: Line → Station → Subsystem | 🚧 |
| `GenerateTechnicalSummary()` | Technische Kurzbewertung | 🚧 |

---

## API-Vertrag (Interface)

```csharp
public interface IFailureInvestigator
{
    Task<InvestigationResult> InvestigateAsync(InvestigationRequest request, CancellationToken ct);
}
```

---

## Eingaben & Ausgaben (Kern)

### Eingaben (InvestigationRequest)

| Feld | Typ | Pflicht |
|------|-----|---------|
| `AlarmText` | `string` | ✅ |
| `ErrorCode` | `string` | ❌ |
| `TagName` | `string` | ❌ |
| `PlcName` | `string` | ❌ |
| `StationName` | `string` | ❌ |
| `LineName` | `string` | ❌ |
| `BlockName` | `string` | ❌ |

### Ausgaben (InvestigationResult)

| Feld | Typ |
|------|-----|
| `RelevantPlcs` | `List<TiaPlc>` |
| `CpuInfo` | `CpuInfo` |
| `Devices` | `List<TiaModule>` |
| `RelatedTags` | `List<TiaTag>` |
| `RelatedBlocks` | `List<TiaBlock>` |
| `RelatedAlarms` | `List<Alarm>` |
| `SimilarFailurePatterns` | `List<FailurePattern>` |
| `AffectedSection` | `string` |
| `TechnicalSummary` | `string` |

---

## Build & Run (künftig)

```bash
# Build
dotnet build FailureInvestigator.sln

# Run
dotnet run --project FailureInvestigator.Cli -- --alarm "Druck zu niedrig" --station "Station_3" --line "Production_Line_1"
```

---

## Nächste Schritte

| Phase | Status | Description |
|-------|--------|-------------|
| Skeleton | ✅ | Dieses Dokument |
| Search Engine Implementation | 🚧 | Directory Traversal |
| Analyzer Implementation | 🚧 | Rule-based Analysis |
| Output Formatter | 🚧 | JSON Formatting |
| CLI Tests | 🚧 | Unit-Tests |
| Documentation | 🚧 | API Docs |

---

**Status**: Skeleton — Ready for Implementation  
**Version**: 1.0  
**Date**: 2026-03-29  
**Dependencies**: TIA-Collector Export, Weslr Entity Model  
**Platform**: Windows (TIA-Collector Requirement)
