namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// Geräteinformationen für den TIA-Roh-Export.
/// 
/// Repräsentiert Devices aus dem TIA Portal V20 (PLC, HMI, IO, etc.).
/// Entspricht dem devices-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
/// </summary>
/// <param name="Id">Eindeutige ID des Geräts</param>
/// <param name="Name">Name des Geräts</param>
/// <param name="Type">Gerätetyp (plc_device, hmi_device, drive_device, io_device, network_device)</param>
/// <param name="HardwareVersion">Optional: Hardware-Version</param>
/// <param name="FirmwareVersion">Optional: Firmware-Version</param>
/// <param name="PartNumber">Optional: Teilenummer</param>
/// <param name="OrderNumber">Optional: Bestellnummer</param>
/// <param name="ProductId">Optional: Produkt-ID</param>
public sealed record DeviceContract(
    string Id,
    string Name,
    string Type,
    string? HardwareVersion = null,
    string? FirmwareVersion = null,
    string? PartNumber = null,
    string? OrderNumber = null,
    string? ProductId = null
);