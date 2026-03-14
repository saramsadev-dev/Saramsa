"""Tests for the weekly digest service."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.test import TestCase

from authentication.models import UserAccount
from feedback_analysis.models import Analysis, Insight
from feedback_analysis.services.digest_service import (
    _week_bounds,
    gather_project_stats,
    gather_user_digest,
    run_weekly_digest,
)
from integrations.models import Project


class WeekBoundsTest(TestCase):
    def test_returns_7_day_window(self):
        now = datetime(2026, 3, 13, 9, 0, tzinfo=timezone.utc)
        since, until = _week_bounds(now)
        self.assertEqual(until, now)
        self.assertEqual(since, now - timedelta(days=7))


class GatherProjectStatsTest(TestCase):
    def setUp(self):
        self.user = UserAccount.objects.create(
            id=uuid.uuid4().hex[:16],
            username="testuser",
            email="test@example.com",
            password="hashed",
        )
        self.project = Project.objects.create(
            id=uuid.uuid4().hex[:16],
            user=self.user,
            name="Test Project",
        )
        self.now = datetime.now(timezone.utc)
        self.since = self.now - timedelta(days=7)

    def test_counts_analyses_in_window(self):
        Analysis.objects.create(
            id=uuid.uuid4().hex[:16],
            project=self.project,
            user=self.user,
            created_at=self.now - timedelta(days=2),
        )
        # Outside window
        Analysis.objects.create(
            id=uuid.uuid4().hex[:16],
            project=self.project,
            user=self.user,
            created_at=self.now - timedelta(days=10),
        )
        stats = gather_project_stats(self.project, self.since, self.now)
        self.assertEqual(stats["analyses_completed"], 1)

    def test_counts_insights(self):
        Insight.objects.create(
            id=uuid.uuid4().hex[:16],
            project=self.project,
            user=self.user,
            created_at=self.now - timedelta(days=1),
        )
        stats = gather_project_stats(self.project, self.since, self.now)
        self.assertEqual(stats["insights_generated"], 1)


class GatherUserDigestTest(TestCase):
    def setUp(self):
        self.user = UserAccount.objects.create(
            id=uuid.uuid4().hex[:16],
            username="digestuser",
            email="digest@example.com",
            password="hashed",
            first_name="Alice",
        )
        self.project = Project.objects.create(
            id=uuid.uuid4().hex[:16],
            user=self.user,
            name="Active Project",
        )
        self.now = datetime.now(timezone.utc)
        self.since = self.now - timedelta(days=7)

    def test_skips_zero_activity_projects(self):
        digest = gather_user_digest(self.user, self.since, self.now)
        self.assertEqual(len(digest["projects"]), 0)

    def test_includes_active_projects(self):
        Analysis.objects.create(
            id=uuid.uuid4().hex[:16],
            project=self.project,
            user=self.user,
            created_at=self.now - timedelta(days=1),
        )
        digest = gather_user_digest(self.user, self.since, self.now)
        self.assertEqual(len(digest["projects"]), 1)
        self.assertEqual(digest["totals"]["analyses_completed"], 1)
        self.assertEqual(digest["first_name"], "Alice")


class RunWeeklyDigestTest(TestCase):
    def setUp(self):
        self.user = UserAccount.objects.create(
            id=uuid.uuid4().hex[:16],
            username="weeklyuser",
            email="weekly@example.com",
            password="hashed",
        )
        self.project = Project.objects.create(
            id=uuid.uuid4().hex[:16],
            user=self.user,
            name="Weekly Project",
        )
        now = datetime.now(timezone.utc)
        Analysis.objects.create(
            id=uuid.uuid4().hex[:16],
            project=self.project,
            user=self.user,
            created_at=now - timedelta(days=1),
        )

    @patch("feedback_analysis.services.digest_service.send_digest_email", return_value=True)
    def test_sends_to_active_users(self, mock_send):
        result = run_weekly_digest()
        self.assertEqual(result["sent"], 1)
        mock_send.assert_called_once()

    @patch("feedback_analysis.services.digest_service.send_digest_email", return_value=True)
    def test_respects_opt_out(self, mock_send):
        self.user.extra = {"weekly_digest_enabled": False}
        self.user.save(update_fields=["extra"])
        result = run_weekly_digest()
        self.assertEqual(result["sent"], 0)
        self.assertEqual(result["skipped"], 1)
        mock_send.assert_not_called()
