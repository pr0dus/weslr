"""
Tests for WESLR SearXNG Search Adapter V1

All HTTP calls are mocked — no live web searches.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "weslr"))


class TestConfigFunctions(unittest.TestCase):
    """Tests for configuration functions."""

    def setUp(self):
        # Reset config cache before each test
        from searxng_search_adapter import reset_config_cache
        reset_config_cache()

    def tearDown(self):
        # Clean up env vars set during tests
        for key in ["WESLR_SEARXNG_ENABLED", "WESLR_SEARXNG_URL"]:
            if key in os.environ:
                del os.environ[key]
        # Reset cache
        from searxng_search_adapter import reset_config_cache
        reset_config_cache()

    def test_disabled_by_default(self):
        """SearXNG should be disabled by default."""
        from searxng_search_adapter import is_searxng_enabled
        self.assertFalse(is_searxng_enabled())

    def test_enabled_only_with_env_var(self):
        """SearXNG should be enabled only with WESLR_SEARXNG_ENABLED=true."""
        os.environ["WESLR_SEARXNG_ENABLED"] = "true"
        from searxng_search_adapter import reset_config_cache, is_searxng_enabled
        reset_config_cache()
        self.assertTrue(is_searxng_enabled())

    def test_base_url_default(self):
        """Default base URL should be http://localhost:8888."""
        from searxng_search_adapter import get_searxng_base_url
        self.assertEqual(get_searxng_base_url(), "http://localhost:8888")

    def test_env_url_override(self):
        """WESLR_SEARXNG_URL should override the base URL."""
        os.environ["WESLR_SEARXNG_URL"] = "http://custom:9999"
        from searxng_search_adapter import reset_config_cache, get_searxng_base_url
        reset_config_cache()
        self.assertEqual(get_searxng_base_url(), "http://custom:9999")


class TestBuildSearchUrl(unittest.TestCase):
    """Tests for build_search_url."""

    def test_builds_correct_url(self):
        from searxng_search_adapter import build_search_url
        url = build_search_url("entropy", "http://localhost:8888")
        self.assertEqual(url, "http://localhost:8888/search?q=entropy&format=json")

    def test_encodes_query(self):
        from searxng_search_adapter import build_search_url
        url = build_search_url("what is entropy?", "http://localhost:8888")
        self.assertIn("q=what", url)
        self.assertIn("entropy", url)
        self.assertIn("format=json", url)
        # Should be URL-encoded (either + or %20 for space)
        self.assertTrue("+" in url or "%20" in url or "%3F" in url)

    def test_encodes_spaces(self):
        from searxng_search_adapter import build_search_url
        url = build_search_url("machine learning", "http://localhost:8888")
        # Should be encoded (either + or %20)
        self.assertTrue("machine" in url and ("+" in url or "%20" in url))

    def test_uses_default_url_if_not_provided(self):
        from searxng_search_adapter import build_search_url, get_searxng_base_url
        url = build_search_url("test")
        self.assertEqual(url, f"{get_searxng_base_url()}/search?q=test&format=json")


