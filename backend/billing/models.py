from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class BillingProfile(TimestampedModel):
    user_id = models.CharField(max_length=64, unique=True, db_index=True)
    stripe_customer_id = models.CharField(max_length=128, unique=True, blank=True, default="")
    stripe_subscription_id = models.CharField(max_length=128, unique=True, blank=True, default="")
    stripe_price_id = models.CharField(max_length=128, blank=True, default="")
    subscription_status = models.CharField(max_length=32, db_index=True, default="inactive")
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    livemode = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "billing_profiles"
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["stripe_customer_id"]),
            models.Index(fields=["stripe_subscription_id"]),
            models.Index(fields=["subscription_status"]),
        ]


class BillingWebhookEvent(TimestampedModel):
    stripe_event_id = models.CharField(max_length=128, primary_key=True)
    event_type = models.CharField(max_length=128, db_index=True)
    processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    livemode = models.BooleanField(default=False)

    class Meta:
        db_table = "billing_webhook_events"
        indexes = [
            models.Index(fields=["event_type"]),
            models.Index(fields=["processed"]),
            models.Index(fields=["created_at"]),
        ]

