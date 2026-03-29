using SiemensToWeslr.TiaCollector.Contracts;
using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Tests.Extraction;

/// <summary>
/// Unit-Tests für ExtractionOrchestrator mit Openness Integration.
/// 
/// Prüft die Integration von OpennessExtractionPipeline in den Extraction-Orchestrator.
/// Keine Openness-Logik, keine Geschäftslogik.
/// </summary>
public class ExtractionOrchestratorTests
{
    private readonly ExtractionOrchestrator _orchestrator = new();

    [Fact]
    public void ExtractAll_WithValidContext_ReturnsSuccess()
    {
        // Arrange
        var projectContract = new ProjectContract(
            Id: "test-project-001",
            Name: "TestProject",
            Type: "AutomationProject",
            Path: "/tmp/test-project",
            Description: "Test project",
            LastModified: "2026-03-29T10:00:00Z",
            Author: "TestUser"
        );

        var context = new ExtractionContext(
            exportId: "test-001",
            exportTimestampUtc: "2026-03-29T13:00:00Z",
            collectorVersion: "1.0.0",
            sourceSystem: "windows",
            projectInfo: projectContract
        );

        // Act
        var result = _orchestrator.ExtractAll(context);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(ProjectExtractionStatus.Success, result.Status);
        Assert.NotNull(result.FullExport);
    }

    [Fact]
    public void ExtractAll_WithNullContext_ThrowsArgumentNullException()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => _orchestrator.ExtractAll(null!));
    }

    [Fact]
    public void ExtractAll_WithNullProjectInfo_ReturnsSuccess()
    {
        // Arrange
        var context = new ExtractionContext(
            exportId: "test-001",
            exportTimestampUtc: "2026-03-29T13:00:00Z",
            collectorVersion: "1.0.0",
            sourceSystem: "windows",
            projectInfo: null
        );

        // Act
        var result = _orchestrator.ExtractAll(context);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(ProjectExtractionStatus.Success, result.Status);
    }
}
