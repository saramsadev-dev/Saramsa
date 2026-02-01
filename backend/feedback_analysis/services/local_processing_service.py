"""
Local ML Processing Service

Orchestrates the local ML pipeline: embedding → aspect matching → sentiment → aggregation → GPT synthesis.
Uses all-MiniLM-L6-v2 for embeddings, cardiffnlp/twitter-roberta-base for sentiment,
and a single GPT-5-mini call for insights/work items.
"""

import logging
import numpy as np
import time
import json
import re
from typing import List, Dict, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
from asgiref.sync import async_to_sync

from aiCore.services.embedding_service import EmbeddingService
from aiCore.services.local_sentiment_service import LocalSentimentService, SentimentResult
from aiCore.services.completion_service import generate_completions
from apis.prompts.synthesis_prompt import create_synthesis_prompt, FALLBACK_RESPONSE_TEMPLATE

logger = logging.getLogger(__name__)

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
class AspectMatch:
    comment_id: int
    comment_text: str
    matched_aspects: List[str]
    similarity_scores: Dict[str, float]
    sentiment_result: SentimentResult


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
      1. Embed comments (all-MiniLM-L6-v2)
      2. Embed aspects (cached per run)
      3. Cosine similarity → map comments to aspects
      4. Sentiment classification (twitter-roberta-base)
      5. Aggregate statistics + extract keywords
      6. Single GPT-5-mini call for insights + work items
    """

    SIMILARITY_THRESHOLD = 0.45
    UNMAPPED_WARNING_THRESHOLD = 0.20
    REPRESENTATIVE_SAMPLE_SIZE = 50

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.sentiment_service = LocalSentimentService()
        logger.info("LocalProcessingService initialized")

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

        # Steps 1-2: embed
        comment_embeddings = self.embedding_service.get_embeddings(comments)
        aspect_embeddings = self.embedding_service.cache_aspect_embeddings(aspects, run_id)

        # Step 3: aspect matching
        raw_matches = self._match_aspects(comments, comment_embeddings, aspects, aspect_embeddings)

        # Step 4: sentiment
        sentiment_results = self.sentiment_service.classify_batch(comments)

        combined_matches = []
        for match, sentiment in zip(raw_matches, sentiment_results):
            combined_matches.append(AspectMatch(
                comment_id=match["comment_id"],
                comment_text=match["comment_text"],
                matched_aspects=match["matched_aspects"],
                similarity_scores=match["similarity_scores"],
                sentiment_result=sentiment,
            ))

        # Step 5: aggregate + keywords
        aggregated_stats = self._aggregate_results(combined_matches, aspects)

        if aggregated_stats.unmapped_percentage > self.UNMAPPED_WARNING_THRESHOLD:
            logger.warning(
                f"High unmapped rate: {aggregated_stats.unmapped_percentage:.1%} "
                f"({aggregated_stats.unmapped_count}/{aggregated_stats.total_comments}). "
                "Consider updating the aspect taxonomy."
            )

        # Step 6: GPT synthesis
        insights, features, work_items = self._synthesize_with_gpt(
            combined_matches, aggregated_stats, aspects, comments, company_name
        )

        processing_time = time.time() - start_time
        logger.info(f"Pipeline completed in {processing_time:.2f}s")

        return ProcessingResult(
            matches=combined_matches,
            aggregated_stats=aggregated_stats,
            processing_time=processing_time,
            model_info={
                "embedding_model": self.embedding_service.MODEL_NAME,
                "sentiment_model": self.sentiment_service.MODEL_NAME,
                "processing_method": "local_ml_pipeline",
            },
            insights=insights,
            features=features,
            work_items=work_items,
        )

    # ------------------------------------------------------------------
    # Aspect matching
    # ------------------------------------------------------------------

    def _match_aspects(self, comments, comment_embeddings, aspects, aspect_embeddings):
        aspect_matrix = np.array([aspect_embeddings[a] for a in aspects])
        matches = []

        for i, (comment, emb) in enumerate(zip(comments, comment_embeddings)):
            similarities = np.dot(emb, aspect_matrix.T)
            matched = []
            scores = {}
            for j, (aspect, sim) in enumerate(zip(aspects, similarities)):
                scores[aspect] = float(sim)
                if sim >= self.SIMILARITY_THRESHOLD:
                    matched.append(aspect)
            if not matched:
                matched = ["UNMAPPED"]
            matches.append({
                "comment_id": i,
                "comment_text": comment,
                "matched_aspects": matched,
                "similarity_scores": scores,
            })
        return matches

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
            sentiment = m.sentiment_result.sentiment
            confidence = m.sentiment_result.confidence
            overall_counts[sentiment] += 1
            confidence_dist[confidence] += 1

            for aspect in m.matched_aspects:
                if aspect == "UNMAPPED":
                    unmapped_count += 1
                else:
                    aspect_sentiment_counts[aspect][sentiment] += 1
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
    # GPT synthesis
    # ------------------------------------------------------------------

    def _synthesize_with_gpt(self, matches, aggregated_stats, aspects, comments, company_name):
        """Call GPT-5-mini once for insights, feature descriptions, and work items."""

        # Build structured extractions payload
        per_comment = []
        for m in matches:
            per_comment.append({
                "comment_id": m.comment_id,
                "aspects": m.matched_aspects,
                "sentiment": m.sentiment_result.sentiment,
                "confidence": m.sentiment_result.confidence,
            })

        structured_extractions = {"per_comment_extractions": per_comment}

        agg_dict = {
            "overall_sentiment": aggregated_stats.overall_sentiment,
            "confidence_distribution": aggregated_stats.confidence_distribution,
            "unmapped_count": aggregated_stats.unmapped_count,
            "unmapped_percentage": aggregated_stats.unmapped_percentage,
            "aspect_sentiment_counts": aggregated_stats.aspect_sentiment_counts,
            "aspect_keywords": aggregated_stats.aspect_keywords,
        }

        samples = self._select_representative_samples(matches, comments)

        prompt = create_synthesis_prompt(
            structured_extractions=structured_extractions,
            aggregated_stats=agg_dict,
            representative_samples=samples,
            company_name=company_name,
        )

        try:
            logger.info("Calling GPT-5-mini for synthesis...")
            raw_result = async_to_sync(generate_completions)(prompt, max_tokens=4000)
            parsed = json.loads(raw_result) if isinstance(raw_result, str) else raw_result

            insights = parsed.get("insights", [])
            features = parsed.get("features", [])
            work_items = parsed.get("work_items", [])
            logger.info(f"GPT synthesis returned {len(insights)} insights, {len(features)} features, {len(work_items)} work items")
            return insights, features, work_items

        except Exception as e:
            logger.error(f"GPT synthesis failed, using fallback: {e}")
            return self._build_fallback(aggregated_stats, aspects)

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
    # Sampling
    # ------------------------------------------------------------------

    def _select_representative_samples(self, matches, comments) -> List[str]:
        """Stratified sample across sentiments, up to REPRESENTATIVE_SAMPLE_SIZE."""
        buckets: Dict[str, List[str]] = defaultdict(list)
        for m in matches:
            buckets[m.sentiment_result.sentiment].append(m.comment_text)

        n = self.REPRESENTATIVE_SAMPLE_SIZE
        total = sum(len(v) for v in buckets.values())
        if total <= n:
            return [m.comment_text for m in matches]

        samples: List[str] = []
        for sentiment, texts in buckets.items():
            share = max(1, int(n * len(texts) / total))
            samples.extend(texts[:share])

        return samples[:n]


# ------------------------------------------------------------------
# Singleton accessor
# ------------------------------------------------------------------
_local_processing_service = None


def get_local_processing_service() -> LocalProcessingService:
    global _local_processing_service
    if _local_processing_service is None:
        _local_processing_service = LocalProcessingService()
    return _local_processing_service
