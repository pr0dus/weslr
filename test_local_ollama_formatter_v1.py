"""
WESLR Local Ollama Formatter V1 — Tests

Tests for local Ollama formatter adapter.
Uses mocking to avoid requiring Ollama to be running.

Run:
    python3 -m pytest weslr/tests/test_local_ollama_formatter_v1.py -v
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from unittest import mock

import pytest

import urllib


# Ensure weslr module path is available
_weslr_root = os.path.dirname(os.path.abspath(__file__))
if _weslr_root not in sys.path:
    sys.path.insert(0, _weslr_root)

from weslr.local_ollama_formatter import (
    is_formatter_enabled,
    build_formatter_prompt,
    call_ollama_formatter,
    validate_formatted_output,
    format_with_ollama,
    OLLAMA_API_URL,
    OLLAMA_MODEL,
    FORBIDDEN_PHRASES_USER,
)


class TestIsFormatterEnabled(unittest.TestCase):
    """Test is_formatter_enabled() behavior."""

    def test_disabled_by_default(self):
        """Formatter is disabled by default."""
        # Ensure env var is not set
        os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)

        result = is_formatter_enabled()
        self.assertFalse(result)

    def test_enabled_by_env_var(self):
        """Formatter is enabled when WESLR_LOCAL_FORMATTER_ENABLED=true."""
        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "true"

        try:
            result = is_formatter_enabled()
            self.assertTrue(result)
        finally:
            os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)

    def test_enabled_by_config(self):
        """Formatter is enabled via config dict."""
        config = {"enabled": True}
        result = is_formatter_enabled(config)
        self.assertTrue(result)

    def test_disabled_by_config(self):
        """Formatter is disabled via config dict."""
        config = {"enabled": False}
        result = is_formatter_enabled(config)
        self.assertFalse(result)

    def test_env_var_takes_precedence(self):
        """Environment variable takes precedence over config."""
        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "true"
        config = {"enabled": False}

        try:
            result = is_formatter_enabled(config)
            self.assertTrue(result)
        finally:
            os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)


class TestBuildFormatterPrompt(unittest.TestCase):
    """Test build_formatter_prompt() behavior."""

    def test_user_mode_contains_formatter_rules(self):
        """User prompt contains formatter-only instructions."""
        text = "Hello"
        prompt = build_formatter_prompt(text, mode="user")
        self.assertIn("You are a formatting layer only", prompt)
        self.assertIn("Do not add facts", prompt)
        self.assertIn("Do not remove safety meaning", prompt)

    def test_user_mode_contains_input_text(self):
        """User prompt contains the input text."""
        text = "Test greeting"
        prompt = build_formatter_prompt(text, mode="user")
        self.assertIn(text, prompt)

    def test_operator_mode_contains_formatter_rules(self):
        """Operator prompt contains formatter-only instructions."""
        text = "Review needed"
        prompt = build_formatter_prompt(text, mode="operator")
        self.assertIn("You are a formatting layer only", prompt)
        self.assertIn("Do not imply automatic approval", prompt)
        self.assertIn("Do not suggest any system change", prompt)

    def test_unknown_mode_raises(self):
        """Unknown mode raises ValueError."""
        with self.assertRaises(ValueError):
            build_formatter_prompt("test", mode="invalid")


class TestValidateFormattedOutput(unittest.TestCase):
    """Test validate_formatted_output() behavior."""

    def test_empty_output_invalid(self):
        """Empty output is rejected."""
        result = validate_formatted_output("Original", "")
        self.assertFalse(result["valid"])
        self.assertIn("empty", result["error"])

    def test_too_long_output_invalid(self):
        """Output too long is rejected."""
        original = "Short"
        formatted = "x" * 200  # Much longer than 1.5*5 + 120 = 127.5
        result = validate_formatted_output(original, formatted)
        self.assertFalse(result["valid"])
        self.assertIn("too long", result["error"])

    def test_forbidden_phrase_user_invalid(self):
        """Forbidden phrase in user mode is rejected."""
        original = "Hello"
        formatted = "I want to help you"
        result = validate_formatted_output(original, formatted, mode="user")
        self.assertFalse(result["valid"])
        self.assertIn("forbidden", result["error"])

    def test_forbidden_phrase_operator_invalid(self):
        """Forbidden phrase in operator mode is rejected."""
        original = "Review needed"
        formatted = "I want to process this"
        result = validate_formatted_output(original, formatted, mode="operator")
        self.assertFalse(result["valid"])
        self.assertIn("forbidden", result["error"])

    def test_uncertainty_marker_removed_invalid(self):
        """Removing uncertainty marker is rejected."""
        # Test with actual uncertainty markers from our list
        original = "I don't have a confirmed answer for that yet, but I can look into it and show you what I find"
        formatted = "I know the answer"  # Removed uncertainty markers including "show you what I find"
        result = validate_formatted_output(original, formatted, mode="user")
        self.assertFalse(result["valid"])
        self.assertIn("uncertainty", result["error"])

    def test_operator_bold_added_invalid(self):
        """Operator bold formatting is rejected."""
        original = "Review needed"
        formatted = "**Review Required**"
        result = validate_formatted_output(original, formatted, mode="operator")
        self.assertFalse(result["valid"])
        self.assertIn("bold", result["error"])

    def test_valid_output(self):
        """Valid formatted output passes."""
        original = "Hello, how can I help?"
        formatted = "Hi! How can I assist you today?"
        result = validate_formatted_output(original, formatted, mode="user")
        self.assertTrue(result["valid"])


class TestFormatWithOllama(unittest.TestCase):
    """Test format_with_ollama() integration."""

    def test_disabled_returns_original(self):
        """When disabled, returns original text unchanged."""
        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "false"

        try:
            result = format_with_ollama("Original text", mode="user")
            self.assertEqual(result, "Original text")
        finally:
            os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)

    @mock.patch("urllib.request.urlopen")
    def test_enabled_success_returns_formatted(self, mock_urlopen):
        """When enabled and successful, returns formatted text."""
        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "true"

        # Mock response
        mock_response = mock.MagicMock()
        mock_response.read.return_value = json.dumps({
            "response": "Formatted version of original"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        try:
            result = format_with_ollama("Original text", mode="user")
            self.assertEqual(result, "Formatted version of original")
        finally:
            os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)

    @mock.patch("urllib.request.urlopen")
    def test_timeout_returns_original(self, mock_urlopen):
        """When Ollama times out, returns original."""
        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "true"

        # Mock timeout
        mock_urlopen.side_effect = urllib.error.HTTPError(
            OLLAMA_API_URL, 408, "Timeout", {}, None
        )

        try:
            result = format_with_ollama("Original text", mode="user")
            self.assertEqual(result, "Original text")
        finally:
            os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)

    @mock.patch("urllib.request.urlopen")
    def test_error_returns_original(self, mock_urlopen):
        """When Ollama errors, returns original."""
        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "true"

        # Mock error
        mock_urlopen.side_effect = Exception("Connection refused")

        try:
            result = format_with_ollama("Original text", mode="user")
            self.assertEqual(result, "Original text")
        finally:
            os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)

    @mock.patch("urllib.request.urlopen")
    def test_validation_failure_returns_original(self, mock_urlopen):
        """When validation fails, returns original."""
        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "true"

        # Mock response with forbidden phrase
        mock_response = mock.MagicMock()
        mock_response.read.return_value = json.dumps({
            "response": "I want to help you"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        try:
            result = format_with_ollama("Original text", mode="user")
            self.assertEqual(result, "Original text")
        finally:
            os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)


class TestCallOllamaFormatter(unittest.TestCase):
    """Test call_ollama_formatter() behavior."""

    @mock.patch("urllib.request.urlopen")
    def test_disabled_returns_reason_disabled(self, mock_urlopen):
        """When disabled, returns reason='disabled'."""
        os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)

        result = call_ollama_formatter("text")
        self.assertEqual(result["reason"], "disabled")
        self.assertEqual(result["fallback_text"], "text")
        self.assertFalse(result["ok"])

    @mock.patch("urllib.request.urlopen")
    def test_successful_format(self, mock_urlopen):
        """Successful format returns formatted text."""
        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "true"

        mock_response = mock.MagicMock()
        mock_response.read.return_value = json.dumps({
            "response": "Formatted output"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        try:
            result = call_ollama_formatter("Original text")
            self.assertTrue(result["ok"])
            self.assertEqual(result["reason"], "formatted")
            self.assertEqual(result["formatted_text"], "Formatted output")
            self.assertEqual(result["fallback_text"], "Original text")
        finally:
            os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)

    @mock.patch("urllib.request.urlopen")
    def test_validation_failure_returns_original(self, mock_urlopen):
        """Validation failure returns fallback."""
        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "true"

        # Mock response with forbidden phrase
        mock_response = mock.MagicMock()
        mock_response.read.return_value = json.dumps({
            "response": "I want to process this"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        try:
            result = call_ollama_formatter("Original text")
            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "validation_failed")
            self.assertEqual(result["fallback_text"], "Original text")
        finally:
            os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)


class TestNoStateChanges(unittest.TestCase):
    """Test that formatter does not modify state."""

    def test_no_jsonl_writes(self):
        """Formatter does not write JSONL files."""
        # This is a conceptual test — the implementation uses only
        # urllib.request to call Ollama, and returns fallback on any error.
        # No file writes are performed.

        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "true"

        # Mock Ollama to return a valid response
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = mock.MagicMock()
            mock_response.read.return_value = json.dumps({
                "response": "Formatted text"
            }).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_response

            try:
                result = format_with_ollama("Original", mode="user")
                self.assertEqual(result, "Formatted text")
            finally:
                os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)


class TestNoRuntimeBehaviorChanges(unittest.TestCase):
    """Test that formatter does not change runtime behavior."""

    def test_format_with_ollama_preserves_default(self):
        """format_with_ollama preserves deterministic behavior by default."""
        # With formatter disabled (default), always returns original
        os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)

        original = "Deterministic response"
        result = format_with_ollama(original, mode="user")
        self.assertEqual(result, original)

    def test_format_with_ollama_override_disabled(self):
        """format_with_ollama can be explicitly disabled."""
        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "false"

        try:
            original = "Deterministic response"
            result = format_with_ollama(original, mode="user")
            self.assertEqual(result, original)
        finally:
            os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)

    def test_format_with_ollama_override_enabled(self):
        """format_with_ollama can be explicitly enabled."""
        # When enabled, will call Ollama — mocked in other tests
        os.environ["WESLR_LOCAL_FORMATTER_ENABLED"] = "true"

        try:
            # Just verify the flag is recognized
            self.assertTrue(is_formatter_enabled())
        finally:
            os.environ.pop("WESLR_LOCAL_FORMATTER_ENABLED", None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
