from django.test import TestCase

from authentication.models import UserAccount
from billing.models import BillingProfile
from billing.services import StripeBillingService
from integrations.models import Organization, OrganizationMembership


def _make_user(user_id: str, email: str, active_org_id: str) -> UserAccount:
    return UserAccount.objects.create(
        id=user_id,
        email=email,
        password="x",
        first_name="Billing",
        last_name="User",
        profile={"role": "user", "active_organization_id": active_org_id},
    )


class WorkspaceScopedBillingTest(TestCase):
    def test_subscription_status_is_shared_by_active_workspace(self) -> None:
        org = Organization.objects.create(id="org-bill", name="Acme", slug="acme")
        admin_one = _make_user("u1", "one@example.com", org.id)
        admin_two = _make_user("u2", "two@example.com", org.id)
        OrganizationMembership.objects.create(id="m1", organization=org, user=admin_one, role="owner", status="active")
        OrganizationMembership.objects.create(id="m2", organization=org, user=admin_two, role="admin", status="active")

        BillingProfile.objects.create(
            user_id=admin_one.id,
            organization_id=org.id,
            stripe_subscription_id="sub_123",
            subscription_status="active",
        )

        status = StripeBillingService().get_subscription_status(admin_two.id)
        self.assertTrue(status["has_subscription"])
        self.assertEqual(status["status"], "active")

    def test_profile_creation_is_per_workspace_not_per_user(self) -> None:
        org = Organization.objects.create(id="org-scope", name="Scope", slug="scope")
        admin_one = _make_user("u1", "one@example.com", org.id)
        admin_two = _make_user("u2", "two@example.com", org.id)
        OrganizationMembership.objects.create(id="m1", organization=org, user=admin_one, role="owner", status="active")
        OrganizationMembership.objects.create(id="m2", organization=org, user=admin_two, role="admin", status="active")

        service = StripeBillingService()
        profile_one = service._get_or_create_profile(admin_one.id)
        profile_two = service._get_or_create_profile(admin_two.id)

        self.assertEqual(profile_one.id, profile_two.id)
        self.assertEqual(BillingProfile.objects.filter(organization_id=org.id).count(), 1)
