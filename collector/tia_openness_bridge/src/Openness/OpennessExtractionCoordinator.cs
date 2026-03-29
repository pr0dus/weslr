using SiemensToWeslr.TiaCollector.Extraction;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Koordiniert TIA Openness Extraction-Schritte.
/// 
/// Bündelt Openness-spezifische Koordinations-Logik.
/// Keine Geschäftslogik, keine Dateilogik.
/// Orientiert sich am Muster der OpennessSessionFactory.
/// </summary>
public sealed class OpennessExtractionCoordinator
{
    private readonly OpennessSessionContext _sessionContext;

    /// <summary>
    /// Initialisiert einen neuen Openness Extraction-Koordinator.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    public OpennessExtractionCoordinator(OpennessSessionContext sessionContext)
    {
        _sessionContext = sessionContext ?? throw new ArgumentNullException(nameof(sessionContext));
    }

    /// <summary>
    /// Startet einen Extraction-Schritt.
    /// </summary>
    /// <param name="stepName">Name des Extraction-Schritts.</param>
    /// <returns>OpennessSessionResult mit Status Success oder Failure.</returns>
    public OpennessSessionResult StartExtractionStep(string stepName)
    {
        try
        {
            if (string.IsNullOrEmpty(stepName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "stepName ist leer oder null.",
                    source: nameof(OpennessExtractionCoordinator)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessExtractionCoordinator)
            );
        }
    }

    /// <summary>
    /// Beendet einen Extraction-Schritt.
    /// </summary>
    /// <param name="stepName">Name des beendeten Extraction-Schritts.</param>
    /// <param name="result">Ergebnis des Schritts.</param>
    /// <returns>OpennessSessionResult mit Status Success oder Failure.</returns>
    public OpennessSessionResult FinishExtractionStep(string stepName, ExtractionResult result)
    {
        try
        {
            if (string.IsNullOrEmpty(stepName))
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "stepName ist leer oder null.",
                    source: nameof(OpennessExtractionCoordinator)
                );
            }

            if (result == null)
            {
                return OpennessSessionFactory.CreateFailure(
                    sessionContext: _sessionContext,
                    error: "result ist null.",
                    source: nameof(OpennessExtractionCoordinator)
                );
            }

            return OpennessSessionFactory.CreateSuccess(_sessionContext);
        }
        catch (Exception ex)
        {
            return OpennessSessionFactory.CreateFailure(
                sessionContext: _sessionContext,
                error: ex.Message,
                source: nameof(OpennessExtractionCoordinator)
            );
        }
    }
}
