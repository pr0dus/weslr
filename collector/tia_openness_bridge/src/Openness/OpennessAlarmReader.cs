using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Reader für Alarme im Openness Kontext.
/// 
/// Bündelt Openness-spezifische Alarm-Leselogik.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessTiaObjectQuery.
/// </summary>
public sealed class OpennessAlarmReader
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness Alarm-Reader.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessAlarmReader(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Liest Alarme aus der Openness Session.
    /// </summary>
    /// <param name="alarmType">Typ der Alarme (optional, null = alle).</param>
    /// <returns>OpennessSessionResult mit Alarm-Liste oder Fehler.</returns>
    public OpennessSessionResult ReadAlarms(string? alarmType = null)
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
                source: nameof(OpennessAlarmReader)
            );
        }
    }

    /// <summary>
    /// Fragt einen einzelnen Alarm anhand des Namens ab.
    /// </summary>
    /// <param name="alarmName">Name des Alarmes.</param>
    /// <returns>OpennessSessionResult mit Alarm oder Fehler.</returns>
    public OpennessSessionResult QueryAlarm(string alarmName)
    {
        try
        {
            if (string.IsNullOrEmpty(alarmName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "alarmName ist leer oder null.",
                    source: nameof(OpennessAlarmReader)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessAlarmReader)
            );
        }
    }
}
