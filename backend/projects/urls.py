from django.urls import path
from .views import ProjectCreateView, ProjectListView, ProjectDetailView, LatestAnalysisView

urlpatterns = [
    path('', ProjectCreateView.as_view(), name='project_create'),
    path('list/', ProjectListView.as_view(), name='project_list'),
    path('<str:project_id>/', ProjectDetailView.as_view(), name='project_detail'),
    path('<str:project_id>/analysis/latest/', LatestAnalysisView.as_view(), name='project_latest_analysis'),
]


