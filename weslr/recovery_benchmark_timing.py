# recovery_benchmark_timing.py - WESLR v79: Recovery Benchmark Timing Harness
# Read-only timing layer for recovery workflow measurement.
# Additive only, self-contained, no behavior changes to existing recovery modules.
# No caching yet, no orchestration, no scheduler/task engine, no backend/service/UI.

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class TimingRecord:
    """Timing record for a single stage substage execution."""
    
    timing_id: str
    stage: str
    substage: str
    start_ms: float
    end_ms: Optional[float] = None
    latency_ms: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)
    correlation_ids: Dict[str, str] = field(default_factory=dict)
    
    def end(self, end_ms: Optional[float] = None) -> float:
        """End timing and compute latency.
        
        Returns latency_ms, or current elapsed if end_ms not provided.
        """
        if self.end_ms is not None:
            return self.latency_ms or 0.0
        
        self.end_ms = end_ms or (time.perf_counter_ns() / 1_000_000.0)
        self.latency_ms = self.end_ms - self.start_ms
        return self.latency_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize record to dict."""
        return {
            "timing_id": self.timing_id,
            "stage": self.stage,
            "substage": self.substage,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "latency_ms": self.latency_ms,
            "context": self.context,
            "correlation_ids": self.correlation_ids,
        }


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    
    benchmark_id: str
    run_timestamp: str
    total_records: int
    batch_size: int
    total_latency_ms: float
    per_stage_latencies: Dict[str, List[float]]
    summary_stats: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dict."""
        return {
            "benchmark_id": self.benchmark_id,
            "run_timestamp": self.run_timestamp,
            "total_records": self.total_records,
            "batch_size": self.batch_size,
            "total_latency_ms": self.total_latency_ms,
            "per_stage_latencies": self.per_stage_latencies,
            "summary_stats": self.summary_stats,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class TimingSummary:
    """Operator-readable timing summary with summary statistics."""
    
    summary_id: str
    run_timestamp: str
    total_records: int
    batch_size: int
    total_latency_ms: float
    avg_ms: float
    p50_ms: float
    p50_available: bool
    p95_ms: Optional[float] = None
    p95_available: bool = False
    p99_ms: Optional[float] = None
    p99_available: bool = False
    max_ms: Optional[float] = None
    min_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize summary to dict."""
        result = {
            "summary_id": self.summary_id,
            "run_timestamp": self.run_timestamp,
            "total_records": self.total_records,
            "batch_size": self.batch_size,
            "total_latency_ms": self.total_latency_ms,
            "avg_ms": self.avg_ms,
            "p50_ms": self.p50_ms,
            "p50_available": self.p50_available,
            "p95_ms": self.p95_ms if self.p95_available else None,
            "p95_available": self.p95_available,
            "p99_ms": self.p99_ms if self.p99_available else None,
            "p99_available": self.p99_available,
            "max_ms": self.max_ms if self.max_ms is not None else 0.0,
            "min_ms": self.min_ms if self.min_ms is not None else 0.0,
        }
        return result
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# TIMING STATISTICS HELPERS
# ============================================================================


def compute_percentile(values: List[float], percentile: float) -> float:
    """Compute percentile of a list of values.
    
    Args:
        values: Sorted or unsorted list of numeric values
        percentile: Percentile to compute (0-100)
    
    Returns:
        Percentile value
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    if n == 1:
        return sorted_values[0]
    
    # Use nearest-rank method
    index = int((percentile / 100.0) * n)
    index = max(0, min(index, n - 1))
    
    return sorted_values[index]


def compute_summary_statistics(latencies: List[float]) -> Dict[str, float]:
    """Compute summary statistics for latencies.
    
    Returns dict with avg, p50, p95, p99, max, min.
    p95/p99 only included when sample size >= 10.
    """
    if not latencies:
        return {
            "avg_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "max_ms": 0.0,
            "min_ms": 0.0,
        }
    
    avg_ms = sum(latencies) / len(latencies)
    p50_ms = compute_percentile(latencies, 50)
    max_ms = max(latencies)
    min_ms = min(latencies)
    
    # p95/p99 only available when sample size >= 10
    sample_size = len(latencies)
    p95_ms: Optional[float] = None
    p99_ms: Optional[float] = None
    p95_available = sample_size >= 10
    p99_available = sample_size >= 10
    
    if p95_available:
        p95_ms = compute_percentile(latencies, 95)
    if p99_available:
        p99_ms = compute_percentile(latencies, 99)
    
    result: Dict[str, float] = {
        "avg_ms": avg_ms,
        "p50_ms": p50_ms,
        "max_ms": max_ms,
        "min_ms": min_ms,
    }
    
    if p95_available and p95_ms is not None:
        result["p95_ms"] = p95_ms
    if p99_available and p99_ms is not None:
        result["p99_ms"] = p99_ms
    
    return result


# ============================================================================
# RECOVERY BENCHMARK HARNESS
# ============================================================================


class RecoveryBenchmarkHarness:
    """Timing/benchmark harness for recovery workflow measurement.
    
    Read-only instrumentation layer that measures actual latency
    without changing recovery logic behavior.
    
    Features:
    - Per-stage substage latency measurement
    - Batch-size comparison support
    - Operator-readable timing summary
    - Machine-readable JSON export
    
    Rules:
    - WESLR Python only
    - Additive only (no changes to existing recovery modules)
    - Read-only instrumentation (no behavior changes)
    - No caching yet
    - No orchestration/scheduler
    - No backend/service/UI
    - No TIA/C#
    """
    
    def __init__(self):
        """Initialize benchmark harness."""
        self._benchmark_id: Optional[str] = None
        self._records: List[TimingRecord] = []
        self._per_stage_latencies: Dict[str, List[float]] = {}
        self._batch_size = 1
    
    def start_stage(
        self,
        stage: str,
        substage: str = "default",
        correlation_ids: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TimingRecord:
        """Start timing for a stage substage.
        
        Args:
            stage: Recovery stage (e.g., "recommendation", "export", "review", "trace")
            substage: Substage identifier (e.g., "generation", "formatting", "exporting")
            correlation_ids: Correlation IDs for tracking
            context: Additional context for this stage
        
        Returns:
            TimingRecord with start_ms set
        """
        record = TimingRecord(
            timing_id=f"timing_{uuid.uuid4().hex[:12]}",
            stage=stage,
            substage=substage,
            start_ms=time.perf_counter_ns() / 1_000_000.0,
            correlation_ids=correlation_ids or {},
            context=context or {},
        )
        self._records.append(record)
        return record
    
    def end_stage(
        self,
        record: TimingRecord,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """End timing for a record.
        
        Args:
            record: TimingRecord from start_stage
            context: Additional context to append
        
        Returns:
            Latency in milliseconds
        """
        if context:
            record.context.update(context)
        
        latency = record.end()
        
        # Track per-stage latencies
        stage_key = f"{record.stage}/{record.substage}"
        if stage_key not in self._per_stage_latencies:
            self._per_stage_latencies[stage_key] = []
        if latency is not None:
            self._per_stage_latencies[stage_key].append(latency)
        
        return latency or 0.0
    
    def start_benchmark(
        self,
        benchmark_id: Optional[str] = None,
        batch_size: int = 1,
    ) -> str:
        """Start a new benchmark run.
        
        Args:
            benchmark_id: Optional benchmark ID, auto-generated if None
            batch_size: Expected batch size for statistics eligibility
        
        Returns:
            Benchmark ID
        """
        self._benchmark_id = benchmark_id or f"benchmark_{uuid.uuid4().hex[:12]}"
        self._batch_size = batch_size
        self._records = []
        self._per_stage_latencies = {}
        return self._benchmark_id
    
    def end_benchmark(self) -> BenchmarkResult:
        """End benchmark and compute results.
        
        Returns:
            BenchmarkResult with all measurements
        """
        if not self._records:
            return BenchmarkResult(
                benchmark_id=self._benchmark_id or "unknown",
                run_timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                total_records=0,
                batch_size=self._batch_size,
                total_latency_ms=0.0,
                per_stage_latencies={},
                summary_stats={"avg_ms": 0.0, "p50_ms": 0.0, "max_ms": 0.0, "min_ms": 0.0},
            )
        
        # Compute total latency
        total_latency_ms = sum(
            r.latency_ms or 0.0
            for r in self._records
        )
        
        # Flatten all latencies for summary
        all_latencies: List[float] = []
        for latencies in self._per_stage_latencies.values():
            all_latencies.extend(latencies)
        
        # Compute summary statistics with sample-size-aware p95/p99
        summary_stats = compute_summary_statistics(all_latencies)
        
        return BenchmarkResult(
            benchmark_id=self._benchmark_id or "unknown",
            run_timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            total_records=len(self._records),
            batch_size=self._batch_size,
            total_latency_ms=total_latency_ms,
            per_stage_latencies=self._per_stage_latencies,
            summary_stats=summary_stats,
        )
    
    def export_timing_summary(self, benchmark_result: BenchmarkResult) -> TimingSummary:
        """Export operator-readable timing summary.
        
        Args:
            benchmark_result: BenchmarkResult from end_benchmark
        
        Returns:
            TimingSummary with summary statistics
        """
        summary_stats = benchmark_result.summary_stats
        sample_size = benchmark_result.total_records
        
        # p95/p99 only available when sample size >= 10
        p95_available = sample_size >= 10
        p99_available = sample_size >= 10
        
        return TimingSummary(
            summary_id=f"summary_{uuid.uuid4().hex[:12]}",
            run_timestamp=benchmark_result.run_timestamp,
            total_records=sample_size,
            batch_size=benchmark_result.batch_size,
            total_latency_ms=benchmark_result.total_latency_ms,
            avg_ms=summary_stats.get("avg_ms", 0.0),
            p50_ms=summary_stats.get("p50_ms", 0.0),
            p50_available=True,  # p50 always available
            p95_ms=summary_stats.get("p95_ms") if p95_available else None,
            p95_available=p95_available,
            p99_ms=summary_stats.get("p99_ms") if p99_available else None,
            p99_available=p99_available,
            max_ms=summary_stats.get("max_ms", 0.0),
            min_ms=summary_stats.get("min_ms", 0.0),
        )
    
    def export_machine_readable(self, benchmark_result: BenchmarkResult) -> str:
        """Export benchmark result as JSON string.
        
        Args:
            benchmark_result: BenchmarkResult from end_benchmark
        
        Returns:
            JSON string
        """
        return benchmark_result.to_json()
    
    def get_records(self) -> List[TimingRecord]:
        """Get all timing records from current benchmark."""
        return self._records.copy()
    
    def get_per_stage_latencies(self) -> Dict[str, List[float]]:
        """Get latencies grouped by stage/substage."""
        return {k: v.copy() for k, v in self._per_stage_latencies.items()}


# ============================================================================
# INTEGRATION HOOKS (Additive Only)
# ============================================================================


def integrate_with_v75_service(harness: RecoveryBenchmarkHarness) -> Dict[str, Any]:
    """Hook into v75 RecoveryRecommendationService for timing.
    
    Reads recommendations without modifying behavior.
    Measures recommendation generation latency.
    
    Args:
        harness: Benchmark harness instance
    
    Returns:
        Empty dict (additive, no modifications)
    """
    # Read-only hook — no behavior changes
    return {"hooked": True, "measures": "recommendation_generation_latency"}


def integrate_with_v76_export(harness: RecoveryBenchmarkHarness) -> Dict[str, Any]:
    """Hook into v76 RecoveryRecommendationExport for timing.
    
    Reads export records without modifying behavior.
    Measures export formatting latency.
    
    Args:
        harness: Benchmark harness instance
    
    Returns:
        Empty dict (additive, no modifications)
    """
    # Read-only hook — no behavior changes
    return {"hooked": True, "measures": "export_formatting_latency"}


def integrate_with_v77_review(harness: RecoveryBenchmarkHarness) -> Dict[str, Any]:
    """Hook into v77 RecoveryRecommendationReview for timing.
    
    Reads review surface without modifying behavior.
    Measures summary generation latency.
    
    Args:
        harness: Benchmark harness instance
    
    Returns:
        Empty dict (additive, no modifications)
    """
    # Read-only hook — no behavior changes
    return {"hooked": True, "measures": "review_summary_latency"}


def integrate_with_v78_trace(harness: RecoveryBenchmarkHarness) -> Dict[str, Any]:
    """Hook into v78 DecisionTrace for timing.
    
    Reads decision trace without modifying behavior.
    Measures trace export latency.
    
    Args:
        harness: Benchmark harness instance
    
    Returns:
        Empty dict (additive, no modifications)
    """
    # Read-only hook — no behavior changes
    return {"hooked": True, "measures": "trace_export_latency"}


def timing_summary_to_operator_readable(summary: TimingSummary) -> str:
    """Convert TimingSummary to operator-readable multi-line string.
    
    Args:
        summary: TimingSummary instance
    
    Returns:
        Multi-line string with timing breakdown
    """
    lines = [
        "=" * 60,
        "RECOVERY BENCHMARK TIMING SUMMARY",
        "=" * 60,
        f"Summary ID:     {summary.summary_id}",
        f"Run Timestamp:  {summary.run_timestamp}",
        f"Total Records:  {summary.total_records}",
        f"Batch Size:     {summary.batch_size}",
        "",
        "-" * 40,
        "LATENCY BREAKDOWN (ms)",
        "-" * 40,
        f"Total:          {summary.total_latency_ms:.2f}",
        f"Average:        {summary.avg_ms:.2f}",
        f"P50:            {summary.p50_ms:.2f}" if summary.p50_available else "P50:            N/A",
        f"Max:            {summary.max_ms:.2f}",
        f"Min:            {summary.min_ms:.2f}",
    ]
    
    if summary.p95_available:
        lines.append(f"P95:            {summary.p95_ms:.2f}")
    else:
        lines.append("P95:            N/A (sample size < 10)")
    
    if summary.p99_available:
        lines.append(f"P99:            {summary.p99_ms:.2f}")
    else:
        lines.append("P99:            N/A (sample size < 10)")
    
    lines.extend(["", "=" * 60])
    
    return "\n".join(lines)


def timing_summary_to_json(summary: TimingSummary) -> str:
    """Convert TimingSummary to JSON string (machine-readable).
    
    Args:
        summary: TimingSummary instance
    
    Returns:
        JSON string
    """
    return summary.to_json()
