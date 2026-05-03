#!/usr/bin/env python3
"""Inline test runner for test_explore.py — avoids subprocess overhead."""
import sys
sys.path.insert(0, '.')

from weslr.goal_decomposer import decompose, expand_keywords
from weslr.hypothesis_scorer import check_charge_balance, chemical_feasibility
from weslr.explore_engine import build_entity_graph, generate_hypotheses, _entity_matches_domain
from weslr.hypothesis_scorer import rank_hypotheses
from weslr.commands.explore import handle_explore

n_pass = 0
n_fail = 0

def check(cond, msg):
    global n_pass, n_fail
    if cond:
        n_pass += 1
        print(f'  PASS: {msg}')
    else:
        n_fail += 1
        print(f'  FAIL: {msg}')

# TestGoalDecomposer
print('TestGoalDecomposer...')
r = decompose("slow down human cell aging")
check("the" not in r["raw_keywords"], "stop word 'the' removed")
check("human" in r["raw_keywords"], "'human' preserved")
keywords = expand_keywords(["aging", "cell"], domain="biology")
check("senescence" in keywords, "'aging' expands to include 'senescence'")
r2 = decompose("create more efficient photovoltaic material")
check(r2["domain"] == "materials_science", "photovoltaic → materials_science domain")
r3 = decompose("design targeted drug delivery for glioblastoma")
check(len(r3["query_components"]) > 0, "query_components non-empty")
check(r3["original_goal"] == "design targeted drug delivery for glioblastoma", "original_goal preserved")

# TestHypothesisScorer
print('TestHypothesisScorer...')
for formula, balanced in [('H2O', True), ('NaCl', True), ('NaCl2', False)]:
    r = check_charge_balance(formula)
    check(r['is_balanced'] == balanced, f'charge_balance({formula})')
r = chemical_feasibility("Cu2ZnSnSe4")
check(r['overall_feasible'] == True, 'chemical_feasibility(Cu2ZnSnSe4) feasible')
r = chemical_feasibility("H999")
check(r['overall_feasible'] == False, 'chemical_feasibility(H999) unfeasible')

# TestExploreEngine
print('TestExploreEngine...')
check(_entity_matches_domain('Dasatinib', 'biology') == True, 'Dasatinib → biology')
check(_entity_matches_domain('Kesterite', 'biology') == False, 'Kesterite → not biology')
check(_entity_matches_domain('Kesterite', 'materials_science') == True, 'Kesterite → materials_science')
mock = [{'arxiv_id': '2401.00001', 'title': 'Dasatinib and quercetin', 'abstract': 'Dasatinib clears senescent cells.'}]
entities = build_entity_graph(mock)
hyps = generate_hypotheses(entities, 'slow down cell aging', domain='biology', max_hypotheses=5)
check(len(hyps) > 0, 'generate_hypotheses returns non-empty list')
ranked = rank_hypotheses(hyps)
check(ranked[0]['confidence'] >= ranked[-1]['confidence'], 'rank_hypotheses sorted descending')

# TestHandleExplore
print('TestHandleExplore...')
r = handle_explore('/explore aging --dry-run', '/explore aging --dry-run')
check('Exploring:' in r, 'output contains "Exploring:"')
check('hypotheses' in r, 'output contains "hypotheses"')
check('Confidence:' in r, 'output contains "Confidence:"')
check('Top 5' in r or 'Top 3' in r, 'output contains top-N header')

print()
print(f'Results: {n_pass} passed, {n_fail} failed')
sys.exit(0 if n_fail == 0 else 1)