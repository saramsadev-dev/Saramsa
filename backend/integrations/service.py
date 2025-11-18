"""
Integration service for managing integration accounts and projects.
Following the existing codebase pattern using aiCore.cosmos_service.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from aiCore.cosmos_service import cosmos_service
from .models import create_integration_account, create_jira_integration_account, create_azure_integration_account, create_project, create_external_link, validate_integration_account, validate_project
from .encryption import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)


class IntegrationsService:
    """Service for managing integrations and projects using Cosmos DB."""
    
    def __init__(self):
        self.cosmos = cosmos_service

    # Integration Account methods
    def create_integration_account(self, user_id: str, provider: str, credentials: Dict[str, Any], 
                                 metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new integration account."""
        try:
            # Encrypt sensitive tokens
            if "api_token" in credentials:
                credentials["tokenEncrypted"] = encrypt_token(credentials["api_token"])
                credentials.pop("api_token", None)  # Remove plain token
            elif "pat_token" in credentials:
                credentials["tokenEncrypted"] = encrypt_token(credentials["pat_token"])
                credentials.pop("pat_token", None)  # Remove plain token
            
            # Create account document
            account_data = create_integration_account(user_id, provider, credentials, metadata)
            validate_integration_account(account_data)
            
            # Store in Cosmos DB integrations container
            container = self.cosmos.get_container('integrations')
            result = container.create_item(account_data)
            
            logger.info(f"Created integration account {account_data['id']} for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating integration account: {e}")
            raise
    
    def create_azure_integration(self, user_id: str, organization: str, pat_token: str) -> Dict[str, Any]:
        """Create Azure DevOps integration account."""
        try:
            # Check if integration already exists for this user and organization
            existing_account = self.get_integration_account_by_provider(user_id, 'azure')
            if existing_account and existing_account.get('metadata', {}).get('organization') == organization:
                # Instead of raising an error, update the existing integration
                logger.info(f"Updating existing Azure integration for user {user_id}, org {organization}")
                return self.update_integration_credentials(existing_account['id'], user_id, 'azure', {
                    'organization': organization,
                    'pat_token': pat_token
                })
            
            # Encrypt the PAT token
            encrypted_pat = encrypt_token(pat_token)
            
            # Create account document
            account_data = create_azure_integration_account(user_id, organization, encrypted_pat)
            validate_integration_account(account_data)
            
            # Store in Cosmos DB integrations container
            container = self.cosmos.get_container('integrations')
            result = container.create_item(account_data)
            
            logger.info(f"Created Azure integration for user {user_id}, org {organization}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating Azure integration: {e}")
            raise
    
    def create_jira_integration(self, user_id: str, domain: str, email: str, api_token: str) -> Dict[str, Any]:
        """Create Jira integration account."""
        try:
            # Check if integration already exists for this user and domain
            existing_account = self.get_integration_account_by_provider(user_id, 'jira')
            if existing_account and existing_account.get('metadata', {}).get('domain') == domain:
                # Instead of raising an error, update the existing integration
                logger.info(f"Updating existing Jira integration for user {user_id}, domain {domain}")
                return self.update_integration_credentials(existing_account['id'], user_id, 'jira', {
                    'domain': domain,
                    'email': email,
                    'api_token': api_token
                })
            
            # Encrypt the API token
            encrypted_token = encrypt_token(api_token)
            
            # Create account document
            account_data = create_jira_integration_account(user_id, domain, email, encrypted_token)
            validate_integration_account(account_data)
            
            # Store in Cosmos DB integrations container
            container = self.cosmos.get_container('integrations')
            result = container.create_item(account_data)
            
            logger.info(f"Created Jira integration for user {user_id}, domain {domain}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating Jira integration: {e}")
            raise
    
    def get_integration_accounts_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all integration accounts for a user."""
        try:
            container = self.cosmos.get_container('integrations')
            
            query = """
                SELECT * FROM c 
                WHERE c.userId = @user_id 
                AND c.type = 'integrationAccount'
            """
            parameters = [{"name": "@user_id", "value": user_id}]
            
            logger.info(f"Querying integration accounts with user_id: {user_id}")
            results = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            logger.info(f"Found {len(results)} integration accounts for user {user_id}")
            
            # Remove sensitive data from response
            for account in results:
                if "credentials" in account and "tokenEncrypted" in account["credentials"]:
                    account["credentials"] = {k: v for k, v in account["credentials"].items() 
                                           if k != "tokenEncrypted"}
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting integration accounts for user {user_id}: {e}")
            raise

    def get_integration_account_by_provider(self, user_id: str, provider: str) -> Optional[Dict[str, Any]]:
        """Get integration account by user and provider."""
        try:
            container = self.cosmos.get_container('integrations')
            
            query = """
                SELECT * FROM c 
                WHERE c.userId = @user_id 
                AND c.provider = @provider 
                AND c.type = 'integrationAccount'
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@provider", "value": provider}
            ]
            
            results = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            if results:
                account = results[0]
                # Remove sensitive data from response
                if "credentials" in account and "tokenEncrypted" in account["credentials"]:
                    account["credentials"] = {k: v for k, v in account["credentials"].items() 
                                           if k != "tokenEncrypted"}
                return account
            return None
            
        except Exception as e:
            logger.error(f"Error getting integration account for {provider}: {e}")
            raise
    
    def get_integration_account_by_id(self, user_id: str, account_id: str) -> Optional[Dict[str, Any]]:
        """Get integration account by ID."""
        try:
            container = self.cosmos.get_container('integrations')
            
            query = """
                SELECT * FROM c 
                WHERE c.userId = @user_id 
                AND c.id = @account_id 
                AND c.type = 'integrationAccount'
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@account_id", "value": account_id}
            ]
            
            results = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            if results:
                account = results[0]
                # Remove sensitive data from response
                if "credentials" in account and "tokenEncrypted" in account["credentials"]:
                    account["credentials"] = {k: v for k, v in account["credentials"].items() 
                                           if k != "tokenEncrypted"}
                return account
            return None
            
        except Exception as e:
            logger.error(f"Error getting integration account by ID {account_id}: {e}")
            raise

    def get_decrypted_credentials_by_account_id(self, user_id: str, account_id: str) -> Optional[Dict[str, Any]]:
        """Get integration account with decrypted credentials by account ID (for internal use only)."""
        try:
            container = self.cosmos.get_container('integrations')
            
            query = """
                SELECT * FROM c 
                WHERE c.userId = @user_id 
                AND c.id = @account_id 
                AND c.type = 'integrationAccount'
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@account_id", "value": account_id}
            ]
            
            results = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            if results:
                account = results[0]
                # Decrypt the token for internal use
                if "credentials" in account and "tokenEncrypted" in account["credentials"]:
                    encrypted_token = account["credentials"]["tokenEncrypted"]
                    decrypted_token = decrypt_token(encrypted_token)
                    
                    # Add decrypted token based on provider
                    if account["provider"] == "azure":
                        account["credentials"]["pat_token"] = decrypted_token
                    elif account["provider"] == "jira":
                        account["credentials"]["api_token"] = decrypted_token
                    
                    # Remove encrypted token
                    account["credentials"].pop("tokenEncrypted", None)
                
                return account
            return None
            
        except Exception as e:
            logger.error(f"Error getting decrypted credentials for account {account_id}: {e}")
            raise

    def get_decrypted_credentials(self, user_id: str, provider: str) -> Optional[Dict[str, Any]]:
        """Get integration account with decrypted credentials (for internal use only)."""
        try:
            container = self.cosmos.get_container('integrations')
            
            query = """
                SELECT * FROM c 
                WHERE c.userId = @user_id 
                AND c.provider = @provider 
                AND c.type = 'integrationAccount'
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@provider", "value": provider}
            ]
            
            results = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            if results:
                account = results[0]
                # Decrypt the token for internal use
                if "credentials" in account and "tokenEncrypted" in account["credentials"]:
                    encrypted_token = account["credentials"]["tokenEncrypted"]
                    decrypted_token = decrypt_token(encrypted_token)
                    
                    # Add decrypted token based on provider
                    if provider == "azure":
                        account["credentials"]["pat_token"] = decrypted_token
                    elif provider == "jira":
                        account["credentials"]["api_token"] = decrypted_token
                    
                return account
            return None
            
        except Exception as e:
            logger.error(f"Error getting decrypted credentials for {provider}: {e}")
            raise

    def update_integration_account(self, user_id: str, provider: str, updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing integration account."""
        try:
            # Get existing account
            existing_account = self.get_integration_account_by_provider(user_id, provider)
            if not existing_account:
                raise ValueError(f"No {provider} integration found for user")
            
            # Update allowed fields
            allowed_fields = ['credentials', 'metadata', 'displayName', 'status']
            for field in allowed_fields:
                if field in updated_data:
                    existing_account[field] = updated_data[field]
            
            # Update timestamp
            existing_account['updatedAt'] = datetime.now(timezone.utc).isoformat()
            
            # Save updated account
            container = self.cosmos.get_container('integrations')
            result = container.replace_item(existing_account['id'], existing_account)
            
            logger.info(f"Updated {provider} integration for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error updating {provider} integration: {e}")
            raise

    def delete_integration_account(self, account_id: str, user_id: str) -> bool:
        """Delete an integration account."""
        try:
            container = self.cosmos.get_container('integrations')
            container.delete_item(item=account_id, partition_key=user_id)
            
            logger.info(f"Deleted integration account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting integration account: {e}")
            return False
    
    def create_project(self, user_id: str, name: str, description: str = None, 
                      external_links: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new project."""
        try:
            container = self.cosmos.get_container('projects')
            
            project_id = str(uuid.uuid4())
            project_data = {
                "id": project_id,
                "type": "project",
                "userId": user_id,
                "name": name,
                "description": description,
                "status": "active",
                "externalLinks": external_links or [],
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "schemaVersion": 1
            }
            
            result = container.create_item(project_data)
            logger.info(f"Created project {name} for user {user_id} (type: {type(user_id)})")
            return result
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a single project by ID."""
        try:
            container = self.cosmos.get_container('projects')
            
            try:
                project = container.read_item(item=project_id, partition_key=project_id)
                
                # Verify user has access
                if project.get('userId') != user_id:
                    logger.warning(f"Access denied: Project {project_id} belongs to user {project.get('userId')}, not {user_id}")
                    return None
                
                return project
                
            except Exception as read_error:
                logger.error(f"Project {project_id} not found: {read_error}")
                return None
            
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None

    def get_projects_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all projects for a user."""
        try:
            container = self.cosmos.get_container('projects')
            
            query = """
                SELECT * FROM c 
                WHERE c.userId = @user_id 
                ORDER BY c.createdAt DESC
            """
            parameters = [{"name": "@user_id", "value": user_id}]
            
            logger.info(f"Querying projects with user_id: {user_id}")
            results = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            logger.info(f"Found {len(results)} projects for user {user_id}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting projects for user {user_id}: {e}")
            raise

    def update_project(self, project_id: str, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a project."""
        try:
            container = self.cosmos.get_container('projects')
            
            # Get the project first
            query = """
                SELECT * FROM c 
                WHERE c.id = @project_id 
                AND c.userId = @user_id
            """
            parameters = [
                {"name": "@project_id", "value": project_id},
                {"name": "@user_id", "value": user_id}
            ]
            
            results = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if not results:
                raise ValueError("Project not found or access denied")
            
            project = results[0]
            
            # Update allowed fields
            # Handle both 'name' and 'project_name' for compatibility
            if 'project_name' in updates:
                project['name'] = updates['project_name']
            elif 'name' in updates:
                project['name'] = updates['name']
            
            if 'description' in updates:
                project['description'] = updates['description']
            
            if 'metadata' in updates:
                project['metadata'] = updates['metadata']
            
            project['updatedAt'] = datetime.now(timezone.utc).isoformat()
            
            # Save updated project
            result = container.replace_item(project['id'], project)
            logger.info(f"Updated project {project_id} for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error updating project: {e}")
            raise

    def delete_project(self, project_id: str, user_id: str) -> bool:
        """Delete a project."""
        try:
            container = self.cosmos.get_container('projects')
            logger.info(f"DELETE PROJECT - project_id: {project_id}, user_id: {user_id}")
            
            # First, query to find the project (works across partitions)
            query = """
                SELECT * FROM c 
                WHERE c.id = @project_id 
                AND c.userId = @user_id
            """
            parameters = [
                {"name": "@project_id", "value": project_id},
                {"name": "@user_id", "value": user_id}
            ]
            
            results = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if not results:
                logger.warning(f"Project {project_id} not found for user {user_id}")
                return False
            
            project_item = results[0]
            logger.info(f"Found project: {project_item.get('id')}")
            logger.info(f"Project keys: {list(project_item.keys())}")
            
            # Try different partition key strategies
            # Strategy 1: Try with userId as partition key
            try:
                logger.info(f"Attempting delete with userId as partition key: {user_id}")
                container.delete_item(item=project_item['id'], partition_key=user_id)
                logger.info(f"Successfully deleted project {project_id} using userId partition key")
                return True
            except Exception as e1:
                logger.warning(f"Delete with userId partition key failed: {e1}")
                
                # Strategy 2: Try with id as partition key
                try:
                    logger.info(f"Attempting delete with id as partition key: {project_item['id']}")
                    container.delete_item(item=project_item['id'], partition_key=project_item['id'])
                    logger.info(f"Successfully deleted project {project_id} using id partition key")
                    return True
                except Exception as e2:
                    logger.error(f"Delete with id partition key also failed: {e2}")
                    raise
            
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}", exc_info=True)
            return False

    def check_external_project_exists(self, provider: str, external_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Check if an external project is already imported by the current user."""
        try:
            container = self.cosmos.get_container('projects')
            
            # Only check for the current user, not all users
            query = """
                SELECT * FROM c 
                WHERE c.userId = @user_id
                AND EXISTS(
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
            
            results = list(container.query_items(
                query=query, 
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Error checking external project {external_id}: {e}")
            return None


# Global service instance
integrations_service = IntegrationsService()
