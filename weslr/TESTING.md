# Weslr Testing & Scoring System (v1)

Additive and reversible test infrastructure for Weslr capabilities.

## Files Added

```
weslr/
├── test_harness.py          # Core test harness class
├── test_scorecard.py        # Release scoring system
├── tests/
│   ├── __init__.py          # Test implementations
│   ├── test_harness_*.py    # Optional: additional harness tests
│   └── test_scorecard_*.py  # Optional: additional scorecard tests
└── run_tests.py             # CLI test runner
```

## Test Harness (`test_harness.py`)

### `WeslrTestHarness` Class

```python
class WeslrTestHarness:
    def register_test(self, category, name, fn):
        """Register a single test."""
    
    def run_category(self, category):
        """Run all tests in a category."""
    
    def run_all(self):
        """Run all tests, return results dict."""
```

### Result Format

```python
{
    "ok": True,
    "categories": {
        "security": {"passed": 8, "failed": 1, "score": 16},
        "governance": {"passed": 10, "failed": 0, "score": 20},
    },
    "total_score": 84,
    "max_score": 100,
    "release_readiness": "limited/operator-supervised pilot",
}
```

### CLI Usage

```bash
# Run all tests
python -m weslr.run_tests

# Run with JSON output
python -m weslr.run_tests --json

# Run specific category
python -m weslr.run_tests --category SECURITY

# Run with specific workspace
python -m weslr.run_tests --workspace /path/to/workspace
```

## Scorecard (`test_scorecard.py`)

### `WeslrScorecard` Class

```python
class WeslrScorecard:
    def calculate_scores(self, results):
        """Calculate weighted scores from test results."""
    
    def release_readiness(self, total_score):
        """Determine release readiness level."""
    
    def evaluate(self, results):
        """Full evaluation: scores + readiness."""
```

### Category Scoring (100 points total)

| Category | Points | Weight |
|----------|--------|--------|
| Security Coverage | 20 | 20% |
| Governance Integrity | 20 | 20% |
| File/Data Understanding | 20 | 20% |
| Continuity Integrity | 15 | 15% |
| Scientific Workflow | 15 | 15% |
| Shell/UX Reliability | 10 | 10% |

### Release Readiness Levels

| Score | Level |
|-------|-------|
| 90-100 | Public test ready |
| 75-89 | Limited/operator-supervised pilot |
| 60-74 | Private beta only |
| Below 60 | Not ready |

### CLI Usage

```bash
# Evaluate existing results
python -m weslr.test_scorecard --input results.json

# Evaluate with detailed output
python -m weslr.test_scorecard --input results.json --detailed
```

## Test Families (V1 Coverage)

### 1. Core Software Correctness
- File routing to correct handlers
- Structured data handling
- Text file processing
- Binary file safety

### 2. AI Behavior / Eval Checks
- Assessment scoring consistency
- Priority assignment validity
- Fit score calculation

### 3. Security / Red-Team Checks
- Secret scrubbing
- Input validation
- Rate limiting
- Path traversal prevention
- Size limits

### 4. Privacy / Access-Control Checks
- Operator-only visibility
- Review state transitions
- No auto-approval
- No auto-implementation

### 5. Governance Checks
- Valid requester type enforcement
- Review history persistence
- State machine integrity

### 6. Non-Deterministic / Metamorphic Checks
- UUID generation consistency
- Timestamp precision
- Idempotent operations

### 7. Monitoring / Production Behavior Checks
- Shell/Backend contract
- Continuity persistence
- State rollback
- Error handling

## V1 Real Test Coverage

| Feature | Test File | Coverage |
|---------|-----------|----------|
| File upload / routing | `TestFileRoutingCorrectness` | ✓ |
| PDF understanding | `TestFileRoutingCorrectness` | ✓ |
| Generic text ingestion | `TestFileRoutingCorrectness` | ✓ |
| Structured data | `TestMalformedInputFallback` | ✓ |
| Scientific notebook | `TestScientificIntegrity` | ✓ |
| Scientific evidence timeline | `TestContinuityPersistence` | ✓ |
| Materials analysis | `TestScientificIntegrity` | ✓ |
| Suggestion box | `TestSuggestionBridgeIntegrity` | ✓ |
| Suggestion bridge | `TestSuggestionBridgeIntegrity` | ✓ |
| Weslr assessment | `TestSuggestionBridgeIntegrity` | ✓ |
| Operator review flow | `TestOperatorOnlyVisibility` | ✓ |
| Shell/backend contract | `TestShellBackendContract` | ✓ |
| Continuity persistence | `TestContinuityPersistence` | ✓ |
| Rollback behavior | `TestContinuityIntegrity` | ✓ |
| Malformed input fallback | `TestMalformedInputFallback` | ✓ |
| No auto-approval | `TestNoAutoApproval` | ✓ |
| No auto-implementation | `TestNoAutoImplementation` | ✓ |
| Review state transitions | `TestReviewStateTransitions` | ✓ |

## Architecture Notes

- **Additive only**: No production files are modified
- **Reversible**: Remove `weslr/test_*.py` and `weslr/tests/` to undo
- **Isolated**: Uses temp directories for tests
- **No external dependencies**: Uses `unittest` from stdlib

## Extending Tests

### Add New Test Class

```python
from unittest import TestCase

class TestYourFeature(TestCase):
    def test_your_test(self):
        # Your test logic here
        self.assertTrue(True)
```

### Register in `tests/__init__.py`

Test classes are auto-discovered by naming convention.

### Add New Category

Update `WeslrScorecard.CATEGORY_WEIGHTS`:

```python
CATEGORY_WEIGHTS = {
    "new_category": 10,  # 10 points
    # ... existing categories
}
```

## Commit Hash

```
Created: 2026-04-04
Files: weslr/test_harness.py, weslr/test_scorecard.py, weslr/tests/__init__.py
```

## Safe Rollback

```bash
# Remove test harness
rm weslr/test_harness.py
rm weslr/test_scorecard.py
rm -rf weslr/tests/
rm weslr/run_tests.py

# No other files are modified
```

## Why This Matters (OC Coder View)

1. **Testability First**: Weslr is now testable from day one with a proper harness
2. **Release Gate**: Scorecard provides objective release readiness metrics
3. **Risk Mitigation**: Red-team/security tests catch issues before production
4. **Audit Trail**: All tests are reproducible and versioned
5. **CI Ready**: Harness works in CI with minimal setup (no Docker needed)
6. **Extensible**: New test families can be added without touching core
7. **Operator Confidence**: Scorecard gives operators clear go/no-go signals
8. **Safe Experimentation**: Test harness runs in isolation, no prod risk

## Next Steps (Not in V1)

- [ ] CI integration (GitHub Actions / GitLab CI)
- [ ] Performance benchmarks
- [ ] Load/stress tests
- [ ] Chaos testing integration
- [ ] Automated regression detection
- [ ] Release notes auto-generation
