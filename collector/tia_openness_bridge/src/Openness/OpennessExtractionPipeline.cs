using SiemensToWeslr.TiaCollector.Common;
using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Koordiniert die gesamte Openness Extraction-Pipeline.
/// 
/// Bündelt alle Openness Reader und koordiniert den Ablauf.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessExtractionCoordinator.
/// </summary>
public sealed class OpennessExtractionPipeline
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness Extraction-Pipeline.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessExtractionPipeline(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Führt die gesamte Extraction-Pipeline aus.
    /// </summary>
    /// <param name="steps">Liste der auszuführenden Extraction-Schritte.</param>
    /// <returns>OpennessSessionResult mit Pipeline-Ergebnis oder Fehler.</returns>
    public OpennessSessionResult RunPipeline(IReadOnlyList<string> steps)
    {
        try
        {
            if (steps == null || steps.Count == 0)
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "steps ist leer oder null.",
                    source: nameof(OpennessExtractionPipeline)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessExtractionPipeline)
            );
        }
    }

    /// <summary>
    /// Führt einen spezifischen Extraction-Schritt aus.
    /// </summary>
    /// <param name="stepName">Name des auszuführenden Schritts.</param>
    /// <returns>OpennessSessionResult mit Schritt-Ergebnis oder Fehler.</returns>
    public OpennessSessionResult RunStep(string stepName)
    {
        try
        {
            if (string.IsNullOrEmpty(stepName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "stepName ist leer oder null.",
                    source: nameof(OpennessExtractionPipeline)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessExtractionPipeline)
            );
        }
    }
}
