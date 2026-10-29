import hashlib
import secrets
import hmac

from django.utils import timezone

from applications.models import ApplicationAPIKey


KEY_PREFIX = "rca_live_"


def hash_api_key(raw_key: str) -> str:
    """Return a SHA-256 hash of an API key."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def create_api_key(application, name: str = "Default key") -> tuple:
    """
    Create an API key.

    Returns:
        (database_record, raw_key)

    The raw key must be shown to the customer only once.
    """
    raw_key = KEY_PREFIX + secrets.token_urlsafe(32)

    api_key = ApplicationAPIKey.objects.create(
        application=application,
        name=name,
        key_prefix=raw_key[:12],
        key_hash=hash_api_key(raw_key),
    )

    return api_key, raw_key


def verify_api_key(raw_key: str):
    """
    Return the associated ApplicationAPIKey if valid.
    Return None if the key is invalid or revoked.
    """
    if not raw_key or not raw_key.startswith(KEY_PREFIX):
        return None

    key_prefix = raw_key[:12]
    candidate_hash = hash_api_key(raw_key)

    candidates = ApplicationAPIKey.objects.filter(
        key_prefix=key_prefix,
        is_active=True,
        revoked_at__isnull=True,
    )

    for candidate in candidates:
        if hmac.compare_digest(candidate.key_hash, candidate_hash):
            return candidate

    return None


def revoke_api_key(api_key: ApplicationAPIKey) -> None:
    """Revoke a key without deleting its audit record."""
    api_key.is_active = False
    api_key.revoked_at = timezone.now()

    api_key.save(update_fields=["is_active", "revoked_at"])