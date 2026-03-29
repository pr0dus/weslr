# Source-Bereich – TIA Openness Bridge (geplante Struktur)

## 1. Zweck des Source-Bereichs

Der **Source-Bereich** (`src/`) enthält später den gesamten C#-Implementierungscode des TIA-Collectors.

**Verantwortung:** Windows-seitiger, read-only Zugriff auf TIA Portal V20-Projekte über TIA Openness API und Extraktion von Engineering-Daten in das definierte TIA-Exportformat.

**Was hier umgesetzt wird:**
- TIA-Verbindungen (Openness)
- Projekt- und Objekt-Leselogik
- Extraktions-Logik pro Objekttyp
- Export-Schreib-Logik
- Diagnose- und Logging-Schnittstellen

**Was hier NICHT umgesetzt wird:**
- C#-Code (erst in einem späteren Schritt)
- Build-Setup (`.sln`, `.csproj`)
- API-Definitionen (diese folgen nach der Strukturierung)

## 2. Empfohlene interne Bausteine

| Baustein | Zweck | Eingaben | Ausgaben | Was **nicht** dazugehört |
|----------|-------|----------|----------|--------------------------|
| **SessionManager** | Verwaltung der TIA Openness Sitzung | None | TIA-Session-Objekt | PLC-Kommunikation, Steuerungslogik |
| **ProjectReader** | Liest das geöffnete TIA-Projekt aus | Session-Objekt | Projekt-Metadaten | Schreib-Operationen, Konvertierung |
| **DeviceExtractor** | Extrahiert Devices (PLC, HMI, IO, etc.) | Projekt-Objekt | Device-Listen | PLC-Status, Runtime-Daten |
| **PlcExtractor** | Extrahiert PLCs mit IP und Konfiguration | Projekt-Objekt | PLC-Listen | SPS-Steuerung, Restart |
| **CpuExtractor** | Extrahiert CPUs mit Interfaces | PLC-Objekt | CPU-Listen | Online-Read, Monitor |
| **ModuleExtractor** | Extrahiert Modules (SM, PS, IM) | PLC-Objekt | Module-Listen | Modul-Konfiguration, Download |
| **TagExtractor** | Extrahiert Tags mit Adressen | Projekt-Objekt | Tag-Listen | Live-Tag-Werte, Force |
| **BlockExtractor** | Extrahiert Program Blocks (OB, FC, FB, DB) | Projekt-Objekt | Block-Listen | Block-Inhalte, Analyse |
| **TopologyExtractor** | Extrahiert Netzwerk-Topologie | Projekt-Objekt | Topologie-Listen | Netzwerk-Scan, Discovery |
| **AlarmExtractor** | Extrahiert alarmrelevante Engineering-Daten | Projekt-Objekt | Alarm-Listen | Alarm-Status, Acknowledge |
| **ExportWriter** | Schreibt `tia_export.json` | Extrahierte Daten | JSON-Datei | Komprimierung, Cloud-Upload |
| **DiagnosticsCollector** | Erfasst Diagnose-Informationen | Extractor-Status | errors, warnings, stats | Log-Dateien, Telemetrie |
| **ErrorHandler** | Behandelt Fehler und Abbrüche | Exception-Objekte | Status, Meldungen | Auto-Recovery, Workarounds |
| **ValidationWriter** | Validiert Export gegen Schema | Extrahierte Daten | Validierungsstatus | JSON-Schema-Editierung |

### Einzelne Bausteine (Zusammenfassung)

- **SessionManager**: Öffnet und verwaltet TIA Openness Sitzung (read-only)
- **ProjectReader**: Liest Projekt-Metadaten (name, path, last_modified, author)
- **DeviceExtractor**: Extrahiert Devices (PLC, HMI, IO, etc.) mit Typ, Version, Nummern
- **PlcExtractor**: Extrahiert PLCs mit IP, Rack, Slot, Model
- **CpuExtractor**: Extrahiert CPUs mit Interfaces (IP, MAC, subnet)
- **ModuleExtractor**: Extrahiert Modules (SM, PS, IM) mit Typ, Version, Nummern
- **TagExtractor**: Extrahiert Tags mit Name, DataType, Adresse, Comment
- **BlockExtractor**: Extrachiert Blocks (OB, FC, FB, DB) mit Typ, Nummer, Networks
- **TopologyExtractor**: Extrahiert Topologie (Netzwerktyp, IP-Verbindungen)
- **AlarmExtractor**: Extrahiert Alarme mit Severity, Message, Tag-Referenz
- **ExportWriter**: Schreibt JSON-Datei nach Schema `tia_export.schema.json`
- **DiagnosticsCollector**: Erfasst Start/End-Time, Files, Objects, Errors, Warnings
- **ErrorHandler**: Behandelt Exceptions, setzt Abbruchstatus, loggt Fehler
- **ValidationWriter**: Prüft Export-Struktur gegen Schema (ohne Schema-Code)

## 3. Datenfluss innerhalb des Collectors

### Logische Reihenfolge (ohne Code)

```
1. SessionManager
   ↓ (TIA Openness Session öffnen)
2. ProjectReader
   ↓ (Projekt-Metadaten lesen)
3. Extractor-Kette
   ↓
   3a. DeviceExtractor (Devices)
   3b. PlcExtractor (PLCs)
   3c. CpuExtractor (CPUs)
   3d. ModuleExtractor (Modules)
   3e. TagExtractor (Tags)
   3f. BlockExtractor (Blocks)
   3g. TopologyExtractor (Topology)
   3h. AlarmExtractor (Alarms)
   ↓
4. DiagnosticsCollector
   ↓ (Diagnose erfassen)
5. ExportWriter
   ↓ (tia_export.json schreiben)
6. ErrorStatus + Logging
```

