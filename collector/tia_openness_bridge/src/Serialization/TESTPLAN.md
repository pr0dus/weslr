# Test- und Verifikationsplan – Serialization-Bereich

## 1. Ziel der Verifikation

Der Serialization-Bereich soll **JSON-Serialisierung von TIA-Export-Data** garantieren.

**Geprüft wird:**
- JSON-Struktur entspricht `schemas/tia_export.schema.json`
- JSON-Ausgabe ist lesbar und formatiert
- Null-Werte werden korrekt behandelt (nicht serialisiert)
- Leere Listen werden korrekt serialisiert (`[]`)
- Property-Namen sind snake_case (z. B. `ip_address` statt `IpAddress`)
- Keine Datei-Ausgabe (Nur String-Serialisierung)

## 2. Zu prüfende Aspekte

| Aspekt | Warum wichtig | Wie prüfen |
|--------|---------------|------------|
| **JSON-Grundstruktur** | Root-Objekt mit keys `metadata`, `project`, `devices`, `plcs`, `cpus`, `modules`, `tag_tables`, `tags`, `program_blocks`, `topology`, `alarms`, `collector_diagnostics` | JSON-Parsing, keys check |
| **Zentrale Exportbereiche** | Jeder Bereich vorhanden, auch wenn leer | count checks |
| **Leere Listen-Handling** | Leere Listen als `[]` statt `null` serialisiert | count == 0 → `[]` |
| **Feldnamen-Konsistenz** | Alle Property-Namen snake_case (JSON-konform) | Manuell oder Auto-Check |
| **JSON-Lesbarkeit** | Pretty-Print mit 2 spaces indentation | visually inspect |
| **Keine Dateiausgabe** | Serialization serialisiert nur String (kein File-Write) | code review |
| **Null-Handling** | null-Werte werden nicht serialisiert (nicht `"field": null`) | JSON-Parsing, properties check |

## 3. Positive Testfälle

### Testfall 1: Vollständiger MVP-Export

- **Input**: `TiaExportContract` mit allen Pflichtfeldern gefüllt
- **Erwartet**: JSON mit allen Bereichen, pretty-printed, alle Pflichtfelder vorhanden
- **Prüfung**: JSON-Parsing → keys check → count checks

### Testfall 2: Teilweise leere optionale Bereiche

- **Input**: `TiaExportContract` mit einigen optionalen Bereichen leer (z. B. `modules: []`)
- **Erwartet**: JSON mit `modules: []`, nicht `modules: null`
- **Prüfung**: JSON-Parsing → `modules.length === 0`

### Testfall 3: Export mit Diagnostikhinweisen

- **Input**: `TiaExportContract` mit `collector_diagnostics` gefüllt (errors, warnings)
- **Erwartet**: JSON mit `collector_diagnostics.errors` und `collector_diagnostics.warnings` als Arrays
- **Prüfung**: JSON-Parsing → `collector_diagnostics.errors.length > 0`

## 4. Negative bzw. Randfälle

### Randfall 1: Fehlende optionale Bereiche

- **Input**: `TiaExportContract` mit `null` für optionale Bereiche (z. B. `Alarms = null`)
- **Erwartet**: JSON ohne `alarms`-Feld (null → property nicht serialisiert)
- **Prüfung**: JSON-Parsing → `Object.keys(json).includes('alarms') === false`

### Randfall 2: Leere Listen

- **Input**: `TiaExportContract` mit leeren Listen (z. B. `Devices = new DeviceContract[0]`)
- **Erwartet**: JSON mit `devices: []`, nicht `devices: null`
- **Prüfung**: JSON-Parsing → `devices.length === 0`

### Randfall 3: Ungewöhnlich kleine Exportobjekte

- **Input**: `TiaExportContract` mit minimalen Daten (nur Pflichtfelder)
- **Erwartet**: JSON mit min. allen Pflichtfeldern, keine Validierungsfehler
- **Prüfung**: JSON-Parsing → Pflichtfelder check

### Randfall 4: Null-bezogene Risiken

- **Input**: `TiaExportContract` mit `null`-Werten in vermeintlich nicht-null-Felder
- **Erwartet**: Keine Laufzeitfehler (Exception handling oder assert)
- **Prüfung**: Exception-Check, Laufzeitverhalten

## 5. Abgrenzung

### Was **nicht** geprüft wird (in diesem Schritt)

| Bereich | Warum nicht | Erst später |
|---------|-------------|-------------|
| **Schema-Validierung** | Keine JSON-Schema-Validierungs-Logik (nur JSON-Parsing) | JSON Schema Validator |
| **Dateisystem-Tests** | Serialization serialisiert nur String (kein File-Write) | ExportWriter-Tests |
| **Openness-Tests** | Serialization ist unabhängig von TIA Openness | Collector-Tests |
| **Weslr-Tests** | Serialization ist TIA-Export-orientiert, nicht Weslr-orientiert | Normalizer-Tests |
| **Integration-Tests** | Nur Unit-Tests für Serialization (keine End-to-End) | Integration Tests |

## 6. Nächste minimale Umsetzungsschritte

### Erste C#-Testdateien (nach diesem Testplan)

| Testdatei | Zweck |
|-----------|-------|
| **TiaExportJsonSerializerTest.cs** | Unit-Tests für Serialisierung (Input: Contract, Output: JSON-String) |
| **EmptyListHandlingTest.cs** | Prüft leere Listen (`[]` statt `null`) |
| **NullHandlingTest.cs** | Prüft null-Werte (Property nicht serialisiert) |
| **PropertyNamingTest.cs** | Prüft snake_case-Naming (z. B. `ip_address`) |
| **PrettyPrintTest.cs** | Prüft Pretty-Print (indent=2, newlines) |
| **SchemaComplianceTest.cs** | Prüft JSON-Struktur gegen Schema (manuell oder mit JSON.NET) |

### Kein Testcode hier

Dieser Testplan definiert nur die **Test-Ziele und Test-Struktur**. Die C#-Test-Implementierung folgt in einem separaten Schritt.

---

*Letzte Aktualisierung: 2026-03-29*