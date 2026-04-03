"""
Tests for TF-IDF keyword extraction in LocalProcessingService.

Validates that keywords are meaningful, distinctive per aspect, and that
bigrams surface useful phrases. Also compares against the old frequency-based
approach to demonstrate quality improvement.
"""

import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saramsa.settings")
django.setup()

import pytest
from collections import Counter
from feedback_analysis.services.local_processing_service import (
    LocalProcessingService,
    _STOPWORDS,
    _WORD_RE,
)


# ---------------------------------------------------------------------------
# Realistic multi-aspect feedback corpus
# ---------------------------------------------------------------------------

SAMPLE_COMMENTS = {
    "pricing": [
        "The pricing is way too expensive compared to competitors.",
        "I love the product but the cost is prohibitive for small teams.",
        "Subscription fees keep increasing every year, very frustrating.",
        "The free tier is too limited, you're forced to upgrade immediately.",
        "Pricing tiers are confusing, hard to tell which plan fits us.",
        "We switched from a competitor because their pricing was transparent.",
        "Monthly billing doesn't work for our budget cycle, need annual options.",
        "The enterprise plan is overpriced for what you get.",
        "Hidden fees in the billing made us reconsider.",
        "Would love a startup discount or flexible pricing.",
        "The per-seat pricing model punishes growing teams unfairly.",
        "Compared to alternatives, the value for money is questionable.",
    ],
    "user_interface": [
        "The dashboard is cluttered and hard to navigate.",
        "UI feels outdated compared to modern tools we use.",
        "Love the clean layout but the color contrast is poor.",
        "Navigation is confusing, took me weeks to find basic settings.",
        "The mobile interface is practically unusable on smaller screens.",
        "Dark mode would be a huge improvement for accessibility.",
        "Too many clicks to reach frequently used features.",
        "The drag and drop functionality is buggy and unresponsive.",
        "Responsive design breaks on tablet, elements overlap badly.",
        "The interface is intuitive for new users, onboarding was smooth.",
        "Font sizes are too small, especially on the analytics page.",
        "The sidebar takes up too much space on narrow monitors.",
    ],
    "performance": [
        "Page load times are unacceptably slow during peak hours.",
        "The app crashes frequently when processing large datasets.",
        "Search is painfully slow, takes 10+ seconds for basic queries.",
        "Upload speeds have degraded significantly since the last update.",
        "The API response time is inconsistent, sometimes timing out.",
        "Memory usage spikes when opening multiple reports simultaneously.",
        "Exporting large CSV files freezes the entire application.",
        "Real-time sync is laggy, changes take minutes to propagate.",
        "The mobile app drains battery extremely fast.",
        "Performance has improved noticeably after the recent optimization.",
        "Background tasks keep running even after logout, wasting resources.",
        "Latency on the analytics dashboard makes it unusable for live monitoring.",
    ],
    "customer_support": [
        "Support response time is terrible, waited 3 days for a reply.",
        "The chatbot is useless, just keeps redirecting to FAQ articles.",
        "Finally got a knowledgeable agent who resolved my issue quickly.",
        "No phone support option is a dealbreaker for enterprise customers.",
        "Documentation is outdated, half the screenshots don't match the current UI.",
        "The community forum is more helpful than official support.",
        "Live chat disconnects randomly mid-conversation, very annoying.",
        "Support team doesn't understand technical issues at all.",
        "Ticket escalation process is opaque, no visibility into progress.",
        "Self-service portal needs better search and troubleshooting guides.",
        "Support hours are limited to US timezone, unusable for our APAC team.",
        "The knowledge base articles are well-written but incomplete.",
    ],
}


# ---------------------------------------------------------------------------
# Old frequency-based extraction (baseline for comparison)
# ---------------------------------------------------------------------------

