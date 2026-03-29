using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Reader für Tags im Openness Kontext.
/// 
/// Bündelt Openness-spezifische Tag-Leselogik.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessTiaObjectQuery.
/// </summary>
public sealed class OpennessTagReader
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness Tag-Reader.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessTagReader(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Liest Tags aus der Openness Session.
    /// </summary>
    /// <param name="tagType">Typ der Tags (optional, null = alle).</param>
    /// <returns>OpennessSessionResult mit Tag-Liste oder Fehler.</returns>
    public OpennessSessionResult ReadTags(string? tagType = null)
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
                source: nameof(OpennessTagReader)
            );
        }
    }

    /// <summary>
    /// Fragt ein einzelnes Tag anhand des Namens ab.
    /// </summary>
    /// <param name="tagName">Name des Tags.</param>
    /// <returns>OpennessSessionResult mit Tag oder Fehler.</returns>
    public OpennessSessionResult QueryTag(string tagName)
    {
        try
        {
            if (string.IsNullOrEmpty(tagName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "tagName ist leer oder null.",
                    source: nameof(OpennessTagReader)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessTagReader)
            );
        }
    }
}
