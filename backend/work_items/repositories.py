"""
Work item repository for DevOps-related data operations.
"""

from typing import Dict, List, Optional, Any
from apis.infrastructure.cosmos_service import cosmos_service
import logging

logger = logging.getLogger(__name__)


class WorkItemRepository:
    """Repository for work item operations."""
    
    def __init__(self):
        self.cosmos_service = cosmos_service
        self.container_name = 'user_stories'  # Using existing container
        self.entity_type = "user_story"
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new work item document."""
        try:
            data['type'] = self.entity_type
            return self.cosmos_service.create_document(self.container_name, data)
        except Exception as e:
            logger.error(f"Error creating work item: {e}")
            raise
    
    def get_by_id(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """Get work item by ID."""
        try:
            return self.cosmos_service.get_document(
                self.container_name, 
                work_item_id, 
                work_item_id
            )
        except Exception as e:
            logger.error(f"Error getting work item by ID {work_item_id}: {e}")
            return None
    
    def get_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get work items for a project."""
        query = "SELECT * FROM c WHERE c.projectId = @project_id AND c.type = @type ORDER BY c.createdAt DESC"
        parameters = [
            {"name": "@project_id", "value": project_id},
            {"name": "@type", "value": self.entity_type}
        ]
        return self.cosmos_service.query_documents(self.container_name, query, parameters)
    
    def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get work items for a user."""
        query = "SELECT * FROM c WHERE c.userId = @user_id AND c.type = @type ORDER BY c.createdAt DESC"
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@type", "value": self.entity_type}
        ]
        return self.cosmos_service.query_documents(self.container_name, query, parameters)
    
    def update(self, work_item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update work item document."""
        try:
            return self.cosmos_service.update_document(
                self.container_name,
                work_item_id,
                work_item_id,
                data
            )
        except Exception as e:
            logger.error(f"Error updating work item {work_item_id}: {e}")
            raise
    
    def delete(self, work_item_id: str) -> bool:
        """Delete work item document."""
        try:
            return self.cosmos_service.delete_document(
                self.container_name,
                work_item_id,
                work_item_id
            )
        except Exception as e:
            logger.error(f"Error deleting work item {work_item_id}: {e}")
            return False
    
    def update_embedded_work_item(self, work_item_id: str, user_id: str, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update embedded work item within a user story document."""
        try:
            # This method handles updating individual work items within the work_items array
            # of a user story document - moved from analysis service
            return self.cosmos_service.update_embedded_work_item(work_item_id, user_id, updated_data)
        except Exception as e:
            logger.error(f"Error updating embedded work item {work_item_id}: {e}")
            return None
    
    def get_work_items_by_project(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get work items by project - consolidated method."""
        try:
            # Query both work_items and deep_analysis types
            query = """
                SELECT * FROM c 
                WHERE c.projectId = @project_id 
                AND (c.type = 'work_items' OR c.type = 'deep_analysis' OR c.type = 'user_story')
                ORDER BY c.generated_at DESC
            """
            parameters = [{"name": "@project_id", "value": project_id}]
            return self.cosmos_service.query_documents('user_stories', query, parameters)
        except Exception as e:
            logger.error(f"Error getting work items by project {project_id}: {e}")
            return None
    
    def get_deep_analysis_by_project(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get deep analysis by project."""
        try:
            query = "SELECT * FROM c WHERE c.projectId = @project_id AND c.type = 'deep_analysis' ORDER BY c.generated_at DESC"
            parameters = [{"name": "@project_id", "value": project_id}]
            return self.cosmos_service.query_documents('user_stories', query, parameters)
        except Exception as e:
            logger.error(f"Error getting deep analysis by project {project_id}: {e}")
            return None