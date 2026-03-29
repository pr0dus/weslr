# Extraction-Bereich – TIA Openness Bridge (geplante Extraktion)

## 1. Zweck des Extraction-Bereichs

Der **Extraktion-Bereich** (`src/Extraction/`) enthält später die **Extraktions-Logik** des TIA-Collectors.

**Zweck:** Lesender Zugriff auf TIA Portal V20-Objekte über TIA Openness API und Überführung der gelesenen Daten in die internen Contract-Objekte (TiaExportContract und alle verknüpften Contracts).

**Rolle im Collector:** Der Extraktion-Bereich ist die **Zwischenschicht** zwischen der TIA Openness API und den reinen Contract-Modellen. Er liest Engineering-Daten aus dem geöffneten TIA-Projekt und übersetzt sie in strukturierte Vertragsobjekte.

**Was hier umgesetzt wird:**
- TIA Openness API-Zugriff (Session, Project, PLCs, CPUs, Devices, etc.)
- Objekt-basierte Extraktions-Logik (für jeden Typ: Project, Device, PLC, CPU, Module, Tags, Blocks, etc.)
- Fehlerbehandlung und Diagnose-Generierung
- Aufbau des TiaExportContract aus extrahierten Daten

**Was hier NICHT umgesetzt wird:**
- C#-Code (erst in einem späteren Schritt)
- JSON-Serialisierung (dieser Bereich extrahiert nur Daten)
- Dateiausgabe (dieser Bereich schreibt keine Dateien)
- Openness-Session-Management (dieser Bereich nutzt Sessions, siehe SessionManager)
- Logging-Implementierung (dieser Bereich generiert Diagnose-Daten, siehe DiagnosticsCollector)

## 2. Geplante Verantwortlichkeiten

| Verantwortlichkeit | Beschreibung | Was **nicht** dazugehört |
|--------------------|--------------|--------------------------|
| **ProjectExtractor** | Liest Projekt-Metadaten (id, name, path, last_modified, author) | Projekt-Änderung, Save |
| **DeviceExtractor** | Liest Device-Informationen (PLC, HMI, IO, etc.) mit Typ, Version, Nummern | Geräte-Konfiguration, Download |
| **PlcExtractor** | Liest PLC-Informationen (IP, Rack, Slot, Model) | PLC-Steuerung, Restart |
| **CpuExtractor** | Liest CPU-Informationen (Interfaces, IP, MAC) | Online-Read, Monitor |
| **ModuleExtractor** | Liest Module (SM, PS, IM) mit Typ, Version, Nummern | Module-Konfiguration, Update |
| **TagTableExtractor** | Liest Tag-Table-Struktur (DB-Blöcke) | Tag-Werte, Live-Read |
| **TagExtractor** | Liest Tag-Metadaten (Name, DataType, Adresse, Comment) | Tag-Status, Force |
| **BlockExtractor** | Liest Block-Metadaten (OB, FC, FB, DB) mit Typ, Nummer, Networks | Block-Inhalte, Analyse |
| **TopologyExtractor** | Liest Topologie (Netzwerktyp, IP-Verbindungen) | Netzwerk-Scan, Discovery |
| **AlarmExtractor** | Liest Alarm-Metadaten (Severity, Message, Tag-Referenz) | Alarm-Status, Acknowledge |
| **TiaExportContractBuilder** | Baut den TiaExportContract aus extrahierten Daten | Serialisierung, File-Write |

### Einzelne Verantwortlichkeiten (Zusammenfassung)

- **ProjectExtractor**: Projekt-Metadaten aus TIA
- **DeviceExtractor**: Devices (PLC, HMI, IO) mit Typ, Version, Nummern
- **PlcExtractor**: PLCs mit IP, Rack, Slot, Model
- **CpuExtractor**: CPUs mit Interfaces (IP, MAC, subnet)
- **ModuleExtractor**: Modules (SM, PS, IM) mit Typ, Version, Nummern
- **TagTableExtractor**: Tag-Tables mit DB-Blöcken
- **TagExtractor**: Tags mit Name, DataType, Adresse, Comment
- **BlockExtractor**: Blocks (OB, FC, FB, DB) mit Typ, Nummer, Networks
- **TopologyExtractor**: Topologie (Netzwerktyp, IP-Verbindungen)
- **AlarmExtractor**: Alarme mit Severity, Message, Tag-Referenz
- **TiaExportContractBuilder**: Baut TiaExportContract aus extrahierten Daten

## 3. Abgrenzung

### Was **nicht** zum Extraction-Bereich gehört

| Bereich | Verantwortung | Warum Extraction **nicht** dazugehört |
|---------|---------------|----------------------------------------|
| **SessionManager** | Openness-Session | Extraction nutzt Sessions, sie sind nicht Teil von Extraction |
| **ExportWriter** | JSON-Datei schreiben | Extraction extrahiert nur Daten, sie schreibt keine Dateien |
| **Normalizer** | Weslr-Transformierung | Extraction ist TIA-relevant, nicht Weslr-relevant |
| **JsonSerializer** | JSON-Serialisierung | Extraction extrahiert Daten in Memory, sie serialisiert nicht |
| **FileSystemWriter** | Datei-IO | Extraction arbeitet in Memory, sie schreibt keine Dateien |
| **ErrorHandler** | Exceptions | Extraction wirft keine neuen Exceptions, sie transportiert nur Daten |
| **Logger** | Logging | Extraction generiert Diagnose-Daten, sie logt nicht |

