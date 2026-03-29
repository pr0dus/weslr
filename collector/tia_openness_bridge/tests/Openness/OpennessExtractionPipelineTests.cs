using SiemensToWeslr.TiaCollector.Extraction;
using SiemensToWeslr.TiaCollector.Openness;

namespace SiemensToWeslr.TiaCollector.Tests.Openness;

/// <summary>
/// Unit-Tests für OpennessExtractionPipeline.
/// 
/// Prüft die Integration der Openness-Pipeline in die Extraction-Pipeline.
/// Keine Openness-Logik, keine Geschäftslogik.
/// </summary>
public class OpennessExtractionPipelineTests
{
    [Fact]
    public void RunPipeline_WithValidSteps_ReturnsSuccess()
    {
        // Arrange
        var sessionContext = new OpennessSessionContext(
            sessionHandle: "test-session-001",
            projectPath: "/tmp/test-project",
            projectName: "TestProject"
        );
        var pipeline = new OpennessExtractionPipeline(sessionContext);

        // Act
        var result = pipeline.RunPipeline(new List<string> { "Step1", "Step2" });

        // Assert
        Assert.True(result.IsSuccess);
        Assert.NotNull(result.SessionContext);
    }

    [Fact]
    public void RunPipeline_WithEmptySteps_ReturnsFailure()
    {
        // Arrange
        var sessionContext = new OpennessSessionContext(
            sessionHandle: "test-session-001",
            projectPath: "/tmp/test-project",
            projectName: "TestProject"
        );
        var pipeline = new OpennessExtractionPipeline(sessionContext);

        // Act
        var result = pipeline.RunPipeline(new List<string>());

        // Assert
        Assert.False(result.IsSuccess);
        Assert.Single(result.Diagnostics);
    }

    [Fact]
    public void RunPipeline_WithNullSteps_ReturnsFailure()
    {
        // Arrange
        var sessionContext = new OpennessSessionContext(
            sessionHandle: "test-session-001",
            projectPath: "/tmp/test-project",
            projectName: "TestProject"
        );
        var pipeline = new OpennessExtractionPipeline(sessionContext);

        // Act
        var result = pipeline.RunPipeline(null);

        // Assert
        Assert.False(result.IsSuccess);
        Assert.Single(result.Diagnostics);
    }

    [Fact]
    public void RunStep_WithValidStepName_ReturnsSuccess()
    {
        // Arrange
        var sessionContext = new OpennessSessionContext(
            sessionHandle: "test-session-001",
            projectPath: "/tmp/test-project",
            projectName: "TestProject"
        );
        var pipeline = new OpennessExtractionPipeline(sessionContext);

        // Act
        var result = pipeline.RunStep("TestStep");

        // Assert
        Assert.True(result.IsSuccess);
    }

    [Fact]
    public void RunStep_WithEmptyStepName_ReturnsFailure()
    {
        // Arrange
        var sessionContext = new OpennessSessionContext(
            sessionHandle: "test-session-001",
            projectPath: "/tmp/test-project",
            projectName: "TestProject"
        );
        var pipeline = new OpennessExtractionPipeline(sessionContext);

        // Act
        var result = pipeline.RunStep("");

        // Assert
        Assert.False(result.IsSuccess);
        Assert.Single(result.Diagnostics);
    }

    [Fact]
    public void RunStep_WithNullStepName_ReturnsFailure()
    {
        // Arrange
        var sessionContext = new OpennessSessionContext(
            sessionHandle: "test-session-001",
            projectPath: "/tmp/test-project",
            projectName: "TestProject"
        );
        var pipeline = new OpennessExtractionPipeline(sessionContext);

        // Act
        var result = pipeline.RunStep(null);

        // Assert
        Assert.False(result.IsSuccess);
        Assert.Single(result.Diagnostics);
    }
}
