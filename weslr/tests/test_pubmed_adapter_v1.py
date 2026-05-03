"""Tests for PubMed adapter and evidence packet storage — Phase 4.2."""
from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.search_adapters.pubmed_adapter import esearch, efetch, search_pubmed
from weslr.search_adapters.evidence_packet_store import append_evidence_packet, load_packets, get_packet


# ─── Mock XML for efetch ──────────────────────────────────────────────────────

_MOCK_EFETCH_XML = b"""<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>BRCA1 mutations and breast cancer survival</ArticleTitle>
        <Abstract>
          <AbstractText>Background: BRCA1 mutation carriers have increased mortality. Methods: We studied 500 patients. Results: Survival was 75% at 5 years. p-value = 0.001. Conclusion: Early intervention improves outcomes.</AbstractText>
        </Abstract>
        <Journal>
          <Title>Nature Medicine</Title>
        </Journal>
        <PubDate>
          <Year>2023</Year>
        </PubDate>
        <AuthorList>
          <Author><LastName>Zhang</LastName><ForeName>Wei</ForeName></Author>
          <Author><LastName>Smith</LastName><ForeName>John</ForeName></Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


class TestPubmedAdapter(unittest.TestCase):
    """Unit tests for PubMed adapter — mocked HTTP."""

    @patch("weslr.search_adapters.pubmed_adapter.requests")
    def test_esearch_returns_pmids(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "esearchresult": {"idlist": ["12345678", "87654321"]}
        }
        mock_requests.get.return_value = mock_resp

        # Patch sleep to be instant
        with patch("weslr.search_adapters.pubmed_adapter.time.sleep"):
            pmids = esearch("BRCA1 breast cancer", retmax=5)

        self.assertEqual(pmids, ["12345678", "87654321"])
        mock_requests.get.assert_called_once()
        args = mock_requests.get.call_args
        self.assertEqual(args[1]["params"]["db"], "pubmed")
        self.assertEqual(args[1]["params"]["retmax"], 5)

    @patch("weslr.search_adapters.pubmed_adapter.requests")
    def test_efetch_parses_article(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.content = _MOCK_EFETCH_XML
        mock_requests.get.return_value = mock_resp

        with patch("weslr.search_adapters.pubmed_adapter.time.sleep"):
            articles = efetch(["12345678"])

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["pmid"], "12345678")
        self.assertEqual(articles[0]["title"], "BRCA1 mutations and breast cancer survival")
        self.assertEqual(articles[0]["journal"], "Nature Medicine")
        self.assertEqual(articles[0]["year"], "2023")
        self.assertIn("Wei", articles[0]["authors"][0])
        self.assertIn("75%", articles[0]["abstract"])

    @patch("weslr.search_adapters.pubmed_adapter.requests")
    def test_search_pubmed_combines_calls(self, mock_requests):
        mock_esearch_resp = MagicMock()
        mock_esearch_resp.json.return_value = {
            "esearchresult": {"idlist": ["12345678"]}
        }
        mock_efetch_resp = MagicMock()
        mock_efetch_resp.content = _MOCK_EFETCH_XML
        mock_requests.get.side_effect = [mock_esearch_resp, mock_efetch_resp]

        with patch("weslr.search_adapters.pubmed_adapter.time.sleep"):
            pmids, articles = search_pubmed("BRCA1", max_results=5)

        self.assertEqual(pmids, ["12345678"])
        self.assertEqual(len(articles), 1)


class TestEvidencePacketStore(unittest.TestCase):
    """Tests for evidence packet storage."""

    def test_append_and_load_packet(self, tmp_path=None):
        # Use a temp file for isolation
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "external_evidence_packets.jsonl"

            packet = {
                "record_type": "external_evidence_packet_v1",
                "source": "pubmed",
                "query": "BRCA1 test",
                "retrieved_at": "2026-05-03T10:00:00Z",
                "result_count": 2,
                "results": [{"pmid": "123", "title": "Test"}],
                "authority": "external_evidence_unverified",
                "automatic_change": False,
                "hidden_learning": False,
                "raw_prompt_stored": False,
            }

            result = append_evidence_packet(packet, doc_store_path=store)
            self.assertEqual(result["status"], "appended")
            self.assertIn("packet_id", result)

            packets = load_packets(limit=10, doc_store_path=store)
            self.assertEqual(len(packets), 1)
            self.assertEqual(packets[0]["query"], "BRCA1 test")

    def test_get_packet(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "external_evidence_packets.jsonl"

            packet = {
                "record_type": "external_evidence_packet_v1",
                "packet_id": "pm_test_001",
                "source": "pubmed",
                "query": "test query",
                "retrieved_at": "2026-05-03T10:00:00Z",
                "result_count": 1,
                "results": [],
                "authority": "external_evidence_unverified",
                "automatic_change": False,
                "hidden_learning": False,
                "raw_prompt_stored": False,
            }

            append_evidence_packet(packet, doc_store_path=store)
            found = get_packet("pm_test_001", doc_store_path=store)
            self.assertIsNotNone(found)
            self.assertEqual(found["packet_id"], "pm_test_001")

            not_found = get_packet("nonexistent", doc_store_path=store)
            self.assertIsNone(not_found)


if __name__ == "__main__":
    unittest.main()
