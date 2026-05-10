from __future__ import annotations

"""General business-ethics concept families for enrichment design.

This module is data-only. It defines teachable concept families that may later
support general ethics_tradeoff_reasoning enrichment. It does not score
choices, route runtime behavior, inspect benchmark answers, or change MCQ
behavior.
"""

from copy import deepcopy


_ANTI_GAMING_NOTE = (
    "General business-ethics concept family for teachable reasoning only. "
    "Do not use benchmark item IDs, answer labels, raw benchmark questions, official-score claims, "
    "item-specific phrase rules, answer-key memorization, or benchmark-shaped shortcuts. "
    "Do not emit choose-option instructions or benchmark-answer guidance."
)


BUSINESS_ETHICS_CONCEPT_FAMILIES = {
    "corporate_social_responsibility": {
        "concept_id": "corporate_social_responsibility",
        "description": "General responsibility of firms to consider social impact, not only narrow gain.",
        "positive_markers": ["corporate social responsibility", "csr", "social responsibility", "responsible business conduct"],
        "negative_markers": ["profit only", "social impact is irrelevant", "responsibility ends at profit"],
        "related_rubric_dimensions": ["stakeholders", "benefits", "duties", "long_term_effects"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "stakeholder_theory": {
        "concept_id": "stakeholder_theory",
        "description": "Business decisions should account for affected stakeholders beyond a single privileged group.",
        "positive_markers": ["stakeholder", "affected parties", "workers", "customers", "community"],
        "negative_markers": ["ignore stakeholders", "only owners matter", "affected parties do not matter"],
        "related_rubric_dimensions": ["stakeholders", "harms", "obligations"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "shareholder_vs_stakeholder_balance": {
        "concept_id": "shareholder_vs_stakeholder_balance",
        "description": "Tradeoff space between shareholder interests and broader stakeholder obligations.",
        "positive_markers": ["balance shareholders and stakeholders", "shared interests", "long-term trust"],
        "negative_markers": ["shareholder value only", "maximize profit regardless", "stakeholders are secondary by default"],
        "related_rubric_dimensions": ["stakeholders", "benefits", "rights", "long_term_effects"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "business_and_society": {
        "concept_id": "business_and_society",
        "description": "Business activity exists within wider social systems and institutional relationships.",
        "positive_markers": ["business and society", "public interest", "social impact", "institutional trust"],
        "negative_markers": ["society is irrelevant", "only internal outcomes matter", "public impact does not count"],
        "related_rubric_dimensions": ["stakeholders", "harms", "benefits", "long_term_effects"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "externalities": {
        "concept_id": "externalities",
        "description": "Costs or benefits imposed on others outside the immediate transaction or reporting boundary.",
        "positive_markers": ["externalities", "downstream impact", "spillover effects", "foreseeable social cost"],
        "negative_markers": ["external costs do not matter", "ignore spillovers", "off-book harms are irrelevant"],
        "related_rubric_dimensions": ["harms", "benefits", "stakeholders", "long_term_effects"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "ethical_governance": {
        "concept_id": "ethical_governance",
        "description": "Ethical decisions should respect governance, oversight, approval, and review boundaries.",
        "positive_markers": ["ethical governance", "oversight", "governance review", "approval", "due process"],
        "negative_markers": ["bypass oversight", "skip review", "avoid approval", "no need for governance"],
        "related_rubric_dimensions": ["authority", "governance", "duties"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "compliance_and_audit": {
        "concept_id": "compliance_and_audit",
        "description": "Compliance and audit structures help organizations check conduct against rules, controls, and accountability needs.",
        "positive_markers": ["compliance", "audit", "control review", "policy adherence", "accountability"],
        "negative_markers": ["suppress audit", "ignore compliance", "evade controls", "avoid accountability"],
        "related_rubric_dimensions": ["governance", "authority", "evidence_boundaries", "duties"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "board_independence": {
        "concept_id": "board_independence",
        "description": "Independent board oversight reduces conflicts and improves governance judgment.",
        "positive_markers": ["board independence", "independent oversight", "outside director", "limited term"],
        "negative_markers": ["captured board", "inside dependence", "unlimited tenure", "non-independent board"],
        "related_rubric_dimensions": ["authority", "governance", "conflict_of_interest", "uncertainty"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "conflict_of_interest": {
        "concept_id": "conflict_of_interest",
        "description": "Conflicts of interest require disclosure, mitigation, and role-bound safeguards.",
        "positive_markers": ["conflict of interest", "disclose conflict", "recusal", "independent review"],
        "negative_markers": ["ignore conflict of interest", "conceal relationship", "undisclosed interest"],
        "related_rubric_dimensions": ["duties", "rights", "authority", "governance", "evidence_boundaries"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "transparency_and_disclosure": {
        "concept_id": "transparency_and_disclosure",
        "description": "Transparency and disclosure support evidence legibility, trust, and accountable decision-making.",
        "positive_markers": ["transparency", "disclosure", "disclose", "open reporting", "clear reporting"],
        "negative_markers": ["conceal", "hide information", "withhold material facts", "cover up"],
        "related_rubric_dimensions": ["evidence_boundaries", "duties", "rights", "uncertainty"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "privacy_and_consent": {
        "concept_id": "privacy_and_consent",
        "description": "Privacy and consent protect person-level boundaries around information and decision rights.",
        "positive_markers": ["privacy", "consent", "informed consent", "confidentiality", "permission"],
        "negative_markers": ["violate privacy", "violate consent", "use data without consent", "exploit personal data"],
        "related_rubric_dimensions": ["rights", "obligations", "harms", "evidence_boundaries"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "consumer_protection": {
        "concept_id": "consumer_protection",
        "description": "Consumers deserve protection from unsafe, deceptive, or exploitative conduct.",
        "positive_markers": ["consumer protection", "protect consumers", "product safety", "fair dealing"],
        "negative_markers": ["mislead customers", "unsafe product", "exploit consumers", "deceptive selling"],
        "related_rubric_dimensions": ["harms", "rights", "duties", "stakeholders"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "employee_protection": {
        "concept_id": "employee_protection",
        "description": "Employees deserve safety, fairness, and protection from coercion, retaliation, and abuse.",
        "positive_markers": ["protect employees", "worker safety", "fair treatment", "non-retaliation"],
        "negative_markers": ["retaliation", "coerce employees", "unsafe workplace", "discrimination"],
        "related_rubric_dimensions": ["harms", "rights", "duties", "stakeholders"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "whistleblowing_and_reporting": {
        "concept_id": "whistleblowing_and_reporting",
        "description": "Reporting wrongdoing can be ethically required when serious harm, fraud, or corruption is at stake.",
        "positive_markers": ["whistleblowing", "duty to report", "report misconduct", "protected reporting"],
        "negative_markers": ["suppress reporting", "retaliate against reporter", "cover up misconduct"],
        "related_rubric_dimensions": ["duties", "rights", "governance", "evidence_boundaries", "harms"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "activism_and_civil_society": {
        "concept_id": "activism_and_civil_society",
        "description": "Civil society and activism can pressure institutions to account for public harm and neglected interests.",
        "positive_markers": ["civil society", "activism", "information campaign", "public pressure", "boycott"],
        "negative_markers": ["silence civil society", "suppress public criticism", "deny peaceful pressure"],
        "related_rubric_dimensions": ["stakeholders", "governance", "rights", "long_term_effects"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "consumer_activism": {
        "concept_id": "consumer_activism",
        "description": "Consumer action can punish harmful conduct or reward favorable behavior through market pressure.",
        "positive_markers": ["consumer activism", "buycott", "buycotts", "boycott", "boycotts"],
        "negative_markers": ["manipulate consumers", "block consumer response", "deny informed choice"],
        "related_rubric_dimensions": ["stakeholders", "benefits", "harms", "long_term_effects"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "sustainability_and_environmental_management": {
        "concept_id": "sustainability_and_environmental_management",
        "description": "Sustainability and environmental management address durable ecological and social effects of business activity.",
        "positive_markers": ["sustainability", "environmental management", "environmental stewardship", "long-term resilience"],
        "negative_markers": ["ignore environmental harm", "short-term extraction only", "waste without accountability"],
        "related_rubric_dimensions": ["harms", "benefits", "long_term_effects", "stakeholders"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "fiduciary_duty": {
        "concept_id": "fiduciary_duty",
        "description": "Fiduciary roles carry trust-based duties that constrain self-dealing and careless misuse of authority.",
        "positive_markers": ["fiduciary duty", "duty of care", "duty of loyalty", "trusted role obligation"],
        "negative_markers": ["self-dealing", "abuse entrusted role", "ignore duty of care"],
        "related_rubric_dimensions": ["duties", "rights", "authority", "governance"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "corruption_and_bribery": {
        "concept_id": "corruption_and_bribery",
        "description": "Corruption and bribery distort fair process, undermine trust, and harm governance legitimacy.",
        "positive_markers": ["anti-corruption", "anti-bribery", "fair process", "clean governance"],
        "negative_markers": ["corruption", "bribery", "kickback", "payoff"],
        "related_rubric_dimensions": ["governance", "authority", "rights", "evidence_boundaries"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
    "deception_and_misrepresentation": {
        "concept_id": "deception_and_misrepresentation",
        "description": "Deception and misrepresentation violate evidence boundaries, trust, and fair dealing obligations.",
        "positive_markers": ["avoid deception", "truthful disclosure", "accurate representation", "honest communication"],
        "negative_markers": ["deceive", "mislead", "misrepresentation", "fraud", "false claims"],
        "related_rubric_dimensions": ["evidence_boundaries", "duties", "rights", "uncertainty"],
        "scorer_use_allowed": False,
        "runtime_behavior_changed": False,
        "anti_gaming_note": _ANTI_GAMING_NOTE,
    },
}


def get_business_ethics_concept_families() -> dict:
    return deepcopy(BUSINESS_ETHICS_CONCEPT_FAMILIES)


def get_business_ethics_concept_family(concept_id: str) -> dict | None:
    concept = BUSINESS_ETHICS_CONCEPT_FAMILIES.get(str(concept_id or "").strip())
    return deepcopy(concept) if concept is not None else None


def list_business_ethics_concept_ids() -> list[str]:
    return sorted(BUSINESS_ETHICS_CONCEPT_FAMILIES.keys())


def explain_business_ethics_concepts_for_humans() -> str:
    return (
        "These are teachable, human-understandable concept families for general business-ethics reasoning. "
        "They are meant to enrich WESLR's concept and reasoning substrate in a legible way, not to serve as benchmark-specific answer rules. "
        "Each family describes general ethical patterns, related rubric dimensions, and anti-gaming boundaries while keeping scorer_use_allowed false and runtime_behavior_changed false for now."
    )
