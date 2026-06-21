# WESLR Controlled Source Access Adapter Boundary V1 Design

## 1. Purpose and Scope
This design defines the boundary for controlled source-access adapters in WESLR. These adapters serve as intermediaries connecting authorized source-locator metadata to source-ingestion execution packets in a governed, safe, and metadata-only fashion. The boundary restricts direct source content access and enforces strict policies for source metadata, access, privacy, and operator observability.

## 2. Necessity of This Boundary
After the source-ingestion execution packet helper, we need this boundary to ensure the controlled, authorized, and verifiable transition from source locator metadata to managed source access metadata. It isolates source access logic from ingestion and interpretation layers, enforcing fail-closed protections and preventing unauthorized content ingestion or runtime impact.

## 3. Key Definitions
- **Source Locator Metadata:** Metadata describing the location, type, and authorization of a source.
- **Source Access Adapter:** A controlled adapter implementing authorized access methods to source metadata without fetching or ingesting actual source content.
- **Source Ingestion Execution Packet:** Packet preparing source content ingestion, downstream from source access adapters.
- **Source Interpretation Packet:** Packet derived from ingestion packets to interpret or analyze source content metadata.
- **Evidence Intake Packet:** Metadata and data packet designed to intake collected evidence.
- **Normalized Evidence Packet:** Structured evidence metadata normalized for analysis and storage.

## 4. Allowed Future Adapter Classes (Design-Only)
- Public URL Metadata Adapter
- Public Webpage Bounded-Access Adapter
- Public PDF Bounded-Access Adapter
- Public Dataset Metadata Adapter
- GitHub Repository Metadata Adapter
- Owner-Uploaded File Adapter
- Owner-Pasted Text Adapter
- Authorized Local File Adapter
- SearXNG Result Metadata Adapter

## 5. Explicitly Blocked Adapter Classes
- Private Account Sources
- Secrets, Tokens, Authentication Files
- Private Memory
- ".weslr" Files
- Hidden Prompts
- Protected Benchmark Items
- Copyrighted Bulk Extraction
- Scraping Behind Login
- User-Private Files Without Explicit Authorization

## 6. Adapter Preflight Requirements
- Owner Authorization
- Source Class Identification
- Source Locator Record Verification
- Access Method Declaration
- Expected Content Type
- License and Access Posture Assessment
- Retention Posture Specification
- Privacy Posture Specification
- Provenance Posture Verification
- Allowed Extraction Depth
- Maximum Content Size
- Explicit No Instruction Authority from Source Content

## 7. Adapter Output Contract
- Metadata-Only Result
- Bounded Content Reference
- Source Hash or Locator Fingerprint
- Provenance Labels
- Access Timestamp
- Redaction Status
- Blocked or Allowed Status
- Reason Codes
- Next Safe Packet Target

## 8. Fail-Closed Statuses
- "blocked_missing_authorization"
- "blocked_unknown_source_class"
- "blocked_private_or_secret_source"
- "blocked_license_or_access_unclear"
- "blocked_content_too_large"
- "blocked_prompt_injection_risk"
- "blocked_untrusted_instruction_attempt"
- "blocked_missing_provenance"
- "ready_for_packet_only_ingestion"

## 9. Prompt-Injection and Hostile-Source Boundary
- Source content treated strictly as data, never as instructions
- No source may override WESLR, OCC, or operator instructions
- Adapter must tag suspicious instructions
- Adapter must not execute any source-provided commands

## 10. Privacy and Retention Boundary
Adapters enforce strict privacy protection and data retention policies, disallowing unauthorized retention or exposure.

## 11. License/Access Boundary
Adapters ensure licenses and access permissions are verified and adhered to before metadata is forwarded.

## 12. Provenance/Currentness Boundary
Adapters maintain provenance metadata to ensure source freshness and integrity.

## 13. Operator Observability Requirements
Adapters must log access attempts, status (allowed/blocked), reason codes, and timestamps to enable operator monitoring and audits.

## 14. Relationship to Future Implementation Helpers
This design is the foundation for forthcoming helper APIs that will facilitate adapter plan construction, validation, summarization, rendering, and serialization.

## 15. Future Helper APIs (Design-Only)
- build_controlled_source_access_adapter_plan_v1
- validate_controlled_source_access_adapter_plan_v1
- summarize_controlled_source_access_adapter_plan_v1
- render_controlled_source_access_adapter_plan_markdown_v1
- to_controlled_source_access_adapter_plan_json_safe_v1

## 16. Required Future Tests (Design-Only)
Comprehensive tests will cover adapter preflight validation, fail-closed enforcement, metadata output contracts, privacy and license boundaries, and operator observability.

## 17. Denied Authority
This design explicitly denies the following for all source access adapters:
- No source access execution
- No ingestion execution
- No accepted evidence creation
- No accepted candidate creation
- No final answer or public claim generation
- No runtime wiring

## 18. Abort Conditions
Adapters must abort plan execution or data forwarding on detection of any policy violations, missing authorization, or suspicious source behavior.

## 19. Recommended Next Lane
REVIEW_WESLR_CONTROLLED_SOURCE_ACCESS_ADAPTER_BOUNDARY_V1

---

*This document serves as the controlled source access adapter boundary design artifact for WESLR. No runtime actions are performed or authorized by this design.*
