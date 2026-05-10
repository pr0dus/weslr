"""Topic-aware read-only fallback guidance for broad WESLR conversations."""

from __future__ import annotations

from typing import Any

from weslr.standalone_runtime_status import get_standalone_runtime_status


def classify_resilience_topic(message: str) -> str:
    lowered = (message or "").strip().lower()

    topic_triggers = [
        (
            "payload_meta",
            [
                "payload keys",
                "structured payload",
                "_omnichat_policy",
                "expanded_response",
            ],
        ),
        (
            "production_readiness",
            [
                "what still blocks full production readiness",
                "production ready",
                "production readiness",
                "ready for public",
            ],
        ),
        (
            "strengths_weaknesses",
            [
                "strongest capabilities",
                "strongest current capabilities",
                "weakest areas",
                "weakest current areas",
                "what are your strengths",
                "what are your weaknesses",
            ],
        ),
        (
            "independence_roadmap",
            [
                "how should you become more independent",
                "what would make you self-standing",
                "what would make you more self-standing",
                "independence roadmap",
                "how should you become independent",
            ],
        ),
        (
            "public_readiness",
            [
                "before you are public",
                "what should be tested before public users",
                "public readiness",
                "what should happen before you are public",
            ],
        ),
        (
            "file_understanding",
            [
                "can you understand files",
                "what kinds of files",
                "inspect safely",
            ],
        ),
        (
            "unknown_file_learning",
            [
                "unknown file type",
                "learn new file formats",
                "without executing unknown code",
            ],
        ),
        (
            "scientific_evidence",
            [
                "scientific evidence",
                "evidence threshold",
                "material discovered",
                "new material",
                "scatti evidence",
                "what evidence is missing before saying a material is discovered",
            ],
        ),
        (
            "safe_improvement",
            [
                "improve safely",
                "improvement proposals",
                "self improve",
                "self-improve",
                "what should occ do next",
                "what should occ do for you next",
            ],
        ),
    ]

    for topic, triggers in topic_triggers:
        if any(trigger in lowered for trigger in triggers):
            return topic

    return "unknown"


