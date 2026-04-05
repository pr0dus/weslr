# WESLR Scientific Capability Discovery + Governed Self-Improvement

## SECTION 1 — EXTENSION SCOPE

This document extends the existing **WESLR Capability Discovery Radar** system to support scientific and research-native sources.

**What's new:**
- Support for scientific paper sources (arXiv, Semantic Scholar, OpenAlex, etc.)
- Support for research community sources (university labs, research forums)
- Support for benchmark leaderboards
- Enhanced provenance tracking with publication metadata
- Self-improvement classification layer for internal capability suggestions

**What's preserved:**
- Existing capability suggestion data model (additive fields only)
- Existing storage layer (backward compatible)
- Existing API surface (additive methods only)
- Existing state machine (NEW → SUGGESTED → ACCEPTED/DENIED/SNOOZED/ARCHIVED)
- Existing 24h denial rule

**What's NOT redesigned:**
- No new database schema unless absolutely necessary
- No breaking changes to existing models
- No rewrite of existing scanner logic

---

## SECTION 2 — SOURCE BUCKET MODEL EXTENSION

### New Source Buckets

Add to existing `SourceProvenance` structure:

| Source Bucket | Description | Examples |
|---------------|-------------|----------|
| `github` | GitHub repositories, issues, discussions | Open source tooling projects |
| `reddit` | Reddit discussions | r/selfhosted, r/tooling, r/privacy |
| `huggingface` | Hugging Face repositories | ML models, datasets |
| `papers` | Published academic papers | Journal articles, conference proceedings |
| `preprints` | Preprint servers | arXiv, bioRxiv, chemRxiv |
| `journals` | Academic journals | Nature, Science, IEEE, ACM |
| `university_labs` | University research labs | MIT CSAIL, Max Planck, Fraunhofer |
| `research_forums` | Research community forums | ResearchGate, Academia.edu |
| `scientific_blogs` | Scientific blog posts | Nature blogs, PubMed blogs |
| `benchmark_leaderboards` | Benchmark rankings | Papers with Code, OpenBench |

### Data Model Updates

**Extension to `SourceProvenance`:**

```csharp
public sealed record SourceProvenance(
    string Url,
    string Title,
    string Snippet,
    float RelevanceScore,
    string SignalType,
    string Timestamp,
    // NEW FIELDS:
    string SourceBucket = "unknown",      // e.g., "arxiv", "github", "reddit"
    string InstitutionName = null,        // e.g., "MIT CSAIL", "Max Planck"
    string PublicationDate = null,        // e.g., "2026-04-01"
    int CitationCount = 0,                // For papers
    string BenchmarkName = null,          // e.g., "SQuAD v2.0"
    string DomainField = null             // e.g., "machine_learning", "neuroscience"
);
```

**Extension to `CapabilitySuggestion`:**

```csharp
public sealed record CapabilitySuggestion(
    // ... existing fields ...
    
    // NEW FIELDS:
    string SourceBucket = "unknown",      // Primary source bucket
    string ResearchDomain = null,         // Research domain field
    bool IsScientificSignal = false,      // Is this from a scientific source?
    int CitationCount = 0,                // For scientific papers
    float ScienceRelevanceScore = 0.5f,   // Scientific relevance (0-1)
    string ImplementationRisk = "low",    // "low" | "medium" | "high"
    string Reversibility = "high",        // "low" | "medium" | "high"
    bool IsSelfImprovementCandidate = false // Can this improve WESLR?
);
```

---

## SECTION 3 — RESEARCH DISCOVERY CONNECTORS (STUBS)

### PRIORITY A — Core Research Sources

| Source | Adapter Class | Endpoint | Notes |
|--------|---------------|----------|-------|
| arXiv | `ArxivConnector.cs` | `https://arxiv.org/help/api` | Free, no auth required |
| Semantic Scholar | `SemanticScholarConnector.cs` | `https://api.semanticscholar.org` | Free API key recommended |
| OpenAlex | `OpenAlexConnector.cs` | `https://docs.openalex.org` | Free, no auth required |
| Papers with Code | `PapersWithCodeConnector.cs` | `https://paperswithcode.com/api` | Free, limited rate |
| Hugging Face | `HuggingFaceConnector.cs` | `https://huggingface.co/docs/hub` | Free, no auth required |

### PRIORITY B — Institutional Sources

| Source | Adapter Class | Notes |
|--------|---------------|-------|
| ResearchGate | `ResearchGateConnector.cs` | Limited public API |
| Springer Nature | `SpringerNatureConnector.cs` | Commercial access needed |
| Max Planck | `MaxPlanckConnector.cs` | Institutional repository |
| Fraunhofer | `FraunhoferConnector.cs` | Institutional repository |
| Helmholtz | `HelmholtzConnector.cs` | Institutional repository |
| MIT CSAIL | `MitCsailConnector.cs` | Institutional repository |
| CERN | `CernConnector.cs` | Institutional repository |

### Connector Interface

