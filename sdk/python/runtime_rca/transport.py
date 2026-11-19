import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from runtime_rca.exceptions import TransportError

logger = logging.getLogger("runtime_rca")


class EventTransport:

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int = 5,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def send_event(self, payload: dict) -> bool:

        url = f"{self.base_url}/api/v1/events/"

        data = json.dumps(payload).encode("utf-8")

        request = Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
            },
            method="POST",
        )

        for attempt in range(self.max_retries + 1):

            try:
                with urlopen(
                    request,
                    timeout=self.timeout,
                ) as response:

                    return 200 <= response.status < 300

            except HTTPError as error:

                # Retry rate limits and temporary server errors.
                if error.code == 429 or error.code >= 500:
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)
                        continue

                raise TransportError(
                    f"API returned HTTP {error.code}"
                ) from error

            except (URLError, TimeoutError, OSError) as error:

                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue

                raise TransportError(
                    "Unable to communicate with Runtime RCA."
                ) from error

        raise TransportError("Event delivery failed.")