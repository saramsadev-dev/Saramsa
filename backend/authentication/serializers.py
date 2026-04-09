from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .services import get_user_service
import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
import bcrypt

class AppUserSerializer(serializers.Serializer):
    """Serializer for PostgreSQL user data"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    confirmPassword = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    role = serializers.CharField(max_length=50, required=False, default='user')
    
    def validate_email(self, value):
        """Check that email is unique using service layer"""
        user_service = get_user_service()
        existing_user = user_service.get_user_by_email(value)
        if existing_user:
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

class AppTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer for PostgreSQL users"""
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Email and password are required")
        
        # Get user using service layer
        user_service = get_user_service()
        user_data = user_service.get_user_by_email(email)
        if not user_data:
            raise serializers.ValidationError("Invalid credentials")
        
        # Verify password using service
        if not user_service._verify_password(password, user_data.get('password', '')):
            raise serializers.ValidationError("Invalid credentials")
        
        # Check if user is active
        if not user_data.get('is_active', True):
            raise serializers.ValidationError("User account is disabled")
        
        # Create custom token payload (user_id is the stable subject for API auth)
        payload = {
            'user_id': user_data.get('id'),
            'email': user_data.get('email'),
            'is_staff': user_data.get('is_staff', False),
            'profile_role': user_data.get('profile', {}).get('role', 'user'),
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),  # 1 hour expiry
            'iat': int(datetime.now(timezone.utc).timestamp())
        }

        # Generate JWT tokens
        access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        # Create refresh token payload
        refresh_payload = {
            'user_id': user_data.get('id'),
            'exp': int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp()),  # 7 days expiry
            'iat': int(datetime.now(timezone.utc).timestamp())
        }
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
        
        return {
            'access': access_token,
            'refresh': refresh_token,
            'user': {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'role': user_data.get('profile', {}).get('role', 'user')
            }
        }

class AppTokenRefreshSerializer(serializers.Serializer):
    """Custom JWT refresh serializer for PostgreSQL users"""
    
    refresh = serializers.CharField()
    
    def validate(self, attrs):
        refresh_token = attrs.get('refresh')
        
        try:
            # Decode refresh token
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # Get user from PostgreSQL
            user_id = payload.get('user_id')
            
            if not user_id:
                raise serializers.ValidationError("Invalid refresh token")
            
            user_service = get_user_service()
            user_data = user_service.get_user_by_id(user_id)
            if not user_data:
                raise serializers.ValidationError("User not found")
            
            # Check if user is active
            if not user_data.get('is_active', True):
                raise serializers.ValidationError("User account is disabled")
            
            # Create new access token
            new_payload = {
                'user_id': user_data.get('id'),
                'email': user_data.get('email'),
                'is_staff': user_data.get('is_staff', False),
                'profile_role': user_data.get('profile', {}).get('role', 'user'),
                'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
                'iat': int(datetime.now(timezone.utc).timestamp())
            }
            
            new_access_token = jwt.encode(new_payload, settings.SECRET_KEY, algorithm='HS256')
            
            return {
                'access': new_access_token,
                'user': {
                    'id': user_data.get('id'),
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

class AppUserProfileSerializer(serializers.Serializer):
    """Serializer for user profile updates"""
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    
    def validate_email(self, value):
        """Check that email is unique if changed"""
        # This would need to be implemented based on your requirements
        return value

class AppPasswordChangeSerializer(serializers.Serializer):
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

class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password request"""
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for password reset"""
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    
    def validate(self, attrs):
        """Validate that passwords match"""
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': "Passwords don't match"
            })
        
        return attrs
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        try:
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        except Exception as e:
            raise serializers.ValidationError(f"Password hashing failed: {str(e)}")


class AppUserRegisterWithOtpSerializer(AppUserSerializer):
    """Serializer for registration with OTP."""
    otp = serializers.CharField(write_only=True, min_length=6, max_length=6)


class RegistrationOtpRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

