namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// Gesamter TIA-Roh-Export als aggregierender Vertragstyp.
/// 
/// Bindet alle Vertragsarten zu einem vollständigen Export zusammen.
/// Entspricht dem gesamten tia_export.schema.json-Schema.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
/// </summary>
/// <param name="Metadata">Export-Metadaten</param>
/// <param name="Project">Projekt-Metadaten</param>
/// <param name="Devices">Liste der Geräte (PLC, HMI, IO, etc.)</param>
/// <param name="Plcs">Liste der PLCs</param>
/// <param name="Cpus">Liste der CPUs</param>
/// <param name="Modules">Liste der Module (SM, PS, IM, etc.)</param>
/// <param name="TagTables">Liste der Tag-Tables</param>
/// <param name="Tags">Liste der Tags</param>
/// <param name="ProgramBlocks">Liste der Programmbausteine (OB, FC, FB, DB)</param>
/// <param name="Topology">Liste der Topologie-Beziehungen</param>
/// <param name="Alarms">Liste der Alarme</param>
/// <param name="CollectorDiagnostics">Liste der Diagnose-Einträge</param>
public sealed record TiaExportContract(
    ExportMetadataContract Metadata,
    ProjectContract Project,
    DeviceContract[] Devices,
    PlcContract[] Plcs,
    CpuContract[] Cpus,
    ModuleContract[] Modules,
    TagTableContract[] TagTables,
    TagContract[] Tags,
    ProgramBlockContract[] ProgramBlocks,
    TopologyRelationContract[] Topology,
    AlarmContract[] Alarms,
    CollectorDiagnosticContract CollectorDiagnostics
);