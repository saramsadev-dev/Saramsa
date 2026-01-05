"""
Integrations repository for integration-related data operations.
"""

from typing import Dict, List, Optional, Any
from apis.infrastructure.cosmos_service import cosmos_service
import logging

logger = logging.getLogger(__name__)


class IntegrationsRepository:
    """Repository for integrations operations."""
    
    def __init__(self):
        self.cosmos_service = cosmos_service
        self.container_name = 'integrations'
        self.entity_type = "integration_account"
    
    def create_integration_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create integration account document."""
        try:
            data['type'] = self.entity_type
            return self.cosmos_service.create_document(self.container_name, data)
        except Exception as e:
            logger.error(f"Error creating integration account: {e}")
            raise
    
    def get_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get integration account by ID."""
        try:
            return self.cosmos_service.get_document(
                self.container_name, 
                account_id, 
                account_id
            )
        except Exception as e:
            logger.error(f"Error getting integration account {account_id}: {e}")
            return None
    
    def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all integration accounts for a user."""
        query = "SELECT * FROM c WHERE c.userId = @user_id AND c.type = @type ORDER BY c.createdAt DESC"
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@type", "value": self.entity_type}
        ]
        return self.cosmos_service.query_documents(self.container_name, query, parameters)
    
    def get_by_user_and_provider(self, user_id: str, provider: str) -> Optional[Dict[str, Any]]:
        """Get integration account by user and provider."""
        query = "SELECT * FROM c WHERE c.userId = @user_id AND c.provider = @provider AND c.type = @type"
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@provider", "value": provider},
            {"name": "@type", "value": self.entity_type}
        ]
        results = self.cosmos_service.query_documents(self.container_name, query, parameters)
        return results[0] if results else None
    
    def update(self, account_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update integration account document."""
        try:
            return self.cosmos_service.update_document(
                self.container_name,
                account_id,
                account_id,
                data
            )
        except Exception as e:
            logger.error(f"Error updating integration account {account_id}: {e}")
            raise
    
    def delete(self, account_id: str) -> bool:
        """Delete integration account document."""
        try:
            return self.cosmos_service.delete_document(
                self.container_name,
                account_id,
                account_id
            )
        except Exception as e:
            logger.error(f"Error deleting integration account {account_id}: {e}")
            return False
    
    # Project-related methods (these might need to be moved to projects repository)
    def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create project document."""
        try:
            data['type'] = 'project'
            return self.cosmos_service.create_document('projects', data)
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    def get_projects_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all projects for a user."""
        query = "SELECT * FROM c WHERE c.userId = @user_id AND c.type = 'project' ORDER BY c.createdAt DESC"
        parameters = [{"name": "@user_id", "value": user_id}]
        return self.cosmos_service.query_documents('projects', query, parameters)
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        try:
            return self.cosmos_service.get_document('projects', project_id, project_id)
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None
    
    def update_project(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update project document."""
        try:
            return self.cosmos_service.update_document('projects', project_id, project_id, data)
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            raise
    
    def delete_project(self, project_id: str) -> bool:
        """Delete project document."""
        try:
            return self.cosmos_service.delete_document('projects', project_id, project_id)
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            return False
    
    def check_external_project_exists(self, provider: str, external_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Check if external project already exists."""
        query = """
        SELECT * FROM c 
        WHERE c.userId = @user_id 
        AND c.type = 'project'
        AND EXISTS (
            SELECT VALUE link FROM link IN c.externalLinks 
            WHERE link.provider = @provider 
            AND link.externalId = @external_id
        )
        """
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@provider", "value": provider},
            {"name": "@external_id", "value": external_id}
        ]
        results = self.cosmos_service.query_documents('projects', query, parameters)
        return results[0] if results else None