using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Kontext für die TIA Openness Session.
/// 
/// Bündelt Openness-spezifische Kontextinformationen.
/// Keine Geschäftslogik, keine Dateilogik.
/// </summary>
public sealed class OpennessSessionContext
{
    /// <summary>
    /// Initialisiert einen neuen Openness Session-Kontext.
    /// </summary>
    /// <param name="sessionHandle">Handle der TIA Openness Session</param>
    /// <param name="projectPath">Pfad zum geöffneten TIA-Projekt</param>
    /// <param name="projectName">Name des geöffneten TIA-Projekts</param>
    public OpennessSessionContext(string sessionHandle, string projectPath, string projectName)
    {
        SessionHandle = sessionHandle;
        ProjectPath = projectPath;
        ProjectName = projectName;
    }

    /// <summary>
    /// Handle der TIA Openness Session.
    /// </summary>
    public string SessionHandle { get; }

    /// <summary>
    /// Pfad zum geöffneten TIA-Projekt.
    /// </summary>
    public string ProjectPath { get; }

    /// <summary>
    /// Name des geöffneten TIA-Projekts.
    /// </summary>
    public string ProjectName { get; }
}