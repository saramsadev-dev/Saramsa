"""
Local ML Processing Service

Orchestrates the local ML pipeline:
  1. Bi-encoder aspect classification (all-MiniLM-L6-v2 cosine similarity)
  2. Aspect-relative sentiment (sentence-level sentiment per matched aspect)
  3. Aggregation + keyword extraction
  4. Lean GPT-5-mini synthesis (aggregates + evidence samples only)
"""

import logging
import time
import re
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from sklearn.metrics.pairwise import cosine_similarity

from aiCore.services.similarity_aspect_service import get_similarity_aspect_service
from aiCore.services.local_sentiment_service import LocalSentimentService, SentimentResult
from apis.prompts.synthesis_prompt import FALLBACK_RESPONSE_TEMPLATE
from .narration_service import get_narration_service

logger = logging.getLogger(__name__)

# Sentence splitting regex: split on . ! ? followed by space or end-of-string,
# but not on abbreviations like "Mr." or "e.g."
_SENTENCE_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$')

# Common English stopwords for keyword extraction
_STOPWORDS = frozenset({
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
    'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her',
    'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs',
    'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
    'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with',
    'about', 'against', 'between', 'through', 'during', 'before', 'after', 'above',
    'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
    'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
    'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's',
    't', 'can', 'will', 'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're',
    've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven',
    'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren',
    'won', 'wouldn', 'also', 'would', 'could', 'much', 'really', 'get', 'got',
    'even', 'still', 'well', 'back', 'like', 'one', 'two', 'go', 'going', 'went',
    'come', 'came', 'make', 'made', 'take', 'took', 'know', 'knew', 'think',
    'thought', 'want', 'said', 'say', 'way', 'thing', 'things', 'lot', 'every',
})

_WORD_RE = re.compile(r'[a-zA-Z]{3,}')


@dataclass
class AspectSentiment:
    """Sentiment result for a specific aspect within a comment."""
    aspect: str
    sentiment: str        # POSITIVE / NEGATIVE / NEUTRAL / MIXED
    confidence: str       # HIGH / MEDIUM / LOW
    source_sentence: str  # The sentence used for this aspect's sentiment
    raw_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class AspectMatch:
    comment_id: int
    comment_text: str
    matched_aspects: List[str]
    aspect_scores: Dict[str, float]
    comment_sentiment: SentimentResult          # Overall comment-level sentiment
    aspect_sentiments: Dict[str, AspectSentiment] = field(default_factory=dict)  # Per-aspect sentiment


@dataclass
class AggregatedStats:
    aspect_sentiment_counts: Dict[str, Dict[str, int]]
    confidence_distribution: Dict[str, int]
    unmapped_count: int
    unmapped_percentage: float
    total_comments: int
    aspect_keywords: Dict[str, List[str]]
    overall_sentiment: Dict[str, float]


@dataclass
class ProcessingResult:
    matches: List[AspectMatch]
    aggregated_stats: AggregatedStats
    processing_time: float
    model_info: Dict[str, str]
    insights: List[str]
    features: List[Dict[str, Any]]
    work_items: List[Dict[str, Any]]


