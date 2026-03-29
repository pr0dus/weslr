using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Mapping für Alarm-Informationen in AlarmContract.
/// 
/// Wandelt eine kleine interne Rohdatenstruktur in AlarmContract um.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class AlarmContractMapper
{
    /// <summary>
    /// Mapping-Methode für AlarmContract.
    /// </summary>
    /// <param name="alarmData">Die Rohdaten für den Alarm.</param>
    /// <returns>AlarmContract mit befüllten Feldern.</returns>
    public static AlarmContract Map(AlarmData alarmData)
    {
        return new AlarmContract(
            Id: alarmData.Id,
            Name: alarmData.Name,
            PlcId: alarmData.PlcId,
            Type: alarmData.Type,
            Severity: alarmData.Severity,
            MessageText: alarmData.MessageText,
            AcknowledgeRequired: alarmData.AcknowledgeRequired,
            ArchiveRequired: alarmData.ArchiveRequired,
            Enabled: alarmData.Enabled,
            TagReference: alarmData.TagReference,
            Delay: alarmData.Delay,
            Deadband: alarmData.Deadband,
            LowLimit: alarmData.LowLimit,
            HighLimit: alarmData.HighLimit
        );
    }
}

/// <summary>
/// Kleines Rohdatenmodell für Alarm-Informationen (innerhalb des Mappers).
/// </summary>
/// <param name="Id">Eindeutige ID des Alarms</param>
/// <param name="Name">Name des Alarms</param>
/// <param name="PlcId">Referenz zur zugehörigen PLC-ID</param>
/// <param name="Type">Alarm-Typ (standard_alarm, extended_alarm, message_class_2, message_class_3)</param>
/// <param name="Severity">Schweregrad (fatal, critical, major, minor, warning)</param>
/// <param name="MessageText">Alarm-Text</param>
/// <param name="AcknowledgeRequired">Optional: Acknowledgment erforderlich</param>
/// <param name="ArchiveRequired">Optional: Archivierung erforderlich</param>
/// <param name="Enabled">Optional: Alarm aktiviert</param>
/// <param name="TagReference">Optional: Tag-Referenz (auslösendes Tag)</param>
/// <param name="Delay">Optional: Alarmverzögerung in Sekunden</param>
/// <param name="Deadband">Optional: Totzone</param>
/// <param name="LowLimit">Optional: Untergrenze</param>
/// <param name="HighLimit">Optional: Obergrenze</param>
internal sealed record AlarmData(
    string Id,
    string Name,
    string PlcId,
    string Type,
    string Severity,
    string MessageText,
    bool? AcknowledgeRequired = null,
    bool? ArchiveRequired = null,
    bool? Enabled = null,
    string? TagReference = null,
    double? Delay = null,
    double? Deadband = null,
    double? LowLimit = null,
    double? HighLimit = null
);