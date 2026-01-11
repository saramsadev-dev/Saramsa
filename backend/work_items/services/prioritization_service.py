"""
Prioritization Service for Work Items

This service handles deterministic prioritization logic based on sentiment metrics.
The LLM should only generate work item descriptions, and this service determines priority.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class WorkItemPrioritizationService:
    """Service for prioritizing work items based on sentiment metrics."""
    
    # Priority thresholds based on sentiment metrics
    CRITICAL_THRESHOLD = {
        "negative_percentage": 70.0,  # >70% negative sentiment
        "comment_count": 50,  # >50 comments
        "user_impact": 0.5,  # >50% of user base affected
    }
    
    HIGH_THRESHOLD = {
        "negative_percentage": 50.0,  # >50% negative sentiment
        "comment_count": 25,  # >25 comments
        "user_impact": 0.25,  # >25% of user base affected
    }
    
    MEDIUM_THRESHOLD = {
        "negative_percentage": 30.0,  # >30% negative sentiment
        "comment_count": 10,  # >10 comments
        "user_impact": 0.10,  # >10% of user base affected
    }
    
    def prioritize_work_items(self, work_items: List[Dict[str, Any]], 
                             analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prioritize work items based on sentiment analysis data.
        
        Args:
            work_items: List of work items from LLM (may have priority already, but we override)
            analysis_data: Sentiment analysis data with features and metrics
            
        Returns:
            Work items with updated priorities based on deterministic rules
        """
        if not work_items:
            return work_items
        
        # Extract feature metrics from analysis data
        feature_metrics = self._extract_feature_metrics(analysis_data)
        
        # Prioritize each work item
        prioritized_items = []
        for item in work_items:
            prioritized_item = item.copy()
            
            # Get feature area for this work item
            feature_area = item.get("feature_area", "").lower() or item.get("featurearea", "").lower()
            
            # Find matching feature metrics
            feature_metric = feature_metrics.get(feature_area)
            
            # Determine priority based on metrics
            priority = self._calculate_priority(feature_metric, item)
            prioritized_item["priority"] = priority
            
            # Update business value with metrics if available
            if feature_metric:
                prioritized_item["business_value"] = self._enhance_business_value(
                    item.get("business_value", ""), 
                    feature_metric
                )
            
            prioritized_items.append(prioritized_item)
        
        return prioritized_items
    
    def _extract_feature_metrics(self, analysis_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Extract feature-level metrics from analysis data.
        
        Returns:
            Dictionary mapping feature names (lowercase) to their metrics
        """
        feature_metrics = {}
        
        # Extract features from various possible locations in analysis_data
        features = []
        if isinstance(analysis_data, dict):
            # Try nested analysisData
            nested_data = analysis_data.get('analysisData', {})
            if isinstance(nested_data, dict):
                features = nested_data.get('features', []) or nested_data.get('feature_asba', []) or nested_data.get('featureasba', [])
            else:
                # Try direct keys
                features = analysis_data.get('features', []) or analysis_data.get('feature_asba', []) or analysis_data.get('featureasba', [])
        
        # Build feature metrics dictionary
        for feature in features:
            if not isinstance(feature, dict):
                continue
            
            feature_name = feature.get('feature', '').strip().lower() or feature.get('name', '').strip().lower()
            if not feature_name:
                continue
            
            sentiment = feature.get('sentiment', {})
            if isinstance(sentiment, dict):
                # Parse percentage strings like "60%"
                def parse_percentage(value):
                    if isinstance(value, (int, float)):
                        return float(value)
                    if isinstance(value, str):
                        return float(value.replace('%', '').strip())
                    return 0.0
                
                comment_count = int(feature.get('comment_count', 0) or feature.get('commentcount', 0))
                
                feature_metrics[feature_name] = {
                    "negative_percentage": parse_percentage(sentiment.get('negative', 0)),
                    "positive_percentage": parse_percentage(sentiment.get('positive', 0)),
                    "neutral_percentage": parse_percentage(sentiment.get('neutral', 0)),
                    "comment_count": comment_count,
                }
        
        return feature_metrics
    
    def _calculate_priority(self, feature_metric: Optional[Dict[str, float]], 
                          work_item: Dict[str, Any]) -> str:
        """
        Calculate priority based on feature metrics.
        
        Returns:
            Priority level: "critical", "high", "medium", or "low"
        """
        if not feature_metric:
            # Fallback to existing priority if no metrics available
            return work_item.get("priority", "medium").lower()
        
        negative_pct = feature_metric.get("negative_percentage", 0.0)
        comment_count = feature_metric.get("comment_count", 0)
        
        # Calculate priority based on thresholds
        # Critical: High negative sentiment AND high comment count
        if (negative_pct >= self.CRITICAL_THRESHOLD["negative_percentage"] and 
            comment_count >= self.CRITICAL_THRESHOLD["comment_count"]):
            return "critical"
        
        # High: Medium-high negative sentiment OR high comment count
        if (negative_pct >= self.HIGH_THRESHOLD["negative_percentage"] or 
            comment_count >= self.HIGH_THRESHOLD["comment_count"]):
            return "high"
        
        # Medium: Some negative sentiment OR moderate comment count
        if (negative_pct >= self.MEDIUM_THRESHOLD["negative_percentage"] or 
            comment_count >= self.MEDIUM_THRESHOLD["comment_count"]):
            return "medium"
        
        # Low: Everything else
        return "low"
    
    def _enhance_business_value(self, existing_value: str, feature_metric: Dict[str, float]) -> str:
        """Enhance business value statement with quantitative metrics."""
        negative_pct = feature_metric.get("negative_percentage", 0.0)
        comment_count = feature_metric.get("comment_count", 0)
        
        metrics_text = f" ({negative_pct:.1f}% negative sentiment from {comment_count} comments)"
        
        if existing_value:
            return existing_value + metrics_text
        return f"Address customer concerns{metrics_text}"


# Global service instance
_prioritization_service = None

def get_prioritization_service() -> WorkItemPrioritizationService:
    """Get the global prioritization service instance."""
    global _prioritization_service
    if _prioritization_service is None:
        _prioritization_service = WorkItemPrioritizationService()
    return _prioritization_service