class LocalProcessingService:
    """
    Orchestrates the local ML pipeline for feedback analysis.

    Pipeline:
      1. Bi-encoder aspect classification (all-MiniLM-L6-v2)
      2. Aspect-relative sentiment (sentence → aspect → sentiment)
      3. Aggregate statistics + extract keywords
      4. Lean GPT-5-mini synthesis (aggregates + evidence only)
    """

    UNMAPPED_WARNING_THRESHOLD = 0.12
    MAX_EVIDENCE_SAMPLES = 30
    SAMPLES_PER_ASPECT = 5

    def __init__(self):
        self.similarity_service = get_similarity_aspect_service()
        self.sentiment_service = LocalSentimentService()
        logger.info("LocalProcessingService initialized with bi-encoder similarity + aspect-relative sentiment")

    def process_comments(self, comments: List[str], aspects: List[str],
                         company_name: str = "Company", run_id: str = None) -> ProcessingResult:
        """Run the full pipeline and return a ProcessingResult."""
        start_time = time.time()

        if not comments:
            raise ValueError("Comments list cannot be empty")
        if not aspects:
            raise ValueError("Aspects list cannot be empty")

        if run_id is None:
            run_id = f"run_{int(time.time())}"

        logger.info(f"Processing {len(comments)} comments with {len(aspects)} aspects (run: {run_id})")

        # Step 1: Bi-encoder similarity aspect classification
        similarity_results = self.similarity_service.classify_aspects(comments, aspects, run_id)

        # Step 2: Aspect-relative sentiment
        # 2a. Get comment-level sentiment for overall counts
        comment_sentiments = self.sentiment_service.classify_batch(comments)

        # 2b. Compute aspect-relative sentiment (sentence-level)
        combined_matches = self._compute_aspect_relative_sentiment(
            similarity_results, comment_sentiments, aspects
        )

        # Step 3: aggregate + keywords (now uses per-aspect sentiment)
        aggregated_stats = self._aggregate_results(combined_matches, aspects)

        if aggregated_stats.unmapped_percentage > self.UNMAPPED_WARNING_THRESHOLD:
            logger.warning(
                f"High unmapped rate: {aggregated_stats.unmapped_percentage:.1%} "
                f"({aggregated_stats.unmapped_count}/{aggregated_stats.total_comments}). "
                "Consider updating the aspect taxonomy."
            )

        # Step 4: Unified narration (single GPT entrypoint)
        insights, features, work_items = self._narrate_with_service(
            combined_matches, aggregated_stats, aspects, company_name
        )

        processing_time = time.time() - start_time
        logger.info(f"Pipeline completed in {processing_time:.2f}s")

        return ProcessingResult(
            matches=combined_matches,
            aggregated_stats=aggregated_stats,
            processing_time=processing_time,
            model_info={
                "aspect_model": self.similarity_service.embedding_service.MODEL_NAME,
                "sentiment_model": self.sentiment_service.MODEL_NAME,
                "processing_method": "local_ml_pipeline_aspect_sentiment",
            },
            insights=insights,
            features=features,
            work_items=work_items,
        )

    # ------------------------------------------------------------------
    # Aspect-relative sentiment
    # ------------------------------------------------------------------

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences. Returns [text] if only one sentence."""
        sentences = _SENTENCE_RE.split(text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        return sentences if sentences else [text]

    def _compute_aspect_relative_sentiment(
        self,
        similarity_results: List[Dict[str, Any]],
        comment_sentiments: List[SentimentResult],
        aspects: List[str],
    ) -> List[AspectMatch]:
        """
        For each comment, find the best-matching sentence per assigned aspect
        and run sentiment on that sentence instead of the whole comment.

        For single-sentence comments, uses the comment-level sentiment directly.
        """
        embedding_service = self.similarity_service.embedding_service

        # Pre-compute aspect embeddings once
        aspect_embeddings = embedding_service.get_embeddings(aspects)
        aspect_to_idx = {a: i for i, a in enumerate(aspects)}

        # Collect all sentences that need sentiment (deduplicated)
        sentence_set: Dict[str, None] = {}  # ordered set via dict
        comment_sentence_map: List[Tuple[List[str], bool]] = []  # (sentences, is_multi)

        for sim_result in similarity_results:
            sentences = self._split_sentences(sim_result["comment_text"])
            is_multi = len(sentences) > 1
            comment_sentence_map.append((sentences, is_multi))
            if is_multi:
                for s in sentences:
                    sentence_set[s] = None

        # Batch-embed and batch-sentiment all unique sentences
        unique_sentences = list(sentence_set.keys())
        sentence_sentiment_map: Dict[str, SentimentResult] = {}
        sentence_embedding_map: Dict[str, np.ndarray] = {}

        if unique_sentences:
            logger.info(f"Aspect-relative sentiment: {len(unique_sentences)} unique sentences from multi-sentence comments")
            sent_embeddings = embedding_service.get_embeddings(unique_sentences)
            sent_sentiments = self.sentiment_service.classify_batch(unique_sentences)
            for i, s in enumerate(unique_sentences):
                sentence_sentiment_map[s] = sent_sentiments[i]
                sentence_embedding_map[s] = sent_embeddings[i]

        # Build AspectMatch objects with per-aspect sentiment
        combined_matches = []
        for idx, (sim_result, comment_sentiment) in enumerate(zip(similarity_results, comment_sentiments)):
            sentences, is_multi = comment_sentence_map[idx]
            matched_aspects = sim_result["matched_aspects"]

            aspect_sentiments: Dict[str, AspectSentiment] = {}

            if not is_multi or not matched_aspects:
                # Single sentence or unmapped: use comment-level sentiment for all aspects
                for aspect in matched_aspects:
                    aspect_sentiments[aspect] = AspectSentiment(
                        aspect=aspect,
                        sentiment=comment_sentiment.sentiment,
                        confidence=comment_sentiment.confidence,
                        source_sentence=sim_result["comment_text"],
                        raw_scores=comment_sentiment.raw_scores,
                    )
            else:
                # Multi-sentence: find best sentence per aspect
                sent_embs = np.array([sentence_embedding_map[s] for s in sentences])

                for aspect in matched_aspects:
                    a_idx = aspect_to_idx.get(aspect)
                    if a_idx is None:
                        # Aspect not in original list (shouldn't happen)
                        aspect_sentiments[aspect] = AspectSentiment(
                            aspect=aspect,
                            sentiment=comment_sentiment.sentiment,
                            confidence=comment_sentiment.confidence,
                            source_sentence=sim_result["comment_text"],
                            raw_scores=comment_sentiment.raw_scores,
                        )
                        continue

                    # Cosine similarity between each sentence and this aspect
                    aspect_emb = aspect_embeddings[a_idx].reshape(1, -1)
                    sims = cosine_similarity(sent_embs, aspect_emb).flatten()
                    best_sent_idx = int(np.argmax(sims))
                    best_sentence = sentences[best_sent_idx]

                    sent_sentiment = sentence_sentiment_map[best_sentence]
                    aspect_sentiments[aspect] = AspectSentiment(
                        aspect=aspect,
                        sentiment=sent_sentiment.sentiment,
                        confidence=sent_sentiment.confidence,
                        source_sentence=best_sentence,
                        raw_scores=sent_sentiment.raw_scores,
                    )

            combined_matches.append(AspectMatch(
                comment_id=sim_result["comment_id"],
                comment_text=sim_result["comment_text"],
                matched_aspects=matched_aspects,
                aspect_scores=sim_result["aspect_scores"],
                comment_sentiment=comment_sentiment,
                aspect_sentiments=aspect_sentiments,
            ))

        multi_count = sum(1 for _, is_multi in comment_sentence_map if is_multi)
        logger.info(
            f"Aspect-relative sentiment complete: {multi_count}/{len(similarity_results)} "
            f"multi-sentence comments processed"
        )

        return combined_matches

    # ------------------------------------------------------------------
    # Aggregation + keyword extraction
    # ------------------------------------------------------------------

    def _aggregate_results(self, matches: List[AspectMatch], aspects: List[str]) -> AggregatedStats:
        aspect_sentiment_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        confidence_dist: Dict[str, int] = defaultdict(int)
        overall_counts: Dict[str, int] = defaultdict(int)
        unmapped_count = 0
        total = len(matches)

        # Collect comment texts per aspect for keyword extraction
        aspect_comments: Dict[str, List[str]] = defaultdict(list)

        for m in matches:
            # Overall sentiment uses comment-level (1 per comment, no inflation)
            overall_counts[m.comment_sentiment.sentiment] += 1
            confidence_dist[m.comment_sentiment.confidence] += 1

            if not m.matched_aspects:
                unmapped_count += 1
                continue

            for aspect in m.matched_aspects:
                if aspect == "UNMAPPED":
                    unmapped_count += 1
                else:
                    # Use aspect-relative sentiment for per-aspect counts
                    asp_sent = m.aspect_sentiments.get(aspect)
                    if asp_sent:
                        aspect_sentiment_counts[aspect][asp_sent.sentiment] += 1
                    else:
                        # Fallback to comment-level
                        aspect_sentiment_counts[aspect][m.comment_sentiment.sentiment] += 1
                    aspect_comments[aspect].append(m.comment_text)

        overall_sentiment = {s.lower(): (c / total) * 100 for s, c in overall_counts.items()} if total else {}

        # Extract real keywords per aspect
        aspect_keywords = {}
        for aspect in aspects:
            texts = aspect_comments.get(aspect, [])
            aspect_keywords[aspect] = self._extract_keywords(texts, top_n=10)

        return AggregatedStats(
            aspect_sentiment_counts=dict(aspect_sentiment_counts),
            confidence_distribution=dict(confidence_dist),
            unmapped_count=unmapped_count,
            unmapped_percentage=unmapped_count / total if total else 0,
            total_comments=total,
            aspect_keywords=aspect_keywords,
            overall_sentiment=overall_sentiment,
        )

    @staticmethod
    def _extract_keywords(texts: List[str], top_n: int = 10) -> List[str]:
        """Extract top keywords from a list of texts using word frequency."""
        counter: Counter = Counter()
        for text in texts:
            words = _WORD_RE.findall(text.lower())
            counter.update(w for w in words if w not in _STOPWORDS)
        return [word for word, _ in counter.most_common(top_n)]

    # ------------------------------------------------------------------
    # Unified narration (single GPT entrypoint)
    # ------------------------------------------------------------------

    def _narrate_with_service(self, matches, aggregated_stats, aspects, company_name):
        """Call unified NarrationService with lean payload."""
        narration_service = get_narration_service()

        features = []
        aspect_key_map = {self._normalize_aspect_key(a): a for a in aspects if a}
        for aspect, sentiment_counts in aggregated_stats.aspect_sentiment_counts.items():
            if aspect == "UNMAPPED":
                continue
            total = sum(sentiment_counts.values())
            if total == 0:
                continue
            features.append({
                "aspect_key": self._normalize_aspect_key(aspect),
                "metrics": {
                    "comment_count": total,
                    "neg_pct": (sentiment_counts.get("NEGATIVE", 0) / total),
                    "mixed_pct": (sentiment_counts.get("MIXED", 0) / total),
                },
                "keywords": aggregated_stats.aspect_keywords.get(aspect, [])[:5],
            })

        narration_input = {
            "project_id": None,
            "analysis_id": None,
            "taxonomy_id": None,
            "taxonomy_version": None,
            "overall": aggregated_stats.overall_sentiment,
            "features": features,
            "evidence": self._build_evidence(matches),
            "work_item_candidates": [],
        }

        narratives = narration_service.generate_narratives(narration_input)

        narrative_map = {f.get("aspect_key"): f.get("description") for f in narratives.get("features", [])}
        sentiment_counts_map = aggregated_stats.aspect_sentiment_counts
        features_out = []
        for feature in features:
            aspect_key = feature.get("aspect_key")
            total_comments = feature["metrics"]["comment_count"]
            aspect_name = aspect_key_map.get(aspect_key, aspect_key)
            aspect_label = aspect_name.replace("_", " ").title() if aspect_name else "General"
            raw_counts = sentiment_counts_map.get(aspect_name, {})
            total = sum(raw_counts.values()) or 1
            pos_pct = (raw_counts.get("POSITIVE", 0) / total) * 100
            neg_pct = (raw_counts.get("NEGATIVE", 0) / total) * 100
            neu_pct = (raw_counts.get("NEUTRAL", 0) / total) * 100
            features_out.append({
                "feature": aspect_label,
                "description": narrative_map.get(aspect_key, f"Customer feedback about {aspect_key}."),
                "sentiment": {
                    "positive": pos_pct,
                    "negative": neg_pct,
                    "neutral": neu_pct,
                },
                "keywords": feature.get("keywords", []),
                "comment_count": total_comments,
            })

        return narratives.get("insights", []), features_out, narratives.get("work_items", [])

    def _build_fallback(self, aggregated_stats, aspects):
        """Produce fallback insights/features/work_items when GPT call fails."""
        insights = list(FALLBACK_RESPONSE_TEMPLATE["insights"])
        work_items = list(FALLBACK_RESPONSE_TEMPLATE["work_items"])

        features = []
        for aspect, sentiment_counts in aggregated_stats.aspect_sentiment_counts.items():
            if aspect == "UNMAPPED":
                continue
            total = sum(sentiment_counts.values())
            if total == 0:
                continue
            features.append({
                "feature": aspect,
                "description": f"Customer feedback about {aspect}.",
                "sentiment": {k.lower(): (v / total) * 100 for k, v in sentiment_counts.items()},
                "keywords": aggregated_stats.aspect_keywords.get(aspect, [])[:5],
                "comment_count": total,
            })

        return insights, features, work_items

    # ------------------------------------------------------------------
    # Evidence sampling (per-aspect, capped)
    # ------------------------------------------------------------------

    def _select_aspect_evidence_samples(self, matches: List[AspectMatch], aspects: List[str]) -> List[str]:
        """
        Select 3-5 representative comments PER ASPECT, capped at MAX_EVIDENCE_SAMPLES total.

        Prioritizes comments with clear sentiment signal (HIGH confidence first).
        """
        aspect_buckets: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)
        # (comment_text, sentiment, confidence)

        for m in matches:
            for aspect in m.matched_aspects:
                if aspect == "UNMAPPED":
                    continue
                asp_sent = m.aspect_sentiments.get(aspect)
                if asp_sent:
                    aspect_buckets[aspect].append(
                        (asp_sent.source_sentence, asp_sent.sentiment, asp_sent.confidence)
                    )
                else:
                    aspect_buckets[aspect].append(
                        (m.comment_text, m.comment_sentiment.sentiment, m.comment_sentiment.confidence)
                    )

        samples: List[str] = []
        budget = self.MAX_EVIDENCE_SAMPLES
        per_aspect = self.SAMPLES_PER_ASPECT

        for aspect in aspects:
            if budget <= 0:
                break
            bucket = aspect_buckets.get(aspect, [])
            if not bucket:
                continue

            # Sort: HIGH confidence first, then diversify by sentiment
            confidence_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            bucket.sort(key=lambda x: confidence_order.get(x[2], 3))

            # Take up to per_aspect, ensuring sentiment diversity
            seen_sentiments = set()
            selected = []
            for text, sentiment, confidence in bucket:
                if len(selected) >= per_aspect:
                    break
                # Prioritize unseen sentiments
                if sentiment not in seen_sentiments:
                    selected.append(f"[{aspect} | {sentiment}] {text[:200]}")
                    seen_sentiments.add(sentiment)
                elif len(selected) < per_aspect:
                    selected.append(f"[{aspect} | {sentiment}] {text[:200]}")

            take = min(len(selected), budget)
            samples.extend(selected[:take])
            budget -= take

        logger.info(f"Evidence samples: {len(samples)} total across {len(aspect_buckets)} aspects")
        return samples

    def _build_evidence(self, matches: List[AspectMatch]) -> List[Dict[str, Any]]:
        """Build evidence list with confidence for narration trimming."""
        evidence = []
        for m in matches:
            for aspect in m.matched_aspects:
                if aspect == "UNMAPPED":
                    continue
                asp_sent = m.aspect_sentiments.get(aspect)
                if asp_sent:
                    confidence = self._confidence_to_score(asp_sent.confidence)
                    text = asp_sent.source_sentence
                    sentiment = asp_sent.sentiment
                else:
                    confidence = self._confidence_to_score(m.comment_sentiment.confidence)
                    text = m.comment_text
                    sentiment = m.comment_sentiment.sentiment
                evidence.append({
                    "aspect_key": self._normalize_aspect_key(aspect),
                    "sentiment": sentiment,
                    "text": text,
                    "confidence": confidence,
                })
        return evidence

    @staticmethod
    def _normalize_aspect_key(label: str) -> str:
        return str(label).strip().lower().replace(" ", "_")

    @staticmethod
    def _confidence_to_score(confidence: str) -> float:
        conf = str(confidence or "").upper()
        return {"HIGH": 0.9, "MEDIUM": 0.6, "LOW": 0.3}.get(conf, 0.0)


# ------------------------------------------------------------------
# Singleton accessor
# ------------------------------------------------------------------
_local_processing_service = None


def get_local_processing_service() -> LocalProcessingService:
    global _local_processing_service
    if _local_processing_service is None:
        _local_processing_service = LocalProcessingService()
    return _local_processing_service
