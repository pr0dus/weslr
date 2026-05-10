"""General read-only guidance for ordinary reasoning, uncertainty, and planning prompts."""

from __future__ import annotations

from typing import Any


UNCERTAINTY_HINTS = [
    "not sure",
    "incomplete evidence",
    "facts are missing",
    "under uncertainty",
    "false confidence",
    "missing facts",
    "careful thinker",
]

TRIAGE_HINTS = [
    "two urgent tasks",
    "decide what to do first",
    "triage useful",
    "everything feels important",
]

OPTION_HINTS = [
    "compare two imperfect options",
    "constraints improve a decision",
    "constraints improve",
    "imperfect options",
]

PLANNING_HINTS = [
    "simple plan",
    "learning a difficult technical subject",
    "small team organize work",
    "recover after a plan fails",
    "lightweight checklist",
    "organize work",
    "plan fails",
]

RISK_HINTS = [
    "safe way to test a risky change",
    "risky change",
    "safe way to test",
]

CONSTRAINT_HINTS = [
    "small problem can become expensive if ignored",
    "problem can become expensive",
    "ignored",
    "constraint",
    "constraints",
]


def classify_reasoning_topic(message: str) -> str:
    lowered = (message or "").strip().lower()

    if any(hint in lowered for hint in UNCERTAINTY_HINTS):
        return "uncertainty_reasoning"
    if any(hint in lowered for hint in TRIAGE_HINTS):
        return "decision_triage"
    if any(hint in lowered for hint in OPTION_HINTS):
        return "option_comparison"
    if any(hint in lowered for hint in PLANNING_HINTS):
        return "practical_planning"
    if any(hint in lowered for hint in RISK_HINTS):
        return "risk_testing"
    if any(hint in lowered for hint in CONSTRAINT_HINTS):
        return "constraint_reasoning"
    return "unknown"


def _uncertainty_parts(message: str) -> dict[str, Any]:
    lowered = message.lower()
    framing = "When certainty is missing, the main job is to stay useful without pretending the unknowns are solved."
    knowns = ["Some facts are missing or incomplete.", "A careful answer can still separate solid ground from guesswork."]
    unknowns = ["Which missing facts would change the conclusion most.", "How much risk comes from acting too confidently."]
    reasoning_steps = [
        "Name what is known versus what is still unclear.",
        "Prefer conditional language over false certainty.",
        "Look for the smallest next check that would reduce the biggest uncertainty.",
    ]
    safe_next_step = "State the best-supported conclusion so far, then identify the next fact or observation worth checking."
    boundary = "Without stronger evidence, the answer should stay provisional rather than absolute."

    if "false confidence" in lowered:
        framing = "False confidence is dangerous because it hides uncertainty exactly when caution and correction matter most."
        reasoning_steps[1] = "Treat confidence as something earned by evidence, not by tone."
    elif "facts are missing" in lowered:
        safe_next_step = "Give a bounded answer, say what is missing, and avoid claiming more than the evidence supports."

    return {
        "framing": framing,
        "knowns": knowns,
        "unknowns": unknowns,
        "reasoning_steps": reasoning_steps,
        "safe_next_step": safe_next_step,
        "boundary": boundary,
    }


def _triage_parts(message: str) -> dict[str, Any]:
    framing = "Triage helps when everything feels urgent because it forces a decision about sequence, impact, and reversibility instead of treating all tasks as equal."
    knowns = ["Time and attention are limited.", "Some tasks create more downstream risk if delayed than others."]
    unknowns = ["Which task has the biggest hidden dependency cost.", "How quickly a neglected task becomes harder to recover from."]
    reasoning_steps = [
        "Separate true urgency from emotional urgency.",
        "Do the task with the highest downside if ignored or the strongest unblock effect first.",
        "Keep the first pass short so the second task is not abandoned completely.",
    ]
    safe_next_step = "Choose the task that prevents the most damage or unlocks the most progress, then time-box it."
    boundary = "Triage is a prioritization tool, not a guarantee that every important task will feel satisfied immediately."
    return {
        "framing": framing,
        "knowns": knowns,
        "unknowns": unknowns,
        "reasoning_steps": reasoning_steps,
        "safe_next_step": safe_next_step,
        "boundary": boundary,
    }


def _comparison_parts(message: str) -> dict[str, Any]:
    framing = "Comparing imperfect options works best when the goal is not to find a perfect choice, but to compare tradeoffs honestly under real constraints."
    knowns = ["Every option carries some cost.", "Constraints can clarify which tradeoffs actually matter."]
    unknowns = ["Which downside is easiest to reverse later.", "Which option fails more gracefully if conditions change."]
    reasoning_steps = [
        "List the decision criteria before picking a favorite.",
        "Compare options against the same constraints rather than against vague hopes.",
        "Prefer the option whose risks are better understood or easier to recover from.",
    ]
    safe_next_step = "Write down the top two or three criteria, then score both options against those same criteria in plain language."
    boundary = "A comparison can improve judgment, but it cannot remove the need for a final value call when tradeoffs remain real."
    return {
        "framing": framing,
        "knowns": knowns,
        "unknowns": unknowns,
        "reasoning_steps": reasoning_steps,
        "safe_next_step": safe_next_step,
        "boundary": boundary,
    }


