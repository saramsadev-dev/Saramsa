import os
import json
import uuid
import secrets
from typing import Dict, List, Optional, Any, Tuple
from azure.cosmos import CosmosClient, PartitionKey
from django.conf import settings
from datetime import datetime, timezone
import threading
import time
import logging

logger = logging.getLogger(__name__)

class CosmosDBService:
    def __init__(self):
        self.client = None
        self.database = None
        self.containers = {}
        self.is_enabled = True
        self._init_error = None  # Store initialization error for debugging
        self._personal_prefix = "personal::"
        self._connection_pool_size = int(os.getenv('COSMOS_CONNECTION_POOL_SIZE', '10'))
        self._request_timeout = int(os.getenv('COSMOS_REQUEST_TIMEOUT', '30'))
        self._retry_total = int(os.getenv('COSMOS_RETRY_TOTAL', '3'))
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'last_reset': datetime.now()
        }
        self._stats_lock = threading.Lock()

        try:
            endpoint = settings.COSMOS_DB_CONFIG.get('endpoint')
            key = settings.COSMOS_DB_CONFIG.get('key')

            # Disable when using placeholder or missing credentials
            if (
                not endpoint
                or 'your-cosmos-account' in str(endpoint)
                or not key
                or key == 'your-cosmos-db-key'
            ):
                self.is_enabled = False
                logger.warning("Cosmos DB disabled: Invalid or missing credentials")
                return

            # Initialize client with basic configuration
            # Azure Cosmos Python SDK uses different parameter names than the old SDK
            self.client = CosmosClient(endpoint, key)
            
            self.database = self.client.get_database_client(
                settings.COSMOS_DB_CONFIG['database_name']
            )

            # Initialize container clients
            self._initialize_containers()
            logger.info(f"Cosmos DB initialized with connection pool size: {self._connection_pool_size}")
            
        except Exception as e:
            # Gracefully disable Cosmos in development/migrations if credentials invalid
            self._init_error = str(e)
            logger.error(f"CosmosDB initialization failed: {e}", exc_info=True)
            self.is_enabled = False
    
    def _initialize_containers(self):
        """Initialize container clients for all data types"""
        for container_name in settings.COSMOS_DB_CONFIG['containers'].values():
            self.containers[container_name] = self.database.get_container_client(container_name)
    
    def get_container(self, container_type: str):
        """Get container client by type"""
        if not self.is_enabled or not self.client:
            raise RuntimeError("Cosmos DB is not configured/enabled. Set valid COSMOS_DB_* environment variables.")
        
        # Ensure database exists (lazy creation - safe to call multiple times)
        try:
            self.database = self.client.create_database_if_not_exists(
                settings.COSMOS_DB_CONFIG['database_name']
            )
        except Exception as e:
            logger.error(f"Error ensuring database exists: {e}")
            raise RuntimeError(f"Failed to access/create database: {e}")
        
        container_name = settings.COSMOS_DB_CONFIG['containers'].get(container_type)
        if not container_name:
            raise ValueError(f"Unknown container type: {container_type}")

        # Return cached container client if present
        if container_name in self.containers:
            return self.containers[container_name]

        # Get the correct partition key for this container type
        partition_keys = {
            'users': '/id',
            'integrations': '/userId',
            'projects': '/userId',
            'analysis': '/projectId', 
            'uploads': '/projectId',
            'user_stories': '/projectId',
            'user_data': '/projectId',
            'password_resets': '/id',
            'insights': '/id',
            'comment_extractions': '/project_id'  # Partition by project_id for efficient queries
        }
        partition_key = partition_keys.get(container_type, '/id')  # Default to '/id' if not specified

        # Lazily create the container if it doesn't exist yet (with correct partition key)
        created = self.create_container_if_not_exists(container_type, partition_key)
        if created is not None:
            return created

        # Fallback to direct client retrieval (may still fail if missing)
        self.containers[container_name] = self.database.get_container_client(container_name)
        return self.containers[container_name]
    
    def create_database_if_not_exists(self):
        """Create database if it doesn't exist"""
        if not self.is_enabled or not self.client:
            raise RuntimeError("Cosmos DB is not configured/enabled. Set valid COSMOS_DB_* environment variables.")
        try:
            self.database = self.client.create_database_if_not_exists(
                settings.COSMOS_DB_CONFIG['database_name']
            )
        except Exception as e:
            logger.error(f"Error creating database: {e}")
    
    def create_container_if_not_exists(self, container_type: str, partition_key_path: str = "/id"):
        """Create container if it doesn't exist"""
        if not self.is_enabled or not self.database:
            raise RuntimeError("Cosmos DB is not configured/enabled. Set valid COSMOS_DB_* environment variables.")
        try:
            container_name = settings.COSMOS_DB_CONFIG['containers'][container_type]
            container = self.database.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(path=partition_key_path)
            )
            self.containers[container_name] = container
            return container
        except Exception as e:
            logger.error(f"Error creating container {container_type}: {e}")
            return None
    
    def create_all_containers(self):
        """Create all containers if they don't exist"""
        if not self.is_enabled or not self.database:
            raise RuntimeError("Cosmos DB is not configured/enabled. Set valid COSMOS_DB_* environment variables.")
        containers_config = {
            'users': '/id',
            'integrations': '/userId',
            'projects': '/userId',
            'analysis': '/projectId', 
            'uploads': '/projectId',
            'user_stories': '/projectId',
            'user_data': '/projectId',
            'password_resets': '/id',
            'insights': '/id',
            'comment_extractions': '/project_id'  # Partition by project_id for efficient queries
        }
        
        for container_type, partition_key in containers_config.items():
            self.create_container_if_not_exists(container_type, partition_key)
    
    def _record_request(self, success: bool = True):
        """Record request statistics."""
        with self._stats_lock:
            self._stats['total_requests'] += 1
            if success:
                self._stats['successful_requests'] += 1
            else:
                self._stats['failed_requests'] += 1
    
    def _record_cache_hit(self):
        """Record cache hit."""
        with self._stats_lock:
            self._stats['cache_hits'] += 1
    
    # Generic CRUD Methods for Repository Pattern
    def create_document(self, container_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic method to create a document in any container."""
        try:
            self._record_request()
            container = self.get_container(container_name)
            result = container.create_item(data)
            self._record_request(success=True)
            return result
        except Exception as e:
            self._record_request(success=False)
            logger.error(f"Error creating document in {container_name}: {e}")
            raise
    
    def get_document(self, container_name: str, item_id: str, partition_key: str) -> Optional[Dict[str, Any]]:
        """Generic method to get a document from any container."""
        try:
            self._record_request()
            container = self.get_container(container_name)
            result = container.read_item(item=item_id, partition_key=partition_key)
            self._record_request(success=True)
            return result
        except Exception as e:
            self._record_request(success=False)
            logger.error(f"Error getting document {item_id} from {container_name}: {e}")
            return None
    
    def update_document(self, container_name: str, item_id: str, partition_key: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generic method to update a document in any container."""
        try:
            self._record_request()
            container = self.get_container(container_name)
            
            # Create a copy of data to avoid mutating the input
            update_data = data.copy()
            
            # Ensure the data has the correct id
            update_data['id'] = item_id
            
            # Determine partition key path based on container type
            # Map container names to their partition key paths
            partition_key_paths = {
                'users': 'id',
                'integrations': 'userId',
                'projects': 'userId',
                'analysis': 'projectId',
                'uploads': 'projectId',
                'user_stories': 'projectId',
                'user_data': 'projectId',
                'password_resets': 'id',
                'insights': 'id'
            }
            
            # Get the partition key field name for this container
            partition_key_field = partition_key_paths.get(container_name, 'id')
            
            # Ensure partition key is set in the document
            # If the partition key field doesn't exist or is different, set it
            if partition_key_field not in update_data or update_data[partition_key_field] != partition_key:
                update_data[partition_key_field] = partition_key
            
            # Use upsert_item which will update if exists or create if not
            # Cosmos DB will automatically extract partition key from the document
            result = container.upsert_item(update_data)
            self._record_request(success=True)
            return result
        except Exception as e:
            self._record_request(success=False)
            logger.error(f"Error updating document {item_id} in {container_name}: {e}")
            return None
    
    def delete_document(self, container_name: str, item_id: str, partition_key: str) -> bool:
        """Generic method to delete a document from any container."""
        try:
            self._record_request()
            container = self.get_container(container_name)
            container.delete_item(item=item_id, partition_key=partition_key)
            self._record_request(success=True)
            return True
        except Exception as e:
            self._record_request(success=False)
            logger.error(f"Error deleting document {item_id} from {container_name}: {e}")
            return False
    
    def query_documents(self, container_name: str, query: str, parameters: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generic method to query documents from any container."""
        try:
            self._record_request()
            container = self.get_container(container_name)
            if parameters:
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
            else:
                items = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
            self._record_request(success=True)
            return items
        except Exception as e:
            self._record_request(success=False)
            logger.error(f"Error querying documents from {container_name}: {e}")
            return []

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self._stats_lock:
            total_requests = self._stats['total_requests']
            success_rate = (self._stats['successful_requests'] / total_requests * 100) if total_requests > 0 else 0
            cache_hit_rate = (self._stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_requests': total_requests,
                'successful_requests': self._stats['successful_requests'],
                'failed_requests': self._stats['failed_requests'],
                'cache_hits': self._stats['cache_hits'],
                'success_rate_percent': round(success_rate, 2),
                'cache_hit_rate_percent': round(cache_hit_rate, 2),
                'connection_pool_size': self._connection_pool_size,
                'request_timeout': self._request_timeout,
                'stats_since': self._stats['last_reset'].isoformat()
            }
    
    def reset_stats(self):
        """Reset performance statistics."""
        with self._stats_lock:
            self._stats = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'cache_hits': 0,
                'last_reset': datetime.now()
            }

    def build_personal_project_id(self, user_id: str, tenant_id: str = "default") -> str:
        """
        Return the draft project id for a user, creating the draft shell if needed.
        """
        project = self.get_or_create_draft_project(user_id=user_id, tenant_id=tenant_id)
        return project["id"]

    def is_personal_project_id(self, project_id: Optional[str]) -> bool:
        if not project_id:
            return False
        return str(project_id).startswith(self._personal_prefix)

    def save_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save user data to Cosmos DB users container"""
        try:
            # Ensure the users container exists
            self.create_container_if_not_exists('users', '/id')
            container = self.get_container('users')
            container.upsert_item(user_data)
            return user_data
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return None
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID from users container"""
        try:
            container = self.get_container('users')
            item = container.read_item(
                item=f'user_{user_id}',
                partition_key=f'user_{user_id}'
            )
            return item
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username from users container"""
        try:
            self.create_container_if_not_exists('users', '/id')
            container = self.get_container('users')
            query = "SELECT * FROM c WHERE c.type = 'user' AND c.username = @username"
            parameters = [{"name": "@username", "value": username}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email from users container"""
        try:
            self.create_container_if_not_exists('users', '/id')
            container = self.get_container('users')
            query = "SELECT * FROM c WHERE c.type = 'user' AND c.email = @email"
            parameters = [{"name": "@email", "value": email}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def save_reset_token(self, email: str, token: str, expires_at: str) -> bool:
        """Save password reset token to Cosmos DB"""
        try:
            self.create_container_if_not_exists('users', '/id')
            container = self.get_container('users')
            
            reset_token_data = {
                'id': f'reset_token_{token}',
                'type': 'password_reset_token',
                'email': email,
                'token': token,
                'expires_at': expires_at,
                'created_at': datetime.now().isoformat(),
                'used': False
            }
            
            container.upsert_item(reset_token_data)
            return True
        except Exception as e:
            logger.error(f"Error saving reset token: {e}")
            return False
    
    def get_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get password reset token from Cosmos DB"""
        try:
            self.create_container_if_not_exists('users', '/id')
            container = self.get_container('users')
            query = "SELECT * FROM c WHERE c.type = 'password_reset_token' AND c.token = @token"
            parameters = [{"name": "@token", "value": token}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error getting reset token: {e}")
            return None
    
    def mark_reset_token_used(self, token: str) -> bool:
        """Mark a reset token as used"""
        try:
            token_data = self.get_reset_token(token)
            if not token_data:
                return False
            
            token_data['used'] = True
            container = self.get_container('users')
            container.upsert_item(token_data)
            return True
        except Exception as e:
            logger.error(f"Error marking reset token as used: {e}")
            return False
    
    def save_analysis_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save analysis data to analysis container with versioning support"""
        logger.info(f"🔍 DEBUG: CosmosService.save_analysis_data called")
        logger.info(f"🔍 DEBUG: Input analysis_data keys: {list(analysis_data.keys())}")
        
        if not analysis_data.get('id'):
            import uuid as _uuid
            analysis_data['id'] = f'analysis_{_uuid.uuid4()}'
            logger.info(f"🔍 DEBUG: Generated new ID: {analysis_data['id']}")
        
        # Add versioning and temporal fields
        project_id = analysis_data.get('projectId')  # Updated to use projectId
        logger.info(f"🔍 DEBUG: Project ID from data: {project_id}")
        
        if project_id:
            # Get next version number for this project
            next_version = self._get_next_analysis_version(project_id)
            analysis_data['version'] = next_version
            analysis_data['quarter'] = self._determine_quarter(analysis_data.get('createdAt'))
            analysis_data['is_latest'] = True
            
            logger.info(f"🔍 DEBUG: Added version: {next_version}, is_latest: True")
            
            # Mark previous analyses as not latest
            self._mark_previous_analyses_not_latest(project_id)
        
        logger.info(f"🔍 DEBUG: Final analysis_data before save:")
        logger.info(f"🔍 DEBUG: - id: {analysis_data.get('id')}")
        logger.info(f"🔍 DEBUG: - projectId: {analysis_data.get('projectId')}")
        logger.info(f"🔍 DEBUG: - userId: {analysis_data.get('userId')}")
        logger.info(f"🔍 DEBUG: - type: {analysis_data.get('type')}")
        logger.info(f"🔍 DEBUG: - has original_comments: {'original_comments' in analysis_data}")
        logger.info(f"🔍 DEBUG: - has feedback: {'feedback' in analysis_data}")
        
        if 'original_comments' in analysis_data:
            logger.info(f"🔍 DEBUG: - original_comments count: {len(analysis_data['original_comments'])}")
        if 'feedback' in analysis_data:
            logger.info(f"🔍 DEBUG: - feedback count: {len(analysis_data['feedback'])}")
        
        try:
            container = self.get_container('analysis')
            logger.info(f"🔍 DEBUG: Got analysis container, about to upsert")
            
            upsert_result = container.upsert_item(analysis_data)
            logger.info(f"✅ CosmosService.save_analysis_data SUCCESS - upserted to analysis container")
            logger.info(f"🔍 DEBUG: Upsert result type: {type(upsert_result)}")
            
            return analysis_data
        except Exception as e:
            logger.error(f"❌ Error saving analysis data to Cosmos: {e}", exc_info=True)
            return None

    def get_latest_analysis_for_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get latest analysis by project_id"""
        try:
            container = self.get_container('analysis')
            query = (
                "SELECT TOP 1 * FROM c WHERE c.projectId = @project_id "
                "ORDER BY c.createdAt DESC"
            )
            params = [{"name": "@project_id", "value": project_id}]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error getting latest analysis: {e}")
            return None

    def get_latest_personal_analysis(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest personal analysis document for a user."""
        try:
            container = self.get_container('analysis')
            query = (
                "SELECT TOP 1 * FROM c WHERE c.userId = @user_id "
                "AND c.metadata.is_personal = true "
                "ORDER BY c.createdAt DESC"
            )
            params = [{"name": "@user_id", "value": user_id}]
            items = list(
                container.query_items(
                    query=query,
                    parameters=params,
                    enable_cross_partition_query=True
                )
            )
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error getting personal analysis: {e}")
            return None
    
    def get_analysis_data(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis data by ID from analysis container"""
        try:
            container = self.get_container('analysis')
            item = container.read_item(
                item=f'analysis_{analysis_id}',
                partition_key=f'analysis_{analysis_id}'
            )
            return item
        except Exception as e:
            logger.error(f"Error getting analysis data: {e}")
            return None
    
    def save_upload_data(self, upload_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save upload data to uploads container"""
        upload_data['id'] = f'upload_{upload_data.get("id", "new")}'
        upload_data['type'] = 'upload'
        
        try:
            container = self.get_container('uploads')
            container.upsert_item(upload_data)
            return upload_data
        except Exception as e:
            logger.error(f"Error saving upload data: {e}")
            return None

    def save_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save user data (comments) to user_data container"""
        # Ensure ID exists (don't modify if already provided)
        if not user_data.get('id'):
            user_data['id'] = str(uuid.uuid4())
        if 'uploaded_date' not in user_data:
            user_data['uploaded_date'] = datetime.now().isoformat()
        
        try:
            container = self.get_container('user_data')
            container.upsert_item(user_data)
            return user_data
        except Exception as e:
            logger.error(f"Error saving user data: {e}")
            return None

    def get_upload_data(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Get upload data by ID from uploads container"""
        try:
            container = self.get_container('uploads')
            item = container.read_item(
                item=f'upload_{upload_id}',
                partition_key=f'upload_{upload_id}'
            )
            return item
        except Exception as e:
            logger.error(f"Error getting upload data: {e}")
            return None

    def get_user_data_by_project(self, user_id: str, project_id: str) -> Optional[Dict[str, Any]]:
        """Get user data (comments) by user ID and project ID"""
        try:
            container = self.get_container('user_data')
            query = (
                "SELECT * FROM c WHERE c.user_id = @user_id "
                "AND c.project_id = @project_id "
                "ORDER BY c.uploaded_date DESC"
            )
            params = [
                {"name": "@user_id", "value": user_id},
                {"name": "@project_id", "value": project_id},
            ]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error querying user data: {e}")
            return None

    def get_user_data_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all user data for a specific user"""
        try:
            container = self.get_container('user_data')
            query = (
                "SELECT * FROM c WHERE c.user_id = @user_id "
                "ORDER BY c.uploaded_date DESC"
            )
            params = [{"name": "@user_id", "value": user_id}]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            return items
        except Exception as e:
            logger.error(f"Error querying user data: {e}")
            return []

    def get_latest_personal_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent personal (non-project) user data for a user."""
        try:
            container = self.get_container('user_data')
            query = (
                "SELECT TOP 1 * FROM c WHERE c.user_id = @user_id "
                "AND c.is_personal = true "
                "ORDER BY c.uploaded_date DESC"
            )
            params = [{"name": "@user_id", "value": user_id}]
            items = list(
                container.query_items(
                    query=query,
                    parameters=params,
                    enable_cross_partition_query=True
                )
            )
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error querying personal user data: {e}")
            return None
    
    def save_user_story(self, user_story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save user story data to user_stories container"""
        if not user_story_data.get('id'):
            user_story_data['id'] = f'user_story_{uuid.uuid4()}'
        user_story_data['type'] = 'user_story'
        
        try:
            container = self.get_container('user_stories')
            container.upsert_item(user_story_data)
            return user_story_data
        except Exception as e:
            logger.error(f"Error saving user story: {e}")
            return None
    
    def patch_user_story(self, user_story_id: str, partition_key: str, patch_operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Patch specific fields in a user story document"""
        try:
            container = self.get_container('user_stories')
            patched_item = container.patch_item(
                item=user_story_id,
                partition_key=partition_key,
                patch_operations=patch_operations
            )
            return patched_item
        except Exception as e:
            logger.error(f"Error patching user story {user_story_id}: {e}")
            return None
    
    def get_user_story(self, user_story_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user story by ID from user_stories container"""
        try:
            container = self.get_container('user_stories')
            item = container.read_item(
                item=user_story_id,
                partition_key=user_id
            )
            return item
        except Exception as e:
            logger.error(f"Error getting user story: {e}")
            return None

    def get_user_story_by_id(self, user_story_id: str) -> Optional[Dict[str, Any]]:
        """Get user story by ID without knowing the partition key upfront."""
        try:
            container = self.get_container('user_stories')
            query = "SELECT * FROM c WHERE c.id = @user_story_id"
            params = [{"name": "@user_story_id", "value": user_story_id}]
            items = list(container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error getting user story by id: {e}")
            return None
    
    def update_user_story(self, user_story_id: str, user_id: str, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user story by ID in user_stories container"""
        try:
            container = self.get_container('user_stories')
            
            # First, get the existing user story
            existing_item = self.get_user_story(user_story_id, user_id)
            if not existing_item:
                logger.warning(f"User story not found: {user_story_id}")
                return None
            
            # Update the user story with new data
            updated_item = {
                **existing_item,
                **updated_data,
                'updated_at': datetime.now().isoformat(),
                'updated_by': user_id
            }
            
            # Save the updated user story
            container.upsert_item(updated_item)
            return updated_item
            
        except Exception as e:
            logger.error(f"Error updating user story: {e}")
            return None

    def update_embedded_work_item(self, work_item_id: str, user_id: str, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a single embedded work item inside a user_story document."""
        try:
            container = self.get_container('user_stories')
            # Find the parent collection that contains the work item for this user
            query = (
                "SELECT * FROM c WHERE c.type = 'user_story' AND c.userId = @user_id"
            )
            params = [{"name": "@user_id", "value": user_id}]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            for item in items:
                work_items = item.get('work_items', [])
                for idx, wi in enumerate(work_items):
                    if wi.get('id') == work_item_id:
                        # Merge update into found work item
                        work_items[idx] = {**wi, **updated_data, 'updated_at': datetime.now().isoformat()}
                        item['work_items'] = work_items
                        item['updated_at'] = datetime.now().isoformat()
                        container.upsert_item(item)
                        return work_items[idx]
            return None
        except Exception as e:
            logger.error(f"Error updating embedded work item: {e}")
            return None

    def remove_embedded_work_item(self, work_item_id: str, user_id: str) -> bool:
        """Remove a single embedded work item from user_story documents."""
        try:
            result = self.delete_embedded_work_items([work_item_id], user_id)
            return result > 0
        except Exception as e:
            logger.error(f"Error removing embedded work item: {e}")
            return False

    def delete_embedded_work_items(self, work_item_ids: List[str], user_id: str) -> int:
        """Delete one or more embedded work items by id from user_story documents. Returns count deleted."""
        try:
            container = self.get_container('user_stories')
            
            # Query for user_story documents
            query = (
                "SELECT * FROM c WHERE c.type = 'user_story' "
                "AND c.userId = @user_id"
            )
            params = [{"name": "@user_id", "value": user_id}]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            
            deleted_count = 0
            for item in items:
                original = item.get('work_items', [])
                if not original:
                    continue
                    
                remaining = [wi for wi in original if wi.get('id') not in set(work_item_ids)]
                if len(remaining) != len(original):
                    deleted_count += len(original) - len(remaining)
                    item['work_items'] = remaining
                    item['updated_at'] = datetime.now().isoformat()
                    
                    # Update summary if it exists
                    if 'summary' in item and 'totalitems' in item['summary']:
                        item['summary']['totalitems'] = len(remaining)
                        
                        # Recalculate type and priority counts
                        type_counts = {}
                        priority_counts = {}
                        for wi in remaining:
                            wi_type = wi.get('type', 'Unknown')
                            wi_priority = wi.get('priority', 'Unknown')
                            type_counts[wi_type] = type_counts.get(wi_type, 0) + 1
                            priority_counts[wi_priority] = priority_counts.get(wi_priority, 0) + 1
                        
                        item['summary']['bytype'] = type_counts
                        item['summary']['bypriority'] = priority_counts
                    
                    container.upsert_item(item)
                    logger.info(f"Updated document {item['id']}: removed {len(original) - len(remaining)} work items")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting embedded work items: {e}")
            return 0

    def delete_work_items_from_user_story(self, user_story_id: str, work_item_ids: List[str], user_id: str) -> Dict[str, Any]:
        """Delete specific work items from a specific user story document."""
        try:
            container = self.get_container('user_stories')

            # Query the specific user story document (works across partitions)
            query = "SELECT * FROM c WHERE c.id = @user_story_id"
            params = [{"name": "@user_story_id", "value": user_story_id}]
            items = list(container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))

            if not items:
                return {"success": False, "error": "User story not found"}

            item = items[0]

            # Ensure this story belongs to the requesting user when a user_id is provided
            if user_id and item.get('userId') and item.get('userId') != user_id:
                return {"success": False, "error": "User story does not belong to the current user"}

            original_work_items = item.get('work_items', [])
            if not original_work_items:
                return {"success": False, "error": "No work items found in user story"}

            # Filter out the work items to delete
            work_item_ids_set = set(work_item_ids)
            remaining_work_items = [wi for wi in original_work_items if wi.get('id') not in work_item_ids_set]

            deleted_count = len(original_work_items) - len(remaining_work_items)
            if deleted_count == 0:
                return {"success": False, "error": "No work items were found to delete"}

            # Update the document
            item['work_items'] = remaining_work_items
            item['updated_at'] = datetime.now().isoformat()

            # Update summary if it exists
            if 'summary' in item:
                item['summary']['totalitems'] = len(remaining_work_items)

                # Recalculate type and priority counts
                type_counts = {}
                priority_counts = {}
                for wi in remaining_work_items:
                    wi_type = wi.get('type', 'Unknown')
                    wi_priority = wi.get('priority', 'Unknown')
                    type_counts[wi_type] = type_counts.get(wi_type, 0) + 1
                    priority_counts[wi_priority] = priority_counts.get(wi_priority, 0) + 1

                item['summary']['bytype'] = type_counts
                item['summary']['bypriority'] = priority_counts

            # Save the updated document (Cosmos will use the item's partition key)
            container.upsert_item(item)

            return {
                "success": True,
                "deleted_count": deleted_count,
                "remaining_count": len(remaining_work_items),
                "user_story_id": user_story_id
            }

        except Exception as e:
            logger.error(f"Error deleting work items from user story {user_story_id}: {e}")
            return {"success": False, "error": str(e)}
    

    # Project operations
    def save_project(self, project_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create or update a project in projects container"""
        try:
            # Ensure container exists
            self.create_container_if_not_exists('projects', '/id')
            container = self.get_container('projects')
            now_iso = self._now()
            project_data.setdefault('createdAt', now_iso)
            project_data.setdefault('updatedAt', now_iso)
            project_data.setdefault('status', 'active')
            project_data.setdefault('config_state', 'complete')
            project_data.setdefault('owner_user_id', project_data.get('userId'))
            project_data.setdefault('tenant_id', project_data.get('tenant_id', 'default'))
            project_data.setdefault('integrations', project_data.get('integrations', {'jira': None, 'azure': None}))
            container.upsert_item(project_data)
            return project_data
        except Exception as e:
            logger.error(f"Error saving project: {e}")
            return None

    def get_or_create_draft_project(self, user_id: str, tenant_id: str = "default") -> Dict[str, Any]:
        """
        Find an existing draft project for the user (within the tenant) or create one.
        """
        if not user_id:
            raise ValueError("user_id is required to create a draft project")

        self.create_container_if_not_exists('projects', '/id')
        container = self.get_container('projects')

        query = (
            "SELECT TOP 1 * FROM c WHERE c.type = 'project' "
            "AND c.status = 'draft' "
            "AND (c.owner_user_id = @user_id OR c.userId = @user_id) "
            "AND c.tenant_id = @tenant_id "
            "ORDER BY c.createdAt DESC"
        )
        params = [
            {"name": "@user_id", "value": str(user_id)},
            {"name": "@tenant_id", "value": tenant_id},
        ]

        items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
        if items:
            project = items[0]
            if not project.get("owner_user_id"):
                project["owner_user_id"] = str(user_id)
                project.setdefault("tenant_id", tenant_id)
                project.setdefault("config_state", project.get("config_state", "unconfigured"))
                project.setdefault("integrations", project.get("integrations", {'jira': None, 'azure': None}))
                project.setdefault("metadata", project.get("metadata", {}))
                container.upsert_item(project)
            return project

        project_id = f"proj_draft_{secrets.token_urlsafe(6)}"
        now_iso = self._now()
        project_doc = {
            "id": project_id,
            "type": "project",
            "name": "Draft Project",
            "description": "Workspace created automatically until integrations are configured.",
            "status": "draft",
            "config_state": "unconfigured",
            "owner_user_id": str(user_id),
            "userId": str(user_id),
            "tenant_id": tenant_id,
            "integrations": {'jira': None, 'azure': None},
            "externalLinks": [],
            "metadata": {"project_type": "draft"},
            "createdAt": now_iso,
            "updatedAt": now_iso,
            "schemaVersion": 1,
        }
        container.create_item(project_doc)
        return project_doc

    def promote_draft_project(
        self,
        project_id: str,
        user_id: str,
        *,
        tenant_id: str = "default",
        integrations: Optional[Dict[str, Any]] = None,
        config_state: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Promote a draft project to active status or update its configuration.
        """
        if not project_id:
            raise ValueError("project_id is required")

        self.create_container_if_not_exists('projects', '/id')
        container = self.get_container('projects')

        try:
            project = container.read_item(item=project_id, partition_key=project_id)
        except Exception as exc:
            raise ValueError(f"Project {project_id} not found: {exc}")

        owner = project.get("owner_user_id") or project.get("userId")
        if owner and str(owner) != str(user_id):
            raise PermissionError("You do not have permission to modify this project")

        project["status"] = "active"
        project["config_state"] = config_state or "complete"
        project["updatedAt"] = self._now()
        project["tenant_id"] = tenant_id or project.get("tenant_id") or "default"
        project["owner_user_id"] = str(user_id)
        project["userId"] = str(user_id)
        if integrations:
            merged_integrations = {**project.get("integrations", {'jira': None, 'azure': None}), **integrations}
            project["integrations"] = merged_integrations
        else:
            project.setdefault("integrations", {'jira': None, 'azure': None})
        if name:
            project["name"] = name
        if description is not None:
            project["description"] = description
        metadata = project.get("metadata", {})
        metadata["project_type"] = "standard"
        project["metadata"] = metadata

        container.upsert_item(project)
        return project

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            self.create_container_if_not_exists('projects', '/id')
            container = self.get_container('projects')
            return container.read_item(item=project_id, partition_key=project_id)
        except Exception as exc:
            logger.error(f"Error getting project {project_id}: {exc}")
            return None

    def ensure_project_context(
        self,
        project_id: Optional[str],
        user_id: str,
        tenant_id: str = "default"
    ) -> Tuple[str, Dict[str, Any], bool]:
        """
        Ensure there is a project id to operate against. Returns (project_id, project_doc, is_draft).
        """
        if project_id:
            project = self.get_project_by_id(project_id)
            is_draft = bool(project and project.get("status") == "draft")
            return project_id, project or {}, is_draft
        draft_project = self.get_or_create_draft_project(user_id=user_id, tenant_id=tenant_id)
        return draft_project["id"], draft_project, True

    def get_project_by_keys(self, owner_user_id: str, organization: str, external_project_id: str) -> Optional[Dict[str, Any]]:
        try:
            self.create_container_if_not_exists('projects', '/id')
            container = self.get_container('projects')
            query = (
                "SELECT * FROM c WHERE c.type = 'project' "
                "AND c.owner_user_id = @owner_user_id "
                "AND c.organization = @organization "
                "AND c.external_project_id = @external_project_id"
            )
            params = [
                {"name": "@owner_user_id", "value": owner_user_id},
                {"name": "@organization", "value": organization},
                {"name": "@external_project_id", "value": external_project_id},
            ]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error querying project: {e}")
            return None

    def get_projects_for_user(self, owner_user_id: str) -> List[Dict[str, Any]]:
        try:
            self.create_container_if_not_exists('projects', '/id')
            container = self.get_container('projects')
            query = (
                "SELECT * FROM c WHERE c.type = 'project' "
                "AND c.owner_user_id = @owner_user_id ORDER BY c.created_at DESC"
            )
            params = [{"name": "@owner_user_id", "value": owner_user_id}]
            return list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return []

    def update_project_last_analysis(self, project_id: str, analysis_id: str) -> bool:
        """Update project's last_analysis_id"""
        try:
            self.create_container_if_not_exists('projects', '/id')
            container = self.get_container('projects')
            item_id = project_id if project_id.startswith('project_') else f'project_{project_id}'
            item = container.read_item(item=item_id, partition_key=item_id)
            item['last_analysis_id'] = analysis_id
            item['updated_at'] = item.get('updated_at') or None
            item['updated_at'] = __import__('datetime').datetime.now().isoformat()
            container.replace_item(item=item_id, body=item)
            return True
        except Exception as e:
            logger.error(f"Error updating project last_analysis_id: {e}")
            return False
    
    def query_items(self, container_type: str, query: str, parameters: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query on specified container"""
        try:
            # Ensure container exists for robust queries
            self.create_container_if_not_exists(container_type, '/id')
            container = self.get_container(container_type)
            if parameters:
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
            else:
                items = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
            return items
        except Exception as e:
            logger.error(f"Error executing query on {container_type}: {e}")
            return []
    
    def delete_item(self, container_type: str, item_id: str, partition_key: str) -> bool:
        """Delete an item from specified container"""
        try:
            container = self.get_container(container_type)
            container.delete_item(
                item=item_id,
                partition_key=partition_key
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting item from {container_type}: {e}")
            return False
    
    def get_container_stats(self) -> Dict[str, Any]:
        """Get statistics for all containers"""
        stats = {}
        for container_type, container_name in settings.COSMOS_DB_CONFIG['containers'].items():
            try:
                container = self.get_container(container_type)
                # Get container properties
                properties = container.read()
                stats[container_type] = {
                    'id': properties['id'],
                    'partition_key': properties['partitionKey'],
                    'last_modified': properties.get('lastModified')
                }
            except Exception as e:
                stats[container_type] = {'error': str(e)}
        return stats

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID from users container"""
        try:
            container = self.get_container('users')
            item = container.read_item(
                item=f'user_{user_id}',
                partition_key=f'user_{user_id}'
            )
            return item
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    def get_user_stories_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get user stories for a specific project from user_stories container"""
        try:
            container = self.get_container('user_stories')
            query = (
                "SELECT * FROM c WHERE c.projectId = @project_id "
                "ORDER BY c.generated_at DESC"
            )
            params = [{"name": "@project_id", "value": project_id}]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            return items
        except Exception as e:
            logger.error(f"Error getting user stories by project: {e}")
            return []

    def get_user_stories_by_user_and_project(self, user_id: str, project_id: str) -> List[Dict[str, Any]]:
        """Get user stories for a specific user and project from user_stories container"""
        try:
            container = self.get_container('user_stories')
            query = (
                "SELECT * FROM c WHERE c.userId = @user_id AND c.projectId = @project_id "
                "ORDER BY c.generated_at DESC"
            )
            params = [
                {"name": "@user_id", "value": user_id},
                {"name": "@project_id", "value": project_id}
            ]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            return items
        except Exception as e:
            logger.error(f"Error getting user stories by user and project: {e}")
            return []

    def get_user_stories_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all user stories for a specific user from user_stories container"""
        try:
            container = self.get_container('user_stories')
            query = (
                "SELECT * FROM c WHERE c.userId = @user_id "
                "ORDER BY c.generated_at DESC"
            )
            params = [{"name": "@user_id", "value": user_id}]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            return items
        except Exception as e:
            logger.error(f"Error getting user stories by user: {e}")
            return []

    # Missing methods that are referenced in the views
    def get_insight(self, insight_id: str) -> Optional[Dict[str, Any]]:
        """Get insight by ID - placeholder implementation"""
        try:
            container = self.get_container('insights')
            item = container.read_item(
                item=insight_id,
                partition_key=insight_id
            )
            return item
        except Exception as e:
            logger.error(f"Error getting insight: {e}")
            return None

    def get_work_items_by_project(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get work items by project - placeholder implementation"""
        try:
            container = self.get_container('user_stories')
            query = (
                "SELECT * FROM c WHERE c.projectId = @project_id "
                "AND c.type = 'work_items' "
                "ORDER BY c.generated_at DESC"
            )
            params = [{"name": "@project_id", "value": project_id}]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            return items
        except Exception as e:
            logger.error(f"Error getting work items by project: {e}")
            return None

    def get_deep_analysis_by_project(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get deep analysis by project - placeholder implementation"""
        try:
            container = self.get_container('user_stories')
            query = (
                "SELECT * FROM c WHERE c.projectId = @project_id "
                "AND c.type = 'deep_analysis' "
                "ORDER BY c.generated_at DESC"
            )
            params = [{"name": "@project_id", "value": project_id}]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            return items
        except Exception as e:
            logger.error(f"Error getting deep analysis by project: {e}")
            return None

    def _get_next_analysis_version(self, project_id: str) -> int:
        """Get the next version number for a project's analysis"""
        try:
            container = self.get_container('analysis')
            query = (
                "SELECT TOP 1 c.version FROM c WHERE c.type = 'analysis' "
                "AND c.project_id = @project_id "
                "ORDER BY c.version DESC"
            )
            params = [{"name": "@project_id", "value": project_id}]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            if items and items[0].get('version'):
                return items[0]['version'] + 1
            return 1
        except Exception as e:
            logger.error(f"Error getting next analysis version: {e}")
            return 1

    def _determine_quarter(self, analysis_date: str) -> str:
        """Determine quarter from analysis date"""
        try:
            from datetime import datetime
            if not analysis_date:
                analysis_date = datetime.now().isoformat()
            
            date_obj = datetime.fromisoformat(analysis_date.replace('Z', '+00:00'))
            year = date_obj.year
            month = date_obj.month
            
            if month <= 3:
                return f"{year}-Q1"
            elif month <= 6:
                return f"{year}-Q2"
            elif month <= 9:
                return f"{year}-Q3"
            else:
                return f"{year}-Q4"
        except Exception as e:
            logger.error(f"Error determining quarter: {e}")
            from datetime import datetime
            now = datetime.now()
            return f"{now.year}-Q{((now.month - 1) // 3) + 1}"

    def _mark_previous_analyses_not_latest(self, project_id: str) -> None:
        """Mark all previous analyses for a project as not latest"""
        try:
            container = self.get_container('analysis')
            query = (
                "SELECT * FROM c WHERE c.type = 'analysis' "
                "AND c.project_id = @project_id "
                "AND c.is_latest = true"
            )
            params = [{"name": "@project_id", "value": project_id}]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            
            for item in items:
                item['is_latest'] = False
                container.upsert_item(item)
        except Exception as e:
            logger.error(f"Error marking previous analyses not latest: {e}")

    def get_analysis_history_for_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all analyses for a project ordered by version"""
        try:
            container = self.get_container('analysis')
            query = (
                "SELECT * FROM c WHERE c.type = 'analysis' "
                "AND c.project_id = @project_id "
                "ORDER BY c.version ASC"
            )
            params = [{"name": "@project_id", "value": project_id}]
            return list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
        except Exception as e:
            logger.error(f"Error getting analysis history: {e}")
            return []

    def get_analysis_by_quarter(self, project_id: str, quarter: str) -> Optional[Dict[str, Any]]:
        """Get analysis for a specific project and quarter"""
        try:
            container = self.get_container('analysis')
            query = (
                "SELECT TOP 1 * FROM c WHERE c.type = 'analysis' "
                "AND c.project_id = @project_id "
                "AND c.quarter = @quarter "
                "ORDER BY c.version DESC"
            )
            params = [
                {"name": "@project_id", "value": project_id},
                {"name": "@quarter", "value": quarter}
            ]
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error getting analysis by quarter: {e}")
            return None

    def get_cumulative_analysis_for_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get cumulative analysis combining all historical data for a project"""
        try:
            # Get all analyses for the project
            analyses = self.get_analysis_history_for_project(project_id)
            if not analyses:
                return None
            
            # Combine all comments from user_data
            all_comments = []
            for analysis in analyses:
                # Get user data for this analysis period
                user_data = self.get_user_data_by_project(
                    analysis.get('user_id', ''), 
                    project_id
                )
                if user_data and user_data.get('comments'):
                    all_comments.extend(user_data['comments'])
            
            if not all_comments:
                return None
            
            # Create cumulative analysis structure
            cumulative = {
                'id': f'cumulative_{project_id}_{datetime.now().strftime("%Y%m%d")}',
                'type': 'cumulative_analysis',
                'project_id': project_id,
                'analysis_date': datetime.now().isoformat(),
                'total_analyses': len(analyses),
                'total_comments': len(all_comments),
                'quarters_covered': list(set(a.get('quarter', '') for a in analyses if a.get('quarter'))),
                'latest_quarter': analyses[-1].get('quarter') if analyses else None,
                'analyses_history': analyses,
                'all_comments': all_comments
            }
            
            return cumulative
        except Exception as e:
            logger.error(f"Error getting cumulative analysis: {e}")
            return None
    
    def save_comment_extraction(self, extraction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Save a single comment extraction document.
        
        CRITICAL: Each extraction is stored separately. Never overwrites previous runs.
        Each run_id creates new documents.
        
        Args:
            extraction_data: Extraction document with run_id, comment_id, schema_version, etc.
            
        Returns:
            Saved document or None if failed
        """
        try:
            container = self.get_container('comment_extractions')
            container.create_item(extraction_data)  # Use create_item to prevent overwrites
            logger.debug(f"Saved comment extraction: {extraction_data.get('id')}")
            return extraction_data
        except Exception as e:
            logger.error(f"Error saving comment extraction: {e}", exc_info=True)
            return None
    
    def get_comment_extractions_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all comment extractions for a specific run_id.
        
        This is what aggregation services read from.
        
        Args:
            run_id: Run ID to query
            
        Returns:
            List of extraction documents
        """
        try:
            container = self.get_container('comment_extractions')
            query = (
                "SELECT * FROM c WHERE c.type = 'comment_extraction' "
                "AND c.run_id = @run_id "
                "ORDER BY c.comment_id ASC"
            )
            params = [{"name": "@run_id", "value": run_id}]
            items = list(container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logger.error(f"Error getting comment extractions by run: {e}")
            return []
    
    def get_comment_extractions_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all comment extractions for a project.
        
        Args:
            project_id: Project ID to query
            
        Returns:
            List of extraction documents
        """
        try:
            container = self.get_container('comment_extractions')
            query = (
                "SELECT * FROM c WHERE c.type = 'comment_extraction' "
                "AND c.project_id = @project_id "
                "ORDER BY c.run_id DESC, c.comment_id ASC"
            )
            params = [{"name": "@project_id", "value": project_id}]
            items = list(container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=False  # Partition by project_id, so no cross-partition needed
            ))
            return items
        except Exception as e:
            logger.error(f"Error getting comment extractions by project: {e}")
            return []
    
    def get_comment_extractions_by_project_and_run(self, project_id: str, run_id: str) -> List[Dict[str, Any]]:
        """
        Get comment extractions for a project and run_id.
        
        Args:
            project_id: Project ID
            run_id: Run ID
            
        Returns:
            List of extraction documents
        """
        try:
            container = self.get_container('comment_extractions')
            query = (
                "SELECT * FROM c WHERE c.type = 'comment_extraction' "
                "AND c.project_id = @project_id AND c.run_id = @run_id "
                "ORDER BY c.comment_id ASC"
            )
            params = [
                {"name": "@project_id", "value": project_id},
                {"name": "@run_id", "value": run_id}
            ]
            items = list(container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=False  # Partition by project_id
            ))
            return items
        except Exception as e:
            logger.error(f"Error getting comment extractions by project and run: {e}")
            return []

# Lazy initialization pattern to avoid import-time side effects
_cosmos_service = None

def get_cosmos_service() -> CosmosDBService:
    """
    Get the global Cosmos DB service instance (lazy initialization).
    Initializes only when first accessed, not at import time.
    """
    global _cosmos_service
    if _cosmos_service is None:
        _cosmos_service = CosmosDBService()
    return _cosmos_service

# Proxy object for backward compatibility with existing imports
class _CosmosServiceProxy:
    """
    Proxy that lazily initializes CosmosDBService on first attribute access.
    This allows existing code that imports 'cosmos_service' to continue working
    without changes, while avoiding import-time initialization.
    """
    def __getattr__(self, name):
        """Delegate attribute access to the actual service instance."""
        return getattr(get_cosmos_service(), name)
    
    def __call__(self, *args, **kwargs):
        """Allow calling the proxy as if it were the service (if service is callable)."""
        service = get_cosmos_service()
        if callable(service):
            return service(*args, **kwargs)
        return service

# Create proxy instance for backward compatibility
cosmos_service = _CosmosServiceProxy()