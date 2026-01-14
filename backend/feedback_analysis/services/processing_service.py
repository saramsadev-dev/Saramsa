"""
Processing service for feedback analysis business logic.

This service handles the core business logic for processing feedback chunks,
AI analysis, normalization, and data aggregation.

CRITICAL: Implements batch integrity validation - validates output length,
comment_id uniqueness, and schema compliance before accepting results.
"""

import asyncio
import uuid
import json
from collections import defaultdict
from datetime import datetime
from .chunking_service import get_chunking_service
from .retry_service import get_retry_service
from .schema_validator import get_validation_service
from apis.prompts import getSentAnalysisPrompt, getDeepAnalysisPrompt
from aiCore.services.completion_service import generate_completions
import logging

logger = logging.getLogger(__name__)


class ProcessingService:
    """Service for processing feedback and analysis business logic."""
    
    def __init__(self):
        self.chunking_service = get_chunking_service()
        self.retry_service = get_retry_service()
        self.validation_service = get_validation_service()
    
    async def process_chunks(self, text: str, prompt_template: str = None, analysis_type: int = 0, 
                            company_name: str = None, suggested_aspects: list = None):
        """
        Process text chunks with AI analysis with automatic retry and batch integrity validation.
        
        CRITICAL: Each batch is validated for integrity before acceptance:
        - Output is valid JSON
        - Output length == input comment count
        - Every comment_id exists exactly once
        - All enum fields contain allowed values
        - If validation fails: retry the batch (do NOT partially store)
        
        Args:
            text: Input text to analyze
            prompt_template: Base prompt template (deprecated, prompts are created per chunk) - kept for backward compatibility
            analysis_type: 0 for sentiment, 1 for deep analysis
            company_name: Optional company name for prompt customization
            suggested_aspects: Optional list of approved aspects (frozen aspect list) - LLM MUST use only these
            
        Returns:
            Analysis results from AI service (only validated batches included)
        """
        # Choose chunking strategy based on analysis type
        if analysis_type == 0:  # Sentiment analysis
            chunks = self.chunking_service.chunk_feedback_for_sentiment(text)
        else:  # Deep analysis
            chunks = self.chunking_service.chunk_feedback_for_deep_analysis(text)
        
        logger.info(f"Processing {len(chunks)} chunks for analysis type {analysis_type}")
        
        # Calculate expected comment count per chunk
        chunk_comment_counts = [self._count_comments_in_chunk(chunk) for chunk in chunks]
        logger.debug(f"Expected comment counts per chunk: {chunk_comment_counts}")
        
        # Calculate starting indices for each batch (for global comment_id mapping)
        # Batch 0: starts at 0, Batch 1: starts at count of batch 0, etc.
        batch_start_indices = []
        cumulative_index = 0
        for count in chunk_comment_counts:
            batch_start_indices.append(cumulative_index)
            cumulative_index += count
        
        results = []
        successful_batches = 0
        failed_batches = 0
        
        for i, chunk in enumerate(chunks):
            expected_count = chunk_comment_counts[i]
            comment_start_index = batch_start_indices[i]
            logger.debug(f"Processing chunk {i+1}/{len(chunks)} (expected {expected_count} comments, starting at global index {comment_start_index}, length: {len(chunk)} chars)")
            
            # Capture loop variables in closure to avoid late binding issues
            current_chunk = chunk
            current_start_index = comment_start_index
            current_batch_index = i
            current_expected_count = expected_count
            
            # Define the operation for this batch with validation
            async def process_single_chunk_with_validation():
                # Create prompt for this specific chunk with correct starting index
                if analysis_type == 0:  # Sentiment analysis
                    chunk_prompt = getSentAnalysisPrompt(
                        company_name=company_name, 
                        feedback_data=current_chunk,
                        suggested_aspects=suggested_aspects,
                        comment_start_index=current_start_index  # Pass global starting index
                    )
                else:  # Deep analysis
                    chunk_prompt = getDeepAnalysisPrompt(company_name=company_name, feedback_data=chunk)
                
                # Call AI completion service with the chunk-specific prompt
                # Calculate required max_tokens: ~150 tokens per comment extraction object
                # For safety, use 200 tokens per comment + 500 buffer
                estimated_tokens_needed = (current_expected_count * 200) + 500
                # Ensure minimum of 4000 tokens for batch processing
                max_tokens = max(estimated_tokens_needed, 4000)
                logger.info(f"📡 [Batch {current_batch_index}] Calling LLM API with max_tokens={max_tokens} (for {current_expected_count} comments)...")
                result = await generate_completions(chunk_prompt, max_tokens=max_tokens)
                logger.info(f"📡 [Batch {current_batch_index}] LLM API response received (type: {type(result).__name__})")
                
                # CRITICAL: Validate batch integrity immediately after LLM response
                logger.info(f"🔍 [Batch {current_batch_index}] Starting validation...")
                valid_extractions, errors, is_valid = self.validation_service.validate_batch_output(
                    result,
                    batch_index=current_batch_index,
                    expected_count=current_expected_count,
                    batch_start_index=current_start_index  # Pass global starting index for correct comment_id fallback
                )
                logger.info(f"🔍 [Batch {current_batch_index}] Validation complete: is_valid={is_valid}, valid_count={len(valid_extractions)}, errors={len(errors)}")
                
                if not is_valid:
                    # Validation failed - raise exception to trigger retry
                    error_summary = f"Batch {current_batch_index} validation failed: {len(errors)} errors. First error: {errors[0] if errors else 'Unknown'}"
                    logger.error(error_summary)
                    raise ValueError(error_summary)
                
                logger.debug(f"Chunk {current_batch_index+1} analysis and validation completed successfully")
                return result
            
            # Process batch with async retry mechanism (since we're already in async context)
            # Directly await the async function - no need for sync wrapper since process_chunks is async
            max_retries = 3
            result = None
            success = False
            last_error = None
            validation_errors = []
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    logger.info(f"🔄 [Batch {i+1}] Attempt {attempt + 1}/{max_retries + 1}...")
                    result = await process_single_chunk_with_validation()
                    
                    # Final validation check before accepting (already done in process_single_chunk_with_validation, but double-check)
                    valid_extractions, errors, is_valid = self.validation_service.validate_batch_output(
                        result,
                        batch_index=i,
                        expected_count=expected_count,
                        batch_start_index=comment_start_index  # Pass global starting index for correct comment_id fallback
                    )
                    validation_errors = errors  # Store for potential error reporting
                    
                    if is_valid:
                        results.append(result)
                        successful_batches += 1
                        success = True
                        if attempt > 0:
                            logger.info(f"✅ Batch {i+1} succeeded after {attempt} retries ({expected_count} comments)")
                        else:
                            logger.info(f"✅ Batch {i+1} processed and validated successfully ({expected_count} comments)")
                        break
                    else:
                        # Validation failed - raise to trigger retry
                        raise ValueError(f"Validation failed: {errors[0] if errors else 'Unknown error'}")
                        
                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    
                    # Check if we've exhausted retries
                    if attempt >= max_retries:
                        failed_batches += 1
                        logger.error(f"❌ Batch {i+1} failed after {max_retries + 1} attempts: {error_msg}")
                        results.append({
                            "chunk_index": i,
                            "error": error_msg,
                            "validation_errors": validation_errors,
                            "processed": False,
                            "attempts": attempt + 1
                        })
                        break
                    else:
                        # Calculate delay for next retry (exponential backoff)
                        delay = min(2 ** attempt, 8)  # 1s, 2s, 4s, max 8s
                        logger.warning(
                            f"⚠️ Batch {i+1} attempt {attempt + 1} failed: {error_msg}. "
                            f"Retrying in {delay}s... ({max_retries - attempt} retries left)"
                        )
                        await asyncio.sleep(delay)
        
        # Log summary
        logger.info(
            f"Completed processing {len(chunks)} chunks: "
            f"{successful_batches} successful, {failed_batches} failed"
        )
        
        # If too many batches failed, log warning
        failure_rate = failed_batches / len(chunks) if chunks else 0
        if failure_rate > 0.1:  # More than 10% failure rate
            logger.warning(
                f"High batch failure rate: {failed_batches}/{len(chunks)} batches failed ({failure_rate:.1%})"
            )
        
        return results
    
    def _count_comments_in_chunk(self, chunk: str) -> int:
        """
        Count comments in a chunk string.
        
        Since chunks are created by joining comments with '\n', we count
        non-empty lines as comments.
        
        Args:
            chunk: Chunk string (newline-separated comments)
            
        Returns:
            Number of comments in the chunk
        """
        if not chunk:
            return 0
        
        # Count non-empty lines (comments)
        lines = chunk.split('\n')
        comment_count = len([line for line in lines if line.strip()])
        return comment_count
    
    async def process_feedback(self, text, company_name: str = None, suggested_aspects: list = None):
        """
        Process feedback text through complete analysis pipeline.
        
        Args:
            text: Feedback text to analyze
            company_name: Optional company name for prompt customization
            suggested_aspects: Optional list of approved aspects (frozen aspect list)
            
        Returns:
            Normalized analysis results
        """
        # Process chunks with sentiment analysis (prompts are created per chunk inside process_chunks)
        comments_analysis = await self.process_chunks(
            text, None, 0, company_name=company_name, suggested_aspects=suggested_aspects
        )
        logger.debug("Comment analysis completed", extra={"result": comments_analysis})

        # Process chunks with deep analysis (prompts are created per chunk inside process_chunks)
        deep_analysis = await self.process_chunks(text, None, 1, company_name=company_name)
        logger.debug("Deep analysis completed", extra={"result": deep_analysis})

        # Ensure lists
        if isinstance(comments_analysis, str):
            comments_analysis = [comments_analysis]
        if isinstance(deep_analysis, str):
            deep_analysis = [deep_analysis]

        # Parse LLM extractions and aggregate using aggregation service
        extracted_comments = self._parse_llm_extractions(comments_analysis)
        
        if extracted_comments is None:
            # Legacy format: use old normalization (backward compatibility)
            logger.warning("Using legacy normalization due to old LLM format")
            normalized_results = self._normalize_analysis_results_legacy(comments_analysis)
        else:
            # New format: use aggregation service
            from .aggregation_service import get_aggregation_service
            aggregation_service = get_aggregation_service()
            normalized_results = aggregation_service.aggregate_comment_extractions(extracted_comments)
        
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

    async def process_uploaded_data_async(self, data, file_type, doc_type, suggested_aspects: list = None):
        """
        Process uploaded data asynchronously based on file type and document type.
        
        Args:
            data: The uploaded data
            file_type: 'json' or 'csv'
            doc_type: 0 for feedback, 1 for user stories
            suggested_aspects: Optional list of approved aspects (frozen aspect list)
            
        Returns:
            Processing results
        """
        if file_type == 'json':
            logger.info("Processing JSON data")

            if doc_type == 0:  # Feedback processing
                # Extract comments from JSON data before processing
                extracted_text = self._extract_text_from_data(data, file_type)
                result = await self.process_feedback(extracted_text, suggested_aspects=suggested_aspects)
                return result
            
            # User Stories
            if doc_type == 1:
                return {'status': 'success', 'details': 'User story processing not implemented'}

        elif file_type == 'csv':
            logger.info("Processing CSV data")
            # Extract comments from CSV data before processing
            if doc_type == 0:  # Feedback processing
                extracted_text = self._extract_text_from_data(data, file_type)
                result = await self.process_feedback(extracted_text, suggested_aspects=suggested_aspects)
                return result
            # Simulate async processing for other doc types
            await asyncio.sleep(1)
            return {
                'status': 'success', 
                'details': 'CSV data processed asynchronously'
            }
        
        return {'status': 'error', 'details': 'Unknown file type'}
    
    def _extract_text_from_data(self, data, file_type):
        """
        Extract text/comments from uploaded data structure.
        
        Args:
            data: The uploaded data (dict, list, or list of dicts)
            file_type: 'json' or 'csv'
            
        Returns:
            String of extracted text/comments joined together
        """
        comments = []
        
        if file_type == 'json':
            if isinstance(data, list):
                # If data is a list of strings, treat as comments
                comments = [str(item) for item in data if item]
            elif isinstance(data, dict):
                # If data has a comments field
                if 'comments' in data and isinstance(data['comments'], list):
                    comments = [str(comment) for comment in data['comments'] if comment]
                # If data has feedback field
                elif 'feedback' in data and isinstance(data['feedback'], list):
                    comments = [str(feedback) for feedback in data['feedback'] if feedback]
                # If data has reviews field
                elif 'reviews' in data and isinstance(data['reviews'], list):
                    comments = [str(review) for review in data['reviews'] if review]
                # If it's a single comment object with text field
                elif 'text' in data:
                    comments = [str(data['text'])]
                else:
                    # Fallback: try to extract any string values
                    logger.warning(f"Unknown JSON structure, attempting to extract text fields. Keys: {list(data.keys())}")
                    for key, value in data.items():
                        if isinstance(value, str) and len(value) > 10:
                            comments.append(value)
                        elif isinstance(value, list):
                            comments.extend([str(item) for item in value if item])
        
        elif file_type == 'csv':
            if isinstance(data, list) and len(data) > 0:
                # Look for common comment column names
                comment_columns = ['comment', 'comments', 'feedback', 'review', 'reviews', 'text', 'content', 'message']
                first_row = data[0] if isinstance(data[0], dict) else None
                
                if first_row:
                    # Find the comment column
                    comment_column = None
                    for col in comment_columns:
                        if col in first_row:
                            comment_column = col
                            break
                    
                    if comment_column:
                        comments = [str(row[comment_column]) for row in data if isinstance(row, dict) and row.get(comment_column)]
                    else:
                        # Fallback: use the first column
                        first_col = list(first_row.keys())[0] if first_row else None
                        if first_col:
                            comments = [str(row[first_col]) for row in data if isinstance(row, dict) and row.get(first_col)]
        
        # Join comments into a single text string
        if comments:
            extracted_text = "\n".join(comments)
            logger.info(f"Extracted {len(comments)} comments/text items from {file_type} data")
            return extracted_text
        else:
            # Fallback: convert entire data to string if no comments found
            logger.warning(f"No comments extracted from {file_type} data, using full data as string")
            return str(data)

    def _parse_llm_extractions(self, comments_analysis):
        """
        Parse LLM extraction results into a unified list of comment extractions.
        
        The new LLM format returns an array of comment extractions per chunk.
        This method combines all chunks and returns a flat list.
        Only processes validated batches (skips error results).
        
        Args:
            comments_analysis: List of LLM responses (one per chunk), each containing
                              an array of comment extractions or error dict
                              
        Returns:
            Flat list of all comment extractions across all chunks, or None if legacy format detected
        """
        all_extractions = []
        
        def safe_parse(item):
            """Safely parse JSON string or return dict as-is."""
            if isinstance(item, dict):
                return item
            try:
                return json.loads(item)
            except Exception:
                return {}
        
        for chunk_result in comments_analysis:
            parsed = safe_parse(chunk_result)
            
            # Skip error results (they're already in dict format with error field)
            if isinstance(parsed, dict) and parsed.get('error'):
                logger.warning(f"Skipping chunk with error: {parsed.get('error')}")
                continue
            
            # Handle new format: array of comment extractions
            if isinstance(parsed, list):
                all_extractions.extend(parsed)
            # Handle legacy format: object with counts/summaries (backward compatibility)
            elif isinstance(parsed, dict):
                # Try to extract comments if in legacy format
                # This maintains backward compatibility
                if 'counts' in parsed or 'sentiment_summary' in parsed:
                    # Legacy format detected - return None to trigger fallback
                    logger.warning("Legacy LLM format detected. LLM should return array of extractions. Falling back to legacy normalization.")
                    return None
                else:
                    # Maybe it's a single extraction object wrapped
                    all_extractions.append(parsed)
        
        return all_extractions if all_extractions else None

    def _normalize_analysis_results_legacy(self, comments_analysis):
        """
        Legacy normalization method for backward compatibility.
        Used when LLM returns old format with counts/summaries.
        
        This method should eventually be deprecated once all LLM responses
        are migrated to the new extraction format.
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
            # Skip error results
            if isinstance(item, dict) and item.get('error'):
                continue
                
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
            self._process_features_legacy(data, feature_map)
            
            # Process keywords
            self._process_keywords_legacy(data, pos_kw_scores, pos_kw_counts, neg_kw_scores, neg_kw_counts)

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

    def _process_features_legacy(self, data, feature_map):
        """Process and merge features from analysis data (legacy method)."""
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

    def _process_keywords_legacy(self, data, pos_kw_scores, pos_kw_counts, neg_kw_scores, neg_kw_counts):
        """Process and aggregate keywords from analysis data (legacy method)."""
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
