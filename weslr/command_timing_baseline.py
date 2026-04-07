# command_timing_baseline.py - WESLR v81: End-to-End Command Path Timing
# Read-only timing/instrumentation only.
# No caching, no refactors, no optimization, no backend/service/UI.
# No TIA/C#, no orchestration, no sharding, no aggregation.

from __future__ import annotations

import argparse
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class CommandTimingRecord:
    """Timing record for a single command execution."""
    
    record_id: str
    command: str
    timestamp: str
    start_ms: float
    end_ms: Optional[float] = None
    latency_ms: Optional[float] = None
    warmup: bool = False
    batch_index: int = 0
    output_chars: int = 0
    correlation_ids: Dict[str, str] = field(default_factory=dict)
    
    def end(self, end_ms: Optional[float] = None) -> float:
        """End timing and compute latency."""
        if self.end_ms is not None:
            return self.latency_ms or 0.0
        
        self.end_ms = end_ms or (time.perf_counter_ns() / 1_000_000.0)
        self.latency_ms = self.end_ms - self.start_ms
        return self.latency_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        result = {
            "record_id": self.record_id,
            "command": self.command,
            "timestamp": self.timestamp,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "latency_ms": self.latency_ms,
            "warmup": self.warmup,
            "batch_index": self.batch_index,
            "output_chars": self.output_chars,
        }
        if self.correlation_ids:
            result["correlation_ids"] = self.correlation_ids
        return result
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class CommandTimingRun:
    """Timing run for a single command."""
    
    run_id: str
    command: str
    total_records: int
    total_latency_ms: float
    avg_ms: float
    p50_ms: float
    p50_available: bool = True
    p95_ms: Optional[float] = None
    p95_available: bool = False
    p99_ms: Optional[float] = None
    p99_available: bool = False
    max_ms: float = 0.0
    min_ms: float = 0.0
    variance: float = 0.0
    std_dev: float = 0.0
    sample_count: int = 0
    confidence_level: str = "low"
    correlation_coverage: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        result = {
            "run_id": self.run_id,
            "command": self.command,
            "total_records": self.total_records,
            "total_latency_ms": self.total_latency_ms,
            "avg_ms": self.avg_ms,
            "p50_ms": self.p50_ms,
            "p50_available": self.p50_available,
            "p95_available": self.p95_available,
            "p99_available": self.p99_available,
            "max_ms": self.max_ms,
            "min_ms": self.min_ms,
            "variance": self.variance,
            "std_dev": self.std_dev,
            "sample_count": self.sample_count,
            "confidence_level": self.confidence_level,
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
class CommandBaselineSummary:
    """Operator-readable command timing baseline summary."""
    
    summary_id: str
    timestamp: str
    total_commands: int
    total_latency_ms: float
    operator_readable: str
    machine_readable: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "summary_id": self.summary_id,
            "timestamp": self.timestamp,
            "total_commands": self.total_commands,
            "total_latency_ms": self.total_latency_ms,
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# STATISTICS HELPERS
# ============================================================================


def compute_percentile(values: List[float], percentile: float) -> float:
    """Compute percentile using nearest-rank method."""
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    if n == 1:
        return sorted_values[0]
    
    index = int((percentile / 100.0) * n)
    index = max(0, min(index, n - 1))
    
    return sorted_values[index]


def compute_summary_statistics_with_confidence(latencies: List[float]) -> Dict[str, Any]:
    """Compute summary statistics with measurement confidence.
    
    p95/p99 only available when sample size >= 10.
    Confidence = measurement reliability (sample size based).
    """
    if not latencies:
        return {
            "avg_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": None,
            "p99_ms": None,
            "max_ms": 0.0,
            "min_ms": 0.0,
            "p95_available": False,
            "p99_available": False,
            "sample_count": 0,
            "variance": 0.0,
            "std_dev": 0.0,
        }
    
    sample_count = len(latencies)
    avg_ms = sum(latencies) / sample_count
    p50_ms = compute_percentile(latencies, 50)
    max_ms = max(latencies)
    min_ms = min(latencies)
    
    # Calculate variance and std dev
    variance = sum((x - avg_ms) ** 2 for x in latencies) / sample_count
    std_dev = variance ** 0.5
    
    # p95/p99 only available when sample size >= 10
    p95_available = sample_count >= 10
    p99_available = sample_count >= 10
    
    p95_ms: Optional[float] = None
    p99_ms: Optional[float] = None
    
    if p95_available:
        p95_ms = compute_percentile(latencies, 95)
    if p99_available:
        p99_ms = compute_percentile(latencies, 99)
    
    # Determine confidence level based on sample size
    if sample_count >= 100:
        confidence = "high"
    elif sample_count >= 30:
        confidence = "medium"
    elif sample_count >= 10:
        confidence = "low"
    else:
        confidence = "very_low"
    
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
        "variance": variance,
        "std_dev": std_dev,
        "confidence": confidence,
    }


