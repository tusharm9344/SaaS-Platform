import uuid

from django.db import models


class ErrorEvent(models.Model):
    class Severity(models.TextChoices):
        DEBUG = "debug", "Debug"
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        CRITICAL = "critical", "Critical"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="error_events",
    )

    incident = models.ForeignKey(
        "incidents.Incident",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    message = models.TextField()
    exception_type = models.CharField(max_length=255, blank=True)
    stack_trace = models.TextField(blank=True)

    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.ERROR,
        db_index=True,
    )

    environment = models.CharField(
        max_length=50,
        default="production",
    )

    fingerprint = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
    )

    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]
        indexes = [
            models.Index(
                fields=["application", "-received_at"],
                name="event_app_received_idx",
            ),
            models.Index(
                fields=["application", "fingerprint"],
                name="event_app_fingerprint_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.exception_type or 'Runtime error'} "
            f"- {self.application.name}"
        )