import uuid
from unittest.mock import patch

from celery.exceptions import Retry
from django.test import TestCase
from django.utils import timezone

from organizations.models import AIProviderConfig, Organization
from applications.models import Application
from ingestion.models import ErrorEvent
from incidents.models import Incident
from investigations.models import Investigation
from investigations.services import investigate_incident, run_ai_investigation
from investigations.tasks import investigate_incident_task


class InvestigationTestBase(TestCase):
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


class InvestigationServiceTests(InvestigationTestBase):
    def investigate(self, incident):
        investigation = Investigation.objects.create(
            incident=incident,
            status=Investigation.Status.RUNNING,
        )
        return investigate_incident(incident, investigation)

    def test_database_error_generates_database_hypothesis(self):
        incident = self.create_incident_with_event(
            "Database connection failed",
            "ConnectionError",
        )

        report = self.investigate(incident)

        self.assertEqual(
            report.status,
            Investigation.Status.COMPLETED,
        )
        self.assertTrue(report.hypotheses)
        self.assertIn("Database", report.hypotheses[0]["cause"])

    def test_unknown_error_generates_fallback_hypothesis(self):
        incident = self.create_incident_with_event(
            "Unexpected widget rendering failure",
            "WidgetError",
        )

        report = self.investigate(incident)

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

        report = self.investigate(incident)

        self.assertTrue(
            Investigation.objects.filter(pk=report.pk).exists()
        )

    def test_ai_investigation_uses_organization_provider_config(self):
        incident = self.create_incident_with_event(
            "Database connection failed",
            "ConnectionError",
        )
        config = AIProviderConfig(
            organization=self.application.organization,
            provider="custom-provider",
            model_name="custom-model",
            encrypted_api_key="encrypted-key",
            api_base="https://ai.example.com/v1",
        )
        event = ErrorEvent.objects.get(incident=incident)

        with patch(
            "organizations.models.AIProviderConfig.objects.filter"
        ) as find_config, patch(
            "organizations.crypto.decrypt_api_key",
            return_value="decrypted-key",
        ) as decrypt_api_key, patch(
            "investigations.clients.ai.generate_completion",
            return_value=(
                '{"summary":"Analysis complete","hypotheses":'
                '[{"cause":"Database connectivity issue","confidence":0.8,'
                '"reasoning":"Evidence supports this hypothesis."}],'
                '"recommended_actions":["Check database availability."]}'
            ),
        ) as generate_completion:
            find_config.return_value.first.return_value = config
            analysis = run_ai_investigation(
                incident,
                [event],
                [{"type": "error_summary"}],
                {"summary": "Fallback analysis"},
            )

        self.assertEqual(analysis["provider"], "custom-provider")
        self.assertEqual(analysis["model"], "custom-model")
        generate_completion.assert_called_once()
        self.assertEqual(
            generate_completion.call_args.kwargs["api_base"],
            "https://ai.example.com/v1",
        )
        self.assertEqual(
            generate_completion.call_args.kwargs["api_key"],
            "decrypted-key",
        )
        decrypt_api_key.assert_called_once_with("encrypted-key")


class CeleryInvestigationTaskTests(InvestigationTestBase):
    def setUp(self):
        super().setUp()

        self.incident = self.create_incident_with_event(
            "Database connection failed",
            "ConnectionError",
        )

        self.redis_patcher = patch(
            "investigations.tasks.redis.Redis.from_url"
        )
        self.mock_redis = self.redis_patcher.start()

        self.mock_lock = self.mock_redis.return_value.lock.return_value
        self.mock_lock.acquire.return_value = True

        self.addCleanup(self.redis_patcher.stop)

    def test_task_completes_investigation_successfully(self):
        result = investigate_incident_task.run(str(self.incident.id))

        investigation = Investigation.objects.get(
            incident=self.incident
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(
            investigation.status,
            Investigation.Status.COMPLETED,
        )

        self.incident.refresh_from_db()

        self.assertEqual(self.incident.status, Incident.Status.OPEN)
        self.mock_lock.release.assert_called_once()

    def test_completed_investigation_is_skipped(self):
        Investigation.objects.create(
            incident=self.incident,
            status=Investigation.Status.COMPLETED,
        )

        result = investigate_incident_task.run(str(self.incident.id))

        self.assertEqual(result["status"], "skipped")
        self.mock_lock.release.assert_called_once()

    def test_missing_incident_is_handled_safely(self):
        missing_id = str(uuid.uuid4())

        result = investigate_incident_task.run(missing_id)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "Incident not found.")

    def test_temporary_failure_triggers_retry(self):
        with patch(
            "investigations.tasks.investigate_incident",
            side_effect=RuntimeError("Temporary RCA failure"),
        ):
            with patch.object(
                investigate_incident_task,
                "retry",
                side_effect=Retry(),
            ):
                with self.assertRaises(Retry):
                    investigate_incident_task.run(
                        str(self.incident.id)
                    )

        investigation = Investigation.objects.get(
            incident=self.incident
        )

        self.assertEqual(
            investigation.status,
            Investigation.Status.PENDING,
        )

        self.incident.refresh_from_db()
        self.assertEqual(self.incident.status, Incident.Status.OPEN)

    def test_maximum_retries_marks_investigation_failed(self):
        investigate_incident_task.push_request(retries=3)

        try:
            with patch(
                "investigations.tasks.investigate_incident",
                side_effect=RuntimeError("Permanent RCA failure"),
            ):
                result = investigate_incident_task.run(
                    str(self.incident.id)
                )
        finally:
            investigate_incident_task.pop_request()

        investigation = Investigation.objects.get(
            incident=self.incident
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            investigation.status,
            Investigation.Status.FAILED,
        )
        self.assertIn(
            "Permanent RCA failure",
            investigation.summary,
        )

        self.incident.refresh_from_db()
        self.assertEqual(self.incident.status, Incident.Status.OPEN)

    def test_locked_incident_triggers_retry(self):
        self.mock_lock.acquire.return_value = False

        with patch.object(
            investigate_incident_task,
            "retry",
            side_effect=Retry(),
        ):
            with self.assertRaises(Retry):
                investigate_incident_task.run(
                    str(self.incident.id)
                )

        self.assertFalse(
            Investigation.objects.filter(
                incident=self.incident
            ).exists()
        )

        self.mock_lock.release.assert_not_called()
