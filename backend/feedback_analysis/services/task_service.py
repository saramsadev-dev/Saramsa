from celery import shared_task, current_task
from typing import List
from .analysis_service import get_analysis_service
from .schema_validator import get_validation_service
from .taxonomy_service import get_taxonomy_service
from .pipeline_health import PipelineHealth
from apis.infrastructure.cache_service import get_cache_service
import logging
import json
import uuid
import os
from datetime import datetime, timezone
from ..schemas.analysis_data_schema import validate_analysis_data

logger = logging.getLogger(__name__)



class TaskService:
    """Service for managing background tasks."""
    
    def __init__(self):
        self.validation_service = get_validation_service()
        self.local_processing_service = None
    
    def process_feedback_background(self, comments, company_name, user_id_str, project_id, analysis_id, task_id=None, suggested_aspects=None):
        """Process user feedback using the local ML pipeline."""
        logger.info(f"📈 Background task started: feedback analysis for project {project_id}")
        logger.info(f"🔍 Input: {len(comments)} comments, user: {user_id_str}, project: {project_id}")
        max_comments = int(os.getenv("MAX_COMMENTS_PER_ANALYSIS", "50000"))
        if len(comments) > max_comments:
            health.mark_failed("max_comments_per_analysis exceeded")
            if task_id:
                cache.set(f"analysis_failed:{analysis_id}", True, ttl=86400)
                cache.set(f"pipeline_health:{task_id}", health.to_dict(), ttl=3600)
            raise ValueError(f"Too many comments for one analysis (max {max_comments})")
        health = PipelineHealth(analysis_id=analysis_id, task_id=task_id)
        cache = get_cache_service()
        if task_id:
            cache.set(f"pipeline_health:{task_id}", health.to_dict(), ttl=3600)

        try:
            health.start_stage("local_pipeline")
            result = self._process_with_local_pipeline(
                comments, company_name, user_id_str, project_id, analysis_id, suggested_aspects
            )
            health.end_stage("local_pipeline")

            # Record narration cost if available
            try:
                from .narration_service import get_narration_service
                narration_status = getattr(get_narration_service(), "last_status", None)
                if narration_status and narration_status != "OK":
                    logger.warning(f"Narration status: {narration_status}")
            except Exception:
                pass

            health.mark_complete()
            try:
                narration_service = get_narration_service()
                if getattr(narration_service, "last_cost", None):
                    health.cost = narration_service.last_cost
            except Exception:
                pass
            result["pipeline_health"] = health.to_dict()
            cache.set(f"pipeline_health:{analysis_id}", health.to_dict(), ttl=3600)
            if task_id:
                cache.set(f"pipeline_health:{task_id}", health.to_dict(), ttl=3600)
            return result
                
        except Exception as e:
            logger.error(f"Error in feedback analysis task: {str(e)}", exc_info=True)
            health.mark_failed(str(e))
            cache.set(f"pipeline_health:{analysis_id}", health.to_dict(), ttl=3600)
            if task_id:
                cache.set(f"pipeline_health:{task_id}", health.to_dict(), ttl=3600)
            cache.set(f"analysis_failed:{analysis_id}", True, ttl=86400)
            raise
    
    def _process_with_local_pipeline(self, comments, company_name, user_id_str, project_id, analysis_id, suggested_aspects=None):
        """
        Process feedback using the local ML pipeline.
        
        This method uses local models for NLI aspect classification and sentiment analysis,
        with a single GPT call for final synthesis.
        """
        logger.info("🤖 Processing with Local ML Pipeline")
        
        # Lazy load the local processing service
        if self.local_processing_service is None:
            try:
                from .local_processing_service import LocalProcessingService
                self.local_processing_service = LocalProcessingService()
                logger.info("✅ LocalProcessingService initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize LocalProcessingService: {e}", exc_info=True)
                raise RuntimeError("Local ML pipeline initialization failed; fallback is disabled.") from e
        
        # 1. Resolve aspect taxonomy (cached → last analysis → GPT suggestion)
        taxonomy, resolved_aspects = self._resolve_taxonomy(comments, project_id, suggested_aspects)
        
        # 2. Process through local ML pipeline
        run_id = str(uuid.uuid4())
        logger.info(f"🚀 Processing {len(comments)} comments through local ML pipeline (run: {run_id})")

        # Build cooperative cancellation checker (Windows solo pool ignores SIGTERM)
        is_cancelled = self._build_cancel_checker(analysis_id)

        pipeline_result = self.local_processing_service.process_comments(
            comments=comments,
            aspects=resolved_aspects,
            company_name=company_name or "Company",
            run_id=run_id,
            is_cancelled=is_cancelled,
            user_id=user_id_str,
        )
        
        logger.info(f"✅ Local ML pipeline completed in {pipeline_result.processing_time:.2f}s")
        logger.info(f"📊 Results: {len(pipeline_result.features)} features, {len(pipeline_result.insights)} insights, {len(pipeline_result.work_items)} work items")
        
        # 3. Convert pipeline result to expected format
        normalized_result = self._convert_pipeline_result_to_schema(pipeline_result, comments)
        try:
            validate_analysis_data(normalized_result)
        except Exception as e:
            logger.error(f"Invalid analysisData schema (local pipeline): {e}")
            raise ValueError(f"Invalid analysisData schema (local pipeline): {e}")
        
        # 4. Save to database
        insight_id = analysis_id
        default_name = f"Run {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        insight_data = {
            'id': f'insight_{insight_id}',
            'type': 'insight',
            'projectId': project_id,
            'userId': user_id_str,
            'analysis_id': analysis_id,
            'taxonomy_id': taxonomy.get('taxonomy_id') if taxonomy else None,
            'taxonomy_version': taxonomy.get('version') if taxonomy else None,
            'analysis_type': 'sentiment_analysis_local_ml',
            'analysis_date': datetime.now().isoformat(),
            'createdAt': datetime.now().isoformat(),
            'run_id': run_id,
            'analysisData': normalized_result,
            'status': 'complete',
            'name': default_name,
            'original_comments': comments,
            'feedback': comments,
            'company_name': company_name,
            'comments_count': len(comments),
            'processing_method': 'local_ml_pipeline',
            'model_info': pipeline_result.model_info,
            'processing_time': pipeline_result.processing_time,
            'insights': pipeline_result.insights,
            'pipeline_work_items': pipeline_result.work_items
        }
        
        # Save using analysis service
        analysis_service = get_analysis_service()
        saved_result = analysis_service.save_analysis_data(insight_data)
        
        if saved_result:
            logger.info(f"✅ Local ML analysis saved to PostgreSQL with ID: {saved_result.get('id')}")
            try:
                analysis_service.update_project_last_analysis(project_id, insight_data["id"])
            except Exception as e:
                logger.warning(f"Could not update project last_analysis: {e}")
        else:
            logger.error(f"❌ Failed to save local ML analysis data to PostgreSQL")
        
        self._record_taxonomy_health(taxonomy, project_id, self._compute_health_metrics_local(pipeline_result))

        return {
            "insight_id": insight_data["id"],
            "project_id": project_id,
            "analysis_id": analysis_id,
            "status": "complete",
            "processing_method": "local_ml_pipeline",
            "processing_time": pipeline_result.processing_time
        }
    
    def _build_cancel_checker(self, analysis_id: str):
        """
        Return a callable that checks Redis for a cancellation flag.

        The celery_ops cancel endpoint sets ``saramsa:cancelled:<task_id>``
        in Redis.  Because we may not know the Celery task_id at this level
        we also check by analysis_id.  The callable is cheap (single Redis
        GET) and is called between NLI batches for cooperative cancellation
        on Windows where SIGTERM is ignored.
        """
        cache = get_cache_service()

        # Get the celery task id if available
        from celery import current_task
        celery_task_id = getattr(current_task.request, "id", None)

        def _is_cancelled() -> bool:
            try:
                if celery_task_id:
                    val = cache.get(f"saramsa:cancelled:{celery_task_id}")
                    if val:
                        logger.info(f"Task {celery_task_id} cancelled via Redis flag")
                        return True
                return False
            except Exception as exc:
                raise RuntimeError("Cancellation checker failed while reading Redis cancellation flag.") from exc

        return _is_cancelled

    def _resolve_taxonomy(self, comments, project_id, suggested_aspects=None):
        """
        Resolve project-owned taxonomy (Phase-1).

        This replaces reuse-from-last-analysis with explicit taxonomy ownership.
        """
        taxonomy_service = get_taxonomy_service()

        # If suggested_aspects are provided (e.g., upload bootstrap), avoid extra GPT calls.
        if suggested_aspects is not None:
            active = taxonomy_service.get_active_taxonomy(project_id, comments=None)
            if not active:
                active = taxonomy_service.create_initial_taxonomy(
                    project_id, suggested_aspects, source="gpt"
                )
                return active, suggested_aspects
            aspects = [a.get("label") or a.get("key") for a in active.get("aspects", []) if isinstance(a, dict)]
            return active, [a for a in aspects if a]

        taxonomy = taxonomy_service.get_active_taxonomy(project_id, comments=comments)
        aspects = [a.get("label") or a.get("key") for a in taxonomy.get("aspects", []) if isinstance(a, dict)]
        return taxonomy, [a for a in aspects if a]

    def _record_taxonomy_health(self, taxonomy, project_id, metrics):
        """Record taxonomy health snapshot without changing taxonomy content."""
        if not taxonomy or not metrics:
            return
        metrics = metrics.copy()
        metrics["taxonomy_age_days"] = self._taxonomy_age_days(taxonomy)
        taxonomy_service = get_taxonomy_service()
        taxonomy_service.record_health_snapshot(project_id, taxonomy, metrics)

    def _compute_health_metrics_local(self, pipeline_result):
        """Compute taxonomy health metrics from local ML pipeline output."""
        try:
            matches = pipeline_result.matches
            total = len(matches)
            if total == 0:
                return None
            aspects_total = 0
            confidence_scores = []
            for match in matches:
                aspects_total += len([a for a in match.matched_aspects if a != "UNMAPPED"])
                scores = match.comment_sentiment.raw_scores or {}
                if scores:
                    confidence_scores.append(max(scores.values()))
            avg_aspects = aspects_total / total if total else 0.0
            confidence_p95 = self._percentile(confidence_scores, 0.95)
            return {
                "last_unmapped_rate": float(pipeline_result.aggregated_stats.unmapped_percentage),
                "last_avg_aspects_per_comment": avg_aspects,
                "last_confidence_p95": confidence_p95,
            }
        except Exception as e:
            logger.warning(f"Failed to compute local taxonomy health metrics: {e}")
            return None

    @staticmethod
    def _percentile(values, p):
        if not values:
            return None
        values = sorted(values)
        if len(values) == 1:
            return values[0]
        idx = int(round((len(values) - 1) * p))
        return values[max(0, min(idx, len(values) - 1))]

    @staticmethod
    def _taxonomy_age_days(taxonomy):
        created_at = taxonomy.get("created_at") or taxonomy.get("createdAt")
        if not created_at:
            return 0.0
        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except Exception:
            return 0.0
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - created_dt).days

    def _convert_pipeline_result_to_schema(self, pipeline_result, original_comments):
        """
        Convert LocalProcessingService result to the expected frontend schema.
        
        This ensures compatibility with existing frontend components.
        """
        # Convert features to expected format
        features_normalized = []
        for feature in pipeline_result.features:
            features_normalized.append({
                'name': feature['feature'],
                'description': feature['description'],
                'sentiment': feature['sentiment'],
                'keywords': feature['keywords'],
                'comment_count': feature['comment_count'],
                'sample_comments': feature.get('sample_comments')
            })
        
        # Calculate overall sentiment from aggregated stats
        overall_sentiment = pipeline_result.aggregated_stats.overall_sentiment
        
        # Count sentiment per comment (not per aspect-match, to avoid inflation)
        total_comments = len(original_comments)
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        for match in pipeline_result.matches:
            sentiment = match.comment_sentiment.sentiment.upper()
            if sentiment == 'POSITIVE':
                positive_count += 1
            elif sentiment == 'NEGATIVE':
                negative_count += 1
            else:
                neutral_count += 1
        
        # Extract keywords from features
        positive_keywords = []
        negative_keywords = []
        
        for feature in pipeline_result.features:
            sentiment = feature['sentiment']
            keywords = feature['keywords']
            
            # Classify keywords based on dominant sentiment
            pos_pct = sentiment.get('positive', 0)
            neg_pct = sentiment.get('negative', 0)
            
            if pos_pct > neg_pct and pos_pct > 40:
                positive_keywords.extend(keywords[:3])
            elif neg_pct > pos_pct and neg_pct > 40:
                negative_keywords.extend(keywords[:3])
        
        # Remove duplicates and limit
        positive_keywords = list(dict.fromkeys(positive_keywords))[:10]
        negative_keywords = list(dict.fromkeys(negative_keywords))[:10]
        
        return {
            'overall': {
                'positive': overall_sentiment.get('positive', 0),
                'negative': overall_sentiment.get('negative', 0),
                'neutral': overall_sentiment.get('neutral', 0),
            },
            'counts': {
                'total': total_comments,
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count,
            },
            'features': features_normalized,
            'positive_keywords': positive_keywords,
            'negative_keywords': negative_keywords,
            # Additional metadata from local pipeline
            'pipeline_metadata': {
                'processing_time': pipeline_result.processing_time,
                'model_info': pipeline_result.model_info,
                'unmapped_percentage': pipeline_result.aggregated_stats.unmapped_percentage,
                'confidence_distribution': dict(pipeline_result.aggregated_stats.confidence_distribution)
            }
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
def process_feedback_task(comments, company_name, user_id_str, project_id, analysis_id, suggested_aspects=None):
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
    task_id = getattr(current_task.request, "id", None)
    return task_service.process_feedback_background(comments, company_name, user_id_str, project_id, analysis_id, task_id, suggested_aspects)
