import redis

from celery import shared_task
from celery.exceptions import Retry

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
        settings.CELERY_BROKER_URL,
        socket_connect_timeout=5,
        socket_timeout=5,
    )

    lock = redis_client.lock(
        f"investigation_lock:{incident_id}",
        timeout=1800,
        blocking=False,
    )

    acquired = False
    investigation = None

    try:

        acquired = lock.acquire()

        # Another worker is processing this incident.
        if not acquired:
            raise self.retry(
                exc=RuntimeError("Incident investigation is locked."),
                countdown=10,
            )

        incident = Incident.objects.get(id=incident_id)

        investigation, _ = Investigation.objects.get_or_create(
            incident=incident,
        )

        # Prevent duplicate completed investigations.
        if investigation.status == Investigation.Status.COMPLETED:
            return {
                "status": "skipped",
                "reason": "Investigation already completed.",
                "incident_id": str(incident.id),
            }

        # Start investigation.
        investigation.status = Investigation.Status.RUNNING
        investigation.save(update_fields=["status"])

        Incident.objects.filter(id=incident.id).update(
            status=Incident.Status.INVESTIGATING,
            updated_at=timezone.now(),
        )

        # Execute RCA.
        investigation = investigate_incident(
            incident,
            investigation,
        )

        # RCA completed does not mean the incident is resolved.
        Incident.objects.filter(id=incident.id).update(
            status=Incident.Status.OPEN,
            updated_at=timezone.now(),
        )

        return {
            "status": "completed",
            "incident_id": str(incident.id),
            "investigation_id": str(investigation.id),
        }

    except Retry:
        raise

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

            if investigation:

                investigation.status = Investigation.Status.FAILED

                investigation.summary = (
                    f"Investigation failed after retries: {str(exc)[:1000]}"
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

        if investigation:

            investigation.status = Investigation.Status.PENDING
            investigation.save(update_fields=["status"])

        Incident.objects.filter(id=incident_id).update(
            status=Incident.Status.OPEN,
            updated_at=timezone.now(),
        )

        raise self.retry(exc=exc)

    finally:

        if acquired:
            try:
                lock.release()
            except redis.exceptions.LockError:
                pass

        close_old_connections()
