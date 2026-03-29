namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// Diagnose-Informationen für den TIA-Roh-Export.
/// 
/// Repräsentiert Diagnose-, Warn- und Fehlerhinweise des Collectors.
/// Entspricht dem collector_diagnostics-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
/// </summary>
/// <param name="StartTime">Startzeitpunkt des Exports (ISO 8601)</param>
/// <param name="EndTime">Endzeitpunkt des Exports (ISO 8601)</param>
/// <param name="DurationMs">Dauer in Millisekunden</param>
/// <param name="FilesProcessed">Anzahl verarbeiteter Dateien</param>
/// <param name="ObjectsExtracted">Anzahl extrahierter Objekte</param>
/// <param name="Errors">Liste der Fehler</param>
/// <param name="Warnings">Liste der Warnungen</param>
public sealed record CollectorDiagnosticContract(
    string StartTime,
    string EndTime,
    long DurationMs,
    int FilesProcessed,
    int ObjectsExtracted,
    DiagnosticEntryContract[] Errors,
    DiagnosticEntryContract[] Warnings
);

/// <summary>
/// Ein einzelner Diagnose-Eintrag (Fehler oder Warnung).
/// </summary>
/// <param name="File">Betroffene Datei</param>
/// <param name="Line">Betroffene Zeile (optional)</param>
/// <param name="Message">Meldungstext</param>
public sealed record DiagnosticEntryContract(
    string File,
    int? Line = null,
    string Message = ""
);