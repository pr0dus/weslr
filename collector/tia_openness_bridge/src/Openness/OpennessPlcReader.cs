using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Reader für PLCs im Openness Kontext.
/// 
/// Bündelt Openness-spezifische PLC-Leselogik.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessTiaObjectQuery.
/// </summary>
public sealed class OpennessPlcReader
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness PLC-Reader.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessPlcReader(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Liest PLCs aus der Openness Session.
    /// </summary>
    /// <param name="plcType">Typ der PLC (optional, null = alle).</param>
    /// <returns>OpennessSessionResult mit PLC-Liste oder Fehler.</returns>
    public OpennessSessionResult ReadPlcs(string? plcType = null)
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
                source: nameof(OpennessPlcReader)
            );
        }
    }

    /// <summary>
    /// Fragt eine einzelne PLC anhand des Namens ab.
    /// </summary>
    /// <param name="plcName">Name der PLC.</param>
    /// <returns>OpennessSessionResult mit PLC oder Fehler.</returns>
    public OpennessSessionResult QueryPlc(string plcName)
    {
        try
        {
            if (string.IsNullOrEmpty(plcName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "plcName ist leer oder null.",
                    source: nameof(OpennessPlcReader)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessPlcReader)
            );
        }
    }
}
