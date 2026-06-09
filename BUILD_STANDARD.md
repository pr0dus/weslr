# WESLR Build Standard V1

## 1. Implementation style
- Use pure Python where possible.
- Keep behavior deterministic.
- Prefer metadata-only unless explicitly approved otherwise.
- Keep outputs JSON-safe.
- Keep helpers side-effect-free.
- Avoid filesystem, network, or subprocess behavior except normal validation commands.
- Avoid environment reads unless explicitly approved.
- Avoid provider/model calls.
- Avoid hidden runtime wiring.

## 2. Testing standard
For new or changed Python work, run:
- `python -m py_compile` on new/changed Python files
- focused `pytest` for new tests
- neighboring tests when relevant and cheap
- `python weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`
- `git diff --check`
- protected-file checks

## 3. Validation standard
Fail closed on:
- unsafe authority
- unknown statuses or enums
- raw private text
- public-claim escalation
- runtime/tool/provider/persistence implication
- `.weslr` implication
- final-answer authority implication
- hidden prompt leakage

## 4. Git hygiene
- Inspect status before editing.
- Do not touch unrelated uncommitted files.
- Commit only allowed related files.
- Remove generated `__pycache__` or `.pyc` artifacts if created.

## 5. Final report requirements
A completed lane report should include:
- repo root
- start HEAD
- end HEAD / commit hash
- files changed
- tests run
- validation results
- protected files status
- release gate status
- gaps or deferred work
- final judgment
