from django.urls import path
from .views import (
    RegisterView, 
    ProfileMeView, 
    CheckUsernameView, 
    CosmosDBTokenObtainPairView,
    CosmosDBTokenRefreshView,
    UserListView, 
    UserDetailView,
    LoginView,
    ForgotPasswordView,
    ResetPasswordView
)
from .credit_views import (
    CreditBalanceView,
    CreditTransactionsView,
    AdminAddCreditsView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'), #verified
    path('login/', LoginView.as_view(), name='login'), #verified
    path('me/', ProfileMeView.as_view(), name='profile'),
    path('check-username', CheckUsernameView.as_view(), name='check-username'), #verified
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('token/', CosmosDBTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CosmosDBTokenRefreshView.as_view(), name='token_refresh'),
    path('refresh/', CosmosDBTokenRefreshView.as_view(), name='refresh'),  # Frontend expects this endpoint
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<str:user_id>/', UserDetailView.as_view(), name='user-detail'),
    # Credit management endpoints
    path('credits/balance/', CreditBalanceView.as_view(), name='credit-balance'),
    path('credits/transactions/', CreditTransactionsView.as_view(), name='credit-transactions'),
    path('credits/admin/add/', AdminAddCreditsView.as_view(), name='admin-add-credits'),
]
