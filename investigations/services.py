import json
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.utils import timezone

from applications.models import DiscoveredContainer
from ingestion.models import ErrorEvent
from ingestion.services import redact_sensitive_data

from investigations.clients.prometheus import PrometheusClient
from investigations.clients.loki import LokiClient
from investigations.models import Investigation


CORRELATION_WINDOW_BEFORE = 10 * 60
CORRELATION_WINDOW_AFTER = 5 * 60

CPU_THRESHOLD = 80
MEMORY_THRESHOLD = 85

MAX_LOGS = 10
MAX_AI_EVENTS = 30

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def add_hypothesis(hypotheses, cause, confidence):
    for hypothesis in hypotheses:
        if hypothesis["cause"] == cause:
            hypothesis["confidence"] = max(
                hypothesis["confidence"],
                confidence,
            )
            return

    hypotheses.append({
        "cause": cause,
        "confidence": confidence,
    })


def collect_container_metrics(containers, start, end):
    if not containers:
        return [], []

    client = PrometheusClient()

    try:
        metrics = client.get_container_metrics(start, end)

    except Exception as exc:
        return [], [{
            "type": "collection_error",
            "source": "Prometheus",
            "message": str(exc),
        }]

    container_ids = {
        container.container_id: container
        for container in containers
    }

    evidence = []
    anomalies = []

    cpu_metrics = {
        item["container_id"]: item
        for item in metrics.get("cpu", [])
    }

    memory_metrics = {
        item["container_id"]: item
        for item in metrics.get("memory", [])
    }

    for container_id, container in container_ids.items():

        cpu_data = cpu_metrics.get(container_id, {})
        memory_data = memory_metrics.get(container_id, {})

        cpu_samples = cpu_data.get("samples", [])
        memory_samples = memory_data.get("samples", [])

        cpu_peak = max(
            (sample["value"] for sample in cpu_samples),
            default=None,
        )

        memory_peak = max(
            (sample["value"] for sample in memory_samples),
            default=None,
        )

        memory_percent = None

        if memory_peak is not None and container.memory_limit:
            memory_percent = (
                memory_peak / container.memory_limit
            ) * 100

        if cpu_peak is None and memory_peak is None:
            continue

        evidence.append({
            "type": "container_metrics",
            "container": container.name,
            "container_id": container_id,
            "cpu_peak_percent": (
                round(cpu_peak, 2)
                if cpu_peak is not None
                else None
            ),
            "memory_peak_mb": (
                round(memory_peak / (1024 * 1024), 2)
                if memory_peak is not None
                else None
            ),
            "memory_peak_percent": (
                round(memory_percent, 2)
                if memory_percent is not None
                else None
            ),
            "window_start": datetime.fromtimestamp(
                start,
                tz=timezone.get_current_timezone(),
            ).isoformat(),
            "window_end": datetime.fromtimestamp(
                end,
                tz=timezone.get_current_timezone(),
            ).isoformat(),
        })

        if cpu_peak is not None and cpu_peak > CPU_THRESHOLD:
            anomalies.append({
                "container": container.name,
                "type": "high_cpu",
                "value": round(cpu_peak, 2),
                "threshold": CPU_THRESHOLD,
            })

        if (
            memory_percent is not None
            and memory_percent > MEMORY_THRESHOLD
        ):
            anomalies.append({
                "container": container.name,
                "type": "high_memory",
                "value": round(memory_percent, 2),
                "threshold": MEMORY_THRESHOLD,
            })

    return evidence, anomalies


def collect_container_logs(containers, start, end):
    if not containers:
        return [], []

    container_names = [
        container.name
        for container in containers
        if container.name
    ]

    if not container_names:
        return [], []

    client = LokiClient()

    try:
        logs = client.get_container_logs(
            container_names=container_names,
            start=start,
            end=end,
            limit=100,
        )

    except Exception as exc:
        return [], [{
            "type": "collection_error",
            "source": "Loki",
            "message": str(exc),
        }]

    evidence = []

    for log in logs[:MAX_LOGS]:
        evidence.append({
            "type": "container_log",
            "timestamp": log["timestamp"],
            "container": log.get("container"),
            "service_name": log.get("service_name"),
            "message": redact_sensitive_data(
                log.get("message", "")
            ),
        })

    return evidence, []


