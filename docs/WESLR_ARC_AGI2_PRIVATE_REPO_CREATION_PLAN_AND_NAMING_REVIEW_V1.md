# WESLR ARC-AGI-2 Private Repo Creation Plan and Naming Review V1

## 1. Source state
- Repository: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Audit-grounded HEAD: `41a15d2899b767b87a92a7f5f89a044384119f01`
- Actual current HEAD: `7d8745c6e1cacc5cfa1163949e3cb4eff8b8c338`
- Current HEAD commit message: `Add ARC AGI-2 local public submission staging audit`
- The exact hash `7d8745c6257f0b1f02a2af77bc6c7a9a6e7f5f5c` is not available as written; the verified current HEAD is the nearby audit-report commit above.
- Staging directory inspected: `/data/data/com.termux/files/home/weslr-arc-agi2-submission-staging`
- Staging audit result: passed and ready for private repo creation planning
- Official/public ARC data untouched: yes
- Official percentage remains: none/0
- Dummy public-surface report remains present and uncommitted in the source repo:
  - `docs/WESLR_ARC_OFFICIAL_PUBLIC_PARSE_SCORER_SURFACE_DUMMY_IMPLEMENTATION_V1.md`

## 2. Naming review
### Recommended package / repo name
- Recommended repo name: `weslr-arc-agi2-submission`

### Repo name candidates reviewed
- `weslr-arc-agi2-submission` — recommended
- `weslr-arc-prize-2026` — too broad / claim-adjacent
- `weslr-arc-agi2-kaggle` — acceptable, but less explicit than the recommended name

### Import package name
- Recommended import package: `weslr_arc_solver`
- Rationale: matches the staged package layout, avoids unnecessary churn, and keeps the public package import path short and stable.

### README title
- Recommended title: `weslr-arc-agi2-submission`
- Optional subtitle: `Local public submission package for ARC-AGI-2`

### License / notice consistency
- Keep `LICENSE` as MIT unless owner policy later requires a different open-source license.
- Keep `NOTICE.md` aligned with the package name and with the no-official-claim wording.
- Ensure README/NOTICE do not imply official score, leaderboard, Kaggle result, prize eligibility, or solved-ARC claims.

## 3. Private repo creation plan
### Visibility recommendation
- Create the repo private first for packaging review and freeze control.
- Make it public only when the package is frozen and ready for prize-eligible submission or public release.

### First commit source
- Use the staged export tree as the first public-package source base.
- Preserve the manifest/hash file from the staging tree as the initial integrity baseline.
- Do not import additional private WESLR-only code after freeze unless it is explicitly copied into the public package and reviewed.

### Branch naming
- Recommended initial branch: `main`
- If using a review branch internally first: `prep/public-package-review`

### Files to include in the private/public package
- `README.md`
- `LICENSE`
- `NOTICE.md`
- `requirements.txt`
- `pytest.ini`
- `submission_notebook_skeleton.py` (or a later notebook artifact once safe)
- `src/weslr_arc_solver/`
- `tests/`
- `docs/METHOD.md`
- `docs/REPRODUCIBILITY.md`
- `docs/NO_INTERNET_EVALUATION.md`
- `docs/PRIVATE_EXCLUSION_CHECKLIST.md`
- `EXPORT_REPORT.md`
- `EXPORT_AUDIT.md`
- `MANIFEST.sha256`

### Files to exclude
- Private WESLR docs and handoff material
- OpenClaw/OCC/Nova instructions and agent context
- `.weslr` state or runtime data
- website/deployment material
- secrets, tokens, credentials, auth configs
- user-specific absolute paths
- unrelated WESLR product code
- official/public ARC data bundles
- hidden/private data
- experimental reports with unsupported claims
- generated caches or build debris

### Secrets/private-path preflight
Before any GitHub repo creation:
1. Re-scan the staged package for private paths and credential words.
2. Confirm no private WESLR imports remain.
3. Confirm manifest coverage matches the exported tree.
4. Confirm the notebook skeleton has no network/API/provider calls.
5. Confirm no official/public ARC data or claim wording was introduced.

### Manifest/hash preservation
- Keep `MANIFEST.sha256` in the exported tree.
- Regenerate only if files change after the freeze point.
- Treat hash drift as a release-blocking change unless deliberately authorized.

### Post-creation validation commands
After any repo creation or visibility flip, run:
- `git diff --check`
- `python -m pytest -q tests/test_dummy_no_data_smoke.py`
- manifest coverage check against `MANIFEST.sha256`
- private path / claim scan on README/docs
- notebook import and path isolation check

## 4. Stop conditions before GitHub creation
Do not create the GitHub repo yet if any of these are true:
- package naming still feels claim-adjacent or ambiguous
- private WESLR imports remain in the public tree
- manifest coverage does not match the exported files
- notebook skeleton still needs public-path cleanup
- any official score / leaderboard / Kaggle / prize / percentage claim appears
- official/public ARC data appears anywhere in the export
- the staging smoke test no longer passes
- the package still depends on runtime/web/provider/OCC paths

## 5. Validation results
- `git diff --check`: pass
- source repo release gate: pass
- source repo release check: pass
- no official/public ARC data touched: confirmed
- no private path/secrets introduced into staged package: confirmed after audit cleanup
- no repo creation performed: confirmed

## 6. Verdict
- Naming verdict: `weslr-arc-agi2-submission` is the best final package/repo name.
- Private repo creation plan verdict: ready for a private repo creation step once the owner approves the freeze.

## 7. Exact recommended first commit procedure
1. Create private repo `weslr-arc-agi2-submission`.
2. Push or import only the staged export tree snapshot.
3. Keep `main` as the default branch.
4. Preserve `MANIFEST.sha256`, `EXPORT_REPORT.md`, and `EXPORT_AUDIT.md` in the first commit.
5. Run the post-creation validation commands above.
6. Only after that, decide whether to make the repo public for the final open-source release.

## 8. Next recommended lane
- Create the private repo only after owner approval of the freeze and naming choice; then perform a public-package readiness review before any visibility change.
