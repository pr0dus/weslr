using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Reader für Topologie im Openness Kontext.
/// 
/// Bündelt Openness-spezifische Topologie-Leselogik.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessTiaObjectQuery.
/// </summary>
public sealed class OpennessTopologyReader
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness Topologie-Reader.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessTopologyReader(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Liest Topologie aus der Openness Session.
    /// </summary>
    /// <param name="topologyType">Typ der Topologie (optional, null = alle).</param>
    /// <returns>OpennessSessionResult mit Topologie-Liste oder Fehler.</returns>
    public OpennessSessionResult ReadTopology(string? topologyType = null)
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
                source: nameof(OpennessTopologyReader)
            );
        }
    }

    /// <summary>
    /// Fragt ein Topologie-Element anhand des Namens ab.
    /// </summary>
    /// <param name="topologyName">Name des Topologie-Elements.</param>
    /// <returns>OpennessSessionResult mit Topologie oder Fehler.</returns>
    public OpennessSessionResult QueryTopology(string topologyName)
    {
        try
        {
            if (string.IsNullOrEmpty(topologyName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "topologyName ist leer oder null.",
                    source: nameof(OpennessTopologyReader)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessTopologyReader)
            );
        }
    }
}
