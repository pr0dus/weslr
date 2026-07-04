from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "src"):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from weslr.arc_agi2_public_data_parse_only_validator import run_arc_agi2_public_data_parse_only_validation_v1


if __name__ == "__main__":
    manifest_path = Path(os.environ.get("WESLR_ARC_AGI2_PUBLIC_MANIFEST_PATH", ROOT / "config" / "arc_agi2_public_data_approval_manifest.parse_only.local.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result = run_arc_agi2_public_data_parse_only_validation_v1(
        manifest,
        repo_root=ROOT,
        staging_root=Path("/data/data/com.termux/files/home/weslr-arc-agi2-submission-staging"),
    )
    print(json.dumps({
        "approved_phase": result["approved_phase"],
        "checksum_match": result["checksum_match"],
        "schema_valid": result["schema_valid"],
        "grid_valid": result["grid_valid"],
        "solution_linkage_valid": result["solution_linkage_valid"],
        "redaction_valid": result["redaction_result"]["valid"],
        "zip_members": result["zip_members"],
        "json_file_names": result["json_file_names"],
        "file_counts": {name: summary["task_count"] for name, summary in result["file_summaries"].items()},
    }, indent=2, ensure_ascii=False))
