using System.Text.Json;
using System.Text.Json.Serialization;

namespace SiemensToWeslr.TiaCollector.Serialization;

/// <summary>
/// JSON-Serialisierer für TIA-Roh-Exports.
/// 
/// Serialisiert den <see cref="TiaExportContract"/> in ein formatiertes JSON-String.
/// Keine Datei-Ausgabe, keine Validierung, keine Geschäftslogik.
/// 
/// Verwendet System.Text.Json für robuste und schnelle Serialisierung.
/// </summary>
public static class TiaExportJsonSerializer
{
    private static readonly JsonSerializerOptions s_jsonOptions = CreateJsonSerializerOptions();

    /// <summary>
    /// Serialisiert einen <see cref="TiaExportContract"/> in einen JSON-String.
    /// </summary>
    /// <param name="export">Der zu serialisierende Export.</param>
    /// <returns>JSON-String (UTF-8, pretty-printed mit 2 spaces indentation).</returns>
    public static string Serialize(TiaExportContract export)
    {
        if (export == null)
            throw new ArgumentNullException(nameof(export));

        return JsonSerializer.Serialize(export, s_jsonOptions);
    }

    /// <summary>
    /// Erstellt die JSON-Serializer-Optionen für den TIA-Export.
    /// </summary>
    /// <returns>JsonSerializerOptions mit snake_case-Naming, null- und leeren Listen-Handling.</returns>
    private static JsonSerializerOptions CreateJsonSerializerOptions()
    {
        var options = new JsonSerializerOptions
        {
            PropertyNamingPolicy = new SnakeCaseNamingPolicy(),
            WriteIndented = true, // pretty-print
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            PropertyNameCaseInsensitive = true
        };

        return options;
    }

    /// <summary>
    /// Snake_Case-Namensrichtlinie für JSON-Property-Namen.
    /// Wandelt C#-PascalCase (z. B. "IpAddress") in snake_case (z. B. "ip_address") um.
    /// </summary>
    private class SnakeCaseNamingPolicy : JsonNamingPolicy
    {
        public override string ConvertName(string name)
        {
            if (string.IsNullOrEmpty(name))
                return name;

            // PascalCase → snake_case
            // Beispiel: "IpAddress" → "ip_address"
            var result = new System.Text.StringBuilder();
            for (int i = 0; i < name.Length; i++)
            {
                if (i > 0 && char.IsUpper(name[i]) && !char.IsUpper(name[i - 1]))
                    result.Append('_');
                result.Append(char.ToLowerInvariant(name[i]));
            }
            return result.ToString();
        }
    }
}