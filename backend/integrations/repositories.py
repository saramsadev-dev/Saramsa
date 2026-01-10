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
    
    def create_or_update_integration_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update integration account document.
        
        If an account with the same userId and provider exists, update it.
        Otherwise, create a new one.
        """
        try:
            user_id = data.get('userId')
            provider = data.get('provider')
            
            if user_id and provider:
                # Check if account already exists
                existing = self.get_by_user_and_provider(user_id, provider)
                if existing:
                    # Update existing account
                    account_id = existing['id']
                    # Merge existing data with new data, preserving id, type, and createdAt
                    updated_data = {**existing, **data}
                    updated_data['id'] = account_id
                    updated_data['type'] = self.entity_type  # Ensure type is correct
                    if 'createdAt' in existing:
                        updated_data['createdAt'] = existing['createdAt']
                    # Update updatedAt timestamp
                    from datetime import datetime, timezone
                    updated_data['updatedAt'] = datetime.now(timezone.utc).isoformat()
                    return self.update(account_id, updated_data)
            
            # Create new account
            return self.create_integration_account(data)
        except Exception as e:
            logger.error(f"Error creating or updating integration account: {e}")
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
    
    def get_integration_account(self, user_id: str, account_id: str) -> Optional[Dict[str, Any]]:
        """Get integration account by user ID and account ID.
        
        Note: The integrations container uses userId as the partition key,
        so we need to use userId when querying by ID.
        """
        try:
            # The integrations container uses userId as partition key, not id
            # So we need to query using userId as partition key
            user_id_str = str(user_id)
            
            # Try to get the document using userId as partition key
            try:
                account = self.cosmos_service.get_document(
                    self.container_name,
                    account_id,
                    user_id_str  # Use userId as partition key, not account_id
                )
            except Exception as doc_error:
                logger.warning(f"Could not get account {account_id} with partition key {user_id_str}: {doc_error}")
                # Fallback: query by id and userId
                query = "SELECT * FROM c WHERE c.id = @account_id AND c.userId = @user_id"
                parameters = [
                    {"name": "@account_id", "value": account_id},
                    {"name": "@user_id", "value": user_id_str}
                ]
                results = self.cosmos_service.query_documents(self.container_name, query, parameters)
                account = results[0] if results else None
            
            if not account:
                logger.warning(f"Account {account_id} not found for user {user_id_str}")
                return None
            
            account_user_id = account.get('userId')
            account_user_id_str = str(account_user_id) if account_user_id else None
            
            logger.debug(f"Found account {account_id} - comparing user IDs: request '{user_id_str}' vs account '{account_user_id_str}'")
            
            # Verify the account belongs to the user
            if account_user_id_str == user_id_str:
                return account
            else:
                logger.warning(f"User ID mismatch for account {account_id}. Request user: '{user_id_str}', Account user: '{account_user_id_str}'")
                return None
        except Exception as e:
            logger.error(f"Error getting integration account {account_id} for user {user_id}: {e}", exc_info=True)
            return None
    
    def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all integration accounts for a user."""
        query = "SELECT * FROM c WHERE c.userId = @user_id AND c.type = @type ORDER BY c.createdAt DESC"
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@type", "value": self.entity_type}
        ]
        return self.cosmos_service.query_documents(self.container_name, query, parameters)
    
    def get_integration_accounts_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all integration accounts for a user (alias for get_by_user)."""
        return self.get_by_user(user_id)
    
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
    
    def delete_integration_account(self, user_id: str, account_id: str) -> bool:
        """Delete integration account by user ID and account ID."""
        try:
            # Verify the account belongs to the user
            account = self.get_integration_account(user_id, account_id)
            if not account:
                return False
            return self.delete(account_id)
        except Exception as e:
            logger.error(f"Error deleting integration account {account_id} for user {user_id}: {e}")
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
        projects = self.cosmos_service.query_documents('projects', query, parameters)
        
        # Ensure all projects have required properties for frontend compatibility
        for project in projects:
            if 'externalLinks' not in project:
                project['externalLinks'] = []
            if 'description' not in project:
                project['description'] = ""
            if 'status' not in project:
                project['status'] = "active"
        
        return projects
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        try:
            return self.cosmos_service.get_document('projects', project_id, project_id)
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None
    
    def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project by ID and user ID (verifies ownership).
        
        Args:
            project_id: Project ID
            user_id: User ID to verify ownership
            
        Returns:
            Project data if found and owned by user, None otherwise
        """
        try:
            logger.info(f"Searching for project {project_id} with user {user_id}")
            query = "SELECT * FROM c WHERE c.id = @project_id AND c.userId = @user_id AND c.type = 'project'"
            parameters = [
                {"name": "@project_id", "value": project_id},
                {"name": "@user_id", "value": user_id}
            ]
            results = self.cosmos_service.query_documents('projects', query, parameters)
            if results:
                project = results[0]
                logger.info(f"Found project {project_id}: {project.get('name', 'Unknown')}")
                
                # Ensure project has required properties for frontend compatibility
                if 'externalLinks' not in project:
                    project['externalLinks'] = []
                if 'description' not in project:
                    project['description'] = ""
                if 'status' not in project:
                    project['status'] = "active"
                
                return project
            else:
                logger.warning(f"No project found with id={project_id}, userId={user_id}, type='project'")
                return None
        except Exception as e:
            logger.error(f"Error getting project {project_id} for user {user_id}: {e}")
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