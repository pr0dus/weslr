"""Public subset schema helpers for official-style MCQ evaluation readiness.

Validation and provenance helpers only. No downloads, no internet, no runtime
answer changes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


REQUIRED_PUBLIC_PROVENANCE_FIELDS = [
    "dataset_name",
    "dataset_version",
    "dataset_source",
    "subset_name",
    "subset_size",
    "source_split",
    "license_note",
    "conversion_schema_version",
    "prompt_format_version",
    "adapter_version",
]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_suite_metadata(suite: dict) -> dict:
    _require(isinstance(suite, dict), "Suite metadata must be a JSON object.")

    suite_id = str(suite.get("suite_id") or suite.get("id") or "").strip()
    _require(bool(suite_id), "Suite must have suite_id or id.")

    sample_only = bool(suite.get("sample_only", False))
    official_score = bool(suite.get("official_score", False))
    internal_eval = bool(suite.get("internal_eval", False))

    _require(official_score is False, "official_score=true is not allowed in V1.")

    metadata = {
        "suite_id": suite_id,
        "sample_only": sample_only,
        "official_score": False,
        "internal_eval": internal_eval,
    }

    if sample_only:
        metadata["internal_eval"] = False
        for field in REQUIRED_PUBLIC_PROVENANCE_FIELDS:
            if field in suite:
                metadata[field] = suite[field]
        return metadata

    _require(internal_eval is True, "Public-subset suites must set internal_eval=true.")

    for field in REQUIRED_PUBLIC_PROVENANCE_FIELDS:
        value = suite.get(field)
        if field == "subset_size":
            _require(isinstance(value, int) and value > 0, f"{field} is required for public-subset suites.")
        else:
            _require(bool(str(value or "").strip()), f"{field} is required for public-subset suites.")
        metadata[field] = value

    metadata["sample_only"] = False
    metadata["internal_eval"] = True
    return metadata


def is_public_subset_suite(suite: dict) -> bool:
    try:
        metadata = validate_suite_metadata(suite)
    except Exception:
        return False
    return (
        metadata.get("sample_only") is False
        and metadata.get("internal_eval") is True
        and metadata.get("official_score") is False
    )


def build_run_provenance(suite_metadata: dict, repo_commit: str | None = None) -> dict:
    metadata = validate_suite_metadata(dict(suite_metadata))
    provenance = {
        "date_run": datetime.now(timezone.utc).isoformat(),
        "official_score": metadata["official_score"],
        "internal_eval": metadata["internal_eval"],
        "sample_only": metadata["sample_only"],
        "repo_commit": repo_commit,
    }

    for field in [
        "adapter_version",
        "conversion_schema_version",
        "prompt_format_version",
        "dataset_name",
        "dataset_version",
        "dataset_source",
        "subset_name",
        "subset_size",
        "source_split",
        "license_note",
    ]:
        provenance[field] = metadata.get(field)

    return provenance