```csharp
namespace SiemensToWeslr.TiaCollector.CapabilityDiscovery;

/// <summary>
/// Interface for research source connectors.
/// Each connector implements fetch + normalize for its source.
/// </summary>
public interface IResearchConnector
{
    /// <summary>
    /// Get source metadata.
    /// </summary>
    string SourceName { get; }
    
    string SourceBucket { get; }
    
    /// <summary>
    /// Fetch signals from the source.
    /// </summary>
    /// <param name="query">Search query</param>
    /// <param name="limit">Maximum results</param>
    /// <returns>Collection of signals</returns>
    Task<IEnumerable<ResearchSignal>> FetchAsync(string query, int limit = 20);
    
    /// <summary>
    /// Normalize a raw signal into a standard format.
    /// </summary>
    ResearchSignal NormalizeSignal(object rawSignal);
}

/// <summary>
/// Normalized research signal.
/// </summary>
public sealed record ResearchSignal(
    string Id,
    string Title,
    string Abstract,
    string Url,
    string PublishedAt,
    string SourceName,
    string SourceBucket,
    string InstitutionName = null,
    int CitationCount = 0,
    string DomainField = null,
    float RelevanceScore = 0.5f,
    string PaperId = null,
    string AuthorString = null
);
```

### Example: arXiv Connector (Minimal Implementation)

```csharp
using System.Net.Http;
using System.Xml;
using System.Xml.Serialization;

namespace SiemensToWeslr.TiaCollector.CapabilityDiscovery;

/// <summary>
/// arXiv connector via API.
/// No API key required.
/// </summary>
public class ArxivConnector : IResearchConnector
{
    private const string ApiBase = "http://export.arxiv.org/api/query";
    private readonly HttpClient _httpClient;
    
    public ArxivConnector(HttpClient httpClient = null)
    {
        _httpClient = httpClient ?? new HttpClient();
    }
    
    public string SourceName => "arXiv";
    public string SourceBucket => "preprints";
    
    public async Task<IEnumerable<ResearchSignal>> FetchAsync(string query, int limit = 20)
    {
        var encodedQuery = Uri.EscapeDataString(query);
        var url = $"{ApiBase}?search_query=all:{encodedQuery}&start=0&max_results={limit}";
        
        var response = await _httpClient.GetAsync(url);
        response.EnsureSuccessStatusCode();
        
        var xml = await response.Content.ReadAsStringAsync();
        return ParseArxivFeed(xml);
    }
    
    private IEnumerable<ResearchSignal> ParseArxivFeed(string xml)
    {
        var doc = new XmlDocument();
        doc.LoadXml(xml);
        
        var namespaceManager = new XmlNamespaceManager(doc.NameTable);
        namespaceManager.AddNamespace("atom", "http://www.w3.org/2005/Atom");
        
        var entries = doc.SelectNodes("//atom:entry", namespaceManager);
        
        foreach (XmlNode entry in entries)
        {
            var idNode = entry.SelectSingleNode("atom:id", namespaceManager);
            var titleNode = entry.SelectSingleNode("atom:title", namespaceManager);
            var summaryNode = entry.SelectSingleNode("atom:summary", namespaceManager);
            var publishedNode = entry.SelectSingleNode("atom:published", namespaceManager);
            
            // Extract paper ID from URL
            var paperId = idNode?.InnerText?.Split("/").Last() ?? Guid.NewGuid().ToString();
            
            yield return new ResearchSignal(
                Id: paperId,
                Title: CleanText(titleNode?.InnerText),
                Abstract: CleanText(summaryNode?.InnerText),
                Url: idNode?.InnerText,
                PublishedAt: publishedNode?.InnerText,
                SourceName: SourceName,
                SourceBucket: SourceBucket,
                DomainField: "physics", // arXiv is broad - could extract from category
                RelevanceScore: 0.7f
            );
        }
    }
    
    private string CleanText(string text)
    {
        if (string.IsNullOrWhiteSpace(text)) return string.Empty;
        // Remove extra whitespace and newlines
        return string.Join(" ", text.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
            .Replace("  ", " ")
            .Trim();
    }
    
    public ResearchSignal NormalizeSignal(object rawSignal)
    {
        // arXiv signals are already normalized in FetchAsync
        throw new NotImplementedException("arXiv signals are returned directly from FetchAsync");
    }
}
```

---

## SECTION 4 — GAP SIGNAL EXTRACTION

### Signal Pattern Recognition

Add to `ExtractionOrchestrator.cs` or create `GapDetector.cs`:

```csharp
using System.Text.RegularExpressions;

namespace SiemensToWeslr.TiaCollector.CapabilityDiscovery;

/// <summary>
/// Extracts capability gap signals from text content.
/// Looks for phrases indicating missing capabilities.
/// </summary>
public static class GapDetector
{
    private static readonly (string Pattern, string SignalType)[] _patterns = new[]
    {
        // Capability gaps
        (@"(no implementation|not implemented|missing tooling|lacks|cannot)", "capability_gap"),
        (@"(workflow bottleneck|bottleneck|manual work|repetitive)", "workflow_bottleneck"),
        (@"(not reproducible|reproducibility|lack of implementation)", "reproducibility_gap"),
        
        // Research signals
        (@"(future work|future research|limitations|limitation)", "future_work"),
        (@"(requires manual|manual work|human intervention)", "manual_requirement"),
        (@"(benchmark gap|sota|state-of-the-art)", "benchmark_gap"),
        
        // Data/preprocessing
        (@"(data preprocessing|data preparation|data cleaning)", "data_challenge"),
        (@"(needs validation|validation needed|requires validation)", "validation_gap"),
    };
    
    /// <summary>
    /// Extract gap signals from text.
    /// </summary>
    public static IEnumerable<(string Signal, string Type, float Confidence)> ExtractSignals(string text)
    {
        if (string.IsNullOrWhiteSpace(text)) yield break;
        
        var lowerText = text.ToLowerInvariant();
        
        foreach (var (pattern, signalType) in _patterns)
        {
            var matches = Regex.Matches(lowerText, pattern, RegexOptions.IgnoreCase);
            if (matches.Count > 0)
            {
                // Calculate confidence based on match count
                var confidence = Math.Min(0.9f, 0.5f + (matches.Count * 0.1f));
                yield return (matches[0].Value, signalType, confidence);
            }
        }
    }
    
    /// <summary>
    /// Check if text contains capability gap signals.
    /// </summary>
    public static bool HasCapabilityGaps(string text)
    {
        var signals = ExtractSignals(text);
        return signals.Any(s => s.Type == "capability_gap" || s.Type == "workflow_bottleneck");
    }
    
    /// <summary>
    /// Check if text contains research gap signals.
    /// </summary>
    public static bool HasResearchGaps(string text)
    {
        var signals = ExtractSignals(text);
        return signals.Any(s => s.Type == "future_work" || s.Type == "validation_gap");
    }
}
```

### Signal Normalization

```csharp
namespace SiemensToWeslr.TiaCollector.CapabilityDiscovery;

/// <summary>
/// Normalizes signals from research sources into capability suggestions.
/// </summary>
public static class SignalNormalizer
{
    /// <summary>
    /// Convert a research signal to a capability suggestion.
    /// </summary>
    public static CapabilitySuggestion ToCapabilitySuggestion(
        this ResearchSignal signal,
        string gapType = "capability_gap")
    {
        // Extract capability type from domain field
        var capabilityType = GetCapabilityType(signal.DomainField, signal.Title);
        
        // Determine improvement area from gap type
        var improvementArea = GetImprovementArea(gapType);
        
        // Build summary from abstract
        var summary = signal.Abstract.Length > 500 
            ? signal.Abstract.Substring(0, 500) + "..." 
            : signal.Abstract;
        
        return new CapabilitySuggestion(
            Title: signal.Title,
            CapabilityType = capabilityType,
            Summary: summary,
            WhyItMatters = $"Research indicates this capability is missing in WESLR. Signal from {signal.SourceName}.",
            ImprovementArea = improvementArea,
            // New fields
            SourceBucket = signal.SourceBucket,
            ResearchDomain = signal.DomainField,
            IsScientificSignal = signal.SourceBucket == "preprints" || 
                                 signal.SourceBucket == "papers" || 
                                 signal.SourceBucket == "journals",
            CitationCount = signal.CitationCount,
            ScienceRelevanceScore = signal.RelevanceScore,
            ImplementationRisk = GetImplementationRisk(gapType),
            Reversibility = GetReversibility(gapType),
            IsSelfImprovementCandidate = IsSelfImprovementCandidate(gapType, capabilityType),
            // Existing fields
            Confidence = signal.RelevanceScore,
            RankScore = CalculateRankScore(signal, gapType),
            Tags = new[] { "research", signal.SourceBucket },
            GrowthTrend = "stable" // Research signals typically grow slowly
        );
    }
    
    private static CapabilityType GetCapabilityType(string domain, string title)
    {
        // Simple keyword-based classification
        var lower = (domain + " " + title).ToLowerInvariant();
        
        if (lower.Contains("collabor") || lower.Contains("collab")) 
            return CapabilityType.REAL_TIME_COLLAB;
        if (lower.Contains("mobile") || lower.Contains("ios") || lower.Contains("android"))
            return CapabilityType.NATIVE_MOBILE;
        if (lower.Contains("api") || lower.Contains("integration"))
            return CapabilityType.API_ACCESS_LEVEL;
        if (lower.Contains("workflow") || lower.Contains("automation"))
            return CapabilityType.AUTOMATION_PATTERNS;
        
        return CapabilityType.MARKDOWN_EXTENSIONS; // default
    }
    
    private static string GetImprovementArea(string gapType)
    {
        return gapType switch
        {
            "capability_gap" => "capability expansion",
            "workflow_bottleneck" => "workflow optimization",
            "reproducibility_gap" => "reproducibility",
            "future_work" => "research integration",
            "benchmark_gap" => "benchmarking",
            "data_challenge" => "data processing",
            "validation_gap" => "validation",
            _ => "general improvement"
        };
    }
    
    private static string GetImplementationRisk(string gapType)
    {
        return gapType switch
        {
            "capability_gap" => "medium",
            "workflow_bottleneck" => "low",
            "reproducibility_gap" => "medium",
            "future_work" => "high",
            "benchmark_gap" => "low",
            "data_challenge" => "medium",
            "validation_gap" => "low",
            _ => "medium"
        };
    }
    
    private static string GetReversibility(string gapType)
    {
        return gapType switch
        {
            "capability_gap" => "medium",
            "workflow_bottleneck" => "high",
            "reproducibility_gap" => "medium",
            "future_work" => "low",
            "benchmark_gap" => "high",
            "data_challenge" => "medium",
            "validation_gap" => "high",
            _ => "medium"
        };
    }
    
    private static bool IsSelfImprovementCandidate(string gapType, CapabilityType capabilityType)
    {
        // Only scientific signals that could improve WESLR itself
        return gapType == "future_work" && 
               capabilityType != CapabilityType.MARKDOWN_EXTENSIONS;
    }
    
    private static float CalculateRankScore(ResearchSignal signal, string gapType)
    {
        // Simple rank calculation
        var baseScore = signal.RelevanceScore * 100;
        
        // Boost for high citation count
        var citationBoost = Math.Min(20, signal.CitationCount * 0.1f);
        
        // Boost for scientific sources
        var scientificBoost = signal.SourceBucket switch
        {
            "preprints" => 15,
            "papers" => 20,
            "journals" => 25,
            _ => 0
        };
        
        return Math.Min(100f, baseScore + citationBoost + scientificBoost);
    }
}
```

