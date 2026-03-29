namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// Alarm-Informationen für den TIA-Roh-Export.
/// 
/// Repräsentiert alarmrelevante Engineering-Daten aus dem TIA Portal V20.
/// Entspricht dem alarms-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
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
public sealed record AlarmContract(
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