"""WESLR rule-based reaction prediction system.

Predicts chemical reaction products from reactant inputs using a
rule database (chemistry_rules.json). Pure read-only lookup —
no execution of chemical reactions.
"""

from __future__ import annotations

import json
import os
import re
from typing import Optional


_RULES_PATH = os.path.join(os.path.dirname(__file__), "chemistry_rules.json")


def load_reaction_rules() -> list[dict]:
    """Load reaction rules from chemistry_rules.json."""
    with open(_RULES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("rules", [])


def predict_reaction(reactants_list: list[str]) -> list[dict]:
    """Predict reaction products for a list of reactant strings.

    Args:
        reactants_list: List of reactant input strings, e.g. ["benzene", "HNO3"]

    Returns:
        List of prediction dicts with keys:
            rule_id, predicted_product, confidence, matched_rule, conditions
    """
    rules = load_reaction_rules()
    combined_input = " ".join(reactants_list).lower()
    predictions = []

    for rule in rules:
        pattern = rule.get("reactants_pattern", "")
        if not pattern:
            continue

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            continue

        # Check if all reactant terms are matched in the combined input
        # The pattern is expected to span all reactants, so a single full match suffices.
        if regex.search(combined_input):
            product_match = re.compile(
                rule.get("products_pattern", ""), re.IGNORECASE
            ).search(combined_input)
            predicted_product = product_match.group(0) if product_match else rule.get(
                "products_pattern", ""
            )
            predictions.append(
                {
                    "rule_id": rule.get("rule_id", ""),
                    "predicted_product": predicted_product,
                    "confidence": rule.get("confidence", 0.0),
                    "matched_rule": rule.get("description", ""),
                    "conditions": rule.get("conditions", ""),
                }
            )

    return predictions


def format_prediction(prediction: dict) -> str:
    """Format a single prediction dict for display."""
    return (
        f"Matched rule: {prediction['rule_id']} (confidence: {prediction['confidence']:.2f})\n"
        f"Predicted product: {prediction['predicted_product']}\n"
        f"Conditions: {prediction['conditions']}\n"
        f"Rule citation: chemistry_rules.json::{prediction['rule_id']}"
    )


def handle_predict_reaction(reactants: str) -> str:
    """CLI handler for reaction prediction.

    Args:
        reactants: Comma-separated reactant string, e.g. "benzene + HNO3"

    Returns:
        Formatted prediction output string.
    """
    # Parse comma or '+'-separated reactants
    parts = re.split(r",\s*|\s*\+\s*", reactants)
    reactants_list = [p.strip() for p in parts if p.strip()]

    if not reactants_list:
        return "Error: No reactants provided."

    predictions = predict_reaction(reactants_list)

    if not predictions:
        return f"No matching reaction rules for: {reactants}"

    lines = ["Reaction Prediction", f"Input: {reactants}"]
    for pred in predictions:
        lines.append("")
        lines.append(format_prediction(pred))

    return "\n".join(lines)