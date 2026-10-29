from django.test import TestCase
from django.utils import timezone

from organizations.models import Organization
from applications.models import Application
from ingestion.models import ErrorEvent
from incidents.models import Incident
from investigations.models import Investigation
from investigations.services import investigate_incident


class InvestigationServiceTests(TestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Test Organization",
            slug="test-organization",
        )

        self.application = Application.objects.create(
            organization=organization,
            name="Test Application",
            slug="test-application",
        )

    def create_incident_with_event(self, message, exception_type):
        incident = Incident.objects.create(
            application=self.application,
            fingerprint="test-fingerprint",
            title=f"{exception_type}: {message}",
            first_seen=timezone.now(),
            last_seen=timezone.now(),
            occurrence_count=1,
        )

        ErrorEvent.objects.create(
            application=self.application,
            incident=incident,
            message=message,
            exception_type=exception_type,
            stack_trace="",
            severity=ErrorEvent.Severity.ERROR,
            environment="test",
            occurred_at=timezone.now(),
        )

        return incident

    def test_database_error_generates_database_hypothesis(self):
        incident = self.create_incident_with_event(
            "Database connection failed",
            "ConnectionError",
        )

        report = investigate_incident(incident)

        self.assertEqual(
            report.status,
            Investigation.Status.COMPLETED,
        )
        self.assertTrue(report.hypotheses)
        self.assertIn(
            "Database",
            report.hypotheses[0]["cause"],
        )

    def test_unknown_error_generates_fallback_hypothesis(self):
        incident = self.create_incident_with_event(
            "Unexpected widget rendering failure",
            "WidgetError",
        )

        report = investigate_incident(incident)

        self.assertEqual(len(report.hypotheses), 1)
        self.assertEqual(
            report.hypotheses[0]["cause"],
            "Unclassified runtime error",
        )

    def test_report_is_saved_to_database(self):
        incident = self.create_incident_with_event(
            "Database connection failed",
            "ConnectionError",
        )

        report = investigate_incident(incident)

        self.assertTrue(
            Investigation.objects.filter(pk=report.pk).exists()
        )