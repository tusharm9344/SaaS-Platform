import uuid
from django.utils import timezone
from django.db import models


class Application(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="applications",
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "slug"],
                name="unique_application_slug_per_organization",
            )
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.name}"
    

class ApplicationAPIKey(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )

    name = models.CharField(max_length=100, default="Default key")
    key_prefix = models.CharField(max_length=12, db_index=True)
    key_hash = models.CharField(max_length=64, unique=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.application.name} - {self.name}"
class Service(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="services",
    )

    name = models.CharField(max_length=200)
    environment = models.CharField(max_length=50, default="production")

    is_active = models.BooleanField(default=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["application", "name", "environment"],
                name="unique_service_per_app_environment",
            )
        ]

        indexes = [
            models.Index(
                fields=["application", "environment"],
                name="service_app_env_idx",
            )
        ]

    def __str__(self):
        return f"{self.application.name} - {self.name} ({self.environment})"


class DiscoveredContainer(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="discovered_containers",
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="containers",
    )

    agent = models.ForeignKey(
        "DiscoveryAgent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="containers",
    )

    container_id = models.CharField(max_length=128)
    name = models.CharField(max_length=255)
    image = models.CharField(max_length=500)
    status = models.CharField(max_length=50)
    health_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
    )

    cpu_percent = models.FloatField(null=True, blank=True)
    memory_usage = models.BigIntegerField(null=True, blank=True)
    memory_limit = models.BigIntegerField(null=True, blank=True)
    memory_percent = models.FloatField(null=True, blank=True)
    metrics_updated_at = models.DateTimeField(null=True, blank=True)

    labels = models.JSONField(default=dict, blank=True)

    is_monitored = models.BooleanField(default=True)

    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["application", "container_id"],
                name="unique_container_per_application",
            )
        ]

        indexes = [
            models.Index(
                fields=["application", "status"],
                name="container_app_status_idx",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"
class DiscoveryAgent(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="discovery_agents",
    )

    agent_id = models.CharField(max_length=64)
    hostname = models.CharField(max_length=255)

    last_heartbeat = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["application", "agent_id"],
                name="unique_discovery_agent_per_application",
            )
        ]

    def __str__(self):
        return f"{self.hostname} ({self.agent_id})"    