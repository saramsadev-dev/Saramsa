from django.urls import path

from .views import (
    StripeBillingPortalSessionView,
    StripeCheckoutSessionView,
    StripeSubscriptionStatusView,
    StripeCancelSubscriptionView,
    StripeResumeSubscriptionView,
    UsageView,
    stripe_webhook,
)

urlpatterns = [
    path("usage/", UsageView.as_view(), name="billing_usage"),
    path("stripe/checkout-session/", StripeCheckoutSessionView.as_view(), name="stripe_checkout_session"),
    path("stripe/portal-session/", StripeBillingPortalSessionView.as_view(), name="stripe_portal_session"),
    path("stripe/subscription/", StripeSubscriptionStatusView.as_view(), name="stripe_subscription_status"),
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
    path("cancel-subscription/", StripeCancelSubscriptionView.as_view(), name="billing_cancel_subscription"),
    path("resume-subscription/", StripeResumeSubscriptionView.as_view(), name="billing_resume_subscription"),
]