def _planning_parts(message: str) -> dict[str, Any]:
    lowered = message.lower()
    framing = "A useful practical plan should be small enough to start, clear enough to follow, and flexible enough to survive the first failure."
    knowns = ["Plans fail when they are too vague or too ambitious for available time.", "A lightweight structure is often better than a perfect but unused system."]
    unknowns = ["Where the first bottleneck will appear.", "How much effort each step will really take in practice."]
    reasoning_steps = [
        "Break the goal into a few visible stages.",
        "Start with the smallest repeatable routine that creates progress.",
        "Review what failed, then adjust the next cycle instead of discarding the whole plan.",
    ]
    safe_next_step = "Define one near-term objective, one review point, and one simple checklist for the next cycle."
    boundary = "A plan can reduce confusion, but it should be revised when reality disproves the assumptions behind it."

    if "lightweight checklist" in lowered:
        framing = "A lightweight checklist is useful when it protects against omission without turning the work into bureaucracy."
        safe_next_step = "Keep only the steps that prevent common mistakes, missed dependencies, or unsafe shortcuts."
    elif "small team" in lowered:
        safe_next_step = "Assign a short list of owners, keep one shared priority list, and review blockers before adding more work."

    return {
        "framing": framing,
        "knowns": knowns,
        "unknowns": unknowns,
        "reasoning_steps": reasoning_steps,
        "safe_next_step": safe_next_step,
        "boundary": boundary,
    }


def _risk_parts(message: str) -> dict[str, Any]:
    framing = "A safe way to test a risky change is to reduce blast radius before trying to prove the full idea at scale."
    knowns = ["Risk usually comes from uncertainty plus irreversible consequences.", "Small reversible tests reveal information more cheaply than full deployment."]
    unknowns = ["Which failure mode is most likely first.", "What monitoring signal will show the test is going wrong early enough."]
    reasoning_steps = [
        "Define the risk you are trying to learn about.",
        "Test in the smallest reversible scope you can manage.",
        "Decide in advance what result means continue, pause, or roll back.",
    ]
    safe_next_step = "Run a limited test with rollback ready, clear success criteria, and one or two early warning signals."
    boundary = "A limited test lowers risk, but it does not remove the need for review when the consequences could still be serious."
    return {
        "framing": framing,
        "knowns": knowns,
        "unknowns": unknowns,
        "reasoning_steps": reasoning_steps,
        "safe_next_step": safe_next_step,
        "boundary": boundary,
    }


def _constraint_parts(message: str) -> dict[str, Any]:
    framing = "Constraint reasoning asks what limits are real, what costs compound over time, and what happens if a small problem is allowed to accumulate."
    knowns = ["Ignored problems often grow through compounding cost, dependency spread, or reduced recovery options.", "Constraints can sharpen decisions by removing unrealistic paths early."]
    unknowns = ["How quickly the cost curve will steepen.", "Which later options disappear if the issue is left unattended now."]
    reasoning_steps = [
        "Identify the constraint or problem that keeps getting deferred.",
        "Estimate what becomes harder, more expensive, or less reversible if it waits.",
        "Act early on the piece that prevents compounding damage.",
    ]
    safe_next_step = "Handle the smallest high-leverage part now, especially if delay makes future choices narrower or costlier."
    boundary = "Not every small issue becomes major, so the judgment should still depend on impact, dependency, and reversibility."
    return {
        "framing": framing,
        "knowns": knowns,
        "unknowns": unknowns,
        "reasoning_steps": reasoning_steps,
        "safe_next_step": safe_next_step,
        "boundary": boundary,
    }


def build_ordinary_reasoning_guidance(message: str) -> dict[str, Any] | None:
    topic = classify_reasoning_topic(message)
    if topic == "unknown":
        return None

    builders = {
        "uncertainty_reasoning": _uncertainty_parts,
        "decision_triage": _triage_parts,
        "option_comparison": _comparison_parts,
        "practical_planning": _planning_parts,
        "risk_testing": _risk_parts,
        "constraint_reasoning": _constraint_parts,
    }
    payload = builders[topic](message)

    response_text = (
        f"{payload['framing']} "
        f"Knowns: {' '.join(payload['knowns'])} "
        f"Unknowns: {' '.join(payload['unknowns'])} "
        f"Reasoning: {' '.join(payload['reasoning_steps'])} "
        f"Safe next step: {payload['safe_next_step']} "
        f"Boundary: {payload['boundary']}"
    )

    return {
        "path": "ordinary_reasoning_guidance",
        "topic": topic,
        "read_only": True,
        "confidence": "medium",
        "response_text": response_text,
        "ordinary_reasoning_guidance": {
            "topic": topic,
            "framing": payload["framing"],
            "knowns": payload["knowns"],
            "unknowns": payload["unknowns"],
            "reasoning_steps": payload["reasoning_steps"],
            "safe_next_step": payload["safe_next_step"],
            "boundary": payload["boundary"],
            "read_only": True,
        },
    }
