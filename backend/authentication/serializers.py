from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.hashers import make_password
from .services import get_user_service


class AppUserSerializer(serializers.Serializer):
    """Serializer for PostgreSQL user data"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    confirmPassword = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    role = serializers.CharField(max_length=50, required=False, default='user')

    def validate_email(self, value):
        user_service = get_user_service()
        if user_service.get_user_by_email(value):
            raise serializers.ValidationError("Email already exists")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirmPassword')
        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({'confirmPassword': "Passwords don't match"})
        return attrs

    def hash_password(self, password):
        return make_password(password)


class AppTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Issue simplejwt tokens for PostgreSQL users."""

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required")

        user_service = get_user_service()
        user_data = user_service.get_user_by_email(email)
        if not user_data:
            raise serializers.ValidationError("Invalid credentials")

        if not user_service._verify_password(password, user_data.get('password', '')):
            raise serializers.ValidationError("Invalid credentials")

        if not user_data.get('is_active', True):
            raise serializers.ValidationError("User account is disabled")

        # Use simplejwt RefreshToken — tokens are tracked by the blacklist
        refresh = RefreshToken()
        refresh['user_id'] = user_data.get('id')
        refresh['email'] = user_data.get('email')
        refresh['is_staff'] = user_data.get('is_staff', False)
        refresh['profile_role'] = user_data.get('profile', {}).get('role', 'user')

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'role': user_data.get('profile', {}).get('role', 'user'),
            }
        }


class AppTokenRefreshSerializer(serializers.Serializer):
    """Refresh access token using simplejwt — handles rotation and blacklisting."""

    refresh = serializers.CharField()

    def validate(self, attrs):
        try:
            old_refresh = RefreshToken(attrs['refresh'])
        except TokenError:
            raise serializers.ValidationError("Invalid or expired refresh token")

        user_id = old_refresh.get('user_id')
        if not user_id:
            raise serializers.ValidationError("Invalid refresh token")

        user_service = get_user_service()
        user_data = user_service.get_user_by_id(user_id)
        if not user_data:
            raise serializers.ValidationError("User not found")

        if not user_data.get('is_active', True):
            raise serializers.ValidationError("User account is disabled")

        # Blacklist the old refresh token (skip if user model incompatible)
        try:
            old_refresh.blacklist()
        except Exception:
            pass  # OutstandingToken FK expects numeric user_id; our IDs are strings

        new_refresh = RefreshToken()
        new_refresh['user_id'] = user_data.get('id')
        new_refresh['email'] = user_data.get('email')
        new_refresh['is_staff'] = user_data.get('is_staff', False)
        new_refresh['profile_role'] = user_data.get('profile', {}).get('role', 'user')

        return {
            'access': str(new_refresh.access_token),
            'user': {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'role': user_data.get('profile', {}).get('role', 'user'),
            }
        }

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

