using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Enumeration für TIA-Objekte im Openness Kontext.
/// 
/// Bündelt Openness-spezifische Enumerationslogik.
/// Keine Geschäftslogik, keine Dateilogik.
/// </summary>
public static class OpennessProjectEnumerator
{
    /// <summary>
    /// Enumeriert Projekte in der Openness Session.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    /// <param name="diagnostics">Diagnose-Hinweise (wird erweitert).</param>
    /// <returns>Liste von OpennessProjectReference.</returns>
    public static List<OpennessProjectReference> EnumerateProjects(
        OpennessSessionContext sessionContext,
        List<DiagnosticEntryData> diagnostics
    )
    {
        // Simulation: Leere Liste (echte Enumeration kommt später)
        diagnostics.Add(new DiagnosticEntryData(
            File: "OpennessProjectEnumerator",
            Message: "Projekt-Enumeration noch nicht implementiert"
        ));
        return [];
    }
}