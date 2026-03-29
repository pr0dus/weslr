namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Referenz auf ein TIA-Projekt in der Openness Session.
/// 
/// Bündelt Projekt-Identifikationsdaten für spätere Abfragen.
/// Keine Geschäftslogik, keine Dateilogik.
/// </summary>
public sealed class OpennessProjectReference
{
    /// <summary>
    /// Initialisiert eine neue Openness Project-Referenz.
    /// </summary>
    /// <param name="projectId">ID des TIA-Projekts</param>
    /// <param name="projectName">Name des TIA-Projekts</param>
    /// <param name="projectPath">Pfad zum TIA-Projekt</param>
    public OpennessProjectReference(string projectId, string projectName, string projectPath)
    {
        ProjectId = projectId;
        ProjectName = projectName;
        ProjectPath = projectPath;
    }

    /// <summary>
    /// ID des TIA-Projekts.
    /// </summary>
    public string ProjectId { get; }

    /// <summary>
    /// Name des TIA-Projekts.
    /// </summary>
    public string ProjectName { get; }

    /// <summary>
    /// Pfad zum TIA-Projekt.
    /// </summary>
    public string ProjectPath { get; }
}