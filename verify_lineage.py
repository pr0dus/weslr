"""Lineage field verification — minimal first slice."""
import json, sys, os
from pathlib import Path

# ── Setup ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# ── Test 1: Root artifact (no parent) ────────────────────────────────────────
print("TEST 1: Root artifact (no parent)")
from weslr.artifact_store import save_artifact, get_artifact, _load_index

idx_before = _load_index()
root_id = save_artifact({
    "type": "artifact_revision",
    "content": "Root artifact test",
    "source": "test",
    "context": {},
})
root = get_artifact(root_id)
assert root is not None, "FAIL: root artifact not retrievable"

has_parents = "parent_artifact_ids" in root
has_root    = "root_artifact_id" in root
has_gen     = "generation" in root

print(f"  parent_artifact_ids present: {has_parents}  (expected: False — empty list not written)")
print(f"  root_artifact_id present:    {has_root}   (expected: True)")
print(f"  generation present:          {has_gen}     (expected: False — generation=0 not written)")

assert root["root_artifact_id"] == root_id, \
    f"FAIL: root_artifact_id should be self, got {root.get('root_artifact_id')}"
print(f"  root_artifact_id == self:   PASS  ({root_id})")
assert root.get("parent_artifact_ids", []) == [], "FAIL: parent_artifact_ids should be empty list"
print(f"  parent_artifact_ids == []:  PASS")
assert root.get("generation", -1) == 0, "FAIL: generation should be 0 for root"
print(f"  generation == 0:            PASS")
print("  TEST 1: PASS\n")

# ── Test 2: Derived artifact (with parent) ────────────────────────────────────
print("TEST 2: Derived artifact (parent = root)")
child_id = save_artifact({
    "type": "artifact_revision",
    "content": "Derived artifact test",
    "source": "test",
    "context": {},
    "parent_artifact_ids": [root_id],
    "root_artifact_id": root_id,
    "generation": 1,
})
child = get_artifact(child_id)
assert child is not None, "FAIL: child artifact not retrievable"

print(f"  parent_artifact_ids: {child.get('parent_artifact_ids')}  (expected: [{root_id}])")
print(f"  root_artifact_id:    {child.get('root_artifact_id')}  (expected: {root_id})")
print(f"  generation:          {child.get('generation')}        (expected: 1)")

assert child["parent_artifact_ids"] == [root_id], \
    f"FAIL: parent should be [root_id], got {child.get('parent_artifact_ids')}"
print(f"  parent_artifact_ids == [root_id]:  PASS")
assert child["root_artifact_id"] == root_id, \
    f"FAIL: root_artifact_id should be root_id, got {child.get('root_artifact_id')}"
print(f"  root_artifact_id == root_id:       PASS")
assert child["generation"] == 1, \
    f"FAIL: generation should be 1, got {child.get('generation')}"
print(f"  generation == 1:                    PASS")
print("  TEST 2: PASS\n")

# ── Test 3: Grandchild (generation 2) ─────────────────────────────────────────
print("TEST 3: Grandchild (generation 2)")
grandchild_id = save_artifact({
    "type": "artifact_revision",
    "content": "Grandchild artifact test",
    "source": "test",
    "context": {},
    "parent_artifact_ids": [child_id],
    "root_artifact_id": root_id,
    "generation": 2,
})
grandchild = get_artifact(grandchild_id)

print(f"  parent_artifact_ids: {grandchild.get('parent_artifact_ids')}  (expected: [{child_id}])")
print(f"  root_artifact_id:    {grandchild.get('root_artifact_id')}  (expected: {root_id})")
print(f"  generation:          {grandchild.get('generation')}        (expected: 2)")

assert grandchild["parent_artifact_ids"] == [child_id], "FAIL"
assert grandchild["root_artifact_id"] == root_id, "FAIL"
assert grandchild["generation"] == 2, "FAIL"
print("  TEST 3: PASS\n")

# ── Test 4: Backward compatibility (old artifact without lineage keys) ────────
print("TEST 4: Backward compatibility — old artifact loads without lineage keys")
old_shape = {
    "artifact_id": "art-0000000000001-1",
    "created_at": "2026-03-01T00:00:00Z",
    "type": "artifact_revision",
    "content": "Old artifact without lineage",
    "source": "legacy",
    "context": {},
}
old_path = BASE_DIR / "continuity" / "artifacts" / "art-0000000000001-1.json"
old_path.parent.mkdir(parents=True, exist_ok=True)
old_path.write_text(json.dumps(old_shape))

loaded = get_artifact("art-0000000000001-1")
assert loaded is not None, "FAIL: old artifact should load"
assert "parent_artifact_ids" not in loaded, "FAIL: old artifact should not have lineage keys"
assert "root_artifact_id" not in loaded, "FAIL: old artifact should not have root_artifact_id"
assert "generation" not in loaded, "FAIL: old artifact should not have generation"
print(f"  Loaded old artifact OK:    {loaded['artifact_id']}")
print(f"  No lineage keys present:    PASS")
old_path.unlink(missing_ok=True)
print("  TEST 4: PASS\n")

# ── Test 5: get_artifact returns None for unknown ID ─────────────────────────
print("TEST 5: Unknown artifact ID returns None")
unknown = get_artifact("art-this-does-not-exist")
assert unknown is None, "FAIL: unknown ID should return None"
print("  TEST 5: PASS\n")

# ── Cleanup ──────────────────────────────────────────────────────────────────
for aid in [root_id, child_id, grandchild_id]:
    p = BASE_DIR / "continuity" / "artifacts" / f"{aid}.json"
    p.unlink(missing_ok=True)

idx_after = _load_index()
assert idx_before == idx_after, "FAIL: index should be unchanged after cleanup"
print("INDEX: unchanged after cleanup — PASS")

print("\n" + "=" * 50)
print("ALL TESTS PASSED — lineage fields verified")
print("=" * 50)