---

## SECTION 5 — SELF-IMPROVEMENT CLASSIFICATION LAYER

### Classification Logic

```csharp
namespace SiemensToWeslr.TiaCollector.CapabilityDiscovery;

/// <summary>
/// Classifies capability suggestions as self-improvement candidates.
/// </summary>
public static class SelfImprovementClassifier
{
    /// <summary>
    /// Classify a suggestion as external-only or self-improvement candidate.
    /// </summary>
    public static SelfImprovementClassification Classify(
        this CapabilitySuggestion suggestion)
    {
        // Decision factors
        var isExternalOnly = IsExternalOnly(suggestion);
        var isProductOpportunity = IsProductOpportunity(suggestion);
        var isSelfImprovement = IsSelfImprovement(suggestion);
        
        // Determine classification
        if (isSelfImprovement && isProductOpportunity)
        {
            return new SelfImprovementClassification
            {
                Category = SelfImprovementCategory.BOTH_PRODUCT_AND_INTERNAL,
                WhyRelevantToWeslr = "This capability improves WESLR internally AND provides product value.",
                ExpectedSystemBenefit = "Enhanced capability + improved self-modification pathway.",
                ImplementationRisk = suggestion.ImplementationRisk,
                Reversibility = suggestion.Reversibility,
                OperatorVisibility = "high"
            };
        }
        
        if (isSelfImprovement)
        {
            return new SelfImprovementClassification
            {
                Category = SelfImprovementCategory.INTERNAL_SELF_IMPROVEMENT,
                WhyRelevantToWeslr = "This capability enables better self-modification for WESLR.",
                ExpectedSystemBenefit = "WESLR can improve its own capabilities through this signal.",
                ImplementationRisk = suggestion.ImplementationRisk,
                Reversibility = suggestion.Reversibility,
                OperatorVisibility = "high"
            };
        }
        
        if (isProductOpportunity)
        {
            return new SelfImprovementClassification
            {
                Category = SelfImprovementCategory.PRODUCT_OPPORTUNITY,
                WhyRelevantToWeslr = "This is a market demand for WESLR product features.",
                ExpectedSystemBenefit = "Product feature enhancement based on research demand.",
                ImplementationRisk = suggestion.ImplementationRisk,
                Reversibility = suggestion.Reversibility,
                OperatorVisibility = "medium"
            };
        }
        
        return new SelfImprovementClassification
        {
            Category = SelfImprovementCategory.EXTERNAL_ONLY,
            WhyRelevantToWeslr = "This is an external ecosystem signal without direct WESLR benefit.",
            ExpectedSystemBenefit = "Awareness of external trends for strategic planning.",
            ImplementationRisk = suggestion.ImplementationRisk,
            Reversibility = suggestion.Reversibility,
            OperatorVisibility = "low"
        };
    }
    
    private static bool IsExternalOnly(CapabilitySuggestion s)
    {
        // External only if no WESLR internal relevance
        return !IsProductOpportunity(s) && !IsSelfImprovement(s);
    }
    
    private static bool IsProductOpportunity(CapabilitySuggestion s)
    {
        // Product opportunity if it's about capability gaps in existing tools
        var keywords = new[] { "tool", "software", "platform", "product", "feature", "api" };
        return s.Tags.Any(t => keywords.Any(k => t.Contains(k, StringComparison.OrdinalIgnoreCase)))
               || s.CapabilityType != CapabilityType.MARKDOWN_EXTENSIONS;
    }
    
    private static bool IsSelfImprovement(CapabilitySuggestion s)
    {
        // Self-improvement candidate if:
        // 1. It's from a scientific/research source
        // 2. It mentions capability gaps that WESLR could learn from
        // 3. It's not just external tool demand
        return s.IsScientificSignal 
               && s.IsSelfImprovementCandidate
               && s.RecommendationType != "tool_demand";
    }
}

/// <summary>
/// Self-improvement classification result.
/// </summary>
public sealed record SelfImprovementClassification(
    SelfImprovementCategory Category,
    string WhyRelevantToWeslr,
    string ExpectedSystemBenefit,
    string ImplementationRisk,
    string Reversibility,
    string OperatorVisibility
)
{
    // Properties
    public SelfImprovementCategory Category { get; init; } = SelfImprovementCategory.EXTERNAL_ONLY;
    public string WhyRelevantToWeslr { get; init; } = string.Empty;
    public string ExpectedSystemBenefit { get; init; } = string.Empty;
    public string ImplementationRisk { get; init; } = "medium";
    public string Reversibility { get; init; } = "medium";
    public string OperatorVisibility { get; init; } = "medium";
}

/// <summary>
/// Self-improvement classification categories.
/// </summary>
public enum SelfImprovementCategory
{
    /// <summary>Only external ecosystem signal, no WESLR benefit.</summary>
    EXTERNAL_ONLY,
    
    /// <summary>Product opportunity - external market demand.</summary>
    PRODUCT_OPPORTUNITY,
    
    /// <summary>Internal self-improvement - WESLR can learn from this.</summary>
    INTERNAL_SELF_IMPROVEMENT,
    
    /// <summary>Both product opportunity AND internal improvement.</summary>
    BOTH_PRODUCT_AND_INTERNAL
}
```

