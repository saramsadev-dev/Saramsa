"""
Production-grade ML Processing Service

Implements the refactored pipeline with:
1. Frozen aspect taxonomies (no dynamic generation)
2. Bi-encoder similarity classification (O(n + m + dot_product))
3. Bounded GPT synthesis (≤15s)
4. Near-real-time performance targets

Pipeline:
  User uploads CSV → POST /analyze → Django view → Celery task
  [ASPECT TAXONOMY PASSED IN]
  1. Embed aspects (cached)
  2. Embed comments (batch)
  3. Cosine similarity → assign up to 2 aspects
  4. Extract sentence span per aspect
  5. Local sentiment classification
  6. Aggregate stats + keywords
  7. GPT-5-mini synthesis (optional, bounded)
  8. Save to Cosmos DB
  9. Return SUCCESS

Performance targets:
- 500-1,000 comments: ~25-30s total
- Linear scaling with comment count
- Deterministic results
- Production-grade error handling
"""

import logging
import time
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter

from aiCore.services.similarity_aspect_service import get_similarity_aspect_service
from aiCore.services.local_sentiment_service import LocalSentimentService, SentimentResult
from feedback_analysis.services.narration_service import get_narration_service
from feedback_analysis.services.aspect_taxonomy_service import get_aspect_taxonomy_service
from apis.prompts.synthesis_prompt import FALLBACK_RESPONSE_TEMPLATE
from feedback_analysis.services.ml.config import (
    REPRESENTATIVE_COMMENTS_SAMPLE_SIZE,
    TARGET_PROCESSING_TIME_SECONDS
)

logger = logging.getLogger(__name__)

# Optimized stopwords for keyword extraction
_STOPWORDS = frozenset({
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her',
    'it', 'its', 'they', 'them', 'their', 'this', 'that', 'these', 'those',
    'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
    'as', 'of', 'at', 'by', 'for', 'with', 'about', 'to', 'from', 'in', 'on',
    'can', 'will', 'would', 'could', 'should', 'much', 'really', 'very', 'just',
    'also', 'get', 'got', 'go', 'come', 'make', 'take', 'know', 'think', 'want',
    'said', 'say', 'like', 'one', 'two', 'way', 'thing', 'things', 'lot', 'every'
})

_WORD_RE = re.compile(r'[a-zA-Z]{3,}')


@dataclass
class ProductionProcessingResult:
    """Complete result of production ML pipeline processing."""
    matches: List[Dict[str, Any]]
    aggregated_stats: Dict[str, Any]
    processing_time: float
    model_info: Dict[str, str]
    insights: List[str]
    features: List[Dict[str, Any]]
    work_items: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]


