from django.test import TestCase

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
