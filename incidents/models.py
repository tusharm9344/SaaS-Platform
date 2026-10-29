import uuid

from django.db import models


class Incident(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        INVESTIGATING = "investigating", "Investigating"
        RESOLVED = "resolved", "Resolved"
        IGNORED = "ignored", "Ignored"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="incidents",
    )

    fingerprint = models.CharField(max_length=64)
    title = models.CharField(max_length=500)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )

    occurrence_count = models.PositiveBigIntegerField(default=0)

    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen"]
        constraints = [
            models.UniqueConstraint(
                fields=["application", "fingerprint"],
                name="unique_incident_app_fingerprint",
            )
        ]
        indexes = [
            models.Index(
                fields=["application", "status", "-last_seen"],
                name="incident_app_status_seen_idx",
            ),
        ]

    def __str__(self):
        return f"{self.application.name} - {self.title}"