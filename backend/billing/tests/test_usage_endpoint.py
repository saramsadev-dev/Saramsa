"""Tests for GET /api/billing/usage/ — exposes current quota state."""

from django.test import TestCase
from rest_framework.test import APIClient

from billing.models import BillingProfile, UsageRecord
from billing.quota import current_period
from billing.tests.helpers import make_admin_user


class UsageEndpointTest(TestCase):
    def setUp(self):
        self.user = make_admin_user("usage-user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_returns_zero_used_and_full_limit_for_new_user(self):
        resp = self.client.get("/api/billing/usage/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        usage = body["data"]["usage"]
        self.assertEqual(usage["analysis"]["used"], 0)
        self.assertEqual(usage["analysis"]["limit"], 50)
        self.assertEqual(usage["analysis"]["remaining"], 50)
        self.assertEqual(usage["work_item_gen"]["used"], 0)
        self.assertEqual(usage["work_item_gen"]["limit"], 100)
        self.assertEqual(usage["work_item_gen"]["remaining"], 100)
        self.assertIn("period", body["data"])

    def test_returnscurrent_period_counts(self):
        UsageRecord.objects.create(
            user_id=self.user.id,
            period=current_period(),
            analysis_count=12,
            work_item_gen_count=4,
        )
        resp = self.client.get("/api/billing/usage/")
        usage = resp.json()["data"]["usage"]
        self.assertEqual(usage["analysis"]["used"], 12)
        self.assertEqual(usage["analysis"]["remaining"], 38)
        self.assertEqual(usage["work_item_gen"]["used"], 4)
        self.assertEqual(usage["work_item_gen"]["remaining"], 96)

    def test_reflects_billing_profile_overrides(self):
        BillingProfile.objects.create(
            user_id=self.user.id,
            metadata={"quota_overrides": {"analysis_limit": 10}},
        )
        resp = self.client.get("/api/billing/usage/")
        usage = resp.json()["data"]["usage"]
        self.assertEqual(usage["analysis"]["limit"], 10)
        self.assertEqual(usage["analysis"]["remaining"], 10)

    def test_remaining_clamped_to_zero_when_over_limit(self):
        UsageRecord.objects.create(
            user_id=self.user.id,
            period=current_period(),
            analysis_count=999,
        )
        resp = self.client.get("/api/billing/usage/")
        usage = resp.json()["data"]["usage"]
        self.assertEqual(usage["analysis"]["remaining"], 0)

    def test_requires_authentication(self):
        unauthed = APIClient()
        resp = unauthed.get("/api/billing/usage/")
        self.assertEqual(resp.status_code, 401)
