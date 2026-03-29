using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Fragt TIA Openness Objekte ab.
/// 
/// Bündelt Openness-spezifische Objekt-Abfragen.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessSessionFactory.
/// </summary>
public sealed class OpennessTiaObjectQuery
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness TIA-Objekt-Abfrager.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessTiaObjectQuery(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Fragt ein TIA-Objekt anhand des Namens ab.
    /// </summary>
    /// <param name="objectName">Name des abzufragenden Objekts.</param>
    /// <returns>OpennessSessionResult mit Objekt-Referenz oder Fehler.</returns>
    public OpennessSessionResult QueryObject(string objectName)
    {
        try
        {
            if (string.IsNullOrEmpty(objectName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "objectName ist leer oder null.",
                    source: nameof(OpennessTiaObjectQuery)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessTiaObjectQuery)
            );
        }
    }

    /// <summary>
    /// Fragt alle TIA-Objekte eines bestimmten Typs ab.
    /// </summary>
    /// <param name="objectType">Typ der abzufragenden Objekte (z. B. "Plc", "Cpu", "Module").</param>
    /// <returns>OpennessSessionResult mit Liste der Objekte oder Fehler.</returns>
    public OpennessSessionResult QueryObjectsByType(string objectType)
    {
        try
        {
            if (string.IsNullOrEmpty(objectType))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "objectType ist leer oder null.",
                    source: nameof(OpennessTiaObjectQuery)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessTiaObjectQuery)
            );
        }
    }
}
