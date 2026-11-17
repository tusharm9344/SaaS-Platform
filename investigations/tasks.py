import redis

from celery import shared_task
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from incidents.models import Incident
from investigations.models import Investigation
from investigations.services import investigate_incident


@shared_task(
    bind=True,
    name="investigations.investigate_incident",
    max_retries=3,
    default_retry_delay=10,
)
def investigate_incident_task(self, incident_id):

    close_old_connections()

    redis_client = redis.Redis.from_url(
        settings.CELERY_BROKER_URL
    )

    lock = redis_client.lock(
        f"investigation_lock:{incident_id}",
        timeout=900,
        blocking=False,
    )

    acquired = False

    try:
        acquired = lock.acquire()

        if not acquired:
            return {
                "status": "skipped",
                "reason": "Another worker is investigating this incident.",
                "incident_id": str(incident_id),
            }

        incident = Incident.objects.get(id=incident_id)

        if Investigation.objects.filter(
            incident=incident,
            status="completed",
        ).exists():
            return {
                "status": "skipped",
                "reason": "Investigation already completed.",
                "incident_id": str(incident.id),
            }

        Incident.objects.filter(id=incident.id).update(
            status=Incident.Status.INVESTIGATING,
            updated_at=timezone.now(),
        )

        investigation, _ = Investigation.objects.get_or_create(
            incident=incident,
        )
        investigation.status = Investigation.Status.RUNNING
        investigation.save(update_fields=["status"])

        investigation = investigate_incident(incident, investigation)

        return {
            "status": "completed",
            "incident_id": str(incident.id),
            "investigation_id": str(investigation.id),
        }

    except Incident.DoesNotExist:
        return {
            "status": "failed",
            "reason": "Incident not found.",
            "incident_id": str(incident_id),
        }

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            investigation = Investigation.objects.filter(
                incident_id=incident_id
            ).first()
            if investigation is not None:
                investigation.status = Investigation.Status.FAILED
                investigation.summary = (
                    f"Investigation failed: {str(exc)[:1000]}"
                )
                investigation.save(
                    update_fields=["status", "summary"]
                )

            Incident.objects.filter(id=incident_id).update(
                status=Incident.Status.OPEN,
                updated_at=timezone.now(),
            )

            return {
                "status": "failed",
                "reason": "Maximum retries exhausted.",
                "incident_id": str(incident_id),
            }

        raise self.retry(exc=exc)
    finally:

        if acquired:
            try:
                lock.release()
            except redis.exceptions.LockError:
                pass

        close_old_connections()
