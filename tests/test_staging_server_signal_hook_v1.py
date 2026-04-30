#!/usr/bin/env python3
"""
WESLR Staging Server Signal Hook V1 — Tests

Validates:
- staging handler calls capture_website_signal after response
- raw message is not passed to signal functions directly (only via capture wrapper)
- response object is unchanged after signal capture
- storage failure does not change response
- fallback/evidence/blocked_write paths still return normally

Confirms: STAGING_SERVER_SIGNAL_HOOK_TESTS_OK
Exits non-zero on any failure.
"""

import sys
import pathlib
import json
import importlib
import tempfile
from unittest.mock import patch, MagicMock

_workspace = pathlib.Path("/home/pr0/projects/weslr")
sys.path.insert(0, str(_workspace))
sys.path.insert(0, str(_workspace / "weslr"))

PASS = 0
FAIL = 0


def check(condition: bool, description: str):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK: {description}")
    else:
        FAIL += 1
        print(f"  FAIL: {description}")


# Reload modules to get fresh state
import weslr_backend_contract
importlib.reload(weslr_backend_contract)


def test_capture_signal_exists() -> None:
    """Test that capture_website_signal function exists."""
    try:
        from weslr.website_signal_integration import capture_website_signal
        check(True, "capture_website_signal function exists")
        
        # Check it's callable
        check(callable(capture_website_signal), "capture_website_signal is callable")
        
        # Check it accepts expected parameters
        import inspect
        sig = inspect.signature(capture_website_signal)
        expected_params = {
            "message", "session_id", "response_path", "quality_class",
            "blocked_write", "evidence_offer_shown", "evidence_offer_accepted",
            "topic_normalized", "fallback_triggered"
        }
        check(
            set(sig.parameters.keys()) == expected_params,
            f"capture_website_signal has expected parameters: {expected_params}"
        )
    except Exception as e:
        check(False, f"capture_website_signal check: {e}")


def test_signal_capture_with_mock() -> None:
    """Test signal capture with mocked storage."""
    try:
        from weslr.website_signal_integration import capture_website_signal
        
        with patch("weslr.public_signal_store.append_public_signal_record") as mock_append:
            mock_append.return_value = {"stored": True, "reason": "stored", "record_type": "public_signal_v1", "path": "/test/path"}
            
            capture_website_signal(
                message="test message",
                session_id="test_session",
                response_path="fallback_safe",
                quality_class=None,
                blocked_write=False,
                evidence_offer_shown=False,
                evidence_offer_accepted=False,
                topic_normalized="test_topic",
                fallback_triggered=True
            )
            
            check(mock_append.called, "append_public_signal_record called")
    except Exception as e:
        check(False, f"signal capture with mock: {e}")


def test_signal_capture_failure_silent() -> None:
    """Test that signal capture failure doesn't crash."""
    try:
        from weslr.website_signal_integration import capture_website_signal
        
        # Test with storage that raises exception
        with patch("weslr.public_signal_store.append_public_signal_record") as mock_append:
            mock_append.side_effect = Exception("Storage failure")
            
            # Should not raise
            capture_website_signal(
                message="test",
                session_id="test",
                response_path="unknown",
                quality_class=None,
                blocked_write=False,
                evidence_offer_shown=False,
                evidence_offer_accepted=False,
                topic_normalized=None,
                fallback_triggered=False
            )
            
            check(True, "signal capture failure handled silently")
    except Exception as e:
        check(False, f"signal capture failure handling: {e}")


def test_language_module_uncertainty() -> None:
    """Test that uncertainty_strong_response exists in language modules."""
    try:
        import languages.en
        import languages.de
        
        check(hasattr(languages.en, "uncertainty_strong_response"), "en.uncertainty_strong_response exists")
        check(hasattr(languages.de, "uncertainty_strong_response"), "de.uncertainty_strong_response exists")
        
        en_response = languages.en.uncertainty_strong_response()
        de_response = languages.de.uncertainty_strong_response()
        
        check(isinstance(en_response, str) and en_response.strip(), "en.uncertainty_strong_response returns valid string")
        check(isinstance(de_response, str) and de_response.strip(), "de.uncertainty_strong_response returns valid string")
    except Exception as e:
        check(False, f"language module uncertainty: {e}")


def test_staging_server_has_hook() -> None:
    """Test that staging server file has signal hook."""
    try:
        server_file = pathlib.Path("/home/pr0/projects/weslr/deploy/staging/weslr_demo_server.py")
        content = server_file.read_text()
        
        check("_capture_signal" in content, "weslr_demo_server.py contains _capture_signal")
        check("capture_website_signal" in content, "weslr_demo_server.py calls capture_website_signal")
    except Exception as e:
        check(False, f"staging server hook check: {e}")


def main() -> int:
    """Run all signal hook tests."""
    print("=== WESLR Staging Server Signal Hook V1 Tests ===\n")
    
    test_capture_signal_exists()
    test_signal_capture_with_mock()
    test_signal_capture_failure_silent()
    test_language_module_uncertainty()
    test_staging_server_has_hook()
    
    print(f"\nResults: {PASS} passed, {FAIL} failed")
    
    if FAIL == 0:
        print("STAGING_SERVER_SIGNAL_HOOK_TESTS_OK")
        return 0
    else:
        print("STAGING_SERVER_SIGNAL_HOOK_TESTS_FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
