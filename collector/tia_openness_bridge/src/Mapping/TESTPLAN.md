# Test- und Verifikationsplan – Mapping-Bereich

## 1. Ziel der Verifikation

Der Mapping-Bereich soll **Korrektheit der Contract-Zuordnung** garantieren.

**Geprüft wird:**
- Jedes Mapping übersetzt Rohdaten korrekt in Contract-Objekte
- Konsistente Feldzuordnung (Rohdaten → Contract-Property)
- Stabile Behandlung optionaler Felder (null → null, leer → leer)
- Stabile ID-Übernahme (Roh-ID → Contract-ID)
- Assembler baut TiaExportContract korrekt aus Teilverträgen
- Keine Vermischung mit JSON-Serialisierung (nur Contract-Bau, keine Serialisierung)

## 2. Zu prüfende Aspekte

| Aspekt | Warum wichtig | Wie prüfen |
|--------|---------------|------------|
| **Einzelmapping-Genauigkeit** | Jedes Mapping-Objekt übersetzt korrekt | Property-Vergleich |
| **Konsistente Feldzuordnung** | Rohdaten-Feld → Contract-Property | Assertion |
| **Stabile Behandlung optionaler Felder** | null/leer bleibt null/leer | null-check |
| **Stabile ID-Übernahme** | Roh-ID → Contract-ID | ID-Check |
| **Vollständiger Assembler** | TiaExportContract korrekt aus Teilverträgen | Contract-Check |
| **Leere Listen-Handling** | Leere Listen → `[]` statt `null` | count-check |
| **Null-bezogene Risiken** | Keine Laufzeitfehler durch null | Exception-Check |

## 3. Positive Testfälle

### Testfall 1: Vollständige Projektinformationen

- **Input**: `ProjectData` mit allen Pflicht- und optionalen Feldern
- **Erwartet**: `ProjectContract` mit allen Feldern korrekt befüllt
- **Prüfung**: Property-Vergleich, null-check

### Testfall 2: Vollständige Geräte-/PLC-/CPU-/Modul-Zuordnung

- **Input**: `DeviceData`, `PlcData`, `CpuData`, `ModuleData` mit allen Feldern
- **Erwartet**: `DeviceContract`, `PlcContract`, `CpuContract`, `ModuleContract` korrekt
- **Prüfung**: Property-Vergleich

### Testfall 3: TagTable- und Tag-Mapping

- **Input**: `TagTableData`, `TagData` mit allen Feldern
- **Erwartet**: `TagTableContract`, `TagContract` korrekt
- **Prüfung**: Property-Vergleich, DB-Block-Check

### Testfall 4: Program-Block-Mapping

- **Input**: `ProgramBlockData` mit allen Feldern (Networks, Interface)
- **Erwartet**: `ProgramBlockContract` korrekt
- **Prüfung**: Property-Vergleich, Networks-Check, Interface-Check

### Testfall 5: Topologie- und Alarm-Mapping

- **Input**: `TopologyRelationData`, `AlarmData` mit allen Feldern
- **Erwartet**: `TopologyRelationContract`, `AlarmContract` korrekt
- **Prüfung**: Property-Vergleich

### Testfall 6: Diagnostikhinweise

- **Input**: `DiagnosticData` mit errors und warnings
- **Erwartet**: `CollectorDiagnosticContract` korrekt
- **Prüfung**: Property-Vergleich, List-check

### Testfall 7: Vollständige Assemblierung eines MVP-Exports

- **Input**: Alle Teilverträge (ProjectContract, DeviceContract[], PlcContract[], etc.)
- **Erwartet**: `TiaExportContract` mit allen Bereichen
- **Prüfung**: Contract-Check, count-checks

## 4. Negative bzw. Randfälle

### Randfall 1: Fehlende optionale Felder

- **Input**: `ProjectData` ohne optionale Felder (z. B. `Path = null`)
- **Erwartet**: `ProjectContract.Path == null`
- **Prüfung**: null-check

### Randfall 2: Leere Listen

- **Input**: `TagTableData.Blocks = null`
- **Erwartet**: `TagTableContract.Blocks == []`
- **Prüfung**: count-check (== 0)

### Randfall 3: Minimal befüllte Rohdatenmodelle

- **Input**: `TagData` mit nur Pflichtfeldern
- **Erwartet**: `TagContract` mit korrekten Pflichtwerten, null für optionale
- **Prüfung**: Property-Vergleich, null-check

### Randfall 4: Unvollständige Objektbezüge

- **Input**: `CpuData` ohne `InterfaceAddresses`
- **Erwartet**: `CpuContract.InterfaceAddresses == []`
- **Prüfung**: count-check (== 0)

### Randfall 5: Null-bezogene Risiken

- **Input**: `PlcData.Gateway = null`, aber nicht alleoptional
- **Erwartet**: Keine Laufzeitfehler (Exception handling)
- **Prüfung**: Exception-Check, Laufzeitverhalten

## 5. Abgrenzung

### Was **nicht** geprüft wird (in diesem Schritt)

| Bereich | Warum nicht | Erst später |
|---------|-------------|-------------|
| **Schema-Validierung** | Keine JSON-Schema-Validierung (nur Contract-Bau) | JSON Schema Validator |
| **JSON-Serialisierung** | Mapping erzeugt nur Contract-Objekte, keine JSON | JsonSerializer-Tests |
| **Dateisystem-Tests** | Mapping arbeitet in Memory, keine Datei-IO | ExportWriter-Tests |
| **Openness-Tests** | Mapping ist unabhängig von TIA Openness | Collector-Tests |
| **Weslr-Tests** | Mapping ist TIA-relevant, nicht Weslr-relevant | Normalizer-Tests |
| **Integration-Tests** | Nur Unit-Tests für Mapping (keine End-to-End) | Integration Tests |

## 6. Nächste minimale Umsetzungsschritte

### Erste C#-Testdateien (nach diesem Testplan)

| Testdatei | Zweck |
|-----------|-------|
| **ProjectContractMapperTest.cs** | Unit-Test für ProjectMapping |
| **DeviceContractMapperTest.cs** | Unit-Test für DeviceMapping |
| **PlcContractMapperTest.cs** | Unit-Test für PlcMapping |
| **CpuContractMapperTest.cs** | Unit-Test für CpuMapping |
| **ModuleContractMapperTest.cs** | Unit-Test für ModuleMapping |
| **TagTableContractMapperTest.cs** | Unit-Test für TagTableMapping |
| **TagContractMapperTest.cs** | Unit-Test für TagMapping |
| **ProgramBlockContractMapperTest.cs** | Unit-Test für BlockMapping |
| **TopologyRelationContractMapperTest.cs** | Unit-Test für TopologyMapping |
| **AlarmContractMapperTest.cs** | Unit-Test für AlarmMapping |
| **CollectorDiagnosticContractMapperTest.cs** | Unit-Test für DiagnoseMapping |
| **TiaExportContractAssemblerTest.cs** | Unit-Test für Assembly |
| **OptionalFieldHandlingTest.cs** | Test für null/leer-Verhalten |
| **IdConsistencyTest.cs** | Test für ID-Übernahme |

### Kein Testcode hier

Dieser Testplan definiert nur die **Test-Ziele und Test-Struktur**. Die C#-Test-Implementierung folgt in einem separaten Schritt.

---

*Letzte Aktualisierung: 2026-03-29*