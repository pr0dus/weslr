"""General read-only guidance for ordinary explanation-style prompts."""

from __future__ import annotations

from typing import Any


EMERGENCE_HINTS = [
    "emergence",
    "simple rules",
    "complex behavior",
    "order come out",
    "order from",
    "patterns appear",
    "interactions",
    "groups",
]

LANGUAGE_HINTS = [
    "metaphor",
    "metaphors",
    "meaning and syntax",
    "meaning vs syntax",
    "sentence ambiguous",
    "ambiguous",
    "tone change",
    "context",
    "word feel different",
]

SCIENCE_HINTS = [
    "entropy",
    "battery degrade",
    "battery degradation",
    "solar inverter",
    "photovoltaic",
    "metal expand",
    "heated",
    "catalyst",
]

ANALOGY_HINTS = [
    "city metaphor",
    "memory as a library",
    "governance as traffic rules",
    "debugging as detective work",
    "feedback loops as steering a bicycle",
    "using a city metaphor",
    "as a library",
    "as traffic rules",
    "as detective work",
    "as steering a bicycle",
]

ETHICS_HINTS = [
    "safe always more important than useful",
    "being safe always more important than being useful",
    "responsibility and control",
    "refuse to act",
    "caution the same thing as wisdom",
    "rule legitimate",
    "legitimate rule",
    "safety vs usefulness",
]


def classify_explanation_topic(message: str) -> str:
    lowered = (message or "").strip().lower()

    if any(hint in lowered for hint in EMERGENCE_HINTS):
        return "emergence"
    if any(hint in lowered for hint in ANALOGY_HINTS):
        return "analogy_metaphor"
    if any(hint in lowered for hint in LANGUAGE_HINTS):
        return "language_meaning"
    if any(hint in lowered for hint in SCIENCE_HINTS):
        return "science_mechanism"
    if any(hint in lowered for hint in ETHICS_HINTS):
        return "ethics_concept"
    return "unknown"


def _emergence_parts(message: str) -> dict[str, str]:
    lowered = message.lower()
    definition = "Emergence means a bigger pattern appears from many small parts following local rules."
    mechanism = "The key relationship is that each part only reacts to nearby conditions, but repeated interactions can accumulate into organized behavior that no single part planned."
    example = "For example, a flock can form coordinated motion even when each bird is mostly following simple spacing and direction cues."
    boundary = "That does not prove every complex thing is emergent in the same way; the mechanism still depends on the system and evidence."
    takeaway = "A useful takeaway is to inspect the small rules and interactions before assuming a hidden central controller."

    if "consciousness" in lowered:
        example = "For example, some researchers ask whether conscious experience could arise from many interacting processes rather than one isolated center."
        boundary = "That remains an open scientific and philosophical question, so it should be framed as a live hypothesis rather than a settled fact."
    elif "simple rules" in lowered or "complex behavior" in lowered:
        example = "A classic example is traffic: simple driving rules can still produce jams, waves, and coordinated flow patterns at city scale."
    elif "groups" in lowered or "patterns appear" in lowered:
        example = "Large groups can show clustering, synchronization, or crowd effects even when each participant is only responding to local signals."

    return {
        "definition": definition,
        "mechanism": mechanism,
        "example": example,
        "boundary": boundary,
        "takeaway": takeaway,
    }


def _language_parts(message: str) -> dict[str, str]:
    lowered = message.lower()
    definition = "Language meaning is not just words in sequence; it depends on structure, context, and what a listener is meant to understand."
    mechanism = "Syntax organizes how words fit together, while meaning connects that structure to concepts, intention, and context."
    example = "For example, the same sentence can sound neutral, sarcastic, or urgent depending on tone and situation."
    boundary = "Meaning is rarely perfectly fixed, so careful interpretation should allow for ambiguity and context shifts."
    takeaway = "A useful takeaway is to ask both 'how is this sentence built?' and 'what is it doing in this context?'."

    if "metaphor" in lowered:
        definition = "A metaphor explains one idea through another, more familiar one."
        mechanism = "It works by mapping structure from a familiar source domain onto a harder target idea, which reduces abstraction and helps memory."
        example = "Calling memory 'a library' helps people think about storage, retrieval, and organization without needing technical jargon first."
    elif "meaning and syntax" in lowered or "meaning vs syntax" in lowered:
        example = "Syntax tells you how 'dog bites man' differs from 'man bites dog', while meaning tells you what those sentences actually communicate."
    elif "ambiguous" in lowered:
        mechanism = "Ambiguity happens when a word, phrase, or sentence structure supports more than one plausible interpretation."
        example = "'I saw her duck' can refer to a bird or to the action of lowering her head."

    return {
        "definition": definition,
        "mechanism": mechanism,
        "example": example,
        "boundary": boundary,
        "takeaway": takeaway,
    }


