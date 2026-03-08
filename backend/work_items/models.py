from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class UserStory(TimestampedModel):
    id = models.CharField(max_length=128, primary_key=True)
    project = models.ForeignKey("integrations.Project", on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    user = models.ForeignKey("authentication.UserAccount", on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    type = models.CharField(max_length=64, default="user_story", db_index=True)
    status = models.CharField(max_length=64, blank=True, default="", db_index=True)
    title = models.CharField(max_length=500, blank=True, default="")
    description = models.TextField(blank=True, default="")
    generated_at = models.DateTimeField(null=True, blank=True, db_index=True)
    work_items = models.JSONField(default=list, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "user_stories"
        indexes = [
            models.Index(fields=["project", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["type", "generated_at"]),
        ]


class WorkItemQualityRule(TimestampedModel):
    id = models.CharField(max_length=128, primary_key=True)
    project = models.ForeignKey("integrations.Project", on_delete=models.CASCADE, db_index=True)
    type = models.CharField(max_length=64, default="work_item_quality_rule", db_index=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "work_item_quality_rules"
        constraints = [
            models.UniqueConstraint(fields=["project"], name="uq_work_item_quality_rule_project"),
        ]

