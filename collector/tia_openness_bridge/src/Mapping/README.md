# Mapping-Bereich – TIA Openness Bridge (geplantes Mapping)

## 1. Zweck des Mapping-Bereichs

Der **Mapping-Bereich** (`src/Mapping/`) enthält später die **Mapping-Logik** des TIA-Collectors.

**Zweck:** Überführung von gelesenen TIA-Objekten (oder Zwischenergebnissen aus der Extraktion) in die internen Collector-Contracts (TiaExportContract und alle verknüpften Contracts).

**Rolle im Collector:** Der Mapping-Bereich ist die **Zwischenschicht** zwischen der Extraktions-Logik und den reinen Contract-Modellen. Er übersetzt Rohdaten aus TIA in strukturierte, serialisierbare Vertragsobjekte.

**Was hier umgesetzt wird:**
- Mapping von TIA-Objekten → Contract-Objekte
- ID-Generierung und -Verwaltung
- Feldzuweisung (Property → Contract)
- Behandlung optionaler Felder
- Aufbau des TiaExportContract aus Contract-Listen

**Was hier NICHT umgesetzt wird:**
- C#-Code (erst in einem späteren Schritt)
- Openness-Zugriffe (dieser Bereich nutzt bereits extrahierte Daten)
- JSON-Serialisierung (dieser Bereich erzeugt nur Contract-Objekte)
- Dateiausgabe (dieser Bereich schreibt keine Dateien)
- Logging-Implementierung (dieser Bereich generiert Diagnose-Daten, siehe DiagnosticsCollector)

## 2. Geplante Verantwortlichkeiten

| Verantwortlichkeit | Beschreibung | Was **nicht** dazugehört |
|--------------------|--------------|--------------------------|
| **ProjectToContractMapper** | Überführt Projekt-Daten in ProjectContract | Projekt-Änderung, Save |
| **DeviceToContractMapper** | Überführt Device-Daten in DeviceContract | Geräte-Konfiguration, Download |
| **PlcToContractMapper** | Überführt PLC-Daten in PlcContract | PLC-Steuerung, Restart |
| **CpuToContractMapper** | Überführt CPU-Daten in CpuContract | Online-Read, Monitor |
| **ModuleToContractMapper** | Überführt Module-Daten in ModuleContract | Module-Konfiguration, Update |
| **TagTableToContractMapper** | Überführt TagTable-Daten in TagTableContract | Tag-Werte, Live-Read |
| **TagToContractMapper** | Überführt Tag-Daten in TagContract | Tag-Status, Force |
| **BlockToContractMapper** | Überführt Block-Daten in ProgramBlockContract | Block-Inhalte, Analyse |
| **TopologyToContractMapper** | Überführt Topologie-Daten in TopologyRelationContract | Netzwerk-Scan, Discovery |
| **AlarmToContractMapper** | Überführt Alarm-Daten in AlarmContract | Alarm-Status, Acknowledge |
| **TiaExportContractBuilder** | Baut TiaExportContract aus Contract-Listen | Serialisierung, File-Write |

### Einzelne Verantwortlichkeiten (Zusammenfassung)

- **ProjectToContractMapper**: Projekt → ProjectContract
- **DeviceToContractMapper**: Device → DeviceContract
- **PlcToContractMapper**: PLC → PlcContract
- **CpuToContractMapper**: CPU → CpuContract
- **ModuleToContractMapper**: Module → ModuleContract
- **TagTableToContractMapper**: TagTable → TagTableContract
- **TagToContractMapper**: Tag → TagContract
- **BlockToContractMapper**: Block → ProgramBlockContract
- **TopologyToContractMapper**: Topology → TopologyRelationContract
- **AlarmToContractMapper**: Alarm → AlarmContract
- **TiaExportContractBuilder**: Contract-Listen → TiaExportContract

## 3. Abgrenzung

### Was **nicht** zum Mapping-Bereich gehört

| Bereich | Verantwortung | Warum Mapping **nicht** dazugehört |
|---------|---------------|------------------------------------|
| **SessionManager** | Openness-Session | Mapping nutzt Sessions, sie sind nicht Teil von Mapping |
| **Extraction** | TIA-Zugriff | Mapping nutzt bereits extrahierte Daten, sie ist nicht Teil von Mapping |
| **JsonSerializer** | JSON-Serialisierung | Mapping erzeugt Contract-Objekte, sie serialisiert nicht |
| **ExportWriter** | Datei schreiben | Mapping arbeitet in Memory, sie schreibt keine Dateien |
| **Normalizer** | Weslr-Transformierung | Mapping ist TIA-relevant, nicht Weslr-relevant |
| **ErrorHandler** | Exceptions | Mapping wirft keine neuen Exceptions, sie transportiert nur Daten |
| **Logger** | Logging | Mapping generiert Diagnose-Daten, sie logt nicht |

### Klare Grenze

- **Extraction**: Konvertierung TIA Openness → Rohdaten
- **Mapping**: Konvertierung Rohdaten → Contract-Objekte
- **Serialization**: Konvertierung Contract → JSON-String
- **ExportWriter**: Konvertierung JSON-String → Datei

## 4. Datenfluss innerhalb des Mapping-Bereichs

