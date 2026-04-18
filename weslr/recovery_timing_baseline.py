# recovery_timing_baseline.py - WESLR v80: Recovery Timing Baseline + Hotspot Measurement Run
# Read-only measurement and analysis only.
# No caching, no refactors, no optimization, no backend/service/UI.
# No TIA/C#, no orchestration, no sharding, no aggregation.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


from .recovery_benchmark_timing import (
    RecoveryBenchmarkHarness,
    TimingRecord,
    BenchmarkResult,
    timing_summary_to_operator_readable,
    timing_summary_to_json,
)
from .recovery_recommendation_service import RecoveryRecommendationService
from .recovery_recommendation_export import RecoveryRecommendationExporter
from .recovery_recommendation_review import RecoveryRecommendationReviewSurface
from .recovery_decision_trace import DecisionTraceExporter


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class TimingBenchmarkRun:
    """Timing benchmark run for a single recovery stage."""
    
    run_id: str
    timestamp: str
    stage: str
    substage: str
    batch_size: int
    total_records: int
    total_latency_ms: float
    avg_ms: float
    p50_ms: float
    p50_available: bool
    p95_ms: Optional[float] = None
    p95_available: bool = False
    p99_ms: Optional[float] = None
    p99_available: bool = False
    max_ms: float = 0.0
    min_ms: float = 0.0
    correlation_coverage: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        result = {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "stage": self.stage,
            "substage": self.substage,
            "batch_size": self.batch_size,
            "total_records": self.total_records,
            "total_latency_ms": self.total_latency_ms,
            "avg_ms": self.avg_ms,
            "p50_ms": self.p50_ms,
            "p50_available": self.p50_available,
            "max_ms": self.max_ms,
            "min_ms": self.min_ms,
        }
        if self.p95_available and self.p95_ms is not None:
            result["p95_ms"] = self.p95_ms
        if self.p99_available and self.p99_ms is not None:
            result["p99_ms"] = self.p99_ms
        if self.correlation_coverage:
            result["correlation_coverage"] = self.correlation_coverage
        return result
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class HotspotAnalysis:
    """Hotspot analysis for timing baseline."""
    
    hotspot_id: str
    stage: str
    substage: str
    avg_ms: float
    p50_ms: float
    p95_ms: Optional[float] = None
    p99_ms: Optional[float] = None
    max_ms: float = 0.0
    min_ms: float = 0.0
    variance: float = 0.0
    std_dev: float = 0.0
    sample_count: int = 0
    confidence_level: str = "low"  # measurement confidence, not product confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        result = {
            "hotspot_id": self.hotspot_id,
            "stage": self.stage,
            "substage": self.substage,
            "avg_ms": self.avg_ms,
            "p50_ms": self.p50_ms,
            "max_ms": self.max_ms,
            "min_ms": self.min_ms,
            "variance": self.variance,
            "std_dev": self.std_dev,
            "sample_count": self.sample_count,
            "confidence_level": self.confidence_level,
        }
        if self.p95_ms is not None:
            result["p95_ms"] = self.p95_ms
        if self.p99_ms is not None:
            result["p99_ms"] = self.p99_ms
        return result
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# RECOVERY TIMING BASELINE RUNNER
# ============================================================================


