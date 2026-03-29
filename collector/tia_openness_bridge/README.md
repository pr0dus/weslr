# TIA Openness Bridge – Windows-seitiger Collector (MVP)

## 1. Ziel des Collectors

Der **TIA Openness Bridge Collector** ist der Windows-seitige Extraktpunkt für Rohdaten aus Siemens TIA Portal V20-Projekten.

**Aufgabe:** Lese Engineering-Daten aus dem geöffneten TIA Portal V20-Projekt (offline) und exportiere sie in das definierte Rohformat (`schemas/tia_export.schema.json`).

**Was er liefert:** Ein JSON-Export mit allen extrahierten Engineering-Objekten (PLCs, CPUs, Devices, Tags, Alarme, Topologie) plus Diagnoseinformationen.

## 2. Abgrenzung

### Was der Collector **nicht** tut

- **Keine Weslr-Analyse:** Keine Transformation in Weslr-Entity-Graphen (dieser Schritt gehört zum Normalizer)
- **Keine PLC-Steuerung:** Keine SPS-Kommunikation (keine Online-Read/Write, keine Steuerungsoperationen)
- **Keine TIA-Projektänderung:** Keine Schreiboperationen auf das ursprüngliche TIA-Projekt (read-only)
- **Keine Laufzeit-Daten:** Keine Überwachung von SPS-Statusdaten (keine I/O-Logik, keine Task-Zyklen)
- **Keine Safety-Logik-Transformation:** Keine Verarbeitung von Safety-Blöcken mit dem Ziel, Safety-Bedingungen zu ändern

### Abgrenzung zum Rest des Plugins

| Komponente | Verantwortung | Collector-Aufgabe |
|------------|---------------|-------------------|
| **Collector** | Lesender Zugriff auf TIA-Objekte | Extrahiert Rohdaten |
| **Normalizer** | Transformation | Wandelt Rohdaten in Normalized Graph |
| **Analyzer** | (später) | Führt Failure-Investigation durch (in Weslr) |

## 3. Eingaben und Voraussetzungen

### Voraussetzungen

- **Betriebssystem:** Windows (TIA Portal V20 läuft nur unter Windows)
- **TIA Portal Version:** V20 (oder abwärtskompatibel)
- **Openness-Kontext:** Der TIA-Collector nutzt TIA Openness API (Siemens .NET-Bibliothek)
- **Arbeitsmodus:** Read-only (keine Änderungen am Projekt)

### Voraussetzungen für den Aufruf

- TIA Portal V20 muss gestartet sein (oder als Hintergrundprozess laufen)
- Das gewünschte Projekt muss geöffnet sein (oder über Openness geöffnet werden)
- Ausreichende Berechtigungen zum Lesen der Projekt-Dateien

## 4. Ausgaben

### Format

- **Schema:** `schemas/tia_export.schema.json`
- **Inhalt:** Read-only Engineering-Daten (Raw Export)
- **Felder:** Projekte, Devices, PLCs, CPUs, Module, TagTables, Tags, Program Blocks, Topology, Alarme
- **Diagnose:** errors, warnings, start_time, end_time, duration_ms, files_processed, objects_extracted

### Ausgabedatei

- **Name:** `tia_export.json` ( oder timestamp-basiert)
- **Ort:** Lokales Verzeichnis (z. B. `output/` oder `temp/`)
- **Format:** JSON (utf-8, nicht komprimiert)
- **Version:** `collector_version`, `tia_portal_version`, `format_version`

## 5. Geplanter Extraktionsumfang im MVP

### Project

- id, name, type, path, description, last_modified, author

### Devices

- id, name, type (plc_device, hmi_device, drive_device, io_device, network_device), hardware_version, firmware_version, part_number, order_number, product_id

### PLCs

- id, device_id, name, rack, slot, model, ip_address, subnet_mask, gateway

### CPUs

- id, plc_id, module_type, name, slot, serial_number, interface_addresses

### Modules (SM, PS, IM, etc.)

- id, plc_id, module_type, name, position, hardware_version, firmware_version, part_number, order_number

### TagTables

- id, name, plc_id, blocks (mit db_number, name, size, organization_block_type)

### Tags