def generate_rule_based_analysis(
    incident,
    events,
    combined_messages,
    metric_anomalies,
    evidence,
):
    """
    Existing rule-based investigation.
    Used whenever AI analysis is unavailable.
    """

    hypotheses = []
    recommended_actions = []

    if any(keyword in combined_messages for keyword in [
        "database", "sql", "postgres", "mysql", "connection pool",
    ]):
        add_hypothesis(
            hypotheses,
            "Database connectivity issue",
            0.65,
        )

        recommended_actions.extend([
            "Check database availability.",
            "Inspect database connection pool limits.",
            "Review database logs.",
        ])

    if any(keyword in combined_messages for keyword in [
        "network", "timeout", "connection refused", "connectionerror",
    ]):
        add_hypothesis(
            hypotheses,
            "Network connectivity issue",
            0.60,
        )

        recommended_actions.extend([
            "Check network connectivity.",
            "Inspect service-to-service communication.",
            "Review timeout configurations.",
        ])

    if any(keyword in combined_messages for keyword in [
        "memory", "out of memory", "resource exhausted", "cpu",
    ]):
        add_hypothesis(
            hypotheses,
            "Resource exhaustion",
            0.70,
        )

        recommended_actions.extend([
            "Inspect CPU and memory utilisation.",
            "Check application resource limits.",
            "Review recent workload changes.",
        ])

    if metric_anomalies:
        add_hypothesis(
            hypotheses,
            "Infrastructure resource pressure",
            0.75,
        )

        recommended_actions.extend([
            "Inspect resource utilisation of affected containers.",
            "Review container CPU and memory limits.",
            "Investigate workload changes around the incident.",
        ])

    if not hypotheses:
        add_hypothesis(
            hypotheses,
            "Unclassified runtime error",
            0.20,
        )

        recommended_actions.append(
            "Inspect the stack trace and application logs manually."
        )

    summary = (
        f"Rule-based investigation completed for {incident.title}. "
        f"Analysed {len(events)} error events."
    )

    return {
        "summary": summary,
        "hypotheses": hypotheses,
        "recommended_actions": list(dict.fromkeys(recommended_actions)),
    }


def run_ai_investigation(
    incident,
    events,
    evidence,
    fallback_analysis,
):
    """
    Analyse collected infrastructure evidence using OpenAI.
    Returns None if AI analysis cannot be completed.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    event_data = []

    for event in events[:MAX_AI_EVENTS]:
        event_data.append({
            "timestamp": event.occurred_at.isoformat(),
            "exception_type": event.exception_type,
            "message": redact_sensitive_data(event.message),
            "stack_trace": redact_sensitive_data(
                event.stack_trace or ""
            )[:4000],
            "severity": event.severity,
        })

    investigation_context = {
        "incident": {
            "title": incident.title,
            "fingerprint": incident.fingerprint,
            "occurrence_count": incident.occurrence_count,
            "first_seen": incident.first_seen.isoformat(),
            "last_seen": incident.last_seen.isoformat(),
        },
        "application_errors": event_data,
        "infrastructure_evidence": evidence,
        "existing_rule_analysis": fallback_analysis,
    }

    system_prompt = """
You are RuntimeRCA, an infrastructure root-cause analysis engine.

Analyse application errors, Docker container metrics and logs.

Your responsibilities:
1. Identify the most likely root cause.
2. Identify potentially affected services.
3. Explain the evidence supporting each hypothesis.
4. Recommend practical remediation steps.

Important rules:
- Use only the supplied evidence.
- Never invent metrics, logs, timestamps or services.
- Temporal correlation alone does not prove causation.
- Distinguish observed facts from hypotheses.
- If evidence is insufficient, explicitly say so.
- Confidence must be between 0 and 1.
- Do not claim a root cause is confirmed without sufficient evidence.

Return valid JSON with exactly this structure:

