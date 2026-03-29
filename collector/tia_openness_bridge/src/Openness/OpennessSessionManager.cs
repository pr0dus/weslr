using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Manager für TIA Openness Sessions.
/// 
/// Bündelt Openness-spezifische Session-Verwaltung.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessSessionFactory.
/// </summary>
public sealed class OpennessSessionManager
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness Session-Manager.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessSessionManager(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Öffnet eine neue Openness Session.
    /// </summary>
    /// <returns>OpennessSessionResult mit Status Success oder Failure.</returns>
    public OpennessSessionResult OpenSession()
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
                source: nameof(OpennessSessionManager)
            );
        }
    }

    /// <summary>
    /// Schließt die aktuelle Openness Session.
    /// </summary>
    /// <returns>OpennessSessionResult mit Status Success oder Failure.</returns>
    public OpennessSessionResult CloseSession()
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
                source: nameof(OpennessSessionManager)
            );
        }
    }

    /// <summary>
    /// Prüft den aktuellen Status der Openness Session.
    /// </summary>
    /// <returns>True, wenn eine gültige Session besteht.</returns>
    public bool IsOpen => !string.IsNullOrEmpty(_sessionContext.SessionHandle);
}
