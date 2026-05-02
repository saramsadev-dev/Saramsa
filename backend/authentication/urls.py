from django.urls import path
from .views import (
    RegisterView,
    RegisterOtpRequestView,
    ProfileMeView,
    AppTokenRefreshView,
    UserListView,
    UserDetailView,
    LoginView,
    ForgotPasswordView,
    ResetPasswordView,
    OrganizationsView,
    SwitchActiveOrganizationView,
    OrganizationMembersView,
    AdminPromptSettingsView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('register/request-otp/', RegisterOtpRequestView.as_view(), name='register_request_otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', ProfileMeView.as_view(), name='profile'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('refresh/', AppTokenRefreshView.as_view(), name='refresh'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<str:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('organizations/', OrganizationsView.as_view(), name='organizations'),
    path('organizations/active/', SwitchActiveOrganizationView.as_view(), name='organizations-active'),
    path('organizations/members/', OrganizationMembersView.as_view(), name='organizations-members'),
    path('admin/prompts/', AdminPromptSettingsView.as_view(), name='admin-prompts'),
]

