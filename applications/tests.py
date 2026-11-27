from django.test import TestCase
from rest_framework.test import APIClient

from applications.models import (
    Application,
    Service,
    DiscoveredContainer,
    DiscoveryAgent,
)
from incidents.models import Incident
from applications.models import Application
from applications.services.api_keys import (
    create_api_key,
    verify_api_key,
    revoke_api_key,
)
from organizations.models import Organization


class ApplicationAPIKeyTests(TestCase):
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

    def test_created_key_is_valid(self):
        api_key, raw_key = create_api_key(self.application)

        verified_key = verify_api_key(raw_key)

        self.assertIsNotNone(verified_key)
        self.assertEqual(verified_key.id, api_key.id)

    def test_invalid_key_is_rejected(self):
        result = verify_api_key("rca_live_invalid_key")

        self.assertIsNone(result)

    def test_revoked_key_is_rejected(self):
        api_key, raw_key = create_api_key(self.application)

        revoke_api_key(api_key)

        result = verify_api_key(raw_key)

        self.assertIsNone(result)

    def test_plaintext_key_is_not_stored(self):
        api_key, raw_key = create_api_key(self.application)

        self.assertNotEqual(api_key.key_hash, raw_key)
        self.assertEqual(len(api_key.key_hash), 64)
class ContainerDiscoveryTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.organization = Organization.objects.create(
            name="Discovery Organization",
            slug="discovery-organization",
        )

        self.application = Application.objects.create(
            organization=self.organization,
            name="Discovery Application",
            slug="discovery-application",
        )

        self.api_key, self.raw_key = create_api_key(
            self.application
        )

        self.url = "/api/v1/containers/discover/"

        self.payload = {
            "agent_id": "test-agent-1",
            "hostname": "test-host",
            "containers": [
                {
                    "container_id": "container-1",
                    "name": "api-1",
                    "image": "api:latest",
                    "status": "running",
                    "health_status": "healthy",
                    "service_name": "api",
                    "environment": "production",
                    "cpu_percent": 30,
                    "memory_usage": 100000000,
                    "memory_limit": 200000000,
                    "memory_percent": 50,
                    "labels": {},
                }
            ],
        }

    def discover(self, payload=None):
        self.client.credentials(
            HTTP_X_API_KEY=self.raw_key
        )

        return self.client.post(
            self.url,
            payload or self.payload,
            format="json",
        )

    def test_valid_container_discovery(self):
        response = self.discover()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["discovered"], 1)

        self.assertEqual(
            DiscoveredContainer.objects.count(),
            1,
        )

        container = DiscoveredContainer.objects.first()

        self.assertEqual(container.name, "api-1")
        self.assertEqual(container.status, "running")
        self.assertEqual(container.health_status, "healthy")
        self.assertEqual(container.cpu_percent, 30)
        self.assertEqual(container.memory_percent, 50)

    def test_invalid_api_key_is_rejected(self):
        self.client.credentials(
            HTTP_X_API_KEY="invalid-key"
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_missing_agent_id_is_rejected(self):
        payload = {
            **self.payload,
            "agent_id": "",
        }

        response = self.discover(payload)

        self.assertEqual(response.status_code, 400)

    def test_empty_container_list_is_accepted(self):
        payload = {
            **self.payload,
            "containers": [],
        }

        response = self.discover(payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["discovered"], 0)

    def test_high_cpu_creates_incident(self):
        payload = {
            **self.payload,
            "containers": [
                {
                    **self.payload["containers"][0],
                    "cpu_percent": 90,
                }
            ],
        }

        response = self.discover(payload)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Incident.objects.filter(
                title__startswith="High CPU usage"
            ).exists()
        )

    def test_high_memory_creates_incident(self):
        payload = {
            **self.payload,
            "containers": [
                {
                    **self.payload["containers"][0],
                    "memory_percent": 95,
                }
            ],
        }

        response = self.discover(payload)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Incident.objects.filter(
                title__startswith="High memory usage"
            ).exists()
        )

    def test_unhealthy_container_creates_incident(self):
        payload = {
            **self.payload,
            "containers": [
                {
                    **self.payload["containers"][0],
                    "health_status": "unhealthy",
                }
            ],
        }

        response = self.discover(payload)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Incident.objects.filter(
                title__startswith="Container unhealthy"
            ).exists()
        )

    def test_stopped_container_creates_incident(self):
        payload = {
            **self.payload,
            "containers": [
                {
                    **self.payload["containers"][0],
                    "status": "exited",
                }
            ],
        }

        response = self.discover(payload)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Incident.objects.filter(
                title__startswith="Container stopped"
            ).exists()
        )

    def test_repeated_discovery_does_not_duplicate_incidents(self):
        payload = {
            **self.payload,
            "containers": [
                {
                    **self.payload["containers"][0],
                    "cpu_percent": 90,
                }
            ],
        }

        self.discover(payload)
        self.discover(payload)

        self.assertEqual(
            Incident.objects.filter(
                title__startswith="High CPU usage"
            ).count(),
            1,
        )

    def test_healthy_recovery_resolves_incident(self):
        unhealthy_payload = {
            **self.payload,
            "containers": [
                {
                    **self.payload["containers"][0],
                    "health_status": "unhealthy",
                }
            ],
        }

        self.discover(unhealthy_payload)

        incident = Incident.objects.get(
            title__startswith="Container unhealthy"
        )

        healthy_payload = {
            **self.payload,
            "containers": [
                {
                    **self.payload["containers"][0],
                    "health_status": "healthy",
                }
            ],
        }

        self.discover(healthy_payload)

        incident.refresh_from_db()

        self.assertEqual(
            incident.status,
            Incident.Status.RESOLVED,
        )