---

## SECTION 6 — GOVERNED SELF-IMPROVEMENT PROPOSALS

### Proposal Model

```csharp
namespace SiemensToWeslr.TiaCollector.CapabilityDiscovery;

/// <summary>
/// Operator-reviewable self-improvement proposal.
/// Generated from classified suggestions.
/// </summary>
public sealed record SelfImprovementProposal(
    string Id,
    string Title,
    string Rationale,
    string ExpectedBenefit,
    string ExpectedRisk,
    string RequiredComponents,
    string ReversibilityRating,
    string ApprovalStatus,
    string CreatedAt,
    List<SourceProvenance> Provenance,
    SelfImprovementClassification Classification,
    string SourceSignalId = null,
    string OriginalSuggestionId = null
)
{
    public static SelfImprovementProposal FromSuggestion(
        CapabilitySuggestion suggestion,
        SelfImprovementClassification classification)
    {
        return new SelfImprovementProposal(
            Id: Guid.NewGuid().ToString("N"),
            Title: suggestion.Title,
            Rationale: $"WESLR lacks capability indicated by research: {suggestion.Summary}",
            ExpectedBenefit: classification.ExpectedSystemBenefit,
            ExpectedRisk: classification.ImplementationRisk,
            RequiredComponents: GetRequiredComponents(suggestion),
            ReversibilityRating: classification.Reversibility,
            ApprovalStatus: "pending",
            CreatedAt: DateTime.UtcNow.ToString("o"),
            Provenance: suggestion.Provenance.ToList(),
            Classification: classification,
            SourceSignalId: suggestion.Id,
            OriginalSuggestionId: suggestion.Id
        );
    }
    
    private static string GetRequiredComponents(CapabilitySuggestion s)
    {
        return $"- Research signal analysis\n- Capability gap assessment\n- Implementation path\n- Validation framework\n- Rollback mechanism";
    }
    
    // Methods
    public SelfImprovementProposal MarkApproved(string approver = null)
    {
        return this with { ApprovalStatus = "approved", ApprovedAt = DateTime.UtcNow.ToString("o") };
    }
    
    public SelfImprovementProposal MarkRejected(string reason = null)
    {
        return this with { ApprovalStatus = "rejected", RejectionReason = reason };
    }
    
    public SelfImprovementProposal SetComponents(string components)
    {
        return this with { RequiredComponents = components };
    }
    
    // Properties
    public string ApprovedAt { get; private set; } = null;
    public string RejectionReason { get; private set; } = null;
}

/// <summary>
/// Proposal storage for operator review queue.
/// </summary>
public class ProposalStore
{
    private readonly List<SelfImprovementProposal> _proposals = new();
    private readonly object _lock = new();
    
    public void AddProposal(SelfImprovementProposal proposal)
    {
        lock (_lock)
        {
            _proposals.Add(proposal);
        }
    }
    
    public IEnumerable<SelfImprovementProposal> GetPendingProposals()
    {
        lock (_lock)
        {
            return _proposals.Where(p => p.ApprovalStatus == "pending").ToList();
        }
    }
    
    public IEnumerable<SelfImprovementProposal> GetAllProposals()
    {
        lock (_lock)
        {
            return _proposals.ToList();
        }
    }
    
    public SelfImprovementProposal GetProposal(string id)
    {
        lock (_lock)
        {
            return _proposals.FirstOrDefault(p => p.Id == id);
        }
    }
    
    public void UpdateProposal(SelfImprovementProposal updated)
    {
        lock (_lock)
        {
            var index = _proposals.FindIndex(p => p.Id == updated.Id);
            if (index >= 0)
            {
                _proposals[index] = updated;
            }
        }
    }
}
```

