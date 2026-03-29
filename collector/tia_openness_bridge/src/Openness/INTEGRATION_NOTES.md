# Integration Notes – Openness-Bereich

## Aktueller Ablauf

1. **OpennessSessionManager** erstellt `OpennessSessionContext` mit SessionHandle, ProjectPath, ProjectName

2. **OpennessProjectOpener** öffnet das Projekt und aktualisiert den Context

3. **OpennessTiaObjectQuery** fragt TIA-Objekte nach Name oder Typ ab

4. **OpennessExtractionCoordinator** koordiniert einzelne Extraction-Schritte

5. **OpennessExtractionPipeline** führt alle Schritte in Reihenfolge aus

6. **OpennessExtractionPipeline** wird von **ExtractionOrchestrator** aufgerufen:
   - Öffnet Openness Session
   - Führt Pipeline aus
   - Integriert Ergebnisse in Extraktion
   - Gibt `ExtractionAssemblyResult` zurück

## Struktur

- `OpennessSessionManager.cs` → Session-Verwaltung
- `OpennessProjectOpener.cs` → Projekt-Öffnung
- `OpennessTiaObjectQuery.cs` → Objekt-Abfragen
- `OpennessExtractionCoordinator.cs` → Schritt-Koordination
- `OpennessExtractionPipeline.cs` → Pipeline-Ausführung
- `OpennessDeviceReader.cs`, `OpennessPlcReader.cs`, etc. → Reader für spezifische Typen
- `OpennessExtractionPipeline.cs` → integriert in ExtractionOrchestrator

## keine Änderung

- Keine Architekturänderung
- Keine neuen Features
- Bestehende Struktur beibehalten
- Nur Openness-spezifische Logik in `Openness/`-Verzeichnis

---

*Letzte Aktualisierung: 2026-03-29*
