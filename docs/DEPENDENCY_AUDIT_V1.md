# WESLR Dependency Audit V1

Date: 2026-05-08
Scope: root Python packaging baseline after Repo Product Identity Pass V1

## Purpose

This document records the first dependency audit for the main WESLR repository.

The goal is not to claim that every dependency is fully known. The goal is to separate:

1. core runtime dependencies that must be installed for WESLR to import and compile,
2. optional feature dependencies used by specific modules,
3. local/system dependencies that should not be installed through Python packaging,
4. unknowns that require a later local/runtime audit.

## Audit result

The current core WESLR package can install, compile, and import on GitHub Actions with no runtime Python dependencies beyond the standard library.

Therefore root `pyproject.toml` keeps:

```toml
dependencies = []
```

This is intentional. It protects the install path from pulling optional, heavy, platform-specific, or feature-specific packages into every environment.

## Optional dependency groups added

### `test`

Used for test execution.

```toml
test = ["pytest>=8"]
```

### `search`

Used by search adapters and web/resource retrieval modules that import `requests`.

```toml
search = ["requests>=2.31"]
```

### `files`

Used by modules that parse YAML or structured files.

```toml
files = ["PyYAML>=6.0"]
```

### `voice`

Used by the voice layer for Google TTS support.

```toml
voice = ["gTTS>=2.5"]
```

### `voice-gpu`

Used by the optional Coqui/XTTS path.

```toml
voice-gpu = ["TTS>=0.22"]
```

This group is intentionally separated because it can be heavy, GPU-sensitive, and unsuitable for Android/Termux or minimal CI.

### `science`

Used by scientific/materials workflows that query external APIs.

```toml
science = ["requests>=2.31"]
```

The `MATERIALS_PROJECT_API_KEY` secret is available for later workflows, but no default CI lane should require it.

### `all`

Convenience development extra without GPU-heavy dependencies.

```toml
all = ["pytest>=8", "requests>=2.31", "PyYAML>=6.0", "gTTS>=2.5"]
```

`TTS` is intentionally excluded from `all` because it is too heavy and platform-specific for default installs.

## Non-Python / system dependencies

Some WESLR features depend on binaries or host capabilities rather than Python packages.

Examples:

- `piper` binary for Piper TTS
- `espeak` / `espeak-ng` for local fallback TTS
- `termux-media-player`, `mpv`, or `ffplay` for playback
- Node/Vite dependencies for `weslr-ui` and other frontend surfaces
- Cloudflare Tunnel / systemd / deployment services for runtime deployment
- Siemens TIA Portal / Openness tooling for the industrial bridge

These should not be declared as Python runtime dependencies.

## Why full dependencies are not declared yet

The repo currently contains multiple product tracks:

- core WESLR runtime
- public surface / website
- industrial Siemens/TIA bridge
- Scatti and frontier science workflows
- voice/local bridge
- deployment/runtime forge
- historical memory and experimental modules

A single broad dependency list would be unsafe and misleading. It would make minimal installs heavier and could break clean CI on modules that are not part of the current smoke gate.

## Current install modes

Minimal core smoke install:

```bash
pip install -e .[test]
```

Search/API workflows:

```bash
pip install -e .[search]
```

File/YAML workflows:

```bash
pip install -e .[files]
```

Voice workflows without GPU:

```bash
pip install -e .[voice]
```

Science/materials workflows:

```bash
pip install -e .[science]
```

General development without GPU-heavy TTS:

```bash
pip install -e .[all]
```

## Current CI stance

The first CI lane remains a smoke gate:

- install package with test extras
- compile `weslr`
- import `weslr`
- list tests non-blocking

Full tests should not become blocking until dependencies, fixtures, local state, and integration requirements are classified.

## Follow-up audit tasks

1. Generate a full import inventory from a local clone.
2. Classify each import as standard library, project-local, Python package, system binary, frontend dependency, or unknown.
3. Identify tests that are pure unit tests and safe for GitHub CI.
4. Move local-state or integration tests into separate test lanes.
5. Add a manually triggered Scatti/materials workflow that uses `MATERIALS_PROJECT_API_KEY`.
6. Add frontend dependency audit for `weslr-ui`, `front-door`, and dashboard assets.
7. Add deployment dependency audit for Ubuntu/OCW runtime.

## V1 conclusion

Dependency Audit V1 establishes a conservative dependency contract:

- core stays standard-library-first,
- optional features receive named extras,
- heavy/platform-specific dependencies stay out of default install,
- full test execution waits for a separate test-lane audit.
