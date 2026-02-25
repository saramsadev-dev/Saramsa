"""
Aggregation Service for Sentiment Analysis

This service handles all deterministic operations that should NOT be done by LLM:
- Counting comments by sentiment
- Calculating percentages
- Aggregating aspects (from locked semantic schema)
- Filtering outliers
- Computing statistics

The LLM should only extract semantic data per comment, and this service aggregates it.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class SentimentAggregationService:
    """Service for aggregating sentiment analysis results from LLM-extracted data."""
    
    # Configuration constants
    MIN_ASPECT_MENTIONS = 3  # Minimum mentions to create an aspect category
    OUTLIER_DETECTION_THRESHOLD = 0.15  # 15% threshold for outlier detection
    KEYWORD_MIN_OCCURRENCES = 2  # Minimum occurrences for keyword to be significant
    
    def aggregate_comment_extractions(self, extracted_comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate LLM-extracted comment data into summary statistics.
        
        Args:
            extracted_comments: List of comment extractions from LLM (CommentExtraction schema), where each entry has:
                - comment_id (int)
                - sentiment (POSITIVE/NEGATIVE/NEUTRAL)
                - confidence (HIGH/MEDIUM/LOW)
                - intent_type (PRAISE/COMPLAINT/SUGGESTION/OBSERVATION)
                - intent_phrase (str)
                - keywords (List[str])
                - aspects (List[str])
                
        Returns:
            Aggregated results with counts, percentages, and aspect summaries
        """
        if not extracted_comments:
            return self._empty_results()
        
        # Step 1: Count sentiments (handles POSITIVE, NEGATIVE, NEUTRAL)
        sentiment_counts = self._count_sentiments(extracted_comments)
        
        # Step 2: Calculate percentages
        total_comments = len(extracted_comments)
        sentiment_percentages = self._calculate_percentages(sentiment_counts, total_comments)
        
        # Step 3: Aggregate aspects (aspect-level sentiment breakdown)
        aspect_aggregations = self._aggregate_aspects(extracted_comments)
        
        # Step 4: Aggregate keywords
        keyword_aggregations = self._aggregate_keywords(extracted_comments)
        
        # Step 5: Filter outliers (optional, based on configuration)
        filtered_aspects = self._filter_outliers(aspect_aggregations)
        
        # Step 6: Calculate aspect coverage (% of comments with at least one aspect)
        aspect_coverage = self._calculate_aspect_coverage(extracted_comments, total_comments)
        
        # Build "overall" summary (frontend expects this)
        overall_summary = {
            "positive": sentiment_percentages.get("positive", 0.0),
            "negative": sentiment_percentages.get("negative", 0.0),
            "neutral": sentiment_percentages.get("neutral", 0.0),
        }

        return {
            "overall": overall_summary,  # Frontend expects this field
            "counts": {
                "total": total_comments,
                "positive": sentiment_counts.get("positive", 0),
                "negative": sentiment_counts.get("negative", 0),
                "neutral": sentiment_counts.get("neutral", 0),
            },
            "sentiment_summary": {
                "positive": f"{sentiment_percentages.get('positive', 0):.2f}%",
                "negative": f"{sentiment_percentages.get('negative', 0):.2f}%",
                "neutral": f"{sentiment_percentages.get('neutral', 0):.2f}%",
            },
            "features": filtered_aspects,  # Use "features" for frontend (alias for aspects)
            "feature_asba": filtered_aspects,  # Keep legacy field name for compatibility
            "positive_keywords": keyword_aggregations["positive"],
            "negative_keywords": keyword_aggregations["negative"],
            "aspect_coverage": aspect_coverage,  # New: % of comments with aspects
        }
    
    def _count_sentiments(self, extracted_comments: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count comments by sentiment type (handles POSITIVE, NEGATIVE, NEUTRAL)."""
        counts = Counter()
        for comment in extracted_comments:
            sentiment = comment.get("sentiment", "NEUTRAL").upper()
            # Map enum values to lowercase keys for consistency
            sentiment_map = {
                "POSITIVE": "positive",
                "NEGATIVE": "negative",
                "NEUTRAL": "neutral",
                "MIXED": "neutral",
            }
            if sentiment in sentiment_map:
                counts[sentiment_map[sentiment]] += 1
            else:
                # Fallback: try lowercase
                sentiment_lower = sentiment.lower()
                if sentiment_lower in ["positive", "negative", "neutral"]:
                    counts[sentiment_lower] += 1
                else:
                    logger.warning(f"Unknown sentiment value: {sentiment}, defaulting to neutral")
                    counts["neutral"] += 1
        return dict(counts)
    
    def _calculate_percentages(self, counts: Dict[str, int], total: int) -> Dict[str, float]:
        """Calculate sentiment percentages."""
        if total == 0:
            return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

        return {
            "positive": (counts.get("positive", 0) / total) * 100,
            "negative": (counts.get("negative", 0) / total) * 100,
            "neutral": (counts.get("neutral", 0) / total) * 100,
        }
    
    def _aggregate_aspects(self, extracted_comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aggregate aspects across all comments with aspect-level sentiment breakdown.
        
        In the locked semantic schema, aspects are simple strings (List[str]),
        and we use the comment-level sentiment to calculate aspect-level sentiment.
        
        Returns:
            List of aspect summaries with sentiment breakdowns and comment counts
        """
        # Aspect aggregation structure:
        # aspect_name -> {
        #   "comment_indices": [list of indices],
        #   "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0},
        #   "all_keywords": set(),
        # }
        aspect_data = defaultdict(lambda: {
            "comment_indices": [],
            "sentiment_counts": Counter({"positive": 0, "negative": 0, "neutral": 0}),
            "all_keywords": set(),
        })
        
        # Aggregate aspect mentions
        for idx, comment in enumerate(extracted_comments):
            # Get aspects (simple array of strings)
            aspects = comment.get("aspects", [])
            if not isinstance(aspects, list):
                continue
            
            # Get comment-level sentiment (used for aspect-level breakdown)
            comment_sentiment = comment.get("sentiment", "NEUTRAL").upper()
            sentiment_map = {
                "POSITIVE": "positive",
                "NEGATIVE": "negative",
                "NEUTRAL": "neutral",
                "MIXED": "neutral",
            }
            sentiment_key = sentiment_map.get(comment_sentiment, "neutral")
            
            # Get keywords for this comment
            keywords = comment.get("keywords", [])
            if not isinstance(keywords, list):
                keywords = []
            
            # Aggregate each aspect mentioned in this comment
            for aspect in aspects:
                if not isinstance(aspect, str):
                    continue
                
                aspect_name = aspect.strip()
                if not aspect_name:
                    continue
                
                # Normalize aspect name (case-insensitive grouping)
                aspect_key = aspect_name.lower()
                
                aspect_data[aspect_key]["comment_indices"].append(idx)
                
                # Count sentiment for this aspect (using comment-level sentiment)
                aspect_data[aspect_key]["sentiment_counts"][sentiment_key] += 1
                
                # Aggregate keywords for this aspect
                aspect_data[aspect_key]["all_keywords"].update(
                    kw.strip() for kw in keywords if isinstance(kw, str) and kw.strip()
                )
        
        # Build aspect summaries (only include aspects with minimum mentions)
        aspect_summaries = []
        for aspect_key, data in aspect_data.items():
            comment_count = len(data["comment_indices"])
            
            # Filter by minimum mentions threshold
            if comment_count < self.MIN_ASPECT_MENTIONS:
                continue
            
            # Calculate aspect sentiment percentages (as NUMBERS, not strings with %)
            # Frontend expects numbers for calculations and display
            total_aspect_mentions = sum(data["sentiment_counts"].values())
            if total_aspect_mentions == 0:
                sentiment_percentages = {
                    "positive": 0.0,
                    "negative": 0.0,
                    "neutral": 100.0,
                }
            else:
                sentiment_percentages = {
                    "positive": round((data['sentiment_counts']['positive'] / total_aspect_mentions) * 100, 1),
                    "negative": round((data['sentiment_counts']['negative'] / total_aspect_mentions) * 100, 1),
                    "neutral": round((data['sentiment_counts']['neutral'] / total_aspect_mentions) * 100, 1),
                }
            
            # Generate description
            description = self._generate_aspect_description(aspect_key, data, extracted_comments)
            
            # Use original casing from first occurrence for display
            # (preserve user's preferred capitalization)
            original_aspect_name = aspect_key
            for comment_idx in data["comment_indices"]:
                if comment_idx < len(extracted_comments):
                    comment_aspects = extracted_comments[comment_idx].get("aspects", [])
                    for asp in comment_aspects:
                        if isinstance(asp, str) and asp.strip().lower() == aspect_key:
                            original_aspect_name = asp.strip()
                            break
                    if original_aspect_name != aspect_key:
                        break
            
            aspect_summaries.append({
                "feature": original_aspect_name,  # Keep field name "feature" for frontend compatibility
                "description": description,
                "sentiment": sentiment_percentages,
                "keywords": list(data["all_keywords"])[:20],  # Limit to top 20 keywords
                "comment_count": comment_count,
            })
        
        # Sort by comment count (descending)
        aspect_summaries.sort(key=lambda x: x["comment_count"], reverse=True)
        
        return aspect_summaries
    
    def _calculate_aspect_coverage(self, extracted_comments: List[Dict[str, Any]], total_comments: int) -> float:
        """
        Calculate aspect coverage: % of comments that have at least one aspect.
        
        Args:
            extracted_comments: List of comment extractions
            total_comments: Total number of comments
            
        Returns:
            Coverage percentage (0.0 - 100.0)
        """
        if total_comments == 0:
            return 0.0
        
        comments_with_aspects = 0
        for comment in extracted_comments:
            aspects = comment.get("aspects", [])
            if isinstance(aspects, list) and len(aspects) > 0:
                # Check if any aspect is non-empty
                if any(isinstance(asp, str) and asp.strip() for asp in aspects):
                    comments_with_aspects += 1
        
        return (comments_with_aspects / total_comments) * 100
    
    def _aggregate_keywords(self, extracted_comments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate keywords by comment-level sentiment polarity.
        
        In the locked semantic schema, keywords are simple strings (List[str]).
        We use the comment-level sentiment to determine keyword polarity.
        
        Returns:
            Dictionary with "positive" and "negative" keyword lists
        """
        positive_keywords = Counter()
        negative_keywords = Counter()
        neutral_keywords = Counter()
        
        # Map comment sentiment to keyword buckets
        for comment in extracted_comments:
            keywords = comment.get("keywords", [])
            if not isinstance(keywords, list):
                continue
            
            comment_sentiment = comment.get("sentiment", "NEUTRAL").upper()
            
            # Aggregate keywords based on comment-level sentiment
            for kw in keywords:
                if not isinstance(kw, str):
                    continue
                
                kw_text = kw.strip().lower()
                if not kw_text:
                    continue
                
                # Categorize keyword based on comment sentiment
                if comment_sentiment == "POSITIVE":
                    positive_keywords[kw_text] += 1
                elif comment_sentiment == "NEGATIVE":
                    negative_keywords[kw_text] += 1
                else:  # NEUTRAL (includes former MIXED)
                    neutral_keywords[kw_text] += 1
        
        # Build keyword lists (only include keywords meeting minimum occurrences)
        # For positive/negative, use a simple count-based sentiment score (frequency)
        positive_kw_list = [
            {
                "keyword": kw,
                "sentiment": min(round(count / 10.0, 2), 1.0),  # Normalize to 0-1 range
            }
            for kw, count in positive_keywords.items()
            if count >= self.KEYWORD_MIN_OCCURRENCES
        ]
        
        negative_kw_list = [
            {
                "keyword": kw,
                "sentiment": min(round(count / 10.0, 2), 1.0),  # Normalize to 0-1 range
            }
            for kw, count in negative_keywords.items()
            if count >= self.KEYWORD_MIN_OCCURRENCES
        ]
        
        # Sort by count (descending), then by keyword (alphabetical)
        positive_kw_list.sort(key=lambda x: (positive_keywords[x["keyword"].lower()], x["keyword"]), reverse=True)
        negative_kw_list.sort(key=lambda x: (negative_keywords[x["keyword"].lower()], x["keyword"]), reverse=True)
        
        return {
            "positive": positive_kw_list[:50],  # Top 50 positive keywords
            "negative": negative_kw_list[:50],  # Top 50 negative keywords
        }
    
    def _filter_outliers(self, aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter outlier aspects based on statistical thresholds.
        
        Currently implements simple threshold-based filtering.
        Can be enhanced with more sophisticated statistical methods.
        """
        if not aspects:
            return aspects
        
        # Filter aspects that are statistical outliers (e.g., too few or too many mentions)
        # This is a simple implementation - can be enhanced with z-score or IQR methods
        filtered = []
        for aspect in aspects:
            comment_count = aspect.get("comment_count", 0)
            
            # Keep aspects within reasonable bounds
            # Could add more sophisticated outlier detection here
            if comment_count >= self.MIN_ASPECT_MENTIONS:
                filtered.append(aspect)
        
        return filtered
    
    def _generate_aspect_description(self, aspect_name: str, aspect_data: Dict, 
                                     extracted_comments: List[Dict[str, Any]]) -> str:
        """
        Generate a description for an aspect based on aggregated data.
        
        This is a simple implementation. In the future, this could use LLM
        to generate natural language summaries, but it would be a separate
        call after aggregation (not mixing with extraction).
        """
        comment_count = len(aspect_data["comment_indices"])
        sentiment_counts = aspect_data["sentiment_counts"]
        
        # Simple rule-based description
        dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else "neutral"
        
        if dominant_sentiment == "positive":
            desc = f"Users generally have positive feedback about {aspect_name}."
        elif dominant_sentiment == "negative":
            desc = f"Users have concerns and negative feedback about {aspect_name}."
        else:
            desc = f"Neutral feedback about {aspect_name} from users."
        
        return desc
    
    def _empty_results(self) -> Dict[str, Any]:
        """Return empty results structure."""
        return {
            "overall": {"positive": 0.0, "negative": 0.0, "neutral": 0.0},
            "counts": {"total": 0, "positive": 0, "negative": 0, "neutral": 0},
            "sentiment_summary": {"positive": "0%", "negative": "0%", "neutral": "0%"},
            "features": [],
            "feature_asba": [],
            "positive_keywords": [],
            "negative_keywords": [],
            "aspect_coverage": 0.0,
        }


# Global service instance
_aggregation_service = None

def get_aggregation_service() -> SentimentAggregationService:
    """Get the global aggregation service instance."""
    global _aggregation_service
    if _aggregation_service is None:
        _aggregation_service = SentimentAggregationService()
    return _aggregation_service