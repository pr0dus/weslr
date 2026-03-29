using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Mapping für Geräteinformationen in DeviceContract.
/// 
/// Wandelt eine kleine interne Rohdatenstruktur in DeviceContract um.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class DeviceContractMapper
{
    /// <summary>
    /// Mapping-Methode für DeviceContract.
    /// </summary>
    /// <param name="deviceData">Die Rohdaten für das Gerät.</param>
    /// <returns>DeviceContract mit befüllten Feldern.</returns>
    public static DeviceContract Map(DeviceData deviceData)
    {
        return new DeviceContract(
            Id: deviceData.Id,
            Name: deviceData.Name,
            Type: deviceData.Type,
            HardwareVersion: deviceData.HardwareVersion,
            FirmwareVersion: deviceData.FirmwareVersion,
            PartNumber: deviceData.PartNumber,
            OrderNumber: deviceData.OrderNumber,
            ProductId: deviceData.ProductId
        );
    }
}

/// <summary>
/// Kleines Rohdatenmodell für Geräteinformationen (innerhalb des Mappers).
/// </summary>
/// <param name="Id">Eindeutige ID des Geräts</param>
/// <param name="Name">Name des Geräts</param>
/// <param name="Type">Gerätetyp (plc_device, hmi_device, drive_device, io_device, network_device)</param>
/// <param name="HardwareVersion">Optional: Hardware-Version</param>
/// <param name="FirmwareVersion">Optional: Firmware-Version</param>
/// <param name="PartNumber">Optional: Teilenummer</param>
/// <param name="OrderNumber">Optional: Bestellnummer</param>
/// <param name="ProductId">Optional: Produkt-ID</param>
internal sealed record DeviceData(
    string Id,
    string Name,
    string Type,
    string? HardwareVersion = null,
    string? FirmwareVersion = null,
    string? PartNumber = null,
    string? OrderNumber = null,
    string? ProductId = null
);