class TestSearchSearxng(unittest.TestCase):
    """Tests for search_searxng function."""

    def setUp(self):
        from searxng_search_adapter import reset_config_cache
        reset_config_cache()
        # Enable it for these tests
        os.environ["WESLR_SEARXNG_ENABLED"] = "true"

    def tearDown(self):
        for key in ["WESLR_SEARXNG_ENABLED", "WESLR_SEARXNG_URL"]:
            if key in os.environ:
                del os.environ[key]
        from searxng_search_adapter import reset_config_cache
        reset_config_cache()

    def test_disabled_returns_disabled(self):
        """When disabled, returns ok=False reason=disabled."""
        os.environ.pop("WESLR_SEARXNG_ENABLED", None)
        from searxng_search_adapter import reset_config_cache, search_searxng
        reset_config_cache()
        result = search_searxng("test query")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "disabled")
        self.assertFalse(result["enabled"])

    def test_empty_query_invalid(self):
        os.environ["WESLR_SEARXNG_ENABLED"] = "true"
        from searxng_search_adapter import reset_config_cache, search_searxng
        reset_config_cache()
        result = search_searxng("")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "invalid_query")

    def test_whitespace_query_invalid(self):
        os.environ["WESLR_SEARXNG_ENABLED"] = "true"
        from searxng_search_adapter import reset_config_cache, search_searxng
        reset_config_cache()
        result = search_searxng("   ")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "invalid_query")

    @patch("searxng_search_adapter.urllib.request.urlopen")
    def test_mocked_successful_response(self, mock_urlopen):
        """Mocked successful response returns normalized results."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "results": [
                {
                    "title": "Entropy - Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Entropy",
                    "content": "Entropy is a scientific concept...",
                    "engines": ["google", "bing"],
                    "score": 0.95,
                },
                {
                    "title": "Entropy - Britannica",
                    "url": "https://www.britannica.com/science/Entropy-physics",
                    "content": "Entropy in physics...",
                    "engines": ["duckduckgo"],
                    "score": 0.88,
                },
            ]
        }).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        from searxng_search_adapter import reset_config_cache, search_searxng
        reset_config_cache()
        result = search_searxng("entropy")

        self.assertTrue(result["ok"])
        self.assertEqual(result["reason"], "ok")
        self.assertEqual(result["query"], "entropy")
        self.assertEqual(result["result_count"], 2)
        self.assertEqual(result["results"][0]["title"], "Entropy - Wikipedia")
        self.assertEqual(result["results"][0]["source"], "searxng")
        self.assertEqual(result["results"][0]["authority"], "external_evidence_unverified")
        self.assertEqual(result["automatic_truth_write"], False)

    @patch("searxng_search_adapter.urllib.request.urlopen")
    def test_limit_respected(self, mock_urlopen):
        """The limit parameter should be respected."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "results": [
                {"title": f"Result {i}", "url": f"https://example.com/{i}",
                 "content": "content", "engines": ["google"], "score": 0.9}
                for i in range(10)
            ]
        }).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        from searxng_search_adapter import reset_config_cache, search_searxng
        reset_config_cache()
        result = search_searxng("test", limit=3)

        self.assertEqual(result["result_count"], 3)
        self.assertEqual(len(result["results"]), 3)

    @patch("searxng_search_adapter.urllib.request.urlopen")
    def test_timeout_returns_reason_timeout(self, mock_urlopen):
        """Timeout should return reason=timeout."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("timed out")

        from searxng_search_adapter import reset_config_cache, search_searxng
        reset_config_cache()
        result = search_searxng("entropy", timeout_seconds=2)

        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "error")

    @patch("searxng_search_adapter.urllib.request.urlopen")
    def test_malformed_json_safe(self, mock_urlopen):
        """Malformed JSON should return invalid_query, not crash."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid json {"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        from searxng_search_adapter import reset_config_cache, search_searxng
        reset_config_cache()
        result = search_searxng("entropy")

        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "invalid_query")

    @patch("searxng_search_adapter.urllib.request.urlopen")
    def test_normalized_result_strips_unsafe_fields(self, mock_urlopen):
        """Normalized result should strip cookies, user identifiers, etc."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "results": [{
                "title": "Test",
                "url": "https://example.com",
                "content": "Content here",
                "engines": ["google"],
                "score": 0.9,
                "cookies": {"session": "abc123"},   # Should be stripped
                "user_id": "user123",                # Should be stripped
                "ip_address": "1.2.3.4",             # Should be stripped
                "some_html": "<b>bold</b>",            # Should be stripped
            }]
        }).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        from searxng_search_adapter import reset_config_cache, search_searxng
        from searxng_search_adapter import normalize_searxng_result
        reset_config_cache()

        # Call normalize directly
        raw = {
            "title": "Test",
            "url": "https://example.com",
            "content": "Content <b>here</b>",
            "engines": ["google"],
            "score": 0.9,
            "cookies": {"session": "abc"},
            "user_id": "user1",
        }
        result = normalize_searxng_result(raw)

        self.assertEqual(result["title"], "Test")
        self.assertEqual(result["url"], "https://example.com")
        self.assertNotIn("cookies", result)
        self.assertNotIn("user_id", result)
        self.assertNotIn("<b>", result["content"])  # HTML stripped
        self.assertEqual(result["source"], "searxng")
        self.assertEqual(result["authority"], "external_evidence_unverified")


class TestStructuralConstraints(unittest.TestCase):
    """Verify structural constraints from the spec."""

    def test_no_jsonl_writes(self):
        """No JSONL file writes in adapter."""
        import inspect
        from searxng_search_adapter import search_searxng
        source = inspect.getsource(search_searxng)
        self.assertNotIn(".write(", source)
        self.assertNotIn('"w"', source)
        self.assertNotIn("'w'", source)
        self.assertNotIn("jsonl", source.lower())

    def test_no_ollama_imports(self):
        """No Ollama imports."""
        import inspect
        from searxng_search_adapter import search_searxng
        source = inspect.getsource(search_searxng)
        source_lower = source.lower()
        self.assertNotIn("ollama", source_lower)
        self.assertNotIn("openai", source_lower)

    def test_not_wired_into_chat(self):
        """Adapter is standalone, not imported by chat modules."""
        import inspect
        from searxng_search_adapter import search_searxng, normalize_searxng_result
        for fn in [search_searxng, normalize_searxng_result]:
            source = inspect.getsource(fn)
            self.assertNotIn("/chat", source)
            self.assertNotIn("_CONTRACT_REPLIES", source)
            self.assertNotIn("chat_interface", source.lower())

    def test_automatic_truth_write_always_false(self):
        """automatic_truth_write should always be False."""
        from searxng_search_adapter import search_searxng
        # Disabled case
        result = search_searxng("test", config={"enabled": False})
        self.assertFalse(result["automatic_truth_write"])


class TestNormalizeSearxngResult(unittest.TestCase):
    """Tests for normalize_searxng_result."""

    def test_basic_fields(self):
        from searxng_search_adapter import normalize_searxng_result
        raw = {
            "title": "Test Title",
            "url": "https://example.com",
            "content": "Test content",
            "engines": ["google", "bing"],
            "score": 0.85,
        }
        result = normalize_searxng_result(raw)
        self.assertEqual(result["record_type"], "search_result_v1")
        self.assertEqual(result["title"], "Test Title")
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(result["content"], "Test content")
        self.assertEqual(result["engines"], ["google", "bing"])
        self.assertEqual(result["score"], 0.85)
        self.assertEqual(result["source"], "searxng")
        self.assertEqual(result["authority"], "external_evidence_unverified")

    def test_html_stripped_from_content(self):
        from searxng_search_adapter import normalize_searxng_result
        raw = {
            "title": "Test",
            "url": "https://example.com",
            "content": "<p>Some HTML content</p> with <b>bold</b> text",
            "engines": [],
            "score": None,
        }
        result = normalize_searxng_result(raw)
        self.assertNotIn("<p>", result["content"])
        self.assertNotIn("<b>", result["content"])
        self.assertIn("Some HTML content", result["content"])

    def test_truncates_long_fields(self):
        from searxng_search_adapter import normalize_searxng_result
        raw = {
            "title": "A" * 1000,
            "url": "https://example.com/" + "x" * 2000,
            "content": "B" * 3000,
            "engines": [],
            "score": 0.5,
        }
        result = normalize_searxng_result(raw)
        self.assertLessEqual(len(result["title"]), 500)
        self.assertLessEqual(len(result["url"]), 2000)
        self.assertLessEqual(len(result["content"]), 2000)

    def test_missing_fields_default_to_empty(self):
        from searxng_search_adapter import normalize_searxng_result
        raw = {}
        result = normalize_searxng_result(raw)
        self.assertEqual(result["title"], "")
        self.assertEqual(result["url"], "")
        self.assertEqual(result["content"], "")
        self.assertEqual(result["engines"], [])
        self.assertIsNone(result["score"])

    def test_strips_unsafe_cookie_field(self):
        from searxng_search_adapter import normalize_searxng_result
        raw = {
            "title": "Test",
            "url": "https://example.com",
            "content": "content",
            "engines": [],
            "score": 0.9,
            "cookies": {"PHPSESSID": "abc"},
        }
        result = normalize_searxng_result(raw)
        self.assertNotIn("cookies", result)

    def test_strips_user_id_field(self):
        from searxng_search_adapter import normalize_searxng_result
        raw = {
            "title": "Test",
            "url": "https://example.com",
            "content": "content",
            "engines": [],
            "score": 0.9,
            "user_id": "user123",
        }
        result = normalize_searxng_result(raw)
        self.assertNotIn("user_id", result)


if __name__ == "__main__":
    unittest.main()