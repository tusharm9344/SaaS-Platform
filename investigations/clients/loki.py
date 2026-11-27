import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


class LokiClient:

    def __init__(self, base_url=None, timeout=10):
        self.base_url = (
            base_url or os.getenv(
                "LOKI_URL",
                "http://localhost:3100"
            )
        ).rstrip("/")

        self.timeout = timeout

    def query_range(
        self,
        query,
        start,
        end,
        limit=100,
        direction="backward",
    ):
        """
        Execute a Loki range query.

        start and end are Unix timestamps in seconds.
        Loki expects nanoseconds.
        """

        params = urlencode({
            "query": query,
            "start": int(start * 1_000_000_000),
            "end": int(end * 1_000_000_000),
            "limit": limit,
            "direction": direction,
        })

        url = f"{self.base_url}/loki/api/v1/query_range?{params}"

        try:
            with urlopen(url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode())

        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Loki HTTP {exc.code}: {error_body}"
            ) from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError(
                f"Loki connection failed: {exc}"
            ) from exc

        if payload.get("status") != "success":
            raise RuntimeError(
                f"Loki query failed: "
                f"{payload.get('error', 'Unknown error')}"
            )

        return payload.get("data", {}).get("result", [])

    def get_container_logs(
        self,
        container_names,
        start,
        end,
        limit=100,
    ):
        """
        Fetch logs from specified Docker containers.
        """

        if not container_names:
            return []

        escaped_names = [
            re.escape(name).replace(r"\-", "-")
            for name in container_names
        ]

        container_regex = (
            "^(" + "|".join(escaped_names) + ")$"
        )

        query = (
            '{platform="docker", '
            f'container=~"{container_regex}"'
            '}'
        )

        streams = self.query_range(
            query=query,
            start=start,
            end=end,
            limit=limit,
        )

        logs = []

        for stream in streams:
            labels = stream.get("stream", {})

            for timestamp, line in stream.get("values", []):
                logs.append({
                    "timestamp": int(timestamp),
                    "container": labels.get("container"),
                    "service_name": labels.get("service_name"),
                    "message": line,
                })

        logs.sort(
            key=lambda item: item["timestamp"],
            reverse=True,
        )

        return logs[:limit]