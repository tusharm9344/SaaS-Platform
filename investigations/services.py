from django.utils import timezone

from incidents.models import Incident
from investigations.models import Investigation


def investigate_incident(incident: Incident) -> Investigation:
    """
    Analyze an incident and save a structured investigation report.

    This first version uses transparent rules rather than AI.
    Hypotheses are suggestions, not confirmed root causes.
    """

    events = incident.events.order_by("-received_at")[:100]

    hypotheses = []
    evidence = []
    recommended_actions = []

    exception_types = set()
    messages = []
    stack_traces = []

    for event in events:
        if event.exception_type:
            exception_types.add(event.exception_type.lower())

        if event.message:
            messages.append(event.message.lower())

        if event.stack_trace:
            stack_traces.append(event.stack_trace.lower())

    searchable_text = " ".join(messages + stack_traces)

    # Rule 1: Database connectivity
    database_keywords = [
        "database connection",
        "connection refused",
        "connection timed out",
        "too many connections",
        "connection pool",
        "postgres",
        "mysql",
        "database unavailable",
    ]

    if any(keyword in searchable_text for keyword in database_keywords):
        hypotheses.append({
            "cause": "Database connectivity or connection exhaustion",
            "confidence": 0.65,
            "reason": (
                "The available error messages contain database "
                "or connection-related indicators."
            ),
        })

        evidence.append({
            "type": "error_message",
            "details": (
                "Database or connection-related keywords were found "
                "in the incident's error events."
            ),
        })

        recommended_actions.extend([
            "Check database availability and connectivity.",
            "Inspect database connection counts and connection-pool usage.",
            "Review database logs around the incident timestamps.",
        ])

    # Rule 2: Network or external-service connectivity
    network_keywords = [
        "connection reset",
        "network is unreachable",
        "name or service not known",
        "temporary failure in name resolution",
        "dns",
        "upstream timed out",
    ]

    if any(keyword in searchable_text for keyword in network_keywords):
        hypotheses.append({
            "cause": "Network or external-service connectivity",
            "confidence": 0.60,
            "reason": (
                "The error text contains indicators of network, "
                "DNS, or upstream connectivity problems."
            ),
        })

        evidence.append({
            "type": "error_message",
            "details": (
                "Network or upstream connectivity indicators "
                "were found in the error events."
            ),
        })

        recommended_actions.extend([
            "Check network connectivity and DNS resolution.",
            "Inspect upstream service health and timeout settings.",
        ])

    # Rule 3: Resource exhaustion
    resource_keywords = [
        "out of memory",
        "memoryerror",
        "memory exhausted",
        "too many open files",
        "disk quota exceeded",
        "no space left on device",
    ]

    if any(keyword in searchable_text for keyword in resource_keywords):
        hypotheses.append({
            "cause": "Application or host resource exhaustion",
            "confidence": 0.70,
            "reason": (
                "The error text contains indicators of memory, "
                "disk, or operating-system resource exhaustion."
            ),
        })

        evidence.append({
            "type": "error_message",
            "details": (
                "Resource-exhaustion indicators were found "
                "in the error events."
            ),
        })

        recommended_actions.extend([
            "Inspect memory, disk, and file-descriptor utilization.",
            "Review resource limits and recent workload changes.",
        ])

    # Rule 4: Unknown exception or no recognized pattern
    if not hypotheses:
        hypotheses.append({
            "cause": "Unclassified runtime error",
            "confidence": 0.20,
            "reason": (
                "The current rule set could not identify a known "
                "failure pattern from the available event text."
            ),
        })

        evidence.append({
            "type": "incident_metadata",
            "details": (
                f"Incident contains {len(messages)} event messages "
                f"and exception types: "
                f"{', '.join(sorted(exception_types)) or 'not provided'}."
            ),
        })

        recommended_actions.extend([
            "Inspect the complete stack trace and surrounding logs.",
            "Check recent deployments and configuration changes.",
            "Add more contextual telemetry to the affected application.",
        ])

    # Remove duplicate actions while preserving their order.
    recommended_actions = list(dict.fromkeys(recommended_actions))

    summary = (
        f"Analyzed incident '{incident.title}' using "
        f"{len(messages)} recent error events. "
        f"Generated {len(hypotheses)} root-cause hypothesis(es). "
        "These hypotheses require verification."
    )

    investigation = Investigation.objects.create(
        incident=incident,
        status=Investigation.Status.COMPLETED,
        summary=summary,
        hypotheses=hypotheses,
        evidence=evidence,
        recommended_actions=recommended_actions,
        completed_at=timezone.now(),
    )

    return investigation