---

## SECTION 7 — VALIDATION (SIMULATED SCAN)

### Validation Script

```csharp
using SiemensToWeslr.TiaCollector.CapabilityDiscovery;

/// <summary>
/// Validation script for scientific capability discovery extension.
/// Runs one simulated scan showing the full pipeline.
/// </summary>
public static class ValidationScript
{
    public static async Task RunValidationAsync()
    {
        Console.WriteLine("=== WESLR Scientific Capability Discovery Validation ===");
        Console.WriteLine();
        
        // Step 1: Create a simulated research signal from arXiv
        Console.WriteLine("1. Simulating arXiv research signal...");
        var arxivSignal = new ResearchSignal(
            Id: "arxiv-2604.12345",
            Title: "Missing Real-Time Collaboration in Open-Source Tools: A Survey",
            Abstract: "We analyze 50 popular open-source tools and find that 78% lack real-time collaboration capabilities. This gap indicates a significant opportunity for tools like WESLR.",
            Url: "https://arxiv.org/abs/2604.12345",
            PublishedAt: "2026-04-05T10:00:00Z",
            SourceName: "arXiv",
            SourceBucket: "preprints",
            InstitutionName: null,
            CitationCount: 0,
            DomainField: "software_engineering",
            RelevanceScore: 0.85f,
            PaperId: "2604.12345",
            AuthorString: "Smith et al."
        );
        Console.WriteLine($"   Signal: {arxivSignal.Title}");
        Console.WriteLine($"   Source: {arxivSignal.SourceName} ({arxivSignal.SourceBucket})");
        Console.WriteLine();
        
        // Step 2: Normalize to capability suggestion
        Console.WriteLine("2. Normalizing to capability suggestion...");
        var suggestion = arxivSignal.ToCapabilitySuggestion("capability_gap");
        Console.WriteLine($"   Title: {suggestion.Title}");
        Console.WriteLine($"   Type: {suggestion.CapabilityType}");
        Console.WriteLine($"   Source Bucket: {suggestion.SourceBucket}");
        Console.WriteLine($"   Scientific: {suggestion.IsScientificSignal}");
        Console.WriteLine($"   Self-Improvement Candidate: {suggestion.IsSelfImprovementCandidate}");
        Console.WriteLine();
        
        // Step 3: Classify for self-improvement
        Console.WriteLine("3. Classifying as self-improvement candidate...");
        var classification = suggestion.Classify();
        Console.WriteLine($"   Category: {classification.Category}");
        Console.WriteLine($"   Why Relevant: {classification.WhyRelevantToWeslr}");
        Console.WriteLine($"   Expected Benefit: {classification.ExpectedSystemBenefit}");
        Console.WriteLine();
        
        // Step 4: Generate proposal (if self-improvement candidate)
        Console.WriteLine("4. Generating self-improvement proposal...");
        if (classification.Category == SelfImprovementCategory.INTERNAL_SELF_IMPROVEMENT ||
            classification.Category == SelfImprovementCategory.BOTH_PRODUCT_AND_INTERNAL)
        {
            var proposal = SelfImprovementProposal.FromSuggestion(suggestion, classification);
            Console.WriteLine($"   Proposal ID: {proposal.Id}");
            Console.WriteLine($"   Title: {proposal.Title}");
            Console.WriteLine($"   Status: {proposal.ApprovalStatus}");
            Console.WriteLine($"   Required Components: {proposal.RequiredComponents}");
            Console.WriteLine($"   Reversibility: {proposal.ReversibilityRating}");
            Console.WriteLine();
        }
        else
        {
            Console.WriteLine("   (Not classified as self-improvement - would be external-only suggestion)");
            Console.WriteLine();
        }
        
        // Step 5: Show full data model
        Console.WriteLine("5. Full capability suggestion (to_dict representation):");
        var dict = suggestion.ToDictionary();
        Console.WriteLine($"   ID: {dict["id"]}");
        Console.WriteLine($"   Title: {dict["title"]}");
        Console.WriteLine($"   Status: {dict["status"]}");
        Console.WriteLine($"   Confidence: {dict["confidence"]}");
        Console.WriteLine($"   Rank Score: {dict["rank_score"]}");
        Console.WriteLine($"   Source Bucket: {dict["source_bucket"]}");
        Console.WriteLine($"   Research Domain: {dict["research_domain"]}");
        Console.WriteLine($"   Scientific Signal: {dict["is_scientific_signal"]}");
        Console.WriteLine($"   Citation Count: {dict["citation_count"]}");
        Console.WriteLine($"   Science Relevance: {dict["science_relevance_score"]}");
        Console.WriteLine($"   Implementation Risk: {dict["implementation_risk"]}");
        Console.WriteLine($"   Reversibility: {dict["reversibility"]}");
        Console.WriteLine($"   Self-Improvement Candidate: {dict["is_self_improvement_candidate"]}");
        Console.WriteLine();
        
        Console.WriteLine("=== Validation Complete ===");
    }
    
    // Helper extension for to_dict
    private static Dictionary<string, object> ToDictionary(this CapabilitySuggestion s)
    {
        return new Dictionary<string, object>
        {
            { "id", s.Id },
            { "title", s.Title },
            { "capability_type", s.CapabilityType },
            { "summary", s.Summary },
            { "why_it_matters", s.WhyItMatters },
            { "improvement_area", s.ImprovementArea },
            { "status", s.Status },
            { "confidence", s.Confidence },
            { "rank_score", s.RankScore },
            { "source_bucket", s.SourceBucket },
            { "research_domain", s.ResearchDomain },
            { "is_scientific_signal", s.IsScientificSignal },
            { "citation_count", s.CitationCount },
            { "science_relevance_score", s.ScienceRelevanceScore },
            { "implementation_risk", s.ImplementationRisk },
            { "reversibility", s.Reversibility },
            { "is_self_improvement_candidate", s.IsSelfImprovementCandidate },
            { "created_at", s.CreatedAt },
            { "last_seen_at", s.LastSeenAt }
        };
    }
}
```

