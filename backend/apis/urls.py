from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('api/insights/', include('insightsGenerator.urls')),
    path('api/workitems/', include('devopsGenerator.urls')),
    path('api/auth/', include('authapp.urls')), 
    path('api/upload/', include('uploadFile.urls')), 
    path('api/projects/', include('projects.urls')),
    path('api/integrations/', include('integrations.urls')),
    
    # Swagger/OpenAPI URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
