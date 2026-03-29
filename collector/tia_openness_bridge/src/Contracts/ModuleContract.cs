namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// Modul-Informationen für den TIA-Roh-Export.
/// 
/// Repräsentiert Module (SM, PS, IM, etc.) aus dem TIA Portal V20.
/// Entspricht dem modules-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
/// </summary>
/// <param name="Id">Eindeutige ID des Moduls</param>
/// <param name="PlcId">Referenz zur zugehörigen PLC-ID</param>
/// <param name="ModuleType">Modul-Typ (z. B. "SM 521", "PS 522", "IM 523")</param>
/// <param name="Name">Name des Moduls</param>
/// <param name="Position">Slot-Position im PLC-Rack (0-basiert)</param>
/// <param name="HardwareVersion">Optional: Hardware-Version</param>
/// <param name="FirmwareVersion">Optional: Firmware-Version</param>
/// <param name="PartNumber">Optional: Teilenummer</param>
/// <param name="OrderNumber">Optional: Bestellnummer</param>
public sealed record ModuleContract(
    string Id,
    string PlcId,
    string ModuleType,
    string Name,
    int Position,
    string? HardwareVersion = null,
    string? FirmwareVersion = null,
    string? PartNumber = null,
    string? OrderNumber = null
);