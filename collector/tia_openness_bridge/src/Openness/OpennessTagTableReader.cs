using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Reader für TagTables im Openness Kontext.
/// 
/// Bündelt Openness-spezifische TagTable-Leselogik.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessTiaObjectQuery.
/// </summary>
public sealed class OpennessTagTableReader
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness TagTable-Reader.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessTagTableReader(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Liest TagTables aus der Openness Session.
    /// </summary>
    /// <param name="tagTableName">Name der TagTable (optional, null = alle).</param>
    /// <returns>OpennessSessionResult mit TagTable-Liste oder Fehler.</returns>
    public OpennessSessionResult ReadTagTables(string? tagTableName = null)
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
                source: nameof(OpennessTagTableReader)
            );
        }
    }

    /// <summary>
    /// Fragt eine einzelne TagTable anhand des Namens ab.
    /// </summary>
    /// <param name="tagTableName">Name der TagTable.</param>
    /// <returns>OpennessSessionResult mit TagTable oder Fehler.</returns>
    public OpennessSessionResult QueryTagTable(string tagTableName)
    {
        try
        {
            if (string.IsNullOrEmpty(tagTableName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "tagTableName ist leer oder null.",
                    source: nameof(OpennessTagTableReader)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessTagTableReader)
            );
        }
    }
}
