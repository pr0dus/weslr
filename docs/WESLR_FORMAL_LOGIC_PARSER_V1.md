# WESLR Formal Logic Parser V1

## 1. Purpose

FormalLogicParser V1 is the missing layer between natural-language MCQ text and `FormalLogicSolver`.

Its role is to convert runtime-only benchmark question and choice text, when explicitly allowed, into normalized logical forms that the reasoning engine can inspect, trace, and challenge without granting private symbolic authority.

This is a design-only document. It does not implement parser code, does not change `FormalLogicSolver`, does not change the MCQ adapter, does not tune benchmark items, and does not claim any official score.

## 2. Evidence from dry-run diagnosis

Observed from the local formal logic dry-run path:

- formal logic dry-run count: 5
- candidate solver routing works: 5/5
- implemented solver runs: 5/5
- `FormalLogicSolver` status: `no_supported_pattern` for all 5/5
- total trace nodes: 23
- total trace edges: 0
- total conflicts: 0
- no official score claimed

Observed parser coverage diagnosis:

- `natural_language_logical_form_extraction`: 3
- `disjunction_elimination_or_cases`: 1
- `unless_conditionals`: 1

Conclusion: the pipeline is connected, but the solver lacks a parser layer that converts natural-language logical statements into normalized logical forms before symbolic reasoning attempts begin.

## 3. Architecture role

FormalLogicParser should:

- read runtime-only question/choice text only when explicitly allowed
- produce structured logical forms
- not select answers
- not use answer keys
- not use item ids as reasoning authority
- not claim official scores
- feed `FormalLogicSolver` and `ReasoningTrace`
- expose unsupported fragments instead of hiding them
- preserve human-legible translations of symbolic output

The parser is an enrichment layer, not a scorer and not an answer authority.

## 4. Proposed parser output schema

Future parser output structure: `LogicalFormParse`

Suggested fields:

- `parse_id`
- `statements`
- `premises`
- `candidate_conclusions`
- `operators`
- `quantifiers`
- `conditionals`
- `negations`
- `disjunctions`
- `conjunctions`
- `exceptions`
- `modality`
- `normalized_terms`
- `parse_confidence`
- `parse_warnings`
- `unsupported_fragments`
- `human_translation`

Design notes:

- `LogicalFormParse` is runtime evidence, not private authority.
- `parse_confidence` must be explicit and available to downstream blocking logic.
- `unsupported_fragments` must remain visible when partial parsing occurs.
- `human_translation` must explain the parser's symbolic interpretation in human-teachable language.

## 5. Statement schema

Each parsed statement should contain:

- `statement_id`
- `raw_text_runtime_only`
- `text_fingerprint`
- `normalized_text`
- `role` = `premise` / `conclusion_candidate` / `background` / `question_instruction`
- `logical_form`
- `confidence`
- `warnings`

Design constraints:

- `raw_text_runtime_only` must never be treated as a default persisted artifact.
- `text_fingerprint` allows correlation without exposing raw benchmark text.
- `normalized_text` should be human-readable normalization, not a benchmark-specific shortcut.

## 6. Supported parser families V1

FormalLogicParser V1 should define these general parser families:

- `natural_language_logical_form_extraction`
- `unless_conditionals`
- `disjunction_elimination_or_cases`
- `negation_detection`
- `quantifier_detection`
- `conclusion_prompt_detection`
- `choice_claim_extraction`

These families should be explicit in diagnostics so the reasoning engine can say what it recognized, what it translated, and what remains unsupported.

## 7. Natural-language logical-form extraction

`natural_language_logical_form_extraction` should map ordinary phrasing into normalized logical structures such as:

- atomic propositions
- implications
- negations
- quantified statements
- conjunctions
- disjunctions
- candidate conclusions

Examples of parser goals at the design level:

- detect proposition-bearing clauses from ordinary prose
- normalize semantically equivalent surface forms into stable logical representations
- separate premises from instructions like whether a conclusion follows
- preserve ambiguity when more than one logical reading is plausible

This is the broadest missing family because several failures were not tied to a narrow operator family but to the absence of a logical-form bridge itself.

## 8. Unless conditionals

Intended translation rule:

- `P unless Q` becomes `if not Q then P`

Equivalent human-teachable explanation:

- if the exception does not hold, the main claim holds

Design requirements:

- parser should record the translation used
- parser should mark ambiguity when natural language is unclear
- parser should not silently collapse ambiguous `unless` phrasing into a single authoritative reading

## 9. Disjunction / case analysis

Intended handling should cover:

- `either/or`
- `at least one`
- `none`
- `some`
- elimination of impossible cases
- preservation of ambiguity when multiple live cases remain

Design requirements:

- parser should expose the disjunctive structure explicitly
- solver may later eliminate impossible cases through traceable warrants
- answer selection must remain blocked when case analysis is still ambiguous

## 10. Trace integration

FormalLogicParser should later create trace nodes such as:

- `parsed_statement`
- `logical_form`
- `parser_warning`
- `unsupported_fragment`

And trace warrants such as:

- natural-language normalization
- conditional translation
- disjunction case split

This should increase trace edges and warrants relative to the current state, where dry-run created nodes but no edges and no conflicts across the diagnosed sample.

## 11. Cognitive legibility

Cognitive Legibility Boundary requirements:

- symbolic forms must be translated for humans
- parser output cannot become private authority
- unsupported fragments must remain visible
- low-confidence parse must block confident answer selection
- parser warrants must remain human-teachable

The parser is acceptable only if it expands transparency rather than hiding natural-language ambiguity behind symbolic compression.

## 12. Anti-gaming boundaries

FormalLogicParser must forbid:

- answer-key use
- item-id use
- benchmark-specific phrase rules
- raw benchmark storage by default
- official-score claims
- answer-position bias
- private symbolic authority

Additional boundary:

- no benchmark-specific memorization rules
- no answer-key memorization behavior
- no answer-key-derived training heuristics

## 13. Future implementation phases

A. parser dataclasses only  
B. parser helper functions  
C. parser redacted diagnostics  
D. FormalLogicSolver consumes parser output  
E. dry-run harness reports parser coverage  
F. arbitrator blocks low-confidence parse  
G. only later, optional MCQ adapter opt-in

This phase ordering preserves the Cognitive Legibility Boundary while avoiding premature solver rewrites.

## 14. Success criteria

Success is not an official score.

Success means:

- fewer `no_supported_pattern` statuses
- more trace edges and warrants
- `parse_confidence` recorded
- `unsupported_fragments` visible
- no raw benchmark storage by default
- no official-score claim

A successful parser layer improves diagnosis, structure, and explainability before it improves answer selection.
