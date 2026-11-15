from django.db import transaction
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from applications.models import Service
from applications.services.api_keys import verify_api_key
from ingestion.models import ErrorEvent
from ingestion.serializers import ErrorEventSerializer
from ingestion.services import redact_sensitive_data
from incidents.services import group_error_event


class ErrorIngestionView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        raw_key = request.headers.get("X-API-Key", "")
        api_key = verify_api_key(raw_key)

        if api_key is None:
            return Response(
                {"error": "Invalid or revoked API key."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not api_key.application.is_active:
            return Response(
                {"error": "Application is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ErrorEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        service_name = validated_data.pop("service_name")
        environment = validated_data["environment"]

        validated_data["message"] = redact_sensitive_data(
            validated_data["message"]
        )
        validated_data["exception_type"] = redact_sensitive_data(
            validated_data.get("exception_type", "")
        )
        validated_data["stack_trace"] = redact_sensitive_data(
            validated_data.get("stack_trace", "")
        )

        with transaction.atomic():
            service, created = Service.objects.get_or_create(
                application=api_key.application,
                name=service_name,
                environment=environment,
            )

            Service.objects.filter(pk=service.pk).update(
                last_seen=timezone.now(),
                is_active=True,
            )

            event = ErrorEvent.objects.create(
                application=api_key.application,
                service=service,
                **validated_data,
            )

            incident = group_error_event(event)

        return Response(
            {
                "event_id": str(event.id),
                "incident_id": str(incident.id),
                "service_id": str(service.id),
                "service_name": service.name,
                "service_created": created,
                "fingerprint": event.fingerprint,
                "status": "accepted",
                "message": "Error event stored and grouped successfully.",
            },
            status=status.HTTP_201_CREATED,
        )
