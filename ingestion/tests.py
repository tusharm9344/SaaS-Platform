from django.test import TestCase

# Create your tests here.
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from organizations.models import Organization
from applications.models import Application, Service, ApplicationAPIKey
from applications.services.api_keys import create_api_key, revoke_api_key

from ingestion.models import ErrorEvent
from incidents.models import Incident


class ErrorIngestionTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.organization = Organization.objects.create(
            name="Test Organization",
            slug="test-organization",
        )

        self.application = Application.objects.create(
            organization=self.organization,
            name="Test Application",
            slug="test-application",
        )

        self.api_key_record, self.raw_api_key = create_api_key(
            self.application
        )

        self.url = "/api/v1/events/"

        self.payload = {
            "service_name": "api",
            "message": "Database connection failed for user 123",
            "exception_type": "ConnectionError",
            "stack_trace": "ConnectionError: database unavailable",
            "severity": "error",
            "environment": "production",
            "occurred_at": timezone.now().isoformat(),
        }

    def ingest(self, payload=None, api_key=None):
        self.client.credentials(
            HTTP_X_API_KEY=api_key or self.raw_api_key
        )

        return self.client.post(
            self.url,
            payload or self.payload,
            format="json",
        )

    def test_valid_event_is_ingested(self):
        with patch(
            "ingestion.views.investigate_incident_task.delay"
        ) as mock_task:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.ingest()

        self.assertEqual(response.status_code, 201)

        self.assertEqual(ErrorEvent.objects.count(), 1)
        self.assertEqual(Incident.objects.count(), 1)
        self.assertEqual(Service.objects.count(), 1)

        event = ErrorEvent.objects.first()

        self.assertEqual(event.application, self.application)
        self.assertEqual(event.service.name, "api")
        self.assertIsNotNone(event.incident)

        mock_task.assert_called_once_with(
            str(event.incident.id)
        )

    def test_invalid_api_key_is_rejected(self):
        response = self.ingest(api_key="invalid-key")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(ErrorEvent.objects.count(), 0)

    def test_revoked_api_key_is_rejected(self):
        revoke_api_key(self.api_key_record)

        response = self.ingest()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(ErrorEvent.objects.count(), 0)

    def test_inactive_application_is_rejected(self):
        self.application.is_active = False
        self.application.save(update_fields=["is_active"])

        response = self.ingest()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ErrorEvent.objects.count(), 0)

    def test_empty_message_is_rejected(self):
        payload = {
            **self.payload,
            "message": "",
        }

        response = self.ingest(payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ErrorEvent.objects.count(), 0)

    def test_empty_service_name_is_rejected(self):
        payload = {
            **self.payload,
            "service_name": "   ",
        }

        response = self.ingest(payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ErrorEvent.objects.count(), 0)

    def test_sensitive_data_is_redacted_before_storage(self):
        payload = {
            **self.payload,
            "message": "Database failed password=supersecret123",
            "stack_trace": (
                "Authorization: Bearer my-secret-token"
            ),
        }

        response = self.ingest(payload)

        self.assertEqual(response.status_code, 201)

        event = ErrorEvent.objects.first()

        self.assertNotIn("supersecret123", event.message)
        self.assertNotIn("my-secret-token", event.stack_trace)

        self.assertIn("[REDACTED]", event.message)
        self.assertIn("[REDACTED]", event.stack_trace)

    def test_existing_service_is_reused(self):
        Service.objects.create(
            application=self.application,
            name="api",
            environment="production",
        )

        response = self.ingest()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Service.objects.count(), 1)

    def test_similar_errors_are_grouped_into_one_incident(self):
        first_response = self.ingest()

        second_payload = {
            **self.payload,
            "message": "Database connection failed for user 456",
        }

        second_response = self.ingest(second_payload)

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)

        self.assertEqual(Incident.objects.count(), 1)
        self.assertEqual(ErrorEvent.objects.count(), 2)

        incident = Incident.objects.first()

        self.assertEqual(incident.occurrence_count, 2)

        self.assertEqual(
            first_response.data["incident_id"],
            second_response.data["incident_id"],
        )