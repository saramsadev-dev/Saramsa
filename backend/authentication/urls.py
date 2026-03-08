from django.urls import path
from .views import (
    RegisterView, 
    RegisterOtpRequestView,
    ProfileMeView, 
    CheckUsernameView, 
    AppTokenObtainPairView,
    AppTokenRefreshView,
    UserListView, 
    UserDetailView,
    LoginView,
    ForgotPasswordView,
    ResetPasswordView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'), #verified
    path('register/request-otp/', RegisterOtpRequestView.as_view(), name='register_request_otp'),
    path('login/', LoginView.as_view(), name='login'), #verified
    path('me/', ProfileMeView.as_view(), name='profile'),
    path('check-username', CheckUsernameView.as_view(), name='check-username'), #verified
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('token/', AppTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', AppTokenRefreshView.as_view(), name='token_refresh'),
    path('refresh/', AppTokenRefreshView.as_view(), name='refresh'),  # Frontend expects this endpoint
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<str:user_id>/', UserDetailView.as_view(), name='user-detail'),
]