{
  "summary": "Investigation summary",
  "hypotheses": [
    {
      "cause": "Possible root cause",
      "confidence": 0.85,
      "reasoning": "Explanation based on evidence"
    }
  ],
  "recommended_actions": [
    "Recommended action"
  ]
}
"""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": json.dumps(
                    investigation_context,
                    default=str,
                ),
            },
        ],
        "response_format": {
            "type": "json_object",
        },
        "temperature": 0.2,
    }

    request = Request(
        OPENAI_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=45) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        content = result["choices"][0]["message"]["content"]
        analysis = json.loads(content)

        summary = analysis.get("summary")
        hypotheses = analysis.get("hypotheses")
        actions = analysis.get("recommended_actions")

        if (
            not isinstance(summary, str)
            or not summary.strip()
            or not isinstance(hypotheses, list)
            or not isinstance(actions, list)
        ):
            return None

        validated_hypotheses = []

        for hypothesis in hypotheses:
            if not isinstance(hypothesis, dict):
                continue

            cause = hypothesis.get("cause")
            confidence = hypothesis.get("confidence")
            reasoning = hypothesis.get("reasoning", "")

            if not isinstance(cause, str) or not cause.strip():
                continue

            try:
                confidence = float(confidence)
            except (TypeError, ValueError):
                continue

            if not 0 <= confidence <= 1:
                continue

            validated_hypotheses.append({
                "cause": cause[:300],
                "confidence": confidence,
                "reasoning": str(reasoning)[:2000],
            })

        validated_actions = [
            action[:1000]
            for action in actions
            if isinstance(action, str) and action.strip()
        ]

        if not validated_hypotheses:
            return None

        return {
            "summary": summary[:10000],
            "hypotheses": validated_hypotheses,
            "recommended_actions": validated_actions,
            "model": model,
        }

    except (
        HTTPError,
        URLError,
        TimeoutError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ):
        return None


def investigate_incident(incident, investigation):

    # 1. Collect application errors

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

    evidence = [{
        "type": "error_summary",
        "event_count": len(events),
        "incident_fingerprint": incident.fingerprint,
        "latest_error": (
            events[0].occurred_at.isoformat()
            if events
            else None
        ),
    }]

    # 2. Determine correlation window

    reference_time = (
        events[0].occurred_at
        if events
        else incident.last_seen
    )

    if reference_time is None:
        reference_time = timezone.now()

    reference_timestamp = reference_time.timestamp()

    start = reference_timestamp - CORRELATION_WINDOW_BEFORE
    end = reference_timestamp + CORRELATION_WINDOW_AFTER

    # 3. Find relevant Docker containers

    containers_query = DiscoveredContainer.objects.filter(
        application=incident.application,
        is_monitored=True,
    )

    if incident.service_id:
        containers_query = containers_query.filter(
            service_id=incident.service_id
        )

    containers = list(containers_query)

    # 4. Collect Prometheus metrics

    metric_evidence, metric_anomalies = collect_container_metrics(
        containers,
        start,
        end,
    )

    evidence.extend(metric_evidence)

    # 5. Collect Loki logs

    log_evidence, log_errors = collect_container_logs(
        containers,
        start,
        end,
    )

    evidence.extend(log_evidence)

    # 6. Record resource anomalies

    for anomaly in metric_anomalies:
        evidence.append({
            "type": "resource_anomaly",
            "container": anomaly["container"],
            "anomaly": anomaly["type"],
            "observed_value": anomaly["value"],
            "threshold": anomaly["threshold"],
        })

    # 7. Record observability collection failures

    evidence.extend(log_errors)

    # 8. Generate rule-based fallback analysis

    fallback_analysis = generate_rule_based_analysis(
        incident,
        events,
        combined_messages,
        metric_anomalies,
        evidence,
    )

    # 9. Run AI investigation

    ai_analysis = run_ai_investigation(
        incident,
        events,
        evidence,
        fallback_analysis,
    )

    if ai_analysis:
        final_summary = ai_analysis["summary"]
        final_hypotheses = ai_analysis["hypotheses"]
        final_actions = ai_analysis["recommended_actions"]

        evidence.append({
            "type": "ai_analysis",
            "provider": "OpenAI",
            "model": ai_analysis["model"],
            "status": "completed",
        })

    else:
        final_summary = (
            fallback_analysis["summary"]
            + " AI analysis was unavailable; rule-based analysis was used."
        )

        final_hypotheses = fallback_analysis["hypotheses"]
        final_actions = fallback_analysis["recommended_actions"]

        evidence.append({
            "type": "ai_analysis",
            "provider": "OpenAI",
            "status": "unavailable",
        })

    # 10. Save investigation

    investigation.summary = final_summary
    investigation.hypotheses = final_hypotheses
    investigation.evidence = evidence
    investigation.recommended_actions = final_actions

    investigation.status = Investigation.Status.COMPLETED
    investigation.completed_at = timezone.now()

    investigation.save()

    return investigation