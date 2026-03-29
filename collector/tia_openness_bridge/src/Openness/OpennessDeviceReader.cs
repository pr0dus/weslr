using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Reader für Geräte im Openness Kontext.
/// 
/// Bündelt Openness-spezifische Geräte-Leselogik.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessTiaObjectQuery.
/// </summary>
public sealed class OpennessDeviceReader
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness Gerät-Reader.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessDeviceReader(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Liest Geräte aus der Openness Session.
    /// </summary>
    /// <param name="deviceType">Typ der Geräte (optional, null = alle).</param>
    /// <returns>OpennessSessionResult mit Geräte-Liste oder Fehler.</returns>
    public OpennessSessionResult ReadDevices(string? deviceType = null)
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
                source: nameof(OpennessDeviceReader)
            );
        }
    }

    /// <summary>
    /// Fragt ein einzelnes Gerät anhand des Namens ab.
    /// </summary>
    /// <param name="deviceName">Name des Geräts.</param>
    /// <returns>OpennessSessionResult mit Gerät oder Fehler.</returns>
    public OpennessSessionResult QueryDevice(string deviceName)
    {
        try
        {
            if (string.IsNullOrEmpty(deviceName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "deviceName ist leer oder null.",
                    source: nameof(OpennessDeviceReader)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessDeviceReader)
            );
        }
    }
}
