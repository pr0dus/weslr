# Failure Investigator v1.0

MVP-Failure-Investigation für Siemens TIA-Portal-Systeme.

## Status: Skeleton 1.0 — 2026-03-29

## Overview

- **Input**: Alarmtext, Fehlercode, Tagname, PLC-Name, Stationsname, Linienname, Bausteinname
- **Output**: Relevante PLCs, CPU, Module, Tags, Bausteine, Alarme, ähnliche Fehler, betroffener Abschnitt, technische Kurzbewertung
- **Fokus**: MVP (keine Predictive-Maintenance, keine Runtime-Telemetrie)
- **Standalone**: Kein Hauptrepo-Einbau, separates Plugin-Repo

---

## Architektur

```
tia-collector/FailureInvestigator/
├── FailureInvestigator.Core/    # Interfaces + Data Models
├── FailureInvestigator.Analyzer/ # Analyse-Logik (Skeleton)
├── FailureInvestigator.Search/   # Suchpfade (Directory Traversal)
├── FailureInvestigator.Output/   # Output-Formatter
├── FailureInvestigator.Cli/      # CLI Entry Point
└── FailureInvestigator.Config/   # Konfiguration
```

---

## Eingaben (Input)

| Feld | Typ | Beschreibung | Pflichtfeld |
|------|-----|--------------|-------------|
| `alarmText` | `string` | Text des Alarms | ✅ |
| `errorcode` | `string` | Fehlercode (z.B. "0x80000001") | ❌ |
| `tagName` | `string` | Name des Tags | ❌ |
| `plcName` | `string` | Name der PLC | ❌ |
| `stationName` | `string` | Stationsname | ❌ |
| `lineName` | `string` | Linienname | ❌ |
| `blockName` | `string` | Bausteinname | ❌ |

### Beispiel-Input

```json
{
  "alarmText": "Druck zu niedrig auf Station 3",
  "errorcode": "0x80000001",
  "tagName": "DB10.DBD200",
  "plcName": "PLC_Station3",
  "stationName": "Station_3",
  "lineName": "Production_Line_1",
  "blockName": "OB1"
}
```

---

## Ausgaben (Output)

| Feld | Beschreibung | Format |
|------|--------------|--------|
| `relevant_plcs` | Relevante PLCs | `List<TiaPlc>` |
| `cpu_info` | CPU-Informationen | `CpuInfo` |
| `devices` | Geräte/Module | `List<TiaModule>` |
| `related_tags` | Relevante Tags | `List<TiaTag>` |
| `related_blocks` | Relevante Bausteine | `List<TiaBlock>` |
| `related_alarms` | Verwandte Alarme | `List<Alarm>` |
| `similar_failure_patterns` | Ähnliche Fehler | `List<FailurePattern>` |
| `affected_section` | Betroffener Produktionsabschnitt | `string` |
| `technical_summary` | Technische Kurzbewertung | `string` |

### Beispiel-Output

```json
{
  "relevant_plcs": [
    {
      "id": "plc-Station3",
      "name": "PLC_Station3",
      "type": "S7-1500",
      "version": "V4.2"
    }
  ],
  "cpu_info": {
    "model": "CPU 1516F-3 PN/DP",
    "firmware": "V2.6.5",
    "status": "RUN",
    "memory_size_mb": 1024
  },
  "devices": [
    {
      "id": "module-IM0",
      "name": "IM 0",
      "type": "6ES7 314-1AG13-0AB0",
      "slot": 0
    }
  ],
  "related_tags": [
    {
      "id": "tag-Pressure",
      "name": "DB10.DBD200",
      "type": "Real",
      "address": "DB10.DBX0.0"
    }
  ],
  "related_blocks": [
    {
      "id": "block-OB1",
      "name": "OB1",
      "type": "OB",
      "number": 1
    }
  ],
  "related_alarms": [
    {
      "id": "alarm-001",
      "text": "Druck zu niedrig",
      "severity": "warning",
      "timestamp": "2026-03-29T10:00:00Z"
    }
  ],
  "similar_failure_patterns": [
    {
      "id": "pattern-001",
      "text": "Druck zu niedrig",
      "frequency": 12,
      "last_occurrence": "2026-03-28T08:30:00Z"
    }
  ],
  "affected_section": "Production_Line_1 > Station_3 > Pressure_System",
  "technical_summary": "Druck-Sensor (DB10.DBD200) unterhalb Sollwert. Überprüfen Sie Ventil Y10 und Druckmesser MP1."
}
```

---

## Analyseablauf

### Phase 1: Input-Validierung & Parsing

```
[Input] → Validate → Parse → NormalizedInput
```

- Prüfung auf mindestens ein Pflichtfeld (`alarmText`)
- Normalisierung der Eingaben (lowercase, Trim)
- Identifikation von Platzhaltern (`{plcName}`, `{stationName}`)

### Phase 2: Suchpfade (Directory Traversal)

```
[NormalizedInput] → SearchPaths → QueryResults
```

#### Suchpfade:

|Suchpfad|Beschreibung|
|--------|-----------|
| `projects/{lineName}/stations/{stationName}/plcs/` | PLC-spezifisch |
| `projects/{lineName}/stations/{stationName}/tags/` | Tag-spezifisch |
| `projects/{lineName}/alarms/` | Alarm-spezifisch |
| `shared/hardware/` | Hardware-Katalog |
| `shared/alarms/` | Alarm-Katalog |

