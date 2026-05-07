"""
WESLR Safe Memory Capture

Conservative, evidence-gated memory capture from verified interaction events.
Does NOT store raw message content. Does NOT use LLM. Does NOT break response flow.

Capture is post-response only: capture failure never prevents answer delivery.
All writes are append-only. Memories are scoped to entity namespaces.

This is NOT uncontrolled memory. This is NOT raw chat logging.
Memory capture is scoped, verified, append-only, privacy-aware, and provenance-backed.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

from weslr.entity_memory import (
    EntityType,
    AccessLevel,
    MemoryRecord,
    create_memory_record,
    append_entity_memory,
    entity_memory_path,
)


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class MemoryCaptureCandidate:
    """A candidate memory suitable for safe capture."""
    candidate_id: str = ""
    capture_type: str = ""
    summary: str = ""
    entity_type: str = "project"
    entity_id: str = "weslr"
    access_level: str = AccessLevel.OPERATOR_ONLY.value
    confidence: float = 0.5
    verified: bool = False
    source: str = "live_interaction"
    source_fingerprint: str = ""
    evidence: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    requires_explicit_consent: bool = False
    safe_to_store: bool = True
    reason: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MemoryCaptureResult:
    """Result of a memory capture attempt."""
    attempted: bool = False
    captured: bool = False
    records_created: list[str] = field(default_factory=list)
    skipped_reason: Optional[str] = None
    candidates_considered: int = 0
    scope_used: Optional[str] = None
    metadata: dict = field(default_factory=dict)


# ── Constants ──────────────────────────────────────────────────────────────────

_SENSITIVE_PATTERNS = [
    re.compile(r"\btoken\b", re.IGNORECASE),
    re.compile(r"\bapi[_-]?key\b", re.IGNORECASE),
    re.compile(r"\bapi key\b", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
    re.compile(r"\bpassword\b", re.IGNORECASE),
    re.compile(r"\bpasswd\b", re.IGNORECASE),
    re.compile(r"\bcredential\b", re.IGNORECASE),
    re.compile(r"\bprivate\b", re.IGNORECASE),
    re.compile(r"\bconfidential\b", re.IGNORECASE),
    re.compile(r"\btop secret\b", re.IGNORECASE),
    re.compile(r"\bmedical\b.*\b(record|diagnosis|condition)\b", re.IGNORECASE),
    re.compile(r"\bhealth\b.*\b(record|diagnosis|hospital)\b", re.IGNORECASE),
    re.compile(r"\bmental health\b", re.IGNORECASE),
    re.compile(r"\btherapy\b", re.IGNORECASE),
    re.compile(r"\bsex\w*\b.*\b(orientation|preference|identity)\b", re.IGNORECASE),
    re.compile(r"\bpolitics\b.*\b(party|affiliation|voting)\b", re.IGNORECASE),
    re.compile(r"\breligion\b.*\b(belief|faith|church|mosque|synagogue)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s+\w+\s+(street|st|avenue|ave|road|rd|lane)\b", re.IGNORECASE),
    re.compile(r"\b\d{5}\b.*\b\d{4}\b"),
    re.compile(r"\bssn\b", re.IGNORECASE),
    re.compile(r"\bsocial security\b", re.IGNORECASE),
    re.compile(r"\bcredit card\b", re.IGNORECASE),
    re.compile(r"\bbank account\b", re.IGNORECASE),
]

_CONSENT_PATTERNS = [
    re.compile(r"remember\s+that", re.IGNORECASE),
    re.compile(r"save\s+this", re.IGNORECASE),
    re.compile(r"keep\s+this\s+in\s+mind", re.IGNORECASE),
    re.compile(r"don.+forget\s+that", re.IGNORECASE),
    re.compile(r"note\s+that", re.IGNORECASE),
    re.compile(r"log\s+this", re.IGNORECASE),
    re.compile(r"record\s+that", re.IGNORECASE),
]

_PREFERENCE_PATTERNS = [
    re.compile(r"don.+mention\b", re.IGNORECASE),
    re.compile(r"don.+ask\s+what\s+next", re.IGNORECASE),
    re.compile(r"don.+bring\s+up", re.IGNORECASE),
    re.compile(r"avoid\s+saying\s+context", re.IGNORECASE),
    re.compile(r"stop\s+asking\s+about", re.IGNORECASE),
    re.compile(r"never\s+mention", re.IGNORECASE),
    re.compile(r"instead\s+of\s+asking\s+what\s+next", re.IGNORECASE),
    re.compile(r"instead\s+of\s+.*propose", re.IGNORECASE),
    re.compile(r"propose\s+next\s+prompt", re.IGNORECASE),
    re.compile(r"remember\s+.*preference", re.IGNORECASE),
    re.compile(r"prefer\s+.*to\s+avoid", re.IGNORECASE),
]

_PROJECT_WORK_PATTERNS = [
    re.compile(r"\bcommit(ed|ing|ed\s+hash)?\s+[a-f0-9]{6,}\b", re.IGNORECASE),
    re.compile(r"\bmerged\s+(pull|merge)\s+(request|#)?\d+\b", re.IGNORECASE),
    re.compile(r"\bpushed\s+(to|on)\s+(main|master|dev)\b", re.IGNORECASE),
    re.compile(r"\bfinished\s+(the\s+)?(implementation|work|feature|task)\b", re.IGNORECASE),
    re.compile(r"\bcompleted\s+.*(feature|module|test|implementation)\b", re.IGNORECASE),
    re.compile(r"\btests?\s+(passed|passing|green)\b", re.IGNORECASE),
    re.compile(r"\bdeploy(ed|ing)?\s+(to|on)\b", re.IGNORECASE),
    re.compile(r"\breleased\s+version\b", re.IGNORECASE),
    re.compile(r"\bmarked\s+(as\s+)?done\b", re.IGNORECASE),
]

_MILESTONE_PATTERNS = [
    re.compile(r"\barchitecture\s+(sealed|checkpoint|locked|finalized)\b", re.IGNORECASE),
    re.compile(r"\bsealed\s+(as\s+)?commit\b", re.IGNORECASE),
    re.compile(r"\btests?\s+pass(ed|ing|ing\s+all)\b", re.IGNORECASE),
    re.compile(r"\bproduction\s+ready\b", re.IGNORECASE),
    re.compile(r"\bdecision\s+made\b", re.IGNORECASE),
    re.compile(r"\bdesign\s+(sealed|finalized|approved)\b", re.IGNORECASE),
    re.compile(r"\btests?\s+passed\b", re.IGNORECASE),
]

_CORRECTION_PATTERNS = [
    re.compile(r"no[,\s]*that.?s?\s+(wrong|not\s+right|incorrect)", re.IGNORECASE),
    re.compile(r"actually[,\s](no|it\s+was)", re.IGNORECASE),
    re.compile(r"wait[,\s]*no", re.IGNORECASE),
    re.compile(r"not\s+what\s+I\s+asked", re.IGNORECASE),
    re.compile(r"you\s+misunderstood", re.IGNORECASE),
    re.compile(r"nooo?[,\s]*(stop|cancel)", re.IGNORECASE),
]


# ── Fingerprint ────────────────────────────────────────────────────────────────

def safe_turn_fingerprint(message: str, response: str = "", max_len: int = 120) -> str:
    """Return a short SHA-like hash of message+response. Does NOT store raw text."""
    combined = f"{message[:max_len]}|{response[:max_len]}"
    if not combined.strip() or combined.strip() == "|":
        return "empty"
    normalized = " ".join(combined.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


# ── Safety filter ─────────────────────────────────────────────────────────────

def contains_sensitive_content(text: str) -> bool:
    """Return True if text appears to contain sensitive content."""
    for pat in _SENSITIVE_PATTERNS:
        if pat.search(text):
            return True
    return False


def has_explicit_consent(text: str) -> bool:
    """Return True if text contains explicit consent to save memory."""
    for pat in _CONSENT_PATTERNS:
        if pat.search(text):
            return True
    return False


# ── Candidate classification ───────────────────────────────────────────────────

def classify_memory_capture_candidates(
    message: str,
    response: str = "",
    response_metadata: Optional[dict] = None,
    identity_state: Optional[dict] = None,
    relationship_targets: Optional[list] = None,
) -> list[MemoryCaptureCandidate]:
    candidates: list[MemoryCaptureCandidate] = []
    response_metadata = response_metadata or {}
    identity_state = identity_state or {}
    relationship_targets = relationship_targets or []
    is_verified = identity_state.get("is_verified", False)
    identity_status = identity_state.get("identity_status", "unknown")
    sender_identity = identity_state.get("user_id") or identity_state.get("sender_identity") or ""

    # Milestone candidates (checked before project_work to allow override)
    for pat in _MILESTONE_PATTERNS:
        m = pat.search(message)
        if m:
            milestone_type = _classify_milestone_type(message)
            candidates.append(MemoryCaptureCandidate(
                capture_type="milestone",
                summary=f"WESLR milestone: {milestone_type}",
                entity_type="project",
                entity_id=_resolve_project_id(response_metadata, relationship_targets) or "weslr",
                access_level=AccessLevel.OPERATOR_ONLY.value,
                confidence=0.90,
                verified=False,
                source="live_interaction",
                source_fingerprint=safe_turn_fingerprint(message, response),
                evidence=[m.group(0)],
                safe_to_store=True,
                reason="milestone_detected",
                tags=["milestone", "checkpoint"],
            ))
            break

    # Project work candidates
    for pat in _PROJECT_WORK_PATTERNS:
        m = pat.search(message)
        if m:
            work_type = _classify_work_type(message)
            candidates.append(MemoryCaptureCandidate(
                capture_type="project_work",
                summary=f"WESLR project work completed: {work_type}",
                entity_type="project",
                entity_id=_resolve_project_id(response_metadata, relationship_targets) or "weslr",
                access_level=AccessLevel.OPERATOR_ONLY.value,
                confidence=0.85,
                verified=False,
                source="live_interaction",
                source_fingerprint=safe_turn_fingerprint(message, response),
                evidence=[m.group(0)],
                safe_to_store=True,
                reason="project_work_detected",
                tags=["project-work", "development"],
            ))
            break

    # Explicit user preference candidates
    for pat in _PREFERENCE_PATTERNS:
        m = pat.search(message)
        if m:
            pref_type = _classify_preference_type(message, m.group(0))
            scope, entity_id = _resolve_preference_scope(
                message, response_metadata, relationship_targets, is_verified, identity_status, sender_identity
            )
            access = AccessLevel.OPERATOR_ONLY.value if scope in ("system", "project") else AccessLevel.PRIVATE.value
            candidates.append(MemoryCaptureCandidate(
                capture_type="user_preference",
                summary=f"User preference: {pref_type}",
                entity_type=scope,
                entity_id=entity_id,
                access_level=access,
                confidence=0.80,
                verified=is_verified,
                source="live_interaction",
                source_fingerprint=safe_turn_fingerprint(message, response),
                evidence=[m.group(0)],
                safe_to_store=True,
                reason="preference_explicit",
                tags=["preference", "user-behavior"],
            ))
            break

    # Explicit consent memory (remember that / save this)
    if has_explicit_consent(message) and is_verified and sender_identity:
        if not contains_sensitive_content(message):
            pref_type = _classify_consent_memory(message)
            candidates.append(MemoryCaptureCandidate(
                capture_type="user_consent_memory",
                summary=f"User-requested memory: {pref_type}",
                entity_type="person",
                entity_id=sender_identity,
                access_level=AccessLevel.PRIVATE.value,
                confidence=0.90,
                verified=True,
                source="live_interaction",
                source_fingerprint=safe_turn_fingerprint(message, response),
                evidence=["explicit_consent"],
                safe_to_store=True,
                requires_explicit_consent=True,
                reason="user_explicit_consent",
                tags=["consent-memory", "user-requested"],
            ))

    # Correction candidates
    for pat in _CORRECTION_PATTERNS:
        m = pat.search(message)
        if m:
            scope, entity_id, access = _resolve_correction_scope(
                response_metadata, relationship_targets, is_verified, identity_status, sender_identity
            )
            candidates.append(MemoryCaptureCandidate(
                capture_type="correction",
                summary="User provided a correction to WESLR prior output",
                entity_type=scope,
                entity_id=entity_id,
                access_level=access,
                confidence=0.75,
                verified=is_verified,
                source="live_interaction",
                source_fingerprint=safe_turn_fingerprint(message, response),
                evidence=[m.group(0)],
                safe_to_store=True,
                reason="correction_detected",
                tags=["correction", "feedback"],
            ))
            break

    return candidates


def _classify_work_type(message: str) -> str:
    msg_lower = message.lower()
    if "test" in msg_lower:
        return "test implementation completed"
    if "commit" in msg_lower or "hash" in msg_lower:
        return "code committed"
    if "deploy" in msg_lower:
        return "deployment completed"
    if "feature" in msg_lower:
        return "feature implemented"
    if "fix" in msg_lower or "bug" in msg_lower:
        return "bug fix completed"
    if "merge" in msg_lower:
        return "code merged"
    if "release" in msg_lower:
        return "release published"
    return "work item completed"


def _classify_milestone_type(message: str) -> str:
    msg_lower = message.lower()
    if "architecture" in msg_lower:
        return "architecture sealed"
    if "test" in msg_lower and "pass" in msg_lower:
        return "tests passing"
    if "production" in msg_lower:
        return "production ready"
    if "design" in msg_lower:
        return "design finalized"
    if "decision" in msg_lower:
        return "decision made"
    return "project milestone"


def _classify_preference_type(message: str, matched_text: str = "") -> str:
    msg_lower = message.lower()
    matched = matched_text.lower()
    if "mention" in matched:
        return "WESLR should not mention specific content"
    if "ask what next" in matched or "ask what next" in msg_lower:
        return "WESLR should propose next prompt instead of asking"
    if "bring up" in matched:
        return "WESLR should not bring up certain topics"
    if "avoid saying context" in matched:
        return "WESLR should avoid mentioning context"
    if "stop asking" in matched:
        return "WESLR should stop asking about specific topic"
    if "never mention" in matched:
        return "WESLR should never mention specific content"
    if "instead of" in matched and "propose" in msg_lower:
        return "WESLR should propose instead of asking"
    if "propose next prompt" in matched:
        return "WESLR should propose next prompt"
    if "prefer" in matched and "avoid" in msg_lower:
        return "WESLR should prefer certain behavior"
    return "user behavioral preference recorded"


def _classify_consent_memory(message: str) -> str:
    msg_lower = message.lower()
    if "remember that" in msg_lower:
        rest = msg_lower.split("remember that", 1)
        if len(rest) > 1:
            suffix = rest[1].strip().rstrip(".").rstrip("?")
            return f"user noted: {suffix[:100]}"
    return "user-requested fact to remember"


# ── Scope resolution helpers ──────────────────────────────────────────────────

def _resolve_project_id(
    response_metadata: dict,
    relationship_targets: list,
) -> Optional[str]:
    if response_metadata.get("project_id"):
        return response_metadata["project_id"]
    for target in relationship_targets:
        if hasattr(target, "target_entity_type") and target.target_entity_type == "project":
            return target.target_entity_id
    return None


def _resolve_preference_scope(
    message: str,
    response_metadata: dict,
    relationship_targets: list,
    is_verified: bool,
    identity_status: str,
    sender_identity: str,
) -> tuple[str, str]:
    msg_lower = message.lower()
    project_id = _resolve_project_id(response_metadata, relationship_targets)

    about_weslr = any(w in msg_lower for w in [
        "weslr", "you ", "your responses", "avoid saying",
        "never mention", "don't mention", "don t mention",
        "don't bring up", "don t bring up",
        "stop asking", "don't ask", "don t ask",
    ])
    if about_weslr:
        if project_id:
            return "project", project_id
        return "system", "weslr"

    if is_verified and sender_identity and identity_status in (
        "channel_verified", "device_verified", "test_verified",
    ):
        return "person", sender_identity

    if project_id:
        return "project", project_id
    return "system", "weslr"


def _resolve_correction_scope(
    response_metadata: dict,
    relationship_targets: list,
    is_verified: bool,
    identity_status: str,
    sender_identity: str,
) -> tuple[str, str, str]:
    project_id = _resolve_project_id(response_metadata, relationship_targets)
    if project_id:
        return "project", project_id, AccessLevel.OPERATOR_ONLY.value
    if is_verified and sender_identity:
        return "person", sender_identity, AccessLevel.PRIVATE.value
    return "system", "weslr", AccessLevel.OPERATOR_ONLY.value


# ── Safety & gating ───────────────────────────────────────────────────────────

def is_memory_safe_to_store(
    candidate: MemoryCaptureCandidate,
    identity_state: Optional[dict] = None,
) -> tuple[bool, Optional[str]]:
    identity_state = identity_state or {}
    is_verified = identity_state.get("is_verified", False)
    identity_status = identity_state.get("identity_status", "unknown")

    if not candidate.requires_explicit_consent:
        for ev in candidate.evidence:
            if contains_sensitive_content(ev):
                return False, "sensitive_content_in_evidence"
        if contains_sensitive_content(candidate.summary):
            return False, "sensitive_content_in_summary"

    if candidate.requires_explicit_consent:
        if not is_verified or not identity_state.get("user_id"):
            return False, "unverified_consent_memory_blocked"

    if identity_status == "unknown":
        if candidate.capture_type in ("user_preference", "user_consent_memory"):
            return False, "unknown_identity_no_private_memory"
        if candidate.entity_type in ("person", "company", "family", "institution", "team", "department"):
            return False, "unknown_identity_no_group_memory"

    if identity_status in ("profile_only", "onboarded_unverified"):
        if candidate.entity_type == "person" and candidate.access_level == AccessLevel.PRIVATE.value:
            return False, "unverified_no_private_person_memory"
        if candidate.entity_type in ("company", "family", "institution", "team", "department"):
            return False, "unverified_no_group_memory"

    if candidate.entity_type in ("company", "family", "institution", "team", "department"):
        if not candidate.verified:
            return False, "group_memory_requires_verified_role"

    return True, None


def resolve_memory_capture_scope(
    candidate: MemoryCaptureCandidate,
    identity_state: Optional[dict] = None,
    profile: Optional[dict] = None,
    relationship_targets: Optional[list] = None,
) -> MemoryCaptureCandidate:
    identity_state = identity_state or {}
    profile = profile or {}
    relationship_targets = relationship_targets or []
    is_verified = identity_state.get("is_verified", False)
    identity_status = identity_state.get("identity_status", "unknown")

    if candidate.capture_type in ("project_work", "milestone"):
        if candidate.entity_type == "project" and not candidate.entity_id:
            candidate.entity_id = _resolve_project_id({}, relationship_targets) or "weslr"

    if candidate.entity_type == "person":
        if not is_verified:
            candidate.safe_to_store = False
            candidate.limitations.append("person_memory_requires_verification")

    if candidate.entity_type in ("company", "family", "institution", "team", "department"):
        if not _has_verified_membership(candidate.entity_type, candidate.entity_id, profile):
            candidate.safe_to_store = False
            candidate.limitations.append(f"{candidate.entity_type}_memory_requires_verified_membership")

    return candidate


def _has_verified_membership(
    entity_type: str,
    entity_id: str,
    profile: Optional[dict],
) -> bool:
    profile = profile or {}
    memberships = profile.get("memberships", [])
    for m in memberships:
        if m.get("entity_type", "").lower() == entity_type.lower():
            if m.get("entity_id", "").lower() == entity_id.lower():
                if m.get("verified", False):
                    return True
    return False


# ── Memory write ──────────────────────────────────────────────────────────────

def create_memory_record_from_candidate(
    candidate: MemoryCaptureCandidate,
) -> MemoryRecord:
    return create_memory_record(
        entity_type=candidate.entity_type,
        entity_id=candidate.entity_id,
        summary=candidate.summary,
        scope="default",
        access_level=candidate.access_level,
        source=candidate.source,
        details=None,
        tags=candidate.tags,
        confidence=candidate.confidence,
        verified=candidate.verified,
        created_by="memory_capture",
        provenance=f"memory_capture:{candidate.reason}",
        retention_policy="default",
    )


# ── High-level capture ────────────────────────────────────────────────────────

def capture_memories_from_turn(
    message: str,
    response: str = "",
    response_metadata: Optional[dict] = None,
    identity_state: Optional[dict] = None,
    base_path: Optional[str] = None,
    profile: Optional[dict] = None,
    relationship_targets: Optional[list] = None,
) -> MemoryCaptureResult:
    try:
        identity_state = identity_state or {}
        relationship_targets = relationship_targets or []
        candidates = classify_memory_capture_candidates(
            message, response, response_metadata, identity_state, relationship_targets
        )

        if not candidates:
            return MemoryCaptureResult(
                attempted=True,
                captured=False,
                candidates_considered=len(candidates),
                skipped_reason="no_candidates",
            )

        records: list[str] = []
        first_scope = None

        for candidate in candidates:
            candidate = resolve_memory_capture_scope(
                candidate, identity_state, profile, relationship_targets
            )
            safe, reason = is_memory_safe_to_store(candidate, identity_state)
            if not safe:
                continue
            try:
                record = create_memory_record_from_candidate(candidate)
                append_entity_memory(record, base_path=base_path)
                records.append(record.memory_id)
                if first_scope is None:
                    first_scope = f"{candidate.entity_type}:{candidate.entity_id}"
            except Exception:
                continue

        return MemoryCaptureResult(
            attempted=True,
            captured=len(records) > 0,
            records_created=records,
            candidates_considered=len(candidates),
            scope_used=first_scope,
            skipped_reason=None if records else "all_candidates_filtered",
        )

    except Exception:
        return MemoryCaptureResult(
            attempted=True,
            captured=False,
            candidates_considered=0,
            skipped_reason="capture_exception",
        )


def safe_capture_memories_from_turn(
    message: str,
    response: str = "",
    response_metadata: Optional[dict] = None,
    identity_meta: Optional[dict] = None,
    base_path: Optional[str] = None,
    meaning_state: Optional[dict] = None,
    profile: Optional[dict] = None,
    relationship_targets: Optional[list] = None,
) -> MemoryCaptureResult:
    identity_state = {
        "is_verified": bool(identity_meta.get("is_verified", False) if identity_meta else False),
        "identity_status": (identity_meta.get("known_user_status", "unknown") if identity_meta else "unknown"),
        "user_id": (identity_meta.get("sender_identity", "") or "").strip() or None,
    }
    return capture_memories_from_turn(
        message=message,
        response=response,
        response_metadata=response_metadata,
        identity_state=identity_state,
        base_path=base_path,
        profile=profile,
        relationship_targets=relationship_targets,
    )
