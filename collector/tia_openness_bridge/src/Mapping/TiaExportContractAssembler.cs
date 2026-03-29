using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Assembler für TiaExportContract aus Teilverträgen.
/// 
/// Baut aus bereits gemappten Teilverträgen einen vollständigen TiaExportContract.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class TiaExportContractAssembler
{
    /// <summary>
    /// Assembler-Methode für TiaExportContract.
    /// </summary>
    /// <param name="metadata">Export-Metadaten</param>
    /// <param name="project">Projektvertrag</param>
    /// <param name="devices">Geräte-Verträge</param>
    /// <param name="plcs">PLC-Verträge</param>
    /// <param name="cpus">CPU-Verträge</param>
    /// <param name="modules">Module-Verträge</param>
    /// <param name="tagTables">Tag-Table-Verträge</param>
    /// <param name="tags">Tag-Verträge</param>
    /// <param name="programBlocks">Programmbaustein-Verträge</param>
    /// <param name="topologyRelations">Topologie-Verträge</param>
    /// <param name="alarms">Alarm-Verträge</param>
    /// <param name="collectorDiagnostics">Diagnose-Verträge</param>
    /// <returns>TiaExportContract mit befüllten Feldern.</returns>
    public static TiaExportContract Assemble(
        ExportMetadataContract metadata,
        ProjectContract project,
        DeviceContract[] devices,
        PlcContract[] plcs,
        CpuContract[] cpus,
        ModuleContract[] modules,
        TagTableContract[] tagTables,
        TagContract[] tags,
        ProgramBlockContract[] programBlocks,
        TopologyRelationContract[] topologyRelations,
        AlarmContract[] alarms,
        CollectorDiagnosticContract collectorDiagnostics
    )
    {
        return new TiaExportContract(
            Metadata: metadata,
            Project: project,
            Devices: devices ?? [],
            Plcs: plcs ?? [],
            Cpus: cpus ?? [],
            Modules: modules ?? [],
            TagTables: tagTables ?? [],
            Tags: tags ?? [],
            ProgramBlocks: programBlocks ?? [],
            Topology: topologyRelations ?? [],
            Alarms: alarms ?? [],
            CollectorDiagnostics: collectorDiagnostics
        );
    }
}