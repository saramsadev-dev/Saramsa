from django.urls import path
from .views import (
    RegisterView, 
    ProfileMeView, 
    CheckUsernameView, 
    CosmosDBTokenObtainPairView,
    CosmosDBTokenRefreshView,
    UserListView, 
    UserDetailView,
    LoginView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'), #verified
    path('login/', LoginView.as_view(), name='login'), #verified
    path('me/', ProfileMeView.as_view(), name='profile'),
    path('check-username', CheckUsernameView.as_view(), name='check-username'), #verified
    path('token/', CosmosDBTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CosmosDBTokenRefreshView.as_view(), name='token_refresh'),
    path('refresh/', CosmosDBTokenRefreshView.as_view(), name='refresh'),  # Frontend expects this endpoint
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<str:user_id>/', UserDetailView.as_view(), name='user-detail'),
]
