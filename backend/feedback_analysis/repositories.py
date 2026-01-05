"""
Analysis repository for analysis-related data operations.
"""

from typing import Dict, List, Optional, Any
from apis.infrastructure.cosmos_service import cosmos_service
import logging

logger = logging.getLogger(__name__)


class AnalysisRepository:
    """Repository for analysis operations."""
    
    def __init__(self):
        self.cosmos_service = cosmos_service
        self.container_name = 'analysis'
        self.entity_type = "analysis"
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new analysis document."""
        try:
            data['type'] = self.entity_type
            return self.cosmos_service.create_document(self.container_name, data)
        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            raise
    
    def get_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by ID."""
        try:
            return self.cosmos_service.get_analysis_data(analysis_id)
        except Exception as e:
            logger.error(f"Error getting analysis by ID {analysis_id}: {e}")
            return None
    
    def get_latest_by_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest analysis for a project."""
        try:
            return self.cosmos_service.get_latest_analysis_for_project(project_id)
        except Exception as e:
            logger.error(f"Error getting latest analysis for project {project_id}: {e}")
            return None
    
    def get_latest_personal_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest personal analysis for a user."""
        try:
            return self.cosmos_service.get_latest_personal_analysis(user_id)
        except Exception as e:
            logger.error(f"Error getting latest personal analysis for user {user_id}: {e}")
            return None
    
    def get_by_project(self, project_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get analyses for a project with optional limit."""
        try:
            # Use existing cosmos service method with query
            query = """
            SELECT * FROM c 
            WHERE c.projectId = @project_id AND c.type = @type 
            ORDER BY c.createdAt DESC 
            OFFSET 0 LIMIT @limit
            """
            parameters = [
                {"name": "@project_id", "value": project_id},
                {"name": "@type", "value": self.entity_type},
                {"name": "@limit", "value": limit}
            ]
            return self.cosmos_service.query_documents(self.container_name, query, parameters)
        except Exception as e:
            logger.error(f"Error getting analyses for project {project_id}: {e}")
            return []
    
    def get_cumulative_data_by_user(self, user_id: str) -> Dict[str, Any]:
        """Get cumulative analysis data for a user across all projects."""
        try:
            query = """
            SELECT * FROM c 
            WHERE c.userId = @user_id AND c.type = @type 
            ORDER BY c.createdAt ASC
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@type", "value": self.entity_type}
            ]
            
            analyses = self.cosmos_service.query_documents(self.container_name, query, parameters)
            
            if not analyses:
                return {
                    'total_analyses': 0,
                    'total_comments': 0,
                    'quarters_covered': [],
                    'latest_quarter': None,
                    'analyses_history': [],
                    'all_comments': []
                }
            
            # Process cumulative data
            all_comments = []
            quarters = set()
            
            for analysis in analyses:
                if 'comments' in analysis:
                    all_comments.extend(analysis['comments'])
                if 'quarter' in analysis:
                    quarters.add(analysis['quarter'])
            
            return {
                'total_analyses': len(analyses),
                'total_comments': len(all_comments),
                'quarters_covered': list(quarters),
                'latest_quarter': analyses[-1].get('quarter') if analyses else None,
                'analyses_history': analyses,
                'all_comments': all_comments
            }
        except Exception as e:
            logger.error(f"Error getting cumulative data for user {user_id}: {e}")
            return {
                'total_analyses': 0,
                'total_comments': 0,
                'quarters_covered': [],
                'latest_quarter': None,
                'analyses_history': [],
                'all_comments': []
            }
    
    # Insights Methods
    def get_all_insights(self) -> List[Dict[str, Any]]:
        """Get all insights."""
        return self.cosmos_service.query_documents("insights", "SELECT * FROM c WHERE c.type = 'insight' ORDER BY c.analysis_date DESC")
    
    def get_insight_by_id(self, insight_id: str) -> Optional[Dict[str, Any]]:
        """Get insight by ID."""
        return self.cosmos_service.get_insight(insight_id)
    
    def get_insights_by_type(self, analysis_type: str) -> List[Dict[str, Any]]:
        """Get insights by analysis type."""
        return self.cosmos_service.query_documents(
            "insights", 
            "SELECT * FROM c WHERE c.type = 'insight' AND c.analysis_type = @analysis_type ORDER BY c.analysis_date DESC",
            [{"name": "@analysis_type", "value": analysis_type}]
        )
    
    # Work Items Methods
    def get_work_items_by_project(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get work items by project."""
        return self.cosmos_service.get_work_items_by_project(project_id)
    
    def get_deep_analysis_by_project(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get deep analysis by project."""
        return self.cosmos_service.get_deep_analysis_by_project(project_id)
    
    # Analysis Data Methods
    def save_analysis_data(self, analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save analysis data."""
        return self.cosmos_service.save_analysis_data(analysis_data)
    
    def update_project_last_analysis(self, project_id: str, analysis_id: str) -> bool:
        """Update project's last analysis."""
        return self.cosmos_service.update_project_last_analysis(project_id, analysis_id)
    
    # User Data Methods
    def get_latest_personal_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get latest personal user data."""
        return self.cosmos_service.get_latest_personal_user_data(user_id)
    
    def get_user_data_by_project(self, user_id: str, project_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by project."""
        return self.cosmos_service.get_user_data_by_project(user_id, project_id)
    
    # User Stories Methods
    def get_user_stories_by_user_and_project(self, user_id: str, project_id: str) -> List[Dict[str, Any]]:
        """Get user stories by user and project."""
        return self.cosmos_service.get_user_stories_by_user_and_project(user_id, project_id)
    
    def get_user_stories_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user stories by user."""
        return self.cosmos_service.get_user_stories_by_user(user_id)
    
    def get_user_stories_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get user stories by project."""
        return self.cosmos_service.get_user_stories_by_project(project_id)
    
    def save_user_story(self, user_story_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save user story."""
        return self.cosmos_service.save_user_story(user_story_data)
    
    def get_user_story(self, user_story_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user story by ID and user."""
        return self.cosmos_service.get_user_story(user_story_id, user_id)
    
    def get_user_story_by_id(self, user_story_id: str) -> Optional[Dict[str, Any]]:
        """Get user story by ID."""
        return self.cosmos_service.get_user_story_by_id(user_story_id)
    
    def delete_user_story(self, user_story_id: str, user_id: str) -> bool:
        """Delete user story."""
        return self.cosmos_service.delete_item(
            container_type='user_stories',
            item_id=user_story_id,
            partition_key=user_id
        )
    
    # Work Item Management Methods
    def update_embedded_work_item(self, work_item_id: str, user_id: str, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update embedded work item."""
        return self.cosmos_service.update_embedded_work_item(work_item_id, user_id, updated_data)
    
    def delete_work_items_from_user_story(self, user_story_id: str, work_item_ids: List[str], user_id: str) -> Dict[str, Any]:
        """Delete work items from user story."""
        return self.cosmos_service.delete_work_items_from_user_story(user_story_id, work_item_ids, user_id)
    
    def delete_embedded_work_items(self, work_item_ids: List[str], user_id: str) -> int:
        """Delete embedded work items."""
        return self.cosmos_service.delete_embedded_work_items(work_item_ids, user_id)
    
    # Analysis History Methods
    def get_analysis_history_for_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get analysis history for project."""
        return self.cosmos_service.get_analysis_history_for_project(project_id)
    
    def get_analysis_by_quarter(self, project_id: str, quarter: str) -> Optional[Dict[str, Any]]:
        """Get analysis by quarter."""
        return self.cosmos_service.get_analysis_by_quarter(project_id, quarter)
    
    def get_cumulative_analysis_for_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get cumulative analysis for project."""
        return self.cosmos_service.get_cumulative_analysis_for_project(project_id)
    
    # Generic Query Methods
    def query_items(self, container_name: str, query: str, parameters: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generic query method."""
        return self.cosmos_service.query_documents(container_name, query, parameters)
    
    def patch_user_story(self, user_story_id: str, partition_key: str, patch_operations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Patch user story."""
        try:
            return self.cosmos_service.patch_user_story(user_story_id, partition_key, patch_operations)
        except Exception as e:
            logger.error(f"Error patching user story {user_story_id}: {e}")
            return None
            
        