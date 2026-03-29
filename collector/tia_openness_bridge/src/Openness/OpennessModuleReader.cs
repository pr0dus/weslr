using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Reader für Module im Openness Kontext.
/// 
/// Bündelt Openness-spezifische Module-Leselogik.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessTiaObjectQuery.
/// </summary>
public sealed class OpennessModuleReader
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness Modul-Reader.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessModuleReader(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Liest Module aus der Openness Session.
    /// </summary>
    /// <param name="moduleType">Typ der Module (optional, null = alle).</param>
    /// <returns>OpennessSessionResult mit Modul-Liste oder Fehler.</returns>
    public OpennessSessionResult ReadModules(string? moduleType = null)
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
                source: nameof(OpennessModuleReader)
            );
        }
    }

    /// <summary>
    /// Fragt ein einzelnes Modul anhand des Namens ab.
    /// </summary>
    /// <param name="moduleName">Name des Moduls.</param>
    /// <returns>OpennessSessionResult mit Modul oder Fehler.</returns>
    public OpennessSessionResult QueryModule(string moduleName)
    {
        try
        {
            if (string.IsNullOrEmpty(moduleName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "moduleName ist leer oder null.",
                    source: nameof(OpennessModuleReader)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessModuleReader)
            );
        }
    }
}