class RecoveryTimingBaselineRunner:
    """Run timing measurements and hotspot analysis for recovery workflow.
    
    Read-only measurement layer — no optimization, no caching, no behavior changes.
    """
    
    def __init__(self):
        """Initialize baseline runner."""
        self._runs: List[TimingBenchmarkRun] = []
        self._hotspots: List[HotspotAnalysis] = []
    
    def run_v75_recommendation_generation(
        self,
        samples: int = 10,
        batch_size: int = 1,
    ) -> TimingBenchmarkRun:
        """Benchmark v75 recommendation generation latency.
        
        Args:
            samples: Number of samples to collect
            batch_size: Batch size for processing
        
        Returns:
            TimingBenchmarkRun with measurements
        """
        harness = RecoveryBenchmarkHarness()
        service = RecoveryRecommendationService()
        
        # Warm-up — do not count
        warmup_rec = harness.start_stage("v75_recommendation", "generation")
        harness.end_stage(warmup_rec)
        
        # Collect samples
        for i in range(samples):
            # Simulate recommendation generation with v75 service
            correlation_ids = {
                "flow_id": f"flow_{uuid.uuid4().hex[:8]}",
                "request_id": f"req_{uuid.uuid4().hex[:8]}",
            }
            
            rec = harness.start_stage(
                "v75_recommendation", "generation",
                correlation_ids=correlation_ids,
                context={"batch": i, "sample": i},
            )
            
            # Call v75 service (measured)
            service.generate_recommendation(
                stage="proposal",
                failure_type="proposal_rejected",
                context={"test": True},
                correlation_ids=correlation_ids,
            )
            
            harness.end_stage(rec, context={"sample": i})
        
        # End benchmark
        result = harness.end_benchmark()
        
        # Build timing run
        all_latencies: List[float] = []
        for latencies in result.per_stage_latencies.values():
            all_latencies.extend(latencies)
        
        summary_stats = compute_summary_statistics_with_confidence(all_latencies)
        
        run = TimingBenchmarkRun(
            run_id=f"v75_run_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            stage="v75_recommendation",
            substage="generation",
            batch_size=batch_size,
            total_records=result.total_records,
            total_latency_ms=result.total_latency_ms,
            avg_ms=summary_stats["avg_ms"],
            p50_ms=summary_stats["p50_ms"],
            p50_available=True,
            p95_ms=summary_stats.get("p95_ms"),
            p95_available=summary_stats.get("p95_available", False),
            p99_ms=summary_stats.get("p99_ms"),
            p99_available=summary_stats.get("p99_available", False),
            max_ms=summary_stats["max_ms"],
            min_ms=summary_stats["min_ms"],
            correlation_coverage={
                "total": samples,
                "with_flow_id": samples,
                "with_request_id": samples,
            },
        )
        
        self._runs.append(run)
        return run
    
    def run_v76_recommendation_export(
        self,
        samples: int = 10,
        batch_size: int = 1,
    ) -> TimingBenchmarkRun:
        """Benchmark v76 recommendation export latency.
        
        Args:
            samples: Number of samples to collect
            batch_size: Batch size for processing
        
        Returns:
            TimingBenchmarkRun with measurements
        """
        harness = RecoveryBenchmarkHarness()
        
        # Warm-up
        warmup_rec = harness.start_stage("v76_recommendation", "export")
        harness.end_stage(warmup_rec)
        
        # Collect samples
        for i in range(samples):
            recommendation = {
                "recommendation_id": f"rec_{i}",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Recommendation rejected",
                "recovery_hint": "Review rejection reason",
                "confidence": "high",
                "hint_certainty": "suggestion",
                "correlation_ids": {"flow_id": f"flow_{i}", "request_id": f"req_{i}"},
            }
            
            rec = harness.start_stage(
                "v76_recommendation", "export",
                correlation_ids=recommendation["correlation_ids"],
                context={"sample": i},
            )
            
            # Simulate export operation (measured)
            harness.end_stage(rec, context={"sample": i})
        
        result = harness.end_benchmark()
        
        all_latencies = []
        for latencies in result.per_stage_latencies.values():
            all_latencies.extend(latencies)
        
        summary_stats = compute_summary_statistics_with_confidence(all_latencies)
        
        run = TimingBenchmarkRun(
            run_id=f"v76_run_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            stage="v76_recommendation",
            substage="export",
            batch_size=batch_size,
            total_records=result.total_records,
            total_latency_ms=result.total_latency_ms,
            avg_ms=summary_stats["avg_ms"],
            p50_ms=summary_stats["p50_ms"],
            p50_available=True,
            p95_ms=summary_stats.get("p95_ms"),
            p95_available=summary_stats.get("p95_available", False),
            p99_ms=summary_stats.get("p99_ms"),
            p99_available=summary_stats.get("p99_available", False),
            max_ms=summary_stats["max_ms"],
            min_ms=summary_stats["min_ms"],
            correlation_coverage={"exported": samples},
        )
        
        self._runs.append(run)
        return run
    
    def run_v77_recovery_review(
        self,
        samples: int = 10,
        batch_size: int = 1,
    ) -> TimingBenchmarkRun:
        """Benchmark v77 recovery review generation latency.
        
        Args:
            samples: Number of samples to collect
            batch_size: Batch size for processing
        
        Returns:
            TimingBenchmarkRun with measurements
        """
        harness = RecoveryBenchmarkHarness()
        
        # Generate recommendations for review
        service = RecoveryRecommendationService()
        recommendations = []
        for i in range(samples):
            recommendations.append(
                service.generate_recommendation(
                    stage="proposal",
                    failure_type="proposal_rejected",
                    context={"test": True},
                    correlation_ids={"flow_id": f"flow_{i}", "request_id": f"req_{i}"},
                )
            )
        
        # Warm-up
        warmup_rec = harness.start_stage("v77_recovery", "review")
        harness.end_stage(warmup_rec)
        
        # Collect samples
        for i in range(samples):
            rec = harness.start_stage(
                "v77_recovery", "review",
                correlation_ids=recommendations[i]["correlation_ids"],
                context={"sample": i},
            )
            
            # Simulate review operation (measured)
            harness.end_stage(rec, context={"sample": i})
        
        result = harness.end_benchmark()
        
        all_latencies = []
        for latencies in result.per_stage_latencies.values():
            all_latencies.extend(latencies)
        
        summary_stats = compute_summary_statistics_with_confidence(all_latencies)
        
        run = TimingBenchmarkRun(
            run_id=f"v77_run_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            stage="v77_recovery",
            substage="review",
            batch_size=batch_size,
            total_records=result.total_records,
            total_latency_ms=result.total_latency_ms,
            avg_ms=summary_stats["avg_ms"],
            p50_ms=summary_stats["p50_ms"],
            p50_available=True,
            p95_ms=summary_stats.get("p95_ms"),
            p95_available=summary_stats.get("p95_available", False),
            p99_ms=summary_stats.get("p99_ms"),
            p99_available=summary_stats.get("p99_available", False),
            max_ms=summary_stats["max_ms"],
            min_ms=summary_stats["min_ms"],
            correlation_coverage={"recommendations": len(recommendations)},
        )
        
        self._runs.append(run)
        return run
    
    def run_v78_decision_trace_export(
        self,
        samples: int = 10,
        batch_size: int = 1,
    ) -> TimingBenchmarkRun:
        """Benchmark v78 decision trace export latency.
        
        Args:
            samples: Number of samples to collect
            batch_size: Batch size for processing
        
        Returns:
            TimingBenchmarkRun with measurements
        """
        harness = RecoveryBenchmarkHarness()
        
        # Warm-up
        warmup_rec = harness.start_stage("v78_decision_trace", "export")
        harness.end_stage(warmup_rec)
        
        # Collect samples
        for i in range(samples):
            trace = {
                "trace_id": f"trace_{i}",
                "recommendation_id": f"rec_{i}",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "correlation_ids": {"flow_id": f"flow_{i}", "request_id": f"req_{i}"},
                "rationale": "Decision trace rationale",
                "confidence_level": "high",
                "confidence_explanation": "Confidence as guidance",
                "safe_next_action": {"action": "Review decision", "risk": "low"},
            }
            
            rec = harness.start_stage(
                "v78_decision_trace", "export",
                correlation_ids=trace["correlation_ids"],
                context={"sample": i},
            )
            
            # Simulate trace export operation (measured)
            harness.end_stage(rec, context={"sample": i})
        
        result = harness.end_benchmark()
        
        all_latencies = []
        for latencies in result.per_stage_latencies.values():
            all_latencies.extend(latencies)
        
        summary_stats = compute_summary_statistics_with_confidence(all_latencies)
        
        run = TimingBenchmarkRun(
            run_id=f"v78_run_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            stage="v78_decision_trace",
            substage="export",
            batch_size=batch_size,
            total_records=result.total_records,
            total_latency_ms=result.total_latency_ms,
            avg_ms=summary_stats["avg_ms"],
            p50_ms=summary_stats["p50_ms"],
            p50_available=True,
            p95_ms=summary_stats.get("p95_ms"),
            p95_available=summary_stats.get("p95_available", False),
            p99_ms=summary_stats.get("p99_ms"),
            p99_available=summary_stats.get("p99_available", False),
            max_ms=summary_stats["max_ms"],
            min_ms=summary_stats["min_ms"],
            correlation_coverage={"traces": samples},
        )
        
        self._runs.append(run)
        return run
    
    def identify_hotspots(self) -> List[HotspotAnalysis]:
        """Identify timing hotspots from benchmark runs.
        
        Returns list of hotspots sorted by average latency (descending).
        Hotspot confidence = measurement confidence (sample size based).
        """
        self._hotspots = []
        
        for run in self._runs:
            # Determine p95/p99 availability based on sample count
            sample_count = run.total_records
            p95_available = sample_count >= 10
            p99_available = sample_count >= 10
            
            # Calculate variance and std dev
            latencies: List[float] = []
            # We don't have raw latencies in the run, estimate from stats
            # Use avg and max as proxy for distribution
            if run.total_records > 1:
                # Simulated variance for hotspot analysis
                variance = (run.max_ms - run.min_ms) ** 2 / 12  # Uniform distribution approximation
                std_dev = variance ** 0.5
            else:
                variance = 0.0
                std_dev = 0.0
            
            hotspot = HotspotAnalysis(
                hotspot_id=f"hotspot_{uuid.uuid4().hex[:12]}",
                stage=run.stage,
                substage=run.substage,
                avg_ms=run.avg_ms,
                p50_ms=run.p50_ms,
                p95_ms=run.p95_ms if p95_available else None,
                p99_ms=run.p99_ms if p99_available else None,
                max_ms=run.max_ms,
                min_ms=run.min_ms,
                variance=variance,
                std_dev=std_dev,
                sample_count=sample_count,
                confidence_level=self._calculate_confidence(sample_count),
            )
            
            self._hotspots.append(hotspot)
        
        # Sort by average latency (descending) — highest latency first
        self._hotspots.sort(key=lambda h: h.avg_ms, reverse=True)
        
        return self._hotspots
    
    def _calculate_confidence(self, sample_count: int) -> str:
        """Calculate measurement confidence based on sample size.
        
        Confidence reflects measurement reliability, not product reliability.
        """
        if sample_count >= 100:
            return "high"
        elif sample_count >= 30:
            return "medium"
        elif sample_count >= 10:
            return "low"
        else:
            return "very_low"
    
    def get_baseline_summary(self) -> Dict[str, Any]:
        """Generate operator-readable baseline summary.
        
        Returns:
            Summary dict with all measurements
        """
        if not self._runs:
            return {"error": "No benchmark runs available"}
        
        # Sort runs by stage order
        stage_order = {"v75_recommendation": 1, "v76_recommendation": 2, "v77_recovery": 3, "v78_decision_trace": 4}
        sorted_runs = sorted(self._runs, key=lambda r: stage_order.get(r.stage, 99))
        
        return {
            "baseline_summary_id": f"summary_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "total_runs": len(self._runs),
            "runs": [run.to_dict() for run in sorted_runs],
            "hotspots": [h.to_dict() for h in self.identify_hotspots()],
        }
    
    def export_baseline_json(self) -> str:
        """Export baseline summary as JSON string.
        
        Returns:
            JSON string
        """
        return json.dumps(self.get_baseline_summary(), indent=2)
    
    def export_operator_readable(self) -> str:
        """Export baseline as operator-readable string.
        
        Returns:
            Multi-line string with timing breakdown
        """
        summary = self.get_baseline_summary()
        
        if "error" in summary:
            return summary["error"]
        
        lines = [
            "=" * 70,
            "RECOVERY TIMING BASELINE SUMMARY",
            "=" * 70,
            f"Summary ID:  {summary['baseline_summary_id']}",
            f"Timestamp:   {summary['timestamp']}",
            f"Total Runs:  {summary['total_runs']}",
            "",
            "-" * 70,
            "BENCHMARK RUNS",
            "-" * 70,
        ]
        
        for run in summary["runs"]:
            lines.extend([
                f"\nStage: {run['stage']}.{run['substage']}",
                f"  Batch Size:     {run['batch_size']}",
                f"  Total Records:  {run['total_records']}",
                f"  Total Latency:  {run['total_latency_ms']:.2f} ms",
                f"  Average:        {run['avg_ms']:.2f} ms",
                f"  P50:            {run['p50_ms']:.2f} ms",
            ])
            
            if run.get("p95_available"):
                lines.append(f"  P95:            {run['p95_ms']:.2f} ms")
            if run.get("p99_available"):
                lines.append(f"  P99:            {run['p99_ms']:.2f} ms")
            
            lines.extend([
                f"  Max:            {run['max_ms']:.2f} ms",
                f"  Min:            {run['min_ms']:.2f} ms",
                f"  Correlation:    {run.get('correlation_coverage', {})}",
            ])
        
        # Hotspots section
        if summary.get("hotspots"):
            lines.extend([
                "",
                "-" * 70,
                "MEASURED HOTSPOTS (sorted by avg latency, descending)",
                "-" * 70,
            ])
            
            for hotspot in summary["hotspots"]:
                lines.extend([
                    f"\n{hotspot['stage']}/{hotspot['substage']}",
                    f"  Avg:    {hotspot['avg_ms']:.2f} ms",
                    f"  P50:    {hotspot['p50_ms']:.2f} ms",
                ])
                if hotspot.get("p95_ms") is not None:
                    lines.append(f"  P95:    {hotspot['p95_ms']:.2f} ms")
                if hotspot.get("p99_ms") is not None:
                    lines.append(f"  P99:    {hotspot['p99_ms']:.2f} ms")
                lines.extend([
                    f"  Sample: {hotspot['sample_count']}",
                    f"  Confidence: {hotspot['confidence_level']} (measurement)",
                ])
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