### Einzelschritte

1. **Session öffnen**: SessionManager → TIA Openness Session
2. **Projekt lesen**: ProjectReader → Projekt-Metadaten
3. **Extraktion**: Alle Extractor-Bausteine → rohe Engineering-Daten
4. **Diagnose erfassen**: DiagnosticsCollector → errors, warnings, stats
5. **Export schreiben**: ExportWriter → `tia_export.json`
6. **Logging**: DiagnosticsCollector → Protokolldatei (optional)

## 4. Read-only-Prinzip in der Source-Struktur

### Wie sich read-only in der Struktur widerspiegeln soll

- **Keine Schreib-Methoden** in Extractors (nur Lesen, keine Save/Write)
- **Keine PLC-Kommunikation** (keine Online-Read/Write, keine Steuerung)
- **Keine TIA-Projekt-Änderung** (keine Apply, Commit, Save im Projekt)
- **Keine Download/Upload** (keine SPS-Datei-Transfers)
- **Keine Runtime-Daten** (keine Live-Tag-Werte, keine Task-Zyklen)

### Konsequenzen für die Code-Struktur

- Extractor-Methoden: `ReadOnlyExtract()`, `GetProjectMetadata()`, `ReadDeviceList()`
- Keine Methoden: `SaveProject()`, `DownloadToPLC()`, `UploadFromPLC()`, `ForceTag()`
- Keine Klassen: `PLCController`, `OnlineInterface`, `RuntimeMonitor`

## 5. Fehler- und Abbruchstellen

### Kritische Fehler (Abbruch)

- **TIA Openness nicht erreichbar** → Abbruch (keine Sitzung)
- **Projekt nicht geöffnet / nicht lesbar** → Abbruch (kein Zugriff)
- **Speicherprobleme** → Abbruch (kein Export möglich)
- **API-Exception** (nicht abgefangen) → Abbruch

### Nicht-kritische Fehler (Warnung + Fortsetzung)

- **Unbekannte Block-Definition** → Warnung, Fallback
- **Unbekannte Tag-Definition** → Warnung, Fallback
- **Topologie unvollständig** → Warnung, Partial-Export

### Abbruch-Logik

- Bei kritischem Fehler: Abbruch-Status setzen, Export löschen, Diagnose speichern
- Bei Teilfehlern: Warnung loggen, Fortsetzen, Partial-Export erlauben
- Keine stillen Abbrüche: Jeder Abbruch muss protokolliert sein

### ErrorHandler-Rolle

- Exception abfangen → Status setzen → Meldung protokollieren → Abbruch oder Fortsetzung
- Keine "Swallowing" von Exceptions: Alle Fehler müssen sichtbar sein

## 6. Was bewusst noch nicht umgesetzt wird

- **Keine PLC-Kommunikation**: Keine SPS-Steuerung (Restart, Stop, Start, Mode-Change)
- **Keine Schreibzugriffe**: Keine Änderungen am TIA-Projekt (keine Apply, Commit, Save)
- **Keine Weslr-Analyse**: Keine Transformation in Weslr-Entity-Graphen (Normalizer-Verantwortung)
- **Keine Runtime-Telemetrie**: Keine Live-Überwachung von SPS-Daten (keine I/O-Logik, keine Task-Zyklen)
- **Keine Cloud-Upload**: Keine Datenübertragung außerhalb des lokalen Systems
- **Keine Komprimierung**: Keine ZIP oder andere Archiv-Formate
- **Keine GUI**: Keine Benutzeroberfläche (nur CLI/Plugin-Interface)

## 7. Nächste minimale Implementierungsschritte

### Erste C#-Quelldateien (nach dieser Struktur-Dokumentation)

| Datei | Zweck |
|-------|-------|
| `SessionManager.cs` | Öffnet TIA Openness Sitzung, verwaltet Verbindungen |
| `ProjectReader.cs` | Liest Projekt-Metadaten (name, path, last_modified, author) |
| `DeviceExtractor.cs` | Extrahiert Devices (Typ, Version, Nummern) |
| `PlcExtractor.cs` | Extrahiert PLCs (IP, Rack, Slot, Model) |
| `CpuExtractor.cs` | Extrahiert CPUs (Interfaces, IP, MAC) |
| `ModuleExtractor.cs` | Extrahiert Modules (SM, PS, IM) |
| `TagExtractor.cs` | Extrahiert Tags (Name, DataType, Adresse) |
| `BlockExtractor.cs` | Extrahiert Blocks (OB, FC, FB, DB) |
| `TopologyExtractor.cs` | Extrahiert Topologie (Netzwerktyp, IPs) |
| `AlarmExtractor.cs` | Extrahiert Alarme (Severity, Message, Tag-Referenz) |
| `ExportWriter.cs` | Schreibt `tia_export.json` nach Schema |
| `DiagnosticsCollector.cs` | Erfasst Diagnose (errors, warnings, stats) |
| `ErrorHandler.cs` | Behandelt Exceptions, setzt Abbruchstatus |

### Kein Code hier

Diese Dokumentation definiert nur die **Struktur und Verantwortlichkeiten**. Die C#-Implementierung folgt in einem separaten Schritt.

---

*Letzte Aktualisierung: 2026-03-29*