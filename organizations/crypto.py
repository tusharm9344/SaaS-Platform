import os

from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured


def get_fernet():
    key = os.getenv("RUNTIMERCA_ENCRYPTION_KEY")

    if not key:
        raise ImproperlyConfigured(
            "RUNTIMERCA_ENCRYPTION_KEY is not configured."
        )

    try:
        return Fernet(key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured(
            "RUNTIMERCA_ENCRYPTION_KEY is invalid."
        ) from exc


def encrypt_api_key(api_key):
    if not api_key:
        raise ValueError("API key cannot be empty.")

    return get_fernet().encrypt(
        api_key.encode("utf-8")
    ).decode("utf-8")


def decrypt_api_key(encrypted_api_key):
    try:
        return get_fernet().decrypt(
            encrypted_api_key.encode("utf-8")
        ).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError(
            "Unable to decrypt the configured API key."
        ) from exc