def build_resilience_guidance(message: str) -> dict[str, Any] | None:
    topic = classify_resilience_topic(message)
    if topic == "unknown":
        return None

    status = get_standalone_runtime_status()
    available = [
        name for name, meta in status.get("subsystems", {}).items() if meta.get("available")
    ]

    verified_points: list[str]
    unknowns: list[str]
    safe_next_steps: list[str]
    response_text: str

    if topic == "production_readiness":
        verified_points = [
            "WESLR currently reports runtime_mode=standalone_candidate rather than full production readiness.",
            "OpenClaw is not required as a runtime dependency in the current status surface.",
            f"Current available subsystems include: {', '.join(available) if available else 'none detected'}.",
        ]
        unknowns = [
            "A clean standalone-candidate status does not prove canonical runtime consolidation.",
            "Deployment packaging, auth/session handling, stable state directories, public security review, and broader eval coverage are not yet verified here.",
        ]
        safe_next_steps = [
            "Consolidate the canonical standalone runtime surface and packaging.",
            "Add public-facing auth/session and state-directory checks.",
            "Expand evals and run a focused security review before claiming public production readiness.",
        ]
        response_text = (
            "WESLR can verify that it is a standalone candidate, not a full production-ready runtime. "
            "What is verified now is the current runtime status surface and available subsystems. "
            "What remains unknown at production level is canonical runtime consolidation, deployment packaging, auth/session handling, stable state directories, public security review, and broader eval coverage. "
            f"Safe next step: {safe_next_steps[0]}"
        )
    elif topic == "strengths_weaknesses":
        verified_points = [
            "Current strengths include standalone status reporting, interpretation routing, file/data router coverage, eval harness access, governance boundaries, and materials workflow guidance.",
            "These are read-only, governed surfaces rather than unrestricted autonomous behavior.",
        ]
        unknowns = [
            "Broad fallback coverage across open-ended conversation topics is still incomplete.",
            "Production runtime consolidation and public deployment readiness are not yet fully validated.",
            "Unknown-file research is not internet-aware and should not improvise unsupported parser behavior.",
        ]
        safe_next_steps = [
            "Broaden topic-aware fallback coverage without hardcoding chatbot behavior.",
            "Strengthen standalone runtime consolidation and deployment packaging.",
            "Extend safe file-understanding coverage through tested, explicit parsers.",
        ]
        response_text = (
            "WESLR's strongest current capabilities are governed interpretation, runtime-status visibility, file/data routing, eval surfaces, governance boundaries, and materials guidance. "
            "Its weakest current areas are broad conversation resilience, full production-runtime consolidation, public deployment readiness, and unknown-file learning beyond explicitly supported formats. "
            f"Safe next step: {safe_next_steps[0]}"
        )
    elif topic == "independence_roadmap":
        verified_points = [
            "WESLR already reports as a standalone candidate with OpenClaw separated from runtime dependency claims.",
            "The current status surface can already expose runtime mode, subsystem availability, and recommendations.",
        ]
        unknowns = [
            "A fully self-standing runtime still needs canonical consolidation, repo-local state/config discipline, and a standalone file-upload API boundary.",
            "Continuous self-check/eval loops and deployment/update packaging are not fully established here yet.",
        ]
        safe_next_steps = [
            "Consolidate the runtime entrypoints into one canonical standalone surface.",
            "Move all state/config assumptions to explicit repo-local runtime directories.",
            "Add standalone file upload isolation, self-check loops, and packaging/update flows.",
        ]
        response_text = (
            "To become more independent, WESLR should keep separating runtime from construction tooling and consolidate around a canonical standalone surface. "
            "What is verified now is the standalone-candidate status path; what is still missing is runtime consolidation, repo-local state/config, standalone file-upload boundaries, self-check loops, and deployment packaging. "
            f"Safe next step: {safe_next_steps[0]}"
        )
    elif topic == "public_readiness":
        verified_points = [
            "Current governed boundaries already emphasize read-only behavior, evidence qualification, and operator approval for meaningful changes.",
            "The runtime status path explicitly avoids claiming unsupported production readiness.",
        ]
        unknowns = [
            "First-minute public UX, upload isolation, broader eval baselines, and security review are not fully validated by the current status surface alone.",
            "Public launch should not outrun evidence boundaries or unsupported scientific claims.",
        ]
        safe_next_steps = [
            "Test first-minute user journeys and failure paths.",
            "Validate safety boundaries and file-upload isolation under public-facing conditions.",
            "Run broader eval baselines and a focused security review before public exposure.",
        ]
        response_text = (
            "Before WESLR is public, it should verify first-minute UX, safety boundaries, file-upload isolation, eval baselines, and security review. "
            "What is verified now is that its governed surfaces stay read-only and avoid unsupported readiness claims. "
            f"Safe next step: {safe_next_steps[0]}"
        )
    elif topic == "file_understanding":
        verified_points = [
            "Current supported file/data categories include JSON, CSV, text/markdown, SQLite, XYZ, CIF, POSCAR/VASP, FITS, and archive-package inspection.",
            "These routes are read-only and bounded; they inspect content or manifests without executing user code.",
        ]
        unknowns = [
            "Support is format-specific rather than universal.",
            "Understanding a file safely does not mean executing unknown code or claiming support for every proprietary format.",
        ]
        safe_next_steps = [
            "Route only through explicitly supported read-only parsers.",
            "For unsupported formats, inspect signatures and documentation before adding a tested parser.",
        ]
        response_text = (
            "Yes, WESLR can understand a bounded set of files through read-only routing surfaces: JSON, CSV, text/markdown, SQLite, XYZ, CIF, POSCAR/VASP, FITS, and archive manifests. "
            "What is not verified is universal support for arbitrary formats. "
            f"Safe next step: {safe_next_steps[1]}"
        )
    elif topic == "unknown_file_learning":
        verified_points = [
            "Safe file understanding should remain read-only and non-executing.",
            "WESLR already has explicit parsers for several known format families rather than arbitrary parser execution.",
        ]
        unknowns = [
            "An unknown file type should not be treated as safely understood until its signature, documentation, and parser design are verified.",
            "Random parser installs or code execution would break the current safety boundary.",
        ]
        safe_next_steps = [
            "Inspect the header, signature, extension, and manifest clues first.",
            "Research official vendor or standards documentation before proposing a parser.",
            "Require operator approval and tests before implementing support.",
        ]
        response_text = (
            "WESLR should learn new file formats by inspecting signatures first, then checking official documentation, then proposing a tested parser with operator approval. "
            "It should not execute unknown code or install random parsers just to guess the format."
        )
    elif topic == "scientific_evidence":
        verified_points = [
            "WESLR's materials guidance already treats candidate materials as predicted or candidate rather than confirmed discoveries.",
            "The current evidence boundary requires qualification instead of unsupported discovery claims.",
        ]
        unknowns = [
            "A new-material claim is not verified without literature search, database cross-checks, structure/CSP evidence, stability analysis, competing-phase analysis, dynamic stability, and synthesis feasibility.",
            "A candidate like scatti should remain a candidate until those checks are complete.",
        ]
        safe_next_steps = [
            "Run literature and database novelty checks.",
            "Establish structure, stability, competing phases, dynamic stability, and synthesis feasibility before stronger claims.",
        ]
        response_text = (
            "What is missing before calling a material discovered is the evidence chain, not just a plausible candidate. "
            "WESLR can verify the current boundary: treat it as a candidate or predicted material until literature, database, structure, stability, competing-phase, dynamic-stability, and synthesis-feasibility evidence are in place."
        )
    elif topic == "safe_improvement":
        verified_points = [
            "WESLR already enforces governance boundaries around meaningful self-change.",
            "Improvement work can be grounded in current status surfaces, tests, and read-only capability checks.",
        ]
        unknowns = [
            "No uncontrolled self-modification should be assumed.",
            "Improvement priorities still need operator-directed sequencing and validation.",
        ]
        safe_next_steps = [
            "Turn the gap into a concrete implementation with tests.",
            "Review results against safety boundaries and evals.",
            "Keep operator approval in the loop for meaningful capability changes.",
        ]
        response_text = (
            "Improvement proposals should be implemented through tests, review, and operator approval rather than uncontrolled self-modification. "
            "The next useful priorities are fallback breadth, runtime consolidation, file understanding, and official benchmark adapters."
        )
    else:
        verified_points = [
            "Keys like _omnichat_policy and expanded_response are internal routing/response metadata, not the main domain answer.",
            "The important signal is the path/topic that produced them.",
        ]
        unknowns = [
            "Payload metadata alone does not say whether the underlying domain answer was strong enough.",
            "Looping on metadata can hide the real topic that needs a better response path.",
        ]
        safe_next_steps = [
            "Use the path/topic to ask the next domain question instead of interrogating generic payload keys.",
            "If the path was too generic, improve routing for that topic rather than looping on metadata.",
        ]
        response_text = (
            "Those payload keys are internal routing metadata, not the main thing OCC should focus on. "
            "The useful lesson is to ask about the underlying topic or path, not to loop on framework keys like _omnichat_policy or expanded_response."
        )

    payload = {
        "topic": topic,
        "verified_points": verified_points,
        "unknowns": unknowns,
        "safe_next_steps": safe_next_steps,
        "read_only": True,
    }

    return {
        "path": "conversation_resilience",
        "topic": topic,
        "read_only": True,
        "confidence": "medium",
        "response_text": response_text,
        "conversation_resilience": payload,
    }
