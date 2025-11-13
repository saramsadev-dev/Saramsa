from django.urls import path
from .views import (
    AnalyzeCommentsView,
    UpdateKeywordsView,
    GetUserCommentsView,
    UserStoryCreationView,
    UserStorySubmissionView,
    JiraDeepAnalysisView,
    GetUserWorkItemsView,
    GetUserStoriesView,
    GetAllUserStoriesView,
    UpdateUserStoryView,
    DeleteUserStoryView,
    DeleteUserStoryItemsView,
    WorkItemRemovalView,
    TestDeleteView,
    DeleteSingleUserStoryItemView
)

urlpatterns = [
    path('user-story-creation/', UserStoryCreationView.as_view(), name='user_story_creation'),
    path('user-story-submission/', UserStorySubmissionView.as_view(), name='user_story_submission'),
    
    # Legacy endpoints (kept for backward compatibility)
    path('analyze/', AnalyzeCommentsView.as_view(), name='analyze_comments'),
    path('jira-deep-analysis/', JiraDeepAnalysisView.as_view(), name='jira_deep_analysis'),
    
    # Utility endpoints
    path('keywords/update/', UpdateKeywordsView.as_view(), name='update_keywords'),
    path('comments/', GetUserCommentsView.as_view(), name='get_user_comments'),
    path('work-items/', GetUserWorkItemsView.as_view(), name='get_user_work_items'),
    
    # User stories endpoints - specific patterns first
    path('user-stories/', GetUserStoriesView.as_view(), name='get_user_stories'),
    path('user-stories/all/', GetAllUserStoriesView.as_view(), name='get_all_user_stories'),
    path('user-stories/delete-items/', DeleteUserStoryItemsView.as_view(), name='delete_user_story_items'),
    path('user-stories/remove-work-items/', WorkItemRemovalView.as_view(), name='remove_work_items'),
    path('user-stories/test-delete/', TestDeleteView.as_view(), name='test_delete'),
    path('user-stories/items/<str:work_item_id>/delete/', DeleteSingleUserStoryItemView.as_view(), name='delete_user_story_item'),
    
    # Generic patterns last
    path('user-stories/<str:user_story_id>/', UpdateUserStoryView.as_view(), name='update_user_story'),
    path('user-stories/<str:user_story_id>/delete/', DeleteUserStoryView.as_view(), name='delete_user_story'),
    
    # Work items endpoints (alias for user stories to maintain frontend compatibility)
    path('work-items/<str:user_story_id>/update/', UpdateUserStoryView.as_view(), name='update_work_item'),

]
