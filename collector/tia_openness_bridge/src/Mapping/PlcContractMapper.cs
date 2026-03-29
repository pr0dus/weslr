using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Mapping für PLC-Informationen in PlcContract.
/// 
/// Wandelt eine kleine interne Rohdatenstruktur in PlcContract um.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class PlcContractMapper
{
    /// <summary>
    /// Mapping-Methode für PlcContract.
    /// </summary>
    /// <param name="plcData">Die Rohdaten für die PLC.</param>
    /// <returns>PlcContract mit befüllten Feldern.</returns>
    public static PlcContract Map(PlcData plcData)
    {
        return new PlcContract(
            Id: plcData.Id,
            DeviceId: plcData.DeviceId,
            Name: plcData.Name,
            Rack: plcData.Rack,
            Slot: plcData.Slot,
            Model: plcData.Model,
            IpAddress: plcData.IpAddress,
            SubnetMask: plcData.SubnetMask,
            Gateway: plcData.Gateway
        );
    }
}

/// <summary>
/// Kleines Rohdatenmodell für PLC-Informationen (innerhalb des Mappers).
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
internal sealed record PlcData(
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