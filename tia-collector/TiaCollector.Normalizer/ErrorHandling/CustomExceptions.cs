using System;

namespace TiaCollector.Normalizer.ErrorHandling;

/// <summary>
/// Mapping-Fehler: Daten konnten nicht zugeordnet werden
/// </summary>
public class MappingException : Exception
{
    public MappingException(string message) : base(message) { }
    public MappingException(string message, Exception inner) : base(message, inner) { }
}

/// <summary>
/// Normalizer-Fehler: Systemfehler
/// </summary>
public class NormalizerException : Exception
{
    public NormalizerException(string message) : base(message) { }
    public NormalizerException(string message, Exception inner) : base(message, inner) { }
}

/// <summary>
/// Validierungs-Fehler: Input-Daten ungültig
/// </summary>
public class ValidationException : Exception
{
    public ValidationException(string message) : base(message) { }
    public ValidationException(string message, Exception inner) : base(message, inner) { }
}