class ProductionProcessingService:
    """
    Production-grade ML processing service with frozen taxonomies and bi-encoder similarity.
    
    Key improvements over previous implementation:
    - Accepts frozen aspect taxonomies (no dynamic generation)
    - Uses bi-encoder similarity (linear scaling)
    - Bounded GPT synthesis (≤15s)
    - Comprehensive error handling
    - Performance monitoring
    """
    
    def __init__(self):
        self.similarity_service = get_similarity_aspect_service()
        self.sentiment_service = LocalSentimentService()
        self.taxonomy_service = get_aspect_taxonomy_service()
        logger.info("ProductionProcessingService initialized with bi-encoder similarity and frozen taxonomies")
    
    def process_comments_with_taxonomy(
        self, 
        comments: List[str], 
        taxonomy_id: str,
        company_name: str = "Company", 
        run_id: Optional[str] = None
    ) -> ProductionProcessingResult:
        """
        Process comments using a frozen aspect taxonomy.
        
        Args:
            comments: List of comment strings
            taxonomy_id: ID of the aspect taxonomy to use
            company_name: Company name for synthesis context
            run_id: Optional run identifier for caching
            
        Returns:
            ProductionProcessingResult with all analysis results
            
        Raises:
            ValueError: If taxonomy not found or comments empty
        """
        # Validate inputs
        if not comments:
            raise ValueError("Comments list cannot be empty")
        
        taxonomy = self.taxonomy_service.get_taxonomy(taxonomy_id)
        if not taxonomy:
            raise ValueError(f"Taxonomy '{taxonomy_id}' not found")
        
        return self._process_with_aspects(
            comments=comments,
            aspects=taxonomy.aspects,
            company_name=company_name,
            run_id=run_id,
            taxonomy_info={
                "taxonomy_id": taxonomy_id,
                "domain": taxonomy.domain,
                "version": taxonomy.version
            }
        )
    
    def process_comments_with_aspects(
        self,
        comments: List[str],
        aspects: List[str],
        company_name: str = "Company",
        run_id: Optional[str] = None
    ) -> ProductionProcessingResult:
        """
        Process comments with provided aspects list.
        
        Args:
            comments: List of comment strings
            aspects: List of aspect names
            company_name: Company name for synthesis context
            run_id: Optional run identifier for caching
            
        Returns:
            ProductionProcessingResult with all analysis results
            
        Raises:
            ValueError: If aspects validation fails
        """
        # Validate aspects
        validation_result = self.taxonomy_service.validate_aspects_for_processing(aspects)
        if not validation_result["valid"]:
            raise ValueError(f"Invalid aspects: {validation_result['error']}")
        
        return self._process_with_aspects(
            comments=comments,
            aspects=aspects,
            company_name=company_name,
            run_id=run_id,
            taxonomy_info={"source": "user_provided"}
        )
    
    def _process_with_aspects(
        self,
        comments: List[str],
        aspects: List[str],
        company_name: str,
        run_id: Optional[str],
        taxonomy_info: Dict[str, Any]
    ) -> ProductionProcessingResult:
        """Internal processing method with performance monitoring and taxonomy quality tracking."""
        start_time = time.time()
        performance_metrics = {}
        
        if run_id is None:
            run_id = f"prod_run_{int(time.time())}"
        
        logger.info(
            f"Processing {len(comments)} comments with {len(aspects)} aspects "
            f"(run: {run_id}, target: {TARGET_PROCESSING_TIME_SECONDS}s)"
        )
        
        # Step 1: Bi-encoder similarity classification
        step_start = time.time()
        similarity_results = self.similarity_service.classify_aspects(comments, aspects, run_id)
        performance_metrics["aspect_classification_time"] = time.time() - step_start
        
        # Step 2: Sentiment classification
        step_start = time.time()
        sentiment_results = self.sentiment_service.classify_batch(comments)
        performance_metrics["sentiment_classification_time"] = time.time() - step_start
        
        # Step 3: Combine results
        step_start = time.time()
        combined_matches = self._combine_results(similarity_results, sentiment_results)
        performance_metrics["result_combination_time"] = time.time() - step_start
        
        # Step 4: Aggregate statistics and extract keywords
        step_start = time.time()
        aggregated_stats = self._aggregate_results(combined_matches, aspects)
        performance_metrics["aggregation_time"] = time.time() - step_start
        
        # Step 5: Update taxonomy quality metrics (Risk 1 fix)
        if "taxonomy_id" in taxonomy_info:
            self._update_taxonomy_quality_metrics(
                taxonomy_info["taxonomy_id"], 
                aggregated_stats
            )
        
        # Step 6: Unified narration (single GPT entrypoint)
        step_start = time.time()
        try:
            insights, features, work_items = self._bounded_gpt_synthesis(
                combined_matches, aggregated_stats, aspects, comments, company_name
            )
            performance_metrics["gpt_synthesis_time"] = time.time() - step_start
            performance_metrics["gpt_synthesis_success"] = True
        except Exception as e:
            logger.warning(f"Narration failed: {e}, using fallback")
            insights, features, work_items = self._fallback_synthesis(aggregated_stats, aspects)
            performance_metrics["gpt_synthesis_time"] = time.time() - step_start
            performance_metrics["gpt_synthesis_success"] = False
        
        # Calculate total processing time
        total_time = time.time() - start_time
        performance_metrics["total_processing_time"] = total_time
        performance_metrics["comments_per_second"] = len(comments) / total_time if total_time > 0 else 0
        performance_metrics["target_met"] = total_time <= TARGET_PROCESSING_TIME_SECONDS
        
        # Add processing method breakdown
        processing_methods = {}
        for result in similarity_results:
            method = result.get("processing_method", "comment")
            processing_methods[method] = processing_methods.get(method, 0) + 1
        performance_metrics["processing_methods"] = processing_methods
        
        # Log performance summary
        logger.info(
            f"Pipeline completed in {total_time:.2f}s "
            f"({performance_metrics['comments_per_second']:.1f} comments/s, "
            f"target {'✅ MET' if performance_metrics['target_met'] else '❌ MISSED'})"
        )
        
        return ProductionProcessingResult(
            matches=[self._match_to_dict(match) for match in combined_matches],
            aggregated_stats=aggregated_stats,
            processing_time=total_time,
            model_info={
                "aspect_model": self.similarity_service.embedding_service.MODEL_NAME,
                "sentiment_model": self.sentiment_service.MODEL_NAME,
                "processing_method": "production_bi_encoder_similarity_v2",
                "taxonomy_info": taxonomy_info
            },
            insights=insights,
            features=features,
            work_items=work_items,
            performance_metrics=performance_metrics
        )
    
    def _update_taxonomy_quality_metrics(self, taxonomy_id: str, stats: Dict[str, Any]) -> None:
        """Update taxonomy quality metrics after processing (Risk 1 fix)."""
        try:
            unmapped_rate = stats.get("unmapped_rate", 0.0)
            
            # Calculate average aspects per comment
            total_comments = stats["counts"]["total"]
            total_aspect_assignments = sum(
                feature["total_mentions"] for feature in stats.get("features", [])
            )
            avg_aspects_per_comment = total_aspect_assignments / total_comments if total_comments > 0 else 0
            
            # Update taxonomy metrics
            self.taxonomy_service.update_taxonomy_metrics(
                taxonomy_id, unmapped_rate, avg_aspects_per_comment
            )
            
            logger.info(
                f"Updated taxonomy '{taxonomy_id}' quality metrics: "
                f"unmapped={unmapped_rate:.1%}, avg_aspects={avg_aspects_per_comment:.2f}"
            )
            
        except Exception as e:
            logger.warning(f"Failed to update taxonomy quality metrics: {e}")
    
    def check_taxonomy_quality_gate(self, taxonomy_id: str) -> Dict[str, Any]:
        """
        Check if taxonomy passes quality gates before reuse (Risk 1 fix).
        
        Returns quality gate result with recommendation.
        """
        taxonomy = self.taxonomy_service.get_taxonomy(taxonomy_id)
        if not taxonomy:
            return {
                "passed": False,
                "reason": f"Taxonomy '{taxonomy_id}' not found"
            }
        
        return self.taxonomy_service.should_reuse_taxonomy(taxonomy)
    
    def _combine_results(
        self, 
        similarity_results: List[Dict[str, Any]], 
        sentiment_results: List[SentimentResult]
    ) -> List[Dict[str, Any]]:
        """Combine similarity and sentiment results."""
        combined = []
        
        for similarity_result, sentiment in zip(similarity_results, sentiment_results):
            combined.append({
                "comment_id": similarity_result["comment_id"],
                "comment_text": similarity_result["comment_text"],
                "matched_aspects": similarity_result["matched_aspects"],
                "aspect_scores": similarity_result["aspect_scores"],
                "sentiment": sentiment.sentiment,
                "confidence": sentiment.confidence,
                "raw_scores": sentiment.raw_scores
            })
        
        return combined
    
    def _aggregate_results(self, matches: List[Dict[str, Any]], aspects: List[str]) -> Dict[str, Any]:
        """
        Aggregate results with CORRECT aspect vs overall sentiment separation.
        
        Production rule:
        - Aspect sentiment = per (comment, aspect) pair
        - Overall sentiment = per comment (dominant sentiment)
        - These are DIFFERENT metrics, never collapse them
        """
        # Aspect-level sentiment aggregation (per comment-aspect pair)
        aspect_sentiment_counts = defaultdict(lambda: defaultdict(int))
        
        # Overall comment-level sentiment aggregation  
        overall_sentiment_counts = defaultdict(int)
        confidence_dist = defaultdict(int)
        total = len(matches)
        
        # Collect texts per aspect for keyword extraction
        aspect_texts = defaultdict(list)
        
        for match in matches:
            comment_sentiment = match["sentiment"]
            confidence = match["confidence"]
            
            # Overall sentiment (one per comment)
            overall_sentiment_counts[comment_sentiment] += 1
            confidence_dist[confidence] += 1
            
            # Aspect sentiment (one per comment-aspect pair)
            for aspect in match["matched_aspects"]:
                # Each (comment, aspect) pair contributes to aspect sentiment
                aspect_sentiment_counts[aspect][comment_sentiment] += 1
                aspect_texts[aspect].append(match["comment_text"])
        
        # Calculate overall percentages (comment-level)
        overall_percentages = {
            sentiment.lower(): (count / total) * 100 
            for sentiment, count in overall_sentiment_counts.items()
        } if total > 0 else {}
        
        # Extract keywords per aspect (optimized, with domain stoplist)
        aspect_keywords = {}
        for aspect in aspects:
            texts = aspect_texts.get(aspect, [])
            aspect_keywords[aspect] = self._extract_keywords_production(texts, aspect, top_n=8)
        
        # Build features list for frontend (aspect-level sentiment)
        features = []
        for aspect in aspects:
            sentiment_counts = dict(aspect_sentiment_counts[aspect])
            total_mentions = sum(sentiment_counts.values())
            
            if total_mentions > 0:
                features.append({
                    "name": aspect,
                    "sentiment_counts": sentiment_counts,
                    "total_mentions": total_mentions,
                    "keywords": aspect_keywords[aspect]
                })
        
        # Calculate unmapped rate
        unmapped_count = len([m for m in matches if not m["matched_aspects"]])
        unmapped_rate = unmapped_count / total if total > 0 else 0
        
        return {
            # Overall sentiment (comment-level)
            "overall": overall_percentages,
            "counts": {
                "total": total,
                **{sentiment.lower(): count for sentiment, count in overall_sentiment_counts.items()}
            },
            # Aspect sentiment (separate from overall)
            "features": features,
            "confidence_distribution": dict(confidence_dist),
            "unmapped_count": unmapped_count,
            "unmapped_rate": unmapped_rate,
            "aspect_coverage": (total - unmapped_count) / total if total > 0 else 0
        }
    
    def _extract_keywords_production(self, texts: List[str], aspect_name: str, top_n: int = 8) -> List[str]:
        """
        Production-grade keyword extraction with domain stoplist.
        
        Removes:
        - Common stopwords
        - Aspect terms themselves  
        - Sentiment words ("good", "bad", "great", "terrible")
        """
        if not texts:
            return []
        
        # Domain stoplist (aspect terms + sentiment words)
        aspect_terms = set(aspect_name.lower().split())
        sentiment_stopwords = {
            'good', 'bad', 'great', 'terrible', 'awful', 'amazing', 'horrible', 
            'excellent', 'poor', 'fantastic', 'worst', 'best', 'love', 'hate',
            'like', 'dislike', 'nice', 'okay', 'fine', 'perfect', 'broken'
        }
        domain_stoplist = _STOPWORDS | aspect_terms | sentiment_stopwords
        
        # Combine all texts and extract words
        combined_text = " ".join(texts).lower()
        words = _WORD_RE.findall(combined_text)
        
        # Filter stopwords and count
        word_counts = Counter(
            word for word in words 
            if word not in domain_stoplist and len(word) >= 3
        )
        
        # Return top N keywords
        return [word for word, _ in word_counts.most_common(top_n)]
    
    def _bounded_gpt_synthesis(
        self,
        matches: List[Dict[str, Any]],
        aggregated_stats: Dict[str, Any],
        aspects: List[str],
        comments: List[str],
        company_name: str
    ) -> Tuple[List[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Unified narration with lean input and focus.
        """
        narration_service = get_narration_service()

        features = []
        for feature in aggregated_stats.get("features", [])[:8]:
            name = feature.get("name")
            total = feature.get("total_mentions", 0)
            sentiment_counts = feature.get("sentiment_counts", {})
            if not name or total == 0:
                continue
            neg_pct = (sentiment_counts.get("NEGATIVE", 0) / total) if total else 0.0
            mixed_pct = (sentiment_counts.get("MIXED", 0) / total) if total else 0.0
            features.append({
                "aspect_key": self._normalize_aspect_key(name),
                "metrics": {
                    "comment_count": total,
                    "neg_pct": neg_pct,
                    "mixed_pct": mixed_pct,
                },
                "keywords": (feature.get("keywords") or [])[:5],
            })

        narration_input = {
            "project_id": None,
            "analysis_id": None,
            "taxonomy_id": None,
            "taxonomy_version": None,
            "overall": aggregated_stats.get("overall"),
            "features": features,
            "evidence": self._build_evidence_from_matches(matches),
            "work_item_candidates": [],
        }

        narratives = narration_service.generate_narratives(narration_input)
        insights = narratives.get("insights", [])[:3]
        work_items = narratives.get("work_items", [])[:3]
        features_out = [{"insight": insight} for insight in insights]
        return insights, features_out, work_items
    
    def _build_evidence_from_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build evidence list from matches with confidence scores."""
        evidence = []
        conf_map = {"HIGH": 0.9, "MEDIUM": 0.6, "LOW": 0.3}
        for match in matches:
            conf = conf_map.get(str(match.get("confidence", "")).upper(), 0.0)
            for aspect in match.get("matched_aspects", []) or []:
                if aspect == "UNMAPPED":
                    continue
                evidence.append({
                    "aspect_key": self._normalize_aspect_key(aspect),
                    "sentiment": match.get("sentiment"),
                    "text": match.get("comment_text"),
                    "confidence": conf,
                })
        return evidence

    @staticmethod
    def _normalize_aspect_key(label: str) -> str:
        return str(label).strip().lower().replace(" ", "_")
    
    def _get_stratified_samples(self, comments: List[str], max_samples: int = 25) -> List[str]:
        """Get stratified sample of comments (not just first N)."""
        if len(comments) <= max_samples:
            return comments
        
        # Simple stratified sampling - take every Nth comment
        step = len(comments) // max_samples
        return [comments[i] for i in range(0, len(comments), step)][:max_samples]
    
    def _truncate_prompt(self, prompt: str, max_tokens: int) -> str:
        """Truncate prompt to fit token limit."""
        words = prompt.split()
        max_words = int(max_tokens / 1.3)  # Conservative estimate
        
        if len(words) <= max_words:
            return prompt
        
        truncated_words = words[:max_words]
        return " ".join(truncated_words) + "\n\nProvide analysis based on available data."
    
    def _parse_synthesis_result(
        self,
        result: Any,
        aspects: List[str] = None
    ) -> Tuple[List[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse GPT synthesis result."""
        try:
            if isinstance(result, str):
                # Try to extract JSON from string
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    result = result[json_start:json_end]
                parsed = json.loads(result)
            else:
                parsed = result
            
            insights = parsed.get("insights", [])[:3]  # Limit to 3
            work_items = parsed.get("work_items", [])[:3]  # Limit to 3

            # Phase-0 contract guard: LLM must not decide aspects or priorities.
            # This is forbidden because aspect inclusion and priority are deterministic decisions.
            if aspects:
                aspect_set = {str(a).strip().lower() for a in aspects if a and a != "UNMAPPED"}
                features = parsed.get("features", [])
                feature_names = {
                    str(f.get("feature") or f.get("name") or "").strip().lower()
                    for f in features if isinstance(f, dict)
                }
                feature_names.discard("")
                introduced = feature_names - aspect_set
                missing = aspect_set - feature_names
                if introduced:
                    logger.warning(
                        "CONTRACT VIOLATION (Phase-0): LLM introduced new aspects: %s",
                        sorted(introduced),
                    )
                if missing and feature_names:
                    logger.warning(
                        "CONTRACT VIOLATION (Phase-0): LLM omitted deterministic aspects: %s",
                        sorted(missing),
                    )
            if any(isinstance(wi, dict) and "priority" in wi for wi in work_items):
                logger.warning(
                    "CONTRACT VIOLATION (Phase-0): LLM attempted to set work item priority"
                )
            
            # Create features from insights (for backward compatibility)
            features = [{"insight": insight} for insight in insights]
            
            return insights, features, work_items
            
        except Exception as e:
            logger.error(f"Failed to parse synthesis result: {e}")
            raise
    
    def _fallback_synthesis(
        self, 
        stats: Dict[str, Any], 
        aspects: List[str]
    ) -> Tuple[List[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Fallback synthesis when GPT fails."""
        total_comments = stats["counts"]["total"]
        top_aspects = sorted(
            stats.get("features", []), 
            key=lambda x: x["total_mentions"], 
            reverse=True
        )[:3]
        
        insights = [
            f"Analyzed {total_comments} comments across {len(aspects)} aspects",
            f"Top concern: {top_aspects[0]['name']}" if top_aspects else "No major concerns identified",
            "GPT synthesis unavailable - using statistical summary"
        ]
        
        features = [{"insight": insight} for insight in insights]
        
        work_items = [
            {
                "title": "Review Analysis Results",
                "description": "Manual review recommended due to synthesis failure",
                "priority": "MEDIUM"
            }
        ]
        
        return insights, features, work_items
    
    def _match_to_dict(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """Convert match to dictionary for serialization."""
        return {
            "comment_id": match["comment_id"],
            "comment_text": match["comment_text"],
            "matched_aspects": match["matched_aspects"],
            "aspect_scores": match["aspect_scores"],
            "sentiment": match["sentiment"],
            "confidence": match["confidence"],
            "raw_scores": match["raw_scores"]
        }


# Singleton instance
_production_processing_service = None

def get_production_processing_service() -> ProductionProcessingService:
    """Get the singleton instance of ProductionProcessingService."""
    global _production_processing_service
    if _production_processing_service is None:
        _production_processing_service = ProductionProcessingService()
    return _production_processing_service
