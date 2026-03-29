using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Tests.Mapping;

/// <summary>
/// Unit-Tests für TiaExportContractAssembler.
/// 
/// Prüft die Assemblierung von TiaExportContract aus einzelnen Teilen.
/// Keine Openness-Logik, keine Geschäftslogik.
/// </summary>
public class TiaExportContractAssemblerTests
{
    private readonly TiaExportContractAssembler _assembler = new();

    [Fact]
    public void Assemble_WithValidData_ReturnsContract()
    {
        // Arrange
        var metadata = new ExportMetadata(
            version: "1.0.0",
            generator: "TiaBridge",
            generatedAtUtc: new DateTime(2026, 3, 29, 12, 0, 0, DateTimeKind.Utc)
        );

        var project = new ProjectContract(
            id: "test-project-001",
            name: "TestProject",
            type: "AutomationProject",
            path: "/tmp/test-project",
            description: "Test project for automation",
            lastModified: new DateTime(2026, 3, 29, 10, 0, 0, DateTimeKind.Utc),
            author: "TestUser"
        );

        var devices = new[]
        {
            new DeviceContract(
                id: "device-001",
                name: "Device1",
                type: "IO-Device",
                parentId: "project-001"
            )
        };

        var plcs = new PlcContract[0];
        var cpus = new CpuContract[0];
        var modules = new ModuleContract[0];
        var tagTables = new TagTableContract[0];
        var tags = new TagContract[0];
        var programBlocks = new ProgramBlockContract[0];
        var topologyRelations = new TopologyRelationContract[0];
        var alarms = new AlarmContract[0];
        var diagnostics = new DiagnosticContract[0];

        // Act
        var contract = _assembler.Assemble(
            metadata: metadata,
            project: project,
            devices: devices,
            plcs: plcs,
            cpus: cpus,
            modules: modules,
            tagTables: tagTables,
            tags: tags,
            programBlocks: programBlocks,
            topologyRelations: topologyRelations,
            alarms: alarms,
            collectorDiagnostics: diagnostics
        );

        // Assert
        Assert.NotNull(contract);
        Assert.Equal("test-project-001", contract.ProjectId);
        Assert.Equal("TestProject", contract.ProjectName);
        Assert.Equal("TestUser", contract.Project?.Author);
        Assert.Single(contract.Devices);
    }

    [Fact]
    public void Assemble_WithEmptyData_ReturnsContract()
    {
        // Arrange
        var metadata = new ExportMetadata(
            version: "1.0.0",
            generator: "TiaBridge",
            generatedAtUtc: new DateTime(2026, 3, 29, 12, 0, 0, DateTimeKind.Utc)
        );

        // Act
        var contract = _assembler.Assemble(
            metadata: metadata,
            project: null,
            devices: Array.Empty<DeviceContract>(),
            plcs: Array.Empty<PlcContract>(),
            cpus: Array.Empty<CpuContract>(),
            modules: Array.Empty<ModuleContract>(),
            tagTables: Array.Empty<TagTableContract>(),
            tags: Array.Empty<TagContract>(),
            programBlocks: Array.Empty<ProgramBlockContract>(),
            topologyRelations: Array.Empty<TopologyRelationContract>(),
            alarms: Array.Empty<AlarmContract>(),
            collectorDiagnostics: Array.Empty<DiagnosticContract>()
        );

        // Assert
        Assert.NotNull(contract);
        Assert.Null(contract.Project);
        Assert.Empty(contract.Devices);
    }

    [Fact]
    public void Assemble_WithNullMetadata_ThrowsArgumentNullException()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => _assembler.Assemble(
            metadata: null!,
            project: null,
            devices: Array.Empty<DeviceContract>(),
            plcs: Array.Empty<PlcContract>(),
            cpus: Array.Empty<CpuContract>(),
            modules: Array.Empty<ModuleContract>(),
            tagTables: Array.Empty<TagTableContract>(),
            tags: Array.Empty<TagContract>(),
            programBlocks: Array.Empty<ProgramBlockContract>(),
            topologyRelations: Array.Empty<TopologyRelationContract>(),
            alarms: Array.Empty<AlarmContract>(),
            collectorDiagnostics: Array.Empty<DiagnosticContract>()
        ));
    }
}
