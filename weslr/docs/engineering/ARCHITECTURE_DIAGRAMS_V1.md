# WESLR Architecture Diagrams — V1

**Version:** 1.0
**Status:** active reference
**Created:** 2026-04-27

All diagrams use [Mermaid](https://mermaid.js.org/) syntax. Render in any Mermaid-compatible viewer (GitHub, GitLab, Mermaid Live Editor).

---

## D1 — High-Level WESLR Layer Diagram

```mermaid
flowchart TB
    subgraph WESLR["WESLR — Entity Intelligence Platform"]
        subgraph FrontDoor["W1 — Front Door"]
            FW[interpret_human_turn]
            DD[Deterministic Dispatch<br/>dispatch_deterministic_handler]
        end

        subgraph CoreLayers["Core Layers"]
            C1[Self Description]
            C2[Capabilities]
            C3[Capability Gaps]
            C4[Proposal Creation]
            C5[Proposal Ranking]
            C6[Proposal Approval]
        end

        subgraph Traceability["C7 / C8 / C9 — Traceability"]
            PT[proposal_traceability.py<br/>proposal_trace.jsonl]
            IP[implementation_planning.py<br/>implementation_plans.jsonl]
            CD[Cross-Reference]
        end

        subgraph ISS["ISS — Internal Sensing System"]
            PR[probe_registry.py<br/>4 probe stubs]
            PP[probe_planning.py]
            PE[probe_execution.py<br/>simulated only]
            DR[diagnostic_records.py<br/>iss_diagnostic_records.jsonl]
        end

        subgraph Registry["Handler Registry"]
            HR[weslr/deterministic_handlers.py<br/>HANDLER_REGISTRY]
        end

        subgraph Formatter["Response Formatter"]
            RF[weslr/response_formatter.py<br/>build_deterministic_response]
        end
    end

    OpenClaw["OpenClaw Runtime"]
    Operator["Operator"]
    JSONL["JSONL Append-Only Logs<br/>3 files"]

    Operator -->|"webchat / command"| FW
    FW --> DD
    DD --> HR
    HR --> |ISS handlers| PP
    HR --> |ISS handlers| PR
    FW --> C1
    FW --> C2
    FW --> C3
    FW --> C4
    FW --> C5
    FW --> C6
    C4 --> PT
    C6 --> PT
    PT --> IP
    IP --> JSONL
    DR --> JSONL
    PT --> JSONL
    HR --> RF
    C1 --> RF
    C2 --> RF
    C3 --> RF
    OpenClaw --> FW
```

**Key:** WESLR sits on OpenClaw. Front door routes to deterministic dispatch or core layers. ISS is a self-contained subsystem that never executes. All state is append-only in JSONL.

---

## D2 — Proposal Lifecycle Diagram

```mermaid
stateDiagram-v2
    [*] --> Gap_Detected: ISS gap signal
    Gap_Detected --> Proposal_Created: operator accepts gap
    Proposal_Created --> Decision_Pending: record_proposal
    Decision_Pending --> Accepted: operator accepts
    Decision_Pending --> Rejected: operator rejects
    Decision_Pending --> Deferred: operator defers
    Accepted --> Plan_Created: create_implementation_plan
    Rejected --> [*]: logged only
    Deferred --> [*]: logged only
    Plan_Created --> [*]: recorded only

    note right of Proposal_Created: append-only<br/>proposal_trace.jsonl
    note right of Plan_Created: append-only<br/>implementation_plans.jsonl
    note right of Accepted: execution_allowed=False<br/>always
```

**Key:** Proposals are created by operator intake (ISS gap acceptance) or explicit command. Decisions are always operator-driven. Plans are created from accepted proposals but never executed in current phase. All transitions are logged.

---

## D3 — ISS Diagnostic Flow

```mermaid
flowchart LR
    subgraph ISS_Query["ISS Read-Only Query Path"]
        Q1["show iss probes"]
        Q2["show gaps"]
        Q3["show diagnostics"]
        Q4["show probe results"]
    end

    subgraph ISS_Probe["ISS Probe Subsystem (non-executing)"]
        REG[get_probe_registry<br/>4 probes defined]
        PLAN[create_probe_plan<br/>declarative plan]
    end

    subgraph ISS_Record["ISS Diagnostic Records"]
        DIAG[load_iss_diagnostics]
        PROBE[make_probe_result<br/>status: ok|degraded|missing|unknown]
        GAP[make_gap_signal<br/>severity: low|medium|high]
    end

    subgraph ISS_Execution["Simulated Execution"]
        SIM[execute_probe_simulated<br/>mode: simulated<br/>no real I/O]
        SIM --> |writes| DIAG
    end

    Q1 --> REG
    Q2 --> DIAG
    Q3 --> DIAG
    Q4 --> DIAG
    Q1 --> PLAN
    REG --> PLAN
    REG --> SIM
    SIM --> PROBE
    PROBE --> DIAG
    GAP --> DIAG

    DIAG --> JSONL["iss_diagnostic_records.jsonl<br/>append-only"]
```

**Key:** ISS has three modes: registry query (read), probe planning (declarative), simulated execution (writes one probe result). All execution is simulated. No real file inspection or network access.

---

## D4 — Handler Dispatch Flow

```mermaid
flowchart TB
    IN["interpret_human_turn(message)"]
    L["lowered = message.lower()"]

    IN --> L
    L --> DD["dispatch_deterministic_handler(message, lowered)"]

    DD --> SORT["sorted(HANDLER_REGISTRY, key=priority, reverse=True)"]
    SORT --> FOR_EACH["for entry in sorted_handlers"]
    FOR_EACH --> MATCH["entry.triggers × lowered.startswith?"]
    MATCH --> |match| FN["handler_fn(message, lowered)"]
    MATCH --> |no match| FOR_EACH
    FN --> RF["build_deterministic_response(...)"]

    RF --> OUT["return result dict"]

    note right of MATCH
        Priority ordering:
        85 = iss_probe_plan
        80 = iss_probe_registry_query
        50 = generic plan (if added)
    end

    note left of OUT
        Returns: message, response_text, path,
        _weslr_deterministic, confidence,
        suggested_mode, payload
    end
```

**Key:** Dispatch sorts the registry by priority descending before evaluation. First matching trigger wins. Returns via formatter for extracted handlers.

---

## D5 — Data Files / Append-Only Logs Diagram

```mermaid
flowchart TB
    subgraph Files["WESLR Data Files (Append-Only)"]
        T1["proposal_trace.jsonl"]
        T2["implementation_plans.jsonl"]
        T3["iss_diagnostic_records.jsonl"]
    end

    subgraph Writers["Write Functions"]
        W1["record_proposal / record_decision"]
        W2["record_implementation_plan"]
        W3["make_probe_result / make_gap_signal<br/>record_iss_diagnostic"]
    end

    subgraph Validators["Write-Side Validators"]
        V1["_validate_proposal_created / _validate_proposal_decision"]
        V2["_validate_implementation_plan"]
        V3["_validate_iss_diagnostic_record"]
    end

    subgraph Loaders["Read Functions (with isolation)"]
        R1["load_trace(limit) — try/except per line"]
        R2["load_implementation_plans(limit) — try/except per line"]
        R3["load_iss_diagnostics(limit) — try/except per line"]
    end

    subgraph Interpretation["interpretation.py Consumers"]
        C1["interpret_human_turn — reads T1/T2/T3"]
        C2["proposal/plan explanation — reads T1/T2"]
        C3["ISS query handlers — reads T3"]
    end

    W1 --> V1 --> T1
    W2 --> V2 --> T2
    W3 --> V3 --> T3

    T1 --> R1 --> C1
    T2 --> R2 --> C1
    T3 --> R3 --> C3

    T1 --> C2
    T2 --> C2
```

**Key:** All writes go through validators. All reads use line-level error isolation. No direct JSONL mutation. Each file is read by specific consumer handlers.

---

## Layer Status Summary

| Layer | ID | Status |
|---|---|---|
| Front Door | W1 | Active |
| Self Description | C1 | Active |
| Capabilities | C2 | Active |
| Capability Gaps | C3 | Active |
| Proposal Creation | C4 | Active |
| Proposal Ranking | C5 | Active |
| Proposal Approval | C6 | Active |
| Proposal Traceability | C7 | Active |
| Implementation Planning | C8 | Active |
| Proposal/Plan Linkage | C9 | Active |
| ISS | ISS | Active |
| Handler Registry | — | Partial (2 entries) |
| Response Formatter | — | Partial (5 handlers) |

---

*Architecture Diagrams V1 — 2026-04-27*
*Mermaid diagrams — render in Mermaid Live Editor or compatible viewer*
