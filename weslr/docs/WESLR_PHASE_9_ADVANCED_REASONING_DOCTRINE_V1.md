"""
weslr/docs/WESLR_PHASE_9_ADVANCED_REASONING_DOCTRINE_V1.md
===========================================================
Phase 9 — Advanced Reasoning & Meta-Learning Doctrine

Author: OCC (WESLR governed intelligence) — Phase 9
"""

# ──────────────────────────────────────────────────────────────────────────────
# PURPOSE
# ──────────────────────────────────────────────────────────────────────────────
# Enable three advanced reasoning capabilities that strengthen hypothesis
# generation without external ML or black-box models:
#
#   1. Abductive reasoning  — generate plausible explanations for observations
#   2. Meta-analysis        — pool evidence across hypotheses/studies
#   3. Transfer/analogy    — cross-domain hypothesis transfer via rules
#
# All operations are deterministic, rule-based, and read-only on user data.
# No learning from user data across tenants (doctrine P11).

# ──────────────────────────────────────────────────────────────────────────────
# 1. ABDUCTIVE REASONER
# ──────────────────────────────────────────────────────────────────────────────
#
# Rules are stored as:  antecedent → consequent (with confidence)
# Example rule: ("high_dose", "response_increase", 0.85)
#
# Backward chaining (BFS, depth ≤ 3):
#   Given observation O, find all rules R where R.consequent matches O.
#   For each matching rule, recursively find rules that produce R.antecedent.
#   Confidence of explanation = product of all rule confidences in chain.
#
# Parsimony bonus: fewer rules → higher score
# Domain relevance: prefer rules from hypothesis's own domain
#
# Integration:
#   - causality.get_causal_links() → automatic rule extraction
#   - discovery correlation patterns → weak rules (confidence = |r|)
#   - user-supplied via /abduce rule add
#
# Output: ranked Explanation objects with provenance

# ──────────────────────────────────────────────────────────────────────────────
# 2. META-ANALYST
# ──────────────────────────────────────────────────────────────────────────────
#
# Fixed-effect model (inverse-variance weighted):
#   pooled_effect = Σ(w_i * effect_i) / Σ(w_i)
#   where w_i = 1 / SE_i²
#
# Random-effects (DerSimonian-Laird):
#   tau² = max(0, (Q - (k-1)) / (Σw_i - Σw_i²/Σw_i))
#   where Q = Σw_i*(effect_i - pooled_fixed)²
#   Pooled = Σ(w_i*effect_i) / Σ(w_i)  [RE weights incorporate tau²]
#
# Heterogeneity:
#   Q = Σw_i*(yi - pooled)²
#   I² = max(0, (Q-(k-1))/Q * 100)
#
# Z = pooled_effect / SE_pooled
# p = 2*(1 - Φ(|Z|))  [standard normal CDF, pure-Python]
#
# Inputs: effect_size, standard_error, sample_size, study_id
# Helper: from_hypotheses(hypothesis_ids) — reads from HypothesisRepository
#
# Constraints:
#   - ≤ 100 studies per meta-analysis
#   - Deterministic: same inputs → identical outputs
#   - No external statistical libraries (pure math + sympy where needed)

# ──────────────────────────────────────────────────────────────────────────────
# 3. TRANSFER ANALOGY ENGINE
# ──────────────────────────────────────────────────────────────────────────────
#
# Analogy: (source_domain, source_concept) ↔ (target_domain, target_concept)
#          with similarity_weight ∈ (0, 1]
#
# Built-in analogies (preloaded):
#   enzyme      ↔ catalyst        (weight 0.90, biology→chemistry)
#   receptor    ↔ binding_site   (weight 0.85, biology→chemistry)
#   gene_expr   ↔ protein_synth  (weight 0.90, biology→chemistry)
#   cell        ↔ compartment    (weight 0.75, biology→chemistry)
#   kinase      ↔ phosphorylator (weight 0.80, biology→chemistry)
#   drug        ↔ ligand         (weight 0.85, pharmacology→chemistry)
#   pathway     ↔ reaction_net   (weight 0.80, biology→chemistry)
#   inhibitor   ↔ blocker        (weight 0.85, pharmacology→chemistry)
#   agonist     ↔ activator      (weight 0.80, pharmacology→biology)
#   dose_resp   ↔ binding_curve  (weight 0.85, pharmacology→chemistry)
#
# Transfer process:
#   1. Find analogy rules matching source hypothesis domain
#   2. Replace domain-specific predicates with target equivalents
#   3. Confidence = original_confidence * similarity_weight
#   4. Provenance: "transferred from <id> via analogy <rule>"
#   5. Auto-save as draft hypothesis in HypothesisRepository
#
# No learning: all analogies are hardcoded or user-added via /transfer add

# ──────────────────────────────────────────────────────────────────────────────
# INTEGRATION POINTS
# ──────────────────────────────────────────────────────────────────────────────
#
# HypothesisRepository (Phase 7):
#   - Abductive explanations → draft hypotheses on user approval
#   - Meta-analysis results  → composite hypothesis (type=meta_analysis)
#   - Transferred hypotheses → separate entries with derived_from provenance
#
# Discovery engine: anomaly flag → trigger abductive reasoner
# Causality: causal_graph edges → rules for abduction
# Experiment suggester: after meta-analysis, suggest heterogeneity-resolving experiments
# Report generator: include abduction + meta-analysis + transfer in reports

# ──────────────────────────────────────────────────────────────────────────────
# OUTPUT LABELS
# ──────────────────────────────────────────────────────────────────────────────
# All meta-analysis: "Synthesized from simulated/demo data – not for clinical use"
# Transfer hypotheses: "Analogous hypothesis – not experimentally validated"
# Abduction: "Plausible explanations – requires experimental validation"

# ──────────────────────────────────────────────────────────────────────────────
# CONSTRAINTS
# ──────────────────────────────────────────────────────────────────────────────
# - No scipy.stats; pure Python math + sympy for CDF/inverse-CDF
# - Deterministic: np.random.seed(seed) default=42 where randomness needed
# - Per-tenant storage: rules, analogies, meta pools keyed by tenant_id
# - BFS depth ≤ 3 for abduction; max 200 rules, 100 studies per meta