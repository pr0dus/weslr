using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Mapping für Modul-Informationen in ModuleContract.
/// 
/// Wandelt eine kleine interne Rohdatenstruktur in ModuleContract um.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class ModuleContractMapper
{
    /// <summary>
    /// Mapping-Methode für ModuleContract.
    /// </summary>
    /// <param name="moduleData">Die Rohdaten für das Modul.</param>
    /// <returns>ModuleContract mit befüllten Feldern.</returns>
    public static ModuleContract Map(ModuleData moduleData)
    {
        return new ModuleContract(
            Id: moduleData.Id,
            PlcId: moduleData.PlcId,
            ModuleType: moduleData.ModuleType,
            Name: moduleData.Name,
            Position: moduleData.Position,
            HardwareVersion: moduleData.HardwareVersion,
            FirmwareVersion: moduleData.FirmwareVersion,
            PartNumber: moduleData.PartNumber,
            OrderNumber: moduleData.OrderNumber
        );
    }
}

/// <summary>
/// Kleines Rohdatenmodell für Modul-Informationen (innerhalb des Mappers).
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
internal sealed record ModuleData(
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