using SiemensToWeslr.TiaCollector.Common;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Diagnose-Eintrag aus dem Openness-Bereich.
/// 
/// Bündelt Openness-spezifische Diagnoseinformationen.
/// Keine Geschäftslogik, keine Dateilogik.
/// </summary>
public sealed class OpennessDiagnosticsEntry
{
    /// <summary>
    /// Initialisiert einen neuen Openness Diagnose-Eintrag.
    /// </summary>
    /// <param name="source">Quelle der Diagnose (z. B. "SessionManager", "ProjectOpener")</param>
    /// <param name="message">Meldungstext</param>
    /// <param name="severity">Schweregrad (info, warning, error)</param>
    /// <param name="context">Optional: Kontextinformationen</param>
    public OpennessDiagnosticsEntry(string source, string message, string severity, string? context = null)
    {
        Source = source;
        Message = message;
        Severity = severity;
        Context = context;
    }

    /// <summary>
    /// Quelle der Diagnose (z. B. "SessionManager", "ProjectOpener").
    /// </summary>
    public string Source { get; }

    /// <summary>
    /// Meldungstext.
    /// </summary>
    public string Message { get; }

    /// <summary>
    /// Schweregrad (info, warning, error).
    /// </summary>
    public string Severity { get; }

    /// <summary>
    /// Kontextinformationen (optional).
    /// </summary>
    public string? Context { get; }

    /// <summary>
    /// Wandelt diesen Eintrag in einen Standard-DiagnosticEntryData um.
    /// </summary>
    public DiagnosticEntryData ToDiagnosticEntry() => new(
        File: Source,
        Message: Message
    );
}