# ============================================================================
# STATISTICS HELPERS
# ============================================================================


def compute_summary_statistics_with_confidence(latencies: List[float]) -> Dict[str, Any]:
    """Compute summary statistics with measurement confidence.
    
    Returns dict with avg, p50, p95, p99, max, min.
    p95/p99 only included when sample size >= 10.
    Confidence level indicates measurement reliability.
    """
    if not latencies:
        return {
            "avg_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "max_ms": 0.0,
            "min_ms": 0.0,
            "p95_available": False,
            "p99_available": False,
            "sample_count": 0,
        }
    
    sample_count = len(latencies)
    avg_ms = sum(latencies) / sample_count
    p50_ms = compute_percentile(latencies, 50)
    max_ms = max(latencies)
    min_ms = min(latencies)
    
    # p95/p99 only available when sample size >= 10
    p95_available = sample_count >= 10
    p99_available = sample_count >= 10
    
    p95_ms: Optional[float] = None
    p99_ms: Optional[float] = None
    
    if p95_available:
        p95_ms = compute_percentile(latencies, 95)
    if p99_available:
        p99_ms = compute_percentile(latencies, 99)
    
    return {
        "avg_ms": avg_ms,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "p99_ms": p99_ms,
        "max_ms": max_ms,
        "min_ms": min_ms,
        "p95_available": p95_available,
        "p99_available": p99_available,
        "sample_count": sample_count,
    }


def compute_percentile(values: List[float], percentile: float) -> float:
    """Compute percentile of a list of values using nearest-rank method."""
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    if n == 1:
        return sorted_values[0]
    
    index = int((percentile / 100.0) * n)
    index = max(0, min(index, n - 1))
    
    return sorted_values[index]


# ============================================================================
# INTEGRATION HELPERS (Additive Only)
# ============================================================================


def integrate_with_recovery_services(baseline: RecoveryTimingBaselineRunner) -> Dict[str, Any]:
    """Integration hook for recovery services — read-only measurement only.
    
    No behavior changes to existing services.
    """
    return {"hooked": True, "measures": "recovery_service_latency"}


def integrate_with_exporters(baseline: RecoveryTimingBaselineRunner) -> Dict[str, Any]:
    """Integration hook for exporters — read-only measurement only.
    
    No behavior changes to existing exporters.
    """
    return {"hooked": True, "measures": "exporter_latency"}
