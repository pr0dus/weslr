"""
WESLR Consolidation Loop — V1 Read-Only Digest

Collects recent traces from safe WESLR stores, clusters repeated themes,
scores and classifies candidates, writes operator-visible consolidation digest.

NO promotion. NO writes to entity_memory, mission_store, or doctrine.
NO deletion. NO daemon scheduling.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


class Trace:
    """Lightweight trace record — metadata only, no raw content."""
    __slots__ = ("id", "source_file", "source_type", "theme", "category",
                 "mission_id", "created_at", "priority", "confidence",
                 "provenance_ref", "extra")

    def __init__(
        self,
        id: str,
        source_file: str,
        source_type: str,
        theme: str,
        category: str,
        mission_id: str | None = None,
        created_at: str | None = None,
        priority: str | None = None,
        confidence: float | None = None,
        provenance_ref: str | None = None,
        extra: dict | None = None,
    ):
        self.id = id
        self.source_file = source_file
        self.source_type = source_type  # pending_message | mission_suggestion | mission
        self.theme = theme
        self.category = category        # evidence_gap | research_question | mission_progress | proposal
        self.mission_id = mission_id
        self.created_at = created_at
        self.priority = priority
        self.confidence = confidence
        self.provenance_ref = provenance_ref or id
        self.extra = extra or {}

    def to_dict(self) -> dict:
        return {s: getattr(self, s) for s in self.__slots__}


class Cluster:
    """Group of related traces sharing a theme."""
    __slots__ = ("id", "theme", "traces", "category", "mission_ids",
                 "first_seen", "last_seen")

    def __init__(self, id: str, theme: str, traces: list[Trace]):
        self.id = id
        self.theme = theme
        self.traces = traces
        self.category = traces[0].category if traces else "unknown"
        self.mission_ids = list({t.mission_id for t in traces if t.mission_id})
        first_times = [t.created_at for t in traces if t.created_at]
        last_times = first_times
        self.first_seen = min(first_times) if first_times else None
        self.last_seen = max(last_times) if last_times else None


class ConsolidationCandidate:
    """A consolidation candidate record for the digest."""
    __slots__ = (
        "cluster_id", "theme", "trace_count", "first_seen", "last_seen",
        "sources", "score", "proposed_destination", "risk_level",
        "provenance", "gate_note", "created_at",
        "operator_action_required", "automatic_execution", "promotion_performed",
    )

    def __init__(
        self,
        cluster_id: str,
        theme: str,
        trace_count: int,
        first_seen: str | None,
        last_seen: str | None,
        sources: list[str],
        score: dict,
        proposed_destination: str,
        risk_level: str,
        provenance: list[str],
        gate_note: str,
        operator_action_required: bool,
    ):
        self.cluster_id = cluster_id
        self.theme = theme
        self.trace_count = trace_count
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.sources = sources
        self.score = score
        self.proposed_destination = proposed_destination
        self.risk_level = risk_level
        self.provenance = provenance
        self.gate_note = gate_note
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.operator_action_required = operator_action_required
        self.automatic_execution = False
        self.promotion_performed = False

    def to_dict(self) -> dict:
        d = {s: getattr(self, s) for s in self.__slots__}
        d["type"] = "consolidation_candidate"
        return d


class ConsolidationDigestResult:
    """Result of a consolidation digest run."""
    __slots__ = ("traces_collected", "clusters_found", "candidates_written",
                 "output_path", "output_file", "digest_records")

    def __init__(
        self,
        traces_collected: int,
        clusters_found: int,
        candidates_written: int,
        output_path: str,
        output_file: str,
        digest_records: list[dict],
    ):
        self.traces_collected = traces_collected
        self.clusters_found = clusters_found
        self.candidates_written = candidates_written
        self.output_path = output_path
        self.output_file = output_file
        self.digest_records = digest_records

    def summary(self) -> str:
        lines = [
            f"traces_collected={self.traces_collected}",
            f"clusters_found={self.clusters_found}",
            f"candidates_written={self.candidates_written}",
            f"output={self.output_path}",
        ]
        return ", ".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ROOT = pathlib.Path(os.environ.get("WESLR_ROOT", pathlib.Path.home() / ".weslr"))
_PENDING_PATH = _ROOT / "pending_messages.jsonl"
_MISSIONS_PATH = _ROOT / "missions.jsonl"
_EVIDENCE_PATH = _ROOT / "external_evidence_packets.jsonl"
_DIGEST_FILENAME = "consolidation_digest.jsonl"

# When root= is explicitly passed, it points at the workspace root (parent of .weslr).
# When root=None, use _ROOT which already points at .weslr.
def _weslr_dir(root: str | None) -> pathlib.Path:
    """Return the .weslr directory path for the given root."""
    if root is None:
        return _ROOT
    return pathlib.Path(root) / ".weslr"

# Theme extraction patterns — no LLM, template-based
_THEME_PATTERNS = [
    (re.compile(r"bandgap|kesterite|perovskite|solar cell|efficiency", re.I), "solar_materials"),
    (re.compile(r"brca1|breast cancer|talazoparib|clinical trial", re.I), "cancer_research"),
    (re.compile(r"evidence|evidence packet|payload", re.I), "evidence_gap"),
    (re.compile(r"hypothesis|proposal|suggestion", re.I), "hypothesis_proposal"),
    (re.compile(r"mission|research goal|current question", re.I), "mission_tracking"),
    (re.compile(r"soft robot|micro-robotics|actuator|biocompatible", re.I), "soft_robotics"),
    (re.compile(r"consolidation|digest|memory", re.I), "memory_consolidation"),
    (re.compile(r"continuity|recall|session", re.I), "continuity_memory"),
    (re.compile(r"doctrine|governance|phase \d+|checkpoint", re.I), "doctrine_governance"),
    (re.compile(r"experiment|simulation|trial", re.I), "experiment_simulation"),
]


def _extract_theme(text: str | None) -> str:
    """Extract a theme slug from text using patterns. Returns 'general' if none."""
    if not text:
        return "general"
    for pattern, slug in _THEME_PATTERNS:
        if pattern.search(text):
            return slug
    return "general"


def _classify_category(theme: str, trace_count: int) -> str:
    """Classify the category of a trace based on its theme and count."""
    if theme in ("evidence_gap",):
        return "evidence_gap"
    if theme in ("solar_materials", "cancer_research", "soft_robotics", "experiment_simulation"):
        return "research_question"
    if theme in ("hypothesis_proposal",):
        return "proposal"
    if theme in ("mission_tracking",):
        return "mission_progress"
    if theme in ("memory_consolidation", "continuity_memory"):
        return "continuity"
    if theme in ("doctrine_governance",):
        return "governance"
    return "general"


def _is_within_hours(ts: str | None, hours: int) -> bool:
    """Return True if timestamp is within the last `hours`."""
    if not ts:
        return False
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return dt >= cutoff


# ---------------------------------------------------------------------------
# Phase 1: Collect
# ---------------------------------------------------------------------------

def collect_traces(root: str | None = None, hours: int = 24) -> list[Trace]:
    """
    Collect traces from safe WESLR stores within the time window.

    Safe sources: pending_messages.jsonl, missions.jsonl.
    Evidence packets: metadata only (packet_id, source, query, retrieved_at, study_count).

    Excludes: raw message content, full evidence study content.
    """
    traces: list[Trace] = []
    weslr = _weslr_dir(root)
    root_path = pathlib.Path(root) if root else _ROOT

    # --- pending_messages.jsonl ---
    pmp = weslr / "pending_messages.jsonl"
    if pmp.exists():
        for line in _read_lines(pmp):
            rec = json.loads(line)
            rec_type = rec.get("record_type") or rec.get("type", "unknown")
            created = rec.get("enqueued_at") or rec.get("created_at")

            if not _is_within_hours(created, hours):
                continue

            if rec_type == "mission_suggestion":
                theme = _extract_theme(rec.get("suggestion", ""))
                traces.append(Trace(
                    id=rec.get("message_id") or rec.get("mission_id") or str(uuid.uuid4()),
                    source_file=str(pmp),
                    source_type="mission_suggestion",
                    theme=theme,
                    category=_classify_category(theme, 1),
                    mission_id=rec.get("mission_id"),
                    created_at=created,
                    priority=rec.get("priority"),
                    confidence=rec.get("confidence"),
                    provenance_ref=rec.get("provenance", ""),
                    extra={"suggestion": _truncate(rec.get("suggestion", ""), 200)},
                ))
            elif rec_type == "pending_message_v1":
                theme = _extract_theme(rec.get("message", ""))
                traces.append(Trace(
                    id=rec.get("message_id", str(uuid.uuid4())),
                    source_file=str(pmp),
                    source_type="pending_message",
                    theme=theme,
                    category=_classify_category(theme, 1),
                    created_at=created,
                    priority=rec.get("priority"),
                    provenance_ref=rec.get("message_id", ""),
                    extra={"queue_type": rec.get("queue_type", "unknown")},
                ))

    # --- missions.jsonl ---
    mip = weslr / "missions.jsonl"
    if mip.exists():
        seen_missions: set[str] = set()
        for line in _read_lines(mip):
            rec = json.loads(line)
            mission_id = rec.get("mission_id", "")
            if not mission_id or mission_id in seen_missions:
                continue
            created = rec.get("created_at")
            last_reviewed = rec.get("last_reviewed_at", created)
            if not _is_within_hours(last_reviewed or created, hours * 2):
                continue
            seen_missions.add(mission_id)

            title = rec.get("title", "")
            research_goal = rec.get("research_goal", "")
            questions = rec.get("current_questions", [])
            theme = _extract_theme(f"{title} {research_goal} {' '.join(questions)}")

            traces.append(Trace(
                id=mission_id,
                source_file=str(mip),
                source_type="mission",
                theme=theme,
                category="mission_progress",
                mission_id=mission_id,
                created_at=created,
                provenance_ref=mission_id,
                extra={
                    "title": _truncate(title, 100),
                    "questions_count": len(questions),
                    "status": rec.get("status", "unknown"),
                },
            ))

    return traces


def _read_lines(path: pathlib.Path) -> iter:
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield line
    except (OSError, IOError):
        return


def _truncate(text: str, max_chars: int) -> str:
    """Truncate long text, never store raw content."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


