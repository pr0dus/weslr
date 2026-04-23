// Node.js validation for lineage_inspector.py logic
// Tests 4 required cases + additional checks

const SCHEMA_VERSION = "1.0";

function inspect_artifact_lineage(artifact, threadIds = null) {
    const artifactId = artifact.artifact_id || "unknown";
    const parentIds = artifact.parent_artifact_ids || [];
    const rootId = artifact.root_artifact_id;
    const generation = artifact.generation;
    const hasGenerationField = "generation" in artifact;

    if (!hasGenerationField) {
        return {
            artifact_id: artifactId,
            lineage_status: "legacy_unknown",
            parent_artifact_ids: [],
            root_artifact_id: null,
            generation: null,
            thread_ids: threadIds || [],
            lineage_complete: false,
            notes: "Artifact predates lineage fields; parent/root/generation unknown.",
            schema_version: SCHEMA_VERSION,
        };
    }

    if (parentIds.length > 0 && rootId === null) {
        return {
            artifact_id: artifactId,
            lineage_status: "incomplete",
            parent_artifact_ids: parentIds.slice(),
            root_artifact_id: null,
            generation: generation !== undefined ? Number(generation) : null,
            thread_ids: threadIds || [],
            lineage_complete: false,
            notes: "Parent references present but root_artifact_id is unset; lineage incomplete.",
            schema_version: SCHEMA_VERSION,
        };
    }

    if (parentIds.length === 0 && generation === 0) {
        return {
            artifact_id: artifactId,
            lineage_status: "root",
            parent_artifact_ids: [],
            root_artifact_id: artifactId,
            generation: 0,
            thread_ids: threadIds || [],
            lineage_complete: true,
            notes: "Root artifact.",
            schema_version: SCHEMA_VERSION,
        };
    }

    return {
        artifact_id: artifactId,
        lineage_status: "derived",
        parent_artifact_ids: parentIds.slice(),
        root_artifact_id: rootId,
        generation: generation !== undefined ? Number(generation) : null,
        thread_ids: threadIds || [],
        lineage_complete: true,
        notes: `Derived from ${parentIds.length} parent${parentIds.length !== 1 ? 's' : ''}.`,
        schema_version: SCHEMA_VERSION,
    };
}

function test(name, artifact, expectedStatus) {
    const result = inspect_artifact_lineage(artifact);
    const ok = result.lineage_status === expectedStatus;
    console.log(`[${ok ? "PASS" : "FAIL"}] ${name}`);
    console.log(`       expected: ${expectedStatus}, got: ${result.lineage_status}`);
    console.log(`       notes: ${result.notes}`);
    if (!ok) {
        console.log(`       FULL: ${JSON.stringify(result)}`);
    }
    return ok;
}

let allPass = true;

// 1. new root artifact -> root
allPass &= test("new root artifact → root",
    { artifact_id: "art-root-1", parent_artifact_ids: [], root_artifact_id: "art-root-1", generation: 0 },
    "root");

// 2. new derived artifact -> derived
allPass &= test("new derived artifact → derived",
    { artifact_id: "art-derived-1", parent_artifact_ids: ["art-root-1"], root_artifact_id: "art-root-1", generation: 1 },
    "derived");

// 3. old artifact with no lineage fields -> legacy_unknown
allPass &= test("old artifact (no lineage fields) → legacy_unknown",
    { artifact_id: "art-old-1", content: "some old content" },
    "legacy_unknown");

// 4. malformed partial lineage -> incomplete
allPass &= test("incomplete lineage (parent without root) → incomplete",
    { artifact_id: "art-incomplete-1", parent_artifact_ids: ["art-root-1"], root_artifact_id: null, generation: 1 },
    "incomplete");

// 5. root lineage_complete=True
const r1 = inspect_artifact_lineage({ artifact_id: "art-r", parent_artifact_ids: [], root_artifact_id: "art-r", generation: 0 });
const ok5 = r1.lineage_complete === true;
console.log(`[${ok5 ? "PASS" : "FAIL"}] root artifact lineage_complete=True`);
allPass &= ok5;

// 6. legacy lineage_complete=False
const r2 = inspect_artifact_lineage({ artifact_id: "art-old", content: "x" });
const ok6 = r2.lineage_complete === false;
console.log(`[${ok6 ? "PASS" : "FAIL"}] legacy_unknown artifact lineage_complete=False`);
allPass &= ok6;

// 7. to_dict has all required fields
const r3 = inspect_artifact_lineage({ artifact_id: "art-d", parent_artifact_ids: ["p1"], root_artifact_id: "root1", generation: 2 });
const required = ["artifact_id", "lineage_status", "parent_artifact_ids", "root_artifact_id", "generation", "thread_ids", "lineage_complete", "notes", "schema_version"];
const ok7 = required.every(k => k in r3);
console.log(`[${ok7 ? "PASS" : "FAIL"}] to_dict has all required fields`);
allPass &= ok7;

// 8. schema_version is 1.0
const ok8 = r3.schema_version === "1.0";
console.log(`[${ok8 ? "PASS" : "FAIL"}] schema_version is 1.0`);
allPass &= ok8;

console.log();
console.log(allPass ? "All validation checks passed." : "Some checks FAILED.");
process.exit(allPass ? 0 : 1);
