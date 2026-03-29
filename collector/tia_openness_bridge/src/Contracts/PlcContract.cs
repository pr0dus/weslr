namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// PLC-Informationen für den TIA-Roh-Export.
/// 
/// Repräsentiert PLCs aus dem TIA Portal V20 (S7-1500, S7-1200, etc.).
/// Entspricht dem plcs-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
/// </summary>
/// <param name="Id">Eindeutige ID der PLC</param>
/// <param name="DeviceId">Referenz zur zugehörigen Device-ID</param>
/// <param name="Name">Name der PLC</param>
/// <param name="Rack">Rack-Nummer (0-basiert)</param>
/// <param name="Slot">Slot-Nummer (0-basiert)</param>
/// <param name="Model">PLC-Modell (z. B. "CPU 1511-1 PN")</param>
/// <param name="IpAddress">Optional: IP-Adresse der PLC</param>
/// <param name="SubnetMask">Optional: Subnetzmaske</param>
/// <param name="Gateway">Optional: Gateway-IP</param>
public sealed record PlcContract(
    string Id,
    string DeviceId,
    string Name,
    int Rack,
    int Slot,
    string Model,
    string? IpAddress = null,
    string? SubnetMask = null,
    string? Gateway = null
);