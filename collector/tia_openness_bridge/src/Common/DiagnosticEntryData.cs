namespace SiemensToWeslr.TiaCollector.Common;

/// <summary>
/// Eintrag für Diagnose-, Warn- oder Fehlerhinweise.
/// 
/// Bündelt Informationen über ein Problem oder eine Warnung.
/// Keine Geschäftslogik, keine Dateilogik.
/// </summary>
public sealed class DiagnosticEntryData
{
    /// <summary>
    /// Initialisiert einen neuen Diagnose-Eintrag.
    /// </summary>
    /// <param name="file">Betroffene Datei</param>
    /// <param name="line">Betroffene Zeile (optional)</param>
    /// <param name="message">Meldungstext</param>
    public DiagnosticEntryData(string file, int? line, string message)
    {
        File = file;
        Line = line;
        Message = message;
    }

    /// <summary>
    /// Initialisiert einen neuen Diagnose-Eintrag ohne Zeilenangabe.
    /// </summary>
    /// <param name="file">Betroffene Datei</param>
    /// <param name="message">Meldungstext</param>
    public DiagnosticEntryData(string file, string message)
        : this(file, null, message)
    {
    }

    /// <summary>
    /// Betroffene Datei.
    /// </summary>
    public string File { get; }

    /// <summary>
    /// Betroffene Zeile (optional).
    /// </summary>
    public int? Line { get; }

    /// <summary>
    /// Meldungstext.
    /// </summary>
    public string Message { get; }
}