def _old_extract_keywords(texts, top_n=10):
    """Original Counter-based extraction for comparison."""
    counter = Counter()
    for text in texts:
        words = _WORD_RE.findall(text.lower())
        counter.update(w for w in words if w not in _STOPWORDS)
    return [word for word, _ in counter.most_common(top_n)]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTfidfKeywordExtraction:

    def test_returns_keywords_for_all_aspects(self):
        """Every aspect with comments should get keywords."""
        aspects = list(SAMPLE_COMMENTS.keys())
        result = LocalProcessingService._extract_keywords_tfidf(
            SAMPLE_COMMENTS, aspects, top_n=10
        )
        for aspect in aspects:
            assert aspect in result, f"Missing keywords for {aspect}"
            assert len(result[aspect]) > 0, f"Empty keywords for {aspect}"

    def test_empty_aspect_returns_empty(self):
        """Aspects with no comments should get an empty list."""
        aspects = ["pricing", "nonexistent_feature"]
        result = LocalProcessingService._extract_keywords_tfidf(
            {"pricing": SAMPLE_COMMENTS["pricing"]}, aspects, top_n=5
        )
        assert len(result["pricing"]) > 0
        assert result["nonexistent_feature"] == []

    def test_keywords_are_distinctive_per_aspect(self):
        """Keywords for different aspects should have minimal overlap."""
        aspects = list(SAMPLE_COMMENTS.keys())
        result = LocalProcessingService._extract_keywords_tfidf(
            SAMPLE_COMMENTS, aspects, top_n=5
        )
        # Check pairwise overlap — top-5 keywords should mostly differ
        for i, a1 in enumerate(aspects):
            for a2 in aspects[i + 1:]:
                overlap = set(result[a1]) & set(result[a2])
                assert len(overlap) <= 2, (
                    f"Too much overlap between {a1} and {a2}: {overlap}"
                )

    def test_aspect_name_tokens_excluded(self):
        """Keywords should not include the aspect name itself."""
        aspects = list(SAMPLE_COMMENTS.keys())
        result = LocalProcessingService._extract_keywords_tfidf(
            SAMPLE_COMMENTS, aspects, top_n=10
        )
        for aspect in aspects:
            aspect_tokens = set(aspect.lower().replace("_", " ").split())
            for kw in result[aspect]:
                kw_tokens = set(kw.split())
                assert not kw_tokens <= aspect_tokens, (
                    f"Keyword '{kw}' for aspect '{aspect}' is just the aspect name"
                )

    def test_bigrams_can_appear(self):
        """At least some aspects should have bigram keywords (two-word phrases)."""
        aspects = list(SAMPLE_COMMENTS.keys())
        result = LocalProcessingService._extract_keywords_tfidf(
            SAMPLE_COMMENTS, aspects, top_n=10
        )
        all_keywords = []
        for kws in result.values():
            all_keywords.extend(kws)
        bigrams = [kw for kw in all_keywords if " " in kw]
        assert len(bigrams) > 0, (
            f"No bigrams found in any aspect. Keywords: {result}"
        )

    def test_quality_improvement_over_frequency(self):
        """TF-IDF keywords should be more distinctive than frequency-based ones.

        Checks that the OLD method produces more cross-aspect duplicates
        (generic words) than the new TF-IDF method.
        """
        aspects = list(SAMPLE_COMMENTS.keys())

        # Old method
        old_results = {}
        for aspect in aspects:
            old_results[aspect] = _old_extract_keywords(SAMPLE_COMMENTS[aspect], top_n=10)

        # New method
        new_results = LocalProcessingService._extract_keywords_tfidf(
            SAMPLE_COMMENTS, aspects, top_n=10
        )

        # Count how many keywords appear in 3+ aspects (generic/noisy)
        def count_generic(results):
            all_kws = []
            for kws in results.values():
                all_kws.extend(kws)
            counts = Counter(all_kws)
            return sum(1 for _, c in counts.items() if c >= 3)

        old_generic = count_generic(old_results)
        new_generic = count_generic(new_results)
        assert new_generic <= old_generic, (
            f"TF-IDF should produce fewer generic keywords. "
            f"Old generic: {old_generic}, New generic: {new_generic}"
        )

    def test_single_aspect_does_not_crash(self):
        """Should handle a single aspect (edge case for TF-IDF)."""
        result = LocalProcessingService._extract_keywords_tfidf(
            {"pricing": SAMPLE_COMMENTS["pricing"]},
            ["pricing"],
            top_n=5,
        )
        assert len(result["pricing"]) > 0

    def test_very_short_texts(self):
        """Should handle very short / few-word comments gracefully."""
        short_comments = {
            "bugs": ["crashes", "broken", "error", "fails", "down"],
        }
        result = LocalProcessingService._extract_keywords_tfidf(
            short_comments, ["bugs"], top_n=5
        )
        assert isinstance(result["bugs"], list)

    def test_empty_corpus(self):
        """Should return empty keywords for all aspects if no comments."""
        result = LocalProcessingService._extract_keywords_tfidf(
            {}, ["pricing", "ui"], top_n=5
        )
        assert result == {"pricing": [], "ui": []}

    def test_stopwords_not_in_output(self):
        """No stopword should appear as a standalone keyword."""
        aspects = list(SAMPLE_COMMENTS.keys())
        result = LocalProcessingService._extract_keywords_tfidf(
            SAMPLE_COMMENTS, aspects, top_n=10
        )
        for aspect, keywords in result.items():
            for kw in keywords:
                # For unigrams, check directly. For bigrams, both words should not be stopwords.
                tokens = kw.split()
                if len(tokens) == 1:
                    assert kw not in _STOPWORDS, (
                        f"Stopword '{kw}' found in {aspect} keywords"
                    )


class TestKeywordQualityReport:
    """Not a pass/fail test — prints a comparison report for manual review."""

    def test_print_comparison(self, capsys):
        """Print old vs new keywords side by side for inspection."""
        aspects = list(SAMPLE_COMMENTS.keys())

        old_results = {}
        for aspect in aspects:
            old_results[aspect] = _old_extract_keywords(SAMPLE_COMMENTS[aspect], top_n=10)

        new_results = LocalProcessingService._extract_keywords_tfidf(
            SAMPLE_COMMENTS, aspects, top_n=10
        )

        print("\n" + "=" * 70)
        print("KEYWORD QUALITY COMPARISON: Frequency vs TF-IDF")
        print("=" * 70)
        for aspect in aspects:
            print(f"\n--- {aspect.upper()} ---")
            print(f"  OLD (frequency): {old_results[aspect]}")
            print(f"  NEW (TF-IDF):    {new_results[aspect]}")
        print("\n" + "=" * 70)
