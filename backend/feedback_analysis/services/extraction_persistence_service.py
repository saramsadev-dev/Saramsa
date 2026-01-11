"""
Extraction Persistence Service

Persists per-comment semantic outputs as the system of record.

CRITICAL RULES:
- Never overwrite raw comments
- Never overwrite previous runs silently
- Treat as derived, replayable data
- This is what aggregation will read from later

Each extraction is stored with:
- comment_id (tied to original comment)
- run_id (unique ID per processing run)
- schema_version (semantic schema version)
- timestamp (when extraction was saved)
- All semantic fields from CommentExtraction
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from feedback_analysis.schemas import SCHEMA_VERSION

logger = logging.getLogger(__name__)


class ExtractionPersistenceService:
    """Service for persisting per-comment semantic extractions."""
    
    def __init__(self):
        from apis.infrastructure.cosmos_service import cosmos_service
        self.cosmos_service = cosmos_service
        self.schema_version = SCHEMA_VERSION
    
    def save_extractions(self, extractions: List[Dict[str, Any]], run_id: str, 
                        project_id: str, user_id: str, 
                        original_comments: List[str]) -> bool:
        """
        Persist per-comment semantic extractions.
        
        Each extraction is stored as a separate row with:
        - comment_id (tied to original comment)
        - run_id (unique ID per processing run)
        - schema_version (semantic schema version)
        - timestamp (when extraction was saved)
        - All semantic fields from CommentExtraction
        
        Args:
            extractions: List of validated comment extractions (CommentExtraction dicts)
            run_id: Unique identifier for this processing run
            project_id: Project ID
            user_id: User ID
            original_comments: Original comments list (for reference, not overwritten)
            
        Returns:
            True if all extractions saved successfully, False otherwise
        """
        if not extractions:
            logger.warning("No extractions to persist")
            return False
        
        timestamp = datetime.now(timezone.utc).isoformat()
        saved_count = 0
        failed_count = 0
        
        for extraction in extractions:
            try:
                # Extract comment_id for document ID
                comment_id = extraction.get("comment_id")
                if comment_id is None:
                    logger.error(f"Extraction missing comment_id, skipping: {extraction}")
                    failed_count += 1
                    continue
                
                # Create document ID: run_id + comment_id ensures uniqueness per run
                doc_id = f"extraction_{run_id}_{comment_id}"
                
                # Build extraction document
                extraction_doc = {
                    "id": doc_id,
                    "type": "comment_extraction",
                    "run_id": run_id,
                    "comment_id": comment_id,
                    "project_id": project_id,
                    "user_id": user_id,
                    "schema_version": self.schema_version,
                    "timestamp": timestamp,
                    "created_at": timestamp,
                    # Semantic fields from CommentExtraction
                    "sentiment": extraction.get("sentiment"),
                    "confidence": extraction.get("confidence"),
                    "intent_type": extraction.get("intent_type"),
                    "intent_phrase": extraction.get("intent_phrase"),
                    "keywords": extraction.get("keywords", []),
                    "aspects": extraction.get("aspects", []),
                    # Metadata
                    "metadata": {
                        "total_comments_in_run": len(extractions),
                        "extraction_index": comment_id,  # 0-based index
                    }
                }
                
                # Save to Cosmos DB (comment_extractions container)
                saved = self.cosmos_service.save_comment_extraction(extraction_doc)
                
                if saved:
                    saved_count += 1
                else:
                    failed_count += 1
                    logger.error(f"Failed to save extraction for comment_id {comment_id}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error saving extraction {extraction.get('comment_id')}: {e}", exc_info=True)
        
        # Log summary
        if failed_count == 0:
            logger.info(
                f"✅ Persisted {saved_count} comment extractions for run_id {run_id} "
                f"(project_id: {project_id}, schema_version: {self.schema_version})"
            )
        else:
            logger.warning(
                f"⚠️ Persisted {saved_count}/{len(extractions)} comment extractions for run_id {run_id} "
                f"({failed_count} failed)"
            )
        
        return failed_count == 0
    
    def get_extractions_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all extractions for a specific run_id.
        
        This is what aggregation services will read from.
        
        Args:
            run_id: Run ID to retrieve extractions for
            
        Returns:
            List of extraction documents
        """
        return self.cosmos_service.get_comment_extractions_by_run(run_id)
    
    def get_extractions_by_project(self, project_id: str, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve extractions for a project, optionally filtered by run_id.
        
        Args:
            project_id: Project ID
            run_id: Optional run ID filter
            
        Returns:
            List of extraction documents
        """
        if run_id:
            return self.cosmos_service.get_comment_extractions_by_project_and_run(project_id, run_id)
        return self.cosmos_service.get_comment_extractions_by_project(project_id)


# Global service instance
_extraction_persistence_service = None

def get_extraction_persistence_service() -> ExtractionPersistenceService:
    """Get the global extraction persistence service instance."""
    global _extraction_persistence_service
    if _extraction_persistence_service is None:
        _extraction_persistence_service = ExtractionPersistenceService()
    return _extraction_persistence_service
