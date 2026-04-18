"""Evidence Intake Module - Phase A

v94c Phase A: Evidence Assimilation (Narrower Slice)
- Evidence source metadata and reference handling
- Normalized evidence schema
- Evidence proposal payload generation
- Ingestion pipeline: parse_external → normalize → generate_proposal_payload

No governance hooks, no application path, no external parsers in Phase A.
"""

__all__ = ["EvidenceSource", "NormalizedEvidence", "EvidenceProposalPayload", "EvidenceIngestion"]

from .models import EvidenceSource, NormalizedEvidence, EvidenceProposalPayload
from .ingestion import EvidenceIngestion
