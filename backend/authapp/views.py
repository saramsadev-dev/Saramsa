from http import HTTPStatus
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .permissions import NoAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
import logging
from aiCore.cosmos_service import cosmos_service
import uuid
from datetime import datetime
from .serializers import (
    CosmosDBUserSerializer, 
    CosmosDBTokenObtainPairSerializer,
    CosmosDBTokenRefreshSerializer
)
from .authentication import CosmosDBJWTAuthentication, CosmosDBUser
import bcrypt

class RegisterView(generics.CreateAPIView):
    permission_classes = [NoAuthentication]
    serializer_class = CosmosDBUserSerializer
    logger = logging.getLogger(__name__)
    
    def get(self, request):
        return Response({
            "db_engine": "cosmos_db",
            "db_name": "saramsa-db",
            "container": "users",
        })

    def create(self, request, *args, **kwargs):
        try:
            self.logger.info(f"Register payload: {request.data}")
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Hash password using bcrypt
            hashed_password = serializer.hash_password(serializer.validated_data['password'])

            # Create user data for Cosmos DB
            user_id = str(uuid.uuid4())
            user_data = {
                'id': f'user_{user_id}',
                'type': 'user',
                'username': serializer.validated_data['username'],
                'email': serializer.validated_data['email'],
                'password': hashed_password,
                'first_name': serializer.validated_data.get('first_name', ''),
                'last_name': serializer.validated_data.get('last_name', ''),
                'is_active': True,
                'is_staff': False,
                'date_joined': datetime.now().isoformat(),
                'profile': {
                    'role': 'admin'
                }
            }

            # Ensure users container exists and save
            from django.conf import settings as _settings  # noqa: F401
            saved_user = cosmos_service.save_user(user_data)
            if not saved_user:
                self.logger.error("Cosmos save_user returned None")
                return Response({"error": "Failed to create user (storage)"}, status=500)

            # Generate JWT tokens for the newly created user
            from .serializers import CosmosDBTokenObtainPairSerializer
            token_serializer = CosmosDBTokenObtainPairSerializer()
            token_data = token_serializer.validate({
                'username': user_data['username'],
                'password': serializer.validated_data['password']
            })

            return Response({
                "success": True,
                "username": user_data['username'],
                "email": user_data['email'],
                "user_id": user_id,
                "message": "User created successfully",
                "access": token_data['access'],
                "refresh": token_data['refresh']
            }, status=201)

        except serializers.ValidationError as ve:
            # Return field-level validation errors with 400 status
            self.logger.info(f"Validation error during registration: {ve.detail}")
            return Response(ve.detail, status=400)

        except Exception as e:
            self.logger.exception(f"Error during registration: {e}")
            return Response({"error": str(e)}, status=500)

class CosmosDBTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view for Cosmos DB users"""
    serializer_class = CosmosDBTokenObtainPairSerializer

class CosmosDBTokenRefreshView(TokenRefreshView):
    """Custom token refresh view for Cosmos DB users"""
    serializer_class = CosmosDBTokenRefreshSerializer

class ProfileMeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CosmosDBJWTAuthentication]
    
    def get(self, request):
        # Get user from Cosmos DB using username from JWT token
        username = request.user.username
        user_data = cosmos_service.get_user_by_username(username)
        
        if not user_data:
            return Response({
                "error": "User not found"
            }, status=404)
        
        # Debug logging
        print(f"🔍 ProfileMeView - username: {username}")
        print(f"🔍 ProfileMeView - user_data keys: {list(user_data.keys())}")
        print(f"🔍 ProfileMeView - user_data['id']: {user_data.get('id')}")
        print(f"🔍 ProfileMeView - user_data['username']: {user_data.get('username')}")
        print(f"🔍 ProfileMeView - request.user.id: {request.user.id}")
        print(f"🔍 ProfileMeView - request.user.username: {request.user.username}")
        
        # Use the authenticated user's ID directly instead of querying again
        return Response({
            "user_id": request.user.id,  # Use the authenticated user's ID directly
            "username": user_data.get('username'),
            "email": user_data.get('email'),
            "first_name": user_data.get('first_name'),
            "last_name": user_data.get('last_name'),
            "company_name": user_data.get('company_name'),
            "company_url": user_data.get('company_url'),
            "avatar_url": user_data.get('avatar_url'),
            "role": user_data.get('profile', {}).get('role', 'user'),
            "date_joined": user_data.get('date_joined')
        })
    
    def patch(self, request):
        """Update basic profile fields stored in Cosmos users container.
        Supports updating: first_name, last_name, email. Fields not provided are left unchanged.
        """
        username = request.user.username
        user_doc = cosmos_service.get_user_by_username(username)
        if not user_doc:
            return Response({"error": "User not found"}, status=404)

        updatable = {"first_name", "last_name", "email", "company_name", "company_url", "avatar_url"}
        changed = False
        for key in updatable:
            if key in request.data:
                user_doc[key] = request.data.get(key, "")
                changed = True
        try:
            if changed:
                cosmos_service.save_user_data(user_doc)
        except Exception as e:
            return Response({"error": f"Failed to update profile: {str(e)}"}, status=500)
        return Response({
            "username": user_doc.get('username'),
            "email": user_doc.get('email'),
            "first_name": user_doc.get('first_name'),
            "last_name": user_doc.get('last_name'),
        })
    
class CheckUsernameView(APIView):
    permission_classes = [NoAuthentication]
    
    def get(self, request):
        username = request.query_params.get('username', '').strip()
        if not username:
            return Response(
                {"error": "Username parameter is required"}
            )
        
        # Check length
        if len(username) < 3:
            return Response({
                "available": False,
                "message": "Username must be at least 3 characters"
            })
        
        # Check character validity
        import re
        if not re.match(r'^[\w.@+-]+\Z', username):
            return Response({
                "available": False,
                "message": "Username can only contain letters, numbers, and @/./+/-/_ characters"
            })
        
        # Check availability in Cosmos DB only
        username_exists = cosmos_service.get_user_by_username(username) is not None
        
        return Response({
            "available": not username_exists,
            "message": "Username is already taken" if username_exists else "Username is available"
        })

class UserListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CosmosDBJWTAuthentication]
    
    def get(self, request):
        """Get all users from Cosmos DB"""
        try:
            users = cosmos_service.query_items("users", "SELECT * FROM c WHERE c.type = 'user'")
            # Remove password hashes from response for security
            for user in users:
                if 'password' in user:
                    user['password'] = '***HIDDEN***'
            return Response({
                "users": users,
                "count": len(users)
            })
        except Exception as e:
            return Response({
                "error": f"Failed to fetch users: {str(e)}"
            }, status=500)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CosmosDBJWTAuthentication]
    
    def get(self, request, user_id):
        """Get specific user by ID from Cosmos DB"""
        try:
            user_data = cosmos_service.get_user_by_id(user_id)
            if not user_data:
                return Response({
                    "error": "User not found"
                }, status=404)
            
            # Remove password hash from response for security
            if 'password' in user_data:
                user_data['password'] = '***HIDDEN***'
            
            return Response(user_data)
        except Exception as e:
            return Response({
                "error": f"Failed to fetch user: {str(e)}"
            }, status=500)

class LoginView(APIView):
    permission_classes = [NoAuthentication]
    
    def post(self, request):
        """Custom login endpoint for Cosmos DB users"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                "error": "Username and password are required"
            }, status=400)
        
        try:
            # Get user from Cosmos DB
            user_data = cosmos_service.get_user_by_username(username)
            if not user_data:
                return Response({
                    "error": "Invalid credentials"
                }, status=401)
            
            # Check password using bcrypt
            stored_password = user_data.get('password', '')
            try:
                # Convert stored password to bytes if it's a string
                if isinstance(stored_password, str):
                    stored_password = stored_password.encode('utf-8')
                
                # Convert input password to bytes
                password_bytes = password.encode('utf-8')
                
                # Use bcrypt to verify password
                if not bcrypt.checkpw(password_bytes, stored_password):
                    return Response({
                        "error": "Invalid credentials"
                    }, status=401)
            except Exception as e:
                return Response({
                    "error": "Invalid credentials"
                }, status=401)
            
            # Check if user is active
            if not user_data.get('is_active', True):
                return Response({
                    "error": "User account is disabled"
                }, status=401)
            
            # Generate JWT token
            from .serializers import CosmosDBTokenObtainPairSerializer
            serializer = CosmosDBTokenObtainPairSerializer()
            token_data = serializer.validate({
                'username': username,
                'password': password
            })
            
            return Response(token_data)
            
        except Exception as e:
            return Response({
                "error": f"Login failed: {str(e)}"
            }, status=500)
