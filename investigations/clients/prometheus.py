import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


class PrometheusClient:

    def __init__(self, base_url=None, timeout=10):
        self.base_url = (
            base_url or os.getenv(
                "PROMETHEUS_URL",
                "http://localhost:9090"
            )
        ).rstrip("/")

        self.timeout = timeout

    def query_range(self, query, start, end, step="15s"):
        """
        Execute a Prometheus range query.

        start and end should be Unix timestamps.
        """

        params = urlencode({
            "query": query,
            "start": start,
            "end": end,
            "step": step,
        })

        url = (
            f"{self.base_url}/api/v1/query_range?{params}"
        )

        try:
            with urlopen(url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode())

        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(
                f"Prometheus request failed: {exc}"
            ) from exc

        if payload.get("status") != "success":
            raise RuntimeError(
                f"Prometheus query failed: "
                f"{payload.get('error', 'Unknown error')}"
            )

        return payload.get("data", {}).get("result", [])

    def get_container_metrics(self, start, end):
        """
        Fetch CPU and memory metrics for Docker containers.
        """

        cpu_query = (
            'rate(container_cpu_usage_seconds_total'
            '{id=~"/docker/.+"}[5m]) * 100'
        )

        memory_query = (
            'container_memory_working_set_bytes'
            '{id=~"/docker/.+"}'
        )

        cpu_results = self.query_range(
            cpu_query,
            start,
            end,
        )

        memory_results = self.query_range(
            memory_query,
            start,
            end,
        )

        return {
            "cpu": self._normalize_results(cpu_results),
            "memory": self._normalize_results(memory_results),
        }

    @staticmethod
    def _normalize_results(results):
        """
        Convert Prometheus container IDs into Docker IDs.
        """

        normalized = []

        for series in results:
            metric_id = series.get("metric", {}).get("id", "")

            if not metric_id.startswith("/docker/"):
                continue

            container_id = metric_id.removeprefix("/docker/")

            samples = [
                {
                    "timestamp": float(timestamp),
                    "value": float(value),
                }
                for timestamp, value in series.get("values", [])
            ]

            normalized.append({
                "container_id": container_id,
                "samples": samples,
            })

        return normalized