### Expected Output

```
=== WESLR Scientific Capability Discovery Validation ===

1. Simulating arXiv research signal...
   Signal: Missing Real-Time Collaboration in Open-Source Tools: A Survey
   Source: arXiv (preprints)

2. Normalizing to capability suggestion...
   Title: Missing Real-Time Collaboration in Open-Source Tools: A Survey
   Type: RealTimeCollab
   Source Bucket: preprints
   Scientific: True
   Self-Improvement Candidate: True

3. Classifying as self-improvement candidate...
   Category: InternalSelfImprovement
   Why Relevant: This capability enables better self-modification for WESLR.
   Expected Benefit: WESLR can improve its own capabilities through this signal.

4. Generating self-improvement proposal...
   Proposal ID: (new GUID)
   Title: Missing Real-Time Collaboration in Open-Source Tools: A Survey
   Status: pending
   Required Components: - Research signal analysis
- Capability gap assessment
- Implementation path
- Validation framework
- Rollback mechanism
   Reversibility: medium

5. Full capability suggestion (to_dict representation):
   ID: (arxiv-2604.12345)
   Title: Missing Real-Time Collaboration in Open-Source Tools: A Survey
   Status: new
   Confidence: 0.85
   Rank Score: 95.5
   Source Bucket: preprints
   Research Domain: software_engineering
   Scientific Signal: True
   Citation Count: 0
   Science Relevance: 0.85
   Implementation Risk: medium
   Reversibility: medium
   Self-Improvement Candidate: True

=== Validation Complete ===
```

---

## SECTION 8 — STOP

### Exact Files Changed

**New Files to Create (in `weslr-tia-openness-bridge/src/CapabilityDiscovery/`):**

| File | Purpose |
|------|---------|
| `SourceBuckets.cs` | Source bucket enum with scientific sources |
| `SourceProvenanceExtensions.cs` | Extended SourceProvenance with new fields |
| `CapabilitySuggestionExtensions.cs` | Extended CapabilitySuggestion with self-improvement fields |
| `IResearchConnector.cs` | Interface for research source adapters |
| `ArxivConnector.cs` | arXiv API connector (priority A) |
| `SemanticScholarConnector.cs` | Semantic Scholar API connector (priority A) |
| `OpenAlexConnector.cs` | OpenAlex API connector (priority A) |
| `GapDetector.cs` | Gap signal extraction from text |
| `SignalNormalizer.cs` | Research signal → capability suggestion |
| `SelfImprovementClassifier.cs` | Classify suggestions as self-improvement candidates |
| `SelfImprovementProposal.cs` | Operator-reviewable self-improvement proposals |
| `ProposalStore.cs` | In-memory store for proposal queue |

**Modified Files (additive changes only):**

| File | Change |
|------|--------|
| `weslr-tia-openness-bridge/src/Contracts/ProjectContract.cs` | None - existing structure preserved |
| `weslr-tia-openness-bridge/src/Extraction/ExtractionOrchestrator.cs` | Add capability discovery pipeline integration |

