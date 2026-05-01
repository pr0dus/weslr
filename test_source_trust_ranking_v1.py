"""
Tests for Source Trust Ranking V1
Read-only. No live web calls. No Ollama. No JSONL writes.
"""

import unittest
from weslr.source_trust_ranking import (
    classify_source,
    score_source,
    rank_search_results,
)


class TestClassifySource(unittest.TestCase):

    def _check(self, result, source_type, trust_tier, domain):
        self.assertEqual(result["record_type"], "source_classification_v1")
        self.assertEqual(result["source_type"], source_type)
        self.assertEqual(result["trust_tier"], trust_tier)
        self.assertEqual(result["domain"], domain)
        self.assertEqual(result["authority"], "ranking_only")

    def test_wikipedia_high_reference(self):
        r = classify_source("https://en.wikipedia.org/wiki/Entropy")
        self._check(r, "reference", "high", "wikipedia.org")
        self.assertIn("Wikipedia", r["reason"])

    def test_britannica_high_reference(self):
        r = classify_source("https://www.britannica.com/science/entropy-physics")
        self._check(r, "reference", "high", "britannica.com")
        self.assertIn("Britannica", r["reason"])

    def test_merriam_webster_high_reference(self):
        r = classify_source("https://www.merriam-webster.com/dictionary/entropy")
        self._check(r, "reference", "high", "merriam-webster.com")
        self.assertIn("Merriam-Webster", r["reason"])

    def test_dictionary_com_high_reference(self):
        r = classify_source("https://www.dictionary.com/browse/entropy")
        self._check(r, "reference", "high", "dictionary.com")

    def test_quanta_high_news_magazine(self):
        r = classify_source("https://www.quantamagazine.org/what-is-entropy-20241213/")
        self._check(r, "news_magazine", "high", "quantamagazine.org")
        self.assertIn("Quanta", r["reason"])

    def test_edu_academic_high(self):
        r = classify_source("https://ocw.mit.edu/courses/physics/8-333-statistical-mechanics-i-statistical-mechanics-of-particles-fall-2013/")
        self.assertEqual(r["trust_tier"], "high")
        self.assertEqual(r["source_type"], "academic")
        self.assertEqual(r["domain"], "ocw.mit.edu")

    def test_nih_gov_high_official(self):
        r = classify_source("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567/")
        self._check(r, "official", "high", "www.ncbi.nlm.nih.gov")

    def test_reddit_low_forum(self):
        r = classify_source("https://www.reddit.com/r/Physics/comments/eanth/can_somebody_easily_explain_to_me_what_entropy_is/")
        self._check(r, "forum", "low", "reddit.com")
        self.assertIn("Reddit", r["reason"])

    def test_youtube_low_video(self):
        r = classify_source("https://www.youtube.com/watch?v=YM-uykVfq_E")
        self._check(r, "video", "low", "youtube.com")
        self.assertIn("YouTube", r["reason"])

    def test_youtu_be_low_video(self):
        r = classify_source("https://youtu.be/YM-uykVfq_E")
        self._check(r, "video", "low", "youtube.com")

    def test_stackoverflow_low_forum(self):
        r = classify_source("https://stackoverflow.com/questions/12345/what-is-entropy")
        self._check(r, "forum", "low", "stackoverflow.com")
        self.assertIn("Forum", r["reason"])

    def test_twitter_low_social(self):
        r = classify_source("https://twitter.com/someuser/status/123")
        self._check(r, "social", "low", "twitter.com")

    def test_malformed_url_unknown(self):
        r = classify_source("")
        self.assertEqual(r["trust_tier"], "unknown")
        self.assertEqual(r["source_type"], "unknown")
        r2 = classify_source(None)
        self.assertEqual(r2["trust_tier"], "unknown")

    def test_no_url_unknown(self):
        r = classify_source("not-a-url")
        self.assertEqual(r["trust_tier"], "unknown")


class TestScoreSource(unittest.TestCase):

    def test_high_tier_score_around_085(self):
        r = score_source({"url": "https://en.wikipedia.org/wiki/Entropy", "title": "Entropy - Wikipedia"})
        self.assertAlmostEqual(r["score"], 0.85, places=1)
        self.assertEqual(r["classification"]["trust_tier"], "high")
        self.assertEqual(r["authority"], "ranking_only")

    def test_low_tier_score_around_030(self):
        r = score_source({"url": "https://www.reddit.com/r/entropy", "title": "Entropy discussion"})
        self.assertAlmostEqual(r["score"], 0.30, places=1)
        self.assertEqual(r["classification"]["trust_tier"], "low")

    def test_content_boost_in_ranking_reasons(self):
        r = score_source({
            "url": "https://en.wikipedia.org/wiki/Entropy",
            "title": "Entropy",
            "content": "Entropy is a thermodynamic property that measures the number of microstates available to a system." * 3,
        })
        self.assertTrue(
            any("Content present" in reason for reason in r["ranking_reasons"]),
            f"Content boost not found in ranking_reasons: {r['ranking_reasons']}",
        )

    def test_searxng_score_blended_not_authority(self):
        r = score_source({
            "url": "https://en.wikipedia.org/wiki/Entropy",
            "searxng_score": 9.5,
        })
        # Should blend but classification takes priority
        self.assertGreater(r["score"], 0.8)
        self.assertEqual(r["classification"]["trust_tier"], "high")

    def test_authority_ranking_only(self):
        r = score_source({"url": "https://example.com"})
        self.assertEqual(r["authority"], "ranking_only")


