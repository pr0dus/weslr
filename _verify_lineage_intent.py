#!/usr/bin/env python3
"""Verify lineage_intent end-to-end."""
import sys
import os
import json

# Ensure workspace is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from weslr.artifact_store import save_artifact, get_artifact, _load_index, ARTIFACTS_DIR
from weslr.lineage_inspector import inspect_artifact_lineage

# Save index state before
idx_before = _load_index()

# 1. Root artifact (no parent fields)
root_id = save_artifact({
    "type": "artifact_revision",
    "content": "root test artifact",
    "source": "verify",
})
print(f"ROOT_ID: {root_id}")

# 2. Derived artifact (with parent fields)
derived_id = save_artifact({
    "type": "artifact_revision",
    "content": "derived test artifact",
    "source": "verify",
    "parent_artifact_ids": [root_id],
    "root_artifact_id": root_id,
    "generation": 1,
})
print(f"DERIVED_ID: {derived_id}")

# 3. Show stored JSON
root = get_artifact(root_id)
derived = get_artifact(derived_id)

print("\n=== ROOT ARTIFACT STORED JSON ===")
print(json.dumps(root, indent=2))

print("\n=== DERIVED ARTIFACT STORED JSON ===")
print(json.dumps(derived, indent=2))

# 4. Run lineage inspection on both
root_insp = inspect_artifact_lineage(root)
derived_insp = inspect_artifact_lineage(derived)

print("\n=== ROOT LINEAGE INSPECTION ===")
print(json.dumps(root_insp.to_dict(), indent=2))

print("\n=== DERIVED LINEAGE INSPECTION ===")
print(json.dumps(derived_insp.to_dict(), indent=2))

# 5. Verify lineage_intent present
assert "lineage_intent" in root, f"FAIL: lineage_intent missing from root"
assert "lineage_intent" in derived, f"FAIL: lineage_intent missing from derived"
assert root["lineage_intent"] == "root", f"FAIL: root lineage_intent = {root['lineage_intent']}"
assert derived["lineage_intent"] == "derived", f"FAIL: derived lineage_intent = {derived['lineage_intent']}"

# 6. Verify status
assert root_insp.lineage_status == "root", f"FAIL: root status = {root_insp.lineage_status}"
assert derived_insp.lineage_status == "derived", f"FAIL: derived status = {derived_insp.lineage_status}"

# 7. Legacy fallback: find an old artifact without lineage_intent
print("\n=== LEGACY FALLBACK CHECK ===")
index = _load_index()
legacy_found = False
for aid in index:
    if aid in (root_id, derived_id):
        continue
    art = get_artifact(aid)
    if art and "generation" not in art and "lineage_intent" not in art:
        insp = inspect_artifact_lineage(art)
        print(f"Legacy artifact: {aid}")
        print(json.dumps(insp.to_dict(), indent=2))
        assert insp.lineage_status == "legacy_unknown", f"FAIL: legacy status = {insp.lineage_status}"
        legacy_found = True
        break

if not legacy_found:
    print("(No legacy artifacts found — skipping legacy check)")

# Cleanup
for aid in [root_id, derived_id]:
    p = ARTIFACTS_DIR / f"{aid}.json"
    p.unlink(missing_ok=True)
idx_after = _load_index()
assert idx_before == idx_after, "FAIL: index not restored after cleanup"

print("\nVERDICT: PASS")