- id, name (vollqualifizierter Name), data_type, address, plc_id, comment, initial_value, read_write, direct_access

### Program Blocks (OB, FC, FB, DB)

- id, name, type, plc_id, number, networks, interface (input, output, in_out, temp, static, constant), comment

### Topology/Network Relations

- id, source_id, target_id, connection_type (profinet, ethernet, mpi, dp, modbus, serial, wireless, virtual), interface_source, interface_target, ip_source, ip_target, subnet

### Alarmrelevante Engineering-Daten

- id, name, plc_id, type (standard_alarm, extended_alarm, message_class_2/3), severity, message_text, acknowledge_required, archive_required, enabled, tag_reference, delay, deadband, low_limit, high_limit

## 6. Fehlerbehandlung

### Kritische Fehler (Abbruch)

- TIA Portal nicht erreichbar → **Abbruch**
- Projekt nicht geöffnet / nicht lesbar → **Abbruch**
- Openness API nicht verfügbar → **Abbruch**
- Speicherprobleme → **Abbruch**

### Nicht-kritische Fehler (Warnung + Fortsetzung)

- Unbekannte Block-Definition → **Warnung**, Fortsetzung mit Fallback
- Unbekannte Tag-Definition → **Warnung**, Fortsetzung mit Standard-Typ
- Netzwerk-Topologie unvollständig → **Warnung**, Fortsetzung mit Partial-Graph

### Sichere Abbruchbedingungen

- Bei kritischem Fehler: Export-Status auf "incomplete" setzen
- Teilergebnisse löschen (keine Halb-Exporte)
- Protokolldateien bleiben erhalten (für Debugging)

### Keine impliziten Aktionen

- Keine automatischen Konvertierungen ohne User-Request
- Keine automatischen Optimierungen
- Keine Stilllegung von Features ohne Logging

## 7. Logging und Nachvollziehbarkeit

### Protokollierungspflichten

- **Export-Timestamp:** ISO 8601-Zeitstempel (start_time, end_time, duration_ms)
- **Quell-Dateipfad:** Absoluter Pfad zur TIA-Projekt-Datei
- **Collector-Version:** Exakte Version des Collectors (build number)
- **Projekt-Metadaten:** name, path, last_modified, author
- **Extraktionsstatistik:** files_processed, objects_extracted
- **Fehlerprotokoll:** Alle errors und warnings in `collector_diagnostics`
- **Rückverfolgbarkeit:** source_file, source_id für jedes extrahierte Objekt

### Warum Nachvollziehbarkeit wichtig ist

- Fehlerursachenanalyse (Wo ist das Problem aufgetreten?)
- Audit-Trail (Wer hat wann was extrahiert?)
- Regelmäßige Exporte vergleichbar machen (Versionierung)
- Integration mit Weslr (source_file, source_id in Entities)

## 8. Nächste Implementierungsschritte

### C#-Artefakte (später)

| Komponente | Zweck | Dateiname (Vorschlag) |
|------------|-------|------------------------|
| **TiaCollectorMain** | Haupt-Programmklasse | `TiaCollectorMain.cs` |
| **TiaProjectReader** | Openness-Zugriff auf Projekt | `TiaProjectReader.cs` |
| **EntityExtractors** | Extraktions-Logik pro Typ | `ProjectExtractor.cs`, `DeviceExtractor.cs`, `PlcExtractor.cs`, `CpuExtractor.cs`, `TagExtractor.cs`, etc. |
| **ExportWriter** | Schreiben von `tia_export.json` | `ExportWriter.cs` |
| **DiagnosticsCollector** | Logging und Diagnose | `DiagnosticsCollector.cs` |

### Minimaler MVP-Umfang

1. TIA-Verbindung herstellen (Openness)
2. Projekt-Struktur auslesen (Project, Devices)
3. PLCs und CPUs extrahieren
4. Tags und TagTables extrahieren
5. Topology-Relationen extrahieren
6. Export in `tia_export.schema.json` schreiben
7. Diagnose-Informationen erfassen

### Kein C#-Code hier

Dieses README beschreibt nur den **Zweck und die Anforderungen**. Die C#-Implementierung folgt in einem separaten Schritt.

---

*Letzte Aktualisierung: 2026-03-29*