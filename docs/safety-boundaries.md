# Sicherheitsgrenzen – Weslr TIA Portal V20 Plugin

## Zweck dieses Dokuments

Dieses Dokument beschreibt die technischen und fachlichen Sicherheitsgrenzen des Plugin-Repositories. Es dient als Referenz für Entwickler, Ingenieure und Sicherheitsbeauftragte, um eindeutig zu klären, was das Plugin kann und was es ausdrücklich **nicht** tut.

## Sicherheitsprinzipien

1. **Read-only by default**: Das Plugin liest nur Engineering-Daten aus dem geöffneten TIA Portal V20-Projekt.
2. **Keine Schreibzugriffe**: Es schreibt **nicht** in das Original-TIA-Projekt, keine Änderungen an Block-Definitionen, Variablen oder Konfigurationen.
3. **Keine SPS-Kommunikation**: Keine Verbindung zur SPS (Online-Read, Online-Write, Monitor, Force, Download, Upload).
4. **Keine Online-Steuerung**: Keine Beeinflussung des laufenden SPS-Programms (Restart, Mode-Wechsel, Signalisierung).
5. **Keine Safety-Bypasses**: Das Plugin berücksichtigt und transformiert keine Safety-Programme (FB/FC/SDB) mit der Absicht, Safety-Bedingungen zu umgehen oder zu manipulieren.
6. **Keine impliziten Aktionen**: Keine automatischen Änderungen, Konvertierungen oder Optimierungen ohne explizite Anforderung.
7. **Keine versteckte Automatisierung**: Jede Transformation (Collector → Raw Export → Normalizer) muss protokolliert und rücksetzbar sein.
8. **Trennungsgebot**: Collector, Normalizer und Analyse sind strikt voneinander getrennt. Keine direkten Verbindungen zwischen SPS-Daten und lateren Laufzeitdaten.

## Betriebsgrenzen

- **Nur Windows**: Das Plugin ist auf Windows-Plattformen ausgelegt (TIA Portal V20 läuft ausschließlich unter Windows).
- **Nur Offline-Modus**: Das Plugin arbeitet mit dem geöffneten TIA-Projekt im Offline-Modus (keine Online-Verbindung nötig).
- **Keine Netzwerkkommunikation**: Keine externen Verbindungen (außer spätere Weslr-Anbindung, die separat spezifiziert wird).
- **Keine Echtzeit**: Keine Echtzeit-Verarbeitung oder -Überwachung.
- **Keine Cloud**: Keine Datenübertragung in die Cloud (alle Verarbeitung lokal auf dem Entwicklungs-PC).

## Daten- und Systemgrenzen

| Bereich | Erlaubt | Verboten |
|---------|---------|----------|
| **Engineering-Daten** | Auslesen von: PLCs, CPUs, Devices, Tags, Alarme, Netzwerkkonfiguration, DB-Inhalten (als Metadaten) | Auslesen von laufenden SPS-Daten (I/O-Status, DB-Inhalte zur Laufzeit) |
| **TIA-Projekt** | Lesender Zugriff auf Projekt-Struktur, Block-Definitionen, Symboltabellen | Schreibender Zugriff auf Projekt-Dateien (.ap20, .ap19, .ap18) |
| **SPS-Kommunikation** | Keine | Online-Read, Online-Write, Force, Restart, Mode-Change, Download, Upload |
| **Safety-Programme** | Lesender Zugriff auf Struktur, **ohne** Transformation der Safety-Logik | Umgehung von Safety-Blöcken, Änderung von Safety-Variablen |
| **Laufzeitdaten** | Keine | Messen, Logging, Aufzeichnen von SPS-Laufzeitverhalten |

## Nicht-Ziele und ausgeschlossene Funktionen

Folgende Funktionen sind **ausdrücklich nicht Teil** des MVP und werden **nicht implementiert**:

