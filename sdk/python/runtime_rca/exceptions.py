class RuntimeRCAError(Exception):
    """Base exception for Runtime RCA SDK errors."""


class ConfigurationError(RuntimeRCAError):
    """Raised when SDK configuration is invalid."""


class TransportError(RuntimeRCAError):
    """Raised when communication with Runtime RCA fails."""