### Klare Grenze

- **Extraction**: Konvertierung TIA Openness → Contract-Objekte
- **Serialization**: Konvertierung Contract → JSON-String
- **ExportWriter**: Konvertierung JSON-String → Datei

## 4. Datenfluss innerhalb der Extraktion

### Logische Reihenfolge (ohne Code)

```
1. SessionManager
   ↓ (TIA Openness Session öffnen)
2. ProjectReader → ProjectContract
   ↓
3. Extraktions-Kette
   ↓
   3a. DeviceExtractor → DeviceContract[]
   3b. PlcExtractor → PlcContract[]
   3c. CpuExtractor → CpuContract[]
   3d. ModuleExtractor → ModuleContract[]
   3e. TagTableExtractor → TagTableContract[]
   3f. TagExtractor → TagContract[]
   3g. BlockExtractor → ProgramBlockContract[]
   3h. TopologyExtractor → TopologyRelationContract[]
   3i. AlarmExtractor → AlarmContract[]
   ↓
4. DiagnosticsCollector → CollectorDiagnosticContract
   ↓
5. TiaExportContractBuilder → TiaExportContract
```

### Einzelschritte

1. **Session öffnen**: SessionManager → TIA Openness Session
2. **Projekt lesen**: ProjectExtractor → ProjectContract
3. **Extraktion**: Alle Extractor-Bausteine → Contract-Listen
4. **Diagnose erfassen**: DiagnosticsCollector → CollectorDiagnosticContract
5. **Contract-Build**: TiaExportContractBuilder → TiaExportContract

## 5. Fehler- und Abbruchverhalten

### Kritische Fehler (Abbruch)

- **TIA Openness nicht erreichbar** → Abbruch (keine Sitzung)
- **Projekt nicht geöffnet / nicht lesbar** → Abbruch (kein Zugriff)
- **API-Exception (nicht abgefangen)** → Abbruch
- **Speicherprobleme** → Abbruch

### Nicht-kritische Fehler (Warnung + Fortsetzung)

- **Unbekannte Block-Definition** → Warnung, Fallback
- **Unbekannte Tag-Definition** → Warnung, Fallback
- **Topologie unvollständig** → Warnung, Partial-Export

### Diagnose-Generierung

- **Fehler**: Exportiert in `collector_diagnostics.errors`
- **Warnungen**: Exportiert in `collector_diagnostics.warnings`
- **Stats**: Exportiert in `collector_diagnostics` (files_processed, objects_extracted)

## 6. Read-only-Prinzip

### Wie das read-only Prinzip im Extraktion-Bereich widerspiegeln soll

- **Keine SPS-Steuerung**: Keine Restart, Stop, Start, Mode-Change
- **Keine SPS-Kommunikation**: Keine Online-Read/Write, keine Force
- **Keine TIA-Projekt-Änderung**: Keine Apply, Commit, Save im Projekt
- **Keine Download/Upload**: Keine SPS-Datei-Transfers
- **Keine Runtime-Daten**: Keine Live-Tag-Werte, keine Task-Zyklen

### Konsequenzen für die Extraktions-Struktur

- **Extraktions-Methoden**: `ReadOnlyExtract()`, `GetProjectMetadata()`, `ReadDeviceList()`
- **Keine Methoden**: `SaveProject()`, `DownloadToPLC()`, `UploadFromPLC()`, `ForceTag()`
- **Keine Klassen**: `PLCController`, `OnlineInterface`, `RuntimeMonitor`

## 7. Nächste minimale Implementierungsschritte

### Erste C#-Extraktions-Dateien (nach dieser Extraktions-Dokumentation)

| Datei | Zweck |
|-------|-------|
| **ProjectExtractor.cs** | Extrahiert Projekt-Metadaten |
| **DeviceExtractor.cs** | Extrahiert Devices (PLC, HMI, IO) |
| **PlcExtractor.cs** | Extrahiert PLCs (IP, Rack, Slot, Model) |
| **CpuExtractor.cs** | Extrahiert CPUs (Interfaces, IP, MAC) |
| **ModuleExtractor.cs** | Extrahiert Modules (SM, PS, IM) |
| **TagTableExtractor.cs** | Extrahiert Tag-Tables |
| **TagExtractor.cs** | Extrahiert Tags |
| **BlockExtractor.cs** | Extrahiert Blocks (OB, FC, FB, DB) |
| **TopologyExtractor.cs** | Extrahiert Topologie |
| **AlarmExtractor.cs** | Extrahiert Alarme |
| **TiaExportContractBuilder.cs** | Baut TiaExportContract aus extrahierten Daten |

### Kein Code hier

Diese Dokumentation definiert nur die **Extraktions-Struktur und Verantwortlichkeiten**. Die C#-Implementierung folgt in einem separaten Schritt.

---

*Letzte Aktualisierung: 2026-03-29*