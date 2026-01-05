"""
Integration service for managing external platform integrations.

This service handles the business logic for creating, managing, and testing
integrations with external platforms like Azure DevOps and Jira.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
import logging

from ..repositories import IntegrationsRepository
from .external_api_service import get_external_api_service

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for integration business logic."""
    
    def __init__(self):
        self.integrations_repo = IntegrationsRepository()
        self.external_api_service = get_external_api_service()
    
    def _get_default_scopes(self, provider: str) -> List[str]:
        """Get default scopes for a provider."""
        scopes_map = {
            "azure": ["vso.project", "vso.code", "vso.work"],
            "jira": ["read:project", "write:issue", "read:issue"]
        }
        return scopes_map.get(provider, [])
    
    def _create_integration_account_document(self, user_id: str, provider: str, credentials: Dict[str, Any], 
                                           metadata: Dict[str, Any], display_name: str = None) -> Dict[str, Any]:
        """Create a new integration account document for Cosmos DB."""
        account_id = f"ia_{uuid.uuid4().hex[:12]}"
        
        return {
            "id": account_id,
            "type": "integrationAccount",
            "userId": user_id,  # This is the partition key for integrations container
            "provider": provider,
            "displayName": display_name or f"{metadata.get('organization', metadata.get('domain', 'Unknown'))} ({provider.title()})",
            "status": "active",
            "credentials": credentials,
            "metadata": metadata,
            "scopes": self._get_default_scopes(provider),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "expiresAt": None,
            "schemaVersion": 1
        }
    
    def _validate_integration_account(self, account_data: Dict[str, Any]) -> bool:
        """Validate integration account data."""
        required_fields = ["userId", "provider", "credentials", "metadata"]
        
        for field in required_fields:
            if field not in account_data:
                raise ValueError(f"Missing required field: {field}")
        
        if account_data["provider"] not in ["azure", "jira"]:
            raise ValueError("Provider must be 'azure' or 'jira'")
        
        return True
    
    def get_integration_accounts_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all integration accounts for a user."""
        try:
            return self.integrations_repo.get_integration_accounts_by_user(user_id)
        except Exception as e:
            logger.error(f"Error getting integration accounts for user {user_id}: {e}")
            raise
    
    def create_azure_integration(self, user_id: str, organization: str, pat_token: str) -> Dict[str, Any]:
        """
        Create or update Azure DevOps integration account.
        
        Args:
            user_id: User ID
            organization: Azure DevOps organization name
            pat_token: Personal Access Token
            
        Returns:
            Created/updated integration account
            
        Raises:
            ValueError: If connection test fails or validation errors
        """
        try:
            # Validate inputs
            if not organization or not pat_token:
                raise ValueError("Organization and PAT token are required")
            
            # Test the connection first
            test_result = self.external_api_service.test_azure_connection(organization, pat_token)
            if not test_result['success']:
                raise ValueError(f"Connection test failed: {test_result['error']}")
            
            # Encrypt the token
            from .encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            encrypted_pat = encryption_service.encrypt_token(pat_token)
            
            # Create account document
            credentials = {
                "tokenEncrypted": encrypted_pat,
                "tokenType": "pat"
            }
            
            metadata = {
                "organization": organization,
                "baseUrl": f"https://dev.azure.com/{organization}"
            }
            
            account_data = self._create_integration_account_document(
                user_id=user_id,
                provider="azure",
                credentials=credentials,
                metadata=metadata,
                display_name=f"{organization} (Azure DevOps)"
            )
            
            self._validate_integration_account(account_data)
            
            return self.integrations_repo.create_or_update_integration_account(account_data)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating Azure integration: {e}")
            raise
    
    def create_jira_integration(self, user_id: str, domain: str, email: str, api_token: str) -> Dict[str, Any]:
        """
        Create or update Jira integration account.
        
        Args:
            user_id: User ID
            domain: Jira domain
            email: User email
            api_token: Jira API token
            
        Returns:
            Created/updated integration account
            
        Raises:
            ValueError: If connection test fails or validation errors
        """
        try:
            # Validate inputs
            if not domain or not email or not api_token:
                raise ValueError("Domain, email, and API token are required")
            
            # Test the connection first
            test_result = self.external_api_service.test_jira_connection(domain, email, api_token)
            if not test_result['success']:
                raise ValueError(f"Connection test failed: {test_result['error']}")
            
            # Encrypt the token
            from .encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            encrypted_token = encryption_service.encrypt_token(api_token)
            
            # Handle domain format properly - normalize domain
            normalized_domain = domain.replace('.atlassian.net', '') if domain.endswith('.atlassian.net') else domain
            base_url = f"https://{normalized_domain}.atlassian.net"
            
            # Create account document
            credentials = {
                "tokenEncrypted": encrypted_token,
                "email": email,
                "tokenType": "api_token"
            }
            
            metadata = {
                "domain": domain,
                "email": email,
                "baseUrl": base_url
            }
            
            account_data = self._create_integration_account_document(
                user_id=user_id,
                provider="jira",
                credentials=credentials,
                metadata=metadata,
                display_name=f"{domain} (Jira)"
            )
            
            self._validate_integration_account(account_data)
            
            return self.integrations_repo.create_or_update_integration_account(account_data)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating Jira integration: {e}")
            raise
    
    def test_integration_connection(self, user_id: str, account_id: str) -> Dict[str, Any]:
        """
        Test connection for an existing integration account.
        
        Args:
            user_id: User ID
            account_id: Integration account ID
            
        Returns:
            Test result with success status and details
        """
        try:
            # Get the integration account
            account = self.integrations_repo.get_integration_account(user_id, account_id)
            if not account:
                raise ValueError("Integration account not found")
            
            provider = account.get('provider')
            credentials = account.get('credentials', {})
            metadata = account.get('metadata', {})
            
            # Decrypt credentials
            from .encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            if provider == 'azure':
                organization = metadata.get('organization')
                encrypted_pat = credentials.get('tokenEncrypted')
                pat_token = encryption_service.decrypt_token(encrypted_pat)
                return self.external_api_service.test_azure_connection(organization, pat_token)
            elif provider == 'jira':
                domain = metadata.get('domain')
                email = metadata.get('email')
                encrypted_token = credentials.get('tokenEncrypted')
                api_token = encryption_service.decrypt_token(encrypted_token)
                return self.external_api_service.test_jira_connection(domain, email, api_token)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error testing integration connection: {e}")
            raise
    
    def delete_integration_account(self, user_id: str, account_id: str) -> bool:
        """
        Delete an integration account.
        
        Args:
            user_id: User ID
            account_id: Integration account ID
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            return self.integrations_repo.delete_integration_account(user_id, account_id)
        except Exception as e:
            logger.error(f"Error deleting integration account {account_id}: {e}")
            raise
    
    def get_external_projects(self, user_id: str, provider: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Get projects from external platform API.
        
        Args:
            user_id: User ID
            provider: 'azure' or 'jira'
            **kwargs: Provider-specific parameters
            
        Returns:
            List of external projects
        """
        try:
            if provider == 'azure':
                organization = kwargs.get('organization')
                pat_token = kwargs.get('pat_token')
                if not organization or not pat_token:
                    raise ValueError("Organization and PAT token are required for Azure")
                return self.external_api_service.fetch_azure_projects(organization, pat_token)
            elif provider == 'jira':
                domain = kwargs.get('domain')
                email = kwargs.get('email')
                api_token = kwargs.get('api_token')
                if not domain or not email or not api_token:
                    raise ValueError("Domain, email, and API token are required for Jira")
                return self.external_api_service.fetch_jira_projects(domain, email, api_token)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching external projects for {provider}: {e}")
            raise
    
    def check_external_project_exists(self, provider: str, external_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if an external project is already imported.
        
        Args:
            provider: 'azure' or 'jira'
            external_id: External project ID
            user_id: User ID
            
        Returns:
            Existing project data if found, None otherwise
        """
        try:
            return self.integrations_repo.check_external_project_exists(provider, external_id, user_id)
        except Exception as e:
            logger.error(f"Error checking external project exists: {e}")
            raise


# Global service instance
_integration_service = None

def get_integration_service() -> IntegrationService:
    """Get the global integration service instance."""
    global _integration_service
    if _integration_service is None:
        _integration_service = IntegrationService()
    return _integration_service