import argparse
import logging
import os

from runtime_rca.discovery import DockerDiscoveryAgent


def main():
    parser = argparse.ArgumentParser(
        description="RuntimeRCA Docker Discovery Agent"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--environment",
        default="production",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    agent = DockerDiscoveryAgent(
        api_key=os.getenv("RUNTIMERCA_API_KEY"),
        base_url=os.getenv(
            "RUNTIMERCA_URL",
            "http://127.0.0.1:8000",
        ),
        interval=args.interval,
        environment=args.environment,
    )

    agent.run_forever()


if __name__ == "__main__":
    main()