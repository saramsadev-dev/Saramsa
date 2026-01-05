"""
Processing service for feedback analysis business logic.

This service handles the core business logic for processing feedback chunks,
AI analysis, normalization, and data aggregation.
"""

import asyncio
import uuid
import json
from collections import defaultdict
from datetime import datetime
from .chunking_service import get_chunking_service
from apis.prompts import getSentAnalysisPrompt, getDeepAnalysisPrompt
import logging

logger = logging.getLogger(__name__)


class ProcessingService:
    """Service for processing feedback and analysis business logic."""
    
    def __init__(self):
        self.chunking_service = get_chunking_service()
    
    async def process_chunks(self, text: str, prompt: str, analysis_type: int):
        """
        Process text chunks with AI analysis.
        
        Args:
            text: Input text to analyze
            prompt: AI prompt to use
            analysis_type: 0 for sentiment, 1 for deep analysis
            
        Returns:
            Analysis results
        """
        # Choose chunking strategy based on analysis type
        if analysis_type == 0:  # Sentiment analysis
            chunks = self.chunking_service.chunk_feedback_for_sentiment(text)
        else:  # Deep analysis
            chunks = self.chunking_service.chunk_feedback_for_deep_analysis(text)
        
        logger.info(f"Processing {len(chunks)} chunks for analysis type {analysis_type}")
        
        # TODO: Integrate with AI completion service
        # This is where you would call the AI service with each chunk
        results = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
            # Placeholder result - replace with actual AI call
            result = {"chunk_index": i, "chunk_length": len(chunk), "processed": True}
            results.append(result)
        
        return results

    async def process_feedback(self, text):
        """
        Process feedback text through complete analysis pipeline.
        
        Args:
            text: Feedback text to analyze
            
        Returns:
            Normalized analysis results
        """
        # Build prompts using structured system with feedback data
        prompt = getSentAnalysisPrompt(feedback_data=text)
        comments_analysis = await self.process_chunks(text, prompt, 0)
        logger.debug("Comment analysis completed", extra={"result": comments_analysis})

        prompt = getDeepAnalysisPrompt(feedback_data=text)
        deep_analysis = await self.process_chunks(text, prompt, 1)
        logger.debug("Deep analysis completed", extra={"result": deep_analysis})

        # Ensure lists
        if isinstance(comments_analysis, str):
            comments_analysis = [comments_analysis]
        if isinstance(deep_analysis, str):
            deep_analysis = [deep_analysis]

        # Normalize and aggregate results
        normalized_results = self._normalize_analysis_results(comments_analysis)
        
        # Save insights to database
        insight_data = self._prepare_insight_data(text, normalized_results, comments_analysis, deep_analysis)
        saved_analysis = self._save_insight(insight_data)
        
        if saved_analysis:
            logger.info(f"Analysis saved to database with ID: {saved_analysis.get('id')}")

        # Return normalized + raw for immediate use
        return {
            **normalized_results,
            'raw_llm': {
                'comment_chunks': comments_analysis,
                'deep_chunks': deep_analysis,
            }
        }

    async def process_uploaded_data_async(self, data, file_type, doc_type):
        """
        Process uploaded data asynchronously based on file type and document type.
        
        Args:
            data: The uploaded data
            file_type: 'json' or 'csv'
            doc_type: 0 for feedback, 1 for user stories
            
        Returns:
            Processing results
        """
        if file_type == 'json':
            logger.info("Processing JSON data")

            if doc_type == 0:  # Feedback processing
                result = await self.process_feedback(str(data))
                return result
            
            # User Stories
            if doc_type == 1:
                return {'status': 'success', 'details': 'User story processing not implemented'}

        elif file_type == 'csv':
            logger.info("Processing CSV data")
            # Simulate async processing
            await asyncio.sleep(1)
            return {
                'status': 'success', 
                'details': 'CSV data processed asynchronously'
            }
        
        return {'status': 'error', 'details': 'Unknown file type'}

    def _normalize_analysis_results(self, comments_analysis):
        """
        Normalize comment analysis across chunks.
        
        Args:
            comments_analysis: List of analysis results from chunks
            
        Returns:
            Normalized analysis dictionary
        """
        total_count = 0
        total_pos = 0
        total_neg = 0
        total_neu = 0

        feature_map = {}
        # Keywords aggregation by polarity
        pos_kw_scores = defaultdict(float)
        pos_kw_counts = defaultdict(int)
        neg_kw_scores = defaultdict(float)
        neg_kw_counts = defaultdict(int)

        def safe_parse(item):
            if isinstance(item, dict):
                return item
            try:
                return json.loads(item)
            except Exception:
                return {}

        for item in comments_analysis:
            data = safe_parse(item)
            counts = data.get('counts') or {}
            
            # Get sentiment data
            t_total = counts.get('total') or 0
            sentiments_any = data.get('sentimentsummary') or data.get('sentiment_summary') or {}
            t_pos = counts.get('positive') or 0
            t_neg = counts.get('negative') or 0
            t_neu = counts.get('neutral') or 0
            
            # If counts are missing but sentiments present, estimate absolute numbers
            if t_total and (not t_pos and not t_neg and not t_neu) and sentiments_any:
                try:
                    p = float(sentiments_any.get('positive') or 0) / 100.0
                    n = float(sentiments_any.get('negative') or 0) / 100.0
                    z = float(sentiments_any.get('neutral') or 0) / 100.0
                    t_pos = round(t_total * p)
                    t_neg = round(t_total * n)
                    t_neu = max(0, t_total - t_pos - t_neg)
                except Exception:
                    pass
                    
            total_count += t_total
            total_pos += t_pos
            total_neg += t_neg
            total_neu += t_neu

            # Process features
            self._process_features(data, feature_map)
            
            # Process keywords
            self._process_keywords(data, pos_kw_scores, pos_kw_counts, neg_kw_scores, neg_kw_counts)

        # Build overall sentiment percentages
        overall = self._calculate_overall_sentiment(total_count, total_pos, total_neg, total_neu)
        
        # Consolidate features and keywords
        normalized_features = list(feature_map.values())
        positive_keywords = self._consolidate_keywords(pos_kw_scores, pos_kw_counts)
        negative_keywords = self._consolidate_keywords(neg_kw_scores, neg_kw_counts)

        return {
            'overall': overall,
            'counts': {
                'total': total_count,
                'positive': total_pos,
                'negative': total_neg,
                'neutral': total_neu,
            },
            'features': normalized_features,
            'positive_keywords': positive_keywords,
            'negative_keywords': negative_keywords,
        }

    def _process_features(self, data, feature_map):
        """Process and merge features from analysis data."""
        features_list = data.get('feature_asba') or data.get('featureasba') or []
        for feat in features_list:
            name = (feat.get('feature') or '').strip()
            if not name:
                continue
                
            key = name.lower()
            existing = feature_map.get(key)
            sentiment = feat.get('sentiment') or {}
            
            description_value = (
                feat.get('description') or 
                feat.get('feature_description') or 
                feat.get('desc') or ''
            )
            keywords_value = feat.get('keywords') or feat.get('feature_keywords') or []
            
            if not existing:
                feature_map[key] = {
                    'name': name,
                    'description': description_value,
                    'sentiment': {
                        'positive': float(sentiment.get('positive') or 0),
                        'negative': float(sentiment.get('negative') or 0),
                        'neutral': float(sentiment.get('neutral') or 0),
                    },
                    'keywords': list(keywords_value),
                }
            else:
                # Merge existing feature
                if not existing.get('description') and description_value:
                    existing['description'] = description_value
                    
                # Average sentiments
                for k in ('positive', 'negative', 'neutral'):
                    try:
                        existing['sentiment'][k] = (
                            existing['sentiment'][k] + float(sentiment.get(k) or 0)
                        ) / 2.0
                    except Exception:
                        pass
                        
                # Merge keywords
                kw_set = set(existing.get('keywords') or [])
                for kw in (keywords_value or []):
                    if kw not in kw_set:
                        existing['keywords'].append(kw)
                        kw_set.add(kw)

    def _process_keywords(self, data, pos_kw_scores, pos_kw_counts, neg_kw_scores, neg_kw_counts):
        """Process and aggregate keywords from analysis data."""
        # Process positive keywords
        for kw in (data.get('positive_keywords') or data.get('positivekeywords') or []):
            word = kw.get('keyword') if isinstance(kw, dict) else None
            score = kw.get('sentiment') if isinstance(kw, dict) else None
            if word:
                pos_kw_counts[word] += 1
                if isinstance(score, (int, float)):
                    pos_kw_scores[word] += float(score)
                    
        # Process negative keywords
        for kw in (data.get('negative_keywords') or data.get('negativekeywords') or []):
            word = kw.get('keyword') if isinstance(kw, dict) else None
            score = kw.get('sentiment') if isinstance(kw, dict) else None
            if word:
                neg_kw_counts[word] += 1
                if isinstance(score, (int, float)):
                    neg_kw_scores[word] += float(score)

    def _calculate_overall_sentiment(self, total_count, total_pos, total_neg, total_neu):
        """Calculate overall sentiment percentages."""
        if total_count > 0:
            return {
                'positive': round((total_pos / total_count) * 100, 2),
                'negative': round((total_neg / total_count) * 100, 2),
                'neutral': round((total_neu / total_count) * 100, 2),
            }
        return None

    def _consolidate_keywords(self, scores, counts):
        """Consolidate keywords with scores and counts."""
        items = []
        for w, c in counts.items():
            avg = scores[w] / c if c else 0.0
            items.append({'keyword': w, 'sentiment': round(avg, 3)})
        # Sort by count desc then sentiment desc
        items.sort(key=lambda x: (counts[x['keyword']], x['sentiment']), reverse=True)
        return items

    def _prepare_insight_data(self, text, normalized_results, comments_analysis, deep_analysis):
        """Prepare insight data for database storage."""
        insight_id = str(uuid.uuid4())
        return {
            'id': f'insight_{insight_id}',
            'type': 'insight',
            'analysis_type': 'feedback_analysis',
            'analysis_date': datetime.now().isoformat(),
            'schema_version': 2,
            **normalized_results,
            'raw_llm': {
                'comment_chunks': comments_analysis,
                'deep_chunks': deep_analysis,
            },
            'metadata': {
                'source': 'file_upload',
                'text_length': len(text),
                'processing_timestamp': datetime.now().isoformat()
            }
        }

    def _save_insight(self, insight_data):
        """Save insight data to database."""
        try:
            from apis.infrastructure.cosmos_service import cosmos_service
            return cosmos_service.save_analysis_data(insight_data)
        except Exception as e:
            logger.error(f"Error saving insight to database: {e}")
            return None


# Global service instance
_processing_service = None

def get_processing_service():
    """Get the global processing service instance."""
    global _processing_service
    if _processing_service is None:
        _processing_service = ProcessingService()
    return _processing_service