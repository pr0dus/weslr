namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// Topologie-Beziehungs-Informationen für den TIA-Roh-Export.
/// 
/// Repräsentiert Topologie-Relationen aus dem TIA Portal V20 (Netzwerkverbindungen).
/// Entspricht dem topology-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
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
public sealed record TopologyRelationContract(
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