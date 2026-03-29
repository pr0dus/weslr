namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// CPU-Informationen für den TIA-Roh-Export.
/// 
/// Repräsentiert CPUs aus dem TIA Portal V20 (z. B. "CPU 1511-1 PN").
/// Entspricht dem cpus-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
/// </summary>
/// <param name="Id">Eindeutige ID der CPU</param>
/// <param name="PlcId">Referenz zur zugehörigen PLC-ID</param>
/// <param name="ModuleType">Typbezeichnung der CPU (z. B. "CPU 1511-1 PN")</param>
/// <param name="Name">Name der CPU</param>
/// <param name="Slot">Slot-Nummer (0-basiert)</param>
/// <param name="SerialNumber">Optional: Seriennummer</param>
/// <param name="InterfaceAddresses">Optional: Liste der Interface-Adressen (IP, MAC, etc.)</param>
public sealed record CpuContract(
    string Id,
    string PlcId,
    string ModuleType,
    string Name,
    int Slot,
    string? SerialNumber = null,
    InterfaceAddressContract[]? InterfaceAddresses = null
);

/// <summary>
/// Interface-Adresse einer CPU (IP, MAC, etc.).
/// </summary>
/// <param name="Interface">Interface-Name (interface_0, interface_1, interface_2)</param>
/// <param name="IpAddress">Optional: IP-Adresse</param>
/// <param name="SubnetMask">Optional: Subnetzmaske</param>
/// <param name="PhysicalAddress">Optional: MAC-Adresse</param>
public sealed record InterfaceAddressContract(
    string Interface,
    string? IpAddress = null,
    string? SubnetMask = null,
    string? PhysicalAddress = null
);