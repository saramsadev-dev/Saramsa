from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from aiCore.cosmos_service import cosmos_service
import jwt
from datetime import datetime, timedelta
from django.conf import settings
import bcrypt

class CosmosDBUserSerializer(serializers.Serializer):
    """Serializer for Cosmos DB user data"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    confirmPassword = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    
    def validate_username(self, value):
        """Check that username is unique in Cosmos DB"""
        existing_user = cosmos_service.get_user_by_username(value)
        if existing_user:
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        """Check that email is unique in Cosmos DB"""
        # Query Cosmos DB for existing email
        users = cosmos_service.query_items("users", "SELECT * FROM c WHERE c.type = 'user' AND c.email = @email", 
                                        [{"name": "@email", "value": value}])
        if users:
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate(self, attrs):
        """Validate that password and confirmPassword match"""
        password = attrs.get('password')
        confirm_password = attrs.get('confirmPassword')
        
        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({
                'confirmPassword': "Passwords don't match"
            })
        
        return attrs
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        try:
            # Convert password to bytes
            password_bytes = password.encode('utf-8')
            
            # Generate salt and hash password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Return as string for storage
            return hashed.decode('utf-8')
        except Exception as e:
            raise serializers.ValidationError(f"Password hashing failed: {str(e)}")

class CosmosDBTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer for Cosmos DB users"""
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError("Username and password are required")
        
        # Get user from Cosmos DB
        user_data = cosmos_service.get_user_by_username(username)
        if not user_data:
            raise serializers.ValidationError("Invalid credentials")
        
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
                raise serializers.ValidationError("Invalid credentials")
        except Exception as e:
            raise serializers.ValidationError("Invalid credentials")
        
        # Check if user is active
        if not user_data.get('is_active', True):
            raise serializers.ValidationError("User account is disabled")
        
        # Create custom token payload
        payload = {
            'user_id': user_data.get('id'),
            'username': user_data.get('username'),
            'email': user_data.get('email'),
            'is_staff': user_data.get('is_staff', False),
            'profile_role': user_data.get('profile', {}).get('role', 'user'),
            'exp': datetime.utcnow() + timedelta(hours=1),  # 1 hour expiry
            'iat': datetime.utcnow()
        }
        
        # Generate JWT tokens
        access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        # Create refresh token payload
        refresh_payload = {
            'user_id': user_data.get('id'),
            'username': user_data.get('username'),
            'exp': datetime.utcnow() + timedelta(days=7),  # 7 days expiry
            'iat': datetime.utcnow()
        }
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
        
        return {
            'access': access_token,
            'refresh': refresh_token,
            'user': {
                'id': user_data.get('id'),
                'username': user_data.get('username'),
                'email': user_data.get('email'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'role': user_data.get('profile', {}).get('role', 'user')
            }
        }

class CosmosDBTokenRefreshSerializer(serializers.Serializer):
    """Custom JWT refresh serializer for Cosmos DB users"""
    
    refresh = serializers.CharField()
    
    def validate(self, attrs):
        refresh_token = attrs.get('refresh')
        
        try:
            # Decode refresh token
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # Get user from Cosmos DB
            user_id = payload.get('user_id')
            username = payload.get('username')
            
            if not user_id or not username:
                raise serializers.ValidationError("Invalid refresh token")
            
            user_data = cosmos_service.get_user_by_username(username)
            if not user_data:
                raise serializers.ValidationError("User not found")
            
            # Check if user is active
            if not user_data.get('is_active', True):
                raise serializers.ValidationError("User account is disabled")
            
            # Create new access token
            new_payload = {
                'user_id': user_data.get('id'),
                'username': user_data.get('username'),
                'email': user_data.get('email'),
                'is_staff': user_data.get('is_staff', False),
                'profile_role': user_data.get('profile', {}).get('role', 'user'),
                'exp': datetime.utcnow() + timedelta(hours=1),
                'iat': datetime.utcnow()
            }
            
            new_access_token = jwt.encode(new_payload, settings.SECRET_KEY, algorithm='HS256')
            
            return {
                'access': new_access_token,
                'user': {
                    'id': user_data.get('id'),
                    'username': user_data.get('username'),
                    'email': user_data.get('email'),
                    'first_name': user_data.get('first_name'),
                    'last_name': user_data.get('last_name'),
                    'role': user_data.get('profile', {}).get('role', 'user')
                }
            }
            
        except jwt.ExpiredSignatureError:
            raise serializers.ValidationError("Refresh token has expired")
        except jwt.InvalidTokenError:
            raise serializers.ValidationError("Invalid refresh token")
        except Exception as e:
            raise serializers.ValidationError(f"Token refresh failed: {str(e)}")

class CosmosDBUserProfileSerializer(serializers.Serializer):
    """Serializer for user profile updates"""
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    
    def validate_email(self, value):
        """Check that email is unique if changed"""
        # This would need to be implemented based on your requirements
        return value

class CosmosDBPasswordChangeSerializer(serializers.Serializer):
    """Serializer for password changes"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    
    def validate_old_password(self, value):
        """Validate old password"""
        # This would need to be implemented based on your requirements
        return value
    
    def validate_new_password(self, value):
        """Validate new password"""
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")
        return value
    
    def hash_new_password(self, password):
        """Hash new password using bcrypt"""
        try:
            # Convert password to bytes
            password_bytes = password.encode('utf-8')
            
            # Generate salt and hash password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Return as string for storage
            return hashed.decode('utf-8')
        except Exception as e:
            raise serializers.ValidationError(f"Password hashing failed: {str(e)}")