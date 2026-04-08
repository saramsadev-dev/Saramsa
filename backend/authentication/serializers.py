from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from .services import get_user_service


class AppUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    confirmPassword = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    role = serializers.CharField(max_length=50, required=False, default='user')

    def validate_email(self, value):
        if get_user_service().get_user_by_email(value):
            raise serializers.ValidationError("Email already exists")
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirmPassword'):
            raise serializers.ValidationError({'confirmPassword': "Passwords don't match"})
        return attrs


class AppTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user_service = get_user_service()
        user_data = user_service.get_user_by_email(attrs['email'])

        if not user_data or not user_service._verify_password(attrs['password'], user_data.get('password', '')):
            raise serializers.ValidationError("Invalid credentials")

        if not user_data.get('is_active', True):
            raise serializers.ValidationError("User account is disabled")

        refresh = RefreshToken()
        refresh[api_settings.USER_ID_CLAIM] = user_data['id']
        refresh['email'] = user_data['email']
        refresh['is_staff'] = user_data.get('is_staff', False)
        refresh['profile_role'] = user_data.get('profile', {}).get('role', 'user')

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'role': user_data.get('profile', {}).get('role', 'user'),
            },
        }


class AppTokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs['refresh'])
        except TokenError as e:
            raise serializers.ValidationError(str(e))

        user_id = refresh.get(api_settings.USER_ID_CLAIM)
        user_service = get_user_service()
        user_data = user_service.get_user_by_id(user_id)

        if not user_data:
            raise serializers.ValidationError("User not found")
        if not user_data.get('is_active', True):
            raise serializers.ValidationError("User account is disabled")

        access = str(refresh.access_token)

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass
            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

        return {
            'access': access,
            'refresh': str(refresh),
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'role': user_data.get('profile', {}).get('role', 'user'),
            },
        }


class AppUserProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    email = serializers.EmailField(required=False)


class AppPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_new_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({'confirm_password': "Passwords don't match"})
        return attrs


class AppUserRegisterWithOtpSerializer(AppUserSerializer):
    otp = serializers.CharField(write_only=True, min_length=6, max_length=6)


class RegistrationOtpRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
