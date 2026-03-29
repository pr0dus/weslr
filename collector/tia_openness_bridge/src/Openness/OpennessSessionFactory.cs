using SiemensToWeslr.TiaCollector.Common;
using SiemensToWeslr.TiaCollector.Openness;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Factory für die Erstellung von Openness Session-Ergebnissen.
/// 
/// Bündelt Openness-spezifische Erstellungslogik.
/// Keine Geschäftslogik, keine Dateilogik.
/// </summary>
public static class OpennessSessionFactory
{
    /// <summary>
    /// Erstellt ein erfolgreiches Openness Session-Ergebnis.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    /// <returns>OpennessSessionResult mit Status Success.</returns>
    public static OpennessSessionResult CreateSuccess(OpennessSessionContext sessionContext)
    {
        return new OpennessSessionResult(sessionContext, status: OpennessSessionStatus.Success);
    }

    /// <summary>
    /// Erstellt ein fehlgeschlagenes Openness Session-Ergebnis.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext (optional).</param>
    /// <param name="error">Fehlermeldung.</param>
    /// <param name="source">Quelle des Fehlers.</param>
    /// <returns>OpennessSessionResult mit Status Failure.</returns>
    public static OpennessSessionResult CreateFailure(OpennessSessionContext? sessionContext, string error, string source)
    {
        var entry = new OpennessDiagnosticsEntry(source, error, "error");
        var diagnostics = new List<DiagnosticEntryData> { entry.ToDiagnosticEntry() };

        return new OpennessSessionResult(
            sessionContext: sessionContext ?? throw new ArgumentNullException(nameof(sessionContext)),
            diagnostics: diagnostics,
            status: OpennessSessionStatus.Failure
        );
    }
}
