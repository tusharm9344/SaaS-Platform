import re


SECRET_PATTERNS = [
    # Authorization headers and bearer tokens
    (
        re.compile(
            r"(?i)(\bauthorization\s*[:=]\s*bearer\s+)[^\s,;]+"
        ),
        r"\1[REDACTED]",
    ),
    (
        re.compile(
            r"(?i)(\bbearer\s+)[A-Za-z0-9._~+/=-]+"
        ),
        r"\1[REDACTED]",
    ),

    # Common credential assignments
    (
        re.compile(
            r"""(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret)\b(\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,;&]+)"""
        ),
        r"\1\2[REDACTED]",
    ),

    # AWS access key IDs
    (
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "[REDACTED_AWS_ACCESS_KEY]",
    ),

    # Common private-key blocks
    (
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            re.DOTALL,
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
]


def redact_sensitive_data(value: str) -> str:
    """
    Redact common credentials from text before storage.

    This is a best-effort safeguard, not a guarantee that
    all secrets or personal information will be detected.
    """
    if not isinstance(value, str):
        return value

    for pattern, replacement in SECRET_PATTERNS:
        value = pattern.sub(replacement, value)

    return value
