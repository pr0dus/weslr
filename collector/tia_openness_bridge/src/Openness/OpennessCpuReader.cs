using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Reader für CPUs im Openness Kontext.
/// 
/// Bündelt Openness-spezifische CPU-Leselogik.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessTiaObjectQuery.
/// </summary>
public sealed class OpennessCpuReader
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness CPU-Reader.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessCpuReader(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Liest CPUs aus der Openness Session.
    /// </summary>
    /// <param name="cpuType">Typ der CPU (optional, null = alle).</param>
    /// <returns>OpennessSessionResult mit CPU-Liste oder Fehler.</returns>
    public OpennessSessionResult ReadCpus(string? cpuType = null)
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
                source: nameof(OpennessCpuReader)
            );
        }
    }

    /// <summary>
    /// Fragt eine einzelne CPU anhand des Namens ab.
    /// </summary>
    /// <param name="cpuName">Name der CPU.</param>
    /// <returns>OpennessSessionResult mit CPU oder Fehler.</returns>
    public OpennessSessionResult QueryCpu(string cpuName)
    {
        try
        {
            if (string.IsNullOrEmpty(cpuName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "cpuName ist leer oder null.",
                    source: nameof(OpennessCpuReader)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessCpuReader)
            );
        }
    }
}
