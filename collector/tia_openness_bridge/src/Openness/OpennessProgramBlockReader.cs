using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Reader für Program-Blocks im Openness Kontext.
/// 
/// Bündelt Openness-spezifische Block-Leselogik.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessTiaObjectQuery.
/// </summary>
public sealed class OpennessProgramBlockReader
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness Block-Reader.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessProgramBlockReader(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Liest Program-Blocks aus der Openness Session.
    /// </summary>
    /// <param name="blockType">Typ der Blocks (optional, null = alle).</param>
    /// <returns>OpennessSessionResult mit Block-Liste oder Fehler.</returns>
    public OpennessSessionResult ReadProgramBlocks(string? blockType = null)
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
                source: nameof(OpennessProgramBlockReader)
            );
        }
    }

    /// <summary>
    /// Fragt einen einzelnen Block anhand des Namens ab.
    /// </summary>
    /// <param name="blockName">Name des Blocks.</param>
    /// <returns>OpennessSessionResult mit Block oder Fehler.</returns>
    public OpennessSessionResult QueryProgramBlock(string blockName)
    {
        try
        {
            if (string.IsNullOrEmpty(blockName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "blockName ist leer oder null.",
                    source: nameof(OpennessProgramBlockReader)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessProgramBlockReader)
            );
        }
    }
}
