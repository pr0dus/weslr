using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Mapping für Topologie-Beziehungs-Informationen in TopologyRelationContract.
/// 
/// Wandelt eine kleine interne Rohdatenstruktur in TopologyRelationContract um.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class TopologyRelationContractMapper
{
    /// <summary>
    /// Mapping-Methode für TopologyRelationContract.
    /// </summary>
    /// <param name="topologyData">Die Rohdaten für die Topologie-Beziehung.</param>
    /// <returns>TopologyRelationContract mit befüllten Feldern.</returns>
    public static TopologyRelationContract Map(TopologyRelationData topologyData)
    {
        return new TopologyRelationContract(
            Id: topologyData.Id,
            SourceId: topologyData.SourceId,
            TargetId: topologyData.TargetId,
            ConnectionType: topologyData.ConnectionType,
            InterfaceSource: topologyData.InterfaceSource,
            InterfaceTarget: topologyData.InterfaceTarget,
            IpAddressSource: topologyData.IpAddressSource,
            IpAddressTarget: topologyData.IpAddressTarget,
            Subnet: topologyData.Subnet
        );
    }
}

/// <summary>
/// Kleines Rohdatenmodell für Topologie-Beziehungs-Informationen (innerhalb des Mappers).
/// </summary>
/// <param name="Id">Eindeutige ID der Relation</param>
/// <param name="SourceId">ID des Quellobjekts (Device, CPU)</param>
/// <param name="TargetId">ID des Zielobjekts (Device, CPU, Netzwerk)</param>
/// <param name="ConnectionType">Verbindungstyp (profinet, ethernet, mpi, dp, modbus, serial, wireless, virtual)</param>
/// <param name="InterfaceSource">Optional: Interface-Name des Quells</param>
/// <param name="InterfaceTarget">Optional: Interface-Name des Ziels</param>
/// <param name="IpAddressSource">Optional: IP-Adresse des Quells</param>
/// <param name="IpAddressTarget">Optional: IP-Adresse des Ziels</param>
/// <param name="Subnet">Optional: Subnetzmaske</param>
internal sealed record TopologyRelationData(
    string Id,
    string SourceId,
    string TargetId,
    string ConnectionType,
    string? InterfaceSource = null,
    string? InterfaceTarget = null,
    string? IpAddressSource = null,
    string? IpAddressTarget = null,
    string? Subnet = null
);