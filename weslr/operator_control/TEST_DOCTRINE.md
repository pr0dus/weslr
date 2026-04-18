# WESLR TEST DOCTRINE

Operational testing philosophy for WESLR development.

---

## 1. CORE TESTING PHILOSOPHY

### 1.1 Purpose of Tests

**Tests protect doctrine, not accidental implementation.**

- Tests encode the intended WESLR behavior and constraints
- Tests are the specification, not the implementation
- If implementation changes but behavior is preserved, tests should pass
- If tests fail, it indicates either:
  - A breaking change to WESLR doctrine (tests need updating)
  - A bug in the implementation (implementation needs fixing)

### 1.2 Behavior Over Implementation

**Behavior matters more than internal quirks.**

- Focus on observable behavior, not internal mechanics
- Test what users/operators see, not how it's computed
- Internal refactoring should not require test changes
- Public interfaces are the contract; tests enforce that contract

### 1.3 Additive Changes Require Backward Compatibility Tests

**Every additive change must include backward compatibility tests.**

- New fields, new methods, new layers should not break existing behavior
- Backward compatibility tests ensure old code continues to work
- When breaking changes are intentional, document them and update tests

---

## 2. MANDATORY TEST CATEGORIES

Each new WESLR layer must include all four test categories:

### 2.1 Model Tests (`Test<Layer>Model`)

**Purpose**: Verify data models, enums, and data structures.

**Scope**:
- Dataclass field presence and defaults
- Enum values and string representations
- Serialization/deserialization (to_dict/from_dict, to_json/from_json)
- Data validation (ranges, required fields, type constraints)

**Not included**:
- Business logic (behavior tests)
- Integration with other layers (integration tests)

### 2.2 Behavior Tests (`Test<Layer>Behavior`)

**Purpose**: Verify the layer's behavior from operator perspective.

**Scope**:
- Input/output behavior for public methods
- Edge cases and error conditions
- State transitions and side effects
- Configuration handling and customization

**Not included**:
- Internal state details (unless observable)
- Implementation-specific optimizations

### 2.3 Integration Hook Tests (`Test<Layer>Integration`)

**Purpose**: Verify the layer hooks into WESLR correctly.

**Scope**:
- Import/exports in `weslr/__init__.py`
- Dependencies on other layers
- Integration with operator workflow commands
- Backward compatibility with existing layers

**Not included**:
- Unit tests of dependencies (those are in their own test files)

### 2.4 Backward Compatibility Tests (`Test<Layer>BackwardCompatibility`)

**Purpose**: Verify the layer doesn't break existing WESLR functionality.

**Scope**:
- Existing code continues to work without changes
- Public API signatures remain compatible
- New fields don't break existing serialization
- Old commit state can still be interpreted

**Not included**:
- Full integration test suite (separate category)

---

## 3. STANDARD NAMING CONVENTIONS

### 3.1 Test File Names

- `weslr/test_<layer>.py` (e.g., `weslr/test_recommendation_delivery.py`)

### 3.2 Test Class Names

- `Test<Layer>Model` — data model tests
- `Test<Layer>Behavior` — behavior tests
- `Test<Layer>Integration` — integration hook tests
- `Test<Layer>BackwardCompatibility` — backward compatibility tests

### 3.3 Test Method Names

- `test_<action>_<condition>` (e.g., `test_to_dict_serialization`, `test_generation_with_full_data`)

---

## 4. WHEN TO CHANGE CODE VS TESTS

### 4.1 Change Code When:

- Behavior changes (unexpected or intentional)
- Bug fix changes observable behavior
- API signature changes (with version bump)
- Breaking change is intentional and documented

### 4.2 Change Tests When:

- **Always**: Fix broken tests (bug in test)
- **Always**: Update expectations when doctrine changes
- **Never**: Update tests to match bugs (fix the bug instead)
- **Never**: Add tests for incorrect behavior (fix the behavior first)

### 4.3 Decision Matrix

| Change Type | Code Change | Test Change |
|-------------|-------------|-------------|
| Bug fix | Required | Required (if test was wrong) |
| Behavioral change | Required | Required |
| API signature change | Required | Required |
| Refactoring (no behavior change) | Optional | Not required |
| New feature | Required | Required |

---

## 5. STANDARD TEST SUMMARY REPORTING

### 5.1 Test Run Command

```bash
python -m unittest weslr.test_<layer> -v
```

### 5.2 Summary Format

```
Ran X tests in Ys

OK (all passing)
# OR
FAILED (failures=Z)
```

### 5.3 Test Coverage Report

For each layer, report:

```
Layer: <layer_name>
Tests:
  - Model: X passed
  - Behavior: X passed
  - Integration: X passed
  - BackwardCompatibility: X passed
Total: X passed, Y failed
Commit: <hash>
```

### 5.4 CI/CD Integration

- All WESLR layers must pass tests before merge
- Test summary is included in commit message
- Test failures block PR merge until resolved

---

## 6. DOCTRINE VIOLATIONS

These are explicit violations of this doctrine and should be rejected:

- Adding a layer without all four test categories
- Deleting tests to make code changes easier
- Updating tests to match incorrect behavior
- Creating test classes without following naming conventions
- Skipping backward compatibility tests for "additive" changes

---

## 7. VERSIONING

### 7.1 Test Version Tracking

Include test version in test module docstring:

```python
"""Test suite for <layer> - Test Doctrine v1
Test Doctrine version: 1.0.0 (2026-04-06)
"""
```

### 7.2 Doctrine Version Bumping

- Update `TEST_DOCTRINE.md` version when breaking changes to testing approach
- Document changes in "CHANGES" section
- Update all test files to match new doctrine

---

*WESLR Operator Test Doctrine v1.0.0*
*Last updated: 2026-04-06*
