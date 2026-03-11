"""
API-level tests for review queue endpoints.

Uses Django test client to verify endpoints return correct
status codes and response shapes.
"""

import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate

from work_items.views.review_views import (
    ReviewQueueListView,
    ReviewQueueStatsView,
    CandidateApproveView,
    CandidateDismissView,
    CandidateSnoozeView,
    CandidateBatchApproveView,
)


def _mock_user():
    user = MagicMock()
    user.id = 'test-user-id'
    user.is_authenticated = True
    user.role = 'admin'
    return user


def _mock_review_service():
    svc = MagicMock()
    svc.get_pending_candidates.return_value = [
        {'id': 'c1', 'title': 'Test', 'status': 'pending', 'priority': 'high'}
    ]
    svc.get_stats.return_value = {
        'pending': 5, 'approved_this_week': 2, 'dismissed_this_week': 1, 'snoozed': 1,
    }
    svc.approve_candidate.return_value = {'id': 'c1', 'status': 'approved'}
    svc.dismiss_candidate.return_value = {'id': 'c1', 'status': 'dismissed'}
    svc.snooze_candidate.return_value = {'id': 'c1', 'status': 'snoozed'}
    svc.batch_approve.return_value = {'approved': 2, 'failed': []}
    svc.repo = MagicMock()
    svc.repo.update_candidate_status.return_value = {'id': 'c1'}
    return svc


class TestReviewQueueListAPI(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = _mock_user()
        self.view = ReviewQueueListView.as_view()

    @patch('work_items.views.review_views.get_review_service')
    def test_list_requires_project_id(self, mock_get_svc):
        request = self.factory.get('/api/work-items/review/')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        assert response.status_code == 400

    @patch('work_items.views.review_views.get_review_service')
    def test_list_returns_candidates(self, mock_get_svc):
        mock_get_svc.return_value = _mock_review_service()
        request = self.factory.get('/api/work-items/review/?project_id=proj1')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        assert response.status_code == 200


class TestReviewQueueStatsAPI(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = _mock_user()
        self.view = ReviewQueueStatsView.as_view()

    @patch('work_items.views.review_views.get_review_service')
    def test_stats_returns_data(self, mock_get_svc):
        mock_get_svc.return_value = _mock_review_service()
        request = self.factory.get('/api/work-items/review/stats/?project_id=proj1')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        assert response.status_code == 200


class TestCandidateApproveAPI(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = _mock_user()
        self.view = CandidateApproveView.as_view()

    @patch('work_items.views.review_views.get_review_service')
    def test_approve_requires_fields(self, mock_get_svc):
        request = self.factory.post('/api/work-items/review/approve/', {}, format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        assert response.status_code == 400

    @patch('work_items.views.review_views.get_review_service')
    def test_approve_succeeds(self, mock_get_svc):
        mock_get_svc.return_value = _mock_review_service()
        data = {'candidate_id': 'c1', 'project_id': 'proj1'}
        request = self.factory.post('/api/work-items/review/approve/', data, format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        assert response.status_code == 200


class TestCandidateDismissAPI(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = _mock_user()
        self.view = CandidateDismissView.as_view()

    @patch('work_items.views.review_views.get_review_service')
    def test_dismiss_requires_reason(self, mock_get_svc):
        data = {'candidate_id': 'c1', 'project_id': 'proj1'}
        request = self.factory.post('/api/work-items/review/dismiss/', data, format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        assert response.status_code == 400

    @patch('work_items.views.review_views.get_review_service')
    def test_dismiss_with_valid_reason(self, mock_get_svc):
        mock_get_svc.return_value = _mock_review_service()
        data = {'candidate_id': 'c1', 'project_id': 'proj1', 'reason': 'not_relevant'}
        request = self.factory.post('/api/work-items/review/dismiss/', data, format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        assert response.status_code == 200


class TestBatchApproveAPI(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = _mock_user()
        self.view = CandidateBatchApproveView.as_view()

    @patch('work_items.views.review_views.get_review_service')
    def test_batch_approve(self, mock_get_svc):
        mock_get_svc.return_value = _mock_review_service()
        data = {'candidate_ids': ['c1', 'c2'], 'project_id': 'proj1'}
        request = self.factory.post('/api/work-items/review/batch-approve/', data, format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        assert response.status_code == 200
