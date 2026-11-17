import uuid

from django.db import models


class Investigation(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    incident = models.OneToOneField(
        "incidents.Incident",
        on_delete=models.CASCADE,
        related_name="investigation",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    summary = models.TextField(blank=True)

    hypotheses = models.JSONField(default=list, blank=True)

    evidence = models.JSONField(default=list, blank=True)

    recommended_actions = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Investigation for {self.incident_id} ({self.status})"