# ---------------------------------------------------------------------------
# Phase 2: Cluster
# ---------------------------------------------------------------------------

def cluster_traces(traces: list[Trace]) -> list[Cluster]:
    """
    Group traces into clusters by theme + mission_id.
    Traces with no mission_id are grouped by theme only.
    """
    key_map: dict[tuple, list[Trace]] = {}

    for t in traces:
        key = (t.theme, t.mission_id)
        if key not in key_map:
            key_map[key] = []
        key_map[key].append(t)

    clusters: list[Cluster] = []
    for (theme, mission_id), group in key_map.items():
        if not group:
            continue
        cluster_id = str(uuid.uuid4())[:8]
        label = theme if not mission_id else f"{theme}_mission"
        clusters.append(Cluster(id=cluster_id, theme=label, traces=group))

    return clusters


# ---------------------------------------------------------------------------
# Phase 3: Score
# ---------------------------------------------------------------------------

def score_cluster(cluster: Cluster) -> dict:
    """Score a cluster on frequency, recency, source diversity, confidence."""
    traces = cluster.traces
    if not traces:
        return {"frequency": 0, "recency": None,
                "source_diversity": 0, "avg_confidence": 0.0, "overall": 0.0}

    n = len(traces)
    sources = list({t.source_type for t in traces})
    confidences = [t.confidence for t in traces if t.confidence is not None]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.5

    recency_ts = cluster.last_seen
    recency_score = 1.0
    if recency_ts:
        try:
            dt = datetime.fromisoformat(recency_ts.replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
            recency_score = max(0.0, 1.0 - (age_hours / (24 * 30)))  # decay over 30 days
        except (ValueError, AttributeError):
            recency_score = 0.5

    diversity_score = min(1.0, len(sources) / 3.0)
    frequency_score = min(1.0, n / 10.0)

    overall = (
        frequency_score * 0.3 +
        recency_score * 0.3 +
        diversity_score * 0.2 +
        avg_conf * 0.2
    )

    return {
        "frequency": n,
        "recency": recency_ts,
        "source_diversity": len(sources),
        "avg_confidence": round(avg_conf, 3),
        "overall": round(overall, 3),
    }


# ---------------------------------------------------------------------------
# Phase 4: Classify Destination
# ---------------------------------------------------------------------------

def classify_destination(cluster: Cluster) -> tuple[str, str, str]:
    """
    Classify proposed destination for a cluster.
    Returns (destination, risk_level, gate_note).

    V1 destinations: mission_store | evidence_hypothesis | proposal_review |
                     entity_memory | continuity | archive_only | validation_gap | general
    """
    theme = cluster.theme
    category = cluster.category
    mission_count = len(cluster.mission_ids)
    trace_count = len(cluster.traces)

    # Mission-related clusters
    if category == "mission_progress" or "mission" in theme:
        if mission_count > 0:
            return ("mission_store", "low",
                    f"Active mission tracking ({trace_count} traces, {mission_count} missions)")
        return ("mission_store", "medium",
                f"Mission-related cluster ({trace_count} traces)")

    # Evidence gaps
    if category == "evidence_gap" or "evidence" in theme:
        return ("evidence_hypothesis", "low",
                f"Evidence gap cluster ({trace_count} traces) — candidate for evidence packet")

    # Research questions
    if category == "research_question":
        return ("evidence_hypothesis", "medium",
                f"Research question cluster ({trace_count} traces) — needs evidence backing")

    # Proposals
    if category == "proposal":
        return ("proposal_review", "medium",
                f"Proposal cluster ({trace_count} traces) — requires operator review")

    # Governance/doctrine — never promote in V1
    if category == "governance" or "doctrine" in theme or "governance" in theme:
        return ("validation_gap", "high",
                f"Governance/doctrine theme detected — requires explicit review, no auto-promotion")

    # Memory consolidation — low risk
    if category == "continuity" or "memory" in theme or "continuity" in theme:
        return ("entity_memory", "low",
                f"Memory/continuity cluster ({trace_count} traces) — operator_review recommended")

    # General / weak clusters
    if trace_count <= 1:
        return ("archive_only", "low",
                f"Single trace, no repetition — no promotion value")

    return ("general", "medium",
            f"General cluster ({trace_count} traces) — review before action")


# ---------------------------------------------------------------------------
# Phase 5-6: Build Candidate + Write Digest
# ---------------------------------------------------------------------------

def make_candidate(cluster: Cluster) -> ConsolidationCandidate:
    """Build a ConsolidationCandidate from a Cluster."""
    score = score_cluster(cluster)
    proposed_dest, risk_level, gate_note = classify_destination(cluster)

    # Provenance: list of source trace refs (no raw content)
    provenance = []
    for t in cluster.traces:
        ref = t.provenance_ref or t.id
        if ref not in provenance:
            provenance.append(ref)
        if len(provenance) >= 10:
            break

    sources = list({t.source_type for t in cluster.traces})

    op_action = risk_level in ("high", "medium") or proposed_dest in (
        "evidence_hypothesis", "proposal_review", "validation_gap")

    return ConsolidationCandidate(
        cluster_id=cluster.id,
        theme=cluster.theme,
        trace_count=len(cluster.traces),
        first_seen=cluster.first_seen,
        last_seen=cluster.last_seen,
        sources=sources,
        score=score,
        proposed_destination=proposed_dest,
        risk_level=risk_level,
        provenance=provenance,
        gate_note=gate_note,
        operator_action_required=op_action,
    )


def write_digest(candidates: list[ConsolidationCandidate],
                 root: str | None = None) -> tuple[str, str, int]:
    """
    Append candidates to consolidation_digest.jsonl.
    Returns (output_dir, output_file, count).
    """
    out_dir = pathlib.Path(root) / ".weslr" if root else _ROOT
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / _DIGEST_FILENAME

    count = 0
    with open(out_path, "a", encoding="utf-8") as f:
        for cand in candidates:
            f.write(json.dumps(cand.to_dict(), ensure_ascii=False) + "\n")
            count += 1

    return str(out_dir), _DIGEST_FILENAME, count


# ---------------------------------------------------------------------------
# Phase 7: Run
# ---------------------------------------------------------------------------

def run_consolidation_digest(root: str | None = None,
                              hours: int = 24) -> ConsolidationDigestResult:
    """
    Run the full consolidation digest pipeline:
    collect → cluster → score → classify → write digest.

    V1: read-only, no promotion.
    """
    # Phase 1: Collect
    traces = collect_traces(root=root, hours=hours)

    # Phase 2: Cluster
    clusters = cluster_traces(traces)

    # Phase 3-4: Score + classify → candidates
    candidates: list[ConsolidationCandidate] = []
    for cluster in clusters:
        if cluster.traces:  # skip empty
            candidates.append(make_candidate(cluster))

    # Phase 6: Write digest
    out_dir, out_file, written = write_digest(candidates, root=root)

    return ConsolidationDigestResult(
        traces_collected=len(traces),
        clusters_found=len(clusters),
        candidates_written=written,
        output_path=str(out_dir),
        output_file=out_file,
        digest_records=[c.to_dict() for c in candidates],
    )


# ---------------------------------------------------------------------------
# CLI helpers (used by commands module)
# ---------------------------------------------------------------------------

def build_text_summary(result: ConsolidationDigestResult) -> str:
    """Build human-readable digest summary."""
    lines = [
        "=== WESLR Consolidation Digest ===",
        f"traces_collected={result.traces_collected}",
        f"clusters_found={result.clusters_found}",
        f"candidates_written={result.candidates_written}",
        f"output={pathlib.Path(result.output_path) / result.output_file}",
        f"promotion_performed={False}",
        "",
    ]

    by_dest: dict[str, list[dict]] = {}
    for rec in result.digest_records:
        dest = rec["proposed_destination"]
        if dest not in by_dest:
            by_dest[dest] = []
        by_dest[dest].append(rec)

    for dest, recs in sorted(by_dest.items()):
        lines.append(f"--- {dest} ({len(recs)}) ---")
        for rec in recs:
            lines.append(
                f"  [{rec['cluster_id']}] {rec['theme']} "
                f"(traces={rec['trace_count']}, risk={rec['risk_level']}, "
                f"action_required={rec['operator_action_required']})"
            )
            lines.append(f"    note: {rec['gate_note']}")

    return "\n".join(lines)