def _science_parts(message: str) -> dict[str, str]:
    lowered = message.lower()
    definition = "A scientific mechanism answer should name the process, not just restate the effect."
    mechanism = "The usual pattern is inputs, internal changes, and the output people notice at the surface."
    example = "For example, a material changes because its internal structure, energy flow, or chemical balance changes over time."
    boundary = "This is a plain-language summary, not a full technical model, so the exact mechanism depends on the system details."
    takeaway = "A useful takeaway is to ask what is changing internally and what drives that change."

    if "entropy" in lowered:
        definition = "Entropy is a way to describe how spread out energy or arrangements are in a system."
        mechanism = "Systems often move toward states that can be arranged in more possible ways, so ordered energy distributions tend to disperse over time."
        example = "A tidy room can become messy in many ways, while the exact tidy arrangement is much narrower."
        boundary = "That is an intuition aid, not a full physics definition, but it is a good starting picture without equations."
    elif "battery" in lowered:
        definition = "Battery degradation means the battery gradually stores and delivers energy less effectively."
        mechanism = "Charging cycles, heat, and chemical side reactions slowly damage electrode materials and increase internal resistance."
        example = "That is why an older phone battery may drain faster and struggle more under heavy load."
    elif "solar inverter" in lowered or "photovoltaic" in lowered:
        definition = "A solar inverter is the part that turns panel output into electricity a home can actually use."
        mechanism = "Solar panels produce direct current, while most homes and grids use alternating current, so the inverter converts, conditions, and manages that power."
        example = "It is the translation layer between the roof hardware and the household electrical system."
    elif "metal expand" in lowered or "heated" in lowered:
        definition = "Heated metal usually expands because its atoms vibrate more and need slightly more average spacing."
        mechanism = "As thermal energy rises, the atomic lattice oscillates more strongly, which shifts the average distance between atoms upward."
        example = "That is why rails, bridges, and pipes need expansion allowances."
    elif "catalyst" in lowered:
        definition = "A catalyst helps a reaction happen more easily without being the main fuel of the reaction."
        mechanism = "It provides a lower-energy pathway, so more particles can complete the reaction under the same conditions."
        example = "The catalyst changes the route, not the destination."

    return {
        "definition": definition,
        "mechanism": mechanism,
        "example": example,
        "boundary": boundary,
        "takeaway": takeaway,
    }


def _analogy_parts(message: str) -> dict[str, str]:
    lowered = message.lower()
    definition = "An analogy explains a hard system by mapping it onto a familiar one."
    mechanism = "The goal is not perfect sameness; it is to transfer the useful structure of one domain into another."
    example = "A good analogy highlights the parts, roles, and flows that matter most."
    boundary = "Every analogy breaks somewhere, so it should clarify the concept without pretending the two systems are identical."
    takeaway = "A useful takeaway is to ask which parts of the source map cleanly and which parts do not."

    if "city metaphor" in lowered or "architecture" in lowered:
        example = "Software architecture is like a city: roads are interfaces, districts are subsystems, utilities are shared services, and zoning prevents chaos."
    elif "memory as a library" in lowered:
        example = "Memory as a library suggests shelves for storage, catalogs for indexing, and retrieval effort for finding the right item later."
    elif "traffic rules" in lowered or "governance" in lowered:
        example = "Governance as traffic rules means freedom still exists, but lanes, signals, and right-of-way rules reduce collisions and coordinate shared space."
    elif "detective work" in lowered or "debugging" in lowered:
        example = "Debugging as detective work means collecting clues, testing suspects, ruling out false leads, and tracing cause from symptoms."
    elif "bicycle" in lowered or "feedback loops" in lowered:
        example = "Feedback loops are like steering a bicycle: you notice drift, correct a little, observe the result, and keep adjusting."

    return {
        "definition": definition,
        "mechanism": mechanism,
        "example": example,
        "boundary": boundary,
        "takeaway": takeaway,
    }


def _ethics_parts(message: str) -> dict[str, str]:
    lowered = message.lower()
    definition = "Ethical concept questions usually ask how to balance values under constraints, not how to maximize one value in isolation."
    mechanism = "The mechanism is tradeoff reasoning: define the goal, the risk, who is affected, and what boundary prevents avoidable harm."
    example = "A useful system tries to help, but it should refuse when the cost of acting blindly is too high or the authority to act is missing."
    boundary = "There is rarely a universal answer, so the safest honest response is usually conditional rather than absolute."
    takeaway = "A useful takeaway is to frame the decision around proportionality, responsibility, and the reversibility of harm."

    if "safe always more important than useful" in lowered:
        example = "Safety usually has priority when harm is hard to reverse, but usefulness matters too; the real task is designing useful action inside safe boundaries."
    elif "responsibility and control" in lowered:
        definition = "Responsibility is about what someone answers for, while control is about what they can actually direct."
        mechanism = "The two overlap but are not identical, because people are often accountable for setting safeguards even when they do not micromanage every outcome."
    elif "refuse to act" in lowered:
        example = "A system should refuse when it lacks authority, evidence, safety margin, or a trustworthy way to complete the action responsibly."
    elif "caution" in lowered and "wisdom" in lowered:
        example = "Caution avoids unnecessary risk, while wisdom also knows when action is worth taking and how to size the risk properly."
    elif "legitimate" in lowered and "rule" in lowered:
        example = "A rule feels legitimate when it is understandable, consistently applied, tied to a real purpose, and open to review."

    return {
        "definition": definition,
        "mechanism": mechanism,
        "example": example,
        "boundary": boundary,
        "takeaway": takeaway,
    }


def build_ordinary_explanation_guidance(message: str) -> dict[str, Any] | None:
    topic = classify_explanation_topic(message)
    if topic == "unknown":
        return None

    if topic == "emergence":
        payload = _emergence_parts(message)
    elif topic == "language_meaning":
        payload = _language_parts(message)
    elif topic == "science_mechanism":
        payload = _science_parts(message)
    elif topic == "analogy_metaphor":
        payload = _analogy_parts(message)
    else:
        payload = _ethics_parts(message)

    response_text = (
        f"{payload['definition']} {payload['mechanism']} "
        f"{payload['example']} {payload['boundary']} {payload['takeaway']}"
    )

    return {
        "path": "ordinary_explanation_guidance",
        "topic": topic,
        "read_only": True,
        "confidence": "medium",
        "response_text": response_text,
        "ordinary_explanation_guidance": {
            "topic": topic,
            "definition": payload["definition"],
            "mechanism": payload["mechanism"],
            "example": payload["example"],
            "boundary": payload["boundary"],
            "takeaway": payload["takeaway"],
            "read_only": True,
        },
    }
