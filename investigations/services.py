from django.utils import timezone

from ingestion.models import ErrorEvent
from investigations.models import Investigation


def investigate_incident(incident, investigation):

    events = list(
        ErrorEvent.objects.filter(
            incident=incident
        ).order_by("-occurred_at")[:100]
    )

    messages = [
        event.message.lower()
        for event in events
    ]

    combined_messages = " ".join(messages)

    hypotheses = []
    evidence = []
    recommended_actions = []

    # Database analysis
    if any(keyword in combined_messages for keyword in [
        "database",
        "sql",
        "postgres",
        "mysql",
        "connection pool",
    ]):
        hypotheses.append({
            "cause": "Database connectivity issue",
            "confidence": 0.65,
        })

        evidence.append(
            "Database-related keywords detected in error events."
        )

        recommended_actions.extend([
            "Check database availability.",
            "Inspect database connection pool limits.",
            "Review database logs.",
        ])

    # Network analysis
    if any(keyword in combined_messages for keyword in [
        "network",
        "timeout",
        "connection refused",
        "connectionerror",
    ]):
        hypotheses.append({
            "cause": "Network connectivity issue",
            "confidence": 0.60,
        })

        evidence.append(
            "Network connectivity or timeout patterns detected."
        )

        recommended_actions.extend([
            "Check network connectivity.",
            "Inspect service-to-service communication.",
            "Review timeout configurations.",
        ])

    # Resource analysis
    if any(keyword in combined_messages for keyword in [
        "memory",
        "out of memory",
        "resource exhausted",
        "cpu",
    ]):
        hypotheses.append({
            "cause": "Resource exhaustion",
            "confidence": 0.70,
        })

        evidence.append(
            "Resource exhaustion patterns detected."
        )

        recommended_actions.extend([
            "Inspect CPU and memory utilisation.",
            "Check application resource limits.",
            "Review recent workload changes.",
        ])

    # Fallback
    if not hypotheses:
        hypotheses.append({
            "cause": "Unclassified runtime error",
            "confidence": 0.20,
        })

        evidence.append(
            "No recognised error pattern was detected."
        )

        recommended_actions.append(
            "Inspect the stack trace and application logs manually."
        )

    investigation.summary = (
        f"Investigation completed for {incident.title}. "
        f"Analysed {len(events)} recent error events."
    )

    investigation.hypotheses = hypotheses
    investigation.evidence = evidence

    investigation.recommended_actions = list(
        dict.fromkeys(recommended_actions)
    )

    investigation.status = Investigation.Status.COMPLETED
    investigation.completed_at = timezone.now()

    investigation.save()

    return investigation