### Logische Reihenfolge (ohne Code)

```
1. Extraction
   ↓ (Rohdaten aus TIA)
2. Mapping-Kette
   ↓
   2a. ProjectToContractMapper → ProjectContract
   2b. DeviceToContractMapper → DeviceContract[]
   2c. PlcToContractMapper → PlcContract[]
   2d. CpuToContractMapper → CpuContract[]
   2e. ModuleToContractMapper → ModuleContract[]
   2f. TagTableToContractMapper → TagTableContract[]
   2g. TagToContractMapper → TagContract[]
   2h. BlockToContractMapper → ProgramBlockContract[]
   2i. TopologyToContractMapper → TopologyRelationContract[]
   2j. AlarmToContractMapper → AlarmContract[]
   ↓
3. TiaExportContractBuilder → TiaExportContract
```

### Einzelschritte

1. **Extraktion**: Extraction → Rohdaten (ohne Contract)
2. **Mapping**: Alle Mapper → Contract-Objekte
3. **Contract-Build**: TiaExportContractBuilder → TiaExportContract

## 5. Qualitätsregeln

### ID-Generierung und -Verwaltung

- **Stabile IDs**: IDs sind eindeutig, 4-16 chars, lowercase alphanumeric
- **Konsistente IDs**: Gleiche TIA-Objekte erhalten gleiche IDs in jedem Export
- **Referenzen**: Contract-Referenzen (z. B. `PlcId` in CpuContract) sind konsistent

### Feldbelegung

- **Konsistente Feldbelegung**: Jedes Contract-Feld wird immer befüllt (wenn verfügbar)
- **Null-Handling**: Optionale Felder werden `null` gesetzt (nicht ignoriert)
- **Keine stillen impliziten Bedeutungsänderungen**: Jede Zuweisung ist dokumentiert

### Nachvollziehbarkeit

- **Quellenverweisung**: Jeder Contract-Objekt enthält Quell-Referenz (TIA-Objekt-ID)
- **Diagnose-Feedback**: Diagnose-Objekte enthalten Mapping-Referenzen

## 6. Fehler- und Randfallbehandlung

### Umgang mit unvollständigen Quellobjekten

- **Fehlende Felder**: Verwende Standardwert oder `null`
- **Ungültige Werte**: Warnung, Standardwert oder `null`
- **Nicht zugeordnete Objekte**: Warnung, Überspringen oder Fallback

### Umgang mit fehlenden optionalen Feldern

- **Leere Listen**: Verwende `new T[]()` statt `null`
- **Fehlende Referenzen**: Verwende `null` oder Fallback-Referenz
- **Unbekannte Werte**: Verwende Standardwert oder `null`

### Diagnose-Feedback

- **Fehler**: Exportiert in `collector_diagnostics.errors`
- **Warnungen**: Exportiert in `collector_diagnostics.warnings`
- **Stats**: Exportiert in `collector_diagnostics` (files_processed, objects_extracted)

## 7. Read-only-Prinzip

### Wie das read-only Prinzip im Mapping widerspiegeln soll

- **Keine SPS-Steuerung**: Keine Restart, Stop, Start, Mode-Change
- **Keine SPS-Kommunikation**: Keine Online-Read/Write, keine Force
- **Keine TIA-Projekt-Änderung**: Keine Apply, Commit, Save im Projekt
- **Keine Download/Upload**: Keine SPS-Datei-Transfers
- **Keine Runtime-Daten**: Keine Live-Tag-Werte, keine Task-Zyklen

### Konsequenzen für die Mapping-Struktur

- **Mapping-Methoden**: `MapProject()`, `MapDevice()`, `MapPlc()`, etc.
- **Keine SPS-Objekte**: Mapping kennt keine SPS-Objekte (nur Contract-Objekte)
- **Keine External References**: Mapping ist self-contained (keine Verweise auf TIA API)

## 8. Nächste minimale Implementierungsschritte

### Erste C#-Mapping-Dateien (nach dieser Mapping-Dokumentation)

| Datei | Zweck |
|-------|-------|
| **ProjectToContractMapper.cs** | Mapping: Projekt → ProjectContract |
| **DeviceToContractMapper.cs** | Mapping: Device → DeviceContract |
| **PlcToContractMapper.cs** | Mapping: PLC → PlcContract |
| **CpuToContractMapper.cs** | Mapping: CPU → CpuContract |
| **ModuleToContractMapper.cs** | Mapping: Module → ModuleContract |
| **TagTableToContractMapper.cs** | Mapping: TagTable → TagTableContract |
| **TagToContractMapper.cs** | Mapping: Tag → TagContract |
| **BlockToContractMapper.cs** | Mapping: Block → ProgramBlockContract |
| **TopologyToContractMapper.cs** | Mapping: Topology → TopologyRelationContract |
| **AlarmToContractMapper.cs** | Mapping: Alarm → AlarmContract |
| **TiaExportContractBuilder.cs** | Baut TiaExportContract aus Contract-Listen |

### Kein Code hier

Diese Dokumentation definiert nur die **Mapping-Struktur und Verantwortlichkeiten**. Die C#-Implementierung folgt in einem separaten Schritt.

---

*Letzte Aktualisierung: 2026-03-29*