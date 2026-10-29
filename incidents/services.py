import hashlib
import re

from django.db import transaction
from django.db.models import F

from incidents.models import Incident


def generate_fingerprint(event) -> str:
    """
    Generate a stable fingerprint for similar errors.

    Uses the application ID, exception type, and normalized
    error message. Stack traces are excluded because their
    line numbers and call paths can vary.
    """
    exception_type = (event.exception_type or "UnknownError").strip()
    message = (event.message or "").strip().lower()

    # Normalize UUIDs, long hexadecimal IDs, and numbers.
    message = re.sub(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
        r"[0-9a-f]{4}-[0-9a-f]{12}\b",
        "<uuid>",
        message,
    )

    message = re.sub(
        r"\b0x[0-9a-f]+\b",
        "<hex>",
        message,
    )

    message = re.sub(
        r"\b\d+\b",
        "<number>",
        message,
    )

    fingerprint_input = (
        f"{event.application_id}|{exception_type}|{message}"
    )

    return hashlib.sha256(
        fingerprint_input.encode("utf-8")
    ).hexdigest()


@transaction.atomic
def group_error_event(event):
    """
    Find or create an incident and associate the event with it.
    """
    fingerprint = generate_fingerprint(event)

    incident, created = Incident.objects.get_or_create(
        application=event.application,
        fingerprint=fingerprint,
        defaults={
            "title": (
                f"{event.exception_type}: {event.message}"
            )[:500],
            "first_seen": event.occurred_at,
            "last_seen": event.occurred_at,
            "occurrence_count": 0,
        },
    )

    if not created:
        Incident.objects.filter(pk=incident.pk).update(
            last_seen=event.occurred_at,
            occurrence_count=F("occurrence_count") + 1,
        )
    else:
        Incident.objects.filter(pk=incident.pk).update(
            occurrence_count=1,
        )

    event.fingerprint = fingerprint
    event.incident = incident
    event.save(update_fields=["fingerprint", "incident"])

    return incident