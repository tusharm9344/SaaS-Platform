import json
import logging
import os
import socket
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import docker

logger = logging.getLogger("runtime_rca.discovery")


class DockerDiscoveryAgent:
    def __init__(
        self,
        api_key=None,
        base_url=None,
        interval=30,
        environment="production",
    ):
        self.api_key = api_key or os.getenv("RUNTIMERCA_API_KEY")
        self.base_url = (
            base_url or os.getenv(
                "RUNTIMERCA_URL",
                "http://127.0.0.1:8000"
            )
        ).rstrip("/")

        self.interval = interval
        self.environment = environment
        self.agent_id = self.get_agent_identity()
        self.hostname = socket.gethostname()

        if not self.api_key:
            raise ValueError("RUNTIMERCA_API_KEY is required")

        self.docker = docker.from_env()

        # Verify Docker connectivity.
        self.docker.ping()

    def get_agent_identity(self):
        identity_dir = Path.home() / ".runtime_rca"
        identity_dir.mkdir(parents=True, exist_ok=True)
        identity_file = identity_dir / "agent_id"

        if identity_file.exists():
            agent_id = identity_file.read_text().strip()
        else:
            agent_id = str(uuid.uuid4())
            identity_file.write_text(agent_id)

        return agent_id

    def get_container_metrics(self, container):
        if container.status != "running":
            return {
                "cpu_percent": None,
                "memory_usage": None,
                "memory_limit": None,
                "memory_percent": None,
            }

        try:
            stats = container.stats(stream=False)
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})
            cpu_delta = (
                cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
                - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            )
            system_delta = (
                cpu_stats.get("system_cpu_usage", 0)
                - precpu_stats.get("system_cpu_usage", 0)
            )
            online_cpus = cpu_stats.get("online_cpus") or len(
                cpu_stats.get("cpu_usage", {}).get("percpu_usage", []) or [1]
            )
            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta >= 0:
                cpu_percent = (
                    cpu_delta / system_delta
                ) * online_cpus * 100

            memory_stats = stats.get("memory_stats", {})
            memory_usage = memory_stats.get("usage", 0)
            memory_limit = memory_stats.get("limit", 0)
            memory_percent = (
                memory_usage / memory_limit * 100
                if memory_limit > 0
                else None
            )

            return {
                "cpu_percent": cpu_percent,
                "memory_usage": memory_usage,
                "memory_limit": memory_limit,
                "memory_percent": memory_percent,
            }
        except docker.errors.DockerException as exc:
            logger.warning(
                "Could not retrieve metrics for container %s: %s",
                container.id,
                exc,
            )
            return {
                "cpu_percent": None,
                "memory_usage": None,
                "memory_limit": None,
                "memory_percent": None,
            }

    def discover_containers(self):
        containers = self.docker.containers.list(all=True)

        discovered = []

        for container in containers:
            attrs = container.attrs
            config = attrs.get("Config", {})
            state = attrs.get("State", {})
            health = state.get("Health", {})
            health_status = health.get("Status")

            labels = config.get("Labels") or {}

            service_name = (
                labels.get("runtime_rca.service")
                or labels.get("com.docker.compose.service")
                or container.name
            )

            environment = (
                labels.get("runtime_rca.environment")
                or self.environment
            )

            metrics = self.get_container_metrics(container)

            image = (
                attrs.get("Config", {}).get("Image")
                or container.image.tags[0]
                if container.image.tags
                else attrs.get("Config", {}).get("Image", "unknown")
            )

            discovered.append({
                "container_id": container.id,
                "name": container.name,
                "image": image,
                "status": container.status,
                "health_status": health_status,
                "service_name": service_name,
                "environment": environment,
                **metrics,
                "labels": {
                    key: value
                    for key, value in labels.items()
                    if not any(
                        sensitive in key.lower()
                        for sensitive in (
                            "password",
                            "secret",
                            "token",
                            "credential",
                            "api_key",
                        )
                    )
                },
            })

        return discovered

    def send_inventory(self, containers):
        payload = json.dumps({
            "agent_id": self.agent_id,
            "hostname": self.hostname,
            "containers": containers,
        }).encode("utf-8")

        request = urllib.request.Request(
            f"{self.base_url}/api/v1/containers/discover/",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=15,
            ) as response:
                result = json.loads(response.read().decode("utf-8"))
                logger.info(
                    "Discovery successful: %s containers",
                    result.get("discovered", 0),
                )
                return result

        except urllib.error.HTTPError as exc:
            logger.error(
                "Discovery API error: HTTP %s",
                exc.code,
            )
            raise

        except urllib.error.URLError as exc:
            logger.error("Could not reach RuntimeRCA: %s", exc)
            raise

    def run_once(self):
        containers = self.discover_containers()

        logger.info(
            "Discovered %s Docker containers",
            len(containers),
        )

        return self.send_inventory(containers)

    def run_forever(self):
        logger.info("RuntimeRCA Docker Discovery Agent started")

        while True:
            try:
                self.run_once()

            except Exception:
                logger.exception("Discovery cycle failed")

            time.sleep(self.interval)