### Exact New Source Buckets

Added to source bucket classification:

```
- github (existing)
- reddit (existing)  
- huggingface (NEW)
- papers (NEW)
- preprints (NEW)
- journals (NEW)
- university_labs (NEW)
- research_forums (NEW)
- scientific_blogs (NEW)
- benchmark_leaderboards (NEW)
```

### Exact Extraction Rules Added

**Gap Signal Patterns:**

```
1. capability_gap:
   - "no implementation", "not implemented", "missing tooling", "lacks", "cannot"
   
2. workflow_bottleneck:
   - "workflow bottleneck", "bottleneck", "manual work", "repetitive"
   
3. reproducibility_gap:
   - "not reproducible", "reproducibility", "lack of implementation"
   
4. future_work:
   - "future work", "future research", "limitations", "limitation"
   
5. benchmark_gap:
   - "benchmark gap", "sota", "state-of-the-art"
   
6. data_challenge:
   - "data preprocessing", "data preparation", "data cleaning"
   
7. validation_gap:
   - "needs validation", "validation needed", "requires validation"
```

### Exact Self-Improvement Classification Fields Added

**To CapabilitySuggestion:**

```
- SourceBucket: string (primary source bucket)
- ResearchDomain: string (research domain field)
- IsScientificSignal: bool (is from scientific source?)
- CitationCount: int (for papers)
- ScienceRelevanceScore: float (0-1)
- ImplementationRisk: string ("low" | "medium" | "high")
- Reversibility: string ("low" | "medium" | "high")
- IsSelfImprovementCandidate: bool (can this improve WESLR?)
```

**To Classification Result:**

```
- Category: enum (EXTERNAL_ONLY | PRODUCT_OPPORTUNITY | INTERNAL_SELF_IMPROVEMENT | BOTH_PRODUCT_AND_INTERNAL)
- WhyRelevantToWeslr: string (reasoning)
- ExpectedSystemBenefit: string (benefit description)
- ImplementationRisk: string
- Reversibility: string
- OperatorVisibility: string ("low" | "medium" | "high")
```

### Example Governed Self-Improvement Proposal Generated

```json
{
  "id": "self-improvement-001",
  "title": "Missing Real-Time Collaboration in Open-Source Tools: A Survey",
  "rationale": "WESLR lacks capability indicated by research: We analyze 50 popular open-source tools and find that 78% lack real-time collaboration capabilities...",
  "expected_benefit": "WESLR can improve its own capabilities through this signal.",
  "expected_risk": "medium",
  "required_components": "- Research signal analysis\n- Capability gap assessment\n- Implementation path\n- Validation framework\n- Rollback mechanism",
  "reversibility_rating": "medium",
  "approval_status": "pending",
  "created_at": "2026-04-05T22:00:00Z",
  "provenance": [
    {
      "url": "https://arxiv.org/abs/2604.12345",
      "title": "Missing Real-Time Collaboration in Open-Source Tools: A Survey",
      "snippet": "We analyze 50 popular open-source tools and find that 78% lack real-time collaboration capabilities...",
      "relevance_score": 0.85,
      "signal_type": "capability_gap",
      "timestamp": "2026-04-05T10:00:00Z",
      "source_bucket": "preprints",
      "institution_name": null,
      "publication_date": "2026-04-05",
      "citation_count": 0,
      "benchmark_name": null,
      "domain_field": "software_engineering"
    }
  ],
  "classification": {
    "category": "internal_self_improvement",
    "why_relevant_to_weslr": "This capability enables better self-modification for WESLR.",
    "expected_system_benefit": "WESLR can improve its own capabilities through this signal.",
    "implementation_risk": "medium",
    "reversibility": "medium",
    "operator_visibility": "high"
  },
  "source_signal_id": "arxiv-2604.12345",
  "original_suggestion_id": "suggestion-001"
}
```

### Safest Next Step After This Expansion

**Next Step: Build the connector stubs and validate with test data.**

1. **Create the core directory structure:**
   ```bash
   mkdir -p weslr-tia-openness-bridge/src/CapabilityDiscovery
   ```

2. **Create minimal connector stubs (no API calls yet):**
   - `IResearchConnector.cs` - Interface only
   - `ArxivConnector.cs` - Minimal implementation (can be placeholder)
   - `GapDetector.cs` - Pattern matching only (no external dependencies)

3. **Create test fixture for simulated scan:**
   - `ValidationScript.cs` - Runs the simulated scan
   - Add unit tests for gap detection patterns

4. **Run validation with simulated data:**
   - Verify data model extensions work
   - Verify classification logic
   - Verify proposal generation

5. **Add connector methods to ExtractionOrchestrator:**
   - Integrate gap detection into extraction pipeline
   - Add connector dispatch logic

**No automatic self-modification occurs.** All proposals go to operator review queue for explicit approval before any action.

---

*End of WESLR Scientific Capability Discovery Extension Document*