- **SPS-Steuerung**: Restart, Stop, Start, Mode-Wechsel, Download/Upload
- **Online-Überwachung**: Monitor, Trace, Force, Variable-Editing
- **Safety-Bypass**: Umgehung von Safety-Blöcken, Veränderung von Safety-variablen, Deaktivierung von Safety-Funktionen
- **Automatische Konvertierung**: Keine automatische Transformation von S7-300 nach S7-1500, keine Block-Konvertierung
- **Versionierung**: Keine Versionierung von TIA-Projekten oder Blocks
- **Code-Generierung**: Keine Erzeugung von S7-Code (STL, LAD, FBD) oder Export in andere Formate
- **Fehlerkorrektur**: Keine automatische Behebung von TIA-Projekt-Fehlern
- **Komprimierung/Optimierung**: Keine Optimierung von DB-Größen, Block-Komprimierung
- **Cloud-Speicherung**: Keine Speicherung von Projektdaten außerhalb des lokalen Systems
- **Echtzeit-Überwachung**: Keine Live-Überwachung von SPS-Daten
- **Netzwerk-Scan**: Keine automatische Erkennung von SPS im Netzwerk (nur geöffnetes Projekt)

## Logging und Nachvollziehbarkeit

### Protokollierungspflichten

- **Export-Timestamp**: Jeder Export muss mit ISO 8601-Zeitstempel versehen sein.
- **Quell-Dateipfad**: Der absolute Pfad zur TIA-Projekt-Datei muss protokolliert werden.
- **Collector-Version**: Die exakte Version des Collectors muss protokolliert werden.
- **Transformations-Log**: Jeder Normalizer-Durchlauf muss protokollieren, welche Objekte transformiert wurden.
- **Fehlerprotokoll**: Alle Fehler und Warnungen müssen in `collector_diagnostics.errors/warnings` aufgenommen werden.
- **Rückverfolgbarkeit**: Jedes Normalized-Graph-Objekt muss Quellen-Herkunft (source_file, source_id) speichern.

### Audit-Trail

- Alle Export-Dateien müssen eindeutige IDs tragen.
- Die Zuordnung zwischen Raw Export und Normalized Graph muss rekonstruierbar sein.
- Jeder Transformations-Schritt muss dokumentiert sein.

## Sichere Fehlerbehandlung

### Kritische Fehler (Abbruch)

- TIA Portal V20 nicht erreichbar → Abbruch
- Projektdaten nicht lesbar → Abbruch
- Schema-Verletzung im Raw Export → Abbruch
- Schema-Verletzung im Normalized Graph → Abbruch
- Speicherprobleme → Abbruch

### Nicht-kritische Fehler (Warnung + Fortsetzung)

- Unbekannte Block-Definitionen → Warnung, Fortsetzung mit Fallback
- Unbekannte Tag-Definitionen → Warnung, Fortsetzung mit Standard-Typ
- Netzwerk-Topologie nicht vollständig → Warnung, Fortsetzung mit Partial-Graph

### Rollback

- Bei kritischem Fehler muss der Export-Status auf "incomplete" gesetzt werden.
- Teilergebnisse werden gelöscht (keine Halb-Exporte).
- Protokolldateien bleiben erhalten (für Debugging).

## Freigaben für spätere Erweiterungen

Folgende Erweiterungen sind **nicht Teil des MVP**, aber **technisch vorgesehen**:

| Bereich | MVP | Spätere Erweiterung |
|---------|-----|---------------------|
| **SPS-Daten** | ❌ | Online-Read (ohne Write), Status-Abfrage |
| **Laufzeit-Daten** | ❌ | Logging von DB-Änderungen (nach explizitem User-Request) |
| **Cloud-Anbindung** | ❌ | Secure HTTPS-Anbindung an Weslr-Backend (nur nach Verschlüsselung) |
| **Netzwerk-Scan** | ❌ | Optionaler "Find PLCs in subnet" (nach Sicherheits-Review) |
| **Versionierung** | ❌ | Projekt-Compare, Diff-View (nach Anforderung) |
| **Online-Change** | ❌ | Online-Edit nach expliziter Freigabe (nach Safety-Review) |
| **Safety-Logik** | ❌ | Safety-Block-Validierung (nur lesend, nach Safety-Review) |

**Hinweis**: Alle Erweiterungen müssen nachträglich in diesem Dokument dokumentiert und freigegeben werden.

---

*Letzte Aktualisierung: 2026-03-29*