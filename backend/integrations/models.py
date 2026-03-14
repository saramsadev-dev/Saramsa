from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class Project(TimestampedModel):
    id = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(
        "authentication.UserAccount",
        on_delete=models.CASCADE,
        related_name="projects",
        db_column="user_id",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=32, default="active", db_index=True)
    external_links = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    last_analysis_id = models.CharField(max_length=128, blank=True, default="")
    last_analyzed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "projects"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status"]),
        ]


class IntegrationAccount(TimestampedModel):
    id = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(
        "authentication.UserAccount",
        on_delete=models.CASCADE,
        related_name="integration_accounts",
        db_column="user_id",
        null=True,
        blank=True,
    )
    provider = models.CharField(max_length=64, db_index=True)
    type = models.CharField(max_length=64, default="integration_account", db_index=True)
    account_name = models.CharField(max_length=255, blank=True, default="")
    credentials = models.JSONField(default=dict, blank=True)
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "integrations"
        constraints = [
            models.UniqueConstraint(fields=["user", "provider"], name="uq_integration_user_provider"),
        ]
        indexes = [
            models.Index(fields=["provider", "created_at"]),
        ]


class ProjectRole(TimestampedModel):
    id = models.CharField(max_length=128, primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_roles")
    user = models.ForeignKey("authentication.UserAccount", on_delete=models.CASCADE, related_name="project_roles")
    role = models.CharField(max_length=32, db_index=True)
    actor_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "project_roles"
        constraints = [
            models.UniqueConstraint(fields=["project", "user"], name="uq_project_user_role"),
        ]
        indexes = [
            models.Index(fields=["project", "role"]),
            models.Index(fields=["user", "role"]),
        ]


class OAuthState(TimestampedModel):
    id = models.CharField(max_length=128, primary_key=True)
    user = models.ForeignKey(
        "authentication.UserAccount",
        on_delete=models.CASCADE,
        related_name="oauth_states",
        db_column="user_id",
        null=True,
        blank=True,
    )
    provider = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, default="active", db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "oauth_states"
        indexes = [
            models.Index(fields=["provider", "status", "created_at"]),
        ]


class FeedbackSource(TimestampedModel):
    id = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(
        "authentication.UserAccount",
        on_delete=models.CASCADE,
        related_name="feedback_sources",
        db_column="user_id",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="feedback_sources",
        db_column="project_id",
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=64, default="feedbackSource", db_index=True)
    provider = models.CharField(max_length=64, db_index=True)
    account_id = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, default="active", db_index=True)
    config = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "feedback_sources"
        indexes = [
            models.Index(fields=["provider", "status", "created_at"]),
            models.Index(fields=["project", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

