using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Mapping für CPU-Informationen in CpuContract.
/// 
/// Wandelt eine kleine interne Rohdatenstruktur in CpuContract um.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class CpuContractMapper
{
    /// <summary>
    /// Mapping-Methode für CpuContract.
    /// </summary>
    /// <param name="cpuData">Die Rohdaten für die CPU.</param>
    /// <returns>CpuContract mit befüllten Feldern.</returns>
    public static CpuContract Map(CpuData cpuData)
    {
        return new CpuContract(
            Id: cpuData.Id,
            PlcId: cpuData.PlcId,
            ModuleType: cpuData.ModuleType,
            Name: cpuData.Name,
            Slot: cpuData.Slot,
            SerialNumber: cpuData.SerialNumber,
            InterfaceAddresses: cpuData.InterfaceAddresses?.ToArray()
        );
    }
}

/// <summary>
/// Kleines Rohdatenmodell für CPU-Informationen (innerhalb des Mappers).
/// </summary>
/// <param name="Id">Eindeutige ID der CPU</param>
/// <param name="PlcId">Referenz zur zugehörigen PLC-ID</param>
/// <param name="ModuleType">Typbezeichnung der CPU (z. B. "CPU 1511-1 PN")</param>
/// <param name="Name">Name der CPU</param>
/// <param name="Slot">Slot-Nummer (0-basiert)</param>
/// <param name="SerialNumber">Optional: Seriennummer</param>
/// <param name="InterfaceAddresses">Optional: Liste der Interface-Adressen</param>
internal sealed record CpuData(
    string Id,
    string PlcId,
    string ModuleType,
    string Name,
    int Slot,
    string? SerialNumber = null,
    InterfaceAddressData[]? InterfaceAddresses = null
);

/// <summary>
/// Kleines Rohdatenmodell für Interface-Adressen (innerhalb des Mappers).
/// </summary>
/// <param name="Interface">Interface-Name (interface_0, interface_1, interface_2)</param>
/// <param name="IpAddress">Optional: IP-Adresse</param>
/// <param name="SubnetMask">Optional: Subnetzmaske</param>
/// <param name="PhysicalAddress">Optional: MAC-Adresse</param>
internal sealed record InterfaceAddressData(
    string Interface,
    string? IpAddress = null,
    string? SubnetMask = null,
    string? PhysicalAddress = null
);