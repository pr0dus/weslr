# CircleForge embedded models

This directory is for **local model files**, not for normal Git-tracked source code.

## Why the model is not in the GitHub repo

Large `.gguf` model files should usually **not** be committed directly into a normal GitHub repository.

Why:
- they make clones huge
- they make pushes unreliable
- they can exceed GitHub’s practical limits
- they pollute Git history even after later cleanup

So CircleForge keeps model files as **local artifacts**.

That means:
- GitHub repo = code, docs, setup, logic
- `models/` = local runtime assets you add separately

## Default embedded target

Current default target:
- **Qwen2.5-0.5B-Instruct**
- expected filename:
  - `qwen2.5-0.5b-instruct.gguf`

Default expected path:
- `CircleForge/models/qwen2.5-0.5b-instruct.gguf`

## If the file is missing

CircleForge is not necessarily broken.

It simply means:
- the embedded provider cannot run yet
- `llm-status` may report `fallback`
- the rest of the project can still be inspected and tested

## Clean public-distribution approaches

### Approach 1 — manual download + clear docs

Document:
- expected model filename
- expected placement path
- optional environment overrides

This is the simplest current approach.

### Approach 2 — release/external-hosted model asset

Provide the model separately through:
- GitHub Releases
- Hugging Face
- another downloadable host

Then tell users to:
1. download the file
2. place it in `models/`
3. run `python3 main.py llm-status`

## Helpful checks

```bash
python3 main.py llm-status
python3 main.py embedded-self-test
```

## Optional overrides

```bash
export CIRCLEFORGE_LLM_PROVIDER=embedded
export CIRCLEFORGE_EMBEDDED_MODEL_PATH=/full/path/to/model.gguf
export CIRCLEFORGE_LLM_MODEL=YourModelName
```

## Recommended human-facing explanation

If someone asks, “Why doesn’t the repo contain the model?” the simple answer is:

> The code is in GitHub. The local model is a separate runtime asset. That keeps the repo small, upload-safe, and easier for other people to clone.