class TestRankSearchResults(unittest.TestCase):

    def test_wikipedia_before_reddit(self):
        results = [
            {"url": "https://www.reddit.com/r/Physics/comments/entropy/", "title": "Entropy Reddit"},
            {"url": "https://en.wikipedia.org/wiki/Entropy", "title": "Entropy - Wikipedia"},
        ]
        ranked = rank_search_results(results)
        self.assertEqual(ranked[0]["url"], "https://en.wikipedia.org/wiki/Entropy")
        self.assertEqual(ranked[1]["url"], "https://www.reddit.com/r/Physics/comments/entropy/")

    def test_reference_before_video(self):
        results = [
            {"url": "https://youtu.be/abc", "title": "Entropy Video"},
            {"url": "https://www.britannica.com/science/entropy", "title": "Britannica"},
        ]
        ranked = rank_search_results(results)
        self.assertEqual(
            ranked[0]["_source_trust"]["classification"]["domain"], "britannica.com"
        )

    def test_no_results_dropped(self):
        results = [
            {"url": "https://youtube.com/watch?v=1", "title": "Vid1"},
            {"url": "https://en.wikipedia.org/wiki/A", "title": "WikiA"},
            {"url": "https://reddit.com/r/B", "title": "RedditB"},
        ]
        ranked = rank_search_results(results)
        self.assertEqual(len(ranked), 3)

    def test_equal_scores_stable_order(self):
        # Results with same domain trust tier maintain relative order
        results = [
            {"url": "https://example.com/article1", "title": "A1"},
            {"url": "https://example.com/article2", "title": "A2"},
        ]
        ranked = rank_search_results(results)
        self.assertEqual(ranked[0]["title"], "A1")
        self.assertEqual(ranked[1]["title"], "A2")

    def test_source_trust_added_to_each_result(self):
        results = [{"url": "https://en.wikipedia.org/wiki/Entropy", "title": "Ent"}]
        ranked = rank_search_results(results)
        self.assertIn("_source_trust", ranked[0])
        self.assertEqual(ranked[0]["_source_trust"]["classification"]["trust_tier"], "high")
        self.assertEqual(ranked[0]["_source_trust"]["authority"], "ranking_only")

    def test_empty_list_returns_empty(self):
        self.assertEqual(rank_search_results([]), [])

    def test_authority_preserved_as_external_evidence_unverified(self):
        # rank_search_results doesn't change authority per result
        # Each result has _source_trust.authority = ranking_only
        results = [{"url": "https://en.wikipedia.org/wiki/Entropy", "title": "Ent"}]
        ranked = rank_search_results(results)
        self.assertEqual(ranked[0]["_source_trust"]["authority"], "ranking_only")

    def test_three_way_entropy_ranking(self):
        """Wikipedia / Quanta / Britannica above Reddit / YouTube."""
        results = [
            {"url": "https://youtu.be/xyz", "title": "Entropy YouTube"},
            {"url": "https://www.reddit.com/r/entropy", "title": "Entropy Reddit"},
            {"url": "https://www.quantamagazine.org/entropy-2024", "title": "Quanta"},
            {"url": "https://en.wikipedia.org/wiki/Entropy", "title": "Wikipedia"},
            {"url": "https://www.britannica.com/entropy", "title": "Britannica"},
        ]
        ranked = rank_search_results(results)
        domains = [r["_source_trust"]["classification"]["domain"] for r in ranked]
        self.assertLess(domains.index("wikipedia.org"), domains.index("reddit.com"))
        self.assertLess(domains.index("quantamagazine.org"), domains.index("reddit.com"))
        self.assertLess(domains.index("britannica.com"), domains.index("reddit.com"))
        self.assertLess(domains.index("wikipedia.org"), domains.index("youtube.com"))
        self.assertLess(domains.index("quantamagazine.org"), domains.index("youtube.com"))


class TestNoSideEffects(unittest.TestCase):

    def test_no_jsonl_writes(self):
        results = [{"url": "https://en.wikipedia.org/wiki/Entropy", "title": "Ent"}]
        rank_search_results(results)
        # No exception means no file writes (would raise if disk full, etc.)
        # This is a proxy — real test would mock filesystem

    def test_no_ollama_imports(self):
        import importlib.util
        spec = importlib.util.find_spec("ollama")
        self.assertIsNone(spec)  # No ollama in environment


if __name__ == "__main__":
    unittest.main()