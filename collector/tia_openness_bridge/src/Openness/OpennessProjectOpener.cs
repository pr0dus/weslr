using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Öffnet TIA Openness Projekte.
/// 
/// Bündelt Openness-spezifische Projekt-Öffnungs-Logik.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessSessionFactory.
/// </summary>
public sealed class OpennessProjectOpener
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness Projekt-Öffner.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessProjectOpener(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Öffnet ein TIA Openness Projekt.
    /// </summary>
    /// <param name="projectPath">Pfad zum TIA-Projekt.</param>
    /// <returns>OpennessSessionResult mit Projekt-Referenz oder Fehler.</returns>
    public OpennessSessionResult OpenProject(string projectPath)
    {
        try
        {
            if (string.IsNullOrEmpty(projectPath))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "projectPath ist leer oder null.",
                    source: nameof(OpennessProjectOpener)
                );
            }

            var projectReference = new OpennessProjectReference(projectPath);
            var updatedContext = new OpennessSessionContext(
                sessionHandle: _sessionContext.SessionHandle,
                projectPath: projectPath,
                projectName: projectReference.ProjectName
            );

            return OpennessSessionFactory.CreateSuccess(updatedContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessProjectOpener)
            );
        }
    }

    /// <summary>
    /// Schließt das aktuell geöffnete Projekt.
    /// </summary>
    /// <returns>OpennessSessionResult mit Status Success oder Failure.</returns>
    public OpennessSessionResult CloseProject()
    {
        try
        {
            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessProjectOpener)
            );
        }
    }
}
