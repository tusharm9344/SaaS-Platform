import hashlib
import re

from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from incidents.models import Incident
def generate_fingerprint(event):
    """
    Generate a stable fingerprint for similar error events.
    Normalize dynamic values so recurring errors are grouped.
    """

    message = event.message or ""

    # Normalize UUIDs.
    message = re.sub(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{12}\b",
        "<UUID>",
        message,
    )

    # Normalize long hexadecimal identifiers.
    message = re.sub(
        r"\b[0-9a-fA-F]{16,}\b",
        "<HEX>",
        message,
    )

    # Normalize numbers.
    message = re.sub(
        r"\b\d+\b",
        "<NUMBER>",
        message,
    )

    fingerprint_input = "|".join([
        str(event.application_id),
        str(event.service_id or ""),
        event.exception_type or "",
        message,
    ])

    return hashlib.sha256(
        fingerprint_input.encode("utf-8")
    ).hexdigest()


@transaction.atomic
@transaction.atomic
def group_error_event(event):
    """
    Group similar error events into incidents.
    Update existing incidents instead of creating duplicates.
    """

    fingerprint = generate_fingerprint(event)

    incident, created = Incident.objects.get_or_create(
        service=event.service,
        fingerprint=fingerprint,
        defaults={
            "application": event.application,
            "title": (
                f"{event.exception_type or 'Runtime error'}: "
                f"{event.message}"
            )[:500],
            "first_seen": event.occurred_at,
            "last_seen": event.occurred_at,
            "occurrence_count": 1,
        },
    )

    if not created:
        Incident.objects.filter(pk=incident.pk).update(
            last_seen=event.occurred_at,
            occurrence_count=F("occurrence_count") + 1,
        )

        # Refresh the Python object with the updated database values.
        incident.refresh_from_db()

    event.fingerprint = fingerprint
    event.incident = incident
    event.save(update_fields=["fingerprint", "incident"])

    return incident
@transaction.atomic
def detect_container_anomalies(container):
    """
    Detect CPU, memory, health, and container-state anomalies.
    Manage incident creation, updates, recovery, and reopening.
    """

    thresholds = {
        "high_cpu": (
            container.cpu_percent,
            80,
            "High CPU usage",
        ),
        "high_memory": (
            container.memory_percent,
            85,
            "High memory usage",
        ),
    }

    def get_fingerprint(anomaly_type):
        fingerprint_input = (
            f"{container.application_id}|"
            f"{container.service_id}|"
            f"{container.container_id}|"
            f"{anomaly_type}"
        )

        return hashlib.sha256(
            fingerprint_input.encode("utf-8")
        ).hexdigest()

    def resolve_anomaly(anomaly_type):
        Incident.objects.filter(
            service=container.service,
            fingerprint=get_fingerprint(anomaly_type),
            status__in=[
                Incident.Status.OPEN,
                Incident.Status.INVESTIGATING,
            ],
        ).update(
            status=Incident.Status.RESOLVED
        )

    def create_or_update_incident(anomaly_type, title, observed_at=None):
        observed_at = observed_at or timezone.now()
        fingerprint = get_fingerprint(anomaly_type)

        incident, created = Incident.objects.get_or_create(
            service=container.service,
            fingerprint=fingerprint,
            defaults={
                "application": container.application,
                "title": title[:500],
                "first_seen": observed_at,
                "last_seen": observed_at,
                "occurrence_count": 1,
            },
        )

        if created:
            return

        updates = {
            "title": title[:500],
            "last_seen": observed_at,
        }

        # Reopen a resolved incident when the anomaly returns.
        if incident.status == Incident.Status.RESOLVED:
            updates["status"] = Incident.Status.OPEN
            updates["occurrence_count"] = (
                F("occurrence_count") + 1
            )

        Incident.objects.filter(
            pk=incident.pk
        ).update(**updates)

    # A removed container is not proof of recovery.
    if container.status == "removed":
        return

    # Detect stopped or dead containers.
    if container.status in ["exited", "stopped", "dead"]:
        create_or_update_incident(
            "container_stopped",
            f"Container stopped: {container.name}",
        )

        # CPU and memory anomalies are no longer active.
        for anomaly_type in thresholds:
            resolve_anomaly(anomaly_type)

        return

    # Only evaluate health and resource metrics for running containers.
    if container.status != "running":
        return

    # A running container resolves a previous stopped-container incident.
    resolve_anomaly("container_stopped")

    # Detect Docker health-check failures.
    if container.health_status == "unhealthy":
        create_or_update_incident(
            "container_unhealthy",
            f"Container unhealthy: {container.name}",
        )

    elif container.health_status == "healthy":
        resolve_anomaly("container_unhealthy")

    # Ignore missing or stale resource metrics.
    if (
        not container.metrics_updated_at
        or container.metrics_updated_at
        < timezone.now() - timedelta(minutes=2)
    ):
        return

    # Detect CPU and memory anomalies.
    for anomaly_type, (value, threshold, title) in thresholds.items():

        if value is None:
            continue

        if value <= threshold:
            resolve_anomaly(anomaly_type)
            continue

        create_or_update_incident(
            anomaly_type,
            f"{title}: {container.name} ({value:.2f}%)",
            observed_at=container.metrics_updated_at,
        )