#!/usr/bin/env python3
"""Validate lineage_inspector.py on the 4 required test cases."""

import sys
sys.path.insert(0, '/data/data/com.termux/files/home/.openclaw/workspace')

from weslr.lineage_inspector import inspect_artifact_lineage, ArtifactLineageInspection
import json

def test(name, artifact, expected_status, thread_ids=None):
    result = inspect_artifact_lineage(artifact, thread_ids=thread_ids)
    ok = result.lineage_status == expected_status
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}")
    print(f"       expected: {expected_status}, got: {result.lineage_status}")
    print(f"       notes: {result.notes}")
    if not ok:
        print(f"       FULL OUTPUT: {json.dumps(result.to_dict(), indent=2)}")
    return ok

all_pass = True

# 1. new root artifact classifies as "root"
all_pass &= test("new root artifact → root",
    {'artifact_id': 'art-root-1', 'parent_artifact_ids': [], 'root_artifact_id': 'art-root-1', 'generation': 0},
    "root")

# 2. new derived artifact classifies as "derived"
all_pass &= test("new derived artifact → derived",
    {'artifact_id': 'art-derived-1', 'parent_artifact_ids': ['art-root-1'], 'root_artifact_id': 'art-root-1', 'generation': 1},
    "derived")

# 3. old artifact with no lineage fields classifies as "legacy_unknown"
all_pass &= test("old artifact (no lineage fields) → legacy_unknown",
    {'artifact_id': 'art-old-1', 'content': 'some old content'},
    "legacy_unknown")

# 4. malformed partial lineage classifies as "incomplete"
all_pass &= test("incomplete lineage (parent without root) → incomplete",
    {'artifact_id': 'art-incomplete-1', 'parent_artifact_ids': ['art-root-1'], 'root_artifact_id': None, 'generation': 1},
    "incomplete")

# 5. root artifact should have lineage_complete=True
r = inspect_artifact_lineage({'artifact_id': 'art-r', 'parent_artifact_ids': [], 'root_artifact_id': 'art-r', 'generation': 0})
ok = r.lineage_complete == True
print(f"[{'PASS' if ok else 'FAIL'}] root artifact lineage_complete=True")
all_pass &= ok

# 6. legacy artifact should have lineage_complete=False
r = inspect_artifact_lineage({'artifact_id': 'art-old', 'content': 'x'})
ok = r.lineage_complete == False
print(f"[{'PASS' if ok else 'FAIL'}] legacy_unknown artifact lineage_complete=False")
all_pass &= ok

# 7. verify to_dict output has all required fields
r = inspect_artifact_lineage({'artifact_id': 'art-d', 'parent_artifact_ids': ['p1'], 'root_artifact_id': 'root1', 'generation': 2})
d = r.to_dict()
required = ['artifact_id', 'lineage_status', 'parent_artifact_ids', 'root_artifact_id', 'generation', 'thread_ids', 'lineage_complete', 'notes', 'schema_version']
ok = all(k in d for k in required)
print(f"[{'PASS' if ok else 'FAIL'}] to_dict has all required fields")
all_pass &= ok

# 8. verify schema_version is set
ok = r.schema_version == "1.0"
print(f"[{'PASS' if ok else 'FAIL'}] schema_version is 1.0")
all_pass &= ok

# 9. verify inspect_artifact_lineage_by_id returns None for unknown artifact
from weslr.lineage_inspector import inspect_artifact_lineage_by_id
r = inspect_artifact_lineage_by_id("nonexistent-artifact-id-xyz")
ok = r is None
print(f"[{'PASS' if ok else 'FAIL'}] inspect_artifact_lineage_by_id returns None for unknown ID")
all_pass &= ok

print()
if all_pass:
    print("All validation checks passed.")
    sys.exit(0)
else:
    print("Some checks FAILED.")
    sys.exit(1)
