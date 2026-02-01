from celery import shared_task
import asyncio
from asgiref.sync import async_to_sync
from .processing_service import get_processing_service
from .analysis_service import get_analysis_service
from .schema_validator import get_validation_service
import logging
import json
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing background tasks."""
    
    def __init__(self):
        self.processing_service = get_processing_service()
        self.validation_service = get_validation_service()
    
    def process_feedback_background(self, comments, company_name, user_id_str, project_id, suggested_aspects=None):
        """
        Process user feedback using LLM with proper chunking, normalize, and save.
        This is the main business logic for background feedback processing.
        
        CRITICAL: Uses token-based chunking (max input tokens per batch) to avoid token limits.
        Comments are never split; if one would exceed the limit, it goes to the next batch.
        Uses LOCKED SEMANTIC SCHEMA - all LLM outputs are validated against exact schema.
        
        Args:
            comments: List of comment strings
            company_name: Optional company name
            user_id_str: User ID string
            project_id: Project ID string
            suggested_aspects: Optional list of frozen aspects (if None, will generate)
        """
        logger.info(f"📈 Background task started: feedback analysis for project {project_id}")
        logger.info(f"🔍 DEBUG: Input parameters - comments count: {len(comments)}, user: {user_id_str}, project: {project_id}")
        logger.info(f"🔍 DEBUG: First few comments: {comments[:3] if len(comments) > 3 else comments}")
        
        try:
            # 1. Generate aspect suggestions if not provided (Step 2 of workflow)
            if suggested_aspects is None:
                logger.info("No suggested_aspects provided - generating aspect suggestions")
                from .aspect_suggestion_service import get_aspect_suggestion_service
                aspect_service = get_aspect_suggestion_service()
                aspect_suggestions_result = async_to_sync(aspect_service.suggest_aspects)(comments)
                suggested_aspects = aspect_suggestions_result.get('suggested_aspects', [])
                logger.info(f"✅ Generated {len(suggested_aspects)} aspect suggestions: {suggested_aspects}")
            else:
                logger.info(f"🔒 Using provided frozen aspect list: {suggested_aspects}")
            
            # 2. Process with token-based batching (pass comments list directly to avoid newline-split issues)
            logger.info(f"Processing {len(comments)} comments with token-based batching")
            comments_analysis = async_to_sync(self.processing_service.process_chunks)(
                analysis_type=0,  # Sentiment analysis
                company_name=company_name,
                suggested_aspects=suggested_aspects,  # Pass frozen aspect list
                comments=comments,  # Pass list directly — batched by token count
            )
            
            # 4. Validate and parse LLM extractions from all chunks (uses locked schema)
            logger.info(f"🔍 STEP 4: Parsing and combining validated results from {len(comments_analysis)} batches...")
            extracted_comments = self._validate_and_parse_chunks(comments_analysis, comments)
            logger.info(f"🔍 STEP 4: Extracted {len(extracted_comments)} total comments from all batches")
            
            if not extracted_comments:
                details = self._format_validation_failure_details(comments_analysis, comments)
                err_suffix = f" First errors: {details[:500]}" if details else " Check server logs for details."
                raise ValueError(
                    "Failed to extract valid comment data from LLM responses. "
                    "All batches failed validation."
                    + err_suffix
                )
            
            # 5. Validate batch integrity
            self._validate_batch_integrity(extracted_comments, comments)
            
            # 6. Generate unique run_id for this processing run (for tracking/auditing, not persistence)
            run_id = str(uuid.uuid4())
            logger.info(f"Generated run_id {run_id} for processing {len(comments)} comments")
            
            # 7. Aggregate using aggregation service (works directly from extracted_comments in memory)
            from .aggregation_service import get_aggregation_service
            aggregation_service = get_aggregation_service()
            normalized = aggregation_service.aggregate_comment_extractions(extracted_comments)
            
            # Ensure counts match actual comment count (system of record)
            normalized['counts']['total'] = len(comments)
            
            # 9. Save aggregated analysis to database with original comments included
            insight_id = str(uuid.uuid4())
            insight_data = {
                'id': f'insight_{insight_id}',
                'type': 'insight',
                'projectId': project_id,  # Use projectId for consistency
                'userId': user_id_str,    # Use userId for consistency
                'analysis_type': 'sentiment_analysis',
                'analysis_date': datetime.now().isoformat(),
                'createdAt': datetime.now().isoformat(),
                'run_id': run_id,  # Unique identifier for this analysis run
                'result': normalized,
                'status': 'complete',
                # Store original comments for retrieval (NEVER overwrite)
                'original_comments': comments,
                'feedback': comments,  # Alternative field name
                'company_name': company_name,
                'comments_count': len(comments)
            }
            
            logger.info(f"🔍 DEBUG: About to save insight_data with keys: {list(insight_data.keys())}")
            logger.info(f"🔍 DEBUG: insight_data id: {insight_data['id']}")
            logger.info(f"🔍 DEBUG: insight_data projectId: {insight_data['projectId']}")
            logger.info(f"🔍 DEBUG: insight_data userId: {insight_data['userId']}")
            logger.info(f"🔍 DEBUG: insight_data original_comments count: {len(insight_data['original_comments'])}")
            logger.info(f"🔍 DEBUG: insight_data feedback count: {len(insight_data['feedback'])}")
            
            # Save using analysis service
            analysis_service = get_analysis_service()
            saved_result = analysis_service.save_analysis_data(insight_data)
            
            if saved_result:
                logger.info(f"✅ Analysis saved to Cosmos DB successfully with ID: {saved_result.get('id')}")
                logger.info(f"🔍 DEBUG: Saved result keys: {list(saved_result.keys()) if saved_result else 'None'}")
                try:
                    analysis_service.update_project_last_analysis(project_id, insight_data["id"])
                except Exception as e:
                    logger.warning(f"Could not update project last_analysis: {e}")
            else:
                logger.error(f"Failed to save analysis data to Cosmos DB")
            
            logger.info(f"Analysis saved to Cosmos DB for background task with {len(comments)} comments")
            
            # Return minimal payload to avoid Celery result backend serialization issues
            # (large normalized result can cause task to be marked FAILURE after save).
            # Frontend fetches latest analysis by project_id on SUCCESS.
            return {
                "insight_id": insight_data["id"],
                "project_id": project_id,
                "status": "complete",
            }

        except Exception as e:
            logger.error(f"Error in feedback analysis task: {str(e)}", exc_info=True)
            raise
    
    def _format_validation_failure_details(self, chunk_results, original_comments):
        """Build a short summary of validation failures from chunk error dicts."""
        lines = []
        for chunk_idx, r in enumerate(chunk_results):
            if not isinstance(r, dict):
                continue
            err_msg = r.get("error")
            if not err_msg:
                continue
            lines.append(f"Chunk {chunk_idx}: {err_msg}")
            for ve in (r.get("validation_errors") or [])[:5]:
                lines.append(f"  - {ve}")
        return "\n".join(lines) if lines else ""

    def _validate_and_parse_chunks(self, chunk_results, original_comments):
        """
        Parse validated LLM outputs from chunks.
        
        NOTE: Validation is already done in processing_service.process_chunks().
        This method only parses and combines validated results.
        
        Args:
            chunk_results: List of validated LLM responses (one per chunk, already validated)
            original_comments: Original comments list for reference
            
        Returns:
            List of validated comment extractions matching locked schema
        """
        all_extractions = []
        error_summaries = []
        running_total = 0
        
        def safe_parse(item):
            """Safely parse JSON string or return dict as-is."""
            if isinstance(item, dict):
                return item
            try:
                return json.loads(item)
            except Exception:
                return {}
        
        for chunk_idx, chunk_result in enumerate(chunk_results):
            logger.debug(f"🔍 Processing chunk {chunk_idx} result...")
            
            # Check for error results (already validated and rejected in processing_service)
            if isinstance(chunk_result, dict):
                if chunk_result.get('error'):
                    error_msg = chunk_result.get('error', 'Unknown error')
                    validation_errors = chunk_result.get('validation_errors', [])
                    error_summaries.append(f"Chunk {chunk_idx}: {error_msg}")
                    if validation_errors:
                        error_summaries.extend([f"  - {err}" for err in validation_errors[:3]])  # First 3 errors
                    logger.warning(f"⚠️ Chunk {chunk_idx} has error, skipping: {error_msg}")
                    continue
                # Check if it's an error dict from retry service
                if 'processed' in chunk_result and not chunk_result.get('processed', False):
                    error_msg = chunk_result.get('error', 'Unknown processing error')
                    error_summaries.append(f"Chunk {chunk_idx}: Processing failed - {error_msg}")
                    logger.warning(f"⚠️ Chunk {chunk_idx} processing failed, skipping: {error_msg}")
                    continue
            
            logger.debug(f"🔍 Chunk {chunk_idx}: Parsing result (type: {type(chunk_result).__name__})...")
            parsed = safe_parse(chunk_result)
            logger.debug(f"🔍 Chunk {chunk_idx}: Parsed type: {type(parsed).__name__}")
            
            # Handle validated array of extractions
            if isinstance(parsed, list):
                n = len(parsed)
                running_total += n
                logger.info(f"✅ Chunk {chunk_idx}: Found {n} validated extractions (running total: {running_total})")
                all_extractions.extend(parsed)
            # Handle legacy format (should not happen if validation worked)
            elif isinstance(parsed, dict) and ('counts' not in parsed and 'sentiment_summary' not in parsed):
                running_total += 1
                logger.info(f"✅ Chunk {chunk_idx}: Found 1 legacy format extraction (running total: {running_total})")
                all_extractions.append(parsed)
            else:
                logger.warning(f"⚠️ Chunk {chunk_idx}: Unexpected format (type: {type(parsed).__name__}), skipping")
        
        # Log detailed error summary if no extractions found
        if not all_extractions and error_summaries:
            logger.error("=" * 80)
            logger.error(f"❌ NO VALID EXTRACTIONS FOUND - All {len(chunk_results)} batches failed validation")
            logger.error("=" * 80)
            for error_summary in error_summaries:
                logger.error(error_summary)
            logger.error("=" * 80)
        
        logger.info(
            f"✅ Parsed {len(all_extractions)} validated extractions from {len(chunk_results)} batches "
            f"({len(error_summaries)} batches had errors). Expected original_comments count: {len(original_comments)}"
        )
        
        return all_extractions
    
    def _validate_batch_integrity(self, extracted_comments, original_comments):
        """
        Validate that all input comments have corresponding outputs.
        
        This is critical for ensuring no comments are silently dropped.
        
        Args:
            extracted_comments: List of extracted comment dictionaries from LLM
            original_comments: Original list of input comments
        """
        if not extracted_comments:
            logger.warning("No extracted comments found - cannot validate integrity")
            return
        
        extracted_count = len(extracted_comments)
        original_count = len(original_comments)
        
        if extracted_count != original_count:
            diff = extracted_count - original_count
            logger.error(
                f"BATCH INTEGRITY VIOLATION: Expected {original_count} extracted comments, "
                f"got {extracted_count}. {'Extra' if diff > 0 else 'Missing'} {abs(diff)} comments."
            )
            raise ValueError(
                f"Batch integrity failed: expected {original_count} extractions, got {extracted_count}. "
                "Some batches may have failed validation or results were misattributed. Check logs."
            )
        logger.info(f"✅ Batch integrity check passed: {extracted_count} comments extracted from {original_count} input comments")
    
    def _normalize_analysis_result_legacy_from_chunks(self, chunk_results, comments):
        """
        Legacy normalization for chunked results (backward compatibility).
        Aggregates legacy format results from multiple chunks.
        
        NOTE: This should only be used for backward compatibility.
        New code should use locked schema validation.
        """
        total_count = 0
        total_pos = 0
        total_neg = 0
        total_neu = 0
        all_features = []
        all_pos_keywords = []
        all_neg_keywords = []
        
        def safe_parse(item):
            if isinstance(item, dict):
                return item
            try:
                return json.loads(item)
            except Exception:
                return {}
        
        # Aggregate across chunks
        for chunk_result in chunk_results:
            if isinstance(chunk_result, dict) and chunk_result.get('error'):
                continue
            
            parsed = safe_parse(chunk_result)
            if not isinstance(parsed, dict):
                continue
            
            counts = parsed.get('counts', {})
            total_count += counts.get('total', 0)
            total_pos += counts.get('positive', 0)
            total_neg += counts.get('negative', 0)
            total_neu += counts.get('neutral', 0)
            
            # Collect features
            features = parsed.get('feature_asba') or parsed.get('featureasba') or []
            all_features.extend(features)
            
            # Collect keywords
            all_pos_keywords.extend(parsed.get('positive_keywords', []) or parsed.get('positivekeywords', []))
            all_neg_keywords.extend(parsed.get('negative_keywords', []) or parsed.get('negativekeywords', []))
        
        # Use the same normalization logic as single-result method
        return self._normalize_analysis_result_legacy({
            'counts': {
                'total': total_count or len(comments),
                'positive': total_pos,
                'negative': total_neg,
                'neutral': total_neu,
            },
            'sentiment_summary': {
                'positive': (total_pos / total_count * 100) if total_count > 0 else 0,
                'negative': (total_neg / total_count * 100) if total_count > 0 else 0,
                'neutral': (total_neu / total_count * 100) if total_count > 0 else 0,
            },
            'feature_asba': all_features,
            'positive_keywords': all_pos_keywords,
            'negative_keywords': all_neg_keywords,
        }, comments)
    
    def _normalize_analysis_result_legacy(self, result, comments):
        """
        Legacy normalization method for backward compatibility.
        Used when LLM returns old format with counts/summaries.
        
        NOTE: This should only be used for backward compatibility.
        New code should use locked schema validation.
        """
        try:
            parsed = json.loads(result) if isinstance(result, str) else (result or {})
        except Exception:
            parsed = {}

        sentiments = parsed.get('sentimentsummary') or parsed.get('sentiment_summary') or {}
        counts = parsed.get('counts') or {}
        features_input = parsed.get('feature_asba') or parsed.get('featureasba') or []
        pos_keys = parsed.get('positive_keywords') or parsed.get('positivekeywords') or []
        neg_keys = parsed.get('negative_keywords') or parsed.get('negativekeywords') or []

        def to_num(v):
            try: 
                return float(v)
            except:
                try: 
                    return int(v)
                except: 
                    return 0

        features_norm = []
        for f in features_input:
            if not isinstance(f, dict): 
                continue
            name = f.get('feature') or f.get('name')
            if not name: 
                continue
            sent = f.get('sentiment') or {}
            features_norm.append({
                'name': name,
                'description': f.get('description') or '',
                'sentiment': {
                    'positive': to_num(sent.get('positive')),
                    'negative': to_num(sent.get('negative')),
                    'neutral': to_num(sent.get('neutral')),
                },
                'keywords': f.get('keywords') or [],
                'comment_count': to_num(f.get('comment_count') or f.get('commentcount') or 0)
            })

        return {
            'overall': {
                'positive': to_num(sentiments.get('positive')),
                'negative': to_num(sentiments.get('negative')),
                'neutral': to_num(sentiments.get('neutral')),
            },
            'counts': {
                'total': len(comments),  # Use actual comments count instead of LLM reported count
                'positive': to_num(counts.get('positive')),
                'negative': to_num(counts.get('negative')),
                'neutral': to_num(counts.get('neutral')),
            },
            'features': features_norm,
            'positive_keywords': pos_keys,
            'negative_keywords': neg_keys,
        }


# Global service instance
_task_service = None

def get_task_service():
    """Get the global task service instance."""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service


# Celery task wrapper - this stays at module level for Celery discovery
@shared_task(name="feedback_analysis.tasks.process_feedback_task")
def process_feedback_task(comments, company_name, user_id_str, project_id, suggested_aspects=None):
    """
    Celery background task wrapper for feedback processing.
    Delegates to TaskService for actual business logic.
    
    Args:
        comments: List of comment strings
        company_name: Optional company name
        user_id_str: User ID string
        project_id: Project ID string
        suggested_aspects: Optional list of frozen aspects (if None, will generate in background task)
    """
    task_service = get_task_service()
    return task_service.process_feedback_background(comments, company_name, user_id_str, project_id, suggested_aspects)
