# Contracts-Bereich – TIA Openness Bridge (geplante Vertragsstruktur)

## 1. Zweck des Contracts-Bereichs

Der **Contracts-Bereich** (`src/Contracts/`) enthält später die **Vertragsdefinitionen** (C#-Modelle, Interfaces, DTOs) für den TIA-Collector.

**Zweck:** Klare Trennung zwischen:
- **Extraktionslogik** (`src/`)
- **Exportstruktur** (`src/Contracts/`)
- **Schemaschema** (`schemas/tia_export.schema.json`)

**Rolle im Collector:** Die Verträge dienen als **Zwischenschicht** zwischen der rohen TIA-Extraktion und dem finalen JSON-Export. Sie stellen sicher, dass die exportierten Daten **strukturiert**, **prüfbar** und **typsicher** sind.

**Was hier umgesetzt wird:**
- C#-Modelle (Klassen, Interfaces)
- Verträge zwischen Extraktions- und Export-Code
- Serialisierungs-Definitionen (JSON.NET oder System.Text.Json)

**Was hier NICHT umgesetzt wird:**
- C#-Code (erst in einem späteren Schritt)
- Implementierung der Extraktions-Logik
- Export-Schreib-Logik
- TIA Openness API-Verbindungen

## 2. Geplante Vertragsarten

| Kategorie | Zweck | Typische Inhalte | Was **nicht** dazugehört |
|-----------|-------|------------------|--------------------------|
| **Export-Metadaten** | Header-Metadaten für den Export | collector_version, export_timestamp, source_file, format_version, tia_portal_version | Session-Status, Projekt-Logik |
| **ProjectContract** | Projekt-Metadaten | id, name, type, path, description, last_modified, author | Openness-Session, Projekt-Änderung |
| **DeviceContract** | Gerätemetadaten | id, name, type, hardware_version, firmware_version, part_number, order_number, product_id | Geräte-Konfiguration, Download |
| **PlcContract** | PLC-Metadaten | id, device_id, name, rack, slot, model, ip_address, subnet_mask, gateway | PLC-Steuerung, Restart |
| **CpuContract** | CPU-Metadaten | id, plc_id, module_type, name, slot, serial_number, interface_addresses | Online-Read, Monitor |
| **ModuleContract** | Module (SM, PS, IM) | id, plc_id, module_type, name, position, hardware_version, firmware_version, part_number | Modul-Konfiguration, Update |
| **TagTableContract** | Tag-Table-Struktur | id, name, plc_id, blocks (mit db_number, name, size, block_type) | Tag-Werte, Live-Read |
| **TagContract** | Tag-Metadaten | id, name, data_type, address, plc_id, comment, initial_value, read_write, direct_access | Tag-Status, Force |
| **BlockContract** | Block-Metadaten (OB, FC, FB, DB) | id, name, type, plc_id, number, networks, interface, comment | Block-Inhalte, Analyse |
| **TopologyContract** | Netzwerk-Topologie | id, source_id, target_id, connection_type, interface_source, interface_target, ip_source, ip_target, subnet | Netzwerk-Scan, Discovery |
| **AlarmContract** | Alarm-Metadaten | id, name, plc_id, type, severity, message_text, acknowledge_required, archive_required, enabled, tag_reference, delay, deadband | Alarm-Status, Acknowledge |
| **DiagnosticsContract** | Diagnose-Informationen | start_time, end_time, duration_ms, files_processed, objects_extracted, errors, warnings | Log-Dateien, Telemetrie |

### Einzelne Vertragsarten (Zusammenfassung)

- **ExportMetadataContract**: Header für den Export (Version, Timestamp, Quelle)
- **ProjectContract**: Projekt-Metadaten (name, path, last_modified, author)
- **DeviceContract**: Geräte (PLC, HMI, IO) mit Typ, Version, Nummern
- **PlcContract**: PLCs mit IP, Rack, Slot, Model
- **CpuContract**: CPUs mit Interfaces (IP, MAC, subnet)
- **ModuleContract**: Modules (SM, PS, IM) mit Typ, Version, Nummern
- **TagTableContract**: Tag-Tables mit DB-Blöcken
- **TagContract**: Tags mit Name, DataType, Adresse, Comment
- **BlockContract**: Blocks (OB, FC, FB, DB) mit Typ, Nummer, Networks
- **TopologyContract**: Topologie (Netzwerktyp, IP-Verbindungen)
- **AlarmContract**: Alarme mit Severity, Message, Tag-Referenz
- **DiagnosticsContract**: Diagnose (errors, warnings, stats)

## 3. Abgrenzung zu anderen Bereichen

### Was **nicht** zum Contracts-Bereich gehört

| Bereich | Verantwortung | Warum Contracts **nicht** dazugehört |
|---------|---------------|--------------------------------------|
| **SessionManager** | Openness-Session | Contracts sind DTOs, keine Sitzungslogik |
| **ProjectReader** | Projekt-Leselogik | Contracts repräsentieren Daten, sie lesen keine Projekt-Struktur |
| **DeviceExtractor** | Extraktions-Logik | Contracts sind Modelle, sie extrahieren keine Daten |
| **ExportWriter** | JSON-Schreib-Logik | Contracts repräsentieren Daten, sie schreiben keine Dateien |
| **ErrorHandler** | Exception-Handling | Contracts sind reine Datenmodelle, sie behandeln keine Exceptions |
| **Normalizer** | Weslr-Transformierung | Contracts sind TIA-Export-Mittel, keine Weslr-Entity-Modelle |
| **Analyzer** | Failure-Investigation | Contracts sind passive Daten, sie analysieren nicht |

### Klare Grenze

- **Contracts**: Reine Datenmodelle (DTOs, POCOs, Records)
- **Extraktion**: Logik, die Daten aus TIA liest und in Contracts schreibt
- **Export**: Logik, die Contracts in JSON serialisiert und schreibt

## 4. Beziehung zum TIA-Export-Schema

### Wie die Contracts das Schema stützen

- **Verträge spiegeln das Schema**: Jede JSON-Struktur in `tia_export.schema.json` hat ein C#-Contract-Modell
- **Typsichere Extraktion**: C#-Typen garantieren, dass die extrahierten Daten dem Schema entsprechen
- **Validierung**: Verträge können Validierungs-Attribute tragen (z. B. `[Required]`, `[Range(0, 1)]`)
- **JSON-Serialization**: Verträge sind serialisierbar (mit JSON.NET oder System.Text.Json)

### Strukturierte Exportobjekte

- Verträge dienen als **Zwischenschicht** zwischen TIA Openness API und JSON-Export
- Sie stellen sicher, dass **nur definierte Felder** exportiert werden
- Sie ermöglichen eine **klare Trennung** zwischen "was extrahiert wird" und "wie exportiert wird"

## 5. Read-only- und Sicherheitsbezug

### Wie die Verträge den read-only Charakter widerspiegeln sollen

- **Keine Methoden**: Verträge sind reine Datencontainer (Properties, keine Methoden)
- **Keine SPS-Kommunikation**: Verträge enthalten keine Logik für SPS-Steuerung
- **Keine Schreib-Operationen**: Verträge repräsentieren nur gelesene Daten
- **Keine API-Abhängigkeiten**: Verträge sind unabhängig von TIA Openness API

### Konsequenzen für die Vertrags-Struktur

- **Properties nur, keine Methoden**: `public string Name { get; set; }`, keine `void Extract()`
- **Keine SPS-Referenzen**: Verträge enthalten keine `PLC`, `Session`, `Project`-Objekte
- **Nur Primitive und Strings**: Verträge nutzen `string`, `int`, `float`, `bool`, `List<T>`, `Dictionary<string, object>`
- **Keine External References**: Verträge sind self-contained (keine Referenzen auf TIA API)

## 6. Nächste minimale Implementierungsschritte

### Erste C#-Vertragstypen (nach dieser Vertrags-Dokumentation)

| Vertrag | Zweck |
|---------|-------|
| **ExportMetadataContract** | Header-Metadaten (Version, Timestamp, Quelle) |
| **ProjectContract** | Projekt-Metadaten (name, path, last_modified, author) |
| **DeviceContract** | Geräte (PLC, HMI, IO) mit Typ, Version, Nummern |
| **PlcContract** | PLCs mit IP, Rack, Slot, Model |
| **CpuContract** | CPUs mit Interfaces (IP, MAC, subnet) |
| **ModuleContract** | Modules (SM, PS, IM) mit Typ, Version, Nummern |
| **TagTableContract** | Tag-Tables mit DB-Blöcken |
| **TagContract** | Tags mit Name, DataType, Adresse, Comment |
| **BlockContract** | Blocks (OB, FC, FB, DB) mit Typ, Nummer, Networks |
| **TopologyContract** | Topologie (Netzwerktyp, IP-Verbindungen) |
| **AlarmContract** | Alarme mit Severity, Message, Tag-Referenz |
| **DiagnosticsContract** | Diagnose (errors, warnings, stats) |

### Kein Code hier

Diese Dokumentation definiert nur die **Vertragsstruktur und Verantwortlichkeiten**. Die C#-Implementierung folgt in einem separaten Schritt.

---

*Letzte Aktualisierung: 2026-03-29*