from django.urls import path
from .views import AsyncFileUploadView
from .testView import AsyncTestView

urlpatterns = [
    path('a/', AsyncFileUploadView.as_view(), name='async-file-upload'),
    path('test/', AsyncTestView.as_view(), name='async-test'),
]
