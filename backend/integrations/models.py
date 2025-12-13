"""
Data structures for integration accounts and projects.
Following the existing codebase pattern of direct Cosmos DB operations.
No Django models - just data structures and helper functions.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json


def create_integration_account(user_id: str, provider: str, credentials: Dict[str, Any], 
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
        "scopes": get_default_scopes(provider),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "expiresAt": None,
        "schemaVersion": 1
    }


def create_azure_integration_account(user_id: str, organization: str, encrypted_pat: str) -> Dict[str, Any]:
    """Create Azure DevOps integration account."""
    credentials = {
        "tokenEncrypted": encrypted_pat,
        "tokenType": "pat"
    }
    
    metadata = {
        "organization": organization,
        "baseUrl": f"https://dev.azure.com/{organization}"
    }
    
    return create_integration_account(
        user_id=user_id,
        provider="azure",
        credentials=credentials,
        metadata=metadata,
        display_name=f"{organization} (Azure DevOps)"
    )


def create_jira_integration_account(user_id: str, domain: str, email: str, encrypted_token: str) -> Dict[str, Any]:
    """Create Jira integration account."""
    credentials = {
        "tokenEncrypted": encrypted_token,
        "email": email,
        "tokenType": "api_token"
    }
    
    # Handle domain format properly - normalize domain
    normalized_domain = domain.replace('.atlassian.net', '') if domain.endswith('.atlassian.net') else domain
    base_url = f"https://{normalized_domain}.atlassian.net"
    
    metadata = {
        "domain": domain,
        "email": email,
        "baseUrl": base_url
    }
    
    return create_integration_account(
        user_id=user_id,
        provider="jira",
        credentials=credentials,
        metadata=metadata,
        display_name=f"{domain} (Jira)"
    )


def create_project(user_id: str, name: str, description: str = None, 
                  external_links: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new project document for Cosmos DB."""
    project_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    return {
        "id": project_id,
        "type": "project",
        "userId": user_id,  # This is the partition key for projects container
        "name": name,
        "description": description,
        "status": "active",
        "createdAt": now,
        "updatedAt": now,
        "externalLinks": external_links or [],
        "schemaVersion": 1
    }


def create_external_link(provider: str, integration_account_id: str, external_id: str, 
                        external_key: str = None, url: str = "") -> Dict[str, Any]:
    """Create an external link for a project."""
    return {
        "provider": provider,
        "integrationAccountId": integration_account_id,
        "externalId": external_id,
        "externalKey": external_key,
        "url": url,
        "status": "ok",
        "lastSyncedAt": None,
        "syncMetadata": {}
    }


def get_default_scopes(provider: str) -> List[str]:
    """Get default scopes for a provider."""
    scopes_map = {
        "azure": ["vso.project", "vso.code", "vso.work"],
        "jira": ["read:project", "write:issue", "read:issue"]
    }
    return scopes_map.get(provider, [])


def validate_integration_account(account_data: Dict[str, Any]) -> bool:
    """Validate integration account data."""
    required_fields = ["userId", "provider", "credentials", "metadata"]
    
    for field in required_fields:
        if field not in account_data:
            raise ValueError(f"Missing required field: {field}")
    
    if account_data["provider"] not in ["azure", "jira"]:
        raise ValueError("Provider must be 'azure' or 'jira'")
    
    return True


def validate_project(project_data: Dict[str, Any]) -> bool:
    """Validate project data."""
    required_fields = ["name", "createdBy"]
    
    for field in required_fields:
        if field not in project_data:
            raise ValueError(f"Missing required field: {field}")
    
    if not project_data["name"].strip():
        raise ValueError("Project name cannot be empty")
    
    return True


# Cosmos DB container configurations
COSMOS_CONTAINERS = {
    'integration_accounts': {
        'partition_key': '/partitionKey',
        'unique_keys': [
            {'paths': ['/tenantId', '/userId', '/provider']},  # One account per provider per user
        ]
    },
    'projects': {
        'partition_key': '/partitionKey',
        'unique_keys': [
            {'paths': ['/tenantId', '/name', '/createdBy']},  # Unique project names per user
        ]
    }
}
