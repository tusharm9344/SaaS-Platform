
from django.test import TestCase
from django.utils import timezone

from organizations.models import Organization
from applications.models import (
    Application,
    DiscoveredContainer,
    Service,
)
from ingestion.models import ErrorEvent
from incidents.models import Incident
from incidents.services import (
    detect_container_anomalies,
    group_error_event,
)


class IncidentGroupingTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Organization",
            slug="test-organization",
        )

        self.application = Application.objects.create(
            organization=self.organization,
            name="Test Application",
            slug="test-application",
        )

    def create_event(self, message):
        return ErrorEvent.objects.create(
            application=self.application,
            message=message,
            exception_type="ConnectionError",
            stack_trace="ConnectionError: database unavailable",
            severity=ErrorEvent.Severity.ERROR,
            environment="production",
            occurred_at=timezone.now(),
        )

    def test_identical_errors_share_one_incident(self):
        event1 = self.create_event(
            "Database connection failed for user 123"
        )
        event2 = self.create_event(
            "Database connection failed for user 456"
        )

        incident1 = group_error_event(event1)
        incident2 = group_error_event(event2)

        self.assertEqual(incident1.id, incident2.id)
        self.assertEqual(
            ErrorEvent.objects.filter(
                incident=incident1
            ).count(),
            2,
        )

    def test_occurrence_count_increments(self):
        event1 = self.create_event(
            "Database connection failed for user 123"
        )
        event2 = self.create_event(
            "Database connection failed for user 456"
        )

        incident1 = group_error_event(event1)
        group_error_event(event2)

        incident1.refresh_from_db()

        self.assertEqual(incident1.occurrence_count, 2)

    def test_different_applications_have_separate_incidents(self):
        other_application = Application.objects.create(
            organization=self.organization,
            name="Another Application",
            slug="another-application",
        )

        event1 = self.create_event("Database connection failed")

        event2 = ErrorEvent.objects.create(
            application=other_application,
            message="Database connection failed",
            exception_type="ConnectionError",
            stack_trace="ConnectionError: database unavailable",
            severity=ErrorEvent.Severity.ERROR,
            environment="production",
            occurred_at=timezone.now(),
        )

        incident1 = group_error_event(event1)
        incident2 = group_error_event(event2)

        self.assertNotEqual(incident1.id, incident2.id)

    def test_new_incident_starts_with_one_occurrence(self):
        event = self.create_event("Redis connection failed")

        incident = group_error_event(event)

        incident.refresh_from_db()

        self.assertEqual(incident.occurrence_count, 1)
        self.assertEqual(
            Incident.objects.filter(pk=incident.pk).count(),
            1,
        )


class ContainerAnomalyTests(TestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Container Organization",
            slug="container-organization",
        )
        self.application = Application.objects.create(
            organization=organization,
            name="Container Application",
            slug="container-application",
        )
        self.service = Service.objects.create(
            application=self.application,
            name="api",
            environment="production",
        )
        self.container = DiscoveredContainer.objects.create(
            application=self.application,
            service=self.service,
            container_id="container-1",
            name="api-1",
            image="api:latest",
            status="running",
            cpu_percent=90,
            memory_percent=50,
            metrics_updated_at=timezone.now(),
        )

    def test_high_cpu_creates_and_updates_incident(self):
        detect_container_anomalies(self.container)
        incident = Incident.objects.get(
            application=self.application,
            service=self.service,
        )
        self.assertEqual(
            incident.title,
            "High CPU usage: api-1 (90.00%)"
        )
        self.assertEqual(incident.occurrence_count, 1)

        # A repeated high CPU reading should not increment the count.
        detect_container_anomalies(self.container)
        incident.refresh_from_db()
        self.assertEqual(incident.occurrence_count, 1)
        self.assertEqual(incident.status, Incident.Status.OPEN)

    def test_low_cpu_resolves_incident_and_high_cpu_reopens_it(self):
        detect_container_anomalies(self.container)
        incident = Incident.objects.get(service=self.service)

        self.container.cpu_percent = 50
        self.container.save(update_fields=["cpu_percent"])
        detect_container_anomalies(self.container)
        incident.refresh_from_db()
        self.assertEqual(incident.status, Incident.Status.RESOLVED)

        self.container.cpu_percent = 90
        self.container.save(update_fields=["cpu_percent"])
        detect_container_anomalies(self.container)
        incident.refresh_from_db()
        self.assertEqual(incident.status, Incident.Status.OPEN)