### Phase 3: Analyse

```
[QueryResults] → Analyze → AnalysisResults
```

#### Analysefunktionen (Skeleton):

| Funktion | Beschreibung |
|----------|--------------|
| `FindRelevantPlcs()` | Sucht PLCs basierend auf `plcName`, `stationName` |
| `FindCpuInfo()` | CPU-Modell, Firmware, Status |
| `FindDevices()` | Module basierend auf PLC-Name |
| `FindRelatedTags()` | Tags basierend auf `tagName`, `errorcode` |
| `FindRelatedBlocks()` | Bausteine basierend auf `blockName` |
| `FindRelatedAlarms()` | Alarme basierend auf `alarmText` |
| `FindSimilarFailurePatterns()` | Ähnliche Fehler basierend auf Alarmtext |
| `GetAffectedSection()` | Hierarchie: Line → Station → Subsystem |
| `GenerateTechnicalSummary()` | Technische Kurzbewertung |

### Phase 4: Output-Formatting

```
[AnalysisResults] → Format → Output
```

- Transformation in Output-JSON
- Erstellung von `technical_summary` (Rule-based)
- Priorisierung von Ergebnissen

---

## Dateiübersicht (Skeleton)

```
tia-collector/FailureInvestigator/
├── FailureInvestigator.sln
├── README.md
├── FailureInvestigator.Core/
│   ├── IFailureInvestigator.cs
│   ├── FailureInvestigatorResult.cs
│   ├── InputModels/
│   │   ├── InvestigationRequest.cs
│   │   └── NormalizedInput.cs
│   ├── OutputModels/
│   │   ├── CpuInfo.cs
│   │   ├── Alarm.cs
│   │   ├── FailurePattern.cs
│   │   └── InvestigationResult.cs
│   └── FailureInvestigator.Core.csproj
├── FailureInvestigator.Analyzer/
│   ├── Analyzer/
│   │   ├── IAnalyzer.cs
│   │   ├── PlcAnalyzer.cs
│   │   ├── TagAnalyzer.cs
│   │   ├── BlockAnalyzer.cs
│   │   ├── AlarmAnalyzer.cs
│   │   └── FailurePatternAnalyzer.cs
│   ├── Analyzers/
│   │   ├── RuleBasedAnalyzer.cs
│   │   └── HybridAnalyzer.cs
│   └── FailureInvestigator.Analyzer.csproj
├── FailureInvestigator.Search/
│   ├── ISearchEngine.cs
│   ├── DirectorySearchEngine.cs
│   ├── FileSystemSearch.cs
│   └── FailureInvestigator.Search.csproj
├── FailureInvestigator.Output/
│   ├── IOutputFormatter.cs
│   ├── JsonOutputFormatter.cs
│   └── FailureInvestigator.Output.csproj
├── FailureInvestigator.Cli/
│   ├── Program.cs
│   ├── CliOptions.cs
│   └── FailureInvestigator.Cli.csproj
├── FailureInvestigator.Config/
│   ├── InvestigatorConfig.cs
│   └── FailureInvestigator.Config.csproj
└── samples/
    ├── sample-request.json
    └── sample-response.json
```

---

## API-Vertrag (Interface)

```csharp
// IFailureInvestigator.cs
public interface IFailureInvestigator
{
    Task<InvestigationResult> InvestigateAsync(InvestigationRequest request, CancellationToken ct);
}
```

---

## Beispiel-Anfrage & Antwort

### Anfrage

```bash
dotnet run --project FailureInvestigator.Cli \
  -- --alarm "Druck zu niedrig" \
  --station "Station_3" \
  --line "Production_Line_1"
```

### Antwort

```json
{
  "success": true,
  "timestamp": "2026-03-29T10:47:00Z",
  "input": {
    "alarmText": "Druck zu niedrig",
    "stationName": "Station_3",
    "lineName": "Production_Line_1"
  },
  "result": {
    "relevant_plcs": [...],
    "cpu_info": {...},
    "devices": [...],
    "related_tags": [...],
    "related_blocks": [...],
    "related_alarms": [...],
    "similar_failure_patterns": [...],
    "affected_section": "Production_Line_1 > Station_3 > Pressure_System",
    "technical_summary": "Druck-Sensor unterhalb Sollwert. Überprüfen Sie Ventil Y10."
  }
}
```

---

## Nächste Schritte (Future)

| Phase | Status | Description |
|-------|--------|-------------|
| Skeleton | ✅ | Dieses Dokument |
| Input/Output Models | 🚧 | Data Models |
| Search Engine | 🚧 | Directory Traversal |
| Analyzers | 🚧 | Rule-based Analysis |
| Output Formatter | 🚧 | JSON Formatting |
| CLI | 🚧 | Command Line Interface |
| Tests | 🚧 | Unit Tests |
| Documentation | 🚧 | API Docs |

---

**Status**: Skeleton — Ready for Implementation  
**Platform**: Windows (TIA-Collector Requirement)  
**Dependencies**: TIA-Collector Export, Weslr Entity Model
