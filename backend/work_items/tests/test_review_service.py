"""
Unit tests for the review queue service.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from work_items.services.review_service import ReviewService, VALID_DISMISS_REASONS


@pytest.fixture
def mock_repo():
    with patch('work_items.services.review_service.WorkItemRepository') as MockRepo:
        repo = MockRepo.return_value
        yield repo


@pytest.fixture
def service(mock_repo):
    svc = ReviewService()
    svc.repo = mock_repo
    return svc


def _candidate(id='c1', status='pending', priority='high', **extra):
    doc = {
        'id': id,
        'projectId': 'proj1',
        'title': f'Candidate {id}',
        'description': 'desc',
        'priority': priority,
        'status': status,
        'createdAt': '2025-01-01T00:00:00Z',
    }
    doc.update(extra)
    return doc


class TestGetPending:
    def test_returns_only_pending(self, service, mock_repo):
        mock_repo.get_candidates_by_status.return_value = [
            _candidate('c1', 'pending'),
            _candidate('c2', 'pending'),
        ]
        result = service.get_pending_candidates('proj1')
        mock_repo.get_candidates_by_status.assert_called_once_with('proj1', 'pending')
        assert len(result) == 2

    def test_sorted_by_priority(self, service, mock_repo):
        mock_repo.get_candidates_by_status.return_value = [
            _candidate('c1', priority='medium'),
            _candidate('c2', priority='critical'),
            _candidate('c3', priority='high'),
        ]
        result = service.get_pending_candidates('proj1')
        priorities = [c['priority'] for c in result]
        assert priorities == ['critical', 'high', 'medium']


class TestApprove:
    def test_sets_status(self, service, mock_repo):
        mock_repo.update_candidate_status.return_value = _candidate('c1', status='approved')
        result = service.approve_candidate('c1', 'user1', 'proj1')
        call_args = mock_repo.update_candidate_status.call_args
        updates = call_args[0][2]
        assert updates['status'] == 'approved'
        assert 'status_changed_at' in updates

    def test_with_edits(self, service, mock_repo):
        mock_repo.update_candidate_status.return_value = _candidate('c1', status='approved', title='New Title')
        service.approve_candidate('c1', 'user1', 'proj1', edits={'title': 'New Title'})
        updates = mock_repo.update_candidate_status.call_args[0][2]
        assert updates['title'] == 'New Title'
        assert updates['status'] == 'approved'


class TestDismiss:
    def test_requires_reason(self, service, mock_repo):
        with pytest.raises(ValueError):
            service.dismiss_candidate('c1', 'user1', 'proj1', reason='')
        mock_repo.update_candidate_status.assert_not_called()

    def test_invalid_reason(self, service, mock_repo):
        with pytest.raises(ValueError, match="Invalid dismiss reason"):
            service.dismiss_candidate('c1', 'user1', 'proj1', reason='yolo')

    def test_valid_dismiss(self, service, mock_repo):
        mock_repo.update_candidate_status.return_value = _candidate('c1', status='dismissed')
        service.dismiss_candidate('c1', 'user1', 'proj1', reason='not_relevant')
        updates = mock_repo.update_candidate_status.call_args[0][2]
        assert updates['status'] == 'dismissed'
        assert updates['dismiss_reason'] == 'not_relevant'


class TestSnooze:
    def test_sets_future_date(self, service, mock_repo):
        mock_repo.update_candidate_status.return_value = _candidate('c1', status='snoozed')
        service.snooze_candidate('c1', 'user1', 'proj1', snooze_days=7)
        updates = mock_repo.update_candidate_status.call_args[0][2]
        assert updates['status'] == 'snoozed'
        snooze_until = datetime.fromisoformat(updates['snooze_until'])
        assert snooze_until > datetime.now(timezone.utc) + timedelta(days=6)


class TestUnsnooze:
    def test_unsnooze_expired(self, service, mock_repo):
        expired = _candidate('c1', status='snoozed',
                             snooze_until=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat())
        mock_repo.get_expired_snoozed_candidates.return_value = [expired]
        mock_repo.update_candidate_status.return_value = _candidate('c1', status='pending')
        count = service.unsnooze_expired()
        assert count == 1
        updates = mock_repo.update_candidate_status.call_args[0][2]
        assert updates['status'] == 'pending'

    def test_skips_future(self, service, mock_repo):
        mock_repo.get_expired_snoozed_candidates.return_value = []
        count = service.unsnooze_expired()
        assert count == 0


class TestMerge:
    def test_merge_candidates(self, service, mock_repo):
        mock_repo.update_candidate_status.return_value = _candidate('c1', status='merged')
        mock_repo.get_candidate_by_id.return_value = _candidate('c2')
        result = service.merge_candidates('c1', 'c2', 'user1', 'proj1')
        source_updates = mock_repo.update_candidate_status.call_args[0][2]
        assert source_updates['status'] == 'merged'
        assert source_updates['merged_into'] == 'c2'
        assert result['id'] == 'c2'


class TestBatchApprove:
    def test_batch_approve(self, service, mock_repo):
        mock_repo.update_candidate_status.return_value = _candidate(status='approved')
        result = service.batch_approve(['c1', 'c2', 'c3'], 'user1', 'proj1')
        assert result['approved'] == 3
        assert result['failed'] == []

    def test_invalid_id_returns_error(self, service, mock_repo):
        mock_repo.update_candidate_status.side_effect = ValueError("Not found")
        result = service.batch_approve(['bad_id'], 'user1', 'proj1')
        assert result['approved'] == 0
        assert len(result['failed']) == 1
