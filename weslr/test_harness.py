"""Weslr Test Harness (v1)

Internal testing infrastructure for Weslr capabilities.
Designed to be additive and reversible — no production modifications.

Test Families:
  - core software correctness
  - AI behavior / eval checks
  - security / red-team checks
  - privacy / access-control checks
  - governance checks
  - non-deterministic / metamorphic checks
  - monitoring / production behavior checks
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from unittest import TestCase, TestLoader, TestResult, TestSuite


__all__ = [
    "WeslrTestHarness",
    "register_weslr_tests",
]


class WeslrTestResult:
    """Result of a test execution."""
    
    def __init__(
        self,
        name: str,
        category: str,
        passed: bool,
        duration_ms: float = 0.0,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.category = category
        self.passed = passed
        self.duration_ms = duration_ms
        self.error = error
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "details": self.details,
        }
    
    @property
    def score(self) -> int:
        return 10 if self.passed else 0


class WeslrCategoryResult:
    """Aggregate result for a test category."""
    
    def __init__(self, category: str):
        self.category = category
        self.tests: List[WeslrTestResult] = []
    
    @property
    def passed_count(self) -> int:
        return sum(1 for t in self.tests if t.passed)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for t in self.tests if not t.passed)
    
    @property
    def total_count(self) -> int:
        return len(self.tests)
    
    @property
    def score(self) -> int:
        """Score out of 100 for this category."""
        if not self.tests:
            return 0
        pct = self.passed_count / self.total_count
        return int(pct * 100)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "total": self.total_count,
            "score": self.score,
            "tests": [t.to_dict() for t in self.tests],
        }


class WeslrTestHarness:
    """Test harness for Weslr capabilities.
    
    Provides:
    - Test registration by category
    - Category-level and aggregate test runs
    - Result reporting in required format
    """
    
    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or Path(__file__).resolve().parent
        self._categories: Dict[str, List[Callable]] = {}
        self._test_classes: List[type] = []
    
    def register_test(self, category: str, name: str, fn: Callable) -> None:
        """Register a single test function.
        
        Args:
            category: Test category (e.g., "security", "governance")
            name: Test name
            fn: Test function that takes TestCase and optional workspace_dir
        """
        if category not in self._categories:
            self._categories[category] = []
        
        # Wrap function in a method that can be used as a test
        def make_test_method():
            def test_method(self: TestCase):
                try:
                    fn(self, self.workspace_dir)
                    self.assertTrue(True)  # Ensure passing
                except Exception as e:
                    raise AssertionError(f"{name} failed: {e}") from e
            return test_method
        
        # Create dynamic test class
        test_class_name = f"Test{name.replace(' ', '_')}"
        test_class = type(test_class_name, (TestCase,), {
            f"test_{name.replace(' ', '_')}": make_test_method(),
            "workspace_dir": self.workspace_dir,
        })
        
        self._test_classes.append(test_class)
        self._categories[category].append(test_class)
    
    def register_test_class(self, category: str, test_class: type) -> None:
        """Register a test class (unittest.TestCase subclass)."""
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(test_class)
        self._test_classes.append(test_class)
    
    def run_category(self, category: str) -> WeslrCategoryResult:
        """Run all tests in a category.
        
        Args:
            category: Category name
            
        Returns:
            CategoryResult with aggregated results
        """
        if category not in self._categories:
            return WeslrCategoryResult(category)
        
        result = WeslrCategoryResult(category)
        loader = TestLoader()
        
        for test_class in self._categories[category]:
            suite = loader.loadTestsFromTestCase(test_class)
            runner = TestRunner(result)
            
            for test in suite:
                runner.run(test)
        
        return result
    
    def run_all(self) -> Dict[str, Any]:
        """Run all tests and return aggregate results.
        
        Returns:
            Result dict with:
            - ok: bool
            - categories: {category: {passed, failed, score}}
            - total_score: int
            - release_readiness: str
        """
        loader = TestLoader()
        all_results: Dict[str, WeslrCategoryResult] = {}
        
        for category, test_classes in self._categories.items():
            cat_result = WeslrCategoryResult(category)
            
            for test_class in test_classes:
                suite = loader.loadTestsFromTestCase(test_class)
                runner = TestRunner(cat_result)
                
                for test in suite:
                    runner.run(test)
            
            all_results[category] = cat_result
        
        # Calculate aggregate score
        total_score = sum(r.score for r in all_results.values())
        max_score = len(all_results) * 100
        
        # Determine release readiness
        if total_score >= 90:
            readiness = "public test ready"
        elif total_score >= 75:
            readiness = "limited/operator-supervised pilot"
        elif total_score >= 60:
            readiness = "private beta only"
        else:
            readiness = "not ready"
        
        # Format results
        categories_dict = {}
        for cat, res in all_results.items():
            # Scale category score to 0-100 based on category requirements
            # (actual scoring done in scorecard)
            categories_dict[cat] = {
                "passed": res.passed_count,
                "failed": res.failed_count,
                "score": res.score,
            }
        
        return {
            "ok": True,
            "categories": categories_dict,
            "total_score": total_score,
            "max_score": max_score,
            "release_readiness": readiness,
        }


class TestRunner:
    """Custom test runner that records results."""
    
    def __init__(self, category_result: WeslrCategoryResult):
        self.category_result = category_result
        self._start_time = None
    
    def run(self, test: TestCase) -> None:
        """Run a single test and record result."""
        import time
        
        test_name = str(test)
        # Extract category from test method name or class
        category = self.category_result.category
        
        self._start_time = time.time()
        
        try:
            test()
            duration = (time.time() - self._start_time) * 1000
            self.category_result.tests.append(WeslrTestResult(
                name=test_name,
                category=category,
                passed=True,
                duration_ms=duration,
            ))
        except AssertionError as e:
            duration = (time.time() - self._start_time) * 1000
            self.category_result.tests.append(WeslrTestResult(
                name=test_name,
                category=category,
                passed=False,
                duration_ms=duration,
                error=str(e),
            ))
        except Exception as e:
            duration = (time.time() - self._start_time) * 1000
            self.category_result.tests.append(WeslrTestResult(
                name=test_name,
                category=category,
                passed=False,
                duration_ms=duration,
                error=f"Unexpected error: {e}",
            ))


def register_weslr_tests(harness: WeslrTestHarness) -> None:
    """Register all standard Weslr V1 test cases.
    
    Tests cover:
    - File routing correctness
    - Upload safety boundaries
    - Operator-only visibility
    - No auto-approval/implementation
    - Review state transitions
    - Rollback behavior
    - Malformed input handling
    - Continuity persistence
    - Shell/backend contract
    """
    
    # Import test implementations
    from . import tests
    
    # Register all test classes from tests module
    for name in dir(tests):
        obj = getattr(tests, name)
        if isinstance(obj, type) and issubclass(obj, TestCase) and obj is not TestCase:
            # Determine category from class name or docstring
            category = _infer_category(name, obj)
            harness.register_test_class(category, obj)


def _infer_category(name: str, test_class: type) -> str:
    """Infer test category from class name or docstring."""
    name_lower = name.lower()
    docstring = (test_class.__doc__ or "").lower()
    
    # Check for data quality first (most specific)
    if ("quality" in name_lower or "data_quality" in name_lower
        or "data quality" in docstring or "sparse" in name_lower
        or "sparse" in docstring or "incomplete" in name_lower
        or "incomplete" in docstring or "malformed" in name_lower
        or "malformed" in docstring or "low information" in docstring
        or "representation" in name_lower or "representational" in docstring):
        return "data_quality"
    # Check for failure/monitoring next (most specific)
    elif ("failure" in name_lower or "monitoring" in name_lower
        or "timeout" in name_lower or "timeout" in docstring
        or "unavailable" in name_lower or "unavailable" in docstring
        or "corruption" in name_lower or "corruption" in docstring
        or "recovery" in name_lower or "recovery" in docstring
        or "transient" in name_lower or "transient" in docstring):
        return "failure_monitoring"
    # Check for privacy/role-boundary next (most specific)
    elif ("privacy" in name_lower or "privacy" in docstring
        or "role" in name_lower or "boundary" in name_lower
        or "visibility" in name_lower or "visibility" in docstring
        or "scoping" in name_lower or "scoping" in docstring
        or "isolation" in name_lower or "isolation" in docstring):
        return "privacy"
    # Check for non-deterministic/metamorphic next (most specific)
    elif ("metamorphic" in name_lower or "non_deterministic" in name_lower 
          or "non-deterministic" in name_lower or "metamorphic" in docstring
          or "stable" in docstring or "repeated" in docstring or "formatting" in name_lower):
        return "non_deterministic"
    elif "security" in name_lower or "red" in name_lower or "safety" in name_lower:
        return "security"
    elif "governance" in name_lower or "review" in name_lower:
        return "governance"
    elif "file" in name_lower or "upload" in name_lower or "route" in name_lower:
        return "file_data"
    elif "continuity" in name_lower or "persistence" in name_lower:
        return "continuity"
    elif "scientific" in name_lower or "workflow" in name_lower:
        return "scientific"
    elif "shell" in name_lower or "contract" in name_lower or "backend" in name_lower:
        return "shell_ux"
    else:
        return "core"


def create_test_harness(workspace_dir: Optional[Path] = None) -> WeslrTestHarness:
    """Create and configure a test harness with all standard tests."""
    harness = WeslrTestHarness(workspace_dir=workspace_dir)
    register_weslr_tests(harness)
    return harness


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """CLI interface for running tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Weslr Test Harness")
    parser.add_argument("--category", "-c", help="Run only this category")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--workspace", "-w", help="Workspace directory")
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace) if args.workspace else None
    harness = create_test_harness(workspace)
    
    if args.category:
        result = harness.run_category(args.category)
        if args.json:
            import json
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"Category: {result.category}")
            print(f"  Passed: {result.passed_count}/{result.total_count}")
            print(f"  Score:  {result.score}/100")
            print(f"{'='*60}")
            
            for test in result.tests:
                status = "✓" if test.passed else "✗"
                print(f"  {status} {test.name}")
                if test.error:
                    print(f"      Error: {test.error}")
    else:
        results = harness.run_all()
        if args.json:
            import json
            print(json.dumps(results, indent=2))
        else:
            print(f"\n{'='*60}")
            print("WESLR TEST HARNESS RESULTS")
            print(f"{'='*60}")
            print(f"\nTotal Score: {results['total_score']}/{results['max_score']}")
            print(f"Release Readiness: {results['release_readiness']}")
            print(f"\nCategories:")
            
            for cat, data in results['categories'].items():
                status = "✓" if data['score'] >= 80 else ("⚠" if data['score'] >= 50 else "✗")
                print(f"  {status} {cat}: {data['score']} ({data['passed']} passed, {data['failed']} failed)")
            
            print()


if __name__ == "__main__":
    main()
