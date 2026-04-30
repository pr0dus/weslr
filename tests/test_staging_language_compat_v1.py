#!/usr/bin/env python3
"""Test language module compatibility for staging server signal hook.

This test verifies that:
1. uncertainty_strong_response exists in all language modules
2. The function returns valid strings
3. The functions are callable without side effects
"""

from __future__ import annotations

import sys
sys.path.insert(0, '/home/pr0/projects/weslr')

import importlib


def test_language_module(name: str) -> tuple[bool, list[str]]:
    """Test a language module for required functions.
    
    Args:
        name: Language module name (e.g., 'en', 'de')
        
    Returns:
        (passed: bool, errors: list[str])
    """
    try:
        lang = importlib.import_module(f'languages.{name}')
    except Exception as e:
        return False, [f"Failed to import languages.{name}: {e}"]
    
    errors = []
    
    # Check required function exists
    if not hasattr(lang, 'uncertainty_strong_response'):
        errors.append(f"Missing uncertainty_strong_response in languages.{name}")
    else:
        func = getattr(lang, 'uncertainty_strong_response')
        if not callable(func):
            errors.append(f"uncertainty_strong_response is not callable in languages.{name}")
        else:
            # Try calling it
            try:
                result = func()
                if not isinstance(result, str):
                    errors.append(f"uncertainty_strong_response returned non-string in languages.{name}: {type(result)}")
                elif not result.strip():
                    errors.append(f"uncertainty_strong_response returned empty string in languages.{name}")
            except Exception as e:
                errors.append(f"uncertainty_strong_response raised exception in languages.{name}: {e}")
    
    return len(errors) == 0, errors


def main() -> int:
    """Run all language module tests."""
    languages = ['en', 'de']
    
    all_passed = True
    for lang in languages:
        passed, errors = test_language_module(lang)
        if not passed:
            all_passed = False
            print(f"FAILED: languages.{lang}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"OK: languages.{lang}")
    
    # Test calling from weslr_backend_contract
    print("\n--- Testing weslr_backend_contract.chat() with unknown input ---")
    try:
        from weslr_backend_contract import chat
        
        # Test with a simple unknown message
        result = chat("asdasd123")
        
        if result.get("success"):
            print("OK: chat() succeeded for unknown input")
        else:
            error = result.get("error", "")
            if "uncertainty_strong_response" in error:
                print(f"FAILED: chat() still references missing uncertainty_strong_response: {error}")
                all_passed = False
            else:
                print(f"WARNING: chat() returned error but not uncertainty_strong_related: {error}")
    except Exception as e:
        if "uncertainty_strong_response" in str(e):
            print(f"FAILED: chat() raised uncertainty_strong_response error: {e}")
            all_passed = False
        else:
            print(f"WARNING: chat() raised exception but not uncertainty_strong_related: {e}")
    
    # Final verdict
    if all_passed:
        print("\n=== LANGUAGE_MODULE_COMPAT_TESTS_PASSED ===")
        return 0
    else:
        print("\n=== LANGUAGE_MODULE_COMPAT_TESTS_FAILED ===")
        return 1


if __name__ == "__main__":
    sys.exit(main())
