# WESLR Test Lane Audit V1

Date: 2026-05-08
Scope: repository-level test lane classification after packaging and dependency audit baseline

## Purpose

This audit defines how WESLR tests should be classified before full test execution becomes a blocking GitHub CI requirement.

The goal is not to rewrite the test suite in this pass. The goal is to prevent unstable or local-state-dependent tests from being treated as safe CI blockers before they are classified.

## Current known state

WESLR now has:

- root `pyproject.toml`
- optional dependency groups
- minimal GitHub Actions smoke CI
- successful install / compile / import smoke gate
- many existing tests spread across multiple locations
- an older `weslr/TESTING.md` that describes a broader test harness and scorecard

The current CI lane is intentionally conservative and does not execute the full test suite.

## Important finding: testing documentation drift

`weslr/TESTING.md` describes a general test harness and CLI runner with commands such as:

```bash
python -m weslr.run_tests
python -m weslr.run_tests --json
python -m weslr.run_tests --category SECURITY
```

However, the current `weslr/run_tests.py` is not a general harness runner. It is a narrow inline runner for explorer/materials-style tests and directly imports modules such as:

- `weslr.goal_decomposer`
- `weslr.hypothesis_scorer`
- `weslr.explore_engine`
- `weslr.commands.explore`

Therefore `weslr/TESTING.md` should be treated as historical/aspirational until the runner and scorecard are reconciled with current code reality.

## Current test locations observed

Tests are currently distributed across several patterns:

```text
weslr/test_*.py
weslr/tests/test_*.py
weslr/tests/weslr/test_*.py
weslr/request_intelligence/tests/test_*.py
tests/weslr/test_*.py
root-level test_*.py
weslr/voice_layer/test_*.py
```

This spread is not automatically wrong, but it means the repo needs explicit test lanes before CI can run tests safely.

## Proposed test lanes

### Lane 0 — Smoke CI

Purpose: prove the repo can install, compile, and import.

Current status: implemented.

Current checks:

```bash
pip install -e .[test]
python -m compileall -q weslr
python - <<'PY'
import weslr
print("WESLR import smoke OK")
PY
```

This lane should remain blocking for every PR.

### Lane 1 — Pure unit tests

Purpose: run deterministic tests that require only standard library or declared lightweight extras.

Allowed characteristics:

- no network
- no API keys
- no GPU
- no audio hardware
- no Cloudflare / systemd / server state
- no writes outside temporary directories
- no reliance on real `~/.weslr`
- no real LLM/provider calls
- no timing-sensitive benchmarks

Candidate areas likely to contain pure unit tests:

- request intelligence classifier
- deterministic handler classification
- safety contracts
- fact extraction
- capability registry/router/store logic
- consolidation logic if temp-rooted
- memory capture logic if temp-rooted
- entity memory if temp-rooted
- relationship depth if temp-rooted

Status: not yet blocking. Needs per-file verification.

### Lane 2 — Stateful local tests

Purpose: run tests that require local filesystem state, local WESLR root, or persistent JSONL/state fixtures.

Allowed only when tests explicitly use temporary roots or isolated fixtures.

Examples:

- memory namespace tests
- consolidation loop tests with local stores
- relationship observation capture
- channel binding tests
- project/entity memory tests
- JSONL archiver tests

Status: should not become blocking until each test confirms isolation from real `~/.weslr`.

### Lane 3 — Integration tests

Purpose: test multi-module flows.

Examples:

- chat responder paths
- workplace chat bridge
- evidence pipeline
- staging demo evidence bridge
- voice session routing without real audio
- main-door routing behavior

Requirements:

- clear fixtures
- no live services unless explicitly marked
- no external network unless manually triggered
- no real deployment mutation

Status: later CI lane, likely non-blocking at first.

### Lane 4 — External API / science tests

Purpose: test scientific and materials workflows that may use external services.

Examples:

- Materials Project checks
- arXiv/PubMed/COD/OQMD/AFLOW/NOMAD adapters
- Scatti/CaSc2TiO6 novelty workflow

Requirements:

- manually triggered workflow
- secrets supplied through GitHub Actions only
- clear API timeouts
- cache or fixture mode when possible
- no claim of scientific proof from screening tests

Status: future manually triggered lane.

### Lane 5 — Voice / hardware tests

Purpose: test TTS/STT/playback behavior.

Examples:

- gTTS generation
- Piper/espeak detection
- Termux media playback
- microphone/STT bridge
- local voice loop

Requirements:

- local runner or device-specific environment
- never required for generic GitHub-hosted CI
- hardware/backend capability detection

Status: local/Ubuntu/Termux lane, not GitHub-hosted default.

### Lane 6 — Deployment/runtime tests

Purpose: test staging and runtime deployment.

Examples:

- `staging.weslr.de`
- Cloudflare Tunnel presence
- systemd service status
- Ubuntu/OCW runtime forge
- website build/deploy

Requirements:

- self-hosted runner or explicitly controlled deployment workflow
- environment protection rules
- no automatic destructive deploys

Status: future Ubuntu/OCW runner lane.

## Immediate recommended CI policy

Do not expand the current blocking CI beyond Lane 0 until Lane 1 has a verified file list.

Recommended next patch after this audit:

1. Add a test inventory script that lists tests and tags obvious risk markers.
2. Create `docs/TEST_LANE_INVENTORY_V1.md` from that inventory.
3. Select a small Lane 1 pilot list of pure tests.
4. Add a non-blocking GitHub Actions job for Lane 1 pilot.
5. Promote Lane 1 pilot to blocking only after it passes repeatedly.

## Risk markers to detect before running tests in CI

A test should not be placed in Lane 1 if it contains or imports patterns such as:

```text
requests
socket
subprocess
threading
http.server
Path.home()
~/.weslr
os.environ required values
API_KEY
MATERIALS_PROJECT_API_KEY
cloudflared
systemctl
termux
mpv
ffplay
piper
espeak
gTTS
TTS
sleep/time benchmark assertions
real provider / LLM calls
```

These patterns do not mean the test is bad. They mean the test needs classification before becoming blocking.

## Testing documentation correction needed

`weslr/TESTING.md` should eventually be updated to distinguish:

- historical harness design
- current actual `weslr/run_tests.py` behavior
- GitHub Actions smoke CI
- future test lanes

Do not delete `weslr/TESTING.md` in this pass. It contains useful test-family thinking, but it should not be treated as fully accurate current operator guidance.

## Current conclusion

WESLR has many tests, but the suite is not yet ready to be run as one blocking CI command.

The correct next maturity step is controlled test-lane classification, not brute-force full-suite execution.

V1 stance:

- Lane 0 smoke CI is active and should remain blocking.
- Lane 1 pure unit CI should be piloted with a small verified list.
- Stateful, integration, science, voice, and deployment tests should remain separate lanes.
- No local-only or external-service tests should block normal PRs by default.