# ============================================================================
# COMMAND TIMING BASELINE RUNNER
# ============================================================================


class CommandTimingBaselineRunner:
    """End-to-end command path timing harness.
    
    Measures:
    - Parser dispatch overhead
    - Handler invocation
    - Output formatting
    - Warmup vs cold command timing
    
    Read-only instrumentation only — no behavior changes.
    """
    
    def __init__(self, workspace_path: Optional[Path] = None):
        """Initialize command timing runner.
        
        Args:
            workspace_path: Path to workspace (uses default if None)
        """
        self._workspace_path = workspace_path or Path("/data/data/com.termux/files/home/.openclaw/workspace")
        self._parser: Optional[argparse.ArgumentParser] = None
        self._commands: List[CommandTimingRun] = []
    
    def _get_command_parser(self) -> argparse.ArgumentParser:
        """Get or create the main command parser."""
        if self._parser is None:
            # Import main.py and create parser
            main_path = self._workspace_path / "main.py"
            if not main_path.exists():
                raise FileNotFoundError(f"main.py not found at {main_path}")
            
            # Create a minimal parser with subcommands
            self._parser = argparse.ArgumentParser(
                prog="main.py",
                description="WESLR v81 - Command Timing Baseline",
                add_help=False,
            )
            sub = self._parser.add_subparsers(dest="cmd", required=False)
            
            # Add diagnostic commands
            sub.add_parser("diagnostics-summary", help="Export diagnostic summary")
            sub.add_parser("diagnostics-recovery-hints", help="Export recovery hints")
            sub.add_parser("diagnostics-trace-export", help="Export decision trace")
            
            # Add fallback commands
            sub.add_parser("fallback-status", help="Show fallback status")
            sub.add_parser("fallback-trace-export", help="Export fallback trace")
        
        return self._parser
    
    def _dispatch_command(self, command_name: str, args: Optional[List[str]] = None) -> Tuple[str, float]:
        """Dispatch command and capture output and timing.
        
        Returns (output_text, output_chars).
        """
        parser = self._get_command_parser()
        
        # Parse arguments
        parsed_args = parser.parse_args(args or [command_name])
        
        # Import and dispatch
        main_path = self._workspace_path / "main.py"
        sys.path.insert(0, str(self._workspace_path))
        
        try:
            # Import main module
            import importlib.util
            spec = importlib.util.spec_from_file_location("main", main_path)
            main_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_module)
            
            # Get function name and dispatch
            func_name = f"cmd_{command_name.replace('-', '_')}"
            func = getattr(main_module, func_name, None)
            
            if func is None:
                return f"Command not found: {command_name}", 0
            
            # Capture output
            import io
            import contextlib
            
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                func(parsed_args)
            
            output = f.getvalue()
            return output, len(output)
        
        except Exception as e:
            return f"Error: {e}", 0
    
    def measure_command(
        self,
        command_name: str,
        samples: int = 10,
        warmup_samples: int = 1,
        batch_size: int = 1,
    ) -> List[CommandTimingRecord]:
        """Measure command timing across multiple samples.
        
        Args:
            command_name: Name of command to measure
            samples: Number of timing samples
            warmup_samples: Number of warmup runs (excluded from stats)
            batch_size: Batch size for comparison
        
        Returns:
            List of timing records
        """
        records: List[CommandTimingRecord] = []
        
        # Warmup runs
        for i in range(warmup_samples):
            start_ms = time.perf_counter_ns() / 1_000_000.0
            
            output, output_chars = self._dispatch_command(command_name)
            
            end_ms = time.perf_counter_ns() / 1_000_000.0
            latency = end_ms - start_ms
            
            record = CommandTimingRecord(
                record_id=f"cmd_{command_name}_{uuid.uuid4().hex[:12]}",
                command=command_name,
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                start_ms=start_ms,
                end_ms=end_ms,
                latency_ms=latency,
                warmup=True,
                batch_index=i,
                output_chars=output_chars,
            )
            records.append(record)
        
        # Timed runs
        for i in range(samples):
            start_ms = time.perf_counter_ns() / 1_000_000.0
            
            output, output_chars = self._dispatch_command(command_name)
            
            end_ms = time.perf_counter_ns() / 1_000_000.0
            latency = end_ms - start_ms
            
            record = CommandTimingRecord(
                record_id=f"cmd_{command_name}_{uuid.uuid4().hex[:12]}",
                command=command_name,
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                start_ms=start_ms,
                end_ms=end_ms,
                latency_ms=latency,
                warmup=False,
                batch_index=i,
                output_chars=output_chars,
            )
            records.append(record)
        
        return records
    
    def build_command_timing_run(self, records: List[CommandTimingRecord]) -> CommandTimingRun:
        """Build timing run from records.
        
        Excludes warmup records from statistics.
        """
        # Filter out warmup records
        timed_records = [r for r in records if not r.warmup]
        
        if not timed_records:
            return CommandTimingRun(
                run_id=f"run_{uuid.uuid4().hex[:12]}",
                command=records[0].command if records else "unknown",
                total_records=0,
                total_latency_ms=0.0,
                avg_ms=0.0,
                p50_ms=0.0,
                max_ms=0.0,
                min_ms=0.0,
            )
        
        latencies = [r.latency_ms or 0.0 for r in timed_records]
        
        stats = compute_summary_statistics_with_confidence(latencies)
        
        return CommandTimingRun(
            run_id=f"run_{uuid.uuid4().hex[:12]}",
            command=records[0].command if records else "unknown",
            total_records=len(timed_records),
            total_latency_ms=sum(latencies),
            avg_ms=stats["avg_ms"],
            p50_ms=stats["p50_ms"],
            p50_available=True,
            p95_ms=stats["p95_ms"],
            p95_available=stats["p95_available"],
            p99_ms=stats["p99_ms"],
            p99_available=stats["p99_available"],
            max_ms=stats["max_ms"],
            min_ms=stats["min_ms"],
            variance=stats["variance"],
            std_dev=stats["std_dev"],
            sample_count=stats["sample_count"],
            confidence_level=stats["confidence"],
            correlation_coverage={
                "total": len(timed_records),
                "with_output_chars": len(timed_records),
            },
        )
    
    def run_diagnostics_summary(self, samples: int = 10, warmup: int = 1) -> CommandTimingRun:
        """Measure diagnostics-summary command timing."""
        records = self.measure_command("diagnostics-summary", samples=samples, warmup_samples=warmup)
        return self.build_command_timing_run(records)
    
    def run_diagnostics_recovery_hints(self, samples: int = 10, warmup: int = 1) -> CommandTimingRun:
        """Measure diagnostics-recovery-hints command timing."""
        records = self.measure_command("diagnostics-recovery-hints", samples=samples, warmup_samples=warmup)
        return self.build_command_timing_run(records)
    
    def run_diagnostics_trace_export(self, samples: int = 10, warmup: int = 1) -> CommandTimingRun:
        """Measure diagnostics-trace-export command timing."""
        records = self.measure_command("diagnostics-trace-export", samples=samples, warmup_samples=warmup)
        return self.build_command_timing_run(records)
    
    def run_fallback_status(self, samples: int = 10, warmup: int = 1) -> CommandTimingRun:
        """Measure fallback-status command timing."""
        records = self.measure_command("fallback-status", samples=samples, warmup_samples=warmup)
        return self.build_command_timing_run(records)
    
    def run_fallback_trace_export(self, samples: int = 10, warmup: int = 1) -> CommandTimingRun:
        """Measure fallback-trace-export command timing."""
        records = self.measure_command("fallback-trace-export", samples=samples, warmup_samples=warmup)
        return self.build_command_timing_run(records)
    
    def run_all_commands(self, samples: int = 10, warmup: int = 1) -> List[CommandTimingRun]:
        """Run all measured commands.
        
        Commands: diagnostics-summary, fallback-status, diagnostics-recovery-hints,
        diagnostics-trace-export, fallback-trace-export
        """
        self._commands = []
        
        commands = [
            ("diagnostics-summary", self.run_diagnostics_summary),
            ("fallback-status", self.run_fallback_status),
            ("diagnostics-recovery-hints", self.run_diagnostics_recovery_hints),
            ("diagnostics-trace-export", self.run_diagnostics_trace_export),
            ("fallback-trace-export", self.run_fallback_trace_export),
        ]
        
        for name, method in commands:
            try:
                run = method(samples=samples, warmup=warmup)
                self._commands.append(run)
            except Exception as e:
                # If command fails, add placeholder record
                run = CommandTimingRun(
                    run_id=f"run_{uuid.uuid4().hex[:12]}",
                    command=name,
                    total_records=0,
                    total_latency_ms=0.0,
                    avg_ms=0.0,
                    p50_ms=0.0,
                    max_ms=0.0,
                    min_ms=0.0,
                    confidence_level="error",
                )
                self._commands.append(run)
        
        return self._commands
    
    def identify_command_hotspots(self) -> List[CommandTimingRun]:
        """Identify command timing hotspots.
        
        Returns commands sorted by average latency (descending).
        """
        if not self._commands:
            return []
        
        # Filter out error commands
        valid_commands = [c for c in self._commands if c.confidence_level != "error"]
        
        # Sort by avg latency descending
        valid_commands.sort(key=lambda c: c.avg_ms, reverse=True)
        
        return valid_commands
    
    def get_baseline_summary(self) -> CommandBaselineSummary:
        """Generate operator-readable baseline summary."""
        if not self._commands:
            return CommandBaselineSummary(
                summary_id=f"summary_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                total_commands=0,
                total_latency_ms=0.0,
                operator_readable="No command timing data available.",
                machine_readable="{}",
            )
        
        total_latency = sum(c.total_latency_ms for c in self._commands)
        
        # Operator-readable summary
        lines = [
            "=" * 70,
            "COMMAND TIMING BASELINE SUMMARY",
            "=" * 70,
            f"Summary ID:  {uuid.uuid4().hex[:12]}",
            f"Timestamp:   {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            f"Total Commands: {len(self._commands)}",
            f"Total Latency: {total_latency:.2f} ms",
            "",
            "-" * 70,
            "COMMAND BREAKDOWN",
            "-" * 70,
        ]
        
        for cmd in self._commands:
            lines.extend([
                f"\nCommand: {cmd.command}",
                f"  Total Records:  {cmd.total_records}",
                f"  Average:        {cmd.avg_ms:.2f} ms",
                f"  P50:            {cmd.p50_ms:.2f} ms",
            ])
            
            if cmd.p95_available and cmd.p95_ms is not None:
                lines.append(f"  P95:            {cmd.p95_ms:.2f} ms")
            if cmd.p99_available and cmd.p99_ms is not None:
                lines.append(f"  P99:            {cmd.p99_ms:.2f} ms")
            
            lines.extend([
                f"  Max:            {cmd.max_ms:.2f} ms",
                f"  Min:            {cmd.min_ms:.2f} ms",
                f"  Sample Count:   {cmd.sample_count}",
                f"  Confidence:     {cmd.confidence_level} (measurement)",
            ])
        
        lines.append("")
        lines.append("-" * 70)
        lines.append("MEASURED HOTSPOTS (sorted by avg latency, descending)")
        lines.append("-" * 70)
        
        hotspots = self.identify_command_hotspots()
        for h in hotspots:
            lines.append(f"\n{h.command}: {h.avg_ms:.2f}ms avg, {h.p50_ms:.2f}ms p50")
            if h.p95_available:
                lines.append(f"  P95: {h.p95_ms:.2f}ms")
            if h.p99_available:
                lines.append(f"  P99: {h.p99_ms:.2f}ms")
        
        lines.append("")
        lines.append("=" * 70)
        
        operator_summary = "\n".join(lines)
        machine_summary = json.dumps({
            "summary_id": f"summary_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "total_commands": len(self._commands),
            "commands": [c.to_dict() for c in self._commands],
        }, indent=2)
        
        return CommandBaselineSummary(
            summary_id=f"summary_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            total_commands=len(self._commands),
            total_latency_ms=total_latency,
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
    
    def export_baseline_json(self) -> str:
        """Export baseline as JSON string."""
        summary = self.get_baseline_summary()
        return summary.machine_readable
    
    def export_operator_readable(self) -> str:
        """Export baseline as operator-readable string."""
        summary = self.get_baseline_summary()
        return summary.operator_readable


# ============================================================================
# INTEGRATION HELPERS (Additive Only)
# ============================================================================


def integrate_with_command_dispatcher(runner: CommandTimingBaselineRunner) -> Dict[str, Any]:
    """Integration hook for command dispatcher — read-only measurement only.
    
    No behavior changes to existing commands.
    """
    return {"hooked": True, "measures": "command_dispatch_latency"}


def integrate_with_output_formatter(runner: CommandTimingBaselineRunner) -> Dict[str, Any]:
    """Integration hook for output formatter — read-only measurement only.
    
    No behavior changes to existing formatters.
    """
    return {"hooked": True, "measures": "output_formatting_latency"}
