"""
Unit tests for cross-analysis deduplication and status defaults in DevOpsService.
"""

import pytest
from unittest.mock import MagicMock, patch

from work_items.services.devops_service import DevOpsService


@pytest.fixture
def service():
    svc = DevOpsService()
    svc.work_item_repo = MagicMock()
    return svc


def _work_item(id='wi1', title='Improve pricing', aspect_key='pricing',
               status='pending', push_status='not_pushed', **extra):
    doc = {
        'id': id,
        'title': title,
        'aspect_key': aspect_key,
        'status': status,
        'push_status': push_status,
        'type': 'Feature',
        'priority': 'high',
        'description': 'desc',
        'tags': ['customer-feedback'],
    }
    doc.update(extra)
    return doc


class TestTitleSimilarity:
    def test_exact_match(self):
        assert DevOpsService._titles_similar('improve pricing', 'improve pricing') is True

    def test_prefix_match(self):
        assert DevOpsService._titles_similar('improve pricing', 'improve pricing experience') is True

    def test_high_ratio(self):
        assert DevOpsService._titles_similar('improve pricing page', 'improve pricing pages') is True

    def test_different_titles(self):
        assert DevOpsService._titles_similar('improve pricing', 'fix login bug') is False

    def test_empty_strings(self):
        assert DevOpsService._titles_similar('', '') is False
        assert DevOpsService._titles_similar('something', '') is False


class TestNormalizeTitle:
    def test_strips_punctuation(self):
        assert DevOpsService._normalize_title('Fix: Login Bug!') == 'fix login bug'

    def test_collapses_whitespace(self):
        assert DevOpsService._normalize_title('  fix   the   bug  ') == 'fix the bug'


class TestCrossAnalysisDedup:
    def test_skips_duplicate_aspect_key(self, service):
        """New item with same aspect_key as existing should be skipped."""
        service.work_item_repo.get_all_work_items_flat.return_value = [
            _work_item('existing1', 'Improve pricing', 'pricing', status='pending'),
        ]
        new_items = [
            _work_item('new1', 'Better pricing experience', 'pricing'),
        ]
        result = service._deduplicate_against_existing(new_items, 'proj1')
        assert len(result) == 0

    def test_skips_duplicate_title(self, service):
        """New item with similar title but different aspect_key should be skipped."""
        service.work_item_repo.get_all_work_items_flat.return_value = [
            _work_item('existing1', 'Improve pricing experience', 'pricing_v2'),
        ]
        new_items = [
            _work_item('new1', 'Improve pricing experience!', 'pricing_v3'),
        ]
        result = service._deduplicate_against_existing(new_items, 'proj1')
        assert len(result) == 0

    def test_keeps_unique_items(self, service):
        """Items with different aspect_key and title should be kept."""
        service.work_item_repo.get_all_work_items_flat.return_value = [
            _work_item('existing1', 'Improve pricing', 'pricing'),
        ]
        new_items = [
            _work_item('new1', 'Fix login bug', 'login'),
        ]
        result = service._deduplicate_against_existing(new_items, 'proj1')
        assert len(result) == 1
        assert result[0]['id'] == 'new1'

    def test_ignores_dismissed_existing(self, service):
        """Dismissed existing items should not block new duplicates."""
        service.work_item_repo.get_all_work_items_flat.return_value = [
            _work_item('existing1', 'Improve pricing', 'pricing', status='dismissed'),
        ]
        new_items = [
            _work_item('new1', 'Improve pricing', 'pricing'),
        ]
        result = service._deduplicate_against_existing(new_items, 'proj1')
        assert len(result) == 1

    def test_blocks_pushed_existing(self, service):
        """Already pushed items should block duplicates."""
        service.work_item_repo.get_all_work_items_flat.return_value = [
            _work_item('existing1', 'Improve pricing', 'pricing',
                       status='approved', push_status='pushed'),
        ]
        new_items = [
            _work_item('new1', 'Improve pricing', 'pricing'),
        ]
        result = service._deduplicate_against_existing(new_items, 'proj1')
        assert len(result) == 0

    def test_no_existing_items(self, service):
        """When no existing items, all new items are kept."""
        service.work_item_repo.get_all_work_items_flat.return_value = []
        new_items = [
            _work_item('new1', 'Improve pricing', 'pricing'),
            _work_item('new2', 'Fix login', 'login'),
        ]
        result = service._deduplicate_against_existing(new_items, 'proj1')
        assert len(result) == 2

    def test_mixed_dedup(self, service):
        """Multiple new items: some duplicates, some unique."""
        service.work_item_repo.get_all_work_items_flat.return_value = [
            _work_item('existing1', 'Improve pricing', 'pricing'),
            _work_item('existing2', 'Enhance onboarding', 'onboarding'),
        ]
        new_items = [
            _work_item('new1', 'Improve pricing', 'pricing'),       # dup
            _work_item('new2', 'Fix login bug', 'login'),           # unique
            _work_item('new3', 'Better onboarding flow', 'onboarding'),  # dup
        ]
        result = service._deduplicate_against_existing(new_items, 'proj1')
        assert len(result) == 1
        assert result[0]['id'] == 'new2'


class TestDefaultStatus:
    def test_create_sets_defaults(self, service):
        """create_work_items should set status=pending and push_status=not_pushed."""
        service.work_item_repo.get_all_work_items_flat.return_value = []
        service.work_item_repo.upsert_by_id.return_value = {'id': 'doc1', 'work_items': []}

        items = [
            {'id': 'wi1', 'title': 'Test', 'type': 'Feature', 'priority': 'high',
             'description': 'desc', 'tags': []},
        ]
        service.create_work_items('user1', items, 'azure',
                                  project_id='proj1', analysis_id='analysis1')

        # Check that the items were mutated to have defaults
        assert items[0]['status'] == 'pending'
        assert items[0]['push_status'] == 'not_pushed'

    def test_create_preserves_existing_status(self, service):
        """create_work_items should not overwrite an already-set status."""
        service.work_item_repo.get_all_work_items_flat.return_value = []
        service.work_item_repo.upsert_by_id.return_value = {'id': 'doc1', 'work_items': []}

        items = [
            {'id': 'wi1', 'title': 'Test', 'type': 'Feature', 'priority': 'high',
             'description': 'desc', 'tags': [], 'status': 'approved', 'push_status': 'pushed'},
        ]
        service.create_work_items('user1', items, 'azure',
                                  project_id='proj1', analysis_id='analysis1')

        assert items[0]['status'] == 'approved'
        assert items[0]['push_status'] == 'pushed'
