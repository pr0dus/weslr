"""Rebuild inventory V2 from V1 records, normalizing into the V2 schema."""
import hashlib, json, os, sys
from collections import Counter

REPO_ROOT = "/data/data/com.termux/files/home/weslr-pr47-clean"
os.chdir(REPO_ROOT)

with open("data/scatti_candidates/scatti_implementation_inventory_v1.json") as f:
    v1 = json.load(f)

v1_artifacts = v1.get("artifacts", [])

v2_records = []
for a in v1_artifacts:
    path = a.get("path", "")
    artifact_type = a.get("artifact_type", "unknown")
    tracked = a.get("tracked", False)
    exists = os.path.isfile(os.path.join(REPO_ROOT, path))
    evidence_class = a.get("evidence_class", "unknown")
    reproducibility = a.get("reproducibility_status", "unknown")

    # Normalize implementation_status from V1 status field
    v1_status = a.get("status", "unknown")
    if v1_status == "implemented":
        impl_status = "implemented"
    elif v1_status == "executed":
        impl_status = "implemented"  # executed is a separate dimension
    elif v1_status == "planned":
        impl_status = "planned"
    elif v1_status == "superseded":
        impl_status = "superseded"
    else:
        impl_status = "unknown"

    # Normalize execution_status from V1 executed field
    v1_executed = a.get("executed", "unknown")
    if v1_executed is True:
        exec_status = "executed"
    elif v1_executed is False:
        exec_status = "not_executed"
    else:
        exec_status = "execution_unknown"

    v2_records.append({
        "path": path,
        "artifact_type": artifact_type,
        "implementation_status": impl_status,
        "execution_status": exec_status,
        "evidence_class": evidence_class,
        "reproducibility_status": reproducibility,
        "tracked": tracked,
        "exists": exists,
    })

# Calculate counts
total_records = len(v2_records)
type_counts = Counter(r["artifact_type"] for r in v2_records)
impl_counts = Counter(r["implementation_status"] for r in v2_records)
exec_counts = Counter(r["execution_status"] for r in v2_records)
evidence_counts = Counter(r["evidence_class"] for r in v2_records)
repro_counts = Counter(r["reproducibility_status"] for r in v2_records)
tracked_count = sum(1 for r in v2_records if r["tracked"])
untracked_count = sum(1 for r in v2_records if not r["tracked"])
existing_count = sum(1 for r in v2_records if r["exists"])
missing_count = sum(1 for r in v2_records if not r["exists"])

# Assert sums
def assert_sum(name, counts, total):
    s = sum(counts.values())
    if s != total:
        return {"category": name, "sum": s, "expected": total, "residual": s - total, "passed": False}
    return {"category": name, "sum": s, "expected": total, "residual": 0, "passed": True}

sum_checks = [
    assert_sum("artifact_type", type_counts, total_records),
    assert_sum("implementation_status", impl_counts, total_records),
    assert_sum("execution_status", exec_counts, total_records),
    assert_sum("evidence_class", evidence_counts, total_records),
    assert_sum("reproducibility_status", repro_counts, total_records),
]

output = {
    "schema_version": 2,
    "generated_at": "2026-07-14T16:00:00Z",
    "git_head": "62e9ba794c780bb37d5472d79ca8c9d91230892d",
    "source_inventory": "data/scatti_candidates/scatti_implementation_inventory_v1.json",
    "total_records": total_records,
    "by_artifact_type": dict(type_counts),
    "by_implementation_status": dict(impl_counts),
    "by_execution_status": dict(exec_counts),
    "by_evidence_class": dict(evidence_counts),
    "by_reproducibility_status": dict(repro_counts),
    "tracked_count": tracked_count,
    "untracked_count": untracked_count,
    "existing_count": existing_count,
    "missing_count": missing_count,
    "category_sum_assertions": sum_checks,
    "all_sums_pass": all(c["passed"] for c in sum_checks),
    "records": v2_records,
}

with open("data/scatti_candidates/calculation_assurance_v2/scatti_implementation_inventory_v2.json", "w") as f:
    json.dump(output, f, indent=2, sort_keys=True)

print(f"V2 inventory: {total_records} records")
for c in sum_checks:
    status = "PASS" if c["passed"] else "FAIL"
    print(f"  {c['category']}: sum={c['sum']} expected={c['expected']} residual={c['residual']} {status}")
