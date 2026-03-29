# Test- und Verifikationsplan – Extraktionsbereich

## 1. Ziel der Verifikation

Der Extraktionsbereich soll **korrekte Engineering-Daten-Extraktion** garantieren.

**Geprüft wird:**
- Extraktionspfad von TIA Openness → Rohdaten ist vollständig
- Projekt, Geräte, PLCs, CPUs, Module, TagTables, Tags, Blocks, Topology, Alarme werden korrekt extrahiert
- Unvollständige Daten werden robust behandelt (Fallback, Warning, Skip)
- Diagnose-Hinweise werden korrekt erzeugt
- Sichere Abbruchbedingungen werden geprüft
- Read-only-Verhalten wird gewährleistet
- Keine Vermischung mit JSON-Serialisierung (nur Datenextraktion)
- Keine Vermischung mit Weslr-Normalisierung

## 2. Zu prüfende Aspekte

| Aspekt | Warum wichtig | Wie prüfen |
|--------|---------------|------------|
| **Extraktionspfad** | Projekt → Rohdaten ist korrekt | Chain-Check |
| **Vollständigkeit** | Alle Zieltypen extrahiert werden | Object-Type-Check |
| **Robustheit** | Unvollständige Daten werden korrekt behandelt | Exception-Check, Warning-Check |
| **Diagnose-Generierung** | Fehler und Warnungen werden erzeugt | Diagnose-Check |
| **Sicherer Abbruch** | Kritische Fehler führen zu Abbruch | Exception-Check |
| **Read-only-Verhalten** | Keine SPS-Steuerung, keine TIA-Änderung | Code-Review |
| **Trennung zu Serialisierung** | Extraktion erzeugt nur Rohdaten, keine JSON | Contract-Check |

## 3. Positive Testfälle

### Testfall 1: Vollständig lesbares Projekt

- **Input**: TIA Projekt (offline) mit allen Objekten lesbar
- **Erwartet**: Projekt-Metadaten, Geräte, PLCs, CPUs, Module, TagTables, Tags, Blocks, Topology, Alarme extrahiert
- **Prüfung**: Chain-Check, Object-Type-Check

### Testfall 2: Teilweise lesbare Engineering-Struktur

- **Input**: TIA Projekt mit einigen unlesbaren Objekten
- **Erwartet**: Lesbare Objekte extrahiert, unlesbare mit Warning/Warning-Skip
- **Prüfung**: Warning-Check, Object-Type-Check

### Testfall 3: Extraktion mit Diagnostikhinweisen

- **Input**: TIA Projekt mit einigen Fehlerfällen
- **Erwartet**: Diagnose-Objekte mit errors und warnings erzeugt
- **Prüfung**: Diagnose-Check

### Testfall 4: Extraktion mit leeren optionalen Bereichen

- **Input**: TIA Projekt ohne bestimmte Objekttypen (z. B. keine Alarme)
- **Erwartet**: Leere Listen (z. B. `alarms = []`) statt `null`
- **Prüfung**: Count-Check (== 0)

### Testfall 5: Vollständiger MVP-Extraktionspfad

- **Input**: TIA Projekt (offline)
- **Erwartet**: Extraktion aller Zieltypen in Rohdatenmodelle
- **Prüfung**: Chain-Check, Object-Type-Check

## 4. Negative bzw. Randfälle

### Randfall 1: Fehlender Projektkontext

- **Input**: Kein geöffnetes TIA Projekt
- **Erwartet**: Sicherer Abbruch mit Fehlermeldung
- **Prüfung**: Exception-Check

### Randfall 2: Unvollständige Geräte- oder PLC-Daten

- **Input**: Geräte oder PLCs mit fehlenden Feldern
- **Erwartet**: Fallback-Werte oder Warning-Skip
- **Prüfung**: Warning-Check, Fallback-Check

### Randfall 3: Fehlende optionale Engineering-Objekte

- **Input**: TIA Projekt ohne Modul-Informationen
- **Erwartet**: Leere Listen (z. B. `modules = []`)
- **Prüfung**: Count-Check (== 0)

### Randfall 4: Leere Teilbereiche

- **Input**: TIA Projekt ohne TagTables
- **Erwartet**: Leere Listen (z. B. `tag_tables = []`)
- **Prüfung**: Count-Check (== 0)

### Randfall 5: Zugriffsfehler auf Teilobjekte

- **Input**: Zugriff auf geschützte TIA-Objekte nicht möglich
- **Erwartet**: Warning, Skip oder Abbruch
- **Prüfung**: Exception-Check, Warning-Check

### Randfall 6: Kontrollierter Abbruch bei kritischen Fehlern

- **Input**: TIA Openness nicht erreichbar
- **Erwartet**: Sicherer Abbruch mit Diagnose
- **Prüfung**: Exception-Check, Diagnose-Check

## 5. Abgrenzung

### Was **nicht** geprüft wird (in diesem Schritt)

| Bereich | Warum nicht | Erst später |
|---------|-------------|-------------|
| **Openness-Implementierung** | Keine C#-Openness-Code in diesem Schritt | C#-Extraction-Tests |
| **JSON-Serialisierung** | Extraktion erzeugt nur Rohdaten, keine JSON | JsonSerializer-Tests |
| **Dateisystem-Tests** | Extraktion arbeitet in Memory, keine Datei-IO | ExportWriter-Tests |
| **Weslr-Tests** | Extraktion ist TIA-relevant, nicht Weslr-relevant | Normalizer-Tests |
| **Integration-Tests** | Nur Unit-Tests für Extraction (keine End-to-End) | Integration Tests |

## 6. Nächste minimale Umsetzungsschritte

### Erste C#-Testdateien (nach diesem Testplan)

| Testdatei | Zweck |
|-----------|-------|
| **ProjectExtractionTest.cs** | Test für Projekt-Extraktion |
| **DeviceExtractionTest.cs** | Test für Device-Extraktion |
| **PlcExtractionTest.cs** | Test für PLC-Extraktion |
| **CpuExtractionTest.cs** | Test für CPU-Extraktion |
| **ModuleExtractionTest.cs** | Test für Module-Extraktion |
| **TagTableExtractionTest.cs** | Test für TagTable-Extraktion |
| **TagExtractionTest.cs** | Test für Tag-Extraktion |
| **BlockExtractionTest.cs** | Test für Block-Extraktion |
| **TopologyExtractionTest.cs** | Test für Topology-Extraktion |
| **AlarmExtractionTest.cs** | Test für Alarm-Extraktion |
| **ExtractionChainTest.cs** | Test für vollständigen Extraktionspfad |
| **EmptyListHandlingTest.cs** | Test für leere Listen |
| **OptionalFieldHandlingTest.cs** | Test für null/leer-Verhalten |

### Kein Testcode hier

Dieser Testplan definiert nur die **Test-Ziele und Test-Struktur**. Die C#-Test-Implementierung folgt in einem separaten Schritt.

---

*Letzte Aktualisierung: 2026-03-29*