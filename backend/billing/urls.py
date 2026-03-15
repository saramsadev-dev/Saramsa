from django.urls import path

from .views import (
    StripeBillingPortalSessionView,
    StripeCheckoutSessionView,
    StripeSubscriptionStatusView,
    stripe_webhook,
)

urlpatterns = [
    path("stripe/checkout-session/", StripeCheckoutSessionView.as_view(), name="stripe_checkout_session"),
    path("stripe/portal-session/", StripeBillingPortalSessionView.as_view(), name="stripe_portal_session"),
    path("stripe/subscription/", StripeSubscriptionStatusView.as_view(), name="stripe_subscription_status"),
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
]

