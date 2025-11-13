"""
External API helpers for testing connections and fetching data from Azure DevOps and Jira.
Reuses existing logic from devopsGenerator app.
"""

import requests
import base64
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def normalize_jira_domain(domain: str) -> str:
    """Normalize Jira domain to remove duplicate .atlassian.net suffixes."""
    # Remove any existing .atlassian.net suffix
    if domain.endswith('.atlassian.net'):
        return domain.replace('.atlassian.net', '')
    return domain


def build_jira_url(domain: str, path: str) -> str:
    """Build a proper Jira URL."""
    normalized_domain = normalize_jira_domain(domain)
    return f"https://{normalized_domain}.atlassian.net{path}"


def test_azure_connection(organization: str, pat_token: str) -> Dict[str, Any]:
    """Test Azure DevOps connection."""
    try:
        # Encode PAT token for Basic Auth
        credentials = base64.b64encode(f":{pat_token}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
        
        # Test with a simple API call to get organization info
        url = f"https://dev.azure.com/{organization}/_apis/projects?api-version=6.0&$top=1"
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': 'Connection successful'
            }
        elif response.status_code == 401:
            return {
                'success': False,
                'error': 'Invalid PAT token or insufficient permissions'
            }
        elif response.status_code == 404:
            return {
                'success': False,
                'error': 'Organization not found'
            }
        else:
            return {
                'success': False,
                'error': f'Connection failed with status {response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Connection timeout'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Unable to connect to Azure DevOps'
        }
    except Exception as e:
        logger.error(f"Error testing Azure connection: {e}")
        return {
            'success': False,
            'error': 'Connection test failed'
        }


def test_jira_connection(domain: str, email: str, api_token: str) -> Dict[str, Any]:
    """Test Jira connection."""
    try:
        # Encode credentials for Basic Auth
        credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
        
        # Test with a simple API call to get user info
        url = build_jira_url(domain, "/rest/api/3/myself")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': 'Connection successful'
            }
        elif response.status_code == 401:
            return {
                'success': False,
                'error': 'Invalid email or API token'
            }
        elif response.status_code == 404:
            return {
                'success': False,
                'error': 'Jira domain not found'
            }
        else:
            return {
                'success': False,
                'error': f'Connection failed with status {response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Connection timeout'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Unable to connect to Jira'
        }
    except Exception as e:
        logger.error(f"Error testing Jira connection: {e}")
        return {
            'success': False,
            'error': 'Connection test failed'
        }


def fetch_azure_projects(organization: str, pat_token: str) -> List[Dict[str, Any]]:
    """Fetch projects from Azure DevOps."""
    try:
        # Encode PAT token for Basic Auth
        credentials = base64.b64encode(f":{pat_token}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
        
        # Get projects
        url = f"https://dev.azure.com/{organization}/_apis/projects?api-version=6.0"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        projects = []
        
        for project in data.get('value', []):
            # Get additional project details
            project_id = project['id']
            project_url = f"https://dev.azure.com/{organization}/_apis/projects/{project_id}?includeCapabilities=true&api-version=6.0"
            
            try:
                project_response = requests.get(project_url, headers=headers, timeout=10)
                if project_response.status_code == 200:
                    project_details = project_response.json()
                    template_name = project_details.get('capabilities', {}).get('processTemplate', {}).get('templateName', 'Unknown')
                else:
                    template_name = 'Unknown'
            except:
                template_name = 'Unknown'
            
            projects.append({
                'id': project['id'],
                'name': project['name'],
                'description': project.get('description', ''),
                'url': project.get('url', ''),
                'templateName': template_name
            })
        
        return projects
        
    except Exception as e:
        logger.error(f"Error fetching Azure projects: {e}")
        raise


def fetch_jira_projects(domain: str, email: str, api_token: str) -> List[Dict[str, Any]]:
    """Fetch projects from Jira."""
    try:
        # Encode credentials for Basic Auth
        credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
        
        # Get projects
        url = build_jira_url(domain, "/rest/api/3/project")
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        projects = []
        
        for project in data:
            projects.append({
                'id': project['id'],
                'key': project['key'],
                'name': project['name'],
                'description': project.get('description', ''),
                'url': project.get('self', ''),
                'isCompanyManaged': project.get('isPrivate', False)
            })
        
        return projects
        
    except Exception as e:
        logger.error(f"Error fetching Jira projects: {e}")
        raise
