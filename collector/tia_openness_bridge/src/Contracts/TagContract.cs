namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// Tag-Informationen für den TIA-Roh-Export.
/// 
/// Repräsentiert einzelne Tags aus dem TIA Portal V20 (z. B. "Global-Variables.MachineSpeed").
/// Entspricht dem tags-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
/// </summary>
/// <param name="Id">Eindeutige ID des Tags</param>
/// <param name="Name">Vollqualifizierter Tag-Name (z. B. "DB42.TemperaturePV")</param>
/// <param name="DataType">Datentyp (BOOL, BYTE, WORD, DWORD, INT, DINT, REAL, STRING, DATE, TIME, etc.)</param>
/// <param name="Address">Speicheradresse (z. B. "DB42.DBW0", "I0.0", "Q4.3")</param>
/// <param name="PlcId">Referenz zur zugehörigen PLC-ID</param>
/// <param name="Comment">Optional: Kommentar zum Tag</param>
/// <param name="InitialValue">Optional: Anfangswert</param>
/// <param name="ReadWrite">Optional: Schreibzugriff erlaubt</param>
/// <param name="DirectAccess">Optional: Direktzugriff</param>
public sealed record TagContract(
    string Id,
    string Name,
    string DataType,
    string Address,
    string PlcId,
    string? Comment = null,
    string? InitialValue = null,
    bool? ReadWrite = null,
    bool? DirectAccess = null
);