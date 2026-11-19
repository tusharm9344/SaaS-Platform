import logging
import traceback

from datetime import datetime, timezone

from runtime_rca.exceptions import ConfigurationError
from runtime_rca.transport import EventTransport
from runtime_rca.worker import EventWorker


logger = logging.getLogger("runtime_rca")


class RuntimeRCA:

    def __init__(
        self,
        api_key,
        service_name,
        environment="production",
        base_url="http://127.0.0.1:8000",
        timeout=5,
        max_retries=3,
        max_queue_size=1000,
    ):

        if not api_key:
            raise ConfigurationError("API key is required.")

        if not service_name or not service_name.strip():
            raise ConfigurationError("Service name is required.")

        if not isinstance(environment, str) or not environment.strip():
            raise ConfigurationError("Environment must be a non-empty string.")

        if timeout <= 0:
            raise ConfigurationError("Timeout must be greater than zero.")

        if max_retries < 0:
            raise ConfigurationError("Max retries cannot be negative.")

        if max_queue_size <= 0:
            raise ConfigurationError("Queue size must be greater than zero.")

        self.service_name = service_name.strip()
        self.environment = environment.strip().lower()

        self.transport = EventTransport(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        self.worker = EventWorker(
            transport=self.transport,
            max_queue_size=max_queue_size,
        )

    def capture_exception(self, exception, severity="error"):

        try:
            stack_trace = "".join(
                traceback.format_exception(
                    type(exception),
                    exception,
                    exception.__traceback__,
                )
            )

            payload = {
                "service_name": self.service_name,
                "message": str(exception),
                "exception_type": type(exception).__name__,
                "stack_trace": stack_trace,
                "severity": severity,
                "environment": self.environment,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            }

            return self.worker.submit(payload)

        except Exception:
            logger.exception(
                "Runtime RCA failed to capture an exception."
            )
            return False

    def capture_message(self, message, severity="error"):

        try:
            if not isinstance(message, str) or not message.strip():
                return False

            payload = {
                "service_name": self.service_name,
                "message": message,
                "exception_type": "",
                "stack_trace": "",
                "severity": severity,
                "environment": self.environment,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            }

            return self.worker.submit(payload)

        except Exception:
            logger.exception(
                "Runtime RCA failed to capture a message."
            )
            return False

    def flush(self, timeout=None):
        return self.worker.flush(timeout=timeout)

    def close(self, timeout=5):
        return self.worker.close(timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback_object):
        self.close()
